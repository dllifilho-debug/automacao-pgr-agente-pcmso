from __future__ import annotations

from datetime import date, timedelta

from agente_medico.motor.estagios.gates import PRAZO_VALIDADE_PGR, stage_1_gates
from agente_medico.motor.tipos import PGR


def _pgr(validade: date, assinatura: bool = True) -> PGR:
    return PGR(validade=validade, assinatura_engenheiro=assinatura, ghes=())


HOJE = date(2026, 5, 17)


def test_pgr_valido_retorna_lista_vazia() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=364))
    assert stage_1_gates(pgr, hoje=HOJE) == []


def test_pgr_sem_assinatura_engenheiro_gera_R_PGR_01() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=100), assinatura=False)
    result = stage_1_gates(pgr, hoje=HOJE)
    assert len(result) == 1
    p = result[0]
    assert p.tipo == "assinatura_invalida"
    assert p.regra_origem == "R-PGR-01"
    assert p.bloqueante is True


def test_pgr_vencido_2_anos_exatos_gera_R_PGR_06() -> None:
    # boundary: exatamente 730 dias → deve gerar pendência
    pgr = _pgr(validade=HOJE - timedelta(days=730))
    result = stage_1_gates(pgr, hoje=HOJE)
    assert len(result) == 1
    assert result[0].tipo == "pgr_vencido"
    assert result[0].regra_origem == "R-PGR-06"


def test_pgr_vencido_2_anos_e_1_dia_gera_R_PGR_06() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=731))
    result = stage_1_gates(pgr, hoje=HOJE)
    assert any(p.tipo == "pgr_vencido" for p in result)


def test_pgr_quase_vencido_1_ano_11_meses_aceita() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=729))
    assert stage_1_gates(pgr, hoje=HOJE) == []


def test_pgr_sem_assinatura_e_vencido_gera_ambas_pendencias() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=800), assinatura=False)
    result = stage_1_gates(pgr, hoje=HOJE)
    tipos = {p.tipo for p in result}
    assert "assinatura_invalida" in tipos
    assert "pgr_vencido" in tipos
    assert len(result) == 2


def test_pendencia_gate_tem_ghe_id_None() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=800), assinatura=False)
    for p in stage_1_gates(pgr, hoje=HOJE):
        assert p.ghe_id is None


def test_pendencia_gate_tem_bloqueante_True() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=800), assinatura=False)
    for p in stage_1_gates(pgr, hoje=HOJE):
        assert p.bloqueante is True


def test_hoje_injetavel() -> None:
    data_customizada = date(2025, 1, 1)
    pgr = _pgr(validade=date(2022, 12, 31))  # > 730 dias antes de 2025-01-01
    result = stage_1_gates(pgr, hoje=data_customizada)
    assert any(p.tipo == "pgr_vencido" for p in result)
