from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page


def paginas_liberadas(caminho: Path) -> Iterator[Page]:
    """Abre `caminho` com pdfplumber e entrega cada página, chamando
    `Page.close()` assim que o consumidor termina de usá-la.

    Sem isso, o cache por página do pdfplumber sobrevive até o objeto PDF
    inteiro fechar — pico de memória cresce com o nº de páginas em vez de
    ficar limitado a uma página por vez. `flush_cache()` sozinho corta só
    parte do pico; `close()` é o que resolve [MEDIDO — 003.ET fatia 2].
    """
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            yield page
            page.close()
