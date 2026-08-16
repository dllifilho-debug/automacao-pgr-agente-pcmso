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
from agente_medico.tests.invariantes import linhas_de_risco as _linhas_de_risco

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
        Risco(agente=a, fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None)
        for a in agentes
    ]
    return GHEContext(pgr_ghe=_ghe(), riscos=riscos)


def _ctx_ruido_quant(relacao_LT: str) -> GHEContext:
    q = Quantificacao(
        valor=90.0, unidade="dB(A)", relacao_LT=relacao_LT,
        pct_LT=None, apenas_qualitativa=False,
    )
    risco = Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, tipo_ibe=None)
    return GHEContext(pgr_ghe=_ghe(), riscos=[risco])


def _ctx_ruido_quant_e_vci(relacao_LT: str) -> GHEContext:
    q = Quantificacao(
        valor=90.0, unidade="dB(A)", relacao_LT=relacao_LT,
        pct_LT=None, apenas_qualitativa=False,
    )
    return GHEContext(pgr_ghe=_ghe(), riscos=[
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, tipo_ibe=None),
        Risco(agente="vibracao_corpo_inteiro", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
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
    assert _linhas_de_risco(result) == []
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


def test_raud01_ruido_sem_quantificacao_emite_sob_presuncao_nao_bloqueante() -> None:
    # Sucede test_raud01_ruido_sem_quantificacao_gera_pendencia_bloqueante
    # (D-ARQ-68 cl.5, 003.EZ): ruído sem quantificação deixou de bloquear puro —
    # R-AUD-01 declara presumir_true sobre ruido_acima_acao, emite audiometria
    # e anexa pendência não-bloqueante nomeando o primitivo presumido.
    ctx = _ctx("ruido")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert _linhas_de_risco(result) != []
    assert not any(p.bloqueante and p.regra_origem == "R-AUD-01" for p in ctx.pendencias)
    assert any(
        p.tipo == "predicado_ausente_presumido" and p.regra_origem == "R-AUD-01"
        for p in ctx.pendencias
    )


def test_raud01_motivo_predicado_serializa_expressao_composta() -> None:
    ctx = _ctx_ruido_quant("acima_acao")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    audio = next(e for e in result if e.exame == "audiometria")
    motivo = next(m for m in audio.motivos if m.regra_id == "R-AUD-01")
    assert motivo.predicado == "ou(ruido_acima_acao, motorista_equipamento_pesado, ototoxico)"
    assert motivo.predicado != "<composto>"


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


def test_execucao_vci_e_ruido_matriz_traz_diagnostico_riscos_e_predicados() -> None:
    pgr = _pgr_com_riscos("GHE-01", (
        _risco_pgr("vibracao_corpo_inteiro"),
        _risco_pgr("ruido", _quant_acima_acao()),
    ))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.riscos_resolvidos == ("ruido", "vibracao_corpo_inteiro")
    assert list(matriz.predicados_avaliados) == sorted(matriz.predicados_avaliados)
    assert ("vibracao_corpo_inteiro", "True") in matriz.predicados_avaliados
    assert ("ruido_acima_acao", "True") in matriz.predicados_avaliados


def test_execucao_vibracao_generica_status_preliminar_linhas_vazias() -> None:
    pgr = _pgr_com_riscos("GHE-01", (_risco_pgr("vibracao"),))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "PRELIMINAR"
    matriz = resultado.matrizes[0]
    assert _linhas_de_risco(matriz.linhas) == []


# ---------------------------------------------------------------------------
# Testes 14-15: motorista_equipamento_pesado dispara R-AUD-01
# ---------------------------------------------------------------------------

def test_raud01_motorista_equipamento_pesado_emite_audiometria_adm_per_mr() -> None:
    # 003.ED: motorista_equipamento_pesado entrou em atividade_critica.ou (substitui
    # o primitivo órfão maquina_pesada), então este risco sozinho agora dispara
    # também R-PKG-ATIVCRIT — resultado tem 2 linhas de audiometria pré-consolidação
    # (R-PKG-ATIVCRIT e R-AUD-01). Filtra pela linha de R-AUD-01 especificamente.
    ctx = _ctx("motorista_equipamento_pesado")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    audiometrias_raud01 = [
        e for e in result if e.exame == "audiometria" and any(m.regra_id == "R-AUD-01" for m in e.motivos)
    ]
    assert audiometrias_raud01
    audio = audiometrias_raud01[0]
    assert Momento.ADM in audio.momentos
    assert Momento.PER in audio.momentos
    assert Momento.MR in audio.momentos
    assert audio.periodicidade_meses == 12
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Testes 16: R-VIB-02 dispara com vibracao_mao_braco sozinho
# ---------------------------------------------------------------------------

def test_rvib02_vmb_sozinho_emite_audiometria() -> None:
    # 003.EZ: R-AUD-04 (piso incondicional) foi DEPRECATED (D-ARQ-81) — só
    # R-VIB-02 dispara audiometria para vibração mão-braço isolada, então
    # volta a existir uma única entrada "audiometria" pré-dedup (reverte a
    # busca em lista de 003.EX).
    ctx = _ctx("vibracao_mao_braco")
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    audio = next(e for e in result if e.exame == "audiometria")
    assert any(m.regra_id == "R-VIB-02" for m in audio.motivos)
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# Testes de integração (continuação)
# ---------------------------------------------------------------------------

def test_execucao_dedup_audiometria_tres_motivos_sem_conflito() -> None:
    # 003.EZ: R-AUD-04 foi DEPRECATED (D-ARQ-81) — a linha "audiometria" volta
    # a fundir só 3 motivos: R-PKG-ATIVCRIT (altura, adm/per/MR) + R-AUD-01
    # (ruído acima_acao, adm/per/MR) + R-AUD-02 (ruído acima_acao, dem).
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
        quantificacao=None, tipo_ibe=None, is_ototoxico=True,
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
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, tipo_ibe=None),
        _risco_ototoxico(),
        Risco(agente="vibracao_mao_braco", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
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
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=q, tipo_ibe=None),
        _risco_ototoxico(),
        Risco(agente="vibracao", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
    ])
    proto = carregar(_PROTOCOLO_DIR)
    stage_5_emissao(ctx, proto)
    assert any(p.bloqueante and p.regra_origem == "R-AUD-02" for p in ctx.pendencias)


def test_raud02_ruido_sem_quantificacao_com_vibracao_generica_e_ototoxico_bloqueia() -> None:
    # Teste 7: ruído sem quantificação (Ausente) + vibração não-qualificada
    # (Ausente) + ototóxico (True). R-AUD-02 = ou[ruido_acima_acao(Ausente),
    # e(ruido=True, ototoxico=True, vibracao_qualquer=Ausente)] — a perna `e`
    # também Ausente. pernas_ausentes coleta nomes além de 'ruido_acima_acao'
    # (a perna `e` e/ou 'vibracao_qualquer'), fora da allowlist de
    # presumir_true=[ruido_acima_acao] — bloqueia. Reversão que mata: trocar
    # "todos os nomes na lista" por "algum nome na lista" no guard de emissao.py.
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
        _risco_ototoxico(),
        Risco(agente="vibracao", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
    ])
    proto = carregar(_PROTOCOLO_DIR)
    result = stage_5_emissao(ctx, proto)
    assert not any(
        e.exame == "audiometria" and any(m.regra_id == "R-AUD-02" for m in e.motivos)
        for e in result
    )
    assert any(p.bloqueante and p.regra_origem == "R-AUD-02" for p in ctx.pendencias)


def test_raud01_raud02_ruido_sem_quantificacao_emite_12m_e_dem_na_mesma_linha() -> None:
    # Testes 4 e 5: GHE só com ruído sem quantificação. R-AUD-01 presume e
    # emite audiometria 12M [adm, per, MR]; R-AUD-02 presume e emite dem — a
    # mesma linha "audiometria" (pós-dedup) carrega os dois motivos e o
    # Momento.DEM. Reversões que matam: remover presumir_true de R-AUD-01
    # (teste 4) / de R-AUD-02 (teste 5) em regras.yaml.
    pgr = _pgr_com_riscos("GHE-01", (_risco_pgr("ruido"),))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    audio = next(e for e in matriz.linhas if e.exame == "audiometria")
    assert audio.periodicidade_meses == 12
    assert {Momento.ADM, Momento.PER, Momento.MR}.issubset(audio.momentos)
    regras_motivos = {m.regra_id for m in audio.motivos}
    assert "R-AUD-01" in regras_motivos  # teste 4
    assert "R-AUD-02" in regras_motivos
    assert Momento.DEM in audio.momentos  # teste 5


def test_raud01_raud02_sem_nenhum_risco_nao_emite_audiometria_matriz_bloqueada() -> None:
    # Teste 12: GHE sem risco relevante para audiometria (nenhum de ruído,
    # motorista_equipamento_pesado, ototóxico ou vibração) não recebe
    # audiometria — antes de D-ARQ-81, R-AUD-04 (piso incondicional) injetava
    # a linha em toda matriz independente de risco. Usa vibração genérica
    # (bloqueante, sem allowlist) só para tornar a matriz BLOQUEADA por motivo
    # não relacionado a audiometria, provando que a ausência de audiometria
    # não é efeito colateral de outro bloqueio. Reversão que mata:
    # reintroduzir R-AUD-04 ativa (status: VALIDADO) em regras.yaml.
    pgr = _pgr_com_riscos("GHE-01", (_risco_pgr("vibracao"),))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "audiometria" not in nomes
    assert matriz.status == "BLOQUEADA"


def test_execucao_ototoxico_via_agente_status_ok_sem_demissional() -> None:
    # 003.EZ: R-AUD-04 foi DEPRECATED (D-ARQ-81 — fundamento refutado por
    # DT-003EY-01), então "sem demissional" volta a ser verdade para ototóxico
    # isolado (sem ruído) — o nome ..._sem_r_aud_02 (EMENDA 3 / 003.EX) fica
    # supérfluo e volta ao nome original, que já cobria o invariante: R-AUD-02
    # (demissional condicionado a ruído/combinação) não dispara só por
    # ototóxico isolado.
    pgr = _pgr_com_riscos("GHE-01", (
        RiscoPGR(tipo="quimico", agente="tolueno", quantificacao=None, severidade=None),
    ))
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    audio = next(e for e in matriz.linhas if e.exame == "audiometria")
    regras_motivos = {m.regra_id for m in audio.motivos}
    assert "R-AUD-01" in regras_motivos
    assert "R-AUD-02" not in regras_motivos
    assert Momento.DEM not in audio.momentos
    assert all(p.tipo != "vocabulario_ausente" for p in matriz.pendencias)
