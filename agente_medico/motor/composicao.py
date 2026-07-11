from __future__ import annotations

import dataclasses

from agente_medico.motor.resolvedor import EntradaIndice, gate_cas, mapear_frases_h
from agente_medico.motor.tipos import (
    BlocoComponente,
    Componente,
    FDS,
    GHEPGR,
    PGR,
    Pendencia,
    ProdutoQuimico,
)


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


def _explodir_bloco(bloco: BlocoComponente) -> tuple[Componente, ...]:
    """Expande um BlocoComponente (grupo verbatim) em N Componente, herdando a faixa do bloco.

    D-ARQ-45 P1/P2 (herança-α): cada membro nasce com concentracao=None (montar_bloco);
    aqui herda a FaixaConcentracao do bloco (replace só troca concentracao) e canonicaliza
    via _normalizar_faixa (D-ARQ-43 P2). Determinístico puro, a MONTANTE do gate_cas
    (D-ARQ-09/41): expandir grupo e herdar faixa é lado-determinístico, nunca LLM.

    Sem gate aqui — gate_cas exige indice_cas, é responsabilidade do resolver (fatia iii).
    Anti-supressão (D-ARQ-31/33): bloco de 1 membro -> tuple de 1; preserva cardinalidade,
    nunca remove membro. cas/nome/flags dos membros intocados (só concentracao muda).
    """
    return tuple(
        _normalizar_faixa(dataclasses.replace(m, concentracao=bloco.concentracao))
        for m in bloco.membros
    )


def resolver_composicao(
    pgr: PGR, indice_cas: dict[str, EntradaIndice]
) -> tuple[PGR, list[Pendencia]]:
    """Motor irmão mínimo: consome fds.composicao_verbatim (tuple[BlocoComponente, ...])
    e escreve fds.composicao resolvida, via _explodir_bloco + gate_cas + mapear_frases_h.

    mapear_frases_h roda em TODOS os ramos do gate_cas, inclusive (c) inválido e
    (d) CAS-oculto (D-ARQ-55 P4): no oculto a flag is_sensibilizante é populada e
    CARREGADA no componente, mas a saída permanece AUSENTE via ramo-0 de
    materialidade() — fronteira deliberada, reordenar o ramo-0 é o passo 2, fora
    de escopo desta fatia.

    D-ARQ-36 nota 003.V (a); D-ARQ-33 cl.1/2 (engenheiro resolve, não emite Risco).
    D-ARQ-45 P1/P2 (aplicação 003.BB): _explodir_bloco já normaliza a faixa (herança-α +
    _normalizar_faixa) — sem chamada separada de _normalizar_faixa neste loop.
    composicao_verbatim é preservado (replace só troca composicao, decisão "manter").
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
            for bloco in produto.fds.composicao_verbatim:
                for sub in _explodir_bloco(bloco):
                    comp_novo, pend = gate_cas(sub, indice_cas)
                    if pend is not None:
                        pendencias_gate.append(pend)
                    comp_novo, pend_h = mapear_frases_h(comp_novo)
                    if pend_h is not None:
                        pendencias_gate.append(pend_h)
                    componentes_novos.append(comp_novo)
            fds_nova = dataclasses.replace(produto.fds, composicao=tuple(componentes_novos))
            produtos_novos.append(dataclasses.replace(produto, fds=fds_nova))
        ghes_novos.append(dataclasses.replace(ghe, produtos_quimicos=tuple(produtos_novos)))
    return dataclasses.replace(pgr, ghes=tuple(ghes_novos)), pendencias_gate
