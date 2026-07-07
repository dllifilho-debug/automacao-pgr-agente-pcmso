from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from agente_medico.motor.tipos import Pendencia

# D-ARQ-50 Parte 2: o transcritor-LLM normaliza linguisticamente bounded (tira
# qualificador, quebra composto, corrige typo óbvio) mas NUNCA emite slug —
# mapear termo normalizado -> slug do vocabulário é escolha determinística,
# não do LLM (D-ARQ-09: sem I/O, sem LLM neste módulo). Termo sem hit exato
# nem fuzzy único vira Pendencia(vocabulario_ausente, D-ARQ-14) — nunca um
# slug escolhido em silêncio (classe D-ARQ-22, D-ARQ-41 P1).

_PONTUACAO = re.compile(r"[^\w\s]", flags=re.UNICODE)
_ESPACOS = re.compile(r"\s+")


def normalizar_termo(termo: str) -> str:
    """NFKD sem acentos, casefold, pontuação->espaço, whitespace colapsado, espaços->'_'."""
    sem_acento = "".join(
        ch for ch in unicodedata.normalize("NFKD", termo) if not unicodedata.combining(ch)
    )
    minusculo = sem_acento.casefold()
    sem_pontuacao = _PONTUACAO.sub(" ", minusculo)
    colapsado = _ESPACOS.sub(" ", sem_pontuacao).strip()
    return colapsado.replace(" ", "_")


def construir_indice_termos(agentes_vocab: dict[str, Any]) -> dict[str, str]:
    """Inverte o vocabulário de agentes: forma normalizada -> slug.

    O próprio slug é sempre uma entrada. Se a meta do slug tiver campo
    "termos" (lista de aliases), cada alias normalizado também entra —
    mecanismo presente nesta fatia mas não populado em agentes.yaml
    (popular aliases é sessão de dado futura).
    Colisão (mesma forma normalizada apontando para slugs distintos) levanta
    ValueError — dado malformado, classe D-ARQ-22.
    """
    indice: dict[str, str] = {}
    for slug, meta in agentes_vocab.items():
        formas_brutas: list[str] = [slug]
        if isinstance(meta, dict):
            aliases = meta.get("termos")
            if aliases:
                formas_brutas.extend(aliases)
        for forma_bruta in formas_brutas:
            forma = normalizar_termo(str(forma_bruta))
            if forma in indice and indice[forma] != slug:
                raise ValueError(
                    f"Colisão de termo no vocabulário: {forma_bruta!r} aponta para "
                    f"{indice[forma]!r} e {slug!r}"
                )
            indice[forma] = slug
    return indice


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


def resolver_termo(termo: str, indice: dict[str, str]) -> ResolucaoTermo:
    """Resolve um termo (já normalizado linguisticamente pelo LLM, D-ARQ-50 P2)
    contra o índice termo->slug.

    1. Hit exato na forma normalizada -> EXATA.
    2. Sem hit: Levenshtein contra todas as chaves do índice; entre as chaves
       com dist <= 2, toma a(s) de distância mínima. Se essas apontarem para
       um único slug -> FUZZY (sinal de baixa-confiança de D-ARQ-50 P2; nunca
       aceito como certeza — roteamento p/ revisão é do consumidor futuro).
       Se não houver candidato, ou os candidatos de distância mínima
       apontarem para 2+ slugs distintos (empate) -> passo 3: escolher um
       slug arbitrariamente seria escolha silenciosa (classe D-ARQ-22).
    3. NAO_RESOLVIDO + Pendencia(vocabulario_ausente, D-ARQ-14), não-bloqueante.
    """
    forma = normalizar_termo(termo)

    slug_exato = indice.get(forma)
    if slug_exato is not None:
        return ResolucaoTermo(termo=termo, slug=slug_exato, confianca=Confianca.EXATA, pendencia=None)

    menor_dist: Optional[int] = None
    slugs_na_menor_dist: set[str] = set()
    for forma_candidata, slug_candidato in indice.items():
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
        return ResolucaoTermo(termo=termo, slug=slug_unico, confianca=Confianca.FUZZY, pendencia=None)

    pendencia = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="protocolo",
        motivo=f"termo '{termo}' não resolvido no vocabulário de agentes (D-ARQ-14)",
        bloqueante=False,
        regra_origem="D-ARQ-50",
    )
    return ResolucaoTermo(termo=termo, slug=None, confianca=Confianca.NAO_RESOLVIDO, pendencia=pendencia)
