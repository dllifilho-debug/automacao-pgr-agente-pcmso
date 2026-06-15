from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    Componente,
    FaixaConcentracao,
    FDS,
    GHEContext,
    GHEPGR,
    Materialidade,
    Momento,
    ProdutoQuimico,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto():  # type: ignore[no-untyped-def]
    return carregar(_PROTOCOLO_DIR)


def _ghe(
    *,
    cargos: tuple[str, ...] = (),
    riscos: tuple[RiscoPGR, ...] = (),
    produtos_quimicos: tuple[ProdutoQuimico, ...] = (),
) -> GHEPGR:
    return GHEPGR(
        id="GHE-TEST",
        nome="Teste",
        cargos=cargos,
        riscos=riscos,
        epis=(),
        produtos_quimicos=produtos_quimicos,
        psicossocial=False,
    )


def _produto(nome: str, *componentes: Componente) -> ProdutoQuimico:
    return ProdutoQuimico(nome=nome, fds=FDS(composicao=componentes))


def test_benzeno_baixa_concentracao_dispara_pacote(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="71-43-2",
        nome="Benzeno",
        concentracao=FaixaConcentracao(1.0, 3.0),
        agente="benzeno",
        is_carcinogeno_iarc=False,
    )
    ghe = _ghe(produtos_quimicos=(_produto("Produto Benzeno", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [
        r for r in ctx.riscos
        if r.agente == "benzeno" and r.fonte == "quimico_composicao"
    ]
    assert len(riscos_quimicos) == 1
    assert riscos_quimicos[0].materialidade is Materialidade.NAO_MATERIAL

    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert "hemograma" in por_exame
    assert "reticulocitos" in por_exame
    assert "acido_transmuconico" in por_exame

    assert por_exame["hemograma"].periodicidade_meses == 6
    assert por_exame["hemograma"].momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}

    assert por_exame["reticulocitos"].periodicidade_meses == 6
    assert por_exame["reticulocitos"].momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}

    assert por_exame["acido_transmuconico"].periodicidade_meses == 6
    assert por_exame["acido_transmuconico"].momentos == {Momento.PER}


def test_benzeno_carcinogeno_bypass_material(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="71-43-2",
        nome="Benzeno",
        concentracao=FaixaConcentracao(1.0, 2.0),
        agente="benzeno",
        is_carcinogeno_iarc=True,
    )
    ghe = _ghe(produtos_quimicos=(_produto("Produto Benzeno", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [
        r for r in ctx.riscos
        if r.agente == "benzeno" and r.fonte == "quimico_composicao"
    ]
    assert len(riscos_quimicos) == 1
    assert riscos_quimicos[0].materialidade is Materialidade.MATERIAL

    pendencias_materialidade = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    assert pendencias_materialidade == []

    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert "hemograma" in por_exame
    assert "reticulocitos" in por_exame
    assert "acido_transmuconico" in por_exame


def test_benzeno_no_inventario_tambem_dispara(proto):  # type: ignore[no-untyped-def]
    ghe = _ghe(
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="benzeno",
                quantificacao=None,
                severidade=None,
            ),
        ),
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert "hemograma" in por_exame
    assert "reticulocitos" in por_exame
    assert "acido_transmuconico" in por_exame


def test_sem_benzeno_nao_emite_pacote(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Tolueno",
        concentracao=FaixaConcentracao(6.0, 10.0),
        agente="tolueno",
    )
    ghe = _ghe(produtos_quimicos=(_produto("Solvente Tolueno", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    emitidos = stage_5_emissao(ctx, proto)
    slugs = {e.exame for e in emitidos}

    assert "reticulocitos" not in slugs
    assert "acido_transmuconico" not in slugs
