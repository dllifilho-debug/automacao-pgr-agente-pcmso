from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.predicados import REGISTRO_PRIMITIVOS
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    Ausente,
    GHEContext,
    GHEPGR,
    Momento,
    PGR,
    Quantificacao,
    Risco,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

HOJE = date(2026, 5, 21)


def _ghe(ghe_id: str = "GHE-01") -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome="Teste",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _ctx(*agentes: str) -> GHEContext:
    riscos = [
        Risco(agente=a, fonte="pgr", detalhe=None, quantificacao=None, anexo_nr07=None)
        for a in agentes
    ]
    return GHEContext(pgr_ghe=_ghe(), riscos=riscos)


def _ctx_ruido_quant(relacao_LT: str) -> GHEContext:
    q = Quantificacao(
        valor=90.0, unidade="dB(A)", relacao_LT=relacao_LT,
        pct_LT=None, apenas_qualitativa=False,
    )
    risco = Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, anexo_nr07=None)
    return GHEContext(pgr_ghe=_ghe(), riscos=[risco])


def _ctx_ruido_quant_e_vci(relacao_LT: str) -> GHEContext:
    q = Quantificacao(
        valor=90.0, unidade="dB(A)", relacao_LT=relacao_LT,
        pct_LT=None, apenas_qualitativa=False,
    )
    return GHEContext(pgr_ghe=_ghe(), riscos=[
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, anexo_nr07=None),
        Risco(agente="vibracao_corpo_inteiro", fonte="pgr", detalhe=None, quantificacao=None, anexo_nr07=None),
    ])


def _quant_acima_acao() -> Quantificacao:
    return Quantificacao(
        valor=90.0, unidade="dB(A)", relacao_LT="acima_acao",
        pct_LT=None, apenas_qualitativa=False,
    )


def _pgr_com_riscos(ghe_id: str, riscos_pgr: tuple[RiscoPGR, ...]) -> PGR:
    ghe = GHEPGR(
        id=ghe_id,
        nome="Teste",
        cargos=(),
        riscos=riscos_pgr,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    return PGR(
        validade=HOJE - timedelta(days=30),
        assinatura_engenheiro=True,
        ghes=(ghe,),
    )


def _risco_pgr(agente: str, quant: Optional[Quantificacao] = None) -> RiscoPGR:
    return RiscoPGR(tipo="fisico", agente=agente, quantificacao=quant, severidade=None)


# ---------------------------------------------------------------------------
# Testes 1-4: Primitivo vibracao_corpo_inteiro
# ---------------------------------------------------------------------------

def test_primitivo_vci_risco_vci_retorna_true() -> None:
    result = REGISTRO_PRIMITIVOS["vibracao_corpo_inteiro"](_ctx("vibracao_corpo_inteiro"))
    assert result is True


def test_primitivo_vci_risco_vibracao_generico_retorna_ausente() -> None:
    result = REGISTRO_PRIMITIVOS["vibracao_corpo_inteiro"](_ctx("vibracao"))
    assert isinstance(result, Ausente)


def test_primitivo_vci_risco_mao_braco_retorna_false() -> None:
    result = REGISTRO_PRIMITIVOS["vibracao_corpo_inteiro"](_ctx("vibracao_mao_braco"))
    assert result is False


def test_primitivo_vci_sem_vibracao_retorna_false() -> None:
    result = REGISTRO_PRIMITIVOS["vibracao_corpo_inteiro"](_ctx())
    assert result is False


# ---------------------------------------------------------------------------
# Testes 5-6: R-VIB-01 via stage_5_emissao
# ---------------------------------------------------------------------------

def test_rvib01_vci_emite_rx_coluna_momentos_adm_mr() -> None:
    ctx = _ctx("vibracao_corpo_inteiro")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    slugs = {e.exame for e in result}
    assert "rx_coluna_lombo_sacra" in slugs
    rx = next(e for e in result if e.exame == "rx_coluna_lombo_sacra")
    assert rx.momentos == {Momento.ADM, Momento.MR}
    assert rx.motivos[0].regra_id == "R-VIB-01"
    assert ctx.pendencias == []


def test_rvib01_vibracao_generica_sem_emissao_com_pendencia_bloqueante() -> None:
    ctx = _ctx("vibracao")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert result == []
    # R-VIB-01 e R-VIB-02 ambos usam vibracao_corpo_inteiro → 2 pendências bloqueantes
    assert len(ctx.pendencias) == 2
    assert all(p.bloqueante for p in ctx.pendencias)
    assert all(p.tipo == "predicado_ausente" for p in ctx.pendencias)
    assert any(p.regra_origem == "R-VIB-01" for p in ctx.pendencias)
    assert any(p.regra_origem == "R-VIB-02" for p in ctx.pendencias)
    assert all(p.ghe_id == "GHE-01" for p in ctx.pendencias)


# ---------------------------------------------------------------------------
# Testes 7-8: R-AUD-01
# ---------------------------------------------------------------------------

def test_raud01_ruido_acima_acao_emite_audiometria_adm_per_mr() -> None:
    ctx = _ctx_ruido_quant("acima_acao")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert any(e.exame == "audiometria" for e in result)
    audio = next(e for e in result if e.exame == "audiometria")
    assert Momento.ADM in audio.momentos
    assert Momento.PER in audio.momentos
    assert Momento.MR in audio.momentos
    assert audio.periodicidade_meses == 12
    assert ctx.pendencias == []


def test_raud01_ruido_sem_quantificacao_gera_pendencia_bloqueante() -> None:
    ctx = _ctx("ruido")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert result == []
    assert any(p.bloqueante and p.regra_origem == "R-AUD-01" for p in ctx.pendencias)


# ---------------------------------------------------------------------------
# Testes 9-10: R-VIB-02
# ---------------------------------------------------------------------------

def test_rvib02_vci_sozinho_emite_audiometria() -> None:
    ctx = _ctx("vibracao_corpo_inteiro")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert any(e.exame == "audiometria" for e in result)


def test_rvib02_vci_com_ruido_abaixo_acao_ainda_emite_audiometria() -> None:
    ctx = _ctx_ruido_quant_e_vci("abaixo_acao")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert any(e.exame == "audiometria" for e in result)
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Testes 11-13: Integração via executar()
# ---------------------------------------------------------------------------

def test_execucao_vci_e_ruido_acima_acao_status_ok_com_rx_e_audiometria() -> None:
    pgr = _pgr_com_riscos("GHE-01", (
        _risco_pgr("vibracao_corpo_inteiro"),
        _risco_pgr("ruido", _quant_acima_acao()),
    ))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    slugs = {e.exame for e in matriz.linhas}
    assert "rx_coluna_lombo_sacra" in slugs
    assert "audiometria" in slugs
    audio = next(e for e in matriz.linhas if e.exame == "audiometria")
    assert audio.periodicidade_meses == 12


def test_execucao_vibracao_generica_status_preliminar_linhas_vazias() -> None:
    pgr = _pgr_com_riscos("GHE-01", (_risco_pgr("vibracao"),))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "PRELIMINAR"
    matriz = resultado.matrizes[0]
    assert matriz.linhas == []


# ---------------------------------------------------------------------------
# Testes 14-15: motorista_equipamento_pesado dispara R-AUD-01
# ---------------------------------------------------------------------------

def test_raud01_motorista_equipamento_pesado_emite_audiometria_adm_per_mr() -> None:
    ctx = _ctx("motorista_equipamento_pesado")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert any(e.exame == "audiometria" for e in result)
    audio = next(e for e in result if e.exame == "audiometria")
    assert Momento.ADM in audio.momentos
    assert Momento.PER in audio.momentos
    assert Momento.MR in audio.momentos
    assert audio.periodicidade_meses == 12
    assert any(m.regra_id == "R-AUD-01" for m in audio.motivos)
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Testes 16: R-VIB-02 dispara com vibracao_mao_braco sozinho
# ---------------------------------------------------------------------------

def test_rvib02_vmb_sozinho_emite_audiometria() -> None:
    ctx = _ctx("vibracao_mao_braco")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert any(e.exame == "audiometria" for e in result)
    audio = next(e for e in result if e.exame == "audiometria")
    assert any(m.regra_id == "R-VIB-02" for m in audio.motivos)
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Testes de integração (continuação)
# ---------------------------------------------------------------------------

def test_execucao_dedup_audiometria_tres_motivos_sem_conflito() -> None:
    pgr = _pgr_com_riscos("GHE-01", (
        _risco_pgr("trabalho_altura"),
        _risco_pgr("ruido", _quant_acima_acao()),
    ))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    audios = [e for e in matriz.linhas if e.exame == "audiometria"]
    assert len(audios) == 1
    audio = audios[0]
    assert audio.periodicidade_meses == 12
    regras_motivos = [m.regra_id for m in audio.motivos]
    assert "R-PKG-ATIVCRIT" in regras_motivos
    assert "R-AUD-01" in regras_motivos
    assert "R-AUD-02" in regras_motivos
    assert len(regras_motivos) == 3
    audio_momentos = audio.momentos
    assert Momento.DEM in audio_momentos


# ---------------------------------------------------------------------------
# Testes 17-22: gatilho ototóxico (002.H)
# ---------------------------------------------------------------------------

def _risco_ototoxico(agente: str = "tolueno") -> Risco:
    return Risco(
        agente=agente, fonte="pgr", detalhe=None,
        quantificacao=None, anexo_nr07=None, is_ototoxico=True,
    )


def test_primitivo_ototoxico_com_risco_ototoxico_retorna_true() -> None:
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[_risco_ototoxico()])
    assert REGISTRO_PRIMITIVOS["ototoxico"](ctx) is True


def test_primitivo_ototoxico_sem_ototoxico_retorna_false() -> None:
    assert REGISTRO_PRIMITIVOS["ototoxico"](_ctx("ruido")) is False


def test_raud01_ototoxico_isolado_emite_audiometria_adm_per_mr() -> None:
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[_risco_ototoxico()])
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    audio = next(e for e in result if e.exame == "audiometria")
    assert {Momento.ADM, Momento.PER, Momento.MR} <= audio.momentos
    assert Momento.DEM not in audio.momentos
    assert audio.periodicidade_meses == 12
    assert any(m.regra_id == "R-AUD-01" for m in audio.motivos)
    assert ctx.pendencias == []


def test_raud02_ruido_abaixo_ototoxico_vibracao_emite_demissional_via_branch_composto() -> None:
    q = Quantificacao(
        valor=80.0, unidade="dB(A)", relacao_LT="abaixo_acao",
        pct_LT=None, apenas_qualitativa=False,
    )
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, anexo_nr07=None),
        _risco_ototoxico(),
        Risco(agente="vibracao_mao_braco", fonte="pgr", detalhe=None, quantificacao=None, anexo_nr07=None),
    ])
    proto = carregar(_PROTOCOLO_DIR)
    # Garante que o demissional NÃO veio do ramo ruido_acima_acao do `ou`,
    # e sim do branch composto e:[ruido, ototoxico, vibracao_qualquer].
    assert REGISTRO_PRIMITIVOS["ruido_acima_acao"](ctx) is False
    result = stage_5_emissao(ctx, proto)
    dem = [e for e in result if e.exame == "audiometria" and Momento.DEM in e.momentos]
    assert dem
    assert any(m.regra_id == "R-AUD-02" for e in dem for m in e.motivos)
    assert ctx.pendencias == []


def test_raud02_vibracao_generica_com_ruido_e_ototoxico_bloqueia() -> None:
    # Branch e:[ruido, ototoxico, vibracao_qualquer] com vibracao sem qualificar tipo
    # → vibracao_qualquer=Ausente → branch=Ausente. Com ruido_acima_acao=False,
    # R-AUD-02 inteiro = Ausente → pendência bloqueante (D-ARQ-13/16).
    q = Quantificacao(
        valor=80.0, unidade="dB(A)", relacao_LT="abaixo_acao",
        pct_LT=None, apenas_qualitativa=False,
    )
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, anexo_nr07=None),
        _risco_ototoxico(),
        Risco(agente="vibracao", fonte="pgr", detalhe=None, quantificacao=None, anexo_nr07=None),
    ])
    proto = carregar(_PROTOCOLO_DIR)
    stage_5_emissao(ctx, proto)
    assert any(p.bloqueante and p.regra_origem == "R-AUD-02" for p in ctx.pendencias)


def test_execucao_ototoxico_via_agente_status_ok_sem_demissional() -> None:
    pgr = _pgr_com_riscos("GHE-01", (
        RiscoPGR(tipo="quimico", agente="tolueno", quantificacao=None, severidade=None),
    ))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    audio = next(e for e in matriz.linhas if e.exame == "audiometria")
    assert Momento.DEM not in audio.momentos
    assert any(m.regra_id == "R-AUD-01" for m in audio.motivos)
    assert all(p.tipo != "vocabulario_ausente" for p in matriz.pendencias)
