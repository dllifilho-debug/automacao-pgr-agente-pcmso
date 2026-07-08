from __future__ import annotations

from datetime import date
from pathlib import Path
from unittest.mock import patch

from agente_medico.adaptadores.orquestracao_pgr import processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)

_PDF_VIVERDE = Path(__file__).parent.parent.parent / "matrizes_originais" / "PGR VIVERDE V02 - 03.02.25.pdf"

_ALVO_EXTRACAO = "agente_medico.adaptadores.orquestracao_pgr.extrair_texto_pgr"

_GHE_VALIDO = GHEVerbatim(
    nome="Setor Teste",
    cargos=("pintor",),
    riscos=(RiscoVerbatim(agente="Ruido", quantificacao="82,2 dB(A)", fonte_geradora="Fonte X"),),
)
_GHE_INVALIDO = GHEVerbatim(nome="", cargos=(), riscos=())


def _paginas_com_bloco(nome_setor: str = "Setor Teste") -> list[str]:
    return [f"SETOR/FUNÇÃO {nome_setor}\nCargo A\nOutraLinha"]


class MockTranscritorConstante:
    """Devolve o MESMO GHEVerbatim canned para todo bloco recebido."""

    def __init__(self, resposta: GHEVerbatim) -> None:
        self._resposta = resposta
        self.blocos_recebidos: list[str] = []

    def transcrever(self, bloco: str) -> GHEVerbatim:
        self.blocos_recebidos.append(bloco)
        return self._resposta


class MockTranscritorSequencial:
    """Devolve um GHEVerbatim distinto por chamada, na ordem dada."""

    def __init__(self, respostas: tuple[GHEVerbatim, ...]) -> None:
        self._respostas = respostas
        self.blocos_recebidos: list[str] = []

    def transcrever(self, bloco: str) -> GHEVerbatim:
        resposta = self._respostas[len(self.blocos_recebidos)]
        self.blocos_recebidos.append(bloco)
        return resposta


class MockTranscritorIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel(self._motivo)


def test_e2e_arquivo_real_ate_resultado_com_transcritor_mockado() -> None:
    mock = MockTranscritorConstante(_GHE_VALIDO)
    resultado, pendencias = processar_arquivo_pgr(
        _PDF_VIVERDE, _PROTO, mock, validade=date.today(), assinatura_engenheiro=True
    )

    assert resultado is not None
    assert len(mock.blocos_recebidos) > 0
    assert resultado.matrizes[0].ghe_id == "GHE-01"


def test_blocos_ausentes_vira_none_e_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=["página sem âncora nenhuma"]):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            validade=date.today(),
            assinatura_engenheiro=True,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "blocos_ausentes"
    assert pendencias[0].bloqueante is True


def test_transcricao_indisponivel_vira_none_e_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorIndisponivel("CHAVE_API_GOOGLE ausente"),
            validade=date.today(),
            assinatura_engenheiro=True,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_pgr"
    assert pendencias[0].bloqueante is True
    assert "CHAVE_API_GOOGLE ausente" in pendencias[0].motivo


def test_aprovacao_parcial_processa_aprovados_e_carrega_pendencia_de_forma() -> None:
    paginas = [
        "SETOR/FUNÇÃO Setor Bom\nCargo A\n"
        "SETOR/FUNÇÃO Setor Ruim\nCargo B"
    ]
    mock = MockTranscritorSequencial((_GHE_VALIDO, _GHE_INVALIDO))
    with patch(_ALVO_EXTRACAO, return_value=paginas):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            mock,
            validade=date.today(),
            assinatura_engenheiro=True,
        )

    assert resultado is not None
    assert len(resultado.matrizes) == 1
    tipos_pendencia = [p.tipo for p in pendencias]
    assert "forma_verbatim_pgr" in tipos_pendencia
    pendencia_forma = next(p for p in pendencias if p.tipo == "forma_verbatim_pgr")
    assert pendencia_forma.bloqueante is True


def test_envelope_validade_atravessa_ate_o_gate_r_pgr_06() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            validade=date(2025, 1, 1),
            assinatura_engenheiro=True,
            hoje=date(2027, 1, 1),
        )

    assert resultado is not None
    assert resultado.status == "REJEITADO"
    assert any(p.regra_origem == "R-PGR-06" for p in resultado.pendencias_globais)
