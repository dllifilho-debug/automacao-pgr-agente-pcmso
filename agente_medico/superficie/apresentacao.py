"""Contrato de apresentação compartilhado pelas CLIs de revisão-RT
(D-ARQ-54 P2, fatia 3).

As CLIs de superfície (cli_envelope, cli_fds) são apresentação-pura sobre
contratos ida/volta do motor: renderizam o artefato-ida, coletam a revisão
do RT via prompts, e emitem o artefato-volta após um self-check. Este
módulo extrai o que era duplicado entre elas — carregamento e validação
estrutural do artefato-ida, leitura de resposta com tratamento de EOF, o
padrão de prompt "Enter mantém o valor atual", a condução da revisão
(carregar → revisar → serializar → self-check), e o esqueleto de main()
via argparse — sem alterar nenhum comportamento observável.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, TextIO


class ArtefatoIdaIlegivel(ValueError):
    """Artefato de ida não é JSON válido ou não tem os campos que a
    renderização usa."""


def carregar_artefato_ida(texto: str, campos_necessarios: frozenset[str]) -> dict[str, Any]:
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise ArtefatoIdaIlegivel(f"JSON inválido: {erro}") from erro

    if not isinstance(dados, dict):
        raise ArtefatoIdaIlegivel(
            f"Artefato de ida deve ser um objeto JSON, recebido {type(dados).__name__}"
        )

    campos_ausentes = campos_necessarios - set(dados)
    if campos_ausentes:
        raise ArtefatoIdaIlegivel(
            f"Artefato de ida sem campo(s) necessário(s) à renderização: {sorted(campos_ausentes)}"
        )

    return dados


def ler_resposta(entrada: TextIO, contexto: str) -> str:
    linha = entrada.readline()
    if linha == "":
        raise EOFError(f"entrada encerrada antes da {contexto}")
    return linha.strip()


def prompt_enter_mantem(
    rotulo: str, valor_atual: str, contexto: str, entrada: TextIO, saida: TextIO
) -> str:
    saida.write(f"{rotulo} [Enter mantém: {valor_atual}]: ")
    resposta = ler_resposta(entrada, contexto)
    if resposta == "":
        return valor_atual
    return resposta


def emitir_volta(dados: dict[str, Any], self_check: Callable[[str], object]) -> str:
    """Serializa `dados` como artefato-volta e roda `self_check` sobre ele
    antes de devolver (self-check único, anti-erro-silencioso D-ARQ-22,
    D-ARQ-54 fatia 4) — compartilhado entre as CLIs e a superfície web."""
    volta = json.dumps(dados, ensure_ascii=False, indent=2)
    self_check(volta)
    return volta


def conduzir_revisao(
    artefato_ida: str,
    campos_necessarios: frozenset[str],
    revisar: Callable[[dict[str, Any], TextIO, TextIO], dict[str, Any]],
    self_check: Callable[[str], object],
    entrada: TextIO,
    saida: TextIO,
) -> str:
    dados = carregar_artefato_ida(artefato_ida, campos_necessarios)
    dados = revisar(dados, entrada, saida)
    return emitir_volta(dados, self_check)


def executar_main(
    descricao: str,
    revisar_fn: Callable[[str, TextIO, TextIO], str],
    argv: Sequence[str] | None,
) -> int:
    parser = argparse.ArgumentParser(description=descricao)
    parser.add_argument("caminho_ida", type=Path)
    parser.add_argument("caminho_volta", type=Path)
    args = parser.parse_args(argv)

    artefato_ida = args.caminho_ida.read_text(encoding="utf-8")
    volta = revisar_fn(artefato_ida, sys.stdin, sys.stdout)
    args.caminho_volta.write_text(volta, encoding="utf-8")
    return 0
