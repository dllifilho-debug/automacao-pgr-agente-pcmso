from __future__ import annotations

from pathlib import Path
from typing import Optional

import pdfplumber


def extrair_tabelas_fds(caminho: Path) -> list[list[list[Optional[str]]]]:
    """DEPRECATED (003.BA): entrada de composição migrou para texto-puro (D-ARQ-42);
    mantida para rastreabilidade, sem consumidor no motor.

    Parse-PDF determinístico da transcrição-FDS (D-ARQ-42 Parte 1).

    Devolve as tabelas CRUAS de extract_tables() de todas as páginas, achatadas numa
    única lista (fronteira de página DESCARTADA nesta fatia — a composição aparece em
    páginas variáveis: pág 0 em Ciplan/Tigre/tinta, pág 2 em Leinertex/Massa; o
    consumidor varre todas as tabelas procurando o header de composição, não "a tabela
    da página X").

    NÃO localiza a região de composição, NÃO interpreta coluna, NÃO desambigua o \\n
    (separador-multi-CAS vs quebra-de-render intra-token), NÃO mapeia grafias de
    CAS-ausente, NÃO monta Componente. Tudo isso é transcrição (DT-003AS-01), fatia
    seguinte. Aqui só extração bruta: bytes -> tabelas cruas, células str | None
    exatamente como o pdfplumber as devolve.

    [DERIVADO — page.extract_tables() puro, medição 003.AS sobre os 6 PDFs de
    fds_originais/; D-ARQ-43 Parte 1 (parse-PDF é camada de texto, sem OCR).]
    """
    tabelas: list[list[list[Optional[str]]]] = []
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            tabelas.extend(page.extract_tables())
    return tabelas
