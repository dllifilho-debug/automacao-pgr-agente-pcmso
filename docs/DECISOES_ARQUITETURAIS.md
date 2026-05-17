# DECISÕES ARQUITETURAIS — AGENTE MÉDICO PCMSO

Decisões de design do sistema, derivadas da formalização do protocolo da Dra. Carolini Polesso. Cada decisão tem ID estável (`D-ARQ-NN`). O ID **não muda** entre versões.

Formato de cada decisão: **Contexto** (o que motivou) → **Decisão** (o que foi resolvido) → **Consequência** (o que isso impõe à implementação).

---

## D-ARQ-01 — Matriz tem duas dimensões independentes

**Contexto.** A matriz PCMSO não é uma lista plana "cargo → exames". Ela tem duas dimensões que se cruzam: *o que pedir* e *quando pedir*.

**Decisão.** Modelar explicitamente:

- **Dimensão 1 — Quais exames.** Função de `(risco × cargo × atividade crítica × pacotes)`. Determinada pela combinação de inventário do PGR, FDS, cargo declarado e predicados de atividade.
- **Dimensão 2 — Quando executar.** Função de `(tipo de exame × Anexo NR-07 × regime regulatório)`. Determina presença em adm / per / MR / RT / dem e periodicidade (6M / 12M / 24M / 60M).

**Consequência.** Estrutura de dados central do agente é uma **matriz bidimensional**, não uma lista. Cada célula é `(exame, momento)`. Periodicidade é atributo do exame, não do par. A regra "Anexo I → só periódico" é uma regra na dimensão temporal, não uma exclusão de exame.

---

## D-ARQ-02 — Sinais indiretos e risco implícito são regras de primeira classe

**Contexto.** A Dra. Carolini não lê o PGR literalmente. Ela infere riscos a partir de:
- **EPIs declarados** (máscara → risco respiratório)
- **Cargo declarado** (soldador → fumos metálicos)
- **Cargo + insumo** (armador + policorte → poeira + CO)

Se o agente lê o PGR só pelo inventário, ele perde sistematicamente esses casos.

**Decisão.** Modelar três fontes de risco com **status equivalente**:

1. **Risco explícito** — declarado no inventário do PGR
2. **Risco implícito por cargo** — derivado da taxonomia de cargos (R-GHE-02, R-PKG-SOLD, R-PKG-ARMADOR)
3. **Risco inferido por sinal indireto** — derivado de EPIs e equipamentos (R-PGR-03)

**Consequência.** O sistema precisa de:
- **Tabela de risco implícito por cargo** — alimentada pelos pacotes do protocolo
- **Tabela de inferência por EPI** — máscara → risco respiratório, etc.
- Mecanismo de **merge** dos três conjuntos antes de aplicar as regras de exame

Sem isso, o agente fica preso a uma leitura literal e produz matrizes piores que a da Dra. Carolini.

---

## D-ARQ-03 — "Atividade crítica" é um predicado pivô

**Contexto.** Várias regras se acionam simultaneamente quando o trabalhador está em "atividade crítica":
- ECG (R-ECG-01)
- Acuidade visual (R-VIS-01)
- Avaliação psicossocial condicional (R-PSY-01)
- Pacote rastreio comorbidade (R-PKG-ATIVCRIT — hemograma, glicemia)

Esse predicado tem composição definida: trabalho em altura, espaço confinado, operação de máquina pesada, eletricidade, manipulação de combustíveis.

**Decisão.** Modelar `atividade_critica` como **predicado de primeira classe** do GHE, computado a partir do inventário + cargo. Múltiplas regras consomem esse predicado. Não duplicar a definição em cada regra.

**Consequência.**
- Mudanças na definição de "atividade crítica" se propagam automaticamente para todas as regras dependentes.
- Facilita auditoria: rastrear todas as regras que dependem desse predicado é trivial.
- Permite que o agente justifique inclusões: *"hemograma incluído porque GHE está classificado como atividade crítica (motivo: trabalho em altura)"*.

---

## D-ARQ-04 — Regime regulatório especializado como exceção controlada

**Contexto.** A Dra. Carolini levantou que aviadores não seguem a NR-07 como regime principal — a ANAC sobrescreve. Na validação v2, ela confirmou que **ANAC é o único regime setorial** que ela aplica; ferroviário, marítimo, eletricistas de alta tensão, profissionais de saúde e mineração seguem NR-07 padrão.

**Decisão.** Modelar o conceito de **regime regulatório aplicável** ao GHE como predicado opcional, com hierarquia:

1. Regime setorial específico (hoje: apenas ANAC para tripulação aeronáutica)
2. NR-07 + correlatas (regime padrão — aplicado a 100% dos casos não-aeronáuticos)
3. Protocolos internos da Dra. Carolini (ex: R-VIB-01 — RX coluna lombo-sacra)

Regimes setoriais **adicionam** exames e **sobrescrevem** periodicidades, mas não removem exames da NR-07 (a menos que explicitamente declarado).

**Justificativa para manter a camada mesmo com apenas um caso:** mais barato modelar como dado agora que como código hardcoded depois. Se surgirem novos regimes (revisão regulatória, novos setores atendidos pelo Seconci), adicionam-se como dados sem mudança de arquitetura.

**Consequência.**
- Não tratar ANAC como `if cargo == "aviador"` espalhado pelo código — é uma camada estrutural com **um único registro** hoje.
- O resultado da matriz precisa **registrar qual regime foi aplicado** para cada exame — fundamental para auditoria.
- Adição de novo regime no futuro = inserir registro na tabela de regimes, não alterar código.

---

## D-ARQ-05 — Lembretes operacionais são saída de primeira classe

**Contexto.** A matriz da Dra. Carolini contém itens como *"verificar metais liberados pelo eletrodo"* (R-OP-01). Isso **não é um exame**. É uma instrução para o executor: *"antes de fechar o PCMSO, faça X"*.

**Decisão.** A saída do agente médico é composta de **dois artefatos**, não um:

1. **Matriz de exames** — exames + momentos + periodicidades + bases normativas
2. **Lista de pendências operacionais** — TODOs que o agente identificou mas que dependem de input externo (FDS de eletrodo, esclarecimento com elaborador do PGR, etc.)

**Consequência.**
- O agente nunca "inventa" um exame quando faltam dados. Ele **registra a pendência** e segue.
- A matriz emitida vem com `status = "preliminar"` enquanto houver pendências abertas.
- A pendência é estruturada: tem destinatário (empresa / médico executor / elaborador do PGR), tipo (solicitar FDS, esclarecer composição, etc.) e prazo.

---

## D-ARQ-06 — Universalidade tem prioridade sobre cobertura completa do Viverde

**Contexto.** O caso de teste é o Viverde (construção civil), mas o objetivo declarado do projeto é funcionar para qualquer setor — construção, mineração, indústria química, saúde, alimentos.

**Decisão.** Sempre que uma regra puder ser expressa em termos **universais** (predicados sobre risco / cargo / atividade / agente químico), expressá-la assim — **mesmo que isso aumente o custo de implementação inicial**. Soluções que funcionam só para construção civil são rejeitadas.

Casos concretos onde isso já está aplicado:
- R-PKG-ATIVCRIT — definido por predicado de atividade, não por cargo de construção
- R-FDS-03 — cutoff de 5% e exceção de cancerígeno funciona para qualquer setor químico
- R-BIO-02 — matriz temporal por Anexo NR-07, não por cargo

**Consequência.**
- Em qualquer decisão futura, perguntar: *"isso funciona pra construção civil, indústria química e saúde ao mesmo tempo?"*. Se não, não é universal.
- Validação do protocolo precisa, em algum momento, ser feita com um **PGR de setor não-construção** (mineração ou farmacêutico) antes de declarar o agente como genérico.

---

## D-ARQ-07 — Protocolo é dado, não código

**Contexto.** As ~50 regras do `PROTOCOLO_AGENTE_MEDICO.md` evoluem com o tempo: a Dra. Carolini muda de opinião, normas são revisadas, novos setores são incorporados.

**Decisão.** As regras do protocolo são **dados estruturados** consumidos pelo agente, não código. Forma sugerida: YAML ou JSON com schema declarado. O motor de inferência é código; as regras não.

Cada regra carrega:
- ID
- Predicado de ativação (em forma estruturada)
- Consequência (exames + periodicidade + momentos)
- Base normativa
- Status (`VALIDADO` / `INFERIDO` / `A VALIDAR`)

**Consequência.**
- Atualizar o protocolo não exige novo deploy do agente — basta atualizar o arquivo de regras.
- A Dra. Carolini pode (futuramente) revisar o protocolo diretamente, sem desenvolvedor intermediário.
- Audit log do agente referencia regras por ID — qualquer mudança é rastreável.

---

## D-ARQ-08 — Pendência tem nível: bloqueante vs operacional

**Contexto.** D-ARQ-05 estabelece pendência operacional como saída de primeira classe (TODOs após matriz pronta). Mas há um segundo tipo de pendência, conceitualmente distinto: dado essencial faltando que impede o motor de fechar a matriz para um GHE (ex: composição química de produto ausente, vibração mencionada sem qualificar tipo).

**Decisão.** Modelar `Pendencia.bloqueante: bool` como atributo de primeira classe.
- **Bloqueante (`True`)** — interrompe o pipeline naquele GHE no estágio em que surge. A `MatrizGHE` retornada vem com `linhas: []` e a lista de pendências bloqueantes. Status global do `Resultado` vira `PRELIMINAR`.
- **Operacional (`False`)** — matriz fecha normalmente, pendência acompanha como TODO para o executor (ex: R-OP-01).

**Consequência.**
- O motor nunca produz matriz "incompleta sem aviso" — bloqueio é explícito.
- A camada de orquestração superior (humano + LLM de extração) pode reagir a bloqueantes solicitando dados faltantes e rerodando o motor.
- Pendências bloqueantes têm prioridade visual no relatório de saída.

---

## D-ARQ-09 — Motor é determinístico; LLM fica fora do caminho crítico

**Contexto.** O sistema completo envolve etapas com LLM (extração de PGR, leitura de FDS, normalização de vocabulário). A tentação é deixar o motor de inferência também consultar LLM em casos ambíguos.

**Decisão.** O motor de inferência é função pura `(PGR_estruturado, Protocolo) → Resultado`. Determinístico, idempotente, sem chamadas a LLM. LLM atua exclusivamente nas camadas a montante (parsing de PGR/FDS) e a jusante (geração de relatório em prosa).

**Consequência.**
- Auditabilidade total: mesmo input → mesmo output, sempre.
- Testes unitários e de integração são triviais (sem mocks de API).
- Toda ambiguidade que o motor encontra vira pendência bloqueante (D-ARQ-08), nunca "chute" via LLM.
- A cascata multi-IA gratuita (Gemini → Groq → OpenRouter) é assunto da camada de extração, não do motor.

---

## D-ARQ-10 — Predicados: primitivos em código, compostos em YAML

**Contexto.** D-ARQ-07 estabelece "regras como dados". A pergunta operacional: predicados (`atividade_critica`, `ruido_acima_acao`) também são dados, ou são código?

**Decisão.** Separar em duas camadas:
- **Primitivos** — funções Python registradas por nome (`@primitivo("ruido_acima_acao")`). Acessam diretamente o `GHEContext` e a estrutura do PGR. Conjunto pequeno (~30) e estável (muda só se o schema do PGR mudar).
- **Compostos** — expressões declarativas em `predicados_compostos.yaml` usando `e/ou/nao` sobre primitivos e outros compostos. Conjunto maior, sujeito a evolução pela especialista clínica.

Exemplo: `atividade_critica` é composto (`ou: [altura, espaco_confinado, maquina_pesada]`), mas `altura` é primitivo (lê `ctx.riscos`).

**Consequência.**
- A Dra. Carolini pode revisar a composição de `atividade_critica` (D-ARQ-03) sem desenvolvedor.
- Mudanças no schema do PGR exigem dev (primitivos), mas mudanças clínicas não.
- Avaliador de compostos é único e simples (~50 linhas).

---

## D-ARQ-11 — Reaproveitamento de exames é responsabilidade do agendador, não do motor

**Contexto.** R-REAPR-01 (biomonitoramento válido por 6M) e R-REAPR-02 (audiometria > 120 dias refaz no demissional) operam sobre o histórico de exames do trabalhador, não sobre o PGR.

**Decisão.** O motor de inferência produz a matriz "ideal" — o que pedir se o trabalhador fosse exame zero. Reaproveitamento é responsabilidade de uma camada superior (chamada de **agendador**) que confronta a matriz ideal com o prontuário e marca o que pode ser reaproveitado.

**Consequência.**
- Motor não toca em datas, prontuários ou histórico individual.
- R-REAPR-01 e R-REAPR-02 não viram regras do protocolo do motor — viram regras do agendador (especificação separada, ainda não desenhada).
- Separação limpa: motor trabalha com função/risco; agendador trabalha com pessoa/histórico.

---

## D-ARQ-12 — Vocabulário é dado tipado de primeira classe

**Contexto.** As regras do protocolo referenciam agentes (`silica`, `manganes`, `benzeno`), cargos (`soldador`, `porteiro`, `armador`), exames (`audiometria`, `espirometria`, `hemograma`) e EPIs (`mascara_pff2`, `protetor_auricular`). Sem definição centralizada desses identificadores e seus metadados, as regras viram strings opacas e o motor não consegue, por exemplo, decidir se um agente é Anexo I ou Anexo II.

**Decisão.** Vocabulário mora em `protocolo/vocabulario/` em 4 YAMLs:

- `agentes.yaml` — cada agente com `anexo_nr07`, `cas`, `is_carcinogeno_iarc`, `tem_lt`, `protocolos_especiais`.
- `cargos.yaml` — cada cargo com `riscos_implicitos` (alimenta R-GHE-02), `pacotes_aplicaveis`.
- `exames.yaml` — cada exame com `momentos_default`, `categoria` (clínico, biomonitoramento, imagem, funcional).
- `epis.yaml` — cada EPI com `riscos_inferidos` (alimenta R-PGR-03 e similares).

Stage 2 do motor hidrata cada `Risco` com metadados do agente (Anexo NR-07 entra direto no objeto `Risco`).

**Consequência.**
- Adicionar agente novo (ex: cromo hexavalente) = inserir entrada no YAML, sem código.
- Stage 5 (emissão) pode escrever regras genéricas tipo "se risco com `anexo_nr07 == 'II'` → ...", em vez de listar cada agente.
- Vocabulário vira o contrato entre o parser de PGR (a camada que LLM normaliza para esses identificadores) e o motor.

---

## D-ARQ-13 — Predicados são tri-estado: True / False / Ausente

**Contexto.** Operacionalização de B-5 (dado ausente = pendência bloqueante). O caso âncora: PGR menciona "vibração" sem qualificar se é corpo inteiro ou mãos-braços. Predicado `vibracao_corpo_inteiro` não consegue retornar `True` (não há confirmação) nem `False` (há evidência parcial). Forçar `False` faz o motor subestimar risco silenciosamente.

**Decisão.** Primitivos retornam `bool | Ausente`. `Ausente` é sentinela com mensagem descritiva. Avaliador de compostos propaga:

- `e: [A, B, Ausente]` → `Ausente`
- `ou: [A, True, Ausente]` → `True`
- `ou: [False, False, Ausente]` → `Ausente`
- `nao: Ausente` → `Ausente`

Predicado que avalia para `Ausente` no estágio 4 gera **pendência bloqueante automática** com a mensagem do sentinela. A regra que dependia desse predicado não dispara. A matriz daquele GHE não fecha.

Regras podem declarar `quando_ausente: false` (default: `bloquear`) para cair como `False` em vez de bloquear — usado quando o protocolo aceita a ausência como evidência negativa.

**Consequência.**
- Não há subestimação silenciosa por dado parcial.
- A pendência aponta diretamente para o predicado e o GHE, com mensagem descritiva (auditável).
- O autor da regra escolhe explicitamente o comportamento quando o dado falta — decisão visível no YAML.

---

## Histórico de revisões

| Versão | Data | Alterações |
|--------|------|------------|
| v1 | 17/05/2026 | Versão inicial — D-ARQ-01 a D-ARQ-07 derivadas da entrevista da Dra. Carolini |
| v2 | 17/05/2026 | D-ARQ-04 atualizada: confirmação de que ANAC é o único regime regulatório sobreposto identificado pela Dra. Carolini; camada arquitetural mantida por argumento de custo evolutivo |
| v3 | 17/05/2026 | Sessão 002 (ARQUITETURA do motor): D-ARQ-08 a D-ARQ-13 adicionadas — níveis de pendência, motor determinístico, predicados primitivos vs compostos, agendador fora do motor, vocabulário tipado, predicados tri-estado |
