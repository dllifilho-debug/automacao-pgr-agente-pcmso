from __future__ import annotations

from datetime import date

from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.tipos import PGR
from agente_medico.tests.fixtures.pgr_viverde import build_pgr_viverde


def test_build_pgr_viverde_retorna_pgr() -> None:
    pgr = build_pgr_viverde()
    assert isinstance(pgr, PGR)


def test_fixture_tem_32_ghes() -> None:
    pgr = build_pgr_viverde()
    assert len(pgr.ghes) == 32


def test_fixture_apenas_acab_09_tem_psicossocial() -> None:
    pgr = build_pgr_viverde()
    com_psicossocial = [g for g in pgr.ghes if g.psicossocial]
    assert len(com_psicossocial) == 1
    assert com_psicossocial[0].id == "Acab-09"


def test_fixture_ghe_fun_tem_riscos_vazios() -> None:
    pgr = build_pgr_viverde()
    ghe_fun = next(g for g in pgr.ghes if g.id == "GHE-FUN")
    assert ghe_fun.riscos == ()
    assert ghe_fun.cargos == (
        "operador_retroescavadeira",
        "operador_escavadeira",
        "motorista",
        "operador_perfuratriz",
    )


def test_stage_1_aceita_pgr_viverde_dentro_do_prazo() -> None:
    """PGR Viverde emitido em 2025-01-10. Em 2026-05-27 (~502 dias) → valido."""
    pgr = build_pgr_viverde()
    pendencias = stage_1_gates(pgr, hoje=date(2026, 5, 27))
    assert pendencias == []


def test_stage_1_rejeita_pgr_viverde_apos_730_dias() -> None:
    """Em 2027-01-10 (730 dias exatos da emissao) → R-PGR-06 dispara."""
    pgr = build_pgr_viverde()
    pendencias = stage_1_gates(pgr, hoje=date(2027, 1, 10))
    assert any(p.regra_origem == "R-PGR-06" for p in pendencias)
