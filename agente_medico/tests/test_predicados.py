from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from agente_medico.motor.predicados import (
    REGISTRO_PRIMITIVOS,
    CicloPredicados,
    PredicadoDesconhecido,
    ResultadoPredicado,
    avaliar,
    avaliar_predicado,
    primitivo,
)
from agente_medico.motor.tipos import Ausente, GHEContext, GHEPGR, Quantificacao, Risco


def _ghe_vazio() -> GHEPGR:
    return GHEPGR(
        id="GHE-01",
        nome="Teste",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _ctx(*agentes: str) -> GHEContext:
    riscos = [Risco(agente=a, fonte="teste", detalhe=None, quantificacao=None, anexo_nr07=None) for a in agentes]
    return GHEContext(pgr_ghe=_ghe_vazio(), riscos=riscos)


def _ctx_ruido_quantificado(relacao_LT: str | None, apenas_qualitativa: bool = False) -> GHEContext:
    q = Quantificacao(valor=85.0, unidade="dB(A)", relacao_LT=relacao_LT, pct_LT=None, apenas_qualitativa=apenas_qualitativa)
    risco = Risco(agente="ruido", fonte="medicao", detalhe=None, quantificacao=q, anexo_nr07=None)
    return GHEContext(pgr_ghe=_ghe_vazio(), riscos=[risco])


def _protocolo_stub(compostos: dict[str, Any] | None = None) -> Any:
    p = MagicMock()
    p.predicados_compostos = compostos or {}
    return p


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

def test_decorator_primitivo_registra_funcao() -> None:
    assert "altura" in REGISTRO_PRIMITIVOS
    assert callable(REGISTRO_PRIMITIVOS["altura"])


def test_decorator_primitivo_sobrescrita_levanta() -> None:
    with pytest.raises(ValueError, match="já registrado"):
        @primitivo("altura")
        def _duplicado(ctx: GHEContext) -> ResultadoPredicado:
            return False


# ---------------------------------------------------------------------------
# Primitivos qualitativos
# ---------------------------------------------------------------------------

def test_altura_true_quando_risco_presente() -> None:
    assert REGISTRO_PRIMITIVOS["altura"](_ctx("trabalho_altura")) is True


def test_altura_false_quando_sem_risco() -> None:
    assert REGISTRO_PRIMITIVOS["altura"](_ctx()) is False


def test_espaco_confinado_true_quando_presente() -> None:
    assert REGISTRO_PRIMITIVOS["espaco_confinado"](_ctx("espaco_confinado")) is True


def test_maquina_pesada_true_quando_presente() -> None:
    assert REGISTRO_PRIMITIVOS["maquina_pesada"](_ctx("maquina_pesada")) is True


def test_ruido_true_quando_presente() -> None:
    assert REGISTRO_PRIMITIVOS["ruido"](_ctx("ruido")) is True


# ---------------------------------------------------------------------------
# ruido_acima_acao
# ---------------------------------------------------------------------------

def test_ruido_acima_acao_false_sem_risco_ruido() -> None:
    result = REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx())
    assert result is False


def test_ruido_acima_acao_ausente_sem_quantificacao() -> None:
    risco = Risco(agente="ruido", fonte="teste", detalhe=None, quantificacao=None, anexo_nr07=None)
    ctx = GHEContext(pgr_ghe=_ghe_vazio(), riscos=[risco])
    result = REGISTRO_PRIMITIVOS["ruido_acima_acao"](ctx)
    assert isinstance(result, Ausente)


def test_ruido_acima_acao_ausente_apenas_qualitativa() -> None:
    result = REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx_ruido_quantificado(relacao_LT=None, apenas_qualitativa=True))
    assert isinstance(result, Ausente)


def test_ruido_acima_acao_true_acima_LT() -> None:
    assert REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx_ruido_quantificado("acima_LT")) is True


def test_ruido_acima_acao_true_acima_acao() -> None:
    assert REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx_ruido_quantificado("acima_acao")) is True


def test_ruido_acima_acao_false_abaixo_acao() -> None:
    assert REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx_ruido_quantificado("abaixo_acao")) is False


# ---------------------------------------------------------------------------
# Avaliador de compostos — tri-estado
# ---------------------------------------------------------------------------

_p = _protocolo_stub()
_ausente = Ausente(mensagem="dado ausente")


def _ctx_simples() -> GHEContext:
    return _ctx()


def test_avaliar_e_todos_true() -> None:
    ctx = _ctx("trabalho_altura", "espaco_confinado")
    expr = {"e": ["altura", "espaco_confinado"]}
    assert avaliar(expr, ctx, _p) is True


def test_avaliar_e_curto_circuito_false() -> None:
    ctx = _ctx("trabalho_altura")
    expr = {"e": ["altura", "espaco_confinado"]}
    assert avaliar(expr, ctx, _p) is False


def test_avaliar_e_propaga_ausente_se_resto_true() -> None:
    ctx = _ctx_ruido_quantificado(relacao_LT=None)  # ruido_acima_acao → Ausente
    ctx.riscos.append(Risco(agente="trabalho_altura", fonte="t", detalhe=None, quantificacao=None, anexo_nr07=None))
    expr = {"e": ["altura", "ruido_acima_acao"]}
    result = avaliar(expr, ctx, _p)
    assert isinstance(result, Ausente)


def test_avaliar_e_nao_propaga_ausente_se_tem_false() -> None:
    ctx = _ctx_ruido_quantificado(relacao_LT=None)  # ruido_acima_acao → Ausente; espaco_confinado → False
    expr = {"e": ["espaco_confinado", "ruido_acima_acao"]}
    assert avaliar(expr, ctx, _p) is False


def test_avaliar_ou_curto_circuito_true() -> None:
    ctx = _ctx("trabalho_altura")
    expr = {"ou": ["altura", "espaco_confinado"]}
    assert avaliar(expr, ctx, _p) is True


def test_avaliar_ou_todos_false() -> None:
    ctx = _ctx()
    expr = {"ou": ["altura", "espaco_confinado"]}
    assert avaliar(expr, ctx, _p) is False


def test_avaliar_ou_propaga_ausente_se_resto_false() -> None:
    ctx = _ctx_ruido_quantificado(relacao_LT=None)  # ruido_acima_acao → Ausente; espaco_confinado → False
    expr = {"ou": ["espaco_confinado", "ruido_acima_acao"]}
    result = avaliar(expr, ctx, _p)
    assert isinstance(result, Ausente)


def test_avaliar_ou_nao_propaga_ausente_se_tem_true() -> None:
    ctx = _ctx_ruido_quantificado(relacao_LT=None)
    ctx.riscos.append(Risco(agente="trabalho_altura", fonte="t", detalhe=None, quantificacao=None, anexo_nr07=None))
    expr = {"ou": ["altura", "ruido_acima_acao"]}
    assert avaliar(expr, ctx, _p) is True


def test_avaliar_nao_inverte_true_false() -> None:
    ctx_com_altura = _ctx("trabalho_altura")
    ctx_sem_altura = _ctx()
    assert avaliar({"nao": "altura"}, ctx_com_altura, _p) is False
    assert avaliar({"nao": "altura"}, ctx_sem_altura, _p) is True


def test_avaliar_nao_propaga_ausente() -> None:
    ctx = _ctx_ruido_quantificado(relacao_LT=None)
    result = avaliar({"nao": "ruido_acima_acao"}, ctx, _p)
    assert isinstance(result, Ausente)


# ---------------------------------------------------------------------------
# avaliar_predicado
# ---------------------------------------------------------------------------

def test_avaliar_predicado_resolve_primitivo() -> None:
    ctx = _ctx("trabalho_altura")
    result = avaliar_predicado("altura", ctx, _protocolo_stub())
    assert result is True


def test_avaliar_predicado_resolve_composto() -> None:
    compostos = {"atividade_critica": {"ou": ["altura", "espaco_confinado", "maquina_pesada"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx("maquina_pesada")
    assert avaliar_predicado("atividade_critica", ctx, proto) is True


def test_avaliar_predicado_desconhecido_levanta_PredicadoDesconhecido() -> None:
    with pytest.raises(PredicadoDesconhecido):
        avaliar_predicado("nao_existe", _ctx(), _protocolo_stub())


def test_avaliar_predicado_ciclo_levanta_CicloPredicados() -> None:
    compostos = {
        "pred_a": {"ou": ["pred_b"]},
        "pred_b": {"ou": ["pred_a"]},
    }
    proto = _protocolo_stub(compostos)
    with pytest.raises(CicloPredicados):
        avaliar_predicado("pred_a", _ctx(), proto)
