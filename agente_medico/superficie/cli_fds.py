"""CLI de revisão-RT do verbatim da FDS (D-ARQ-54 fatia 2).

Apresentação-pura sobre o contrato ida/volta de motor/revisao_verbatim.py:
a CLI renderiza o artefato-ida produzido por serializar_verbatim, coleta a
revisão-RT bloco a bloco / membro a membro, e emite o artefato-volta
consumido por desserializar_verbatim. Lógica-de-domínio ZERO — a superfície
consome o artefato, não o reconstrói.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, TextIO

from agente_medico.motor.revisao_verbatim import desserializar_verbatim

_CAMPOS_ENVELOPE = {"versao", "blocos"}


class ArtefatoIdaIlegivel(ValueError):
    """Artefato de ida não é JSON válido ou não tem os campos que a
    renderização usa (versao/blocos)."""


def revisar_verbatim(artefato_ida: str, entrada: TextIO, saida: TextIO) -> str:
    """Conduz a revisão-RT do verbatim da FDS: renderiza o artefato-ida em
    `saida`, coleta a revisão bloco a bloco / membro a membro via `entrada`,
    e retorna o artefato-volta. Sem re-validação de conteúdo — confia no
    produtor (serializar_verbatim); o self-check final reutiliza
    desserializar_verbatim (anti-erro-silencioso D-ARQ-22). gate_forma NÃO
    é chamado aqui — já roda em montar_fds_revisado por decisão selada."""
    try:
        dados = json.loads(artefato_ida)
    except json.JSONDecodeError as erro:
        raise ArtefatoIdaIlegivel(f"JSON inválido: {erro}") from erro

    if not isinstance(dados, dict):
        raise ArtefatoIdaIlegivel(
            f"Artefato de ida deve ser um objeto JSON, recebido {type(dados).__name__}"
        )

    campos_ausentes = _CAMPOS_ENVELOPE - set(dados)
    if campos_ausentes:
        raise ArtefatoIdaIlegivel(
            f"Artefato de ida sem campo(s) necessário(s) à renderização: {sorted(campos_ausentes)}"
        )

    blocos_revisados = [
        _revisar_bloco(bloco, i, entrada, saida) for i, bloco in enumerate(dados["blocos"], start=1)
    ]
    dados["blocos"] = blocos_revisados

    volta = json.dumps(dados, ensure_ascii=False, indent=2)
    desserializar_verbatim(volta)
    return volta


def _revisar_bloco(
    bloco: dict[str, Any], indice: int, entrada: TextIO, saida: TextIO
) -> dict[str, Any]:
    membros = bloco["membros"]
    saida.write(f"Bloco {indice} — faixa: {bloco['faixa']}\n")
    for j, membro in enumerate(membros, start=1):
        saida.write(f"  {j}. {membro['cas']} | {membro['nome']}\n")

    faixa = _prompt_faixa(bloco["faixa"], entrada, saida)

    membros_revisados: list[dict[str, str]] = []
    for j, membro in enumerate(membros, start=1):
        resultado = _revisar_membro(membro, j, entrada, saida)
        if resultado is not None:
            membros_revisados.append(resultado)

    return {"faixa": faixa, "membros": membros_revisados}


def _prompt_faixa(faixa_atual: str, entrada: TextIO, saida: TextIO) -> str:
    saida.write(f"Faixa [Enter mantém: {faixa_atual}]: ")
    linha = entrada.readline()
    if linha == "":
        raise EOFError("entrada encerrada antes da revisão-RT")
    resposta = linha.strip()
    if resposta == "":
        return faixa_atual
    return resposta


def _revisar_membro(
    membro: dict[str, str], indice: int, entrada: TextIO, saida: TextIO
) -> dict[str, str] | None:
    while True:
        saida.write(f"  Membro {indice} [Enter mantém / e edita / r remove]: ")
        linha = entrada.readline()
        if linha == "":
            raise EOFError("entrada encerrada antes da revisão-RT")
        resposta = linha.strip()
        if resposta == "":
            return {"cas": membro["cas"], "nome": membro["nome"]}
        if resposta == "r":
            return None
        if resposta == "e":
            cas = _prompt_campo("CAS", membro["cas"], entrada, saida)
            nome = _prompt_campo("Nome", membro["nome"], entrada, saida)
            return {"cas": cas, "nome": nome}
        saida.write(f"Opção inválida: {resposta!r}. Digite Enter, 'e' ou 'r'.\n")


def _prompt_campo(rotulo: str, valor_atual: str, entrada: TextIO, saida: TextIO) -> str:
    saida.write(f"  {rotulo} [Enter mantém: {valor_atual}]: ")
    linha = entrada.readline()
    if linha == "":
        raise EOFError("entrada encerrada antes da revisão-RT")
    resposta = linha.strip()
    if resposta == "":
        return valor_atual
    return resposta


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Revisão-RT do verbatim da FDS (D-ARQ-54 fatia 2)."
    )
    parser.add_argument("caminho_ida", type=Path)
    parser.add_argument("caminho_volta", type=Path)
    args = parser.parse_args(argv)

    artefato_ida = args.caminho_ida.read_text(encoding="utf-8")
    volta = revisar_verbatim(artefato_ida, sys.stdin, sys.stdout)
    args.caminho_volta.write_text(volta, encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
