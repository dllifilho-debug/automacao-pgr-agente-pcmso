from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.adaptadores.transcritor_gemini_card import TranscritorGeminiCard
from agente_medico.motor.extracao_pgr import (
    extrair_texto_pgr,
    recortar_cards_cargo,
    recuperar_titulos_cargo,
)
from agente_medico.motor.transcritor_pgr import gate_forma_ghe

# _ALVO aponta para transcritor_gemini.requests.post (não
# transcritor_gemini_card) porque a cascata HTTP (_chamar_gemini) mora no
# adaptador FDS e é REUSADA por import intra-pacote — é a mesma função, o
# mesmo ponto de mock, molde test_transcritor_gemini_pgr.py.
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
    # Literais calibrados no PASSO 0 (UFGD card [0], titulo "13.1 Advogado"):
    # nome = "Setor Jurídico", risco ergonômico agente="Postura inadequada"/
    # fonte_geradora="Mobiliário inadequado".
    payload = {
        "nome": "Setor Jurídico",
        "cargos": ["Advogado"],
        "riscos": [
            {"agente": "Postura inadequada", "quantificacao": "", "fonte_geradora": "Mobiliário inadequado"},
        ],
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiCard(chave="fake")
        ghe = cliente.transcrever("Lotação: Escala de Trabalho: Qtde:\n...", "13.1 Advogado")

    assert ghe.nome == "Setor Jurídico"
    assert ghe.cargos == ("Advogado",)
    assert isinstance(ghe.cargos, tuple)
    assert len(ghe.riscos) == 1
    risco = ghe.riscos[0]
    assert risco.agente == "Postura inadequada"
    assert risco.quantificacao == ""
    assert risco.fonte_geradora == "Mobiliário inadequado"
    assert isinstance(ghe.riscos, tuple)


def test_riscos_vazio_e_resultado_legitimo_e_gate_aprova() -> None:
    # Composição — regressão 003.DG-3: card todo-N/A (riscos=[]) é forma
    # legítima e o gate NÃO reprova sozinho por ausência de risco.
    payload = {"nome": "Setor Jurídico", "cargos": ["Advogado"], "riscos": []}
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiCard(chave="fake")
        ghe = cliente.transcrever("texto qualquer", "13.1 Advogado")

    assert ghe.riscos == ()
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == (ghe,)
    assert pendencias == ()


def test_sem_chave_nao_chama_http_e_levanta_transcricao_indisponivel() -> None:
    with patch(_ALVO) as mock_post:
        cliente = TranscritorGeminiCard(chave="")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer", "13.1 Advogado")
    mock_post.assert_not_called()
    assert exc.value.motivo == "CHAVE_API_GOOGLE ausente"


def test_resposta_nao_integra_levanta_transcricao_indisponivel() -> None:
    # 003.EW: _chamar_gemini agora acumula um motivo por modelo na mensagem
    # (Parte B) — a mensagem deixa de ser um match exato e passa a começar
    # com o mesmo prefixo de sempre.
    resp = Mock(status_code=503)
    with patch(_ALVO, return_value=resp):
        cliente = TranscritorGeminiCard(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer", "13.1 Advogado")
    assert exc.value.motivo.startswith("cascata Gemini sem resposta íntegra (200 + STOP)")


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
        cliente = TranscritorGeminiCard(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer", "13.1 Advogado")
    assert exc.value.motivo.startswith("JSON inválido:")


def test_campos_ausentes_viram_string_vazia_ou_tupla_vazia() -> None:
    payload: dict[str, Any] = {
        "nome": "Setor Jurídico",
        "riscos": [{"agente": "Postura inadequada"}],
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGeminiCard(chave="fake")
        ghe = cliente.transcrever("texto qualquer", "13.1 Advogado")

    assert ghe.cargos == ()
    assert ghe.riscos[0].quantificacao == ""
    assert ghe.riscos[0].fonte_geradora == ""


def test_prompt_enviado_contem_o_card_e_o_titulo() -> None:
    payload = {"nome": "Setor Jurídico", "cargos": [], "riscos": []}
    capturado: dict[str, Any] = {}
    card = "Lotação: Escala de Trabalho: Qtde:\nSetor Jurídico 40hs/ semana 2 – Efetivos"
    titulo = "13.1 Advogado"

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        capturado.update(json)
        return _resposta_200(payload)

    with patch(_ALVO, side_effect=_post):
        TranscritorGeminiCard(chave="fake").transcrever(card, titulo)

    prompt_enviado = capturado["contents"][0]["parts"][0]["text"]
    assert card in prompt_enviado
    assert titulo in prompt_enviado


# ---------------------------------------------------------------------------
# Ao vivo (marcador requer_api + requer_pdfs) — API real do Gemini e PDFs
# reais EBSERH, skip se ausentes. Molde requer_api de
# test_transcritor_gemini.py + requer_pdfs de test_transcritor_pgr.py.
# ---------------------------------------------------------------------------

def requer_api(fn):
    """Ao vivo: pula sem chave (skipif) E declara-se isento da blindagem
    de rede do conftest.py (marcador ao_vivo, 003.EW)."""
    fn = pytest.mark.ao_vivo(fn)
    return pytest.mark.skipif(
        not os.environ.get("CHAVE_API_GOOGLE"),
        reason="CHAVE_API_GOOGLE ausente — teste ao vivo do transcritor Gemini-card indisponível",
    )(fn)

_CAMINHO_UFGD = Path("matrizes_originais/PGR_EBSERH_UFGD_v7.pdf")
_CAMINHO_HUMAP = Path("matrizes_originais/PGR_EBSERH_HUMAP.pdf")

requer_pdfs = pytest.mark.skipif(
    not (_CAMINHO_UFGD.exists() and _CAMINHO_HUMAP.exists()),
    reason="PDFs EBSERH (UFGD-v7/HUMAP) ausentes; teste ao vivo indisponível",
)


@requer_api
@requer_pdfs
def test_transcricao_ao_vivo_ufgd_card_0_titulo_13_1_advogado() -> None:
    paginas = extrair_texto_pgr(_CAMINHO_UFGD)
    cards = recortar_cards_cargo(paginas)
    titulos = recuperar_titulos_cargo(paginas)
    assert titulos[0] == "13.1 Advogado"

    cliente = TranscritorGeminiCard()
    ghe = cliente.transcrever(cards[0], titulos[0])

    aprovados, pendencias = gate_forma_ghe([ghe])
    assert pendencias == (), f"gate de forma reprovou o GHE: {pendencias}"
    assert aprovados == (ghe,)

    assert ghe.cargos == ("Advogado",)
    # Literal de lotação medido no PASSO 0 (linha seguinte à âncora de
    # labels); comparação tolerante só a whitespace colapsado (molde 003.BO)
    # — a transcrição ao vivo pode variar espaçamento, nunca o conteúdo.
    literal_lotacao = "Setor Jurídico"
    nome_colapsado = " ".join(ghe.nome.split())
    assert literal_lotacao in nome_colapsado


@requer_api
@requer_pdfs
def test_transcricao_ao_vivo_humap_card_0_titulo_vazio() -> None:
    paginas = extrair_texto_pgr(_CAMINHO_HUMAP)
    cards = recortar_cards_cargo(paginas)
    titulos = recuperar_titulos_cargo(paginas)
    assert titulos[0] == ""

    cliente = TranscritorGeminiCard()
    ghe = cliente.transcrever(cards[0], titulos[0])

    aprovados, pendencias = gate_forma_ghe([ghe])
    assert pendencias == (), f"gate de forma reprovou o GHE: {pendencias}"
    assert aprovados == (ghe,)

    # Gabaritos medidos no PASSO 0 (linha "SetorJurídico: ADVOGADO 40hs/semana
    # VerTab."): cargo verbatim sem mudar caixa (regra 2b do prompt); nome com
    # desglue bounded, comparação tolerante só a whitespace colapsado.
    assert ghe.cargos == ("ADVOGADO",)
    nome_colapsado = " ".join(ghe.nome.split())
    assert "Setor Jurídico" in nome_colapsado
