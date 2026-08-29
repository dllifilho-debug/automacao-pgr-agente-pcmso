# Medicao: a regra de forma da periodicidade (003.EO) sobrevive ao corpus?

`[MEDIDO — 29/08/2026]` Responde ao refino que `DT-003EW-02` exigia antes de implementar a
formatacao. **Nao commitado** ate revisao do Diovanni.

**Regra sob teste (003.EO):** o numero de meses so aparece na celula quando a periodicidade e
diferente de 12M, exceto `rx_torax_oit`, que sempre traz. Quando aparece, gruda no momento `PER`.

**Instrumento:** `scripts/medir_cobertura_e_forma.py` (versionado, funcao `confere_regra_003eo`),
com a correcao `6f2e9f0` (003.EZ) ja aplicada.
**Corpus:** 28 documentos `MATRIZ*` de `matrizes_originais/`, convertidos `.doc -> .docx` por
`soffice --headless --convert-to docx`. A equivalencia dessa conversao com Word COM esta medida em
`VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`.

## Agregado — e por que ele engana sozinho

| | 003.EY (26 docs, instrumento pre-`6f2e9f0`) | 003.FE (28 docs, instrumento corrigido) |
|---|---|---|
| confirmam | 4366 | **4281** |
| contrariam | **2853** | **1805** |
| % contradicao | ~39,5% | **~29,7%** |

A contradicao caiu, mas nao sumiu — e parar aqui levaria a concluir que a regra nao sobrevive.
Ela **nao esta distribuida**.

## O corte que decide — contradicao por ano do documento

| Ano | Docs | Confirma | Contraria | % contra |
|---|---|---|---|---|
| 2024 | 1 | 62 | 0 | **0,0%** |
| 2025 | 9 | 1260 | 1173 | **48,2%** |
| **2026** | **10** | **2896** | **122** | **4,0%** |
| sem data no nome | 3 | 63 | 510 | 89,0% |

Somas conferem contra o agregado: 62+1260+2896+63 = **4281**; 0+1173+122+510 = **1805**.

**Correcao de atribuicao, ancorada em doc versionado:** dos 3 "sem data no nome", dois sao
`CONSCIENTE RESERVA 0028` (base e copia), datados **04/2025** por
`GABARITO_003EX_audiometria_dem.md`. Reatribuidos ao ano correto:

| Ano | Docs | Confirma | Contraria | % contra |
|---|---|---|---|---|
| 2025 | 11 | 1323 | 1681 | **55,9%** |
| **2026** | **10** | **2896** | **122** | **4,0%** |

O terceiro (`CJR ENGENHARIA`) nao tem data no nome nem em doc versionado; fica fora, com 2
ocorrencias — irrelevante para o agregado.

## Detalhe por documento (2026)

| Documento | Confirma | Contraria | % |
|---|---|---|---|
| SINDUSCON-GO 27.08.26 | 7 | 0 | 0,0% |
| SECONCI GOIAS 20.03.26 | 201 | 0 | 0,0% |
| RICCO CONSTRUTORA ESCRITORIO 10.07.26 | 45 | 0 | 0,0% |
| WVM 05 ENTREVERDES 20.07.26 | 519 | 7 | 1,3% |
| DINAMICA ENGENHARIA 07.01.26 | 128 | 2 | 1,5% |
| VILA BRASIL 26.08.26 | 345 | 10 | 2,8% |
| SPE T65 08.07.26 | 449 | 15 | 3,2% |
| CMO VISTAMERICA 28.07.26 | 557 | 23 | 4,0% |
| PORTO ARARAS 1 06.07.26 | 349 | 34 | 8,9% |
| CONSCIENTE SPE 0030 08.07.26 | 296 | 31 | 9,5% |

## Leitura

A regra **e da convencao corrente do escritorio**, nao uma invariante do acervo historico.
Acerta **96% em 2026** e falha em **mais da metade de 2025**. A natureza das contradicoes e
consistente com isso: sao exames de 12M que **imprimem** o numero (`Audiometria (12 meses)
(ADM, PER...)`), forma `grupo_separado`, 542 ocorrencias no corpus — o formato antigo.

Consequencia para o app: o emissor produz **documento novo**, na convencao corrente.
Reproduzir a convencao de 2025 nao e requisito — seria emitir um formato que o escritorio
abandonou. `deed9f6` implementa a regra correta para o que o app deve emitir.

Nao fecha `DT-003EW-02` inteira: os 4% residuais de 2026 (122 ocorrencias) nao foram
investigados nominalmente. `[INTERPRETADO — prioridade na revisao de saida]`

## Ressalvas

1. Corte por **ano do nome do arquivo**, nao por data interna do documento — exceto os dois
   RESERVA, reatribuidos por doc versionado.
2. O corpus de 003.EY tinha 26 documentos; este tem 28 (SINDUSCON e VILA BRASIL entraram em
   28/08). Parte da variacao do agregado e corpus, parte e instrumento; as duas nao se separam
   nesta rodada. O corte por ano nao depende dessa separacao.
3. **Procedencia do corpus, corrigida na re-conferencia deste artefato** (`D-ARQ-84` cl.3).
   A primeira redacao afirmava que o corpus "nao e versionado". **Falso.**
   `matrizes_originais/` esta no `.gitignore` (linha 23), mas `git ls-files matrizes_originais/`
   devolve **17 arquivos versionados** — `.gitignore` nao afeta arquivo ja rastreado. Dos 28
   documentos desta medicao, uma minoria tem historico no git; a maioria nao. O corpus e
   **parcialmente** versionado, o que e pior que qualquer um dos extremos: nao da para saber,
   sem consultar o git, se um documento do acervo tem diff ou nao. Divida nomeada nesta sessao.
