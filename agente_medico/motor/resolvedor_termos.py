from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional, Sequence

from agente_medico.motor.tipos import Pendencia

# D-ARQ-50 Parte 2: o transcritor-LLM normaliza linguisticamente bounded (tira
# qualificador, quebra composto, corrige typo óbvio) mas NUNCA emite slug —
# mapear termo normalizado -> slug do vocabulário é escolha determinística,
# não do LLM (D-ARQ-09: sem I/O, sem LLM neste módulo). Termo sem hit exato
# nem fuzzy único vira Pendencia(vocabulario_ausente, D-ARQ-14) — nunca um
# slug escolhido em silêncio (classe D-ARQ-22, D-ARQ-41 P1).

_PONTUACAO = re.compile(r"[^\w\s]", flags=re.UNICODE)
_ESPACOS = re.compile(r"\s+")

# DT-003DM-01 (D-ARQ-50 P2): raio 2 sobre forma <=4 chars permite editar
# >=50% da string — identidade não sobrevive. Sigla resolve só por exata,
# nas duas direções (busca e candidata).
PISO_FUZZY = 4


def normalizar_termo(termo: str) -> str:
    """NFKD sem acentos, casefold, pontuação->espaço, whitespace colapsado, espaços->'_'."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", termo) if not unicodedata.combining(ch)
    )
    minusculo = sem_acento.casefold()
    sem_pontuacao = _PONTUACAO.sub(" ", minusculo)
    colapsado = _ESPACOS.sub(" ", sem_pontuacao).strip()
    return colapsado.replace(" ", "_")


@dataclass(frozen=True)
class IndiceTermos:
    """Vocabulário de agentes invertido + allowlist de opt-in fuzzy (D-ARQ-64).

    slug_por_forma é o mesmo índice forma->slug de sempre. fuzzy_permitido
    é o conjunto de slugs cujo campo agentes.yaml `fuzzy_permitido: true`
    autoriza devolver Confianca.FUZZY para esse slug — dado, não heurística
    (D-ARQ-64). fracoes_sem_agente (D-ARQ-83) são formas normalizadas que
    nomeiam fração/medida sem identificar substância — NUNCA entram em
    slug_por_forma (D-ARQ-83 cl.2).
    """

    slug_por_forma: dict[str, str]
    fuzzy_permitido: frozenset[str]
    fracoes_sem_agente: frozenset[str]


def construir_indice_termos(
    agentes_vocab: dict[str, Any], *, fracoes_sem_agente: Sequence[str] = ()
) -> IndiceTermos:
    """Inverte o vocabulário de agentes: forma normalizada -> slug.

    O próprio slug é sempre uma entrada. Se a meta do slug tiver campo
    "termos" (lista de aliases), cada alias normalizado também entra —
    mecanismo presente nesta fatia mas não populado em agentes.yaml
    (popular aliases é sessão de dado futura).
    Colisão (mesma forma normalizada apontando para slugs distintos) levanta
    ValueError — dado malformado, classe D-ARQ-22.
    fuzzy_permitido (D-ARQ-64) é lido de meta["fuzzy_permitido"] is True —
    opt-in por slug, dado explícito no vocabulário, nunca inferido.
    fracoes_sem_agente (D-ARQ-83) normaliza cada forma recebida; colisão
    com slug_por_forma é erro (D-ARQ-83 cl.2) — dado malformado nunca passa
    em silêncio.
    """
    indice: dict[str, str] = {}
    fuzzy_permitido: set[str] = set()
    for slug, meta in agentes_vocab.items():
        formas_brutas: list[str] = [slug]
        if isinstance(meta, dict):
            aliases = meta.get("termos")
            if aliases:
                formas_brutas.extend(aliases)
            if meta.get("fuzzy_permitido") is True:
                fuzzy_permitido.add(slug)
        for forma_bruta in formas_brutas:
            forma = normalizar_termo(str(forma_bruta))
            if forma in indice and indice[forma] != slug:
                raise ValueError(
                    f"Colisão de termo no vocabulário: {forma_bruta!r} aponta para "
                    f"{indice[forma]!r} e {slug!r}"
                )
            indice[forma] = slug

    fracoes: set[str] = set()
    for forma_bruta in fracoes_sem_agente:
        forma = normalizar_termo(str(forma_bruta))
        if forma in indice:
            raise ValueError(
                f"Colisão de fração-sem-agente com termo do vocabulário: {forma_bruta!r} "
                f"já aponta para o slug {indice[forma]!r}"
            )
        fracoes.add(forma)

    return IndiceTermos(
        slug_por_forma=indice,
        fuzzy_permitido=frozenset(fuzzy_permitido),
        fracoes_sem_agente=frozenset(fracoes),
    )


def _levenshtein(a: str, b: str) -> int:
    """Distância de edição clássica (DP), sem dependência nova."""
    if a == b:
        return 0
    len_a, len_b = len(a), len(b)
    if len_a == 0:
        return len_b
    if len_b == 0:
        return len_a
    anterior = list(range(len_b + 1))
    for i, ca in enumerate(a, start=1):
        atual = [i] + [0] * len_b
        for j, cb in enumerate(b, start=1):
            custo = 0 if ca == cb else 1
            atual[j] = min(
                anterior[j] + 1,
                atual[j - 1] + 1,
                anterior[j - 1] + custo,
            )
        anterior = atual
    return anterior[len_b]


class Confianca(Enum):
    EXATA = "EXATA"
    FUZZY = "FUZZY"
    NAO_RESOLVIDO = "NAO_RESOLVIDO"


@dataclass(frozen=True)
class ResolucaoTermo:
    termo: str
    slug: Optional[str]
    confianca: Confianca
    pendencia: Optional[Pendencia]


def resolver_termo(termo: str, indice: IndiceTermos) -> ResolucaoTermo:
    """Resolve um termo (já normalizado linguisticamente pelo LLM, D-ARQ-50 P2)
    contra o índice termo->slug.

    1. Hit exato na forma normalizada -> EXATA.
    2. Sem hit: forma reconhecida como fração-sem-agente (D-ARQ-83) ->
       NAO_RESOLVIDO com Pendencia fracao_sem_agente/elaborador_pgr/R-PGR-05.
       Roda ANTES do fuzzy (D-ARQ-83 cl.3): a forma nunca está em
       slug_por_forma (cl.2), então não compete com o passo 1, mas precisa
       ser decidida antes do passo 3 para não sair como fuzzy_recusado por
       coincidência futura de vizinhança.
    3. Sem hit nem fração: Levenshtein contra todas as chaves do índice;
       entre as chaves com dist <= 2, toma a(s) de distância mínima. Se
       essas apontarem para um único slug -> candidato a FUZZY (sinal de
       baixa-confiança de D-ARQ-50 P2; nunca aceito como certeza —
       roteamento p/ revisão é do consumidor futuro). Piso bilateral
       (DT-003DM-01): forma com <= PISO_FUZZY chars não participa do fuzzy,
       nem como termo de busca nem como chave candidata — resolve só pela
       via exata do passo 1.
       Se não houver candidato, ou os candidatos de distância mínima
       apontarem para 2+ slugs distintos (empate) -> passo 4: escolher um
       slug arbitrariamente seria escolha silenciosa (classe D-ARQ-22).
       D-ARQ-64: o veto de allowlist roda SÓ DEPOIS de eleito o vencedor —
       nunca filtrando candidatos durante a busca de menor distância (fazer
       isso deixaria um candidato fora da allowlist escorregar para um 2º
       candidato mais distante como falso-positivo). Se o vencedor não está
       em indice.fuzzy_permitido -> NAO_RESOLVIDO com Pendencia
       fuzzy_recusado nomeando o termo, o slug vencedor e a distância.
    4. NAO_RESOLVIDO + Pendencia(vocabulario_ausente, D-ARQ-14), não-bloqueante.
    """
    forma = normalizar_termo(termo)

    slug_exato = indice.slug_por_forma.get(forma)
    if slug_exato is not None:
        return ResolucaoTermo(termo=termo, slug=slug_exato, confianca=Confianca.EXATA, pendencia=None)

    if forma in indice.fracoes_sem_agente:
        pendencia_fracao = Pendencia(
            tipo="fracao_sem_agente",
            destinatario="elaborador_pgr",
            motivo=(
                f"termo '{termo}' declara fração/medida sem identificar a substância — "
                "solicitar FDS e falar com o elaborador do PGR (R-PGR-05)"
            ),
            bloqueante=False,
            regra_origem="R-PGR-05",
        )
        return ResolucaoTermo(
            termo=termo, slug=None, confianca=Confianca.NAO_RESOLVIDO, pendencia=pendencia_fracao
        )

    menor_dist: Optional[int] = None
    slugs_na_menor_dist: set[str] = set()
    if len(forma) > PISO_FUZZY:
        for forma_candidata, slug_candidato in indice.slug_por_forma.items():
            if len(forma_candidata) <= PISO_FUZZY:
                continue
            dist = _levenshtein(forma, forma_candidata)
            if dist > 2:
                continue
            if menor_dist is None or dist < menor_dist:
                menor_dist = dist
                slugs_na_menor_dist = {slug_candidato}
            elif dist == menor_dist:
                slugs_na_menor_dist.add(slug_candidato)

    if menor_dist is not None and len(slugs_na_menor_dist) == 1:
        slug_unico = next(iter(slugs_na_menor_dist))
        if slug_unico in indice.fuzzy_permitido:
            return ResolucaoTermo(termo=termo, slug=slug_unico, confianca=Confianca.FUZZY, pendencia=None)
        pendencia_recusada = Pendencia(
            tipo="fuzzy_recusado",
            destinatario="extracao",
            motivo=(
                f"termo '{termo}' aproximaria de '{slug_unico}' (distância {menor_dist}) "
                "mas o slug não está na allowlist fuzzy_permitido (D-ARQ-64)"
            ),
            bloqueante=False,
            regra_origem="D-ARQ-64",
        )
        return ResolucaoTermo(
            termo=termo, slug=None, confianca=Confianca.NAO_RESOLVIDO, pendencia=pendencia_recusada
        )

    pendencia = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="protocolo",
        motivo=f"termo '{termo}' não resolvido no vocabulário de agentes (D-ARQ-14)",
        bloqueante=False,
        regra_origem="D-ARQ-50",
    )
    return ResolucaoTermo(termo=termo, slug=None, confianca=Confianca.NAO_RESOLVIDO, pendencia=pendencia)
