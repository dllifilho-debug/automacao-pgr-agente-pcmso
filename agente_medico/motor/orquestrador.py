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
from agente_medico.motor.predicados import PRIMITIVOS_INCONDICIONAIS
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.resolvedor import EntradaIndice
from agente_medico.motor.tipos import (
    Ausente,
    ExameEmitido,
    GHEContext,
    MatrizGHE,
    PGR,
    Pendencia,
    Resultado,
)


# D-ARQ-82 cl.2 (emendada em 003.FC): lista FECHADA de causas-acerto. O default
# é LACUNA — tipo novo entra aqui só por decisão explícita, nunca por omissão de
# quem o criou. fracao_sem_agente: R-PGR-05 (nota 003.EJ), via D-ARQ-83 cl.3.
# fuzzy_recusado NÃO entra: a recusa de D-ARQ-64 é acerto de RESOLUÇÃO, não
# evidência de que nenhuma conduta é devida (caso Metiletilcetona → R-BIO-04).
CAUSAS_ACERTO_NAO_RESOLUCAO = frozenset({"fracao_sem_agente"})


def _serializar_valor_predicado(v: bool | Ausente) -> str:
    if isinstance(v, Ausente):
        return f"AUSENTE: {v.mensagem}"
    return "True" if v else "False"


def _diagnostico(ctx: GHEContext) -> tuple[tuple[str, ...], tuple[tuple[str, str], ...]]:
    riscos_resolvidos = tuple(sorted({r.agente for r in ctx.riscos}))
    predicados_avaliados = tuple(
        sorted((nome, _serializar_valor_predicado(v)) for nome, v in ctx.predicados.items())
    )
    return riscos_resolvidos, predicados_avaliados


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
        riscos_resolvidos, predicados_avaliados = _diagnostico(ctx)
        # D-ARQ-82 cl.1: VÁLIDA exige ausência de LACUNA, não de pendência. Sobre
        # ghe.riscos (RiscoPGR bruto, não ctx.riscos promovido) — a causa viaja com
        # o risco (cl.3). Default protetivo: causa fora do frozenset (inclusive None)
        # é lacuna.
        tem_lacuna = any(
            r.causa_nao_resolucao not in CAUSAS_ACERTO_NAO_RESOLUCAO
            for r in ghe.riscos if r.agente is None
        )

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
                riscos_resolvidos=riscos_resolvidos,
                predicados_avaliados=predicados_avaliados,
                nome_ghe=ctx.pgr_ghe.nome,
                cargos=ctx.pgr_ghe.cargos,
            )
        else:
            # D-ARQ-31 fatia 3 (estendido por D-ARQ-71 cl.2): pendência com âncora vai
            # para a linha — bloqueante ou não; sem match, volta ao nível da matriz.
            # Status decidido PÓS-anexação.
            linhas, restantes = anexar_pendencias(linhas, list(ctx.pendencias))
            bloqueantes_restantes = [p for p in restantes if p.bloqueante]
            nao_bloqueantes_restantes = [p for p in restantes if not p.bloqueante]
            # D-ARQ-71 cl.3: conta só anexada BLOQUEANTE — anexada não-bloqueante não
            # deve derrubar VÁLIDA para PARCIAL (bug latente que a fatia 2a introduziria
            # sem este fix).
            tem_anexada = any(p.bloqueante for ln in linhas for p in ln.pendencias_anexadas)
            tem_bloqueio = bool(bloqueantes_restantes) or tem_anexada
            pendencias_matriz = nao_bloqueantes_restantes + bloqueantes_restantes
            # D-ARQ-68 cl.5 alínea (d): matriz com linha emitida sob presunção
            # protetiva não pode sair VÁLIDA — sem a presunção não haveria linha,
            # e VÁLIDA sem ressalva no nível da matriz esconderia exatamente o
            # dado que ninguém mediu. Vale tanto anexada à linha quanto no nível
            # da matriz.
            tem_presumida = any(
                p.tipo == "predicado_ausente_presumido" for p in pendencias_matriz
            ) or any(
                p.tipo == "predicado_ausente_presumido"
                for ln in linhas
                for p in ln.pendencias_anexadas
            )
            # R-CLI-01 (piso universal) emite sempre — linhas nunca fica vazia.
            # Tri-estado computa só sobre linhas com origem em risco, excluindo
            # as emitidas por regra incondicional (D-ARQ-31 fatia 2, 003.EC).
            linhas_com_risco = [
                ln for ln in linhas
                if any(m.predicado not in PRIMITIVOS_INCONDICIONAIS for m in ln.motivos)
            ]
            if not tem_bloqueio and not tem_presumida and not tem_lacuna:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="VÁLIDA",
                    riscos_resolvidos=riscos_resolvidos,
                    predicados_avaliados=predicados_avaliados,
                    nome_ghe=ctx.pgr_ghe.nome,
                    cargos=ctx.pgr_ghe.cargos,
                )
            elif linhas_com_risco:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="PARCIAL",
                    riscos_resolvidos=riscos_resolvidos,
                    predicados_avaliados=predicados_avaliados,
                    nome_ghe=ctx.pgr_ghe.nome,
                    cargos=ctx.pgr_ghe.cargos,
                )
            else:
                matriz = MatrizGHE(
                    ghe_id=ghe.id,
                    linhas=linhas,
                    pendencias=pendencias_matriz,
                    regime_aplicado=ctx.regime,
                    status="BLOQUEADA",
                    riscos_resolvidos=riscos_resolvidos,
                    predicados_avaliados=predicados_avaliados,
                    nome_ghe=ctx.pgr_ghe.nome,
                    cargos=ctx.pgr_ghe.cargos,
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
