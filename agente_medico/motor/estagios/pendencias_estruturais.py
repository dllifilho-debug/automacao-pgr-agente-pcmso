from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any

from agente_medico.motor.predicados import riscos_com_contaminante_sem_fds
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import GHEContext, Pendencia

TIPO_CONTAMINANTE_A_CONFIRMAR = "contaminante_a_confirmar"
TIPO_MENOR_APRENDIZ_LISTA_TIP = "menor_aprendiz_lista_tip"

# "menos aprendiz" é a grafia do próprio adendo Hetrin (pág. 8), não erro de leitura.
_MENOR_APRENDIZ = re.compile(r"\bmeno[rs]\s+aprendiz\b")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)).casefold()


def _menor_aprendiz_lista_tip(ctx: GHEContext, lista_tip: Mapping[str, Any]) -> None:
    """R-TIP-01 (Decreto 6.481/2008, Arts. 2º e 3º e Lista TIP): menor aprendiz em GHE com
    agente de um item da Lista TIP. O trabalho é proibido ao menor de 18 anos salvo as
    exceções do Art. 2º § 1º, que o PGR não informa — vai à médica, sem mudar exame (a
    audiometria segue R-AUD-01, como pede o e-mail da Dra. Carolini). Não bloqueia."""
    cargos = [c for c in ctx.pgr_ghe.cargos if _MENOR_APRENDIZ.search(_sem_acento(c))]
    if not cargos:
        return
    agentes = {r.agente for r in ctx.riscos}
    itens = [
        f"{entrada['descricao']} (item {item})"
        for item, entrada in sorted(lista_tip.items(), key=lambda par: int(par[0]))
        if agentes & set(entrada["agentes"])
    ]
    if not itens:
        return
    ctx.pendencias.append(
        Pendencia(
            tipo=TIPO_MENOR_APRENDIZ_LISTA_TIP,
            destinatario="medico",
            motivo=(
                f"{', '.join(cargos)} em {ctx.pgr_ghe.id}: o PGR declara para menor aprendiz risco da "
                f"Lista TIP (Decreto 6.481/2008) — {'; '.join(itens)}. Proibido ao menor de 18 anos, "
                "salvo autorização do MTE a partir dos 16 anos ou parecer técnico depositado no MTE "
                "(Art. 2º § 1º); fora disso, só trabalho técnico ou administrativo fora das áreas de "
                "risco (Art. 3º). Construção civil é atividade da lista (item 58). Conferir a exposição "
                "e a aptidão"
            ),
            bloqueante=False,
            regra_origem="R-TIP-01",
            ghe_id=ctx.pgr_ghe.id,
        )
    )


def _contaminantes_a_confirmar(ctx: GHEContext) -> None:
    """R-FDS-07 (NR-07 7.5.5): agente do GHE cujo vocabulário lista contaminante
    em `contaminantes_a_confirmar` (aguarrás, querosene, nafta → benzeno), sem o
    contaminante entre os riscos e sem FDS anexada no GHE que declare o próprio
    agente. Não bloqueia. O pacote presumido sai pela R-PKG-BZ-PRES."""
    contaminantes = dict.fromkeys(c for r in ctx.riscos for c in r.contaminantes_a_confirmar)
    for contaminante in contaminantes:
        vistos: set[str] = set()
        for risco in riscos_com_contaminante_sem_fds(ctx, contaminante):
            if risco.agente in vistos:
                continue
            vistos.add(risco.agente)
            ctx.pendencias.append(
                Pendencia(
                    tipo=TIPO_CONTAMINANTE_A_CONFIRMAR,
                    destinatario="empresa",
                    motivo=(
                        f"{risco.termo or risco.agente} sem FDS anexada em {ctx.pgr_ghe.id}: a FDS pode "
                        f"declarar {contaminante} como contaminante; pedir a FDS ao elaborador do PGR "
                        f"e anexá-la (NR-07 7.5.5)"
                    ),
                    bloqueante=False,
                    regra_origem="R-FDS-07",
                    ghe_id=ctx.pgr_ghe.id,
                )
            )


def stage_3_pendencias_estruturais(ctx: GHEContext, proto: Protocolo) -> None:
    _contaminantes_a_confirmar(ctx)
    _menor_aprendiz_lista_tip(ctx, proto.vocabulario.lista_tip)
    for produto in ctx.pgr_ghe.produtos_quimicos:
        if produto.fds is None:
            ctx.pendencias.append(
                Pendencia(
                    tipo="composicao_ausente",
                    destinatario="empresa",
                    motivo=f"produto '{produto.nome}' (GHE {ctx.pgr_ghe.id}) sem FDS — composição química ausente; exigir FDS",
                    bloqueante=True,
                    regra_origem="R-PGR-04",
                    ghe_id=ctx.pgr_ghe.id,
                )
            )
            continue
        if not produto.fds.composicao:
            ctx.pendencias.append(
                Pendencia(
                    tipo="composicao_ausente",
                    destinatario="empresa",
                    motivo=f"produto '{produto.nome}' (GHE {ctx.pgr_ghe.id}) com FDS sem composição declarada; exigir composição",
                    bloqueante=True,
                    regra_origem="R-PGR-04",
                    ghe_id=ctx.pgr_ghe.id,
                )
            )
            continue
        for comp in produto.fds.composicao:
            if not comp.cas.strip():
                ctx.pendencias.append(
                    Pendencia(
                        tipo="composicao_ausente",
                        destinatario="empresa",
                        motivo=f"produto '{produto.nome}' (GHE {ctx.pgr_ghe.id}): componente '{comp.nome}' sem CAS — composição inadequada (não resolve via CAS)",
                        bloqueante=True,
                        regra_origem="R-PGR-04",
                        ghe_id=ctx.pgr_ghe.id,
                    )
                )
