from __future__ import annotations

from agente_medico.motor.tipos import ExameEmitido, Momento, Motivo


class ConflitoProtocolo(RuntimeError):
    """Duas regras divergem em periodicidade para o mesmo exame."""


def stage_8_consolidacao(exames: list[ExameEmitido]) -> list[ExameEmitido]:
    """
    R-GHE-03: dedup por slug canônico de exame.

    Regras (D-ARQ-39):
    - Mesmo exame normalizado → MERGE:
        periodicidade_meses = min componente a componente (mais frequente cobre menos frequente);
            0 ("sem periódico") perde para qualquer periodicidade
        periodicidade_apos_15a = min componente a componente, None tratado como +infinito
            nos dois lados (resultado None só quando AMBOS os lados são None)
        momentos = união dos sets
        motivos  = concatenação preservando ordem (sem dedup de Motivo)
        pendencias_anexadas = concatenação preservando ordem
        mantém primeira ocorrência (string exame e ordem na lista)

    Periodicidade divergente entre regras convergentes no mesmo exame nunca é
    contradição de protocolo — é composição resolvível célula a célula por piso
    (D-ARQ-39). `ConflitoProtocolo` permanece definido como veículo de captura
    por-GHE (D-ARQ-15) para outros call-sites, mas este estágio não o dispara mais.

    Identidade do exame: slug canônico do vocabulário (já normalizado por construção).

    Função pura. Não muta entrada. Retorna lista nova preservando ordem de
    primeira ocorrência.
    """
    indices: dict[str, int] = {}
    result: list[ExameEmitido] = []

    for exame in exames:
        norm = exame.exame

        if norm not in indices:
            indices[norm] = len(result)
            result.append(
                ExameEmitido(
                    exame=exame.exame,
                    periodicidade_meses=exame.periodicidade_meses,
                    momentos=set(exame.momentos),
                    motivos=list(exame.motivos),
                    periodicidade_apos_15a=exame.periodicidade_apos_15a,
                    pendencias_anexadas=list(exame.pendencias_anexadas),
                )
            )
        else:
            existing = result[indices[norm]]
            existing.periodicidade_meses = _piso_periodicidade(
                existing.periodicidade_meses, exame.periodicidade_meses
            )
            existing_apos_15a = (
                existing.periodicidade_apos_15a
                if existing.periodicidade_apos_15a is not None
                else float("inf")
            )
            exame_apos_15a = (
                exame.periodicidade_apos_15a
                if exame.periodicidade_apos_15a is not None
                else float("inf")
            )
            piso_apos_15a = min(existing_apos_15a, exame_apos_15a)
            existing.periodicidade_apos_15a = (
                None if piso_apos_15a == float("inf") else int(piso_apos_15a)
            )
            existing.momentos |= exame.momentos
            existing.motivos.extend(exame.motivos)
            existing.pendencias_anexadas.extend(exame.pendencias_anexadas)

    return result


def _piso_periodicidade(a: int, b: int) -> int:
    """0 é "sem periódico" (só os momentos da linha, ex.: R-RX-01-adm), não o intervalo mais
    curto: perde para qualquer periodicidade. Medido: Viverde Acab-05, RX só admissional da
    sílica (pior caso, D-ARQ-68 cl.3) + RX 60M do PNOS saía 0 e apagava os 60M (14/10/2026)."""
    if a == 0 or b == 0:
        return max(a, b)
    return min(a, b)

