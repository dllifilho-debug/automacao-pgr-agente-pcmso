"""Sugestão de exames para o ASO, por linha da matriz (D-ARQ-91).

Roda depois da consolidação, sobre as linhas já emitidas e os riscos do GHE:
não emite, não dispensa e não muda exame nenhum — só diz, para cada linha, se
o exame é obrigatório pelos critérios da NR-07 (e então consta no ASO, item
7.5.19.1 "d"), se não é obrigatório pelo critério (sugestão: não solicitar) ou
se o app não tem o dado para decidir (conferir). A médica valida depois, como
valida a matriz.
"""
from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from agente_medico.motor.classificacao_ruido import classificar_ruido
from agente_medico.motor.leo_resolver import avaliar_medicao_quimica
from agente_medico.motor.tipos import (
    NIVEIS_RISCO_PXS,
    Criterio,
    ExameEmitido,
    RelatorioASO,
    Risco,
    SugestaoASO,
    Veredito,
)

_PRIORIDADE: dict[Veredito, int] = {"OBRIGATORIO": 0, "CONFERIR": 1, "NAO_OBRIGATORIO": 2}

EXAME_CLINICO = "exame_clinico"
AUDIOMETRIA = "audiometria"
RUIDO = "ruido"

# R-ASO-02: regras que materializam o NR-07 Anexo III item 1 (poeira mineral).
_PREFIXOS_ANEXO_III: tuple[str, ...] = ("R-RX-01", "R-ESP-02")

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

_NOTA_BAIXO = (
    "passa a obrigatório se o PGR indicar monitoramento desde a classificação baixa ou "
    "medidas de prevenção imediatas (NR-07 item 7.5.12 \"a\"/\"b\") — o app não lê isso do PGR"
)


def _moderado_ou_acima(nivel: str) -> bool:
    return nivel in NIVEIS_RISCO_PXS and NIVEIS_RISCO_PXS.index(nivel) >= _NIVEL_MODERADO


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
        texto = f"{risco.agente}: avaliado na matriz AIHA do PGR — nível não lido pelo app"
    elif risco.fonte == "explicito":
        texto = f"{risco.agente}: o PGR não traz classificação na linha do risco"
    else:
        texto = f"{risco.agente}: risco sem classificação do PGR (origem {risco.fonte})"
    return Criterio("CONFERIR", "R-ASO-06", texto)


def _criterio_cancerigeno(risco: Risco, agentes_vocab: Mapping[str, Any]) -> Criterio | None:
    """R-ASO-04 — NR-07 Anexo V item 4.1.1: exame do exposto a cancerígeno é obrigatório
    acima de 10% do limite de exposição ou sem avaliação ambiental. Cancerígeno pelo
    `is_carcinogeno_iarc` do vocabulário (o PGR não traz o campo)."""
    if (agentes_vocab.get(risco.agente) or {}).get("is_carcinogeno_iarc") is not True:
        return None
    if _sem_avaliacao_ambiental(risco):
        return Criterio(
            "OBRIGATORIO", "R-ASO-04",
            f"{risco.agente}: cancerígeno sem avaliação ambiental (NR-07 Anexo V item 4.1.1)",
        )
    pct = _pct_limite(risco, agentes_vocab)
    if pct is None:
        return Criterio(
            "CONFERIR", "R-ASO-04",
            f"{risco.agente}: cancerígeno com medição sem limite de exposição de referência",
        )
    if pct > _PCT_CANCERIGENO:
        return Criterio(
            "OBRIGATORIO", "R-ASO-04",
            f"{risco.agente}: cancerígeno a {pct:.0f}% do limite, acima de 10% "
            "(NR-07 Anexo V item 4.1.1)",
        )
    return Criterio(
        "NAO_OBRIGATORIO", "R-ASO-04",
        f"{risco.agente}: cancerígeno a {pct:.0f}% do limite, até 10% (NR-07 Anexo V item 4.1.1)",
    )


def _medicao_acima_nivel_acao(risco: Risco, agentes_vocab: Mapping[str, Any]) -> str | None:
    q = risco.quantificacao
    if q is None or q.apenas_qualitativa or q.valor is None:
        return None
    limiar = _NIVEL_ACAO_VIBRACAO.get(risco.agente)
    if limiar is not None:
        if q.unidade in _UNIDADES_ACELERACAO and q.valor > limiar:
            return (
                f"{risco.agente}: aren {q.valor:g} m/s² acima do nível de ação {limiar:g} m/s² "
                "(NR-09 Anexo I itens 5.2.2/5.3.2)"
            )
        return None
    avaliacao = avaliar_medicao_quimica(risco.agente, q, agentes_vocab)
    if avaliacao is not None and not avaliacao.abaixo_nivel_acao:
        return (
            f"{risco.agente}: medição a {avaliacao.pct_limite:.0f}% do LT, acima do nível de ação "
            "(NR-07 item 7.5.12 \"b\" c/c NR-09 item 9.6.1 \"b\")"
        )
    return None


def _criterio_geral(risco: Risco, agentes_vocab: Mapping[str, Any]) -> Criterio:
    """R-ASO-06 — obrigatório com medição acima do nível de ação da NR-09 ou classificação
    do PGR moderada ou acima (NR-07 item 7.5.12 "b"; e-mail da Dra. Carolini, regra
    geral). Baixo/irrelevante: não obrigatório pelo critério. Sem nível: conferir."""
    acima = _medicao_acima_nivel_acao(risco, agentes_vocab)
    if acima is not None:
        return Criterio("OBRIGATORIO", "R-ASO-06", acima)
    nivel = risco.nivel_risco
    if nivel is None:
        return _sem_classificacao(risco)
    if _moderado_ou_acima(nivel):
        return Criterio(
            "OBRIGATORIO", "R-ASO-06",
            f"{risco.agente}: classificado {nivel} no PGR (NR-07 item 7.5.12 \"b\")",
        )
    return Criterio(
        "NAO_OBRIGATORIO", "R-ASO-06", f"{risco.agente}: classificado {nivel} no PGR; {_NOTA_BAIXO}"
    )


def _criterio_ruido(riscos: Sequence[Risco], agentes_vocab: Mapping[str, Any]) -> list[Criterio]:
    """R-ASO-05 — audiometria obrigatória com ruído ≥ 80 dB(A) (NR-07 Anexo II item 2;
    NR-09 item 9.6.1 "c", R-RUIDO-01), classificação moderada ou acima, ou classificação
    baixa com ototóxico ou vibração no GHE (Anexo II item 7; e-mail da Dra. Carolini)."""
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
        nivel = risco.nivel_risco
        if q is not None and q.valor is not None and relacao in _RUIDO_ACIMA_ACAO:
            criterios.append(Criterio(
                "OBRIGATORIO", "R-ASO-05",
                f"ruído {q.valor:g} dB(A), ≥ 80 dB(A) (NR-07 Anexo II item 2)",
            ))
        elif nivel is not None and _moderado_ou_acima(nivel):
            criterios.append(Criterio("OBRIGATORIO", "R-ASO-05", f"ruído classificado {nivel} no PGR"))
        elif nivel == "BAIXO" and agravante:
            criterios.append(Criterio(
                "OBRIGATORIO", "R-ASO-05",
                "ruído classificado BAIXO com ototóxico ou vibração no GHE (NR-07 Anexo II item 7)",
            ))
        elif nivel is not None:
            agravo = "" if nivel == "BAIXO" else ", nível abaixo de BAIXO"
            criterios.append(Criterio(
                "NAO_OBRIGATORIO", "R-ASO-05",
                f"ruído classificado {nivel} no PGR, sem medição ≥ 80 dB(A)"
                + (agravo if agravante else ", sem ototóxico nem vibração no GHE"),
            ))
        else:
            criterios.append(_sem_classificacao(risco))
    return criterios


def _criterios_da_linha(
    linha: ExameEmitido, riscos: Sequence[Risco], agentes_vocab: Mapping[str, Any]
) -> list[Criterio]:
    if linha.exame == EXAME_CLINICO:
        # R-ASO-01 — NR-07 item 7.5.19.1 "d": o exame clínico consta sempre no ASO.
        return [Criterio("OBRIGATORIO", "R-ASO-01", "exame clínico (NR-07 item 7.5.19.1 \"d\")")]
    criterios: list[Criterio] = []
    ruido_avaliado = False
    if linha.exame == AUDIOMETRIA:
        criterios += _criterio_ruido(riscos, agentes_vocab)
        ruido_avaliado = True
    for motivo in linha.motivos:
        if motivo.regra_id.startswith(_PREFIXOS_ANEXO_III):
            criterios.append(Criterio(
                "OBRIGATORIO", "R-ASO-02",
                f"poeira mineral, {motivo.regra_id} (NR-07 Anexo III item 1)",
            ))
            continue
        if not motivo.origens:
            criterios.append(Criterio(
                "CONFERIR", "R-ASO-06",
                f"{motivo.regra_id}: a regra não parte de um risco classificado do GHE",
            ))
            continue
        for origem in motivo.origens:
            if origem.presumida:
                criterios.append(Criterio(
                    "CONFERIR", "R-ASO-06",
                    f"{origem.agente}: {motivo.regra_id} emitida com a perna `{origem.perna}` "
                    "presumida pelo app, sem o dado que a confirme",
                ))
            elif origem.agente in _APTIDAO_NR:
                criterios.append(Criterio(
                    "OBRIGATORIO", "R-ASO-03", f"aptidão para {_APTIDAO_NR[origem.agente]}"
                ))
            elif origem.agente == RUIDO:
                if not ruido_avaliado:
                    criterios += _criterio_ruido(riscos, agentes_vocab)
                    ruido_avaliado = True
            else:
                do_agente = [r for r in riscos if r.agente == origem.agente]
                if not do_agente:
                    criterios.append(Criterio(
                        "CONFERIR", "R-ASO-06", f"{origem.agente}: risco de origem fora do GHE"
                    ))
                for risco in do_agente:
                    cancerigeno = _criterio_cancerigeno(risco, agentes_vocab)
                    if cancerigeno is not None:
                        criterios.append(cancerigeno)
                    criterios.append(_criterio_geral(risco, agentes_vocab))
    return criterios


def sugerir_aso(
    linhas: Sequence[ExameEmitido], riscos: Sequence[Risco], agentes_vocab: Mapping[str, Any]
) -> RelatorioASO:
    """Um exame é obrigatório se qualquer critério o obrigar (cada item da NR-07 obriga
    sozinho); senão conferir, se algum critério não pôde decidir; senão não obrigatório."""
    sugestoes: list[SugestaoASO] = []
    for linha in linhas:
        criterios = tuple(dict.fromkeys(_criterios_da_linha(linha, riscos, agentes_vocab)))
        veredito: Veredito = min(
            (c.veredito for c in criterios), key=_PRIORIDADE.__getitem__, default="CONFERIR"
        )
        ordenados = tuple(sorted(criterios, key=lambda c: _PRIORIDADE[c.veredito]))
        sugestoes.append(SugestaoASO(linha.exame, veredito, ordenados))
    aptidoes = tuple(
        f"Consignar aptidão para {_APTIDAO_NR[agente]}"
        for agente in _APTIDAO_NR
        if any(r.agente == agente for r in riscos)
    )
    return RelatorioASO(tuple(sugestoes), aptidoes)
