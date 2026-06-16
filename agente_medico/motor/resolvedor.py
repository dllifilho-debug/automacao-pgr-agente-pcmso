from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from typing import Any, Optional

from agente_medico.motor.tipos import Componente, Pendencia


@dataclass(frozen=True)
class EntradaIndice:
    slug: str
    is_carcinogeno_iarc: bool


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


def construir_indice_cas(agentes_vocab: dict[str, Any]) -> dict[str, EntradaIndice]:
    """Inverte o vocabulário de agentes: CAS normalizado -> EntradaIndice (slug + flag de carcinogenicidade).

    Agentes físicos e de metadata pobre (sem campo "cas") são pulados.
    Colisão de CAS entre slugs distintos levanta ValueError (integridade do vocabulário).
    is_sensibilizante deliberadamente fora — chave inexistente em agentes.yaml (DT-003T-01).
    """
    indice: dict[str, EntradaIndice] = {}
    for slug, meta in agentes_vocab.items():
        cas_raw = meta.get("cas") if isinstance(meta, dict) else None
        if not cas_raw:
            continue
        cas_norm = _so_digitos(str(cas_raw))
        if not cas_norm:
            continue
        if cas_norm in indice and indice[cas_norm].slug != slug:
            raise ValueError(
                f"Colisão de CAS no vocabulário: {cas_raw!r} aponta para "
                f"{indice[cas_norm].slug!r} e {slug!r}"
            )
        indice[cas_norm] = EntradaIndice(
            slug=slug,
            is_carcinogeno_iarc=bool(meta.get("is_carcinogeno_iarc", False)),
        )
    return indice


def gate_cas(
    componente: Componente,
    indice_cas: dict[str, EntradaIndice],
) -> tuple[Componente, Optional[Pendencia]]:
    """Gate de boa-formação do CAS transcrito (D-ARQ-36 Parte 2).

    Quatro ramos:
      (a) válido + slug resolvido  -> Componente hidratado com agente=slug, None
      (b) válido + sem slug        -> Pendencia vocabulario_ausente, não-bloqueante
      (c) inválido no dígito       -> Pendencia cas_invalido, bloqueante
      (d) ausente/oculto           -> Pendencia cas_ausente, não-bloqueante

    Popula is_carcinogeno_iarc a partir do índice (D-ARQ-36 Parte 3).
    is_sensibilizante NÃO é tocada — chave inexistente em agentes.yaml (DT-003T-01),
    introduzi-la é sessão de dado própria (cruza DT-003M-01).
    is_ototoxico / anexo_nr07 permanecem re-hidratados por-slug no lado-médico
    (só existem em Risco, não em Componente).
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
    entrada = indice_cas.get(cas_norm)
    if entrada is None:
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
    return dataclasses.replace(
        componente,
        agente=entrada.slug,
        is_carcinogeno_iarc=entrada.is_carcinogeno_iarc,  # D-ARQ-36 Parte 3
    ), None
