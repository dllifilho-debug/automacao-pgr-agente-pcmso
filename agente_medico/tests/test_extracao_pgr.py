from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import extrair_texto_pgr

# PDF é tracked no git (matrizes_originais/) — ausência é falha explícita,
# não skip (espelha a decisão de test_extracao_fds.py para o acervo untracked,
# mas aqui o arquivo está sob controle de versão: 003.BL / D-ARQ-50).
CAMINHO_PGR = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")


@pytest.fixture(scope="module")
def paginas() -> list[str]:
    # 151 páginas é caro para parsear por teste — uma extração para a suíte inteira.
    return extrair_texto_pgr(CAMINHO_PGR)


def test_numero_de_paginas(paginas: list[str]) -> None:
    assert len(paginas) == 151


def test_toda_pagina_e_str(paginas: list[str]) -> None:
    assert all(isinstance(pagina, str) for pagina in paginas)


def test_contagem_de_blocos_setor_funcao(paginas: list[str]) -> None:
    n_blocos = sum(
        1
        for pagina in paginas
        for linha in pagina.splitlines()
        if linha.startswith("SETOR/FUNÇÃO")
    )
    assert n_blocos == 42


def test_ghe_pintura_preserva_adjacencia_agente_valor(paginas: list[str]) -> None:
    # GHE 13 - Pintura (pág. 71), medido em 003.BL: teste de perda-silenciosa
    # (classe D-ARQ-22) para os valores da quantificação por agente.
    pagina_pintura = paginas[71]
    assert "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in pagina_pintura
    assert "78,8 dB(A) em funcionamento" in pagina_pintura
    assert "Etanol 4,4 ppm" in pagina_pintura
    # "Acetato de Etila" quebra em 2 linhas na extração desta página (verbatim,
    # sem reconstrução de layout — isso é fatia futura de transcrição-LLM).
    assert "Acetato de" in pagina_pintura
    assert "Etila 1 ppm" in pagina_pintura
    assert "Tolueno 6,3 ppm" in pagina_pintura


def test_saida_verbatim_preserva_acento_e_caixa(paginas: list[str]) -> None:
    pagina_pintura = paginas[71]
    assert "SETOR/FUNÇÃO" in pagina_pintura
    assert "SETOR/FUNCAO" not in pagina_pintura
