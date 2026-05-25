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

**Nota de implementação (Sessão 002.D2, 18/05/2026).** A camada de cache em `ctx.predicados` (introduzida no Stage 4) preserva a semântica de avaliação preguiçosa do avaliador de compostos: predicados nunca alcançados por short-circuit (`ou: [True, X]` não avalia X) não entram no cache. Isso é por design — Stage 4 cacheia o caminho real de avaliação, não produz um snapshot proposicional completo. Auditoria de "quais predicados são verdadeiros sobre este GHE" é responsabilidade de trace/UI, não da forma do dicionário. Detalhes do trade-off em `HISTORICO_OPERACIONAL.md § Sessão 002.D2`.

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

**Nota de implementação (Sessão 002.D1, 18/05/2026).** A identidade de cada item do vocabulário em Python é representada como `str` (slug canônico), com validação no `carregar()` que rejeita qualquer regra referenciando slug inexistente. Não usa `Enum` nem `Literal`. Decisão tomada após avaliar as três alternativas — detalhes e gatilho de reavaliação em `HISTORICO_OPERACIONAL.md` § Sessão 002.D1.

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

## D-ARQ-14 — Vocabulário ausente em runtime gera Pendencia, não exceção nem persistência

**Contexto.** D-ARQ-12 estabelece o vocabulário (agentes, cargos, exames, EPIs) como dado tipado de primeira classe. Em runtime, o motor vai encontrar PGRs que referenciam agentes ou usam cargos que ainda não estão no vocabulário — porque o vocabulário é append-only e cresce com a base de PGRs processados. A pergunta operacional: o que o motor faz quando o vocabulário é insuficiente para o PGR sendo processado?

O motor legado (`modules/agente_medico_ia.py`) resolve isso escrevendo cargos desconhecidos em `data/cargos_desconhecidos.json` durante a execução, para backlog futuro de expansão.

**Decisão.** O motor novo **não replica** o padrão de persistência do legado. Quando o Stage 2 (ou qualquer estágio futuro) encontra agente ou cargo ausente do vocabulário:

- **Hidrata o item com defaults** (campos opcionais como `None`, listas vazias) — não falha
- **Emite `Pendencia(bloqueante=False)`** descrevendo o vocabulário ausente, com `tipo="vocabulario_ausente"` e `ghe_id` do contexto
- **Não escreve em disco**, não chama LLM, não interrompe o pipeline

Persistência do backlog de vocabulário ausente é responsabilidade da camada de observabilidade externa ao motor (CLI, web, batch — quem consome o `Resultado` decide o que fazer com as pendências).

**Consequência.**
- Motor permanece função pura (D-ARQ-09 preservada): mesmo input → mesmo output, idempotente, testável sem mocks.
- Caso de uso "primeiro PGR de um setor novo" não quebra o motor — gera pendências operacionais que orientam a expansão futura do vocabulário.
- Pendências de vocabulário ausente são auditáveis no `Resultado.matrizes[i].pendencias` e podem ser agregadas por camada superior para alimentar backlog de expansão.
- Padrão universal: aplica-se a agentes, cargos, EPIs, exames — qualquer vocabulário introduzido no futuro segue a mesma regra.

**Aplicação na D3.** Stage 2 (Sessão 002.D3) implementa essa regra para `agentes.yaml` e `cargos.yaml`. Agente do `RiscoPGR` ausente do vocabulário → hidrata com `anexo_nr07=None` + pendência. Cargo do GHE ausente → pula expansão R-GHE-02 + pendência com `regra_origem="R-GHE-02"`.

---

## D-ARQ-15 — Orquestrador compõe os estágios e define o status do Resultado

**Contexto.** Os estágios do motor (gates, riscos, predicados, emissão, consolidação) foram implementados como funções puras independentes ao longo das sessões 002.A–002.D3, sem encadeamento. Faltava a peça que recebe um `PGR`, roda os estágios na ordem correta, decide o que acontece quando um GHE não fecha, e produz o `Resultado` final com `status`. A Sessão 002.D4 — originalmente planejada como Stage 3 — foi re-escopada para esta peça (ver `HISTORICO_OPERACIONAL.md` § 002.D4).

**Decisão.** `executar(pgr, protocolo, hoje=None) -> Resultado` em `agente_medico/motor/orquestrador.py` é o único ponto de composição do motor. Política de status em três níveis:

- **Gate bloqueante (Stage 1) → `status="REJEITADO"`.** PGR não assinado ou vencido é documento inadmissível na entrada. Retorna imediatamente com `matrizes=[]`, `pendencias_globais` contendo o gate completo e `motivo_rejeicao` com os bloqueantes concatenados. Não processa GHE algum.
- **GHE bloqueado com PGR válido → `status="PRELIMINAR"`.** Qualquer `Pendencia(bloqueante=True)` em `ctx.pendencias` (predicado `Ausente` via Stage 5, ou `ConflitoProtocolo`) fecha aquela `MatrizGHE` com `linhas=[]` e suas pendências; os demais GHEs fecham normalmente. Basta um GHE bloqueado para o `status` global cair para `PRELIMINAR`.
- **Nenhum bloqueio → `status="OK"`.**

`ConflitoProtocolo` levantado por `stage_8_consolidacao` é **capturado por-GHE** e convertido em `Pendencia(tipo="conflito_protocolo", bloqueante=True)` — não propaga como exceção, não derruba os outros GHEs, fica auditável no `Resultado`. (Trocar para fail-fast em CI é decisão revisável, isolada a uma linha.)

Determinismo (D-ARQ-09 preservada): `executar()` não lê disco, não chama LLM, não usa `date.today()` — apenas repassa `hoje` a `stage_1_gates`. Puro a menos de `hoje`.

**Consequência.**
- O motor passa a ter um contrato de entrada/saída único e testável end-to-end.
- Pontos de extensão demarcados no corpo, sem stub: Stage 3 (pendências estruturais) entre riscos e predicados; Stage 6 (regime) entre emissão e consolidação. Encaixam sem reescrever a composição.
- A camada superior (CLI, web, batch) reage ao `status`: `REJEITADO` pede correção do PGR; `PRELIMINAR` lista os GHEs bloqueados e o que falta; `OK` libera a matriz.

---

## D-ARQ-16 — Arquétipo de exposição física qualificável; subtipo via identidade de agente

**Contexto.** A matriz da Dra. Patrícia define um arquétipo "exposição física → exame". Algumas exposições são qualificáveis: ruído pelo nível (acima/abaixo do nível de ação), vibração pelo tipo (corpo inteiro vs mão-braço). A vibração é o caso âncora de D-ARQ-13: o PGR frequentemente diz "vibração" sem qualificar, e forçar um valor subestima ou superestima risco. Pergunta de design: como o motor representa o subtipo de vibração, dado que `RiscoPGR` não tem campo para isso?

**Decisão.**
- Exposições físicas permanecem **primitivos** (D-ARQ-10), não um eixo novo de vocabulário. Já é o padrão de `altura`, `ruido`, `espaco_confinado`.
- Regras de exposição são **independentes e componíveis** — uma por gatilho clínico distinto. A convergência de um mesmo exame por múltiplos gatilhos é resolvida na **consolidação (Stage 8)** via dedup, nunca por fusão de regras. Fundir destruiria o audit trail por `regra_id` (D-ARQ-03) e não comportaria momentos divergentes por gatilho.
- Subtipo de risco **sem casa própria no modelo** (caso da vibração: o tipo) é representado como **identidade de agente** — três slugs em `agentes.yaml`: `vibracao_corpo_inteiro`, `vibracao_mao_braco`, `vibracao` (genérico). O primitivo retorna `True` (slug específico presente), `Ausente` (slug genérico presente — D-ARQ-13), `False` (ausente). **Não se adiciona campo `subtipo` a `RiscoPGR`.**

**Justificativa.** Qualificadores de naturezas distintas já têm representação própria: nível em `Quantificacao`, composição em `ProdutoQuimico.fds`. O tipo da vibração é o único qualificador sem casa — um campo `subtipo` genérico em `RiscoPGR` serviria apenas à vibração, pagando custo em três tipos centrais (`RiscoPGR`, `Risco`, `stage_2_riscos`) por um único caso. Slugs isolam a vibração sem tocar tipo.

**Gatilho de promoção.** Se um segundo risco exigir qualificador-tipo sem casa própria, promover subtipo a campo tipado de `RiscoPGR` — com dois casos provando o padrão, não um.

**Consequência.**
- Vibração tri-estado funciona sem mudança de tipo; exercita D-ARQ-13 contra dado real e o caminho `Ausente` → pendência bloqueante → `PRELIMINAR` do orquestrador (D-ARQ-15).
- A relação entre os três slugs é convenção codificada no primitivo, não garantia de tipo: slug fora da família vira pendência de vocabulário (D-ARQ-14), não vibração genérica. Paliativo aceito; a promoção é o caminho estrutural.
- O helper de qualificação por nível (`Quantificacao`) **não se aplica** à vibração (que qualifica por slug). Permanece inline em `ruido_acima_acao` até um segundo caso de `Quantificacao` (sílica/poeira/névoas) justificar a extração.

**Aplicação na leva 002.E (IDs corrigidos na 002.F).** Três slugs de vibração +
primitivo `vibracao_corpo_inteiro` + `R-VIB-01` (vibração corpo inteiro → RX coluna
lombo-sacra `[ADM, MR]`, VALIDADO) + `R-AUD-01` (`ruido_acima_acao` → audiometria
`[ADM, PER, MR]` 12M, VALIDADO) + `R-AUD-02` (`ruido_acima_acao` → audiometria
`[DEM]` 12M, VALIDADO) + `R-VIB-02` (`vibracao_corpo_inteiro` → audiometria
`[ADM, PER, MR]` 12M, VALIDADO). Gatilhos diferidos: ototóxico (gatilho de R-AUD-01
e branch ruído+ototóxico+vibração de R-AUD-02), motorista de equip. pesado (R-AUD-01),
vibração mãos-braços (R-VIB-02). Audiometria converge de R-PKG-ATIVCRIT / R-AUD-01 /
R-AUD-02 / R-VIB-02 e é resolvida por dedup (R-GHE-03 em consolidacao.py), nunca por
fusão de regras.

**Atualização 002.G (23/05/2026).** Dois dos três diferidos implementados: primitivo
`motorista_equipamento_pesado` (gatilho de R-AUD-01) e primitivo `vibracao_mao_braco`,
composto em `vibracao_qualquer` = `ou:[vibracao_corpo_inteiro, vibracao_mao_braco]`
(R-VIB-02 migra de `vibracao_corpo_inteiro` para `vibracao_qualquer`). **Diferido
remanescente: ototóxico** (gatilho de R-AUD-01 + branch `e:[ruido, ototoxico,
vibracao_qualquer]` de R-AUD-02) → Sessão 002.H. O gatilho de promoção desta decisão
**não disparou**: nenhum dos três exige qualificador-tipo sem casa própria (ototóxico
= flag booleana por agente; motorista = slug de atividade; VMB = slug que completa a
família de vibração). Modelo por slug permanece. Motorista nasce dormente até
`cargos.yaml` mapear cargo→slug (DT-002G-01).

**Atualização 002.H (23/05/2026) — arquétipo completo.** Terceiro e último diferido
implementado: campo `is_ototoxico: bool = False` em `Risco`, 12 agentes ototóxicos em
`agentes.yaml`, primitivo `ototoxico` (bi-estado), R-AUD-01 ganha `ototoxico` no `ou`,
R-AUD-02 ganha branch `{e: [ruido, ototoxico, vibracao_qualquer]}`. Com isso o arquétipo
de exposição física está **completo** — todos os gatilhos de R-AUD-01/R-AUD-02/R-VIB-01/
R-VIB-02 alcançados. O **gatilho de promoção desta decisão nunca disparou** ao longo de
002.E–002.H: nenhum dos qualificadores (nível de ruído → `Quantificacao`; tipo de vibração
→ slug; ototóxico → flag por agente; motorista → slug de atividade) exigiu campo `subtipo`
genérico em `RiscoPGR`. O modelo por slug/flag se sustentou; a promoção permanece como
caminho estrutural ainda não necessário. Paliativo registrado: metadata química dos
agentes ototóxicos entra pobre (DT-002H-01, append-only) — não afeta o arquétipo físico,
afeta regras químicas futuras.

---

## D-ARQ-17 — Stage 3: pendências estruturais (integridade do input por-GHE)

**Contexto.** R-PGR-04 (composição química ausente → exigir FDS; "a matriz não pode ser fechada") é regra VALIDADA sem lugar no motor. Stage 1 verifica só propriedades do documento (assinatura/validade — R-PGR-01/06). Stage 2 hidrata riscos e emite `vocabulario_ausente` (D-ARQ-14). Stage 4 (D-ARQ-13) bloqueia por predicado `Ausente`, mas só quando uma regra é avaliada sobre o predicado e só se o primitivo for tri-estado. Produto químico sem FDS resolvível é incompletude do input que existe independentemente de qualquer regra disparar; delegá-la ao mecanismo de predicado espalha a responsabilidade de integridade por todos os primitivos químicos e a torna esquecível.

**Decisão.** Stage 3 — pendências estruturais — entre Stage 2 e Stage 4 (posição já demarcada em D-ARQ-15). `stage_3_pendencias_estruturais(ctx: GHEContext, proto: Protocolo) -> None`, função pura (D-ARQ-09), lê `ctx.pgr_ghe`, muta só `ctx.pendencias`. Verifica pré-condições de integridade do input por-GHE antes de qualquer predicado. Caso âncora R-PGR-04, por produto em `ctx.pgr_ghe.produtos_quimicos`: `fds is None` (composição ausente), `fds.composicao` vazia (FDS sem composição), ou componente com CAS vazio (composição inadequada, não resolve via CAS que R-FDS-04 exige) → `Pendencia(tipo="composicao_ausente", destinatario="empresa", motivo=..., bloqueante=True, regra_origem="R-PGR-04", ghe_id=ctx.pgr_ghe.id)`. Bloqueante por-GHE → PRELIMINAR pelo trilho existente do orquestrador (D-ARQ-08, D-ARQ-15), nunca REJEITADO (R-PGR-04 manda exigir FDS, não rejeitar o PGR; R-PGR-05 reforça "não rejeitar"). Categoria append-only: novos checks estruturais (PGR sem GHE, GHE sem cargo, unidade de quantificação inválida) entram aqui sem novo estágio.

Fronteira com as camadas vizinhas:
- **vs Stage 2 / D-ARQ-14:** `vocabulario_ausente` = item nomeado fora do vocabulário (lacuna do protocolo, não-bloqueante, destinatário "protocolo"). Stage 3 = input do PGR incompleto (lacuna do documento, bloqueante, destinatário "empresa").
- **vs Stage 4 / D-ARQ-13:** predicado `Ausente` = risco presente mal-qualificado, avaliado sob demanda pela regra. Stage 3 = integridade verificada incondicionalmente, centralizada, antes dos predicados.

**Consequência.**
- A corretude da integridade de FDS não depende da disciplina tri-estado de cada primitivo químico — fica centralizada.
- Stage 3 não short-circuita o GHE: Stage 4/5 ainda rodam após o bloqueio, acumulando pendências num passe só (D-ARQ-08 — a camada superior reage rerodando). Não-short-circuit é decisão, não dívida.
- Universal (D-ARQ-06): expresso em `ProdutoQuimico`, vale para construção (tinta/solvente sem FDS), química (matéria-prima) e saúde (óxido de etileno, glutaraldeído).
- Encaixe sem reescrever o orquestrador: substitui o comentário `# Stage 3 (...) encaixará aqui` pela chamada.
- R-PGR-05 (PGR mal escrito) fica fora — ver DT-002I-01 no protocolo.

**Pré-requisito de implementação (sessão 002.J).** Antes de adicionar Stage 3, confirmar via `git show` de `predicados.py`, `regras.yaml` e `estagios/predicados_stage.py`/`emissao.py` que nenhum estágio já lê `ProdutoQuimico.fds` — verificação de não-duplicação, não pré-condição da decisão.

**Aplicação na sessão 002.J (24/05/2026).** Stage 3 implementado conforme esta decisão. Pré-requisito de não-duplicação **confirmado**: `ProdutoQuimico.fds` não é consumido por nenhum estágio anterior (grep retornou só a definição em `tipos.py`) — Stage 3 é o único consumidor. `stage_3_pendencias_estruturais` em `estagios/pendencias_estruturais.py`, três sub-casos de R-PGR-04 (`fds is None`, `composicao` vazia, componente sem CAS), todos bloqueantes por-GHE, `destinatario="empresa"`. Encaixe no orquestrador por substituição do comentário, sem reescrita da composição. Não-short-circuit verificado por teste de integração (Stage 4/5 rodam após o bloqueio; trilho PRELIMINAR do D-ARQ-15 absorve sem alteração). 269 testes verdes, mypy strict 27 arquivos. Categoria append-only inaugurada com um único check (R-PGR-04); demais checks estruturais entram sob demanda.

---

## D-ARQ-18 — Estratégia de validação Viverde: gabarito é a RQ.61 (PDF/DOCX), não o banco extraído

**Contexto.** A validação end-to-end do motor contra o caso Viverde precisa de um gabarito — a matriz "correta" contra a qual a saída do motor é conferida. Duas candidatas a gabarito coexistiam: a RQ.61 original (PDF validado pela Dra. Carolini) e `data/banco_ghe_cargo_v1.json` (extração regex do PDF pelo `scripts/migrar_pdf_rq61.py`, camada "sessao2" de 17/05, nunca documentada nos docs vivos). A 002.K auditou o banco contra o PDF para decidir qual é o gabarito, a granularidade da comparação, o mapa de vocabulário e a fronteira com o legado.

**Achados da auditoria (002.K).**
- Banco: 57 chaves `GHE:cargo`, 31 GHEs distintos. O PDF tem três blocos com numeração reutilizada (Estrutura GHE 01–16, Acabamento GHE 01–09, Administração GHE 01–06) — o migrador desambiguou por prefixo mas **perdeu funções inteiras** presentes no PDF (meio oficial de carpinteiro/pedreiro/eletricista, aplicador de asfalto, vigia, operador de grua, mestre de obra, cinco "encarregado de X", administrativo, jovem aprendiz). Cobertura parcial.
- **17 linhas-fantasma** (exame presente com todos os momentos `adm/mro/ret/dem = False`). Confronto com o PDF: todas são exames marcados "(P)" = só Periódico na RQ.61 (convenção de biomonitoramento, coerente com R-BIO-02: carcinógeno/Anexo I → só periódico). O parser não soube ler a notação "P" e gravou tudo-False em vez de per-only. **Não é diferenciação clínica nem exame ausente — é cegueira do parser à notação.** Recuperável, mas é erro que o original não tem.
- Divergências intra-GHE do banco (FORMA, CREMALHEIRA, HIDRO, ASSENTAMENTO) eram artefato das fantasmas, não diferenciação real — no PDF os cargos do mesmo GHE têm matriz idêntica nos casos checados (consistente com R-GHE-01).
- Uma divergência inter-GHE **real e fiel ao PDF**: pintor em `GHE 13 Estrutura-Pintura` (4 exames, sem químico) ≠ pintor em `GHE 05 Acabamento-Pintura` (10 exames, com trans-trans-mucônico + reticulócitos). Inventários de risco diferentes por GHE no documento — o banco acertou aqui.

**Decisão.**
1. **Gabarito de validação = RQ.61 em PDF/DOCX, não `banco_ghe_cargo_v1.json`.** Conferir o motor contra a extração lossy cobraria matrizes erradas (funções faltando, células per-only serializadas como ausentes). O original está disponível e estruturado em tabela. O banco e o restante de `data/` ficam como **legado documentado** (ver HISTORICO 002.K) — não alimentam o motor nem a validação.
2. **Granularidade = por-GHE.** O motor emite por-GHE (R-GHE-01, D-ARQ-01); o PDF é por-função. O colapso por-GHE é **parte da validação** (verificar GHE-a-GHE que a RQ.61 respeita R-GHE-01 — cargos do mesmo GHE com matriz idêntica), não pressuposto. Onde o PDF divergir intra-GHE, é achado clínico a triar, não erro de comparação.
3. **Mapa nome↔slug = fixture de teste (002.M), não item do motor.** Normalização texto-humano → slug é trabalho a montante do motor (D-ARQ-12); em validação determinística não há LLM, logo o mapa ("Ácido Trans Trans Mucônico" → slug, "Carboxihemoglobina" → slug, etc.) mora na fixture, construído do vocabulário humano da RQ.61. Candidato separado e não decidido: `exames.yaml` ganhar campo `sinonimos` para o parser real — escopo de motor, fora da 002.K.
4. **Política de divergência motor↔PDF = bug-do-motor OU lacuna-do-protocolo. Nunca "fonte divergente".** A RQ.61 é conduta clínica da Dra. Carolini (a Dra. Patrícia, coordenadora, assina os documentos; a validação clínica de todo o conteúdo é da Carolini — confirmado pelo Diovanni na 002.K). Logo não há "convenção da Patrícia" a descartar: toda divergência entre a saída do motor e o PDF é sinal — ou o motor aplicou mal uma regra (bug), ou o PDF expressa conduta correta da Carolini ainda não formalizada (lacuna do protocolo → DT clínica → sessão CONHECIMENTO). Nenhuma divergência é ruído de autoria. Esta cláusula protege D-ARQ-06: a 002.M não pode degenerar em "fazer o motor reproduzir a planilha de uma empresa".

**Estratégia de validação do método — estudo cruzado multi-matriz.** A validação do *método* (não do resultado de uma obra) se faz confrontando **as múltiplas matrizes RQ.61 + PCMSOs** disponíveis, não o Viverde isolado. Inventário levantado na 002.K (`matrizes_originais/`): 7 matrizes, 5 PCMSOs, 4 pares completos matriz+PCMSO (Viverde, CMO Construtora, Vistamerica, GPL-R78/Naturia). O cruzamento separa **regra-por-cargo** de **regra-por-agente-químico**: se uma conduta (ex: Mn sanguíneo no serralheiro, RX 24M) se repete entre empresas, é regra de cargo; se varia conforme o agente químico declarado no PCMSO daquela obra, a regra é sobre o agente e o cargo só o carreia. A matriz dá o resultado; o PCMSO dá o porquê (inventário + FDS). Esta é a estratégia oficial da fase de validação, originada de proposta do Diovanni na 002.K.

**Consequência.**
- 002.L (estruturar PGR Viverde) usa o `.docx` do PGR (leitura por tabela), e a RQ.61 PDF/DOCX como gabarito.
- A fase ganhou um passo não previsto no kickoff: **K (estratégia) → estudo cruzado das 4 matrizes [CONHECIMENTO, nova] → L (estruturar PGR) → M (test_viverde.py)**. O estudo precede a escrita do teste porque as divergências motor↔PDF que ele revela podem ser lacunas clínicas (não-bugs), e essas precisam da Carolini antes de virarem asserção de teste.
- Duas DT clínicas abertas na 002.K alimentam o estudo e a próxima rodada com a Carolini (ver protocolo): RX OIT 24M e serralheiro=fumos metálicos.
- `dicionario_cas.py` / `sinonimos_quimicos.json` (camada legado `data/`) ficam como **candidatos** a enriquecer `agentes.yaml` — a verificar no estudo, não decidido aqui.

---

## D-ARQ-19 — Periodicidade dependente de tempo de exposição acumulado é do agendador, não do motor

**Contexto.** R-RX-01 refinada (002.L-estudo) introduz periodicidades de RX que mudam conforme **tempo de exposição acumulado** do trabalhador (cortes em 15 anos: ex. sílica/asbesto sem medição = 24M até 15 anos, depois 12M). Tempo acumulado é atributo do **histórico individual**, não do PGR nem da função — o motor (função pura `(PGR, Protocolo) → Resultado`, D-ARQ-09) não tem acesso a ele.

**Decisão.** O motor emite sempre a **faixa inicial** (≤ 15 anos) e anexa ao exame um **metadado de encurtamento** declarando a regra (ex.: `apos_anos_exposicao: 15 → periodicidade: 12M`). O **agendador** (D-ARQ-11), que já confronta a matriz ideal com o histórico do trabalhador, resolve o encurtamento.

**Consequência.**
- Motor permanece determinístico e sem estado individual; não lê tempo de serviço.
- A regra de encurtamento vive como dado anexo ao `ExameEmitido`, consumido pelo agendador — mesma separação motor/agendador de R-REAPR-01/02.
- Refina o tipo `Quantificacao` (trilha D-ARQ-16 / F-3): além de `pct_LT`, discretizar **4 faixas de %LEO** e um estado **`sem_avaliacao_quantitativa`** de primeira classe — distinto de `apenas_qualitativa`, porque "sem medição" dispara 24M enquanto a v2 colapsava qualitativa → 12M.

**Base.** Aplicação de D-ARQ-09 e D-ARQ-11 a R-RX-01 refinada. Origem: 002.L-estudo.

---

## Histórico de revisões

| Versão | Data | Alterações |
|--------|------|------------|
| v1 | 17/05/2026 | Versão inicial — D-ARQ-01 a D-ARQ-07 derivadas da entrevista da Dra. Carolini |
| v2 | 17/05/2026 | D-ARQ-04 atualizada: confirmação de que ANAC é o único regime regulatório sobreposto identificado pela Dra. Carolini; camada arquitetural mantida por argumento de custo evolutivo |
| v3 | 17/05/2026 | Sessão 002 (ARQUITETURA do motor): D-ARQ-08 a D-ARQ-13 adicionadas — níveis de pendência, motor determinístico, predicados primitivos vs compostos, agendador fora do motor, vocabulário tipado, predicados tri-estado |
| v4 | 18/05/2026 | Sessão 002.D1: nota de implementação em D-ARQ-12 (vocabulário como `str` validada, não Enum/Literal) |
| v5 | 18/05/2026 | Sessão 002.D2: nota de implementação em D-ARQ-10 (cache de predicados respeita short-circuit, não força eager) |
| v6 | 19/05/2026 | Sessão 002.D3: D-ARQ-14 adicionada — vocabulário ausente em runtime gera Pendencia operacional, não exceção nem persistência em disco |
| v7 | 21/05/2026 | Sessão 002.D4: D-ARQ-15 adicionada — orquestrador `executar()` compõe os estágios e define política de status (REJEITADO/PRELIMINAR/OK); captura de ConflitoProtocolo por-GHE |
| v8 | 21/05/2026 | Sessão 002.E (ARQUITETURA): D-ARQ-16 adicionada — arquétipo de exposição física qualificável, subtipo de vibração via identidade de agente (não campo em RiscoPGR), regras componíveis com dedup no Stage 8 |
| v9 | 22/05/2026 | Sessão 002.F: correção de IDs/escopo da 002.E — R-RUI-01/02 (IDs inexistentes no protocolo) viram R-AUD-01, R-AUD-02 (nova) e R-VIB-02; momentos corrigidos para incluir MR; parágrafo de aplicação do D-ARQ-16 reescrito |
| v10 | 23/05/2026 | Sessão 002.G: D-ARQ-16 atualizado — motorista_equipamento_pesado e vibracao_mao_braco (composto vibracao_qualquer) implementados; diferido remanescente é ototóxico (002.H); gatilho de promoção não disparou |
| v11 | 23/05/2026 | Sessão 002.H: D-ARQ-16 atualizado — gatilho ototóxico implementado, arquétipo de exposição física completo; gatilho de promoção não disparou em 002.E–002.H; metadata química pobre dos ototóxicos registrada como DT-002H-01 |
| v12 | 23/05/2026 | Sessão 002.I (ARQUITETURA): D-ARQ-17 adicionada — Stage 3 pendências estruturais, âncora R-PGR-04, bloqueante por-GHE; R-PGR-05 vira DT-002I-01 |
| v13 | 24/05/2026 | Sessão 002.J: D-ARQ-17 ganha parágrafo "Aplicação na sessão 002.J" — Stage 3 implementado, não-duplicação confirmada (único consumidor de `ProdutoQuimico.fds`), não-short-circuit verificado por teste de integração |
| v14 | 24/05/2026 | Sessão 002.K (ARQUITETURA): D-ARQ-18 adicionada — gabarito de validação é a RQ.61 (PDF/DOCX), não `banco_ghe_cargo_v1.json` (extração lossy: funções perdidas, cega à notação "P", 17 linhas-fantasma); granularidade por-GHE; mapa nome↔slug na fixture; política de divergência motor↔PDF (bug OU lacuna, nunca fonte divergente); estratégia de estudo cruzado multi-matriz |