"""Verbatim transcrito (mock do LLM-transcritor) das FDS-reais do T65 — D-ARQ-46.

Saída esperada do LLM-transcritor = entrada da montagem (transcricao_fds.montar_composicao).
Texto CRU por bloco (faixa/membros como string), fiel à medição determinística dos
PDFs reais (`pdfplumber.extract_tables` sobre fds_originais/, 003.AN/AS): preserva o `\n` de
quebra-de-render (TiO₂ `134363-67-\n7`; nomes partidos), as grafias-de-ausente medidas
(`ND`/`NA`/`vários`) e os separadores en-dash. A montagem (P3/P4/P5) é que normaliza isto
ao gabarito `fds_t65`; aqui o verbatim é deliberadamente sujo.

Cada componente é um BlocoVerbatim singleton (1 membro) — nenhum destes dois casos tem
bloco multi-CAS real (esse caso é fds_verbatim_leinertex.py, 003.AZ).

Pareados a fds_t65 (D-ARQ-42 Parte 4 / 003.AT): tinta acrílica e cimento Ciplan — os dois
casos com a seção de composição produzível por componente. Adesivo Tigre fica fora: grid
não-isolável (patologia 1 de DT-003AS-01) barra a producibilidade do verbatim (MEK/Acetato
sem faixa na própria linha), limite aberto na camada-LLM, não na montagem.

[DERIVADO — medir_fds_gabarito_output.txt, medição 003.AN/AS; fds_t65.py em disco.]
"""
from __future__ import annotations

from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim


def tinta_acrilica_verbatim() -> tuple[BlocoVerbatim, ...]:
    # FISPQ 004/2008, Nova Rocha. 9 componentes; CAS-ausente grafado ND/NA (notação europeia).
    return (
        BlocoVerbatim(faixa="0,1 – 0,4", membros=(
            MembroVerbatim(cas="ND", nome="Derivados Isotiazolonas e\nSemi-Acetais"),)),
        BlocoVerbatim(faixa="1 - 15", membros=(
            MembroVerbatim(cas="134363-67-\n7", nome="Dióxido de Titânio"),)),
        BlocoVerbatim(faixa="0,1 - 3", membros=(
            MembroVerbatim(cas="51274-00-1", nome="Óxido de Ferro Amarelo"),)),
        BlocoVerbatim(faixa="5 - 15", membros=(
            MembroVerbatim(cas="ND", nome="Carbonato de Cálcio ppt"),)),
        BlocoVerbatim(faixa="5 - 15", membros=(
            MembroVerbatim(cas="1332-58-7", nome="Silicato de Alumínio\nhidratado"),)),
        BlocoVerbatim(faixa="5 - 15", membros=(
            MembroVerbatim(cas="ND", nome="Carbonato de cálcio natural"),)),
        BlocoVerbatim(faixa="0,1 - 1", membros=(
            MembroVerbatim(cas="1336-21-6", nome="Hidróxido de amônia\n(24°Be)"),)),
        BlocoVerbatim(faixa="3 - 30", membros=(
            MembroVerbatim(cas="NA", nome="Polímeros acrílicos aquosos\n(a 50%)"),)),
        BlocoVerbatim(faixa="0,1 – 1,2", membros=(
            MembroVerbatim(cas="ND", nome="Alquil Lauril Érter"),)),
    )


def cimento_ciplan_verbatim() -> tuple[BlocoVerbatim, ...]:
    # FISPQ Ciplan, Cimento Portland (NBR 14725). 8 componentes; 'vários' é grafia-de-ausente.
    return (
        BlocoVerbatim(faixa="20 - 70", membros=(
            MembroVerbatim(cas="12168-85-3", nome="Silicato tricálcico"),)),
        BlocoVerbatim(faixa="10 - 60", membros=(
            MembroVerbatim(cas="10034-77-2", nome="Silicato dicálcico"),)),
        BlocoVerbatim(faixa="5 - 15", membros=(
            MembroVerbatim(cas="12068-35-8", nome="Ferro-aluminato de cálcio"),)),
        BlocoVerbatim(faixa="2 - 10", membros=(
            MembroVerbatim(cas="vários", nome="Sulfato de cálcio"),)),
        BlocoVerbatim(faixa="1 - 15", membros=(
            MembroVerbatim(cas="1242-78-3", nome="Aluminato tricálcico"),)),
        BlocoVerbatim(faixa="0 - 5", membros=(
            MembroVerbatim(cas="1317-65-3", nome="Carbonato de cálcio"),)),
        BlocoVerbatim(faixa="0 - 4", membros=(
            MembroVerbatim(cas="1309-48-4", nome="Óxido de magnésio"),)),
        BlocoVerbatim(faixa="0 - 0,2", membros=(
            MembroVerbatim(cas="1305-78-8", nome="Óxido de cálcio"),)),
    )
