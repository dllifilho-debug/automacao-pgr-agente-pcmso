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
from agente_medico.motor.tipos import PGR, BlocoVerbatim
from agente_medico.motor.transcricao_fds import montar_fds

__all__ = [
    "AVISO_SEM_CASAMENTO",
    "AgenteEmComum",
    "GHESugerido",
    "SugestaoVinculo",
    "sugerir_ghes",
]

AVISO_SEM_CASAMENTO = (
    "Nenhum GHE do PGR declara os agentes desta FDS — confira se o PGR está "
    "desatualizado ou se a FDS é de outro produto."
)


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
    inválido ou fora do vocabulário) — não conta, mas aparece (cl.1)."""

    ghes: tuple[GHESugerido, ...]
    componentes_sem_slug: tuple[str, ...]

    @property
    def sem_casamento(self) -> bool:
        """cl.4: dispara o aviso não bloqueante."""
        return not self.ghes


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
    return SugestaoVinculo(ghes=tuple(sugeridos), componentes_sem_slug=tuple(sem_slug))
