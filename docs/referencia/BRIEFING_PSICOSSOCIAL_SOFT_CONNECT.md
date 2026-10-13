# Briefing — inventário psicossocial não detectado (PGR Soft Connect15 v04)

`[MEDIDO — 13/10/2026, branch claude/busy-cerf-tqxkmg]` Ponto de partida da sessão de 13/10/2026 (branch `claude/admiring-maxwell-dhcgko`), que o
implementou: D-ARQ-94, emenda 3.

## Sintoma

`[PGR] - Soft Connect15 - Versão 04. Outubro 2026 (1).pdf` (467 págs., em `matrizes_originais/`)
tem inventário psicossocial avaliado em todos os 21 GHE: linhas do grupo
`ERGONÔMICOS - PSICOSSOCIAL`, com nível BAIXO/MÉDIO/ALTO. 44 linhas têm nível que o vocabulário
de níveis classifica, e MÉDIO e ALTO caem em `corte`.

O app devolve `InventarioPsicossocial(avaliado=False, moderado_ou_acima=False)`. Com isso:
- R-PSY-06/R-PSY-08 não disparam: a Avaliação Psicossocial e a Saúde Mental somem da matriz;
- R-PSY-07 pode avisar "PGR sem inventário psicossocial" sem razão.

## Causa medida

`avaliar_inventario_psicossocial` (`agente_medico/motor/extracao_pgr.py`) exige, na MESMA linha
de texto, o começo `psicossocia` (`_LINHA_FATOR_PSICOSSOCIAL`) e um rótulo de nível
(`classificar_nivel_pgr`). Neste PDF, o texto do pdfplumber parte a tabela em colunas: as linhas
começam com `PSICOSSOCIAL ...`, mas o nível fica noutra linha. Exemplos reais:

- `PSICOSSOCIAL OS RESULTADOS) – ENQUADRAMENTO REALIZADO POR DE/ PARA A METODOLOGIA ANEXADA A`
- `PSICOSSOCIAL coletivista OS RESULTADOS) – ...`
- `PSICOSSOCIAL divisão social do trabalho)`

`detectar_psicossocial` dá True; o que falha é a leitura do nível.

## Evidência de que o dado existe

`pdfplumber.Page.extract_tables()` devolve as células limpas. A coluna 0 traz o grupo
(`ERGONÔMICOS - PSICOSSOCIAL`, com variantes `ERGONÔMICO S - PSICOSSOCIAL` e
`ERGONÔMIC OS - PSICOSSOCIA L`, quebradas pela largura da coluna), a coluna 1 traz o fator e a
última coluna traz o nível. Páginas 39–295.

## Gabarito

`matrizes_originais/MATRIZ DE EXAMES(ADENDO)SERRINHA 201 DEL EMPREEND. IMOB 21.09.26.doc`
(obra SOFT CONNECT 15, data 17/08/2026, versão anterior do PGR). A médica pede Avaliação
Psicossocial e Saúde Mental em parte dos GHE. A versão 04 (09/2026) acrescenta as avaliações
psicossociais; conferir GHE a GHE.

## Critério de não-regressão (o mesmo das duas fatias anteriores)

Ler os 53 PDFs de `matrizes_originais/` com `io_pdf.ler_faixa` e comparar `main` × código novo em
`avaliar_inventario_psicossocial` e `detectar_psicossocial`. Esperado: só o Soft Connect muda.
Nos 14 PGRs com marcador, medidos em 09/10/2026 (nota de R-PSY-08), 4 só citam o FRPRT e 10 têm
fator avaliado: nenhum deles pode mudar.

## Pontos de decisão (do Diovanni)

1. Onde ler o nível: tabela (`extract_tables`) ou reconstrução de linha por palavras com
   coordenadas. Medir custo de tempo: o reparse de PDF é ~79% da suíte (DH-003EC-02).
2. Se o nível não for lido mas o marcador existir: hoje sai `avaliado=False` em silêncio.
   Alternativa: aviso não bloqueante "inventário citado, nível não lido", como em
   `numeracao_ghe_duplicada` (andamento de 13/10/2026 em D-ARQ-57).
