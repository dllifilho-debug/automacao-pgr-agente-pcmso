from __future__ import annotations

from collections.abc import Sequence
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


_ANCORA_GHE = "SETOR/FUNÇÃO"


def recortar_blocos_ghe(paginas: Sequence[str]) -> list[str]:
    """Núcleo puro (sem I/O) do recorte determinístico dos blocos GHE
    (esqueleto D-ARQ-49 P2; D-ARQ-50). paginas = saída de extrair_texto_pgr,
    lista-por-página, na ordem do documento.

    Âncora: linha.startswith(_ANCORA_GHE), match VERBATIM — sem normalização
    (difere do molde _recortar_composicao da FDS de propósito: medição 003.BM
    achou n=1 forma de âncora no acervo Viverde, com o gate de 42 ocorrências
    provando estabilidade; o limite dessa escolha é documentado abaixo,
    classe D-ARQ-22).

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

    Limites (D-ARQ-22): âncora derivada de n=1 (PGR Viverde), gate de 42
    blocos medido em 003.BM; conteúdo do documento ANTES da 1ª âncora
    (pág. 33) é descartado (fora de qualquer bloco); a cauda do ÚLTIMO bloco
    (última âncora na pág. 146 de 151) sobre-inclui as 4 páginas finais do
    documento até o fim — medido no script descartável de 003.BM, nunca
    cortado fino aqui.

    NÃO separa cargo/risco/quantificação dentro do bloco, NÃO transcreve,
    NÃO classifica GHE — tudo isso é fatia futura (transcrição-LLM).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if linha.startswith(_ANCORA_GHE)]
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
    descarta, da 1ª linha do documento até a linha ANTERIOR à 1ª âncora
    _ANCORA_GHE. A transcrição-LLM do conteúdo do topo é fatia futura.

    paginas = saída de extrair_texto_pgr, lista-por-página, na ordem do
    documento. As linhas de todas as páginas são achatadas numa sequência
    única, na ordem do documento (fronteira de página vira "\\n" na
    reconstrução do texto), e juntadas com "\\n" — exatamente como em
    recortar_blocos_ghe. Reusa _ANCORA_GHE e o mesmo critério
    linha.startswith(_ANCORA_GHE), VERBATIM, sem normalização.

    Zero âncoras -> None (falha explícita; quem transforma isso em Pendência
    é o chamador, fatia futura — nunca devolver o documento inteiro como
    fallback). 1ª âncora na 1ª linha do documento -> "" (topo genuinamente
    vazio). Caso contrário -> topo VERBATIM (acentos, caixa preservados).

    Limite herdado (classe D-ARQ-22): âncora derivada de n=1 (PGR Viverde)
    como fronteira-fim do topo; generalização para múltiplos PGRs é
    requisito (b) da 003.BS, sessão à parte.

    Sem I/O, sem LLM (D-ARQ-09), sem parse de conteúdo do topo (emissão, RT,
    validade = fatias 2-3, ADIADAS POR MEDIÇÃO — DT-003L-01).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if linha.startswith(_ANCORA_GHE)]
    if not indices_ancora:
        return None
    return "\n".join(linhas[: indices_ancora[0]])
