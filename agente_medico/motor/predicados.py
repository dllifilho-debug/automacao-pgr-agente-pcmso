from __future__ import annotations

from dataclasses import replace
from typing import Any, Callable, Union

from agente_medico.motor.leo_resolver import classifica_cenario, resolve_leo
from agente_medico.motor.tipos import Ausente, Fracao, GHEContext, Quantificacao

ResultadoPredicado = Union[bool, Ausente]

REGISTRO_PRIMITIVOS: dict[str, Callable[[GHEContext], ResultadoPredicado]] = {}

# Predicados incondicionais (sempre True, independente de risco) — usados pelo
# orquestrador (D-ARQ-31 fatia 2) para excluir linhas de piso universal do
# cálculo do tri-estado, preservando o poder discriminante VÁLIDA/PARCIAL/BLOQUEADA.
PRIMITIVOS_INCONDICIONAIS: frozenset[str] = frozenset({"todo_trabalhador"})


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


@primitivo("todo_trabalhador")
def _todo_trabalhador(ctx: GHEContext) -> bool:
    """R-CLI-01; NR-07 item 7.5.8 (exame clínico para todo empregado)."""
    return True


@primitivo("altura")
def _altura(ctx: GHEContext) -> bool:
    return any(r.agente == "trabalho_altura" for r in ctx.riscos)


@primitivo("espaco_confinado")
def _espaco_confinado(ctx: GHEContext) -> bool:
    return any(r.agente == "espaco_confinado" for r in ctx.riscos)


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


# Bordas conferidas vs Quadro 1 Anexo III NR-07 (Portaria MTP 567/2022) — [DERIVADO — 002.N]
# Quadro 1 usa "≤" nos limites superiores de cada faixa; CLSC = limite sup IC 95% da média aritmética
_PCT_LEO_BAIXO: float = 10.0   # ate_10:    pct_LT <= 10  (adm only)
_PCT_LEO_MEDIO: float = 50.0   # 10_50:  10 < pct_LT <= 50  (60M/36M)
_PCT_LEO_ALTO: float = 100.0   # 50_100: 50 < pct_LT <= 100 (36M/24M); acima_100: > 100 (12M)


def _helper_silica_asbesto(ctx: GHEContext) -> Union[Quantificacao, bool, Ausente]:
    risco = next((r for r in ctx.riscos if r.agente in {"silica", "asbesto"}), None)
    if risco is None:                                               # (a)
        return False
    q = risco.quantificacao
    if q is None:                                                   # (b)
        # R-RX-01 / NR-07 Anexo III Quadro 1, ramo "Empresas sem avaliações
        # quantitativas" (Portaria MTP 567/2022): sem laudo é faixa válida, não
        # pendência — os dois ramos do Quadro 1 são exaustivos.
        return Quantificacao(
            valor=None,
            unidade=None,
            relacao_LT=None,
            pct_LT=None,
            apenas_qualitativa=False,
            sem_avaliacao_quantitativa=True,
        )
    if (
        q.pct_LT is None
        and not q.sem_avaliacao_quantitativa
        and q.valor is not None
        and q.pct_quartzo is not None
    ):
        if q.fracao is None:
            return Ausente(
                "Sílica/asbesto com medição quantitativa mas sem fração informada — "
                "declarar respirável ou total para resolver o LEO (Anexo 12 NR-15)"
            )
        cenario_norm = classifica_cenario(ctx.pgr_ghe.cenario)
        res = resolve_leo(risco.agente, q.fracao, cenario_norm, q.pct_quartzo)
        leo = res.leo
        if leo is None:
            return Ausente(
                f"Sílica/asbesto: LEO indefinido para o cenário — {res.fonte_normativa}"
            )
        q = replace(q, pct_LT=(q.valor / leo) * 100.0)

    if q.pct_LT is not None and q.sem_avaliacao_quantitativa:      # (c)
        return Ausente(
            "Sílica/asbesto declara medição (pct_LT) e ausência de avaliação "
            "quantitativa ao mesmo tempo — input contraditório, corrigir no PGR"
        )
    if q.pct_LT is None and not q.sem_avaliacao_quantitativa:      # (d)
        return Ausente(
            "Sílica/asbesto sem quantificação nem indicação de ausência de "
            "avaliação — medir ou declarar ausência de laudo"
        )
    return q                                                        # (e)


@primitivo("fumos_metalicos")
def _fumos_metalicos(ctx: GHEContext) -> bool:
    return any(r.agente == "fumos_metalicos" for r in ctx.riscos)


@primitivo("silica")
def _silica(ctx: GHEContext) -> bool:
    """R-ESP-02; NR-07 Anexo III item 3.1 (Portaria MTP 567/2022)."""
    return any(r.agente == "silica" for r in ctx.riscos)


@primitivo("asbesto")
def _asbesto(ctx: GHEContext) -> bool:
    """R-ESP-02; NR-07 Anexo III item 3.1 (Portaria MTP 567/2022)."""
    return any(r.agente == "asbesto" for r in ctx.riscos)


@primitivo("benzeno")
def _benzeno(ctx: GHEContext) -> bool:
    return any(r.agente == "benzeno" for r in ctx.riscos)


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
    return r.pct_LT is not None and _PCT_LEO_BAIXO < r.pct_LT <= _PCT_LEO_MEDIO


@primitivo("silica_asbesto_leo_50_100")
def _silica_asbesto_leo_50_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_MEDIO < r.pct_LT <= _PCT_LEO_ALTO


@primitivo("silica_asbesto_leo_acima_100")
def _silica_asbesto_leo_acima_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT > _PCT_LEO_ALTO


@primitivo("pnos")
def _pnos(ctx: GHEContext) -> bool:
    """R-ESP-02; NR-07 Anexo III item 3.1 (Portaria MTP 567/2022). Único consumidor em
    runtime: R-ESP-02 — R-RX-01-pnos é DEPRECATED e filtrada pelo carregador; as faixas
    de RX usam pnos_leo_*/pnos_sem_medicao, não este."""
    return any(r.agente == "poeira_nao_classificada" for r in ctx.riscos)


# Quadro 2 Anexo III NR-07 (Portaria 567/2022) — PNOS [DERIVADO — 002.X/002.Y]
# Faixas agrupam diferente do Quadro 1: ate_10 (≤10), 10_100 (>10 e ≤100), acima_100 (>100)
def _helper_pnos(ctx: GHEContext) -> Union[Quantificacao, bool, Ausente]:
    risco = next((r for r in ctx.riscos if r.agente == "poeira_nao_classificada"), None)
    if risco is None:
        return False
    q = risco.quantificacao
    if q is None:
        # Sem laudo = sem_medicao (faixa válida do Quadro 2: adm+60M). NÃO bloqueia.
        # Ambos os Quadros (1 e 2) do Anexo III têm ramo de ausência exaustivo.
        return Quantificacao(
            valor=None,
            unidade=None,
            relacao_LT=None,
            pct_LT=None,
            apenas_qualitativa=False,
            sem_avaliacao_quantitativa=True,
        )
    if (
        q.pct_LT is None
        and not q.sem_avaliacao_quantitativa
        and q.valor is not None
    ):
        # D-ARQ-29: fração do PNOS é INVARIANTE (Quadro 2 só mede respirável; LEO fixo
        # 3 mg/m³ resp). Diferente de sílica (D-ARQ-24/002.V), injeta RESPIRAVEL quando
        # None em vez de bloquear — a fração não é grau de liberdade do laudo aqui.
        fracao = q.fracao if q.fracao is not None else Fracao.RESPIRAVEL
        cenario_norm = classifica_cenario(ctx.pgr_ghe.cenario)
        res = resolve_leo("poeira_nao_classificada", fracao, cenario_norm, q.pct_quartzo)
        if res.leo is None:
            return Ausente(f"PNOS: LEO indefinido — {res.fonte_normativa}")
        q = replace(q, pct_LT=(q.valor / res.leo) * 100.0)
    if q.pct_LT is not None and q.sem_avaliacao_quantitativa:
        return Ausente(
            "PNOS declara medição (pct_LT) e ausência de avaliação quantitativa ao "
            "mesmo tempo — input contraditório, corrigir no PGR"
        )
    return q


@primitivo("pnos_sem_medicao")
def _pnos_sem_medicao(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.sem_avaliacao_quantitativa


@primitivo("pnos_leo_ate_10")
def _pnos_leo_ate_10(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT <= _PCT_LEO_BAIXO


@primitivo("pnos_leo_10_100")
def _pnos_leo_10_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_BAIXO < r.pct_LT <= _PCT_LEO_ALTO


@primitivo("pnos_leo_acima_100")
def _pnos_leo_acima_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT > _PCT_LEO_ALTO


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


def _serializar_predicado(expr: object) -> str:
    if isinstance(expr, str):
        return expr
    if isinstance(expr, dict):
        if "e" in expr:
            return f"e({', '.join(_serializar_predicado(f) for f in expr['e'])})"
        if "ou" in expr:
            return f"ou({', '.join(_serializar_predicado(f) for f in expr['ou'])})"
        if "nao" in expr:
            return f"nao({_serializar_predicado(expr['nao'])})"
    raise ValueError(f"Expressão de predicado inválida: {expr!r}")


def _coletar_pernas_ausentes_absorvidas(
    expr: Any,
    ctx: GHEContext,
    protocolo: Any,
    acc: list[tuple[str, Ausente]],
    _visitados: frozenset[str] = frozenset(),
) -> None:
    if isinstance(expr, str):
        # D-ARQ-71 cl.1 emenda: expande composto nomeado — a absorção pode morar
        # DENTRO do composto (ex.: vibracao_qualquer = ou(VCI, VMB)), não só na
        # expressão literal da regra. Primitivo/fallback-agente/desconhecido não
        # tem onde descer — comportamento atual (sem coleta) preservado.
        compostos: dict[str, Any] = protocolo.predicados_compostos
        if expr in compostos and expr not in _visitados:
            _coletar_pernas_ausentes_absorvidas(
                compostos[expr], ctx, protocolo, acc, _visitados | {expr}
            )
        return
    if not isinstance(expr, dict):
        return
    if "ou" in expr:
        filhos = expr["ou"]
        valores = [avaliar(filho, ctx, protocolo) for filho in filhos]
        alguma_true = any(v is True for v in valores)
        for filho, valor in zip(filhos, valores):
            if alguma_true and isinstance(valor, Ausente):
                nome = filho if isinstance(filho, str) else _serializar_predicado(filho)
                acc.append((nome, valor))
            _coletar_pernas_ausentes_absorvidas(filho, ctx, protocolo, acc, _visitados)
    elif "e" in expr:
        for filho in expr["e"]:
            _coletar_pernas_ausentes_absorvidas(filho, ctx, protocolo, acc, _visitados)
    elif "nao" in expr:
        _coletar_pernas_ausentes_absorvidas(expr["nao"], ctx, protocolo, acc, _visitados)


def pernas_ausentes_absorvidas(
    expr: Any, ctx: GHEContext, protocolo: Any
) -> tuple[tuple[str, Ausente], ...]:
    """D-ARQ-71 cl.1: dentro de cada nó `ou` da expressão, uma perna que resolve
    Ausente fica invisível quando outra perna do mesmo `ou` resolve True — `avaliar`
    descarta o Ausente ao dar `return True` no curto-circuito (nota 002.D2 de
    D-ARQ-10, preservada). Esta função reavalia a expressão inteira (sem short-circuit)
    só para achar essas pernas, sem alterar `avaliar`/`avaliar_predicado`. `e`/`nao` só
    recorrem: seu próprio Ausente já propaga para cima e vira pendência bloqueante
    pelo caminho existente — não duplicar aqui. Atravessa predicado composto nomeado
    (emenda D-ARQ-71 cl.1) com guarda de ciclo estrutural própria — a detecção e
    sinalização de ciclo real continuam sendo de `avaliar`/`avaliar_predicado`
    (D-ARQ-09); esta guarda é defesa em profundidade, não caminho esperado.
    Retorna pares (nome_da_perna, Ausente) em ordem estável de ocorrência — o nome é
    a perna literal quando string, ou a serialização de `_serializar_predicado`
    quando sub-expressão."""
    acc: list[tuple[str, Ausente]] = []
    _coletar_pernas_ausentes_absorvidas(expr, ctx, protocolo, acc)
    return tuple(acc)


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
    # Fallback por identidade de agente: habilita a família R-BIO-04-<agente>
    # (roteamento de biomonitoramento) sem exigir um primitivo dedicado por agente.
    agentes = getattr(protocolo.vocabulario, "agentes", {})
    if nome in agentes:
        resultado = any(r.agente == nome for r in ctx.riscos)
        ctx.predicados[nome] = resultado
        return resultado
    raise PredicadoDesconhecido(nome)
