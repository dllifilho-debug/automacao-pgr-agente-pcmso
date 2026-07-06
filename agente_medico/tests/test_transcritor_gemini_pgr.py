from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.extracao_pgr import extrair_texto_pgr, recortar_blocos_ghe
from agente_medico.motor.transcritor_pgr import gate_forma_ghe

# _ALVO aponta para transcritor_gemini.requests.post (não
# transcritor_gemini_pgr) porque a cascata HTTP (_chamar_gemini) mora no
# adaptador FDS e é REUSADA por import intra-pacote — é a mesma função, o
# mesmo ponto de mock, molde test_transcritor_gemini.py.
_ALVO = "agente_medico.adaptadores.transcritor_gemini.requests.post"


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


# ---------------------------------------------------------------------------
# Núcleo — mock de HTTP, sem rede real. Cascata/finishReason já cobertos em
# test_transcritor_gemini.py (mesma função _chamar_gemini reusada) — não
# re-testados aqui.
# ---------------------------------------------------------------------------


def test_json_completo_vira_gheverbatim() -> None:
    payload = {
        "nome": "Pintura",
        "cargos": ["pintor", "meio oficial de pintor", "servente"],
        "riscos": [
            {"agente": "Ruído", "quantificacao": "78,8 dB(A)", "fonte_geradora": "Maquinas e equipamentos"},
        ],
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiGHE(chave="fake")
        ghe = cliente.transcrever("SETOR/FUNÇÃO Pintura/ pintor\n...")

    assert ghe.nome == "Pintura"
    assert ghe.cargos == ("pintor", "meio oficial de pintor", "servente")
    assert isinstance(ghe.cargos, tuple)
    assert len(ghe.riscos) == 1
    risco = ghe.riscos[0]
    assert risco.agente == "Ruído"
    assert risco.quantificacao == "78,8 dB(A)"
    assert risco.fonte_geradora == "Maquinas e equipamentos"
    assert isinstance(ghe.riscos, tuple)


def test_multi_agente_mesmo_et_vira_riscos_separados_com_fonte_copiada() -> None:
    # Literais medidos 003.BK/003.BM (GHE 13/14 - Pintura, pág. 71).
    fonte = "Thinner/Zarcão"
    payload = {
        "nome": "Pintura",
        "cargos": [],
        "riscos": [
            {"agente": "Etanol", "quantificacao": "4,4 ppm", "fonte_geradora": fonte},
            {"agente": "Acetato de Etila", "quantificacao": "1 ppm", "fonte_geradora": fonte},
            {"agente": "Tolueno", "quantificacao": "6,3 ppm", "fonte_geradora": fonte},
        ],
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiGHE(chave="fake")
        ghe = cliente.transcrever("texto qualquer")

    assert len(ghe.riscos) == 3
    assert {r.fonte_geradora for r in ghe.riscos} == {fonte}
    assert {r.agente for r in ghe.riscos} == {"Etanol", "Acetato de Etila", "Tolueno"}


def test_campos_ausentes_viram_string_vazia_ou_tupla_vazia() -> None:
    payload: dict[str, Any] = {
        "nome": "Estrutura de concreto armado",
        "riscos": [{"agente": "Ruído"}],
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiGHE(chave="fake")
        ghe = cliente.transcrever("texto qualquer")

    assert ghe.cargos == ()
    assert ghe.riscos[0].quantificacao == ""
    assert ghe.riscos[0].fonte_geradora == ""


def test_riscos_vazio_e_resultado_legitimo_sem_excecao() -> None:
    payload = {"nome": "Estrutura de concreto armado", "cargos": [], "riscos": []}
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiGHE(chave="fake")
        ghe = cliente.transcrever("texto qualquer")

    assert ghe.riscos == ()


def test_json_com_markdown_fence_e_limpo() -> None:
    payload = {"nome": "Pintura", "cargos": [], "riscos": []}
    resp = Mock(status_code=200)
    resp.json.return_value = {
        "candidates": [
            {
                "content": {"parts": [{"text": f"```json\n{json.dumps(payload)}\n```"}]},
                "finishReason": "STOP",
            }
        ]
    }
    with patch(_ALVO, return_value=resp):
        cliente = TranscritorGeminiGHE(chave="fake")
        ghe = cliente.transcrever("texto qualquer")
    assert ghe.nome == "Pintura"


def test_json_invalido_levanta_transcricao_indisponivel() -> None:
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
        cliente = TranscritorGeminiGHE(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert exc.value.motivo.startswith("JSON inválido:")


def test_sem_chave_nao_chama_http_e_levanta_transcricao_indisponivel() -> None:
    with patch(_ALVO) as mock_post:
        cliente = TranscritorGeminiGHE(chave="")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    mock_post.assert_not_called()
    assert exc.value.motivo == "CHAVE_API_GOOGLE ausente"


def test_prompt_enviado_contem_o_texto_do_bloco() -> None:
    payload = {"nome": "Pintura", "cargos": [], "riscos": []}
    capturado: dict[str, Any] = {}
    bloco = "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente\nET 51 Tolueno 6,3 ppm"

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        capturado.update(json)
        return _resposta_200(payload)

    with patch(_ALVO, side_effect=_post):
        TranscritorGeminiGHE(chave="fake").transcrever(bloco)

    prompt_enviado = capturado["contents"][0]["parts"][0]["text"]
    assert bloco in prompt_enviado


# ---------------------------------------------------------------------------
# Ao vivo (marcador requer_api + requer_pdfs) — API real do Gemini e PDF real
# do Viverde, skip se ausentes. Molde requer_api de test_transcritor_gemini.py
# + requer_pdfs de test_transcritor_pgr.py.
# ---------------------------------------------------------------------------

requer_api = pytest.mark.skipif(
    not os.environ.get("CHAVE_API_GOOGLE"),
    reason="CHAVE_API_GOOGLE ausente — teste ao vivo do transcritor Gemini-GHE indisponível",
)

_CAMINHO_PGR = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")
requer_pdfs = pytest.mark.skipif(
    not _CAMINHO_PGR.exists(),
    reason="matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf ausente; teste ao vivo indisponível",
)


@requer_api
@requer_pdfs
def test_transcricao_ao_vivo_bloco_pintura_thinner_zarcao() -> None:
    paginas = extrair_texto_pgr(_CAMINHO_PGR)
    blocos = recortar_blocos_ghe(paginas)
    bloco = next((b for b in blocos if "Thinner" in b or "Zarc" in b), None)
    assert bloco is not None, "bloco com Thinner/Zarcão não encontrado no recorte"

    cliente = TranscritorGeminiGHE()
    ghe = cliente.transcrever(bloco)

    assert "Pintura" in ghe.nome
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert pendencias == (), f"gate de forma reprovou o GHE: {pendencias}"
    assert aprovados == (ghe,)

    agentes = {r.agente.strip() for r in ghe.riscos}
    assert agentes >= {"Etanol", "Acetato de Etila", "Tolueno"}

    # Literais medidos 003.BK/003.BM, pág. 71 (GHE Pintura). Comparação
    # tolerante só a whitespace (colapsado), nunca a conteúdo — a transcrição
    # ao vivo pode variar espaçamento, nunca o valor em si.
    esperado = {
        "Etanol": "4,4 ppm",
        "Acetato de Etila": "1 ppm",
        "Tolueno": "6,3 ppm",
    }
    for risco in ghe.riscos:
        agente = risco.agente.strip()
        if agente in esperado:
            quantificacao = " ".join(risco.quantificacao.split())
            assert quantificacao == esperado[agente]
            assert risco.fonte_geradora.strip() == "Thinner/Zarcão"
