# Periodicidades e bordas de faixa conferidas vs Quadro 1 Anexo III NR-07 (Portaria MTP 567/2022)
# [DERIVADO — 002.N]. Bordas: ate_10 ≤10; 10_50: >10 e ≤50; 50_100: >50 e ≤100; acima_100: >100.
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import pytest

from agente_medico.motor.estagios.consolidacao import stage_8_consolidacao
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


def test_rx_pnos_sem_medicao_roteia_60m() -> None:
    # q=None -> sem_medicao (faixa válida Quadro 2: adm+60M). NÃO bloqueia — mesmo
    # tratamento do ramo (b) da sílica (Quadro 1) desde 003.EH.
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
# 003.EH — R-RX-01 / NR-07 Anexo III Quadro 1, ramo "Empresas sem avaliações
# quantitativas" (Portaria MTP 567/2022): quantificacao=None é faixa válida
# (sem_medicao), não pendência — os dois ramos do Quadro 1 são exaustivos.
# Redireciona test_rx_silica_sem_quantificacao_gera_ausente_bloqueante (comportamento
# antigo: Ausente bloqueante). Antes: rx_list == [] e pendencia bloqueante com
# "laudo"/"avaliação" no motivo. Depois: emite rx_torax_oit 24M/12 e zero pendência.
# ---------------------------------------------------------------------------

def test_rx_silica_quantificacao_none_roteia_24m_apos12() -> None:
    ctx, proto = _ctx_com_agente("silica", None)
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 24
    assert rx.periodicidade_apos_15a == 12
    assert {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}.issubset(rx.momentos)
    assert any(m.regra_id == "R-RX-01-sem" for m in rx.motivos)


def test_rx_silica_quantificacao_none_sem_pendencia_ausente() -> None:
    ctx, proto = _ctx_com_agente("silica", None)
    stage_5_emissao(ctx, proto)
    pendencias_silica = [
        p
        for p in ctx.pendencias
        if p.tipo == "predicado_ausente" and "silica_asbesto" in p.motivo
    ]
    assert pendencias_silica == [], f"Não deveria haver pendência: {pendencias_silica}"


# ---------------------------------------------------------------------------
# Regressão — ramo (d): medição afirmada (valor) mas não roteável (pct_quartzo
# ausente) segue Ausente. D-ARQ-08/13 intactos: não escolher faixa inventa número.
# ---------------------------------------------------------------------------

def test_rx_silica_valor_sem_pct_quartzo_continua_ausente_bloqueante() -> None:
    q_incompleta = Quantificacao(
        valor=0.05,
        unidade="mg/m³",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        sem_avaliacao_quantitativa=False,
        pct_quartzo=None,
    )
    ctx, proto = _ctx_com_agente("silica", q_incompleta)
    exames = stage_5_emissao(ctx, proto)
    rx_list = [e for e in exames if e.exame == "rx_torax_oit"]
    assert rx_list == [], "Medição não roteável (sem pct_quartzo) não deve emitir rx_torax_oit"
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


# Regressão de bordas: Quadro 1 usa ≤ no limite superior de cada faixa (NR-07 / Portaria 567/2022)
# pct=50 pertence à faixa 10_50 (≤50); pct=100 pertence à faixa 50_100 (≤100). [DERIVADO — 002.N]

def test_borda_pct50_pertence_faixa_10_50() -> None:
    """CLSC=50% LEO → faixa 10_50 (60M/36M), não 50_100. Bordas ≤ confirmadas no Quadro 1."""
    ctx, proto = _ctx_com_agente("silica", _q(50.0))
    assert ctx.predicados.get("silica_asbesto_leo_10_50") is True
    assert ctx.predicados.get("silica_asbesto_leo_50_100") is not True
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60
    assert rx.periodicidade_apos_15a == 36


def test_borda_pct100_pertence_faixa_50_100() -> None:
    """CLSC=100% LEO → faixa 50_100 (36M/24M), não acima_100. Bordas ≤ confirmadas no Quadro 1."""
    ctx, proto = _ctx_com_agente("silica", _q(100.0))
    assert ctx.predicados.get("silica_asbesto_leo_50_100") is True
    assert ctx.predicados.get("silica_asbesto_leo_acima_100") is not True
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 36
    assert rx.periodicidade_apos_15a == 24


# ---------------------------------------------------------------------------
# Stage 8: conflito e merge com periodicidade_apos_15a
# ---------------------------------------------------------------------------

def _motivo(regra_id: str) -> Motivo:
    return Motivo(regra_id=regra_id, predicado="teste", risco_origem=None, detalhe=None)


def test_stage8_piso_apos15a_diferente() -> None:
    """D-ARQ-39: apos_15a divergente não é mais ConflitoProtocolo — resolve por piso."""
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
    result = stage_8_consolidacao(exames)
    assert len(result) == 1
    assert result[0].periodicidade_apos_15a == 6


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


# ---------------------------------------------------------------------------
# PNOS — Quadro 2 Anexo III NR-07 (Portaria 567/2022) [DERIVADO — 002.X/002.Y]
# ---------------------------------------------------------------------------

def _q_pnos_mgm3(valor: float) -> Quantificacao:
    """Quantificação em mg/m³ sem pct_LT — exercita conversão via resolve_leo (D-ARQ-29)."""
    return Quantificacao(
        valor=valor,
        unidade="mg/m³",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
    )


def test_rx_pnos_pct5_roteia_apenas_adm() -> None:
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q(5.0))
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 0
    assert rx.momentos == {Momento.ADM}


def test_rx_pnos_pct50_roteia_apenas_adm() -> None:
    # faixa 10_100: 50% cai em (10,100] -> só adm (NÃO 60M)
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q(50.0))
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 0
    assert rx.momentos == {Momento.ADM}


def test_rx_pnos_pct150_roteia_60m() -> None:
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q(150.0))
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60
    assert rx.periodicidade_apos_15a is None


def test_rx_pnos_mgm3_baixo_converte_e_nao_bloqueia() -> None:
    # 0.163 / 3.0 = 5.43% -> ate_10 -> só adm. D-ARQ-29: NÃO bloqueia por fracao ausente (vs sílica).
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q_pnos_mgm3(0.163))
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 0
    assert rx.momentos == {Momento.ADM}
    assert [p for p in ctx.pendencias if p.bloqueante] == []


def test_rx_pnos_mgm3_alto_roteia_60m() -> None:
    # 21.94 / 3.0 = 731% -> acima_100 -> 60M
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q_pnos_mgm3(21.94))
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60


_PREDICADOS_FAIXA_PNOS = ["pnos_leo_ate_10", "pnos_leo_10_100", "pnos_leo_acima_100"]


@pytest.mark.parametrize("pct", [0.0, _PCT_LEO_BAIXO, 50.0, _PCT_LEO_ALTO, 150.0])
def test_exclusividade_faixas_pnos(pct: float) -> None:
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q(pct))
    disparados = [p for p in _PREDICADOS_FAIXA_PNOS if ctx.predicados.get(p) is True]
    assert len(disparados) == 1, f"pct={pct}: esperava 1 faixa PNOS, got {disparados}"


def test_rx_pnos_deprecated_nao_emite_dupla() -> None:
    # R-RX-01-pnos DEPRECATED filtrado pelo carregador: garante que só 1 rx_torax_oit é emitido.
    ctx, proto = _ctx_com_agente("poeira_nao_classificada", _q(5.0))
    rx_list = [e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit"]
    assert len(rx_list) == 1, f"R-RX-01-pnos DEPRECATED não deve coexistir com a faixa: {rx_list}"
    assert rx_list[0].periodicidade_meses == 0
