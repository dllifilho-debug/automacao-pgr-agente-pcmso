from __future__ import annotations

from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import GHEContext, Pendencia


def stage_3_pendencias_estruturais(ctx: GHEContext, proto: Protocolo) -> None:
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
