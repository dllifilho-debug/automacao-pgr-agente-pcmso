"""Ponto de entrada de produção do motor novo (D-ARQ-40): fachada fina sobre executar_com_composicao."""

from __future__ import annotations

from datetime import date

from .orquestrador import executar_com_composicao
from .protocolo import Protocolo
from .resolvedor import construir_indice_cas
from .tipos import PGR, Resultado


def processar_pgr(pgr: PGR, protocolo: Protocolo, hoje: date | None = None) -> Resultado:
    indice_cas = construir_indice_cas(protocolo.vocabulario.agentes)
    return executar_com_composicao(pgr, protocolo, indice_cas, hoje)
