from __future__ import annotations

import dataclasses

from agente_medico.motor.tipos import BlocoComponente, Componente


def bloco_de(c: Componente) -> BlocoComponente:
    """Embrulha um Componente resolvido-style num BlocoComponente singleton (1->1),
    para alimentar composicao_verbatim em fixtures de teste que não exercitam
    expansão-de-grupo (D-ARQ-45 P1/P2, aplicação 003.BB)."""
    return BlocoComponente(
        concentracao=c.concentracao,
        membros=(dataclasses.replace(c, concentracao=None),),
    )
