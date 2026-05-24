# HISTÓRICO OPERACIONAL — AGENTE MÉDICO PCMSO

Registro cronológico de sessões, decisões operacionais e lições aprendidas.
Não substituir — apenas acrescentar entradas ao final.

---

## Sessão 001 — 16-17/05/2026

**Tipo:** CONHECIMENTO
**Participantes:** Diovanni Lisita + Dra. Carolini Polesso (assíncrona)
**Objetivo:** Primeira extração formal do protocolo clínico da Dra. Carolini

### O que foi feito

1. Diovanni enviou roteiro estruturado de 10 blocos e 47 perguntas à Dra. Carolini via WhatsApp (arquivo: `ROTEIRO_ENTREVISTA_DRA_CAROLINI.md`)
2. Dra. Carolini respondeu em 47 áudios (~30min total), gravados em 16/05/2026
3. Transcrição feita via **Whisper** (modelo `medium`, CPU, local na máquina de Diovanni) — ~20 min de processamento para 47 arquivos `.ogg`
4. Pareamento pergunta → resposta feito manualmente com apoio do Claude
5. Protocolo formalizado em `PROTOCOLO_AGENTE_MEDICO.md` v1
6. Segunda rodada de validação feita por escrito (6 perguntas de lacuna) — respondida em 17/05/2026
7. Protocolo atualizado para v2 — sem lacunas remanescentes

### Resultados

- `PROTOCOLO_AGENTE_MEDICO.md` v2 — ~50 regras com IDs estáveis, todas `[VALIDADO]`
- `DECISOES_ARQUITETURAIS.md` v2 — 7 decisões de design (D-ARQ-01 a D-ARQ-07)
- Matriz RQ.61 Viverde validada como correta pela Dra. Carolini

### Método que funcionou

**Perguntas estruturadas por bloco → áudio assíncrono → transcrição Whisper → pareamento → protocolo formalizado → rodada de validação por escrito**

Esse fluxo é replicável para outras especialistas (ergonomia, psicossocial, higiene ocupacional). Pontos de atenção:

- Whisper `medium` tem boa acurácia para PT-BR técnico de medicina do trabalho
- Termos específicos que o Whisper errou: "FISPQ" transcrito como "FISPIC", "fumos metálicos" às vezes como "fomos metálicos", "PNOS" correto. Revisar esses termos manualmente em transcrições futuras
- Segunda rodada por escrito (sem áudio) foi mais eficiente para fechar lacunas pontuais
- Mandar o protocolo formalizado para a especialista revisar (em vez de novas perguntas isoladas) captura discordâncias estruturais que perguntas não capturam

### Lacunas que ficaram para futuras sessões

- Item exato da NR-07 que fundamenta espirometria via EPI (R-PGR-03, R-ESP-01) — citado pela Dra. Carolini mas não localizado no texto da norma
- Item exato da NR-07 que fundamenta RX de tórax para sílica ≥ 10% LT (R-RX-01) — idem
- Validação do protocolo com PGR de setor não-construção (mineração ou farmacêutico) — D-ARQ-06

### Próxima sessão planejada

**Tipo:** ARQUITETURA
**Objetivo:** Desenhar o motor de inferência do agente sobre o protocolo v2
**Pré-requisitos:** protocolo v2 commitado no repositório

---

## Sessão 002 — 17/05/2026

**Tipo:** ARQUITETURA
**Participantes:** Diovanni Lisita + Claude (Arquiteto)
**Objetivo:** Desenhar o motor de inferência sobre o protocolo v2

### O que foi feito

1. Proposta inicial de pipeline em 9 estágios + 5 bifurcações abertas para decisão (B-1 a B-5)
2. Diovanni autorizou Claude a fechar as bifurcações pela melhor decisão técnica
3. Claude revisou criticamente o próprio desenho e identificou 6 fragilidades estruturais (F-1 a F-6)
4. Decisões consolidadas em D-ARQ-08 a D-ARQ-13
5. Pipeline reduzido para 8 estágios (matriz temporal por Anexo virou lint de carregamento, não estágio runtime)
6. Tipos centrais especificados (`PGR`, `GHEContext`, `Risco`, `Quantificacao`, `ExameEmitido`, `Pendencia`, `Resultado`)
7. Schema YAML de regras, predicados compostos e vocabulário especificado
8. Estrutura de arquivos do motor definida

### Resultados

- `DECISOES_ARQUITETURAIS.md` v3 — 6 novas decisões (D-ARQ-08 a D-ARQ-13)
- Pipeline do motor em 8 estágios: gates → expansão de riscos → pendências bloqueantes → predicados → emissão → regime → consolidação → TODOs operacionais
- Contrato de cada estágio definido como função pura

### Bifurcações fechadas pelo Arquiteto (autorizado pelo Diovanni)

| ID  | Bifurcação                                     | Decisão                                                |
|-----|------------------------------------------------|--------------------------------------------------------|
| B-1 | Schema de predicado: simples ou composto       | Composto com `e/ou/nao`                                |
| B-2 | Onde definir predicados                        | Primitivos em código, compostos em YAML (D-ARQ-10)     |
| B-3 | Granularidade do audit trail                   | Granular: regra_id + predicado + risco_origem + detalhe |
| B-4 | Reaproveitamento dentro ou fora do motor       | Fora — agendador é camada separada (D-ARQ-11)          |
| B-5 | Dado faltante = bloqueante ou silencioso?      | Bloqueante por default, com `quando_ausente: false` como escape (operacionalizado em D-ARQ-13) |

### Fragilidades identificadas na auto-revisão (F-1 a F-6)

| ID  | Fragilidade                                                    | Resolução                                              |
|-----|----------------------------------------------------------------|--------------------------------------------------------|
| F-1 | Vocabulário referenciado mas não modelado                      | D-ARQ-12 — 4 YAMLs em `protocolo/vocabulario/`         |
| F-2 | Stage 6 (matriz temporal) com semântica ambígua                | Virou lint de carregamento; pipeline cai para 8 estágios |
| F-3 | `Quantificacao` mencionada mas não tipada                      | Tipo definido com `valor`, `unidade`, `relacao_LT`, `pct_LT`, `apenas_qualitativa` |
| F-4 | B-5 sem operacionalização concreta                             | D-ARQ-13 — predicados tri-estado                       |
| F-5 | Como regra sabe o Anexo do risco que originou                  | Stage 2 hidrata `Risco` com metadados de `agentes.yaml` (consequência de D-ARQ-12) |
| F-6 | Regime ANAC sem estrutura definida                             | YAML por regime em `protocolo/regimes/` com `adiciona_exames`, `sobrescreve_periodicidade`, `remove_exames` |

### Decisão sobre a cascata multi-IA gratuita

Plano antigo recuperado das conversas anteriores:

```
Gemini 2.5 Flash → Gemini 2.0 Flash → Groq Llama-3.3-70b → OpenRouter Mistral
```

Posicionamento: a cascata é da **camada de extração de PGR**, não do motor (D-ARQ-09 reforça que motor é determinístico).

Sequência acordada:

1. Implementar motor sobre PGR mockado em Python (sem LLM)
2. Validar motor contra matriz RQ.61 Viverde
3. Voltar à camada de extração e adaptar prompt do Gemini ao schema novo
4. Implementar cascata 4-providers depois do prompt validado em 1 PGR

Antecipar a cascata agora seria otimização prematura — gargalo atual é motor inexistente, não quota de API.

### Estrutura de arquivos definida

```
agente_medico/
    motor/
        tipos.py
        protocolo.py
        predicados.py
        lint.py
        estagios/
            gates.py riscos.py pendencias.py predicados_stage.py
            emissao.py regime.py consolidacao.py todos.py
        orquestrador.py
    protocolo/
        vocabulario/
            agentes.yaml cargos.yaml exames.yaml epis.yaml
        predicados_compostos.yaml
        regras.yaml
        regimes/
            anac.yaml
    tests/
        unitarios/
        integracao/
            test_viverde.py
```

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.A)
**Objetivo:** Estrutura inicial — `tipos.py` + `protocolo.py` + carregamento dos YAMLs do vocabulário e do protocolo (sem lógica de inferência ainda)
**Pré-requisitos:** D-ARQ-08 a D-ARQ-13 commitadas em `DECISOES_ARQUITETURAIS.md`
**Subsessões previstas:**
- 002.A — tipos + carregamento + validação de schema
- 002.B — predicados (registro de primitivos) + estágio gates + teste
- 002.C — emissão + consolidação + teste com 2-3 regras
- 002.D — estágios restantes + integração Viverde

---

## Sessão 002.A — 17/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6, v2.1.143)
**Objetivo:** Estrutura inicial do motor — tipos + carregamento de protocolo

### O que foi feito

1. Patch dos docs `DECISOES_ARQUITETURAIS.md` (v3) e `HISTORICO_OPERACIONAL.md` (Sessão 002) commitado em `main`
2. Branch `feature/motor-002a-tipos` criada
3. Prompt cirúrgico (`prompt_002a.txt`) executado no Claude Code via `Get-Content -Raw prompt_002a.txt | claude`
4. Estrutura `agente_medico/` criada: 16 dataclasses/enums em `tipos.py`, função `carregar()` em `protocolo.py`, 7 YAMLs mínimos do protocolo, 5 testes
5. PyYAML adicionado ao `requirements.txt`
6. `.gitignore` adicionado na raiz do projeto (cobre `**/__pycache__/`, `**/*.pyc`, `.mypy_cache/`)
7. Commits: `6f48f8c feat(motor): estrutura inicial (002.A)` + `ba0b03c chore: adiciona .gitignore`
8. Push da branch `feature/motor-002a-tipos` pro GitHub

### Resultados

- **Critério 1** — `pytest agente_medico/tests/` → 5/5 verdes (3 mínimos + 2 extras)
- **Critério 2** — `carregar('agente_medico/protocolo/')` → sem erro
- **Critério 3** — `mypy --strict agente_medico/motor/tipos.py` → no issues found
- 23 arquivos criados, 315 linhas de código

### Problemas operacionais durante a sessão

**P-1. Repositório local com `.git/` corrompido.**
Antes de executar a 002.A, ao tentar `git push` o repositório acusou `fatal: You are not currently on a branch` e em seguida `fatal: your current branch appears to be broken`. Causa provável: remoção manual de um worktree do Claude Code (`.claude/worktrees/romantic-margulis-dcccad`) deixou refs órfãs no `.git/`. Diagnóstico: `.git/objects` com apenas 41 objetos (esperado: 1229+), pack files perdidos.

**Reparo aplicado:**
1. Backup do diretório inteiro (`automacao-pgr-seconci_BACKUP_20260517_134236`)
2. Clone fresh em pasta paralela (`automacao-pgr-seconci_FRESH`) — 1229 objetos baixados do GitHub
3. Cópia dos 2 docs novos (DECISOES v3, HISTORICO Sessão 002) pra `docs/` do clone fresh
4. Commit + push dos docs no clone fresh
5. Renomeação: pasta quebrada → `_BROKEN`, fresh → oficial

**P-2. Crash do computador durante a primeira tentativa de executar o prompt 002.A.**
Provável causa: VS Code + PowerShell + navegador + Claude Code rodando simultaneamente saturaram a RAM. Computador travou e foi reiniciado. Nada foi perdido (Code ainda não tinha criado arquivos). Segunda tentativa rodou só com PowerShell aberto.

**P-3. Pipe `Get-Content | claude` conflitou com menu de confirmação interativo.**
Ao adicionar a flag `--dangerously-skip-permissions`, o menu de warning bloqueava a stdin (já consumida pelo pipe), impossibilitando confirmar com `2`. Solução: rodar `claude` normalmente sem pipe e usar `@prompt_002a.txt` dentro da sessão interativa pra referenciar o arquivo. Funcionou na primeira tentativa.

**P-4. Claude Code tentou usar caminhos Linux (`/mnt/c/...`) em ambiente Windows.**
Primeira chamada de `Bash(cd /mnt/c/Users/...)` falhou. Code corrigiu automaticamente substituindo por `PowerShell(New-Item ...)`. Sem intervenção necessária — adicionado lembrete pra futuras sessões priorizarem comandos Windows nativos.

### Lições aprendidas

- **Worktrees do Claude Code não devem ser removidos manualmente.** Se for limpar `.claude/worktrees/`, usar comando do próprio Code, não `rm -rf`.
- **Antes de executar Code, fechar tudo exceto PowerShell.** RAM é gargalo real em máquinas de dev.
- **Pipe pra Code só funciona sem flags interativas.** Pra modo bypass, abrir Code sem pipe e usar `@arquivo.txt` dentro da sessão.
- **Backup físico do diretório antes de qualquer operação destrutiva de git.** Saved a vida hoje.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.B)
**Branch:** `feature/motor-002b-predicados-gates` (já criada a partir de 002.A)
**Objetivo:** Implementar `predicados.py` (registro de primitivos via decorator, avaliador de compostos com tri-estado conforme D-ARQ-13) + `estagios/gates.py` (R-PGR-01 e R-PGR-06) + testes
**Escopo de primitivos:** ~5 primitivos básicos (`altura`, `espaco_confinado`, `maquina_pesada`, `ruido`, `ruido_acima_acao`) — suficiente pra deixar `atividade_critica` testável. Demais primitivos entram nas sessões 002.C e 002.D conforme as regras que os usam forem implementadas.

---

## Sessão 002.B — 17/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6, v2.1.143)
**Branch:** `feature/motor-002b-predicados-gates`
**Objetivo:** Predicados primitivos + Stage 1 (gates)

### O que foi feito

1. Criado `agente_medico/motor/predicados.py` — decorator `@primitivo`, registro `REGISTRO_PRIMITIVOS`, 5 primitivos físicos (`altura`, `espaco_confinado`, `maquina_pesada`, `ruido`, `ruido_acima_acao`), avaliador de compostos com tri-estado (`e`/`ou`/`nao`), `avaliar_predicado` com detecção de ciclo via exceção `CicloPredicados`
2. Criado `agente_medico/motor/estagios/__init__.py` + `gates.py` — `stage_1_gates(pgr, hoje=None)` implementando R-PGR-01 (assinatura de engenheiro) e R-PGR-06 (validade do PGR, prazo de 730 dias = 2 anos), com `hoje` injetável para testes
3. Criados `agente_medico/tests/test_predicados.py` e `test_gates.py` — cobertura completa: registro, todos os 5 primitivos, tri-estado em todas as combinações (e/ou/nao com bool e Ausente), resolução de primitivo vs composto, ciclo, boundaries de R-PGR-06 (1a11m, 2 anos exatos, 2 anos + 1 dia)
4. Commit único `6d011c1 feat(motor): predicados primitivos + stage_1_gates (002.B)` pushed para origin

### Resultados

- **pytest** — 41/41 verdes (5 da 002.A + 36 novos)
- **mypy --strict** em `predicados.py` e `estagios/gates.py` — `Success: no issues found in 2 source files`
- 5 arquivos novos, 453 linhas adicionadas

### Decisão de implementação registrada

**Semântica de `pgr.validade`:** interpretada como "data de emissão do PGR" (não data limite). Gate R-PGR-06 falha se `(hoje - pgr.validade) >= timedelta(days=730)`. Justificativa: R-PGR-06 diz "validade emitida há 2 anos ou mais" — implementação em "data de emissão" se alinha melhor com a redação do protocolo. Caso o parser de PGR (camada anterior) entregue "data limite" em vez de emissão, o tipo precisará ser desambiguado em 002.C.

### Problemas operacionais durante a sessão

**P-5. Paste direto no Claude Code travou (mesmo problema da 002.A).**
Colar o conteúdo do prompt diretamente no terminal do Claude Code não funcionou — o input não foi aceito. Solução consolidada (já validada em 002.A): copiar `prompt_002b.txt` pra raiz do projeto e digitar comando curto `Leia o arquivo prompt_002b.txt e execute todas as tarefas descritas nele.` Funcionou na primeira tentativa.

### Lições aprendidas

- **Paste de prompts longos no Code é instável.** Padrão consolidado: salvar prompt como `.txt` na raiz do projeto, instruir o Code via comando curto referenciando o arquivo. Vale anotar isso como protocolo permanente.
- **Manter `hoje` injetável em funções com `date.today()` desde o início.** Sem isso, testes de boundary em datas ficam frágeis.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.C)
**Branch:** `feature/motor-002c-emissao` (a criar a partir de 002.B)
**Objetivo:** Stage 5 (emissão de exames via `regras.yaml`) + Stage 8 (consolidação/dedup) + regra `R-PKG-ATIVCRIT` completa end-to-end com `atividade_critica` testável
**Pré-requisito:** popular `predicados_compostos.yaml` com `atividade_critica`; popular `regras.yaml` com R-PKG-ATIVCRIT; validar que pipeline gates → predicados → emissão funciona end-to-end em fixture mockado

## Sessão 002.C — 18/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6, v2.1.143)
**Branch:** `feature/motor-002c-emissao`
**Objetivo:** Emissão (Stage 5) + consolidação/dedup (Stage 8) + R-PKG-ATIVCRIT end-to-end

### O que foi feito

1. `predicados_compostos.yaml` populado com `atividade_critica` (ou: altura, espaco_confinado, maquina_pesada)
2. `regras.yaml` populado com R-PKG-ATIVCRIT (5 exames: hemograma, glicemia, audiometria, acuidade_visual, ecg — todos 12M, adm/per/MR)
3. `agente_medico/motor/estagios/emissao.py` — `stage_5_emissao`: avalia `quando` da regra via `avaliar`, emite `ExameEmitido` quando True, trata tri-estado D-ARQ-13 (Ausente → `Pendencia` bloqueante; `quando_ausente: false` silencia)
4. `agente_medico/motor/estagios/consolidacao.py` — `stage_8_consolidacao` + exceção `ConflitoProtocolo`: dedup por nome normalizado (`strip().lower()`), merge de momentos via união de sets, concatenação de motivos, falha dura em divergência de periodicidade
5. 3 arquivos de teste: `test_emissao.py` (7), `test_consolidacao.py` (7), `test_integracao_002c.py` (1 end-to-end)
6. `types-PyYAML` instalado para satisfazer `mypy --strict` (stubs ausentes em `protocolo.py`)

### Resultados

- **pytest** — 56/56 verdes (41 anteriores + 15 novos)
- **mypy --strict** em `emissao.py` + `consolidacao.py` → Success: no issues found
- Teste de integração valida Stage 1 → Stage 5 → Stage 8 em PGR mockado com risco "trabalho_altura" → 5 exames de R-PKG-ATIVCRIT emitidos corretamente

### Dívida técnica registrada

**DT-002C-01 (audit trail incompleto).** `Motivo.risco_origem=None` em todos os `ExameEmitido` produzidos pelo Stage 5. Audit trail completo requer mudar a assinatura de `avaliar_predicado` para devolver contexto (riscos_responsaveis) além de `bool | Ausente`. Não é dívida da 002.C — é decisão arquitetural nova. Endereçar como D-ARQ-14 quando o problema se manifestar na UI (com 1 regra hoje não há ambiguidade que justifique).

**DT-002C-02 (identidade do exame por string).** Dedup em `stage_8_consolidacao` usa `nome.strip().lower()` como chave. Pré-requisito da 002.D: popular `vocabulario/exames.yaml` ANTES de adicionar qualquer segunda regra ao `regras.yaml`. Refatorar a única regra existente é trivial; postergar essa transição depois de N regras é dívida exponencial.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.D)
**Branch:** `feature/motor-002d-vocabulario` (a criar de main após merge da 002.C)
**Objetivo:** Vocabulário tipado (`vocabulario/exames.yaml` primeiro — endereça DT-002C-02) + Stage 2 (expansão de riscos) + Stage 4 (popular `ctx.predicados`) + Stage 3 (pendências bloqueantes restantes)

---

## Sessão 002.D1 — 18/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6, v2.1.143)
**Branch:** `feature/motor-002d-vocabulario`
**Objetivo:** Vocabulário tipado de exames + validação no carregamento — endereçar DT-002C-02

### O que foi feito

1. Sessão 002.D originalmente planejada como uma única; **dividida em D1–D4** pelo Arquiteto antes de iniciar, para respeitar a regra "1 implementação por sessão do Code". Sequência prevista: D1 (vocabulário), D2 (Stage 4 — `ctx.predicados`), D3 (Stage 2 — expansão de riscos), D4 (Stage 3 — pendências bloqueantes restantes).
2. `vocabulario/exames.yaml` populado com **5 slugs** (todos os atualmente referenciados por `regras.yaml`): `hemograma`, `glicemia`, `audiometria`, `acuidade_visual`, `ecg`. Cada um com `nome_exibicao`, `categoria` (clinico/ocupacional/laboratorial) e `fonte_matriz`. Demais exames da matriz da Dra. Patrícia entram conforme novas regras forem adicionadas.
3. `motor/protocolo.py` — função privada `_validar_exames_em_regras()` adicionada e chamada ao final de `carregar()`, antes do `return`. Toda referência `item["exame"]` em `regras.yaml` é validada contra os slugs declarados em `vocabulario/exames.yaml`. Slug inexistente → `ValueError` com mensagem contendo o slug, o id da regra e a lista de slugs disponíveis.
4. `motor/estagios/consolidacao.py` — `stage_8_consolidacao` agora deduplica por **slug canônico** (`norm = exame.exame`) em vez de string humana normalizada (`strip().lower()`). Docstring atualizada. Semântica mais estrita: `"hemograma"` ≠ `"hemograma_completo"` (mesmo humanamente parecidos), enquanto `"Hemograma"` e `"hemograma"` deixam de ser deduplicados (não é mais caso de uso real — vocabulário garante slug canônico desde a carga).
5. 5 testes novos em `agente_medico/tests/test_vocabulario.py`: carregamento do YAML, validação de metadados, referência válida em R-PKG-ATIVCRIT, falha quando regra referencia slug inexistente, aceitação de vocabulário vazio quando nenhuma regra emite exame.
6. `test_consolidacao.py` — `test_dedup_case_insensitive` substituído por dois testes que refletem a nova semântica: `test_dedup_slug_canonico` (slugs iguais mergem) e `test_dedup_slugs_diferentes_nao_mergem` (slugs distintos viram linhas distintas).

### Resultados

- **pytest** `agente_medico/tests/` → **62/62 verdes** (56 anteriores − 1 (teste antigo substituído) + 1 (substituído por dois) + 5 novos = 62)
- **pytest** suite global → **211 passed** (acima dos 209 anteriores)
- **mypy --strict** `agente_medico/` → `Success: no issues found in 18 source files`
- **DT-002C-02 RESOLVIDA** — identidade do exame deixou de ser string solta normalizada e passou a ser slug canônico validado no startup.

### Decisão de implementação registrada

**Identidade do exame = `str` validada na carga, não `Enum` nem `Literal`.**
Avaliadas 3 opções: (A) `Literal[...]` com slugs — typing estático forte, mas força edição de Python a cada exame novo; (B) `Enum` dinâmica construída a partir do YAML — typing parcial, custo de `# type: ignore[misc]` no construtor; (C) `str` validada em `carregar()` — sem magia, sem ignore, validação no startup. Escolhido C.

Justificativa: o sistema já carrega o protocolo no startup, então erro de slug inválido falha o boot exatamente como falharia com Enum dinâmica — sem custo adicional de typing. A "tipagem forte" de Enum dinâmica é ilusória (mypy também não consegue verificar slug existente em tempo de checagem). Custo aceito: ausência de autocomplete de slugs no IDE; o protocolo é YAML, então o slug já vive como string nessa camada.

Esta decisão **implementa** D-ARQ-12 (vocabulário tipado de primeira classe). Não a contradiz. Ver nota de implementação adicionada em D-ARQ-12.

### Gatilho de reavaliação registrado

Se o `vocabulario/exames.yaml` ultrapassar **~30 entradas** e a ausência de autocomplete começar a impactar a produtividade da equipe ou aumentar a taxa de typo em prompts/PRs, reavaliar a opção B (Enum dinâmica gerada do YAML) ou A (geração de stubs `.pyi` com `Literal`). Hoje (5 entradas) o trade-off é confortável.

### Problemas operacionais durante a sessão

**P-6. Project knowledge do Claude (claude.ai) com índice desatualizado.**
Ao retomar a 002.D, o Arquiteto não conseguiu enxergar via `project_knowledge_search` os arquivos novos das sessões 002.A/B/C (que estavam no GitHub conectado mas ainda não indexados). Resultado: o primeiro prompt cirúrgico foi escrito sobre suposição em vez de estado real. Detectado e corrigido em conversa antes do código ser tocado. Lição: nas próximas sessões, o Arquiteto sempre pede `git log --oneline -30` + leitura dos arquivos relevantes via comandos do PowerShell **antes** de escrever qualquer prompt, em vez de confiar no project knowledge.

**P-7. PowerShell sem `pytest` direto no PATH.**
Comando `pytest -q` falhou (`O termo 'pytest' não é reconhecido...`). Resolvido com `python -m pytest -q`. Lição: padronizar `python -m pytest` em todos os passos a passo futuros — funciona com pytest instalado globalmente ou em venv, com ou sem PATH ajustado.

**P-8. Pasta `Temp` do Windows com permissão corrompida.**
Testes que usam fixture `tmp_path` do pytest falhavam com `WinError 5: Acesso negado` em `C:\Users\Computador\AppData\Local\Temp\pytest-of-Computador`. Resolvido deletando a pasta via PowerShell Administrador. O mesmo procedimento limpou o `.pytest_cache` da raiz do projeto (que dava `Permission denied` em todo `git status`). Lição: futuros sintomas de permissão em pasta gerada por ferramenta (`Temp`, `.pytest_cache`, `.mypy_cache`) — primeira tentativa é deletar via Admin, não tentar `Remove-Item` no PowerShell normal.

**P-9. `.pyc` no `tests/__pycache__/` rastreados pelo git.**
2 arquivos `.pyc` apareceram como `modified:` antes do início da sessão (resquício pré-`.gitignore`). Resetados com `git checkout --` antes de começar. Lição: no início de toda sessão, conferir `git status` e tratar `modified:` em arquivos gerados (`__pycache__/`, `.pyc`) com `git checkout --` antes de tocar em código.

### Dívida técnica

Nenhuma nascida nesta sessão. **DT-002C-01** (audit trail incompleto — `Motivo.risco_origem=None`) continua aberta — será endereçada quando o problema se manifestar na UI ou em sessão dedicada de auditabilidade. **DT-002C-02 resolvida.**

### Lições aprendidas

- **Project knowledge não substitui leitura direta dos arquivos via terminal.** Quando o Arquiteto está numa janela do claude.ai e o usuário trabalha em outra máquina, a única fonte de verdade é o GitHub via comandos do usuário. Project knowledge é cache, com latência de indexação.
- **`python -m pytest` é portável; `pytest` direto não.** Mesmo padrão vale para `mypy`, `pip`, qualquer ferramenta instalável via pip.
- **Decisão de implementação ≠ decisão arquitetural.** Princípio (D-ARQ) é estável e raro de mudar; escolha técnica (str vs Enum) é local e revisitável. Documentar em camadas separadas evita inflar D-ARQs.
- **Dividir sessão em sub-sessões ANTES de começar** (002.D → D1/D2/D3/D4) custa segundos de planejamento e economiza horas de retrabalho. A regra "1 implementação por sessão" é mais importante que parece.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.D2)
**Branch:** `feature/motor-002d2-predicados-ctx` (a criar de main após merge da 002.D1)
**Objetivo:** Stage 4 — popular `ctx.predicados` antes do Stage 5 consumi-los. Hoje o Stage 5 chama `avaliar(regra["quando"], ctx, protocolo)` que computa predicados sob demanda; Stage 4 vai pré-computar e cachear no `ctx`, separando "computar predicado" de "consumir predicado". Pré-requisito da 002.D3 (Stage 2 hidrata `Risco` com metadados antes do Stage 4 computar predicados que dependem desses metadados).

---

## Sessão 002.D2 — 18/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6, v2.1.143)
**Branch:** `feature/motor-002d2-predicados-ctx`
**Objetivo:** Stage 4 — popular `ctx.predicados` + memoização do avaliador

### O que foi feito

1. `motor/predicados.py` — `avaliar_predicado` agora consulta `ctx.predicados[nome]` antes de computar; armazena após. Memoização atinge primitivos e compostos. Detecção de ciclo (`CicloPredicados`) preservada via parâmetro `_visitados` ortogonal ao cache.
2. `motor/estagios/predicados_stage.py` criado — `stage_4_predicados(ctx, protocolo) -> None` itera `protocolo.regras` chamando `avaliar(regra["quando"], ctx, protocolo)`. O efeito de cascata da memoização faz com que predicados transitivamente referenciados sejam populados sem código adicional.
3. `tests/test_predicados_stage.py` criado — 4 testes: populamento de primitivos referenciados, idempotência, predicado `Ausente` cacheado sem criar pendência (Stage 4 não conhece política de regra), economia de recomputação verificada com primitivo instrumentado via `monkeypatch.setitem`.
4. `tests/test_integracao_002c.py` atualizado — `stage_4_predicados` injetado entre `stage_1_gates` e `stage_5_emissao`. Resultado final do pipeline idêntico ao anterior. Assertions adicionais sobre `ctx.predicados`.
5. Commit único `22c41cf feat(motor): stage_4_predicados + memoização em avaliar_predicado (002.D2)` + amend de comentário apontando para este histórico.

### Resultados

- **pytest** `agente_medico/tests/` → **66/66 verdes** (62 anteriores + 4 novos)
- **pytest** suite global → **215 passed** (acima dos 211 anteriores)
- **mypy --strict** `agente_medico/` → `Success: no issues found in 20 source files`
- Nenhum teste existente quebrou com a introdução da memoização.

### Decisão de implementação registrada

**Cache de predicados preserva semântica de avaliação preguiçosa.** O avaliador de compostos faz short-circuit (`ou: [True, X, Y]` retorna sem avaliar X e Y); a memoização não desfaz isso. Consequência: após Stage 4, `ctx.predicados` contém apenas os predicados que o caminho de avaliação real percorreu — não um snapshot proposicional completo sobre o GHE.

Alternativa rejeitada: avaliar todos os primitivos sintaticamente referenciados nos compostos. Foi descartada porque (a) Stage 4 é cache para Stage 5, não auditoria; (b) força avaliação de primitivos que poderiam retornar `Ausente`, poluindo o cache com estado nunca consultado; (c) viola expectativa de qualquer operador lógico sério. Auditoria de "quais predicados foram avaliados" é responsabilidade de trace/relatório, não da forma do dicionário.

Nota de implementação adicionada em D-ARQ-10.

### Divergência de spec detectada e resolvida

O prompt original especificava assertions como `ctx.predicados["espaco_confinado"] is False` após Stage 4 com risco `trabalho_altura`. Isso colidia com o short-circuit do operador `ou`. O Code detectou a divergência, **parou antes de "ajeitar" silenciosamente**, implementou a versão correta e reportou as duas opções ao Arquiteto com diagnóstico técnico. Comportamento exemplar — o protocolo "bloqueador reportado pelo Code = decisão do Arquiteto" funcionou como desenhado.

### Problemas operacionais

**P-10. `Bash(Get-ChildItem ...)` falhou com `command not found`.** O tool `Bash` do Claude Code roda em git-bash, não PowerShell — comandos PowerShell-only não funcionam ali. O Code corrigiu sozinho usando `PowerShell(...)` na chamada seguinte. Lição: prompts futuros podem dizer explicitamente "comandos PowerShell vão via tool `PowerShell`, não `Bash`".

### Lições aprendidas

- **Revisar spec contra semântica do avaliador antes de escrever testes.** Eu (Arquiteto) escrevi assertions que assumiam avaliação eager e o Code pegou. Próximas specs de teste sobre predicados compostos: verificar se as assertions são coerentes com short-circuit antes de mandar.
- **`monkeypatch.setitem` é o padrão pra mexer em registros globais em teste.** Pytest restaura automaticamente; dispensa try/finally e é mais legível.
- **Tools do Code não são intercambiáveis.** `Bash` ≠ `PowerShell`. Vale documentar em prompts futuros.

### Dívida técnica

Nenhuma nascida nesta sessão. **DT-002C-01** (audit trail incompleto) continua aberta.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.D3)
**Branch:** `feature/motor-002d3-stage-riscos` (a criar de main após merge da 002.D2)
**Objetivo:** Stage 2 — expansão de riscos do `PGR.GHEPGR.riscos` (tipo `RiscoPGR`) para `ctx.riscos` (tipo `Risco`), hidratando com metadados de `vocabulario/agentes.yaml` (`anexo_nr07`, etc.). Hoje `ctx.riscos` é construído manualmente nos testes; após D3, sai do Stage 2. Pré-requisito do D4 (Stage 3 — pendências bloqueantes por dado essencial faltando).

---

## Sessão 002.D3 — 19/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6) + Claude (Arquiteto)
**Objetivo:** Stage 2 do motor — expansão de riscos do PGR para `ctx.riscos`, hidratando com metadados de `vocabulario/agentes.yaml` e expandindo com risco implícito por cargo (R-GHE-02) via `vocabulario/cargos.yaml`.

### O que foi feito

1. **Vocabulário mínimo populado:**
   - `agentes.yaml`: adicionados `fumos_metalicos`, `radiacao_uv_ir`, `trabalho_altura` com metadados clínicos aproximados (anexo NR-07, CAS, IARC, protocolos especiais)
   - `cargos.yaml`: adicionado `soldador` com `riscos_implicitos: [fumos_metalicos, radiacao_uv_ir]`
2. **Stage 2 implementado** em `agente_medico/motor/estagios/riscos.py`:
   - Fase A: hidrata `RiscoPGR` → `Risco` consultando `agentes.yaml`
   - Fase B: expande riscos implícitos do cargo via `cargos.yaml`
   - Dedup: mesmo agente vindo das duas fontes resulta em um único `Risco` (`fonte="explicito"` vence), com nota concatenada em `detalhe`
   - Vocabulário ausente em runtime gera `Pendencia` operacional (não-bloqueante)
3. **Testes:** 6 novos em `test_riscos_stage.py` + ajuste em `test_integracao_002c.py` (pipeline agora usa Stage 2 em vez de construir `Risco` manualmente)
4. **Higiene:** removidos do tracking dois `.pyc` residuais em `tests/__pycache__/` que escapavam do `.gitignore` antigo
5. Commits: `96d2de1` (vocabulário) + `a10dae0` (motor + testes) + `badb824` (higiene .pyc)
6. PR #17 mergeado em main (merge commit `ff8f715`)

### Resultados

- **Critério 1** — `python -m pytest agente_medico/tests/ tests/` → 221/221 verdes (215 base + 6 novos)
- **Critério 2** — `python -m mypy --strict agente_medico/motor/estagios/riscos.py` → no issues
- **Critério 3** — `python -m mypy --strict agente_medico/motor/` → regressão zero
- Stage 2 não toca disco, não chama LLM (D-ARQ-09 preservada)

### Decisões arquiteturais aplicadas

1. **Stage 2 muta `ctx`** (não retorna) — consistência com Stage 4
2. **`RiscoPGR.severidade` não migra para `Risco`** — protocolo da Dra. Carolini usa anexo NR-07 e quantificação relativa ao LT, não severidade do PGR
3. **Dedup explícito > implícito** — mesmo agente das duas fontes vira 1 `Risco` com `fonte="explicito"`, preservando `quantificacao` do PGR; informação do cargo implícito vai concatenada no `detalhe` para preservar audit trail
4. **Vocabulário ausente gera `Pendencia` operacional, não exceção nem persistência em disco** — promovida a D-ARQ-14 (ver `DECISOES_ARQUITETURAIS.md`)

### Problemas operacionais

**P-11. Branch D3 criada antes do merge da D2.** Diovanni criou `feature/motor-002d3-stage2-riscos` ainda na D2, antes do PR #16 ser mergeado. Resultado: branch local carregava commits da D2 + `.gitignore` staged + dois diffs documentais de teste não-commitados. Recuperação: `git stash` do gitignore, commit dos diffs documentais ainda na branch D2, push, PR D2 mergeado, cherry-pick do commit documental pra main, `.gitignore` aplicado em main, branch D3 antiga apagada (`git branch -D`) e recriada limpa a partir de main atualizada. Lição: **criar branch da próxima sessão SÓ depois do merge da sessão anterior em main**.

**P-12. `.pyc` antigos reaparecendo como modified mesmo após `.gitignore` cobrir o padrão.** Causa: arquivos já estavam trackeados de antes — `.gitignore` só impede *novos* arquivos, não desfaz tracking existente. Solução: `git rm --cached` nos `.pyc` específicos. Adicionado como commit de higiene `badb824`.

**P-13. Display do PowerShell mostrando caracteres UTF-8 quebrados.** `Get-Content arquivo.yaml` sem `-Encoding UTF8` mostra `Vocabulário` como `VocabulÃ¡rio`. Arquivos estão íntegros em disco — é só o display do PowerShell assumindo CP1252. Solução: sempre usar `-Encoding UTF8` quando o output tiver acentos.

**P-14. Confusão sobre "215 testes verdes".** Kickoff da sessão dizia 215, mas `pytest agente_medico/tests/` rodou 66. Hipótese confirmada: 215 = motor novo (66) + suite legada (149). Comando completo é `python -m pytest agente_medico/tests/ tests/`. Documentar isso evita repetir o susto.

### Lições aprendidas

- **Não criar branch da próxima sessão antes do merge da atual em main.** Custou 6 comandos de recuperação na D3.
- **`.gitignore` não desfaz tracking existente.** Para parar de trackear arquivo já trackeado: `git rm --cached <arquivo>`.
- **Vocabulário ausente em runtime é decisão recorrente.** Promovida a D-ARQ-14 para evitar relitígio em D4, D5, etc.
- **`-Encoding UTF8` no `Get-Content`** quando o output tiver acentos.

### Dívida técnica

**Nascida nesta sessão:**
- **DT-D3-02 — Granularidade de `fumos_metalicos` em agentes.yaml é aproximação.** Hoje é categoria única; granularidade fina por metal individual (Mn, Cr, Pb), cada com seu anexo NR-07, é tema de sessão CONHECIMENTO futura com Dra. Carolini. Registrada como pendência clínica em `PROTOCOLO_AGENTE_MEDICO.md`.

**Continuam abertas:**
- **DT-002C-01** — audit trail incompleto (fora de escopo desde 002.C)

### Próxima sessão planejada

**Tipo:** a definir (provável IMPLEMENTAÇÃO — integração Viverde)
**Objetivo:** primeiro teste end-to-end do motor contra a matriz RQ.61 Viverde (`tests/integracao/test_viverde.py`, previsto na 002.A, ainda inexistente). Valida o motor contra matriz real, não fixtures. Stage 6 (regime/ANAC) fica em fila atrás disso — só entra se o Viverde exercitar cargo aeronáutico.
**Pré-requisito:** orquestrador em main ✓ (D4)

---

## Sessão 002.D4 — 21/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code
**Branch:** `feature/motor-002d4-orquestrador`
**Objetivo final:** orquestrador `executar()` — encadeamento do pipeline

### Re-escopagem (Stage 3 → orquestrador)

A D4 entrou planejada como Stage 3 (pendências bloqueantes por predicado `Ausente`). Em sessão, a leitura do código real revelou duas coisas que mudaram o escopo:

1. **O tratamento `Ausente → Pendencia bloqueante` já existia no Stage 5** (`stage_5_emissao`, implementado na 002.C), com o flag `quando_ausente: false` lido lá — porque a política é por-regra. O Stage 4 (002.D2) documenta explicitamente que delega esse tratamento ao Stage 5. Implementar o Stage 3 como planejado duplicaria lógica viva e testada.
2. **Não existia orquestrador.** Os cinco estágios eram funções soltas — nada compunha o pipeline, fechava a matriz de GHE bloqueado ou definia `Resultado.status`. A segunda metade do objetivo da D4 ("a matriz não fecha, status cai para PRELIMINAR") dependia dessa peça inexistente.

Decisão do Arquiteto, autorizada pelo Diovanni: re-escopar a D4 para o orquestrador — a ponta que de fato travava a espinha dorsal. O Stage 3 (validação estrutural de dado essencial ausente, ex: produto químico sem composição via D-ARQ-08) foi **adiado para sessão CONHECIMENTO**, porque "que dado ausente bloqueia o GHE" é decisão clínica da Dra. Carolini, não de implementação.

### O que foi feito

1. `agente_medico/motor/orquestrador.py` — `executar(pgr, protocolo, hoje=None) -> Resultado` (D-ARQ-15). Gate bloqueante → REJEITADO imediato; loop por GHE (riscos → predicados → emissão → consolidação) fechando `MatrizGHE` com `linhas=[]` em GHE bloqueado; `ConflitoProtocolo` capturado por-GHE como `Pendencia` bloqueante; status global OK/PRELIMINAR. Pontos de extensão Stage 3 e Stage 6 marcados por comentário, sem stub.
2. `agente_medico/tests/test_orquestrador.py` — 8 testes (REJEITADO por assinatura e por validade, OK, predicado Ausente bloqueia GHE, `quando_ausente: false` não bloqueia, dois GHEs com um bloqueando, end-to-end trabalho_altura, ConflitoProtocolo vira pendência).

### Resultados

- **pytest** `agente_medico/tests/ tests/` — 229/229 verdes (221 anteriores + 8 novos)
- **mypy --strict** em `orquestrador.py` — Success: no issues found
- Commit único `0acf4bf`; merge via PR #18 (`a611ae7`)

### Decisão registrada

D-ARQ-15 (orquestrador + política de status). Gate bloqueante classificado como `REJEITADO` (não `PRELIMINAR`): PGR inadmissível na entrada não tem matriz preliminar a produzir.

### Dívida técnica

**Nascida nesta sessão:**
- **DT-D4-01 — Stage 3 (validação estrutural) adiado para sessão CONHECIMENTO.** Critério de "dado essencial ausente que bloqueia o GHE" é clínico (Dra. Carolini). Caso âncora a levar: produto químico sem composição resolvível (`ProdutoQuimico.fds is None`), já previsto em D-ARQ-08. Ponto de encaixe no orquestrador já demarcado.
- **DT-D4-02 — Stage 6 (regime/ANAC) ausente.** Próximo da espinha dorsal, atrás da integração Viverde. Ponto de encaixe já demarcado.

**Continuam abertas:**
- **DT-002C-01** — audit trail incompleto (fora de escopo desde 002.C)
- **DT-D3-02** — granularidade de `fumos_metalicos` (sessão CONHECIMENTO)

---

## Sessão 002.E — 21/05/2026 (arquitetura) + entrega defeituosa

**Tipo:** ARQUITETURA + IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code
**Branch:** `feature/motor-002e-exposicao-fisica` (mergeada — PR #19, commit `d8ad8f8`)
**Objetivo:** Arquétipo de exposição física (vibração + audiometria) sobre o motor

### O que foi feito

1. D-ARQ-16 formalizada: arquétipo de exposição física qualificável; subtipo de
   vibração via identidade de agente (3 slugs em `agentes.yaml`), não campo em
   `RiscoPGR`; regras componíveis com dedup no Stage 8 (R-GHE-03), nunca fusão.
2. Primitivo `vibracao_corpo_inteiro` (tri-estado: True / Ausente / False).
3. Regras de exposição em `regras.yaml`.

### Defeito entregue (corrigido na 002.F)

A leva 002.E implementou as regras de audiometria/ruído com **IDs inexistentes no
protocolo** e escopo infiel:

- `R-RUI-01` (`ruido_acima_acao` → audiometria `[adm, per]`, status A_VALIDAR) — ID
  inventado. O protocolo já tinha `R-AUD-01` (audiometria `[adm, per, MR]` por gatilho,
  VALIDADO) e `R-AUD-02` (demissional separado).
- `R-RUI-02` (`e[ruido, vibracao_corpo_inteiro]` → audiometria) — ID inventado e escopo
  estreito demais. O protocolo tem `R-VIB-02`: qualquer vibração dispara audiometria,
  **sem exigir ruído**.
- `R-AUD-02` não foi implementada.
- Momentos omitiram `MR` em ambas.

**Causa-raiz.** O Arquiteto construiu sobre a Matriz Dra. Patrícia (fonte item 3) e
resposta verbal, **sem ler `PROTOCOLO_AGENTE_MEDICO.md` (fonte item 1)**, que já tinha
as regras formalizadas e VALIDADAS — inclusive com os IDs estáveis corretos. R-VIB-01
(o único correto na leva) coincidiu por acaso. Sintoma revelador: R-RUI-01 entrou como
`A_VALIDAR` "a revalidar com a Dra. Carolini" — rebaixando para pendente uma regra que
já estava validada no protocolo.

**Lição (caso-âncora da regra de ouro).** Este é o custo empírico de pular o item 1 da
hierarquia de fontes. Um ID infiel não fica contido: mergeou em main e contaminou o
audit trail por `regra_id` de tudo a jusante, exigindo uma sessão inteira de
reconciliação (002.F) para corrigir. A regra de ouro — ler os docs vivos inteiros,
começando pelo protocolo, antes de formalizar ou codificar — não é cerimônia; é o que
teria evitado a 002.F por completo. IDs de regra são contrato: nunca inventados sem
confirmar ausência no protocolo.

---

## Sessão 002.F — 22/05/2026

**Tipo:** CONHECIMENTO/ARQUITETURA (reconciliação) + IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code
**Branch:** `feature/motor-002f-correcao-ids-audiometria` (mergeada — commit `8affedd`)
**Objetivo:** Corrigir os IDs/escopo infiéis da 002.E, reconciliando com o protocolo

### O que foi feito

1. Reconciliação do estado da 002.E contra `PROTOCOLO_AGENTE_MEDICO.md` (lido inteiro)
   e `DECISOES_ARQUITETURAIS.md` (git HEAD — cache do project knowledge estava stale,
   parava em D-ARQ-13 / 002.D1).
2. Correção cirúrgica (caminho A — sem reverter a 002.E; vocabulário, primitivos,
   R-VIB-01 e o corpo do D-ARQ-16 estavam corretos):
   - `R-RUI-01` → `R-AUD-01` (`ruido_acima_acao` → audiometria `[adm, per, MR]` 12M,
     VALIDADO).
   - `R-AUD-02` criada (`ruido_acima_acao` → audiometria `[dem]` 12M, VALIDADO).
   - `R-RUI-02` → `R-VIB-02` (`vibracao_corpo_inteiro` → audiometria `[adm, per, MR]`
     12M; deixa de exigir ruído).
   - Momentos corrigidos (incluem MR).
3. Testes da 002.E reescritos: renomes R-RUI→R-AUD/R-VIB, asserts de momentos,
   contagem de pendências (vibração genérica → 2 bloqueantes: R-VIB-01 + R-VIB-02) e de
   motivos (dedup altura+ruído → 3 motivos: R-PKG-ATIVCRIT + R-AUD-01 + R-AUD-02, com
   DEM no merge). Comentários de IDs em `test_integracao_002c.py` e
   `test_predicados_stage.py` atualizados.
4. D-ARQ-16: parágrafo "Aplicação na leva 002.E" reescrito com os IDs corretos; tabela
   de revisões → v9.

### Resultados

- **pytest** `agente_medico/tests/ tests/` — 242/242 verdes
- **mypy --strict** `agente_medico/motor/` — no issues found (11 arquivos)
- `git grep "R-RUI" -- agente_medico/` — zero ocorrências (trava objetiva do rename)

### Decisão de design relevante

R-AUD-01 e R-AUD-02 compartilham `quando: ruido_acima_acao` hoje, mas ficam **regras
separadas** (D-ARQ-16: uma regra por gatilho clínico, dedup resolve convergência).
Fundir destruiria o audit trail e a extensão futura — R-AUD-02 ganhará o branch
ruído+ototóxico+vibração quando `is_ototoxico` existir. R-AUD-01 e R-VIB-02 **não**
re-listam altura/confinado/máquina: esses já emitem audiometria via R-PKG-ATIVCRIT, e a
convergência é resolvida pela dedup (R-GHE-03), não por re-listagem. Guard-rail: toda
regra de audiometria tem de ser 12M, senão R-GHE-03 levanta ConflitoProtocolo e o
orquestrador (D-ARQ-15) derruba o GHE para PRELIMINAR.

### Dívida técnica

**DT-002F-01 — primitivo `ruido` puro sem consumidor.** Registrado em `predicados.py`,
mas nenhuma regra o referencia após a 002.F (`R-RUI-02` era o único uso — usava
`e[ruido, vibracao_corpo_inteiro]`). **Não remover:** é candidato a gatilho futuro
(ruído isolado abaixo da ação em combinação que o protocolo venha a formalizar).
Documentado para evitar remoção acidental como "código morto". Teste
`test_predicados_stage.py` agora afirma `"ruido" not in ctx.predicados` — coerente com
o cache preguiçoso de predicados (D-ARQ-10 / 002.D2).

### Escopo diferido (não é dívida da 002.F — falta de primitivo/flag)

- `is_ototoxico` em `agentes.yaml` + primitivo `ototoxico` — gatilho ototóxico de
  R-AUD-01 e branch ruído+ototóxico+vibração de R-AUD-02.
- primitivo `motorista_equipamento_pesado` — gatilho motorista de R-AUD-01.
- primitivo `vibracao_maos_bracos` — para R-VIB-02 cobrir "qualquer vibração".

### Próxima sessão planejada

A definir pelo Diovanni. Candidatos naturais: implementar os gatilhos diferidos acima
(ototóxico / motorista / vibração mãos-braços) ou retomar a sequência original do motor
(Stage 3 — pendências estruturais, demarcado em D-ARQ-15).

---

## Sessão 002.G — 23/05/2026

**Tipo:** CONHECIMENTO/ARQUITETURA → IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code (Sonnet 4.6)
**Branch:** `feature/motor-002g-gatilhos-motorista-vibracao` → PR #21 (merge commit `3533cd6`)
**Commit:** `163e004`
**Objetivo:** Completar dois dos três gatilhos diferidos do arquétipo de exposição física (D-ARQ-16): motorista de equipamento pesado e vibração mãos-braços. Ototóxico fica para 002.H.

### O que foi feito

1. `predicados.py` — dois primitivos novos:
   - `motorista_equipamento_pesado` — bi-estado True/False, lê slug de atividade em `ctx.riscos` (padrão de `altura`)
   - `vibracao_mao_braco` — tri-estado espelhando `vibracao_corpo_inteiro`: True (slug específico), `Ausente` (slug genérico `vibracao` presente — D-ARQ-13), False
2. `predicados_compostos.yaml` — composto `vibracao_qualquer: {ou: [vibracao_corpo_inteiro, vibracao_mao_braco]}`. Nome distinto do slug `vibracao` para evitar colisão.
3. `regras.yaml` — `quando` de duas regras:
   - R-AUD-01 → `{ou: [ruido_acima_acao, motorista_equipamento_pesado]}` (ototóxico segue diferido)
   - R-VIB-02 → `vibracao_qualquer`
   R-AUD-02 e R-VIB-01 intocados.
4. `agentes.yaml` — entrada `motorista_equipamento_pesado` (`tem_lt: false`, `protocolos_especiais: [R-AUD-01, R-VIS-01]`).
5. Testes — 12 novos (242 → 254): primitivos, composto via `avaliar`, e emissão de R-AUD-01 por motorista / R-VIB-02 por VMB.

### Resultados

- **pytest** `agente_medico/tests/ tests/` — 254/254 verdes
- **mypy --strict** `agente_medico/motor` — no issues (11 arquivos)

### Decisão de leitura registrada (gatilho de promoção D-ARQ-16 não dispara)

Os três diferidos foram avaliados contra o §"Gatilho de promoção" do D-ARQ-16 (promover subtipo a campo de `RiscoPGR` só com um *segundo* qualificador-tipo sem casa própria). Nenhum exige promoção: ototóxico tem casa (flag booleana por agente), motorista é slug de atividade, VMB completa a família de slugs de vibração já existente. Modelo por slug permanece — paliativo aceito em D-ARQ-16, sem mudança de tipo.

### Teste em risco verificado (não reescrito)

`test_rvib01_vibracao_generica_sem_emissao_com_pendencia_bloqueante` afirmava 2 pendências bloqueantes (R-VIB-01 + R-VIB-02). Com R-VIB-02 migrando para `vibracao_qualquer`, o slug genérico `vibracao` resolve `ou:[Ausente, Ausente]` → `Ausente` → bloqueante mantido. Contagem e `regra_origem` preservados. Confirmado que nenhum teste pré-existente foi reescrito — exatamente a aposta da 2ª passada do Arquiteto.

### Dívida técnica registrada

**DT-002G-01 (motorista nasce dormente).** O primitivo `motorista_equipamento_pesado` lê `ctx.riscos`, mas `cargos.yaml` não mapeia nenhum cargo (ex: "motorista", "operador") para esse slug. Em PGR real, o slug só chega se vier explícito no inventário — coisa rara. Logo o gatilho de R-AUD-01-por-motorista está implementado mas dormente até `cargos.yaml` ganhar o mapeamento cargo→slug. Não é bug: é crescimento append-only do vocabulário guiado por PGR (D-ARQ-14). Implicação: a validação Viverde não exercita esse caminho — não interpretar como regressão. Mapear cargos de motorista é trabalho de uma sessão de vocabulário, não da 002.G.

**DT-002G-02 (slugs de atividade fora do vocabulário — herdada).** `espaco_confinado` e `maquina_pesada` são lidos pelos primitivos homônimos, mas não existem em `agentes.yaml`. Hoje um PGR com esses riscos hidrata com defaults + `Pendencia(tipo="vocabulario_ausente", bloqueante=False)` (D-ARQ-14) — funciona, mas gera ruído de pendência. Pré-existente à 002.G (introduzida quando os primitivos foram criados na 002.B). Anotada aqui; correção é trivial (adicionar as entradas) mas fora de escopo desta sessão.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.H)
**Branch:** `feature/motor-002h-ototoxico` (a criar de main na hora)
**Objetivo:** Terceiro gatilho diferido — ototóxico. Campo `is_ototoxico: bool = False` em `Risco` (tipos.py); `riscos.py` preenche via `meta.get("is_ototoxico", False)`; 12 agentes ototóxicos novos em `agentes.yaml` (linha 82 da matriz Patrícia: tolueno, xileno, estireno, n-hexano, dissulfeto de carbono, tricloroetileno, monóxido de carbono, cianeto de hidrogênio, chumbo, mercúrio, arsênio, manganês); primitivo `ototoxico` (`any(r.is_ototoxico ...)`, bi-estado); R-AUD-01 ganha ototóxico no `ou`; R-AUD-02 ganha branch `{e: [ruido, ototoxico, vibracao_qualquer]}`. Toca tipos.py + riscos.py — daí ser sessão separada da 002.G.

---

## Sessão 002.H — 23/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code (Sonnet 4.6)
**Branch:** `feature/motor-002h-ototoxico` — commit `70292fb` (aguardando PR/merge)
**Objetivo:** Terceiro e último gatilho diferido do arquétipo de exposição física (D-ARQ-16): ototóxico. Com ele, o arquétipo fica completo.

### O que foi feito

1. `tipos.py` — `Risco` ganha `is_ototoxico: bool = False` (último campo; default não quebra construção posicional do frozen dataclass).
2. `riscos.py` — Fase A e Fase B propagam `is_ototoxico=meta.get("is_ototoxico", False)` no mesmo trilho de `anexo_nr07`. Ramos de default (agente ausente / replace de implícito) caem em `False` sem alteração.
3. `agentes.yaml` — 12 agentes ototóxicos (matriz Patrícia linha 82): tolueno, xileno, estireno, n_hexano, dissulfeto_de_carbono, tricloroetileno, monoxido_de_carbono, cianeto_de_hidrogenio, chumbo, mercurio, arsenio, manganes. Todos com `is_ototoxico: true`, demais campos em default.
4. `predicados.py` — primitivo `ototoxico` bi-estado: `any(r.is_ototoxico for r in ctx.riscos)`.
5. `regras.yaml` — `quando` de duas regras:
   - R-AUD-01 → `{ou: [ruido_acima_acao, motorista_equipamento_pesado, ototoxico]}`
   - R-AUD-02 → `{ou: [ruido_acima_acao, {e: [ruido, ototoxico, vibracao_qualquer]}]}`
   `base_normativa` de ambas reescrita (remove "diferido").
6. Testes — 6 novos (254 → 260): primitivo isolado, R-AUD-01 por ototóxico isolado, R-AUD-02 via branch composto (com guard `ruido_acima_acao is False` provando que o demissional veio do `e`, não do ruído), vibração genérica + ruído + ototóxico → bloqueante (D-ARQ-13), e integração via `executar()` com agente químico hidratado pelo Stage 2.

### Resultados

- **pytest** `agente_medico/tests/ tests/` — 260/260 verdes
- **mypy --strict** `agente_medico` — no issues found (25 arquivos)

### Regressão capturada pela suite completa (7º arquivo, fora do plano)

`test_predicados_stage.py::test_popula_primitivos_referenciados` quebrou: afirmava `"ruido" not in ctx.predicados`. A R-AUD-02 nova introduz `ruido` no branch `e`; no cenário do teste (altura+ruído sem quantificação), `ruido_acima_acao=False`, então o `ou` não curto-circuita, avança ao `e` e avalia+cacheia `ruido`. Asserção invertida para `"ruido" in ctx.predicados` com comentário explicativo referenciando D-ARQ-10. Correção validada pelo Arquiteto (não foi "ajeita aí" autônomo: a análise do Code foi conferida contra o avaliador antes de aceitar). É exatamente o tipo de regressão que rodar as duas suites existe para pegar — registro honesto de que a validação por-arquivo do primeiro turno teria deixado passar.

### Dívida técnica

**DT-002F-01 RESOLVIDA.** O primitivo `ruido` puro deixou de ser "sem consumidor": R-AUD-02 agora o referencia no branch `{e: [ruido, ototoxico, vibracao_qualquer]}`. Não é mais candidato a remoção como código morto. A DT-002F-01 (no histórico da 002.F) está encerrada por esta sessão.

**DT-002H-01 — metadata química pobre dos 12 ototóxicos.** Chumbo, manganês, mercúrio e arsênio entraram com `anexo_nr07: null`, `tem_lt: false`, `is_carcinogeno_iarc: false` — clinicamente falso (Mn é Anexo II e dispara R-BIO-03/R-CLI-03 no protocolo; As é IARC grupo 1). Paliativo aceito e **seguro hoje**: nenhuma regra em `regras.yaml` consome esses campos para esses agentes — só `is_ototoxico` é lido. Risco futuro: quando R-BIO-03/R-CLI-03 virarem regra do motor, vão confiar no vocabulário e subestimar silenciosamente. Antes de qualquer regra química tocar esses quatro agentes, enriquecer a metadata (anexo, LT, IARC, CAS). Append-only (D-ARQ-14). Mesmo padrão de pendência diferida da DT-002G-01.

### Gatilho de promoção D-ARQ-16 — não disparou (confirmação final)

Ototóxico tem casa própria (flag booleana por agente), igual aos outros dois diferidos. Nenhum dos três gatilhos do arquétipo exigiu promover subtipo a campo de `RiscoPGR`. O modelo por slug/flag permanece. Com a 002.H, **o arquétipo de exposição física está completo** e o gatilho de promoção nunca disparou ao longo de 002.E–002.H — registro de que o paliativo de D-ARQ-16 se sustentou.

### Próxima sessão planejada

A definir pelo Diovanni. O arquétipo de exposição física está fechado; candidatos naturais: retomar a sequência original do motor (Stage 3 — pendências estruturais, demarcado em D-ARQ-15), Stage 6 (regime regulatório), ou uma sessão de vocabulário (mapear cargos→slug de motorista, fechando DT-002G-01; ou enriquecer metadata química, fechando DT-002H-01). Pendência paralela fora do motor: confirmar estado da cascata de API gratuita da camada de extração (D-ARQ-09 — Gemini/Groq/OpenRouter), não verificada.

---

*Entradas futuras abaixo desta linha*
