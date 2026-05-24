from __future__ import annotations

from datetime import date

import pytest

from agente_medico.motor.estagios.pendencias_estruturais import stage_3_pendencias_estruturais
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, Vocabulario
from agente_medico.motor.tipos import (
    Componente,
    FDS,
    GHEContext,
    GHEPGR,
    PGR,
    Pendencia,
    ProdutoQuimico,
)


def _proto_vazio() -> Protocolo:
    return Protocolo(
        vocabulario=Vocabulario(agentes={}, cargos={}, exames={}, epis={}),
        predicados_compostos={},
        regras=[],
        regimes={},
    )


def _ghe(
    ghe_id: str = "GHE-01",
    produtos_quimicos: tuple[ProdutoQuimico, ...] = (),
    cargos: tuple[str, ...] = (),
) -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome="Teste",
        cargos=cargos,
        riscos=(),
        epis=(),
        produtos_quimicos=produtos_quimicos,
        psicossocial=False,
    )


def _comp(cas: str = "64-17-5", nome: str = "etanol") -> Componente:
    return Componente(cas=cas, nome=nome, concentracao=None)


def _ctx(ghe: GHEPGR) -> GHEContext:
    return GHEContext(pgr_ghe=ghe)


# ---------------------------------------------------------------------------
# Caso 1 — fds=None → 1 bloqueante
# ---------------------------------------------------------------------------


def test_fds_none_emite_pendencia_bloqueante() -> None:
    ghe = _ghe(produtos_quimicos=(ProdutoQuimico(nome="tolueno", fds=None),))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.bloqueante is True
    assert p.tipo == "composicao_ausente"
    assert p.regra_origem == "R-PGR-04"
    assert p.ghe_id == "GHE-01"


# ---------------------------------------------------------------------------
# Caso 2 — fds com composicao vazia → 1 bloqueante
# ---------------------------------------------------------------------------


def test_fds_composicao_vazia_emite_pendencia_bloqueante() -> None:
    produto = ProdutoQuimico(nome="solvente X", fds=FDS(composicao=()))
    ghe = _ghe(produtos_quimicos=(produto,))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.bloqueante is True
    assert p.tipo == "composicao_ausente"
    assert p.regra_origem == "R-PGR-04"


# ---------------------------------------------------------------------------
# Casos 3a / 3b — componente com cas vazio ou só espaços → bloqueante
# ---------------------------------------------------------------------------


def test_componente_cas_string_vazia_emite_bloqueante() -> None:
    produto = ProdutoQuimico(
        nome="produto Y",
        fds=FDS(composicao=(_comp(cas=""),)),
    )
    ghe = _ghe(produtos_quimicos=(produto,))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert len(ctx.pendencias) == 1
    assert ctx.pendencias[0].bloqueante is True
    assert ctx.pendencias[0].regra_origem == "R-PGR-04"


def test_componente_cas_apenas_espacos_emite_bloqueante() -> None:
    produto = ProdutoQuimico(
        nome="produto Z",
        fds=FDS(composicao=(_comp(cas="   "),)),
    )
    ghe = _ghe(produtos_quimicos=(produto,))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert len(ctx.pendencias) == 1
    assert ctx.pendencias[0].bloqueante is True


# ---------------------------------------------------------------------------
# Caso 4 — FDS completa → zero pendência
# ---------------------------------------------------------------------------


def test_fds_completa_zero_pendencias() -> None:
    produto = ProdutoQuimico(
        nome="etanol absoluto",
        fds=FDS(composicao=(_comp(cas="64-17-5", nome="etanol"),)),
    )
    ghe = _ghe(produtos_quimicos=(produto,))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Caso 5 — sem produtos químicos → zero pendência
# ---------------------------------------------------------------------------


def test_sem_produtos_quimicos_zero_pendencias() -> None:
    ghe = _ghe(produtos_quimicos=())
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Caso 6 — múltiplos produtos: um sem FDS + um completo → exatamente 1 bloqueante
# ---------------------------------------------------------------------------


def test_multiplos_produtos_um_sem_fds_um_completo() -> None:
    produto_sem_fds = ProdutoQuimico(nome="tolueno", fds=None)
    produto_ok = ProdutoQuimico(
        nome="etanol",
        fds=FDS(composicao=(_comp(cas="64-17-5", nome="etanol"),)),
    )
    ghe = _ghe(produtos_quimicos=(produto_sem_fds, produto_ok))
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    bloqueantes = [p for p in ctx.pendencias if p.bloqueante]
    assert len(bloqueantes) == 1
    assert bloqueantes[0].regra_origem == "R-PGR-04"


# ---------------------------------------------------------------------------
# Caso 7 — integração executar(): produto sem FDS → PRELIMINAR, linhas=[], pendência R-PGR-04
# ---------------------------------------------------------------------------


def test_integracao_executar_produto_sem_fds_preliminar() -> None:
    hoje = date(2026, 5, 24)
    validade_futura = date(2027, 12, 31)
    produto = ProdutoQuimico(nome="benzeno", fds=None)
    ghe = _ghe(ghe_id="GHE-02", produtos_quimicos=(produto,))
    pgr = PGR(
        validade=validade_futura,
        assinatura_engenheiro=True,
        ghes=(ghe,),
    )
    resultado = executar(pgr, _proto_vazio(), hoje=hoje)
    assert resultado.status == "PRELIMINAR"
    assert len(resultado.matrizes) == 1
    assert resultado.matrizes[0].linhas == []
    pendencias = resultado.matrizes[0].pendencias
    assert any(p.regra_origem == "R-PGR-04" and p.bloqueante for p in pendencias)


# ---------------------------------------------------------------------------
# Caso 8 — universalidade (D-ARQ-06): GHE de saúde com produto sem FDS → bloqueia igual
# ---------------------------------------------------------------------------


def test_universalidade_ghe_saude_produto_sem_fds_bloqueia() -> None:
    produto = ProdutoQuimico(nome="óxido de etileno", fds=None)
    ghe = _ghe(
        ghe_id="GHE-SAUDE",
        produtos_quimicos=(produto,),
        cargos=("enfermeiro",),
    )
    ctx = _ctx(ghe)
    stage_3_pendencias_estruturais(ctx, _proto_vazio())
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.bloqueante is True
    assert p.regra_origem == "R-PGR-04"
    assert p.tipo == "composicao_ausente"
