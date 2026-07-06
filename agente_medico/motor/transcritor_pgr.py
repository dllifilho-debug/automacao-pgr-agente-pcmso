from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from agente_medico.motor.tipos import GHEVerbatim, Pendencia

# [DERIVADO — D-ARQ-49 P3 / D-ARQ-50 C3; molde D-ARQ-47]
# Invocação injetável (cl.2) + gate de forma (cl.3) sob o candidato verbatim
# (cl.1), espelhando o transcritor-LLM-FDS (D-ARQ-47). Composição fim-a-fim
# recorte->transcrição->resolver do lado-PGR só existe em teste nesta fatia
# (harness mockado) — não há revisão-RT nem montagem de produção aqui ainda.


class TranscritorGHE(Protocol):
    """Contrato do cliente-LLM injetável do lado-PGR (D-ARQ-49 P3/D-ARQ-50 C3).

    Recebe UM bloco (saída de recortar_blocos_ghe, 003.BM) e emite o
    candidato GHEVerbatim. Carga bounded medida (D-ARQ-50 C3): parear
    agente<->valor fundido, agrupar multi-agente do mesmo ET, separar agente
    de quantificação, ler Fonte geradora, separar cargos da âncora. NÃO emite
    slug, não computa valor, não atribui id.

    O grid de classificação (I/O/T, prob/sev/GR) e a cauda do bloco são
    RUÍDO — descartados, não transcritos. O texto do prompt fica para a
    fatia do cliente real — este é só o contrato de forma.
    """

    def transcrever(self, bloco: str) -> GHEVerbatim: ...


def transcrever_ghes(
    blocos: Sequence[str], cliente: TranscritorGHE
) -> tuple[GHEVerbatim, ...]:
    """Ponto único de invocação do transcritor-LLM do lado-PGR (molde
    transcrever_fds, D-ARQ-47): o cliente entra por parâmetro tipado, nunca
    importado no módulo — testável com mock, sem bater em API/SDK real.
    Delega bloco a bloco, na ordem, sem retry/telemetria nesta fatia. Saída
    é CANDIDATA: a admissão fica para fatia futura (revisão a jusante).
    """
    return tuple(cliente.transcrever(bloco) for bloco in blocos)


def gate_forma_ghe(
    ghes: Sequence[GHEVerbatim],
) -> tuple[tuple[GHEVerbatim, ...], tuple[Pendencia, ...]]:
    """Gate de FORMA, não de conteúdo (molde gate_forma FDS, D-ARQ-47 cl.3).
    GHE APROVADO se: (a) nome.strip() != ""; e (b) todo risco tem
    agente.strip() != "".

    GHE REPROVADO é EXCLUÍDO dos aprovados e vira Pendencia bloqueante: sem
    o gate, uma transcrição vazia entraria em silêncio (classe D-ARQ-22).
    Cargos vazios NÃO reprovam (GHE mono-função sem lista de cargos é forma
    legítima — critério de conteúdo é gabarito, não gate). Ordem e
    identidade dos aprovados preservadas.
    """
    aprovados: list[GHEVerbatim] = []
    pendencias: list[Pendencia] = []
    for ghe in ghes:
        nome_valido = ghe.nome.strip() != ""
        riscos_validos = all(risco.agente.strip() != "" for risco in ghe.riscos)
        if nome_valido and riscos_validos:
            aprovados.append(ghe)
        else:
            pendencias.append(
                Pendencia(
                    tipo="forma_verbatim_pgr",
                    destinatario="extracao",
                    motivo=(
                        f"GHE verbatim reprovado no gate de forma: "
                        f"nome={ghe.nome!r}, riscos={len(ghe.riscos)}"
                    ),
                    bloqueante=True,
                    regra_origem="D-ARQ-49",
                )
            )
    return tuple(aprovados), tuple(pendencias)
