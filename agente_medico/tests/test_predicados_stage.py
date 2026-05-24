from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.predicados import REGISTRO_PRIMITIVOS, avaliar_predicado
from agente_medico.motor.protocolo import Protocolo, Vocabulario, carregar
from agente_medico.motor.tipos import Ausente, GHEContext, GHEPGR, Risco

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _ghe() -> GHEPGR:
    return GHEPGR(
        id="GHE-01",
        nome="Teste",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _ctx_altura() -> GHEContext:
    return GHEContext(
        pgr_ghe=_ghe(),
        riscos=[
            Risco(
                agente="trabalho_altura",
                fonte="explicito",
                detalhe=None,
                quantificacao=None,
                anexo_nr07=None,
            )
        ],
    )


def test_popula_primitivos_referenciados() -> None:
    ctx = _ctx_altura()
    proto = carregar(_PROTOCOLO_DIR)
    stage_4_predicados(ctx, proto)

    # altura=True dispara ou-curto-circuito: atividade_critica resolvida como True
    assert ctx.predicados["altura"] is True
    assert ctx.predicados["atividade_critica"] is True

    # R-AUD-01 referencia ruido_acima_acao; R-AUD-02 referencia ruido_acima_acao e
    # também `ruido` no branch e:[ruido, ototoxico, vibracao_qualquer]. Neste cenário
    # ruido_acima_acao=False (ruído sem quantificação), então o `ou` não curto-circuita
    # e avança ao branch `e`, que avalia e cacheia `ruido` (002.H). Cf. D-ARQ-10.
    assert "ruido_acima_acao" in ctx.predicados
    assert "vibracao_corpo_inteiro" in ctx.predicados
    assert "ruido" in ctx.predicados

    # Nota: espaco_confinado e maquina_pesada NÃO são avaliados porque o `ou`
    # curto-circuita assim que altura=True é encontrado. Decisão arquitetural:
    # Stage 4 preserva semântica preguiçosa, cacheia apenas o caminho real de
    # avaliação. Ver docs/HISTORICO_OPERACIONAL.md § Sessão 002.D2.
    assert "espaco_confinado" not in ctx.predicados
    assert "maquina_pesada" not in ctx.predicados


def test_idempotencia() -> None:
    ctx = _ctx_altura()
    proto = carregar(_PROTOCOLO_DIR)

    stage_4_predicados(ctx, proto)
    predicados_apos_primeira = dict(ctx.predicados)

    stage_4_predicados(ctx, proto)
    predicados_apos_segunda = dict(ctx.predicados)

    assert predicados_apos_primeira == predicados_apos_segunda


def test_predicado_ausente_eh_cacheado_sem_pendencia() -> None:
    risco_ruido = Risco(
        agente="ruido",
        fonte="pgr",
        detalhe=None,
        quantificacao=None,  # sem quantificação → ruido_acima_acao retorna Ausente
        anexo_nr07=None,
    )
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[risco_ruido])

    proto_teste = Protocolo(
        vocabulario=Vocabulario(agentes={}, cargos={}, exames={}, epis={}),
        predicados_compostos={},
        regras=[
            {"id": "R-TESTE", "quando": "ruido_acima_acao", "emite": []}
        ],
        regimes={},
    )

    stage_4_predicados(ctx, proto_teste)

    assert isinstance(ctx.predicados["ruido_acima_acao"], Ausente)
    assert ctx.pendencias == []


def test_cache_economiza_recomputacao(monkeypatch: pytest.MonkeyPatch) -> None:
    contador: list[int] = [0]
    original = REGISTRO_PRIMITIVOS["altura"]

    def primitivo_contador(ctx: GHEContext) -> Any:
        contador[0] += 1
        return original(ctx)

    monkeypatch.setitem(REGISTRO_PRIMITIVOS, "altura", primitivo_contador)

    ctx = _ctx_altura()
    proto = carregar(_PROTOCOLO_DIR)

    stage_4_predicados(ctx, proto)

    # 3 chamadas adicionais — devem todas bater o cache
    avaliar_predicado("altura", ctx, proto)
    avaliar_predicado("altura", ctx, proto)
    avaliar_predicado("altura", ctx, proto)

    assert contador[0] == 1
