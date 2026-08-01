"""Render da matriz de saída (D-ARQ-72), extraído de scripts/medicao_pgr.py
(003.EM fatia 1) para dar à matriz uma superfície própria — precondição para
a coordenadora validar o Marco 1. Apresentação-pura sobre `MatrizGHE`,
lógica-de-domínio zero (D-ARQ-54 P1, herdada).
"""

from __future__ import annotations

from agente_medico.motor.tipos import MatrizGHE, Pendencia


def _formatar_pendencia(p: Pendencia) -> str:
    linha_ghe = f"  ghe_id: `{p.ghe_id}`\n" if p.ghe_id is not None else ""
    return (
        f"- tipo: `{p.tipo}`\n"
        f"  destinatario: `{p.destinatario}`\n"
        f"  motivo: {p.motivo}\n"
        f"  bloqueante: {p.bloqueante}\n"
        f"  regra_origem: {p.regra_origem}\n"
        f"{linha_ghe}"
    )


def renderizar_matriz(matriz: MatrizGHE) -> list[str]:
    linhas: list[str] = []
    linhas.append(f"### GHE `{matriz.ghe_id}` — status matriz: `{matriz.status}`")
    linhas.append("")
    if matriz.regime_aplicado is not None:
        linhas.append(f"- regime_aplicado: {matriz.regime_aplicado}")
    if matriz.riscos_resolvidos:
        riscos_fmt = ", ".join(f"`{r}`" for r in matriz.riscos_resolvidos)
    else:
        riscos_fmt = "(nenhum)"
    linhas.append(f"- riscos_resolvidos: {riscos_fmt}")
    predicados_fmt = "; ".join(f"{nome}={valor}" for nome, valor in matriz.predicados_avaliados)
    linhas.append(f"- predicados_avaliados: {predicados_fmt}")
    if matriz.pendencias:
        linhas.append("- pendências da matriz:")
        for p in matriz.pendencias:
            linhas.append("  " + _formatar_pendencia(p).replace("\n", "\n  ").rstrip())
    linhas.append("")
    if matriz.linhas:
        linhas.append("| exame | periodicidade_meses | periodicidade_apos_15a | momentos | motivos (regra_id) | predicado | detalhe | pendências anexadas |")
        linhas.append("|---|---|---|---|---|---|---|---|")
        for exame in matriz.linhas:
            momentos = ", ".join(sorted(m.value for m in exame.momentos))
            motivos = ", ".join(m.regra_id for m in exame.motivos)
            predicados = ", ".join(m.predicado for m in exame.motivos)
            detalhes = ", ".join(m.detalhe for m in exame.motivos if m.detalhe is not None)
            if exame.pendencias_anexadas:
                pendencias_anexadas = ", ".join(
                    f"{p.tipo} ({p.regra_origem}, {'bloqueante' if p.bloqueante else 'nao-bloqueante'})"
                    for p in exame.pendencias_anexadas
                )
            else:
                pendencias_anexadas = "(nenhuma)"
            linhas.append(
                f"| {exame.exame} | {exame.periodicidade_meses} | "
                f"{exame.periodicidade_apos_15a} | {momentos} | {motivos} | "
                f"{predicados} | {detalhes} | {pendencias_anexadas} |"
            )
    else:
        linhas.append("(sem exames emitidos)")
    linhas.append("")
    return linhas
