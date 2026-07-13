from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import GHEContext, GHEPGR, Momento, Risco

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
    assert len(emitidos) == 1, f"{agente}: esperado apenas 1 exame emitido, got {list(por_exame)}"


def test_regra_bio_04_chumbo_grupo_sc(proto) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente("chumbo")
    emitidos = stage_5_emissao(ctx, proto)
    por_exame = {e.exame: e for e in emitidos}

    assert "chumbo_sangue" in por_exame
    assert "ala_urinario" in por_exame
    assert len(emitidos) == 2

    for slug in ("chumbo_sangue", "ala_urinario"):
        linha = por_exame[slug]
        assert linha.motivos[0].regra_id == "R-BIO-04-chumbo"
        assert linha.periodicidade_meses == 6
        assert linha.momentos == _MOMENTOS_QUADRO_2


def test_sem_agente_nao_emite_biomonitoramento(proto) -> None:  # type: ignore[no-untyped-def]
    ctx = _ctx_com_agente("ruido")
    emitidos = stage_5_emissao(ctx, proto)
    assert emitidos == []
