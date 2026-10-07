from __future__ import annotations

import re
import unicodedata

from agente_medico.motor.predicados import riscos_com_contaminante_sem_fds
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import GHEContext, Pendencia

TIPO_CONTAMINANTE_A_CONFIRMAR = "contaminante_a_confirmar"
TIPO_MENOR_APRENDIZ_COM_RUIDO = "menor_aprendiz_com_ruido"

# "menos aprendiz" é a grafia do próprio adendo Hetrin (pág. 8), não erro de leitura.
_MENOR_APRENDIZ = re.compile(r"\bmeno[rs]\s+aprendiz\b")


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)).casefold()


def _menor_aprendiz_com_ruido(ctx: GHEContext) -> None:
    """R-AUD-05: o PGR declara ruído no GHE de um menor aprendiz. A audiometria segue
    R-AUD-01 (o e-mail da Dra. Carolini pede audiometria com risco moderado ou acima);
    o alerta leva à revisão médica a exposição de menor de 18 anos a ruído, que a
    matriz das médicas do Hetrin 30/09/2026 tratou sem audiometria. Não bloqueia."""
    cargos = [c for c in ctx.pgr_ghe.cargos if _MENOR_APRENDIZ.search(_sem_acento(c))]
    if not cargos or not any(r.agente == "ruido" for r in ctx.riscos):
        return
    ctx.pendencias.append(
        Pendencia(
            tipo=TIPO_MENOR_APRENDIZ_COM_RUIDO,
            destinatario="medico",
            motivo=(
                f"{', '.join(cargos)} em {ctx.pgr_ghe.id}: o PGR declara exposição a ruído para menor "
                "aprendiz — conferir a exposição de menor de 18 anos e a audiometria"
            ),
            bloqueante=False,
            regra_origem="R-AUD-05",
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
    _menor_aprendiz_com_ruido(ctx)
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
