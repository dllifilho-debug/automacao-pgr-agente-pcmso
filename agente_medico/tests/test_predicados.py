from __future__ import annotations

import ast
from pathlib import Path
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
    pernas_ausentes,
    pernas_ausentes_absorvidas,
    primitivo,
)
from agente_medico.motor.protocolo import Vocabulario, carregar
from agente_medico.motor.tipos import Ausente, GHEContext, GHEPGR, Quantificacao, Risco

_PREDICADOS_PATH = Path(__file__).parent.parent / "motor" / "predicados.py"
_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


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
    riscos = [Risco(agente=a, fonte="teste", detalhe=None, quantificacao=None, tipo_ibe=None) for a in agentes]
    return GHEContext(pgr_ghe=_ghe_vazio(), riscos=riscos)


def _ctx_ruido_quantificado(relacao_LT: str | None, apenas_qualitativa: bool = False) -> GHEContext:
    q = Quantificacao(valor=85.0, unidade="dB(A)", relacao_LT=relacao_LT, pct_LT=None, apenas_qualitativa=apenas_qualitativa)
    risco = Risco(agente="ruido", fonte="medicao", detalhe=None, quantificacao=q, tipo_ibe=None)
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


def test_ruido_true_quando_presente() -> None:
    assert REGISTRO_PRIMITIVOS["ruido"](_ctx("ruido")) is True


# ---------------------------------------------------------------------------
# ruido_acima_acao
# ---------------------------------------------------------------------------

def test_ruido_acima_acao_false_sem_risco_ruido() -> None:
    result = REGISTRO_PRIMITIVOS["ruido_acima_acao"](_ctx())
    assert result is False


def test_ruido_acima_acao_ausente_sem_quantificacao() -> None:
    risco = Risco(agente="ruido", fonte="teste", detalhe=None, quantificacao=None, tipo_ibe=None)
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
    ctx.riscos.append(Risco(agente="trabalho_altura", fonte="t", detalhe=None, quantificacao=None, tipo_ibe=None))
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
    ctx.riscos.append(Risco(agente="trabalho_altura", fonte="t", detalhe=None, quantificacao=None, tipo_ibe=None))
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
    compostos = {"atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx("motorista_equipamento_pesado")
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


# ---------------------------------------------------------------------------
# motorista_equipamento_pesado
# ---------------------------------------------------------------------------

def test_motorista_equipamento_pesado_true_quando_presente() -> None:
    assert REGISTRO_PRIMITIVOS["motorista_equipamento_pesado"](_ctx("motorista_equipamento_pesado")) is True


def test_motorista_equipamento_pesado_false_quando_ausente() -> None:
    assert REGISTRO_PRIMITIVOS["motorista_equipamento_pesado"](_ctx()) is False


# ---------------------------------------------------------------------------
# vibracao_mao_braco
# ---------------------------------------------------------------------------

def test_vibracao_mao_braco_true_slug_especifico() -> None:
    assert REGISTRO_PRIMITIVOS["vibracao_mao_braco"](_ctx("vibracao_mao_braco")) is True


def test_vibracao_mao_braco_ausente_slug_generico() -> None:
    result = REGISTRO_PRIMITIVOS["vibracao_mao_braco"](_ctx("vibracao"))
    assert isinstance(result, Ausente)


def test_vibracao_mao_braco_false_vci_presente() -> None:
    assert REGISTRO_PRIMITIVOS["vibracao_mao_braco"](_ctx("vibracao_corpo_inteiro")) is False


def test_vibracao_mao_braco_false_sem_vibracao() -> None:
    assert REGISTRO_PRIMITIVOS["vibracao_mao_braco"](_ctx()) is False


# ---------------------------------------------------------------------------
# vibracao_qualquer (composto)
# ---------------------------------------------------------------------------

_compostos_vibracao = {"vibracao_qualquer": {"ou": ["vibracao_corpo_inteiro", "vibracao_mao_braco"]}}


def test_vibracao_qualquer_true_por_vci() -> None:
    proto = _protocolo_stub(_compostos_vibracao)
    assert avaliar_predicado("vibracao_qualquer", _ctx("vibracao_corpo_inteiro"), proto) is True


def test_vibracao_qualquer_true_por_vmb() -> None:
    proto = _protocolo_stub(_compostos_vibracao)
    assert avaliar_predicado("vibracao_qualquer", _ctx("vibracao_mao_braco"), proto) is True


def test_vibracao_qualquer_ausente_por_generico() -> None:
    proto = _protocolo_stub(_compostos_vibracao)
    result = avaliar_predicado("vibracao_qualquer", _ctx("vibracao"), proto)
    assert isinstance(result, Ausente)


def test_vibracao_qualquer_false_por_nenhum() -> None:
    proto = _protocolo_stub(_compostos_vibracao)
    assert avaliar_predicado("vibracao_qualquer", _ctx(), proto) is False


# ---------------------------------------------------------------------------
# Fallback por identidade de agente (R-BIO-04)
# ---------------------------------------------------------------------------

def _protocolo_stub_agentes(agentes: dict[str, Any]) -> Any:
    proto = _protocolo_stub()
    proto.vocabulario = Vocabulario(agentes=agentes, cargos={}, exames={}, epis={})
    return proto


def test_fallback_agente_true_quando_presente_no_ctx() -> None:
    proto = _protocolo_stub_agentes({"chumbo": {}})
    assert avaliar_predicado("chumbo", _ctx("chumbo"), proto) is True


def test_fallback_agente_false_quando_ausente_no_ctx() -> None:
    proto = _protocolo_stub_agentes({"chumbo": {}})
    assert avaliar_predicado("chumbo", _ctx(), proto) is False


def test_fallback_agente_nao_aplica_a_nome_fora_do_vocabulario() -> None:
    proto = _protocolo_stub_agentes({"chumbo": {}})
    with pytest.raises(PredicadoDesconhecido):
        avaliar_predicado("agente_com_typo", _ctx(), proto)


# ---------------------------------------------------------------------------
# Anti-órfão (003.ED, molde D-ARQ-64 cláusula 5): extrai do próprio fonte de
# predicados.py todo literal comparado contra `r.agente` (== ou `in {...}`) e
# cruza com as chaves reais de vocabulario/agentes.yaml. Um literal sem slug
# correspondente é um primitivo morto em produção — o bug de 003.ED
# (maquina_pesada) não tinha nenhum teste que pudesse detectá-lo porque os
# testes de predicados constroem contexto sintético. Este teste computa do
# dado real; nunca digite a lista de literais aqui.
# ---------------------------------------------------------------------------

def _e_r_agente(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and node.attr == "agente"
        and isinstance(node.value, ast.Name)
        and node.value.id == "r"
    )


def _literal_str(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _literais_agente_comparados(caminho: Path) -> set[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    literais: set[str] = set()
    for node in ast.walk(arvore):
        if not isinstance(node, ast.Compare) or len(node.ops) != 1:
            continue
        op = node.ops[0]
        esquerda = node.left
        direita = node.comparators[0]
        if isinstance(op, ast.Eq):
            if _e_r_agente(esquerda):
                literal = _literal_str(direita)
            elif _e_r_agente(direita):
                literal = _literal_str(esquerda)
            else:
                literal = None
            if literal is not None:
                literais.add(literal)
        elif isinstance(op, ast.In) and _e_r_agente(esquerda):
            if isinstance(direita, (ast.Set, ast.Tuple, ast.List)):
                for elt in direita.elts:
                    literal = _literal_str(elt)
                    if literal is not None:
                        literais.add(literal)
    return literais


# ---------------------------------------------------------------------------
# pernas_ausentes_absorvidas (D-ARQ-71 cl.1): perna Ausente de um `ou` some do
# tri-estado quando outra perna do MESMO `ou` resolve True — avaliar() descarta
# via curto-circuito (nota 002.D2 de D-ARQ-10). Esta função reavalia sem
# curto-circuito só para tornar essa perna visível, sem tocar avaliar/avaliar_predicado.
# ---------------------------------------------------------------------------

def _ctx_ruido_sem_quant_e(*agentes: str) -> GHEContext:
    risco_ruido = Risco(agente="ruido", fonte="teste", detalhe=None, quantificacao=None, tipo_ibe=None)
    outros = [Risco(agente=a, fonte="teste", detalhe=None, quantificacao=None, tipo_ibe=None) for a in agentes]
    return GHEContext(pgr_ghe=_ghe_vazio(), riscos=[risco_ruido, *outros])


def test_pernas_ausentes_absorvidas_ou_ausente_antes_de_true() -> None:
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura")
    expr = {"ou": ["ruido_acima_acao", "altura"]}
    resultado = pernas_ausentes_absorvidas(expr, ctx, _p)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_absorvidas_ou_ausente_depois_de_true_ordem_invertida() -> None:
    # Prova que a detecção não é ordem-dependente — sem este teste a fatia não está pronta.
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura")
    expr = {"ou": ["altura", "ruido_acima_acao"]}
    resultado = pernas_ausentes_absorvidas(expr, ctx, _p)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_absorvidas_ou_false_true_nao_detecta_nada() -> None:
    ctx = _ctx("trabalho_altura")
    expr = {"ou": ["espaco_confinado", "altura"]}
    assert pernas_ausentes_absorvidas(expr, ctx, _p) == ()


def test_pernas_ausentes_absorvidas_ou_ausente_sem_true_nao_absorve() -> None:
    # O `ou` inteiro resolve Ausente (bolha pra cima) — caminho bloqueante existente
    # (predicado_ausente) segue como está; esta função não deve reportar nada aqui.
    ctx = _ctx_ruido_sem_quant_e()
    expr = {"ou": ["ruido_acima_acao", "espaco_confinado"]}
    assert pernas_ausentes_absorvidas(expr, ctx, _p) == ()


def test_pernas_ausentes_absorvidas_e_nao_coleta() -> None:
    # `e` com perna Ausente propaga Ausente pra cima e já vira pendência bloqueante
    # pelo caminho existente — não duplicar aqui.
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura")
    expr = {"e": ["altura", "ruido_acima_acao"]}
    assert pernas_ausentes_absorvidas(expr, ctx, _p) == ()


def test_pernas_ausentes_absorvidas_ou_aninhado_dentro_de_e_detectado() -> None:
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura", "espaco_confinado")
    expr = {"e": [{"ou": ["ruido_acima_acao", "altura"]}, "espaco_confinado"]}
    resultado = pernas_ausentes_absorvidas(expr, ctx, _p)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


# ---------------------------------------------------------------------------
# pernas_ausentes_absorvidas — emenda D-ARQ-71 cl.1: atravessa predicado
# composto nomeado (a absorção pode morar DENTRO do composto, ex.:
# vibracao_qualquer = ou(vibracao_corpo_inteiro, vibracao_mao_braco)).
# ---------------------------------------------------------------------------


def test_pernas_ausentes_absorvidas_composto_nomeado_string_pura() -> None:
    # Teste 10: quando é string pura nomeando um composto — antes da emenda,
    # _coletar... retornava () na primeira linha (isinstance(expr, dict) falso).
    compostos = {"c": {"ou": ["ruido_acima_acao", "altura"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura")
    resultado = pernas_ausentes_absorvidas("c", ctx, proto)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_absorvidas_composto_aninhado_em_e() -> None:
    # Teste 11: composto nomeado como filho de um "e".
    compostos = {"c": {"ou": ["ruido_acima_acao", "altura"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx_ruido_sem_quant_e("trabalho_altura", "espaco_confinado")
    expr = {"e": ["espaco_confinado", "c"]}
    resultado = pernas_ausentes_absorvidas(expr, ctx, proto)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_absorvidas_ciclo_propaga_ciclopredicados() -> None:
    # Teste 12: composto que se referencia — a chamada avaliar(filho, ...) dentro da
    # travessia levanta CicloPredicados antes que a guarda estrutural própria importe
    # (nota de realidade do Arquiteto). Contrato: exceção propagada, não retorno vazio.
    compostos = {"a": {"ou": ["a"]}}
    proto = _protocolo_stub(compostos)
    with pytest.raises(CicloPredicados):
        pernas_ausentes_absorvidas("a", _ctx(), proto)


def test_pernas_ausentes_absorvidas_composto_sem_absorcao() -> None:
    # Teste 13: composto cujas pernas resolvem True/False sem Ausente — zero pendência.
    compostos = {"c": {"ou": ["altura", "espaco_confinado"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx("trabalho_altura")
    assert pernas_ausentes_absorvidas("c", ctx, proto) == ()


# ---------------------------------------------------------------------------
# pernas_ausentes — D-ARQ-68 cl.5: irmã de pernas_ausentes_absorvidas, sem o
# gate alguma_true no `ou` (coleta toda perna Ausente, haja ou não True) e
# com coleta do próprio primitivo/composto quando `expr` é string simples.
# ---------------------------------------------------------------------------


def test_pernas_ausentes_ou_sem_nenhuma_perna_true() -> None:
    # Teste 1: reversão que mata — reintroduzir o gate alguma_true.
    ctx = _ctx_ruido_sem_quant_e()
    expr = {"ou": ["ruido_acima_acao", "espaco_confinado"]}
    resultado = pernas_ausentes(expr, ctx, _p)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_string_simples_coleta_proprio_nome() -> None:
    # Teste 2: reversão que mata — remover o ramo string-coleta (a armadilha de 2a).
    ctx = _ctx_ruido_sem_quant_e()
    resultado = pernas_ausentes("ruido_acima_acao", ctx, _p)
    assert len(resultado) == 1
    nome, ausente = resultado[0]
    assert nome == "ruido_acima_acao"
    assert isinstance(ausente, Ausente)


def test_pernas_ausentes_desce_em_composto_nomeado_sem_true() -> None:
    # Teste 3: reversão que mata — remover a expansão de predicados_compostos.
    compostos = {"c": {"ou": ["ruido_acima_acao", "espaco_confinado"]}}
    proto = _protocolo_stub(compostos)
    ctx = _ctx_ruido_sem_quant_e()
    resultado = pernas_ausentes("c", ctx, proto)
    nomes = {nome for nome, _ in resultado}
    assert "ruido_acima_acao" in nomes


def test_todo_literal_de_agente_em_predicados_existe_no_vocabulario() -> None:
    literais = _literais_agente_comparados(_PREDICADOS_PATH)
    assert literais, "nenhum literal de agente extraído — extrator quebrado ou predicados.py vazio"

    protocolo = carregar(_PROTOCOLO_DIR)
    slugs = set(protocolo.vocabulario.agentes.keys())

    orfaos = literais - slugs
    assert orfaos == set(), (
        f"literais de r.agente == '...' em predicados.py sem slug correspondente "
        f"em vocabulario/agentes.yaml (primitivo morto em produção): {sorted(orfaos)}"
    )
