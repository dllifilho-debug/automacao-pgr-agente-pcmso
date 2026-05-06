"""
tests/test_extracao_fallback.py

Testes para a Camada 0 (Gemini) de extrair_pgr_com_fallback()
em modules/modulo_pcmso.py.

Estratégia de mock:
- extrair_pgr_com_fallback é importada UMA VEZ no topo (evita re-import de pandas/numpy)
- sys.modules["streamlit"] é patchado em cada teste durante a CHAMADA da função
  (funciona porque o import do streamlit ocorre dentro do try/except da função)
- utils.ia_client.extrair_pgr_estruturado_via_gemini é patchada diretamente
"""

import sys
import pytest
from unittest.mock import patch, MagicMock

# ── Import único — evita re-import de pandas/numpy em cada teste ──────────────
from modules.modulo_pcmso import extrair_pgr_com_fallback


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _make_st_mock(chave: str = "") -> MagicMock:
    """Cria mock de streamlit com st.secrets.get configurado."""
    st_mock = MagicMock()
    st_mock.secrets.get = MagicMock(
        side_effect=lambda key, default="": chave if key == "CHAVE_API_GOOGLE" else default
    )
    return st_mock


_GHES_FAKE_3 = [
    {
        "ghe": "GHE 01 - Estrutura fôrma de pilar",
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

_GHES_FAKE_1 = [_GHES_FAKE_3[0]]   # apenas 1 GHE → deve fazer fallback


# ─── Testes ───────────────────────────────────────────────────────────────────

class TestCamada0GeminiUsadaQuandoChaveDisponivel:

    def test_fonte_gemini_retornada(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")
        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=_GHES_FAKE_3,
            ):
                dados, fonte = extrair_pgr_com_fallback("texto do pgr qualquer")

        assert fonte == "gemini", f"Esperado fonte='gemini', obtido '{fonte}'"

    def test_dados_sao_os_do_gemini(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")
        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=_GHES_FAKE_3,
            ):
                dados, fonte = extrair_pgr_com_fallback("texto")

        assert dados is _GHES_FAKE_3
        assert len(dados) == 3

    def test_gemini_recebe_texto_e_chave_corretos(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")
        chamadas = []

        def capturar(texto, chave):
            chamadas.append((texto, chave))
            return _GHES_FAKE_3

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                side_effect=capturar,
            ):
                extrair_pgr_com_fallback("PGR TEXTO REAL")

        assert chamadas, "Gemini não foi chamado"
        assert chamadas[0][0] == "PGR TEXTO REAL"
        assert chamadas[0][1] == "CHAVE_VALIDA_123"


class TestCamada0PuladaSemChave:

    def test_sem_chave_nao_chama_gemini(self):
        st_mock = _make_st_mock(chave="")   # chave vazia
        gemini_mock = MagicMock(return_value=_GHES_FAKE_3)

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                gemini_mock,
            ):
                _, fonte = extrair_pgr_com_fallback("texto")

        gemini_mock.assert_not_called()
        assert fonte != "gemini", "Sem chave, fonte não deveria ser 'gemini'"

    def test_sem_streamlit_nao_lanca_excecao(self):
        """Se streamlit levantar ImportError, o sistema continua normalmente."""
        # Simula ImportError ao tentar importar streamlit
        with patch.dict(sys.modules, {"streamlit": None}):
            # sys.modules[key] = None faz 'import streamlit' lançar ImportError
            dados, fonte = extrair_pgr_com_fallback("texto pgr")

        assert isinstance(dados, list)
        assert isinstance(fonte, str)
        assert fonte != "gemini"


class TestCamada0FalhaSilenciosaParaRegex:

    def test_excecao_na_gemini_nao_propaga(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                side_effect=RuntimeError("API down"),
            ):
                # Não deve lançar exceção
                dados, fonte = extrair_pgr_com_fallback("texto pgr")

        assert fonte != "gemini", "Após falha da API, fonte não deve ser 'gemini'"

    def test_excecao_retorna_tupla_valida(self):
        """Mesmo com Gemini falhando, retorna (list, str) — nunca None."""
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                side_effect=Exception("timeout"),
            ):
                resultado = extrair_pgr_com_fallback("texto pgr")

        assert isinstance(resultado, tuple)
        assert len(resultado) == 2
        dados, fonte = resultado
        assert isinstance(dados, list)
        assert isinstance(fonte, str)


class TestCamada0PuladaSeMenosDe2GHE:

    def test_1_ghe_faz_fallback(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=_GHES_FAKE_1,   # 1 GHE < threshold
            ):
                _, fonte = extrair_pgr_com_fallback("texto")

        assert fonte != "gemini", (
            "Com apenas 1 GHE do Gemini, deveria ter feito fallback para regex"
        )

    def test_lista_vazia_faz_fallback(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=[],
            ):
                _, fonte = extrair_pgr_com_fallback("texto")

        assert fonte != "gemini"

    def test_none_faz_fallback(self):
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=None,
            ):
                _, fonte = extrair_pgr_com_fallback("texto")

        assert fonte != "gemini"

    def test_2_ghes_e_suficiente(self):
        """Exatamente 2 GHEs deve ser aceito (threshold >= 2)."""
        st_mock = _make_st_mock(chave="CHAVE_VALIDA_123")
        dois_ghes = _GHES_FAKE_3[:2]

        with patch.dict(sys.modules, {"streamlit": st_mock}):
            with patch(
                "utils.ia_client.extrair_pgr_estruturado_via_gemini",
                return_value=dois_ghes,
            ):
                dados, fonte = extrair_pgr_com_fallback("texto")

        assert fonte == "gemini"
        assert len(dados) == 2
