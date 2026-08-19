# Pendências clínicas em aberto

Extraído do §11 de `docs/PROTOCOLO_AGENTE_MEDICO.md` em 003.ET (fatia 0), por D-ARQ-63:
o §11 era 58,9% do PROTOCOLO e estourava o nível 1 do gate de abertura. Conteúdo movido
verbatim; nenhuma dívida foi criada, fechada, reenquadrada ou reescrita nesta operação.

Convenção preservada: `DT-*` = dívida técnica/clínica, `DH-*` = dívida de higiene.
O documento-mãe é `docs/PROTOCOLO_AGENTE_MEDICO.md`.

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

**Nota (003.EI):** sob R-ESP-02 este veredito fica desatualizado — tinta é agente químico não-mineral, cai no item 3.2 do Anexo III (condicionado a sinais ou sintomas respiratórios), logo NÃO dispara espirometria por exposição. O veredito original é preservado como registro do que se sabia em 002.L-estudo.

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

**Pergunta de método (derivação normativa, D-ARQ-27 — Carolini valida saída pronta, não método)** (método, não resultado): *quando um laudo traz uma estatística que não é o CLSC do Quadro 1 — média simples, pico, percentil 95 — qual é a conduta?* Recusar e pedir CLSC? Tratar como sem-avaliação-quantitativa (R-RX-01-sem, 24M)? Converter? A resposta define se o gap fecha por sinalização na extração (D-ARQ-25 Parte B → Pendencia), por campo discriminador com regra consumidora, ou por fallback clínico.

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

### DT-003M-01 — Ordem ramo-0-vs-bypass quando o CAS é oculto `[FECHADA — D-ARQ-56, 003.CK]`

**Origem:** Sessão 003.M (13/06/2026), leitura da FDS do Adesivo PVC Tigre (PGR ALT T65).

**Situação.** O predicado de materialidade (003.J, `motor/materialidade.py`) avalia o ramo 0 (`agente is None` → AUSENTE) ANTES do ramo 1 (bypass de perigo → MATERIAL). A justificativa da 003.J: sem slug não há flags confiáveis. A FDS do Adesivo PVC traz um contra-exemplo: o componente "Segredo Industrial 2" declara H334 (sensibilização respiratória) + H317 (sensibilização dérmica) na própria FDS, mas tem CAS OCULTO (segredo industrial). Sem CAS → sem slug → `agente=None` → ramo 0 → AUSENTE, mascarando o bypass-sensibilizante que a flag justificaria.

**Por que é arquitetura, não disciplina de fixture.** O estado `sem-slug + flag-de-perigo-declarada-no-documento` é alcançável pelo PIPELINE REAL, não só pela fixture-à-mão: a FDS declara perigo por frase-H em componente de CAS oculto; a extração (D-ARQ-25 Parte B) resolve CAS→slug→flag, e o CAS oculto quebra a cadeia. A flag de perigo é dado do documento, não conhecimento injetado. A pergunta de arquitetura: quando o documento declara sensibilização mas oculta o CAS, o sistema deve (a) bloquear por falta de slug (perde o sinal de perigo declarado) ou (b) honrar a flag mesmo sem slug?

**O que a reabertura exige (sessão própria).** Decisão sobre a ordem ramo-0-vs-bypass — toca o predicado da 003.J e o gate-CAS de D-ARQ-33 cláusula 3 (CAS oculto ≠ CAS inválido — casos distintos que o gate hoje não separa). Provavelmente a mesma sessão de DT-003M-02 (expansão de vocabulário), porque "sem-slug + flag" e "popular slugs de FDS" são dois lados de cobrir composição-de-FDS.

**Nota de cluster (003.CH).** Unificada com DT-003M-02(B) e DT-003T-01 sob "extrair perigo (frases-H) para as flags do `Componente`". A reordenação do ramo-0 aqui pedida (honrar bypass antes do slug-check) só é segura DEPOIS que a perigo-transcrição (recorte B de D-ARQ-42) popular `is_carcinogeno_iarc`/`is_sensibilizante` — hoje `False` por não-extração, não por classificação (`[VERIFICADO — git grep, 003.CH]`). Sequência ratificada: perigo-transcrição → reordenação (fecha DT-003M-01 + DT-003M-02(B) juntas). Ver reframe em DT-003M-02.

**Status:** FECHADA (003.CK, D-ARQ-56, PR #192). Resolução: alternativa (b) — honrar a flag mesmo sem slug. Caso-âncora coberto por teste de travessia e de fixture real.

**Nota (003.CI).** Pré-condição escrita: D-ARQ-55 (recorte B) dá contrato ao perigo-transcrito — `frases_h` por-membro + mapa {H334,H317}→`is_sensibilizante`. Com a flag populada e carregada mesmo no CAS-oculto (SI2), "ausência de flag" passa a significar "FDS sem perigo". A reordenação ramo-0-vs-bypass que esta DT pede é o **passo 2** (honrar flag antes do slug-check, em `materialidade()` + Fase C), agora seguro. DT segue ABERTA até o passo 2 (fecha junto com DT-003M-02(B)).

**Nota de fechamento (003.CK, D-ARQ-56).** Passo 2 implementado (PR #192): bypass avaliado ANTES do ramo-0 em `materialidade()` — SI2 (H334+H317, CAS oculto) → MATERIAL; Fase C emite `bypass_sem_slug` bloqueante nomeando as frases-H literais, SEM promover Risco (promoção-sem-slug é DT-003CK-01, condicionada a regra clínica de sensibilizante genérico). Testes: `test_cas_oculto_com_h334_h317_e_material_via_bypass_sem_slug` (inversão do teste-fronteira de 003.CJ) e `test_adesivo_segredo_industrial_2_bypass_sem_slug_bloqueante` (fixture real). Custo declarado: visibilidade, não conduta — exame ainda não dispara no CAS-oculto.

---

### DT-003M-02 — Vocabulário (agentes.yaml) não cobre composição-de-FDS `[ABERTA — só (A) dado; (B) FECHADA por D-ARQ-56, 003.CK]`

**Origem:** Sessão 003.M (13/06/2026), medição da fixture-FDS sobre `agentes.yaml`.

**Situação.** Dos 24 componentes de 3 FDS reais (Tinta Acrílica, Cimento Ciplan, Adesivo PVC), 23 caem em ramo 0 do predicado de materialidade (`agente=None`, slug não resolvido). Só 2 substâncias têm slug em `agentes.yaml`: `dioxido_de_titanio` (TiO₂) e `metil_etil_cetona` (MEK). `agentes.yaml` é vocabulário de inventário-de-PGR (sílica, asbesto, poeira, ruído, ototóxicos, fumos, agentes-marcador) — não de composição-de-FDS. Os ingredientes típicos de produto comercial (carbonato de cálcio, silicato de alumínio, silicato tricálcico/dicálcico, óxido de ferro, polímeros acrílicos, isotiazolonas, acetona, acetato de etila, copolímero de PVC) NÃO estão no vocabulário.

**Consequência.** A materialidade-por-concentração e a materialidade-por-bypass só são exercitáveis sobre componentes com slug. Enquanto o vocabulário não cobrir composição-de-FDS, a fixture-real rende majoritariamente AUSENTE (ramo 0) — fiel ao estado, mas sem travessia para MATERIAL/NÃO-MATERIAL na maioria. Ramo 5 (NÃO-MATERIAL fiel) não tem nenhum caso vivo nas 3 FDS (nenhum componente com slug tem faixa inteira ≤5%).

**Irmã de DT-003L-01.** DT-003L-01 mapeia as formas de declaração química no PGR (lado-inventário); DT-003M-02 mede o vazio de vocabulário no lado-composição. Ambas são input empírico para a camada de extração/normalização (D-ARQ-25) e para a expansão de `agentes.yaml`.

**O que a expansão exige (sessão de dado, não desta fatia).** Adicionar os agentes de FDS a `agentes.yaml` com `is_carcinogeno_iarc`/`is_sensibilizante` por agente, fonte marcada por agente (D-ARQ-27). É tarefa de dado com proveniência, maior que uma fixture e de natureza distinta — não empilhar com fixture.

**Andamento (003.N, parcial — NÃO fecha).** Frente (b) executada em recorte (b-mínimo): das substâncias de ramo 0, partição medida — 14 têm CAS resolvível na fixture, ~9 têm cas="" (não populáveis por slug; dependem de descoberta-CAS ou são CAS-oculto). Dos 14 com CAS, populados 2 (`acetona` 67-64-1, `acetato_de_etila` 141-78-6) — os únicos que atravessam para MATERIAL/straddle quando hidratados; os 12 inertes restantes (carbonatos, silicatos, óxidos do clínquer, ferro-aluminato) são flag-False → NÃO-MATERIAL sem efeito de conduta, adiados até a hidratação provar que distingui-los importa. Inaugurado o padrão de ficha-de-composição (003.N, commit 4945396). Reenquadramento medido: popular agentes.yaml NÃO destrava o predicado — materialidade() lê flags do Componente, não do yaml (D-ARQ-34 Parte 4); o elo é a hidratação CAS→slug→flags (D-ARQ-25 Parte B, inexistente). (b) entrega vocabulário pronto para a hidratação, não travessia. O sensibilizante-CAS-oculto (Segredo Industrial 2) é DT-003M-01, não esta DT.

**Reframe (003.CH, 10/07/2026) — o andamento 003.N está defasado; (B) tem pré-requisito duro.** Duas correções ao registro acima, verificadas por git nesta sessão:

1. **A hidratação CAS→slug→flags que 003.N deu por "inexistente" FOI construída.** `resolvedor.py`/`gate_cas` (003.S), `composicao.py`/`resolver_composicao` (003.V/W), cadeia de transcrição-FDS FECHADA (DT-003AS-01, 003.BI). O elo existe; falta vocabulário para os ingredientes resolverem nele.
2. **As flags de perigo do `Componente` NÃO são populadas em produção** `[VERIFICADO — git grep, 003.CH]`. Nenhum código fora de fixture seta `is_carcinogeno_iarc=True`/`is_sensibilizante=True`; o transcritor "não classifica perigo" (frases-H = recorte (B) EXCLUÍDO de D-ARQ-42); `MembroVerbatim`/`BlocoVerbatim` não carregam campo de perigo. Logo, em produção, "sem flag" significa **"não extraímos"**, não **"FDS declarou sem perigo"**.

**Consequência — separação DADO vs. ARQUITETURA.** DT-003M-02 mistura duas naturezas:
- **(A) DADO** — popular `agentes.yaml` com ingredientes de FDS + flags com proveniência (é o "sessão de dado" que a DT já nomeia; fonte = CAS Registry/IARC/GHS via D-ARQ-27, não a Carolini).
- **(B) ARQUITETURA** — o default da Fase C "componente sem slug → `materialidade_ausente` BLOQUEANTE" (`riscos.py`, ramo `agente is None`). Combinado com vocabulário esparso, trava o GHE para toda FDS com carga inerte.

**Achado sobre (B).** "Sem slug → bloqueia" NÃO é bug: é o estado conservador-CORRETO enquanto o perigo não é extraído. Não-bloquear o inerte por ausência-de-flag passaria carcinógeno real em silêncio (D-ARQ-22), porque a flag está `False` por não-extração, não por classificação. (Não estoura hoje porque carcinógenos in-vocab — benzeno — disparam por identidade de slug via R-PKG-BZ, 003.Q, mascarando o buraco.)

**(B) não é resolvível isolada — pré-requisito duro:** a **transcrição de perigo** (frases-H → flags do `Componente`), que é o recorte (B) excluído de D-ARQ-42 e o MESMO cluster de DT-003M-01 (honrar frase-H de CAS oculto) e DT-003T-01 (`is_sensibilizante` ausente). Os três convergem em "extrair perigo para as flags do `Componente`". Só quando "ausência de flag" significar "FDS declarou sem perigo" é que a reordenação do ramo-0 (honrar flag antes do slug-check, em `materialidade()` + Fase C) fica segura e fecha DT-003M-01 + DT-003M-02(B) de uma vez.

**Sequência ratificada pelo Diovanni (003.CH):** (1) perigo-transcrição (recorte B de D-ARQ-42) → popula as flags e fecha DT-003T-01; (2) só então a reordenação do ramo-0 → fecha DT-003M-01 + DT-003M-02(B) juntas. A digitação de vocabulário (A) e a lista-de-inertes ficam sinalizadas como **paliativo** (enumeração paralela ao sinal que a FDS já carrega). `[INTERPRETADO — prioridade na revisão de saída]` na articulação "ausência de frase-H ⇒ inerte" (ancorada em R-FDS-06, sem norma literal).

**Status:** ABERTA só em **(A)** (sessão de dado — vocabulário de FDS com proveniência). **(B) FECHADA (003.CK, D-ARQ-56, PR #192):** componente sem slug e sem frase-H declarada deixa de travar o GHE — pendência `materialidade_ausente` NÃO-bloqueante (inerte-declarado, R-FDS-06); frase-H não-mapeada mantém bloqueante (conservador-correto, D-ARQ-35). Cluster resolvido: DT-003T-01 fechada (003.CI/CJ), DT-003M-01 fechada (003.CK).

**Nota (003.CI).** O pré-requisito duro (perigo-transcrição) ganhou contrato em D-ARQ-55: o recorte B popula `is_sensibilizante` a partir da frase-H. (B) NÃO fecha nesta sessão — depende do **passo 2** (reordenação do ramo-0 de `materialidade()`/Fase C para honrar a flag antes do `agente is None`), que fecha (B) junto com DT-003M-01. (A) (digitar vocabulário de FDS) segue sessão de dado, sinalizada como paliativo. DT segue ABERTA.

**Nota de fechamento de (B) (003.CK, D-ARQ-56).** Passo 2 implementado (PR #192): Fase C tripartida no `agente is None` — (a) bypass declarado → `bypass_sem_slug` bloqueante; (b) `frases_h == ()` → inerte-declarado NÃO-bloqueante (fecha (B)); (c) frase-H não-mapeada → bloqueante mantido. Ressalva de fixture: `()` de `fds_verbatim_t65` é medição PENDENTE (003.CJ decisão 6) — os testes de fixture real exercitam o contrato dado o input, sem afirmar ausência na FDS real (comentários corrigidos em `1ad7ca3`).

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

**Nota de cluster (003.CH).** DT-003T-01 é a **fatia 1** do cluster unificado (DT-003M-01 + DT-003M-02(B) + DT-003T-01): a perigo-transcrição (recorte B de D-ARQ-42) que popula `is_sensibilizante` (e confirma `is_carcinogeno_iarc`) no `Componente` a partir da frase-H da FDS é o pré-requisito duro das outras duas. Sequência ratificada (003.CH): esta fatia primeiro → depois a reordenação do ramo-0. Ver reframe em DT-003M-02.

**Status:** RESOLVIDA (003.CI) por D-ARQ-55, por caminho DISTINTO do que a DT propunha. A DT pedia `is_sensibilizante` no `EntradaIndice`/`agentes.yaml` (fonte-vocabulário, casada por CAS); D-ARQ-55 popula `is_sensibilizante` a partir da **frase-H transcrita da FDS** ({H334,H317} → flag, mapa determinístico resolver-side), proveniência = FDS admitida pelo RT, não vocabulário. O vetor vocabulário-side fica DESNECESSÁRIO para o cluster — a fonte da flag é a FDS. Se um sensibilizante conhecido SEM H-phrase na FDS específica exigir fonte-vocabulário no futuro, é sessão de dado própria e não bloqueia. Implementação (código) é fatia futura; a arquitetura da entrada da flag está decidida. DT-003M-01/DT-003M-02(B) fecham no passo 2 (reordenação).

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

### DT-003AS-01 — Patologias de layout/transcrição da tabela de composição de FDS `[FECHADA — 003.BI]`

**Origem:** Sessão 003.AS (29/06/2026), medição determinística (`pdfplumber.extract_tables()` puro) dos 6 PDFs de `fds_originais/`, ao construir a fatia parse-PDF (D-ARQ-42 Parte 1 / D-ARQ-43 Parte 1).

**Situação.** O parse-PDF determinístico (`extrair_tabelas_fds`, 003.AS) entrega as tabelas cruas do pdfplumber. A montagem `grade crua → tuple[Componente,...]` (transcrição, fatia futura) enfrenta seis patologias medidas em dado real, distintas das de D-ARQ-43 (que cobriu conteúdo: multi-CAS, ordem-de-faixa, CAS-oculto). Estas são de **layout/coluna/token**:

1. **Composição não-isolável (Ciplan, Tigre) — a mais grave.** `extract_tables` funde a composição com o resto da página num grid multi-seção: em Ciplan, a composição são as colunas 4-7 de linhas não-contíguas dentro de uma tabela única que carrega seções 1-7; em Tigre, é um grid de 9 colunas. Não há "tabela de composição" isolável por índice. A transcrição precisa **localizar a região por âncora de header textual** ('COMPOSIÇÃO E INFORMAÇÕES SOBRE INGREDIENTES' como início, header da seção seguinte como fim), não por "pegar a tabela N". Contrasta com tinta/Leinertex/Massa, onde a composição é tabela isolada limpa.
2. **Coluna deslocada na mesma tabela (Tigre).** Nome/CAS/faixa vêm em col 1/4/7 para Acetona/Copolímero/tiofenodiil/Segredo, mas em col 0/3 sem faixa para MEK e Acetato — a faixa não está em `None` numa posição fixa, simplesmente não está naquela linha. Parser por índice fixo perde a faixa em silêncio (erro silencioso plausível, D-ARQ-22). Exige heurística por posição/bbox, não índice.
3. **`\n` intra-token no CAS (tinta, TiO₂ `134363-67-\n7`).** O mesmo `\n` é separador-multi-CAS (P1, split legítimo) em Leinertex/Massa e quebra-de-render-no-meio-de-um-CAS em tinta. Desambiguar exige regex de CAS bem-formado (dígitos-dígitos-dígito) antes de decidir split — julgamento, lado-transcrição, NÃO no `.split("\n")` cego de `_explodir_multi_cas` (mexê-lo reabriria D-ARQ-45).
4. **Múltiplas grafias de CAS-ausente.** `vários` (Ciplan), `ND`/`NA`/`*`/`**`/`****` (Tigre/tinta), `Segredo Industrial`/`Informação confidencial` (Leinertex/Massa) — todas mapeiam para `cas=""` (convenção da fixture), mas o mapa de grafias é interpretação.
5. **Separador de faixa varia:** hífen comum `-` (Ciplan/tinta) vs en-dash `–` (Tigre/Leinertex/Massa). Normalizar antes de `_normalizar_faixa` ler o par.
6. **Coluna de perigo europeia (tinta: 'Símbolo' Xn/Xi/C, 'Frases R' R21/22…).** Perigo declarado no documento — deliberadamente **descartado** pelo recorte (A) de D-ARQ-42 (frases-H/R fora de escopo, cruza DT-003M-01/DT-003T-01). Registrado para a fatia futura de perigo-transcrito saber onde o dado mora.

**Seção da composição — número a confirmar.** Ciplan rotula a composição **"2 COMPOSIÇÃO E INFORMAÇÕES SOBRE INGREDIENTES"** (literal na medição) — seção **2**, não 3. Tinta não numera. D-ARQ-42/43 e R-FDS-02 dizem "seção 3 / 2-3". Variação por fabricante/versão da norma comprovada em dado. `[A CONFIRMAR — número da seção de composição na ABNT NBR 14725 vigente; conferir texto oficial antes de cravar âncora de header textual na transcrição]`.

**Sobre "ler qualquer FDS" (moldura, não promessa).** A meta é ler qualquer FDS **digital** (com camada de texto). FDS escaneada sem OCR é imagem — `extract_tables` devolve vazio; OCR é contingência futura declarada (D-ARQ-43 Parte 1), não construída. Mesmo entre as digitais, não há parser de regra fixa que leia "qualquer layout" — a medição mostrou 4 layouts incompatíveis em 6 PDFs. Por isso a transcrição é **LLM** (D-ARQ-41/42): tolera layout nunca visto por ler o sentido, não a posição. E mesmo a transcrição-LLM é **não-determinística e sua saída é candidata** revisada pelo responsável técnico (D-ARQ-33 cl.4), não classificação automática confiável. Hoje o motor lê 0 FDS automaticamente (3 transcritas à mão); o caminho é parse-PDF (✓ 003.AS) → transcrição-LLM (fatia futura) → muitas FDS, não qualquer uma; cada layout novo que quebrar vira input append-by-medição.

**O que a transcrição exige (fatia futura, não esta).** Localização-de-composição por header textual (patologia 1); leitura por posição/bbox (2); desambiguação `\n` por regex-CAS (3); dicionário de grafias-de-ausente (4); normalização de separador de faixa (5). O mecanismo (LLM vs heurística determinística vs híbrido) é decisão da fatia de transcrição, à luz de D-ARQ-41 Parte 3 (gate de slug) e D-ARQ-42 Parte 1.

**Andamento (003.AU).** Patologias 3/4/5 materializadas como funções puras determinísticas em `agente_medico/motor/transcricao_fds.py` (`desambiguar_cas`/`normalizar_cas_ausente`/`parsear_faixa`), isoladas, sem consumidor. P3 com heurística refinada (preserva o `\n` só quando ambos os fragmentos são CAS bem-formados; senão junta — validade é do `gate_cas`, não da camada de forma). Restam ABERTAS as patologias 1 (composição não-isolável, grid fundido Ciplan/Tigre) e 2 (coluna deslocada/bbox) — camada-LLM/localização, fatia futura. DT segue ABERTA.

**Andamento (003.AX).** Patologias 1 (composição não-isolável) e 2 (coluna deslocada) DECIDIDAS na camada-LLM, não em parser determinístico por bbox (nota de aplicação 003.AX em D-ARQ-42): a transcrição é LLM semântico sobre `extract_text` da região âncora-por-título (003.AT), não sobre `extract_tables`. Medição read-only (Ciplan/Tigre, 003.AX): o título-âncora sobrevive no `extract_text` e some no `extract_tables` do Tigre; a patologia 2 é **artefato do `extract_tables`** — no `extract_text` MEK/Acetato voltam com faixa. Mecanismo (LLM) decidido; IMPL do transcritor é fatia futura. Consequência da troca tabelas→texto sobre o multi-CAS (D-ARQ-45) e sobre o `extrair_tabelas_fds` (003.AS): DT-003AX-01 (abaixo).

**Andamento (003.AY).** Entrada da camada-LLM cravada em TEXTO-PURO (`extract_text` âncora-por-título) pela reconciliação DT-003AX-01 (nota 003.AY em D-ARQ-42). Patologia 1 (grid fundido) opera sobre `extract_text` (título-âncora localiza o início; isolamento da grade segue camada-LLM); patologia 2 (coluna deslocada) confirmada artefato do `extract_tables`, não recorre no texto. Patologia 1 segue input da IMPL do transcritor; DT segue ABERTA.

**Andamento (003.AZ).** Fatia (i) do transcritor materializada: forma do verbatim-grupo (`BlocoVerbatim` aninhado) + montagem-de-grupo (`montar_composicao → tuple[BlocoComponente,...]`, faixa 1×/bloco). Falta a expansão 1→N + herança-α no resolver e o `extrair_tabelas_fds` DEPRECATED — fatia (ii)/003.BA.

**Andamento (003.BD) — patologia 1 MEDIDA e DESBLOQUEADA (producibilidade confirmada).** Medição CONHECIMENTO (`extract_text` pdfplumber da região âncora-por-título dos 2 grid-fundidos, transcrição por sentido contra o gabarito `fds_t65`): **Tigre 7/7, Ciplan 8/8** em `cas` + `concentracao`. O "grid fundido" é **interleave de coluna em ordem linear do texto** (composição intercalada com a seção vizinha), NÃO perda de informação — os triplos estão todos presentes. A ordem de coluna INVERTE por fabricante (Tigre `[nome, CAS, faixa]`, Ciplan `[nome, faixa, CAS]`) → o LLM roteia por FORMATO do token (CAS `dd…-dd-d`; faixa `n–n %`), não por posição — confirma a decisão anti-bbox de 003.AX. Ruído (tabela de LT em ppm, Tigre p.1) descartado pela disciplina do triplo. Reenquadra o limite de D-ARQ-46 ("producibilidade barrada pela patologia 1"): o bloqueio era ausência de LLM real invocado, não impossibilidade intrínseca. Contrato de invocação+gate do transcritor-LLM cravado em **D-ARQ-47** (revisão-RT-sobre-verbatim como admissão do candidato). Patologia 2 confirmada artefato do `extract_tables` (003.AX), não recorre no texto. **A DT segue ABERTA:** falta a IMPL do transcritor-LLM real + `extrair_texto_fds` (parse-texto greenfield); DT-003M-01 (frase-H/CAS-oculto SI2/H334) intocada, fora do recorte A.

**Andamento 003.BE (02/07/2026):** `extrair_texto_fds` materializada (D-ARQ-47 consequência) — recorte âncora-por-título com sobre-inclusão, núcleo puro + wrapper, 16 testes, suíte 491→507. Resta transcritor-LLM real + gate de forma (cláusulas 1-3/5). DT segue ABERTA.

**Andamento 003.BF (02/07/2026):** invocação injetável (`TranscritorLLM` Protocol + `transcrever_fds`, cl.1/2) + `gate_forma` (cl.3, reprovado → Pendencia bloqueante `forma_verbatim_fds`) + harness mockado tinta/Ciplan sobre `extrair_texto_fds` real, materializados (`transcritor_fds.py`, 10 testes, suíte 507→517). Resta cliente-LLM real + prompt (cl.5) e ponto de revisão-RT (cl.4). DT segue ABERTA.

**Fechamento (003.BI, 05/07/2026).** Patologias 1/2 resolvidas na camada-LLM sobre `extract_text` (003.AX/BD/BE); patologias 3/4/5 em `transcricao_fds.py` (003.AU); invocação+gate (003.BF); cliente real (003.BG); validação ao vivo 3/3 (003.BH); revisão-RT + serialização (003.BI, `motor/revisao_verbatim.py`) — cadeia extração→LLM→gate→revisão-RT→montagem→resolvedor completa. Residual que NÃO reabre esta DT: DT-003M-01 (frase-H/CAS-oculto, recorte A), DT-003BG-01 (gabarito 3/6), DT-003AW-01 (grafia-de-ausente com `\n`, não-medida), UI da revisão-RT.

**Status:** FECHADA (003.BI). Cadeia extração→LLM→gate→revisão-RT→montagem→resolvedor completa e testada fim-a-fim (mock, sem API) contra `fds_t65`. Patologia 1 producível por LLM validado ao vivo (003.BD/BH, D-ARQ-47). Residuais listados acima não reabrem esta DT.

---

### DT-003AW-01 — Grafia-de-ausente quebrada por `\n` de render escapa ao reconhecimento `[ABERTA — não-medida, não-bloqueante]`

**Origem:** Sessão 003.AW (30/06/2026), passada adversária sobre a montagem `verbatim → Componente` (D-ARQ-46).

**Situação.** A montagem aplica `normalizar_cas_ausente(desambiguar_cas(cas_bruto))` (D-ARQ-46 Parte 4). Se uma grafia-de-ausente textual chegar quebrada por `\n` de render no campo `cas` (ex.: `"Segredo\nIndustrial"`, plausível em coluna estreita), `desambiguar_cas` junta os fragmentos sem espaço (`"SegredoIndustrial"`) — nenhum fragmento é CAS bem-formado — e `normalizar_cas_ausente` não casa a grafia `"segredo industrial"` (com espaço) em `_GRAFIAS_CAS_AUSENTE`. Resultado: `cas="SegredoIndustrial"` em vez de `""` → ramo (c) `cas_invalido` em vez de ramo (d) `cas_ausente`. A **ordem inversa** falha igual: `"Segredo\nIndustrial".casefold()` também não casa `"segredo industrial"`. Logo não é eixo de ordem (D-ARQ-46 Parte 4 confirma "ambas as ordens passam os medidos"); é patologia de **grafia-ausente-multilinha**, não coberta por P3 nem P4.

**Por que não resolver agora.** Não-medida: `"Segredo Industrial"` foi medida (003.AN/AS) sempre como string única, nunca partida por `\n`. Resolver sobre hipótese viola D-ARQ-22 (anti-falsa-completude). Correção candidata quando/se medida: normalizar `\n→espaço` nas grafias textuais antes do casefold, ou casar `_GRAFIAS_CAS_AUSENTE` com whitespace colapsado.

**Status:** ABERTA. Não-bloqueante. Não é regressão (estado de hoje). Input para a fatia futura, se a patologia aparecer em FDS real.

---

### DT-003AX-01 — Virada tabelas→texto reabre o mecanismo de explosão multi-CAS e o papel do parse-PDF `[ABERTA — reconciliação dedicada]`

**Origem:** Sessão 003.AX (30/06/2026), medição read-only de `extract_text` sobre Ciplan/Tigre/Leinertex ao decidir a representação-de-entrada do transcritor (nota 003.AX em D-ARQ-42).

**Situação.** A entrada do LLM-transcritor passou a `extract_text` (recupera título-âncora e faixa que o `extract_tables` perde — patologia 2 era artefato). Mas o `extract_text` NÃO preserva o CAS multi-valor empilhado numa célula (`"2634-33-5\n55965-84-9"`): no texto, o bloco "Derivados de:" vem como header + sub-componentes em linhas separadas, cada CAS na sua linha, com a faixa do bloco em linha própria. Isso (a) tira o gatilho `\n`-célula do `_explodir_multi_cas` (D-ARQ-45, 003.AR) — o MECANISMO, não a DECISÃO de explodir 1→N com herança-α (que cruza D-ARQ-35 e permanece); e (b) questiona o `extrair_tabelas_fds` (003.AS, `extract_tables`) como camada-de-entrada do transcritor para grid fundido.

**O que a reconciliação exige.** Decidir texto-puro vs híbrido texto+tabelas; e, no caso escolhido, como a explosão 1→N e a herança-α se materializam sem o `\n`-célula, sem mover a decisão de cardinalidade para o LLM (D-ARQ-45 Parte 1 a proíbe). Medir a associação faixa↔componente no bloco "Derivados de:" em texto antes de cravar (anti-D-ARQ-22; a faixa não está colada ao CAS no texto linear).

**Andamento (003.AY) — RESOLVIDA.** Reconciliação fechada por medição read-only (`extract_text`/`extract_tables` dos 6 PDFs): (1) entrada do transcritor = TEXTO-PURO (`extract_text` âncora-por-título), não híbrido — híbrido sinalizado como paliativo (roteador por-FDS frágil + aposta na disjunção do acervo, classe D-ARQ-22/06); (2) a explosão multi-CAS migra de `\n`-split (`_explodir_multi_cas`, 003.AR) p/ expansão-de-grupo no resolvedor — a DECISÃO do D-ARQ-45 (explodir 1→N + herança-α, resolvedor-side, cardinalidade fora do LLM) permanece, só o mecanismo muda; (3) `extrair_tabelas_fds` (003.AS) deixa de ser a entrada do transcritor → candidato a DEPRECATED ou cross-check determinístico (IMPL decide). Detalhe e medição em DECISOES (nota de aplicação 003.AY em D-ARQ-42 + nota 003.AY em D-ARQ-45). Aberto p/ IMPL: forma do verbatim-grupo (`BlocoVerbatim` vs `ComponenteVerbatim`+`grupo_id`); destino de `_explodir_multi_cas`/`extrair_tabelas_fds`.

**Status:** RESOLVIDA (003.AY) — reconciliação decidida (texto-puro + expansão-de-grupo). IMPL pendente (forma do verbatim-grupo + resolvedor + destino do parse-tables), não-bloqueante.

---

### DT-003BV-01 — Formato de validade no topo do PGR: mês-ano, multi-candidata, sem `dd/mm/aaaa` `[DERIVADO — medição do topo Viverde, 003.BV]`

**Origem:** Sessão 003.BV (08/07/2026), medição do topo Viverde via `recortar_topo` (D-ARQ-53 P4).

**Situação.** O topo do PGR Viverde NÃO carrega data em `dd/mm/aaaa`. A validade (insumo de R-PGR-06) aparece em granularidade MÊS-ANO e em três candidatas empilhadas: "GOIÂNIA, FEVEREIRO 2023" (emissão original), "ATUALIZADO FEVEREIRO 2024", "ATUALIZADO FEVEREIRO 2025" (última atualização). A precisão de dia (03/02/25) existe só no nome do arquivo, fora do corpo transcrito. Consequência: o resolver `validade_texto→date` de D-ARQ-53 P3 não pode assumir `dd/mm/aaaa` nem candidata única — precisa (a) parsear mês-ano PT-BR ("FEVEREIRO 2025" → 2025-02), (b) escolher entre múltiplas candidatas por política "mais recente", (c) tolerar que a última atualização, não a emissão, conta para R-PGR-06. Erro de escolha flipa o gate eliminatório em silêncio (classe D-ARQ-22): hoje 08/07/2026, FEV/2025 (~17m) VÁLIDO vs. FEV/2023 (~41m) rejeita PGR válido — caso concreto que valida o insight pré-preenchimento+confirmação-RT de D-ARQ-53 P2.

**Pergunta de método (derivação normativa, D-ARQ-27; fonte: NR-01 vigente — validade/revisão do PGR):** quando o topo traz emissão + N atualizações em mês-ano, qual data conta para os 2 anos de R-PGR-06 — a última atualização (hipótese atual) ou a emissão original? E granularidade mês-ano conta o 1º dia do mês, o último, ou exige confirmação-RT do dia exato? Buscar o método, não o caso Viverde.

**Resolução parcial `[INTERPRETADO — prioridade na revisão de saída]`.** Até validar: última atualização = data de R-PGR-06; mês-ano resolve para o 1º dia do mês como default conservador, dia exato na confirmação-RT (molde D-ARQ-53 P2). Cravar sem a médica seria [INTERPRETADO] disfarçado de derivado — por isso o pré-preenchimento+confirmação-RT já é a topologia.

**Impacto:** insumo direto da fatia 3 de D-ARQ-53 (resolver + evidência-de-credencial). NÃO bloqueia a fatia 2 (`EnvelopeVerbatim` é texto-cru, não interpreta data). Achado irmão da mesma medição: assinatura-imagem → bool R-PGR-01 não text-derivable → 100% confirmação-RT (registrado no gabarito 003.BV; não vira DT própria por já estar coberto pela confirmação-RT de D-ARQ-53 P2).

**Medição 003.DT (topo Fascino, LLM ao vivo).** Rodada `ida` confirmou os dois eixos da DT em caso real de construção civil (Consciente SPE 0030). O topo traz 6 candidatas de validade, todas resolvem `data=None`: mm/aaaa ("06/2026","06/2027","11/2025") — não suportado por design (decisão D2), agora medido como formato REAL, não hipótese; e por extenso COM "de" ("15 de junho de 2026") — `_MES_ANO` exige `\s+` entre mês e ano ("Junho 2026" casa, "junho de 2026" não), LACUNA do próprio formato extenso que o resolver cobre. `proposta=None`: validade 100% delegada à confirmação-RT — coerente com a topologia, mas sem sinal de que o motor não propôs. Fix acionável do "de" (regex `(?:de\s+)?` opcional): próxima IMPLEMENTAÇÃO curta, exige teste falha-sem/passa-com. mm/aaaa permanece escopo deferido (D2) até decisão de política. Credencial RT (Título+CREA) transcrita e aprovada no `gate_forma_topo` — R-PGR-01 satisfeito por evidência text-derivable neste caso.

**Resolução 003.DU (faceta "de").** Fix implementado: `_MES_ANO` ganha `(?:de\s+)?` — "JUNHO DE 2026" resolve igual a "JUNHO 2026"; por tolerância a prefixo, "15 DE JUNHO DE 2026" também casa, resolvendo para o 1º dia do mês (dia é edição-RT, coerente com o default conservador — decisão de aceitar o drop do dia, DECISOES v144). Teste falha-sem/passa-com em `test_de_opcional_entre_mes_e_ano_resolve`. Commit `63edefe`, merge PR #250. Faceta mm/aaaa permanece deferida (D2) até decisão de política; a pergunta de método (última-atualização-vs-emissão, granularidade de dia) segue [INTERPRETADO].

**Status:** ABERTA. Não-bloqueante. Cruza D-ARQ-53 P3/P4. Faceta "de" FECHADA em 003.DU; mm/aaaa e método seguem abertos.

---

### DT-003CB-01 — `Quantificacao.valor` de ruído não discrimina NEN vs. SPL pontual/pico `[ABERTA — irmã de DT-002V-01]`

**Origem:** Sessão 003.CB (09/07/2026), CONHECIMENTO — derivação de R-RUIDO-01.

**Situação.** R-RUIDO-01 roteia a faixa (`abaixo_acao`/`entre_acao_LT`/`acima_LT`) comparando `Quantificacao.valor` (dB(A)) aos limiares 80/85. A classificação só é válida se o número for o **NEN** (nível de exposição normalizado p/ 8h). Mas `valor: Optional[float]` é anônimo — não garante que carrega o NEN e não uma leitura instantânea, pico, ou média simples. Enquanto `valor` vinha de fixture, a garantia era humana; com a extração de PGRs reais (D-ARQ-25) preenchendo `valor` via `parsear_quantificacao` (003.BZ), some a garantia: um laudo que reporte pico ou SPL pontual no campo faz R-RUIDO-01 rotear a faixa sobre o número errado e emitir/omitir audiometria demissional **sem sinal** — erro clínico silencioso (a classe que D-ARQ-22 combate).

**Espelho de DT-002V-01.** Idêntica em forma à do RX/CLSC: lá o campo não discrimina CLSC vs. média/pico; aqui não discrimina NEN vs. SPL. A premissa de fundo é a mesma: o motor **consome** a estatística pronta do laudo (NEN pela NHO-01), não a calcula — a médica lê o NEN da avaliação ambiental (NR-09), não refaz a dose. Confiança alta pela separação NR-07-consome/NR-09-produz, mas é premissa, não fato verificado.

**Pergunta de método (derivação normativa, D-ARQ-27; fontes: NHO-01 Fundacentro + NR-15 Anexo 1 vigentes):** quando o laudo traz uma métrica de ruído que não é o NEN — SPL pontual, pico, média simples — qual a conduta? Recusar e pedir NEN? Tratar como sem-avaliação-quantitativa (pendência)? Buscar o método, não o caso.

**Impacto até resolver:** a fatia 3 de D-ARQ-51 roteia sob a premissa "`valor` é NEN quando há avaliação quantitativa de ruído"; a borda 80/85 fica `[INTERPRETADO]` quanto à estatística de entrada, não quanto ao limiar (o limiar é `[DERIVADO]`). Candidato de fechamento: campo discriminador de estatística (comum a CLSC e NEN) com regra consumidora, ou sinalização na extração (D-ARQ-25 → Pendencia).

**Status:** ABERTA. Não-bloqueante. Cruza R-RUIDO-01, D-ARQ-51 fatia 3, DT-002V-01.

---

### DT-003CI-01 — Carcinógeno-via-frase-H: H350/H351 é GHS, não IARC — bypass próprio deferido `[ABERTA — deferida por D-ARQ-55]`

**Origem:** Sessão 003.CI (10/07/2026), 2ª passada crítica sobre o mapa frase-H→flag de D-ARQ-55.

**Situação.** O recorte (B) mapeia as frases-H de sensibilização ({H334, H317} → `is_sensibilizante`). O análogo carcinógeno seria {H350 (pode causar câncer), H351 (suspeito de causar câncer)} → carcinógeno. Mas a flag existente é `is_carcinogeno_iarc` — proveniência **IARC**. H350/H351 é carcinogenicidade **GHS/CLP** (autoclassificação do fabricante / CLP), sistema distinto do IARC: sobrepõem-se muito, mas um H351 pode existir para substância que a IARC não avaliou. Popular `is_carcinogeno_iarc` a partir do H-code lavaria proveniência GHS como IARC — erro-silencioso da classe D-ARQ-22.

**Decisão de deferimento (D-ARQ-55, ratificada pelo Diovanni).** Recorte B NÃO mapeia carcinógeno-via-frase-H. O H350/H351 bem-formado é transcrito e carregado cru em `Componente.frases_h` (não perdido — anti-supressão), sem virar flag nesta fatia. O carcinógeno já tem caminho vivo por outra via: `is_carcinogeno_iarc` vocab/slug-sourced (agentes.yaml/gate-CAS) + R-PKG-BZ por identidade de agente (benzeno). Não há furo urgente — os casos-âncora do cluster são sensibilização.

**O que a resolução exige (sessão própria).** Flag NOVA `is_carcinogeno_ghs` (proveniência GHS, distinta de `is_carcinogeno_iarc`), apendada à lista de bypass de `materialidade()` (cl.5 D-ARQ-33, append-only) + mapa {H350, H351} → `is_carcinogeno_ghs` no resolver-side + cobertura de teste. Decidir se a revisão de saída reconcilia GHS↔IARC por agente (D-ARQ-27). `[INTERPRETADO — prioridade na revisão de saída]` na articulação "H350 GHS dispara bypass sem confirmação IARC".

**Status:** ABERTA. Não-bloqueante. Deferida por design de D-ARQ-55; append-only sobre o bypass. Irmã da sensibilização do recorte B.

### DT-003CK-01 — Promoção de Risco sem slug (bypass com CAS oculto) `[ABERTA — condicionada a regra clínica]`

**Origem:** Sessão 003.CK (10/07/2026), decisão P3(a) de D-ARQ-56.

**Situação.** Com D-ARQ-56, o bypass declarado na FDS com CAS oculto é honrado (`materialidade()` → MATERIAL) e visível (`bypass_sem_slug` bloqueante nomeando as frases-H), mas o componente NÃO é promovido a `Risco`: `Risco.agente: str` rejeita `None`, e promover exigiria (i) `Optional[str]` propagado por consolidação/emissão/regras sem consumidor clínico, ou (ii) slug inventado (D-ARQ-22). Custo declarado: exame NÃO dispara para sensibilizante de CAS oculto — o sistema entrega visibilidade (MATERIAL + pendência bloqueante), não conduta.

**O que a resolução exige.** Regra clínica formalizada de conduta para sensibilizante-sem-agente (qual exame/periodicidade um "sensibilizante genérico" dispara — método pela literatura oficial vigente, D-ARQ-27), ANTES de qualquer mudança no contrato de `Risco`. Sem a regra, promover é forma sem função.

**Status:** ABERTA. Não-bloqueante (a pendência bloqueante `bypass_sem_slug` já impede saída silenciosa).

### DT-003CM-01 — Mapa de cabeçalhos de bloco GHE multi-PGR: âncora `SETOR/FUNÇÃO` cobre 1 de 15 `[FECHADA — 003.CQ, 1ª leva de D-ARQ-57 completa]`

**Origem:** Sessão 003.CM (11/07/2026), medição da generalização da âncora de recorte (requisito (b) da 003.BS; medição prevista na NOTA 003.BM sobre a amostra de DT-003L-01). Varredura read-only dos 15 PGRs do acervo via pdfplumber (mesmo extrator de `extrair_texto_pgr`); Ricco Hetrin, Ricco Serra Dourada e Seconci REV3 por censo pypdf `[MEDIDO com pypdf — forma de linha a confirmar com pdfplumber se virarem caso-âncora]`.

**Situação.** A âncora atual do recorte (`linha.startswith("SETOR/FUNÇÃO")`, verbatim, `extracao_pgr.py`) casa em **1 de 15 PGRs** (Viverde, 42×). Não existe âncora única multi-PGR — o acervo (só construção civil) usa pelo menos 5 formas de cabeçalho de bloco:

1. **`GHE NN` seco + sub-linha `SETOR/FUNÇÃO ...`** (Viverde) — 31 cabeçalhos `GHE NN` no inventário.
2. **`GHE NN - TÍTULO`** (Vistamérica 50×, CMO Ver.02 14×, Seconci REV3/REV4 18×, TPB Andrade 1×, AURO 19×) — a forma mais frequente, 6 PGRs.
3. **`INVENTÁRIO DE RISCO GHE NN`** (ALT T65 16×, EURO Setor C 19×) — "GHE" NÃO inicia a linha; âncora por startswith de "GHE" falharia.
4. **`GHE: NN - TÍTULO`** (R78 Naturia) — variante com dois-pontos; doc é "PARTE 2", começa no meio do GHE 07 (sem topo — caso de doc parcial).
5. **Sem GHE — bloco por cargo** (`CARGO/FUNÇÃO: ...` Ricco-Adm; `CARGO X - CBO: NNNN` Cjr; Hetrin e Serra Dourada idem por censo) — 4 PGRs; forma 6 de DT-003L-01. Recorte por GHE inaplicável; unidade de bloco = cargo.

Floramazônia (forma 2 de DT-003L-01 — carta pedindo FDS) não tem inventário; traz índice `GHE NN - Título` em prosa de resposta — armadilha de falso positivo em nível de documento.

**Achados críticos.**

- **Caso-Vistamérica (classe D-ARQ-22):** a âncora atual ocorre exatamente 1× no Vistamérica (pág. 36 de 173, 1-based) → `recortar_blocos_ghe` produziria 1 "bloco" de ~137 páginas, lixo silencioso — 1 âncora não dispara a falha explícita de zero âncoras. Mesma consultoria (CMO) ≠ mesmo template.
- **Viverde conflaciona 2 seções:** inventário por-GHE (31 cabeçalhos `GHE NN`, págs. 34–123) + quadro por-atividade `PROCESSO/SUBPROCESSO/ATIVIDADES` (págs. 131–147, com `SETOR/FUNÇÃO`, SEM linha GHE). Das 42 âncoras atuais, 17 estão no quadro por-atividade; os 32 GHEs canônicos do MAPA vêm desse re-agrupamento. (Páginas 1-based; a NOTA 003.BM reportou 1ª pág. 33 / última 146 em contagem 0-based — mesmo achado, 42 blocos.)
- **Discriminador candidato (medido, não decidido):** `^(INVENTÁRIO DE RISCO )?GHE:? \d+( - TÍTULO)?$` em linha curta separa cabeçalho de prosa em 10/12 docs pdfplumber — exclui corretamente campos internos ("Quantidade de Funcionários expostos neste GHE: 08") e prosa ("Fisioterapia do GHE 17 para GHE 11"). Armadilhas restantes: índice do Floramazônia e a 2ª seção do Viverde.

**Impacto na arquitetura (input para o D-ARQ do req. (b), sessão própria).** Âncora única verbatim não generaliza nem intra-setor. A generalização é um **localizador de blocos** com repertório de formas medidas + **gate estrutural** ("0 ou 1 bloco achado em doc >N págs → pendência bloqueante") para matar o caso-Vistamérica silencioso. Família cargo-based é fronteira de escopo (unidade cargo, não GHE), não variação de âncora. Multi-setor (química, saúde) segue não-medido — extensão futura via fontes públicas/sintéticos rotulados (lembrete 06/07/2026).

**Nota (003.CN) — consumida por D-ARQ-57.** A sessão ARQUITETURA do req. (b) fechou o localizador de blocos como **D-ARQ-57**: repertório determinístico de reconhecedores GHE (discriminador `^(INVENTÁRIO DE RISCO )?GHE:? \d+( - título)?$`, formas 1–4) substituindo a âncora `SETOR/FUNÇÃO` verbatim; gate de segmentação densidade+contagem (mata o caso-Vistamérica que a falha de zero-âncoras não pega); família cargo-based (forma 5) reconhecida e sinalizada (`pgr_cargo_based` bloqueante), recorte-por-cargo diferido. DT permanece **ABERTA** até a IMPL do localizador (D-ARQ-57 a consome, não a fecha).

**Nota (003.CO) — forma 1 refinada.** O Viverde contém também `"GHE NN-"` (traço colado ao número, ex. `"GHE 01- Engenharia planejamento de obra"`), medido no PDF real durante a IMPLEMENTAÇÃO da fatia 1 de D-ARQ-57. O reconhecedor tolera espaçamento variável no traço (`\s*-\s*`). Fatia 1 de D-ARQ-57 implementada (PR #198); DT segue **ABERTA** (fatias 2–3, gate de segmentação e família cargo-based).

**Nota (003.CP) — calibração do gate medida sobre o acervo.** Medição direta dos 15 PGRs com a lógica exata de `eh_cabecalho_ghe` @ HEAD (pdfplumber; Hetrin, Serra Dourada e Seconci REV3/REV4 por pypdf — mesma ressalva de forma-de-linha do censo original): legítimos GHE-based param em 34,8% de densidade máxima (ALT T65); implausíveis começam em 44,4% (TPB). Limiares ratificados: X=40%, N=10. Divergência registrada: Seconci REV3/REV4 medem 15/16 blocos via pypdf vs "18×" do censo 003.CM `[MEDIDO com pypdf — forma de linha a confirmar com pdfplumber se virar caso-âncora]`. Fatia 2 de D-ARQ-57 implementada (PR #200); DT segue **ABERTA** (falta fatia 3 — família cargo-based).

**Nota (003.CQ) — peça 3 implementada; DT FECHADA.** Condição de fechamento ("IMPL do localizador", nota 003.CN) cumprida: 1ª leva de D-ARQ-57 completa (peças 1-2-3, PRs #198/#200/#202). Medição 003.CQ resolve o caveat pypdf de Hetrin/Serra Dourada (forma de linha confirmada por amostra pdfplumber: substring "GHE" só em prosa, zero âncoras possíveis; sinal-cargo = grid-header AIHA `Função ... Perigo / Risco`, corrigindo o "idem" do censo 003.CM — lá `CARGO/FUNÇÃO:` era boilerplate de assinatura, não cabeçalho de bloco). Resíduos que NÃO reabrem a DT: recorte-por-cargo (fatia futura própria, D-ARQ-57); medição multi-setor (química/saúde); DT-003L-01 forma 6 segue ABERTA.

**Status:** FECHADA (003.CQ). Insumo obrigatório da sessão ARQUITETURA do requisito (b) da 003.BS — consumida por D-ARQ-57 (003.CN); IMPLEMENTAÇÃO completa em 003.CQ (1ª leva 3/3, PR #202).

### DT-003DB-01 — Anatomia do bloco-cargo: a família cargo-based parte em N:1 (grupo-GHE) vs 1:1 (card-por-cargo); ambas reduzem a `GHEPGR` `[DERIVADO — medição de 4 witnesses, 003.DB]`

**Origem:** Sessão 003.DB (16-17/07/2026), CONHECIMENTO/medição. Pré-requisito duro nomeado por D-ARQ-57 peça 4 e DT-003CS-01 critério (2)/(3): medir a anatomia do bloco-cargo antes de arquitetar o recorte-por-cargo. Medição read-only (pdfplumber host) dos 4 witnesses trackeados em `matrizes_originais/`: Ricco-Adm (`PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf`), Cjr (`pgr_Cjr Engenharia Ltda (M Construtora).pdf`), UFGD-v7 (`PGR_EBSERH_UFGD_v7.pdf`) e HUMAP (`PGR_EBSERH_HUMAP.pdf`).

**Situação — a "família cargo-based" (D-ARQ-57 peça 3) NÃO é homogênea.** Parte em duas anatomias de cardinalidade cargo↔tabela-de-risco:

- **N:1 — grupo-de-cargos (GHE com header diferente).** Ricco-Adm: bloco = `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` (2 blocos medidos), a linha `CARGO/FUNÇÃO:` lista N cargos slash-separated, e 1 `INVENTÁRIO DOS RISCOS OCUPACIONAIS DO SETOR EM FUNÇÃO DO GHE` é compartilhado por todos. Estruturalmente é um GHE — o header é o único ponto que difere do repertório peça 1.
- **1:1 — card-por-cargo.** Cjr (Sistema ESO, `CARGO <nome> - CBO: NNNN`, 1 cargo no doc, inventário por-categoria sufixado com o cargo — `INVENTÁRIO DE RISCOS <categoria> - <CARGO>`); UFGD-v7 (`Lotação: Escala de Trabalho: Qtde:`, 105 cards, tabela `RISCOS AMBIENTAIS` de 5 categorias embutida — FÍSICO/QUÍMICO/BIOLÓGICO/ERGONOMICO/ACIDENTES em linhas); HUMAP (`Lotação: EscaladeTrabalho: Qtd:`, 140 cards, idem, whitespace colado). Cada cargo carrega o próprio inventário.

**Achado estrutural (input direto da ARQUITETURA da peça 4).** Ambas as anatomias reduzem ao `GHEPGR` existente: o 1:1 é um GHE degenerado (`cargos=[1 cargo]`, riscos próprios); o N:1 é um GHE normal (`cargos=[N]`, riscos compartilhados). A hidratação `GHEVerbatim→GHEPGR` (D-ARQ-51) já suporta os dois. **Consequência: o "recorte-por-cargo" NÃO é uma 2ª unidade de bloco (tipo novo) — é (a) um novo conjunto de reconhecedores de RECORTE por-cargo (1:1) + binding da tabela de risco POR POSIÇÃO dentro do bloco, e (b) possível extensão do repertório GHE (peça 1) com `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` para o N:1.** O tipo de dado a jusante é reusado; o maquinário de recorte+binding é novo — não é "de graça".

**Gabarito isolado medido:**

| witness | setor | âncora de bloco | cardinalidade | nº blocos | tabela de risco |
|---|---|---|---|---|---|
| Ricco-Adm | construção (MGE) | `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` | N:1 | 2 | `INVENTÁRIO DOS RISCOS ... EM FUNÇÃO DO GHE` (compartilhada) |
| Cjr | construção (Sistema ESO) | `CARGO <nome> - CBO: NNNN` | 1:1 | 1 | `INVENTÁRIO DE RISCOS <cat> - <CARGO>` (por-categoria) |
| UFGD-v7 | saúde EBSERH | `Lotação: Escala de Trabalho: Qtde:` | 1:1 | 105 | `RISCOS AMBIENTAIS` (5-cat embutida) |
| HUMAP | saúde EBSERH | `Lotação: EscaladeTrabalho: Qtd:` | 1:1 | 140 | `RISCOS AMBIENTAIS` (idem, colado) |

Contagens cruzadas com 003.CZ/DA: UFGD 105 / HUMAP 140 batem exato o reconhecedor-Lotação.

**Caveats de medição (para a IMPL não tropeçar):**
1. **Recorte prende a tabela por posição, não por contagem global.** `RISCOS AMBIENTAIS` sobreconta no texto plano (UFGD 122>105; HUMAP 159>140) — a tabela do card é a que segue a âncora DENTRO do bloco, não a N-ésima do documento. Naive-count = subsegmentação silenciosa (classe D-ARQ-22).
2. **Título numerado EBSERH `NN.N <Cargo>` NÃO serve de âncora de recorte** (UFGD 134 títulos > 105 cards — pega subsseções de recomendação tipo `13.5.1 Mobiliário`). A âncora confiável é a `Lotação:`-tripla (já no repertório peça 3, 003.DA).
3. **Cargo-nome em local variável** entre os 1:1: título numerado (UFGD `13.1 Advogado`) vs valor da Lotação (`SetorJurídico: ADVOGADO`, HUMAP) vs linha CBO (Cjr) vs slash-list (Ricco-Adm N:1). Concern da transcrição-LLM do bloco-cargo, não do recorte.

**Fork para a ARQUITETURA (003.DC — não decidido em medição).** Ricco-Adm (N:1) roteia por (i) extensão de âncora GHE (peça 1) — `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` vira reconhecedor GHE, doc processa como GHE normal, NÃO `pgr_cargo_based`; ou (ii) caminho cargo. A medição aponta (i) — GHE-shaped. 003.CQ excluiu esse header do repertório GHE "por redundância como sinal de família"; reabri-lo como âncora de RECORTE é decisão de arquitetura, com risco não-medido (header como ruído em doc GHE-based). Se (i), o recorte-por-cargo genuíno restringe-se aos 1:1 (Cjr + EBSERH).

**Nota (003.DC) — fork resolvido rota (i).** A ARQUITETURA da peça 4 (D-ARQ-57 andamento 003.DC) resolveu o fork: Ricco-Adm N:1 vai por **extensão de âncora GHE (peça 1)** — `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` entra em `_RECONHECEDORES_GHE`, doc ingere como GHE normal (R-GHE-01 [VALIDADO]: N cargos compartilham 1 inventário → matriz idêntica). Rota (ii) rejeitada (exigiria binding 1-tabela:N-cargos sem ganho clínico). Recorte-por-cargo genuíno restringe-se aos **1:1** (Cjr + EBSERH), via `recortar_cards_cargo` + `_RECORTADORES_CARGO`. DT segue ABERTA (fecha na IMPL da peça 4, fatias 4a-4d — DT-003CS-01/EBSERH em 4d). `[ARQUITETURA — 003.DC]`

**Nota (003.DD) — forma documentada é a VISUAL; o verbatim extraído perde um til.** A fatia 4a (IMPLEMENTAÇÃO, PR #222) mediu o texto real extraído por pdfplumber sobre `PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf`: a 1ª palavra do header sai `INFORMAÇOES` (Õ→O, perda de diacrítico específica de fonte/glifo, codepoint `0x4f` confirmado por `hex(ord(c))` — o mesmo `Õ` em `FUNÇÕES`, mais adiante na mesma linha, extrai correto, `0xd5`). A forma `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` citada acima e em DT-003DB-01 é a forma VISUAL (como o documento aparenta ao olho humano/leitor de PDF), não o verbatim do parser. O reconhecedor da forma 5 (`_reconhece_cabecalho_informacoes_cargos_funcoes`) cobre as duas via classe `[OÕ]`, sem normalização NFC/NFD (convenção VERBATIM da peça 1 preservada). `[IMPLEMENTADO — 003.DD; PR #222]`

**Status:** ABERTA (medição entregue; consumida pela ARQUITETURA da peça 4 de D-ARQ-57, na 003.DC). Não bloqueia. Cruza DT-003CS-01 (EBSERH/saúde), DT-003L-01 forma 6, D-ARQ-57 peça 4. Nenhuma R-* tocada.

### DT-003DV-01 — Resolução de sílica no vocabulário: falso negativo (termos reais do acervo ausentes) e falso positivo potencial (fuzzy 'Silício'→'silica') `[FECHADA — facetas A (003.DW) e B (003.DY)]`

Medição (Fascino, 19 GHEs, commit `1980a00`, relatório `relatorios/003dv_fascino_rodar.md`, gitignored): 232 pendências `vocabulario_ausente`, 33 `predicado_ausente`, 4 `resolucao_fuzzy`; nenhum outro tipo emitido.

**Faceta A (falso negativo).** 'Sílica livre', 'Quartzo' e 'Poeira respirável' não resolvem no vocabulário de agentes (pendências `vocabulario_ausente` recorrentes; ausência confirmada por grep em `agente_medico/protocolo/`). Consequência medida: a família R-RX-01* acionou em exatamente 1 dos 19 GHEs (GHE-17). Em PGR de construção civil com sílica declarada em texto, a família de regras mais sensível do protocolo fica silenciada por lacuna de termo — classe D-ARQ-22 (erro silencioso).

**Faceta B (falso positivo potencial).** O único acionamento de R-RX-01* veio da resolução fuzzy 'Silício'→'silica' (GHE-17, Serralheiro). Silício metálico/liga não é sílica cristalina; par suspeito da mesma classe do `TCE` proibido (escolha silenciosa). Revisão do par no raio fuzzy pendente.

**Fechamento exige decisão de dado**, não só de motor: popular `termos:` segue o critério de grafia normativa com fonte (lição 003.DM) — não entra junto com esta DT.

**Observação de instrumento (não-DT) — REFUTADA por medição (003.ED).** Esta observação dizia que a pendência global do relatório não carrega o GHE de origem, exigindo cruzamento manual com o PDF. Medido em 003.ED: o relatório de `rodar-offline` TEM identidade por GHE — cada seção `### GHE` carrega sua própria lista de pendências e tabela de exames. A limitação era presumida, não medida; procedência corrigida aqui em vez de apagada (D-ARQ-06/registro de erro).

**Status faceta A: RESOLVIDA (003.DW).** `silica.termos` populado com 6 grafias de sílica cristalina livre — "Sílica livre", "Sílica livre cristalizada", "Sílica livre cristalina", "Quartzo", "Cristobalita", "Tridimita" → slug `silica`, EXATA. Fonte: NR-15 Anexo 12 ("Sílica Livre Cristalizada": quartzo/cristobalita/tridimita) + NR-07 Anexo III Quadro 1; CAS 14808-60-7. Estende o critério Tier 1 (D-ARQ-50 P2) de "grafia do Anexo I" para fonte-por-natureza-do-agente (poeira-mineral/RX não tem biomonitoramento). Índice 99→105, slugs 79 inalterado, sem colisão; teste `test_termos_silica_resolvem_exata`. Commit `8363fcb`, PR #253. Literal "cristalizada" vs "cristalina" `[INCERTO — confirmar texto oficial MTE]`.

**Achado 003.DW — família não-sílica (anti-FP D-ARQ-22).** O relatório Fascino expôs além dos 3 termos da faceta A: silicatos (tricálcico/dicálcico/alumínio/zircônio), poeira respirável, poeira de madeira. NÃO resolvem para `silica` — seriam falso-positivo de silicose (mesma classe do `Silício`); seguem `vocabulario_ausente` (pendência honesta), cravado em `test_termos_silicato_e_poeira_nao_resolvem_para_silica`. Fila de enriquecimento (não-DT): silicatos → candidatos a slug próprio/PNOS; **`poeira respirável` precisa do diff da matriz humana no Marco 1** para decidir fração-de-sílica-declarada vs PNOS — não cravado sem o gabarito.

**Status faceta B: RESOLVIDA (003.DY, D-ARQ-64).** Ramo FUZZY passou a ser opt-in por allowlist de dado: `fuzzy_permitido: true` em 18 slugs de cauda de `agentes.yaml`; `silica` fora da allowlist. 'Silício'/'Silicio' → `NAO_RESOLVIDO` + pendência `fuzzy_recusado` (não-bloqueante, destinatário extração) nomeando o termo, `silica` e a distância 2 — cravado em `test_silicio_recusa_fuzzy_para_silica`. O veto é do resultado eleito, nunca filtro de candidato (caso-âncora metanoll/metanol/etanol em D-ARQ-64 cl. 3); a cauda legítima sobrevive ('Microrganismo'→`microrganismos` FUZZY). Sincronia allowlist × canais de criticidade é teste computado do dado (`test_allowlist_disjunta_dos_canais_de_criticidade`). Suíte 945→949. Detalhe e medição completa (105/79 · 4 pares · 94=77+17 · 61+18=79) em D-ARQ-64.

**(DT-003DV-01 FECHADA — facetas A (003.DW) e B (003.DY) resolvidas.)**

### DT-003EB-01 — Pacote-base incondicional da matriz humana sem conceito correspondente no motor `[REENQUADRADA — 003.EC, não fechada]`

**Origem:** Sessão 003.EB (25/07/2026), diff da rodada `rodar-offline` (Fascino, D-ARQ-65) contra a matriz humana `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` (validada Dra. Carolini) — Marco 1.

**Situação original (003.EB).** A matriz humana aplicaria um pacote-base incondicional de **10 exames em 19/19 GHEs do Fascino**, inclusive no setor sem risco ocupacional específico. Medido: **~190 de ~194 células** do diff sem conceito correspondente no motor — a maior massa isolada do diff.

**Reenquadramento (003.EC) — premissa REFUTADA por medição do próprio gabarito.** Contagem direta contra `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` mostra que "pacote-base de 10 exames em 19/19 GHEs" não é o que o gabarito contém:

- **Medido:** apenas **4 exames em 19/19 GHEs** (Exame Clínico, Audiometria, Avaliação Psicossocial, Av. Médica de Saúde Mental); Acuidade Visual 17/19; Hemograma/Glicemia/ECG 16/19; Espirometria/RX Tórax OIT 16/19.
- Células distintas somam **~177, não ~194**.
- **GHE-06 (Administração) recebe 4 exames** e **GHE-19 (Vendas) recebe 5** — o oposto de "inclusive o setor sem risco recebe o pacote".

**O gap decompõe em 4 classes** (não uma massa homogênea):
1. Regras `[VALIDADO]` órfãs de `regras.yaml` (existiam no protocolo, nunca materializadas).
2. Lacuna de vocabulário ('Poeira respirável', 'Poeira de madeira', 'Poeiras Respiráveis/Metálicas', 'Trabalho em Altura').
3. Divergência de periodicidade contra regra já existente (ver DT-003EC-01).
4. Conceito genuinamente ausente — só esta classe exige sessão CONHECIMENTO.

**003.EC fecha a maior fatia da classe (1)** — R-CLI-01 materializado (D-ARQ-66).

**Resíduo (então) ABERTO = classe (4).** `Av. Médica de Saúde Mental` não existe em nenhuma regra do protocolo. A Avaliação Psicossocial aparece **incondicional** no gabarito, contra R-PSY-01 `[VALIDADO]` **condicionada** — mesmo arco de NR-1 psicossocial da entrevista original. **NÃO formalizar sobre n=1**: supersedir uma regra `[VALIDADO]` com base em um único PGR de uma empresa reprova em D-ARQ-06 (universalidade). Gatilho de formalização = **2º PGR atualizado no acervo**, não este.

**Classe (4) FECHADA (003.EN).** Gatilho satisfeito e medido: 2º grupo de PGRs atualizados no acervo (6 documentos posteriores a 26/05/2026, 5 clientes distintos, 2 médicas distintas) mostra Avaliação Psicossocial e Av. Médica de Saúde Mental em 99% de 284 cargos, contra ~0% em 13 documentos anteriores — não é mais n=1. **R-PSY-02** materializada (§5.7) sucede R-PSY-01 (agora `[DEPRECATED]`), incondicional via `todo_trabalhador`. Classes (2) (lacuna de vocabulário — 'Poeira respirável'/'Poeira de madeira'/'Trabalho em Altura' residuais) e (3) (divergência de periodicidade, DT-003EC-01) seguem ABERTAS — DT-003EB-01 não fecha por inteiro nesta sessão.

**Ressalva sobre a qualidade do gabarito.** O documento carrega anotações de rascunho no próprio corpo (ex.: "veja com a Segurança, acho que é betoneira"; "Incluir no WORD do PCMSI idade maior ou igual 18 anos") — "validada Dra. Carolini" merece qualificação antes de servir de gabarito de regressão (D-ARQ-18): confirmar com a Dra. Carolini se as anotações de rascunho compõem a matriz validada ou são resíduo de edição.

**Correção factual ao relatório 003.EB.** RX 60m ocorre em **GHE-08 (Carpintaria) E GHE-09 (Armação)**, não só GHE-09 — corrige o texto de 003.EB.

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura, classe 4):** `Av. Médica de Saúde Mental` é conceito próprio, distinto de Avaliação Psicossocial, ou duplicidade de rótulo? A Avaliação Psicossocial incondicional é conduta atualizada da matriz, ou anotação de rascunho não-validada?

**Status:** REENQUADRADA, não fechada. Resíduo (classe 4) exige sessão CONHECIMENTO com gate D-ARQ-63 e 2º PGR no acervo antes de tocar R-PSY-01 ou criar regra nova.

**Nota (003.ED).** Classe (2) perdeu a maior fatia: o alias de altura fechou 16 GHEs × 5
exames = 80 células, com cruzamento nominal contra o gabarito sem falso positivo nem falso
negativo. Classe (4) inalterada. Achado novo a medir: **GHE-19 (Vendas) tem `ctx.riscos == []`**
— o gabarito pede Acuidade Visual ali e o motor não tem nada a emitir. Falta distinguir
"o PGR não declara risco para Vendas" de "declara e nada resolveu": a primeira leitura manda
a acuidade para classe (4) (conceito ausente, n=1, não formalizar); a segunda, para classe (2)
(lacuna de vocabulário). `[A MEDIR — não concluir sem medir]`

### DT-003EB-02 — R-BIO-04 emite indicador biológico onde a matriz humana pede só menção documental em risco baixo `[ABERTA — 003.EB]`

**Origem:** Sessão 003.EB (25/07/2026), mesmo diff acima.

**Situação.** Sob anotação explícita de risco baixo no PGR, a matriz humana solicita apenas **menção documental no PCMSO**, não o indicador biológico em si. R-BIO-04 emitiu 4 indicadores biológicos nesses GHEs do Fascino (GHE-10: acetona_urina, mek_urina; GHE-16: ortocresol_urina, acido_metilhipurico — todos PER 6m).

**Hipótese:** falta um gate de nível de risco no predicado de R-BIO-04 (risco baixo → menção documental, não exame).

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura):** o que caracteriza "risco baixo" para fins de dispensa do indicador biológico — a anotação explícita no PGR é suficiente, ou há um limiar quantitativo por trás? A menção documental tem forma própria (texto padrão no PCMSO) ou é livre?

**Status:** ABERTA. Formalização exige sessão CONHECIMENTO com gate D-ARQ-63 antes de alterar R-BIO-04.

### DT-003EC-01 — Matriz humana emite RX Tórax OIT 12M onde R-RX-01 sem-medição prescreve 24M `[ABERTA — 003.EC, não-bloqueante]`

**Origem:** Sessão 003.EC (26/07/2026), medição do gabarito `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` (Fascino) contra R-RX-01/faixas de PNOS.

**Situação.** O gabarito dá RX Tórax OIT em **12M em 14 GHEs** e **60M em GHE-08 (poeira de madeira)** e **GHE-09 (poeiras respiráveis/metálicas)**. O 60M casa com PNOS/Quadro 2 (faixa "sem avaliação quantitativa" → 60M, já implementada). O **12M NÃO casa com R-RX-01**: 12M é a faixa >100% LEO do Quadro 1 (sílica/asbesto), e "sem avaliação quantitativa" prescreve **24M** `[DERIVADO — NR-7 Anexo III Quadro 1]` — não 12M. O PGR não traz quantificação para esses GHEs.

**Pergunta de método (derivação normativa, D-ARQ-27):** a conduta de 12M no gabarito corresponde a uma leitura de exposição >100% LEO feita por fora do PGR escrito (ex.: conhecimento de campo da Dra. Carolini sobre o canteiro), ou a um critério distinto do Quadro 1 que o protocolo ainda não capturou? Buscar o **método** por trás da conduta, não só resolver os 14 GHEs do caso.

**Resolve de passagem** o pré-registro de DT-003DV-01 (achado 003.DW): 'Poeira respirável' é tratada como **sílica-like** no gabarito (RX 12M/24M, não faixa PNOS), **NÃO como PNOS** — confirma a suspeita registrada em 003.DW sem fechar a lacuna de vocabulário (classe 2 de DT-003EB-01).

**Nota (003.EH)** — a divergência saiu de hipótese para medida. Com o ramo de ausência destravado, o motor emite 24M em 14 GHEs exatamente onde o gabarito dá 12M — os mesmos 14 (GHE-01–05, 07, 10–13, 15–18). A pergunta de método é idêntica, mas agora com contraparte medida dos dois lados, não com um lado vazio. Mantida a norma (24M): supersedir regra derivada de texto literal sobre n=1 empresa reprova em D-ARQ-06 — o gatilho de reabertura segue sendo o 2º PGR atualizado no acervo. Os outros 2 GHEs com RX no gabarito (GHE-08 poeira de madeira, GHE-09 poeiras respiráveis/metálicas, ambos 60M) seguem sem emitir por lacuna de vocabulário — `poeira_nao_classificada` e `fumos_metalicos` não têm chave `termos:` em `agentes.yaml` `[VERIFICADO — 003.EH]`. Classe (2) de DT-003EB-01; sessão de dado própria, com critério de grafia normativa por fonte.

**Correção 003.EJ (não apagar a nota 003.EH acima — D-ARQ-06, registro de erro).** A nota de 003.EH atribui a ausência de RX em GHE-08 e GHE-09 a "lacuna de vocabulário". Medido e derivado em 003.EJ, o diagnóstico é outro: **GHE-08** declara `Poeira de madeira` — agente identificável que não é sílica/asbesto/carvão (fora do Quadro 1, literal) e cujo enquadramento no Quadro 2 depende do rodapé (não sensibilizante, baixa toxicidade); **GHE-09** declara `Poeiras Respiráveis/Metálicas`, fração + categoria sem substância → R-PGR-05. Em nenhum dos dois a ausência de RX é lacuna de vocabulário. Ver DT-003EJ-01 (GHE-08) e a nota de aplicação 003.EJ em R-PGR-05 (GHE-09).

**Status:** ABERTA. Não-bloqueante — nenhuma regra alterada por esta DT; questão de método para sessão CONHECIMENTO futura.

### DT-003DX-01 — Migrar acreção pós-decisão para satélites `docs/darq/` `[ABERTA — higiene de doc]`

D-ARQ-63 (003.DX) mediu 49% do DECISOES_ARQUITETURAIS.md como diário — acreção pós-decisão
(`Changelog`, `Nota de implementação`, `Aplicação na sessão`, `Andamento`, 39% do corpo,
177.214 chars) somada à tabela de revisões (16%, 87.328 chars). O gate de dois níveis
(D-ARQ-63) contorna o custo de leitura; não resolve a causa. Três frentes, nenhuma
pré-requisito da outra: (a) mover a acreção de cada D-ARQ para um satélite
`docs/darq/D-ARQ-NN.md` com ponteiro no bloco original; (b) D-ARQ-57 é 13,2% do corpo
sozinho (59.755 chars, 51.818 de acreção) — candidato à primeira migração, maior retorno
isolado; (c) a tabela de revisões (87.328 chars, 100% diário) como arquivo próprio,
`docs/HISTORICO_REVISOES_DARQ.md` ou equivalente. Reduziria o corpo-decisão de ~453 mil
para ~276 mil chars. Não-bloqueante — a leitura via `INDICE_DARQ.md` + gate de dois níveis
já cabe em contexto sem esta migração.

---

### DH-003EC-01 — `scripts/medir_painel.py` reporta verde sobre vermelho, conta prosa como implementação e não vigia derivados `[PARCIALMENTE RESOLVIDA — 003.EF; faceta (b) ABERTA]`

**Origem:** re-tiragem do painel na sessão 003.EC (26/07/2026), pós-merge do PR #263. Três facetas medidas, em ordem de gravidade.

**(a) Cegueira a falha.** `medir_suite()` casa apenas `(\d+) passed(?:, (\d+) skipped)?` sobre o stdout do pytest e nunca lê `resultado.returncode`. Suíte vermelha é reportada como o número de verdes, sem sinal algum. Caso real desta sessão: a tiragem devolveu "966 passed, 6 skipped" com `tests/test_gerar_indice_darq.py::test_indice_em_disco_nao_divergiu` quebrado — 973 coletados − 966 passed − 6 skipped = 1 teste engolido pelo parser. É a classe de erro silencioso plausível de D-ARQ-22 dentro do próprio artefato de gestão à vista: o número que existe para dar visibilidade é cego ao estado que mais importa. Correção candidata: checar `returncode` e levantar quando ≠ 0; capturar `failed`/`error` no regex.

**(b) ID citado conta como ID implementado.** `medir_cobertura_clinica()` casa `R-[A-Z]+-[0-9]+` em qualquer string de `regras.yaml`, inclusive prosa de `base_normativa`. R-TEMP-01 entrou no numerador em 003.EC por ser citado na `base_normativa` de R-CLI-01. Contradiz o critério que a reconciliação 003.DE aplicou ao excluir R-ECG-01/R-OP-01/R-VIS-01. Correção candidata: em `regras.yaml`, casar somente o campo `id:`; manter o grep amplo em `motor/**/*.py` (onde a menção em docstring É rastreabilidade de código). NÃO editar `base_normativa` para o número se comportar — citação normativa é rastreabilidade protegida pela exceção de comentário do projeto; mexer no dado para consertar a métrica é pior que a métrica torta.

**(c) Derivado sem vigilância.** `docs/INDICE_DARQ.md` é gerado por `scripts/gerar_indice_darq.py` e é o Nível 1 do gate D-ARQ-63. Ficou defasado (v150 · 65 decisões contra v151 · 66) por um commit inteiro em main, sem que nada no painel piscasse — a próxima sessão teria cumprido o gate lendo um índice que não contém D-ARQ-66. Correção candidata: 4º número no painel, ou gate no ritual de fechamento que rode o gerador e falhe se o diff não for vazio.

**Procedência das facetas (b) e (c):** ambas causadas por omissões do prompt do Arquiteto em 003.EC — citar R-TEMP-01 na `base_normativa` e não mandar regerar o derivado ao criar D-ARQ-66. Registrado para que a causa não se perca na correção do instrumento.

**Status:** PARCIALMENTE RESOLVIDA (003.EF).
(a) cegueira a falha — RESOLVIDA: `medir_suite()` lê `returncode` e levanta em suíte vermelha (`4abfeb5`), 3 testes falha-sem/passa-com.
(c) derivado sem vigilância — RESOLVIDA: `INDICE_DARQ` regenerado (`c89f569`) e estado do derivado exposto como 4ª linha do painel (`642a705`), 2 testes. O gate já existia (`test_indice_em_disco_nao_divergiu`); 003.EF tornou-o visível sem pagar a suíte completa.
(b) ID citado conta como ID implementado — ABERTA, não tocada em 003.EF. Correção candidata inalterada: casar somente o campo `id:` em `regras.yaml`. Consequência viva: o painel segue com dois números (20 pelo instrumento / 19 pela intenção).

Nova instância de DH-003EC-01(b) (003.EN): a `base_normativa` de R-PSY-02 cita "R-PSY-01 (DEPRECATED)". Verificado de disco: `R-PSY-01 in ativos` = `False` — o header de R-PSY-01 em §5.7 contém "DEPRECATED", então o filtro `_ids_ativos_protocolo()` já o exclui do denominador antes da interseção, mesmo padrão de R-ESP-01/R-ESP-02 em 003.EI. A citação em prosa não infla numerador nem denominador. NÃO editada a `base_normativa` para o número se comportar; instância registrada.

### DH-003EC-02 — 79% do tempo da suíte é reparse de PDF real em setup por-teste `[ABERTA — higiene de instrumento]`

**Origem:** medição `--durations=15` da suíte completa, sessão 003.EC, baseline main `e3cba55`.

**Situação.** Suíte completa em **1366s (22min46)** para 973 testes coletados. Os 15 mais lentos somam ~1074s — cerca de **79% do tempo** — e todos são parse de PDF real, a maioria em `setup`, logo repetido a cada teste em vez de compartilhado:

| tempo | fase | teste |
|---|---|---|
| 134,6s | call | test_orquestracao_pgr.py::...fascino_real_rota_deterministica_aceita_zero_invocacao_llm |
| 93,2s | setup | test_extracao_pgr.py::...ebserh_humap_e_card_gated_por_densidade |
| 90,5s | call | test_orquestracao_pgr.py::...humap_real_gated_por_densidade |
| 90,4s | setup | test_transcritor_card.py::...ufgd_v7_real_105_pares_titulos_extremos |
| 90,2s | call | test_orquestracao_pgr.py::...ufgd_real_105_invocacoes_card_titulo |
| 84,7s | setup | test_transcritor_card.py::...humap_real_140_pares_titulos_vazios |
| 84,5s | setup | test_extracao_pgr.py::...ebserh_ufgd_v7_e_card_sem_pendencia |
| 75,1s | call | test_orquestracao_pgr.py::test_e2e_arquivo_real_ate_resultado |
| 74,8s | call | test_orquestracao_pgr.py::...viverde_real_familia_nao_reconhecida |
| 65,7s | setup | test_parser_familia_consciente.py::...devolve_19_blocos |

Documentos envolvidos: HUMAP, UFGD-v7, Fascino, Viverde.

**Correção candidata.** Fixture `scope="session"` para o texto extraído de cada PDF real, substituindo a extração por-setup. Toca APENAS quantas vezes o PDF é lido — nada do que os testes asseram muda. Fatia de higiene, não de comportamento.

**Por que importa além do conforto.** 22 minutos por rodada encarece exatamente a disciplina de medir-antes-de-afirmar, que em 003.EC pegou três defeitos que relatório verde não pegava: os 4 testes exigidos que não existiam (denunciados por 963→963), as 48 falhas não reconciliadas (denunciadas por 7+17+1≠48) e o índice derivado defasado (denunciado por 966≠967). Instrumento caro é instrumento que se deixa de usar.

**Correção de suspeita (registrar).** A hipótese inicial do Arquiteto era I/O de rede em `tests/test_gemini_extracao.py` — **REFUTADA** pela medição. É CPU de pdfplumber sobre documentos grandes, não espera de socket.

**Status:** ABERTA. Não-bloqueante.

### DT-003ED-01 — Grafia natural com preposição não resolve contra slug sem preposição `[PARCIALMENTE RESOLVIDA — 003.EJ; faceta máquina pesada ABERTA]`

**Origem:** 003.ED, ao medir por que R-PKG-ATIVCRIT não acionava no caso real.

**Situação.** O slug do vocabulário elide a preposição; o PGR escreve a forma natural. A
distância é sempre 3 ("em_", "de_"), fora do raio fuzzy 2 — nunca salvável por Levenshtein,
mesmo padrão que a Tier 1 de 003.DM mediu nos químicos. Medido `[MEDIDO — resolvedor real
sobre o vocabulário real @ e7311fd]`:

| termo | resolve |
|---|---|
| `Trabalho em Altura` | NAO_RESOLVIDO (FECHADO em 003.ED por alias NR-35) |
| `Motorista de equipamento pesado` | NAO_RESOLVIDO |
| `Motorista equipamento pesado` | EXATA |
| `Vibração de corpo inteiro` | NAO_RESOLVIDO |
| `Vibracao corpo inteiro` | EXATA |
| `Operador de máquina pesada` | NAO_RESOLVIDO |
| `Espaço confinado` / `Ruído` / `Eletricidade` / `Umidade` | EXATA |

**Impacto.** Atinge R-VIB-01 e R-VIB-02 `[VALIDADO]` pela via da vibração, e a perna de
máquina pesada de R-PKG-ATIVCRIT/R-ECG-01. Classe (2) de DT-003EB-01.

**O que a resolução exige (fatia de dado própria, uma fonte por vez).** Vibração: grafia
literal do **Anexo I da NR-09** — "Vibrações em Mãos e Braços (VMB)" e "Vibrações de Corpo
Inteiro (VCI)" `[INCERTO — literal NÃO conferido no texto vigente; a NR-09 tem atualização
2026, conferir `nr-09-atualizada-2026.pdf` antes de gravar]`. Máquina pesada: **sem grafia
normativa** — é Tier 2, bloqueada por DT-003DM-01; caminho alternativo é `riscos_implicitos`
por cargo (R-GHE-02) nos cargos operadores, decisão de dado própria com teste de
indissociabilidade vs. contingência (R-GHE-05).

**Atualização 003.EJ.** O `[INCERTO — literal NÃO conferido]` da vibração está **resolvido**:
NR-09 Anexo I, itens 1.1 e 2.1, "Vibrações em Mãos e Braços - VMB" e "Vibrações de Corpo
Inteiro - VCI", texto vigente `nr-09-atualizada-2026.pdf` conferido em 29/07/2026. Faceta
vibração **RESOLVIDA** (003.EJ, D-ARQ-70). Faceta **máquina pesada segue ABERTA** — sem grafia
normativa, caminho por `riscos_implicitos` de cargo.

**Status:** PARCIALMENTE RESOLVIDA (003.EJ). Faceta vibração RESOLVIDA; faceta máquina pesada ABERTA, não-bloqueante.

### DH-003ED-01 — Relatório do harness não carrega o gatilho por linha `[PARCIALMENTE RESOLVIDA — 003.EG; faceta risco_origem ABERTA]`

**Origem:** 003.ED, ao tentar atribuir causa às 16 emissões de R-PKG-ATIVCRIT. Precedente: DH-003EC-01.

**Situação.** O relatório de `rodar-offline` imprime pendências e, por GHE, a tabela de exames
com `regra_id` — mas NÃO os slugs resolvidos em `ctx.riscos` nem qual perna de um predicado
composto disparou. Consequência medida: o relatório não distingue "risco resolvido e não
relevante aqui" de "risco nunca presente"; responder "por que esta linha foi emitida" exigiu
reabrir o motor em memória. D-ARQ-22 Parte B exige que cada exame emitido carregue **regra de
origem, gatilho e status de validação** — o instrumento entrega a regra e omite os outros dois.

**Correção candidata.** Por GHE, listar slugs resolvidos; por linha emitida, o átomo do
predicado que a satisfez e o status da regra. Irmã de DH-003EC-01.

**Resolução (003.EG).** Facetas FECHADAS: `MatrizGHE.riscos_resolvidos` traz os slugs por GHE
(`ctx.riscos`, espelhados via `_diagnostico(ctx)` no orquestrador) e `Motivo.predicado` passa a
serializar a expressão real do `quando` da regra (`e(...)`/`ou(...)`/`nao(...)`, fim do literal
`"<composto>"`) — o átomo disparador de cada linha agora é derivável por inspeção de
`predicados_avaliados` sem reabrir o motor em memória. Faceta ABERTA: `Motivo.risco_origem`
segue `None` — qual risco específico satisfez a perna vencedora de um predicado composto não é
explícito, só derivável por leitura de `predicados_avaliados`. Rastro real exigiria mudar a
assinatura de `predicados.avaliar` (usada em todo o motor) — recorte deixado fora por decisão
do Arquiteto.

**Status:** PARCIALMENTE RESOLVIDA (003.EG). Faceta `risco_origem` ABERTA, não-bloqueante.

### DT-003EE-01 — `ConflitoProtocolo` sem disparador após D-ARQ-39 `[ABERTA, não-bloqueante]`

Medido em 003.EE: `grep -rn "raise ConflitoProtocolo" --include=*.py .` = zero no repo. `ConflitoProtocolo`
(`consolidacao.py:6`) e `except ConflitoProtocolo` (`orquestrador.py:52`) permanecem definidos e inalcançáveis.
Decisão de 003.EE: MANTER — o veículo de captura por-GHE é contrato de D-ARQ-15; removê-lo é revogação parcial de
D-ARQ-15, não limpeza. Registrado para não virar descoberta-surpresa (classe de erro que D-ARQ-67 pagou em 003.ED:
código inalcançável verde na suíte). Fecha quando (a) um call-site futuro voltar a levantá-la, ou (b) uma sessão
ARQUITETURA decidir que D-ARQ-15 não precisa mais do veículo.

### DT-003EG-01 — Audiometria emitida pelo motivo errado quando a perna do ruído está bloqueada `[FECHADA — D-ARQ-68 cl.5, 003.EZ]`

**Origem:** medição `003eg_fascino_rodar.md` (Fascino, 19 GHEs, commit `5a2d15b`), habilitada
pela Entrega 3 de 003.EG — o motivo por linha só ficou visível no relatório a partir desta sessão.

**Situação.** `audiometria` 12M é emitida em 16 de 19 GHEs. Em 15 deles o motivo é
`R-PKG-ATIVCRIT` (atividade crítica); `R-AUD-01` (ruído) aparece em apenas 1. Em GHEs onde o PGR
cita ruído, a perna de R-AUD-01 está bloqueada por `predicado_ausente` (quantificação ausente
via `ruido_acima_acao`) — mas o exame sai de qualquer forma, só que por outra regra, cujo
gatilho não é a exposição a ruído. Exame certo, razão errada: a linha não aponta para a
exposição que clinicamente a justificaria.

**Impacto.** Atrito direto com D-ARQ-22 Parte B (regra de origem, gatilho e status por exame
emitido) — o exame está presente, mas o `regra_id`/`predicado` da linha não é o do risco que
motivaria a auditoria a olhar para ele. Não-bloqueante para rodar (o exame certo sai de todo
modo); bloqueante para auditoria de PCMSO (a linha engana sobre a causa clínica). Só ficou
visível porque a Entrega 3 de 003.EG passou a imprimir o motivo por linha — antes, o relatório
mostrava só que `audiometria` saiu, não por qual regra.

**Status:** ABERTA. Não-bloqueante para rodar; candidata de investigação para sessão futura.

**Nota aditiva (003.EK).** Segue ABERTA — nenhuma regra mudou de motivo. Mas o eixo ganhou instrumento: D-ARQ-71 (pendência `perna_ausente_absorvida`) e a 8ª coluna do relatório (DH-003EJ-01 faceta b) tornam a causa visível quando o motivo impresso não é o esperado — a mesma classe de lacuna que esta DT descreve agora aparece na saída em vez de exigir rerun in-process para diagnosticar. Não fecha esta DT: o motivo errado continua saindo, só passou a ser auditável sem instrumentação ad-hoc.

**Nota aditiva (003.EX).** Segue ABERTA — `R-AUD-04` (piso universal, `todo_trabalhador`) não a
fecha nem a agrava: os motivos são concatenados por `stage_8_consolidacao` (D-ARQ-39), não
substituídos, então a linha de audiometria de um GHE com ruído mal-quantificado passa a carregar
`R-PKG-ATIVCRIT`/`R-AUD-04` **e** continua sem `R-AUD-01`/`R-AUD-02` — o exame sai pelo motivo
certo em mais casos (o piso cobre), mas onde `R-PKG-ATIVCRIT` já cobria antes, a audiometria
continua saindo pela regra errada. `DT-003EW-01` (irmã desta DT — mesma raiz
`ruido_acima_acao = Ausente`) foi FECHADA em 003.EX, mas por resolver a **saída** (agora tem
`DEM`), não a raiz. Esta DT segue sendo a que rastreia a raiz em si.

**Nota aditiva (003.EY).** Deixa de ser candidata de investigação não-bloqueante e passa a
**caminho crítico**: a varredura de 23 obras (`DT-003EY-01`) nomeia o predicado que falta aqui
— NR-07 Anexo II item 2, `ruido_acima_acao` quando o PGR cita ruído sem quantificar — com
evidência documental direta (21 de 226 cargos sem audiometria anotados `Ruído (abaixo do nível
de ação)` pela própria médica). `DT-003EY-01` depende da resolução deste predicado para a
correção candidata (ID nova sucedendo `R-AUD-04`). Não fecha aqui — a raiz continua
indeterminada, só ganhou o nome do que falta.

**FECHADA em 003.EZ, medição confirmada contra o Fascino (`rodar-offline`,
`relatorios/003ez_fascino_rodar.md`).** `D-ARQ-68` cl.5 resolve a raiz que esta DT rastreava
desde a origem: `ruido_acima_acao` deixa de ser um beco sem saída bloqueante e passa a admitir
presunção protetiva declarada (`R-AUD-01`/`R-AUD-02`, `quando_ausente: {presumir_true:
[ruido_acima_acao]}`). Medido: **17 GHEs do Fascino declaram `ruido`, todos com
`ruido_acima_acao = AUSENTE`**, e os **17** passam a carregar `R-AUD-01`/`R-AUD-02` na coluna de
motivos da linha de audiometria — contra **1** na baseline 003.EX (exatamente a métrica de que
esta DT reclamava, "`R-AUD-01` aparece em apenas 1"). Os 2 GHEs restantes não declaram ruído:
GHE-14 recebe audiometria por atividade crítica (sem `DEM`, correto — `R-AUD-02` não dispara sem
ruído) e GHE-19 não recebe audiometria — nenhum risco que a justifique, comportamento correto,
não regressão. Exame certo, razão certa: a linha agora aponta para a exposição que clinicamente
a justifica, com o sinal de que o dado é presumido — não medido — visível na pendência
`predicado_ausente_presumido` (32 ocorrências no corpus, 16 GHEs × 2 regras — o 17º GHE com
ruído, GHE-16, resolve por `perna_ausente_absorvida`, D-ARQ-71 cl.2; ver nota de fronteira em
D-ARQ-68 cl.5) e no piso `PARCIAL` da matriz (nunca `VÁLIDA`).

### DH-003EG-01 — Bytes NUL do PGR vazam para o artefato de saída `[ABERTA — higiene de instrumento]`

**Origem:** medição `003eg_fascino_rodar.md` (Fascino, commit `5a2d15b`).

**Situação.** O relatório carrega 122 bytes `\x00`, originados do texto verbatim do Fascino
(ex.: `'Microorganismos \x00Bacterias, virus, fungos e protozoários'`) dentro do campo `motivo`
de pendências `vocabulario_ausente`. Efeito medido: `grep` classifica o relatório como binário e
recusa saída de texto — o instrumento de diagnóstico quebra a ferramenta que o lê. DT-003DR-01
foi FECHADA em 003.DS no reconhecedor; a sanitização não alcança o artefato de saída do harness
de medição.

**Correção candidata.** Sanitizar NUL na renderização (`_renderizar_relatorio` ou o ponto de
formatação de `motivo`), não no dado — o dado verbatim é evidência, não deve ser reescrito na
origem.

**Registro adicional.** O arquivo é gravado com `\r\n` — recorrência da classe DH-003M-01.

**Status:** ABERTA. Não-bloqueante.

**Nota aditiva (003.EP).** Segue ABERTA — a DH não fecha. Bytes NUL no relatório do harness: **122 → 18** `[MEDIDO — 003.EP, contagem direta sobre \`003eo_fascino_rodar.md\` e \`003ep_fascino_rodar.md\`]`. A fatia 2 de 003.EP (separação nome/CBO na célula "Cargo / Função") removeu 85% como efeito colateral — o blob de cargo com CBO/NUL embutido era a maior fonte medida de NUL no relatório, e a separação limpa o CBO nas pendências `vocabulario_ausente` que citam o nome do cargo. O resíduo de 18 bytes tem outra origem (não medida nesta sessão) e não foi investigado — a correção candidata original (sanitizar na renderização, não no dado) continua válida e não foi implementada.

### DH-003EG-02 — O instrumento que pauta a fila vive fora do git `[ABERTA — higiene de método]`

**Origem:** 003.EG, ao abrir a sessão contra um diff desatualizado.

**Situação.** `.gitignore:26` ignora `relatorios/` inteiro (`git ls-files relatorios/` = vazio).
O diff motor×gabarito é o instrumento que pauta a fila desde D-ARQ-62, e nada em `git log`
denuncia um relatório vencido. Consequência medida: o último diff completo era de 003.EB
(`6f29928`) e envelheceu 4 sessões — 003.EC/ED/EE/EF mudaram o motor sem que a evidência fosse
re-tirada; a fila de 003.EG chegou a ser pautada contra ele. Mesma classe de DT-003DX-02 (regra
do gate fora do git).

**Correção candidata.** Versionar o sumário do diff (contagens + achados), mantendo o relatório
bruto ignorado — o sumário é pequeno, revisável em PR, e denuncia idade por si; o relatório
bruto continua grande e reproduzível sob demanda.

**Status:** ABERTA. Não-bloqueante.

### DH-003EG-03 — Derivado do `INDICE_DARQ` tem vigilância, mas o ritual não a invoca em sessão docs-only `[ABERTA — higiene de método]`

**Origem:** 003.EG (emenda), ao fechar a sessão principal.

**Situação.** 003.EF implementou a vigilância do derivado (`medir_indice_darq()`, 4ª linha do
painel) depois que `docs/INDICE_DARQ.md` ficou defasado no merge do PR #267. Na sessão
seguinte a mesma classe se repetiu: o commit `186150e` (DECISOES v154→v155) inseriu 24 linhas
sem regenerar o índice — 94 linhas divergentes, `test_indice_em_disco_nao_divergiu` vermelho.
Corrigido em `973a343` (47 linhas trocadas). Causa nomeada: o prompt de fechamento do
Arquiteto dispensou a suíte com a justificativa "docs-only" — a rede existia e foi desligada
por instrução, não por falha do instrumento; o teste que teria pego roda em 0,43s.

**Por que detectar não previne.** A vigilância só dispara quando alguém roda a suíte (ou o
teste específico), e a sessão docs-only é justamente a que não roda — o instrumento é
correto, o ritual em torno dele é que tinha um buraco.

**Correção instalada nesta emenda.** Cláusula fixa em `CLAUDE.md` ("Verificação": nenhum
prompt dispensa a suíte; toda sessão que toca `DECISOES_ARQUITETURAIS.md` regenera o índice)
e passo 3 do `docs/RITUAL_FECHAMENTO.md`.

**Resíduo ABERTO.** Ambas as correções dependem de leitura humana/agente — nenhum mecanismo
impede a 3ª ocorrência. Automação real (hook de pre-commit que regenera o índice quando
`DECISOES_ARQUITETURAIS.md` está staged) fica candidata, com a ressalva medida de que
`core.hooksPath` mora em `.git/config`, não versionado — o hook falharia em silêncio em outro
clone sem um passo de setup explícito.

**Status:** ABERTA. Não-bloqueante.

### DT-003EH-01 — Faixa de RX pode encurtar quando o laudo existe mas não está no PGR, e não há sinal `[ABERTA — depende de D-ARQ-28]`

**Origem:** 003.EH, ao destravar o ramo de ausência de R-RX-01.

**Situação.** O motor passa a emitir 24M para PGR silencioso sobre medição (ramo "empresas sem avaliações quantitativas"). Se a empresa de fato tiver avaliação quantitativa não transcrita no PGR e a faixa real for >100% LEO (12M), o motor subdimensiona sem sinal — a classe de erro silencioso plausível que D-ARQ-22 combate.

O sinal correto seria pendência NÃO-bloqueante anexada à linha ("faixa pode encurtar se houver avaliação quantitativa"), no molde da cláusula 3 de D-ARQ-31. Mecanismo inexistente: `emissao.py` só cria `Pendencia` no ramo `Ausente`, sempre `bloqueante=True` `[VERIFICADO — leitura de emissao.py:56-75, 003.EH]`; o trilho declarativo regra→pendência-não-bloqueante é D-ARQ-28, ainda PROPOSTA — mesma dependência de DT-002Y-01. Construí-lo em 003.EH violaria "uma coisa por vez".

**Status:** ABERTA. Não-bloqueante — a conduta emitida é a que a norma prescreve para o estado que o documento revela. Fecha com D-ARQ-28 ou por decisão própria.

### DH-003EH-01 — Mensagem do ramo (d) de `_helper_silica_asbesto` ficou órfã de sentido `[ABERTA — higiene de instrumento]`

**Origem:** 003.EH, revisão do Arquiteto sobre `7dd68e6` (achado de revisão, não de rodada).

**Situação.** Até 003.EG os ramos (b) e (d) compartilhavam o texto "Sílica/asbesto sem quantificação nem indicação de ausência de avaliação — medir ou declarar ausência de laudo". Com (b) reclassificado, (d) só é alcançável quando há medição afirmada mas não roteável (`valor` presente sem `pct_quartzo`/`fracao`) — e a mensagem manda "declarar ausência de laudo" a quem tem laudo, sem nomear o dado que realmente falta.

**Comportamento correto, diagnóstico enganoso.** Mesma classe de DT-003EG-01 (a linha não aponta para a causa real) e atrito com D-ARQ-22 Parte B (a pendência deve nomear o gatilho).

**Correção candidata.** Mensagem própria do ramo (d), nomeando `pct_quartzo`/`fracao`; toca a asserção de `test_rx_silica_valor_sem_pct_quartzo_continua_ausente_bloqueante`. Não empilhada em 003.EH por ser implementação nova, não redação.

**Status:** ABERTA. Não-bloqueante.

### DT-003EI-01 — R-PKG-SOLD e R-PKG-ARMADOR prescrevem espirometria incondicional onde o Anexo III 3.2 condiciona a sintoma `[ABERTA — 003.EI]`

**Origem:** 003.EI, ao materializar R-ESP-02 (poeira mineral, item 3.1) e depreciar R-ESP-01.

**Situação.** R-PKG-SOLD e R-PKG-ARMADOR são `[VALIDADO]` e prescrevem "Espirometria 24M (adm/per/MR/dem)" por fumos metálicos / policorte — agentes que caem no item 3.2 (agressor pulmonar não-mineral), cujo gatilho normativo é sinais ou sintomas respiratórios, não exposição.

**Pergunta de método (derivação normativa, D-ARQ-27):** a conduta é adição clínica legítima sobre o piso normativo, ou herdou a leitura do anexo anterior à 567/2022?

**Status:** ABERTA. Não-bloqueante — nenhuma das duas está materializada em `regras.yaml` `[VERIFICADO — grep do campo id:, 003.EI]`.

### DH-003EI-01 — Campo `status` de `regras.yaml` sem enum validado; convenção do PROTOCOLO diverge do dado real `[PARCIALMENTE RESOLVIDA — 003.EM; faceta 1 (enum não validado) ABERTA]`

**Origem:** 003.EI, ao gravar R-ESP-02 com `status: DERIVADO`.

**Faceta 1 — `status` não é enum validado.** R-ESP-02 introduz `DERIVADO`, quarto valor do campo `status` em `regras.yaml` (hoje: `VALIDADO` 58, `INTERPRETADO` 5, `DEPRECATED` 1). O carregador (`protocolo.py:64`) só distingue `DEPRECATED`, para excluí-lo do motor de avaliação; qualquer outra string passa sem checagem contra um conjunto fechado. `[MEDIDO — 003.EI]`.

**Faceta 2 — o campo `status` de `regras.yaml` diverge da convenção do PROTOCOLO.** Regras derivadas de texto normativo estão gravadas como `VALIDADO` (`R-RX-01-sem`, `R-BIO-04-*`), e o campo é lido num único ponto (`protocolo.py:64`), apenas para excluir `DEPRECATED` — não alcança `ExameEmitido` nem `Motivo`. Consequência: D-ARQ-22 Parte B ("a saída distingue por exame o status de validação da regra que o gerou") segue descumprida neste eixo, apesar de a Entrega 3 de 003.EG ter materializado `riscos_resolvidos` e `predicado`.

**Resolução da faceta 2 — 003.EM (D-ARQ-72).** `Motivo.status_regra` (`agente_medico/motor/tipos.py`) populado em `agente_medico/motor/estagios/emissao.py` via `regra.get("status")`, e renderizado por exame na coluna "status regra" de `superficie/apresentacao_matriz.py`. `Motivo`/`ExameEmitido` agora carregam o status de validação da regra que gerou a linha — o eixo que esta faceta registrava como descumprido fecha.

**Faceta 1 segue ABERTA.** `status` continua sem enum fechado. Medido em 003.EM: 65 regras em `regras.yaml`, todas com o campo, distribuídas em `VALIDADO` 58 / `INTERPRETADO` 5 / `DERIVADO` 1 / `DEPRECATED` 1.

**Status:** PARCIALMENTE RESOLVIDA. Faceta 1 ABERTA, não-bloqueante. Reconciliar exige varrer os 65 status existentes e fechar o enum — candidata a fechar junto com DH-003EM-01 (mesma sessão, mesmo dado).

### DH-003EI-02 — Taxonomia de `categoria` de exame diverge entre D-ARQ-12, o validador e o dado `[ABERTA — higiene de dado]`

**Origem:** 003.EI, bloqueador ao inserir o slug `espirometria`. Registro restaurado na passada de verificação do Arquiteto — a DH-003EI-01 original foi reescrita para o eixo `status` e este achado ficou sem casa.

Três conjuntos distintos `[MEDIDO — 003.EI]`: D-ARQ-12 prevê {clínico, biomonitoramento, imagem, funcional}; `test_vocabulario.py` valida {clinico, ocupacional, laboratorial, imagem}; o dado usa {laboratorial 43, ocupacional 4, imagem 2} — `clinico` está na lista validada com zero ocorrências. A implementação (002.D1) divergiu do texto decidido e nunca foi resincronizada.

Consumo de produção do campo: ZERO `[VERIFICADO — git grep "categoria" em motor/, superficie/, adaptadores/, scripts/, 003.EI]`. Único leitor é o teste de forma. Quarta instância da classe "campo sem consumidor" em quatro sessões (`anexo_nr07`, `tipo_ibe`, `disparador_clinico`, esta).

Decisão de 003.EI: espirometria seguiu a convenção do dado (`ocupacional`, precedente audiometria/ECG/acuidade_visual, todos funcionais), sem ampliar a enumeração.

Reconciliar exige retaxonomizar os 49 exames e decidir se o eixo tem função — sessão própria.

**Status:** ABERTA. Não-bloqueante.

### DT-003EJ-01 — `Poeira de madeira` é agente identificável fora dos dois quadros do Anexo III `[ABERTA — não-bloqueante]`

**Origem:** 003.EJ, derivação da ausência de RX em GHE-08 (Carpintaria) do Fascino.

**Situação.** O PGR declara `Poeira de madeira` — diferente de `Poeira respirável`, é agente identificável e admitiria slug próprio. Mas: (a) não é sílica, asbesto nem carvão mineral → fora do Quadro 1 `[DERIVADO — literal do Quadro 1]`; (b) o Quadro 2 exige, pelo rodapé, material não sensibilizante e de baixa toxicidade — poeira de madeira é sensibilizante respiratório reconhecido e há classificação de carcinogenicidade para poeira de madeira `[INCERTO — não conferido em fonte primária nesta sessão; a lista IARC não é capturável por fetch, conferir no monograph oficial antes de cravar]`. Se (b) se confirmar, madeira **não é PNOS** e fica fora dos dois quadros → sem RX pelo Anexo III, e sem espirometria pelo 3.1 (não é poeira mineral; cai no 3.2, condicionado a sinais/sintomas, fora do motor por D-ARQ-09).

**Consequência.** O RX 60M que a matriz humana prescreve em GHE-08 fica sem âncora nos dois quadros — mesma classe de DT-003EC-01, e o gatilho de reabertura é o mesmo (2º PGR atualizado no acervo, não n=1).

**O que a resolução exige.** Conferir a classificação de carcinogenicidade e de sensibilização da poeira de madeira em fonte primária; decidir se madeira ganha slug próprio com regime próprio ou permanece `vocabulario_ausente` honesto. Não-bloqueante: hoje o motor não emite, que é o comportamento correto sob a derivação acima.

### DT-003EJ-02 — Perna `Ausente` absorvida por `ou` verdadeiro não gera pendência; matriz vai a VÁLIDA com lacuna ambiental real ainda visível em `predicados_avaliados` `[RESOLVIDA — D-ARQ-71, 003.EK]`

**Origem:** 003.EJ, medição do Fascino — GHE-16 muda de `PARCIAL` para `VÁLIDA` ao resolver o alias de vibração mão-braço (D-ARQ-70), sem previsão do Arquiteto.

**Situação.** O sinal não se perdeu: `predicados_avaliados` do GHE-16 registra `ruido_acima_acao=AUSENTE` e o relatório o imprime. O que desapareceu foi a Pendencia, e o tri-estado de D-ARQ-31 computa sobre pendências e linhas, não sobre predicados avaliados — por isso a matriz vai a VÁLIDA com lacuna ambiental real registrada dois campos ao lado. O remédio NÃO exige D-ARQ-28 (trilho declarativo regra→pendência) nem mudar a assinatura de `predicados.avaliar`: a informação já está disponível no ponto da avaliação — mas só parcialmente: correção de 003.EK (`[MEDIDO — leitura de disco]`), a afirmação vale apenas para a perna avaliada ANTES do primeiro `True` no loop do `ou` (o loop descarta `primeiro_ausente_ou` ao retornar). No caso-âncora funciona por acidente de ordem — registro do erro preservado por D-ARQ-06 (correção ordem-dependente reprova).

**Família correta:** irmã de DH-003ED-01 faceta `risco_origem` (o avaliador sabe qual perna decidiu e não conta) e de DT-003EG-01 (a linha não aponta para a causa real).

**Caso-âncora:** GHE-16 do Fascino, PARCIAL → VÁLIDA com ruído sem laudo, 003.EJ.

**Status:** RESOLVIDA em 003.EK por **D-ARQ-71** — passada de diagnóstico separada (`pernas_ausentes_absorvidas`) detecta a perna absorvida sem depender de ordem, gera `Pendencia` não-bloqueante anexada à linha; tri-estado não se move.

### DH-003EJ-01 — O relatório do harness omite informação de pendência: atribuição por GHE e anexação por linha `[RESOLVIDA — 003.EK]`

**Origem:** 003.EJ. Duas facetas do mesmo eixo — `scripts/medicao_pgr.py`, `_formatar_pendencia` / `_renderizar_relatorio`.

**Faceta (a) — `ghe_id` não impresso. RESOLVIDA (003.EJ, commit afb8889).** `Pendencia.ghe_id` existe (`tipos.py:284`) e é preenchido (`hidratacao.py:116`), mas o formatador não o imprimia: 159 das 178 pendências de vocabulário saíam na seção global sem identidade de GHE, e atribuí-las exigia reparsear o PDF por fora.

**Faceta (b) — `ExameEmitido.pendencias_anexadas` não impressas. RESOLVIDA (003.EK, commit `823d467`).** A tabela de exames ganhou 8ª coluna de pendências anexadas. Consequência que motivou a correção: GHE-16 aparecia `PARCIAL` sem causa visível no relatório, e diagnosticar a divergência da previsão #5 exigiu rerun in-process contra dois vocabulários. D-ARQ-31 cl.3 anexa a pendência à linha justamente para matar subdimensionamento silencioso (D-ARQ-22) — o instrumento agora mostra.

**Registro de procedência:** a mensagem do commit `afb8889` rotula a faceta (a) como "DH-003ED-01 faceta de atribuicao". Rótulo impreciso do Arquiteto — DH-003ED-01 trata do gatilho por linha (`riscos_resolvidos`/`predicado`/`risco_origem`), eixo distinto. Não alterar DH-003ED-01; a correção fica registrada aqui.

**Status:** RESOLVIDA. Irmãs: DH-003EC-01, DH-003ED-01, DH-003EG-01 — quarta faceta do mesmo harness, agora fechada.

### DH-003EM-01 — Ordem de leitura da revisão em `apresentacao_matriz.py` é literal de vocabulário digitado em código, sem teste computado do dado `[ABERTA — higiene de instrumento]`

**Origem:** revisão do Arquiteto sobre a fatia 2 de 003.EM (D-ARQ-72).

**Situação.** `_STATUS_INSPECIONAR_PRIMEIRO = ("INTERPRETADO", "DERIVADO")` em `superficie/apresentacao_matriz.py:13` é literal de vocabulário digitado em código, sem teste computado do dado — a classe exata que D-ARQ-67 ("literal de vocabulário em código é contrato verificado por teste computado do dado") existe para impedir.

**Modo de falha nomeado.** Renomear ou acrescentar um valor de `status` em `regras.yaml` (ex.: `DERIVADA`, ou um `INTERPRETADO` virando `INTERPRETADA`) faz o bloco "inspecionar primeiro" esvaziar em silêncio, sem teste vermelho. É supressão silenciosa de exatamente a informação que D-ARQ-22 Parte B quer destacar para a revisão clínica.

**Correção candidata (não implementada nesta sessão).** Teste que computa o conjunto de `status` distintos de `regras.yaml` e afirma que todo valor fora de `{VALIDADO, DEPRECATED}` está coberto por `_STATUS_INSPECIONAR_PRIMEIRO`. Casa com a faceta 1 de DH-003EI-01 — as duas se resolvem na mesma sessão.

**Status:** ABERTA. Não-bloqueante.

### DH-003EM-02 — Bloco "inspecionar primeiro" nunca exercitado no primeiro nível de leitura (`INTERPRETADO`) no acervo real `[ABERTA — higiene de método]`

**Origem:** medição do Fascino, 003.EM.

**Situação.** Medido: `INTERPRETADO` = 0 ocorrências em 19 GHEs, apesar de existirem 5 regras `INTERPRETADO` em `regras.yaml`. O primeiro nível da ordem de leitura de D-ARQ-22 Parte B nunca é exercido neste PGR — o bloco "inspecionar primeiro" só mostra `DERIVADO`, e apenas de `R-ESP-02`.

**Não é defeito** — é medição de que o instrumento não está sendo exercido no caminho que mais importa. Registrado para que a ausência não seja lida como "não há regra interpretada".

**Status:** ABERTA. Não-bloqueante.

### DT-003EO-01 — Empresa/obra/tipo-de-documento não têm casa no modelo do motor `[ABERTA — não-bloqueante]`

**Origem:** 003.EO, fatia 2 (D-ARQ-73).

**Situação.** Nenhum tipo do motor (`PGR`, `GHEPGR`, `EnvelopeVerbatim`, `EnvelopeConfirmado`, `MatrizGHE`, `Resultado`) carrega razão social, nome de obra ou tipo de documento (Obra Nova/Atualização/Adendo/Funções Iniciais) — dado presente no cabeçalho de todo `matrizes_originais/*.doc(x)` medido. `CabecalhoDocumento` (`documento_matriz.py`) recebe esses campos por parâmetro do emissor, sem confirmação-RT nem persistência — irmã de DT-003BV-01 (validade) e da mesma classe de seam humano de D-ARQ-53 P2.

**Consequência.** Quem chama `montar_documento` hoje (harness de medição, futuro app S3) precisa preencher o cabeçalho manualmente por PGR. Não bloqueia o emissor — é lacuna de modelo, não de apresentação.

**Status:** ABERTA. Não-bloqueante.

### DT-003EO-02 — Grafia de `Glicemia`/`RX Tórax` no vocabulário: indecisa, não resolvida `[ABERTA — indeciso, D-ARQ-06]`

**Origem:** 003.EO, fatia 0 (medição 0b).

**Situação.** Medido por CRM (Patrícia CRM-GO 14.949; Carolini CRM-GO 14.864) em ~30 documentos de `matrizes_originais/`: `Glicemia de Jejum` × `Glicemia em Jejum` e `RX Tórax` × `RX de Tórax` **convivem dentro do mesmo médico e, em vários casos, dentro do mesmo documento** (`CONSCIENTE RESERVA 0028`, `CMO VARANDAS BUENO`, `SECONCI GOIÁS`, `GPL INCORPORAÇÃO R78` trazem as duas grafias no mesmo arquivo). Não há corte limpo por médica que decida a grafia dominante — parece copy-paste de template ao longo do tempo, não convenção pessoal.

**Decisão (D-ARQ-06 aplicado):** yaml não tocado. `nome_exibicao` de `glicemia` e `rx_torax_oit` permanecem como estavam antes de 003.EO.

**O que reabriria isto.** Uma amostra maior e mais recente (pós-2026) com corte temporal claro, ou confirmação direta da médica sobre qual grafia é a atual.

**Status:** ABERTA. Não-bloqueante.

### DT-003EO-03 — Clínico semestral de R-CLI-02/R-CLI-03 sem alcance em produção nos GHEs com manganês (serralheiro/armador) `[ABERTA — não-bloqueante]`

**Origem:** 003.EO EMENDA 1, fatia 4 — medição confirmada contra o Fascino real.

**Situação.** O gabarito Fascino prescreve `Exame Clínico` semestral (6M) para GHE-09 (Armador) e GHE-17 (Serralheiro) — R-CLI-03 `[VALIDADO]` (manganês fora do Anexo I dispara clínico semestral) e possivelmente R-CLI-02. O motor emite 12M (default R-CLI-01) nos dois GHEs, medido nesta sessão. Mesma raiz de DT-003EI-01: o pacote clínico serralheiro/armador (`R-PKG-SOLD`/`R-PKG-ARMADOR`) não está materializado em `regras.yaml` — o motor nunca resolve manganês para esses GHEs, logo R-CLI-03 nunca dispara.

**Não materializado nesta sessão** — 003.EO não toca conduta clínica, por cláusula fixa do prompt. Registro do achado, não correção.

**Manganês não tem slug em `exames.yaml` — `R-BIO-03` `[VALIDADO]` não é materializável enquanto ele não existir** `[VERIFICADO — grep em `regras.yaml` e `exames.yaml` @ árvore de trabalho, 003.EO EMENDA 3]`. `manganes` não aparece em `regras.yaml` em nenhuma forma (nem `id:`, nem `emite`, nem `quando`), e não há slug de exame para "Manganês no sangue"/"Manganês sanguíneo" em `exames.yaml` (existe só como agente em `agentes.yaml`). R-BIO-03 (NR-15: qualquer exposição confirmada a Mn → manganês sanguíneo semestral em adm/per/MR, regra do protocolo desde a v2) **nunca foi materializada, e não é materializável enquanto o exame não existir no vocabulário** — mesma classe de achado de 003.EH sobre `R-RX-01-sem`. Popular o slug é pré-requisito de qualquer materialização do pacote Mn/serralheiro-armador, antes mesmo de `R-PKG-SOLD`/`R-PKG-ARMADOR` entrarem em `regras.yaml`.

**Status:** ABERTA. Não-bloqueante. Resolve-se junto com DT-003EI-01 (materializar o pacote Mn — o slug de manganês é a peça que falta primeiro).

### DT-003EO-04 — `GHEPGR.cargos` chega como 1 string por GHE do parser da família Consciente; a expansão GHE→cargo de D-ARQ-73 não separa cargos reais `[FECHADA — 003.EP]`

**Origem:** 003.EO, fatia 4 — medição contra o Fascino real (achado fora do previsto pela EMENDA 1); quantificado nas EMENDAs 3 e 4.

**Situação — duas facetas de gravidade diferente**, ambas do mesmo `_extrair_cargos_da_linha` (`agente_medico/motor/parser_familia_consciente.py:133`, docstring atualizado nesta sessão):

- **(a) Concatenação — cosmética.** `GHEPGR.cargos` chega como tupla de UM elemento por GHE, a linha inteira da coluna Cargo/Função verbatim (ex.: `"Auxiliar de Engenharia \x003121\x0005\x00, Estagiário de Engenharia \x004110\x0010\x00, ..."`, CBO colado ao nome com NUL embutido), delimitador inconsistente entre vírgula (maioria) e ponto-e-vírgula (GHE-07). Os cargos estão todos lá, numa string só; o documento sai com uma linha em vez de N. Feio, recuperável, visível.
- **(b) Perda por quebra de linha — silenciosa, a faceta grave.** `_extrair_cargos_da_linha` só captura a linha física do próprio rótulo "Cargo / Função"; cargo cuja lista continua na linha física seguinte da tabela **não chega a `GHEPGR` de jeito nenhum** — por instrução explícita da sessão 003.DZ (escopo declarado, não bug). Um cargo perdido é um trabalhador sem matriz de exames, e o documento sai sem sinal de que ele existia — erro silencioso plausível, a classe exata que D-ARQ-22 combate, invisível justamente porque o documento parece completo.

**Medição nominal (003.EO EMENDA 3, cruzamento contra os 41 cargos do gabarito, read-only):** **35 de 41 cargos sobrevivem (85%); 6 são perdidos pela faceta (b), concentrados em 2 de 19 GHEs.** Os outros 17 GHEs preservam 100% dos cargos.

| GHE | cargos do gabarito | sobrevivem | perdidos |
|---|---|---|---|
| GHE-03 | 8 | 4 | Encarregado de Pintor; Encarregado de Carpinteiro; Supervisor de Instalações Elétricas; Auxiliar de Obra |
| GHE-06 | 5 | 3 | Aprendiz Administrativo de Obra; Assistente Administrativo de Obras |

GHE-03 é o caso originalmente medido em 003.DZ. **GHE-06 é um 2º caso, não citado na medição original** — o limite era mais amplo do que o registro anterior indicava (docstring corrigido nesta sessão, commit `d826f46`).

**Consequência visível agora.** A expansão GHE→cargo de D-ARQ-73 (`montar_documento`) está correta para o dado que recebe — com 1 elemento (ou com elemento faltando por (b)), produz exatamente isso. Mas esta é a primeira sessão com emissor de documento real, e as duas facetas ficam visíveis pela primeira vez: o HTML/DOCX do Fascino sai com uma linha por GHE em vez de uma por cargo (a), e 6 cargos reais do gabarito simplesmente não aparecem em lugar nenhum do documento (b).

**Decisão (EMENDA 4 do Arquiteto): fecha em `003.EP`, não nesta sessão.** Três razões: (1) recuperar a linha física seguinte reverte escopo declarado por outra sessão (003.DZ) — decisão de Arquiteto com D-ARQ próprio, não patch de fim de sessão; (2) o separador não é decidível sem desenho — delimitador inconsistente + CBO colado ao nome com NUL embutido (`Encarregado de Elétrica 99501\x0005\x00`) fazem um split ingênuo por vírgula produzir cargo fantasma a partir de código CBO, dano pior que o atual (hoje faltam cargos; ali sobrariam cargos inexistentes); (3) uma coisa por vez — 003.EO já tem 12 testes, 3 arquivos novos, uma D-ARQ e quatro DTs. `003.EP` = duas peças: recuperação de linha física (exige D-ARQ que reveja o escopo de 003.DZ) + separação cargo/CBO (exige decidir separador, CBO e nome).

**Caminho avaliado e rejeitado nesta sessão:** emitir `Pendencia` não-bloqueante ("lista de cargos pode estar truncada"), no molde de D-ARQ-71, tornando o erro visível sem consertá-lo. Rejeitado porque a **detecção é o problema em aberto, não a pendência**: o parser não sabe que truncou. Saber exigiria heurística de continuação de linha (frágil) ou uma contagem de cargos declarada que o PGR não fornece — o campo que existe é "Quantidade de Funcionários expostos neste GHE", que conta pessoas, não cargos. `003.EP` reavalia este caminho com o desenho em mãos, não do zero.

**Candidato natural:** fatia 2 do roteamento de D-ARQ-65 (que já precisa tocar `parser_familia_consciente.py`).

**Status histórico (até 003.EO):** ABERTA. Não-bloqueante para o motor/merge (D-ARQ-08); **o marco S2 não fecha sem ela** — ver PLANO_V1.md.

**Fechamento (003.EP, fatias 1-3; commits `aaa9eca`/`486d54d`/`7f19cf4`).** Ambas as facetas fecham.

- **(a) Concatenação — fechada.** A célula passa a render um nome por cargo — `GHEPGR.cargos` deixa de ser 1 string por GHE. O código CBO é descartado (não modelado): precedente 003.DG-1 (campo novo exige consumidor a jusante na mesma fatia — seria a 5ª instância de campo-sem-consumidor, após `anexo_nr07`, `tipo_ibe`, `disparador_clinico`, `categoria`). Dívida nomeada com consumidor candidato: **DT-003ED-01 faceta máquina pesada** (D-ARQ-65 cláusula 5, abaixo).
- **(b) Perda por quebra de linha — fechada.** `_extrair_cargos_da_linha` (003.EP fatia 1) passa a capturar as linhas físicas seguintes na banda do valor do rótulo, por transição de banda (não pelo literal do próximo campo) — os 6 cargos nomeados na tabela acima (GHE-03: 4; GHE-06: 2) chegam a `GHEPGR`.

**Evidência.** Gate nominal (003.EP fatia 2): os 41 nomes extraídos do Fascino real batem, nome a nome (case-insensitive), com **0 divergências** contra `relatorios/003eo_emenda3_cargos_perdidos.md`. E2e real (003.EP fatia 3, `agente_medico/tests/test_documento_matriz.py::test_pipeline_real_fascino_ate_documento_41_linhas_cargo`): pipeline completo até `montar_documento` produz **41 `LinhaCargo`**, os 6 cargos nomeados presentes nominalmente, nenhum `LinhaCargo.cargo` vazio.

**Correção de premissa da EMENDA 4 (o registro acima FICA — D-ARQ-06, isto não o substitui, complementa).** A EMENDA 4 atribuiu a indecisão do separador a dois problemas somados: "delimitador inconsistente (vírgula×ponto-e-vírgula) + CBO colado ao nome com NUL". Medido em 003.EP fatia 0 (`relatorios/003ep_anatomia_cargo.md`): o sintoma estava certo, a causa não. Os dois grupos de dígitos colados ao nome não são dois números — são **um único código CBO-2002 no formato `NNNN-NN`**, partido em duas partes pela extração do PDF. O `\x00` entre eles é o **mesmo glifo-hífen** que o módulo já tratava como equivalente a `-` em `_PADRAO_TITULO_ANCORA` (`[-\x00]`) e que aparece tanto no separador do título do GHE (`'GHE 01 \x00 ENGENHARIA'`) quanto dentro de palavra composta (`'HIDRO\x00SANITÁRIAS'`) — não é uma classe nova de ambiguidade, é a mesma já catalogada. A âncora de separação nome/CBO é o **código** (corrida final de dígitos-e-separadores), não o delimitador entre entradas — vírgula×ponto-e-vírgula vira mero aparo de string, resolvido dividindo por ambos. Medido: **41/41 entradas têm o código; 40/41 têm o glifo antes dele** — a exceção (`"Encarregado de Elétrica 99501\x0005\x00"`, sem NUL antes do CBO) não impediu a separação correta; é resíduo nomeado, não a mesma dívida (ver DT-003EP-02).

**Resíduos que sobrevivem ao fechamento — NÃO são esta dívida.** Ver **DT-003EP-01** (R-GHE-02 inalcançável em produção mesmo com nomes reais) e **DT-003EP-02** (dois caminhos de silêncio remanescentes no parser, não exercitados no corpus Fascino).

**Nota aditiva (003.EQ, mesma ID, não abre dívida nova).** Fechamento confirmado em produção real, não só em teste: a rodada manual de 04/08/2026 no host do Diovanni renderizou 41 cargos em 19 GHEs, com os 6 antes perdidos presentes nominalmente (GHE-03: Encarregado de Pintor, Encarregado de Carpinteiro, Supervisor de Instalações Elétricas, Auxiliar de Obra; GHE-06: Aprendiz Administrativo de Obra, Assistente Administrativo de Obras).

**Status:** FECHADA em 003.EP.

### DT-003EP-01 — R-GHE-02 é inalcançável em produção: `cargos_vocab.get(cargo)` é lookup exato contra slugs minúsculos, sem resolver `[ABERTA — não-bloqueante]`

**Origem:** 003.EP fatia 4 (revisão do Arquiteto, ao fechar DT-003EO-04).

**Situação.** `agente_medico/motor/estagios/riscos.py:61` faz `cargos_vocab.get(cargo)` — lookup exato, case-sensitive, contra as chaves de `cargos.yaml` (`soldador`, `serralheiro`, `pintor`, `carpinteiro`, ...), sem passar por `normalizar_termo` nem pelo resolver de D-ARQ-50 P2. Antes de 003.EP isso era invisível: `cargos` era um blob de texto por GHE (1 string com CBO/NUL embutido, DT-003EO-04 faceta (a)) que não casaria nenhuma chave do vocabulário de qualquer forma — o miss estava mascarado pela faceta (a). Com nomes reais e limpos (pós 003.EP), o miss vira **medido, não hipotético**: pendências `regra_origem="R-GHE-02"` saíram de 19 (1 por GHE, sempre miss no blob) para **41 (1 por cargo, sempre miss no nome)** — `relatorios/003ep_fascino_rodar.md` vs. `003eo_fascino_rodar.md`, delta exato +22 = 41-19, medido nesta sessão.

**Agravante.** `soldador` é o único cargo em `cargos.yaml` com `riscos_implicitos` não-vazio (`[fumos_metalicos, radiacao_uv_ir]`) e `pacotes_aplicaveis` não-vazio (`[R-PKG-SOLD]`) — e só não dispara **por acidente de caixa**: um cargo extraído literalmente `"Soldador"` (capitalizado, como todo nome verbatim do parser) nunca casa a chave `soldador` (minúscula) num `.get()` exato, mesmo sendo a mesma palavra. Mesma classe do "VCI resolvia por acidente ortográfico" (003.EJ). Classe de `R-RX-01-sem` (003.EH) e `R-BIO-03` (003.EO): regra formalmente `[VALIDADO]`, verde na suíte (nenhum teste unitário exercita o cargo real do parser contra o vocabulário), **morta em produção**.

**Não é conserto de passagem desta fatia.** Ligar o resolver (`normalizar_termo`/D-ARQ-50 P2) a `cargos_vocab` faria R-GHE-02 promover risco implícito de verdade e R-PKG-SOLD disparar pela 1ª vez em produção — isso **muda conduta clínica**, não é higiene de parser. Exige fatia própria com gate clínico e teste-por-regra (mesma disciplina de qualquer R-* nova/reativada), fora do escopo de 003.EP (que não toca `riscos.py`/`cargos.yaml` por instrução explícita).

**Status:** ABERTA. Não-bloqueante — a regra segue formalmente `[VALIDADO]` e não regride; só deixa de estar mascarada.

### DT-003EP-02 — Dois caminhos de silêncio remanescentes no parser da família Consciente `[ABERTA — não-bloqueante]`

**Origem:** 003.EP fatia 4 (revisão do Arquiteto, ao fechar DT-003EO-04).

**Situação — duas bordas não exercitadas nos 19 blocos do Fascino, ambas em `parser_familia_consciente.py`:**

- **(a) Entrada sem cauda CBO vira cargo fantasma.** `_separar_nome_cbo` (ramo `if not ocorrencias: return entrada`) devolve QUALQUER entrada sem candidata a CBO inteira, como se fosse um nome válido — sem sinal de que é suspeita. Medido indiretamente (003.EP fatia 2, varredura inversa do gate da fatia 1): a reversão do laço de overflow COM o split da fatia 2 ainda ativo produz **36** cargos no total (não 41, não os 35 originais) — o `+1` sobre 35 é o fragmento órfão `"Encarregado"` do GHE-03 truncado (a metade de "Encarregado de Pintor" que fica na linha do rótulo quando a continuação não é lida), que a separação aceita como cargo por não ter como distingui-lo de um cargo legítimo sem CBO. Esse é exatamente o dano que a EMENDA 4 de 003.EO havia nomeado como **pior que a perda** ("sobrariam cargos inexistentes") — só que agora medido, não hipotético.
- **(b) Rótulo sem valor na própria linha devolve zero cargos, sem sinal.** `if len(palavras_rotulo) > 3:` — quando a célula "Cargo / Função" está vazia na própria linha do rótulo e o valor só começa na linha física seguinte, a função devolve `()` silenciosamente. É o mesmo modo de falha que a fatia 1 fechou (overflow não capturado), reintroduzido pela borda: a fatia 1 só lê continuação a partir de `palavras_rotulo[3]`, que não existe quando o rótulo não carrega nenhuma palavra de valor.

**Nenhum dos dois é alcançável nos 19 blocos do Fascino** (medido, gate 41/41 sem sobra nem falta) — mas "não alcançável no corpus medido" **não é** "impossível": a família Consciente tem outros PGRs (`matrizes_originais/`) não medidos nesta sessão, e o layout de formulário de 2 colunas (D-ARQ-65 cláusula 5) pode ter uma célula mais longa em algum deles.

**Candidatos de resolução, a decidir em fatia própria (nenhum implementado aqui):**
1. `FamiliaNaoReconhecida` — canal já existente (D-ARQ-65 cláusula 2), mas GROSSO: joga o documento inteiro para a rota LLM, hoje bloqueada por quota (`transcricao_indisponivel_pgr`).
2. Sinal novo do parser (`Pendencia` ou tipo de retorno que carregue "célula suspeita") para a camada de roteamento decidir — mecanismo que não existe hoje, fora do escopo de definir aqui.

**Status:** ABERTA. Não-bloqueante — não exercitado no corpus medido.

### DH-003EP-01 — `_sanitizar` apaga o glifo-hífen no documento assinado, em vez de convertê-lo `[ABERTA — higiene de instrumento]`

**Origem:** 003.EP fatia 4 (revisão do Arquiteto).

**Situação.** `superficie/documento_matriz.py:36` (`_LIMPAR_CONTROLE`) remove controle ASCII, incluindo `\x00`, **sem substituição**. Se `\x00` é o mesmo glifo-hífen que D-ARQ-65 cláusula 5 e `_PADRAO_TITULO_ANCORA` já tratam como equivalente a `-`, então `nome_ghe` verbatim `'INSTALAÇÕES HIDRO\x00SANITÁRIAS'` sai, no documento renderizado (HTML/DOCX, o que a Dra. Carolini assina), como `'INSTALAÇÕES HIDROSANITÁRIAS'` — palavra colada, sem o hífen que o dado original carregava. Confirmado nesta sessão: `_sanitizar('INSTALAÇÕES HIDRO\x00SANITÁRIAS')` → `'INSTALAÇÕES HIDROSANITÁRIAS'`.

`[INCERTO — o mapeamento correto (`\x00` → `-`) não foi confirmado contra o glifo real da fonte do PDF; pode ser espaço, pode ser hífen, pode ser nada. Não decidido nesta sessão.]`

**Nota sobre o comentário de procedência existente.** `documento_matriz.py:32-35` descreve a origem do NUL como "glifo de CBO quebrado" — medidamente incompleto: o mesmo glifo aparece também no separador do título do GHE (`'GHE 01 \x00 ENGENHARIA'`) e dentro de palavra composta (`'HIDRO\x00SANITÁRIAS'`), não só colado a CBO. Comentário não editado nesta fatia (fora de `docs/`, fora do escopo de 003.EP) — registrado aqui para a sessão que resolver esta DH.

**Nota aditiva (003.EQ, mesma ID, não abre dívida nova).** A DH sai de hipótese para confirmada na saída real: na rodada de 04/08/2026 o GHE-10 aparece na tela e no documento como `INSTALAÇÕES HIDROSANITÁRIAS` — o glifo-hífen foi apagado em vez de convertido, na palavra composta, no artefato que a médica assina. O `[INCERTO]` sobre o mapeamento (`\x00` → `-` vs espaço vs nada) permanece: a confirmação é do sintoma, não do mapeamento correto.

**Status:** ABERTA. Não-bloqueante — higiene de instrumento, não perda de dado (o dado verbatim em `MatrizGHE.nome_ghe` permanece correto; só a renderização apaga em vez de converter).

### DH-003EQ-01 — preservação-em-download da casca sem cobertura automatizada `[ABERTA — lacuna de ferramenta]`

**Origem:** 003.EQ (emenda 2).

**Situação.** `AppTest` do Streamlit instalado (1.56.0, dentro do pin `>=1.35.0,<2.0.0`) não expõe `download_button`: `element_tree.py` não tem case para o elemento, que cai em `UnknownElement` (não-`Widget`, sem `.click()`); não há accessor em `dir(AppTest)`, ao contrário de `button`/`checkbox`/`file_uploader`/`text_input` `[MEDIDO — Code, 003.EQ]`. O rerun-no-clique foi confirmado no fonte (`on_click` default `"rerun"`) e corrigido por `st.session_state`; a decisão de reuso está coberta por teste de unidade (9a-9c), mas o fio entre o clique real e essa decisão segue sem cobertura — irredutível com o tooling atual, não falta de trabalho.

**Gatilho de fechamento.** Versão de Streamlit cujo `AppTest` exponha `download_button`. Até lá, passada manual no navegador antes de cada release.

**Passada de 04/08/2026 (Diovanni, host real, upload nativo).** Os dois casos passaram: 19 GHEs/41 cargos com assinatura marcada, downloads presentes; sem assinatura, banner "PGR rejeitado" nomeando `assinatura_invalida` (R-PGR-01), nenhum download oferecido.

**Status:** ABERTA — lacuna de ferramenta, não falta de trabalho.

### DT-003EQ-01 — lixo de recorte vaza como termo de agente `[ABERTA — faceta de DT-003L-01]`

**Origem:** 003.EQ, rodada real do Fascino.

**Situação.** A pendência `vocabulario_ausente` cita como termo `'Bater contra ou ser atingido por (trânsito) S Irrelevante Avaliação e IIBR / AQUALIRPS. A metodologia executada acima para cada 1.5.6.1 alínea Riscos das Funções novas empresas riscos das'` — parágrafos inteiros do PGR capturados como se fossem um agente. Não é lacuna de vocabulário: nenhum `termos:` resolveria isso. É defeito de recorte/transcrição a montante, faceta de DT-003L-01.

**Não-bloqueante** — vira pendência honesta, não conduta errada.

**Candidato de resolução.** Gate de forma sobre o termo transcrito — comprimento e pontuação como discriminantes — decisão de arquitetura própria.

**Status:** ABERTA.

### DT-003EQ-02 — `Maganês` recusado pelo fuzzy: custo clínico do D-ARQ-64 medido `[ABERTA — decisão de dado]`

**Origem:** 003.EQ, rodada real do Fascino.

**Situação.** O PGR do Fascino escreve `Maganês` (typo de Manganês). O resolvedor encontra `manganes` a distância 1, mas o slug é carregado (fora da allowlist) → `fuzzy_recusado`, pendência não-bloqueante, agente não resolvido. D-ARQ-64 está operando exatamente como desenhado — o veto de resultado sobre slug crítico é o comportamento correto, e afrouxá-lo reabriria a classe `Silício`→`silica`.

**Custo real.** Exposição a manganês declarada no documento não chega ao motor, e R-BIO-03/R-CLI-03 não disparam. Casa com DT-003EO-03 (clínico semestral do Mn sem alcance) e com a nota de DT-003EP-01 (`soldador` sem resolver).

**Caminho candidato.** Alias medido sob D-ARQ-70 (grafia de corpus + fonte dupla + teste anti-FP) — `Maganês` é grafia medida em documento real, não hipótese. Não mexer na allowlist: `manganes` é slug carregado por definição.

**Status:** ABERTA — decisão do Arquiteto, fatia própria.

### DT-003EQ-03 — `status == "PRELIMINAR"` não aparece na tela nem no documento `[ABERTA — não-bloqueante]`

**Origem:** 003.EQ, rodada real do Fascino.

**Situação.** O orquestrador carimba `PRELIMINAR` quando qualquer GHE fica `PARCIAL` ou `BLOQUEADA`. No Fascino esse é o caso normal (2 VÁLIDA / 16 PARCIAL / 1 BLOQUEADA), logo todo documento gerado hoje é preliminar e nada no artefato assinado o declara.

**Mitigado em parte.** As pendências aparecem na tela. **Não mitigado:** o DOCX que a médica assina não carrega marca. Irmã de DT-003EO-01 (cabeçalho como seam humano).

**Fronteira com D-ARQ-74.** D-ARQ-74 cl.1 cobre `REJEITADO`, não `PRELIMINAR` — deliberado, porque matriz parcial é entrega válida por D-ARQ-31; falta só a marca.

**Status:** ABERTA — não-bloqueante.

### Registro de caminho não-ocorrente (003.EQ) — cargo com zero células indistinguível de cargo sem exame exigido

Não abre DT. O caminho "cargo com zero células no documento assinado, indistinguível de
cargo sem exame exigido" foi levantado pelo Arquiteto e medido como não-ocorrente no
Fascino: todo cargo dos 41 recebe no mínimo os três incondicionais (Exame Clínico
R-CLI-01; Avaliação Psicossocial e Av. Médica de Saúde Mental R-PSY-02). Registrado para
não ser redescoberto como hipótese; reabre se uma regra incondicional for depreciada.

### DH-003ES-01 — ramos `NEGAR` e `LIBERAR` do gate sem cobertura de casca `[ABERTA — lacuna de cobertura]`

**Origem:** 003.ES fatia 2.

**Situação.** Os três desfechos de `decidir_acesso` têm teste de unidade (003.ES, testes 5-7 de
`test_autorizacao.py`), mas a tradução casca→ação em `app_matriz.py` só é exercitada no ramo
`PEDIR_LOGIN`: os dois testes de `test_entrypoint_app.py` (`test_entrypoint_sem_login_para_no_gate`
e `test_is_logged_in_nao_booleano_e_tratado_como_nao_logado`) fixam `is_logged_in` em `False` e em
`"sim"` (string truthy, não o literal `True`) — em ambos, `_logado` avalia `False` e a decisão é
sempre `PEDIR_LOGIN`. Ninguém testa que `NEGAR` mostra o erro e o botão "Sair" sem chamar
`pagina_matriz()`, nem que `LIBERAR` chega à página. A sonda 2 de 003.ES mediu que `monkeypatch`
sobre `streamlit.user` alcança o script rodado por `AppTest` (`exception: ElementList()`,
`markdown: ['anonimo']`), então os dois ramos são alcançáveis — a lacuna é de execução, não de
ferramenta.

**Contraste com DH-003EQ-01.** Irmã pela origem (limite de harness do `AppTest`), oposta pelo
diagnóstico: lá o harness não expõe `download_button` — sem caminho disponível. Aqui há caminho
medido (sonda 2) e a lacuna é só não ter sido exercitada ainda.

**Status:** ABERTA — não-bloqueante. A decisão em si está coberta por unidade e é fail-closed;
falta cobrir a tradução casca→ação nos dois ramos que `test_entrypoint_app.py` ainda não toca.

### DH-003ET-01 — fixtures de PDF não versionadas `[ABERTA — higiene de instrumento]`

**Origem:** 003.ET fatia 2, emenda.

**Situação.** `matrizes_originais/` tem **12 PDFs tracked**, e nem o
`pgr_Cjr Engenharia Ltda (M Construtora).pdf` nem o PGR Fascino (`PGR - CONSCIENTE CONSTRUTORA E
INCORPORADORA SPE 0030 - FASCINO (15.07.26).pdf`) estão entre eles — os dois só existem no host do
Diovanni. Consequência: `agente_medico/tests/test_documento_matriz.py` (e2e Fascino),
`agente_medico/tests/test_parser_familia_consciente.py` e o caso Fascino de
`test_liberacao_cache_pdf.py` dependem de arquivos ausentes em clone limpo — em clone limpo eles
skipam em silêncio, e a suíte segue verde com menos cobertura do que o número sugere. Classe
DH-003ES-01 (lacuna de cobertura silenciosa).

**Origem do achado.** Nasceu na emenda da fatia 2, quando um teste novo apontava para uma fixture
não versionada com comentário afirmando o contrário; corrigido para o Viverde (tracked) no caso
que permitia a troca, e nomeado como dívida no caso que não permitia (Fascino exige um PDF
específico, não substituível).

**Status:** ABERTA — não-bloqueante. Resolução (versionar as fixtures, trocar por PDFs
sintéticos, ou marcar explicitamente a suíte como condicionada) é sessão própria.

### DH-003EU-01 — o legado perdeu o nome canônico do seu arquivo de dependências `[ABERTA — higiene de ambiente, duas facetas]`

Consequência aceita de D-ARQ-78 cláusula 2, registrada para não ser redescoberta como defeito.

**(a) `.devcontainer/devcontainer.json`** roda `[ -f requirements.txt ] && pip3 install --user -r
requirements.txt` e passa a instalar as 5 deps do app novo, não as 14 do legado. Efeito **não
medido** — ninguém verificou se o devcontainer é usado por alguém hoje. Não tocado na fatia 1 por
decisão do Arquiteto: mexer sem medir troca uma incerteza por outra.

**(b) O legado ficou órfão.** Quem rodar `pip install -r requirements.txt` na raiz esperando servir
`app.py` instala o conjunto errado, e o legado quebra por falta de `pandas`/`supabase`. **Falha
ruidosa, não silenciosa** — lado certo do trade, e o inverso exato do risco que D-ARQ-77 cl.1
combatia. Conserto, se um dia for preciso: apontar o consumidor do legado para
`requirements-legado.txt`.

Não-bloqueante: nenhum caminho de produção do app novo passa por qualquer das duas facetas.

### DH-003EU-02 — `test_dockerfile_instala_o_requirements_do_app_nao_o_do_legado` promete mais do que discrimina `[ABERTA — higiene de instrumento]`

Após D-ARQ-78 cl.2, a asserção `not any("requirements-legado.txt" in tokens ...)` só fica vermelha
se alguém escrever `COPY requirements-legado.txt` no `Dockerfile` — cenário que ninguém produz por
acidente. O teste discrimina algo real, mas de probabilidade desprezível.

**O invariante que importa está coberto, em outro arquivo:** se o `requirements.txt` da raiz voltar
a ser o do legado, `test_nada_declarado_a_mais_do_que_o_importado`
(`agente_medico/tests/test_requirements_app.py`) fica vermelho na hora, porque `pandas`, `supabase`
e `opencv-python-headless` apareceriam declarados sem serem importados. **Não há lacuna de
cobertura — há um nome de teste que promete mais do que o corpo entrega.** Origem: redação do
Arquiteto no prompt da fatia 1, não do Code.

### DT-003EW-01 — Audiometria sem demissional `[FECHADA — R-AUD-04, 003.EX]`

**Origem:** 003.EW, comparação contra o gabarito real da Dra. Carolini
(`MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc`, mesma obra do Fascino).

**Situação.** O gabarito pede `Audiometria (ADM, PER, MRO, DEM)` — inclui o momento demissional. O
motor emite audiometria sem `DEM` em ~35 dos 36 cargos comparados. É a divergência de maior alcance
encontrada na sessão, e não estava registrada em nenhuma dívida aberta antes desta comparação.
Replicada de forma independente no TOCTAO (segundo documento, emissor diferente) — descarta acaso
de um gabarito só.

**Prioridade.** Sobre `DT-003EW-02` e `DT-003EW-03` — é o item que muda o documento assinado em
mais linhas.

**Reenquadramento (003.EX).** A leitura original tratava esta DT como divergência clínica
independente. Medida a raiz: é a **terceira manifestação** de `ruido_acima_acao` resolvendo
`Ausente` quando o PGR cita ruído sem quantificar — junto com `DT-003EG-01` (audiometria pelo
motivo errado) e o caso GHE-16 de `D-ARQ-71`. `R-AUD-04` **resolve a saída** (audiometria com
`DEM` sai para todo trabalhador, incondicional) **sem resolver a raiz** — `ruido_acima_acao`
continua indeterminado nos mesmos PGRs, só deixou de ser a única via para `DEM` aparecer.

**Status:** FECHADA em 003.EX por `R-AUD-04` (piso universal, `todo_trabalhador`, NR-07 Anexo II
4.1 `[DERIVADO]` + matriz-precedente `[INTERPRETADO]` — ver `docs/referencia/GABARITO_003EX_audiometria_dem.md`). Fechamento é da manifestação (saída sem `DEM`), não da raiz (`ruido_acima_acao =
Ausente`), que segue viva em `DT-003EG-01`.

**Nota aditiva (003.EZ) — reabertura e fechamento no mesmo movimento, não silenciados.**
`R-AUD-04`, o mecanismo que fechava esta DT, foi `[DEPRECATED — fundamento refutado por
DT-003EY-01, sem sucessora]` (`D-ARQ-81`). Isso **reabriria** esta DT — o `DEM` incondicional que
a fechava deixa de existir — não fosse `D-ARQ-68` cl.5 fechá-la de novo por um caminho diferente
na mesma sessão: `R-AUD-02` passa a declarar `quando_ausente: {presumir_true:
[ruido_acima_acao]}`, e o `DEM` volta a sair, agora pela **presunção protetiva** sobre o
predicado que `DT-003EG-01` e `DT-003EY-01` nomeiam como a raiz — não mais pelo piso
incondicional. Efeito líquido: o `DEM` continua saindo (fechamento mantido), mas a linha carrega
pendência não-bloqueante nomeando o primitivo presumido, e a matriz cai para `PARCIAL` em vez de
`VÁLIDA` — a raiz (`ruido_acima_acao = Ausente`) fica **visível** em vez de absorvida pelo piso.
`DT-003EG-01` é a que rastreia se a raiz em si (o motivo impresso na linha) também se resolve —
ver nota aditiva ali.

### DT-003EW-02 — Periodicidade não impressa no documento `[ABERTA]`

**Origem:** 003.EW, comparação contra o mesmo gabarito de `DT-003EW-01`.

**Situação.** O gabarito escreve `Espirometria (ADM, PER 24 meses, ...)` e
`RX de Tórax OIT (ADM, PER 12 meses, ...)` — o número da periodicidade impresso junto ao momento. O
app imprime só `PER`, sem o número, em 27 cargos para cada exame. Duas causas possíveis, não
distinguidas nesta sessão: a periodicidade calculada é diferente da esperada, ou a regra de
formatação de saída não está sendo aplicada (`PLANO_V1` manda o RX sempre trazer o número). Medir
antes de corrigir — as duas causas pedem correções diferentes. Irmã de `DT-003EC-01`, mesma classe
de defeito de apresentação sobre valor correto (ou não) do motor.

**Status:** ABERTA — medição pendente antes de qualquer correção.

**Nota aditiva (003.EY).** Causa isolada `[MEDIDO — 003.EY]`: é apresentação, não valor do
motor — `documento_matriz.py::_formatar_celula` monta `f"{nome_exibicao} ({momentos})"`, e a
string `periodicidade` não ocorre no arquivo (`git grep -c periodicidade --
agente_medico/superficie/documento_matriz.py` = 0). Das duas causas que esta DT nomeava, é a
segunda — não há caminho de código que já calcule e descarte o número; ele nunca é montado.
Registrar também: a regra de forma de 003.EO (número só aparece quando periodicidade ≠12M,
exceto RX Tórax OIT, que sempre traz) é contrariada em **2853** ocorrências contra **4366**
confirmações no corpus amplo de 003.EY (26 documentos, todos os exames) — sinal forte de que a
regra não sobrevive fora do par Fascino/RESERVA que a originou, não número final: o agregado é
por segmento de célula, e "contraria" só fica bem definido conhecendo a periodicidade real por
exame (que esta DT ainda não resolveu). Refino pendente antes de implementar a formatação.

**Nota aditiva (003.EZ).** Esta DT tem duas facetas que a nota de 003.EY não distinguia por
nome: **leitura** (o instrumento de medição, `medir_audiometria_dem.py`/`parsear_momentos`,
precisa separar a periodicidade colada ao rótulo do momento — ex. `"DEM 12 meses"` — para medir
corretamente) e **escrita** (o app de produção, `documento_matriz.py`, precisa *imprimir* o
número junto ao momento no documento assinado). A faceta de **leitura** foi **RESOLVIDA** na
fatia 0b desta sessão (`parsear_momentos` passa a separar periodicidade colada ao rótulo,
commit `6f2e9f0`) — instrumento de medição, não o app. A faceta de **escrita** (o que esta DT
mede desde a origem: `documento_matriz.py::_formatar_celula` nunca monta o número) **segue
ABERTA** — nenhum código de produção foi tocado nesta sessão.

### DT-003EW-03 — Exames do gabarito ausentes na saída `[ABERTA]`

**Origem:** 003.EW, comparação contra o mesmo gabarito de `DT-003EW-01`.

**Situação.** Carboxihemoglobina ausente em 2 cargos do gabarito e Manganês no sangue ausente em 1.
O caso do manganês liga-se a `DT-003EQ-02` (`Maganês`, grafia do documento, recusado pelo
resolvedor fuzzy). **Achado convergente independente:** a Dra. Carolini anotou à mão, ao lado de
"Encanador", *"risco baixo no pgr para acetona e metiletilcetona"* — e `Metiletilcetona` foi
recusado pelo mesmo fuzzy na mesma rodada (distância 2 de `metil_etil_cetona`, que já tem regra e
indicador biológico cadastrados). Duas rotas de evidência independentes (anotação manual da médica
e transcrição real do TOCTAO) apontando o mesmo agente sob o mesmo obstáculo de vocabulário.

**Status:** ABERTA — mesma decisão de dado de `DT-003EQ-02`, candidata a resolver junto.

### DH-003EW-01 — Aviso de procedência de IA sem teste do caso positivo `[ABERTA — lacuna de cobertura]`

**Origem:** 003.EW fatia 1, teste do aviso de procedência (`web_matriz.py`).

**Situação.** O teste existente cobre só o caso `chamadas_ia == 0` (aviso ausente quando a rota
determinística cobre tudo). Trocar a condição `if cache.chamadas_ia > 0` por `< 0`, ou apagar o
bloco inteiro, não deixa nada vermelho — nenhum teste exercita o caminho em que o aviso **deveria**
aparecer. É justamente o caminho que importa para a rastreabilidade clínica: a matriz veio (parcial
ou totalmente) de transcrição por IA, e o operador precisa ver isso antes de levar o documento para
assinatura (D-ARQ-22, revisão de saída).

**Status:** ABERTA — não-bloqueante (o mecanismo funciona, medido ao vivo no TOCTAO; falta só a
cobertura do caso positivo).

### DH-003EW-02 — Família TOCTAO não medida `[ABERTA — cobertura de extração]`

**Origem:** 003.EW, sanity-check da rota determinística neutralizado experimentalmente pelo
Arquiteto (12/08/2026) contra o TOCTAO.

**Situação.** Com o sanity-check neutralizado, o parser determinístico atravessa o TOCTAO e devolve
18 blocos e 61 cargos — números plausíveis —, mas apenas **3 riscos em todo o documento**, e cargos
truncados na primeira palavra composta (`Auxiliar de`, `Engenheiro`, em vez de `Auxiliar de
Engenharia`, `Engenheiro Civil`). Geometria medida que explica a falha: o rótulo `GRUPO` está em
`x0=57,0`, mas os dados dele estão em `75,0` — 18pt de desalinhamento, geometria inexistente no
Fascino; a banda `FONTE` é instável entre páginas (178,8 · 179,4 · 183,9 · 185,6). **O
sanity-check está correto ao recusar esta família** — sem ele, a matriz sairia com 18 GHEs e 61
cargos e nenhum exame por exposição, com aparência plena de sucesso: o pior modo de falha do
sistema (matriz plausível e errada), evitado por construção.
`[MEDIDO — Arquiteto, 12/08/2026, sandbox Linux: 46,7s, pico 89 MB]`

**Status:** ABERTA — cobertura de extração para uma família nova é sessão própria de medição
(molde D-ARQ-65), não decisão de conduta clínica.

### DH-003EW-03 — Arquivo de configuração gerado por PowerShell nasce com BOM `[ABERTA — higiene de ambiente]`

**Origem:** 003.EW, materialização do `secrets.toml` na máquina do operador.

**Situação.** `Add-Content -Encoding UTF8` (PowerShell 5.1) escreve BOM UTF-8 no início do arquivo.
O parser `toml` (usado por `st.secrets`) carrega o arquivo sem levantar erro, mas a primeira chave
vem com o BOM colado ao nome (`﻿CHAVE_API_GOOGLE`, caractere invisível antes do "C") — então
`st.secrets.get("CHAVE_API_GOOGLE")` devolve vazio, e o app se comporta como se a chave estivesse
ausente: falha silenciosa, sem exceção, sem mensagem. `tomli` (usado em teste) falha explicitamente
sobre o mesmo arquivo, o que é como o problema foi encontrado. Aplica-se a qualquer
`secrets.toml` de deploy gerado por PowerShell no bloco `[auth]` também, não só a
`CHAVE_API_GOOGLE`. Solução medida:
`[System.IO.File]::WriteAllText(caminho, conteudo, New-Object System.Text.UTF8Encoding($false))`
— o `$false` desliga o BOM.

**Status:** ABERTA — higiene de ambiente, não bloqueia nenhum caminho de produção (o `.toml` do
deploy é materializado por `materializar_secrets.py`, não por PowerShell direto).

### DH-003EX-01 — Heurística de forma no extrator do gabarito assume no máximo 2 grupos após "Audiometria" `[ABERTA — higiene de instrumento]`

**Origem:** 003.EX fatia 0, `scripts/medir_audiometria_dem.py::_extrair_linha_audiometria`.

**Situação.** O extrator captura até dois grupos entre parênteses após "Audiometria" — o bastante
para cobrir as duas formas medidas no acervo: `Audiometria (ADM, PER, MRO, DEM)` (SPE 0030, um
grupo) e `Audiometria (12 meses), (ADM, PER, MRO, DEM)` (RESERVA 0028, período + momentos, dois
grupos). É suposição sobre a forma da célula, não estrutura garantida pelo `.docx` — uma célula
com três grupos (ex.: período + faixa + momentos, ou dois exames colados sem separador com o
segundo trazendo dois grupos) quebra em silêncio: o terceiro grupo em diante é ignorado sem
aviso, e nada no instrumento testa esse caso. Forma 1 (período em grupo separado) é dominante nos
RESERVA e inexistente no SPE 0030 — o próximo documento do acervo pode ter uma terceira variação
não antecipada.

**Impacto.** Não-bloqueante para a medição já feita (nenhuma ocorrência de 3+ grupos foi
observada nos três documentos medidos em 003.EX — verificado, não assumido). Candidato a
descoberta-surpresa se o instrumento for reusado em corpus maior sem essa checagem.

**Correção candidata.** Reportar como rótulo não reconhecido — ou como forma anômala explícita —
quando um quarto/terceiro grupo aparece com conteúdo não vazio, em vez de descartá-lo
silenciosamente; teste com célula sintética de 3 grupos que falhe sem a checagem.

**Status:** ABERTA. Não-bloqueante — instrumento de medição, não código de produção clínica.

### DT-003EY-01 — Fundamento de `R-AUD-04` refutado pelo corpus `[FECHADA — D-ARQ-81/D-ARQ-68 cl.5, 003.EZ]`

**Origem:** 003.EY fatia 0, varredura de cobertura de audiometria sobre 23 obras canônicas
(26 arquivos, lista nominal fechada em EMENDA 1 do prompt de sessão).

**Situação.** `R-AUD-04` emite audiometria por `todo_trabalhador` (D-ARQ-66, piso incondicional)
apoiada em matriz-precedente **n=2** (SPE 0030 + RESERVA 0028, ambos 100% de cobertura,
criada em 003.EX). A varredura de 23 obras mede universalidade em **7/23** (6/23 com piso
`n_cargos ≥ 17` — sem o piso, o CJR entra universal com `n=1` e RICCO HETRIN `(1)` com `n=5`,
mesmo peso que um documento de 54 cargos), com distribuição de fração larga entre as
não-universais (`0.200` a `0.984`) — **não** o padrão "40/41 por exceção pontual isolada" que
sustentaria o piso universal mesmo fora do critério estrito. A convergência n=2 de 003.EX é
artefato de amostra: SPE 0030 e RESERVA 0028 são justamente as duas matrizes onde a médica
estendeu audiometria ao administrativo, não uma amostra representativa do acervo.

**Consequência.** O motor superemite audiometria nos cargos administrativos de 16 das 23 obras
medidas (as não-universais).

**Predicado que o corpus indica.** NR-07 Anexo II item 2 — o universo do exame audiométrico é
quem está **acima do nível de ação** conforme informado no PGR, não todo trabalhador. Evidência
documental direta: a anotação `Ruído (abaixo do nível de ação)`, escrita pela própria médica, em
**21 dos 226 cargos** sem audiometria — concentrada em 3 documentos (ENGESEG ESTRUTURAL FILIAL
24.04.25, ENGESEG ESTRUTURAL FILIAL 21.11.24, CMO VARANDAS BUENO).

**Ressalva obrigatória.** Ausência de anotação nos outros 205 cargos sem audiometria não é
negação de exposição — ambíguo ≠ negativo. A leitura do predicado é candidata, não confirmada
cargo a cargo.

**Limite da amostra `[MEDIDO — 003.EY]`.** A refutação cobre **26 de 36 gabaritos-matriz
identificáveis** no acervo. Ficam fora, nomeados: 5 `.pdf`, 4 `.rtf` e 1 `.xlsx` (formatos não
extraídos nesta fatia), mais **11 PCMSO completos e 1 PGR** em `.doc`/`.docx` que podem conter
matriz embutida e não foram inspecionados. Exclusão nomeada não é dado ausente, mas também não é
cobertura: qualquer leitura de `7/23` como "o acervo" está errada.

E o limite que nenhuma amostra maior dentro deste acervo corrige: **todas as 23 obras são
construção civil.** É limitação estrutural do corpus, não de tamanho — a mesma que `R-AUD-04` já
declarava na própria `base_normativa` ("LIMITE: ambos construção civil"). A regra sucessora nasce
com ela; a diferença é que agora está medida e escrita, não herdada em silêncio. Reinspecionar no
1º PGR de saúde ou química (D-ARQ-06).

**Ligação.** Mesma raiz de `DT-003EG-01` (audiometria emitida pelo motivo errado quando a perna
do ruído está bloqueada) — as duas dívidas rastreiam o mesmo predicado indeterminado
(`ruido_acima_acao` quando o PGR cita ruído sem quantificar). São uma dívida só vista por dois
ângulos: lá, o motivo impresso é enganoso; aqui, a emissão em si é a que está em questão.

**Correção candidata.** ID nova com o predicado (`ruido_acima_acao` resolvido ou piso
NR-07-Anexo-II-item-2), `R-AUD-04` `[DEPRECATED — sucedida por R-AUD-05]` com o corpo
preservado (mudança de escopo de aplicação ⇒ ID nova, nunca remover a antiga).

**Status:** FECHADA em 003.EZ, por duas decisões que endereçam as duas metades do problema.
`D-ARQ-81` qualifica o nível 2 de `D-ARQ-22`: precedente de corpus enviesado (aqui, setorial —
todas as 23 obras são construção civil) não amplia universo que a norma já define; refuta
formalmente o fundamento de `R-AUD-04`, que sai `[DEPRECATED — fundamento refutado por
DT-003EY-01, sem sucessora]` — **sem sucessora**, porque não há conduta nova a herdar, há
conduta a retirar (cl.2). O predicado que o corpus indicava (NR-07 Anexo II item 2,
`ruido_acima_acao`) não vira nova regra incondicional — `D-ARQ-68` cl.5 resolve pelo lado
oposto: quando o PGR está silencioso sobre a quantificação do ruído, e a NR-09 (9.4.1/9.4.2) não
obriga a resposta, o motor declara presunção protetiva por primitivo (`R-AUD-01`/`R-AUD-02`,
`quando_ausente: {presumir_true: [ruido_acima_acao]}`) em vez de universalizar por
`todo_trabalhador`. A ressalva "ambíguo ≠ negativo" desta DT é exatamente por que a correção
final não é uma regra incondicional nova — é presunção auditável, com pendência não-bloqueante e
piso `PARCIAL` (nunca `VÁLIDA`), preservando o sinal que a leitura cargo-a-cargo ainda não
confirma.

### DH-003EY-01 — Indexação fixa de célula quebra em tabela com mesclagem `[FECHADA — 003.EZ fatia 0]`

**Origem:** 003.EY fatia 0, `scripts/medir_cobertura_e_forma.py`, ao medir ATZUM (13 colunas
físicas).

**Situação.** Documentos de tabela única com mais de 2 colunas físicas mesclam FUNÇÃO/EXAMES
SOLICITADOS ao longo de várias colunas — `python-docx` repete o mesmo texto em cada coluna do
span de mesclagem. A indexação fixa `celulas[0]`/`celulas[1]` — herdada de
`scripts/medir_audiometria_dem.py` (003.EX) — lê a própria mesclagem de FUNÇÃO como se fosse a
coluna de exames nesses casos: ATZUM (13 colunas) media **0/47** audiometria antes da correção.
Corrigido em `medir_cobertura_e_forma.py` com `_celulas_logicas` (colapsa células adjacentes de
texto idêntico antes de indexar).

**Alcance.** `scripts/medir_audiometria_dem.py` (003.EX) **segue com a indexação fixa, não foi
corrigido** — os dois documentos medidos naquela sessão (SPE 0030: 2 colunas físicas; RESERVA
0028: 4 colunas, mas sem mesclagem que atinja a coluna de exames) têm forma que não expõe o
defeito, então a medição de 003.EX permanece válida. O instrumento continua vulnerável se
reusado em outra família de documento sem essa checagem.

**Correção candidata.** Portar `_celulas_logicas` para `medir_audiometria_dem.py`.

**Status:** FECHADA em 003.EZ fatia 0 (commit `598c19c`) — `_celulas_logicas` migrou para
`medir_audiometria_dem.py`; `medir_cobertura_e_forma.py` passa a importar em vez de manter
cópia própria (D-ARQ-67). Checkpoints de 003.EX reverificados intactos.

### DH-003EY-02 — Binário `universal` sem piso de `n_cargos` `[FECHADA — 003.EZ fatia 0]`

**Origem:** 003.EY fatia 0, agregação da Pergunta A (`fração == 1.0` ⇒ `universal`).

**Situação.** `fração == 1.0` trata `1/1` (CJR ENGENHARIA, um único cargo no documento) e `5/5`
(RICCO HETRIN `(1)`, adendo parcial de 5 cargos) como evidência do mesmo peso que `54/54`
(CMO VARANDAS BUENO). Sem piso declarado, o binário infla a contagem de "documentos universais"
com amostras pequenas demais para confirmar ou refutar universalidade.

**Correção candidata.** Reportar sempre com piso declarado ao lado — nesta sessão, `n_cargos ≥
17` muda o agregado de 7/23 para 6/23. Piso é escolha editorial, não medição; deve ficar
explícito em qualquer citação do número.

**Status:** FECHADA em 003.EZ fatia 0 (commit `dfff654`) — agregado de universalidade passa a
sair sempre com o piso declarado ao lado (`universais_bruto` e `universais_com_piso(N)`, N como
parâmetro), saída de primeira classe do instrumento, não mais cálculo à mão.

### DT-003EZ-01 — Matriz sem nenhuma linha derivada de risco sai `VÁLIDA` `[ABERTA]`

**Origem:** medição 003.EZ fatia 1 (`relatorios/003ez_fascino_rodar.md`), GHE-19 (Vendas).

**Situação.** GHE-19 tem `riscos_resolvidos: (nenhum)` e todos os predicados `False` exceto
`todo_trabalhador`. Não tem pendência alguma, logo `tem_bloqueio` é falso, e
`orquestrador.executar` testa `if not tem_bloqueio → VÁLIDA` **antes** de olhar
`linhas_com_risco` — o GHE sai `VÁLIDA` com **zero** linhas determinadas por risco, carregando
só os incondicionais `R-CLI-01` e `R-PSY-02` `[VERIFICADO — orquestrador.py:110-141]`.

**Alcance da D-ARQ-66 cl.2.** A cláusula foi escrita para impedir que a linha incondicional
promovesse `BLOQUEADA → PARCIAL`, e faz isso: `linhas_com_risco` exclui motivos incondicionais.
Mas ela só é consultada no ramo `elif`, **depois** de `VÁLIDA`. Protege a fronteira
`PARCIAL`/`BLOQUEADA` e **não** a fronteira de `VÁLIDA`. É lacuna de desenho da própria cl.2,
não regressão desta sessão.

**Não introduzida em 003.EZ, exposta por ela** `[VERIFICADO — relatorios/003ex_fascino_rodar_DEPOIS.md, GHE-19 já VÁLIDA]`. O que muda: com `R-AUD-04` ativa, GHE-19 ao menos carregava a
linha de audiometria; agora é matriz assinável, selada `VÁLIDA`, sem uma única linha determinada
por risco.

**Por que importa.** `VÁLIDA` significa, para a revisão de saída, "todo risco determinou sua
conduta". Aqui nenhum determinou. E `riscos_resolvidos: (nenhum)` é ambíguo entre "o PGR não
declara risco para este GHE" e "nada resolveu" — que D-ARQ-13 existe justamente para não
confundir. `D-ARQ-74` não pega: ele barra só `REJEITADO`.

**Correção candidata (não decidida).** Quarto estado, ou `VÁLIDA` condicionada a
`linhas_com_risco` não-vazia. Ambas mudam o contrato do tri-estado (D-ARQ-31) — decisão de
arquitetura própria, não conserto de fatia.

**Emendas de fato (003.FB)** `[MEDIDO — relatorios/003ez_fascino_rodar.md]`. Duas afirmações
desta DT estavam imprecisas e ficam corrigidas aqui, sem alterar a conclusão: (i) *"Não tem
pendência alguma"* é falso — GHE-19 carrega duas pendências `vocabulario_ausente` de
`R-GHE-02` (cargos sem `riscos_implicitos`); o que não há é pendência **bloqueante**, e essas
pendências ocorrem em 19/19 GHEs (41 no total, uma por cargo, artefato de `DT-003EP-01`), logo
não discriminam nada. (ii) A ambiguidade de `riscos_resolvidos: (nenhum)` que esta DT nomeia
está **resolvida no caso medido, no braço ruim**: GHE-19 declara três termos de risco
(`Postural`, `Piso irregular ou em desnível` e um recorte espúrio de `DT-003EQ-01`) e nenhum
resolveu. Resolvida em desenho por `D-ARQ-82`; segue ABERTA até a implementação (003.FC).

**Status:** ABERTA. Não-bloqueante para o merge desta sessão: a conduta emitida está correta, o
que está errado é o selo.

### DT-003FA-01 — Base de `D-ARQ-70` cita a NR-09 por portaria superada `[ABERTA — não-bloqueante]`

**Origem:** sessão 003.FA, ao ler `D-ARQ-70` integral na verificação do prompt da fatia 1.

**Situação.** A **Base** de `D-ARQ-70` registra: *"Literal da NR-09 Anexo I conferido no PDF
oficial (gov.br/trabalho-e-emprego, `nr-09-atualizada-2026.pdf`, **Portaria MTP 426/2021**)"*.
O nome do arquivo é de 2026 e a portaria citada é de 2021 — superada pela **Portaria MTE n.º
105, de 29/01/2026**, achado da 003.EZ. Quando aquela sessão descobriu a mudança da NR-09, o
corpo de `D-ARQ-70` não foi reconciliado; a proveniência ficou apontando para a redação
anterior.

**O que está e o que não está em risco.** O alias ancorado ali é `VMB`/`VCI`
(`vibracao_mao_braco`, `vibracao_corpo_inteiro`), sob `D-ARQ-70` cl.5 — sigla que é literal do
Anexo I da NR-09. A 003.EZ mediu que a NR-09 vigente **tem** Anexo I (Vibração), logo a
expectativa é que o conteúdo sobreviva e o defeito seja de **rótulo de proveniência**. Isso é
expectativa, não medição: ninguém releu o Anexo I vigente atrás das siglas. Enquanto não for
relido, a âncora de `D-ARQ-70` cl.5 está `[INCERTO — conferir VMB/VCI no Anexo I da NR-09
vigente, Portaria MTE 105/2026, texto oficial MTE]`.

**O que a resolução exige.** Reler o Anexo I da NR-09 vigente no texto oficial do MTE,
confirmar (ou não) que `VMB` e `VCI` seguem literais da norma, e corrigir a Base de `D-ARQ-70`
para a portaria vigente. Se as siglas não sobreviverem, o caso deixa de ser rótulo e vira
revisão de alias — aí com efeito de conduta, porque `vibracao_mao_braco` alcança `R-VIB-02` e
`R-AUD-01`.

**Classe.** Mesma de `D-ARQ-69` e da nota 003.FA anexada a ela: proveniência normativa que
envelhece em silêncio porque nada no repositório vigia a citação depois de escrita.

**Status:** ABERTA, não-bloqueante. Não trava produção nem a fila da 003.FA.

### DH-003FB-01 — Detecção de erro factual do Arquiteto depende inteiramente do Diovanni `[ABERTA — higiene de método]`

**Origem:** sessão 003.FB, ao revisar o próprio método após duas correções factuais dentro da
mesma sessão.

**Situação.** O modo de falha dominante e catalogado do projeto é de **conferência** (afirmação
factual × fonte primária), não de julgamento: gate pulado em 003.DP, gate de 003.FA omitindo a
própria `D-ARQ-70` que a sessão ia alterar, a classe "leio a forma, não a prova" com 11+
ocorrências, parser ad-hoc do Arquiteto produzindo gabarito errado, mecanismo-sem-efeito 2× em
003.EW. Em 003.FB houve mais duas: uma fatia de re-medição proposta sem poder de decidir entre
desenhos, e a afirmação de que o orquestrador "não pode ter o dado" quando `RiscoPGR(agente=None)`
já viaja no `GHEPGR`. Em todos os casos quem detectou foi o Diovanni ou uma leitura de código
posterior — nunca a suíte, nunca o ritual.

**Proposta a decidir em sessão META própria.** Conferidor factual por subagente, rodando dentro
da sessão do Arquiteto sobre todo artefato que **crava fato** (D-ARQ, prompt cirúrgico, número do
painel, spec de dado), com três condições: (1) **não emite veredito** — emite achados com arquivo,
âncora e o comando que reproduz, porque "conferido, está ok" é declaração não-auditável da mesma
classe que a `003.DQ` combate, agravada por a ferramenta devolver só a mensagem final do
subagente e nunca o transcript; (2) **prompt fixo e versionado no repo**, genérico, jamais
apontando o que conferir — prompt ajustável por sessão deixa o builder desviar do próprio ponto
cego; (3) o **Crítico não muda**: sessão nova, artefato + barra, `003.DQ` intocada — ele apenas
passa a receber artefato já limpo de erro factual e gasta a sessão nos três itens da barra.

**Discordância registrada, para não se perder.** **Nenhum gate novo.** O gargalo do projeto não é
falta de crítica — são 62 pendências abertas, 3 travando produção, 53/79 slugs sem `termos:` e
divergência medida contra o gabarito humano (003.EW). O ganho pretendido é tirar conferência do
Diovanni, não somar cerimônia; se isto virar um quarto passo de ritual com declaração própria,
terá piorado o projeto.

**Fronteira com `DT-003DX-02`.** O prompt fixo do conferidor é conteúdo do público **Arquiteto**,
que é exatamente a metade ainda não resolvida daquela DT (o público Code já mora em `CLAUDE.md`
versionado). Seria a primeira regra do público Arquiteto a entrar no git.

**Limite de isolamento medido em 003.FB.** Subagente **não** herda o contexto conversacional do
builder — isso é estrutural. Mas alcança as mesmas fontes laterais (memória de projeto do Cowork,
project knowledge, `relatorios/`, prompts da pasta do Cowork), não há tipo de agente com perfil
"sem memória, sem projeto", e o toolset não é removível por chamada. Para o papel de **Crítico** o
isolamento é, portanto, **apenas instrução** — motivo pelo qual a proposta NÃO substitui o
Gauntlet. Para o papel de **conferidor** isso não importa, porque a saída é falsificável por
comando.

**Status:** ABERTA, não-bloqueante. Método, não motor. Nenhuma R-* tocada.

### DH-003FB-02 — Leitura do repo pelo mount do Cowork deixa `.git/index.lock` órfão que trava o Code `[ABERTA — higiene de ambiente]`

**Origem:** sessão 003.FB, entrega A. O Code abriu a sessão encontrando `.git/index.lock`
e o removeu por conta própria, reportando "stale, safe to remove" — tecnicamente correto
(0 bytes, sem processo git vivo), mas é decisão que o método reserva ao Arquiteto:
bloqueador se reporta, não se resolve.

**Causa, que não é do repo.** O lock foi criado pelo **Arquiteto**, não pelo Code: o
`git status` executado pelo Cowork sobre a pasta montada emite
`warning: unable to unlink .git/index.lock: Operation not permitted` — o git do mount cria
o lock e não consegue removê-lo, por permissão do sistema de arquivos montado. O resíduo
fica para quem abrir o repo em seguida no host.

**Consequência.** Toda sessão de Code aberta logo depois de uma leitura do Arquiteto pode
encontrar um lock órfão e ser empurrada a decidir sozinha sobre ele. O incentivo é para o
Code normalizar a remoção — e um lock **não**-órfão (processo git real em curso) removido
por hábito corrompe o índice.

**O que a resolução exige.** Decidir a regra: ou o Arquiteto limpa o lock ao final de cada
leitura, ou o `CLAUDE.md` do repo (público Code) passa a instruir explicitamente
"lock órfão: reportar, nunca remover", ou a leitura do Arquiteto deixa de usar comandos que
tomam o lock (`git status` toma; `git show`/`git log` não). A terceira é a mais barata e a
única que ataca a causa. Ver [[cowork-mount-regras]].

**Status:** ABERTA, não-bloqueante. Ambiente, não motor. Nenhuma R-* tocada.

### DH-003FB-03 — O `PAINEL_ESTADO.md` se declara "vivo" mas seu baseline envelhece por desenho `[ABERTA — higiene de instrumento]`

**Origem:** sessão 003.FB, passo 5 do ritual.

**Situação.** O painel abre com *"Painel vivo, não foto datada. Mostra o estado corrente
medido de disco (git), não estimativa"*, e sua regra de cadência re-tira **apenas** quando um
dos três números clínicos se move, um marco fecha, ou a sessão é META. As duas afirmações
convivem mal: o bloco **Baseline** carrega hash, contagem de suíte e versões de doc, que
mudam a cada sessão **independentemente** dos três números.

**Medido em 003.FB.** O painel declara `main a8bb4d1 · 1137 passed, 6 skipped · PROTOCOLO
v90 · DECISOES v173`. O estado real é `main a48836d · 1147 passed, 6 skipped · PROTOCOLO
v90 · DECISOES v177` — **três sessões de defasagem** (003.FA, 003.FB entregas A e B), com a
contagem de suíte errada em 10 testes. Cada defasagem foi individualmente correta pela regra;
o efeito acumulado não é.

**Por que importa.** Quem lê o painel para saber "onde estamos" lê 1137 como corrente. É erro
silencioso plausível — classe `D-ARQ-22` — no documento cuja única função é ser a leitura
rápida do estado. A 003.FA já registrou a defasagem no fechamento para que a sessão seguinte
não a lesse como esquecimento; 003.FB a registra de novo, maior. O padrão indica desenho, não
descuido.

**Correção candidata (não decidida).** Separar o que envelhece do que não envelhece: os
**três números** seguem re-tirados por evento (regra atual, intacta), e o **Baseline** —
hash, suíte, versões — passa a ser atualizado em todo fechamento, custo marginal ~zero porque
o ritual já mede tudo isso no passo 6. Alternativa: derivar o Baseline por script, como
`INDICE_DARQ.md`, e proibir edição à mão. A segunda é mais fiel à doutrina anti-cache do
projeto e mais cara.

**Status:** ABERTA, não-bloqueante. Instrumento, não motor. Nenhuma R-* tocada.
