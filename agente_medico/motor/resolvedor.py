from __future__ import annotations

import dataclasses
from typing import Any, Optional

from agente_medico.motor.tipos import Componente, Pendencia


def _so_digitos(cas: str) -> str:
    """Mantém apenas os dígitos de uma string CAS (remove hífens, espaços, etc.)."""
    return "".join(ch for ch in cas if ch.isdigit())


def cas_bem_formado(cas: str) -> bool:
    """Valida o dígito verificador do CAS Registry Number.

    D-ARQ-33 cl.3 / D-ARQ-36 Parte 2.
    Fonte: cas.org/training/documentation/chemical-substances/checkdig
    """
    d = _so_digitos(cas)
    if len(d) < 5:
        return False
    verificador = int(d[-1])
    corpo = d[:-1]
    soma = sum(int(digito) * peso for peso, digito in enumerate(reversed(corpo), start=1))
    return soma % 10 == verificador


def construir_indice_cas(agentes_vocab: dict[str, Any]) -> dict[str, str]:
    """Inverte o vocabulário de agentes: CAS normalizado -> slug.

    Agentes físicos e de metadata pobre (sem campo "cas") são pulados.
    Colisão de CAS entre slugs distintos levanta ValueError (integridade do vocabulário).
    """
    indice: dict[str, str] = {}
    for slug, meta in agentes_vocab.items():
        cas_raw = meta.get("cas") if isinstance(meta, dict) else None
        if not cas_raw:
            continue
        cas_norm = _so_digitos(str(cas_raw))
        if not cas_norm:
            continue
        if cas_norm in indice and indice[cas_norm] != slug:
            raise ValueError(
                f"Colisão de CAS no vocabulário: {cas_raw!r} aponta para "
                f"{indice[cas_norm]!r} e {slug!r}"
            )
        indice[cas_norm] = slug
    return indice


def gate_cas(
    componente: Componente,
    indice_cas: dict[str, str],
) -> tuple[Componente, Optional[Pendencia]]:
    """Gate de boa-formação do CAS transcrito (D-ARQ-36 Parte 2).

    Quatro ramos:
      (a) válido + slug resolvido  -> Componente hidratado com agente=slug, None
      (b) válido + sem slug        -> Pendencia vocabulario_ausente, não-bloqueante
      (c) inválido no dígito       -> Pendencia cas_invalido, bloqueante
      (d) ausente/oculto           -> Pendencia cas_ausente, não-bloqueante

    NÃO popula is_carcinogeno_iarc / is_sensibilizante — unificação de
    fonte-de-flag é diferida (D-ARQ-36 Parte 3).
    """
    cas_norm = _so_digitos(componente.cas)

    # Ramo (d): CAS ausente ou oculto (segredo industrial). Oculto != inválido;
    # DT-003M-01 (honrar frase-H sem CAS -> MATERIAL) permanece fora de escopo.
    if not cas_norm:
        return componente, Pendencia(
            tipo="cas_ausente",
            destinatario="empresa",
            motivo=(
                f"CAS ausente ou oculto para componente '{componente.nome}'"
                " — revisão pelo RT (D-ARQ-33 cl.4)"
            ),
            bloqueante=False,
            regra_origem="D-ARQ-36",
        )

    # Ramo (c): CAS falha o dígito verificador.
    if not cas_bem_formado(componente.cas):
        return componente, Pendencia(
            tipo="cas_invalido",
            destinatario="empresa",
            motivo=(
                f"CAS '{componente.cas}' do componente '{componente.nome}'"
                " falha o dígito verificador (D-ARQ-33 cl.3)"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-36",
        )

    # Ramo (b): CAS válido mas slug não resolvido no vocabulário (D-ARQ-14).
    slug = indice_cas.get(cas_norm)
    if slug is None:
        return componente, Pendencia(
            tipo="vocabulario_ausente",
            destinatario="protocolo",
            motivo=(
                f"CAS '{componente.cas}' do componente '{componente.nome}'"
                " não encontrado no vocabulário (D-ARQ-14)"
            ),
            bloqueante=False,
            regra_origem="D-ARQ-36",
        )

    # Ramo (a): CAS válido com slug resolvido.
    return dataclasses.replace(componente, agente=slug), None
