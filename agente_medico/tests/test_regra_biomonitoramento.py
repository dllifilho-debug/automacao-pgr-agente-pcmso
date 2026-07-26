from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import GHEContext, GHEPGR, Momento, Risco
from agente_medico.tests.invariantes import linhas_de_risco

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

_MOMENTOS_PER = {Momento.PER}
_MOMENTOS_QUADRO_2 = {Momento.ADM, Momento.PER, Momento.RT, Momento.MR, Momento.DEM}


@pytest.fixture(scope="module")
def proto():  # type: ignore[no-untyped-def]
    return carregar(_PROTOCOLO_DIR)


def _ghe() -> GHEPGR:
    return GHEPGR(
        id="GHE-TEST",
        nome="Teste",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _ctx_com_agente(agente: str) -> GHEContext:
    risco = Risco(agente=agente, fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None)
    return GHEContext(pgr_ghe=_ghe(), riscos=[risco])


@pytest.mark.parametrize(
    "agente, regra_id, exame",
    [
        ("acetona", "R-BIO-04-acetona", "acetona_urina"),
        ("arsenio", "R-BIO-04-arsenio", "arsenio_urina"),
        ("dissulfeto_de_carbono", "R-BIO-04-dissulfeto_de_carbono", "ttca_urina"),
        ("estireno", "R-BIO-04-estireno", "acido_mandelico_fenilglioxilico"),
        ("mercurio", "R-BIO-04-mercurio", "mercurio_urina"),
        ("metil_etil_cetona", "R-BIO-04-metil_etil_cetona", "mek_urina"),
        ("monoxido_de_carbono", "R-BIO-04-monoxido_de_carbono", "carboxihemoglobina"),
        ("n_hexano", "R-BIO-04-n_hexano", "hexanodiona_urina"),
        ("tolueno", "R-BIO-04-tolueno", "ortocresol_urina"),
        ("tricloroetileno", "R-BIO-04-tricloroetileno", "acido_tricloroacetico"),
        ("xileno", "R-BIO-04-xileno", "acido_metilhipurico"),
        ("cromo_hexavalente", "R-BIO-04-cromo_hexavalente", "cromo_urina"),
        ("cobalto", "R-BIO-04-cobalto", "cobalto_urina"),
        ("fenol", "R-BIO-04-fenol", "fenol_urina"),
        ("metanol", "R-BIO-04-metanol", "metanol_urina"),
        ("diclorometano", "R-BIO-04-diclorometano", "diclorometano_urina"),
        ("etilbenzeno", "R-BIO-04-etilbenzeno", "acido_mandelico_fenilglioxilico"),
        ("anilina", "R-BIO-04-anilina", "metahemoglobina_sangue"),
        ("nitrobenzeno", "R-BIO-04-nitrobenzeno", "metahemoglobina_sangue"),
        ("indutores_metahemoglobina", "R-BIO-04-indutores_metahemoglobina", "metahemoglobina_sangue"),
        ("tricloroetano_111", "R-BIO-04-tricloroetano_111", "acido_tricloroacetico"),
        ("butadieno_13", "R-BIO-04-butadieno_13", "dihidro_acetilcisteina_butano_urina"),
        ("hdi", "R-BIO-04-hdi", "hexametilenodiamina_urina"),
        ("metoxietanol_2", "R-BIO-04-metoxietanol_2", "acido_metoxiacetico_urina"),
        ("metoxietilacetato_2", "R-BIO-04-metoxietilacetato_2", "acido_metoxiacetico_urina"),
        ("propanol_2", "R-BIO-04-propanol_2", "acetona_urina"),
        ("tdi", "R-BIO-04-tdi", "toluenodiamino_urina"),
        ("butoxietanol_2", "R-BIO-04-butoxietanol_2", "acido_butoxiacetico_urina"),
        ("chumbo_tetraetila", "R-BIO-04-chumbo_tetraetila", "chumbo_urina"),
        ("ciclohexanona", "R-BIO-04-ciclohexanona", "ciclohexanol_urina"),
        ("clorobenzeno", "R-BIO-04-clorobenzeno", "clorocatecol_urina"),
        ("etoxietanol", "R-BIO-04-etoxietanol", "acido_etoxiacetico_urina"),
        ("etoxietilacetato", "R-BIO-04-etoxietilacetato", "acido_etoxiacetico_urina"),
        ("furfural", "R-BIO-04-furfural", "acido_furoico_urina"),
        ("metil_butil_cetona", "R-BIO-04-metil_butil_cetona", "hexanodiona_urina"),
        ("mibk", "R-BIO-04-mibk", "mibk_urina"),
        ("n_metil_2_pirrolidona", "R-BIO-04-n_metil_2_pirrolidona", "hidroxi_metil_pirrolidona_urina"),
        ("dimetilacetamida", "R-BIO-04-dimetilacetamida", "metilacetamida_urina"),
        ("dimetilformamida", "R-BIO-04-dimetilformamida", "metilformamida_urina"),
        ("oxido_de_etileno", "R-BIO-04-oxido_de_etileno", "aduto_hev_hemoglobina"),
        ("tetracloroetileno", "R-BIO-04-tetracloroetileno", "tetracloroetileno_sangue"),
        ("tetrahidrofurano", "R-BIO-04-tetrahidrofurano", "tetrahidrofurano_urina"),
    ],
)
def test_regra_bio_04_grupo_ee(proto, agente: str, regra_id: str, exame: str) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente(agente)
    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert exame in por_exame, f"{agente}: esperado exame '{exame}', emitidos={list(por_exame)}"
    linha = por_exame[exame]
    assert linha.motivos[0].regra_id == regra_id
    assert linha.periodicidade_meses == 6
    assert linha.momentos == _MOMENTOS_PER
    # R-CLI-01 (piso universal, 003.EC) soma exame_clinico a toda matriz; a
    # contagem que importa é a das linhas de origem em risco.
    assert len(linhas_de_risco(emitidos)) == 1, (
        f"{agente}: esperado apenas 1 exame de risco emitido, got {list(por_exame)}"
    )


def test_regra_bio_04_chumbo_grupo_sc(proto) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente("chumbo")
    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert "chumbo_sangue" in por_exame
    assert "ala_urinario" in por_exame
    assert len(linhas_de_risco(emitidos)) == 2

    for slug in ("chumbo_sangue", "ala_urinario"):
        linha = por_exame[slug]
        assert linha.motivos[0].regra_id == "R-BIO-04-chumbo"
        assert linha.periodicidade_meses == 6
        assert linha.momentos == _MOMENTOS_QUADRO_2


@pytest.mark.parametrize(
    "agente, regra_id, exame",
    [
        ("cadmio", "R-BIO-04-cadmio", "cadmio_urina"),
        ("fluoretos", "R-BIO-04-fluoretos", "fluoreto_urinario"),
        (
            "inseticidas_inibidores_colinesterase",
            "R-BIO-04-inseticidas_inibidores_colinesterase",
            "acetilcolinesterase_eritrocitaria",
        ),
    ],
)
def test_regra_bio_04_grupo_sc_agente_unico(proto, agente: str, regra_id: str, exame: str) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente(agente)
    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert exame in por_exame, f"{agente}: esperado '{exame}', emitidos={list(por_exame)}"
    linha = por_exame[exame]
    assert linha.motivos[0].regra_id == regra_id
    assert linha.periodicidade_meses == 6
    assert linha.momentos == _MOMENTOS_QUADRO_2
    assert len(linhas_de_risco(emitidos)) == 1, (
        f"{agente}: esperado 1 exame de risco, got {list(por_exame)}"
    )


def test_sem_agente_nao_emite_biomonitoramento(proto) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente("ruido")
    emitidos = stage_5_emissao(ctx, proto)
    assert linhas_de_risco(emitidos) == []
