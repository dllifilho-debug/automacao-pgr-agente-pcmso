from __future__ import annotations

from datetime import date

from agente_medico.motor.estagios.consolidacao import ConflitoProtocolo, stage_8_consolidacao
from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.estagios.pendencias_estruturais import stage_3_pendencias_estruturais
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import (
    ExameEmitido,
    GHEContext,
    MatrizGHE,
    PGR,
    Pendencia,
    Resultado,
)


def executar(pgr: PGR, protocolo: Protocolo, hoje: date | None = None) -> Resultado:
    pendencias_gate = stage_1_gates(pgr, hoje)
    if any(p.bloqueante for p in pendencias_gate):
        motivo = "; ".join(p.motivo for p in pendencias_gate if p.bloqueante)
        return Resultado(
            status="REJEITADO",
            matrizes=[],
            pendencias_globais=pendencias_gate,
            motivo_rejeicao=motivo,
        )

    matrizes: list[MatrizGHE] = []
    for ghe in pgr.ghes:
        ctx = GHEContext(pgr_ghe=ghe)
        stage_2_riscos(ctx, protocolo)
        stage_3_pendencias_estruturais(ctx, protocolo)
        stage_4_predicados(ctx, protocolo)
        exames: list[ExameEmitido] = stage_5_emissao(ctx, protocolo)
        # Stage 6 (regime) encaixará aqui

        if any(p.bloqueante for p in ctx.pendencias):
            matriz = MatrizGHE(
                ghe_id=ghe.id,
                linhas=[],
                pendencias=list(ctx.pendencias),
                regime_aplicado=ctx.regime,
            )
        else:
            try:
                linhas = stage_8_consolidacao(exames)
            except ConflitoProtocolo as e:
                ctx.pendencias.append(
                    Pendencia(
                        tipo="conflito_protocolo",
                        destinatario="protocolo",
                        motivo=str(e),
                        bloqueante=True,
                        regra_origem=None,
                        ghe_id=ghe.id,
                    )
                )
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=[],
                    pendencias=list(ctx.pendencias),
                    regime_aplicado=ctx.regime,
                )
            else:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=list(ctx.pendencias),
                    regime_aplicado=ctx.regime,
                )
        matrizes.append(matriz)

    houve_bloqueio = any(any(p.bloqueante for p in m.pendencias) for m in matrizes)
    pendencias_globais = [p for p in pendencias_gate if not p.bloqueante]
    return Resultado(
        status="PRELIMINAR" if houve_bloqueio else "OK",
        matrizes=matrizes,
        pendencias_globais=pendencias_globais,
        motivo_rejeicao=None,
    )
