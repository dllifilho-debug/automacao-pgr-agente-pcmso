# Censo dos rótulos de nível de risco nos PGRs do acervo

`[MEDIDO — 08/10/2026, branch claude/fervent-shannon-1nq8hw sobre main a9a4427]`. Fonte do vocabulário
`agente_medico/protocolo/vocabulario/niveis_risco.yaml` (D-ARQ-95).

**Método.** Texto de todas as páginas dos 32 PGRs em PDF de `matrizes_originais/` (pdfplumber, script
descartável no scratchpad da sessão). Por documento: rótulos nos formatos "N N RÓTULO (N)" (P×S) e
"N - RÓTULO" (AIHA), e páginas de legenda (página com "nível de risco", "matriz", "classificação",
"gradação" ou "probabilidade" e ao menos 4 rótulos), lidas em ordem. As legendas duvidosas foram
conferidas no texto da página.

## Escalas encontradas

| Escala | Ordem (legenda do próprio PGR) | PGRs |
|---|---|---|
| P×S (família Consciente/CMO 2026) | Irrelevante < Baixo < Moderado < Alto < Crítico | Fascino 15.07.26; Toctao ALT 65; Vila Brasil 25.08.26; CMO Aurora e Aurora adendo 27.08.26; CMO Verde Maris; Porto Araras I; Vistamerica 2026-07-28; WV Maldi 2026-07-22 |
| BS 8800 | Trivial < Tolerável < Moderado < Substancial < Intolerável | ALT T65 2024/2026; Euro Setor C; PGR "AURO"; R78 Naturia; Seconci R02AA rev3 e rev4; TPB Andrade; Cjr Engenharia; CMO Ver.02 Rev.02, Vistamerica Rev.01 e Viverde V02 ("BS 8800:1996 adaptada") |
| AIHA Ricco | Trivial < Baixo < Moderado < Alto < Muito Alto (item 4.1.1; coluna Classificação à parte: Irrelevante / De atenção / Crítica / Não tolerável) | Hetrin mar/25 e 14.09.26; REV06; adendo "Funções Faltantes"; Serra Dourada mai/24 |
| Sinduscon-GO | Irrelevante (P×S = 4) < Baixo < Médio (P×S = 10 ou 12) < Alto < Crítico | PGR do Sinduscon-GO, emissão 19/08/2026 ("PGR - Programa de Gerenciamento de Riscos 27.08.26.pdf") |
| Ricco Administração | Baixo < Médio < Alto < Crítico | Ricco Administração 2025 e 10.07.26 |

**Sem nível legível no texto:** CMO Floramazônia (12 págs.); EBSERH UFGD legado e v7 (só a coluna de
classificação AIHA, "1 - Irrelevante … 4 - Não tolerável").

## O que não é nível de risco (falsos positivos conferidos)

- "superior a 20% do efetivo" — critério de número de expostos (CMO Ver.02, pág. 11).
- "risco individual elevado" — classe de agente biológico da NR-32 (EBSERH HUMAP pág. 33; Seconci R02AA rev4 pág. 27).
- "Leve", "Grave", "Significativo", "Aceitável" — escalas de severidade ou de aceitabilidade dentro das metodologias, não o nível final.

## Posição em relação ao corte "moderado ou acima" (e-mail da Dra. Carolini, R-ASO-06)

- Abaixo: Irrelevante, Trivial, Tolerável, Baixo.
- No corte ou acima: Moderado, Alto, Muito Alto, Substancial, Crítico, Intolerável, Não tolerável.
- Médio: no corte `[INTERPRETADO]` — degrau logo acima de Baixo, a posição do Moderado nas duas escalas em que aparece; decisão do Diovanni (08/10/2026), revisão das médicas na saída.
- Qualquer outro rótulo: sem posição, a sugestão sai conferir.
