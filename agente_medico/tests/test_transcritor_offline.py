"""Testes dos clientes-bomba offline movidos para adaptadores/ (003.EQ) —
cada teste carrega a reversão que deve deixá-lo vermelho."""

from __future__ import annotations

import pytest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline


def test_transcritor_offline_levanta_transcricao_indisponivel() -> None:
    # Reversão que mata: fazer transcrever() devolver um GHEVerbatim em vez
    # de levantar TranscricaoIndisponivel — a rodada offline viraria mock
    # silencioso em vez de recusa nomeada (D-ARQ-65).
    with pytest.raises(TranscricaoIndisponivel):
        TranscritorGHEOffline().transcrever("bloco qualquer")
    with pytest.raises(TranscricaoIndisponivel):
        TranscritorCardOffline().transcrever("card qualquer", "titulo qualquer")
