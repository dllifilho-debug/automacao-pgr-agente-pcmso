"""
tests/test_camada0_app.py

Testes da Camada 0 Gemini integrada ao caminho principal de app.py
(via helper tentar_gemini_para_ghes_sem_cargo + lógica condicional).

Estratégia: testa o helper isolado e simula o fluxo de app.py
(decisão Gemini-vs-distribuição) sem importar app.py inteiro,
já que ele tem chamadas top-level de Streamlit.
"""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest

from modules.modulo_pcmso import tentar_gemini_para_ghes_sem_cargo


_GHES_FAKE_3 = [
    {
        "ghe": "GHE 01 - Estrutura fôrma",
        "cargos": ["Carpinteiro", "Servente"],
        "riscos_mapeados": [{"nome_agente": "Ruído", "perigo_especifico": ""}],
        "exames": [],
    },
    {
        "ghe": "GHE 02 - Armação",
        "cargos": ["Armador", "Servente"],
        "riscos_mapeados": [{"nome_agente": "Ruído", "perigo_especifico": ""}],
        "exames": [],
    },
    {
        "ghe": "GHE 03 - Alvenaria",
        "cargos": ["Pedreiro", "Servente"],
        "riscos_mapeados": [{"nome_agente": "Poeira de cimento", "perigo_especifico": ""}],
        "exames": [],
    },
]


def _st_mock_com_chave(chave: str = "") -> MagicMock:
    st_mock = MagicMock()
    st_mock.secrets.get = MagicMock(
        side_effect=lambda key, default="": chave if key == "CHAVE_API_GOOGLE" else default
    )
    return st_mock


# ──────────────────────────────────────────────────────────────────────────────
# Simulação do fluxo de app.py (decisão Gemini vs distribuição heurística)
# ──────────────────────────────────────────────────────────────────────────────

def _simular_fluxo_app(
    texto_pgr: str,
    cargos_sao_ghe_names: bool,
    distribuir_mock,
):
    """
    Reproduz a lógica condicional inserida em app.py (linhas ~578+):
      - Se _cargos_sao_apenas_ghe_names → tenta Gemini
      - Se Gemini falha → chama _distribuir_cargos_por_ghe
    """
    fonte = "local"
    dados_ghe = [{"ghe": "GHE 01", "cargos": ["GHE 01"]}]  # placeholder

    if cargos_sao_ghe_names:
        dados_ia, _fonte_ia = tentar_gemini_para_ghes_sem_cargo(texto_pgr)
        if _fonte_ia == "gemini" and dados_ia:
            dados_ghe = dados_ia
            fonte = "gemini"

        if fonte != "gemini":
            distribuir_mock(["Cargo A"], dados_ghe)

    return dados_ghe, fonte


# ──────────────────────────────────────────────────────────────────────────────
# Testes
# ──────────────────────────────────────────────────────────────────────────────

def test_gemini_ativado_quando_ghe_sem_cargos():
    st_mock = _st_mock_com_chave("CHAVE_VALIDA_123")
    distribuir_mock = MagicMock()

    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch(
            "utils.ia_client.extrair_pgr_estruturado_via_gemini",
            return_value=_GHES_FAKE_3,
        ):
            dados_ghe, fonte = _simular_fluxo_app(
                texto_pgr="texto qualquer",
                cargos_sao_ghe_names=True,
                distribuir_mock=distribuir_mock,
            )

    assert fonte == "gemini", f"Esperado fonte='gemini', obtido '{fonte}'"
    assert dados_ghe == _GHES_FAKE_3
    distribuir_mock.assert_not_called()


def test_gemini_nao_ativado_quando_cargos_reais():
    st_mock = _st_mock_com_chave("CHAVE_VALIDA_123")
    distribuir_mock = MagicMock()

    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch(
            "utils.ia_client.extrair_pgr_estruturado_via_gemini",
            return_value=_GHES_FAKE_3,
        ) as gemini_mock:
            dados_ghe, fonte = _simular_fluxo_app(
                texto_pgr="texto qualquer",
                cargos_sao_ghe_names=False,
                distribuir_mock=distribuir_mock,
            )

    assert fonte == "local"
    gemini_mock.assert_not_called()
    distribuir_mock.assert_not_called()


def test_fallback_para_distribuir_quando_gemini_falha():
    st_mock = _st_mock_com_chave("CHAVE_VALIDA_123")
    distribuir_mock = MagicMock()

    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch(
            "utils.ia_client.extrair_pgr_estruturado_via_gemini",
            side_effect=Exception("API down"),
        ):
            dados_ghe, fonte = _simular_fluxo_app(
                texto_pgr="texto qualquer",
                cargos_sao_ghe_names=True,
                distribuir_mock=distribuir_mock,
            )

    assert fonte != "gemini"
    distribuir_mock.assert_called_once()


def test_helper_le_chave_de_environ_quando_st_secrets_vazio():
    st_mock = _st_mock_com_chave("")
    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch.dict(os.environ, {"CHAVE_API_GOOGLE": "CHAVE_DO_ENV"}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=_GHES_FAKE_3,
            ) as gemini_mock:
                dados, fonte = tentar_gemini_para_ghes_sem_cargo("texto pgr")

    assert fonte == "gemini"
    assert dados == _GHES_FAKE_3
    gemini_mock.assert_called_once()
    args, _ = gemini_mock.call_args
    assert args[1] == "CHAVE_DO_ENV"


def test_helper_retorna_none_sem_chave():
    st_mock = _st_mock_com_chave("")
    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CHAVE_API_GOOGLE", None)
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
            ) as gemini_mock:
                dados, fonte = tentar_gemini_para_ghes_sem_cargo("texto pgr")

    assert dados is None
    assert fonte is None
    gemini_mock.assert_not_called()


def test_helper_retorna_none_quando_gemini_devolve_menos_de_2_ghes():
    st_mock = _st_mock_com_chave("CHAVE_X")
    with patch.dict(sys.modules, {"streamlit": st_mock}):
        with patch(
            "utils.ia_client.extrair_pgr_estruturado_via_gemini",
            return_value=[_GHES_FAKE_3[0]],
        ):
            dados, fonte = tentar_gemini_para_ghes_sem_cargo("texto pgr")

    assert dados is None
    assert fonte is None
