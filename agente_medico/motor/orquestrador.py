from __future__ import annotations

import dataclasses
from datetime import date

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.estagios.anexacao import anexar_pendencias
from agente_medico.motor.estagios.consolidacao import ConflitoProtocolo, stage_8_consolidacao
from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.estagios.pendencias_estruturais import stage_3_pendencias_estruturais
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.resolvedor import EntradaIndice
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

        # D-ARQ-31 fatia 2: consolidação roda SEMPRE (inclusive sob pendência
        # bloqueante) para distinguir PARCIAL (linhas determináveis presentes)
        # de BLOQUEADA (nenhuma linha). status carimbado por intenção nos dois sítios.
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
                status="BLOQUEADA",
            )
        else:
            bloqueantes = [p for p in ctx.pendencias if p.bloqueante]
            nao_bloqueantes = [p for p in ctx.pendencias if not p.bloqueante]
            # D-ARQ-31 fatia 3: pendência bloqueante com âncora vai para a linha;
            # sem match, volta ao nível da matriz. Status decidido PÓS-anexação.
            linhas, bloqueantes_restantes = anexar_pendencias(linhas, bloqueantes)
            tem_anexada = any(ln.pendencias_anexadas for ln in linhas)
            tem_bloqueio = bool(bloqueantes_restantes) or tem_anexada
            pendencias_matriz = nao_bloqueantes + bloqueantes_restantes
            if not tem_bloqueio:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="VÁLIDA",
                )
            elif linhas:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="PARCIAL",
                )
            else:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="BLOQUEADA",
                )
        matrizes.append(matriz)

    houve_bloqueio = any(m.status in {"PARCIAL", "BLOQUEADA"} for m in matrizes)
    pendencias_globais = [p for p in pendencias_gate if not p.bloqueante]
    return Resultado(
        status="PRELIMINAR" if houve_bloqueio else "OK",
        matrizes=matrizes,
        pendencias_globais=pendencias_globais,
        motivo_rejeicao=None,
    )


def executar_com_composicao(
    pgr: PGR,
    protocolo: Protocolo,
    indice_cas: dict[str, EntradaIndice],
    hoje: date | None = None,
) -> Resultado:
    """Costura D-ARQ-37 (forma α, 003.Z): resolve a composição da FDS (gate-CAS) ANTES
    de executar(), e remonta o Resultado anexando as pendências do gate ao balde global.
    Pendências do gate são globais (sem ghe_id) — gate roda a montante da mesa de GHE.
    Remontagem via dataclasses.replace; NUNCA mutação de pendencias_globais.
    """
    pgr_resolvido, pend_gate = resolver_composicao(pgr, indice_cas)
    resultado = executar(pgr_resolvido, protocolo, hoje)
    return dataclasses.replace(
        resultado,
        pendencias_globais=resultado.pendencias_globais + pend_gate,
    )
