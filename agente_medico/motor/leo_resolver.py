from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Callable

from agente_medico.motor.tipos import CenarioExposicao, CenarioNormativo, Fracao


@dataclass(frozen=True)
class ResultadoLeo:
    leo: float | None  # mg/m³; None = LEO indefinido
    fonte_normativa: str  # contrato D-ARQ-24: (leo, fonte_normativa)


# PALIATIVO B.1: slug duplicado de agentes.yaml (silica). B.2 deve referenciar o
# canônico do vocabulário, não esta string. Dívida registrada (002.S).
SILICA = "silica"  # se divergir de agentes.yaml -> PARAR e reportar, não inventar
PNOS = "poeira_nao_classificada"  # se divergir de agentes.yaml -> PARAR e reportar

# --- classificador de cenário ---
# Inclusão/exclusão como tabela (CNAE 2.0 Seção B ∩ campo de aplicação NR-22):
_CNAE_MINERACAO = ("05", "07", "08", "099")  # divisões + grupo 099 (apoio a mineral)
_CNAE_PETROLEO = ("091",)  # apoio a petróleo/gás -> NR-37, fora
# "extracao"/"beneficiamento" SOZINHOS não contam (pegam petróleo/indústria) — universalidade.
_KEYWORDS_MINERACAO = (
    "lavra",
    "garimpo",
    "mineracao",
    "extracao mineral",
    "beneficiamento mineral",
    "pesquisa mineral",
)


def _normaliza(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def classifica_cenario(cenario: CenarioExposicao | None) -> CenarioNormativo:
    if cenario is None:
        return CenarioNormativo.GERAL

    cnae_n = re.sub(r"\D", "", cenario.cnae or "")

    if cnae_n.startswith(_CNAE_PETROLEO):
        # apoio a petróleo/gás — testa keyword para não classificar como mineração por CNAE
        pass
    elif cnae_n.startswith(_CNAE_MINERACAO):
        return CenarioNormativo.MINERACAO

    atividade = cenario.atividade or ""
    local = cenario.local or ""
    texto = _normaliza(f"{atividade} {local}")
    if any(kw in texto for kw in _KEYWORDS_MINERACAO):
        return CenarioNormativo.MINERACAO

    return CenarioNormativo.GERAL


# --- LEO-resolver: cadeia de precedência D-ARQ-24 como tabela por agente ---

_NivelLeo = Callable[[Fracao, CenarioNormativo, "float | None"], "tuple[float, str] | None"]


def _silica_n1_setorial(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (1). NR-22 Anexo V (Portaria MTE 105/2026, alt. 261/2026)
    if cenario is CenarioNormativo.MINERACAO and fracao is Fracao.RESPIRAVEL:
        return (0.05, "NR-22 Anexo V (Portaria MTE 105/2026, alt. 261/2026)")
    return None


def _silica_n2_anexo_nr09(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (2). Sílica não tem anexo próprio NR-09.
    return None


def _silica_n3_anexo12(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (3). NR-15 Anexo 12 via transitório NR-09 9.6.1
    if cenario is not CenarioNormativo.GERAL or pct_quartzo is None:
        return None
    if fracao is Fracao.RESPIRAVEL:
        return (8.0 / (pct_quartzo + 2), "NR-15 Anexo 12 via NR-09 9.6.1 (respiravel)")
    return (24.0 / (pct_quartzo + 3), "NR-15 Anexo 12 via NR-09 9.6.1 (total)")
    # mppdc legada 8,5/(%quartzo+10) NÃO implementar (abandonada — D-ARQ-24)


def _silica_n4_acgih(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (4). Fora de escopo B.1.
    return None


def _pnos_n1_setorial(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (1). PNOS não tem LEO setorial próprio (rodapé Quadro 2).
    return None


def _pnos_n2_anexo_nr09(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (2). PNOS não tem anexo próprio NR-09.
    return None


def _pnos_n3_anexo12(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (3). PNOS não tem fórmula NR-15 Anexo 12.
    return None


def _pnos_n4_acgih(
    fracao: Fracao, cenario: CenarioNormativo, pct_quartzo: float | None
) -> tuple[float, str] | None:
    # D-ARQ-24 nível (4). PNOS sem LEO próprio (rodapé Quadro 2) -> TLV-PNOS ACGIH.
    # [DERIVADO — ACGIH TLV-PNOS 3 mg/m³ resp via NR-09 9.6.1.1]. Fração sempre respirável (Quadro 2).
    if fracao is Fracao.RESPIRAVEL:
        return (3.0, "ACGIH TLV-PNOS 3 mg/m³ resp via NR-09 9.6.1.1")
    return None


_PRECEDENCIA: dict[str, tuple[_NivelLeo, ...]] = {
    SILICA: (_silica_n1_setorial, _silica_n2_anexo_nr09, _silica_n3_anexo12, _silica_n4_acgih),
    PNOS: (_pnos_n1_setorial, _pnos_n2_anexo_nr09, _pnos_n3_anexo12, _pnos_n4_acgih),
}


def resolve_leo(
    agente: str,
    fracao: Fracao,
    cenario: CenarioNormativo,
    pct_quartzo: float | None,
) -> ResultadoLeo:
    niveis = _PRECEDENCIA.get(agente)
    if niveis:
        for nivel in niveis:
            resultado = nivel(fracao, cenario, pct_quartzo)
            if resultado is not None:
                leo, fonte = resultado
                return ResultadoLeo(leo=leo, fonte_normativa=fonte)
    return ResultadoLeo(
        leo=None,
        fonte_normativa=(
            f"LEO indefinido: agente={agente} fracao={fracao.value} cenario={cenario.value}"
        ),
    )
