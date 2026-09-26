# Pendências clínicas em aberto

Extraído do §11 de `docs/PROTOCOLO_AGENTE_MEDICO.md` em 003.ET (fatia 0), por D-ARQ-63:
o §11 era 58,9% do PROTOCOLO e estourava o nível 1 do gate de abertura. Conteúdo movido
verbatim; nenhuma dívida foi criada, fechada, reenquadrada ou reescrita nesta operação.

Convenção preservada: `DT-*` = dívida técnica/clínica, `DH-*` = dívida de higiene.
O documento-mãe é `docs/PROTOCOLO_AGENTE_MEDICO.md`.

## 11. PENDÊNCIAS CLÍNICAS EM ABERTO

Itens identificados durante a implementação do motor que precisam de validação clínica em sessões CONHECIMENTO futuras com a Dra. Carolini.

> **Estado `DISPENSADA` (convenção, 003.FE).** Dívida pode sair da lista por decisão, não só
> por pagamento. `[DISPENSADA — <motivo>]` marca item medido, real, e deliberadamente não
> endereçado; exige motivo escrito e não reabre sem fato novo. Motivo da convenção: em 29/08/2026
> a lista tinha 73 headers abertos contra 26 fechados, e nenhum estado permitia encerrar item que
> ninguém vai pagar — backlog monotônico por desenho. Não é D-ARQ: é convenção de vocabulário
> deste documento, promovível se virar padrão.

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

### DT-003M-02 — Vocabulário (agentes.yaml) não cobre composição-de-FDS `[(A) PARCIALMENTE RESOLVIDA — 28 slugs novos (19+9), sessões docs/003fg-.../docs/003fh-...; (B) FECHADA por D-ARQ-56, 003.CK]`

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

**(A) parcialmente resolvida (sessão `docs/003fg-validacao-ao-vivo-fatia2b`, 20/09/2026) — sessão de dado, pedido do Diovanni.** 19 slugs novos em `agentes.yaml`, cobrindo os CAS reais das 6 FDS medidas no acervo (`fds_originais/`, validação ao vivo da fatia 2b) que ainda caíam em `vocabulario_ausente`: 8 do Cimento Ciplan (`cimento_portland`, `silicato_tricalcico`, `silicato_dicalcico`, `ferro_aluminato_de_calcio`, `aluminato_tricalcico`, `carbonato_de_calcio`, `oxido_de_magnesio`, `oxido_de_calcio`), 3 da Tinta Acrílica (`oxido_de_ferro_amarelo`, `silicato_de_aluminio_hidratado`, `hidroxido_de_amonia`), 3 do Adesivo PVC Tigre (`copolimero_de_pvc`, `branqueador_optico_fb184` — faltava na 1ª leva desta sessão, corrigido antes do commit) e 6 conservantes/biocidas da Textura Leinertex/Massa Corrida (`benzisotiazolinona`, `mistura_cmit_mit`, `diuron`, `carbendazim`, `n_octil_isotiazolinona`, `aguarras_mineral`). Fonte de `is_carcinogeno_iarc`: IARC Monographs "List of Classifications" (Grupo 1/2A/2B → true; Grupo 3/não avaliado → false), verificado via busca (domínio oficial `monographs.iarc.who.int` bloqueado pelo proxy de egresso desta sessão — cruzado via SDS de fabricante/PubChem/InChem/ChemicalBook). **Nenhum dos 19 é carcinógeno IARC** — achado coerente, não esperado nem forçado. `tem_lt=true` só em `hidroxido_de_amonia` (amônia no Quadro 1, Anexo 11 da NR-15); os demais `false`. **Achado colateral — 2 CAS malformados na FDS real (não do vocabulário):** a FDS da Ciplan declara aluminato tricálcico como `1242-78-3` e a FDS da Leinertex declara N-octil isotiazolinona como `26530-20-2` — ambos FALHAM o dígito verificador (`cas_bem_formado`), defeito de OCR/transcrição do PDF original. Usados os CAS corretos (`12042-78-3`/`26530-20-1`, dígito confere, fonte externa) para o slug; uma FDS real repetindo o CAS malformado continua caindo em `cas_invalido` — comportamento correto do gate (D-ARQ-36 ramo c), não bug, registrado em comentário no `agentes.yaml`. Cobertura CAS movida por `scripts/medir_painel`: **50/80 (62%) → 69/99 (70%)**. Guards de inventário atualizados com reversão nomeada: `test_indice_real_tem_125_entradas`→`test_indice_real_tem_144_entradas` (125→144, +19 slugs, cada um 1 forma sem `termos:`); `test_vigia_pares_fuzzy_chaves_longas` ganhou 1 par novo no gabarito (`silicato_dicalcico`/`silicato_tricalcico`, nenhum com `fuzzy_permitido`, revisado e aceito, mesma classe do par MEK/MBK já existente). Nenhuma `R-*` tocada — (A) é dado, não regra clínica; `materialidade()` já lê a flag do `Componente` (D-ARQ-34 P4), esses 19 slugs ficam prontos pra resolver via `gate_cas` na próxima FDS real que os declarar. **Restam candidatos não cobertos** desta mesma leva de FDS (entradas sem CAS único — "ND"/"NA"/"vários"/segredo industrial — ficam de fora por desenho, não são populáveis por slug) e todo o universo de FDS AINDA não medidas no acervo (as 11 FDS por-cargo do commit `96a15e9` não foram examinadas nesta sessão).

**2ª leva (A) — sessão `docs/003fh-fds-por-cargo`, 20/09/2026, pedido do Diovanni.** Examinadas as 11 FDS reais por-cargo do acervo (commit `96a15e9`) — dedup por hash reduz a 8 documentos distintos: Adesivo PVC Tigre (Almoxarife/Encanador/Montador, MESMA composição já coberta na 1ª leva, nenhum CAS novo), Água Sanitária Zulu (Aux. Serviços Gerais/Serviços Gerais), Cimentcola Interno Quartzolit (Azulejista, cimento Portland já coberto), Desmoldante Concentrado (Carpinteiro, SEM composição declarada — "não apresenta ingredientes que contribuam para o perigo"), Impermeabilizante Asfáltico (Impermeabilizante/páginas 13+ de `FDS PINTOR.pdf`), Eletrodo 60.13 (Montador de Estruturas Metálicas/Soldador). **9 slugs novos**: `hipoclorito_de_sodio`, `carbonato_de_sodio` (Água Sanitária), `asfalto` (Impermeabilizante — **único carcinógeno IARC desta leva**: Grupo 2A/2B, Monografia Vol.103/2013, exposição ocupacional a betume oxidado/duro + emissões), `ferro`, `feldspato`, `silicato_de_potassio`, `bentonita`, `celulose`, `carbonato_de_potassio` (Eletrodo de solda). **Limitação medida:** as páginas 0-11 de `FDS PINTOR.pdf` (produto "BLASCOR", provável tinta) são PDF só-imagem — `pdfplumber` não extrai texto ali, sem composição legível nesta sessão (exigiria OCR, fora de escopo). Cobertura CAS: **69/99 (70%) → 78/108 (72%)**. Detalhe completo: `DECISOES_ARQUITETURAIS.md` v205 (nota de aplicação em `D-ARQ-36`).

**Status:** (A) PARCIALMENTE RESOLVIDA — recorte medido (17 FDS do acervo entre as duas levas) coberto; universo maior de FDS reais segue aberto para sessões futuras conforme medição (nenhuma FDS nova conhecida no acervo no momento; `FDS PINTOR.pdf` págs. 0-11 pendente de OCR). **(B) FECHADA (003.CK, D-ARQ-56, PR #192):** componente sem slug e sem frase-H declarada deixa de travar o GHE — pendência `materialidade_ausente` NÃO-bloqueante (inerte-declarado, R-FDS-06); frase-H não-mapeada mantém bloqueante (conservador-correto, D-ARQ-35). Cluster resolvido: DT-003T-01 fechada (003.CI/CJ), DT-003M-01 fechada (003.CK).

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

**Nota (branch `claude/hopeful-newton-yjv3k7`, 23/09/2026) — forma nova medida: faixa de
vigência.** Porto Araras I e Vila Brasil Escritório trazem `Vigência: 04/2026 – 04/2027` /
`07/2026 – 07/2027`; `resolver_validade` devolve `data = null` e `proposta = null` para a
candidata. Não é silêncio (o RT recebe a candidata explícita e digita a data), mas é mais um
caso da faceta `mm/aaaa`, agora como intervalo. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`

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

**Nota (branch `claude/hopeful-newton-yjv3k7`, 23/09/2026) — classe (4) ganha 2º PGR.** Vila
Brasil Escritório: 4 GHEs que o PGR declara só com risco postural, piso irregular, trânsito ou
violência (DIREÇÃO, VIGILÂNCIA, PLANEJAMENTO, PATRIMÔNIO) recebem no gabarito acuidade visual
(6 cargos) e audiometria (4 cargos); o motor emite só o pacote base e marca os cargos com
`vocabulario_ausente` (sem riscos implícitos). 10 células. Distingue a leitura em aberto da nota
003.ED: aqui o PGR **declara** riscos, e nenhum deles pede esses exames — classe (4), conceito
ausente, não lacuna de vocabulário. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`

**Nota (003.ED).** Classe (2) perdeu a maior fatia: o alias de altura fechou 16 GHEs × 5
exames = 80 células, com cruzamento nominal contra o gabarito sem falso positivo nem falso
negativo. Classe (4) inalterada. Achado novo a medir: **GHE-19 (Vendas) tem `ctx.riscos == []`**
— o gabarito pede Acuidade Visual ali e o motor não tem nada a emitir. Falta distinguir
"o PGR não declara risco para Vendas" de "declara e nada resolveu": a primeira leitura manda
a acuidade para classe (4) (conceito ausente, n=1, não formalizar); a segunda, para classe (2)
(lacuna de vocabulário). `[A MEDIR — não concluir sem medir]`


**Decisão clínica (Diovanni, 23/09/2026) + medição — "o cargo deve ser motorista, tem que ver
na descrição do cargo".** Classe (4) de Vila Brasil, medido no bloco inteiro de cada GHE
`[MEDIDO — mesma branch]`: **DIREÇÃO** (Motorista MG) — a descrição diz "dirigem e manobram
veículos", risco "trânsito" declarado → confirma (acuidade + audiometria, 2 células).
**PATRIMÔNIO** — descrição sem direção, mas risco "Bater contra ou ser atingido por (trânsito) —
deslocamento em via pública" → compatível (2 células). **VIGILÂNCIA** (acuidade, 2 células) e
**PLANEJAMENTO** (acuidade + audiometria, 4 células) — nenhum termo de direção nem de trânsito no
bloco: a hipótese não os explica. Implementação candidata: condução de veículo (descrição do cargo
ou risco de trânsito) → acuidade visual + audiometria; vigia e planejamento seguem classe (4)
abertos.

**Implementação parcial (branch `claude/inspiring-turing-0ylkmk`, 24/09/2026) — `R-PKG-TRANSITO`.**
Sinal escolhido pelo Diovanni entre três medidos: **risco de trânsito declarado**
("Bater contra ou ser atingido por (trânsito)", slug novo `transito_via_publica`, só a frase
completa). Medido nos 3 PGRs pareados: 3/3 GHEs com o risco recebem acuidade + audiometria no
gabarito (DIREÇÃO e PATRIMÔNIO de Vila Brasil, VENDAS do Fascino), 0/58 dos demais. "Ver na
descrição do cargo" acertava só a DIREÇÃO e dava falso positivo por "dirigem"/"conduzir" em 4
GHEs — descartado. **Fecha o achado 003.ED do GHE-19 (Vendas):** o PGR **declara** o risco, e o
termo não resolvia porque o parser colava a legenda "(P × S)" no último risco do bloco —
corrigido (linha que começa na banda GRUPO sem ser categoria encerra o risco; no acervo
determinístico inteiro, só esse risco mudou). Efeito `[MEDIDO — comparar_matriz_gabarito, antes =
worktree main 5977bf5]`: subemissão 13→9 (Vila Brasil), 9→5 (Fascino), Porto Araras inalterado,
zero superemissão nova. 4 testes (`test_pkg_transito.py`), varredura inversa 4/4. **Seguem
abertos na classe (4):** VIGILÂNCIA (acuidade, 2 células) e PLANEJAMENTO (acuidade +
audiometria, 4 células) de Vila Brasil — sem trânsito nem direção no bloco.
### DT-003EB-02 — R-BIO-04 emite indicador biológico onde a matriz humana pede só menção documental em risco baixo `[RESOLVIDA — IMPLEMENTAÇÃO, branch claude/eager-fermat-txbn7h, 24/09/2026: R-BIO-05, só IRRELEVANTE]`

**Origem:** Sessão 003.EB (25/07/2026), mesmo diff acima.

**Situação.** Sob anotação explícita de risco baixo no PGR, a matriz humana solicita apenas **menção documental no PCMSO**, não o indicador biológico em si. R-BIO-04 emitiu 4 indicadores biológicos nesses GHEs do Fascino (GHE-10: acetona_urina, mek_urina; GHE-16: ortocresol_urina, acido_metilhipurico — todos PER 6m).

**Hipótese:** falta um gate de nível de risco no predicado de R-BIO-04 (risco baixo → menção documental, não exame).

**Pergunta para a Dra. Carolini (sessão CONHECIMENTO futura):** o que caracteriza "risco baixo" para fins de dispensa do indicador biológico — a anotação explícita no PGR é suficiente, ou há um limiar quantitativo por trás? A menção documental tem forma própria (texto padrão no PCMSO) ou é livre?

**Status:** ABERTA. Formalização exige sessão CONHECIMENTO com gate D-ARQ-63 antes de alterar R-BIO-04.


**Nota (branch `claude/hopeful-newton-yjv3k7`, 23/09/2026) — dois casos em sentidos opostos.**
Com o alias `Metiletilcetona` (`DT-(sessão claude/hopeful-newton-yjv3k7)-02`), o motor passa a
emitir `mek_urina` para o pintor nos dois PGRs com a grafia no GHE PINTURA. Fascino (gabarito da
Dra. Carolini, anotação "risco baixo no PGR"): o gabarito **não** pede MEK — superemissão desta
DT. Porto Araras I (gabarito da Dra. Patrícia, anotação "risco classificado como baixo"): o
gabarito **pede** `Metil-etil-cetona (PER 6 meses)`. Mesma anotação de risco baixo, condutas
opostas entre as duas médicas. Porto Araras também mostra `acido_butoxiacetico_urina` emitido para
o pintor onde a médica anotou 2-butoxietanol como "irrelevante". A pergunta de método desta DT
fica mais nítida, não resolvida. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`

**Decisão clínica (Diovanni, 23/09/2026): segue a conduta da Dra. Carolini** — risco classificado
como baixo no PGR → indicador biológico **não** é emitido; só menção documental no PCMSO.
Medição de viabilidade `[MEDIDO — mesma branch]`: o nível de risco (P×S →
IRRELEVANTE/BAIXO/MODERADO/ALTO) está na própria linha do agente químico em 100% das linhas
medidas (Fascino 6 BAIXO; Porto Araras 6 BAIXO + 1 IRRELEVANTE; Aurora 5 BAIXO + 2 MODERADO). O
parser **não** extrai esse nível hoje (`RiscoVerbatim` = agente, quantificação, fonte). A
implementação exige: campo de nível na extração (rota determinística e transcritor LLM),
hidratação até `RiscoPGR`, e gate em `R-BIO-04`; mais a forma de saída da "menção documental".
Ainda não implementado.

**Nota (branch `claude/inspiring-turing-0ylkmk`, 24/09/2026).** Metade da extração exigida acima
passa a existir por causa de `DT-003EC-01`: `RiscoPGR.nivel_risco`/`Risco.nivel_risco` são
populados pela rota determinística (família Consciente). Faltam a rota LLM, o gate em `R-BIO-04`
e a forma de saída da "menção documental".

**Resolução (branch `claude/eager-fermat-txbn7h`, 24/09/2026) — `R-BIO-05`, dispensa só em
IRRELEVANTE.** Implementada primeiro como decidido em 23/09 (dispensa em BAIXO e IRRELEVANTE,
menção como observação na linha do cargo) e medida contra os 3 gabaritos antes de entregar
(`comparar_matriz_gabarito`, `main 657ccda` × working tree): superemissão 7→0 (Fascino) e 1→0
(Porto Araras I), mas **subemissão 0→6 (Porto Araras I) e 9→13 (Vila Brasil)**. A nota acima
subestimava a divergência: a Dra. Patrícia pede o indicador com risco BAIXO em **10/10** células
medidas (acetona, tolueno, xileno, MEK, ciclohexanona), não só no MEK de um pintor. Reportado
como bloqueador; **decisão do Diovanni (24/09/2026): dispensa só em IRRELEVANTE**, o único nível
em que as duas médicas concordam (Porto Araras I, 2-butoxietanol do pintor). Efeito final: Porto
Araras superemissão 1→0; Fascino e Vila Brasil idênticos. As 7 células do Fascino (conduta da
Dra. Carolini em risco BAIXO) seguem como superemissão, declarada em R-BIO-05.

Forma de saída: `Observacao` em `MatrizGHE.observacoes`, renderizada na célula do cargo depois
dos exames ("Obs.: risco irrelevante no PGR para <agente> — incluir menção no PCMSO; não
solicitado: <exame>"). Escopo: 42 `R-BIO-04-*` do Quadro 1 (IBE/EE); Quadro 2 fora. Rota LLM
continua sem `nivel_risco` — ali o indicador sai sempre (lado protetivo). NR-07 vigente não
conferida (gov.br negado pela rede) `[A CONFERIR — D-ARQ-69]`. 11 testes
(`test_bio_risco_irrelevante.py`), varredura inversa 14 reversões, 11/11 testes discriminantes.

**Nota (mesma branch, pós-merge do PR #368, 24/09/2026) — `[A CONFERIR]` acima fechado.** NR-07
conferida no PDF fornecido pelo Diovanni (`nr-07-atualizada-2022-1_4.pdf`, cabeçalho até Portaria
MTP 567/2022): o **7.5.12 "b"** torna os exames laboratoriais obrigatórios *"quando houver
exposições ocupacionais acima dos níveis de ação determinados na NR-09 ou se a classificação de
riscos do PGR indicar"* — R-BIO-05 é compatível com a norma. Detalhe e trecho literal em
PROTOCOLO §5.9 (v98).

**Nota (branch `claude/determined-fermi-xxah3h`, 24/09/2026) — Aurora: a Dra. Patrícia dispensa
o indicador em BAIXO.** Matriz do app pós-deploy (rota LLM) × gabarito RQ.61 do Aurora Lago das
Rosas 27.08.26. No GHE 11 (Instalações Hidro-sanitárias) o PGR classifica Acetona como **BAIXO**
(P1×S3) e MEK, Ciclohexanona e THF como **MODERADO**. O gabarito pede MEK, ciclohexanol e THF
(PER 6M) e **omite a acetona**, com anotação manuscrita *"classificação baixo no PGR para
Acetona"* nos 3 cargos. O app emite `Acetona na urina (PER 6 meses)` nos 3 — correto sob R-BIO-05
(só IRRELEVANTE dispensa), superemissão contra o gabarito. É contraexemplo da medição que motivou
"só IRRELEVANTE" ("a Dra. Patrícia pede o indicador em BAIXO em 10/10 células"): a mesma médica,
num PGR posterior, dispensa em BAIXO e anota o motivo. Nenhum químico do Aurora está em
IRRELEVANTE (71 linhas `Químico`: 41 BAIXO, 30 MODERADO), então R-BIO-05 não dispara e nenhuma
observação sai — como esperado. **Não alterado:** o corte BAIXO×IRRELEVANTE é decisão clínica do
Diovanni `[MEDIDO — branch claude/determined-fermi-xxah3h]`.

**Nota (branch `claude/hopeful-ramanujan-rbgh4s`, 25/09/2026) — BAIXO fica condicionado a medição.**
Diovanni pediu a dispensa em BAIXO; reapresentada a medição de 24/09 (Porto Araras I e Vila Brasil
pioram), ele pediu parecer clínico. Parecer: não dispensar em BAIXO sem medição — no Aurora o
próprio PGR marca acetona e xileno como *"Avaliação ainda qualitativa — resultado quantitativo
pendente de medição"*, e sem valor a primeira condição do NR-07 7.5.12 "b" (acima do nível de ação)
não é demonstrável. R-BIO-05 inalterada. Proposta registrada em `D-ARQ-86` (ARQUITETURA PROPOSTA):
medição informada na tela por (GHE, agente) com procedência de laudo, e dispensa em BAIXO só com
medição abaixo do nível de ação. Aguarda ratificação e as questões Q1–Q4 da decisão.

**Nota (mesma branch, 25/09/2026, pós-merge do PR #383) — fatia 1 de `D-ARQ-86` implementada.**
R-BIO-05 dispensa em BAIXO quando há medição do agente abaixo do nível de ação (metade do LT da
NR-15 Anexo 11), informada na tela com laudo ou transcrita do PGR; sem medição, BAIXO emite. 21
agentes; os 7 cancerígenos IARC 1/2A com LT ficam fora (decisão do Diovanni). O conflito entre as
condutas das médicas passa a se resolver por evidência: com laudo abaixo do nível de ação, a
matriz segue o Aurora; sem laudo, segue Porto Araras I e Vila Brasil. Os 3 pares determinísticos
não mudam (sem medição de químico).

### DT-003EC-01 — Matriz humana emite RX Tórax OIT 12M onde R-RX-01 sem-medição prescreve 24M `[RESOLVIDA — IMPLEMENTAÇÃO, branch claude/inspiring-turing-0ylkmk, 24/09/2026: ramo R-RX-01-qual]`

**Nota (mesma branch, 25/09/2026) — 2º GHE do Aurora com dispensa em BAIXO.** Matriz_9 do app ×
gabarito: no GHE 18 PINTURA, a anotação dos 3 cargos diz *"Inserir no Word do PCMSO risco
ocupacional baixo no PGR para Octoato de Cobalto, Thinner Acetona, Thinner Metiletilcetona,
Thinner Tolueno e Xileno"* — todos BAIXO no PGR — e o gabarito não pede ácido metil-hipúrico,
ortocresol, MEK nem acetona. O app emite ácido metil-hipúrico (origem na revisão: `xileno ← PGR
(nível BAIXO) | FDS — componente Xileno do produto Fundo Zarcão`). Exceções no mesmo GHE: pede
t,t-mucônico (benzeno das FDS de aguarrás — cancerígeno, regime do Anexo V) e **cobalto na urina**
apesar de citar o octoato de cobalto na anotação de risco baixo (contradição interna do gabarito).
Somado ao GHE 11: 2 GHEs, 5 agentes do Quadro 1 dispensados em BAIXO pela mesma médica num PGR de
27/08/26. Decisão do Diovanni `[MEDIDO — branch claude/determined-fermi-xxah3h]`.

**Origem:** Sessão 003.EC (26/07/2026), medição do gabarito `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` (Fascino) contra R-RX-01/faixas de PNOS.

**Situação.** O gabarito dá RX Tórax OIT em **12M em 14 GHEs** e **60M em GHE-08 (poeira de madeira)** e **GHE-09 (poeiras respiráveis/metálicas)**. O 60M casa com PNOS/Quadro 2 (faixa "sem avaliação quantitativa" → 60M, já implementada). O **12M NÃO casa com R-RX-01**: 12M é a faixa >100% LEO do Quadro 1 (sílica/asbesto), e "sem avaliação quantitativa" prescreve **24M** `[DERIVADO — NR-7 Anexo III Quadro 1]` — não 12M. O PGR não traz quantificação para esses GHEs.

**Pergunta de método (derivação normativa, D-ARQ-27):** a conduta de 12M no gabarito corresponde a uma leitura de exposição >100% LEO feita por fora do PGR escrito (ex.: conhecimento de campo da Dra. Carolini sobre o canteiro), ou a um critério distinto do Quadro 1 que o protocolo ainda não capturou? Buscar o **método** por trás da conduta, não só resolver os 14 GHEs do caso.

**Resolve de passagem** o pré-registro de DT-003DV-01 (achado 003.DW): 'Poeira respirável' é tratada como **sílica-like** no gabarito (RX 12M/24M, não faixa PNOS), **NÃO como PNOS** — confirma a suspeita registrada em 003.DW sem fechar a lacuna de vocabulário (classe 2 de DT-003EB-01).

**Nota (003.EH)** — a divergência saiu de hipótese para medida. Com o ramo de ausência destravado, o motor emite 24M em 14 GHEs exatamente onde o gabarito dá 12M — os mesmos 14 (GHE-01–05, 07, 10–13, 15–18). A pergunta de método é idêntica, mas agora com contraparte medida dos dois lados, não com um lado vazio. Mantida a norma (24M): supersedir regra derivada de texto literal sobre n=1 empresa reprova em D-ARQ-06 — o gatilho de reabertura segue sendo o 2º PGR atualizado no acervo. Os outros 2 GHEs com RX no gabarito (GHE-08 poeira de madeira, GHE-09 poeiras respiráveis/metálicas, ambos 60M) seguem sem emitir por lacuna de vocabulário — `poeira_nao_classificada` e `fumos_metalicos` não têm chave `termos:` em `agentes.yaml` `[VERIFICADO — 003.EH]`. Classe (2) de DT-003EB-01; sessão de dado própria, com critério de grafia normativa por fonte.

**Correção 003.EJ (não apagar a nota 003.EH acima — D-ARQ-06, registro de erro).** A nota de 003.EH atribui a ausência de RX em GHE-08 e GHE-09 a "lacuna de vocabulário". Medido e derivado em 003.EJ, o diagnóstico é outro: **GHE-08** declara `Poeira de madeira` — agente identificável que não é sílica/asbesto/carvão (fora do Quadro 1, literal) e cujo enquadramento no Quadro 2 depende do rodapé (não sensibilizante, baixa toxicidade); **GHE-09** declara `Poeiras Respiráveis/Metálicas`, fração + categoria sem substância → R-PGR-05. Em nenhum dos dois a ausência de RX é lacuna de vocabulário. Ver DT-003EJ-01 (GHE-08) e a nota de aplicação 003.EJ em R-PGR-05 (GHE-09).

**Nota (sessão atual, branch `claude/festive-gates-soy0fr`) — gatilho de reabertura satisfeito: 2º PGR independente com a mesma divergência.** Comparação nova, PGR(ADENDO) CMO Residencial Aurora Lago das Rosas 27.08.26 × gabarito RQ.61 assinado (Dra. Patrícia Montalvo Moraes — mesma médica do caso-âncora Fascino, empresa e data distintas). `[MEDIDO — PGR(ADENDO)CMO RESIDENCIAL AURORA LAGO DAS ROSAS 27.08.26.pdf]`: o documento não contém nenhuma medição quantitativa (0 ocorrências de `mg/m³`, `dB(A)` ou `ppm` no PDF inteiro; 62 ocorrências do aviso de template "⚠ Avaliação ainda qualitativa... apague este aviso", nunca substituído) — mesma classe do caso-âncora ("PGR não traz quantificação"). `[MEDIDO — MATRIZ DE EXAMES(ADENDO)CMO RESIDENCIAL AURORA LAGO DAS ROSAS 27.08.26.pdf]`: o gabarito assinado prescreve RX Tórax OIT em **12 meses** nos GHEs de sílica sem medição — mesmo valor do caso-âncora Fascino, mesma divergência contra R-RX-01-sem (24M). O app (rota 100% LLM) emite 24M nesses GHEs, coerente com R-RX-01-sem. Isto satisfaz o gatilho de reabertura nomeado acima e na nota 003.EH ("2º PGR atualizado no acervo, não n=1") com uma segunda empresa/PGR independente — mesma médica, mesma conduta conservadora, dois documentos distintos. **Não implementado nesta sessão**: divergência entre medição real (12M, gabarito) e valor esperado da regra (24M, R-RX-01-sem) é bloqueador nomeado — decisão do Arquiteto/Dra. Carolini sobre se "sem medição" deveria rotear a 12M em vez de 24M, não ajuste unilateral de código para bater com o gabarito.

**Status:** ABERTA. Não-bloqueante — nenhuma regra alterada por esta DT; questão de método, agora com gatilho de reabertura satisfeito, para sessão CONHECIMENTO com a Dra. Carolini.

**Nota (branch `claude/hopeful-newton-yjv3k7`, 23/09/2026) — 3º e 4º PGR com a mesma divergência.**
Porto Araras I (24 células) e Vila Brasil Escritório (8 células): motor 24M, gabarito 12M, em todo
GHE onde os dois emitem RX tórax OIT. Os dois gabaritos são assinados pela Dra. Patrícia Montalvo
Moraes. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`. Nada alterado; reforça o gatilho de reabertura já satisfeito.


**Decisão clínica (Diovanni, 23/09/2026) + medição — "12M o motivo deve ser a sílica
qualitativa".** Medido `[MEDIDO — branch claude/hopeful-newton-yjv3k7, sobre main 7dbe93e]`: nos
4 PGRs pareados (Fascino, Aurora, Porto Araras I, Vila Brasil) a sílica é avaliada
**qualitativamente** (matriz P×S AIHA na própria linha — "4 1 BAIXO", "3 2 MODERADO" — com
"avaliação qualitativa — resultado quantitativo pendente de medição"); o motor lê como
`silica_asbesto_sem_medicao` e emite 24M. Em Porto Araras e Vila Brasil, **todo** GHE com RX 24M
no motor declara sílica, e o gabarito dá 12M em 100% deles (27/27 e 8/8); GHEs com poeira não
sílica (madeira, PNOS) saem 60M e batem. **Ressalva medida:** 24M aparece em 15 das 34 matrizes
assinadas do acervo (ENGESEG, GPL R78, Horus, Reserva 0028, Dinâmica, Floramazônia, Flamboyant…),
às vezes junto de 12M na mesma matriz; nenhuma tem PGR completo no acervo para conferir o estado
da sílica. Na Floramazônia, 12M cai nos GHEs de sílica (betoneira, produção, cremalheira) e 24M em
armação e carpintaria — compatível com a hipótese, não prova. **Implementação candidata:** ramo
"sílica com avaliação qualitativa" → 12M, distinto de "sem avaliação" (24M, texto literal do
Anexo III da NR-07), `[INTERPRETADO — conduta das médicas nos 4 pares, decisão do Diovanni]`.
Exige distinguir, na extração, qualitativa × sem avaliação — hoje não distinguido.

**Resolução (branch `claude/inspiring-turing-0ylkmk`, 24/09/2026) — `R-RX-01-qual` implementado.**
Sinal de "avaliação qualitativa" = colunas S·P·NÍVEL DE RISCO preenchidas na linha do risco
(matriz P×S). Extração: `RiscoVerbatim.avaliacao_qualitativa` (banda calibrada por bloco em
`parser_familia_consciente`, 587/587 linhas de risco capturadas nos 3 PGRs da família) →
`RiscoPGR.nivel_risco` (`hidratacao.parsear_nivel_risco`; "NÃO DEFINIDO" = não avaliado, sem
pendência; texto não reconhecido = `avaliacao_qualitativa_nao_parseada` não-bloqueante) →
`Risco.nivel_risco` (Fase A) → primitivo `silica_qualitativa`, disjunto de
`silica_asbesto_sem_medicao`. Regra `R-RX-01-qual`: 12M constante `[adm, per, MR, dem]`,
`[INTERPRETADO — prioridade na revisão de saída]`. 9 testes novos
(`test_rx_silica_qualitativa.py`), varredura inversa 11 reversões / 9 testes, todas
discriminantes. Efeito medido `[MEDIDO — comparar_matriz_gabarito, antes = worktree main
cadcd33]`: divergência RX 24M×12M **27 → 0** (Porto Araras I), **8 → 0** (Vila Brasil),
**31 → 0** (Fascino); nenhuma outra célula mudou nos três pares.
**Fica aberto, declarado:** (a) asbesto qualitativo segue 24M — sem caso nem decisão; (b) rotas
LLM e card não extraem a avaliação (`avaliacao_qualitativa=""`), então PGR que não é da família
Consciente segue 24M para sílica — Aurora Lago das Rosas passa pela rota LLM e não foi medido
aqui `[A MEDIR]`; (c) conferência do texto vigente do Quadro 1 exigida por D-ARQ-69 não
refeita nesta sessão (`www.gov.br` negado pela política de rede) — vale a de 003.EH `[A CONFERIR]`.
**Nota (branch `claude/eager-fermat-txbn7h`, 24/09/2026) — item (c) fechado.** Quadro 1 do Anexo III
conferido no PDF da NR-07 fornecido pelo Diovanni (cabeçalho até Portaria MTP 567/2022): mesmos
dois ramos lidos em 003.EH, sem ramo qualitativo. Detalhe em PROTOCOLO §5.4 (v98).
**Nota (mesma branch, 24/09/2026) — item (b) parcialmente fechado.** A rota LLM passa a extrair a
avaliação nos PGRs de escala P×S (5 do acervo, 109 blocos); nos de escore somado segue ausente,
por guarda determinística — ver `DT-(sessão claude/eager-fermat-txbn7h)-01`. Rota card segue sem.
**Nota (branch `claude/determined-fermi-xxah3h`, 24/09/2026) — `[A MEDIR]` da rota LLM fechado
no Aurora.** Matriz gerada no app pós-deploy de `main c1b760e` (Gemini, prompt com regra 6b) ×
gabarito da Dra. Patrícia: RX Tórax OIT **PER 12 meses** exatamente nos GHEs 03, 05, 08, 13, 14,
15, 16, 18 e 22 (27 cargos), **60 meses** nos GHEs 01, 02, 04, 06, 07, 09, 10, 11, 12 e 21, sem RX
em 17, 19 e 20 — **22/22 GHEs e 59/59 cargos idênticos ao gabarito** na periodicidade do RX. O
PGR não tem medição quantitativa, então o 12M só pode vir de `R-RX-01-qual`: o Gemini devolveu o
nível P×S nas linhas de sílica e a guarda de escala o aceitou. A antiga divergência 24M×12M do
Aurora (nota da branch `claude/festive-gates-soy0fr` acima) está fechada.

### DT-(sessão claude/eager-fermat-txbn7h)-01 — PGRs de escore somado (Trivial…Intolerável) não têm nível P×S: R-RX-01-qual e R-BIO-05 não se aplicam `[ABERTA — decisão clínica]`

**Origem.** Implementação da extração do nível na rota LLM (24/09/2026). Medido nos 17 PGRs do
acervo que caem na rota LLM: 5 usam a matriz P×S (Irrelevante/Baixo/Moderado/Alto/Crítico,
legenda em 100% dos blocos) e 12 usam escore somado multifatorial com classes
Trivial/Tolerável/Moderado/Substancial/Intolerável (Viverde V02, Vistamerica Ver.02, Seconci
REV3/REV4, AURO, ALT T65, EURO Setor C, CMO Ver.02 e os PCMSO Vistamerica/R78/Envolt). Nesses 12
o padrão S·P·NÍVEL do parser casaria 13–65 falsos níveis por PGR (ex.: "… 5 40 Moderado", onde
40 é escore e Moderado é classe de outra escala) — por isso a guarda descarta o nível fora da
escala P×S.

**Pergunta clínica.** As decisões de R-RX-01-qual (sílica qualitativa → RX 12M) e R-BIO-05
(IRRELEVANTE dispensa IBE/EE) foram tomadas sobre a escala P×S. Valem para a escala de escore?
Em particular: (1) sílica com classificação de escore declarada conta como "avaliação
qualitativa" para o RX 12M? (2) "Trivial" equivale a "Irrelevante" para dispensar o indicador?
Sem decisão, a rota segue o lado protetivo: RX 24M (R-RX-01-sem) e indicador emitido.

**Status:** ABERTA. Não-bloqueante.

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

**Situação.** `.gitignore:42` ignora `relatorios/` inteiro (`git ls-files relatorios/` = vazio).
O diff motor×gabarito é o instrumento que pauta a fila desde D-ARQ-62, e nada em `git log`
denuncia um relatório vencido. Consequência medida: o último diff completo era de 003.EB
(`6f29928`) e envelheceu 4 sessões — 003.EC/ED/EE/EF mudaram o motor sem que a evidência fosse
re-tirada; a fila de 003.EG chegou a ser pautada contra ele. Mesma classe de DT-003DX-02 (regra
do gate fora do git).

**Correção candidata.** Versionar o sumário do diff (contagens + achados), mantendo o relatório
bruto ignorado — o sumário é pequeno, revisável em PR, e denuncia idade por si; o relatório
bruto continua grande e reproduzível sob demanda.

**Status:** ABERTA. Não-bloqueante.

**Reincidência medida (04/09/2026, sessão 003.FI) e endereçada em parte (003.FJ).** A varredura de
dado pessoal que fechou `DH-003FH-02` e abriu `DH-003FI-01` rodou de `/tmp` num container remoto —
`varrer.py` (4.669 B) e `passe3.py` (2.979 B) — e morreria com ele. Era a mesma classe desta DH:
`DH-003FE-01` promete que a cláusula de reabertura é testável, e sem instrumento versionado a
promessa não se cumpre.

**Pago para este instrumento, não para a classe.** 003.FJ versiona
`scripts/varrer_acervo_lgpd.py` com `tests/test_varrer_acervo_lgpd.py` (**30 testes** @ `3fb98e2`, reversão
nomeada cada um, mais o portão `tests/test_cobertura_varrer_acervo.py` que trava **100% de
cobertura** do script). Foram 10 na entrega inicial (`4c86f18`), 13 no
1º gap (`cc62333`, destino do texto extraído), 14 no 3º (`9b0d496`, exclusão medida em vez de
tamanho de lista), 16 no 4º (`4d85c35`, cinco classes coletadas que nenhuma saída lia) 19 no 5º
(`b4580d5`, os três ramos de falha de `varrer()`) 21 no 6º (`dc77b28`, dois dos três ramos de
`extrair_metadata_autoria`) e 30 + portão no fecho de classe (`3fb98e2`). **A DH segue ABERTA:** o diff motor×gabarito, que é o instrumento original desta dívida,
continua em `relatorios/`, ignorado pelo `.gitignore:42`. Um instrumento a menos fora do git não
fecha a dívida de todos eles.

**Correção de âncora (10/09/2026).** A `Situação` e a nota acima citavam `.gitignore:26`; a entrada
`relatorios/` está na **linha 42** — a 26 é linha de comentário. A âncora vinha propagada desde
003.EG sem re-medição, e o mesmo erro estava no bloco 003.FJ de `HISTORICO_OPERACIONAL.md`. Nada
mais da DH muda: `git ls-files relatorios/` segue vazio e a DH segue **ABERTA**.

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

### DT-003EJ-01 — `Poeira de madeira` é agente identificável fora dos dois quadros do Anexo III `[RESOLVIDA — R-RX-03/R-ESP-03, sessão atual]`

**Origem:** 003.EJ, derivação da ausência de RX em GHE-08 (Carpintaria) do Fascino.

**Situação.** O PGR declara `Poeira de madeira` — diferente de `Poeira respirável`, é agente identificável e admitiria slug próprio. Mas: (a) não é sílica, asbesto nem carvão mineral → fora do Quadro 1 `[DERIVADO — literal do Quadro 1]`; (b) o Quadro 2 exige, pelo rodapé, material não sensibilizante e de baixa toxicidade — poeira de madeira é sensibilizante respiratório reconhecido e há classificação de carcinogenicidade para poeira de madeira `[INCERTO — não conferido em fonte primária nesta sessão; a lista IARC não é capturável por fetch, conferir no monograph oficial antes de cravar]`. Se (b) se confirmar, madeira **não é PNOS** e fica fora dos dois quadros → sem RX pelo Anexo III, e sem espirometria pelo 3.1 (não é poeira mineral; cai no 3.2, condicionado a sinais/sintomas, fora do motor por D-ARQ-09).

**Consequência.** O RX 60M que a matriz humana prescreve em GHE-08 fica sem âncora nos dois quadros — mesma classe de DT-003EC-01, e o gatilho de reabertura é o mesmo (2º PGR atualizado no acervo, não n=1).

**O que a resolução exige.** Conferir a classificação de carcinogenicidade e de sensibilização da poeira de madeira em fonte primária; decidir se madeira ganha slug próprio com regime próprio ou permanece `vocabulario_ausente` honesto. Não-bloqueante: hoje o motor não emite, que é o comportamento correto sob a derivação acima.

**Nota (sessão atual, branch `claude/festive-gates-soy0fr`) — gatilho de reabertura satisfeito + faceta (b) parcialmente confirmada.** Comparação nova, PGR(ADENDO) CMO Residencial Aurora Lago das Rosas 27.08.26 (matriz do app × gabarito RQ.61 assinado pela Dra. Patrícia Montalvo Moraes) declara `Poeira de madeira` em **GHE 04 - Carpintaria** — mesma denominação de cargo do caso-âncora original (GHE-08 Carpintaria, Fascino). É o **2º PGR do acervo** com essa ocorrência, satisfazendo o gatilho de reabertura já nomeado acima. `[MEDIDO — PGR(ADENDO) CMO RESIDENCIAL AURORA LAGO DAS ROSAS 27.08.26.pdf, página 30]`: o próprio PGR bruto lista, na coluna "Agravos à Saúde" da linha de `Poeira de madeira`, **"adenocarcinoma das vias respiratórias superiores"** — o elaborador já registra o efeito carcinogênico característico, sem que o motor hoje o capture. Metade da faceta (b) agora tem fonte primária: IARC Monographs Volume 62 (1995), *Wood Dust and Formaldehyde*, classifica pó de madeira em **Grupo 1** (carcinogênico para humanos, evidência suficiente em humanos), reafirmado no Volume 100C (2012), *Arsenic, Metals, Fibres, and Dusts* `[DERIVADO — IARC Monographs, consulta desta sessão; NÃO é gov.br/MTE nem Fundacentro — a NR-07/NHO brasileiras não têm lista própria de carcinógenos, remetem ao Anexo V; sinalizar a fonte como internacional se isso virar `is_carcinogeno_iarc: true` em `agentes.yaml`]`. A faceta de **sensibilização respiratória** (asma ocupacional por poeiras de madeira, ex. cedro/plicatic acid) segue `[INCERTO — não conferido em fonte primária nesta sessão]`. A decisão em aberto não muda: carcinogenicidade confirmada não define sozinha o regime (Quadro 1 do Anexo III é fechado a sílica/asbesto/carvão mineral por texto literal; carcinógeno fora desses três agentes vai para regime próprio do Anexo V, não para R-RX-01) — segue exigindo decisão do Arquiteto sobre slug próprio × regime, não implementado nesta sessão.

**Nota (mesma sessão, branch `claude/festive-gates-soy0fr`) — periodicidade do RX deixa de ser amostra única (n=1 → n=2), mesmo valor.** `[MEDIDO — MATRIZ DE EXAMES(ADENDO)CMO RESIDENCIAL AURORA LAGO DAS ROSAS 27.08.26.pdf, página 3]`: o gabarito assinado (Dra. Patrícia Montalvo Moraes) prescreve, para os 3 cargos do GHE 04 - Carpintaria (Carpinteiro, Meio Oficial de Carpinteiro, Servente), **RX de Tórax OIT (ADM, PER 60 meses, MRO, DEM)** — o mesmo valor do caso-âncora original (GHE-08 Carpintaria, Fascino, também 60M). Duas PGRs independentes, mesma médica, mesmo cargo (Carpintaria), mesmo número: deixa de ser amostra única para propor 60M como periodicidade do eventual slug `poeira_de_madeira`, se e quando o Arquiteto decidir por slug próprio.

Duas ressalvas medidas, não decisivas para a leitura acima mas registradas por rigor:

1. **Réplica não é limpa 1:1.** O PGR bruto da Aurora (página 30) declara, no mesmo bloco de risco do GHE-04, **duas linhas químicas distintas** — `Poeira de madeira` e `Poeira respirável` (esta última é `fracao_sem_agente`, D-ARQ-83, sem substância própria) — coexistindo. O caso-âncora do Fascino (GHE-08) tinha só `Poeira de madeira`, isolada. O co-occurrence na Aurora não muda a leitura (o caso isolado do Fascino já bate em 60M sozinho), mas os dois casos não são réplicas idênticas.
2. **Achado novo, faceta ainda não nomeada.** O mesmo gabarito prescreve Espirometria (ADM, PER 24 meses, MRO, DEM) para o mesmo GHE-04 — mas `R-ESP-02` (item 3.1, disparo incondicional) é ancorado em **poeira mineral** (sílica/asbesto/PNOS); poeira de madeira é orgânica, não mineral, e não está no escopo de substância de `R-ESP-02` como especificado hoje. Se a prescrição da Dra. Patrícia for tomada ao pé da letra, o regime do slug novo precisaria decidir também a espirometria, não só o RX — pergunta em aberto, não investigada além desta observação.

**Resolução (mesma sessão, branch `claude/festive-gates-soy0fr`).** Decisão tomada pelo Diovanni: slug próprio, `poeira_de_madeira` em `agentes.yaml` (`is_carcinogeno_iarc: true`, IARC Grupo 1). Regime materializado em duas regras novas — `R-RX-03` (RX 60M) e `R-ESP-03` (Espirometria 24M, resolve de passagem a ressalva 2 acima) — ambas `[INTERPRETADO]`, ancoradas nos 2 PGRs medidos (Fascino GHE-08 + Aurora GHE-04), não em texto normativo brasileiro (que não cobre o agente). Autorização explícita: a implementação só avançou sem passar por sessão CONHECIMENTO com a Dra. Carolini porque o Diovanni confirmou que a validação humana de toda matriz antes de sair para o cliente é **reconferência linha a linha**, não sign-off superficial — o risco de uma regra `[INTERPRETADO]` errada não sai do app sem ser pega. A ressalva 1 (co-occurrence com `Poeira respirável`/`fracao_sem_agente` na Aurora) não afeta a implementação — `poeira_de_madeira` resolve por identidade própria, independente do que mais o GHE declara. Sensibilização respiratória (item (b) original) segue `[INCERTO — não conferido em fonte primária]`, registrado em `agentes.yaml`; não bloqueia porque o regime de R-RX-03/R-ESP-03 não depende dela.

**Status:** RESOLVIDA.


**Nota (branch `claude/hopeful-newton-yjv3k7`, 23/09/2026) — grafia `Poeira da madeira` não
resolve.** Porto Araras I, GHE CARPINTARIA: o PGR escreve `Poeira da madeira` (com "da").
`fuzzy_recusado` — distância 1 de `poeira_de_madeira`, slug fora da allowlist `fuzzy_permitido`
(D-ARQ-64). O gabarito pede espirometria e RX tórax OIT para carpinteiro e meio oficial (4 células)
e o motor não emite, com a pendência visível. Candidato: alias `poeira da madeira` em `termos:` de
`poeira_de_madeira` (forma, mesma classe de 003.FH/003.FL), não implementado. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`
**Implementado (mesma branch, pós-merge do PR #361):** `termos: ["Poeira da madeira"]` em
`poeira_de_madeira`; resolve `EXATA`. Na remedição, carpinteiro e meio oficial de Porto Araras
batem com o gabarito (espirometria e RX tórax OIT).
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

**Nota (branch `claude/determined-fermi-xxah3h`, 25/09/2026) — 2º caso real, Aurora.** O PGR do
Aurora Lago das Rosas traz `Químico Manganês — Fumos e gases de soldagem`, nível MODERADO, no GHE
16 SERRALHERIA; o gabarito da Dra. Patrícia pede `Manganês no sangue (ADM, PER 6 meses, MRO)` aos
3 cargos, e o app não emite nada. Aqui o agente resolve (`manganes`, CAS 7439-96-5) — a lacuna é
só a de materialização descrita acima: `R-BIO-03` `[VALIDADO]` no PROTOCOLO, sem entrada em
`regras.yaml`, sem slug de exame em `exames.yaml` `[VERIFICADO — grep, mesma data]`.

**Nota (mesma branch, pós-merge do PR #376, 25/09/2026) — parágrafo R-BIO-03 fechado.** `R-BIO-03`
materializada: regra em `regras.yaml` e slug `manganes_sangue` em `exames.yaml` (PROTOCOLO v101).
O restante desta DT continua ABERTO: `R-CLI-02`/`R-CLI-03` (clínico semestral) seguem só em texto, e
o Fascino segue sem resolver manganês pela grafia "Maganês" (DT-003EQ-02). Base NR-15 de R-BIO-03
conferida: Anexo 12, "Manganês e seus compostos", item 7 (PROTOCOLO v102) — o mesmo item sustenta o
clínico semestral de R-CLI-03.

**Nota (mesma branch, pós-merge do PR #377, 25/09/2026) — R-CLI-03 materializada; R-CLI-02 bloqueada
por medição.** `R-CLI-03` entra em `regras.yaml` (clínico 6M para Mn, NR-15 Anexo 12 item 7).
`R-CLI-02` foi implementada e medida: nos 3 pares determinísticos, +5 divergências de
periodicidade (clínico 6M onde a Dra. Patrícia pede 12M — Porto Araras I GHE-13/14, Vila Brasil
GHE-23/26, todos com agentes do Anexo I em BAIXO/IRRELEVANTE), nenhuma corrigida — retirada. No
Aurora a mesma médica pede 6M nos GHEs 11 (Quadro 1 MODERADO), 16 (Mn), 18/22 (benzeno) e 21
(tricloroetileno). Decisão clínica do Diovanni: qual gatilho do semestral (Mn / cancerígeno / nível
MODERADO+). Fascino (armador/serralheiro 6M) segue dependente de DT-003EQ-02 ("Maganês").

**Nota (branch `claude/jolly-wozniak-iz0ley`, 26/09/2026) — R-CLI-05 sucede R-CLI-02; Serralheria do
Fascino resolvida.** Gatilho decidido sob D-ARQ-22 (nível 2, matriz do Aurora): cancerígeno IARC 1/2A
com indicador biológico, ou agente com indicador biológico MODERADO+ (PROTOCOLO v106). DT-003EQ-02
fechada pelo alias `Maganês`: Fascino GHE-17 em 6M, igual ao gabarito. **Resta aberto:** Fascino
GHE-09 (Armação), 6M no gabarito sem manganês nem agente do Anexo I no PGR.

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

### DT-003EQ-02 — `Maganês` recusado pelo fuzzy: custo clínico do D-ARQ-64 medido `[FECHADA — branch claude/jolly-wozniak-iz0ley, 26/09/2026]`

**Origem:** 003.EQ, rodada real do Fascino.

**Situação.** O PGR do Fascino escreve `Maganês` (typo de Manganês). O resolvedor encontra `manganes` a distância 1, mas o slug é carregado (fora da allowlist) → `fuzzy_recusado`, pendência não-bloqueante, agente não resolvido. D-ARQ-64 está operando exatamente como desenhado — o veto de resultado sobre slug crítico é o comportamento correto, e afrouxá-lo reabriria a classe `Silício`→`silica`.

**Custo real.** Exposição a manganês declarada no documento não chega ao motor, e R-BIO-03/R-CLI-03 não disparam. Casa com DT-003EO-03 (clínico semestral do Mn sem alcance) e com a nota de DT-003EP-01 (`soldador` sem resolver).

**Caminho candidato.** Alias medido sob D-ARQ-70 (grafia de corpus + fonte dupla + teste anti-FP) — `Maganês` é grafia medida em documento real, não hipótese. Não mexer na allowlist: `manganes` é slug carregado por definição.

**Fechamento (branch `claude/jolly-wozniak-iz0ley`, 26/09/2026, decisão do Diovanni).** Alias
`termos: ["Maganês"]` em `manganes` (D-ARQ-70 Tier 1-C): 1 ocorrência medida, p. 82 do PGR do
Fascino, GHE 17 SERRALHERIA; âncora no literal "Manganês e seus compostos" da NR-15 Anexo 12.
Allowlist intocada. Medido nos 3 pares (`main` × árvore): Fascino GHE-17 ganha clínico 6M e
manganês no sangue, iguais ao gabarito; Porto Araras I e Vila Brasil idênticos. **Anti-FP (cl.1.iv)
não virou teste:** "Magnésio"/"Magnesita" não resolvem para `manganes` nem com `fuzzy_permitido`
ligado (distância 3 e 4), então o teste não teria reversão que o matasse (CLAUDE.md). O
deslocamento de slug fica coberto pelo teste de resolução exata.

**Status:** FECHADA.

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

**Status:** ABERTA — faceta de leitura RESOLVIDA (003.EZ); faceta de escrita IMPLEMENTADA em
003.FE apos o refino que esta DT exigia (ver nota aditiva 003.FE abaixo). Segue ABERTA pelos
4% residuais de 2026, nao investigados nominalmente.

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

**Nota aditiva (003.FE) — o refino exigido foi feito; a regra e da convencao corrente.**
`[MEDIDO — 29/08/2026, 28 documentos MATRIZ* de matrizes_originais/, instrumento scripts/medir_cobertura_e_forma.py com a correcao 6f2e9f0 aplicada]`

A nota de 003.EY registrava 2853 contradicoes contra 4366 confirmacoes e concluia que a regra
"nao sobrevive fora do par Fascino/RESERVA que a originou". A remedicao devolve **4281 confirmam
/ 1805 contrariam** — e o agregado enganava, porque a contradicao **nao esta distribuida**.
Por ano do documento:

| Ano | Docs | Confirma | Contraria | % contra |
|---|---|---|---|---|
| 2026 | 10 | 2896 | 122 | **4,0%** |
| 2025 | 11 | 1323 | 1681 | **55,9%** |

O bucket 2025 inclui os dois CONSCIENTE RESERVA 0028, reatribuidos de "sem data no nome" para
04/2025 pela tabela de docs/referencia/GABARITO_003EX_audiometria_dem.md.

A regra de 003.EO descreve a **convencao corrente do escritorio**, nao uma invariante do acervo
historico. As contradicoes de 2025 sao a forma antiga — 542 ocorrencias de `grupo_separado`
no corpus, do tipo "Audiometria (12 meses), (ADM, PER...)". Como o emissor produz documento
**novo**, reproduzir a convencao abandonada nao e requisito, e a implementacao de `deed9f6`
esta correta para o que o app deve emitir.

**Nao fecha esta DT:** os 4% residuais de 2026 (122 ocorrencias) nao foram investigados
nominalmente `[INTERPRETADO — prioridade na revisao de saida]`. Corte por documento e ressalvas
em docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md.

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

### DT-003EZ-01 — Matriz sem nenhuma linha derivada de risco sai `VÁLIDA` `[FECHADA — 003.FC]`

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

**Resolução (003.FC).** Selo de `D-ARQ-82` implementado: `RiscoPGR.causa_nao_resolucao`
(cl.3), `CAUSAS_ACERTO_NAO_RESOLUCAO` fechada no orquestrador (cl.2, emendada nesta
sessão) e o conjunto `not tem_lacuna` no gate de `VÁLIDA` (cl.1). Medido no Fascino:
**3 VÁLIDA → 0** (GHE-14 e GHE-16 → PARCIAL, GHE-19 → BLOQUEADA), com o invariante
confirmado de que nenhum GHE fora de {14,16,19} se moveu.

**Status:** FECHADA em 003.FC. A conduta emitida sempre esteve correta; o que estava
errado era o selo — corrigido pela implementação acima.

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

### DH-003FB-01 — Detecção de erro factual do Arquiteto depende inteiramente do Diovanni `[FECHADA — 003.FD]`

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
versionado). [CORRIGIDO — 003.FD-E: a redação original desta linha dizia "Seria a primeira regra do público Arquiteto a entrar no git". Falso — `/kickoff` (D-ARQ-26) está sob git desde 0dd0449, sessão 002.U. O que era inédito não é a presença desse público no git, e sim a entrada da REGRA DE CADÊNCIA ao lado do instrumento, o que D-ARQ-84 fez. Erro achado pelo Gauntlet ao julgar D-ARQ-84, que havia herdado esta afirmação sem conferir.]

**Limite de isolamento medido em 003.FB.** Subagente **não** herda o contexto conversacional do
builder — isso é estrutural. Mas alcança as mesmas fontes laterais (memória de projeto do Cowork,
project knowledge, `relatorios/`, prompts da pasta do Cowork), não há tipo de agente com perfil
"sem memória, sem projeto", e o toolset não é removível por chamada. Para o papel de **Crítico** o
isolamento é, portanto, **apenas instrução** — motivo pelo qual a proposta NÃO substitui o
Gauntlet. Para o papel de **conferidor** isso não importa, porque a saída é falsificável por
comando.

**Instrumento entregue e testado com gabarito (003.FB, 20/08/2026).** As duas skills existem e
estão versionadas: `.claude/skills/conferir/` (conferidor factual) e `.claude/skills/critico/`
(Gauntlet). A **decisão de cadência — quando cada uma é obrigatória — segue ABERTA** e é o objeto
desta dívida: instrumento entregue não é regra adotada, e instituir gate novo por baixo do pano
seria o oposto do que esta DT propõe. Precedente da separação: `D-ARQ-63` peça 1 (gerador de
índice entregue, decisão registrada junto).

Resultado medido dos três testes `[MEDIDO — 003.FB, gabarito fechado antes da execução]`:

- **`/conferir`, artefato com 6 defeitos plantados (4 reais de 003.FB + 2 fabricados): 5 pegos.**
  Além do gabarito, achou um defeito não plantado e não percebido pelo Arquiteto — literal de
  `Pendencia` omitindo o campo obrigatório `motivo`. Na âncora de linha foi além do previsto
  (identificou que a linha citada era o *título* do bloco, não seu fim, e que os dois pontos de
  inserção do artefato não coincidiam entre si).
- **O defeito que escapou foi uma contagem de uso citada de passagem**, fora do tema central do
  artefato, enquanto todas as contagens do tema central foram pegas. Causa de desenho
  identificada: a regra original mandava **não** listar os `CONFERE`, o que tornava impossível
  distinguir "afirmação conferida" de "afirmação nunca extraída". Corrigido antes do commit — a
  skill passa a exigir inventário de 100% das afirmações com status de uma palavra, detalhando só
  `DIVERGE`/`NÃO VERIFICÁVEL`, e a recontar toda contagem inclusive as incidentais.
- **`/critico`, artefato deliberadamente ruim: REJEITA**, com gate declarado e eixo derivado
  corretamente vazio (o artefato não citava D-ARQ alguma — registrado como gap). O maior gap que
  apontou foi **melhor que o do gabarito**: em vez da não-universalidade (o defeito óbvio, que
  também identificou), nomeou que presumir `silica` para fração não identificada contradiz a nota
  003.EJ de `R-PGR-05`, quebra `test_termos_silicato_e_poeira_nao_resolvem_para_silica` — teste
  existente no repo — e reabre por fiat de ARQUITETURA uma pendência que o protocolo mantém aberta
  para CONHECIMENTO (`DT-002I-01`).
- **`/critico` sobre `D-ARQ-82` real: APROVA** — ver "Gate de fechamento" no bloco 003.FB do
  HISTORICO.
- **Terceira correção, comum às duas:** no teste, o Code redirecionou saída para arquivo, percebeu
  e desfez. `allowed-tools` não barra `>` dentro de comando permitido; a proibição de escrever e
  redirecionar passou a constar no corpo das duas skills.

**Resolução (003.FD).** Cadência decidida em `D-ARQ-84`: `/conferir` obrigatório sobre artefato que crava fato (lista fechada de 5 tipos), **sem declaração ritual nova** — a evidência é o relatório falsificável, não um selo; `/critico` inalterado. A discordância registrada acima ("nenhum gate novo") é a razão da cl.2, não uma ressalva vencida por ela. O que a decisão **não** resolve: o isolamento do subagente segue sendo instrução, não estrutura — motivo pelo qual o conferidor não substitui o Gauntlet.

**Status:** FECHADA em 003.FD. Método, não motor. Nenhuma R-* tocada.

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

### DH-003FB-03 — O `PAINEL_ESTADO.md` se declara "vivo" mas seu baseline envelhece por desenho `[PARCIALMENTE RESOLVIDA — 003.FD; instrumento em DT-003FD-01]`

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

**Resolução parcial (003.FD).** A **regra** foi decidida em `D-ARQ-85`: duas cadências no mesmo documento (Baseline em todo fechamento com commit; três números clínicos por evento, regra intacta), com a assimetria de testabilidade declarada — hash não é testável por não-divergência (muda a cada commit) e contagem de suíte não é testável sem recursão. Isso **descarta** a segunda correção candidata registrada acima ("derivar o Baseline por script, proibindo edição à mão") como impossível na forma integral, e não como cara. O **instrumento** — `scripts/medir_painel.py` emitindo a linha pronta e o teste das versões de doc — segue ABERTO em `DT-003FD-01`.

**Status:** PARCIALMENTE RESOLVIDA (003.FD); instrumento em `DT-003FD-01`. Instrumento, não motor. Nenhuma R-* tocada.

### DH-003FC-01 — Leitura do repo pelo mount do Cowork não tem caminho de limpeza para objeto materializado dentro da árvore `[FECHADA — 003.FC]`

**Origem:** sessão 003.FC, abertura. Irmã de `DH-003FB-02`.

**Situação.** Materializar um git object dentro do repo (`git show > arquivo`) cria um
untracked que o mount não consegue apagar — delete negado por permissão do sistema de
arquivos montado, mesma classe de restrição de `DH-003FB-02`. O resíduo (4 arquivos
`.gate_tmp_*.md`) foi removido manualmente pelo Diovanni na abertura desta sessão.

**Regra adotada.** O Arquiteto lê por `git show` para stdout, nunca redirecionado para
dentro do repo. Se precisar persistir conteúdo lido, o destino é fora da árvore montada.

**Status:** FECHADA em 003.FC — regra adotada e registrada. Ambiente, não motor. Nenhuma
R-* tocada.

### DH-003FC-02 — Relatório de `rodar-offline` particiona pendência de nível-cargo e de nível-termo em listas que não coincidem `[ABERTA — não-bloqueante]`

**Origem:** sessão 003.FC, medição de abertura do Fascino.

**Situação.** O bloco `### GHE` do relatório de `rodar-offline` lista só pendências de
nível-cargo (`R-GHE-02`); as de nível-termo (`vocabulario_ausente`, `fuzzy_recusado`,
`fracao_sem_agente`) aparecem só na seção `## Pendências` global, e as duas listas não
coincidem. É o "par partido entre dois canais" que `D-ARQ-82` cl.3 descreve no Contexto —
a cl.3 reúne o par no **motor** (a causa passa a viajar no `RiscoPGR`), não no
**relatório**. Conferência por-GHE exige cruzar as duas listas à mão.

**Status:** ABERTA, não-bloqueante. Achado independente da sessão de Code que implementou
o selo — instrumento, não motor. Nenhuma R-* tocada.

### DH-003FC-03 — H1 do PROTOCOLO defasado 88 versões contra a tabela de revisões `[FECHADA — 003.FC]`

**Origem:** sessão 003.FC. Exposto por um Crítico que declarou `PROTOCOLO v2` na linha de
gate de um julgamento de IMPLEMENTAÇÃO — leitura fiel de um título errado (o H1 dizia "v2"
enquanto a tabela de revisões estava em v90).

**Causa.** Título com número é cache que diverge do conteúdo — mesma doutrina de
`D-ARQ-63` peça 1 (o índice derivado existe justamente para não confiar em cache dentro do
próprio documento).

**Status:** FECHADA em 003.FC — número removido do H1 de `PROTOCOLO_AGENTE_MEDICO.md`
(ver PROTOCOLO v91); a versão passa a viver só na tabela. Nenhuma R-* tocada.

### DH-003FC-04 — Três defeitos estruturais da skill `/critico`, medidos ao julgar D-ARQ-82 `[FECHADA — 003.FD]`

**Origem:** sessão 003.FC, gate de fechamento (dois vereditos do Gauntlet sobre D-ARQ-82:
a decisão de ARQUITETURA e o diff de IMPLEMENTAÇÃO).

**Situação — três facetas.**

(a) O bloco `Saída` da skill tem slots fixos para os três testes de ARQUITETURA
(`universalidade | caso local | registrabilidade`) e nenhum para os quatro itens da barra
de IMPLEMENTAÇÃO — o veredito de IMPL desta sessão reportou a barra errada por seguir o
template ao pé da letra.

(b) O item 4 da barra de IMPLEMENTAÇÃO ("suíte de referência roda verde") não é testável
pelo `allowed-tools` da skill (sem acesso a rodar a suíte); em vez de disparar a regra
"dúvida rejeita" da própria skill, o item simplesmente não foi avaliado.

(c) `git diff` está fora do `allowed-tools` da skill, o que obriga a nomear o artefato
multi-commit por hash em vez de por diff direto.

**Consequência.** Nenhum dos três invalidou o julgamento desta sessão — os quatro itens de
IMPLEMENTAÇÃO ficam evidenciados no bloco 003.FC do HISTORICO, à parte do veredito da
skill —, mas os três reaparecem em toda sessão de IMPLEMENTAÇÃO futura que use `/critico`.

**Resolução (003.FD).** As três facetas corrigidas na skill: (a) o bloco `Saída` ganha linha de testes por modo, com instrução de emitir só a do modo julgado; (b) o item 4 da barra de IMPLEMENTAÇÃO passa de teste do Crítico a **evidência registrada pelo builder** (contagem + commit + comando canônico), verificada sem re-execução — alteração de barra autorizada pelo Diovanni em 003.FD, registrada em `D-ARQ-84` cl.4 e no changelog v183; (c) `Bash(git diff *)` entra no `allowed-tools`, e a Regra zero passa a admitir `git diff <base>..<topo>` para artefato multi-commit.

**Paliativo embutido na faceta (b), sinalizado:** a exceção nominal que permite ao Crítico ler a linha de registro de suíte dentro de um bloco que ele foi instruído a não abrir resolve a contradição sem resolver a estrutura — ver `DT-003FD-02`.

**Ressalva de sincronização.** A barra vive em **dois** sítios: `.claude/skills/critico/SKILL.md` (versionado) e as instruções do projeto Cowork (fora do git). Esta sessão altera o primeiro; o segundo é edição do Diovanni, fora do alcance do Code. É a mesma exposição que `DT-003DX-02` descreve, agora com um sítio a mais — registrada ali, não como dívida nova.

**Status:** FECHADA em 003.FD. Instrumento, não motor nem regra clínica.

### DH-003FC-05 — `.claude/worktrees/romantic-margulis-dcccad` trackeado como GITLINK sem `.gitmodules` `[ABERTA — não-bloqueante, herdada]`

**Origem:** sessão 003.FC, achado lateral ao conferir o estado da árvore.

**Situação.** `.claude/worktrees/romantic-margulis-dcccad` está trackeado como GITLINK
(modo `160000`, entrada de submódulo) sem `.gitmodules` correspondente — submódulo
pendurado; um `git clone` do repositório produz um diretório vazio nesse caminho.
Introduzido em `e50d75e`, já presente em `main` — herdado, não desta sessão.

**Por que o `.gitignore` não protege.** `.gitignore` já cobre o padrão
(`.claude/*` + `!.claude/skills/`), mas ignore não alcança caminho **já trackeado** — mesma
classe do `.pyc` já descrita em `CLAUDE.md`.

**Correção candidata.** `git rm --cached` em commit próprio, **fora** desta branch (que já
foi julgada pelo Crítico).

**Status:** ABERTA, não-bloqueante. Nesta sessão apenas registrada — `.claude/` não foi
tocado. Nenhuma R-* tocada.

### DT-003FD-01 — Instrumento do Baseline do painel não existe; a cl.1 de D-ARQ-85 roda à mão `[ABERTA — higiene de instrumento]`

**Origem:** sessão 003.FD, ao decidir `D-ARQ-85`.

**Situação.** A cl.1 institui re-tiragem do Baseline em todo fechamento com commit; a cl.2 diz de onde cada parte sai. O instrumento que emite a linha pronta não existe: `scripts/medir_painel.py` já mede hash (`_baseline()`), suíte (`medir_suite()`, sob `--suite`) e sincronia do índice, mas **não** lê as versões de `PROTOCOLO`/`DECISOES` e **não** compõe a linha do Baseline `[MEDIDO — 003.FD, leitura de scripts/medir_painel.py @ 6421286]`.

**O que a resolução exige (fatia própria).** (a) função que lê a última linha `| vN |` da tabela de revisões de cada doc vivo — o padrão já existe em `scripts/gerar_indice_darq.py` (`_REGEX_VERSAO`), a reusar em vez de reescrever; (b) composição da linha do Baseline no formato do painel, com a contagem de suíte carimbada pelo commit em que foi medida; (c) teste de não-divergência **restrito às versões de doc** — nunca ao hash, nunca à contagem (cl.3); (d) atualizar `test_main_sem_flag_suite_imprime_5_linhas_no_formato_esperado`, que quebra por contrato ao acrescentar linha à saída de `main()`.

**Reversão nomeada, para quando a fatia for especificada.** O teste de (c) fica vermelho se a função de (a) passar a ler a **primeira** linha `| vN |` da tabela em vez da última. Registrado desde já porque `CLAUDE.md` exige que todo teste novo nomeie a reversão que o mata, e essa é a reversão de **código**; editar o painel à mão também o deixa vermelho, mas isso é reversão de **dado** e não satisfaz a regra sozinha.

**Faceta descoberta em 003.FD, ao aplicar a regra três vezes.** A cl.1 de `D-ARQ-85` manda re-tirar o Baseline em todo fechamento que produza commit; a prática medida em 003.ER manda gravar a `main` **de partida** da sessão, com o hash de merge entrando na tiragem seguinte. As duas convivem no caso normal, mas colidem quando uma sessão produz **vários** fechamentos com commit — três, nesta (fechamento + duas emendas) —, e a resposta correta foi "não tocar" nas três, pela regra da 003.ER. O instrumento desta DT precisa resolver isso explicitamente: **re-tirar o Baseline não é função de "houve commit", e sim de "a sessão fechou"**. Sem esse critério no script, ele reescreveria o campo a cada emenda, que é o oposto do que a 003.ER mediu.

**Status:** ABERTA, não-bloqueante. Instrumento, não motor. Nenhuma R-* tocada.

### DT-003FD-02 — O registro de suíte que a barra de IMPLEMENTAÇÃO exige mora onde o Crítico está proibido de ler `[ABERTA — higiene de instrumento]`

**Origem:** sessão 003.FD, passada de verificação do próprio prompt — não da execução.

**Situação.** A barra de IMPLEMENTAÇÃO passa a exigir que o Crítico **verifique** o registro da suíte (contagem + commit). O único lugar onde esse registro hoje existe é o bloco `## Sessão <ID>` do `HISTORICO_OPERACIONAL.md` — que a Regra zero da skill `/critico` **proíbe** ler, por ser o raciocínio do builder. A barra nova, na primeira redação deste prompt, mandava ler exatamente o que a Regra zero da mesma skill proíbe: contradição interna do instrumento, da classe 11 que esta própria sessão está criando.

**Paliativo adotado em 003.FD, sinalizado como tal.** Exceção nominal e mínima na Regra zero: só a linha do registro de suíte pode ser lida daquele bloco, por ser medição e não raciocínio. **Isto é paliativo:** resolve a contradição, não resolve o fato de o isolamento do Crítico continuar dependendo de o agente obedecer a uma exceção de uma linha dentro do documento que ele foi instruído a não abrir.

**Correção estrutural candidata (não decidida).** Mover o registro para fora do bloco de sessão: todo commit que fecha fatia de implementação carrega, na **mensagem do commit**, a linha `suíte: N passed, M skipped`. Fica legível por `git log`, que já está no `allowed-tools`, sem abrir o HISTORICO. Custo: muda o protocolo do Code (`CLAUDE.md` da raiz), fora do escopo autorizado nesta sessão. Medido contra o caso real: a mensagem de `f995f7d` — a árvore em que 003.FC mediu 1154 passed — **não** carrega a contagem `[MEDIDO — 003.FD, git log @ 6421286]`.

**Status:** ABERTA, não-bloqueante. Instrumento, não motor. Nenhuma R-* tocada.

### DH-003FD-01 — A barra de ARQUITETURA não tem forma aplicável a decisão META `[ABERTA — higiene de método]`

**Origem:** sessão 003.FD, ao redigir `D-ARQ-84` e `D-ARQ-85` e perceber que o Gauntlet não teria como julgá-las pela barra vigente.

**Situação.** O item 1 da barra de ARQUITETURA é o teste dos três setores — "responde sim para construção civil, indústria química e saúde ao mesmo tempo" —, e a skill `/critico` o operacionaliza mandando **instanciar um caso concreto em cada setor**, com a instrução explícita de que não conseguir construir o caso de química ou de saúde **é** o gap. Decisão META não tem setor: `D-ARQ-32`, `D-ARQ-63`, `D-ARQ-84` e `D-ARQ-85` são regras sobre como o projeto trabalha, não sobre o que o motor faz com um PGR. Pela letra da barra somada à regra "dúvida rejeita", toda decisão META seria rejeitada pelo item 1 — e as decisões META já existentes foram registradas sem que isso aparecesse. Quatro delas declaram-se META no próprio corpo e foram lidas integralmente nesta sessão (`D-ARQ-26`, `D-ARQ-30`, `D-ARQ-32`, `D-ARQ-63`); a varredura exaustiva do documento **não** foi feita, e a contagem total de decisões META em `DECISOES` fica `[A MEDIR]` — não é o número que sustenta esta pendência, e cravá-lo sem medir seria a classe 1 do `/conferir`.

**Por que não foi resolvido nesta sessão.** Alterar a barra de ARQUITETURA é decisão do Diovanni, e o que ele autorizou em 003.FD foi a alteração do item 4 da barra de **IMPLEMENTAÇÃO**. Ampliar por conta própria seria decisão silenciosa — a classe que `D-ARQ-22` combate.

**Correções candidatas (nenhuma decidida).** (1) A barra ganha modo META próprio, com itens que testem o que uma decisão de processo deve satisfazer (aplica-se sem o contexto da sessão que a produziu; não depende de quem a escreveu; tem consequência observável). (2) O item 1 passa a ler "universal quanto ao seu objeto": para decisão de produto, os três setores; para decisão de método, os quatro modos de sessão. (3) Decisão META sai do escopo do Gauntlet — **não recomendada** pelo Arquiteto: `D-ARQ-84` é precisamente uma decisão META, e retirar do julgamento a classe de decisão que governa o julgamento é o pior lugar para abrir exceção.

**Confirmação independente (003.FD, 3ª rodada do Gauntlet).** O Crítico, a frio e sem acesso a esta
dívida, declarou no próprio veredito que o artefato é META, que **a skill não tem barra para esse
modo**, e que o tratou como ARQUITETURA por eliminação — nomeando os mesmos precedentes que esta
dívida cita. Contorno improvisado por quem julga, duas vezes seguidas (1ª e 3ª rodadas), é o
sintoma que a correção candidata (1) — modo META próprio na barra — endereça.

**Status:** ABERTA, não-bloqueante. Método, não motor. Nenhuma R-* tocada.

### DT-003FD-03 — O gate de fechamento não tem âncora versionada em nenhuma D-ARQ `[ABERTA — higiene de método]`

**Origem:** sessão 003.FD, 2ª rejeição do Gauntlet sobre `D-ARQ-84`. Não é o gap apontado — é a **causa** dele.

**Situação.** `git grep -i "gate de fechamento"` em `docs/DECISOES_ARQUITETURAIS.md` @ `c765863` não devolve cláusula instituidora: o texto normativo do Gauntlet — sessão nova, artefato + barra do modo, declaração obrigatória, "rejeição aponta o maior gap", "builder e Crítico nunca são a mesma sessão" — vive **só** nas instruções do projeto Cowork, fora do git. O gate de **abertura** tem âncora (`003.DQ`, ampliada por `D-ARQ-63`); o de **fechamento** não tem nenhuma.

**Como o defeito se manifestou.** O Arquiteto, ao redigir a cl.4 de `D-ARQ-84`, atribuiu a paternidade do gate de fechamento a `003.DQ` — a única decisão de método sobre gates que existe no git. A atribuição errada não foi descuido isolado: foi a busca por uma âncora versionada onde não há nenhuma. Erro achado pelo Crítico, a frio, na 2ª rodada.

**Por que importa mais do que a correção pontual.** É a regra que governa o julgamento de **todo** artefato do projeto — a que decide se uma decisão entra no protocolo — e é a única peça central de método sem histórico, diff ou PR. Pode divergir em silêncio entre o que o Cowork mostra ao Arquiteto e o que a skill `/critico` versionada executa; a alteração do item 4 da barra em 003.FD **já criou essa divergência**, porque o sítio versionado foi editado e o do Cowork depende de edição manual do Diovanni.

**O que a resolução exige (sessão própria).** D-ARQ que institua o gate de fechamento no git, com o texto da barra por modo, a regra de sessão-nova e a forma da declaração — reduzindo as instruções do Cowork a ponteiro, exatamente como `003.EG` fez para o público Code em `CLAUDE.md`. É a metade Arquiteto de `DT-003DX-02`, agora com um caso medido em vez de risco hipotético.

**Fronteira com `DT-003DX-02`.** Aquela DT nomeia o problema geral (regra de método fora do git, resíduo Arquiteto ABERTO). Esta é a faceta específica e mais grave: não é uma regra qualquer, é a que julga todas as outras. Não duplica — instancia.

**Status:** ABERTA, não-bloqueante. Método, não motor. Nenhuma R-* tocada.

### DH-003FD-02 — A proibição de escrever, nas skills de método, não é enforçável pelo `allowed-tools` `[ABERTA — higiene de instrumento]`

**Origem:** sessão 003.FD, 3ª rodada do Gauntlet. **Segunda ocorrência medida da mesma classe.**

**Situação.** A Regra zero de `/conferir` e `/critico` proíbe escrever qualquer coisa — *"nem arquivo, nem edição, nem redirecionamento de saída (`>`, `>>`, `tee`) — nem para scratch"*. A proibição é **textual**: o `allowed-tools` autoriza `Bash(git show *)`, e um `>` dentro de um comando autorizado não é barrado por ele. Na 3ª rodada o Crítico gravou `/tmp/darq_full.txt` por redirecionamento, percebeu, removeu o arquivo antes de ler conteúdo a partir dele, refez o julgamento só com `git show`/`git grep` e **reportou**.

**Por que é dívida e não descuido.** A primeira ocorrência foi em 003.FB, durante o teste com gabarito das duas skills — e foi **justamente por causa dela** que a proibição passou a constar no corpo das duas (`DH-003FB-01`, "Terceira correção, comum às duas"). A proibição existe há uma sessão e foi violada com ela impressa no documento que o agente estava seguindo. Instrução textual contra um comportamento que o mecanismo permite não é controle — é aviso.

**Agravante específico do ambiente.** Um arquivo materializado dentro da árvore montada não é removível pelo mount (`DH-003FC-01`, `DH-003FB-02`). Aqui o destino foi `/tmp`, fora da árvore, e por isso a remoção funcionou. A mesma violação apontando para dentro do repo teria deixado resíduo que o Arquiteto precisa limpar à mão.

**Correções candidatas (nenhuma decidida).** (1) Estreitar o `allowed-tools` para formas de comando sem redirecionamento, se a sintaxe de permissão suportar — **`[A MEDIR]`**, não se sabe se suporta. (2) Manter a proibição textual e acrescentar às duas skills a instrução de **declarar a violação no relatório** quando ocorrer — codifica o que este Crítico fez espontaneamente e certo, transformando um deslize silenciável em achado. (3) Aceitar como risco residual declarado, dado que a auto-correção funcionou nas duas ocorrências. O Arquiteto recomenda **(2)** como piso, independente de (1) ser viável: é barato, e o valor da 3ª rodada veio de o agente ter reportado, não de não ter errado.

**Não invalida o veredito da 3ª rodada.** O arquivo foi removido antes de qualquer leitura de conteúdo e o julgamento foi refeito por leitura direta; a saída é falsificável pelos comandos que ela cita.

**Status:** ABERTA, não-bloqueante. Instrumento, não motor. Nenhuma R-* tocada.

### DH-003FE-01 — Acervo parcialmente versionado sob `.gitignore` que o proíbe `[DISPENSADA — decisão do Diovanni, 29/08/2026]`

**Medido (29/08/2026).** `.gitignore` linha 22-23 diz *"Dados sensíveis de clientes (matrizes
reais, não commitar)"* e ignora `matrizes_originais/`. Mas `git ls-files matrizes_originais/`
devolve **17 arquivos versionados** — `.gitignore` não afeta arquivo já rastreado. Dos 17, **um**
carrega dado pessoal: `PGR VIVERDE V02 - 03.02.25.pdf`, com **17 CPFs** no log de assinatura
digital (4 pessoas nominalmente identificadas da CMO Construtora, com e-mail e IP). Os outros 16
foram varridos: zero ocorrência.

**Por que DISPENSADA.** Repositório privado, sem exposição conhecida; o dado é log de assinatura
de documento que já é assinado; e o campo não é usado nem será — o motor lê inventário de risco e
GHE, nada mais. Limpar exigiria reescrever o histórico de 1132 commits com PRs mergeados, custo
desproporcional ao risco. **Decisão explícita do Diovanni em 29/08/2026**, registrada para não ser
redescoberta e re-litigada a cada varredura.

**Reabre se:** o repositório deixar de ser privado, ou o acervo passar a conter dado de
trabalhador (hoje não contém — medido: matriz de exames tem 0 ocorrências de CPF).

**Cláusula testada em 04/09/2026 (sessão 003.FI) — NÃO disparou. Segue DISPENSADA.**
**Instrumento versionado em 003.FJ:** `python -m scripts.varrer_acervo_lgpd` reproduz esta
verificação a partir do repositório — `83 de 83 extraídos, 7 CPFs distintos em 4 arquivos, 20 nomes
de pessoa na metadata`, os mesmos números de 003.FI. Quem re-testar a cláusula roda o comando; não
depende mais de reescrever a varredura.
PR #322 levou `matrizes_originais/` de 17 para **83 arquivos**. Varredura post-hoc dos 83, com
extração real de texto (pdfplumber; OOXML por `zipfile`; `.doc`/`.rtf` por LibreOffice headless):
**83 de 83 extraídos, 0 escaneados, 0 não medidos.**

- **Eixo que decide a cláusula — dado de TRABALHADOR: ausente.** 34 arquivos casaram marcador
  (`ASO`, relação de empregados, `matrícula`, data de admissão, apto/inapto, prontuário) e o
  contexto de cada classe foi lido: é integralmente **prosa de procedimento e campo em branco de
  formulário** — *"Relação de empregados próprios, em planilha EXCEL, discriminando nome…"* é a
  exigência que a empresa deve cumprir, não a lista; `"(Nome do funcionário)"` é lacuna em modelo de
  placa de máquina; `"MATRÍCULA:"` é campo vazio de permissão de trabalho; `"prontuário médico
  individual"` é o literal da NR-07 sendo citado. Nenhum ASO preenchido, nenhuma lista nominal,
  nenhum resultado de exame ligado a pessoa. Contagem de marcador é forma; o contexto é a prova.
- **Repositório segue privado**, 0 forks (medido pela API do GitHub) — a outra metade da cláusula.
- **CPF com dígito verificador válido: 7 distintos, em 4 arquivos**, todos em página de assinatura
  digital ou ficha de responsável técnico, sempre acompanhados de nome e e-mail corporativo:
  `PGR VIVERDE V02` (`.pdf` e `.docx`), `PCMSO OBRA NOVA TOCTAO SPE_T65 [assinado].pdf` e
  `PGR - Programa de Gerenciamento de Riscos 27.08.26.pdf`. São **signatários** — profissionais
  assinando documento que já é assinado —, a mesma classe que sustentou a dispensa de 29/08.
  O `17` do VIVERDE bate exato com a medição original: lá o número era de **ocorrências**, aqui os
  **distintos** são 4. Mesma medição, contagem diferente — não é divergência.
- **PIS/NIT: 1 real de 3 candidatos.** Descartados: número de série de calibrador de vazão
  (`41461832041`) e ruído de texto invertido no `PGR_EBSERH_HUMAP.pdf`. O real é o NIT do
  responsável técnico, junto do CPF dele.
- **CRM em 11 arquivos, CREA em 13, e-mail em 29** — registro profissional e e-mail corporativo,
  a faixa que o `.gitignore` já declara como dado pessoal comum de baixo risco.

**Eixo novo, que não estava à vista quando a dispensa foi tomada — `DH-003FI-01`.**
**64 dos 83 arquivos** carregam metadata de autoria, com **20 nomes de pessoa** distintos —
cabeçalho OLE2 nos `.doc`/`.rtf`, `docProps/core.xml` nos `.docx`/`.xlsx`, dicionário de informações
nos `.pdf`. Inclui as médicas do PCMSO, a equipe do escritório e engenheiros de terceiros. Não está
no corpo do documento e sobrevive a qualquer redação de conteúdo. Não muda a classificação — dado
pessoal comum de profissional, mesma faixa do CRM —, mas é achado de eixo distinto e tem DH própria.
Números medidos sobre o escopo completo; ver `DH-003FI-01` e sua `Correção 003.FI-C2`.

**Nota de instrumento, medida.** A primeira passada deu `ERRO_EXTRACAO` em **28 dos 83**, porque o
container não tinha `libreoffice-writer`. **Composição dos 28, por extensão:** `.doc` **27 de 27** e
`.rtf` **1 de 4** — `PCMSO (OBRA NOVA) PASSARELA ESTADIO SERRA DOURADA.rtf`. Os outros **3 `.rtf`**
extraíram nessa mesma passada e saíram classificados `ACHADO`; RTF é parcialmente texto plano e não
depende do filtro Writer do mesmo jeito que o OLE2 do `.doc`. Instalado o filtro e re-rodados os 28:
**1 `ACHADO`, 27 limpos**. Fecha: `28 + 3 = 31` = `.doc` (27) + `.rtf` (4); e `31 + 38 .pdf +
13 .docx + 1 .xlsx = 83`. Depois disso o `apt-get` quebrou `charset_normalizer` e matou a terceira
passada em silêncio; reinstalado e re-rodado. **Varredura que não declara o que não conseguiu ler
não é varredura.**

> **Correção 003.FI-C5 (04/09/2026).** A redação anterior dizia `"28 dos 83 — todos os .doc e .rtf"`.
> O **28 estava certo**; o descritor, não — `.doc` + `.rtf` são **31**, e a frase fazia o número não
> reconciliar com partição medível alguma. **Nenhum arquivo ficou sem estado declarado:** os 3 `.rtf`
> que a frase engolia saíram `ACHADO` no próprio passe 1, e a soma `83 = 28 erro + 32 achado +
> 23 limpo` já fechava na saída bruta. O defeito era de reconstrutibilidade — um terceiro lendo só o
> texto não conseguia refazer a conta —, não de cobertura. Achado pela 3ª rodada do `/critico`.

### DH-003FE-02 — Branches remotas órfãs anteriores ao ritual `[FECHADA em 02/09/2026 — descarte executado]`

**Medido (29/08/2026, primeira aplicação do passo 9 do ritual).** Restam no remoto
`origin/claude/eloquent-mcnulty-e0cdc2` (`43a61bf`, 07/05/2026) e
`origin/claude/quizzical-rhodes-e3ae5f` (`d7cf602`, 06/05/2026) — **não mergeadas em `main`**,
de ~4 meses atrás, anteriores ao passo 9. Não são candidatas a `git branch -d` justamente por
não estarem mergeadas: podem carregar commit único, ou ser lixo de sessão abandonada.

**O que a resolução exige.** Inspecionar `git log main..origin/claude/<nome>` em cada uma e
decidir: descartar (`push origin --delete`) ou recuperar o que houver. Não-bloqueante; o passo 9
impede que o caso se repita daqui pra frente, mas não varre o passivo.

**Resolução (02/09/2026).** Inspeção feita, com correção de método: `git log main..<branch>` dava
297 e 293 commits, número enganoso — `git merge-base` retorna **vazio** nas duas. As branches não
divergiram de `main`: têm **história desconexa**. Raiz comum entre elas é `6e98990`
*"Add files via upload"* (03/04/2026); `main` tem três raízes, nenhuma delas. É a linha de
desenvolvimento anterior à reconstrução do repositório — conteúdo migrado, história não.

`quizzical` está contida em `eloquent` exceto por `tests/test_integracao_camada0.py`.

**Diff de conteúdo.** O bruto (217 arquivos, 67.028 deleções) é ruído de fim de linha: a linhagem
antiga é CRLF, `main` é LF. Com `--ignore-cr-at-eol --ignore-all-space` sobram **11 arquivos e
~197 linhas**. Em todo arquivo compartilhado `main` está à frente — `modules/agente_medico_ia.py`
dá **+6/−94** a favor de `main`, que tem `_CARGOS_ADMIN_TOKENS`, `_ALIASES_EXAME` e
`_validacao_universal(..., is_admin=)`; as 6 linhas "únicas" da branch são a assinatura antiga da
mesma função. As +53 de `utils/ia_client.py` são `print("[GEMINI DEBUG] ...", flush=True)`.

**A linhagem antiga é regressão clínica, não reserva.** Em `modules/modulo_pcmso.py`,
`NOTAS_RISCO_QUIMICO` pareia `serralheiro` / `Cromo hexavalente` com
`"Carboxihemoglobina no Sangue"`; `main` grava `"Cromo na Urina"`. Carboxihemoglobina é o IBE de
monóxido de carbono, não de Cr(VI) — `[CONFERIR NR-07 Anexo I Quadro 1, texto vigente em
gov.br/MTE]`, embora o veredito não dependa da norma: `main` já grava o valor correto. Pior, a
`quizzical` carrega `test_serralheiro_tem_carboxihemoglobina`, que **fixa o erro** — restaurar
aquele dado reintroduziria a regressão com teste protegendo-a.

**Único conteúdo ausente de `main`:** a heurística `_suspeitar_distribuicao_incorreta` (28 linhas
+ 3 testes), preservada como `DT-003FG-01`; `logo.png` (marca Seconci-GO, 146 KB — `main` não tem
imagem nenhuma); e `testar_pcmso.py` (harness manual, superado pelas CLIs de `superficie/`).

**Execução bloqueada.** Descarte decidido pelo Diovanni em 02/09/2026, mas
`git push origin --delete` das duas retorna **HTTP 403** no container da sessão remota. Não é o
proxy (`/__agentproxy/status` com `recentRelayFailures: []`) nem falta de rede: a mesma credencial
criou branch e empurrou commits no mesmo turno. É escopo de credencial — o container empurra ref,
não apaga ref. O GitHub MCP desta sessão também não expõe delete de branch (tem `create_branch`,
não o inverso). Fica para execução manual do Diovanni:

```
git push origin --delete claude/eloquent-mcnulty-e0cdc2
git push origin --delete claude/quizzical-rhodes-e3ae5f
```

Estado no fechamento: as duas seguem no remoto, em `43a61bf` (07/05/2026) e `d7cf602`
(06/05/2026). Nada local a apagar — nunca existiram como branch local. A decisão está registrada
e a única ideia recuperável já está em `DT-003FG-01`, então o delete não perde mais nada.

**Execução concluída (02/09/2026).** O 403 era escopo da credencial do container, não do
Diovanni: rodado no Claude Code local, `git push origin --delete` das duas teve sucesso.
Confirmado por `git ls-remote origin` a partir do container — nenhuma referência às duas branches
no remoto. Commits únicos nomeados antes do delete: `eloquent-mcnulty-e0cdc2` carregava 2
(`c21e1ab` logging, `43a61bf` debug print swap), `quizzical-rhodes-e3ae5f` carregava 1 (`d7cf602`,
sessão5 — validação e2e + bugfixes), consistente com a medição anterior desta DH (`quizzical`
contida em `eloquent` exceto por `tests/test_integracao_camada0.py`).

### DT-003FE-01 — Segunda família de parser: âncora `GHE NN` (T65) `[REENQUADRADA — 003.FF; ver DT-003FF-01]`

> **Reenquadrada em 003.FF (31/08/2026).** A medição no `pdfplumber` do motor falsificou quatro afirmações da redação abaixo — a âncora do T65 **já é reconhecida** (16/16). Redação original preservada para rastreabilidade; o diagnóstico correto está em `DT-003FF-01`.

**Medido (29/08/2026).** `extracao_pgr.py` localiza bloco por `DADOS GERAIS` + título `N.N`, e
existe **uma única família** no repo (`parser_familia_consciente.py`). Dos 4 PGRs varridos,
`DADOS GERAIS` aparece **só no Ricco ADM** (o único que atravessou). O `PGR - ALT T65 2024.2026`
tem **16 blocos ancorados em `GHE 01`..`GHE 16`**, cada um com cargo, atividade e perigos
nomeados — âncora mais simples que a da família existente.

**O que a resolução exige.** Medir a forma da âncora no extrator do motor (`pdfplumber`, não
`pdftotext` — os dois discordaram nesta medição), escrever a família 2 e medir o acerto contra a
matriz assinada do T65, que já está no acervo (par 8 do pareamento). Detalhe em
`docs/referencia/MEDICAO_003FE_RICCO_e_parses.md`. Faceta de `DT-003L-01`.

### DT-003FE-02 — Avaliação Psicossocial sem periódico no gabarito Ricco `[A VALIDAR — divergência clínica]`

**Medido (29/08/2026).** No par Ricco Administração, `Avaliação Psicossocial` sai `(ADM, MRO)` na
matriz assinada e `(ADM, MRO, PER)` na saída do motor, em **11 de 12 cargos**. `R-PSY-02`
prescreve `adm/per/MR` incondicional, derivado da medição de corpus de 003.AH/003.EO.

**Não é defeito de parser** — o motor aplica a regra escrita; o gabarito diverge dela. Ou a regra
está larga demais, ou este documento é exceção. Exige contraste com os demais gabaritos
pós-26/05/2026 antes de tocar `R-PSY-02`; **não alterar a regra com n=1**.

### DT-003FF-01 — Reenquadramento de `DT-003FE-01`: o gargalo do T65 é a família de conteúdo `[ABERTA — insumo medido, não-bloqueante]`

**Medido (29-31/08/2026, `pdfplumber` do motor, `main c9db9cc`).** Quatro afirmações de
`DT-003FE-01` divergem do medido:

1. "`extracao_pgr.py` localiza bloco por `DADOS GERAIS`" — `DADOS GERAIS` só é lido em
   `_recuperar_titulo_do_vao`, da rota **card** (EBSERH). Não participa do roteamento GHE.
2. "o motor não enxerga os 16 blocos do T65" — `eh_cabecalho_ghe` casa **16/16**
   (`INVENTÁRIO DE RISCO GHE NN`); `avaliar_estrutura` devolve `("ghe", None)`.
3. "família que ninguém escreveu" (âncora) — a forma 3 de `_RECONHECEDORES_GHE` cita
   **"ALT T65"** nominalmente desde `D-ARQ-57` peça 1.
4. "`familia_nao_medida` impediu o T65 de atravessar" — é **não-bloqueante**; o bloqueio de
   003.FE foi o HTTP 503 da cascata Gemini. **Confirmado empiricamente em 003.FF:** com o
   serviço de pé, o T65 atravessou pela rota LLM — 16/16 GHEs, zero pendência bloqueante, sem
   uma linha de parser nova.

**O gargalo real.** `parser_familia_consciente._parsear_bloco` recusa **16/16** blocos por
cabeçalho `GRUPO/PERIGO/FONTE/AGRAVO` não localizado. É a família de **conteúdo do bloco**
(`D-ARQ-65` fatia 1), não a âncora de recorte (`D-ARQ-57` peça 1, já resolvida para o T65).

**O que a resolução exige.** Se a família 2 for escrita, o layout é tratável pela mesma técnica
da família 1 (cabeçalho localizável em 16/16 pelo núcleo `{Perigo, Exposição, Medidas,
controle}`; `Atividade/Setor:` como nome do GHE; `Funções Envolvidas` como cargos). O que não
transporta: **22,9% dos tokens de grupo têm typo na fonte** (`Ergnômico` 14, `Fisíco` 11, de 109)
e `Ergnômico` não sobrevive a normalização NFD+upper; o T65 **tem quantificação em 16/16 blocos**
onde a família 1 declara família qualitativa; e o mapeamento de coluna é `DT-003FF-02`.

**Prioridade rebaixada em 003.FF.** A medição do par (48,4%) mostrou que a família 2 **não é o
maior movimento**: escrita e com o mapeamento resolvido, o T65 seguiria perto de 48%, porque os
termos entregues continuariam sem casar no vocabulário (`R-PGR-07`). Detalhe em
`docs/referencia/MEDICAO_003FF_gargalo_T65.md` e `MEDICAO_003FF_par_T65.md`.

### DT-003FF-02 — Mapeamento coluna→`RiscoVerbatim` em família sem coluna de agente nomeado `[ABERTA — decisão de arquitetura]`

**Medido (29-31/08/2026).** As colunas do T65 não mapeiam 1:1 nas da família 1:

| Família 1 (Consciente/Fascino) | Família 2 (T65) |
|---|---|
| `PERIGO / ASPECTO` = **agente nomeado** (`Ruido`, `Destilados de Petróleo`) | `Perigo` = **descrição de perigo** (`Queda em altura`, `Postura incorreta de trabalho`) |
| `FONTE` | `Origem do Risco` |
| `AGRAVO` | `Risco` (possíveis lesões ou agravos) |
| — | `Exposição` (Habitual/Eventual), probabilidade / severidade / grau |

`RiscoVerbatim.agente` alimenta o resolvedor de termos. **No T65 não existe coluna de agente
nomeado.** Mapear `Perigo` → `agente` entrega ao resolvedor uma frase descritiva — que foi
exatamente o que a rota LLM fez em 003.FF, produzindo 45 termos descritivos não resolvidos.

**Origem no prompt, não só no documento.** `_PROMPT_GHE` (`transcritor_gemini_pgr.py`) é
calibrado para a família Fascino — crava a âncora `"SETOR/FUNÇÃO ..."` (que o T65 não tem) e
manda ignorar o cabeçalho `"Cód. Atividades Perigo Exposição Fonte geradora..."` (que é do
Fascino). Sua **regra 3c** manda transcrever o próprio texto do perigo como `agente` quando não
há quantificação: no Fascino é exceção, no T65 é a regra geral.

**O que a resolução exige.** Decidir o que ocupa `agente` quando a família não nomeia agente —
e se o prompt de transcrição deve ser por família. Bloqueia a escrita da família 2
(`DT-003FF-01`). Não bloqueia a cobertura de termo.

### DH-003FF-01 — Escopo da `Decisão 003.DG-3`: "zero riscos aprova" foi medida na rota card `[ABERTA — higiene de decisão]`

**Medido (29/08/2026).** `gate_forma_ghe` aprova GHE com zero riscos: a condição é
`all(risco.agente.strip() != "" for risco in ghe.riscos)`, e `all()` sobre sequência vazia é
`True`; basta `nome` não-vazio.

**Não é defeito.** É decisão deliberada — `DECISOES_ARQUITETURAIS.md` l. 2053: *"card todo-`N/A`
→ `riscos=()` → gate APROVA … num cargo administrativo, GHE sem risco ocupacional é forma
clinicamente legítima"*, travada por
`test_transcritor_card.py::test_composicao_card_todo_na_sem_riscos_aprova_no_gate`.

**O que fica aberto.** A decisão foi medida sobre a rota **card** (EBSERH, cargo administrativo)
e é aplicada globalmente a `gate_forma_ghe`. Na rota **ghe**, `GHE14` do T65 (Portaria) tem 2
riscos reais grafados `Ergnômico` — com repertório de lista fechada sairia vazio e **aprovado**,
em silêncio. A decisão está certa no escopo medido e larga fora dele.

**O que a resolução exige.** Reabrir com escopo por rota é decisão de ARQUITETURA:
`GHEVerbatim` não carrega o texto do bloco (só `nome`/`cargos`/`riscos`), então o invariante
teria de morar em `preparar_ghes` ou no parser da família. Lastro contra falso-positivo já
medido: Fascino pela rota determinística, 19/19 blocos, distribuição
`[8,8,8,9,10,5,22,13,11,19,12,21,10,6,11,28,21,12,3]`, **mínimo 3, zero blocos vazios**.

### DT-003FF-03 — RT fora do span do recorte de topo `[ABERTA — não-bloqueante]`

**Medido (31/08/2026).** `medicao_pgr ida` sobre o T65 devolveu `credencial` com
`responsavel_tecnico`, `titulo_rt` e `registro_profissional` todos `""`. O RT existe e está
completo — **página 46, a última**: *"elaborado pelo Coordenador de Segurança do trabalho Weder
Morais Silva sob o número de registro 1020541245D-GO … Engenheiro de segurança do trabalho —
CREA: 1020541245D-GO — Responsável pela elaboração e implementação do documento."*

`recortar_topo` (`D-ARQ-53`) devolve da 1ª linha do documento até a linha **anterior à 1ª âncora
GHE** — no T65 isso termina na página 11. **O recorte de topo assume que o RT vive antes do
primeiro GHE**, e o T65 falsifica a premissa.

**O que a resolução exige.** Mesma classe do título-de-card do EBSERH, resolvida em `003.DH` por
`recuperar_titulos_cargo` — recuperar do vão sem reabrir o recorte. Aqui o vão é a **cauda** do
documento, não o preâmbulo. Não bloqueia: `R-PGR-01` (assinatura por engenheiro) é confirmada
pelo seam humano, não pela transcrição.

### DT-003FF-04 — `vocabulario_ausente` que suprime exame é não-bloqueante `[ABERTA — decisão de direção segura]`

**Medido (31/08/2026, par T65).** `"Queda em altura"` (13 ocorrências) não resolveu para
`trabalho_altura`; o predicado `altura` ficou `False` em todos os 16 GHEs; `R-PKG-ATIVCRIT` não
disparou; **175 células de exame do gabarito assinado não foram emitidas** — acuidade visual,
hemograma, glicemia e ECG. A pendência `vocabulario_ausente` que acompanha a omissão é
**não-bloqueante**: o documento segue emitível com o exame faltando.

**A questão.** Termo não resolvido que alimenta predicado de pacote remove exame do documento
final sem bloquear a emissão. Ou a pendência bloqueia nesse caminho, ou a direção segura do
projeto aceita a omissão — **hoje aceita por omissão, não por decisão**. Tensão explícita com
`D-ARQ-31/35` (anti-supressão) e com `R-PGR-07` cl.1 (divergência de nomenclatura não é ausência
de risco).

**O que a resolução exige.** Distinguir `vocabulario_ausente` que só perde granularidade de
`vocabulario_ausente` que suprime exame — o segundo é decidível: o predicado que ficou `False`
por termo não resolvido é rastreável. Nomeada por `R-PGR-07` (003.FF), que expõe sem resolver.

### DT-003FG-01 — Detector de distribuição suspeita de cargos por GHE `[ABERTA — MEDIDA 23/09/2026: critérios herdados refutados, substituto proposto; decisão do Arquiteto]`

**Origem.** `modules/modulo_pcmso.py` em `origin/claude/eloquent-mcnulty-e0cdc2`, commit `43a61bf`
(07/05/2026), na linhagem de história desconexa varrida por `DH-003FE-02`. Confirmado ausente de
`main` (`git grep` vazio). Registrado aqui **antes** de a branch ser apagada, para a ideia não
morrer com o código.

**O que era.** `_suspeitar_distribuicao_incorreta(dados_ghe) -> bool`, 28 linhas, com dois
critérios sobre a saída do distribuidor de cargos:

- **(a)** algum GHE com **≥ 10 cargos** — sinal de fallback que despejou tudo num balde;
- **(b)** **> 30% dos GHEs** com listas de cargos idênticas entre si — sinal de cópia em massa.

Verdadeiro em qualquer um dos dois. No `app.py` daquela linhagem, o disparo somava-se a
"GHE sem cargo real" para acionar a re-extração via LLM. Tinha 3 testes
(`tests/test_camada0_app.py`): muitos cargos, cargos repetidos, distribuição normal.

**Por que não é port.** O código é do **motor legado** (`modules/`), que o `CLAUDE.md` marca como
não-tocar, e depende do `app.py` antigo. Além disso não é regra clínica: é detector de qualidade
de parse. O que vale é o **critério**, não a implementação.

**O que a resolução exige.** Decidir se o motor novo precisa de um discriminante equivalente —
hoje ele bloqueia nomeado por ausência (`DT-003DK-01`, anti-supressão), mas **não tem sinal para
distribuição presente e implausível**: um parse que atribui todos os cargos ao mesmo GHE atravessa
sem pendência. Se entrar, entra medido contra o acervo pareado (qual o maior nº de cargos por GHE
observado num gabarito assinado? qual a taxa real de GHEs com lista idêntica?), não com os
limiares 10 e 30% herdados, que não têm proveniência conhecida. Faceta de `DT-003L-01`.

**Medição `[MEDIDO — 23/09/2026, branch claude/hopeful-newton-yjv3k7, sobre main 9782074]`.**
Relatório completo, com método e números por arquivo:
`docs/referencia/MEDICAO_DT003FG01_distribuicao_cargos_ghe.md`. Nenhum código tocado.

- **Critério (a) ≥ 10 cargos/GHE — REFUTADO.** Nas 16 matrizes assinadas de layout `GHE NN`,
  máximo **19** cargos/GHE e **4 de 16** matrizes com algum GHE ≥ 10, todos administrativos
  legítimos (Vila Brasil ADMINISTRAÇÃO 01 = 19; Porto Araras 1 ADMINISTRAÇÃO = 16; Dinamica
  ADMINISTRAÇÃO = 15). Em 5 das 18 matrizes de layout `SETOR:` o agrupamento é plano (28 a 63
  cargos): a matriz assinada nem sempre é organizada por GHE.
- **Critério (b) > 30% dos GHEs com lista idêntica — não discrimina.** Máximo assinado **28,6%**
  (CMO Vistamerica, 8/28), 25,6% (CMO Varandas Bueno). Repetição legítima: produção dividida em
  GHEs por frente, mesmos cargos. Folga de 1,4 p.p. até o limiar herdado.
- **Lado do motor.** Rota determinística (`preparar_ghes`, clientes offline) sobre 29 PGRs do
  acervo: 26 bloqueiam antes da distribuição (14 `familia_nao_medida`→LLM, 8
  `segmentacao_implausivel`, 3 `pgr_cargo_based`, 1 rota card) e **3 atravessam** (Fascino, Vila
  Brasil Escritório, Porto Araras I). O "tudo num balde" que motivou a DT já é coberto, na
  **segmentação**, pelo gate anti-Vistamérica (D-ARQ-57 peça 2): a transcrição é por bloco.
- **O que discrimina de fato (n pequeno).** Porto Araras atravessa **com parse errado** (DT nova
  abaixo). Dois sinais separam esse parse ruim dos bons e dos gabaritos:
  cargo terminado em preposição (gabaritos **0/1421**; Fascino+Vila Brasil **0/46**; Porto Araras
  **26/51**) e cargo repetido no mesmo GHE (gabaritos **1** — duplicata real do documento humano;
  bons **0**; Porto Araras **6**). **Limite:** n = 1 parse ruim e n = 2 bons. Não pega
  truncamento sem preposição final (`Analista`, `Vigia`) nem GHE perdido.

**Proposta para decisão do Arquiteto.** Descartar (a) e (b) como critérios. Se o detector entrar,
ele entra como **sinal de truncamento de nome de cargo** (preposição final e/ou repetição no mesmo
GHE → `Pendencia` nomeada), não como sinal de distribuição. É forma de parse, não regra clínica
(sem `R-*`). A reversão que deixaria o teste vermelho é remover o predicado da composição de
pendências de `preparar_ghes`; o caso real é Porto Araras. A DT não fecha por esta nota:
fecha pela decisão (implementar o sinal substituto ou `DISPENSADA`, com o motivo).

**Nota (mesma branch, 23/09/2026).** O parse ruim que motivou o sinal substituto (Porto Araras)
foi consertado na causa — `_separar_nome_cbo` cortava a última palavra de cargo sem CBO
(`DT-(sessão claude/hopeful-newton-yjv3k7)-01`, RESOLVIDA). Pós-fix, o sinal de preposição final
e o de cargo repetido no mesmo GHE dão **0** nos três PGRs que atravessam a rota determinística.
O sinal perdeu o único caso positivo medido; a decisão (implementar como defesa ou `DISPENSADA`)
segue com o Arquiteto.

### DH-003FH-01 — `D-ARQ-84` cl.1(c) não foi aplicada a três blocos de sessão consecutivos `[ABERTA — higiene de método]`

**Origem:** sessão 003.FH, conferência dos blocos 003.FE/FF/FG do `HISTORICO_OPERACIONAL.md`.

**Medido.** `D-ARQ-84` cl.1 — aprovada em 003.FD (22/08/2026, 3ª rodada do Gauntlet) — obriga
`/conferir` sobre **"(c) bloco de sessão do `HISTORICO_OPERACIONAL.md`"**, antes de o artefato ser
gravado em doc vivo. Os blocos **003.FE, 003.FF e 003.FG** foram redigidos depois dessa aprovação.
Os três carregam divergência: **118 afirmações extraídas, 91 CONFERE, 10 DIVERGE, 17 NÃO
VERIFICÁVEL** (@ `eb94b06`).

Não é regra ausente nem regra nova a criar: é regra **aprovada, versionada e não aplicada**, três
vezes seguidas, ao artefato que ela nomeia por extenso. O `RITUAL_FECHAMENTO.md` passo 8 já a
replica. A lacuna é de execução, não de texto.

**As 10 divergências, por classe do `/conferir`:**
- classe 1 (número herdado citado como corrente): 3 — âncora e duração da suíte de 003.FE; `48`
  commits de código em 003.FG.
- classe 4 (âncora que envelheceu): 2 — `DH-003FE-02` declarada `DECIDIDA` depois de fechada;
  branch do PR #317 declarada apagada antes do PR #318 sair dela.
- classe 6 (nome/símbolo que não existe): 2 — "forma 3 de `_RECONHECEDORES_GHE`" (a tupla tem 2
  entradas; a numeração está na docstring de `eh_cabecalho_ghe`); "`DADOS GERAIS` só é lido em
  `_recuperar_titulo_do_vao`" (a função casa `_PADRAO_TITULO_CARGO`, não aquela string).
- classe 3 (citação não transcrita): 1 — "CREA 1020541245D-GO" onde o verbatim diz "número de
  registro", contra a convenção de D-ARQ-53 P2 ("credencial crua sem assumir CREA").
- outras 2: `DT-003FD-02` declarada paga com header `[ABERTA]`; `test_serralheiro_tem_carboxihemoglobina`
  atribuído à branch órfã quando está em `main` desde o PR #271.

**Teste de morte desta DH:** uma sessão fechar com bloco conferido e o relatório do `/conferir`
referenciado no próprio bloco, sem DIVERGE material. Se três fechamentos seguidos fizerem isso, a
DH fecha por comportamento, não por decisão.

**Faceta nova, medida em 003.FH — auto-conferência não substitui conferência.** A própria 003.FH
rodou `/conferir` sobre o seu bloco **na sessão que o escreveu** e declarou *"21 afirmações, 21
CONFERE, 0 DIVERGE"*. Uma passada **a frio** sobre o mesmo bloco, @ `919b32c`, extraiu **46** e achou
**2 DIVERGE** — uma delas um fato errado sobre o acervo, a outra o próprio placar limpo. Ou seja: a
cláusula foi cumprida na letra e falhou no efeito.

O `Crítico` já resolve isso para o Gauntlet — `INSTRUCOES_ARQUITETO.md` §6: *"roda em sessão nova,
nunca na que produziu o artefato"*. `D-ARQ-84` **não** estende a mesma exigência ao `/conferir`.
Se estender é decisão do Arquiteto, e ainda **não tem origem medida suficiente**: são duas
ocorrências (esta e as três desta DH), e §11 exige origem medida + teste de morte para regra nova.
Registrado como insumo da próxima META, não como cláusula proposta.

**Status:** ABERTA, não-bloqueante. Método, não motor. Nenhuma R-* tocada.

### DH-003FH-02 — Os três gabaritos que sustentam os números de 003.FE/FF não são reproduzíveis a partir do repositório `[FECHADA em 04/09/2026 — acervo completo versionado, suíte verde medida]`

**Origem:** sessão 003.FH, ao medir a suíte no container.

**Medido @ `eb94b06`.** `matrizes_originais/` tem **17 arquivos rastreados** apesar de a pasta estar
no `.gitignore:23` (git ignora só o não-rastreado). Quatro PGRs que os testes e as medições abrem
**não** estão entre os 17:

| PGR | quem depende |
|---|---|
| `PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf` | 2 testes vermelhos; medição 91,1% (003.FE) |
| `pgr_Cjr Engenharia Ltda (M Construtora).pdf` | 6 testes vermelhos |
| `PGR - CONSCIENTE … SPE 0030 - FASCINO (15.07.26).pdf` | skips; medição 97,0% (003.FE) |
| `PGR - ALT T65 2024.2026.pdf` | medição 48,4% e as 24 formas do resíduo (003.FF) |

**Consequência.** A suíte no container dá **1137 passed, 8 failed, 21 skipped** contra os
`1160 passed, 6 skipped` herdados — **1166 coletados nos dois casos**, logo nenhum teste foi criado
ou perdido; o que muda é quantos conseguem rodar. E os três percentuais que 003.FE/FF publicam como
resultado principal (Fascino 97,0%, Ricco 91,1%, T65 48,4%) **só são re-mediveis na máquina do
Diovanni**. Gabarito que não reproduz não é gabarito — é testemunho.

**Não é `DH-003FE-01`.** Aquela foi **DISPENSADA** por decisão do Diovanni em 29/08 sobre um eixo
distinto: se versionar acervo com dado pessoal era aceitável. Esta é sobre **irreprodutibilidade de
medição**, e a dispensa daquela não a cobre — a decisão de dispensar não foi tomada com este custo
à vista. Também não é `DH-003ET-01` (fixtures de PDF não versionadas), que nomeia a classe mas não
mede este efeito sobre os gabaritos publicados.

**Achado colateral, dentro de `DH-003ET-01`:** a mesma ausência de PDF produz `skip` declarado em
alguns testes e `FileNotFoundError` em outros. Inconsistência de instrumento, não de conduta
clínica.

**Caminho candidato, não decidido:** versionar os 4 PGRs faltantes (mesmo critério dos 17 que já
entraram), ou publicar um extrato textual versionado por PGR suficiente para os testes, mantendo o
PDF fora. A escolha é do Arquiteto — as duas têm custo de LGPD distinto.

**Status:** **FECHADA em 04/09/2026** (sessão 003.FI) — o acervo completo foi versionado (PR #322),
os 4 PGRs que esta DH nomeia estão rastreados sob os nomes exatos, e a suíte roda verde no container
(`1169 passed, 6 skipped, 0 failed`). Deixa de ser bloqueante para reprodução de gabarito. A classe
mais ampla segue em `DH-003ET-01` (fixtures de PDF não versionadas), que **não** foi resolvida — só
deixou de se manifestar neste acervo.

> **Correção 003.FI-C6 (04/09/2026).** Esta linha dizia `"**Status:** ABERTA, não-bloqueante para o
> motor; bloqueante para reprodução de gabarito"` **enquanto o header da DH já dizia FECHADA** — a
> `Resolução` e a `Correção 003.FI-C2` foram inseridas antes dela e nenhuma a reescreveu. Um terceiro
> que abrisse só esta DH leria os dois estados no mesmo bloco. Achado pela 4ª rodada do `/critico`.

**Resolução (04/09/2026, sessão 003.FI).** O Diovanni subiu o acervo completo — PR #322, 66 arquivos
novos, `matrizes_originais/` passa de 17 para **83 arquivos rastreados**, 386 MB. Foi escolhido o
primeiro caminho candidato (versionar os PDFs), não o extrato textual.

**Medido nesta sessão, árvore parada @ `4d1bc01`:** os **8** arquivos de `matrizes_originais/`
referenciados pelos testes existem em disco. Suíte completa pelo comando canônico
`python -m pytest agente_medico/tests/ tests/`: **1169 passed, 6 skipped, 0 failed** em 580.32s.

**E os 4 PGRs que esta DH nomeia estão rastreados sob os nomes exatos da tabela acima**, conferidos
um a um com `git ls-tree -r -l 7815f20`: `PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf` (567.168 B),
`pgr_Cjr Engenharia Ltda (M Construtora).pdf` (1.037.924 B), `PGR - CONSCIENTE … FASCINO
(15.07.26).pdf` (10.366.538 B) e `PGR - ALT T65 2024.2026.pdf` (1.296.117 B). O T65 é o único dos
quatro que nenhum teste abre — é insumo de `medicao_pgr` —, e por isso a suíte verde não responde
por ele; o `ls-tree` responde.

> **Correção 003.FI-C2 (04/09/2026).** A primeira redação dizia **7**, medidos por
> `git grep -ohE "matrizes_originais/[^\"']+\.(pdf|docx|doc|xlsx)"`. O `/conferir` a frio mostrou que
> esse comando exige `matrizes_originais/` colado ao nome **num literal só**, e
> `tests/test_regressao_pcmso.py:168` monta o caminho partido
> (`ROOT / "matrizes_originais" / "PCMSO(ATUALIZAÇÃO)CMO RESIDENCIAL VIVERDE AREIAO 06.03.25.pdf"`),
> logo invisível ao grep. Re-medido por casamento de nome de arquivo do acervo contra o texto dos
> testes, com normalização NFC: **8**. O 8º está rastreado, então a conclusão não muda — mas o
> comando publicado media **literais de string, não aberturas**, e teria escondido um arquivo ausente.

**O que fecha esta DH é a escolha do Arquiteto, não a aritmética.** A DH não crava critério numérico:
ela nomeia um critério qualitativo (gabarito reproduzível a partir do repo) e deixa dois caminhos
candidatos explicitamente não decididos. O Diovanni escolheu o primeiro ao mergear o PR #322; a
suíte verde é a **evidência** de que o critério qualitativo foi atendido.

**A conta fecha exata, e é ela que fecha a DH:** `1160` passed herdados de 003.FE `+ 8` testes de
003.FH `+ 1` da correção 003.FH-C3 = **1169**; `skipped` volta de **21** para os **6** herdados. Os
8 vermelhos e os 15 skips extras que esta DH nomeou eram, um-para-um, os PGRs ausentes — e sumiram
com a chegada deles. `mypy --strict` no alvo canônico segue limpo, 48 arquivos.

**Os três percentuais de 003.FE/FF passam a ser re-mediveis a partir do repositório.** Não foram
re-medidos aqui — fica `[A MEDIR]`, porque re-medir é rodar `medicao_pgr`, fora da suíte, e esta
sessão não o fez. O que esta DH afirmava (irreprodutibilidade) deixou de valer; o valor dos
percentuais não foi reconferido.

### DT-003FH-01 — 19 das 24 formas do resíduo do T65 ficam sem alias por falta do documento `[ABERTA — insumo medido, não-bloqueante]`

**Origem:** sessão 003.FH, fatia de dado de `R-PGR-07`.

**Situação.** 003.FF mediu **57 de 98 ocorrências (58%) do resíduo do T65 correspondendo a 9 slugs
já existentes**, em 24 termos distintos. Esta sessão populou **5 aliases** — os únicos cujo verbatim
está transcrito em doc versionado (`MEDICAO_003FF_par_T65.md` §3/§4/§7). Os outros 19 não têm
verbatim no repo e o PGR ALT T65 não está no acervo (`DH-003FH-02`), então não são re-mediveis aqui.

**Cobertura entregue:** `trabalho_altura` e `silica` — os dois que 003.FF mede como respondendo por
**227 das 227 células faltantes**. `esforco_fisico` e 2 das 6 formas de `postura_inadequada`.

**Fora por decisão, não por falta de dado:** `"Choque Elétrico"` → `eletricidade` e
`"Objetos cortantes e/ou perfurocortantes"` → `acidente_perfurocortante`. Nos dois o termo nomeia o
**dano** ou o **objeto** e o slug nomeia o **agente**; atribuir é inferir agente por proximidade de
texto, que `R-PGR-05`/`D-ARQ-14` mandam não fazer. Decisão do Arquiteto, não do Code.
`"Queda de mesmo nível"` (14 ocorrências) não tem slug correspondente — não é `queda_de_materiais`
nem `trabalho_altura`.

**O que fecha esta DT:** o T65 (ou o extrato do seu resíduo) chegando ao repo, e uma passada que
popule os 19 restantes com o mesmo critério de procedência.

**Metade da condição caiu em 04/09/2026 (sessão 003.FI).** O PR #322 trouxe o T65 ao acervo.
**`matrizes_originais/PGR - ALT T65 2024.2026.pdf` está rastreado sob o nome exato que a
`DH-003FH-02` nomeou** — blob `7f5c942`, 1.296.117 bytes —, mais dois arquivos da mesma família:
`PCMSO OBRA NOVA TOCTAO SPE_T65_ 18.03.2024 [assinado].pdf` e `PGR - TOCTAO ALT 65.pdf`.
Os 19 termos deixam de ser `[A MEDIR]` por falta de documento — passam a ser re-mediveis a partir do
repositório. **A DT NÃO fecha aqui:** falta a passada que popula os aliases, e ela é fatia de dado
com o mesmo critério de procedência das 5 de 003.FH (verbatim medido, reversão nomeada, varredura
inversa). Sessão futura.

> **Correção 003.FI-C4 (04/09/2026).** A primeira redação criava uma **ressalva fabricada**: dizia
> que o T65 chegara "em dois arquivos" com nomes diferentes do que a `DH-003FH-02` cita, e marcava
> `[A MEDIR]` se seriam o mesmo documento. **Não havia o que medir** — o arquivo com o nome exato
> está rastreado em `4d1bc01` e em `7815f20`, e um `git ls-tree` responde. Reproduz:
> `git ls-tree -r 7815f20 -- "matrizes_originais/PGR - ALT T65 2024.2026.pdf"`.
> **Causa medida:** a lista de "dois arquivos" saiu da saída do passe 3 da varredura, que **só
> imprime arquivo com marcador**; o `PGR - ALT T65 2024.2026.pdf` tem zero marcadores, então não
> apareceu. Ele **foi varrido** — está no cache dos 83/83 —, mas eu li uma **listagem filtrada como
> se fosse inventário**. O `/critico` apanhou isso na 2ª rodada.

**Status:** ABERTA, não-bloqueante. Dado, não motor. Insumo destravado, trabalho não feito.

### DH-003FI-01 — Nome de pessoa na metadata dos arquivos do acervo `[ABERTA — medida, não-bloqueante]`

**Origem:** sessão 003.FI, varredura do acervo depois do PR #322.

**Medido (04/09/2026, os 83 arquivos de `matrizes_originais/` — escopo completo).**
**64 arquivos** carregam metadata de autoria: cabeçalho OLE2 nos `.doc`/`.rtf` (campos `Author` e
`Last Saved By`), `docProps/core.xml` nos `.docx`/`.xlsx` (`dc:creator`, `cp:lastModifiedBy`), e
dicionário de informações nos `.pdf` (`Author`). **27 valores distintos**, dos quais 7 não são
pessoa (`DELL`, `CMO`, `RIMA`, `Computador`, `Admin`, `Usuario`, `python-docx`) e **20 são nome de
pessoa** — médicas do PCMSO (incluindo a coordenadora nomeada nos próprios documentos), pessoal do
escritório, engenheiros de terceiros e o do Diovanni.
Reproduz, desde 003.FJ, por instrumento versionado: `python -m scripts.varrer_acervo_lgpd`, que
imprime `valores distintos no campo de autoria: 27 = 20 nomes de pessoa + 7 de conta generica/
equipamento excluidos NESTA medicao` — a conta fecha na própria linha, e o tamanho da lista do
filtro (8 entradas) sai declarado ao lado, separado do que foi de fato excluído.

> **Correção 003.FJ-C3 (08/09/2026).** A redação anterior citava a saída como
> `"20 distintos (excluidos 8 …)"`, e `20 + 8 = 28` contra os **27** medidos. O `8` era o
> **tamanho da lista** `VALORES_NAO_PESSOA`, não o que apareceu no acervo: `Microsoft Office Word`
> está no filtro e nunca ocorreu. O script emitia número sem o escopo que o produziu — **o próprio
> invariante que ele instala, violado por ele**. Corrigido na fonte do script (`excluidos_nesta_medicao()`)
> e aqui. Achado pela 3ª rodada do `/critico`. Os comandos avulsos seguem valendo para conferência
pontual: `file -b <arquivo.doc>` para OLE2; `unzip -p <arquivo.docx> docProps/core.xml` para OOXML;
`pdfplumber.open(p).metadata["Author"]` para PDF.

> **Correção 003.FI-C2 (04/09/2026).** A primeira redação desta DH dizia **40 arquivos / 16 nomes**.
> Estava errada por **escopo não declarado**: o `40` era rendimento sobre os **45 não-PDF**, e os
> **38 PDFs não tinham sido varridos**. Re-medido sobre os 83, os números são os acima. O `/conferir`
> a frio marcou o `40` como DIVERGE por não bater com partição medível alguma (83 total, 38 PDF,
> 45 não-PDF) — e o achado, ao ser reproduzido, revelou um escopo maior, não menor. Oito nomes só
> existem nos PDFs.

**Por que é eixo próprio e não nota na `DH-003FE-01`.** Aquela mede dado pessoal no **conteúdo**, e
foi dispensada sobre esse eixo. Este dado está no **cabeçalho do arquivo**: nenhuma varredura de
conteúdo o encontra, nenhuma redação de corpo o remove, e ele viaja junto do binário para qualquer
lugar em que o arquivo seja aberto. A dispensa de 29/08 não foi tomada com este custo à vista —
mesma forma do argumento que a própria `DH-003FH-02` usou para não se deixar cobrir por ela.

**Classificação, e ela não é alarmante.** Dado pessoal **comum** (LGPD art. 5º I) de profissional
identificado no exercício da função — mesma faixa do CRM e do CREA que os documentos já publicam no
corpo, e o repositório é privado. **Não** é dado sensível, **não** é dado de trabalhador sob
vigilância de saúde. Não muda o veredito de `DH-003FE-01`.

**Não-bloqueante, e o custo de limpar é medido.** Limpar exigiria reescrever os **64** binários e
o histórico que já os contém — o mesmo custo desproporcional que dispensou a `DH-003FE-01`. A decisão
é do Arquiteto; esta DH existe para que o fato esteja registrado antes de alguém redescobri-lo.

**Status:** ABERTA. Registro de fato medido, não pedido de trabalho.

### DT-(sessão não numerada, branch `claude/youthful-lamport-3kfkog`)-01 — Nível de risco psicossocial do PGR bruto (COPSOQ) é boilerplate, não sinal por GHE `[RESOLVIDA — R-PSY-03/R-PSY-02 DEPRECATED, sessão branch claude/fervent-brown-7dcc0y]`

**Origem.** Handoff da sessão que abriu o PR #335 (branch `claude/festive-gates-soy0fr`): tabela
manuscrita das Dras. Carolini e Patrícia, não baseada em norma, cruza tipo de atividade (Trabalho
em Altura/Espaço Confinado × Sem Atividade Crítica) com nível de risco psicossocial (baixo/médio/
alto, corte SRQ-20≥7) para decidir Avaliação Psicossocial/Av. Médica de Saúde Mental — em aparente
contradição com `R-PSY-02` (`quando: todo_trabalhador`, incondicional, `[DERIVADO — corpus de 6
matrizes pós-vigência, 5 clientes, 2 médicas, 284 cargos, 99% de cobertura; grupo de controle de 13
matrizes pré-vigência em ~0%]`, sucede `R-PSY-01` DEPRECATED que era condicionada a atividade
crítica). Hipótese não testada proposta no handoff: se nenhum PGR real jamais declara risco
psicossocial baixo, os 99% incondicionais deixam de contradizer a tabela nova — decidiria se
`R-PSY-02` precisa revisão.

**Medido — refuta a hipótese, por motivo mais específico que "baixo existe".** Abertos os 2 PGRs
brutos do acervo com par mais recente medido (Fascino, Aurora Lago das Rosas), seção "26.1
INVENTÁRIO DE RISCOS PSICOSSOCIAIS" (COPSOQ II-BR/AQUALI-RPS, 9 fatores, Matriz 5×5 P×S)
`[MEDIDO — pdfplumber desta sessão; Fascino páginas 90-91, Aurora páginas 75-76]`:

- **BAIXO aparece, predominante nos 2 documentos:** 7-8 de 9 fatores BAIXO, 1-2 MODERADO, nenhum
  ALTO.
- **Mas a tabela é boilerplate, não medição por GHE.** Texto **idêntico** — mesma lista de cargos
  (Armador, Carpinteiro, Eletricista, Servente, Pedreiro etc.), mesmas descrições de fator, quase
  os mesmos valores P×S — nos 2 PGRs, de 2 empresas distintas. O próprio documento rotula a tabela
  de "modelo": "Replicar o modelo acima para cada função/cargo... obrigatório para a validade do
  PGR (NR-01 subitem 1.5.6.1 alínea 'a')" — e nenhum dos 2 PGRs replica. Aparece **uma vez**, sob
  um GHE genérico ("TÉCNICO ADM/OPERACIONAL"), nunca sob GHE-06 Administração nem GHE-19 Vendas
  (os GHEs citados no handoff como "aparentemente baixo risco").
- Os cartões de perigo de GHE-06 Administração e GHE-19 Vendas (Fascino, páginas 43 e 88) **não
  têm linha Psicossocial própria** — só uma nota remetendo ao item 26.1 genérico.
- **Instrumentos diferentes, não sobrepostos.** O PGR usa COPSOQ (por GHE nominal, quando
  preenchido). A tabela das doutoras usa corte SRQ-20≥7 — questionário clínico autoaplicado ao
  trabalhador individual, cujo resultado só existe depois do exame; não é dado extraível do texto
  do PGR.

**Leitura.** O eixo "nível de risco psicossocial" da tabela das doutoras não pode vir, pelo menos
nos 2 PGRs medidos, de extração do texto do PGR — a seção que existiria para isso é preenchimento
de conformidade genérico (mesmo texto em empresas diferentes), não sinal diferenciado por GHE.
`GHEPGR.psicossocial` (bool, hoje sem nenhuma regra que o leia) não tem de onde vir um nível
baixo/médio/alto real por essa via. Reforça o precedente já escrito na `base_normativa` de
`R-PSY-02` (PGR sem FRPRT — Ricco 2026 Adm — cuja matriz emite mesmo assim, sob a postura de
`D-ARQ-68`): aqui o PGR não está silencioso, está com FRPRT preenchido e predominantemente BAIXO,
e mesmo assim não há, no próprio documento, diferenciação por GHE que pudesse ter alimentado uma
condicional. Os 99% incondicionais medidos e a tabela nova continuam parecendo contraditórios — a
hipótese "PGR nunca declara baixo" está refutada, não confirmada.

**Não implementado.** Decisão sobre revisar `R-PSY-02`, tratar a tabela das doutoras como
instrumento clínico separado (SRQ-20 pós-exame, não gatilho de pré-exame), ou pedir sessão
CONHECIMENTO com a Dra. Carolini sobre a origem real do eixo "nível de risco psicossocial" da
tabela é do Arquiteto. Divergência entre medição real e a hipótese do handoff é bloqueador nomeado
(regra do `CLAUDE.md`) — registrado, não ajustado para bater com a hipótese.

**Numeração.** Sessão aberta pelo harness na branch `claude/youthful-lamport-3kfkog`, sem número
`003.F?` atribuído — mesma classe de desvio já declarada em 003.FI/003.FJ/003.FK/003.FL e na
sessão do PR #335. ID desta DT fica sem sessão numérica até o Arquiteto rotular; número não
fabricado aqui.

**Status:** ABERTA, não-bloqueante. Bloqueia decisão clínica sobre `R-PSY-02`, não bloqueia
produção — a regra atual segue rodando como está.

**Atualização — resposta da Dra. Carolini (17/09/2026), duas rodadas.**

Rodada 1, sobre a estrutura da tabela das doutoras: **não é circular.** Trabalho em altura
(atividade crítica) → Avaliação Psicossocial + Av. Saúde Mental, incondicional (bate com
`R-PSY-02` hoje). Sem trabalho em altura → só SRQ-20 (triagem); SRQ-20 ≥ 7 → aí sim Avaliação
Psicossocial. Resolve a objeção original desta DT (SRQ-20 não pode gatilhar o próprio exame que
o mede) — é cascata em 2 estágios, não um único exame se autocondicionando.

Rodada 2, pergunta de fechamento sobre o eixo que falta (nível de risco psicossocial em GHE-06
Administração/GHE-19 Vendas do Fascino, que a matriz assinada de 08/07/2026 mostra recebendo os
dois exames mesmo sem atividade crítica — contradição aparente com a rodada 1): duas respostas.
(1) **"A classificação de risco não sou eu que faço, vem do PGR."** Confirma a direção da
medição desta DT — o eixo deveria vir do documento, não de julgamento clínico ad-hoc — mas não
resolve o problema que a medição achou: nos 2 PGRs conferidos (Fascino, Aurora), a seção do PGR
que deveria carregar esse dado (26.1, COPSOQ) é boilerplate genérico, sem diferenciação real por
GHE. Se a fonte é o PGR e o PGR normalmente não tem esse dado, a pergunta de origem do eixo
continua sem resposta prática — só muda de "quem classifica" para "o documento raramente
classifica".
(2) **A matriz de 08/07/2026 não serve mais de referência — "o protocolo mudou agora, em
setembro; tô refazendo todas as matrizes; não pode olhar por essa aí."** Isto invalida o
documento usado nesta DT como evidência de prática corrente: ele reflete o protocolo ANTERIOR a
setembro/2026, não o que ela descreveu na rodada 1. Consequência direta e mais séria: o corpus
que fundamenta `R-PSY-02` como `[DERIVADO]` — "6 matrizes pós-vigência NR-01, 5 clientes, 2
médicas, 284 cargos, 99% de cobertura" — não tem, até agora, confirmação de que alguma dessas 6
matrizes já é pós-protocolo-de-setembro. Se todas são do protocolo antigo (mesma classe do
documento de 08/07 aqui invalidado), a medição de 99% incondicional está datada — mede a prática
anterior, não a atual, e `R-PSY-02` pode já estar desatualizada mesmo antes de qualquer questão
sobre a tabela das doutoras.

**Atualização — 2 matrizes pós-setembro medidas, achado se inverte (17/09/2026).**

O Diovanni forneceu 2 matrizes novas, ambas pós-mudança de protocolo, com desfechos opostos:

- **Ricco Hetrin, 14/09/2026, VALIDADA** (confirmado pelo Diovanni — não é rascunho). PGR bruto
  correspondente (`matrizes_originais/PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf`,
  197 páginas) lido por completo `[MEDIDO — pdfplumber, 197/197 páginas]`: **zero** ocorrência de
  "psicossocial"/"COPSOQ"/"FRPRT"/"SRQ" em qualquer página. A matriz validada sai com **zero**
  exames psicossociais em **28 de 28 cargos** — inclusive Pedreiro, cujo bloco de risco no PGR
  (página 31) já lista "QUEDAS DE ALTURA" com EPI de cinto paraquedista `[MEDIDO]`. Atividade
  crítica presente no PGR, exame psicossocial ausente na matriz.
- **CMO Residencial Varandas Flamboyant, 16/09/2026, validada por Carolini M. P. Lisita.** Todo
  GHE, incluindo Portaria (Servente, sem atividade crítica), sai com Avaliação Psicossocial +
  Av. Médica de Saúde Mental incondicional — mesmo padrão de sempre.

**Causa, segundo o Diovanni: não é atividade crítica nem nível de risco julgado pela médica — é
decisão do engenheiro que elabora o PGR.** "Quem decide o psicossocial é o PGR. No do Hetrin o
engenheiro não quis ter o psicossocial. Por isso na matriz não tem." Isso refuta a leitura de
cascata por atividade (rodada 1 da Dra. Carolini) — o contra-exemplo do Pedreiro/altura no Hetrin
já bastaria — e é consistente com a rodada 2 ("a classificação vem do PGR"), mas afina o *quem*:
não é uma classificação de risco baixo/médio/alto que alguém preenche no PGR — é uma decisão
binária do engenheiro autor: incluir ou não a seção/inventário de risco psicossocial no documento.
PGR sem a seção → motor não deveria emitir nada. PGR com a seção → emite incondicional para
o PGR inteiro (não há, até agora, evidência de variação por GHE dentro do mesmo PGR).

**Já tem endereço no código, nunca implementado.** `GHEPGR.psicossocial: bool`
(`agente_medico/motor/tipos.py:202`) existe desde `D-ARQ-49` P2 (maio/2026), desenhado
nomeadamente como sinal de PGR-documenta-psicossocial para alimentar o extinto `R-PSY-01` — e
nunca ganhou extrator: `hidratacao.py:133` crava `psicossocial=False` sempre, sem ler o PGR.
`R-PSY-02` (regra viva) não lê o campo — dispara `quando: todo_trabalhador`, incondicional,
independente do PGR.

**Proposta, não implementada — decisão do Arquiteto.**
1. Extrator: detectar no texto do PGR a presença da seção de inventário psicossocial (mesmo
   marcador medido no Fascino/Aurora: "INVENTÁRIO DE RISCOS PSICOSSOCIAIS"/COPSOQ/FRPRT) e
   popular `GHEPGR.psicossocial`.
2. `R-PSY-03` nova (sucede `R-PSY-02` — mudança de escopo de aplicação exige ID nova, mesma
   convenção de `R-PSY-01→R-PSY-02`), `quando: psicossocial`, mesma conduta atual
   (avaliacao_psicossocial + avaliacao_saude_mental, adm/per/MR).
3. `R-PSY-02` sai `[DEPRECATED — fundamento refutado por n=2 pós-protocolo, Hetrin 14/09 ×
   Varandas 16/09, mesmo padrão de D-ARQ-81 aplicado a R-AUD-04]`.

**Risco residual, não resolvido.** N=2 é o piso de reabertura que este projeto já usa (precedente
`poeira_de_madeira`/`DT-003EJ-01`), não uma amostra grande — ambos os PGRs são de obra de
construção civil, mesma classe de risco físico. Não sabemos ainda se a granularidade é por PGR
inteiro (medido: sim, nos 2 casos) ou se pode variar por GHE dentro do mesmo PGR quando o
elaborador documenta parcialmente. Sem pergunta nova pra Dra. Carolini — ela já indicou não ter
mais paciência para esta rodada; a decisão de implementar (ou esperar mais um caso) é do
Arquiteto, não pendente de resposta clínica adicional.

**Status atualizado:** ABERTA — de "aguardando matriz nova" para "proposta concreta pronta,
aguardando autorização de implementação". Não bloqueia produção (regra atual, embora com
fundamento refutado, segue rodando sem crash).

**RESOLVIDA (17/09/2026, branch `claude/fervent-brown-7dcc0y`, autorizada pelo Diovanni).**
Proposta implementada tal como registrada acima: `detectar_psicossocial` (`extracao_pgr.py`)
extrai o marcador do PGR inteiro e popula `GHEPGR.psicossocial`; `R-PSY-03` nova (`quando:
psicossocial`, mesma conduta) sucede `R-PSY-02`, que sai `[DEPRECATED — fundamento refutado]`
em `regras.yaml`/`PROTOCOLO_AGENTE_MEDICO.md` §5.7 (PROTOCOLO v93→v94). Risco residual desta DT
(granularidade por PGR inteiro vs. por GHE, n=2) **não resolvido** — fica registrado no corpo de
`R-PSY-03` (`regras.yaml`/PROTOCOLO §5.7), não reaberto aqui como pendência solta. Testes com
reversão nomeada em `test_extracao_pgr.py` (extrator), `test_hidratacao.py`/`test_predicados.py`
(threading + primitivo) e `test_orquestrador.py` (regra fim-a-fim + R-PSY-02 excluída do motor);
quebras legítimas em `test_integracao_002c.py` e o `test_integracao_end_to_end` de
`test_orquestrador.py` corrigidas com causa nomeada (perdem as 2 linhas que só saíam por
R-PSY-02 incondicional). Detalhe completo em HISTORICO_OPERACIONAL.md (bloco desta sessão).

### DT-(sessão não numerada, branch `claude/youthful-lamport-3kfkog`)-02 — Segunda variante do template Ricco Hetrin quebra o reconhecedor de família AIHA `[REENQUADRADA + fix de diagnóstico IMPLEMENTADO — 17/09/2026, branch claude/fervent-brown-7dcc0y; ARQUITETURA da ingestão (peça 5) proposta — 18-19/09/2026, branch claude/dreamy-mayer-os6jce; fatiamento 5a→5b→5c→5d RATIFICADO — 19/09/2026, branch claude/blissful-knuth-riqucz; ainda ABERTA até a IMPL fechar]`

**Origem.** Diovanni reportou erro real no serviço ao tentar gerar a matriz do PGR
`PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf` (197 páginas): `"Parse total falho —
nenhuma matriz gerada (D-ARQ-22)"`, `segmentacao_implausivel: 0 bloco(s) GHE detectado(s) em
documento de 197 páginas`.

**Medido — reproduzido localmente.** `avaliar_estrutura`/`avaliar_familia` direto contra o PDF:
`eh_cabecalho_ghe` = 0 casos, `eh_ancora_card_cargo` = 0 casos, `avaliar_familia` = `None` →
cai no fallback `avaliar_segmentacao`, que bloqueia (`_LIMIAR_PAGINAS_DOC_MINIMO` excedido, 0
blocos). Por `D-ARQ-57`, pendência de estrutura bloqueia **antes** de qualquer tentativa de rota
LLM — não existe hoje workaround no app para este documento específico.

**Causa raiz.** É a MESMA família já reconhecida (grid AIHA, `_reconhece_funcao_grid_perigo_risco`,
regex `r"Função .*Perigo / Risco"` — comentário do código já cita "Hetrin/Serra Dourada" como
caso-âncora). Confirmado no PGR de março/2025 do mesmo Hetrin
(`matrizes_originais/01. PGR RICCO HETRIN - MAR25.pdf`): o cabeçalho aparece **exatamente** como
`"Função Identificação de Perigo / Risco Tempo de Meio de..."`, título-caixa, uma linha só —
casa limpo. No PGR de 14/09/2026 (mesmo cliente, mesma obra), o cabeçalho da tabela virou **TUDO
CAIXA ALTA** e o `pdfplumber` extrai `"FUNÇÃO"` e `"PERIGO/ RISCO"` em **linhas separadas** — dois
motivos independentes de falha (maiúscula E fragmentação de linha), confirmado por busca
case-insensitive: zero linha do documento inteiro casa `"FUN.?.?O.*PERIGO.*RISCO"` mesmo
afrouxando o regex. Não é reversão trivial de 1 linha — o cabeçalho não aparece inteiro em
nenhuma linha extraída, precisa de reconhecedor que junte linhas vizinhas ou case por conjunto de
palavras-chave, não regex de linha única.

**Não implementado.** Escopo de sessão própria (nova família/variante de parser), no molde do
que o projeto já fez para o T65 (`DT-003FE-01`/`DT-003FF-01`). Não tocado nesta sessão —
registrado para não se perder.

**Reenquadramento (17/09/2026, branch `claude/fervent-brown-7dcc0y`) — a causa raiz acima está
incompleta: "casa limpo" no PGR de março era só o teste do regex isolado, não o pipeline
inteiro.** Reproduzido `avaliar_estrutura`/`avaliar_familia`/`parsear_arquivo` direto contra os
dois PDFs reais (`01. PGR RICCO HETRIN - MAR25.pdf` e `PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN
14.09.26.pdf`) `[MEDIDO — execução direta desta sessão]`:

- **PGR mar/2025:** `eh_cabecalho_ghe`=0, `eh_ancora_card_cargo`=0, `_reconhece_funcao_grid_perigo_risco`=**123** casos → `avaliar_familia` retorna `Pendencia(tipo="pgr_cargo_based", bloqueante=True, motivo="...recorte-GHE inaplicável")`. **Também bloqueado hoje** — não gera matriz.
- **PGR set/2026 (14/09):** mesmos reconhecedores GHE/card = 0; `_reconhece_funcao_grid_perigo_risco`=**0** (cabeçalho em caixa alta e fragmentado em linhas, como já diagnosticado) → `avaliar_familia` retorna `None` → cai no fallback `avaliar_segmentacao`, que bloqueia como `segmentacao_implausivel`.
- `parsear_arquivo` (`parser_familia_consciente.py`, D-ARQ-65) devolve **0 blocos para os dois arquivos**, sem `FamiliaNaoReconhecida` — não por bug, mas porque esse módulo é o parser determinístico da família **Consciente/Fascino** (cabeçalho `GRUPO/PERIGO-ASPECTO/FONTE/AGRAVO`, D-ARQ-65), inteiramente distinta do grid AIHA Hetrin/Serra Dourada (`Função ... Perigo/Risco`). Confundir os dois nomes ("reconhecedor da família AIHA") foi o erro de leitura da sessão anterior.

**O achado que muda o escopo.** `D-ARQ-57` peça 3 (003.CQ) e a decisão da peça 4 (003.DC,
ratificada pelo Diovanni) **excluem deliberadamente** o grid AIHA do recorte-por-cargo que foi
construído: *"grid-header AIHA Hetrin/SD **FORA** [do repertório de recorte] — sinal-de-família
≠ âncora-de-recorte... o grid AIHA não delimita card individual (é cabeçalho de tabela
compartilhada)"* (D-ARQ-57, notas 003.DC/003.DF). O recorte-por-cargo 1:1 que a peça 4 entregou
(`recortar_cards_cargo`) serve só Cjr (`CARGO-CBO`) e EBSERH (`Lotação:`-tripla) — famílias
"1 card = 1 cargo autocontido". O grid AIHA é estruturalmente diferente: **1 tabela
compartilhada, N linhas-de-cargo** — mais parecido com a tabela de risco do Fascino (D-ARQ-65)
do que com um card EBSERH, mas sem cabeçalho-GHE numerado para segmentar por GHE. **Conclusão:
a família Hetrin/Serra Dourada nunca teve caminho de ingestão automática — nem antes nem depois
da mudança de cabeçalho de setembro.** `_reconhece_funcao_grid_perigo_risco` sempre foi só
diagnóstico (classificar corretamente como `pgr_cargo_based` para revisão humana), nunca um
passo rumo a parsear a tabela.

**O que o conserto do regex ainda vale — e o que não vale.** Ajustar o reconhecedor para casar o
cabeçalho em caixa-alta/fragmentado (a causa raiz textual, que segue correta) restauraria a
pendência **correta** (`pgr_cargo_based`, "recorte-GHE inaplicável") no PGR de setembro, em vez
da atual `segmentacao_implausivel` (que sugere anomalia estrutural, não família reconhecida e
deliberadamente não-automatizada) — ganho real de qualidade de diagnóstico para quem revisa. **Não
gera matriz em nenhum dos dois casos** — mar/2025 já está bloqueado hoje pelo mesmo
`pgr_cargo_based`, sem ninguém ter notado por não ter sido tentado em produção.

**Escopo real de "resolver" o Hetrin/Serra Dourada é maior que uma variante de parser — é uma
peça nova, irmã da peça 4.** Precisaria: (1) decidir a unidade de recorte de uma tabela
compartilhada por linha-de-cargo (não card, não GHE — molde mais próximo é a extração de linhas
de risco do Fascino em `parser_familia_consciente.py`, D-ARQ-65, mas sem os blocos-GHE que lá
segmentam por GHE); (2) ARQUITETURA própria (molde D-ARQ-57 peça 4 / D-ARQ-65), não fatia
avulsa — mesmo padrão que `DT-003FE-01` virou `DT-003FF-01` ao ser investigada a fundo (T65: "o
gargalo é a família de conteúdo", não a âncora). Precedente direto de escopo subestimado citado
por engano nesta própria DT.

**Fix de escopo contido, implementado (17/09/2026, mesma branch, autorizado pelo Diovanni — só o
regex, não a arquitetura de ingestão).** `_reconhece_funcao_grid_perigo_risco_fragmentado` novo em
`extracao_pgr.py`, casa o cabeçalho quebrado em 2 linhas adjacentes (`\b`-delimitado, anti-prosa),
integrado em `avaliar_familia`. Restaura a pendência **correta** no PGR de 14/09/2026:
`pgr_cargo_based` em vez de `segmentacao_implausivel`. Validado contra os 40 PGRs reais do acervo
— só este documento muda de classificação. 15 testes com reversão nomeada, varredura inversa
15/15 confirmada. Nota de aplicação em `D-ARQ-57` (`DECISOES_ARQUITETURAIS.md`). Detalhe em
HISTORICO_OPERACIONAL.md (bloco desta sessão).

**Status:** REENQUADRADA, fix parcial IMPLEMENTADO. Deixou de ser "bug de regressão" (nunca
funcionou) e passou a ser "família nunca implementada, exclusão deliberada de D-ARQ-57/D-ARQ-65".
O conserto do regex acima corrige o DIAGNÓSTICO (pendência certa, revisão humana informada
corretamente) — **não gera matriz** em nenhum PGR Hetrin/Serra Dourada, nem no de março/2025 nem
no de setembro/2026: ambos bloqueiam hoje, corretamente, para revisão humana. Gerar matriz exige
ARQUITETURA própria (unidade de recorte de tabela compartilhada por linha-de-cargo, molde D-ARQ-57
peça 4/D-ARQ-65) — escopo e prioridade a definir pelo Arquiteto, não aberta nesta sessão.

**Nota (sessão branch `claude/dreamy-mayer-os6jce`, 18-19/09/2026) — ARQUITETURA da peça 5 proposta; DT segue ABERTA.** A ARQUITETURA pedida acima foi feita: `D-ARQ-57`, andamento "ARQUITETURA da peça 5" (`DECISOES_ARQUITETURAIS.md`). Medição própria contra os 3 witnesses reais (`01. PGR RICCO HETRIN - MAR25.pdf`, `01. PGR RICCO SERRA DOURADA - MAI.24 1.pdf`, `PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf`) refina a hipótese desta DT ("molde mais próximo é a extração de linhas de risco do Fascino") para uma recomendação testada: banda de coluna calibrada por bloco (`PalavraPDF`, molde exato de `parser_familia_consciente.py`/D-ARQ-65), não `pdfplumber.extract_tables()` — que funciona nos 2 witnesses limpos mas é frágil no witness do chamado real (Hetrin/set-2026, coluna sem grade estável, o mesmo sintoma que já tinha feito o projeto abandonar bandas fixas no Fascino). Fatiamento proposto 5a-5d (5a/5b: recorte + decomposição N:1; 5c: transcrição da célula de risco; 5d: roteamento + plug + e2e, só aqui esta DT fecha) — nenhuma fatia implementada nesta sessão. Achado nomeado: o witness do chamado real (Hetrin/set-2026) é o mais instável dos 3 e só é destravado nas fatias 5b/5d, não na 5a — se a prioridade é esse documento específico, a ordem do fatiamento precisa de decisão explícita do Arquiteto/Diovanni antes da IMPL. Escrita autorizada pelo usuário desta sessão ("pode gravar"); ratificação formal do Diovanni sobre o fatiamento/prioridade não registrada neste turno. `[ARQUITETURA — sessão branch claude/dreamy-mayer-os6jce]`

**Nota (sessão branch `claude/blissful-knuth-riqucz`, 19/09/2026) — fatiamento ratificado pelo Diovanni; DT segue ABERTA.** Decisão: manter 5a→5b→5c→5d, sem reordenar para priorizar o witness Hetrin/set-2026 antes de 5a calibrado nos 2 witnesses limpos — o risco nomeado na nota acima fica aceito, não mitigado. Detalhe da ratificação em `D-ARQ-57` (`DECISOES_ARQUITETURAIS.md`). Esta DT permanece ABERTA — fecha só na fatia 5d; nenhuma fatia implementada nesta sessão (docs-only). `[RATIFICADO — Diovanni; sessão branch claude/blissful-knuth-riqucz]`

**Nota (mesma sessão, mesmo dia) — fatia 5a IMPLEMENTADA; DT segue ABERTA (fecha só na 5d).** `agente_medico/motor/parser_familia_grid_aiha.py`: banda de coluna + fronteira de função, validado contra os 2 witnesses limpos (nomes e contagens de linha exatas). A medição desta fatia corrigiu a hipótese de ambiguidade registrada na nota de ratificação acima — era artefato de um bug de agrupamento de linha (rótulo colidindo com outras colunas no mesmo `top`), não estrutura real do grid; corrigido, `TrechoAmbiguo`/`Pendencia` não entraram no código. Detalhe completo em `D-ARQ-57` (`DECISOES_ARQUITETURAIS.md`, nota "Fatia 5a IMPLEMENTADA") e HISTORICO (bloco desta sessão). Próximo: 5b (decomposição N:1, caso do witness instável Hetrin/set-2026). `[IMPLEMENTADO — sessão branch claude/blissful-knuth-riqucz]`

**Nota (sessão branch `claude/nice-ptolemy-wxk1wo`) — bloqueador medido ao abrir a 5b: zero N:1 real acessível; DT segue ABERTA.** Medição contra os 2 witnesses calibrados (`segmentar_arquivo` real, intervalo cheio) achou 3 candidatos com `/` no nome (Hetrin/mar: `Encarregado de Encanador/Hidráulica`, `Comprador / Compradora`, `Engenheiro Civil / Planejamento`; Serra Dourada: 0) — nenhum é N:1 genuíno: o texto cru sob cada um descreve 1 papel só (par de gênero ou título composto), não uma lista de cargos distintos compartilhando 1 grupo de risco. O N:1 real (molde do exemplo da ARQUITETURA) só existe em Hetrin/set-2026, e esse witness não é alcançável pela fatia 5a — `segmentar_arquivo` levanta `GrupoFuncaoNaoReconhecido`: o grid desse documento usa cabeçalho `'FUNÇÃO'`/`'TIPO'` em CAIXA ALTA (medido pág. 14, 0-indexed) contra o title-case (`'Função'`/`'Tipo'`) que `_localizar_cabecalho_grid` exige — nenhuma página do documento tem `'Função'` exato fora de uma tabela não-relacionada (EPI-por-função, pág. 62). Bloqueador reportado, sem código de produção nesta sessão; decisão de como prosseguir (generalizar o reconhecedor de cabeçalho antes de decompor N:1, redefinir escopo da 5b, ou outra ordem) cabe ao Arquiteto. Detalhe completo em `D-ARQ-57` (`DECISOES_ARQUITETURAIS.md`, nota "Bloqueador medido ao abrir a fatia 5b") e HISTORICO (bloco desta sessão). `[MEDIDO — sessão branch claude/nice-ptolemy-wxk1wo; bloqueador reportado, decisão do Arquiteto]`

**Nota (mesma sessão, mesmo dia) — medição aprofundada e decisão do Diovanni: não perseguir Hetrin/set-2026 agora; DT segue ABERTA.** A pedido do Diovanni, medi o que "aceitar cabeçalho CAIXA ALTA" exigiria de fato: banda Função ~50-83pt (bem mais estreita que os 2 witnesses limpos, quase 1 palavra por linha física); o único caso N:1 real do documento (pág. 14, 6 cargos: Engenheiro Civil/Engenheiro Residente/Estagiário de Engenharia/Apontador/Administrativo de Obra/Técnico de Segurança do Trabalho) tem o separador `/` **ausente** entre 2 dos 6 nomes no texto extraído; e o cabeçalho **não repete em toda página** do intervalo (pág. 32 sem `'FUNÇÃO'`/`'TIPO'`) — quebra o contrato "recalibra por página" da fatia 5a. Achado que decidiu a sessão: mesmo com a 5b completa pra esse witness, o documento não ingere hoje — faltam 5c/5d, nenhuma implementada — já cai em revisão humana, gated by design (mesma classe HUMAP/Cjr, `DT-003DK-01`), sem risco de dado errado. **Decisão do Diovanni: não perseguir a calibração do Hetrin/set-2026 agora**, revisitar quando houver sinal se é template novo do cliente Ricco (a partir de 14/09/26) ou formatação pontual desse envio. Detalhe completo em `D-ARQ-57` (`DECISOES_ARQUITETURAIS.md`, nota "medição aprofundada") e HISTORICO (bloco desta sessão). `[MEDIDO — sessão branch claude/nice-ptolemy-wxk1wo; decisão do Diovanni]`

### DT-(sessão não numerada, branch `claude/dreamy-mayer-os6jce`)-01 — Relatório de rastreabilidade/proveniência da matriz (origem de cada risco/exame, por-que da decisão do motor) `[ABERTA — proposta registrada, sem ARQUITETURA própria]`

**Origem.** Pedido do usuário nesta sessão, durante a revisão da auditoria comparativa da matriz Aurora Lago das Rosas (comparativo app × matriz aprovada pelas médicas): a matriz de exames deveria vir acompanhada de um relatório explicando de onde o app tirou cada risco, de onde tirou cada exame e por que decidiu o que decidiu — não necessariamente uma "auditoria", mas rastreabilidade suficiente para a médica coordenadora entender a origem de uma decisão do app sem precisar reconstruir manualmente a cadeia PGR→regra→exame (exatamente o trabalho que a auditoria Aurora precisou fazer à mão).

**Situação atual.** Parte do mecanismo já existe, mas não sobrevive além da execução:
- Toda regra clínica já carrega `R-CATEGORIA-NN` e a fonte normativa em comentário/docstring — convenção fixa deste projeto (`CLAUDE.md`, seção "Código"), auditável no código-fonte mas não no artefato final entregue à médica.
- `Pendencia` já carrega `tipo`/`bloqueante`/`destinatario`/`regra_origem` (D-ARQ-57 e outras decisões reusam esse mecanismo) — mas só para o que ficou em dúvida ou foi rejeitado, nunca para o que **entrou** na matriz.
- Para os exames que efetivamente saem no `.docx` final, a cadeia agente-do-PGR → regra que disparou → periodicidade/evento aplicado é calculada em runtime e descartada assim que o Word é gerado. Não há hoje nenhum dado de proveniência persistido para o caminho feliz (só para o caminho de pendência).

**Escopo real — não é ajuste de relatório, é mudança de arquitetura.** Cada ponto do motor (`agente_medico/motor`) que hoje retorna só o valor final (periodicidade, evento, exame) precisaria passar a retornar valor + proveniência (qual agente do PGR, qual regra, qual decisão de periodicidade/evento). Isso toca o núcleo do motor, não a superfície de geração do `.docx` — não é um prompt de implementação direto, é candidato a sessão ARQUITETURA própria (levantar onde exatamente a proveniência se perde hoje, decidir a forma do dado de rastro, decidir se ele é gerado sempre ou só sob flag, decidir onde/como aparece no documento entregue).

**Não medido nesta sessão.** Nenhum ponto específico do motor foi inspecionado para confirmar exatamente onde a proveniência se perde nem qual seria o formato do dado de rastro — a avaliação acima é qualitativa, feita em conversa, sem leitura de código. Antes de virar D-ARQ precisa da mesma disciplina de medição que `D-ARQ-57`/`D-ARQ-65` já seguem: ler o motor real, nomear os pontos de perda, medir contra um caso-âncora.

**Priorização.** Deliberadamente adiada nesta sessão — o usuário escolheu fechar a arquitetura do grid AIHA primeiro (`D-ARQ-57` peça 5, acima) e registrar este item "no gatilho" para não se perder. Nenhuma prioridade relativa foi definida entre este item e a fatia 5a-5d de D-ARQ-57.

**Status:** ABERTA. Aguardando sessão ARQUITETURA própria (medição real do motor, molde D-ARQ-57/D-ARQ-65) antes de qualquer código. `[DERIVADO — discussão em chat desta sessão, sem leitura de código; escrita autorizada pelo usuário, "pode gravar"]`

**Nota (sessão branch `claude/blissful-knuth-riqucz`, 19/09/2026) — prioridade definida pelo Diovanni: D-ARQ-57 peça 5 fecha primeiro.** Nenhuma sessão ARQUITETURA para este item antes de `D-ARQ-57` peça 5 chegar à fatia 5d (`pgr_cargo_based`/grid AIHA vira ingestão real). Decisão de sequenciamento de trabalho entre duas frentes arquiteturais abertas, não de arquitetura desta DT — escopo, pontos de perda de proveniência no motor e forma do dado de rastro seguem exatamente como descritos acima, nada medido nesta sessão. `[DECISÃO DE SEQUENCIAMENTO — Diovanni; sessão branch claude/blissful-knuth-riqucz]`

**Nota (sessão branch `claude/cool-babbage-whh1zw`, 26/09/2026) — sequência trocada pelo Diovanni; virou `D-ARQ-87`, fatia 1 IMPLEMENTADA.** O Diovanni pediu o item antes de `D-ARQ-57` 5d. A medição no código corrigiu a premissa acima: a proveniência do caminho feliz já persiste em `Motivo` (`D-ARQ-22` Parte B, `D-ARQ-72`) e aparece na revisão da tela. O que se perdia era o que cada regra pediu antes do piso da consolidação (periodicidade e momentos) e o texto da base normativa — fechado na fatia 1. Seguem abertas: fatia 2 (memorial `.docx` para as médicas) e fatia 3 (retorno das correções pelo código da linha). **Status:** ABERTA até a fatia 2.

### DT-(sessão claude/nice-ptolemy-wxk1wo)-01 — Casamento manual FDS↔produto do PGR: falta o elo que liga a composição extraída ao `ProdutoQuimico` certo `[RESOLVIDA — fatia 2b IMPLEMENTADA, sessão claude/003ff-fatia2b]`

**Origem.** Pedido do Diovanni nesta sessão: a tela só tinha upload de PGR; produtos químicos (CAS, agravos à saúde) vêm da FDS/FISPQ e complementam o PGR/PCMSO. Fatia 1 (`D-ARQ-47`, nota de aplicação desta sessão) já sobe: `pagina_matriz()` aceita upload avulso de FDS, roda `preparar_composicao` (extração real + transcrição-LLM + gate de forma) e mostra CAS/nome/frases-H na tela — com ou sem PGR.

**O que falta.** A composição extraída da FDS não está ligada a nenhum `ProdutoQuimico` do PGR (`GHEPGR.produtos_quimicos`, `motor/tipos.py`) — sem esse elo, `FDS.composicao_verbatim` nunca é populado em produção, `resolver_composicao`/`executar_com_composicao` (já rodam dentro de `processar_pgr`, D-ARQ-40) não têm o que resolver, e o CAS/frase-H da FDS nunca chega em `Risco.materialidade`/exame emitido. Decisão já tomada com o Diovanni (não automática): pra cada FDS enviada, o usuário escolhe MANUALMENTE, numa lista, qual `ProdutoQuimico.nome` do PGR ela corresponde — casamento automático por nome foi descartado por risco de vínculo errado e silencioso (classe D-ARQ-22).

**O que a implementação vai precisar (não medido/desenhado ainda).**
1. Expor uma lista de candidatos pra tela escolher — hoje `_rodar_parse_deterministico`/`processar_arquivo_pgr` devolvem `Resultado` (matrizes já resolvidas), não o `PGR` hidratado antes da resolução de composição.
2. Uma forma barata de RE-rodar só a resolução de composição (`processar_pgr`/`executar_com_composicao`, sem custo de LLM/parse de PDF) depois que o usuário escolhe o casamento — hoje isso é tudo feito numa passada só dentro de `processar_arquivo_pgr`. Provável separação: uma função que devolve o `PGR` hidratado (caro, cacheável) + uma chamada barata de `processar_pgr` sobre esse `PGR` já com o `fds` do produto casado anexado (`dataclasses.replace`).
3. UI: `st.selectbox` por FDS enviada, listando os candidatos do PGR já parseado; sem PGR processado, a FDS fica só no modo avulso (fatia 1, sem casamento — comportamento já existente).

**Achado que travou a retomada (mesma sessão, ao reabrir esta DT) — `GHEPGR.produtos_quimicos` NÃO existe em produção; a suposição do item 1 acima estava errada.** `hidratar_pgr` (`motor/hidratacao.py:137`) crava `produtos_quimicos=()` sempre — o comentário da própria linha 17 nomeia o motivo: "EPIs, produtos_quimicos e cenario ficam em default (diferidos, `D-ARQ-49 P2`)". Não é um dado já extraído esperando ser exposto na tela — é um campo deferido desde a arquitetura original do parse-PGR, nunca implementado. Construir a extração formal (nome de produto químico por GHE, a partir do texto do PGR) é trabalho do tamanho da própria `D-ARQ-49` (sessão de medição própria), não algo que cabe dentro desta fatia.

**Alternativa considerada — reusar `RiscoVerbatim.agente`/`fonte_geradora` como substituto da lista de produto.** Esses campos JÁ existem (`GHEVerbatim`/`RiscoVerbatim`, `D-ARQ-49` Parte 2/nota 003.BN) e carregam o texto cru do risco declarado — plausivelmente o mesmo nome do produto na maioria dos casos ("Tinta acrílica", "Solvente"). O refactor caro/barato (item 2 acima) seria o MESMO trabalho independente da fonte da lista — não é jogado fora se a extração formal vier depois, só troca de onde a `selectbox` lê as opções. **Não seguido nesta sessão** porque a qualidade de `agente` como "nome de produto" não foi medida contra um PGR real — pode vir limpo ou misturado com risco não-químico (ex. "Ruído contínuo", que não corresponde a produto nenhum) —, e é o usuário real escolhendo na tela; ruído na lista pesa mais que noutro contexto.

**Decisão do Diovanni: parar aqui.** Não implementar fatia 2 nesta sessão, nem pelo caminho da extração formal (D-ARQ-49 P2, fora de escopo/tamanho) nem pelo substituto (`agente`/`fonte_geradora`, não medido). Dois caminhos nomeados pra retomada, nenhum escolhido: (a) medir como `agente`/`fonte_geradora` aparece num PGR real antes de decidir se o substituto serve; (b) abrir sessão de arquitetura própria pra `D-ARQ-49` Parte 2 (extração formal de `produtos_quimicos`) direto.

**Caminho (a) medido (mesma sessão, mesmo dia) — substituto descartado por dado real, não por cautela.** `parsear_arquivo` (`parser_familia_consciente.py`, D-ARQ-65, determinístico — sem LLM, sem chave) contra o PGR real da família Consciente/Fascino (`matrizes_originais/PGR - CONSCIENTE... FASCINO (15.07.26).pdf`): 19 GHEs, 237 riscos. Achado: a granularidade de `agente`/`fonte_geradora` não é "produto", é **componente químico individual dentro de um grupo por atividade** — `fonte_geradora="Exposição a tintas e seus componentes."` sozinha agrupa ~15 `agente` distintos (`Destilados (Petróleo) leves tratados com hidrogênio`, `Tolueno`, `Etanol`, `Metiletilcetona`, `Xileno`, `Dióxido de Titânio`, `Óxido de Ferro Amarelo`...) — a tabela de composição de 1 produto (tinta), já decomposta ingrediente-a-ingrediente no próprio texto do PGR. Mesmo padrão em `"Na execução do trabalho de encanação"` (Hidróxido de sódio, Acetona, Acetato de etila, Copolímero de PVC...) e soldagem (Silicato de alumínio, Ferro, Manganês, Quartzo...). **Não é 1:1** (1 `agente` = 1 produto): é 1 FDS : N linhas de `agente` — o inverso do N:1 medido na fatia 5b (`D-ARQ-57`) mais cedo nesta sessão. Uma `selectbox` de `agente` pra escolher "qual corresponde a esta FDS" obrigaria o usuário a saber que 15 itens da lista são o mesmo produto — não tem 1 item limpo pra apontar. Substituto descartado — confirma, com dado real, que a rota (a) não serve como concebida (casamento 1 FDS : 1 `agente`); resta a rota (b), e ela precisa decidir algo novo: casar a FDS num **grupo de riscos** (por `fonte_geradora`), não num produto único nomeado, porque o PGR (ao menos este witness) não nomeia produto — só declara os componentes. De passagem: achei uma linha corrompida (`"Bater contra ou ser atingido por (trânsito)..."`) — já é defeito conhecido e registrado (`DT-003L-01`, nota acima nesta mesma seção), nada novo. `[MEDIDO — parsear_arquivo real contra o Fascino, sessão claude/nice-ptolemy-wxk1wo; decisão de parar de novo é do Diovanni]`

**Status:** ABERTA. Não-bloqueante: a fatia 1 (extração avulsa, `PR #345`) já entrega valor sozinha. Único caminho de retomada agora: (b) — sessão de arquitetura própria pra `D-ARQ-49` Parte 2, decidindo a unidade de casamento como grupo-por-`fonte_geradora`, não produto nomeado. `[DERIVADO — pedido do Diovanni nesta sessão; leitura de `orquestracao_pgr.py`/`web_matriz.py`/`motor/entrada.py`/`motor/hidratacao.py`/`D-ARQ-49`; medido contra o Fascino real; decisão de parar é do Diovanni]`

**Caminho (b) aberto (sessão `claude/sharp-wozniak-j4596a`) — o próprio agrupamento por `fonte_geradora` é rejeitado; achado novo muda a forma da fatia.** Medido de forma reproduzível contra o mesmo Fascino (`parsear_arquivo`, função já versionada, 19 GHEs/237 riscos): grupos FÍSICOS de `n=2` (`'Operação de máquinas...'` → `['Ruido', 'Vibrações localizadas (mão e braço)']`; `'Poeiras geradas no processo produtivo...'` → `['Sílica livre', 'Poeira respirável']`) contra QUÍMICOS reais de `n=10`/`n=8`/`n≈15` — lacuna limpa NESTE witness, mas sem garantia estrutural de que um PGR diferente não combine 3+ agentes físicos sob 1 `fonte_geradora` (Ruído/Vibração/Radiação aparecem separadas noutros GHEs deste mesmo documento); cravar corte de `n` sem essa garantia inventa categoria sem fonte (D-ARQ-22). Pior: `stage_3_pendencias_estruturais`/R-PGR-04 (`estagios/pendencias_estruturais.py:7-19`, `[VALIDADO]`) emite pendência BLOQUEANTE `composicao_ausente` para todo `produto.fds is None` — nunca disparou até hoje porque `produtos_quimicos` sempre foi `()`; populá-lo automaticamente sem garantia estrutural de filtro arriscaria disparar essa regra falsamente em GHEs físicos que este witness não mostrou (Ruído/Vibração/Postural/Trabalho-em-Altura não são "produto químico" e não deveriam exigir FDS). Nenhuma das duas sessões anteriores (v197/v198) tinha olhado `pendencias_estruturais.py` — achado novo desta sessão, não repetição.

**Decisão de arquitetura revisada.** `produtos_quimicos` NÃO é extraído na hidratação (zero mudança em `hidratar_ghe`/`hidratar_pgr` — sem regressão de R-PGR-04). O RT passa a CRIAR o `ProdutoQuimico` explicitamente na tela (fatia 2b), ao anexar uma FDS avulsa a um GHE do PGR já carregado — o slot só nasce com `fds` já populada, nunca `None` órfão, então R-PGR-04 nunca dispara por essa via (seu gatilho original — PGR aponta produto sem dar composição — segue não-implementado, declarado, não escondido). Fatia 2a: split cheap/expensive em `processar_arquivo_pgr` (expor o `PGR` hidratado antes de `processar_pgr`, sem reprocessar PDF/LLM a cada rerun do Streamlit). Detalhe completo, discriminantes e fronteiras: `DECISOES_ARQUITETURAIS.md` v199 (nota em `D-ARQ-49`).

**Ratificado (mesma sessão, 20/09/2026).** Diovanni ratifica a decisão acima como desenhada (RT cria o produto na tela; fatiamento 2a→2b sem reordenar). Gap do Crítico (universalidade em indústria química não medida) aceito, não mitigado. Detalhe: `DECISOES_ARQUITETURAIS.md` v200 (ratificação em `D-ARQ-49`).

**Fatia 2a implementada (sessão `claude/blissful-johnson-mdeqn5`).** `preparar_pgr_hidratado` extraída em `orquestracao_pgr.py` (`preparar_ghes` -> `hidratar_pgr`, parando antes de `processar_pgr`); `processar_arquivo_pgr` vira wrapper fino sobre ela + `processar_pgr`, mesmo comportamento externo (suíte existente verde, sem teste novo — discriminante nomeado na ARQUITETURA v199/v200). Detalhe: `DECISOES_ARQUITETURAIS.md` v201 (nota de aplicação em `D-ARQ-49`).

**Fatia 2b implementada (sessão `claude/003ff-fatia2b`).** UI em `web_matriz.py`: com um PGR já carregado na tela (`cache.pgr_hidratado is not None`) e uma FDS avulsa com composição extraída, `pagina_matriz()` oferece `st.selectbox` sobre os GHEs do PGR + `st.text_input` do nome do produto (pré-preenchido com o nome do arquivo, decisão de tela — `fonte_geradora` não sobrevive à hidratação, então não é usada como referência: trazê-la exigiria reabrir a fronteira ratificada de `preparar_pgr_hidratado`, fora do escopo desta fatia). Ao confirmar, `anexar_produto_e_reprocessar` (núcleo puro, sem streamlit) cria `ProdutoQuimico(nome, fds)` já com `fds` populada (nunca `None` órfão — R-PGR-04 não dispara por esta via, como previsto na ARQUITETURA), anexa ao GHE escolhido via `dataclasses.replace` aninhado e roda `processar_pgr` de novo sobre o PGR mutado — sem chamar `preparar_pgr_hidratado`, sem tocar PDF/LLM. `CacheMatrizes` ganha o campo aditivo `pgr_hidratado` (molde `chamadas_ia`) pra sobreviver entre reruns do Streamlit em `st.session_state`. Sem PGR carregado, comportamento idêntico ao de antes (fluxo avulso da fatia 1/`D-ARQ-47`). Medido ao vivo (`test_pagina_matriz_fds_anexada_persiste_entre_reruns_sem_chamada_ia`, `AppTest`): FDS de tolueno (CAS 108-88-3) anexada atravessa até `Resultado.matrizes` com o componente resolvido/promovido (Fase C, `resolver_composicao`+`estagios/riscos.py`), `chamadas_ia == 0` no rerun, e um 2º `.run()` sem tocar em widget confirma que o produto NÃO desaparece (persistência em `st.session_state`, a reversão nomeada pela ARQUITETURA). Fronteira respeitada: só `web_matriz.py`/`test_web_matriz.py` tocados; `orquestracao_pgr.py` e o motor intocados — a fatia 2a bastou. Detalhe completo: `DECISOES_ARQUITETURAIS.md` v202 (nota de aplicação em `D-ARQ-49`).

**Status:** RESOLVIDA — D-ARQ-49 Parte 2 (fatias 2a+2b) fecha IMPLEMENTADA. `[MEDIDO — parsear_arquivo real contra o Fascino + leitura de estagios/pendencias_estruturais.py/PROTOCOLO_AGENTE_MEDICO.md §R-PGR-04, sessão claude/sharp-wozniak-j4596a; ratificação do Diovanni na mesma sessão; fatia 2a medida na sessão claude/blissful-johnson-mdeqn5; fatia 2b medida na sessão claude/003ff-fatia2b]`

---

### DT-(sessão branch `docs/003fi-achado-gate-forma-faixa`)-01 — `gate_forma` reprova a maioria dos blocos reais de FDS: separador de faixa raso demais para o padrão real de tabela `[RESOLVIDA — IMPLEMENTAÇÃO, sessão claude/nice-fermat-xahkji]`

**Origem.** Diovanni testou o app publicado (`automacao-pgr-agente-pcmso.streamlit.app`) com 14 FDS reais do acervo (as mesmas medidas nas duas levas de `DT-003M-02`, mais `IMPERMEABILIZANTE.pdf`) e reportou o resultado por screenshot — a maioria dos blocos saiu como `forma_verbatim_fds: Bloco verbatim reprovado no gate de forma`, com CAS e nome perfeitamente legíveis no motivo da pendência.

**Medido — causa raiz confirmada, não hipótese.** `extrair_texto_fds` (determinístico, sem LLM) sobre os mesmos PDFs mostra que a fonte já chega **sem separador** entre os dois números da faixa de concentração, antes de qualquer transcrição:
```
'Hipoclorito de sódio 15 19% 7681-52-9'      # Água Sanitária Zulu
'Acetona 67-64-1 30 70'                       # Adesivo PVC Tigre
'Asfalto 8052-42-4 35 a 50'                   # Impermeabilizante — usa "a", não hífen
```
O `pdfplumber` extrai as duas colunas (mínimo/máximo) como números soltos lado a lado — o hífen visual da tabela do PDF de origem não sobrevive à extração de texto por posição. `gate_forma` (`motor/transcritor_fds.py`) exige `parsear_faixa(faixa) is not None`; `parsear_faixa` usa `_SEPARADOR_FAIXA = re.compile(r"[-–]")` — só hífen/en-dash (`transcricao_fds.py:90`). Sem separador reconhecido → `None` → bloco inteiro reprovado, bloqueante, mesmo com CAS/nome íntegros.

**O LLM não é a causa, mas é inconsistente.** O prompt (`transcritor_gemini.py`, regra 1) já pede "dois números separados por hífen/en-dash" — e às vezes o Gemini insere o hífen que a fonte não tem (funcionou no Cimentcola Interno Quartzolit/Azulejista: "20,0 - 60,0" no candidato, apesar de a fonte trazer "20,0 60,0" sem hífen), às vezes só transcreve os dois números como estão (a maioria dos casos do teste do Diovanni). Comportamento **não-determinístico** do modelo sobre o mesmo tipo de entrada — não dá para contar com o LLM resolver isso de forma confiável.

**Impacto medido — não é caso isolado.** Apareceu em 3 fabricantes distintos (Tigre/adesivo, Zulu/água sanitária, fabricante do eletrodo de solda) — é o padrão comum de tabela de composição nas FDS brasileiras reais do acervo, não uma malformação pontual de 1 documento. Na prática, o gate está descartando a maior parte da composição real que sobe pelo app hoje — o vocabulário de 28 slugs novos populado em `DT-003M-02` (duas levas, `PR #351`/`#352`) vale pouco enquanto o dado nem atravessa o gate de forma antes de chegar em `gate_cas`.

**Achado colateral, natureza distinta — não desta DT.** 2 dos 14 arquivos (`IMPERMEABILIZANTE.pdf`, e uma das cópias de `FDS MONTADOR.pdf`/`FDS SERVIÇOS GERAIS.pdf`, hash-idênticas a arquivos que noutra invocação tiveram sucesso) voltaram `transcricao_indisponivel_fds: JSON inválido` — falha de invocação do LLM (JSON malformado na resposta), não de forma. É instabilidade pontual do modelo sobre o MESMO PDF byte-idêntico noutra chamada — sugere robustecer com retry, mas é problema de natureza diferente do separador de faixa; não misturar as duas correções numa só fatia.

**Proposta (não implementada nesta sessão — handoff por reinício de janela de contexto).** Estender `_SEPARADOR_FAIXA` para reconhecer também espaço puro entre dois números válidos e o literal `" a "` (case-insensitive), sem tocar no LLM/prompt — mantém a extração e o parse 100% determinísticos, só amplia o que conta como separador válido. Risco de falso-positivo (dois números soltos que não sejam min/max de uma faixa real) é mitigado por `_texto_para_float` já exigir token numérico limpo após a troca vírgula→ponto — ruído não-numérico (texto, datas) continua caindo em `None`, não muda esse comportamento. Mexe em `motor/transcricao_fds.py` — contrato de `parsear_faixa` citado em D-ARQ-34 Parte 1 (faixa é FaixaConcentracao, não escalar) e D-ARQ-43 Parte 2 (separadores hífen/en-dash, DT-003AS-01 patologia 5); esta DT amplia o conjunto de separadores aceitos, não revoga a decisão anterior. Precisa de teste com reversão nomeada (regra do CLAUDE.md): candidato natural é "faixa sem separador reconhecido continua reprovando" revertendo a mudança de regex — os 3 casos reais acima (`'15 19'`, `'30 70'`, `'35 a 50'`) são candidatos diretos de fixture, já medidos, prontos para virar caso de teste sem inventar dado novo.

**Resolução (sessão `claude/nice-fermat-xahkji`).** Implementada exatamente a proposta acima, sem desvio: `_SEPARADOR_FAIXA_FALLBACK = re.compile(r"\s+a\s+|\s+", re.IGNORECASE)` em `motor/transcricao_fds.py`, consultado em `parsear_faixa` só quando `_SEPARADOR_FAIXA` (hífen/en-dash) não encontra 2 partes — nunca compete com o separador primário, então as âncoras de D-ARQ-43 P2 (`"0,2 – 0,05"` etc.) continuam pelo caminho antigo, byte a byte. LLM/prompt intocados, como prescrito.

Os 3 casos reais viraram fixture direta, sem dado inventado: `parsear_faixa("15 19") == FaixaConcentracao(15.0, 19.0)`, `parsear_faixa("30 70") == FaixaConcentracao(30.0, 70.0)`, `parsear_faixa("35 a 50") == FaixaConcentracao(35.0, 50.0)` — mais 2 testes de fronteira (fallback não compete com hífen presente; fallback não resgata lixo sem espaço, ex. `"indisponível"`) e 1 teste no nível do gate (`test_faixas_reais_sem_hifen_sao_aprovadas`, `motor/transcritor_fds.py::gate_forma`), confirmando que os 3 blocos reais deixam de gerar `Pendencia` bloqueante.

**Varredura inversa `[MEDIDO — mesma sessão]`.** Reversão nomeada na própria proposta: revogar o fallback (remover a chamada a `_SEPARADOR_FAIXA_FALLBACK` em `parsear_faixa`, restaurando só `_SEPARADOR_FAIXA`). Aplicada isoladamente (só o código-fonte, testes intactos): derruba exatamente 4/6 testes novos — os 3 casos reais + o teste de gate — e preserva os outros 2 (que descrevem comportamento que não depende do fallback existir: hífen presente sempre vence, lixo sem espaço sempre falha). Nenhum teste pré-existente da suíte se move. Restaurada em seguida, suíte volta a verde.

**Risco de falso-positivo, como antecipado na proposta.** `_texto_para_float` já exige token numérico limpo pós-troca vírgula→ponto; ruído não-numérico (texto, datas com barra) continua caindo em `None` sem tratamento especial — nenhum ajuste extra precisou entrar para conter isso.

**Fora do escopo desta fatia, como já registrado.** O achado colateral (2/14 arquivos com `transcricao_indisponivel_fds`, falha de invocação do LLM/JSON malformado) não foi tocado — natureza distinta (robustez de invocação, não forma), conforme já isolado na nota original.

**Status:** RESOLVIDA. `[MEDIDO — recorte `test_transcricao_fds.py`+`test_transcritor_fds.py`+`test_montagem_verbatim.py`+`test_revisao_verbatim.py`+`test_orquestracao_fds.py`+`test_transcritor_gemini.py`+`test_cli_fds.py`+`test_web_fds.py`+`test_web_matriz.py`+`test_composicao_propaga_pendencias.py`+`test_integracao_composicao_fase_c.py`: 156 passed, 3 skipped; varredura inversa 4/6 discriminantes confirmados; `mypy --strict` alvo canônico limpo; suíte completa em `docs/HISTORICO_OPERACIONAL.md` (bloco desta sessão)]`

### DT-(sessão `claude/nice-fermat-xahkji`, achado pós-PR #354)-01 — `gate_forma` reprova faixa dupla-desigualdade (`">= X - < Y"`), classe irmã do separador ausente `[RESOLVIDA — IMPLEMENTAÇÃO, mesma sessão]`

**Origem.** Diovanni testou o app publicado de novo (antes do merge do PR #354, com FDS reais de outro PGR — "CMO Residencial Verdes Mares") e subiu os PDFs usados ao acervo (`fds_originais/`, commit `111ee0e`). Resultado colado por e-mail: a maioria das FDS já passou a mostrar o botão "Anexar ao GHE" — confirma o fix da DT anterior — mas `DESMOLD SIKA - (GHE 05 CARPINTARIA).pdf` reportou `forma_verbatim_fds: Bloco verbatim reprovado no gate de forma: faixa='>= 0.1 - < 1', membros=[dazomete (ISO)]`.

**Medido — causa raiz confirmada, PDF real na mão.** `extrair_texto_fds` sobre o PDF que o próprio Diovanni subiu confirma o texto exato: `"dazomete (ISO) 533-74-4 >= 0.1 - < 1"`. Não é separador ausente (há hífen: `"- <"`) — é uma **faixa dupla-desigualdade**: `">="` antes do piso e `"<"` antes do teto, notação diferente de `"X - Y"` simples. `parsear_faixa` checa `bruto.startswith(">")` (D-ARQ-34 P1, semi-aberta simples) ANTES de qualquer split — para `">= 0.1 - < 1"` isso captura o `">"` inicial e tenta `_texto_para_float("= 0.1 - < 1")`, que falha (não é float), perdendo o teto e devolvendo `None`. Os outros 2 blocos da mesma FDS (`"< 0.1"`, semi-aberta simples) passam normalmente — por isso o botão "Anexar" ainda aparece para este arquivo (block-a-block, não all-or-nothing), só o bloco do dazomete vira pendência bloqueante isolada.

**Família correta:** irmã da DT anterior (mesmo D-ARQ-34 P1/D-ARQ-43 P2, mesmo módulo `parsear_faixa`) — separador presente, mas a notação de desigualdade dupla não era reconhecida. Achado novo, não coberto pela proposta original (que só cobria separador ausente).

**Resolução (mesma sessão).** `_FAIXA_COMPOSTA = re.compile(r"^>=?\s*([\d.,]+)\s*[-–]\s*<=?\s*([\d.,]+)$")` em `motor/transcricao_fds.py`, checada em `parsear_faixa` ANTES dos ramos `startswith("<")`/`startswith(">")` — sem essa ordem, a faixa composta é capturada erroneamente pelo ramo de semi-aberta simples. `=?` aceita tanto o operador estrito quanto "ou-igual" (`>=`/`<=`), mesmo vocabulário de desigualdade que o resto do módulo já reconhece isoladamente (D-ARQ-34 P1) — não introduz conceito novo, só permite os dois lados aparecerem juntos. LLM/prompt intocados; `gate_forma` não mudou (reusa `parsear_faixa`).

5 testes novos: o caso real (`">= 0.1 - < 1"` → `(0.1, 1.0)`), operador estrito (`"> 0.1 - < 1"`), teto ou-igual (`">= 0.1 - <= 1"`), confirmação de que as semi-abertas simples (`"> 1"`, `"< 5"`) continuam intocadas, e 1 teste no gate com o bloco real (CAS 533-74-4, dazomete). **Varredura inversa `[MEDIDO — mesma sessão]`:** revogar só o branch `_FAIXA_COMPOSTA` (código-fonte, testes intactos) derruba exatamente 4/5 — os 3 casos de faixa composta + o teste de gate; o teste "não rouba semi-abertas simples" permanece verde (não depende do branch novo). Nenhum teste pré-existente se move. Restaurado em seguida, suíte volta a verde.

**Escopo, deliberadamente estreito (na 1ª leva desta DT).** Só `">"`/`">="` no piso e `"<"`/`"<="` no teto, **ambos os lados presentes** — o mesmo par que D-ARQ-34 P1 já trata isoladamente. Não adicionei `≥`/`≤` unicode: nenhuma FDS medida usa esses caracteres; se aparecerem, é achado novo, registra-se quando medido (regra do CLAUDE.md — número/padrão não medido não entra por antecipação).

**Nota (mesma sessão, achado do acervo Aurora pós-PR #355) — a exigência de "ambos os lados" era estreita demais, corrigida na mesma DT.** Diovanni subiu FDS reais de outro PGR ("CMO Residencial Aurora") ao acervo (`fds_originais/`, commit `683f5f7`). `extrair_texto_fds` sobre `Fundo Zarcão- PINTURA ESMALTE SINTÉTICO- PINTOR.pdf` mostra `"Destilados de Petróleo levemente tratados com hidrogênio 10 - <50 64742-47-8"` — faixa `"10 - <50"`: hífen presente, mas só o TETO tem operador (`"<50"`), o piso é número puro (`"10"`). O regex original (`^>=?...<=?...$`, ambos obrigatórios) não casava — `_texto_para_float("10 ")` funcionava mas o resto da string não batia o padrão inteiro, devolvendo `None` sem sequer tentar o split. Generalizado para `^(?:>=?)?\s*([\d.,]+)\s*[-–]\s*(?:<=?)?\s*([\d.,]+)$` — cada lado com operador **opcional independente** — e a checagem só entra quando `">" in bruto or "<" in bruto` (gate por substring, barato), preservando intocado o caminho antigo para o caso sem nenhum operador (mesmo princípio "não competir com o separador primário" já usado no fallback de espaço/`" a "`). 2 testes unitários novos (`"10 - <50"` → `(10.0, 50.0)`; `">10 - 50"` → `(10.0, 50.0)`, simétrico ao achado mas com piso — não medido em FDS real, mas mesma classe de forma, coberto pelo mesmo regex) + 1 no gate com o bloco real completo (CAS 64742-47-8). Varredura inversa: reverter só o regex para a forma simétrica antiga derruba exatamente os 3 testes novos desta nota, preserva os 5 da 1ª leva (dazomete) e todo o resto da suíte.

**Status:** RESOLVIDA (as duas levas). `[MEDIDO — recorte `test_transcricao_fds.py`+`test_transcritor_fds.py`+`test_montagem_verbatim.py`+`test_revisao_verbatim.py`+`test_orquestracao_fds.py`+`test_transcritor_gemini.py`+`test_cli_fds.py`+`test_web_fds.py`+`test_web_matriz.py`+`test_composicao_propaga_pendencias.py`+`test_integracao_composicao_fase_c.py`: 164 passed, 3 skipped; varredura inversa da 1ª leva 4/5 e da 2ª leva 3/3 discriminantes confirmados; `mypy --strict` alvo canônico limpo; suíte completa em `docs/HISTORICO_OPERACIONAL.md` (bloco desta sessão)]`

### DT-(sessão `claude/hopeful-newton-yjv3k7`)-01 — Porto Araras I atravessa a rota determinística com GHE perdido e cargos truncados, sem pendência `[RESOLVIDA — IMPLEMENTAÇÃO, mesma branch, 23/09/2026; gate de número saltado IMPLEMENTADO em seguida]`

**Origem.** Medição de `DT-003FG-01` (mesma sessão). `preparar_ghes` com clientes offline sobre
`matrizes_originais/PGR — PORTO ARARAS I SPE EMPREENDIMENTOS IMOBILIARIOS LTDA.pdf` (par 6 de
`PAREAMENTO_ACERVO.md`, confiança ALTA) devolve 15 GHEs, 51 cargos e **nenhuma pendência**.
Conferido contra o texto do PDF (`pdfplumber`, 102 páginas) e contra o gabarito pareado
(`MATRIZ DE EXAMES(ATUALIZAÇÃO)PORTO ARARAS 1 … 06.07.26`).

**Medido.**
- **(a) GHE perdido, sem sinal.** O PDF tem 16 cabeçalhos de GHE; `GHE - 14 PINTURA` (pág. 66,
  cargo `Pintor`) tem o número depois do hífen. `eh_cabecalho_ghe("GHE - 14 PINTURA")` → `False`;
  `"GHE 13 - INSTALAÇÕES HIDROSSANITÁRIAS"` e `"GHE 15 - PORTARIA"` → `True`. As duas rotas
  (`parsear_arquivo` e `recortar_blocos_ghe`) usam o mesmo reconhecedor, então as duas contam 15,
  `len(candidatos) == len(blocos)` passa e a rota determinística é aceita. O `Pintor` — no
  gabarito com acetona, tolueno, metiletilcetona e xileno — sai da matriz sem pendência. É a
  classe D-ARQ-22 / anti-supressão (D-ARQ-31/35): trabalhador sem matriz, documento com aparência
  de completo.
- **(b) Nomes de cargo truncados.** 26/51 cargos terminam em preposição (`Operador de`,
  `Meio Oficial de`, `Encarregado de` ×5, `Técnico de Segurança do`, …), outros saem cortados sem
  preposição (`Analista`, `Engenheiro`, `Vigia` ×2). O parser da família Consciente lê a
  continuação pela banda `x0` medida no Fascino (D-ARQ-65 cl.5); a geometria de Porto Araras
  difere. Mesma classe de `DH-003EW-02` (TOCTAO), com uma diferença: lá o sanity-check recusava a
  família, aqui não recusa.

**Não medido nesta sessão `[A MEDIR]`:** o que a matriz final de Porto Araras emite a jusante
(exige envelope do topo; `comparar_matriz_gabarito` não foi rodado); se `"GHE - NN"` aparece em
outros PGRs do acervo; a geometria da célula de cargo de Porto Araras.

**O que a resolução exige.** Duas decisões separadas, do Arquiteto: (1) reconhecedor para
`"GHE - NN TÍTULO"` em `_RECONHECEDORES_GHE` (extensão medida, molde DT-003CM-01), ou gate que
detecte número de GHE saltado (13 → 15) como pendência; (2) Porto Araras vira família medida
(molde D-ARQ-65) ou passa a ser recusado como o TOCTAO. O sinal substituto proposto em
`DT-003FG-01` teria bloqueado (b), **não** (a).

**Resolução `[MEDIDO — 23/09/2026, mesma branch, sobre main 365b571]`.** Detalhe em `D-ARQ-57`
(andamento desta sessão) e no HISTORICO.
- **(a) resolvida e ampliada.** A varredura dos 43 PDFs achou um 2º caso da mesma forma, maior:
  Vila Brasil Escritório tinha `GHE\x00 01 \x00 ADMINISTRAÇÃO 01` … `GHE\x00 22`, e o motor
  reconhecia só os GHEs 23–26 (**22 de 26 GHEs perdidos**, 4 GHEs e 5 cargos sem pendência).
  Forma 6 em `_RECONHECEDORES_GHE`; título por padrão espelho.
- **(b) resolvida — a causa não era geometria.** O nome inteiro já está na linha do rótulo;
  `_separar_nome_cbo` cortava a última palavra de todo cargo sem CBO (a "cauda" casava espaço
  puro). Trocado por `_PADRAO_CBO`, que também separa dois cargos unidos só pelo CBO (Vila
  Brasil, vírgula ausente).
- **Medido pós-fix.** Porto Araras 16 GHEs / 52 cargos; Vila Brasil 26 / 86 — contagens iguais
  às dos gabaritos pareados, nomes divergentes só por grafia humana (acento, `I`×`l`, anotação da
  médica). Fascino idêntico ao estado anterior (19 / 41, mesmos nomes).
- **Resíduo, do próprio documento:** `Analista jurídico júnior \x00CBO` (o PDF traz o literal
  `CBO`) e `Business Partner - RH \x002524` (código cortado na célula do PDF). Ficam visíveis.
- **Não medido `[A MEDIR]`:** a matriz de exames que Porto Araras e Vila Brasil emitem a jusante
  (exige envelope do topo; `comparar_matriz_gabarito` não rodado).
  **Medido depois (mesma branch, 23/09/2026):** 96,8% e 95,1% das células do gabarito reproduzidas;
  nenhuma lacuna silenciosa. Classificação em `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`.
- **Gate de número de GHE saltado — proposta, não implementado.** Pós-fix, só dispararia em R78
  e Floramazônia, já bloqueados por `segmentacao_implausivel`: zero bloqueio novo no acervo. É
  defesa para forma futura desconhecida (o reconhecedor falha e as duas rotas concordam no erro).
  Decisão do Arquiteto.

**Nota (mesma branch, pós-merge do PR #359, 23/09/2026) — gate implementado.** Diovanni mandou
seguir com o gate. `avaliar_numeracao_ghe` (pendência bloqueante `numeracao_ghe_lacunar`),
encadeado depois de `avaliar_segmentacao` em `avaliar_estrutura`; detalhe em `D-ARQ-57`
(andamento) e no HISTORICO. Reproduzindo o estado pré-PR #359 (forma 6 fora do repertório), o
gate acusa o GHE 14 de Porto Araras (teste real com `monkeypatch`). No acervo atual, 0 desfecho
muda.

### DH-(sessão `claude/hopeful-newton-yjv3k7`)-01 — `comparar_matriz_gabarito` produz divergência falsa em 3 casos medidos `[RESOLVIDA — mesma branch, pós-merge do PR #361]`

**Origem.** Comparação Porto Araras I e Vila Brasil Escritório × gabarito (mesma branch,
23/09/2026). 21 de 74 células divergentes são do instrumento, não do motor `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`:
- **Cargo repetido em dois GHEs.** `extrair_gabarito` e `extrair_motor` chaveiam por cargo; o
  último GHE sobrescreve o anterior. `estagiário` (ADMINISTRAÇÃO e SESMT, Porto Araras) gera 7
  subemissões falsas. Correção candidata: chave (GHE, cargo), ou comparar o conjunto de exames de
  todas as ocorrências.
- **Grafia de exame sem alias.** `rx de coluna lombo sacra` não casa `rx_coluna_lombo_sacra`
  (1 super + 1 sub). Correção candidata: entrada em `_ALIAS_GRAFIA`.
- **Momentos sem vírgula no gabarito.** `ECG (ADM PER, MRO)` (Vila Brasil) é lido como só `MRO`
  (12 divergências de momento). Correção candidata: aceitar espaço como separador de momento.

Não mexe em conduta; distorce a leitura da fila clínica.

**Nota (mesma branch, pós-merge do PR #362) — mais duas formas, mesma classe.** Anotação da médica
em linha própria sem parêntese nem hífen (`Pintor\nIncluir no WORD…`, Porto Araras — pintor,
encanador e meio oficial hidráulico ficavam sem par) e grafias de MEK do gabarito
(`Metil-etil-cetona`, `Metil Etil Cetona`, `Metil-etil-cetona na urina`). Corrigidas em
`_ANOTACAO_COLADA` e `_ALIAS_GRAFIA`; 2 testes com reversão nomeada.

**Resolução (mesma branch, pós-merge do PR #361, 23/09/2026).** As três correções candidatas
implementadas: `_chaves_por_ocorrencia` (cargo repetido ganha o ordinal da ocorrência nos dois
lados; contagens diferentes deixam o cargo sem par, visível), entrada `rx de coluna lombo sacra`
em `_ALIAS_GRAFIA`, e `_momentos_do_rotulo` em `scripts/medir_audiometria_dem.py` (espaço vale
como separador só se todo token for momento; compartilhado com o instrumento de DEM). Remedição:
Porto Araras **100%** de identidade de exame (383/383; restam as 24 de periodicidade do RX,
`DT-003EC-01`); Vila Brasil 95,2% (338/355), 0 divergência de momento, 17 subemissões — todas
reais e já classificadas. 4 testes novos + 1 do alias abaixo, varredura inversa 5/5.

### DT-(sessão `claude/hopeful-newton-yjv3k7`)-02 — Termo de risco "produto + agente" não resolve (`Adesivo CPVC Ciclohexanona`) `[RESOLVIDA — aliases por termo, mesma branch, pós-merge do PR #362]`

**Origem.** Vila Brasil Escritório, GHEs INSTALAÇÕES HIDROSSANITÁRIAS e ASSISTÊNCIA TÉCNICA
MANUTENÇÃO ENERGIZADA: o PGR declara o agente como `Adesivo CPVC Ciclohexanona` e `Adesivo CPVC
Metiletilcetona` — nome do produto colado ao do agente. `vocabulario_ausente` (visível). O
gabarito pede ciclohexanol na urina, fenol na urina e MEK na urina para encanador e instalador
(6 células) e o motor não emite. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`

**O que a resolução exige.** Decidir entre alias por termo inteiro (frágil: um por produto) ou
extração do agente dentro do termo (reconhecer slug conhecido como sufixo). É o mesmo eixo de
"produto × agente" do casamento FDS↔PGR (`DT-(sessão claude/nice-ptolemy-wxk1wo)-01`), pelo lado do
PGR. Antes de decidir, medir quantos termos do acervo têm essa forma.

**Medição (mesma branch, pós-merge do PR #362, 23/09/2026).** Nos 3 PGRs que atravessam a rota
determinística (Fascino, Porto Araras I, Vila Brasil Escritório), 93 termos distintos não
resolvidos; 17 contêm uma forma conhecida do vocabulário como trecho de palavra inteira. Extração
genérica do agente de dentro do termo acertaria 14 e **erraria 3 com confiança**: `Polímero de
fenol` e `4,4-(1-metiletilideno)bis(fenol)` (bisfenol A) virariam `fenol` → fenol urinário emitido
errado; `Vibração localizada (mão e braço)` viraria `vibracao` genérico. Classe D-ARQ-22. Além
disso, `Metiletilcetona` (sem "(MEK)") não resolvia nem sozinho — `fuzzy_recusado` nos 3 PGRs.

**Decisão (Diovanni): aliases por termo.** 12 formas em `termos:` de `agentes.yaml`: `Argamassa
Cimento Portland` e 7 `Cimento <componente>` (Vila Brasil), `Adesivo CPVC Ciclohexanona`, `Adesivo
CPVC Metiletilcetona`, `Metiletilcetona`, `Massa acriílica - Hidróxido de amônia 24°Be` (Fascino).
Fora, de propósito: `Cimento Sulfato de cálcio` (não há slug `sulfato_de_calcio`), `Polímero de
fenol` e o bisfenol (não são fenol livre). Seguem como `vocabulario_ausente` visível. Guard de
inventário 154 → 166; o vigia de pares fuzzy (DT-003DM-01) pegou o par novo
`cimento_silicato_dicalcico`/`…_tricalcico`, revisado e aceito (mesmos slugs do par já aceito).

**Efeito medido.** Vila Brasil: ciclohexanol urinário volta para encanador e instalador; MEK
urinário também (o gabarito escreve `Metil-etil-cetona` — alias de grafia no instrumento).
Identidade de exame 96,3% (342/355); restam 13 subemissões, 10 da classe (4) de `DT-003EB-01`, 2
de fenol urinário (bisfenol/polímero, fora de propósito) e 1 de `Produtos DomissanItários`. Porto
Araras: pintor passa a ter MEK urinário, como o gabarito pede. Fascino: +1 linha (`mek_urina` no
GHE PINTURA), onde o gabarito não pede — caso de `DT-003EB-02`. `[MEDIDO — `docs/referencia/MEDICAO_PORTO_ARARAS_VILA_BRASIL_vs_GABARITO.md`]`


### DT-(sessão `claude/inspiring-turing-0ylkmk`)-01 — Tela da matriz re-transcreve todas as FDS a cada rerun: 429 na cascata inteira e o "Anexar ao GHE" se perde `[RESOLVIDA — IMPLEMENTAÇÃO, mesma sessão, 24/09/2026]`

**Origem.** Teste do Diovanni em produção (PGR CMO Aurora + ~17 FDS, 23-24/09/2026): FDS com
`transcricao_indisponivel_fds` — HTTP 429 nos três modelos da cascata — e o anexo de `Fundo
Zarcão` ao GHE-18 não acontecia. Painel do AI Studio (nível gratuito, capturas do Diovanni): ~600
requisições no dia, ~400 delas 429; pico RPM 23/15 no Flash Lite, RPD 23/20 nos dois Flash.

**Causa.** `pagina_matriz` chamava `preparar_composicao(..., TranscritorGemini())` para cada FDS
enviada em **todo** rerun do Streamlit (qualquer widget: selectbox de GHE, nome do produto,
clique em "Anexar", submit do formulário). N FDS × até 3 modelos por interação; os próprios 429
contam na janela por minuto, então a cota não se recuperava enquanto a tela era usada. No rerun
do clique, a composição voltava vazia (429), o bloco `if ... and blocos_fds:` não renderizava o
botão e o clique era descartado. Reproduzido com `AppTest` (3 FDS: upload 3 chamadas, clique +3;
com 429 no 2º rerun, produto não anexado e botão ausente). Os testes existentes não pegavam:
mockavam `preparar_composicao` com retorno fixo, sem contar chamadas por rerun.

**Fix.** `preparar_composicao_cacheada` (núcleo puro de `superficie/web_matriz.py`): memoiza por
SHA-256 do conteúdo da FDS num dict em `st.session_state["web_matriz_cache_fds"]`.
`transcricao_indisponivel_fds` (falha transitória de invocação) **não** é memoizada — o rerun
seguinte tenta de novo; composição extraída e `composicao_ausente_fds` são determinísticas sobre
o conteúdo e são. 3 testes, varredura inversa 3/3 discriminantes (reversões: remover o lookup;
memoizar incondicionalmente; dict novo por rerun / casca chamando `preparar_composicao` direto).

**Fora do escopo, a decidir.** (a) Upload de muitas FDS de uma vez ainda dispara N chamadas em
sequência e pode bater no RPM do nível gratuito — espaçamento/backoff em 429 muda a decisão
"sem retry por modelo" de D-ARQ-47/48. (b) O motivo do 429 não carrega o `quotaId` do corpo da
resposta (por minuto × por dia), então a tela não diz ao RT se basta esperar. (c) O nível
gratuito (20 RPD por modelo Flash, painel do AI Studio em 24/09/2026) não comporta um dia normal
de PGR + FDS — decisão de faturamento é do Diovanni.


### DT-(sessão `claude/determined-fermi-xxah3h`)-01 — Produtos de FDS anexados não aparecem na tela da matriz `[RESOLVIDA — IMPLEMENTAÇÃO, fatias A, B e C, 25/09/2026]`

**Origem.** Diovanni, depois de rodar o Aurora Lago das Rosas com 16 FDS: "não consegui enxergar
elas". Medido na tela exportada: a confirmação "Produto X anexado ao GHE Y" só aparece no rerun do
próprio clique e some na interação seguinte; nenhuma lista de anexos por GHE; as pendências de
Fase C citam CAS das FDS sem dizer de qual produto/GHE. A FDS de aguarrás (benzeno <0,1%) aparece
com o seletor em GHE-16 (Serralheria), mas a aguarrás está no GHE 18 (Pintura) do PGR — o motor
emite ácido t,t-mucônico ao serralheiro (o gabarito não pede) e não ao pintor (o gabarito pede).
Com o anexo visível, o operador teria visto.

**Fatia A (implementada, mesma branch).** Status por FDS lido depois do clique ("anexada a
GHE-xx" / "ainda não anexada"); recusa de anexo duplicado (mesmo nome no mesmo GHE); painel
"Produtos anexados" com cada componente como `resolver_composicao` o resolve (CAS → slug ou "não
reconhecido no vocabulário") e botão Remover (`remover_produto_e_reprocessar`, sem PDF/LLM).

**Resta.** (B) origem do exame na revisão ("via FDS X, componente Y") — o `Motivo` de
`stage_5_emissao` não carrega o produto hoje (`risco_origem=None`), então é mudança de motor, não
só de tela; (C) anexos que sobrevivem a reprocessamento (a chave do cache inclui o envelope —
trocar validade/assinatura refaz o PGR hidratado sem os produtos, sem aviso; leitura de código,
`[A MEDIR]`) e FDS em mais de um GHE — muda o contrato de `CacheMatrizes` (D-ARQ-49 Parte 2
fatia 2b), exige nota de decisão antes.

**Fatia B (implementada, mesma branch, pós-merge do PR #372).** Seção "Revisão — origem dos
exames" na tela, fora do documento assinado: por GHE, exame × regra × status × origem. Origem vem
de `Motivo.risco_origem`, que o motor passa a preencher nas regras de agente direto (R-BIO-04-*),
com todas as fontes do agente (PGR com nível, FDS com produto, cargo) — decisão do Diovanni entre
três caminhos; regra composta mostra o predicado. Mesma seção lista o enquadramento de cada agente
no Decreto 3.048/1999, Anexo IV (`enquadramento_3048`, D-ARQ-12), com "sem enquadramento
conferido" distinto de "não consta (conferido)". Resta a fatia C.

**Fatia C (implementada, mesma branch, pós-merge do PR #373) — DT resolvida.** Produtos anexados
são reaplicados quando o mesmo PDF é reprocessado (troca de validade/assinatura); PDF diferente não
herda anexos; anexo de GHE que sumiu no reparse é avisado uma vez. FDS pode ir para vários GHEs
(multiselect sem default — o clique não anexa sem escolha). Nota em D-ARQ-49 (DECISOES v217). O
`[A MEDIR]` da perda de anexos ficou medido por teste: sem a reaplicação, trocar só a validade
refaz o PGR hidratado sem o produto (`test_anexo_sobrevive_ao_reprocessamento_do_mesmo_pdf`).


### DT-(sessão `claude/determined-fermi-xxah3h`)-02 — FDS fora do formato NBR 14725: composição não localizada (Eletrodo E-6013 Gerdau) `[DECIDIDA — caminho (a), Diovanni, 25/09/2026; aguarda a FDS do fornecedor]`

**Origem.** Tela do app em produção (Aurora, 25/09/2026): `FISPQ Eletrodos E 6013 ( Gerdau) - (GHE
14 - SERRALHERIA).pdf` → `composicao_ausente_fds`. Arquivo no acervo (`fds_originais/`).

**Causa medida.** O documento é uma "Ficha de Segurança de Produto" da Gerdau, não uma FDS no
formato NBR 14725: não tem a seção "3. Composição e informações sobre os ingredientes". A tabela
de substâncias está em "2. SUBSTÂNCIAS PERIGOSAS" (CAS, OSHA PEL, % em peso, peso específico) e
a seção seguinte é "3. PROPRIEDADES FÍSICO–QUÍMICAS". `_ANCORA_COMPOSICAO` ("COMPOSICAO E
INFORMACOES SOBRE", derivada de n=6 FDS NBR 14725) não casa em nenhuma linha → `None` →
pendência bloqueante. É o comportamento desenhado (D-ARQ-47: sem região, nunca o documento
inteiro como fallback), não defeito.

**O que a ficha traz.** Manganês 7439-96-5, dióxido de titânio 13463-67-7, ferro 7439-89-6,
carbonato de cálcio 1317-65-3, zircônio 12166-47-1 — materiais formados na decomposição durante a
soldagem. O manganês já está no PGR (GHE 16), então esta ficha não destrava a lacuna de
`DT-003EO-03`.

**Caminhos.** (a) Pedir ao fornecedor a FDS no formato NBR 14725 — nenhuma mudança no app;
(b) âncora adicional "SUBSTANCIAS PERIGOSAS" restrita a título de seção numerado — n=1, documento
fora da norma, e a tabela mistura % em peso com OSHA PEL (risco de o transcritor pegar a coluna
errada). Recomendação: (a). Decisão do Diovanni.

**Decisão (Diovanni, 25/09/2026).** Caminho (a): pedir ao fornecedor a FDS do eletrodo no formato
NBR 14725. Nenhuma mudança no app; a âncora de composição fica como está (D-ARQ-47). A DT fecha
quando a FDS nova passar pela tela com a composição extraída — até lá, a pendência
`composicao_ausente_fds` desse arquivo é esperada.

### DT-(sessão `claude/hopeful-ramanujan-rbgh4s`)-01 — Asbesto sem LEO no resolver: medição de asbesto não decide a faixa de R-RX-01 `[ABERTA — sem caso real]`

**Origem.** Fatia 2 de `D-ARQ-86` (25/09/2026). O texto ratificado previa sílica, PNOS e asbesto;
o Diovanni decidiu implementar só sílica e PNOS.

**Causa medida.** `leo_resolver._PRECEDENCIA` só tem sílica e PNOS; `_helper_silica_asbesto`
(`predicados.py`) só calcula `pct_LT` com `pct_quartzo`, que o asbesto não tem. Medição de asbesto
com valor cai no ramo (d) → `Ausente`. O LEO é o LT do Anexo 12 da NR-15, item 12: **2,0 f/cm³**
para fibras respiráveis de crisotila (conferido no PDF `normas/nr-15-anexo-12 (3).pdf`).

**Por que não agora.** Asbesto aparece em 0 dos 29 PGRs do acervo como agente de GHE (só em texto
padrão sobre asbestose). Incluir exigiria registro no resolver, mudança na condição do helper de
R-RX-01 e unidade f/cm³ na tela, sem nenhum caso para conferir.

**Reabre quando** um PGR real trouxer asbesto como agente de exposição.

### DT-(sessão `claude/jolly-wozniak-iz0ley`)-01 — CO da manta asfáltica sem inventário no PGR: o motor não avisa o elaborador `[ABERTA — não-bloqueante]`

**Origem.** Decisão do asfalto (PROTOCOLO v107). Os PGRs CMO (Aurora 27/08/26 GHE 22, Vistamerica
28/07/26) descrevem caldeira a 180 °C e maçarico, mas não inventariam o monóxido de carbono; os PGRs
Viverde V02 e Vistamerica Ver.02 inventariam ("queima de produtos derivados de petróleo", MODERADO).

**Situação.** `R-PKG-ASF-CO` emite a carboxihemoglobina por `cimento_asfaltico`, mas o NR-07 7.5.18
pede exame relacionado a risco **classificado no PGR**. A conduta recomendada é emitir o exame e
pedir ao elaborador a inclusão do CO (R-PGR-04, informação crítica ausente). `regras.yaml` não tem
mecanismo de regra que gere pendência — precisa de código no motor, fatia própria.

**Status:** ABERTA — não-bloqueante.

### DT-(sessão `claude/jolly-wozniak-iz0ley`)-02 — NR-07 Anexo V: o documento não registra exposição a cancerígeno nem a guarda de 40 anos do prontuário `[ABERTA — não-bloqueante]`

**Origem.** Leitura da NR-07 Anexo V (texto oficial em `normas/nr-07-atualizada-2022-1 .pdf`) na
decisão do asfalto. Item 3.1: o médico responsável registra no PCMSO as atividades e funções com
exposição a substância cancerígena identificada no PGR; item 4.1: prontuário por no mínimo 40 anos
após o desligamento.

**Situação.** O documento da matriz não marca GHE com cancerígeno nem traz a observação dos 40 anos.
Candidato: observação por GHE derivada dos agentes cancerígenos (a lista de `cancerigeno_com_ibe` mais
asfalto/sílica/poeira de madeira etc.), com a fonte do 003.DP. Qual lista a NR-07 usa para
"cancerígena" não está definida no glossário `[A CONFERIR — LINACH, Portaria Interministerial 9/2014]`.

**Status:** ABERTA — não-bloqueante.


### DT-(sessão `claude/cool-babbage-whh1zw`)-01 — Gatilho de solda por marcador de agente, não pela fonte geradora declarada `[ABERTA — não-bloqueante]`

**Origem.** `R-PKG-SOLD-CO` (26/09/2026). O gatilho escolhido pelo Diovanni foi "soldagem declarada
como fonte geradora no GHE" (via exposição real, R-GHE-05); a medição antes de implementar mostrou
que o motor não lê esse campo.

**Causa medida.** As três rotas de extração preenchem `RiscoVerbatim.fonte_geradora`
(`parser_familia_consciente.py`, `transcritor_gemini_pgr.py`, `transcritor_gemini_card.py`), mas a
hidratação o descarta: `RiscoPGR` (`tipos.py`) não tem o campo e os três construtores em
`hidratacao.py` não o passam. Nenhum predicado alcança "soldagem"/"eletrodo". Por isso
`R-VIS-01-solda` e `R-PKG-SOLD-CO` disparam por `solda_indicador` (manganês ou fumos metálicos),
marcador `[INTERPRETADO]`: um GHE com manganês sem solda recebe acuidade com DEM e COHb.

**Caminho (a1).** `fonte_geradora: str = ""` em `RiscoPGR`, passado nos três construtores da
hidratação; primitivo `soldagem_declarada` (fonte geradora dos riscos do GHE casa `sold|eletrodo`);
`solda_indicador` passa a usá-lo nas duas regras de solda de uma vez. Muda `tipos.py` → nota em
`DECISOES_ARQUITETURAIS.md`. Risco a medir antes: falso positivo quando outro GHE cita "máquina de
solda" só como equipamento. Medido nesta sessão, rota determinística: dos PGRs do acervo, 3 parseiam
pela família Consciente e só o GHE Serralheria do Fascino tem `sold|eletrodo` na fonte geradora (12
riscos); na rota por IA (Aurora e demais CMO) `[A MEDIR]`, sem chave no container.

**Status:** ABERTA — não-bloqueante (a saída do Aurora GHE 16 é a mesma pelos dois gatilhos).
