"""Agravo à saúde de cada perigo na tabela do PCMSO (D-ARQ-96 cl.3) — apresentação, sem decisão de exame.

O texto vem de `vocabulario/agravos.yaml`: pelo agente que o perigo resolve em `agentes.yaml` ou, para perigo sem
agente (acidente, ergonômico, psicossocial), pelos `termos` do próprio vocabulário. Sem casamento, o PCMSO usa o
agravo do PGR (D-ARQ-93) marcado para conferência; sem nenhum dos dois, o agravo fica ausente e visível.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from agente_medico.motor.resolvedor_termos import (
    Confianca,
    IndiceTermos,
    construir_indice_termos,
    normalizar_termo,
    resolver_termo,
)

CAMINHO_PADRAO = Path(__file__).resolve().parent.parent / "protocolo" / "vocabulario" / "agravos.yaml"


class VocabularioAgravosInvalido(ValueError):
    """Dado malformado em agravos.yaml (classe D-ARQ-22): nunca carrega em silêncio."""


class OrigemAgravo(Enum):
    DICIONARIO = "dicionario"
    PGR_CONFERIR = "pgr_conferir"
    AUSENTE = "ausente"


@dataclass(frozen=True)
class EntradaAgravo:
    chave: str
    texto: str
    fonte: str
    agente: str | None


@dataclass(frozen=True)
class AgravoPCMSO:
    texto: str
    origem: OrigemAgravo
    chave: str | None


@dataclass(frozen=True)
class VocabularioAgravos:
    por_agente: dict[str, EntradaAgravo]
    por_forma: dict[str, EntradaAgravo]
    indice_agentes: IndiceTermos


def _texto_obrigatorio(chave: str, campo: str, meta: dict[str, Any]) -> str:
    valor = meta.get(campo)
    if not isinstance(valor, str) or not valor.strip():
        raise VocabularioAgravosInvalido(f"agravos.yaml: {chave!r} sem {campo!r}")
    return valor.strip()


def carregar_agravos(agentes_vocab: dict[str, Any], caminho: Path = CAMINHO_PADRAO) -> VocabularioAgravos:
    """Valida e indexa o vocabulário: agente existente e único; termo que não resolve em agente nem colide."""
    bruto = yaml.safe_load(caminho.read_text(encoding="utf-8")) or {}
    entradas = bruto.get("agravos")
    if not isinstance(entradas, dict):
        raise VocabularioAgravosInvalido("agravos.yaml sem a chave 'agravos'")
    indice_agentes = construir_indice_termos(agentes_vocab)
    por_agente: dict[str, EntradaAgravo] = {}
    por_forma: dict[str, EntradaAgravo] = {}
    for chave, meta in entradas.items():
        if not isinstance(meta, dict):
            raise VocabularioAgravosInvalido(f"agravos.yaml: {chave!r} não é um mapeamento")
        agente = meta.get("agente")
        termos = meta.get("termos") or []
        if (agente is None) == (not termos):
            raise VocabularioAgravosInvalido(f"agravos.yaml: {chave!r} precisa de 'agente' ou de 'termos', não dos dois")
        entrada = EntradaAgravo(
            chave=str(chave),
            texto=_texto_obrigatorio(chave, "texto", meta),
            fonte=_texto_obrigatorio(chave, "fonte", meta),
            agente=str(agente) if agente is not None else None,
        )
        if entrada.agente is not None:
            if entrada.agente not in agentes_vocab:
                raise VocabularioAgravosInvalido(f"agravos.yaml: {chave!r} aponta para agente inexistente {agente!r}")
            if entrada.agente in por_agente:
                raise VocabularioAgravosInvalido(f"agravos.yaml: agente {agente!r} em duas entradas")
            por_agente[entrada.agente] = entrada
            continue
        for termo in termos:
            forma = normalizar_termo(str(termo))
            slug = indice_agentes.slug_por_forma.get(forma)
            if slug is not None:
                # Sinônimo de agente muda exame: é decisão à parte, não entra pelo agravo.
                raise VocabularioAgravosInvalido(f"agravos.yaml: termo {termo!r} de {chave!r} já resolve no agente {slug!r}")
            if forma in por_forma:
                raise VocabularioAgravosInvalido(f"agravos.yaml: termo {termo!r} em duas entradas")
            por_forma[forma] = entrada
    return VocabularioAgravos(por_agente=por_agente, por_forma=por_forma, indice_agentes=indice_agentes)


def agravo_do_perigo(perigo: str, agravo_pgr: str | None, vocabulario: VocabularioAgravos) -> AgravoPCMSO:
    """Agravo para uma linha do PCMSO: dicionário (agente EXATA, depois forma), senão o do PGR para conferir."""
    resolucao = resolver_termo(perigo, vocabulario.indice_agentes)
    entrada = None
    if resolucao.confianca is Confianca.EXATA and resolucao.slug is not None:
        entrada = vocabulario.por_agente.get(resolucao.slug)
    if entrada is None:
        entrada = vocabulario.por_forma.get(normalizar_termo(perigo))
    if entrada is not None:
        return AgravoPCMSO(texto=entrada.texto, origem=OrigemAgravo.DICIONARIO, chave=entrada.chave)
    if agravo_pgr and agravo_pgr.strip():
        return AgravoPCMSO(texto=agravo_pgr.strip(), origem=OrigemAgravo.PGR_CONFERIR, chave=None)
    return AgravoPCMSO(texto="", origem=OrigemAgravo.AUSENTE, chave=None)
