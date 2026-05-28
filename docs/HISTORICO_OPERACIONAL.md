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

## Sessão 002.I — 23/05/2026

**Tipo:** ARQUITETURA (sem código)
**Participantes:** Diovanni Lisita + Claude (Arquiteto)
**Branch:** nenhuma (decisão arquitetural; implementação fica para 002.J)
**Objetivo:** Fechar o desenho de Stage 3 (pendências estruturais), demarcado em D-ARQ-15 entre Stage 2 e Stage 4.

### Decisão

D-ARQ-17 adicionada. Stage 3 existe como verificação de integridade do input por-GHE, centralizada, antes dos predicados. Âncora: R-PGR-04 (produto químico sem FDS resolvível → bloqueante por-GHE → PRELIMINAR). Contrato espelha `stage_2_riscos`: função pura `(ctx, proto) -> None`, muta só `ctx.pendencias`; não toca `tipos.py` (`Pendencia` já carrega `ghe_id`/`bloqueante`). Encaixa substituindo o comentário no orquestrador, sem reescrever a composição.

### 2ª passada do Arquiteto — 5 erros corrigidos antes do fechamento

1. Argumento da lacuna reescrito: a justificativa de Stage 3 é **centralização** da integridade de FDS (vs. obrigação tri-estado distribuída por primitivo), não um buraco em D-ARQ-13 — o desenho v1 afirmava erradamente que o predicado "retornaria False".
2. Removida a afirmação categórica "nenhum estágio lê `ProdutoQuimico.fds`" — `predicados.py`/stage_4-5-8 não foram lidos nesta sessão. Virou pré-requisito de verificação da 002.J.
3. Exemplo de `Pendencia` sem `motivo` (campo obrigatório) — corrigido.
4. Numeração: implementação é 002.J, não "002.I-impl".
5. `Componente.cas` é `str` não-Optional → checagem é string-vazia, não `is None`.

### Fora de escopo (registrado)

R-PGR-05 (PGR mal escrito) não vira Stage 3 v1 — limiar de genericidade é decisão clínica (DT-002I-01 no protocolo, sessão CONHECIMENTO futura).

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (Sessão 002.J)
**Objetivo:** Stage 3, só R-PGR-04, bloqueante por-GHE. Pré-requisito: confirmar via git show que nenhum estágio já lê `fds`. Confirmar numeração contra git log antes de nomear a branch (criada de main na hora).

---

## Sessão 002.J — 24/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code (Sonnet 4.6)
**Branch:** `feature/motor-002j-stage3-estrutural` — commit `e86ed77` → PR #24 (merge commit `6017b96`)
**Objetivo:** Stage 3 — pendências estruturais (R-PGR-04), demarcado em D-ARQ-15 e desenhado em D-ARQ-17. Implementação fechada na 002.I; esta sessão confirmou estado, validou não-duplicação e codificou.

### O que foi feito

1. **Pré-requisito de não-duplicação confirmado (escrito em D-ARQ-17):** `grep` por `fds`/`composic`/`produtos_quimic`/`ProdutoQuimico` em `agente_medico/motor` + `agente_medico/protocolo` retornou hits **apenas em `tipos.py`** (definição de `FDS`/`ProdutoQuimico`/`produtos_quimicos`) — zero consumo em `predicados.py`, `predicados_stage.py`, `emissao.py`, `regras.yaml` ou qualquer outro estágio. Stage 3 é o **primeiro e único consumidor** de `ProdutoQuimico.fds`. Gate limpo, sem bloqueador.
2. **NOVO `agente_medico/motor/estagios/pendencias_estruturais.py`** — `stage_3_pendencias_estruturais(ctx, proto) -> None`, função pura (D-ARQ-09), lê `ctx.pgr_ghe.produtos_quimicos`, muta só `ctx.pendencias`. Três sub-casos de R-PGR-04, todos `bloqueante=True`, `tipo="composicao_ausente"`, `destinatario="empresa"`, `regra_origem="R-PGR-04"`, `ghe_id=ctx.pgr_ghe.id`: (a) `fds is None`; (b) `fds.composicao` vazia; (c) componente com `cas.strip()` vazio (uma pendência por componente sem CAS). `proto` na assinatura por simetria com os demais estágios — não consultado.
3. **EDITADO `orquestrador.py`** — import alfabético (entre `gates` e `predicados_stage`); comentário `# Stage 3 (...) encaixará aqui` substituído por `stage_3_pendencias_estruturais(ctx, protocolo)`. Nada mais na composição mudou. `tipos.py` intocado (`Pendencia` já carregava `ghe_id`/`bloqueante`).
4. **9 testes** em `test_stage_3_pendencias_estruturais.py` cobrindo os casos 1–8 da spec (3 = `cas=""` + `cas="   "`), incluindo integração via `executar()` (PRELIMINAR, `linhas=[]`, pendência R-PGR-04) e universalidade fora de construção (óxido de etileno / GHE de saúde — prova que o predicado é sobre `ProdutoQuimico`, não sobre cargo, D-ARQ-06).

### Resultados

- **pytest** `agente_medico/tests/ tests/` — **269/269 verdes** (260 anteriores + 9 novos; as duas suites)
- **mypy --strict** `agente_medico` — `Success: no issues found in 27 source files`
- **Regressão:** nenhuma. Todos os GHEs pré-existentes das duas suites usam `produtos_quimicos=()` — verificado pelo Code *antes* de implementar, materializando a checagem que a 2ª passada do prompt previu.

### Não-short-circuit verificado (não só pretendido)

D-ARQ-17 exige que Stage 4/5 rodem após o bloqueio (acúmulo num passe, não early-return). O teste de integração roda `executar()` com protocolo vazio e GHE bloqueado por R-PGR-04 sem estourar: Stage 4/5 atravessam (sem regras → sem exames), e o ramo `if any(p.bloqueante ...)` pós-emissão fecha `linhas=[]`. O trilho PRELIMINAR do orquestrador (D-ARQ-08/D-ARQ-15) absorveu o bloqueio sem qualquer alteração — Stage 3 só precisou mutar `ctx.pendencias`.

### Dívida técnica

Nenhuma nascida nesta sessão. **Continuam abertas:** DT-002C-01 (audit trail incompleto), DT-D3-02 (granularidade de `fumos_metalicos` — sessão CONHECIMENTO), DT-002G-01 (motorista dormente), DT-002G-02 (slugs de atividade fora do vocabulário), DT-002H-01 (metadata química pobre dos ototóxicos), DT-002I-01 (limiar de genericidade de R-PGR-05 — sessão CONHECIMENTO). DT-D4-01 (Stage 3 adiado) **encerrada** — Stage 3 implementado nesta sessão.

### Categoria Stage 3 aberta para crescimento append-only

D-ARQ-17 prevê novos checks estruturais (PGR sem GHE, GHE sem cargo, unidade de quantificação inválida) entrando em `pendencias_estruturais.py` sem novo estágio. Nenhum implementado nesta sessão — só R-PGR-04. Os demais entram quando houver caso de uso ou regra clínica que os exija.

### Próxima sessão planejada

A definir pelo Diovanni. Candidatos naturais: Stage 6 (regime regulatório / ANAC — D-ARQ-04, ponto de encaixe demarcado no orquestrador), integração Viverde end-to-end (`tests/integracao/test_viverde.py`, previsto desde a 002.A e ainda inexistente), ou sessão de vocabulário (fechar DT-002G-01 mapeando cargos→slug de motorista; ou DT-002H-01 enriquecendo metadata química). Pendência paralela fora do motor: estado da cascata de API gratuita da camada de extração (D-ARQ-09), não verificada desde a 002.

---

## Sessão 002.K — 24/05/2026

**Tipo:** ARQUITETURA (auditoria da camada de dados Viverde + estratégia de validação end-to-end)
**Participantes:** Diovanni Lisita + Claude (Arquiteto)
**Branch:** `docs/fechamento-002k` (commit de docs; sem branch de motor — sessão de arquitetura pura)
**Objetivo:** auditar o que existe na camada de dados Viverde/legado, decidir a estratégia de comparação motor↔gabarito, e documentar a camada que vivia fora dos docs vivos. Saída: D-ARQ-18 + esta entrada. Sem código de motor.

### Camada de dados "sessao2" — ponto cego fechado

Existia uma camada de dados Viverde/legado, datada de 17/05/2026 (tag de commit "feat(sessao2)"), **nunca documentada em doc vivo**. Inventário e destino de cada parte:

- **`scripts/migrar_pdf_rq61.py`** — parser regex do PDF da RQ.61 → `banco_ghe_cargo_v1.json`. **Legado.** Será substituído pela re-extração do `.docx` na 002.L. **Bug conhecido (ver abaixo), não corrigido por decisão.**
- **`scripts/migrar_matrizes_pdf.py`, `scripts/migrar_riscos_excel.py`** — migradores alimentados pela Matriz Patrícia (`.xlsx`). Paradigma legado (lookup), não tocam o motor novo.
- **`data/banco_ghe_cargo_v1.json`** — 57 chaves `GHE:cargo`, 31 GHEs. Extração lossy da RQ.61. **Legado — aposentado como gabarito (D-ARQ-18).**
- **`data/banco_matrizes_v1_1.json`, `banco_matrizes_v2.json`, `banco_riscos_nr7.json`** — bancos do motor legado (Streamlit, `modules/agente_medico_ia.py`). Não alimentam o motor novo.
- **`data/dicionario_cas.py`, `sinonimos_quimicos.json`** — **candidatos** a enriquecer `agentes.yaml` (a verificar no estudo cruzado; não decidido).
- **`data/mapa_cbo_cargo.json`, `cargos_desconhecidos.json`, `matriz_exames.py`** — legado. `cargos_desconhecidos.json` é o padrão de persistência que D-ARQ-14 **rejeitou** para o motor novo — confirma que `data/` é legado.

**Conclusão:** `data/` + os 3 `scripts/` são legado. Não alimentam o motor nem a validação. Ponto cego documental fechado.

### Auditoria do banco contra o PDF da RQ.61 (Viverde Areião)

Confronto do `banco_ghe_cargo_v1.json` contra `matrizes_originais/MATRIZ DE EXAMES(ATUALIZAÇÃO)CMO VIVERDE AREIAO 06.03.2025.pdf` (15 págs, lido inteiro, tabela limpa). Achados detalhados em D-ARQ-18. Síntese:

- **Cobertura parcial:** o PDF tem três blocos com numeração reutilizada (Estrutura 01–16, Acabamento 01–09, Administração 01–06); o banco perdeu funções inteiras (meios-oficiais, encarregados, vigia, etc.).
- **17 linhas-fantasma** (exame com todos os momentos `False`): todas são exames "(P)" = só Periódico que o parser não soube ler. Bug de notação, não diferenciação clínica. Recuperáveis, mas defeito que o original não tem.
- **Divergências intra-GHE do banco** eram artefato das fantasmas; no PDF os cargos do mesmo GHE batem (consistente com R-GHE-01) nos casos checados.
- **Divergência inter-GHE real e fiel ao PDF:** pintor Estrutura (4 exames, sem químico) ≠ pintor Acabamento (10 exames, com pacote benzeno). Inventários diferentes por GHE — o banco acertou.

### Bug conhecido não corrigido (decisão do Arquiteto)

`migrar_pdf_rq61.py` é cego à notação "(P)" da RQ.61 (biomonitoramento só-periódico), gravando esses exames com todos os momentos `False`. **Não será corrigido:** o script é legado e será substituído pela re-extração do `.docx` na 002.L. Corrigi-lo é trabalho jogado fora. Registrado aqui para um próximo chat não reinvestigar o mesmo defeito como se fosse novo.

### Autoria clínica da RQ.61 — esclarecido

O PDF mostra duas médicas: Dra. Patrícia Montalvo Moraes (cabeçalho, coordenadora) e Dra. Carolini Polesso (rodapé, validação). Esclarecido pelo Diovanni: **a validação clínica de todo o conteúdo é da Dra. Carolini; a Dra. Patrícia, como coordenadora, assina os documentos validados pela Carolini.** Não há duas fontes clínicas divergentes — a RQ.61 é conduta da Carolini. Consequência arquitetural na cláusula 4 de D-ARQ-18 (política de divergência: bug OU lacuna, nunca "fonte divergente").

### Inventário de matrizes e PCMSOs (`matrizes_originais/`)

Levantado para dimensionar o estudo cruzado. 7 matrizes, 5 PCMSOs:

- **Pares completos (matriz + PCMSO) — 4:** Viverde Areião, CMO Construtora ADM, Vistamerica, GPL-R78 / Naturia (mesma obra, nome variando entre os dois arquivos).
- **Matrizes órfãs (sem PCMSO):** Dinâmica Engenharia (`.doc`, 07.01.26), Seconci Goiás (`.doc`, 20.03.26).
- **PCMSO órfão (sem matriz):** Ricco Construtora (`.docx`).
- **Também presentes:** `Matriz função-risco-exames - validado Dra. Patrícia 06.2025.xlsx` (Matriz Patrícia — item 3 da hierarquia, template genérico, distinto das RQ.61 por-obra; é o `.xlsx` anexado ao project knowledge); PGR Viverde V02 em `.pdf` **e `.docx`** (o `.docx`, 01/05/2026, é o insumo da 002.L — leitura por tabela).

O estudo do método roda nos **4 pares completos**; órfãs entram como reforço (matriz-só confirma repetição de resultado; PCMSO-só ativa quando surgir matriz).

### Decisões (D-ARQ-18)

Gabarito = RQ.61 PDF/DOCX, não o banco. Granularidade por-GHE (R-GHE-01 a verificar contra o PDF na 002.M). Mapa nome↔slug na fixture. Política de divergência motor↔PDF = bug OU lacuna. Estratégia de validação do método = estudo cruzado multi-matriz (proposta do Diovanni, adotada como oficial).

### Mapa da fase corrigido

O kickoff modelava K→L→M. A 002.K revelou um passo faltante: divergências motor↔PDF podem ser lacunas clínicas (não-bugs) que precisam da Carolini antes de virarem asserção de teste. Fase corrigida:

**K (estratégia) → estudo cruzado das 4 matrizes [CONHECIMENTO, nova] → L (estruturar PGR Viverde) → M (test_viverde.py).**

### Dívida técnica / clínica

- **Novas (clínicas, sessão CONHECIMENTO):** DT-002K-01 (gatilho de RX 24M ausente em R-RX-01), DT-002K-02 (serralheiro e pacote de fumos metálicos). Ambas no protocolo, ambas alimentam o estudo cruzado.
- **Continuam abertas:** DT-002C-01, DT-D3-02, DT-002G-01, DT-002G-02, DT-002H-01, DT-002I-01.
- **Bug legado registrado (não-dívida do motor):** cegueira de `migrar_pdf_rq61.py` à notação "P" — não corrigido por decisão (script legado, será substituído).

### Próxima sessão planejada

**Tipo:** CONHECIMENTO — estudo cruzado das 4 matrizes + PCMSOs (Viverde, CMO, Vistamerica, R78).
**Objetivo:** separar regra-por-cargo de regra-por-agente-químico, com foco inicial em DT-002K-01 (RX 24M) e DT-002K-02 (serralheiro/fumos). Por divergência, buscar o método (o gatilho universal), não o resultado por empresa.
**Primeira ação:** cruzar a conduta do serralheiro e do RX 24M entre as 4 matrizes; onde divergir, abrir o PCMSO da obra para checar o agente químico declarado (hipótese do Diovanni: o produto da FDS dispara a periodicidade). Material para levar à Dra. Carolini ao fim do estudo.
**Pré-requisito:** confirmar se há matrizes/PCMSOs além de `matrizes_originais/` (o Diovanni mencionou ter mais salvas localmente).

---

## Sessão 002.L-estudo — 25/05/2026

**Tipo:** CONHECIMENTO
**Participantes:** Diovanni Lisita + Dra. Carolini Polesso (assíncrona, com fundamentação normativa) + Claude (Arquiteto)
**Objetivo:** Extrair o método da Dra. Carolini para DT-002K-01 (RX 24M) e DT-002K-02 (serralheiro/fumos), via estudo cruzado das matrizes.

### O que foi feito

1. Releitura do protocolo (item 1) e da Matriz Patrícia (item 3). Achado de estado: project knowledge defasado (protocolo v2, D-ARQ até 13) — confirmado contra git real (HEAD 4dbec6d, último D-ARQ-18, R-GHE até 04). Git venceu o cache, como previsto.
2. A Matriz Patrícia mostrou RX OIT só em 12M/60M e 24M pertencendo à espirometria — gerou hipótese (parcial) de que o RX-24M da RQ.61 fosse artefato.
3. A Dra. Carolini respondeu com fundamentação no Anexo III da NR-07 (Portaria 567/2022), o que **dispensou o cruzamento das 4 matrizes** para extração do método. Cruzamento ficou como auditoria opcional, não executada.

### Resultados (método extraído)

- **DT-002K-02 (serralheiro) — RESOLVIDA, hipótese do Arquiteto revertida.** Não há risco por denominação de cargo (NR-01/NR-07). Risco implícito (R-GHE-02) só vale quando a operação é a atividade-fim (soldador industrial); serralheiro de obra = solda contingente → confirmação documental. Formalizado: R-GHE-02 refinada + R-GHE-05 nova. Caso Viverde confirmou a via-agente (cromo medido <10% LT ACGIH, GHE 10).
- **DT-002K-01 (RX 24M) — RESOLVIDA.** Existe RX 24M legítimo: sílica/asbesto **sem avaliação quantitativa** (adm + 24M até 15 anos). Banda ausente na Patrícia e em R-RX-01 v2. R-RX-01 refinada com a tabela completa do Anexo III. A v2 (A-VAL-06) simplificou demais.
- **D-ARQ-19 nova:** periodicidade dependente de tempo de exposição acumulado (corte 15 anos) é do agendador, não do motor.

### Lições

- Quando a especialista fundamenta na norma, a fonte (item 1 + item 2) dispensa o cruzamento empírico (item 3/4). O cruzamento serve para o que a norma não decide.
- Hipótese de Arquiteto não é método: a R1 da Carolini reverteu "serralheiro = cargo-de-solda". Buscar o método via fonte, não inferir do padrão das matrizes.

### Dívidas / pré-requisitos registrados

- **Pré-requisito da 002.M:** auditar a RQ.61 Viverde antes de `test_viverde.py` — o gabarito pode conter PNOS-24M errado (correto 60M) e pintor-RX-24M (confusão com espirometria). Não validar contra valor errado. Toca D-ARQ-18 (RQ.61 vira gabarito após correção).
- **TODO normativo (R-RX-01):** conferir faixas/anos do Anexo III contra a redação literal da Portaria 567/2022 antes de codar.
- **DT-D3-02 (granularidade de `fumos_metalicos`):** ganha relevância — Cr⁶⁺ em soldagem de inox é o caso concreto. Não resolvida aqui.
- **`matrizes_originais/` (~35 arquivos untracked):** decidir destino (commitar como dado de auditoria vs. `.gitignore`). Não resolvido nesta sessão.

### Próxima sessão planejada

**Tipo:** IMPLEMENTAÇÃO (002.M) — `test_viverde.py`, precedida da auditoria da RQ.61 (pré-requisito acima).

---

## Sessão 002.L0 — 25/05/2026

**Tipo:** IMPLEMENTAÇÃO (motor)
**Participantes:** Diovanni Lisita + Claude (Arquiteto) + Claude Code (Sonnet)
**Branch:** `feature/motor-002l0-rx-periodicidade-condicional`
**Objetivo:** Implementar R-RX-01 refinada (periodicidade condicional de RX) destravando a 002.L (estruturar PGR Viverde).

### Contexto / por que esta sessão existe

A 002.M (test_viverde) estava bloqueada: o PGR Viverde estruturado não existe (só PDF/DOCX crus). E a 002.L (estruturar PGR) esbarrava em duas lacunas de tipo que a 002.L-estudo deixou só no papel: (1) `Quantificacao` não representava "sem avaliação quantitativa" (gatilho do RX 24M); (2) o motor não suportava periodicidade dependente de quantificação. A 002.L0 resolve as duas antes de estruturar qualquer PGR. Sequência revisada: **002.L0 → 002.L (estruturar PGR) → 002.M (test_viverde)**.

### Decisões de arquitetura tomadas

- **D-ARQ-20:** periodicidade condicional via família de regras por faixa (Caminho B), sem estender o schema de regra. Motor intocado; condicionalidade em primitivos+compostos (D-ARQ-10).
- **D-ARQ-19 refinado:** encurtamento de 15 anos como segundo valor `periodicidade_apos_15a` no `ExameEmitido`; gatilho temporal no `Motivo`, não no schema.
- **Estado contraditório → pendência, não precedência.** Avaliada e rejeitada a opção de `sem_avaliacao` ter precedência sobre `pct_LT` — seria formalizar regra clínica não-validada. Input contraditório vira `Ausente` bloqueante (D-ARQ-08/13).

### O que foi entregue

- `Quantificacao.sem_avaliacao_quantitativa` + `ExameEmitido.periodicidade_apos_15a`.
- 3 agentes novos (`silica`, `asbesto`, `poeira_nao_classificada`), slug `rx_torax_oit`.
- 7 primitivos de faixa + helper `_helper_silica_asbesto` (5 ramos; estado contraditório → Ausente).
- Família `R-RX-01-*` (6 regras) + R-RX-02 executável.
- Stage 8 compara `periodicidade_apos_15a` no conflito/merge.
- `test_rx_periodicidade.py`: 15 testes (roteamento, Ausente, exclusividade de fronteiras, contraditório, Stage 8).
- **284 testes verdes / mypy --strict limpo** (era 269).

### Dívidas registradas (não resolvidas nesta sessão)

- **DT-D3-02 ganha corpo:** `anexo_nr07: null` em `manganes` e `fumos_metalicos` no `agentes.yaml` — inconsistente com Mn=Anexo II e Cr⁶⁺=Anexo I. Os agentes novos (sílica/asbesto) entraram com Anexo I correto; os antigos ficaram como estavam (fora de escopo da L0).
- **Valores a-conferir (opção B):** periodicidades e limiares de %LEO em `regras.yaml` + `predicados.py` (`_PCT_LEO_*`) são transcrição da Carolini, não verbatim do Anexo III. `test_rx_periodicidade.py` crava os valores literais nas asserções de roteamento (âncora-comentário no topo do arquivo). Ao conferir a Portaria 567/2022: atualizar regras.yaml + predicados.py + asserções do teste juntos.
- **Cópias mortas na raiz:** existem `DECISOES_ARQUITETURAIS.md` e `HISTORICO_OPERACIONAL.md` na raiz do repo (formato antigo `ADR-NNN`), divergentes dos vivos em `docs/`. São fósseis de 15/05 que nunca foram removidos e já causaram confusão de leitura. Limpeza dedicada futura (`git rm` das cópias da raiz após confirmar que nada as referencia).
- **`matrizes_originais/` (~35 untracked):** destino indefinido (corpus de auditoria multi-setor vs. `.gitignore`), com triagem de PII obrigatória antes de qualquer `git add`. Destaques: Engeseg Metalúrgica (soldador atividade-fim puro) e Fazenda Jamaica/JBJ (primeiro PGR não-construção, validação D-ARQ-06).

### Próxima sessão planejada (registrada na 002.K0/L0 — agora executada, ver abaixo)
Tipo: IMPLEMENTAÇÃO (dados/fixture) — 002.L: estruturar PGR Viverde. **Executada em 25/05/2026 — virou CONHECIMENTO+ARQUITETURA (ver entrada da sessão abaixo).**

---

## Sessão 002.L — 25/05/2026

**Tipo:** CONHECIMENTO + ARQUITETURA (planejada como IMPLEMENTAÇÃO; mudou de natureza no meio)
**Participantes:** Diovanni + Claude (Arquiteto, Chat)
**Branch:** docs/fechamento-002l-mapa-ghe
**Objetivo planejado:** estruturar o PGR Viverde no schema do motor (fixture).
**Objetivo real entregue:** mapa de GHE do Viverde + decisão arquitetural sobre agrupamento. O fixture Python foi adiado para a 002.L-fixture.

### Por que mudou de natureza

Ao estruturar o PGR, o Diovanni apontou que o **agrupamento em GHE varia por elaborador**: a CMO (PGR Viverde) separa o pedreiro em 6 GHEs por atividade; outras empresas agrupam num único GHE "pedreiro". Isso levantou a dúvida de se o motor deve respeitar o agrupamento do PGR ou re-agrupar por critério próprio. A dúvida é arquitetural e precedia qualquer fixture — estruturar o Viverde "como veio" antes de resolvê-la seria construir sobre premissa não-validada. A sessão passou de transcrição para decisão de design.

### Decisão de arquitetura

**D-ARQ-21** (registrada em DECISOES_ARQUITETURAIS.md): o agrupamento em GHE é canônico; o motor respeita o GHE do PGR, não re-agrupa. Base: a Dra. Carolini respeita o agrupamento do PGR recebido (Hipótese A, confirmada pelo Diovanni). Consequência: a mesma obra modelada por dois elaboradores produz matrizes diferentes, e isso é correto — fidelidade ao PGR vence consistência inter-PGR. Estende R-GHE-04 (inventário canônico) ao agrupamento.

### O que foi entregue

- **docs/MAPA_GHE_VIVERDE.md** (novo): transcrição fiel dos ~28 GHEs declarados pela CMO (16 Estrutura + 9 Acabamento + 6 Administração + 1 Fundação-pendência), com cargos, riscos, quantificações e EPIs de cada um. É a spec da 002.L-fixture.
- **DT-002L-01** (PROTOCOLO): conversão mg/m³ → %LEO para rotear faixa de RX — pergunta de método para a Carolini.

### Achados do PGR Viverde (dívidas herdadas pela 002.M)

- **Serralheiro = Dióxido de Titânio, não cromo/Mn.** O PGR mede TiO₂ (0,008 mg/m³) na solda; a nota da RQ.61 dizia "Cromo <10% LT". Divergência PGR↔RQ.61 (D-ARQ-18) a resolver na 002.M. O pacote-soldador não é disparado pelo agente declarado neste PGR.
- **Sílica sempre em mg/m³** (4 ocorrências, 0,005–0,0071), nunca em %LEO → DT-002L-01.
- **Fundação sem inventário de risco** (op. retroescavadeira/escavadeira/motorista/perfuratriz na matriz cargo×tarefa, sem bloco ET próprio) → pendência R-PGR-04 no fixture (GHE com riscos vazios).
- **Gás e marceneiro** citados na matriz, sem bloco de risco — confirmar na 002.L-fixture se é lacuna ou absorção por outro GHE.
- **Ruído "aguardando medição"** em Adm-03 (ADC12) → pendência de medição.
- **Numeração de GHE da CMO tem saltos/repetições** — preservados nome e cargos declarados; id estável no fixture, nome = SETOR/FUNÇÃO da CMO.

### Próxima sessão planejada

**002.L-fixture — IMPLEMENTAÇÃO (dados):** transcrever o MAPA_GHE_VIVERDE.md validado para fixture Python (instanciando os dataclasses do motor, sem loader novo — não há conftest/fixtures no projeto). Aparece a cascata de vocabulário: popular cargos.yaml (~29 cargos do Viverde) e agentes.yaml (~13 agentes: metil_etil_cetona, etanol, estireno, dioxido_de_titanio, monoxido_de_carbono, cloreto_de_hidrogenio, etc.). Serralheiro entra sem riscos_implicitos de solda (R-GHE-05). Pré-requisito da 002.M (test_viverde).

---

## Sessao 002.L1 (parte 1 — vocabulario) — 25/05/2026

**Tipo:** IMPLEMENTACAO (dados/vocabulario)
**Branch:** feature/motor-002l1-fixture-viverde (NAO mergeada — continua na parte 2)
**Objetivo:** preparar vocabulario + fixture do PGR Viverde. Parte 1 (vocabulario)
concluida; parte 2 (fixture Python) segue em chat novo, mesma branch.

### Entregue (3 commits, suite 284 verde, sem regressao)

- b9d8368 — 5 agentes quimicos: etanol, metil_etil_cetona, cloreto_de_hidrogenio
  (Anexo 11, cadastraveis); dioxido_de_titanio e propanediamina_tridecyloxy ([A VALIDAR]).
- 49272fb — 43 cargos, TODOS magros (riscos_implicitos: [], pacotes_aplicaveis: []),
  por R-GHE-05 + D-ARQ-21 (risco vem do PGR, nao da denominacao). Ajustou 2 testes
  que documentavam ausencia de cargo (test_integracao_002c usa __NAO_EXISTE__).
- 0e89468 — 5 agentes de exposicao: ruido, espaco_confinado, eletricidade, umidade,
  microrganismos. ruido e espaco_confinado ja eram predicados primitivos orfaos
  (faltava o slug no vocabulario); ruido destrava a cadeia de audiometria (R-AUD-01/02).

### Decisao de design (registrar)

**Cargos entram magros por padrao.** Exame vem do risco inventariado no PGR, nao de
pacote colado ao nome do cargo. Unica excecao e soldador (legado), cuja atividade-fim
e indissociavel do risco (R-GHE-02). Aplicacao de R-GHE-05 a todo o vocabulario de cargos.

### Decisoes de MODELAGEM do fixture (travadas nesta sessao, valem para a parte 2)

1. **Cargos:** meio-oficial = slug proprio (meio_oficial_<cargo>); servente = slug
   unico; operadores = operador_<maquina>; estagiario/encarregado = slug unico.
2. **EPIs:** texto livre fiel ao PGR (ex: "protetor auditivo NRRsf>=15"), sem
   vocabulario de EPI. Motor nao consome epis para decidir exame.
3. **Quimico medido = RiscoPGR** (tipo="quimico", agente=slug, quantificacao=...),
   NAO ProdutoQuimico. produtos_quimicos=() em todos os GHEs (Viverde nao tem FDS
   de produto comercial estruturada).
4. **Arquivo:** agente_medico/tests/fixtures/pgr_viverde.py (pasta nova), funcao
   unica build_pgr_viverde() -> PGR, GHE a GHE, legivel. Sem conftest (nao existe no projeto).
5. **RUIDO classificado no fixture** (criterio normativo firme NR-15: nivel de acao
   80 dB(A), LT 85). Mapeamento relacao_LT: <80 = "abaixo_acao"; 80-85 = "entre_acao_LT";
   >85 = "acima_LT". O predicado ruido_acima_acao le relacao_LT (string), NAO o dB(A).
   Valores por GHE: betoneira 89,6 / bancada 89,3 / serralheria 88,7 = acima_LT;
   hidro 83,3 / prumada 82,8 / carpintaria 82,2 = entre_acao_LT; demais <80 = abaixo_acao.
   EXCECAO: Adm-03 (mestre de obra) ruido "aguardando medicao" → relacao_LT=None +
   apenas_qualitativa=True → Ausente → pendencia bloqueante (fiel ao PGR).
6. **SILICA permanece pendente** (DT-002L-01): valor mg/m3 + unidade, mas pct_LT=None
   e sem_avaliacao_quantitativa=FALSE (tem medicao, falta conversao mg/m3->%LEO).
   NAO usar sem_avaliacao_quantitativa=True (seria estado contraditorio — fix 85ef43b da 002.L0).
   Diferenca para o ruido: silica tem criterio ambiguo (%quartzo, fonte de LEO) → pendencia;
   ruido tem criterio firme (80/85) → classificado.
7. **Ergonomico e acidente FORA do vocabulario de proposito:** esforco_fisico,
   movimento_repetitivo, queda entram no fixture como RiscoPGR mas SEM slug cadastrado
   → Stage 2 gera pendencia "vocabulario_ausente" nao-bloqueante = sinal "fora de escopo
   de exame do agente medico" (decisao ii). Cadastra-los mataria a sinalizacao.
8. **radiacao nao-ionizante (solda) reusa o slug existente radiacao_uv_ir** (do soldador) —
   nao criar slug duplicado.
9. **Fundacao:** GHE-FUN com riscos=() (op. retroescavadeira/escavadeira/motorista/
   perfuratriz na matriz cargo×tarefa, sem bloco de risco no PGR) → pendencia estrutural R-PGR-04.

### Proxima sessao

**002.L1 parte 2 (fixture) — chat novo, mesma branch feature/motor-002l1-fixture-viverde.**
Construir agente_medico/tests/fixtures/pgr_viverde.py a partir de docs/MAPA_GHE_VIVERDE.md
(fonte) aplicando as 9 decisoes acima, em 3 blocos (Estrutura / Acabamento / Admin+Fundacao)
+ teste minimo de Stage 1 aceitar o PGR. Depois: 002.M (test_viverde.py).
Dividas herdadas do MAPA: serralheiro=TiO2 vs RQ.61 (D-ARQ-18); DT-002L-01 (conversao mg/m3);
gas/marceneiro a confirmar.

---

## Sessão 002.L1 parte 2 — fixture Viverde — 27/05/2026

**Tipo:** IMPLEMENTAÇÃO
**Participantes:** Diovanni Lisita + Claude Code (Sonnet 4.6).
**Branch:** `feature/motor-002l1-fixture-viverde` (não mergeada).

### Entregue (3 commits)

- `18b7d15` — feat(vocab): adiciona 11 agentes-marcador para inventário canônico (decisões 10-12)
- `bc0066c` — feat(tests): fixture pgr_viverde - 32 GHEs em 3 blocos (002.L1 parte 2)
- `3301e8e` — test(fixture): smoke tests sobre fixture pgr_viverde + Stage 1 (002.L1 parte 2)

Suite: 290 testes verdes em `python -m pytest agente_medico/tests/ tests/`.
mypy --strict: clean nos arquivos novos.

### 3 decisões novas

**Decisão 10 — Ergonômico/acidente/dermatite no inventário canônico.**
Riscos ergonômicos, de acidente e dermatite entram no GHE como `RiscoPGR` com
slug próprio em `agentes.yaml` (R-GHE-04, MAPA linha 14: "inventário é
canônico"). Não disparam propósito clínico hoje (nenhuma R-PROP-* consome
agentes-marcador). Substitui decisão 7.

**Decisão 11 — Flag `disparador_clinico` em agentes.yaml.**
Agentes que não disparam regra clínica do motor recebem `disparador_clinico: false`.
Agentes pré-existentes (commitados antes de 002.L1 parte 2) não recebem o campo
e contam como `true` por convenção. Auditoria de PCMSO consegue, daqui em diante,
listar os agentes-marcador com um grep.

**Decisão 12 — Químico declarado sem agente nominal / sem medição.**
Quando o PGR cita exposição química sem agente identificável (ex: "primer,
cimento polimérico, mastique sem mg/m³") ou sem medição (CO em manta a quente),
modela-se como `RiscoPGR(agente="quimico_nao_especificado", quantificacao=None)`.
Pendência de FDS (R-PGR-04) é responsabilidade do Stage 3 do motor, não do
fixture. O fixture só transcreve o PGR como o engenheiro escreveu.

### Decisão deprecada

**Decisão 7 (parte 1) DEPRECATED em 27/05/2026.**
Redação original: "ergonômico/acidente fora do vocabulário de propósito (sinalização
via vocabulario_ausente)". Interpretação ambígua durante a parte 2 levaria a omitir
esses riscos do fixture, contrariando R-GHE-04 + MAPA linha 14 (inventário
canônico). Sucessora: decisão 10.

### Dívidas técnicas registradas

**DT-002L1-01:** Cargo `motorista` commitado genérico, fora da convenção
`operador_<máquina>` da decisão 1. Renomear para `motorista_cacamba` quando
convier (sem urgência clínica).

**DT-002L1-02:** Grafia de `relacao_LT` no helper `_ruido` (`abaixo_acao` /
`acima_acao` / `acima_LT`) ainda não validada contra `predicados.py`. Revisar
quando Stage 4 consumir o fixture; ajustar helper se a convenção do motor
divergir.

### Próxima sessão planejada

**Tipo:** decisão do Arquiteto (provável: PR único da branch
`feature/motor-002l1-fixture-viverde` em main, depois sessão 002.M para
endereçar divergência PGR↔RQ.61 do serralheiro — Est-09 TiO2 vs cromo/Mn).

---

## Sessão 002.M — virada de metodologia + encaminhamento do serralheiro (28/05/2026)

**Tipo:** CONHECIMENTO + META + ARQUITETURA
**Participantes:** Diovanni Lisita + Claude (Arquiteto). SEM Claude Code (sessão sem código).
**Branch:** docs (sem alteração de motor/fixture/vocabulário).

### Contexto
A Dra. Carolini não fará mais validação prévia de regras. Protocolo v8 congelado. A validação
clínica migra para REVISÃO DE SAÍDA: a médica (Patrícia/Carolini) lê a matriz gerada de um PGR
real e procura erros. Desenvolvimento mira erro zero; erros viram correções (PDCA). A 002.M,
planejada como pergunta à Carolini sobre o serralheiro, foi reescrita: a questão clínica já
estava resolvida (R-GHE-05) e a indisponibilidade da fonte exigiu formalizar o novo modelo.

### O que foi decidido
1. **Modelo de qualidade erro-zero + revisão de saída + PDCA (D-ARQ-22).** Hierarquia nova de
   resolução de incerteza: norma vigente → matriz validada (RQ.61/Patrícia) → analogia com
   `[VALIDADO]` → interpretação do Arquiteto marcada. Status `[A VALIDAR — Carolini]` descontinuado;
   novos `[DERIVADO — fonte]` e `[INTERPRETADO — prioridade na revisão de saída]`. Erro-zero apoia-se
   em determinismo (D-ARQ-09) + pendência-em-vez-de-chute (D-ARQ-08/13) + rastreabilidade por linha
   com status de validação (D-ARQ-03 estendido). Risco residual: erro silencioso plausível, mitigado
   pela rastreabilidade.
2. **Operação como dado de primeira classe (D-ARQ-23, PROPOSTA).** A divergência do serralheiro é
   estrutural, não clínica: o motor não modela operações, então não avalia "solda confirmada".
   D-ARQ-23 propõe campo `operacoes` no `GHEPGR` + inferência em Stage 2. A implementar.
3. **Serralheiro Est-09 documentado.** PGR Viverde declara TiO2 + radiação de solda (não declara
   fumos_metalicos nem cromo — cromo só na RQ.61, que é saída). Sem D-ARQ-23 o motor não dispara o
   pacote de fumos. Divergência esperada, rastreada. Nota em R-GHE-05 + comentário do fixture Est-09
   a atualizar quando D-ARQ-23 for implementada. Técnico: fumo de solda é mistura; TiO2 e cromo são
   constituintes do mesmo fumo (OSHA FS-3647; literatura de eletrodo).
4. **Três pendências órfãs reclassificadas** (DT-D3-02, DT-002I-01, DT-002L-01): de "perguntar à
   Carolini" para a hierarquia de D-ARQ-22. DT-002L-01 e DT-D3-02 têm âncora normativa (resolver
   `[DERIVADO]` no site oficial); DT-002I-01 sem âncora objetiva (candidata a `[INTERPRETADO]`).

### Fontes normativas confirmadas (site oficial MTE, vigentes em 28/05/2026)
- Índice oficial: gov.br/trabalho-e-emprego .../ctpp-nrs/normas-regulamentadoras-nrs
- NR-7 (PCMSO), NR-9 (avaliação/controle de exposições — NÃO é mais o PPRA; gerenciamento de risco
  migrou para NR-1), NR-15 (insalubridade): links de "texto vigente" na página índice. Anexos da
  NR-15 (PDFs separados) a conferir ao resolver DT-002L-01 e DT-D3-02.
- TODO normativo herdado (R-RX-01, "transcrição a-conferir"): conferir faixas de %LEO,
  periodicidades e corte de 15 anos contra o Anexo III da NR-07 vigente. Agora `[DERIVADO]`, não
  pergunta à Carolini.

### Próxima sessão planejada
Decisão do Diovanni. Candidatas:
- IMPLEMENTAÇÃO D-ARQ-23 (operação como dado + inferência de solda em Stage 2 + fixture Est-09).
- IMPLEMENTAÇÃO 002.D2 (Stage 4 — `ctx.predicados`), roadmap do motor.
- Normativa `[DERIVADO]`: resolver DT-002L-01 + TODO de R-RX-01 conferindo texto literal das NRs
  no site oficial (sem dependência de terceiros; fecha valores "a-conferir" do regras.yaml).

---
*Entradas futuras abaixo desta linha*
