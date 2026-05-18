from __future__ import annotations

from agente_medico.motor.tipos import ExameEmitido, Momento, Motivo


class ConflitoProtocolo(RuntimeError):
    """Duas regras divergem em periodicidade para o mesmo exame."""


def stage_8_consolidacao(exames: list[ExameEmitido]) -> list[ExameEmitido]:
    """
    R-GHE-03: dedup por nome de exame (normalizado).

    Regras:
    - Mesmo exame normalizado + mesma periodicidade_meses → MERGE:
        momentos = união dos sets
        motivos  = concatenação preservando ordem (sem dedup de Motivo)
        mantém primeira ocorrência (string exame e ordem na lista)
    - Mesmo exame normalizado + periodicidade_meses DIFERENTE → raise ConflitoProtocolo

    Identidade do exame: nome.strip().lower()

    Função pura. Não muta entrada. Retorna lista nova preservando ordem de
    primeira ocorrência.
    """
    indices: dict[str, int] = {}
    result: list[ExameEmitido] = []

    for exame in exames:
        norm = exame.exame.strip().lower()

        if norm not in indices:
            indices[norm] = len(result)
            result.append(
                ExameEmitido(
                    exame=exame.exame,
                    periodicidade_meses=exame.periodicidade_meses,
                    momentos=set(exame.momentos),
                    motivos=list(exame.motivos),
                )
            )
        else:
            existing = result[indices[norm]]
            if existing.periodicidade_meses != exame.periodicidade_meses:
                regras_a = [m.regra_id for m in existing.motivos]
                regras_b = [m.regra_id for m in exame.motivos]
                raise ConflitoProtocolo(
                    f"Conflito de periodicidade para '{existing.exame}': "
                    f"regras {regras_a} pedem {existing.periodicidade_meses}M; "
                    f"regras {regras_b} pedem {exame.periodicidade_meses}M"
                )
            existing.momentos |= exame.momentos
            existing.motivos.extend(exame.motivos)

    return result
