from __future__ import annotations

import logging
import math
import os
import json
import subprocess
import sys
from collections.abc import Iterator
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path

import pdfplumber
from pdfplumber.page import Page

from agente_medico.motor.glifos_pdf import GerenciadorComGlifos

_log = logging.getLogger(__name__)

# Abaixo disso, subir processos custa mais que ler em série.
_MIN_PAGINAS_PARALELO = 16
_MAX_PROCESSOS_PADRAO = 4
# Raiz do repositório: cwd do subprocesso, para `-m agente_medico...` resolver.
_RAIZ = Path(__file__).resolve().parents[2]


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
        with ThreadPoolExecutor(max_workers=n) as pool:
            partes = list(pool.map(lambda f: _ler_faixa_em_subprocesso(caminho, *f), faixas))
    except (subprocess.CalledProcessError, OSError, ValueError) as e:
        _log.warning("Leitura paralela de %s falhou (%s); lendo em série.", caminho, e)
        return tuple(ler_faixa(caminho, 0, total))
    return tuple(p for parte in partes for p in parte)


def _ler_faixa_em_subprocesso(caminho: Path, inicio: int, fim: int) -> list[PaginaLida]:
    # Subprocesso próprio, não multiprocessing: o `spawn` reimporta o módulo
    # principal de quem chama, e sob `streamlit run` esse módulo é o script do
    # app — cada filho reexecutava a página e o pool quebrava [MEDIDO —
    # 01/10/2026, RuntimeError de bootstrapping em `streamlit run`].
    saida = subprocess.run(
        [sys.executable, "-m", "agente_medico.motor.io_pdf", str(Path(caminho).resolve()), str(inicio), str(fim)],
        cwd=_RAIZ,
        capture_output=True,
        check=True,
    )
    return [
        PaginaLida(texto, tuple((t, x0, top) for t, x0, top in palavras))
        for texto, palavras in json.loads(saida.stdout)
    ]


if __name__ == "__main__":
    _caminho, _inicio, _fim = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    # JSON de tipos simples: a classe deste módulo, rodando como __main__, não
    # seria a mesma do processo que lê a saída. float sai em repr, ida e volta exata.
    json.dump(
        [[p.texto, [list(w) for w in p.palavras]] for p in ler_faixa(Path(_caminho), _inicio, _fim)],
        sys.stdout,
    )
