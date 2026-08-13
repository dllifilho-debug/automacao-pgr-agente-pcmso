from __future__ import annotations

import json
import os
from datetime import date
from pathlib import Path
from typing import Any
from unittest.mock import Mock, patch

import pytest
import requests

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel, TranscritorGemini
from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.extracao_fds import extrair_texto_fds
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import FDS, GHEPGR, PGR, BlocoVerbatim, MembroVerbatim, ProdutoQuimico
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_fds import gate_forma, transcrever_fds
from agente_medico.tests.fixtures.fds_t65 import adesivo_pvc_tigre, cimento_ciplan, tinta_acrilica

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
# Núcleo — mock de HTTP, sem rede real.
# ---------------------------------------------------------------------------


def test_parseia_json_em_blocoverbatim() -> None:
    payload = {
        "blocos": [
            {"faixa": "1 - 5", "membros": [{"cas": "64-17-5", "nome": "Etanol"}]},
        ]
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")

    assert resultado == (
        BlocoVerbatim(faixa="1 - 5", membros=(MembroVerbatim(cas="64-17-5", nome="Etanol"),)),
    )


def test_bloco_multi_cas_vira_multiplos_membros_mesma_faixa() -> None:
    payload = {
        "blocos": [
            {
                "faixa": "0,2 – 0,05",
                "membros": [
                    {"cas": "2634-33-5", "nome": "1,2-benzotiazolin-3-ona"},
                    {"cas": "55965-84-9", "nome": "5-cloro-2-metil-2H-isotiazole-3-ona"},
                ],
            }
        ]
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")

    assert len(resultado) == 1
    assert resultado[0].faixa == "0,2 – 0,05"
    assert len(resultado[0].membros) == 2


def test_cascata_primeiro_modelo_falha_segundo_responde() -> None:
    payload = {"blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3", "nome": "X"}]}]}
    resp_erro = Mock(status_code=500)
    resp_ok = _resposta_200(payload)
    chamadas: list[str] = []

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        chamadas.append(url)
        return resp_erro if len(chamadas) == 1 else resp_ok

    with patch(_ALVO, side_effect=_post):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")

    assert len(chamadas) == 2
    assert "gemini-2.5-flash" in chamadas[0]
    assert "gemini-2.5-pro" in chamadas[1]
    assert resultado[0].membros[0].cas == "1-2-3"


def test_todos_os_modelos_falham_levanta_transcricao_indisponivel() -> None:
    with patch(_ALVO, return_value=Mock(status_code=500)):
        cliente = TranscritorGemini(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert exc.value.motivo == "cascata Gemini sem resposta íntegra (200 + STOP)"


def test_todos_os_modelos_max_tokens_levanta_transcricao_indisponivel() -> None:
    payload = {"blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3", "nome": "X"}]}]}
    with patch(_ALVO, return_value=_resposta_200(payload, finish_reason="MAX_TOKENS")):
        cliente = TranscritorGemini(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert "resposta íntegra" in exc.value.motivo


def test_primeiro_modelo_max_tokens_segundo_stop_cascata_continua() -> None:
    payload_truncado = {"blocos": [{"faixa": "0 - 0", "membros": [{"cas": "0-0-0", "nome": "Truncado"}]}]}
    payload_ok = {"blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3", "nome": "X"}]}]}
    chamadas: list[str] = []

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        chamadas.append(url)
        if len(chamadas) == 1:
            return _resposta_200(payload_truncado, finish_reason="MAX_TOKENS")
        return _resposta_200(payload_ok)

    with patch(_ALVO, side_effect=_post):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")

    assert len(chamadas) == 2
    assert resultado[0].membros[0].cas == "1-2-3"


def test_excecao_de_rede_passa_para_o_proximo_modelo() -> None:
    payload = {"blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3", "nome": "X"}]}]}
    chamadas: list[str] = []

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        chamadas.append(url)
        if len(chamadas) == 1:
            raise requests.exceptions.Timeout("timeout")
        return _resposta_200(payload)

    with patch(_ALVO, side_effect=_post):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")

    assert len(chamadas) == 2
    assert resultado != ()


def test_cas_oculto_vira_string_vazia() -> None:
    payload = {
        "blocos": [{"faixa": "0 - 1", "membros": [{"cas": "", "nome": "Segredo Industrial"}]}]
    }
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")
    assert resultado[0].membros[0].cas == ""


def test_cas_ausente_da_chave_json_vira_string_vazia() -> None:
    payload = {"blocos": [{"faixa": "0 - 1", "membros": [{"nome": "Segredo Industrial"}]}]}
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")
    assert resultado[0].membros[0].cas == ""


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
        cliente = TranscritorGemini(chave="fake")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    assert exc.value.motivo.startswith("JSON inválido:")


def test_blocos_vazio_e_resultado_legitimo_sem_excecao() -> None:
    payload: dict[str, Any] = {"blocos": []}
    with patch(_ALVO, return_value=_resposta_200(payload)):
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")
    assert resultado == ()


def test_json_com_markdown_fence_e_limpo() -> None:
    payload = {"blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3", "nome": "X"}]}]}
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
        cliente = TranscritorGemini(chave="fake")
        resultado = cliente.transcrever("texto qualquer")
    assert resultado[0].membros[0].cas == "1-2-3"


def test_sem_chave_nao_chama_http_e_levanta_transcricao_indisponivel() -> None:
    with patch(_ALVO) as mock_post:
        cliente = TranscritorGemini(chave="")
        with pytest.raises(TranscricaoIndisponivel) as exc:
            cliente.transcrever("texto qualquer")
    mock_post.assert_not_called()
    assert exc.value.motivo == "CHAVE_API_GOOGLE ausente"


def test_payload_usa_temperature_zero() -> None:
    payload: dict[str, Any] = {"blocos": []}
    capturado: dict[str, Any] = {}

    def _post(url: str, json: dict[str, Any], timeout: int) -> Mock:
        capturado.update(json)
        return _resposta_200(payload)

    with patch(_ALVO, side_effect=_post):
        TranscritorGemini(chave="fake").transcrever("texto qualquer")

    assert capturado["generationConfig"]["temperature"] == 0


# ---------------------------------------------------------------------------
# Ao vivo (marcador requer_api) — API real do Gemini, skip sem CHAVE_API_GOOGLE.
#
# Gabarito completo (cas+concentracao via fds_t65.py, D-ARQ-34 fatia 3) só
# existe para 3 dos 6 PDFs de fds_originais/: Ciplan, Adesivo Tigre, Tinta
# Acrílica. Leinertex/Massa-Corrida/Amanco não têm gabarito comparável nesta
# fatia (fds_verbatim_leinertex.py cobre só os blocos multi-CAS, não a FDS
# inteira) — fora do recorte deste teste ao vivo; reportado ao Arquiteto no
# fechamento em vez de fixture inventada aqui.
# ---------------------------------------------------------------------------

def requer_api(fn):
    """Ao vivo: pula sem chave (skipif) E declara-se isento da blindagem
    de rede do conftest.py (marcador ao_vivo, 003.EW)."""
    fn = pytest.mark.ao_vivo(fn)
    return pytest.mark.skipif(
        not os.environ.get("CHAVE_API_GOOGLE"),
        reason="CHAVE_API_GOOGLE ausente — teste ao vivo do transcritor Gemini indisponível",
    )(fn)

_PASTA = Path("fds_originais")
_CASOS = {
    "ciplan": (_PASTA / "01 - FISPQ_cimento - Ciplan.pdf", cimento_ciplan),
    "tigre": (_PASTA / "270 -FISPQ -  Adesivo PVC Incolor Tigre.pdf", adesivo_pvc_tigre),
    "tinta": (_PASTA / "tinta_acrilica.pdf", tinta_acrilica),
}


def _pgr_com_fds(fds: FDS) -> PGR:
    return PGR(
        validade=date(2026, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="G1",
                nome="GHE 1",
                cargos=("c",),
                riscos=(),
                epis=(),
                produtos_quimicos=(ProdutoQuimico(nome="Produto", fds=fds),),
                psicossocial=False,
            ),
        ),
    )


@requer_api
@pytest.mark.parametrize("nome_caso", sorted(_CASOS))
def test_transcricao_ao_vivo_bate_cas_e_concentracao_do_gabarito(nome_caso: str) -> None:
    caminho, gabarito_fn = _CASOS[nome_caso]
    assert caminho.exists(), f"PDF ausente: {caminho}"

    protocolo_dir = Path(__file__).parent.parent / "protocolo"
    proto = carregar(protocolo_dir)
    indice = construir_indice_cas(proto.vocabulario.agentes)

    texto = extrair_texto_fds(caminho)
    assert texto is not None

    cliente = TranscritorGemini()
    candidato = transcrever_fds(texto, cliente)
    aprovados, pendencias = gate_forma(candidato)
    assert pendencias == (), f"gate de forma reprovou blocos: {pendencias}"

    fds = montar_fds(aprovados)
    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), indice)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None

    comps = resolvido.composicao
    gabarito = gabarito_fn()
    assert len(comps) == len(gabarito)
    for c, g in zip(comps, gabarito):
        assert c.cas == g.cas
        assert c.concentracao == g.concentracao
        # nome NÃO é comparado por == : transcrição ao vivo pode variar
        # grafia/espaçamento em relação ao gabarito digitado à mão.
