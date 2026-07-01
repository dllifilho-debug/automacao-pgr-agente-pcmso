"""Testes de integração: _explodir_bloco plugado em resolver_composicao (D-ARQ-45 P1/P2,
aplicação 003.BB). resolver_composicao consome fds.composicao_verbatim (BlocoComponente)
e escreve fds.composicao resolvida via _explodir_bloco + gate_cas.

_explodir_multi_cas foi aposentada nesta sessão; cobertura isolada da expansão-de-grupo
mora em test_explodir_bloco.py (fatia ii, 003.BA). Aqui só a integração com o resolver.
"""
from __future__ import annotations

from datetime import date

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import (
    BlocoComponente,
    Componente,
    FaixaConcentracao,
    FDS,
    GHEPGR,
    PGR,
    ProdutoQuimico,
)


def _pgr_com_bloco(bloco: BlocoComponente) -> PGR:
    return PGR(
        validade=date(2026, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="G1",
                nome="GHE 1",
                cargos=("c",),
                riscos=(),
                epis=(),
                produtos_quimicos=(
                    ProdutoQuimico(
                        nome="Tinta",
                        fds=FDS(composicao=(), composicao_verbatim=(bloco,)),
                    ),
                ),
                psicossocial=False,
            ),
        ),
    )


def test_resolver_explode_bloco_para_n_componentes() -> None:
    # 71-43-2 = benzeno (no vocabulário); 67-64-1 = acetona (no vocabulário).
    indice = construir_indice_cas(
        {
            "benzeno": {"cas": "71-43-2", "is_carcinogeno_iarc": True},
            "acetona": {"cas": "67-64-1"},
        }
    )
    bloco = BlocoComponente(
        concentracao=FaixaConcentracao(minimo=0.05, maximo=0.2),
        membros=(
            Componente(cas="71-43-2", nome="Derivados"),
            Componente(cas="67-64-1", nome="Derivados"),
        ),
    )
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(bloco), indice)
    comps = pgr_out.ghes[0].produtos_quimicos[0].fds.composicao
    assert len(comps) == 2
    assert {c.agente for c in comps} == {"benzeno", "acetona"}
    assert all(c.concentracao == FaixaConcentracao(minimo=0.05, maximo=0.2) for c in comps)


def test_resolver_explode_e_normaliza_faixa_invertida() -> None:
    # Herança-α primeiro, normalização P2 depois: faixa invertida do bloco
    # (0,2 - 0,05) é herdada por cada sub-CAS e então canonicalizada.
    indice = construir_indice_cas({"benzeno": {"cas": "71-43-2"}, "acetona": {"cas": "67-64-1"}})
    bloco = BlocoComponente(
        concentracao=FaixaConcentracao(minimo=0.2, maximo=0.05),
        membros=(
            Componente(cas="71-43-2", nome="Derivados invertidos"),
            Componente(cas="67-64-1", nome="Derivados invertidos"),
        ),
    )
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(bloco), indice)
    comps = pgr_out.ghes[0].produtos_quimicos[0].fds.composicao
    assert len(comps) == 2
    assert all(c.concentracao == FaixaConcentracao(minimo=0.05, maximo=0.2) for c in comps)


def test_resolver_single_cas_inalterado() -> None:
    indice = construir_indice_cas({"acetona": {"cas": "67-64-1"}})
    bloco = BlocoComponente(
        concentracao=None,
        membros=(Componente(cas="67-64-1", nome="Acetona"),),
    )
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(bloco), indice)
    comps = pgr_out.ghes[0].produtos_quimicos[0].fds.composicao
    assert len(comps) == 1
    assert comps[0].agente == "acetona"


def test_resolver_preserva_composicao_verbatim() -> None:
    # Decisão "manter" (D-ARQ-45 P2, aplicação 003.BB): resolver_composicao escreve
    # composicao resolvida SEM zerar/perder composicao_verbatim de entrada.
    indice = construir_indice_cas({"acetona": {"cas": "67-64-1"}})
    bloco = BlocoComponente(
        concentracao=FaixaConcentracao(minimo=1.0, maximo=5.0),
        membros=(Componente(cas="67-64-1", nome="Acetona"),),
    )
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(bloco), indice)
    fds = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert fds is not None
    assert len(fds.composicao) == 1
    assert fds.composicao_verbatim == (bloco,)
