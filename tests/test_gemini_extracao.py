"""
tests/test_gemini_extracao.py

Testes unitários para extrair_pgr_estruturado_via_gemini() em utils/ia_client.py.
Todos os testes usam unittest.mock — nenhuma chamada real à API Gemini é feita.
"""

import json
import pytest
from unittest.mock import patch

from utils.ia_client import extrair_pgr_estruturado_via_gemini

# ─── Constantes de suporte ────────────────────────────────────────────────────

_CHAVE_FAKE = "CHAVE_FAKE_PARA_TESTES"

_JSON_VALIDO = json.dumps({
    "ghes": [
        {
            "numero": "01",
            "titulo": "Estrutura de concreto armado - Execução fôrma de pilar e laje",
            "cargos": ["Carpinteiro", "Meio Oficial de Carpinteiro", "Servente"],
            "riscos": ["Ruído", "Poeira de madeira", "Trabalho em altura"],
        },
        {
            "numero": "02",
            "titulo": "Estrutura de concreto armado - Armação",
            "cargos": ["Armador", "Meio Oficial de Armador", "Servente"],
            "riscos": ["Ruído", "Trabalho em altura"],
        },
    ]
})

_JSON_GHE_UNICO = json.dumps({
    "ghes": [
        {
            "numero": "7",        # número sem padding — deve virar "07"
            "titulo": "Alvenaria interna e externa",
            "cargos": ["Pedreiro", "Servente"],
            "riscos": ["Ruído", "Poeira de cimento", "Eletricidade"],
        }
    ]
})

# ─── Testes ───────────────────────────────────────────────────────────────────

class TestExtracaoSchemaValido:
    """Mock retorna JSON bem-formado → verifica estrutura do retorno."""

    def test_retorna_lista_nao_nula(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        assert resultado is not None
        assert isinstance(resultado, list)

    def test_quantidade_de_ghes(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        assert len(resultado) == 2

    def test_campos_obrigatorios_presentes(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        campos = {"ghe", "cargos", "riscos_mapeados", "exames"}
        for item in resultado:
            assert campos.issubset(item.keys()), (
                f"Campos faltando em {item}: {campos - set(item.keys())}"
            )

    def test_campo_ghe_prefixo_correto(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        assert resultado[0]["ghe"] == "GHE 01 - Estrutura de concreto armado - Execução fôrma de pilar e laje"
        assert resultado[1]["ghe"] == "GHE 02 - Estrutura de concreto armado - Armação"

    def test_cargos_preservados(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        assert resultado[0]["cargos"] == ["Carpinteiro", "Meio Oficial de Carpinteiro", "Servente"]

    def test_exames_lista_vazia(self):
        """exames deve ser sempre lista vazia — resolvido depois pelo agente IA."""
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", _CHAVE_FAKE)
        for item in resultado:
            assert item["exames"] == [], (
                f"exames deveria ser [] mas é {item['exames']}"
            )


class TestExtracaoFallbackSemChave:
    """Sem chave API → retorna None sem chamar a API."""

    def test_chave_vazia_retorna_none(self):
        with patch("utils.ia_client._chamar_gemini") as mock_api:
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", "")
        assert resultado is None
        mock_api.assert_not_called()

    def test_chave_none_retorna_none(self):
        with patch("utils.ia_client._chamar_gemini") as mock_api:
            # None é inválido como chave — deve retornar None sem chamar API
            resultado = extrair_pgr_estruturado_via_gemini("texto qualquer", "")
        assert resultado is None
        mock_api.assert_not_called()


class TestExtracaoFallbackJsonInvalido:
    """API responde mas JSON é malformado → retorna None, não lança exceção."""

    def test_json_malformado(self):
        with patch("utils.ia_client._chamar_gemini", return_value="isso nao e json {{{"):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None

    def test_json_sem_chave_ghes(self):
        """JSON válido mas sem a chave 'ghes'."""
        payload = json.dumps({"ghe_list": []})
        with patch("utils.ia_client._chamar_gemini", return_value=payload):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None

    def test_json_ghes_vazio(self):
        """JSON com 'ghes': [] → retorna None (nenhum GHE extraído)."""
        payload = json.dumps({"ghes": []})
        with patch("utils.ia_client._chamar_gemini", return_value=payload):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None

    def test_json_com_markdown_fence(self):
        """Gemini às vezes devolve ```json ... ``` — _limpar_json deve remover."""
        payload = f"```json\n{_JSON_VALIDO}\n```"
        with patch("utils.ia_client._chamar_gemini", return_value=payload):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is not None
        assert len(resultado) == 2

    def test_api_retorna_none(self):
        """_chamar_gemini retorna None (todos os modelos falharam)."""
        with patch("utils.ia_client._chamar_gemini", return_value=None):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None


class TestExtracaoFallbackApiError:
    """API lança exceção → retorna None, não propaga a exceção."""

    def test_requests_exception(self):
        import requests
        with patch(
            "utils.ia_client._chamar_gemini",
            side_effect=requests.RequestException("timeout"),
        ):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None

    def test_generic_exception(self):
        with patch(
            "utils.ia_client._chamar_gemini",
            side_effect=RuntimeError("unexpected"),
        ):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is None


class TestExtracaoConvertRiscosParaDict:
    """Verifica que 'riscos' do Gemini vira riscos_mapeados com nome_agente."""

    def test_riscos_viram_lista_de_dicts(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        riscos = resultado[0]["riscos_mapeados"]
        assert isinstance(riscos, list)
        for r in riscos:
            assert isinstance(r, dict), f"Risco não é dict: {r}"
            assert "nome_agente" in r, f"Falta 'nome_agente' em: {r}"
            assert "perigo_especifico" in r, f"Falta 'perigo_especifico' em: {r}"

    def test_nome_agente_preserva_texto(self):
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        nomes = [r["nome_agente"] for r in resultado[0]["riscos_mapeados"]]
        assert "Ruído" in nomes
        assert "Poeira de madeira" in nomes
        assert "Trabalho em altura" in nomes

    def test_perigo_especifico_sempre_string_vazia(self):
        """perigo_especifico deve ser '' — o PGR não nos diz o CAS."""
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_VALIDO):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        for ghe in resultado:
            for r in ghe["riscos_mapeados"]:
                assert r["perigo_especifico"] == "", (
                    f"perigo_especifico deveria ser '' mas é {r['perigo_especifico']!r}"
                )

    def test_numero_ghe_sem_padding_vira_dois_digitos(self):
        """numero '7' deve virar 'GHE 07 - ...' no campo ghe."""
        with patch("utils.ia_client._chamar_gemini", return_value=_JSON_GHE_UNICO):
            resultado = extrair_pgr_estruturado_via_gemini("texto", _CHAVE_FAKE)
        assert resultado is not None
        assert resultado[0]["ghe"].startswith("GHE 07 - ")

    def test_pgr_truncado_a_40000_chars(self):
        """Confirma que o texto enviado à API nunca excede 40 000 chars."""
        texto_longo = "X" * 100_000
        chamadas = []

        def capturar_prompt(prompt, chave, **kwargs):
            chamadas.append(prompt)
            return _JSON_VALIDO

        with patch("utils.ia_client._chamar_gemini", side_effect=capturar_prompt):
            extrair_pgr_estruturado_via_gemini(texto_longo, _CHAVE_FAKE)

        assert chamadas, "API não foi chamada"
        # O prompt inclui o texto truncado: confirma que os X's não excedem 40k
        assert chamadas[0].count("X") <= 40_000, (
            f"Texto enviado tem {chamadas[0].count('X')} chars de PGR, esperado <= 40000"
        )
