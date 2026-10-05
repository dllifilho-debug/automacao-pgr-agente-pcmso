from __future__ import annotations

import dataclasses
from collections.abc import Sequence
from typing import NamedTuple, Protocol

from agente_medico.motor.parser_familia_grid_aiha import GrupoFuncaoAIHA
from agente_medico.motor.tipos import GHEVerbatim

# [DERIVADO — D-ARQ-57 peça 5, fatia G2 (sessão claude/gifted-cerf-0loir2);
# molde transcritor_card.py (peça 4) e TranscritorGHEEmLote (003.EW)]
# A fronteira entre funções é determinística (parser_familia_grid_aiha,
# fatia G1); o conteúdo de cada grupo — nome normalizado, cargos e riscos —
# vai ao LLM. gate_forma_ghe (transcritor_pgr) é reusado a jusante sem
# alteração, como na rota card.


class EntradaGrid(NamedTuple):
    """O que o LLM recebe por grupo: o nome como saiu do PDF (verbatim, com
    o espaçamento quebrado que a extração deixa — "CARPINTEIR O") e o texto
    das linhas do grupo, uma linha física por linha."""

    nome_verbatim: str
    texto: str


class TranscritorGrid(Protocol):
    """Cliente-LLM injetável da rota grid. Transcreve vários grupos por
    invocação porque o gargalo do nível gratuito é requisição, não token
    (D-ARQ-80); um PGR do template set-2026 tem 22 a 30 grupos.

    Contrato duro, o mesmo de TranscritorGHEEmLote: a saída tem o MESMO
    comprimento e a MESMA ordem da entrada. Faltante vira GHEVerbatim vazio,
    que gate_forma_ghe reprova como pendência bloqueante — nunca tupla curta.
    """

    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]: ...


def entrada_do_grupo(grupo: GrupoFuncaoAIHA) -> EntradaGrid:
    return EntradaGrid(
        nome_verbatim=grupo.nome,
        texto="\n".join(linha.texto for linha in grupo.linhas),
    )


def transcrever_grupos_grid(
    grupos: Sequence[GrupoFuncaoAIHA], cliente: TranscritorGrid
) -> tuple[GHEVerbatim, ...]:
    """Ponto único de invocação do transcritor-LLM da rota grid. Saída é
    CANDIDATA: a admissão é de gate_forma_ghe, a jusante.

    Comprimento da saída diferente do de `grupos` levanta ValueError
    (alinhamento grupo<->GHE nunca quebra em silêncio, classe D-ARQ-22).

    `avaliacao_qualitativa` sai sempre vazia. O grid AIHA classifica por
    Probabilidade/Efeito/Nível/Classificação, não pela matriz P×S
    (Irrelevante…Crítico) sobre a qual R-RX-01-qual e R-BIO-05 foram
    decididas — e a palavra "IRRELEVANTE" aparece na coluna Classificação
    do grid, o que enganaria a guarda por legenda da rota GHE
    (_restringir_avaliacao_a_escala_pxs). Vazio leva nivel_risco a None,
    o lado que emite — mesma decisão daquela guarda para bloco fora da
    escala P×S.
    """
    if not grupos:
        return ()
    resultado = tuple(cliente.transcrever_lote([entrada_do_grupo(g) for g in grupos]))
    if len(resultado) != len(grupos):
        raise ValueError(
            f"transcritor do grid devolveu {len(resultado)} GHEs para "
            f"{len(grupos)} grupos — alinhamento quebrado"
        )
    return tuple(_sem_avaliacao_qualitativa(ghe) for ghe in resultado)


def _sem_avaliacao_qualitativa(ghe: GHEVerbatim) -> GHEVerbatim:
    if not any(risco.avaliacao_qualitativa for risco in ghe.riscos):
        return ghe
    riscos = tuple(dataclasses.replace(risco, avaliacao_qualitativa="") for risco in ghe.riscos)
    return dataclasses.replace(ghe, riscos=riscos)
