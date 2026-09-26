"""Revisão da matriz na tela web — apresentação-pura sobre `MatrizGHE`
(D-ARQ-72, herdando D-ARQ-54 P1). Não entra no documento assinado: é o que o
RT lê para conferir de onde veio cada exame antes de levar a matriz à médica.

Duas leituras por GHE:
- por exame: regra (com a periodicidade que cada uma pediu, D-ARQ-87), status
  da regra e origem do risco (`Motivo.risco_origem`,
  preenchido pelo motor só nas regras de agente direto — D-ARQ-22 Parte B,
  recorte atômico; nas demais aparece o predicado);
- por agente: enquadramento no Decreto 3.048/1999, Anexo IV, lido do campo
  `enquadramento_3048` de `agentes.yaml` (D-ARQ-12, reabertura parcial de
  DT-003BA-01). Referência previdenciária, não decisão de exame do PCMSO.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE

NAO_CONFERIDO_3048 = "sem enquadramento conferido"
NAO_CONSTA_3048 = "não consta no Anexo IV (conferido)"


@dataclass(frozen=True)
class LinhaRevisao:
    exame: str
    periodicidade: str
    regras: str
    status: str
    origem: str


@dataclass(frozen=True)
class EnquadramentoAgente:
    agente: str
    enquadramento: str


@dataclass(frozen=True)
class RevisaoGHE:
    ghe_id: str
    nome_ghe: str
    linhas: tuple[LinhaRevisao, ...]
    enquadramentos: tuple[EnquadramentoAgente, ...]


def _origem(exame: ExameEmitido) -> str:
    origens = [m.risco_origem for m in exame.motivos if m.risco_origem is not None]
    if origens:
        return " / ".join(dict.fromkeys(origens))
    return "predicado: " + " / ".join(dict.fromkeys(m.predicado for m in exame.motivos))


def _regras(exame: ExameEmitido) -> str:
    """Cada regra com a periodicidade que ela pediu (D-ARQ-87): quando duas
    regras pedem o mesmo exame, a linha mostra por que ficou a menor."""
    return ", ".join(
        dict.fromkeys(
            m.regra_id if m.periodicidade_meses is None
            else f"{m.regra_id} ({m.periodicidade_meses} meses)"
            for m in exame.motivos
        )
    )


def _linha(exame: ExameEmitido, exames_vocab: dict[str, Any]) -> LinhaRevisao:
    return LinhaRevisao(
        exame=exames_vocab.get(exame.exame, {}).get("nome_exibicao", exame.exame),
        periodicidade=f"{exame.periodicidade_meses} meses",
        regras=_regras(exame),
        status=", ".join(dict.fromkeys(m.status_regra or "(sem status)" for m in exame.motivos)),
        origem=_origem(exame),
    )


def enquadramento_3048(agente: str, agentes_vocab: dict[str, Any]) -> str:
    """Chave ausente = ninguém conferiu o agente contra o Anexo IV; `null` =
    conferido e não consta. Os dois não podem sair iguais na tela."""
    meta = agentes_vocab.get(agente)
    if meta is None or "enquadramento_3048" not in meta:
        return NAO_CONFERIDO_3048
    valor = meta["enquadramento_3048"]
    if valor is None:
        return NAO_CONSTA_3048
    return f"item {valor['codigo']} — {valor['tempo_exposicao']}"


def montar_revisao(
    matrizes: Sequence[MatrizGHE],
    exames_vocab: dict[str, Any],
    agentes_vocab: dict[str, Any],
) -> tuple[RevisaoGHE, ...]:
    return tuple(
        RevisaoGHE(
            ghe_id=m.ghe_id,
            nome_ghe=m.nome_ghe,
            linhas=tuple(_linha(e, exames_vocab) for e in m.linhas),
            enquadramentos=tuple(
                EnquadramentoAgente(agente=a, enquadramento=enquadramento_3048(a, agentes_vocab))
                for a in m.riscos_resolvidos
            ),
        )
        for m in matrizes
    )


def _celula(texto: str) -> str:
    return texto.replace("|", "\\|")


def tabela_markdown(revisao: RevisaoGHE) -> str:
    cabecalho = "| Exame | Periodicidade | Regra | Status | Origem |\n|---|---|---|---|---|"
    linhas = [
        "| "
        + " | ".join(
            _celula(c) for c in (l.exame, l.periodicidade, l.regras, l.status, l.origem)
        )
        + " |"
        for l in revisao.linhas
    ]
    return "\n".join([cabecalho, *linhas])

