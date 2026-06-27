from __future__ import annotations

import dataclasses

from agente_medico.motor.resolvedor import EntradaIndice, gate_cas
from agente_medico.motor.tipos import Componente, FDS, GHEPGR, PGR, Pendencia, ProdutoQuimico


def _normalizar_faixa(componente: Componente) -> Componente:
    """Canonicaliza a ordem da faixa de concentração transcrita verbatim da FDS.
    D-ARQ-43 P2: P2a (par invertido, ex. 0,2-0,05) -> (0.05, 0.2); P2b (piso-textual
    00-10) -> (0.0, 10.0), sem inverter. min()/max() cobre ambos sem ramo condicional.
    Só normaliza quando minimo E maximo são não-None: None é sentinela de faixa
    semi-aberta (piso_efetivo/teto_efetivo), nunca valor comparável (D-ARQ-34 P1).
    Sem faixa (concentracao None) -> intocado. Frozen: reescrita via replace (D-ARQ-09).
    """
    faixa = componente.concentracao
    if faixa is None or faixa.minimo is None or faixa.maximo is None:
        return componente
    lo = min(faixa.minimo, faixa.maximo)
    hi = max(faixa.minimo, faixa.maximo)
    if lo == faixa.minimo and hi == faixa.maximo:
        return componente
    faixa_nova = dataclasses.replace(faixa, minimo=lo, maximo=hi)
    return dataclasses.replace(componente, concentracao=faixa_nova)


def resolver_composicao(
    pgr: PGR, indice_cas: dict[str, EntradaIndice]
) -> tuple[PGR, list[Pendencia]]:
    """Motor irmão mínimo: resolve CAS de cada Componente da FDS via gate_cas.

    D-ARQ-36 nota 003.V (a); D-ARQ-33 cl.1/2 (engenheiro resolve, não emite Risco).
    Remontagem da cascata frozen via dataclasses.replace — DELIBERADA por pureza
    (D-ARQ-09: não mutar objetos frozen, não afrouxar a invariante).

    Pendências do gate são ACUMULADAS e retornadas no [1] (D-ARQ-37 forma α, 003.Z).
    Sem ghe_id — gate a montante da mesa de GHE, pendência global. Costura ao Resultado
    via executar_com_composicao (orquestrador).

    ISOLADO nesta fatia: executar() e orquestrador INTOCADOS. Nasce sem chamador no
    pipeline — plug é fatia seguinte (espelha 003.J/003.S).
    """
    ghes_novos: list[GHEPGR] = []
    pendencias_gate: list[Pendencia] = []
    for ghe in pgr.ghes:
        produtos_novos: list[ProdutoQuimico] = []
        for produto in ghe.produtos_quimicos:
            if produto.fds is None:
                produtos_novos.append(produto)
                continue
            componentes_novos: list[Componente] = []
            for c in produto.fds.composicao:
                c = _normalizar_faixa(c)
                comp_novo, pend = gate_cas(c, indice_cas)
                componentes_novos.append(comp_novo)
                if pend is not None:
                    pendencias_gate.append(pend)
            fds_nova = dataclasses.replace(produto.fds, composicao=tuple(componentes_novos))
            produtos_novos.append(dataclasses.replace(produto, fds=fds_nova))
        ghes_novos.append(dataclasses.replace(ghe, produtos_quimicos=tuple(produtos_novos)))
    return dataclasses.replace(pgr, ghes=tuple(ghes_novos)), pendencias_gate
