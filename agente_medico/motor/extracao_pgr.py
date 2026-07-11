from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path

import pdfplumber

from agente_medico.motor.tipos import Pendencia

# D-ARQ-57 peça 2 (gate anti-Vistamérica): limiares calibrados em 003.CP sobre
# os 15 PGRs de DT-003CM-01.
_LIMIAR_DENSIDADE_PCT = 40.0  # maior legítimo medido: 34,8% (ALT T65); implausíveis ≥ 44,4%
_LIMIAR_PAGINAS_DOC_MINIMO = 10  # ≤1 bloco em doc > 10 págs → implausível


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


def avaliar_segmentacao(paginas: Sequence[str]) -> Pendencia | None:
    """Gate anti-Vistamérica (D-ARQ-57 peça 2): detecta segmentação GHE
    implausível por densidade + contagem, sem depender de conteúdo — só da
    forma do recorte de recortar_blocos_ghe. Limiares calibrados em 003.CP
    sobre os 15 PGRs de DT-003CM-01, ratificado em 003.CN.

    Reproduz o mesmo achatamento e a mesma fronteira de bloco de
    recortar_blocos_ghe (âncora via eh_cabecalho_ghe, bloco i = âncora i até
    a linha anterior à âncora i+1, último bloco até o fim), mas rastreia a
    página 1-based de cada linha achatada para medir a extensão em páginas de
    cada bloco: pag(última linha do bloco) - pag(linha da âncora) + 1.

    Dois testes independentes, qualquer um decide implausibilidade:
    - Contagem: <= 1 bloco (inclui zero âncoras) num documento com mais de
      _LIMIAR_PAGINAS_DOC_MINIMO páginas — massa insuficiente para um único
      bloco cobrir o documento inteiro ser plausível.
    - Densidade: maior bloco ocupa mais de _LIMIAR_DENSIDADE_PCT% do total de
      páginas do documento.

    Sem I/O, sem LLM (D-ARQ-09); não altera recortar_blocos_ghe/recortar_topo.
    """
    linhas_com_pagina: list[tuple[int, str]] = [
        (indice_pagina + 1, linha)
        for indice_pagina, pagina in enumerate(paginas)
        for linha in pagina.splitlines()
    ]
    indices_ancora = [
        i for i, (_, linha) in enumerate(linhas_com_pagina) if eh_cabecalho_ghe(linha)
    ]
    n_blocos = len(indices_ancora)
    total_paginas = len(paginas)

    if n_blocos <= 1 and total_paginas > _LIMIAR_PAGINAS_DOC_MINIMO:
        return Pendencia(
            tipo="segmentacao_implausivel",
            destinatario="extracao",
            motivo=(
                f"Segmentação implausível: {n_blocos} bloco(s) GHE detectado(s) "
                f"em documento de {total_paginas} páginas"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-57",
            ghe_id=None,
        )

    if n_blocos == 0:
        return None

    limites = [*indices_ancora, len(linhas_com_pagina)]
    maior_extensao_paginas = max(
        linhas_com_pagina[fim - 1][0] - linhas_com_pagina[inicio][0] + 1
        for inicio, fim in zip(limites, limites[1:])
    )
    percentual_maior_bloco = (maior_extensao_paginas / total_paginas) * 100

    if percentual_maior_bloco > _LIMIAR_DENSIDADE_PCT:
        return Pendencia(
            tipo="segmentacao_implausivel",
            destinatario="extracao",
            motivo=(
                f"Segmentação implausível: maior bloco GHE ocupa "
                f"{maior_extensao_paginas} de {total_paginas} páginas "
                f"({percentual_maior_bloco:.1f}%)"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-57",
            ghe_id=None,
        )

    return None
