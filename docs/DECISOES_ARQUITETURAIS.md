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
