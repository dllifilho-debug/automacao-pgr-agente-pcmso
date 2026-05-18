from __future__ import annotations

import pytest

from agente_medico.motor.estagios.consolidacao import ConflitoProtocolo, stage_8_consolidacao
from agente_medico.motor.tipos import ExameEmitido, Momento, Motivo


def _motivo(regra_id: str) -> Motivo:
    return Motivo(regra_id=regra_id, predicado="teste", risco_origem=None, detalhe=None)


def _exame(nome: str, periodicidade: int, momentos: set[Momento], regra_id: str = "R-A") -> ExameEmitido:
    return ExameEmitido(
        exame=nome,
        periodicidade_meses=periodicidade,
        momentos=set(momentos),
        motivos=[_motivo(regra_id)],
    )


def test_dedup_simples_mesma_periodicidade_mesmos_momentos() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("Hemograma", 12, {Momento.ADM}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert len(result[0].motivos) == 2
    assert result[0].motivos[0].regra_id == "R-A"
    assert result[0].motivos[1].regra_id == "R-B"


def test_dedup_merge_momentos() -> None:
    entrada = [
        _exame("Audiometria", 12, {Momento.ADM, Momento.PER}, "R-A"),
        _exame("Audiometria", 12, {Momento.MR}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].momentos == {Momento.ADM, Momento.PER, Momento.MR}


def test_dedup_case_insensitive() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("hemograma ", 12, {Momento.PER}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].exame == "Hemograma"


def test_conflito_periodicidade_levanta_excecao() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("Hemograma",  6, {Momento.PER}, "R-B"),
    ]
    with pytest.raises(ConflitoProtocolo) as exc_info:
        stage_8_consolidacao(entrada)
    msg = str(exc_info.value)
    assert "R-A" in msg
    assert "R-B" in msg
    assert "12" in msg
    assert "6" in msg


def test_exames_distintos_preservados() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}),
        _exame("Glicemia",  12, {Momento.ADM}),
        _exame("ECG",       12, {Momento.ADM}),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 3
    assert [e.exame for e in result] == ["Hemograma", "Glicemia", "ECG"]


def test_ordem_primeira_ocorrencia_preservada() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("Glicemia",  12, {Momento.ADM}, "R-A"),
        _exame("Hemograma", 12, {Momento.PER}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 2
    assert result[0].exame == "Hemograma"
    assert result[1].exame == "Glicemia"


def test_funcao_pura_nao_muta_entrada() -> None:
    e1 = _exame("Hemograma", 12, {Momento.ADM}, "R-A")
    e2 = _exame("Hemograma", 12, {Momento.PER}, "R-B")
    momentos_antes = set(e1.momentos)
    motivos_antes = list(e1.motivos)
    entrada = [e1, e2]

    stage_8_consolidacao(entrada)

    assert len(entrada) == 2
    assert entrada[0] is e1
    assert entrada[1] is e2
    assert e1.momentos == momentos_antes
    assert e1.motivos == motivos_antes
