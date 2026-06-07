from __future__ import annotations

from agente_medico.motor.tipos import ExameEmitido, Pendencia


def anexar_pendencias(
    linhas: list[ExameEmitido],
    bloqueantes: list[Pendencia],
) -> tuple[list[ExameEmitido], list[Pendencia]]:
    """D-ARQ-31 fatia 3: move cada Pendencia bloqueante com âncora para a(s) linha(s)
    cujo slug de exame casa (interseção exames_alvo × slugs presentes).

    Retorna (linhas com pendências anexadas, bloqueantes sem match restantes).
    Pendência sem âncora, ou cuja âncora não casa nenhuma linha emitida, volta como
    restante (fica no nível da matriz — Tipo A, sem linha para escalar).

    Requisito de segurança (D-ARQ-31): toda pendência cuja âncora casa uma linha
    presente É anexada a essa linha por construção — o piso determinado nunca é emitido
    sem o teto pendente visível ao lado. A anexação é total; não há ramo de "piso sem
    teto" porque o slot na linha torna a anexação sempre viável quando há match.

    Muta as linhas recebidas (cópias recém-consolidadas do Stage 8), não a entrada
    original do pipeline — mesmo padrão de mutação-de-cópia-local do Stage 8.
    """
    slugs_presentes = {ln.exame for ln in linhas}
    restantes: list[Pendencia] = []
    for p in bloqueantes:
        alvos = set(p.exames_alvo) & slugs_presentes
        if not alvos:
            restantes.append(p)
            continue
        for ln in linhas:
            if ln.exame in alvos:
                ln.pendencias_anexadas.append(p)
    return linhas, restantes
