from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import extrair_texto_pgr, recortar_topo
from agente_medico.motor.tipos import EnvelopeVerbatim, Pendencia
from agente_medico.motor.transcritor_topo import gate_forma_topo, transcrever_topo

CAMINHO_PGR = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")

# Harness de integração desta fatia (D-ARQ-53 P2/P3, molde requer_pdfs de
# test_transcritor_pgr.py) — ausência do PDF vira skip, não falha.
requer_pdfs = pytest.mark.skipif(
    not CAMINHO_PGR.exists(),
    reason="matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf ausente; harness integração 003.BW indisponível",
)

try:
    from agente_medico.tests.test_extracao_pgr import paginas  # noqa: F401
except ImportError:

    @pytest.fixture(scope="module")
    def paginas() -> list[str]:
        return extrair_texto_pgr(CAMINHO_PGR)


# Gabarito verbatim medido na sessão 003.BV (topo do PGR Viverde, D-ARQ-53 P4).
GABARITO_003BV = EnvelopeVerbatim(
    validade_textos=("FEVEREIRO 2023", "FEVEREIRO 2024", "FEVEREIRO 2025"),
    responsavel_tecnico="Elisângela Alves Faria",
    titulo_rt="Eng. Ambiental e de Segurança do Trabalho",
    registro_profissional="CREA – 1016192983D-GO",
)


class MockTranscritorTopo:
    """Mock injetável (LLM SEMPRE mockado em teste, nunca API real — molde
    MockTranscritorGHE). Captura o topo recebido em topos_recebidos.
    """

    def __init__(self, resultado: EnvelopeVerbatim) -> None:
        self._resultado = resultado
        self.topos_recebidos: list[str] = []

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        self.topos_recebidos.append(topo)
        return self._resultado


def _envelope(
    validade_textos: tuple[str, ...] = ("FEVEREIRO 2025",),
    responsavel_tecnico: str = "Fulano de Tal",
    titulo_rt: str = "Eng. de Segurança do Trabalho",
    registro_profissional: str = "CREA – 000000",
) -> EnvelopeVerbatim:
    return EnvelopeVerbatim(
        validade_textos=validade_textos,
        responsavel_tecnico=responsavel_tecnico,
        titulo_rt=titulo_rt,
        registro_profissional=registro_profissional,
    )


# ---------------------------------------------------------------------------
# Núcleo — rodam sempre, sem PDF.
# ---------------------------------------------------------------------------


def test_transcrever_topo_delega_ao_cliente_e_passa_topo_verbatim() -> None:
    topo = "GOIÂNIA, FEVEREIRO 2025\nlinha qualquer"
    mock = MockTranscritorTopo(resultado=GABARITO_003BV)
    resultado = transcrever_topo(topo, mock)
    assert resultado == GABARITO_003BV
    assert mock.topos_recebidos == [topo]


def test_gate_forma_topo_aprova_gabarito_003bv() -> None:
    aprovado, pendencias = gate_forma_topo(GABARITO_003BV)
    assert aprovado == GABARITO_003BV
    assert pendencias == ()


def test_gate_forma_topo_reprova_candidata_vazia() -> None:
    envelope = _envelope(validade_textos=("FEVEREIRO 2025", "  "))
    aprovado, pendencias = gate_forma_topo(envelope)
    assert aprovado is None
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert isinstance(pendencia, Pendencia)
    assert pendencia.tipo == "forma_verbatim_topo"
    assert pendencia.bloqueante is True
    assert pendencia.destinatario == "extracao"
    assert pendencia.regra_origem == "D-ARQ-53"


def test_gate_forma_topo_reprova_envelope_integralmente_vazio() -> None:
    envelope = EnvelopeVerbatim(
        validade_textos=(),
        responsavel_tecnico="",
        titulo_rt="",
        registro_profissional="",
    )
    aprovado, pendencias = gate_forma_topo(envelope)
    assert aprovado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_topo"


def test_gate_forma_topo_aprova_envelope_parcial_sem_registro_profissional() -> None:
    envelope = _envelope(registro_profissional="")
    aprovado, pendencias = gate_forma_topo(envelope)
    assert aprovado == envelope
    assert pendencias == ()


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs; espelha test_transcritor_pgr.py).
# ---------------------------------------------------------------------------


@requer_pdfs
def test_transcrever_topo_recebe_o_topo_inteiro_com_responsabilidade_tecnica(
    paginas: list[str],
) -> None:
    topo = recortar_topo(paginas)
    assert topo is not None
    mock = MockTranscritorTopo(resultado=GABARITO_003BV)
    transcrever_topo(topo, mock)
    assert len(mock.topos_recebidos) == 1
    # "RESPONSABILIDADE" isolado, não "...TÉCNICA": o PDF real traz o título
    # com typo de origem ("RESPONSABILIDADE TÉNICA", sem o "C") — verbatim
    # preserva o documento, inclusive seus erros (D-ARQ-53 P3).
    assert "RESPONSABILIDADE" in mock.topos_recebidos[0]
