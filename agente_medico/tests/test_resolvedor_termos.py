from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.hidratacao import hidratar_ghe
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import (
    PISO_FUZZY,
    Confianca,
    IndiceTermos,
    _levenshtein,
    construir_indice_termos,
    resolver_termo,
)
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def indice_real() -> IndiceTermos:
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(
        p.vocabulario.agentes, fracoes_sem_agente=p.vocabulario.fracoes_sem_agente
    )


# ---------------------------------------------------------------------------
# construir_indice_termos — vocabulário real
# ---------------------------------------------------------------------------

def test_indice_real_tem_144_entradas(indice_real: IndiceTermos) -> None:
    # 114 -> 119 em 003.FH: +5 aliases de R-PGR-07 (proposta 003.FF). 119 -> 120 na
    # correção 003.FH-C3: +1 alias, a grafia singular do par de sufixo de
    # `postura_inadequada`. 120 -> 123 em 003.FL: +3 aliases de PNOS/PNOR em
    # `poeira_nao_classificada`, achado da comparação PGR Viverde × gabarito
    # assinado (Dra. Patrícia Montalvo Moraes). 123 -> 124 na mesma sessão
    # (branch `claude/festive-gates-soy0fr`): +1 alias, a mesma classificação
    # PNOS nomeada por extenso, achado da comparação PGR CMO Residencial Aurora
    # Lago das Rosas × gabarito assinado. 124 -> 125 na mesma sessão: +1 slug
    # novo, `poeira_de_madeira` (DT-003EJ-01 RESOLVIDA, R-RX-03/R-ESP-03) — o
    # próprio slug entra sem precisar de `termos:` (normaliza igual ao literal
    # "Poeira de madeira" do PGR). 125 -> 144 (branch `docs/003fg-...`, DT-003M-02(A)):
    # +19 slugs de composição-de-FDS (cimento Ciplan, tinta acrílica, Adesivo PVC
    # Tigre, conservantes Leinertex — vocabulário CAS, não termo de PGR); cada um
    # entra sem `termos:`, o próprio slug normaliza como 1 forma. Guard de
    # inventário movido junto com o dado, lição de 003.CV/003.DM.
    assert len(indice_real.slug_por_forma) == 144


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
# resolver_termo — aliases de vibração Tier 1-C (003.EJ, D-ARQ-70)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "termo,slug_esperado",
    [
        ("Vibrações localizadas (mão e braço)", "vibracao_mao_braco"),
        ("Vibração (mão e braço)", "vibracao_mao_braco"),
        ("VMB", "vibracao_mao_braco"),
        ("VCI", "vibracao_corpo_inteiro"),
    ],
)
def test_aliases_vibracao_tier1c_resolvem_exata(
    indice_real: IndiceTermos, termo: str, slug_esperado: str
) -> None:
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == slug_esperado
    assert resolucao.pendencia is None


@pytest.mark.parametrize(
    "termo",
    [
        "Vibrações localizadas (mão e braço)",
        "Vibração (mão e braço)",
        "VMB",
        "Vibrações em Mãos e Braços",
    ],
)
def test_aliases_mao_braco_nao_resolvem_para_corpo_inteiro_ou_generico(
    indice_real: IndiceTermos, termo: str
) -> None:
    # anti-FP D-ARQ-70 cl.1.iv: grafia de mão-e-braço não pode escorregar para
    # o slug vizinho da mesma família (corpo inteiro) nem para o genérico.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.slug != "vibracao_corpo_inteiro"
    assert resolucao.slug != "vibracao"


def test_vibracao_generica_continua_resolvendo_slug_generico(indice_real: IndiceTermos) -> None:
    # "Vibração" segue alimentando o ramo Ausente de D-ARQ-13/D-ARQ-16 — os
    # aliases de corpus não deslocam o slug genérico.
    resolucao = resolver_termo("Vibração", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "vibracao"
    assert resolucao.pendencia is None


# ---------------------------------------------------------------------------
# resolver_termo — aliases ergonômicos (003.FA, D-ARQ-70 cl.1)
# ---------------------------------------------------------------------------

def test_postural_resolve_exata_para_postura_inadequada(indice_real: IndiceTermos) -> None:
    resolucao = resolver_termo("Postural", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "postura_inadequada"
    assert resolucao.pendencia is None


def test_postural_nao_resolve_para_vizinhos_da_familia_ergonomica(
    indice_real: IndiceTermos,
) -> None:
    # anti-FP D-ARQ-70 cl.1.iv: "Postural" não pode escorregar para os slugs
    # vizinhos da mesma família ergonômica.
    resolucao = resolver_termo("Postural", indice_real)
    assert resolucao.slug != "esforco_fisico"
    assert resolucao.slug != "movimento_repetitivo"


def test_levantamento_manual_resolve_exata_para_esforco_fisico(
    indice_real: IndiceTermos,
) -> None:
    resolucao = resolver_termo("Levantamento e Transporte Manual de cargas", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "esforco_fisico"
    assert resolucao.pendencia is None


def test_levantamento_manual_nao_resolve_para_vizinhos_da_familia_ergonomica(
    indice_real: IndiceTermos,
) -> None:
    # anti-FP D-ARQ-70 cl.1.iv: "Levantamento e Transporte Manual de cargas"
    # não pode escorregar para os slugs vizinhos da mesma família ergonômica.
    resolucao = resolver_termo("Levantamento e Transporte Manual de cargas", indice_real)
    assert resolucao.slug != "postura_inadequada"
    assert resolucao.slug != "movimento_repetitivo"


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
# resolver_termo — sigla PNOS/PNOR (R-RX-01-pnos-*/R-ESP-02, NR-07 Anexo III
# Quadro 2). Medido no PGR VIVERDE V02 - 03.02.25.pdf: a CMO nomeia a
# classificação diretamente na coluna "Perigo" ("PNOS/ PNOR", quebrada em
# duas linhas pelo PDF) — não é fração isolada (D-ARQ-83 cl.2 não se aplica).
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("termo", ["PNOS", "PNOR", "PNOS/PNOR", "pnos", "PNOS / PNOR"])
def test_sigla_pnos_pnor_resolve_para_poeira_nao_classificada(
    indice_real: IndiceTermos, termo: str
) -> None:
    # Reversão: remover os aliases de `poeira_nao_classificada.termos` em
    # agentes.yaml (ou reduzi-los a ["PNOS/PNOR"], derrubando as parametrizações
    # "PNOS"/"PNOR" isoladas) faz este teste falhar — confiança cai para
    # NAO_RESOLVIDO e o slug retorna None.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "poeira_nao_classificada"
    assert resolucao.pendencia is None


# ---------------------------------------------------------------------------
# resolver_termo — PNOS por extenso (R-RX-01-pnos-*/R-ESP-02, NR-07 Anexo III
# Quadro 2). Medido no PGR(ADENDO) CMO RESIDENCIAL AURORA LAGO DAS ROSAS
# 27.08.26.pdf: a CMO nomeia a mesma classificação por extenso em vez da
# sigla — "Particulados insolúveis ou de baixa solubilidade não
# especificados de outra maneira (PNOS)", 10 ocorrências no documento — sem
# nenhum uso da sigla isolada nesse PGR. Mesma classificação de D-ARQ-83
# cl.2, não fração isolada.
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "termo",
    [
        "Particulados insolúveis ou de baixa solubilidade não especificados de outra maneira (PNOS)",
        "particulados insolúveis ou de baixa solubilidade não especificados de outra maneira (pnos)",
        "Particulados insolúveis ou de baixa solubilidade não especificados de outra  maneira (PNOS)",
    ],
)
def test_pnos_por_extenso_resolve_para_poeira_nao_classificada(
    indice_real: IndiceTermos, termo: str
) -> None:
    # Reversão: remover o 4º alias (a forma por extenso) de
    # `poeira_nao_classificada.termos` em agentes.yaml faz este teste falhar —
    # confiança cai para NAO_RESOLVIDO e o slug retorna None.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "poeira_nao_classificada"
    assert resolucao.pendencia is None


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
        # DT-003M-02(A), branch `docs/003fg-...`: par novo, mesma classe dos acima
        # (substâncias distintas de nome parecido — silicato tri- vs dicálcico, os
        # dois componentes reais do Cimento Ciplan). Nenhum dos dois slugs tem
        # `fuzzy_permitido: true` (omitido, default False, D-ARQ-64) — revisado e
        # aceito no gabarito, não bloqueia; se algum dia alguém marcar fuzzy_permitido
        # nesse par, esta proximidade já está documentada aqui.
        frozenset({"silicato_dicalcico", "silicato_tricalcico"}),
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

    # D-ARQ-82 cl.3 (003.FC): a hidratação grava a causa real da não-resolução
    # no risco — aqui "fuzzy_recusado", não um tipo qualquer. O que muda com a
    # emenda 003.FC é como o selo CLASSIFICA essa causa (deixa de ser
    # causa-acerto), não o que a hidratação escreve no campo.
    ghe = GHEVerbatim(
        nome="Teste",
        cargos=(),
        riscos=(RiscoVerbatim(agente="metanoll", quantificacao="", fonte_geradora=""),),
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)
    assert ghe_pgr.riscos[0].agente is None
    assert ghe_pgr.riscos[0].causa_nao_resolucao == "fuzzy_recusado"


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


# ---------------------------------------------------------------------------
# resolver_termo — fração-sem-agente (D-ARQ-83)
# ---------------------------------------------------------------------------

def test_poeira_respiravel_nao_resolve_com_pendencia_fracao_sem_agente(
    indice_real: IndiceTermos,
) -> None:
    # Reverte para: sem a cl.3 (consulta antes do fuzzy), devolveria
    # vocabulario_ausente / protocolo / D-ARQ-50.
    resolucao = resolver_termo("Poeira respirável", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "fracao_sem_agente"
    assert resolucao.pendencia.destinatario == "elaborador_pgr"
    assert resolucao.pendencia.regra_origem == "R-PGR-05"
    assert resolucao.pendencia.bloqueante is False


def test_poeiras_respiraveis_metalicas_nao_resolve_com_pendencia_fracao_sem_agente(
    indice_real: IndiceTermos,
) -> None:
    # Reverte para: sem a cl.3, devolveria vocabulario_ausente / protocolo / D-ARQ-50.
    resolucao = resolver_termo("Poeiras Respiráveis/Metálicas", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert resolucao.pendencia is not None
    assert resolucao.pendencia.tipo == "fracao_sem_agente"
    assert resolucao.pendencia.destinatario == "elaborador_pgr"
    assert resolucao.pendencia.regra_origem == "R-PGR-05"


def test_poeira_de_madeira_nao_e_fracao_sem_agente(indice_real: IndiceTermos) -> None:
    # anti-FP D-ARQ-83 cl.4(iv), preservado: madeira é o agente, o termo não
    # entra na categoria fracao_sem_agente. Reverte para: categoria virar
    # balde de tudo que começa com "poeira".
    resolucao = resolver_termo("Poeira de madeira", indice_real)
    assert resolucao.pendencia is None or resolucao.pendencia.tipo != "fracao_sem_agente"


@pytest.mark.parametrize("termo", ["Poeira de madeira", "poeira de madeira", "POEIRA DE MADEIRA"])
def test_poeira_de_madeira_resolve_para_slug_proprio(
    indice_real: IndiceTermos, termo: str
) -> None:
    # Correção (DT-003EJ-01 RESOLVIDA, R-RX-03/R-ESP-03): até esta sessão o termo
    # ficava vocabulario_ausente por decisão deliberada (madeira não é PNOS,
    # ver test_poeira_de_madeira_nao_e_fracao_sem_agente acima) — o registro
    # antigo da asserção NAO_RESOLVIDO fica preservado no histórico (D-ARQ-06),
    # não aqui. Reversão: remover o agente `poeira_de_madeira` de agentes.yaml
    # faz este teste falhar — confiança cai para NAO_RESOLVIDO.
    resolucao = resolver_termo(termo, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "poeira_de_madeira"
    assert resolucao.pendencia is None


def test_fracoes_sem_agente_nunca_entram_no_indice_de_slugs(indice_real: IndiceTermos) -> None:
    # D-ARQ-83 cl.2, computado do dado real. Reverte para: a forma resolveria
    # e D-ARQ-82 cl.1 devolveria VÁLIDA.
    assert indice_real.fracoes_sem_agente, "fracoes_sem_agente vazio — teste degenerou"
    assert indice_real.fracoes_sem_agente.isdisjoint(indice_real.slug_por_forma.keys())


def test_fracoes_sem_agente_alcancavel_pelo_caminho_de_producao() -> None:
    # Mesma chamada de orquestracao_pgr.py:269. Reverte para: campo populado
    # no YAML mas nunca passado ao construtor (classe D-ARQ-67/campo morto).
    p = carregar(PROTOCOLO_DIR)
    indice = construir_indice_termos(
        p.vocabulario.agentes, fracoes_sem_agente=p.vocabulario.fracoes_sem_agente
    )
    assert indice.fracoes_sem_agente


def test_fracao_sem_agente_colidindo_com_slug_levanta_value_error() -> None:
    vocab_sintetico = {"poeira_de_ferro": {}}
    with pytest.raises(ValueError, match="Colisão"):
        construir_indice_termos(vocab_sintetico, fracoes_sem_agente=["Poeira de ferro"])


# ---------------------------------------------------------------------------
# R-PGR-07 (proposta 003.FF) — sinonímia de nomenclatura de perigo, 003.FH
#
# Fatia de DADO: nenhum código de motor tocado. Cada teste nomeia a reversão
# em `agentes.yaml` que o deixa vermelho — sem isso o teste não entra
# (CLAUDE.md, cláusula de reversão nomeada).
#
# Escopo declarado: só formas com verbatim MEDIDO e citado em doc versionado
# (MEDICAO_003FF_par_T65.md §3/§4/§7). O PGR ALT T65 não está no acervo
# versionado (DH-003FE-01), logo as demais formas do resíduo ficam [A MEDIR].
# ---------------------------------------------------------------------------

def test_r_pgr_07_queda_em_altura_resolve_trabalho_altura(
    indice_real: IndiceTermos,
) -> None:
    """Reversão que mata: remover "Queda em altura" de `termos:` de
    `trabalho_altura` em agentes.yaml. Sinônimo, não typo — Levenshtein ≤2
    contra "Trabalho em Altura" nunca casaria (13 caracteres de distância),
    e `trabalho_altura` sequer tem `fuzzy_permitido`.
    """
    resolucao = resolver_termo("Queda em altura", indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "trabalho_altura"
    assert resolucao.pendencia is None


# NOTA: "o alias novo não desloca a grafia da NR-35" NÃO ganha teste próprio.
# `test_aliases_tier1_resolvem_exata` já carrega ("Trabalho em Altura",
# "trabalho_altura") desde 003.DM, e a reversão que mataria um mata o outro —
# não seria discriminante. Varredura inversa de 003.EK aplicada antes de entrar.


@pytest.mark.parametrize(
    "grafia",
    [
        "Sílica Livre - Poeira respirável",
        "Silica Livre - Poeira respiravel",
        "SÍLICA LIVRE - POEIRA RESPIRÁVEL",
    ],
)
def test_r_pgr_07_silica_com_fracao_resolve_nas_tres_grafias_de_caixa(
    indice_real: IndiceTermos, grafia: str
) -> None:
    """Reversão que mata as três: remover "Sílica Livre - Poeira respirável" de
    `termos:` de `silica`.

    Reversões parciais, **medidas** na correção 003.FH-C3 (a redação anterior
    dizia que retirar o `.casefold()` matava "as duas últimas", e não mata):
    são DOIS mecanismos independentes em `normalizar_termo`, cada um cobrindo
    uma grafia. Retirar o `.casefold()` mata só "SÍLICA LIVRE - POEIRA
    RESPIRÁVEL" — a forma sem acento continua resolvendo, porque quem a colapsa
    é a decomposição NFKD, que roda antes. Retirar o descarte de combinantes
    NFKD mata só "Silica Livre - Poeira respiravel". Nenhum dos dois, sozinho,
    mata duas grafias.
    """
    resolucao = resolver_termo(grafia, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "silica"


def test_fracao_nua_segue_nao_resolvida_apos_o_alias_de_silica(
    indice_real: IndiceTermos,
) -> None:
    """D-ARQ-83 cl.2 sobrevive à fatia: substância+fração resolve, fração nua não.

    Reversão que mata: **remover "Poeira respirável" de `fracoes_sem_agente`** —
    com ou sem promovê-la a `termos:` de `silica`, as duas variantes deixam este
    teste vermelho. É o erro que o alias novo torna tentador e que atribuiria
    sílica a toda poeira medida, inclusive a de madeira e a metálica.

    Reversão que NÃO serve, e por quê: acrescentar "Poeira respirável" a
    `termos:` de `silica` **sem** tirá-la de `fracoes_sem_agente` faz
    `construir_indice_termos` levantar `ValueError` de colisão — o teste erra na
    fixture em vez de falhar na asserção, logo quem discrimina ali é o guard de
    colisão pré-existente, não este teste (varredura inversa, 003.FH).
    """
    resolucao = resolver_termo("Poeira respirável", indice_real)
    assert resolucao.confianca == Confianca.NAO_RESOLVIDO
    assert resolucao.slug is None
    assert "poeira_respiravel" in indice_real.fracoes_sem_agente
    assert "poeira_respiravel" not in indice_real.slug_por_forma


def test_r_pgr_07_sufixo_ou_volumes_resolve_esforco_fisico(
    indice_real: IndiceTermos,
) -> None:
    """Reversão que mata: remover
    "Levantamento e transporte manual de cargas ou volumes" de `termos:` de
    `esforco_fisico`. O alias antigo, sem o sufixo, não alcança: são 11
    caracteres de diferença contra um piso fuzzy de 2.
    """
    resolucao = resolver_termo(
        "Levantamento e transporte manual de cargas ou volumes", indice_real
    )
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "esforco_fisico"


@pytest.mark.parametrize(
    "forma",
    ["Postura incorreta de trabalho", "Postura de pé por longos períodos"],
)
def test_r_pgr_07_duas_formas_de_postura_resolvem_postura_inadequada(
    indice_real: IndiceTermos, forma: str
) -> None:
    """Reversão que mata: remover as duas formas de `termos:` de
    `postura_inadequada`, deixando só "Postural". Nenhuma das duas cai no raio
    fuzzy de "Postural".
    """
    resolucao = resolver_termo(forma, indice_real)
    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "postura_inadequada"


def test_r_pgr_07_par_de_sufixo_de_postura_resolve_exata_nas_duas_grafias(
    indice_real: IndiceTermos,
) -> None:
    """O par de grafias do §4 difere por SUFIXO, e as duas têm de sair EXATA.

    Reversão que mata: remover **"Postura de pé por longos período"** (singular)
    de `termos:` de `postura_inadequada`, mantendo a plural. A singular continua
    chegando ao slug — mas pelo ramo FUZZY de D-ARQ-64, distância 1, porque
    `postura_inadequada` tem `fuzzy_permitido: true` —, logo a asserção de
    `Confianca.EXATA` fica vermelha e a de slug, não. É exatamente a confusão que
    a correção 003.FH-C3 desfez: `casefold`/NFKD colapsam caixa e acento, nunca
    "periodo" vs "periodos".

    Discriminante contra o teste acima, medido: remover a grafia **singular**
    mata só este (o de cima segue verde); remover a plural mata os dois. Logo
    este teste cobre comportamento que nenhum outro cobre.
    """
    for grafia in ("Postura de pé por longos períodos", "Postura de pé por longos período"):
        resolucao = resolver_termo(grafia, indice_real)
        assert resolucao.confianca == Confianca.EXATA, grafia
        assert resolucao.slug == "postura_inadequada", grafia
        assert resolucao.pendencia is None, grafia
