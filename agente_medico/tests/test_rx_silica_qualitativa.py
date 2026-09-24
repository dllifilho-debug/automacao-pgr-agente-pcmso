"""R-RX-01-qual / DT-003EC-01 — sílica com avaliação qualitativa P×S no PGR
emite RX tórax OIT 12M, distinto do ramo "sem avaliação quantitativa" (24M,
R-RX-01-sem). Cada teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.hidratacao import hidratar_ghe
from agente_medico.motor.parser_familia_consciente import PalavraPDF, parsear_paginas
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import IndiceTermos, construir_indice_termos
from agente_medico.motor.tipos import (
    GHEPGR,
    ExameEmitido,
    GHEContext,
    GHEVerbatim,
    Momento,
    RiscoPGR,
    RiscoVerbatim,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


# Coordenadas copiadas da linha real de sílica do GHE 02 (ARMAÇÃO) de Porto
# Araras I: cabeçalho S@437/P@462/MEDIDAS@541 na linha GRUPO.
def _pagina_porto_araras(*extras: PalavraPDF) -> tuple[PalavraPDF, ...]:
    return (
        _p("GHE", 52.0, 10.0),
        _p("02", 76.0, 10.0),
        _p("-", 91.0, 10.0),
        _p("ARMAÇÃO", 98.0, 10.0),
        _p("PERIGO", 113.0, 20.0),
        _p("NÍVEL", 489.0, 20.0),
        _p("GRUPO", 57.0, 25.0),
        _p("FONTE", 177.0, 25.0),
        _p("AGRAVO", 257.0, 25.0),
        _p("S", 437.0, 25.0),
        _p("P", 462.0, 25.0),
        _p("MEDIDAS", 541.0, 25.0),
        _p("QUIMICO", 57.0, 100.0),
        _p("Sílica", 113.0, 100.0),
        _p("livre", 133.0, 100.0),
        _p("Manipulação", 177.0, 100.0),
        _p("A", 257.0, 100.0),
        _p("exposição", 264.0, 100.0),
        _p("4", 437.0, 100.0),
        _p("1", 463.0, 100.0),
        _p("BAIXO", 496.0, 100.0),
        _p("Uso", 541.0, 100.0),
        *extras,
    )


def test_parser_captura_s_p_nivel_na_linha_do_risco() -> None:
    # Reversão que mata: _parsear_bloco deixar de passar
    # _localizar_colunas_avaliacao(...) a _extrair_riscos (avaliacao=None) —
    # a banda S·P·NÍVEL some e avaliacao_qualitativa sai "".
    (ghe,) = parsear_paginas([_pagina_porto_araras()])

    (risco,) = ghe.riscos
    assert risco.agente == "Sílica livre"
    assert risco.avaliacao_qualitativa == "4 1 BAIXO"


def test_parser_acha_medidas_na_linha_perigo_forma_fascino() -> None:
    # Fascino: MEDIDAS@578 está na linha PERIGO, não na linha GRUPO (medido).
    # Reversão que mata: procurar "MEDIDAS" só em linha_grupo — o fim da banda
    # não é localizado e a avaliação sai "".
    pagina = (
        _p("GHE", 10.0, 10.0),
        _p("06", 30.0, 10.0),
        _p("-", 45.0, 10.0),
        _p("PRODUÇÃO", 50.0, 10.0),
        _p("PERIGO", 113.0, 20.0),
        _p("NÍVEL", 526.0, 20.0),
        _p("MEDIDAS", 578.0, 20.0),
        _p("GRUPO", 57.0, 25.0),
        _p("FONTE", 174.0, 25.0),
        _p("AGRAVO", 318.0, 25.0),
        _p("S", 473.0, 25.0),
        _p("P", 498.0, 25.0),
        _p("QUIMICO", 57.0, 100.0),
        _p("Sílica", 113.0, 100.0),
        _p("livre", 133.0, 100.0),
        _p("Em", 174.0, 100.0),
        _p("A", 318.0, 100.0),
        _p("3", 473.0, 100.0),
        _p("2", 500.0, 100.0),
        _p("MODERADO", 526.0, 100.0),
        _p("Uso", 578.0, 100.0),
    )
    (ghe,) = parsear_paginas([pagina])

    assert ghe.riscos[0].avaliacao_qualitativa == "3 2 MODERADO"


def test_parser_linha_so_com_avaliacao_nao_estende_o_risco() -> None:
    # Reversão que mata: contar palavra da banda "avaliacao" como conteúdo
    # (tem_conteudo = True) — a linha "(4)" deixa de encerrar o span e a
    # palavra órfã da banda AGENTE na linha seguinte é colada ao agente.
    extras = (
        _p("(4)", 503.0, 110.0),
        _p("órfã", 113.0, 120.0),
    )
    (ghe,) = parsear_paginas([_pagina_porto_araras(*extras)])

    assert ghe.riscos[0].agente == "Sílica livre"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def indice(proto: Protocolo) -> IndiceTermos:
    return construir_indice_termos(proto.vocabulario.agentes)


def _ghe_verbatim(avaliacao: str) -> GHEVerbatim:
    return GHEVerbatim(
        nome="ARMAÇÃO",
        cargos=("Armador",),
        riscos=(
            RiscoVerbatim(
                agente="Sílica livre",
                quantificacao="",
                fonte_geradora="Manipulação do produto",
                avaliacao_qualitativa=avaliacao,
            ),
        ),
    )


@pytest.mark.parametrize(
    ("avaliacao", "nivel"),
    [
        ("4 1 BAIXO (4)", "BAIXO"),          # Porto Araras I
        ("3 2 MODERADO \x006\x00", "MODERADO"),  # Vila Brasil / Fascino
    ],
)
def test_hidratacao_leva_o_nivel_ao_risco_pgr(
    indice: IndiceTermos, avaliacao: str, nivel: str
) -> None:
    # Reversão que mata: não passar nivel_risco=nivel_risco ao RiscoPGR do
    # ramo EXATA em hidratar_ghe — o nível fica None e o ramo R-RX-01-qual
    # nunca é alcançado em produção.
    ghe_pgr, pendencias = hidratar_ghe(_ghe_verbatim(avaliacao), indice, posicao=1)

    assert ghe_pgr.riscos[0].agente == "silica"
    assert ghe_pgr.riscos[0].nivel_risco == nivel
    assert pendencias == []


def test_hidratacao_nao_definido_e_declaracao_nao_pendencia(indice: IndiceTermos) -> None:
    # "NÃO DEFINIDO" é o PGR declarando que não avaliou (Porto Araras I, 8/172).
    # Reversão que mata: tratar "NÃO DEFINIDO" como texto não reconhecido — sai
    # pendência avaliacao_qualitativa_nao_parseada falsa.
    ghe_pgr, pendencias = hidratar_ghe(_ghe_verbatim("NÃO DEFINIDO"), indice, posicao=1)

    assert ghe_pgr.riscos[0].nivel_risco is None
    assert pendencias == []


def test_hidratacao_avaliacao_ininteligivel_vira_pendencia_nao_bloqueante(
    indice: IndiceTermos,
) -> None:
    # Reversão que mata: remover o append da Pendencia
    # avaliacao_qualitativa_nao_parseada — o texto some em silêncio e a sílica
    # cai em 24M sem ninguém saber por quê (anti-supressão D-ARQ-31/35).
    ghe_pgr, pendencias = hidratar_ghe(_ghe_verbatim("BAIXO"), indice, posicao=1)

    assert ghe_pgr.riscos[0].nivel_risco is None
    assert [(p.tipo, p.bloqueante) for p in pendencias] == [
        ("avaliacao_qualitativa_nao_parseada", False)
    ]


def _rx(proto: Protocolo, agente: str, nivel_risco: str | None) -> tuple[ExameEmitido, GHEContext]:
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste",
        cargos=(),
        riscos=(
            RiscoPGR(
                tipo="", agente=agente, quantificacao=None, severidade=None, nivel_risco=nivel_risco
            ),
        ),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    rx = next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")
    return rx, ctx


def test_silica_com_avaliacao_qualitativa_emite_rx_12m_por_r_rx_01_qual(proto: Protocolo) -> None:
    # Reversões que matam, cada uma sozinha: (a) apenas_qualitativa=False no
    # ramo (b) de _helper_silica_asbesto; (b) Fase A de stage_2_riscos não
    # copiar nivel_risco para Risco; (c) silica_asbesto_sem_medicao perder o
    # "and not r.apenas_qualitativa" (R-RX-01-sem dispara junto); (d) remover
    # R-RX-01-qual de regras.yaml.
    rx, ctx = _rx(proto, "silica", "BAIXO")

    assert rx.periodicidade_meses == 12
    assert rx.periodicidade_apos_15a is None
    assert rx.momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}
    assert [m.regra_id for m in rx.motivos] == ["R-RX-01-qual"]
    assert ctx.pendencias == []


def test_asbesto_com_avaliacao_qualitativa_segue_24m(proto: Protocolo) -> None:
    # A decisão do Diovanni é sobre sílica; asbesto não tem medição nem decisão.
    # Reversão que mata: tirar o `risco.agente == "silica"` de
    # apenas_qualitativa no helper — asbesto qualitativo cairia em 12M.
    rx, _ = _rx(proto, "asbesto", "BAIXO")

    assert rx.periodicidade_meses == 24
    assert [m.regra_id for m in rx.motivos] == ["R-RX-01-sem"]
