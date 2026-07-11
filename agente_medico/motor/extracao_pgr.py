from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path

import pdfplumber


def extrair_texto_pgr(caminho: Path) -> list[str]:
    """Parse-doc determinístico do parse-PGR (D-ARQ-49 P1; D-ARQ-50 P1):
    texto VERBATIM por página do PDF do PGR, via pdfplumber.extract_text
    (text-puro, camada de texto). Página sem texto -> "".

    Fronteira de página PRESERVADA (difere de extrair_tabelas_fds, que a
    descartou): blocos GHE cruzam páginas e o recorte futuro consome
    lista-por-página (mesmo shape do núcleo _recortar_composicao da FDS).

    NÃO localiza bloco GHE, NÃO separa agente/quantificação, NÃO transcreve,
    NÃO emite slug — tudo fatia futura (transcrição-LLM, D-ARQ-50 P2/C3).
    Sem LLM aqui (D-ARQ-09). Limites: PDF sem camada de texto (escaneado)
    devolve páginas vazias — detecção/contingência OCR é do chamador, fatia
    futura (D-ARQ-43 P1); .docx é cross-check/fallback futuro, não entrada
    primária (D-ARQ-50 P1).

    [DERIVADO — pdfplumber.extract_text puro; medição 003.BK sobre
    matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf, D-ARQ-50.]
    """
    with pdfplumber.open(caminho) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _reconhece_cabecalho_ghe_padrao(linha: str) -> bool:
    linha_normalizada = linha.strip()
    if len(linha_normalizada) > 80:
        return False
    return re.fullmatch(
        r"(INVENTÁRIO DE RISCO )?GHE:? \d+(\s*-\s*.+)?", linha_normalizada
    ) is not None


_RECONHECEDORES_GHE: tuple[Callable[[str], bool], ...] = (
    _reconhece_cabecalho_ghe_padrao,
)


def eh_cabecalho_ghe(linha: str) -> bool:
    """Reconhecedor de linha-âncora de bloco GHE (D-ARQ-57 peça 1, consome
    DT-003CM-01): função pura, verdadeiro sse ALGUM reconhecedor do
    repertório _RECONHECEDORES_GHE casar a linha.

    Substitui a âncora fixa _ANCORA_GHE = "SETOR/FUNÇÃO" (n=1, medição
    003.BM/003.BL). O único reconhecedor hoje cobre as 4 formas de
    cabeçalho medidas em DT-003CM-01 sobre o acervo de 15 PGRs:
    1. "GHE 12" (Viverde)
    2. "GHE 12 - TÍTULO" (Vistamérica/CMO/Seconci/TPB/AURO)
    3. "INVENTÁRIO DE RISCO GHE 12" (ALT T65/EURO)
    4. "GHE: 07 - TÍTULO" (R78 Naturia)

    Estruturado como tupla de funções linha->bool em disjunção para
    extensão futura (novas formas de cabeçalho) sem tocar o consumidor
    (recortar_blocos_ghe/recortar_topo).
    """
    return any(reconhecedor(linha) for reconhecedor in _RECONHECEDORES_GHE)


def recortar_blocos_ghe(paginas: Sequence[str]) -> list[str]:
    """Núcleo puro (sem I/O) do recorte determinístico dos blocos GHE
    (esqueleto D-ARQ-49 P2; D-ARQ-50; âncora trocada por D-ARQ-57 peça 1).
    paginas = saída de extrair_texto_pgr, lista-por-página, na ordem do
    documento.

    Âncora: eh_cabecalho_ghe(linha) — repertório de reconhecedores de
    cabeçalho GHE (D-ARQ-57 peça 1, consome DT-003CM-01), VERBATIM — sem
    normalização de acento/caixa (difere do molde _recortar_composicao da
    FDS de propósito). A âncora "SETOR/FUNÇÃO" (n=1, medição 003.BM) sofria
    de conflação (D-ARQ-22): no Viverde ela também abre a 2ª seção
    PROCESSO/SUBPROCESSO, sem linha de cabeçalho GHE — essa 2ª seção deixa
    de casar com a nova âncora, por design (resolve a conflação em vez de
    contorná-la).

    As linhas de todas as páginas são achatadas numa sequência única, na
    ordem do documento (fronteira de página vira "\\n" na reconstrução do
    texto, como no molde _recortar_composicao). Bloco i = da linha da âncora
    i até a linha anterior à âncora i+1; o último bloco vai até a última
    linha do documento.

    Blocos são CONTÍGUOS e a sobre-inclusão é direção segura (D-ARQ-31/35):
    o grid de classificação I/O/T/probabilidade/severidade/grau-de-risco e a
    cauda do documento (rodapé, próximo processo/etapa) ficam dentro do
    bloco como RUÍDO — são descartados a jusante pela transcrição-LLM
    (D-ARQ-50 C3), nunca cortados finos aqui.

    Zero âncoras -> [] (falha explícita; quem transforma isso em Pendência é
    o chamador, fatia futura — nunca devolver o documento inteiro como
    fallback).

    Saída VERBATIM (acentos, caixa preservados) — sem I/O, sem LLM
    (D-ARQ-09), sem termo->slug.

    Limites (D-ARQ-22): repertório derivado de 15 PGRs (DT-003CM-01), gate
    de 31 blocos sobre o Viverde após a troca de âncora (regressão explícita
    de 42 para 31 em relação à âncora "SETOR/FUNÇÃO", pela resolução da
    conflação com a 2ª seção PROCESSO/SUBPROCESSO); conteúdo do documento
    ANTES da 1ª âncora (pág. 33) é descartado (fora de qualquer bloco); a
    cauda do ÚLTIMO bloco (última âncora na pág. 146 de 151) sobre-inclui as
    4 páginas finais do documento até o fim — medido no script descartável
    de 003.BM, nunca cortado fino aqui.

    NÃO separa cargo/risco/quantificação dentro do bloco, NÃO transcreve,
    NÃO classifica GHE — tudo isso é fatia futura (transcrição-LLM).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)]
    if not indices_ancora:
        return []
    limites = [*indices_ancora, len(linhas)]
    return [
        "\n".join(linhas[inicio:fim])
        for inicio, fim in zip(limites, limites[1:])
    ]


def recortar_topo(paginas: Sequence[str]) -> str | None:
    """Núcleo puro (sem I/O) do recorte-de-topo (D-ARQ-53 parte 1): inverso
    determinístico de recortar_blocos_ghe — devolve a região que aquele
    descarta, da 1ª linha do documento até a linha ANTERIOR à 1ª âncora de
    cabeçalho GHE. A transcrição-LLM do conteúdo do topo é fatia futura.

    paginas = saída de extrair_texto_pgr, lista-por-página, na ordem do
    documento. As linhas de todas as páginas são achatadas numa sequência
    única, na ordem do documento (fronteira de página vira "\\n" na
    reconstrução do texto), e juntadas com "\\n" — exatamente como em
    recortar_blocos_ghe. Reusa eh_cabecalho_ghe (D-ARQ-57 peça 1), VERBATIM,
    sem normalização.

    Zero âncoras -> None (falha explícita; quem transforma isso em Pendência
    é o chamador, fatia futura — nunca devolver o documento inteiro como
    fallback). 1ª âncora na 1ª linha do documento -> "" (topo genuinamente
    vazio). Caso contrário -> topo VERBATIM (acentos, caixa preservados).

    Limite herdado (classe D-ARQ-22): repertório de reconhecedores derivado
    de 15 PGRs (DT-003CM-01) como fronteira-fim do topo; generalização para
    novas formas de cabeçalho fora do acervo medido é requisito futuro.

    Sem I/O, sem LLM (D-ARQ-09), sem parse de conteúdo do topo (emissão, RT,
    validade = fatias 2-3, ADIADAS POR MEDIÇÃO — DT-003L-01).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)]
    if not indices_ancora:
        return None
    return "\n".join(linhas[: indices_ancora[0]])
