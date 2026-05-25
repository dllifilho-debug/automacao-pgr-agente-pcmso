from __future__ import annotations

from typing import Any, Callable, Union

from agente_medico.motor.tipos import Ausente, GHEContext, Quantificacao

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


@primitivo("vibracao_corpo_inteiro")
def _vibracao_corpo_inteiro(ctx: GHEContext) -> ResultadoPredicado:
    if any(r.agente == "vibracao_corpo_inteiro" for r in ctx.riscos):
        return True
    if any(r.agente == "vibracao" for r in ctx.riscos):
        return Ausente(
            mensagem="Vibração presente sem qualificação de tipo — necessário "
                     "especificar corpo inteiro ou mãos-braços para avaliar"
        )
    return False


@primitivo("motorista_equipamento_pesado")
def _motorista_equipamento_pesado(ctx: GHEContext) -> bool:
    return any(r.agente == "motorista_equipamento_pesado" for r in ctx.riscos)


@primitivo("vibracao_mao_braco")
def _vibracao_mao_braco(ctx: GHEContext) -> ResultadoPredicado:
    if any(r.agente == "vibracao_mao_braco" for r in ctx.riscos):
        return True
    if any(r.agente == "vibracao" for r in ctx.riscos):
        return Ausente(mensagem="Vibração presente sem qualificação de tipo — necessário "
                                "especificar corpo inteiro ou mãos-braços para avaliar")
    return False


@primitivo("ototoxico")
def _ototoxico(ctx: GHEContext) -> bool:
    return any(r.is_ototoxico for r in ctx.riscos)


# TODO normativo: conferir vs Anexo III Portaria 567/2022 — opção B
_PCT_LEO_BAIXO: float = 10.0   # ate_10: pct_LT <= this
_PCT_LEO_MEDIO: float = 50.0   # 10_50: prev < pct_LT < this
_PCT_LEO_ALTO: float = 100.0   # 50_100: prev <= pct_LT < this; acima_100: >= this


def _helper_silica_asbesto(ctx: GHEContext) -> Union[Quantificacao, bool, Ausente]:
    risco = next((r for r in ctx.riscos if r.agente in {"silica", "asbesto"}), None)
    if risco is None:
        return False
    q = risco.quantificacao
    if q is None or (q.pct_LT is None and not q.sem_avaliacao_quantitativa):
        return Ausente(
            "Sílica/asbesto sem quantificação nem indicação de ausência de "
            "avaliação — medir ou declarar ausência de laudo"
        )
    return q


@primitivo("fumos_metalicos")
def _fumos_metalicos(ctx: GHEContext) -> bool:
    return any(r.agente == "fumos_metalicos" for r in ctx.riscos)


@primitivo("silica_asbesto_sem_medicao")
def _silica_asbesto_sem_medicao(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.sem_avaliacao_quantitativa


@primitivo("silica_asbesto_leo_ate_10")
def _silica_asbesto_leo_ate_10(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT <= _PCT_LEO_BAIXO


@primitivo("silica_asbesto_leo_10_50")
def _silica_asbesto_leo_10_50(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_BAIXO < r.pct_LT < _PCT_LEO_MEDIO


@primitivo("silica_asbesto_leo_50_100")
def _silica_asbesto_leo_50_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_MEDIO <= r.pct_LT < _PCT_LEO_ALTO


@primitivo("silica_asbesto_leo_acima_100")
def _silica_asbesto_leo_acima_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT >= _PCT_LEO_ALTO


@primitivo("pnos")
def _pnos(ctx: GHEContext) -> bool:
    return any(r.agente == "poeira_nao_classificada" for r in ctx.riscos)


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
