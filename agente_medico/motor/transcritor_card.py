from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from agente_medico.motor.tipos import GHEVerbatim

# [DERIVADO — D-ARQ-57 peça 4 fatia 4c-ii; molde D-ARQ-49 (transcritor_pgr.py)]
# Invocação injetável sob o candidato verbatim, espelhando o transcritor-LLM-GHE
# de bloco. Contrato de FORMA apenas: o texto do prompt-card (003.DG-2) e o
# cliente real ficam para 4c-iii; plug/roteamento em preparar_ghes fica para 4d.
# gate_forma_ghe é REUSADO sem alteração, importado de transcritor_pgr — não
# há gate próprio nesta fatia nem neste módulo (decisão 003.DG-3).


class TranscritorCard(Protocol):
    """Contrato do cliente-LLM injetável do card cargo-based (D-ARQ-57 peça 4
    fatia 4c-ii; decisões 003.DG-1, 003.DG-2, 003.DC).

    Recebe UM card (saída de recortar_cards_cargo, 003.DC — card 1:1 = GHE de
    1 cargo) e o TÍTULO correspondente (saída de recuperar_titulos_cargo,
    mesmo índice) e emite o candidato GHEVerbatim. Saída = reuso ESTRITO de
    GHEVerbatim (003.DG-1): categoria/nível/tipo-de-exposição/vias são RUÍDO
    do card — descartados, não transcritos; quantificação "" é aceita
    (qualitativo/ausente). O texto do prompt-card fica para a fatia do
    cliente real (4c-iii, 003.DG-2) — este é só o contrato de forma.

    Semântica bounded (para a implementação futura do cliente real): nome =
    lotação/setor da linha SEGUINTE à âncora de labels (nunca a própria linha
    de labels `Lotação: Escala de Trabalho: Qtde:`); cargos = o único cargo
    do card — lido do titulo quando não-vazio (UFGD), senão embutido no
    corpo do card (HUMAP); desglue bounded do space-collapse (D-ARQ-50 P2).
    titulo é VERBATIM com prefixo numérico (`13.1 Advogado`); separar o
    número do nome-de-cargo é concern do prompt (4c-iii) — NENHUMA aritmética
    de índice é feita sobre o número aqui (restrição 003.DH: a numeração do
    documento tem lacuna).
    """

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim: ...


def transcrever_cards(
    cards: Sequence[str], titulos: Sequence[str], cliente: TranscritorCard
) -> tuple[GHEVerbatim, ...]:
    """Ponto único de invocação do transcritor-LLM do card (molde
    transcrever_ghes): o cliente entra por parâmetro tipado, nunca importado
    no módulo — testável com mock, sem bater em API/SDK real. Delega par a
    par (card, titulo) na ordem, sem retry/telemetria nesta fatia. Saída é
    CANDIDATA — a admissão é responsabilidade de gate_forma_ghe (reusado de
    transcritor_pgr, 003.DG-3) a jusante.

    len(cards) != len(titulos) levanta ValueError com as duas contagens na
    mensagem: o paralelismo por índice é garantido por construção —
    recortar_cards_cargo e recuperar_titulos_cargo espelham as mesmas
    âncoras — logo um mismatch é bug de construção, não condição do
    documento; por isso exceção, não Pendencia.
    """
    if len(cards) != len(titulos):
        raise ValueError(
            f"cards e titulos devem ter o mesmo tamanho: "
            f"{len(cards)} cards, {len(titulos)} titulos"
        )
    return tuple(
        cliente.transcrever(card, titulo) for card, titulo in zip(cards, titulos)
    )
