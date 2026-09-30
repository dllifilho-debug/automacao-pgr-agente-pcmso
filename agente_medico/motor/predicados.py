from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, replace
from typing import Any, Callable, Optional, Union

from agente_medico.motor.leo_resolver import classifica_cenario, resolve_leo
from agente_medico.motor.tipos import (
    NIVEIS_RISCO_PXS,
    Ausente,
    Fracao,
    GHEContext,
    Quantificacao,
    Risco,
)

ResultadoPredicado = Union[bool, Ausente]
FiltroRisco = Callable[[Risco], bool]
RiscosDoPrimitivo = Callable[[GHEContext], tuple[Risco, ...]]

REGISTRO_PRIMITIVOS: dict[str, Callable[[GHEContext], ResultadoPredicado]] = {}

# D-ARQ-88 cl.3: os riscos do GHE que satisfazem cada primitivo, lidos pela
# passada de explicação. Todo primitivo declara os seus ou está em
# PRIMITIVOS_SEM_RISCO (gatilho de GHE ou de cargo, sem risco a apontar).
REGISTRO_RISCOS: dict[str, RiscosDoPrimitivo] = {}
PRIMITIVOS_SEM_RISCO: frozenset[str] = frozenset(
    {"todo_trabalhador", "psicossocial", "cargo_porteiro"}
)

# Predicados incondicionais (sempre True, independente de risco) — usados pelo
# orquestrador (D-ARQ-31 fatia 2) para excluir linhas de piso universal do
# cálculo do tri-estado, preservando o poder discriminante VÁLIDA/PARCIAL/BLOQUEADA.
PRIMITIVOS_INCONDICIONAIS: frozenset[str] = frozenset({"todo_trabalhador"})


class PredicadoDesconhecido(KeyError):
    pass


class CicloPredicados(RuntimeError):
    pass


def primitivo(
    nome: str, riscos: Optional[RiscosDoPrimitivo] = None
) -> Callable[[Callable[[GHEContext], ResultadoPredicado]], Callable[[GHEContext], ResultadoPredicado]]:
    def decorator(fn: Callable[[GHEContext], ResultadoPredicado]) -> Callable[[GHEContext], ResultadoPredicado]:
        if nome in REGISTRO_PRIMITIVOS:
            raise ValueError(f"Primitivo '{nome}' já registrado — sobrescrita não permitida")
        REGISTRO_PRIMITIVOS[nome] = fn
        if riscos is not None:
            REGISTRO_RISCOS[nome] = riscos
        return fn
    return decorator


def _riscos_por(filtro: FiltroRisco) -> RiscosDoPrimitivo:
    return lambda ctx: tuple(r for r in ctx.riscos if filtro(r))


def _risco_unico(escolha: Callable[[GHEContext], Optional[Risco]]) -> RiscosDoPrimitivo:
    """Primitivo de quantificação: o risco é o que o helper leu, não todo
    risco do agente (D-ARQ-88 cl.3)."""
    def riscos(ctx: GHEContext) -> tuple[Risco, ...]:
        risco = escolha(ctx)
        return () if risco is None else (risco,)
    return riscos


def _por_filtro(nome: str, filtro: FiltroRisco) -> None:
    """Primitivo booleano de filtro único (D-ARQ-88 Q4): o predicado é
    `any(filtro)` e os riscos são os que passam no mesmo filtro."""
    def predicado(ctx: GHEContext) -> bool:
        return any(filtro(r) for r in ctx.riscos)
    primitivo(nome, riscos=_riscos_por(filtro))(predicado)


@primitivo("todo_trabalhador")
def _todo_trabalhador(ctx: GHEContext) -> bool:
    """R-CLI-01; NR-07 item 7.5.8 (exame clínico para todo empregado)."""
    return True


_por_filtro("altura", lambda r: r.agente == "trabalho_altura")
_por_filtro("espaco_confinado", lambda r: r.agente == "espaco_confinado")
_por_filtro("ruido", lambda r: r.agente == "ruido")


def _risco_ruido(ctx: GHEContext) -> Optional[Risco]:
    return next((r for r in ctx.riscos if r.agente == "ruido"), None)


@primitivo("ruido_acima_acao", riscos=_risco_unico(_risco_ruido))
def _ruido_acima_acao(ctx: GHEContext) -> ResultadoPredicado:
    risco_ruido = _risco_ruido(ctx)
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


def _vci(r: Risco) -> bool:
    return r.agente == "vibracao_corpo_inteiro"


def _vmb(r: Risco) -> bool:
    return r.agente == "vibracao_mao_braco"


@primitivo("vibracao_corpo_inteiro", riscos=_riscos_por(_vci))
def _vibracao_corpo_inteiro(ctx: GHEContext) -> ResultadoPredicado:
    if any(_vci(r) for r in ctx.riscos):
        return True
    if any(r.agente == "vibracao" for r in ctx.riscos):
        return Ausente(
            mensagem="Vibração presente sem qualificação de tipo — necessário "
                     "especificar corpo inteiro ou mãos-braços para avaliar"
        )
    return False


_por_filtro("motorista_equipamento_pesado", lambda r: r.agente == "motorista_equipamento_pesado")


@primitivo("vibracao_mao_braco", riscos=_riscos_por(_vmb))
def _vibracao_mao_braco(ctx: GHEContext) -> ResultadoPredicado:
    if any(_vmb(r) for r in ctx.riscos):
        return True
    if any(r.agente == "vibracao" for r in ctx.riscos):
        return Ausente(mensagem="Vibração presente sem qualificação de tipo — necessário "
                                "especificar corpo inteiro ou mãos-braços para avaliar")
    return False


_por_filtro("ototoxico", lambda r: r.is_ototoxico)


# Bordas conferidas vs Quadro 1 Anexo III NR-07 (Portaria MTP 567/2022) — [DERIVADO — 002.N]
# Quadro 1 usa "≤" nos limites superiores de cada faixa; CLSC = limite sup IC 95% da média aritmética
_PCT_LEO_BAIXO: float = 10.0   # ate_10:    pct_LT <= 10  (adm only)
_PCT_LEO_MEDIO: float = 50.0   # 10_50:  10 < pct_LT <= 50  (60M/36M)
_PCT_LEO_ALTO: float = 100.0   # 50_100: 50 < pct_LT <= 100 (36M/24M); acima_100: > 100 (12M)


def _risco_silica_asbesto(ctx: GHEContext) -> Optional[Risco]:
    return next((r for r in ctx.riscos if r.agente in {"silica", "asbesto"}), None)


def _helper_silica_asbesto(ctx: GHEContext) -> Union[Quantificacao, bool, Ausente]:
    risco = _risco_silica_asbesto(ctx)
    if risco is None:                                               # (a)
        return False
    q = risco.quantificacao
    if q is None:                                                   # (b)
        # R-RX-01 / NR-07 Anexo III Quadro 1, ramo "Empresas sem avaliações
        # quantitativas" (Portaria MTP 567/2022): sem laudo é faixa válida, não
        # pendência — os dois ramos do Quadro 1 são exaustivos.
        # R-RX-01-qual (DT-003EC-01): dentro desse ramo, sílica com avaliação
        # qualitativa P×S declarada na linha do risco é estado próprio
        # (apenas_qualitativa). Só sílica — asbesto sem medição nem decisão.
        return Quantificacao(
            valor=None,
            unidade=None,
            relacao_LT=None,
            pct_LT=None,
            apenas_qualitativa=risco.agente == "silica" and risco.nivel_risco is not None,
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


_por_filtro("fumos_metalicos", lambda r: r.agente == "fumos_metalicos")


@primitivo("psicossocial")
def _psicossocial(ctx: GHEContext) -> bool:
    """R-PSY-05 (ex-R-PSY-03); NR-01 itens 1.5.3.1.4/1.5.3.2.1/1.5.4.4.5.3 — sinal
    PGR-documenta-psicossocial (GHEPGR.psicossocial, extraído por
    detectar_psicossocial em extracao_pgr.py)."""
    return ctx.pgr_ghe.psicossocial


# R-RX-03/R-ESP-03; agente carcinogênico (IARC Grupo 1) fora dos Quadros 1 e 2
# do Anexo III NR-07 (não é sílica/asbesto/carvão nem PNOS) — DT-003EJ-01.
_por_filtro("poeira_de_madeira", lambda r: r.agente == "poeira_de_madeira")
# R-RX-04/R-ESP-02; gesso tem LEO (ACGIH), logo não é PNOS do Quadro 2 do Anexo III
# NR-07 — predicado próprio, fora de pnos_*.
_por_filtro("gesso", lambda r: r.agente == "poeira_de_gesso")
# R-ESP-02; NR-07 Anexo III item 3.1 (Portaria MTP 567/2022).
_por_filtro("silica", lambda r: r.agente == "silica")
_por_filtro("asbesto", lambda r: r.agente == "asbesto")
_por_filtro("benzeno", lambda r: r.agente == "benzeno")


_NIVEIS_MODERADO_OU_ACIMA: frozenset[str] = frozenset(
    NIVEIS_RISCO_PXS[NIVEIS_RISCO_PXS.index("MODERADO"):]
)


# R-CLI-05 perna (b): agente com indicador biológico no Anexo I da NR-07
# (Quadro 1 ou 2) classificado MODERADO ou acima na avaliação P×S do PGR.
# Risco de FDS ou implícito não traz nível e não conta. [DERIVADO — matriz
# Dra. Patrícia, Aurora 27/08/26, GHE 11: MEK/THF/ciclohexanona MODERADO → 6M].
_por_filtro(
    "agente_ibe_moderado_ou_acima",
    lambda r: r.tipo_ibe is not None and r.nivel_risco in _NIVEIS_MODERADO_OU_ACIMA,
)


_CARGO_PORTEIRO = re.compile(r"\bporteir[oa]s?\b")


@primitivo("cargo_porteiro")
def _cargo_porteiro(ctx: GHEContext) -> bool:
    """R-VIS-02 [VALIDADO]: porteiro recebe acuidade visual sem demissional. Gatilho
    pelo cargo do PGR, normalizado — a Fase B só casa o cargo pela chave exata do
    vocabulário e "Porteiro" nunca vira `porteiro`."""
    for cargo in ctx.pgr_ghe.cargos:
        sem_acento = unicodedata.normalize("NFKD", str(cargo))
        normalizado = "".join(c for c in sem_acento if not unicodedata.combining(c)).casefold()
        if _CARGO_PORTEIRO.search(normalizado):
            return True
    return False


@primitivo("silica_asbesto_sem_medicao", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_asbesto_sem_medicao(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.sem_avaliacao_quantitativa and not r.apenas_qualitativa


@primitivo("silica_qualitativa", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_qualitativa(ctx: GHEContext) -> ResultadoPredicado:
    """R-RX-01-qual (DT-003EC-01): sílica sem avaliação quantitativa, com
    avaliação qualitativa P×S no PGR. Disjunto de silica_asbesto_sem_medicao
    por construção — os dois leem o mesmo helper e partem por apenas_qualitativa."""
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.sem_avaliacao_quantitativa and r.apenas_qualitativa


@primitivo("silica_asbesto_leo_ate_10", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_asbesto_leo_ate_10(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT <= _PCT_LEO_BAIXO


@primitivo("silica_asbesto_leo_10_50", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_asbesto_leo_10_50(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_BAIXO < r.pct_LT <= _PCT_LEO_MEDIO


@primitivo("silica_asbesto_leo_50_100", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_asbesto_leo_50_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_MEDIO < r.pct_LT <= _PCT_LEO_ALTO


@primitivo("silica_asbesto_leo_acima_100", riscos=_risco_unico(_risco_silica_asbesto))
def _silica_asbesto_leo_acima_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_silica_asbesto(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT > _PCT_LEO_ALTO


# R-ESP-02; NR-07 Anexo III item 3.1 (Portaria MTP 567/2022). Único consumidor em
# runtime: R-ESP-02 — R-RX-01-pnos é DEPRECATED e filtrada pelo carregador; as faixas
# de RX usam pnos_leo_*/pnos_sem_medicao, não este.
_por_filtro("pnos", lambda r: r.agente == "poeira_nao_classificada")


# Quadro 2 Anexo III NR-07 (Portaria 567/2022) — PNOS [DERIVADO — 002.X/002.Y]
# Faixas agrupam diferente do Quadro 1: ate_10 (≤10), 10_100 (>10 e ≤100), acima_100 (>100)
def _risco_pnos(ctx: GHEContext) -> Optional[Risco]:
    return next((r for r in ctx.riscos if r.agente == "poeira_nao_classificada"), None)


def _helper_pnos(ctx: GHEContext) -> Union[Quantificacao, bool, Ausente]:
    risco = _risco_pnos(ctx)
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


@primitivo("pnos_sem_medicao", riscos=_risco_unico(_risco_pnos))
def _pnos_sem_medicao(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.sem_avaliacao_quantitativa


@primitivo("pnos_leo_ate_10", riscos=_risco_unico(_risco_pnos))
def _pnos_leo_ate_10(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and r.pct_LT <= _PCT_LEO_BAIXO


@primitivo("pnos_leo_10_100", riscos=_risco_unico(_risco_pnos))
def _pnos_leo_10_100(ctx: GHEContext) -> ResultadoPredicado:
    r = _helper_pnos(ctx)
    if not isinstance(r, Quantificacao):
        return r
    return r.pct_LT is not None and _PCT_LEO_BAIXO < r.pct_LT <= _PCT_LEO_ALTO


@primitivo("pnos_leo_acima_100", riscos=_risco_unico(_risco_pnos))
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


def serializar_predicado(expr: object) -> str:
    if isinstance(expr, str):
        return expr
    if isinstance(expr, dict):
        if "e" in expr:
            return f"e({', '.join(serializar_predicado(f) for f in expr['e'])})"
        if "ou" in expr:
            return f"ou({', '.join(serializar_predicado(f) for f in expr['ou'])})"
        if "nao" in expr:
            return f"nao({serializar_predicado(expr['nao'])})"
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
                nome = filho if isinstance(filho, str) else serializar_predicado(filho)
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
    a perna literal quando string, ou a serialização de `serializar_predicado`
    quando sub-expressão."""
    acc: list[tuple[str, Ausente]] = []
    _coletar_pernas_ausentes_absorvidas(expr, ctx, protocolo, acc)
    return tuple(acc)


def _coletar_pernas_ausentes(
    expr: Any,
    ctx: GHEContext,
    protocolo: Any,
    acc: list[tuple[str, Ausente]],
    _visitados: frozenset[str] = frozenset(),
) -> None:
    if isinstance(expr, str):
        # Armadilha nomeada (D-ARQ-68 cl.5): ao contrário de
        # `_coletar_pernas_ausentes_absorvidas`, aqui o primitivo/composto
        # string É avaliado e coletado por si — sem isto, `quando:` de string
        # simples devolveria conjunto vazio mesmo quando o primitivo é Ausente.
        valor = avaliar(expr, ctx, protocolo, _visitados)
        if isinstance(valor, Ausente):
            acc.append((expr, valor))
        compostos: dict[str, Any] = protocolo.predicados_compostos
        if expr in compostos and expr not in _visitados:
            _coletar_pernas_ausentes(
                compostos[expr], ctx, protocolo, acc, _visitados | {expr}
            )
        return
    if not isinstance(expr, dict):
        return
    if "ou" in expr:
        for filho in expr["ou"]:
            # Diferença única frente a `_coletar_pernas_ausentes_absorvidas`:
            # sem o gate `alguma_true` — toda perna Ausente é coletada, haja
            # ou não perna True no mesmo `ou`. Filhos string são cobertos pela
            # própria recursão (ramo acima); só sub-expressão (dict) precisa
            # de avaliação própria aqui, para não coletar em duplicidade.
            if isinstance(filho, dict):
                valor = avaliar(filho, ctx, protocolo, _visitados)
                if isinstance(valor, Ausente):
                    acc.append((serializar_predicado(filho), valor))
            _coletar_pernas_ausentes(filho, ctx, protocolo, acc, _visitados)
    elif "e" in expr:
        for filho in expr["e"]:
            _coletar_pernas_ausentes(filho, ctx, protocolo, acc, _visitados)
    elif "nao" in expr:
        _coletar_pernas_ausentes(expr["nao"], ctx, protocolo, acc, _visitados)


def pernas_ausentes(
    expr: Any, ctx: GHEContext, protocolo: Any
) -> tuple[tuple[str, Ausente], ...]:
    """D-ARQ-68 cl.5: irmã de `pernas_ausentes_absorvidas`, mesma assinatura,
    mesma ordem estável, mesma expansão de composto nomeado, mesma guarda de
    ciclo. Diferença única no nó `ou`: sem o gate `alguma_true` — coleta toda
    perna Ausente do `ou`, haja ou não perna True (aqui não há absorção a
    detectar: o objetivo é enumerar TODO primitivo ausente que a regra
    precisaria para decidir, para a presunção declarada de D-ARQ-68 cl.5
    poder checar se cobre todos eles). `avaliar`/`avaliar_predicado`
    intocados."""
    acc: list[tuple[str, Ausente]] = []
    _coletar_pernas_ausentes(expr, ctx, protocolo, acc)
    return tuple(acc)


@dataclass(frozen=True)
class RiscoDaPerna:
    perna: str
    risco: Risco
    presumida: bool


def _riscos_da_folha(nome: str, ctx: GHEContext, protocolo: Any) -> tuple[Risco, ...]:
    if nome in REGISTRO_RISCOS:
        return REGISTRO_RISCOS[nome](ctx)
    if nome in REGISTRO_PRIMITIVOS:
        return ()
    # Fallback por identidade de agente (D-ARQ-58), o mesmo de avaliar_predicado.
    return tuple(r for r in ctx.riscos if r.agente == nome)


def _coletar_riscos_das_pernas(
    expr: Any,
    ctx: GHEContext,
    protocolo: Any,
    presumidos: frozenset[str],
    acc: list[RiscoDaPerna],
    _visitados: frozenset[str] = frozenset(),
) -> None:
    if isinstance(expr, str):
        valor = avaliar(expr, ctx, protocolo)
        compostos: dict[str, Any] = protocolo.predicados_compostos
        if expr in compostos:
            if expr in _visitados:
                return
            if valor is True or (isinstance(valor, Ausente) and presumidos):
                _coletar_riscos_das_pernas(
                    compostos[expr], ctx, protocolo, presumidos, acc, _visitados | {expr}
                )
            return
        if valor is True:
            presumida = False
        elif isinstance(valor, Ausente) and expr in presumidos:
            presumida = True
        else:
            return
        acc.extend(RiscoDaPerna(expr, r, presumida) for r in _riscos_da_folha(expr, ctx, protocolo))
        return
    if not isinstance(expr, dict):
        return
    if "ou" in expr:
        for filho in expr["ou"]:
            _coletar_riscos_das_pernas(filho, ctx, protocolo, presumidos, acc, _visitados)
    elif "e" in expr:
        valor_e = avaliar(expr, ctx, protocolo)
        if valor_e is True or (isinstance(valor_e, Ausente) and presumidos):
            for filho in expr["e"]:
                _coletar_riscos_das_pernas(filho, ctx, protocolo, presumidos, acc, _visitados)
    # `nao` não contribui: negação não tem risco a apontar (D-ARQ-88 cl.1).


def riscos_das_pernas_verdadeiras(
    expr: Any,
    ctx: GHEContext,
    protocolo: Any,
    presumidos: frozenset[str] = frozenset(),
) -> tuple[RiscoDaPerna, ...]:
    """D-ARQ-88 cl.1-2: os riscos do GHE que satisfazem cada perna verdadeira
    de uma regra que emitiu. Molde de `pernas_ausentes_absorvidas` (D-ARQ-71):
    passada separada, `avaliar`/`avaliar_predicado` intocados. No `ou`, toda
    perna True contribui, não só a primeira; `e` True desce em todas; composto
    nomeado é expandido com guarda de ciclo. Perna `Ausente` só contribui, com
    `presumida=True`, quando a regra emitiu por presunção e o nome está em
    `presumidos` (`quando_ausente.presumir_true`, D-ARQ-68 cl.5). Avalia sobre
    cópia do cache: `ctx.predicados` não muda, logo `predicados_avaliados`
    também não. Ordem estável de ocorrência; o mesmo risco entra uma vez."""
    copia = replace(ctx, predicados=dict(ctx.predicados))
    acc: list[RiscoDaPerna] = []
    _coletar_riscos_das_pernas(expr, copia, protocolo, presumidos, acc)
    vistos: set[int] = set()
    unicos: list[RiscoDaPerna] = []
    for item in acc:
        if id(item.risco) not in vistos:
            vistos.add(id(item.risco))
            unicos.append(item)
    return tuple(unicos)


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
