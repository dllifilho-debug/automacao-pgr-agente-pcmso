"""Verbatim transcrito (mock do LLM-transcritor) das FDS-reais do T65 — D-ARQ-46.

Saída esperada do LLM-transcritor = entrada da montagem (transcricao_fds.montar_composicao).
Texto CRU por componente (cas/nome/faixa como string), fiel à medição determinística dos
PDFs reais (`pdfplumber.extract_tables` sobre fds_originais/, 003.AN/AS): preserva o `\n` de
quebra-de-render (TiO₂ `134363-67-\n7`; nomes partidos), as grafias-de-ausente medidas
(`ND`/`NA`/`vários`) e os separadores en-dash. A montagem (P3/P4/P5) é que normaliza isto
ao gabarito `fds_t65`; aqui o verbatim é deliberadamente sujo.

Pareados a fds_t65 (D-ARQ-42 Parte 4 / 003.AT): tinta acrílica e cimento Ciplan — os dois
casos com a seção de composição produzível por componente. Adesivo Tigre fica fora: grid
não-isolável (patologia 1 de DT-003AS-01) barra a producibilidade do verbatim (MEK/Acetato
sem faixa na própria linha), limite aberto na camada-LLM, não na montagem.

[DERIVADO — medir_fds_gabarito_output.txt, medição 003.AN/AS; fds_t65.py em disco.]
"""
from __future__ import annotations

from agente_medico.motor.tipos import ComponenteVerbatim


def tinta_acrilica_verbatim() -> tuple[ComponenteVerbatim, ...]:
    # FISPQ 004/2008, Nova Rocha. 9 componentes; CAS-ausente grafado ND/NA (notação europeia).
    return (
        ComponenteVerbatim(cas="ND", nome="Derivados Isotiazolonas e\nSemi-Acetais", faixa="0,1 – 0,4"),
        ComponenteVerbatim(cas="134363-67-\n7", nome="Dióxido de Titânio", faixa="1 - 15"),
        ComponenteVerbatim(cas="51274-00-1", nome="Óxido de Ferro Amarelo", faixa="0,1 - 3"),
        ComponenteVerbatim(cas="ND", nome="Carbonato de Cálcio ppt", faixa="5 - 15"),
        ComponenteVerbatim(cas="1332-58-7", nome="Silicato de Alumínio\nhidratado", faixa="5 - 15"),
        ComponenteVerbatim(cas="ND", nome="Carbonato de cálcio natural", faixa="5 - 15"),
        ComponenteVerbatim(cas="1336-21-6", nome="Hidróxido de amônia\n(24°Be)", faixa="0,1 - 1"),
        ComponenteVerbatim(cas="NA", nome="Polímeros acrílicos aquosos\n(a 50%)", faixa="3 - 30"),
        ComponenteVerbatim(cas="ND", nome="Alquil Lauril Érter", faixa="0,1 – 1,2"),
    )


def cimento_ciplan_verbatim() -> tuple[ComponenteVerbatim, ...]:
    # FISPQ Ciplan, Cimento Portland (NBR 14725). 8 componentes; 'vários' é grafia-de-ausente.
    return (
        ComponenteVerbatim(cas="12168-85-3", nome="Silicato tricálcico", faixa="20 - 70"),
        ComponenteVerbatim(cas="10034-77-2", nome="Silicato dicálcico", faixa="10 - 60"),
        ComponenteVerbatim(cas="12068-35-8", nome="Ferro-aluminato de cálcio", faixa="5 - 15"),
        ComponenteVerbatim(cas="vários", nome="Sulfato de cálcio", faixa="2 - 10"),
        ComponenteVerbatim(cas="1242-78-3", nome="Aluminato tricálcico", faixa="1 - 15"),
        ComponenteVerbatim(cas="1317-65-3", nome="Carbonato de cálcio", faixa="0 - 5"),
        ComponenteVerbatim(cas="1309-48-4", nome="Óxido de magnésio", faixa="0 - 4"),
        ComponenteVerbatim(cas="1305-78-8", nome="Óxido de cálcio", faixa="0 - 0,2"),
    )
