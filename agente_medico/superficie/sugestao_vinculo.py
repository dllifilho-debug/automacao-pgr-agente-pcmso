"""Sugestão de vínculo FDS↔GHE por agente em comum (D-ARQ-90 fatia 1).

Núcleo puro, sem streamlit. Apresentação: não cria produto, não anexa, não
muda matriz (D-ARQ-49 Parte 2 preservada — o anexo continua sendo o clique do
RT). Sinal único (cl.1): slug dos componentes da FDS, resolvido por CAS pelo
mesmo montar_fds + gate_cas do motor, contra RiscoPGR.agente de cada GHE.
Nome de arquivo, número de GHE no nome e cargo não entram.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Sequence

from agente_medico.motor.resolvedor import construir_indice_cas, gate_cas
from agente_medico.motor.tipos import PGR, BlocoVerbatim, Pendencia
from agente_medico.motor.transcricao_fds import montar_fds

__all__ = [
    "AVISO_SEM_CASAMENTO",
    "AVISO_SEM_COMPONENTE_RECONHECIDO",
    "AVISO_SEM_INGREDIENTE_DECLARADO",
    "AgenteEmComum",
    "GHESugerido",
    "SugestaoVinculo",
    "fds_sem_ingrediente_declarado",
    "sugerir_ghes",
]

AVISO_SEM_CASAMENTO = (
    "Nenhum GHE do PGR declara os agentes desta FDS — confira se o PGR está "
    "desatualizado ou se a FDS é de outro produto."
)

AVISO_SEM_COMPONENTE_RECONHECIDO = (
    "Nenhum componente desta FDS foi reconhecido no vocabulário de agentes, então "
    "não há como sugerir GHE — a lacuna é do vocabulário, não do PGR nem da FDS."
)

AVISO_SEM_INGREDIENTE_DECLARADO = (
    "A FDS não declara ingrediente perigoso; confira contra o que o PGR declara."
)


def fds_sem_ingrediente_declarado(
    blocos_fds: Sequence[BlocoVerbatim], pendencias_fds: Sequence[Pendencia]
) -> bool:
    """Composição lida e vazia, sem pendência: a seção 3 existe e não lista
    ingrediente (caso FDS CARPINTEIRO, DT-(sessão claude/keen-curie-xdm7kb)-02).
    Com pendência (região ausente, transcrição indisponível, bloco reprovado) a
    composição vazia é falha de leitura, não declaração da FDS."""
    return not blocos_fds and not pendencias_fds


@dataclass(frozen=True)
class AgenteEmComum:
    slug: str
    nome_na_fds: str


@dataclass(frozen=True)
class GHESugerido:
    ghe_id: str
    ghe_nome: str
    agentes: tuple[AgenteEmComum, ...]


@dataclass(frozen=True)
class SugestaoVinculo:
    """ghes: todo GHE com ≥1 agente em comum, sem limiar (cl.2), do maior para
    o menor número de agentes; empate fica na ordem do PGR. componentes_sem_slug:
    "CAS | nome" de cada membro que o motor não resolveria (CAS ausente,
    inválido ou fora do vocabulário) — não conta, mas aparece (cl.1).
    agentes_da_fds: slugs resolvidos da FDS, casem ou não com algum GHE."""

    ghes: tuple[GHESugerido, ...]
    componentes_sem_slug: tuple[str, ...]
    agentes_da_fds: tuple[str, ...] = ()

    @property
    def sem_componente_reconhecido(self) -> bool:
        """Nada resolveu para slug: sem sinal, a divergência não é do PGR."""
        return not self.agentes_da_fds

    @property
    def sem_casamento(self) -> bool:
        """cl.4: há agente resolvido na FDS e nenhum GHE o declara."""
        return bool(self.agentes_da_fds) and not self.ghes

    @property
    def mais_agentes_em_comum(self) -> tuple[str, ...]:
        """GHEs do topo (maior contagem, empates incluídos) — o que o botão
        "Marcar" preenche. Decisão do Diovanni em 30/09/2026 sobre a cl.3: marcar
        todos os sugeridos levava agente genérico (sílica de uma FDS de eletrodo)
        a GHEs sem relação com o produto a dois cliques do anexo."""
        if not self.ghes:
            return ()
        topo = len(self.ghes[0].agentes)
        return tuple(g.ghe_id for g in self.ghes if len(g.agentes) == topo)


def sugerir_ghes(
    blocos_fds: Sequence[BlocoVerbatim],
    pgr_hidratado: PGR,
    agentes_vocab: dict[str, Any],
) -> SugestaoVinculo:
    indice = construir_indice_cas(agentes_vocab)
    nome_por_slug: dict[str, str] = {}
    sem_slug: list[str] = []
    for bloco in montar_fds(blocos_fds).composicao_verbatim:
        for membro in bloco.membros:
            resolvido, _ = gate_cas(membro, indice)
            if resolvido.agente is None:
                sem_slug.append(f"{membro.cas or '—'} | {membro.nome}")
            else:
                nome_por_slug.setdefault(resolvido.agente, membro.nome)

    sugeridos: list[GHESugerido] = []
    for ghe in pgr_hidratado.ghes:
        slugs_ghe = {r.agente for r in ghe.riscos if r.agente is not None}
        em_comum = tuple(
            AgenteEmComum(slug=slug, nome_na_fds=nome)
            for slug, nome in nome_por_slug.items()
            if slug in slugs_ghe
        )
        if em_comum:
            sugeridos.append(GHESugerido(ghe_id=ghe.id, ghe_nome=ghe.nome, agentes=em_comum))
    sugeridos.sort(key=lambda g: len(g.agentes), reverse=True)
    return SugestaoVinculo(
        ghes=tuple(sugeridos),
        componentes_sem_slug=tuple(sem_slug),
        agentes_da_fds=tuple(nome_por_slug),
    )
