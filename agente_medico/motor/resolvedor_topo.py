from __future__ import annotations

import re
import unicodedata
from datetime import date

from agente_medico.motor.tipos import CandidataValidade, EnvelopeVerbatim

# D-ARQ-53 P3 / DT-003BV-01 / R-PGR-06 (NR-01 — validade do PGR): resolvedor
# determinístico validade_textos -> date. Puro, sem I/O, sem LLM (molde
# resolvedor_termos.py). Só mês-ano PT-BR por extenso é medido em topo até
# esta fatia (decisão D2) — dd/mm/aaaa e outros formatos NÃO são suportados
# aqui; candidata não-parseável vira data=None, nunca bloqueia (a decisão
# final é da confirmação-RT).

_MESES = {
    "janeiro": 1,
    "fevereiro": 2,
    "marco": 3,
    "abril": 4,
    "maio": 5,
    "junho": 6,
    "julho": 7,
    "agosto": 8,
    "setembro": 9,
    "outubro": 10,
    "novembro": 11,
    "dezembro": 12,
}

_MES_ANO = re.compile(
    r"\b(" + "|".join(_MESES) + r")\b\s+(\d{4})\b",
    flags=re.IGNORECASE,
)


def _sem_acento(texto: str) -> str:
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(ch)
    )


def resolver_candidata(texto: str) -> CandidataValidade:
    """Resolve UMA candidata crua de validade. Regex mês-ano PT-BR (12 meses
    por extenso, case-insensitive, insensível a acento — "MARÇO"/"MARCO"
    resolvem igual), tolerante a prefixo/sufixo ("GOIÂNIA, FEVEREIRO 2023").
    Mês-ano resolve para o 1º dia do mês — default conservador da resolução
    parcial de DT-003BV-01 [INTERPRETADO]; dia exato é edição do RT.

    Mais de um match mês-ano na mesma string -> data=None (ambiguidade não
    resolve em silêncio, classe D-ARQ-22). dd/mm/aaaa e qualquer outro
    formato NÃO suportados nesta fatia -> data=None.
    """
    normalizado = _sem_acento(texto)
    matches = list(_MES_ANO.finditer(normalizado))
    if len(matches) != 1:
        return CandidataValidade(texto=texto, data=None)

    mes_str, ano_str = matches[0].group(1), matches[0].group(2)
    mes = _MESES[mes_str.lower()]
    ano = int(ano_str)
    return CandidataValidade(texto=texto, data=date(ano, mes, 1))


def resolver_validade(
    envelope: EnvelopeVerbatim,
) -> tuple[tuple[CandidataValidade, ...], date | None]:
    """Aplica resolver_candidata a cada elemento de validade_textos, na
    ordem. Proposta = max das datas resolvidas — política "mais recente" =
    última atualização conta (DT-003BV-01, hipótese atual). Zero resolvidas
    -> None.
    """
    candidatas = tuple(resolver_candidata(texto) for texto in envelope.validade_textos)
    datas = [c.data for c in candidatas if c.data is not None]
    proposta = max(datas) if datas else None
    return candidatas, proposta
