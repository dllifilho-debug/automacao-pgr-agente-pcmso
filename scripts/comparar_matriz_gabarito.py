"""Compara a matriz do motor com uma matriz humana assinada (D-ARQ-62).

Instrumento de medição versionado. Existe porque a comparação motor×gabarito
é a evidência que pauta a fila clínica, e ela vinha sendo feita por script
descartável em `/tmp` ou por planilha do Arquiteto — a classe de `DH-003EG-02`.

**Caminho de conversão.** `.doc → .docx` por LibreOffice, lido como TABELA por
`python-docx`. Não é escolha de conveniência: `VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`
mediu que esse caminho reproduz o Word COM célula a célula, e mediu justamente
no SPE 0030. A conversão para `txt` é que distorce célula, e é a que carrega a
ressalva "número a reconferir".

**Pareamento por slug, não por grafia.** Os dois lados chegam a slug de exame
antes de comparar: o motor já emite slug; o gabarito passa por
`carregar_mapa_nome_para_slug`, que lê `exames.yaml`. Assim "Glicemia em Jejum"
e "Glicemia de Jejum" não viram divergência clínica — `DT-003EO-02` é
divergência de forma de saída, e este instrumento não a confunde com decisão.

Uso:

    python -m scripts.comparar_matriz_gabarito <pgr.pdf> <envelope.json> \
        <gabarito.doc> <relatorio.md>

A rota é determinística (clientes offline, D-ARQ-65): qualquer chamada a LLM
vira pendência bloqueante nomeada, nunca mock silencioso. Sem chave de API.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from docx import Document

from agente_medico.adaptadores.orquestracao_pgr import processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_offline import (
    TranscritorCardOffline,
    TranscritorGHEOffline,
)
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.motor.tipos import MatrizGHE, Momento
from scripts.medir_cobertura_e_forma import (
    FormaPeriodicidade,
    carregar_mapa_nome_para_slug,
    extrair_forma_periodicidade,
    segmentar_exames,
)

_RAIZ = Path(__file__).resolve().parents[1]

# Anotação manuscrita da médica colada ao nome do cargo. Duas formas medidas no
# acervo: entre parênteses em linha própria, e após hífen na mesma linha
# ("Operador de Betoneiro- veja com a Segurança..."). Sem este corte o cargo não
# pareia e a divergência aparece como cargo ausente, que é falso.
_ANOTACAO_COLADA = re.compile(r"\s*[-–(]\s*(?:incluir|veja|obs)\b.*$", re.IGNORECASE | re.DOTALL)

_PADRAO_GHE = re.compile(r"^\s*(?:GHE|SETOR)\b", re.IGNORECASE)
_RODAPE = re.compile(
    r"^\s*(?:respons[áa]vel|m[ée]dico\(a\)|data(?: do pgr)?\b|fun[çc][ãa]o|exames solicitados"
    r"|empresa|obra\b|crm|adendo)",
    re.IGNORECASE,
)

# Rótulo de momento vazando para dentro do nome do exame. Causa medida: o
# gabarito traz `Avaliação Psicossocial ADM, PER, MRO)` — sem o parêntese de
# ABERTURA, em todas as linhas. Sem esta limpeza o nome não casa slug nenhum e a
# célula vira superemissão + subemissão falsas, uma por cargo. É a armadilha que
# `MEDICAO_FASCINO_vs_GABARITO.md` registra ter contado como "36 exames a mais"
# na primeira passada. Classe: ambíguo nunca vira negativo.
_MOMENTO_NO_NOME = re.compile(
    r"\s*\b(?:ADM|PER|MRO|MR|RET|RT|DEM)\b[\s,]*(?:\d+\s*meses?)?[\s,)]*", re.IGNORECASE
)

# Grafias que divergem entre o gabarito e `exames.yaml`. São divergência de forma
# de saída (`DT-003EO-02`), não decisão clínica — por isso moram aqui, no
# instrumento de medição, e não no vocabulário, que é conteúdo clínico e exigiria
# revisão de `R-*`. Cada entrada é uma grafia medida no acervo, não suposta.
_ALIAS_GRAFIA = {
    "glicemia em jejum": "glicemia de jejum",
    "rx de torax oit": "rx torax oit",
    "rx da coluna lombo-sacra": "rx coluna lombo-sacra",
    "rx de coluna lombo-sacra": "rx coluna lombo-sacra",
    "av. medica de saude mental": "avaliacao medica de saude mental",
}


class ConversaoIndisponivel(RuntimeError):
    """LibreOffice ausente ou sem o filtro Writer — falha nomeada, nunca silêncio."""


def normalizar_cargo(bruto: str) -> str:
    """Nome de cargo comparável entre os dois lados: anotação manuscrita cortada,
    espaços colapsados, caixa baixa."""
    sem_anotacao = _ANOTACAO_COLADA.sub("", bruto)
    return re.sub(r"\s+", " ", sem_anotacao).strip(" -–").lower()


def converter_para_docx(origem: Path, destino: Path) -> Path:
    """`.doc` → `.docx` por LibreOffice headless. `.docx` de entrada passa direto."""
    if origem.suffix.lower() == ".docx":
        return origem
    if shutil.which("soffice") is None:
        raise ConversaoIndisponivel("soffice ausente no PATH")
    destino.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "docx", "--outdir", str(destino), str(origem)],
        capture_output=True,
        timeout=300,
        check=False,
    )
    convertido = destino / (origem.stem + ".docx")
    if not convertido.exists():
        raise ConversaoIndisponivel(
            f"conversao_sem_saida para {origem.name} (falta libreoffice-writer?)"
        )
    return convertido


def _celulas_logicas(celulas: Sequence[object]) -> list[str]:
    """Colapsa células mescladas repetidas, preservando a ordem."""
    vistos: list[str] = []
    for celula in celulas:
        texto = str(getattr(celula, "text", "")).strip()
        if not vistos or vistos[-1] != texto:
            vistos.append(texto)
    return vistos


def extrair_gabarito(
    caminho_docx: Path, mapa_nomes: Mapping[str, str]
) -> dict[str, dict[str, FormaPeriodicidade]]:
    """cargo normalizado → slug de exame → forma medida na célula."""
    documento = Document(str(caminho_docx))
    fora: dict[str, dict[str, FormaPeriodicidade]] = {}
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas = _celulas_logicas(linha.cells)
            if len(celulas) < 2:
                continue
            cargo_bruto = celulas[0]
            if not cargo_bruto or _PADRAO_GHE.match(cargo_bruto) or _RODAPE.match(cargo_bruto):
                continue
            formas = [
                resolver_slug(extrair_forma_periodicidade(seg, dict(mapa_nomes)), mapa_nomes)
                for seg in segmentar_exames(celulas[1])
            ]
            if not formas:
                continue
            fora[normalizar_cargo(cargo_bruto)] = {f.exame: f for f in formas}
    return fora


def resolver_slug(
    forma: FormaPeriodicidade, mapa_nomes: Mapping[str, str]
) -> FormaPeriodicidade:
    """Segunda tentativa de slug quando a primeira não reconheceu o nome.

    `extrair_forma_periodicidade` já mapeia pelo `nome_exibicao` do vocabulário e
    cai no nome normalizado quando não acha. Aqui o nome é limpo de rótulo de
    momento vazado e passado pelo alias de grafia antes de nova consulta. Sem
    isto, três exames por cargo deixam de parear neste acervo.
    """
    if forma.exame in mapa_nomes.values():
        return forma
    limpo = _MOMENTO_NO_NOME.sub(" ", forma.nome_bruto)
    limpo = re.sub(r"[\s,;.()]+$", "", re.sub(r"\s+", " ", limpo)).strip()
    chave = _normalizar_grafia(limpo)
    chave = _ALIAS_GRAFIA.get(chave, chave)
    slug = mapa_nomes.get(chave, chave)
    return FormaPeriodicidade(
        forma.nome_bruto, slug, forma.meses, forma.forma, forma.momentos, forma.texto_bruto
    )


def _normalizar_grafia(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def extrair_motor(matrizes: Iterable[MatrizGHE]) -> dict[str, dict[str, object]]:
    """cargo normalizado → slug de exame → ExameEmitido. Expansão GHE→cargo por
    herança pura (R-GHE-01), igual a `montar_documento` — não recalcula."""
    fora: dict[str, dict[str, object]] = {}
    for matriz in matrizes:
        por_slug = {linha.exame: linha for linha in matriz.linhas}
        for cargo in matriz.cargos:
            nome = getattr(cargo, "nome", cargo)
            fora[normalizar_cargo(str(nome))] = dict(por_slug)
    return fora


@dataclass(frozen=True)
class Divergencia:
    cargo: str
    exame: str
    detalhe: str


@dataclass(frozen=True)
class Comparacao:
    cargos_pareados: tuple[str, ...] = ()
    cargos_so_motor: tuple[str, ...] = ()
    cargos_so_gabarito: tuple[str, ...] = ()
    superemissao: tuple[Divergencia, ...] = ()
    subemissao: tuple[Divergencia, ...] = ()
    divergencia_momentos: tuple[Divergencia, ...] = ()
    divergencia_periodicidade: tuple[Divergencia, ...] = ()
    celulas_motor: int = 0
    celulas_gabarito: int = 0
    cargos_identicos: int = 0
    alertas: tuple[str, ...] = field(default_factory=tuple)


def _momentos_do_motor(exame: object) -> frozenset[Momento]:
    return frozenset(getattr(exame, "momentos", ()))


def comparar(
    motor: Mapping[str, Mapping[str, object]],
    gabarito: Mapping[str, Mapping[str, FormaPeriodicidade]],
) -> Comparacao:
    pareados = sorted(set(motor) & set(gabarito))
    superem: list[Divergencia] = []
    subem: list[Divergencia] = []
    div_mom: list[Divergencia] = []
    div_per: list[Divergencia] = []
    alertas: list[str] = []
    identicos = 0

    for cargo in pareados:
        em, eg = motor[cargo], gabarito[cargo]
        extra, falta = set(em) - set(eg), set(eg) - set(em)
        superem.extend(Divergencia(cargo, e, "motor emite, gabarito não") for e in sorted(extra))
        subem.extend(Divergencia(cargo, e, "gabarito tem, motor não") for e in sorted(falta))
        if not extra and not falta:
            identicos += 1
        for slug in sorted(set(em) & set(eg)):
            emitido, forma = em[slug], eg[slug]
            mm, mg = _momentos_do_motor(emitido), forma.momentos
            if mg and mm != mg:
                div_mom.append(
                    Divergencia(
                        cargo,
                        slug,
                        f"motor={sorted(m.name for m in mm)} gabarito={sorted(m.name for m in mg)}",
                    )
                )
            meses_motor = getattr(emitido, "periodicidade_meses", None)
            if forma.meses is not None and meses_motor is not None and forma.meses != meses_motor:
                div_per.append(
                    Divergencia(cargo, slug, f"motor={meses_motor}M gabarito={forma.meses}M")
                )

    if not pareados:
        alertas.append("nenhum cargo pareou — pareamento quebrado, não acervo limpo")

    return Comparacao(
        cargos_pareados=tuple(pareados),
        cargos_so_motor=tuple(sorted(set(motor) - set(gabarito))),
        cargos_so_gabarito=tuple(sorted(set(gabarito) - set(motor))),
        superemissao=tuple(superem),
        subemissao=tuple(subem),
        divergencia_momentos=tuple(div_mom),
        divergencia_periodicidade=tuple(div_per),
        celulas_motor=sum(len(v) for v in motor.values()),
        celulas_gabarito=sum(len(v) for v in gabarito.values()),
        cargos_identicos=identicos,
        alertas=tuple(alertas),
    )


def linhas_escopo(c: Comparacao) -> list[str]:
    """Todo número sai com o escopo que o produziu, na mesma linha (003.FJ)."""
    pareados = len(c.cargos_pareados)
    repro = c.celulas_gabarito - len(c.subemissao)
    pct = f"{repro / c.celulas_gabarito * 100:.1f}%" if c.celulas_gabarito else "n/d"
    return [
        f"- cargos: motor {len(c.cargos_pareados) + len(c.cargos_so_motor)}, "
        f"gabarito {pareados + len(c.cargos_so_gabarito)}, pareados por nome {pareados}",
        f"- células (cargo × exame): motor {c.celulas_motor}, gabarito {c.celulas_gabarito}",
        f"- cargos com conjunto de exames idêntico: {c.cargos_identicos} de {pareados}",
        f"- células do gabarito reproduzidas por identidade de exame: {repro} = {pct}",
        f"- superemissão (motor emite, gabarito não): {len(c.superemissao)} células",
        f"- subemissão (gabarito tem, motor não): {len(c.subemissao)} células",
        f"- divergência de momentos: {len(c.divergencia_momentos)} células",
        f"- divergência de periodicidade: {len(c.divergencia_periodicidade)} células",
    ]


def _secao(titulo: str, itens: Sequence[Divergencia]) -> list[str]:
    if not itens:
        return [f"## {titulo} — nenhuma", ""]
    linhas = [f"## {titulo} — {len(itens)} células", ""]
    linhas.extend(f"- `{d.cargo}` · `{d.exame}` — {d.detalhe}" for d in itens)
    linhas.append("")
    return linhas


def gerar_relatorio(c: Comparacao, pgr: Path, gabarito: Path) -> str:
    linhas = [
        "# Comparação motor × matriz assinada",
        "",
        f"- PGR: `{pgr.name}`",
        f"- gabarito: `{gabarito.name}`",
        "",
        "## Resultado",
        "",
        *linhas_escopo(c),
        "",
    ]
    if c.alertas:
        linhas.extend(["## Alertas", "", *(f"- {a}" for a in c.alertas), ""])
    if c.cargos_so_motor or c.cargos_so_gabarito:
        linhas.extend(["## Cargos que não parearam", ""])
        linhas.extend(f"- só no motor: `{x}`" for x in c.cargos_so_motor)
        linhas.extend(f"- só no gabarito: `{x}`" for x in c.cargos_so_gabarito)
        linhas.append("")
    linhas.extend(_secao("Superemissão", c.superemissao))
    linhas.extend(_secao("Subemissão", c.subemissao))
    linhas.extend(_secao("Divergência de momentos", c.divergencia_momentos))
    linhas.extend(_secao("Divergência de periodicidade", c.divergencia_periodicidade))
    return "\n".join(linhas) + "\n"


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pgr")
    parser.add_argument("envelope")
    parser.add_argument("gabarito")
    parser.add_argument("relatorio")
    args = parser.parse_args(argv)

    pgr, gabarito_doc = Path(args.pgr), Path(args.gabarito)
    envelope = desserializar_confirmacao(Path(args.envelope).read_text(encoding="utf-8"))
    protocolo = carregar(_RAIZ / "agente_medico" / "protocolo")
    resultado, _pendencias = processar_arquivo_pgr(
        pgr, protocolo, TranscritorGHEOffline(), TranscritorCardOffline(), envelope
    )
    if resultado is None:
        print("pipeline devolveu None — pendência bloqueante, nada a comparar", file=sys.stderr)
        return 1

    temporario = Path(tempfile.mkdtemp(prefix="cmp_gabarito_"))
    try:
        docx = converter_para_docx(gabarito_doc, temporario)
        gabarito = extrair_gabarito(docx, carregar_mapa_nome_para_slug())
    finally:
        shutil.rmtree(temporario, ignore_errors=True)

    comparacao = comparar(extrair_motor(resultado.matrizes), gabarito)
    Path(args.relatorio).write_text(
        gerar_relatorio(comparacao, pgr, gabarito_doc), encoding="utf-8"
    )
    for linha in linhas_escopo(comparacao):
        print(linha)
    return 0


if __name__ == "__main__":  # pragma: no cover - entrypoint
    raise SystemExit(main())
