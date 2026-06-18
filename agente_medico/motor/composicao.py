from __future__ import annotations

import dataclasses

from agente_medico.motor.resolvedor import EntradaIndice, gate_cas
from agente_medico.motor.tipos import FDS, GHEPGR, PGR, ProdutoQuimico


def resolver_composicao(pgr: PGR, indice_cas: dict[str, EntradaIndice]) -> PGR:
    """Motor irmão mínimo: resolve CAS de cada Componente da FDS via gate_cas.

    D-ARQ-36 nota 003.V (a); D-ARQ-33 cl.1/2 (engenheiro resolve, não emite Risco).
    Remontagem da cascata frozen via dataclasses.replace — DELIBERADA por pureza
    (D-ARQ-09: não mutar objetos frozen, não afrouxar a invariante).

    Pendências do gate são DESCARTADAS nesta fatia. Propagação ao Resultado é costura
    posterior fora de escopo — ver DH-003P-01.

    ISOLADO nesta fatia: executar() e orquestrador INTOCADOS. Nasce sem chamador no
    pipeline — plug é fatia seguinte (espelha 003.J/003.S).
    """
    ghes_novos: list[GHEPGR] = []
    for ghe in pgr.ghes:
        produtos_novos: list[ProdutoQuimico] = []
        for produto in ghe.produtos_quimicos:
            if produto.fds is None:
                produtos_novos.append(produto)
                continue
            componentes_novos = tuple(
                gate_cas(c, indice_cas)[0] for c in produto.fds.composicao
            )
            fds_nova = dataclasses.replace(produto.fds, composicao=componentes_novos)
            produtos_novos.append(dataclasses.replace(produto, fds=fds_nova))
        ghes_novos.append(dataclasses.replace(ghe, produtos_quimicos=tuple(produtos_novos)))
    return dataclasses.replace(pgr, ghes=tuple(ghes_novos))
