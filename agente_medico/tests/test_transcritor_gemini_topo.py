from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.adaptadores.transcritor_gemini_topo import (
    TranscritorGeminiTopo,
    _parsear_envelope,
)
from agente_medico.motor.tipos import EnvelopeVerbatim
from agente_medico.tests.test_transcritor_topo import GABARITO_003BV

# _ALVO aponta para transcritor_gemini.requests.post (não
# transcritor_gemini_topo) porque a cascata HTTP (_chamar_gemini) mora no
# adaptador FDS e é REUSADA por import intra-pacote — é a mesma função, o
# mesmo ponto de mock, molde test_transcritor_gemini_pgr.py.
_ALVO = "agente_medico.adaptadores.transcritor_gemini.requests.post"

_PAYLOAD_003BV = {
    "validade_textos": ["FEVEREIRO 2023", "FEVEREIRO 2024", "FEVEREIRO 2025"],
    "responsavel_tecnico": "Elisângela Alves Faria",
    "titulo_rt": "Eng. Ambiental e de Segurança do Trabalho",
    "registro_profissional": "CREA – 1016192983D-GO",
}


def _resposta_200(payload: dict[str, Any], finish_reason: str = "STOP") -> Mock:
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "candidates": [
            {
                "content": {"parts": [{"text": json.dumps(payload)}]},
                "finishReason": finish_reason,
            }
        ]
    }
    return resp


def test_parsear_envelope_json_canonico_bate_com_gabarito_003bv() -> None:
    envelope = _parsear_envelope(json.dumps(_PAYLOAD_003BV))
    assert envelope == GABARITO_003BV


def test_parsear_envelope_com_markdown_fence_e_limpo() -> None:
    texto = f"```json\n{json.dumps(_PAYLOAD_003BV)}\n```"
    envelope = _parsear_envelope(texto)
    assert envelope == GABARITO_003BV


def test_parsear_envelope_campos_ausentes_ou_null_viram_vazio() -> None:
    payload: dict[str, Any] = {
        "validade_textos": None,
        "responsavel_tecnico": None,
        "titulo_rt": None,
    }
    envelope = _parsear_envelope(json.dumps(payload))
    assert envelope == EnvelopeVerbatim(
        validade_textos=(),
        responsavel_tecnico="",
        titulo_rt="",
        registro_profissional="",
    )
    assert isinstance(envelope.validade_textos, tuple)


def test_sem_chave_nao_chama_http_e_levanta_transcricao_indisponivel() -> None:
    with patch(_ALVO) as mock_post:
        cliente = TranscritorGeminiTopo(chave="")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    mock_post.assert_not_called()
    assert exc.value.motivo == "CHAVE_API_GOOGLE ausente"


def test_cascata_sem_resposta_levanta_transcricao_indisponivel() -> None:
    with patch(
        "agente_medico.adaptadores.transcritor_gemini_topo._chamar_gemini",
        return_value=None,
    ):
        cliente = TranscritorGeminiTopo(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert exc.value.motivo == "cascata Gemini sem resposta íntegra (200 + STOP)"


def test_resposta_nao_json_levanta_transcricao_indisponivel() -> None:
    resp = Mock(status_code=200)
    resp.json.return_value = {
        "candidates": [
            {
                "content": {"parts": [{"text": "isso nao e json {{{"}]},
                "finishReason": "STOP",
            }
        ]
    }
    with patch(_ALVO, return_value=resp):
        cliente = TranscritorGeminiTopo(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert exc.value.motivo.startswith("JSON inválido:")


def test_integracao_mockada_transcrever_bate_com_gabarito_003bv() -> None:
    with patch(_ALVO, return_value=_resposta_200(_PAYLOAD_003BV)):
        cliente = TranscritorGeminiTopo(chave="fake")
        envelope = cliente.transcrever("texto qualquer do topo")
    assert envelope == GABARITO_003BV
