from __future__ import annotations

from agente_medico.motor.predicados import avaliar
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import GHEContext


def stage_4_predicados(ctx: GHEContext, protocolo: Protocolo) -> None:
    """
    Pré-popula ctx.predicados com todos os predicados nomeados que
    aparecem nas regras (e seus transitivos via compostos).

    Não cria Pendencia. A criação de pendências bloqueantes por Ausente
    continua em stage_5_emissao, que sabe a política da regra
    (`quando_ausente: false`).

    Idempotente: rodar duas vezes não muda ctx.predicados.
    Função "impura" só no sentido de mutar ctx.predicados — mas o cache
    é semanticamente equivalente a recomputar.
    """
    for regra in protocolo.regras:
        avaliar(regra["quando"], ctx, protocolo)
