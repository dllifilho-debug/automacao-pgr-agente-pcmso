"""Índice derivado das decisões D-ARQ de docs/DECISOES_ARQUITETURAIS.md.

Cada decisão é um header `## D-ARQ-NN — Título` até o header seguinte (ou até
"## Histórico de revisões", que não é decisão e não entra no índice). Status
é a primeira linha do bloco que casa `**Status[:]**`, texto após o marcador,
truncado no primeiro ponto final; ausente, célula vazia (não inferir). Versão
da fonte é o último `| vNNN |` da tabela de revisões.
"""

from __future__ import annotations

import re
from pathlib import Path

_RAIZ = Path(__file__).resolve().parent.parent

_CAMINHO_DECISOES = _RAIZ / "docs" / "DECISOES_ARQUITETURAIS.md"
_CAMINHO_INDICE = _RAIZ / "docs" / "INDICE_DARQ.md"

_REGEX_HEADER = re.compile(r"^## D-ARQ-(\d+) — (.+)$", re.MULTILINE)
_REGEX_HISTORICO = re.compile(r"^## Histórico de revisões$", re.MULTILINE)
_REGEX_SUBSECAO = re.compile(r"^### ", re.MULTILINE)
_REGEX_STATUS = re.compile(r"^\*\*Status:?\*\*\s*(.+)$", re.MULTILINE)
_REGEX_VERSAO = re.compile(r"^\|\s*v(\d+)\s*\|", re.MULTILINE)


def _escapar_pipe(texto: str) -> str:
    return texto.replace("|", "\\|")


def _status_do_bloco(bloco: str) -> str:
    subsecao = _REGEX_SUBSECAO.search(bloco)
    corpo_proprio = bloco[: subsecao.start()] if subsecao is not None else bloco
    correspondencia = _REGEX_STATUS.search(corpo_proprio)
    if correspondencia is None:
        return ""
    return correspondencia.group(1).split(".")[0].strip()


def gerar_indice() -> str:
    texto = _CAMINHO_DECISOES.read_text(encoding="utf-8")

    fim_historico = _REGEX_HISTORICO.search(texto)
    limite = fim_historico.start() if fim_historico is not None else len(texto)

    headers = list(_REGEX_HEADER.finditer(texto))
    linhas_tabela: list[str] = []
    for indice, header in enumerate(headers):
        if header.start() >= limite:
            continue
        inicio_bloco = header.end()
        fim_bloco = headers[indice + 1].start() if indice + 1 < len(headers) else limite
        bloco = texto[inicio_bloco:fim_bloco]

        id_ = f"D-ARQ-{header.group(1)}"
        titulo = _escapar_pipe(header.group(2).strip())
        status = _escapar_pipe(_status_do_bloco(bloco))
        numero_linha = texto.count("\n", 0, header.start()) + 1
        chars = len(bloco)

        linhas_tabela.append(f"| {id_} | {titulo} | {status} | {numero_linha} | {chars} |")

    versoes = _REGEX_VERSAO.findall(texto)
    versao_fonte = f"v{versoes[-1]}" if versoes else "v?"

    partes = [
        "# ÍNDICE D-ARQ — DERIVADO, NÃO EDITAR À MÃO",
        "",
        "Gerado por `scripts/gerar_indice_darq.py` a partir de",
        "`docs/DECISOES_ARQUITETURAIS.md`. Editar este arquivo à mão faz",
        "`tests/test_gerar_indice_darq.py` falhar.",
        "",
        f"Fonte: DECISOES_ARQUITETURAIS.md {versao_fonte} · {len(linhas_tabela)} decisões",
        "",
        "| ID | Título | Status | Linha | Chars |",
        "|---|---|---|---|---|",
        *linhas_tabela,
        "",
    ]
    return "\n".join(partes)


def main() -> None:
    _CAMINHO_INDICE.write_text(gerar_indice(), encoding="utf-8")


if __name__ == "__main__":
    main()
