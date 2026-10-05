from __future__ import annotations

from collections.abc import Sequence
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from agente_medico.adaptadores import orquestracao_pgr
from agente_medico.adaptadores.orquestracao_pgr import preparar_ghes, processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.io_pdf import ler_pdf
from agente_medico.motor.parser_familia_grid_aiha import GrupoFuncaoNaoReconhecido
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import EnvelopeConfirmado, GHEVerbatim, RiscoVerbatim
from agente_medico.motor.transcritor_grid import EntradaGrid
from agente_medico.superficie.web_matriz import _TranscritorContado, _TranscritorGridContado

# D-ARQ-57 peça 5, fatia G3: rota grid ligada em preparar_ghes. PDF real: o
# adendo da Ricco (20 págs., 8 grupos), o mais barato dos três do template
# set-2026.
_RAIZ = Path(__file__).parent.parent.parent
_PDF_ADENDO = _RAIZ / "matrizes_originais" / "ADENDO - FUNÇÕES FALTANTES - PGR RICCO.pdf"
_PROTO = carregar(_RAIZ / "agente_medico" / "protocolo")
_ENVELOPE = EnvelopeConfirmado(validade=date.today(), assinatura_engenheiro=True)

requer_adendo = pytest.mark.skipif(not _PDF_ADENDO.exists(), reason="PDF do adendo Ricco ausente")


class _NuncaChamado:
    def transcrever(self, *args: object) -> GHEVerbatim:
        raise AssertionError("cliente de outra rota invocado na rota grid")


class _GridEco:
    """Um GHE por grupo, com o nome verbatim e um risco de ruído."""

    def __init__(self) -> None:
        self.recebido: list[EntradaGrid] = []

    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]:
        self.recebido.extend(entradas)
        return tuple(
            GHEVerbatim(
                nome=e.nome_verbatim,
                cargos=(e.nome_verbatim,),
                riscos=(RiscoVerbatim("RUÍDO CONTÍNUO OU INTERMITENTE", "", ""),),
            )
            for e in entradas
        )


class _GridIndisponivel:
    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]:
        raise TranscricaoIndisponivel("cota diária esgotada")


@pytest.fixture(scope="module")
def leitura_adendo() -> object:
    return ler_pdf(_PDF_ADENDO)


@requer_adendo
def test_adendo_com_cliente_grid_vira_oito_ghes(leitura_adendo: object) -> None:
    # Reversão que mata: tirar o desvio para _preparar_grid em preparar_ghes
    # — o adendo volta a sair só com pgr_cargo_based.
    cliente = _GridEco()
    aprovados, pendencias = preparar_ghes(
        _PDF_ADENDO, _NuncaChamado(), _NuncaChamado(), leitura_adendo, cliente  # type: ignore[arg-type]
    )
    assert len(aprovados) == 8
    assert aprovados[0].nome == "ENCARREGADO DE ELETRICISTA"
    assert pendencias == ()
    assert len(cliente.recebido) == 8


@requer_adendo
def test_adendo_sem_cliente_grid_segue_bloqueado(leitura_adendo: object) -> None:
    # Reversão que mata: desviar para a rota grid sem checar
    # `cliente_grid is not None` (quebra com None em vez de bloquear).
    aprovados, pendencias = preparar_ghes(
        _PDF_ADENDO, _NuncaChamado(), _NuncaChamado(), leitura_adendo  # type: ignore[arg-type]
    )
    assert aprovados == ()
    assert [(p.tipo, p.bloqueante) for p in pendencias] == [("pgr_cargo_based", True)]


@requer_adendo
def test_transcricao_indisponivel_na_rota_grid_vira_pendencia_bloqueante(leitura_adendo: object) -> None:
    # Reversão que mata: não capturar TranscricaoIndisponivel em
    # _preparar_grid — a exceção sobe até a tela.
    aprovados, pendencias = preparar_ghes(
        _PDF_ADENDO, _NuncaChamado(), _NuncaChamado(), leitura_adendo, _GridIndisponivel()  # type: ignore[arg-type]
    )
    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_pgr"
    assert pendencias[0].bloqueante
    assert pendencias[0].motivo.startswith("[rota grid]")
    assert pendencias[0].regra_origem == "D-ARQ-57"


@requer_adendo
def test_grid_que_nao_segmenta_mantem_o_bloqueio_e_diz_por_que(leitura_adendo: object) -> None:
    # Reversão que mata: não capturar GrupoFuncaoNaoReconhecido em
    # _preparar_grid.
    def _falha(_: object) -> object:
        raise GrupoFuncaoNaoReconhecido("página com cabeçalho e sem nome de função")

    with patch.object(orquestracao_pgr, "segmentar_documento", _falha):
        aprovados, pendencias = preparar_ghes(
            _PDF_ADENDO, _NuncaChamado(), _NuncaChamado(), leitura_adendo, _GridEco()  # type: ignore[arg-type]
        )
    assert aprovados == ()
    assert [(p.tipo, p.bloqueante) for p in pendencias] == [
        ("pgr_cargo_based", True),
        ("familia_nao_medida", False),
    ]
    assert pendencias[1].motivo.startswith("[rota grid]")


@requer_adendo
def test_processar_arquivo_pgr_leva_o_cliente_grid_ate_a_matriz() -> None:
    # Reversão que mata: preparar_pgr_hidratado não repassar cliente_grid a
    # preparar_ghes (o parâmetro opcional some no caminho e o resultado é None).
    resultado, _ = processar_arquivo_pgr(
        _PDF_ADENDO,
        _PROTO,
        _NuncaChamado(),
        _NuncaChamado(),
        _ENVELOPE,
        cliente_grid=_GridEco(),
    )
    assert resultado is not None
    assert len(resultado.matrizes) == 8


def test_tela_conta_os_grupos_do_grid_como_blocos_lidos_por_ia() -> None:
    # Reversão que mata: _TranscritorGridContado delegar sem somar
    # len(entradas) no contador da rota GHE — a tela diria "0 bloco(s)".
    contador = _TranscritorContado(interno=_NuncaChamado())
    grid = _TranscritorGridContado(interno=_GridEco(), contador=contador)
    grid.transcrever_lote([EntradaGrid("PINTOR", "UMIDADE"), EntradaGrid("SERVENTE", "RUÍDO")])
    assert contador.chamadas == 2
