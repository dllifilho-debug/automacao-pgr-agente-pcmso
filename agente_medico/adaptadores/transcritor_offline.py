"""Clientes-bomba offline (D-ARQ-65), movidos de scripts/medicao_pgr.py
(003.EQ): `superficie/` não deve importar de `scripts/`, que é instrumento
de medição — corpo idêntico ao original, sem mudança de comportamento.
"""

from __future__ import annotations

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.tipos import GHEVerbatim


class TranscritorGHEOffline:
    """Rodada OFFLINE (D-ARQ-65): recusa nomeada, nunca mock — se a rota
    determinística for recusada, o fallback LLM cai aqui e vira pendência
    bloqueante transcricao_indisponivel_pgr no relatório."""

    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel("rodada offline: cliente LLM indisponível por design")


class TranscritorCardOffline:
    """Rodada OFFLINE (D-ARQ-65): recusa nomeada, nunca mock — se a rota
    determinística for recusada, o fallback LLM cai aqui e vira pendência
    bloqueante transcricao_indisponivel_pgr no relatório."""

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel("rodada offline: cliente LLM indisponível por design")
