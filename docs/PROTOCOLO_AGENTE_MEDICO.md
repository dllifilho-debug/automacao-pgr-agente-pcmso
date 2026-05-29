# PROTOCOLO DO AGENTE MÉDICO PCMSO — v2

**Fonte primária:** Entrevista assíncrona com Dra. Carolini Polesso (Coordenadora PCMSO, Seconci-GO), 47 áudios em 16/05/2026 + segunda rodada de validação em 17/05/2026.
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
- `[DERIVADO — fonte]` — resolvido após 002.M por fonte objetiva: norma vigente (citar NR
  e item, conferida no site oficial do MTE), matriz já validada como precedente (RQ.61
  Carolini / matriz Patrícia), ou analogia direta com regra `[VALIDADO]`. Alta confiança;
  a fonte é nomeada no corpo da regra.
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

#### R-CLI-02 — Anexo I e Anexo II (NR-07) `[VALIDADO]`
Cada anexo, isoladamente, demanda clínico **semestral**. Quando o trabalhador está exposto a agentes de **ambos os anexos**, registrar em **uma única linha** semestral (não duplicar).

#### R-CLI-03 — Manganês fora dos Anexos `[VALIDADO]`
O **manganês** é o único agente fora dos Anexos I e II da NR-07 que dispara clínico semestral. Base: NR-15 — exposição a Mn exige avaliação biológica independente do limite de tolerância.

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
| R-RX-01-pnos | pnos | 60M | — |

`R-RX-01` permanece o ID clínico estável; as entradas `R-RX-01-*` são implementação (D-ARQ-20). **Estado contraditório:** se o PGR declara `pct_LT` e ausência de avaliação quantitativa ao mesmo tempo, o motor emite pendência bloqueante (não escolhe faixa) — input incoerente vira pedido de correção, não chute (D-ARQ-08/13). **Valores conferidos `[DERIVADO — fonte]`:** periodicidades, limiares e corte de 15 anos conferidos contra o texto literal do Anexo III da NR-07, Quadro 1 (Portaria MTP 567/2022), no site do MTE (002.N). Faixas fechadas com limite superior inclusivo (`≤`): >10 e ≤50; >50 e ≤100; >100. Variável de roteamento é o CLSC = limite superior do IC 95% da média aritmética (distribuição lognormal), conforme definição literal do Quadro 1 — NÃO é percentil 95. NOTA 2 do Quadro 1: trabalhador com exposição reduzida que esteve em concentração maior por ≥1 ano mantém o intervalo do período de maior exposição (a modelar — ver DT). PNOS segue o Quadro 2, não o Quadro 1 (ver R-RX-01-pnos e DT própria).

**Base normativa:** Anexo III da NR-07 (Portaria 567/2022). Validação clínica: Dra. Carolini, 05/2025.

**TODO normativo — RESOLVIDO em 002.N `[DERIVADO]`:** faixas, periodicidades e corte de 15 anos do Quadro 1 (sílica/asbesto) conferidos contra o texto literal do Anexo III (Portaria 567/2022, site do MTE). Resíduos abertos: (a) classificador de faixa deve rotear por CLSC e tratar bordas com `≤` (fix de código); (b) PNOS achata o Quadro 2 (DT); (c) R-RX-02 fumos sem âncora no Anexo III (DT).

#### R-RX-02 — Fumos metálicos `[VALIDADO]`
Cargo com exposição a fumos metálicos (incluindo soldador) → RX **60 meses** em adm/per/MR/dem.

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

#### R-BIO-02 — Matriz temporal por Anexo NR-07 `[VALIDADO]`
- **Anexo I** (carcinógenos sem LT seguro) → biomonitoramento **apenas no periódico**
- **Anexo II** (com LT) → biomonitoramento em **adm + per + RT + MR + dem**

#### R-BIO-03 — Manganês `[VALIDADO]`
Qualquer exposição confirmada a Mn → **manganês sanguíneo semestral em adm + per + MR**. Base: NR-15, independente do LT.

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

### DT-002L-01 — Conversão de concentração medida (mg/m³) em faixa de %LEO para RX `[A VALIDAR]`

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