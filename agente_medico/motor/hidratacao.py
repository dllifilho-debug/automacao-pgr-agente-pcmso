"""Hidratação GHEVerbatim -> GHEPGR / PGR (D-ARQ-51 fatia 1b e costura plural).

Consome resolver_termo (resolvedor_termos.py) por risco. Seam 1: GHEPGR.id é
posicional sobre a ordem transcrita ("GHE-01", "GHE-02", ...) — NÃO deriva de
GHEVerbatim.nome (texto livre do LLM colide entre blocos) nem é id canônico
(re-agrupamento MAPA 42->32 é fatia downstream, D-ARQ-50 C1). Seam 4: recorte
de identidade — id, nome, cargos e agente-slug são hidratados; quantificacao
é parseada por parsear_quantificacao (D-ARQ-51 fatia 2), independente da
resolução do agente — o parse roda 1x por risco antes do tri-estado. Texto
parseável vira Quantificacao; vazio vira None sem pendência; texto não-vazio
ininteligível vira None + Pendencia quantificacao_nao_parseada não-bloqueante
(anti-supressão D-ARQ-31/35: medição transcrita nunca some em silêncio, o
risco entra mesmo assim). Recorte remanescente: quantificacao de ruído
(slug "ruido", EXATA ou FUZZY) é classificada em relacao_LT por
classificar_ruido (D-ARQ-51 fatia 3, R-RUIDO-01), aplicada pós-resolução do
termo — agente=None não classifica. nivel_risco (DT-003EC-01) é extraído
do texto S·P·NÍVEL da avaliação qualitativa P×S por parsear_nivel_risco;
texto não reconhecido vira Pendencia avaliacao_qualitativa_nao_parseada
não-bloqueante, pelo mesmo motivo da quantificação.
EPIs, produtos_quimicos e cenario ficam em default (diferidos, D-ARQ-49 P2).
psicossocial (R-PSY-03) é populado por parâmetro — o extrator
(detectar_psicossocial, extracao_pgr.py) roda sobre o texto cru do PGR
inteiro, fora do escopo por-GHE desta hidratação; o valor chega já resolvido
e é replicado para todo GHEPGR do documento, default False para chamador que
não o repassa. Risco NUNCA descartado (D-ARQ-31/35 P3): tri-estado do
resolver (EXATA/FUZZY/NAO_RESOLVIDO) sempre vira exatamente 1 RiscoPGR.
"""
from __future__ import annotations

import dataclasses
import re
from collections.abc import Sequence
from datetime import date
from typing import Optional

from agente_medico.motor.classificacao_ruido import classificar_ruido
from agente_medico.motor.quantificacao import parsear_quantificacao
from agente_medico.motor.resolvedor_termos import Confianca, IndiceTermos, resolver_termo
from agente_medico.motor.tipos import GHEPGR, PGR, GHEVerbatim, Pendencia, RiscoPGR


# S·P·NÍVEL da matriz P×S (legenda dos PGRs medidos: Irrelevante/Baixo/
# Moderado/Alto/Crítico). search, não match: tolera ruído de coluna vizinha
# antes do par S P sem aceitar nível solto sem os dois números.
_PADRAO_AVALIACAO_QUALITATIVA = re.compile(
    r"(?<!\S)\d+\s+\d+\s+(IRRELEVANTE|BAIXO|MODERADO|ALTO|CR[IÍ]TICO)(?!\S)"
)
# Declaração explícita de não-avaliação, medida em Porto Araras I (8/172
# riscos, todos "Ausência de agente nocivo") — não é falha de parse.
_AVALIACAO_NAO_DEFINIDA = "NÃO DEFINIDO"


def parsear_nivel_risco(texto: str) -> tuple[Optional[str], bool]:
    """Nível P×S do texto verbatim das colunas S·P·NÍVEL (DT-003EC-01).
    Devolve (nível, reconhecido): nível em maiúsculas ou None; reconhecido
    False só quando há texto que não é nem nível nem "NÃO DEFINIDO" — o
    chamador transforma isso em pendência, nunca em silêncio."""
    bruto = texto.strip().upper()
    if not bruto:
        return None, True
    m = _PADRAO_AVALIACAO_QUALITATIVA.search(bruto)
    if m is not None:
        return m.group(1).replace("CRITICO", "CRÍTICO"), True
    return None, bruto == _AVALIACAO_NAO_DEFINIDA


def hidratar_ghe(
    ghe: GHEVerbatim,
    indice: IndiceTermos,
    posicao: int,
    psicossocial: bool = False,
) -> tuple[GHEPGR, list[Pendencia]]:
    """Hidrata um bloco GHE transcrito em GHEPGR + pendências (D-ARQ-51).

    Por RiscoVerbatim, resolve o termo cru contra o índice de vocabulário:
    EXATA -> agente=slug, sem pendência. FUZZY -> agente=slug + Pendencia
    resolucao_fuzzy não-bloqueante (o resolver retorna pendencia=None no
    FUZZY por design — fabricá-la aqui é o "consumidor futuro" a que seu
    docstring delega). NAO_RESOLVIDO -> agente=None + a Pendencia
    vocabulario_ausente que o próprio resolver já emitiu, apenas com ghe_id
    preenchido. quantificacao é parseada 1x por risco (parsear_quantificacao,
    D-ARQ-51 fatia 2), independente do tri-estado acima; texto cru não-vazio
    que falha o parse rende Pendencia quantificacao_nao_parseada
    não-bloqueante (anti-supressão D-ARQ-31/35), sem impedir o risco de entrar.
    Quando o slug resolvido é "ruido" (EXATA ou FUZZY) e a quantificação foi
    parseada, classificar_ruido (D-ARQ-51 fatia 3, R-RUIDO-01) preenche
    relacao_LT antes de montar o RiscoPGR; agente=None não classifica.
    """
    # Handle do bloco transcrito, NÃO id canônico (D-ARQ-51 seam 1;
    # re-agrupamento 42->32 é fatia downstream).
    ghe_id = f"GHE-{posicao:02d}"

    riscos: list[RiscoPGR] = []
    pendencias: list[Pendencia] = []

    for risco_verbatim in ghe.riscos:
        resolucao = resolver_termo(risco_verbatim.agente, indice)
        quantificacao = parsear_quantificacao(risco_verbatim.quantificacao)
        if risco_verbatim.quantificacao.strip() != "" and quantificacao is None:
            pendencias.append(
                Pendencia(
                    tipo="quantificacao_nao_parseada",
                    destinatario="extracao",
                    motivo=(
                        f"quantificação '{risco_verbatim.quantificacao}' não pôde ser "
                        "interpretada — revisão recomendada"
                    ),
                    bloqueante=False,
                    regra_origem="D-ARQ-51",
                    ghe_id=ghe_id,
                )
            )

        if resolucao.slug == "ruido" and quantificacao is not None:
            quantificacao = classificar_ruido(quantificacao)

        nivel_risco, avaliacao_reconhecida = parsear_nivel_risco(
            risco_verbatim.avaliacao_qualitativa
        )
        if not avaliacao_reconhecida:
            pendencias.append(
                Pendencia(
                    tipo="avaliacao_qualitativa_nao_parseada",
                    destinatario="extracao",
                    motivo=(
                        f"avaliação qualitativa '{risco_verbatim.avaliacao_qualitativa}' "
                        "não pôde ser interpretada — revisão recomendada"
                    ),
                    bloqueante=False,
                    regra_origem="D-ARQ-51",
                    ghe_id=ghe_id,
                )
            )

        if resolucao.confianca == Confianca.EXATA:
            riscos.append(
                RiscoPGR(
                    tipo="",
                    agente=resolucao.slug,
                    quantificacao=quantificacao,
                    severidade=None,
                    nivel_risco=nivel_risco,
                )
            )
        elif resolucao.confianca == Confianca.FUZZY:
            riscos.append(
                RiscoPGR(
                    tipo="",
                    agente=resolucao.slug,
                    quantificacao=quantificacao,
                    severidade=None,
                    nivel_risco=nivel_risco,
                )
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
            # Erro-zero (D-ARQ-22): NAO_RESOLVIDO sem pendência é violação de contrato
            # do resolver — estourar aqui, nunca produzir agente=None órfão (seam 3).
            assert resolucao.pendencia is not None
            # Invariante: agente=None sempre pareado com exatamente 1 pendência —
            # o guard da Fase A (estagios/riscos.py, 1a) confia nisso (D-ARQ-51 seam 3).
            # causa_nao_resolucao (D-ARQ-82 cl.3): a Resolucao já conhece o tipo da
            # pendência aqui — em vez de descartá-lo, ele viaja com o risco.
            riscos.append(
                RiscoPGR(
                    tipo="",
                    agente=None,
                    quantificacao=quantificacao,
                    severidade=None,
                    causa_nao_resolucao=resolucao.pendencia.tipo,
                    nivel_risco=nivel_risco,
                )
            )
            pendencias.append(dataclasses.replace(resolucao.pendencia, ghe_id=ghe_id))

    ghe_pgr = GHEPGR(
        id=ghe_id,
        nome=ghe.nome,
        cargos=ghe.cargos,
        riscos=tuple(riscos),
        epis=(),
        produtos_quimicos=(),
        psicossocial=psicossocial,
        cenario=None,
    )
    return ghe_pgr, pendencias


def hidratar_pgr(
    ghes: Sequence[GHEVerbatim],
    indice: IndiceTermos,
    validade: date,
    assinatura_engenheiro: bool,
    psicossocial: bool = False,
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
        ghe_pgr, pendencias_ghe = hidratar_ghe(ghe, indice, posicao, psicossocial)
        ghes_pgr.append(ghe_pgr)
        pendencias.extend(pendencias_ghe)

    pgr = PGR(
        validade=validade,
        assinatura_engenheiro=assinatura_engenheiro,
        ghes=tuple(ghes_pgr),
    )
    return pgr, pendencias
