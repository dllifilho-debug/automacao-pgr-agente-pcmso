from __future__ import annotations

from datetime import date, timedelta

from agente_medico.motor.tipos import PGR, Pendencia

PRAZO_VALIDADE_PGR = timedelta(days=730)


def stage_1_gates(pgr: PGR, hoje: date | None = None) -> list[Pendencia]:
    """
    R-PGR-01: PGR.assinatura_engenheiro == False → pendência bloqueante.
    R-PGR-06: (hoje - pgr.validade) >= 730 dias → pendência bloqueante.

    `hoje` injetável para testes. Default: date.today().
    Semântica de pgr.validade: data de emissão do PGR (não data limite).
    """
    data_hoje = hoje if hoje is not None else date.today()
    pendencias: list[Pendencia] = []

    if not pgr.assinatura_engenheiro:
        pendencias.append(
            Pendencia(
                tipo="assinatura_invalida",
                destinatario="empresa",
                motivo="PGR não assinado por engenheiro de segurança do trabalho (NR-18)",
                bloqueante=True,
                regra_origem="R-PGR-01",
                ghe_id=None,
            )
        )

    if (data_hoje - pgr.validade) >= PRAZO_VALIDADE_PGR:
        pendencias.append(
            Pendencia(
                tipo="pgr_vencido",
                destinatario="empresa",
                motivo=f"PGR emitido em {pgr.validade.isoformat()} — validade máxima de 2 anos excedida (R-PGR-06)",
                bloqueante=True,
                regra_origem="R-PGR-06",
                ghe_id=None,
            )
        )

    return pendencias
