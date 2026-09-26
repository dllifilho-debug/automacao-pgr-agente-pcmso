from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.parser_familia_grid_aiha import (
    GrupoFuncaoNaoReconhecido,
    PalavraPDF,
    segmentar_arquivo,
    segmentar_paginas,
)

CAMINHO_PDF_HETRIN_MAR = Path("matrizes_originais/01. PGR RICCO HETRIN - MAR25.pdf")
CAMINHO_PDF_SERRA_DOURADA = Path("matrizes_originais/01. PGR RICCO SERRA DOURADA - MAI.24 1.pdf")

requer_pdfs = pytest.mark.skipif(
    not (CAMINHO_PDF_HETRIN_MAR.exists() and CAMINHO_PDF_SERRA_DOURADA.exists()),
    reason="PDFs Hetrin/Serra Dourada ausentes; harness integração fatia 5a indisponível",
)


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


# ---------------------------------------------------------------------------
# Cabeçalho sintético reusado nos testes de núcleo puro — molde exato do
# medido (Função@57.1, Tipo@116.8, quebrado em 4 linhas físicas; ver
# _localizar_cabecalho_grid). x0/top verbatim da medição real (pág. 63,
# Hetrin/mar), só os valores essenciais aos dois anchors + à linha
# Exposição+Propagação.
# ---------------------------------------------------------------------------


def _cabecalho() -> tuple[PalavraPDF, ...]:
    return (
        _p("Tipo", 116.8, 80.1),
        _p("de", 132.4, 80.1),
        _p("Função", 57.1, 83.8),
        _p("Identificação", 183.1, 83.8),
        _p("Risco", 119.4, 87.5),
        _p("Exposição", 366.9, 91.5),
        _p("Propagação", 410.2, 91.5),
        _p("Risco", 575.8, 91.5),
    )


def _risco(texto_marcador: str, top: float) -> tuple[PalavraPDF, ...]:
    """Uma linha de risco mínima (banda Tipo de Risco/Identificação, fora
    da banda Função) — só o suficiente pra não ser banda Função."""
    return (_p("-", 147.0, top), _p(texto_marcador, 155.0, top))


def _titulo(nome: str, x0: float, top: float) -> tuple[PalavraPDF, ...]:
    palavras = nome.split(" ")
    x = x0
    saida = []
    for palavra in palavras:
        saida.append(_p(palavra, x, top))
        x += len(palavra) + 1
    return tuple(saida)


def test_nucleo_puro_uma_pagina_uma_funcao_sem_ambiguidade() -> None:
    # Risco ANTES do rótulo (molde real: 2-6 linhas de risco por página
    # antes do nome) + risco DEPOIS. Ambos devem entrar no mesmo grupo —
    # cada página pertence inteira a uma função (ver nota de topo do
    # módulo). Reversão: se o código voltar a tratar linhas pré-rótulo
    # como pertencentes a um grupo diferente (ou descartá-las), o grupo
    # sai com 1 linha em vez de 2.
    pagina = (
        *_cabecalho(),
        *_risco("Ruido", 135.5),
        *_titulo("Alfa", 35.0, 150.0),
        *_risco("Poeira", 165.0),
    )
    grupos = segmentar_paginas([pagina])
    assert len(grupos) == 1
    assert grupos[0].nome == "Alfa"
    assert len(grupos[0].linhas) == 2
    assert grupos[0].linhas[0].texto.startswith("- Ruido")
    assert grupos[0].linhas[1].texto.startswith("- Poeira")


def test_nucleo_puro_titulo_quebrado_em_duas_linhas_sem_quebra_de_paragrafo() -> None:
    # Molde real: "Técnico de Segurança do" / "Trabalho" (Serra Dourada,
    # pág. 62) — nome quebra em 2 linhas físicas, distância ~7.4pt (mesma
    # ordem de grandeza de linhas do MESMO parágrafo). Reversão: se
    # _resolver_titulo voltar a usar só linhas_funcao[0], nome sai truncado
    # em "Alfa" em vez de "Alfa Beta".
    pagina = (
        *_cabecalho(),
        *_titulo("Alfa", 35.0, 150.0),
        *_titulo("Beta", 35.0, 157.4),  # delta 7.4pt — mesmo parágrafo
        *_risco("Ruido", 172.0),
    )
    grupos = segmentar_paginas([pagina])
    assert len(grupos) == 1
    assert grupos[0].nome == "Alfa Beta"


def test_nucleo_puro_quebra_de_paragrafo_encerra_titulo_nao_vira_descricao() -> None:
    # Molde real: gap ~15pt entre o nome (mesmo quebrado em >1 linha) e a
    # descrição — medido em 12 ocorrências, 2 witnesses, 100% consistente.
    # Reversão: se o limiar de quebra sumir (_resolver_titulo concatena
    # tudo), nome sai "Alfa Descricao da funcao" em vez de só "Alfa".
    pagina = (
        *_cabecalho(),
        *_titulo("Alfa", 35.0, 150.0),
        *_titulo("Descricao", 28.0, 165.0),  # delta 15.0pt — quebra de parágrafo
        *_risco("Ruido", 180.0),
    )
    grupos = segmentar_paginas([pagina])
    assert len(grupos) == 1
    assert grupos[0].nome == "Alfa"


def test_nucleo_puro_pagina_continuacao_mesmo_nome_nao_fecha_grupo() -> None:
    # 2 páginas, mesmo nome ("CONTINUAÇÃO" real do documento) — risco das
    # duas páginas soma no MESMO grupo. Reversão: se a comparação
    # nome_pagina != nome_aberto quebrar (ex. sempre tratar página nova
    # como grupo novo), sai 2 grupos em vez de 1.
    pagina_a = (*_cabecalho(), *_titulo("Alfa", 35.0, 150.0), *_risco("Ruido", 165.0))
    pagina_b = (*_cabecalho(), *_risco("Poeira", 135.5), *_titulo("Alfa", 35.0, 150.0), *_risco("Calor", 165.0))
    grupos = segmentar_paginas([pagina_a, pagina_b])
    assert len(grupos) == 1
    assert grupos[0].nome == "Alfa"
    assert len(grupos[0].linhas) == 3


def test_nucleo_puro_pagina_nova_com_nome_diferente_fecha_grupo_e_risco_pre_rotulo_vai_pro_novo() -> None:
    # 2 páginas, nomes diferentes. As linhas de risco ANTES do rótulo da
    # 2ª função (molde real: sempre existem, 2-6 por página) pertencem à
    # função NOVA, não à antiga — é o achado que corrigiu a hipótese
    # inicial de ambiguidade (ver nota de topo do módulo). Reversão: se o
    # código voltar a tratar essas linhas como pendentes/ambíguas ou
    # atribuí-las à função anterior, a contagem de Beta cai de 2 para 1
    # (ou Alfa sobe de 1 para 2).
    pagina_a = (*_cabecalho(), *_titulo("Alfa", 35.0, 150.0), *_risco("Ruido", 165.0))
    pagina_b = (
        *_cabecalho(),
        *_risco("Poeira", 135.5),  # pré-rótulo — pertence a Beta
        *_titulo("Beta", 35.0, 150.0),
        *_risco("Calor", 165.0),
    )
    grupos = segmentar_paginas([pagina_a, pagina_b])
    assert len(grupos) == 2
    alfa, beta = grupos
    assert alfa.nome == "Alfa"
    assert len(alfa.linhas) == 1
    assert beta.nome == "Beta"
    assert len(beta.linhas) == 2
    assert beta.linhas[0].texto.startswith("- Poeira")


def test_nucleo_puro_nome_no_mesmo_top_de_outras_colunas_nao_quebra_grupo() -> None:
    # Molde real do bug medido (Hetrin/mar, pág. 64): o rótulo da função
    # pode compartilhar o MESMO `top` de palavras de OUTRAS colunas (banda
    # resto) — um reconhecedor que exige a linha física INTEIRA dentro da
    # banda Função perde esse rótulo. Aqui, "Alfa" (banda Função) e
    # "OutraColuna" (banda resto) dividem top=150.0. Reversão: se o código
    # voltar a agrupar a página inteira ANTES de separar por coluna (perde
    # a separação função/resto antes do agrupamento), a linha mista falha
    # o teste de banda pura e "Alfa" nunca é reconhecido como rótulo — a
    # 2ª página cairia num grupo espúrio em vez de continuar "Alfa".
    pagina_a = (*_cabecalho(), *_titulo("Alfa", 35.0, 150.0), *_risco("Ruido", 165.0))
    pagina_b = (
        *_cabecalho(),
        *_risco("Poeira", 135.5),
        *_titulo("Alfa", 35.0, 150.0),
        _p("OutraColuna", 400.0, 150.0),  # mesmo top do rótulo, banda resto
        *_risco("Calor", 165.0),
    )
    grupos = segmentar_paginas([pagina_a, pagina_b])
    assert len(grupos) == 1
    assert grupos[0].nome == "Alfa"
    assert len(grupos[0].linhas) == 4  # Ruido + Poeira + a linha mista + Calor


def test_nucleo_puro_rodape_matriz_de_risco_nao_vira_nome_de_funcao() -> None:
    # Rodapé verbatim medido (top=549.4 nos 2 witnesses, repete em toda
    # página) — cabe inteiro na banda Função por coincidência de largura,
    # e nada mais distingue estruturalmente esta linha de um nome de
    # função curto. Página cujo ÚNICO conteúdo na banda Função é o
    # rodapé (sem título real) — sem a exclusão por literal, essa linha
    # resolveria como nome_pagina e um grupo espúrio "Matriz de Risco
    # AIHA" apareceria em vez de levantar a falha explícita. Reversão: se
    # a exclusão por literal sumir, `grupos` sai com 1 grupo espúrio em
    # vez de levantar GrupoFuncaoNaoReconhecido.
    pagina = (
        *_cabecalho(),
        *_risco("Ruido", 135.5),
        _p("Matriz", 57.1, 549.4),
        _p("de", 80.3, 549.4),
        _p("Risco", 90.3, 549.4),
        _p("AIHA", 109.4, 549.4),
    )
    with pytest.raises(GrupoFuncaoNaoReconhecido):
        segmentar_paginas([pagina])


def test_pagina_sem_cabecalho_levanta_grupofuncaonaoreconhecido() -> None:
    pagina = (_p("qualquer", 100.0, 10.0), _p("coisa", 150.0, 10.0))
    with pytest.raises(GrupoFuncaoNaoReconhecido):
        segmentar_paginas([pagina])


def test_pagina_com_cabecalho_mas_sem_linha_funcao_levanta_grupofuncaonaoreconhecido() -> None:
    pagina = (*_cabecalho(), *_risco("Ruido", 135.5))
    with pytest.raises(GrupoFuncaoNaoReconhecido):
        segmentar_paginas([pagina])


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs) — PDFs reais dos 2 witnesses limpos.
# Números medidos diretamente contra o disco (sessão claude/blissful-
# knuth-riqucz) — não estimados.
# ---------------------------------------------------------------------------


@requer_pdfs
def test_segmentar_arquivo_hetrin_mar_paginacao_real() -> None:
    grupos = segmentar_arquivo(CAMINHO_PDF_HETRIN_MAR, 63, 66)
    assert [g.nome for g in grupos] == ["Administrativo de Obra", "Almoxarife"]
    assert len(grupos[0].linhas) == 95
    assert len(grupos[1].linhas) == 111


@requer_pdfs
def test_segmentar_arquivo_serra_dourada_paginacao_real() -> None:
    grupos = segmentar_arquivo(CAMINHO_PDF_SERRA_DOURADA, 58, 63)
    assert [g.nome for g in grupos] == [
        "Encarregado de Obra",
        "Pedreiro",
        "Técnico de Segurança do Trabalho",
    ]
    assert len(grupos[0].linhas) == 101
    assert len(grupos[1].linhas) == 118
    assert len(grupos[2].linhas) == 101


@requer_pdfs
def test_segmentar_arquivo_hetrin_mar_contagem_de_funcoes_bate_extract_tables() -> None:
    # Instrumento independente (D-ARQ-57, extract_tables()) mediu ~60
    # funções no documento inteiro (~123 páginas). 41 funções em 80
    # páginas (63-142) extrapola pra ~63 no documento inteiro — mesma
    # ordem de grandeza, confirmação cruzada sem reusar o mesmo método.
    grupos = segmentar_arquivo(CAMINHO_PDF_HETRIN_MAR, 63, 142)
    assert len(grupos) == 41


@requer_pdfs
def test_segmentar_arquivo_serra_dourada_paginacao_rigida_sem_resto() -> None:
    # 56 páginas (58-113) / 28 funções = exatamente 2 páginas por função,
    # sem sobra — confirma a invariante "1 função = 1 nova + 1
    # CONTINUAÇÃO" no witness inteiro, não só na amostra de 3 funções.
    grupos = segmentar_arquivo(CAMINHO_PDF_SERRA_DOURADA, 58, 113)
    assert len(grupos) == 28
