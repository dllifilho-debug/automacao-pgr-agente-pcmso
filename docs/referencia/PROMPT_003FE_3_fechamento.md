# Prompt de fechamento — Sessao 003.FE

Instanciacao do `RITUAL_FECHAMENTO.md`. `main` = `c6bd7e0` (PR #315 mergeado, branch varrida
pelo passo 9 recem-criado). **Nenhuma D-ARQ criada ou tocada; nenhuma R-* criada, alterada ou
depreciada.** Logo: `gerar_indice_darq` NAO se aplica; `PROTOCOLO_AGENTE_MEDICO.md` NAO e tocado.

Ordem: fatias 1, 2, 3 — commit nominal proprio em cada uma.

---

## Fatia 1 — medicao do par 2 entra no git, e as pendencias novas

**Primeiro** o `git add` nominal do arquivo de medicao — as duas DT novas o citam, e pendencia
que aponta para arquivo fora do git e procedencia nao verificavel (foi exatamente o gap que o
Gauntlet apontou em `deed9f6`):

```
docs/referencia/MEDICAO_003FE_RICCO_e_parses.md
```

Os `PROMPT_*.md` seguem fora do git.

**Depois**, no mesmo commit ou em commit proprio, as entradas em `docs/PENDENCIAS_CLINICAS.md`

Duas entradas novas, ao fim do documento, seguindo a convencao de header existente.

**(a) Convencao nova — inserir ANTES das duas entradas**, como nota de convencao no topo do
documento (junto de onde o vocabulario de status e explicado, se houver; senao, imediatamente
antes da primeira `### D`):

```
> **Estado `DISPENSADA` (convencao, 003.FE).** Divida pode sair da lista por decisao, nao so
> por pagamento. `[DISPENSADA — <motivo>]` marca item medido, real, e deliberadamente nao
> endereçado; exige motivo escrito e nao reabre sem fato novo. Motivo da convencao: em 29/08/2026
> a lista tinha 73 headers abertos contra 26 fechados, e nenhum estado permitia encerrar item que
> ninguem vai pagar — backlog monotonico por desenho. Nao e D-ARQ: e convencao de vocabulario
> deste documento, promovivel se virar padrao.
```

**(b)**

```
### DH-003FE-01 — Acervo parcialmente versionado sob `.gitignore` que o proibe `[DISPENSADA — decisao do Diovanni, 29/08/2026]`

**Medido (29/08/2026).** `.gitignore` linha 22-23 diz *"Dados sensiveis de clientes (matrizes
reais, nao commitar)"* e ignora `matrizes_originais/`. Mas `git ls-files matrizes_originais/`
devolve **17 arquivos versionados** — `.gitignore` nao afeta arquivo ja rastreado. Dos 17, **um**
carrega dado pessoal: `PGR VIVERDE V02 - 03.02.25.pdf`, com **17 CPFs** no log de assinatura
digital (4 pessoas nominalmente identificadas da CMO Construtora, com e-mail e IP). Os outros 16
foram varridos: zero ocorrencia.

**Por que DISPENSADA.** Repositorio privado, sem exposicao conhecida; o dado e log de assinatura
de documento que ja e assinado; e o campo nao e usado nem sera — o motor le inventario de risco e
GHE, nada mais. Limpar exigiria reescrever o historico de 1132 commits com PRs mergeados, custo
desproporcional ao risco. **Decisao explicita do Diovanni em 29/08/2026**, registrada para nao ser
redescoberta e re-litigada a cada varredura.

**Reabre se:** o repositorio deixar de ser privado, ou o acervo passar a conter dado de
trabalhador (hoje nao contem — medido: matriz de exames tem 0 ocorrencias de CPF).
```

```
### DH-003FE-02 — Branches remotas orfas anteriores ao ritual `[ABERTA — higiene de ambiente, nao-bloqueante]`

**Medido (29/08/2026, primeira aplicacao do passo 9 do ritual).** Restam no remoto
`origin/claude/eloquent-mcnulty-e0cdc2` (`43a61bf`, 07/05/2026) e
`origin/claude/quizzical-rhodes-e3ae5f` (`d7cf602`, 06/05/2026) — **nao mergeadas em `main`**,
de ~4 meses atras, anteriores ao passo 9. Nao sao candidatas a `git branch -d` justamente por
nao estarem mergeadas: podem carregar commit unico, ou ser lixo de sessao abandonada.

**O que a resolucao exige.** Inspecionar `git log main..origin/claude/<nome>` em cada uma e
decidir: descartar (`push origin --delete`) ou recuperar o que houver. Nao-bloqueante; o passo 9
impede que o caso se repita daqui pra frente, mas nao varre o passivo.
```

```
### DT-003FE-01 — Segunda familia de parser: ancora `GHE NN` (T65) `[ABERTA — insumo medido, nao-bloqueante]`

**Medido (29/08/2026).** `extracao_pgr.py` localiza bloco por `DADOS GERAIS` + titulo `N.N`, e
existe **uma unica familia** no repo (`parser_familia_consciente.py`). Dos 4 PGRs varridos,
`DADOS GERAIS` aparece **so no Ricco ADM** (o unico que atravessou). O `PGR - ALT T65 2024.2026`
tem **16 blocos ancorados em `GHE 01`..`GHE 16`**, cada um com cargo, atividade e perigos
nomeados — ancora mais simples que a da familia existente.

**O que a resolucao exige.** Medir a forma da ancora no extrator do motor (`pdfplumber`, nao
`pdftotext` — os dois discordaram nesta medicao), escrever a familia 2 e medir o acerto contra a
matriz assinada do T65, que ja esta no acervo (par 8 do pareamento). Detalhe em
`docs/referencia/MEDICAO_003FE_RICCO_e_parses.md`. Faceta de `DT-003L-01`.
```

```
### DT-003FE-02 — Avaliacao Psicossocial sem periodico no gabarito Ricco `[A VALIDAR — divergencia clinica]`

**Medido (29/08/2026).** No par Ricco Administracao, `Avaliacao Psicossocial` sai `(ADM, MRO)` na
matriz assinada e `(ADM, MRO, PER)` na saida do motor, em **11 de 12 cargos**. `R-PSY-02`
prescreve `adm/per/MR` incondicional, derivado da medicao de corpus de 003.AH/003.EO.

**Nao e defeito de parser** — o motor aplica a regra escrita; o gabarito diverge dela. Ou a regra
esta larga demais, ou este documento e excecao. Exige contraste com os demais gabaritos
pos-26/05/2026 antes de tocar `R-PSY-02`; **nao alterar a regra com n=1**.
```

## Fatia 2 — bloco da sessao em `docs/HISTORICO_OPERACIONAL.md`

Ao fim do documento, apos o bloco `## Sessao 003.FD`:

```
## Sessão 003.FE — 28-29/08/2026 — IMPLEMENTAÇÃO

Aberta a partir de `main 5b4958b` (PR #314, merge de 003.FD), branch
`fix/003fe-periodicidade-celula`. Fecha a faceta de **escrita** de `DT-003EW-02`: a matriz
emitida nao imprimia a periodicidade, e sem ela o documento nao e assinavel.

**Entrega.** `documento_matriz.py::_formatar_celula`/`_formatar_momentos` passam a imprimir o
numero de meses grudado ao momento `PER` quando `periodicidade_meses != 12`, com excecao unica
para `rx_torax_oit`, que sempre imprime — excecao no dado (`periodicidade_sempre_visivel` em
`exames.yaml`), nunca literal no emissor (`D-ARQ-07`). 6 testes novos, cada um com a reversao
nomeada; varredura inversa 6/6.

**A regra nao foi derivada — foi medida no acervo.** 6 gabaritos assinados deram a forma; a
remedicao contra 28 documentos deu a validade: **4281 confirmam / 1805 contrariam** no agregado,
mas por ano do documento **2026 = 2896/122 (4,0% de contradicao)** e **2025 = 1323/1681 (55,9%)**.
A regra e a **convencao corrente do escritorio**, nao invariante do acervo historico — e o app
emite documento novo. Detalhe em `docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md`.

**Primeira medicao externa do projeto.** O app rodou local (`app_matriz_local.py`) sobre o PGR
Fascino e a saida foi comparada com a matriz assinada da mesma obra (Dra. Carolini, CRM-GO
14.864): **353 de 364 celulas reproduzidas = 97,0%**, 32 de 40 funcoes com conjunto de exames
identico. As 11 celulas faltantes concentram-se em **Armador e Serralheiro** (`R-PKG-ARMADOR` e
`R-PKG-SOLD` nao disparam sem `fumos_metalicos` no inventario — divergencia ja prevista por
`R-GHE-05`). As 4 sobrando sao biomonitoramento que a medica nao pediu, e ela escreveu a razao a
mao na celula: *"Incluir no word do PCMSO, risco baixo no PGR para acetona e metiletilcetona"* —
regra clinica ainda nao formalizada. Em `docs/referencia/MEDICAO_FASCINO_vs_GABARITO.md`.

**Segunda e terceira medicoes externas — e o gargalo ficou nomeado.** O app rodou local sobre
mais tres PGRs. **Ricco Administracao atravessou: 41 de 45 celulas = 91,1%**, 11 de 12 funcoes
com conjunto identico, **zero exame emitido a mais**; as 4 faltantes sao o pacote de atividade
critica numa unica funcao. **Sinduscon e T65 nao atravessaram** — `segmentacao_implausivel`
(0 blocos em 59 paginas) e `familia_nao_medida`. A causa e uma so e esta medida: o extrator
localiza bloco por `DADOS GERAIS`, presente **so** no PGR que atravessou, e o repo tem **uma
unica familia de parser**. O T65 traz 16 blocos ancorados em `GHE 01`..`GHE 16`, estrutura mais
simples que a da familia existente, que o motor nao enxerga. **O gargalo nao e a decisao
clinica — e a porta de entrada**, exatamente o que o painel declara desde `DT-003L-01`, agora com
numero em documento real. Em `docs/referencia/MEDICAO_003FE_RICCO_e_parses.md`.

**Instrumento: Word COM deixou de ser necessario.** `soffice --convert-to docx` + `python-docx`
reproduz a medicao Word COM registrada em `GABARITO_003EX_audiometria_dem.md` — 3 de 3 documentos
identicos na cobertura de audiometria; a unica divergencia (1 cargo) e atribuivel a `6f2e9f0`,
nao a conversao. Medicao sobre o acervo passa a rodar no ambiente do Arquiteto.
Em `docs/referencia/VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`.

**Ciclo do Gauntlet: 2 rodadas — 1 rejeicao, 1 aprovacao.** A rejeicao foi de **procedencia**: o
comentario do teste fundava a regra num arquivo nunca commitado, enquanto a propria
`DT-003EW-02` registrava no git contradicao da mesma regra e dizia *"refino pendente antes de
implementar a formatacao"*. Corrigido pelo prompt #2 (4 fatias). Na 2a rodada o Critico verificou
por `git diff-tree` que as arvores de `15dec76` e `deed9f6` sao identicas, leu `8c82512` linha a
linha, e conferiu **alcancabilidade em producao** (`web_matriz.py:139` passa
`protocolo.vocabulario.exames` verbatim) — tres verificacoes que o Arquiteto nao fizera.

**Commits:** `deed9f6` (fix), `15dec76` (registro de suite), `84fd483` (medicoes), `8c82512`
(procedencia), `5d24f8e` (DT reconciliada), `4fa18bd` (passo 9 do ritual). Merge `c6bd7e0`,
PR #315.

**Verificacao:** suite **1160 passed, 6 skipped** (`python -m pytest agente_medico/tests/ tests/`,
1444.52s, medida em `4fa18bd`); `mypy --strict agente_medico/superficie` limpo, 11 arquivos
(medido em `deed9f6`; fatias seguintes so tocaram comentario e markdown).

**Divida paga sem sessao META:** `DT-003FD-02` (registro de suite morava onde a Regra zero do
Critico proibe ler) — `15dec76` e a primeira materializacao da correcao estrutural que aquela DT
nomeava: a contagem na mensagem do commit. O paliativo da excecao nominal pode sair.

**Pendencias.** `DT-003EW-02` faceta de escrita IMPLEMENTADA, segue ABERTA pelos 4% residuais de
2026 (122 ocorrencias nao investigadas nominalmente). Novas: `DH-003FE-01` (acervo parcialmente
versionado — **DISPENSADA**, decisao do Diovanni), `DH-003FE-02` (branches remotas orfas de maio),
`DT-003FE-01` (familia 2 do parser, ancora `GHE NN` — insumo medido) e `DT-003FE-02` (psicossocial
sem periodico no gabarito Ricco, `A VALIDAR`). Convencao nova: estado `DISPENSADA` no vocabulario de pendencias.

**Licoes de metodo.**
- **Janela de leitura tratada como fim de bloco, 12a ocorrencia da classe "leio a forma, nao a
  prova" — e a mais cara ate agora.** O Arquiteto leu `DT-003EW-02` com `grep -A18` e nao viu que
  o bloco continuava: duas telas abaixo estavam a contradicao medida em 003.EY e a frase *"refino
  pendente antes de implementar a formatacao"*. Custou um PR rejeitado e um prompt cirurgico
  inteiro. **O gate de abertura da sessao nao cobria a DT que era o eixo do artefato** — mesma
  falha de 003.FA, agora sobre `PENDENCIAS_CLINICAS.md` em vez de `DECISOES`.
- **Comando entregue sem poder ser testado falha.** Tres comandos PowerShell do Arquiteto
  quebraram em sequencia (wildcard nao expandido; `python-docx` nao le `.doc`; Word COM com
  `Visible=false` travou em dialogo invisivel e deixou processo zumbi de ~4000 CPU-segundos).
  Tudo que o Arquiteto rodou no proprio ambiente funcionou. **Regra derivada: trabalho de medicao
  roda onde pode ser verificado antes de ser entregue.**
- **Contagem par nao prova balanceamento.** Na conferencia do prompt #2, duas crases orfas se
  compensavam e o contador dava par. O defeito so apareceu ao casar os pares. Mesma classe.
- **Preocupacao com dado pessoal travou o projeto duas vezes** (LGPD do acervo, depois CPF no
  git). Nos dois casos a medicao mostrou risco baixo e a cautela custou fluxo. Registrado a
  pedido do Diovanni.
```

## Fatia 3 — `docs/PAINEL_ESTADO.md`

**Baseline** (re-tirado em todo fechamento que produza commit, `D-ARQ-85` cl.1) — substituir a
linha `**Baseline:**` por:

```
**Baseline:** branch `fix/003fe-periodicidade-celula` sobre `main 5b4958b` · **1160 passed, 6 skipped** *(medido em `4fa18bd`, sessão 003.FE)* · PROTOCOLO v91 · DECISOES v186
```

**Tres numeros clinicos** — substituir a linha seguinte por:

```
**Três números clínicos avaliados, não re-tirados nesta tiragem** — 003.FE é IMPLEMENTAÇÃO de apresentação: nenhuma R-* criada, alterada ou depreciada; vocabulário/CAS intocado; as 3 dívidas que travam produção seguem as mesmas. Nenhum dos três se moveu. Decisão declarada sob `D-ARQ-85` cl.1.
```

A linha `**Tiragem corrente:**` **NAO muda** (003.EZ · 16/08/2026) — os tres numeros nao foram
re-tirados. Paragrafos de tiragem sao registro historico e nao sao reescritos (`D-ARQ-85`).

## Fatia 4 — `/kickoff` passa a reconhecer `DISPENSADA` (sem ela a convencao nasce morta)

`.claude/skills/kickoff/SKILL.md`, item **5** da secao de coleta. O texto atual manda listar
todo header `### DT-`/`### DH-` cujo marcador **NAO contenha FECHADA, RESOLVIDA ou REENQUADRADA**.
`[DISPENSADA — <motivo>]` nao contem nenhuma das tres, logo **seria listada como aberta para
sempre** — a convencao da Fatia 1 tiraria o item da lista apenas no papel.

Acrescentar `DISPENSADA` ao conjunto de exclusao do item 5, preservando o resto da frase e o
parenteses de correcao 003.DQ que ela ja carrega. O vocabulario de exclusao passa a ser
**FECHADA, RESOLVIDA, REENQUADRADA, DISPENSADA**.

`[MEDIDO — 29/08/2026: o filtro invertido do item 5 nao exclui DISPENSADA; verificado contra o
texto do SKILL.md em `c6bd7e0`.]` Achado na conferencia deste proprio prompt de fechamento —
classe 11 do `/conferir` (clausula que contradiz o corpo do proprio artefato).

## Verificacao

```
python -m pytest agente_medico/tests/ tests/
```

Previsao: **1160 passed, 6 skipped — inalterado.** Fatias so tocam markdown.
`mypy` e `gerar_indice_darq` nao se aplicam.

Push com autorizacao. Depois do merge, passo 9 de novo.
