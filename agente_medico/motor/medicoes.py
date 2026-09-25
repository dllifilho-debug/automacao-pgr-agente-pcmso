"""Medição quantitativa informada na tela → Quantificacao nos riscos do PGR (D-ARQ-86 cl.2/cl.4).

Roda sobre o PGR já hidratado, antes de processar_pgr — mesma costura dos
produtos anexados (D-ARQ-49): nem reparse do PDF, nem LLM. O motor não sabe de
onde veio a Quantificacao; a procedência viaja nela (cl.3).
"""
from __future__ import annotations

import dataclasses
from collections.abc import Mapping, Sequence
from typing import Any

from agente_medico.motor.leo_resolver import avaliar_medicao_quimica
from agente_medico.motor.tipos import PGR, MedicaoInformada, Pendencia, Quantificacao, RiscoPGR


def _quantificacao(medicao: MedicaoInformada) -> Quantificacao:
    return Quantificacao(
        valor=medicao.valor,
        unidade=medicao.unidade,
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        procedencia=medicao.procedencia,
    )


def _pct(agente: str, q: Quantificacao, agentes_vocab: Mapping[str, Any]) -> float | None:
    avaliacao = avaliar_medicao_quimica(agente, q, agentes_vocab)
    return None if avaliacao is None else avaliacao.pct_limite


def _escolher(
    risco: RiscoPGR,
    informada: Quantificacao,
    ghe_id: str,
    agentes_vocab: Mapping[str, Any],
) -> tuple[Quantificacao, Pendencia | None]:
    """cl.4: valor do PGR e valor informado divergentes → pendência e fica o
    maior em % do LT (lado protetivo). Sem LT para comparar, fica o informado."""
    do_pgr = risco.quantificacao
    assert risco.agente is not None
    if do_pgr is None or do_pgr.valor is None:
        return informada, None
    if (do_pgr.valor, do_pgr.unidade) == (informada.valor, informada.unidade):
        return informada, None
    pct_pgr = _pct(risco.agente, do_pgr, agentes_vocab)
    pct_informada = _pct(risco.agente, informada, agentes_vocab)
    escolhida = (
        do_pgr
        if pct_pgr is not None and (pct_informada is None or pct_pgr > pct_informada)
        else informada
    )
    origem = "do PGR" if escolhida is do_pgr else "informado"
    pendencia = Pendencia(
        tipo="medicao_divergente",
        destinatario="elaborador_pgr",
        motivo=(
            f"'{risco.agente}': PGR traz {do_pgr.valor:g} {do_pgr.unidade} e a medição "
            f"informada é {informada.valor:g} {informada.unidade} — usado o valor {origem} "
            f"(maior em % do LT; D-ARQ-86 cl.4)"
        ),
        bloqueante=False,
        ghe_id=ghe_id,
    )
    return escolhida, pendencia


def aplicar_medicoes(
    pgr: PGR, medicoes: Sequence[MedicaoInformada], agentes_vocab: Mapping[str, Any]
) -> tuple[PGR, tuple[Pendencia, ...]]:
    pendencias: list[Pendencia] = []
    ghes = list(pgr.ghes)
    for medicao in medicoes:
        indice = next((i for i, g in enumerate(ghes) if g.id == medicao.ghe_id), None)
        riscos = () if indice is None else ghes[indice].riscos
        if not any(r.agente == medicao.agente for r in riscos):
            pendencias.append(
                Pendencia(
                    tipo="medicao_sem_risco",
                    destinatario="rt",
                    motivo=(
                        f"Medição de '{medicao.agente}' (laudo {medicao.procedencia.laudo}) sem "
                        f"risco desse agente no PGR de {medicao.ghe_id} — não aplicada"
                    ),
                    bloqueante=False,
                    ghe_id=medicao.ghe_id,
                )
            )
            continue
        assert indice is not None
        informada = _quantificacao(medicao)
        novos: list[RiscoPGR] = []
        for risco in riscos:
            if risco.agente != medicao.agente:
                novos.append(risco)
                continue
            escolhida, pendencia = _escolher(risco, informada, medicao.ghe_id, agentes_vocab)
            if pendencia is not None:
                pendencias.append(pendencia)
            novos.append(dataclasses.replace(risco, quantificacao=escolhida))
        ghes[indice] = dataclasses.replace(ghes[indice], riscos=tuple(novos))
    return dataclasses.replace(pgr, ghes=tuple(ghes)), tuple(pendencias)
