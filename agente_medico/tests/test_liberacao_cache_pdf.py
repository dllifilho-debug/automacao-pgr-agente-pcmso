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
test_parsear_arquivo_devolve_19_blocos etc., sobre o PGR Fascino).

Escolha de PDF por teste: o teste de extrair_texto_pgr usa o PGR Viverde
(tracked no git — ver test_extracao_pgr.py, mesma convenção) para que o
discriminante de ORDEM rode em qualquer clone, sem depender de acervo
untracked. O teste de parsear_arquivo precisa de um PDF da família
Consciente/Fascino (o Viverde não é reconhecido por essa família — cairia
no fallback LLM, fora do escopo determinístico); o único PDF dessa família
no repositório (Fascino) NÃO está tracked, então esse teste sozinho continua
dependendo de acervo local e skipa em clone limpo. Os dois exercitam o MESMO
helper (paginas_liberadas) — o teste do Viverde já protege a correção fora
do host de desenvolvimento; o do Fascino é reforço quando o acervo está
presente."""

from __future__ import annotations

from pathlib import Path

import pdfplumber
import pdfplumber.page
import pytest

from agente_medico.motor.extracao_pgr import extrair_texto_pgr
from agente_medico.motor.parser_familia_consciente import parsear_arquivo

# PDF é tracked no git (matrizes_originais/) — mesma convenção de
# test_extracao_pgr.py: ausência é falha explícita, não skip.
CAMINHO_PGR_VIVERDE = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")

# Família Consciente/Fascino (parser_familia_consciente só reconhece essa
# família — o Viverde cairia no fallback LLM). Este PDF NÃO está tracked no
# git (medido: ausente de `git ls-files matrizes_originais/`) — dívida do
# acervo, não escolha deste teste; skipa em clone limpo até a fixture ser
# versionada ou substituída por um PDF sintético da família.
CAMINHO_PGR_FASCINO = Path(
    "matrizes_originais/PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"
)

requer_pdf_fascino = pytest.mark.skipif(
    not CAMINHO_PGR_FASCINO.exists(),
    reason="PDF Fascino ausente (não tracked); harness 003.ET indisponível neste clone",
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


def test_extrair_texto_pgr_libera_pagina_durante_a_extracao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    n_paginas = _contar_paginas(CAMINHO_PGR_VIVERDE)
    assert n_paginas > 1  # guarda anti-vazio

    eventos = _espionar_sequencia(monkeypatch, "extract_text")
    extrair_texto_pgr(CAMINHO_PGR_VIVERDE)

    _assert_liberacao_durante_extracao(eventos, n_paginas)


@requer_pdf_fascino
def test_parsear_arquivo_libera_pagina_durante_a_extracao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    n_paginas = _contar_paginas(CAMINHO_PGR_FASCINO)
    assert n_paginas > 1  # guarda anti-vazio

    eventos = _espionar_sequencia(monkeypatch, "extract_words")
    parsear_arquivo(CAMINHO_PGR_FASCINO)

    _assert_liberacao_durante_extracao(eventos, n_paginas)
