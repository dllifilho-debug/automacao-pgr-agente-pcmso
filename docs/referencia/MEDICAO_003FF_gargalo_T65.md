# Medicao 003.FF passo 0 — anatomia do T65 e o que a `DT-003FE-01` erra

`[MEDIDO — 29/08/2026, pdfplumber 0.11.10 do motor, Python 3.10.12, host = VM Cowork]`
Varredura read-only, nenhum arquivo do motor tocado. Documento:
`matrizes_originais/PGR - ALT T65 2024.2026.pdf`, 46 paginas, `main c9db9cc`.

**Este documento passou por duas passadas.** A 1a cravou dois numeros errados, corrigidos na
2a e anotados abaixo como CORRIGIDO. O erro foi de criterio de medicao, nao de leitura do PDF;
o historico fica a vista de proposito.

## 1. O que `DT-003FE-01` afirma, e o que a medicao mostra

| Afirmacao | Medido | Veredito |
|---|---|---|
| "`extracao_pgr.py` localiza bloco por `DADOS GERAIS`" | `DADOS GERAIS` so e lido em `_recuperar_titulo_do_vao`, da rota **card** (EBSERH). Nao participa do roteamento GHE. | **DIVERGE** |
| "o motor nao enxerga os 16 blocos do T65" | `eh_cabecalho_ghe` casa **16/16** `INVENTARIO DE RISCO GHE NN`; `recortar_blocos_ghe` -> **16 blocos**; `avaliar_estrutura` -> `("ghe", None)`. | **DIVERGE** |
| "familia de parser que ninguem escreveu" (ancora) | Forma 3 de `_RECONHECEDORES_GHE` cita **"ALT T65"** nominalmente desde `D-ARQ-57` peca 1. | **DIVERGE** |
| "`familia_nao_medida` impediu o T65 de atravessar" | `familia_nao_medida` e **nao-bloqueante** (`orquestracao_pgr.py`). O bloqueio foi o HTTP 503 -> `transcricao_indisponivel_pgr`. | **DIVERGE** |
| "estrutura mais simples que a da familia existente" | O **layout** e tratavel pela mesma tecnica da familia 1 (secao 3). O que e mais dificil e a **semantica das colunas** (4.3), a **tolerancia a typo** (4.1) e a **quantificacao** (4.4). | **PARCIAL** |

A ressalva de instrumento do proprio `MEDICAO_003FE_RICCO_e_parses.md` ("medir no `pdfplumber`,
nao no `pdftotext`") estava certa: medida no extrator do motor, a ancora **ja passa**.

## 2. Onde o T65 realmente para

`parser_familia_consciente._parsear_bloco` recusa **16/16** blocos, todos por
`FamiliaNaoReconhecida: cabecalho de tabela (GRUPO/PERIGO/FONTE/AGRAVO) nao localizado`.
Gargalo = familia de **conteudo do bloco** (`D-ARQ-65` fatia 1), nao ancora de recorte
(`D-ARQ-57` peca 1, ja resolvida para o T65).

## 3. O layout e tratavel — a tecnica da familia 1 transporta

**CORRIGIDO.** A 1a passada afirmou "cabecalho rotacionado" e "cabecalho localizavel em 2 de
16 blocos". Ambos falsos:

- `extract_words()` devolve **zero** palavras nao-upright no documento inteiro. Nao ha rotacao;
  o visual de letras espacadas e char-spacing de celula estreita.
- O "2 de 16" era artefato do criterio: exigia a palavra `Origem` na mesma linha agrupada, e
  `Origem do` / `Risco` quebram em duas linhas fisicas (delta-top ~4,8pt >
  `_TOLERANCIA_LINHA_PT` = 2,5pt).

Com o nucleo `{Perigo, Exposicao, Medidas, controle}` numa mesma linha agrupada, o cabecalho e
localizavel em **16 de 16** blocos, cada um com seus proprios x0 — calibracao POR BLOCO,
exatamente o molde de `_localizar_cabecalho_tabela`:

| Coluna | Faixa de x0 nos 16 blocos |
|---|---|
| `Perigo` | 50,8 – 58,0 |
| `Exposicao` | 109,9 – 121,6 |
| `Medidas` | 472,1 – 483,7 |
| `controle` | 513,9 – 524,5 |

Outros invariantes, **16/16**: rotulo `Funcoes Envolvidas` (cargos); linha
`Atividade/Setor: <nome>` (nome do GHE — a linha-ancora do T65 **nao** carrega titulo, entao
`_extrair_titulo_ancora` devolve `""` em 16/16); token de grupo do risco sempre como **1a
palavra da linha** (contagem por 1a-palavra == contagem por ocorrencia, 16/16).

## 4. O que e realmente mais dificil

### 4.1 Typo na fonte quebra repertorio de lista fechada

Tokens de grupo com filtro de banda (1a palavra da linha E x0 na faixa `[perigo_x-16,
perigo_x+1]`), **109 riscos** em 16 blocos:

| Forma no documento | Ocorrencias | Sobrevive a normalizacao NFD+upper? |
|---|---|---|
| `Acidentes` | 44 | sim |
| `Ergonomico` (acento correto) | 18 | sim |
| **`Ergnomico`** (letra faltando) | **14** | **NAO** |
| `Quimico` | 13 | sim |
| **`Fisico`** grafado `Fisíco` (acento trocado) | **11** | sim |
| `Fisico` (correto) | 7 | sim |
| `fisico` (minuscula) | 2 | sim |

Riscos por bloco: `[7, 7, 4, 5, 7, 10, 12, 8, 8, 6, 7, 5, 6, 2, 8, 7]` = 109.

**25 de 109 (22,9%) tem grafia defeituosa.** Normalizar NFD+upper resolve `Fisíco`/`fisico`;
**nao** resolve `Ergnomico`, que perde uma letra — 14 de 109 (12,8%) exigem tolerancia alem de
normalizacao (prefixo, distancia de edicao, ou banda-x0 como criterio primario).

Descartados pelo filtro de banda (prosa, corretamente fora): `quimicos,` 3, `quimicos.` 1,
`quimicos` 1.

### 4.2 O silencio que isso produz — e por que NAO e um defeito do gate

`GHE14` (Portaria) tem **2 riscos reais**, ambos grafados `Ergnomico`. Um repertorio de lista
fechada no molde de `_TOKENS_CATEGORIA` devolveria `riscos=()` para esse bloco.

E `gate_forma_ghe` **aprova** um GHE com zero riscos: a condicao e
`all(risco.agente.strip() != "" for risco in ghe.riscos)`, e `all()` sobre sequencia vazia e
`True`; basta `nome` nao-vazio. Bloco com risco real sairia aprovado, vazio, em silencio.

**CORRIGIDO — isso NAO e um defeito latente, e ja foi julgado.** A `Decisao 003.DG-3`
(`DECISOES_ARQUITETURAIS.md` l. 2053) diz, textualmente: *"Observacao (NAO buraco —
reclassificada na 2a passada): card todo-`N/A` -> `riscos=()` -> gate APROVA (`all()` sobre
vazio e `True`); num cargo administrativo, GHE sem risco ocupacional e forma clinicamente
legitima."* Existe teste de regressao que trava o comportamento:
`test_transcritor_card.py::test_composicao_card_todo_na_sem_riscos_aprova_no_gate`.

O achado que sobrevive e mais estreito, e continua real: **a decisao 003.DG-3 foi medida sobre
a rota CARD (EBSERH, cargo administrativo) e e aplicada globalmente a `gate_forma_ghe`.** No
T65, rota GHE, ela cobre um caso que nao e o dela — `GHE14` nao e cargo administrativo sem
risco, e um bloco cuja tabela de risco tem 2 linhas. A decisao esta certa no escopo medido e
larga fora dele.

Consequencia de metodo: **mudar `gate_forma_ghe` NAO e fatia curta de IMPLEMENTACAO** — quebra
decisao registrada com teste de regressao. E o gate nao tem como distinguir os dois casos:
`GHEVerbatim` nao carrega o texto do bloco, so `nome`/`cargos`/`riscos`. O invariante teria de
morar em `preparar_ghes` (que tem `blocos`) ou no proprio parser da familia. Reabrir 003.DG-3
com escopo por rota e decisao de ARQUITETURA.

### 4.3 As colunas do T65 nao mapeiam 1:1 nas da familia 1

| Familia 1 (Consciente/Fascino) | Familia 2 (T65) |
|---|---|
| `GRUPO` | grupo (1a palavra da linha) |
| `PERIGO / ASPECTO` = **agente nomeado** (`Ruido`, `Destilados de Petroleo`) | `Perigo` = **descricao de perigo** (`Postura incorreta de trabalho`, `Queda em altura`) |
| `FONTE` = fonte geradora | `Origem do Risco` = fonte geradora |
| `AGRAVO` | `Risco` = possiveis lesoes ou agravos |
| — | `Exposicao` (Habitual/Eventual), probabilidade / severidade / grau |

`RiscoVerbatim.agente` alimenta o resolvedor de termos a jusante. No T65 **nao existe coluna de
agente nomeado**: mapear `Perigo` -> `agente` entrega ao resolvedor uma frase descritiva, nao um
agente. Decisao de ARQUITETURA, nao de implementacao — e o bloqueador real da escrita da
familia 2. `[INTERPRETADO — a consequencia a jusante foi lida no codigo do resolvedor, nao
medida em execucao]`

### 4.4 O T65 tem quantificacao; a familia 1 declara que nao ha

Secao `AGENTE AVALIADO | RESULTADO | LIMITE DE TOLERANCIA | SITUACAO` presente em **16/16**
blocos. A familia 1 crava `quantificacao=""` justificando "familia qualitativa — zero
quantificacao numerica medida nas 237 linhas-de-risco dos 19 blocos (003.DZ)". Verdadeiro para
o Fascino, falso para o T65. O dado existe e alimenta a cadeia LEO/NHO; ignora-lo e perda de
insumo, captura-lo e escopo alem de "copiar a familia 1".

## 5. O que continua verdadeiro sobre a rota LLM

`familia_nao_medida` e nao-bloqueante, entao o T65 **pode** atravessar pela rota LLM sem que
uma linha de parser seja escrita, se a cascata Gemini responder.

`[NAO VERIFICAVEL AQUI]` se a saida do LLM passa `gate_forma_ghe` no T65 — depende da saida do
modelo, e a VM do Cowork nao tem egress para `generativelanguage.googleapis.com` (HTTP 000). A
rodada tem de sair do PowerShell do Diovanni.

Ressalva permanente: a rota LLM e nao-deterministica, entao um acerto tirado por ela mistura
erro de transcricao com erro de regra clinica.

## 6. Reproducao

Scripts descartaveis (nao versionados), todos sobre o PDF acima:

1. `extrair_texto_pgr` -> `eh_cabecalho_ghe` -> `recortar_blocos_ghe` -> `avaliar_estrutura`.
2. `PalavraPDF` sobre `page.extract_words()` -> `_agrupar_linhas` -> `_parsear_bloco` bloco a
   bloco, capturando `FamiliaNaoReconhecida`.
3. Checagem de `upright` em todas as palavras da pagina do cabecalho.
4. Por bloco: linha agrupada contendo `{Perigo, Exposicao, Medidas, controle}` -> x0 por coluna;
   presenca de `Atividade/Setor:`, `Funcoes Envolvidas`, `AGENTE AVALIADO`.
5. Tokens de grupo: 1a palavra da linha, prefixo tolerante sobre NFD+upper, filtrada pela banda
   `[perigo_x-16, perigo_x+1]`; contagem por forma grafica e por bloco.
