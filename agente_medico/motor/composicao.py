from __future__ import annotations

import dataclasses

from agente_medico.motor.resolvedor import EntradaIndice, gate_cas
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


def _explodir_multi_cas(componente: Componente) -> list[Componente]:
    """Explode um bloco "Derivados de:" multi-CAS em N Componente, um por CAS.

    D-ARQ-45 (003.AQ): a FDS declara derivados num bloco único com os CAS empilhados
    numa célula (medição 003.AN: '2634-33-5\\n55965-84-9', separados por \\n pelo
    extract_tables do pdfplumber). Componente.cas é str singular; um CAS-plural é
    mal-formado por construção e cairia espuriamente no ramo (c) cas_invalido do gate.
    Logo a explosão é operação determinística do resolvedor, a MONTANTE do gate_cas
    (D-ARQ-09/41: partir separador é lado-determinístico, nunca LLM).

    Herança-α (D-ARQ-45 Parte 2): cada sub-Componente herda a faixa INTEIRA do bloco
    (replace só troca cas; nome/concentracao/flags herdados) — fiel ao documento,
    sobre-materializa na direção segura (anti-supressão D-ARQ-31/33 cl.5/35 P3).

    Separador = '\\n' literal. [DERIVADO — 003.AN, único separador medido; vírgula/;//
    são especulação sem medição, fora de escopo. Reconhecer "bloco empilhado" vs
    "linhas de tabela separadas" é critério de transcrição, herdado pela IMPL do
    transcritor-FDS (D-ARQ-45 item 2 aberto), não do resolvedor.]

    Idempotente e anti-supressão por construção: single-CAS (sem \\n) -> [componente]
    (objeto original, preserva identidade); cas vazio ou só-espaço -> [componente]
    intacto (segue para o ramo (d) do gate). NUNCA remove componente: piso de 1.
    """
    pedacos = [p.strip() for p in componente.cas.split("\n")]
    pedacos = [p for p in pedacos if p]
    if len(pedacos) <= 1:
        return [componente]
    return [dataclasses.replace(componente, cas=p) for p in pedacos]


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
                for sub in _explodir_multi_cas(c):
                    sub = _normalizar_faixa(sub)
                    comp_novo, pend = gate_cas(sub, indice_cas)
                    componentes_novos.append(comp_novo)
                    if pend is not None:
                        pendencias_gate.append(pend)
            fds_nova = dataclasses.replace(produto.fds, composicao=tuple(componentes_novos))
            produtos_novos.append(dataclasses.replace(produto, fds=fds_nova))
        ghes_novos.append(dataclasses.replace(ghe, produtos_quimicos=tuple(produtos_novos)))
    return dataclasses.replace(pgr, ghes=tuple(ghes_novos)), pendencias_gate
