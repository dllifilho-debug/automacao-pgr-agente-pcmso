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
