"""B.2 — plug resolve_leo em _helper_silica_asbesto (D-ARQ-24).
Padrão de montagem idêntico a _ctx_com_agente de test_rx_periodicidade.py.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import (
    CenarioExposicao,
    Fracao,
    GHEContext,
    GHEPGR,
    PGR,
    Quantificacao,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _ctx_silica(
    quantificacao: Quantificacao, cenario: CenarioExposicao | None = None
) -> tuple[GHEContext, Protocolo]:
    proto = _proto()
    risco_pgr = RiscoPGR(tipo="quimico", agente="silica", quantificacao=quantificacao, severidade=None)
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste B2",
        cargos=(),
        riscos=(risco_pgr,),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
        cenario=cenario,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return ctx, proto


def _pgr_silica(
    quantificacao: Quantificacao, cenario: CenarioExposicao | None = None
) -> tuple[PGR, Protocolo]:
    proto = _proto()
    risco_pgr = RiscoPGR(tipo="quimico", agente="silica", quantificacao=quantificacao, severidade=None)
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste B2",
        cargos=(),
        riscos=(risco_pgr,),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
        cenario=cenario,
    )
    pgr = PGR(validade=date.today(), assinatura_engenheiro=True, ghes=(ghe,))
    return pgr, proto


# ---------------------------------------------------------------------------
# Teste A — fração decide a faixa (falha sem o campo fracao, passa com)
# ---------------------------------------------------------------------------
# Valores ancorados em test_leo_resolver.py (pct_quartzo=10.0, cenário=GERAL):
#   RESPIRAVEL: LEO = 8.0 / (10 + 2) = 8/12 ≈ 0.6667 mg/m³
#   TOTAL:      LEO = 24.0 / (10 + 3) = 24/13 ≈ 1.8462 mg/m³
# Com valor=0.5 mg/m³:
#   pct_LT(RESP)  = 0.5 / (8/12)  * 100 = 75.0%   → faixa 50_100 → 36M/24M
#   pct_LT(TOTAL) = 0.5 / (24/13) * 100 ≈ 27.08%  → faixa 10_50  → 60M/36M
#   Borda cruzada: 75 > 50 e 27 < 50 → faixas distintas.

def test_fracao_decide_faixa_rx() -> None:
    # (i) pct_LT resolvidos, conta documentada
    leo_resp  = 8.0  / (10.0 + 2)   # NR-15 Anexo 12 respirável
    leo_total = 24.0 / (10.0 + 3)   # NR-15 Anexo 12 total
    pct_lt_resp  = (0.5 / leo_resp)  * 100.0   # ≈ 75.0%
    pct_lt_total = (0.5 / leo_total) * 100.0   # ≈ 27.08%
    assert pct_lt_resp  == pytest.approx(75.0)
    assert pct_lt_total == pytest.approx(100.0 * 0.5 * 13.0 / 24.0, rel=1e-3)

    # (ii) cruzam a borda 50 → faixas distintas
    assert pct_lt_resp  > 50.0
    assert pct_lt_total < 50.0

    q_resp = Quantificacao(
        valor=0.5, unidade="mg/m³", relacao_LT=None,
        pct_LT=None, apenas_qualitativa=False,
        pct_quartzo=10.0, fracao=Fracao.RESPIRAVEL,
    )
    q_total = Quantificacao(
        valor=0.5, unidade="mg/m³", relacao_LT=None,
        pct_LT=None, apenas_qualitativa=False,
        pct_quartzo=10.0, fracao=Fracao.TOTAL,
    )

    ctx_resp, proto = _ctx_silica(q_resp)
    ctx_total, _    = _ctx_silica(q_total)

    exames_resp  = stage_5_emissao(ctx_resp,  proto)
    exames_total = stage_5_emissao(ctx_total, proto)

    rx_resp  = next(e for e in exames_resp  if e.exame == "rx_torax_oit")
    rx_total = next(e for e in exames_total if e.exame == "rx_torax_oit")

    # (iii) periodicidades distintas: 50_100 → 36M/24M; 10_50 → 60M/36M
    assert rx_resp.periodicidade_meses    == 36   # faixa 50_100
    assert rx_resp.periodicidade_apos_15a == 24
    assert rx_total.periodicidade_meses    == 60  # faixa 10_50
    assert rx_total.periodicidade_apos_15a == 36
    assert rx_resp.periodicidade_meses != rx_total.periodicidade_meses


# ---------------------------------------------------------------------------
# Teste B — fração ausente → Pendência bloqueante (status PRELIMINAR)
# ---------------------------------------------------------------------------

def test_fracao_ausente_gera_pendencia_bloqueante() -> None:
    q = Quantificacao(
        valor=0.5, unidade="mg/m³", relacao_LT=None,
        pct_LT=None, apenas_qualitativa=False,
        pct_quartzo=10.0, fracao=None,
    )
    pgr, proto = _pgr_silica(q)
    resultado = executar(pgr, proto, hoje=date.today())

    # (i) nenhuma linha de RX emitida para o GHE
    assert len(resultado.matrizes) == 1
    assert resultado.matrizes[0].linhas == []

    # (ii) Pendencia(bloqueante=True) presente no Resultado
    bloqueantes = [p for m in resultado.matrizes for p in m.pendencias if p.bloqueante]
    assert bloqueantes, "Deve haver pendência bloqueante quando fracao=None"
    assert any("fração" in p.motivo or "fracao" in p.motivo for p in bloqueantes)

    # (iii) orquestrador.py linha 78: houve_bloqueio → status "PRELIMINAR"
    assert resultado.status == "PRELIMINAR"


# ---------------------------------------------------------------------------
# Teste C — sílica/mineração/TOTAL → LEO indefinido → Pendência bloqueante
# ---------------------------------------------------------------------------

def test_silica_mineracao_total_leo_indefinido_bloqueante() -> None:
    cenario = CenarioExposicao(cnae="07.10-3", atividade=None, local=None)  # MINERACAO
    q = Quantificacao(
        valor=0.5, unidade="mg/m³", relacao_LT=None,
        pct_LT=None, apenas_qualitativa=False,
        pct_quartzo=10.0, fracao=Fracao.TOTAL,
    )
    pgr, proto = _pgr_silica(q, cenario=cenario)
    resultado = executar(pgr, proto, hoje=date.today())

    # nenhuma linha de RX emitida
    assert resultado.matrizes[0].linhas == []

    # pendência bloqueante com mensagem de LEO indefinido
    bloqueantes = [p for m in resultado.matrizes for p in m.pendencias if p.bloqueante]
    assert bloqueantes
    assert any("indefinido" in p.motivo.lower() for p in bloqueantes)

    # orquestrador.py linha 78: houve_bloqueio → "PRELIMINAR"
    assert resultado.status == "PRELIMINAR"
