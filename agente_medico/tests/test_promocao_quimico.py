from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    Componente,
    FaixaConcentracao,
    FDS,
    GHEContext,
    GHEPGR,
    Materialidade,
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


def test_componente_material_promovido_sem_pendencia(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Tolueno",
        concentracao=FaixaConcentracao(6.0, 10.0),
        agente="tolueno",
    )
    ghe = _ghe(produtos_quimicos=(_produto("Solvente A", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert len(riscos_quimicos) == 1
    risco = riscos_quimicos[0]
    assert risco.agente == "tolueno"
    assert risco.materialidade is Materialidade.MATERIAL

    pendencias_materialidade = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    assert pendencias_materialidade == []


def test_componente_nao_material_promovido_prova_nao_filtro(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="1330-20-7",
        nome="Xileno",
        concentracao=FaixaConcentracao(1.0, 4.0),
        agente="xileno",
    )
    ghe = _ghe(produtos_quimicos=(_produto("Solvente B", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert len(riscos_quimicos) == 1
    assert riscos_quimicos[0].materialidade is Materialidade.NAO_MATERIAL

    pendencias_materialidade = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    assert pendencias_materialidade == []


def test_componente_carcinogeno_abaixo_cutoff_bypass_material(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Componente Carcinogenico",
        concentracao=FaixaConcentracao(1.0, 2.0),
        agente="tolueno",
        is_carcinogeno_iarc=True,
    )
    ghe = _ghe(produtos_quimicos=(_produto("Solvente C", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert len(riscos_quimicos) == 1
    risco = riscos_quimicos[0]
    assert risco.materialidade is Materialidade.MATERIAL
    assert risco.is_carcinogeno_iarc is True


def test_componente_sem_slug_nao_promove_gera_pendencia_bloqueante(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="0000-00-0",
        nome="Componente Sem Slug",
        concentracao=FaixaConcentracao(10.0, 20.0),
        agente=None,
    )
    ghe = _ghe(produtos_quimicos=(_produto("Produto D", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert riscos_quimicos == []

    pendencias_materialidade = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    assert len(pendencias_materialidade) == 1
    pend = pendencias_materialidade[0]
    assert pend.bloqueante is True
    assert pend.regra_origem == "D-ARQ-35"
    assert "Componente Sem Slug" in pend.motivo


def test_componente_straddle_promovido_com_pendencia_bloqueante(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Componente Straddle",
        concentracao=FaixaConcentracao(2.0, 8.0),
        agente="tolueno",
    )
    ghe = _ghe(produtos_quimicos=(_produto("Produto E", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert len(riscos_quimicos) == 1
    assert riscos_quimicos[0].materialidade is Materialidade.AUSENTE

    pendencias_materialidade = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    assert len(pendencias_materialidade) == 1
    pend = pendencias_materialidade[0]
    assert pend.bloqueante is True
    assert pend.regra_origem == "D-ARQ-35"


def test_rehidratacao_por_slug_aplica_is_ototoxico_do_vocabulario(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Tolueno",
        concentracao=FaixaConcentracao(6.0, 10.0),
        agente="tolueno",
    )
    ghe = _ghe(produtos_quimicos=(_produto("Solvente F", componente),))
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    riscos_quimicos = [r for r in ctx.riscos if r.fonte == "quimico_composicao"]
    assert len(riscos_quimicos) == 1
    assert riscos_quimicos[0].is_ototoxico is True


def test_sem_dedup_risco_explicito_e_quimico_coexistem(proto):  # type: ignore[no-untyped-def]
    componente = Componente(
        cas="108-88-3",
        nome="Tolueno",
        concentracao=FaixaConcentracao(6.0, 10.0),
        agente="tolueno",
    )
    ghe = _ghe(
        riscos=(
            RiscoPGR(
                tipo="quimico",
                agente="tolueno",
                quantificacao=None,
                severidade=None,
            ),
        ),
        produtos_quimicos=(_produto("Solvente G", componente),),
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    toluenos = [r for r in ctx.riscos if r.agente == "tolueno"]
    assert len(toluenos) == 2
    fontes = {r.fonte for r in toluenos}
    assert fontes == {"explicito", "quimico_composicao"}
