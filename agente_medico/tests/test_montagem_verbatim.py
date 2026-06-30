from __future__ import annotations

from agente_medico.motor.tipos import Componente, ComponenteVerbatim, FaixaConcentracao
from agente_medico.motor.transcricao_fds import montar_componente, montar_composicao
from agente_medico.tests.fixtures.fds_t65 import cimento_ciplan, tinta_acrilica
from agente_medico.tests.fixtures.fds_verbatim_t65 import (
    cimento_ciplan_verbatim,
    tinta_acrilica_verbatim,
)


# ---------------------------------------------------------------------------
# Gabarito por par PDF↔fds_t65 (D-ARQ-42 P4 / D-ARQ-46): compara campos-de-dado
# (cas exato + concentracao numérica); nome é texto-livre-de-LLM, não-==.
# ---------------------------------------------------------------------------

def _assert_campos_de_dado(
    montados: tuple[Componente, ...], gabarito: tuple[Componente, ...]
) -> None:
    assert len(montados) == len(gabarito)
    for m, g in zip(montados, gabarito):
        assert m.cas == g.cas
        assert m.concentracao == g.concentracao


def test_montagem_tinta_reproduz_gabarito_campos_de_dado() -> None:
    montados = montar_composicao(tinta_acrilica_verbatim())
    _assert_campos_de_dado(montados, tinta_acrilica())


def test_montagem_ciplan_reproduz_gabarito_campos_de_dado() -> None:
    montados = montar_composicao(cimento_ciplan_verbatim())
    _assert_campos_de_dado(montados, cimento_ciplan())


def test_montar_composicao_preserva_cardinalidade_e_tipo() -> None:
    montados = montar_composicao(tinta_acrilica_verbatim())
    assert len(montados) == 9
    assert all(isinstance(c, Componente) for c in montados)


# ---------------------------------------------------------------------------
# montar_componente — P3/P4/P5 integradas (D-ARQ-46 Parte 4)
# ---------------------------------------------------------------------------

def test_montar_componente_junta_quebra_render_no_cas() -> None:
    # P3: TiO₂ com \n intra-token vira CAS contínuo (segue errado no doc → ramo c do gate
    # a jusante; juntar é forma, não validade).
    c = montar_componente(ComponenteVerbatim(cas="134363-67-\n7", nome="TiO2", faixa="1 - 15"))
    assert c.cas == "134363-67-7"


def test_montar_componente_grafia_ausente_vira_cas_vazio() -> None:
    # P4: 'vários' (Ciplan) → '' → ramo (d) cas_ausente do gate, a jusante.
    c = montar_componente(ComponenteVerbatim(cas="vários", nome="Sulfato de cálcio", faixa="2 - 10"))
    assert c.cas == ""


def test_montar_componente_faixa_en_dash() -> None:
    c = montar_componente(ComponenteVerbatim(cas="67-64-1", nome="Acetona", faixa="30 – 70"))
    assert c.concentracao == FaixaConcentracao(minimo=30.0, maximo=70.0)


def test_montar_componente_faixa_vazia_vira_none() -> None:
    # Limite D-ARQ-46: faixa ausente → '' → None → sentinela AUSENTE (D-ARQ-34 P1).
    c = montar_componente(ComponenteVerbatim(cas="67-64-1", nome="X", faixa=""))
    assert c.concentracao is None


def test_montar_componente_nome_strip_preserva_quebra_interna() -> None:
    # nome = strip apenas (D-ARQ-46 P4): tira bordas, mantém \n interno; informativo, não-==.
    c = montar_componente(
        ComponenteVerbatim(cas="ND", nome="  Derivados\nSemi-Acetais  ", faixa="0,1 – 0,4")
    )
    assert c.nome == "Derivados\nSemi-Acetais"


def test_montar_componente_flags_e_agente_no_default() -> None:
    # Recorte A (D-ARQ-42 P3 / D-ARQ-46): montagem não popula slug nem flags de perigo.
    c = montar_componente(ComponenteVerbatim(cas="67-64-1", nome="Acetona", faixa="30 – 70"))
    assert c.agente is None
    assert c.is_carcinogeno_iarc is False
    assert c.is_sensibilizante is False


# ---------------------------------------------------------------------------
# Fronteira: montagem é 1→1; explosão e ordenação ficam no resolvedor (D-ARQ-46 P4)
# ---------------------------------------------------------------------------

def test_montar_componente_nao_explode_multi_cas() -> None:
    # D-ARQ-45: o \n multi-CAS legítimo (ambos fragmentos bem-formados) é preservado pela
    # montagem; a explosão 1→N (_explodir_multi_cas) é do resolvedor, a jusante.
    c = montar_componente(
        ComponenteVerbatim(cas="2634-33-5\n55965-84-9", nome="Derivados", faixa="0,2 – 0,05")
    )
    assert c.cas == "2634-33-5\n55965-84-9"
    assert "\n" in c.cas


def test_montar_componente_nao_ordena_faixa() -> None:
    # 003.AP: par invertido sai invertido; a ordenação (_normalizar_faixa) é do resolvedor.
    c = montar_componente(ComponenteVerbatim(cas="x", nome="y", faixa="0,2 – 0,05"))
    assert c.concentracao == FaixaConcentracao(minimo=0.2, maximo=0.05)
