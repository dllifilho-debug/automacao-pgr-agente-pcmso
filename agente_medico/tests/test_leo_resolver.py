"""Testes do LEO-resolver e classificador de cenário para sílica (B.1 D-ARQ-24).
[DERIVADO — 002.S]
"""
from __future__ import annotations

import pytest

from agente_medico.motor.leo_resolver import SILICA, classifica_cenario, resolve_leo
from agente_medico.motor.tipos import CenarioExposicao, CenarioNormativo, Fracao


# ---------------------------------------------------------------------------
# classifica_cenario
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "cnae, atividade, local, esperado",
    [
        ("07.10-3", None, None, CenarioNormativo.MINERACAO),
        ("0990-4/03", None, None, CenarioNormativo.MINERACAO),
        ("0500-3", None, None, CenarioNormativo.MINERACAO),
        ("0910-6/00", None, None, CenarioNormativo.GERAL),
        ("06.00-0", None, None, CenarioNormativo.GERAL),
        ("09", None, None, CenarioNormativo.GERAL),
    ],
)
def test_classifica_cenario_por_cnae(
    cnae: str, atividade: str | None, local: str | None, esperado: CenarioNormativo
) -> None:
    cenario = CenarioExposicao(cnae=cnae, atividade=atividade, local=local)
    resultado = classifica_cenario(cenario)
    assert resultado is esperado, f"cnae={cnae!r}: esperado {esperado}, obtido {resultado}"


def test_classifica_cenario_keyword_lavra() -> None:
    cenario = CenarioExposicao(cnae=None, atividade="lavra de minério", local=None)
    assert classifica_cenario(cenario) is CenarioNormativo.MINERACAO, (
        "keyword 'lavra' deve classificar como MINERACAO mesmo sem CNAE"
    )


def test_classifica_cenario_extracao_sozinha_nao_casa() -> None:
    cenario = CenarioExposicao(cnae=None, atividade="extração de petróleo", local=None)
    assert classifica_cenario(cenario) is CenarioNormativo.GERAL, (
        "'extração' sozinha não deve classificar como MINERACAO (universalidade)"
    )


def test_classifica_cenario_none() -> None:
    assert classifica_cenario(None) is CenarioNormativo.GERAL, (
        "cenario None deve retornar GERAL"
    )


# ---------------------------------------------------------------------------
# resolve_leo
# ---------------------------------------------------------------------------


def test_resolve_leo_silica_respiravel_mineracao() -> None:
    resultado = resolve_leo(SILICA, Fracao.RESPIRAVEL, CenarioNormativo.MINERACAO, None)
    assert resultado.leo == pytest.approx(0.05), (
        "sílica respirável em mineração: LEO deve ser 0,05 mg/m³ (NR-22 Anexo V)"
    )
    assert "105" in resultado.fonte_normativa and "261" in resultado.fonte_normativa, (
        "fonte deve referenciar Portaria MTE 105/2026, alt. 261/2026"
    )


def test_resolve_leo_silica_total_mineracao_indefinido() -> None:
    resultado = resolve_leo(SILICA, Fracao.TOTAL, CenarioNormativo.MINERACAO, None)
    assert resultado.leo is None, (
        "sílica total em mineração: LEO indefinido por desenho (B.1 só cobre respirável)"
    )
    assert resultado.fonte_normativa != "", "fonte_normativa não deve ser vazia"


def test_resolve_leo_silica_respiravel_geral_com_quartzo() -> None:
    resultado = resolve_leo(SILICA, Fracao.RESPIRAVEL, CenarioNormativo.GERAL, 10.0)
    assert resultado.leo == pytest.approx(8.0 / 12.0), (
        "sílica respirável geral: 8/(pct_quartzo+2) com pct_quartzo=10"
    )
    assert "Anexo 12" in resultado.fonte_normativa, "fonte deve referenciar Anexo 12"


def test_resolve_leo_silica_total_geral_com_quartzo() -> None:
    resultado = resolve_leo(SILICA, Fracao.TOTAL, CenarioNormativo.GERAL, 10.0)
    assert resultado.leo == pytest.approx(24.0 / 13.0), (
        "sílica total geral: 24/(pct_quartzo+3) com pct_quartzo=10"
    )
    assert "Anexo 12" in resultado.fonte_normativa, "fonte deve referenciar Anexo 12"


def test_resolve_leo_silica_respiravel_geral_sem_quartzo() -> None:
    resultado = resolve_leo(SILICA, Fracao.RESPIRAVEL, CenarioNormativo.GERAL, None)
    assert resultado.leo is None, (
        "sílica respirável geral sem %quartzo: Anexo 12 exige pct_quartzo, LEO deve ser None"
    )


def test_resolve_leo_agente_fora_da_tabela() -> None:
    resultado = resolve_leo("chumbo", Fracao.RESPIRAVEL, CenarioNormativo.GERAL, 10.0)
    assert resultado.leo is None, (
        "agente fora da tabela de precedência deve retornar LEO None"
    )
