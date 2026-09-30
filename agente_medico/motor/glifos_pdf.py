"""D-ARQ-89 cl.1–3: glifo que o gerador do PDF deixa sem mapeamento Unicode
(ToUnicode U+0000) é restaurado na extração pelo nome em `/Differences`, numa
tabela verificada glifo a glifo. Glifo fora da tabela segue U+0000 (cl.2): a
sanitização de apresentação cobre."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pdfminer.pdffont import PDFFont, PDFSimpleFont
from pdfminer.pdfinterp import PDFResourceManager
from pdfminer.pdftypes import resolve1


@dataclass(frozen=True)
class GlifoRestaurado:
    caractere: str
    procedencia: str


# Conjunto ".case" da Inter (pontuação para caixa-alta e dígitos). Medido em
# 29/09/2026 nos 3 PGRs do acervo com NUL (Fascino, Vila Brasil, Verde Maris):
# 5.879 ocorrências, todas destes 13 glifos da fonte "Inter-Thin" (Type3).
# Procedência = recorte a 500 dpi da primeira ocorrência, conferido à vista.
_FASCINO = "PGR Fascino 15.07.26"
GLIFOS_RESTAURADOS: dict[tuple[str, str], GlifoRestaurado] = {
    ("Inter-Thin", "g14B"): GlifoRestaurado("(", f"{_FASCINO}, p. 2, 'Psicossociais (FRPRT)'"),
    ("Inter-Thin", "g14C"): GlifoRestaurado(")", f"{_FASCINO}, p. 2, 'Psicossociais (FRPRT)'"),
    ("Inter-Thin", "g14D"): GlifoRestaurado("[", f"{_FASCINO}, p. 13, 'mínimo de [X] brigadistas'"),
    ("Inter-Thin", "g14E"): GlifoRestaurado("]", f"{_FASCINO}, p. 13, 'mínimo de [X] brigadistas'"),
    ("Inter-Thin", "g15C"): GlifoRestaurado("-", f"{_FASCINO}, p. 2, 'Equipamentos (NR-12)'"),
    ("Inter-Thin", "g15D"): GlifoRestaurado("–", f"{_FASCINO}, p. 3, 'Qd 3037 – Lotes 20'"),
    ("Inter-Thin", "g15E"): GlifoRestaurado("—", f"{_FASCINO}, p. 2, 'CIPA — Comissão'"),
    ("Inter-Thin", "g16E"): GlifoRestaurado(":", f"{_FASCINO}, p. 4, 'item 1.5.6.1: (a)'"),
    ("Inter-Thin", "g17E"): GlifoRestaurado("<", f"{_FASCINO}, p. 8, '10 % < Exposição'"),
    ("Inter-Thin", "g17F"): GlifoRestaurado(">", f"{_FASCINO}, p. 9, 'cargas (>23 kg'"),
    ("Inter-Thin", "g181"): GlifoRestaurado("+", f"{_FASCINO}, p. 45, 'FPS 30+'"),
    ("Inter-Thin", "g183"): GlifoRestaurado("×", f"{_FASCINO}, p. 5, 'Matriz 5×5'"),
    ("Inter-Thin", "g18B"): GlifoRestaurado("*", f"{_FASCINO}, p. 10, '2, 3, 4*'"),
}


def nome_da_fonte(fontname: str) -> str:
    """Nome sem o prefixo de subconjunto ("BBAAAA+Inter-Thin" -> "Inter-Thin")."""
    return fontname.split("+", 1)[-1]


def _nomes_differences(spec: Any) -> dict[int, str]:
    encoding = resolve1(spec.get("Encoding")) if isinstance(spec, dict) else None
    if not isinstance(encoding, dict):
        return {}
    nomes: dict[int, str] = {}
    codigo: int | None = None
    for item in resolve1(encoding.get("Differences")) or []:
        item = resolve1(item)
        if isinstance(item, int):
            codigo = item
        elif codigo is not None:
            nomes[codigo] = str(getattr(item, "name", item))
            codigo += 1
    return nomes


def restaurar_glifos(font: PDFFont, spec: Any) -> int:
    """Troca, no mapa ToUnicode da fonte, U+0000 pelo caractere da tabela.
    Devolve quantos códigos foram restaurados."""
    if not isinstance(font, PDFSimpleFont) or font.unicode_map is None:
        return 0
    mapa: dict[int, str] | None = getattr(font.unicode_map, "cid2unichr", None)
    if mapa is None:
        return 0
    nulos = [codigo for codigo, texto in mapa.items() if texto == "\x00"]
    if not nulos:
        return 0
    fonte = nome_da_fonte(str(font.fontname))
    nomes = _nomes_differences(spec)
    restaurados = 0
    for codigo in nulos:
        glifo = GLIFOS_RESTAURADOS.get((fonte, nomes.get(codigo, "")))
        if glifo is not None:
            mapa[codigo] = glifo.caractere
            restaurados += 1
    return restaurados


class GerenciadorComGlifos(PDFResourceManager):
    """`PDFResourceManager` que restaura os glifos da tabela ao carregar cada
    fonte. Injetado no pdfplumber por `io_pdf.paginas_liberadas`."""

    def get_font(self, objid: object, spec: Any) -> PDFFont:
        font = super().get_font(objid, spec)
        restaurar_glifos(font, spec)
        return font
