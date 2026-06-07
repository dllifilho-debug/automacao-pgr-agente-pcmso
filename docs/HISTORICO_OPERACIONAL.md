# HISTÓRICO OPERACIONAL — AGENTE PCMSO

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

## Sessão 002.N — 29/05/2026 — CONHECIMENTO normativo + correção de borda
Branch: feature/regras-002n-rx01-leo (7 commits). Foco: conferência [DERIVADO] das entradas
"a-conferir" de R-RX-01 contra o texto literal vigente das NRs (site MTE) + resolução de DT-002L-01.

### Conferência normativa (texto literal, site oficial MTE)
- **NR-7 Anexo III, Quadro 1 (Portaria MTP 567/2022)** conferido. As 5 entradas de sílica/asbesto
  de R-RX-01 saíram de "a-conferir" para [DERIVADO]: periodicidades (≤10% só adm; >10–50% 60M→36M;
  >50–100% 36M→24M; >100% 12M sem corte; sem-medição 24M→12M) e corte de 15 anos confirmados.
  Achado: bordas fecham com ≤ no topo de cada faixa; variável de roteamento é CLSC (limite sup. do
  IC 95% da média aritmética lognormal — NÃO percentil 95).
- **NR-9 item 9.6.1** (transitório: usar LT da NR-15 enquanto não há anexo NR-9) e **9.6.1.1**
  (ACGIH na ausência de LT) confirmados.
- **NR-15 Anexo 12** (Portaria SSST 1/1991): LT da sílica = f(%quartzo) — respirável 8/(%quartzo+2),
  total 24/(%quartzo+3).
- **NR-22 Anexo V**: Portaria MTE 105/2026 fixou 0,05 ppm (unidade incoerente); Portaria MTE 261/2026
  corrigiu para 0,05 mg/m³ poeira respirável e revogou o §2º do art. 4º da 105. LEO de sílica na
  mineração = 0,05 mg/m³.

### Decisões e pendências
- **DT-002L-01 RESOLVIDA** [DERIVADO]+[INTERPRETADO]: a NR-7 não fixa o LEO; roteia por CLSC/LEO.
  O valor do LEO vem do arranjo NR-9 + anexo setorial por agente/cenário (sílica não-mineração: LT
  Anexo 12 NR-15; mineração: 0,05 mg/m³ NR-22). %quartzo é entrada obrigatória fora de mineração.
- **D-ARQ-24** criado: contrato do LEO-resolver (origem do LEO por agente/cenário, cadeia de
  precedência NR-9). Ortogonal a D-ARQ-04 (regime do PCMSO ≠ fonte do LEO). Implementação pendente.
- **DT-002N-01** aberta: R-RX-01-pnos achata as 4 faixas do Quadro 2 do Anexo III num único 60M.
  R-RX-01-pnos rebaixado VALIDADO→INTERPRETADO. Explodir em família por faixa (pendente).
- **R-RX-02 (fumos)** rebaixado VALIDADO→INTERPRETADO: 60M sem âncora no Anexo III (fumos não é
  Quadro 1 nem Quadro 2). Roteamento correto depende de decompor fumos em metais individuais —
  aponta DT-D3-02 (já existente).

### Correção de código (commit fix 002.N)
- predicados.py: bordas de faixa LEO corrigidas de </>= para ≤ no topo (silica_asbesto_leo_10_50,
  _50_100, _acima_100). pct=50 agora cai em 10_50 (era 50_100); pct=100 em 50_100 (era acima_100).
  Erro estava duplicado em 3 funções; era divergência da norma, achada na conferência.
- test_rx_periodicidade.py: header A-CONFERIR→[DERIVADO]; +2 testes de regressão de borda (pct=50→60M/36M,
  pct=100→36M/24M) que falhavam antes do fix.
- Suíte: 290→292, verde. mypy --strict limpo.

### Lições / método
- Resumo do Code ≠ literal do arquivo: várias vezes o "idêntico/N linhas" mascarou o conteúdo real;
  só o dump literal (Get-Content) permitiu conferência e edição cirúrgica sem adivinhar.
- A borda ≤ era achado de conferência contra a norma, não suposição — virou teste de regressão.
- Carolini fora do loop até a conclusão (PDCA, D-ARQ-22): conferência por fonte objetiva, não crivo
  clínico prévio. Tags [DERIVADO]/[INTERPRETADO] carregam a validação até a revisão de saída final.
- **Quebra de protocolo de merge (ba38c74).** O commit da DT-002N-02 foi direto em `main`, fora de
  PR — os 9 commits anteriores entraram corretamente via PR #32. Causa: após o merge do PR #32 a
  branch ativa virou `main`, e o prompt do commit não foi precedido de checagem de branch (higiene
  de abertura). Aceito como está (doc-only, conteúdo correto, história linear — reverter custaria
  mais que o defeito). Regra reforçada: TODO prompt que vai commitar deve ser precedido de
  `git branch --show-current`; trabalho entra em `main` só via PR com merge commit autorizado.

### Residuais abertos (próximas sessões)
- IMPLEMENTAÇÃO D-ARQ-24: LEO-resolver (mg/m³ + %quartzo → CLSC/LEO → faixa). Destrava sílica do
  Viverde (hoje pct_LT=None). Pré-requisito: campo pct_quartzo em Quantificacao + cenário de
  exposição derivado do PGR (GHEPGR não tem CNAE/atividade/local hoje).
- IMPLEMENTAÇÃO DT-002N-01: explodir R-RX-01-pnos em família por faixa do Quadro 2.
- IMPLEMENTAÇÃO Fatia B: janela demissional condicional do Quadro 1 (no agendador).
- META: DT-002N-02 — notação de status DERIVADO diverge entre D-ARQ-22 Parte A (três sabores
  tipados) e convenção v9 (um `[DERIVADO — fonte]`). A 002.N operou na notação v9; fonte real nos
  corpos (sem erro silencioso). Reconciliar os dois documentos antes de propagar a notação —
  preferível como primeira pauta da 002.O. Não reabrir a 002.N.
- D-ARQ-23 (operação como dado), DT-D3-02 (fumos → metais individuais): herdados, abertos.

### Próxima sessão planejada
Decisão do Diovanni. Recomendação do Arquiteto: IMPLEMENTAÇÃO D-ARQ-24 (LEO-resolver) — é a fundação
que destrava o roteamento de sílica em mg/m³ e da qual dependem as fatias B/C.

---
## Sessão 002.O — 29/05/2026 — META (reconciliação de notação)
Branch: docs/meta-002o-notacao-derivado. Foco: resolver DT-002N-02 —
reconciliar a notação de status `[DERIVADO]` entre D-ARQ-22 Parte A e a convenção do PROTOCOLO.

### Achado central
A DT-002N-02 estava mal formulada. Não havia conflito de conteúdo entre D-ARQ-22 e a convenção do
PROTOCOLO — havia descrição imprecisa no resumo da 002.N. D-ARQ-22 Parte A NÃO define "três sabores
tipados": define um único formato `[DERIVADO — <fonte>]`, fonte preenchida conforme o nível 1-3 da
hierarquia; `[INTERPRETADO]` é o nível 4 (marcador irmão, não sabor de DERIVADO). A convenção do
PROTOCOLO nunca foi "genérica" — sempre exigiu fonte objetiva nomeada, com a mesma hierarquia. Os
dois sempre concordaram no fundo; divergiam só em ONDE a fonte aparece: corpo (PROTOCOLO) vs.
marcador (D-ARQ-22).

### Decisões
- Notação canônica: fonte NO MARCADOR (`[DERIVADO — NR-x item y]`, `[DERIVADO — RQ.61/Patrícia]`,
  `[DERIVADO — analogia R-XXX]`). Rastreabilidade no token vence economia visual.
- Convenção `[DERIVADO]` do PROTOCOLO reescrita (hierarquia de 4 níveis + fonte no marcador).
- R-RX-01 "Valores conferidos": `[DERIVADO — fonte]` → `[DERIVADO — NR-7 Anexo III Quadro 1]`
  (alinhamento de formato; mesma ID, sem mudança de semântica).
- Nota de resolução em D-ARQ-22 (corpo de D-ARQ-22 não muda).
- Sem reclassificação de regra. Sem código. Sem alteração de suíte (doc-only).

### Lições / método
- "Três sabores tipados" foi conclusão do resumo da 002.N, não do literal de D-ARQ-22. Só o dump
  literal da Parte A desfez — reforça a lição da 002.N (resumo ≠ literal).
- DT de "divergência entre dois textos" exige ler os dois literais antes de abrir, não os resumos.

### Residuais abertos (próximas sessões)
- IMPLEMENTAÇÃO D-ARQ-24: LEO-resolver (mg/m³ + %quartzo → CLSC/LEO → faixa). Destrava sílica do
  Viverde. Recomendação do Arquiteto para a próxima sessão.
- IMPLEMENTAÇÃO DT-002N-01: explodir R-RX-01-pnos em família por faixa do Quadro 2.
- IMPLEMENTAÇÃO Fatia B: janela demissional condicional do Quadro 1 (agendador).
- D-ARQ-23 (operação como dado), DT-D3-02 (fumos → metais individuais): herdados, abertos.

### Próxima sessão planejada
Decisão do Diovanni. Recomendação do Arquiteto: IMPLEMENTAÇÃO D-ARQ-24 (LEO-resolver).

---

## Sessão 002.P — 30/05/2026 — ARQUITETURA (camada de extração)
Branch: docs/arq-002p-ponte-parser-motor. Foco: especificar a camada que transforma PGR real
em tipos.PGR, destravando o objetivo de produção (qualquer PGR, qualquer setor).

### Achado central
O motor nunca recebeu PGR real — só a fixture Viverde escrita à mão. O caminho de produção atual
(Streamlit) usa parser_pgr.py (regex), que cospe chaves cruas sem quantificação nem vocabulário
canônico, três níveis abaixo do que tipos.PGR exige. A extração-LLM (extrair_pgr_estruturado_via_
gemini) existe mas devolve linguagem natural sem quantificação nem slugs. A camada de extração que
o motor novo precisa é a etapa 3 do plano original do projeto, adiada até o motor existir — nunca feita.

### Decisões
- D-ARQ-25 criada (três partes): (A) contrato de fronteira é tipos.PGR, sem intermediário; parser
  legado não portado. (B) normalização de vocabulário (linguagem natural → slug) é responsabilidade
  da extração, a montante; motor permanece puro (D-ARQ-09). (C) contrato-alvo completo de tipos.PGR
  especificado, conferido contra o arquivo real: campos existentes preenchidos, campos existentes
  não-preenchidos pelos extratores legados (gates, EPI, psicossocial, FDS/CAS), campos inexistentes
  para extensão futura (pct_quartzo + cenário de exposição, ambos pré-requisito de D-ARQ-24).
- Roadmap de produção fixado: estender tipos.py → implementar extração LLM→tipos.PGR → validar
  contra fixture Viverde (gabarito de forma) → validar contra PGR não-construção (universalidade).

### Lições / método
- Cache do project knowledge estava atrás do disco: tipos.py indexado faltava periodicidade_apos_15a
  e is_ototoxico. Contrato campo-a-campo (Parte C) só foi fechado após dump literal do tipos.py atual.
  Reforça a regra de ouro: índice serve para ler arquitetura; git/disco vence para a verdade do estado.

### Residuais abertos (próximas sessões)
- IMPLEMENTAÇÃO: estender tipos.py (Parte C de D-ARQ-25) — campos de gate/EPI/psicossocial/FDS já
  existem; faltam pct_quartzo e cenário de exposição.
- IMPLEMENTAÇÃO D-ARQ-24 (LEO-resolver): destravada assim que cenário + pct_quartzo existirem.
- IMPLEMENTAÇÃO DT-002N-01 (PNOS família por faixa); Fatia B (janela demissional, agendador).
- META herdada [RESOLVIDA na sessão de rename]: nome/identidade decidido — "Agente PCMSO" (display) / `agente-pcmso` (slug). Menções a Seconci-GO removidas de PROTOCOLO (header) e DECISOES (D-ARQ-04); procedência `[VALIDADO]` preservada (fonte = entrevista Dra. Carolini). Linha 849 mantida — "Seconci Goiás" ali é nome de matriz órfã em matrizes_originais/, dado de inventário, não vínculo institucional. Itens manuais fora do git: rename repo GitHub, subdomínio Streamlit, system prompt do projeto.
- D-ARQ-23 (operação como dado), DT-D3-02 (fumos → metais individuais): herdados, abertos.

### Próxima sessão planejada
Decisão do Diovanni. Recomendação do Arquiteto: IMPLEMENTAÇÃO da extensão de tipos.py (Parte C) —
é o pré-requisito mecânico de tudo (extração e D-ARQ-24 dependem dos campos novos).

---

*Entradas futuras abaixo desta linha*

---

## Sessão 002.Q — 30/05/2026 — IMPLEMENTAÇÃO (tipos.py Parte C)
Branch: `feature/tipos-002q-cenario-pct-quartzo` — PR #36 (merge commit b1294c2). Foco: estender `tipos.py` com os campos da Parte C de D-ARQ-25 — `pct_quartzo` e cenário de exposição, pré-requisitos de dados do LEO-resolver (D-ARQ-24).

### O que foi feito

1. `Quantificacao.pct_quartzo: Optional[float] = None` — denominador da fórmula do Anexo 12 (NR-15), pré-requisito do LEO-resolver (R-RX-01 / D-ARQ-24).
2. Novo `CenarioExposicao` (dataclass frozen; `cnae`/`atividade`/`local`, todos `Optional`, default `None`) — definido imediatamente antes de `GHEPGR`.
3. `GHEPGR.cenario: Optional[CenarioExposicao] = None` — contexto fático por GHE.
4. 5 testes em `agente_medico/tests/test_tipos.py`.

### Resultados

- **pytest** `agente_medico/tests/ tests/` — 297/297 verdes (292 + 5 novos). Nenhum pré-existente quebrou.
- **mypy --strict** `agente_medico/motor` — Success: no issues found (12 source files).
- Commit `46e32dc`; merge via PR #36 (merge commit b1294c2).

### Decisão de design

Cenário vira sub-objeto `CenarioExposicao` (não campos soltos em `GHEPGR`). Razão: coesão (cenário é unidade fática), evolução prevista por D-ARQ-24 (mais dados de cenário virão), opcionalidade limpa. `pct_quartzo` fica direto em `Quantificacao` (pertence à quantificação, sem coesão externa). `CenarioExposicao` carrega só dado fático — a derivação normativa (mineração-NR-22) permanece no LEO-resolver downstream, preservando D-ARQ-24. Confirmada com o Diovanni nesta sessão (proposta da 002.P, aprovada na 002.Q).

### Cobertura de teste

`pct_quartzo` materializa caminho de regra clínica (R-RX-01 / D-ARQ-24) → 2 testes que falham sem o campo (default None + aceitação de valor). Cenário ainda sem consumidor clínico (D-ARQ-24 não implementado) → 3 testes de construção/serialização (`asdict`), sem lógica clínica.

### Residuais abertos (próximas sessões)
- IMPLEMENTAÇÃO D-ARQ-24 (LEO-resolver): destravada — campos existem; falta o resolver + classificador CLSC.
- IMPLEMENTAÇÃO extração LLM→`tipos.PGR` (D-ARQ-25 itens A/B restantes).
- IMPLEMENTAÇÃO DT-002N-01 (PNOS família por faixa); Fatia B (janela demissional, agendador).
- D-ARQ-23 (operação como dado), DT-D3-02 (fumos → metais individuais): herdados, abertos.

### Próxima sessão planejada
Decisão do Diovanni.

---

## Sessão 002.R — 30/05/2026 — IMPLEMENTAÇÃO → ARQUITETURA → META (gate de A, repriorização para B, gate de procedência)

**Foco declarado:** IMPLEMENTAÇÃO (fechar tipos.py Parte C, D-ARQ-25). Arco real: o gate mostrou a Parte C já 100% materializada pela 002.Q → a sessão virou ARQUITETURA (spec de B.1, recorte, decisão tabela Python-vs-YAML) e terminou em META (nota de método). Os três focos numa sessão, registrados no cabeçalho.

**Gate de A (D-ARQ-25 Parte C).** Cruzamento da Parte C literal (DECISOES vivo) × tipos.py real: todos os campos dos três baldes presentes. "Existem mas ninguém preenche" são gap de extração, não de tipo (fora de escopo, confirmado pelo próprio D-ARQ-25). pct_quartzo + CenarioExposicao criados na 002.Q. Passo (1) de D-ARQ-25 concluído; (A) morto. Não codar sobre tipo fechado.

**Repriorização para (B) D-ARQ-24.** LEO-resolver + classificador CLSC. Spec de B.1 fechada (classificador de cenário + LEO-resolver, sem CLSC/plug no pipeline): tipos Fracao/CenarioNormativo em tipos.py, ResultadoLeo + lógica + tabela de precedência em motor/leo_resolver.py novo, teste em tests/test_leo_resolver.py. Tabela de precedência como módulo Python tabelado, não YAML (a tabela LEO não é regra clínica — muda por portaria, não por opinião da Carolini; argumento YAML de D-ARQ-07 não se aplica). B.1 NÃO foi implementada — segue para próxima sessão de código.

**2ª passada (gatilho do Diovanni).** Revisão adversarial do prompt de B.1 achou: (1) CRÍTICO — CNAE "06" (petróleo/NR-37) cravado como mineração/NR-22, valor que rodada anterior marcava como incerto, degradado a hardcode na transcrição para o prompt; lista correta para sílica/NR-22 é 05/07/08/09 e volta a marcador de procedência até confirmação; (2) B.2 (CLSC→faixa) anunciada como trivial sem investigar que CLSC exige amostra de medições que Quantificacao.valor (float único) não modela — possível gap de tipo antes de B.2, a investigar; (3) ResultadoLeo é output interno, não pertence a tipos.py (vai em leo_resolver.py).

**Nota de método (META) — D-ARQ-22 v22.** Gate de procedência factual no ponto de emissão do prompt cirúrgico, gêmeo do gate de estado. Origem empírica: o CNAE "06". Gravada em DECISOES (D-ARQ-22, nota de aplicação, mesma ID), PR mergeado em main. Doc-only.

**Pendências abertas para a próxima sessão de código:**
- B.1 (classificador de cenário + LEO-resolver) — spec fechada, prompt cirúrgico a reemitir com o CNAE corrigido (06 = petróleo/NR-37 está fora; 05/07/08/09 são candidatos [DERIVADO — confirmar contra NR-22 Anexo V + CNAE 2.0], não cravar sem confirmar).
- Antes de B.2: confirmar o que alimenta o CLSC (Quantificacao já basta como CLSC pronto, ou falta campo de amostra) e ler o texto vivo de R-RX-01 (até aqui veio do cache).

**Suíte:** 297 verde / mypy limpo, herdado da 002.Q; 002.R não rodou código (doc-only). Reconfirmar na abertura de B.1 por higiene, não por suspeita de regressão.

---

## Sessão de rename — "Agente PCMSO" (30/05/2026) [META + manutenção app]

Duas frentes distintas, registradas separadas por escopo e natureza diferentes.

### Frente 1 — Rename do projeto (doc-only, escopo do kickoff)
Fase 1 (identidade): decidido "Agente PCMSO" (display) / `agente-pcmso` (slug-alvo) — domínio carregado pelo PCMSO, sem cola em construção, sem "Médico" redundante. Fase 2 (propagação): 6 edições doc em PROTOCOLO/DECISOES/HISTORICO (3 títulos H1 + remoção de vínculo Seconci-GO em header do PROTOCOLO e D-ARQ-04; procedência `[VALIDADO]` preservada, fonte = entrevista Dra. Carolini). PR #37, merge commit 24df3fa.

Itens manuais fora do git, todos concluídos: repo GitHub renomeado; subdomínio Streamlit; system prompt do projeto (instruções claude.ai — "(Seconci-GO)" removido, vale a partir do próximo chat).

DIVERGÊNCIA slug decidido vs. slug real: a Fase 1 decidiu `agente-pcmso` puro, mas o rename efetivo (repo GitHub + Streamlit) ficou `automacao-pgr-agente-pcmso` — o nome técnico antigo do pipeline (`automacao-pgr-`) permaneceu como prefixo. Repo real: dllifilho-debug/automacao-pgr-agente-pcmso. App real: automacao-pgr-agente-pcmso.streamlit.app. Não é resíduo Seconci (limpo); é o slug do pipeline não removido. Alinhar ao slug puro é renomeação futura opcional (repo + Streamlit de novo), decisão de Diovanni.

Nota de método: o grep de verificação de resíduo errou na 1ª passada por case-sensitivity — buscou "Agente Médico" e não casou o título em caixa alta "AGENTE MÉDICO PCMSO". Verificação de rename deve ser case-insensitive. Buraco pego no passo 4 pelo Code antes do commit, fechado com 6ª edição (título H1 do HISTORICO).

### Frente 2 — Remoção de branding Seconci do app legado (fora do escopo doc-only)
Frente aberta conscientemente durante a sessão, NÃO prevista no kickoff doc-only. Toca app.py (casca Streamlit do legado). logo.png removido do git; 5 ocorrências "Seconci" em app.py (docstring, set_page_config, fallback login, rodapé, sidebar) → "Agente PCMSO"; fallback visual escudo + Agente PCMSO, sem dependência de imagem. 297/297 verde. PR #38, merge commit e7d6a73.

Ressalva de validade (D-ARQ-25 Parte A): o legado Streamlit será aposentado e app.py morre com ele. A limpeza do nome se justifica enquanto o app está vivo e em uso (confirmado por Diovanni: app funcionando), não como investimento de longo prazo.

### Nota de método — commit direto em main fora de PR
Durante a sessão, `.devcontainer/devcontainer.json` apareceu em main via commit f9a9ced ("Added Dev Container Folder"), commitado direto em main pela UI do GitHub, sem branch nem PR. Origem legítima (autoria do Diovanni, config de ambiente de dev, inofensivo), confirmada por git log. Registrado como desvio do protocolo de merge (branch → PR → merge commit): commit direto em main fura o fluxo silenciosamente. Tolerável para config de ambiente; não normalizar para código de motor/protocolo.

### Pendências ortogonais não tratadas
- matrizes_originais/ (37 não-rastreados) — decidir gitignore vs. versionar quando abrir a sessão de validação (D-ARQ-18).
- Slug com prefixo `automacao-pgr-` (ver divergência na Frente 1) — alinhamento opcional futuro.
- Descasamento aceito: display "Agente PCMSO" ↔ pasta de código `agente_medico/`. Refactor de pasta é sessão de código futura, não bloqueia.

---

## Sessão 002.S — B.1: LEO-resolver + classificador de cenário (D-ARQ-24)

**Foco:** CONHECIMENTO normativo (bloqueio de procedência) → IMPLEMENTAÇÃO.
**Commit:** c1e2be6 (merge em main via PR). 3 arquivos, 241 linhas. 312 verdes (297+15), mypy --strict limpo.

**Bloqueio resolvido (CONHECIMENTO).** O prompt da 002.R trazia CNAE "06" como mineração/NR-22 — erro: 06 = petróleo/gás (NR-37). Confirmado contra fonte vigente (CNAE 2.0 IBGE/Concla + campo de aplicação NR-22):
- Mineração/NR-22 = divisões **05, 07, 08** + grupo **099** (apoio a mineral).
- Fora: **06** (petróleo) e **091** (apoio a petróleo/gás → NR-37). A divisão 09 é split — cravar "09" a 2 dígitos repetiria o defeito do "06".
- `09` puro (divisão sem grupo) → GERAL por ambiguidade; mineração legítima sem CNAE granular entra pela keyword.

**Achado de procedência da sílica (105→261).** D-ARQ-24 citava só "Portaria MTE 261/2026". Cadeia real: Anexo V da NR-22 **aprovado pela Portaria MTE 105/2026** (trazia "0,05 ppm", unidade inconsistente) e **corrigido pela 261/2026** para **0,05 mg/m³ respirável** (revogou §2º art. 4º da 105). Valor vigente confirmado; código e D-ARQ-24 passam a citar a cadeia 105→261.

**Entregue.** `Fracao`/`CenarioNormativo` (tipos.py); `classifica_cenario` + `resolve_leo` + `ResultadoLeo` (leo_resolver.py, fora de tipos.py); 15 testes. Cadeia de precedência D-ARQ-24 como tabela de 4 níveis por agente (n2/n4 vazios para sílica, estrutura preservada p/ universalidade).

**Decisão de B.1: `(silica, total, MINERACAO)` = LEO indefinido** (`leo=None`, fonte não-vazia), não fallback ao Anexo 12. NR-22 Anexo V só fixa respirável; total-mineração é vazio normativo. Não exercido pelo RX OIT (que usa respirável, R-RX-01/D-ARQ-24).

**Dívidas registradas (revisitar em B.2):**
- Slug `silica` duplicado em leo_resolver.py — paliativo consciente; B.2 deve referenciar o canônico de agentes.yaml.
- `re.sub(r"\D","",cnae)` é tolerante a lixo (`"x05y"`→`"05"`) — ok em B.1 (input estruturado), pressuposto que a extração real (B.2) herda.
- `_NivelLeo` com forward refs em string — cosmético, limpar se tocar o módulo.

---

## Sessão 002.T — 31/05/2026 — META (desenho da skill /kickoff) + higiene

**Foco:** META — desenhar a skill de abertura de sessão. Não tocou motor, protocolo nem regra clínica. Gravou D-ARQ-26.

**Higiene de ambiente (feito nesta sessão):**
- Pasta local renomeada de automacao-pgr-seconci → automacao-pgr-pcmso. git grep confirmou zero referências funcionais ao nome antigo (só narrativa no HISTORICO 187-188 e um comentário em tests/test_regressao_pcmso.py:19, ambos sem impacto). Rename transparente ao git e ao Code (reapontar a sessão do Code à pasta nova; o erro "working directory no longer exists" era o ponteiro velho, não perda).

**Desenho da skill /kickoff → D-ARQ-26.** Ver DECISOES. Resumo: skill versionada em .claude/skills/kickoff/, invocação explícita, híbrida (coleta factual no Code, julgamento no Arquiteto), burra por design (lê/reporta, não calcula/seleciona), saída em tela. Material externo (vídeos via NotebookLM) confirmou a arquitetura de "verificação antes da entrega" (independente da nossa — as três zonas) e alertou sobre consumo de contexto; mecânica de instalação do vídeo (UI/skill-creator) foi descartada por não ser versionada. Doc oficial do Claude Code confirmou onde mora e como dispara.

**Pendências abertas:**
- IMPLEMENTAR a skill /kickoff (sessão de Code): criar .claude/skills/kickoff/SKILL.md a partir do desenho em D-ARQ-26; o Code confirma frontmatter + allowed-tools contra um SKILL.md real (/mnt/skills/public/*) ANTES de gravar; reiniciar o Code uma vez (diretório de skills novo); testar /kickoff. Eval: reproduzir o estado que geraria o kickoff de B.2, lendo só git + HISTORICO.
- B.2 (D-ARQ-24, próxima de CÓDIGO): CLSC → faixa → plug no pipeline. ANTES de codar, resolver (CONHECIMENTO/ARQUITETURA): Quantificacao.valor é float único; CLSC (limite superior do IC 95% da média lognormal, R-RX-01) exige amostra de medições — confirmar se valor serve como CLSC pronto ou se falta campo de tipo (pode encostar em D-ARQ-25 Parte C). Ler texto vivo de R-RX-01 (até aqui veio do cache).
- Dívidas da B.1 (registradas na 002.S): slug silica → canônico de agentes.yaml; tolerância do re.sub ao plugar extração real; cosmético _NivelLeo.
- DÍVIDA DE HIGIENE (nova, baixa urgência): raiz do projeto poluída — prompt_*.txt consumidos (002.A–002.M) e três cópias-fantasma de doc na raiz (DECISOES/HISTORICO/PROTOCOLO de 17/05, congeladas em D-ARQ-13) com mesmo nome dos docs vivos de docs/. Risco: Get-Content sem docs\ na frente lê a versão velha achando que é a viva. Resolver em sessão de higiene: apagar/arquivar prompts mortos, apagar as cópias-fantasma (docs/ é canônico). Encosta na decisão .gitignore vs versionar adiada em D-ARQ-18.

**Suíte:** 312 verde / mypy limpo, herdado da 002.S; sessão META não rodou código.

---

## Sessão 002.U — 31/05/2026 — IMPLEMENTAÇÃO/META (skill /kickoff gravada)

**Foco:** IMPLEMENTAÇÃO/META — gravar a skill /kickoff desenhada em D-ARQ-26 e fechar os [INCERTO] de frontmatter. Não tocou motor, protocolo nem regra clínica.

**Branch:** `feature/skill-kickoff` (de main dd5682b).

**Frontmatter resolvido contra doc oficial** (code.claude.com/docs/en/skills, não blog):
- `disable-model-invocation: true` materializa a propriedade 1 (invocação explícita, sem auto-load; descrição fora de contexto até invocar). `user-invocable: false` seria erro — esconde do menu `/`, deixa só o Claude invocar.
- Command e skill foram fundidos no Claude Code; o artefato é skill (`.claude/skills/kickoff/SKILL.md`), forma recomendada.
- `allowed-tools` read-only `Bash(git log *) Bash(git status *) Read` — sem escrita (propriedade 4).
- Coleta via tools próprias do Code, não injeção `!`comando`` — robustez Windows/PowerShell (default-bash arrisca não rodar; acento arrisca CP1252). Injeção fica como upgrade se eval mostrar passo pulado.

**Bloqueador resolvido — `.claude/` era gitignored inteiro.** D-ARQ-26 exige a skill "sob git". `.gitignore` tinha `.claude/` (config local). Exceção cirúrgica: `.claude/*` + `!.claude/skills/` (re-incluir filho exige abrir o parent — `!.claude/skills/` sozinho não destrava). `git check-ignore` confirmou destravado. Resolve versionamento para skills; decisão geral .gitignore-vs-versionar (D-ARQ-18) segue adiada.

**Correção de transcrição.** 002.T declarava suíte "297 verde herdado da 002.S" — 002.S fechou em 312 (297+15 da B.1). Corrigido 297→312. Pego pelo cruzamento manual git×HISTORICO na abertura desta sessão, não pela skill (skill lê só o último bloco; cruzamento entre sessões é do Arquiteto — coerente com "skill fina").

**Eval do /kickoff — VERDE.** Reproduziu o estado lendo só git + HISTORICO: log verbatim (topo dd5682b/c1e2be6), status, bloco 002.T integral com B.2 e dívidas da B.1, suíte 312 (valor corrigido, não resumido), cruzamento sem divergência. Devolveu foco/prioridade/numeração ao Arquiteto. Detectou que roda dentro da própria sessão que a implementou (pendência "IMPLEMENTAR /kickoff" ainda aberta no 002.T) e reportou como trabalho em curso, não divergência. Comportamento "burro por design" confirmado.

**Entregue.** `.claude/skills/kickoff/SKILL.md` (novo); nota de aplicação 002.U + linha v24 no D-ARQ-26; correção 297→312 no 002.T; exceção de gitignore. 4 arquivos.

**Suíte:** 312 verde / mypy limpo, herdado da 002.S; sessão de implementação de skill (META), não rodou o motor.

**Próxima sessão de CÓDIGO — B.2 (D-ARQ-24):** CLSC → faixa → plug no pipeline. Bloqueio a resolver ANTES de codar (CONHECIMENTO/ARQUITETURA): `Quantificacao.valor` é float único; CLSC (limite superior do IC 95% da média lognormal, R-RX-01) exige amostra de medições — confirmar se valor serve como CLSC pronto ou se falta campo de tipo (encosta em D-ARQ-25 Parte C). Ler texto vivo de R-RX-01 (até aqui veio do cache). Abrir com /kickoff.

---

## Sessão 002.V — 01/06/2026 — CONHECIMENTO/ARQUITETURA (bloqueio do plug B.2 fechado)

**Foco:** CONHECIMENTO/ARQUITETURA — resolver o bloqueio da B.2 (D-ARQ-24) antes de virar código: decidir se `Quantificacao.valor` (float único) serve como CLSC pronto ou se falta campo no modelo. Não tocou código, motor nem regra clínica.

**Reformulação do bloqueio.** A pergunta da 002.U ("`valor` float vs. amostra de medições") era a errada. `valor: float` único basta — o motor **consome** o CLSC do laudo, não o calcula (cálculo do IC 95% lognormal é trabalho de higienista/NR-09, a montante; a amostra nunca entra no motor). A premissa "médica lê CLSC, não recalcula" ficou registrada como DT-002V-01 (A VALIDAR com Carolini).

**Campo que de fato faltava — a fração.** Leitura de `leo_resolver.py` (B.1): `resolve_leo` exige `fracao: Fracao` como primeiro argumento e a fração decide a fórmula do Anexo 12 (respirável `8/(%q+2)` vs. total `24/(%q+3)`). Mas `Quantificacao` não tem campo de fração — o Enum `Fracao` e o resolver existem desde a B.1, faltava o campo na medição que os liga (gêmeo do `pct_quartzo` da 002.Q). O plug da B.2 não tinha de onde ler a fração.

**Decisão de modelo:** `Quantificacao.fracao: Optional[Fracao] = None`. Ao lado de `valor` (fração é propriedade da medição, pareada à concentração), não em `CenarioExposicao` (fração e cenário são ortogonais na assinatura do resolver), não derivada de `unidade`. Pendência bloqueante quando sílica/asbesto + quantitativa + `fracao is None`.

**Testes especificados (para a sessão de código):** (1) sílica fora de mineração, mesmo `valor`+`pct_quartzo`, `fracao=RESPIRAVEL` vs. `TOTAL` → LEOs/faixas diferentes (falha sem o campo, passa com); (2) borda — sílica/mineração/`TOTAL` → resolver indefinido → Pendencia (cobre o vazio normativo que a B.1 deixou explícito, changelog 002.S).

**Docs atualizados:** DT-002V-01 nova (PROTOCOLO, tabela → v12); changelog 002.V em D-ARQ-24 (mesma ID — premissa refinada, saída inalterada); nota 002.V em D-ARQ-25 Parte C (DECISOES, tabela → v25).

**Dívida de conformidade detectada (não tratada aqui).** Duas DTs estão resolvidas no corpo mas mantêm marca de pendência no título — DT-002N-02 (resolvida na 002.O, ainda `[INTERPRETADO]` sem linha `Status: RESOLVIDA`) e DT-002L-01 (resolvida na 002.N, título ainda `[A VALIDAR]` embora o campo Status diga "Resolvida na 002.N"). Uma varredura por `[A VALIDAR]`/`[INTERPRETADO]` as confunde com pendência aberta. Não corrigido nesta sessão (escopo da 002.V é o bloqueio da B.2; correção de marca é META à parte, não mistura no commit de fechamento). Registrado para não se perder.

**Próxima sessão de CÓDIGO — B.2 (D-ARQ-24):** adicionar `fracao` a `Quantificacao` + 2 testes → classificador CLSC (faixa) → plug `resolve_leo` no pipeline. Abrir com /kickoff. O prompt cirúrgico do Code exige o gate de estado real (git log/status + leitura de `tipos.py`, `leo_resolver.py`, `regras.yaml`) no início daquela sessão.

**Suíte:** 312 verde / mypy limpo, herdado da 002.U. Sessão de CONHECIMENTO/ARQUITETURA, não rodou o motor.

---

## Sessão 002.W — 02/06/2026 — IMPLEMENTAÇÃO (B.2: plug resolve_leo + Quantificacao.fracao) + virada de método

**Foco:** IMPLEMENTAÇÃO — fechar a B.2 (D-ARQ-24) especificada na 002.V: campo `fracao` em `Quantificacao` + 2 testes → plug `resolve_leo` no pipeline via `_helper_silica_asbesto`. Escopo e ordem herdados da 002.V.

**Gate de leitura ampliado.** A revisão crítica do prompt (3 passadas) expôs que o plug atravessa `estagios/riscos.py`, fora do gate original. Leitura confirmou: (1) `stage_2_riscos` passa `quantificacao` por referência → `fracao` sobrevive à conversão PGR→Risco sem tocar `riscos.py`; (2) `Risco.agente` mantém o slug do PGR sem normalização → `_PRECEDENCIA` acerta. Lição: o gate cobre todo arquivo que o código atravessa, não só os que edita.

**Decisão arquitetural (changelog D-ARQ-24, mesma ID):** `pct_LT` do PGR tem precedência sobre `resolve_leo`. O ramo do plug só dispara quando `pct_LT is None`. Saída inalterada para quem já mandava `pct_LT`.

**Entrega.** `Quantificacao.fracao: Optional[Fracao] = None`. Ramo em `_helper_silica_asbesto` antes da guarda (c): medição bruta sem `pct_LT` → `fracao is None` devolve Ausente; fração presente resolve LEO e calcula `pct_LT`; LEO indefinido devolve Ausente. Conversão Ausente→Pendencia(bloqueante) já em `emissao.py` via `quando_ausente`. Predicado puro; 5 predicados de faixa intocados.

**Testes (+3, `test_b2_fracao_resolver.py`):** A — RESPIRAVEL→75%→36M vs. TOTAL→27%→60M (borda 50 cruzada); B — `fracao=None`→PRELIMINAR, sem RX, bloqueante; C — sílica/mineração/TOTAL→LEO indefinido→bloqueante (fecha o teste-borda da 002.V).

**Dívidas registradas (não tratadas):** asbesto fora de `_PRECEDENCIA` (medição bruta→Pendencia, correto para B.2); `resolve_leo` não valida `valor`/`pct_quartzo` negativos.

**Virada de método (D-ARQ-27).** Decidido: durante a construção, a fonte operante de método é a derivação direta das normas via PDCA; a Dra. Carolini valida as saídas (matrizes de exames) no aceite final, não consulta de método durante a build. Regras derivadas por interpretação carregam `INTERPRETADO` até a validação. DT-002L-01 é a primeira instância — pergunta de método respondida por derivação própria e materializada na B.2. Risco aceito e mitigação em D-ARQ-27.

**Higiene de conformidade (dívida da 002.V, fechada aqui).** Títulos de DT-002L-01 (`[A VALIDAR]` removido, `Status: RESOLVIDA`) e DT-002N-02 (`[INTERPRETADO]` removido, `Status: RESOLVIDA na 002.O`, caminho (a)) corrigidos — paravam de dar falso-positivo em varredura de pendência aberta. DT-002V-01 permanece `[A VALIDAR]` corretamente (item de aceite final sob D-ARQ-27).

**Incidente operacional — commit em `main` em vez da branch.** O Code commitou `87c650c` em `main` local (não fez checkout em `feature/b2-fracao-classificador`, que já existia). Detectado pelo Arquiteto via `git log --all --decorate` no gate de push; o relatório do Code não nomeou a branch. Correção sem perda: `git branch -f feature/b2-fracao-classificador 87c650c` → `git reset --hard origin/main`. Nada pushado durante o erro. Mergeado depois via PR (merge commit `052ef77`).

**Reforço de gate (toda sessão de código futura):** gate de abertura exige `git branch --show-current`, PARA se for `main`; relatório de fechamento do Code declara a branch do commit.

**Suíte:** 315 verde (312 baseline + 3) / mypy --strict limpo (33 files). Commit `87c650c`, merge `052ef77`.

**Próxima sessão — 002.X (CONHECIMENTO):** derivar das normas, sob D-ARQ-27, o método para os buracos remanescentes — asbesto no `_PRECEDENCIA` (existe Anexo/LEO setorial próprio?) e PNOS por faixa do Quadro 2 (DT-002N-01). Depois dos buracos fechados: PGR como teste de integração final (rodar, não implementar — o que quebrar volta pra fila).

---

## Sessão 002.X — 03/06/2026 — CONHECIMENTO (derivação normativa: asbesto-LEO + PNOS Quadro 2)

**Foco:** fechar os dois buracos do kickoff — asbesto fora do `_PRECEDENCIA` e PNOS achatado no Quadro 2 — por derivação da norma vigente (D-ARQ-27), conferida no texto literal (MTE).

**Conferência (texto literal).** Anexo III NR-07 (Portaria 567/2022) e Anexo 12 NR-15 (SSST 1/1991 + 22/1994). Periodicidades do Quadro 1 do protocolo reconfirmadas corretas.

**Buraco 2 (PNOS) — RESOLVIDO.** 4 faixas do Quadro 2 confirmadas (DT-002N-01 estava certa). Refinamentos: faixa 10–100% é evento único aos 5 anos + critério clínico (não 60M); LEO do PNOS = TLV-PNOS ACGIH 3 mg/m³ resp (nível 4). R-RX-01-pnos DEPRECATED → família de 4.

**Buraco 1 (asbesto) — RESOLVIDO.** LEO = 2,0 f/cm³ (NR-15 Anexo 12), unidade f/cm³, fixo, fração respirável. Periodicidade não muda (Quadro 1 já cobre). Exige unit-awareness no resolver. Detalhe em D-ARQ-24 changelog 002.X.

**Reauditoria crítica (2ª passada).** Achou 1 buraco grave próprio (LEO do PNOS não tratado na 1ª passada — a explosão em faixas estava sem denominador), 1 médio (carvão afirmado com "LT próprio" sem base — corrigido: LEO via ACGIH), e fronteira do demissional condicional imprecisa (corrigida: 50% / 1 vs 2 anos). PNOS-LEO só fechou após a reauditoria.

**Lacunas novas rastreadas:** DT-002X-01 (LEO carvão mineral), DT-002X-02 (vigilância pós-ocupacional asbesto 30a — 4ª dimensão temporal adiada), DT-002X-03 (NOTA 1, leitura 0/1+ → encaminhamento).

**Higiene de conformidade.** Reposta a linha de changelog da 002.W no DECISOES (D-ARQ-27 estava no corpo sem linha na tabela de revisões).

**Não implementado.** Sessão de CONHECIMENTO: tudo é especificação. Nenhuma regra a código, nenhum teste — implementação (família PNOS + LEO ACGIH/asbesto no resolver + classificador CLSC + unit-awareness, cada um com teste que falha sem a regra) é sessão de código futura.

**Suíte: 315 verde** (inalterada — sem código). **Próxima sessão:** decidir entre (a) sessão de código materializando PNOS/asbesto-LEO no resolver, ou (b) PGR como teste de integração (rodar, não implementar). Carvão (DT-002X-01) pede busca dedicada antes de virar código.

---

## Sessão 002.Y — 04/06/2026 — IMPLEMENTAÇÃO (a1-PNOS: família R-RX-01-pnos-* em código)

**Foco.** Materializar a família R-RX-01-pnos-* especificada na 002.X (Quadro 2 do Anexo III, 4 faixas) — primeira sessão de código tocando PNOS. Recorte decidido em ARQUITETURA na abertura: "a1-cheio" (4 faixas + conversão mg/m³ + injeção de fração), não "a1-núcleo" (só faixas com pct_LT sintético).

**Decisão de recorte (abertura).** Bifurcação 002.X "(a) código PNOS/asbesto-LEO vs (b) PGR como integração" recortada: 002.Y = só PNOS (a1), separado de asbesto (tem dívida própria — confirmação MTE de 2,0 f/cm³, unit-awareness f/cm³). Asbesto e carvão (DT-002X-01) ficam para sessões próprias. Leitura "(a) é pré-requisito de (b)" revalidada contra o código: parcialmente — sílica já roteia (B.2/002.W), mas PNOS do Viverde emitia 60M único (deprecated), logo materializar PNOS é pré-requisito das linhas de PNOS do (b).

**D-ARQ-29 (decidida em sessão).** PNOS injeta fração RESPIRAVEL quando ausente, não bloqueia — invariante do Quadro 2 (só mede respirável, LEO fixo 3 mg/m³ resp ACGIH), assimetria intencional com sílica (D-ARQ-24/002.V bloqueia porque lá fração é fato do laudo). Decisão inicial do Arquiteto era "a1-núcleo" (bloquear como sílica, adiar a fração); revertida na mesma sessão ao reconhecer que fração em PNOS não é grau de liberdade — é norma.

**D-ARQ-28 (proposta).** Caminho declarativo regra→lembrete operacional (`Pendencia` não-bloqueante emitida por regra). Não implementado — `emissao.py` só emite `ExameEmitido`, `R-OP-01` é string sem trilho. Caso-âncora duplo: R-OP-01 e a repetição clínica da faixa PNOS 10–100%.

**Entregue.** 6 arquivos, +241/−4, commit 9bb243e, PR #49 merge commit em main (65b8bc4):
- `leo_resolver.py` — slug PNOS + 4 níveis (n4 ACGIH 3,0 resp) + entrada _PRECEDENCIA
- `predicados.py` — `_helper_pnos` (injeta RESPIRAVEL, nunca retorna None) + 4 primitivos de faixa; import de Fracao; `pnos` binário marcado DEPRECATED
- `protocolo.py` — carregador filtra `status: DEPRECATED` (universal, não só PNOS)
- `regras.yaml` — R-RX-01-pnos → DEPRECATED (mantida, contrato de ID) + 4 entradas R-RX-01-pnos-ate10/-10a100/-acima100/-sem (INTERPRETADO)
- `test_rx_periodicidade.py` — 12 testes PNOS (faixas sintéticas, conversão mg/m³, exclusividade, dupla-emissão, sem_medicao renomeado)
- `test_protocolo_carregamento.py` — 1 teste do filtro DEPRECATED

**Fase 1 (gate antes de editar).** 3 incertos resolvidos por leitura: (1a) carregador NÃO filtrava DEPRECATED → filtro adicionado; (1b) pct_LT resolvido em stage_4 via avaliar() → testes PNOS espelham sílica; (1c) factory = build_pgr_viverde(), executar(pgr, protocolo, hoje=None). Ajuste do Code: teste do carregador usa `emite: []` (validação de exames roda sobre lista já filtrada; fixture tem exames vazio).

**Suíte: 327 verde** (315 baseline → 326 com 12 PNOS → 327 com filtro DEPRECATED). mypy --strict limpo, 13 arquivos.

**Pendências abertas.** DT-002Y-01 (lembrete 10–100% — depende de D-ARQ-28); DT-002Y-02 (validação PNOS contra Viverde real — sessão de integração); DT-002X-01 (LEO carvão, busca MTE); asbesto-LEO (confirmação MTE 2,0 f/cm³ + unit-awareness); item de processo: `.gitignore` para dumps de inspeção (`*_diff.txt`), micro-commit isolado.

**Próxima sessão.** (b) PGR Viverde como teste de integração — agora destravado do lado PNOS. Sílica já roteia, PNOS roteia; faltam asbesto (não está no Viverde) e o comportamento em contexto completo. DT-002Y-02 fecha aqui.

---

---
## Sessão 002.Z — 04/06/2026 — IMPLEMENTAÇÃO (integração Viverde: PNOS em contexto completo, DT-002Y-02)
**Foco.** Fechar DT-002Y-02: validar a família R-RX-01-pnos-* (materializada na 002.Y, testes sintéticos) contra o PGR Viverde inteiro via `executar()` — provar que os PNOS reais roteiam por faixa sem achatar e sem bloquear na presença dos demais riscos.
**Abertura.** PR #51 (`chore/abertura-002z`): `.gitignore` ignora `*_diff.txt` — item de processo aberto na 002.X, fechado. D-ARQ-30 (briefing diário informativo) não entrou — condicionado a evidência do briefing das 03:30, que só roda 05/06; texto validado aguarda aceite na próxima abertura.
**Entregue.** `agente_medico/tests/test_integracao_viverde.py` (1 teste + função diagnóstica `diagnostico_zona_cinza()` sob `if __name__ == "__main__"`, não coletada pelo pytest). Commit `9651bb3`, +144. Chama `executar(build_pgr_viverde(), carregar(_PROTOCOLO_DIR), hoje=date(2025,6,1))` — `hoje` fixo imuniza contra R-PGR-06 (validade do PGR 10/01/2025; 730 dias cruzam em 01/2027, teste viraria vermelho sozinho com `date.today()`).
**Provado (DT-002Y-02 FECHADA).** Anti-achatamento PNOS em dado real, não sintético: 6 GHEs PNOS-limpo rotearam — 5 medidos → `rx_torax_oit` 0M admissional (faixas <100% LEO: ate10/10a100, ambas admissional-único); Est-02 sem-medição → 60M. O par 0-vs-60 prova que as faixas discriminam e que a R-RX-01-pnos DEPRECATED (60M único) não está ativa. `status=PRELIMINAR` (Adm-03: ruído sem medição → Ausente bloqueante, bloqueio parcial legítimo). 32 matrizes. Suíte **328 verde** (327→328). mypy --strict limpo.
**Descoberto (→ DT-002Z-01).** Diagnóstico da zona-cinza (5 GHEs com risco coabitando PNOS): 4 GHEs sílica×PNOS (Est-07, Acab-05/06/08) bloqueiam por sílica sem fração (D-ARQ-24, case d → Ausente em todas as faixas R-RX-01-*); o `rx_torax_oit` do PNOS não emite (0 linhas) porque o orquestrador zera `linhas` no primeiro bloqueante — all-or-nothing por GHE. Est-08 (MEK+PNOS, sem sílica) NÃO bloqueia: MEK sem regra de RX OIT, PNOS roteia 0M — falso-cinza, suspeita de interferência MEK×PNOS descartada. Evidência reproduzível em `diagnostico_zona_cinza()`.
**Pendências abertas.** **DT-002Z-01 (nova)** — orquestrador all-or-nothing por GHE: primeiro risco bloqueante zera exames de outros riscos do mesmo GHE que já rotearam. Reavaliar emissão parcial (estados VÁLIDO/PARCIAL/BLOQUEADO; matriz preliminar não-apta a assinatura). Caso-âncora: Acab-05 — sílica sem fração bloqueia; o RX que o PNOS justificaria (faixa acima100 [DERIVADO, não observado: bloqueio precedeu a emissão]) some junto. Contraste observado: Est-08 roteia PNOS a 0M sem bloquear. Universal, não só sílica×PNOS. Decisão de MÉTODO resolvida por fonte documental (NR-07/09/15 vigentes + protocolo já formalizado + arquivos da Dra. Carolini em matrizes_originais/), NÃO por consulta direta à Dra. Carolini — ela valida apenas na entrega final (matrizes + leitura de FDS), não em consulta de percurso. Pergunta a derivar das fontes: GHE com um risco pendente vai ao PCMSO como parcial, ou risco pendente invalida o GHE inteiro? [INCERTO — conferir NR-07 vigente via web_search]. Binário vs tri-estado é a tradução técnica. Implica (quando decidido): contrato do orquestrador + gerador de PCMSO + auditor + regressão, mesma leva. Cross-ref: D-ARQ-28 (trilho `Pendencia` não-bloqueante, proposta) é candidato a mecanismo de sinalização; DT-002Y-01 (lembrete PNOS 10–100%) é o mesmo problema de fundo "motor diz mais que passou/travou". Manter all-or-nothing até decisão. Evidência: `diagnostico_zona_cinza()` em `test_integracao_viverde.py`. — Demais inalteradas: DT-002Y-01, DT-002X-01 (LEO carvão), asbesto-LEO (MTE 2,0 f/cm³ + unit-awareness), D-ARQ-30 (aguarda briefing).
**Próxima sessão.** DT-002Z-01 abre como CONHECIMENTO por fonte documental — derivar o método das NR-07/09/15 vigentes (conferir versão via web_search) + protocolo formalizado + material da Dra. Carolini, antes de virar ARQUITETURA (D-ARQ nova, binário vs tri-estado). Dra. Carolini valida só na entrega final, não em percurso. Asbesto e carvão seguem na fila de IMPLEMENTAÇÃO.
---

## Sessão 003.A — 05/06/2026 — CONHECIMENTO → ARQUITETURA (DT-002Z-01: contrato de saída do orquestrador — parcial vs. binário)

**Foco.** Resolver DT-002Z-01 por fonte documental: o orquestrador all-or-nothing por GHE deve emitir matriz parcial ou invalidar o GHE inteiro quando um risco bloqueia? Derivar o método da NR-07 vigente + protocolo formalizado, sem consulta de percurso à Dra. Carolini (valida só na entrega final). Caso-âncora: Acab-05 Viverde (sílica sem fração bloqueia, RX do PNOS some junto).

**Abertura.** Virada de bloco 002.Z→003.A (série A–Z esgotada; D-ARQ-26 marca a virada como cega ao kickoff). main em `5222d34`, sincronizada com `origin/main`; **328 verde** herdado (002.Z). Micro-commits de higiene (não-foco):
- **D-ARQ-30** (rotina de briefing diário informativo) aceita e gravada — número confirmado livre (DECISOES terminava em D-ARQ-29). Briefing de 05/06 provou-se útil (achou a dívida de formatação abaixo), mas rodou em sandbox sem pandas; tratado como aponta-não-afirma.
- Correção de formatação dos títulos das sessões 002.X / 002.Y / 002.Z: de negrito para cabeçalho `## Sessão ...` (3 ocorrências) — sem isso o grep de cabeçalho do kickoff para em 002.W.
- Bloco 002.Z duplicado: já fora desde `5222d34`. Nada a fazer.

**Derivado (NR-07 vigente, texto oficial gov.br).** A NR-07 (Portaria 567/2022) não legisla emissão de motor, mas fixa a postura diante de dado insuficiente/inconsistente: 7.5.1 (PCMSO elaborado considerando os riscos do PGR), 7.5.5 (reavaliar inconsistências do inventário com os responsáveis pelo PGR — reconciliar), 7.6.4 (registrar insuficiência de informação, não suprimir). Padrão normativo: sinalizar + reconciliar + registrar; nenhuma âncora para suprimir exames determinados por dado faltando em outro agente do mesmo GHE. Reforço `[VALIDADO]`: R-PGR-04/R-PGR-05 (solicitar dado, não rejeitar). All-or-nothing intra-GHE = rejeição silenciosa, contradiz a postura validada.

**Decidido (DT-002Z-01 FECHADA → D-ARQ-31).** Bloqueio é por-risco/por-linha, nunca por-GHE. `MatrizGHE` ganha `status ∈ {VÁLIDA, PARCIAL, BLOQUEADA}`; orquestrador deixa de zerar `linhas` no primeiro bloqueante (emite as determináveis + carrega as pendências); pendência bloqueante incidente sobre linha emitida fica anexada à linha (condição de segurança — mata o subdimensionamento silencioso do caso convergente sílica×PNOS, D-ARQ-22). `Resultado` global cai a PRELIMINAR se qualquer GHE for PARCIAL/BLOQUEADA (trilho D-ARQ-15 preservado; muda só a granularidade da `MatrizGHE`). Direção (parcial > binário; por-risco) `[DERIVADO — NR-07 7.5.5/7.6.4; analogia R-PGR-04/05]`; modelo tri-estado + anexação `[INTERPRETADO — prioridade na revisão de saída]`. 2ª passada adversarial: o único argumento pró-binário (subdimensionamento do caso convergente) é absorvido pela anexação à linha — não derruba o parcial. Sem R-* nova (decisão de motor). DECISOES → v29 (D-ARQ-30), v30 (D-ARQ-31); PROTOCOLO → v16 (DT-002Z-01 catalogada RESOLVIDA na seção 11).

**Nada implementado.** Sessão CONHECIMENTO→ARQUITETURA, sem código. Suíte permanece **328 verde** herdada (não medida nesta sessão). Implementação de D-ARQ-31 é multi-fatia (tipo `MatrizGHE.status` + orquestrador + dedup convergente no Stage 8 + propagação de status + auditor + regressão) — fila IMPLEMENTAÇÃO.

**Pendências abertas.** **DT-002Z-01 FECHADA.** Implementação de D-ARQ-31 entra na fila IMPLEMENTAÇÃO (primeira fatia a recortar na abertura da sessão de código: tipo `MatrizGHE.status` + orquestrador, ou Stage 8 dedup). **DH-003A-01 (nova, higiene doc, próxima abertura):** conformidade estrutural do PROTOCOLO — header "v2" desatualizado (tabela em v16) + duas seções "## 11" (renumerar a 2ª para "## 12"). Doc-only, não-bloqueante, fora do foco. Demais inalteradas: DT-002Y-01 (lembrete PNOS 10–100%, dep. D-ARQ-28), DT-002X-01 (LEO carvão), asbesto-LEO (MTE 2,0 f/cm³ + unit-awareness). Norte estratégico (estabilizar o motor): após D-ARQ-31, frente FDS lado-motor (formalizar regras químicas, fechar `quimico_nao_especificado`).

**Próxima sessão.** Implementação fatiada de D-ARQ-31 (IMPLEMENTAÇÃO) OU frente FDS lado-motor — prioridade a decidir na abertura. Gate de estado real (`git log --oneline -10`, `git status`, leitura via PowerShell dos arquivos a tocar) obrigatório antes do prompt cirúrgico.

## Sessão 003.B — 06/06/2026 — IMPLEMENTAÇÃO (D-ARQ-31 fatia 1: MatrizGHE.status tri-estado inerte)

**Foco.** Primeira fatia da implementação de D-ARQ-31: introduzir o campo `status` em `MatrizGHE` como vocabulário inerte, sem produtor. Decisão de recorte tomada na abertura (ver "Recorte").

**Abertura.** main em `2c413f7` (herdado da 003.A `642491c`); 328 verde herdado. Gate de estado real cumprido: git log/status (main limpa), localização dos tipos (`agente_medico/motor/tipos.py` linhas 126/145/153), leitura de `tipos.py`, `orquestrador.py` e `test_tipos.py` antes de fechar a spec. Branch gate disparou corretamente — Code parou em `main`, branch `feature/darq-31-fatia1-status-inerte` criada com autorização.

**Recorte (decisão de Arquiteto — refina o handoff da 003.A).** O handoff previa fatia 1 = "tipo + orquestrador deixa de zerar `linhas`". 2ª passada derrubou isso: marcar `status` mantendo o zeramento carimbaria `BLOQUEADA` em GHE que o modelo-alvo classifica como `PARCIAL` (`PARCIAL` só se distingue de `BLOQUEADA` quando há linhas determináveis presentes — e o zeramento remove exatamente essas linhas). Status correto depende de deixar de zerar; logo, status e fim-do-zeramento são inseparáveis. Recorte adotado **(a')**: fatia 1 = só o campo inerte (default `VÁLIDA`), nenhum toque no orquestrador.

**Confirmação no orquestrador real.** `MatrizGHE` é construída em TRÊS sítios de `orquestrador.py`: ramo bloqueante (`if any(p.bloqueante...)` → `linhas=[]` antes de consolidar; alvo PARCIAL), ramo `ConflitoProtocolo` (→ `linhas=[]`; alvo BLOQUEADA) e ramo sucesso (`linhas` consolidadas; alvo VÁLIDA). Assimetria real entre os dois ramos de zeramento, registrada para a fatia 2.

**Refatiamento de D-ARQ-31 (substitui o plano 2-fatias do handoff).**
- Fatia 1 (FEITA): campo `MatrizGHE.status` inerte.
- Fatia 2: orquestrador deixa de zerar `linhas` + produtor de status (VÁLIDA/PARCIAL/BLOQUEADA, respeitando a assimetria dos três sítios) + propagação `Resultado.status`.
- Fatia 3: anexação pendência-à-linha (D-ARQ-22) + dedup convergente Stage 8 (Acab-05 sílica×PNOS).
- Fatia 4: auditor + regressão Viverde.
Nota para a fatia 2: `MatrizGHE` é construída em TRÊS sítios; o produtor de status tem de setar `status` explicitamente nos três — não confiar no default `VÁLIDA` no ramo de sucesso, senão o default vaza por omissão em vez de ser afirmado por intenção.

**Implementado.** `agente_medico/motor/tipos.py`: campo `status: Literal["VÁLIDA","PARCIAL","BLOQUEADA"] = "VÁLIDA"` em `MatrizGHE`, com comentário de rastreabilidade D-ARQ-31. `agente_medico/tests/test_tipos.py`: 2 testes novos (`test_matriz_ghe_status_default_valida`, `test_matriz_ghe_status_aceita_tri_estado`). `orquestrador.py` NÃO tocado.

**Verificação.** Suíte completa (`agente_medico/tests/ + tests/`): 328 → **330 verde** (+2, zero regressão). Motor novo isolado: 181. mypy --strict em `tipos.py`: limpo. Commit `7a188de` na branch; merge `2c413f7` em main via PR #54 ("Create a merge commit").

**Decisão de processo (D-ARQ-32).** Gravada nesta sessão: handoff é a 4ª entrega do ritual de encerramento. Emenda a D-ARQ-26/SKILL.md considerada e descartada — garantia via solicitação do Diovanni no encerramento de cada chat. Ver DECISOES v31.

**Pendências abertas.** D-ARQ-31 fatias 2/3/4 na fila IMPLEMENTAÇÃO (próxima: fatia 2 — orquestrador para de zerar + produtor de status + propagação; gate de estado real obrigatório, reler `orquestrador.py` real pois linhas mudam após merges). Demais inalteradas: DH-003A-01 (higiene doc PROTOCOLO — header "v2" vs tabela v16; duas seções "## 11"), DT-002Y-01 (PNOS 10–100%, dep. D-ARQ-28), DT-002X-01 (LEO carvão), asbesto-LEO. Norte estratégico: após D-ARQ-31, frente FDS lado-motor.

**Próxima sessão.** D-ARQ-31 fatia 2 (IMPLEMENTAÇÃO). Gate de estado real obrigatório antes do prompt cirúrgico.

## Sessão 003.C — 06/06/2026 — IMPLEMENTAÇÃO (D-ARQ-31 fatia 2: orquestrador para de zerar + produtor status tri-estado)

**Foco.** Segunda fatia de D-ARQ-31: dar vida ao campo `MatrizGHE.status` (inerte desde a fatia 1). Consolidação passa a rodar SEMPRE; produtor de status carimba VÁLIDA/PARCIAL/BLOQUEADA por intenção.

**Abertura.** main em `13bc09e` (Merge PR #55, fechamento docs 003.B); 330 verde herdado (181 motor novo isolado). Gate de estado real cumprido: leitura de `orquestrador.py`, `tipos.py`, `test_orquestrador.py`, `consolidacao.py`, `emissao.py` e `predicados.py` reais antes de fechar a spec. Branch gate disparou — Code parou em `main`, branch `feature/darq-31-fatia2-produtor-status` criada com autorização.

**Decisão de recorte (refina o handoff).** O handoff previa propagação `Resultado.status→PRELIMINAR` dentro da fatia 2. 2ª passada contra o orquestrador real derrubou: `executar` JÁ mapeia `houve_bloqueio→PRELIMINAR` e reserva REJEITADO ao gate Stage 1 (coerente com a cláusula 4 do corpo de D-ARQ-31; D-ARQ-15 intocado). A propagação não precisava mudar — removida da fatia. Regra de agregação multi-GHE proposta na abertura (todas BLOQUEADA→REJEITADO) descartada na 2ª passada: contrariava D-ARQ-15 e o código vigente.

**Refinamento de D-ARQ-31 (sítios de construção).** O "TRÊS sítios" citado no handoff e no bloco 003.B refere-se à estrutura ANTIGA do orquestrador (ramo bloqueante separado que pulava a consolidação). Pós-fatia 2 são DOIS sítios de construção de `MatrizGHE`: o `except ConflitoProtocolo` (→ BLOQUEADA) e o `else`, que ramifica em três valores de status (sem bloqueio→VÁLIDA; bloqueio+linhas→PARCIAL; bloqueio+sem linhas→BLOQUEADA). Ver DECISOES (nota de implementação sob D-ARQ-31). Não procurar um terceiro sítio: deixou de existir.

**Implementado.** `agente_medico/motor/orquestrador.py`: bloco `if any bloqueante / else` substituído — `stage_8_consolidacao` roda sempre (inclusive sob pendência bloqueante), permitindo distinguir PARCIAL (linhas determináveis presentes) de BLOQUEADA (nenhuma linha); status setado por string literal direta no construtor (sem variável intermediária, sem import de `Literal` no orquestrador). `agente_medico/tests/test_orquestrador.py`: 3 testes novos (`test_ghe_status_valida`, `test_ghe_status_bloqueada_sem_linhas`, `test_ghe_parcial_linhas_presentes_com_bloqueio`). O teste PARCIAL é o falha-sem/passa-com da fatia, ancorado em fixtures de testes verdes pré-existentes (`test_ghe_sem_bloqueio_ok` para `trabalho_altura`→5 linhas; `test_dois_ghes_um_bloqueia` para `ruido`→`Ausente`).

**Verificação.** Motor novo isolado: 181 → **184** (+3). Suíte completa (`agente_medico/tests/ + tests/`): 330 → **333** (+3, zero regressão). mypy --strict em `agente_medico/motor`: limpo (13 arquivos). Commit `76d5de1` na branch; merge `d0a68d4` em main via PR #56 ("Create a merge commit").

**Paliativo registrado.** Linha PARCIAL carrega a pendência bloqueante só no nível da matriz, não anexada à linha específica (D-ARQ-22 / fatia 3). Não é erro silencioso — `status="PARCIAL"` denuncia incompletude. PARCIAL-sem-âncora-de-linha existe transitoriamente em main entre fatias 2 e 3, aceito conscientemente.

**Pendências abertas.** D-ARQ-31 fatias 3 (anexação pendência-à-linha D-ARQ-22 + dedup convergente Stage 8, Acab-05 sílica×PNOS) e 4 (auditor + regressão Viverde) na fila IMPLEMENTAÇÃO. Demais inalteradas: DH-003A-01 (higiene doc PROTOCOLO — header "v2" vs tabela v16; duas seções "## 11"), DT-002Y-01 (PNOS 10–100%, dep. D-ARQ-28), DT-002X-01 (LEO carvão), asbesto-LEO. Norte estratégico: após D-ARQ-31, frente FDS lado-motor.

**Próxima sessão.** D-ARQ-31 fatia 3 (IMPLEMENTAÇÃO) OU frente FDS lado-motor (CONHECIMENTO/ARQUITETURA) — prioridade a decidir na abertura. Gate de estado real obrigatório antes do prompt cirúrgico.

## Sessão 003.D — 07/06/2026 — IMPLEMENTAÇÃO (D-ARQ-31 fatia 3: anexação pendência-à-linha)

**Foco.** Cláusula 3 de D-ARQ-31: pendência bloqueante com âncora de exame anexa-se à linha emitida, não fica solta no GHE. Materializa a condição de segurança (piso nunca sem teto visível).

**Abertura.** main em `6f9302a` (PR #57, fechamento docs 003.C); 333 verde herdado (184 isolado). Gate de estado real cumprido: leitura de `tipos.py`, `orquestrador.py`, `estagios/consolidacao.py`, `estagios/emissao.py`, `predicados.py`, `regras.yaml`, `test_orquestrador.py`, `test_integracao_viverde.py` reais; DECISOES integral (D-ARQ-22/24/29/31). Caminhos corrigidos a meio: Stage 5/8 vivem em `estagios/`, não em `motor/` direto. Branch gate disparou — Code parou em `main`, branch `feature/darq-31-fatia3-anexacao` criada com autorização.

**Achados das passadas de revisão (4 passadas antes do prompt).** (1) O "dedup convergente Stage 8" do handoff não tem caso-âncora vivo — a sílica bloqueada não emite linha, logo Stage 8 vê um único `rx_torax_oit`; anexação é passo NOVO pós-emissão, não mudança no merge. Recortado para fila. (2) A linha do RX já existe desde a fatia 2 (consolidação roda sempre); a fatia 3 só MOVE a pendência para a linha — o teste é sobre anexação, não sobre recuperar exame. (3) `diagnostico_zona_cinza()` real revelou: 4 GHEs sílica+PNOS anexam (Acab-05 piso 60M `pnos-acima100`; Acab-06/08, Est-07 piso 0M `pnos-10a100`), cada um com 5 pendências da família sílica; Est-08 é controle (sem sílica, VÁLIDA). Corrigiu o exemplo canônico do D-ARQ ("admissional" → 60M no Acab-05). (4) `ExameEmitido` com `list` mutável exigiu propagar `pendencias_anexadas` no construtor de cópia E no merge do Stage 8 (bomba-relógio para fatia futura que anexe antes do Stage 8).

**Implementado.** `tipos.py`: `Pendencia.exames_alvo: tuple[str,...]=()` + `ExameEmitido.pendencias_anexadas: list[Pendencia]`. `emissao.py`: carimbo de `exames_alvo` no caminho `Ausente`. `estagios/anexacao.py` (novo): `anexar_pendencias` puro, move por interseção slug×linha, devolve `(linhas, bloqueantes_restantes)`. `estagios/consolidacao.py`: propaga `pendencias_anexadas` no construtor de cópia e no extend do merge. `orquestrador.py`: anexação no `else` pós-Stage-8, status tri-estado recomputado depois, `houve_bloqueio` derivado de `m.status`, `tem_bloqueio` órfã pré-`try` removida. Testes: `test_anexacao.py` (5 unit, inclui salvaguarda piso-nunca-sem-teto); `test_orquestrador.py` (`test_ghe_parcial` redirecionado à linha); `test_integracao_viverde.py` (`test_acab05...` falha-sem/passa-com + Adm-03 redirecionado).

**Dois bloqueadores na verificação (Code parou, Arquiteto decidiu).** (1) `test_integracao_viverde_pnos_roteia_sem_achatar` quebrou no Adm-03: a premissa da spec "Adm-03 não é atingido" estava errada — ruído sem medição anexa à audiometria. Comportamento correto da fatia 3; asserção redirecionada à linha + espelho "não resta solto". Evidência de universalidade. (2) mypy: variável intermediária `status: str` alargava o `Literal` de `MatrizGHE`. Voltou ao padrão da fatia 2 (string literal direta em três construtores, sem variável). Ambos corrigidos; sem terceiro caso stale.

**Verificação.** Suíte completa (`agente_medico/tests/ + tests/`): 333 → **339** (+6: 5 anexação + 1 Acab-05; `test_ghe_parcial` e Adm-03 atualizados, não somam). Isolado: 184 → **190**. mypy --strict `agente_medico/motor`: limpo (14 arquivos). Commit `f25cd48` na branch; merge `f1cb412` em main via PR #58 ("Create a merge commit").

**Pendências abertas.** D-ARQ-31 fatia 4 (auditor da invariante global piso-sem-teto + regressão Viverde dos 32 GHEs) na fila IMPLEMENTAÇÃO — fecha o arco. Dedup convergente Stage 8: item próprio (mudança de comportamento do `ConflitoProtocolo`, decisão própria). Demais inalteradas: DH-003A-01 (higiene doc PROTOCOLO header v2→v16; 2ª "## 11"), DT-002Y-01 (lembrete PNOS, dep. D-ARQ-28), DT-002X-01 (LEO carvão), asbesto-LEO, R-RX-02/DT-D3-02 (fumos sem âncora). Norte: após fatia 4, frente FDS lado-motor.

**Próxima sessão.** D-ARQ-31 fatia 4 (IMPLEMENTAÇÃO) — auditor + regressão Viverde, fecha o arco. FDS lado-motor na seguinte, com o motor selado. Gate de estado real obrigatório (reler `anexacao.py` novo, `orquestrador.py` e `test_integracao_viverde.py` alterados pós-merge).
