from __future__ import annotations

import logging
import math
import os
from collections.abc import Iterator
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from multiprocessing import get_context
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page

from agente_medico.motor.glifos_pdf import GerenciadorComGlifos

_log = logging.getLogger(__name__)

# Abaixo disso, subir processos custa mais que ler em série.
_MIN_PAGINAS_PARALELO = 16
_MAX_PROCESSOS_PADRAO = 4
_ENV_PROCESSOS = "PCMSO_PDF_PROCESSOS"


def paginas_liberadas(caminho: Path) -> Iterator[Page]:
    """Abre `caminho` com pdfplumber e entrega cada página, chamando
    `Page.close()` assim que o consumidor termina de usá-la.

    Sem isso, o cache por página do pdfplumber sobrevive até o objeto PDF
    inteiro fechar — pico de memória cresce com o nº de páginas em vez de
    ficar limitado a uma página por vez. `flush_cache()` sozinho corta só
    parte do pico; `close()` é o que resolve [MEDIDO — 003.ET fatia 2].
    """
    with pdfplumber.open(caminho) as pdf:
        # D-ARQ-89 cl.1: antes da primeira página, que é quando o pdfplumber
        # passa a usar o gerenciador para carregar fontes.
        pdf.rsrcmgr = GerenciadorComGlifos()
        for page in pdf.pages:
            yield page
            page.close()


@dataclass(frozen=True)
class PaginaLida:
    """Uma página lida uma vez: o texto de `extract_text` e as palavras de
    `extract_words` como (texto, x0, top). Os dois saem do mesmo layout da
    página, calculado uma vez só."""

    texto: str
    palavras: tuple[tuple[str, float, float], ...]


def ler_faixa(caminho: Path, inicio: int, fim: int) -> list[PaginaLida]:
    """Lê as páginas [inicio, fim) com o mesmo cuidado de
    `paginas_liberadas`: glifos restaurados (D-ARQ-89) e `close()` por
    página durante a leitura (003.ET)."""
    lidas: list[PaginaLida] = []
    with pdfplumber.open(caminho) as pdf:
        pdf.rsrcmgr = GerenciadorComGlifos()
        for page in pdf.pages[inicio:fim]:
            texto = page.extract_text() or ""
            palavras = tuple((w["text"], w["x0"], w["top"]) for w in page.extract_words())
            lidas.append(PaginaLida(texto, palavras))
            page.close()
    return lidas


def processos_padrao() -> int:
    """`PCMSO_PDF_PROCESSOS` se definido; senão min(4, nº de CPUs)."""
    bruto = os.environ.get(_ENV_PROCESSOS)
    if bruto is not None:
        try:
            valor = int(bruto)
        except ValueError as e:
            raise ValueError(f"{_ENV_PROCESSOS}={bruto!r} não é inteiro") from e
        if valor < 1:
            raise ValueError(f"{_ENV_PROCESSOS}={bruto!r} deve ser >= 1")
        return valor
    return min(_MAX_PROCESSOS_PADRAO, os.cpu_count() or 1)


def _faixas(total: int, processos: int) -> list[tuple[int, int]]:
    # Duas faixas por processo: páginas de tabela custam mais que as de texto
    # corrido, e faixas menores equilibram a carga entre os processos.
    passo = max(1, math.ceil(total / (processos * 2)))
    return [(i, min(i + passo, total)) for i in range(0, total, passo)]


def ler_pdf(caminho: Path, processos: int | None = None) -> tuple[PaginaLida, ...]:
    """Leitura única do PDF, por faixas de páginas em processos separados.
    O resultado é o mesmo da leitura em série, página a página e na ordem
    do documento; se o pool falhar, lê em série."""
    n = processos_padrao() if processos is None else processos
    with pdfplumber.open(caminho) as pdf:
        total = len(pdf.pages)
    if n <= 1 or total < _MIN_PAGINAS_PARALELO:
        return tuple(ler_faixa(caminho, 0, total))

    faixas = _faixas(total, n)
    try:
        # spawn: o mesmo comportamento no Linux do deploy e no Windows local,
        # sem herdar threads do Streamlit num fork.
        with ProcessPoolExecutor(max_workers=n, mp_context=get_context("spawn")) as pool:
            partes = list(pool.map(ler_faixa, [caminho] * len(faixas), *zip(*faixas)))
    except (BrokenProcessPool, OSError) as e:
        _log.warning("Leitura paralela de %s falhou (%s); lendo em série.", caminho, e)
        return tuple(ler_faixa(caminho, 0, total))
    return tuple(p for parte in partes for p in parte)
