"""R-PKG-TRANSITO / DT-003EB-01 classe (4) — risco de trânsito declarado no PGR
emite acuidade visual + audiometria 12M adm/per/MR. Cada teste nomeia a
reversão de código que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.parser_familia_consciente import PalavraPDF, parsear_paginas
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import (
    Confianca,
    IndiceTermos,
    construir_indice_termos,
    resolver_termo,
)
from agente_medico.motor.tipos import GHEPGR, GHEContext, Momento, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_TERMO_PGR = "Bater contra ou ser atingido por (trânsito)"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def indice(proto: Protocolo) -> IndiceTermos:
    return construir_indice_termos(proto.vocabulario.agentes)


def test_termo_do_pgr_resolve_exato_para_transito_via_publica(indice: IndiceTermos) -> None:
    # Reversão que mata: tirar o termo de `termos:` de transito_via_publica em
    # agentes.yaml — o risco volta a vocabulario_ausente e o pacote não dispara.
    resolucao = resolver_termo(_TERMO_PGR, indice)

    assert resolucao.confianca == Confianca.EXATA
    assert resolucao.slug == "transito_via_publica"


def test_transito_sozinho_nao_resolve(indice: IndiceTermos) -> None:
    # Anti-FP: "trânsito" aparece no acervo como circulação a pé ("Evitar o
    # trânsito em corredores"). Mutação que mata: acrescentar "Trânsito" aos
    # termos de transito_via_publica.
    assert resolver_termo("Trânsito", indice).confianca == Confianca.NAO_RESOLVIDO


def test_risco_de_transito_emite_acuidade_e_audiometria_12m(proto: Protocolo) -> None:
    # Reversão que mata: remover R-PKG-TRANSITO de regras.yaml — o GHE só com
    # risco de trânsito não recebe nenhum dos dois exames.
    ghe = GHEPGR(
        id="GHE-01",
        nome="DIREÇÃO",
        cargos=(),
        riscos=(RiscoPGR(tipo="", agente="transito_via_publica", quantificacao=None, severidade=None),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    exames = {e.exame: e for e in stage_5_emissao(ctx, proto)}

    for slug in ("acuidade_visual", "audiometria"):
        assert exames[slug].periodicidade_meses == 12
        assert exames[slug].momentos == {Momento.ADM, Momento.PER, Momento.MR}
        assert [m.regra_id for m in exames[slug].motivos] == ["R-PKG-TRANSITO"]


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


def test_legenda_colada_ao_ultimo_risco_nao_entra_no_agente() -> None:
    # Coordenadas do GHE VENDAS do Fascino: a linha "Legenda (P × S)" começa
    # na banda GRUPO (x=59) logo após o último risco, sem linha vazia.
    # Reversão que mata: remover o break por 1ª palavra na banda GRUPO em
    # _extrair_riscos — o agente vira "Bater ... (trânsito) S): Irrelevante".
    pagina = (
        _p("GHE", 10.0, 10.0),
        _p("19", 30.0, 10.0),
        _p("-", 45.0, 10.0),
        _p("VENDAS", 50.0, 10.0),
        _p("PERIGO", 113.0, 20.0),
        _p("GRUPO", 57.0, 25.0),
        _p("FONTE", 174.0, 25.0),
        _p("AGRAVO", 277.0, 25.0),
        _p("ACIDENTE", 57.0, 100.0),
        _p("Bater", 113.0, 100.0),
        _p("contra", 132.0, 100.0),
        _p("ou", 156.0, 100.0),
        _p("Atividades", 174.0, 100.0),
        _p("ser", 113.0, 110.0),
        _p("atingido", 125.0, 110.0),
        _p("por", 154.0, 110.0),
        _p("deslocamento", 174.0, 110.0),
        _p("(trânsito)", 113.0, 120.0),
        _p("pública", 174.0, 120.0),
        _p("Legenda", 59.0, 130.0),
        _p("S):", 116.0, 130.0),
        _p("Irrelevante", 151.0, 130.0),
    )
    (ghe,) = parsear_paginas([pagina])

    assert ghe.riscos[0].agente == _TERMO_PGR
