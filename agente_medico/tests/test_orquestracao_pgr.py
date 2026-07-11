from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

from agente_medico.adaptadores.orquestracao_pgr import preparar_envelope, processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.extracao_pgr import eh_cabecalho_ghe
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.motor.tipos import EnvelopeConfirmado, EnvelopeVerbatim, GHEVerbatim, RiscoVerbatim

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

_ENVELOPE_PADRAO = EnvelopeConfirmado(validade=date.today(), assinatura_engenheiro=True)


def _paginas_com_bloco(nome_setor: str = "Setor Teste") -> list[str]:
    return [f"GHE 1 - {nome_setor}\nCargo A\nOutraLinha"]


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


class MockTranscritorTopoConstante:
    """Devolve o MESMO EnvelopeVerbatim canned para todo topo recebido."""

    def __init__(self, resposta: EnvelopeVerbatim) -> None:
        self._resposta = resposta
        self.topos_recebidos: list[str] = []

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        self.topos_recebidos.append(topo)
        return self._resposta


class MockTranscritorTopoIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        raise TranscricaoIndisponivel(self._motivo)


def test_e2e_arquivo_real_ate_resultado_com_transcritor_mockado() -> None:
    mock = MockTranscritorConstante(_GHE_VALIDO)
    resultado, pendencias = processar_arquivo_pgr(
        _PDF_VIVERDE, _PROTO, mock, envelope=_ENVELOPE_PADRAO
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
            envelope=_ENVELOPE_PADRAO,
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
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_pgr"
    assert pendencias[0].bloqueante is True
    assert "CHAVE_API_GOOGLE ausente" in pendencias[0].motivo


def test_aprovacao_parcial_processa_aprovados_e_carrega_pendencia_de_forma() -> None:
    paginas = [
        "GHE 1 - Setor Bom\nCargo A\n"
        "GHE 2 - Setor Ruim\nCargo B"
    ]
    mock = MockTranscritorSequencial((_GHE_VALIDO, _GHE_INVALIDO))
    with patch(_ALVO_EXTRACAO, return_value=paginas):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            mock,
            envelope=_ENVELOPE_PADRAO,
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
            envelope=EnvelopeConfirmado(validade=date(2025, 1, 1), assinatura_engenheiro=True),
            hoje=date(2027, 1, 1),
        )

    assert resultado is not None
    assert resultado.status == "REJEITADO"
    assert any(p.regra_origem == "R-PGR-06" for p in resultado.pendencias_globais)


# ---------------------------------------------------------------------------
# preparar_envelope — ida completa do envelope (D-ARQ-53 fatia 4)
# ---------------------------------------------------------------------------


_ENVELOPE_VIVERDE_GABARITO = EnvelopeVerbatim(
    validade_textos=("GOIÂNIA, FEVEREIRO 2023",),
    responsavel_tecnico="Fulano",
    titulo_rt="Engenheiro de Segurança",
    registro_profissional="CREA-GO 123",
)


def test_preparar_envelope_pdf_real_viverde_gera_artefato_com_proposta_pre_preenchida() -> None:
    mock = MockTranscritorTopoConstante(_ENVELOPE_VIVERDE_GABARITO)
    artefato, pendencias = preparar_envelope(_PDF_VIVERDE, mock)

    assert artefato is not None
    assert pendencias == ()
    assert len(mock.topos_recebidos) == 1
    topo_recebido = mock.topos_recebidos[0]
    # Inverso determinístico de recortar_blocos_ghe: nenhuma linha do topo
    # recebido é (ou vem depois d)a âncora de bloco GHE.
    assert not any(eh_cabecalho_ghe(linha) for linha in topo_recebido.splitlines())

    dados = json.loads(artefato)
    assert dados["confirmacao"]["validade"] == "2023-02-01"


def test_preparar_envelope_sem_ancora_de_topo_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=["página sem âncora nenhuma"]):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(_ENVELOPE_VIVERDE_GABARITO)
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "topo_ausente"
    assert pendencias[0].bloqueante is True


def test_preparar_envelope_transcricao_indisponivel_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoIndisponivel("CHAVE_API_GOOGLE ausente")
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_topo"
    assert pendencias[0].bloqueante is True
    assert "CHAVE_API_GOOGLE ausente" in pendencias[0].motivo


def test_preparar_envelope_integralmente_vazio_vira_pendencia_de_forma() -> None:
    envelope_vazio = EnvelopeVerbatim(
        validade_textos=(), responsavel_tecnico="", titulo_rt="", registro_profissional=""
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_vazio)
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_topo"
    assert pendencias[0].bloqueante is True


# ---------------------------------------------------------------------------
# Ida-e-volta completa: preparar_envelope -> confirmação-RT simulada ->
# processar_arquivo_pgr. Caso concreto DT-003BV-01 / R-PGR-06 (003.BX).
# ---------------------------------------------------------------------------


def test_ida_e_volta_validade_antiga_gera_pendencia_r_pgr_06_bloqueante() -> None:
    envelope_bruto = EnvelopeVerbatim(
        validade_textos=("FEVEREIRO 2023",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, pend_envelope = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_bruto)
        )
        assert pend_envelope == ()
        assert artefato is not None

        dados = json.loads(artefato)
        assert dados["confirmacao"]["validade"] == "2023-02-01"
        dados["confirmacao"]["assinatura_engenheiro"] = True
        envelope_confirmado = desserializar_confirmacao(json.dumps(dados))

        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            envelope=envelope_confirmado,
            hoje=date(2026, 7, 8),
        )

    assert resultado is not None
    pendencias_r06 = [p for p in resultado.pendencias_globais if p.regra_origem == "R-PGR-06"]
    assert len(pendencias_r06) == 1
    assert pendencias_r06[0].bloqueante is True


def test_ida_e_volta_validade_recente_nao_gera_pendencia_r_pgr_06() -> None:
    envelope_bruto = EnvelopeVerbatim(
        validade_textos=("FEVEREIRO 2025",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, _ = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_bruto)
        )
        assert artefato is not None

        dados = json.loads(artefato)
        assert dados["confirmacao"]["validade"] == "2025-02-01"
        dados["confirmacao"]["assinatura_engenheiro"] = True
        envelope_confirmado = desserializar_confirmacao(json.dumps(dados))

        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            envelope=envelope_confirmado,
            hoje=date(2026, 7, 8),
        )

    assert resultado is not None
    assert not any(p.regra_origem == "R-PGR-06" for p in resultado.pendencias_globais)
