"""Sugestão dos riscos que constam no ASO, por risco do GHE (D-ARQ-91, emenda de 07/10/2026).

O ASO traz "a descrição dos perigos ou fatores de risco identificados e classificados no
PGR que necessitem de controle médico previsto no PCMSO, ou a sua inexistência" (NR-07
item 7.5.19.1 "c"). Roda depois da consolidação, sobre os riscos do GHE: não emite, não
dispensa e não muda exame nenhum — só diz, para cada risco, se consta no ASO, se não
consta pelo critério ou se o app não tem o dado para decidir (conferir). A médica valida
depois, como valida a matriz.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agente_medico.motor.classificacao_ruido import classificar_ruido
from agente_medico.motor.leo_resolver import PNOS, SILICA, avaliar_medicao_quimica
from agente_medico.motor.niveis_pgr import classificar_nivel_pgr
from agente_medico.motor.tipos import (
    NIVEIS_RISCO_PXS,
    Criterio,
    ExameEmitido,
    RelatorioASO,
    Risco,
    RiscoPGR,
    SugestaoASO,
    VereditoASO,
)

_PRIORIDADE: dict[VereditoASO, int] = {"CONSTA": 0, "CONFERIR": 1, "NAO_CONSTA": 2}

RUIDO = "ruido"

# R-ASO-02: os agentes do composto `poeira_mineral` (predicados_compostos.yaml), que
# R-RX-01 e R-ESP-02 levam ao NR-07 Anexo III item 1.
_POEIRA_MINERAL = frozenset({SILICA, "asbesto", PNOS})

# R-ASO-03: atividades com aptidão consignada no ASO por NR (NR-07 7.5.19.2).
_APTIDAO_NR: dict[str, str] = {
    "trabalho_altura": "trabalho em altura (NR-07 item 7.5.19.2 c/c NR-35 item 35.4.4.1)",
    "espaco_confinado": "trabalho em espaço confinado (NR-07 item 7.5.19.2 c/c NR-33 item 33.5.19.2)",
}

_VIBRACAO = frozenset({"vibracao", "vibracao_corpo_inteiro", "vibracao_mao_braco"})
# R-ASO-06: nível de ação da vibração em aren (m/s²), NR-09 Anexo I itens 5.2.2 e 5.3.2.
_NIVEL_ACAO_VIBRACAO: dict[str, float] = {"vibracao_mao_braco": 2.5, "vibracao_corpo_inteiro": 0.5}
_UNIDADES_ACELERACAO = frozenset({"m/s2", "m/s²"})

_RUIDO_ACIMA_ACAO = frozenset({"entre_acao_LT", "acima_LT", "acima_acao"})
_NIVEL_MODERADO = NIVEIS_RISCO_PXS.index("MODERADO")
_PCT_CANCERIGENO = 10.0

_NOTA_MODERADO = "moderado ou acima consta (e-mail da Dra. Carolini; NR-07 item 7.5.19.1 \"c\")"

# R-ASO-06 (D-ARQ-91 emenda 2): grupos do PGR que nenhuma exceção do e-mail (ruído,
# vibração, químicos, poeiras, cancerígenos, agentes sem LT) alcança.
_GRUPOS_SEM_EXCECAO = frozenset({"ACIDENTE", "ERGONOMICO"})
_MARCAS_APTIDAO = ("altura", "confinad")

_NOTA_BAIXO = (
    "passa a constar se o PGR indicar monitoramento desde a classificação baixa ou "
    "medidas de prevenção imediatas (NR-07 item 7.5.12 \"a\"/\"b\") — o app não lê isso do PGR"
)


def _moderado_ou_acima(nivel: str) -> bool:
    return nivel in NIVEIS_RISCO_PXS and NIVEIS_RISCO_PXS.index(nivel) >= _NIVEL_MODERADO


def _nivel(
    nivel_risco: str | None, nivel_pgr: str, niveis: Mapping[str, Any]
) -> tuple[str, bool] | None:
    """(rótulo, moderado ou acima). O nível P×S, quando há, decide como sempre; sem ele,
    o rótulo que o PGR escreve em outra escala, pelo vocabulário `niveis_risco.yaml`
    (D-ARQ-95). Rótulo desconhecido ou conflitante: None — conferir."""
    if nivel_risco is not None:
        return nivel_risco, _moderado_ou_acima(nivel_risco)
    achado = classificar_nivel_pgr(nivel_pgr, niveis)
    return (achado.rotulo, achado.posicao == "corte") if achado is not None else None


def _pct_limite(risco: Risco, agentes_vocab: Mapping[str, Any]) -> float | None:
    q = risco.quantificacao
    if q is None:
        return None
    avaliacao = avaliar_medicao_quimica(risco.agente, q, agentes_vocab)
    if avaliacao is not None:
        return avaliacao.pct_limite
    return q.pct_LT


def _sem_avaliacao_ambiental(risco: Risco) -> bool:
    q = risco.quantificacao
    return q is None or q.apenas_qualitativa or q.sem_avaliacao_quantitativa or q.valor is None


def _sem_classificacao(risco: Risco) -> Criterio:
    """D-ARQ-22: o que o app não classifica aparece como conferir, nunca some."""
    if risco.avaliacao_qualitativa_aiha:
        texto = "avaliado na matriz AIHA do PGR — nível não lido pelo app"
    elif risco.fonte == "explicito":
        texto = "o PGR não traz classificação na linha do risco"
    else:
        texto = f"risco sem classificação do PGR (origem {risco.fonte})"
    return Criterio("CONFERIR", "R-ASO-06", texto)


def _criterio_cancerigeno(risco: Risco, agentes_vocab: Mapping[str, Any]) -> Criterio | None:
    """R-ASO-04 — NR-07 Anexo V item 4.1.1: controle médico do exposto a cancerígeno é
    obrigatório acima de 10% do limite de exposição ou sem avaliação ambiental.
    Cancerígeno pelo `is_carcinogeno_iarc` do vocabulário (o PGR não traz o campo)."""
    if (agentes_vocab.get(risco.agente) or {}).get("is_carcinogeno_iarc") is not True:
        return None
    if _sem_avaliacao_ambiental(risco):
        return Criterio(
            "CONSTA", "R-ASO-04", "cancerígeno sem avaliação ambiental (NR-07 Anexo V item 4.1.1)"
        )
    pct = _pct_limite(risco, agentes_vocab)
    if pct is None:
        return Criterio(
            "CONFERIR", "R-ASO-04", "cancerígeno com medição sem limite de exposição de referência"
        )
    if pct > _PCT_CANCERIGENO:
        return Criterio(
            "CONSTA", "R-ASO-04",
            f"cancerígeno a {pct:.0f}% do limite, acima de 10% (NR-07 Anexo V item 4.1.1)",
        )
    return Criterio(
        "NAO_CONSTA", "R-ASO-04",
        f"cancerígeno a {pct:.0f}% do limite, até 10% (NR-07 Anexo V item 4.1.1)",
    )


def _medicao_acima_nivel_acao(risco: Risco, agentes_vocab: Mapping[str, Any]) -> str | None:
    q = risco.quantificacao
    if q is None or q.apenas_qualitativa or q.valor is None:
        return None
    limiar = _NIVEL_ACAO_VIBRACAO.get(risco.agente)
    if limiar is not None:
        if q.unidade in _UNIDADES_ACELERACAO and q.valor > limiar:
            return (
                f"aren {q.valor:g} m/s² acima do nível de ação {limiar:g} m/s² "
                "(NR-09 Anexo I itens 5.2.2/5.3.2)"
            )
        return None
    avaliacao = avaliar_medicao_quimica(risco.agente, q, agentes_vocab)
    if avaliacao is not None and not avaliacao.abaixo_nivel_acao:
        return (
            f"medição a {avaliacao.pct_limite:.0f}% do LT, acima do nível de ação "
            "(NR-07 item 7.5.12 \"b\" c/c NR-09 item 9.6.1 \"b\")"
        )
    return None


def _criterio_geral(risco: Risco, agentes_vocab: Mapping[str, Any], niveis: Mapping[str, Any]) -> Criterio:
    """R-ASO-06 — consta com medição acima do nível de ação da NR-09 (NR-07 item 7.5.12
    "b") ou classificação do PGR moderada ou acima, de qualquer grupo de risco, inclusive
    acidente e ergonômico (e-mail da Dra. Carolini, regra geral, leitura literal — o corte
    é do e-mail; a NR-07 item 7.5.19.1 "c" não fixa nível). Baixo/irrelevante: não consta
    pelo critério. Sem nível: conferir. Nível de outra escala que não a P×S: D-ARQ-95."""
    acima = _medicao_acima_nivel_acao(risco, agentes_vocab)
    if acima is not None:
        return Criterio("CONSTA", "R-ASO-06", acima)
    nivel = _nivel(risco.nivel_risco, risco.nivel_pgr, niveis)
    if nivel is None:
        return _sem_classificacao(risco)
    rotulo, corte = nivel
    if corte:
        return Criterio("CONSTA", "R-ASO-06", f"classificado {rotulo} no PGR; {_NOTA_MODERADO}")
    return Criterio("NAO_CONSTA", "R-ASO-06", f"classificado {rotulo} no PGR; {_NOTA_BAIXO}")


def _criterio_termo(risco_pgr: RiscoPGR, niveis: Mapping[str, Any]) -> Criterio:
    """R-ASO-06 para o termo do PGR que o app não reconheceu (D-ARQ-91 emenda 2). A regra
    geral do e-mail decide pela classificação e pelo grupo, sem o agente: moderado ou
    acima consta; abaixo disso, acidente e ergonômico não constam (nenhuma exceção do
    e-mail os alcança); químico, físico e biológico baixos podem cair numa exceção que o
    app não decide sem o agente — conferir. Grupo não lido (rotas da IA): conferir."""
    achado = _nivel(risco_pgr.nivel_risco, risco_pgr.nivel_pgr, niveis)
    grupo = risco_pgr.tipo
    if achado is None:
        return Criterio("CONFERIR", "R-ASO-06", "risco do PGR não reconhecido pelo app, sem classificação — classificar à mão")
    nivel, corte = achado
    if corte:
        return Criterio("CONSTA", "R-ASO-06", f"classificado {nivel} no PGR; {_NOTA_MODERADO}")
    termo = (risco_pgr.termo or "").lower()
    # R-ASO-03: altura e espaço confinado constam sempre, pela aptidão. Variante que o
    # app não reconheceu não pode sair "não consta" só por ser ACIDENTE baixo.
    if any(marca in termo for marca in _MARCAS_APTIDAO):
        return Criterio(
            "CONFERIR", "R-ASO-03",
            f"{grupo or 'risco'} {nivel} não reconhecido que cita altura ou espaço confinado — conferir a aptidão",
        )
    if grupo in _GRUPOS_SEM_EXCECAO:
        return Criterio(
            "NAO_CONSTA", "R-ASO-06",
            f"{grupo} classificado {nivel} no PGR — abaixo de moderado, fora das exceções do e-mail "
            "(ruído, vibração, químicos, poeiras)",
        )
    if grupo:
        return Criterio(
            "CONFERIR", "R-ASO-06",
            f"{grupo} classificado {nivel} no PGR, não reconhecido pelo app — conferir se cabe exceção do "
            "e-mail (químico com monitoramento desde a classificação baixa, poeira mineral, cancerígeno, "
            "ruído com ototóxico/vibração, agente sem limite de tolerância)",
        )
    return Criterio(
        "CONFERIR", "R-ASO-06",
        f"classificado {nivel} no PGR, não reconhecido pelo app e sem grupo lido — classificar à mão",
    )


def _criterio_ruido(
    riscos: Sequence[Risco], agentes_vocab: Mapping[str, Any], niveis: Mapping[str, Any]
) -> list[Criterio]:
    """R-ASO-05 — ruído consta com medição ≥ 80 dB(A) (NR-07 Anexo II item 2; NR-09 item
    9.6.1 "c", R-RUIDO-01), classificação moderada ou acima, ou classificação baixa com
    ototóxico ou vibração no GHE (Anexo II item 7; e-mail da Dra. Carolini)."""
    agravante = any(
        r.is_ototoxico
        or (agentes_vocab.get(r.agente) or {}).get("is_ototoxico") is True
        or r.agente in _VIBRACAO
        for r in riscos
    )
    criterios: list[Criterio] = []
    for risco in (r for r in riscos if r.agente == RUIDO):
        q = risco.quantificacao
        relacao = classificar_ruido(q).relacao_LT if q is not None else None
        achado = _nivel(risco.nivel_risco, risco.nivel_pgr, niveis)
        nivel, corte = achado if achado is not None else (None, False)
        # Na escala P×S só BAIXO conta como "mesmo baixo" do e-mail (IRRELEVANTE não);
        # em outra escala, todo rótulo abaixo do corte — o lado protetivo (D-ARQ-95).
        baixo = risco.nivel_risco == "BAIXO" or (risco.nivel_risco is None and nivel is not None)
        if q is not None and q.valor is not None and relacao in _RUIDO_ACIMA_ACAO:
            criterios.append(
                Criterio("CONSTA", "R-ASO-05", f"{q.valor:g} dB(A), ≥ 80 dB(A) (NR-07 Anexo II item 2)")
            )
        elif nivel is not None and corte:
            criterios.append(Criterio("CONSTA", "R-ASO-05", f"classificado {nivel} no PGR"))
        elif baixo and agravante:
            criterios.append(Criterio(
                "CONSTA", "R-ASO-05",
                f"classificado {nivel} com ototóxico ou vibração no GHE (NR-07 Anexo II item 7)",
            ))
        elif nivel is not None:
            complemento = "" if agravante else ", sem ototóxico nem vibração no GHE"
            criterios.append(Criterio(
                "NAO_CONSTA", "R-ASO-05",
                f"classificado {nivel} no PGR, sem medição ≥ 80 dB(A){complemento}",
            ))
        else:
            criterios.append(_sem_classificacao(risco))
    return criterios


def _criterios_do_agente(
    agente: str, riscos: Sequence[Risco], agentes_vocab: Mapping[str, Any], niveis: Mapping[str, Any]
) -> list[Criterio]:
    if agente in _POEIRA_MINERAL:
        return [Criterio("CONSTA", "R-ASO-02", "poeira mineral (NR-07 Anexo III item 1)")]
    if agente in _APTIDAO_NR:
        return [Criterio("CONSTA", "R-ASO-03", f"aptidão para {_APTIDAO_NR[agente]}")]
    if agente == RUIDO:
        return _criterio_ruido(riscos, agentes_vocab, niveis)
    criterios: list[Criterio] = []
    for risco in (r for r in riscos if r.agente == agente):
        cancerigeno = _criterio_cancerigeno(risco, agentes_vocab)
        if cancerigeno is not None:
            criterios.append(cancerigeno)
        criterios.append(_criterio_geral(risco, agentes_vocab, niveis))
    return criterios


def _consolidar(criterios: Sequence[Criterio]) -> tuple[VereditoASO, tuple[Criterio, ...]]:
    """Um critério que faça constar basta (cada item da NR-07 obriga sozinho); senão
    conferir, se algum critério não pôde decidir; senão não consta."""
    unicos = tuple(dict.fromkeys(criterios))
    veredito: VereditoASO = min(
        (c.veredito for c in unicos), key=_PRIORIDADE.__getitem__, default="CONFERIR"
    )
    return veredito, tuple(sorted(unicos, key=lambda c: _PRIORIDADE[c.veredito]))


def sugerir_aso(
    linhas: Sequence[ExameEmitido],
    riscos: Sequence[Risco],
    riscos_pgr: Sequence[RiscoPGR],
    agentes_vocab: Mapping[str, Any],
    niveis_risco: Mapping[str, Any] | None = None,
) -> RelatorioASO:
    """Uma sugestão por agente do GHE (linhas do PGR do mesmo agente juntas) e uma por
    termo do PGR que não virou agente (CONFERIR, D-ARQ-22). `exames` é informativo: os
    exames da matriz cuja origem é o agente — o ASO traz o risco, não o exame.
    `niveis_risco`: vocabulário de rótulos de nível de outras escalas (D-ARQ-95)."""
    niveis: Mapping[str, Any] = niveis_risco or {}
    sugestoes: list[SugestaoASO] = []
    for agente in dict.fromkeys(r.agente for r in riscos):
        veredito, criterios = _consolidar(_criterios_do_agente(agente, riscos, agentes_vocab, niveis))
        exames = tuple(
            linha.exame
            for linha in linhas
            if any(o.agente == agente for m in linha.motivos for o in m.origens)
        )
        sugestoes.append(SugestaoASO(agente, True, veredito, criterios, exames))
    for termo in dict.fromkeys(r.termo for r in riscos_pgr if r.agente is None and r.termo):
        veredito, criterios = _consolidar(
            [_criterio_termo(r, niveis) for r in riscos_pgr if r.agente is None and r.termo == termo]
        )
        sugestoes.append(SugestaoASO(termo, False, veredito, criterios, ()))
    aptidoes = tuple(
        f"Consignar aptidão para {_APTIDAO_NR[agente]}"
        for agente in _APTIDAO_NR
        if any(r.agente == agente for r in riscos)
    )
    # R-ASO-07 — NR-07 item 7.5.19.1 "c", "ou a sua inexistência": só quando todo risco
    # foi decidido como não consta; havendo conferir, a inexistência não está provada.
    inexistencia = all(s.veredito == "NAO_CONSTA" for s in sugestoes)
    return RelatorioASO(tuple(sugestoes), aptidoes, inexistencia)
