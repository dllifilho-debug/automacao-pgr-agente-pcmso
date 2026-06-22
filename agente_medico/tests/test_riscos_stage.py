from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    GHEContext,
    GHEPGR,
    Quantificacao,
    RiscoPGR,
    TipoIBE,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto():  # type: ignore[no-untyped-def]
    return carregar(_PROTOCOLO_DIR)


def _ghe(
    *,
    cargos: tuple[str, ...] = (),
    riscos: tuple[RiscoPGR, ...] = (),
) -> GHEPGR:
    return GHEPGR(
        id="GHE-TEST",
        nome="Teste",
        cargos=cargos,
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def test_hidrata_risco_explicito_com_anexo_nr07(proto):  # type: ignore[no-untyped-def]
    quant = Quantificacao(
        valor=0.5,
        unidade="mg/m³",
        relacao_LT="<",
        pct_LT=50.0,
        apenas_qualitativa=False,
    )
    ghe = _ghe(
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="fumos_metalicos",
                quantificacao=quant,
                severidade=None,
            ),
        )
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert len(ctx.riscos) == 1
    risco = ctx.riscos[0]
    assert risco.agente == "fumos_metalicos"
    assert risco.fonte == "explicito"
    assert risco.quantificacao == quant
    assert risco.tipo_ibe is None  # vocabulário define null
    assert ctx.pendencias == []


def test_hidrata_risco_com_tipo_ibe_ee(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe(
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="acetona",
                quantificacao=None,
                severidade=None,
            ),
        )
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert len(ctx.riscos) == 1
    assert ctx.riscos[0].tipo_ibe == TipoIBE.EE


def test_risco_explicito_agente_ausente_gera_pendencia_nao_bloqueante(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe(
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="agente_desconhecido_xyz",
                quantificacao=None,
                severidade=None,
            ),
        )
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert len(ctx.riscos) == 1
    assert ctx.riscos[0].tipo_ibe is None
    assert ctx.riscos[0].fonte == "explicito"

    assert len(ctx.pendencias) == 1
    pend = ctx.pendencias[0]
    assert pend.bloqueante is False
    assert pend.tipo == "vocabulario_ausente"
    assert "agente_desconhecido_xyz" in pend.motivo


def test_expande_riscos_implicitos_de_cargo_soldador(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe(cargos=("soldador",))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert len(ctx.riscos) == 2
    agentes = {r.agente for r in ctx.riscos}
    assert agentes == {"fumos_metalicos", "radiacao_uv_ir"}
    for r in ctx.riscos:
        assert r.fonte == "implicito_cargo"
    assert ctx.pendencias == []


def test_dedup_explicito_vence_implicito(proto):  # type: ignore[no-untyped-def]
    quant = Quantificacao(
        valor=1.2,
        unidade="mg/m³",
        relacao_LT=">",
        pct_LT=120.0,
        apenas_qualitativa=False,
    )
    ghe = _ghe(
        cargos=("soldador",),
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="fumos_metalicos",
                quantificacao=quant,
                severidade="alto",
            ),
        ),
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert len(ctx.riscos) == 2

    fumos = next(r for r in ctx.riscos if r.agente == "fumos_metalicos")
    assert fumos.fonte == "explicito"
    assert fumos.quantificacao == quant
    assert fumos.detalhe is not None
    assert "também implícito pelo cargo soldador" in fumos.detalhe

    radiacao = next(r for r in ctx.riscos if r.agente == "radiacao_uv_ir")
    assert radiacao.fonte == "implicito_cargo"

    assert ctx.pendencias == []


def test_cargo_desconhecido_gera_pendencia(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe(cargos=("__NAO_EXISTE__",))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert ctx.riscos == []
    assert len(ctx.pendencias) == 1
    pend = ctx.pendencias[0]
    assert pend.regra_origem == "R-GHE-02"
    assert pend.bloqueante is False
    assert "__NAO_EXISTE__" in pend.motivo


def test_ghe_sem_cargos_nem_riscos_resulta_em_ctx_riscos_vazio(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe()
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    assert ctx.riscos == []
    assert ctx.pendencias == []
