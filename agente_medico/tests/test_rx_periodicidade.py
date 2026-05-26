# VALORES DE PERIODICIDADE A-CONFERIR vs Anexo III Portaria 567/2022
# (002.L-estudo, opção B). Ao conferir a norma, atualizar AQUI + regras.yaml juntos.
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from agente_medico.motor.estagios.consolidacao import ConflitoProtocolo, stage_8_consolidacao
from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.predicados import _PCT_LEO_ALTO, _PCT_LEO_BAIXO, _PCT_LEO_MEDIO
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import (
    Ausente,
    ExameEmitido,
    GHEContext,
    GHEPGR,
    Momento,
    Motivo,
    PGR,
    Quantificacao,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _q(pct_LT: float) -> Quantificacao:
    return Quantificacao(
        valor=pct_LT,
        unidade="%LT",
        relacao_LT=None,
        pct_LT=pct_LT,
        apenas_qualitativa=False,
    )


def _q_sem_medicao() -> Quantificacao:
    return Quantificacao(
        valor=None,
        unidade=None,
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        sem_avaliacao_quantitativa=True,
    )


def _ctx_com_agente(agente: str, quantificacao: Quantificacao | None = None) -> tuple[GHEContext, Protocolo]:
    proto = _proto()
    risco_pgr = RiscoPGR(tipo="quimico", agente=agente, quantificacao=quantificacao, severidade=None)
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste RX",
        cargos=(),
        riscos=(risco_pgr,),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return ctx, proto


# ---------------------------------------------------------------------------
# Roteamento das faixas
# ---------------------------------------------------------------------------

def test_rx_silica_sem_medicao_roteia_24m_apos12() -> None:
    ctx, proto = _ctx_com_agente("silica", _q_sem_medicao())
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 24
    assert rx.periodicidade_apos_15a == 12
    assert {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}.issubset(rx.momentos)
    assert ctx.pendencias == []


def test_rx_pnos_roteia_60m_sem_apos15a() -> None:
    ctx, proto = _ctx_com_agente("poeira_nao_classificada")
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60
    assert rx.periodicidade_apos_15a is None


def test_rx_silica_pct120_roteia_12m() -> None:
    ctx, proto = _ctx_com_agente("silica", _q(120.0))
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 12
    assert rx.periodicidade_apos_15a is None


def test_rx_silica_pct30_roteia_60m_apos36() -> None:
    ctx, proto = _ctx_com_agente("silica", _q(30.0))
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60
    assert rx.periodicidade_apos_15a == 36


def test_rx_silica_pct70_roteia_36m_apos24() -> None:
    ctx, proto = _ctx_com_agente("silica", _q(70.0))
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 36
    assert rx.periodicidade_apos_15a == 24


def test_rx_silica_pct5_roteia_apenas_adm() -> None:
    ctx, proto = _ctx_com_agente("silica", _q(5.0))
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 0
    assert rx.momentos == {Momento.ADM}
    assert rx.periodicidade_apos_15a is None


# ---------------------------------------------------------------------------
# Ausente bloqueante quando silica sem quantificacao
# ---------------------------------------------------------------------------

def test_rx_silica_sem_quantificacao_gera_ausente_bloqueante() -> None:
    ctx, proto = _ctx_com_agente("silica", None)
    exames = stage_5_emissao(ctx, proto)
    rx_list = [e for e in exames if e.exame == "rx_torax_oit"]
    assert rx_list == [], "Não deve emitir rx_torax_oit quando silica sem quantificacao"
    bloqueantes = [p for p in ctx.pendencias if p.bloqueante]
    assert bloqueantes, "Deve haver pendencia bloqueante"
    assert any("laudo" in p.motivo.lower() or "avaliação" in p.motivo.lower() for p in bloqueantes)


# ---------------------------------------------------------------------------
# Exclusividade: fronteiras {0, 10, 50, 100, 150}
# ---------------------------------------------------------------------------

_PREDICADOS_FAIXA = [
    "silica_asbesto_leo_ate_10",
    "silica_asbesto_leo_10_50",
    "silica_asbesto_leo_50_100",
    "silica_asbesto_leo_acima_100",
]


@pytest.mark.parametrize("pct", [0.0, _PCT_LEO_BAIXO, _PCT_LEO_MEDIO, _PCT_LEO_ALTO, 150.0])
def test_exclusividade_faixas(pct: float) -> None:
    ctx, proto = _ctx_com_agente("silica", _q(pct))
    disparados = [p for p in _PREDICADOS_FAIXA if ctx.predicados.get(p) is True]
    assert len(disparados) == 1, (
        f"pct={pct}: esperava exatamente 1 faixa, got {disparados}"
    )


# ---------------------------------------------------------------------------
# Stage 8: conflito e merge com periodicidade_apos_15a
# ---------------------------------------------------------------------------

def _motivo(regra_id: str) -> Motivo:
    return Motivo(regra_id=regra_id, predicado="teste", risco_origem=None, detalhe=None)


def test_stage8_conflito_apos15a_diferente() -> None:
    exames = [
        ExameEmitido(
            exame="rx_torax_oit",
            periodicidade_meses=24,
            momentos={Momento.ADM},
            motivos=[_motivo("R-RX-01-sem")],
            periodicidade_apos_15a=12,
        ),
        ExameEmitido(
            exame="rx_torax_oit",
            periodicidade_meses=24,
            momentos={Momento.PER},
            motivos=[_motivo("R-RX-OUTRO")],
            periodicidade_apos_15a=6,
        ),
    ]
    with pytest.raises(ConflitoProtocolo):
        stage_8_consolidacao(exames)


def test_stage8_merge_preserva_apos15a() -> None:
    exames = [
        ExameEmitido(
            exame="rx_torax_oit",
            periodicidade_meses=24,
            momentos={Momento.ADM},
            motivos=[_motivo("R-A")],
            periodicidade_apos_15a=12,
        ),
        ExameEmitido(
            exame="rx_torax_oit",
            periodicidade_meses=24,
            momentos={Momento.PER},
            motivos=[_motivo("R-B")],
            periodicidade_apos_15a=12,
        ),
    ]
    result = stage_8_consolidacao(exames)
    assert len(result) == 1
    assert result[0].periodicidade_apos_15a == 12
    assert result[0].momentos == {Momento.ADM, Momento.PER}


# ---------------------------------------------------------------------------
# Dado contraditório: pct_LT e sem_avaliacao_quantitativa ao mesmo tempo
# ---------------------------------------------------------------------------

def test_rx_silica_contradictorio_bloqueante_sem_emissao() -> None:
    q_contradictoria = Quantificacao(
        valor=70.0,
        unidade="%LT",
        relacao_LT=None,
        pct_LT=70.0,
        apenas_qualitativa=False,
        sem_avaliacao_quantitativa=True,
    )
    ctx, proto = _ctx_com_agente("silica", q_contradictoria)
    exames = stage_5_emissao(ctx, proto)
    rx_list = [e for e in exames if e.exame == "rx_torax_oit"]
    assert rx_list == [], "Estado contraditório não deve emitir rx_torax_oit"
    bloqueantes = [p for p in ctx.pendencias if p.bloqueante]
    assert bloqueantes, "Deve haver pendência bloqueante"
    assert any("contraditório" in p.motivo for p in bloqueantes), (
        "Motivo da pendência deve mencionar 'contraditório'"
    )
    for pred in _PREDICADOS_FAIXA + ["silica_asbesto_sem_medicao"]:
        assert ctx.predicados.get(pred) is not True, (
            f"Predicado {pred!r} não deve ser True em estado contraditório"
        )
