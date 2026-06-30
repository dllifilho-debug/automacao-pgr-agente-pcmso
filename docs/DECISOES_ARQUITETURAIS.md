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

## D-ARQ-39 — Convergência de mesmo-exame com periodicidades distintas resolve por piso component-wise, não por ConflitoProtocolo

**Status:** DECISÃO DE ARQUITETURA (ARQUITETURA). Sem código nesta sessão. Implementação (substituição do gate de erro por cálculo de mínimo + duas atribuições) é fatia IMPL futura. Autorização para virar D-ARQ é do Diovanni.

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
