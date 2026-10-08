"""Nome dos downloads no padrão das médicas no acervo ("MATRIZ DE EXAMES(ATUALIZAÇÃO)RICCO
CONSTRUTORA HETRIN 14.09.26.doc"), montado com o que foi digitado na tela (pedido do
Diovanni, 08/10/2026). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.tipos import RelatorioASO, Resultado
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.web_matriz import nome_arquivo, pagina_matriz
from agente_medico.tests.test_relatorio_aso import _matriz, _sugestao


def _cab(empresa: str = "", obra: str = "", tipo: str = "", data: str = "") -> CabecalhoDocumento:
    return CabecalhoDocumento(empresa, obra, tipo, data, "Dra. X", "CRM 1")


def test_nome_no_padrao_das_medicas() -> None:
    # Reversões que matam: (1) devolver sempre o genérico; (2) não pôr o tipo em
    # maiúsculas entre parênteses colado no documento; (3) não trocar a barra da data
    # por ponto (a barra só some e a data vira "081026").
    cab = _cab("RICCO", "HETRIM", "Atualização", "08/10/26")
    assert nome_arquivo("MATRIZ DE EXAMES", cab, "docx", "matriz.docx") == "MATRIZ DE EXAMES(ATUALIZAÇÃO)RICCO HETRIM 08.10.26.docx"


def test_campos_vazios_ficam_de_fora_e_sem_tipo_nao_ha_parenteses() -> None:
    # Reversões que matam: (1) parênteses vazios quando não há tipo; (2) juntar as
    # partes sem descartar as vazias (espaço duplo entre empresa e data).
    assert nome_arquivo("RISCOS PARA O ASO", _cab("RICCO", "", "", "08.10.26"), "docx", "x") == "RISCOS PARA O ASO RICCO 08.10.26.docx"


def test_caracteres_proibidos_no_windows_saem() -> None:
    # Reversão que mata: não limpar os caracteres proibidos — o navegador no Windows
    # troca ou recusa o nome.
    cab = _cab('A:B*C?"D<E>F|G\\H', "", "Adendo", "")
    assert nome_arquivo("MATRIZ DE EXAMES", cab, "html", "x") == "MATRIZ DE EXAMES(ADENDO)ABCDEFGH.html"


def test_sem_nada_digitado_sai_o_generico() -> None:
    # Reversão que mata: tirar a volta ao genérico — sairia "MATRIZ DE EXAMES .docx".
    assert nome_arquivo("MATRIZ DE EXAMES", _cab(" ", "", "", ""), "docx", "matriz.docx") == "matriz.docx"


def test_tela_usa_o_nome_digitado_nos_quatro_downloads(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: deixar qualquer um dos `file_name` literais em pagina_matriz.
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
    _submeter_formulario(at, campos={"Empresa": "RICCO", "Obra": "HETRIM", "Tipo de documento": "Atualização", "Data": "08/10/26"})

    assert not at.exception
    sufixo = "(ATUALIZAÇÃO)RICCO HETRIM 08.10.26"
    assert set(nomes) == {
        f"MATRIZ DE EXAMES{sufixo}.docx",
        f"MATRIZ DE EXAMES{sufixo}.html",
        f"MEMORIAL DE RACIOCÍNIO{sufixo}.docx",
        f"RISCOS PARA O ASO{sufixo}.docx",
    }
