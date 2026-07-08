"""Hidratação GHEVerbatim -> GHEPGR / PGR (D-ARQ-51 fatia 1b e costura plural).

Consome resolver_termo (resolvedor_termos.py) por risco. Seam 1: GHEPGR.id é
posicional sobre a ordem transcrita ("GHE-01", "GHE-02", ...) — NÃO deriva de
GHEVerbatim.nome (texto livre do LLM colide entre blocos) nem é id canônico
(re-agrupamento MAPA 42->32 é fatia downstream, D-ARQ-50 C1). Seam 4: recorte
de identidade — id, nome, cargos e agente-slug são hidratados; quantificacao
fica None (parse de "6,3 ppm" é fatia resolver-side futura; o texto cru
sobrevive em RiscoVerbatim, GHEVerbatim é preservado a montante). EPIs,
produtos_quimicos, psicossocial e cenario ficam em default (diferidos,
D-ARQ-49 P2). Risco NUNCA descartado (D-ARQ-31/35 P3): tri-estado do
resolver (EXATA/FUZZY/NAO_RESOLVIDO) sempre vira exatamente 1 RiscoPGR.
"""
from __future__ import annotations

import dataclasses
from datetime import date
from typing import Sequence

from agente_medico.motor.resolvedor_termos import Confianca, resolver_termo
from agente_medico.motor.tipos import GHEPGR, PGR, GHEVerbatim, Pendencia, RiscoPGR


def hidratar_ghe(
    ghe: GHEVerbatim,
    indice: dict[str, str],
    posicao: int,
) -> tuple[GHEPGR, list[Pendencia]]:
    """Hidrata um bloco GHE transcrito em GHEPGR + pendências (D-ARQ-51).

    Por RiscoVerbatim, resolve o termo cru contra o índice de vocabulário:
    EXATA -> agente=slug, sem pendência. FUZZY -> agente=slug + Pendencia
    resolucao_fuzzy não-bloqueante (o resolver retorna pendencia=None no
    FUZZY por design — fabricá-la aqui é o "consumidor futuro" a que seu
    docstring delega). NAO_RESOLVIDO -> agente=None + a Pendencia
    vocabulario_ausente que o próprio resolver já emitiu, apenas com ghe_id
    preenchido.
    """
    # Handle do bloco transcrito, NÃO id canônico (D-ARQ-51 seam 1;
    # re-agrupamento 42->32 é fatia downstream).
    ghe_id = f"GHE-{posicao:02d}"

    riscos: list[RiscoPGR] = []
    pendencias: list[Pendencia] = []

    for risco_verbatim in ghe.riscos:
        resolucao = resolver_termo(risco_verbatim.agente, indice)

        if resolucao.confianca == Confianca.EXATA:
            riscos.append(
                RiscoPGR(tipo="", agente=resolucao.slug, quantificacao=None, severidade=None)
            )
        elif resolucao.confianca == Confianca.FUZZY:
            riscos.append(
                RiscoPGR(tipo="", agente=resolucao.slug, quantificacao=None, severidade=None)
            )
            pendencias.append(
                Pendencia(
                    tipo="resolucao_fuzzy",
                    destinatario="extracao",
                    motivo=(
                        f"termo '{risco_verbatim.agente}' resolvido por aproximação a "
                        f"'{resolucao.slug}' — revisão recomendada"
                    ),
                    bloqueante=False,
                    regra_origem="D-ARQ-51",
                    ghe_id=ghe_id,
                )
            )
        else:
            # Invariante: agente=None sempre pareado com exatamente 1 pendência —
            # o guard da Fase A (estagios/riscos.py, 1a) confia nisso (D-ARQ-51 seam 3).
            riscos.append(RiscoPGR(tipo="", agente=None, quantificacao=None, severidade=None))
            # Erro-zero (D-ARQ-22): NAO_RESOLVIDO sem pendência é violação de contrato
            # do resolver — estourar aqui, nunca produzir agente=None órfão (seam 3).
            assert resolucao.pendencia is not None
            pendencias.append(dataclasses.replace(resolucao.pendencia, ghe_id=ghe_id))

    ghe_pgr = GHEPGR(
        id=ghe_id,
        nome=ghe.nome,
        cargos=ghe.cargos,
        riscos=tuple(riscos),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
        cenario=None,
    )
    return ghe_pgr, pendencias


def hidratar_pgr(
    ghes: Sequence[GHEVerbatim],
    indice: dict[str, str],
    validade: date,
    assinatura_engenheiro: bool,
) -> tuple[PGR, list[Pendencia]]:
    """Hidrata a sequência de blocos GHE transcritos em PGR (D-ARQ-51 costura plural).

    Consumidor de produção de hidratar_ghe: itera os blocos na ordem transcrita
    e delega cada um (a posição 1-based, seam 1, vem daqui), agregando as
    pendências de todos os blocos numa lista única na mesma ordem. validade e
    assinatura_engenheiro são envelope por parâmetro obrigatório, sem default —
    a FONTE desses campos é a transcrição de topo do documento, fatia futura;
    o parâmetro não inventa dado (D-ARQ-22), apenas repassa verbatim ao PGR.
    """
    ghes_pgr: list[GHEPGR] = []
    pendencias: list[Pendencia] = []

    for posicao, ghe in enumerate(ghes, start=1):
        ghe_pgr, pendencias_ghe = hidratar_ghe(ghe, indice, posicao)
        ghes_pgr.append(ghe_pgr)
        pendencias.extend(pendencias_ghe)

    pgr = PGR(
        validade=validade,
        assinatura_engenheiro=assinatura_engenheiro,
        ghes=tuple(ghes_pgr),
    )
    return pgr, pendencias
