"""Verbatim transcrito (mock do LLM-transcritor) do bloco multi-CAS real da FDS Leinertex.

Mock do LLM-transcritor sobre extract_text: os N CAS que o extract_tables trazia
empilhados em 1 célula (\n) chegam já separados em membros (medição 003.AY). Recorte A
(D-ARQ-42 P3): montagem não popula slug/agente nem flags de perigo; expansão-de-grupo e
herança-α da faixa ficam no resolver (fatia ii, D-ARQ-45 P1/P2).

[DERIVADO — medir_fds_gabarito_output.txt L119-120]
"""
from __future__ import annotations

from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim


def leinertex_derivados_verbatim() -> tuple[BlocoVerbatim, ...]:
    return (
        BlocoVerbatim(faixa="0,2 – 0,05", membros=(
            MembroVerbatim(cas="2634-33-5", nome="1,2-benzotiazolin-3-ona"),
            MembroVerbatim(cas="55965-84-9", nome="5-cloro-2-metil-2H-isotiazole-3-ona e 2-metil-2H-isotiazole-3-ona"),
        )),
        BlocoVerbatim(faixa="0,1 – 0,05", membros=(
            MembroVerbatim(cas="330-54-1", nome="3-(3,4-dichlorophenyl)-1,1-dimethylurea"),
            MembroVerbatim(cas="10605-21-7", nome="methyl benzimidazol-2-ylcarbamate"),
            MembroVerbatim(cas="26530-20-2", nome="N-octil isotiazolinona"),
        )),
    )
