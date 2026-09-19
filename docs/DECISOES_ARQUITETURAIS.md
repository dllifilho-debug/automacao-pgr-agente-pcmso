# DECISÕES ARQUITETURAIS — AGENTE PCMSO

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

**Justificativa para manter a camada mesmo com apenas um caso:** mais barato modelar como dado agora que como código hardcoded depois. Se surgirem novos regimes (revisão regulatória, novos setores), adicionam-se como dados sem mudança de arquitetura.

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

**Decisão.** O motor emite sempre a **faixa inicial** (≤ 15 anos) em `periodicidade_meses` e, quando há encurtamento por tempo, a periodicidade pós-corte em **`periodicidade_apos_15a: Optional[int]`** (None quando não há corte). Não é metadado abstrato — é a segunda metade da mesma grandeza, tipada como `int`. O gatilho temporal ("15 anos") vive em `Motivo.detalhe` (texto), não no schema do exame. O **agendador** (D-ARQ-11), que já confronta a matriz ideal com o histórico do trabalhador, seleciona qual valor aplicar.

**Consequência.**
- Motor permanece determinístico e sem estado individual; não lê tempo de serviço.
- O segundo valor (`periodicidade_apos_15a`) vive como campo do `ExameEmitido`, consumido pelo agendador — mesma separação motor/agendador de R-REAPR-01/02. `stage_8_consolidacao` compara ambos os valores ao detectar `ConflitoProtocolo`.
- Refina o tipo `Quantificacao` (trilha D-ARQ-16 / F-3): além de `pct_LT`, discretizar **4 faixas de %LEO** (≤10 / 10–50 / 50–100 / >100) mais o estado **`sem_avaliacao_quantitativa`** de primeira classe — distinto de `apenas_qualitativa`, porque "sem medição" dispara 24M enquanto a v2 colapsava qualitativa → 12M.

**Base.** Aplicação de D-ARQ-09 e D-ARQ-11 a R-RX-01 refinada. Origem: 002.L-estudo. Refinado na 002.L0 (modelagem por segundo valor `periodicidade_apos_15a`, não metadado).

---

## D-ARQ-20 — Periodicidade condicional via família de regras por faixa, não via schema de regra estendido

**Contexto.** R-RX-01 refinada tem periodicidade que varia conforme a quantificação do risco-origem (faixa de %LEO + estado de avaliação). O formato de regra do motor é `quando (predicado) → emite [periodicidade constante]` — não suporta periodicidade como função da quantificação. Duas saídas: (A) estender o schema de regra (toca emissão, carregador, schema e todos os testes que assumem periodicidade constante); (B) explodir em família de regras de periodicidade constante, cada uma disparada por um predicado de faixa.

**Decisão.** Caminho B. R-RX-01 vira a família `R-RX-01-{adm, sem, baixa, media, alta, pnos}` em `regras.yaml`, cada entrada com periodicidade constante, disparada por um primitivo de faixa (`silica_asbesto_leo_ate_10`, `silica_asbesto_sem_medicao`, etc.). A condicionalidade clínica vive em primitivos (código) + compostos (YAML), onde D-ARQ-10 a colocou. O contrato do motor (`predicado → emite constante`) permanece intocado.

**Consequência.**
- Motor não muda (emissão, carregador e schema de regra preservados) — Caminho B usa o mecanismo predicado→regra existente.
- Cada faixa tem ID próprio e `base_normativa` própria → audit trail por faixa (o motor já referencia `regra_id`).
- Exclusividade das faixas é responsabilidade dos predicados, não do motor: cobrir a reta sem buraco nem sobreposição; estado contraditório (medição + ausência de medição declaradas juntas) vira `Ausente`/pendência bloqueante, nunca `ConflitoProtocolo`.
- **Contrato de ID:** `R-RX-01` permanece o nome clínico no protocolo; `R-RX-01-*` são entradas de implementação. ID estável honrado.

**Base.** Sessão 002.L0 (25/05/2026). Caso-âncora: R-RX-01.

---

## D-ARQ-21 — O agrupamento em GHE é canônico: o motor respeita o GHE do PGR, não re-agrupa

**Contexto.** O motor consome `PGR.ghes: tuple[GHEPGR]` como unidade de entrada. Mas o agrupamento de trabalhadores em GHE **varia por elaborador do PGR**: a CMO (PGR Viverde) separa o pedreiro em GHEs distintos por atividade (alvenaria, serviços gerais, reboco, contrapiso, cerâmica, bancada); outras empresas agrupam tudo num único GHE "pedreiro". Mesma obra, mesmo risco, modelagem diferente conforme quem escreveu o PGR. Isso levanta a dúvida: o motor deve respeitar o agrupamento do PGR, ou reconstruir os GHEs por critério próprio (cargo + perfil de exposição) antes de emitir?

**Decisão.** O motor **respeita o agrupamento do PGR como canônico** e emite matriz por-GHE conforme o PGR trouxe. Não normaliza, não re-agrupa, não reconstrói GHEs. Validação: a Dra. Carolini confirma que respeita o agrupamento do PGR recebido (não reorganiza os trabalhadores antes de decidir exames). O agrupamento é input confiável no mesmo sentido em que o inventário de risco é (R-GHE-04).

**Consequência.**
- O motor não ganha estágio de normalização de GHE — `GHEPGR` continua sendo a unidade de entrada dada.
- A mesma obra modelada por dois elaboradores produz matrizes diferentes, e **isso é correto**: fidelidade ao PGR vence consistência inter-PGR. A variabilidade é responsabilidade do elaborador, não do agente.
- Universalidade preservada (D-ARQ-06): o motor funciona para qualquer agrupamento porque não impõe nenhum.
- A saída deve registrar o agrupamento aplicado (auditoria — qual GHE do PGR originou cada matriz).
- Estende R-GHE-04 ("inventário é canônico") ao agrupamento: **o agrupamento também é canônico**.

**Base.** Sessão 002.L (25/05/2026). Confirmado por Diovanni (conhecimento do domínio: agrupamento varia por elaborador) e pela conduta da Dra. Carolini (respeita o PGR). Caso-âncora: pedreiro em 6 GHEs no PGR Viverde-CMO.

---

## D-ARQ-22 — Modelo de qualidade: erro-zero, revisão de saída e PDCA

**Contexto.** Até 002.M a incerteza clínica era resolvida perguntando à Dra. Carolini
(validação prévia, regra a regra). A partir de 002.M ela não faz mais isso; o protocolo
v8 fica congelado. A validação clínica não desaparece — desloca-se para REVISÃO DE SAÍDA:
quando o sistema extrai a matriz de um PGR, uma médica do trabalho (Patrícia/Carolini) lê
a matriz gerada e caça erros de escrita/geração. O desenvolvimento mira erro zero para
minimizar esse trabalho; erros achados viram correções (PDCA).

**Decisão — duas partes.**

*Parte A — hierarquia de resolução de incerteza clínica nova.* Resolver na ordem, parando
no primeiro nível que resolver:
1. Norma vigente (texto literal, conferido no site oficial do MTE) → `[DERIVADO — NR-x item y]`.
2. Matriz validada como precedente (RQ.61 Carolini / matriz Patrícia) → `[DERIVADO — RQ.61/Patrícia]`.
3. Analogia com regra `[VALIDADO]` existente → `[DERIVADO — analogia R-XXX]`.
4. Interpretação do Arquiteto, só quando 1-3 não resolvem → `[INTERPRETADO — prioridade na
   revisão de saída]`. Marca explícita, nunca disfarçada de validada.

*Parte B — o que torna erro-zero alcançável.* O motor se apoia em três pernas que já existem
e devem ser preservadas em toda regra futura:
- Determinismo (D-ARQ-09): mesmo PGR → mesma matriz; correção PDCA é testável e regressão detectável.
- Pendência-em-vez-de-chute (D-ARQ-08/13): ambiguidade vira pendência bloqueante, nunca exame
  errado silencioso.
- Rastreabilidade por linha (D-ARQ-03, audit trail granular): cada exame emitido carrega regra
  de origem, gatilho e — NOVO a partir de 002.M — o status de validação da regra (VALIDADO/
  DERIVADO/INTERPRETADO). A revisão de saída usa isso para priorizar: olha primeiro os
  `[INTERPRETADO]`, depois os `[DERIVADO]` por analogia, por último os `[VALIDADO]`.

**Consequência.**
- O status `[A VALIDAR — Carolini]` é descontinuado (ver PROTOCOLO § convenções e § pendências).
- O risco residual do modelo é o ERRO SILENCIOSO PLAUSÍVEL: erro que pareça correto na matriz e
  escape da leitura. Mitigação direta = a rastreabilidade por linha acima; quanto melhor a saída
  expõe origem e status, menor a chance de erro silencioso passar pela revisão.
- Toda regra criada após 002.M nomeia sua fonte no corpo (norma, matriz-precedente, analogia, ou
  marca de interpretação). Rastreabilidade regulatória: da regra à fonte.
- A saída do agente deve, quando implementada a camada de relatório, distinguir por exame o status
  de validação da regra que o gerou — requisito de produto derivado deste modelo.

**Aplicação na sessão 002.R — gate de procedência no ponto de emissão do prompt cirúrgico.** O erro silencioso plausível não se restringe à matriz: ocorre também no prompt do Code, upstream. Antes de emitir prompt cirúrgico, roda gate gêmeo ao de estado (`git log`/`status`): cada valor factual no prompt — prefixo CNAE, LT, fórmula, nº/artigo de NR, slug, periodicidade — sai com marcador da Parte A (`[DERIVADO — fonte]` ou `[INTERPRETADO]`) ou não sai. Valor sem marcador válido é barrado; "ainda não resolvido" é ausência de marcador, não um marcador. Detecção da regressão: valor que estava sob marcador numa rodada anterior e reaparece cravado sem fonte no prompt = regressão de procedência — remarcar. A falha nasce na transcrição raciocínio→prompt, onde "parecer pronto" compete com "estar correto" e o valor cravado vence o marcador por estética. Origem empírica: CNAE "06" (petróleo/NR-37) cravado como mineração/NR-22 num prompt que rodada anterior marcava `[DERIVADO — confirmar]`.

**Resolução de DT-002N-02 (002.O).** A divergência registrada na 002.N — "Parte A (três sabores
tipados) vs. convenção v9 (genérico)" — era imprecisão do resumo, não conflito de conteúdo. A Parte A
não define "três sabores tipados": define UM formato (`[DERIVADO — <fonte>]`) com a fonte preenchida
conforme o nível 1-3 da hierarquia que resolveu; `[INTERPRETADO]` é o nível 4 (marcador irmão, não
um sabor de DERIVADO). A convenção do PROTOCOLO também nunca foi "genérica" — sempre exigiu fonte
nomeada. Os dois concordavam no fundo; divergiam só em ONDE a fonte aparece. Notação canônica:
fonte NO MARCADOR. Convenção do PROTOCOLO alinhada. Sem reclassificação de regra. Rastreabilidade no
marcador vence economia visual (mesma lógica da exceção ID+NR em código).

**Nota de aplicação 003.EG — Parte B materializada na saída do motor.** `MatrizGHE` ganha dois
campos aditivos, com default e ordem estável: `riscos_resolvidos` (slugs de `ctx.riscos` por
GHE) e `predicados_avaliados` (cache nome→valor de `ctx.predicados`, serializado —
`True`/`False`/`AUSENTE: <mensagem>`). `Motivo.predicado` passa a carregar a expressão real do
`quando` da regra (`e(...)`/`ou(...)`/`nao(...)`), não mais o literal `"<composto>"`. Decisão do
Arquiteto: não abrir D-ARQ nova — o contrato de rastreabilidade por linha já existe na Parte B
acima; isto a materializa na saída, não a redecide. Recorte descartado, registrado para não ser
esquecido: rastro estruturado dentro de `predicados.avaliar` (qual risco específico satisfez a
perna vencedora de um predicado composto) mudaria a assinatura da função, usada em todo o motor
— avaliado e deixado fora desta sessão. Detalhe em PROTOCOLO DH-003ED-01 (PARCIALMENTE
RESOLVIDA, faceta `risco_origem` ABERTA) e HISTORICO 003.EG.

**Base.** Sessão 002.M (28/05/2026). Decisão de metodologia — sem caso-âncora de código.

---

## D-ARQ-23 — Operação/atividade é dado de primeira classe do GHE

**Contexto.** R-GHE-05 (risco contingente → confirmação documental) é validada e completa,
mas não é implementável: seu gatilho é "operação de risco confirmada documentalmente" (ex.:
serralheiro que solda), e `GHEPGR` (`tipos.py`) não modela operações/tarefas — só agentes
(`riscos`), cargos, EPIs, produtos químicos, psicossocial. O motor não tem onde ler "este GHE
solda". Caso âncora: serralheiro Viverde (Est-09), cujas tarefas ET38-ET42 descrevem solda mas
se perdem na modelagem atual; o motor não dispara o pacote de fumos que a RQ.61 atribuiu.

**Decisão (PROPOSTA — a implementar em sessão futura).** Modelar operação/atividade confirmada
como dado de primeira classe do GHE, distinto de agente. Esboço:
- Campo novo em `GHEPGR` (ex.: `operacoes: tuple[str, ...]`), alimentado pelo parser de PGR a
  partir das tarefas declaradas (ET38-ET42 → `solda`).
- Stage 2 (expansão de riscos) ganha regra de inferência: operação confirmada → risco implícito
  (solda → `fumos_metalicos`), mesma família de R-PGR-03 (sinal via EPI) e R-GHE-02/05.
- Universal: "operação Y confirmada → risco implícito Z" serve a qualquer setor.

**Consequência.**
- Destrava R-GHE-05 e a reprodução do serralheiro Viverde no motor.
- Exige: alterar `tipos.py` (campo novo), atualizar fixture `pgr_viverde.py` (popular `operacoes`),
  regra de inferência em Stage 2, ajuste do parser a montante. Cada regra nova com teste (metodologia).
- Modelagem fina (nome do campo, vocabulário de operações, onde mora a inferência) decide-se no
  início da sessão de implementação.

**Status:** PROPOSTA. Não implementada. Originada em 002.M.

**Base.** Sessão 002.M (28/05/2026). Caso-âncora: serralheiro Viverde (Est-09), tarefas ET38-ET42.

---

## D-ARQ-24 — Origem do LEO é resolvida por agente e cenário, separada do regime do PCMSO

**Contexto.** R-RX-01 roteia a periodicidade do RX OIT pela razão CLSC/LEO (CLSC = limite superior do IC 95% da média aritmética lognormal, definição literal do Quadro 1 do Anexo III da NR-07 — não percentil 95). O motor hoje recebe `pct_LT` pronto e morre quando o PGR só traz concentração absoluta (sílica Viverde: mg/m³, `pct_LT=None`). Falta a peça que produz a faixa a partir de mg/m³ + %quartzo + cenário. Resolvido o método em DT-002L-01: a NR-07 Anexo III NÃO fixa o LEO — só usa a fração CLSC/LEO; quem fornece o valor é o arranjo NR-09 (item 9.6.1, transitório) + anexo setorial, por agente e cenário de exposição.

**Decisão.** Introduzir um **LEO-resolver** como camada de dados entre o input fático do PGR e o classificador de faixa. Assinatura conceitual: `resolve_leo(agente, fracao, contexto_exposicao) -> (leo, fonte_normativa)`. Cadeia de precedência, agnóstica a agente:
1. LEO setorial específico para (agente, cenário) — ex.: sílica cristalina respirável em mineração = 0,05 mg/m³ (NR-22 Anexo V, Portaria MTE 105/2026, alt. 261/2026).
2. Anexo próprio da NR-09 para o agente, quando existir.
3. LT da NR-15 e anexos, via transitório NR-09 item 9.6.1 — ex.: sílica fora de mineração = LT do Anexo 12, função do %quartzo (respirável 8/(%quartzo+2); total 24/(%quartzo+3)).
4. ACGIH (NR-09 item 9.6.1.1), na ausência de LT na NR-15.

O cenário ("isto é mineração NR-22") nasce como DERIVAÇÃO de dados fáticos do PGR por GHE (CNAE, atividade de lavra/beneficiamento, local), nunca como string normativa no YAML/fixture. A fração (respirável/total) pareia CLSC e LEO na mesma fração; o roteamento do RX OIT usa respirável.

**Fronteira com decisões existentes (não confundir):**
- NÃO é instância de D-ARQ-04. D-ARQ-04 trata de **qual regime rege o PCMSO do GHE** (ANAC sobrescreve; mineração segue NR-07 padrão — confirmado pela Dra. Carolini). O LEO-resolver NÃO sobrescreve o PCMSO: o minerador segue NR-07; a NR-22 Anexo V só fornece o **valor do LEO** de um agente que alimenta a razão CLSC/LEO da própria NR-07. São eixos ortogonais: D-ARQ-04 = norma do programa; D-ARQ-24 = fonte do número do LEO por agente.
- D-ARQ-19/20 consomem a faixa já resolvida (discretização + família de regras). O LEO-resolver é upstream: produz a faixa que eles consomem.
- A validade da unidade de quantificação (mg/m³, %quartzo presente) é pré-condição estrutural do Stage 3 (D-ARQ-17), não responsabilidade do resolver.

**Consequência.**
- A escolha do LEO mora no resolver/classificador, como dado tabelado (precedência), não como `if agente == X` espalhado. Novo anexo setorial = novo registro, não novo branch.
- Retorno carrega `(leo, fonte_normativa)` — procedência rastreável da linha à norma (NR + portaria), coerente com a exigência de rastreabilidade regulatória do PCMSO.
- Destrava o `pct_LT=None` da sílica medida: dado mg/m³ + %quartzo + cenário, o resolver produz LEO → CLSC/LEO → faixa.
- %quartzo é entrada obrigatória fora de mineração (denominador da fórmula do Anexo 12); em mineração o LEO é fixo e %quartzo não é necessário para o LEO.
- A via mppdc legada do Anexo 12 (8,5/(%quartzo+10)) fica fora de escopo (abandonada na prática) — decisão consciente, não silenciosa.
- **002.Q:** os dados que o resolver exige (`Quantificacao.pct_quartzo`, `GHEPGR.cenario`) passam a existir no tipo (D-ARQ-25 Parte C, PR #36). Destrava parcial: o contrato de dados está pronto; o resolver e o classificador CLSC continuam não implementados.

**Base.** Sessão 002.N (28/05/2026). Resolução de DT-002L-01. Fontes [DERIVADO]: NR-07 Anexo III (Portaria 567/2022); NR-09 item 9.6.1/9.6.1.1; NR-15 Anexo 12 (Portaria SSST 1/1991); NR-22 Anexo V (Portaria MTE 261/2026) — todas conferidas no site do MTE. Implementação (resolver + classificador CLSC + testes) é sessão de código futura, não fechada aqui.

**Changelog.**
- **002.S** — Procedência do nível (1) corrigida: o Anexo V da NR-22 foi aprovado pela Portaria MTE 105/2026 e o LEO da sílica corrigido para 0,05 mg/m³ respirável pela Portaria MTE 261/2026 (que revogou o "0,05 ppm" da 105). Citar a cadeia 105→261, não só a 261. Refinamento de procedência — valor e cadeia de precedência inalterados, mesma ID.
- **002.S** — Materialização B.1: `resolve_leo(silica, total, MINERACAO)` retorna LEO indefinido por desenho (NR-22 Anexo V só fixa respirável; total-mineração é vazio normativo). A tabela de precedência mantém as 4 posições mesmo com n2/n4 vazios para sílica (universalidade: novo anexo setorial = novo registro). CNAE-mineração = 05/07/08/099; 06 e 091 (petróleo) fora.
- **002.V** — Bloqueio do plug B.2 (continuação operacional de DT-002L-01, resolvida na 002.N) fechado em CONHECIMENTO/ARQUITETURA, antes de virar código. Duas premissas explicitadas: (a) o motor **consome** o CLSC pronto do laudo, não o calcula — `Quantificacao.valor` `float` único basta; a amostra de medições e o cálculo do IC 95% lognormal são trabalho de higienista (NR-09), a montante, e não entram em `tipos.PGR`. [Premissa de fundo: médica lê CLSC, não recalcula — registrada como DT-002V-01, A VALIDAR com Carolini; confiança alta pela separação NR-07/NR-09.] (b) a **fração** (respirável/total) é dado da `Quantificacao` que alimenta `resolve_leo`, não do cenário — `leo_resolver.py` já trata `fracao` e `cenario` como argumentos ortogonais (`nivel(fracao, cenario, pct_quartzo)`). Faltava `Quantificacao.fracao` (gêmeo de `pct_quartzo`/002.Q: o Enum `Fracao` e o resolver já existiam desde a B.1, faltava o campo na medição que os liga). Decisão: `fracao: Optional[Fracao] = None` em `Quantificacao`. Quando sílica/asbesto com avaliação quantitativa e `fracao is None`, o plug emite Pendencia bloqueante (não chuta RESPIRAVEL) — coerente com o "estado contraditório" de R-RX-01 e D-ARQ-08/13. Implementação (campo + classificador CLSC + plug + testes) é sessão de código futura.
- **002.X** — Asbesto e PNOS entram na tabela de precedência do LEO-resolver. **Asbesto:** níveis (1)/(2) vazios; LEO = nível (3) NR-15 Anexo 12 = **2,0 f/cm³** FIXO (não fórmula), unidade **f/cm³** (não mg/m³), fração sempre respirável, pct_quartzo=None. **PNOS:** níveis (1)–(3) vazios por definição (PNOS = "sem LEO próprio", rodapé Quadro 2); LEO = nível (4) ACGIH TLV-PNOS = **3 mg/m³ respirável** `[DERIVADO — ACGIH via NR-9 9.6.1.1]`; articulação "genérico ACGIH alimenta o roteamento do Quadro 2" é `[INTERPRETADO]` (a norma define PNOS como sem-LEO mas roteia por %LEO — reconciliação técnica, valida na saída por D-ARQ-27). **Consequência sobre a arquitetura:** o nível (4) ACGIH deixa de ser fallback raro e vira caminho normal (PNOS, e provável carvão) → `agentes.yaml` passa a carregar valores ACGIH tabelados como dado de primeira classe. Exige **unit-awareness** no resolver/classificador (f/cm³ vs mg/m³): laudo em unidade incompatível com o agente é erro estrutural → Stage 3 (D-ARQ-17), mesmo ponto onde DT-002V-01 ataca a estatística do CLSC. **Carvão mineral:** 3º agente do Quadro 1 (567/2022); LEO fora da NR-15 → candidato a nível (4), valor a resolver (DT-002X-01). Implementação (ramos asbesto/PNOS no resolver + classificador CLSC + testes) é sessão de código futura.
- **002.Y** — Ramo PNOS materializado no resolver (`_pnos_n1..n4`; n1–n3 → None, n4 ACGIH → 3,0 mg/m³ resp se fração RESPIRAVEL). PNOS entra em `_PRECEDENCIA`. O nível (4) ACGIH, antes fallback raro, é agora caminho normal (confirmado em código, não só especificado). Consumido por `_helper_pnos` (predicados.py) via injeção de fração — ver D-ARQ-29.

---

## D-ARQ-25 — Camada de extração: contrato LLM→motor e normalização de vocabulário a montante

**Contexto.** O motor é função pura `(PGR_estruturado, Protocolo) → Resultado` (D-ARQ-09) e
consome `tipos.PGR`. Hoje a única fonte de `tipos.PGR` é fixture escrita à mão (Viverde). Para
o objetivo de produção — rodar sobre qualquer PGR real de qualquer setor, não só o caso-teste —
falta a camada que transforma PGR real (PDF/docx) em `tipos.PGR`. Essa é a etapa 3 do plano
original do projeto ("voltar à camada de extração e adaptar o prompt do Gemini ao schema novo"),
adiada até o motor existir. O motor agora existe. Dois extratores legados coexistem e nenhum
serve: `parser_pgr.py` (regex) devolve dict de chaves cruas (`"RUIDO"`), sem quantificação, sem
vocabulário canônico, e mistura extração com decisão de exames (viola D-ARQ-09);
`extrair_pgr_estruturado_via_gemini` (LLM) devolve GHEs em linguagem natural com cargos e riscos
como texto, mas sem quantificação e sem slugs canônicos. Ambos ficam abaixo do contrato que
`tipos.PGR` exige.

**Decisão — três partes.**

*Parte A — o contrato de fronteira é `tipos.PGR`, sem intermediário.* A camada de extração produz
diretamente `tipos.PGR`/`GHEPGR`/`RiscoPGR`/`Quantificacao`. Não há formato intermediário próprio
da extração. O motor não muda para acomodar a extração; a extração produz o que o motor já exige.
O parser legado (`parser_pgr.py`) NÃO é portado — fica no legado Streamlit, aposentado com ele.

*Parte B — normalização de vocabulário é responsabilidade da extração, a montante do motor.* A
tradução de risco/cargo/EPI em linguagem natural para o slug canônico do `vocabulario/*.yaml`
acontece na camada de extração, antes de instanciar `RiscoPGR.agente`. O motor recebe slugs
canônicos e permanece puro (D-ARQ-09 preservada). Risco/cargo sem slug correspondente vira
`Pendencia(tipo="vocabulario_ausente", bloqueante=False)` conforme D-ARQ-14 — a extração não
inventa slug nem descarta o agente. Mecanismo de normalização (LLM com vocabulário no prompt,
dicionário de sinônimos, ou híbrido) é decisão de implementação, não deste D-ARQ.

*Parte C — forma final de `tipos.PGR` (contrato-alvo completo).* A extração precisa preencher
campos que `tipos.py` hoje não tem. O contrato-alvo é especificado aqui de uma vez; a
implementação de cada campo é fatiada em sessões futuras. Conferido contra `tipos.py` (002.P):

- JÁ EXISTEM e a extração preenche: `PGR.ghes`, `GHEPGR.{id,nome,cargos,riscos}`,
  `RiscoPGR.{tipo,agente}`, `Quantificacao.{valor,unidade,relacao_LT,pct_LT,apenas_qualitativa,
  sem_avaliacao_quantitativa}`.
- EXISTEM no tipo mas nenhum extrator legado preenche (gap de extração, não de tipo):
  `PGR.validade`, `PGR.assinatura_engenheiro` (gates R-PGR-01/R-PGR-06); `GHEPGR.{epis,
  produtos_quimicos,psicossocial}` (R-PGR-03 sinal por EPI; R-FDS-* via produtos; R-PSY-01);
  `ProdutoQuimico.fds`; `Componente.cas`.
- NÃO EXISTEM no tipo — extensão futura: `Quantificacao.pct_quartzo` (denominador Anexo 12,
  D-ARQ-24); cenário de exposição em `GHEPGR` (CNAE, atividade, local) que alimenta o
  LEO-resolver a decidir mineração-NR-22 vs. não-mineração (D-ARQ-24). Forma exata da extensão
  (campos diretos vs. sub-objeto `CenarioExposicao`) é decisão de implementação da sessão que
  encostar em D-ARQ-24.

**Fronteira com decisões existentes (não confundir):**
- Preserva D-ARQ-09: motor puro; toda LLM (extração, normalização) fica a montante.
- Consome D-ARQ-12: o vocabulário tipado é o alvo da normalização da Parte B.
- Consome D-ARQ-14: vocabulário ausente em runtime → Pendencia, não exceção; aplica-se à extração.
- Destrava D-ARQ-24: os campos `pct_quartzo` e cenário de exposição (Parte C) são pré-requisito
  do LEO-resolver. D-ARQ-24 não implementa até a extração entregar esses dados (ou fixture supri-los).
- Substitui o caminho de extração do legado, não o motor: o parser regex e o Gemini atual são
  referência histórica, não base de código a evoluir.

**Consequência.**
- Roadmap de produção: (1) estender `tipos.py` com os campos faltantes (Parte C); (2) implementar
  a extração LLM→`tipos.PGR` com normalização de vocabulário; (3) validar a extração contra a
  fixture Viverde (extrair um PGR Viverde real deve reproduzir, ou aproximar-se de, a fixture
  escrita à mão — gabarito de forma, D-ARQ-18); (4) validar contra um PGR não-construção
  (D-ARQ-06, universalidade). Fatias independentes, ordem revisável.
- Determinismo do motor intacto: a extração pode ser não-determinística (LLM), mas seu output é
  `tipos.PGR` congelado que o motor processa deterministicamente. A fronteira LLM/determinístico
  é exatamente `tipos.PGR`.
- Rastreabilidade: cada campo extraído deve poder apontar para o trecho do PGR de origem
  (requisito de auditoria do PCMSO) — exigência registrada, detalhe de implementação futuro.

**Base.** Sessão 002.P (30/05/2026). Decisão de arquitetura — sem caso-âncora de código.
Origem: leitura dos contratos reais (`tipos.py`, `parser_pgr.py`, `ia_client.py`, fixture Viverde)
e do plano original em HISTORICO § Sessão 002 (etapa 3 adiada). Implementação é sessão futura.

**Aplicação na sessão 002.Q (30/05/2026).** A forma da extensão da Parte C foi decidida e implementada: cenário de exposição vira sub-objeto `CenarioExposicao` (dataclass frozen, campos `cnae`/`atividade`/`local` todos `Optional`, default `None`), e `GHEPGR` ganha `cenario: Optional[CenarioExposicao] = None`. `pct_quartzo: Optional[float] = None` fica direto em `Quantificacao`. Razão da escolha de sub-objeto sobre campos soltos: coesão (cenário é unidade fática), evolução prevista por D-ARQ-24 (mais dados de cenário virão), opcionalidade limpa. `CenarioExposicao` carrega só dado fático — a derivação normativa (mineração-NR-22) permanece no LEO-resolver downstream, preservando D-ARQ-24. PR #36, commit 46e32dc. Testes: 5 novos (pct_quartzo materializa R-RX-01/D-ARQ-24 — falha sem o campo; cenário só construção/serialização, sem consumidor clínico). Os itens (2) da extração e o LEO-resolver seguem como sessões futuras.

**Nota (002.V).** `Quantificacao.fracao: Optional[Fracao]` identificado como campo faltante do contrato-alvo (categoria "NÃO EXISTEM no tipo — extensão futura", junto a `pct_quartzo`). Pré-requisito do plug do LEO-resolver no pipeline (D-ARQ-24): `resolve_leo` exige `fracao` como argumento desde a B.1, mas nenhum campo de `tipos.PGR` a fornecia. Materialização na sessão de código da B.2.

**Nota (003.BA, discussão de escopo pós-merge) — fronteira de PRODUTO: o que o motor novo EMITE.** A saída do legado que o engenheiro usa (Anexo I do PGR: inventário NR-01 + higiene NR-15/09 + exames NR-07 + Dec 3.048 + eSocial Tab 24) empacota quatro domínios numa linha — o acoplamento que D-ARQ-09 separa. Confirmado em disco (937209c): o `Resultado` do motor novo emite só o lado-MÉDICO — matriz GHE×`ExameEmitido` (exame/periodicidade/momentos/rastreabilidade regra→norma/pendências); zero previdenciário (Dec 3.048) e zero eSocial (`git grep` vazio em `agente_medico/`; vivem só em `modules/modulo_esocial_xml.py` / `modulo_engenharia.py`). A tela é lado-ENGENHEIRO (Anexo I), que no modelo é INPUT (`tipos.PGR`), não produto do agente médico. **Decisão de escopo (Arquiteto recomenda, Diovanni ratifica):** NÃO replicar o Anexo I do engenheiro no motor novo agora — (1) é escopo do engenheiro, não o diferencial médico; (2) rodaria sobre fixture até a ingestão existir (prova de vida falsa); (3) Dec 3.048/eSocial são mapeamento-commodity que o legado já faz; (4) "completo assim" re-acopla o que D-ARQ-09 separou. Previdenciário + eSocial + colunas de engenharia = **frente de EMISSÃO separada, perto do cutover**, reusando os mapeamentos do legado — requisito de PARIDADE p/ desligar o Streamlit (não se pode entregar menos colunas que o engenheiro usa hoje), não escopo do motor de decisão. A prova de vida certa é o **Marco 1** já cravado no PAINEL (PGR real → matriz PCMSO rastreável validada pela coordenadora), não uma réplica visual do Anexo I. Abre **DT-003BA-01**. Nenhuma R-* criada/alterada. Sem código.

DT-003BA-01: fronteira de produto — colunas previdenciária (Dec 3.048), eSocial (Tab 24) e demais saídas de engenharia ficam FORA do motor de decisão; entram como frente de emissão perto do cutover (paridade p/ desligar o Streamlit). Resolver NO cutover, com input do que o engenheiro/cliente de fato usa — não cravar cedo ("o dado precede a regra").

---

## D-ARQ-26 — Ritual de abertura de sessão é uma skill /kickoff: coletor de estado determinístico, julgamento no Arquiteto

**Contexto.** A abertura de cada sessão repete um ritual de precisão obrigatória: reler docs vivos na ordem, rodar o gate de estado (git log/status), cruzar git × HISTORICO, derivar o número da próxima sessão e o foco das pendências. Feito de memória turno a turno, o ritual degrada — a 002.R registrou o caso: valor factual ([INCERTO]) virou hardcode na transcrição (CNAE "06"). O kickoff que o Arquiteto escreve à mão carrega [INTERPRETADO] recorrentes — número da sessão, topo de main esperado — inferidos da leitura do estado, não do estado real. A raiz é a mesma do D-ARQ-22: estado inferido virando estado afirmado.

**Decisão.** Materializar o ritual de abertura como uma skill do Claude Code, `/kickoff`, versionada no repo em `.claude/skills/kickoff/SKILL.md` (sob git — não na área de skills da UI, que não é versionada e seria cópia-fantasma, contra a regra de fonte-de-verdade). Quatro propriedades, decididas na sessão de desenho:

1. **Invocação explícita** (`/kickoff`), não auto-load. O ritual dispara por ato consciente na abertura, como `git status` — não "quando o agente acha relevante". Auto-load reintroduz o não-determinismo que se combate.
2. **Híbrida: a skill coleta, o Arquiteto julga.** A skill roda a parte factual (git + HISTORICO) e reporta estado; o Arquiteto destila o kickoff final no chat (foco declarado vs. real, gate de 2ª passada, prioridade, número da próxima sessão). A skill nunca decide foco, prioridade, recorte, nem calcula o sucessor da série.
3. **Skill burra por design.** Regra-mestra: entre calcular/selecionar e ler/reportar, sempre ler e reportar. Toda vez que a skill calcula ou seleciona, erra em caso de borda (virada de bloco 00X.Z, sessão sem número de série como o rename, bloco de pendências resumido); toda vez que lê e reporta verbatim, acerta. Menos lógica embutida = menos coisa a desatualizar.
4. **Saída só em tela, nenhum arquivo.** Evita criar artefato-fantasma (a própria poluição que o projeto combate na raiz) e remove dependência de permissão de escrita.

**Estrutura (três zonas, padrão Agent Skills):** Definição (o que faz / o que nunca faz — incl. nunca inventar estado, nunca criar branch, nunca ler docs-fantasma da raiz) → Lógica (coleta: git log/status; último cabeçalho de sessão do HISTORICO verbatim; cruzamento git × HISTORICO com PARADA na divergência; cópia literal-integral do bloco de pendências; suíte herdada) → Verificação (todo valor factual tem origem real ou marca [INTERPRETADO]; divergência git×HISTORICO vira o relato principal, não o esqueleto).

**Fronteira com decisões existentes (não confundir):**
- Operacionaliza parcialmente D-ARQ-22 (gate de procedência): a skill embute "nunca cravar valor sem origem", mas referencia o D-ARQ-22 vigente em vez de fixar versão — a skill aponta para a fonte viva, não a copia (mesma disciplina anti-cache).
- Não toca D-ARQ-09 nem o motor: é META, fora do caminho de inferência clínica.
- O cruzamento git × HISTORICO que PARA na divergência é o mecanismo central — é o que pegaria "sessão fechada incompleta" (ex.: código em main que o HISTORICO não reflete). Divergência é sinal de bug de processo, reportado, nunca silenciado escolhendo o git.

**Consequência.**
- O [INTERPRETADO] recorrente do número de sessão e do estado esperado some do kickoff: passa a vir do HISTORICO/git reais coletados pela skill.
- Skill fina é descartável sem custo se na prática não economizar sobre rodar os comandos à mão — é META, não toca motor. O valor não é complexidade; é tornar o ritual não-opcional e idêntico toda vez.
- Implementação (gravar o SKILL.md, confirmar frontmatter/allowed-tools contra exemplo real, testar /kickoff) é sessão de Code futura. O eval de aceitação: /kickoff reproduzir, lendo só git + HISTORICO, o estado que um kickoff manual produziria (gabarito disponível: rascunho de B.2 da 002.S).

**Base.** Sessão META (31/05/2026). Origem: intuição do Diovanni a partir de material externo sobre skills (NotebookLM de 3 vídeos); mecânica de skills confirmada na doc oficial do Claude Code (.claude/skills/, frontmatter controla invoke-mode, padrão Agent Skills aberto). Desenho do SKILL.md fechado nesta sessão; allowed-tools e sintaxe exata do frontmatter ficam [INCERTO — Code confirma contra SKILL.md real antes de gravar]. Implementação não fechada aqui.

**Aplicação na sessão 002.U (31/05/2026).** Frontmatter resolvido contra a doc oficial (code.claude.com/docs/en/skills), não blog — os [INCERTO] da Base ficam fechados:
- Command e skill foram fundidos no Claude Code; o artefato é `.claude/skills/kickoff/SKILL.md` (skill, forma recomendada) — não command, não skill auto-invocada.
- A propriedade 1 (invocação explícita, sem auto-load) materializa-se com `disable-model-invocation: true`: só o usuário invoca `/kickoff` e a descrição nem entra em contexto até a invocação. `user-invocable: false` seria erro — esconde do menu `/` e deixa só o Claude invocar, o oposto da propriedade 1.
- `allowed-tools` pré-aprova tools sem prompt; para skill de projeto só vale após o trust dialog do workspace. Escopo read-only `Bash(git log *) Bash(git status *) Read` — sem escrita (propriedade 4). O token exato é validado em `/permissions` antes de gravar.
- Coleta de estado na v1: a skill instrui o Claude a rodar os comandos com as próprias tools, não injeção `!`comando`` — robustez no ambiente Windows/PowerShell (injeção default-bash arrisca não rodar; output com acento arrisca CP1252). Injeção fica como upgrade se o eval mostrar passo pulado.
- Versionamento: `.claude/` era ignorado inteiro; exceção cirúrgica `.claude/*` + `!.claude/skills/` põe a skill sob git sem expor worktrees/config local. Resolve para skills o caso da dívida de versionamento adiada em D-ARQ-18; a decisão geral .gitignore-vs-versionar segue adiada.

---

## D-ARQ-27 — Método de construção: derivação normativa via PDCA, Carolini valida saídas (não método)

**Sessão:** 002.W (02/06/2026)

**Decisão.** Durante a construção do agente, a fonte operante de método clínico é a leitura direta das normas (NR-07, NR-09, NR-15 e correlatas, versão vigente). A Dra. Carolini participa como **validadora das saídas** (as matrizes de exames geradas), ao final do projeto — não como consultora de método durante a formalização das regras. O time estuda a norma, deriva a regra, marca o que é interpretação, e roda o ciclo PDCA.

**Efeito sobre a hierarquia de fontes.** A hierarquia original põe o protocolo da Carolini no topo (item 1). Esta decisão estabelece que, na fase de construção, esse item está em aberto — a regra é derivada da norma (item 2) e marcada `[INTERPRETADO]` quando a norma não crava o critério. A validação da Carolini no aceite final é o que promove uma regra de `[INTERPRETADO]` para `VALIDADO`. A hierarquia não muda; muda quando cada item entra em vigor.

**Risco aceito e mitigação.** Derivar método só da norma tem ponto cego: periodicidade por faixa, critério de encurtamento e leitura de CLSC são frequentemente interpretação clínica que a NR não fixa. Mitigação obrigatória: toda regra derivada por interpretação carrega `status: INTERPRETADO` e a marca da fonte normativa de origem. A Matriz da Dra. Patrícia segue como referência (item 3), não gabarito. O teste-final-PGR gera as matrizes que vão ao aceite da Carolini — é o ponto de validação do ciclo.

**PDCA aplicado:** Plan (ler a norma, formular a regra) → Do (implementar com teste) → Check (marcar INTERPRETADO o que é interpretação; rodar o PGR de teste) → Act (validação final da Carolini promove INTERPRETADO→VALIDADO ou corrige).

**Primeira instância do método:** DT-002L-01 — pergunta de método originalmente endereçada à Carolini ("como converter mg/m³ em faixa de %LEO?") foi respondida por derivação normativa própria (NR-15 Anexo 12 via NR-09 9.6.1) e materializada em código na B.2 (002.W). A validação da conversão segue para o aceite final, conforme esta decisão.

---

## D-ARQ-28 — Caminho declarativo regra→lembrete operacional (PROPOSTA, não implementada)

**Contexto.** D-ARQ-05 estabelece lembrete operacional como saída de primeira classe (TODO não-bloqueante para o executor). Mas o motor não tem caminho para uma *regra* de `regras.yaml` emitir um lembrete: `stage_5_emissao` produz apenas `ExameEmitido`, e `R-OP-01` ("verificar FDS do eletrodo") existe só como string em `agentes.yaml.protocolos_especiais`, sem mecanismo que a transforme em `Pendencia`. Caso âncora: a faixa `pnos_leo_10_100` (R-RX-01-pnos-10a100) — o Quadro 2 prevê "repetir RX após 5 anos a critério clínico", uma repetição não-periódica que é exatamente um lembrete operacional. Em 002.Y a faixa emite só o admissional; o lembrete clínico ficou sem casa (DT-002Y-01).

**Decisão (PROPOSTA).** Estender o emissor para que uma entrada de regra possa declarar um lembrete que vira `Pendencia(bloqueante=False)`. Esboço: campo opcional `lembrete` na regra (`{tipo, destinatario, motivo}`); `stage_5_emissao` o converte em `Pendencia` quando a regra dispara, mutando `ctx.pendencias` como já faz para Ausente. Universal: serve a R-OP-01 (FDS de eletrodo), à repetição clínica do PNOS, e a qualquer "faça X após a matriz" futuro.

**Consequência.** Toca `emissao.py` + schema de regra + carregador + testes — mudança de mecanismo, não de dado. Por isso ficou fora de 002.Y (que era materialização de dado clínico): empacotar as duas violaria "uma implementação por sessão" e misturaria naturezas. Quando implementada, R-RX-01-pnos-10a100 ganha o lembrete e DT-002Y-01 fecha.

**Status:** PROPOSTA. Não implementada. Originada em 002.Y. Caso-âncora duplo: R-OP-01 (preexistente, sem trilho) e R-RX-01-pnos-10a100 (002.Y).

**Base.** Sessão 002.Y (04/06/2026).

---

## D-ARQ-29 — Fração do PNOS é invariante normativa: helper injeta RESPIRAVEL, não bloqueia

**Contexto.** D-ARQ-24/002.V fixou que sílica/asbesto com medição quantitativa e `fracao=None` gera `Ausente` bloqueante — a fração (respirável/total) é fato do laudo que muda a fórmula do Anexo 12 (respirável `8/(%q+2)`, total `24/(%q+3)`), e chutá-la inventaria um número de exposição (erro silencioso, a classe que D-ARQ-22 combate). Ao materializar PNOS (002.Y), `_helper_pnos` enfrenta o mesmo `fracao=None`: a fixture Viverde traz 11 PNOS medidos em mg/m³ sem fração declarada. Aplicar a regra da sílica (bloquear) deixaria todo PNOS medido sem rotear.

**Decisão.** Para PNOS, o helper **injeta `fracao=RESPIRAVEL` quando `None`**, não bloqueia. Justificativa: em PNOS a fração não é grau de liberdade do laudo — o Quadro 2 do Anexo III só define comportamento para poeira respirável ("sem ramo TOTAL", R-RX-01/002.X), e o LEO é fixo (TLV-PNOS ACGIH 3 mg/m³ resp), não fórmula que dependa da fração. Injetar RESPIRAVEL não chuta um fato ausente: codifica uma invariante da norma. A assimetria com sílica (sílica bloqueia, PNOS injeta) é **intencional e documentada no helper** — não é inconsistência, é a norma sendo diferente: fração é fato em sílica, invariante em PNOS.

**Fronteira com D-ARQ-24/002.V (não confundir).** D-ARQ-24 manda bloquear em sílica/asbesto porque lá a fração altera o denominador. D-ARQ-29 não revoga isso — vale só para PNOS, onde o denominador é fixo. As duas regras coexistem: o `_helper_silica_asbesto` bloqueia, o `_helper_pnos` injeta. Não unificar os helpers nesse ponto é decisão, não dívida.

**Consequência.**
- PNOS medido em mg/m³ roteia por faixa sem pendência de fração — destrava o roteamento que o Viverde exige.
- O erro silencioso que D-ARQ-22 combate **não** reaparece: não há número de exposição inventado, porque o LEO do PNOS é fixo independentemente da fração.
- Validação contra Viverde real (os 11 PNOS em contexto completo) fica para a sessão de integração — ver DT-002Y-02. Em 002.Y a decisão é coberta por testes sintéticos de conversão (`mg/m³ → faixa`, com asserção de não-bloqueio).

**Base.** Sessão 002.Y (04/06/2026). Caso-âncora: PNOS medido do PGR Viverde. Materializa R-RX-01 (Quadro 2, 002.X) em código.

---

## D-ARQ-30 — Rotina de briefing diário é informativa; /kickoff permanece o gate de abertura

**Contexto.** Claude Code Routines (research preview, abril/2026) permite rodar uma sessão do Code na nuvem por agendamento, sem máquina local ligada. Tentação: usar isso para substituir o ritual de abertura (/kickoff, D-ARQ-26). Mas o /kickoff tem duas metades — coleta factual (git/HISTORICO) e julgamento do Arquiteto (foco, prioridade, recorte, número da sessão) — e só a primeira é automatizável. A segunda exige o Diovanni e o chat.

**Decisão.** Uma rotina agendada (03:30 BRT, diária, somente leitura) gera um briefing de ESTADO FACTUAL do projeto e o envia por e-mail: git log -10, git status, último bloco do HISTORICO verbatim, contagem da suíte, DTs abertas. A rotina NUNCA julga foco/prioridade/recorte, nunca calcula o número da próxima sessão, nunca escreve no repo (sem commit/push/branch/edição). É pré-aquecimento informativo, não decisão.

O /kickoff (D-ARQ-26) permanece o gate canônico de abertura de sessão, de invocação consciente. Razão de não ser redundante: o briefing roda 03:30 e pode estar VELHO quando a sessão abre (outro merge entre o briefing e o início do trabalho); o /kickoff recoleta o estado real NAQUELE instante. Confiar no briefing como estado de abertura seria usar cache em vez da fonte — o que o protocolo proíbe (git vence sempre).

**Fronteira com D-ARQ-26 (não confundir).** D-ARQ-26 = ritual de abertura, invocação consciente, coleta + julgamento, na hora de trabalhar. D-ARQ-30 = briefing desassistido, agendado, só coleta, antes de acordar. Momentos e responsabilidades distintos; nenhum cobre o outro.

**Papel: aponta, não afirma.** O briefing levanta bandeiras para o /kickoff conferir — não estabelece fatos. Evidência empírica (05/06/2026, 1º briefing): acertou ao detectar uma dívida de formatação que o /kickoff é estruturalmente cego para ver (sessões 002.X–Z gravadas com negrito em vez de cabeçalho ##, invisíveis ao grep de cabeçalho do próprio kickoff) — valor que o gate sozinho não tem. Mas errou a confiança da suíte: rodou em branch sandbox sem pandas, reportou "328 verde" como alegação do HISTORICO, não medição própria. Lição: o briefing é bom a apontar, fraco a afirmar; tratar achados como pistas a verificar, nunca como estado.

**Consequência.**
- A rotina respeita read-only por design: permissões limitadas a git log/status, pytest, leitura de arquivo, envio de e-mail. Qualquer escrita seria decisão silenciosa (a classe que D-ARQ-22 combate).
- Roda em ambiente sandbox (branch própria, sem suíte legada por falta de pandas) — confirma na prática que valida só parcialmente e NÃO substitui o /kickoff no ambiente real.
- Não substitui o /kickoff; se o briefing e o /kickoff divergirem, o /kickoff (mais recente, ambiente real) vence.
- Research preview: comportamento e limites podem mudar; Pro = 5 execuções/dia (1 rotina diária cabe folgado).

**Base.** Sessão META (04/06/2026), aceite empírico 05/06/2026. Origem: feature Routines do Claude Code. Implementação: rotina criada na UI, não versionada no repo (config de produto, não código do projeto).

---

## D-ARQ-31 — Bloqueio é por-risco/por-linha, não por-GHE: MatrizGHE tri-estado (VÁLIDA/PARCIAL/BLOQUEADA) com pendência anexada à linha

**Contexto.** D-ARQ-15 definiu a política de status do orquestrador: um GHE com `Pendencia(bloqueante=True)` fecha aquela `MatrizGHE` com `linhas=[]` e o `Resultado` global cai para `PRELIMINAR`; os demais GHEs fecham normalmente. Isso resolve o cross-GHE (um GHE bloqueado não derruba os outros), mas dentro de um GHE a `MatrizGHE` é binária: ou linhas completas, ou vazia. O primeiro risco bloqueante zera as linhas que outros riscos do mesmo GHE já rotearam. Caso-âncora — Acab-05 (Viverde): sílica sem fração bloqueia (`Ausente` em todas as faixas R-RX-01-*, D-ARQ-24/D-ARQ-29) e o `rx_torax_oit` que o PNOS justificaria (faixa baixa → admissional) some junto, porque o orquestrador zera `linhas` no primeiro bloqueante. O contraste Est-08 (MEK+PNOS, sem sílica: PNOS roteia 0M sem bloquear) prova que o problema é o achatamento, não o PNOS. Universal, não só sílica×PNOS: qualquer GHE com um risco resolvido e outro com dado faltando sofre o mesmo (química: um agente com FDS + um sem; etc.).

A pergunta de método (DT-002Z-01): GHE com um risco pendente vai ao PCMSO como parcial, ou o risco pendente invalida o GHE inteiro?

**Resolução normativa.** A NR-07 vigente (Portaria 567/2022) não legisla emissão de motor, mas fixa a postura diante de dado insuficiente/inconsistente: o item 7.5.1 estabelece que o PCMSO é elaborado considerando os riscos ocupacionais identificados e classificados pelo PGR; o item 7.5.5 manda o médico reavaliar inconsistências no inventário de riscos em conjunto com os responsáveis pelo PGR (reconciliar, não descartar); o item 7.6.4 manda registrar a insuficiência de informação, não suprimir o programa. Em nenhum ponto a norma manda apagar os exames determinados de um trabalhador porque um agente do mesmo GHE está com dado faltando — o padrão é sinalizar + reconciliar + registrar, com o resto seguindo. Reforço por regra `[VALIDADO]`: R-PGR-04 e R-PGR-05 mandam solicitar o dado, não rejeitar. O all-or-nothing intra-GHE é uma rejeição silenciosa que contradiz essa postura. `[DERIVADO — NR-07 7.5.5/7.6.4 (Portaria 567/2022); analogia R-PGR-04/R-PGR-05]`.

**Decisão.** Bloqueio passa a ser por-risco/por-linha, nunca por-GHE. A matriz de um GHE é a composição das contribuições por-risco independentes (já o que D-ARQ-16 e R-GHE-03 afirmam); um risco sem dado não apaga a contribuição determinada de outro.

1. `MatrizGHE` ganha `status ∈ {VÁLIDA, PARCIAL, BLOQUEADA}`:
   - **VÁLIDA** — todas as contribuições de risco determinaram.
   - **PARCIAL** — algumas determinaram (linhas emitidas), outras estão bloqueadas (pendências carregadas).
   - **BLOQUEADA** — nenhuma contribuição pôde ser determinada (único risco do GHE bloqueado; ou bloqueio estrutural Stage 3 que impede sequer conhecer o agente, sem nenhum outro risco determinável no GHE).
2. O orquestrador deixa de zerar `linhas` no primeiro bloqueante. Emite as linhas determináveis e carrega as `Pendencia(bloqueante=True)` junto, na mesma `MatrizGHE`.
3. Pendência bloqueante que incide sobre uma linha emitida fica anexada à linha, não solta no nível do GHE. Caso convergente (R-GHE-03, linha única): quando um risco bloqueado e um determinado convergem no mesmo exame (Acab-05: sílica `Ausente` + PNOS admissional → `rx_torax_oit`), a linha sai com o piso determinado (admissional) e a pendência da sílica anexada ("periodicidade pode escalar quando a fração for fornecida"). Isto é condição de segurança, não opcional — ver Consequência.
4. `Resultado.status` global cai para `PRELIMINAR` se qualquer GHE for PARCIAL ou BLOQUEADA (trilho de D-ARQ-15 preservado; muda só a granularidade da `MatrizGHE`, não a política de status global). REJEITADO segue exclusivo dos gates Stage 1.

Direção da decisão (parcial sobre binário; bloqueio por-risco) é `[DERIVADO — NR-07 7.5.5/7.6.4; analogia R-PGR-04/R-PGR-05]`. O modelo tri-estado específico e a anexação pendência-à-linha são `[INTERPRETADO — prioridade na revisão de saída]`: a norma não fixa a forma técnica.

**Por que não o binário (2ª passada).** O único argumento real pró-binário é o subdimensionamento silencioso do caso convergente — emitir "admissional" para uma linha que a sílica poderia escalar a 12M/24M é um teto silencioso, a classe de erro que D-ARQ-22 combate. Esse argumento não derruba o parcial: impõe a restrição da cláusula 3 (pendência anexada à linha torna o teto visível, não silencioso). O outro argumento pró-binário — proteger contra assinar matriz incompleta — já é coberto por `status=PRELIMINAR` + pendência. Em troca, o binário suprime exame determinado (subexame — a direção de dano), sem âncora normativa. O parcial tem âncora (7.5.5/7.6.4) e não subexamina.

**Fronteira com decisões existentes (não confundir):**
- **D-ARQ-15** — não revoga a política de status global (REJEITADO/PRELIMINAR/OK). Refina a granularidade: a `MatrizGHE` deixa de ser binária (linhas-completas vs. `linhas=[]`) e ganha o estado PARCIAL. PRELIMINAR continua sendo o status global de "não-apto a assinatura".
- **D-ARQ-08** — `Pendencia(bloqueante=True)` permanece; muda como ela interage com a emissão: bloqueia a contribuição do risco dela, não o GHE inteiro. A distinção bloqueante/operacional é intocada.
- **D-ARQ-16 / R-GHE-03** — base conceitual: regras de exposição são independentes e componíveis, convergência resolvida por dedup no Stage 8. Esta decisão é a consequência lógica de tratar a composição como de fato independente também sob bloqueio.
- **D-ARQ-22** — a anexação pendência-à-linha (cláusula 3) é a mitigação direta do erro silencioso plausível no caso convergente. A rastreabilidade por linha (`regra_id`) é o que torna a anexação possível.
- **D-ARQ-24 / D-ARQ-29** — preservadas. Sílica sem fração continua gerando `Ausente` bloqueante (a fração altera o denominador do Anexo 12); PNOS continua injetando RESPIRAVEL (invariante do Quadro 2). O que muda é que esse bloqueio da sílica não contamina o GHE — fica contido na contribuição da sílica e anexado à linha de RX.
- **D-ARQ-28** — distinta, não é o veículo: D-ARQ-28 adiciona trilho regra→`Pendencia(bloqueante=False)` (lembrete operacional). D-ARQ-31 trata de como `Pendencia` bloqueante interage com a emissão. Podem compartilhar encanamento (uma regra/estágio emitindo `Pendencia` carregada na `MatrizGHE`), mas são mecanismos conceitualmente separados — não unificar sem decisão própria.

**Consequência.**
- Toca, na mesma leva lógica (mas fatiável em sessões de Code): contrato/tipo de `MatrizGHE` (campo `status` + anexação de pendência à linha emitida); orquestrador (parar de zerar `linhas`; computar o tri-estado a partir das contribuições); `stage_8_consolidacao` (dedup do caso convergente preservando piso determinado + pendência anexada); propagação de `Resultado.status`; auditor; regressão. Cada mudança com teste que falhe sem ela e passe com ela (metodologia).
- Requisito de segurança (não-negociável): a pendência bloqueante que incide sobre uma linha emitida tem de ser anexável à linha. A arquitetura suporta (audit trail por `regra_id`, D-ARQ-08). Se, para uma linha específica, a anexação for inviável na implementação, aquela linha volta a ser bloqueante — o piso determinado nunca é emitido sem o teto pendente visível ao lado.
- Universalidade (D-ARQ-06): expresso em termos de contribuição-por-risco, vale para construção, química, saúde, mineração. Não é regra de sílica×PNOS.
- BLOQUEADA não é "erro" — é estado legítimo e auditável (GHE cujo único risco não determinou). PARCIAL e BLOQUEADA ambos rebaixam o global a PRELIMINAR; a distinção entre eles é informativa para a revisão de saída.
- Implementação (tipo + orquestrador + Stage 8 + status + auditor + testes) é multi-fatia, sessões de Code futuras — não fechada aqui. Esta sessão fecha a decisão de método/arquitetura (CONHECIMENTO→ARQUITETURA). Fecha DT-002Z-01.

**Base.** Sessão 003.A (05/06/2026). Resolução de DT-002Z-01. Fontes: NR-07 itens 7.5.1/7.5.5/7.6.4 (Portaria MTP 567/2022), conferidas no texto oficial do MTE (gov.br). Reforço: analogia R-PGR-04/R-PGR-05 (`[VALIDADO]`). Caso-âncora: Acab-05 Viverde (sílica×PNOS no mesmo GHE; `diagnostico_zona_cinza()` em `test_integracao_viverde.py`).

**Nota de implementação (fatia 2, sessão 003.C).** O "três sítios de construção de `MatrizGHE`" citado no planejamento (handoff/003.B) refere-se à estrutura do orquestrador ANTERIOR à fatia 2 (ramo bloqueante separado que pulava `stage_8_consolidacao`). Na fatia 2 esse ramo foi eliminado — a consolidação roda sempre, para distinguir PARCIAL (linhas presentes) de BLOQUEADA (nenhuma linha). Restam DOIS sítios de construção: `except ConflitoProtocolo` (BLOQUEADA) e o `else` (que ramifica em VÁLIDA/PARCIAL/BLOQUEADA conforme bloqueio e presença de linhas). `Resultado.status` NÃO foi tocado: `executar` já mapeava `houve_bloqueio→PRELIMINAR` e REJEITADO segue exclusivo do gate Stage 1 (cláusula 4 acima) — D-ARQ-15 íntegro. Fatia 2 = cláusulas 1, 2 e 4 parciais; a anexação pendência-à-linha (cláusula 3) é fatia 3. Commit `76d5de1`, merge `d0a68d4` (PR #56). Suíte 330→333.

**Nota de implementação (fatia 3, sessão 003.D).** Cláusula 3 materializada: pendência bloqueante com âncora de exame anexa-se à linha emitida, não fica solta no nível do GHE. Mecânica: `Pendencia.exames_alvo: tuple[str, ...]` (carimbada em `emissao.py` no caminho `Ausente`, lendo os slugs de `regra["emite"]`) + `ExameEmitido.pendencias_anexadas: list[Pendencia]` (slot na linha) + estágio puro `estagios/anexacao.py` (`anexar_pendencias`: move por interseção slug×linha; sem match volta ao nível da matriz). Anexação roda PÓS-Stage-8, no `else` do orquestrador; status tri-estado recomputado depois da anexação (não antes — uma linha pode perder bloqueante para a anexação). `houve_bloqueio` global passa a derivar de `m.status in {PARCIAL, BLOQUEADA}` (não mais de `m.pendencias`), porque pendências movidas para linhas deixariam o critério antigo cego. Requisito de segurança garantido por construção: o slot na linha torna a anexação sempre viável quando há match — piso nunca emitido sem teto visível.

Correção factual do exemplo canônico (cláusula 3 dizia "piso determinado (admissional)"): no Acab-05 real o PNOS é >100% LEO → piso **60M** (`R-RX-01-pnos-acima100`), não admissional. "Admissional/0M" vale para Acab-06/Acab-08/Est-07 (`R-RX-01-pnos-10a100`). `[DERIVADO — saída real diagnostico_zona_cinza, 003.D]`.

Evidência empírica de universalidade (D-ARQ-06): a anexação generalizou além de sílica×PNOS sem regra específica — Adm-03 (ruído sem medição → pendência de âncora `audiometria`) anexou à linha de audiometria do pacote ativcrit, comportamento idêntico fora da zona cinza da sílica. A premissa da spec de que "Adm-03 não é atingido" estava errada; a suíte pegou (o gate de estado real cobriu só a zona cinza). Os testes Adm-03 e `test_ghe_parcial_linhas_presentes_com_bloqueio` foram redirecionados de `matriz.pendencias` para `linha.pendencias_anexadas`, com asserção-espelho "não resta solto".

Recorte: o dedup convergente do Stage 8 (dois riscos determinados emitindo o mesmo exame com periodicidades distintas → escolha de piso em vez de `ConflitoProtocolo`) SAIU do escopo da fatia 3 — não tem caso-âncora vivo (a sílica bloqueada não emite linha, logo não há convergência de duas linhas). Entra na fila como item próprio; quando vier, é mudança de comportamento do `raise ConflitoProtocolo` e merece decisão própria. Commit `f25cd48`, merge `f1cb412` (PR #58). Suíte 333→339 (181→? isolado: 184→190).

**Nota de implementação (fatia 4, sessão 003.E).** Arco D-ARQ-31 fechado: auditor da invariante piso-sem-teto + regressão Viverde tri-estado, ambos como rede de teste (não custo em produção). Decisão de localização: o auditor mora na CAMADA DE TESTE (`agente_medico/tests/invariantes.py`), não em `motor/` — a invariante já é garantida POR CONSTRUÇÃO por `anexar_pendencias` (toda bloqueante com âncora-casante é anexada; não há ramo de piso-sem-teto), logo o risco real é regressão futura no código, papel de teste; um auditor em produção só adicionaria modo de falha a motor determinístico cuja invariante não pode ser violada por input. `auditar_invariante_piso_teto(resultado) -> list[ViolacaoPisoSemTeto]`: retorno ESTRUTURADO (frozen, campos só-str — ghe_id/exame/regra_origem/motivo — porque ExameEmitido é mutável e não serve a == estável), nunca bool; quando dispara, diz qual GHE e exame achatou. Critério: bloqueante COM exames_alvo SOLTA na matriz cuja âncora casa um slug emitido do mesmo GHE = violação. Sobre saída real é sempre [] (construção); o teste sintético `test_invariante_piso_teto.py` fabrica o estado de violação à mão (que o pipeline nunca produz) — sem ele o auditor jamais seria exercitado no vermelho.

Regressão Viverde tri-estado (a entrega que fecha o arco; o auditor é a rede estreita): congela a forma dos 32 GHEs pós-fatia-3. Diagnóstico real (003.E) instrumentado para imprimir status + pendencias_anexadas confirmou ponto-a-ponto: Acab-05 PARCIAL (rx 60M pnos-acima100, família sílica adm/sem/baixa/media/alta anexada); Acab-06/Acab-08/Est-07 PARCIAL (rx 0M pnos-10a100, mesma família anexada); Est-08 VÁLIDA (rx 0M pnos-ate10, anexada VAZIA). Correção factual sobre o handoff: Est-08 não é "controle sem linha rx" — emite rx pela faixa PNOS branda (pnos-ate10), mas sem sílica não ganha família anexada → VÁLIDA. A família R-RX-01-pnos-* é governada por PNOS, não por sílica; sílica só adiciona as 5 pendências por cima. Prova de que a anexação é dirigida por sílica, não por PNOS (linha rx existe nos dois estados; família anexada só onde há sílica). Asserções estruturais (linha presente + família ⊆ anexadas + não-solta + status), sem cravar periodicidade exceto Acab-05. Contagem dos 32 por invariantes derivadas (soma==32, PARCIAL≥4, VÁLIDA≥1, BLOQUEADA==0), não números cegos de GHEs não medidos. Suíte 339→347 (+8: 4 sintéticos + 4 integração); isolado 190→198. mypy --strict limpo (15 arquivos: 14 motor + invariantes.py). Commit 6f80f46, merge fa11ba3 (PR #60, "Create a merge commit").

---

## D-ARQ-32 — Handoff de sessão é a 4ª entrega do ritual de encerramento

**Contexto.** O encerramento de sessão já produzia três entregas (update dos docs vivos; prompt de gravação p/ o Code quando há doc; as 3 perguntas de fechamento — entra em DECISOES/PROTOCOLO/HISTORICO?). Faltava formalizar a quarta, que sustenta a continuidade entre chats: o handoff colado na abertura seguinte.

**Decisão.** Todo fechamento de sessão produz quatro entregas: (1) update dos docs vivos; (2) prompt de gravação p/ o Code quando houver doc a gravar; (3) as 3 perguntas de fechamento; (4) handoff atualizado p/ a próxima abertura.

**Natureza do handoff.** É DERIVADO dos docs vivos + git, reescrito do zero a cada sessão, nunca versionado, nunca crava estado (SHA, contagem de testes, número de sessão — isso é do /kickoff e do briefing). Orienta, não é estado. Se divergir do git, o git vence.

**Fronteira.** D-ARQ-26 (/kickoff) e D-ARQ-30 (briefing) cobrem ESTADO na abertura; D-ARQ-32 cobre ORIENTAÇÃO no encerramento.

**Garantia de execução — emenda a D-ARQ-26 considerada e descartada.** Cogitou-se emendar o SKILL.md do /kickoff com um lembrete das 4 entregas, para a regra ser recarregada por toda sessão (inclusive IMPLEMENTAÇÃO pura, que pode não reler este DECISOES). Descartada: (a) o kickoff é coletor de abertura read-only/não-decisório — instruir encerramento ali contraria seu desenho e adiciona risco ao gate de abertura; (b) o lembrete chegaria na abertura, distante do momento de uso (o encerramento), e sairia do contexto antes de ser útil. Veículo de garantia adotado: Diovanni solicita o handoff ao Arquiteto no encerramento de cada chat. Gatilho no momento certo, sem tocar engrenagem. D-ARQ-26 permanece intocado.

`[META — decisão de processo. Não toca motor nem protocolo clínico.]`

---

## D-ARQ-33 — Lado-engenheiro é motor irmão de resolução de composição química; conduta permanece no lado-médico

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA). Implementação multi-fatia futura. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** O reenquadramento da 003.F estabeleceu o par ENGENHEIRO/HIGIENISTA → MÉDICO: o engenheiro produz a base do PGR (inventário de risco por GHE, a partir da FDS), o médico produz a base do PCMSO. `tipos.PGR` (D-ARQ-25) é a mesa entre os dois. Hoje o lado-engenheiro só existe no legado Streamlit (`modulo_engenharia.py`), acoplando extração + decisão + UI (viola D-ARQ-09). A frente FDS construiu o estudo (003.G) sobre a fundação normativa verificada na 003.F. A pergunta de arquitetura: o lado-engenheiro é camada de extração (sub-componente do D-ARQ-25) ou motor irmão (segundo componente determinístico)?

**Decisão.** Motor irmão — mas **estreitado a resolução de composição química**, não a um segundo motor de inventário completo. A decisão tem cinco partes:

1. **Topologia.** A fronteira `tipos.PGR` separa dois OFÍCIOS (engenheiro/médico), não LLM/determinístico. A fronteira LLM↔determinístico existe *dentro* de cada lado:

```
   FDS → [extração LLM: resolvedor CAS→ficha + descoberta + revisão humana]   (D-ARQ-25, D-ARQ-14)
       → fichas resolvidas
       → [MOTOR IRMÃO: resolução de composição química, determinístico]        (D-ARQ-09)
       → tipos.PGR (A MESA)                                                     (D-ARQ-25)
       → [MOTOR MÉDICO: PGR → matriz]                                           (existente)
       → Resultado (PCMSO)
```

   Refina D-ARQ-25: a extração vira sub-camada do lado-engenheiro; o motor irmão fica entre ela e `tipos.PGR`. A descoberta CAS via LLM permanece a montante do motor irmão (preserva D-ARQ-09 nos dois lados).

2. **Escopo estreito.** O motor irmão vai de *fichas resolvidas → composição química estruturada em `ProdutoQuimico`*. NÃO reconstrói o esqueleto do PGR (GHEs/cargos/riscos físicos vêm do PGR do engenheiro); enriquece os `ProdutoQuimico` específicos cujos campos já existem no tipo (`GHEPGR.produtos_quimicos`, `ProdutoQuimico.fds`, `Componente.cas` — D-ARQ-25 Parte C). O lado-engenheiro **não decide conduta**: exame, periodicidade e momentos são todos do lado-médico (R-FDS-*, R-BIO-*, R-PKG-*). Duplicar regra médica no lado-engenheiro é o erro que esta cláusula proíbe.

3. **Gate de admissão + pendência tipada.** O que torna isto motor (e não extração) é a topologia pendência-vs-chute (D-ARQ-08/09/13):
   - CAS que falha o dígito verificador → `Pendencia`, nunca inventa agente. `[DERIVADO — algoritmo check-digit do CAS Registry]`. (Verificado: os fantasmas `022-00-9`/`014-00-0` da 003.F falham o dígito.)
   - "Hidrocarbonetos aromáticos" sem CAS resolvível (R-FDS-04) → `Pendencia`.
   - Concentração em faixa que cruza um limiar de materialidade → `Ausente`/`Pendencia` bloqueante (D-ARQ-13), não chute para um dos lados.

4. **Saída é candidata, não classificação final autônoma.** Por NR-9 e responsabilidade técnica (ART), a composição classificada pelo motor irmão é candidata; a admissão final é ato do responsável técnico que assina o PGR — ancora no gate existente R-PGR-01, **não** numa camada de "revisão de saída" nova. `[DERIVADO — R-PGR-01 (assinatura por engenheiro de segurança); NR-9 (classificação de risco é ato técnico do empregador)]`. Espelha, sem replicar, o modelo de revisão de saída do lado-médico (D-ARQ-22).

5. **Materialidade é predicado, não atributo armazenado (resolução do cutoff — caminho C).** O limiar `5%` (R-FDS-03) é **constante de protocolo**, `[VALIDADO — conduta Carolini, GHS/ABNT 14725]`, sem âncora NR. A materialidade de um componente é **predicado derivado** computado em cada lado sobre `concentração ∨ (qualquer bypass do cutoff)` — nunca um bool gravado na ficha. Os bypasses do cutoff são uma **lista** de dados, não um único critério:
   - carcinógeno IARC — `[VALIDADO — R-FDS-03/04]`; a cláusula "independe de concentração / >0%" é `[INTERPRETADO — boa prática INCA/Anexo V]`, não literal na norma;
   - sensibilizante respiratório/dérmico — `[INTERPRETADO — generalização]` (ex.: isocianatos, glutaraldeído, relevantes <5%);
   - demais perigos da frase-H que a conduta justificar — append-only.
   `agentes.yaml` ganha as flags de perigo correspondentes (D-ARQ-12). A mesa transporta `concentração` + flags; a materialidade é derivada onde consumida. **(C) é carrega-tudo-e-marca, nunca filtro de entrada:** descartar <5% não-bypass na admissão suprimiria componentes que o lado-médico filtraria por outra regra (ototóxico, órgão-alvo) — subdimensionamento silencioso (D-ARQ-22) e a mesma supressão que D-ARQ-31 matou intra-GHE. A partição limiar=dado / materialidade=predicado tri-estado / dois consumidores é `[INTERPRETADO]`, por analogia a 7.5.12 b e ao padrão NA-NR9 do contrato da mesa.

**Consequência.**
- Não infla escopo: encaixa em tipos que já existem, reusa a infra de `Pendencia` (D-ARQ-08/14) e regras-como-dado (D-ARQ-07). "Motor irmão" = segundo consumidor determinístico da mesma infra, não código duplicado.
- O contrato da mesa (ficha de agente químico) é extensão de `agentes.yaml`, não ID de regra novo: `cas` validado, `tipo_ibe ∈ {EE,SC}`, `ibmp`/valor-ref, `momento_coleta`, flags de perigo, `orgao_alvo`. Procedências: `tipo_ibe`/`ibmp`/`momento_coleta` `[DERIVADO — NR-07 Anexo I, 567/2022]`; o vocabulário dos códigos de `momento_coleta` (FJ/FS/AJ…) `[INCERTO — glossário literal a confirmar no PDF oficial MTE]`.
- A regra que consome `tipo_ibe` para fixar momentos do biomonitoramento é a sucessora de R-BIO-02 (DT-FDS-01, ABERTA, sessão própria, exige Quadro 2 inteiro, lado-médico). A ficha carrega o dado; a regra que o lê é fora desta frente. O dado precede a regra.
- Periodicidade NÃO entra na ficha: "biomonitoramento = 6M" é R-BIO-01 (universal); a janela ±45d (7.5.13) é tolerância de agendamento (D-ARQ-11). Ambas fora da ficha e do motor.
- Sinergia entre agentes está fora de escopo de regra (o Anexo I opera por agente isolado) — declarado, não omisso; `orgao_alvo` é dado de apoio à decisão (visão por sistema na revisão de saída), nunca disparador de exame/periodicidade.
- Gap de tipo a verificar na implementação (gate de estado real, não afirmado aqui): a materialidade-predicado exige `Componente.concentracao`; D-ARQ-25 Parte C lista `Componente.cas`, não a concentração — candidato a extensão futura na categoria de `pct_quartzo`/`fracao`. Conferir no git antes de qualquer prompt cirúrgico.

**Pré-condição de validação (D-ARQ-06).** Antes de selar, rodar a decisão contra um caso não-construção. Já exercitado parcialmente em 003.G: caso-saúde (óxido de etileno = carcinógeno IARC 1 → coberto pelo bypass-carcinógeno; glutaraldeído/isocianato sensibilizante <5% → **revelou** que materialidade não é binária `concentração|carcinógeno`, forçando a lista de bypasses da cláusula 5). O passo é necessário, não cerimônia: foi ele que achou o furo. Caso-químico (matéria-prima) a confirmar na sessão de implementação. `[INCERTO — confirmar no PDF oficial MTE se TDI/isocianatos têm IBE/EE próprio no Quadro 1; exemplo visto só em fonte secundária]`.

**Fronteira com decisões existentes (não confundir):**
- **D-ARQ-25** — não revoga. Refina: a fronteira `tipos.PGR` é entre ofícios; a extração LLM vira sub-camada do lado-engenheiro, a montante do motor irmão.
- **D-ARQ-09** — preservada nos dois lados: toda LLM (descoberta CAS, extração) fica a montante; o motor irmão é função pura.
- **D-ARQ-08/13/14** — reusados: ambiguidade de composição → `Pendencia` tipada/bloqueante, nunca chute.
- **D-ARQ-22** — a cláusula 4 (candidato + admissão R-PGR-01) é o espelho-engenheiro do modelo de revisão de saída; não replica o aparato, ancora no gate existente.
- **D-ARQ-31** — a cláusula 5 (não-filtro-de-entrada) é o mesmo princípio anti-supressão, aplicado à admissão de componente em vez do bloqueio intra-GHE.
- **R-FDS-03/04, R-BIO-01/02/03, R-PKG-BZ/SOLD** — IDs intactas, semântica intacta. Esta decisão não cria nem altera regra clínica; cria contrato de dado e motor.

**Base.** Sessão 003.G (08/06/2026), estudo da frente FDS. Fundação: conferência do Anexo I (Portaria MTP 567/2022) contra texto oficial MTE (003.F). Reforço: NR-9 (classificação de risco é ato do empregador), NR-07 7.5.5. Caso-âncora de método: FDS de pintura da 003.F (65 agentes; auto-descoberta poderosa-e-perigosa). Decisão de arquitetura — sem código. Resolve a tensão "camada vs. motor irmão" do estudo FDS.

**Changelog.**
- **003.H** — Gap de tipo da cláusula 5 conferido no git (gate de estado real): `Componente.concentracao` JÁ EXISTE em `tipos.py:33`, porém como `Optional[float]` escalar. O gap documentado (campo ausente) está fechado; abre-se o gap de FORMA — escalar é um ponto, não enxerga faixa, e a cláusula 3 exige "concentração em faixa que cruza um limiar → Ausente/Pendencia". Sucedido por **D-ARQ-34** (concentração vira faixa; materialidade vira predicado tri-estado). Mesma ID, sem alteração de conteúdo de D-ARQ-33.

## D-ARQ-34 — Materialidade do lado-engenheiro: concentração é faixa, materialidade é predicado tri-estado compartilhado

**Status:** DECISÃO DE ARQUITETURA. Sem código nesta sessão. Implementação (extensão de tipo + predicado + flags + testes) é sessão futura. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-33 cláusula 5 fechou a direção (materialidade = predicado tri-estado derivado, bypasses = lista, caminho C) e nomeou dois consumidores: médico (R-FDS-03, escrito) e engenheiro (motor irmão, declarado e não escrito). Esta decisão escreve o consumidor-engenheiro. O gap de tipo que D-ARQ-33 mandava conferir está fechado quanto à EXISTÊNCIA (`Componente.concentracao` presente, `tipos.py:33`) e ABERTO quanto à FORMA: o campo é `Optional[float]` escalar, e a cláusula 3 de D-ARQ-33 exige que concentração em faixa que cruza um limiar vire Ausente/Pendencia — escalar é ponto, não faixa. FDS declara composição em faixa (ABNT NBR 14725 seção 3). Colapsar a faixa num escalar a montante decide a materialidade fora do motor determinístico, em silêncio — o chute que a cláusula 3 proíbe. Gêmeo estrutural de DT-002V-01 (`Quantificacao.valor: float` que não discrimina a estatística).

**Decisão — quatro partes.**

*Parte 1 — concentração é faixa, não escalar.* `Componente.concentracao` passa de `Optional[float]` a faixa `(min, max)`, espelhando valor+qualificador de `Quantificacao` e o sub-objeto frozen de `CenarioExposicao` (002.Q). Sentinelas: sub-objeto inteiro `None` → não extraída → AUSENTE; `min = None` → piso desconhecido lido como 0; `max = None` → teto desconhecido lido como +∞. Assim "< 5%" = `(None, 5.0)`; "> 1%" = `(1.0, None)`; "1–5%" = `(1.0, 5.0)`; ponto "2%" = `(2.0, 2.0)`. Forma exata do tipo (dataclass `FaixaConcentracao` frozen vs. par de campos) é decisão da sessão de implementação — recomendado sub-objeto frozen (coesão, mesma razão de `CenarioExposicao`); o que se crava aqui é a semântica min/max + sentinelas.

*Parte 2 — predicado de materialidade tri-estado `{MATERIAL, NÃO-MATERIAL, AUSENTE}`* (espelha D-ARQ-13). **Pré-condição (não é ramo):** materialidade só é avaliada em componente que passou o gate de admissão de D-ARQ-33 cláusula 3 (CAS válido pelo dígito verificador). CAS inválido → Pendencia no gate, componente não chega à materialidade. Ordem de avaliação:
0. componente admitido (CAS válido) mas slug NÃO resolvido no vocabulário (D-ARQ-14, agente fora de `agentes.yaml`) → **AUSENTE**/Pendencia BLOQUEANTE. Sem slug não há flags; não decidir NÃO-MATERIAL por concentração — carcinógeno desconhecido <5% viraria supressão silenciosa (D-ARQ-22).
1. qualquer bypass `True` → **MATERIAL** (independe de concentração, inclusive `concentracao=None`).
2. (sem bypass) concentração ausente → **AUSENTE**/Pendencia.
3. (sem bypass, faixa presente) faixa cruza o cutoff `min ≤ 5 < max` (com `min→0`, `max→+∞` para `None`) → **AUSENTE**/Pendencia (straddle, cláusula 3 de D-ARQ-33).
4. (sem bypass, faixa presente) `min > 5` → **MATERIAL**.
5. (sem bypass, faixa presente) `max ≤ 5` → **NÃO-MATERIAL**.
Exaustivo e exclusivo sobre faixa presente. Borda: R-FDS-03 diz "> 5%", logo 5,0 exato é não-material (`min>5` estrito; `max≤5` inclusivo) — `[INTERPRETADO]` enquanto a unidade do cutoff não for confirmada (DT-FDS-02). Faixa com piso exatamente 5 ("5–10%") cai em straddle por construção → Pendencia, RT resolve na admissão; reduzir esse ruído ajustando a borda seria chute. Faixa inválida (`min > max`) é erro de integridade → Stage 3 (D-ARQ-17), não materialidade.

*Parte 3 — bypasses são lista de flags em `agentes.yaml`, append-only* (D-ARQ-12). `is_carcinogeno_iarc: bool` JÁ EXISTE — bypass `[VALIDADO — R-FDS-03/04]` na existência; "independe de concentração / >0%" é `[INTERPRETADO — boa prática INCA/Anexo V]`. `is_sensibilizante: bool` é flag NOVA (respiratório/dérmico), `[INTERPRETADO — generalização]` (isocianatos, glutaraldeído <5% — caso-saúde de 003.G). Demais perigos da frase-H entram como flag por classe quando a conduta os justificar, não a tabela GHS inteira. A POPULAÇÃO de `is_sensibilizante` (quais agentes recebem `True`) é tarefa de dado com fonte marcada, não desta decisão de arquitetura.

*Parte 4 — materialidade é predicado computado em cada lado, nunca bool armazenado; flags chegam pela ficha normalizada.* O cálculo das Partes 2–3 é função pura `(faixa, flags) → {MATERIAL, NÃO-MATERIAL, AUSENTE}`, chamada independentemente pelo lado-médico (R-FDS-03) e pelo lado-engenheiro (motor irmão) — não um valor compartilhado na mesa. As flags chegam ao predicado pela FICHA JÁ NORMALIZADA (a extração resolveu CAS→slug→flags, D-ARQ-25 Parte B), não por consulta do motor irmão a `agentes.yaml` por CAS — o motor irmão é puro sobre o que a ficha traz (D-ARQ-09). NÃO-MATERIAL não descarta o componente: fica na mesa marcado, porque o lado-médico pode filtrá-lo por outra regra (ototóxico, órgão-alvo) — carrega-tudo-e-marca (cláusula 5 de D-ARQ-33; anti-supressão de D-ARQ-31). AUSENTE: no motor irmão → Pendencia (gate); no motor médico → pendência bloqueante (D-ARQ-13).

**Consequência.**
- Não cria nem altera regra clínica (R-* intactas; R-FDS-03/04 semântica preservada, segue D-ARQ-33). Cria contrato de dado (faixa + flags) e contrato de motor (predicado de materialidade).
- Migração de tipo `Optional[float]` → faixa toca quem lê `Componente.concentracao` hoje — GATE DE ESTADO REAL OBRIGATÓRIO na sessão de implementação (grep por `.concentracao` no motor) antes de qualquer prompt cirúrgico; não afirmado aqui que ninguém lê.
- Cobertura de teste (implementação): predicado nos ramos 0–5 + straddle + bypass-com-`None` + faixas semi-abertas (`< 5%`, `> 1%`) + borda 5,0; cada teste falha sem a regra e passa com ela.

**Fronteiras (não confundir):**
- **D-ARQ-33** — não revoga; escreve o consumidor-engenheiro da cláusula 5 e resolve a forma do gap de tipo que ela deixou aberto.
- **D-ARQ-13** — o tri-estado de materialidade espelha True/False/Ausente; AUSENTE reusa o trilho pendência-bloqueante.
- **DT-002V-01** — mesma classe (escalar que perde informação do gate); D-ARQ-34 resolve para concentração, NÃO fecha DT-002V-01 (aquela é a estatística do CLSC, lado físico). Gêmeas, não a mesma.
- **DT-FDS-01 (trilho)** — materialidade usa concentração + flags de perigo; NÃO toca `tipo_ibe`. `tipo_ibe {EE,SC}` é eixo Quadro 1/Quadro 2 = comportamento temporal do biomonitoramento, governado pela R-BIO-02-sucessora (DT-FDS-01, sessão própria, lado-médico). Esta decisão para na materialidade; não deriva momentos.

**Base.** Sessão 003.H (09/06/2026), protocolo-engenheiro pós-D-ARQ-33. Três passadas adversariais: (1ª) forma faixa sobre escalar; (2ª) árvore tri-estado + ramo de vocabulário ausente; (3ª) pré-condição gate-precede-materialidade + ramo 0 reescopado (CAS inválido é gate, não ramo) + pendência bloqueante. Caso-âncora: composição em faixa de FDS (ABNT NBR 14725); furo das faixas semi-abertas (passada 1) e do carcinógeno-desconhecido-<5% (passadas 2–3). Decisão de arquitetura — sem código.

**Aplicação na sessão 003.I (10/06/2026) — fatia 1 (Parte 1, contrato de dado).** Forma do tipo decidida e implementada: sub-objeto `FaixaConcentracao` frozen (não par de campos soltos em `Componente`), campos `minimo`/`maximo: Optional[float]` (não `min`/`max` — sombreiam builtin sob mypy strict). Sentinelas da Parte 1 encapsuladas como métodos no próprio tipo (`piso_efetivo()` → `minimo if not None else 0.0`; `teto_efetivo()` → `maximo if not None else +inf`), compartilhadas pelos dois consumidores (médico/engenheiro) para não divergirem — mesma razão do predicado-compartilhado da Parte 4. SEM `__post_init__`: `minimo>maximo` é erro de integridade do Stage 3 (D-ARQ-17), não rejeição na construção; o tipo é portador, validar aqui mataria o trilho de Pendencia. Migração `Componente.concentracao: Optional[float]` → `Optional[FaixaConcentracao] = None`; o default `None` casa a sentinela "não extraída → AUSENTE" (ramo 2 do predicado, fatia 2) e preserva a única fixture que constrói `Componente` (`test_stage_3:47`, nomeada). Commit 591a04d, merge 3240e10 (PR #65, "Create a merge commit"). 6 testes novos (`test_faixa_concentracao.py`): faixa fechada / semi-aberta inferior / semi-aberta superior / ponto + default-None + aceita-faixa; cada um falha sem a fatia. Partes 2–4 (predicado, flags, gate-CAS) NÃO tocadas — fatia futura.

**Aplicação na sessão 003.J (11/06/2026) — fatia 2 (Partes 2–4, predicado isolado).** Predicado de materialidade materializado isolado, NÃO plugado em consumidor (R-FDS-03 e motor irmão são fatias futuras; "o dado precede a regra"). `Componente` ganha três campos: `agente: Optional[str] = None` — discriminante do ramo 0 (CAS válido mas slug não resolvido no vocabulário, D-ARQ-14 → AUSENTE); escolhido sobre `resolvido: bool` por NÃO armazenar derivado (mesma disciplina anti-bool-armazenado da Parte 4) e por espelhar `RiscoPGR.agente`/`Risco.agente`. `is_carcinogeno_iarc: bool = False` e `is_sensibilizante: bool = False` (nova) — flags soltas espelhando o padrão `Risco.is_ototoxico`, NÃO agregado `FlagsPerigo`: gate de estado real (grep repo inteiro) confirmou que o motor não tem container de flags e o gatilho de promoção (D-ARQ-16, "dois casos provam o padrão") não disparou. Predicado puro `materialidade(componente) -> Materialidade {MATERIAL, NAO_MATERIAL, AUSENTE}` em módulo NEUTRO novo `motor/materialidade.py` (não no motor médico nem no irmão inexistente, pois é compartilhado pelos dois — Parte 4); ramos 0–5, consome `piso_efetivo()/teto_efetivo()` da fatia 1; retorna o enum e NÃO toca `ctx.pendencias` (a tradução AUSENTE→Pendencia é do consumidor — mais puro que os primitivos tri-estado de D-ARQ-13 de propósito, por servir dois trilhos de pendência distintos). Gate-CAS (D-ARQ-33 cl.3) CONFIRMADO pré-condição a montante, NÃO ramo: `Componente.cas: str` é obrigatório no tipo, validado pelo dígito verificador no motor irmão futuro — o componente que chega à materialidade já passou; a ressalva herdada do handoff (gate-CAS como pré-requisito da fatia) estava superdimensionada. Borda 5,0 exata = NÃO-MATERIAL (`min>5` estrito, `max≤5` inclusivo), `[INTERPRETADO — DT-FDS-02]` até a unidade do cutoff ser confirmada. `agentes.yaml` INTOCADO — as flags do componente chegam pela ficha normalizada (D-ARQ-25 Parte B, extração futura), não por leitura de `agentes.yaml` por CAS (predicado puro sobre o que o `Componente` traz). 11 testes sintéticos em `test_materialidade.py` (um por ramo 0–5 + straddle + bypass-com-`concentracao=None` + semi-abertas `<5%`/`>1%` + borda 5,0 exata + piso-5-faixa-5–10-straddle); cada um falha sem o predicado. mypy --strict limpo (`materialidade.py` + `tipos.py`). Commit d0e8417, merge dd9c200 (PR #67, "Create a merge commit"). Suíte 353→364 / isolado 204→215. Restante de D-ARQ-34: hidratação das flags a partir da ficha + plug em R-FDS-03 + integração com o motor irmão = fatias futuras.

**Refinamento de método do gate de estado real (003.I).** Para fatia que migra TIPO COMPARTILHADO, o grep do gate varre o REPO INTEIRO, não só `agente_medico/`: `tipos.py` é importável de `modules/`/`scripts/`/`tests/`, mypy strict não cobre o legado, logo construção com tipo errado entraria em silêncio (classe D-ARQ-22). A Consequência de D-ARQ-34 dizia "grep `.concentracao` no motor" — insuficiente para tipo compartilhado. Varrido o repo nesta sessão: único hit fora de `agente_medico/` era `modulo_pcmso.py:989` (`fispq.get("componentes")`, acesso a dict do legado, falso positivo case-insensitive do Select-String) — não importa `tipos.Componente`. Blast radius nulo afirmado sobre o repo todo, não meia varredura.

## D-ARQ-35 — Risco químico de composição é a 4ª fonte de risco, promovida no Stage 2 médico; o motor irmão não a produz

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA). Sem código nesta sessão. Implementação (promoção em Stage 2 + regras químicas + cobertura) é multi-fatia futura. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-02 modela três fontes de risco com status equivalente — explícito (inventário), implícito-por-cargo (R-GHE-02/05), inferido-por-sinal (EPI, R-PGR-03) — todas merged antes das regras de exame, todas no lado-médico, cada uma marcada por `regra_id`. Composição química de FDS não é nenhuma das três: é buraco na taxonomia de D-ARQ-02. D-ARQ-33/34 deram ao lado-engenheiro a resolução de composição (`ProdutoQuimico` enriquecido + predicado de materialidade), mas o predicado de materialidade (003.J, `motor/materialidade.py`) está **órfão de consumidor de produção desde a 003.J** — nenhuma regra de conduta lê o risco químico que a composição materializa. O elo faltante é a promoção `produto químico enriquecido → Risco` que o motor médico processa pelo maquinário existente (Stage 2→4→5, dedup, anexação). Duas perguntas de arquitetura, acopladas: **onde** mora a promoção (engenheiro ou médico) e **o que** é a coisa promovida (`Risco` sintetizado ou caminho paralelo).

**Decisão — três partes.**

*Parte 1 — ONDE: Stage 2 do motor médico, espelhando D-ARQ-23.* A promoção lê `GHEPGR.produtos_quimicos` (enriquecido pelo motor irmão na mesa, D-ARQ-33 cl.2) e infere o risco químico implícito — mecanicamente idêntico ao que D-ARQ-23 desenha para `operação confirmada → risco implícito` (solda → fumos). **A cl.2 de D-ARQ-33 fica intocada:** o motor irmão produz `ProdutoQuimico` enriquecido, tipo que ele já escreve na mesa, e **não** emite `RiscoPGR`. Promover seria reconstruir inventário — exatamente o que as três passadas da 003.G estreitaram para fora do irmão. A síntese do `Risco` mora no lado que decide conduta, não no que resolve composição. `[DERIVADO — analogia D-ARQ-23; D-ARQ-33 cl.2 literal]`.

*Parte 2 — O QUE: promoção a `Risco` (4ª fonte de D-ARQ-02), não caminho químico paralelo.* O risco químico de composição entra como **quarta fonte** na família de D-ARQ-02, com status equivalente às outras três, merged antes das regras de exame, marcado por `regra_id` (audit trail: "risco químico X derivado do componente Y do produto Z, via materialidade MATERIAL"). Consome o maquinário existente — dedup por R-GHE-03, convergência por D-ARQ-16, anexação pendência-à-linha por D-ARQ-31 — sem reconstruir nenhum deles. Conduta química vira "mais regras" em `regras.yaml` (lado-químico hoje vazio), igual ao físico. `[DERIVADO — extensão D-ARQ-02]`.

*Parte 3 — materialidade anda junto com a promoção, não a porteia.* **Todo componente que passou o gate-CAS e tem slug resolvido promove a `Risco`**, carregando materialidade (`{MATERIAL, NÃO-MATERIAL, AUSENTE}`, D-ARQ-34) e flags como **dado** do risco — não é MATERIAL que decide se o risco existe. As regras de conduta disparam condicionalmente sobre materialidade/flags/anexo do risco promovido. Razão (não-negociável): se só MATERIAL promovesse, um componente NÃO-MATERIAL-mas-ototóxico (ou órgão-alvo) sumiria antes de o lado-médico poder filtrá-lo por outra regra — viola D-ARQ-34 Parte 4 ("NÃO-MATERIAL não descarta o componente") e reintroduz o subdimensionamento silencioso que D-ARQ-33 cl.5 e D-ARQ-31 mataram. Materialidade é atributo do risco promovido, não porteira da sua existência. Flags chegam por **cópia-pra-frente** do `Componente` resolvido (003.J: `is_carcinogeno_iarc`, `is_sensibilizante`) — fonte única, sem o motor médico re-consultar `agentes.yaml` por CAS. `[INTERPRETADO — prioridade na revisão de saída]` (a forma "promove-tudo-com-slug, materialidade como dado" é decisão de arquitetura, sem âncora normativa direta; análoga a 7.5.5 e ao anti-supressão de D-ARQ-31).

**Consequência.**
- Estende D-ARQ-02 sem revogá-lo: a 4ª fonte é cidadã de primeira classe igual às três, com a mesma disciplina de marca por `regra_id`. Risco químico **derivado** e marcado — não contrabandeado no inventário declarado (ver fronteira R-GHE-04).
- Motor irmão segue genuinamente estreito (D-ARQ-33 cl.2 literal): escreve `ProdutoQuimico`, não `Risco`.
- Motor médico permanece puro (D-ARQ-09): recebe o produto enriquecido na mesa e promove deterministicamente, sem LLM, sem disco.
- Dá consumidor de produção ao predicado de materialidade, órfão desde a 003.J.
- Universal (D-ARQ-06): "componente com slug → risco químico promovido" serve a construção (solvente de tinta), química (matéria-prima), saúde (óxido de etileno, glutaraldeído) — expresso em termos de componente, não de setor.
- **Furo de flags a sinalizar (decisão de fatia, não desta decisão):** o `Componente` carrega só `is_carcinogeno_iarc` + `is_sensibilizante` (003.J) — **não** `is_ototoxico` nem os demais flags físico-conduta. Um solvente ototóxico de FDS (ex.: tolueno) promovido por cópia-pra-frente perde o gatilho de R-AUD-01. Saída na sessão de implementação: ou o conjunto de flags de `Componente` cresce, ou a promoção faz re-hidratação **determinística por slug** de `agentes.yaml` para os flags que a ficha não carrega (re-hidratação por-slug ≠ conflito-de-fonte: é flag ausente na ficha, não flag divergente). Forma decide-se na fatia, com gate de estado real.
- Gate de estado real obrigatório antes de qualquer prompt cirúrgico: grep do Stage 2 médico (`stage_2_riscos`, merge de fontes de risco) e de quem constrói `Risco` a partir de fonte não-inventário, para mapear o ponto de inserção da 4ª fonte. Não afirmado aqui que o ponto está livre.

**Fronteiras (não confundir):**
- **D-ARQ-02** — estende (4ª fonte de risco). Não altera as três existentes nem o mecanismo de merge.
- **D-ARQ-23** — espelha o mecanismo: ambos são `dado-da-mesa → risco implícito inferido em Stage 2 médico` (operação→fumos lá; produto→risco químico aqui). Não unifica os dois — vocabulários e gatilhos distintos; compartilham só o padrão de inferência. D-ARQ-23 segue PROPOSTA e independente.
- **D-ARQ-33** — cl.2 **intocada**: o motor irmão não passa a emitir `Risco`. Esta decisão escreve o consumidor médico do que o irmão produz, não amplia o irmão. Resolve a tensão interna de D-ARQ-33 (Contexto "engenheiro deriva risco da FDS" vs. cl.2 "irmão só enriquece `ProdutoQuimico`") a favor do literal da cl.2: a derivação químico→risco-para-conduta mora no médico.
- **D-ARQ-34** — consome o predicado de materialidade como **atributo** do risco promovido (Parte 3), não como filtro de promoção. Não toca a forma do predicado nem dos tipos da 003.I/003.J.
- **D-ARQ-09** — preservada nos dois lados: química (CAS→slug→flags) fica a montante via extração/irmão; a promoção é função pura sobre a mesa.
- **D-ARQ-16 / R-GHE-03 / D-ARQ-31** — reusados sem alteração: o risco químico promovido converge/deduplica e anexa pendência-à-linha pelo mesmo trilho do risco físico.
- **R-GHE-04** — não violada. R-GHE-04 manda o médico respeitar o inventário **recebido** sem reinterpretar; o risco químico é **sintetizado** (derivado, marcado `regra_id`), classe que D-ARQ-02 já legitima ao lado do implícito-por-cargo e do inferido-por-EPI. Promover no médico-side marca-o como derivado; promover no engenheiro-side e injetá-lo em `GHEPGR.riscos` o lavaria como declarado — é isso que esta decisão evita.
- **R-FDS-03/04, R-BIO-*, R-PKG-*** — IDs intactas, semântica intacta. Esta decisão não cria nem altera regra clínica; cria mecanismo de promoção (4ª fonte) e abre espaço para as regras químicas de conduta, que são trabalho de sessão própria (lado-médico, sobre o eixo de DT-FDS-01).

**Base.** Sessão 003.O. Estende D-ARQ-02; espelha D-ARQ-23; resolve a tensão interna de D-ARQ-33 a favor da cl.2 literal; dá consumidor ao predicado de materialidade de D-ARQ-34/003.J. Duas passadas adversariais nesta sessão: (1ª) médico-side sub-justificado, virei para engenheiro-side por um seam de fonte-de-flag; (2ª) o seam era fantasma (cópia-pra-frente, não re-hidratação) — engenheiro-side cai por reconstruir inventário (cl.2 literal) e por R-GHE-04 lavar risco derivado como declarado; converge em médico-side, 4ª fonte. Decisão de arquitetura — sem código. Caso-âncora de método: solvente de FDS (acetona/acetato 003.N, tolueno-ototóxico hipotético) cujo risco químico hoje não tem como chegar à conduta.

**Aplicação na sessão 003.P (14/06/2026) — fatia 1 (promoção Componente→Risco, contrato de risco).** Fase C adicionada a `stage_2_riscos` (`estagios/riscos.py`): por componente de `produto.fds.composicao`, promove a `Risco(fonte="quimico_composicao")` — 4ª fonte de D-ARQ-02 materializada no Stage 2 médico. `Risco` estendido em `tipos.py` com `materialidade: Optional[Materialidade] = None`, `is_carcinogeno_iarc`/`is_sensibilizante` (flags soltas, sem agregado — padrão `Risco.is_ototoxico` 002.H; gatilho de promoção D-ARQ-16 não disparou). Enum `Materialidade` movido de `materialidade.py` para `tipos.py` (quebra de ciclo de import; refactor puro). **Sem consumidor** (`regras.yaml`/emissão intocados — o Risco promovido não dispara exame ainda; isola como 003.J isolou o predicado). **Sem dedup de risco** (D-ARQ-16 literal: convergência resolvida no Stage 8, nunca por fusão no Stage 2 — fundir destruiria o audit trail por `fonte`). Três caminhos de promoção: ramo 0 (`agente=None`, sem slug — `Risco.agente: str` rejeita `None`) → não-promove + `Pendencia(tipo="materialidade_ausente", bloqueante=True)`; ramos 2/3 (slug presente, materialidade AUSENTE por concentração-ausente/straddle) → promove com `materialidade=AUSENTE` **e** pendência bloqueante; ramos 1/4/5 (MATERIAL/NÃO-MATERIAL) → promove sem pendência. Origem de flag forçada pela forma dos tipos: `is_ototoxico`/`anexo_nr07` re-hidratados de agentes.yaml por-slug (idêntico Fases A/B — o "furo de flags" que D-ARQ-35 sinalizou como decisão de fatia não exigia decisão: o padrão vivo das Fases A/B já lê `is_ototoxico` do yaml por slug); `is_carcinogeno_iarc`/`is_sensibilizante`/`materialidade` por cópia-pra-frente do Componente (cobre CAS-oculto de DT-003M-01). Marcas: Fase C [DERIVADO — molde Fase A/B de `riscos.py`; D-ARQ-12; D-ARQ-35 Parte 1/3]; três-caminhos [DERIVADO — D-ARQ-34 Parte 4; ramos de `materialidade.py`]; premissa gate-CAS-inexistente nesta fatia [INTERPRETADO — pré-condição a montante, motor irmão inexistente]. Commit `cddf092`, PR a abrir ("Create a merge commit"). Suíte 222→229 isolado; mypy --strict limpo (16 arquivos). DH-003P-01 aberta.

**Aplicação na sessão 003.Q (15/06/2026) — fatia 2 (primeira regra química consumindo a 4ª fonte).** R-PKG-BZ (pacote benzeno) adicionada a `regras.yaml` como a PRIMEIRA regra de conduta disparada por agente químico — lado-químico de `regras.yaml` saiu de 0 para 1 regra disparando por agente químico. Primitivo `benzeno` (bi-estado, `any(r.agente == "benzeno")`, nunca Ausente) consome o `Risco(fonte="quimico_composicao")` que a Fase C (003.P) promove, SEM filtrar fonte: dispara igual por risco explícito (inventário) ou promovido (composição-FDS) — coerente com D-ARQ-02 (fontes têm status equivalente, merged antes das regras) e com R-FDS-03/04 (benzeno via FDS, mesmo <5%, mesmo via CAS de aromáticos genéricos → pacote, carcinógeno independe de concentração). Agnóstico também à materialidade: a regra dispara por presença de slug, não pela materialidade do risco promovido — materialidade fica como dado do risco (D-ARQ-35 Parte 3), não porteira da conduta. Pacote: hemograma 6M [adm/per/MR/dem] + reticulócitos 6M [adm/per/MR/dem] + t,t-mucônico 6M [per]. `benzeno` novo em `agentes.yaml` (`cas: "71-43-2"` [DERIVADO — CAS Registry]; `is_carcinogeno_iarc: true` [DERIVADO — IARC grupo 1]; `anexo_nr07: null` e `tem_lt: null` — eixo Quadro 1/2 / IBE do Anexo I é débito DT-FDS-01; a regra dispara por identidade de agente, null é honesto, não crava valor sem fonte); `reticulocitos`/`acido_transmuconico` novos em `exames.yaml`. Periodicidade: hemograma e t,t-mucônico [VALIDADO — R-PKG-BZ]; reticulócitos 6M [DERIVADO — analogia hemograma R-PKG-BZ] (protocolo dá momentos, não periodicidade). NÃO toca `tipos.py`, `materialidade.py`, orquestrador, Stage 8 — só dado (yaml) + primitivo + regra + teste. Ainda sintético: sem hidratação CAS→slug→flags (D-ARQ-25 Parte B), benzeno-via-FDS só existe em fixture à mão — fecha o par promoção→conduta, não a travessia de produção. Commit `ab1b386`, merge `1078baa` (PR #77, "Create a merge commit"). Suíte 229→233 isolado; mypy --strict limpo. (Detalhe do blast radius e do desvio de processo — correção de teste pré-existente quebrado por consequência mecânica — no bloco 003.Q do HISTORICO; DH-003P-01 segue aberta, não tocada.)

**Nota (003.V).** A 4ª fonte ganha produtor real de composição resolvida a montante: `resolver_composicao` (motor irmão mínimo, ver D-ARQ-36 aplicação 003.V) entrega `ProdutoQuimico.fds.composicao` com componentes resolvidos via gate-CAS, e a Fase C então os promove a `Risco(fonte="quimico_composicao")` sem alteração. Até 003.U a composição da fixture chegava resolvida à mão (slug populado na própria fixture, pulando o gate); a 003.W move a resolução para o pipeline (fixture crua → `resolver_composicao` → Fase C). Fase C intocada — esta nota não altera D-ARQ-35, registra o produtor que a alimenta.

**Nota (003.W).** O produtor anunciado na nota 003.V existe: `resolver_composicao` materializado em `motor/composicao.py` (D-ARQ-36 aplicação 003.W), ISOLADO ainda — sem chamador no pipeline. Quando plugado (fatia futura), a fixture crua atravessa `resolver_composicao` → Fase C e a 4ª fonte é promovida a partir de composição resolvida pelo gate, não de slug cravado à mão. Fase C intocada.

**Nota (003.X).** A cadeia que a nota 003.W dava como "fatia futura" (`fixture crua → resolver_composicao → Fase C`) ganhou teste de integração — `test_integracao_composicao_fase_c.py`, 6 testes, ISOLADO de `executar()`. Provado sobre o vocabulário REAL (`construir_indice_cas(agentes.yaml)`, primeira execução do índice sobre dado de produção): o GHE-adesivo promove 3 `Risco(fonte="quimico_composicao")` (acetona/MEK MATERIAL, acetato AUSENTE-straddle), os 4 componentes sem-slug não promovem. A Fase C não foi tocada — esta nota registra a costura provada, não altera D-ARQ-35.

## D-ARQ-36 — Extração de composição é bicamada (LLM-transcrição + resolvedor determinístico); "CAS transcrito" é a fronteira; gate-CAS é a fatia 1

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA). Sem código nesta sessão. Implementação por fatias — fatia 1 = gate-CAS (Parte 2). Autorização para virar D-ARQ é do Diovanni.

**Contexto.** O candidato (i) do handoff 003.Q — hidratação CAS→slug→flags (D-ARQ-25 Parte B), o gargalo real para FDS de produção entrar — foi confirmado pelo Diovanni e aberto em ARQUITETURA. Recomendação do Arquiteto sobre (ii)/(iii) do mesmo handoff: única frente que sai do sintético; o predicado de materialidade está órfão de consumidor de produção desde a 003.J, e (i) constrói a costura que D-ARQ-34 Parte 4 pressupõe pronta.

A leitura literal dos docs vivos expôs uma tensão entre D-ARQ-34 Parte 4 — "flags chegam pela ficha já normalizada, extração resolveu CAS→slug→flags" — e a aplicação real da 003.P, que re-hidratou `is_ototoxico`/`anexo_nr07` de `agentes.yaml` por-slug no Stage 2 médico. Hoje, sobre dado sintético, ninguém percebe a divergência; (i) é exatamente a fatia que constrói o "CAS→slug→flags" que D-ARQ-34 dá por pronto. Essa costura tinha de fechar primeiro, ou a próxima sessão de código implementaria sobre contrato ambíguo.

Três passadas adversariais sobre a forma (escopo) reduziram uma proposta inicial de quatro decisões a uma só. (1ª) A proposta inicial empilhava DF-1 (extração bicamada), DF-2 (fonte canônica de flag = resolvedor, removendo a re-hidratação do médico), DF-3 (honrar frase-H sem slug → MATERIAL) e DF-4 (4 ramos do gate). (2ª, a pedido do Diovanni) DF-3 caiu: inverte o ramo 0 da 003.J (`agente is None → AUSENTE`, anti-supressão-silenciosa) e É o enunciado de DT-003M-01 `[ABERTA]` — importar uma DT aberta como corolário quebraria "uma coisa por vez"; DT-003M-01 permanece sessão própria. DF-2 foi rebaixada a nota de não-conformidade diferida: cravá-la decidiria o destino de uma costura que a fatia 1 (gate-CAS) não toca. DF-1 deixou de ser vendida como leitura nova de D-ARQ-09 — é D-ARQ-33 cl.1 ("descoberta CAS via LLM a montante, preserva D-ARQ-09 nos dois lados") tornada explícita. (3ª, "seja crítico") confirmou que, removidas DF-2/DF-3, o que sobra é só o gate-CAS — estreito, testável com CAS sintéticos, sem depender de nenhuma decisão diferida nem da reabertura do predicado.

**Decisão — três partes.**

*Parte 1 — topologia da sub-camada (explicita D-ARQ-33 cl.1, não a substitui).* A extração de composição química é bicamada: **LLM-transcrição** (lê a FDS e transcreve nome/CAS/faixa de concentração/frases-H para texto estruturado; na zona R-FDS-04 — "hidrocarbonetos aromáticos" sem CAS resolvível — propõe um CAS-candidato de baixa confiança para revisão humana, nunca classificação autônoma) + **resolvedor determinístico** (recebe o CAS transcrito, valida o dígito verificador, resolve CAS→slug em `agentes.yaml`, popula as flags do `Componente` e monta o `Componente` resolvido). A fronteira LLM↔determinístico é o **"CAS transcrito"** — o ponto exato em que D-ARQ-09 se aplica ao lado-engenheiro (espelha a fronteira "tipos.PGR" do lado-médico, D-ARQ-25 Parte A). Releitura de D-ARQ-34 Parte 4: "ficha normalizada" = saída do resolvedor determinístico, não da LLM-transcrição — a normalização CAS→slug→flags é trabalho do resolvedor, não do LLM. O resolvedor só resolve **CAS→slug**; `name→slug` (normalização por nome, sem CAS) permanece indecisa em D-ARQ-25 Parte B — fora do escopo desta decisão. `[DERIVADO — D-ARQ-33 cl.1 literal]`.

*Parte 2 — gate-CAS é a fatia 1: quatro ramos sobre o CAS transcrito.* O resolvedor recebe o CAS transcrito e classifica em quatro ramos, antes de qualquer outro processamento:
- **(a) válido + slug resolvido** — CAS com dígito verificador ok e slug presente em `agentes.yaml` → hidrata o `Componente` normalmente (flags + `agente`), segue o fluxo da 003.J/003.P.
- **(b) válido + sem-slug** — CAS com dígito ok mas slug NÃO resolvido (vocabulário ausente) → `Pendencia(tipo="vocabulario_ausente", bloqueante=False)` conforme D-ARQ-14; `Componente.agente=None`. O bloqueio (se houver) fica a cargo do predicado de materialidade ramo 0 (003.J) no lado-médico — o gate **não duplica** essa integridade.
- **(c) inválido no dígito** — CAS que falha o dígito verificador → `Pendencia(bloqueante=True)`. Caso-âncora: os CAS-fantasma `022-00-9`/`014-00-0` identificados na 003.F caem aqui — dígito conferido, falham.
- **(d) oculto/ausente** — CAS oculto (segredo industrial) ou ausente → `Pendencia`. Oculto ≠ inválido (DT-003M-01) — são ramos distintos, não o mesmo tratamento. Honrar a frase-H declarada quando o CAS está oculto (promover a MATERIAL sem slug) reabriria o ramo 0 da 003.J e É o enunciado de DT-003M-01 — explicitamente **fora de escopo** desta decisão.

*Parte 3 — unificação da fonte-de-flag é direção, não decisão; 003.P não tocada.* O gate-CAS, na fatia 1, **não popula flags de conduta-física** (`is_ototoxico`, `anexo_nr07`) — só valida CAS e resolve slug. A re-hidratação por-slug que a 003.P introduziu no Stage 2 médico permanece como está. Mover essa re-hidratação para o resolvedor (fonte única de flag) é a **direção** apontada por D-ARQ-25 Parte B + D-ARQ-34 Parte 4, mas decidir e remover a re-hidratação do médico é **item próprio, STOP-and-report, decidido pelo Diovanni** — não cabe nesta fatia. Até essa decisão, a coexistência das duas fontes (ficha normalizada do resolvedor + re-hidratação por-slug do médico) é **redundância benigna e idempotente** — ambas leem o mesmo `agentes.yaml` por-slug, não divergem.

**Consequência.**

Dois limites honestos, confirmados na passada final, declarados aqui em vez de mascarados por mecanismo novo:

1. **O gate valida boa-formação, não correção-de-transcrição.** Um CAS transcrito incorretamente pela LLM, mas ainda assim válido no dígito verificador, resolve para um slug ERRADO — e o gate-CAS não pega isso. Esse erro só é capturado pela revisão de saída (D-ARQ-22) ou pelo responsável técnico (D-ARQ-33 cl.4, R-PGR-01). Um cross-check nome↔CAS (a FDS declara nome E CAS; conferir consistência) foi considerado e descartado da fatia 1: pressupõe `name→slug`, que a Parte 1 exclui explicitamente do escopo. É trabalho pós-decisão-de-`name→slug`, não fatia futura do gate-CAS.

2. **O ramo (b) permanece não-bloqueante.** Mover o bloqueio do vocabulário-ausente para o gate duplicaria a integridade que D-ARQ-17 centralizou e que a 003.J materializou no predicado de materialidade (ramo 0). O gate é lado-engenheiro; o predicado roda nos dois lados (engenheiro e médico) — bloquear cedo, no gate, tiraria do lado-médico a disciplina tri-estado (D-ARQ-13) sobre o mesmo dado. Adicionar mecanismo em qualquer um dos dois lados para "cobrir" esses limites seria "parecer completo" vencendo "estar correto" — o viés que D-ARQ-22 nomeia. A recomendação é declarar os limites e seguir, não adicionar mecanismo.

Demais consequências:
- Dá forma à fronteira LLM↔determinístico do lado-engenheiro que D-ARQ-25/33 davam só como topologia em prosa — "CAS transcrito" é agora o ponto de corte nomeado, testável com CAS sintéticos (válido-com-slug, válido-sem-slug, inválido-no-dígito, oculto/ausente).
- A fatia 1 (gate-CAS) é implementável isolada — não depende de DF-2 (unificação de flag, diferida) nem de DF-3/DT-003M-01 (frase-H sem slug, fora de escopo).
- Algoritmo do dígito verificador do CAS é `[DERIVADO]` nesta sessão, conferido só contra os casos conhecidos (benzeno 71-43-2 confere; fantasmas 022-00-9/014-00-0 da 003.F falham) — conferir contra fonte autoritativa na implementação antes de tratar como `[VALIDADO]`.

**Fronteiras (não confundir):**
- **D-ARQ-25 Parte B** — esta decisão é a primeira fatia da normalização de vocabulário a montante do motor que D-ARQ-25 Parte B previa sem forma. `name→slug` permanece indeciso, fora desta decisão.
- **D-ARQ-33 cl.1** — não revoga; torna explícita a topologia bicamada (LLM-transcrição + resolvedor determinístico) que cl.1 já enunciava em prosa, nomeando a fronteira como "CAS transcrito".
- **D-ARQ-33 cl.4** — reforçada: o limite 1 da Consequência (gate valida boa-formação, não correção) é exatamente o espaço que cl.4 (admissão final é ato do responsável técnico, R-PGR-01) cobre.
- **D-ARQ-34 Parte 4** — releitura, não revogação: "ficha normalizada" passa a ter dono explícito (saída do resolvedor determinístico, não da LLM-transcrição).
- **D-ARQ-35 Parte 3** — não tocada: a Parte 3 desta decisão (unificação de fonte-de-flag) é diferida; D-ARQ-35 Parte 3 (materialidade anda junto com a promoção) segue intocada, alimentada pelas mesmas flags de hoje (003.P).
- **D-ARQ-14 / D-ARQ-17 / D-ARQ-13** — reusados sem alteração: ramo (b) cai em D-ARQ-14 (vocabulário ausente, não-bloqueante); ramos (c)/(d) caem em pendência bloqueante na linha de D-ARQ-17/13, sem novo mecanismo.
- **D-ARQ-22** — o limite 1 (gate não pega CAS-errado-mas-válido) é risco residual da classe "erro silencioso plausível" que D-ARQ-22 nomeia; mitigação é a revisão de saída existente, não mecanismo novo no gate.
- **DT-003M-01 / DT-FDS-02** — referenciadas explicitamente como fora de escopo desta decisão, sem mudança de status.

**Base.** Sessão 003.R (15/06/2026). Resolve a costura entre D-ARQ-34 Parte 4 e a aplicação real da 003.P, explicitando D-ARQ-33 cl.1. Topologia bicamada `[DERIVADO — D-ARQ-33 cl.1 literal]`; CAS-candidato LLM `[INTERPRETADO]` por construção (espelha D-ARQ-33 cl.4 — candidato, não classificação autônoma). Três passadas adversariais sobre o escopo (DF-1 a DF-4 → só o gate-CAS sobrevive). Decisão de arquitetura — sem código. Implementação (fatia 1 = gate-CAS) é sessão de código futura.

**Aplicação na sessão 003.S (15/06/2026) — fatia 1 (gate-CAS, resolvedor determinístico).** Módulo greenfield `agente_medico/motor/resolvedor.py` (paralelo a `materialidade.py`; sem submódulo `engenharia/` — gatilho de promoção D-ARQ-16 não disparou com um arquivo só), quatro funções puras: `_so_digitos` (normaliza CAS), `cas_bem_formado` (dígito verificador do CAS Registry), `construir_indice_cas` (inverte o vocabulário CAS→slug — o índice inverso NÃO existia, `agentes.yaml` só era lido por-slug; colisão → `ValueError`, molde "divergir → PARAR e reportar" do `leo_resolver`), `gate_cas` (4 ramos). Retorno `tuple[Componente, Optional[Pendencia]]` (árvore exclusiva → no máximo uma pendência). Ramos: (a) válido+slug → `dataclasses.replace(agente=slug)`, sem pendência; (b) válido+sem-slug → `Pendencia(tipo="vocabulario_ausente", destinatario="protocolo", bloqueante=False)` (D-ARQ-14); (c) dígito falha → `Pendencia(tipo="cas_invalido", destinatario="empresa", bloqueante=True)` (fantasmas `022-00-9`/`014-00-0` da 003.F caem aqui); (d) CAS ausente → `Pendencia(tipo="cas_ausente", destinatario="empresa", bloqueante=False)` (oculto≠inválido — assimetria malformação-vs-ausência-legítima; o bloqueio mora downstream na Fase C, que transforma `agente=None` em `materialidade_ausente` bloqueante). Todas as pendências com `regra_origem="D-ARQ-36"`, `ghe_id=None` (gate roda a montante da mesa). NÃO popula flags de perigo (`is_carcinogeno_iarc`/`is_sensibilizante`) — unificação de fonte-de-flag é diferida (D-ARQ-36 Parte 3). Isolado, sem consumidor (espelha o predicado isolado da 003.J). Algoritmo do dígito verificador promovido `[DERIVADO]`→`[VALIDADO]` — conferido contra CAS.org (fonte autoritativa primária, cas.org/training/documentation/chemical-substances/checkdig) + Apache Commons Validator / Wikipedia / ThermInfo / R-httk; benzeno `71-43-2`, água `7732-18-5`, metanol `67-56-1` conferem. Commit `5429954`, PR a abrir ("Create a merge commit"). Suíte 233→246 isolado (+13); mypy --strict limpo (17 arquivos).

**Aplicação na sessão 003.T (16/06/2026) — fatia 2 (Parte 3 parcial: gate-CAS popula is_carcinogeno_iarc).** O gate-CAS passa a popular `is_carcinogeno_iarc` no `Componente` resolvido, fechando o buraco que `resolvedor.py:64` declarava ("NÃO popula flags"). Forma: novo tipo frozen `EntradaIndice` (`slug` + `is_carcinogeno_iarc`) substitui o retorno `dict[str, str]` de `construir_indice_cas` — o índice deixa de carregar só identidade e passa a carregar a flag de perigo lida de `agentes.yaml` por-slug no momento da construção (leitura única, não a cada chamada do gate; razão da forma (2) sobre (1)/(3): mantém `gate_cas` com um só argumento e a fixture de teste com uma só estrutura). `gate_cas` ramo (a): `dataclasses.replace(componente, agente=entrada.slug, is_carcinogeno_iarc=entrada.is_carcinogeno_iarc)`; ramos (b)/(c)/(d) intactos. Gate de procedência (D-ARQ-22) ANTES de tocar código confirmou `is_carcinogeno_iarc` presente e explícita em todos os agentes do yaml (benzeno `71-43-2` → `true`) — sem degradação silenciosa por `.get(..., False)`. **Recorte decidido por gate de procedência:** `is_sensibilizante` está AUSENTE do `agentes.yaml` (chave inexistente em todos os agentes) — fica FORA desta fatia, NÃO entra no `EntradaIndice`, o gate não a toca (DT-003T-01). 2ª passada reverteu a recomendação inicial de "incluir is_sensibilizante no EntradaIndice degradando para False com marca-comentário" por ser fiação fantasma de dado inexistente (a marca viveria no código-fonte, não no dado; `False` tipado seria indistinguível de classificação real — erro silencioso plausível de D-ARQ-22). `is_ototoxico`/`anexo_nr07` permanecem re-hidratados por-slug no lado-médico (Fases A/B/C de `riscos.py`) — só existem em `Risco`, não em `Componente`, o gate não tem onde escrevê-los. **Parte 3 segue PARCIAL:** esta fatia fez só a flag carcinógeno; a unificação-de-fonte-de-flag (mover a re-hidratação por-slug do médico para o resolvedor) permanece diferida, STOP-and-report do Diovanni, como D-ARQ-36 Parte 3 já marcava — intocada nesta fatia. Gate segue ISOLADO, sem consumidor (espelha 003.J/003.S; o consumidor é o motor irmão, não construído). Commit `f308693`, merge `9058884` (PR #81, "Create a merge commit"). Suíte 246→248 isolado (+2: par carcinógeno/não-carcinógeno do ramo (a) provando população-do-dado, não `True` cravado); mypy --strict limpo (16 arquivos); blast radius 2 arquivos (`resolvedor.py`, `test_resolvedor.py`).

**Aplicação na sessão 003.V (16/06/2026) — ARQUITETURA (fatia 3 do arco (i): motor irmão mínimo + fonte-de-flag resolvida).** Mini-sessão de ARQUITETURA que fecha a costura entre D-ARQ-34 Parte 4 ("ficha normalizada resolve CAS→slug→flags") e a forma de plugar o gate-CAS (isolado desde 003.S/003.T) num consumidor de produção. Duas decisões:

(a) **Motor irmão mínimo = `resolver_composicao(pgr, indice_cas) -> PGR`**, função pura a montante de `executar()`. Aplica `gate_cas` componente a componente e remonta a estrutura frozen (`PGR`→`GHEPGR`→`ProdutoQuimico`→`FDS`→`Componente`) com composição resolvida. A remontagem via `dataclasses.replace` em cascata é DELIBERADA, não custo aceito a contragosto: mutar uma cópia ou afrouxar o `frozen=True` dos tipos foi rejeitado por quebrar a imutabilidade que sustenta a pureza do motor (D-ARQ-09) — o preço em código de remontagem é o que paga a garantia de que nenhum estágio a jusante observa um `PGR` mutável. Preserva D-ARQ-33 cl.1/2 (engenheiro resolve composição, não emite `Risco`) e D-ARQ-35 Parte 1 (médico promove no Stage 2). A Fase C de `riscos.py` e `executar()` ficam intocados. A fixture `fds_t65` (003.M) é reescrita CRUA (`agente=None` em todos os componentes); o gate resolve pelo CAS — exercitando os 4 ramos sobre os CAS reais das 3 FDS, inclusive (c) o TiO₂ de CAS errado `134363-67-7` que a 003.M documentou e (d) o Segredo Industrial de CAS oculto. O nome físico do módulo (`motor/composicao.py` vs. submódulo `engenharia/`) fica deliberadamente em aberto para a abertura da 003.W — decisão de implementação que o gatilho de promoção D-ARQ-16 ("dois arquivos provam o padrão") resolve com o código na mão, não de memória. `[DERIVADO — D-ARQ-33 cl.1/2 literal; D-ARQ-36 Parte 1]`.

(b) **Fonte-de-flag resolvida a favor da transcrição (Parte 3 sai de "diferida" para resolvida quanto a `is_carcinogeno_iarc`).** O `gate_cas` deixa de sobrescrever `is_carcinogeno_iarc` no ramo (a): a flag é propriedade do componente-NESTE-PRODUTO (via de exposição, ligação em matriz), não da substância em abstrato — o yaml fornece identidade (slug), a FDS transcrita fornece periculosidade-neste-produto. Reverte a sobrescrita que a 003.T introduziu (ramo (a) parava de fazer `is_carcinogeno_iarc=entrada.is_carcinogeno_iarc`); `EntradaIndice.is_carcinogeno_iarc` permanece carregado mas inerte, aguardando a Parte 3 plena (tri-estado + `is_sensibilizante`, sessão própria). Caso-âncora que prova a reversão: o TiO₂ da Tinta Acrílica (003.M) — yaml=`true` (substância, IARC 2B em abstrato), Componente=`false` (este produto, base água, via inalatória não aplica); honrar o yaml apagaria a divergência substância-vs-produto que D-ARQ-34 Parte 4 protege. A 003.T populou do yaml por NÃO ter consumidor que expusesse o conflito; a 003.V é o primeiro consumidor (`resolver_composicao` + fixture TiO₂) e ele prova yaml-como-fonte errado para o caso real. STOP-and-report cumprido: decisão autorizada pelo Diovanni. `[INTERPRETADO — prioridade na revisão de saída]` (qual fonte vence quando há divergência não tem âncora normativa; o caso TiO₂ a ancora empiricamente).

Descartado nesta sessão o tri-estado `Optional[bool]` para `is_carcinogeno_iarc` (distinguir "FDS diz não-carcinógeno" de "FDS não opinou"): é a complexidade que a Parte 3 deliberadamente adiou; (b.2)-simples (transcrição vence, `bool`, gate não toca a flag) é o recorte honesto, deixando o tri-estado para quando `is_sensibilizante` for decidido junto (DT-003T-01 + DT-003M-01, sessão própria). Sem código nesta sessão — implementação da fatia (`resolver_composicao` + fixture crua + reversão + testes dos 4 ramos) é a 003.W.

**Aplicação na sessão 003.W (16/06/2026) — IMPLEMENTAÇÃO (fatia 3 do arco i: motor irmão mínimo + reversão da fonte-de-flag).** Materializadas as duas decisões da 003.V em uma leva coesa. (a) `resolver_composicao(pgr, indice_cas) -> PGR` em módulo greenfield `agente_medico/motor/composicao.py` (flat, não submódulo `engenharia/` — gatilho de promoção D-ARQ-16 não disparou com um arquivo só): função pura a montante de `executar()`, aplica `gate_cas` componente a componente e remonta a cascata frozen (`PGR`→`GHEPGR`→`ProdutoQuimico`→`FDS`→`Componente`) via `dataclasses.replace`; descarta a `Pendencia` do gate nesta fatia (propagação ao `Resultado` é costura posterior, liga DH-003P-01). ISOLADO — `executar()` e orquestrador INTOCADOS, sem chamador no pipeline (plug é fatia seguinte; espelha o predicado isolado da 003.J e o gate isolado da 003.S). (b) Reversão da sobrescrita de `is_carcinogeno_iarc` no ramo (a) do `gate_cas` (reverte 003.T): `replace(componente, agente=entrada.slug)` sem a flag; `EntradaIndice.is_carcinogeno_iarc` fica carregado mas inerte. A flag é da transcrição do `Componente`, não do índice — yaml dá identidade, FDS dá periculosidade-neste-produto (D-ARQ-34 Parte 4). Fixture `fds_t65` reescrita CRUA (`agente=None` em todos; TiO₂ com o CAS errado real `134363-67-7` que falha o dígito → ramo (c)); o gate resolve pelo CAS. `test_materialidade_fds` migrado para a cadeia `fixture crua → gate_cas → materialidade` (decisão A, autorizada): contagem mudou de 1/23/0 para **2 MATERIAL / 22 AUSENTE / 0 NÃO-MATERIAL** — acetona e acetato_de_etila ganharam slug em 003.N e resolvem pelo CAS (acetona piso 30>5 → MATERIAL; acetato piso 5 ≤ 5 < 30 → straddle → AUSENTE; MEK piso 10>5 → MATERIAL). Teste da reversão (`test_gate_reversao_nao_sobrescreve_flag`): índice com `dioxido_de_titanio`=True + componente cru False → flag fica False (FALHA sob 003.T, PASSA pós-reversão — discriminante). 4 ramos sobre CAS reais das 3 FDS, incl. dois (c): TiO₂ errado `134363-67-7` e aluminato `1242-78-3` (este último também falha o dígito — `[DERIVADO — cas_bem_formado, 003.W]`; achado de transcrição registrado como DT, ver HISTORICO). Honestidade de escopo: a fatia NÃO tira de produção — `resolver_composicao` nasce isolado, a entrada segue fixture; move a fronteira do sintético para a entrada da transcrição (o salto de produção é a LLM-transcrição, D-ARQ-25 Parte B, fatia futura). `[DERIVADO — D-ARQ-36 nota 003.V (a)/(b); D-ARQ-33 cl.1/2; D-ARQ-09]`. Commit `9029282`, merge `24c058d` (PR #85, "Create a merge commit"). Suíte 248→255 isolado (+7) / 404 total (legado intocado); mypy --strict limpo.

**Aplicação na sessão 003.X (18/06/2026) — (i₀), teste de integração (sem produção).** O descarte da `Pendencia` do gate por `resolver_composicao` (declarado na aplicação 003.W, ligado a DH-003P-01) virou **degradação observável em teste**: TiO₂ (CAS errado `134363-67-7`, ramo c → `cas_invalido` bloqueante) e copolímero PVC (`9003-22-9`, ramo b → `vocabulario_ausente`) chegam à Fase C **indistinguíveis** — ambos `agente=None` → ramo 0 → `materialidade_ausente`/D-ARQ-35. A procedência do gate (c vs. b) é fundida no descarte. `test_degradacao_procedencia_cas_invalido_vira_materialidade_ausente` crava isto; quando (i') propagar a `Pendencia` ao `Resultado` (fecha DH-003P-01), esse teste muda de asserção. Sem código de produção. `[DERIVADO — saída real da cadeia, 003.X]`. Commit `f17db90`, merge `31c767b` (PR #87, "Create a merge commit"). Suíte 255→**261 isolado** / 410 total (legado intocado). mypy --strict limpo (1 arquivo).

## D-ARQ-37 — Propagação da pendência do gate-CAS ao Resultado é via retorno-tupla do motor irmão, como pendência global, não realocação para o Stage 3

**Status:** DECISÃO DE ARQUITETURA. Sem código nesta sessão. Implementação (assinatura de `resolver_composicao` + wrapper + costura ao Resultado + testes) é sessão futura (003.Z). Autorização para virar D-ARQ é do Diovanni.

**Contexto.** A 003.W materializou `resolver_composicao` (motor irmão mínimo) isolado, com a `Pendencia` do `gate_cas` **descartada** por design (`composicao.py`: pega `gate_cas(...)[0]`, joga fora o `[1]`), ligando o débito a DH-003P-01. A 003.X observou em teste a consequência: TiO₂ (ramo c, `cas_invalido` bloqueante) e copolímero PVC (ramo b, `vocabulario_ausente` não-bloqueante) chegam à Fase C **indistinguíveis** — ambos `agente=None` → `materialidade_ausente`. O handoff 003.Y previa fechar isto plugando `resolver_composicao` no pipeline + propagando a pendência. A pergunta de arquitetura: **a integridade de CAS é propagada do gate, ou realocada para o estágio que já é dono da integridade de input (Stage 3, D-ARQ-17)?**

**Realocação para o Stage 3 — considerada e rejeitada.** A tentação era estender `stage_3_pendencias_estruturais` para validar o dígito verificador (`cas_bem_formado`) no ramo de componente, já que o Stage 3 tem `ghe_id` correto e é o dono nomeado da integridade de input por-GHE. Rejeitada por **ordem de estágios**, confirmada no `orquestrador.py`: `stage_2_riscos` (que contém a Fase C de promoção química) roda **antes** de `stage_3_pendencias_estruturais`. Quando o Stage 3 rodasse, a Fase C já teria consumido o componente de CAS inválido com `agente=None` e já teria emitido `materialidade_ausente` um estágio antes — o Stage 3 acrescentaria uma segunda pendência, não corrigiria a primeira. Além disso: a procedência ramo-c-vs-ramo-b **só existe no `[1]` que `gate_cas` retorna**, e some no descarte de `resolver_composicao`; depois de `agente=None`, nenhum estágio a jusante pode reconstruí-la. A realocação consertaria na camada errada um dano que nasce a montante. `[DERIVADO — ordem de estágios em orquestrador.py; Fase C em riscos.py; descarte em composicao.py]`.

**Decisão.** A propagação é a resposta correta porque é a única operação no ponto onde o dado ainda está vivo (o `[1]` do gate, antes do descarte). Forma:
1. `resolver_composicao` passa de `-> PGR` a `-> tuple[PGR, list[Pendencia]]`. Captura o `[1]` de cada `gate_cas` que hoje descarta, acumulando-o, em vez de jogá-lo fora.
2. **As pendências do gate são de nível-resolução, globais por natureza — não recebem `ghe_id`.** O `gate_cas` roda a montante da mesa (D-ARQ-36), onde GHE estruturalmente não existe; carimbar `ghe_id` reintroduziria contexto que a arquitetura deliberadamente manteve fora do lado-engenheiro. A qual GHE/produto um CAS-inválido pertence é rastreável pelo nome do componente no `motivo` da própria pendência — trabalho da revisão de saída (D-ARQ-22), não do tipo. Destino coerente: `Resultado.pendencias_globais`, onde `executar` já põe as pendências sem-matriz (gate Stage 1 não-bloqueante) — `orquestrador.py`.
3. O wrapper de produção `executar_com_composicao(pgr, protocolo, indice_cas, hoje=None) -> Resultado` encadeia `pgr_resolvido, pend_gate = resolver_composicao(pgr, indice_cas)` → `resultado = executar(pgr_resolvido, protocolo, hoje)` → costura via `dataclasses.replace(resultado, pendencias_globais=resultado.pendencias_globais + pend_gate)`. **Remontagem, não mutação** — coerente com a disciplina anti-mutação do projeto (D-ARQ-09; cascata frozen remontada por `replace` na 003.V). Embora `Resultado` seja mutável (`tipos.py`, `@dataclass` sem `frozen`), mutar o objeto que `executar` devolveu repetiria o anti-padrão que `resolver_composicao` paga caro pra evitar. `executar` permanece intocado e indiferente a `indice_cas` (D-ARQ-09/15 intactos); o wrapper é o ponto onde a transcrição-LLM futura (D-ARQ-25 Parte B) injetará o índice real.
4. Forma alternativa β (coletor paralelo, `resolver_composicao` mantém `-> PGR`) rejeitada: `resolver_composicao` já tem a tupla na mão e já a descarta explicitamente; α para de descartar, β reconstruiria um canal para um dado já disponível. α é a mudança mínima sobre o código existente.

**Pureza preservada.** Retorno-tupla **não** viola D-ARQ-09: aquela decisão é sobre o motor **médico** (`executar`) ser puro/determinístico. `resolver_composicao` é o motor irmão; retornar `(PGR, pendências)` é tão determinístico quanto retornar `PGR` (mesmo input → mesmo output). A pureza que a 003.V invocou era imutabilidade-da-cascata-frozen (não mutar `frozen=True`), preservada — `resolver_composicao` continua remontando via `dataclasses.replace`, e o wrapper costura o `Resultado` também por `replace`.

**Limite declarado (não mascarado por mecanismo novo — D-ARQ-22).** α faz a pendência **precisa** do gate (tipo/destinatário/bloqueio corretos por ramo) chegar ao `Resultado`. **Não** elimina o `materialidade_ausente` que a Fase C já emite para o mesmo componente sem-slug: para componente de ramo (b)/(c)/(d), a Fase C vê `agente=None` e emite a pendência achatada **antes** (Stage 2), e α **adiciona** a precisa ao lado, sem suprimir a achatada. Resultado: dupla pendência para o componente sem-slug — melhor que hoje (a precisa passa a existir), não limpo (a achatada persiste). Fechar DH-003P-01 aqui significa "a procedência do gate chega ao Resultado", não "a Fase C para de achatar". Eliminar a duplicação — a Fase C consumir a pendência do gate em vez de re-derivar materialidade para componente sem-slug — é fatia e decisão separadas. Registrado como DT-003Y-01.

**Divergência do handoff 003.Y, declarada.** O handoff dizia "(i') plug + propagação da Pendencia ao Resultado". Converge no destino (propagação). Diverge na mecânica: o handoff não especificava retorno-tupla nem o destino global, e não tinha confrontado o gate contra o Stage 3 lado a lado (o que teria exposto a tentação de realocação e sua refutação pela ordem de estágios). Handoff orienta; git + literais vencem.

**Fronteiras (não confundir):**
- **D-ARQ-17** — não revoga nem estende. A realocação para o Stage 3 foi explicitamente rejeitada (ordem de estágios). O Stage 3 segue dono da integridade de **presença** de CAS (CAS vazio → `composicao_ausente`); a boa-formação (dígito) fica com o gate, propagada por α como pendência global. Não há duplicação de integridade.
- **D-ARQ-36** — o gate-CAS é intocado: continua validando boa-formação a montante e retornando `(Componente, Optional[Pendencia])` com `ghe_id=None`. Muda só o consumidor (`resolver_composicao` para de descartar o `[1]`).
- **D-ARQ-09** — preservada nos dois lados (ver "Pureza preservada").
- **D-ARQ-35 Parte 3 / Fase C** — intocada nesta decisão. A Fase C continua promovendo e continua emitindo `materialidade_ausente` para sem-slug. A duplicação com a pendência propagada é o limite declarado, endereçado por DT separada.
- **DH-003P-01** — fechada por esta decisão (no sentido declarado: procedência do gate chega ao Resultado).

**Base.** Sessão 003.Y (19/06/2026). Resolve a forma de DH-003P-01 confrontando gate-CAS (D-ARQ-36) contra Stage 3 (D-ARQ-17) e Fase C (D-ARQ-35) sobre os literais em disco. Seis passadas adversariais ao longo da sessão; a última refutou o carimbo de `ghe_id` (incoerente com o destino global — pendência com GHE viveria em `MatrizGHE`, não em `pendencias_globais`), e antes a refutação de "Stage 3 dono" (ordem de estágios) e de "wrapper sem propagação é cosmético" (é regressão). Decisão de arquitetura — sem código. Implementação (003.Z): troca de assinatura de `resolver_composicao` (gate de estado real obrigatório — `git grep resolver_composicao` mapeia os testes 003.W/003.X que quebram com a tupla), wrapper, costura por `replace`, testes falha-sem/passa-com. Passada adversarial extra sobre o prompt cirúrgico antes de emitir (toca assinatura de função compartilhada).

**Aplicação na sessão 003.Z (20/06/2026) — IMPLEMENTAÇÃO (forma α materializada).** A forma α selada na 003.Y virou código. (1) `resolver_composicao` passa de `-> PGR` a `-> tuple[PGR, list[Pendencia]]`: o `[1]` de cada `gate_cas` — antes descartado em `composicao.py` — é acumulado em `pendencias_gate` (sem `ghe_id`, global por natureza; gate roda a montante da mesa de GHE) e retornado no segundo elemento. (2) Wrapper `executar_com_composicao(pgr, protocolo, indice_cas, hoje=None) -> Resultado` em `orquestrador.py`: encadeia `resolver_composicao` → `executar` → costura via `dataclasses.replace(resultado, pendencias_globais=resultado.pendencias_globais + pend_gate)`. Remontagem, não mutação. (3) `executar()` INTOCADO — não recebe `indice_cas`, D-ARQ-09/15 intactos (sentinela `test_executar_nao_recebe_indice_cas` crava a assinatura `[pgr, protocolo, hoje]`). Os 3 chamadores de teste pré-existentes (003.W/003.X) adaptados ao unpack `pgr, _ = …`; asserções intocadas. 9 testes novos em `test_composicao_propaga_pendencias.py` (presença por-ramo b/c/d no `[1]` por `>=1`; sem-`ghe_id`; costura no global por diferencial `n_wrap == n_base + n_gate`; sentinela de assinatura). DH-003P-01: forma fechada em 003.Y, MATERIALIZADA EM CÓDIGO aqui (a propagação que a decisão prometia existe e tem teste). DT-003Y-01 permanece ABERTA: a Fase C segue emitindo `materialidade_ausente` para componente sem-slug ao lado da pendência precisa do gate (dupla pendência), fatia/decisão própria. `[DERIVADO — saída real da cadeia + mypy delta-zero vs. baseline, 003.Z]`. Commit `df3cad2`, merge `cba6048` (PR #90, "Create a merge commit"). Suíte 261→**270 isolado** / 410→**419 total**, 100% verde. mypy --strict: 26 erros pré-existentes (DH-003P-01 / imports `Materialidade`, fora de escopo), delta ZERO vs. baseline `e322ccf` (confronto `df3cad2` vs `df3cad2~1`: 26=26).

## D-ARQ-38 — `tipo_ibe` tem dois consumidores de prontidões distintas; o campo entra para ser consumido; a forma do emissor de biomonitoramento é adiada por dependência do mapa agente→biomarcador
Status: DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código. Implementação multi-fatia futura. Autorização para virar D-ARQ é do Diovanni.
Contexto. DT-003AB-01 (003.AB) mapeou `anexo_nr07` como campo morto/misturado e pôs a substituição `anexo_nr07 → tipo_ibe` como insumo herdado por R-BIO-04. D-ARQ-33 antecipou `tipo_ibe ∈ {EE,SC}` como dado da mesa, com "a regra que o consome é a sucessora de R-BIO-02, fora daquela frente — o dado precede a regra". O gate de estado real desta sessão (greps em disco) revelou três fatos que D-ARQ-33 não previa: (a) `tipo_ibe` não existe em produção (só fixture `test_resolvedor.py`); (b) o schema de `emite` (`emissao.py:47,79`) só emite slug literal fixo, não biomarcador-do-agente-que-disparou; (c) o mapa agente→biomarcador é zero-vocabulário (`agentes.yaml` não tem campo `biomarcador`/`ibmp` em nenhum agente). Logo a frente que D-ARQ-33 tratava como um consumidor único é, na verdade, dois consumidores de prontidões diferentes.
Decisão — quatro partes.

1. `tipo_ibe` tem dois consumidores, não um. (i) R-CLI-02 (clínico semestral por exposição a Quadro 1 ou 2) — consome só a presença `{EE,SC} vs None`, emite `exame_clinico` (slug fixo, schema atual basta). (ii) R-BIO-04 (biomonitoramento por Quadro) — consome a distinção fina EE/SC e emite o biomarcador de cada agente nos momentos do Quadro. R-CLI-03 (Mn) e R-PKG-BZ (benzeno) não consomem tipo_ibe — disparam por identidade de agente. `[DERIVADO — PROTOCOLO §5.1, §5.9; schema emite em emissao.py]`.
2. O campo entra para ser consumido, não morto. Introduzir `tipo_ibe` só se justifica porque R-CLI-02 o consome de imediato — caso contrário recriaríamos o campo-morto que DT-003AB-01 condena, sob nome novo. A prontidão de R-CLI-02 é o que autoriza a migração de campo agora; o biomonitoramento, adiado, não a bloqueia.
3. A forma do emissor de biomonitoramento é adiada por dependência de dado, com critério de resolução nomeado. R-BIO-04 (emitir biomarcador-por-agente) está bloqueado pelo mapa agente→biomarcador inexistente. A escolha de mecanismo (regra-por-agente molde R-PKG-BZ / stage Python genérico / schema estendido) não fecha até o mapa existir, porque a cardinalidade agente→biomarcador (1 exame para Cr⁶⁺; 2 para chumbo = Pb-S+ALA-U) e a regularidade momentos-por-Quadro decidem stage-vs-regras. Adiamento por dado ausente, não indecisão. `[DERIVADO — agentes.yaml sem campo biomarcador; D-ARQ-20 (família-vs-schema)]`.
4. Ordem das fatias. (a) CONHECIMENTO: derivar `tipo_ibe` três-vias (EE/SC/None) e o mapa agente→biomarcador contra texto oficial MTE — uma sessão, os dois do mesmo Anexo I. (b) IMPL: campo `tipo_ibe` + migração `anexo_nr07` (mecânica; gate de tipo compartilhado, passada adversária extra no prompt per 003.W). (c) IMPL: R-CLI-02 consome tipo_ibe (YAML), condicionada à resolução do dedup convergente clínico anual×semestral — D-ARQ-31 nota fatia 3. (d) ARQUITETURA+IMPL: emissor de biomonitoramento, com mapa em mãos.
Consequência.

* Dá a R-BIO-04 um caminho honesto: o que está pronto (clínico, R-CLI-02) avança; o que está data-bloqueado (biomonitoramento) espera o mapa, declarado como dependência, não chutado.
* A migração `anexo_nr07 → tipo_ibe` deixa de ser "a implementação de R-BIO-04" e vira fatia de dado isolada (b), consumida primeiro pelo clínico.
* Universal (D-ARQ-06): tipo_ibe é keyed em agente (cádmio/química, tolueno/construção, agente/saúde), não em setor.
Fronteiras (não confundir):

* D-ARQ-33 — refina, não revoga: a frente "sucessora de R-BIO-02 consome tipo_ibe" tinha um consumidor; esta decisão acha dois e separa prontidões. `tipo_ibe` na ficha-engenheiro (D-ARQ-33) é o mesmo campo; aqui se decide quem o lê no lado-médico.
* D-ARQ-31 — o dedup convergente clínico anual×semestral (cláusula 4c) é o item próprio que a nota fatia 3 deixou em aberto; R-CLI-02 não o resolve, depende dele.
* D-ARQ-35 — a 4ª fonte química promovida no Stage 2 carrega o agente cujo `tipo_ibe` ambos os consumidores leem; o mecanismo de promoção é intocado.
* R-CLI-02/03, R-BIO-04, R-PKG-BZ — IDs e semântica intactas; nenhuma regra clínica criada/alterada nesta sessão. Cria contrato de consumo de dado.
Base. Sessão 003.AC (21/06/2026). Gate de estado real: `tipo_ibe` ausente de produção; schema `emite` slug-fixo; mapa biomarcador zero-vocab (greps em disco). Quatro passadas adversariais (a última sobre o texto da decisão: corrigiu R-CLI-03≠tipo_ibe, granularidade grossa de R-CLI-02, e o seam de dedup convergente como caveat de prontidão). Achados de procedência herdados pela CONHECIMENTO: fixture `test_resolvedor.py:50` tagueia benzeno SC (errado, é Quadro 1/EE) `[DERIVADO — R-BIO-04]`; etanol/HCl `"11"` (NR-15) provável tipo_ibe None, MEK `"11"` mas Quadro 1/EE por R-BIO-04 — os três "11" não mapeiam uniforme `[INCERTO — confirmar contra texto MTE]`. Decisão de arquitetura — sem código.

**Aplicação na sessão 003.AD (21/06/2026) — CONHECIMENTO (fatia (a) da cláusula 4: derivação `tipo_ibe` três-vias + mapa agente→biomarcador).** Os dois produtos da cláusula 4(a) derivados contra o texto oficial do Anexo I (Portaria MTP 567/2022, gov.br/MTE; Quadro 1 IBE/EE e Quadro 2 IBE/SC lidos inteiros).

Critério três-vias `[DERIVADO — NR-07 Anexo I Quadros 1/2, 567/2022, MTE]`: `SC` ⟺ substância no Quadro 2 (conjunto fechado, 4 entradas: cádmio e comp. inorg.; chumbo e comp. inorg.; inseticidas inibidores da colinesterase; flúor/HF/fluoretos inorg.); `EE` ⟺ substância no Quadro 1 (41 substâncias); `None` ⟺ ausente de ambos. Casamento por CAS quando há; por classe/nome para as 4 entradas sem CAS (inseticidas, flúor/fluoretos no Q2; "Indutores de Metahemoglobina" no Q1) — o índice CAS→slug (D-ARQ-36) não as alcança.

Aplicação aos 13 agentes com IBE de `agentes.yaml` (tabela slug→tipo_ibe em DT-003AB-01): 12 EE (acetona, arsenio, benzeno, dissulfeto_de_carbono, estireno, mercurio, metil_etil_cetona, monoxido_de_carbono, n_hexano, tolueno, tricloroetileno, xileno) + 1 SC (chumbo); demais None. Dos 4 SC do Quadro 2, o vocabulário modela só chumbo; dos 41 EE do Quadro 1, modela 12.

Achados de procedência herdados confirmados contra texto oficial: benzeno é **EE** (Quadro 1, S-PMA/TTMA) — a fixture `test_resolvedor.py:50` que o tagueia SC está errada (corrigir na fatia b); o hematológico do R-PKG-BZ vem do Anexo V, não do Quadro. MEK é EE; etanol e HCl são None — os três "11" (NR-15) não mapeiam uniforme (`[INCERTO]`→`[DERIVADO]`).

Três achados novos da aplicação: (1) **9 dos 12 EE têm `cas: null`** no yaml (só acetona, MEK, benzeno têm CAS) — logo `tipo_ibe` é dado gravado offline (derivado por identidade de agente nesta sessão), não casado em runtime por `construir_indice_cas`; popular os 9 CAS faltantes é tarefa de dado paralela, fora do caminho crítico da fatia b. (2) **`chumbo` é ambíguo no eixo Quadro**: inorgânico (7439-92-1) → Q2/SC (Pb-S **e** ALA-U); tetraetila (78-00-2) → Q1/EE (chumbo urina). Recomendado `SC` (inorgânico é o caso ocupacional default), com a decisão registrada explicitamente na migração — não cravar em silêncio. (3) `is_ototoxico` ⊥ `tipo_ibe`: dos 12 ototóxicos, 9 EE, 1 SC, 2 None (cianeto, manganês) — audiometria-por-ototóxico e biomonitoramento-por-Quadro não se pressupõem.

Cardinalidade heterogênea do mapa agente→biomarcador **confirma o data-bloqueio do emissor** (cláusula 3, fatia d): chumbo inorg. = 2 indicadores **simultâneos** (Pb-S **e** ALA-U); benzeno/CO/tolueno/estireno = N **alternativos** ("ou"); Cr⁶⁺ = 1 indicador, 2 critérios de momento; resto 1:1. O emissor não pode assumir um exame por agente. Sem código.

**Aplicação na sessão 003.AE (22/06/2026) — IMPLEMENTAÇÃO (fatia (b) da cláusula 4: migração `anexo_nr07 → tipo_ibe`).** Campo `tipo_ibe` introduzido e `anexo_nr07` migrado, transcrevendo a tabela 003.AD (DT-003AB-01). Forma: enum `TipoIBE(Enum)` {EE, SC} (molde `Materialidade`, 003.J), `tipo_ibe: Optional[TipoIBE]` in-place na posição 5 de `Risco` (sem default, substituindo `anexo_nr07: Optional[str]`); three-way {EE/SC/None} via `Optional`. Gate de tipo compartilhado (repo inteiro, per 003.I): consumo-zero reconfirmado em disco (2 asserções de teste, zero roteamento). 3 hidratações em `riscos.py` viram conversão string→enum (`TipoIBE(meta["tipo_ibe"]) if ... else None`); `agentes.yaml` grava `tipo_ibe` por slug (12 EE + chumbo SC explícito + resto null); comentário stale benzeno reescrito. `tipo_ibe` entra **sem consumidor de produção** (R-CLI-02 é fatia c, com seam de dedup convergente aberto) — "o dado precede a regra" (cl.2), espelha o predicado órfão da 003.J. 419→420 verde, mypy delta-zero (26 baseline DH-003P-01). Commit `e778da8`, merge `78ba5ee` (PR #96). `[DERIVADO — tabela 003.AD; molde Materialidade 003.J; gate de estado real em disco]`.

**Aplicação na sessão 003.CT (12/07/2026) — ARQUITETURA (fatia (d) da cláusula 4: forma do emissor de biomonitoramento, data-desbloqueada).** O data-bloqueio da cl.3 caiu: o mapa agente→biomarcador existe desde 003.AD (PROTOCOLO §5.9). Gate de estado real (disco): `stage_5_emissao` emite slug fixo por regra (`emissao.py`); `Momento` tem RT (Quadro 2 expressável); `exames.yaml` não tem os biomarcadores (só benzeno); `regras.yaml` só emite R-PKG-BZ do lado químico — os 12 agentes com `tipo_ibe` carregam o Quadro e produzem ZERO exame (máquina inerte, padrão do localizador pré-003.CR). **Forma escolhida (ratificada pelo Diovanni): família regra-por-agente, molde R-PKG-BZ** — NÃO estágio Python genérico nem schema estendido. `R-BIO-04-<agente>` em `regras.yaml`, biomarcador no `emite`, momentos por Quadro (EE→`[per]`; SC→`[adm,per,RT,MR,dem]`, R-BIO-04), 6M (R-BIO-01). **Zero código no motor** (reusa `stage_5_emissao`), **zero schema** (biomarcador no `emite`, não em `agentes.yaml`); só adiciona regras YAML + slugs em `exames.yaml`. Precedente: D-ARQ-20 (família > schema estendido), R-PKG-BZ (emissor químico já é regra-por-agente). Cardinalidade declarativa: 1:1 um item; "e" (chumbo Pb-S+ALA-U) dois itens; "ou" (CO/tolueno/estireno/TCE/arsênio) emite o 1º canônico + alternativos no `base_normativa`, `[INTERPRETADO]` (conduta-de-saída = revisão-RT, não pergunta à Carolini — D-ARQ-27). Cr⁶⁺ fora (não-vocab; ilustrou cardinalidade em 003.AD, ganha regra quando entrar). Exclusões: benzeno (R-PKG-BZ, Anexo V, já emite t,t-mucônico) e Mn (R-PKG-SOLD/R-BIO-03) ficam pacote. Trade-off (2ª passada): n≈12 favorece família; se cruzar ~25 agentes, migrar p/ estágio genérico é refatoração futura nomeada (critério "unificar só quando a forma confirmar", molde D-ARQ-54) — não prematuro. **Escopo = fatia (d) só**; R-CLI-02 (fatia c) segue travada em D-ARQ-39 (dedup convergente anual×semestral), não empilha. R-BIO-04 mantém ID (família materializa, molde R-RX-01-\<faixa\>); sem PROTOCOLO novo, sem R- nova. Muda saída (sinalizado): ~11 agentes passam a emitir biomonitoramento; cada regra exige teste-que-falha-sem-ela. Spec fechada (12 regras) no HISTORICO 003.CT. Fatia (d) IMPL é sessão própria. `[DERIVADO — mapa 003.AD; emissao.py slug-fixo; D-ARQ-20/R-PKG-BZ molde]`. Sem código.

**Aplicação na sessão 003.CU (13/07/2026) — IMPLEMENTAÇÃO (fatia (d) da cláusula 4: emissor de biomonitoramento materializado).** Família `R-BIO-04-<agente>` implementada exatamente na forma decidida em 003.CT — **zero código no motor**, reuso de `stage_5_emissao`. 12 regras em `regras.yaml` (11 Quadro 1/EE `[per]` 6M, um exame cada; `R-BIO-04-chumbo` Quadro 2/SC `[adm,per,RT,MR,dem]` 6M, Pb-S **e** ALA-U) + 13 slugs de biomarcador em `exames.yaml`. **Habilitador de motor (1 mudança, universal): fallback de predicado por identidade de agente** — ver D-ARQ-58; sem ele `quando: <agente>` levantaria `PredicadoDesconhecido` (só benzeno/fumos tinham primitivo dedicado). Correção da spec pré-IMPL (2ª passada do Arquiteto sobre a Matriz Dra. Patrícia 06/2025 + NR-7 vigente): o slug do tolueno da spec de 003.CT (`tolueno_urina`) era **erro** — o IBE vigente é **o-cresol na urina** (Portaria SEPRT 2020, alinhada ACGIH; ácido hipúrico é o indicador antigo). Emissor materializou `ortocresol_urina`. As 4 "bordas ou" de 003.CT colapsaram: a Matriz fixa 1 canônico por agente (estireno = *soma* mandélico+fenilglioxílico, exame único, não escolha) → nenhum `[INTERPRETADO]` emitido. Suíte 788+4→804+4 (+16: 11 EE parametrizado + chumbo + caso-negativo + 3 do fallback); mypy delta-zero (46 baseline). Commit `5cf2f24`, merge PR #208 (`2f2ec10`). R-BIO-04 mantém ID; PROTOCOLO ganha changelog 003.CU (correção tolueno), sem R- nova. `[DERIVADO — spec 003.CT; Matriz Patrícia 06/2025; NR-7 Anexo I Quadro 1 rev.2020]`.

**Aplicação na sessão 003.CV (13/07/2026) — IMPLEMENTAÇÃO (extensão da família ao Quadro 2/SC completo).** Mesma forma da 003.CU, **zero motor** (D-ARQ-58 já resolve qualquer slug de `vocabulario.agentes`). 3 regras SC novas — `R-BIO-04-cadmio`, `R-BIO-04-fluoretos`, `R-BIO-04-inseticidas_inibidores_colinesterase` — todas `[adm,per,RT,MR,dem]` 6M, um exame cada, fechando o Quadro 2 do Anexo I em **4/4** (antes só chumbo). Biomarcadores canônicos confirmados contra a Matriz Dra. Patrícia 06/2025 (aba "Periodicidade Exames"): cádmio→cádmio na urina, flúor/HF/fluoretos→fluoreto urinário, inseticidas→**acetilcolinesterase eritrocitária** (canônico entre "OU"; butirilcolinesterase plasma/soro é a alternativa — `[INTERPRETADO — escolha do canônico, revisão de saída]`). A Matriz confirmou empiricamente o eixo de R-BIO-04: agentes EE aparecem só com periódico, os 4 SC com os 5 momentos. Inseticidas modelado como **slug-classe único** (não por praga), alinhado a Anexo I + Matriz. 3 agentes em `agentes.yaml` (`tipo_ibe: SC`) + 3 slugs em `exames.yaml` + 3 regras + teste SC parametrizado. **Bloqueador de gate real** (Code parou, decisão do Arquiteto): `test_indice_real_tem_45_entradas` quebrou (45→48) — os 3 agentes entram no índice de termos do resolvedor; guard de inventário irmão do de vocabulário (22→25), atualizado para 48. Suíte 804+4→807+4 (+3 regra SC); mypy delta-zero (46). Commit `c198ff1`, merge PR #210 (`714aa68`). R-BIO-04 mantém ID; PROTOCOLO v55 (changelog Quadro 2 completo), sem R- nova. `[DERIVADO — Matriz Patrícia 06/2025; NR-7 Anexo I Quadro 2, Portaria 567/2022]`.

**Aplicação na sessão 003.CW (13/07/2026) — IMPLEMENTAÇÃO (extensão da família ao Quadro 1/EE, lote 1).** Mesma forma de 003.CU/CV, **zero motor** (D-ARQ-58 resolve qualquer slug). 9 regras EE novas (cromo_hexavalente, cobalto, fenol, metanol, diclorometano, etilbenzeno, anilina, nitrobenzeno, indutores_metahemoglobina), todas `[per]` 6M / um exame, biomarcadores conferidos no texto oficial do Anexo I Quadro 1 (567/2022, gov.br/MTE). Decisões: (a) cluster metahemoglobina = 3 slugs — anilina e nitrobenzeno são **nomeados** no Anexo, a classe indutores_metahemoglobina pega o resto, os 3 emitem `metahemoglobina_sangue` (molde slug-classe da CV, mas com os dois agentes nomeados como slug próprio); (b) anilina "OU" → canônico metahemoglobina, p-aminofenol alternativo no base_normativa `[INTERPRETADO]`; (c) etilbenzeno reusa `acido_mandelico_fenilglioxilico` (zero slug novo); (d) cromo um exame (mesmo analito, dois critérios). 9 agentes (`tipo_ibe: EE`, CAS gravado exceto a classe) + 6 slugs + 9 regras + 9 casos EE parametrizados. Guards no mesmo commit (lição da CV): exames 25→31, índice 48→57. Suíte 807+4→**816+4**; mypy delta-zero (46). Commit `ff06ace`, merge PR #212 (`95dc482`). Verificação do Arquiteto (2 passadas, git objects em ff06ace): forma + semântica limpas, cross-reference slug↔agente↔exame OK, 24 regras R-BIO-04. **Heads-up registrado:** lote pousa em 24/25; o EE lote 2 cruza o limiar ~25 da 003.CT → dispara o refactor família→estágio genérico (molde D-ARQ-54). `[DERIVADO — NR-07 Anexo I Quadro 1, 567/2022; Matriz Patrícia 06/2025]`.

## D-ARQ-39 — Convergência de mesmo-exame com periodicidades distintas resolve por piso component-wise, não por ConflitoProtocolo

**Status:** IMPLEMENTADA (003.EE, commit `52aa6f3`). Decisão tomada em 003.AF.

**Contexto.** D-ARQ-31 fatia 3 (nota 003.D) recortou explicitamente para fora do seu escopo o dedup convergente do Stage 8: "dois riscos determinados emitindo o mesmo exame com periodicidades distintas → escolha de piso em vez de `ConflitoProtocolo` ... Entra na fila como item próprio; quando vier, é mudança de comportamento do `raise ConflitoProtocolo` e merece decisão própria." Este D-ARQ é esse item. Disparado pela fatia (c) de D-ARQ-38 (R-CLI-02 consome `tipo_ibe`): R-CLI-01 (clínico anual, 12M) e R-CLI-02 (clínico semestral, 6M) convergem no mesmo `exame_clinico` no mesmo GHE com periodicidades distintas, e hoje isso bloquearia o GHE — pré-condição arquitetural de R-CLI-02, não código clínico.

**Gate de estado real (greps/sed em disco nesta sessão).** Confirmado contra `consolidacao.py:20-70` e `tipos.py:157-161`:
- A chave de normalização do dedup é `exame.exame` (slug canônico), nada mais entra.
- O caminho de convergência tem TRÊS mutações incondicionais (`consolidacao.py:58-60`): `existing.momentos |= exame.momentos`; `existing.motivos.extend(exame.motivos)`; `existing.pendencias_anexadas.extend(exame.pendencias_anexadas)`. Executam sempre que a checagem de igualdade não dispara `raise` — não dependem de quão exata foi a igualdade.
- O ÚNICO eixo comparado para decidir conflito são os dois campos de periodicidade (`periodicidade_meses`, `periodicidade_apos_15a`), por igualdade estrita (`consolidacao.py:46-49`). Qualquer divergência em qualquer um → `raise ConflitoProtocolo` imediato, sem merge parcial.
- `ExameEmitido` (`tipos.py:157,160`) tem `periodicidade_meses: int` + `periodicidade_apos_15a: Optional[int] = None`. Suporta piso component-wise sem mudança de tipo.
- `motivos` é só concatenado (`extend`), nunca deduplicado nem filtrado nem "escolhido"; `regra_id` vive dentro de cada `Motivo`, nunca em campo de `ExameEmitido` escolhido. `base_normativa` é metadado de `regras.yaml`, não chega ao runtime.

**Decisão.** Periodicidade divergente no mesmo exame **nunca foi contradição de protocolo** — é composição resolvível célula a célula: o exame mais frequente cobre a necessidade do menos frequente, sempre. Tratá-la como `ConflitoProtocolo` (desenhado para captura de contradição irresolvível, D-ARQ-15) é falso positivo. A correção é da semântica do estágio, não regra clínica nova.

1. No caminho de convergência do Stage 8, o gate de entrada troca de `igualdade-ou-raise` (`consolidacao.py:46-49`) para **sempre calcular o mínimo**: `existing.periodicidade_meses = min(existing.periodicidade_meses, exame.periodicidade_meses)` e `existing.periodicidade_apos_15a = min(...)` tratando **`None` como +∞ nos DOIS campos**.
2. As três mutações incondicionais (`consolidacao.py:58-60`: momentos `|=`, motivos `extend`, pendencias_anexadas `extend`) ficam **intactas, no lugar**. São agnósticas a "match exato" vs. "piso calculado" — não precisam ser duplicadas nem movidas. Proveniência (`motivos`) e teto bloqueante (`pendencias_anexadas`) preservados de ambos os lados por construção, não por cláusula nova.
3. O único código genuinamente novo são as duas atribuições de mínimo da cláusula 1 — hoje ausentes porque, ao chegar ao caminho de convergência, os campos já eram iguais por construção do `if`.
4. **`None` = +∞ nos dois campos é semântica obrigatória.** Caso concreto: sílica-sem-medição (`R-RX-01-sem`: 24M base, 12M após 15a) × fumos (`R-RX-02`: 60M base, `apos_15a=None`) → piso `min(24,60)=24` base, `min(12,+∞)=12` após 15a. A linha herda o encurtamento da regra que o tinha — "mais frequente cobre menos frequente" vale célula a célula. Sem `None`=+∞, `apos_15a=None` quebraria o `min`.
5. O `raise ConflitoProtocolo` é removido do **caminho de periodicidade divergente deste loop de dedup** — perde esse disparador específico. O tipo `ConflitoProtocolo` permanece como veículo de captura por-GHE de D-ARQ-15 (`except ConflitoProtocolo` no orquestrador segue válido para outros call-sites, se houver). Esta decisão NÃO afirma que era o único `raise` do arquivo — afirma que era o único do caminho de periodicidade divergente do dedup.

**Procedência.**
- Caso-âncora **vivo**: sílica×fumos no RX (24M×60M→24M base / 12M após 15a), presente no diagnóstico Viverde. `[DERIVADO — D-ARQ-31 fatia 3 recorte; saída real de consolidacao.py]`
- Piso clínico **iminente** (R-CLI-01×R-CLI-02 → semestral vence anual), motivação da fatia (c) de D-ARQ-38, ainda SEM código (R-CLI-* inexistente em `regras.yaml`, verificado nesta sessão). `[DERIVADO — R-CLI-02 ("uma única linha semestral, não duplicar") + R-GHE-03]`
- Generalização do mesmo mecanismo aos demais exames (não só clínico/RX) `[INTERPRETADO — prioridade na revisão de saída]` — universal por análise (mais-frequente-cobre-menos-frequente), sem âncora clínica por exame.
- Preservação de `motivos`/`pendencias_anexadas` no piso `[DERIVADO — mutações incondicionais já presentes, consolidacao.py:58-60]`

**Consequência.**
- Mata o falso-bloqueio à espreita: o primeiro GHE com sílica+fumos ambos determinados (RX 24M×60M — iminente assim que a fração da sílica for fornecida) deixaria de bloquear indevidamente. É a classe de erro que D-ARQ-22 combate, plantada de propósito no all-or-nothing de periodicidade.
- O requisito de segurança piso-sem-teto de D-ARQ-31 (pendência bloqueante anexada à linha nunca perdida quando há piso) fica garantido **por construção**, não por vigilância: a linha 60 (`pendencias_anexadas.extend`) já roda no caminho de convergência, incondicional. O auditor `auditar_invariante_piso_teto` (003.E, camada de teste) cobre a regressão.
- Toca só `consolidacao.py` (loop de dedup). `ExameEmitido` intacto. Cada mudança com teste que falhe sem ela e passe com ela (metodologia): caso de piso base; caso de piso `apos_15a` com `None`=+∞; preservação de `pendencias_anexadas` no piso (asserção de não-regressão sobre a linha 60); preservação de `motivos`.
- Universal (D-ARQ-06): expresso em termos de exame convergente, vale para construção, química, saúde, mineração. Não é regra de clínico×clínico nem de sílica×fumos.

**Nota de implementação obrigatória (regressão Viverde tri-estado).** A fatia IMPL recompõe a forma dos GHEs afetados pelo piso. GHEs que hoje são BLOQUEADA (ou levantam `ConflitoProtocolo`) por convergência de periodicidade — sílica×fumos no RX é o caso vivo — passam a VÁLIDA/PARCIAL com linha emitida + pendência anexada. Isso é **mudança de forma esperada, não regressão**: a regressão Viverde tri-estado dos 32 GHEs (D-ARQ-31 fatia 4, 003.E) DEVE ser recomputada e reasserida na fatia IMPL. Falha da suíte por GHE que mudou de BLOQUEADA→PARCIAL onde o piso agora emite é esperada e deve atualizar a asserção, não ser tratada como bug.

**Nota de aplicação 003.EE (IMPL) — duas correções de procedência medidas.**
- *Cláusula 1, redação.* "`None` como +∞ nos DOIS campos" é imprecisa: `ExameEmitido.periodicidade_meses`
  é `int` não-Optional (`tipos.py:270`) e `emissao.py:87` o constrói com `int(...)`. `None` é irrepresentável
  nesse campo; a IMPL trata `None`=+∞ só em `periodicidade_apos_15a`, que é o único Optional. Refinamento de
  redação, mesma ID — a semântica do piso não muda.
- *Nota de implementação obrigatória, REFUTADA POR MEDIÇÃO.* A nota previa GHEs mudando de BLOQUEADA para
  PARCIAL/VÁLIDA e qualificava sílica×fumos como caso-âncora **vivo**, "presente no diagnóstico Viverde".
  Medição em três vias sobre `agente_medico/tests/fixtures/pgr_viverde.py`. **(a) Explícita:** `fumos_metalicos`
  tem zero ocorrências como `RiscoPGR`; as 4 ocorrências de `silica` têm todas `quantificacao` preenchida, logo
  `silica_asbesto_sem_medicao` não dispara em GHE nenhum. **(b) Implícita por cargo:** o único cargo que injeta
  `fumos_metalicos` é `soldador` (`cargos.yaml:3`), ausente da fixture; o GHE de solda é
  `Est-09 "Solda / serralheria"`, com `cargos=("serralheiro","meio_oficial_serralheiro","servente")`, os três com
  `riscos_implicitos: []` — o que **não é lacuna, é R-GHE-05 `[VALIDADO]` cumprida**: "o campo `riscos_implicitos`
  só contém riscos indissociáveis. Serralheiro NÃO recebe {solda, fumos_metalicos, manganes} ali". Os 39 cargos da
  fixture estão todos em `cargos.yaml`, zero órfãos. **(c) Por operação confirmada:** não existe — `GHEPGR` não
  modela operações; **D-ARQ-23 é PROPOSTA, não implementada**. Regressão tri-estado dos 32 GHEs recomputada e
  **inalterada**; lista de GHEs afetados **vazia**.
  **Causa estrutural nomeada (não coincidência de fixture).** As três vias de entrada de `fumos_metalicos` estão
  fechadas ao mesmo tempo, por razões distintas e todas já documentadas: (a) o PGR não declara o agente, (b) a
  regra clínica validada proíbe atribuí-lo por cargo, (c) a via que o resgataria depende de D-ARQ-23, ainda
  PROPOSTA. Enquanto D-ARQ-23 não for implementada, o caso-âncora de D-ARQ-39 é **inalcançável por construção**
  no acervo Viverde. Já registrado na "Nota de implementação (002.M)" de R-GHE-05, que documenta Est-09 nominalmente
  (declara `radiacao_uv_ir` + `dioxido_de_titanio`, descreve solda em ET38-ET42, não declara fumos nem cromo) e
  conclui: "divergência esperada e rastreada, não erro do fixture". Nada a acrescentar ao PROTOCOLO — a emenda só
  passa a citá-lo.
  **Origem provável do erro de procedência** `[INTERPRETADO — não verificado contra o que o autor de 003.AF consultou]`:
  o cromo do serralheiro Viverde aparece na RQ.61, que é matriz de **saída** validada, não no PGR de **entrada**
  (nota 002.M de R-GHE-05). Qualificar como "vivo na entrada" um agente que só existe na saída é confusão de
  camada, não descuido de redação.
  **Procedência do artefato citado, resolvida:** `git ls-files` não retorna nenhum arquivo versionado com "diagnost"
  — não existe "diagnóstico Viverde" no repo; a procedência apontava para fora do versionado, não auditável. O
  `[A MEDIR]` da redação anterior fica **FECHADO** por esta medição.
  A âncora era **iminente**, não viva — mesma classe de erro que 003.EC (DT-003EB-01) e 003.ED (DT-003DV-01).
  D-ARQ-39 entra em produção **latente**.
- *Cláusula 5, medida além do que ela afirmava.* A cláusula recusou-se a afirmar que o `raise` do dedup era o único
  do arquivo. Medição: `grep -rn "raise ConflitoProtocolo" --include=*.py .` retorna **zero** no repo inteiro após
  esta IMPL. `ConflitoProtocolo` (`consolidacao.py:6`) e o `except` (`orquestrador.py:52`) permanecem definidos e
  inalcançáveis. Decisão: MANTER ambos — o veículo de captura por-GHE de D-ARQ-15 segue sendo contrato, e removê-lo
  exigiria revogar D-ARQ-15 nesse ponto. Registrado como DT-003EE-01, não-bloqueante.

**Nota de aplicação 003.EG (correção de procedência, mesma ID, status inalterado).** O
fechamento de 003.EE atribuiu a latência do caso-âncora a D-ARQ-23 ainda PROPOSTA (via "operação
confirmada"). Medição da rodada Fascino (`003eg_fascino_rodar.md`, commit `5a2d15b`): a rota de
convergência do dedup **passou a ter tráfego** — duas linhas de `audiometria` unificam motivos de
mais de uma regra: `[R-PKG-ATIVCRIT, R-VIB-02]` e `[R-PKG-ATIVCRIT, R-AUD-01]`. O disparador real
foi o alias Tier 1 de "Trabalho em Altura" (003.ED, D-ARQ-67), não D-ARQ-23 — a via viva não é a
que a nota de 003.EE apontava. **Status permanece LATENTE**: as duas convergências medidas são
ambas 12M, logo o piso component-wise (`min` entre periodicidades distintas) segue sem exercício
— o que roda hoje é dedup de motivos (`motivos.extend`, cláusula 2), não a cláusula 1 (`min`).
Corrige-se a causa atribuída à latência, não o veredito.

**Fronteiras (não confundir):**
- **D-ARQ-31** — não revoga; completa o recorte que a nota da fatia 3 (003.D) deixou explicitamente aberto. O requisito piso-sem-teto da fatia 3/4 é preservado por construção (cláusula 2).
- **D-ARQ-15** — `ConflitoProtocolo` como veículo de captura por-GHE permanece; perde só o disparador de periodicidade divergente do dedup. REJEITADO/PRELIMINAR/OK intactos.
- **D-ARQ-16 / R-GHE-03** — base conceitual: regras componíveis, convergência por dedup no Stage 8, nunca fusão de regras. Esta decisão é a consequência lógica de tratar periodicidade como componível também — o piso é dedup, não fusão (as regras permanecem distintas; só a linha emitida compõe).
- **D-ARQ-19** — o piso opera nos dois escalares que ela definiu (`periodicidade_meses`, `periodicidade_apos_15a`); component-wise honra a semântica "segunda metade da mesma grandeza".
- **D-ARQ-38** — pré-condição da fatia (c): R-CLI-02 não emite linha sem este seam resolvido. A fatia (c) é, na ordem real: este seam (003.AF) → R-CLI-01 IMPL → R-CLI-02 IMPL (R-CLI-* inexistente em código, verificado nesta sessão).
- **R-CLI-01/02, R-RX-01/02** — IDs e semântica intactas; nenhuma regra clínica criada ou alterada. Esta decisão é contrato de motor.

**Base.** Sessão 003.AF (22/06/2026). Resolve o recorte de dedup convergente que D-ARQ-31 fatia 3 deixou aberto; pré-condição de D-ARQ-38 fatia (c). Gate de estado real: `consolidacao.py:20-70`, `tipos.py:157-161` lidos em disco — `ConflitoProtocolo` por periodicidade é o único eixo de conflito do dedup; mutações de momentos/motivos/pendências já incondicionais. Passada adversária (gatilho "qual a melhor saída" + duas passadas de verificação): refutou unificação-sem-ler-branch (resolvida — caminho já é único), apagamento-de-proveniência (fantasma — `motivos.extend` já aditivo), âncora trocada (corrigida — vivo é RX, clínico é iminente). Decisão de arquitetura — sem código. Implementação (substituição do gate + duas atribuições de mínimo + recomputação da regressão Viverde) é sessão IMPL futura.

## D-ARQ-40 — Ponto de entrada de produção do motor novo é uma fachada que esconde a construção do índice CAS; harness, não travessia de PGR real

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação (módulo + função + testes) é a 003.AK. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** O gate de estado real desta sessão (três greps em disco) estabeleceu três fatos que reescrevem o foco herdado do handoff 003.AJ ("plugar `executar_com_composicao` no pipeline de produção"):
- `executar()` (orquestrador) **não tem chamador de produção**. Os hits de `executar` em `app.py` são `_executar_extracao` (flag de `session_state` do Streamlit), falso positivo sem relação com o motor médico.
- `executar_com_composicao` (wrapper forma α, D-ARQ-37/003.Z) tem **um único chamador: `test_composicao_propaga_pendencias.py`**. Confirmado de disco, não de handoff.
- **Não existe ponto de entrada do motor novo.** Zero `__main__`/`argparse`/`def main`/`click` em módulo de produção dentro de `agente_medico/`; o único hit é `__main__` de teste manual em `test_integracao_viverde.py`. `app.py` (Streamlit, raiz) é o legado, aposentado por D-ARQ-25 Parte A — não portado, não evoluído.

Logo "plugar em produção" pressupunha um "produção" que não existe. A 003.AJ não decide *onde* o wrapper encaixa num pipeline — decide se o motor novo **ganha** um ponto de entrada de produção agora, e com que forma. `[DERIVADO — saída real dos três greps, 003.AJ]`.

**Decisão.** O motor novo ganha um ponto de entrada de produção agora, como **fachada fina** sobre o wrapper existente, em módulo greenfield `agente_medico/motor/entrada.py`, função `processar_pgr`. Quatro cláusulas:

1. **Duas portas, não uma.** `executar_com_composicao` (wrapper, índice CAS explícito na assinatura, testável isoladamente, ponto de injeção da transcrição-LLM futura) permanece **intocado**. `processar_pgr` é uma camada **acima**: constrói/fecha o `indice_cas` internamente e o esconde do chamador. A porta de baixo é a costura mecânica testável; a de cima é a fachada de produção que recebe só o que o mundo real tem. `processar_pgr` não reimplementa nada do wrapper — é composição, não cópia (a resolução de composição via `gate_cas` já vive dentro de `resolver_composicao`, dentro do wrapper). `[INTERPRETADO — recomendação do Arquiteto; Diovanni não objetou. NÃO é decisão validada do Diovanni: o item "uma vs. duas portas" foi colocado e não contestado, não escolhido explicitamente.]`

2. **A decisão é o princípio "a fachada esconde a mecânica do índice do chamador", NÃO uma assinatura concreta.** O contrato de arquitetura é: quem chama o motor em produção fornece um PGR e o protocolo, não sabe montar o índice CAS — isso é mecânica interna, escondida pela fachada. A aridade exata de `processar_pgr` (quantos parâmetros; se carrega vocabulário; de onde vem o índice) **não é decidida aqui** — é consequência do que a 003.AK medir em disco (ver cláusula 4). A forma `processar_pgr(pgr, protocolo, hoje=None) -> Resultado` é **exemplo ilustrativo provisório, não cláusula**: só vale se o `indice_cas` for derivável do `Protocolo` que entra; se o vocabulário de agentes morar separado do `Protocolo`, a assinatura ganha entrada (ou a fachada carrega o vocabulário ela mesma) e o princípio "esconder do chamador" se mantém com forma diferente. Cravar a assinatura aqui seria literal sem fonte de disco — barrado pelo gate de procedência (D-ARQ-22).

3. **Contrato de entrada é `tipos.PGR` cru** (D-ARQ-25 Parte A literal — "o contrato de fronteira é `tipos.PGR`, sem intermediário"). `processar_pgr` **não** parseia PDF/docx, **não** normaliza vocabulário, **não** chama LLM. Recebe `tipos.PGR` já estruturado, com composição crua (componentes com CAS transcrito, `agente=None` antes do gate) — exatamente o que a `fds_t65` crua é hoje. `processar_pgr` é o lugar onde a transcrição-LLM (D-ARQ-25 Parte B) injetará seu output no futuro; a assinatura é **estável a essa injeção** — quando o extrator chegar, muda a *origem* do `pgr`, não a fachada. Construir a tomada antes do extrator é a ordem natural (a casa antes do morador). `[DERIVADO — D-ARQ-25 Parte A/B; D-ARQ-37 (wrapper é ponto de injeção)]`.

4. **Rótulo de escopo (cravado para não inflar em releitura futura): harness de produção, não travessia de PGR real.** Até a transcrição-LLM (D-ARQ-25 Parte B) existir, a única origem de `tipos.PGR` é fixture escrita à mão. O ponto de entrada estar pronto **não** significa que o motor processa PGR real — significa que a tomada está construída. O salto de produção real (PDF/docx → `tipos.PGR`) segue a jusante, em D-ARQ-25 Parte B, declarado e não mascarado. Espelha a honestidade-de-escopo de 003.W/003.X: a fatia move a fronteira do wrapper-só-em-teste para o wrapper-com-fachada-de-produção; a entrada ainda é fixture. Mesmo padrão, passo seguinte.

**CLI: extensão futura, não esta decisão.** Um CLI presume um consumidor de linha de comando e um arquivo PGR a parsear — ambos inexistentes (a entrada é `tipos.PGR` em memória, de fixture). CLI hoje seria casca em volta de fixture (fiação fantasma, D-ARQ-22). Adicionável trivialmente **quando** houver parse de PGR real (que é D-ARQ-25 Parte B). `[INTERPRETADO]`.

**Consequência.**
- Dá ao motor novo a fachada de produção que ele nunca teve, sem tocar o legado (`app.py` Streamlit intocado, aposentado por D-ARQ-25). Greenfield — sem decisão de fronteira com o legado.
- O wrapper `executar_com_composicao` (D-ARQ-37) permanece o ponto de injeção testável e o lugar da transcrição-LLM; a fachada não o substitui nem o altera.
- A estabilidade da assinatura de `processar_pgr` à injeção futura do extrator é a entrega de design: a tomada não se mexe quando o extrator plugar.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado). Cria contrato de ponto de entrada.

**Aberto para a 003.AK (gate de estado real obrigatório antes de qualquer prompt cirúrgico):**
- `git grep` de `processar_pgr` e `entrada.py` — confirmar greenfield **quanto a colisão E quanto a encaixe**: se já existe um `motor/__init__.py` que re-exporta API pública ou módulo de fachada parcial, `entrada.py` pode não ser o lugar arquitetural certo. Não verificado nesta sessão. `[A CONFIRMAR — git, 003.AK]`.
- **Origem do `indice_cas` — pode forçar revisão da assinatura (cláusula 2):** confirmar se `construir_indice_cas` se alimenta do `Protocolo` que entra em `processar_pgr` ou de um vocabulário (`agentes.yaml`) carregado separadamente. Se separado, a assinatura ganha entrada ou a fachada carrega o vocabulário. `[A CONFIRMAR — git, 003.AK]`.
- Forma da construção do índice (import-time / cache / por-chamada) — decisão de implementação dependente de como o vocabulário é carregado hoje. `[A CONFIRMAR — git, 003.AK]`.
- Passada adversarial extra sobre o prompt cirúrgico antes de emitir (toca orquestrador + ponto de entrada novo — caminho compartilhado, per 003.W).
- Reconfirmar 420/420 por pytest real antes de tocar arquivo.

**Fronteiras (não confundir):**
- **D-ARQ-37** — intocada: o wrapper `executar_com_composicao(pgr, protocolo, indice_cas, hoje=None)` permanece com índice explícito, é a porta de baixo. `processar_pgr` é a porta de cima que o consome. Forma α preservada.
- **D-ARQ-25** — Parte A é o contrato de entrada (`tipos.PGR` cru); Parte B (transcrição-LLM) é o salto a jusante que a fachada declara, não implementa. `processar_pgr` é a tomada da Parte B.
- **D-ARQ-09/15** — `executar()` permanece intocado, puro, indiferente a `indice_cas`. A fachada não altera o motor médico.
- **Inversão de sequenciamento A→B** — registrada como decisão de processo (DECISOES v55/v56, PAINEL), **não** D-ARQ numerado. D-ARQ-40 é contrato de motor (ponto de entrada), distinto daquela — não a re-registra.

**Base.** Sessão 003.AJ (23/06/2026). Gate de estado real: três greps em disco (`executar` fora de teste / `executar_com_composicao` / entry-points em `agente_medico/`) — não há ponto de entrada do motor novo, `app.py` é legado/falso-positivo. Duas passadas adversariais sobre a síntese: a 1ª rebaixou greenfield-de-`entrada.py` e origem-do-índice a condicionais de disco; a 2ª corrigiu (i) procedência de "duas portas" (recomendação do Arquiteto, não decisão do Diovanni), (ii) assinatura concreta saindo do corpo da decisão para exemplo provisório, (iii) encaixe-do-arquivo como questão de design da AK além de colisão. Decisão de arquitetura — sem código. Implementação é 003.AK.

**Aplicação na sessão 003.AK (24/06/2026) — IMPLEMENTAÇÃO (fachada `processar_pgr`).** Os três condicionais de disco da cláusula 4 caíram a favor da forma ilustrativa. `construir_indice_cas` (`resolvedor.py:36`) recebe `agentes_vocab: dict[str, Any]`, derivável de `Protocolo.vocabulario.agentes` — os chamadores reais já o alimentam assim; logo a assinatura `processar_pgr(pgr, protocolo, hoje=None) -> Resultado` se sustenta sem parâmetro extra (cláusula 2 resolvida a favor do exemplo). `entrada.py` greenfield (G1 zero hits em código; G3 `motor/__init__.py` vazio, sem fachada parcial a respeitar). Corpo: `executar_com_composicao(pgr, protocolo, construir_indice_cas(protocolo.vocabulario.agentes), hoje)` — esconde a mecânica do índice do chamador (cláusulas 1/2), composição não cópia, sem `try/except` (ValueError de colisão CAS propaga). Item B (re-export canônico em `motor/__init__.py`: `from .entrada import processar_pgr` + `__all__`) incluído, `[INTERPRETADO]` não-objetado. Wrapper `executar_com_composicao`, `executar()`, `resolver_composicao`, `gate_cas`, legado `app.py` INTOCADOS (cláusula 3, fronteiras). Harness, não travessia: entrada por fixture, salto de produção real segue em D-ARQ-25 Parte B (cláusula 4 honrada). 4 testes em `test_entrada_processar_pgr.py` (fachada constrói o índice; equivalência ao wrapper por `status`+contagens, não `==` de `Resultado` mutável; repasse de `hoje`; import canônico). Desvio de teste reportado e corrigido (calibração de `hoje` vs. limiar R-PGR-06 de 730 dias → `date(2027,1,1)`) → DT-003AK-01 (dívida de teste, não-bloqueante). Suíte 420→424 verde; mypy --strict delta-zero (26 pré-existentes, DH-003P-01). Commit `a378999`, merge `ee233b4` (PR #104, "Create a merge commit"). D-ARQ-40 fechado.

## D-ARQ-41 — Camada de extração é bicamada (transcritor-LLM + resolvedor determinístico); a fronteira é um contrato transcrito tipado; parse-PGR e transcrição-FDS são duas instâncias do mesmo padrão

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação por fatias futuras (transcrição-FDS tem resolvedor pronto; parse-PGR é greenfield). Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-25 Parte B ("normalização de vocabulário é responsabilidade da extração, a montante do motor; mecanismo é decisão de implementação") nunca decidiu o mecanismo, e o parse-PGR (PDF/docx → `tipos.PGR`) é greenfield, zero código (confirmado en passant em D-ARQ-40). D-ARQ-36 resolveu UMA metade da extração — a transcrição-FDS — como bicamada (LLM-transcrição + resolvedor determinístico, fronteira "CAS transcrito"), e deixou `name→slug` explicitamente fora ("o resolvedor só resolve CAS→slug; `name→slug` permanece indecisa em D-ARQ-25 Parte B"). Esta decisão NÃO implementa o parse-PGR: decide o **padrão** da camada de extração inteira e nomeia a **fronteira** do parse-PGR, fechando o nó topológico que D-ARQ-36 empurrou.

Passada de verificação que corrigiu o escopo: a simetria com D-ARQ-36 é real na topologia mas **assimétrica no peso**. Em D-ARQ-36 o resolvedor determinístico é substantivo (dígito verificador, índice exato, 4 ramos) porque CAS é token rígido. No parse-PGR o resolvedor (`termo→slug`) é quase vazio — toda a dificuldade real (as 6 formas de DT-003L-01, achar GHE, casar agente↔cargo na linha, ler quantificação) está na camada LLM. Logo a peça NOVA desta decisão não é "existe resolvedor depois" (D-ARQ-14 já o exige); é a **forma do contrato transcrito** que o LLM produz. Tratar a topologia como a decisão enterraria essa peça.

**Decisão — três partes.**

*Parte 1 — o padrão da extração é bicamada: transcritor-LLM + resolvedor determinístico, separados por um contrato transcrito tipado.* Generaliza D-ARQ-36 de "caso do CAS" para **o padrão de toda extração documento→`tipos.PGR`**. O transcritor-LLM lê o documento heterogêneo e produz um contrato intermediário estruturado com termos em linguagem natural (não normalizados); o resolvedor determinístico recebe esse contrato e o normaliza para os tipos canônicos. A fronteira LLM↔determinístico é o contrato transcrito — o ponto exato em que D-ARQ-09 se aplica. Razão de não ser monocamada (LLM recebe o vocabulário no prompt e já cospe slug): perderia o gate de admissão — o LLM escolheria o slug em silêncio, e slug errado entraria sem sinal, a classe de erro que D-ARQ-22 combate. A bicamada mantém a escolha de slug como decisão **determinística e auditável**; o LLM só transcreve o que está escrito. `[DERIVADO — D-ARQ-36 cl.1 generalizada; D-ARQ-09; D-ARQ-22]`.

*Parte 2 — o contrato transcrito do parse-PGR ("PGR transcrita") é estrutura `GHEPGR`-shaped com termos crus + FDS apontadas, NÃO `tipos.PGR`.* `tipos.PGR` é o que sai **do resolvedor**, não do LLM. A "PGR transcrita" carrega: a árvore de GHEs com `id`/`nome`; cargos, riscos, EPIs como **texto em linguagem natural**; quantificações como transcritas (valor + unidade + qualificador em texto); e **FDS apontadas** (referência ao documento de composição, não a composição resolvida). A forma exata desse tipo intermediário (dataclass própria vs. dict estruturado vs. `tipos.PGR` com campos-slug vazios) é decisão de implementação da fatia que construir o parse-PGR — o que se crava é a SEMÂNTICA: termos crus, FDS apenas apontadas, sem slug, sem composição resolvida. `[INTERPRETADO — a peça nova; sem âncora normativa, espelha o "CAS transcrito" de D-ARQ-36 P1]`.

*Parte 3 — `termo→slug` é determinístico e auditável; o LLM nunca escolhe slug; o MECANISMO FINO e a GRANULARIDADE ficam adiados por dependência de medição.* O resolvedor faz `termo→slug` contra o vocabulário (`agentes/cargos/exames/epis.yaml`); termo sem correspondência → `Pendencia(tipo="vocabulario_ausente", bloqueante=False)` (D-ARQ-14), o vocabulário cresce append-only alimentado pelas pendências. O QUE FICA ABERTO, por não ser decidível sem medir sobre os PGRs reais de DT-003L-01: a granularidade da fronteira — *quanto* o LLM normaliza antes de entregar o termo. CAS é token rígido (D-ARQ-36 funciona com índice exato); termo de risco é texto fluido ("ruído" / "ruído contínuo" / "exposição a ruído acima de 85 dB"), e um casamento exato geraria falso `vocabulario_ausente`. Três saídas candidatas, a escolher na implementação medindo onde os falsos caem: (a) LLM transcreve verbatim + resolvedor normaliza agressivo (lowercase/strip/remove qualificador) + dicionário de sinônimos; (b) LLM normaliza linguisticamente para um termo-conceito + resolvedor faz só conceito→slug; (c) híbrido — dicionário resolve o conhecido, o resto vira candidato-LLM de baixa confiança para revisão humana, espelhando a zona R-FDS-04 de D-ARQ-36 P1. Cravar (a)/(b)/(c) agora seria `[INTERPRETADO]` disfarçado de derivado; o adiamento é por dado ausente, não indecisão — mesmo molde de D-ARQ-38 (emissor de biomonitoramento adiado pelo mapa agente→biomarcador). `[DERIVADO — D-ARQ-14; molde de adiamento-por-dado de D-ARQ-38]`.

**Consequência.**
- Eleva o padrão bicamada a contrato de toda a extração: parse-PGR e transcrição-FDS são duas INSTÂNCIAS do mesmo padrão, com transcritores-LLM e resolvedores distintos por documento-fonte, não dois desenhos.
- Dá forma à fronteira do parse-PGR ("PGR transcrita") que D-ARQ-25 dava só como prosa.
- Determinismo do motor intacto (D-ARQ-09): toda LLM (estruturação do PGR, transcrição da FDS) fica a montante das duas fronteiras transcritas; os resolvedores e o motor são puros.
- Honestidade de escopo: esta decisão fecha topologia + fronteira + princípio do gate de slug. NÃO fecha o mecanismo fino do `name→slug` (adiado por medição), nem a ordem de implementação, nem o prompt, nem a forma do campo de sinônimos, nem as 6 formas de DT-003L-01 (input da implementação).
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado). Cria contrato de camada.

**Fronteiras (não confundir):**
- **D-ARQ-25 Parte B** — esta decisão é a forma que a Parte B dava como guarda-chuva: nomeia a fronteira do parse-PGR e generaliza o padrão. `tipos.PGR` segue o contrato de saída (Parte A); a "PGR transcrita" é upstream dele.
- **D-ARQ-36** — não revoga; é a instância-FDS do mesmo padrão. "CAS transcrito" e "PGR transcrita" são as duas fronteiras transcritas. O resolvedor da FDS (`gate_cas` 003.S/T + `resolver_composicao` 003.W) já existe e está costurado (003.Z); o do PGR (`termo→slug`) é greenfield. A "PGR transcrita" entrega `ProdutoQuimico.fds.composicao` CRUA (componentes com CAS transcrito, `agente=None`); `resolver_composicao` a resolve a jusante — o parse-PGR é upstream do encanamento químico existente, não o reconstrói.
- **D-ARQ-09** — preservada: as duas fronteiras transcritas são onde a LLM para e o determinístico começa.
- **D-ARQ-14** — reusado: termo cru sem slug → `vocabulario_ausente` não-bloqueante; vocabulário append-only.
- **D-ARQ-18 cl.3** — retoma o candidato `exames.yaml.sinonimos` (campo de sinônimos "candidato separado e não decidido"): volta à mesa como uma das saídas da Parte 3, decidido na implementação, não aqui.
- **D-ARQ-22** — a recusa da monocamada é a mitigação do erro silencioso plausível (slug escolhido pelo LLM sem auditoria).
- **D-ARQ-38** — molde do adiamento-por-dado: como o emissor de biomonitoramento esperou o mapa agente→biomarcador, o mecanismo do `name→slug` espera a medição sobre os PGRs de DT-003L-01.
- **DT-003L-01** — input empírico da implementação (as 6 formas de declaração química no PGR que o transcritor-LLM tem de aguentar); não é resolvida aqui.

**Base.** Sessão 003.AL (25/06/2026). Generaliza D-ARQ-36 cl.1; nomeia a fronteira do parse-PGR; fecha o nó topológico de D-ARQ-25 Parte B. Três passadas adversariais: (1ª) bicamada simétrica a D-ARQ-36; (2ª) achou a assimetria de peso — o resolvedor do PGR é quase-vazio, a peça nova é o contrato transcrito, não a topologia; (3ª) corrigiu o escopo — `name→slug` tem mecanismo adiado por medição (não fechado), e a metade quase-pronta da extração é a FDS (resolvedor existe), não a PGR. Decisão de arquitetura — sem código. Implementação por fatias futuras.

## D-ARQ-42 — Transcritor-FDS é a camada-LLM da instância-FDS de D-ARQ-41; contrato de saída é `tuple[Componente,...]` cravado; recorte (A) identidade+concentração; mecanismo adiado por medição

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação por fatias futuras; a medição que destrava o mecanismo é a 003.AN (CONHECIMENTO). Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-41 fixou o padrão bicamada de toda extração (transcritor-LLM + resolvedor determinístico, fronteira = contrato transcrito tipado) e nomeou as duas instâncias: parse-PGR (greenfield) e transcrição-FDS. A transcrição-FDS é a metade quase-pronta: o resolvedor determinístico da FDS JÁ EXISTE e está costurado fim-a-fim — `gate_cas` (003.S/T), `resolver_composicao` (003.W), propagação ao Resultado (003.Z), fachada `processar_pgr` (003.AK). Falta só a camada a montante do "CAS transcrito": o transcritor que lê o PDF da FDS e produz o contrato transcrito. Esta decisão fecha o **padrão e o contrato** dessa camada; NÃO a implementa.

**Gate de estado real (greps + literais em disco nesta sessão).**
- O contrato de saída do transcritor JÁ ESTÁ CRAVADO: não há tipo intermediário. `resolver_composicao` (`composicao.py`) consome `produto.fds.composicao` — `tuple[Componente, ...]` — e roda `gate_cas` componente a componente. O transcritor produz exatamente isso. `Componente` (`tipos.py`): `cas: str`, `nome: str`, `concentracao: Optional[FaixaConcentracao]`, `agente: Optional[str] = None`, `is_carcinogeno_iarc: bool = False`, `is_sensibilizante: bool = False`. `[DERIVADO — tipos.py / composicao.py em disco]`.
- Transcritor é greenfield: `git grep` de `pdfplumber|pypdf|fitz|pymupdf|ia_client|extrair.*gemini` em `agente_medico/` + `scripts/` → zero hits. Não há parse de PDF de produção no motor novo. `[DERIVADO — grep, 003.AM]`.
- A fixture `fds_t65` (`tests/fixtures/fds_t65.py`) É o output-esperado do transcritor, transcrito à mão de 3 FDS reais (Ciplan / Adesivo Tigre / Tinta Acrílica). NÃO é a entrada — é metade do par (PDF, `Componente[]`). Os 3 PDFs-fonte existem em `fds_originais/` (Ciplan, Adesivo Tigre, Tinta Acrílica), confirmado por inspeção do diretório. `[DERIVADO — fds_t65.py + fds_originais/]`. O casamento arquivo↔função-fixture é `[INTERPRETADO — confirmar abrindo cada PDF na IMPL]`.

**Decisão — quatro partes.**

*Parte 1 — o transcritor-FDS é a camada-LLM da instância-FDS de D-ARQ-41, bicamada interna.* O transcritor é, ele mesmo, bicamada: **parse-PDF (determinístico)** lê o documento e extrai texto; **transcrição (LLM)** lê o texto e produz `tuple[Componente,...]`. A fronteira interna é "texto extraído do PDF" — a transcrição-LLM recebe texto, não bytes de PDF. Razão (D-ARQ-09): a leitura de bytes é determinística e testável sem API; misturá-la com a transcrição borraria a fronteira que sustenta a pureza. `[DERIVADO — D-ARQ-41 P1; D-ARQ-09]`.

*Parte 2 — contrato de saída é `tuple[Componente,...]` cru, cravado em disco; o transcritor NÃO inventa tipo.* Produz `Componente(cas=<transcrito>, nome=<transcrito>, concentracao=<FaixaConcentracao transcrita>, agente=None)`. NÃO resolve slug (downstream, `gate_cas`), NÃO corrige CAS (transcreve fielmente, inclusive o errado — TiO₂ `134363-67-7` da fixture cai no ramo (c) do gate por construção), NÃO classifica perigo (Parte 3). O contrato de saída é estável à substituição da entrada: quando o transcritor real existir, muda a *origem* da `tuple[Componente,...]`, não a fronteira que `resolver_composicao` consome. `[DERIVADO — composicao.py; D-ARQ-25 Parte A/B; D-ARQ-36]`.

*Parte 3 — recorte (A): transcreve identidade+concentração; flags de perigo NÃO são classificadas pelo transcritor — ficam no default-por-ausência, declarado como tal.* O transcritor emite `is_carcinogeno_iarc=False`/`is_sensibilizante=False` **por ausência de classificação, não por classificar como não-perigoso** — idêntico ao `False`-por-ausência que `resolver_composicao` já produz hoje. Isto NÃO é "não toca o tipo e ninguém grava nada": o transcritor grava `False`, e D-ARQ-22 nomeia o risco — `False` tipado é indistinguível de "classificado como não-sensibilizante". A defesa é a mesma de DT-003T-01 (recusa de `is_sensibilizante` no `EntradaIndice`): o `False` é default-por-ausência-de-dado, com autor declarado, não classificação. As frases-H/R do documento (notações BR/GHS/europeia entre as 3 FDS) **ficam fora desta fatia** — `Componente` não tem campo para frase-H crua, e adicioná-lo cruzaria DT-003M-01 (ramo-0-vs-bypass com CAS oculto) e DT-003T-01 (`is_sensibilizante` ausente do yaml), ambas ABERTAS. Caso-âncora do custo declarado: "Segredo Industrial 2" (Adesivo Tigre) — H334+H317 declarados na FDS, CAS oculto → `cas=""`, `agente=None`, flags `False` → ramo 0 → AUSENTE, mascarando o bypass-sensibilizante. **Não é regressão** (é o estado de hoje, registrado em DT-003M-01); (A) não piora, só não resolve. Perigo-transcrito entra em fatia própria, depois que DT-003M-01 decidir a ordem ramo-0-vs-bypass. `[DERIVADO — fds_t65.py; D-ARQ-22; DT-003T-01]`; o recorte (A) é decisão do Diovanni (confirmada nesta sessão).

*Parte 4 — princípio do gabarito: campos verificáveis deterministicamente ancoram; `nome` exige critério próprio; o mecanismo fino é adiado por medição.* O teste do transcritor compara a saída contra os campos-de-dado da `fds_t65` (não os comentários, que são anotação humana — ex.: o "CAS correto" do TiO₂ que o transcritor não conhece), com o LLM fixado/mockado — nunca testa a API. Rigor por-campo: `cas` exato (token rígido), `concentracao` numérica (tolerância clara); **`nome` é texto-livre-de-LLM e NÃO é gabaritável por `==`** (um LLM pode transcrever "Metiletilcetona (MEK)" / "MEK" / "Metil etil cetona" do mesmo PDF) — o critério de aceitação de `nome` é ele mesmo decisão aberta. O **mecanismo fino** do transcritor (OCR-ou-não no parse-PDF; prompt; tratamento das 3 notações; critério de `nome`; fronteira-OCR — ver abaixo) **fica adiado por medição sobre os 3 PDFs reais**, no molde de D-ARQ-41 P3 (que adiou `name→slug` por medição sobre os PGRs) e D-ARQ-38 (emissor adiado pelo mapa). Adiamento por dado ausente, não indecisão. `[DERIVADO — fds_t65.py; molde D-ARQ-41 P3 / D-ARQ-38]`.

**Fronteira-OCR (ponto aberto nomeado, não fechado).** Triagem-LLM dos 3 PDFs (Perplexity/GPT, 003.AM) aponta: os 3 têm camada de texto; **`01-Ciplan` é escaneado-com-OCR com ruído explícito** ("Start of OCR for page 1", caracteres corrompidos), enquanto Adesivo Tigre e Tinta Acrílica são texto nativo. `[INTERPRETADO — triagem LLM de segunda mão; confirmar por extração determinística na 003.AN]`. Consequência: o parse-PDF entrega texto sujo para 1 de 3 casos do próprio gabarito. Decisão aberta — o ruído de OCR é absorvido pelo LLM-transcritor (joga robustez no não-determinismo) ou tratado por etapa de limpeza determinística antes do LLM (testável, tira carga do LLM)? A forma depende de *quão* sujo o Ciplan está — medição da 003.AN. A fronteira-OCR existe e está nomeada; ignorá-la repetiria o erro que D-ARQ-41 evitou ao adiar `name→slug`.

**Consequência.**
- Fecha o padrão+contrato+recorte+princípio-de-gabarito da transcrição-FDS sem implementar — a metade quase-pronta da extração ganha sua decisão de fronteira antes do código.
- Dá gabarito de aceitação real (3 pares PDF↔`Componente[]` em disco) que prova o transcritor sem testar a API — destravando IMPL futura testável.
- Determinismo intacto (D-ARQ-09): toda LLM (parse-de-texto-sujo, transcrição) fica a montante do "CAS transcrito"; o resolvedor e o motor seguem puros.
- Honestidade de escopo: NÃO fecha mecanismo fino, fronteira-OCR, critério de `nome`, prompt, nem o estado real dos PDFs — todos adiados para a medição (003.AN). NÃO tira de produção: o salto real é a IMPL do transcritor + plug, fatias a jusante da medição.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado). Cria contrato de camada de extração-FDS.

**Aberto para a 003.AN (CONHECIMENTO/medição — gate de estado real obrigatório):**
- Extrair os 3 PDFs por ferramenta determinística (pdfplumber/pdfminer sobre os bytes) e confirmar/refutar a triagem-LLM: quais são texto-nativo, quão sujo é o OCR do Ciplan. `[A CONFIRMAR — extração, 003.AN]`.
- Confirmar o casamento arquivo↔função-fixture abrindo cada PDF (a transcrição à mão bate?). `[A CONFIRMAR — 003.AN]`.
- Medir a regularidade da seção 3 (composição) nas 3 notações (BR/GHS/europeia) — quão estruturável é cada uma → decide prompt e granularidade.
- Decidir a fronteira-OCR (LLM absorve vs. limpeza determinística) com o ruído real medido.
- Decidir o critério de aceitação de `nome` (normalização? casamento por CAS-primário com `nome` informativo? campo não-asserido?).

**Fronteiras (não confundir):**
- **D-ARQ-41** — esta decisão é a instância-FDS concreta do padrão que D-ARQ-41 fixou em abstrato. "CAS transcrito" (D-ARQ-36) e a saída do transcritor-FDS são a mesma fronteira vista dos dois lados.
- **D-ARQ-36** — o resolvedor da FDS (`gate_cas`) é intocado; o transcritor é a camada a montante dele que faltava. O transcritor produz a `Componente` crua que o gate já consome.
- **D-ARQ-25 Parte A/B** — Parte A é o contrato (`tipos.PGR`/`Componente` cru); o transcritor-FDS é uma das implementações da Parte B (extração a montante).
- **D-ARQ-09** — preservada: a fronteira parse-texto↔transcrição-LLM e o "CAS transcrito" são onde o LLM para e o determinístico começa.
- **DT-003M-01 / DT-003T-01** — referenciadas como fora de escopo (perigo-transcrito); sem mudança de status.
- **D-ARQ-22** — o `False`-por-ausência das flags (Parte 3) é risco residual da classe "erro silencioso plausível"; mitigação = declará-lo como default-por-ausência com autor, não mecanismo novo.

**Base.** Sessão 003.AM (25/06/2026). Fecha o padrão/contrato da transcrição-FDS, instância de D-ARQ-41. Gate de estado real: contrato de saída cravado (`tuple[Componente,...]`), transcritor greenfield (grep zero), 3 pares PDF↔fixture em disco. Três passadas adversariais sobre a síntese: (1ª) "(A) não toca o tipo" corrigido — (A) grava `False`-por-ausência com autor novo, declarado (D-ARQ-22); (2ª) "gabarito = saída == fixture" refutado — gabarito é por-campo, `nome` texto-livre-de-LLM não é `==`; (3ª) "fatia 1 de IMPL" refutado — a forma do transcritor depende de medir os 3 PDFs (estado/OCR/notações), adiada para CONHECIMENTO (003.AN), molde D-ARQ-41. Triagem-LLM dos PDFs tratada como pista (D-ARQ-30, aponta-não-afirma). Recorte (A) confirmado pelo Diovanni. Decisão de arquitetura — sem código.

**Aplicação na sessão 003.AS (29/06/2026) — IMPLEMENTAÇÃO (Parte 1, camada parse-PDF determinística).** Primeira fatia de IMPL do transcritor-FDS: a camada parse-PDF determinística (D-ARQ-42 Parte 1) materializada como `extrair_tabelas_fds(caminho) -> list[list[list[Optional[str]]]]` em módulo greenfield `agente_medico/motor/extracao_fds.py` (gate de não-colisão confirmado de disco: zero hits `extracao_fds`/`extrair_tabelas_fds`, `motor/__init__.py` só re-exporta `processar_pgr`). `pdfplumber.extract_tables()` puro sobre todas as páginas, achatadas numa lista (fronteira de página descartada — composição aparece em páginas variáveis; consumidor varre todas as tabelas). Devolve as tabelas CRUAS: não localiza composição, não interpreta coluna, não desambigua `\n`, não mapeia grafias de CAS-ausente, não monta `Componente` — tudo isso é transcrição (fatia futura). Recorte desceu na sessão de "extrai a tabela de composição" para "extrai as tabelas cruas da página": a medição (003.AS, `extract_tables` sobre os 6 PDFs de `fds_originais/`) provou que em Ciplan/Tigre a composição NÃO é tabela isolável — vem fundida num grid multi-seção, sem âncora de índice. Asserção literal forte só onde a composição está isolada com gabarito (tinta: header + 9 linhas + `\n`-intra-token do TiO₂ `134363-67-\n7`; Leinertex/Massa: `\n`-empilhado `2634-33-5\n55965-84-9`); asserção fraca (≥1 tabela, roda sem erro) onde está fundida (Ciplan/Tigre). As patologias de layout/transcrição que a medição expôs estão catalogadas em DT-003AS-01 (PROTOCOLO §11), input da fatia de transcrição. Isolado, sem consumidor (espelha o gate-CAS isolado da 003.S e o predicado isolado da 003.J): move a fronteira de fixture-crua para PDF-cru-extraído; não tira de produção (a transcrição que vira `Componente` é fatia a jusante, D-ARQ-25 Parte B). `[DERIVADO — medição 003.AS; D-ARQ-42 Parte 1; D-ARQ-43 Parte 1]`. Commit `8da2fed`, merge `567454e` (PR #115, "Create a merge commit"). Suíte 443→451 (+8); mypy --strict limpo em `extracao_fds.py`.

**Aplicação na sessão 003.AT (29/06/2026) — ARQUITETURA (mecanismo do transcritor-LLM: localização, nome, gabarito).** Fecha três dos pontos que D-ARQ-42 Parte 4 adiou por medição, agora decidíveis com DT-003AS-01 / D-ARQ-43 em mãos. (1) **Localização-de-composição por título normativo, não por número de seção.** A camada-LLM localiza a região pelo título `COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES` (início) até o título da seção seguinte (fim) — não por "seção 3" nem por índice de tabela. Razão: o título da seção é estável na NBR 14725:2023, mas o número varia por fabricante (Ciplan rotula "2", medido em DT-003AS-01); ancorar por número quebra no Ciplan, por título é robusto à renumeração. Limite declarado (D-ARQ-22, anti-falsa-completude): em grid-fundido (Ciplan/Tigre, patologia 1 de DT-003AS-01) a âncora localiza o **início**, não isola a grade — a leitura por bbox/posição (patologia 2) remanesce adiada. Opera sobre texto na camada-LLM; o parse-PDF determinístico (`extracao_fds.py`, 003.AS) é intocado. Keyed na NBR 14725 (escopo FDS-BR; não universal a FDS de outra norma-fonte). `[DERIVADO — convergência de fontes secundárias + literais de FDS reais; texto oficial ABNT é pago, não conferido — mais próximo de INTERPRETADO que de DERIVADO-norma na hierarquia de D-ARQ-22; a âncora-por-título não depende do número, logo o status frouxo da numeração não a enfraquece]`. (2) **Critério de `nome`: transcrito informativo, não gabaritado por `==`.** Formaliza D-ARQ-42 Parte 4 / D-ARQ-43 Parte 2 como cláusula: o teste assere `cas` (token rígido, exato) + `concentracao` (faixa numérica, tolerância); `nome` é texto-livre-de-LLM, não-`==` (quebras de linha layout-dependentes). Para CAS oculto (ramo d), `nome` é o único identificador e importa como dado, ainda não como asserção. `[DERIVADO — D-ARQ-43 Parte 2]`. (3) **Gabarito: par PDF↔fixture em disco, LLM fixado/mockado, nunca testa API.** Os 3 pares (Ciplan / Adesivo Tigre / Tinta Acrílica) em `fds_originais/` ↔ `fds_t65` são o output-esperado; o teste compara os campos-de-dado da fixture (não os comentários, anotação humana — ex.: o "CAS correto" do TiO₂ que o transcritor não conhece). `[DERIVADO — fds_t65.py + fds_originais/ em disco; D-ARQ-42 Parte 4]`. **Recorte (A) mantido:** frase-H/perigo fora; flags no default-por-ausência (Parte 3). Segredo Industrial 2 (H334+H317, CAS oculto) → ramo d → `cas=""` → AUSENTE; não resolvido aqui (DT-003M-01). **Adiado por medição para a IMPL** (molde D-ARQ-41 P3): prompt de transcrição; desambiguação `\n` por regex-CAS (patologia 3); dicionário de grafias-de-ausente → `cas=""` / ramo d (patologia 4); normalização de separador `-`/`–` (patologia 5) — catálogo em DT-003AS-01. Nenhuma regra clínica criada/alterada. Sem código.

**Aplicação na sessão 003.AU (29/06/2026) — IMPLEMENTAÇÃO (fatia 1 da camada de normalização do verbatim).** Patologias 3/4/5 de DT-003AS-01 materializadas como funções puras determinísticas em módulo greenfield `agente_medico/motor/transcricao_fds.py`, ISOLADO (sem LLM, sem montar `Componente`, sem consumidor — espelha gate isolado 003.S / parse isolado 003.AS). Fronteira da fatia: só a normalização determinística do verbatim; o LLM-transcritor (mockado) + montagem em `Componente` + contrato do verbatim transcrito (tipo intermediário, gêmeo da "PGR transcrita" de D-ARQ-41 P2) ficam para fatia futura. Três funções: `desambiguar_cas` (P3), `normalizar_cas_ausente` (P4), `parsear_faixa` (P5, sem ordenar — min/max é do resolvedor, `_normalizar_faixa` 003.AP). Refinamento da heurística P3 (corrige a spec do prompt): a regra dupla "preserva se ambos fragmentos bem-formados; junta se a junção é bem-formada" tinha buraco no TiO₂ — `134363-67-` passa o dígito isoladamente (coincidência), mas a junção `134363-67-7` FALHA (CAS real e errado do documento, ramo (c) do gate, DT-003AS-01); pela regra dupla o TiO₂ ficava indefinido. Regra corrigida: preserva o `\n` só quando AMBOS os fragmentos são bem-formados isoladamente (multi-CAS real); senão junta, sem exigir junção válida — validade é do `gate_cas` (D-ARQ-36), não da camada de forma. Limite residual (D-ARQ-22): falso-preserva se uma quebra produzir dois fragmentos ambos coincidentemente bem-formados — sem caso medido. `[DERIVADO — cas_bem_formado validado em disco, 003.AU; DT-003AS-01]`. `tipos.py`/`composicao.py`(`_explodir_multi_cas`)/`extracao_fds.py`/`resolvedor.py` INTOCADOS (só importa `cas_bem_formado`). 26 testes; suíte 451→477; mypy --strict limpo. Commit `0135754`, merge `f3452bb`, PR #118.

**Aplicação na sessão 003.AX (30/06/2026) — ARQUITETURA (patologias 1/2 de DT-003AS-01: mecanismo e representação-de-entrada do transcritor).** Fecha as duas patologias de layout que D-ARQ-42 Parte 1 / DT-003AS-01 deixaram abertas, com medição read-only de `extract_text`/`extract_words` sobre Ciplan e Tigre (espelha 003.AN/AS; não toca motor). (1) **Patologias 1/2 resolvem-se na camada-LLM lendo por sentido, não em parser determinístico por bbox/posição.** Forçado por três: (a) D-ARQ-41/42 já selaram transcrição-LLM porque os 4 layouts incompatíveis em 6 PDFs refutam parser de regra fixa; (b) universalidade — LLM semântico lê FDS de qualquer setor, bbox afinado a Ciplan/Tigre é solução-pontual; (c) o "exige heurística por bbox" da patologia 2 é evidência a favor do LLM, não mandato de construir heurística. (2) **A entrada do LLM é `extract_text` da região âncora-por-título, não `extract_tables`.** Medido: o título-âncora da 003.AT (`COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES`) sobrevive no `extract_text` e SOME no `extract_tables` do Tigre; e a patologia 2 (coluna deslocada que "perde faixa em silêncio") é **artefato do `extract_tables`** — no `extract_text` MEK e Acetato voltam com faixa (`10 – 42`, `05 – 30`), o texto linear lê o triplo inteiro. Ruído residual: colunas lado-a-lado intercaladas linha a linha (mobília de página), tolerada pelo LLM por reconhecimento do triplo nome+cas+faixa. Refinamento herdado à 003.AT (não a reabre): a âncora-por-título tolera título quebrado em linhas e intercalado. (3) **Consequência aberta — DT-003AX-01:** a virada `extract_tables → extract_text` desestabiliza, de uma vez, o MECANISMO de explosão multi-CAS do D-ARQ-45 (o `_explodir_multi_cas` depende do CAS empilhado `"2634-33-5\n55965-84-9"` numa célula única — formato que NÃO existe no `extract_text`, onde os CAS vêm em linhas separadas com a faixa do bloco em linha própria) E o papel do `extrair_tabelas_fds` da 003.AS como camada-de-entrada do transcritor. A DECISÃO do D-ARQ-45 (explodir 1 bloco → N componentes com herança-α da faixa, cruza D-ARQ-35) permanece; só o mecanismo `\n`-célula cai. A reconciliação texto-puro vs híbrido texto+tabelas — incluindo a associação faixa↔componente no bloco "Derivados de:", ambígua em texto linear — é passada dedicada, não esta. Recorte (A) mantido. Nenhuma regra clínica criada/alterada. Sem código. `[DERIVADO — medição read-only extract_text/words Ciplan+Tigre, 003.AX; D-ARQ-41/42; DT-003AS-01]`.

**Aplicação na sessão 003.AY (30/06/2026) — CONHECIMENTO/medição → ARQUITETURA (reconciliação DT-003AX-01: representação-de-entrada texto-puro + mecanismo de explosão multi-CAS).** Fecha a reconciliação que a nota 003.AX abriu (DT-003AX-01), por medição read-only de `extract_text`/`extract_tables` sobre os 6 PDFs de `fds_originais/` (espelha 003.AN/AS/AX; não toca motor). **Medido (disco):** (a) o bloco "Derivados de:" sobrevive no `extract_text` (header + N CAS + faixa única do bloco), mas a estrutura de linha morre — os CAS vêm em linhas separadas (sem o token empilhado `"2634-33-5\n55965-84-9"`) e a POSIÇÃO da faixa é instável entre FDS (Leinertex blk1: faixa em linha própria entre os 2 CAS; blk2: colada ao componente do meio; Massa: na 1ª linha, antes dos nomes); (b) o mesmo bloco no `extract_tables` é UMA linha perfeita — `cell[1]="2634-33-5\n55965-84-9"` (o `\n`-célula que `_explodir_multi_cas`/003.AR consome) + `cell[2]` com a faixa do bloco: agrupamento + associação-α de graça; (c) DISJUNÇÃO no acervo — blocos multi-CAS "Derivados de:" existem SÓ em Leinertex/Massa (table-isolável-limpo), e os grid-fundidos Ciplan/Tigre (que forçaram a virada p/ texto na 003.AX) NÃO têm bloco multi-CAS. **Decisão (1) — entrada TEXTO-PURO, não híbrido.** Uma só representação (`extract_text` âncora-por-título, 003.AT). Razões: universalidade (D-ARQ-06) — o híbrido (`extract_tables` p/ table-limpo + `extract_text` p/ grid-fundido) aposta que a disjunção dos 6 PDFs é estrutural, mas uma FDS grid-fundida COM bloco multi-CAS quebra-o; o roteador por-FDS do híbrido ("é grid-fundido?") é classificação nova e superfície de erro silencioso (misroteia → perde `\n`-célula ou perde título-âncora — classe D-ARQ-22); e a instabilidade de posição da faixa (medida) torna um parser-de-bloco-textual-determinístico inseguro, logo o agrupamento É semântico (LLM lê o bloco como unidade), mecanismo já selado em D-ARQ-41/42 — texto-puro não adiciona paradigma, híbrido adiciona roteador. **Híbrido é PALIATIVO** (sinalizado): reusa `_explodir_multi_cas` intacto mas não resolve "entrada universal", compra-o com roteador frágil + aposta na coincidência do acervo. **Decisão (2) — a explosão migra de `\n`-split p/ expansão-de-grupo no resolvedor; a DECISÃO do D-ARQ-45 permanece.** O LLM-transcritor emite o bloco "Derivados de:" como UM grupo verbatim (lista de CAS + a faixa única do bloco), preservando o agrupamento que o documento escreve (header + uma faixa); o resolvedor expande 1 grupo → N `Componente` com herança-α. Cardinalidade NÃO vai p/ o LLM (D-ARQ-45 Parte 1 honrada): o LLM não decide quantos nem copia α por-CAS — só transcreve o limite do bloco como desenhado. D-ARQ-45 Partes 1/2 (explodir + α, resolvedor-side) intactas; só o MECANISMO `\n`-célula (003.AR) muda. **Decisão (3) — `extrair_tabelas_fds` (003.AS) deixa de ser a entrada do transcritor.** Sob texto-puro a camada-LLM recebe `extract_text`, não `extract_tables`; `extrair_tabelas_fds` fica construído-isolado-não-consumido (estado da 003.AS) → candidato a DEPRECATED ou a cross-check determinístico, decidido na IMPL, não cravado aqui. **Aberto p/ a IMPL** (gate de estado real obrigatório): forma do verbatim-grupo (`BlocoVerbatim` envolvendo faixa+N(cas,nome) vs `ComponenteVerbatim` flat + `grupo_id`); `_explodir_multi_cas` (003.AR, `\n`-split) aposentado vs generalizado p/ expansão-de-grupo; destino do `extrair_tabelas_fds`. **Limites (D-ARQ-22):** "Derivados de:" como delimitador é DERIVADO de 3 blocos em 2 FDS (n pequeno; grupo sob outro header / sem header não-medido — o agrupamento-LLM-semântico é robusto a variação de string literal, argumento extra pró texto-puro); o LLM passa a carregar carga semântica BOUNDED (ler qual faixa única está no escopo do bloco) — defensável como transcrição (faixa escrita uma vez por bloco), resíduo candidato-revisado-pelo-RT (D-ARQ-33 cl.4), bounded porque não parte/copia/computa a faixa nem decide N. Recorte (A) mantido. `[DERIVADO — medição read-only extract_text/extract_tables dos 6 PDFs, 003.AY; D-ARQ-41/42/45; D-ARQ-06; D-ARQ-22]`. Resolve DT-003AX-01. Nenhuma regra clínica criada/alterada. Sem código.

**Nota 003.CH (10/07/2026) — recorte (B) perigo-transcrição ratificado como próxima frente do cluster-FDS.** O recorte (A) desta decisão (identidade + concentração) deixou as **frases-H / classificação de perigo FORA** de escopo, por design. A sessão 003.CH (CONHECIMENTO, reframe de DT-003M-02) mediu por git que esse recorte (B) excluído é o **pré-requisito duro** de três DTs abertas: DT-003M-01 (honrar frase-H de CAS oculto), DT-003M-02(B) (não-bloquear componente inerte sem slug) e DT-003T-01 (`is_sensibilizante` ausente). Sem perigo transcrito, `Componente.is_carcinogeno_iarc`/`is_sensibilizante` são `False` em produção por **não-extração**, não por classificação (`[VERIFICADO — git grep, 003.CH]`: nenhum código fora de fixture as levanta; o transcritor "não classifica perigo"; `MembroVerbatim`/`BlocoVerbatim` sem campo de perigo). Logo o cluster tem sequência ratificada pelo Diovanni: **(1) estender a transcrição para extrair frases-H → popular as flags do `Componente` (recorte B; fecha DT-003T-01); (2) só então reordenar o ramo-0 de `materialidade()`+Fase C (honrar flag antes do slug-check) → fecha DT-003M-01 + DT-003M-02(B) juntas.** A digitação de vocabulário e a lista-de-inertes ficam sinalizadas como **paliativo** (enumeração paralela ao sinal que a FDS já carrega). Esta nota registra a frente e a sequência; a decisão de arquitetura do recorte (B) — contrato do verbatim-de-perigo, mapa frase-H→flag, gate de confiança (R-FDS-06) — é sessão própria. Não altera o contrato do recorte (A). `[DERIVADO — git grep 003.CH; D-ARQ-33 cl.5; D-ARQ-34 Parte 2/3; D-ARQ-22]`. Nenhuma regra clínica criada/alterada. Sem código.

## D-ARQ-43 — Medição dos 6 PDFs de FDS fecha fronteira-OCR e critério-de-nome do transcritor; catálogo de patologias da seção 3 é input da IMPL

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA). Sem código. Fecha dois dos cinco pontos que D-ARQ-42 adiou por medição; cataloga o restante como input da IMPL do transcritor. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-42 adiou cinco pontos do transcritor-FDS "por medição sobre os 3 PDFs reais": mecanismo fino, fronteira-OCR, critério de `nome`, prompt, tratamento das notações. A 003.AN mediu — por extração determinística (`pdfplumber.extract_text`/`extract_tables` sobre os bytes) de **6** PDFs de `fds_originais/` (os 3 do gabarito `fds_t65` + 3 de acervo sem par de fixture). Achado que corrige a Base de D-ARQ-42: o diretório tem **6** PDFs, não 3 — a inspeção da 003.AM escopou aos 3 do fixture. `[DERIVADO — ls + medição em disco, 003.AN]`.

**Gate de estado real (literais da medição, não triagem de 2ª mão).**
- Os 6 PDFs têm camada de texto nativa. Metadados: Ghostscript 8.70/8.61, Word 2010/2013, PDFCreator — geradores digitais, nenhum scanner. `extract_text` denso nos 6; `extract_tables` recupera a tabela de composição como grade `[nome, faixa, CAS]` onde a seção 3 é tabular. `[DERIVADO — metadata + char-count + extract_tables, 003.AN]`.
- **A triagem-LLM da 003.AM (Ciplan = escaneado-com-OCR) está REFUTADA.** Ciplan: 3340/3202 chars em 2 páginas, tabela de composição extraída limpa (8 componentes), zero marcador de OCR, zero corrupção. É nativo. O sinal de KB-baixo (28,4) estava certo; a triagem-LLM era ruído (D-ARQ-30: aponta, não afirma — aqui afirmou errado e a medição corrigiu). `[DERIVADO — medição Ciplan, 003.AN]`.

**Decisão — dois fechamentos + um catálogo.**

*Parte 1 — fronteira-OCR FECHADA: o parse-PDF do transcritor é extração de camada de texto, sem OCR.* O parse-PDF determinístico (camada interna de D-ARQ-42 Parte 1) é `pdfplumber` sobre a camada de texto. Não há etapa de OCR no transcritor. A decisão aberta de D-ARQ-42 ("LLM absorve ruído de OCR vs. limpeza determinística") **evapora por medição**: não há ruído de OCR — os 6 PDFs do acervo são nativos. OCR é contingência futura declarada (se um PGR trouxer FDS escaneada de verdade), não construída. `[DERIVADO — medição dos 6, 003.AN; molde "casa antes do morador" D-ARQ-40 cl.4]`.

*Parte 2 — critério de `nome` FECHADO: casamento por CAS-primário; `nome` é transcrito informativo, não gabaritado por `==`.* O teste do transcritor assere `cas` (token rígido) + `concentracao` (faixa numérica); `nome` fica livre, não-`==`. Prova na medição: o mesmo componente sai com quebras de linha layout-dependentes (`134363-67-\n7`; `2,5-tiofenodiilbis (5-terc-\nbutil-1,3-benzoxazole)`) — um `==` sobre `nome` falharia por artefato de extração, não por erro de transcrição. Para componente de **CAS oculto** (sem chave estável), `nome` é o único identificador e importa como dado — mas ainda não como asserção de teste. Confirma D-ARQ-42 Parte 4. `[DERIVADO — nomes partidos na medição, 003.AN]`.

*Parte 3 — catálogo de patologias da seção 3 (input cravado da IMPL do transcritor; não decididas aqui).* A medição expôs três patologias com caso-âncora vivo, que a IMPL do transcritor tem de aguentar:
- **(P1) CAS plural / multi-linha numa célula.** Leinertex e Massa-Corrida agrupam sub-componentes sob "Derivados de:" com CAS empilhados (`2634-33-5\n55965-84-9`) e faixa única. Um `Componente` ≠ uma linha-de-tabela. Explode em N vs. agrega é decisão aberta — cruza a granularidade da promoção (D-ARQ-35). Registrada em **DT-003AN-01**, não decidida aqui.
- **(P2) faixa em duas formas, ambas exigindo normalização de ordem no resolvedor.** (P2a) genuinamente invertida `min>max`: `0,2 – 0,05`, `0,1 – 0,05`, `0,01 – 0,008` (Leinertex, Massa-Corrida). (P2b) piso-textual `00`: `00 – 10`, `00 – 0,5` (Tigre) — ordem correta, piso zero escrito `00`. **Ambas resolvidas por `min()/max()` sobre o par no resolvedor determinístico** — `(0.05, 0.2)` e `(0.0, 10.0)` respectivamente. O transcritor transcreve verbatim; a normalização de ordem é responsabilidade NOVA do resolvedor (`gate_cas`/`resolver_composicao` não a têm hoje). **NÃO é "sempre inverter"**: (P2b) já está em ordem; `min/max` cobre os dois sem ramo condicional. `[DERIVADO — faixas literais da medição, 003.AN]`. Toca contrato do resolvedor → motivo da ID nova.
- **(P3) CAS ausente legítimo, três sabores.** `ND`/`NA` (Tinta), `Segredo Industrial`/`Informação confidencial` (Tigre, Massa-Corrida, Leinertex) → todos `cas=""` → ramo (d) `cas_ausente` não-bloqueante de D-ARQ-36, **não** ramo (c) `cas_invalido`. 4 dos 6 PDFs têm CAS ocultado por segredo industrial — oculto≠inválido de D-ARQ-36 confirmado em dado real. O caso-âncora de DT-003M-01 está vivo e literal: Segredo Industrial 2 do Tigre declara H334+H317 com CAS oculto → `cas=""` → ramo 0 → AUSENTE, mascarando o bypass-sensibilizante. (A) de D-ARQ-42 recorta isto pra fora; a medição confirma que o recorte é o estado real, não hipótese. DT-003M-01 referenciada, status inalterado.

**Consequência.**
- Os cinco pontos adiados por D-ARQ-42 resolvem assim: OCR (fechado, Parte 1), critério-nome (fechado, Parte 2), notações/mecanismo-fino/prompt → o catálogo P1–P3 é o input que a IMPL consome; o mecanismo fino e o prompt decidem-se na IMPL com o catálogo em mãos (molde D-ARQ-41 P3).
- P2 dá responsabilidade nova ao resolvedor determinístico (normalização de ordem de faixa), testável (par invertido → `min/max` → faixa válida; par `00 – N` → faixa válida sem inversão).
- Não tira de produção: a IMPL do transcritor + plug seguem a jusante. A entrada segue fixture até a transcrição-LLM existir (D-ARQ-25 Parte B).
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado). Fecha contrato da camada de extração-FDS.

**Fronteiras (não confundir):**
- **D-ARQ-42** — fecha os pontos que ela adiou; não revoga. Contrato de saída (`tuple[Componente,...]`), recorte (A), bicamada interna — intocados.
- **D-ARQ-36** — P3 confirma os 4 ramos do gate em dado real (ramo d, oculto≠inválido). P2 adiciona normalização de ordem ao resolvedor, a montante do gate-CAS, sem tocar os 4 ramos.
- **D-ARQ-34** — P2 alimenta `FaixaConcentracao(minimo, maximo)`: a ordem normalizada é pré-condição de `piso_efetivo`/`teto_efetivo` rotearem materialidade (faixa `min>max` é erro de integridade Stage 3, D-ARQ-17 — a normalização no resolvedor a evita antes do Stage 3).
- **D-ARQ-35** — P1 (explode-vs-agrega) cruza a granularidade da promoção; DT-003AN-01 a guarda, não a decide.
- **DT-003M-01 / DT-003T-01** — P3 confirma DT-003M-01 viva (H334 Tigre); sem mudança de status. Perigo-transcrito segue fora de escopo (recorte A).

**Base.** Sessão 003.AN (26/06/2026). Medição determinística de 6 PDFs de `fds_originais/` (pdfplumber). Fecha fronteira-OCR (escaneado refutado) e critério-nome (CAS-primário, nome não-`==`); cataloga P1–P3 como input da IMPL. Passada adversária sobre o texto: corrigiu P2 de "faixa invertida" (um caso) para invertida-P2a + piso-textual-00-P2b (dois sub-casos, `min/max` cobre ambos sem "sempre inverter") — confronto contra os literais `00 – 10`/`0,2 – 0,05`. Decisão de arquitetura — sem código.

**Aplicação na sessão 003.AP (27/06/2026) — IMPLEMENTAÇÃO (P2: normalização min/max no resolvedor).** A patologia P2 do catálogo (Parte 3) virou código. Helper puro `_normalizar_faixa(componente) -> Componente` em `agente_medico/motor/composicao.py`, aplicado a cada componente **antes** do `gate_cas` no loop de `resolver_composicao` — a ordem da faixa é ortogonal ao ramo do CAS, e canonicalizar antes da resolução espelha "transcreve verbatim → resolvedor normaliza" (D-ARQ-41). Responsabilidade NOVA do resolvedor confirmada: `gate_cas`/`resolver_composicao` não tinham normalização de ordem. P2a (par invertido `0,2–0,05`) → `(0.05, 0.2)` por `min()/max()`; P2b (piso-textual `00–10`) → `(0.0, 10.0)` passa incólume — `min/max` cobre os dois **sem ramo condicional**, confirmando "não é sempre inverter". Guarda obrigatória: normaliza só quando `minimo` E `maximo` são não-None — `None` é sentinela de faixa semi-aberta (`piso_efetivo`/`teto_efetivo`, D-ARQ-34 Parte 1), nunca valor comparável; `min(None, 5.0)` seria `TypeError`. `concentracao is None` (sub-objeto ausente) → intocado. Idempotente (faixa já-ordenada não muda). Frozen preservado (reescrita via `dataclasses.replace`, D-ARQ-09). `tipos.py` INTOCADO — o `__post_init__` segue ausente, o trilho de integridade `min>max` do Stage 3 (D-ARQ-17) intacto para faixas que cheguem por outro caminho; a normalização canonicaliza a FDS-via-resolver sem rejeitar nada. Gate de estado real (repo inteiro, tipo compartilhado per 003.I) + passada adversária sobre o prompt (per 003.W) antes de emitir. 8 testes em `test_normalizacao_faixa.py` (P2a / P2b / já-ordenada / semi-aberta inferior-`None` / semi-aberta superior-`None` / `concentracao` ausente / ponto / idempotência); cada um falha sem o helper. `[DERIVADO — catálogo P2 003.AN; literais de composicao.py/tipos.py em disco]`. Commit `534f239`, merge `ec60c60` (PR #110, "Create a merge commit"). Suíte 424→432; mypy --strict limpo em `composicao.py`.

## D-ARQ-44 — `.gitattributes` `*.md text eol=lf`: terminador de markdown blindado na origem

**Sessão:** 003.AO (26/06/2026) — META/higiene, doc-only.

**Medição (003.AN).** Gravação dos 3 docs vivos ficou 100% CRLF no working tree; o blob salvou LF-puro só porque `core.autocrlf=true` renormalizou no `git add` (0 CRLF nos blobs staged). A integridade do terminador dependia do autocrlf acertar a cada gravação — fragilidade medida, não teórica.

**Decisão.** `.gitattributes` na raiz com `*.md text eol=lf`. Terminador LF passa a ser normativo no commit, independe de cliente ou de `core.autocrlf`. Cobre `docs/`, `agente_medico/`, `.claude/skills/kickoff/` [DERIVADO — `git ls-files '*.md'`].

**Escopo — `*.md` e não `*` global.** `* text eol=lf` reescreveria o terminador de `.py`/fixtures no próximo toque — risco de reescrita não-pedida num repo de 424 testes, vetado numa sessão doc-only. `*.md` é cirúrgico: markdown é texto puro, sem asserção de byte-terminador em teste. O terreno `.py`/cp1252 fica para uma META futura, com o motor na mão.

**Distinção de DH [VALIDADO — PROTOCOLO §DH-003M-01].** DH-003M-01 é `\r\n` literal como conteúdo de string (defeito de caractere, quebra `grep "^## Sess"`). Esta é o terminador `0x0D 0x0A` de fim de linha, autocrlf-dependente (defeito de byte). Fenômenos distintos, curas distintas. Abre DH-003AO-01; DH-003M-01 permanece ABERTA.

**Efeito e limite.** O `.gitattributes` rege checkouts e adds futuros; não reescreve blobs já commitados até o próximo `modified`+`add`. Renormalização retroativa (`git add --renormalize`) NÃO executada nesta sessão — fora de escopo.

**Status.** DH-003AO-01 RESOLVIDA por D-ARQ-44 no mesmo ato.

**Nota (003.BC) — lacuna `.py` fechada.** `*.py text eol=lf` adicionado ao `.gitattributes` (PR #130), ao lado da regra `*.md` já existente (003.AO). Fecha o "terreno `.py`/cp1252 fica para uma META futura" que esta decisão deixou aberto acima, candidato sinalizado após o incidente CRLF da 003.BB (12 `.py` gravados em CRLF, tratado à mão fora do gate na hora, registrado como candidato a META no bloco 003.BB do HISTORICO). `git add --renormalize .` tocou 21 arquivos NÃO-`.py` (yaml/json/txt/toml/`.gitignore`/`.python-version`/`devcontainer.json`/`refatoracao/*`, todos com CRLF residual sem cobertura de `.gitattributes`) — confirmados EOL-only por diff (sem mudança de conteúdo após strip de `\r`), escopo reduzido de volta a só `.gitattributes` (os 21 NÃO renormalizados nesta sessão), gate final delta-zero nos `.py` confirmado. Abre DH-003BC-01 (CRLF residual nos 21 não-`.py`; correção futura candidata: `* text=auto` + exceções binárias + renormalize dedicado em branch própria).

## D-ARQ-45 — Explosão de bloco "Derivados de:" multi-CAS mora no resolvedor (1→N a montante do gate-CAS); cada sub-componente herda a faixa inteira do bloco

**Status.** DECISÃO DE ARQUITETURA. Sem código nesta sessão. Implementação (forma do trânsito CAS-plural + explosão no resolvedor + testes sintéticos) é fatia IMPL futura.

**Contexto.** A medição da 003.AN (D-ARQ-43 Parte 3, patologia P1) expôs que Leinertex e Massa-Corrida declaram na seção 3 blocos "Derivados de:" agrupando 2–3 sub-componentes com CAS empilhados numa célula (`2634-33-5\n55965-84-9`, faixa única `0,2 – 0,05`). Um `Componente` carrega um `cas: str` singular; um bloco multi-CAS não é um `Componente`. DT-003AN-01 deixou aberto o fork explode-vs-agrega, registrando que cruza D-ARQ-35 (a granularidade da promoção a `Risco` herda a da granularidade do `Componente`). Esta decisão resolve o fork. A decidibilidade não dependeu do transcritor (greenfield): o consumidor que governa a granularidade — Fase C → `Risco(fonte="quimico_composicao")` (D-ARQ-35 / 003.P-Q) — já está construído e estável, logo o critério de correção de P1 é determinável agora.

**Decisão — Parte 1: a explosão 1→N mora no resolvedor (`composicao.py`), a montante do `gate_cas`, downstream do transcritor verbatim.** O transcritor-LLM transcreve o bloco "Derivados de:" verbatim (D-ARQ-41 P1 / D-ARQ-42 P2: transcreve o documento como ele é — e no documento o bloco é UMA entrada com CAS empilhados, não N entradas); o resolvedor explode em N `Componente` antes de rodar `gate_cas` em cada um. Três razões: (a) `Componente.cas: str` é singular e `cas_bem_formado`/`gate_cas` operam sobre um CAS único com dígito verificador — um CAS-plural é mal-formado por construção e cairia espuriamente no ramo (c) `cas_invalido`; o CAS-plural não pode sobreviver até o gate, alguém o parte antes; (b) partir `"2634-33-5\n55965-84-9"` em `["2634-33-5", "55965-84-9"]` é operação mecânica sobre separador, sem julgamento — normalização determinística e auditável que D-ARQ-09/41 alocam ao lado determinístico, nunca ao LLM (espelha a recusa da monocamada em D-ARQ-41: o LLM não decide cardinalidade, como não escolhe slug); (c) explosão no resolvedor torna P1 fatia sintética testável imediatamente (fixture crua de bloco → `resolver_composicao` → N componentes), espelhando como a P2 (003.AP) foi fatia limpa. A operação é 1→N — distinta do endomorfismo 1→1 de `_normalizar_faixa` (P2); o que transfere da P2 não é a cardinalidade, é o princípio: normalização determinística é resolvedor-side. [DERIVADO — `composicao.py` / `tipos.py` em disco; D-ARQ-41 P1; D-ARQ-09].

**Decisão — Parte 2: cada sub-`Componente` herda a faixa de concentração inteira do bloco (α).** Bloco com faixa `(0.05, 0.2)` → cada sub-CAS recebe `(0.05, 0.2)`. Rejeitadas: (β) repartir a faixa entre os sub-CAS inventa um número que o documento não traz (erro silencioso plausível, D-ARQ-22 — pior que sobre-atribuir: fabrica dado fático de exposição); (γ) mandar cada sub-CAS para AUSENTE descarta o teto que o documento garante e sub-materializa (um sub-CAS straddle no cutoff viraria pendência em vez de materializar — a sub-supressão que D-ARQ-31 / D-ARQ-33 cl.5 / D-ARQ-35 Parte 3 mataram). α é fiel ao documento (transcreve o teto garantido: nenhum sub-CAS excede o teto do bloco), sobre-materializa na direção segura já ratificada (carrega-tudo-e-marca; materialidade não é porteira da promoção — D-ARQ-35 Parte 3 — logo sobre-materializar não força exame errado, só mantém o componente vivo e marcado pra revisão de saída), e reusa `FaixaConcentracao`/`piso_efetivo`/`teto_efetivo` (003.I) sem mecanismo novo. [DERIVADO — D-ARQ-33 cl.5; D-ARQ-35 P3; D-ARQ-34 P1].

**Limite declarado (não mascarado por mecanismo novo — D-ARQ-22).** A sobre-materialização de α não é marcável no tipo: um sub-`Componente` que herdou a faixa do bloco fica indistinguível de um cuja faixa individual foi medida em `(0.05, 0.2)`. A revisão de saída não vê "concentração herdada de bloco, não medida". Risco residual da classe "erro silencioso plausível", mitigado pela revisão de saída (D-ARQ-22), não por mecanismo no motor. Marcador de proveniência de concentração-herdada foi considerado e adiado: sem caso de consumo vivo (nenhuma regra lê "esta concentração é herdada"), adicioná-lo agora seria fiação fantasma — mesma lógica que recusou `is_sensibilizante` fantasma (DT-003T-01) e o tri-estado `Optional[bool]` (D-ARQ-36 / 003.V). Quando a revisão de saída provar que distinguir importa, vira DT/fatia própria.

**Consequência.** Fecha DT-003AN-01 (fork explode-vs-agrega resolvido a favor de explode). Cruza D-ARQ-35 conforme previsto: explodir multiplica os `Risco(fonte="quimico_composicao")` promovidos no Stage 2 médico — cada derivado vira seu próprio risco químico, marcado por `regra_id`; é o comportamento desejado (anti-supressão), não efeito colateral. Dá responsabilidade nova ao resolvedor (explosão 1→N) — testável sinteticamente (bloco multi-CAS cru → N componentes, cada um com a faixa compartilhada, cada um resolvido pelo gate); cada teste falha sem a explosão e passa com ela. Não tira de produção: entrada segue fixture, transcritor segue greenfield (D-ARQ-42); P1 é avanço de contrato, não travessia de FDS real — o salto é a camada-LLM (D-ARQ-25 Parte B). Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado quanto a conduta); cria contrato de resolvedor.

**Aberto para a IMPL (gate de estado real obrigatório antes de qualquer prompt cirúrgico).** (1) Forma do trânsito CAS-plural do transcritor ao ponto de explosão: `Componente.cas: str` não comporta CAS-plural sem ou (a) um separador convencionado no campo `cas` que o resolvedor parte (frágil — um `\n` no campo é o que o gate trataria como inválido), ou (b) uma estrutura de bloco distinta antes do resolvedor. Gêmeo da decisão de forma da P2 (`FaixaConcentracao` frozen vs. par de campos) — decide-se na IMPL com o tipo na mão, gate de estado real, passada adversária sobre o prompt (toca tipo compartilhado, per 003.I / 003.W). [A CONFIRMAR — git, IMPL]. (2) Distinção empilhado-numa-célula vs. linhas-de-tabela-separadas (critério de transcrição, herdado pela IMPL do transcritor, não do resolvedor): a 003.AN mediu P1 como CAS empilhados numa célula (`extract_tables` devolve `2634-33-5\n55965-84-9`); não confirmado se algum dos 6 PDFs lista derivados em linhas-de-tabela separadas — caso em que `extract_tables` devolve N linhas e o transcritor naturalmente emite N, sem explosão (caminho feliz, não P1). Se ambos os formatos existem no acervo, o transcritor precisa reconhecer "bloco" vs "linhas soltas" — decisão da IMPL do transcritor-FDS, não desta decisão de resolvedor. [A CONFIRMAR — abrir os 6 PDFs, IMPL transcritor].

**Fronteiras.** D-ARQ-43 P1 — esta decisão materializa a arquitetura da patologia P1; P2 (normalização de ordem) já foi 003.AP, P3 (CAS oculto) segue em DT-003M-01. D-ARQ-41 / D-ARQ-42 — não revoga: o transcritor transcreve verbatim (bloco como bloco); a explosão é normalização resolvedor-side, downstream do "CAS transcrito". D-ARQ-35 — consome: a granularidade da promoção herda a do `Componente`; não toca o mecanismo de promoção (Fase C intocada). D-ARQ-34 — α reusa `FaixaConcentracao`/`piso_efetivo`/`teto_efetivo` sem alteração. D-ARQ-09 — preservada: explosão determinística e auditável, LLM a montante do "CAS transcrito". DT-003AN-01 — fechada por esta decisão; DT-003M-01 / DT-003T-01 intocadas, fora de escopo.

**Base.** Sessão 003.AQ (27/06/2026). Resolve DT-003AN-01. Gate de decidibilidade: o consumidor médico (Fase C, D-ARQ-35 / 003.P-Q) já construído e estável governa a granularidade — fork determinável agora, não dependente do transcritor greenfield. Duas passadas adversariais: a 1ª quebrou o paralelo P2 por cardinalidade (1→N ≠ endomorfismo 1→1), forçando o argumento do contrato `cas: str` singular; a 2ª eliminou β (invenção de número) e γ (sub-supressão) por princípios já selados, e adiou o marcador de proveniência por falta de consumo vivo. Decisão de arquitetura — sem código. Implementação é fatia IMPL futura.

**Aplicação na sessão 003.AR (IMPLEMENTAÇÃO).** A decisão virou código: `_explodir_multi_cas` em `composicao.py`, aplicada como primeira operação do loop de `resolver_composicao`, a montante de `_normalizar_faixa` e `gate_cas`. Forma do trânsito CAS-plural resolvida a favor da opção (a) — separador no campo `cas`, não tipo de bloco novo (opção (b) reabriria o contrato `tuple[Componente,...]` de D-ARQ-42). A ordem explodir→normalizar→gate neutraliza a fragilidade anotada na decisão ("um `\n` no campo é o que o gate trataria como inválido"): o `\n` é consumido pelo split e nunca alcança `cas_bem_formado`. Herança-α materializada por `replace(componente, cas=p)`, que troca só o campo `cas` e herda nome/concentracao/flags. Separador = `\n` literal [DERIVADO — 003.AN, único medido]; outros separadores e a distinção "bloco empilhado" vs "linhas de tabela separadas" permanecem critério de transcrição, herdados pela IMPL do transcritor-FDS (item 2 acima, ABERTO). Três limites materializados em teste pela passada adversária: single-CAS é no-op que preserva identidade (`is`); `cas` vazio/só-espaço não remove o componente (piso de 1, anti-supressão — segue ao ramo (d) do gate); `strip` de espaços internos por pedaço. `resolvedor.py`/`tipos.py`/orquestrador/`fds_t65` INTOCADOS; blast radius 2 arquivos. 11 testes (`test_explosao_multi_cas.py`: 8 isolados + 3 integração); suíte 432→443; mypy --strict delta-zero em `composicao.py`. Commit `a04da18`, merge `f89abb3`, PR #113.

**Nota (003.AY) — o mecanismo `\n`-célula da aplicação 003.AR cai com a virada p/ `extract_text`; a decisão (explodir 1→N + α) permanece.** A reconciliação DT-003AX-01 (nota de aplicação 003.AY em D-ARQ-42) selou entrada texto-puro para o transcritor-FDS. No `extract_text` o bloco "Derivados de:" não traz o token empilhado `"2634-33-5\n55965-84-9"` numa célula — os CAS vêm em linhas separadas sob o header, com a faixa do bloco em linha própria (medido em disco, 003.AY). Logo `_explodir_multi_cas` (003.AR), que parte o `\n`-célula no campo `cas`, perde o gatilho. As Partes 1 e 2 desta decisão são preservadas: a explosão 1→N e a herança-α continuam resolvedor-side, fora do LLM (D-ARQ-45 P1). O que muda é o MECANISMO — de `\n`-split p/ expansão-de-grupo: o transcritor emite o bloco como um grupo verbatim (CAS + faixa única), o resolvedor expande. Forma do verbatim-grupo e o destino de `_explodir_multi_cas` (aposentar vs generalizar) ficam ABERTOS para a IMPL, com gate de estado real. DT-003AN-01 segue RESOLVIDA por esta decisão; só o caminho de implementação se ajusta.

**Nota (003.AZ) — mecanismo grupo-verbatim materializado na montagem (fatia i); expansão resolver-side pendente (fatia ii).** A fatia (i) (nota 003.AZ em D-ARQ-46) cravou a forma (`BlocoVerbatim`) e a montagem (`montar_bloco → BlocoComponente`: faixa 1×/bloco, membros `Componente` com `concentracao=None`). Partes 1/2 intactas: explosão 1→N + herança-α seguem RESOLVER-SIDE e fora do LLM — entram na fatia (ii)/003.BA como `_explodir_bloco(BlocoComponente) → tuple[Componente,...]` (replace da `concentracao` herdada + `_normalizar_faixa` + `gate_cas`), **aposentando** `_explodir_multi_cas` (`\n`-split 003.AR, gatilho morto sob texto-puro). Ratificado na 003.AZ: aposentar `_explodir_multi_cas` (não generalizar) e `extrair_tabelas_fds` (003.AS) → **DEPRECATED** (não cross-check), ambos na fatia (ii). DT-003AN-01 segue RESOLVIDA; só o caminho de IMPL avança.

**Nota (003.BA, fatia ii, recorte enxuto) — `_explodir_bloco` materializado como adição isolada; gate/aposentadoria/wiring ficam para a fatia (iii).** `_explodir_bloco(bloco: BlocoComponente) -> tuple[Componente, ...]` entra em `composicao.py` (ao lado de `_explodir_multi_cas`, sem substituí-lo): expande os membros do bloco (cada um nasce com `concentracao=None`, D-ARQ-46) herdando a `FaixaConcentracao` do bloco via `dataclasses.replace` e canonicalizando com `_normalizar_faixa` (D-ARQ-43 P2) — exatamente as Partes 1/2 desta decisão, só que sobre `BlocoComponente` em vez do `\n`-célula. Recorte ENXUTO, ratificado: sem `gate_cas` dentro de `_explodir_bloco` (o gate exige `indice_cas`, que é do resolver — chamá-lo aqui misturaria responsabilidade e adiaria a fatia iii sem necessidade); sem chamador em `resolver_composicao`; sem tocar `_explodir_multi_cas`, `FDS.composicao` ou `test_explosao_multi_cas.py`. `extrair_tabelas_fds` (003.AS) ganha docstring `DEPRECATED (003.BA)` (corpo intocado) — só o registro formal do destino já ratificado em 003.AZ, sem remoção de código. Anti-supressão preservada: bloco de 1 membro → tupla de 1 (nunca remove). 6 testes novos (`test_explodir_bloco.py`, cada um falha sem a função e passa com); suíte 489→495; mypy --strict delta-zero em `composicao.py`. Aposentar `_explodir_multi_cas`, plugar `_explodir_bloco` em `resolver_composicao` e migrar `test_explosao_multi_cas.py` seguem ABERTOS para a fatia (iii)/003.BB. Commit `add384f`, branch `feat-003ba-explodir-bloco`. Nenhuma R-* criada/alterada.

**Aplicação na sessão 003.BB (01/07/2026) — IMPLEMENTAÇÃO fatia (iii): `_explodir_bloco` plugado no resolver; `_explodir_multi_cas` aposentado.** Fecha as três pendências do bloco 003.BA. (1) **Wiring:** `resolver_composicao` deixa de varrer `produto.fds.composicao : tuple[Componente,...]` e passa a varrer `produto.fds.composicao_verbatim : tuple[BlocoComponente,...]`, expandindo cada bloco por `_explodir_bloco` (1→N, herança-α + `_normalizar_faixa` já embutidos, D-ARQ-45 P1/P2 + D-ARQ-43 P2) e rodando `gate_cas` em cada sub-`Componente`; o resultado resolvido é escrito em `fds.composicao`. A chamada standalone de `_normalizar_faixa` no loop some (subsumida por `_explodir_bloco`). (2) **Aposentadoria:** `_explodir_multi_cas` (`\n`-split, 003.AR — gatilho morto sob texto-puro desde a nota 003.AY) é DELETADA; a cobertura isolada equivalente já vive em `test_explodir_bloco.py` (6 testes, 003.BA). (3) **Preservação do verbatim (decisão B, "manter"):** o `dataclasses.replace` só troca `composicao`, logo `composicao_verbatim` sobrevive intacto no FDS resolvido — proveniência barata, espírito carrega-tudo-e-marca (D-ARQ-31/35 P3); coberto por teste dedicado. Fork da forma-de-trânsito ratificado pelo Diovanni: campo separado em vez de tipo polimórfico honra `mypy --strict` (um só campo com Componente-antes/Bloco-depois seria mentira de tipo); downstream (`riscos.py`, `pendencias_estruturais.py`, `fds_t65`, path do `executar` direto) INTOCADO — lê `composicao` resolvida; materializa a fronteira D-ARQ-41 (transcrição agrupada ↔ resolução plana) no tipo, universal (agnóstica a setor). Opções C (tipos `FDSVerbatim` vs `FDS` distintos) e D (`composicao` vira blocos, downstream explode on-read) descartadas: C muda assinatura de PGR/orquestrador (over-engineering com transcritor greenfield, D-ARQ-42); D espalha a explosão por múltiplos consumidores, violando "explosão mora no resolvedor" (D-ARQ-45 P1). Nenhuma R-* criada/alterada. Suíte 495→488 (−8 asserções isoladas de `_explodir_multi_cas`, +1 preservação-verbatim); mypy --strict delta-zero em `composicao.py` e `tipos.py`. Commit `05b0e41`, merge `05731bd`, PR #128, "Create a merge commit". DT-003AN-01 segue RESOLVIDA (só o caminho de IMPL fechou). `[DERIVADO — IMPL 003.BB host; D-ARQ-45 P1/P2; D-ARQ-46]`.

**Nota (003.BC) — porta de entrada de produção ratificada: fork A.** `montar_fds(blocos: Sequence[BlocoVerbatim]) -> FDS` materializa em `transcricao_fds.py` a invariante que a nota 003.BB deixou implícita ("FDS pré-resolução tem `composicao_verbatim` cheio / `composicao` vazio"): `FDS(composicao=(), composicao_verbatim=montar_composicao(blocos))`. **Fork A** (função nomeada, única porta de entrada) ratificado sobre **fork B** (cada chamador constrói `FDS(...)` na mão, replicando `composicao=()` em N pontos) — B espalha a invariante como convenção-sem-guarda-de-tipo, o mesmo risco de fiação-implícita que `montar_bloco`/`montar_composicao` já evitaram ao nomear a montagem em vez de deixá-la implícita em cada chamador. Teste de integração fim-a-fim (`montar_fds → resolver_composicao`) pareado 1:1 contra o gabarito `fds_t65.tinta_acrilica()` (cas + concentração, 9/9 blocos) — primeira prova em disco de que a cadeia verbatim→FDS→resolver produz a composição esperada do PDF real, sem ajuste de gabarito/fixture. `[DERIVADO — IMPL 003.BC; D-ARQ-46]`.

## D-ARQ-46 — Contrato do verbatim transcrito da FDS: o LLM-transcritor emite verbatim cru (texto por campo); `tuple[Componente,...]` é saída da montagem determinística, não do LLM

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código. Implementação (montagem + LLM-transcritor mockado) é fatia futura (003.AW). Autorização para virar D-ARQ dada pelo Diovanni (003.AV).

**Contexto.** D-ARQ-42 selou o transcritor-FDS como camada-LLM da instância-FDS de D-ARQ-41 e cravou o contrato de saída como `tuple[Componente,...]`. A 003.AU adicionou a camada de normalização determinística do verbatim (`transcricao_fds.py`: P3 `desambiguar_cas`, P4 `normalizar_cas_ausente`, P5 `parsear_faixa`) e marcou como fatia futura: o LLM-transcritor mockado, a montagem em `Componente`, e o contrato do verbatim transcrito (tipo intermediário, gêmeo da "PGR transcrita" de D-ARQ-41 P2). Esta decisão sela esse contrato. Não implementa.

**Gate de estado real (greps + literais em disco, 003.AV).**
- `transcricao_fds.py`: P3/P4/P5 são funções puras sobre strings cruas isoladas — `desambiguar_cas(str)->str`, `normalizar_cas_ausente(str)->str`, `parsear_faixa(str)->Optional[FaixaConcentracao]`. Não há tipo-verbatim, montagem, nem consumidor (só `test_transcricao_fds.py` importa). `[VERIFICADO — git grep + Get-Content]`.
- `tipos.py`: `Componente(cas: str, nome: str, concentracao: Optional[FaixaConcentracao]=None, agente: Optional[str]=None, is_carcinogeno_iarc=False, is_sensibilizante=False)`, frozen. `concentracao` é `FaixaConcentracao` já parseada — não há campo para texto cru de faixa. `[VERIFICADO]`.
- `Componente` é construído só em testes/fixtures; produção o recebe via `resolver_composicao`. `_explodir_multi_cas` (D-ARQ-45) e `_normalizar_faixa` (003.AP) moram no resolvedor (`composicao.py`), a jusante. `[VERIFICADO]`.

**Decisão — quatro partes.**

*Parte 1 — correção de D-ARQ-42 P2: o LLM-transcritor emite verbatim CRU, não `Componente` com `FaixaConcentracao`.* D-ARQ-42 P2 diz, na letra, "o transcritor produz `Componente(... concentracao=<FaixaConcentracao transcrita>, agente=None)`". Essa cláusula é superada pela existência de P5 (`parsear_faixa`, 003.AU), que recebe texto bruto e produz `FaixaConcentracao`: se o LLM já entregasse `FaixaConcentracao`, P5 seria código morto. A 003.AU criou esse split (LLM-transcritor vs. montagem) ao construir P3/P4/P5 sem reconciliar P2. 003.AV formaliza: o LLM-transcritor emite o verbatim (texto cru por campo); `tuple[Componente,...]` é saída da montagem determinística (que aplica P3/P4/P5), não do LLM. A descrição de D-ARQ-42 P2 passa a valer para a saída da montagem, não para a saída do LLM. `[DERIVADO — P5 em transcricao_fds.py, 003.AU; D-ARQ-41 P1]`.

*Parte 2 — semântica do verbatim (o que se crava).* O verbatim carrega, por componente da seção de composição: cas cru (com `\n` de quebra-de-render, grafia-de-ausente, ou oculto — sem limpar), nome cru, faixa como texto cru (`"0,2 – 0,05"`, `"< 5%"`, `""`). NÃO carrega: slug, `FaixaConcentracao` parseada, flags de perigo (recorte A de D-ARQ-42 P3), explosão multi-CAS, ordenação min/max. FDS inteira = sequência desses por-componente. O argumento estrutural que força o verbatim distinto de `Componente`: o texto cru de faixa não tem casa em `Componente.concentracao` (que é `FaixaConcentracao`), e o LLM emitir faixa-parseada / CAS-explodido / slug seria normalização em silêncio na camada LLM — viola D-ARQ-41 P1 e mata P5/`_explodir`/`gate_cas` (D-ARQ-22). `[DERIVADO — tipos.py + transcricao_fds.py em disco]`.

*Parte 3 — fronteira LLM↔determinístico = o verbatim.* Instancia D-ARQ-41 P1 para a FDS: o LLM-transcritor produz o verbatim (não-determinístico, candidato a revisão — D-ARQ-33 cl.4); montagem (P3/P4/P5) + resolvedor (`gate_cas`, `_explodir_multi_cas`, `_normalizar_faixa`) são determinísticos (D-ARQ-09). O "CAS transcrito" de D-ARQ-36 é o mesmo ponto visto do lado do gate; o verbatim é a forma completa dele (cas + nome + faixa). `[DERIVADO — D-ARQ-41 P1; D-ARQ-36 P1]`.

*Parte 4 — montagem é 1→1; explosão e ordenação ficam no resolvedor.* A montagem leva uma linha-verbatim a um `Componente`: `cas = normalizar_cas_ausente(desambiguar_cas(cas_bruto))`, `concentracao = parsear_faixa(faixa_bruta)`, `nome = nome_bruto.strip()`, `agente=None`, flags default. Uma linha → um `Componente` — a explosão multi-CAS (1→N, `_explodir_multi_cas`, D-ARQ-45) e a ordenação min/max (`_normalizar_faixa`, 003.AP) permanecem intocadas no resolvedor, a jusante. `desambiguar_cas` preserva o `\n` multi-CAS legítimo (ambos fragmentos bem-formados), que sobrevive a `normalizar_cas_ausente` e chega ao `_explodir_multi_cas`; `parsear_faixa` devolve faixa sem ordenar, que `_normalizar_faixa` ordena. Zero duplicação. `[DERIVADO — header de transcricao_fds.py; D-ARQ-45; 003.AP]`.

**Recomendações de implementação (003.AW decide com gate de estado real e código na mão — NÃO crava de arquitetura, precedente D-ARQ-34→003.I / D-ARQ-42→003.V→003.W):**
- Forma do verbatim: dataclass frozen dedicada (coesão + disciplina frozen), campos all-string — vs. dict / tupla-de-str. Recomendo dataclass.
- Local da montagem: `transcricao_fds.py` (camada que compõe P3/P4/P5) — vs. `composicao.py`. Recomendo `transcricao_fds.py` por responsabilidade.
- Ordem `P3→P4` no cas (forma antes de classificar ausência) — ambas as ordens passam os casos medidos; baixo risco.
- Nomes de campo.

**Limites declarados (D-ARQ-22, não mascarados):**
- O tipo de três campos é agnóstico às patologias 1/2 de DT-003AS-01 (composição não-isolável, coluna deslocada): faixa ausente vira `faixa_bruta=""` → `parsear_faixa` → `None` → sentinela AUSENTE (D-ARQ-34 P1). Mas a producibilidade de um verbatim é barrada pela patologia 1 (grid não-isolável Ciplan/Tigre): sem o LLM conseguir emitir os triplos por-componente, não há verbatim — bloqueio upstream, aberto, camada-LLM. O tipo não espera 1/2; a existência de verbatim para aquelas FDS depende da patologia 1.
- Recorte (A) mantido: frase-H/perigo fora; flags `False`-por-ausência. "Segredo Industrial 2" (Adesivo Tigre, H334+H317, CAS oculto) → `cas=""` → ramo (d) do gate → AUSENTE, mascarando o bypass-sensibilizante — estado de hoje (DT-003M-01), não regressão; 003.AV não resolve.

**Fronteiras (não confundir):**
- **D-ARQ-42** — corrige P2 (LLM emite verbatim cru, não `Componente` com `FaixaConcentracao`); P1 (bicamada parse-PDF→LLM), P3 (recorte A) e P4 (gabarito por-campo) intactas.
- **D-ARQ-41** — instância-FDS da fronteira "contrato transcrito tipado" (P1) e do verbatim ("PGR transcrita" gêmeo, P2).
- **D-ARQ-45 / 003.AP** — `_explodir_multi_cas` e `_normalizar_faixa` intocados; a montagem não explode nem ordena.
- **D-ARQ-34** — `FaixaConcentracao` reusada; `parsear_faixa` a produz sem ordenar (ordem é do resolvedor).
- **D-ARQ-09 / D-ARQ-36** — preservadas: toda LLM a montante do verbatim; montagem e resolvedor puros.
- **DT-003AS-01 / DT-003M-01 / DT-003T-01** — referenciadas; status inalterado.

**Base.** Sessão 003.AV (29/06/2026). Sela o contrato do verbatim que D-ARQ-42 P2 + D-ARQ-41 P2 deixaram aberto; corrige D-ARQ-42 P2 contra a existência de P5 (003.AU). Gate de estado real: `transcricao_fds.py` + `tipos.py` + greps em disco. Duas passadas: a 1ª esboçou tipo+montagem; a passada crítica achou (a) a contradição D-ARQ-42 P2 ⇄ P5/003.AU enterrada como "refino", promovida a correção explícita, e (b) overreach — dataclass-form e local-de-módulo rebaixados de crava para recomendação (precedente ARQUITETURA-crava-semântica / IMPL-crava-forma). Decisão de arquitetura — sem código.
**Aplicação na sessão 003.AW (30/06/2026) — IMPLEMENTAÇÃO (montagem verbatim → `tuple[Componente,...]` + LLM-transcritor mockado).** As recomendações de forma viraram código, decididas com gate de estado real (suíte 477 reconfirmada por pytest; releitura literal de `tipos.py`/`transcricao_fds.py`/`composicao.py`/`fds_t65.py`; `git grep` confirmou `Componente` construído só em testes — a montagem é o 1º ponto de produção que o constrói). (1) **Tipo:** `ComponenteVerbatim(cas: str, nome: str, faixa: str)`, frozen, em `tipos.py` — dado mora no lar dos dataclasses; campo `faixa` (não `concentracao`) marca texto cru, distinto de `Componente.concentracao: FaixaConcentracao`. (2) **Montagem:** `montar_componente(v) -> Componente` (1→1) + `montar_composicao(Sequence) -> tuple[Componente,...]` em `transcricao_fds.py` (camada que compõe P3/P4/P5) — recomendação confirmada. (3) **Ordem cravada (D-ARQ-46 Parte 4):** `normalizar_cas_ausente(desambiguar_cas(cas))`. (4) **Gabarito por par PDF↔`fds_t65`** com verbatim mockado fiel à medição 003.AN/AS (`medir_fds_gabarito_output.txt`): tinta (9 comp.) e Ciplan (8 comp.) reproduzem `cas` (exato) + `concentracao`; `nome` não-`==` (D-ARQ-42 Parte 4). Adesivo Tigre fora do gabarito verde — patologia 1 (grid fundido) barra a producibilidade do verbatim (limite de D-ARQ-46 / DT-003AS-01). A passada adversária (toca tipo compartilhado `tipos.py`, molde 003.W) expôs DT-003AW-01 (grafia-de-ausente quebrada por `\n` de render, não-reconhecida por nenhuma ordem P3/P4; não-medida, não-bloqueante). 11 testes (`test_montagem_verbatim.py`); suíte 477→488; mypy --strict limpo nos 4 arquivos. `tipos.py` ganha tipo novo sem alterar `Componente`; `composicao.py`/`resolvedor.py` intocados (a montagem não explode nem ordena). Commit `ec3b225`, merge `8054f5b`, PR #121, "Create a merge commit". Nenhuma regra clínica criada/alterada. `[DERIVADO — pytest/mypy/git em disco, 003.AW]`.

**Aplicação na sessão 003.AZ (01/07/2026) — IMPLEMENTAÇÃO fatia (i): forma do verbatim-grupo + montagem.** Materializa a fatia (i) do transcritor-FDS sob entrada texto-puro (nota 003.AY). **Forma ratificada: `BlocoVerbatim` aninhado**, não `ComponenteVerbatim` flat + `grupo_id` — a faixa única é propriedade do bloco (medição 003.AY: escrita 1× no bloco "Derivados de:"), logo aninhar codifica a herança-α no tipo; flat+grupo_id deixaria a faixa duplicada/órfã e a coesão do grupo como invariante reconstruível-e-violável sobre chave sintética (anti-D-ARQ-09). **Tipos** (`tipos.py`): `MembroVerbatim(cas, nome)`; `BlocoVerbatim(faixa, membros)` — verbatim cru AGRUPADO, fronteira LLM↔determinístico, singleton = bloco de 1 membro; `BlocoComponente(concentracao, membros)` — saída da montagem / entrada da expansão-de-grupo (resolver, fatia ii), membros são `Componente` com `concentracao=None` (herança-α RESOLVER-SIDE, D-ARQ-45 P1/P2). `ComponenteVerbatim` (003.AV/AW) **APOSENTADO** (superseded). **Montagem** (`transcricao_fds.py`): `_montar_membro` (P3/P4 no cas, strip no nome, Recorte A), `montar_bloco` (P5 na faixa 1×/bloco; NÃO explode/ordena/herda), `montar_composicao: Sequence[BlocoVerbatim] → tuple[BlocoComponente,...]`; P3/P4/P5 intocadas. **Testes**: `fds_verbatim_t65` migrada a BlocoVerbatim-singleton; `fds_verbatim_leinertex` nova (multi-CAS real N=2/N=3) cobrindo o grupo (falha sem BlocoVerbatim, passa com); 12 testes; suíte 488→489; mypy --strict delta-zero. Expansão 1→N + herança-α (fatia ii) aberta p/ 003.BA. Commit `9a4eaf3`. Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.AZ; D-ARQ-45 P1/P2; medição 003.AN/AY]`.

**Aplicação na sessão 003.BB (01/07/2026) — IMPLEMENTAÇÃO: `FDS` ganha `composicao_verbatim`, entrada do resolver.** A fatia (iii) fecha o trânsito montagem→resolver que a fatia (i)/003.AZ deixou aberto (`montar_composicao → tuple[BlocoComponente,...]` existia sem consumidor no pipeline). `FDS` passa a carregar **dois** campos de composição: `composicao_verbatim: tuple[BlocoComponente, ...] = ()` (entrada, agrupada, saída da montagem) e `composicao: tuple[Componente, ...]` (saída, plana, resolvida — lida pelos estágios médicos). `resolver_composicao` é a transformação entre as duas formas: lê `composicao_verbatim`, escreve `composicao`, preserva o verbatim. Invariante implícita (não imposta pelo tipo): FDS pré-resolução tem `composicao_verbatim` cheio / `composicao` vazio; pós-resolução, `composicao` cheio + `composicao_verbatim` preservado. Marcador de estado (pré/pós) considerado e adiado: sem consumo vivo — mesma lógica anti-fiação-fantasma de D-ARQ-45 e D-ARQ-36. `ComponenteVerbatim` já estava APOSENTADO (003.AZ); `BlocoVerbatim`/`BlocoComponente`/`montar_composicao` intactos. `[DERIVADO — IMPL 003.BB host; tipos.py em disco; D-ARQ-45; D-ARQ-41 P1]`.

**Nota (003.BC) — `montar_fds` fecha o trânsito que a nota 003.BB descreveu.** A invariante implícita registrada em 003.BB ("composicao vazio / composicao_verbatim cheio" na entrada do resolver) ganha função nomeada e testada: `montar_fds(blocos) -> FDS` é a ÚNICA porta de entrada de produção verbatim→FDS (fork A, ver nota 003.BC em D-ARQ-45) — nenhum chamador constrói `FDS` de verbatim na mão. Composição pura sobre `montar_composicao` já existente; `BlocoVerbatim`/`BlocoComponente` intactos. `[DERIVADO — IMPL 003.BC; D-ARQ-45]`.

## D-ARQ-47 — Contrato de invocação e gate do transcritor-LLM-FDS: candidato verbatim revisado pelo RT é a fronteira LLM↔determinístico

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA). Sem código nesta sessão. Implementação (parse-texto greenfield + transcritor-LLM injetável + gate de forma + harness mockado) é fatia futura. Autorização para virar D-ARQ dada pelo Diovanni (003.BD).

**Contexto.** D-ARQ-41/42 selaram o transcritor-FDS como camada-LLM (bicamada interna parse-PDF→LLM, fronteira "CAS transcrito"); D-ARQ-46 cravou que o LLM emite verbatim cru e a montagem determinística produz `Componente`. Toda a cadeia a jusante do verbatim está construída e testada com o LLM MOCKADO: montagem (003.AW/AZ), `_explodir_bloco`/wiring (003.BB), `montar_fds` (003.BC), pareado 1:1 contra `fds_t65.tinta_acrilica()`. Falta a peça que nenhuma fatia tocou: a invocação REAL do transcritor-LLM e a fronteira em que o candidato não-determinístico entra no pipeline determinístico. DT-003AS-01 patologia 1 (grid fundido Ciplan/Tigre) era o caso-âncora dado como "producibilidade barrada" (D-ARQ-46 limites); esta sessão mediu e o desbloqueou.

**Medição (003.BD, CONHECIMENTO — a passada do Arquiteto como classe do transcritor-LLM).** `extract_text` (pdfplumber) da região âncora-por-título dos 2 grid-fundidos, transcrição por sentido contra o gabarito `fds_t65`:
- Tigre 7/7, Ciplan 8/8 em `cas` + `concentracao`. O "grid fundido" é interleave de coluna em ordem linear do texto (composição intercalada com a seção vizinha), NÃO perda de informação — os triplos estão todos presentes.
- Ordem de coluna INVERTE por fabricante: Tigre `[nome, CAS, faixa]`, Ciplan `[nome, faixa, CAS]`. Roteamento por FORMATO do token (CAS `dd…-dd-d`; faixa `n–n %`), não por posição — reforça a decisão anti-bbox de 003.AX.
- Ruído descartável pela disciplina do triplo: a tabela de LT em ppm (Tigre p.1) repete nomes sem CAS e sem %-faixa → não é composição.
- CAS oculto: `*`/`**` (Tigre), `vários` (Ciplan) → `cas=""` (ramo d de D-ARQ-36). Frases-H em rodapé (SI2: H334) — recorte A deixa fora; DT-003M-01 viva.
- Nome multi-linha (Tigre comp. 5, `2,5-tiofenodiilbis (5-terc-\nbutil-1,3-benzoxazole)`) reassemblado por sentido.
`[DERIVADO — medição extract_text dos 2 grid-fundidos vs. fds_t65, 003.BD]`. Reenquadra D-ARQ-46: o bloqueio era ausência de LLM real invocado, não impossibilidade intrínseca.

**Decisão — cinco cláusulas.**

*Cláusula 1 — fronteira e forma.* O transcritor-LLM recebe TEXTO (`extract_text` da região âncora-por-título, 003.AT/AY) e emite `tuple[BlocoVerbatim,...]` candidato — tipo já materializado (003.AZ). NÃO emite `Componente`, não resolve slug, não explode multi-CAS, não ordena faixa, não classifica perigo. Confirma D-ARQ-46 P1/P3; o verbatim é a fronteira LLM↔determinístico. `[DERIVADO — D-ARQ-46 P1/P3; tipos.py em disco]`.

*Cláusula 2 — invocação injetável, nunca global.* O cliente-LLM é injetado como parâmetro (forma ex.: `transcrever_fds(texto: str, cliente: TranscritorLLM) -> tuple[BlocoVerbatim,...]`), nunca importado no módulo — para testar com mock/gravação sem bater na API (D-ARQ-42 P4). O LLM fica a montante do verbatim; motor determinístico intacto (D-ARQ-09). `[DERIVADO — D-ARQ-09; D-ARQ-42 P4]`.

*Cláusula 3 — gate de FORMA, não de conteúdo.* Antes de o candidato entrar em `montar_fds`, gate determinístico de schema: cada `BlocoVerbatim` tem faixa-texto parseável (ou vazia → sentinela AUSENTE, D-ARQ-34 P1) e ≥1 membro nomeado. O gate NÃO valida CAS (é do `gate_cas` a jusante, D-ARQ-36), não decide materialidade, não corrige. Falha de forma → `Pendencia`, nunca chute (D-ARQ-08/22). `[DERIVADO — D-ARQ-36; D-ARQ-22]`.

*Cláusula 4 — revisão do RT sobre o verbatim é a admissão do candidato.* A saída do LLM é candidata (D-ARQ-33 cl.4). O `BlocoVerbatim` é o artefato de revisão humana — texto legível, 1:1 com o documento — revisado/editado pelo responsável técnico ANTES de `montar_fds`. Ancora no gate existente R-PGR-01 (assinatura por engenheiro), espelha D-ARQ-33 cl.4, sem criar camada de revisão nova. É a peça topológica que faltava: onde o não-determinístico vira aceito. `[DERIVADO — D-ARQ-33 cl.4; R-PGR-01]`.

*Cláusula 5 — roteamento por formato-de-token (princípio derivado da medição).* O triplo (`nome + token-CAS + token-faixa-%`) é a âncora semântica; a ordem de coluna é irrelevante; linhas sem CAS+%-faixa (tabela de LT em ppm) são descartadas. O texto exato do prompt é adiado à IMPL (molde D-ARQ-42 P4); o PRINCÍPIO entra no contrato como derivado da medição 003.BD. `[DERIVADO — medição 003.BD]`.

**Consequência.**
- Fecha a fronteira que faltava para o transcritor-FDS sair do mock: contrato de invocação + gate + ponto de revisão, sem implementar.
- Dá `extrair_texto_fds` (parse-texto greenfield) como camada determinística a montante — sucede o papel que `extrair_tabelas_fds` (003.AS) perdeu ao virar DEPRECATED (003.BB, sob entrada texto-puro).
- Determinismo intacto (D-ARQ-09): toda LLM a montante do verbatim; gate de forma, montagem e resolvedor puros.
- Universal (D-ARQ-06): "documento → texto → triplos-candidatos → verbatim revisado → determinístico" serve qualquer FDS digital de qualquer setor; a conduta segue no lado-médico.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO inalterado quanto a conduta). Cria contrato de camada de extração-FDS.

**Limites declarados (D-ARQ-22).**
- Producibilidade validada em 2 grid-fundidos (Ciplan/Tigre, medição) + 3 isolados (tinta/Leinertex/Massa, mock). n pequeno; FDS de outra norma-fonte ou escaneada fora (OCR = contingência D-ARQ-43 P1).
- Recorte A mantido: frase-H de rodapé não transcrita; SI2/H334 → `cas=""` → AUSENTE, mascarando o bypass-sensibilizante (estado de hoje, DT-003M-01, não regressão).
- A revisão-RT-sobre-verbatim é o gate de qualidade; sem ela o candidato-LLM é não-confiável por construção. Não é paliativo — é a topologia correta (cl.4). Alternativa rejeitada na 2ª passada: gate automático de confiança (sem humano) para FDS "fáceis" introduziria classificador fácil-vs-difícil, superfície de erro silencioso (D-ARQ-22).

**Fronteiras (não confundir):**
- **D-ARQ-42** — instancia a invocação da camada-LLM que D-ARQ-42 P4 adiou "por medição"; a medição 003.BD fecha o ponto. Contrato de saída (`tuple[...]`), recorte A, bicamada interna intactos.
- **D-ARQ-46** — reenquadra o limite "producibilidade barrada pela patologia 1": desbloqueado por medição. Contrato do verbatim intacto.
- **D-ARQ-36** — o `gate_cas` a jusante é intocado; o gate desta decisão é de forma, a montante da montagem.
- **D-ARQ-33 cl.4 / R-PGR-01** — a cl.4 é a admissão do candidato ancorada no gate existente, não camada nova.
- **D-ARQ-09** — preservada: verbatim é a fronteira; LLM a montante.
- **DT-003AS-01** — patologia 1 medida/producível; DT permanece ABERTA até a IMPL do transcritor-LLM + `extrair_texto_fds`. DT-003M-01 (frase-H/CAS-oculto) intocada, fora do recorte A.

**Base.** Sessão 003.BD (02/07/2026). Medição (CONHECIMENTO) desbloqueia patologia 1; contrato (ARQUITETURA) crava a invocação+gate. Modo A+B na mesma sessão, ordenado B→A (medição alimenta o contrato). Duas passadas: a 1ª esboçou as 5 cláusulas; a 2ª quase derrubou a cl.4 (gate automático) e reafirmou revisão-RT como topologia, não paliativo. Decisão de arquitetura — sem código. Implementação por fatias futuras (gate de estado real obrigatório: `extrair_texto_fds` greenfield).

**Aplicação na sessão 003.BE (02/07/2026) — IMPLEMENTAÇÃO fatia 1:** `extrair_texto_fds` (parse-texto greenfield, camada determinística a montante do transcritor-LLM). Materializa a consequência "dá `extrair_texto_fds` como camada determinística a montante", com gate de estado real (medição `extract_text` linha-a-linha dos 6 PDFs de `fds_originais/` ANTES da spec). Mecanismo do recorte (decisão desta sessão): início na primeira linha cuja normalização (NFD sem combining + upper) contém `COMPOSICAO E INFORMACOES SOBRE` — prefixo proposital: o sufixo `(OS )?INGREDIENTES` é instável no acervo (Ciplan omite "OS"; Tigre quebra o título em 2 linhas intercaladas com o endereço — medido). Fim por SOBRE-INCLUSÃO: a região vai até o FIM DA PÁGINA do primeiro título-fim (regex `\d+\s*[–\-.]?\s*(IDENTIFICACAO DE PERIGOS|MEDIDAS DE PRIMEIROS[ -]SOCORROS)`) encontrado a partir da linha seguinte à âncora — NUNCA corte fino na linha do título-fim: medido no Tigre (grid fundido) que `2. IDENTIFICAÇÃO DE PERIGOS` antecede 6 dos 7 triplos, intercalados nas linhas seguintes; corte fino suprimiria composição em silêncio (anti-supressão D-ARQ-31/35; classe D-ARQ-22). O ruído sobre-incluído é descartado a jusante pelo LLM via disciplina do triplo (cláusula 5). Título-fim ausente → até a última página (sobre-inclusão, direção segura — não é chute); âncora ausente → `None` (falha explícita; `Pendencia` é do chamador, fatia futura — nunca documento-inteiro como fallback). Saída VERBATIM (normalização só localiza). Forma: núcleo puro `_recortar_composicao(paginas) -> str | None` (testável sem PDF) + wrapper de I/O `extrair_texto_fds(caminho)`, em `extracao_fds.py` (mesmo módulo da DEPRECATED `extrair_tabelas_fds`, corpo desta intocado). 16 testes (`test_extrair_texto_fds.py`): 7 de núcleo puro sem PDF + 9 de integração com skipif SELETIVO (`requer_pdfs` só na integração; os puros rodam sempre — defeito de `pytestmark` módulo-level da 1ª rodada detectado na revisão do Arquiteto e corrigido por amend pré-push). Suíte 491→507 (host); mypy --strict delta-zero (46 pré-existentes, stash-comparado). Limites (D-ARQ-22): âncora/títulos-fim derivados de n=6 (NBR 14725 BR, keyed); FDS escaneada fora (OCR = contingência D-ARQ-43 P1); FDS com outro título-fim cai no ramo até-o-fim. Commit `db884e2`, merge `221f454`, PR #134, "Create a merge commit". Cláusulas 1-5 do contrato intactas; transcritor-LLM real + gate de forma seguem fatia futura. Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.BE host; medição extract_text dos 6 PDFs; D-ARQ-47]`

**Aplicação na sessão 003.BF (02/07/2026) — IMPLEMENTAÇÃO fatia 2:** invocação injetável + gate de forma + harness mockado (cláusulas 1-3/5). Módulo greenfield `transcritor_fds.py`: `TranscritorLLM` (Protocol, cl.1/2 — recebe TEXTO de `extrair_texto_fds`, emite `tuple[BlocoVerbatim,...]` CANDIDATO; cl.5 documentada na docstring como princípio da implementação real, prompt fica para a fatia do cliente); `transcrever_fds(texto, cliente)` como ponto único de invocação (cl.2 — cliente por parâmetro, nunca importado; instrumentação futura entra aqui); `gate_forma(blocos) -> (aprovados, pendencias)` (cl.3 — aprovado se ≥1 membro nomeado E faixa vazia [→ AUSENTE, D-ARQ-34 P1] OU parseável pela MESMA `parsear_faixa` da montagem, consistência gate↔montagem por construção). Bloco reprovado é EXCLUÍDO + `Pendencia(tipo="forma_verbatim_fds", destinatario="extracao", bloqueante=True, regra_origem="D-ARQ-47")` — bloqueante espelha o ramo (c) do gate-CAS (dado corrompido, não ausência); a exclusão é anti-erro-silencioso: sem o gate, faixa não-vazia-e-ininteligível viraria `concentracao=None` na montagem, indistinguível de ausência legítima (classe D-ARQ-22). CAS não validado (D-ARQ-36, `gate_cas` a jusante). Cl.4 preservada por omissão deliberada: nenhuma função de produção compõe `transcrever_fds → gate_forma → montar_fds` — seria bypass da revisão-RT; a composição fim-a-fim existe SÓ no harness de teste. Harness (integração, `requer_pdfs`): tinta acrílica + Ciplan — `extrair_texto_fds` real → mock injetado (texto recebido assertado contra a âncora) → gate → `montar_fds` → `resolver_composicao` → pareamento `cas`+`concentracao` contra `fds_t65` (`nome` não-`==`, D-ARQ-42 P4). Limite (D-ARQ-22): Tigre fora do harness — transcritível provado na medição 003.BD (7/7), mas fixture verbatim é dado de julgamento humano (Arquiteto), não desta fatia. 10 testes (8 núcleo sem PDF + 2 integração); suíte 507→517 (host); mypy --strict delta-zero (46 pré-existentes, nenhum nos arquivos novos). 1ª rodada do Code aprovada na revisão do Arquiteto sobre git objects, sem correção. Commit `0cf24fd`, merge `591a4d8`, PR #136, "Create a merge commit". Resta da DT-003AS-01: cliente-LLM real + prompt (cl.5 mecanismo fino), costura `None`→`Pendencia` do `extrair_texto_fds`, e o ponto de revisão-RT (cl.4). Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.BF host; D-ARQ-47 cl.1-3/5]`

**Aplicação na sessão 003.BG (03/07/2026) — IMPLEMENTAÇÃO fatia (e1):** cliente-LLM real + prompt (cl.5) + costura `None`→`Pendencia`, parando antes de `montar_fds` (cl.4 intacta). Adaptador `TranscritorGemini` (`adaptadores/transcritor_gemini.py`, fora do motor por D-ARQ-48): cascata 4 modelos Gemini, `temperature=0`, chave `CHAVE_API_GOOGLE` `st.secrets`→`os.environ`, prompt cl.5 (triplo nome+CAS+faixa verbatim, roteamento por formato-de-token, descarta linha sem CAS+faixa, CAS oculto→`""`, nome multi-linha reassemblado), parse JSON→`tuple[BlocoVerbatim,...]`. `preparar_composicao` (`adaptadores/orquestracao_fds.py`): extrair_texto_fds→transcrever_fds→gate_forma; NÃO chama montar_fds (cl.4). Revisão do Arquiteto sobre objects pegou bloqueador (falha de invocação colapsando em `()` silencioso); corrigido com `TranscricaoIndisponivel`→`Pendencia` bloqueante `transcricao_indisponivel_fds`, distinta de `composicao_ausente_fds`; `{"blocos":[]}` segue `()` legítimo (anti-supressão D-ARQ-31/35). cl.1/2/5 exercidas; cl.3-em-produção e cl.4 (revisão-RT) seguem para (e2). **Adaptador Gemini real NÃO verificado ao vivo** (teste `@requer_api` skipado) — validação é pré-requisito bloqueante de (e2). 517→538 verdes, mypy delta-zero. Commit `34077c9` + fix `879a085`, merge `391a2da`, PR #138. Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.BG host; D-ARQ-47 cl.1/2/5; D-ARQ-48]`

**Aplicação na sessão 003.BI (05/07/2026) — IMPLEMENTAÇÃO fatia (e2):** revisão-RT (cl.4) + serialização verbatim ida/volta — FECHA DT-003AS-01. Módulo greenfield `motor/revisao_verbatim.py` (puro, sem I/O, D-ARQ-48 preservada): `VerbatimInvalido(ValueError)`; `serializar_verbatim` (JSON `ensure_ascii=False`/`indent=2`, envelope `{"versao":1,"blocos":[...]}`); `desserializar_verbatim` (schema ESTRITO: campo extra/faltante/tipo errado/versão desconhecida → `VerbatimInvalido` com mensagem indexada por bloco/membro; nunca aceitação parcial — anti-erro-silencioso, classe D-ARQ-22); garantia round-trip `desserializar(serializar(x)) == x`, inclusive `\n` intra-token (TiO₂/nome multi-linha — razão da escolha JSON sobre formato tabular: fidelidade byte-exata do verbatim). `montar_fds_revisado` = `gate_forma` → `montar_fds` sobre o verbatim PÓS-revisão-RT: a admissão do candidato ancora em R-PGR-01/D-ARQ-33 cl.4 (cl.4 de D-ARQ-47); NÃO é o bypass vedado pela nota de `transcritor_fds.py` (aquele parte do candidato cru). Re-passar no `gate_forma` é deliberado: edição do RT pode introduzir forma inválida; mesmo gate = consistência por construção. Fora do escopo, declarado: tradução `VerbatimInvalido`→`Pendencia` e o ponto de UI onde o RT edita (Streamlit) — fatia futura. Limite declarado: nada impede estruturalmente chamador futuro de passar candidato cru a `montar_fds_revisado`; enforcement é processo/UI (já era limite de D-ARQ-47). Observação de revisão (não-bloqueante): rejeição de campo extra no ENVELOPE implementada sem teste dedicado (8 casos de rejeição da spec cobertos). 17 testes (`test_revisao_verbatim.py`: round-trip ×5, rejeições ×8, `montar_fds_revisado` ×2, fim-a-fim tinta com revisão simulada vs. `fds_t65`, edição-RT efetiva). Suíte 540→557, 3 skipped; mypy --strict delta-zero. Revisão do Arquiteto sobre objects: aprovada sem correção. Commit `d5c60d4`, merge `0b89904`, PR #142, "Create a merge commit". Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.BI host; D-ARQ-47 cl.4]`

## D-ARQ-48 — Fronteira de impureza: adaptador-LLM fora do motor, invariante de pureza testável

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003.BG).

**Decisão.** O cliente-LLM concreto vive em `agente_medico/adaptadores/`, nunca em `agente_medico/motor/`. `adaptadores/` importa `motor/`; o inverso é PROIBIDO. O motor recebe só o Protocol `TranscritorLLM` (D-ARQ-47 cl.2) e o `tuple[BlocoVerbatim,...]` já desembrulhado — nunca sabe que existe HTTP, chave, cascata de modelo ou SDK. Invariante materializada em `test_pureza_motor.py` (AST sobre `motor/` via `rglob`): nenhum módulo importa `requests`/`streamlit`/`google.generativeai`/`genai` nem lê `os.environ`.

**Consequência.** Resolve as duas questões abertas do handoff 003.BF de forma universal: fornecedor isolado (D-ARQ-06 — trocar Gemini→Claude toca só `adaptadores/`, zero linha no motor) e chave fora do motor (lida no adaptador). Preserva D-ARQ-09 (motor determinístico; LLM a montante do verbatim, via injeção).

**Limite (D-ARQ-22).** O teste de pureza detecta `os.environ` por acesso-de-atributo, não `from os import environ`. Borda teórica — motor puro hoje; refinamento aberto, não-bloqueante.

**Base.** Sessão 003.BG (03/07/2026), IMPL fatia (e1) sob D-ARQ-47. `[DERIVADO — IMPL 003.BG host; motor auditado puro sobre objects]`

**Nota 003.BH (05/07/2026).** Validação ao vivo revelou 4º modo de falha de invocação — resposta HTTP 200 com finishReason != STOP (thinking do gemini-2.5-flash compartilha o budget de maxOutputTokens; truncamento não-determinístico, thoughtsTokenCount medido 4320–13231). Gate de integridade dentro do adaptador: só 200 + STOP atravessa a fronteira; teto artificial removido do payload. Reafirma o princípio da fronteira: anomalia de transporte/geração vira TranscricaoIndisponivel, nunca atravessa como dado. `[DERIVADO — medição+IMPL 003.BH host; D-ARQ-48]`

## D-ARQ-49 — Contrato do parse-PGR: instância-PGR de D-ARQ-41; recorte esqueleto-GHE (cargos+riscos+quantificação crus + FDS apontadas); mecanismo termo→slug adiado por medição

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação por fatias futuras; a medição que destrava o mecanismo é sessão CONHECIMENTO própria. Autorização para virar D-ARQ é do Diovanni.

**Contexto.** D-ARQ-25 Parte B ("normalização de vocabulário é responsabilidade da extração, a montante do motor; mecanismo é decisão de implementação") deixou o parse-PGR (PDF/docx → `tipos.PGR`) greenfield, mecanismo indeciso. D-ARQ-41 fixou o padrão bicamada de toda extração (transcritor-LLM + resolvedor determinístico, fronteira = contrato transcrito tipado) e nomeou as duas instâncias — parse-PGR e transcrição-FDS — mas deixou aberto, para o parse-PGR: a forma do tipo "PGR transcrita" (P2) e o mecanismo `termo→slug` + granularidade (P3, adiado por medição sobre os PGRs de DT-003L-01). A instância-FDS FECHOU (DT-003AS-01, 003.BI: cadeia extração→LLM→gate→revisão-RT→montagem→resolvedor completa) e serve de template: D-ARQ-42 cravou contrato+recorte+gabarito+fronteira-parse↔LLM da FDS **antes** da medição (003.AN), adiando só o mecanismo fino. Esta decisão faz o mesmo para o parse-PGR — é o **irmão de D-ARQ-42 do lado-PGR**, a segunda metade da porta de entrada.

**Gate de estado real (disco, 003.BJ).**
- parse-PGR greenfield: `git grep -E "termo.*slug|normaliz.*vocab|pgr_transcrit" -- agente_medico/**/*.py` → zero hits. Nenhuma camada de extração de PGR no motor novo. `[DERIVADO — grep, 003.BJ]`.
- **Gabarito-par existe em disco:** `agente_medico/tests/fixtures/pgr_viverde.py` (`tipos.PGR` transcrito à mão) ↔ `matrizes_originais/PGR VIVERDE V02 - 03.02.25.{pdf,docx}`. Mesmo arranjo que destravou a FDS (`fds_t65` ↔ `fds_originais/`). `[DERIVADO — find/ls, 003.BJ]`. O casamento fixture↔documento é `[INTERPRETADO — confirmar abrindo o PGR na medição/IMPL]`.
- Contrato de saída `tipos.PGR` já materializado (D-ARQ-25 Parte C, 002.Q: `Quantificacao.pct_quartzo`, `GHEPGR.cenario`; `fracao` notado 002.V) — o tipo que a extração preenche está pronto; falta a camada que o preenche. `[DERIVADO — D-ARQ-25 Parte C em disco]`.

**Decisão — quatro partes (espelham D-ARQ-42).**

*Parte 1 — o parse-PGR é a camada bicamada interna da instância-PGR de D-ARQ-41.* Parse-doc (determinístico: `.docx`/`.pdf` → texto/estrutura) → transcrição-LLM (texto → "PGR transcrita"). Fronteira interna = texto/estrutura extraída; a transcrição-LLM recebe texto, não bytes. Razão D-ARQ-09 (leitura de bytes é determinística e testável sem API; misturá-la com a transcrição borraria a fronteira que sustenta a pureza). Diferença medível vs. o lado-FDS: o PGR Viverde é `.docx` nativo (+ `.pdf`) — provável parse mais limpo, sem o OCR-sujo que o Ciplan trouxe (D-ARQ-42 fronteira-OCR); se a fronteira-OCR recorre é questão da medição, não presumida. `[DERIVADO — D-ARQ-41 P1; D-ARQ-09]`.

*Parte 2 — recorte da 1ª fatia = esqueleto GHE.* A "PGR transcrita" da 1ª fatia carrega: árvore de GHEs `{id, nome}`; **cargos e riscos como texto cru** (linguagem natural, sem slug); **quantificação como transcrita** (valor + unidade + qualificador em texto, sem normalizar); **FDS apenas apontadas** (referência ao produto/documento de composição — NÃO a composição resolvida; alimenta a cadeia química já pronta `resolver_composicao`/`gate_cas` a jusante, não a reconstrói). FICAM FORA da 1ª fatia, nomeados como diferidos: **EPIs** (R-PGR-03 sinal-EPI), **psicossocial** (R-PSY-01), e os **campos-de-topo dos gates** (`PGR.validade`, `PGR.assinatura_engenheiro` — R-PGR-01/R-PGR-06). Razão: `cargos+riscos+quantificação` é a espinha que R-GHE-*/emissão consomem — a maior massa restante da porta de entrada; EPIs/psi/gates são segundo-ordem (sinal indireto, condicional) ou leitura de campo-de-topo trivial. **Universalidade (gate CLAUDE.md):** o esqueleto GHE/cargo/risco é a espinha de qualquer PGR — construção civil, indústria química, saúde; as 6 formas de declaração química de DT-003L-01 vivem ABAIXO dele, no ramo químico, não no esqueleto. `[INTERPRETADO — recorte recomendado pelo Arquiteto, ratificado pelo Diovanni em 003.BJ]`.

*Parte 3 — a SEMÂNTICA da "PGR transcrita" é cravada; a FORMA concreta do tipo, NÃO.* Semântica cravada (espelha D-ARQ-41 P2 e o "CAS transcrito"/"verbatim FDS" de D-ARQ-46): termos crus, FDS apontadas, sem slug, sem composição resolvida, sem quantificação normalizada. Forma concreta — dataclass própria vs. dict estruturado vs. `tipos.PGR` com campos-slug vazios — é decisão de IMPL da fatia, condicionada ao que o disco mostrar; cravá-la aqui seria literal sem fonte (barrado por D-ARQ-22). `[INTERPRETADO — a peça nova, sem âncora normativa; espelha D-ARQ-41 P2]`.

[NOTA 003.BN — P3 FECHADO na IMPL: forma concreta da "PGR transcrita" = GHEVerbatim(nome, cargos, riscos) + RiscoVerbatim(agente, quantificacao, fonte_geradora), frozen dataclasses em tipos.py (commit d4fa02a, PR #150). SEM campo id (o doc não traz — D-ARQ-50 C1; id pelo LLM seria identidade silenciosa, classe D-ARQ-22; atribuição a jusante). Multi-agente do mesmo ET achatado em riscos separados com fonte_geradora copiada (sem grupo-verbatim: nada herda valor — difere do lado-FDS). Gate de forma do lado-PGR (molde D-ARQ-47 cl.3) emite Pendencia com regra_origem="D-ARQ-49" — não existe D-ARQ próprio do gate-PGR, por decisão (assimetria com a FDS registrada aqui). GHE com riscos=() passa o gate: forma legítima; perda-silenciosa de riscos não é detectável por forma.]

[NOTA 003.BO — regra 3c do prompt real (calibração PASSO 0, ET02–04): perigo de acidente sem valor numérico é transcrito com o texto do perigo como agente (ex.: "Contato com o disco desprotegido") e quantificacao="" — amplia a semântica de RiscoVerbatim.agente nos qualitativos; verbatim e bounded, resolvedor a jusante trata (D-ARQ-50 P2). Commit 2abf42a, PR #152.]

[NOTA (sessão não numerada, branch `claude/fervent-brown-7dcc0y`, 17/09/2026) — psicossocial (diferido acima, "R-PSY-01") ganha extrator: `detectar_psicossocial` (`extracao_pgr.py`) varre o texto cru do PGR inteiro por 3 marcadores ("Inventário de Riscos Psicossociais"/COPSOQ/FRPRT, case-insensitive) e popula `GHEPGR.psicossocial`, replicado a todo GHE do documento (sinal de PGR inteiro, não por GHE — mesma leitura da Parte 2 acima). `hidratar_ghe`/`hidratar_pgr` ganham parâmetro `psicossocial: bool = False` em vez do hardcoded `False`; `processar_arquivo_pgr` roda uma 3ª leitura de `extrair_texto_pgr` sobre o mesmo arquivo (mesma classe da duplicação já documentada em D-ARQ-52/53 entre `preparar_envelope`/`preparar_ghes`). Consumidor: `R-PSY-03` (`regras.yaml`, `predicados.py`), sucede `R-PSY-02` (DEPRECATED — fundamento refutado, `DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-01`). EPIs e campos-de-topo dos gates seguem diferidos — esta nota fecha só a peça psicossocial. Nenhuma cláusula de D-ARQ-49 alterada.]

*Parte 4 — princípio do gabarito + mecanismo adiado por medição.* Gabarito: `pgr_viverde.py` ↔ PGR Viverde real (par em disco), campos verificáveis deterministicamente ancoram (`id`/`nome` de GHE; presença de cargos/riscos por GHE), LLM fixado/mockado, **nunca testa API**. Como no lado-FDS (D-ARQ-42 P4), campos texto-livre-de-LLM (nome cru de cargo/risco) NÃO são gabaritáveis por `==` — critério de aceitação próprio. **ADIADO POR MEDIÇÃO** (molde D-ARQ-42→003.AN e D-ARQ-41 P3): o mecanismo fino `termo→slug` — as 3 saídas candidatas de D-ARQ-41 P3 [(a) LLM verbatim + resolvedor-agressivo + sinônimos; (b) LLM normaliza para termo-conceito + resolvedor conceito→slug; (c) híbrido dicionário + candidato-LLM de baixa confiança]; a granularidade da fronteira (quanto o LLM normaliza); o prompt; o parse-doc de `.docx` (XML de tabela) vs. `.pdf`. DT-003L-01 mapeou só as formas QUÍMICAS do PGR; a disposição de GHE/cargo/risco/quantificação em PGR real ainda não foi medida — a medição é sessão CONHECIMENTO própria. Adiamento por dado ausente, não indecisão. `[DERIVADO — molde D-ARQ-42 P4 / D-ARQ-41 P3; DT-003L-01]`.

**Consequência.**
- Fecha padrão-instância + recorte + gabarito + fronteira-parse↔LLM do parse-PGR sem implementar — a segunda metade da extração ganha sua decisão de fronteira, como a FDS teve em D-ARQ-42.
- Determinismo do motor intacto (D-ARQ-09): toda LLM (parse-de-texto, transcrição) fica a montante da "PGR transcrita"; o resolvedor `termo→slug` e o motor seguem puros.
- Honestidade de escopo: NÃO fecha o mecanismo `termo→slug`, a forma concreta do tipo, o prompt, o parse `.docx`/`.pdf`, nem o critério de `nome` — todos adiados para a medição. NÃO tira de produção: a entrada segue fixture até a transcrição-LLM existir (D-ARQ-25 Parte B); a fachada `processar_pgr` (D-ARQ-40) é estável à injeção do extrator.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v41 inalterado). Cria contrato de camada de extração-PGR.

**Aberto para a sessão de medição (CONHECIMENTO — gate de estado real obrigatório):**
- Abrir o PGR Viverde (`.docx` e `.pdf`) e confirmar o casamento com `pgr_viverde.py`: a fixture bate com o documento? `[A CONFIRMAR — medição]`.
- Medir a estrutura de GHE/cargo/risco/quantificação em PGR real (Viverde + amostra multi-setor de DT-003L-01): quão estruturável; `.docx` (XML de tabela) vs. `.pdf` (pdfplumber); a fronteira-OCR de D-ARQ-42 recorre?
- Decidir a saída (a/b/c) de `termo→slug` medindo onde caem os falsos `vocabulario_ausente` (termo de risco é texto fluido: "ruído" / "ruído contínuo" / "exposição a ruído acima de 85 dB").
- Decidir o critério de aceitação de `nome` cru (cargo/risco).

**Fronteiras (não confundir):**
- **D-ARQ-25 Parte A/B** — Parte A é o contrato de saída (`tipos.PGR`); esta decisão dá forma à Parte B (extração-PGR a montante) que a Parte B dava só como prosa.
- **D-ARQ-41** — esta é a instância-PGR concreta do padrão fixado em abstrato; "PGR transcrita" é a fronteira transcrita do lado-PGR, gêmea do "CAS/verbatim transcrito" do lado-FDS. P3 (mecanismo `termo→slug`) é retomado e mantido adiado por medição.
- **D-ARQ-42** — irmão do lado-FDS: mesmo corte (contrato+recorte+gabarito antes; mecanismo por medição depois). O parse-PGR NÃO reusa o transcritor-FDS — documento-fonte distinto, resolvedor distinto (`termo→slug`, não CAS→slug).
- **D-ARQ-40** — `processar_pgr` (fachada) já recebe `tipos.PGR` cru; o parse-PGR é o que passará a produzir esse `tipos.PGR` (hoje fixture). A assinatura da fachada é estável à injeção (D-ARQ-40 cl.3).
- **D-ARQ-09** — preservada: a fronteira parse-doc↔transcrição-LLM e a "PGR transcrita" são onde o LLM para e o determinístico começa.
- **D-ARQ-14** — reusado: termo cru sem slug → `vocabulario_ausente` não-bloqueante; vocabulário append-only alimentado pelas pendências.
- **DT-003L-01** — input empírico (6 formas químicas) da IMPL; não resolvida aqui. A medição de esqueleto-GHE a complementa (formas de cargo/risco/quantificação, ainda não medidas).

**Base.** Sessão 003.BJ (05/07/2026). Instância-PGR de D-ARQ-41; irmão de D-ARQ-42; dá forma à Parte B de D-ARQ-25 para o lado-PGR. Gate de estado real: parse-PGR greenfield (grep zero), gabarito-par `pgr_viverde.py` ↔ PGR Viverde `.docx`/`.pdf` em disco, contrato `tipos.PGR` já materializado (Parte C). Duas passadas adversariais sobre a síntese: (1ª) propôs congelar a forma concreta do tipo "PGR transcrita" nesta sessão; (2ª) corrigiu — forma concreta é IMPL (D-ARQ-41 P2), literal sem fonte de disco → só a semântica se crava; e o mecanismo `termo→slug` é adiado por medição, não decidido (DT-003L-01 cobre só o químico, não o esqueleto GHE/cargo/risco). Decisão de arquitetura — sem código.

## D-ARQ-50 — Medição do PGR Viverde fecha parse-doc e mecanismo termo→slug do parse-PGR; irmão de D-ARQ-43 do lado-PGR

**Status:** DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA). Sem código. Fecha os pontos que D-ARQ-49 Parte 4 adiou por medição; irmão de D-ARQ-43 (que fez o mesmo para a FDS). Autorização para virar D-ARQ do Diovanni, ratificada em 003.BK.

**Contexto.** D-ARQ-49 Parte 4 adiou "por medição sobre o PGR Viverde real": parse-doc `.docx` vs `.pdf`, mecanismo `termo→slug` (a/b/c de D-ARQ-41 P3), granularidade, prompt, critério de `nome` e o casamento fixture↔documento. A 003.BK mediu — extração determinística (`python-docx` + `pdfplumber.extract_text`/`extract_tables` sobre os bytes) do par `matrizes_originais/PGR VIVERDE V02 - 03.02.25.{docx,pdf}` ↔ `agente_medico/tests/fixtures/pgr_viverde.py`. Esta decisão faz para o parse-PGR o que D-ARQ-43 fez para a FDS: fecha fronteira-de-parse e cataloga o resíduo como input da IMPL.

**Gate de estado real (literais da medição, 003.BK).**
- `.pdf`: 151 págs, producer **FPDF 1.86** — nativo digital, zero OCR (a fronteira-OCR de D-ARQ-42/43 NÃO recorre — medido, não presumido). 42 blocos GHE (`SETOR/FUNÇÃO`); inventário como header linear `RÓTULO valor` + grid de classificação largo. `[DERIVADO — metadata + extract_text, 003.BK]`.
- `.docx`: 214 tabelas, 1911 parágrafos. Inventário = tabelas 20-col **rotacionadas** com o header (ETAPA/PROCESSO/GHE/ATIVIDADES/SETOR-FUNÇÃO/cargos/atividade-detalhada) **fundido num blob mesclado replicado em 18 colunas**; grid de classificação em células endereçáveis. `[DERIVADO — python-docx, 003.BK]`.
- Teste de perda-silenciosa (classe D-ARQ-22): `extract_text` do PDF recuperou **todos** os valores medidos da GHE-Pintura densa (`78,8 dB(A)`, `Etanol 4,4 ppm`, `Acetato de Etila 1 ppm`, `Tolueno 6,3 ppm`), com adjacência agente↔valor e agrupamento multi-agente sob o mesmo `ET` preservados. Diferente do `extract_tables` da FDS (perdia faixa em silêncio, D-ARQ-AY), o `extract_text` do PGR não perde valor. `[DERIVADO — medição pág. 71, 003.BK]`. `[CORRIGIDO 003.BL: o literal "78,2" registrado originalmente não existe como texto em nenhum dos dois formatos — verificação independente sobre git objects; as ocorrências de "78,2" no XML do .docx eram coordenadas de desenho vetorial. Texto do .docx = {78,3: 1, 78,8: 4}, idêntico ao text layer do PDF — sem perda silenciosa; reforça P1.]`

**Decisão — dois fechamentos + um catálogo.**

*Parte 1 — parse-doc FECHADO: PDF via `pdfplumber.extract_text` (text-puro), não `.docx`.* O parse-doc determinístico (camada interna de D-ARQ-49 P1) é `pdfplumber.extract_text` sobre a camada de texto do PDF — NÃO `.docx`/python-docx nem `extract_tables`. Justificativa medida, com trade-off REAL e assimétrico: o `.docx` é mais colunar no grid de risco (células reais) mas FUNDE o header GHE no blob mesclado; o PDF lineariza header+cargos limpos mas interleava o grid. A decisão NÃO é "PDF é mais limpo em tudo" (não é); é movida por (i) **universalidade (D-ARQ-06)** — `.docx` não é garantido no acervo (os 15 PGRs de DT-003L-01 são PDF; `.docx` é exceção do Viverde), construir sobre a estrutura `.docx` é solução-pontual; (ii) **reuso do paradigma** text-puro+LLM-semântico já selado para a FDS (D-ARQ-41/42/AY) — o grid interleavado é o caso "ler por sentido" já sancionado, não paradigma novo; (iii) zero-OCR medido (FPDF nativo). `.docx` fica como cross-check determinístico/fallback opcional, decidido na IMPL — não entrada primária. Paliativo sinalizado: PGR só-`.docx` sem PDF → parse-XML `.docx`, contingência declarada (molde "casa antes do morador", D-ARQ-40 cl.4), não a via primária. `[DERIVADO — medição 003.BK; D-ARQ-06; D-ARQ-49 P1]`.

[NOTA 003.BM: a IMPL do recorte-GHE fixou âncora VERBATIM startswith("SETOR/FUNÇÃO"), sem normalização — medição 003.BM: 42 blocos, 0 ocorrências contains-sem-startswith; 1ª âncora pág. 33, última pág. 146/151 (cauda de 4 págs. sobre-incluída no último bloco); bloco cruza fronteira de página (Pintura, págs. 71–73). Generalização da âncora multi-PGR é medição futura sobre a amostra de DT-003L-01.]

[NOTA 003.BO — correção de literal (classe v86/003.BL): a Fonte geradora do bloco Pintura é "Thinner/Zarcão e tinta esmalte sintético" (célula quebrada em 2 linhas pelo PDF; verificação determinística no bloco 12). O "Thinner/Zarcão" citado nesta D-ARQ e em 003.BK é forma abreviada da medição — onde esta D-ARQ o cita como exemplo, ler a forma longa. Validação ao vivo 003.BO: LLM reagrupou por sentido e transcreveu a forma longa corretamente. Commit aedf1e6, PR #152.]

[NOTA 003.BP — Parte 2 MATERIALIZADA: resolvedor determinístico em motor/resolvedor_termos.py. As 3 granularidades deixadas à IMPL, fechadas: (i) normalização determinística (NFKD sem acento, casefold, pontuação→espaço, espaços→"_") — o typo de acento da cauda medida ("fisico") morre aqui e os próprios slugs formam o índice base sem sinônimo algum; (ii) fuzzy = Levenshtein ≤2 sobre a forma normalizada, slug ÚNICO na distância mínima, sempre Confianca.FUZZY (baixa-confiança, nunca certeza — roteamento p/ revisão é do consumidor futuro); empate entre slugs distintos → NAO_RESOLVIDO (classe D-ARQ-22); (iii) tabela de sinônimos = campo opcional termos: por entrada de agentes.yaml, índice reverso no molde construir_indice_cas, colisão→ValueError ruidoso; campo NÃO populado — alias real (ex.: "Thinner"→slug) é escolha química, sessão de dado futura (nit registrado: termos: como string em vez de lista iteraria por caractere — guarda é dessa sessão). "Thinner" NAO_RESOLVIDO por design (produto ≠ agente). Resíduo → Pendencia(vocabulario_ausente, D-ARQ-14) não-bloqueante, regra_origem D-ARQ-50. Isolado sem consumidor (molde 003.J/003.S) — hidratação GHEVerbatim→tipos.PGR é fatia futura. Commit 6bbbce6, merge 4abeaf9, PR #154.]

[NOTA 003.DM — Parte 2, campo `termos:` POPULADO (Tier 1). O mecanismo existia desde 003.BP mas nascia vazio: alias real foi declarado "escolha química, sessão de dado futura". Esta sessão fecha a Tier 1 com 20 aliases, todos derivados do texto oficial do Anexo I da NR-07 (Quadros 1 e 2, Portaria MTP 567/2022, PDF `nr-07-atualizada-2022-1.pdf` em gov.br/trabalho-e-emprego). CRITÉRIO DE ADMISSÃO DA TIER 1: entra a grafia literal da substância no Anexo I quando difere do slug após `normalizar_termo()`. Não entra sigla comercial. Razão: a grafia do Anexo é [DERIVADO] de fonte normativa primária, auditável e não-ambígua; sigla é jargão sem fonte normativa e com ambiguidade real. Caso decisivo — `TCE` é usado tanto para tricloroetileno quanto para 1,1,1-tricloroetano, e AMBOS estão no vocabulário: popular seria escolha silenciosa entre agentes distintos, classe D-ARQ-22. `TCE` fica proibido sem decisão explícita registrada. RECORTE: 18 aliases são citação integral [DERIVADO]; 2 são recorte do literal e carregam [INTERPRETADO — recorte do literal] no próprio YAML (`arsenio` ← "Arsênico", integral "Arsênico elementar e seus compostos inorgânicos solúveis, exceto arsina e arsenato de gálio"; `tdi` ← "Tolueno diisocianato", integral "2,4 e 2,6 Tolueno diisocianato (puros ou em mistura dos dois isômeros)") — a frase institucional integral não é o que um PGR escreve. O QUE A TIER 1 DESTRAVA, MEDIDO: a divergência grafia-normativa × slug é sistemática, não pontual, e boa parte cai FORA do raio fuzzy ≤2, logo não era salvável por Levenshtein — "Sulfeto de carbono"→`dissulfeto_de_carbono` dista 3 (resolvia NAO_RESOLVIDO); "Indutores de Metahemoglobina" e "Inseticidas inibidores da Colinesterase" distam 3 pelo "de"/"da"; "Flúor, ácido fluorídrico e fluoretos inorgânicos"→`fluoretos`. Outras resolviam apenas FUZZY (baixa-confiança) e passam a EXATA: "Xilenos", "Arsênico", "Metiletilcetona (MEK)". VERIFICAÇÃO PRÉVIA DO ARQUITETO (simulação de `normalizar_termo` + Levenshtein reais sobre agentes.yaml em c45759e, antes do prompt): colisão exata ValueError — nenhuma; alias redundante (que normalizasse para o próprio slug) — nenhum; pares dist ≤2 apontando a slugs distintos 4→5, sendo o único par novo (`2_butoxietanol`↔`2_metoxietanol`) espelho de um par de slugs já existente, logo nenhuma classe nova de ambiguidade fuzzy; regressão herdada 8/8. Conferido contra o commit pós-fato: índice real 99, spec == commit nos 20. `termos` é lista nos 20, mesmo com um elemento — o nit da 003.BP (string faria `formas_brutas.extend` iterar por caractere) respeitado. Guard de inventário movido no mesmo commit (lição da 003.CV): `test_indice_real_tem_79_entradas`→`_99_entradas`, 79 slugs + 20 aliases. Zero deleção em agentes.yaml — nenhum campo pré-existente tocado. Motor intocado. Nenhuma R-* criada ou alterada. Suíte 899+6→919+6 (+20 exato). Commit 190e9aa, merge 9527d9e, PR #240. Tier 2 (siglas) fica bloqueada por DT-003DM-01.]

[NOTA 003.DN — Parte 2, piso bilateral no fuzzy FECHA DT-003DM-01. `PISO_FUZZY = 4` em `motor/resolvedor_termos.py`: forma normalizada com `len <= 4` não entra no fuzzy nem como termo de busca nem como chave candidata — bilateral, porque um piso só do lado-busca deixaria a chave curta (`mibk`, 4 chars) ser atingida por uma busca mais longa pela porta de trás (`mibk9`, dist 1); `test_termo_curto_com_sufixo_nao_aterrissa_em_sigla` crava esse lado. Abaixo do piso, resolução é só EXATA: `HDI`→`hdi` continua EXATA; `hdl` digitado deixa de resolver `hdi` por FUZZY (o comportamento que a DT apontava como falha) e cai em `NAO_RESOLVIDO`/`vocabulario_ausente` (`test_sigla_typada_nao_resolve_vizinha`, `test_sigla_exata_continua_exata`). NÃO elimina os pares dist ≤2 entre chaves >4 já registrados em DT-003DM-01 (`etanol`↔`metanol`, `metil_etil_cetona`↔`metil_butil_cetona`, `metoxietanol_2`↔`butoxietanol_2`) — a DT nunca prometeu isso: o alvo era a sigla curta, e a colisão de chaves longas já caía no ramo seguro (empate→`NAO_RESOLVIDO`, D-ARQ-22 respeitado). Teste de vigia `test_vigia_pares_fuzzy_chaves_longas` fixa um gabarito FECHADO desses pares sobre o índice real de 99 entradas (inclui 1 par novo introduzido pelos aliases da 003.DM, `2_butoxietanol`↔`2_metoxietanol`) — para que uma futura adição ao vocabulário que abra um par novo quebre o teste em vez de caducar em silêncio, a própria lição que a DT registrou ("ninguém re-mediu entre 003.BP e 003.DM"). Reparo no mesmo lote (commit `6e956cd`): o teste sintético de empate (`test_empate_fuzzy_entre_dois_slugs_nao_resolve`) usava chaves ≤4 chars (`bat`/`cot`/`cat`), que passaram a cair sob o piso e deixaram de exercitar o ramo de empate fuzzy — substituídas por chaves >4 (`abcdef`/`abcdeg`/`abcdeh`), restaurando a cobertura original. Motor tocado (`resolver_termo`), zero mudança de dado (`agentes.yaml` intocado). Tier 2 (siglas) segue não-populada — pré-requisito de motor cumprido, decisão de popular siglas fica para sessão de dado dedicada. Suíte 919+6→923+6 (+4 exato, verificado nesta sessão META); `mypy --strict agente_medico/motor/` limpo, delta-zero. Commits `c96e73f`+`6e956cd`, merge PR #242, main `d703aa3`.]

[NOTA 003.DW — Parte 2, `silica.termos` populado + critério Tier 1 estendido (DT-003DV-01 faceta A). 6 grafias de sílica cristalina livre (Sílica livre / cristalizada / cristalina, Quartzo, Cristobalita, Tridimita) → slug `silica`, EXATA. Fonte: NR-15 Anexo 12 "Sílica Livre Cristalizada" + NR-07 Anexo III Quadro 1 — NÃO Anexo I (sílica é poeira-mineral/RX, não biomonitoramento); o comentário do critério Tier 1 em `agentes.yaml` passa a admitir a fonte-por-natureza-do-agente. Anti-FP D-ARQ-22 em teste: silicatos / poeira respirável / poeira de madeira NÃO resolvem para `silica`. Índice 99→105, slugs 79 inalterado, sem colisão; vigia de pares fuzzy (003.DN) verde sob +6 aliases. Faceta B (fuzzy `Silício`→`silica`) deferida a 003.DX. `[DERIVADO — corpus Fascino 003.DV; NR-15 Anexo 12 / NR-07 Anexo III Quadro 1 via web]`; literal cristalizada/cristalina `[INCERTO — texto oficial MTE]`. Commit `8363fcb`, merge PR #253 (`862fd57`).]

*Parte 2 — mecanismo termo→slug FECHADO: (c)-shaped — LLM normaliza linguisticamente bounded, resolver é a autoridade determinística de slug + flag de confiança.* Das 3 saídas de D-ARQ-41 P3, a medição descarta (a) e (b) e refina (c): (a) [verbatim + resolver-agressivo + sinônimos] quebra na cauda de typos medida (`Eaquipamento desprotegido`, `Microrganismo (bacterias, fugos)`, `fisico`) — normalização exata não pega erro ortográfico e o dicionário de sinônimos vira perseguição infinita; (b) [LLM normaliza para conceito] lida com typo melhor, MAS a escolha de conceito É a escolha de slug em silêncio — viola o gate D-ARQ-41-P1 (classe de erro D-ARQ-22). (c) mantém a escolha de slug determinística e auditável **onde importa clinicamente** (slug químico/físico dispara biomonitoramento/exame) e empurra a cauda de typo — majoritariamente acidente/ergonômico, baixa criticidade — para revisão (candidato-LLM baixa-confiança, zona R-FDS-04 de D-ARQ-36 P1), não erro silencioso. Forma refinada que dissolve a falsa nitidez a/b/c: o LLM-transcritor faz normalização linguística **bounded** (tira qualificador `(Aguardando avaliação)`, quebra composto `Movimento repetitivo e esforço fisico`, corrige typo óbvio) e SEPARA agente de quantificação fundida (`Tolueno 6,3 ppm`, `Ruído\n89,6 dB(A)`) — leitura semântica bounded já sancionada em D-ARQ-AY — mas NÃO emite slug; o resolver determinístico faz termo-normalizado→slug contra o vocabulário + emite `Pendencia(vocabulario_ausente)` (D-ARQ-14) / flag de baixa-confiança no resíduo. A granularidade fina (limiar de edit-distance, forma da tabela de sinônimos, forma do sinal de confiança) fica para a IMPL. `[DERIVADO — medição de fluidez 003.BK; D-ARQ-41 P1/P3; D-ARQ-14; D-ARQ-22]`.

*Parte 3 — catálogo (input cravado da IMPL; casamento e recortes de gabarito).*
- **(C1) Casamento fixture↔documento é de FORMA, não de contagem/conteúdo.** PDF tem 42 blocos `SETOR/FUNÇÃO`; a fixture tem 32 GHEs canônicos (`MAPA_GHE_VIVERDE.md` re-agrupou). Agentes químicos divergem: o doc traz `Tolueno`/`Xileno`/`Acetato de Etila` inline que a fixture NÃO tem; a fixture tem `dioxido_de_titanio`/`propanediamina` que vêm de FDS, não do inventário-texto. A fixture foi construída do MAPA (doc intermediário), não do PGR cru. → confirma D-ARQ-18 (gabarito é forma); o critério de aceitação compara ESQUELETO (presença/forma de GHE/cargo/risco), não contagem de GHE nem conjunto exato de agente. `[DERIVADO — 42 vs 32 + diff de agentes, 003.BK]`.
- **(C2) Viverde é gabarito FORTE para o esqueleto, FRACO para FDS-apontada.** Viverde é DT-003L-01 forma-5 (agente genérico + composto inline): químicos declarados inline com ppm, produto no campo `Fonte geradora` (`Thinner/Zarcão`), NÃO via FDS apontada — 1 menção a FISPQ em 151 págs. → a 1ª fatia de IMPL (esqueleto GHE+cargos+riscos+quantificação) tem par-gabarito sólido no Viverde; a fatia FDS-apontada (D-ARQ-49 P2) exige gabarito forma-1 (T65/EURO com link `acrobat.adobe.com`), não o Viverde. `[DERIVADO — medição FISPQ + campo Fonte geradora, 003.BK]`.
- **(C3) Carga semântica bounded do LLM medida, não presumida.** O transcritor-LLM carrega: parear agente↔valor fundido na célula, agrupar multi-agente sob o mesmo `ET`, separar agente de quantificação, ler `Fonte geradora`. Tudo bounded (não parte/computa valor, não escolhe slug) — defensável como transcrição, resíduo candidato-revisão-RT (D-ARQ-33 cl.4). O grid de classificação (I/O/T/EP/PE/E, prob/sev/GR) é RUÍDO para o recorte D-ARQ-49 P2 — descartado, não transcrito. `[DERIVADO — medição págs. 33/71, 003.BK]`.

**Consequência.**
- Fecha parse-doc (Parte 1) e mecanismo termo→slug (Parte 2) que D-ARQ-49 P4 adiou; o catálogo C1–C3 é input da IMPL do parse-PGR.
- Não tira de produção: a IMPL do parse-doc + transcritor-LLM + resolver seguem a jusante; a entrada segue fixture até a transcrição-LLM existir (D-ARQ-25 Parte B); a fachada `processar_pgr` (D-ARQ-40) é estável à injeção.
- Determinismo do motor intacto (D-ARQ-09): parse-doc (`extract_text`) e resolver `termo→slug` são determinísticos; só a transcrição/normalização-linguística é LLM, a montante da "PGR transcrita".
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v41 inalterado). Fecha contrato da camada de extração-PGR. Complementa DT-003L-01 (esqueleto-GHE agora medido) sem tocar o PROTOCOLO.

**Fronteiras (não confundir):**
- **D-ARQ-49** — fecha os pontos que ela adiou (P4); não revoga. Recorte (P2), semântica-cravada (P3), bicamada interna (P1) intocados.
- **D-ARQ-43** — irmão do lado-FDS: mesmo molde (medição fecha fronteira-de-parse + cataloga resíduo). "PDF text-puro sem OCR" e "gabarito de forma" ecoam D-ARQ-43 P1/P2. O parse-PGR NÃO reusa o transcritor-FDS (documento e resolver distintos).
- **D-ARQ-41** — Parte 2 fecha o `termo→slug` que P3 adiou por medição; a bicamada (transcritor-LLM + resolver, gate de slug determinístico) é honrada.
- **D-ARQ-AY** — o "text-puro > tables" e "LLM lê grid-fundido por sentido" da FDS são reusados no PGR (Parte 1).
- **DT-003L-01** — a medição do esqueleto-GHE (formas de cargo/risco/quantificação) complementa o mapa das 6 formas químicas; C1–C3 são input da IMPL. Permanece ABERTA.

**Base.** Sessão 003.BK (06/07/2026). Medição determinística do par PGR Viverde `.docx`/`.pdf` ↔ `pgr_viverde.py`. Fecha parse-doc (PDF text-puro) e termo→slug ((c)-shaped). Passada de verificação crítica (pedida pelo Diovanni antes de ratificar): (1) teste de perda-silenciosa do `extract_text` PASSOU (valores + adjacência preservados) — a recomendação de parse-doc sobrevive ao ataque empírico; correção honesta — `.docx` é mais colunar no grid, PDF vence por universalidade+reuso, não por "mais limpo em tudo"; (2) recomendação de termo→slug reenquadrada — (b) lida com typo melhor mas viola o gate; (c) vence por auditabilidade onde importa clinicamente, o typo-tail é revisão de baixa-criticidade. Ratificada pelo Diovanni em 003.BK. Decisão de arquitetura — sem código.

## D-ARQ-51 — Hidratação GHEVerbatim → tipos.PGR: consumidor de produção do resolver termo→slug; id posicional, agente tri-estado→Optional, None-agente não-bloqueante

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO por fatias. 1a (contrato de tipo) materializada em 003.BQ; 1b (`hidratar_ghe`) e o parse de quantificação são fatias futuras. Autorização para virar D-ARQ do Diovanni (003.BQ).

**Contexto.** D-ARQ-49/50 fecharam a camada de extração-PGR até a "PGR transcrita" (`GHEVerbatim`, 003.BN) e o resolver `termo→slug` (`resolvedor_termos.py`, 003.BP) — este ISOLADO, sem consumidor de produção. Falta a peça que converte `GHEVerbatim` → `tipos.PGR`/`GHEPGR`/`RiscoPGR` consumindo o resolver: a hidratação. Dá vida ao resolver (D-ARQ-50 P2); é a 6ª fatia do parse-PGR.

**Decisão — quatro seams.**

1. **id do GHE = posicional determinístico.** `GHEVerbatim` não tem id (D-ARQ-50 C1: o doc não traz; LLM atribuir = identidade silenciosa, D-ARQ-22); `GHEPGR.id` exige `str`. A hidratação atribui id posicional sobre a ordem transcrita (`GHE-01`…), NÃO derivado de `nome` (texto-livre-de-LLM, colide — 42 blocos, vários "Pintura"). Honesto: handle do bloco transcrito, não id canônico. Paliativo sinalizado: id posicional ≠ id canônico; o re-agrupamento MAPA 42→32 é fatia downstream. `[DERIVADO — D-ARQ-50 C1; D-ARQ-22]`. (Fatia 1b — não materializado em 1a.)

2. **agente: `RiscoVerbatim.agente` (termo) → `RiscoPGR.agente` (slug), com o tri-estado do resolver.** EXATA→slug; FUZZY→slug + `Pendencia` não-bloqueante (candidato baixa-confiança revisado na saída, D-ARQ-47 cl.4); NAO_RESOLVIDO→`agente=None` + a `vocabulario_ausente` não-bloqueante que o resolver já emite. Risco NUNCA descartado (anti-supressão, D-ARQ-31/35 P3); slug NUNCA inventado (D-ARQ-22). Forçou `RiscoPGR.agente: str → Optional[str]`, espelho de `Componente.agente` do lado-FDS (D-ARQ-14). `[DERIVADO — D-ARQ-14; D-ARQ-31; espelho Componente.agente]`. **Materializado em 1a: a virada de tipo.**

3. **Política None-agente na Fase A do Stage 2 (classe D-ARQ-08).** Risco com `agente=None`: a Fase A não promove a `Risco` (`Risco.agente: str`; inventar = D-ARQ-22) e NÃO bloqueia — apenas `continue`. Não-bloqueante contra o espelho-FDS (`materialidade_ausente` é bloqueante): D-ARQ-14 é não-bloqueante por design e D-ARQ-50 P2 mediu que a cauda não-resolvida é baixa-criticidade (acidente/ergonômico) → revisão, não erro silencioso. Assimetria com o lado-FDS (lá bloqueia: químico sem materialidade é inaferível, alta-criticidade) intencional e documentada, molde D-ARQ-29. Sem pendência nova na Fase A: o `None` vem pareado com a pendência que o resolver emitiu na hidratação (invariante de 1b) — evita o duplo de DT-003Y-01. **Materializado em 1a: o guard.**

4. **Recorte identidade-primeiro; parse de quantificação diferido.** A 1ª leva de hidratação (1b) preenche id + nome + cargos + agente-slug; `RiscoPGR.quantificacao=None`. O parse do texto cru (`"6,3 ppm"→Quantificacao`) é resolver-side determinístico (molde `parsear_faixa`/`_normalizar_faixa` do lado-FDS), natureza distinta de identidade → fatia 2. Anti-perda: o texto cru sobrevive no `GHEVerbatim` de entrada (preservado a montante). Diferidos já nomeados (D-ARQ-49 P2): EPIs, psicossocial, gates de topo (`validade`/`assinatura`) → `GHEPGR` com defaults; envelope PGR-topo é fatia irmã. `[INTERPRETADO — recorte, ratificado 003.BQ]`.

**Consequência.**
- Dá consumidor de produção ao resolver `termo→slug` (órfão desde 003.BP).
- Motor puro (D-ARQ-09): a hidratação é determinística; LLM parou no verbatim.
- Universal (D-ARQ-06): id posicional + termo→slug + defaults servem qualquer setor; as formas químicas de DT-003L-01 vivem abaixo, no ramo quantificação/FDS.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v41 inalterado). Cria contrato de camada.

**Fronteiras (não confundir):**
- **D-ARQ-49/50** — consome (a "PGR transcrita" e o resolver); não revoga.
- **D-ARQ-14** — reusado (`vocabulario_ausente` não-bloqueante).
- **D-ARQ-31 / D-ARQ-35 P3** — anti-supressão: risco não-resolvido preservado, não descartado.
- **D-ARQ-29** — molde da assimetria bloqueante-vs-não-bloqueante entre lados.
- **D-ARQ-08** — a política None-agente é a escolha bloqueante-vs-operacional.
- **Componente.agente (lado-FDS)** — espelho estrutural do `RiscoPGR.agente` Optional.

**Base.** Sessão 003.BQ (07/07/2026). Gate de estado real (git objects): `RiscoPGR.agente` só lido por `stage_2_riscos` Fase A; `RiscoPGR.tipo`/`severidade` zero consumidores no motor (só fixture); `RiscoPGR` construído só em fixtures. Duas passadas: (1ª) recorte identidade-primeiro + virada Optional; (2ª, pós-gate) o gate revelou o acoplamento tipo→Fase A (mypy) → split 1a/1b, e a política None-agente (D-ARQ-08) resolvida não-bloqueante por D-ARQ-14 + D-ARQ-50 P2.

**Aplicação 003.BQ fatia 1a (07/07/2026) — contrato de tipo, isolado.** `RiscoPGR.agente: str→Optional[str]` (`tipos.py`) + guard `if risco_pgr.agente is None: continue` na Fase A de `stage_2_riscos` (`riscos.py`) — materializa os seams 2 (virada de tipo) e 3 (guard não-bloqueante, `continue`-sem-duplo). Seams 1 (id) e 4 (recorte) são 1b. Blast radius confirmado repo-inteiro: só `tipos.py` + `riscos.py` (`RiscoPGR` construído só em fixtures; `predicados.py`/`transcritor_pgr.py` leem `Risco`/`RiscoVerbatim`, não `RiscoPGR`). Guard defensivo (a hidratação que produz `None` é 1b) exercitado por teste sintético (falha sem o guard, provado por stash-removal: `Risco(agente=None)` construído → `assert 2==1`). Suíte 597→598, 4 skipped; mypy --strict delta-zero (`tipos.py` + `riscos.py`). Commit `b38a76a`, merge `e87759f` (PR #156, "Create a merge commit"). `[DERIVADO — IMPL 003.BQ 1a host; gate de estado real em disco]`.

**Aplicação 003.BQ fatia 1b (07/07/2026) — `hidratar_ghe`, seams 1 e 4.** `motor/hidratacao.py` greenfield flat: `hidratar_ghe(ghe, indice, posicao) -> tuple[GHEPGR, list[Pendencia]]` — a posição entrou na assinatura porque o seam 1 exige ordem e o GHE isolado não a conhece. Id posicional `GHE-{posicao:02d}` 1-based (handle do bloco, não id canônico). Tri-estado: EXATA→slug; FUZZY→slug + `Pendencia(tipo="resolucao_fuzzy", destinatario="extracao")` não-bloqueante fabricada NA HIDRATAÇÃO (o resolver retorna `pendencia=None` no FUZZY por design — o "consumidor futuro" do seu docstring é esta camada; nomes `[INTERPRETADO — ratificados 003.BQ]`); NAO_RESOLVIDO→`agente=None` + a pendência do resolver com `ghe_id` injetado via `replace`. Revisão do Arquiteto sobre objects corrigiu 1 desvio material: `if pendencia is not None`→`assert` (erro-zero D-ARQ-22 — `None` órfão viola o seam 3 e deve estourar, não degradar). `RiscoPGR.tipo=""` (convenção-verbatim de ausência; zero consumidores, gate 1a), `severidade=None`, `quantificacao=None` (seam 4 — parse é fatia 2). `fonte_geradora` não migra (anti-perda: GHEVerbatim preservado a montante). Isolado — nada plugado em `executar()`/`entrada.py`. 6 testes (tri-estado, id determinístico, pareamento None↔pendência, gabarito de forma moldado em Est-01 do Viverde — D-ARQ-50 C1, forma não contagem). Suíte 598→604, 4 skipped; mypy --strict delta-zero. Commits `b039f0d`+`682d106`, merge `663f9f1` (PR #158, 2 pais verificados sobre objects). `[DERIVADO — IMPL 003.BQ 1b host; revisão do Arquiteto sobre git objects]`.

**Aplicação 003.BR (07/07/2026) — costura plural, fatia irmã.** `hidratar_pgr(ghes: Sequence[GHEVerbatim], indice, validade, assinatura_engenheiro) -> tuple[PGR, list[Pendencia]]` em `hidratacao.py` — consumidor de produção de `hidratar_ghe` (que estava isolado desde 1b): itera com posição 1-based (seam 1 — a posição vem do chamador, como desenhado), agrega pendências na ordem dos blocos, monta `PGR`. Envelope (`validade`/`assinatura_engenheiro`) por parâmetro obrigatório sem default — a FONTE é a transcrição de topo do documento, fatia futura; parâmetro não inventa dado (D-ARQ-22), desloca a procedência ao chamador. Alternativa rejeitada: retornar `tuple[GHEPGR, ...]` sem montar PGR (não fecha a travessia). Índice recebido, não construído dentro (fachada esconde mecânica de índice, D-ARQ-40; camada não). Destrava o primeiro e2e verbatim→Resultado em teste: Est-01 Viverde moldado (D-ARQ-50 C1) → `hidratar_pgr` → `processar_pgr`, asserção de travessia de identidade (`matrizes[0].ghe_id == "GHE-01"`). Revisão do Arquiteto sobre objects corrigiu 2 desvios: (i) MATERIAL — asserção tautológica de status no e2e (`status in` Literal dos 3 valores — teste que não pode falhar não é gate) → travessia de identidade; (ii) MENOR — `typing.Sequence` deprecated → `collections.abc`. `entrada.py`/`executar()` intocados — plug de produção (cliente LLM real + fonte do envelope) é fatia seguinte. 5 testes; suíte 604→609, 4 skipped; mypy --strict delta-zero. Commits `110b2c8`+`3039af4`, merge PR #160 (`e064778`, "Create a merge commit"). `[DERIVADO — IMPL 003.BR host; revisão do Arquiteto sobre git objects]`.

**Aplicação 003.BZ (fatia 2) — parse de quantificação.** `parsear_quantificacao(texto: str) -> Optional[Quantificacao]` em `motor/quantificacao.py` novo — módulo próprio (não em `hidratacao.py`), molde `parsear_faixa`/`_texto_para_float` de `transcricao_fds.py` replicado LOCALMENTE (não importado — camadas distintas: faixa de FDS é concentração de componente, quantificação de GHE é medição ambiental). Só o medido no Viverde (`docs/MAPA_GHE_VIVERDE.md`): unidade ∈ {`dB(A)`, `mg/m³`/`mg/m3`, `ppm`}, número BR vírgula→ponto; `mg/m³`/`mg/m3` normalizam para `mg/m3` (convenção fixture/predicados), `dB(A)`/`ppm` literais; vazio/whitespace, número ilegível ou unidade fora do conjunto → `None`. Saída parseável sempre com `relacao_LT=None`/`pct_LT=None`/`apenas_qualitativa=False` — o parser NÃO distingue ausente de ininteligível, quem distingue é o chamador. `hidratar_ghe` (`motor/hidratacao.py`) passa a parsear 1× por risco, ANTES do tri-estado (independe da resolução do agente), nos 3 ramos EXATA/FUZZY/NAO_RESOLVIDO. Anti-supressão D-ARQ-31/35: texto cru não-vazio que falha o parse gera `Pendencia(tipo="quantificacao_nao_parseada", bloqueante=False)` — medição transcrita nunca some em silêncio, o risco entra mesmo assim com `quantificacao=None`. Recorte remanescente EXPLÍCITO (não paliativo): `relacao_LT` permanece sempre `None` — classificação dB→relação (a exemplo de NR-15/NR-09) é regra clínica não formalizada, exige `R-*` nova em fatia futura própria. 7 decisões IMPL ratificadas (as 6 da sessão + 1 na revisão do Arquiteto: aceitação case-insensitive de grafia de unidade — desvio MENOR aceito, sem âncora contrária no Viverde). Commits `4f1866d`+`3a4baf5`, merge PR #174 (`79e9499`). Suíte 658→671, mypy --strict delta-zero. `[DERIVADO — IMPL 003.BZ host; revisão do Arquiteto]`.

**Aplicação 003.CB (CONHECIMENTO) — R-RUIDO-01 destrava a fatia 3.** O recorte remanescente da 003.BZ (`relacao_LT` sempre `None`, classificação dB→relação não formalizada) tinha um bloqueador clínico, não de engenharia: faltava a `R-*` que define os limiares. Formalizada em **R-RUIDO-01** (PROTOCOLO v43): NEN <80 `abaixo_acao`, 80–85 `entre_acao_LT`, ≥85 `acima_LT`. Limiares `[DERIVADO]` (85 = LT NR-15 Anexo 1; 80 = nível de ação NR-09 c/c NLI NHO-01, conferidos via web — D-ARQ-27). A fatia 3 (código: `hidratar_ghe`/classificador preenchendo `relacao_LT` a partir do `valor` dB(A) parseado em 003.BZ) fica **desbloqueada para IMPLEMENTAÇÃO** — cobertura de teste por faixa exigida (R-RUIDO-01). Ressalva herdada à IMPL: **DT-003CB-01** (o `valor` não discrimina NEN vs. SPL/pico — irmã de DT-002V-01; a borda 80/85 fica `[INTERPRETADO]` quanto à estatística de entrada, `[DERIVADO]` quanto ao limiar). Sem código nesta sessão. `[DERIVADO — R-RUIDO-01; NR-15 Anexo 1; NR-09/NHO-01 via web; D-ARQ-27]`.

**Aplicação 003.CC (fatia 3) — classificador R-RUIDO-01.** `classificar_ruido(q: Quantificacao) -> Quantificacao` em `motor/classificacao_ruido.py` novo — módulo próprio (regra clínica não mora no parser sintático de 003.BZ: o parse é agnóstico de agente, a classificação exige o slug pós-resolução). Pré-condições: `valor` não-None, `unidade == "dB(A)"`, não-qualitativa, `relacao_LT is None` (idempotente — nunca sobrescreve); fora disso retorna `q` inalterada, via `dataclasses.replace` (frozen). Partição R-RUIDO-01: <80 `abaixo_acao`, 80≤v<85 `entre_acao_LT`, ≥85 `acima_LT`; `acima_acao` NUNCA emitido (sinônimo-legado só aceito pelo predicado — testado explicitamente). `hidratar_ghe` aplica pós-resolução quando slug=="ruido" (EXATA ou FUZZY — FUZZY classifica por coerência com o desenho: entra com slug + pendência não-bloqueante; agente=None não classifica, NAO_RESOLVIDO excluído naturalmente pelo slug None). `_ruido_acima_acao` e R-AUD-* intocados (consumidor inalterado, como exigia R-RUIDO-01). DT-003CB-01 documentada no docstring (valor assumido NEN; SPL/pico indiscriminável no tipo — segue ABERTA). 15 testes novos: 11 unitários (faixas + bordas 80/85/84.9 + não-classificação + idempotência + nunca-acima_acao) e 4 de integração (âncoras Viverde 78,8→`abaixo_acao`, 89,6→`acima_LT`; não-ruído com dB(A) não classifica; ruído sem quantificação preserva caminho Ausente). Recorte remanescente da fatia 2 FECHADO. Commit `9500c2a`, PR #179, merge `975ae85`. Suíte 678→693, mypy --strict delta-zero. `[DERIVADO — IMPL 003.CC host; revisão do Arquiteto sobre git objects]`.

## D-ARQ-52 — Plug de produção lado-PGR: costura arquivo→Resultado; envelope RT-supplied; atravessa a hidratação (assimetria não-bloqueante vs. FDS)

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003.BS). Consumidor de produção da cadeia de extração-PGR (D-ARQ-49/50/51), que estava fechada mas isolada de produção até 003.BR. Autorização para virar D-ARQ do Diovanni (003.BS).

**Contexto.** 003.BR deixou `hidratar_pgr` em main sem chamador de produção (`entrada.py`/`executar()` intocados). Toda a cadeia existia isolada: `extrair_texto_pgr` (D-ARQ-50 P1) → `recortar_blocos_ghe` → `transcrever_ghes`/`gate_forma_ghe` + `TranscritorGeminiGHE` (validado ao vivo, 003.BO) → `construir_indice_termos` → `hidratar_pgr` → `processar_pgr`. Faltava a costura de I/O que atravessa arquivo→Resultado — o mesmo risco de código-órfão recorrente do projeto (resolver 003.BP→BQ, `hidratar_ghe`→BR). O molde é o lado-FDS `adaptadores/orquestracao_fds.py::preparar_composicao` (D-ARQ-47 cl.1-3).

**Decisão — três seams.**
1. **`preparar_ghes` (adaptador, I/O+LLM) para no verbatim, espelho de `preparar_composicao`.** `extrair_texto_pgr → recortar_blocos_ghe → transcrever_ghes → gate_forma_ghe`. Duas `Pendencia` bloqueantes distintas, nenhuma vira `()` silencioso (anti-supressão D-ARQ-31/35): `recortar_blocos_ghe → []` (zero âncoras) → `blocos_ausentes`; `TranscricaoIndisponivel` (chave ausente, cascata sem 200, JSON ininteligível) → `transcricao_indisponivel_pgr`. Ambas `regra_origem="D-ARQ-52"`.
2. **`processar_arquivo_pgr` (adaptador) ATRAVESSA verbatim→`hidratar_pgr`→`processar_pgr` sem gate-RT intermediário.** Difere do lado-FDS, onde `preparar_composicao` para antes de `montar_fds` para a admissão-RT preceder a resolução química (bloqueante-alta-criticidade). No PGR, a resolução termo→slug da hidratação é não-bloqueante por design (D-ARQ-50 P2 mediu a cauda como baixa-criticidade — acidente/ergonômico); a revisão-RT do PGR é pós-hoc, nas pendências FUZZY/`vocabulario_ausente` emitidas. É a assimetria medida D-ARQ-29, não violação do espelho. Parse total falho (aprovados vazio: blocos ausentes, transcrição indisponível ou todos reprovados no gate) → `(None, pendencias)`, não inventa PGR (D-ARQ-22). Aprovação PARCIAL → processa os aprovados e CARREGA as pendências bloqueantes dos reprovados na lista final.
3. **Envelope (`validade`/`assinatura_engenheiro`) por-parâmetro, RT-supplied.** Reusa o seam desenhado em `hidratar_pgr` (003.BR, parâmetro sem default). Gate eliminatório (R-PGR-01/R-PGR-06) é alta-criticidade — confiar extração-LLM não-revisada num gate que rejeita o PGR inteiro é mais arriscado que a cauda termo→slug; RT confirmando é o conservador. **Paliativo sinalizado:** envelope RT-supplied ≠ document-derived; a FONTE real é a transcrição-de-topo (D-ARQ-49 P2), fatia irmã. `entrada.py`/`processar_pgr` intocados. **Paliativo FECHADO no nível do adaptador (003.BY, D-ARQ-53 fatia 4):** origem de `validade`/`assinatura_engenheiro` agora é document-derived + confirmação-RT (`preparar_envelope` + `desserializar_confirmacao` → `EnvelopeConfirmado`).

**Consequência.**
- Dá chamador de produção à cadeia extração-PGR (órfã desde 003.BR); primeiro e2e REAL arquivo→Resultado (só o LLM mockado; PDF Viverde real).
- Motor puro (D-ARQ-09/48): a impureza (I/O+LLM) fica no adaptador; motor intocado. Adaptador→motor é legal; a fronteira D-ARQ-48 só veda o inverso.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v41 inalterado). Cria contrato de camada de costura.

**Fora de escopo (sinalizado).** Zeramento de linha por bloqueio de GHE (D-ARQ-31 fatia 2, `MatrizGHE.status` inerte aqui). Camada de edição-RT do verbatim-PGR (análogo `revisao_verbatim.py`/003.BI — sem ela, erro de transcrição só aflora no output-review de slug). Âncora de recorte segue Viverde-pontual (NOTA 003.BM).

**Universalidade.** Fecha a TRAVESSIA VIVERDE, não a universal. Para universalidade real faltam, depois deste plug: (a) transcrição-de-topo do envelope; (b) generalização multi-PGR da âncora de recorte (medição sobre a amostra DT-003L-01).

**Fronteiras (não confundir).**
- **D-ARQ-49/50/51** — consome (cadeia + resolver + hidratação); não revoga.
- **D-ARQ-47 / orquestracao_fds.py** — molde da costura; a assimetria "atravessa vs. para no verbatim" é deliberada (seam 2).
- **D-ARQ-29 / D-ARQ-50 P2** — a assimetria bloqueante-vs-não-bloqueante entre lados.
- **D-ARQ-48** — preservada; o adaptador é o lado impuro, o motor segue puro/testável.

**Base.** Sessão 003.BS (07/07/2026). Gate de estado real (git objects sobre 73a66c7): cadeia isolada, `entrada.py` recebendo PGR pronto. Duas passadas: (1ª) recorte de 3 seams + envelope RT-supplied; (2ª, revisão do Arquiteto sobre objects do commit) e2e com travessia de identidade (não asserção de status tautológica, lição 003.BR) + envelope provado atravessando R-PGR-06. APROVADO sem correção.

**Aplicação 003.BS (07/07/2026).** `adaptadores/orquestracao_pgr.py` greenfield: `preparar_ghes` + `processar_arquivo_pgr`, molde `orquestracao_fds.py`. 5 testes (`test_orquestracao_pgr.py`): e2e PDF Viverde real + mock → `Resultado` com travessia `matrizes[0].ghe_id=="GHE-01"`; `blocos_ausentes`→(None,bloqueante); `transcricao_indisponivel_pgr`→(None,bloqueante); aprovação parcial (`forma_verbatim_pgr` carregada + `Resultado` não-nulo); envelope `validade`/`hoje` atravessando até R-PGR-06→REJEITADO. Suíte 609→614, 4 skipped; mypy --strict delta-zero (motor+adaptadores). `entrada.py` intocado. Commit `f4405a3`, merge `980fb9d` (PR #162, "Create a merge commit"). Nenhuma R-* criada/alterada. `[DERIVADO — IMPL 003.BS host; revisão do Arquiteto sobre git objects]`.

## D-ARQ-53 — Transcrição-de-topo do envelope: instância-envelope de D-ARQ-41; pré-preenchimento document-derived + confirmação-RT no gate eliminatório (molde revisão-RT D-ARQ-47 cl.4); mecanismo adiado por medição

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Fecha o paliativo "envelope RT-supplied" que D-ARQ-52 seam 3 declarou (fonte real = transcrição-de-topo). Implementação por fatias futuras; a medição do topo do documento é sessão CONHECIMENTO própria. Autorização para virar D-ARQ do Diovanni (003.BT).

**Contexto.** D-ARQ-52 seam 3 fechou a costura arquivo→Resultado do lado-PGR com o envelope (`PGR.validade`/`PGR.assinatura_engenheiro`) **RT-supplied por parâmetro**, e nomeou-o paliativo: "envelope RT-supplied ≠ document-derived; a FONTE real é a transcrição-de-topo (D-ARQ-49 P2)". Com o plug em produção (`processar_arquivo_pgr`, main), todo uso real força o RT a digitar dado que já está no documento — custo recorrente. Esta decisão dá forma à transcrição-de-topo: é a **instância-envelope de D-ARQ-41** (irmã de D-ARQ-42 lado-FDS e D-ARQ-49 lado-esqueleto), a terceira fronteira transcrita da porta de entrada.

**Gate de estado real (disco, 003.BT).**
- Envelope é `PGR.validade: date` + `PGR.assinatura_engenheiro: bool` (`tipos.py` linhas 154-155), consumido só por `estagios/gates.py` (R-PGR-01: `not assinatura_engenheiro` → bloqueante; R-PGR-06: `(hoje - validade) >= 730d` → bloqueante). `[DERIVADO — tipos.py / estagios/gates.py em disco]`.
- O topo do documento é DESCARTADO hoje: `recortar_blocos_ghe` (`extracao_pgr.py`) começa na 1ª âncora `SETOR/FUNÇÃO` (pág. 33 no Viverde) — "conteúdo do documento ANTES da 1ª âncora é descartado". Emissão e responsável técnico vivem nesse topo descartado. `[DERIVADO — extracao_pgr.py em disco]`.
- Envelope RT-supplied por parâmetro sem default em `processar_arquivo_pgr`/`hidratar_pgr` (`validade`/`assinatura_engenheiro`) — seam pronto para receber a fonte document-derived. `[DERIVADO — orquestracao_pgr.py / hidratacao.py em disco]`.

**Decisão — quatro partes (espelham D-ARQ-49).**

*Parte 1 — bicamada interna, instância-envelope de D-ARQ-41.* Parse-doc determinístico (recorte-de-topo, greenfield) → transcrição-LLM (topo → `EnvelopeVerbatim`). Reusa `extrair_texto_pgr` (páginas já materializadas, D-ARQ-50 P1); o recorte-de-topo é o inverso de `recortar_blocos_ghe` — pega a região do início do documento até a 1ª âncora GHE (o que o recorte de blocos joga fora). Isolado, sem consumidor na 1ª fatia (molde 003.J/003.S/003.BM). Fronteira interna = texto-do-topo; a transcrição-LLM recebe texto, não bytes (D-ARQ-09). `[DERIVADO — D-ARQ-41 P1; D-ARQ-09; extracao_pgr.py]`.

*Parte 2 — o insight que distingue esta instância das outras duas: pré-preenchimento + confirmação-RT, NÃO document-derived autônomo, porque o consumidor é gate ELIMINATÓRIO.* R-PGR-01/R-PGR-06 rejeitam o PGR inteiro. Um `date`/`bool` **confiante-e-errado** da LLM atravessa em silêncio e ou rejeita PGR válido ou aceita PGR vencido — classe D-ARQ-22, em alta criticidade. A assimetria não-bloqueante D-ARQ-29/D-ARQ-50 P2 (cauda termo→slug de baixa criticidade → revisão pós-hoc) **NÃO** cobre o envelope: aqui não é cauda, é o gate de admissão — a mesma razão que levou D-ARQ-52 seam 3 a escolher RT-supplied. Resolução: a transcrição-de-topo **pré-preenche** os dois campos e o **RT confirma/edita** antes do gate, molde da revisão-RT da FDS (D-ARQ-47 cl.4, `revisao_verbatim.py`, 003.BI). O paliativo removido é o **custo recorrente** de o RT garimpar o documento — não a confirmação humana no gate, que permanece conservadora (confirmação barata de pré-preenchimento vs. digitação do zero). `[INTERPRETADO — o insight novo; sem âncora normativa; espelha D-ARQ-47 cl.4 e a postura conservadora de D-ARQ-52 seam 3]`.

*Parte 3 — a SEMÂNTICA do `EnvelopeVerbatim` é cravada; a FORMA concreta, NÃO.* Semântica (espelha D-ARQ-49 P3): campos de TEXTO CRU (ex.: `validade_texto`, `responsavel_tecnico`, `registro_profissional`), sem `date`, sem `bool`, sem juízo de "engenheiro vs. técnico". A fronteira LLM↔determinístico (D-ARQ-09): a LLM transcreve o texto do topo; o resolvedor determinístico converte `validade_texto → date` (formatos BR) e monta a EVIDÊNCIA de credencial para o RT — o `bool` de R-PGR-01 e a `date` de R-PGR-06 saem da **confirmação-RT**, com a transcrição+resolvedor como default. `gate_forma_topo` + `Pendencia` bloqueante para topo mal-formado (molde `gate_forma_ghe`, D-ARQ-47 cl.3). A forma concreta do tipo (frozen dataclass própria vs. campos no verbatim existente) é IMPL, condicionada ao disco — cravá-la aqui seria literal sem fonte (D-ARQ-22). `[INTERPRETADO — espelha D-ARQ-49 P3 / D-ARQ-41 P2]`.

*Parte 4 — princípio do gabarito + mecanismo adiado por medição.* Gabarito: topo do `PGR VIVERDE V02` (par em disco) ↔ campos verificáveis (data de emissão, responsável técnico), LLM fixado/mockado, nunca testa API. **ADIADO POR MEDIÇÃO** (molde D-ARQ-49 P4 → D-ARQ-50): o topo do documento **nunca foi medido** (o recorte o descarta). A medir na sessão CONHECIMENTO própria: localização de emissão/assinatura no topo (âncora normativa vs. posição); formatos de data BR reais; que evidência distingue "engenheiro de segurança" de "técnico" (R-PGR-01) e se é resolvível ou fica 100% na confirmação-RT; prompt; se a fronteira-OCR (D-ARQ-42) recorre no topo. Adiamento por dado ausente, não indecisão. `[DERIVADO — molde D-ARQ-49 P4 / D-ARQ-50; DT-003L-01]`.

**Consequência.**
- Fecha padrão-instância + recorte + gabarito + fronteira + o insight pré-preenchimento/confirmação-RT do envelope sem implementar; o paliativo D-ARQ-52 seam 3 ganha caminho de saída declarado.
- Determinismo do motor intacto (D-ARQ-09): a LLM (transcrição-de-topo) fica a montante do `EnvelopeVerbatim`; resolvedor e motor seguem puros.
- **Universalidade (gate CLAUDE.md):** validade + assinatura de engenheiro responsável são exigência de NR-01 para QUALQUER PGR (construção civil, química, saúde) — não é Viverde. O que varia (posição/formato no topo) é o adiado por medição, não o cravado.
- **Paliativo remanescente sinalizado:** o recorte-de-topo herda a âncora `SETOR/FUNÇÃO` (n=1 Viverde) como fronteira-fim da região; generalização multi-PGR da âncora é o requisito (b) da 003.BS, sessão à parte.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v41 inalterado). Cria contrato da terceira fronteira transcrita.

**Fatiamento previsto (IMPL futura, ordem):** (1) recorte-de-topo determinístico, isolado, gabarito topo-Viverde; (2) `EnvelopeVerbatim` + contrato `TranscritorTopo` (Protocol) + `gate_forma_topo`, LLM mockado; (3) resolvedor `validade_texto→date` + evidência-de-credencial + seam de confirmação-RT (molde `revisao_verbatim.py`); (4) plug em `processar_arquivo_pgr` — troca a *origem* de `validade`/`assinatura_engenheiro` de "RT do zero" para "document-derived pré-preenchido + RT confirma". `entrada.py`/`processar_pgr` intocados. A medição (formatos/localização) precede a fatia 2.

**Fronteiras (não confundir):**
- **D-ARQ-52 seam 3** — esta decisão é o caminho de saída do paliativo que aquele seam declarou; a costura arquivo→Resultado é intocada, muda a *origem* do envelope.
- **D-ARQ-49** — irmã do lado-esqueleto: mesmo corte (contrato+recorte+gabarito antes; mecanismo por medição depois). O recorte-de-topo é complementar ao `recortar_blocos_ghe` (pega o topo que ele descarta), não o reconstrói.
- **D-ARQ-47 cl.4** — molde do pré-preenchimento+confirmação-RT (`revisao_verbatim.py`); o envelope é revisão-RT mais simples (dois campos vs. composição).
- **D-ARQ-41** — instância-envelope concreta do padrão bicamada; `EnvelopeVerbatim` é a terceira fronteira transcrita (após "CAS transcrito" e "PGR transcrita").
- **D-ARQ-09** — preservada: a transcrição-de-topo é onde o LLM para e o determinístico (resolvedor + confirmação-RT + gates) começa.
- **DT-003L-01** — input de medição (o topo dos PGRs da amostra multi-setor, ainda não medido); não resolvida aqui.

**Nota de aplicação (003.BW — fatia 2).** `EnvelopeVerbatim` frozen em `tipos.py` (validade_textos PLURAL — candidatas cruas na ordem do documento, política "mais recente" é resolvedor-side, fatia 3; SEM campo de assinatura — bool de R-PGR-01 é 100% confirmação-RT, P2; bloco implementação excluído por consumo-zero, reversível); `TranscritorTopo` (Protocol) + `transcrever_topo` + `gate_forma_topo` em `transcritor_topo.py` novo (molde gate_forma_ghe; reprova candidata vazia/envelope integralmente vazio com strip() em tudo). LLM mockado, gabarito 003.BV. Achado: typo de origem "TÉNICA" na camada de texto do topo Viverde (correção factual a 003.BV) — âncora da fatia 3 sem match exato de título. Commits 3cdef6f+16f2c6b, PR #168, merge 321c6da. Suíte 619→626, mypy delta-zero. Fatias restantes: 3 (resolvedor+confirmação-RT) e 4 (plug).

**Nota de aplicação (003.BX — fatia 3).** `CandidataValidade` + `EnvelopeConfirmado` frozen em `tipos.py`; `resolvedor_topo.py` novo (mês-ano PT-BR, SÓ o medido — `dd/mm/aaaa` excluído por consumo-zero; 1º dia do mês [INTERPRETADO], DT-003BV-01; max() = mais recente; ambiguidade/não-parseável/ano fora do range → None, nunca crash nem bloqueio) + `revisao_envelope.py` novo (molde `revisao_verbatim.py`: artefato JSON v1, schema estrito em todos os níveis; credencial crua sem heurística de token; `assinatura_engenheiro` sem default). 7 decisões IMPL ratificadas. Commits 0f2c52c+1e51cd4 (fix ValueError formulado na revisão via git objects), PR #170, merge cc87e88. Suíte 626→652, mypy delta-zero. Fatia restante: 4 (plug em `processar_arquivo_pgr`).

**Nota de aplicação (003.BY — fatia 4, DECISÃO COMPLETA 4/4).** Plug materializado: `preparar_envelope` em `orquestracao_pgr.py` (ida completa até o artefato JSON, parando antes da confirmação-RT — seam humano fora do adaptador, molde `orquestracao_fds`; pendências `topo_ausente`/`transcricao_indisponivel_topo`/repasse `forma_verbatim_topo`); `processar_arquivo_pgr` agora recebe `envelope: EnvelopeConfirmado` (origem document-derived + confirmação-RT via `desserializar_confirmacao`), fechando o paliativo D-ARQ-52 seam 3 no nível do adaptador. Extração 2× estrutural (seam humano entre invocações). 6 decisões IMPL ratificadas. Commits `7549fd4`+`5ab8c8d`, PR #172, merge `a081a3f`. Suíte 652→658, mypy delta-zero. Remanescente explícito (não paliativo): cliente-LLM real do topo + superfície RT (UI/CLI), sessão própria.

**Nota de aplicação (003.CA — cliente-LLM real do topo).** `TranscritorGeminiTopo` em `adaptadores/transcritor_gemini_topo.py` (molde `transcritor_gemini_pgr.py`; reuso intra-pacote da cascata Gemini do adaptador FDS; prompt verbatim com candidatas cruas na ordem, tolerância ao typo de âncora "TÉNICA", credencial crua sem assumir CREA, sem juízo de credencial nem assinatura; parse leniente — reprovação de vazio é de `gate_forma_topo`, ponto único). Sonda ao vivo 4/4 campos no gabarito 003.BV (PDF Viverde + API real; script descartável não commitado). 1 desvio MENOR aceito na revisão. Commits `3fe3b3d`+`30fdd8b`, PR #176, merge `49a30ec`. Suíte 671→678, mypy delta-zero. Remanescente de D-ARQ-53: superfície RT (UI/CLI). Prompt calibrado em n=1 (requisito (b) 003.BS aberto).

**Base.** Sessão 003.BT (08/07/2026). Instância-envelope de D-ARQ-41; irmã de D-ARQ-49; caminho de saída do paliativo D-ARQ-52 seam 3. Gate de estado real (disco): envelope `date`/`bool` em `tipos.py`, gates em `estagios/gates.py`, topo descartado por `recortar_blocos_ghe`, seam RT-supplied pronto em `orquestracao_pgr.py`/`hidratacao.py`. Duas passadas: (1ª) nova bicamada document-derived autônoma substituindo os parâmetros RT; (2ª, crítica) document-derived autônomo num gate ELIMINATÓRIO reintroduz o risco que D-ARQ-52 seam 3 evitou — confiante-e-errado passa em silêncio → corrigido para pré-preenchimento + confirmação-RT (molde D-ARQ-47 cl.4), removendo o custo recorrente sem abrir mão da postura conservadora no gate. Decisão de arquitetura — sem código.

## D-ARQ-54 — Superfície RT como apresentação-pura sobre o contrato ida/volta; CLI primeiro, web herda o mesmo artefato; escopo = os dois seams de confirmação (envelope + FDS)

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Fecha o último remanescente nomeado de D-ARQ-53 ("superfície RT (UI/CLI)") e o ponto humano de D-ARQ-47 cl.4 lado-FDS. Implementação por fatias futuras. Autorização para virar D-ARQ do Diovanni (003.CD).

**Contexto.** Os dois pontos humanos da porta de entrada existem hoje **só como par serializar/desserializar JSON**, sem nenhuma superfície que um responsável técnico use:
- Envelope (D-ARQ-53 P3): `serializar_envelope` (ida) → RT → `desserializar_confirmacao → EnvelopeConfirmado` (volta). `motor/revisao_envelope.py`.
- FDS (D-ARQ-47 cl.4): `serializar_verbatim` (ida) → RT → `desserializar_verbatim` + `montar_fds_revisado` (volta). `motor/revisao_verbatim.py`.

`preparar_envelope`/`orquestracao_fds` montam a ida e **param antes da confirmação** ("seam humano fora do adaptador"). Falta a superfície que renderize ida → humano → volta. Sem ela, todo uso real do pipeline trava no seam.

**Gate de estado real (disco, 003.CD).**
- `revisao_envelope.py`: `serializar_envelope(candidatas,...) -> str` + `desserializar_confirmacao(texto) -> EnvelopeConfirmado`, schema estrito, `EnvelopeRevisadoInvalido` para adulteração. `[DERIVADO — git show HEAD]`
- `revisao_verbatim.py`: `serializar_verbatim(blocos) -> str` + `desserializar_verbatim(texto) -> tuple[BlocoVerbatim,...]` com garantia `desserializar(serializar(x)) == x` + `montar_fds_revisado`, `VerbatimInvalido`. `[DERIVADO — git show HEAD]`
- Nenhum consumidor humano dos dois artefatos existe. `[DERIVADO — git grep]`

**Decisão — quatro partes.**

*Parte 1 — apresentação-pura, lógica-de-domínio ZERO.* A superfície RT é **camada de apresentação sobre o contrato ida/volta já existente**: lê o artefato-ida (JSON), renderiza ao humano, coleta edição/confirmação, emite o artefato-volta (JSON) que `desserializar_*` consome. Não interpreta data, não julga credencial, não classifica composição — tudo isso já vive no resolvedor determinístico a montante. A superfície não pode introduzir juízo novo; se precisar, é sinal de que falta regra no resolvedor, não na UI. Preserva D-ARQ-09 (motor puro) e a invariante "seam humano fora do adaptador" de D-ARQ-52/53. `[INTERPRETADO — espelha D-ARQ-09 e a postura seam-humano-fora-do-adaptador]`

*Parte 2 — uma abstração para os dois seams.* Envelope e FDS são a mesma forma: "artefato-ida → edição → artefato-volta". A superfície expõe **um contrato de apresentação único** (renderizar artefato + coletar volta válido), instanciado duas vezes (envelope, FDS), não duas superfícies independentes. A diferença entre eles é só o schema do artefato — dado, não código de superfície. `[INTERPRETADO — generalização sobre os dois pares serializar/desserializar em disco]`

*Parte 3 — CLI primeiro; web herda o mesmo artefato.* A primeira fatia é **CLI**: menor superfície que fecha o loop fim-a-fim, testável deterministicamente (fixture stdin/stdout, sem mock de framework), zero dependência de lib; e o Streamlit é o motor legado "não tocar". Web (Streamlit ou outro) é fatia posterior sobre o **mesmo contrato de artefato** de P2 — CLI-first não fecha a porta do web, porque ambos são adaptadores da mesma apresentação. 2ª passada considerada e rejeitada: Streamlit-first acoplaria a superfície a um framework antes de o contrato de apresentação estar exercido por teste. `[INTERPRETADO — decisão de Diovanni, 003.CD]`

*Parte 4 — universalidade e o gabarito.* O contrato de apresentação vale para qualquer PGR/FDS de qualquer setor, porque opera sobre o artefato JSON (universal por construção), não sobre conteúdo Viverde. Gabarito da fatia CLI: artefato-ida do envelope Viverde (par em disco) → sessão CLI simulada (stdin de confirmação) → artefato-volta que `desserializar_confirmacao` aceita, `EnvelopeConfirmado` verificável. Idem FDS com `fds_t65`. LLM nunca entra (a superfície é a jusante do transcritor). `[DERIVADO — molde de gabarito D-ARQ-53 P4]`

**Consequência.**
- Fecha o remanescente "superfície RT (UI/CLI)" de D-ARQ-53 e o ponto de revisão-RT de D-ARQ-47 cl.4 com um contrato de apresentação único, sem implementar.
- Determinismo intacto (D-ARQ-09): a superfície é I/O humano nas bordas, resolvedor/motor seguem puros.
- **Universalidade (gate CLAUDE.md):** confirmação de validade/assinatura e revisão de composição de FDS são exigência para qualquer PGR/FDS — construção civil, química, saúde. A superfície opera sobre artefato, agnóstica de setor.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v44 inalterado). Cria o contrato da superfície RT.

**Fatiamento previsto (IMPL futura, ordem):** (1) CLI do envelope — renderiza candidatas + credencial-crua, coleta escolha de validade + `assinatura_engenheiro` (bool), emite artefato-volta; gabarito envelope-Viverde. (2) CLI da FDS — renderiza `BlocoVerbatim`, coleta edição, emite volta; gabarito `fds_t65`. (3) unificação num contrato de apresentação comum se as duas fatias confirmarem a forma compartilhada (não antes — anti-falsa-completude D-ARQ-22). (4) web (Streamlit ou outro) como adaptador irmão sobre o mesmo contrato — sessão própria.

**Fronteiras (não confundir):**
- **D-ARQ-53** — esta decisão é o remanescente "superfície RT (UI/CLI)" que aquela deixou aberto; consome o artefato-ida do envelope, não o reconstrói.
- **D-ARQ-47 cl.4** — o ponto de revisão-RT da FDS; esta superfície é a instância humana dele.
- **D-ARQ-52 seam 3** — a costura arquivo→Resultado é intocada; a superfície fica no seam humano, fora do adaptador.
- **D-ARQ-09** — preservada: a superfície é borda de I/O, não lógica.
- **Escopo:** render de saída (matriz tri-estado D-ARQ-31 + pendências) fica FORA — é apresentação-de-saída, D-ARQ próprio. Esta decisão é só confirmação-de-entrada.

**Base.** Sessão 003.CD (09/07/2026). Remanescente de D-ARQ-53. Gate de estado real (disco): pares serializar/desserializar em `revisao_envelope.py`/`revisao_verbatim.py`, sem consumidor humano. Duas passadas: (1ª) superfície por seam, cada uma sua; (2ª, crítica) os dois seams são a mesma forma "ida→edição→volta" → contrato de apresentação único, instanciado duas vezes; CLI-first porque exerce o contrato limpo antes de qualquer framework. Decisão de arquitetura — sem código.

**Aplicação (003.CE — fatia 1).** CLI do envelope materializada em
`superficie/cli_envelope.py` (pacote NOVO `agente_medico/superficie/` —
casa da camada de apresentação, distinto de `adaptadores/` que costura
LLM/arquivo). `revisar_envelope(artefato_ida, entrada, saida) -> str`:
renderiza credencial crua + candidatas + proposta, coleta validade (Enter
mantém proposta; validação SÓ de forma ISO) e assinatura_engenheiro (s/n
explícito, sem default — 003.BV), emite artefato-volta com self-check via
`desserializar_confirmacao` (reutiliza o validador, anti-erro-silencioso
D-ARQ-22). Lógica-de-domínio zero confirmada. Contrato de apresentação
abstrato NÃO criado (fatia 3, anti-falsa-completude D-ARQ-22). Achado de
revisão pré-merge: EOF em stdin virava loop infinito (readline() == ""
confundido com Enter); corrigido com EOFError, 2 testes. Gabarito
envelope-Viverde fim-a-fim (preparar_envelope → CLI → EnvelopeConfirmado).
Commits 62ca3e5 + 0a4f4fc, merge a0153a8, PR #182. Suíte 697→708
(704 passed + 4 skipped), mypy --strict delta-zero. Fatias 2–4 abertas.

**Aplicação (003.CF — fatia 2).** CLI da FDS materializada em
`superficie/cli_fds.py`. `revisar_verbatim(artefato_ida, entrada, saida) -> str`:
renderiza blocos/membros crus (byte-exato), coleta faixa com Enter-mantém e
revisão por membro com gate único `[Enter mantém / e edita / r remove]`
(drill-down cas/nome só no "e"; SEM "adicionar" — membro sem procedência de
transcrição, correção é re-transcrever a FDS); bloco com membros vazio aceito
(juízo do `gate_forma` a jusante); self-check via `desserializar_verbatim`
(`gate_forma` segue exclusivo de `montar_fds_revisado`, decisão selada);
`EOFError` antes do strip em todo prompt (lição 003.CE). `ArtefatoIdaIlegivel`
local — contrato abstrato segue NÃO criado (fatia 3, anti-falsa-completude
D-ARQ-22). Defeito pego em revisão pré-merge: gabarito com literais inventados
em vez de `fds_verbatim_t65` cru — corrigido (roundtrip byte-exato com `\n`
intra-token do TiO₂). Remanescente nomeado: adaptador FDS sem emissor do
artefato-ida em produção. Commits 45ca92b + 3b7f5ee, merge 7c272a8, PR #184.
Suíte 708→720 (716 passed + 4 skipped), mypy --strict delta-zero. Fatias 3–4
(unificação, web) abertas — a fatia 3 tem gatilho satisfeito (duas instâncias
confirmaram a forma).

**Aplicação (003.CG — fatia 3).** Contrato de apresentação materializado
em `superficie/apresentacao.py` (D-ARQ-54 P2): `ArtefatoIdaIlegivel`
única, `carregar_artefato_ida` (validação estrutural do artefato-ida),
`ler_resposta` (EOF→`EOFError` antes do strip), `prompt_enter_mantem`,
`conduzir_revisao` (carregar → revisar → serializar → self-check; o
`revisar` é callable por-seam porque na FDS a renderização é intercalada
com a coleta — fases separadas quebrariam o fluxo real) e `executar_main`
(esqueleto argparse). `cli_envelope.py`/`cli_fds.py` viram instâncias do
contrato; ficam por-seam os renders e os prompts de juízo próprio
(validade-ISO, s/n, gate [Enter/e/r]). Refactor comportamento-preservante:
os 23 testes das CLIs INTOCADOS como gate de regressão (byte-identidade de
mensagens, prompts e ordem de writes). Emissor do artefato-ida em produção
segue FORA (remanescente 003.CF — costura de produção ou fatia 4).
Commits dfdd4fa + fec0739, merge bb426a5, PR #186. Suíte 720→727
(723 passed + 4 skipped), mypy --strict delta-zero. Resta fatia 4 (web),
agora sobre o contrato unificado.

**Aplicação (003.CL — fatia 4, ÚLTIMA).** Web materializada como adaptador
irmão das CLIs em `superficie/web_envelope.py` + `superficie/web_fds.py`
(Streamlit — dependência já pinada; teste determinístico via
`streamlit.testing.v1.AppTest`, sem browser/servidor; motor legado intocado).
A metade TextIO do contrato (`conduzir_revisao`/`ler_resposta`/
`prompt_enter_mantem`) NÃO migra — é sequencial de terminal, Streamlit é
rerun-reativo; o web herda a metade ARTEFATO (`carregar_artefato_ida`,
`ArtefatoIdaIlegivel`, self-check via `desserializar_*`) + `emitir_volta`
extraído em `apresentacao.py` (o rabo dumps+self-check de `conduzir_revisao`
— anti-erro-silencioso D-ARQ-22 num ponto só). Núcleo puro por seam
(`montar_volta_envelope`/`montar_volta_verbatim`, sem import de streamlit,
pytest puro) + casca fina (`pagina_envelope`/`pagina_fds`, auto-contidas por
exigência de `AppTest.from_function` — re-executa só o texto da função).
Semânticas das CLIs preservadas: assinatura sem default (radio `index=None`,
003.BV), Enter-mantém vira default de input, radio de membro default
"mantém", SEM adicionar membro (procedência de transcrição), `gate_forma`
segue exclusivo de `montar_fds_revisado`. Achado de revisão pré-merge
(D-ARQ-22): `except ValueError` em `pagina_envelope` capturava
`EnvelopeRevisadoInvalido` (subclasse) do self-check rotulando falha interna
como "Data inválida" — corrigido (validação de forma em try próprio; núcleo
sem except, self-check propaga — postura de `pagina_fds`). Commits 0a257de +
9885879 + 367ea96 + f8819df (fixup), merge 7652b36, PR #194. Suíte 744→754
(754 passed + 4 skipped), mypy --strict delta-zero (46). **D-ARQ-54
COMPLETA — 4/4 fatias em main.** Remanescentes FORA do escopo desta D-ARQ:
emissor do artefato-ida FDS em produção (003.CF) e render de saída
(matriz/pendências — D-ARQ próprio).

## D-ARQ-55 — Recorte (B) da transcrição-FDS: verbatim-de-perigo é por-membro (H-code cru); mapa frase-H→flag é determinístico resolver-side (só sensibilização); confiança ancora em R-FDS-06 + revisão-RT

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação por fatias futuras. Ratificada pelo Diovanni (003.CI).

**Contexto.** D-ARQ-42 recortou a transcrição-FDS em (A) identidade+concentração e deixou as frases-H / classificação de perigo FORA por design. A 003.CH mediu por git que esse recorte (B) excluído é o pré-requisito duro do cluster DT-003M-01 + DT-003M-02(B) + DT-003T-01: em produção `Componente.is_carcinogeno_iarc`/`is_sensibilizante` são `False` por NÃO-extração, não por classificação (`[VERIFICADO — git grep, 003.CH]`). Enquanto "ausência de flag" significar "não extraímos", a reordenação do ramo-0 de `materialidade()` (honrar bypass antes do slug-check) passaria carcinógeno/sensibilizante real em silêncio (D-ARQ-22). Esta decisão escreve o CONTRATO do recorte (B) — como o perigo entra na cadeia de transcrição e vira flag — sem implementá-lo, e é explicitamente o **passo 1** da sequência ratificada em 003.CH (perigo-transcrição primeiro; reordenação do ramo-0 é o passo 2, sessão própria).

**Gate de estado real (código em disco nesta sessão).**
- Cadeia de transcrição-FDS FECHADA (003.BI): `extrair_texto_fds` → `TranscritorLLM.transcrever(texto) -> tuple[BlocoVerbatim,...]` (`transcritor_fds.py`) → serialização/revisão-RT (`revisao_verbatim.py`) → `gate_forma` → `montar_fds` → `resolver_composicao`/`gate_cas` (`composicao.py`/`resolvedor.py`) → `Componente` → Fase C (`estagios/riscos.py`) promove a `Risco`. `[DERIVADO — leitura em disco, 003.CI]`.
- `MembroVerbatim` (`tipos.py`): `cas: str`, `nome: str` — sem campo de perigo. `BlocoVerbatim`: `faixa: str` (1×/bloco, D-ARQ-46/003.AY), `membros`. `Componente`: `cas`, `nome`, `concentracao`, `agente`, `is_carcinogeno_iarc=False`, `is_sensibilizante=False`. `materialidade()` ramo 1 já lê `is_carcinogeno_iarc or is_sensibilizante` → MATERIAL (bypass); Fase C copia as flags pra frente ao promover. `[DERIVADO — tipos.py/materialidade.py/riscos.py em disco]`.
- Nenhum populador de flag de perigo fora de fixture (`[VERIFICADO — git grep, 003.CH, reconfirmado 003.CI]`).

**Decisão — quatro partes.**

*Parte 1 — verbatim-de-perigo é por-membro, H-code cru; mecanismo de localização adiado por medição.* `MembroVerbatim` ganha `frases_h: tuple[str, ...] = ()`; o transcritor-LLM transcreve os códigos H (GHS, ABNT NBR 14725) declarados para cada componente FIELMENTE — verbatim, como `cas`/`nome`, sem classificar. Granularidade por-MEMBRO (não por-bloco): a faixa é 1×/bloco (medido 003.AY), mas o perigo cola na linha-substância/CAS da seção 3 (estrutura GHS). `Componente` ganha `frases_h: tuple[str, ...] = ()` também — o cru sobrevive à montagem, espelhando `cas` (que permanece cru em `Componente` mesmo após `agente` resolvido). `()` = FDS declarou sem H-phrase para o membro — significado que só existe porque o transcritor agora OLHA (`[INTERPRETADO — prioridade na revisão de saída]`, ancorado em R-FDS-06, sem norma literal). A coluna europeia legada (Símbolo Xn/Xi/C + frases-R, patologia 6 de DT-003AS-01) fica FORA de escopo — notação distinta do GHS, registrada. **Adiado por medição** (molde D-ARQ-42/43): o MECANISMO de o LLM localizar/associar a frase-H por componente em layout variado — sobretudo o caso-rodapé (SI2 Tigre, H334/H317 fora da grade de composição) — fica para a IMPL, sobre os PDFs reais. Crava-se o contrato (por-membro), não o mecanismo. `[DERIVADO — estrutura GHS/seção 3 NBR 14725; DT-003AS-01 patologia 6; DT-003M-01]`.

*Parte 2 — mapa frase-H→flag é determinístico, resolver-side, só sensibilização no recorte B.* Uma função pura resolver-side (ao lado de `gate_cas` em `resolver_composicao`) lê `Componente.frases_h` e seta as flags: **{H334 (sensibilização respiratória), H317 (sensibilização dérmica)} → `is_sensibilizante=True`**. Reconhecido-e-mapeado → flag. H-code bem-formado fora do mapa (H350, H302…) → carregado cru em `frases_h`, sem flag, sem pendência (preservado para a revisão de saída — D-ARQ-22 satisfeito pela PRESERVAÇÃO do cru, não por chute). Token malformado (não casa a forma `H\d{3}`) → `Pendencia` não-bloqueante, destinatário RT (D-ARQ-33 cl.4). `is_carcinogeno_iarc` **permanece vocab/slug-sourced** (proveniência IARC, via `agentes.yaml`/gate-CAS) — NÃO é populado de H350/H351. Razão (a passada adversarial que forçou o recorte): **H350/H351 é carcinogenicidade GHS/CLP, não IARC** — popular `is_carcinogeno_iarc` a partir do H-code lavaria proveniência GHS como IARC, o erro-silencioso exato da classe D-ARQ-22. O carcinógeno-via-frase-H vira **DT nova** (DT-003CI-01, PROTOCOLO §11), deferida: futura flag `is_carcinogeno_ghs` apendada à lista de bypass (cl.5 D-ARQ-33, append-only). Os casos-âncora do cluster são todos sensibilização (SI2 H334/H317; DT-003T-01); o carcinógeno já tem caminho vivo (slug/IARC + R-PKG-BZ por identidade). Uma coisa por vez. `[DERIVADO — GHS H334/H317 = sensibilização; D-ARQ-33 cl.5; D-ARQ-22]`; o par código→flag é `[INTERPRETADO — prioridade na revisão de saída]` até a fonte GHS literal ser conferida.

*Parte 3 — confiança ancora em R-FDS-06 (confia no conteúdo) + revisão-RT (admite o candidato); o gate é de FORMA.* A frase-H declarada é autoritativa: R-FDS-06 (`[VALIDADO]`) fixa que confiar na FDS é o default, sem desconfiança sistemática por classe — logo a flag deriva do H-code declarado sem confirmação contra base externa de sensibilizante. O que se confia não é a classificação do LLM: é a frase-H da FDS, transcrita verbatim e ADMITIDA pelo RT (D-ARQ-47 cl.4). `frases_h` entra no schema de serialização do artefato ida/volta (`_CAMPOS_MEMBRO` de `revisao_verbatim.py` ganha `"frases_h"`; a superfície D-ARQ-54 renderiza o perigo por membro) — o RT revisa o perigo como revisa CAS/nome. O gate valida FORMA (`H\d{3}` bem-formado), mapeia os reconhecidos, emite pendência só em token malformado (D-ARQ-22). Cadeia de confiança: FDS declara → LLM transcreve verbatim → RT admite → mapa determinístico → flag. `[DERIVADO — R-FDS-06; D-ARQ-47 cl.4; D-ARQ-22]`.

*Parte 4 — fronteira de escopo: recorte B popula o sinal; a reordenação do ramo-0 é o passo 2.* Com as flags populadas por frase-H, "ausência de flag" passa a significar "FDS declarou sem perigo", não "não extraímos" — a pré-condição que a reordenação exige. Consequências por caso:
- **Componente in-vocab (agente resolvido):** o recorte B JÁ corrige a saída — sensibilizante <5% → `materialidade` ramo 1 (bypass) → MATERIAL → promove a `Risco` com `is_sensibilizante=True`. Fecha o caso-saúde glutaraldeído/isocianato de 003.G, agora executável.
- **CAS-oculto (SI2 Tigre, `agente=None`):** a flag é populada e CARREGADA (gate-CAS ramo (d) devolve o componente intacto, preservando `frases_h`/flags), disponível na mesa; mas `materialidade()` ramo-0 (`agente is None → AUSENTE`) e a Fase C (`if componente.agente is None`) ainda curto-circuitam → saída inalterada no recorte B (NÃO regressão — é o estado de hoje). Honrar a flag antes do slug-check é o **passo 2** (reordenação do ramo-0 + Fase C), que fecha DT-003M-01 + DT-003M-02(B) juntas.
- **DT-003T-01 FECHA** com o recorte B: `is_sensibilizante` deixa de ser default-por-ausência e passa a ser populada com proveniência = frase-H admitida pelo RT. A recusa de introduzir a chave no `EntradaIndice`/`agentes.yaml` (o vetor da DT) fica superada: a fonte da flag é a FDS transcrita, não o vocabulário. "O dado precede a regra."

**Consequência.**
- NÃO cria nem altera regra clínica (R-* intactas; R-FDS-06 semântica preservada — ganha consumidor executável, nota de aplicação no PROTOCOLO). Estende o recorte de D-ARQ-42 (A→B) sem revogar o contrato (A).
- Determinismo intacto (D-ARQ-09): o LLM transcreve o H-code cru a montante; o mapa H-code→flag é função pura resolver-side.
- Anti-supressão (D-ARQ-22/31): o cru `frases_h` preservado em `Componente` é o mecanismo que impede perda de sinal — H-code não-mapeado (futuro carcinógeno-GHS) não some, fica na mesa para a fatia append-only.
- Cobertura de teste (IMPL): H334→sensibilizante, H317→sensibilizante, ambos, H350-não-mapeado→carrega-sem-flag, malformado→pendência, `()`→sem-flag; in-vocab sensibilizante <5% → MATERIAL; CAS-oculto sensibilizante → flag populada+carregada com saída ainda AUSENTE (documenta a fronteira do passo 2); roundtrip de serialização com `frases_h`. Cada teste falha sem a fatia.
- Gate de estado real antes de qualquer prompt cirúrgico: grep de quem constrói `MembroVerbatim`/`Componente` (fixtures; o gabarito `fds_t65`/`fds_verbatim_t65` ganha `frases_h` — SI2 → `("H334","H317")`); confirmar que `resolver_composicao` está plugado no pipeline antes de afirmar travessia de produção.

**Fronteiras (não confundir):**
- **D-ARQ-42/43** — estende o recorte (A→B); contrato de saída (`tuple[Componente,...]`), bicamada interna, fronteira "CAS transcrito" intactos. A nota 003.CH de D-ARQ-42 anunciou esta frente; D-ARQ-55 a escreve.
- **D-ARQ-46/47** — `frases_h` é campo novo do verbatim (por-membro); o gate de forma do perigo é irmão de `gate_forma`/`gate_cas`; a admissão pelo RT (cl.4) passa a cobrir o perigo.
- **D-ARQ-33 cl.5** — o bypass é lista append-only; recorte B apende sensibilização (via frase-H); carcinógeno-GHS apende depois (DT-003CI-01).
- **D-ARQ-34/35** — materialidade e promoção intactas; o recorte B só passa a POPULAR os bypasses que D-ARQ-34 Parte 2/4 já previa como dado da ficha.
- **DT-003M-01 / DT-003M-02(B) / DT-003T-01** — DT-003T-01 fecha; DT-003M-01 e DT-003M-02(B) ganham a pré-condição (flags populadas), fecham no passo 2 (reordenação).
- **DT-003CI-01** — carcinógeno-via-frase-H (H350/H351 GHS ≠ IARC), deferido.

**Nota de implementação (003.CJ).** Recorte B implementado em PR #190 (merge `1632145`; commits `bc78788` motor+testes, `4565eb0` revisão-RT+superfície+fixtures, `d4adb36` higiene mypy). Decisões de IMPL onde esta D-ARQ deixou aberto (registro completo no HISTORICO 003.CJ): `frases_h` OBRIGATÓRIO no schema do artefato-RT com `versao` mantida em 1 (sem artefato v1 persistido; ausência-como-`()` reintroduziria a ambiguidade D-ARQ-22); `cli_fds` no escopo (schema estrito quebraria o self-check da superfície); pendência `frase_h_malformada` com `destinatario="empresa"` não-bloqueante (espelha `cas_ausente`); mapa roda em TODOS os ramos do gate_cas e a flag só LIGA; forma `H\d{3}` estrita case-sensitive; `Risco` NÃO ganha `frases_h`. Cobertura: unit a–g, travessia h–i (in-vocab <5% → MATERIAL; CAS-oculto → flag carregada, saída AUSENTE — fronteira do passo 2 documentada por teste), roundtrip j–k, superfície l. Suite 723→740. `mapear_frases_h` carrega R-FDS-06 na docstring (rastreabilidade regulatória; footprint executável move o número-1 do PAINEL 18→19/42).

**Base.** Sessão 003.CI (10/07/2026), ARQUITETURA — passo 1 do cluster-FDS ratificado em 003.CH. Docs vivos lidos inteiros por git objects (PROTOCOLO v45, DECISOES até D-ARQ-54) + código da cadeia de transcrição em disco. Duas passadas críticas: (1ª) granularidade por-membro confirmada da estrutura GHS, mas o MECANISMO de localização (caso-rodapé SI2) adiado por medição — não cravar leitura de layout sem medir; (2ª) H350/H351→`is_carcinogeno_iarc` REFUTADO (GHS≠IARC, erro-silencioso D-ARQ-22) → recorte B mapeia só sensibilização, carcinógeno-GHS vira DT-003CI-01. Decisão de arquitetura — sem código. Ratificada pelo Diovanni.

## D-ARQ-56 — Passo 2 do cluster-FDS: bypass antes do slug-check em `materialidade()`; Fase C tripartida no sem-slug; promoção-sem-slug deferida (DT-003CK-01)

**Contexto.** D-ARQ-55 (recorte B, implementada em 003.CJ) populou `Componente.frases_h` + mapa {H334,H317}→`is_sensibilizante` — "ausência de flag" passou a significar "FDS declarou sem perigo", a pré-condição que a sequência ratificada em 003.CH exigia. Esta decisão executa o **passo 2**: honrar a flag antes do slug-check, fechando DT-003M-01 e DT-003M-02(B).

*Parte 1 — `materialidade()`: bypass avaliado ANTES do ramo-0.* O ramo-bypass (`is_carcinogeno_iarc or is_sensibilizante` → MATERIAL) passa à frente do ramo-0 (`agente is None` → AUSENTE). A flag vem da FDS via `frases_h` (D-ARQ-55), não do slug — o rationale da 003.J ("sem slug não há flags confiáveis") caducou para sensibilização. Caso-âncora: SI2 Tigre (H334+H317, CAS oculto) → MATERIAL. `[DERIVADO — D-ARQ-55; DT-003M-01]`

*Parte 2 — ramo-0 remanescente mantém AUSENTE.* Sem slug e sem flag, NÃO decidir por concentração: `is_carcinogeno_iarc` segue slug-dependente (carcinógeno-via-frase-H refutado, DT-003CI-01) — NÃO-MATERIAL por concentração seria supressão silenciosa (D-ARQ-22). O fechamento de DT-003M-02(B) acontece na Fase C (natureza da pendência), não no predicado. `[DERIVADO — D-ARQ-22; DT-003CI-01]`

*Parte 3 — Fase C: `agente is None` tripartido.* (a) flag de bypass ligada → `Pendencia(tipo="bypass_sem_slug", destinatario="empresa", bloqueante=True, regra_origem="D-ARQ-56")`, motivo nomeia as frases-H literais; NÃO promove Risco. (b) `frases_h == ()` → inerte-declarado: `materialidade_ausente` NÃO-bloqueante, `regra_origem="R-FDS-06"` — fecha DT-003M-02(B); a articulação "ausência de frase-H ⇒ inerte" permanece `[INTERPRETADO — prioridade na revisão de saída]`. (c) frases-H presentes não-mapeadas (ex. H350) → pendência bloqueante D-ARQ-35 mantida (conservador-correto).

*Parte 4 — promoção-sem-slug DEFERIDA (decisão P3(a), ratificada).* `Risco.agente: str` rejeita `None`; promover exigiria `Optional[str]` propagado por consolidação/emissão/regras (custo alto, sem consumidor) ou slug inventado (D-ARQ-22). Não existe regra clínica formalizada de conduta para sensibilizante-sem-agente — promover seria forma sem função. **Custo declarado, explícito:** exame NÃO dispara para sensibilizante de CAS oculto; o sistema entrega visibilidade (MATERIAL + pendência bloqueante nomeada), não conduta. Registrado como DT-003CK-01, condicionada a regra clínica.

**Universalidade.** O sinal vem do documento (frases-H GHS/NBR 14725), não de vocabulário setorial — vale igualmente para construção civil, indústria química e saúde.

**Fronteiras.** D-ARQ-55 — consome (flags populadas; fronteira do teste i fechada). D-ARQ-35 — ramo (c) preserva o bloqueio conservador. D-ARQ-33 cl.5 — lista de bypass intocada (append-only). D-ARQ-14 — ramo-0 permanece para sem-slug-sem-flag.

**Efeitos em DT.** DT-003M-01 FECHA. DT-003M-02(B) FECHA ((A), dado, segue aberta). DT-003CK-01 ABERTA (promoção-sem-slug).

**Nota de implementação (003.CK, mesma sessão).** PR #192 (merge `f7aa825`), 3 commits: `b82d4a3` (materialidade.py + inversão do teste-fronteira 003.CJ + teste de preservação do ramo-0), `0305166` (Fase C tripartida + testes (a)/(b)/(c) em `test_promocao_quimico.py` + fixture real SI2 em `test_integracao_composicao_fase_c.py`), `1ad7ca3` (fixup: comentários de fixture não afirmam ausência de frase-H — `()` de `fds_verbatim_t65` é medição PENDENTE, 003.CJ decisão 6; achado do Arquiteto na revisão pré-PR). Suite 740→744 + 4 skip; mypy `--strict` zero erro novo (46 baseline).

**Base.** Sessão 003.CK (10/07/2026), ARQUITETURA→IMPLEMENTAÇÃO. Kickoff + docs/código relidos por git objects (HEAD `8d73f16`). Espec P1–P3 fechada em 2ª passada crítica (a 1ª declarara IMPL com espec aberta) e ratificada pelo Diovanni (P3(a); ARQ+IMPL na mesma sessão).

## D-ARQ-57 — Localizador de blocos GHE: repertório determinístico de âncoras medidas + gate de segmentação; família cargo-based é fronteira de escopo sinalizada, não variação de âncora

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Consome integralmente DT-003CM-01 (medição dos 15 PGRs, 003.CM); é o requisito (b) da 003.BS ("generalização multi-PGR da âncora de recorte"), nomeado paliativo remanescente em D-ARQ-52/53. Implementação por fatias futuras. Autorização para virar D-ARQ do Diovanni (003.CN).

**Contexto.** `recortar_blocos_ghe` e `recortar_topo` (`motor/extracao_pgr.py`) dependem ambos de `_ANCORA_GHE = "SETOR/FUNÇÃO"`, match VERBATIM `startswith`, derivado de n=1 (Viverde). DT-003CM-01 mediu a generalização: a âncora casa **1 de 15 PGRs**; o acervo (só construção civil) usa ≥5 formas de cabeçalho de bloco. A NOTA 003.BM já declarara o limite ("generalização da âncora multi-PGR é medição futura"); a medição fechou. Esta decisão dá forma ao localizador que substitui a âncora única.

**Gate de estado real (disco, ddae587).**
- `recortar_blocos_ghe(paginas)`: achata linhas, `indices_ancora = [i for i,l ... if l.startswith(_ANCORA_GHE)]`, bloco i = âncora i → âncora i+1, último → fim; zero âncoras → `[]` (falha explícita, Pendência é do chamador). `[DERIVADO — git show ddae587:extracao_pgr.py]`
- `recortar_topo(paginas)`: inverso — 1ª linha até a linha ANTERIOR à 1ª âncora; **reusa `_ANCORA_GHE`** como fronteira-fim. `[DERIVADO — git show ddae587]`
- Ambos são núcleo puro (sem I/O, sem LLM, D-ARQ-09); a troca de âncora é solidária aos dois. `[DERIVADO — git show ddae587]`

**Decisão — três peças + um recorte.**

*Peça 1 — a localização permanece DETERMINÍSTICA (repertório de reconhecedores), NÃO migra para o LLM.* A localização de blocos é a região-finding que **precede** a transcrição-LLM — mesmo lugar do `extrair_texto_fds` (âncora-por-título + sobre-inclusão; o LLM lê o conteúdo por sentido depois, D-ARQ-47/AY). Mover a segmentação para o LLM: (a) viola D-ARQ-09 (fronteira testável sem API); (b) põe a decisão de CARDINALIDADE de blocos no LLM — o anti-padrão que D-ARQ-45 P1 proíbe (cardinalidade fora do LLM); (c) reintroduz a sub-segmentação silenciosa (caso-Vistamérica) mascarada por plausibilidade do modelo. `_ANCORA_GHE` verbatim único → **repertório de reconhecedores de cabeçalho GHE**, cada um função pura `linha -> bool` (testável), aplicados em disjunção. Discriminador já medido em DT-003CM-01, cobre formas 1–4 (GHE-based) em 10/12 docs pdfplumber: `^(INVENTÁRIO DE RISCO )?GHE:? \d+( - <título>)?$` em linha curta. Ganho colateral medido: resolve a **conflação Viverde** — a 2ª seção (`PROCESSO/SUBPROCESSO`, com `SETOR/FUNÇÃO` mas SEM linha GHE) deixa de casar. **Custo sinalizado:** a saída do recorte Viverde muda (42 âncoras `SETOR/FUNÇÃO` → 31 GHE-headers); é regressão de gabarito a tratar na IMPL, explícita, não silenciosa. `[DERIVADO — DT-003CM-01; extrair_texto_fds molde; D-ARQ-09/45]`

*Peça 2 — gate de segmentação anti-Vistamérica (o achado crítico de DT-003CM-01).* Trocar a âncora NÃO basta: o caso-Vistamérica (1 âncora na pág. 36 → 1 "bloco" de ~137 págs, lixo silencioso) atravessa a falha de zero-âncoras — 1 âncora ≠ zero. Gate de plausibilidade de segmentação, critério **densidade + contagem** (ratificado pelo Diovanni, 003.CN): bloco cuja extensão é desproporcional (candidato: 1 bloco cobre > X% das páginas do documento) **OU** `nº blocos ≤ 1` em doc > N págs → `Pendencia` bloqueante `segmentacao_implausivel`, `regra_origem="D-ARQ-57"`. Só-contagem (`≤1 bloco`) foi considerado e rejeitado: não pega bloco-gigante desproporcional em doc com 2+ blocos (brecha D-ARQ-22). Os limiares X/N ficam para a IMPL, calibrados contra os 15 medidos. Este gate é o que torna o localizador seguro diante de forma NÃO-medida (química/saúde): forma nova → 0-1 bloco ou bloco desproporcional → pendência bloqueante, nunca matriz sobre lixo. `[DERIVADO — DT-003CM-01 achado Vistamérica; D-ARQ-22/31/35 anti-supressão]`

*Peça 3 — família cargo-based (forma 5, 4/15) = fronteira de escopo, RECONHECER + SINALIZAR, não construir agora.* Ricco-Adm/Cjr/Hetrin/Serra Dourada não têm estrutura-GHE: a unidade de bloco é **cargo** (`CARGO/FUNÇÃO:`, `CARGO X - CBO: NNNN`) — forma 6 de DT-003L-01. Recorte-GHE é inaplicável. O localizador **reconhece** a família (ausência de reconhecedor-GHE + presença de reconhecedor-cargo) e emite `Pendencia` bloqueante `pgr_cargo_based` (unidade = cargo, recorte-GHE inaplicável), `regra_origem="D-ARQ-57"` — NUNCA força recorte-GHE nem falha silenciosa. **Recorte-por-cargo (2ª unidade de bloco) NÃO é construído nesta linha** (ratificado 003.CN): empilhar duas unidades de bloco numa decisão só violaria "uma coisa por vez" e o recorte-cargo ainda não tem gabarito medido isolado. É fatia futura própria. `[DERIVADO — DT-003CM-01 família cargo-based; DT-003L-01 forma 6; D-ARQ-06]`

*Recorte da 1ª leva.* Sobre-inclusão e fronteira-fim (bloco i → âncora i+1; último → fim) PRESERVADAS (direção segura já selada). `recortar_topo` reconciliado no mesmo commit (fronteira-fim do topo = 1ª âncora do repertório GHE, não mais `SETOR/FUNÇÃO`). Fora da 1ª leva: recorte-por-cargo (peça 3, fatia futura); extensão multi-setor do repertório (química/saúde não-medidos — cresce por medição append, o gate da peça 2 segura o intervalo).

**Consequência.**
- Fecha o requisito (b) da 003.BS (paliativo nomeado em D-ARQ-52 "Universalidade" e D-ARQ-53 P.remanescente): a âncora deixa de ser Viverde-pontual.
- Determinismo do motor intacto (D-ARQ-09): localização determinística, transcrição-LLM segue a jusante e a montante da "PGR transcrita".
- **Universalidade (gate CLAUDE.md):** o reconhecedor de família (GHE-based vs cargo-based) é o que dá universalidade — química/saúde podem ser qualquer um dos dois. O repertório de âncoras vem de n=15 SÓ construção civil; o gate de segmentação é a rede para o não-medido. Paliativo honesto sinalizado, não solução-Viverde.
- Não cria nem altera regra clínica (R-* intactas; PROTOCOLO v49 inalterado). Cria contrato do localizador de blocos.

**Fatiamento previsto (IMPL futura, ordem):**
1. Repertório de reconhecedores GHE + troca da âncora em `recortar_blocos_ghe` **e** `recortar_topo` (solidários); gabarito Viverde re-medido (31/32 blocos).
2. Gate de segmentação (`segmentacao_implausivel`, densidade+contagem) com limiares X/N calibrados nos 15; caso-âncora Vistamérica no teste (1 bloco/137 págs → bloqueante).
3. Reconhecedor de família + `pgr_cargo_based` bloqueante; caso-âncora Ricco-Adm/Cjr.
4. (futura, própria) recorte-por-cargo como 2ª unidade de bloco.

**Fronteiras (não confundir):**
- **DT-003CM-01** — input medido integral; permanece ABERTA até a IMPL do localizador (esta decisão a consome, não a fecha).
- **D-ARQ-50 P1 / D-ARQ-53 P1** — `extrair_texto_pgr` e o mecanismo de `recortar_topo` intocados; muda a ÂNCORA que ambos herdam.
- **D-ARQ-49/52** — a costura arquivo→Resultado (`processar_arquivo_pgr`) é estável; o localizador troca por dentro.
- **D-ARQ-45 P1** — reusado como fundamento: cardinalidade (nº de blocos) NÃO vai para o LLM.
- **DT-003L-01** — forma 6 (cargo-based) é a família da peça 3; permanece ABERTA.
- **D-ARQ-09** — preservada: localização determinística, LLM a jusante.

**Base.** Sessão 003.CN (11/07/2026), ARQUITETURA. Kickoff + PROTOCOLO v49 + DECISOES v110 relidos por git objects (HEAD `ddae587`); estado real de `extracao_pgr.py` conferido em disco. Duas passadas: (1ª) recomendou repertório determinístico + gate estrutural + tratamento cargo-based; (2ª crítica) confirmou que só-troca-de-âncora deixa o caso-Vistamérica passar (gate de densidade obrigatório, não só contagem) e que recorte-cargo empilhado viola "uma coisa por vez". Duas escolhas ratificadas pelo Diovanni (003.CN): família cargo-based = reconhecer+sinalizar (não construir); gate = densidade+contagem. Decisão de arquitetura — sem código.

**Andamento (003.CO) — peça 1 IMPLEMENTADA.** `eh_cabecalho_ghe` + repertório `_RECONHECEDORES_GHE` em disjunção materializam a peça 1 em `motor/extracao_pgr.py` (`recortar_blocos_ghe`/`recortar_topo` migrados, solidários). Regex `fullmatch` com teto de 80 caracteres e traço `\s*-\s*` (espaçamento variável — refino sobre o discriminador medido em DT-003CM-01, que não cobria `"GHE NN-"` colado, achado no Viverde real). Gabarito Viverde **31 confirmado**; conflação da 2ª seção (`PROCESSO/SUBPROCESSO`) resolvida por design, como previsto. Peças 2 (gate de segmentação) e 3 (família cargo-based) pendentes. PR #198, merge `4571ec6`. Detalhe em HISTORICO 003.CO.

**Andamento (003.CP) — peça 2 IMPLEMENTADA.** `avaliar_segmentacao(paginas) -> Pendencia | None` em `motor/extracao_pgr.py`: gate puro densidade+contagem sobre a mesma fronteira de bloco de `recortar_blocos_ghe`, emite `segmentacao_implausivel` bloqueante (`regra_origem="D-ARQ-57"`, `destinatario="extracao"`). Limiares calibrados por medição direta dos 15 PGRs do acervo (003.CP, ratificados pelo Diovanni): densidade X=40% (maior legítimo medido 34,8%, ALT T65; implausíveis ≥44,4%) e contagem N=10 (≤1 bloco em doc >10 págs). Ganho não previsto: a densidade mata a armadilha-Floramazônia (6 falsos cabeçalhos em prosa, maior "bloco" 50% — a contagem sozinha não pegaria). Falsos-positivos conhecidos e aceitos por design (anti-supressão D-ARQ-22/31/35): TPB Andrade (1 âncora legítima em 45 págs) e R78 Naturia (doc parcial) viram pendência p/ revisão humana, nunca lixo silencioso. Peça 3 (cargo-based) pendente. PR #200, merge `81e9a9b`. Detalhe em HISTORICO 003.CP.

**Andamento (003.CQ) — peça 3 IMPLEMENTADA; 1ª leva completa (3/3).** `eh_sinal_cargo` + `_RECONHECEDORES_CARGO` (3 formas medidas em 003.CQ, pdfplumber: `CARGO/FUNÇÃO:` Ricco-Adm; `CARGO ... CBO: NNNNNN` Cjr; grid-header AIHA `Função ... Perigo / Risco` Hetrin/Serra Dourada) + `avaliar_familia` (zero âncoras GHE e ≥1 sinal-cargo → `pgr_cargo_based` bloqueante, regra_origem="D-ARQ-57") + composto `avaliar_estrutura` (família ANTES do gate, exclusão mútua — diagnóstico específico vence genérico; decisão fina de 003.CQ, cargo-based nunca sai como `segmentacao_implausivel`). Refino sobre o censo 003.CM: Hetrin/SD não usam `CARGO/FUNÇÃO:` como cabeçalho (lá é boilerplate de assinatura); o sinal deles é o grid-header AIHA. Forma `INFORMAÇOES SOBRE CARGOS/FUNÇÕES NN` (Ricco-Adm) fora do repertório por redundância com a forma 1. `eh_sinal_cargo` é SINAL DE FAMÍLIA, não âncora de recorte — recorte-por-cargo segue fatia futura própria. 15 testes (sintéticos + Ricco-Adm e Cjr reais). PR #202, merge `a769dbc`. Detalhe em HISTORICO 003.CQ.

**Andamento (003.CR) — 1ª leva PLUGADA em produção + refino da peça 2.** `avaliar_estrutura` conectado em `preparar_ghes` (`adaptadores/orquestracao_pgr.py`), ANTES de `recortar_blocos_ghe`/transcrição: doc cargo-based ou segmentação implausível bloqueia no pipeline real sem gastar chamada LLM sobre recorte inválido; diagnóstico específico (`segmentacao_implausivel`) vence `blocos_ausentes` genérico em doc grande. A 1ª leva (repertório+gate+família) deixa de ser inerte — a nota de contexto "avaliar_estrutura sem chamador de produção" fica fechada. Plugar expôs defeito latente da peça 2: o ramo de densidade não tinha o piso de páginas que a contagem já tinha — doc pequeno com bloco único satura 100% por definição matemática (a densidade nunca foi calibrada abaixo do piso; legítimo máx. 34,8% medido em docs grandes), disparando falso-`segmentacao_implausivel` e quebrando 5 testes legítimos de doc pequeno. Correção (NÃO paliativa — o piso sempre foi a intenção da peça 2): `total_paginas > _LIMIAR_PAGINAS_DOC_MINIMO` guardando o ramo de densidade, espelhando a contagem; abaixo do piso a segmentação não é julgada por nenhum dos dois testes (bloco único cobrindo doc pequeno é plausível). Universal (constr./química/saúde): PGR minúsculo passa ao processamento; a patologia Vistamérica — sempre grande — segue pega. Muda saída do motor: docs ≤ piso deixam de ser marcados por densidade. Commits `e73b281` (piso) + `82a4a81` (plug), PR #204, merge `0e95574`. Detalhe em HISTORICO 003.CR.

**Andamento (003.CS) — 1ª validação out-of-sample do localizador (medição multi-setor).** Dois PGRs reais fora de construção civil, medidos com `avaliar_estrutura` (pdfplumber, host). (1) **Bertoncini** (metalúrgica, Sistema ESO) → `pgr_cargo_based`: o reconhecedor de família acertou fora de construção civil (química/indústria cai no ramo cargo-based) — ação nenhuma. (2) **HU-UFGD** (hospital universitário, template EBSERH, 197 págs) → `segmentacao_implausivel`, 0 âncoras. Sonda de estrutura (host) mostrou que o HU **não** é narrativo nem cargo-based: é GHE-conceitual — ~23 blocos `GRUPO HOMOGÊNEO DE EXPOSIÇÃO SIMILAR (GHES)` segmentados por `Unidade / Setor`, linhas por `Cargo/Função`, tabela `Riscos | Agente de Risco | Fonte Geradora | Expostos`. A âncora de D-ARQ-57 exige `GHE: NN` numerado (formato Viverde); o cabeçalho EBSERH é `GRUPO HOMOGÊNEO DE EXPOSIÇÃO SIMILAR (GHES)` **sem numeração** → 0 match. Leitura arquitetural: a rede de segurança (peça 2) **funcionou** — bloqueou, não gerou matriz sobre lixo (design validado nesse eixo); o furo é real e específico do **repertório de âncora GHE**, não da família (acertou a especificidade) nem do gate. Não é "forma não-medível que se bloqueia p/ sempre" — é forma NOVA agora medida, do padrão dominante da saúde pública federal (EBSERH cobre todos os HUs). Candidata a extensão de repertório → **DT-003CS-01** (aberta). Sem código, sem R-*. `[MEDIDO — pdfplumber host, 003.CS; 2 PGRs públicos]`

**Andamento (003.CZ) — censo out-of-sample n=3 reenquadra DT-003CS-01: a forma EBSERH vigente é cargo-based, não GHE.** Censo web (template corporativo `PGR.SOST.001`/`USOST`, v7.0 2023, ~40 HUs) + medição host (pdfplumber, 3 PGRs EBSERH reais). Achado: UFGD-v7.0 08/2023 (184p) e HUMAP (368p) **convergem** numa forma **card por lotação/cargo** — `DADOS GERAIS` + linha-tripla `Lotação: … Escala de Trabalho: … Qtd` (105/140 cards), **sem** cabeçalho GHE/GHES; o witness GHES/`INVENTÁRIO DE RISCOS / ANÁLISE NN` da 003.CS é doc **legado** da UFGD (197p, n=1). Leitura: o EBSERH vigente NÃO é GHE-conceitual → o furo migra da **peça 1** (âncora GHE) para a **peça 3** (família cargo-based) — `_RECONHECEDORES_CARGO` não inclui a realização `Lotação:`-tripla. Colisão medida e descartada (n=3): card e GHES nunca coexistem no mesmo doc (b_ card=0/GHES=23; a_/d_ card=105/140/GHES=0) → somar o reconhecedor-Lotação não mislabela o doc GHES (e `avaliar_familia` já veta por GHE-presente). `DADOS GERAIS` rejeitado como âncora (frágil ao space-collapse: 105 no doc espaçado, 0 no colado); âncora = tripla `^Lota[cç][aã]o:\s*.*Escala\s*de\s*Trabalho:\s*.*Qtde?:` (tolerância de espaço, molde do traço `\s*-\s*` da peça 1, validada contra as 2 realizações — espaçada e colada). GHES/ANÁLISE **aposentado** (n=1, forma superada; anti-overfit simétrico ao que a medição refutou). Recorte-por-cargo (DT-003L-01 forma 6) **elevado** de fatia genérica adiada a alavanca do setor saúde — construção-cargo e EBSERH-saúde convergem na mesma unidade de bloco. `[INCERTO — dominância nos ~40 HUs é convergência n=2, não cobertura provada]`. Sem código (ARQUITETURA). `[MEDIDO — pdfplumber host, 003.CZ; 3 PGRs EBSERH públicos]`

**Andamento (003.DA) — forma 4 do repertório cargo-based implementada: reconhecedor `Lotação:`-tripla.** `_reconhece_lotacao_escala_qtd` somado a `_RECONHECEDORES_CARGO` (`extracao_pgr.py`), materializando o reenquadramento de DT-003CS-01 (003.CZ) — EBSERH-vigente (template corporativo `PGR.SOST.001`, card por lotação/cargo) agora roteia a `pgr_cargo_based` bloqueante via `avaliar_familia`/`avaliar_estrutura`. n=2 realizações medidas e validadas em teste real: espaçada UFGD-v7 (a_, 105 matches) e colada HUMAP (d_, 140 matches); não-colisão confirmada no legado GHES (b_, 0 matches no nível-função). 3 PGRs EBSERH públicos trackeados em `matrizes_originais/` (precedente Ricco/Cjr 003.CQ — teste real com falha explícita, não skip). Commits `1e67ca9` (PDFs) + `de56c3c` (reconhecedor+testes). `[MEDIDO — pdfplumber host, 003.CZ; teste real, 003.DA]`

**Andamento (003.DB) — medição da anatomia do bloco-cargo (pré-requisito da peça 4).** CONHECIMENTO/medição dos 4 witnesses trackeados (pdfplumber host): a família cargo-based (peça 3) parte em **N:1** grupo-GHE (Ricco-Adm, bloco `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN`, N cargos slash-separated : 1 inventário compartilhado — GHE-shaped) vs **1:1** card-por-cargo (Cjr `CARGO-CBO`, 1 cargo; UFGD 105 / HUMAP 140 cards `Lotação:`-tripla, `RISCOS AMBIENTAIS` embutida). Achado que reenquadra a peça 4: ambas reduzem ao `GHEPGR` (1:1 = GHE de 1 cargo; N:1 = GHE normal), logo o recorte-por-cargo NÃO é 2ª unidade de bloco (tipo novo) — é reconhecedores de recorte + binding da tabela de risco por-posição, reusando `GHEVerbatim→GHEPGR` (D-ARQ-51). Fork para a ARQUITETURA (003.DC): Ricco-Adm N:1 roteia por extensão de âncora GHE (peça 1) vs caminho cargo. Gabarito + caveats (contagem-global sobreconta a tabela; título numerado NÃO-âncora) em DT-003DB-01. Sem código, sem R-*. `[MEDIDO — pdfplumber host, 003.DB; 4 witnesses trackeados]`

**Andamento (003.DC) — decisão da peça 4: recorte-por-cargo reduz a `GHEPGR`; fork N:1 resolvido rota (i); fatiamento 4a-4d.** ARQUITETURA consumindo DT-003DB-01. **Fork N:1 (Ricco-Adm) → rota (i):** o header `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` entra na peça 1 (`_RECONHECEDORES_GHE`, regex numerado fullmatch); Ricco-Adm ingere como GHE-based e sai de `pgr_cargo_based`. Justificativa não-conveniência: o N:1 é GHE estrutural **E** clínico — N cargos slash-separated compartilham 1 inventário → **R-GHE-01** [VALIDADO] (matriz idêntica p/ todas as funções do GHE) casa exato; rota (ii) exigiria binding 1-tabela:N-cargos sem ganho clínico (R-GHE-01 já iguala). Papel do header muda de sinal-de-família (excluído 003.CQ por redundância) p/ **âncora-de-recorte GHE** — o argumento de redundância não se aplica. Custo (header-como-ruído em doc GHE-based) não-medido → mitigado por regex numerado fullmatch + gate peça 2 + medição pré-merge (15 do acervo + witnesses out-of-sample). Consequência: recorte-por-cargo genuíno = só **1:1** (Cjr + EBSERH). **Recorte 1:1:** `recortar_cards_cargo` espelho de `recortar_blocos_ghe`, repertório NOVO `_RECORTADORES_CARGO` (Lotação-tripla + `CARGO-CBO`; grid-header AIHA Hetrin/SD **FORA** — sinal-de-família ≠ âncora-de-recorte); card i = âncora i→i+1 → `GHEVerbatim(cargos=[1])` → `hidratar_ghe` **inalterado** (D-ARQ-51 já suporta GHE de 1 cargo); id `GHE-NN` correto (1:1 = GHE de 1 cargo, não paliativo). Caveats DT-003DB-01 mortos por construção: (1) tabela pelo span, rejeitado recorte por contagem de `RISCOS AMBIENTAIS` (= subsegmentação silenciosa, D-ARQ-22); (2) título `NN.N` não-âncora (âncora = Lotação-tripla); (3) cargo-nome variável = concern transcrição-LLM. **Roteamento — a peça 3 estreita, não some:** `avaliar_estrutura` parte a família — cargo recortável (Lotação/CBO) → ingere; cargo só-sinal-de-família (grid AIHA) → segue `pgr_cargo_based` bloqueante (anti-supressão D-ARQ-31/35). **Passagem de verificação (2ª passada, pedida pelo Diovanni) — 3 furos materiais na 1ª proposta:** (V1) 4a não é só a âncora — ingestão atravessa `avaliar_segmentacao` (Ricco-Adm tem 2 blocos; densidade X=40 pode falso-marcar witness legítimo) + transcrição de anatomia nova → medição pré-merge = `avaliar_estrutura` **fim-a-fim** no Ricco-Adm, divergência vs. esperado = **BLOQUEADOR** (não ajusta limiar em silêncio), inclui gabarito de forma do bloco N:1; (V2) **Cjr tropeça no próprio gate** — 1 card no doc → ramo-contagem (≤1 bloco em doc >N págs) marca implausível → Cjr fica **GATED por design** (revisão humana, classe TPB Andrade), witness do recorte (gabarito 1 card), não da travessia; recalibrar gate p/ unidade-cargo **REJEITADO** (n=1 não calibra; overfit simétrico ao refutado em 003.CZ); quem a peça 4 destrava de fato = **EBSERH** (105/140 cards, passa folgado); (V3) **transcrição do card não existe** — a 1ª passada assumiu reuso do transcritor-GHE em silêncio; o card EBSERH tem anatomia nova (Lotação-tripla, `RISCOS AMBIENTAIS` 5-cat embutida, cargo-nome variável) → o "4b" ingênuo eram 3 fatias disfarçadas. **Fatiamento 4a→4b→4c→4d** (empilhar recorte+roteamento+transcrição viola "uma coisa por vez", veto 003.CN): **4a** fork(i) — reconhecedor N:1 em `_RECONHECEDORES_GHE` + medição fim-a-fim + gabarito de forma + teste real Ricco-Adm (pré-merge: zero ruído do header nos 15 + witnesses); **4b** `recortar_cards_cargo` isolado (molde construir-sem-plugar 003.BP/BQ) — `_RECORTADORES_CARGO`, gabarito real 105/140/1 exato, gate nos spans com limiares herdados `[INTERPRETADO — recalibrar se witness legítimo divergir]`, Cjr-gated documentado; **4c** transcrição do card — gabarito de forma 1 UFGD + 1 HUMAP, prompt-reuso vs prompt-card, `gate_forma` sobre a saída; **4d** split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — **só aqui DT-003CS-01 FECHA**. 4a e 4b independentes; 4a primeiro (menor/menor-risco, destrava construção N:1). Não é R-* — motor contract (como peças 1-3), sem teste-por-regra clínica, mas teste real com falha explícita obrigatório (precedente 003.CQ/DA). DT-003DB-01 e DT-003CS-01 seguem ABERTAS (consumidas pela decisão, fecham na IMPL). Ratificado pelo Diovanni. Sem código, sem R-*. PAINEL não re-tirado. `[ARQUITETURA — 003.DC; consome DT-003DB-01; R-GHE-01 [VALIDADO]; D-ARQ-51/06/09/22/31]`

**Andamento (003.DD) — fatia 4a IMPLEMENTADA e mergeada: forma 5 do repertório GHE.** PR #222 (`dfdcbc5`, main `7ee4be9`). `_reconhece_cabecalho_informacoes_cargos_funcoes` somado a `_RECONHECEDORES_GHE`, materializando a rota (i) da 003.DC: header N:1 `INFORMAÇ[OÕ]ES SOBRE CARGOS/FUNÇÕES NN` (fullmatch, teto 80 chars) — Ricco-Adm sai de `pgr_cargo_based`, ingere GHE-based (2 blocos). **Decisão 003.DD-1 (regex sem normalização).** Medição prévia (Etapa 0a) achou BLOQUEADOR: o verbatim real extraído tem perda de diacrítico determinística de fonte/glifo na 1ª palavra (`INFORMAÇOES`, Õ→O, codepoint `0x4f`, confirmado por `hex(ord(c))` — não é artefato de terminal/console; o mesmo `Õ` em `FUNÇÕES` extrai correto, `0xd5`). Regex candidata (com `Õ` só) não casava — 0 matches em vez de 2. Decisão do Arquiteto: classe `[OÕ]` no ponto medido, SEM normalização NFC/NFD — verbatim-estrito codificaria o defeito de extração como contrato de forma, e normalizar mudaria a convenção VERBATIM da peça 1 inteira (fora do escopo da fatia). Re-medição R1: 2 matches no Ricco-Adm (págs. 14/15), 0 nos demais 17 documentos (15/15 do acervo DT-003CM-01 + 3 EBSERH) — zero ruído confirmado. **Decisão 003.DD-2 (gate mantido, Ricco-Adm gated by design).** Medição R2 (`avaliar_estrutura` simulado com a regex final) achou 2º BLOQUEADOR: bloco 2 (âncora pág. 15, vai ao fim do doc de 24 págs.) mede 10 págs. = 41,7% > `_LIMIAR_DENSIDADE_PCT` (40,0%) → `segmentacao_implausivel`, não `None`. Decisão do Arquiteto: rota (i) MANTIDA; Ricco-Adm fica GATED por densidade **by design** — mesma classe do Cjr (V2 de 003.DC): witness de que reconhecedor+recorte funcionam (2 blocos, âncoras corretas), revisão humana bloqueante, anti-supressão vence. Limiar **NÃO recalibrado**: margem restante contra os implausíveis (≥44,4%) seria de só 2,7pp, contra ~10pp da calibração original (003.CP). **Dívida candidata (sem DT formal):** a causa direta do gate é a sobre-inclusão da cauda do último bloco (bloco 2 vai até o fim do documento por construção de `recortar_blocos_ghe`, limitação conhecida desde o Viverde, D-ARQ-22) — infla a densidade medida do último bloco em qualquer doc pequeno com header no fim; eventual correção é estrutural (fronteira-fim do último bloco), não recalibração de limiar. Testes: +2 forma-5 (verbatim medida `INFORMAÇOES...` + forma sã `INFORMAÇÕES...`, falha explícita demonstrada via stash pré/pós-código), +2 armadilhas (sem número; sufixo rejeitado por fullmatch), flip 1-por-1 do teste real Ricco-Adm (`pgr_cargo_based` → `segmentacao_implausivel`, ≠ `pgr_cargo_based` — o ponto da 4a), +1 `test_recorte_blocos_ghe_ricco_adm_real` (witness do recorte apesar do gate). Suíte 825+4→830+4 (+5 líquido); mypy --strict: mesmos 46 pré-existentes, zero nos arquivos tocados. `_RECONHECEDORES_CARGO`/`avaliar_familia`/`avaliar_estrutura`/`avaliar_segmentacao`/`recortar_blocos_ghe`/`recortar_topo` inalterados. Nenhuma R-* criada/alterada. Fatias 4b (recorte 1:1 isolado), 4c (transcrição do card), 4d (plug + fecha DT-003CS-01) seguem abertas. `[IMPLEMENTADO — 003.DD; PR #222]`

**Andamento (003.DF) — fatia 4b IMPLEMENTADA e mergeada: recortar_cards_cargo ISOLADO.** PR #226 (`2bb8d20`, main `64ccf06`). Molde construir-sem-plugar (003.BP/BQ): `_RECORTADORES_CARGO` (2 membros, reuso EXATO dos predicados já existentes — `_reconhece_lotacao_escala_qtd` e `_reconhece_cargo_cbo`, zero regex duplicada) + `eh_ancora_card_cargo` (espelho de `eh_cabecalho_ghe`) + `recortar_cards_cargo` (espelho estrutural exato de `recortar_blocos_ghe` — mesmo achatamento, mesma fronteira de card, mesma sobre-inclusão como direção segura D-ARQ-31/35, zero âncoras → `[]`). `_reconhece_funcao_grid_perigo_risco` (grid AIHA) e `_reconhece_cargo_funcao_dois_pontos` (`CARGO/FUNÇÃO:`) ficam FORA do repertório de recorte — sinal-de-família ≠ âncora-de-recorte (decisão 003.DC): o grid AIHA não delimita card individual, e o header Ricco-Adm já recorta como GHE (forma 5, fatia 4a). Gabarito real medido: UFGD-v7 **105** cards, HUMAP **140** cards, Cjr **1** card — todos EXATOS, zero divergência, nenhum ajuste de regex ou limiar. `_LIMIAR_DENSIDADE_PCT`/`_LIMIAR_PAGINAS_DOC_MINIMO` intocados. Testes: 7 novos (2 sintéticos de fronteira — Lotação-tripla e CARGO-CBO —, 1 zero-âncora, 1 negativo grid-AIHA-não-ancora, 3 reais 105/140/1); falha explícita demonstrada via `git stash` (sem o código, `ImportError` na coleta da suíte inteira). Suíte 834+4→841+4 (+7); `mypy --strict agente_medico/motor/`: zero erros (os 46 pré-existentes vivem todos em `agente_medico/tests/*.py`, nunca em `motor/`) — delta-zero. `avaliar_estrutura`/`avaliar_familia`/`avaliar_segmentacao` inalterados (split de roteamento é 4d); nenhuma transcrição de card (4c); nenhum plug em `preparar_ghes` (4d). Nenhuma R-* criada/alterada. Nota 003.DF em DT-003CS-01 (4b fechada, DT segue ABERTA até 4d). `[IMPLEMENTADO — 003.DF; PR #226]`

**Andamento (003.DG) — ARQUITETURA da fatia 4c: gabarito de forma do card medido, 4 decisões de transcrição, rota-de-recuperação do cargo; 4b NÃO reabre.** Sessão ARQUITETURA/medição (sem código) sobre 2 witnesses ricos extraídos por `recortar_cards_cargo` REAL (UFGD-v7 card [16], lotação Laboratório de Análises Clínicas e Anatomia Patológica; HUMAP card [51], `MÉDICO–ANESTESIOLOGIA` da Clínica Cirúrgica; ambos exercitam as 5 categorias de risco, cobrindo as 2 realizações — espaçada e colada). Seleção por riqueza com exclusão do ÚLTIMO card e teto de 3× a mediana de linhas: o último card é inflado pela cauda-até-o-fim-do-documento (classe da dívida 003.DD) e a 1ª rodada de seleção o elegeu por premiar poluição de span em vez de riqueza de card. Contagens 105/140 re-conferidas EXATAS nos dois witnesses (cláusula de bloqueador não disparou).

**Andamento (003.DH) — fatia 4c-i IMPLEMENTADA e mergeada: `recuperar_titulos_cargo` isolado.** PR #229 (`5215dcf`, main `b9c142d`). Materializa a decisão 003.DG-4: `recuperar_titulos_cargo(paginas) -> list[str]` em `motor/extracao_pgr.py`, função pura, espelho estrutural EXATO de `recortar_cards_cargo` (mesmo achatamento, mesmos índices de âncora via `eh_ancora_card_cargo`, mesma saída VERBATIM, zero âncoras → `[]`). Para o card `i` o VÃO é `linhas[âncora i-1 : âncora i]`; para o card `0` é o texto PRÉ-ÂNCORA que o recorte descarta — é ali que vive o título do primeiro card. Varredura PARA TRÁS devolvendo a linha mais próxima da âncora que satisfaça o **PAR**: casa `^\d{1,3}\.\d{1,3}\s+\S` E tem `DADOS\s*GERAIS` dentro das 3 linhas seguintes. Saída paralela por ÍNDICE aos cards; `""` é ausência EXPLÍCITA e nunca é filtrada da lista — filtrar desalinharia títulos e cards em silêncio (classe D-ARQ-22), e a invariante `len(recuperar_titulos_cargo(p)) == len(recortar_cards_cargo(p))` virou teste nos 3 witnesses reais.

*Decisão 003.DH-1 (a âncora de recuperação é o PAR, não o padrão numérico).* Medição da própria sessão achou o furo ANTES do código: a rota "última linha `NN.N` antes da âncora" produz FALSO-POSITIVO no HUMAP — casa `4.3 RESUMO FINAL DA IDENTIFICAÇÃO DOS RISCOS BIOLÓGICOS MAIS`, título de SEÇÃO e não de cargo. A causa foi REGRESSÃO DE SPEC entre sessões (não achado do documento): a medição H2 de 003.DG exigia o par `NN.N` + `DADOS GERAIS` — a anatomia medida —, e o gate escrito na abertura da 003.DH simplificou para o padrão numérico solto, largando a adjacência. Exigir o par custa ZERO no verdadeiro-positivo (UFGD segue 105/105) e zera o falso-positivo (HUMAP 1 → 0, rejeitado nominalmente). `DADOS\s*GERAIS` tolerante a espaço é obrigatório (o HUMAP extrai colado, `DADOSGERAIS`). A janela de 3 linhas é `[INTERPRETADO]` — funcionou nos 3 witnesses, mas a distância real título→`DADOS GERAIS` não foi medida card a card.

*Gate pré-IMPL (003.DG-4) cumprido e ENDURECIDO na execução.* O gate herdado era "105/105 títulos recuperados"; a passada de verificação da abertura julgou-o FRACO (contagem cega passaria com falsos-positivos) e acrescentou 2 critérios: títulos DISTINTOS e numeração ESTRITAMENTE CRESCENTE. Resultado medido no UFGD-v7: 105/105 recuperados, 105/105 distintos, crescente — GATE PASSA, com literais `13.1 Advogado` … `13.106 Terapeuta Ocupacional`. Gabarito dos outros witnesses (medido antes de virar teste, nunca escrito de memória): HUMAP 140 cards / **0** títulos, Cjr 1 card / **0** títulos — zero é resultado LEGÍTIMO ali (o cargo vive na linha de valores do próprio card, não em título numerado).

*Restrição explícita gravada no código.* O número do título NÃO é índice do card e nenhuma aritmética é feita sobre ele: o UFGD tem 105 cards com títulos indo até `13.106` — a numeração do documento tem lacuna.

Gates: suíte 841+4 → **853+4** (+12 exato: 6 sintéticos + 3 reais + 3 de invariante); `mypy --strict agente_medico/motor/` zero erros, delta-zero. Falha explícita demonstrada via `git stash push -- agente_medico/motor/extracao_pgr.py` (`ImportError` na coleta, não falha silenciosa); `git stash pop` restaurou verde. Revisão do Arquiteto sobre git objects: aprovada sem correção — a única auto-correção do Code foi bug no texto do PRÓPRIO teste (filler sintético continha a substring `DADOS GERAIS`), corrigido no teste com a produção intacta, classe distinta do ajuste-para-fechar que a cláusula de bloqueador proíbe. `recortar_cards_cargo`/`eh_ancora_card_cargo`/`_RECORTADORES_CARGO`/`recortar_blocos_ghe`/`recortar_topo`/`avaliar_*` e os dois limiares INTOCADOS; nenhum plug em `preparar_ghes` (4d). Nenhuma R-* criada/alterada. Restam **4c-ii** (contrato `TranscritorCard` + `transcrever_cards` + `gate_forma_ghe` reusado, LLM mockado — molde 003.BN), **4c-iii** (cliente real + prompt-card + sonda ao vivo — molde 003.BO/CA) e **4d** (split de roteamento + plug + e2e EBSERH, que FECHA DT-003CS-01). `[IMPLEMENTADO — 003.DH; PR #229]`

**Andamento (003.DI) — fatia 4c-ii IMPLEMENTADA e mergeada: contrato `TranscritorCard` mockado.** PR #231 (`0c1e970`, main `81f0962`). Molde construir-sem-plugar 003.BN (contrato sob mock antes do cliente real): módulo NOVO `motor/transcritor_card.py` (precedente `transcritor_topo.py`/003.BW — um módulo por unidade transcrita; `transcritor_pgr.py` intocado) com `TranscritorCard` (Protocol) e `transcrever_cards(cards, titulos, cliente) -> tuple[GHEVerbatim, ...]` — delega par a par na ordem, cliente injetado, sem retry/telemetria, saída CANDIDATA. `gate_forma_ghe` REUSADO sem alteração via import (003.DG-3) — nenhum gate próprio no módulo. Docstrings cravam a semântica bounded para a 4c-iii: nome = lotação/setor da linha SEGUINTE à âncora de labels (nunca a linha `Lotação: Escala de Trabalho: Qtde:`); cargos = o cargo único do card (do titulo quando não-vazio — UFGD — senão embutido no corpo — HUMAP); desglue bounded do space-collapse (D-ARQ-50 P2); titulo VERBATIM com prefixo numérico e NENHUMA aritmética sobre o número (restrição 003.DH: numeração com lacuna).

*Decisão 003.DI-1 (contrato de 2 argumentos; mismatch = ValueError, não Pendencia).* `transcrever(card, titulo)` em vez de concatenar o título no span: a montagem-do-input é concern declarado da 4c (003.DG-4) e o tipo distinto impede reuso acidental do cliente-GHE; `""` = ausência explícita, espelho exato da saída de `recuperar_titulos_cargo`. `len(cards) != len(titulos)` levanta `ValueError` com as duas contagens: o paralelismo por índice é garantido por construção (as duas funções espelham as mesmas âncoras) — mismatch é bug de construção, não condição de documento.

Testes (8): 5 núcleo sem PDF (delegação/pareamento verbatim por índice; listas vazias → `()`; mismatch → `ValueError`; composição com o gate: nome vazio reprova `forma_verbatim_pgr` bloqueante; card todo-N/A com `riscos=()` APROVA — regressão da observação 003.DG-3, forma legítima) + 3 reais sem skip (UFGD-v7 105 pares, literais `13.1 Advogado`/`13.106 Terapeuta Ocupacional`; HUMAP 140 pares todos `""`; Cjr 1 par `""`), fixtures reusadas de `test_extracao_pgr.py`. Suíte 853+4 → **861+4** (+8 exato); `mypy --strict agente_medico/motor/` zero erros, delta-zero; falha explícita via stash (`ImportError` na coleta). Revisão do Arquiteto sobre git objects: aprovada sem correção; 1 observação cosmética (`CAMINHO_PGR_CJR` duplicado como literal em vez de importado — nota, não reabre). Resta **4c-iii** (cliente real + prompt-card + sonda ao vivo — molde 003.BO/CA) e **4d** (split de roteamento + plug `preparar_ghes` + e2e EBSERH, que FECHA DT-003CS-01). Nenhuma R-* criada/alterada. `[IMPLEMENTADO — 003.DI; PR #231]`

**Andamento (003.DJ) — fatia 4c-iii IMPLEMENTADA e mergeada: cliente Gemini real do transcritor-card.** PR #233 (`d50769f`, main `6c04a51`). `TranscritorGeminiCard` em `adaptadores/transcritor_gemini_card.py` novo (molde `transcritor_gemini_pgr`/`_topo`, fora do motor — D-ARQ-09): reuso intra-pacote da cascata (`_obter_chave`/`_chamar_gemini`/`TranscricaoIndisponivel`) E de `_parsear_ghe` do adaptador GHE-PGR (mesma forma JSON `{nome,cargos,riscos}` — saída é reuso ESTRITO de `GHEVerbatim` por 003.DG-1; duplicar o parser seria o mesmo código reescrito). `_PROMPT_CARD` dedicado (003.DG-2), calibrado em PASSO 0 de medição com literais reais (nenhum exemplo inventado — molde 003.BO): nome = lotação da linha-SEGUINTE-à-âncora de labels (`Setor Jurídico 40hs/ semana 2 – Efetivos` → `Setor Jurídico`); cargo = título sem prefixo numérico (`13.1 Advogado` → `Advogado`, sem aritmética — restrição 003.DH) ou, com título vazio, embutido pós-dois-pontos no corpo (`SetorJurídico: ADVOGADO…` → `ADVOGADO`, HUMAP); desglue bounded do space-collapse (D-ARQ-50 P2); categoria/nível/tipo-de-exposição/vias descartados como ruído (003.DG-1); card todo-N/A → `riscos=[]` legítimo (003.DG-3). Testes: 7 mockados (molde `test_transcritor_gemini_pgr`, cascata não re-testada) + 2 ao vivo `requer_api`+`requer_pdfs` (UFGD card[0] `cargos==("Advogado",)`; HUMAP card[0] `cargos==("ADVOGADO",)`). Revisão do Arquiteto pré-merge: 1 correção formulada e aplicada por amend (`363a78b`→`d50769f`) — gabarito do teste ao vivo HUMAP estava fraco (não-vazio em vez do literal medido), endurecido na classe do gate-fraco de 003.DH. Sonda ao vivo (host, chave real): 1ª rodada VERDE 2/2 em 167s — nenhuma correção de prompt (contraste com 003.BO, cuja 1ª rodada reprovou). Suíte 861+4 → 868+6 (+7 passed; +2 skip sem chave); mypy --strict delta-zero. Resta a 4d. `[IMPLEMENTADO — 003.DJ; PR #233]`

**Andamento (003.DK) — fatia 4d IMPLEMENTADA e mergeada; peça 4 COMPLETA; DT-003CS-01 FECHA.** PR #235 (`842ae5e`, main `a249ea5`). Split de roteamento: `avaliar_estrutura -> tuple[Rota, Pendencia | None]` com precedência âncora-GHE > âncora-card (`eh_ancora_card_cargo`) > sinal-de-família > fallback `avaliar_segmentacao` (3º ramo = pré-4d na íntegra — correção de bloqueador: sem o fallback, doc âncora-zero como o EBSERH legado GHES sairia silencioso, D-ARQ-22/31/35; witness real commitado). Gate de spans generalizado (`_avaliar_spans`, âncora e substantivo do motivo parametrizados; lado GHE byte-idêntico; limiares INTOCADOS). Plug: `preparar_ghes`/`processar_arquivo_pgr` ganham `cliente_card` injetável; rota card = recorte + recuperação de títulos + `transcrever_cards` + `gate_forma_ghe`. Medição final: UFGD-v7 INGERE (`("card", None)`, e2e 105 pares, 1º título `13.1 Advogado`, pendências vazias); HUMAP GATED por densidade — 2º bloqueador da sessão: cauda de assinatura de 183/368 págs. (49,7%) infla o último span, mesma classe 003.DD-2, 2ª testemunha (lado card) → promovida a **DT-003DK-01**; Cjr GATED por contagem (V2/003.DC confirmado); demais 14 do acervo inalterados; Bertoncini ausente do disco `[INCERTO]`. Suíte 868+6→877+6 (+9); mypy delta-zero; falha explícita via stash. Nenhuma R-* criada/alterada. `[IMPLEMENTADO — 003.DK; PR #235; FECHA DT-003CS-01]`

*Anatomia medida do card.* `[NN.N NomeDoCargo]` → `[DADOS GERAIS]` → `[Lotação: … labels]` → `[linha de valores]` → `DESCRIÇÃO SUMÁRIA DAS ATRIBUIÇÕES` → `EQUIPAMENTOS DE TRABALHO` → `RISCOS AMBIENTAIS` (tabela 5 categorias × {fator de risco, fonte geradora, vias de transmissão, categoria/nível, tipo de exposição}) → `EPI EXISTENTES` → `EPC EXISTENTES` → `RECOMENDAÇÕES PARA MEDIDAS DE CONTROLE` → `[nº pág.]`. Quatro achados de forma: (1) a linha-âncora é de LABELS PUROS (`Lotação: Escala de Trabalho: Qtde:`) — o setor vem da linha SEGUINTE, logo `nome` NÃO pode vir "da linha-âncora" como reza o docstring de `GHEVerbatim` (reuso cego do prompt-GHE transcreveria o cabeçalho da tabela como nome do setor); (2) **o nome do cargo está FORA do span no UFGD** — como a âncora da 4b é a `Lotação:`-tripla, o título `NN.N Cargo` de cada card cai na CAUDA do card ANTERIOR; o HUMAP é auto-suficiente (cargo embutido na linha de valores, `UnidadedeClínicaCirúrgica:MÉDICO–ANESTESIOLOGIA`); (3) space-collapse integral no HUMAP (`Produtosquímicos`, `EscaladeTrabalho`) + tabelas rotacionadas extraídas ESPELHADAS no anexo de radioproteção (`ocisíF`, `edadilibitudorpeR`) — hazard de transcrição; (4) `quantificacao` é `""` em 100% dos riscos dos dois witnesses (nenhum dB/ppm) e a ordem de colunas da tabela de risco DIVERGE entre UFGD e HUMAP.

*Medição de confirmação (n=105+140).* H1 (título dentro do corpo) e H2 (título recuperável da cauda) mediram 5 e 97/104 na 1ª rodada — os 7 "furos" da H2 são ARTEFATO da própria regex de medição (`\d{1,2}` no sufixo não casa os títulos `13.100`–`13.106`, de 3 dígitos; as caudas exibidas continham o par corretamente). Corrigido o cap: **recuperação = 104/104 caudas** + card [0] recuperável do texto PRÉ-ÂNCORA (`13.1 Advogado / DADOS GERAIS`, descartado pelo recorte por construção) → cobre os **105/105**. H1=5 é REAL e informativo: em 5 cards o título fica mais fundo que 6 linhas do fim → a recuperação deve varrer o VÃO INTEIRO entre âncoras, nunca janela fixa. HUMAP: **140/140 com cargo presente** (os 2 classificados como "sem" — cards [41] e [127] — trazem o cargo em linha PRÓPRIA, `FARMACÊUTICO 1-CPC`, não colado à lotação: layout varia, cargo nunca falta). Veredito: anatomia REGULAR.

*Decisão 003.DG-1 (tipo de saída = reuso ESTRITO de `GHEVerbatim`).* O card oferece por risco fator (→`agente`) e fonte geradora (→`fonte_geradora`); categoria (`FÍSICO`…), nível (`3 Crítica`), tipo de exposição (`Permanente`/`Intermitente`/`Eventual`) e vias de transmissão NÃO têm casa em `RiscoVerbatim`. Achado que inverteu a inclinação preliminar da sessão: `hidratar_ghe` já emite `tipo=""` e `severidade=None` HARDCODED — esses dois já são placeholder no caminho Viverde, então descartar é PARIDADE, não regressão; e estender o tipo os faria morrer uma camada depois, no `hidratar_ghe` que 003.DC congelou — campo de consumo-zero, exatamente o que 003.BW rejeitou. `quantificacao=""` é aceito (o gate não exige quantificação). **Dívida candidata nomeada** (sem DT formal): `tipo de exposição` e o nível `3 Crítica` têm peso clínico plausível para periodicidade — é deferimento COM peso, não descarte trivial; eventual consumo exige campo novo E consumidor a jusante na MESMA fatia.

*Decisão 003.DG-2 (prompt-card DEDICADO, não reuso do prompt-GHE).* Quatro razões MEDIDAS, não intuição: `nome` vem da linha-seguinte-à-âncora; cargo embutido (HUMAP) ou recuperado do preâmbulo (UFGD); space-collapse exige desglue (normalização bounded, D-ARQ-50 P2); ordem de colunas divergente entre os dois docs. Fecha o furo V3 de 003.DC (reuso do transcritor-GHE assumido em silêncio).

*Decisão 003.DG-3 (`gate_forma_ghe` REUSADO sem alteração).* Os requisitos do gate (`nome` não-vazio; todo risco com `agente` não-vazio) são satisfeitos pelo card, e `quantificacao` vazia não é critério. Observação (NÃO buraco — reclassificada na 2ª passada): card todo-`N/A` → `riscos=()` → gate APROVA (`all()` sobre vazio é `True`); num cargo administrativo, GHE sem risco ocupacional é forma clinicamente legítima.

*Decisão 003.DG-4 (rota-de-recuperação do cargo na 4c; 4b INTACTA).* O preâmbulo `NN.N Cargo` + `DADOS GERAIS` é recuperado do TEXTO DE PÁGINA CHEIO (não dos spans), deterministicamente, varrendo o vão entre âncoras; a borda do card [0] cai naturalmente (está no pré-âncora). Alternativa REJEITADA: estender o span para trás na 4b reabriria código já mergeado E reintroduziria a fragilidade a space-collapse do `DADOS GERAIS`-como-âncora que 003.CZ já refutou (105 no doc espaçado, 0 no colado). Não é paliativo: montagem-do-input-de-transcrição é concern da 4c, recorte é da 4b — a camada certa. **Gate pré-IMPL da 4c:** re-medir a recuperação com a regex corrigida (sufixo de 3 dígitos, varredura do vão inteiro) exigindo **105/105 títulos recuperados**; divergência = BLOQUEADOR, parar e reportar.

Ratificado pelo Diovanni. Sem código, sem R-*. PAINEL não re-tirado. `[MEDIDO — pdfplumber host, 003.DG; 2 witnesses + censo 105/140]` `[ARQUITETURA — 003.DG; consome D-ARQ-57 peça 4 / decisão 003.DC]`

**Andamento (sessão branch `claude/dreamy-mayer-os6jce`, número não atribuído, 18-19/09/2026) — ARQUITETURA da peça 5: recorte do grid AIHA (Hetrin/Serra Dourada) via banda de coluna calibrada por bloco, molde D-ARQ-65; fatiamento 5a-5d.** Sessão ARQUITETURA/medição (sem código), pedida pelo usuário ("abre a arquitetura do grid AIHA" → "vamos fechar a AIHA"), consumindo `DT-(sessão claude/youthful-lamport-3kfkog)-02` (`PENDENCIAS_CLINICAS.md`) — o fix do regex fragmentado (PR #338, já em main) restaura o diagnóstico correto (`pgr_cargo_based`), mas nenhum PGR da família grid-AIHA gera matriz hoje: a peça 3/4 sempre tratou o grid como sinal-de-família, nunca como caminho de ingestão.

**Medição desta sessão** `[MEDIDO — pdfplumber, execução direta contra os 3 witnesses reais em matrizes_originais/]`, contra `01. PGR RICCO HETRIN - MAR25.pdf` (396 págs.), `01. PGR RICCO SERRA DOURADA - MAI.24 1.pdf` (272 págs.) e `PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf` (197 págs., o documento do chamado real do Diovanni na DT). A anatomia é 1 tabela ÚNICA contínua por dezenas de páginas — o cabeçalho `Função | Identificação de Perigo/Risco | ...` que a peça 3 reconhece repete em TODA página do intervalo (Hetrin/mar: págs. 63-185, 123 seguidas, zero gap; Serra Dourada: págs. 58-113, 56 seguidas, zero gap), nunca delimitando função — confirma a leitura já registrada na DT ("sinal-de-família ≠ âncora-de-recorte"). `extract_text()` linear (o primitivo de toda a peça 1/3, `linha -> bool`) é inutilizável aqui: um reconhecedor "linha curta = nome de função" sobre o texto linearizado produz fragmentos de sigla de categoria de risco ("A", "Q", "N o"), não nomes — as colunas se intercalam por posição Y. `pdfplumber.extract_tables()` resolve estruturalmente nos 2 witnesses limpos (coluna Função = 1 célula não-vazia por grupo, `None` nas linhas seguintes do mesmo grupo; ~60 funções contadas em Hetrin/mar, padrão idêntico em Serra Dourada), mas é FRÁGIL no witness do chamado real (Hetrin/set-2026): 8-9 tabelas espúrias por página (fragmentos de cabeçalho em coluna estreita), célula de função quebrada palavra-por-linha. ~22 grupos contados ali, com grupos **N:1** (ex.: `ENGENHEIRO CIVIL/ENGENHEIRO RESIDENTE/ESTAGIÁRIO DE ENGENHARIA/APONTADOR/ADMINISTRATIVO DE OBRA/TÉCNICO DE SEGURANÇA` compartilhando 1 grupo de risco); decompondo as barras dá ~28-29 cargos, batendo com o "28/28 cargos" já medido na matriz aprovada desse mesmo documento (achado psicossocial, sessão `claude/youthful-lamport-3kfkog`) — validação cruzada, não coincidência.

**Achado que muda a recomendação da DT.** A DT registrava "molde mais próximo é a extração de linhas de risco do Fascino" como hipótese não testada. Medido: `parser_familia_consciente.py` (D-ARQ-65) não usa `extract_tables()` — usa `pdfplumber.extract_words()` + banda de coluna calibrada POR BLOCO a partir do próprio cabeçalho (`PalavraPDF`, `_localizar_cabecalho_tabela`, `_banda`), porque a medição original de bandas fixas (003.DZ, comentário no próprio módulo) divergiu contra o acervo real — posição de coluna varia por bloco, não é grade rígida. É o MESMO sintoma que quebrou `extract_tables()` no Hetrin/set (coluna sem grade estável). Esse módulo já resolve, para outra família, o sub-problema estrutural do grid-AIHA: `_separar_cargos_da_celula`/`_extrair_cargos_da_linha` já decompõem célula com múltiplos cargos compartilhando 1 grupo de risco em `GHEVerbatim(cargos=[...])` — o caso N:1 medido acima. Conclusão: `extract_tables()` funciona nos 2 witnesses limpos, mas não é o caminho recomendado — o próprio histórico do projeto já testou e abandonou detecção automática de tabela por exatamente esta classe de instabilidade de coluna.

**Decisão — módulo irmão a `parser_familia_consciente.py`, mesma classe de primitivo (`PalavraPDF` + banda por bloco), schema de coluna próprio; fatiamento 4 peças.**

*5a — banda de coluna calibrada por bloco + reconhecedor de fronteira de função.* Fronteira testada: "1ª célula da coluna Função não-vazia E diferente do último nome aberto" — funciona nos 2 witnesses limpos; continuidade entre páginas de `CONTINUAÇÃO` resolve comparando contra o último nome aberto, não contra a página anterior isolada. Medido e testado só contra Hetrin/mar e Serra Dourada — os 2 limpos primeiro, molde da peça 4 (Cjr/UFGD antes do caso difícil).

*5b — decomposição N:1* (reuso/generalização de `_separar_cargos_da_celula`). Só entra depois de 5a sólido: é o caso mais instável (Hetrin/set), não o âncora de calibração.

*5c — parsing da célula "Identificação de Perigo/Risco"* (itens `- ...`) → `RiscoVerbatim`, mesma forma-alvo de toda rota determinística (D-ARQ-49/50).

*5d — roteamento* em `avaliar_estrutura`/`avaliar_familia` (`pgr_cargo_based` bloqueante vira ingestão real quando a família casa) + plug em `preparar_ghes` + e2e contra os 3 PDFs reais. Só aqui a DT fecha.

**Risco nomeado, não escondido.** Hetrin/set-2026 — o witness do chamado real — é o mais instável dos 3 (coluna sem grade, N:1) e só é destravado nas fatias 5b/5d, não na 5a. Se a prioridade real é esse documento específico, a ordem exige decisão do Arquiteto/Diovanni antes de iniciar a IMPL — não assumida aqui.

**Fronteiras.** D-ARQ-57 peça 3 (`eh_sinal_cargo`, reconhecedor de família) e D-ARQ-65/Fascino permanecem intocados — esta decisão só dá caminho de ingestão ao que hoje é só diagnóstico. Não cria nem altera regra clínica (nenhuma `R-*` tocada). Não fecha `DT-(sessão claude/youthful-lamport-3kfkog)-02` — fecha só na fatia 5d.

**Base.** Sessão (branch `claude/dreamy-mayer-os6jce`, número não atribuído), 18-19/09/2026. Medição própria desta sessão contra os 3 PDFs reais trackeados em `matrizes_originais/`, sem reusar números de sessões anteriores. Escrita nos docs vivos autorizada pelo usuário desta sessão ("pode gravar"); ratificação formal do Diovanni não registrada neste turno — decisão fica sinalizada como ARQUITETURA proposta, não fechada, até essa confirmação chegar por outro canal. Sem código, sem R-*. PAINEL não re-tirado (nenhum número clínico se move). `[ARQUITETURA — consome DT-(sessão claude/youthful-lamport-3kfkog)-02; D-ARQ-57 peça 3/4; D-ARQ-65]`

**Ratificação (sessão branch `claude/blissful-knuth-riqucz`, número não atribuído, 19/09/2026).** Diovanni ratifica o fatiamento 5a→5b→5c→5d acima como desenhado — sem reordenar para priorizar o witness Hetrin/set-2026 (o documento do chamado real) antes de 5a estar calibrado nos 2 witnesses limpos. O risco nomeado na nota acima (Hetrin/set-2026 só é destravado nas fatias 5b/5d, não na 5a) fica aceito, não mitigado por reordenação — decisão explícita, não omissão. D-ARQ-57 peça 5 passa de ARQUITETURA proposta para **ARQUITETURA ratificada**, liberada para IMPL a partir de 5a. Sem código nesta sessão; nenhuma cláusula de D-ARQ alterada, nenhuma D-ARQ nova. `[RATIFICADO — Diovanni; sessão branch claude/blissful-knuth-riqucz]`

**Fatia 5a IMPLEMENTADA (mesma sessão, mesmo dia) — a hipótese de ambiguidade da nota de ARQUITETURA acima estava incompleta; corrigida por medição, não por decisão.** `agente_medico/motor/parser_familia_grid_aiha.py` (módulo irmão a `parser_familia_consciente.py`, D-ARQ-65) implementa banda de coluna calibrada por PÁGINA (não por bloco GHE — o cabeçalho do grid repete em toda página) + reconhecedor de fronteira de função. Medição desta sessão contra os 2 witnesses limpos achou DOIS problemas na anatomia que a sessão de ARQUITETURA não tinha medido:

1. **O rótulo da função pode compartilhar o mesmo `top` de palavras de OUTRAS colunas** (medido Hetrin/mar pág. 64: "Administrativo de Obra" no mesmo `top` de "Cutânea"/"Vestimenta de trabalho (H)", colunas Meio de Propagação/Eliminação) — um reconhecedor que agrupa a página inteira em linha ANTES de separar por coluna perde esse rótulo (tratou um fragmento de descrição, "serviços administrativos,", como se fosse nome de função nova). Corrigido separando as palavras em duas correntes (banda Função vs. resto) ANTES de agrupar em linha.
2. **O nome pode quebrar em mais de uma linha física** (medido: "Técnico de Segurança do" + "Trabalho", Serra Dourada) — a fronteira título/descrição é a QUEBRA DE ESPAÇAMENTO vertical (linhas do mesmo parágrafo distam ~7.4-7.6pt; a quebra nome→descrição distam ~14.9-15.0pt, medido em 12 ocorrências, 2 witnesses, 100% consistente), não "1 linha só".

**Corrigidos os dois, a "ambiguidade" que motivou a decisão de marcar pendência (nota de ratificação acima) desaparece**: com a separação por coluna, cada página resolve exatamente 1 nome (repetição = continuação, nome novo = fecha o grupo anterior e abre um novo), e TODAS as linhas de resto da página — inclusive as que aparecem antes do rótulo, sempre presentes, 2 a 6 por página — pertencem à função que a página resolve. Não sobra pendência: era artefato do bug (1), não estrutura real do documento. `TrechoAmbiguo`/`Pendencia` desenhados na ratificação NÃO entraram no código — campo sem consumidor teria sido D-ARQ-DG-1.

**Validação.** Núcleo puro: 7 testes sintéticos, reversão nomeada 7/7 confirmada (varredura inversa desta sessão). Integração contra os 2 PDFs reais: nomes e contagens de linha exatas batendo (Hetrin/mar "Administrativo de Obra"=95, "Almoxarife"=111; Serra Dourada "Encarregado de Obra"=101, "Pedreiro"=118, "Técnico de Segurança do Trabalho"=101). Confirmação cruzada com instrumento independente: 41 funções medidas em Hetrin/mar págs. 63-142 (80 de ~123 páginas) extrapola pra ~63 no documento inteiro — mesma ordem de grandeza do "~60 funções" que `extract_tables()` já tinha medido nesta mesma D-ARQ; Serra Dourada págs. 58-113 (56 páginas) fecha em exatos 28 grupos, sem sobra (56/28=2, confirma "1 função = 1 nova + 1 CONTINUAÇÃO" no witness inteiro, não só na amostra). `mypy --strict` alvo canônico: limpo, **49 arquivos** (+1). Suíte nova: 13 testes, todos passando (`agente_medico/tests/test_parser_familia_grid_aiha.py`); recorte que cobre os derivados tocados (nenhum outro módulo importa este ainda — escopo exato, não zero).

**Escopo.** Só 5a (banda + fronteira + nome + linhas cruas por grupo). Decomposição N:1 (5b, caso do witness instável Hetrin/set-2026), parsing da célula "Identificação de Perigo/Risco" em RiscoVerbatim (5c) e roteamento/plug em `preparar_ghes` (5d, onde `DT-(sessão claude/youthful-lamport-3kfkog)-02` fecha) seguem fatias futuras, ordem 5a→5b→5c→5d inalterada (ratificação acima). Sem `R-*` criada/alterada/depreciada; PROTOCOLO inalterado. `[IMPLEMENTADO — sessão branch claude/blissful-knuth-riqucz; consome a ratificação acima]`

**Bloqueador medido ao abrir a fatia 5b (sessão branch `claude/nice-ptolemy-wxk1wo`) — a premissa "decomposição N:1" não tem alvo real acessível pela 5a; reportado, não ajustado.** Antes de escrever código, esta sessão mediu contra os 2 witnesses calibrados (`segmentar_arquivo` real, D-ARQ-57 fatia 5a, intervalo cheio): Hetrin/mar (págs. 63-185) devolve **63 grupos**, dos quais **3** têm `/` no nome (`'Encarregado de Encanador/Hidráulica'` págs. 81-82, `'Comprador / Compradora'` págs. 130-131, `'Engenheiro Civil / Planejamento'` págs. 142-143); Serra Dourada (págs. 58-113) devolve **28 grupos**, **0** com `/`. Nenhum dos 3 candidatos é o N:1 que motivou a fatia (lista de cargos DISTINTOS compartilhando 1 grupo de risco, molde do exemplo da ARQUITETURA — "ENGENHEIRO CIVIL/ENGENHEIRO RESIDENTE/ESTAGIÁRIO DE ENGENHARIA/APONTADOR/..."): o texto cru sob cada título descreve **1 papel só** — `'Comprador / Compradora'` é par de gênero gramatical (masc./fem. do mesmo cargo, "Recebe requisições de compras, executa processo de cotação..."); `'Engenheiro Civil / Planejamento'` e `'Encarregado de Encanador/Hidráulica'` são título composto de 1 cargo só (a descrição sob cada um cobre as duas metades do nome como 1 atribuição, não 2 cargos com riscos próprios). Decompor qualquer um dos 3 por `/` produziria GHE fantasma sem risco próprio (ex.: "Compradora" como grupo à parte) — dado clinicamente errado, não fidelidade a mais forma.

**O N:1 real só existe no witness que a 5a não alcança.** `segmentar_arquivo` contra `PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf` (197 págs., o documento do chamado real) levanta `GrupoFuncaoNaoReconhecido` em qualquer página do intervalo do grid (medido págs. 11-36, 0-indexed — `page.find_tables()` devolve 8 a 10 tabelas por página nesse intervalo, batendo com "8-9 tabelas espúrias por página" já registrado na ARQUITETURA). Causa raiz medida: `_localizar_cabecalho_grid` (`parser_familia_grid_aiha.py`) exige `p.text == "Função"` e `p.text == "Tipo"` (title-case, calibrado nos 2 witnesses limpos); o grid deste documento usa cabeçalho em CAIXA ALTA — pág. 14 (0-indexed), palavra `'FUNÇÃO'` em top=132.2/x0=60.2 e `'TIPO'` em top=128.6/x0=100.6, nunca `'Função'`/`'Tipo'` — varredura das 197 páginas por `p.text == "Função"` exato acha só a pág. 62 (tabela de EPI-por-função, tabela diferente, sem relação com o grid de risco). O cabeçalho também carrega 2 rótulos ausentes nos 2 witnesses limpos (`'AVALIAÇÃO'`/`'DE'`/`'RISCO'` como linha de seção; `'CÓDIGO'`/`'eSocial'`) e a ordem das colunas trocada — mesmo conjunto de conceitos (tipo de risco, identificação de perigo/risco, tempo de exposição, meio de propagação/eliminação, nível de risco, probabilidade, efeito, classificação, controle existente, código e-Social), forma de cabeçalho distinta — consistente com ser a MESMA família (grid AIHA) em revisão de template posterior (14/09/26), não uma família nova.

**Conclusão — decisão do Arquiteto, não ajustada para bater.** A fatia 5b, como ratificada ("decomposição N:1... reuso/generalização de `_separar_cargos_da_celula`... caso mais instável (Hetrin/set), não o âncora de calibração"), presumia que o witness instável ficaria alcançável para gerar o caso real assim que a decomposição existisse. Medido: o bloqueio é anterior — nem o cabeçalho localiza, então nenhuma decomposição tem dado real para verificar (cláusula de verificação do `CLAUDE.md`: teste cuja reversão não é nomeável contra dado real não entra — não há hoje um `nome` N:1 genuíno alcançável para nomear essa reversão). Escrever decomposição calibrada em zero casos reais repetiria a classe já registrada em `DH-003EK` (teste especificado que não toca o comportamento que diz cobrir). Bloqueador reportado, sem código nesta sessão além desta medição; decisão de como prosseguir (generalizar `_localizar_cabecalho_grid` para a forma CAIXA-ALTA antes de decompor N:1; redefinir 5b como sem alvo dentro dos 2 witnesses calibrados e adiar decomposição para quando o cabeçalho Hetrin/set for coberto; ou outra ordem) cabe ao Arquiteto. `DT-(sessão claude/youthful-lamport-3kfkog)-02` segue ABERTA — nota espelhada em `PENDENCIAS_CLINICAS.md`. Nenhuma cláusula de D-ARQ alterada, nenhuma D-ARQ nova; nenhuma `R-*` tocada; PROTOCOLO inalterado. `[MEDIDO — pdfplumber host, sessão claude/nice-ptolemy-wxk1wo, contra os 3 witnesses reais em matrizes_originais/; ARQUITETURA/bloqueador, sem código de produção]`

### DT-003CS-01 — Forma EBSERH vigente é card cargo-based (`Lotação:`-tripla); fix na peça 3, GHES aposentado — saúde `[FECHADA — 003.DK]`

**Contexto.** 1ª medição out-of-sample de D-ARQ-57 (003.CS) sobre PGR real de saúde: HU-UFGD (template EBSERH, padrão de todos os Hospitais Universitários federais). Documento GHE-conceitual, bem-formado e recortável — ~23 blocos `GRUPO HOMOGÊNEO DE EXPOSIÇÃO SIMILAR (GHES)`, segmentados por `Unidade / Setor <nome>` (~40 seções), cada bloco com tabela de risco e linhas por `Cargo/Função`. A âncora atual (`^(INVENTÁRIO DE RISCO )?GHE:? \d+...`) exige numeração; o cabeçalho EBSERH é textual sem número → 0 âncoras → `avaliar_segmentacao` emite `segmentacao_implausivel` (bloqueio correto, mas por ausência de cobertura, não por doc defeituoso).

**O que a medição já deu.** Forma nova de cabeçalho GHE (EBSERH/GHES), witness real, gabarito aproximado (~23 GHES / ~40 Unidade-Setor no HU-UFGD). `[MEDIDO — pdfplumber host, 003.CS]`

**Critério de resolução (antes de implementar).** (1) Censo formal molde DT-003CM-01: confirmar que a forma EBSERH é padrão (**n≥3 HUs**, não generalizar de n=1); (2) decidir a **unidade de recorte** — `Unidade / Setor` (bloco externo) vs. `GHES`-por-setor (medir cardinalidade 1:1 ou 1:N); (3) reconhecedor puro `linha -> bool` do cabeçalho EBSERH somado ao `_RECONHECEDORES_GHE` em disjunção (mesmo mecanismo da peça 1). Fatia IMPL futura sob D-ARQ-57; "uma coisa por vez" — não empilhar com recorte-por-cargo (DT-003L-01 forma 6).

**Prioridade (recomendação do Arquiteto).** Alta em universalidade: EBSERH cobre toda a rede federal de HUs → resolve uma fatia grande do setor saúde de uma vez. `[DERIVADO — medição 003.CS; consome mecanismo D-ARQ-57 peça 1]`

**Reenquadramento (003.CZ) — a premissa GHE (peça 1) está refutada; o fix é peça 3.** O texto do critério acima presumia forma-GHE (extensão de âncora GHE). A medição n=3 da 003.CZ mostra que o EBSERH **vigente** é card cargo-based (`Lotação:`-tripla), não GHE — o item original só descrevia o doc **legado** (n=1). Reencaminhamento: (1) o reconhecedor entra em `_RECONHECEDORES_CARGO` (peça 3), roteando EBSERH-atual a `pgr_cargo_based` bloqueante — não uma âncora nova na peça 1; (2) "confirmar n≥3" SATISFEITO no nível-forma (template corporativo `PGR.SOST.001` v7.0, 2 HUs convergentes + evidência de padronização); (3) "unidade de recorte" resolve-se no **recorte-por-cargo** (DT-003L-01 forma 6), não aqui. GHES/`ANÁLISE NN` **aposentado** (não cobrir sem reaparição fora do doc legado). A DT permanece **ABERTA** porque reconhecer+sinalizar é diagnóstico, **não ingestão**: EBSERH só entra em produção quando o recorte-por-cargo existir — palativo explícito, aceito pelo Diovanni. Sucessão de trabalho: fatia IMPL "reconhecedor `Lotação:` na peça 3" (curta) → recorte-por-cargo (fatia grande, abre o setor saúde). `[MEDIDO — pdfplumber host, 003.CZ; 3 PGRs EBSERH públicos]`

**Nota (003.DC) — o recorte-por-cargo que fecha esta DT é a peça 4 (fatia 4d).** A ARQUITETURA da peça 4 (D-ARQ-57 andamento 003.DC) desenhou o recorte 1:1 (`recortar_cards_cargo` + `_RECORTADORES_CARGO` com a Lotação-tripla que 003.DA já adicionou como sinal-de-família). EBSERH-vigente entra em produção — e esta DT **FECHA** — na fatia **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH), não antes; até lá segue reconhecer+sinalizar (`pgr_cargo_based`). Sequência: 4a (fork N:1, peça 1) → 4b (`recortar_cards_cargo` isolado) → 4c (transcrição do card) → 4d (plug, fecha esta DT). `[ARQUITETURA — 003.DC]`

**Nota (003.DB) — anatomia medida; o EBSERH-vigente confirma 1:1.** A medição da 003.DB (DT-003DB-01) confirma a forma card EBSERH como **1:1** (UFGD 105 / HUMAP 140 cards, `RISCOS AMBIENTAIS` própria por card) e situa o recorte EBSERH no mesmo maquinário 1:1 do Cjr (Sistema ESO). O critério (2) desta DT ("unidade de recorte") está medido: card = 1 cargo : 1 tabela, âncora `Lotação:`-tripla, tabela ligada por posição dentro do bloco. A DT segue **ABERTA** — reconhecer+sinalizar é diagnóstico, não ingestão: EBSERH só entra em produção quando o recorte-por-cargo existir (arquitetura da peça 4 na 003.DC).

**Nota (003.DD) — fatia 4a FECHADA; esta DT segue ABERTA (fecha na 4d).** A fatia 4a (fork N:1 do Ricco-Adm, forma 5 do repertório GHE) foi implementada e mergeada (PR #222) — mas é ortogonal ao EBSERH-vigente (que é 1:1, não N:1). O critério de fechamento desta DT continua sendo a fatia **4d** (split de roteamento + plug `preparar_ghes` + e2e EBSERH), que depende de 4b (`recortar_cards_cargo` isolado) e 4c (transcrição do card), ainda não implementadas. `[IMPLEMENTADO — 003.DD; PR #222; não fecha esta DT]`

**Nota (003.DF) — fatia 4b FECHADA; esta DT segue ABERTA (fecha na 4d).** `recortar_cards_cargo` isolado (PR #226) — o EBSERH-vigente (1:1, UFGD/HUMAP) agora TEM recorte funcional (gabarito 105/140 exato), mas construído-sem-plugar: nenhum roteamento, nenhuma transcrição, nenhum plug em `preparar_ghes` ainda. Resta **4c** (transcrição do card — gabarito de forma 1 UFGD + 1 HUMAP, prompt-reuso vs. prompt-card, `gate_forma`) e **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — só aqui esta DT FECHA). `[IMPLEMENTADO — 003.DF; PR #226; não fecha esta DT]`

**Nota (003.DG) — fatia 4c ESPECIFICADA (ARQUITETURA); esta DT segue ABERTA (fecha na 4d).** Gabarito de forma do card medido em 2 witnesses ricos e 4 decisões ratificadas: reuso ESTRITO de `GHEVerbatim` (003.DG-1), prompt-card dedicado (003.DG-2), `gate_forma_ghe` sem alteração (003.DG-3), rota-de-recuperação do cargo com 4b intacta (003.DG-4). Achado estrutural: no UFGD o nome do cargo está FORA do span do card (a âncora `Lotação:`-tripla começa DEPOIS do título `NN.N Cargo`, que cai na cauda do card anterior) — recuperável **105/105** do texto cheio (104 caudas + card [0] do pré-âncora), confirmado por medição. Resta a IMPL da 4c (transcritor-card dedicado + recuperação de preâmbulo; gate 105/105 pré-merge) e a **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — só ali esta DT FECHA). `[ARQUITETURA — 003.DG; sem código; não fecha esta DT]`

**Nota (003.DH) — fatia 4c-i FECHADA; esta DT segue ABERTA (fecha na 4d).** `recuperar_titulos_cargo` mergeado (PR #229): a rota-de-recuperação decidida em 003.DG-4 existe em produção e o EBSERH-UFGD tem o nome do cargo recuperável 105/105, com `recortar_cards_cargo` intacto. Construído-sem-plugar: nenhum roteamento, nenhuma transcrição, nenhum plug. Resta **4c-ii** (contrato de transcrição, LLM mockado), **4c-iii** (cliente real + prompt-card) e **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — só ali esta DT FECHA). `[IMPLEMENTADO — 003.DH; PR #229; não fecha esta DT]`

**Nota (003.DI) — fatia 4c-ii FECHADA; esta DT segue ABERTA (fecha na 4d).** Contrato `TranscritorCard` + `transcrever_cards` mergeados (PR #231), LLM mockado (molde 003.BN), `gate_forma_ghe` reusado sem alteração (003.DG-3). Construído-sem-plugar: nenhum cliente real, nenhum roteamento, nenhum plug. Resta **4c-iii** (cliente real + prompt-card) e **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — só ali esta DT FECHA). `[IMPLEMENTADO — 003.DI; PR #231; não fecha esta DT]`

**Nota (003.DJ) — fatia 4c-iii FECHADA; esta DT segue ABERTA (fecha na 4d).** Cliente real `TranscritorGeminiCard` + prompt-card dedicado mergeados (PR #233), validados ao vivo contra UFGD e HUMAP (2/2 na 1ª rodada). A fatia 4c está COMPLETA (i recuperação + ii contrato + iii cliente real). Construído-sem-plugar: nenhum roteamento, nenhum plug. Resta **4d** (split de roteamento em `avaliar_estrutura` + plug `preparar_ghes` + e2e EBSERH — só ali esta DT FECHA). `[IMPLEMENTADO — 003.DJ; PR #233; não fecha esta DT]`

**Nota (003.DK) — FECHADA.** Fatia 4d mergeada (PR #235): EBSERH-vigente entra em produção pela rota card — roteamento em `avaliar_estrutura`, plug em `preparar_ghes`, e2e UFGD ingerindo fim-a-fim (105 cards). HUMAP fica GATED by design (densidade inflada pela cauda de assinatura — classe 003.DD-2, ver DT-003DK-01): bloqueio de plausibilidade para revisão humana, não furo de cobertura — o mecanismo (rota + recorte 140/140 + transcrição validada ao vivo em 003.DJ) está completo. `[IMPLEMENTADO — 003.DK; PR #235]`

**Andamento (sessão atual, branch `claude/fervent-brown-7dcc0y`, 17/09/2026) — refino do sinal-de-família do grid AIHA (peça 3); recorte-por-cargo do grid segue FORA de escopo.** A revisão de 14/09/2026 do PGR Hetrin (mesmo cliente/obra do witness-âncora de 003.CQ) mudou o wrap de coluna do cabeçalho do grid: `_reconhece_funcao_grid_perigo_risco` (linha única, Título-Caso) parou de casar — "Função"/"Perigo"/"Risco" saem fragmentados em duas linhas físicas adjacentes, em caixa alta, intercaladas com palavras de outras colunas (`"FUNÇÃO (quando MEIO DE"` / `"RISCO PERIGO/ RISCO TEMPO DE..."`). Sem sinal-cargo algum, `avaliar_familia` devolvia `None` e o documento caía no fallback `avaliar_segmentacao`, saindo com a pendência **errada** (`segmentacao_implausivel`, sugere doc anômalo) em vez da correta (`pgr_cargo_based`, família já reconhecida — `[MEDIDO — reprodução direta desta sessão contra o PDF real]`).

**Achado que precedeu o código: o grid AIHA nunca teve caminho de ingestão, nem antes desta regressão.** Rodado `avaliar_estrutura`/`parsear_arquivo` contra os dois PGRs Hetrin reais (mar/2025 e set/2026): o de março **também bloqueia hoje**, via `pgr_cargo_based` (123 linhas casam o regex original) — ninguém tinha testado o pipeline fim-a-fim em produção, só o regex isolado. `parser_familia_consciente.py` (D-ARQ-65) é o parser da família **Consciente/Fascino** (cabeçalho `GRUPO/PERIGO-ASPECTO/FONTE/AGRAVO`), inteiramente distinto do grid AIHA — confundir os dois nomes foi o erro de leitura do handoff anterior (`PENDENCIAS_CLINICAS.md`, DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-02, reenquadrada nesta sessão). O recorte-por-cargo da peça 4 (`_RECORTADORES_CARGO`) exclui o grid AIHA **por decisão** (003.DC/003.DF: "sinal-de-família ≠ âncora-de-recorte... o grid AIHA não delimita card individual") — continua excluído; esta sessão NÃO reabre essa decisão.

**Fix, escopo contido (autorizado pelo Diovanni: só o regex, não a arquitetura de ingestão).** `_reconhece_funcao_grid_perigo_risco_fragmentado(linha_a, linha_b)` novo em `extracao_pgr.py`: casa "Função"/"Perigo"/"Risco" (`\b`-delimitado, case-insensitive) no PAR de linhas adjacentes concatenadas, em vez de uma linha só — `\b` evita falso-positivo em prosa no plural ("perigos e riscos", presente no próprio PGR fora da tabela). Integrado em `avaliar_familia` como soma adicional a `n_sinais_cargo` (não altera `eh_sinal_cargo`/`_RECONHECEDORES_CARGO`, cujo contrato é linha única — os outros 3 reconhecedores da peça 3 ficam intocados). Validado por varredura contra os **40 PGRs reais** trackeados em `matrizes_originais/` (script ad-hoc, não commitado — resultado registrado aqui): a classificação de `avaliar_familia` muda em **exatamente 1** documento (o Hetrin de 14/09/2026, `None`→`pgr_cargo_based`); os outros 39 — incluindo as 3 famílias cargo-based já reconhecidas por outro recorte (Cjr, EBSERH UFGD/HUMAP) e todas as famílias GHE-based — ficam bytewise inalterados. 15 testes novos com reversão nomeada (varredura inversa 15/15 confirmada, incluindo 2 testes reais contra o PDF do Hetrin 14/09/2026 e 1 de não-regressão contra o de março/2025). `mypy --strict` alvo canônico limpo, 48 arquivos, delta-zero. **Não gera matriz** — o documento segue bloqueado para revisão humana, com a pendência correta agora. `[IMPLEMENTADO — sessão atual; DT reenquadrada, não fechada — ver PENDENCIAS_CLINICAS.md]`

### DT-003DK-01 — Sobre-inclusão da cauda do último span infla densidade e gatea documentos legítimos (fronteira-fim) `[ABERTA — 003.DK]`

**Contexto.** `recortar_blocos_ghe` e `recortar_cards_cargo` levam o último bloco/card até o fim do documento por construção (direção segura, D-ARQ-31/35). Cauda não-pertencente (assinaturas, anexos) infla a extensão do último span e dispara o gate de densidade da peça 2. Nomeada como dívida candidata em 003.DD-2; promovida a DT com a 2ª testemunha.

**Testemunhas medidas.** Ricco-Adm (lado GHE, 003.DD: bloco 2 = 10/24 págs., 41,7%) e HUMAP (lado card, 003.DK: 183/368 págs., 49,7% — cauda é bloco de assinatura eletrônica do PGR inteiro, não card).

**Não bloqueia produção.** Documentos gated vão a revisão humana bloqueante — anti-supressão funcionando como projetado; o custo é ingestão automática negada a docs legítimos.

**Critério de resolução.** Correção ESTRUTURAL da fronteira-fim do último span (nunca recalibração de limiar — margem restante 2,7pp, 003.DD; nunca âncora-de-fim de boilerplate n=1 — overfit, classe refutada em 003.CZ). Exige forma de fim-de-conteúdo medida em n≥3 documentos; teste de aceite: Ricco-Adm e HUMAP flipam para ingestão SEM abrir o buraco Vistamérica (cauda gigante genuína continua gated). `[DERIVADO — 003.DD-2 + 003.DK; D-ARQ-22/31/35]`

### DT-003DL-01 — `is_carcinogeno_iarc` e `tem_lt` são campos de vocabulário sem consumidor; premissa de "varrer e popular" refutada `[REENQUADRADA — 003.DP; DEFERIDA]`

**Reenquadramento (003.DP).** A DT nascera pedindo varredura para popular os dois campos com valores corretos (IARC Monographs + NR-15 Anexo 11). A investigação de 003.DP refutou a premissa por três medições de disco/git:

1. **Nenhum consumidor.** `git grep tem_lt -- '*.py'` = vazio (já registrado em HISTORICO 003.Q). `is_carcinogeno_iarc` do vocabulário é carregado em `EntradaIndice` mas NÃO aplicado ao `Componente` (`resolvedor.py:42`, reversão D-ARQ-36 nota 003.V), sob teste vivo (`test_resolvedor.py:143`). O motor lê a flag da transcrição GHS, não do vocabulário.
2. **Legado não lê o vocabulário.** `modules/agente_medico_ia.py`/`agente_medico_nr7.py` usam bancos JSON; nenhuma referência a `agentes.yaml` ou aos campos. "Em produção" na redação original é impreciso: os campos estão versionados, nenhum caminho de produção os consome.
3. **`tem_lt` codifica eixo aposentado.** Era o proxy de "com LT / sem LT" de R-BIO-02 `[DEPRECATED]` (sucedida por R-BIO-04, eixo `tipo_ibe`).

**Decisão 003.DP — zero mudança de dado.** Não popular valores; não normalizar `false`→`null` (churn sem consumidor, e quebraria `test_vocabulario.py:64`, que fixa `acetona`/`acetato_de_etila` = `false`, valores corretos). Enriquecimento deferido à chegada de um consumidor real, conforme precedente DT-002H-01 (append-only, D-ARQ-14).

**Estado medido (003.DP, 56 agentes químicos):** `is_carcinogeno_iarc` 28 false / 6 true / 22 null; `tem_lt` 27 false / 6 true / 23 null.

**Partição de responsabilidade:**
- `is_carcinogeno_iarc` → território de **DT-003CI-01** (GHS≠IARC, fonte única). NÃO tocar aqui. Célula mais perigosa apontada a ela: `arsenio` e `tricloroetileno` gravam `false` sendo IARC Grupo 1 — supressão latente quando a ligação agente→Componente for feita. Insumo para DT-003CI-01, não para esta DT.
- `tem_lt` → sem consumidor; futuro estrutural é **depreciar** (aceitar que presença de LT não volta ao vocabulário) **ou promover a `leo_nr15: {valor, unidade, fonte}`** se o LEO-resolver (D-ARQ-24 nível 3) vier a buscar valores de NR-15 no vocabulário. Decisão gated pela necessidade do resolver — não há gatilho hoje.

**Insumo pronto para o dia do enriquecimento.** A pesquisa normativa de 003.DP (Quadro 1 do Anexo 11 vigente parseado; Anexo 12 lido — asbesto/sílica/manganês com LT próprio; mapeamento IARC vols 1–123 + corroboração por-sítio vols 1–140) está em `docs/referencia/GABARITO_003DP_anexo11-12_iarc.md`. Quando um consumidor forçar o enriquecimento, os valores estão coletados e auditados — não refazer a pesquisa.

**Achado colateral (fora de escopo, para conferência futura):** Anexo 12 item 18 fixa conduta clínica de asbesto (adm/dem/anual + telerradiografia OIT + espirometria; acompanhamento 30 anos pós-contrato escalonado por tempo de exposição). Candidata a R-* própria — conferir se o protocolo já cobre antes de criar ID.

`[REENQUADRADA — 003.DP; substitui o pedido de varredura de 003.DL; herda a natureza deferida de DT-002H-01; is_carcinogeno_iarc partido para DT-003CI-01]`

### DT-003DM-01 — Invariante do raio fuzzy quebrada: o Levenshtein ≤2 não é mais seguro por construção, e siglas curtas o degradam a empate permanente `[FECHADA — 003.DN]`

**Contexto.** A revisão da 003.BP registrou, como fundamento de segurança do fallback fuzzy, que *"nenhum par dos 45 slugs reais dista ≤2 entre si"* — logo nenhum falso-positivo era possível no vocabulário de então. **A propriedade caducou em silêncio.** Medida em `c45759e` (79 slugs), há **4 pares dentro do raio**:

| par | dist |
|---|---|
| `etanol` ↔ `metanol` | 1 |
| `hdi` ↔ `tdi` | 1 |
| `metil_etil_cetona` ↔ `metil_butil_cetona` | 2 |
| `metoxietanol_2` ↔ `butoxietanol_2` | 2 |

Ninguém re-mediu entre 003.BP e 003.DM. A garantia seguiu sendo citada como se valesse.

**Não produz erro silencioso, hoje.** Empate de distância mínima entre slugs distintos cai em `NAO_RESOLVIDO` + `Pendencia(vocabulario_ausente)` — o ramo seguro, D-ARQ-22 respeitado por construção. O efeito é **degradação do tier fuzzy**, não escolha errada. Por isso é dívida, não bug.

**Por que isso bloqueia a Tier 2 (siglas).** Sigla é string curta, e num termo de 3 caracteres o raio 2 cobre quase todo o espaço de 3 letras — `hdi` ↔ `tdi` já ilustra com o vocabulário atual. Popular `dmf`, `dma`, `nmp`, `thf`, `mek`, `mbk` tornaria o tier fuzzy das siglas empate permanente: tecnicamente seguro, praticamente morto, com o índice crescendo sem resolver. Foi a razão de a 003.DM recusar as siglas e fechar só a Tier 1.

**Correção proposta (não implementada, decisão de arquitetura pendente):** piso de comprimento no fuzzy — forma normalizada com ≤4 caracteres resolve só por via exata, sem fallback Levenshtein. Isso é alteração em `resolver_termo`, ou seja **motor**, não dado — por isso não coube numa fatia data-only. Alternativa a considerar: raio proporcional ao comprimento em vez de constante 2.

**Escopo.** Decidir o critério (piso fixo vs. raio proporcional), implementar em `motor/resolvedor_termos.py`, e só então abrir a Tier 2 de aliases. Exige teste que falhe sem a regra: sigla curta typada não deve resolver a sigla vizinha.

**Nota (003.DN) — FECHADA.** Critério decidido: piso fixo (`PISO_FUZZY = 4`), bilateral — forma abaixo do piso não participa do fuzzy nem como busca nem como candidata, resolve só por via exata. `hdi`↔`tdi` (o par que ilustrava o risco) some da lista de colisão porque ambos caem sob o piso; `hdl` digitado não resolve mais `hdi` por FUZZY. Teste exigido pelo escopo desta DT existe (`test_sigla_typada_nao_resolve_vizinha`) mais 3 companheiros (busca-curta-contra-candidata-curta, exata-continua-exata, vigia de pares longos). **O que fica de fora, por design, não por lacuna:** os 3 pares dist ≤2 entre chaves >4 (`etanol`↔`metanol`, `metil_etil_cetona`↔`metil_butil_cetona`, `metoxietanol_2`↔`butoxietanol_2`) e o par novo introduzido pelos aliases da 003.DM (`2_butoxietanol`↔`2_metoxietanol`) continuam dentro do raio — a DT nunca pediu para eliminá-los, só para parar de degradar com siglas curtas; esses seguem caindo no ramo seguro (empate→`NAO_RESOLVIDO`) e agora estão sob teste de vigia contra regressão silenciosa futura. Tier 2 (siglas) segue não-populada — o bloqueio de MOTOR que esta DT representava está removido; popular siglas reais é decisão de dado, fatia própria. Commits `c96e73f`+`6e956cd`, merge PR #242.

`[FECHADA — 003.DN; piso implementado em c96e73f/6e956cd; Tier 2 de aliases segue bloqueada por escopo de dado, não por motor; relacionada a D-ARQ-50 Parte 2, D-ARQ-22]`

**Nota (003.DO) — checagem de pré-condição, Tier 2 confirmada fora de escopo.** Dispatch chegou como tarefa de IMPLEMENTAÇÃO da Tier 2 de siglas, com a premissa "destravada" pelo fechamento desta DT. Checagem contra o texto integral desta DT e da nota de aplicação 003.DM (DECISOES v136: *"grafia normativa entra, sigla comercial não; `TCE` proibido por ambiguidade tricloroetileno/1,1,1-tricloroetano"*) mostra dois gates distintos, não um: o de **motor** (piso fuzzy) fechou aqui; o de **dado** (fonte normativa de cada sigla + política para pares ambíguos) nunca foi decidido — é citado nas duas sessões como "decisão de dado futura", não como pendente-mas-óbvio. Verificado de disco nesta sessão: `tricloroetileno` (linha 85) e `tricloroetano_111` (linha 399) seguem ambos no vocabulário em `agentes.yaml` — o par `TCE` continua ambíguo hoje, não é risco hipotético. Diovanni consultado; decisão: **não abrir Tier 2 nesta sessão**. Zero código tocado; zero mudança em `agentes.yaml`. `[CONFIRMADO — 003.DO; nenhuma mudança de escopo; suíte e mypy re-verificados delta-zero contra `91235de`]`

## D-ARQ-58 — Resolução de predicado por identidade de agente: fallback genérico no avaliador, não um primitivo dedicado por agente

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (mesma sessão 003.CU). Autorização para virar D-ARQ é do Diovanni (ratificada).

**Contexto.** `avaliar_predicado` (`predicados.py`) resolvia `quando` só por três vias: `ctx.predicados`, `REGISTRO_PRIMITIVOS`, `predicados_compostos`; fora disso, `PredicadoDesconhecido`. Cada agente usado como predicado exigia um `@primitivo("x")` escrito à mão — um one-liner `any(r.agente == "x" for r in ctx.riscos)` (só benzeno e fumos_metalicos existiam do lado químico). A família R-BIO-04 (`quando: acetona`, `quando: tolueno`, …) não dispararia: 12 agentes sem primitivo → exceção na emissão. A premissa "zero motor" de D-ARQ-38 fatia (d)/003.CT estava **incompleta** — o emissor é genérico, mas a camada de predicado exigia um símbolo por agente (achado de gate da IMPL, reportado antes de codar).

**Decisão (2 forks, recomendação B ratificada).** (A) 12 primitivos à mão (molde `_benzeno`) — segue o padrão, mas repaga o custo por agente para sempre (forma Viverde). (B, escolhida) **fallback genérico**: se `nome ∉` predicados/primitivos/compostos **mas** `nome ∈ protocolo.vocabulario.agentes` → resolve como `any(r.agente == nome for r in ctx.riscos)`; senão mantém `PredicadoDesconhecido`. Uma mudança de motor, universal (qualquer agente do vocabulário vira predicado sem boilerplate), e o typo continua levantando (só cai no fallback quem existe no vocabulário).

**Fronteiras.** Precedência preservada: primitivos/compostos vencem o fallback → `benzeno`/`fumos_metalicos` seguem resolvendo pelo primitivo (redundantes sob o fallback; limpeza é sessão futura, não esta). Universalidade (D-ARQ-06): biomonitoramento por identidade de agente é o padrão que se repete em construção/química/saúde. `[DERIVADO — predicados.py; gate de IMPL 003.CU]`.

**Aplicação 003.CU (IMPLEMENTAÇÃO).** Fallback inserido entre `predicados_compostos` e `raise PredicadoDesconhecido`; docstring cita a família R-BIO-04. Testes: `test_fallback_agente_*` (presente→True, ausente→False, fora-do-vocabulário→`PredicadoDesconhecido`). Commit `5cf2f24`, merge PR #208. Sem regra clínica criada/alterada.

## D-ARQ-59 — O refactor família R-BIO-04 → "estágio genérico" é gatilho falso; a família é a forma final, o limiar ~25 aposentado

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA, sessão 003.CX). Sem código. Fecha o heads-up deixado por 003.CT/003.CW ("EE lote 2 cruza ~25 → dispara refactor família→estágio genérico, molde D-ARQ-54"). Autorização para virar D-ARQ é do Diovanni (ratificada).

**Contexto.** 003.CT cravou, ao decidir a família `R-BIO-04-<agente>`, um trade-off nomeado: "n≈12 favorece família; se cruzar ~25 agentes, migrar p/ estágio genérico é refatoração futura (critério 'unificar só quando a forma confirmar', molde D-ARQ-54 P3)". 003.CW pousou em 24 regras R-BIO-04 (21/41 EE do Quadro 1) e registrou o heads-up: o EE lote 2 cruzaria ~25 e dispararia o refactor **antes** de mais agentes. Esta decisão é a 2ª passada crítica sobre esse gatilho, no kickoff da 003.CX. Nota: "molde D-ARQ-54" refere-se ao **princípio** de D-ARQ-54 P3/fatia 3 ("unificar só quando a forma confirmar", anti-falsa-completude D-ARQ-22) — D-ARQ-54 em si é a superfície RT, sem relação com biomonitoramento.

**Gate de estado real (disco, 003.CX).**
- `regras.yaml`: cada `R-BIO-04-<agente>` é bloco puro-dado — `id`, `quando: <agente>`, `emite: [{exame, periodicidade_meses: 6, momentos}]`, `base_normativa` (citação própria: Quadro + biomarcador), `status`. Zero lógica. `[DERIVADO — regras.yaml]`
- `stage_5_emissao` emite slug-fixo por regra, iterando genericamente; `avaliar_predicado` resolve `quando: <agente>` pelo fallback genérico de D-ARQ-58 (`any(r.agente == nome ...)`), sem símbolo por agente. **Não existe código por-agente.** `[DERIVADO — D-ARQ-58 aplicação 003.CU; emissao.py slug-fixo]`
- PROTOCOLO §5.9 já é a fonte única agente→biomarcador→Quadro; `regras.yaml` é sua materialização. `[DERIVADO — PROTOCOLO §5.9]`

**Decisão — rejeitar o refactor; a família é a forma final.** Quatro razões, em ordem de peso:

1. *O motor já é genérico (D-ARQ-58).* O limiar ~25 foi cravado em 003.CT como proxy de "quando a complexidade de motor justifica unificar num estágio". Mas D-ARQ-58 (mesma sessão que iniciou a família, 003.CU) já tornou o avaliador genérico: qualquer slug de `vocabulario.agentes` vira predicado sem boilerplate. **O que o "estágio genérico" construiria já está construído.** O gatilho foi definido antes de D-ARQ-58 internalizar essa generalidade — é um proxy de complexidade que D-ARQ-58 retirou. O limiar ~25 fica **aposentado**.

2. *O par (ID + `base_normativa`) por agente é ativo regulatório, não dívida.* CLAUDE.md exige rastreabilidade linha-de-código→norma para auditoria PCMSO. Cada `R-BIO-04-<agente>` carrega ID estável e citação normativa própria. Colapsar numa tabela ou (a) perde a citação por agente ou (b) a reduplica dentro da tabela — e aí "estágio genérico" é `regras.yaml` com outra roupa: ganho marginal, custo de auditoria real.

3. *Os fatos clínicos são dado (D-ARQ-07), não código.* `momentos`/`periodicidade`/`exame` estão explícitos em cada regra. A tentação do estágio genérico é derivar `momentos` do Quadro (EE→`[per]`, SC→`[adm,per,RT,MR,dem]`) **em código** — isso é regra clínica virando lógica, regressão contra D-ARQ-07/09. A família mantém cada fato clínico como dado.

4. *Universalidade não discrimina.* Tabela e família servem construção civil/química/saúde igualmente (gate CLAUDE.md satisfeito por ambas). O eixo decisivo é rastreabilidade + D-ARQ-07 — ambos favorecem a família.

**Steelman do refactor (custo real reconhecido).** A 41/41 EE + outros Quadros/normas, `regras.yaml` pode chegar a 60–100+ blocos quase idênticos: revisão de PR tediosa e, sobretudo, **edição Quadro-wide** (corrigir um `momento` de todo um Quadro toca N linhas em vez de uma; risco de typo em lote grande). Custo genuíno, mas pequeno e **endereçável sem refactor**.

**Resposta ao custo real (não paliativo).** Se a manutenção Quadro-wide doer, a forma correta é um **teste de consistência `§5.9`↔`regras.yaml`**: como §5.9 já é fonte única, o teste verifica que cada linha da tabela tem regra correspondente com biomarcador e Quadro coerentes (e vice-versa). Dá o benefício de fonte-única (mudar uma vez, verificar N; typo pego no gate) preservando ID, citação e testabilidade por regra — sem tocar motor nem D-ARQ-07. Fica **proposto**, não implementado; dispara só se o volume incomodar.

**Consequência.**
- Limiar ~25 aposentado. **EE lote 2 desbloqueado** — não há mais gate arquitetural antes de continuar a expansão da família R-BIO-04. A ordem de continuar é decisão de kickoff, não bloqueada por design.
- Nenhuma regra clínica criada/alterada (R-* intactas; PROTOCOLO inalterado). R-BIO-04 mantém ID e forma família.
- D-ARQ-38 fatia (d) permanece a decisão-mãe da família; esta decisão fecha o trade-off "família vs estágio" que ela deixou nomeado, a favor da família.

`[DERIVADO — regras.yaml; D-ARQ-58; PROTOCOLO §5.9; D-ARQ-38 003.CT/CW; princípio D-ARQ-54 P3]`. Sem código.

## D-ARQ-60 — Reconciliação nome-de-exibição §5.9 → slug canônico mora no guardião (registro explícito), não no doc; §5.9 é fonte humana, `regras.yaml` a chave de máquina

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (sessão 003.CY). Materializa o teste de consistência `§5.9`↔`regras.yaml` proposto em D-ARQ-59. Autorização para virar D-ARQ ratificada pelo Diovanni.

**Contexto.** D-ARQ-59 propôs (não implementou) um teste-guardião: cada agente do mapa §5.9 tem `R-BIO-04-<agente>` correspondente e vice-versa. 003.CY implementa. Na 1ª corrida contra dado pré-existente ele achou dois desencontros reais entre as fontes — o valor esperado de um guardião.

**Achado 1 — benzeno roteado por pacote.** benzeno está no §5.9 (Quadro 1/EE, TTMA) mas não tem `R-BIO-04-benzeno`: é coberto por `R-PKG-BZ` (§6, ácido transmucônico semestral). Comparação por contagem daria falso positivo. Tratado por registro explícito `EXCECOES_PACOTE = {"benzeno": "R-PKG-BZ"}`; o teste valida que o pacote existe em `protocolo.regras` (exceção não vira carimbo vazio).

**Achado 2 — a coluna "agente (slug)" continha prosa em 6/25 linhas.** chumbo (inorgânico), cromo hexavalente (comp. solúveis), cádmio (inorgânico), flúor / HF / fluoretos inorgânicos, indutores de metahemoglobina (classe), inseticidas inibidores da colinesterase — nome descritivo (acento, parênteses, `/`, qualificador clínico), não o slug canônico.

**Decisão — a reconciliação descritivo→slug mora no guardião, via registro explícito.** Mesma classe de reconciliação já resolvida para benzeno (mecanismo de D-ARQ-59) → mesmo mecanismo: `APELIDOS_MAPA` (sibling de `EXCECOES_PACOTE`) mapeia as 6 strings de exibição aos slugs; o parser resolve col1 via `APELIDOS_MAPA` (default identidade) antes de comparar. Auto-guardado: apelido→slug sem regra cai em `faltando` (vermelho); regra sem linha no mapa cai em `orfas` (vermelho) — o registro não fabrica cobertura.

**Alternativas rejeitadas.**
1. *Normalização no parser* — não-determinística: de "flúor / HF / fluoretos inorgânicos" nenhuma regra recupera `fluoretos` (3º token). Matching fuzzy dentro de um guardião contradiz o propósito dele.
2. *Coluna `slug` no §5.9* — duplicação em 19/25 linhas, novo vetor de drift (coluna descritiva não-guardada), e a variante "col1 vira slug puro" perde qualificador clínico real (Cr⁶⁺ "comp. solúveis"). Inventaria 2º mecanismo (coluna no doc) para o que o registro já resolve — o smell "`regras.yaml` com outra roupa" de D-ARQ-59.

**Corolário — header §5.9 `agente (slug)` → `agente`.** A coluna é fonte **humana** (prosa com qualificador clínico), não chave; o cabeçalho prometia slug e entregava prosa. `regras.yaml` é a chave canônica; §5.9 é o mapa legível. Edição de uma célula, sem tocar as 25 linhas de dado.

**Nota de implementação.** Detecção da tabela ancora por heading `5.9` + primeira linha separadora (`|---|`), não por palavras-chave — a heurística por palavras colidia com prosa de changelog dentro da própria seção. `protocolo.regras` é `list[dict]` (acesso `r["id"]`). Guardião `test_consistencia_mapa59_regras.py`, 2 testes; poder discriminante confirmado nos dois eixos (regra órfã / apelido faltante). Suíte 816+4→818+4, mypy delta-zero.

**Consequência.** O guardião converte o casamento §5.9↔yaml (antes verificado a olho) em invariante de máquina; EE lote 2 nasce coberto (agente novo cai nas duas fontes ou vermelha; nome em prosa exige entrada em `APELIDOS_MAPA`). Nenhuma regra clínica criada/alterada; `R-BIO-04` mantém ID e forma. PROTOCOLO §5.9 tocado só no header. PAINEL não re-tira.

`[DERIVADO — D-ARQ-59 proposta do teste; test_consistencia_mapa59_regras.py c934d72; PROTOCOLO §5.9; regras.yaml R-PKG-BZ]`.

## D-ARQ-61 — Critério de escolha do indicador canônico quando o Anexo I oferece múltiplas opções ("ou")

**Status:** DECISÃO DE ARQUITETURA (sessão 003.DL), aplicada na mesma sessão às 5 regras do EE lote 2 com "ou" real. Ratificada pelo Diovanni. Não cria nem altera regra clínica — governa a *escolha* dentro de R-BIO-04.

**Contexto.** O Quadro 1 do Anexo I lista, para vários agentes, dois a quatro indicadores biológicos ligados por "ou" (1,1,1-tricloroetano tem 4; ciclohexanona, clorobenzeno, N,N-dimetilformamida e tetracloroetileno têm 2). O modelo emite **um** exame por regra. Até 003.DL a escolha era feita caso a caso, sem critério registrado — cinco escolhas já em produção (tolueno, CO, anilina, estireno, tricloroetileno) tinham sido tomadas sem regra explícita que as gerasse.

**Decisão — critério ordenado, aplicado nesta ordem:**

1. **Descartar indicadores em *ar exalado final*.** Não são exames laboratoriais de rotina; nenhuma matriz validada os emprega.
2. **Entre os restantes, adotar o que a Matriz validada usa.**
3. **Se a Matriz não cobrir o agente: sem default — escalar para decisão explícita e registrá-la.**
4. **Marcar sempre `[INTERPRETADO]`** na `base_normativa`, **nomeando as opções descartadas**.

**Validação retroativa — o critério explica 100% das escolhas anteriores**, nenhuma das quais foi tomada sob ele:

| Agente | Opções no Anexo | Escolhido | Regra que explica |
|---|---|---|---|
| tolueno | sangue / urina / orto-cresol | orto-cresol | 2 (Matriz venceu o "1º listado") |
| monóxido de carbono | COHb / ar exalado | COHb | 1 |
| anilina | p-aminofenol / metahemoglobina | metahemoglobina | 2 (Matriz venceu o "1º listado") |
| estireno | soma mandélico+fenilglioxílico / estireno urina | soma | 2 |
| tricloroetileno | ác. tricloroacético / tricloroetanol sangue | ác. tricloroacético | 2 |
| inseticidas (Quadro 2) | acetilcolinesterase / butirilcolinesterase | acetilcolinesterase | 2 |

Nenhum contraexemplo encontrado no acervo.

**Sobre a regra 3 (correção feita na 2ª passada).** A formulação inicial era *"se a Matriz não cobrir, adotar o 1º listado no Anexo I"*. **Rejeitada:** a ordem do Anexo não tem significado normativo declarado, logo seria default arbitrário produzindo escolha errada **em silêncio** — classe D-ARQ-22. Escalar produz decisão consciente. Não dispara no lote 2 (a Matriz cobre os 22), então o custo da correção foi zero e o ganho é futuro.

**Objeção antecipada — isso não inverte a hierarquia de fontes.** A regra 2 faz a Matriz (nível 3, "referência, não gabarito") determinar o canônico. A hierarquia decide **o que é verdade normativa** — quais indicadores são válidos = Anexo I, nível 2 — e todos os candidatos já passaram por esse filtro antes de a regra 2 agir. A Matriz decide apenas **qual dos já-válidos adotar na prática**, que é escolha de prática clínica, não de norma. A prática da médica coordenadora é precisamente o conhecimento tácito que o Papel 1 existe para formalizar: usar a Matriz como desempate de canônico é o uso correto dela.

**Universalidade.** O critério não depende de setor — opera sobre a estrutura do Anexo I (que é nacional e setor-agnóstica) e sobre a Matriz. Vale para construção civil, indústria química e saúde igualmente.

**Consequência.** As 5 escolhas de canônico do EE lote 2 derivam do critério em vez de julgamento ad-hoc, e cada uma nomeia suas descartadas na `base_normativa` (auditável). Escolhas futuras deixam de ser decisão de sessão. `R-BIO-04` mantém ID e forma; nenhuma R-* criada ou alterada.

`[DERIVADO — NR-07 Anexo I Quadro 1, Portaria MTP 567/2022, texto oficial gov.br; Matriz Dra. Patrícia 06/2025; regras.yaml 1477cf7]`

## D-ARQ-62 — Redirecionamento de foco pós-003.DQ: Marco 1 via caso-âncora real; recorte construção civil como sequenciamento, não arquitetura

**Status:** DECISÃO DE FOCO (sessão 003.DR). Ratificada pelo Diovanni. Não cria nem altera regra clínica.

**Contexto.** Dez sessões (003.DL–003.DQ) sem tocar as 3 dívidas que o PAINEL declara como travando produção (DT-003L-01, DT-003M-02, DT-FDS-02); Marco 1 não alcançado; ausência de entrega visível à diretoria.

**Decisão (4 cláusulas):**
1. **Prioridade = Marco 1 via caso-âncora.** Rodar o pipeline completo (`preparar_envelope` → confirmação-RT → `processar_arquivo_pgr`) no `PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf`, com diff contra a matriz humana `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc`.
2. **Recorte construção civil é sequenciamento de dados, não arquitetura.** Encolhe a fila de formas/ingredientes a cobrir (acervo real ~todo construção civil: CMO, Consciente, Dinâmica, Ricco, Toctao, Viverde, T65, Seconci-GO). Nenhum componente do motor condiciona comportamento a setor; fatia que introduzir ramo setorial viola universalidade e é rejeitada.
3. **Modo de operação: rodar em uso real, corrigir pelo erro** — sustentado pelo anti-supressão (D-ARQ-31/35: erro → pendência nomeada, nunca silêncio). Complemento obrigatório: pendência cobre ausência; conteúdo errado presente só o diff contra matriz humana detecta — rodada em caso real com matriz correspondente sempre inclui diff.
4. **Fila de despacho pautada pelo relatório de MEDIÇÃO**, não pela ordem de abertura das DTs. DT-003L-01 e DT-003M-02 reescopadas ao acervo construção civil, abertas. DT-FDS-02 resolve-se de passagem (derivação ABNT NBR 14725 vigente, fonte primária — tarefa do Arquiteto).

**Resultado da 1ª medição (003.DR).** Pipeline bloqueou em `preparar_envelope` com `topo_ausente` (D-ARQ-53): zero âncoras GHE reconhecidas no Fascino. Causa MEDIDA (pdfplumber sobre o PDF real): os 19 cabeçalhos existem (`GHE 01 – ENGENHARIA` … `GHE 19 – VENDAS`, págs. 28–88), mas o glifo separador extrai como U+0000 (`GHE 01 \x00 ENGENHARIA`; pág. 75 sem espaço: `GHE 16\x00 PINTURA`), e `_reconhece_cabecalho_ghe_padrao` exige `-` literal. Mesma classe de defeito glifo-de-fonte de 003.DD (Ricco, Õ→0x4F); o U+0000 permeia o documento (ex.: `NR\x0001`, CBOs). Abre **DT-003DR-01**. O modo "rodar e corrigir pelo erro" funcionou como desenhado: bloqueio nomeado, zero silêncio.

**DT-003DR-01 (ABERTA, bloqueia ingestão — faceta de DT-003L-01):** separador de cabeçalho GHE extraído como U+0000 no layout Consciente derruba as duas rotas de âncora (`recortar_topo` e `recortar_blocos_ghe`). Correção candidata (003.DS): estender a classe de separador do reconhecedor padrão com o literal medido (precedente `[OÕ]` de 003.DD), fixture com linhas VERBATIM do Fascino, re-rodar a medição.

**Nota (003.DS) — FECHADA.** Reconhecedor padrão estendido para `[-\x00]` (PR #247, `536a4f4`); as duas rotas de âncora restauradas — medição determinística sobre o PDF Fascino real: 19 âncoras, `recortar_topo` não-None (`topo_ausente` resolvido), 19 blocos, `avaliar_estrutura`=`('ghe', None)`, `avaliar_segmentacao`=`None` (sem gate de densidade residual a reescopar). Fixture VERBATIM Fascino nas duas listas parametrizadas de `test_extracao_pgr.py` (3 positivas + 2 armadilhas). Run com LLM não exercido (sem chave) — não é critério desta DT. `[IMPLEMENTADO — 003.DS; PR #247]`

`[DERIVADO — medição 003.DR sobre matrizes_originais/PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf @ c71fb77; relatorios/003dr_fascino_relatorio.md (untracked)]`

**DT-003DS-01 (ABERTA — 003.DS; faceta de DT-003L-01; não-bloqueante de ingestão):** 20º cabeçalho do Fascino é `GHE\x00 TÉCNICO ADM / OPERACIONAL` (pág. 89) — GHE **sem número**. `_reconhece_cabecalho_ghe_padrao` exige `\d+` (fullmatch) → não casa, por design nesta sessão. Deferido por 3 razões: (1) reconhecer "GHE" sem dígito exige derrubar o guard-de-dígito que hoje rejeita a linha-glossário `GHE Grupo Homogêneo de Exposição:` (102 char) — precisa de discriminador novo, não tweak; (2) fora do repertório medido DT-003CM-01 (as 5 formas têm número); (3) o ` / ` de "TÉCNICO ADM / OPERACIONAL" é padrão cargo-slash — pode ser rota card (`eh_ancora_card_cargo`), decisão de classificação. Custo de deferir (nomeado): sem âncora própria, o conteúdo da pág. 89 funde na cauda do bloco de GHE 19 VENDAS → risco de **mis-segmentação** dos cargos técnico/adm. Resolução: decidir rota (GHE-sem-número vs card) derivada de ≥1 forma adicional no acervo; aceite = pág. 89 recorta em bloco próprio sem reabrir a linha-glossário como falso-positivo. `[DERIVADO — medição 003.DS Fascino]`

**Nota de aplicação (003.EB).** Modo offline (003.EB): subcomando `rodar-offline` dispensa
`CHAVE_API_GOOGLE`; clientes-bomba levantam `TranscricaoIndisponivel` se invocados — recusa
nomeada vira pendência bloqueante no relatório, nunca mock (coerente com D-ARQ-65: rodada
que a rota determinística cobre não invoca LLM).

## D-ARQ-63 — Gate de abertura em dois níveis: índice derivado + eixo nomeado

**Contexto.** O gate de abertura (CLAUDE.md, obrigação declarável instituída pela META
003.DQ após o gate pulado em 003.DP) exige leitura integral de PROTOCOLO e DECISOES antes
de qualquer formalização. Medição 003.DX: o DECISOES saiu de 8.734 bytes (17/05/2026) para
561.889 (24/07/2026) — 64× em 68 dias, com taxa recente (10/07→24/07) de ~10,6 mil
bytes/dia e acelerando, não estabilizando. Somado ao PROTOCOLO (~169 mil bytes), o gate
integral pede ~732 mil bytes, aproximadamente 185 mil tokens `[APROXIMADO — estimativa de
tokenização, conferir se o número for usado para decisão]`. Não cabe em contexto algum
junto com o trabalho da sessão. É aritmética, não desleixo: a regra foi escrita quando o
DECISOES era uma fração disso, e passou a ser impagável sem que nada quebrasse visivelmente
— a sessão apenas declarava o gate e seguia.

Causa medida `[MEDIDO — 003.DX, git objects @ 86cda09]`, em caracteres (não bytes — o
documento é UTF-8 com acentuação densa; não misturar as duas unidades):

- Corpo das 62 decisões: **453.685 chars**, dos quais **177.214 (39%) são acreção
  pós-decisão** — blocos `Changelog`, `Nota de implementação`, `Aplicação na sessão`,
  `Andamento`.
- Tabela de revisões: **87.328 chars, 16% do documento** — 145 linhas, 100% diário.
- Somadas, a massa de diário é **264 mil de 541 mil chars: 49% do DECISOES**.
- Concentração parcial: **D-ARQ-57 sozinho é 59.755 chars (13,2% do corpo), 51.818 de
  acreção**; D-ARQ-42 é 25.396. A cauda é longa — não há dois vilões, há um padrão.

O DECISOES virou registro de decisões **mais** diário de implementação. O diário duplica o
HISTORICO. O gate obriga a reler, toda sessão, o histórico de fatiamento de PRs que já está
registrado em outro documento vivo.

Nota de justiça sobre a causa: cada nota individual foi a coisa certa a escrever — registrar
onde a decisão foi materializada é rastreabilidade regulatória, exigência do PCMSO. O que
faltou não foi disciplina, foi um teto para onde a nota mora.

**Decisão — duas peças, ambas necessárias; nenhuma resolve sozinha.**

*Peça 1 — índice derivado, nunca escrito à mão.* `docs/INDICE_DARQ.md`, uma linha por
decisão (ID, título, status quando presente, linha de início, tamanho em chars), **gerado
por `scripts/gerar_indice_darq.py` a partir do próprio DECISOES**. Índice mantido à mão é
cache, e cache diverge — é a doutrina anti-cache do projeto aplicada a si mesma. Teste de
não-divergência (`gerar_indice()` == arquivo em disco) torna a divergência vermelha em vez
de descoberta tardia. O campo `chars` não é enfeite: é o que permite orçar o nível 2 antes
de começar a ler. Status sai vazio quando o bloco não declara um `[MEDIDO: 28 dos 62
declaram]` — ausência não é inferida.

*Peça 2 — gate em dois níveis, declarado nominalmente.*

- **Nível 1, sempre integral:** PROTOCOLO inteiro + `INDICE_DARQ.md` inteiro + corpo
  integral das decisões-mãe transversais **D-ARQ-06** (universalidade), **D-ARQ-09**
  (pureza do motor) e **D-ARQ-22** (modelo de qualidade) — as três incidem sobre qualquer
  decisão, independente do eixo.
- **Nível 2, por eixo:** corpo integral dos D-ARQ da cadeia que a sessão toca, escolhidos
  pelo Arquiteto a partir dos títulos do índice e **nomeados na linha do gate**.

Forma da declaração:

`Gate de abertura: PROTOCOLO vX integral, ÍNDICE vY integral, transversais D-ARQ-{06,09,22}, eixo <nome> = D-ARQ-{...} integral (git objects @ <hash>)`

Segue bloqueável pelo Diovanni em uma linha, sem auditar a leitura — que era o ponto da
003.DQ. Muda o que se lê; não muda se se lê, nem se se declara.

**Consequência.**

- O gate volta a caber: nível 1 ≈ PROTOCOLO (169k bytes) + índice (~5k) + as três
  transversais (~6,4k chars somados); nível 2 orçado pelo campo `chars` do índice antes de
  abrir qualquer bloco.
- **Risco residual assumido:** eixo mal escolhido faz a sessão pular um D-ARQ relevante —
  falha silenciosa, classe D-ARQ-22. Mitigação: a escolha é nominal e auditável contra o
  índice; não elimina o risco, torna-o visível e contestável. `[INTERPRETADO — prioridade
  na revisão de saída]`
- **Índice sem campo `eixo`, deliberadamente.** Eixo não é derivável do documento hoje;
  classificar as 62 decisões é trabalho de julgamento, fatia própria. Enquanto não existir,
  o nível 2 é escolha nominal do Arquiteto sobre os títulos, não lookup. Inventar o campo
  agora o faria nascer como cache.
- **Atrito novo, aceito:** o campo `chars` muda a cada edição de qualquer D-ARQ, logo toda
  PR que tocar o DECISOES precisa regenerar o índice ou o teste fica vermelho. É o
  comportamento desejado — é o que impede o índice de virar cache — mas é custo real em
  toda sessão de doc. Se o atrito se mostrar alto, a saída é rodar o gerador como hook de
  pre-commit; decisão adiada até haver evidência, não antecipada.
- **Dívida aberta (DT-003DX-01), três frentes:** (a) migrar a acreção pós-decisão para
  satélites `docs/darq/D-ARQ-NN.md` com ponteiro no D-ARQ; (b) D-ARQ-57 especificamente,
  13% do corpo sozinho; (c) a tabela de revisões (87k chars), candidata a arquivo próprio.
  Reduziria o corpo-decisão a ~276 mil chars. **Não é pré-requisito** desta decisão — não
  resolve o gate sozinha (ainda seriam ~70 mil tokens) — mas para a hemorragia e barateia
  o nível 2.

**Fronteiras (não confundir).**

- **CLAUDE.md (pasta do projeto Cowork) / META 003.DQ** — não revoga a obrigação
  do gate nem a linha declarável; substitui o conteúdo do nível 1 e acrescenta o
  nível 2. O texto normativo do gate vive hoje FORA do git `[MEDIDO — 003.DX]`,
  o que esta decisão não corrige — ver DT-003DX-02.
- **D-ARQ-26 (`/kickoff`)** — intocado. O kickoff coleta ESTADO (git, HISTORICO); o gate lê
  CONHECIMENTO ACUMULADO (protocolo, decisões). Momentos e objetos distintos; nenhum cobre
  o outro. A skill não passa a ler DECISOES.
- **D-ARQ-22** — o índice derivado é aplicação direta do gate de procedência ao próprio
  aparato de método: valor não-derivável (eixo) não entra no artefato derivado.
- **D-ARQ-44** — o índice é `.md`, logo já coberto por `*.md text eol=lf`; o terminador não
  é decisão nova.
- Não toca motor, protocolo clínico nem vocabulário. **Nenhuma R-* criada ou alterada.**

**Base.** Sessão 003.DX (24/07/2026), META. Origem: o gate integral revelou-se impossível de
cumprir na abertura da própria 003.DX — medido e reportado em vez de contornado com uma
declaração vazia. Peça 1 implementada em PR #255 (`scripts/gerar_indice_darq.py`,
`docs/INDICE_DARQ.md`, `tests/test_gerar_indice_darq.py`; suíte 939→944).

**Correção de medição interna à sessão (registrada por rastreabilidade).** A primeira
medição do Arquiteto reportou 50% de acreção e "D-ARQ-62 com 92k chars". Estava errada: a
delimitação de bloco ia do header até o fim do arquivo, e como D-ARQ-62 é a última decisão,
seu bloco engoliu a tabela de revisões inteira. A saída correta do gerador (que exclui
`## Histórico de revisões` por spec) expôs o defeito. Números desta decisão são os
corrigidos. O episódio é evidência a favor da cláusula de divergência dos prompts
cirúrgicos — que aqui pegou erro do Arquiteto, não do Code.

### DT-003DX-02 — A regra do gate mora fora do git `[PARCIALMENTE RESOLVIDA — 003.EG]`

**Origem:** Sessão 003.DX, bloqueio da PR B: o prompt cirúrgico assumia
`CLAUDE.md` no repo; o arquivo não existe no working tree nem no histórico
(`git log --all -- CLAUDE.md` vazio) `[MEDIDO — Code, 003.DX]`. A regra do gate
vive em `CLAUDE.md` na pasta do projeto Cowork, não versionado.

**Situação.** A obrigação declarável do gate (META 003.DQ, ampliada por
D-ARQ-63) e o protocolo do Claude Code (branch, `git add` nominal, cláusula de
divergência) são regras normativas do projeto que hoje não têm histórico, diff
nem PR. Podem divergir em silêncio. É exatamente a categoria que a doutrina do
projeto reserva a "ponteiro e julgamento, nunca fonte" — mas está carregando
fonte.

**O que a resolução exige (sessão própria).** Decidir a casa canônica das regras
de método no git (candidatos: `docs/METODO_ARQUITETO.md`; `CLAUDE.md` na raiz do
repo, que o Claude Code autocarrega) e reduzir o CLAUDE.md do Cowork a ponteiro.
Cuidado: as regras hoje misturam dois públicos — Arquiteto (gate, universalidade,
paliativos) e Code (branch, add nominal, divergência); a partição por público é
parte da decisão, não detalhe de execução.

**Resolução (003.EG, emenda).** A regra de método do público Code passa a existir versionada
em `CLAUDE.md` na raiz do repo — auditável, com histórico, diff e PR, e autocarregada pelo
Claude Code (candidato citado acima, escolhido). Disparador: a mesma classe de erro que esta
DT descreve ("regra fora do git diverge em silêncio") se materializou em código nesta própria
sessão — DH-003EG-03, `INDICE_DARQ` defasado por uma instrução de fechamento que dispensou a
suíte, sem rede versionada que a contestasse. Convenção adotada: o `CLAUDE.md` do repo é a
fonte; o `CLAUDE.md` do projeto Cowork (público Arquiteto — gate, universalidade, paliativos)
é reduzido a ponteiro para ele quanto às regras de método do Code. **Resíduo ABERTO:** nenhum
mecanismo detecta divergência entre os dois arquivos — se o Cowork for editado sem espelhar o
repo, a divergência silenciosa que esta DT nomeia continua possível, só que agora com metade
do problema (Code) resolvida e a outra metade (Arquiteto) intacta.

**Status:** PARCIALMENTE RESOLVIDA (003.EG). Método, não motor. Nenhuma R-* tocada.

## D-ARQ-64 — Ramo FUZZY opt-in por allowlist de dado: o veto é do resultado, nunca filtro de candidato

**Contexto.** DT-003DV-01 faceta B: o único acionamento de R-RX-01* na 1ª rodada ao vivo
(Fascino, 003.DV) veio do fuzzy 'Silício'→'silica' (dist 2) — silício metálico não é sílica
cristalina; falso-positivo da família de regras mais sensível do protocolo, classe D-ARQ-22.
O fuzzy generalista (D-ARQ-50 P2, raio 2 + piso DT-003DM-01) opera sobre um vocabulário onde
a maioria dos slugs carrega criticidade (regra, predicado, ototoxicidade ou risco implícito
de cargo): aproximação ortográfica que aterrissa em slug carregado dispara conduta clínica.
Medição desta sessão `[MEDIDO — 003.DY, código real sobre o vocabulário real]`:

| Grandeza | Valor medido |
|---|---|
| Índice de termos | **105 formas / 79 slugs** |
| Pares protegidos por empate (vigia 003.DN) | **4** |
| Zonas fuzzy exclusivas (chave elegível sem vizinho de outro slug no raio) | **94 = 77 carregadas + 17 de cauda** |
| Slugs carregados pelos canais de criticidade | **61/79** — regras.yaml 51 (token YAML, não texto bruto) + predicados.py 12 + is_ototoxico 12 + cargos.yaml 2 + epis.yaml 0 (medido vazio) |
| Allowlist `fuzzy_permitido` | **18 slugs** |
| Invariantes de fechamento | **77+17=94 · 61+18=79** |

**Decisão — 6 cláusulas.**

1. **Opt-in por dado, nunca inferido.** Campo `fuzzy_permitido: true` em
   `agentes.yaml`, por slug. Só slug marcado pode ser devolvido como `Confianca.FUZZY`.
   Tiragem inicial: 18 slugs de cauda (acidentes mecânicos, ergonômicos, físicos sem
   regra, químicos sem canal de criticidade). Ausência do campo = não permitido.
2. **A allowlist viaja com o índice.** `IndiceTermos` (frozen dataclass,
   `resolvedor_termos.py`): `slug_por_forma: dict[str, str]` +
   `fuzzy_permitido: frozenset[str]`, ambos construídos por `construir_indice_termos`
   (mesma lógica de colisão→`ValueError`). Consumidores (`hidratar_ghe`/`hidratar_pgr`,
   `processar_arquivo_pgr`) recebem o tipo, não dois argumentos soltos.
3. **O veto é do RESULTADO, nunca filtro de candidato.** A busca fuzzy roda inalterada
   (todos os candidatos elegíveis pelo piso, distância mínima, empate→NAO_RESOLVIDO);
   a allowlist incide SÓ sobre o vencedor eleito. Caso-âncora do falso-positivo evitado:
   'metanoll' tem `metanol` a dist 1 (vencedor único, fora da allowlist) e `etanol` a
   dist 2 (na allowlist). Vetar o resultado recusa `metanol` nomeadamente; filtrar
   candidatos apagaria `metanol` da disputa e faria `etanol` vencer sozinho — resolução
   FUZZY para o agente errado. Regressão cravada em
   `test_metanoll_recusa_metanol_e_nunca_resolve_etanol`.
4. **Recusa é pendência nomeada, não silêncio.** Vencedor fora da allowlist →
   `NAO_RESOLVIDO` + `Pendencia(tipo="fuzzy_recusado", destinatario="extracao",
   bloqueante=False, regra_origem="D-ARQ-64")` cujo motivo nomeia o termo, o slug
   vencedor e a distância medida. O ramo `else` de `hidratar_ghe` já trata (agente=None
   + pendência com `ghe_id` injetado, assert do seam 3 de D-ARQ-51 mantido).
5. **Sincronia allowlist × criticidade é teste computado, nunca lista digitada.**
   Nenhum slug `fuzzy_permitido` pode aparecer na união dos canais de criticidade —
   átomos de `quando` em `regras.yaml` (token YAML parseado, estável contra edição de
   prosa/comentário), literais de agente em `predicados.py`, `is_ototoxico` em
   `agentes.yaml`, `riscos_implicitos` em `cargos.yaml`. O teste
   (`test_allowlist_disjunta_dos_canais_de_criticidade`) computa os canais do dado real;
   slug que ganhar criticidade com allowlist ligada quebra vermelho, não caduca.
6. **Medição de conjunto fecha com par de invariantes, não com número solto.**
   `77+17=94` (toda zona exclusiva é carregada ou cauda; zero órfãs) e `61+18=79`
   (todo slug é carregado ou permitido; interseção vazia). A tiragem original do
   Arquiteto não tinha as invariantes e por isso um furo passou: `cargos.yaml` varrido
   só contra a cauda e `radiacao_uv_ir` excluído da allowlist sem ser somado à união —
   reportava 60/79 e 76 zonas carregadas, deixando 1 zona órfã inexplicada (76+17=93≠94).
   Valores desta decisão são os medidos pelo Code (cláusula de divergência dos prompts
   cirúrgicos, 2º BLOQUEADOR da sessão; o 1º pegou 'netanol' empatando etanol/metanol a
   dist 1 — termo do caso-âncora trocado por 'metanoll', com medição, antes do teste).

**Consequência.**

- Fuzzy sobre slug carregado morre recusado e nomeado; a zona de cauda (17 zonas,
  ex.: 'Microrganismo'→`microrganismos`) sobrevive intacta. Empate segue decidido ANTES
  do veto — os 4 pares do vigia continuam protegidos pelo mecanismo de empate, não pela
  allowlist.
- Adicionar slug à allowlist é decisão de dado auditável: o teste de sincronia recusa
  slug carregado; carga nova em slug permitido (regra, predicado, ototoxicidade, cargo)
  também quebra o teste — o par allowlist/criticidade não diverge em silêncio.
- `etanol` está na allowlist mas sua zona é protegida por empate (par etanol/metanol) —
  a allowlist não o expõe a falso-positivo por construção do veto-de-resultado.

**Fronteiras (não confundir).** D-ARQ-50 P2 — a busca fuzzy (raio, piso, empate) não
muda; muda só o que se devolve. DT-003DM-01 — piso bilateral intocado. D-ARQ-22 —
aplicação direta: recusa nomeada onde havia escolha de baixa confiança sobre slug
crítico. D-ARQ-14 — `vocabulario_ausente` segue para termo sem candidato ou empate;
`fuzzy_recusado` é tipo novo, exclusivo do veto. Nenhuma R-* criada ou alterada.

**Base.** Sessão 003.DY (25/07/2026), branch `feat/003dy-fuzzy-opt-in`. Suíte 945→949
passed, 6 skipped; `mypy --strict` sem erro novo. Fecha DT-003DV-01 faceta B e a DT
inteira (PROTOCOLO v66).

## D-ARQ-65 — Extração determinística por família de template; LLM rebaixado a acelerador para família não-medida; manual é corretivo, não rotina

**Contexto.** A rodada 003.DZ pediu apenas a re-execução do `rodar` medido em 003.DV, sem
qualquer código de motor no escopo. A extração LLM (`transcritor_gemini_pgr.py`, cascata
`_MODELOS` de D-ARQ-52) bloqueou 2× seguidas com `429 RESOURCE_EXHAUSTED` — quota diária
free-tier do projeto Gemini esgotada (`generate_content_free_tier_requests`, limite 20/dia
por modelo), diagnosticado por sonda HTTP direta fora do harness. Zero âncoras, zero blocos,
pendência bloqueante `transcricao_indisponivel_pgr`/D-ARQ-52 nas duas tentativas — o caminho
crítico de extração do Fascino inteiro depende de um terceiro cuja quota está fora do
controle do projeto. Medição adicional sobre o mesmo PDF (pdfplumber, sem LLM) mostrou que a
família de template Consciente/Fascino tem estrutura estável o bastante para um parser
determinístico: **20 âncoras**, rótulos de cabeçalho **20/20**, **237 linhas-de-risco**
ancoradas por token de categoria (`FISICO|QUIMICO|ERGONOMICO|ACIDENTE|BIOLOGICO`), bandas x
estáveis (`GRUPO@56`, `AGENTE@[113,177)`, `FONTE@177+`), **zero** quantificação numérica e
**zero** FDS apontada em todo o documento. Isso não é generalizável a qualquer PGR (D-ARQ-41
segue de pé para o caso geral) — é uma propriedade **de família de template**, medida.

**Decisão — 4 cláusulas.**

1. **Rota determinística por família medida.** Para uma família de template com estrutura
   medida (bandas x estáveis, âncoras de cabeçalho e de categoria-de-risco regulares), a
   extração pode rodar por um parser determinístico dedicado à família, emitindo o MESMO
   verbatim tipado (`GHEVerbatim`/`RiscoVerbatim`) sob o MESMO gate de forma
   (`gate_forma_ghe`) que a rota LLM já usa — o consumidor a jusante (hidratação, motor) não
   distingue a origem do verbatim.
2. **Roteamento por família.** Família reconhecida-e-medida → determinístico, sem tocar
   LLM. Família não-reconhecida → LLM-se-disponível, com `Pendencia` nomeando a família nova
   (sinal para medição futura, não silêncio). LLM indisponível (quota, rede, cascata sem
   `200 + STOP`) só vira pendência BLOQUEANTE quando a família em questão não é medida —
   família medida nunca fica refém de terceiro.
3. **Procedência no verbatim.** O verbatim carrega a origem (`deterministico:<familia>` |
   `llm` | `manual`), para que pendências e auditoria distingam de onde o dado veio.
   Implementação do campo e da costura de procedência é **deferida à fatia do roteamento**
   (fatia 2) — esta fatia (1) constrói o parser isolado, sem plugá-lo.
4. **Manual é corretivo, não rotina.** Entrada manual (RT corrigindo um verbatim) segue
   existindo como via de correção pontual sobre um caso que falhou nas duas rotas
   automáticas — nunca substitui rotina de extração, nem para família não-medida.

**Registrar.** Esta decisão **NÃO revoga D-ARQ-41/49/50** — o parser universal
determinístico (documento→`tipos.PGR` para QUALQUER PGR) segue inexistente e não é o que
está sendo proposto; D-ARQ-41 continua sendo o padrão bicamada (transcritor-LLM +
resolvedor) para o caso geral. O que muda é a existência de um parser **POR FAMÍLIA**
medida, como atalho determinístico quando a família específica já foi caracterizada — LLM
rebaixado de único caminho a acelerador-de-cobertura para família ainda não medida. Risco
declarado: **drift de template** (nova revisão do PGR de uma construtora muda o layout e o
parser determinístico da família passa a produzir lixo silencioso) — mitigado por
gate de forma (rejeita verbatim malformado, família ou não), fixture VERBATIM (literais
reais travados em teste, drift vira teste vermelho) e falha explícita (nunca fallback
silencioso para dado incompleto). Contexto que motivou a decisão: `429` free-tier medido
2× em 003.DZ — requisito de independência de terceiro no caminho crítico de extração.

**Consequência.**
- Família Consciente/Fascino ganha caminho de extração que não depende de quota de
  terceiro; medição desta sessão é o gabarito de bandas/âncoras da fatia 1 (parser
  isolado).
- Roteamento entre as rotas (determinístico/LLM/pendência-de-família-nova) e a costura de
  procedência no verbatim são trabalho da fatia 2 — não desta sessão.
- Nenhuma R-* criada ou alterada; motor clínico intocado. Decisão de arquitetura da camada
  de extração, não do protocolo.

**Fronteiras (não confundir).**
- **D-ARQ-41** — intocada; padrão bicamada segue sendo a via para família não-medida
  (Parte 1/2/3 inalteradas). Esta decisão não é uma terceira camada — é uma rota
  alternativa à camada-LLM, restrita a família medida.
- **D-ARQ-49/50** — o contrato do parse-PGR e o mecanismo termo→slug (resolvedor)
  seguem os mesmos; o parser determinístico por família produz o MESMO verbatim que a
  rota LLM entregaria, entrando no mesmo resolvedor a jusante.
- **D-ARQ-52** — pendência `transcricao_indisponivel_pgr` segue existindo para a rota LLM;
  esta decisão apenas evita que ela seja bloqueante quando a família tem rota
  determinística disponível.
- **D-ARQ-09** — preservada: o parser determinístico é motor (determinístico, puro sobre
  bytes do documento no wrapper de I/O), não introduz não-determinismo novo.

**Base.** Sessão 003.DZ (25/07/2026), ratificado pelo Diovanni. Origem: bloqueio de quota
429 (2× medido) no `rodar` do Fascino expôs dependência de terceiro no caminho crítico;
medição de bandas/âncoras da família Consciente confirmou viabilidade de parser
determinístico por família. Implementação em fatias: fatia 1 (esta sessão) = parser
isolado, sem plug; fatia 2 (futura) = roteamento + procedência no verbatim.

**Nota de aplicação (003.EA — fatia 2, roteamento).** `preparar_ghes` (rota "ghe") tenta
`parsear_arquivo(caminho)` (2ª leitura do PDF, mesma classe do seam humano de
`processar_arquivo_pgr` — D-ARQ-52) ANTES do cliente LLM. Aceitação exige as DUAS
condições: nenhum `FamiliaNaoReconhecida` (exceção tipada nova, `ValueError`, levantada
pelos dois pontos de falha de `_parsear_bloco`) E `len(candidatos) == len(blocos)` — as
duas rotas reconstroem linha por caminhos distintos (`pdfplumber.extract_words` direto vs.
`extrair_texto_pgr`/`recortar_blocos_ghe`), então divergência de contagem é tratada como
família não reconhecida (conservador; motivo nomeia as duas contagens). Aceita →
`gate_forma_ghe(candidatos)`, cliente LLM NUNCA invocado. Recusada (exceção OU contagem) →
`Pendencia` NÃO-bloqueante nova, tipo `familia_nao_medida` (`destinatario="extracao"`,
`regra_origem="D-ARQ-65"`), anexada às pendências devolvidas; fluxo LLM segue INALTERADO
(`transcrever_ghes` → `gate_forma_ghe`) — `transcricao_indisponivel_pgr` no fallback segue
bloqueante como sempre. Rota "card" (EBSERH — família não medida para o parser)
INTOCADA. Procedência no verbatim (`deterministico:<familia>`\|`llm`\|`manual`) segue
deferida (fatia 3). Testemunha positiva: Fascino real, 19/19 aprovados, zero invocação
LLM. Testemunha negativa: Viverde real, `FamiliaNaoReconhecida` (família não medida) aciona
o fallback LLM sem bloquear.

**Nota de aplicação (sessão atual, branch `claude/festive-gates-soy0fr`) — terceira
testemunha negativa.** `parsear_arquivo` rodado diretamente (sem LLM) contra
`PGR(ADENDO)CMO RESIDENCIAL AURORA LAGO DAS ROSAS 27.08.26.pdf` levanta
`FamiliaNaoReconhecida` já no 1º bloco (`ADMINISTRAÇÃO`: "cabeçalho de tabela
GRUPO/PERIGO/FONTE/AGRAVO não localizado") `[MEDIDO — execução direta desta sessão]`.
Confirma, por leitura do código (`orquestracao_pgr.py:188-211`), que a falha é
**do documento inteiro**, não por bloco: `parsear_arquivo` roda uma vez sobre o arquivo
completo, e a exceção no 1º bloco aborta a chamada antes de alcançar os 8 blocos
seguintes — não há parse parcial nem contaminação seletiva de um GHE. A `Pendencia`
`familia_nao_medida` resultante governa o documento inteiro, e o fluxo LLM (medido no app
como rota "100% LLM" para esta matriz) assume todos os 9 GHEs, não só o que disparou a
exceção — mesmo comportamento do caso Viverde, terceira família distinta a confirmá-lo.

**Cláusula 5 NOVA (003.EP fatia 0/1) — o bloco é um formulário de 2 colunas fixas, não só
uma tabela de riscos.** Medição 003.EP fatia 0 (`relatorios/003ep_anatomia_cargo.md`, M1/M2,
19/19 blocos do Fascino real): a célula "Cargo / Função" pertence a um formulário de rótulos
ordenados em duas colunas — rótulo à esquerda, valor à direita — com `x0` **idênticos
bit-a-bit nos 19/19 blocos** (`58.499347642527084` / `279.2172167102426`); onde existe
continuação física do valor (2/19 blocos), o desvio contra a banda do valor é **0,0pt
exato**. Célula = linha do rótulo + linhas físicas seguintes cuja 1ª palavra cai na banda do
valor, terminando na primeira linha que volta para a banda do rótulo — critério de
**transição de banda**, nunca o literal do próximo rótulo (nenhum campo específico,
"Qt. Trabalhadores" incluso, é verificado contra repertório algum). Isso é **distinto** da
calibração por bloco da tabela de riscos (banda AGENTE/FONTE, cláusulas 1-4 acima) — lá a
indentação varia PORQUE o conteúdo da célula anterior varia (`x0` de FONTE mede 168,3–198,5pt
entre blocos); aqui as colunas do formulário são fixas, o mesmo `x0` nos 19/19. A
distinção importa porque barateia qualquer campo futuro do mesmo formulário ("Qt.
Trabalhadores", "Descrição das Atividades", "Local de Trabalho" — todos já medidos usando as
mesmas duas bandas, `relatorios/003ep_anatomia_cargo.md` M1/M2): a mesma rotina de captura
serve, sem recalibração por bloco.

**Nota de aplicação (003.EP fatias 1-3, commits `aaa9eca`/`486d54d`/`7f19cf4`).**
`_extrair_cargos_da_linha` (`parser_familia_consciente.py`) passa a aplicar a Cláusula 5: lê
a célula "Cargo / Função" inteira (rótulo + overflow por transição de banda, fatia 1),
separa cada entrada por delimitador (`,`/`;`, nunca `\x00` — glifo interno a nome composto)
e descarta a cauda CBO-2002 (fatia 2). **O CBO é descartado, não modelado** — precedente
003.DG-1 (campo novo exige consumidor a jusante na mesma fatia; seria a 5ª instância de
campo-sem-consumidor, após `anexo_nr07`, `tipo_ibe`, `disparador_clinico`, `categoria`).
Dívida nomeada COM consumidor candidato: **DT-003ED-01 faceta máquina pesada**, cujo caminho
declarado é `riscos_implicitos` por cargo — o CBO seria chave melhor que nome livre para
esse mapeamento, decisão de fatia própria. Medição de não-regressão (`relatorios/
003ep_fascino_rodar.md` vs. `003eo_fascino_rodar.md`): linhas de exame **171→171** e status
por GHE **idêntico nos 19/19** — o único movimento é a pendência não-bloqueante
`regra_origem="R-GHE-02"`, **19→41** (DT-003EP-01, PROTOCOLO §11), efeito colateral esperado
de cargos reais chegarem ao vocabulário pela 1ª vez, não regressão de conduta.

**Por que não abrir D-ARQ nova para 003.EP.** 003.DZ declarou um RECORTE de escopo (fatia 1
= parser isolado, sem separação cargo/CBO), não um invariante de desenho da família — a
Cláusula 5 e sua nota de aplicação **estendem** o recorte medido, no mesmo molde que
D-ARQ-57 peça 1 usou para acrescentar as formas 4 e 5 de âncora GHE sem abrir uma decisão
nova a cada forma de template descoberta.

## D-ARQ-66 — Emissão incondicional é regra de primeira classe; o tri-estado de D-ARQ-31 computa sobre contribuições de risco, não sobre linhas emitidas

**Contexto.** Até 003.EC toda emissão era condicionada a predicado de risco. R-CLI-01
(clínico anual, piso universal) é [VALIDADO] desde a v2 do protocolo e nunca foi
implementada por falta de caminho para regra incondicional. DT-003EB-01 enquadrava isso
como "pacote-base sem conceito no motor"; a medição do gabarito Fascino (003.EC) refutou a
premissa — ver reenquadramento no PROTOCOLO.

**Achado que dimensiona a decisão.** `stage_5_emissao` já itera sobre REGRAS (não sobre
riscos) e já grava `risco_origem=None`. O invariante "toda linha deriva de um risco" nunca
existiu em código. Emitir incondicionalmente custou um primitivo — zero mudança em
`tipos.py`, `emissao.py` ou contrato de `MatrizGHE`.

**Decisão — 2 cláusulas.**

1. **O primitivo incondicional é nomeado pelo sentido clínico** (`todo_trabalhador`), não
   vacuamente (`sempre`), porque vai para o audit trail em `Motivo.predicado` e é lido na
   revisão de saída. Registrado em `PRIMITIVOS_INCONDICIONAIS`.
2. **O tri-estado VÁLIDA/PARCIAL/BLOQUEADA de D-ARQ-31 passa a ser computado sobre
   `linhas_com_risco`** — exclui as linhas cujos `Motivo.predicado` sejam todos
   incondicionais. `MatrizGHE.linhas` segue carregando a linha incondicional; muda só o
   gate do status.

**Justificativa da cláusula 2.** Sem ela, `linhas` nunca fica vazia, BLOQUEADA vira estado
inalcançável e "nenhum risco determinou" se apresenta como PARCIAL — erro silencioso
plausível da classe que D-ARQ-22 combate, no ponto exato onde a revisão de saída mais
precisa do sinal. Massa medida: no Fascino, 14 de 19 GHEs BLOQUEADA passariam a PARCIAL sem
que um único risco determinasse.

**Fronteiras.** D-ARQ-31 preservado (bloqueio por-risco/por-linha, anexação
pendência-à-linha, requisito piso-sem-teto). D-ARQ-15 intacto. Anti-supressão intacta: a
linha É emitida e visível, apenas não conta para o status.

**Universalidade (D-ARQ-06).** Clínico anual para todo trabalhador vale construção,
indústria química e saúde igualmente. Não é regra de construção civil.

**Base.** Sessão 003.EC. Commit f175e76 (11 arquivos, 154+/22−; suíte 963→967; mypy
--strict delta-zero em `motor` + `invariantes.py`).

## D-ARQ-67 — Literal de vocabulário em código é contrato verificado por teste computado do dado

**Contexto.** O primitivo `maquina_pesada` comparava `r.agente == "maquina_pesada"` contra
um slug que nunca existiu em `agentes.yaml`. Nenhum teste pegava: os testes do primitivo
constroem `GHEContext` sintético (o literal casa consigo mesmo) e o `ou` de `atividade_critica`
mascarava a perna morta com as pernas vivas. Código inalcançável em produção, verde na suíte,
por várias sessões — R-PKG-ATIVCRIT [VALIDADO] silenciado pela perna de máquina pesada sem
qualquer sinal. Classe D-ARQ-22 (erro silencioso plausível), do lado do código.

**Decisão — 4 cláusulas.**

1. Todo literal de vocabulário comparado em código de motor é CONTRATO com o dado, e o
   contrato é verificado por teste que COMPUTA os dois lados do dado real: literais extraídos
   do próprio fonte (AST), slugs lidos do YAML real. Nunca lista digitada, nunca revisão humana.
2. O teste falha quando o conjunto de órfãos é não-vazio. Literal órfão introduzido no futuro
   quebra vermelho; não caduca em silêncio.
3. Molde reusado da cláusula 5 de D-ARQ-64 (sincronia allowlist × canais de criticidade),
   generalizado: sempre que código e dado se referenciam por string, o casamento vira teste
   computado do dado, não convenção.
4. Um conceito → um slug → um primitivo. Predicado que duplica conceito de slug existente é
   APONTADO ao slug (o órfão morre); não se cria alias nem slug-espelho para preservar o rótulo.

**Consequência.** Teste sintético sobre primitivo deixa de ser evidência de alcançabilidade —
prova que a função funciona, não que algum dado a alcança. A cobertura de alcançabilidade é
do teste computado, não do teste de unidade.
`[VERIFICADO — varredura de 13 literais de agente em predicados.py contra 79 slugs de
agentes.yaml, 003.ED: 1 órfão, eliminado]`

**Base.** Sessão 003.ED (26/07/2026), commit `7b2e65d`.

## D-ARQ-68 — Silêncio documental mapeia para o ramo normativo de ausência quando a norma o define; sem esse ramo, D-ARQ-13 prevalece

**Contexto.** R-RX-01 roteia RX de tórax OIT pelo Quadro 1 do Anexo III da NR-07, que parte as empresas em dois ramos exaustivos — com medições quantitativas periódicas (4 faixas por LSC/LEO) e sem avaliações quantitativas (adm + 24M, 12M após 15 anos). O motor tratava a ausência de `quantificacao` como `Ausente` bloqueante, criando um terceiro estado que a norma não tem. Efeito medido no Fascino (003.EG): 14 GHEs com sílica resolvida, 70 pendências `predicado_ausente`, zero linhas de RX — a regra mais sensível do protocolo silenciada por um estado inventado pelo motor.

**Decisão — 5 cláusulas.**

1. Quando a norma aplicável define ramo explícito e exaustivo para "sem avaliação / sem medição", a ausência do dado no documento mapeia para esse ramo — o motor emite a conduta do ramo, não pendência bloqueante. A norma já decidiu o que fazer sob ausência; bloquear é substituir a decisão dela por silêncio.
2. Sem esse ramo, D-ARQ-13 prevalece: ausência → `Ausente` → pendência bloqueante. A condicional é o que impede esta decisão de virar afrouxamento geral do tri-estado.
3. Afirmação incompleta não é silêncio. Dado parcialmente afirmado que não roteia (`valor` sem `pct_quartzo`/`fracao`; flags contraditórias) permanece bloqueante mesmo quando a norma tem ramo de ausência — ali o documento declara pertencer ao ramo "com medições", e escolher faixa inventaria número (D-ARQ-08/22).
4. A ponte "documento silencioso ⇒ estado sem avaliação" é `[INTERPRETADO]` e vai marcada na regra que a usa: a norma fala do estado do mundo (a empresa), o motor lê o documento. Onde a divergência importar, o sinal de confirmação é o remédio — não o bloqueio.
5. **Delegação normativa a documento que a norma não obriga a responder.** Quando a norma **delega o predicado a um documento** que o motor lê (*"conforme informado no PGR"*, NR-07 Anexo II item 2) **e** a norma que rege esse documento **não obriga a resposta** (NR-09 9.4.1/9.4.2 — avaliação quantitativa *"quando aplicáveis"* / *"quando necessária"*), o silêncio não é defeito do documento, e a cl.2 não se aplica sem qualificação. A regra pode declarar a presunção **por primitivo nomeado**, com quatro exigências cumulativas:

   a) a presunção é **na direção protetiva** — presume-se dentro do universo da obrigação, nunca fora dele;
   b) a presunção é **declarada no dado** (`regras.yaml`), por primitivo, nunca inferida em código nem aplicada a "qualquer ausência da regra";
   c) a emissão carrega **pendência não-bloqueante** nomeando o primitivo presumido e o dado que falta, e a regra sai marcada `[INTERPRETADO — prioridade na revisão de saída]`;
   d) **matriz com linha emitida sob presunção não pode ser `VÁLIDA`** — o piso é `PARCIAL`.

   A alínea (d) separa esta decisão de `D-ARQ-71` cl.3, e a distinção é material. Lá o tri-estado não se move porque a conduta foi determinada por uma perna `True` independente — a lacuna era de visibilidade. Aqui a conduta **repousa inteiramente sobre a presunção**: sem ela não haveria linha. Deixar sair `VÁLIDA` produziria documento assinável, sem ressalva no nível da matriz, sustentado por dado que ninguém mediu — o erro silencioso plausível de `D-ARQ-22`, no ponto onde a revisão de saída mais precisa do sinal.

   A **cl.3 permanece e vence**: afirmação incompleta não é silêncio. `pct_LT` ou `relacao_LT` parcialmente afirmados seguem bloqueando. A presunção só alcança o estado em que o documento **nada diz** sobre o nível.

   **Fronteira com a cl.1:** lá a norma decide o que fazer sob ausência e o motor obedece; aqui a norma **não decide**, e o motor declara presunção auditável. Estados distintos, tipos de pendência distintos.

   **Universalidade (D-ARQ-06).** Expressa sobre a forma da norma (delegação a documento + não-obrigatoriedade da resposta), não sobre agente nem setor.

   **Nota ao contra-exemplo da cl.2 (003.EZ).** O corpo desta decisão cita o ruído como contra-exemplo vivo da cl.2 (*"Sílica destrava, ruído não"*). Continua correto quanto ao que 003.EH mediu — NR-15 Anexo 1 e NHO-01 não definem faixa default para ruído sem medição. O que faltava era a NR-09 9.4.2: a avaliação quantitativa é condicional, logo o PGR silencioso pode estar em conformidade, e o encaminhamento "corrigir o PGR" (R-PGR-05) não existe. A cl.5 endereça esse estado; a cl.2 segue valendo onde a norma **exige** a resposta.

   **Fronteira com D-ARQ-71, medida `[MEDIDO — 003.EZ, Fascino]`.** As 32 pendências `predicado_ausente_presumido` são **16 GHEs × 2 regras**, não 17 — e 17 GHEs declaram ruído sem quantificação. O 17º é o **GHE-16**: ali `vibracao_qualquer` resolve `True`, o `ou` curto-circuita, a regra **não** chega ao ramo `Ausente`, e a lacuna do ruído sai como `perna_ausente_absorvida` (D-ARQ-71 cl.2). As duas decisões particionam limpo: **perna absorvida** quando existe perna `True` independente, **presunção** quando não existe.

   Consequência que a revisão de saída precisa conhecer: **dois GHEs com a mesma lacuna documental recebem selos diferentes** — `PARCIAL` pela alínea (d) desta cláusula quando nada mais dispara, `VÁLIDA` pela cl.3 de D-ARQ-71 quando algo mais dispara. É desenho dos dois lados (lá a conduta está determinada por perna independente; aqui repousa na presunção), não inconsistência — mas é sutil, e por isso está escrito.

**Caso-âncora:** R-RX-01 / Quadro 1 (003.EH, commit `7dd68e6`). Contra-exemplo vivo e medido — a cláusula 2 não é teórica: ruído. `R-AUD-01`/`R-AUD-02` dependem de `ruido_acima_acao`, que devolve `Ausente` quando o PGR cita ruído sem quantificação. NR-15 Anexo 1 e NHO-01 não definem faixa default para ruído sem medição — logo o ramo 2 se aplica e o bloqueio permanece. Medido na mesma rodada `37cdda6`: as 4 pendências `predicado_ausente` restantes são todas `R-AUD-01`/`R-AUD-02` (GHE-06 e GHE-12), inalteradas. Sílica destrava, ruído não, pela diferença entre as normas — que é exatamente o que a decisão prevê.

**Fronteiras (não confundir).**

- D-ARQ-13 — não revogado. Segue sendo o default; esta decisão nomeia a exceção e a condiciona à existência do ramo normativo.
- D-ARQ-29 — trata de `fracao` ausente (invariante do Quadro 2), nunca de `quantificacao` ausente. Ortogonal. A assimetria sílica×PNOS que existia no ramo `q is None` não era coberta por D-ARQ-29 e deixa de existir aqui.
- D-ARQ-31 — ortogonal: trata de como pendência bloqueante interage com a emissão; esta trata de como input vira estado, a montante.
- D-ARQ-22 — a cláusula 3 é a proteção contra o erro silencioso; a cláusula 4 exige a marca `[INTERPRETADO]` que a revisão de saída usa para priorizar.

**Consequência.**

- Regra materializada e verde na suíte pode estar inalcançável em produção quando o campo que seu predicado lê não é escrito por nenhum produtor real. Classe irmã de D-ARQ-67 (literal de vocabulário sem contrato) e do primitivo órfão de 003.ED. Ao criar predicado que lê campo de `Quantificacao`, verificar quem o escreve fora de fixture.
- Toda aplicação desta decisão nomeia, na regra, o ramo normativo literal que autorizou o mapeamento — sem ramo citável, aplica-se a cláusula 2.

**Universalidade (D-ARQ-06).** "Empresa sem avaliação quantitativa" é estado de empresa, não de setor — e é o caso mais comum fora de indústria com higienista. Vale construção, química e saúde igualmente.

**Base.** Sessão 003.EH. Texto literal do Anexo III conferido no PDF oficial do MTE (Portaria MTP 567/2022). Commit `7dd68e6`, merge `37cdda6` (PR #270).

## D-ARQ-69 — Regra clínica escrita antes da sessão não é materializada sem conferir o texto vigente da norma que ela mesma cita

**Contexto.** R-ESP-01 era `[VALIDADO]` desde a v2 do protocolo (17/05/2026) e citava "NR-07, item de espirometria" como base normativa. Ao materializá-la em 003.EI, a conferência do Anexo III vigente (Portaria MTP 567/2022, PDF oficial MTE) mostrou divergência nas duas pernas: o gatilho é **poeira mineral** (item 3.1), não "químico respiratório / fumos metálicos"; e a exceção-EPI (3.3) é condicionada a histórico de doença respiratória crônica ou sinais/sintomas, condicionante ausente da redação. Sem a conferência, a sessão ia instalar campo novo (`via_respiratoria`) em `agentes.yaml` e emitir espirometria por solvente — superemissão contra a norma, classe D-ARQ-22. Custo medido do desvio: três reformulações de escopo antes de alguém abrir a norma que a própria regra citava.

**Decisão — 3 cláusulas.**

1. Regra clínica redigida em sessão anterior e ainda não materializada não é materializada sem conferência do texto vigente da norma que ela cita como base. A conferência é declarada com fonte e data, no corpo da regra.
2. Divergência encontrada resolve pela hierarquia de D-ARQ-22 Parte A (norma vigente vence redação antiga), e o resultado obedece à regra de versionamento do projeto: conduta prescrita alterada → nova ID + antiga DEPRECATED.
3. `[VALIDADO]` não dispensa a conferência. O marcador atesta crivo clínico no momento da entrevista (16-17/05/2026), não vigência normativa perene — a norma pode ter mudado depois do crivo, e nesse caso a redação carrega o texto revogado.

**Fronteiras (não confundir).**

- D-ARQ-22 — Parte A já põe norma vigente como nível 1. Esta decisão não a repete: nomeia o MOMENTO em que a conferência passa a ser obrigatória (materialização), que a Parte A não fixa.
- D-ARQ-27 — derivação normativa é o método; esta é o gatilho que o convoca.
- D-ARQ-68 — irmã: aquela trata de como input vira estado; esta, de como regra escrita se relaciona com norma vigente.
- Não toca motor. Nenhuma R-* criada ou alterada por esta decisão.

**Caso-âncora:** R-ESP-01 → R-ESP-02 (003.EI). Contra-exemplo registrado: R-CLI-01 foi materializada em 003.EC sem conferência prévia e bateu com a norma — resultado correto por sorte, não por método; é o tipo de acerto que esconde a lacuna.

**Universalidade (D-ARQ-06):** vale para qualquer regra do protocolo, qualquer setor.

**Base.** Sessão 003.EI. Texto do Anexo III conferido no PDF oficial do MTE.

**Nota de aplicação 003.FA — a página oficial não é o texto oficial.** Ao conferir a NR-07
nesta sessão, medido que a **página** da NR-7 no portal do MTE lista alterações apenas até a
Portaria SEPRT n.º 8.873, de 23/07/2021, e **não menciona a Portaria MTP n.º 567, de
10/03/2022** — justamente a que deu redação aos Anexos I e III sobre os quais metade deste
protocolo se apoia. O **PDF servido por essa mesma página** traz a 567/2022 no cabeçalho, junto
com a Portaria SEPRT n.º 1.295/2021, também ausente da listagem. `[MEDIDO — 003.FA, 18/08/2026]`
Consequência para o gate desta decisão: conferir vigência pela listagem da página oficial erra
por duas portarias. A conferência exigida por `D-ARQ-69` é contra o **texto** — o cabeçalho do
próprio arquivo normativo —, nunca contra o metadado da página que o hospeda. Nenhuma regra
`R-*` afetada; o projeto já operava com a 567/2022.

**Resíduo aberto, não corrigido nesta sessão.** A **Base** de `D-ARQ-70` cita "Literal da NR-09
Anexo I conferido no PDF oficial (`nr-09-atualizada-2026.pdf`, **Portaria MTP 426/2021**)" — o
nome do arquivo é 2026 e a portaria citada é de 2021, superada pela **Portaria MTE n.º 105, de
29/01/2026**, achado da 003.EZ. O corpo de `D-ARQ-70` não foi reconciliado quando aquela sessão
fez o achado. Não corrigido aqui por ser sítio de outra decisão; registrado para a fila.

## D-ARQ-70 — Alias de corpus medido entra no vocabulário só ancorado em literal normativo, com fonte dupla e teste anti-FP

**Contexto.** O campo `termos:` (D-ARQ-50 P2) admitia, pelos critérios de 003.DM e 003.DW, a grafia literal da norma quando difere do slug. A medição do Fascino (003.EJ) mostrou que isso não cobre o caso real: o PGR escreve `Vibrações localizadas (mão e braço)` em 9 GHEs, grafia que nenhuma norma emprega, e o slug `vibracao_mao_braco` elide o "e" que a grafia natural carrega ("mãos e braços"). Medido no mesmo corpus: `vibracao_corpo_inteiro` resolve hoje por **acidente** — o PGR escreve `Vibração (corpo inteiro)` e `normalizar_termo` converte parênteses e espaços em `_`, colidindo exatamente com o slug. A família de vibração dependia de coincidência ortográfica, não de contrato — classe D-ARQ-67 do lado do dado.

**Decisão — 5 cláusulas.**

1. **Admissão (Tier 1-C).** Entra em `termos:` a grafia que cumpra as quatro: (i) **medida** em documento real do acervo, com arquivo e contagem nomeados no comentário do YAML — nunca hipotética; (ii) atribuição ao slug sustentada por **conter o núcleo semântico do literal normativo vigente** ou sua redução direta; (iii) gravada com **fonte dupla** — o documento medido e o literal da norma que a ancora; (iv) coberta por **teste anti-FP** provando que a grafia não resolve para slug vizinho da mesma família.
2. **Fronteira com a proibição de D-ARQ-50 P2.** O que a saída (a) daquela decisão rejeitou foi o dicionário de sinônimos **especulativo** ("perseguição infinita"). Alias medido é *append-by-medição*, o mesmo padrão que D-ARQ-57 usa para âncoras de bloco. A diferença é falsificável, não retórica: alias sem documento medido citado é especulativo e não entra.
3. **O LLM não ganha o trabalho.** A alternativa rejeitada era instruir o transcritor a emitir a grafia normativa da família. Isso move escolha quase-slug para o LLM, contra D-ARQ-41 P1 e D-ARQ-50 P2. O transcritor segue verbatim-bounded; a reconciliação é resolver-side e determinística.
4. **Alias redundante não entra** — grafia que normaliza para o próprio slug (003.DM). `Vibração (corpo inteiro)` é o caso: já resolve EXATA sem alias.
5. **Sigla entra quando é o literal da norma e não-ambígua.** A proibição de sigla de 003.DM foi motivada por `TCE`, jargão sem fonte e ambíguo entre dois agentes do vocabulário. `VMB`/`VCI` são o literal do Anexo I da NR-09, não-ambíguos, e ficam sob `PISO_FUZZY = 4` — resolvem só por EXATA. Caso distinto, não exceção ao caso decidido.

**Fronteiras (não confundir).** D-ARQ-64 — intocada: alias resolve EXATA, o veto de fuzzy não incide; `vibracao_mao_braco` segue fora da allowlist por ser slug carregado. D-ARQ-67 — o contrato código↔dado segue verificado por teste computado; esta decisão trata do lado do dado. D-ARQ-14 — termo sem candidato segue `vocabulario_ausente`. D-ARQ-50 P2 — mecanismo de busca inalterado.

**Caso-âncora:** `vibracao_mao_braco` no Fascino, 9 GHEs, com efeito de conduta medido em GHE-12 (audiometria que não existia na matriz). Índice 106 → 112, zero colisão, 4 pares fuzzy inalterados — medido pelo Arquiteto antes do prompt e reconfirmado na sessão.

**Universalidade (D-ARQ-06).** A assimetria slug × grafia natural não é privilégio da vibração nem da construção civil: qualquer família cujo slug elida preposição, artigo ou plural cai no mesmo caso, em qualquer setor.

**Base.** Sessão 003.EJ. Literal da NR-09 Anexo I conferido no PDF oficial (gov.br/trabalho-e-emprego, `nr-09-atualizada-2026.pdf`, Portaria MTP 426/2021). Nenhuma R-* criada ou alterada.

## D-ARQ-71 — Perna `Ausente` absorvida por `ou` verdadeiro gera pendência não-bloqueante anexada à linha; o tri-estado não se move

**Contexto.** 003.EJ mediu no Fascino que GHE-16 passou de PARCIAL a VÁLIDA ao resolver o alias de vibração (D-ARQ-70), sem previsão do Arquiteto. O mecanismo: R-AUD-02 é `ou: [ruido_acima_acao, e(ruido, ototoxico, vibracao_qualquer)]`; com `vibracao_qualquer` resolvendo `True`, a perna `ruido_acima_acao` — que resolve `Ausente` (ruído sem laudo) — é absorvida pelo curto-circuito do `ou`. A `Pendencia` some; o tri-estado de D-ARQ-31 computa sobre pendências e linhas, não sobre `predicados_avaliados`. Resultado: matriz VÁLIDA com lacuna ambiental real registrada dois campos ao lado. Conduta emitida CORRETA (a audiometria é devida de qualquer forma); o que falha é a visibilidade — classe D-ARQ-22 (erro silencioso plausível). Registrado como DT-003EJ-02 `[A DECIDIR]`, decisão de arquitetura própria.

**Achado que dimensiona a decisão `[MEDIDO — leitura de disco, 003.EK]`.** A DT afirmava que "a informação já está disponível no ponto da avaliação". Só parcialmente: no ramo `ou` de `avaliar` (`predicados.py`), o loop acumula `primeiro_ausente_ou` e o descarta ao dar `return True`. A perna `Ausente` só existe como valor se avaliada ANTES do primeiro `True`. No caso-âncora funciona por acidente de ordem — `ruido_acima_acao` é a primeira perna de R-AUD-02. Trocada a ordem no YAML, a mesma lacuna sumiria. Correção ordem-dependente reprova em D-ARQ-06.

**Decisão — 3 cláusulas.**

1. **Detecção em passada de diagnóstico separada, que atravessa predicado composto nomeado.** `avaliar`/`avaliar_predicado` permanecem intocados — preguiça do `ou` preservada (nota 002.D2 de D-ARQ-10). Função nova (`pernas_ausentes_absorvidas`) reavalia sem curto-circuito, só nas regras que EMITIRAM, e desce em `protocolo.predicados_compostos` quando a perna é uma string que nomeia composto — com guarda de ciclo estrutural própria. Sem a expansão, a detecção seria profundidade-dependente: R-VIB-02 (`quando: vibracao_qualquer`) e R-AUD-02 citam o composto por NOME, e as duas pernas de `vibracao_qualquer` podem resolver `Ausente`. Efeito colateral declarado e desejado: as pernas antes não alcançadas passam a aparecer em `MatrizGHE.predicados_avaliados`. `e`/`nao` só recorrem — seu próprio `Ausente` já propaga e vira pendência bloqueante pelo caminho existente.
2. **Pendência não-bloqueante, anexada à linha.** `tipo="perna_ausente_absorvida"`, `exames_alvo` = slugs de `regra["emite"]`. `anexar_pendencias` (D-ARQ-31 fatia 3) passa a anexar por match de âncora independentemente da polaridade. O requisito de segurança piso-sem-teto continua valendo só para bloqueante — a linha já é válida com ou sem a não-bloqueante.
3. **O tri-estado não se move.** `tem_anexada` passa a contar apenas anexadas BLOQUEANTES. Sem esse fix, a cl.2 derrubaria GHEs VÁLIDA para PARCIAL — o oposto do pretendido. GHE-16 segue VÁLIDA: a conduta está correta, a lacuna é de visibilidade. Rebaixar reintroduziria PARCIAL em massa por lacunas sem efeito clínico, diluindo o sinal — mesma lógica da cláusula 2 de D-ARQ-66.

**Fronteiras (não confundir).**

* D-ARQ-28 — NÃO é o veículo e NÃO fecha. D-ARQ-28 é trilho declarativo da regra para lembrete operacional; esta decisão é sinal do avaliador sobre perna absorvida. Mas ambas dependem do mesmo encanamento ausente (`emissao.py` só criava `Pendencia` no ramo `Ausente`, sempre bloqueante). DT-002Y-01 e DT-003EH-01 seguem esperando D-ARQ-28.
* D-ARQ-31 — preservado. Muda o conjunto de entrada de `anexar_pendencias` e o critério de `tem_anexada`; a cláusula 3 (anexação bloqueante) e a invariante piso-sem-teto ficam intactas.
* D-ARQ-10 — preservado. A preguiça do `ou` e o cache "caminho real de avaliação" não mudam; a passada de diagnóstico é separada e não altera valor de retorno.
* D-ARQ-54 — o consumidor desta decisão é o instrumento, não a produção. `resultado.matrizes` tem 1 consumidor no repo inteiro, `scripts/medicao_pgr.py` `[VERIFICADO — grep, 003.EK]`; `agente_medico/superficie/` não referencia `MatrizGHE` nem `ExameEmitido`. Coerente com o escopo declarado de D-ARQ-54 ("render de saída fica FORA — apresentação-de-saída, D-ARQ próprio"). Logo D-ARQ-71 faz o campo nascer correto ANTES de a apresentação-de-saída existir; não entrega visibilidade a leitor de produção, porque não há leitor de produção da matriz.

**Duplicação, decidida e não tratada.** A pendência nasce por REGRA, não por perna. Medido: em GHE-16 a mesma perna (`ruido_acima_acao`) gera 2 pendências, uma por R-AUD-01 e outra por R-AUD-02, ambas anexadas à mesma linha `audiometria` (dedup R-GHE-03). Manter por-regra: fundir por `(ghe_id, perna)` perderia `regra_origem`, que é o que D-ARQ-22 Parte B exige de cada sinal. Se o ruído tornar o relatório ilegível, vira DT própria.

**Universalidade (D-ARQ-06).** Expresso sobre a forma do predicado (`ou` com perna indeterminada), não sobre agente ou setor. Vale construção, química e saúde igualmente.

**Base.** Sessão 003.EK. Resolve DT-003EJ-02 e a faceta (b) de DH-003EJ-01. Commits `4f5c91f`, `cd39cb8`, `823d467`, `1894602`; merge `54637e4` (PR #275). Suíte 1001→1013→1019 passed, 6 skipped; `mypy --strict` delta-zero, 34 arquivos. Sem caso medido no acervo para a expansão de composto da cl.1 — no Fascino, GHE-16 tem `vibracao_mao_braco` qualificado e nenhum `vibracao` genérico, logo `vibracao_corpo_inteiro` resolve `False`, não `Ausente`. A cláusula é justificada por leitura de disco (R-VIB-02/R-AUD-02 citam `vibracao_qualquer` por nome), não por medição — registrado para não se confundir com regra exercitada.

## D-ARQ-72 — Apresentação-de-saída da matriz é superfície própria em `superficie/`, apresentação-pura herdando D-ARQ-54 P1; o status de validação da regra atravessa até `Motivo`

**Aviso de procedência.** O corpo abaixo é reconstrução do Arquiteto a partir do código em disco (`apresentacao_matriz.py`, `tipos.py`, `emissao.py`, mensagens de commit) — o prompt original de 003.EM não estava disponível ao redigir este fechamento.

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (fatias 0-2, sessão 003.EM).

**Contexto.** D-ARQ-54 fechou a confirmação-de-entrada (envelope + FDS) e deixou explicitamente fora de escopo: "render de saída (matriz tri-estado D-ARQ-31 + pendências) fica FORA — é apresentação-de-saída, D-ARQ próprio." Esta é essa D-ARQ. O render existia, mas inline em `scripts/medicao_pgr.py` — um harness de medição, com um único consumidor. Sem superfície própria, o critério de pronto do Marco 1 ("a coordenadora clínica valida a matriz de exames de saída") não tem sobre o que operar.

**Cláusulas.**

1. A apresentação-de-saída não toca o motor. `renderizar_matriz(matriz: MatrizGHE) -> list[str]` (`agente_medico/superficie/apresentacao_matriz.py`) é função pura sobre o resultado; lógica-de-domínio zero. Herda D-ARQ-54 P1 e preserva D-ARQ-09. Medido: status das matrizes do Fascino inalterado (3 VÁLIDA / 15 PARCIAL / 1 BLOQUEADA).
2. Mora em `superficie/`, não em `scripts/`. O harness (`scripts/medicao_pgr.py`) passa a ser consumidor do render, não dono. Extração byte-idêntica (fatia 1) — os 7 testes existentes de `tests/test_medicao_pgr.py` passaram sem alteração e sem teste novo, o que é o próprio gate da preservação `[VERIFICADO — git show d86de25:tests/test_medicao_pgr.py, 7 testes inalterados]`.
3. O status de validação da regra atravessa até `Motivo.status_regra` (`agente_medico/motor/tipos.py`), populado de `regra.get("status")` em `agente_medico/motor/estagios/emissao.py`. Fecha D-ARQ-22 Parte B no eixo que DH-003EI-01 faceta 2 registrava como descumprido: a saída passa a distinguir, por exame, o status da regra que o gerou.
4. Ordem de leitura da revisão: `INTERPRETADO` primeiro, `DERIVADO` depois, `VALIDADO` nunca entra no bloco "inspecionar primeiro" (`_STATUS_INSPECIONAR_PRIMEIRO` em `apresentacao_matriz.py:13`). Materializa a priorização que D-ARQ-22 Parte B descreve em prosa. Literal digitado em código sem teste computado do dado — registrado como DH-003EM-01, classe D-ARQ-67.

**Fronteiras (não confundir).**

* D-ARQ-54 — confirmação de entrada; esta é saída. Compartilham a postura apresentação-pura, não o artefato.
* D-ARQ-31 — o tri-estado é consumido pelo render, nunca recomputado.
* Escopo desta D-ARQ: markdown. Emissores Word/HTML no formato do escritório e app de upload são fatias futuras, fora daqui.

**Consequência.** A matriz ganha superfície própria — precondição do Marco 1, não o Marco 1. Nenhuma regra clínica criada ou alterada.

**Base.** Sessão 003.EM. Fatias 0-2, commits `9ca7372`, `d86de25`, `69d035e`. Fecha faceta 2 de DH-003EI-01; abre DH-003EM-01 e DH-003EM-02 (§11 do PROTOCOLO). Detalhe em HISTORICO 003.EM.

## D-ARQ-73 — Emissor de saída no formato do escritório: estrutura intermediária única com N renderizadores; expansão GHE→cargo é apresentação; ordem de exibição é dado cravado, não literal solto; cabeçalho/rodapé são seam humano

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (fatias 1-3, sessão 003.EO + EMENDA 1).

**Contexto.** D-ARQ-72 fechou a apresentação-de-saída em markdown de diagnóstico, para a
coordenadora clínica revisar regra a regra. Falta o documento que a Dra. Carolini efetivamente
assina — Word/HTML no formato que o escritório já usa (`matrizes_originais/*.doc(x)`), por
cargo, sem rastreabilidade. Medição da fatia 0 (relatório `003eo_gabarito_forma.md`, não
versionado): o gabarito Fascino (19 GHEs, 41 linhas de função) mostrou que a ordem de exibição
dos exames dentro da célula **não é constante** entre GHEs — dois GHEs administrativos (sem
exames laboratoriais) invertem a posição relativa de `Avaliação Psicossocial` e `Av. Médica de
Saúde Mental` frente ao template dos outros 17. Isso bloqueou a fatia 2 até decisão do
Arquiteto (EMENDA 1).

**Cláusulas.**

1. **Estrutura intermediária única, N renderizadores.** `DocumentoMatriz` (`CabecalhoDocumento`,
   `BlocoGHE`/`LinhaCargo`, `RodapeDocumento`) é dataclass frozen, pura, sem I/O
   (`agente_medico/superficie/documento_matriz.py`, D-ARQ-72 cl.2 — mora ao lado de
   `apresentacao_matriz.py`). `renderizar_html` e `renderizar_docx` consomem a MESMA estrutura;
   nenhum recalcula nada — só formatam.
2. **Expansão GHE→cargo é apresentação, não regra nova.** `montar_documento` replica a mesma
   tupla de células para cada cargo de `MatrizGHE.cargos` — herança pura, ancorada em R-GHE-01
   `[VALIDADO]` ("todas as funções dentro de um mesmo GHE recebem matriz idêntica") e em
   D-ARQ-21 (o agrupamento em GHE é canônico). GHE com `cargos == ()` emite bloco com
   `linhas == ()` — nunca inventa placeholder.
3. **Ordem de exibição é dado cravado no vocabulário, não literal solto no emissor.** Decisão do
   Arquiteto (EMENDA 1 a 003.EO): a inversão medida em 2 GHEs administrativos não é replicada —
   ordem de exames dentro da célula **não é conduta clínica** (nenhuma R-\*/NR a prescreve; o
   que a revisão de saída valida são os três invariantes de D-ARQ-22 Parte B: quais exames,
   quais momentos, qual periodicidade — não a ordem deles). Sob a hipótese "ruído de digitação"
   do gabarito, replicar a inversão reproduziria um artefato de edição; sob "padrão
   administrativo", o custo de não replicar é diferença cosmética **visível por construção**
   (a coordenadora vê e corrige em segundos) — o oposto do erro silencioso que D-ARQ-22 combate.
   A alternativa rejeitada — ordem como função do perfil do cargo — inventaria um eixo de dado
   sobre 2 observações do mesmo documento (viola D-ARQ-06, mesmo padrão do precedente
   R-PSY-02 que esperou o 2º PGR do acervo). Materializada como `ordem_exibicao: int` opcional
   em `agente_medico/protocolo/vocabulario/exames.yaml`, ao lado de `nome_exibicao` — mesma
   casa, mesma natureza de dado de apresentação; só os slugs medidos na sequência majoritária
   (17/19 GHEs) o carregam, os demais saem depois em ordem alfabética de slug (fallback do
   emissor, D-ARQ-67: guardado por teste de unicidade computado do yaml + teste de que o
   fallback nunca usa sentinela que suba o exame sem ordem para o topo).
4. **Mapa `Momento→rótulo` do escritório é literal guardado por teste computado do enum**
   (D-ARQ-67, precedente DH-003EM-01): `test_mapa_momentos_cobre_todos_os_membros_do_enum`
   computa `set(Momento)` e afirma cobertura total — `Momento` novo quebra o teste, não some
   da célula em silêncio.
5. **Cabeçalho/rodapé são parâmetro do emissor, nunca derivados de `MatrizGHE`/`Resultado`.**
   Medição da fatia 0: nenhum tipo do motor carrega razão social, nome de obra ou tipo de
   documento (Obra Nova/Atualização/Adendo/Funções Iniciais). Isto é lacuna real, não dívida a
   fechar aqui — mesma classe de seam humano de D-ARQ-53 P2 (confirmação-RT); registrada como
   DT-003EO-01, não-bloqueante.
6. **Sanitização de controle na renderização, nunca no dado.** Cargo/nome-de-GHE verbatim do
   PGR pode carregar bytes NUL (glifo de CBO quebrado, mesma origem de DT-003DR-01/DH-003EG-01
   — medido no Fascino, 19/19 GHEs). `documento_matriz.py` sanitiza controle ASCII só na
   formatação de célula/cargo/título — `MatrizGHE.cargos` permanece verbatim, é evidência,
   como DH-003EG-01 já prescrevia como correção candidata.

**Fronteiras (não confundir).**

* D-ARQ-72 — render de diagnóstico (markdown, rastreabilidade completa, consumida pela revisão
  regra-a-regra). D-ARQ-73 é o documento limpo que a médica assina — a rastreabilidade fica
  DE FORA por decisão do Arquiteto (§S2.4 do `docs/PLANO_V1.md`): misturar atrapalha a
  validação em vez de ajudar. Compartilham a postura apresentação-pura, D-ARQ-54 P1, não o
  artefato nem o público.
* D-ARQ-54 — confirmação de entrada (envelope + FDS); esta é emissão de saída.
* D-ARQ-21/R-GHE-01 — a expansão GHE→cargo CONSOME a garantia (matriz idêntica por GHE); não a
  recomputa nem a reinterpreta.
* Escopo desta D-ARQ: HTML + DOCX no formato do escritório. App de upload (S3 do
  `docs/PLANO_V1.md`) e hospedagem (S0) são fatias futuras, fora daqui.

**Consequência.** Achado de granularidade (fora do previsto, medido na fatia 4 contra o
Fascino real): `GHEPGR.cargos` chega do parser da família Consciente
(`parser_familia_consciente.py`, D-ARQ-65 fatia 1) como UM elemento por GHE — a linha inteira
da coluna Cargo/Função, verbatim, não uma lista de cargos individuais (decisão já documentada
no código: "separação fina de CBO/cargo individual não é desta fatia"). A expansão GHE→cargo
desta D-ARQ está correta para o dado que recebe; com um único elemento, produz uma única linha
— a forma visual do gabarito (uma linha por cargo) só se realiza quando o parser da família
entregar cargos separados. Registrado como DT-003EO-04, não-bloqueante, candidato natural da
fatia 2 do roteamento de D-ARQ-65 (que já precisa tocar o parser). Nenhuma regra clínica criada
ou alterada nesta D-ARQ.

**Base.** Sessão 003.EO + EMENDA 1 (01/08/2026). Fatia 0 (medição, bloqueou fatia 2 original);
EMENDA 1 do Arquiteto resolveu ordem_exibicao e corrigiu a medição de contagem de cargos do
prompt original (41 linhas reais, não 37 — causa nomeada no parser do Arquiteto, não no Code).
Detalhe em HISTORICO 003.EO.

**Nota de aplicação (sessão atual, branch `claude/youthful-lamport-3kfkog`) — estilo visual do
`.docx` portado do legado.** `renderizar_docx` ganha borda de tabela (`Table Grid`), cabeçalho
de coluna com fundo e texto brancos, e título/cabeçalho de GHE em cor de destaque — técnica
portada de `modules/modulo_pcmso.py::gerar_docx_rq61` (v9.5, legado, já em produção), sem trazer
nome nem identidade visual de terceiro (pedido explícito do Diovanni): a cor reaproveitada é só
a paleta que o legado já usa, trocável em um lugar só. Nenhuma cláusula desta D-ARQ alterada —
cl.1 (estrutura única/N renderizadores) e cl.2 (expansão GHE→cargo) intocadas; `montar_documento`
e `DocumentoMatriz` sem uma linha tocada, só `renderizar_docx` (função de renderização pura).
Correção de leitura própria desta sessão: o escopo inicial cogitava reusar também o merge
vertical de célula por Cargo do legado — não se aplica à forma atual, que já emite **um cargo por
linha** (não um cargo repetido por exame-linha, como o legado); não há célula repetida para
mesclar. `renderizar_html` inalterado. 3 testes novos com reversão nomeada (estilo de tabela,
sombreado+cor do cabeçalho de coluna, cor do título/cabeçalho de GHE), 3/3 confirmadas por
varredura inversa. Verificação visual: pipeline real (PDF Fascino, 19 GHEs) renderizado a `.docx`
e convertido a PDF via `soffice --headless`, páginas inspecionadas como imagem — sem defeito de
layout introduzido. Nenhuma `R-*` criada, alterada ou depreciada; `PROTOCOLO_AGENTE_MEDICO.md`
inalterado (não há regra clínica tocada).

## D-ARQ-74 — Superfície que emite artefato assinável lê o status do Resultado e nunca emite documento sem conteúdo clínico

**Status:** DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (sessão 003.EQ). Não cria nem altera
regra clínica.

**Contexto — caso-âncora medido.** A fatia 1 do S3 (`superficie/web_matriz.py`) tratava
apenas `resultado is None` como falha. O gate eliminatório de R-PGR-01 produz
`Resultado(status="REJEITADO", matrizes=[])` (`orquestrador.py:42-51`) — que **não é
None**. Consequência medida em dois ambientes independentes (sandbox do Code e host do
Diovanni): a tela renderizou as 154 pendências de extração, ofereceu os dois downloads,
e produziu `matriz.html` de **187 bytes** e `matriz.docx` com **zero `<w:tbl>`** — só
cabeçalho e rodapé, incluindo nome e CRM da médica. Um documento assinável, sem uma
única linha de exame e sem um único aviso.

A informação existia e estava carimbada: o motor emitiu
`Pendencia(tipo="assinatura_invalida", regra_origem="R-PGR-01")` com o motivo literal
"PGR não assinado por engenheiro de segurança do trabalho (NR-18)". A superfície a
descartou — iterava `pend_forma + pend_hidr` e nunca `resultado.pendencias_globais`.
Quarta ocorrência da classe "o dado existe, o consumidor não lê" (`R-RX-01-sem` 003.EH,
`R-GHE-02` 003.EP, `anexo_nr07` 003.AB, esta).

**Decisão — 4 cláusulas.**

1. **Status do `Resultado` é contrato de superfície, não detalhe interno.** Toda
   superfície que emite artefato destinado a assinatura lê `resultado.status`.
   `REJEITADO` é parada dura: nomeia o motivo de cada pendência bloqueante e não emite
   documento nem oferece download.
2. **`pendencias_globais` são renderizadas sempre, em bloco próprio, antes das
   pendências de extração.** Materializa D-ARQ-08 ("pendências bloqueantes têm
   prioridade visual") na superfície. O caso-âncora mostra por quê: 154 pendências de
   vocabulário afogaram a única que decidia a emissão.
3. **Guarda anti-documento-vazio, independente do gate.** Documento sem nenhuma
   `LinhaCargo` não é oferecido para download, qualquer que seja o status. A guarda é
   sobre o artefato, não sobre a causa — um caminho futuro que zere as linhas por outro
   motivo cai nela também.
4. **Estado rejeitado não entra em cache.** Cache de resultado caro não pode mascarar
   `REJEITADO` num rerun subsequente.

**Consequência.** Superfície é apresentação-pura (D-ARQ-54 P1), mas apresentação-pura
não significa cega ao status: descartar o campo que decide se o artefato pode existir é
lógica de domínio por omissão. A regra vale para `apresentacao_matriz.py`,
`documento_matriz.py` e qualquer emissor futuro — verificar na próxima sessão que os
tocar. `[A MEDIR — os outros emissores não foram auditados nesta sessão]`

**Universalidade (D-ARQ-06).** Independe de setor: qualquer PGR reprovado em gate
eliminatório, em qualquer ramo, produzia o mesmo artefato vazio.

**Base.** Sessão 003.EQ, commit `4b0a541`. Testes 10a-10c em
`agente_medico/tests/test_web_matriz.py`, cada um com reversão nomeada e confirmada
vermelha. Achado originado da verificação manual do Diovanni — não da suíte, que
permanecia 1059 verde com o defeito vivo.

## D-ARQ-75 — Hospedagem por consumo, não por tier; autenticação é gate com allowlist própria; o que sobe é o app novo, com dependências medidas

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.ER, sem código de motor. Fecha o §S0 do `docs/PLANO_V1.md`. Implementação é 003.ES,
por fatias. (O marcador `**Status:**` fica sozinho na linha e sem ponto final de propósito: o
gerador do índice trunca o status no primeiro `.`, e "DECISÃO DE ARQUITETURA (sessão 003" é
como D-ARQ-72/73/74 aparecem hoje — evitável.)

**Contexto — o que a medição derrubou.** O §S0 do `PLANO_V1` recomendava, desde 05/08/2026,
"hospedar em nuvem paga de piso ~2 GB", com o pico de RAM marcado `[A MEDIR]` e estimado em
~450-500 MB por extrapolação de sandbox. A medição direta do caminho de produção derruba as
duas coisas.

`executar_rota_determinista` completo sobre o PGR Fascino (10,4 MB, 119 páginas), saída correta
(19 GHEs, 41 cargos, HTML de 16.768 bytes, 154 pendências): **128,5s, pico RSS 904 MB**.
`parsear_arquivo` isolado: **64,9s, 731 MB** — a diferença é `extrair_texto_pgr` relendo o mesmo
arquivo, segunda leitura declarada por construção na nota de aplicação 003.EA de D-ARQ-65.
`[MEDIDO — 003.ER, sandbox Linux, 05/08/2026; tempo é indicativo (hardware difere), memória é
mais transferível — mesma ressalva do bloco original do S0]`

Consequência: 2 GB não é piso confortável, é o teto de **um** usuário — 904 MB de pico mais
~150-250 MB de runtime Streamlit. E Python não devolve arena ao SO depois do pico, então o
processo permanece com RSS alto mesmo ocioso.

**Decisão — 4 cláusulas.**

1. **Provedor cobrado por consumo, nunca por tier de RAM fixa.** Com pico medido de 904 MB num
   documento de 10,4 MB, escolher um tier é apostar no maior PGR que ainda não chegou. Railway,
   plano Hobby: RAM $10/GB/mês, CPU $20/vCPU/mês, subscrição $5/mês com $5 de uso incluído,
   teto de 48 GB por serviço. `[DERIVADO — docs.railway.com/pricing/plans, conferido
   05/08/2026]` Custo esperado ~$10-15/mês `[APROXIMADO — aritmética do Arquiteto sobre as
   tarifas oficiais, conferir na primeira fatura]`. Render descartada pelo modelo, não pelo
   preço; os valores de tier da Render `[APROXIMADO — não verificado em fonte primária]`.
   Streamlit Community Cloud segue fora: 1 GB de limite. `[A CONFIRMAR — a página
   `deployments/serverless` da Railway não foi lida; se houver scale-to-zero aplicável, o custo
   cai. Não é pré-requisito.]`

2. **Autenticação é gate de duas partes, e a segunda é código nosso.** `st.login()` com client
   OIDC **do projeto**, não do tenant do cliente — usar o Workspace do cliente exigiria que a TI
   dele criasse e autorizasse o OAuth client, que é a mesma barreira organizacional que reverteu
   a recomendação local em 05/08. Três cláusulas subordinadas, todas obrigatórias:

   - **(a) Allowlist é gate, não refinamento.** A doc oficial é explícita: *"OIDC supports
     authentication, but not authorization"* `[DERIVADO —
     docs.streamlit.io/develop/concepts/connections/authentication, conferido 05/08/2026]`. Com
     provider Google e client próprio, **qualquer conta Google do mundo completa o login**. A
     autorização é lista de e-mails no app. Sem ela o app está aberto.
   - **(b) O gate roda antes de qualquer consumo.** Padrão da doc — `if not
     st.user.is_logged_in: ...; st.stop()` — no topo de `pagina_matriz()`, **antes** do
     `st.file_uploader`. Do contrário um não-autorizado dispara os 904 MB.
   - **(c) Segredo nunca em arquivo versionado.** `.gitignore` cobre `.streamlit/secrets.toml`
     desde 003.ER (fatia 0), antes de o arquivo existir. Os valores vivem em variáveis de
     ambiente do provedor. `[A CONFIRMAR — a doc do `st.login` só documenta `secrets.toml`
     como fonte; se ele não ler variável de ambiente, o entrypoint do container materializa o
     arquivo em runtime a partir das env vars.]`

   **Risco aceito e nomeado:** o cookie de identidade do Streamlit expira em **30 dias e não é
   configurável** `[DERIVADO — mesma fonte]`. Mitigação existe (ler a expiração do provider em
   `st.user` e chamar `st.logout()`); fica de fora da V1 por decisão do Diovanni, registrada,
   não esquecida.

3. **O deploy usa `requirements-app.txt` enxuto, não o `requirements.txt` da raiz.** Varredura de
   `motor/` + `superficie/` + `adaptadores/`: os únicos terceiros importados são **`streamlit`,
   `pdfplumber`, `PyYAML`, `python-docx`, `requests`**. Ficam fora `pandas`, `numpy`,
   `opencv-python-headless`, `PyMuPDF`, `pytesseract`, `pdf2image`, `supabase`, `rapidfuzz` (o
   Levenshtein é próprio, `resolvedor_termos.py:85`) e `google-generativeai` (os transcritores
   Gemini falam HTTP direto via `requests`). O `requirements.txt` atual é do legado Streamlit;
   subir com ele infla imagem e baseline de RAM sem servir a uma linha do app novo. **O pin
   precisa de piso que garanta `st.login`** — `>=1.35.0` permite resolver para versão sem o
   comando, e a falha apareceria só no deploy. `[A CONFIRMAR — a doc não declara a versão de
   introdução de `st.login`; conferir no changelog antes de cravar o número. Medido: o host do
   Diovanni roda 1.56.0, DH-003EQ-01.]`

   **Correção de método, registrada (D-ARQ-06).** A primeira varredura do Arquiteto usou
   `grep "^import"` — cego a import indentado, e `web_matriz.py:186` importa `streamlit` dentro
   de `pagina_matriz()`. O conjunto de cinco sobreviveu à correção do instrumento, mas por
   coincidência: uma dependência lazy exótica teria passado e quebrado só em produção. Classe
   DH-003EC-01(a) — instrumento verde sobre buraco.

4. **128s é entrega, com o feedback que já existe.** `web_matriz.py` já tem
   `st.spinner("Processando PGR — o parse do PDF pode levar alguns minutos...")` em volta da
   chamada cara `[MEDIDO — 003.ER, leitura de disco]`. O que não existe é progresso incremental,
   e para um parse opaco de 128s o spinner pode bastar. A **leitura única do PDF** (corta a
   segunda passada, ~metade do tempo e provável queda do pico) é dívida nomeada com fatia
   própria e medida, **depois** do deploy — irmã de DH-003EC-02.

**Medições que inocentaram riscos levantados (registradas para não voltarem como hipótese).**
`CacheMatrizes` em `st.session_state` serializa em **72 KB** (matrizes 44 KB, vocabulário
7,6 KB, pendências 19,5 KB) — footprint por sessão é ruído, não risco de RAM. O PDF do cliente
**não** fica em disco: `pagina_matriz()` usa `tempfile.TemporaryDirectory()` como context
manager, e o `renderizar_docx` acontece dentro dele. `[MEDIDO — 003.ER]`

**Universalidade (D-ARQ-06).** Hospedagem e autenticação independem de setor — construção civil,
indústria química e saúde sobem o mesmo PDF na mesma tela, sob o mesmo gate.

**Fronteiras (não confundir).**

* **D-ARQ-09 / D-ARQ-48** — preservadas: a auth é borda de I/O na casca, em `superficie/`. O
  invariante de `test_pureza_motor.py` (nenhum módulo de `motor/` importa `streamlit`) segue
  intacto, e o núcleo puro por seam continua sem ver a autenticação.
* **D-ARQ-54 P1** — apresentação-pura preservada: a allowlist é controle de acesso, não juízo de
  domínio. Nenhuma regra clínica se move para a superfície.
* **D-ARQ-74** — intacta. A guarda anti-documento-vazio segue valendo, e o `[A MEDIR]` dela
  (auditar `apresentacao_matriz.py` e `documento_matriz.py`) continua aberto, não é desta
  decisão.
* **D-ARQ-65** — a segunda leitura do PDF é propriedade declarada da nota 003.EA, não defeito
  novo; esta decisão a mede e a adia, não a revoga.
* Não toca motor, protocolo clínico nem vocabulário. **Nenhuma R-* criada ou alterada.**

**Base.** Sessão 003.ER (05/08/2026), ARQUITETURA. Gate de abertura cumprido e declarado.
Origem: os dois `[A DECIDIR]` do §S0 do `PLANO_V1` (escopo de acesso; mecanismo de auth) e o
`[A MEDIR]` de RAM. Respostas do Diovanni: acesso **também fora do escritório**; **não vincular
ao tenant corporativo**; **deploy agora**, leitura única depois. Correção de premissa registrada:
o Diovanni justificou o não-vínculo por "tem que funcionar em qualquer lugar" — `st.login`
autentica a pessoa, não a rede, e funcionaria de qualquer lugar com tenant corporativo; a razão
que sustenta a decisão é a dependência de TI de terceiro, não a mobilidade. Segunda passada
crítica (a pedido do Diovanni) produziu sete achados sobre a primeira versão desta decisão,
todos incorporados acima — o mais grave, a ausência de `.streamlit/secrets.toml` no `.gitignore`,
virou a fatia 0 e pré-requisito da fatia de auth.

**Nota de aplicação — 003.ES.** Os três `[A CONFIRMAR]` desta decisão estão resolvidos, e a
cláusula 2(b) foi superada em parte por D-ARQ-76 (o gate mora no entrypoint, não em
`pagina_matriz()`; razão medida lá).

* Versão de introdução de `st.login` — CONFIRMADA: 1.42.0. `[DERIVADO —
  docs.streamlit.io/develop/quick-reference/release-notes/2025, conferido 08/08/2026]` O pin de
  `requirements-app.txt` é `streamlit>=1.42.0,<2.0.0`, guardado por teste próprio
  (`test_piso_de_streamlit_garante_st_login`) — sem ele, rebaixar o piso não deixaria nada
  vermelho e a quebra apareceria só no deploy.
* `st.login` e variável de ambiente — RESOLVIDO pelo lado negativo. A doc de secrets documenta o
  fluxo `secrets.toml` → variáveis de ambiente (segredos de nível raiz viram env vars), nunca o
  contrário, e acessar segredo sem o arquivo levanta `FileNotFoundError` `[DERIVADO —
  docs.streamlit.io/develop/concepts/connections/secrets-management, conferido 08/08/2026]`. Não
  há caminho documentado de env var → `[auth]`. O materializador de `secrets.toml` no entrypoint
  do container deixa de ser plano B e vira o caminho da fatia de deploy. Ressalva honesta: a doc
  não afirma que env var não funciona; ausência de documentação não é prova de ausência de
  suporte. Projetar contra o documentado é a escolha.
* Scale-to-zero da Railway — CONFIRMADO que existe. Serviço dorme após 10 min sem tráfego
  outbound (inbound não conta), sem cobrança de compute enquanto dorme; habilitado em
  Settings → Deploy → Serverless `[DERIVADO — docs.railway.com/reference/app-sleeping, conferido
  08/08/2026]`. Um app que só responde a upload não emite outbound e deve dormir bem.
* Achado que a fatia 3 herda: o `secrets.toml` per-project é descoberto em `$CWD/.streamlit/`,
  onde `$CWD` é a pasta de onde o Streamlit foi executado — o mesmo vale para o `config.toml` já
  versionado (tema, `maxUploadSize = 50`). O start command precisa rodar com CWD na raiz do repo.

**Nota de aplicação — 003.ET. A premissa dos 904 MB (cláusula 1) foi refutada por medição.** O
pico não é propriedade do documento nem do pipeline — é **cache de página do pdfplumber nunca
liberado**. Com `Page.close()` chamado por página (helper `paginas_liberadas`,
`motor/io_pdf.py`), o e2e do Fascino cai de **859 MB para 103 MB** (sandbox Linux) e de
**674,3 MB para 114,8 MB** (host Windows, `psutil.Process().memory_info().peak_wset`), com saída
idêntica nos dois ambientes (`PRELIMINAR`, 19 matrizes, 154 pendências).
`[MEDIDO — 003.ET fatia 2, 09/08/2026]`

Medição adicional que muda o desenho de quem for corrigir isso em outro lugar: `flush_cache()`
sozinho deixa **398 MB**; `close()` sozinho entrega **88 MB**; chamar os dois equivale a `close()`
sozinho. Um teste que espionasse só `flush_cache` ficaria verde sobre a implementação errada.

**Consequência.** O descarte do Streamlit Community Cloud (limite de 1 GB) e a estimativa de
~$10-15/mês da cláusula 1 pendiam do número de 904 MB. Com o app na faixa de 250-350 MB somando o
runtime do Streamlit, hospedagem gratuita volta à mesa. A cláusula 1 **não é revogada nesta
sessão** — o destino do deploy é decisão de sessão própria, com o número medido em mãos (nota em
`docs/PLANO_V1.md` §S0).

**Erro de método registrado (D-ARQ-06).** 003.ER mediu o sintoma (pico de RAM) e concluiu sobre o
provedor sem investigar a causa; o Arquiteto leu essa decisão integralmente no gate de abertura de
003.ET e repetiu a conclusão sem questioná-la. A pergunta que faltava — "por que consome isso?" —
custou dois comandos de medição, e foi disparada por uma pergunta do Diovanni sobre custo, não por
revisão do Arquiteto. Regra derivada: número de consumo que vai fundamentar decisão de
arquitetura exige a pergunta pela causa antes de virar premissa.

## D-ARQ-76 — O gate de acesso mora no entrypoint; a decisão é núcleo puro; a fronteira do provedor de identidade normaliza antes de decidir

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.ES, fatias 1 e 2. Nasce da implementação de D-ARQ-75 e supersede em parte a cláusula
2(b) daquela decisão. Nenhuma regra `R-*` criada, alterada ou depreciada.

**Contexto — o que a medição derrubou.** D-ARQ-75 cláusula 2(b) prescrevia o gate "no topo de
`pagina_matriz()`, antes do `st.file_uploader`". Duas medições da 003.ES tornaram a letra
impraticável e a intenção alcançável por outro caminho.

Medição 1 (sonda de harness). `st.user.is_logged_in` não existe quando a autenticação não está
configurada — "For a locally running app, this attribute is only available when authentication
(`st.login()`) is configured in `secrets.toml`. Otherwise, it does not exist"
`[DERIVADO — docs.streamlit.io/develop/api-reference/user/st.user, conferido 08/08/2026]`.
Injetar `at.secrets["auth"]` no `AppTest` não faz o atributo passar a existir: o `AttributeError`
é idêntico com e sem a injeção `[MEDIDO — 003.ES, streamlit 1.56.0]`. Leitura: o bloco `[auth]` é
consumido na subida do servidor, e `AppTest` não sobe servidor. Não há caminho de injeção de
identidade pelo harness — os atributos expostos são `secrets`, `session_state` e `query_params`.
Consequência: com o gate dentro de `pagina_matriz()`, os quatro testes de casca de
`test_web_matriz.py` (entregues verdes em 003.EQ) parariam no login sem conserto disponível.

Medição 2 (tipo na fronteira). `UserInfoProxy` tipa `__getattr__`/`.get()` como
`str | bool | TokensProxy | None`, sem propriedade tipada para `is_logged_in`
`[MEDIDO — 003.ES, `streamlit/user_info.py`, 1.56.0]`. `st.user.is_logged_in` nunca chega como
`bool`, nem `st.user.get("email")` como `str | None`.

**Decisão — 4 cláusulas.**

1. **O gate roda no entrypoint da raiz, não na página.** `app_matriz.py` decide o acesso antes de
   chamar `pagina_matriz()`. A intenção de D-ARQ-75 2(b) — nada consome os 904 MB do parse antes
   do gate — fica preservada: o entrypoint é o único caminho de produção desde a fatia 1 desta
   mesma sessão. O que muda é o lugar, não a garantia. Custo aceito e nomeado: superfície web
   futura precisa chamar o gate explicitamente; a proteção não é mais por construção da página.
2. **A decisão de acesso é núcleo puro, com três desfechos explícitos.**
   `superficie/autorizacao.py`: `GateAcesso` (`PEDIR_LOGIN`/`NEGAR`/`LIBERAR`),
   `carregar_allowlist`, `esta_autorizado`, `decidir_acesso`. Nenhuma delas importa `streamlit`
   nem lê `os.environ` — `decidir_acesso` recebe `esta_logado: bool`. É isso que torna a decisão
   testável sem harness, e é a razão de a lógica ter saído da casca: a parte alcançável por teste
   passou a ser a parte que decide. Molde de `web_matriz.py` (núcleo puro + casca fina),
   D-ARQ-54 P1.
3. **A fronteira normaliza estritamente, e é fail-closed.** A casca converte antes de chamar o
   núcleo: `st.user.is_logged_in is True` (não `bool(...)`) e `isinstance(bruto, str)` para o
   e-mail. Qualquer valor que não seja o literal `True` é não-logado; o que não for `str` vira
   `None`, que a allowlist já nega. `cast` e `# type: ignore` foram rejeitados — mentem para o
   verificador exatamente na fronteira de segurança, que é onde ele deve incomodar. Mudar a
   assinatura de `decidir_acesso` também foi rejeitado: o núcleo puro não absorve o desleixo de
   tipo de biblioteca externa. Ganho não previsto: a fronteira passou a ser fail-closed por
   construção, não por confiança no provedor.
4. **A allowlist vem de variável de ambiente, não de `st.secrets`.** `PCMSO_ALLOWLIST`, e-mails
   separados por vírgula, lida por `os.environ`. A allowlist é código nosso e não deve depender
   do materializador de segredo do provedor (fatia 3). Lacuna consciente: nenhum teste crava o
   nome da variável — trocá-lo não deixa nada vermelho. Aceita porque o modo de falha é
   fail-closed e imediatamente visível: variável errada = allowlist vazia = ninguém entra,
   inclusive quem testa. Não é app aberto por engano.

**Universalidade (D-ARQ-06).** Acesso e identidade independem de setor — construção civil,
indústria química e saúde entram pelo mesmo gate, com a mesma allowlist.

**Fronteiras (não confundir).**

* D-ARQ-75 cláusula 2(b) — superada em parte por esta decisão, apenas quanto ao lugar do gate.
  As cláusulas 2(a) (allowlist obrigatória, OIDC autentica mas não autoriza) e 2(c) (segredo fora
  do git) seguem íntegras, assim como as cláusulas 1, 3 e 4 de D-ARQ-75.
* D-ARQ-09 / D-ARQ-48 — preservadas: a auth é borda de I/O na casca. O invariante de
  `test_pureza_motor.py` segue intacto e `superficie/autorizacao.py` não importa `streamlit`.
* D-ARQ-54 P1 — preservada: a allowlist é controle de acesso, não juízo de domínio. Nenhuma regra
  clínica se move para a superfície.
* D-ARQ-74 — intacta. A guarda anti-documento-vazio segue valendo, a jusante do gate.
* Não toca motor, protocolo clínico nem vocabulário.

**Base.** Sessão 003.ES (08/08/2026), IMPLEMENTAÇÃO. Duas sondas com bloqueador reportado pelo
Code e resolvido pelo Arquiteto, no procedimento previsto. Suíte 1066 → 1074 passed, 6 skipped;
`mypy --strict` limpo, 45 arquivos.

## D-ARQ-77 — Mecanismo de build é o Dockerfile; o segredo é materializado antes do servidor

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.ET, fatia 1. Implementa o mecanismo de deploy adiado por D-ARQ-75/76. Nenhuma regra
`R-*` criada, alterada ou depreciada.

**Contexto.** D-ARQ-75/76 decidiram provedor, autenticação e o lugar do gate; nenhuma das duas
decidiu como o build efetivamente empacota e sobe o app. O repositório tem, na raiz, `app.py` e
`requirements.txt` do legado — o app Streamlit anterior ao app novo (`app_matriz.py`,
`requirements-app.txt`). Sem mecanismo declarado, a detecção automática do builder decide por
convenção, e a convenção favorece o legado.

**Decisão — 4 cláusulas.**

1. **Dockerfile decide o build, não a detecção do builder.** O builder vigente da Railway é o
   **Railpack** (não Nixpacks) `[DERIVADO — docs.railway.com/builds/build-configuration,
   conferido 08-09/08/2026]`. Ele detecta Python por `main.py`/`app.py`/`start.py`/… ou por
   `requirements.txt`/`pyproject.toml`/`Pipfile`, instala com `requirements.txt` via pip, e
   escolhe o start command pelo primeiro arquivo da mesma lista `[DERIVADO —
   railpack.com/languages/python, conferido 08-09/08/2026]`. Com `app.py` e `requirements.txt`
   do legado na raiz, um deploy sem Dockerfile instalaria as 14 dependências do legado e subiria
   o app legado — dois erros silenciosos, com o serviço reportando saudável. `Dockerfile` na raiz
   (nome exato, D maiúsculo) é detectado e usado, e passa a decidir o build no lugar da detecção
   `[DERIVADO — docs.railway.com/builds/dockerfiles]`. `agente_medico/`, `app_matriz.py` e
   `.streamlit/` são copiados explicitamente; o legado nunca entra na imagem.

2. **O materializador de segredo é start command de shell, antes do `streamlit run`.**
   `app_matriz.py` lê `st.user.is_logged_in` na primeira linha executável do gate (D-ARQ-76), e o
   atributo só existe com o bloco `[auth]` configurado — consumido na subida do servidor (medição
   1 de D-ARQ-76). Materializar o segredo em Python dentro do próprio app chegaria tarde demais:
   o `AttributeError` já teria acontecido. A forma escolhida é núcleo puro
   (`gerar_toml_auth` em `agente_medico/superficie/materializar_secrets.py`, sem I/O, lê o
   `Mapping` que a casca fornece) mais uma casca fina lendo `os.environ` e escrevendo
   `.streamlit/secrets.toml`, chamada por um `entrypoint.sh` de três linhas antes do
   `exec streamlit run` — mesmo molde de D-ARQ-76 cláusula 2 (núcleo puro + casca fina), e também
   porque a suíte deste projeto roda em host Windows, onde um teste que exercitasse o shell em si
   seria pulado por `skipif` (classe DH-003ES-01); `test_deploy_artefatos.py` cobre o núcleo puro
   e a ordem textual das linhas do `entrypoint.sh`, nunca a execução do shell.

3. **`PCMSO_ALLOWLIST` não entra no `secrets.toml`.** Preserva D-ARQ-76 cláusula 4 — a allowlist
   é código nosso, lida direto de `os.environ`, sem depender do materializador de segredo do
   provedor de identidade.

4. **O `requirements.txt` do legado permanece.** O legado é território "não tocar" (D-ARQ-09/48
   preservadas fora de `motor/`); a coexistência dos dois `requirements*.txt` na raiz deixa de
   importar no momento em que o Dockerfile, não a detecção, decide qual deles o build usa.

**Razão que sustenta a decisão, e é o ponto.** O builder da Railway trocou de Nixpacks para
Railpack entre a escrita de D-ARQ-75 (05/08/2026) e a implementação desta fatia (08/08/2026).
Apoiar a cláusula 3 de D-ARQ-75 (deploy do app novo) numa heurística de detecção de builder que
muda sem aviso é, na infraestrutura, o mesmo erro que D-ARQ-65 cláusula 2 rejeitou na extração:
caminho crítico refém de comportamento de terceiro não travado por contrato.

**Universalidade (D-ARQ-06).** O mecanismo de build independe de setor — qualquer PGR de
qualquer cliente sobe pelo mesmo Dockerfile, pelo mesmo entrypoint.

**Fronteiras (não confundir).**

* D-ARQ-09 / D-ARQ-48 — preservadas: nada desta decisão entra em `motor/`; o Dockerfile copia
  `agente_medico/` inteiro, mas o que decide o que roda continua sendo o entrypoint da aplicação.
* D-ARQ-54 P1 — preservada: `materializar_secrets.py` não julga domínio clínico.
* D-ARQ-74 — intacta a jusante; a guarda anti-documento-vazio não muda com o mecanismo de build.
* D-ARQ-76 — intacta; esta decisão materializa a cláusula 3 de D-ARQ-75 (segredo fora do git,
  valores em variável de ambiente do provedor), não a supersede.

**Lacuna nomeada.** `.dockerignore` exclui `matrizes_originais/` (~32 MB de documentos de
cliente, medido em disco via `git ls-files`) do build context — sem essa exclusão, esses
documentos subiriam ao builder sem necessidade nenhuma de estarem lá.

**Base.** Sessão 003.ET, fatia 1 (09/08/2026), IMPLEMENTAÇÃO. `Dockerfile`, `.dockerignore`,
`entrypoint.sh`, `agente_medico/superficie/materializar_secrets.py`,
`tests/test_deploy_artefatos.py`. PR #288.

## D-ARQ-78 — Destino do deploy é o Streamlit Community Cloud; o nome do arquivo de dependências é contrato da plataforma; o gate próprio permanece porque a allowlist nativa é transitiva

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.EU, fatias 1-2. Fecha o §S0 do `docs/PLANO_V1.md`, reaberto pela nota 003.ET.
Nenhuma regra `R-*` criada, alterada ou depreciada.

**Contexto — o requisito que não tinha sido perguntado.** D-ARQ-75 escolheu provedor pago por
consumo com a premissa de 904 MB de pico. A nota 003.ET refutou a premissa (103-115 MB com
`Page.close()` por página) e registrou o requisito que o Diovanni declarou no curso da sessão e
que **nunca foi checado com ele em 003.ER: custo zero**. Confirmado nesta sessão como **literal**
— $0,00, sem conta de faturamento.

**Decisão — 4 cláusulas.**

1. **O alvo é o Streamlit Community Cloud; Cloud Run fica como fallback, não como primário.**
   Railway sai por assinatura fixa de $5/mês, que colide com o requisito. Cloud Run sai do topo
   por medição, não por preconceito: *"A Cloud Run instance that has any open WebSocket connection
   is considered active, so CPU is allocated and the service is billed as instance-based billing"*
   `[DERIVADO — cloud.google.com/run/docs/triggering/websockets, conferido 10/08/2026]`. Vale
   então o free tier instance-based — 240.000 vCPU-s e 450.000 GiB-s/mês
   `[DERIVADO — cloud.google.com/run/pricing, us-central1]` —, que a 1 vCPU são **66,7 h/mês** de
   instância viva. Uma aba do Streamlit aberta 8h/dia × 22 dias custa ≈ **$7,45/mês**
   `[APROXIMADO — aritmética do Arquiteto sobre as tarifas oficiais]`. O Community Cloud é a única
   opção estruturalmente $0. **O `Dockerfile`, `entrypoint.sh` e `materializar_secrets.py` de
   D-ARQ-77 não são descartados:** ficam dormentes e são o que torna o fallback para Cloud Run
   grátis de implementar se o Community Cloud furar em RAM ou no limite de apps.

2. **O nome do arquivo de dependências é contrato da plataforma, não preferência nossa.** O
   Community Cloud usa o **primeiro arquivo reconhecido** que encontra, procurando no diretório do
   entrypoint e depois na raiz; os nomes reconhecidos são `uv.lock`, `Pipfile`, `environment.yml`,
   `requirements.txt`, `pyproject.toml`
   `[DERIVADO — docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies,
   conferido 10/08/2026]`. `requirements-app.txt` **não é reconhecido** e não há como apontar outro
   arquivo — com `app_matriz.py` na raiz, um deploy instalaria as 14 dependências do legado.
   Solução: **renomear, nunca duplicar** — o app assume `requirements.txt`, o legado vira
   `requirements-legado.txt`. Duplicar criaria duas listas vivas (Docker lê uma, Community Cloud
   lê a outra) que divergem em silêncio: erro silencioso plausível de D-ARQ-22.
   **Efeito não previsto, e é ganho:** com o `requirements.txt` da raiz sendo o do app, a detecção
   automática de builder passa a acertar por padrão — o renomeio **remove a causa-raiz** que
   motivou D-ARQ-77 cláusula 1, em vez de contorná-la.

3. **O gate próprio permanece, e a razão agora é medida.** A tentação era descartá-lo: o app
   privado do Community Cloud já traz login e lista de e-mails nativos. A doc desfaz a aparência —
   *"They can also pass these permissions to others by inviting more viewers"*
   `[DERIVADO — docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app, conferido
   10/08/2026]`. **A allowlist nativa é transitiva:** quem entra pode abrir para terceiros. Para
   app com PGR de cliente, ela não é gate. `PCMSO_ALLOWLIST` é a única lista que um viewer não
   estende. Segunda razão, independente: o toggle "Make this app public" é um clique no menu Share.
   D-ARQ-76 cláusula 4 sobrevive **sem tocar código**: *"the root-level secrets are also accessible
   as environment variables"*, com exemplo literal `os.environ[...]`
   `[DERIVADO — docs.streamlit.io/develop/concepts/connections/secrets-management, conferido
   10/08/2026]` — a chave colada em nível raiz do TOML chega em `os.environ`.

4. **A ordem de configuração é rígida, e a rigidez vem de código nosso.** `app_matriz.py` lê
   `st.user.is_logged_in` na primeira linha executável, e o atributo não existe sem `[auth]`
   (medição 1 de D-ARQ-76); o Community Cloud força `showErrorDetails = false`
   `[DERIVADO — docs.streamlit.io/deploy/streamlit-community-cloud/status]`. Deploy sem os
   segredos colados = tela de erro sem causa visível. A fatia 1 troca o `AttributeError` por
   mensagem explícita (`_identidade_do_provedor`), mas **não dispensa a ordem**: escolher o
   subdomínio → criar o OAuth client do Google com `redirect_uri` = `<URL do app>/oauth2callback`
   → colar o TOML (`[auth]` + `PCMSO_ALLOWLIST` em nível raiz) em *Advanced settings* → só então
   deploy. **Não existe "subir primeiro, autenticar depois".** Pré-requisito operacional
   independente: *"You are only allowed one private app at a time"* `[DERIVADO — mesma fonte da
   cláusula 3]` — o legado Seconci precisa liberar a vaga.

**Universalidade (D-ARQ-06).** Hospedagem, identidade e mecanismo de build independem de setor —
construção civil, indústria química e saúde sobem o mesmo PDF na mesma tela, sob o mesmo gate.

**Fronteiras (não confundir).**

* **D-ARQ-77 cláusula 4** — **superada**: o `requirements.txt` do legado não permanece com esse
  nome. A cláusula 1 (Dockerfile decide o build) segue íntegra, e sua causa-raiz foi removida pela
  cláusula 2 desta decisão, não a própria cláusula.
* **D-ARQ-76** — intacta, e a cláusula 4 ganha confirmação documental que ela não tinha.
* **D-ARQ-75** — cláusula 1 (provedor por consumo) **revogada** por esta decisão; as cláusulas
  2(a), 2(c) e 3 seguem íntegras. A 2(b) já havia sido superada por D-ARQ-76.
* **D-ARQ-09 / D-ARQ-48** — preservadas: nada desta decisão entra em `motor/`. O invariante de
  `test_pureza_motor.py` segue intacto.
* **D-ARQ-54 P1 / D-ARQ-74** — preservadas. Nenhuma regra clínica se move para a superfície.

**`[A CONFIRMAR]` remanescentes, nomeados para não sumirem.**

* **Limite de RAM do Community Cloud** — não localizado em cinco páginas oficiais lidas nesta
  sessão. Não afirmar que não existe (ver erro de método abaixo). Com pico medido em 103-115 MB,
  o risco é baixo; o primeiro deploy é a medição.
* **Se o subdomínio é escolhível antes do primeiro boot.** Se não for, há circularidade com o
  `redirect_uri`, e a saída é um deploy descartável que ocupa temporariamente a vaga única.

**Dois erros de método do Arquiteto, registrados (D-ARQ-06).**

1. *Ausência de evidência tratada como evidência de ausência.* Li a página `status` inteira, não
   achei "1 app privado", e afirmei que o número de D-ARQ-75/§S0 estava sem proveniência. Está na
   doc, em página irmã (`share-your-app`). Quase enfraqueci uma restrição real que é pré-requisito
   duro de deploy. Regra derivada: "não localizei em X" nunca vira "não tem proveniência" sem
   varrer as páginas irmãs da mesma seção.
2. *Número envelhecido cravado como gabarito bloqueante.* O prompt da fatia 1 cravou `mypy = 45
   arquivos`, valor de 003.ES (`88b1d64`). O real é **47**: 003.ET criou `motor/io_pdf.py` e
   `superficie/materializar_secrets.py` e seu fechamento não re-mediu ("nenhum `.py` tocado"). O
   `CLAUDE.md` da raiz **já advertia** que o número sobe com módulo novo, e o Arquiteto o leu no
   gate e cravou assim mesmo. O Code parou e reportou, no procedimento previsto; a referência foi
   corrigida em `8fd6039`. Terceira ocorrência da classe.

**Base.** Sessão 003.EU (10/08/2026), ARQUITETURA + IMPLEMENTAÇÃO (fatia 1). Gate de abertura
cumprido e declarado. Fatia 1: PR #291, merge `0d222c1`, commits `da1ebd2`/`5b1eb7d`/`8fd6039`;
suíte 1085→**1086 passed, 6 skipped**; `mypy --strict` limpo, **47 arquivos**.

## D-ARQ-79 — Entrypoint de desenvolvimento sem gate é porta deliberada, travada por teste no entrypoint de produção

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.EV, fatia 1 (PR #293, merge `75255e8`). Nenhuma regra `R-*` tocada.

**Contexto.** D-ARQ-76 pôs o gate de acesso no entrypoint, e D-ARQ-78 cl.4 mediu a consequência:
sem o bloco `[auth]`, `app_matriz.py` para em "Aplicativo mal configurado". Correto em produção e
inviável na máquina do operador, que é onde a matriz é gerada para validação clínica — exigir
OAuth do Google para rodar `streamlit run` localmente é barreira sem contrapartida.

**Decisão — 3 cláusulas.**

1. **Existe um segundo entrypoint, `app_matriz_local.py`, sem gate.** Chama `pagina_matriz()`
   direto. É a porta de desenvolvimento, e o fato de ela não ter autenticação é o ponto dela.
2. **A separação é travada por teste, não por disciplina.**
   `test_entrypoint_de_producao_nao_usa_o_entrypoint_local` crava que o `entrypoint.sh` do
   container aponta para `app_matriz.py` e nunca para o local. Sem esse teste, a porta sem
   autenticação chegaria à internet por um descuido de uma linha.
3. **A identidade visual mora nos entrypoints, não na página.** `st.set_page_config` tem de ser o
   primeiro comando Streamlit da página, e o gate chama `st.title` antes de `pagina_matriz()` —
   dentro da página, quebraria com `StreamlitAPIException` no caminho do gate.

**Universalidade (D-ARQ-06).** Independe de setor.

**Fronteiras.** D-ARQ-76 intacta — o gate de produção não muda. D-ARQ-77 intacta — o `Dockerfile`
copia e executa o entrypoint de produção. Não toca motor, protocolo nem vocabulário.

**Base.** 003.EV fatia 1. Suíte 1086→1088 passed, 6 skipped; `mypy --strict` limpo, **48
arquivos** (sobe de 47 por `app_matriz_local.py` entrar no alvo canônico).

## D-ARQ-80 — No nível gratuito o gargalo é requisição, não token: a unidade de invocação do transcritor é o lote

**Status:** DECISÃO DE ARQUITETURA

Sessão 003.EW, fatias 1-2. Nenhuma regra `R-*` tocada.

**Contexto — os números que obrigam a decisão.** Medidos no painel do nível gratuito e em rodada
real contra o PGR TOCTAO, 11-12/08/2026:

* Limites por modelo, nível gratuito: **RPM 5 · TPM 250.000 · RPD 20**
  `[MEDIDO — aistudio.google.com/rate-limit, projeto do Diovanni, 12/08/2026]`
* TOCTAO: 106 páginas, **18 blocos GHE**, ~27.000 tokens no documento inteiro
* Desenho anterior: **uma requisição por bloco** = 18 de 20 requisições diárias num único
  documento, transportando 11% de uma janela de contexto
* Cascata anterior, medida modelo a modelo: `gemini-2.5-flash` **HTTP 429**; `gemini-2.5-pro`
  **HTTP 404 — "no longer available to new users"**; `gemini-2.0-flash-001` e `gemini-2.0-flash`
  **não existem mais**; `gemini-flash-latest` **HTTP 200 / finishReason STOP**, JSON correto, 13,3s
* Custo de raciocínio no maior bloco: prompt 5.704 · **thinking 2.917** · resposta 268 — o
  raciocínio consome **11×** a saída útil

**Decisão — 4 cláusulas.**

1. **A unidade de invocação é o lote, não o bloco.** `TranscritorGHEEmLote` (protocolo aditivo em
   `motor/transcritor_pgr.py`) e `_BLOCOS_POR_LOTE = 6`: três requisições por documento em vez de
   dezoito. **6 e não 18** porque uma resposta única concentra risco — uma falha custaria o
   documento inteiro e a requisição do mesmo jeito. Descer para uma chamada (20 documentos/dia)
   exige medir antes que a resposta única sai íntegra.
2. **Alinhamento é contrato duro, com dupla guarda.** A saída do lote tem o mesmo comprimento e a
   mesma ordem da entrada; faltante vira `GHEVerbatim` vazio, que `gate_forma_ghe` reprova como
   pendência bloqueante. `transcrever_ghes` ainda confere o comprimento e levanta. Redundante de
   propósito: um lote curto desalinharia bloco e conteúdo, e cada GHE receberia os riscos do
   vizinho — matriz plausível e errada, o pior modo de falha deste sistema (D-ARQ-22).
3. **Cascata com alias `-latest` à frente, versão fixa só como reserva.** Três dos quatro modelos
   cravados morreram. Mesma classe que D-ARQ-77 nomeou: caminho crítico refém de terceiro sem
   contrato.
4. **Falha de cascata carrega o motivo por modelo.** O `except Exception: continue` anterior
   apagava a causa; descobrir que eram 429, 404 e dois inexistentes exigiu um script paralelo
   fora do repositório. Diagnóstico que depende de instrumento improvisado não é diagnóstico.

5. **Mecanismo entregue não é efeito entregue, e a suíte fica verde nos dois casos.** Esta sessão
   produziu o mesmo defeito **duas vezes**, com origens independentes: a rota LLM estava pronta no
   motor desde D-ARQ-65 e inerte porque a superfície injetava o cliente-bomba; e a transcrição em
   lote nasceu completa na fatia 2 e inerte porque o `_TranscritorContado` da fatia 1 interceptava
   o *duck-typing* de `transcrever_ghes` sem expor `transcrever_lote`. Nos dois casos, todos os
   testes passavam — porque cada um exercitava uma peça, e nenhum media o caminho inteiro.
   **Consequência:** fatia que liga um mecanismo ao caminho de produção exige um teste que meça o
   caminho completo, não as peças. No caso do lote, o discriminante é contar invocações de
   `_chamar_gemini` para um documento de N blocos e exigir `ceil(N/6)`, não `N`. Registrado como
   candidato, não implementado nesta fatia.

**Universalidade (D-ARQ-06).** A rota LLM é o que torna o sistema capaz de ler PGR de **qualquer
emissor**, sem medir família por família — o caminho previsto por D-ARQ-65 e nunca ligado à
superfície até 003.EW.

**Fronteiras.** D-ARQ-09 preservada: o motor de decisão segue determinístico, o LLM só transcreve
tabela a montante, e `gate_forma_ghe` valida antes da entrada. D-ARQ-65 preservada: a rota
determinística é sempre tentada primeiro e, quando aceita, o cliente LLM nunca é invocado — no
Fascino o consumo é zero. Não toca motor de inferência, protocolo nem vocabulário.

**Travessia completa medida `[MEDIDO — 13/08/2026, rodada real no host do Diovanni]`.** O TOCTAO
— emissor **nunca medido** pela rota determinística — atravessou pela rota LLM e produziu matriz
assinável: **18 GHEs · 61 cargos · 79 linhas · 18.670 bytes de HTML · zero pendência dentro do
documento**, com o aviso de procedência exibido (`18 bloco(s) lido(s) por IA`).

**O lote entregou o efeito prometido: 3 requisições para 18 blocos** (`ceil(18/6)`), confirmadas no
painel (`Gemini 3.7 Flash · RPD 3/20` — linha inexistente antes da rodada; `gemini-flash-latest`
resolve para 3.7 Flash). TPM 20,65K de 250K — 8% do teto. Tempo total ~5 min
`[APROXIMADO — estimativa do operador, não cronometrado]`.

**Comparação com a rota determinística no MESMO documento** (sanity-check neutralizado
experimentalmente pelo Arquiteto, 12/08): 18 blocos e 61 cargos nos dois, mas a determinística
devolveu **3 riscos no documento inteiro** e cargos **truncados na primeira palavra composta**
(`Auxiliar de`, `Engenheiro`), enquanto a rota LLM devolveu cargos íntegros
(`Auxiliar de Engenharia`, `Engenheiro Civil`) e riscos resolvidos — com emissão de Espirometria,
RX Tórax OIT, Acetona na urina e MEK na urina.

**Achado clínico de convergência tripla, o mais forte da sessão.** No GHE-11 Hidráulica a rota LLM
emitiu **Acetona na urina + Metil-etil-cetona (MEK) na urina** para Encanador, Meio Oficial e
Servente. Três caminhos independentes apontam a mesma conduta: (1) a Dra. Carolini anotou à mão no
gabarito do Fascino, ao lado de "Encanador", *"risco baixo no pgr para acetona e metiletilcetona"*;
(2) no Fascino a rota determinística **recusou** `Metiletilcetona` pelo fuzzy (distância 2 de
`metil_etil_cetona`, `DT-003EQ-02`); (3) no TOCTAO a rota LLM transcreveu e o motor emitiu o
indicador biológico sozinho. Reforça a prioridade do alias medido sob D-ARQ-70.

**Capacidade real no nível gratuito, medida no painel:** RPD por modelo — 2.5 Flash **20**,
3.6 Flash **20**, 3.7 Flash **20**, **3.5 Flash Lite 500**. Com 3 requisições por documento e a
cascata caindo para o Lite sob cota, a capacidade agregada é de **~186 PGRs/dia**
`[APROXIMADO — aritmética do Arquiteto sobre os RPD do painel]`. O desenho anterior (1 requisição
por bloco) dava **1 PGR/dia**.

**`[A CONFIRMAR]`** — `thinkingBudget = 512` é estimativa do Arquiteto, não medição; e os dois
achados clínicos replicados no TOCTAO (audiometria sem `DEM`; espirometria e RX sem a
periodicidade impressa) confirmam `DT-003EW-01` e `DT-003EW-02` em **segundo documento**, o que
descarta acaso de um gabarito só.

**Dois erros de método do Arquiteto, registrados (D-ARQ-06).**

1. *Listagem tratada como disponibilidade.* O primeiro diagnóstico reportou `gemini-2.5-pro` como
   OK porque ele aparece em `GET /models`; a chamada real devolve 404. Aparecer no catálogo não é
   poder usar — o único teste de disponibilidade é a chamada.
2. *Fixture global especificado sem medir os dependentes.* O `conftest.py` de blindagem de rede
   foi escrito como `autouse` sem verificar que existiam 6 testes `requer_api` dependentes da
   chave; quebrou os seis. Corrigido com opt-out por marcador nomeado `ao_vivo`. O Code parou e
   reportou, no procedimento previsto.

**Base.** Sessão 003.EW, fatias 1-2 (11-12/08/2026). Fatia 1: PR #294, merge `66f3ecf`. Fatia 2:
PR #295, merge `0136426` (inclui a emenda do wrapper — ver cláusula 5). Suíte
1092→1097→**1099 passed, 6 skipped** (fatia 2, cascata+lote: +5 líquido, não os +6 previstos no
prompt — o item de motivos acumulados reescreveu um teste pré-existente cuja mensagem genérica
deixou de existir, em vez de duplicar cobertura ao lado dele; emenda do wrapper: +2); `mypy
--strict` limpo, 48 arquivos.

## D-ARQ-81 — Precedente de corpus enviesado não amplia universo normativo; regra refutada é estado próprio, distinto de sucedida

**Contexto.** `R-AUD-04` foi criada em 003.EX sobre matriz-precedente `n=2` concordante
(D-ARQ-22 Parte A nível 2), universalizando audiometria para todo trabalhador. 003.EY mediu
23 obras e refutou o fundamento: universalidade em **7/23** (6/23 com piso `n_cargos ≥ 17`),
distribuição larga entre as não-universais. As duas matrizes de 003.EX eram justamente as
duas em que a médica estendeu ao administrativo — **artefato de amostra, não convergência**.
`D-ARQ-22` nível 2 diz "matriz validada como precedente" sem qualificar setor, tamanho nem
dispersão.

**Cláusula 1 — qualificação do nível 2 de D-ARQ-22.** Matriz-precedente só resolve incerteza
quando: (a) o corpus tem dispersão declarada entre clientes **e** setores, e o viés que ele
não cobre é nomeado na regra; (b) a amostra é a **população identificável**, não a fatia
conveniente — recorte por formato de arquivo ou disponibilidade entra na regra como limite
medido; (c) **quando a norma define o universo da obrigação, o precedente não autoriza
ampliá-lo** — pode confirmar conduta dentro do universo, não redesenhá-lo. Precedente que
amplia universo normativo é `[INTERPRETADO]` nível 4, nunca `[DERIVADO]` nível 2.

A alínea (c) é a que teria barrado `R-AUD-04`: o item 2 do Anexo II **define** o universo, e o
precedente foi usado para estendê-lo. `R-PSY-02` passa no mesmo teste e continua de pé — a
NR-01 obriga inventariar o FRPRT para todo trabalhador e **não define universo restrito de
exame**; ali o precedente preencheu vazio normativo, não contrariou recorte.

**Cláusula 2 — `DEPRECATED por refutação` é estado distinto de `DEPRECATED por sucessão`.**
Regra cujo **fundamento** foi refutado por medição posterior não tem sucessora por definição:
não há conduta nova a prescrever, há conduta a retirar. Marcação:
`[DEPRECATED — fundamento refutado por <ID da dívida>, sem sucessora]`, corpo integralmente
preservado, com a medição que refutou citada no próprio bloco. Nunca remover a ID — a
auditoria do PCMSO precisa explicar por que a matriz de ontem trazia a linha e a de hoje não.
Distingue-se de `R-ESP-01→R-ESP-02`, `R-PSY-01→R-PSY-02` e `R-BIO-02→R-BIO-04`, todas
sucessões com regra viva do outro lado.

**Consequência.** Toda regra nascida de matriz-precedente declara, no corpo, a dispersão do
corpus e o viés que não cobre. `R-AUD-04` já declarava ("ambos construção civil") e ainda
assim passou, porque declarar não era condição de nada. A cl.1 (c) torna a declaração
operante.

**Universalidade (D-ARQ-06).** Regra sobre uso de evidência, não sobre agente. Vale para
qualquer eixo cujo corpus seja de um setor só — que é o estado do acervo inteiro.

**Base.** Sessão 003.EZ. Origem: `DT-003EY-01`. Candidato registrado e não aberto em 003.EX
("quando um precedente de corpus setorialmente enviesado autoriza universalizar"), aberto aqui
porque a situação repetiu com custo medido — condição escrita lá.

## D-ARQ-82 — O selo `VÁLIDA` computa sobre a CAUSA da não-resolução, nunca sobre sua contagem; não-resolução que é acerto do motor não rebaixa a matriz

**Contexto.** `DT-003EZ-01` registrou que uma matriz sem nenhuma linha derivada de risco sai
`VÁLIDA`. A causa mecânica é que `orquestrador.executar` testa `if not tem_bloqueio and not
tem_presumida` **antes** de olhar `linhas_com_risco`: a cláusula 2 de `D-ARQ-66` protege a
fronteira `PARCIAL`/`BLOQUEADA` e **não** a fronteira de `VÁLIDA`. Lacuna de desenho da própria
cl.2, não regressão.

O caso-âncora **não é** o GHE-19 da DT. É o **GHE-16** `[MEDIDO — Fascino,
relatorios/003ez_fascino_rodar.md @ d218556; contagem REVERIFICADA termo a termo em 003.FB]`:
carrega **19 termos não resolvidos, dos quais 13 são componentes químicos de composição** (o
restante: 1 fração — `Poeira respirável`, causa-acerto — e 5 ergonômicos/de acidente), e ainda
assim sai `VÁLIDA`. Uma matriz assinável, selada como "todo risco determinou sua conduta", cujo
PGR declara agentes que o motor não identificou.

Entre esses 13 está **`Metiletilcetona`** — grafia que não resolve, embora o slug
`metil_etil_cetona` exista no vocabulário e resolva no GHE-10 do mesmo documento. É lacuna de
`termos:`, não agente desconhecido, e o agente tem **conduta devida**: `R-BIO-04` Quadro 1/EE,
biomonitoramento 6M no periódico. Ou seja, o selo `VÁLIDA` hoje cobre uma matriz à qual falta um
biomonitoramento exigido pelo Anexo I da NR-07. O dano não é hipotético. É o erro silencioso plausível de
`D-ARQ-22` no ponto onde a revisão de saída mais precisa do sinal. GHE-19 (3 termos declarados,
nenhum resolvido) é o caso secundário, e a redação de `DT-003EZ-01` o descrevia com duas
imprecisões factuais — ver "Correções de fato", abaixo.

**O que impede a solução ingênua.** Condicionar o selo a "existe termo não resolvido" é
inadmissível: 003.FA decompôs as 154 ocorrências de termo não resolvido do Fascino e mediu que
**12,9% são ACERTOS do motor** — `Poeira respirável` não resolver é `R-PGR-05` funcionando;
`Silício` não virar sílica é `D-ARQ-64` funcionando. Um selo por contagem contaria acerto como
falha, permanentemente e por desenho.

**O que faltava para a solução correta.** A discriminação tem de vir do **tipo** da
não-resolução — mas o discriminante não está disponível no ponto do selo. `hidratacao.py`
mantém a invariante *"agente=None sempre pareado com exatamente 1 pendência"* (`D-ARQ-51` seam
3, com `assert`), e ainda assim o par viaja **partido entre dois canais**: o `RiscoPGR` entra no
`PGR` e chega ao orquestrador; a `Pendencia` que carrega o tipo sai pelo retorno-tupla de
`processar_arquivo_pgr` e nunca entra no `Resultado` `[VERIFICADO — leitura de
adaptadores/orquestracao_pgr.py e motor/hidratacao.py, 07476ed]`.

---

**Decisão — 6 cláusulas.**

1. **`VÁLIDA` exige ausência de lacuna, não ausência de pendência.** Para todo `RiscoPGR` do GHE
   com `agente is None`, a causa da não-resolução tem de ser uma **causa-acerto**. Havendo ao
   menos uma causa-lacuna, a matriz não pode ser `VÁLIDA`. GHE que não declara risco algum
   satisfaz a cláusula vacuamente e segue `VÁLIDA` — ver cl.6.

2. **A causa é tipada no dado, e a lista de acertos é fechada e declarada.** Cada causa-acerto
   entra nomeando a decisão ou regra que a torna acerto: `fuzzy_recusado` (`D-ARQ-64` cl.4) e
   fração-declarada-sem-agente (`R-PGR-05`, nota de aplicação 003.EJ). **Ausência de causa
   registrada é lacuna** — o default é protetivo, e tipo novo entra na lista de acertos só por
   decisão explícita, nunca por omissão de quem o criou.

   > **[EMENDADA em 003.FC — `fuzzy_recusado` NÃO é mais causa-acerto. Redação
   > original acima preservada para rastreabilidade (não remover — auditoria
   > histórica do PCMSO); a redação vigente está em "Emenda 003.FC", abaixo.]**

3. **A causa viaja com o risco, não apenas com a pendência.** `RiscoPGR` passa a carregar a
   causa da não-resolução, preenchida no ramo `NAO_RESOLVIDO` de `hidratar_ghe`, onde a
   `Resolucao` já a conhece e hoje a descarta. A duplicação com a `Pendencia` do outro canal é
   declarada e vigiada por invariante de pareamento 1:1, teste computado do dado no molde de
   `D-ARQ-67` cl.3 — cache não vigiado diverge. Campo e consumidor entram na **mesma fatia**
   (precedente 003.DG-1); `RiscoPGR` já carrega um campo morto (`tipo: str`, sempre `""`, zero
   consumidores em produção `[VERIFICADO — git grep em todo o pacote, 07476ed]`) e não ganha um
   segundo. Reusar esse campo em vez de criar outro foi avaliado e rejeitado: `tipo` denota a
   natureza do risco, não a causa da não-resolução, e há teste cravando o contrato atual
   (`test_hidratacao.py:222`, `assert all(r.tipo == "" for r in ghe_pgr.riscos)`).

4. **Slug resolvido sem regra consumidora é contribuição DETERMINADA, não lacuna.** Não rebaixa
   o selo. Um slug que resolve e não dispara exame é a norma não prescrevendo exame para aquele
   agente — `postura_inadequada` e `esforco_fisico` (003.FA) são o caso. Consequência explícita:
   **não** se cria teste "todo slug tem consumidor a jusante"; ele nasceria vermelho em massa e o
   comportamento que ele acusaria é o correto e majoritário. Isto é a direção **oposta** de
   `D-ARQ-67` (literal em código apontando para slug inexistente), não sua aplicação — não
   confundir as duas.

5. **A fronteira `PARCIAL`/`BLOQUEADA` mantém o eixo de `D-ARQ-31` cl.1 e estende o conjunto de
   causas.** O eixo declarado lá é a **determinação da contribuição** ("todas determinaram" /
   "algumas determinaram" / "nenhuma contribuição pôde ser determinada"); os exemplos entre
   parênteses citam bloqueio ("único risco do GHE bloqueado; ou bloqueio estrutural Stage 3")
   porque, em 003.A, bloqueio era a única forma conhecida de não-determinação. Esta decisão
   acrescenta uma segunda forma — **termo não resolvido por lacuna** —, preservando o eixo.
   Logo: lacuna com alguma linha determinada por risco → `PARCIAL`; lacuna com
   `linhas_com_risco` vazia → `BLOQUEADA`. Nenhum estado novo é criado; o que se estende é o
   conjunto de causas de não-determinação, e isso está declarado, não deduzido em silêncio.

6. **Quarto estado avaliado e rejeitado.** Um estado próprio para "GHE sem risco declarado"
   custaria o contrato de `D-ARQ-31` cl.1 e todos os seus consumidores para descrever um caso em
   que `VÁLIDA` já é verdadeira: a conduta emitida (incondicionais de `R-CLI-01`/`R-PSY-02`) está
   completa, nada ficou indeterminado, e `riscos_resolvidos: (nenhum)` está impresso ao lado na
   saída (`D-ARQ-22` Parte B, nota 003.EG). O que tornava GHE-19 escandaloso não é ter zero risco
   resolvido — é ter risco **declarado** que não resolveu, e a cl.1 pega isso.

---

**Emenda 003.FC — `fuzzy_recusado` sai da lista de causas-acerto da cl.2.**

Ao implementar o selo, a medição de abertura do Fascino `[MEDIDO — 003.FC, fc0b468,
relatorios/003fc_fascino_rodar_ANTES.md]` mostrou que `Metiletilcetona` — o termo que o
Contexto desta decisão nomeia como *"lacuna de `termos:`, não agente desconhecido, e o
agente tem conduta devida: `R-BIO-04` Quadro 1/EE"* — sai do resolver como
**`fuzzy_recusado`** (aproximaria de `metil_etil_cetona`, distância 2, slug fora da
allowlist). Pela cl.2 como escrita, esse tipo era causa-acerto: a decisão classificava
como acerto do motor exatamente o caso de dano que a justificou. Um GHE cujos únicos
termos não resolvidos fossem esse e a fração sairia `VÁLIDA` cobrindo biomonitoramento
exigido pelo Anexo I da NR-07.

Causa estrutural: `fuzzy_recusado` é estado **composto** e o motor não o parte.
`Silício`→`silica` é acerto — o termo não é aquele agente. `Metiletilcetona`→
`metil_etil_cetona` é recusa correta de resolução **sobre** uma lacuna real de `termos:`,
com conduta devida. Distinguir os dois é precisamente o que a recusa declara não saber
fazer, e a cl.2 já manda ler o indecidível de forma protetiva ("ausência de causa
registrada é lacuna — o default é protetivo").

**Redação vigente da cl.2** — a original fica preservada acima com marca de emenda
(molde `R-AUD-04`/`R-ESP-01`: texto antigo nunca some, rastreabilidade histórica): a
lista fechada de causas-acerto é **`fracao_sem_agente`** (`R-PGR-05`, nota de aplicação
003.EJ, via `D-ARQ-83`). **`fuzzy_recusado` é lacuna** — a recusa de `D-ARQ-64` é acerto
de *resolução*, não evidência de que nenhuma conduta é devida. O remédio para
`fuzzy_recusado` recorrente é admitir a grafia em `termos:` sob `D-ARQ-70`, nunca selar
a matriz.

**Efeito medido: nulo no Fascino** `[MEDIDO — 003.FC]`. GHE-14 e GHE-19 têm zero
`fuzzy_recusado`; GHE-16 cai a `PARCIAL` pelas outras 15 lacunas com ou sem a emenda. A
previsão `3 VÁLIDA → 0` não muda. A emenda é de princípio, e o momento é antes de o selo
entrar em `main`.

**Fronteira com `D-ARQ-83` cl.3 — muda de caráter, não é revogada.** Aquela cláusula fixa
a ordem fração-antes-do-fuzzy alegando, entre outras razões, que a inversão faria a cl.2
desta decisão "classificar acerto sob a decisão errada". Com esta emenda a inversão passa
a classificar um **acerto como lacuna** — erro na direção protetiva. A ordem da cl.3
continua valendo pela razão que sobrevive: causa e **destinatário** corretos
(`elaborador_pgr` vs `extracao`), que é o que `R-PGR-05` prescreve. O argumento de
segurança do selo cai; o de correção de encaminhamento fica.

**Correção de fato no caso-âncora** `[MEDIDO — 003.FC, fc0b468]`: GHE-16 tem **17**
termos não resolvidos, não 19 — 13 químicos (12 `vocabulario_ausente` + `Metiletilcetona`
em `fuzzy_recusado`), 1 fração, 3 ergonômicos/de acidente. Os 2 de diferença são
`postura_inadequada` e `esforco_fisico`, resolvidos pelos aliases de 003.FA e presentes em
`riscos_resolvidos` do GHE-16 — a aritmética fecha (19 − 2 = 17). Sob a cl.2 emendada,
**16 dos 17** são lacuna.

**Correção de fato na seção "Correções de fato em `DT-003EZ-01`"** `[MEDIDO — 003.FC]`: o
item (ii) afirma que GHE-19 "declara três termos de risco e nenhum resolveu". **Um
resolve** — `postura_inadequada`. O desfecho não muda (a linha não é emitida,
`linhas_com_risco` segue vazia → `BLOQUEADA` pela cl.5), mas o fato vai corrigido.

---

**Risco assumido, declarado: saturação do selo.** A previsão é que os **3 GHEs `VÁLIDA` do
Fascino caiam para 0** — GHE-16 e GHE-14 para `PARCIAL`, GHE-19 para `BLOQUEADA`. Um selo que
nunca acende `VÁLIDA` perde poder discriminante, que é exatamente a crítica que `D-ARQ-66` cl.2 e
`D-ARQ-71` cl.3 fizeram à diluição de sinal. Aceito, por dois motivos: (a) o retrato é
**verdadeiro** — **53 de 79** slugs de `agentes.yaml` não têm `termos:` `[MEDIDO — parse YAML de
`agentes.yaml`, 07476ed, 003.FB]`, e o selo passa a
medir a distância real até a matriz assinável, subindo conforme o vocabulário cresce; (b) a
alternativa — restringir a cl.1 às lacunas "com efeito clínico" — é inexequível, porque o efeito
de um termo que não resolveu é justamente o que não se sabe. A previsão é `[A MEDIR — 003.FC]`:
a medição disponível é de `d218556`, anterior aos aliases de 003.FA, que já resolvem `Postural`.

**Correção de número herdado.** O valor "55 de 79 sem `termos:`" circula no projeto como estado
corrente; ele é a medição de **abertura** de 003.FA. A própria entrega daquela sessão adicionou
`termos:` a `postura_inadequada` e `esforco_fisico`, levando a **53**. Reconferido nos dois
pontos da árvore `[MEDIDO — 003.FB: 07476ed~2 → 55; 07476ed → 53]`. Nenhuma conclusão desta
decisão muda; o registro fica para que o número não seja recitado errado.

**Correções de fato em `DT-003EZ-01`** (a DT permanece, com estas emendas): (i) *"Não tem
pendência alguma"* é falso — GHE-19 tem duas pendências `vocabulario_ausente` de `R-GHE-02`
(cargos sem `riscos_implicitos`); o que não há é pendência **bloqueante**, e essas duas ocorrem
em 19/19 GHEs (41 ao todo, 1 por cargo, artefato de `DT-003EP-01`) — não discriminam nada. (ii) A
ambiguidade de `riscos_resolvidos: (nenhum)` que a DT nomeia está **resolvida no caso medido, no
braço ruim**: GHE-19 declara três termos de risco e nenhum resolveu. `[MEDIDO — 003.FB]`

**Fronteiras (não confundir).**

- **`D-ARQ-66` cl.2** — complementar, não revogada. Aquela impede que linha incondicional promova
  `BLOQUEADA → PARCIAL`; esta impede que ausência de bloqueio promova a `VÁLIDA`. Mesma família,
  fronteiras opostas do mesmo tri-estado.
- **`D-ARQ-31`** — cl.2 (bloqueio por-risco), cl.3 (anexação pendência-à-linha) e a invariante
  piso-sem-teto intocadas. Só a cl.1 é aplicada a um caso que ela já cobria pela letra.
- **`D-ARQ-68` cl.5(d)** e **`D-ARQ-71` cl.3** — intocadas: seguem decidindo os seus casos
  (presunção protetiva rebaixa; perna absorvida não rebaixa). Esta decisão não altera nenhum dos
  dois, e a assimetria declarada entre eles permanece.
- **`D-ARQ-13`/`D-ARQ-14`** — o tri-estado do predicado e o destino da pendência de vocabulário
  não mudam. `vocabulario_ausente` segue não-bloqueante; o que muda é que **não-bloqueante deixa
  de significar irrelevante para o selo**.
- **`D-ARQ-64`** — a recusa de fuzzy segue exatamente como está; esta decisão apenas a nomeia
  como causa-acerto na cl.2.
- **`D-ARQ-51` seam 3** — a invariante 1:1 é preservada e passa a ser vigiada por teste; a cl.3
  reúne o par, não o cria.
- **`D-ARQ-09`** — pureza preservada: a causa entra pelo `PGR`, input do motor. `executar` não
  muda de assinatura e não passa a ler pendências de outro canal.
- **Nenhuma `R-*` criada, alterada ou depreciada.** Nenhuma conduta clínica emitida muda: as
  mesmas linhas, com as mesmas periodicidades e momentos. Muda o **selo** da matriz.

**Universalidade (`D-ARQ-06`).** Expressa sobre a forma — a causa da não-resolução de um termo —,
não sobre agente, família de risco ou setor. Vale construção civil, indústria química e saúde
igualmente; o GHE-16 que a motiva é químico, o GHE-19 é administrativo.

**Dependência de dado, declarada.** A cl.2 nomeia a fração-declarada-sem-agente como
causa-acerto, e esse tipo **não existe hoje** `[VERIFICADO — varredura de `tipo="` em
`agente_medico/motor/`, 07476ed]`: `Poeira respirável` cai em `vocabulario_ausente`,
indistinguível de lacuna. Implementar a cl.1 antes de o tipo existir derrubaria o selo por acerto
do motor em **14 GHEs** (`Poeira respirável`, nota 003.EJ). A entrega de dado é **pré-requisito
da implementação**, não posterior a ela.

**Base.** Sessão 003.FB (19/08/2026). Resolve `DT-003EZ-01`. Decisão escrita e fechada nesta
sessão; implementação em 003.FC (campo + consumidor na mesma fatia, cl.3), com efeito medido por
GHE e varredura inversa.

## D-ARQ-83 — Termo reconhecido-como-não-agente é categoria própria do vocabulário: entra para NÃO resolver, com pendência de causa e destinatário próprios

**Contexto.** `D-ARQ-82` cl.2 nomeia a fração-declarada-sem-agente como **causa-acerto** — não-resolução que é o motor funcionando, não lacuna —, e esse tipo de pendência não existe: `Poeira respirável` cai hoje em `vocabulario_ausente`, indistinguível de agente desconhecido `[VERIFICADO — varredura de `tipo="` em `agente_medico/motor/`, 07476ed]`. Sem o tipo, implementar a cl.1 daquela decisão derrubaria o selo por acerto do motor em **14 GHEs**.

A conduta clínica já está prescrita e não muda: `R-PGR-05` manda solicitar FDS, conversar com o elaborador do PGR e **não rejeitar** o PGR; a nota de aplicação 003.EJ já nomeia o destinatário correto — *"o elaborador do PGR, não o vocabulário do protocolo"*. O que falta é o mecanismo.

**Âncora normativa** `[DERIVADO — NR-07 Anexo III, PDF oficial MTE `nr-07-atualizada-2022-1.pdf`, conferido em 003.FB, 19/08/2026]`. O Quadro 1 trata de "poeira **contendo** sílica, asbesto ou carvão mineral"; o Quadro 2 encabeça o ramo "empresas com medições quantitativas periódicas **de poeira respirável**". Citações na forma já conferida e gravada em `R-PGR-05` (nota 003.EJ); a releitura de 003.FB no PDF oficial as confirmou, mas foi **leitura assistida**, não transcrição caractere a caractere do cabeçalho — para citar o título em caixa alta, reconferir no PDF. A norma constrói *poeira contendo `<substância>`* e mede *poeira respirável*: **a fração é o que se mede, o agente é o que a poeira contém.** Termo que nomeia só a fração não permite rotear entre os Quadros, porque as três condições do rodapé do Quadro 2 são predicados sobre o material.

---

**Decisão — 4 cláusulas.**

1. **Categoria própria e tipada, fora de `agentes:`.** O dado mora em bloco top-level novo de `agentes.yaml`; `Vocabulario` ganha o campo, `construir_indice_termos` passa a recebê-lo e `IndiceTermos` ganha um terceiro campo (`frozenset` de formas normalizadas), ao lado de `slug_por_forma` e `fuzzy_permitido`. Custo medido: **1 chamador em produção** (`adaptadores/orquestracao_pgr.py:269`) e 8 usos em teste `[VERIFICADO — git grep, 07476ed]`.

   Duas alternativas avaliadas e rejeitadas. **Slug-sentinela dentro de `agentes:`** com flag `nao_agente: true` seria mais barato (reusaria `termos:` sem tocar o carregador), mas põe um não-agente no balde de agentes — contra a tipagem de `D-ARQ-12` — e contamina a métrica de 79 slugs que o projeto usa como referência. **Quinto YAML** custaria o mesmo que a opção adotada e exigiria emendar `D-ARQ-12` ("vocabulário mora em 4 YAMLs") sem ganho. A escolha é a menor extensão que preserva a tipagem.

2. **A forma NUNCA entra em `slug_por_forma`** — requisito de segurança, não detalhe de implementação. Se entrasse, o termo resolveria, viraria contribuição determinada, e `D-ARQ-82` cl.1 devolveria `VÁLIDA` para a matriz: exatamente o desfecho que aquela decisão existe para impedir. Travado por teste **computado do dado** (molde `D-ARQ-67` cl.3), afirmando que nenhuma forma desta categoria aparece no índice de slugs — nunca lista digitada.

3. **A consulta roda depois do hit exato e ANTES do fuzzy; a pendência tem tipo e destinatário próprios.** A ordem é escolhida por robustez, **não por um risco vivo** — e a diferença está medida. Hoje nenhuma das três formas de interesse tem candidato a distância ≤ 2 no índice real (114 formas): `poeira_respiravel`, `poeiras_respiraveis_metalicas` e `poeira_de_madeira` caem todas direto no ramo `vocabulario_ausente`, sem passar pelo ramo fuzzy `[MEDIDO — 003.FB, Levenshtein computado sobre o índice real em `07476ed`]`. Portanto a inversão da ordem **não** produziria erro hoje.

   A ordem é fixada mesmo assim porque a alternativa falha **em silêncio e no futuro**: basta um slug novo entrar no raio de uma forma da categoria — ou uma grafia mais curta ser admitida por medição — para que o termo passe a sair como `fuzzy_recusado`, pendência de **causa errada**, atribuindo a `D-ARQ-64` o que é `R-PGR-05`; e `D-ARQ-82` cl.2, que lê a causa, passaria a classificar acerto sob a decisão errada. Sem esta cláusula o defeito nasceria de uma edição de vocabulário sem relação aparente, do tipo que nenhum teste da categoria estaria vigiando. Casamento devolve `NAO_RESOLVIDO` com `Pendencia(tipo="fracao_sem_agente", destinatario="elaborador_pgr", bloqueante=False, regra_origem="R-PGR-05")`. O destinatário **não é valor novo**: `elaborador_pgr` já existe — **3 usos em produção** (`motor/estagios/emissao.py`) e 2 em teste `[VERIFICADO — git grep, 07476ed]`. `Pendencia.destinatario` é `str` livre, sem validação de domínio; a pendência entra num canal estabelecido, não abre um.

4. **Admissão de forma: o rigor de `D-ARQ-70` cl.1, com o critério (ii) invertido.** Entra a grafia que cumpra as quatro: (i) **medida** em documento real do acervo, com arquivo e contagem nomeados no comentário do YAML; (ii) o termo nomeia **fração ou forma de medida sem identificar a substância**, ancorado em literal normativo — em `D-ARQ-70` o critério é conter o núcleo semântico do agente, aqui é **não identificar agente algum**; (iii) gravada com **fonte dupla** (documento medido + literal da norma); (iv) coberta por **teste anti-FP** provando que termo que NOMEIA agente não entra na categoria.

   **Tiragem inicial** `[MEDIDO — Fascino, `relatorios/003ez_fascino_rodar.md`]`: `Poeira respirável`, 14 ocorrências em 14 GHEs distintos, `[DERIVADO — NR-07 Anexo III Quadro 2, coluna literal]`; `Poeiras Respiráveis/Metálicas`, 2 ocorrências, `[INTERPRETADO — prioridade na revisão de saída]`, porque "Metálicas" é qualificador de agente-**classe** e não de fração: continua sem substância identificável e sem rotear por nenhum dos dois Quadros, mas a atribuição é leitura do Arquiteto (precedente: `esforco_fisico` em 003.FA). Total 16 ocorrências / 2 formas — bate exatamente com a classe "fração sem agente" da decomposição de resíduo de 003.FA.

   **Caso-âncora do anti-FP:** `Poeira de madeira` (1 ocorrência no mesmo corpus) **não** entra — madeira é o agente, e o termo segue `vocabulario_ausente`. Sem esse teste, a categoria degenera em balde de tudo que começa com "poeira".

---

**O que esta decisão deliberadamente NÃO faz.** Não enumera as frações granulométricas. "Inalável" e "torácica" não aparecem na NR-07 e não têm uma única ocorrência no corpus — entrariam como especulação, vetada pela cl.4(i). A NHO 08 da Fundacentro ("Coleta de Material Particulado Sólido Suspenso no Ar de Ambientes de Trabalho") foi consultada e **não** se confirmou que define as três frações; o ano de edição vigente também ficou ambíguo entre as páginas oficiais consultadas `[INCERTO — 003.FB, conferir na biblioteca de NHOs da Fundacentro antes de citar]`; por isso não é usada como âncora, e não é necessária. A categoria cresce por medição, nunca por completude teórica de uma lista.

**Fronteiras (não confundir).**

- **`D-ARQ-70`** — irmã e oposta: lá o termo entra no vocabulário para **resolver** a um slug; aqui entra para **não resolver**. Mesmo rigor de admissão, critério (ii) invertido. `termos:` não é tocado.
- **`D-ARQ-64`** — intocada. A busca fuzzy, o piso, o empate e a allowlist não mudam. O que muda é que uma classe de termo é decidida **antes** de a busca rodar — e a cl.3 explica por que a ordem não é arbitrária.
- **`D-ARQ-14`** — preservada: termo sem candidato e sem casamento nesta categoria segue `vocabulario_ausente`, não-bloqueante. Esta decisão subtrai um caso daquele balde, não o substitui.
- **`D-ARQ-12`** — a tipagem é o motivo da cl.1, não um obstáculo a ela: a categoria entra tipada e nomeada. O número de YAMLs de vocabulário não muda.
- **`D-ARQ-82`** — esta decisão materializa a causa-acerto que a cl.2 daquela nomeia. É pré-requisito da implementação do selo (003.FC), não consequência dela.
- **`R-PGR-05`** — **ID e semântica intactas.** A conduta (solicitar FDS, falar com o elaborador, não rejeitar) já estava prescrita desde a v2 e a nota 003.EJ; esta decisão dá a ela um canal de saída tipado. **Nenhuma `R-*` criada, alterada ou depreciada.**

**Universalidade (`D-ARQ-06`).** Expressa sobre a forma do termo — nomeia medida sem nomear substância —, não sobre poeira, agente ou setor. Um laudo que declara "névoa" sem o produto, ou "fibras" sem a variedade, cai na mesma categoria em qualquer setor. Vale construção civil, indústria química e saúde igualmente.

**Consequência.** Um tipo de pendência novo só é causa-acerto para `D-ARQ-82` cl.2 se **for declarado lá** — o default daquela cláusula é lacuna. Esta decisão cria o tipo; incluí-lo na lista de acertos é ato explícito da implementação de 003.FC, e o teste do selo deve falhar se a inclusão for esquecida.

**Base.** Sessão 003.FB, entrega B1 (19/08/2026). Âncora do Anexo III conferida no texto oficial do MTE nesta sessão, em leitura independente da de 003.EJ. Implementação (dado + teste) na entrega B2; consumo pelo selo em 003.FC.

**Nota de aplicação (sessão atual, branch `claude/festive-gates-soy0fr`) — anti-FP "Poeira de madeira" confirmado, agente ganha slug próprio.** A tiragem inicial desta decisão (003.FB) usou "Poeira de madeira" como anti-FP para confirmar que o termo **não** colide por fuzzy com as duas formas admitidas em `fracoes_sem_agente` — sem decidir se madeira teria tratamento próprio (isso ficou em `DT-003EJ-01`). Esta sessão resolve `DT-003EJ-01`: `poeira_de_madeira` entra em `agentes.yaml` como agente identificável (`R-RX-03`/`R-ESP-03`), nunca entrando em `fracoes_sem_agente` — a previsão do anti-FP original se confirma como projetada, cl.4(iv) ("o termo entra por NÃO identificar agente" — aqui identifica, então não entra nesta categoria).

## D-ARQ-84 — Conferência factual é obrigação sem declaração; julgamento permanece gate declarado — os dois instrumentos separam-se pela natureza da falha, não pelo momento

**Status:** DECISÃO DE MÉTODO (META)

Sessão 003.FD (22/08/2026). `[META — decisão de processo. Não toca motor nem protocolo clínico. Nenhuma R-* criada, alterada ou depreciada.]`

**Contexto.** As duas skills existem e estão versionadas desde 003.FB (`.claude/skills/conferir/`, `.claude/skills/critico/`); a cadência — quando cada uma é obrigatória — foi deixada ABERTA por desenho, porque instrumento entregue não é regra adotada (`DH-003FB-01`; precedente de separação: `D-ARQ-63` peça 1). A sessão 003.FC forneceu a medição que faltava, e ela é dupla: sobre a **mesma** decisão (`D-ARQ-82`), `/conferir` extraiu 28 afirmações e achou **1 `DIVERGE` material** que duas passadas de revisão do Arquiteto não pegaram; e o Gauntlet, a frio e em sessão nova, **aprovou** o mesmo artefato sem pegar a contradição da cl.2. Os dois instrumentos rodaram sobre o mesmo objeto e falharam em coisas diferentes — evidência direta de que não são substitutos um do outro.

O modo de falha dominante e catalogado do projeto é de **conferência** (afirmação factual × fonte primária), não de julgamento: gate pulado em 003.DP; gate de 003.FA omitindo a própria `D-ARQ-70` que a sessão ia alterar; a classe "leio a forma, não a prova" com 11+ ocorrências; parser ad-hoc do Arquiteto produzindo gabarito errado; mecanismo-sem-efeito 2× em 003.EW; CNAE "06" cravado sem fonte, que originou a aplicação 002.R de `D-ARQ-22`. Em nenhum desses casos quem detectou foi a suíte ou o ritual — foi o Diovanni ou uma leitura de código posterior. **O instrumento que endereça essa classe existia desde 003.FB e não foi invocado sobre `D-ARQ-82`.**

**Decisão — cinco cláusulas.**

**cl.1 — `/conferir` é obrigatório sobre artefato que crava fato**, antes de o artefato virar trabalho do Code ou ser gravado em doc vivo. Lista fechada do que crava fato: (a) prompt cirúrgico para o Claude Code; (b) corpo de D-ARQ nova ou de emenda a D-ARQ existente; (c) bloco de sessão do `HISTORICO_OPERACIONAL.md`; (d) re-tiragem do `PAINEL_ESTADO.md`; (e) spec de dado (vocabulário, gabarito, mapa agente→indicador). Ficam fora: discussão conceitual, decisão de foco sem número, e o handoff de `D-ARQ-32` — que por desenho não crava estado.

**cl.2 — Nenhuma declaração ritual nova.** O cumprimento **não** é declarado por linha de gate. A evidência é o próprio relatório do conferidor — contagem, inventário de 100% das afirmações extraídas e o hash contra o qual conferiu —, referenciado no bloco da sessão. Razão: a declaração instituída por `003.DQ` existe porque **leitura** é não-falsificável de fora; um relatório em que cada achado carrega o comando que o reproduz **é** falsificável, e selo sobre coisa falsificável é a categoria não-auditável que `D-ARQ-22` combate. Esta cláusula é o que impede a decisão de virar um quarto passo de cerimônia — a discordância registrada em `DH-003FB-01` ("nenhum gate novo"), honrada e não descartada.

**cl.3 — `DIVERGE` material bloqueia a emissão.** Divergência que altera o que o artefato prescreve é bloqueador: corrigir e re-conferir antes de emitir. `NÃO VERIFICÁVEL` **não** bloqueia — é achado que entra no registro e, quando seu objeto for comportamento do motor, converte-se em **teste**, não em medição avulsa. Precedente medido: o `NÃO VERIFICÁVEL` #4/5 do relatório de 003.FC virou o teste T7 sobre a grafia nua `"Metiletilcetona"`, e não uma nota de rodapé.

**cl.4 — `/critico` inalterado quanto à cadência.** O gate de fechamento permanece exatamente como o método do projeto o define — sessão nova, artefato + barra do modo, declaração obrigatória —, e esta decisão não o altera. Não ganha item de barra por força dela. O que muda é o insumo: passa a receber artefato já limpo de erro factual e gasta a sessão nos itens da barra.

> **Procedência do gate de fechamento — declarada, não presumida.** O texto normativo desse gate vive nas **instruções do projeto Cowork, fora do git**: nenhuma D-ARQ o institui `[MEDIDO — 003.FD-E2 @ c765863: git grep -i "gate de fechamento" em DECISOES_ARQUITETURAIS.md não devolve cláusula instituidora anterior a esta]`. O que `003.DQ` instituiu foi a obrigação declarável do gate de **abertura** — assim registrado no Contexto de `D-ARQ-63` e coerente com a linha "Docs" do bloco 003.DQ do HISTORICO (*"CLAUDE.md do ambiente Arquiteto e instruções do projeto atualizados fora do repo"*). O instrumento `/critico` nasce em 003.FB (`e1952ac`). A regra que governa o julgamento de todo artefato deste projeto é, portanto, a única peça central de método **sem âncora versionada** — ver `DT-003FD-03`.

> **Correção 003.FD-E2 (Gauntlet, 2ª rejeição).** A redação original desta cláusula dizia *"Permanece o gate de fechamento instituído por `003.DQ`"*. Falsa: `003.DQ` instituiu o gate de **abertura**, como a própria seção de Fronteiras deste artefato registra duas telas abaixo (*"`003.DQ` / `D-ARQ-63` — gate de **abertura**"*) e como a cl.2 acima já usava corretamente (*"a declaração instituída por `003.DQ` existe porque **leitura** é não-falsificável"*). É a **classe 2** de `/conferir` pela segunda vez no mesmo artefato — e também **classe 11**, por contradizer duas outras passagens do próprio corpo. Causa registrada: a emenda `003.FD-E` corrigiu **só o gap apontado**, sem re-conferir o artefato inteiro, contrariando a cl.3 desta mesma decisão (*"corrigir e re-conferir antes de emitir"*). Nenhuma outra cláusula é tocada.

**cl.5 — Coerência interna do artefato é conferência, não julgamento.** "Nenhuma cláusula contradiz um fato afirmado no corpo do próprio artefato" entra como **classe de erro do `/conferir`** (classe 11), não como 4º item da barra de ARQUITETURA. Razão medida, não estética: a contradição da cl.2 de `D-ARQ-82` só se tornou visível ao cruzar o texto da decisão com o comportamento real do resolver — `Metiletilcetona` sai como `fuzzy_recusado`, estado que a cl.2 classificava como acerto do motor, enquanto o Contexto da mesma decisão nomeava aquele termo como lacuna com conduta devida por `R-BIO-04`. É trabalho de quem lê o repo, não de quem lê o artefato. O Gauntlet teve a decisão inteira na mão, a frio, e não a pegou; presumir que um item novo de barra o faria pegar seria decidir contra a própria medição que motivou a decisão.

**Consequência.**

- O Arquiteto deixa de ser o detector de último recurso do próprio erro factual — objetivo declarado de `DH-003FB-01`, que **fecha** com esta decisão.
- Custo por sessão: uma invocação de skill sobre o pacote já pronto. Sem passo declaratório, sem sessão nova, sem espera.
- **Risco residual assumido:** `/conferir` roda como subagente, e subagente alcança as mesmas fontes laterais do builder (memória do Cowork, project knowledge, `relatorios/`) — o isolamento é **instrução, não estrutura** `[MEDIDO — 003.FB]`. Para o conferidor isso não invalida a saída, porque cada achado carrega o comando que o reproduz; é exatamente por isso que ele **não** substitui o Gauntlet, cujo isolamento importa. `[INTERPRETADO — prioridade na revisão de saída]`
- Achado colateral, registrado para não passar por aprovação silenciosa: `DH-003FD-01` — a barra de ARQUITETURA, cujo item 1 é o teste dos três setores (construção civil, indústria química, saúde), não tem forma aplicável a decisão META. Esta decisão inclusive. Não bloqueia; nomeado.

**Fronteiras (não confundir).**

- **`003.DQ` / `D-ARQ-63`** — gate de **abertura**, sobre conhecimento acumulado, declarado nominalmente. Esta decisão é sobre o artefato **produzido** na sessão, e não é declarada. Momentos e objetos distintos; nenhuma revoga a outra.
- **`D-ARQ-22`** — aplicação direta da Parte A ao artefato inteiro. O gate de procedência do prompt cirúrgico (aplicação 002.R) exigia marcador **por valor cravado**; esta decisão exige conferência **por afirmação extraída**. Mesma doutrina, cobertura maior.
- **`D-ARQ-26` (`/kickoff`)** — intocado. O kickoff coleta ESTADO na abertura; o conferidor confere AFIRMAÇÃO na saída. A skill não passa a ler DECISOES.
- **`D-ARQ-30` (briefing)** — intocado; nem coleta nem confere, aponta.
- **`D-ARQ-32` (handoff)** — fora da cl.1 por desenho, e não por esquecimento: o handoff é DERIVADO, reescrito do zero a cada sessão e, por definição daquela decisão, **não crava estado**.
- **`DT-003DX-02`** — a cadência aqui decidida é regra do público **Arquiteto**, e as skills que a materializam já vivem no git. O que esta decisão acrescenta **não** é o ineditismo do versionamento: instrumento desse público está sob git desde `/kickoff` (`D-ARQ-26`, commit `0dd0449`, sessão 002.U), e `/conferir`/`/critico` desde `e1952ac` (003.FB). O que entra no git aqui é a **regra de cadência** — até esta decisão o instrumento era versionado e a obrigação de usá-lo não era. **Reduz, não fecha** o resíduo daquela DT: gate, universalidade e paliativos seguem no `CLAUDE.md` do projeto Cowork, sem mecanismo que detecte divergência contra o repo.
- Não toca motor, protocolo clínico nem vocabulário.

> **Correção 003.FD-E (Gauntlet), mesma decisão, sem mudança de cláusula.** A redação original desta fronteira dizia *"É a primeira regra desse público sob versionamento"*. É **falsa** contra `D-ARQ-26` — citada duas linhas acima, na mesma seção de Fronteiras — e contraditória com a frase imediatamente anterior dela própria ("as skills que a materializam já vivem no git"). Origem: afirmação herdada de `DH-003FB-01` (*"Seria a primeira regra do público Arquiteto a entrar no git"*) e reproduzida sem conferir. Achada pelo Crítico a frio @ `4ccc31b`, depois do merge do PR #311. É simultaneamente a **classe 2** (afirmação sobre o que outra decisão diz) e a **classe 11** (cláusula que contradiz o corpo do próprio artefato) de `/conferir` — as duas que esta decisão institui. Nenhuma cláusula de `D-ARQ-84` é tocada: o defeito estava na seção de Fronteiras, não no dispositivo.

**Base.** Sessão 003.FD (22/08/2026), META. Evidência: 003.FB (teste com gabarito fechado antes da execução — `/conferir` pegou 5 de 6 defeitos plantados e achou 1 não plantado; `/critico` rejeitou o artefato-isca nomeando gap melhor que o do gabarito) e 003.FC (1 `DIVERGE` material em 28 afirmações extraídas; Gauntlet aprovou o mesmo artefato sem ver a contradição da cl.2).

---

## D-ARQ-85 — Baseline e números clínicos do painel têm relógios distintos: o que envelhece a cada commit é re-tirado a cada fechamento

**Status:** DECISÃO DE MÉTODO (META)

Sessão 003.FD (22/08/2026). `[META — decisão de processo. Não toca motor nem protocolo clínico. Nenhuma R-* criada, alterada ou depreciada.]`

**Contexto.** O `PAINEL_ESTADO.md` abre declarando-se *"painel vivo, não foto datada"*, e sua regra de cadência re-tira **por evento**: merge que move um dos três números clínicos, marco fechado, ou sessão META. O bloco **Baseline**, porém, carrega hash, contagem de suíte e versões de doc — grandezas que mudam **por commit**, não por evento clínico. As duas afirmações convivem mal, e a defasagem é medida em três sessões consecutivas: 003.FA registrou; 003.FB mediu (painel em `main a8bb4d1 · 1137 passed · DECISOES v173` contra estado real `main a48836d · 1147 passed · DECISOES v177` — três sessões de atraso, contagem errada em 10 testes, **cada defasagem individualmente correta pela regra**); 003.FC pagou com uma nota `[PALIATIVO]` gravada no corpo do próprio painel. Padrão em três sessões é desenho, não descuido.

**Decisão — três cláusulas.**

**cl.1 — Duas cadências, um documento.** Os **três números clínicos** seguem a regra atual, **intacta**: re-tirados por evento (merge que move número, marco fechado, sessão META). O bloco **Baseline** passa a ser re-tirado em **todo fechamento de sessão que produza commit**, como passo do ritual (`RITUAL_FECHAMENTO.md` passo 5). Custo marginal ~zero: o passo 1 já lê as versões dos docs e o passo 6 já mede a suíte quando ela é medida.

**cl.2 — Derivado onde é barato, carimbado onde é caro.** Hash e versões de `PROTOCOLO`/`DECISOES` são deriváveis do repo em tempo desprezível e passam a sair de `scripts/medir_painel.py`. A contagem de suíte **não** é derivável sem rodar a suíte `[MEDIDO — DH-003EC-02: 1366s / 22min46 para 973 testes coletados; a suíte hoje é maior]` — permanece entrada de **medição**, e é gravada **sempre junto do commit em que foi medida**, nunca solta. Consequência imediata e desejada: uma sessão docs-only, que legitimamente não roda a suíte completa, grava no Baseline a contagem herdada **com o commit de origem visível**, em vez de reapresentá-la como corrente.

**cl.3 — O que é testável é testado; o que não é, é declarado.** Teste de não-divergência cobre **apenas as versões de doc** do Baseline, contra as tabelas de revisão reais. O **hash não é testável por não-divergência**: muda a cada commit, e um teste sobre ele ficaria vermelho por construção — ao contrário de `INDICE_DARQ.md`, que deriva de **conteúdo**, não de posição no histórico. A **contagem de suíte** não é testável sem recursão (teste que roda a suíte dentro da suíte). Esta assimetria é declarada, não contornada: derivar o Baseline inteiro por script — a segunda correção candidata de `DH-003FB-03`, e a mais fiel à doutrina anti-cache à primeira vista — é **impossível** pelas duas razões acima. Registrá-lo aqui é o que impede a sessão seguinte de tentar de novo.

**Consequência.**

- A nota `[PALIATIVO — 003.FC]` do painel sai: a cadência que ela paliava passa a existir.
- Os parágrafos de tiragem ("Instrumento oficial nesta tiragem", "Nota de escopo desta tiragem") continuam sendo **registro histórico** da tiragem que os produziu e **não** são reescritos por re-tiragem de Baseline — reescrevê-los falsificaria o que aquela sessão mediu. 003.FC acertou isso por emenda (`9bc875d`); esta cláusula promove o acerto de nota a regra.
- Instrumento (`scripts/medir_painel.py` emitindo a linha pronta + teste das versões) é **fatia própria e não é pré-requisito**: a cl.1 vale a partir desta sessão, com o Baseline colado à mão. Precedente de separação: `D-ARQ-63` peça 1. Registrado em `DT-003FD-01`.
- **Atrito novo, aceito e nomeado:** acrescentar linha à saída de `main()` em `scripts/medir_painel.py` quebra `test_main_sem_flag_suite_imprime_5_linhas_no_formato_esperado` `[MEDIDO — 003.FD, leitura de `tests/test_medir_painel.py` @ `6421286`]`. O teste é atualizado na mesma fatia do instrumento — contrato de saída mudando, não regressão.

**Fronteiras (não confundir).**

- **`D-ARQ-63` peça 1 (`INDICE_DARQ.md`)** — molde **parcial**, não completo. Lá o derivado é 100% função do conteúdo do documento-fonte; aqui um terço do Baseline é posição no histórico (hash) e outro terço custa 22min46 (suíte). Copiar o molde inteiro é exatamente o erro que a cl.3 nomeia.
- **`D-ARQ-22`** — Baseline defasado é erro silencioso plausível **no documento cuja única função é ser a leitura rápida do estado**. Esta decisão é mitigação direta dessa classe.
- **`D-ARQ-32` (handoff)** — não confundir: o handoff não crava estado por desenho; o painel crava, e é por isso que envelhece.
- Não toca motor, protocolo clínico nem vocabulário.

**Base.** Sessão 003.FD (22/08/2026), META. Resolve a decisão que `DH-003FB-03` deixou aberta; medições de 003.FB e 003.FC citadas acima.

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
| v15 | 25/05/2026 | Sessão 002.L-estudo: D-ARQ-19 adicionada (periodicidade por tempo de exposição = agendador) |
| v16 | 25/05/2026 | Sessão 002.L0: D-ARQ-20 adicionada (periodicidade condicional via família de regras por faixa); D-ARQ-19 refinado (segundo valor `periodicidade_apos_15a`, não metadado) |
| v17 | 25/05/2026 | Sessão 002.L: D-ARQ-21 adicionada — agrupamento em GHE é canônico, motor respeita o GHE do PGR sem re-agrupar (origem: PGR Viverde-CMO, pedreiro em 6 GHEs; Carolini respeita o agrupamento) |
| v18 | 28/05/2026 | Sessão 002.M: D-ARQ-22 adicionada (modelo erro-zero + revisão de saída + PDCA; hierarquia de resolução de incerteza; status [A VALIDAR — Carolini] descontinuado); D-ARQ-23 adicionada (operação como dado de primeira classe do GHE — PROPOSTA, não implementada) |
| v19 | 29/05/2026 | Sessão 002.O (META): DT-002N-02 resolvida — nota de resolução em D-ARQ-22; notação `[DERIVADO]` canônica = fonte no marcador (Parte A); convenção do PROTOCOLO alinhada. Doc-only, sem reclassificação de regra |
| v20 | 30/05/2026 | Sessão 002.P (ARQUITETURA): D-ARQ-25 adicionada — camada de extração, contrato de fronteira é `tipos.PGR` (sem intermediário); normalização de vocabulário a montante do motor (preserva D-ARQ-09); contrato-alvo completo de `tipos.PGR` especificado (campos existentes vs. extensão futura: pct_quartzo + cenário de exposição para D-ARQ-24). Parser legado não portado. |
| v21 | 30/05/2026 | Sessão 002.Q (IMPLEMENTAÇÃO): D-ARQ-25 Parte C implementada — `Quantificacao.pct_quartzo` + sub-objeto `CenarioExposicao` em `GHEPGR.cenario`; nota de aplicação em D-ARQ-25 e D-ARQ-24 (destrava parcial). Suíte 292→297, mypy --strict limpo. PR #36, commit 46e32dc. |
| v22 | 30/05/2026 | Sessão 002.R (META): nota de aplicação em D-ARQ-22 — gate de procedência factual no ponto de emissão do prompt cirúrgico; estende o alvo da mitigação de erro silencioso (Consequência) ao prompt do Code; sem reclassificação de regra |
| v23 | 31/05/2026 | Sessão META 002.T: D-ARQ-26 adicionada — ritual de abertura de sessão como skill /kickoff (coletor de estado determinístico, julgamento no Arquiteto; invocação explícita, híbrida, skill-fina, saída em tela). Implementação é sessão de Code futura. |
| v24 | 31/05/2026 | Sessão 002.U (IMPLEMENTAÇÃO): nota de aplicação em D-ARQ-26 — frontmatter resolvido contra doc oficial (`disable-model-invocation: true`; `allowed-tools` read-only); SKILL.md `/kickoff` gravado em `.claude/skills/kickoff/`; coleta via tools (não injeção) na v1. Correção de transcrição: suíte 002.T 297→312. |
| v25 | 01/06/2026 | Sessão 002.V (CONHECIMENTO/ARQUITETURA): changelog 002.V em D-ARQ-24 (premissa "motor consome CLSC pronto" + decisão `Quantificacao.fracao: Optional[Fracao]`, mesma ID); nota 002.V em D-ARQ-25 Parte C (`fracao` no contrato-alvo). Sem código — bloqueio do plug B.2 fechado antes de implementar. |
| v26 | 02/06/2026 | Sessão 002.W: D-ARQ-27 adicionada — método de construção (derivação normativa via PDCA; Carolini valida saídas, não método); primeira instância DT-002L-01. Linha de changelog omitida no fechamento da 002.W, reposta na 002.X (higiene de conformidade). |
| v27 | 03/06/2026 | Sessão 002.X (CONHECIMENTO): changelog 002.X em D-ARQ-24 — asbesto (LEO 2,0 f/cm³, f/cm³, NR-15 Anexo 12) e PNOS (LEO ACGIH 3 mg/m³ resp, nível 4) na tabela de precedência; nível (4) ACGIH vira caminho normal; unit-awareness exigida. R-RX-01-pnos DEPRECATED → família; ID clínico R-RX-01 inalterado. |
| v28 | 04/06/2026 | Sessão 002.Y (IMPLEMENTAÇÃO): D-ARQ-29 adicionada (PNOS injeta fração RESPIRAVEL — invariante do Quadro 2; assimetria intencional com D-ARQ-24/002.V); D-ARQ-28 adicionada (PROPOSTA — caminho declarativo regra→lembrete operacional); changelog 002.Y em D-ARQ-24 (ramo PNOS no resolver materializado, nível 4 ACGIH vira caminho normal). Família R-RX-01-pnos-* em código. Suíte 315→327. PR #49, commit 9bb243e. |
| v29 | 05/06/2026 | Sessão 003.A: D-ARQ-30 adicionada — rotina de briefing diário informativa; /kickoff permanece o gate de abertura (aceite empírico 05/06; briefing aponta, não afirma). Sem código. |
| v30 | 05/06/2026 | Sessão 003.A: D-ARQ-31 adicionada — bloqueio por-risco/por-linha (não por-GHE); MatrizGHE tri-estado VÁLIDA/PARCIAL/BLOQUEADA; pendência bloqueante anexada à linha emitida; resolve DT-002Z-01 por fonte documental (NR-07 7.5.5/7.6.4 + analogia R-PGR-04/05). Sem código — decisão de arquitetura, implementação multi-fatia futura. |
| v31 | 06/06/2026 | Sessão 003.B: D-ARQ-32 adicionada — handoff de sessão como 4ª entrega do ritual de encerramento (derivado, não-versionado, não-crava-estado); emenda a D-ARQ-26/SKILL.md considerada e descartada (garantia via solicitação do Diovanni no encerramento de cada chat). Decisão de processo, sem código. |
| v32 | 06/06/2026 | Sessão 003.C (IMPLEMENTAÇÃO): nota de implementação sob D-ARQ-31 — fatia 2 colapsa o ramo bloqueante (consolidação roda sempre), restam dois sítios de construção; `Resultado.status` intocado (D-ARQ-15 íntegro); cláusula 3 (anexação à linha) fica para fatia 3. Suíte 330→333, commit 76d5de1, PR #56. |
| v33 | 07/06/2026 | Sessão 003.D (IMPLEMENTAÇÃO): nota de implementação fatia 3 sob D-ARQ-31 — anexação pendência-à-linha por slug (`Pendencia.exames_alvo` + `ExameEmitido.pendencias_anexadas` + `estagios/anexacao.py`); status recomputado pós-anexação; `houve_bloqueio` deriva de `m.status`. Correção factual do exemplo canônico (Acab-05 piso 60M, não admissional). Universalidade comprovada via Adm-03 (ruído→audiometria). Dedup convergente Stage 8 fora de escopo (item próprio). Suíte 333→339, commit f25cd48, PR #58. |
| v34 | 07/06/2026 | Sessão 003.E (IMPLEMENTAÇÃO): nota de implementação fatia 4 sob D-ARQ-31 — arco fechado; auditor `auditar_invariante_piso_teto` na camada de teste (não motor/, invariante garantida por construção); retorno estruturado `ViolacaoPisoSemTeto`; teste sintético fabrica violação que o pipeline nunca produz. Regressão Viverde tri-estado: 4 PARCIAL (Acab-05/06/08, Est-07 sílica anexada) + Est-08 VÁLIDA (PNOS sem sílica). Correção factual: família R-RX-01-pnos-* governada por PNOS, não sílica. Suíte 339→347, isolado 190→198, commit 6f80f46, merge fa11ba3, PR #60. |
| v35 | 08/06/2026 | Sessão 003.G (CONHECIMENTO→ARQUITETURA): D-ARQ-33 adicionada — lado-engenheiro = motor irmão de resolução de composição química (estreitado por 3 passadas adversariais); conduta permanece no lado-médico; refina D-ARQ-25 (fronteira tipos.PGR = ofícios); cutoff 5% = limiar-dado + materialidade-predicado com lista de bypasses (caminho C). Sem código. |
| v36 | 09/06/2026 | Sessão 003.H (ARQUITETURA): D-ARQ-34 adicionada — materialidade do lado-engenheiro; `Componente.concentracao` vira faixa `(min,max)` (escalar `Optional[float]` insuficiente p/ cláusula 5 de D-ARQ-33); predicado tri-estado `{MATERIAL, NÃO-MATERIAL, AUSENTE}` com pré-condição gate-CAS + ramo 0 vocabulário-ausente; flag `is_sensibilizante` nova; changelog em D-ARQ-33 (gap-de-tipo conferido, `tipos.py:33`). DT-FDS-02 aberta (unidade do cutoff). Sem código. |
| v37 | 10/06/2026 | Sessão 003.I (IMPLEMENTAÇÃO): nota de aplicação fatia 1 em D-ARQ-34 — `FaixaConcentracao` frozen + migração `Componente.concentracao`→`Optional[FaixaConcentracao] = None`; sentinelas como método no tipo (`piso_efetivo`/`teto_efetivo`); sem `__post_init__` (`min>max` é Stage 3); gate de estado real refinado (tipo compartilhado → grep no repo inteiro). Commit 591a04d, merge 3240e10, PR #65. Suíte 347→353 / isolado 198→204. |
| v38 | 11/06/2026 | Sessão 003.J (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-34 — predicado `materialidade(componente) -> Materialidade` isolado em `motor/materialidade.py` (módulo neutro, retorna enum, não toca pendência); `Componente` ganha `agente: Optional[str]` (discriminante ramo 0, escolhido sobre `resolvido: bool`), `is_carcinogeno_iarc`/`is_sensibilizante` (flags soltas, sem agregado — padrão `Risco.is_ototoxico`). Gate-CAS confirmado pré-condição a montante, não ramo. agentes.yaml intocado. 11 testes sintéticos. Commit d0e8417, merge dd9c200, PR #67. Suíte 353→364 / isolado 204→215. |
| v39 | 14/06/2026 | Sessão 003.O (CONHECIMENTO→ARQUITETURA): D-ARQ-35 adicionada — risco químico de composição é a 4ª fonte de risco (estende D-ARQ-02), promovida no Stage 2 médico espelhando D-ARQ-23; motor irmão NÃO a produz (D-ARQ-33 cl.2 intocada); materialidade anda junto com a promoção, não a porteia; resolve a tensão interna de D-ARQ-33 a favor do literal da cl.2; dá consumidor de produção ao predicado de materialidade órfão desde 003.J. Furo de flags (Componente sem is_ototoxico) sinalizado como decisão de fatia. Sem código. |
| v40 | 14/06/2026 | Sessão 003.P (IMPLEMENTAÇÃO): nota de aplicação fatia 1 em D-ARQ-35 — Fase C em `stage_2_riscos` promove componente de FDS a `Risco(fonte="quimico_composicao")` (4ª fonte); `Risco` +3 campos (`materialidade`/`is_carcinogeno_iarc`/`is_sensibilizante`); `Materialidade` movido p/ `tipos.py` (quebra ciclo); sem dedup (D-ARQ-16); três-caminhos (ramo 0 não-promove+pendência; ramos 2/3 promove+pendência; ramos 1/4/5 promove); flags por origem única (ototóxico/anexo por-slug, materialidade-flags cópia-pra-frente). Sem consumidor. DH-003P-01 aberta. Commit `cddf092`. Suíte 222→229 isolado. |
| v41 | 15/06/2026 | Sessão 003.Q (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-35 — R-PKG-BZ, primeira regra química em `regras.yaml` (lado-químico 0→1), consome `Risco(fonte="quimico_composicao")` via primitivo `benzeno` agnóstico à fonte e à materialidade; `benzeno` em `agentes.yaml` (CAS 71-43-2, IARC grupo 1, anexo/LT null por DT-FDS-01), `reticulocitos`/`acido_transmuconico` em `exames.yaml`. Ainda sintético (sem hidratação D-ARQ-25 Parte B). Commit `ab1b386`, merge `1078baa`, PR #77. Suíte 229→233 isolado. |
| v42 | 15/06/2026 | Sessão 003.R (CONHECIMENTO→ARQUITETURA): D-ARQ-36 adicionada — sub-camada determinística de resolução de composição (extração = LLM-transcrição + resolvedor determinístico; fronteira LLM↔determinístico é "CAS transcrito", D-ARQ-33 cl.1 explicitada); gate-CAS é a fatia 1 (4 ramos: válido+slug / válido+sem-slug→vocabulario_ausente / inválido→bloqueante / oculto≠inválido); releitura de D-ARQ-34 Parte 4 (ficha normalizada = saída do resolvedor); unificação da fonte-de-flag da 003.P diferida (não toca 003.P nesta fatia). DT-003M-01 (frase-H sem slug) e DT-FDS-02 fora de escopo. Sem código. |
| v43 | 15/06/2026 | Sessão 003.S (IMPLEMENTAÇÃO): nota de aplicação fatia 1 em D-ARQ-36 — gate-CAS em módulo greenfield `resolvedor.py` (paralelo a `materialidade.py`); 4 funções puras (`_so_digitos`, `cas_bem_formado` dígito-verificador, `construir_indice_cas` CAS→slug que não existia, `gate_cas` 4 ramos); ramos (a) slug / (b) vocabulario_ausente não-bloq / (c) cas_invalido bloqueante / (d) cas_ausente não-bloq; NÃO popula flags (Parte 3 diferida); isolado sem consumidor (espelha 003.J); algoritmo do dígito `[DERIVADO]`→`[VALIDADO]` (CAS.org + 4 corroborantes). Commit 5429954. Suíte 233→246 isolado (+13); mypy --strict limpo. |
| v44 | 16/06/2026 | Sessão 003.T (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-36 — gate-CAS popula `is_carcinogeno_iarc` via `EntradaIndice` (frozen, slug+flag; substitui `dict[str,str]` de `construir_indice_cas`); ramo (a) faz `replace(agente, is_carcinogeno_iarc)`. `is_sensibilizante` recortada por gate de procedência (ausente do yaml → DT-003T-01); 2ª passada reverteu incluí-la (fiação fantasma). `is_ototoxico`/`anexo_nr07` seguem no lado-médico (só em Risco). Parte 3 PARCIAL — unificação de fonte-de-flag segue diferida. Gate isolado, sem consumidor. Commit `f308693`, merge `9058884`, PR #81. Suíte 246→248 isolado. |
| v45 | 16/06/2026 | Sessão 003.V (ARQUITETURA): nota de aplicação 003.V em D-ARQ-36 — motor irmão mínimo `resolver_composicao` (a montante de `executar()`, aplica gate-CAS + remonta PGR frozen via `replace` em cascata, deliberada por pureza D-ARQ-09) como consumidor de produção do gate isolado; fixture `fds_t65` a reescrever crua (gate resolve pelo CAS, exercita 4 ramos sobre FDS real); nome do módulo aberto p/ 003.W. Fonte-de-flag resolvida a favor da transcrição: gate NÃO sobrescreve `is_carcinogeno_iarc` (reverte 003.T; `EntradaIndice` inerte); caso-âncora TiO₂ (yaml=true substância vs Componente=false este-produto, D-ARQ-34 Parte 4). Tri-estado `Optional[bool]` descartado. STOP-and-report da Parte 3 autorizado pelo Diovanni. Sem código — implementação é 003.W. Nota em D-ARQ-35 (4ª fonte ganha produtor de composição resolvida). |
| v46 | 16/06/2026 | Sessão 003.W (IMPLEMENTAÇÃO): nota de aplicação 003.W em D-ARQ-36 — `resolver_composicao` (motor irmão mínimo) em `motor/composicao.py` flat, isolado a montante de `executar()`, remonta cascata frozen via `replace`; reversão da sobrescrita de `is_carcinogeno_iarc` no ramo (a) do gate (reverte 003.T, `EntradaIndice` inerte); fixture `fds_t65` crua (TiO₂ CAS errado → ramo c); `test_materialidade_fds` migrado p/ cadeia resolvida (contagem 1/23/0 → 2/22/0, acetona/acetato resolvem por slug 003.N); teste-reversão discriminante; 4 ramos sobre CAS real (2 ramos c: TiO₂ errado + aluminato 1242-78-3). Nota 003.W em D-ARQ-35 (produtor existe, isolado). Commit `9029282`, merge `24c058d`, PR #85. Suíte 248→255 isolado / 404 total. |
| v47 | 18/06/2026 | Sessão 003.X (IMPLEMENTAÇÃO): notas de aplicação 003.X em D-ARQ-35 (cadeia resolver_composicao→Fase C com teste de integração sobre vocabulário real) e D-ARQ-36 (degradação de procedência do descarte virou observável em teste; (i') a fecha). (i₀) — só teste, zero produção. Commit f17db90, merge 31c767b, PR #87. Suíte 255→261 isolado / 410 total. |
| v48 | 19/06/2026 | Sessão 003.Y (ARQUITETURA): D-ARQ-37 adicionada — propagação da pendência do gate-CAS ao Resultado via retorno-tupla de `resolver_composicao` (`-> tuple[PGR, list[Pendencia]]`), como pendência global (sem `ghe_id` — gate roda a montante da mesa) costurada em `pendencias_globais` por `dataclasses.replace` (não mutação), via wrapper `executar_com_composicao`. Realocação para o Stage 3 rejeitada (Fase C/Stage 2 roda antes do Stage 3; procedência c-vs-b só vive no `[1]` do gate antes do descarte). Pureza D-ARQ-09 preservada (motor irmão, não `executar`). Fecha DH-003P-01 (procedência chega ao Resultado); achatamento residual da Fase C para componente sem-slug fica como DT-003Y-01. Sem código — implementação é 003.Z. |
| v49 | 20/06/2026 | Sessão 003.Z (IMPLEMENTAÇÃO): forma α de D-ARQ-37 materializada — `resolver_composicao -> tuple[PGR, list[Pendencia]]` (acumula o `[1]` do gate sem `ghe_id`); wrapper `executar_com_composicao` costura `pendencias_globais` por `dataclasses.replace`; `executar()` intocado (sentinela de assinatura). 3 chamadores adaptados ao unpack; 9 testes novos (presença por-ramo, costura diferencial). DH-003P-01 materializada em código (forma fechada em 003.Y). DT-003Y-01 segue aberta (dupla pendência da Fase C). Commit `df3cad2`, merge `cba6048`, PR #90. Suíte 261→270 isolado / 410→419 total. mypy delta-zero vs. baseline. |
| v50 | 21/06/2026 | Sessão 003.AB (ARQUITETURA-leve): investigação de `anexo_nr07` concluída. Achado (campo morto, consumo-zero verificado por git; eixo misturado NR-07/NR-15) catalogado como DT-003AB-01 no PROTOCOLO v26, não como D-ARQ — é achado de dado herdado pela implementação de R-BIO-04, não decisão de arquitetura. Substituição `anexo_nr07 → tipo_ibe` (D-ARQ-33) é consequência mecânica de R-BIO-04. Nenhum D-ARQ criado/alterado. |
| v51 | 21/06/2026 | Sessão 003.AC (ARQUITETURA): D-ARQ-38 adicionada — `tipo_ibe` tem dois consumidores de prontidões distintas (R-CLI-02 clínico semestral, consome {EE,SC}-vs-None, schema atual basta; R-BIO-04 biomonitoramento, consome EE/SC fino, data-bloqueado pelo mapa agente→biomarcador zero-vocab); campo entra para ser consumido (mata campo-morto DT-003AB-01), não morto; forma do emissor de biomonitoramento adiada por dependência de dado; ordem de fatias selada. R-CLI-03/R-PKG-BZ não consomem tipo_ibe (identidade de agente). Sem regra clínica criada/alterada; sem código. |
| v52 | 21/06/2026 | Sessão 003.AD (CONHECIMENTO): nota de aplicação 003.AD em D-ARQ-38 — fatia (a) cumprida; `tipo_ibe` três-vias derivado contra texto oficial (Quadro 1 IBE/EE 41 / Quadro 2 IBE/SC 4); 12 EE + 1 SC (chumbo) no vocabulário; 3 achados (9 CAS null → tipo_ibe gravado não casado por CAS; chumbo ambíguo Q2/Q1; is_ototoxico ⊥ tipo_ibe); cardinalidade heterogênea confirma data-bloqueio do emissor. Sem código. |
| v53 | 22/06/2026 | Sessão 003.AE (IMPLEMENTAÇÃO): nota de aplicação 003.AE em D-ARQ-38 — fatia (b) materializada; enum `TipoIBE` {EE,SC} + migração `anexo_nr07 → tipo_ibe` in-place posição 5; gate de tipo compartilhado repo-inteiro (consumo-zero reconfirmado); 3 conversões string→enum; `agentes.yaml` por slug (12 EE + chumbo SC + resto null); campo sem consumidor (R-CLI-02 = fatia c). 419→420, mypy delta-zero. Sem regra clínica alterada. |
| v54 | 22/06/2026 | Sessão 003.AF (ARQUITETURA): D-ARQ-39 adicionada — convergência de mesmo-exame com periodicidades distintas resolve por piso component-wise (min nos dois campos, None=+∞), substituindo o raise ConflitoProtocolo do loop de dedup; geral (não clínico); as 3 mutações incondicionais (momentos/motivos/pendencias_anexadas) preservam proveniência e teto por construção; único código novo = 2 atribuições de mínimo. Resolve o recorte de D-ARQ-31 fatia 3; pré-condição da fatia (c) de D-ARQ-38. Caso-âncora vivo = sílica×fumos no RX. R-CLI-* inexistente em regras.yaml (fatia c é seam→R-CLI-01→R-CLI-02). Corrige de passagem o cabeçalho cru do D-ARQ-38 (sem `## `, gravado na 003.AC). Nenhuma regra clínica criada/alterada. Sem código. |
| v55 | 22/06/2026 | Sessão 003.AG (META): decisão de processo — criado `docs/PAINEL_ESTADO.md` (painel de gestão à vista; 1ª tiragem = inventário 003.AG: cobertura 17/41 ≈ 41%, extração 0 código / D-ARQ-25 ausente, 3 DTs bloqueantes = facetas do subsistema de ingestão). Cadência de atualização: por evento (merge que move número + fechamento de marco + piso 1×/META), nunca por calendário; re-tiragem é passo do ritual de fechamento. Recomendação de pivô A→B (extração antes de completar clínica) registrada mas NÃO selada — pendente de ratificação da diretoria; se ratificada vira D-ARQ próprio. Sem novo D-ARQ numerado. Sem código. Sem regra clínica alterada. |
| v56 | 23/06/2026 | Sessão 003.AH (ARQUITETURA): inversão de sequenciamento A→B RATIFICADA pela diretoria (22/06) — extração antes de completar a frente clínica. Registrada como decisão de processo (changelog + `PAINEL_ESTADO.md`), NÃO D-ARQ numerado: sequenciamento de trabalho, não contrato de motor (mesmo tratamento da decisão de processo v55; carimbo `[META]` de D-ARQ-32). Frente clínica (`R-CLI-01`→`R-CLI-02`) pausada em ~41% num ponto limpo (D-ARQ-39 selou o dedup). Slice map da extração medido de disco (`git show` de composicao/orquestrador/resolvedor/materialidade/riscos/tipos/agentes.yaml): sub-camada química FDS→Risco com encanamento determinístico completo e costurado mas SEM chamador de produção (`executar_com_composicao` só em teste); gargalo = índice CAS raso (9/43 slugs com CAS) + `name→slug` indeciso (D-ARQ-36 P1) + parse-PGR greenfield (D-ARQ-25, 0 código). Fatia 1 da extração = popular CAS (sessão de DADO, 003.AI), depois plugar a costura. Sem novo D-ARQ. Sem código. Sem regra clínica alterada. |
| v57 | 23/06/2026 | Sessão 003.AJ (ARQUITETURA): D-ARQ-40 adicionada — ponto de entrada de produção do motor novo é fachada fina `processar_pgr` (`entrada.py`, greenfield) sobre `executar_com_composicao`; duas portas (wrapper testável de índice explícito + fachada que esconde a construção do índice); decisão é o princípio "esconder a mecânica do índice", não a assinatura concreta (provisória, condicionada ao disco da AK); contrato de entrada `tipos.PGR` cru (D-ARQ-25 Pt A), tomada da transcrição-LLM (Pt B); harness não-travessia. Gate de estado real: não existe ponto de entrada do motor novo (3 greps). Legado `app.py` intocado. Sem código. |
| v58 | 24/06/2026 | Sessão 003.AK (IMPLEMENTAÇÃO): nota de aplicação 003.AK em D-ARQ-40 — fachada `processar_pgr` materializada em `entrada.py` greenfield; assinatura `(pgr, protocolo, hoje=None)` confirmada por disco (índice derivável do `Protocolo`); re-export canônico em `motor/__init__.py`; wrapper/`executar()`/legado intocados; harness não-travessia. 4 testes, 420→424, mypy delta-zero. DT-003AK-01 (dívida de teste). Commit a378999, merge ee233b4, PR #104. |
| v59 | 25/06/2026 | Sessão 003.AL (ARQUITETURA): D-ARQ-41 adicionada — camada de extração é bicamada (transcritor-LLM + resolvedor determinístico), fronteira = contrato transcrito tipado; generaliza D-ARQ-36 (instância-FDS) ao padrão de toda extração; nomeia a "PGR transcrita" (estrutura `GHEPGR`-shaped, termos crus, FDS apontadas, NÃO `tipos.PGR`); `termo→slug` determinístico/auditável (gate D-ARQ-14), com mecanismo fino + granularidade (a/b/c) ADIADOS por medição sobre os PGRs de DT-003L-01 (molde D-ARQ-38). Recusa monocamada (LLM cospe slug → erro silencioso D-ARQ-22). Sem regra clínica criada/alterada. Sem código. |
| v60 | 25/06/2026 | Sessão 003.AM (ARQUITETURA): D-ARQ-42 adicionada — transcritor-FDS é a camada-LLM da instância-FDS de D-ARQ-41; contrato de saída `tuple[Componente,...]` cravado em disco (sem tipo intermediário); bicamada interna (parse-PDF determinístico → transcrição-LLM); recorte (A) identidade+concentração, flags de perigo no default-por-ausência com autor declarado (D-ARQ-22, não "perigo fora"); princípio de gabarito por-campo (`cas`/`concentracao` ancoram, `nome` texto-livre não-`==`); mecanismo fino + fronteira-OCR (Ciplan escaneado) + critério de `nome` ADIADOS por medição dos 3 PDFs reais → 003.AN (molde D-ARQ-41 P3). 3 pares PDF↔fixture em `fds_originais/`/`fds_t65`. Nenhuma regra clínica criada/alterada. Sem código. |
| v61 | 26/06/2026 | Sessão 003.AN (CONHECIMENTO/medição): D-ARQ-43 adicionada — medição determinística de 6 PDFs de `fds_originais/` (pdfplumber) fecha fronteira-OCR (escaneado refutado: Ciplan é nativo; sem OCR no transcritor) e critério-nome (casa por CAS-primário, `nome` não-`==`); cataloga 3 patologias da seção 3 como input da IMPL (P1 CAS plural "Derivados de:" → DT-003AN-01; P2 faixa invertida-P2a + piso-textual-00-P2b → normalização min/max no resolvedor; P3 CAS oculto 3 sabores → ramo d do gate, DT-003M-01 viva). DT-003AN-01 adicionada (PROTOCOLO v29). Triagem-LLM da 003.AM (Ciplan OCR) refutada por medição. Nenhuma regra clínica criada/alterada. Sem código. |
| v62 | 26/06/2026 | Sessão 003.AO (META/higiene): D-ARQ-44 adicionada — `.gitattributes` `*.md text eol=lf` blinda terminador de markdown na origem (independe de `core.autocrlf`); escopo `*.md` cirúrgico (não `*` global, que reescreveria `.py`/fixtures); abre+RESOLVE DH-003AO-01; distinta de DH-003M-01 (`\r\n` literal-conteúdo, segue ABERTA). Doc-only, sem código, sem regra clínica. |
| v63 | 27/06/2026 | Sessão 003.AP (IMPLEMENTAÇÃO): nota de aplicação 003.AP em D-ARQ-43 — patologia P2 materializada; helper `_normalizar_faixa` em `composicao.py`, aplicado antes do `gate_cas` no loop de `resolver_composicao`; `min()/max()` cobre P2a (invertida) e P2b (piso-textual 00) sem ramo condicional; guarda dupla de `None` (sentinela semi-aberta, não comparável); idempotente; frozen via `replace`; `tipos.py` intocado (Stage 3 / `min>max` intacto). Responsabilidade nova do resolvedor. 8 testes; 424→432; mypy limpo. Commit `534f239`, merge `ec60c60`, PR #110. Sem regra clínica criada/alterada. |
| v64 | 27/06/2026 | Sessão 003.AQ (ARQUITETURA): D-ARQ-45 adicionada — explosão de bloco "Derivados de:" multi-CAS mora no resolvedor (`composicao.py`), operação 1→N a montante do `gate_cas`, downstream do transcritor verbatim; cada sub-`Componente` herda a faixa inteira do bloco (α — fiel ao documento, sobre-materializa na direção segura, anti-supressão D-ARQ-31/33 cl.5/35 P3); β (repartir) e γ (AUSENTE) rejeitadas; marcador de proveniência de concentração-herdada adiado (sem consumo vivo). Resolve DT-003AN-01; cruza D-ARQ-35 (granularidade da promoção). Forma do trânsito CAS-plural + distinção empilhado-vs-linhas-soltas abertas para a IMPL. Nenhuma regra clínica criada/alterada. Sem código. |
| v65 | 28/06/2026 | Sessão 003.AR (IMPLEMENTAÇÃO): nota de aplicação 003.AR em D-ARQ-45 — P1 materializada; `_explodir_multi_cas` em `composicao.py`, primeira operação do loop de `resolver_composicao` (a montante de `_normalizar_faixa`/`gate_cas`); forma (a) cravada (separador `\n` no campo `cas`, não tipo de bloco — não reabre D-ARQ-42); ordem explodir→normalizar→gate neutraliza o `\n`-inválido; herança-α via `replace(cas=p)`; piso de 1 (anti-supressão); separador `\n` [DERIVADO — 003.AN]. 11 testes; 432→443; mypy delta-zero; `tipos.py`/`resolvedor.py` intocados. Commit `a04da18`, merge `f89abb3`, PR #113. Sem regra clínica criada/alterada. |
| v66 | 29/06/2026 | Sessão 003.AS (IMPLEMENTAÇÃO): nota de aplicação 003.AS em D-ARQ-42 — camada parse-PDF determinística do transcritor-FDS (`extrair_tabelas_fds`, `extracao_fds.py` greenfield, `pdfplumber.extract_tables()` cru, tabelas achatadas sobre páginas); recorte desceu de "extrai composição" para "extrai tabelas cruas" (medição provou composição não-isolável em Ciplan/Tigre — grid multi-seção fundido); asserção literal forte onde isolada (tinta/Leinertex/Massa), fraca onde fundida. DT-003AS-01 adicionada (PROTOCOLO §11, patologias de layout/transcrição). Isolado sem consumidor. Commit `8da2fed`, merge `567454e`, PR #115. Suíte 443→451. Sem regra clínica criada/alterada. |
| v67 | 29/06/2026 | Sessão 003.AT (ARQUITETURA): nota de aplicação 003.AT em D-ARQ-42 — mecanismo do transcritor-LLM, três cláusulas (localização por título normativo, não número de seção, robusta à renumeração de fabricante, com limite declarado em grid-fundido; `nome` transcrito informativo não-`==`; gabarito por par PDF↔`fds_t65` em disco, LLM mockado, nunca testa API). Pré-requisito factual "seção 2 vs 3" fechado por busca NBR 14725 (ancora por título, não número). Recorte (A) mantido; prompt + patologias 3/4/5 adiados para a IMPL (DT-003AS-01). Nenhuma regra clínica criada/alterada. Sem código. |
| v68 | 29/06/2026 | Sessão 003.AU (IMPLEMENTAÇÃO): nota de aplicação 003.AU em D-ARQ-42 — fatia 1 da camada de normalização do verbatim-FDS (patologias 3/4/5 como funções puras em `transcricao_fds.py`, isolado); heurística P3 corrigida (preserva-só-se-ambos-fragmentos-bem-formados; validade é do gate, não da camada de forma); limite residual de falso-preserva. Suíte 451→477. Commit `0135754`, merge `f3452bb`, PR #118. Sem regra clínica criada/alterada. |
| v69 | 29/06/2026 | Sessão 003.AV (ARQUITETURA): D-ARQ-46 adicionada — contrato do verbatim transcrito da FDS; LLM-transcritor emite verbatim cru (cas/nome/faixa como texto), tuple[Componente,...] é saída da montagem determinística, NÃO do LLM (corrige D-ARQ-42 P2 contra a existência de P5/003.AU — senão parsear_faixa é morto); fronteira LLM↔determinístico = o verbatim; montagem 1→1 (explosão D-ARQ-45 e ordenação 003.AP ficam no resolvedor). Dataclass-form e local-de-módulo rebaixados a recomendação (IMPL 003.AW). Recorte A mantido; producibilidade barrada por patologia 1 (DT-003AS-01). Nenhuma regra clínica criada/alterada. Sem código. |
| v70 | 30/06/2026 | Sessão 003.AW (IMPLEMENTAÇÃO): nota de aplicação 003.AW em D-ARQ-46 — montagem `verbatim → tuple[Componente,...]` materializada. `ComponenteVerbatim(cas/nome/faixa: str)` frozen em `tipos.py`; `montar_componente` (1→1) + `montar_composicao` em `transcricao_fds.py` aplicando P3/P4/P5 (ordem cravada `normalizar_cas_ausente(desambiguar_cas(...))`); explosão multi-CAS e ordenação seguem no resolvedor (intocado). Gabarito por par PDF↔`fds_t65` com verbatim mockado fiel à medição 003.AN/AS (tinta+Ciplan; `cas` exato + `concentracao`; `nome` não-`==`); Tigre fora (patologia 1). DT-003AW-01 aberta (PROTOCOLO v34). 11 testes; suíte 477→488; mypy --strict limpo. Commit `ec3b225`, merge `8054f5b`, PR #121. Nenhuma R-* criada/alterada. |
| v71 | 30/06/2026 | Sessão 003.AX (ARQUITETURA): nota de aplicação 003.AX em D-ARQ-42 — patologias 1/2 de DT-003AS-01 resolvem-se na camada-LLM (não bbox determinístico; D-ARQ-41/42 + universalidade); entrada do LLM = `extract_text` da região âncora-por-título, não `extract_tables` (medido: título-âncora some no `extract_tables` do Tigre e sobrevive no texto; patologia 2 = artefato do `extract_tables`, faixa de MEK/Acetato volta no texto). DT-003AX-01 aberta (PROTOCOLO v35): a virada tabelas→texto reabre o mecanismo de explosão multi-CAS (D-ARQ-45 `\n`-célula, não a decisão) + o papel do `extrair_tabelas_fds` (003.AS); reconciliação texto-puro vs híbrido é passada dedicada. Medição read-only Ciplan+Tigre+Leinertex. Nenhuma R-* criada/alterada. Sem código. |
| v72 | 30/06/2026 | Sessão 003.AY (CONHECIMENTO/medição → ARQUITETURA): nota de aplicação 003.AY em D-ARQ-42 + nota 003.AY em D-ARQ-45 — reconciliação DT-003AX-01 RESOLVIDA. Medição read-only `extract_text`/`extract_tables` dos 6 PDFs: bloco "Derivados de:" sobrevive no texto mas perde a estrutura de linha (CAS em linhas separadas, posição da faixa instável, sem `\n`-célula); `extract_tables` dá a linha perfeita com `\n`-célula + faixa; multi-CAS e grid-fundido DISJUNTOS no acervo. Decisão: (1) entrada TEXTO-PURO `extract_text` (não híbrido — híbrido é paliativo: roteador frágil + aposta na coincidência do acervo, classe D-ARQ-22/06); (2) explosão migra de `\n`-split (003.AR) p/ expansão-de-grupo no resolvedor — decisão D-ARQ-45 (explodir 1→N + α) preservada, só o mecanismo muda, cardinalidade fora do LLM (D-ARQ-45 P1); (3) `extrair_tabelas_fds` (003.AS) deixa de ser entrada do transcritor → candidato DEPRECATED/cross-check (IMPL decide). DT-003AX-01 RESOLVIDA (PROTOCOLO v36). Aberto p/ IMPL: forma do verbatim-grupo, destino de `_explodir_multi_cas`/`extrair_tabelas_fds`. Nenhuma regra clínica criada/alterada. Sem código. |
| v73 | 01/07/2026 | Sessão 003.AZ (IMPLEMENTAÇÃO — fatia i): nota 003.AZ em D-ARQ-46 + nota 003.AZ em D-ARQ-45 — forma do verbatim-grupo materializada. `BlocoVerbatim` aninhado ratificado (`MembroVerbatim`+`BlocoVerbatim`+`BlocoComponente` frozen em `tipos.py`; `ComponenteVerbatim` aposentado, singleton = bloco de 1); montagem `Sequence[BlocoVerbatim] → tuple[BlocoComponente,...]` (`transcricao_fds.py`; faixa 1×/bloco; herança-α/explosão seguem RESOLVER-SIDE, D-ARQ-45 P1/P2). Fixtures: `fds_verbatim_t65`→singleton; `fds_verbatim_leinertex` nova (multi-CAS N=2/N=3). Ratificado p/ fatia ii (003.BA): `_explodir_multi_cas` aposentar, `extrair_tabelas_fds` DEPRECATED. Suíte 488→489; mypy delta-zero. Commit `9a4eaf3`. Nenhuma R-* criada/alterada. |
| v74 | 01/07/2026 | Sessão 003.BA (IMPLEMENTAÇÃO — fatia ii, recorte enxuto): nota 003.BA em D-ARQ-45 — `_explodir_bloco(BlocoComponente) -> tuple[Componente,...]` adicionado em `composicao.py` (ao lado de `_explodir_multi_cas`, sem substituí-lo): herda a `FaixaConcentracao` do bloco por membro e canonicaliza via `_normalizar_faixa`; sem `gate_cas` dentro (fica no resolver, fatia iii), sem chamador em `resolver_composicao`. `extrair_tabelas_fds` (003.AS) marcado `DEPRECATED (003.BA)` na docstring (corpo intocado). `_explodir_multi_cas`/`FDS.composicao`/`test_explosao_multi_cas.py` intocados — aposentadoria/wiring/migração ficam para 003.BB. 6 testes novos (`test_explodir_bloco.py`); suíte 489→495; mypy --strict delta-zero em `composicao.py`. Commit `add384f`, branch `feat-003ba-explodir-bloco`. Nenhuma R-* criada/alterada. |
| v75 | 01/07/2026 | Sessão 003.BA (adenda — discussão de escopo pós-merge, sem código): nota 003.BA em D-ARQ-25 — fronteira de PRODUTO. Motor novo emite só o lado-médico (matriz GHE×ExameEmitido rastreável); Dec 3.048 e eSocial Tab 24 confirmados ausentes do motor (git grep vazio em agente_medico/; vivem no legado modulo_esocial_xml/modulo_engenharia). Decisão: não replicar o Anexo I do engenheiro no motor novo agora (escopo do engenheiro, não diferencial; rodaria sobre fixture; commodity; re-acopla D-ARQ-09); previdenciário+eSocial = frente de emissão separada perto do cutover (paridade p/ desligar Streamlit). Prova de vida = Marco 1 (já no PAINEL), não réplica visual. Abre DT-003BA-01. Nenhuma R-* criada/alterada. Sem código. |
| v76 | 01/07/2026 | Sessão 003.BB (IMPLEMENTAÇÃO fatia iii): notas de aplicação em D-ARQ-45 (`_explodir_bloco` plugado no resolver, `_explodir_multi_cas` aposentado, forma de trânsito = campo `composicao_verbatim`) e D-ARQ-46 (`FDS.composicao_verbatim` como entrada do resolver). Suíte 495→488, mypy delta-zero. Commit `05b0e41`, merge `05731bd`, PR #128. Nenhuma R-* alterada. |
| v77 | 01-02/07/2026 | Sessão 003.BC (META + IMPLEMENTAÇÃO): nota de aplicação em D-ARQ-44 — `.gitattributes` `*.py text eol=lf` (PR #130), fecha a lacuna sinalizada em 003.BB; desvio do gate (21 não-`.py` CRLF-only tocados por `--renormalize`) confirmado EOL-only e revertido, escopo reduzido; abre DH-003BC-01. Notas de aplicação em D-ARQ-45/D-ARQ-46 — `montar_fds(blocos) -> FDS` (`transcricao_fds.py`), porta de entrada única de produção verbatim→FDS, fork A ratificado sobre fork B (construção manual descartada); teste de integração fim-a-fim pareado 1:1 contra gabarito `fds_t65.tinta_acrilica()`. Suíte 488→491, mypy --strict delta-zero. Commit `3eb0d21`, merge `1038d7a`, PR #131 (PR #130 para a parte META). Nenhuma R-* alterada. |
| v78 | 02/07/2026 | Sessão 003.BD (CONHECIMENTO/medição → ARQUITETURA): D-ARQ-47 adicionada — contrato de invocação e gate do transcritor-LLM-FDS (5 cláusulas: LLM recebe texto/emite `tuple[BlocoVerbatim,...]` candidato; invocação injetável nunca-global testável sem API; gate de FORMA não-conteúdo; revisão-RT-sobre-verbatim ancorada em R-PGR-01/D-ARQ-33 cl.4 = admissão do candidato; roteamento por formato-de-token). Medição (B): patologia 1 de DT-003AS-01 DESBLOQUEADA — grid fundido Ciplan/Tigre transcritível por LLM sobre `extract_text` (Tigre 7/7, Ciplan 8/8 vs. `fds_t65`); fusão = interleave de coluna, não perda de dado; ordem de coluna inverte por fabricante → roteia por formato. Reenquadra D-ARQ-46 (bloqueio era ausência de LLM real, não impossibilidade). DT-003AS-01 segue ABERTA (IMPL do transcritor-LLM + `extrair_texto_fds` greenfield pendente); DT-003M-01 intocada (recorte A). Nenhuma regra clínica criada/alterada. Sem código. |
| v79 | 02/07/2026 | Sessão 003.BE (IMPLEMENTAÇÃO): nota de aplicação 003.BE em D-ARQ-47 — `extrair_texto_fds` materializada (recorte âncora-por-título com sobre-inclusão até fim-da-página-do-título-fim; núcleo puro `_recortar_composicao` + wrapper; 16 testes, suíte 491→507; skipif seletivo corrigido por amend pré-push). Nenhuma regra clínica criada/alterada. Commit `db884e2`, merge `221f454`, PR #134. |
| v80 | 02/07/2026 | Sessão 003.BF (IMPLEMENTAÇÃO): nota de aplicação 003.BF em D-ARQ-47 — invocação injetável (`TranscritorLLM` Protocol + `transcrever_fds`) + `gate_forma` (cl.3, reusa `parsear_faixa`; reprovado → Pendencia bloqueante `forma_verbatim_fds`) + harness mockado tinta/Ciplan consumindo `extrair_texto_fds` real; cl.4 preservada (sem compositor de produção). 10 testes, suíte 507→517. Nenhuma regra clínica criada/alterada. Commit `0cf24fd`, merge `591a4d8`, PR #136. |
| v81 | 03/07/2026 | Sessão 003.BG (IMPLEMENTAÇÃO fatia (e1)): D-ARQ-48 adicionada (fronteira de impureza — adaptador-LLM fora do motor, invariante de pureza testável via AST) + nota 003.BG em D-ARQ-47 (`TranscritorGemini` real + `preparar_composicao`; falha de invocação → `TranscricaoIndisponivel`→`Pendencia`, não `()` silencioso; para antes de `montar_fds`, cl.4 intacta). Adaptador Gemini NÃO exercido ao vivo (`@requer_api` skipado) — validação = pré-requisito bloqueante de (e2). 517→538 verdes, mypy delta-zero. Commit `34077c9`+`879a085`, merge `391a2da`, PR #138. Nenhuma R-* criada/alterada. |
| v82 | 05/07/2026 | Sessão 003.BH (CONHECIMENTO/medição + fix): validação ao vivo de (e1) sob DT-003AS-01 — 3/3 `@requer_api` passed (ciplan/tigre/tinta), ressalva ESCRITO-NÃO-VERIFICADO de 003.BG resolvida. Medição revelou 4º modo de falha de invocação: HTTP 200 com finishReason=MAX_TOKENS (thinking do gemini-2.5-flash compartilha o budget de `maxOutputTokens`; thoughtsTokenCount medido 4320–13231; truncamento não-determinístico). Nota 003.BH em D-ARQ-48: gate de integridade no adaptador (só 200+STOP atravessa a fronteira; teto removido do payload). Suíte 538→540, mypy delta-zero. Commit `fe1b908`, merge `9689fc3`, PR #140. Nenhuma R-* criada/alterada. |
| v83 | 05/07/2026 | Sessão 003.BI (IMPLEMENTAÇÃO fatia (e2)): nota de aplicação 003.BI em D-ARQ-47 — FECHA DT-003AS-01. Módulo greenfield `motor/revisao_verbatim.py` (puro, D-ARQ-48 preservada): `VerbatimInvalido`, `serializar_verbatim`/`desserializar_verbatim` (JSON envelope `{"versao":1,"blocos":[...]}`, schema estrito anti-erro-silencioso, round-trip byte-exato incl. `\n` intra-token), `montar_fds_revisado` (`gate_forma`→`montar_fds` sobre o verbatim PÓS-revisão-RT, cl.4, sem violar o bypass vedado em `transcritor_fds.py`). 17 testes, suíte 540→557, 3 skipped, mypy delta-zero. Revisão do Arquiteto sem correção. Commit `d5c60d4`, merge `0b89904`, PR #142. Nenhuma R-* criada/alterada. |
| v84 | 05/07/2026 | Sessão 003.BJ (ARQUITETURA): D-ARQ-49 adicionada — contrato do parse-PGR (instância-PGR de D-ARQ-41; irmão de D-ARQ-42 do lado-PGR). 4 partes: (1) bicamada interna parse-doc↔transcrição-LLM; (2) recorte da 1ª fatia = esqueleto GHE `{id,nome}` + cargos/riscos/quantificação crus + FDS apontadas (EPIs/psicossocial/gates diferidos); (3) semântica da "PGR transcrita" cravada, forma concreta do tipo = IMPL (D-ARQ-22); (4) gabarito `pgr_viverde.py` ↔ PGR Viverde `.docx`/`.pdf` em disco, mecanismo `termo→slug`+prompt+parse-doc adiados por medição (molde D-ARQ-42→003.AN). Gate de estado real: parse-PGR greenfield (grep zero), gabarito-par em disco, `tipos.PGR` já materializado (Parte C). Recorte ratificado pelo Diovanni. Sem código. Nenhuma R-* criada/alterada. |
| v85 | 06/07/2026 | Sessão 003.BK (CONHECIMENTO/medição): D-ARQ-50 adicionada — medição do PGR Viverde `.docx`/`.pdf` ↔ `pgr_viverde.py` fecha 2 pontos de D-ARQ-49 P4. P1 parse-doc = PDF `pdfplumber.extract_text` text-puro (não `.docx`), por universalidade (D-ARQ-06) + reuso do paradigma FDS (D-ARQ-AY) — `.docx` é mais colunar no grid mas funde o header GHE e não é universal no acervo; `.docx` = cross-check/fallback. P2 termo→slug = (c)-shaped: LLM normaliza linguisticamente bounded + separa agente/quantificação, NÃO emite slug; resolver determinístico = autoridade de slug + flag de confiança; typo-tail (baixa criticidade) → revisão, não erro silencioso (gate D-ARQ-41-P1 / D-ARQ-22). P3 catálogo C1–C3 (casamento-de-forma 42-blocos vs 32-GHEs; gabarito forte-esqueleto/fraco-FDS-apontada; carga semântica bounded medida). Verificação crítica: teste de perda-silenciosa do `extract_text` passou. Zero OCR (FPDF nativo). Sem código. Nenhuma R-* criada/alterada. |
| v86 | 06/07/2026 | Sessão 003.BL (IMPLEMENTAÇÃO): correção de literal em D-ARQ-50 (gate de estado real): "78,2/78,8 dB(A)" → "78,8 dB(A)" — o "78,2" era fantasma (coordenada vetorial no XML do .docx, não texto; docx↔pdf idênticos nos valores dB, reforça P1). Mesma ID, decisão intacta, sem D-ARQ nova. Entrega da sessão: extrair_texto_pgr (parse-doc do parse-PGR, D-ARQ-50 P1) no main via PR #146, 557→562 verdes. |
| v87 | 06/07/2026 | Sessão 003.BM (IMPLEMENTAÇÃO): nota em D-ARQ-50 (mesma ID) — âncora do recorte-GHE é verbatim sem normalização, com literais da medição 003.BM (42 blocos, 1ª âncora pág. 33, última pág. 146, cauda 4 págs., bloco cruza página). Entrega da sessão: recortar_blocos_ghe (2ª fatia do parse-PGR, D-ARQ-49 P2) no main via PR #148, 562→569 verdes. Nenhuma R-* criada/alterada. |
| v88 | 06/07/2026 | Sessão 003.BN (IMPLEMENTAÇÃO): nota de aplicação em D-ARQ-49 — P3 fechado; GHEVerbatim/RiscoVerbatim (sem id, D-ARQ-50 C1/D-ARQ-22) + transcrever_ghes + gate_forma_ghe (molde D-ARQ-47) em transcritor_pgr.py. LLM mockado, 8 testes. Suíte 569→577. Commit d4fa02a, merge 94bd5c4, PR #150. |
| v89 | 06/07/2026 | Sessão 003.BO (IMPLEMENTAÇÃO): notas em D-ARQ-49 (regra 3c — perigo de acidente como agente, quantificacao="") e D-ARQ-50 (correção de literal — fonte geradora forma-longa "Thinner/Zarcão e tinta esmalte sintético"; 003.BK citava forma curta). Entrega: TranscritorGeminiGHE (cliente-LLM real do transcritor-GHE, 4ª fatia do parse-PGR) + validação ao vivo Viverde verde no main via PR #152, 577→585 verdes. DT-003BO-01 aberta (observabilidade da cascata). Nenhuma R-* criada/alterada. |
| v90 | 07/07/2026 | Sessão 003.BP (IMPLEMENTAÇÃO): nota de aplicação 003.BP em D-ARQ-50 — Parte 2 materializada em motor/resolvedor_termos.py (normalização determinística + índice com aliases termos:/colisão→ValueError + fuzzy Levenshtein ≤2 único-candidato sempre FUZZY + Pendencia vocabulario_ausente não-bloqueante); campo termos: não populado (sessão de dado futura); isolado sem consumidor (molde 003.J/003.S). Suíte 585→597. Commit 6bbbce6, merge 4abeaf9, PR #154. |
| v91 | 07/07/2026 | Sessão 003.BQ fatia 1a (IMPLEMENTAÇÃO): D-ARQ-51 criada — hidratação GHEVerbatim→tipos.PGR (consumidor de produção do resolver termo→slug). Fatia 1a materializa o contrato de tipo: RiscoPGR.agente str→Optional[str] + guard None não-bloqueante na Fase A do Stage 2 (seams 2/3). Suíte 597→598. Commit b38a76a, merge e87759f, PR #156. Nenhuma R-* tocada. |
| v92 | 07/07/2026 | Sessão 003.BQ fatia 1b (IMPLEMENTAÇÃO): nota de aplicação em D-ARQ-51 — `hidratar_ghe` materializa os seams 1 (id posicional `GHE-{posicao:02d}`) e 4 (recorte identidade-primeiro, `quantificacao=None`); tri-estado do resolver hidratado com pendência FUZZY fabricada na hidratação. Suíte 598→604. Commits b039f0d+682d106, merge 663f9f1, PR #158. Nenhuma R-* tocada. |
| v93 | 07/07/2026 | Sessão 003.BR (IMPLEMENTAÇÃO): nota de aplicação 003.BR em D-ARQ-51 — costura plural `hidratar_pgr` (consumidor de produção de `hidratar_ghe`; envelope por parâmetro sem default; primeiro e2e verbatim→Resultado em teste). Suíte 604→609, mypy delta-zero. Commits `110b2c8`+`3039af4`, merge PR #160. Nenhuma R-* criada/alterada. |
| v94 | 07/07/2026 | Sessão 003.BS (IMPLEMENTAÇÃO): D-ARQ-52 criada — plug de produção lado-PGR (`adaptadores/orquestracao_pgr.py`: `preparar_ghes`+`processar_arquivo_pgr`), costura arquivo→Resultado. Espelho de `orquestracao_fds.py`, mas atravessa a hidratação (assimetria não-bloqueante D-ARQ-29/D-ARQ-50 P2); envelope RT-supplied (paliativo: fonte real é transcrição-de-topo); `entrada.py` intocado. Primeiro e2e REAL arquivo→Resultado (PDF Viverde, só LLM mockado). Fecha a travessia Viverde, não a universal. Suíte 609→614, mypy delta-zero. Commit `f4405a3`, merge PR #162 (`980fb9d`). Nenhuma R-* criada/alterada. |
| v95 | 08/07/2026 | Sessão 003.BT (ARQUITETURA): D-ARQ-53 criada — transcrição-de-topo do envelope (instância-envelope de D-ARQ-41; irmã de D-ARQ-49), caminho de saída do paliativo "envelope RT-supplied" de D-ARQ-52 seam 3. 4 partes: (1) bicamada interna recorte-de-topo (inverso de `recortar_blocos_ghe`, pega o topo descartado) → transcrição-LLM; (2) insight central — gate ELIMINATÓRIO (R-PGR-01/06) exige pré-preenchimento + confirmação-RT (molde D-ARQ-47 cl.4), NÃO document-derived autônomo (confiante-e-errado passa em silêncio, classe D-ARQ-22); (3) `EnvelopeVerbatim` texto-cru semântica cravada, forma = IMPL; (4) gabarito topo-Viverde, mecanismo (formatos de data, localização, evidência engenheiro-vs-técnico) adiado por medição — topo nunca medido. Gate de estado real: envelope `date`/`bool` em `tipos.py`, gates em `estagios/gates.py`, topo descartado por `recortar_blocos_ghe`, seam RT-supplied pronto. Universalidade: envelope é exigência NR-01 de qualquer PGR. Duas passadas (2ª corrigiu document-derived autônomo → revisão-RT). Sem código. Nenhuma R-* criada/alterada. |
| v96 | 08/07/2026 | Sessão 003.BW (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-53 — EnvelopeVerbatim + TranscritorTopo (Protocol) + gate_forma_topo em transcritor_topo.py novo, LLM mockado, gabarito 003.BV; 5 decisões IMPL (plural de candidatas, sem campo de assinatura, bloco implementação excluído por consumo-zero, dataclass própria, módulo próprio); achado typo "TÉNICA" na camada de texto do topo Viverde (correção factual a 003.BV). Commits 3cdef6f+16f2c6b, PR #168, merge 321c6da. Suíte 619→626, mypy delta-zero. |
| v97 | 08/07/2026 | Sessão 003.BX (IMPLEMENTAÇÃO): nota de aplicação fatia 3 em D-ARQ-53 — resolvedor_topo.py (validade mês-ano PT-BR multi-candidata, só o medido, 1º dia do mês [INTERPRETADO]) + revisao_envelope.py (seam confirmação-RT, JSON v1 estrito, credencial crua, assinatura sem default) + CandidataValidade/EnvelopeConfirmado em tipos.py; 7 decisões IMPL ratificadas; fix ValueError (ano fora do range) formulado na revisão. Commits 0f2c52c+1e51cd4, PR #170, merge cc87e88. Suíte 626→652, mypy delta-zero. DT-003BV-01 segue ABERTA (pergunta de método à Carolini). |
| v98 | 08/07/2026 | Sessão 003.BY (IMPLEMENTAÇÃO): nota de aplicação fatia 4 em D-ARQ-53 (DECISÃO COMPLETA 4/4) — `preparar_envelope` em `orquestracao_pgr.py` (ida completa até o artefato JSON, parando antes da confirmação-RT) + `processar_arquivo_pgr` passa a receber `envelope: EnvelopeConfirmado`, fechando o paliativo "envelope RT-supplied" de D-ARQ-52 seam 3 no nível do adaptador. 6 decisões IMPL ratificadas. Commits 7549fd4+5ab8c8d, PR #172, merge a081a3f. Suíte 652→658, mypy delta-zero. Remanescente explícito: cliente-LLM real do topo + superfície RT (UI/CLI). |
| v99 | 09/07/2026 | Sessão 003.BZ (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-51 — `parsear_quantificacao` em `motor/quantificacao.py` novo (módulo próprio, molde `parsear_faixa` replicado local, não importado); `hidratar_ghe` parseia 1× por risco antes do tri-estado; `Pendencia quantificacao_nao_parseada` não-bloqueante (anti-supressão D-ARQ-31/35). Recorte remanescente explícito: `relacao_LT` sempre `None` — classificação dB→relação é regra clínica não formalizada, exige `R-*` nova em fatia futura. 7 decisões IMPL ratificadas (as 6 da sessão + aceitação case-insensitive de unidade, desvio MENOR aceito na revisão do Arquiteto). Commits 4f1866d+3a4baf5, PR #174, merge 79e9499. Suíte 658→671, mypy delta-zero. |
| v100 | 09/07/2026 | Sessão 003.CA (IMPLEMENTAÇÃO): nota de aplicação cliente-LLM real do topo em D-ARQ-53 — `TranscritorGeminiTopo` (molde adaptador GHE, cascata reusada), sonda ao vivo 4/4 no gabarito 003.BV, 1 desvio MENOR aceito. Commits 3fe3b3d+30fdd8b, PR #176, merge 49a30ec. Suíte 671→678, mypy delta-zero. Remanescente: superfície RT (UI/CLI). |
| v101 | 09/07/2026 | Sessão 003.CB (CONHECIMENTO): nota de aplicação 003.CB em D-ARQ-51 — **R-RUIDO-01** (PROTOCOLO v43) destrava a fatia 3 (`relacao_LT` sempre `None` até 003.BZ era bloqueio clínico, não de engenharia): limiares NEN <80/80–85/≥85 → `abaixo_acao`/`entre_acao_LT`/`acima_LT`, `[DERIVADO]` NR-15 Anexo 1 (85=LT) + NR-09/NHO-01 (80=nível de ação), conferidos via web (D-ARQ-27). Fatia 3 desbloqueada p/ IMPL (cobertura por faixa exigida). DT-003CB-01 herdada à IMPL (`valor` não discrimina NEN vs SPL/pico — irmã de DT-002V-01). Sem código. Nenhum número de suíte movido (PAINEL não re-tira — sem merge). |
| v102 | 09/07/2026 | Sessão 003.CC (IMPLEMENTAÇÃO): nota de aplicação fatia 3 em D-ARQ-51 — classificador R-RUIDO-01 (`motor/classificacao_ruido.py` novo, aplicado em `hidratar_ghe` pós-resolução quando slug=="ruido"; `acima_acao` nunca emitido; predicado e R-AUD-* intocados). Recorte remanescente da 003.BZ fechado. DT-003CB-01 documentada em docstring, segue ABERTA. Commit `9500c2a`, PR #179, merge `975ae85`. Suíte 678→693, mypy delta-zero. Nenhuma R-* criada/alterada (R-RUIDO-01 já era v43; ganha status implementada-com-teste). |
| v103 | 09/07/2026 | Sessão 003.CD (ARQUITETURA): **D-ARQ-54** adicionada — superfície RT como apresentação-pura sobre o contrato ida/volta já existente (lógica-de-domínio ZERO; preserva D-ARQ-09 e "seam humano fora do adaptador"); um contrato de apresentação instanciado nos dois seams (envelope `revisao_envelope.py` + FDS `revisao_verbatim.py`); **CLI primeiro** (exerce o contrato antes de framework; web herda o mesmo artefato), decisão de Diovanni; escopo = só os dois seams de confirmação (render de saída matriz/pendências fica FORA, D-ARQ próprio). Fecha o remanescente "superfície RT (UI/CLI)" de D-ARQ-53. Gate de estado real: pares serializar/desserializar em disco, sem consumidor humano. Nenhuma R-* criada/alterada (PROTOCOLO v44 intocado). Sem código. |
| v104 | 10/07/2026 | Sessão 003.CE (IMPLEMENTAÇÃO): nota de aplicação fatia 1 em D-ARQ-54 — CLI do envelope em pacote novo `agente_medico/superficie/` (`cli_envelope.py`, apresentação-pura, lógica-de-domínio zero); `revisar_envelope` renderiza credencial+candidatas+proposta, coleta validade (Enter mantém proposta, validação só de forma) e assinatura_engenheiro (s/n sem default), self-check via `desserializar_confirmacao`. Achado pré-merge: EOF em stdin causava loop infinito, corrigido com `EOFError` + 2 testes. Gabarito envelope-Viverde fim-a-fim. Commits 62ca3e5+0a4f4fc, merge a0153a8, PR #182. Suíte 697→708 (704 passed + 4 skipped), mypy --strict delta-zero. Fatias 2–4 (CLI FDS, unificação, web) abertas. |
| v105 | 10/07/2026 | Sessão 003.CF (IMPLEMENTAÇÃO): nota de aplicação fatia 2 em D-ARQ-54 — CLI da FDS em `superficie/cli_fds.py` (apresentação-pura, lógica-de-domínio zero); `revisar_verbatim` renderiza blocos/membros crus, coleta faixa (Enter mantém) e revisão por membro (`[Enter mantém / e edita / r remove]`, drill-down só no "e"; sem "adicionar" — procedência de transcrição), self-check via `desserializar_verbatim` (`gate_forma` segue só em `montar_fds_revisado`); `EOFError` antes do strip em todo prompt (lição 003.CE). Defeito pego em revisão pré-merge: gabarito com literais inventados em vez de `fds_verbatim_t65` cru — corrigido (roundtrip byte-exato, `\n` intra-token). Remanescente nomeado: adaptador FDS sem emissor do artefato-ida em produção. Commits 45ca92b+3b7f5ee, merge 7c272a8, PR #184. Suíte 708→720 (716 passed + 4 skipped), mypy --strict delta-zero. Fatias 3–4 abertas (gatilho da 3 satisfeito). |
| v106 | 10/07/2026 | Sessão 003.CG (IMPLEMENTAÇÃO): nota de aplicação fatia 3 em D-ARQ-54 — contrato de apresentação unificado em `superficie/apresentacao.py` (exceção única, loader, ler_resposta, prompt_enter_mantem, conduzir_revisao com revisar-callable, executar_main); CLIs viram instâncias, testes existentes intocados (gate de regressão byte-idêntico). Commits dfdd4fa+fec0739, merge bb426a5, PR #186. Suíte 720→727, mypy delta-zero. Resta fatia 4 (web). |
| v107 | 10/07/2026 | Sessão 003.CI (ARQUITETURA): **D-ARQ-55** adicionada — recorte (B) da transcrição-FDS (perigo-transcrição, passo 1 do cluster ratificado em 003.CH). `MembroVerbatim`/`Componente` ganham `frases_h: tuple[str,...]` cru (por-membro, H-code GHS verbatim); mapa determinístico resolver-side {H334,H317}→`is_sensibilizante` (só sensibilização); H350/H351 REFUTADO em `is_carcinogeno_iarc` (GHS≠IARC, D-ARQ-22) → DT-003CI-01 deferida (futura `is_carcinogeno_ghs`, append cl.5); confiança ancora R-FDS-06 (confia conteúdo) + revisão-RT (D-ARQ-47 cl.4, `_CAMPOS_MEMBRO`+`frases_h`), gate de FORMA. DT-003T-01 FECHA; DT-003M-01/DT-003M-02(B) ganham pré-condição, fecham no passo 2 (reordenação ramo-0). Mecanismo de localização por-membro adiado por medição. Nenhuma R-* criada/alterada (R-FDS-06 ganha nota de aplicação, PROTOCOLO v46). Sem código. PAINEL não re-tirado (nenhum número movido). |
| v108 | 10/07/2026 | Sessão 003.CJ (IMPLEMENTAÇÃO): **D-ARQ-55 implementada** — PR #190 (`bc78788`/`4565eb0`/`d4adb36`): `frases_h` em `MembroVerbatim`/`Componente` (cru, propagado intocado pela montagem); `mapear_frases_h` resolver-side ({H334,H317}→`is_sensibilizante`, forma `H\d{3}` estrita, pendência `frase_h_malformada` não-bloqueante, flag só liga, todos os ramos do gate_cas inclusive CAS-oculto); `frases_h` OBRIGATÓRIO no artefato-RT (`versao` mantida 1) + `cli_fds` renderiza/edita/preserva; fixtures: SI2 `("H334","H317")` (medido), `fds_verbatim_t65` `()` com nota de medição pendente. Suite 723→740 (+17). Nota de implementação em D-ARQ-55; 7 decisões de IMPL no HISTORICO 003.CJ. PROTOCOLO v47 (R-FDS-06 implementada). PAINEL re-tirado (R-FDS-06 footprint executável: 18→19/42). |
| v109 | 10/07/2026 | Sessão 003.CK (ARQUITETURA→IMPLEMENTAÇÃO): **D-ARQ-56** adicionada e implementada na mesma sessão (PR #192, merge `f7aa825`) — passo 2 do cluster-FDS: bypass antes do slug-check em `materialidade()` (SI2/CAS-oculto → MATERIAL); Fase C tripartida no sem-slug ((a) `bypass_sem_slug` bloqueante sem promover Risco; (b) inerte-declarado não-bloqueante via R-FDS-06; (c) não-mapeado bloqueante D-ARQ-35); promoção-sem-slug deferida (DT-003CK-01, condicionada a regra clínica de sensibilizante genérico). **DT-003M-01 e DT-003M-02(B) FECHADAS.** Suite 740→744; mypy zero novo. PROTOCOLO v48. PAINEL re-tirado. |
| v111 | 11/07/2026 | Sessão 003.CN (ARQUITETURA): **D-ARQ-57** adicionada — localizador de blocos GHE (requisito (b) da 003.BS), consome DT-003CM-01. Âncora `SETOR/FUNÇÃO` verbatim única (n=1 Viverde, cobre 1/15) → repertório determinístico de reconhecedores GHE (`^(INVENTÁRIO DE RISCO )?GHE:? \d+( - título)?$`, formas 1–4), NÃO migra p/ LLM (D-ARQ-09/45 P1). Gate de segmentação anti-Vistamérica (densidade+contagem: bloco > X% das págs OU ≤1 bloco em doc >N págs → `segmentacao_implausivel` bloqueante) — só-troca-de-âncora deixaria o caso-Vistamérica (1 âncora → bloco de ~137 págs) passar. Família cargo-based (forma 5, 4/15) = reconhecer+sinalizar `pgr_cargo_based` bloqueante; recorte-por-cargo é fatia futura própria. `recortar_topo` solidário (mesma âncora). Custo sinalizado: recorte Viverde 42→31 blocos (regressão de gabarito na IMPL). Duas escolhas ratificadas pelo Diovanni (cargo-based reconhecer-não-construir; gate densidade+contagem). DT-003CM-01 segue ABERTA até a IMPL. Nenhuma R-* criada/alterada (PROTOCOLO v49 intocado). Sem código. PAINEL não re-tirado (nenhum número movido). |
| v112 | 11/07/2026 | Sessão 003.CO (IMPLEMENTAÇÃO): **andamento em D-ARQ-57** — peça 1 IMPLEMENTADA (`eh_cabecalho_ghe`, repertório em disjunção, regex `fullmatch` com teto 80 chars e `\s*-\s*`; gabarito Viverde 31 confirmado; conflação da 2ª seção resolvida por design). Peças 2 e 3 pendentes. PR #198, merge `4571ec6`. Nenhuma R-* criada/alterada. |
| v110 | 11/07/2026 | Sessão 003.CL (IMPLEMENTAÇÃO): nota de aplicação fatia 4 em D-ARQ-54 — **D-ARQ-54 COMPLETA (4/4 fatias)**: web como adaptador irmão das CLIs (`superficie/web_envelope.py`/`web_fds.py`, Streamlit + AppTest determinístico); `emitir_volta` extraído em `apresentacao.py`; núcleo puro + casca fina; semânticas das CLIs preservadas (assinatura sem default 003.BV; sem adicionar membro). Achado pré-merge D-ARQ-22 corrigido (self-check mascarado como "Data inválida" no web do envelope, fixup `f8819df`). PR #194, merge `7652b36`. Suíte 744→754+4; mypy delta-zero (46). PROTOCOLO v48 intocado (nenhuma R-*). PAINEL re-tirado (marco superfície RT fecha). |
| v113 | 11/07/2026 | Sessão 003.CP (IMPLEMENTAÇÃO): **andamento em D-ARQ-57** — peça 2 IMPLEMENTADA (`avaliar_segmentacao`, gate puro densidade+contagem sobre a fronteira de bloco de `recortar_blocos_ghe`, `segmentacao_implausivel` bloqueante). Limiares X=40%/N=10 calibrados por medição direta dos 15 PGRs (legítimos ≤34,8%, implausíveis ≥44,4%); densidade pega a armadilha-Floramazônia (contagem sozinha não pegaria). Falsos-positivos aceitos por design (TPB Andrade, R78 Naturia). Peça 3 (cargo-based) pendente. PR #200, merge `81e9a9b`. Nenhuma R-* criada/alterada. |
| v114 | 12/07/2026 | Sessão 003.CQ (IMPLEMENTAÇÃO): nota em D-ARQ-57 — peça 3 implementada, 1ª leva completa (3/3); exclusão mútua família→gate selada em avaliar_estrutura. PR #202. |
| v115 | 12/07/2026 | Sessão 003.CR (IMPLEMENTAÇÃO): **andamento em D-ARQ-57** — `avaliar_estrutura` PLUGADO em produção (`preparar_ghes`: gate de estrutura antes do recorte/transcrição, bloqueia cargo-based/segmentação implausível sem gastar LLM). Refino da peça 2: piso de páginas (`_LIMIAR_PAGINAS_DOC_MINIMO`) espelhado no ramo de densidade de `avaliar_segmentacao` — doc pequeno com bloco único saturava o percentual (falso-`segmentacao_implausivel`, quebrava 5 testes legítimos); densidade só julga acima do piso já presente na contagem (muda saída para docs ≤ piso). Regressão coberta. Commits `e73b281`+`82a4a81`, PR #204, merge `0e95574`. Suíte 784→788+4; mypy delta-zero (46). Nenhuma R-* criada/alterada. PAINEL não re-tirado (nenhum número de headline movido). |
| v116 | 12/07/2026 | Sessão 003.CS (ARQUITETURA): **andamento em D-ARQ-57** — 1ª validação out-of-sample (2 PGRs reais fora de construção civil). Bertoncini (metalúrgica/ESO) → `pgr_cargo_based`, família acertou; ação nenhuma. HU-UFGD (saúde/EBSERH, 197 págs) → `segmentacao_implausivel` (0 âncoras): sonda revelou GHE-conceitual (~23 GHES por Unidade/Setor, sem numeração) — forma EBSERH que a âncora `GHE: NN` não cobre. Rede de segurança validada (bloqueia, não gera lixo); furo real e específico do repertório de âncora GHE, não da família/gate. **DT-003CS-01** aberta (extensão de repertório forma EBSERH, saúde). Sem código, sem R-*. PROTOCOLO inalterado. PAINEL não re-tirado. |
| v117 | 12/07/2026 | Sessão 003.CT (ARQUITETURA): **andamento em D-ARQ-38** (fatia d, data-desbloqueada pelo mapa 003.AD) — forma do emissor de biomonitoramento decidida: **família regra-por-agente** `R-BIO-04-<agente>` (molde R-PKG-BZ/D-ARQ-20), biomarcador no `emite`, momentos por Quadro (EE→[per]; SC→[adm,per,RT,MR,dem]), 6M; zero motor, zero schema, só `regras.yaml` + `exames.yaml`. Cardinalidade: 1:1 / "e" (chumbo 2 exames) / "ou" 1º canônico+nota [INTERPRETADO]. Benzeno/Mn ficam pacote; Cr⁶⁺ fora (não-vocab). Escopo fatia d só; R-CLI-02 (c) segue travada em D-ARQ-39. Spec 12 regras. R-BIO-04 mantém ID, sem PROTOCOLO novo, sem R- nova. Sem código. PAINEL não re-tirado (ARQUITETURA, nenhum número movido). |
| v118 | 13/07/2026 | Sessão 003.CU (IMPLEMENTAÇÃO): **D-ARQ-38 fatia (d) materializada** (família `R-BIO-04-<agente>`, 12 regras + 13 slugs, zero motor via `stage_5_emissao`) + **D-ARQ-58 criada e implementada** (fallback de predicado por identidade de agente — habilitador da família; typo ainda levanta). Correção pré-IMPL do tolueno: `tolueno_urina` (spec 003.CT) era erro → `ortocresol_urina` (NR-7 rev.2020 o-cresol, confirmado Matriz Patrícia); 4 "bordas ou" colapsadas (Matriz fixa 1 canônico, estireno=soma). Suíte 788→804+4; mypy delta-zero (46). Commit `5cf2f24`, merge PR #208 (`2f2ec10`). R-BIO-04 mantém ID; PROTOCOLO v54 (changelog tolueno), sem R- nova. PAINEL não re-tirado (headline 19/42 não move — R-BIO-04 já contado; ver HISTORICO 003.CU). |
| v119 | 13/07/2026 | Sessão 003.CV (IMPLEMENTAÇÃO): **extensão de D-ARQ-38 ao Quadro 2/SC completo** — 3 regras `R-BIO-04-<agente>` (cádmio, fluoretos, inseticidas inibidores da colinesterase), todas `[adm,per,RT,MR,dem]` 6M; Quadro 2 fecha 4/4 (antes só chumbo). Zero motor (D-ARQ-58 já resolve). Biomarcadores canônicos da Matriz Patrícia 06/2025; inseticida→acetilcolinesterase eritrocitária `[INTERPRETADO]` (butirilcolinesterase é a alternativa OU); slug-classe único. Bloqueador de gate: `test_indice_real_tem_45_entradas` 45→48 (guard de inventário irmão do vocab 22→25), atualizado por decisão do Arquiteto. Suíte 804→807+4; mypy delta-zero (46). Commit `c198ff1`, merge PR #210 (`714aa68`). R-BIO-04 mantém ID; PROTOCOLO v55 (changelog Quadro 2 completo), sem R- nova. PAINEL não re-tirado (nenhum dos 3 números move — família já contada, DT-003M-02(A) é vocabulário-FDS, não biomonitoramento). |
| v120 | 13/07/2026 | Sessão 003.CW (IMPLEMENTAÇÃO): **extensão de D-ARQ-38 ao Quadro 1/EE lote 1** — 9 regras `R-BIO-04-<agente>` (cromo hexavalente, cobalto, fenol, metanol, diclorometano, etilbenzeno, anilina, nitrobenzeno, indutores de metahemoglobina), todas `[per]` 6M / um exame; cluster metahemoglobina = 3 slugs (anilina+nitrobenzeno nomeados no Anexo + classe), exame compartilhado; anilina "ou"→canônico metahemoglobina `[INTERPRETADO]`; etilbenzeno reusa slug do estireno; cromo um exame (2 critérios). Zero motor (D-ARQ-58). Guards: exames 25→31, índice 48→57. EE Quadro 1: 12/41→21/41; total R-BIO-04 = 24. Suíte 807→816+4; mypy delta-zero (46). Commit `ff06ace`, merge PR #212 (`95dc482`). R-BIO-04 mantém ID; PROTOCOLO v56, sem R- nova. PAINEL não re-tirado. **(Linha reposta na 003.CX — omitida no fechamento da 003.CW; higiene de conformidade.)** |
| v121 | 15/07/2026 | Sessão 003.CX (ARQUITETURA): **D-ARQ-59 adicionada** — o refactor família R-BIO-04→"estágio genérico" é gatilho falso; **limiar ~25 aposentado**, EE lote 2 desbloqueado. Razão: motor já genérico desde D-ARQ-58 (nada de código por-agente a eliminar); (ID + `base_normativa`) por regra é ativo de rastreabilidade PCMSO; fatos clínicos são dado (D-ARQ-07), estágio genérico arriscaria empurrá-los a código. Custo real (edição Quadro-wide a 60–100+ regras) endereçável por teste de consistência `§5.9`↔`regras.yaml` (proposto, não implementado), não por refactor. Correção do kickoff: "molde D-ARQ-54" = princípio P3, não a decisão D-ARQ-54 (superfície RT). Sem código; R-* e PROTOCOLO inalterados. PAINEL não re-tirado (ARQUITETURA, nenhum número movido). |
| v122 | 15/07/2026 | Sessão 003.CY (IMPLEMENTAÇÃO): **D-ARQ-60 adicionada** — materializa o teste de consistência §5.9↔regras.yaml proposto em D-ARQ-59 (guardião `test_consistencia_mapa59_regras.py`). Reconciliação nome-de-exibição §5.9→slug mora no guardião via registro explícito `APELIDOS_MAPA` (sibling de `EXCECOES_PACOTE`; benzeno→R-PKG-BZ validado); rejeitadas normalização (não-determinística) e coluna-slug no §5.9 (duplicação 19/25 + perda de qualificador clínico). Corolário: header §5.9 `agente (slug)`→`agente` (coluna é fonte humana, não chave). Nota impl: detecção de tabela por heading 5.9 + separador (não palavras-chave, colidia com prosa de changelog); `protocolo.regras` é list[dict]. Poder discriminante confirmado (regra órfã / apelido faltante). Suíte 816+4→818+4, mypy delta-zero (46). Commit `c934d72`, merge `b2c9d58` PR #215. R-BIO-04 mantém ID; PROTOCOLO tocado só no header §5.9 (cosmético), sem R- nova. PAINEL não re-tira. |
| v123 | 16/07/2026 | Sessão 003.CZ (ARQUITETURA): **andamento em D-ARQ-57 + reenquadramento de DT-003CS-01**. Censo out-of-sample n=3 (pdfplumber host, 3 PGRs EBSERH reais): o template EBSERH **vigente** (`Doc v7.0 08/2023`, convergente UFGD-v7 + HUMAP) é **card cargo/lotação**, não GHE-conceitual; o witness GHES/`ANÁLISE NN` da 003.CS é doc **legado** UFGD (n=1). Furo migra **peça 1 (âncora GHE) → peça 3 (família cargo-based)**: somar a `_RECONHECEDORES_CARGO` a tripla `^Lota[cç][aã]o:…Escala\s*de\s*Trabalho:…Qtde?:` (tolerante a space-collapse; `DADOS GERAIS` rejeitado por frágil). Colisão card↔GHES medida e descartada (n=3, nunca coexistem). GHES/ANÁLISE **aposentado** (anti-overfit). Recorte-por-cargo (DT-003L-01 forma 6) **elevado** a alavanca do setor saúde. Paliativo: reconhecer+sinalizar é diagnóstico, não ingestão — EBSERH bloqueado até recorte-por-cargo. `[INCERTO]` dominância ~40 HUs (n=2). Sem código; R-* e PROTOCOLO inalterados. PAINEL não re-tirado (ARQUITETURA, nenhum número movido). |
| v124 | 16/07/2026 | Sessão 003.DA (IMPLEMENTAÇÃO): andamento D-ARQ-57 peça 3 — forma 4 do repertório cargo-based implementada (reconhecedor Lotação/Escala/Qtd, card do template corporativo EBSERH PGR.SOST.001; n=2 realizações medidas: espaçada UFGD-v7 e colada HUMAP). EBSERH-vigente agora roteia a pgr_cargo_based bloqueante, materializando o reenquadramento de DT-003CS-01 (003.CZ). 3 PGRs EBSERH públicos trackeados em matrizes_originais/ (precedente Ricco/Cjr 003.CQ). |
| v125 | 17/07/2026 | Sessão 003.DB (CONHECIMENTO/medição): andamento em D-ARQ-57 — anatomia do bloco-cargo medida (4 witnesses); família parte N:1 grupo-GHE vs 1:1 card, ambas reduzem a `GHEPGR`; recorte-por-cargo = reconhecedores + binding-por-posição, não 2ª unidade de bloco. Fork Ricco-Adm N:1 para a ARQUITETURA da peça 4 (003.DC). Nota em DT-003CS-01 (crit (2) medido). DT-003DB-01 no PROTOCOLO §11. Nenhuma R-* criada/alterada. Sem código. |
| v126 | 17/07/2026 | Sessão 003.DC (ARQUITETURA): **andamento em D-ARQ-57 — decisão da peça 4** (recorte-por-cargo reduz a `GHEPGR`). Fork N:1 (Ricco-Adm) resolvido **rota (i)**: header `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` entra em `_RECONHECEDORES_GHE` (N:1 é GHE estrutural+clínico, R-GHE-01 [VALIDADO]); rota (ii) rejeitada; recorte-por-cargo genuíno = só 1:1 (Cjr+EBSERH). Recorte 1:1 = `recortar_cards_cargo` + `_RECORTADORES_CARGO` (Lotação-tripla + `CARGO-CBO`; grid AIHA fora), card→GHEPGR de 1 cargo, `hidratar_ghe` inalterado; caveats DT-003DB-01 mortos por span. Peça 3 estreita (cargo recortável ingere / só-sinal-família segue `pgr_cargo_based`). Passagem de verificação (2ª passada, pedida pelo Diovanni) achou 3 furos: 4a atravessa gate+transcrição (não só âncora); Cjr GATED por design (1 card, ramo-contagem) → quem destrava é EBSERH; transcrição-de-card não existe (reuso assumido em silêncio). Fatiamento **4a-4d** (fork / recorte isolado / transcrição-card / plug — só 4d fecha DT-003CS-01); gate-a-recalibrar = bloqueador, não ajuste silencioso. Nota 003.DC em DT-003CS-01. DT-003DB-01/DT-003CS-01 seguem ABERTAS (consumidas). Nenhuma R-* criada/alterada. Sem código. PAINEL não re-tirado. |
| v127 | 17/07/2026 | Sessão 003.DD (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4a IMPLEMENTADA e mergeada** — forma 5 do repertório GHE (`_reconhece_cabecalho_informacoes_cargos_funcoes`, header N:1 `INFORMAÇ[OÕ]ES SOBRE CARGOS/FUNÇÕES NN`), rota (i) da 003.DC materializada; Ricco-Adm sai de `pgr_cargo_based`. **Decisão 003.DD-1:** classe `[OÕ]` no ponto medido, sem normalização NFC/NFD — perda de diacrítico determinística de fonte/glifo (Õ→O, codepoint `0x4f`) medida no Ricco-Adm real; verbatim-estrito codificaria defeito de extração como contrato, normalização mudaria a convenção VERBATIM da peça 1 inteira. **Decisão 003.DD-2:** Ricco-Adm fica GATED por densidade BY DESIGN — bloco 2 = 10/24 págs. = 41,7% > 40,0%; limiar NÃO recalibrado (margem restante vs. implausíveis ≥44,4% seria 2,7pp; calibração 003.CP tinha ~10pp); classe Cjr/V2-003.DC, witness do recorte (2 blocos, âncoras corretas), revisão humana bloqueante, anti-supressão vence. Dívida candidata (sem DT formal): cauda do último bloco infla densidade por sobre-inclusão (D-ARQ-22) — causa direta do gate; correção eventual é estrutural, não recalibração. Nota 003.DD em DT-003CS-01 (4a fechada, DT segue ABERTA até 4d). Suíte 825+4→830+4 (+5), mypy delta-zero (46). Commit `dfdcbc5`, merge PR #222 (`7ee4be9`). Nenhuma R-* criada/alterada. |
| v128 | 18/07/2026 | Sessão 003.DE (IMPLEMENTAÇÃO): não é D-ARQ numerado — linha de processo. `scripts/medir_painel.py` passa a ser o **instrumento oficial de re-tiragem** dos 3 números da Camada 2 do PAINEL_ESTADO.md (cobertura clínica, CAS, suíte), medindo direto do disco com escopo recursivo (`regras.yaml` ∪ `motor/**/*.py`) — sucessor do `git grep` manual usado até 003.CJ. A 1ª rodada do instrumento já pagou: expôs **drift de rótulo de superfície** na tabela Camada 2 do PAINEL (a linha "`regras.yaml` (dado)" mede `agentes.yaml`/`protocolos_especiais` também, sem declarar; `R-ECG-01`/`R-OP-01`/`R-VIS-01` nunca estiveram em `regras.yaml`) — achado registrado em HISTORICO 003.DE; correção da tabela em si fica para a re-tiragem formal do PAINEL, **não disparada nesta sessão**. Suíte 830+4→834+4 (+4), mypy delta-zero em `scripts/medir_painel.py`. Commits `bfb5292`+`f30592d`, merge PR #224 (`9502be9`). Nenhuma R-* criada/alterada. PROTOCOLO intacto. PAINEL não re-tirado. |
| v129 | 18/07/2026 | Sessão 003.DF (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4b IMPLEMENTADA e mergeada** — `recortar_cards_cargo` isolado (molde construir-sem-plugar 003.BP/BQ), `_RECORTADORES_CARGO` (2 membros, reuso de `_reconhece_lotacao_escala_qtd`/`_reconhece_cargo_cbo`, zero regex duplicada; grid AIHA e `CARGO/FUNÇÃO:` FORA — sinal-de-família ≠ âncora-de-recorte, 003.DC), `eh_ancora_card_cargo` espelho de `eh_cabecalho_ghe`. Gabarito real UFGD-v7 **105**/HUMAP **140**/Cjr **1** cards, EXATO, zero divergência; limiares intocados. 7 testes novos (sintéticos de fronteira + negativo grid-AIHA + 3 reais), falha explícita via stash (`ImportError` na coleta). Suíte 834+4→841+4 (+7); `mypy --strict motor/`: zero erros, delta-zero. Nota 003.DF em DT-003CS-01 (4b fechada, DT segue ABERTA até 4d). Commit `2bb8d20`, merge PR #226 (`64ccf06`). Nenhuma R-* criada/alterada. |
| v130 | 18/07/2026 | Sessão 003.DG (ARQUITETURA/medição): **andamento em D-ARQ-57 — especificação da fatia 4c**. Gabarito de forma do card EBSERH medido em 2 witnesses ricos (UFGD [16], HUMAP [51], 5 categorias cada); anatomia `[NN.N Cargo][DADOS GERAIS][Lotação: labels][valores][…RISCOS AMBIENTAIS…]`. Quatro decisões ratificadas: **003.DG-1** tipo de saída = reuso ESTRITO de `GHEVerbatim` (categoria/nível/tipo-de-exposição descartados — `hidratar_ghe` já emite `tipo=""`/`severidade=None` hardcoded, descartar é paridade e não regressão; carregá-los = campo de consumo-zero, rejeitado em 003.BW; dívida candidata nomeada: `tipo de exposição`/`3 Crítica` têm peso clínico p/ periodicidade); **003.DG-2** prompt-card DEDICADO (4 razões medidas: nome vem da linha-seguinte-à-âncora, cargo embutido/recuperado, space-collapse HUMAP, ordem de colunas divergente) — fecha o furo V3 de 003.DC; **003.DG-3** `gate_forma_ghe` reusado sem alteração (card todo-N/A → `riscos=()` aprova: forma legítima, não buraco); **003.DG-4** rota-de-recuperação do cargo na 4c, **4b NÃO reabre** (no UFGD o título `NN.N Cargo` cai na cauda do card anterior; recuperação do texto cheio = 104/104 caudas + card [0] do pré-âncora = 105/105; alternativa de estender o span rejeitada por reabrir código mergeado e herdar a fragilidade do `DADOS GERAIS`-como-âncora refutada em 003.CZ). Achados de medição: H1/H2 iniciais (5 e 97/104) eram ARTEFATO da regex de medição (títulos `13.100`–`13.106`, sufixo de 3 dígitos); H1=5 real (título mais fundo que 6 linhas → varrer o vão inteiro); HUMAP 140/140 com cargo presente (2 em linha própria). Gate pré-IMPL da 4c: 105/105 títulos recuperados, divergência = bloqueador. Sem código, sem R-*. PROTOCOLO intacto. PAINEL não re-tirado. |
| v131 | 18/07/2026 | Sessão 003.DH (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4c-i IMPLEMENTADA e mergeada** — `recuperar_titulos_cargo` isolado em `motor/extracao_pgr.py`, materializando a decisão 003.DG-4 (título do cargo fora do span do card no EBSERH-UFGD, recuperado do texto de página cheia; vão do card 0 = texto pré-âncora). Saída paralela por ÍNDICE aos cards, `""` = ausência explícita nunca filtrada (anti-D-ARQ-22), invariante `len(titulos) == len(cards)` testada nos 3 reais. **Decisão 003.DH-1:** a âncora de recuperação é o **PAR** `NN.N` + `DADOS\s*GERAIS` adjacente (janela 3 linhas, `[INTERPRETADO]`), não o padrão numérico solto — este produzia falso-positivo medido no HUMAP (`4.3 RESUMO FINAL…`, título de seção); causa foi REGRESSÃO DE SPEC entre sessões (a medição H2 de 003.DG exigia o par; o gate da abertura da 003.DH largou a adjacência), não achado do documento. Custo do discriminador: ZERO no verdadeiro-positivo (UFGD 105/105), falso-positivo zerado (HUMAP 1→0). Gate pré-IMPL herdado ("105/105 recuperados") julgado FRACO na abertura e ENDURECIDO com 2 critérios (títulos distintos + numeração estritamente crescente): passou 105/105/105 no UFGD, literais `13.1 Advogado`…`13.106 Terapeuta Ocupacional`; gabarito medido dos outros witnesses HUMAP 140/**0** e Cjr 1/**0** (zero legítimo — cargo vive na linha de valores). Restrição gravada no código: número do título NÃO é índice de card (105 cards, numeração até `13.106`, lacuna). Suíte 841+4→**853+4** (+12); `mypy --strict motor/` zero erros, delta-zero; falha explícita via stash (`ImportError` na coleta). Revisão do Arquiteto sobre git objects aprovada sem correção. Nota 003.DH em DT-003CS-01 (4c-i fechada, DT ABERTA até 4d). Commit `5215dcf`, merge PR #229 (`b9c142d`). Nenhuma R-* criada/alterada. |
| v132 | 18/07/2026 | Sessão 003.DI (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4c-ii IMPLEMENTADA e mergeada** — módulo novo `motor/transcritor_card.py`: `TranscritorCard` (Protocol) + `transcrever_cards`, LLM mockado (molde 003.BN), `gate_forma_ghe` reusado sem alteração via import (003.DG-3); saída = reuso ESTRITO de `GHEVerbatim` (003.DG-1). **Decisão 003.DI-1:** contrato de 2 argumentos `transcrever(card, titulo)` (montagem-do-input é concern da 4c; tipo distinto impede reuso acidental do cliente-GHE; `""` = ausência explícita, espelho de `recuperar_titulos_cargo`); mismatch de comprimento = `ValueError`, não `Pendencia` (bug de construção, não condição de documento). 8 testes (5 núcleo + 3 reais sem skip: UFGD 105 pares com literais extremos, HUMAP 140/`""`, Cjr 1/`""`). Suíte 853+4→861+4 (+8); mypy delta-zero; falha explícita via stash. Nota 003.DI em DT-003CS-01 (4c-ii fechada, DT ABERTA até 4d). Commit `0c1e970`, merge PR #231 (`81f0962`). Nenhuma R-* criada/alterada. |
| v133 | 18/07/2026 | Sessão 003.DJ (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4c-iii IMPLEMENTADA e mergeada** — `TranscritorGeminiCard` em `adaptadores/transcritor_gemini_card.py` (molde 003.BO/CA; reuso da cascata + `_parsear_ghe`); `_PROMPT_CARD` dedicado (003.DG-2) calibrado em PASSO 0 com literais reais dos 2 witnesses; 7 testes mockados + 2 ao vivo; sonda ao vivo VERDE 2/2 na 1ª rodada (UFGD `("Advogado",)`, HUMAP `("ADVOGADO",)`); revisão do Arquiteto endureceu gabarito HUMAP pré-merge (amend `363a78b`→`d50769f`, classe gate-fraco 003.DH). Fatia 4c COMPLETA. Suíte 861+4→868+6; mypy delta-zero. Nota 003.DJ em DT-003CS-01 (DT ABERTA até 4d). Commit `d50769f`, merge PR #233 (`6c04a51`). Nenhuma R-* criada/alterada. |
| v134 | 19/07/2026 | Sessão 003.DK (IMPLEMENTAÇÃO): **D-ARQ-57 fatia 4d IMPLEMENTADA e mergeada — peça 4 COMPLETA; DT-003CS-01 FECHADA** (split de roteamento ghe/card + plug `preparar_ghes` + e2e EBSERH; UFGD ingere, HUMAP/Cjr gated by design). 2 bloqueadores corrigidos pré-código (fallback do 3º ramo; HUMAP gated — cauda de assinatura). **DT-003DK-01 ABERTA** (fronteira-fim do último span, 2 testemunhas). Suíte 868+6→877+6; mypy delta-zero. Commit `842ae5e`, merge PR #235 (`a249ea5`). Nenhuma R-* criada/alterada. PAINEL re-tirado (tiragem 003.DK). |
| v135 | 19/07/2026 | Sessão 003.DL (IMPLEMENTAÇÃO + ARQUITETURA): **EE lote 2 — Quadro 1/EE FECHA em 41/41**; família `R-BIO-04-*` 24→46 regras, 22 agentes novos, 17 exames novos. **D-ARQ-61 CRIADA** (critério de canônico para "ou" do Anexo I; valida retroativamente 6 escolhas anteriores; regra 3 corrigida na 2ª passada de "1º listado" para "escalar sem default"). **DT-003DL-01 ABERTA** (`is_carcinogeno_iarc`/`tem_lt` nunca populados com rigor; `null` explícito nos 22 para evitar vocabulário bimodal). 1 bloqueador legítimo levantado pelo Code (prompt omitia os 2 campos) e corrigido pelo Arquiteto. Suíte 877+6→899+6 (+22 exato); mypy `--strict` limpo, delta-zero. Commit `1477cf7`. Nenhuma R-* criada/alterada. PAINEL não re-tira. |
| v136 | 19/07/2026 | Sessão 003.DM (IMPLEMENTAÇÃO): **campo `termos:` populado — Tier 1, 20 aliases** derivados da grafia literal do Anexo I da NR-07 (Portaria 567/2022); nota de aplicação 003.DM em D-ARQ-50 Parte 2. Critério de admissão registrado: grafia normativa entra (`[DERIVADO]`), sigla comercial não; `TCE` proibido por ambiguidade tricloroetileno/1,1,1-tricloroetano (classe D-ARQ-22). 18 integrais + 2 recortes `[INTERPRETADO]`. **DT-003DM-01 ABERTA** (invariante do raio fuzzy da 003.BP quebrada — 4 pares dist ≤2 entre os 79 slugs; bloqueia Tier 2/siglas). Verificação prévia do Arquiteto: zero colisão, zero redundante, 1 par fuzzy novo (espelho de par já existente), regressão herdada 8/8. Guard 79→99 no mesmo commit. Motor intocado, zero deleção em `agentes.yaml`. Suíte 899+6→919+6 (+20 exato); mypy delta-zero. Commit `190e9aa`, merge `9527d9e`, PR #240. Nenhuma R-* criada/alterada. PROTOCOLO não move (v59). PAINEL não re-tira. |
| v137 | 19/07/2026 | Sessão 003.DN (IMPLEMENTAÇÃO): **piso bilateral no fuzzy — `PISO_FUZZY = 4` em `motor/resolvedor_termos.py`, FECHA DT-003DM-01.** Forma normalizada `len <= 4` resolve só por via exata (nem busca nem candidata participam do fuzzy) — `hdi`↔`tdi` sai da lista de colisão, `hdl` digitado deixa de resolver `hdi` por FUZZY. Nota de aplicação 003.DN em D-ARQ-50 Parte 2. Pares dist ≤2 entre chaves >4 (`etanol`/`metanol` etc.) permanecem — fora do escopo da correção, seguem no ramo seguro (empate→`NAO_RESOLVIDO`), agora sob teste de vigia fechado (`test_vigia_pares_fuzzy_chaves_longas`) contra regressão silenciosa. Ramo de empate sintético reparado no mesmo lote (chaves ≤4 do teste antigo caíam sob o piso e cegavam a cobertura). Tier 2 (siglas) segue não-populada — pré-requisito de motor cumprido, população é decisão de dado futura. Motor tocado, zero mudança em `agentes.yaml`. Suíte 919+6→923+6 (+4 exato); `mypy --strict` limpo, delta-zero — verificados nesta sessão META de fechamento (20/07/2026), retroativa ao merge PR #242 que faltou o commit de docs. Commits `c96e73f`+`6e956cd`, merge `d703aa3`. Nenhuma R-* criada/alterada. PROTOCOLO não move (v59). PAINEL não re-tira (DT-003DM-01 nunca esteve entre as 3 dívidas que travam produção). |
| v138 | 20/07/2026 | Sessão 003.DO (dispatch de IMPLEMENTAÇÃO → checagem de pré-condição): dispatch pediu a Tier 2 de siglas como "destravada" pelo fechamento de DT-003DM-01. Checagem contra o texto da própria DT e da nota 003.DM (v136: "grafia normativa entra, sigla comercial não; `TCE` proibido por ambiguidade") separou 2 gates: **motor** (piso fuzzy, FECHADO em 003.DN) e **dado** (fonte normativa + política de par ambíguo, nunca decidido). `TCE` confirmado ambíguo hoje de disco (`tricloroetileno` e `tricloroetano_111` ambos slugs vigentes em `agentes.yaml`). Pergunta feita ao Diovanni em vez de assumir; resposta: **não abrir Tier 2 agora** — 3ª confirmação independente da mesma linha (003.DM recusou, kickoff 003.DN recusou, 003.DO recusou). Nota 003.DO anexada a DT-003DM-01. Zero código, zero mudança em `agentes.yaml`, nenhuma R-* criada/alterada. `mypy --strict agente_medico/motor/` limpo nesta sessão; `pytest` completo (923 passed, 6 skipped) terminou em background após o encerramento pedido — delta-zero confirmado por medição contra a baseline 003.DN. PROTOCOLO não move (v59). PAINEL não re-tira. |
| v139 | 21/07/2026 | Sessão 003.DP (CONHECIMENTO/ARQUITETURA): **DT-003DL-01 REENQUADRADA — varredura refutada, zero mudança de dado.** Dispatch pedia popular `is_carcinogeno_iarc`/`tem_lt`; investigação mediu que os dois campos não têm consumidor (`git grep tem_lt`=vazio; `is_carcinogeno_iarc` do vocab inerte por teste `test_resolvedor.py:143`; legado usa JSON, não lê `agentes.yaml`) e que `tem_lt` codifica o eixo de R-BIO-02 `[DEPRECATED]`. Popular criaria dupla-fonte GHS×IARC (território DT-003CI-01) e trabalho sem leitor. Decisão: não popular, não normalizar `false`→`null`; enriquecimento deferido à chegada de consumidor (precedente DT-002H-01, append-only). Pesquisa normativa (Anexo 11 Quadro 1 parseado, Anexo 12 lido, mapa IARC) preservada em `docs/referencia/GABARITO_003DP_anexo11-12_iarc.md` como insumo pronto. Achado de processo: o gate de abertura (ler PROTOCOLO+DECISOES inteiros antes de arquitetar) foi pulado no início da sessão e recuperado no meio — custo medido: Anexo 12/manganês e a inércia dos campos já estavam nos docs. Nenhum `.py`/`.yaml`/teste tocado. PROTOCOLO não move (v59). PAINEL não re-tira. |
| v140 | 21/07/2026 | Sessão 003.DQ (META): linha de processo, não D-ARQ — selado o critério de numerador do PAINEL: superfície de dado SEM consumidor em runtime não conta como materializada (ratifica a decisão da tiragem 003.DE/DK sobre R-ECG-01/R-OP-01/R-VIS-01 em agentes.yaml.protocolos_especiais; mesmo princípio de DT-003DL-01/003.DP). Caminho de entrada no numerador: ganhar consumidor executável (mecanismo Pendencia/lembrete — cruza DT-002Y-01). Correções de processo: kickoff (SKILL.md item 5) passa a varrer DECISOES + PROTOCOLO com match invertido; gate de abertura declarável adotado no CLAUDE.md do ambiente Arquiteto. Docs: PROTOCOLO v60, PAINEL re-tirado 003.DQ. Sem código. |
| v141 | 22/07/2026 | Sessão 003.DR (IMPLEMENTAÇÃO/MEDIÇÃO): **D-ARQ-62 CRIADA** (redirecionamento de foco pós-003.DQ: Marco 1 via caso-âncora Fascino; recorte construção civil como sequenciamento com cláusula anti-hard-code; fila pautada por medição). Harness genérico `scripts/medicao_pgr.py` (commit `aa40050`, merge PR #245 `c71fb77`); 1ª medição real bloqueou em `topo_ausente` — causa medida: separador de cabeçalho GHE extrai como U+0000 (19 âncoras falham, classe glifo-de-fonte 003.DD). **DT-003DR-01 ABERTA** (faceta de DT-003L-01). Motor intocado; suíte 923 passed, 6 skipped; nenhuma R-* criada/alterada. PAINEL re-tirado (003.DR). |
| v142 | 22/07/2026 | Sessão 003.DS (IMPLEMENTAÇÃO): **DT-003DR-01 FECHADA** — `_reconhece_cabecalho_ghe_padrao` estende a classe de separador para `[-\x00]` (`extracao_pgr.py`), aceitando o glifo U+0000 dos 19 cabeçalhos GHE do Fascino (dominante `GHE 01 \x00 TÍTULO`, `GHE 16\x00 PINTURA` sem espaço, NUL embutido `GHE 10 … HIDRO\x00SANITÁRIAS`); precedente `[OÕ]` de 003.DD, sem novo D-ARQ. Medição determinística pós-fix (sem LLM): 19 âncoras, `recortar_topo` não-None (`topo_ausente` resolvido), 19 blocos, `avaliar_estrutura`=`('ghe', None)`, `avaliar_segmentacao`=`None` (gate de densidade não dispara → nada a reescopar). **DT-003DS-01 ABERTA** (20º cabeçalho `GHE\x00 TÉCNICO ADM / OPERACIONAL` sem número, pág. 89 — faceta de DT-003L-01, não-bloqueante). Ressalva: run ao vivo (LLM: `transcrever_topo`/`gate_forma_topo` + transcrições GHE/card) NÃO exercido — próximo instrumento; achados novos = medição nova, não reabertura desta DT. Suíte 923→**928 passed** (+5 casos parametrizados), 6 skipped; `mypy --strict extracao_pgr.py` limpo. Commit `536a4f4`, merge PR #247 (`66ace94`). Nenhuma R-* criada/alterada. PROTOCOLO não move (v60). PAINEL — correção A (carimbo da meia-aplicação de 003.DR + disposição das DTs; os 3 números não movem). |
| v143 | 22/07/2026 | Sessão 003.DT (IMPLEMENTAÇÃO/MEDIÇÃO): rodada Fascino `ida` ao vivo — 1º exercício dos estágios LLM (`transcrever_topo`+`gate_forma_topo`); pipeline de topo fim-a-fim OK, credencial RT transcrita e aprovada, artefato `relatorios/003dt_fascino_ida.json` (gitignored). Ressalva "run LLM não exercido" (003.DS) FECHADA p/ o topo. Achado → DT-003BV-01 (PROTOCOLO v61): `proposta=None` porque as 6 candidatas caem em mm/aaaa (design D2, agora medido real) + extenso-com-"de" (LACUNA `_MES_ANO`). `rodar` (GHE+card) ainda não exercido (falta volta-RT). Sem código de motor; suíte inalterada 928/6. PROTOCOLO v61. PAINEL não re-tira (números não movem; Marco 1 não fecha). |
| v144 | 23/07/2026 | Sessão 003.DU (IMPLEMENTAÇÃO): fix `_MES_ANO` — `(?:de\s+)?` torna o "de" opcional entre mês e ano (`resolvedor_topo.py`); "JUNHO DE 2026" e, por tolerância a prefixo, "15 DE JUNHO DE 2026" resolvem para o 1º dia do mês (**decisão: aceitar o drop do dia** — dia é edição-RT, coerente com o default conservador de DT-003BV-01). Fecha a faceta "de" medida em 003.DT; mm/aaaa permanece deferido (D2). Teste novo falha-sem/passa-com (`test_de_opcional_entre_mes_e_ano_resolve`). Suíte 928→929 passed, 6 skipped; `mypy --strict` sem erro novo. Commit `63edefe`, merge PR #250 `3470111`. Nenhuma R-* criada/alterada (R-PGR-06 semântica intacta — só o parser determinístico ganha cobertura). PROTOCOLO v62. PAINEL não re-tira (nenhum dos 3 números move; contagem de testes é carimbo de baseline, não um dos 3 números). |
| v145 | 24/07/2026 | Sessão 003.DW (CONHECIMENTO/dado): nota de aplicação 003.DW em D-ARQ-50 Parte 2 (mesma ID) — `silica.termos` populado (DT-003DV-01 faceta A); critério Tier 1 estendido a fonte-por-natureza-do-agente (NR-15 Anexo 12 / NR-07 Anexo III Quadro 1, não só Anexo I). Anti-FP dos não-sílica em teste. Índice 99→105, slugs 79 inalterado. Faceta B → 003.DX. Commit `8363fcb`, PR #253. Nenhum D-ARQ novo, nenhuma R-* criada/alterada. |
| v146 | 24/07/2026 | Sessão 003.DX (META): **D-ARQ-63 CRIADA** — gate de abertura em dois níveis: `docs/INDICE_DARQ.md` derivado (peça 1, PR #255, `scripts/gerar_indice_darq.py`, suíte 939→944) + nível 1 (PROTOCOLO + ÍNDICE + transversais D-ARQ-06/09/22) integral sempre, nível 2 (eixo nomeado) por sessão. Causa: DECISOES 64× em 68 dias (8.734→561.889 bytes), 49% diário (acreção pós-decisão + tabela de revisões). **DT-003DX-01 ABERTA** (PROTOCOLO v65) — migrar acreção para satélites `docs/darq/`. CLAUDE.md substitui o parágrafo do gate. Nenhuma R-* criada/alterada. |
| v147 | 25/07/2026 | Sessão 003.DY (IMPLEMENTAÇÃO): **D-ARQ-64 CRIADA** — ramo FUZZY opt-in por allowlist de dado (`fuzzy_permitido: true` em 18 slugs de cauda de `agentes.yaml`); `IndiceTermos` (frozen: `slug_por_forma` + `fuzzy_permitido`); veto de RESULTADO pós-eleição, nunca filtro de candidato (caso-âncora metanoll/metanol/etanol); recusa = `NAO_RESOLVIDO` + `fuzzy_recusado` nomeando termo/slug/distância. Medição: índice 105/79, 4 pares por empate, 94 zonas exclusivas = 77 carregadas + 17 cauda, 61/79 carregados, invariantes 77+17=94 e 61+18=79 (corrigem furo da tiragem original do Arquiteto: 60/76). **Fecha DT-003DV-01 faceta B e a DT inteira** (PROTOCOLO v66). Suíte 945→949, mypy --strict sem erro novo. Nenhuma R-* criada/alterada. |
| v148 | 25/07/2026 | Sessão 003.DZ (ARQUITETURA): **D-ARQ-65 CRIADA** — extração determinística por família de template; parser dedicado a família medida emite o MESMO verbatim tipado sob o MESMO gate de forma da rota LLM; LLM rebaixado a acelerador para família não-medida (pendência nomeia família nova); indisponibilidade de LLM só bloqueia família não-medida; procedência no verbatim (`deterministico:<familia>`\|`llm`\|`manual`) deferida à fatia de roteamento; manual é corretivo, não rotina. Origem: `429 RESOURCE_EXHAUSTED` (quota free-tier Gemini) bloqueou o `rodar` do Fascino 2× seguidas — dependência de terceiro no caminho crítico. Medição da família Consciente/Fascino: 20 âncoras, rótulos de cabeçalho 20/20, 237 linhas-de-risco ancoradas por token de categoria, bandas x estáveis (GRUPO@56, AGENTE@[113,177), FONTE@177+), zero quantificação numérica, zero FDS apontada. **NÃO revoga D-ARQ-41/49/50** — parser universal segue inexistente, o que muda é parser POR FAMÍLIA. Sem código nesta linha (fatia 1/parser isolado é o próximo commit da mesma sessão). Nenhuma R-* criada/alterada. |
| v149 | 25/07/2026 | Sessão 003.EA (IMPLEMENTAÇÃO): **D-ARQ-65 fatia 2 IMPLEMENTADA — roteamento determinístico-primeiro.** `FamiliaNaoReconhecida(ValueError)` nova em `parser_familia_consciente.py` (substitui os 2 `ValueError` genéricos de `_parsear_bloco`, mensagens inalteradas). `preparar_ghes` (rota "ghe") tenta `parsear_arquivo(caminho)` ANTES do cliente LLM (2ª leitura do PDF, mesma classe do seam humano D-ARQ-52); aceita só se nenhum `FamiliaNaoReconhecida` E `len(candidatos) == len(blocos)` (divergência de contagem = família não reconhecida, conservador); aceita → `gate_forma_ghe` direto, cliente LLM nunca invocado; recusada → `Pendencia` não-bloqueante `familia_nao_medida` (`regra_origem="D-ARQ-65"`) anexada, fallback LLM segue inalterado. Rota "card" intocada; procedência no verbatim segue deferida (fatia 3). Testemunhas reais: Fascino 19/19 aprovados sem invocação LLM; Viverde (família não medida) aciona fallback via `FamiliaNaoReconhecida`, testemunha negativa. Nota de aplicação 003.EA em D-ARQ-65. Suíte 957+6→963+6 (+6 exato); `mypy --strict` delta-zero (46 erros pré-existentes em 5 arquivos FDS-side, nenhum nos arquivos tocados). Nenhuma R-* criada/alterada. PROTOCOLO não move. PAINEL não re-tirado nesta sessão (fechamento é sessão própria). |
| v150 | 25/07/2026 | Sessão 003.EB (MEDIÇÃO): nota de aplicação 003.EB em D-ARQ-62 — subcomando `rodar-offline` em `scripts/medicao_pgr.py` dispensa `CHAVE_API_GOOGLE`; clientes-bomba levantam `TranscricaoIndisponivel` se invocados, recusa nomeada vira pendência bloqueante, nunca mock (coerente com D-ARQ-65). Rodada Fascino offline: 19/19 GHEs, zero `familia_nao_medida`, zero `transcricao_indisponivel_pgr`. Diff contra a matriz humana (Marco 1) instrumentado: DT-003EB-01 (pacote-base incondicional sem conceito no motor, ~190/~194 células) e DT-003EB-02 (R-BIO-04 emite indicador biológico onde a matriz humana pede menção documental em risco baixo) — ambas em PROTOCOLO v67 §11. Suíte 963 passed, 6 skipped (inalterada); `mypy --strict` delta-zero. Nenhuma R-* criada/alterada. Nenhum D-ARQ novo. |
| v151 | 26/07/2026 | Sessão 003.EC (IMPLEMENTAÇÃO): **D-ARQ-66 CRIADA** — emissão incondicional é regra de primeira classe (primitivo `todo_trabalhador`, `PRIMITIVOS_INCONDICIONAIS`); tri-estado de D-ARQ-31 passa a computar sobre `linhas_com_risco`, excluindo linhas cujo `Motivo.predicado` seja todo incondicional (`MatrizGHE.linhas` segue carregando a linha incondicional — muda só o gate do status). **R-CLI-01 materializada** (exame clínico 12M, `[adm, per, MR, RT, dem]`, `exame_clinico` novo em `exames.yaml`) — fecha a maior fatia de DT-003EB-01. **DT-003EB-01 REENQUADRADA** (não fechada): premissa "pacote-base incondicional ~190/~194 células" refutada por medição do gabarito Fascino (4 exames em 19/19, não ~190; GHE-06 Administração recebe 4, GHE-19 Vendas recebe 5); gap decomposto em 4 classes, só classe (4) — conceito genuinamente ausente — exige CONHECIMENTO; resíduo ABERTO = `Av. Médica de Saúde Mental` (inexistente em regra) + Avaliação Psicossocial incondicional vs R-PSY-01 [VALIDADO] condicionada, gatilho de formalização = 2º PGR no acervo (D-ARQ-06), não n=1. **DT-003EC-01 CRIADA (ABERTA)**: gabarito Fascino emite RX Tórax OIT 12M em GHEs sem quantificação onde R-RX-01 sem-medição prescreve 24M — pergunta de método (D-ARQ-27), não-bloqueante; resolve de passagem o pré-registro de DT-003DV-01/003.DW ('Poeira respirável' tratada como sílica-like, não PNOS, no gabarito). 4 testes falha-sem/passa-com em `test_orquestrador.py`, verificados empiricamente red/green (regra marcada `DEPRECATED` → 4 falham; restaurada → 4 passam). Helper `linhas_de_risco` consolidado em `agente_medico/tests/invariantes.py` (precedente de auditor compartilhado), substitui 2 cópias locais duplicadas + evita uma 3ª. Lição de processo: escopo de quebra esperada por lista-de-arquivos-à-mão falhou 2× (7→48 falhas reais); critério correto é semântico ("teste carrega o protocolo real e assere contagem exata/lista vazia de emissões"), não enumeração. Suíte 963→967 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` (alvo correto do projeto) delta-zero. Commit `f175e76`. PROTOCOLO v68. PAINEL não re-tirado nesta sessão. |
| v152 | 26/07/2026 | Sessão 003.ED (IMPLEMENTAÇÃO): **D-ARQ-67 CRIADA** — literal de vocabulário em código é contrato verificado por teste computado do dado (literais extraídos via AST de `predicados.py` cruzados contra slugs reais de `agentes.yaml`; um conceito → um slug → um primitivo). Origem: primitivo `maquina_pesada` comparava slug inexistente — código inalcançável em produção, verde na suíte (testes sintéticos do primitivo casavam o literal consigo mesmo; o `ou` de `atividade_critica` mascarava a perna morta). Alias Tier 1 `"Trabalho em Altura"` (NR-35 título + item 35.2.1, Portaria MTP 4.218/2022, texto vigente `nr-35-atualizada-2025-1.pdf`) resolve o termo que antes ficava a distância 3 do slug (fora do raio fuzzy); `atividade_critica.ou` passa a referenciar `motorista_equipamento_pesado` no lugar do primitivo órfão. Medição Fascino (`rodar-offline`, D-ARQ-65): 16/19 GHEs passam a emitir R-PKG-ATIVCRIT, cruzamento NOMINAL contra o gabarito humano com interseção 16 e conjuntos "só motor"/"só gabarito" vazios; medição isolada das 3 pernas de `atividade_critica` por GHE (sem short-circuit) fecha 16 = 16 (trabalho_altura) + 0 (motorista_equipamento_pesado) + 0 (espaço_confinado) − 0 (sobreposição). **DT-003ED-01 CRIADA (ABERTA)**: grafia natural com preposição não resolve contra slug sem preposição (dist. 3, fora do raio fuzzy 2) — atinge R-VIB-01/02 pela via de vibração e a perna de máquina pesada de R-PKG-ATIVCRIT/R-ECG-01. **DH-003ED-01 CRIADA (ABERTA)**: relatório do harness não carrega slugs resolvidos nem o átomo do predicado composto que disparou uma linha — só a regra final. **DT-003DV-01 refutada por medição**: o relatório TEM identidade por GHE (cada seção `### GHE` carrega tabela própria); observação de instrumento anterior estava errada. Suíte 967→968 passed, 6 skipped (+2 novos: alias no parametrize + teste computado anti-órfão; −1 removido: teste sintético do primitivo morto); `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero; índice de termos 105→106. Commit `7b2e65d`. PROTOCOLO v70. PAINEL não re-tirado nesta sessão (re-tiragem é pós-merge). |
| v153 | 26/07/2026 | Sessão 003.EE (IMPLEMENTAÇÃO): **D-ARQ-39 IMPLEMENTADA** — o caminho de convergência do `stage_8_consolidacao` troca `igualdade-estrita-ou-raise` por piso component-wise (`min` em `periodicidade_meses`; `min` com `None`=+∞ em `periodicidade_apos_15a`, resultado `None` só quando ambos os lados são `None`). As três mutações incondicionais (`momentos |=`, `motivos.extend`, `pendencias_anexadas.extend`) intactas no lugar, cláusula 2. Toca só `consolidacao.py` no motor. **Duas correções de procedência medidas** (nota de aplicação 003.EE em D-ARQ-39): (i) cláusula 1 imprecisa — `periodicidade_meses` é `int` não-Optional (`tipos.py:270`), `None` irrepresentável, tratamento de `None` só cabe em `apos_15a`; redação, mesma ID; (ii) **nota de implementação obrigatória REFUTADA** — a fixture `pgr_viverde.py` tem `fumos_metalicos` em zero GHEs e as 4 ocorrências de `silica` todas com `quantificacao`, então `silica_asbesto_sem_medicao` nunca dispara: regressão tri-estado **inalterada**, lista de GHEs afetados **vazia**, âncora era iminente e não viva. D-ARQ-39 entra **latente**. **DT-003EE-01 CRIADA (ABERTA, não-bloqueante)**: zero `raise ConflitoProtocolo` no repo após a IMPL — classe e `except` do orquestrador inalcançáveis; decisão é MANTER (contrato D-ARQ-15), não remover. Testes: 5 de piso novos em `test_consolidacao.py` (base, `apos_15a` com `None`=+∞, ambos `None`, preservação de `pendencias_anexadas`, preservação de `motivos`), −1 removido (o de conflito); `test_rx_periodicidade.py` e `test_orquestrador.py` reescritos 1-para-1 de raise para piso. Suíte 968→**972 passed, 6 skipped** (+4 líquido, previsto = medido); `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Commit `52aa6f3`. PROTOCOLO v71. PAINEL **não re-tirado** — nenhum dos 3 números se move. |
| v154 | 26/07/2026 | Sessão 003.EE (emenda de evidência, docs only): a refutação da nota de implementação de D-ARQ-39 foi medida em **três vias**, não uma — a redação de v153 provava só a via explícita (`RiscoPGR` na fixture) e calava sobre a via por cargo e a via por operação. **(b) Por cargo:** único injetor de `fumos_metalicos` é `soldador`, ausente da fixture; `Est-09 "Solda / serralheria"` usa `serralheiro`/`meio_oficial_serralheiro`/`servente` com `riscos_implicitos: []`, que **é R-GHE-05 `[VALIDADO]` cumprida, não lacuna**; 39 cargos, zero órfãos. **(c) Por operação:** inexistente — `GHEPGR` não modela operações, **D-ARQ-23 PROPOSTA**. Conclusão **inalterada** (lista de GHEs afetados vazia, D-ARQ-39 latente) — só a evidência era insuficiente. **Causa estrutural:** as três vias fechadas simultaneamente tornam o caso-âncora **inalcançável por construção** até D-ARQ-23 ser implementada; já documentado na nota 002.M de R-GHE-05, a emenda só passa a citá-lo. **Origem provável do erro de procedência `[INTERPRETADO]`:** o cromo do serralheiro está na RQ.61 (matriz de SAÍDA), não no PGR de entrada — confusão de camada. **`[A MEDIR]` do artefato FECHADO:** nenhum arquivo versionado com "diagnost". Correção de rota registrada: a v153 atribuiu a causa a DT-002K-02 supondo-a aberta; DT-002K-02 está **RESOLVIDA** desde 002.L-estudo e a referência correta é D-ARQ-23 — erro pego pelo bloqueio do Code antes de qualquer escrita. PROTOCOLO **não move** nesta emenda. Sem mudança de código, suíte não re-executada (árvore de docs). |
| v155 | 27/07/2026 | Sessão 003.EG (IMPLEMENTAÇÃO): nota de aplicação em D-ARQ-22 Parte B — `MatrizGHE.riscos_resolvidos`/`predicados_avaliados` (aditivos, default, ordem estável) e `Motivo.predicado` serializando a expressão real (fim do literal `"<composto>"`) materializam a rastreabilidade por linha na saída do motor; recorte descartado registrado (rastro dentro de `predicados.avaliar` mudaria assinatura usada em todo o motor); nenhum D-ARQ novo. **Correção de procedência em D-ARQ-39** (mesma ID, status inalterado): a rota de convergência do dedup passou a ter tráfego na rodada Fascino (duas linhas de `audiometria` unificando motivos, `[R-PKG-ATIVCRIT, R-VIB-02]` e `[R-PKG-ATIVCRIT, R-AUD-01]`), mas o disparador foi o alias de altura de 003.ED (D-ARQ-67), não D-ARQ-23 como a nota de 003.EE atribuía; status permanece LATENTE — as duas convergências medidas são ambas 12M, o piso `min` segue sem exercício. DH-003ED-01 PARCIALMENTE RESOLVIDA (PROTOCOLO §11) — facetas `riscos_resolvidos`/`predicado` FECHADAS, faceta `risco_origem` ABERTA. DT-003EG-01 (audiometria pelo motivo errado quando a perna do ruído bloqueia), DH-003EG-01 (bytes NUL do PGR vazam para o relatório) e DH-003EG-02 (instrumento de diff fora do git) CRIADAS (§11 do PROTOCOLO). Medição Fascino (`5a2d15b`): 19 GHEs → 2 VÁLIDA / 15 PARCIAL / 2 BLOQUEADA, 104 linhas de exame. Suíte 977→982 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Commits `94a5720`, `76f1afa`, `5a2d15b`. PROTOCOLO v72→v73. Detalhe em HISTORICO 003.EG. |
| v156 | 27/07/2026 | Sessão 003.EG (EMENDA — correção de método): **DT-003DX-02 PARCIALMENTE RESOLVIDA** — regra de método do público Code passa a existir versionada em `CLAUDE.md` na raiz do repo (auditável, autocarregada pelo Claude Code); `CLAUDE.md` do Cowork reduzido a ponteiro quanto a essas regras. Resíduo ABERTO: nenhum mecanismo detecta divergência entre os dois arquivos. Disparador: DH-003EG-03 (PROTOCOLO v74, §11) — `INDICE_DARQ` ficou defasado 94 linhas no commit `186150e` desta mesma sessão porque o prompt de fechamento dispensou a suíte por "docs-only", 2ª ocorrência da classe em 2 sessões (1ª: `c89f569`, 003.EF); corrigido em `973a343`. Correção instalada: cláusula fixa em `CLAUDE.md` + `docs/RITUAL_FECHAMENTO.md` (NOVO, checklist de 7 passos). Causa nomeada no Arquiteto, não no Code. Esta emenda toca `DECISOES_ARQUITETURAIS.md` — a regra que ela institui foi aplicada a ela mesma: `INDICE_DARQ.md` regenerado, `test_indice_em_disco_nao_divergiu` verde. Suíte inalterada (nenhum código tocado); `agente_medico/tests/ tests/` = 982 passed, 6 skipped (medido, árvore parada). Nenhuma R-* criada/alterada. PROTOCOLO v73→v74. Detalhe em HISTORICO 003.EG. |
| v157 | 28/07/2026 | Sessão 003.EH (FECHAMENTO — docs): **D-ARQ-68 CRIADA** — silêncio documental mapeia para o ramo normativo de ausência quando a norma o define, condicionada (D-ARQ-13 prevalece sem esse ramo); caso-âncora R-RX-01 (Quadro 1, commit `7dd68e6`); contra-exemplo medido: ruído (`R-AUD-01`/`R-AUD-02`) não destrava, pela ausência de ramo normativo de faixa-default. Detalhe em HISTORICO 003.EH. |
| v158 | 28-29/07/2026 | Sessão 003.EI (FECHAMENTO — docs): **D-ARQ-69 CRIADA** — regra clínica escrita antes da sessão não é materializada sem conferir o texto vigente da norma que ela mesma cita (3 cláusulas: obrigatoriedade da conferência declarada com fonte/data; divergência resolve por D-ARQ-22 Parte A + nova ID/DEPRECATED; `[VALIDADO]` não dispensa a conferência); caso-âncora R-ESP-01 → R-ESP-02 (003.EI), três reformulações de escopo antes de conferir o Anexo III que a própria regra citava; contra-exemplo registrado R-CLI-01 (003.EC, bateu com a norma sem conferência prévia — acerto por sorte, não por método). Detalhe em HISTORICO 003.EI. |
| v159 | 30/07/2026 | Sessão 003.EJ (IMPLEMENTAÇÃO + MEDIÇÃO): **D-ARQ-70 CRIADA** — aliases Tier 1-C de vibração (VMB/VCI + grafias de corpus mão-braço) em `agentes.yaml`, índice termo→slug 106→112 (medido, zero colisão, 4 pares fuzzy inalterados); `_formatar_pendencia` (`scripts/medicao_pgr.py`) passa a imprimir `ghe_id`. Medição Fascino confirma 6 das 8 previsões do Arquiteto; 2 divergem e viram DT-003EJ-02 (GHE-16 PARCIAL→VÁLIDA: pendência `predicado_ausente` de R-AUD-02 some porque a perna e(ruido,ototoxico,vibracao_qualquer) deixa de ser Ausente quando vibracao_qualquer resolve True — único dos 9 GHEs com VMB que também é ototóxico). DT-003EJ-01 aberta (poeira de madeira, GHE-08). Suíte e mypy do fechamento: [A MEDIR]. |
| v160 | 31/07/2026 | Sessão 003.EK (FECHAMENTO): **D-ARQ-71 CRIADA** — perna `Ausente` absorvida por `ou` verdadeiro (curto-circuito de `avaliar`) gera pendência não-bloqueante `perna_ausente_absorvida` anexada à linha via passada de diagnóstico separada que atravessa predicado composto nomeado (`pernas_ausentes_absorvidas`); tri-estado não se move (`tem_anexada` conta só bloqueante). Resolve DT-003EJ-02 e faceta (b) de DH-003EJ-01. Medição Fascino: 2 pendências, ambas GHE-16, ancoradas em `audiometria`; status 3 VÁLIDA / 15 PARCIAL / 1 BLOQUEADA inalterado. Suíte 1001→1013→1019 passed, 6 skipped; `mypy --strict` delta-zero, 34 arquivos. Commits `4f5c91f`, `cd39cb8`, `823d467`, `1894602`; merge `54637e4` (PR #275). |
| v161 | 31/07/2026 | Sessão 003.EM (FECHAMENTO): **D-ARQ-72 CRIADA** — apresentação-de-saída da matriz (`renderizar_matriz`, `agente_medico/superficie/apresentacao_matriz.py`) é superfície própria, apresentação-pura herdando D-ARQ-54 P1 (lógica-de-domínio zero); extraída byte-idêntica de `scripts/medicao_pgr.py` (7 testes existentes inalterados); `Motivo.status_regra` populado de `regra.get("status")` fecha D-ARQ-22 Parte B no eixo que DH-003EI-01 faceta 2 registrava descumprido; ordem de leitura `INTERPRETADO`→`DERIVADO` materializa o bloco "inspecionar primeiro". Fecha faceta 2 de DH-003EI-01 (§11 PROTOCOLO); abre DH-003EM-01 (literal `_STATUS_INSPECIONAR_PRIMEIRO` sem teste computado, classe D-ARQ-67) e DH-003EM-02 (bloco nunca exercitado no nível `INTERPRETADO` no Fascino). Nenhuma R-* criada ou alterada. Detalhe em HISTORICO 003.EM. |
| v162 | 01/08/2026 | Sessão 003.EO + EMENDA 1 (FECHAMENTO): **D-ARQ-73 CRIADA** — emissor de saída no formato do escritório (`agente_medico/superficie/documento_matriz.py`): `DocumentoMatriz` única + `renderizar_html`/`renderizar_docx`; expansão GHE→cargo ancorada em R-GHE-01/D-ARQ-21; ordem de exibição dos exames cravada como `ordem_exibicao` opcional em `exames.yaml` (decisão do Arquiteto na EMENDA 1, após medição achar ordem não-constante entre GHEs — bloqueador nomeado da fatia 0); cabeçalho/rodapé seam humano (DT-003EO-01); sanitização de controle (NUL) só na renderização (DH-003EG-01). `MatrizGHE` ganha `nome_ghe`/`cargos` aditivos (fatia 1). Medição fatia 4 contra Fascino real: tabela da EMENDA 1 confirmada exatamente (12/19 GHEs idênticos, 4 células de superemissão, 10 de subemissão); achados novos confirmados (RX 12M×24M em 14 GHEs, clínico 6M×12M em GHE-09/17 → DT-003EO-03); achado fora do previsto: `GHEPGR.cargos` chega como 1 string por GHE (D-ARQ-65 fatia 1, já documentado no parser) → DT-003EO-04. Grafia Glicemia/RX ficou indecisa (D-ARQ-06) → DT-003EO-02, yaml intocado. `docs/PLANO_V1.md` migrado da pasta do Cowork (pendência de versionamento do próprio arquivo). Nenhuma R-* criada, alterada ou depreciada. Detalhe em HISTORICO 003.EO. |
| v163 | 03/08/2026 | Sessão 003.EP fatias 0-4 (MEDIÇÃO + IMPLEMENTAÇÃO + FECHAMENTO): **D-ARQ-65 Cláusula 5 NOVA** — o bloco da família medida é um formulário de rótulos em 2 colunas fixas (rótulo esquerda/valor direita), não só a tabela de riscos já calibrada por bloco; `x0` idênticos bit-a-bit nos 19/19 blocos do Fascino (`58.499347642527084`/`279.2172167102426`), continuações do valor com desvio 0,0pt exato; critério de fim de célula é transição de banda, nunca o literal do próximo rótulo. Nota de aplicação: `_extrair_cargos_da_linha` passa a capturar overflow por banda (fatia 1) e separar nome/CBO por entrada (fatia 2, CBO descartado — precedente 003.DG-1, candidato de consumo futuro DT-003ED-01 faceta máquina pesada); correção de premissa da EMENDA 4 de 003.EO preservada (D-ARQ-06): delimitador e CBO-colado-ao-nome não eram dois problemas, é 1 código CBO-2002 partido pelo mesmo glifo-hífen (`\x00`≡`-`) já catalogado em `_PADRAO_TITULO_ANCORA`. Não abriu D-ARQ nova — extensão de recorte medido, molde D-ARQ-57 peça 1. Fecha **DT-003EO-04** (PROTOCOLO §11) nas duas facetas, evidência: gate nominal 0 divergências (41 nomes) + e2e real (41 `LinhaCargo`). Abre **DT-003EP-01** (R-GHE-02 inalcançável — `cargos_vocab.get(cargo)` sem resolver, 19→41 pendências medido), **DT-003EP-02** (dois caminhos de silêncio remanescentes no parser, não exercitados no Fascino) e **DH-003EP-01** (`_sanitizar` apaga glifo-hífen no documento assinado). Nota aditiva em DH-003EG-01 (bytes NUL do relatório 122→18, resíduo de outra origem). Não-regressão medida: linhas de exame 171→171, status por GHE idêntico nos 19/19. Suíte 1039→1048 passed, 6 skipped; `mypy --strict` 42 arquivos, limpo. Commits `aaa9eca`/`486d54d`/`7f19cf4`. Nenhuma R-* criada, alterada ou depreciada. Detalhe em HISTORICO 003.EP. |
| v164 | 04/08/2026 | Sessão 003.EQ: D-ARQ-74 nova |
| v165 | 05/08/2026 | Sessão 003.ER (ARQUITETURA): **D-ARQ-75 CRIADA** — fecha o §S0 do `PLANO_V1` (hospedagem + autenticação). Provedor por consumo, não por tier (Railway Hobby; RAM $10/GB/mês, teto 48 GB/serviço, `[DERIVADO — docs.railway.com/pricing/plans]`) porque o pico medido do e2e determinístico do Fascino é **904 MB / 128,5s**, contra ~450-500 MB extrapolados no registro anterior — 2 GB deixa de ser piso e vira teto de um usuário. Autenticação `st.login()` com client OIDC do projeto + **allowlist própria obrigatória** (OIDC autentica, não autoriza — `[DERIVADO — docs.streamlit.io/.../authentication]`), gate antes do `file_uploader`, segredo fora do git. Cookie de identidade de 30 dias não-configurável = risco aceito e nomeado. `requirements-app.txt` enxuto: 5 terceiros medidos (streamlit, pdfplumber, PyYAML, python-docx, requests) contra os 14 do `requirements.txt` do legado; pin do Streamlit precisa de piso que garanta `st.login`. Leitura única do PDF (2ª passada de `extrair_texto_pgr`, ~metade do tempo) adiada para fatia própria medida. Correção de método registrada: a 1ª varredura de dependências usou `grep "^import"`, cego a import indentado (classe DH-003EC-01(a)). Riscos inocentados por medição: cache em `session_state` = 72 KB; PDF do cliente não persiste em disco (`TemporaryDirectory`). Nenhuma R-* criada ou alterada; motor, protocolo e vocabulário intocados. Implementação é 003.ES. Detalhe em HISTORICO 003.ER. |
| v166 | 08/08/2026 | Sessão 003.ES fatias 1-2 (IMPLEMENTAÇÃO): **D-ARQ-76 CRIADA** — o gate de acesso mora no entrypoint (`app_matriz.py`), não em `pagina_matriz()`, **superando em parte D-ARQ-75 cláusula 2(b)**; a decisão de acesso é núcleo puro com três desfechos (`GateAcesso` PEDIR_LOGIN/NEGAR/LIBERAR em `superficie/autorizacao.py`, sem importar streamlit nem ler `os.environ`); a fronteira normaliza estritamente (`is True`+`isinstance`), fail-closed por construção; allowlist por env var `PCMSO_ALLOWLIST`, não por `st.secrets`. Razões medidas: `at.secrets["auth"]` não faz `st.user.is_logged_in` existir no `AppTest` (`AttributeError` idêntico com e sem injeção — o bloco `[auth]` é consumido na subida do servidor), e `UserInfoProxy` tipa `getattr`/`.get()` como `str | bool | TokensProxy | None`, nunca `bool`/`str | None`. `cast` e `# type: ignore` rejeitados por mentirem ao verificador na fronteira de segurança. Nota de aplicação em **D-ARQ-75**: os três `[A CONFIRMAR]` fechados — `st.login` nasce no 1.42.0; env var resolvido pelo lado negativo (a doc documenta `secrets.toml`→env, nunca o contrário); Railway Serverless existe e dorme por ausência de *outbound*. Fatia 1: `requirements-app.txt` (5 terceiros por AST) + entrypoint na raiz (lacuna não prevista por D-ARQ-75). Suíte 1062→**1074 passed, 6 skipped**; `mypy --strict` limpo, **45 arquivos** (comando canônico passa a incluir `app_matriz.py`). Nenhuma R-* criada, alterada ou depreciada. Fatia 3 (deploy) adiada para 003.ET. Detalhe em HISTORICO 003.ES. |
| v167 | 10/08/2026 | Sessão 003.ET fatias 1-2 + fechamento (08-10/08/2026): **D-ARQ-77 CRIADA** — mecanismo de build é o Dockerfile, não a detecção do builder (Railway trocou Nixpacks→Railpack entre D-ARQ-75 e a implementação); segredo materializado por shell no entrypoint antes do `streamlit run`, núcleo puro `gerar_toml_auth` + casca em `materializar_secrets.py`; `requirements.txt` do legado permanece, agora inofensivo. Nota de aplicação em **D-ARQ-75** (mesma ID): a premissa dos 904 MB (cláusula 1) refutada por medição — pico é cache de página do pdfplumber nunca liberado, não propriedade do documento; `Page.close()` por página derruba o e2e do Fascino de 859→103 MB (sandbox) e 674,3→114,8 MB (host Windows), saída idêntica; `flush_cache()` sozinho só chega a 398 MB, `close()` sozinho a 88 MB. Destino do deploy **reaberto** — a base de "provedor pago por consumo" caiu, hospedagem gratuita volta à mesa, decisão em sessão própria (`docs/PLANO_V1.md` §S0). Erro de método registrado (D-ARQ-06): 003.ER mediu sintoma e concluiu sobre provedor sem perguntar a causa; o Arquiteto repetiu a conclusão no gate de abertura de 003.ET sem questionar, até a pergunta do Diovanni sobre custo forçar a investigação. **DH-003ET-01 ABERTA** (`docs/PENDENCIAS_CLINICAS.md`) — fixtures de PDF (Fascino, Cjr Engenharia) não versionadas, testes que dependem delas skipam em silêncio em clone limpo. Nenhuma R-* criada, alterada ou depreciada. PROTOCOLO v88 (registra a partição do §11 da fatia 0). Suíte 1085 passed, 6 skipped (inalterada — sessão docs-only); `mypy --strict` não roda (nenhum `.py` tocado nesta fatia). Commits/PRs das fatias: #287 (fatia 0, partição §11), #288 (fatia 1, deploy), #289 (fatia 2, memória). Detalhe em HISTORICO 003.ET. |
| v168 | 10/08/2026 | Sessão 003.EU (ARQUITETURA + IMPLEMENTAÇÃO): **D-ARQ-78 CRIADA** — destino do deploy é o Streamlit Community Cloud, por requisito de custo zero **literal** confirmado com o Diovanni (nunca perguntado em 003.ER). Railway sai por assinatura fixa; Cloud Run sai do topo por medição — WebSocket aberto força *instance-based billing* (free tier 240k vCPU-s/mês = 66,7 h a 1 vCPU; aba aberta 8h/dia × 22 dias ≈ $7,45/mês `[APROXIMADO]`) — e **fica como fallback**, que é o que preserva o valor do `Dockerfile` de D-ARQ-77. O nome do arquivo de dependências vira contrato da plataforma (5 nomes reconhecidos, `requirements-app.txt` invisível): **renomear, nunca duplicar** — o app assume `requirements.txt`, legado vira `requirements-legado.txt`; efeito não previsto é que isso **remove a causa-raiz** de D-ARQ-77 cl.1. O gate próprio **permanece** por razão medida: a allowlist nativa de viewers é **transitiva** (*"They can also pass these permissions to others by inviting more viewers"*), e `PCMSO_ALLOWLIST` sobrevive sem tocar código (segredo de nível raiz vira env var, exemplo literal na doc). Ordem de configuração rígida (subdomínio → OAuth client → TOML → deploy), porque sem `[auth]` o entrypoint estourava `AttributeError` e o Community Cloud força `showErrorDetails=false`. **D-ARQ-75 cláusula 1 revogada**; **D-ARQ-77 cláusula 4 superada**. `[A CONFIRMAR]`: limite de RAM (não localizado em 5 páginas oficiais) e se o subdomínio é escolhível antes do 1º boot. Dois erros de método do Arquiteto registrados: ausência de evidência tratada como evidência de ausência ("1 app privado" existe, em página irmã), e `mypy = 45` cravado como gabarito bloqueante quando o real era 47 (003.ET criou 2 módulos e não re-mediu) — o Code parou e reportou, no procedimento previsto. **DH-003EU-01** e **DH-003EU-02** ABERTAS. Nenhuma R-* criada, alterada ou depreciada; PROTOCOLO intocado. Suíte 1085→1086 passed, 6 skipped; `mypy --strict` limpo, 47 arquivos. Detalhe em HISTORICO 003.EU. |
| v169 | 11/08/2026 | Sessão 003.EV fatia 1 (IMPLEMENTAÇÃO): **D-ARQ-79 CRIADA** — entrypoint de desenvolvimento sem gate (`app_matriz_local.py`, chama `pagina_matriz()` direto) é porta deliberada para rodar a matriz na máquina do operador sem exigir OAuth do Google; a separação é travada por teste (`test_entrypoint_de_producao_nao_usa_o_entrypoint_local`), não por disciplina — sem ele, a porta sem autenticação chegaria à internet por um descuido de uma linha; identidade visual (`st.set_page_config`, título "Matriz de Exames — PCMSO") mora nos entrypoints, não na página, porque o gate chama `st.title` antes de `pagina_matriz()`. D-ARQ-76 e D-ARQ-77 intactas. Fechamento em docs desta sessão ficou em atraso duas sessões (falha de método do Arquiteto, registrada em HISTORICO 003.EW). Suíte 1086→1088 passed, 6 skipped; `mypy --strict` limpo, 48 arquivos (`app_matriz_local.py` entra no alvo canônico). PR #293, merge `75255e8`. Detalhe em HISTORICO 003.EV. |
| v170 | 11-12/08/2026 | Sessão 003.EW fatias 1-2 (IMPLEMENTAÇÃO): **D-ARQ-80 CRIADA** — no nível gratuito o gargalo é requisição (RPD 20), não token (TPM 250k): a unidade de invocação do transcritor passa a ser o lote, não o bloco (`TranscritorGHEEmLote`, `_BLOCOS_POR_LOTE = 6` — três requisições por documento de 18 blocos em vez de dezoito); alinhamento bloco↔GHE é contrato duro com dupla guarda (`GHEVerbatim` vazio no faltante + `ValueError` de comprimento); cascata de modelos com aliases `-latest` à frente (três dos quatro modelos cravados haviam morrido: HTTP 429, HTTP 404, dois inexistentes) e motivo por modelo na exceção. Fatia 1 (PR #294, `66f3ecf`) ligou a rota LLM à superfície, inerte desde D-ARQ-65 por o cliente-bomba nunca ser trocado; fatia 2 (PR #295, `0136426`) entregou o lote no motor e no cliente Gemini, e uma emenda subsequente corrigiu o mesmo padrão de defeito pela segunda vez na sessão — `_TranscritorContado` (fatia 1) interceptava o *duck-typing* de `transcrever_ghes` por não expor `transcrever_lote`, deixando o lote inerte em produção mesmo pronto no cliente. Travessia real do TOCTAO (emissor nunca medido pela rota determinística): 18 GHEs, 61 cargos, zero pendência, 3 requisições confirmadas no painel `[MEDIDO — 13/08/2026]`. Achado clínico de convergência tripla (Acetona + MEK na urina, GHE-11 Hidráulica) entre a anotação manual da Dra. Carolini, a recusa fuzzy do Fascino e a transcrição do TOCTAO — abre DT-003EW-01/02/03. Suíte 1092→1097→1099 passed, 6 skipped (fatia 2 rendeu +5 líquido, não os +6 previstos — item de motivos acumulados reescreveu teste pré-existente; emenda do wrapper +2); `mypy --strict` limpo, 48 arquivos. Detalhe em HISTORICO 003.EW. |
| v171 | 16/08/2026 | Sessão 003.EZ fatia 1 (ARQUITETURA): **D-ARQ-68 cláusula 5 NOVA** — delegação normativa a documento que a norma não obriga a responder (NR-09 9.4.1/9.4.2, avaliação quantitativa condicional): presunção protetiva declarada por primitivo nomeado em `regras.yaml`, nunca inferida em código, com quatro exigências cumulativas (direção protetiva; declaração no dado; pendência não-bloqueante `[INTERPRETADO — prioridade na revisão de saída]`; piso `PARCIAL`, nunca `VÁLIDA`). Nota ao contra-exemplo do ruído na cl.2: a leitura de 003.EH estava correta para o texto que tinha (NR-15 Anexo 1/NHO-01 sem faixa default) e incompleta quanto à NR-09 9.4.2 — o PGR silencioso pode estar em conformidade. **D-ARQ-81 CRIADA** — qualificação do nível 2 de D-ARQ-22: matriz-precedente não amplia universo que a norma já define (só confirma conduta dentro dele); `DEPRECATED por refutação` (sem sucessora) é estado distinto de `DEPRECATED por sucessão`. Refuta o fundamento de `R-AUD-04` (universalidade medida em 7/23 obras, `DT-003EY-01`), que sai `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]` no Commit 2 da fatia 1 (`2fbc41f`). Nenhuma R-* alterada nesta fatia (docs-only). Índice D-ARQ regenerado, **81 decisões**. Detalhe em HISTORICO 003.EZ. |
| v172 | 16/08/2026 | Sessão 003.EZ fatia 1, EMENDA 1 (docs — correção de número e registro): dois números commitados errados corrigidos nas **duas** cópias (`PENDENCIAS_CLINICAS.md`/`PROTOCOLO_AGENTE_MEDICO.md` v90) — GHEs com ruído sem quantificação carregando `R-AUD-01`/`R-AUD-02` nos motivos: **17/17** (o denominador anterior confundia GHEs com linha de audiometria com GHEs que declaram ruído — são conjuntos diferentes); linhas de exame: **173 → 172 (−1)** contra `main` em `7c7ec10` com `R-AUD-04` ativa (o número anterior comparava contra a baseline pré-`R-AUD-04` de 003.EH, predecessor errado). **D-ARQ-68 cl.5** ganha nota de fronteira medida com D-ARQ-71: as 32 pendências `predicado_ausente_presumido` são 16 GHEs × 2 regras, não 17 — o 17º (GHE-16) resolve por `perna_ausente_absorvida` (D-ARQ-71 cl.2, `vibracao_qualquer` curto-circuita o `ou` antes do ramo `Ausente`), registrando que dois GHEs com a mesma lacuna documental recebem selos diferentes (`PARCIAL` vs `VÁLIDA`) por desenho, não inconsistência. **DT-003EZ-01 CRIADA (ABERTA)** em `PENDENCIAS_CLINICAS.md` — matriz sem nenhuma linha derivada de risco (GHE-19) sai `VÁLIDA` porque `orquestrador.executar` testa `not tem_bloqueio` antes de `linhas_com_risco`; lacuna de desenho da própria D-ARQ-66 cl.2 (protege a fronteira PARCIAL/BLOQUEADA, não a de VÁLIDA), exposta por esta fatia, não introduzida por ela; não-bloqueante para o merge (a conduta emitida está correta, o selo é que erra). Nenhuma R-* nem motor tocados. Números de suíte de motor não remedidos (`1137 passed, 6 skipped`, medido em `010abbe`, continua valendo). Índice D-ARQ regenerado, **81 decisões**, fonte **v172**. Detalhe em HISTORICO 003.EZ. |
| v173 | 16/08/2026 | Sessão 003.EZ — FECHAMENTO (docs — correção de rótulo e encerramento): o changelog v171 dizia que `R-AUD-04` saiu `DEPRECATED` "na fatia 2" — a sessão teve fatias 0, 0b e 1, nunca uma fatia 2; a depreciação ocorreu no **Commit 2 da fatia 1** (`2fbc41f`). Corrigida a expressão em v171 (rótulo, não número nem fato). Sessão encerrada — ver bloco 003.EZ em HISTORICO_OPERACIONAL.md para o fechamento completo (fatias, PRs, conferência normativa D-ARQ-69, medições e lições de método). |
| v174 | 18/08/2026 | Sessão 003.FA fatia 1 (dado + teste + docs): dois aliases `termos:` sob `D-ARQ-70` cl.1 — `postura_inadequada` recebe "Postural" (19 ocorrências medidas, literal NR-17 17.4.3 "a") e `esforco_fisico` recebe "Levantamento e Transporte Manual de cargas" (12 ocorrências, literal NR-17 17.5, atribuição ao slug marcada `[INTERPRETADO]`). Quatro testes com reversão nomeada, dois deles anti-FP contra vizinho da família ergonômica (requisito (iv) de `D-ARQ-70`). Índice de termos 112 → 114 formas, zero colisão. **Nota de aplicação 003.FA em `D-ARQ-69`** — a página oficial da NR-7 omite as Portarias MTP 567/2022 e SEPRT 1.295/2021 que o PDF por ela servido lista; conferir vigência pela página erra por duas portarias. Resíduo registrado: a Base de `D-ARQ-70` cita a NR-09 pela Portaria MTP 426/2021, superada pela MTE 105/2026 (achado 003.EZ), não reconciliado. Recorte declarado: dos 56 termos distintos não resolvidos medidos na abertura, só estes 2 entram — fração sem agente (`R-PGR-05`) e recusa fuzzy (`D-ARQ-64`) **não devem** resolver; slugs com conduta ficam no regime estrito; termos sem slug são fatia própria. **Nenhuma D-ARQ criada** — `D-ARQ-82` foi especificada e descartada como gatilho falso na verificação, por `D-ARQ-70` cl.1 (ii) já cobrir o caso. Nenhuma R-* criada, alterada ou depreciada; nenhum código de motor tocado. |
| v175 | 18/08/2026 | Sessão 003.FA — FECHAMENTO (docs): passos 2, 4 e 5 do ritual, não executados no merge da fatia 1. **`DT-003FA-01` CRIADA (ABERTA, não-bloqueante)** — a Base de `D-ARQ-70` cita a NR-09 pela Portaria MTP 426/2021, superada pela MTE 105/2026 (achado 003.EZ, não reconciliado à época); a âncora de `D-ARQ-70` cl.5 (`VMB`/`VCI`) fica `[INCERTO]` até o Anexo I vigente ser relido. Bloco 003.FA gravado em `HISTORICO_OPERACIONAL.md` com a medição de abertura (154 ocorrências de termo não resolvido, 56 distintas, 19/19 GHEs; 55 de 79 slugs sem `termos:`; 3 GHEs `VÁLIDA`), a decomposição do resíduo em 6 classes e as 6 lições de método. **Painel avaliado e NÃO re-tirado** — nenhum dos três números clínicos se moveu (regras 22/42, vocabulário/CAS 50/79, dívidas 3). Registro de rastreabilidade: **`D-ARQ-82` foi especificada por inteiro e descartada antes de qualquer commit** — gatilho falso, `D-ARQ-70` cl.1 (ii) já cobre o caso ("conter o núcleo semântico do literal normativo ou sua redução direta"); a numeração 82 **não foi consumida**. Nenhuma R-* criada, alterada ou depreciada; nenhuma D-ARQ criada; nenhum código tocado. |
| v176 | 19/08/2026 | Sessão 003.FB (ARQUITETURA, entrega A — decisão escrita, sem código): **`D-ARQ-82` CRIADA** — o selo `VÁLIDA` computa sobre a **causa** da não-resolução de um termo, nunca sobre a contagem; 6 cláusulas. cl.1 `VÁLIDA` exige ausência de **lacuna**, não de pendência; cl.2 causa-acerto é lista fechada e declarada (`fuzzy_recusado`/`D-ARQ-64` cl.4 e fração-sem-agente/`R-PGR-05` nota 003.EJ), ausência de causa registrada é lacuna (default protetivo); cl.3 a causa passa a viajar no `RiscoPGR`, com invariante de pareamento 1:1 vigiada por teste computado (molde `D-ARQ-67` cl.3), campo e consumidor na MESMA fatia (precedente 003.DG-1); cl.4 slug resolvido sem regra consumidora é contribuição DETERMINADA, e **não** se cria teste "todo slug tem consumidor" (direção oposta de `D-ARQ-67`); cl.5 mantém o eixo de `D-ARQ-31` cl.1 (determinação da contribuição) e **estende o conjunto de causas** de não-determinação, sem estado novo; cl.6 quarto estado avaliado e REJEITADO. Caso-âncora **GHE-16** `[MEDIDO — Fascino, 003ez_fascino_rodar.md @ d218556; reverificado termo a termo em 003.FB]`: 19 termos não resolvidos (13 químicos de composição, 1 fração, 5 ergonômicos/acidente) e ainda assim `VÁLIDA` — entre os 13, `Metiletilcetona`, cujo slug `metil_etil_cetona` existe e resolve no GHE-10 do mesmo documento, com conduta devida por `R-BIO-04` (Quadro 1/EE, 6M periódico). Risco de **saturação do selo** assumido e declarado no corpo (previsão `[A MEDIR — 003.FC]`: 3 `VÁLIDA` → 0). Correção de número herdado: slugs sem `termos:` são **53** de 79, não 55 — o 55 é a medição de abertura de 003.FA, cuja própria entrega levou a 53 `[MEDIDO — 003.FB, parse YAML em `07476ed~2` e `07476ed`]`. **Dependência de dado declarada:** a cl.2 nomeia a fração-sem-agente como causa-acerto e esse tipo de pendência NÃO existe hoje — implementar a cl.1 antes dele derrubaria o selo por acerto do motor em 14 GHEs. Nenhuma R-* tocada; PROTOCOLO segue v90. Implementação em 003.FC. Detalhe em HISTORICO 003.FB. |
| v177 | 19/08/2026 | Sessão 003.FB entrega B1 (ARQUITETURA — decisão escrita): **`D-ARQ-83` CRIADA** — termo reconhecido-como-não-agente é categoria própria do vocabulário: entra para **NÃO** resolver, com pendência de causa e destinatário próprios. Materializa a causa-acerto que `D-ARQ-82` cl.2 nomeia e sem a qual a implementação do selo derrubaria 14 GHEs por acerto do motor. cl.1 categoria tipada em bloco top-level de `agentes.yaml` (rejeitados: slug-sentinela dentro de `agentes:`, que poria não-agente no balde de agentes contra `D-ARQ-12` e contaminaria a métrica de 79 slugs; e 5º YAML, que exigiria emendar `D-ARQ-12` sem ganho) — custo medido: 1 chamador em produção + 8 usos em teste; cl.2 a forma **nunca** entra em `slug_por_forma`, requisito de segurança travado por teste computado do dado (sem isso o termo resolveria, viraria contribuição determinada e `D-ARQ-82` cl.1 devolveria `VÁLIDA`); cl.3 consulta **depois** do hit exato e **antes** do fuzzy, com `Pendencia(tipo="fracao_sem_agente", destinatario="elaborador_pgr", regra_origem="R-PGR-05")` — ordem fixada por robustez e **não** por risco vivo: medido que `poeira_respiravel`, `poeiras_respiraveis_metalicas` e `poeira_de_madeira` não têm candidato a distância ≤2 no índice real de 114 formas `[MEDIDO — 003.FB, Levenshtein computado em 07476ed]`, logo a inversão não erraria hoje, mas passaria a errar em silêncio quando um slug novo entrasse no raio; cl.4 admissão com o rigor de `D-ARQ-70` cl.1 e o critério (ii) **invertido** (o termo entra por NÃO identificar agente). Âncora `[DERIVADO — NR-07 Anexo III Quadros 1 e 2, texto oficial MTE, releitura independente em 003.FB]`: a norma trata "poeira **contendo** `<substância>`" e mede "**poeira respirável**". Tiragem inicial 2 formas / 16 ocorrências (`Poeira respirável` 14 GHEs `[DERIVADO]`; `Poeiras Respiráveis/Metálicas` 2 `[INTERPRETADO]`), anti-FP `Poeira de madeira`. Frações granulométricas **não** enumeradas — "inalável"/"torácica" sem literal na NR-07 e sem ocorrência no corpus; NHO 08 consultada e não usada como âncora `[INCERTO]`. Nenhuma R-* criada, alterada ou depreciada; `R-PGR-05` com ID e semântica intactas; PROTOCOLO segue v90. Detalhe em HISTORICO 003.FB. |
| v178 | 19/08/2026 | Sessão 003.FB — FECHAMENTO (docs): passos 2, 4 e 5 do ritual. **`DH-003FB-02` CRIADA** (ABERTA, não-bloqueante) — leitura do repo pelo mount do Cowork deixa `.git/index.lock` órfão (o `git status` do mount toma o lock e não consegue removê-lo, por permissão), que a sessão seguinte de Code encontra e é empurrada a resolver sozinha; causa é do Arquiteto, não do repo. **`DH-003FB-03` CRIADA** (ABERTA, não-bloqueante) — o `PAINEL_ESTADO.md` se declara "vivo, não foto datada" mas sua regra de re-tiragem por-número-clínico deixa o bloco **Baseline** (hash, suíte, versões) envelhecer por desenho: medido em 003.FB, o painel diz `a8bb4d1 · 1137 passed · DECISOES v173` contra o real `a48836d · 1147 passed · DECISOES v177`, três sessões de defasagem e 10 testes de erro na contagem; correção candidata é separar Baseline (todo fechamento) dos três números (por evento). Painel **avaliado e NÃO re-tirado** — nenhum dos três números clínicos se moveu (regras 22/42 inalterado: nenhuma R-* tocada; vocabulário/CAS 50/79 inalterado: a categoria nova não cria slug nem CAS; dívidas-que-travam-produção 3 inalterado), nenhum marco fechou, sessão não é META. Suíte **1147 passed, 6 skipped**, medida em `a48836d`. PROTOCOLO segue **v90**. Detalhe em HISTORICO 003.FB. |
| v179 | 20/08/2026 | Sessão 003.FB — instrumento de método (docs + skills, sem tocar motor nem protocolo): duas skills versionadas em `.claude/skills/` — **`/conferir`** (conferidor factual: extrai toda afirmação factual de um artefato e confere contra o repo, com inventário de 100% das afirmações, achados com âncora e comando que reproduz, e **sem emitir veredito** — selo não-auditável é a classe que a `003.DQ` combate) e **`/critico`** (Gauntlet: julga a frio contra a barra do modo, com gate declarado, **eixo derivado das fronteiras do próprio artefato** em vez de escolhido pelo builder, e proibição de corrigir ou reescrever). Ambas testadas com gabarito fechado antes da execução: `/conferir` pegou 5 de 6 defeitos plantados e achou 1 não plantado; `/critico` rejeitou o artefato-isca nomeando gap melhor que o do gabarito, e aprovou `D-ARQ-82` real. Três correções nasceram do teste (inventário obrigatório; recontar contagem incidental; proibição de escrever/redirecionar saída). Nota registrada em `DH-003FB-01` com os números; **a decisão de cadência — quando cada skill é obrigatória — segue ABERTA**, para sessão META: instrumento entregue não é regra adotada. **`Gate de fechamento: CRÍTICO aprovou`** gravado no bloco 003.FB para `D-ARQ-82`; **`D-ARQ-83` segue sem julgamento**. Nenhuma R-* criada, alterada ou depreciada; PROTOCOLO segue v90. Detalhe em HISTORICO 003.FB. |
| v180 | 21/08/2026 | Sessão 003.FC, passo 1 (ARQUITETURA — emenda, docs-only): **Emenda 003.FC em `D-ARQ-82`** — `fuzzy_recusado` sai da lista de causas-acerto da cl.2. Medição de abertura do Fascino `[MEDIDO — 003.FC, fc0b468, relatorios/003fc_fascino_rodar_ANTES.md]` achou `Metiletilcetona` (o termo com conduta devida `R-BIO-04` que motiva `D-ARQ-82`) saindo do resolver como `fuzzy_recusado`, não como lacuna — pela cl.2 original isso era causa-acerto, classificando como acerto do motor exatamente o caso de dano que justificou a decisão. Causa estrutural: `fuzzy_recusado` é estado composto (recusa de resolução **sobre** possível lacuna real de `termos:`) que o motor não parte; a cl.2 já manda ler o indecidível de forma protetiva. Cl.2 emendada: única causa-acerto fechada é `fracao_sem_agente` (`R-PGR-05`, via `D-ARQ-83`); `fuzzy_recusado` é lacuna, remédio é admitir a grafia sob `D-ARQ-70`. Fronteira com `D-ARQ-83` cl.3 muda de caráter (argumento de segurança do selo cai, o de destinatário correto fica) mas a ordem fração-antes-do-fuzzy não é revogada. Duas correções de fato no caso-âncora: GHE-16 tem **17** termos não resolvidos, não 19 (os 2 de diferença resolvem pelos aliases de 003.FA); e GHE-19 tem **um** risco resolvido (`postura_inadequada`), não zero — o desfecho (`BLOQUEADA`, `linhas_com_risco` vazia) não muda. Efeito medido no Fascino: nulo (GHE-14/GHE-19 têm zero `fuzzy_recusado`; GHE-16 já cai a `PARCIAL` pelas outras 15 lacunas); previsão `3 VÁLIDA → 0` intacta. Nenhuma R-* criada, alterada ou depreciada; PROTOCOLO segue v90. Índice D-ARQ regenerado. Implementação segue em 003.FC (mesma sessão, entrega separada). |
| v181 | 21/08/2026 | Sessão 003.FC — **correção de registro da Emenda 003.FC**, achada pelo `/conferir` (1 DIVERGE em 28 afirmações extraídas): a emenda afirmava *"a cl.2 passa a ler"* sem que o texto da cl.2 tivesse sido editado, deixando a cláusula impressa dizendo o oposto da emenda dentro do mesmo corpo de decisão. Corrigido em duas pontas: (a) marca `[EMENDADA em 003.FC]` in-place ao final da cl.2, com a redação original preservada (molde `R-AUD-04`/`R-ESP-01` — texto antigo nunca some, rastreabilidade histórica do PCMSO); (b) o parágrafo passa de *"A cl.2 passa a ler"* para *"Redação vigente da cl.2"*, apontando para a original marcada em vez de alegar reescrita silenciosa. **`NÃO VERIFICÁVEL` #4/5 do relatório convertido em teste, não em medição:** T7 (`test_orquestrador.py`) exercita a **grafia nua** `"Metiletilcetona"` contra o índice real de `agentes.yaml` e confirma `NAO_RESOLVIDO`/`fuzzy_recusado` (distância 2 de `metil_etil_cetona`, slug fora de `fuzzy_permitido`) — distinta do alias EXATO `"Metiletilcetona (MEK)"` (`agentes.yaml:186`), que normaliza para `metiletilcetona_mek` e não cobre a grafia nua; reversão nomeada confirmada. Suíte 1153→**1154 passed, 6 skipped**; `mypy --strict` limpo, 48 arquivos. Nenhuma `R-*` criada, alterada ou depreciada; PROTOCOLO segue **v90**. Commits `f995f7d` + este. Detalhe em HISTORICO 003.FC. |
| v182 | 21/08/2026 | Sessão 003.FC — **FECHAMENTO** (docs + índice derivado): dois vereditos do Gauntlet gravados, com ressalva de barra (`DH-003FC-04` — o veredito de IMPLEMENTAÇÃO reportou os três testes de ARQUITETURA por defeito de template da skill; os quatro itens de IMPLEMENTAÇÃO ficam evidenciados no bloco 003.FC do HISTORICO). **`DT-003EZ-01` FECHADA** (`PENDENCIAS_CLINICAS.md`) — selo de `D-ARQ-82` implementado e medido: 3 `VÁLIDA` → 0 (GHE-14/16 → PARCIAL, GHE-19 → BLOQUEADA). Cinco `DH-003FC-*` novas: **01** e **03** criadas e resolvidas na própria sessão (limpeza de objeto materializado dentro do mount; H1 do PROTOCOLO defasado 88 versões); **02**, **04**, **05** abertas, não-bloqueantes (relatório de `rodar-offline` particiona pendência de nível-cargo e nível-termo em listas que não coincidem; três defeitos estruturais de `/critico`, para META; GITLINK pendurado em `.claude/worktrees/`, herdado, correção fora desta branch). PROTOCOLO v90→v91 (H1 sem número de versão — título alinhado à convenção dos demais docs vivos, nenhum conteúdo clínico tocado). Painel avaliado com baseline re-tirado à mão como paliativo declarado (`PAINEL_ESTADO.md`, três ocorrências de `1137 passed` atualizadas para `1154 passed`, nota `[PALIATIVO]` gravada; `DH-003FB-03` segue ABERTA — a regra de re-tiragem por-evento não muda). Suíte **1154 passed, 6 skipped**; `mypy --strict` limpo, 48 arquivos. Nenhuma `R-*` criada, alterada ou depreciada. Detalhe em HISTORICO 003.FC. |
| v183 | 22/08/2026 | Sessão 003.FD — META (docs + skills, sem tocar motor nem protocolo clínico): **D-ARQ-84 CRIADA** — `/conferir` passa a ser obrigatório sobre artefato que crava fato (lista fechada de 5 tipos), **sem declaração ritual nova** (a evidência é o relatório falsificável, não um selo — `D-ARQ-22`); `DIVERGE` material bloqueia a emissão, `NÃO VERIFICÁVEL` converte-se em teste quando o objeto é comportamento do motor; `/critico` inalterado quanto à cadência (`003.DQ` intocada); coerência interna do artefato entra como classe de erro do conferidor, **não** como 4º item da barra de ARQUITETURA — decidido contra a medição de que o Gauntlet leu a decisão inteira a frio e não pegou a contradição da cl.2 de `D-ARQ-82`. **D-ARQ-85 CRIADA** — Baseline e três números clínicos do painel passam a ter cadências distintas (Baseline em todo fechamento; três números por evento, regra intacta), com hash e versões derivados do repo, contagem de suíte carimbada com o commit em que foi medida, e declaração explícita de que hash e contagem **não** são testáveis por não-divergência. **Barra de IMPLEMENTAÇÃO alterada** (autorizada pelo Diovanni nesta sessão): o item 4 deixa de ser teste do Crítico e passa a ser evidência registrada pelo builder, que o Crítico verifica sem re-executar — `DH-003FC-04(b)` fechada. `DH-003FB-01` **FECHADA** (cadência decidida), `DH-003FC-04` **FECHADA** (três facetas: slots de saída por modo, item 4 reescrito, `git diff` no `allowed-tools`), `DH-003FB-03` **PARCIALMENTE RESOLVIDA** (regra decidida; instrumento em `DT-003FD-01`). Três pendências novas, todas não-bloqueantes: `DT-003FD-01` (instrumento do Baseline), `DT-003FD-02` (o registro de suíte que a barra nova exige mora onde a Regra zero do Crítico proíbe ler — resolvido por exceção nominal **declarada como paliativo**) e `DH-003FD-01` (a barra de ARQUITETURA não tem forma aplicável a decisão META). PROTOCOLO segue **v91** — nenhuma `R-*` criada, alterada ou depreciada. Detalhe em HISTORICO 003.FD. |
| v184 | 22/08/2026 | Sessão 003.FD — **EMENDA (Gauntlet)**: correção do gap que rejeitou `D-ARQ-84`. A fronteira `DT-003DX-02` afirmava *"É a primeira regra desse público sob versionamento"* — falso contra `D-ARQ-26` (`/kickoff` versionado em `0dd0449`, sessão 002.U) e contra `/conferir`/`/critico` (`e1952ac`, 003.FB), e contraditório com a frase anterior da própria fronteira. Redação corrigida para nomear o que a decisão de fato acrescenta (a **regra de cadência** entra no git, não o instrumento, que já estava) + nota `Correção 003.FD-E` preservando a redação rejeitada. **Nenhuma cláusula de `D-ARQ-84` tocada** — o defeito era de fronteira, não de dispositivo; `D-ARQ-85` **APROVADA** sem alteração. Semente da afirmação corrigida também em `DH-003FB-01`. Vereditos gravados no bloco 003.FD do HISTORICO, com ressalva de procedência: **o Gauntlet correu depois do merge do PR #311** — o bloco entrou em `main` com o gate por preencher. Nenhuma `R-*` criada, alterada ou depreciada; PROTOCOLO segue **v91**; contagem de decisões inalterada em **85**. Detalhe em HISTORICO 003.FD. |
| v185 | 22/08/2026 | Sessão 003.FD — **2ª EMENDA (Gauntlet)**: `D-ARQ-84` rejeitada pela segunda vez, mesma classe de erro em ponto distinto. A cl.4 afirmava *"Permanece o gate de fechamento instituído por `003.DQ`"* — falso: `003.DQ` instituiu o gate de **abertura** (Contexto de `D-ARQ-63`; bloco 003.DQ do HISTORICO registra que as instruções foram atualizadas **fora do repo**), e `/critico` nasce em 003.FB (`e1952ac`). Contradizia, no mesmo corpo, a cl.2 e a seção de Fronteiras. Cláusula reescrita **sem alterar o dispositivo** + bloco de procedência declarando que o gate de fechamento **não tem âncora versionada em D-ARQ alguma** (`git grep` @ `c765863`) → abre **`DT-003FD-03`**. Nota `Correção 003.FD-E2` preserva a redação rejeitada; nota `Correção 003.FD-E` reposicionada para o fim da seção (defeito de estrutura introduzido pela 1ª emenda, que a partia ao meio). **Varredura completa do artefato feita antes desta emenda** — 28 afirmações extraídas, 27 CONFERE / 1 DIVERGE —, em vez da correção pontual que a 1ª emenda fez e que deixou este defeito passar (violação da cl.3 da própria `D-ARQ-84`). `D-ARQ-85` intacta e aprovada. Nenhuma `R-*` criada, alterada ou depreciada; PROTOCOLO segue **v91**; decisões inalteradas em **85**. Detalhe em HISTORICO 003.FD. |
| v186 | 22/08/2026 | Sessão 003.FD — **FECHAMENTO**: `D-ARQ-84` **APROVADA** na 3ª rodada do Gauntlet (@ `e98c192`, sessão nova a frio) — universalidade, caso local e registrabilidade PASSA, com a nota `[MEDIDO]` de procedência da cl.4 reconferida de forma independente pelo próprio Crítico (`git grep` @ `c765863` e @ `HEAD`) e o precedente da cl.3 (`# T7 (003.FC)`) verificado no arquivo de teste real. Ciclo: **três rodadas, duas rejeições, uma aprovação**; `D-ARQ-85` aprovada de primeira. Duas pendências movidas: **`DH-003FD-01`** ganha confirmação independente (o Crítico declarou por conta própria que a skill não tem barra para o modo META e tratou o artefato como ARQUITETURA por eliminação) e **`DT-003FD-01`** ganha a faceta do critério de re-tiragem (Baseline é função de "a sessão fechou", não de "houve commit" — medido nas três emissões desta sessão). Uma pendência nova: **`DH-003FD-02`**, ABERTA — a proibição de escrever nas skills de método é textual e não enforçável pelo `allowed-tools`, 2ª ocorrência medida, a 1ª sendo a que originou a própria proibição em 003.FB. `PAINEL_ESTADO.md` **não** re-tirado, pela regra medida em 003.ER (o campo grava a `main` de partida; `e98c192` entra na tiragem de 003.FE) — decisão declarada, não omissão. Nenhuma `R-*` criada, alterada ou depreciada; PROTOCOLO segue **v91**; decisões inalteradas em **85**. Detalhe em HISTORICO 003.FD. |
| v187 | 15/09/2026 | Sessão atual (branch `claude/festive-gates-soy0fr`, número ainda não atribuído) — comparação PGR "CMO Residencial Aurora Lago das Rosas" (matriz do app × gabarito RQ.61 assinado, Dra. Patrícia Montalvo Moraes) contra o motor. **Nota de aplicação em `D-ARQ-65`** (mesma ID, sem cláusula alterada) — terceira testemunha negativa: `parsear_arquivo` rodado diretamente contra o PGR bruto da Aurora levanta `FamiliaNaoReconhecida` já no 1º bloco (`ADMINISTRAÇÃO`); leitura de `orquestracao_pgr.py:188-211` confirma que a falha é do documento inteiro (uma só chamada a `parsear_arquivo` por arquivo, exceção no 1º bloco aborta antes dos 8 seguintes), não contaminação seletiva de um GHE — mesmo padrão já registrado para Viverde, agora numa terceira família de template. Nenhuma `R-*`/D-ARQ criada, alterada ou depreciada; nenhum código de motor tocado nesta nota. PROTOCOLO inalterado, segue **v92**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v188 | 16/09/2026 | Sessão atual (branch `claude/festive-gates-soy0fr`, mesma sessão da v187 — IMPLEMENTAÇÃO): **Nota de aplicação em `D-ARQ-83`** (mesma ID, sem cláusula alterada) — o anti-FP "Poeira de madeira" da tiragem original (003.FB) se confirma: o termo nunca entrou em `fracoes_sem_agente`, e esta sessão dá a ele slug próprio (`poeira_de_madeira`, `agentes.yaml`) em vez de tratá-lo como fração-sem-agente. **`R-RX-03` e `R-ESP-03` CRIADAS** (ver changelog do PROTOCOLO v93) — resolvem `DT-003EJ-01`. Nenhuma cláusula de D-ARQ alterada; nenhuma D-ARQ nova. PROTOCOLO v92→**v93**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v189 | 16/09/2026 | Sessão (branch `claude/youthful-lamport-3kfkog`, número não atribuído): **Nota de aplicação em `D-ARQ-73`** (mesma ID, nenhuma cláusula alterada) — `renderizar_docx` ganha estilo visual portado de `modules/modulo_pcmso.py::gerar_docx_rq61` (legado, v9.5): borda de tabela, cabeçalho de coluna com fundo/texto brancos, título e cabeçalho de GHE em cor de destaque, sem nome nem identidade de terceiro. Correção de escopo própria da sessão: merge vertical de célula por Cargo (também do legado) não se aplica — a forma atual já emite um cargo por linha, não repetido por exame. `montar_documento`/`DocumentoMatriz` sem uma linha tocada; `renderizar_html` inalterado. 3 testes novos, 3/3 reversão inversa confirmada; verificação visual via pipeline real (Fascino) convertido a PDF e inspecionado. Nenhuma `R-*` criada, alterada ou depreciada; PROTOCOLO inalterado, segue **v93**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v190 | 17/09/2026 | Sessão atual (branch `claude/fervent-brown-7dcc0y`, número não atribuído; IMPLEMENTAÇÃO, autorizada pelo Diovanni): **Nota de aplicação em `D-ARQ-49`** (mesma ID, nenhuma cláusula alterada) — o campo psicossocial diferido na Parte 2 (então nomeado "R-PSY-01") ganha extrator: `detectar_psicossocial` (`extracao_pgr.py`) popula `GHEPGR.psicossocial` lendo o texto cru do PGR inteiro por 3 marcadores; `hidratar_ghe`/`hidratar_pgr` ganham parâmetro homônimo; `processar_arquivo_pgr` roda uma 3ª leitura de `extrair_texto_pgr` (mesma classe da duplicação já documentada em D-ARQ-52/53). **`R-PSY-02` DEPRECATED, `R-PSY-03` CRIADA** (ver changelog do PROTOCOLO v94) — resolve `DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-01`. Nenhuma cláusula de D-ARQ alterada; nenhuma D-ARQ nova. PROTOCOLO v93→**v94**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v191 | 17/09/2026 | Sessão atual (branch `claude/fervent-brown-7dcc0y`, mesma sessão da v190; IMPLEMENTAÇÃO, escopo autorizado pelo Diovanni — só o regex, não a arquitetura de ingestão): **Nota de aplicação em `D-ARQ-57`** (mesma ID, nenhuma cláusula alterada) — `_reconhece_funcao_grid_perigo_risco_fragmentado` novo casa o cabeçalho do grid AIHA (Hetrin/Serra Dourada) fragmentado em duas linhas adjacentes (revisão de 14/09/2026 do PGR Hetrin mudou o wrap de coluna), restaurando a pendência correta `pgr_cargo_based` no lugar de `segmentacao_implausivel`. Achado que precedeu o código: o grid AIHA nunca teve caminho de ingestão automática — nem o PGR de março/2025 gera matriz hoje (já bloqueava via `pgr_cargo_based`, medido pela primeira vez nesta sessão) — `parser_familia_consciente.py` (D-ARQ-65) é de outra família (Consciente/Fascino), e a peça 4 (D-ARQ-57) exclui o grid AIHA do recorte-por-cargo por decisão (003.DC/003.DF). `DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-02` REENQUADRADA (`PENDENCIAS_CLINICAS.md`), não fechada — segue precisando de ARQUITETURA própria (unidade de recorte de tabela compartilhada por linha-de-cargo) para gerar matriz. Validado contra os 40 PGRs reais do acervo: só o Hetrin 14/09/2026 muda de classificação. 15 testes novos com reversão nomeada, varredura inversa 15/15 confirmada. Nenhuma `R-*` criada, alterada ou depreciada; nenhuma D-ARQ nova. PROTOCOLO inalterado, segue **v94**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v192 | 19/09/2026 | Sessão atual (branch `claude/blissful-knuth-riqucz`, número não atribuído; ARQUITETURA — ratificação, docs-only): **Ratificação em `D-ARQ-57`** (mesma ID, nenhuma cláusula alterada) — Diovanni ratifica o fatiamento 5a→5b→5c→5d proposto pela sessão `claude/dreamy-mayer-os6jce` (18-19/09): sem reordenar para priorizar o witness Hetrin/set-2026 (o documento do chamado real) antes de 5a calibrado nos 2 witnesses limpos; risco nomeado naquela sessão (Hetrin/set-2026 só destravado em 5b/5d) mantido, aceito, não mitigado por reordenação. `DT-(sessão claude/youthful-lamport-3kfkog)-02` (`PENDENCIAS_CLINICAS.md`) recebe nota da ratificação — segue ABERTA até a fatia 5d fechar. `DT-(sessão claude/dreamy-mayer-os6jce)-01` (relatório de rastreabilidade/proveniência da matriz) recebe nota de sequenciamento: Diovanni prioriza fechar D-ARQ-57 peça 5 antes de abrir sessão ARQUITETURA própria para aquele item. Nenhuma `R-*` criada, alterada ou depreciada; nenhuma D-ARQ nova. PROTOCOLO inalterado, segue **v94**; decisões inalteradas em **85**. Índice D-ARQ regenerado. |
| v193 | 19/09/2026 | Sessão atual (branch `claude/blissful-knuth-riqucz`, mesma sessão da v192; IMPLEMENTAÇÃO): **Nota de aplicação em `D-ARQ-57`** (mesma ID, nenhuma cláusula alterada) — fatia 5a (`agente_medico/motor/parser_familia_grid_aiha.py`) IMPLEMENTADA: banda de coluna calibrada por página + fronteira de função. Medição desta sessão achou 2 problemas de anatomia não previstos na ARQUITETURA (rótulo compartilha `top` com outras colunas; nome quebra em >1 linha física) — corrigidos, e a "ambiguidade" que motivou `TrechoAmbiguo`/`Pendencia` na ratificação (v192) desaparece: era artefato de bug, não estrutura real. `TrechoAmbiguo` não entrou no código. Validado contra os 2 witnesses reais: nomes e contagens de linha exatas batendo; confirmação cruzada com `extract_tables()` (41 funções/80 páginas Hetrin/mar extrapola pra ~63, mesma ordem do "~60" já medido; Serra Dourada 56 páginas/28 grupos exato, sem sobra). `mypy --strict` alvo canônico limpo, **49 arquivos** (+1). Suíte nova `test_parser_familia_grid_aiha.py`: 13 testes, reversão nomeada 7/7 nos testes de núcleo puro. Nenhuma `R-*` criada, alterada ou depreciada; nenhuma D-ARQ nova. PROTOCOLO inalterado, segue **v94**; decisões inalteradas em **85**. Índice D-ARQ regenerado. Detalhe em HISTORICO (bloco desta sessão). |
| v194 | 19/09/2026 | Sessão atual (branch `claude/nice-ptolemy-wxk1wo`, número não atribuído; ARQUITETURA/bloqueador, sem código de produção): **Nota de aplicação em `D-ARQ-57`** (mesma ID, nenhuma cláusula alterada) — ao abrir a fatia 5b (decomposição N:1), medição contra os 2 witnesses calibrados (`segmentar_arquivo` real) achou **zero** casos de N:1 genuíno alcançável: os 3 candidatos com `/` no nome (Hetrin/mar) são título composto ou par de gênero de **1 cargo só**, confirmado lendo a descrição sob cada um. O N:1 real (lista de cargos distintos, molde da ARQUITETURA) só existe no witness Hetrin/set-2026, que a fatia 5a não alcança: `segmentar_arquivo` levanta `GrupoFuncaoNaoReconhecido` porque o grid desse documento usa cabeçalho em CAIXA ALTA (`'FUNÇÃO'`/`'TIPO'`, pág. 14) contra o title-case exigido por `_localizar_cabecalho_grid` — nenhuma página do documento inteiro tem `'Função'` exato fora de uma tabela não-relacionada (pág. 62, EPI-por-função). Bloqueador reportado: fatia 5b sem alvo real hoje; decisão de como prosseguir cabe ao Arquiteto. `DT-(sessão claude/youthful-lamport-3kfkog)-02` segue ABERTA — nota espelhada em `PENDENCIAS_CLINICAS.md`. Nenhuma `R-*` criada, alterada ou depreciada; nenhuma D-ARQ nova. PROTOCOLO inalterado, segue **v94**; decisões inalteradas em **85**. Índice D-ARQ regenerado. |
