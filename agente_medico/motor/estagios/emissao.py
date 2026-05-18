from __future__ import annotations

from agente_medico.motor.predicados import ResultadoPredicado, avaliar
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import (
    Ausente,
    ExameEmitido,
    GHEContext,
    Momento,
    Motivo,
    Pendencia,
)

_MOMENTOS: dict[str, Momento] = {m.name: m for m in Momento}


def _converter_momento(raw: str, regra_id: str, exame: str) -> Momento:
    key = raw.upper()
    if key not in _MOMENTOS:
        raise ValueError(
            f"Momento inválido '{raw}' na regra '{regra_id}', exame '{exame}'"
        )
    return _MOMENTOS[key]


def stage_5_emissao(ctx: GHEContext, protocolo: Protocolo) -> list[ExameEmitido]:
    """
    Para cada regra em protocolo.regras:
      1. Avaliar expressão `quando` via avaliar(expr, ctx, protocolo).
      2. Se True  → emitir todos os itens de `emite` como ExameEmitido.
      3. Se False → não emite, sem pendência.
      4. Se Ausente:
          - Se regra tem `quando_ausente: false` → trata como False (não emite, sem pendência)
          - Caso contrário → adiciona Pendencia(bloqueante=True) ao ctx.pendencias e não emite
    Retorna lista de ExameEmitido na ordem em que foram emitidos.
    Não muta ctx exceto ctx.pendencias.
    """
    emitidos: list[ExameEmitido] = []

    for regra in protocolo.regras:
        resultado: ResultadoPredicado = avaliar(regra["quando"], ctx, protocolo)

        if isinstance(resultado, Ausente):
            quando_ausente = regra.get("quando_ausente")
            if quando_ausente is False:
                continue
            ctx.pendencias.append(
                Pendencia(
                    tipo="predicado_ausente",
                    destinatario="elaborador_pgr",
                    motivo=(
                        f"Regra {regra['id']}: predicado '{regra['quando']}' "
                        f"não pôde ser avaliado — {resultado.mensagem}"
                    ),
                    bloqueante=True,
                    regra_origem=str(regra["id"]),
                    ghe_id=ctx.pgr_ghe.id,
                )
            )
            continue

        if not resultado:
            continue

        predicado_str = (
            str(regra["quando"])
            if isinstance(regra["quando"], str)
            else "<composto>"
        )
        motivo = Motivo(
            regra_id=str(regra["id"]),
            predicado=predicado_str,
            risco_origem=None,
            detalhe=f"Emitido por regra {regra['id']}",
        )

        for item in regra["emite"]:
            momentos: set[Momento] = {
                _converter_momento(str(m), str(regra["id"]), str(item["exame"]))
                for m in item["momentos"]
            }
            emitidos.append(
                ExameEmitido(
                    exame=str(item["exame"]),
                    periodicidade_meses=int(item["periodicidade_meses"]),
                    momentos=momentos,
                    motivos=[motivo],
                )
            )

    return emitidos
