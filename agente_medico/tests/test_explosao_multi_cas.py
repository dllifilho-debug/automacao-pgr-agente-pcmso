"""Testes da explosão de bloco "Derivados de:" multi-CAS no resolvedor (D-ARQ-45).

Cada teste falha sem _explodir_multi_cas e passa com ela (cobertura por regra, metodologia).
Fixtures cruas e sintéticas — não tocam fds_t65 (patologia distinta: cas="" é ramo d, não P1).
"""
from __future__ import annotations

import dataclasses

from agente_medico.motor.composicao import _explodir_multi_cas, resolver_composicao
from agente_medico.motor.resolvedor import EntradaIndice, construir_indice_cas
from agente_medico.motor.tipos import (
    Componente,
    FaixaConcentracao,
    FDS,
    GHEPGR,
    PGR,
    ProdutoQuimico,
)
from datetime import date


# --- _explodir_multi_cas isolado ---

def test_explode_bloco_dois_cas_um_por_cas() -> None:
    bloco = Componente(
        cas="2634-33-5\n55965-84-9",
        nome="Derivados de isotiazolinona",
        concentracao=FaixaConcentracao(minimo=0.05, maximo=0.2),
    )
    out = _explodir_multi_cas(bloco)
    assert [c.cas for c in out] == ["2634-33-5", "55965-84-9"]


def test_explode_herda_faixa_inteira_em_cada_sub() -> None:
    faixa = FaixaConcentracao(minimo=0.05, maximo=0.2)
    bloco = Componente(cas="2634-33-5\n55965-84-9", nome="Derivados", concentracao=faixa)
    out = _explodir_multi_cas(bloco)
    assert all(c.concentracao == faixa for c in out)
    assert len(out) == 2


def test_explode_herda_nome_e_flags() -> None:
    bloco = Componente(
        cas="71-43-2\n67-64-1",
        nome="Bloco X",
        is_carcinogeno_iarc=True,
        is_sensibilizante=True,
    )
    out = _explodir_multi_cas(bloco)
    assert all(c.nome == "Bloco X" for c in out)
    assert all(c.is_carcinogeno_iarc and c.is_sensibilizante for c in out)


def test_explode_tres_cas() -> None:
    bloco = Componente(cas="71-43-2\n67-64-1\n78-93-3", nome="Tri")
    out = _explodir_multi_cas(bloco)
    assert len(out) == 3
    assert [c.cas for c in out] == ["71-43-2", "67-64-1", "78-93-3"]


def test_single_cas_e_no_op_preserva_identidade() -> None:
    comp = Componente(cas="67-64-1", nome="Acetona")
    out = _explodir_multi_cas(comp)
    assert out == [comp]
    assert out[0] is comp


def test_cas_vazio_nao_some_preserva_componente() -> None:
    comp = Componente(cas="", nome="Segredo Industrial")
    out = _explodir_multi_cas(comp)
    assert out == [comp]
    assert out[0] is comp


def test_cas_so_espaco_e_no_op() -> None:
    comp = Componente(cas="   ", nome="Branco")
    out = _explodir_multi_cas(comp)
    assert out == [comp]
    assert out[0] is comp


def test_pedacos_strip_espacos_internos() -> None:
    bloco = Componente(cas=" 71-43-2 \n 67-64-1 ", nome="Com espaços")
    out = _explodir_multi_cas(bloco)
    assert [c.cas for c in out] == ["71-43-2", "67-64-1"]


# --- explosão dentro de resolver_composicao (integração) ---

def _pgr_com_bloco(componente: Componente) -> PGR:
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
                    ProdutoQuimico(nome="Tinta", fds=FDS(composicao=(componente,))),
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
    bloco = Componente(
        cas="71-43-2\n67-64-1",
        nome="Derivados",
        concentracao=FaixaConcentracao(minimo=0.05, maximo=0.2),
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
    bloco = Componente(
        cas="71-43-2\n67-64-1",
        nome="Derivados invertidos",
        concentracao=FaixaConcentracao(minimo=0.2, maximo=0.05),
    )
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(bloco), indice)
    comps = pgr_out.ghes[0].produtos_quimicos[0].fds.composicao
    assert len(comps) == 2
    assert all(c.concentracao == FaixaConcentracao(minimo=0.05, maximo=0.2) for c in comps)


def test_resolver_single_cas_inalterado() -> None:
    indice = construir_indice_cas({"acetona": {"cas": "67-64-1"}})
    comp = Componente(cas="67-64-1", nome="Acetona")
    pgr_out, _pend = resolver_composicao(_pgr_com_bloco(comp), indice)
    comps = pgr_out.ghes[0].produtos_quimicos[0].fds.composicao
    assert len(comps) == 1
    assert comps[0].agente == "acetona"
