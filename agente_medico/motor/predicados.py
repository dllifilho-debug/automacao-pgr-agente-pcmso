from __future__ import annotations

from typing import Any, Callable, Union

from agente_medico.motor.tipos import Ausente, GHEContext

ResultadoPredicado = Union[bool, Ausente]

REGISTRO_PRIMITIVOS: dict[str, Callable[[GHEContext], ResultadoPredicado]] = {}


class PredicadoDesconhecido(KeyError):
    pass


class CicloPredicados(RuntimeError):
    pass


def primitivo(nome: str) -> Callable[[Callable[[GHEContext], ResultadoPredicado]], Callable[[GHEContext], ResultadoPredicado]]:
    def decorator(fn: Callable[[GHEContext], ResultadoPredicado]) -> Callable[[GHEContext], ResultadoPredicado]:
        if nome in REGISTRO_PRIMITIVOS:
            raise ValueError(f"Primitivo '{nome}' já registrado — sobrescrita não permitida")
        REGISTRO_PRIMITIVOS[nome] = fn
        return fn
    return decorator


@primitivo("altura")
def _altura(ctx: GHEContext) -> bool:
    return any(r.agente == "trabalho_altura" for r in ctx.riscos)


@primitivo("espaco_confinado")
def _espaco_confinado(ctx: GHEContext) -> bool:
    return any(r.agente == "espaco_confinado" for r in ctx.riscos)


@primitivo("maquina_pesada")
def _maquina_pesada(ctx: GHEContext) -> bool:
    return any(r.agente == "maquina_pesada" for r in ctx.riscos)


@primitivo("ruido")
def _ruido(ctx: GHEContext) -> bool:
    return any(r.agente == "ruido" for r in ctx.riscos)


@primitivo("ruido_acima_acao")
def _ruido_acima_acao(ctx: GHEContext) -> ResultadoPredicado:
    risco_ruido = next((r for r in ctx.riscos if r.agente == "ruido"), None)
    if risco_ruido is None:
        return False
    q = risco_ruido.quantificacao
    if q is None or q.apenas_qualitativa or q.relacao_LT is None:
        return Ausente(
            mensagem="Ruído presente sem quantificação — necessário medir para avaliar exposição acima do nível de ação"
        )
    if q.relacao_LT in {"acima_acao", "acima_LT", "entre_acao_LT"}:
        return True
    return False


def avaliar(expr: Any, ctx: GHEContext, protocolo: Any, _visitados: frozenset[str] = frozenset()) -> ResultadoPredicado:
    if isinstance(expr, str):
        return avaliar_predicado(expr, ctx, protocolo, _visitados)
    if isinstance(expr, dict):
        if "e" in expr:
            filhos: list[Any] = expr["e"]
            primeiro_ausente: Ausente | None = None
            for filho in filhos:
                val = avaliar(filho, ctx, protocolo, _visitados)
                if val is False:
                    return False
                if isinstance(val, Ausente) and primeiro_ausente is None:
                    primeiro_ausente = val
            return primeiro_ausente if primeiro_ausente is not None else True
        if "ou" in expr:
            filhos_ou: list[Any] = expr["ou"]
            primeiro_ausente_ou: Ausente | None = None
            for filho in filhos_ou:
                val = avaliar(filho, ctx, protocolo, _visitados)
                if val is True:
                    return True
                if isinstance(val, Ausente) and primeiro_ausente_ou is None:
                    primeiro_ausente_ou = val
            return primeiro_ausente_ou if primeiro_ausente_ou is not None else False
        if "nao" in expr:
            val = avaliar(expr["nao"], ctx, protocolo, _visitados)
            if isinstance(val, Ausente):
                return val
            return not val
    raise ValueError(f"Expressão de predicado inválida: {expr!r}")


def avaliar_predicado(nome: str, ctx: GHEContext, protocolo: Any, _visitados: frozenset[str] = frozenset()) -> ResultadoPredicado:
    if nome in ctx.predicados:
        return ctx.predicados[nome]
    if nome in REGISTRO_PRIMITIVOS:
        resultado = REGISTRO_PRIMITIVOS[nome](ctx)
        ctx.predicados[nome] = resultado
        return resultado
    compostos: dict[str, Any] = protocolo.predicados_compostos
    if nome in compostos:
        if nome in _visitados:
            raise CicloPredicados(f"Ciclo detectado ao avaliar predicado '{nome}'")
        resultado = avaliar(compostos[nome], ctx, protocolo, _visitados | {nome})
        ctx.predicados[nome] = resultado
        return resultado
    raise PredicadoDesconhecido(nome)
