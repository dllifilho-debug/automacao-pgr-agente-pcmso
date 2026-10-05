from __future__ import annotations

import functools
from pathlib import Path

import pytest

from agente_medico.motor.io_pdf import paginas_liberadas
from agente_medico.motor.parser_familia_grid_aiha import (
    GrupoFuncaoNaoReconhecido,
    PalavraPDF,
    localizar_intervalos_grid,
    segmentar_arquivo,
    segmentar_documento,
    segmentar_documento_arquivo,
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


# ---------------------------------------------------------------------------
# Fatia G1 (D-ARQ-57 peça 5, sessão claude/gifted-cerf-0loir2): template
# set-2026 da Ricco — cabeçalho em CAIXA ALTA, às vezes fragmentado em
# letras; cabeçalho no meio da página, com a função anterior acima dele;
# página sem cabeçalho dentro do grid; mais de um intervalo de grid.
# Posições do cabeçalho copiadas da pág. 30 do Hetrin/set-2026 (rótulos
# fragmentados), deslocadas por `topo`.
# ---------------------------------------------------------------------------

CAMINHO_PDF_RICCO_REV06 = Path("matrizes_originais/PGR_RICCO_2026_REV06.pdf")
CAMINHO_PDF_RICCO_ADENDO = Path("matrizes_originais/ADENDO - FUNÇÕES FALTANTES - PGR RICCO.pdf")

requer_pdfs_set2026 = pytest.mark.skipif(
    not (CAMINHO_PDF_RICCO_REV06.exists() and CAMINHO_PDF_RICCO_ADENDO.exists()),
    reason="PDFs Ricco set-2026 ausentes; harness integração fatia G1 indisponível",
)


def _cabecalho_caixa_alta(topo: float) -> tuple[PalavraPDF, ...]:
    return (
        _p("C", 178.0, topo - 6.1),
        _p("eSocial", 203.0, topo - 6.1),
        _p("T", 82.0, topo - 3.5),
        _p("IP", 85.0, topo - 3.5),
        _p("O", 90.0, topo - 3.5),
        _p("FUNÇÃO", 39.1, topo),
        _p("R", 84.0, topo + 3.6),
        _p("IS", 87.0, topo + 3.6),
        _p("P", 121.0, topo + 3.6),
        _p("E", 124.0, topo + 3.6),
        _p("R", 127.0, topo + 3.6),
        _p("I", 131.0, topo + 3.6),
        _p("G", 132.0, topo + 3.6),
        _p("O", 136.0, topo + 3.6),
        _p("/", 140.0, topo + 3.6),
        _p("R", 143.0, topo + 3.6),
        _p("IS", 147.0, topo + 3.6),
        _p("C", 151.0, topo + 3.6),
        _p("O", 155.0, topo + 3.6),
        _p("E", 251.0, topo + 7.5),
        _p("X", 254.0, topo + 7.5),
        _p("PO", 257.0, topo + 7.5),
        _p("SIÇÃO", 263.0, topo + 7.5),
    )


def _risco_caixa_alta(marcador: str, top: float) -> tuple[PalavraPDF, ...]:
    return (_p(marcador, 110.0, top),)


def _pagina_caixa_alta(nome: str, topo: float, riscos: tuple[str, ...]) -> tuple[PalavraPDF, ...]:
    corpo: list[PalavraPDF] = []
    for indice, risco in enumerate(riscos):
        corpo.extend(_risco_caixa_alta(risco, topo + 30.0 + 10.0 * indice))
    return (*_cabecalho_caixa_alta(topo), *corpo, _p(nome, 40.0, topo + 60.0))


def test_g1_cabecalho_caixa_alta_fragmentado_calibra_a_pagina() -> None:
    # Reversão que mata: _localizar_cabecalho_grid sem o fallback
    # _localizar_cabecalho_caixa_alta (só title-case) -> GrupoFuncaoNaoReconhecido.
    grupos = segmentar_paginas([_pagina_caixa_alta("PINTOR", 100.0, ("RUÍDO",))])
    assert [g.nome for g in grupos] == ["PINTOR"]
    assert [linha.texto for linha in grupos[0].linhas] == ["RUÍDO"]


def test_g1_banda_funcao_termina_no_rotulo_tipo_fragmentado() -> None:
    # Letra de categoria de risco ("F", coluna Tipo de Risco, x0=86) acima
    # do nome. Reversão que mata: tipo_risco_x0 = max(a_direita) em vez de
    # min — a letra cai na banda Função e vira o nome do grupo.
    pagina = (*_pagina_caixa_alta("PINTOR", 100.0, ()), _p("F", 86.0, 140.0))
    grupos = segmentar_paginas([pagina])
    assert [g.nome for g in grupos] == ["PINTOR"]
    assert [linha.texto for linha in grupos[0].linhas] == ["F"]


def test_g1_tabela_de_epi_por_funcao_nao_e_cabecalho_do_grid() -> None:
    # "FUNÇÃO" sem PERIGO e EXPOSIÇ no bloco (tabela de EPI por função,
    # pág. 8 do adendo). Reversão que mata: tirar a checagem do texto colado
    # do bloco — a página vira intervalo de grid.
    pagina_epi = (
        _p("FUNÇÃO", 39.1, 100.0),
        _p("EPI", 200.0, 100.0),
        _p("obrigatório", 215.0, 100.0),
        _p("PEDREIRO", 40.0, 120.0),
    )
    assert localizar_intervalos_grid([pagina_epi]) == ()


def test_g1_conteudo_acima_do_cabecalho_vai_para_a_funcao_anterior() -> None:
    # Reversão que mata: remover o bloco `acima` de segmentar_paginas — a
    # linha "POEIRA" (continuação de PEDREIRO no topo da página de PINTOR)
    # some dos dois grupos.
    pagina_a = _pagina_caixa_alta("PEDREIRO", 100.0, ("RUÍDO",))
    pagina_b = (_p("POEIRA", 110.0, 60.0), *_pagina_caixa_alta("PINTOR", 300.0, ("CALOR",)))
    grupos = segmentar_paginas([pagina_a, pagina_b])
    assert [g.nome for g in grupos] == ["PEDREIRO", "PINTOR"]
    assert [linha.texto for linha in grupos[0].linhas] == ["RUÍDO", "POEIRA"]
    assert [linha.texto for linha in grupos[1].linhas] == ["CALOR"]


def test_g1_pagina_sem_cabecalho_e_continuacao_sem_titulo_corrido() -> None:
    # Pág. 32 do Hetrin/set-2026: sem cabeçalho, continuação de PINTOR,
    # com o título corrido do PGR no topo. Reversões que matam: (a) voltar
    # a levantar GrupoFuncaoNaoReconhecido em página sem cabeçalho; (b)
    # tirar o filtro _sem_titulo_corrido — o título corrido entra no grupo.
    titulo = tuple(
        _p(texto, x, 72.4)
        for texto, x in (
            ("PGR", 208.0),
            ("|", 225.0),
            ("PROGRAMA", 228.0),
            ("DE", 272.0),
            ("GERENCIAMENTO", 283.0),
            ("DE", 349.0),
            ("RISCOS", 360.0),
        )
    )
    pagina_a = _pagina_caixa_alta("PINTOR", 100.0, ("RUÍDO",))
    pagina_sem_cabecalho = (*titulo, _p("UMIDADE", 108.6, 108.1))
    pagina_c = _pagina_caixa_alta("PORTEIRO", 100.0, ("CALOR",))
    grupos = segmentar_paginas([pagina_a, pagina_sem_cabecalho, pagina_c])
    assert [g.nome for g in grupos] == ["PINTOR", "PORTEIRO"]
    assert [linha.texto for linha in grupos[0].linhas] == ["RUÍDO", "UMIDADE"]


def test_g1_intervalos_admitem_lacuna_de_uma_pagina_e_separam_as_maiores() -> None:
    # Reversões que matam: _LACUNA_MAX_SEM_CABECALHO = 0 (a lacuna de 1
    # página parte o 1º intervalo); juntar tudo num intervalo só.
    grid = _pagina_caixa_alta("PINTOR", 100.0, ("RUÍDO",))
    fora = (_p("texto", 100.0, 100.0),)
    paginas = [grid, grid, fora, grid, fora, fora, fora, grid]
    assert localizar_intervalos_grid(paginas) == ((0, 3), (7, 7))


def test_g1_grupo_nao_continua_de_um_intervalo_para_o_seguinte() -> None:
    # Mesmo nome nos dois intervalos (último do corpo e 1º do adendo, no
    # REV06, são funções diferentes; aqui o caso extremo). Reversão que
    # mata: segmentar_documento chamar segmentar_paginas uma vez só, do
    # início do 1º ao fim do último intervalo — vira 1 grupo.
    grid = _pagina_caixa_alta("ALFA", 100.0, ("RUÍDO",))
    fora = (_p("texto", 100.0, 100.0),)
    grupos = segmentar_documento([grid, fora, fora, grid])
    assert [g.nome for g in grupos] == ["ALFA", "ALFA"]


# Integração G1. Números medidos na sessão claude/gifted-cerf-0loir2. A
# leitura do PDF inteiro é cara (DH-003EC-02); uma por arquivo, compartilhada.
_NOMES_HETRIN_SET = [
    "ENGENHEIRO CIVIL/ ENGENHEIRO RESIDENTE/ ESTAGIÁRIO DE ENGENHARIA/ APONTADOR ADMINISTRATIVO DE OBRA/ "
    "TÉCNICO DE SEGURANÇA DO TRABALHO",
    "ALMOXARIFE",
    "ARMADOR",
    "AUXILIAR DE SERVIÇOS GERAIS/ SERVIÇOS GERAIS",
    "AZULEJISTA",
    "CARPINTEIR O",
    "ELETRICISTA",
    "ENCANADOR",
    "ENCARREGADOS",
    "GESSEIRO",
    "MESTRE DE OBRAS",
    "MONTADOR",
    "MONTADOR DE ESTRUTURAS METÁLICAS",
    "MOTORISTA DE CAMINHÃO",
    "OPERADOR DE BETONEIRA",
    "OPERADOR DE RETROESCAVADEIRA",
    "PEDREIRO",
    "PINTOR",
    "PORTEIRO",
    "SERVENTE",
    "SOLDADOR",
    "VIGIA DIURNO/ VIGIA NOTURNO",
]
_NOMES_RICCO_ADENDO = [
    "ENCARREGADO DE ELETRICISTA",
    "ENCARREGADO DE INSTALAÇÕES E LÉ T R I C A E HIDR O S S A N I T Á R IAS",
    "EN C AR R E G A D O D E EN C A N A D O R",
    "ENCARREGADO DE ARMAÇÃO",
    "ENCARREGADO DE CARPINTEIRO",
    "ENCARREGADO DE OBRA",
    "AUXILIAR ADMINISTRATVO",
    "MENOS APRENDIZ",
]


@functools.lru_cache(maxsize=None)
def _paginas(caminho: Path) -> tuple[tuple[PalavraPDF, ...], ...]:
    return tuple(
        tuple(PalavraPDF(text=w["text"], x0=w["x0"], top=w["top"]) for w in page.extract_words())
        for page in paginas_liberadas(caminho)
    )


@requer_pdfs_set2026
def test_g1_rev06_corpo_hetrin_set_e_adendo_anexado() -> None:
    # REV06 = Hetrin/set-2026 (págs. 0-196, texto idêntico página a página)
    # + adendo (197-216): um teste cobre os dois. As 22 funções do corpo são
    # as da matriz 14.09.26 do acervo, na mesma ordem (a matriz abre o grupo
    # N:1 em cargos); a pág. 32, sem cabeçalho, fica com PINTOR.
    # Reversões que matam: só a forma title-case (nenhum intervalo); página
    # sem cabeçalho voltar a levantar exceção; lacuna sem limite (um
    # intervalo só, 14-204); _LACUNA_MAX_SEM_CABECALHO = 0 (a pág. 32 parte
    # o corpo em dois).
    paginas = _paginas(CAMINHO_PDF_RICCO_REV06)
    assert localizar_intervalos_grid(paginas) == ((14, 36), (197, 204))
    grupos = segmentar_documento(paginas)
    assert [g.nome for g in grupos] == _NOMES_HETRIN_SET + _NOMES_RICCO_ADENDO
    pintor = grupos[_NOMES_HETRIN_SET.index("PINTOR")]
    assert any("UMIDADE" in linha.texto for linha in pintor.linhas)


@requer_pdfs_set2026
def test_g1_adendo_isolado_com_cabecalho_fragmentado() -> None:
    # Reversão que mata: exigir "PERIGO/RISCO" colado (págs. 2-3 do
    # adendo têm "PERIGO/" e "RISCO" em linhas diferentes e saem do grid).
    paginas = _paginas(CAMINHO_PDF_RICCO_ADENDO)
    assert localizar_intervalos_grid(paginas) == ((0, 7),)
    assert [g.nome for g in segmentar_documento(paginas)] == _NOMES_RICCO_ADENDO


@requer_pdfs
def test_g1_witnesses_title_case_documento_inteiro_sem_intervalo_espurio() -> None:
    # Não regressão da 5a pelo caminho novo (documento inteiro, sem
    # intervalo dado): o localizador acha só o grid, e as contagens de
    # grupos são as já medidas (63 e 28). Reversão que mata: tirar a
    # checagem PERIGO/EXPOSIÇ do bloco CAIXA ALTA — as págs. com "FUNÇÃO"
    # fora do grid viram intervalo.
    hetrin_mar = _paginas(CAMINHO_PDF_HETRIN_MAR)
    serra = _paginas(CAMINHO_PDF_SERRA_DOURADA)
    assert localizar_intervalos_grid(hetrin_mar) == ((63, 185),)
    assert localizar_intervalos_grid(serra) == ((58, 113),)
    assert len(segmentar_documento(hetrin_mar)) == 63
    assert len(segmentar_documento(serra)) == 28
