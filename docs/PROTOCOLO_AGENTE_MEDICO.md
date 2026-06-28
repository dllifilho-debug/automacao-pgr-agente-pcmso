# PROTOCOLO DO AGENTE PCMSO — v2

**Fonte primária:** Entrevista assíncrona com Dra. Carolini Polesso (Coordenadora PCMSO), 47 áudios em 16/05/2026 + segunda rodada de validação em 17/05/2026.
**Caso de referência:** PGR Viverde V02 (03.02.2025) + Matriz RQ.61 Viverde (06.03.2025) — **validada como correta** pela Dra. Carolini.
**Status:** Protocolo validado. Pendências de v1 fechadas.

Cada regra tem ID estável (`R-CATEGORIA-NN`). O ID **não muda** entre versões — alterações de conteúdo geram nota de revisão na própria regra.

Convenções de status:
- `[VALIDADO]` — extraído diretamente da entrevista com a Dra. Carolini (16-17/05/2026),
  sem ambiguidade. CONGELADO a partir de 002.M: a fonte primária não faz mais validação
  prévia. Regras `[VALIDADO]` são base estável; não reabrem exceto por norma vigente que
  as contradiga.
- `[INFERIDO]` — deduzido de outras respostas da entrevista. Não será mais promovido pela
  Dra. Carolini; resolução segue a hierarquia de D-ARQ-22.
- `[A VALIDAR — Carolini]` — DESCONTINUADO a partir de 002.M. Itens reclassificados em
  `[DERIVADO]` ou `[INTERPRETADO]`.
- `[DERIVADO — fonte]` — resolvido após 002.M por fonte objetiva, seguindo a hierarquia de
  4 níveis de D-ARQ-22 Parte A (parar no primeiro que resolver): (1) norma vigente conferida
  no site oficial do MTE → `[DERIVADO — NR-x item y]`; (2) matriz validada como precedente
  (RQ.61 Carolini / matriz Patrícia) → `[DERIVADO — RQ.61/Patrícia]`; (3) analogia direta com
  regra `[VALIDADO]` → `[DERIVADO — analogia R-XXX]`. Alta confiança; a fonte é nomeada NO
  PRÓPRIO MARCADOR, não apenas no corpo. O nível 4 (norma/matriz/analogia não resolvem) produz
  `[INTERPRETADO]`, abaixo — saída da mesma árvore de decisão, não um estado paralelo.
- `[INTERPRETADO — prioridade na revisão de saída]` — decisão do Arquiteto onde norma/
  matriz/analogia não foram conclusivas. NÃO houve crivo clínico prévio. É a categoria que
  a revisão de saída (médica lendo a matriz gerada) deve inspecionar PRIMEIRO. Não é um
  buraco permanente: é o item de maior incerteza no ciclo PDCA, marcado para atenção.

---

## 1. GATES DE ACEITAÇÃO DO PGR

São condições eliminatórias. Se qualquer gate falhar, o PGR é rejeitado e a matriz não é montada.

### R-PGR-01 — Assinatura por engenheiro `[VALIDADO]`
PGR deve ser assinado por **engenheiro de segurança do trabalho**. Assinatura apenas por técnico → rejeitado.
**Base normativa:** NR-18 (conforme citado pela Dra. Carolini).

### R-PGR-06 — Validade vigente `[VALIDADO]`
PGR com validade emitida há **2 anos ou mais** → rejeitado. Solicitar atualização à empresa.

---

## 2. ORDEM DE LEITURA DO PGR

### R-PGR-02 — Sequência de leitura `[VALIDADO]`
A leitura é **sequencial e gera a matriz em paralelo** (não há leitura prévia completa antes de montar):

1. **Cabeçalho** — verificar gates (R-PGR-01 e R-PGR-06)
2. **Inventário de riscos** — riscos identificados por GHE
3. **Agravos à saúde** — efeitos associados a cada risco
4. **EPIs indicados por GHE** — sinal indireto de risco (ver R-PGR-03)
5. **Padronização final** — aplicar NR-07 + NR-15 + protocolos especiais

A **fonte geradora do risco** é consultada apenas quando necessária para esclarecer dúvida.

### R-PGR-03 — Sinal indireto via EPI `[VALIDADO]`
Quando o PGR exige **máscara de proteção respiratória (PFF2, PFF3 ou facial)** mas **não declara risco químico no inventário** → presumir exposição química respiratória.

**Consequência mínima:** incluir espirometria (ver R-ESP-01).

**Base normativa:** NR-07, item de espirometria. Confirmado pela Dra. Carolini como exigência normativa, não conduta clínica isolada.

### R-PGR-04 — Informação crítica ausente `[VALIDADO]`
Se a **descrição da composição de produtos químicos** estiver ausente ou inadequada → exigir FDS antes de montar a matriz. Sem composição química resolvida, a matriz não pode ser fechada.

### R-PGR-05 — PGR mal escrito `[VALIDADO]`
PGR com riscos genéricos, sem quantificação, sem agentes especificados:
1. Solicitar FDS dos produtos à empresa
2. Conversar com o elaborador do PGR para esclarecer

Não rejeitar o PGR por essa razão.

---

## 3. MODELO DE GHE

### R-GHE-01 — Unidade de análise `[VALIDADO]`
A análise é feita **GHE a GHE**. Todas as funções dentro de um mesmo GHE recebem **matriz idêntica de exames e periodicidade**. Não há diferenciação por cargo dentro do mesmo GHE.

### R-GHE-02 — Risco implícito pelo cargo `[VALIDADO]`
Cargos cuja **operação geradora de risco é indissociável da função-fim** recebem os exames desse risco **mesmo quando o inventário do PGR não declara explicitamente** a exposição.

**Critério de aplicabilidade (refino 002.L-estudo).** O risco implícito por cargo só vale quando a operação causadora é a atividade-fim do cargo — nunca pela mera denominação. A NR-01/NR-07 (Portaria 567/2022) não reconhece "risco por denominação de cargo"; o risco é definido pela exposição real classificada no PGR. Quando a operação de risco é **contingente** (pode ou não ocorrer na função), o risco não é atribuído automaticamente — recai em confirmação documental (ver R-GHE-05).

**Caso âncora — soldador (industrial):** soldar é a atividade-fim → fumos metálicos são indissociáveis. Mesmo sem o inventário citar, a presença do cargo implica exposição. Aplicar protocolo de fumos metálicos (ver R-PKG-SOLD).

**Contra-exemplo — serralheiro de obra:** solda é contingente (a função pode ser só corte a frio, dobra, gradil, esquadria). NÃO atribuir fumos/Mn/CO por cargo. Ver R-GHE-05.

Esta regra é a expressão clínica do princípio *"não existe solda sem fumos metálicos"* — **desde que soldar seja a atividade-fim**. O sistema aceita risco implícito por cargo como cidadão de primeira classe, condicionado ao critério de indissociabilidade.

**Base:** Dra. Carolini, R1 (05/2025); NR-01/NR-07 (Portaria 567/2022).

### R-GHE-03 — Múltiplos riscos, mesmo exame `[VALIDADO]`
Quando o mesmo exame é exigido por riscos distintos no mesmo GHE → **linha única** na matriz. A periodicidade não se altera em função do número de riscos que pedem o exame.

### R-GHE-04 — Risco listado mas não convincente `[VALIDADO]`
Quando o PGR lista um risco que parece não realista para o GHE, a Dra. Carolini **segue o inventário** sem reinterpretar nem rejeitar. O documento é a fonte de verdade do escopo de risco.

**Implicação para o agente:** não implementar lógica de "filtragem clínica de riscos do PGR". O inventário é canonical.

### R-GHE-05 — Risco contingente exige confirmação documental `[VALIDADO]`
Cargo cuja operação de risco é **contingente** (não indissociável da função-fim) não recebe o risco por atribuição implícita. O risco entra como **pendência de confirmação documental**: solicitar PGR/FDS que confirme a operação (ver R-FDS-01, R-PGR-04, R-PGR-05).

- **PGR/FDS confirma a operação de risco** (ex.: serralheiro que solda — MIG/TIG/eletrodo) → aciona exatamente os exames do risco confirmado (ex.: pacote de fumos metálicos, idêntico ao soldador).
- **PGR/FDS descreve apenas operações sem o risco** (ex.: serralheiro só com corte a frio, dobra, fixação de gradil, montagem de esquadria) → não aciona os exames daquele risco.

**Caso âncora — serralheiro de obra.** No caso Viverde (RQ.61, GHE 10), o pacote de fumos/Mn disparou porque o PCMSO declarava agente medido ("Risco Cromo abaixo de 10% LT da ACGIH") — exposição confirmada documentalmente, não atribuição por cargo.

**Implicação para a taxonomia (`cargos.yaml.riscos_implicitos`, D-ARQ-02/D-ARQ-12):** o campo `riscos_implicitos` só contém riscos indissociáveis. Serralheiro NÃO recebe `{solda, fumos_metalicos, manganes}` ali. (O hardcode `serralheiro → cromo` do motor legado em `modules/agente_medico_ia.py` está obsoleto e contradiz esta regra — não replicar no motor novo.)

**Nota de implementação (002.M).** R-GHE-05 é clinicamente completa, mas depende de um
dado que o motor ainda não modela: a **operação confirmada** do GHE. `GHEPGR` (`tipos.py`)
carrega `cargos`, `riscos` (agentes), `epis`, `produtos_quimicos`, `psicossocial` — não
carrega operações/tarefas. Sem isso o motor não avalia "a operação de solda foi confirmada".
Endereçado por D-ARQ-23 (operação como dado de primeira classe). Até lá, R-GHE-05 não é
executável no motor novo.

**Caso âncora documentado — serralheiro Viverde (Est-09).** O PGR Viverde declara, para o
serralheiro, os agentes `radiacao_uv_ir` (solda) e `dioxido_de_titanio` (0,008 mg/m³), além
de ruído e acidente; descreve nas tarefas ET38-ET42 "solda com eletrodo revestido". NÃO
declara `fumos_metalicos` nem cromo no inventário de entrada. O cromo ("Risco Cromo abaixo
de 10% LT da ACGIH") aparece só na RQ.61, que é a matriz de SAÍDA validada — não na entrada.
Logo, o motor processando o PGR puro vê marcadores de solda (radiação UV de solda + TiO2,
constituinte do revestimento rutílico do eletrodo) mas nenhum agente que dispare R-PKG-SOLD/
R-RX-02 (gatilho `fumos_metalicos`). Sem modelar a operação (D-ARQ-23), o motor NÃO reproduz
o pacote de fumos da RQ.61 — divergência esperada e rastreada, não erro do fixture. Fundamento
técnico: fumo de solda de eletrodo revestido é mistura (Fe, Mn, Cr, Ni + constituintes do
revestimento como TiO2 e fluoretos); TiO2 e cromo são dois constituintes do mesmo fumo, não
agentes contraditórios; Mn está presente em praticamente todo eletrodo (R-FDS-05). Fontes
técnicas: OSHA FS-3647; literatura de composição de eletrodo revestido.

**Base:** Dra. Carolini, R1 (05/2025); NR-01/NR-07 (Portaria 567/2022). Resolve DT-002K-02.

---

## 4. INTERPRETAÇÃO DE FDS

### R-FDS-01 — Quando exigir FDS `[VALIDADO]`
Solicitar FDS à empresa quando:
- A composição química está ausente ou genérica no PGR
- O cargo pressupõe exposição química não inventariada (ex: pintor, soldador)
- O PGR é mal escrito (ver R-PGR-05)

### R-FDS-02 — Priorização de leitura `[VALIDADO]`
Ao ler uma FDS, priorizar nesta ordem:
1. **Composição** (seção 2 / 3)
2. **Toxicologia** (seção 11)
3. **EPIs recomendados** (seção 8)

### R-FDS-03 — Cutoff por concentração `[VALIDADO]`
- **Componentes com concentração > 5%** → considerar e pedir biomonitoramento
- **Componentes cancerígenos** (classificados pela IARC) → considerar **independente da concentração**

### R-FDS-04 — FDS com descrição genérica `[VALIDADO]`
FDS com termo genérico (ex: "hidrocarbonetos aromáticos") sem especificar o componente → resolver pelo **CAS** de cada constituinte.

**Caso âncora — benzeno:** se o CAS revelar presença de benzeno, **independente da concentração**, aplicar protocolo benzeno (ver R-PKG-BZ).

#### Nota de procedência — cutoff de 5% e carcinógeno-independe (003.G) `[INTERPRETADO]`
O limiar **5%** de R-FDS-03 é conduta da Dra. Carolini alinhada a GHS/ABNT 14725, **sem âncora em NR** — mantém-se `[VALIDADO]` como conduta, **não** `[DERIVADO]`. A cláusula "carcinógeno independe de concentração" (R-FDS-03 IARC; R-FDS-04 benzeno via CAS) é boa prática INCA/Anexo V, `[INTERPRETADO]` — não é ">0%" escrito na norma. Por D-ARQ-33 (caminho C), o 5% é **limiar-dado** (constante de protocolo) e a materialidade é **predicado tri-estado derivado** consumido por cada lado da mesa (médico via R-FDS-03; engenheiro via protocolo-engenheiro futuro); os bypasses do cutoff são uma **lista** (carcinógeno IARC, sensibilizante, demais perigos da frase-H), não um critério binário. IDs R-FDS-03/04 inalteradas, semântica intacta — esta nota é só procedência.

### R-FDS-05 — Eletrodo de solda `[VALIDADO]`
O metal de adição do eletrodo só é identificável pela FDS específica do eletrodo. **Solicitar à empresa.** Praticamente todos os eletrodos contêm manganês → presumir Mn na ausência de informação contrária.

### R-FDS-06 — Confiança na FDS `[VALIDADO]`
Não há classe de produto químico em que a Dra. Carolini sistematicamente desconfia da FDS. O único cenário de desconfiança é a **FDS com descrição genérica** (R-FDS-04), resolvido via CAS.

**Implicação para o agente:** confiar nos dados de FDS é o default; investigação adicional só é disparada por genericidade da descrição.

---

## 5. REGRAS POR TIPO DE EXAME

### 5.1 Exame Clínico

#### R-CLI-01 — Default anual `[VALIDADO]`
Exame clínico **anual** é o piso — vale inclusive para administrativo sem risco.
**Justificativa clínica:** trabalhadores com doença crônica devem ter clínico anual; como não há triagem prévia, padroniza-se anual para todos.

#### R-CLI-02 — Quadro 1 e Quadro 2 do Anexo I (NR-07) `[VALIDADO]`
Exposição a agente biomonitorado do Anexo I (Quadro 1 ou Quadro 2) demanda clínico **semestral**. Quando exposto a agentes de **ambos os Quadros**, registrar em **uma única linha** semestral (não duplicar).

> **Changelog 003.AA (mesma ID — relabel sem mudança de saída).** "Anexo I / Anexo II" → "Quadro 1 / Quadro 2 do Anexo I" (567/2022; "Anexo II" da NR-07 é ruído, não químico-com-LT). O conjunto de agentes que dispara o semestral não muda → saída estável → ID preservada.
> **Ressalva `[INTERPRETADO — prioridade na revisão de saída]`:** o semestral é conduta da Dra. Carolini, não a NR-07 — item 7.5.8 fixa clínico **anual** para exposto (menor a critério médico). A borda "carcinógeno só de Anexo V, sem indicador no Anexo I, dispara semestral?" não está cravada (fonte primária congelada desde 002.M) — inspecionar na revisão de saída.

#### R-CLI-03 — Manganês fora do Anexo I `[VALIDADO]`
O **manganês** é o único agente fora do Anexo I (Quadros 1 e 2) da NR-07 que dispara clínico semestral. Base: NR-15 — exposição a Mn exige avaliação biológica independente do limite de tolerância.

> **Changelog 003.AA (mesma ID).** "fora dos Anexos I e II" → "fora do Anexo I (Quadros 1 e 2)": Mn não consta em nenhum Quadro do Anexo I; o antigo "Anexo II" era o balde químico-com-LT (vocabulário pré-567), hoje inexistente nesse sentido. Conteúdo inalterado. A unicidade sob o eixo novo segue `[VALIDADO]`; reconfirmar de passagem se algum agente de Anexo V a altera (`[INTERPRETADO — revisão de saída]`).

#### R-CLI-04 — Risco físico isolado `[VALIDADO]`
**Nenhum** risco físico (ruído, calor, vibração) isoladamente justifica clínico semestral. O default anual prevalece.

### 5.2 Audiometria

#### R-AUD-01 — Indicações para 12M (adm/per/MR) `[VALIDADO]`
Audiometria **12 meses** em **adm/per/MR** quando houver pelo menos uma das condições:
- Ruído (qualquer nível, mesmo abaixo do nível de ação, **se combinado** com outras condições abaixo)
- Motorista de equipamento pesado
- Trabalho em altura
- Espaço confinado
- Exposição a ototóxicos
- Exposição a vibração (corpo inteiro ou mãos-braços)

#### R-AUD-02 — Audiometria no demissional `[VALIDADO]`
Demissional **é executado** apenas quando:
- **Ruído acima do nível de ação**, OU
- Combinação **ruído + ototóxico + vibração**

Para trabalho em altura, equip. pesada e espaço confinado **sem ruído**: faz adm/per/MR, **não faz** demissional.

#### R-AUD-03 — Validade do demissional `[VALIDADO]`
Audiometria realizada há **mais de 120 dias** → refazer no demissional.

### 5.3 Espirometria

#### R-ESP-01 — Default e exceção via EPI `[VALIDADO]`
- **Default** = 24 meses (adm/per/MR/dem) — exposição a químico respiratório, fumos metálicos
- **Exceção (sinal por EPI):** PGR exige máscara (PFF2/PFF3) sem risco químico declarado → espirometria **adm + MR apenas** (sem periódico, sem demissional)

**Base normativa:** NR-07, item de espirometria. Confirmado pela Dra. Carolini como exigência normativa.

### 5.4 Raio-X de Tórax (OIT)

#### R-RX-01 — RX de tórax OIT (sílica/asbesto e PNOS) `[VALIDADO]`
Periodicidade do RX de tórax padrão OIT conforme **Anexo III da NR-07 (Portaria 567/2022)**. Depende de: agente, faixa de exposição vs. LEO, existência de avaliação quantitativa e tempo de exposição acumulado.

**Sílica / asbesto — COM avaliação quantitativa periódica:**

| Faixa (CLSC vs. LEO) | RX tórax OIT |
|---|---|
| ≤ 10% LEO | admissional apenas |
| 10% < CLSC ≤ 50% LEO | adm + 60M até 15 anos → 36M após |
| 50% < CLSC ≤ 100% LEO | adm + 36M até 15 anos → **24M** após |
| > 100% LEO | adm + 12M desde o início |

**Sílica / asbesto — SEM avaliação quantitativa** (canteiro sem laudo de higienista; caso mais comum):
- adm + **24M** até 15 anos de exposição → 12M após.

**PNOS** (poeiras de menor toxicidade), com ou sem medição:
- adm + **60M**. Nunca 24M.

**Notas:**
- "Sem avaliação quantitativa" é estado distinto de "qualitativa": dispara **24M**, não 12M. Corrige A-VAL-06 (v2), que simplificou demais.
- A periodicidade da **espirometria** (adm + 24M, R-ESP-01) é independente do RX — não confundir o 24M dos dois exames.
- O corte de 15 anos é **tempo de exposição acumulado** → resolvido pelo agendador, não pelo motor (ver D-ARQ-19).

**Implementação (002.L0, D-ARQ-20).** R-RX-01 é implementada como família de regras de periodicidade constante em `regras.yaml`, uma por faixa:

| Entrada | Predicado (`quando`) | Periodicidade | Encurtamento (>15a) |
|---|---|---|---|
| R-RX-01-adm | silica_asbesto_leo_ate_10 | só admissional | — |
| R-RX-01-sem | silica_asbesto_sem_medicao | 24M | → 12M |
| R-RX-01-baixa | silica_asbesto_leo_10_50 | 60M | → 36M |
| R-RX-01-media | silica_asbesto_leo_50_100 | 36M | → 24M |
| R-RX-01-alta | silica_asbesto_leo_acima_100 | 12M | — |
| R-RX-01-pnos-ate10 | pnos_leo_ate_10 | só admissional | — |
| R-RX-01-pnos-10a100 | pnos_leo_10_100 | só admissional (motor) | — |
| R-RX-01-pnos-acima100 | pnos_leo_acima_100 | 60M | — |
| R-RX-01-pnos-sem | pnos_sem_medicao | 60M | — |

`R-RX-01` permanece o ID clínico estável; as entradas `R-RX-01-*` são implementação (D-ARQ-20). **Estado contraditório:** se o PGR declara `pct_LT` e ausência de avaliação quantitativa ao mesmo tempo, o motor emite pendência bloqueante (não escolhe faixa) — input incoerente vira pedido de correção, não chute (D-ARQ-08/13). **Valores conferidos `[DERIVADO — NR-7 Anexo III Quadro 1]`:** periodicidades, limiares e corte de 15 anos conferidos contra o texto literal do Anexo III da NR-07, Quadro 1 (Portaria MTP 567/2022), no site do MTE (002.N). Faixas fechadas com limite superior inclusivo (`≤`): >10 e ≤50; >50 e ≤100; >100. Variável de roteamento é o CLSC = limite superior do IC 95% da média aritmética (distribuição lognormal), conforme definição literal do Quadro 1 — NÃO é percentil 95. NOTA 2 do Quadro 1: trabalhador com exposição reduzida que esteve em concentração maior por ≥1 ano mantém o intervalo do período de maior exposição (a modelar — ver DT). PNOS segue o Quadro 2, não o Quadro 1 (ver R-RX-01-pnos e DT própria).

**PNOS — refinamento do Quadro 2 (002.X).** A entrada única `R-RX-01-pnos` (60M constante) está DEPRECATED, sucedida pela família de 4 faixas acima (mesma razão de D-ARQ-20 já usada no Quadro 1). Texto literal do Quadro 2 conferido (Anexo III NR-07, Portaria 567/2022, site MTE):
- pnos_leo_ate_10 (CLSC ≤ 10% LEO) → só admissional.
- pnos_leo_10_100 (10% < CLSC ≤ 100% LEO) → admissional; RX único **após 5 anos** de exposição (gatilho de tempo acumulado → agendador, D-ARQ-19, em Motivo.detalhe); **repetir a critério clínico** (não-periódico → lembrete operacional, D-ARQ-05). NÃO é 60M recorrente. `[DERIVADO — NR-7 Anexo III Quadro 2 (Portaria 567/2022)]`; a modelagem "evento único + lembrete" (vs. periodicidade) é `[INTERPRETADO]`.
- pnos_leo_acima_100 / pnos_sem_medicao → adm + 60M ("a cada 5 anos").
Fração do PNOS é sempre RESPIRAVEL (Quadro 2 mede "poeira respirável"); sem ramo TOTAL.

**PNOS — implementação (002.Y).** A família `R-RX-01-pnos-*` foi materializada em código (PR #49, commit 9bb243e): predicados de faixa `pnos_leo_ate_10`/`pnos_leo_10_100`/`pnos_leo_acima_100`/`pnos_sem_medicao` (predicados.py) + ramo PNOS no LEO-resolver (3 mg/m³ resp, nível 4) + 4 entradas em regras.yaml (status INTERPRETADO) + `R-RX-01-pnos` única marcada DEPRECATED (mantida por contrato de ID; carregador passa a filtrar DEPRECATED). Periodicidades: ate_10 e 10_100 → só admissional; acima_100 e sem_medicao → adm + 60M. O roteamento de PNOS medido em mg/m³ usa injeção de fração RESPIRAVEL (D-ARQ-29). Pendências abertas: lembrete "repetir após 5 anos a critério clínico" da faixa 10_100 não materializado (DT-002Y-01); validação contra Viverde real adiada (DT-002Y-02).

**LEO do PNOS — reconciliação (002.X).** O rodapé do Quadro 2 define PNOS pela condição "não possuir um LEO definido", mas a tabela roteia por % do LEO. Reconciliação: o material é PNOS porque não tem LEO *próprio*; o roteamento usa o LEO *genérico* de PNOS = TLV-PNOS da ACGIH = **3 mg/m³ (respirável)**, via NR-09 item 9.6.1.1 (nível 4 do LEO-resolver, D-ARQ-24). `[DERIVADO — ACGIH TLV-PNOS, via NR-9 9.6.1.1]` no valor; `[INTERPRETADO]` na articulação "este genérico alimenta o Quadro 2" — não está escrita na norma; é o item de maior incerteza desta sessão, inspecionar PRIMEIRO na revisão de saída (D-ARQ-27).

**Pré-requisito para o predicado `pnos` ser computável.** Para o motor classificar um agente como PNOS, `agentes.yaml` precisa carregar as 3 condições ACGIH 2017 (rodapé do Quadro 2): (a) sem LEO próprio definido; (b) insolúvel/pouco solúvel; (c) baixa toxicidade (não citotóxico/genotóxico/reativo, não radioativo, não sensibilizante). Sem esse metadado o predicado `pnos` não tem como ser decidido. Implementação futura.

**Asbesto — origem do LEO (002.X).** A periodicidade do asbesto NÃO muda: o Quadro 1 já o cobre nas mesmas faixas de sílica. O que faltava era a origem do LEO. Resolvido: não há LEO setorial de mineração para asbesto (nível 1 vazio); LEO = nível (3) do resolver = LT da NR-15 Anexo 12 = **2,0 f/cm³** (fibras respiráveis), FIXO (não fórmula), unidade f/cm³ (não mg/m³), fração sempre respirável, pct_quartzo irrelevante. Fibra respirável = Ø<3µm, comprimento>5µm, razão L/D>3:1. Anfibólios (crocidolita/amosita/etc.) proibidos, sem LT. `[DERIVADO — NR-15 Anexo 12 itens 12/12.1 (Portaria SSST 1/1991 e 22/1994); confirmar texto oficial MTE antes de considerar VALIDADO]`. Detalhe arquitetural em D-ARQ-24 changelog 002.X.

**Carvão mineral — lacuna (002.X).** O Quadro 1 vigente é "Sílica, Asbesto **ou Carvão Mineral**" (incluído pela 567/2022). O predicado `silica_asbesto_*` cobre 2 dos 3 agentes do Quadro 1 — fere D-ARQ-06. Ver DT-002X-01 (LEO do carvão a resolver). Até lá o carvão não entra na família de roteamento.

**Demissional condicional do Quadro 1 (002.X) — dado para o agendador.** A norma adiciona demissional condicionado ao reaproveitamento (D-ARQ-11/19): último exame há mais de **2 anos** nas faixas ≤10% e 10–50%; há mais de **1 ano** nas faixas 50–100%, >100% e **sem-avaliação**. A fronteira é em 50%; sem-avaliação usa 1 ano. Motor emite a faixa-base; o agendador aplica o demissional condicional com essa granularidade.

**Base normativa:** Anexo III da NR-07 (Portaria 567/2022). Validação clínica: Dra. Carolini, 05/2025.

**TODO normativo — RESOLVIDO em 002.N `[DERIVADO]`:** faixas, periodicidades e corte de 15 anos do Quadro 1 (sílica/asbesto) conferidos contra o texto literal do Anexo III (Portaria 567/2022, site do MTE). Resíduos abertos: (a) classificador de faixa deve rotear por CLSC e tratar bordas com `≤` (fix de código); (b) PNOS achata o Quadro 2 (DT); (c) R-RX-02 fumos sem âncora no Anexo III (DT).

#### R-RX-02 — Fumos metálicos `[INTERPRETADO — prioridade na revisão de saída]`
Cargo com exposição a fumos metálicos (incluindo soldador) → RX **60 meses** em adm/per/MR/dem.
**Ressalva normativa (002.N):** o 60M NÃO tem âncora no Anexo III da NR-07 — fumos metálicos não são poeira mineral (Quadro 1) nem PNOS (Quadro 2). O valor provém da matriz Patrícia ou de analogia, não de norma vigente conferida. Além disso, DT-002K-02 (resolvida) firmou que o risco é por exposição real ao metal individual (Mn, Cr⁶⁺...), não pela categoria genérica "fumos metálicos". O roteamento correto de RX por fumos depende da decomposição em metais individuais — ver DT-D3-02. Até lá, R-RX-02 mantém o caso âncora (soldador) funcional, mas o 60M é [INTERPRETADO], não [VALIDADO].

**Implementação (002.L0).** R-RX-02 passou a existir como regra executável em `regras.yaml` (`quando: fumos_metalicos → RX 60M`). Até a 002.L0 constava apenas como `protocolos_especiais` documental em `agentes.yaml`, sem regra correspondente — fumos metálicos não emitia RX no motor.

### 5.5 ECG

#### R-ECG-01 — Indicação `[VALIDADO]`
ECG em **adm/per/MR**, periodicidade conforme periódico da matriz, **sem restrição etária**, para:
- Operador de máquinas pesadas
- Trabalho em altura
- Espaço confinado
- Exposição à eletricidade

### 5.6 Acuidade Visual

#### R-VIS-01 — Atividades críticas `[VALIDADO]`
Acuidade visual em **adm/per/MR** para toda atividade crítica:
- Eletricista
- Trabalho em altura
- Motorista
- Espaço confinado
- Soldador

**Exceção do soldador:** soldador é o **único caso** que tem acuidade visual também **no demissional**.

#### R-VIS-02 — Porteiro `[VALIDADO]`
Porteiro também recebe acuidade visual em **adm/per/MR**, **sem demissional**.

### 5.7 Avaliação Psicossocial

#### R-PSY-01 — Indicações `[VALIDADO]`
- **Espaço confinado** → sempre
- **Trabalho em altura** → somente se houver **atividade crítica concomitante** (ex: operação de máquina pesada) **E** o PGR reconheça risco psicossocial
- **Risco psicossocial classificado como moderado** (ou superior) no PGR → sempre, independente da atividade

### 5.8 Vibração

#### R-VIB-01 — RX de coluna lombo-sacra `[VALIDADO]`
Exposição confirmada a **vibração de corpo inteiro** → RX coluna **lombo-sacra** em **adm + MR**.
**Justificativa clínica:** vibração agrava patologia preexistente de coluna.
**Observação:** essa é a única conduta da Dra. Carolini que ela mesma considerou "fora do que as normas explicitamente exigem".

#### R-VIB-02 — Vibração ativa audiometria `[VALIDADO]`
Qualquer vibração (corpo inteiro ou mãos-braços) → **audiometria 12M**, mesmo com ruído abaixo do nível de ação. Ver R-AUD-01.

### 5.9 Biomonitoramento Químico

#### R-BIO-01 — Periodicidade fixa `[VALIDADO]`
Todo exame de biomonitoramento de agente químico = **6 meses**. Sem exceção.

#### R-BIO-02 — Matriz temporal por Anexo NR-07 `[DEPRECATED — sucedida por R-BIO-04 em 003.AA; ver DT-FDS-01]`

> **Redação original preservada para rastreabilidade (não remover — auditoria histórica do PCMSO):**
> - Anexo I (carcinógenos sem LT seguro) → biomonitoramento apenas no periódico
> - Anexo II (com LT) → biomonitoramento em adm + per + RT + MR + dem

**Motivo da depreciação.** O critério "Anexo I/II = carcinógeno-sem-LT / com-LT" contradiz o Anexo I vigente (567/2022): o eixo é Quadro 1 (IBE/EE) vs Quadro 2 (IBE/SC) e "Anexo II" da NR-07 é ruído. A reclassificação muda a saída temporal de agentes de alta frequência (solventes) → exigiu nova ID. Sucessora: R-BIO-04.

#### R-BIO-03 — Manganês `[VALIDADO]`
Qualquer exposição confirmada a Mn → **manganês sanguíneo semestral em adm + per + MR**. Base: NR-15, independente do LT.

#### R-BIO-04 — Matriz temporal por Quadro do Anexo I (NR-07) `[DERIVADO — NR-07 Anexo I + itens 7.5.13/7.5.15/7.5.19.4/7.5.19.5, Portaria MTP 567/2022, texto oficial MTE]`

Sucede R-BIO-02. O eixo do biomonitoramento químico é o **Quadro do Anexo I onde o indicador da substância está listado** (natureza do indicador: IBE/EE vs IBE/SC) — NÃO carcinogenicidade nem presença de LT.

- **Quadro 1 — IBE/EE** (exposição excessiva; sem caráter diagnóstico, afere absorção e sinaliza exposição acima do LEO): biomonitoramento **6M, obrigatório apenas no periódico**. `[DERIVADO — literal 7.5.15]` Alteração → médico informa o PGR para reavaliação dos riscos (7.5.19.4); não é conduta clínica individual.
- **Quadro 2 — IBE/SC** (significado clínico; evidencia disfunção orgânica): biomonitoramento **6M em adm + per + RT + MR + dem**. `[DERIVADO — 7.5.15 a contrario: o item exime só o Quadro 1; o Quadro 2 segue a obrigação geral de 7.5.6/7.5.12. Inferência expressio-unius, não frase literal afirmativa — inspecionar na revisão de saída]` Alteração → CAT/afastamento/Previdência/reavaliação PGR (7.5.19.5).

Ambos a 6M ±45d (7.5.13). "Obrigatório apenas no periódico" não impede o médico de solicitar exame extra em outro momento (7.5.18).

**Roteamento substância→Quadro** (leitura direta da tabela do Anexo I, não da carcinogenicidade):
- **Quadro 2 (IBE/SC), 4 entradas:** cádmio e compostos inorgânicos; chumbo e compostos inorgânicos (Pb-S + ALA-U); inseticidas inibidores da colinesterase; flúor, ácido fluorídrico e fluoretos inorgânicos.
- **Quadro 1 (IBE/EE):** todo o restante da tabela — solventes (tolueno, xilenos, MEK, acetona, n-hexano, estireno…), Cr⁶⁺, CO, benzeno (via SPMA/TTMA), etc.

**Carcinógenos têm regime próprio no Anexo V** (gatilho: exposição >10% do LEO ou sem avaliação ambiental; prontuário 40 anos; benzeno remetido a IN SSST 02/1995 + Portaria de Consolidação 5/MS). A carcinogenicidade **não** desloca a substância para "só periódico" — o momento é decidido pelo Quadro do indicador.

**Caso-âncora da mudança de saída (motiva nova ID, não R-BIO-02 corrigido):** o **tolueno** e os solventes comuns (xileno, MEK, acetona — os agentes mais frequentes nas matrizes reais) têm LT, não são carcinógenos, e o indicador é IBE/EE (Quadro 1) → **só periódico**. O critério de R-BIO-02 ("com LT → cinco momentos") os emitia em adm+per+RT+MR+dem → **superdimensionamento**. Como muda a matriz temporal de agentes de alta frequência → nova ID. (Cádmio NÃO serve de contra-exemplo: carcinógeno E com LT ao mesmo tempo, ambíguo nos dois baldes do critério antigo.)

R-BIO-01 (6M) e R-BIO-03 (manganês, fora do Anexo I, via NR-15) inalterados quanto a conteúdo.

> **Changelog 003.AD (mesma ID — mapa biomarcador + confirmação da lista contra texto oficial).** Quadro 1 (41 substâncias) e Quadro 2 (4) conferidos inteiros no texto oficial (Portaria 567/2022, gov.br/MTE). Quadro 2 confirmado: cádmio e comp. inorg. (cádmio urina); chumbo e comp. inorg. (Pb-S **e** ALA-U — dois indicadores simultâneos); inseticidas inibidores da colinesterase (acetilcolinesterase eritrocitária *ou* butilcolinesterase plasma/soro); flúor/HF/fluoretos inorg. (fluoreto urinário). Cardinalidade não-uniforme (1:1 / N-alternativos / 2-simultâneos) é o que mantém a forma do emissor adiada (D-ARQ-38 cl.3). Dos 4 agentes SC do Quadro 2, o vocabulário modela só chumbo; dos 41 EE do Quadro 1, modela 12. `[DERIVADO — NR-07 Anexo I Quadros 1/2, Portaria 567/2022, texto oficial MTE]`

Mapa agente→biomarcador dos agentes do vocabulário (insumo para o emissor de biomonitoramento, fatia d de D-ARQ-38 — mecanismo ainda data-bloqueado):

| agente (slug) | Quadro | biomarcador (Anexo I) |
|---|---|---|
| acetona | 1/EE | acetona urina |
| arsenio | 1/EE | As inorg. + metabólitos metilados urina (exceto arsina/arsenato de gálio) |
| benzeno | 1/EE | S-PMA *ou* TTMA urina |
| dissulfeto_de_carbono | 1/EE | TTCA urina ("Sulfeto de carbono" no Anexo) |
| estireno | 1/EE | ác. mandélico+fenilglioxílico *ou* estireno urina |
| mercurio | 1/EE | mercúrio urina ("Mercúrio metálico"; orgânico fora) |
| metil_etil_cetona | 1/EE | MEK urina |
| monoxido_de_carbono | 1/EE | COHb *ou* CO ar exalado |
| n_hexano | 1/EE | 2,5-hexanodiona urina |
| tolueno | 1/EE | tolueno sangue/urina *ou* o-cresol urina |
| tricloroetileno | 1/EE | ác. tricloroacético *ou* tricloroetanol |
| xileno | 1/EE | ác. metilhipúrico urina |
| chumbo (inorgânico) | 2/SC | Pb-S **e** ALA-U |

---

## 6. PACOTES POR CARGO / ATIVIDADE

Pacotes são conjuntos pré-formalizados de exames que disparam em bloco quando o predicado se torna verdadeiro.

### R-PKG-ATIVCRIT — Pacote Atividade Crítica `[VALIDADO]`
**Predicado:** trabalhador exposto a **trabalho em altura, espaço confinado ou operação de máquina pesada** (qualquer um dos três).

**Exames (12M em adm/per/MR):**
- Hemograma
- Glicemia
- Audiometria
- Acuidade visual
- ECG

**Observação arquitetural:** hemograma e glicemia entram aqui como **rastreio de comorbidade** (não como biomonitoramento). A lógica é: comorbidade não detectada contraindica atividade crítica.

### R-PKG-SOLD — Pacote Soldador `[VALIDADO]`
**Predicado:** cargo "soldador" presente, ou exposição a fumos metálicos declarada.

**Exames:**
- RX tórax 60M (adm/per/MR/dem)
- Espirometria 24M (adm/per/MR/dem)
- Carboxihemoglobina semestral (per)
- Manganês sanguíneo semestral (adm/per/MR) — assumindo Mn no eletrodo (ver R-FDS-05)
- Acuidade visual adm/per/MR/dem (caso único com demissional — ver R-VIS-01)
- **TODO operacional:** solicitar FDS do eletrodo para confirmar/adicionar metais (R-OP-01)

### R-PKG-BZ — Pacote Benzeno `[VALIDADO]`
**Predicado:** benzeno identificado na composição (via FDS, mesmo em concentração < 5%, mesmo via CAS de hidrocarbonetos aromáticos genéricos).

**Exames:**
- Hemograma semestral (adm/per/MR/dem)
- Reticulócitos (adm/per/MR/dem)
- Ácido trans-trans-mucônico semestral (per)

### R-PKG-ARMADOR — Pacote Armador com Policorte `[VALIDADO]`
**Predicado:** armador (construção civil) com exposição a policorte.

**Exames:**
- RX tórax 60M (adm/per/MR/dem)
- Espirometria 24M (adm/per/MR/dem)
- Carboxihemoglobina semestral (per)

### R-PKG-PORT — Pacote Porteiro `[VALIDADO]`
**Predicado:** cargo "porteiro".

**Exames:**
- Acuidade visual adm/per/MR (ver R-VIS-02)

---

## 7. MATRIZ TEMPORAL E REAPROVEITAMENTO

### R-TEMP-01 — Momentos do exame médico ocupacional `[VALIDADO]`
- **Admissional** (adm)
- **Periódico** (per)
- **Mudança de Risco Ocupacional** (MRO ou MR) — *substitui "mudança de função"*
- **Retorno ao Trabalho** (RT)
- **Demissional** (dem)

### R-MRO-01 — Mudança de Risco Ocupacional `[VALIDADO]`
"Mudança de função" **não existe mais** como categoria. O conceito atual é **Mudança de Risco Ocupacional (MRO)**. Na MRO, aplica-se a matriz do **novo cargo**.

### R-REAPR-01 — Reaproveitamento de químicos `[VALIDADO]`
Exames de biomonitoramento químico têm **validade de 6 meses**. Repete-se apenas se o último exame foi realizado há ≥ 6 meses.

### R-REAPR-02 — Audiometria no demissional `[VALIDADO]`
Audiometria com mais de **120 dias** → refazer no demissional. Ver R-AUD-03.

---

## 8. REGIMES REGULATÓRIOS ESPECIALIZADOS

### R-REG-ANAC — Aviadores `[VALIDADO]`
Tripulação aeronáutica → aplicar **normativa ANAC**, que demanda exames adicionais à NR-07. A NR-07 não é o regime aplicável principal.

**Confirmação v2:** a Dra. Carolini confirmou que **ANAC é o único regime regulatório setorial** que ela aplica sobrescrevendo a NR-07. Categorias como ferroviário, marítimo, eletricistas de alta tensão, profissionais de saúde e mineração seguem **NR-07 padrão** no protocolo dela.

**Decisão arquitetural relacionada:** D-ARQ-04 (ver `DECISOES_ARQUITETURAIS.md`).

---

## 9. LEMBRETES OPERACIONAIS (TODOs da matriz)

### R-OP-01 — FDS do eletrodo `[VALIDADO]`
Em toda matriz com soldador, registrar item operacional:
> *"Verificar metais liberados pelo eletrodo usado pela empresa — solicitar FDS específica."*

Esse item **não é exame** — é um TODO para quem executa o PCMSO confirmar metais antes de fechar a matriz.

**Decisão arquitetural relacionada:** D-ARQ-05.

---

## 10. METODOLOGIA — COMO ENSINAR A UMA MÉDICA NOVA

Síntese narrativa fornecida pela Dra. Carolini em resposta a 10.1:

1. Verificar **validade** do PGR (< 2 anos)
2. Verificar **assinatura** por engenheiro de segurança do trabalho
3. Ler o **inventário** — riscos, agravos e EPIs indicados
4. **Padronizar** conforme NR-07 e NR-15 (para Mn)
5. Para químicos: Anexo I → periódico semestral; Anexo II → semestral em adm/per/MR/RT/dem
6. Para atividades críticas (altura, espaço confinado, máq. pesada): aplicar R-PKG-ATIVCRIT
7. Para soldador: aplicar R-PKG-SOLD
8. Para porteiro: aplicar R-PKG-PORT
9. Para exposição a poeiras: aplicar R-RX-01
10. Exames clínicos sempre anuais como base (ver R-CLI-01)
11. Exceções regulatórias (ex: aviadores → ANAC) sobrescrevem a NR-07

---

## 11. PENDÊNCIAS CLÍNICAS EM ABERTO

Itens identificados durante a implementação do motor que precisam de validação clínica em sessões CONHECIMENTO futuras com a Dra. Carolini.

### DT-D3-02 — Granularidade de `fumos_metalicos` `[A VALIDAR]`

**Origem:** Sessão 002.D3 (19/05/2026), durante a implementação do Stage 2.

**Situação atual no vocabulário:** `agentes.yaml` contém `fumos_metalicos` como **agente único**, categoria genérica para soldador (R-GHE-02, R-PKG-SOLD, R-OP-01, R-RX-02). Metadados aproximados: `anexo_nr07: null`, `is_carcinogeno_iarc: false`, `tem_lt: true`.

**Lacuna clínica.** Fumos metálicos é, na prática, uma mistura de metais individuais (Mn, Cr hexavalente, Pb, Ni, Cd, etc.), cada um com:
- Anexo NR-07 próprio (Mn em Anexo II, Cr⁶⁺ Anexo I por carcinogenicidade IARC)
- CAS específico
- Biomonitoramento específico (ácido transmuconico para benzeno é precedente análogo)
- Toxicologia distinta

Manter `fumos_metalicos` como categoria única faz o motor emitir matriz correta para o caso âncora (soldador padrão), mas perde resolução para:
- Eletrodos que liberam metais específicos (R-OP-01 já pede FDS do eletrodo)
- Soldagem em aço inox (Cr⁶⁺ → carcinogênico, conduta especial)
- Soldagem com alumínio, manganês de alta concentração

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura):**
1. Em que momento da análise você decompõe "fumos metálicos" em metais individuais?
2. Quais metais individuais merecem entrada própria em `agentes.yaml` desde já?
3. R-OP-01 ("verificar FDS do eletrodo") deveria virar gatilho automático para granularização, ou continua como TODO operacional?

**Status:** REABERTA SOB NOVA METODOLOGIA (002.M). Era `[A VALIDAR — Carolini]`; fonte
indisponível. Resolução por D-ARQ-22: decompor `fumos_metalicos` em metais individuais
(Mn, Cr⁶⁺, Ni, Pb) conforme Anexos I/II da NR-07 e LTs do Anexo 11/13 da NR-15 vigentes —
conferir texto literal no site oficial do MTE antes de formalizar (`[DERIVADO]`). Não bloqueia
(categoria única mantém o caso âncora funcional).

### DT-002I-01 — Limiar de genericidade de R-PGR-05 `[A VALIDAR]`

**Origem:** Sessão 002.I (19→23/05/2026), durante o desenho de Stage 3.

**Situação.** R-PGR-04 (composição química ausente) tem consequência estrutural explícita — "a matriz não pode ser fechada" → Stage 3 bloqueante (D-ARQ-17). R-PGR-05 (PGR mal escrito: riscos genéricos, sem quantificação, sem agentes especificados) não tem: o protocolo manda "solicitar FDS / conversar com o elaborador" e diz **não rejeitar**, mas não define se a matriz **bloqueia** (PRELIMINAR até correção) ou apenas acompanha TODO operacional. Parte do conteúdo de R-PGR-05 já tem mecanismo: "sem quantificação" → predicado `Ausente` (D-ARQ-13); "sem agente especificado" → `vocabulario_ausente` (D-ARQ-14). O resíduo é o **limiar de vagueza global do inventário** — decisão clínica, não arquitetural.

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura):** a partir de que ponto a generalidade do inventário te faz parar e exigir reescrita do PGR, vs. seguir montando a matriz com ressalva operacional? Buscar o **método** (o limiar), não o resultado por empresa.

**Status:** REABERTA SOB NOVA METODOLOGIA (002.M). Era `[A VALIDAR — Carolini]`. Sem norma
objetiva que fixe o limiar de vagueza — candidata a `[INTERPRETADO — prioridade na revisão
de saída]` quando decidida. Não bloqueia (R-PGR-04 / Stage 3 cobrem o caso âncora).

---

### DT-002K-01 — Gatilho de RX de tórax OIT em 24 meses `[A VALIDAR]`

**Origem:** Sessão 002.K (24/05/2026), auditoria da RQ.61 Viverde contra o protocolo.

**Situação.** A RQ.61 (validada pela Dra. Carolini) prescreve **RX OIT com periodicidade de 24 meses** de forma sistemática — carpinteiro, pintor, serralheiro, gesseiro, entre outros. R-RX-01 conhece apenas **12M** (sílica/poeira não caracterizada/qualitativa) e **60M** (PNOS, sílica < 10% LT); R-RX-02 conhece **60M** (fumos metálicos). **Nenhuma regra do protocolo gera RX 24M.** O valor 24M não existe no vocabulário de periodicidade de RX da Carolini conforme formalizado.

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO):** o que dispara RX de tórax em 24 meses, em distinção a 12M e 60M? É um nível de exposição intermediário? Um tipo de poeira específico? Buscar o **método** (o gatilho), não o caso Viverde.

**Status:** RESOLVIDA (002.L-estudo, 25/05/2026). Resolvida por R-RX-01 refinada (Anexo III NR-07): existe RX 24M legítimo para **sílica/asbesto sem avaliação quantitativa** (adm + 24M até 15 anos) — banda ausente em R-RX-01 v2 e na matriz Patrícia. Não é nível "intermediário" genérico nem poeira específica: é o estado "sem medição quantitativa".

**Veredito sobre a RQ.61 Viverde** (a confirmar contra o inventário de cada GHE na auditoria da 002.M):
- RX 24M para PNOS (madeira/gesso) → **erro** (correto 60M).
- RX 24M para sílica/asbesto sem medição → **correto**.
- RX 24M no pintor (agente = tinta) → **confusão de exames**: tinta pede espirometria 24M (R-ESP-01), não RX.

### DT-002K-02 — Serralheiro e o pacote de fumos metálicos `[A VALIDAR]`

**Origem:** Sessão 002.K (24/05/2026), auditoria da RQ.61 Viverde.

**Situação.** A RQ.61 prescreve ao **serralheiro** (GHE 10): RX OIT, Carboxihemoglobina (6m, P), **Manganês sanguíneo (6m, ADM/PER/MRO)**, Exame Clínico semestral — quase o conteúdo de R-PKG-SOLD (pacote soldador). R-GHE-02 e R-PKG-SOLD nomeiam o gatilho como "soldador presente, ou exposição a fumos metálicos declarada"; **serralheiro não é nomeado**. A RQ.61 trata serralheiro como exposto a fumos metálicos (a nota do GHE cita "Risco Cromo abaixo de 10% LT da ACGIH").

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO):** serralheiro dispara o pacote de fumos metálicos por qual via — o cargo em si (risco implícito, como soldador em R-GHE-02), ou o agente químico (cromo/Mn) declarado no PCMSO daquela obra? Se for o agente, qual o predicado universal? Buscar o método.

**Status:** RESOLVIDA (002.L-estudo, 25/05/2026). Resposta da Dra. Carolini (R1): **risco é por exposição real, não por denominação de cargo** — NR-01/NR-07 não reconhece "risco implícito por denominação". O princípio "não existe solda sem fumos" (R-GHE-02) só vale quando soldar é a atividade-fim (soldador industrial). Serralheiro de obra: solda é **contingente** → exige confirmação documental. Formalizado em R-GHE-05; R-GHE-02 refinada com o critério indissociável vs. contingente.

**Confirmação no caso Viverde:** o pacote disparou pelo **agente declarado** (nota do GHE 10: "Risco Cromo abaixo de 10% LT da ACGIH"), não pela denominação "serralheiro" — a via-agente operando. A hipótese inicial do Arquiteto (serralheiro como cargo-de-solda) foi **revertida** pela médica.

### DT-002L-01 — Conversão de concentração medida (mg/m³) em faixa de %LEO para RX

**Origem:** Sessão 002.L (25/05/2026), estruturação do PGR Viverde.

**Situação.** R-RX-01 (Anexo III NR-07) roteia a periodicidade do RX de tórax por
faixa de exposição vs. LEO (≤10%, 10–50%, 50–100%, >100%). Mas os PGRs declaram a
exposição à sílica como **concentração absoluta medida** (ex.: PGR Viverde — sílica
0,0050 a 0,0071 mg/m³), não como percentual do LEO. O motor espera `pct_LT`; o PGR
fornece mg/m³. Falta a regra de conversão.

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO):** como se converte a
concentração medida (mg/m³) na faixa de %LEO que decide a periodicidade do RX? Qual
o limite de exposição de referência e a fonte (NR-15 Anexo 12? ACGIH TLV? depende do
%quartzo da amostra)? Buscar o método (a fórmula/critério), não o valor do caso Viverde.

**Impacto até resolver:** sílica medida em mg/m³ entra no fixture com `pct_LT=None` →
o motor a trata como quantificação incompleta (pendência), não emite RX por faixa. Os
valores do Viverde são baixíssimos (provável ≤10% LEO = só admissional), mas o motor
não crava isso sem a regra de conversão validada.

**Status:** [DERIVADO — fonte] (método) + [INTERPRETADO — prioridade na revisão de saída]
(leitura do arranjo). Resolvida na 002.N. A NR-7 Anexo III não fixa o LEO; roteia por CLSC/LEO,
onde CLSC = limite superior do IC 95% da média lognormal (definição literal do Quadro 1 do
Anexo III — NÃO é percentil 95). O valor do LEO vem do arranjo NR-9 + anexo setorial, por
agente e cenário:
- sílica fora de mineração: LEO = LT do Anexo 12 da NR-15 (transitório NR-9, item 9.6.1) —
  fração respirável 8/(%quartzo+2), total 24/(%quartzo+3). [DERIVADO — NR-15 Anexo 12
  (Portaria SSST 1/1991); NR-9 item 9.6.1, conferidas no site do MTE]
- sílica em mineração: LEO = 0,05 mg/m³ na poeira respirável (NR-22 Anexo V, Portaria MTE
  261/2026), que sobrepõe a fórmula do Anexo 12 nesse setor. [DERIVADO — gov.br, Portaria
  MTE 261/2026]
%quartzo é entrada obrigatória fora de mineração (denominador da fórmula). A leitura "a NR-7
não fixa o LEO" é [INTERPRETADO]: não há norma conclusiva nem crivo clínico sobre o ponto —
inspecionar na revisão de saída. Pendência derivada (sessão futura): contrato de LEO-resolver
no motor e classificador de R-RX-01 roteando por CLSC.

**Status: RESOLVIDA.** Derivação normativa fechada na 002.N (método: CLSC vs. LEO do Anexo 12 NR-15 / NR-22 setorial). Materializada em código na B.2 (002.W, commit `87c650c`): `resolve_leo` + plug em `_helper_silica_asbesto` calculam `pct_LT` a partir de `valor` + `pct_quartzo` + `fracao`. A pergunta de método que era endereçada à Carolini foi respondida por derivação própria (D-ARQ-27); a validação da conversão segue para o aceite final das matrizes, não bloqueia o motor.

### DT-002N-01 — PNOS achata as 4 faixas do Quadro 2 do Anexo III `[DERIVADO — fonte]`

**Origem:** Sessão 002.N (28/05/2026), conferência do Anexo III contra o texto literal (MTE).

**Situação.** `R-RX-01-pnos` em regras.yaml emite RX OIT 60M constante para o predicado `pnos`. Mas o Quadro 2 do Anexo III (PNOS — partículas insolúveis ou pouco solúveis de baixa toxicidade) tem QUATRO comportamentos por faixa de CLSC/LEO, não um:
- CLSC ≤ 10% LEO → admissional apenas
- 10% < CLSC ≤ 100% LEO → adm + após 5 anos + repetir a critério clínico
- CLSC > 100% LEO → adm + a cada 5 anos (60M)
- sem avaliação quantitativa → adm + a cada 5 anos (60M)
A regra única de 60M só está correta para as duas últimas faixas. Subdimensiona ≤10% (que é só admissional) e a faixa intermediária.

**Resolução `[DERIVADO — fonte]`:** explodir `R-RX-01-pnos` em família por faixa do Quadro 2, espelhando o padrão D-ARQ-20 já usado no Quadro 1. Predicados de faixa para PNOS (`pnos_leo_ate_10`, `pnos_leo_10_100`, `pnos_leo_acima_100`, `pnos_sem_medicao`). Fonte: NR-07 Anexo III Quadro 2 (Portaria MTP 567/2022), conferido no site do MTE. A faixa intermediária ("após 5 anos + repetir a critério clínico") tem componente clínico não-periódico — modelar como lembrete operacional (D-ARQ-05), não periodicidade fixa.

**Impacto:** baixo no caso âncora (Viverde tem PNOS de madeira/gesso, provável faixa baixa). Não bloqueia. Implementação na sessão de código que tratar o classificador de faixa (mesma que R-RX-01 CLSC).

**Status: RESOLVIDA (002.X).** Quadro 2 conferido contra o texto literal (Portaria 567/2022, MTE): as 4 faixas batem. Refinamentos: (i) faixa intermediária 10–100% é evento único aos 5 anos + critério clínico, NÃO 60M recorrente; (ii) LEO do PNOS = TLV-PNOS ACGIH 3 mg/m³ respirável (nível 4 do resolver) — a DT original explodia as faixas sem definir o denominador; sem o LEO o classificador não roda. Família R-RX-01-pnos-* especificada em R-RX-01. Implementação (predicados de faixa + LEO ACGIH + testes) é sessão de código futura.

---

### DT-002N-02 — Notação de status DERIVADO: convenção v9 diverge do D-ARQ-22 Parte A

**Origem:** Sessão 002.N (29/05/2026), revisão de método (META) ao final da sessão.

**Situação.** Há divergência entre dois documentos vivos sobre a notação do status DERIVADO:
- **D-ARQ-22 Parte A** define TRÊS sabores tipados: `[DERIVADO — NR-x item y]` (norma), `[DERIVADO — RQ.61/Patrícia]` (precedente), `[DERIVADO — analogia R-XXX]` (analogia).
- **Convenção de status v9** (§ convenções do protocolo) define UM só: `[DERIVADO — fonte]`, com a fonte livre no corpo.

A distinção não é cosmética: a própria seção **Consequência** do D-ARQ-22 usa os sabores para priorizar a revisão de saída — "olha primeiro os `[INTERPRETADO]`, depois os `[DERIVADO]` **por analogia**, por último os `[VALIDADO]`". Se a revisão prioriza DERIVADO-analogia diferente de DERIVADO-norma, achatar tudo em `[DERIVADO — fonte]` **perde informação que o modelo de qualidade usa**. Leitura do Arquiteto: a v9 enfraqueceu o D-ARQ-22 sem intenção (divergência), não o consolidou deliberadamente — mas a decisão final é do Diovanni.

**Impacto.** A sessão 002.N inteira operou na notação v9 (`[DERIVADO — fonte]`, e em alguns pontos `[DERIVADO]` solto ou `[DERIVADO — 002.N]` com a sessão no lugar da fonte; `[INTERPRETADO]` por vezes sem o sufixo "— prioridade na revisão de saída"). A fonte real está nomeada nos corpos das regras/DTs, então NÃO há erro silencioso — é não-conformidade de marca, não erro de conteúdo. Atinge: convenção v9, base_normativa das 5 R-RX-01, status de R-RX-01-pnos/R-RX-02, DT-002L-01, comentário de predicados.py e header de test_rx_periodicidade.py.

**Resolução (sessão META ou abertura da 002.O — NÃO reabrir a 002.N):**
1. Decidir entre (a) manter os três sabores tipados do D-ARQ-22 e corrigir a convenção v9 para refleti-los; ou (b) consolidar deliberadamente em um `[DERIVADO]` único e adicionar nota no D-ARQ-22 Parte A registrando a consolidação (com justificativa de que a priorização da revisão não depende do sabor).
2. Se (a): varrer os `[DERIVADO — fonte]`/`[DERIVADO]` da 002.N para a forma tipada (`[DERIVADO — NR-7 Anexo III ...]` etc.) e completar os `[INTERPRETADO]` truncados com o sufixo canônico.
3. Reconciliar D-ARQ-22 ↔ convenção v9 como fonte única de verdade da notação (hierarquia: D-ARQ é decisão-mãe; convenção do protocolo deve refleti-la, não simplificá-la em silêncio).

**Não bloqueia** o merge da 002.N (conteúdo correto, fonte rastreável nos corpos). É dívida de conformidade de método, prioridade média.

**Status: RESOLVIDA na 002.O.** Caminho (a) adotado: mantidos os três sabores tipados do D-ARQ-22 Parte A; convenção v9 corrigida para refleti-los (fonte no marcador, alinhada à decisão-mãe). Convenção do protocolo passa a refletir o D-ARQ-22, não simplificá-lo.

### DT-002V-01 — `Quantificacao.valor` não discrimina qual estatística carrega `[A VALIDAR]`

**Origem:** Sessão 002.V (01/06/2026), CONHECIMENTO/ARQUITETURA.

**Lacuna.** R-RX-01 roteia a faixa de RX OIT pelo CLSC (limite superior do IC 95% da média aritmética lognormal — "NÃO é percentil 95"). Mas `Quantificacao.valor` é um `float` anônimo: o tipo não garante que o número ali é o CLSC, e não média simples, pico, ou percentil 95. Enquanto `valor` vinha de fixture escrita à mão (sempre CLSC por construção), a garantia era humana. Com a extração de PGRs reais (D-ARQ-25) preenchendo `valor`, a garantia desaparece: um laudo que reporte outra estatística no campo faz o motor rotear faixa sobre o número errado e emitir periodicidade de exame errada **sem sinal** — erro clínico silencioso (a classe que D-ARQ-22 combate).

**Por que abre agora.** A B.2 (plug do LEO-resolver no pipeline) é a primeira vez que o motor roteia faixa de RX por `valor` real, não de fixture. O consumidor que torna a premissa perigosa nasce aqui.

**Premissa de fundo (a confirmar com a Dra. Carolini).** O motor **consome** o CLSC pronto do laudo, não o calcula — a médica do trabalho lê o CLSC da avaliação ambiental (NR-09), não refaz a estatística. Se isso vale sempre, a cardinalidade `valor: float` único basta e a amostra de medições nunca entra no motor. Confiança alta pela separação estrutural NR-07-consome / NR-09-produz, mas é premissa, não fato verificado.

**Pergunta de método para a Carolini** (método, não resultado): *quando um laudo traz uma estatística que não é o CLSC do Quadro 1 — média simples, pico, percentil 95 — qual é a conduta?* Recusar e pedir CLSC? Tratar como sem-avaliação-quantitativa (R-RX-01-sem, 24M)? Converter? A resposta define se o gap fecha por sinalização na extração (D-ARQ-25 Parte B → Pendencia), por campo discriminador com regra consumidora, ou por fallback clínico.

**Não bloqueia a B.2.** O plug roteia sob a premissa "valor é CLSC quando há avaliação quantitativa"; esta DT registra a premissa como dívida, não como impedimento. Continuação operacional de DT-002L-01 (método de conversão mg/m³ → faixa, resolvido na 002.N) e D-ARQ-24 (LEO-resolver). Independe da decisão de modelo da B.2 (`Quantificacao.fracao`).

---

### DT-002X-01 — LEO do carvão mineral (3º agente do Quadro 1) `[INCERTO — LEO do carvão a confirmar em fonte vigente]`
**Origem:** 002.X, conferência do Anexo III vigente.
**Situação.** Carvão mineral foi incluído no Quadro 1 (567/2022) mas não está no Anexo 12 da NR-15 (que tem só asbesto, Mn, sílica). LEO a resolver: candidato a nível (4) ACGIH (coal dust tem TLV próprio, variável por tipo e teor de sílica) ou nível (1) se houver anexo setorial de mineração de carvão. Valor NÃO cravado — exige busca dedicada no texto vigente.
**Impacto:** baixo no caso âncora (Viverde não tem carvão). Não bloqueia. Resolver antes de adicionar `carvao_mineral` à família de roteamento do Quadro 1.

### DT-002X-02 — Vigilância pós-ocupacional do asbesto (30 anos) `[DERIVADO — fonte]`
**Origem:** 002.X, leitura literal do Anexo III item 2.17.
**Situação.** Após término de contrato com exposição a asbesto, o empregador disponibiliza exames de controle por ≥30 anos, periodicidade por tempo de exposição acumulado: a cada 3 anos (≤12a), a cada 2 anos (>12 a 20a), anual (>20a); espirometria pós-demissional segue a mesma periodicidade do RX (item 3.5). Casa com a guarda de 30 anos da avaliação ambiental (NR-15 Anexo 12 item 11.1). `[DERIVADO — NR-7 Anexo III 2.17/2.17.1/3.5; NR-15 Anexo 12 11.1 (Portaria 567/2022; SSST 1/1991)]`.
**Lacuna estrutural.** É uma 4ª dimensão temporal (pós-vínculo, fora de adm/per/MR/RT/dem) e tempo-acumulado-dependente — não tem casa no motor nem no agendador atual. Proposta: motor emite lembrete operacional (D-ARQ-05) "vigilância pós-ocupacional 30 anos exigida (asbesto)" quando há exposição a asbesto; agendamento real fica para camada futura. Modelar a 4ª dimensão é decisão arquitetural própria — adiada, não fechada nesta sessão.

### DT-002X-03 — NOTA 1 do Quadro 1: leitura radiológica 0/1+ → encaminhamento `[DERIVADO — fonte]`
**Origem:** 002.X.
**Situação.** A NOTA 1 do Quadro 1 manda encaminhar a médico especializado o trabalhador com leitura radiológica OIT ≥ 0/1. É conduta condicionada ao **resultado** do exame — o motor é função pura sobre o PGR (D-ARQ-09), não lê resultado. `[DERIVADO — NR-7 Anexo III Quadro 1 NOTA 1 (Portaria 567/2022)]`. Conduta para lembrete operacional (D-ARQ-05) ou camada de laudo/agendador. Não bloqueia. Registrada para não se perder.

---

### DT-002Y-01 — Lembrete "repetir a critério clínico" da faixa PNOS 10–100% `[INTERPRETADO]`
**Origem:** 002.Y, materialização da família R-RX-01-pnos-*.
**Situação.** O Quadro 2 do Anexo III, faixa 10% < CLSC ≤ 100% LEO, prescreve admissional + RX único após 5 anos + **repetir a critério clínico**. A repetição clínica é um lembrete operacional não-periódico (D-ARQ-05), mas o motor não tem caminho regra→lembrete: `stage_5_emissao` só emite `ExameEmitido`. Em 002.Y a regra `R-RX-01-pnos-10a100` emite só o admissional; o "após 5 anos" vive em `base_normativa` (texto), e a repetição clínica não é emitida.
**Resolução.** Depende de D-ARQ-28 (proposta — caminho declarativo regra→`Pendencia` não-bloqueante). Quando implementada, a faixa ganha o lembrete e esta DT fecha. Paliativo aceito (sinalizado): admissional + gatilho de 5 anos corretos; falta só a repetição clínica. NÃO bloqueia — a reta de faixas está coberta e nenhuma subdimensiona.

### DT-002Y-02 — Validação PNOS contra Viverde real adiada para integração `[A VALIDAR — integração]`
**Origem:** 002.Y, decisão de recorte de teste.
**Situação.** D-ARQ-29 (injeção RESPIRAVEL para PNOS) foi coberta em 002.Y por testes sintéticos de conversão (`mg/m³ → faixa`, com asserção de não-bloqueio), não pela fixture Viverde completa — a fixture tem 3 sub-funções de GHEs e isolar um GHE-PNOS limpo seria andaime desproporcional numa sessão de dado. Os 11 PNOS medidos do Viverde (0,08 a 21,94 mg/m³, cruzando as faixas ate_10/10_100/acima_100) só serão exercitados em contexto completo na sessão de integração.
**Resolução.** Cobrir na 002.Z (b — PGR Viverde como teste de integração): rodar o PGR inteiro e confirmar que os GHEs com PNOS roteiam por faixa sem bloquear, em presença dos demais riscos. NÃO bloqueia — é o teste de integração que sempre seria da 002.Z, não buraco da a1.

---

### DT-002Z-01 — Orquestrador all-or-nothing por GHE: matriz parcial vs. binário `[DERIVADO — fonte]`

**Origem:** Sessão 002.Z (04/06/2026), integração Viverde — diagnóstico da zona-cinza (`diagnostico_zona_cinza()` em `test_integracao_viverde.py`).

**Situação.** D-ARQ-15 fecha um GHE com `Pendencia(bloqueante=True)` zerando `linhas` — `MatrizGHE` binária (completa ou vazia). O primeiro risco bloqueante apaga os exames que outros riscos do mesmo GHE já rotearam. Caso-âncora Acab-05: sílica sem fração bloqueia (`Ausente` em todas as faixas R-RX-01-*, D-ARQ-24/29) e o `rx_torax_oit` que o PNOS justificaria (admissional) some junto. Universal, não só sílica×PNOS. Pergunta de método: GHE com um risco pendente vai ao PCMSO como parcial, ou o risco pendente invalida o GHE inteiro?

**Status: RESOLVIDA (003.A) — por fonte documental, virou D-ARQ-31.** A NR-07 (Portaria 567/2022) não tem âncora para all-or-nothing: a postura diante de dado insuficiente é sinalizar + reconciliar + registrar (7.5.1 PCMSO derivado dos riscos do PGR; 7.5.5 reavalia inconsistências com o PGR; 7.6.4 registra insuficiência), nunca suprimir exames determinados. Reforço `[VALIDADO]`: R-PGR-04/R-PGR-05 (solicitar dado, não rejeitar). Decisão: bloqueio é por-risco/por-linha; `MatrizGHE` ganha tri-estado VÁLIDA/PARCIAL/BLOQUEADA; pendência bloqueante incidente sobre linha emitida fica anexada à linha (mata o subdimensionamento silencioso do caso convergente — D-ARQ-22). Direção `[DERIVADO — NR-07 7.5.5/7.6.4]`; modelo tri-estado + anexação `[INTERPRETADO]`. Não é regra clínica (R-*) — é contrato de motor → **D-ARQ-31**. Implementação multi-fatia, sessões de Code futuras.

### DT-FDS-01 — R-BIO-02 contradito pelo Anexo I vigente (eixo Quadro 1/Quadro 2, não "Anexo I/II")

**Origem:** Sessão 003.F (07/06/2026), frente FDS (CONHECIMENTO), conferência do Anexo I da NR-07 vigente contra o texto oficial (gov.br/MTE), durante a derivação do esquema da ficha de agente químico.

**Situação.** R-BIO-02 redige: "Anexo I (carcinógenos sem LT seguro) → biomonitoramento apenas no periódico; Anexo II (com LT) → adm + per + RT + MR + dem". Três problemas contra o texto literal vigente (Portaria 567/2022):

1. **Rótulo desatualizado.** Na NR-07 vigente, "Anexo II" é *Controle médico da exposição a níveis de pressão sonora* (ruído), não "químico com LT". O eixo do biomonitoramento químico é **Quadro 1 vs Quadro 2, ambos dentro do Anexo I**. "Anexo I/II" é nomenclatura da NR-07 pré-567/2022.
2. **Critério errado.** O que define o Quadro 1 não é "carcinógeno sem LT" — é ser *Indicador Biológico de Exposição Excessiva (IBE/EE)*: indicador sem caráter diagnóstico, que afere absorção e sinaliza exposição acima dos limites. O Quadro 2 é *Indicador Biológico de Exposição com Significado Clínico (IBE/SC)*: evidencia disfunção orgânica. Carcinógenos têm tratamento próprio no **Anexo V**, fora deste eixo.
3. **Comportamento temporal sem âncora.** O texto fixa: Quadro 1 **não obrigatório** em adm/RT/MR/dem (7.5.15) → na prática só periódico; ambos a 6M ±45d (7.5.13). Quando alterado, o Quadro 2 dispara conduta (CAT/afastamento/Previdência, 7.5.19.5) e o Quadro 1 dispara reavaliação PGR↔PCMSO (7.5.19.4). A semântica "Anexo II → cinco momentos" do R-BIO-02 não tem âncora literal e precisa ser rederivada sobre o eixo correto.

**Procedência do achado factual:** `[DERIVADO — NR-07 Anexo I (definições IBE/EE e IBE/SC) + itens 7.5.13/7.5.15/7.5.19.4/7.5.19.5, Portaria MTP 567/2022, texto oficial conferido no site do MTE]`. A leitura cobriu o corpo 7.x integral e o Quadro 1; **o Quadro 2 não foi lido por inteiro** (só fragmentos).

**Por que não corrigir agora.** (a) Reabertura muda critério/escopo de saída → exige **nova ID + R-BIO-02 DEPRECATED** (versionamento de regra clínica), decisão do Diovanni. (b) A redação da sucessora exige o **Quadro 2 completo**, não lido nesta conferência. (c) É correção do lado-médico, independente da frente FDS (lado-engenheiro); acoplar viola "uma coisa por vez".

**O que a reabertura exige (sessão CONHECIMENTO própria):**
1. Ler o **Quadro 2 inteiro** no texto oficial.
2. **Resolver a posição do benzeno (não cravada nesta sessão):** o benzeno tem indicadores listados no Anexo I (SPMA 45 µg/g creat; TTMA 750 µg/g creat), mas, sendo carcinógeno IARC 1, é preciso confirmar se está no Quadro 1, no Quadro 2, e/ou recebe tratamento no Anexo V — e como isso se concilia com R-PKG-BZ (hemograma + reticulócitos + t,t-mucônico). O hemograma do benzeno pode ter âncora diferente do Quadro 1 (rastreio hematológico).
3. Mapear os demais agentes modelados (R-BIO-03 manganês; solventes) em Quadro 1 vs Quadro 2, conferindo se algum muda de comportamento temporal sob o eixo correto.
4. Redigir a sucessora (nova ID) por eixo Quadro 1/Quadro 2, momentos derivados de 7.5.13/7.5.15; R-BIO-02 → DEPRECATED com link.

**Status:** RESOLVIDA na 003.AA (20/06/2026).

**Resolução (003.AA).** Quadro 2 lido por inteiro no texto oficial (gov.br/MTE, 567/2022). Eixo formalizado em **R-BIO-04** (nova ID); R-BIO-02 → DEPRECATED.
1. Quadro 1 (IBE/EE) → só periódico (7.5.15 literal); Quadro 2 (IBE/SC) → adm+per+RT+MR+dem (7.5.15 a contrario); 6M ±45d ambos (7.5.13).
2. Quadro 2 = cádmio inorg., chumbo inorg. (Pb-S+ALA-U), inseticidas anticolinesterásicos, flúor/fluoretos. Quadro 1 = restante.
3. Benzeno (item 2 resolvido): TTMA/SPMA são Quadro 1 → periódico; hemograma+reticulócitos do R-PKG-BZ vêm do regime benzeno (Anexo V → IN SSST 02/1995 + Portaria Consolidação 5/MS), não do Quadro 1. R-PKG-BZ válido; âncora esclarecida. Siderurgia mantém regra vigente (obs. da tabela do Quadro 1).
4. Manganês (R-BIO-03): fora do Anexo I — eixo não o toca.
5. Mudança de saída que motiva nova ID: tolueno/solventes (Quadro 1, com LT, não carcinógenos) — R-BIO-02 emitia 5 momentos, R-BIO-04 emite só periódico (superdimensionamento). Cádmio descartado como contra-exemplo (ambíguo: carcinógeno E com LT).
6. Irmãs R-CLI-02/03: relabel "Anexo I/II" → "Quadro 1/2 do Anexo I" (mesma ID + changelog). Borda Anexo-V do semestral → [INTERPRETADO — revisão de saída].

**Derivada para 003.AB (IMPLEMENTAÇÃO ou ARQUITETURA — `git grep` decide):** confirmar se R-BIO-02 tem consumidor no motor (roteador `anexo_nr07 → momentos`). Hipótese da passada de verificação 003.AA: os momentos moram nos pacotes/por-exame (solventes já saem periódico-só na matriz de referência; R-PKG-BZ já crava TTMA só no periódico), não em roteador genérico — nesse caso não há teste-que-falha e criar o roteador seria fiação fantasma.

**Apontamento-irmão (não confundir com esta DT):** R-CLI-02 e R-CLI-03 usam o mesmo vocabulário "Anexo I / Anexo II" e podem sofrer do mesmo rótulo pré-567/2022 — mas governam **clínico semestral**, não biomonitoramento, e são regra distinta. Verificar na mesma sessão de reabertura, como item separado.

---

### DT-FDS-02 — Unidade do cutoff de 5% de materialidade `[INCERTO — confirmar % m/m em ABNT NBR 14725 / conduta Carolini no PDF oficial]`

**Origem:** Sessão 003.H (09/06/2026), formalização de D-ARQ-34 (materialidade do lado-engenheiro), 2ª passada adversarial.

**Situação.** O cutoff de 5% (R-FDS-03) e a concentração extraída da FDS precisam estar na mesma unidade (% m/m vs % v/v), senão o predicado de straddle (`min ≤ 5 < max`, D-ARQ-34 Parte 2) compara grandezas diferentes e a borda 5,0 (material vs. não-material) decide sobre bases incompatíveis. ABNT NBR 14725 tipicamente usa % m/m na seção 3 da FDS, mas o texto não foi conferido nesta sessão. Não bloqueia a forma faixa (a faixa carrega o número; unidade é metadado da ficha).

**Pergunta de método:** o cutoff de 5% de R-FDS-03 é % m/m? A FDS reporta composição em que base, e há caso de divergência (v/v) que exija normalização antes do predicado? Buscar a base, não o caso.

**Impacto até resolver:** a borda 5,0→não-material de D-ARQ-34 Parte 2 fica `[INTERPRETADO]`, não `[VALIDADO]`. Candidato: campo `unidade` na faixa de concentração, ou presumir % m/m com a presunção marcada. Decidir na sessão de implementação de D-ARQ-34 ou em sessão própria.

**Status:** ABERTA. Não bloqueia. Lado-engenheiro, independente de DT-FDS-01 (lado-médico).

---

### DT-003L-01 — Mapa de formas de declaração de agente químico no PGR (input para D-ARQ-25) `[DERIVADO — medição de 15 PGRs, 003.L]`

**Origem:** Sessão 003.L (13/06/2026), caça do caso-âncora de materialidade. Varredura read-only de 15 PGRs do acervo via pdfplumber (marcador "Químico" + agente nomeado + marcador de FDS-apontada).

**Situação.** Não existe "o formato do PGR" para o lado-químico — a camada de extração (D-ARQ-25) terá de aguentar pelo menos 6 formas distintas:

1. **Agente + link FISPQ por GHE** (T65, EURO Setor C) — caminho feliz; produto nomeado + FDS apontada por URL `acrobat.adobe.com`, agente a agente. Família de hashes compartilhada entre PGRs da mesma consultoria.
2. **Carta pedindo FDS ao contratante** (CMO Floramazônia) — o PGR contém o pedido "encaminhar as FDS dos produtos utilizados"; R-PGR-04 literal em estado selvagem.
3. **Template vazio** (Ricco-Adm) — tabela "Inventário de Produtos Químicos" com tudo "conforme FISPQ e Informações Técnicas em Anexo", sem dado inline nem link.
4. **Boilerplate-only** (Cjr, TPB Andrade, Seconci REV3/REV4, Auro) — "Químico" só em texto regulatório NR-9/NR-32/EPI; FDS/FISPQ genéricos, nunca product-linked; sem agente real.
5. **Agente genérico + composto inline** (CMO, Vistamérica, Viverde) — RISCO QUÍMICO por GHE com agente genérico, mais um nome de composto solto ("Graxa ET … tridecyloxy-propyl" — ver achado lateral 003.L).
6. **Matriz por-cargo com dezenas de agentes nomeados + código e-Social, sem link** (Ricco Hetrin, Ricco Serra Dourada) — a forma mais densa; agente inline estruturado, FDS referenciada só genericamente, costura agente↔cargo na própria linha.

Links `acrobat.adobe.com` (forma 1) aparecem em apenas 2 dos 15 PGRs — Shape 1 é a exceção, não a norma.

**Procedência:** `[DERIVADO — medição direta de 15 PGRs, 003.L]`. A taxonomia em 6 grupos é organização do Arquiteto sobre a medição.

**Impacto na arquitetura.** A extração (D-ARQ-25 Parte B: normalização linguagem natural → slug; e a sub-camada de descoberta CAS de D-ARQ-33) precisa cobrir todas as 6 formas, não só a feliz. Formas 2/3 disparam R-PGR-04 (pendência, FDS a solicitar). Forma 4 é degrau-0 honesto (sem químico real). Formas 1/5/6 carregam agente nomeado em estruturas diferentes — cada uma exige estratégia de extração própria.

**Status:** ABERTA. Não bloqueia. Insumo a consultar quando a camada de extração (D-ARQ-25) for desenhada — define o que o extrator/normalizador tem de aguentar.

---

### DT-003M-01 — Ordem ramo-0-vs-bypass quando o CAS é oculto `[ABERTA — decisão de arquitetura]`

**Origem:** Sessão 003.M (13/06/2026), leitura da FDS do Adesivo PVC Tigre (PGR ALT T65).

**Situação.** O predicado de materialidade (003.J, `motor/materialidade.py`) avalia o ramo 0 (`agente is None` → AUSENTE) ANTES do ramo 1 (bypass de perigo → MATERIAL). A justificativa da 003.J: sem slug não há flags confiáveis. A FDS do Adesivo PVC traz um contra-exemplo: o componente "Segredo Industrial 2" declara H334 (sensibilização respiratória) + H317 (sensibilização dérmica) na própria FDS, mas tem CAS OCULTO (segredo industrial). Sem CAS → sem slug → `agente=None` → ramo 0 → AUSENTE, mascarando o bypass-sensibilizante que a flag justificaria.

**Por que é arquitetura, não disciplina de fixture.** O estado `sem-slug + flag-de-perigo-declarada-no-documento` é alcançável pelo PIPELINE REAL, não só pela fixture-à-mão: a FDS declara perigo por frase-H em componente de CAS oculto; a extração (D-ARQ-25 Parte B) resolve CAS→slug→flag, e o CAS oculto quebra a cadeia. A flag de perigo é dado do documento, não conhecimento injetado. A pergunta de arquitetura: quando o documento declara sensibilização mas oculta o CAS, o sistema deve (a) bloquear por falta de slug (perde o sinal de perigo declarado) ou (b) honrar a flag mesmo sem slug?

**O que a reabertura exige (sessão própria).** Decisão sobre a ordem ramo-0-vs-bypass — toca o predicado da 003.J e o gate-CAS de D-ARQ-33 cláusula 3 (CAS oculto ≠ CAS inválido — casos distintos que o gate hoje não separa). Provavelmente a mesma sessão de DT-003M-02 (expansão de vocabulário), porque "sem-slug + flag" e "popular slugs de FDS" são dois lados de cobrir composição-de-FDS.

**Status:** ABERTA. Não bloqueia. Caso-âncora vivo capturado na fixture (`fds_t65.py`, Adesivo PVC componente "Segredo Industrial 2", comentado).

---

### DT-003M-02 — Vocabulário (agentes.yaml) não cobre composição-de-FDS `[ABERTA — input para expansão]`

**Origem:** Sessão 003.M (13/06/2026), medição da fixture-FDS sobre `agentes.yaml`.

**Situação.** Dos 24 componentes de 3 FDS reais (Tinta Acrílica, Cimento Ciplan, Adesivo PVC), 23 caem em ramo 0 do predicado de materialidade (`agente=None`, slug não resolvido). Só 2 substâncias têm slug em `agentes.yaml`: `dioxido_de_titanio` (TiO₂) e `metil_etil_cetona` (MEK). `agentes.yaml` é vocabulário de inventário-de-PGR (sílica, asbesto, poeira, ruído, ototóxicos, fumos, agentes-marcador) — não de composição-de-FDS. Os ingredientes típicos de produto comercial (carbonato de cálcio, silicato de alumínio, silicato tricálcico/dicálcico, óxido de ferro, polímeros acrílicos, isotiazolonas, acetona, acetato de etila, copolímero de PVC) NÃO estão no vocabulário.

**Consequência.** A materialidade-por-concentração e a materialidade-por-bypass só são exercitáveis sobre componentes com slug. Enquanto o vocabulário não cobrir composição-de-FDS, a fixture-real rende majoritariamente AUSENTE (ramo 0) — fiel ao estado, mas sem travessia para MATERIAL/NÃO-MATERIAL na maioria. Ramo 5 (NÃO-MATERIAL fiel) não tem nenhum caso vivo nas 3 FDS (nenhum componente com slug tem faixa inteira ≤5%).

**Irmã de DT-003L-01.** DT-003L-01 mapeia as formas de declaração química no PGR (lado-inventário); DT-003M-02 mede o vazio de vocabulário no lado-composição. Ambas são input empírico para a camada de extração/normalização (D-ARQ-25) e para a expansão de `agentes.yaml`.

**O que a expansão exige (sessão de dado, não desta fatia).** Adicionar os agentes de FDS a `agentes.yaml` com `is_carcinogeno_iarc`/`is_sensibilizante` por agente, fonte marcada por agente (D-ARQ-27). É tarefa de dado com proveniência, maior que uma fixture e de natureza distinta — não empilhar com fixture.

**Andamento (003.N, parcial — NÃO fecha).** Frente (b) executada em recorte (b-mínimo): das substâncias de ramo 0, partição medida — 14 têm CAS resolvível na fixture, ~9 têm cas="" (não populáveis por slug; dependem de descoberta-CAS ou são CAS-oculto). Dos 14 com CAS, populados 2 (`acetona` 67-64-1, `acetato_de_etila` 141-78-6) — os únicos que atravessam para MATERIAL/straddle quando hidratados; os 12 inertes restantes (carbonatos, silicatos, óxidos do clínquer, ferro-aluminato) são flag-False → NÃO-MATERIAL sem efeito de conduta, adiados até a hidratação provar que distingui-los importa. Inaugurado o padrão de ficha-de-composição (003.N, commit 4945396). Reenquadramento medido: popular agentes.yaml NÃO destrava o predicado — materialidade() lê flags do Componente, não do yaml (D-ARQ-34 Parte 4); o elo é a hidratação CAS→slug→flags (D-ARQ-25 Parte B, inexistente). (b) entrega vocabulário pronto para a hidratação, não travessia. O sensibilizante-CAS-oculto (Segredo Industrial 2) é DT-003M-01, não esta DT.

**Status:** ABERTA. Não bloqueia. Restam 12 inertes-com-CAS + as substâncias cas="" + a regra que consome a flag (hidratação/fatia 4).

---

### DH-003M-01 — `\r\n` literal reincidente no HISTORICO `[ABERTA — higiene doc]`

**Origem:** Sessão 003.M (13/06/2026), leitura do HISTORICO no kickoff.

**Situação.** O bloco da Sessão 003.L em `docs/HISTORICO_OPERACIONAL.md` foi gravado com sequências de texto literal `\r\n` em vez de quebras de linha reais — mesmo defeito já observado no bloco 003.K. Consequência prática: `grep "^## Sess"` não casa o cabeçalho afetado, e o `/kickoff` (que depende de `^## Sess` para achar a última sessão) subconta sessões e pode não enxergar o bloco como última. É defeito de gravação, não de conteúdo.

**Recomendação.** Conserto pontual (re-gravar o bloco com newlines reais) resolve o caso, não a CLASSE. Duas opções estruturais: (1) quebrar o HISTORICO em arquivo-por-sessão com índice — escala e mata a classe; (2) tirar o `/kickoff` da dependência de `^## Sess` (remenda). Decisão do Diovanni. O bloco 003.M desta sessão foi gravado com newlines reais (não reincide).

**Status:** ABERTA. Doc-only, não-bloqueante. Distinta de DH-003A-01 (header "v2" + 2ª "## 11").

---

### DH-003P-01 — Imports de `Materialidade` apontam para módulo re-exportador, não a fonte canônica `[ABERTA — higiene de código]`

**Origem:** Sessão 003.P (14/06/2026), fatia 1 de D-ARQ-35.

**Situação.** O enum `Materialidade` foi movido para `tipos.py` (fonte canônica do contrato; quebra de ciclo de import com `materialidade.py`). `materialidade.py` o re-exporta ao fazer `from ...tipos import Componente, Materialidade`. Dois testes (`test_materialidade.py`, `test_materialidade_fds.py`) ainda importam `Materialidade` de `agente_medico.motor.materialidade` — funciona por re-export, mas a fonte canônica passou a ser `tipos`. Frágil a um `__all__` ou lint futuro.

**Recomendação.** Redirecionar os imports de `Materialidade` desses testes para `tipos`. Varredura única, teste-only. Não tocado nesta fatia (uma implementação por sessão; redirecionar import de teste mergeado é fora do escopo).

**Status:** ABERTA. Higiene, não-bloqueante.

---

### DT-003T-01 — `is_sensibilizante` ausente do `agentes.yaml` `[ABERTA — input para sessão de dado]`

**Origem:** Sessão 003.T (16/06/2026), gate de procedência da fatia 2 de D-ARQ-36 Parte 3.

**Situação.** Ao popular as flags de perigo no gate-CAS, o gate de procedência (D-ARQ-22) sobre `agentes.yaml` revelou: `is_carcinogeno_iarc` existe e está explícita em todos os agentes, mas `is_sensibilizante` **não existe como chave em nenhum agente** do vocabulário. A fatia 003.T populou só `is_carcinogeno_iarc` (presente, honesta); `is_sensibilizante` ficou de fora — NÃO entra no `EntradaIndice`, o gate não a toca, o `Componente` a mantém no default `False` por ausência-de-dado (não por classificação).

**Por que não popular agora.** Popular `is_sensibilizante` é dado-com-proveniência: exige decidir, por agente, quais recebem `true`, contra fonte marcada (frase-H H334/H317 da FDS, classificação GHS/ABNT 14725). É natureza distinta de mecânica (gate lê chave que já existe) — empacotar viola "uma coisa por vez". Foi considerado e descartado incluí-la no `EntradaIndice` degradando para `False` com marca-comentário: a marca viveria no código-fonte, não no dado, e um `False` tipado é indistinguível de "classificado como não-sensibilizante" — o erro silencioso plausível de D-ARQ-22.

**O que a introdução exige (sessão de dado própria).** Campo `is_sensibilizante` no `EntradaIndice` + leitura no `construir_indice_cas` + população no `agentes.yaml` com proveniência por agente. **Cruza DT-003M-01** (sensibilizante de CAS oculto / frase-H sem slug, ABERTA): a forma de como sensibilizante entra no sistema pode mudar conforme aquela decisão — logo a forma do campo deve ser decidida COM a fonte e COM DT-003M-01 resolvida, não chutada antes. Mesma razão pela qual `is_ototoxico` entrou completo na 002.H (flag + agentes + primitivo + regra na mesma leva).

**Status:** ABERTA. Não-bloqueante. Lado-engenheiro/vocabulário, não toca regra clínica.

---

### DT-003AB-01 — Campo `anexo_nr07` é eixo morto/misturado; insumo herdado pela implementação de R-BIO-04 `[ABERTA — input para sessão de R-BIO-04]`

**Origem:** Sessão 003.AB (21/06/2026), ARQUITETURA-leve de higiene de dado. Investigação derivada do apontamento de 003.AA ("`git grep` de consumidor de R-BIO-02/`anexo_nr07` decide IMPLEMENTAÇÃO vs. ARQUITETURA").

**Achado (medido nesta sessão, não herdado de handoff).** O campo `anexo_nr07` (`agentes.yaml`, hidratado em `Risco`) está em estado terminal sob o eixo vigente (567/2022) e nenhum doc vivo registrava o estado real:

1. **Consumo de produção = zero** `[VERIFICADO — git grep '*.py' nesta sessão]`. Nenhuma regra, predicado ou estágio lê `.anexo_nr07` do `Risco` para rotear momento/exame/periodicidade. As únicas leituras são duas asserções de teste (`test_riscos_stage.py`, asserções `risco.anexo_nr07 is None`) checando o caso de vocabulário `null` (benzeno). O campo é armazenado, nunca consumido.
2. **Hidratação viva em 3 sítios** `[VERIFICADO — git grep]`: as três Fases (A/B/C) de `riscos.py` que fazem `meta.get("anexo_nr07")`. A 4ª ocorrência no mesmo arquivo é `anexo_nr07=None` literal (fallback de vocabulário-ausente), não hidratação. Não há re-hidratação em via separada — o comentário em `resolvedor.py` ("`is_ototoxico`/`anexo_nr07` re-hidratados por-slug no lado-médico") refere-se a esses 3 sítios.
3. **Eixo misturado entre duas normas** `[VERIFICADO — agentes.yaml colado nesta sessão]`. O campo nomeado `anexo_nr07` carrega: `"I"` (silica, asbesto) = NR-07 Anexo I; `"11"` (etanol, metil_etil_cetona, cloreto_de_hidrogenio) = **NR-15 Anexo 11** (LT de insalubridade), redundante com `tem_lt`. Um campo, dois eixos normativos, nome que promete um só.
4. **`"I"` em silica/asbesto é semanticamente vazio** `[INTERPRETADO]`. Poeira mineral não tem IBE no Anexo I — silica/asbesto roteiam por R-RX-01 (RX OIT por CLSC/LEO), não por biomonitoramento. O `"I"` ali não denota "Quadro 1".
5. **Comentário-benzeno stale** `[VERIFICADO]`. O comentário em `agentes.yaml` que começa `# anexo_nr07 e tem_lt = null` cita "débito DT-FDS-01 (lado-médico, sessão própria)" como aberto; DT-FDS-01 foi RESOLVIDA em 003.AA. O `null` do benzeno permanece correto (dispara por identidade de agente, R-PKG-BZ); só o comentário envelheceu.

**Por que é insumo herdado, não decisão a executar agora.** O eixo-alvo do biomonitoramento é `tipo_ibe ∈ {EE, SC}` (D-ARQ-33, contrato da mesa) — e R-BIO-04 (v25) roteia por "natureza do indicador IBE/EE vs IBE/SC", não por `anexo_nr07`. Logo a substituição `anexo_nr07 → tipo_ibe` é **consequência mecânica** de implementar R-BIO-04 (não há como rotear EE/SC sem campo EE/SC), não decisão própria da 003.AB. É **substituição, não rename**: `"11"` (NR-15) não traduz para EE/SC, obrigando re-derivar por agente (qual Quadro, ou nenhum) — trabalho clínico que pertence à sessão de R-BIO-04. Esta DT existe para que essa sessão herde a leitura semântica (estado do campo + os 5 achados acima) em vez de regrepá-la do zero; o gate de estado real de R-BIO-04 confirma *estado* (git/baseline), não *semântica*.

**O que a implementação de R-BIO-04 deve fazer (pré-condições, a confirmar por git naquela sessão):**
1. Reconfirmar consumo-zero e o número de sítios (`git grep anexo_nr07 '*.py'` no repo inteiro — tipo compartilhado, varredura total per 003.I).
2. Substituir `anexo_nr07: Optional[str]` por `tipo_ibe` (forma `{EE,SC}` vs. enum a decidir na fatia), re-derivando o valor por agente via Quadro 1/2 de R-BIO-04 — `"11"`/NR-15 sai (redundante com `tem_lt`), `"I"`/silica-asbesto vira `None` (sem IBE).
3. Blast radius medido nesta sessão: a definição em `tipos.py`, 3 hidratações em `riscos.py`, 1 comentário em `resolvedor.py`, e ~18 sítios de teste que constroem `Risco` passando `anexo_nr07=None` (contagem por grep; alguns em compreensão de lista — reconferir na migração). Todos tocados ao migrar o campo.
4. Corrigir o comentário stale (`agentes.yaml`, bloco `# anexo_nr07 e tem_lt = null`) — R-BIO-04 reescreve esse trecho ao introduzir `tipo_ibe` de qualquer forma.

**Derivação 003.AD (21/06/2026) — `tipo_ibe` derivado por slug; a fatia b transcreve, não re-deriva.** A sessão CONHECIMENTO 003.AD derivou o conteúdo de `tipo_ibe` por agente contra o texto oficial do Anexo I (critério e mapa biomarcador em D-ARQ-38 aplicação 003.AD e R-BIO-04 changelog 003.AD). Tabela que a migração da fatia b transcreve:
- **EE** (12): acetona, arsenio, benzeno, dissulfeto_de_carbono, estireno, mercurio, metil_etil_cetona, monoxido_de_carbono, n_hexano, tolueno, tricloroetileno, xileno.
- **SC** (1): chumbo `[decisão: inorgânico — ver refinamento 3]`.
- **None**: todos os demais (etanol, cloreto_de_hidrogenio, acetato_de_etila, dioxido_de_titanio, propanediamina_tridecyloxy, quimico_nao_especificado, cianeto_de_hidrogenio, manganes, silica, asbesto, poeira_nao_classificada, fumos_metalicos + físicos/ergonômicos/acidente/biológico).

Refinamentos aos passos da migração desta DT:
1. Passo 2 ("re-derivar tipo_ibe por agente") está **feito** — a fatia b transcreve a tabela acima. `"11"`/NR-15 → MEK=EE, etanol=HCl=None; `"I"`/silica-asbesto → None.
2. **benzeno=EE** corrige (a) a fixture `test_resolvedor.py:50` (taggeava SC) e (b) o comentário stale do benzeno no `agentes.yaml` (bloco `# anexo_nr07 e tem_lt = null ... débito DT-FDS-01`): DT-FDS-01 RESOLVIDA (003.AA) e tipo_ibe=EE derivado — reescrever ao introduzir tipo_ibe.
3. **chumbo=SC** é decisão a gravar explícita (Q2 inorgânico vs Q1 tetraetila); não cravar em silêncio.
4. **9 dos 12 EE têm `cas: null`** → `tipo_ibe` é dado gravado, não casado por CAS; popular os 9 CAS (arsenio, dissulfeto_de_carbono, estireno, mercurio, monoxido_de_carbono, n_hexano, tolueno, tricloroetileno, xileno) é tarefa de dado paralela à fatia b, não pré-requisito dela.
5. **Cobertura SC parcial**: dos 4 SC do Quadro 2, só chumbo tem slug. Cádmio, inseticidas anticolinesterásicos e flúor/fluoretos não existem em `agentes.yaml` — quando a extração os trouxer, viram `vocabulario_ausente` (D-ARQ-14), não erro silencioso. Expansão de vocabulário é sessão de dado própria.

**Status:** RESOLVIDA na 003.AE (22/06/2026). A migração de campo `anexo_nr07 → tipo_ibe` (passos 1-4 da DT + refinamentos 1-3 da nota 003.AD) foi materializada: enum `TipoIBE` {EE,SC} in-place, valor re-derivado por slug da tabela acima (12 EE + chumbo SC explícito + resto None), fixture e comentário stale corrigidos, consumo-zero reconfirmado por git, 419→420 verde (D-ARQ-38 aplicação 003.AE; commit `e778da8`, merge `78ba5ee`, PR #96). Resíduos NÃO-migração (refinamentos 4-5: 9 CAS null dos EE + cobertura SC parcial) destacados em **DT-003AE-01**, sessão de dado própria.

---

### DT-003AE-01 — Resíduos de dado pós-migração `tipo_ibe`: 9 CAS null + cobertura SC parcial `[ABERTA — sessão de dado própria]`

**Origem:** Sessão 003.AE (22/06/2026), fechamento da migração `anexo_nr07 → tipo_ibe`. Recorte dos refinamentos 4-5 da nota 003.AD da DT-003AB-01, que NÃO são da migração de campo (tarefa de dado distinta, explicitamente marcada como "não pré-requisito" e "sessão própria").

**Situação.** Dois resíduos de dado, ambos não-bloqueantes:
1. **9 dos 12 EE têm `cas: null`** em `agentes.yaml` (só acetona, MEK, benzeno têm CAS). `tipo_ibe` é dado gravado por identidade de agente, não casado por CAS em runtime — a migração funcionou sem os CAS. Faltam: arsenio, dissulfeto_de_carbono, estireno, mercurio, monoxido_de_carbono, n_hexano, tolueno, tricloroetileno, xileno. Afeta o gate-CAS (D-ARQ-36) e a extração futura, NÃO `tipo_ibe`.
2. **Cobertura SC parcial.** Dos 4 agentes SC do Quadro 2 (cádmio, chumbo, anticolinesterásicos, flúor/fluoretos), o vocabulário modela só `chumbo`. Quando a extração trouxer os demais (cádmio/galvanoplastia, fluoretos/alumínio-vidro), viram `vocabulario_ausente` (D-ARQ-14), não erro silencioso.

**O que a resolução exige (sessão de dado, não esta fatia).** Popular os 9 CAS com fonte marcada por agente (CAS Registry, D-ARQ-27) e/ou expandir os slugs SC do Quadro 2. Tarefa de dado com proveniência, natureza distinta de migração de campo — não empilhar.

**Status:** ABERTA. Não-bloqueante. Lado-vocabulário, não toca regra clínica.

---

### DT-003AN-01 — Granularidade do "Derivados de:" multi-CAS na transcrição de FDS `[RESOLVIDA por D-ARQ-45 (003.AQ)]`

**Origem:** Sessão 003.AN (26/06/2026), medição dos 6 PDFs de `fds_originais/`.

**Situação.** Leinertex e Massa-Corrida declaram, na seção 3, blocos "Derivados de:" agrupando 2–3 sub-componentes com CAS empilhados numa célula (`2634-33-5\n55965-84-9`, faixa única `0,2 – 0,05`). O transcritor-FDS (D-ARQ-42) produz `tuple[Componente,...]`; um `Componente` carrega um `cas: str`. Decisão aberta: o bloco multi-CAS explode em N `Componente` (um por CAS, faixa compartilhada) ou agrega num só (qual CAS-primário)? Cruza D-ARQ-35 (a granularidade da promoção a `Risco` herda a granularidade do `Componente`): explodir multiplica os riscos químicos promovidos; agregar perde sub-componentes.

**Por que não decidir agora.** É decisão de arquitetura de granularidade, dependente de como o lado-médico consome o risco promovido — não medição. A medição revelou a forma; a decisão é da sessão que desenhar a IMPL do transcritor (ou ARQUITETURA própria), com o catálogo P1–P3 de D-ARQ-43 em mãos.

**Status:** RESOLVIDA por D-ARQ-45 (003.AQ). O fork explode-vs-agrega foi resolvido a favor de **explode**: o bloco multi-CAS explode em N `Componente` no resolvedor (1→N a montante do `gate_cas`), cada um herdando a faixa inteira do bloco (α). Nota herdada pela IMPL do transcritor-FDS: a distinção empilhado-numa-célula (`extract_tables` devolve `2634-33-5\n55965-84-9`, exige explosão) vs. linhas-de-tabela-separadas (`extract_tables` devolve N linhas, transcritor emite N sem explosão) é critério de transcrição, decisão da IMPL do transcritor — não do resolvedor. Não bloqueia.

---

### DH-003AO-01 — Terminador CRLF de working tree em `.md`, autocrlf-dependente `[RESOLVIDA — D-ARQ-44]`

**Origem:** Sessão 003.AO (26/06/2026), a partir da medição da 003.AN (os 3 docs vivos gravados 100% CRLF no working tree; LF salvo só porque `core.autocrlf=true` renormalizou no `git add`).

**Situação.** Sem regra por arquivo, a integridade do terminador de fim de linha dos `.md` dependia de o `autocrlf` acertar a cada gravação. Distinta de DH-003M-01 (`\r\n` literal como conteúdo de string, defeito de caractere; esta é o byte `0x0D 0x0A` de fim de linha).

**Resolução.** `.gitattributes` na raiz com `*.md text eol=lf` (D-ARQ-44). Escopo `*.md`, não `*` global, para não arrastar reescrita de `.py`/fixtures. Cobre `docs/`, `agente_medico/`, `.claude/skills/kickoff/`.

**Status:** RESOLVIDA por D-ARQ-44. DH-003M-01 permanece ABERTA (defeito distinto).

---

## 11. PONTOS VALIDADOS NA SEGUNDA RODADA (17/05/2026)

Todas as 6 lacunas levantadas na v1 foram resolvidas pela Dra. Carolini:

| ID | Tema | Resposta | Regra atualizada |
|----|------|----------|------------------|
| A-VAL-01 | Risco do PGR não convincente | Segue inventário sem reinterpretar | R-GHE-04 → VALIDADO |
| A-VAL-02 | Classes de FDS desconfiadas | Não existem além de FDS genérica | R-FDS-06 → VALIDADO |
| A-VAL-03 | Espirometria por máscara — clínica ou normativa? | **Normativa** — NR-07, item espirometria | R-ESP-01, R-PGR-03 → base normativa |
| A-VAL-04 | Revisão da matriz Viverde | Matriz correta, sem alterações | Bloco 9 fechado |
| A-VAL-05 | Outros regimes regulatórios | Só aviação (ANAC) | R-REG-ANAC, D-ARQ-04 → simplificada |
| A-VAL-06 | RX sílica ≥ 10% LT | 12 meses, conforme NR-07 | R-RX-01 → VALIDADO |

**Nenhuma lacuna remanescente** no protocolo a partir desta versão.

---

## Histórico de revisões

| Versão | Data | Alterações |
|--------|------|------------|
| v1 | 17/05/2026 | Versão inicial — consolidação dos 47 áudios da Dra. Carolini |
| v2 | 17/05/2026 | Segunda rodada — 6 lacunas (A-VAL-01 a A-VAL-06) fechadas; R-GHE-04 e R-FDS-06 promovidas a VALIDADO; R-RX-01 saiu de INFERIDO para VALIDADO; bases normativas confirmadas em R-ESP-01, R-PGR-03 e R-RX-01; matriz Viverde validada como correta; ANAC confirmada como único regime regulatório sobreposto |
| v3 | 19/05/2026 | Sessão 002.D3: seção 11 "Pendências clínicas em aberto" adicionada com DT-D3-02 (granularidade de fumos_metalicos a refinar com Dra. Carolini) |
| v4 | 23/05/2026 | Sessão 002.I: DT-002I-01 adicionada (limiar de genericidade de R-PGR-05) |
| v5 | 24/05/2026 | Sessão 002.K: DT-002K-01 (gatilho de RX 24M ausente em R-RX-01) e DT-002K-02 (serralheiro e pacote de fumos metálicos) adicionadas — ambas para sessão CONHECIMENTO, originadas da auditoria da RQ.61 contra o protocolo |
| v6 | 25/05/2026 | Sessão 002.L-estudo: DT-002K-01 e DT-002K-02 RESOLVIDAS. R-GHE-02 refinada (indissociável vs. contingente); R-GHE-05 nova (risco contingente → confirmação documental); R-RX-01 refinada com tabela do Anexo III (4 faixas %LEO + estado sem-medição = gatilho do 24M; PNOS 60M). |
| v7 | 25/05/2026 | Sessão 002.L0: R-RX-01 implementada como família R-RX-01-* (D-ARQ-20); R-RX-02 virou regra executável; estado contraditório de quantificação → pendência bloqueante. |
| v8 | 25/05/2026 | Sessão 002.L: DT-002L-01 adicionada (conversão mg/m³ → %LEO para rotear faixa de RX — pergunta de método para a Carolini, originada da estruturação do PGR Viverde) |
| v9 | 28/05/2026 | Sessão 002.M: fonte primária congelada; validação migra para revisão de saída (erro-zero + PDCA, D-ARQ-22). Convenções de status revisadas. Nota de implementação em R-GHE-05 (depende de D-ARQ-23). DT-D3-02/002I-01/002L-01 reclassificadas. Divergência serralheiro Est-09 documentada. |
| v10 | 29/05/2026 | Sessão 002.N: R-RX-01 sílica/asbesto sai de a-conferir → [DERIVADO] (NR-7 Anexo III Quadro 1, 567/2022; bordas ≤, CLSC, NOTA 2); DT-002L-01 RESOLVIDA (LEO sourcing NR-9/NR-15/NR-22); D-ARQ-24 (LEO-resolver); DT-002N-01 aberta (PNOS achata Quadro 2); R-RX-01-pnos e R-RX-02 rebaixados VALIDADO→INTERPRETADO. |
| v11 | 29/05/2026 | Sessão 002.O (META): DT-002N-02 resolvida. Convenção `[DERIVADO]` alinhada a D-ARQ-22 Parte A — fonte vai no marcador (`[DERIVADO — NR-x item y]` etc.), não só no corpo. R-RX-01 "Valores conferidos" passa a `[DERIVADO — NR-7 Anexo III Quadro 1]`. Sem reclassificação de regra. |
| v12 | 01/06/2026 | Sessão 002.V (CONHECIMENTO/ARQUITETURA): DT-002V-01 adicionada — `Quantificacao.valor` não discrimina se o número é o CLSC; premissa "motor consome CLSC, não calcula" a validar com Carolini. Sem reclassificação de regra. |
| v13 | 02/06/2026 | Sessão 002.W: DT-002L-01 e DT-002N-02 resolvidas (marca de pendência removida do título, Status RESOLVIDA no corpo); higiene de conformidade da dívida 002.V. |
| v14 | 03/06/2026 | Sessão 002.X (CONHECIMENTO): DT-002N-01 RESOLVIDA (PNOS Quadro 2: 4 faixas + LEO ACGIH 3 mg/m³ resp; faixa 10–100% = evento único + critério clínico, não 60M); R-RX-01-pnos DEPRECATED → família R-RX-01-pnos-* (ID clínico R-RX-01 inalterado); asbesto LEO 2,0 f/cm³ (f/cm³, fixo, NR-15 Anexo 12); DT-002X-01 (LEO carvão), DT-002X-02 (pós-ocupacional asbesto 30a), DT-002X-03 (NOTA 1) adicionadas. Nada implementado — especificação para sessão de código. |
| v15 | 04/06/2026 | Sessão 002.Y (IMPLEMENTAÇÃO): família R-RX-01-pnos-* materializada em código (predicados de faixa + ramo PNOS no resolver + 4 regras INTERPRETADO + R-RX-01-pnos DEPRECATED); D-ARQ-29 (injeção fração RESPIRAVEL); DT-002Y-01 (lembrete 10–100% não materializado, depende de D-ARQ-28) e DT-002Y-02 (validação Viverde real adiada p/ integração) adicionadas. Suíte 315→327. PR #49, commit 9bb243e. |
| v16 | 05/06/2026 | Sessão 003.A (CONHECIMENTO→ARQUITETURA): DT-002Z-01 catalogada na seção 11 e RESOLVIDA — orquestrador all-or-nothing por GHE resolvido por fonte documental (NR-07 7.5.5/7.6.4), virou D-ARQ-31 (bloqueio por-risco/por-linha, MatrizGHE tri-estado, pendência anexada à linha). Sem reclassificação nem regra clínica nova. |
| v17 | 07/06/2026 | Sessão 003.F (CONHECIMENTO): frente FDS aberta. DT-FDS-01 adicionada — R-BIO-02 [VALIDADO] contradito pelo Anexo I vigente (eixo Quadro 1/IBE-EE vs Quadro 2/IBE-SC, não "Anexo I/II"; conferido no texto oficial MTE, 567/2022). Reabertura adiada para sessão própria (exige Quadro 2 inteiro). R-CLI-02/03 sob suspeita do mesmo rótulo. Nenhuma regra alterada nesta sessão. |
| v18 | 08/06/2026 | Sessão 003.G: nota de procedência em R-FDS-03/04 (cutoff 5% = [VALIDADO] conduta Carolini sem âncora NR; carcinógeno-independe = [INTERPRETADO] INCA/Anexo V; ligação com D-ARQ-33 caminho C). Mesma ID, semântica intacta. Nenhuma regra criada/alterada. |
| v19 | 09/06/2026 | Sessão 003.H (ARQUITETURA): DT-FDS-02 adicionada — unidade do cutoff de 5% (% m/m a confirmar em ABNT NBR 14725); borda 5,0 de D-ARQ-34 fica [INTERPRETADO] até confirmar. Lado-engenheiro, independente de DT-FDS-01. Nenhuma regra criada/alterada. |\r\n| v20 | 13/06/2026 | Sessão 003.L: DT-003L-01 adicionada (mapa de 6 formas de declaração químico no PGR — input empírico para D-ARQ-25; varredura read-only de 15 PGRs). Achados laterais (HISTORICO): tracking misto em matrizes_originais/; "Graxa ET" possível composição inline (veredito-Viverde sob suspeita). Caça do caso-âncora — sem código, sem regra clínica alterada. |
| v21 | 13/06/2026 | Sessão 003.M: DT-003M-01 (ramo-0-vs-bypass com CAS oculto — decisão de arquitetura), DT-003M-02 (vocabulário não cobre composição-de-FDS; medição 23/24 ramo 0) e DH-003M-01 (`\r\n` literal reincidente no HISTORICO) adicionadas. Fatia 3 de D-ARQ-34 (fixture-FDS real) — sem regra clínica criada/alterada. |
| v22 | 13/06/2026 | Sessão 003.N: nota de andamento em DT-003M-02 (frente b-mínimo — 2 solventes de FDS populados em agentes.yaml: acetona, acetato_de_etila; DT segue ABERTA). Sem regra clínica alterada. |
| v23 | 14/06/2026 | Sessão 003.P (IMPLEMENTAÇÃO): DH-003P-01 adicionada (imports de `Materialidade` apontam p/ módulo re-exportador, não `tipos` canônico — higiene de código). Nenhuma regra clínica criada/alterada (`regras.yaml` intocado; fatia 1 de D-ARQ-35 é contrato de risco, não conduta). |
| v24 | 16/06/2026 | Sessão 003.T: DT-003T-01 adicionada (`is_sensibilizante` ausente do `agentes.yaml`; gate-CAS popula só `is_carcinogeno_iarc`; introduzi-la é sessão de dado própria, cruza DT-003M-01). Fatia 2 de D-ARQ-36 Parte 3 — sem regra clínica criada/alterada (gate materializa D-ARQ, não R-*). |
| v25 | 20/06/2026 | Sessão 003.AA (CONHECIMENTO): DT-FDS-01 RESOLVIDA. R-BIO-04 nova (eixo Quadro 1/IBE-EE só-periódico [7.5.15 literal] vs Quadro 2/IBE-SC cinco-momentos [a contrario]; carcinógeno = Anexo V, não desloca momento; caso-âncora tolueno/solventes — superdimensionamento); R-BIO-02 DEPRECATED. R-CLI-02/03 relabel "Anexo I/II" → "Quadro 1/2 do Anexo I" (mesma ID; semestral = conduta Carolini, não 7.5.8; borda Anexo-V [INTERPRETADO]). Quadro 2 lido inteiro (MTE). Sem código. |
| v26 | 21/06/2026 | Sessão 003.AB (ARQUITETURA-leve): DT-003AB-01 adicionada (seção 11) — campo `anexo_nr07` mapeado como eixo morto (consumo-zero verificado por git) e misturado (NR-07 "I" / NR-15 "11"), insumo herdado pela implementação de R-BIO-04 (substituição → `tipo_ibe`, D-ARQ-33). Sem regra clínica criada/alterada; sem código. |
| v27 | 21/06/2026 | Sessão 003.AD (CONHECIMENTO): R-BIO-04 changelog 003.AD (mapa agente→biomarcador + confirmação Quadro 1/2 contra texto oficial; mesma ID); DT-003AB-01 nota de derivação (tabela tipo_ibe por slug que a fatia b transcreve; benzeno=EE corrige fixture+comentário stale; chumbo=SC; 9 CAS null; cobertura SC parcial). DT-003AB-01 segue ABERTA. Sem regra criada/alterada; sem código. |
| v28 | 22/06/2026 | Sessão 003.AE (IMPLEMENTAÇÃO): DT-003AB-01 RESOLVIDA (migração `anexo_nr07 → tipo_ibe` materializada — enum `TipoIBE`, valor por slug, fixture/comentário corrigidos, 419→420). DT-003AE-01 adicionada (resíduos de dado: 9 CAS null dos EE + cobertura SC parcial do Quadro 2 — sessão de dado própria). Sem regra clínica criada/alterada. |
| v29 | 26/06/2026 | Sessão 003.AN (CONHECIMENTO/medição): DT-003AN-01 adicionada (seção 11) — granularidade do "Derivados de:" multi-CAS na transcrição de FDS (explode em N `Componente` vs. agrega; cruza D-ARQ-35), input para a IMPL do transcritor-FDS, originada da medição dos 6 PDFs de `fds_originais/`. Sem regra clínica criada/alterada. Sem código. |
| v30 | 26/06/2026 | Sessão 003.AO (META/higiene): DH-003AO-01 adicionada e RESOLVIDA (seção 11) — `.gitattributes` `*.md text eol=lf` blinda terminador de markdown na origem (independe de `core.autocrlf`); distinta de DH-003M-01 (`\r\n` literal-conteúdo, segue ABERTA). Doc-only, sem código, sem regra clínica. |
| v31 | 27/06/2026 | Sessão 003.AQ (ARQUITETURA): DT-003AN-01 RESOLVIDA por D-ARQ-45 (seção 11) — fork explode-vs-agrega resolvido a favor de explode (bloco multi-CAS explode em N `Componente` no resolvedor, herança-α da faixa inteira); nota da distinção empilhado-vs-linhas-soltas herdada pela IMPL do transcritor-FDS. Nenhuma R-* tocada (P1 não cria/altera conduta). Sem código. |
