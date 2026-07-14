from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import (
    Confianca,
    construir_indice_termos,
    resolver_termo,
)

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def indice_real() -> dict[str, str]:
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(p.vocabulario.agentes)


# ---------------------------------------------------------------------------
# construir_indice_termos — vocabulário real
# ---------------------------------------------------------------------------

def test_indice_real_tem_57_entradas(indice_real: dict[str, str]) -> None:
    assert len(indice_real) == 57


# ---------------------------------------------------------------------------
# resolver_termo — exatos reais (003.BO)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "termo,slug_esperado",
    [
        ("Ruído", "ruido"),
        ("Etanol", "etanol"),
        ("Acetato de Etila", "acetato_de_etila"),
        ("Tolueno", "tolueno"),
    ],
)
def test_exatos_reais_003bo(indice_real: dict[str, str], termo: str, slug_esperado: str) -> None:
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == slug_esperado
    assert resolucao.pendencia is None


def test_esforco_fisico_typo_acento_morre_na_normalizacao(indice_real: dict[str, str]) -> None:
    resolucao = resolver_termo("esforço fisico", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "esforco_fisico"
    assert resolucao.pendencia is None


def test_microrganismo_singular_resolve_fuzzy(indice_real: dict[str, str]) -> None:
    resolucao = resolver_termo("Microrganismo", indice_real)
    assert resolucao.confianca == Confianca.FUZZY
    assert resolucao.slug == "microrganismos"
    assert resolucao.pendencia is None


def test_thinner_nao_resolvido_produto_nao_e_agente(indice_real: dict[str, str]) -> None:
    resolucao = resolver_termo("Thinner", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"
    assert resolucao.pendencia.bloqueante is False


def test_eaquipamento_desprotegido_dist_maior_que_2(indice_real: dict[str, str]) -> None:
    resolucao = resolver_termo("Eaquipamento desprotegido", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


# ---------------------------------------------------------------------------
# resolver_termo — sintéticos (empate fuzzy, aliases)
# ---------------------------------------------------------------------------

def test_empate_fuzzy_entre_dois_slugs_nao_resolve() -> None:
    # "cat" está a dist 1 de "bat" e "cot" — dois slugs distintos na mesma dist mínima.
    vocab_sintetico: dict[str, dict[str, object]] = {"bat": {}, "cot": {}}
    indice = construir_indice_termos(vocab_sintetico)
    resolucao = resolver_termo("cat", indice)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


def test_alias_via_campo_termos_resolve_exata() -> None:
    vocab_sintetico = {"acetona": {"termos": ["propanona"]}}
    indice = construir_indice_termos(vocab_sintetico)
    resolucao = resolver_termo("Propanona", indice)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "acetona"
    assert resolucao.pendencia is None


def test_alias_colidindo_com_outro_slug_levanta_value_error() -> None:
    vocab_sintetico = {
        "acetona": {"termos": ["propanona"]},
        "propanona": {},
    }
    with pytest.raises(ValueError, match="Colisão"):
        construir_indice_termos(vocab_sintetico)
