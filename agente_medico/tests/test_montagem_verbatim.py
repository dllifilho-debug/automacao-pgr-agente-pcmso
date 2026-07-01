from __future__ import annotations

from agente_medico.motor.tipos import (
    BlocoComponente,
    BlocoVerbatim,
    Componente,
    FaixaConcentracao,
    MembroVerbatim,
)
from agente_medico.motor.transcricao_fds import _montar_membro, montar_bloco, montar_composicao
from agente_medico.tests.fixtures.fds_t65 import cimento_ciplan, tinta_acrilica
from agente_medico.tests.fixtures.fds_verbatim_leinertex import leinertex_derivados_verbatim
from agente_medico.tests.fixtures.fds_verbatim_t65 import (
    cimento_ciplan_verbatim,
    tinta_acrilica_verbatim,
)


# ---------------------------------------------------------------------------
# Gabarito por par PDF↔fds_t65 (D-ARQ-42 P4 / D-ARQ-46): compara campos-de-dado
# (cas exato + concentracao numérica); nome é texto-livre-de-LLM, não-==. Blocos
# de fds_verbatim_t65 são singletons (1 membro), então cada bloco monta 1 gabarito.
# ---------------------------------------------------------------------------

def _assert_campos_de_dado_singleton(
    montados: tuple[BlocoComponente, ...], gabarito: tuple[Componente, ...]
) -> None:
    assert len(montados) == len(gabarito)
    for bloco, g in zip(montados, gabarito):
        assert len(bloco.membros) == 1
        assert bloco.membros[0].cas == g.cas
        assert bloco.concentracao == g.concentracao


def test_montagem_tinta_reproduz_gabarito_campos_de_dado() -> None:
    montados = montar_composicao(tinta_acrilica_verbatim())
    assert len(montados) == 9
    assert all(len(b.membros) == 1 for b in montados)
    _assert_campos_de_dado_singleton(montados, tinta_acrilica())


def test_montagem_ciplan_reproduz_gabarito_campos_de_dado() -> None:
    montados = montar_composicao(cimento_ciplan_verbatim())
    assert len(montados) == 8
    assert all(len(b.membros) == 1 for b in montados)
    _assert_campos_de_dado_singleton(montados, cimento_ciplan())


def test_montar_composicao_preserva_cardinalidade_e_tipo() -> None:
    montados = montar_composicao(tinta_acrilica_verbatim())
    assert len(montados) == 9
    assert all(isinstance(b, BlocoComponente) for b in montados)


# ---------------------------------------------------------------------------
# _montar_membro / montar_bloco — P3/P4/P5 integradas (D-ARQ-46 Parte 4)
# ---------------------------------------------------------------------------

def test_montar_membro_junta_quebra_render_no_cas() -> None:
    # P3: TiO₂ com \n intra-token vira CAS contínuo (segue errado no doc → ramo c do gate
    # a jusante; juntar é forma, não validade).
    c = _montar_membro(MembroVerbatim(cas="134363-67-\n7", nome="TiO2"))
    assert c.cas == "134363-67-7"


def test_montar_membro_grafia_ausente_vira_cas_vazio() -> None:
    # P4: 'vários' (Ciplan) → '' → ramo (d) cas_ausente do gate, a jusante.
    c = _montar_membro(MembroVerbatim(cas="vários", nome="Sulfato de cálcio"))
    assert c.cas == ""


def test_montar_membro_nome_strip_preserva_quebra_interna() -> None:
    # nome = strip apenas (D-ARQ-46 P4): tira bordas, mantém \n interno; informativo, não-==.
    c = _montar_membro(MembroVerbatim(cas="ND", nome="  Derivados\nSemi-Acetais  "))
    assert c.nome == "Derivados\nSemi-Acetais"


def test_montar_membro_flags_e_agente_no_default() -> None:
    # Recorte A (D-ARQ-42 P3 / D-ARQ-46): montagem não popula slug nem flags de perigo.
    c = _montar_membro(MembroVerbatim(cas="67-64-1", nome="Acetona"))
    assert c.agente is None
    assert c.is_carcinogeno_iarc is False
    assert c.is_sensibilizante is False


def test_montar_bloco_faixa_en_dash() -> None:
    bc = montar_bloco(BlocoVerbatim(faixa="30 – 70", membros=(MembroVerbatim(cas="67-64-1", nome="Acetona"),)))
    assert bc.concentracao == FaixaConcentracao(minimo=30.0, maximo=70.0)


def test_montar_bloco_faixa_vazia_vira_none() -> None:
    # Limite D-ARQ-46: faixa ausente → '' → None → sentinela AUSENTE (D-ARQ-34 P1).
    bc = montar_bloco(BlocoVerbatim(faixa="", membros=(MembroVerbatim(cas="67-64-1", nome="X"),)))
    assert bc.concentracao is None


def test_montar_bloco_nao_ordena_faixa() -> None:
    # 003.AP: par invertido sai invertido; a ordenação (_normalizar_faixa) é do resolvedor.
    bc = montar_bloco(BlocoVerbatim(faixa="0,2 – 0,05", membros=(MembroVerbatim(cas="x", nome="y"),)))
    assert bc.concentracao == FaixaConcentracao(minimo=0.2, maximo=0.05)


# ---------------------------------------------------------------------------
# Fronteira: montagem de bloco preserva o grupo verbatim; expansão-de-grupo e
# herança-α da faixa ficam no resolvedor (D-ARQ-46 P4, refinado 003.AZ)
# ---------------------------------------------------------------------------

def test_montar_bloco_multi_cas_preserva_grupo_sem_explodir_nem_herdar() -> None:
    # D-ARQ-45: o bloco multi-CAS legítimo (N membros) é preservado como grupo pela
    # montagem; a expansão-de-grupo (1→N) e a herança-α da faixa são do resolvedor, a jusante.
    bloco = leinertex_derivados_verbatim()[0]
    bc = montar_bloco(bloco)
    assert len(bc.membros) == 2
    assert bc.membros[0].cas == "2634-33-5"
    assert bc.membros[1].cas == "55965-84-9"
    assert all(m.concentracao is None for m in bc.membros)  # herança-α pendente (resolver)
    assert bc.concentracao == FaixaConcentracao(minimo=0.2, maximo=0.05)  # faixa do bloco, 1×, não ordenada


def test_montar_bloco_multi_cas_preserva_grupo_de_tres_membros() -> None:
    bloco = leinertex_derivados_verbatim()[1]
    bc = montar_bloco(bloco)
    assert len(bc.membros) == 3
    assert bc.membros[0].cas == "330-54-1"
    assert bc.membros[1].cas == "10605-21-7"
    assert bc.membros[2].cas == "26530-20-2"
    assert all(m.concentracao is None for m in bc.membros)
    assert bc.concentracao == FaixaConcentracao(minimo=0.1, maximo=0.05)
