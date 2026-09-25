"""D-ARQ-86 fatia 2 — medição de sílica e PNOS informada na tela decide a faixa
de R-RX-01 (NR-07 Anexo III, Quadros 1 e 2; LT da sílica pela NR-15 Anexo 12).
Asbesto fora (decisão do Diovanni, 25/09/2026). Cada teste nomeia a reversão
de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.medicoes import aplicar_medicoes
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    ExameEmitido,
    Fracao,
    MedicaoInformada,
    Pendencia,
    ProcedenciaMedicao,
    Quantificacao,
    RiscoPGR,
)
from agente_medico.superficie.web_matriz import agentes_mensuraveis, pagina_matriz

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_LAUDO = ProcedenciaMedicao(origem="informada", laudo="L-07", data=date(2026, 5, 10))


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _pgr(*riscos: RiscoPGR) -> PGR:
    ghe = GHEPGR(
        id="GHE-03",
        nome="ARMAÇÃO",
        cargos=("Armador",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))


def _risco(agente: str, q: Quantificacao | None = None) -> RiscoPGR:
    return RiscoPGR(tipo="Químico", agente=agente, quantificacao=q, severidade=None, nivel_risco="BAIXO")


def _silica(valor: float, fracao: Fracao = Fracao.RESPIRAVEL, quartzo: float = 8.0) -> MedicaoInformada:
    return MedicaoInformada("GHE-03", "silica", valor, "mg/m3", _LAUDO, fracao, quartzo)


def _rx(proto: Protocolo, pgr: PGR, *medicoes: MedicaoInformada) -> ExameEmitido:
    pgr_medido, _ = aplicar_medicoes(pgr, medicoes, proto.vocabulario.agentes)
    matriz = processar_pgr(pgr_medido, proto).matrizes[0]
    return next(e for e in matriz.linhas if e.exame == "rx_torax_oit")


def test_silica_medida_a_30_por_cento_do_leo_da_rx_de_60_meses(proto: Protocolo) -> None:
    # 0,24 mg/m³ respirável com 8% de quartzo: LT = 8/(8+2) = 0,8 mg/m³ → 30%.
    # Sem medição sairia 12M (R-RX-01-qual). Reversão que mata: _quantificacao de
    # medicoes.py não repassar pct_quartzo/fracao — o helper de R-RX-01 não
    # resolve o LEO e a faixa medida não sai.
    rx = _rx(proto, _pgr(_risco("silica")), _silica(0.24))

    assert (rx.periodicidade_meses, rx.motivos[0].regra_id) == (60, "R-RX-01-baixa")


def test_fracao_total_usa_a_formula_da_poeira_total(proto: Protocolo) -> None:
    # 1,5 mg/m³ total, 8% quartzo: LT total = 24/(8+3) = 2,18 → 69% → 36M. Pela
    # fórmula respirável (0,8) seriam 188% → 12M. Reversão que mata:
    # _quantificacao fixar Fracao.RESPIRAVEL em vez de usar medicao.fracao.
    rx = _rx(proto, _pgr(_risco("silica")), _silica(1.5, Fracao.TOTAL))

    assert (rx.periodicidade_meses, rx.motivos[0].regra_id) == (36, "R-RX-01-media")


def test_origem_do_rx_mostra_a_medicao_e_o_laudo(proto: Protocolo) -> None:
    # D-ARQ-86 cl.3. Reversão que mata: tirar _AGENTE_DA_FAIXA de _risco_origem —
    # a faixa decidida pela medição ficaria sem origem na revisão.
    rx = _rx(proto, _pgr(_risco("silica")), _silica(0.24))

    assert rx.motivos[0].risco_origem == (
        "silica ← PGR (nível BAIXO); medição 0,24 mg/m³ (laudo L-07, 10/05/2026)"
    )


def test_pnos_medido_sai_da_faixa_sem_medicao(proto: Protocolo) -> None:
    # 0,9 mg/m³ = 30% do LEO de 3 mg/m³ (ACGIH via NR-09 9.6.1.1) → Quadro 2,
    # faixa 10–100%: só admissional. Sem medição: adm + 60M. Reversão que mata:
    # tirar as faixas pnos_leo_* de _AGENTE_DA_FAIXA — a faixa medida sairia sem
    # a medição na origem da revisão.
    sem = _rx(proto, _pgr(_risco("poeira_nao_classificada")))
    com = _rx(
        proto,
        _pgr(_risco("poeira_nao_classificada")),
        MedicaoInformada("GHE-03", "poeira_nao_classificada", 0.9, "mg/m3", _LAUDO, Fracao.RESPIRAVEL),
    )

    assert sem.motivos[0].regra_id == "R-RX-01-pnos-sem"
    assert com.motivos[0].regra_id == "R-RX-01-pnos-10a100"
    assert com.motivos[0].risco_origem == (
        "poeira_nao_classificada ← PGR (nível BAIXO); medição 0,9 mg/m³ (laudo L-07, 10/05/2026)"
    )


def test_divergencia_de_silica_fica_com_o_maior_percentual(proto: Protocolo) -> None:
    # PGR: 0,5 mg/m³ resp com 8% quartzo (62,5%); laudo informado: 0,1 (12,5%).
    # Reversão que mata: _pct de medicoes.py sem o ramo pct_leo_poeira — sem % para
    # comparar, ficaria o valor informado, mais baixo.
    do_pgr = Quantificacao(0.5, "mg/m3", None, None, False, pct_quartzo=8.0, fracao=Fracao.RESPIRAVEL)
    pgr, pendencias = aplicar_medicoes(
        _pgr(_risco("silica", do_pgr)), (_silica(0.1),), proto.vocabulario.agentes
    )

    assert pgr.ghes[0].riscos[0].quantificacao == do_pgr
    assert [p.tipo for p in pendencias] == ["medicao_divergente"]


def test_tela_oferece_silica_e_pnos_e_nao_asbesto(proto: Protocolo) -> None:
    # Reversão que mata: tirar sílica ou PNOS de AGENTES_POEIRA_MEDIVEIS, ou pôr
    # asbesto (o resolver não tem o LEO dele — medição sem efeito).
    pgr = _pgr(
        _risco("silica"),
        _risco("poeira_nao_classificada"),
        _risco("asbesto"),
        _risco("xileno"),
        _risco("ruido"),
    )

    assert agentes_mensuraveis(pgr, "GHE-03", proto) == {
        "silica": ("mg/m3",),
        "poeira_nao_classificada": ("mg/m3",),
        "xileno": ("ppm", "mg/m3"),
    }


def _pagina_com_silica(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    pgr = _pgr(_risco("silica"))

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    at.text_input[len(at.text_input) - 1].set_value("2026-12-31").run()
    at.checkbox[0].set_value(True).run()
    at.button[0].click().run()
    at.run()
    assert not at.exception
    at.number_input(key="medicao_valor").set_value(0.24)
    at.text_input(key="medicao_laudo").set_value("L-07")
    return at


def test_tela_registra_silica_com_fracao_e_quartzo(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: o callback ignorar "medicao_fracao" (fixar respirável) —
    # a medição total entraria com a fórmula errada.
    at = _pagina_com_silica(monkeypatch)
    at.selectbox(key="medicao_fracao").set_value(Fracao.TOTAL.value)
    at.number_input(key="medicao_quartzo").set_value(8.0)
    at.button(key="registrar_medicao").click().run()
    assert not at.exception

    (medicao,) = at.session_state["web_matriz_cache"].medicoes
    assert (medicao.agente, medicao.fracao, medicao.pct_quartzo) == ("silica", Fracao.TOTAL, 8.0)


def test_tela_recusa_silica_sem_quartzo(monkeypatch: pytest.MonkeyPatch) -> None:
    # Sem %quartzo não há LT (NR-15 Anexo 12). Reversão que mata: tirar a checagem
    # de pct_quartzo de _registrar_medicao — a medição entraria e o RX cairia em
    # pendência de LEO indefinido.
    at = _pagina_com_silica(monkeypatch)
    at.button(key="registrar_medicao").click().run()

    assert at.session_state["web_matriz_cache"].medicoes == ()
    assert [w.value for w in at.warning] == ["Sílica: informe o % de quartzo do laudo (NR-15 Anexo 12)."]
