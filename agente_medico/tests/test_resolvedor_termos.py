from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import (
    PISO_FUZZY,
    Confianca,
    IndiceTermos,
    _levenshtein,
    construir_indice_termos,
    resolver_termo,
)

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def indice_real() -> IndiceTermos:
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(p.vocabulario.agentes)


# ---------------------------------------------------------------------------
# construir_indice_termos — vocabulário real
# ---------------------------------------------------------------------------

def test_indice_real_tem_106_entradas(indice_real: IndiceTermos) -> None:
    assert len(indice_real.slug_por_forma) == 106


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
def test_exatos_reais_003bo(indice_real: IndiceTermos, termo: str, slug_esperado: str) -> None:
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == slug_esperado
    assert resolucao.pendencia is None


def test_esforco_fisico_typo_acento_morre_na_normalizacao(indice_real: IndiceTermos) -> None:
    resolucao = resolver_termo("esforço fisico", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "esforco_fisico"
    assert resolucao.pendencia is None


def test_thinner_nao_resolvido_produto_nao_e_agente(indice_real: IndiceTermos) -> None:
    resolucao = resolver_termo("Thinner", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"
    assert resolucao.pendencia.bloqueante is False


def test_eaquipamento_desprotegido_dist_maior_que_2(indice_real: IndiceTermos) -> None:
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
        ("Trabalho em Altura", "trabalho_altura"),
    ],
)
def test_aliases_tier1_resolvem_exata(indice_real: IndiceTermos, termo: str, slug_esperado: str) -> None:
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
def test_termos_silica_resolvem_exata(indice_real: IndiceTermos, termo: str) -> None:
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
    indice_real: IndiceTermos, termo: str
) -> None:
    # anti-FP D-ARQ-22: grafias vizinhas de sílica que não são o agente sílica.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.slug != "silica"


# ---------------------------------------------------------------------------
# resolver_termo — piso bilateral no fuzzy (DT-003DM-01, D-ARQ-50 P2)
# ---------------------------------------------------------------------------

def test_sigla_typada_nao_resolve_vizinha(indice_real: IndiceTermos) -> None:
    # Sem o piso, "hdl" resolvia FUZZY->hdi (dist 1 única). Forma <= PISO_FUZZY
    # não participa do fuzzy como termo de busca.
    resolucao = resolver_termo("hdl", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


def test_termo_curto_com_sufixo_nao_aterrissa_em_sigla(indice_real: IndiceTermos) -> None:
    # Lado-candidato do piso: "mibk9" tem len 5 (passa o piso de busca), dist 1
    # de "mibk" (len 4, barrada como candidata) — única chave a dist <= 2.
    resolucao = resolver_termo("mibk9", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "vocabulario_ausente"


def test_sigla_exata_continua_exata(indice_real: IndiceTermos) -> None:
    resolucao = resolver_termo("HDI", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "hdi"
    assert resolucao.pendencia is None


def test_vigia_pares_fuzzy_chaves_longas(indice_real: IndiceTermos) -> None:
    # vigia DT-003DM-01 — par novo dentro do raio deve quebrar ruidosamente,
    # não caducar em silêncio como em 003.BP->003.DM.
    chaves = list(indice_real.slug_por_forma.items())
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
    # fuzzy_permitido nos dois slugs (D-ARQ-64): garante que o teste exercita
    # o ramo de EMPATE, não o de recusa por allowlist.
    vocab_sintetico: dict[str, dict[str, object]] = {
        "abcdef": {"fuzzy_permitido": True},
        "abcdeg": {"fuzzy_permitido": True},
    }
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


# ---------------------------------------------------------------------------
# resolver_termo — veto de allowlist fuzzy (D-ARQ-64, DT-003DV-01 faceta B)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("termo", ["Silício", "Silicio"])
def test_silicio_recusa_fuzzy_para_silica(indice_real: IndiceTermos, termo: str) -> None:
    # DT-003DV-01 faceta B: "Silício" (elemento, não o agente) está a dist 2
    # de "silica" — sem allowlist, virava FUZZY silica (falso-positivo com
    # R-RX-01 na cauda). Com D-ARQ-64, silica fora da allowlist -> recusa.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "fuzzy_recusado"
    assert resolucao.pendencia.destinatario == "extracao"
    assert resolucao.pendencia.bloqueante is False
    assert resolucao.pendencia.regra_origem == "D-ARQ-64"
    assert "silica" in resolucao.pendencia.motivo
    assert "2" in resolucao.pendencia.motivo
    assert termo in resolucao.pendencia.motivo


def test_microrganismo_singular_sobrevive_na_cauda(indice_real: IndiceTermos) -> None:
    # Zona de cauda (D-ARQ-64): microrganismos está na allowlist — o fuzzy
    # legítimo singular->plural continua vivo.
    resolucao = resolver_termo("Microrganismo", indice_real)
    assert resolucao.confianca == Confianca.FUZZY
    assert resolucao.slug == "microrganismos"
    assert resolucao.pendencia is None


def test_metanoll_recusa_metanol_e_nunca_resolve_etanol(indice_real: IndiceTermos) -> None:
    # Regressão do falso-positivo de filtro-de-candidato (D-ARQ-64): "metanoll"
    # tem metanol a dist 1 (vencedor único, fora da allowlist) e etanol a dist 2
    # (na allowlist). O veto é do RESULTADO: metanol vence e é recusado. Se a
    # allowlist filtrasse candidatos, metanol sumiria da disputa e etanol (dist 2)
    # venceria sozinho -> FUZZY etanol, exatamente o falso-positivo vedado.
    resolucao = resolver_termo("metanoll", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.slug != "etanol"
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "fuzzy_recusado"
    assert "metanol" in resolucao.pendencia.motivo
    assert "etanol" not in resolucao.pendencia.motivo.replace("metanol", "")


def test_allowlist_disjunta_dos_canais_de_criticidade(indice_real: IndiceTermos) -> None:
    # Sincronia D-ARQ-64: slug na allowlist fuzzy NÃO pode carregar criticidade
    # por nenhum dos 4 canais — computados do dado real, nunca lista digitada.
    import re

    import agente_medico.motor.predicados as predicados_mod

    p = carregar(PROTOCOLO_DIR)

    # Canal 1: regras.yaml — átomos (nomes) referenciados em "quando".
    def atomos_quando(no: object) -> set[str]:
        if isinstance(no, str):
            return {no}
        if isinstance(no, dict):
            return {a for v in no.values() for a in atomos_quando(v)}
        if isinstance(no, list):
            return {a for item in no for a in atomos_quando(item)}
        return set()

    canal_regras = {a for regra in p.regras for a in atomos_quando(regra.get("quando"))}

    # Canal 2: literais de agente em predicados.py (r.agente == "x" / in {...}).
    import inspect

    fonte = inspect.getsource(predicados_mod)
    canal_predicados = set(re.findall(r'r\.agente\s*==\s*"([a-z0-9_]+)"', fonte))
    for grupo in re.findall(r"r\.agente\s+in\s+\{([^}]*)\}", fonte):
        canal_predicados.update(re.findall(r'"([a-z0-9_]+)"', grupo))

    # Canal 3: is_ototoxico no agentes.yaml.
    canal_ototoxico = {
        slug
        for slug, meta in p.vocabulario.agentes.items()
        if isinstance(meta, dict) and meta.get("is_ototoxico") is True
    }

    # Canal 4: cargos.yaml — riscos_implicitos.
    canal_cargos = {
        risco
        for meta in p.vocabulario.cargos.values()
        if isinstance(meta, dict)
        for risco in meta.get("riscos_implicitos", [])
    }

    uniao = canal_regras | canal_predicados | canal_ototoxico | canal_cargos
    assert uniao, "canais de criticidade vazios — teste degenerou"
    assert indice_real.fuzzy_permitido, "allowlist vazia — teste degenerou"
    assert indice_real.fuzzy_permitido & uniao == set()
