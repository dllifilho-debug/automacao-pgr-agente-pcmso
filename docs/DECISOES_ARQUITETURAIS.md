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

## Histórico de revisões

| Versão | Data | Alterações |
|--------|------|------------|
| v1 | 17/05/2026 | Versão inicial — D-ARQ-01 a D-ARQ-07 derivadas da entrevista da Dra. Carolini |
| v2 | 17/05/2026 | D-ARQ-04 atualizada: confirmação de que ANAC é o único regime regulatório sobreposto identificado pela Dra. Carolini; camada arquitetural mantida por argumento de custo evolutivo |
