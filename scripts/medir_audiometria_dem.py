"""Instrumento de medição (003.EX fatia 0): a audiometria sai com `DEM` para
quem não tem exposição a ruído, nos gabaritos humanos? Não é código de
produção — nenhuma regra clínica é lida ou alterada aqui, `regras.yaml` não é
tocado. Reuso obrigatório (D-ARQ-67): o mapa rótulo->Momento é a inversão de
`_ROTULO_MOMENTO` (agente_medico/superficie/documento_matriz.py), nunca
redigitado.
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

from docx import Document

from agente_medico.motor.tipos import Momento
from agente_medico.superficie.documento_matriz import _ROTULO_MOMENTO

_ROTULO_PARA_MOMENTO: dict[str, Momento] = {
    rotulo: momento for momento, rotulo in _ROTULO_MOMENTO.items()
}

_PADRAO_GHE = re.compile(r"^GHE\s*\d+")
_PADRAO_GRUPO = re.compile(r"\(([^)]*)\)")
_PADRAO_METADADO = re.compile(r"^(Empresa|Obra|M[eé]dico|SETOR|Data|Adendo)", re.IGNORECASE)
_CABECALHOS_TABELA = {"FUNÇÃO", "EXAMES SOLICITADOS"}


def parsear_momentos(celula: str) -> frozenset[Momento]:
    """Extrai os `Momento` reconhecidos do último grupo entre parênteses de
    uma célula de exame já isolada a uma linha (ex.: "Audiometria (ADM, PER,
    MRO, DEM)"). O último grupo é o dos momentos — quando a periodicidade
    vem embutida num grupo anterior (ex.: "Audiometria (12 meses), (ADM,
    PER, MRO, DEM)"), esse grupo é ignorado por não ser o último.
    """
    grupos = _PADRAO_GRUPO.findall(celula)
    if not grupos:
        return frozenset()
    momentos: set[Momento] = set()
    for rotulo in grupos[-1].split(","):
        momento = _ROTULO_PARA_MOMENTO.get(rotulo.strip())
        if momento is not None:
            momentos.add(momento)
    return frozenset(momentos)


def rotulos_nao_reconhecidos(celula: str) -> frozenset[str]:
    """Rótulos do último grupo entre parênteses que não batem com nenhum
    `Momento` conhecido (via `_ROTULO_PARA_MOMENTO`) — reportados, não
    engolidos em silêncio.
    """
    grupos = _PADRAO_GRUPO.findall(celula)
    if not grupos:
        return frozenset()
    return frozenset(
        rotulo.strip()
        for rotulo in grupos[-1].split(",")
        if rotulo.strip() and rotulo.strip() not in _ROTULO_PARA_MOMENTO
    )


_PADRAO_TRECHO_AUDIOMETRIA = re.compile(
    r"Audiometria\s*(\([^)]*\))\s*,?\s*(\([^)]*\))?", re.IGNORECASE
)


def _extrair_linha_audiometria(texto_celula: str) -> str | None:
    # Audiometria nem sempre abre a própria linha — em alguns cargos do
    # gabarito RESERVA 0028 ela vem colada ao exame anterior na mesma linha
    # (ex.: "Exame Clinico (...), Audiometria (...);"), e às vezes a
    # periodicidade vem num grupo separado antes dos momentos (ex.:
    # "Audiometria (12 meses), (ADM, PER, MRO, DEM)"). Captura no máximo os
    # dois primeiros grupos entre parênteses após "Audiometria" — o bastante
    # para cobrir período+momentos sem sangrar para o próximo exame da
    # célula, que normalmente não é separado por ';' ou '\n'.
    match = _PADRAO_TRECHO_AUDIOMETRIA.search(texto_celula)
    if match is None:
        return None
    return match.group(0).strip()


def _linha_e_cargo(cargo: str) -> bool:
    cargo = cargo.strip()
    if not cargo:
        return False
    if _PADRAO_GHE.match(cargo):
        return False
    if cargo.upper() in _CABECALHOS_TABELA:
        return False
    if _PADRAO_METADADO.match(cargo):
        return False
    return True


@dataclass(frozen=True)
class RegistroCargo:
    ghe: str
    cargo: str
    tem_audiometria: bool
    momentos_audiometria: frozenset[Momento]
    rotulos_nao_reconhecidos: frozenset[str] = frozenset()


def extrair_registros(caminho: Path) -> tuple[list[RegistroCargo], list[str]]:
    documento = Document(str(caminho))
    registros: list[RegistroCargo] = []
    suspeitas: list[str] = []
    ghe_atual = "(sem agrupamento GHE)"
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas = linha.cells
            cargo = celulas[0].text.strip()
            if _PADRAO_GHE.match(cargo):
                ghe_atual = re.sub(r"\s+", " ", cargo)
                continue
            if not _linha_e_cargo(cargo) or len(celulas) < 2:
                continue
            linha_audio = _extrair_linha_audiometria(celulas[1].text)
            if linha_audio is None:
                registros.append(RegistroCargo(ghe_atual, cargo, False, frozenset()))
                continue
            momentos = parsear_momentos(linha_audio)
            desconhecidos = rotulos_nao_reconhecidos(linha_audio)
            if desconhecidos:
                suspeitas.append(
                    f"[{ghe_atual}] {cargo}: rótulo(s) não reconhecido(s) "
                    f"{sorted(desconhecidos)} em {linha_audio!r}"
                )
            registros.append(RegistroCargo(ghe_atual, cargo, True, momentos, desconhecidos))
    return registros, suspeitas


def classificar_dem(
    com_audio: list[RegistroCargo],
) -> tuple[list[RegistroCargo], list[RegistroCargo], list[RegistroCargo]]:
    """Separa cargos com linha de audiometria em três grupos, não dois.
    Ausência de leitura não é negação de conduta: célula com rótulo não
    reconhecido na própria linha de audiometria vai para `indeterminado`,
    não para `sem_dem` — o parser recusou-se a adivinhar (D-ARQ-13 fora do
    motor), e a agregação não pode reverter essa recusa silenciosamente.
    """
    com_dem = [r for r in com_audio if Momento.DEM in r.momentos_audiometria]
    indeterminado = [
        r
        for r in com_audio
        if Momento.DEM not in r.momentos_audiometria and r.rotulos_nao_reconhecidos
    ]
    sem_dem = [
        r
        for r in com_audio
        if Momento.DEM not in r.momentos_audiometria and not r.rotulos_nao_reconhecidos
    ]
    return com_dem, indeterminado, sem_dem


def _cargo_para_exibicao(cargo: str) -> str:
    # A coluna FUNÇÃO às vezes tem anotação da médica na mesma célula, em
    # parágrafo separado (EMENDA 1, 003.EX) — cargo e anotação continuam um
    # único registro; só o "\n" embutido precisa virar separador visível
    # para não quebrar o item da lista em duas linhas no relatório.
    return cargo.replace("\n", " / ")


def gerar_secao(nome_doc: str, registros: list[RegistroCargo], suspeitas: list[str]) -> str:
    com_audio = [r for r in registros if r.tem_audiometria]
    com_dem, indeterminado, sem_dem = classificar_dem(com_audio)
    linhas = [
        f"## {nome_doc}",
        "",
        f"- total de cargos: {len(registros)}",
        f"- cargos com linha de audiometria: {len(com_audio)}",
        f"- com DEM: {len(com_dem)}",
        f"- indeterminado (rótulo não reconhecido na linha de audiometria): {len(indeterminado)}",
        f"- sem DEM (forma limpa, confirmado): {len(sem_dem)}",
        "",
        "### Cargos com audiometria + DEM",
        "",
    ]
    linhas.extend(f"- [{r.ghe}] {_cargo_para_exibicao(r.cargo)}" for r in com_dem)
    linhas.append("")
    linhas.append("### Cargos indeterminados (não contar como sem DEM)")
    linhas.append("")
    linhas.extend(f"- [{r.ghe}] {_cargo_para_exibicao(r.cargo)}" for r in indeterminado)
    linhas.append("")
    linhas.append("### Cargos com audiometria SEM DEM (forma limpa, confirmado)")
    linhas.append("")
    linhas.extend(f"- [{r.ghe}] {_cargo_para_exibicao(r.cargo)}" for r in sem_dem)
    linhas.append("")
    if suspeitas:
        linhas.append("### Rótulos não reconhecidos")
        linhas.append("")
        linhas.extend(f"- {s}" for s in suspeitas)
        linhas.append("")
    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", nargs="+", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    args = parser.parse_args()

    secoes = []
    for caminho in args.docx:
        registros, suspeitas = extrair_registros(caminho)
        secoes.append(gerar_secao(caminho.name, registros, suspeitas))

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text("\n".join(secoes), encoding="utf-8")
    print(f"Relatório gravado em {args.saida}", file=sys.stderr)


if __name__ == "__main__":
    main()
