from __future__ import annotations

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
