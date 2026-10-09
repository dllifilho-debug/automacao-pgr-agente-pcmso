"""Formulário: Tipo como lista de opções e Data ISO convertida uma vez no cabeçalho (pedido do
Diovanni, 09/10/2026, depois do Quasar Bueno: arquivo "MATRIZ DE EXAMES(MATRIZ DE EXAMES)…",
nenhum (X) marcado e "2026-10-09" na matriz). Cada teste nomeia a reversão que o deixa
vermelho."""

from __future__ import annotations

from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.tipos import RelatorioASO, Resultado
from agente_medico.superficie.web_matriz import data_do_formulario, pagina_matriz, tipo_do_formulario
from agente_medico.tests.test_relatorio_aso import _matriz, _sugestao


def test_tipo_da_lista_e_o_outro_digitado() -> None:
    # Reversões que matam: (1) usar sempre o texto ao lado, mesmo sem "Outro" — o "Adendo"
    # some quando o campo tem resto de digitação; (2) devolver "Outro" em vez do texto.
    assert tipo_do_formulario("Adendo", "sobrou texto") == "Adendo"
    assert tipo_do_formulario("Outro", " Aditivo de obra ") == "Aditivo de obra"
    assert tipo_do_formulario(None, "") == ""


def test_data_iso_vira_dia_mes_ano_e_o_resto_fica_como_digitado() -> None:
    # Reversão que mata: devolver o texto sem converter — a matriz e o nome do arquivo voltam
    # a sair "2026-10-09".
    assert data_do_formulario("2026-10-09") == "09/10/2026"
    assert data_do_formulario(" 2026-10-09 ") == "09/10/2026"
    assert data_do_formulario("08/10/26") == "08/10/26"


def test_formulario_leva_tipo_da_lista_e_data_convertida_ao_nome_do_arquivo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversões que matam: (1) montar o cabeçalho com `data_documento` cru — o nome sai
    # "2026-10-05"; (2) montar com o texto de "Outro tipo" — o "(ADENDO)" some.
    from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario

    nomes: list[str] = []

    def _download_espiao(rotulo: str, dados: Any, **kwargs: Any) -> bool:
        nomes.append(str(kwargs.get("file_name")))
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)
    _mockar_parse_deterministico(
        monkeypatch, Resultado(status="OK", matrizes=[_matriz(RelatorioASO((_sugestao("ruido", "CONSTA"),)))])
    )
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(
        at,
        campos={"Empresa": "COOPERATIVA", "Obra": "QUASAR BUENO", "Tipo de documento": "Adendo", "Data": "2026-10-05"},
    )

    assert not at.exception
    assert "MATRIZ DE EXAMES(ADENDO)COOPERATIVA QUASAR BUENO 05.10.2026.docx" in nomes
