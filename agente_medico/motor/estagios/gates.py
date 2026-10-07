from __future__ import annotations

from datetime import date, timedelta

from agente_medico.motor.tipos import PGR, Pendencia

PRAZO_VALIDADE_PGR = timedelta(days=730)
# NR-01 item 1.5.3.1.4 (redação da Portaria MTE 1.419/2024): o gerenciamento de riscos
# abrange os fatores de risco psicossociais; vigência em 26/05/2026 (Portaria MTE 765/2025).
VIGENCIA_FRPRT_NR01 = date(2026, 5, 26)
TIPO_PGR_SEM_INVENTARIO_PSICOSSOCIAL = "pgr_sem_inventario_psicossocial"


def stage_1_gates(pgr: PGR, hoje: date | None = None) -> list[Pendencia]:
    """
    R-PGR-01: PGR.assinatura_engenheiro == False → pendência bloqueante.
    R-PGR-06: (hoje - pgr.validade) >= 730 dias → pendência bloqueante.
    R-PSY-07: PGR emitido a partir da vigência do FRPRT na NR-01 sem inventário
    psicossocial → pendência não bloqueante (só alerta; não gera nem tira exame).

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

    # R-PSY-07 — NR-01 item 1.5.3.1.4. Sem o inventário, R-PSY-05 e a perna da altura
    # de R-PSY-06 não disparam: o alerta impede que a falta passe em silêncio.
    if pgr.validade >= VIGENCIA_FRPRT_NR01 and not any(g.psicossocial for g in pgr.ghes):
        pendencias.append(
            Pendencia(
                tipo=TIPO_PGR_SEM_INVENTARIO_PSICOSSOCIAL,
                destinatario="empresa",
                motivo=(
                    f"PGR emitido em {pgr.validade.strftime('%d/%m/%Y')} sem inventário de riscos "
                    "psicossociais: a NR-01 (item 1.5.3.1.4, vigente desde 26/05/2026) manda o "
                    "gerenciamento de riscos abrangê-los. Sem o inventário, a matriz sai sem Av. Médica "
                    "de Saúde Mental e sem Avaliação Psicossocial por trabalho em altura — conferir o PGR"
                ),
                bloqueante=False,
                regra_origem="R-PSY-07",
                ghe_id=None,
            )
        )

    return pendencias
