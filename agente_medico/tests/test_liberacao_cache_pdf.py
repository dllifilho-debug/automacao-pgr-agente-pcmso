"""Guarda a liberação de cache de página do pdfplumber (003.ET fatia 2):
os wrappers de I/O que consomem páginas via `paginas_liberadas` têm de
fechar cada página DURANTE a extração — não só no fim.

O discriminante é ORDEM, não contagem. `pdfplumber.pdf.PDF.close()` (chamado
ao sair do `with pdfplumber.open(...)` de `paginas_liberadas`) já refecha
sozinho todas as páginas do documento; qualquer implementação correta,
portanto, dispara `Page.close()` mais vezes que o nº de páginas — contar
chamadas não discrimina liberação-durante de liberação-só-no-fim. O que
discrimina é: pelo menos um `close()` acontece ANTES da extração da ÚLTIMA
página. Numa implementação que só libera no fim (ou que troca `close()` por
`flush_cache()` no laço — este último não dispara evento nenhum, porque
espionamos `close`, não `flush_cache`), todo `close()` observado vem DEPOIS
de todas as extrações, porque só o refechamento do with-exit os produz.

Espiona `Page.close`, não `Page.flush_cache`: medição do Arquiteto (prompt
003.ET) mostrou que `flush_cache()` sozinho corta só parte do pico (398 MB
contra 88 MB) — um teste sobre `flush_cache` ficaria verde numa
implementação que entrega o resultado errado.

Reversões nomeadas, ambas devem deixar `_assert_liberacao_durante_extracao`
vermelho:
(a) remover a chamada de `close()` do laço em `agente_medico/motor/io_pdf.py`
    — sobra só o refechamento do with-exit, nenhum close antes do fim;
(b) trocar `close()` por `flush_cache()` no mesmo laço — mesmo efeito na
    sequência, porque `flush_cache` não é espionado.

Caso B (saída inalterada) não é duplicado aqui: já coberto por
test_extracao_pgr.py (test_numero_de_paginas, test_toda_pagina_e_str,
test_ghe_pintura_preserva_adjacencia_agente_valor etc., sobre o PGR Viverde)
e por test_parser_familia_consciente.py (fixture ghes_fascino +
test_parsear_arquivo_devolve_19_blocos etc., sobre o PGR Fascino)."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import pdfplumber.page
import pytest

from agente_medico.motor.extracao_pgr import extrair_texto_pgr
from agente_medico.motor.parser_familia_consciente import parsear_arquivo

# 18 páginas, ASCII, já tracked e usado por test_extracao_pgr.py
# (CAMINHO_PGR_CJR) — reaproveita um PDF já pago pela suíte em vez de
# introduzir mais um reparse caro (custo nomeado em CLAUDE.md/DH-003EC-02).
CAMINHO_PGR = Path("matrizes_originais/pgr_Cjr Engenharia Ltda (M Construtora).pdf")

requer_pdf = pytest.mark.skipif(
    not CAMINHO_PGR.exists(), reason="PDF Cjr ausente; harness 003.ET indisponível"
)


def _contar_paginas(caminho: Path) -> int:
    with pdfplumber.open(caminho) as pdf:
        return len(pdf.pages)


def _espionar_sequencia(monkeypatch: pytest.MonkeyPatch, metodo_extracao: str) -> list[str]:
    eventos: list[str] = []

    original_extrair = getattr(pdfplumber.page.Page, metodo_extracao)

    def _extrair_espiao(self: pdfplumber.page.Page, *a: object, **kw: object) -> object:
        eventos.append("extrai")
        return original_extrair(self, *a, **kw)

    original_close = pdfplumber.page.Page.close

    def _close_espiao(self: pdfplumber.page.Page) -> None:
        eventos.append("fecha")
        original_close(self)

    monkeypatch.setattr(pdfplumber.page.Page, metodo_extracao, _extrair_espiao)
    monkeypatch.setattr(pdfplumber.page.Page, "close", _close_espiao)
    return eventos


def _assert_liberacao_durante_extracao(eventos: list[str], n_paginas: int) -> None:
    assert eventos.count("extrai") == n_paginas
    assert eventos.count("fecha") >= n_paginas  # sanidade: nenhuma pagina ficou sem fechar

    indice_ultima_extracao = max(i for i, e in enumerate(eventos) if e == "extrai")
    fechou_antes_do_fim = any(e == "fecha" for e in eventos[:indice_ultima_extracao])
    assert fechou_antes_do_fim, (
        "nenhuma pagina foi fechada antes da extracao da ultima pagina — "
        "liberacao so no fim (nao durante), ou close() nao esta sendo chamado no laco"
    )


@requer_pdf
def test_extrair_texto_pgr_libera_pagina_durante_a_extracao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    n_paginas = _contar_paginas(CAMINHO_PGR)
    assert n_paginas > 1  # guarda anti-vazio

    eventos = _espionar_sequencia(monkeypatch, "extract_text")
    extrair_texto_pgr(CAMINHO_PGR)

    _assert_liberacao_durante_extracao(eventos, n_paginas)


@requer_pdf
def test_parsear_arquivo_libera_pagina_durante_a_extracao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    n_paginas = _contar_paginas(CAMINHO_PGR)
    assert n_paginas > 1  # guarda anti-vazio

    eventos = _espionar_sequencia(monkeypatch, "extract_words")
    parsear_arquivo(CAMINHO_PGR)

    _assert_liberacao_durante_extracao(eventos, n_paginas)
