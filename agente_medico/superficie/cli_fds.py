"""CLI de revisão-RT do verbatim da FDS (D-ARQ-54 fatia 2).

Apresentação-pura sobre o contrato ida/volta de motor/revisao_verbatim.py:
a CLI renderiza o artefato-ida produzido por serializar_verbatim, coleta a
revisão-RT bloco a bloco / membro a membro, e emite o artefato-volta
consumido por desserializar_verbatim. Lógica-de-domínio ZERO — a superfície
consome o artefato, não o reconstrói.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, TextIO

from agente_medico.motor.revisao_verbatim import desserializar_verbatim
from agente_medico.superficie.apresentacao import (
    ArtefatoIdaIlegivel,
    conduzir_revisao,
    executar_main,
    ler_resposta,
    prompt_enter_mantem,
)

_CAMPOS_ENVELOPE = frozenset({"versao", "blocos"})

__all__ = ["ArtefatoIdaIlegivel", "revisar_verbatim", "main"]


def revisar_verbatim(artefato_ida: str, entrada: TextIO, saida: TextIO) -> str:
    """Conduz a revisão-RT do verbatim da FDS: renderiza o artefato-ida em
    `saida`, coleta a revisão bloco a bloco / membro a membro via `entrada`,
    e retorna o artefato-volta. Sem re-validação de conteúdo — confia no
    produtor (serializar_verbatim); o self-check final reutiliza
    desserializar_verbatim (anti-erro-silencioso D-ARQ-22). gate_forma NÃO
    é chamado aqui — já roda em montar_fds_revisado por decisão selada."""
    return conduzir_revisao(
        artefato_ida,
        _CAMPOS_ENVELOPE,
        _revisar,
        desserializar_verbatim,
        entrada,
        saida,
    )


def _revisar(dados: dict[str, Any], entrada: TextIO, saida: TextIO) -> dict[str, Any]:
    blocos_revisados = [
        _revisar_bloco(bloco, i, entrada, saida) for i, bloco in enumerate(dados["blocos"], start=1)
    ]
    dados["blocos"] = blocos_revisados
    return dados


def _revisar_bloco(
    bloco: dict[str, Any], indice: int, entrada: TextIO, saida: TextIO
) -> dict[str, Any]:
    membros = bloco["membros"]
    saida.write(f"Bloco {indice} — faixa: {bloco['faixa']}\n")
    for j, membro in enumerate(membros, start=1):
        saida.write(f"  {j}. {membro['cas']} | {membro['nome']}\n")

    faixa = prompt_enter_mantem("Faixa", bloco["faixa"], "revisão-RT", entrada, saida)

    membros_revisados: list[dict[str, str]] = []
    for j, membro in enumerate(membros, start=1):
        resultado = _revisar_membro(membro, j, entrada, saida)
        if resultado is not None:
            membros_revisados.append(resultado)

    return {"faixa": faixa, "membros": membros_revisados}


def _revisar_membro(
    membro: dict[str, str], indice: int, entrada: TextIO, saida: TextIO
) -> dict[str, str] | None:
    while True:
        saida.write(f"  Membro {indice} [Enter mantém / e edita / r remove]: ")
        resposta = ler_resposta(entrada, "revisão-RT")
        if resposta == "":
            return {"cas": membro["cas"], "nome": membro["nome"]}
        if resposta == "r":
            return None
        if resposta == "e":
            cas = prompt_enter_mantem("  CAS", membro["cas"], "revisão-RT", entrada, saida)
            nome = prompt_enter_mantem("  Nome", membro["nome"], "revisão-RT", entrada, saida)
            return {"cas": cas, "nome": nome}
        saida.write(f"Opção inválida: {resposta!r}. Digite Enter, 'e' ou 'r'.\n")


def main(argv: Sequence[str] | None = None) -> int:
    return executar_main(
        "Revisão-RT do verbatim da FDS (D-ARQ-54 fatia 2).",
        revisar_verbatim,
        argv,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
