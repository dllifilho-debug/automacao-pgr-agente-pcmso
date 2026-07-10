"""CLI de confirmação-RT do envelope do topo (D-ARQ-54 fatia 1).

Apresentação-pura sobre o contrato ida/volta de motor/revisao_envelope.py
(D-ARQ-53 P3): a CLI renderiza o artefato-ida produzido por
serializar_envelope, coleta validade + assinatura_engenheiro do RT, e emite
o artefato-volta consumido por desserializar_confirmacao. Lógica-de-domínio
ZERO — a superfície consome o artefato, não o reconstrói.
"""

from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from typing import Any, TextIO

from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.superficie.apresentacao import (
    ArtefatoIdaIlegivel,
    conduzir_revisao,
    executar_main,
    ler_resposta,
)

_CAMPOS_RENDERIZACAO = frozenset({"candidatas", "proposta", "credencial", "confirmacao"})

__all__ = ["ArtefatoIdaIlegivel", "revisar_envelope", "main"]


def revisar_envelope(artefato_ida: str, entrada: TextIO, saida: TextIO) -> str:
    """Conduz a confirmação-RT do envelope: renderiza o artefato-ida em
    `saida`, coleta validade + assinatura_engenheiro via `entrada`, e
    retorna o artefato-volta. Sem re-validação de domínio — confia no
    produtor (serializar_envelope); o self-check final reutiliza
    desserializar_confirmacao (anti-erro-silencioso D-ARQ-22)."""
    return conduzir_revisao(
        artefato_ida,
        _CAMPOS_RENDERIZACAO,
        _revisar,
        desserializar_confirmacao,
        entrada,
        saida,
    )


def _revisar(dados: dict[str, Any], entrada: TextIO, saida: TextIO) -> dict[str, Any]:
    _renderizar(dados, saida)

    validade = _prompt_validade(dados["proposta"], entrada, saida)
    assinatura = _prompt_assinatura(entrada, saida)

    dados["confirmacao"]["validade"] = validade
    dados["confirmacao"]["assinatura_engenheiro"] = assinatura

    return dados


def _renderizar(dados: dict[str, Any], saida: TextIO) -> None:
    credencial = dados["credencial"]
    saida.write("Credencial:\n")
    saida.write(f"  Responsável técnico: {credencial['responsavel_tecnico']}\n")
    saida.write(f"  Título RT: {credencial['titulo_rt']}\n")
    saida.write(f"  Registro profissional: {credencial['registro_profissional']}\n")

    saida.write("\nCandidatas de validade:\n")
    for i, candidata in enumerate(dados["candidatas"], start=1):
        data_texto = candidata["data"] if candidata["data"] is not None else "(não-parseável)"
        saida.write(f"  {i}. {candidata['texto']} -> {data_texto}\n")

    proposta = dados["proposta"]
    proposta_texto = proposta if proposta is not None else "(nenhuma)"
    saida.write(f"\nProposta: {proposta_texto}\n\n")


def _prompt_validade(proposta: str | None, entrada: TextIO, saida: TextIO) -> str:
    proposta_texto = proposta if proposta is not None else "(nenhuma)"
    while True:
        saida.write(f"Validade [Enter mantém: {proposta_texto}]: ")
        resposta = ler_resposta(entrada, "confirmação-RT")
        if resposta == "":
            if proposta is not None:
                return proposta
            saida.write("Nenhuma proposta disponível — informe uma data ISO (AAAA-MM-DD).\n")
            continue
        try:
            date.fromisoformat(resposta)
        except ValueError:
            saida.write(f"Data inválida: {resposta!r}. Use o formato ISO (AAAA-MM-DD).\n")
            continue
        return resposta


def _prompt_assinatura(entrada: TextIO, saida: TextIO) -> bool:
    while True:
        saida.write("Assinatura do engenheiro confirmada? (s/n): ")
        resposta = ler_resposta(entrada, "confirmação-RT").lower()
        if resposta == "s":
            return True
        if resposta == "n":
            return False
        saida.write(f"Entrada inválida: {resposta!r}. Digite 's' ou 'n'.\n")


def main(argv: Sequence[str] | None = None) -> int:
    return executar_main(
        "Confirmação-RT do envelope do topo (D-ARQ-54 fatia 1).",
        revisar_envelope,
        argv,
    )


if __name__ == "__main__":
    import sys

    sys.exit(main())
