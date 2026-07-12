from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import (
    avaliar_estrutura,
    avaliar_familia,
    avaliar_segmentacao,
    eh_cabecalho_ghe,
    eh_sinal_cargo,
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


def test_contagem_de_linhas_setor_funcao_no_texto(paginas: list[str]) -> None:
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
    assert len(recortar_blocos_ghe(paginas)) == 31


def test_recorte_blocos_ghe_todo_bloco_comeca_com_ancora(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    assert all(eh_cabecalho_ghe(bloco.splitlines()[0]) for bloco in blocos)


def test_recorte_blocos_ghe_invariante_de_particao(paginas: list[str]) -> None:
    # Anti perda-silenciosa (classe D-ARQ-22): juntar os blocos de volta
    # reproduz exatamente o texto do documento da 1ª âncora até o fim —
    # nenhuma linha é duplicada ou descartada no recorte.
    blocos = recortar_blocos_ghe(paginas)
    linhas = [linha for pagina in paginas for linha in pagina.splitlines()]
    i_primeira_ancora = next(
        i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)
    )
    texto_esperado = "\n".join(linhas[i_primeira_ancora:])
    assert "\n".join(blocos) == texto_esperado


def test_recorte_blocos_ghe_pintura_preserva_agente_valor(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    (bloco_pintura,) = [
        bloco
        for bloco in blocos
        if "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in bloco
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
        if "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in bloco
    ]
    assert "Estireno 0,1 ppm" in bloco_pintura


def test_recorte_blocos_ghe_sem_ancora_devolve_lista_vazia() -> None:
    assert recortar_blocos_ghe(["sem ancora aqui", ""]) == []


def test_recorte_blocos_ghe_duas_ancoras_mesma_pagina() -> None:
    pagina = "GHE 1\nlinha A\nGHE 2\nlinha B"
    blocos = recortar_blocos_ghe([pagina])
    assert blocos == ["GHE 1\nlinha A", "GHE 2\nlinha B"]


def test_recorte_topo_termina_antes_da_primeira_ancora(paginas: list[str]) -> None:
    topo = recortar_topo(paginas)
    assert topo is not None
    assert not any(eh_cabecalho_ghe(linha) for linha in topo.splitlines())


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
    assert recortar_topo(["GHE 1\nlinha A"]) == ""


# ---------------------------------------------------------------------------
# eh_cabecalho_ghe — repertório de reconhecedores (D-ARQ-57 peça 1,
# DT-003CM-01): formas 1-4 medidas sobre o acervo de 15 PGRs.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "linha",
    [
        "GHE 12",
        "GHE 12 - OBRAS",
        "INVENTÁRIO DE RISCO GHE 3",
        "GHE: 07 - ADMINISTRATIVO",
    ],
)
def test_eh_cabecalho_ghe_reconhece_cada_forma_medida(linha: str) -> None:
    assert eh_cabecalho_ghe(linha)


@pytest.mark.parametrize(
    "linha",
    [
        "SETOR/FUNÇÃO Pintura/ pintor",
        "Quantidade de Funcionários expostos neste GHE: 08",
        "Fisioterapia do GHE 17 para GHE 11",
    ],
)
def test_eh_cabecalho_ghe_rejeita_armadilhas_medidas(linha: str) -> None:
    assert not eh_cabecalho_ghe(linha)


def test_recorte_blocos_ghe_conflacao_viverde_nao_gera_bloco_por_processo_subprocesso(
    paginas: list[str],
) -> None:
    # Conflação D-ARQ-22: a 2ª seção do Viverde (PROCESSO/SUBPROCESSO) também
    # começava com "SETOR/FUNÇÃO" mas não tem linha de cabeçalho GHE — a
    # troca de âncora (D-ARQ-57 peça 1) resolve isso por design, deixando de
    # gerar bloco para essa seção.
    blocos = recortar_blocos_ghe(paginas)
    assert not any("PROCESSO/SUBPROCESSO" in bloco.splitlines()[0] for bloco in blocos)


# ---------------------------------------------------------------------------
# avaliar_segmentacao — gate anti-Vistamérica, densidade + contagem
# (D-ARQ-57 peça 2, limiares calibrados em 003.CP sobre DT-003CM-01).
# ---------------------------------------------------------------------------


def _construir_paginas(total_paginas: int, ancoras: dict[int, str]) -> list[str]:
    # 1 linha por página: "GHE n" nas páginas-âncora (1-based), filler nas
    # demais — controla exatamente a extensão em páginas de cada bloco.
    return [
        ancoras.get(pagina, f"linha comum pág. {pagina}")
        for pagina in range(1, total_paginas + 1)
    ]


def test_avaliar_segmentacao_uma_ancora_doc_grande_e_pendencia_por_contagem() -> None:
    paginas = _construir_paginas(20, {5: "GHE 1"})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_zero_ancoras_doc_grande_e_pendencia_por_contagem() -> None:
    paginas = _construir_paginas(20, {})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_doc_pequeno_uma_ancora_e_none() -> None:
    # 8 páginas está abaixo de _LIMIAR_PAGINAS_DOC_MINIMO=10 — 1 bloco
    # cobrindo o documento inteiro é plausível num doc pequeno.
    paginas = _construir_paginas(8, {8: "GHE 1"})
    assert avaliar_segmentacao(paginas) is None


def test_avaliar_segmentacao_bloco_denso_e_pendencia_por_densidade() -> None:
    # Âncoras nas págs. 1,2,3,4,12 -> blocos de 1,1,1,8,9 páginas (últ. bloco
    # vai até a pág. 20) — o bloco de 9 págs. excede 40% de 20 (=8 págs.).
    paginas = _construir_paginas(
        20, {1: "GHE 1", 2: "GHE 2", 3: "GHE 3", 4: "GHE 4", 12: "GHE 5"}
    )
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_blocos_distribuidos_e_none() -> None:
    # Âncoras nas págs. 1,5,9,13,17 -> todo bloco tem 4 páginas (<= 40% de 20).
    paginas = _construir_paginas(
        20, {1: "GHE 1", 5: "GHE 2", 9: "GHE 3", 13: "GHE 4", 17: "GHE 5"}
    )
    assert avaliar_segmentacao(paginas) is None


def test_avaliar_segmentacao_pendencia_e_bloqueante_com_regra_origem_darq57() -> None:
    paginas = _construir_paginas(20, {})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-57"


def test_avaliar_segmentacao_viverde_e_none(paginas: list[str]) -> None:
    # Medição 003.CP: Viverde 151 págs., 31 blocos, maior bloco 29 págs.
    # (= 19,2%) — bem abaixo dos dois limiares.
    assert avaliar_segmentacao(paginas) is None


# ---------------------------------------------------------------------------
# eh_sinal_cargo / avaliar_familia / avaliar_estrutura — família cargo-based
# (D-ARQ-57 peça 3, DT-003CM-01): 3 formas medidas em 003.CQ sobre o acervo.
# ---------------------------------------------------------------------------

CAMINHO_PGR_RICCO_ADM = Path("matrizes_originais/PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf")
CAMINHO_PGR_CJR = Path("matrizes_originais/pgr_Cjr Engenharia Ltda (M Construtora).pdf")


@pytest.mark.parametrize(
    "linha",
    [
        "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas",
        "CARGO TECNÓLOGO EM EDIFICAÇÕES - CBO: 214280",
        "Função Identificação de Perigo / Risco Tempo de Meio de Nível de "
        "Eliminação ou Controle Existente",
    ],
)
def test_eh_sinal_cargo_reconhece_cada_forma_medida(linha: str) -> None:
    assert eh_sinal_cargo(linha)


@pytest.mark.parametrize(
    "linha",
    [
        "Função/Cargo:",
        "cargo estão expostos.",
        "XXVIII - Seguro contra acidentes de trabalho, á cargo do empregador, "
        "sem excluir, a indenização",
        "SETOR/FUNÇÃO: PRODUÇÃO",
    ],
)
def test_eh_sinal_cargo_rejeita_armadilhas_medidas(linha: str) -> None:
    assert not eh_sinal_cargo(linha)


def test_avaliar_familia_sem_ghe_com_sinal_cargo_e_pendencia() -> None:
    paginas = ["linha comum", "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    pendencia = avaliar_familia(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-57"
    assert pendencia.ghe_id is None


def test_avaliar_familia_com_ancora_ghe_e_sinal_cargo_e_none() -> None:
    paginas = ["GHE 1", "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    assert avaliar_familia(paginas) is None


def test_avaliar_familia_sem_ghe_e_sem_sinal_e_none() -> None:
    paginas = ["linha comum", "outra linha comum"]
    assert avaliar_familia(paginas) is None


def test_avaliar_estrutura_cargo_based_grande_e_pgr_cargo_based_nao_segmentacao() -> None:
    # Doc grande (>10 págs.), 0 âncoras GHE, com sinal-cargo: sem a peça 3
    # este caso cairia no gate genérico e emitiria segmentacao_implausivel
    # (contagem: 0 blocos em doc >10 págs.) — a peça 3 sela a exclusão mútua.
    paginas = _construir_paginas(20, {}) + ["CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    pendencia = avaliar_estrutura(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
    assert pendencia.tipo != "segmentacao_implausivel"


def test_avaliar_estrutura_ghe_implausivel_delega_segmentacao() -> None:
    paginas = _construir_paginas(20, {5: "GHE 1"})
    pendencia = avaliar_estrutura(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_estrutura_viverde_e_none(paginas: list[str]) -> None:
    assert avaliar_estrutura(paginas) is None


def test_avaliar_estrutura_ricco_adm_real_e_pgr_cargo_based() -> None:
    paginas_ricco = extrair_texto_pgr(CAMINHO_PGR_RICCO_ADM)
    pendencia = avaliar_estrutura(paginas_ricco)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"


def test_avaliar_estrutura_cjr_real_e_pgr_cargo_based() -> None:
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    pendencia = avaliar_estrutura(paginas_cjr)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
