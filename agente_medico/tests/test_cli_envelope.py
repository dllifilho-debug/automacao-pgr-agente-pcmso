from __future__ import annotations

import io
from datetime import date
from pathlib import Path

import pytest

from agente_medico.adaptadores.orquestracao_pgr import preparar_envelope
from agente_medico.motor.revisao_envelope import desserializar_confirmacao, serializar_envelope
from agente_medico.motor.tipos import CandidataValidade, EnvelopeVerbatim
from agente_medico.superficie.cli_envelope import ArtefatoIdaIlegivel, revisar_envelope

_PDF_VIVERDE = Path(__file__).parent.parent.parent / "matrizes_originais" / "PGR VIVERDE V02 - 03.02.25.pdf"

_ENVELOPE_VIVERDE_GABARITO = EnvelopeVerbatim(
    validade_textos=("GOIÂNIA, FEVEREIRO 2023",),
    responsavel_tecnico="Fulano",
    titulo_rt="Engenheiro de Segurança",
    registro_profissional="CREA-GO 123",
)


class MockTranscritorTopoConstante:
    """Devolve o MESMO EnvelopeVerbatim canned para todo topo recebido."""

    def __init__(self, resposta: EnvelopeVerbatim) -> None:
        self._resposta = resposta
        self.topos_recebidos: list[str] = []

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        self.topos_recebidos.append(topo)
        return self._resposta


_ENVELOPE_PADRAO = EnvelopeVerbatim(
    validade_textos=("FEVEREIRO 2025",),
    responsavel_tecnico="Fulano de Tal",
    titulo_rt="Engenheiro de Segurança",
    registro_profissional="CREA-GO 123",
)


def _ida_padrao() -> str:
    candidatas = (CandidataValidade(texto="FEVEREIRO 2025", data=date(2025, 2, 1)),)
    return serializar_envelope(_ENVELOPE_PADRAO, candidatas, proposta=date(2025, 2, 1))


def _ida_sem_proposta() -> str:
    candidatas = (CandidataValidade(texto="texto não-parseável qualquer", data=None),)
    return serializar_envelope(_ENVELOPE_PADRAO, candidatas, proposta=None)


def test_enter_e_s_aceita_proposta_e_assinatura_true() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2025, 2, 1)
    assert confirmado.assinatura_engenheiro is True


def test_data_iso_digitada_prevalece_sobre_proposta() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("2025-03-15\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2025, 3, 15)


def test_data_invalida_reprompta_ate_iso_valida() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("31/12/2026\n2026-12-31\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida, hoje=date(2027, 1, 1))
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2026, 12, 31)
    assert "Data inválida" in saida.getvalue()


def test_assinatura_n_vira_false() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\nn\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.assinatura_engenheiro is False


def test_assinatura_entrada_invalida_reprompta() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\nx\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.assinatura_engenheiro is True
    assert "Entrada inválida" in saida.getvalue()


def test_proposta_null_enter_reprompta_ate_iso_digitada() -> None:
    ida = _ida_sem_proposta()
    entrada = io.StringIO("\n2025-06-01\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(ida, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2025, 6, 1)
    assert "Nenhuma proposta disponível" in saida.getvalue()


def test_render_contem_credencial_crua_e_candidata_com_data_null() -> None:
    ida = _ida_sem_proposta()
    entrada = io.StringIO("2025-06-01\ns\n")
    saida = io.StringIO()

    revisar_envelope(ida, entrada, saida)
    render = saida.getvalue()

    assert "Fulano de Tal" in render
    assert "Engenheiro de Segurança" in render
    assert "CREA-GO 123" in render
    assert "texto não-parseável qualquer" in render
    assert "(não-parseável)" in render


def test_ida_ilegivel_levanta_erro() -> None:
    with pytest.raises(ArtefatoIdaIlegivel):
        revisar_envelope("não é json", io.StringIO(), io.StringIO())

    with pytest.raises(ArtefatoIdaIlegivel):
        revisar_envelope('{"candidatas": []}', io.StringIO(), io.StringIO())


def test_stdin_exaurido_levanta_eof_sem_travar() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("")
    saida = io.StringIO()

    with pytest.raises(EOFError):
        revisar_envelope(ida, entrada, saida)


def test_stdin_acaba_apos_validade_levanta_eof_na_assinatura() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("2027-01-01\n")
    saida = io.StringIO()

    with pytest.raises(EOFError):
        revisar_envelope(ida, entrada, saida)


def test_gabarito_viverde_fim_a_fim() -> None:
    mock = MockTranscritorTopoConstante(_ENVELOPE_VIVERDE_GABARITO)
    artefato, pendencias = preparar_envelope(_PDF_VIVERDE, mock)
    assert artefato is not None
    assert pendencias == ()

    entrada = io.StringIO("\ns\n")
    saida = io.StringIO()
    volta = revisar_envelope(artefato, entrada, saida)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2023, 2, 1)
    assert confirmado.assinatura_engenheiro is True


def test_emissao_futura_digitada_reprompta() -> None:
    # Reversão que mata: _prompt_validade voltar a só `date.fromisoformat` — o
    # vencimento digitado (2027-04-01) seria aceito e R-PGR-06 não dispararia.
    entrada = io.StringIO("2027-04-01\n2026-09-01\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(_ida_padrao(), entrada, saida, hoje=date(2026, 9, 25))

    assert desserializar_confirmacao(volta).validade == date(2026, 9, 1)
    assert "Data de emissão no futuro" in saida.getvalue()


def test_proposta_futura_aceita_com_enter_reprompta() -> None:
    # Reversão que mata: o Enter devolver a proposta sem passar por
    # validar_data_emissao — proposta futura (capa com data errada) passaria.
    entrada = io.StringIO("\n2025-01-10\ns\n")
    saida = io.StringIO()

    volta = revisar_envelope(_ida_padrao(), entrada, saida, hoje=date(2025, 1, 15))

    assert desserializar_confirmacao(volta).validade == date(2025, 1, 10)
    assert "Data de emissão no futuro: '2025-02-01'" in saida.getvalue()


def test_prompt_pede_a_data_de_emissao_do_pgr() -> None:
    # Reversão que mata: o prompt voltar a dizer "Validade" — foi o rótulo que
    # levou o vencimento a ser digitado no lugar da emissão (Aurora, 25/09/2026).
    saida = io.StringIO()

    revisar_envelope(_ida_padrao(), io.StringIO("\ns\n"), saida, hoje=date(2026, 9, 25))

    assert "Data de emissão do PGR [Enter mantém: 2025-02-01]" in saida.getvalue()
