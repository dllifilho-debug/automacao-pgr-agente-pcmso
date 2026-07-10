from __future__ import annotations

import pytest

from agente_medico.motor.classificacao_ruido import classificar_ruido
from agente_medico.motor.tipos import Quantificacao


def _q(
    *,
    valor: float | None,
    unidade: str | None = "dB(A)",
    relacao_LT: str | None = None,
    apenas_qualitativa: bool = False,
) -> Quantificacao:
    return Quantificacao(
        valor=valor,
        unidade=unidade,
        relacao_LT=relacao_LT,
        pct_LT=None,
        apenas_qualitativa=apenas_qualitativa,
    )


@pytest.mark.parametrize(
    "valor,esperado",
    [
        (79.0, "abaixo_acao"),
        (80.0, "entre_acao_LT"),
        (84.0, "entre_acao_LT"),
        (84.9, "entre_acao_LT"),
        (85.0, "acima_LT"),
        (90.0, "acima_LT"),
    ],
)
def test_classificar_ruido_por_faixa(valor: float, esperado: str) -> None:
    q = classificar_ruido(_q(valor=valor))
    assert q.relacao_LT == esperado


def test_classificar_ruido_nunca_emite_acima_acao() -> None:
    for valor in (79.0, 80.0, 85.0, 120.0):
        q = classificar_ruido(_q(valor=valor))
        assert q.relacao_LT != "acima_acao"


def test_nao_classifica_valor_none() -> None:
    q = _q(valor=None)
    assert classificar_ruido(q) == q


def test_nao_classifica_unidade_diferente_de_dba() -> None:
    q = _q(valor=90.0, unidade="mg/m3")
    assert classificar_ruido(q) == q


def test_nao_classifica_apenas_qualitativa() -> None:
    q = _q(valor=90.0, apenas_qualitativa=True)
    assert classificar_ruido(q) == q


def test_nao_sobrescreve_relacao_lt_ja_preenchida() -> None:
    q = _q(valor=90.0, relacao_LT="abaixo_acao")
    assert classificar_ruido(q) == q
