from __future__ import annotations

import dataclasses
import re
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
    is_carcinogeno_iarc é carregado no índice mas não aplicado ao Componente nesta fatia
    (reversão D-ARQ-36 nota 003.V — flag vem da transcrição, não do índice).
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

    NÃO popula flags de perigo — a flag é da transcrição do Componente, não do índice
    (D-ARQ-36 nota 003.V). EntradaIndice.is_carcinogeno_iarc fica carregado mas inerte
    até a Parte 3 plena (tri-estado + is_sensibilizante, sessão própria).
    is_sensibilizante NÃO é tocada — chave inexistente em agentes.yaml (DT-003T-01),
    introduzi-la é sessão de dado própria (cruza DT-003M-01).
    is_ototoxico / tipo_ibe permanecem re-hidratados por-slug no lado-médico
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

    # Ramo (a): CAS válido com slug resolvido. [DERIVADO — D-ARQ-36 nota 003.V (a); D-ARQ-34 Parte 4]
    return dataclasses.replace(componente, agente=entrada.slug), None


_FRASES_H_SENSIBILIZANTE = frozenset({"H334", "H317"})  # D-ARQ-55 P2: sensibilização respiratória/dérmica GHS
_FORMA_FRASE_H = re.compile(r"^H\d{3}$")


def mapear_frases_h(componente: Componente) -> tuple[Componente, Optional[Pendencia]]:
    """Mapa determinístico resolver-side, irmão de gate_cas (D-ARQ-55 P2/P3).

    Para cada token de componente.frases_h (verbatim, D-ARQ-55 P1), avalia
    token.strip() contra _FORMA_FRASE_H (H\\d{3}, estrito, case-sensitive —
    "h334" é malformado, tolerância não medida não é chutada):
      - casa a forma E está em _FRASES_H_SENSIBILIZANTE (H334/H317)
        -> liga is_sensibilizante=True.
      - casa a forma mas fora do mapa (H350, H302…) -> nada: cru preservado,
        sem flag, sem pendência (D-ARQ-22 satisfeito pela PRESERVAÇÃO —
        H-code não-mapeado não some).
      - não casa a forma -> 1 Pendencia não-bloqueante tipo=
        "frase_h_malformada", destinatario="empresa", regra_origem=
        "D-ARQ-55", agregando todos os tokens malformados do componente no
        motivo (revisão-RT, D-ARQ-33 cl.4).

    frases_h NUNCA é reescrito (cru intocado); a flag só LIGA, nunca desliga
    (se já True, permanece True). frases_h == () -> (componente, None) sem
    trabalho. is_carcinogeno_iarc é INTOCADO (GHS != IARC, DT-003CI-01 deferida).
    """
    if not componente.frases_h:
        return componente, None

    liga_sensibilizante = False
    malformados: list[str] = []
    for token in componente.frases_h:
        candidato = token.strip()
        if not _FORMA_FRASE_H.match(candidato):
            malformados.append(token)
            continue
        if candidato in _FRASES_H_SENSIBILIZANTE:
            liga_sensibilizante = True

    componente_novo = componente
    if liga_sensibilizante and not componente.is_sensibilizante:
        componente_novo = dataclasses.replace(componente_novo, is_sensibilizante=True)

    if not malformados:
        return componente_novo, None

    pendencia = Pendencia(
        tipo="frase_h_malformada",
        destinatario="empresa",
        motivo=(
            f"Frase(s)-H malformada(s) {malformados!r} no componente "
            f"'{componente.nome}' (CAS {componente.cas!r})"
            " — revisão pelo RT (D-ARQ-33 cl.4)"
        ),
        bloqueante=False,
        regra_origem="D-ARQ-55",
    )
    return componente_novo, pendencia
