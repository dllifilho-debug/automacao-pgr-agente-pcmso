# PROTOCOLO DO AGENTE MÉDICO PCMSO — v2

**Fonte primária:** Entrevista assíncrona com Dra. Carolini Polesso (Coordenadora PCMSO, Seconci-GO), 47 áudios em 16/05/2026 + segunda rodada de validação em 17/05/2026.
**Caso de referência:** PGR Viverde V02 (03.02.2025) + Matriz RQ.61 Viverde (06.03.2025) — **validada como correta** pela Dra. Carolini.
**Status:** Protocolo validado. Pendências de v1 fechadas.

Cada regra tem ID estável (`R-CATEGORIA-NN`). O ID **não muda** entre versões — alterações de conteúdo geram nota de revisão na própria regra.

Convenções de status:
- `[VALIDADO]` — extraído diretamente da entrevista, sem ambiguidade
- `[INFERIDO]` — extraído por dedução de outras respostas, precisa confirmação
- `[A VALIDAR]` — lacuna ou ponto em que a resposta foi parcial

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
Cargos com risco característico recebem os exames do risco **mesmo quando o inventário do PGR não declara explicitamente** a exposição.

**Caso âncora — soldador:** mesmo que o inventário não cite fumos metálicos, a presença do cargo "soldador" implica exposição. Aplicar protocolo de fumos metálicos (ver R-PKG-SOLD).

Esta regra é a expressão clínica do princípio: *"não existe solda sem fumos metálicos"*. O sistema deve aceitar **risco implícito por cargo** como cidadão de primeira classe.

### R-GHE-03 — Múltiplos riscos, mesmo exame `[VALIDADO]`
Quando o mesmo exame é exigido por riscos distintos no mesmo GHE → **linha única** na matriz. A periodicidade não se altera em função do número de riscos que pedem o exame.

### R-GHE-04 — Risco listado mas não convincente `[VALIDADO]`
Quando o PGR lista um risco que parece não realista para o GHE, a Dra. Carolini **segue o inventário** sem reinterpretar nem rejeitar. O documento é a fonte de verdade do escopo de risco.

**Implicação para o agente:** não implementar lógica de "filtragem clínica de riscos do PGR". O inventário é canonical.

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

#### R-RX-01 — Sílica e PNOS `[VALIDADO]`
- **Sílica com medição quantitativa < 10% do LT** → RX 60 meses
- **Sílica com medição quantitativa ≥ 10% do LT** → RX 12 meses
- **Sílica com avaliação apenas qualitativa** → RX 12 meses (precaucional)
- **PNOS** (poeira não classificada) → RX 60 meses
- **Poeira não caracterizada no PGR** (sem distinção mineral / PNOS / orgânica) → tratar como sílica → RX 12 meses

**Base normativa:** NR-07, item de RX de tórax para exposição a sílicas. Confirmado pela Dra. Carolini.

#### R-RX-02 — Fumos metálicos `[VALIDADO]`
Cargo com exposição a fumos metálicos (incluindo soldador) → RX **60 meses** em adm/per/MR/dem.

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

**Status:** A VALIDAR. Não bloqueia o motor — caso âncora soldador continua funcional com a categoria única. Refinamento entra quando houver método extraído da especialista.

### DT-002I-01 — Limiar de genericidade de R-PGR-05 `[A VALIDAR]`

**Origem:** Sessão 002.I (19→23/05/2026), durante o desenho de Stage 3.

**Situação.** R-PGR-04 (composição química ausente) tem consequência estrutural explícita — "a matriz não pode ser fechada" → Stage 3 bloqueante (D-ARQ-17). R-PGR-05 (PGR mal escrito: riscos genéricos, sem quantificação, sem agentes especificados) não tem: o protocolo manda "solicitar FDS / conversar com o elaborador" e diz **não rejeitar**, mas não define se a matriz **bloqueia** (PRELIMINAR até correção) ou apenas acompanha TODO operacional. Parte do conteúdo de R-PGR-05 já tem mecanismo: "sem quantificação" → predicado `Ausente` (D-ARQ-13); "sem agente especificado" → `vocabulario_ausente` (D-ARQ-14). O resíduo é o **limiar de vagueza global do inventário** — decisão clínica, não arquitetural.

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura):** a partir de que ponto a generalidade do inventário te faz parar e exigir reescrita do PGR, vs. seguir montando a matriz com ressalva operacional? Buscar o **método** (o limiar), não o resultado por empresa.

**Status:** A VALIDAR. Não bloqueia o motor — R-PGR-04/Stage 3 cobrem o caso âncora (FDS faltante).

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