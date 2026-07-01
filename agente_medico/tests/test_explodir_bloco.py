"""Testes da expansão-de-grupo BlocoComponente -> tuple[Componente,...] (D-ARQ-45 P1/P2, 003.BA).

Cada teste falha sem _explodir_bloco e passa com ela (cobertura por regra, metodologia).
Nasceu isolada (fatia ii, sem gate/sem chamador); plugada em resolver_composicao na
fatia iii (003.BB) — cobertura aqui permanece válida e intacta.
"""
from __future__ import annotations

from agente_medico.motor.composicao import _explodir_bloco
from agente_medico.motor.tipos import BlocoComponente, Componente, FaixaConcentracao


def test_explode_dois_membros_heranca_faixa() -> None:
    faixa = FaixaConcentracao(minimo=1.0, maximo=5.0)
    bloco = BlocoComponente(
        concentracao=faixa,
        membros=(
            Componente(cas="2634-33-5", nome="A"),
            Componente(cas="55965-84-9", nome="B"),
        ),
    )
    out = _explodir_bloco(bloco)
    assert len(out) == 2
    assert all(c.concentracao == faixa for c in out)


def test_explode_tres_membros_preserva_cardinalidade() -> None:
    faixa = FaixaConcentracao(minimo=0.05, maximo=0.1)
    bloco = BlocoComponente(
        concentracao=faixa,
        membros=(
            Componente(cas="330-54-1", nome="A"),
            Componente(cas="10605-21-7", nome="B"),
            Componente(cas="26530-20-2", nome="C"),
        ),
    )
    out = _explodir_bloco(bloco)
    assert len(out) == 3


def test_explode_singleton_preserva_cardinalidade() -> None:
    faixa = FaixaConcentracao(minimo=1.0, maximo=15.0)
    bloco = BlocoComponente(concentracao=faixa, membros=(Componente(cas="67-64-1", nome="Acetona"),))
    out = _explodir_bloco(bloco)
    assert len(out) == 1


def test_explode_heranca_alfa_normaliza_faixa_invertida() -> None:
    bloco = BlocoComponente(
        concentracao=FaixaConcentracao(minimo=0.2, maximo=0.05),
        membros=(Componente(cas="x", nome="y"),),
    )
    out = _explodir_bloco(bloco)
    assert out[0].concentracao == FaixaConcentracao(minimo=0.05, maximo=0.2)


def test_explode_bloco_sem_faixa_membros_saem_sem_faixa() -> None:
    bloco = BlocoComponente(
        concentracao=None,
        membros=(
            Componente(cas="67-64-1", nome="A"),
            Componente(cas="78-93-3", nome="B"),
        ),
    )
    out = _explodir_bloco(bloco)
    assert all(c.concentracao is None for c in out)


def test_explode_preserva_cas_nome_e_flags_do_membro() -> None:
    faixa = FaixaConcentracao(minimo=0.0, maximo=1.0)
    membro = Componente(
        cas="67-64-1",
        nome="Acetona",
        is_carcinogeno_iarc=True,
        is_sensibilizante=True,
    )
    bloco = BlocoComponente(concentracao=faixa, membros=(membro,))
    out = _explodir_bloco(bloco)
    assert out[0].cas == "67-64-1"
    assert out[0].nome == "Acetona"
    assert out[0].is_carcinogeno_iarc is True
    assert out[0].is_sensibilizante is True
