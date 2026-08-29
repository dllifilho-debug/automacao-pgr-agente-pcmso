# Validacao: conversao LibreOffice reproduz a medicao Word COM

`[MEDIDO — 29/08/2026]` **Nao commitado.** Gerado pelo Arquiteto.

**Pergunta.** O projeto trata Word COM como unico caminho de medicao confiavel
(`gabarito-humano-tem-ruido`: *"Word COM tem fidelidade de celula maior que LibreOffice->txt"*).
Essa ressalva vale para `.doc -> .docx` lido como **tabela** por `python-docx`, ou so para
`LibreOffice -> txt`?

**Metodo.** Os mesmos 3 documentos que 003.EX mediu por Word COM foram convertidos por
`soffice --headless --convert-to docx` e passados pelo mesmo instrumento versionado
(`scripts/medir_cobertura_e_forma.py`). Comparacao contra
`docs/referencia/GABARITO_003EX_audiometria_dem.md` (versionado).

## Resultado — cobertura de audiometria (Bloco A)

| Documento | Word COM (003.EX) | LibreOffice (hoje) | |
|---|---|---|---|
| SPE 0030 | 41 cargos / 41 com audiometria | 41 / 41 | IDENTICO |
| RESERVA 0028 (base) | 44 / 43 | 44 / 43 | IDENTICO |
| RESERVA 0028 (1) | 44 / 44 | 44 / 44 | IDENTICO |

## Resultado — classificacao do momento DEM (Bloco D)

| Documento | | com_dem | sem_dem | indeterminado |
|---|---|---|---|---|
| SPE 0030 | Word COM | 38 | 3 | 0 |
| SPE 0030 | LibreOffice | **38** | **3** | **0** |
| RESERVA 0028 (1) | Word COM | 42 | 0 | 2 |
| RESERVA 0028 (1) | LibreOffice | **43** | **0** | **1** |

## A unica divergencia e do INSTRUMENTO, nao da conversao

Um cargo, no RESERVA 0028 (1). O `GABARITO_003EX` nomeia os dois indeterminados daquele
documento:

1. cargo **"Assistente Administrativo de Seguranca do Trabalho"** —
   `Audiometria (ADM, PER, MRO, DEM 12 meses)`. Citacao do gabarito: *"O rotulo `DEM 12 meses`
   nao bate com `DEM` exato — classificado `indeterminado`."*
2. celula com **parentese de abertura ausente** — `Audiometria (12 meses) ADM, PER, MRO, DEM)`,
   *"genuinamente malformada no documento de origem"*.

O caso (1) e exatamente o defeito corrigido por **`6f2e9f0`** (003.EZ), cujo titulo e
*"parsear_momentos separa periodicidade colada ao rotulo (DEM 12 meses)"*. O gabarito 003.EX foi
medido ANTES dessa correcao; esta rodada e DEPOIS. Logo o caso (1) resolve e vira `com_dem`
(42 -> 43), e o caso (2), que segue malformado, permanece o unico `indeterminado` (2 -> 1).

A aritmetica fecha exatamente. **Nenhuma divergencia e atribuivel a conversao.**

## Consequencia

Para **esta** classe de medicao — extrair celula de tabela de matriz e classificar exame,
momento e periodicidade — `soffice --convert-to docx` + `python-docx` **reproduz o Word COM**.
A ressalva de `gabarito-humano-tem-ruido` vale para `LibreOffice -> txt` (fluxo de texto, perde
fronteira de celula, "inventou absorcao de cargo vizinho"), **nao** para `-> docx` lido como
tabela.

Efeito pratico: medicao sobre o acervo pode rodar no ambiente do Arquiteto, sem Word, sem
`pywin32` e sem automacao COM no host — que travou em 28/08 com `Visible=false` e deixou um
processo zumbi. Nao se aplica a leitura que dependa de formatacao rica (cor, negrito, revisao),
nao testada aqui.

Ressalva: 3 documentos, 2 medicoes. Amostra pequena, escolhida por ser a unica com medicao
Word COM registrada em doc versionado.
