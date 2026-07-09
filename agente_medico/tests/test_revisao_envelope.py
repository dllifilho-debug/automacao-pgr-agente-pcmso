from __future__ import annotations

import json
from datetime import date

import pytest

from agente_medico.motor.resolvedor_topo import resolver_validade
from agente_medico.motor.revisao_envelope import (
    EnvelopeRevisadoInvalido,
    desserializar_confirmacao,
    serializar_envelope,
)
from agente_medico.motor.tipos import EnvelopeConfirmado, EnvelopeVerbatim

GABARITO_003BV = EnvelopeVerbatim(
    validade_textos=("FEVEREIRO 2023", "FEVEREIRO 2024", "FEVEREIRO 2025"),
    responsavel_tecnico="Elisângela Alves Faria",
    titulo_rt="Eng. Ambiental e de Segurança do Trabalho",
    registro_profissional="CREA – 1016192983D-GO",
)


def _preencher_assinatura(texto_ida: str, assinatura: bool = True) -> str:
    dados = json.loads(texto_ida)
    dados["confirmacao"]["assinatura_engenheiro"] = assinatura
    return json.dumps(dados, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_round_trip_sem_edicao_aceita_proposta_pre_preenchida() -> None:
    candidatas, proposta = resolver_validade(GABARITO_003BV)
    texto_ida = serializar_envelope(GABARITO_003BV, candidatas, proposta)
    texto_volta = _preencher_assinatura(texto_ida, assinatura=True)
    confirmado = desserializar_confirmacao(texto_volta)
    assert confirmado == EnvelopeConfirmado(validade=date(2025, 2, 1), assinatura_engenheiro=True)


def test_rt_edita_dia_exato() -> None:
    candidatas, proposta = resolver_validade(GABARITO_003BV)
    texto_ida = serializar_envelope(GABARITO_003BV, candidatas, proposta)
    dados = json.loads(texto_ida)
    dados["confirmacao"]["validade"] = "2025-02-03"
    dados["confirmacao"]["assinatura_engenheiro"] = True
    texto_volta = json.dumps(dados, ensure_ascii=False, indent=2)

    confirmado = desserializar_confirmacao(texto_volta)
    assert confirmado.validade == date(2025, 2, 3)


# ---------------------------------------------------------------------------
# Schema estrito — cada rejeição diz O QUE falhou (D-ARQ-22)
# ---------------------------------------------------------------------------


def _texto_valido() -> str:
    candidatas, proposta = resolver_validade(GABARITO_003BV)
    texto_ida = serializar_envelope(GABARITO_003BV, candidatas, proposta)
    return _preencher_assinatura(texto_ida, assinatura=True)


def test_rejeita_json_invalido() -> None:
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao("{isso nao e json")


def test_rejeita_campo_desconhecido_no_topo() -> None:
    dados = json.loads(_texto_valido())
    dados["extra"] = "x"
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_campo_desconhecido_em_candidata() -> None:
    dados = json.loads(_texto_valido())
    dados["candidatas"][0]["extra"] = "x"
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_campo_desconhecido_em_credencial() -> None:
    dados = json.loads(_texto_valido())
    dados["credencial"]["extra"] = "x"
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_campo_desconhecido_em_confirmacao() -> None:
    dados = json.loads(_texto_valido())
    dados["confirmacao"]["extra"] = "x"
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_versao_desconhecida() -> None:
    dados = json.loads(_texto_valido())
    dados["versao"] = 2
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_assinatura_null() -> None:
    dados = json.loads(_texto_valido())
    dados["confirmacao"]["assinatura_engenheiro"] = None
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_assinatura_ausente() -> None:
    dados = json.loads(_texto_valido())
    del dados["confirmacao"]["assinatura_engenheiro"]
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_validade_ausente() -> None:
    dados = json.loads(_texto_valido())
    del dados["confirmacao"]["validade"]
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


def test_rejeita_validade_malformada() -> None:
    dados = json.loads(_texto_valido())
    dados["confirmacao"]["validade"] = "FEVEREIRO 2025"
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(json.dumps(dados))


# ---------------------------------------------------------------------------
# Proposta None: RT tem que digitar — sem regressão do RT-supplied atual.
# ---------------------------------------------------------------------------


def test_proposta_none_serializa_validade_null() -> None:
    envelope = EnvelopeVerbatim(
        validade_textos=("PGR 2023",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    candidatas, proposta = resolver_validade(envelope)
    assert proposta is None
    texto_ida = serializar_envelope(envelope, candidatas, proposta)
    dados = json.loads(texto_ida)
    assert dados["confirmacao"]["validade"] is None


def test_proposta_none_sem_rt_preencher_validade_rejeita() -> None:
    envelope = EnvelopeVerbatim(
        validade_textos=("PGR 2023",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    candidatas, proposta = resolver_validade(envelope)
    texto_ida = serializar_envelope(envelope, candidatas, proposta)
    texto_volta = _preencher_assinatura(texto_ida, assinatura=True)
    with pytest.raises(EnvelopeRevisadoInvalido):
        desserializar_confirmacao(texto_volta)


# ---------------------------------------------------------------------------
# Candidata não-parseável aparece explícita (data: null), não omitida.
# ---------------------------------------------------------------------------


def test_candidata_nao_parseavel_aparece_com_data_null_no_json() -> None:
    envelope = EnvelopeVerbatim(
        validade_textos=("FEVEREIRO 2025", "PGR 2023"),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    candidatas, proposta = resolver_validade(envelope)
    texto_ida = serializar_envelope(envelope, candidatas, proposta)
    dados = json.loads(texto_ida)
    assert dados["candidatas"] == [
        {"texto": "FEVEREIRO 2025", "data": "2025-02-01"},
        {"texto": "PGR 2023", "data": None},
    ]
