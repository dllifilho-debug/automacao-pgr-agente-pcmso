from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import (
    extrair_texto_pgr,
    recortar_blocos_ghe,
    recortar_topo,
)

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


def test_recorte_blocos_ghe_contagem(paginas: list[str]) -> None:
    assert len(recortar_blocos_ghe(paginas)) == 42


def test_recorte_blocos_ghe_todo_bloco_comeca_com_ancora(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    assert all(bloco.startswith("SETOR/FUNÇÃO") for bloco in blocos)


def test_recorte_blocos_ghe_invariante_de_particao(paginas: list[str]) -> None:
    # Anti perda-silenciosa (classe D-ARQ-22): juntar os blocos de volta
    # reproduz exatamente o texto do documento da 1ª âncora até o fim —
    # nenhuma linha é duplicada ou descartada no recorte.
    blocos = recortar_blocos_ghe(paginas)
    linhas = [linha for pagina in paginas for linha in pagina.splitlines()]
    i_primeira_ancora = next(
        i for i, linha in enumerate(linhas) if linha.startswith("SETOR/FUNÇÃO")
    )
    texto_esperado = "\n".join(linhas[i_primeira_ancora:])
    assert "\n".join(blocos) == texto_esperado


def test_recorte_blocos_ghe_pintura_preserva_agente_valor(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    (bloco_pintura,) = [
        bloco
        for bloco in blocos
        if bloco.startswith("SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente")
    ]
    assert "78,8 dB(A) em funcionamento" in bloco_pintura
    assert "Etanol 4,4 ppm" in bloco_pintura
    assert "Tolueno 6,3 ppm" in bloco_pintura


def test_recorte_blocos_ghe_pintura_cruza_fronteira_de_pagina(paginas: list[str]) -> None:
    # Literal REAL cravado na medição 003.BM (pág. 72, linha 3): pertence ao
    # bloco da Pintura (âncora na pág. 71) mas está na página SEGUINTE —
    # prova que o recorte não trava na fronteira de página.
    blocos = recortar_blocos_ghe(paginas)
    (bloco_pintura,) = [
        bloco
        for bloco in blocos
        if bloco.startswith("SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente")
    ]
    assert "Estireno 0,1 ppm" in bloco_pintura


def test_recorte_blocos_ghe_sem_ancora_devolve_lista_vazia() -> None:
    assert recortar_blocos_ghe(["sem ancora aqui", ""]) == []


def test_recorte_blocos_ghe_duas_ancoras_mesma_pagina() -> None:
    pagina = "SETOR/FUNÇÃO Um\nlinha A\nSETOR/FUNÇÃO Dois\nlinha B"
    blocos = recortar_blocos_ghe([pagina])
    assert blocos == ["SETOR/FUNÇÃO Um\nlinha A", "SETOR/FUNÇÃO Dois\nlinha B"]


def test_recorte_topo_termina_antes_da_primeira_ancora(paginas: list[str]) -> None:
    topo = recortar_topo(paginas)
    assert topo is not None
    assert not any(linha.startswith("SETOR/FUNÇÃO") for linha in topo.splitlines())


def test_recorte_topo_nao_vazio_no_viverde(paginas: list[str]) -> None:
    topo = recortar_topo(paginas)
    assert isinstance(topo, str)
    assert topo != ""


def test_recorte_topo_invariante_de_particao(paginas: list[str]) -> None:
    # Anti perda-silenciosa (classe D-ARQ-22): topo + blocos reconstrói
    # exatamente o texto do documento inteiro — nenhuma linha duplicada
    # ou descartada entre topo e blocos.
    topo = recortar_topo(paginas)
    assert topo is not None
    blocos = recortar_blocos_ghe(paginas)
    linhas = [linha for pagina in paginas for linha in pagina.splitlines()]
    texto_esperado = "\n".join(linhas)
    assert topo + "\n" + "\n".join(blocos) == texto_esperado


def test_recorte_topo_sem_ancora_devolve_none() -> None:
    assert recortar_topo(["sem ancora aqui", ""]) is None


def test_recorte_topo_ancora_na_primeira_linha_devolve_vazio() -> None:
    assert recortar_topo(["SETOR/FUNÇÃO Um\nlinha A"]) == ""
