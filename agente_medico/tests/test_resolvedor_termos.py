from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import (
    PISO_FUZZY,
    Confianca,
    _levenshtein,
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

def test_indice_real_tem_105_entradas(indice_real: dict[str, str]) -> None:
    assert len(indice_real) == 105


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
# resolver_termo — aliases Tier 1 reais (003.DM, D-ARQ-50 Parte 2)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "termo,slug_esperado",
    [
        ("1,1,1 Tricloroetano", "tricloroetano_111"),
        ("1,3 butadieno", "butadieno_13"),
        ("1,6 diisocianato de hexametileno (HDI)", "hdi"),
        ("2-butoxietanol", "butoxietanol_2"),
        ("2-metoxietanol", "metoxietanol_2"),
        ("2-metoxietilacetato", "metoxietilacetato_2"),
        ("2-propanol", "propanol_2"),
        ("Cromo hexavalente (compostos solúveis)", "cromo_hexavalente"),
        ("Indutores de Metahemoglobina", "indutores_metahemoglobina"),
        ("Mercúrio metálico", "mercurio"),
        ("Metiletilcetona (MEK)", "metil_etil_cetona"),
        ("Metilisobutilcetona (MIBK)", "mibk"),
        ("N,N Dimetilacetamida", "dimetilacetamida"),
        ("N,N Dimetilformamida", "dimetilformamida"),
        ("Sulfeto de carbono", "dissulfeto_de_carbono"),
        ("Xilenos", "xileno"),
        ("Inseticidas inibidores da Colinesterase", "inseticidas_inibidores_colinesterase"),
        ("Flúor, ácido fluorídrico e fluoretos inorgânicos", "fluoretos"),
        ("Arsênico", "arsenio"),
        ("Tolueno diisocianato", "tdi"),
    ],
)
def test_aliases_tier1_resolvem_exata(indice_real: dict[str, str], termo: str, slug_esperado: str) -> None:
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == slug_esperado
    assert resolucao.pendencia is None


# ---------------------------------------------------------------------------
# resolver_termo — termos de sílica (DT-003DV-01 faceta A, NR-15 Anexo 12 /
# NR-07 Anexo III Quadro 1)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "termo",
    [
        "Sílica livre",
        "Sílica livre cristalizada",
        "Sílica livre cristalina",
        "Quartzo",
        "Cristobalita",
        "Tridimita",
    ],
)
def test_termos_silica_resolvem_exata(indice_real: dict[str, str], termo: str) -> None:
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "silica"
    assert resolucao.pendencia is None


@pytest.mark.parametrize(
    "termo",
    [
        "Silicato de alumínio",
        "Silicato tricálcico",
        "Poeira respirável",
        "Poeira de madeira",
    ],
)
def test_termos_silicato_e_poeira_nao_resolvem_para_silica(
    indice_real: dict[str, str], termo: str
) -> None:
    # anti-FP D-ARQ-22: grafias vizinhas de sílica que não são o agente sílica.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.slug != "silica"


# ---------------------------------------------------------------------------
# resolver_termo — piso bilateral no fuzzy (DT-003DM-01, D-ARQ-50 P2)
# ---------------------------------------------------------------------------

def test_sigla_typada_nao_resolve_vizinha(indice_real: dict[str, str]) -> None:
    # Sem o piso, "hdl" resolvia FUZZY->hdi (dist 1 única). Forma <= PISO_FUZZY
    # não participa do fuzzy como termo de busca.
    resolucao = resolver_termo("hdl", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


def test_termo_curto_com_sufixo_nao_aterrissa_em_sigla(indice_real: dict[str, str]) -> None:
    # Lado-candidato do piso: "mibk9" tem len 5 (passa o piso de busca), dist 1
    # de "mibk" (len 4, barrada como candidata) — única chave a dist <= 2.
    resolucao = resolver_termo("mibk9", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


def test_sigla_exata_continua_exata(indice_real: dict[str, str]) -> None:
    resolucao = resolver_termo("HDI", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "hdi"
    assert resolucao.pendencia is None


def test_vigia_pares_fuzzy_chaves_longas(indice_real: dict[str, str]) -> None:
    # vigia DT-003DM-01 — par novo dentro do raio deve quebrar ruidosamente,
    # não caducar em silêncio como em 003.BP->003.DM.
    chaves = list(indice_real.items())
    pares = {
        frozenset({f1, f2})
        for i, (f1, s1) in enumerate(chaves)
        for f2, s2 in chaves[i + 1:]
        if len(f1) > PISO_FUZZY and len(f2) > PISO_FUZZY and s1 != s2
        and _levenshtein(f1, f2) <= 2
    }
    gabarito = {
        frozenset({"etanol", "metanol"}),
        frozenset({"metil_etil_cetona", "metil_butil_cetona"}),
        frozenset({"metoxietanol_2", "butoxietanol_2"}),
        frozenset({"2_butoxietanol", "2_metoxietanol"}),
    }
    assert pares == gabarito


# ---------------------------------------------------------------------------
# resolver_termo — sintéticos (empate fuzzy, aliases)
# ---------------------------------------------------------------------------

def test_empate_fuzzy_entre_dois_slugs_nao_resolve() -> None:
    # "abcdeh" está a dist 1 de "abcdef" e "abcdeg" (ambas len 6 > PISO_FUZZY)
    # — dois slugs distintos na mesma dist mínima -> empate -> NAO_RESOLVIDO.
    vocab_sintetico: dict[str, dict[str, object]] = {"abcdef": {}, "abcdeg": {}}
    indice = construir_indice_termos(vocab_sintetico)
    resolucao = resolver_termo("abcdeh", indice)
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
