"""D-ARQ-88 — origem do risco pelas pernas verdadeiras da regra que emitiu
(DH-003ED-01, faceta `risco_origem`). Caso de conferência: Aurora 27/08/26,
GHE 11 INSTALAÇÕES HIDRO-SANITÁRIAS (PGR p. 45: ciclohexanona, metiletilcetona e
tetrahidrofurano MODERADO) — R-CLI-05 saía com `risco_origem=None`. Cada teste
nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.predicados import (
    PRIMITIVOS_SEM_RISCO,
    REGISTRO_PRIMITIVOS,
    REGISTRO_RISCOS,
    riscos_das_pernas_verdadeiras,
)
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    GHEContext,
    GHEVerbatim,
    Motivo,
    Quantificacao,
    Risco,
    RiscoPGR,
    RiscoVerbatim,
    TipoIBE,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 29)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _ghe(riscos: tuple[RiscoPGR, ...]) -> GHEPGR:
    return GHEPGR(
        id="GHE-11",
        nome="INSTALAÇÕES HIDRO-SANITÁRIAS",
        cargos=("Encanador",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _motivo(proto: Protocolo, regra_id: str, *riscos: RiscoPGR) -> Motivo:
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(_ghe(riscos),))
    (matriz,) = processar_pgr(pgr, proto, hoje=_HOJE).matrizes
    return next(m for linha in matriz.linhas for m in linha.motivos if m.regra_id == regra_id)


def _risco(agente: str, nivel: str | None = "MODERADO", q: Quantificacao | None = None) -> RiscoPGR:
    return RiscoPGR(tipo="", agente=agente, quantificacao=q, severidade=None, nivel_risco=nivel)


def _agentes(m: Motivo) -> list[str]:
    return [o.agente for o in m.origens]


def test_aurora_ghe11_cli05_aponta_os_tres_solventes_moderados(proto: Protocolo) -> None:
    # Rota da hidratação real, termos como no PGR. Reversões que matam: filtro da
    # perna (b) sem o nível (o xileno BAIXO entraria); voltar `_risco_origem`
    # (R-CLI-05 composta sairia sem origem).
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    termos = (
        ("Ciclohexanona", "2 3 MODERADO"),
        ("Metiletilcetona (MEK)", "2 3 MODERADO"),
        ("Tetrahidrofurano", "2 3 MODERADO"),
        ("Xileno", "1 1 BAIXO"),
    )
    ghe = GHEVerbatim(
        nome="INSTALAÇÕES HIDRO-SANITÁRIAS",
        cargos=("Encanador",),
        riscos=tuple(
            RiscoVerbatim(agente=t, quantificacao="", fonte_geradora="", avaliacao_qualitativa=a)
            for t, a in termos
        ),
    )
    pgr, _ = hidratar_pgr([ghe], indice, date(2030, 1, 1), True)
    (matriz,) = processar_pgr(pgr, proto, hoje=_HOJE).matrizes
    cli05 = next(m for linha in matriz.linhas for m in linha.motivos if m.regra_id == "R-CLI-05")

    assert _agentes(cli05) == ["ciclohexanona", "metil_etil_cetona", "tetrahidrofurano"]
    assert {o.perna for o in cli05.origens} == {"agente_ibe_moderado_ou_acima"}
    assert cli05.risco_origem == (
        "ciclohexanona ← PGR (nível MODERADO) + metil_etil_cetona ← PGR (nível MODERADO)"
        " + tetrahidrofurano ← PGR (nível MODERADO)"
    )


def test_ou_com_duas_pernas_verdadeiras_traz_as_duas(proto: Protocolo) -> None:
    # R-AUD-01 = ou(ruido_acima_acao, motorista_equipamento_pesado, ototoxico).
    # Reversão que mata: parar no primeiro filho True do `ou` — o tolueno sumiria.
    m = _motivo(proto, "R-AUD-01", _risco("motorista_equipamento_pesado"), _risco("tolueno"))

    assert [(o.perna, o.agente) for o in m.origens] == [
        ("motorista_equipamento_pesado", "motorista_equipamento_pesado"),
        ("ototoxico", "tolueno"),
    ]


def test_perna_ausente_absorvida_nao_vira_origem(proto: Protocolo) -> None:
    # Ruído sem laudo é Ausente, absorvido pela perna ototóxica (D-ARQ-71). A regra
    # emitiu por perna verdadeira, não por presunção. Reversão que mata: aceitar
    # folha Ausente sem exigir `expr in presumidos` — o ruído entraria presumido.
    m = _motivo(proto, "R-AUD-01", _risco("ruido"), _risco("tolueno"))

    assert [(o.agente, o.presumida) for o in m.origens] == [("tolueno", False)]


def test_perna_presumida_sai_marcada(proto: Protocolo) -> None:
    # D-ARQ-88 Q1: R-AUD-01 emitida só por presunção protetiva do ruído sem laudo
    # (D-ARQ-68 cl.5). Reversão que mata: não repassar `primitivos_presumidos` a
    # `_emitir_regra` no ramo presumido — a origem sairia vazia.
    m = _motivo(proto, "R-AUD-01", _risco("ruido"))

    assert [(o.perna, o.agente, o.presumida) for o in m.origens] == [
        ("ruido_acima_acao", "ruido", True)
    ]
    assert m.risco_origem == "ruido ← PGR (nível MODERADO) [presumido: ruido_acima_acao]"


def test_composto_nomeado_e_expandido(proto: Protocolo) -> None:
    # R-PKG-ATIVCRIT cita `atividade_critica` pelo nome. Reversão que mata: não
    # descer em `protocolo.predicados_compostos` — a origem sairia vazia.
    m = _motivo(proto, "R-PKG-ATIVCRIT", _risco("trabalho_altura"))

    assert [(o.perna, o.agente) for o in m.origens] == [("altura", "trabalho_altura")]


def test_e_verdadeiro_traz_todas_as_pernas(proto: Protocolo) -> None:
    # R-AUD-02 perna e(ruido, ototoxico, vibracao_qualquer), com ruído medido abaixo
    # do nível de ação (ruido_acima_acao False). Reversão que mata: o nó `e` não
    # descer nos filhos — a origem sairia vazia.
    abaixo = Quantificacao(valor=None, unidade=None, relacao_LT="abaixo_acao", pct_LT=None, apenas_qualitativa=False)
    m = _motivo(
        proto, "R-AUD-02", _risco("ruido", q=abaixo), _risco("tolueno"), _risco("vibracao_mao_braco")
    )

    assert _agentes(m) == ["ruido", "tolueno", "vibracao_mao_braco"]


def test_faixa_de_leo_so_com_asbesto_aponta_o_asbesto(proto: Protocolo) -> None:
    # O helper de sílica/asbesto lê o primeiro dos dois; a origem é esse risco.
    # Reversão que mata: registrar os riscos das faixas `silica_asbesto_leo_*` por
    # `r.agente == "silica"` (o antigo `_AGENTE_DA_FAIXA`) — sairia sem origem.
    medido = Quantificacao(valor=None, unidade=None, relacao_LT=None, pct_LT=5.0, apenas_qualitativa=False)
    m = _motivo(proto, "R-RX-01-adm", _risco("asbesto", q=medido))

    assert _agentes(m) == ["asbesto"]


def test_passada_nao_muda_o_cache_de_predicados(proto: Protocolo) -> None:
    # D-ARQ-88 cl.2. Reversão que mata: avaliar sobre o `ctx` recebido em vez da
    # cópia — o cache ganharia as pernas avaliadas e `predicados_avaliados` mudaria.
    ctx = GHEContext(
        pgr_ghe=_ghe(()),
        riscos=[Risco("tolueno", "explicito", None, None, TipoIBE.EE, is_ototoxico=True)],
    )
    regra = next(r for r in proto.regras if r["id"] == "R-AUD-01")

    pernas = riscos_das_pernas_verdadeiras(regra["quando"], ctx, proto)

    assert [p.risco.agente for p in pernas] == ["tolueno"]
    assert ctx.predicados == {}


def test_todo_primitivo_declara_riscos_ou_e_sem_risco() -> None:
    # D-ARQ-88 cl.3 (molde D-ARQ-67). Reversão que mata: tirar `riscos=` de um
    # `@primitivo` (ex.: `ruido_acima_acao`) — ele ficaria sem declaração.
    sem_declaracao = set(REGISTRO_PRIMITIVOS) - set(REGISTRO_RISCOS) - PRIMITIVOS_SEM_RISCO
    ambos = set(REGISTRO_RISCOS) & PRIMITIVOS_SEM_RISCO

    assert sem_declaracao == set()
    assert ambos == set()
    assert PRIMITIVOS_SEM_RISCO <= set(REGISTRO_PRIMITIVOS)


def _contextos(proto: Protocolo) -> list[GHEContext]:
    ctxs = []
    for slug, meta in proto.vocabulario.agentes.items():
        tipo_ibe = TipoIBE(meta["tipo_ibe"]) if meta.get("tipo_ibe") else None
        for q in (
            None,
            Quantificacao(valor=None, unidade=None, relacao_LT="acima_LT", pct_LT=None, apenas_qualitativa=False),
            Quantificacao(valor=None, unidade=None, relacao_LT=None, pct_LT=60.0, apenas_qualitativa=False),
        ):
            risco = Risco(
                slug, "explicito", None, q, tipo_ibe,
                is_ototoxico=bool(meta.get("is_ototoxico", False)), nivel_risco="MODERADO",
            )
            ctxs.append(GHEContext(pgr_ghe=_ghe(()), riscos=[risco]))
    return ctxs


def test_primitivo_verdadeiro_sempre_tem_risco(proto: Protocolo) -> None:
    # Filtro e riscos não divergem (D-ARQ-88 Q4): em todo contexto de um agente do
    # vocabulário, primitivo True ⇒ lista de riscos não vazia. Reversão que mata:
    # declarar os riscos do ototóxico por `r.agente == "ototoxico"`.
    casos = 0
    for ctx in _contextos(proto):
        for nome, fn in REGISTRO_PRIMITIVOS.items():
            if nome in PRIMITIVOS_SEM_RISCO or fn(ctx) is not True:
                continue
            casos += 1
            assert REGISTRO_RISCOS[nome](ctx), (nome, ctx.riscos[0].agente)
    assert casos > 0
