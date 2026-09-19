from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, Optional

from agente_medico.motor.io_pdf import paginas_liberadas

# [DERIVADO — D-ARQ-57 peça 5, fatia 5a; ratificado sessão claude/blissful-
# knuth-riqucz sobre a proposta da sessão claude/dreamy-mayer-os6jce]
#
# Parser determinístico da família de template "grid AIHA" (Hetrin/Serra
# Dourada): módulo IRMÃO a parser_familia_consciente.py (D-ARQ-65), mesma
# classe de primitivo (PalavraPDF + banda de coluna calibrada), schema de
# coluna PRÓPRIO — a anatomia real do grid AIHA não é a mesma do Fascino
# (ver abaixo) e não compartilha código com aquele módulo além da forma do
# primitivo (por isso a duplicação de PalavraPDF/_Linha/_agrupar_linhas
# aqui, mesmo padrão já usado por aquele módulo — não existe um módulo
# comum de primitivos hoje).
#
# ESTA FATIA (5a de 4, D-ARQ-57 peça 5): só "banda de coluna calibrada por
# BLOCO + reconhecedor de fronteira de função". Decomposição N:1 de um
# grupo com múltiplos cargos compartilhando 1 lista de risco (5b), parsing
# da célula "Identificação de Perigo/Risco" em algo do formato RiscoVerbatim
# (5c) e roteamento/plug em preparar_ghes (5d) são fatias futuras — aqui a
# saída é só nome + linhas cruas atribuídas a cada função.
#
# ANATOMIA MEDIDA (sessão claude/blissful-knuth-riqucz, pdfplumber direto
# contra os 2 witnesses limpos: "01. PGR RICCO HETRIN - MAR25.pdf" págs.
# 63+, "01. PGR RICCO SERRA DOURADA - MAI.24 1.pdf" págs. 58+):
#
# "BLOCO" aqui é a PÁGINA, não um bloco GHE — o cabeçalho do grid
# (Função | Tipo de Risco | Identificação de Perigo/Risco | ...) repete em
# TODA página do intervalo (já registrado em D-ARQ-57, notas 003.DG/
# sessão dreamy-mayer-os6jce), então a banda de coluna é recalibrada por
# página, não herdada de um cabeçalho-de-bloco como no Fascino.
#
# Cada função ocupa exatamente 1 página "nova" + 1 página "CONTINUAÇÃO"
# (medido em 41 funções consecutivas, Hetrin/mar págs. 63-142 — nome
# repete verbatim na CONTINUAÇÃO; contagem extrapolada pro documento
# inteiro, ~63, bate com o "~60 funções" já medido em D-ARQ-57 por
# `extract_tables()`, instrumento independente). Cada página do intervalo
# pertence inteira a UMA função — atribuição de conteúdo é por página, não
# por posição da linha dentro da página.
#
# AS COLUNAS FLUEM INDEPENDENTES, NÃO EM GRADE LINHA-A-LINHA — duas
# consequências medidas, as duas resolvidas nesta fatia:
#
# (1) O nome da função pode compartilhar o MESMO `top` de palavras de
# OUTRAS colunas (medido pág. 64 Hetrin/mar: "Administrativo de Obra" no
# mesmo top de "Cutânea"/"Vestimenta de trabalho (H)", colunas Meio de
# Propagação/Eliminação). Um reconhecedor que exige a LINHA FÍSICA inteira
# dentro da banda Função perderia esse rótulo. Corrigido separando as
# palavras da página em duas correntes (banda Função vs. resto) ANTES de
# agrupar em linha — cada corrente agrupa só consigo mesma, sem colisão.
#
# (2) O nome pode quebrar em MAIS de uma linha física (medido: "Técnico de
# Segurança do" + "Trabalho", Serra Dourada). A fronteira título/descrição
# não é "1 linha só": é a quebra de espaçamento vertical — linhas do MESMO
# parágrafo (nome ou descrição) distam ~7.4-7.6pt; a quebra entre nome e
# descrição distam ~14.9-15.0pt (medido em 12 ocorrências, 2 witnesses,
# 100% consistente — parágrafo com espaço extra no documento-fonte).
# `_LIMIAR_QUEBRA_TITULO_PT` (10.0) fica seguro no meio das duas.
#
# `pdfplumber.find_tables()` NÃO serve pra nenhuma das duas: devolve a
# página inteira como 1 única linha de tabela (bbox conferido, págs. 64/65
# Hetrin/mar), sem fronteira interna recuperável — descartado como
# instrumento, coerente com a decisão já registrada em D-ARQ-57 de não
# depender de `extract_tables()` pra este parser.

_TOLERANCIA_LINHA_PT = 2.5  # mesma técnica de _agrupar_linhas, D-ARQ-65/parser_familia_consciente.py
_TOLERANCIA_COLUNA_PT = 3.0  # mesma ordem de grandeza da tolerância de banda do D-ARQ-65
_LIMIAR_QUEBRA_TITULO_PT = 10.0  # ver nota (2) acima — medido, não estimado

# Rodapé de página, repete verbatim idêntico em toda página do intervalo
# medido (top=549.4 nos 2 witnesses) — cabe inteiro dentro da banda Função
# por coincidência de largura (4 palavras curtas). Não é nome de função
# real (verbatim, medido, não hipótese).
_RODAPE_MATRIZ_RISCO = "Matriz de Risco AIHA"


class GrupoFuncaoNaoReconhecido(ValueError):
    """Página do intervalo do grid AIHA sem cabeçalho reconhecível (Função
    / Tipo de Risco / Exposição+Propagação), ou com cabeçalho reconhecido
    mas nenhuma linha na coluna Função — sinal de roteamento pro caller
    (D-ARQ-57 peça 5 fatia 5d, fora desta fatia): página fora do grid, ou
    variante de cabeçalho ainda não medida. Nunca silêncio (D-ARQ-31/35)."""


class PalavraPDF(NamedTuple):
    """Palavra pré-extraída de uma página do PDF — mesmo contrato mínimo
    de parser_familia_consciente.py (texto + posição), independente do
    extrator real (pdfplumber no wrapper `segmentar_arquivo`)."""

    text: str
    x0: float
    top: float


class _Linha(NamedTuple):
    palavras: tuple[PalavraPDF, ...]

    @property
    def texto(self) -> str:
        return " ".join(p.text for p in self.palavras)


def _agrupar_linhas(palavras: Sequence[PalavraPDF]) -> list[_Linha]:
    """Agrupa palavras por tolerância de `top` — mesma função de
    parser_familia_consciente.py (duplicada: não existe módulo de
    primitivos comum hoje, ver nota de topo do arquivo). Quem chama decide
    QUAIS palavras entram (aqui, sempre já filtradas por coluna — ver nota
    (1) de topo do arquivo: agrupar a página inteira de uma vez, com
    colunas independentes, perderia rótulo por colisão de `top`)."""
    ordenadas = sorted(palavras, key=lambda p: p.top)
    linhas: list[list[PalavraPDF]] = []
    topo_atual: Optional[float] = None
    for p in ordenadas:
        if topo_atual is None or abs(p.top - topo_atual) > _TOLERANCIA_LINHA_PT:
            linhas.append([])
            topo_atual = p.top
        linhas[-1].append(p)
    return [_Linha(tuple(sorted(grupo, key=lambda p: p.x0))) for grupo in linhas]


def _localizar_cabecalho_grid(
    linhas: Sequence[_Linha],
) -> Optional[tuple[float, float, float]]:
    """(funcao_x0, tipo_risco_x0, header_fim_top) calibrados a partir do
    cabeçalho desta página. None se não-localizável — BLOQUEADOR (página
    sem cabeçalho reconhecível não é dado a tolerar em silêncio, mesmo
    espírito de `_localizar_cabecalho_tabela` em parser_familia_consciente.py).

    O cabeçalho quebra em VÁRIAS linhas físicas (medido: "Tipo"/"de"/
    "Código" numa linha, "Função"/"Identificação..."/"Tempo"/"Meio"/
    "Nível"/"Eliminação..." na seguinte, "Risco"/"e-Social"/
    "Probabilidade"/"Efeito"/"Classificação" na seguinte, "Exposição"/
    "Propagação"/"Risco" na última) — "Função" e "Tipo" nunca dividem a
    MESMA linha física, por isso são buscados em buscas separadas (mesmo
    padrão de `_localizar_cabecalho_tabela`, que busca GRUPO/FONTE/AGRAVO
    numa linha e PERIGO/ASPECTO em outra).

    header_fim_top = top da linha que contém "Exposição" E "Propagação"
    juntas — combinação exclusiva do cabeçalho (medido: "Exposição" sozinha
    também aparece como VALOR da coluna Tempo de Exposição em linhas de
    dado; "Propagação" só aparece no cabeçalho). Linhas com
    `top <= header_fim_top` são cabeçalho ou boilerplate de página (título
    corrido "AVALIAÇÃO GLOBAL DO PGR...", subtítulo de seção "5.1.2 -
    EXPOSIÇÃO A FATORES DE RISCO...") — nunca corpo do grid.
    """
    funcao_x0: Optional[float] = None
    for linha in linhas:
        for p in linha.palavras:
            if p.text == "Função":
                funcao_x0 = p.x0
                break
        if funcao_x0 is not None:
            break
    if funcao_x0 is None:
        return None

    tipo_x0: Optional[float] = None
    for linha in linhas:
        for p in linha.palavras:
            if p.text == "Tipo":
                tipo_x0 = p.x0
                break
        if tipo_x0 is not None:
            break
    if tipo_x0 is None:
        return None

    header_fim_top: Optional[float] = None
    for linha in linhas:
        textos = {p.text for p in linha.palavras}
        if {"Exposição", "Propagação"} <= textos:
            # max(), não palavras[0].top: a própria linha do cabeçalho tem
            # variação interna de `top` dentro da tolerância de agrupamento
            # (medido: "Risco" residual de outra sub-linha do cabeçalho,
            # top=91.26, agrupado com "Exposição"/"Propagação"/"Risco" reais
            # do cabeçalho, top=91.50, mesma _Linha) — usar a palavra mais à
            # esquerda (`palavras[0]`, ordenada por x0) subestimaria o fim
            # do cabeçalho e vazaria a própria linha do cabeçalho pro corpo
            # (Serra Dourada pág. 58: "Exposição Propagação Risco" aparecia
            # como 1ª linha de risco, antes de qualquer conteúdo real).
            header_fim_top = max(p.top for p in linha.palavras)
            break
    if header_fim_top is None:
        return None

    return funcao_x0, tipo_x0, header_fim_top


def _resolver_titulo(linhas_funcao: Sequence[_Linha]) -> Optional[str]:
    """Nome da função = linhas consecutivas da coluna Função a partir da
    1ª, unidas por espaço, até (sem incluir) a 1ª quebra de espaçamento
    >= `_LIMIAR_QUEBRA_TITULO_PT` — ver nota (2) de topo do arquivo. None
    se não houver nenhuma linha na coluna Função nesta página."""
    if not linhas_funcao:
        return None
    partes = [linhas_funcao[0].texto]
    ultimo_top = linhas_funcao[0].palavras[0].top
    for linha in linhas_funcao[1:]:
        top = linha.palavras[0].top
        if top - ultimo_top >= _LIMIAR_QUEBRA_TITULO_PT:
            break
        partes.append(linha.texto)
        ultimo_top = top
    return " ".join(partes)


class GrupoFuncaoAIHA(NamedTuple):
    """Um grupo (função) do grid AIHA com fronteira resolvida — nome
    verbatim (ver `_resolver_titulo`) + linhas fora da coluna Função de
    TODAS as páginas atribuídas a este grupo (cada página pertence
    inteira a uma função — ver nota de topo do arquivo). Decomposição N:1
    (múltiplos cargos por grupo) e parsing da célula de risco em algo do
    formato RiscoVerbatim são fatias seguintes (5b/5c) — aqui o dado é
    cru, uma `_Linha` por linha física do corpo do grid."""

    nome: str
    linhas: tuple[_Linha, ...]


def segmentar_paginas(
    paginas: Sequence[Sequence[PalavraPDF]],
) -> tuple[GrupoFuncaoAIHA, ...]:
    """Núcleo puro (D-ARQ-09) da fatia 5a (D-ARQ-57 peça 5): banda de
    coluna calibrada por página + reconhecedor de fronteira de função.

    Por página: localiza o cabeçalho (calibra a banda Função), separa as
    palavras do corpo em duas correntes (Função vs. resto) e resolve o
    nome da página (`_resolver_titulo`). Nome igual ao último aberto =
    continuação (mesmo grupo); nome novo = fecha o grupo aberto e abre um
    novo. TODAS as linhas de resto da página entram no grupo que fica
    aberto ao final da página — cada página pertence inteira a uma função.

    Zero páginas -> tupla vazia. Página sem cabeçalho reconhecível, ou com
    cabeçalho reconhecido mas sem nenhuma linha na coluna Função ->
    GrupoFuncaoNaoReconhecido (falha explícita; roteamento decide o
    fallback, fatia 5d, fora desta fatia).
    """
    grupos: list[GrupoFuncaoAIHA] = []
    nome_aberto: Optional[str] = None
    buffer_grupo: list[_Linha] = []

    for palavras_pagina in paginas:
        linhas_completas = _agrupar_linhas(palavras_pagina)
        cabecalho = _localizar_cabecalho_grid(linhas_completas)
        if cabecalho is None:
            raise GrupoFuncaoNaoReconhecido(
                "Página sem cabeçalho do grid AIHA (Função / Tipo de Risco / "
                "Exposição+Propagação) reconhecível — banda de coluna não "
                "calibrável (D-ARQ-57 peça 5 fatia 5a)"
            )
        funcao_x0, tipo_risco_x0, header_fim_top = cabecalho
        limite = tipo_risco_x0 - _TOLERANCIA_COLUNA_PT

        corpo = [p for p in palavras_pagina if p.top > header_fim_top]
        palavras_funcao = [p for p in corpo if p.x0 < limite]
        palavras_resto = [p for p in corpo if p.x0 >= limite]

        linhas_funcao = [
            linha for linha in _agrupar_linhas(palavras_funcao) if linha.texto != _RODAPE_MATRIZ_RISCO
        ]
        linhas_resto = _agrupar_linhas(palavras_resto)

        nome_pagina = _resolver_titulo(linhas_funcao)
        if nome_pagina is None:
            raise GrupoFuncaoNaoReconhecido(
                "Página com cabeçalho do grid AIHA reconhecido mas sem "
                "nenhuma linha na coluna Função — corpo do grid inesperado "
                "(D-ARQ-57 peça 5 fatia 5a)"
            )

        if nome_pagina != nome_aberto:
            if nome_aberto is not None:
                grupos.append(GrupoFuncaoAIHA(nome=nome_aberto, linhas=tuple(buffer_grupo)))
            nome_aberto = nome_pagina
            buffer_grupo = []
        buffer_grupo.extend(linhas_resto)

    if nome_aberto is not None:
        grupos.append(GrupoFuncaoAIHA(nome=nome_aberto, linhas=tuple(buffer_grupo)))

    return tuple(grupos)


def segmentar_arquivo(
    caminho: Path, pagina_inicio: int, pagina_fim: int
) -> tuple[GrupoFuncaoAIHA, ...]:
    """Wrapper de I/O (D-ARQ-09): único ponto do módulo que toca disco.
    `pagina_inicio`/`pagina_fim` são 0-indexed, ambos inclusive — o
    intervalo de páginas do grid AIHA dentro do PGR, que o roteamento
    (fatia 5d, fora desta fatia) é quem identifica; esta fatia não varre o
    documento inteiro procurando o grid."""
    paginas = [
        tuple(
            PalavraPDF(text=w["text"], x0=w["x0"], top=w["top"])
            for w in page.extract_words()
        )
        for indice, page in enumerate(paginas_liberadas(caminho))
        if pagina_inicio <= indice <= pagina_fim
    ]
    return segmentar_paginas(paginas)
