"""Leitura única do PDF (`io_pdf.ler_pdf`): por faixas de páginas em processos
separados, com texto e palavras idênticos aos de `extrair_texto_pgr` e
`parsear_arquivo`. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pdfplumber
import pdfplumber.page
import pytest

import agente_medico.adaptadores.orquestracao_pgr as orq
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline
from agente_medico.motor import io_pdf
from agente_medico.motor.extracao_pgr import extrair_texto_pgr
from agente_medico.motor.io_pdf import PaginaLida, ler_faixa, ler_pdf, paginas_liberadas, processos_padrao
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import EnvelopeConfirmado, GHEVerbatim, RiscoVerbatim
from agente_medico.tests.test_liberacao_cache_pdf import (
    _assert_liberacao_durante_extracao,
    _espionar_sequencia,
)

_VIVERDE = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")
_FASCINO = Path(
    "matrizes_originais/PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"
)
_GHE = GHEVerbatim(
    nome="Setor Teste",
    cargos=("Servente",),
    riscos=(RiscoVerbatim(agente="Ruido", quantificacao="82,2 dB(A)", fonte_geradora="Fonte X"),),
)
requer_fascino = pytest.mark.skipif(not _FASCINO.exists(), reason="PDF Fascino ausente (não tracked)")


@pytest.fixture(scope="module")
def leitura_viverde_paralela() -> tuple[PaginaLida, ...]:
    return ler_pdf(_VIVERDE, processos=2)


def test_leitura_paralela_da_o_texto_e_as_palavras_da_leitura_atual(
    leitura_viverde_paralela: tuple[PaginaLida, ...],
) -> None:
    # Reversões que matam: (1) juntar as faixas fora da ordem do documento;
    # (2) faixa com fim exclusivo errado (i + passo - 1) — perde uma página por
    # faixa.
    palavras = [
        tuple((w["text"], w["x0"], w["top"]) for w in pg.extract_words()) for pg in paginas_liberadas(_VIVERDE)
    ]
    assert [p.texto for p in leitura_viverde_paralela] == extrair_texto_pgr(_VIVERDE)
    assert [p.palavras for p in leitura_viverde_paralela] == palavras


@requer_fascino
def test_leitura_paralela_restaura_glifos(monkeypatch: pytest.MonkeyPatch) -> None:
    # D-ARQ-89: os processos filhos também usam GerenciadorComGlifos.
    # Reversão que mata: tirar `pdf.rsrcmgr = GerenciadorComGlifos()` de ler_faixa.
    assert [p.texto for p in ler_pdf(_FASCINO, processos=2)] == extrair_texto_pgr(_FASCINO)


def test_ler_faixa_libera_pagina_durante_a_leitura(monkeypatch: pytest.MonkeyPatch) -> None:
    # 003.ET no processo filho: a espionagem só enxerga o processo corrente, então
    # o teste chama a função do filho direto. Reversões que matam: tirar
    # `page.close()` do laço de ler_faixa, ou trocá-lo por `flush_cache()`.
    with pdfplumber.open(_VIVERDE) as pdf:
        n_paginas = min(len(pdf.pages), 10)
    eventos = _espionar_sequencia(monkeypatch, "extract_text")
    ler_faixa(_VIVERDE, 0, n_paginas)
    _assert_liberacao_durante_extracao(eventos, n_paginas)


def test_pool_quebrado_cai_para_leitura_em_serie(
    monkeypatch: pytest.MonkeyPatch, leitura_viverde_paralela: tuple[PaginaLida, ...]
) -> None:
    # Reversão que mata: tirar o `except (BrokenProcessPool, OSError)` de ler_pdf —
    # a falha do pool sobe e o PGR não é lido.
    class _PoolQuebrado:
        def __init__(self, *a: Any, **k: Any) -> None:
            raise OSError("sem processos (teste)")

    monkeypatch.setattr(io_pdf, "ProcessPoolExecutor", _PoolQuebrado)
    assert ler_pdf(_VIVERDE, processos=2) == leitura_viverde_paralela


@pytest.mark.parametrize("valor", ["0", "dois"])
def test_variavel_de_processos_invalida_e_erro(monkeypatch: pytest.MonkeyPatch, valor: str) -> None:
    # Reversão que mata: aceitar o valor em silêncio (0 cairia na leitura em
    # série sem aviso; texto derrubaria o app longe da causa).
    monkeypatch.setenv("PCMSO_PDF_PROCESSOS", valor)
    with pytest.raises(ValueError, match="PCMSO_PDF_PROCESSOS"):
        processos_padrao()


def test_processamento_le_o_pdf_uma_vez(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões que matam: (1) preparar_pgr_hidratado chamar preparar_ghes sem a
    # leitura — preparar_ghes lê de novo; (2) o sinal psicossocial voltar a
    # extrair o texto do arquivo; (3) o parser determinístico voltar a
    # parsear_arquivo(caminho). Qualquer abertura do PDF fora de ler_pdf falha.
    chamadas: list[Path] = []
    leitura = (PaginaLida("GHE 1 - Setor Teste\nCargo A\nOutraLinha", ()),)

    def _ler(caminho: Path, processos: int | None = None) -> tuple[PaginaLida, ...]:
        chamadas.append(caminho)
        return leitura

    def _abrir(*a: Any, **k: Any) -> Any:
        raise AssertionError("PDF aberto fora de ler_pdf")

    monkeypatch.setattr(orq, "ler_pdf", _ler)
    # Rota determinística aceita (1 bloco no texto, 1 GHE no parser), para o
    # fluxo chegar ao sinal psicossocial.
    monkeypatch.setattr(orq, "parsear_leitura", lambda _: (_GHE,))
    monkeypatch.setattr(pdfplumber, "open", _abrir)
    pgr, _ = orq.preparar_pgr_hidratado(
        Path("qualquer.pdf"),
        carregar(Path(__file__).parent.parent / "protocolo"),
        TranscritorGHEOffline(),
        TranscritorCardOffline(),
        EnvelopeConfirmado(validade=date(2030, 1, 1), assinatura_engenheiro=True),
    )
    assert pgr is not None
    assert chamadas == [Path("qualquer.pdf")]
