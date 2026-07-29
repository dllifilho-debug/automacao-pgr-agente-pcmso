# R-ESP-02 / NR-07 Anexo III item 3.1 (Portaria MTP 567/2022) [DERIVADO — 003.EI].
# Espirometria por exposição a poeira mineral (sílica/asbesto/PNOS): 24M em
# [adm, per, MR, dem], sem depender de quantificação — o item 3.1 não roteia por faixa.
from __future__ import annotations

from pathlib import Path

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEContext, GHEPGR, Momento, Quantificacao, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _ctx_com_agente(agente: str | None, quantificacao: Quantificacao | None = None) -> tuple[GHEContext, Protocolo]:
    proto = _proto()
    riscos = () if agente is None else (
        RiscoPGR(tipo="quimico", agente=agente, quantificacao=quantificacao, severidade=None),
    )
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste Espirometria",
        cargos=(),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return ctx, proto


_MOMENTOS_ESPERADOS = {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}


# ---------------------------------------------------------------------------
# Cada perna do composto poeira_mineral (silica / asbesto / pnos) + negativo
# ---------------------------------------------------------------------------

def test_espirometria_silica_emite_24m_todos_momentos() -> None:
    ctx, proto = _ctx_com_agente("silica")
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert esp.periodicidade_apos_15a is None
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)
    assert any(m.regra_id == "R-ESP-02" for m in esp.motivos)


def test_espirometria_asbesto_emite_24m_todos_momentos() -> None:
    ctx, proto = _ctx_com_agente("asbesto")
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert esp.periodicidade_apos_15a is None
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)


def test_espirometria_pnos_emite_24m_todos_momentos() -> None:
    ctx, proto = _ctx_com_agente("poeira_nao_classificada")
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert esp.periodicidade_apos_15a is None
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)


def test_espirometria_sem_poeira_mineral_nao_emite() -> None:
    ctx, proto = _ctx_com_agente(None)
    exames = stage_5_emissao(ctx, proto)
    esp_list = [e for e in exames if e.exame == "espirometria"]
    assert esp_list == [], f"Sem poeira mineral não deveria emitir espirometria: {esp_list}"


# ---------------------------------------------------------------------------
# Item 3.1 não roteia por faixa: emissão independe de quantificação — contraste
# deliberado com R-RX-01 (que ali roteia por R-RX-01-sem).
# ---------------------------------------------------------------------------

def test_espirometria_silica_sem_quantificacao_emite_normalmente() -> None:
    ctx, proto = _ctx_com_agente("silica", quantificacao=None)
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)


# ---------------------------------------------------------------------------
# Emenda do Arquiteto (retomada 003.EI): assimetria RX x espirometria no mesmo
# GHE quando a medição de sílica é incompleta (valor sem pct_quartzo/fracao) —
# ramo (d) de _helper_silica_asbesto. D-ARQ-31: bloqueio é por-risco/por-linha,
# não se propaga entre exames do mesmo risco. Não é bug: o item 3.1 não roteia
# por faixa, logo não há gate de quantificação para a espirometria bloquear.
# ---------------------------------------------------------------------------

def test_espirometria_emite_mesmo_com_rx_bloqueado_por_medicao_incompleta() -> None:
    q_incompleta = Quantificacao(
        valor=0.05,
        unidade="mg/m³",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        sem_avaliacao_quantitativa=False,
        pct_quartzo=None,
    )
    ctx, proto = _ctx_com_agente("silica", q_incompleta)
    exames = stage_5_emissao(ctx, proto)

    rx_list = [e for e in exames if e.exame == "rx_torax_oit"]
    assert rx_list == [], "Medição não roteável (sem pct_quartzo) não deve emitir rx_torax_oit"
    bloqueantes = [p for p in ctx.pendencias if p.bloqueante]
    assert bloqueantes, "Deve haver pendência bloqueante do RX"

    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)
