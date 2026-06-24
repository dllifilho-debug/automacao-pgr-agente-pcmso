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

## Sessão 003.E — 07/06/2026 — IMPLEMENTAÇÃO (D-ARQ-31 fatia 4: auditor + regressão tri-estado — fecha o arco)

**Foco.** Fatia 4 de D-ARQ-31, a última: auditor da invariante piso-sem-teto + regressão Viverde tri-estado. Verificação de mecânica já implementada (fatias 1-3), não muda motor — só adiciona rede de regressão. Fecha o arco D-ARQ-31.

**Abertura.** Dois ambientes no mesmo HEAD `12ba1cf` (kickoff local: main + 36 untracked matrizes_originais/; briefing sandbox: branch própria, clone limpo) — não-divergência, registrada. 339/190 herdado pré-sessão. Foco IMPLEMENTAÇÃO declarado (handoff + sequenciamento endossado: fatia 4 sela o motor → FDS lado-motor depois). Gate de estado real: DECISOES (D-ARQ-31 integral + fronteiras 08/15/16/22), orquestrador.py, anexacao.py, test_integracao_viverde.py, tipos.py — todos lidos reais via Get-Content -Encoding UTF8. Branch gate disparou: Code parou em main, feature/darq-31-fatia4-auditor criada com autorização (artefato `already exists` na 2ª execução do -b; reflog + log main..feature vazio confirmaram criação correta do HEAD, sem desvio).

**Decisão de abertura (auditor: teste ou motor?).** Resolvida por leitura do código: CAMADA DE TESTE, não motor/. A invariante é garantida por construção por `anexar_pendencias` (não há ramo piso-sem-teto), logo o risco é regressão futura no código (papel de teste), não input malformado; auditor em produção só somaria modo de falha a motor determinístico. Forma do retorno corrigida pela leitura de tipos.py: `ViolacaoPisoSemTeto` frozen de campos só-str (ExameEmitido é mutável → não serve a == estável). Realocação de peso na 3ª passada: o auditor é rede estreita (sobre saída real sempre []; cobre só regressão da anexação fatia 3), a regressão Viverde dirigida é o que fecha o arco (cobre o reachatar da fatia 2). Complementares, não redundantes — razão técnica das duas entregas.

**Lição 003.D aplicada (zona cinza assertiva).** Não cravei Acab-06/08, Est-07, Est-08 de memória. Code rodou diagnostico_zona_cinza() real, instrumentado em duas rodadas: 1ª imprimia só bloqueou+periodicidade (cego a status/anexadas — Code sinalizou a lacuna honestamente e parou); 2ª instrumentou status + pendencias_anexadas. Confronto ponto-a-ponto bateu integralmente. ACHADO: Est-08 não era "controle sem linha rx" como o handoff dizia — emite rx pela faixa PNOS branda (pnos-ate10) mas sem família sílica anexada → VÁLIDA. A família R-RX-01-pnos-* é governada por PNOS, não sílica. Asserção mede o status real (VÁLIDA confirmada por anexada==[]), não o crava.

**Implementado.** `agente_medico/tests/invariantes.py` (novo): `ViolacaoPisoSemTeto` (frozen, 4 campos str) + `auditar_invariante_piso_teto` puro. `test_invariante_piso_teto.py` (novo): 4 sintéticos — violação fabricada detectada, anexação correta não-viola, BLOQUEADA sem linha não-viola, Tipo A sem âncora não-viola. `test_integracao_viverde.py` (alterado): diagnóstico instrumentado (status + anexadas); auditor global sobre Viverde (==[]); contagem tri-estado dos 32 por invariantes derivadas (soma==32, PARCIAL≥4, VÁLIDA≥1, BLOQUEADA==0); zona cinza assertiva (Acab-06/08/Est-07 família⊆anexadas + não-solta + PARCIAL); Est-08 VÁLIDA. Sem cravar periodicidade exceto Acab-05.

**Sem bloqueadores na verificação.** Fatia limpa: nenhuma parada do Code além dos gates planejados (abertura + diagnóstico 3a). Sem stale, sem mypy a corrigir.

**Verificação.** Suíte completa: 339 → **347** (+8: 4 sintéticos + 4 integração). Isolado (agente_medico/tests/): 190 → **198** (medido pós-merge, não estimado). mypy --strict agente_medico/motor + invariantes.py: limpo (15 arquivos). Commit `6f80f46`; merge `fa11ba3` em main via PR #60 ("Create a merge commit", fast-forward 12ba1cf..fa11ba3).

**Pendências abertas.** Arco D-ARQ-31 FECHADO (fatias 1→4). Norte: frente FDS lado-motor, com o motor de bloqueio selado. Inalteradas: dedup convergente Stage 8 (item próprio, sem caso-âncora vivo; determinado×determinado emitindo mesmo exame com periodicidades distintas → escolha de piso em vez de `raise ConflitoProtocolo` [INTERPRETADO — comportamento atual do Stage 8 não relido nesta sessão; reler consolidacao.py ao abrir o item]); DH-003A-01 (higiene header PROTOCOLO v2→v16, 2ª "## 11"); DT-002Y-01 (lembrete PNOS, dep. D-ARQ-28); DT-002X-01 (LEO carvão); asbesto-LEO 30 anos pós-ocupacional; R-RX-02/DT-D3-02 (fumos sem âncora); DT-002V-01 (semântica CLSC vs média).

**Próxima sessão.** Frente FDS lado-motor (CONHECIMENTO/ARQUITETURA) — formalizar regras químicas do legado (`modules/modulo_engenharia.py` dicionário-H/matriz → protocolo → regras determinísticas), fechar quimico_nao_especificado. Primeiro passo: ler modulo_engenharia.py E modulo_auditor_v1_1.py reais (Get-Content -Encoding UTF8) — aproveitar o CONHECIMENTO químico validado (mapeamentos CAS→risco), não portar o CÓDIGO (acoplado a Streamlit, mistura extração+decisão, viola D-ARQ-09). Distinção registrada na 003.E. Gate de estado real obrigatório.

## Sessão 003.F — 07/06/2026 — CONHECIMENTO (frente FDS aberta: reenquadramento + conferência Anexo I)

**Foco.** Primeira sessão da frente FDS lado-motor, com o arco D-ARQ-31 fechado (motor de bloqueio selado). CONHECIMENTO: ler o legado como norma, conferir a base normativa do biomonitoramento químico, abrir o estudo da frente. Sem código, sem mudança de motor.

**Reenquadramento central (Diovanni).** O projeto é o par ENGENHEIRO/HIGIENISTA → MÉDICO: dois agentes seniores, ofícios distintos. O engenheiro produz a base do PGR (inventário de risco por GHE, a partir da FDS); o médico produz a base do PCMSO (matriz de exames). `tipos.PGR` (D-ARQ-25) é A MESA entre os dois. A frente FDS = construir o LADO-ENGENHEIRO, hoje preso ao legado Streamlit (`modulo_engenharia.py`), acoplado errado. Correção de leitura do Arquiteto ao longo da sessão: o ativo não é a tabela de 15 CAS (cache), é o RESOLVEDOR CAS→ficha com auto-descoberta + humano no loop.

**Leitura do legado como norma (não portar — D-ARQ-09).** `modulo_engenharia.py`: a ideia a manter é o `buscar_ou_descobrir_cas` (resolve CAS, descobre via Gemini quando desconhecido) + revisão humana (`contenteditable`). `modulo_auditor_v1_1.py`: confirmado paradigma cargo→matriz legado (oposto ao motor GHE/risco), só `normalizar_exame` aproveitável como nomenclatura. Os dicionários DICIONARIO_H/MATRIZ_OFICIAL são grade de risco do PGR — motor consome, não recalcula (D-ARQ-21).

**Saída real de FDS (provada empiricamente).** Execução do legado sobre FDS de pintura (65 agentes): a auto-descoberta FUNCIONA (50 dos 65 fora do dicionário) E É PERIGOSA — 6 CAS fantasma (regex `\d{2,7}-\d{2}-\d` captura nº de seção; Gemini alucina "Formaldeído"/"carcinógeno" sobre lixo: `022-00-9`, `014-00-0`, etc.), prob. fixa em 3 (risco vira só perigo da frase H), sem cutoff de concentração, biomarcador como texto livre sem IBMP, duplicatas por CAS divergente (`136-51-6`/`136-53-8`), e falha em agentes reais conhecidos (cumeno/etilbenzeno/n-butanol = "NAO MAPEADO"). Lição: confinar a descoberta à extração (a montante, fora do motor puro) + Pendencia (D-ARQ-14) + revisão humana; nunca dado validado direto (D-ARQ-09/22). É a versão-FDS da revisão-de-saída do D-ARQ-22.

**Conferência normativa (texto oficial MTE, Portaria 567/2022 — NR-07 Anexo I + corpo 7.5).** Disparada por proposta do Perplexity (estudo aprofundado colado pelo Diovanni) que apontou os dois quadros do Anexo I. Conferido contra o PDF oficial gov.br, não fonte secundária:
- Eixo do biomonitoramento químico = QUADRO 1 (IBE/EE — só periódico, 7.5.15) vs QUADRO 2 (IBE/SC — dispara conduta CAT/afastamento, 7.5.19.5), AMBOS dentro do Anexo I. NÃO é "Anexo I/II" (Anexo II na NR vigente = ruído). Ambos 6M ±45d (7.5.13); sazonal pode ser anual (7.5.14).
- Quatro colunas propostas pelo Perplexity, julgadas: `tipo_ibe {EE,SC}` ACEITA `[DERIVADO]`; `periodicidade 6M + janela ±45d` ACEITA `[DERIVADO 7.5.13]`; `momento_coleta` ACEITA e mais forte (códigos FJ/FS/AJ JÁ no Anexo, agente a agente, obrigatório por 7.5.12.1); `gatilho NA-NR9` REJEITADA como coluna — é PREDICADO (cruza Quantificacao×agente, 7.5.12 b), não atributo da ficha.
- IBMP confirmado como dado de 1ª classe, com tabela-fonte real no Anexo I (Quadro 1 lido integral).
- Conduta-por-resultado (chumbo (M) Pb-S≥30 → afasta) = LEMBRETE OPERACIONAL (D-ARQ-05), não disparador de motor (D-ARQ-09) — mesma natureza de DT-002X-03.
- Cutoff de 5% (R-FDS-03): NÃO tem âncora NR — regra de projeto (GHS/ABNT 14725) ou conduta Carolini. `[VALIDADO]` como conduta dela, não `[DERIVADO]`.

**ACHADO PESADO — DT-FDS-01.** R-BIO-02 `[VALIDADO]` está CONTRADITO pela norma vigente: rótulo "Anexo I/II" desatualizado (pré-567/2022), critério "carcinógeno sem LT" errado, semântica de 5 momentos sem âncora. Pela convenção de versionamento, reabertura exige nova ID + DEPRECATED — mas NESTA sessão NÃO: exige o Quadro 2 lido inteiro (não lido), é lado-médico (não FDS), decisão de reabrir é do Diovanni. Registrada como DT ABERTA (sinalizada, não silenciosa). Posição do benzeno NÃO cravada (carcinógeno IARC 1 — pode estar em Quadro 2 e/ou Anexo V; conciliar com R-PKG-BZ na reabertura). R-CLI-02/03 sob suspeita do mesmo rótulo (apontamento-irmão).

**Decisões de arquitetura — NÃO fechadas (vão para o estudo da próxima sessão).** Lado-engenheiro = motor irmão (inclinação do Arquiteto, reforçada por NR-9: classificar risco é ato técnico do empregador, reavaliável com o médico 7.5.5) — a consolidar. Contrato da mesa, fronteira da descoberta, sinergia/alvo-órgão (fora de escopo de regra, apoio à decisão) — idem. Nenhuma vira D-ARQ nesta sessão; o estudo da FDS é que fecha.

**Verificação.** Sem código. Suíte inalterada (347 completa / 198 isolado — não rodada, não tocada). Sem mudança de motor, DECISOES intocado.

**Pendências abertas.** DT-FDS-01 (R-BIO-02 contradito — reabertura em sessão própria). Estudo da frente FDS não escrito (a conferência mudou sua fundação — escrever sobre [DERIVADO], não [INCERTO]). Inalteradas: dedup convergente Stage 8, DH-003A-01 (header PROTOCOLO; agora há 2ª "## 11" + revisar), DT-002Y-01, DT-002X-01, asbesto-LEO, R-RX-02/DT-D3-02, DT-002V-01.

**Próxima sessão.** Frente FDS (CONHECIMENTO→ARQUITETURA): ESCREVER O ESTUDO DA FRENTE FDS sobre a fundação verificada. Quatro eixos: (1) lado-engenheiro camada vs. motor irmão; (2) contrato da mesa com as colunas conferidas; (3) cutoff 5% e carcinógeno-independe (procedência); (4) sinergia/alvo-órgão (escopo declarado). NÃO reabrir R-BIO-02 aqui (sessão própria, exige Quadro 2). Ler docs vivos inteiros antes.

## Sessão 003.G — 08/06/2026 — CONHECIMENTO→ARQUITETURA (estudo da frente FDS: motor irmão + contrato da mesa)

**Foco.** Escrever o estudo da frente FDS sobre a fundação verificada na 003.F (Anexo I / 567/2022). Quatro eixos. Sem código.

**Achado de abertura — "347 verde" não estava medido.** A 003.F propagou 347 completa / 198 isolado como herdado, marcado "não rodada". Rodado no container: motor isolado 198/198 VERDE; suíte completa 1 falha (`tests/test_regressao_pcmso.py::TestCabecalho::test_cabecalho_preenchido_docx`) por artefato de ambiente (`python-docx` ausente → fallback CSV), não regressão — nada em f25cd48..ded00d9 toca geração de docx. Nota processual, não DT: reconfirmar na máquina do Diovanni; parar de carregar contagem sem medir.

**Eixo 1 — motor irmão (três passadas).** Lado-engenheiro = MOTOR IRMÃO, estreitado por refinamento adversarial. 1ª recomendação ("classifica risco") derrubada na 3ª passada: arrisca duplicar regra médica. Versão final: resolução determinística de COMPOSIÇÃO QUÍMICA (fichas→ProdutoQuimico), conduta toda no lado-médico. Topologia: extração LLM (descoberta CAS) → motor irmão (det.) → tipos.PGR (mesa entre ofícios) → motor médico. Refina D-ARQ-25 (fronteira = ofícios, não LLM/det.). Vira D-ARQ-33.

**Eixo 2 — contrato da mesa.** Ficha de agente químico = extensão de agentes.yaml (D-ARQ-12), ZERO ID de regra novo. Colunas: cas validado (check-digit), tipo_ibe {EE,SC}, ibmp, momento_coleta, flags de perigo, orgao_alvo. Check-digit CAS como gate de admissão — verificado que pega os fantasmas 022-00-9/014-00-0 da 003.F. Fronteira fina: ficha carrega tipo_ibe (dado, esta frente); regra que o consome é R-BIO-02-sucessora (DT-FDS-01, sessão própria). Periodicidade NÃO entra (R-BIO-01 já universal; ±45d é agendador). Rejeitado como coluna: NA-NR9 (é predicado, 7.5.12 b).

**Eixo 3 — cutoff 5% (caminho C).** Limiar 5% = dado (constante de protocolo, [VALIDADO] conduta Carolini, sem âncora NR); materialidade = predicado tri-estado derivado, não atributo armazenado. Dois consumidores (médico R-FDS-03; engenheiro pós-D-ARQ-33). (C) é carrega-tudo-e-marca, NUNCA filtro de entrada (supressão = D-ARQ-22/D-ARQ-31). Faixa cruzando cutoff → Ausente/pendência. Generalizado: bypasses do cutoff são LISTA (carcinógeno + sensibilizante + frase-H), não binário — furo achado via caso-saúde (glutaraldeído/isocianato <5% sumiria). R-FDS-03/04 mesma ID, só nota de procedência.

**Eixo 4 — sinergia/órgão-alvo.** Fora de escopo de regra (Anexo I opera por agente isolado), declarado não omisso. orgao_alvo = dado de apoio à decisão, nunca disparador.

**Conferência normativa (web, fonte secundária — marcada).** Glossário momento_coleta: códigos FJ/FS/AJ/FJFS confirmados EM USO agente-a-agente (mercúrio metálico=AJ), significado literal NÃO cravado de secundária [INCERTO — PDF oficial]. Reforço do eixo IBE/EE vs IBE/SC confirmado. TDI/isocianato com IBE/EE no Quadro 1 visto só em secundária [INCERTO].

**Verificação.** Sem código. Suíte: motor isolado 198/198; completa 339 verde + 1 falha-de-ambiente (não regressão). DT-FDS-01 NÃO reaberta (trilho respeitado). Arco D-ARQ-31 intocado.

**Pendências abertas.** D-ARQ-33 carrega: gap de tipo Componente.concentracao a conferir no git (implementação); glossário momento_coleta [INCERTO — PDF oficial]; TDI no Quadro 1 [INCERTO]; validação caso-químico (D-ARQ-06). DT-FDS-01 (R-BIO-02, sessão própria). Inalteradas: dedup convergente Stage 8, DH-003A-01 (2ª "## 11"), DT-002Y-01, DT-002X-01, asbesto-LEO, R-RX-02/DT-D3-02, DT-002V-01.

**Próxima sessão.** Decisão do Diovanni na abertura. Candidatos: (a) reabertura R-BIO-02 (DT-FDS-01) — exige Quadro 2 inteiro lido no PDF oficial, lado-médico; (b) protocolo-engenheiro pós-D-ARQ-33 (formalizar materialidade do lado-engenheiro, bypasses do cutoff); (c) implementação D-ARQ-33 fatia 1 (extensão de tipos + agentes.yaml). Ler docs vivos inteiros antes.

## Sessão 003.H — 09/06/2026 — ARQUITETURA (protocolo-engenheiro: materialidade do lado-engenheiro, D-ARQ-34)

**Foco.** Escrever o consumidor-engenheiro da materialidade que D-ARQ-33 cláusula 5 deixou declarado e não escrito (candidato (b) da 003.G). Sem código.

**Gate de abertura — divergência git resolvida.** Kickoff (máquina real) e briefing (container) divergiram no git: kickoff = `main` em `a762f38` sincronizado com `origin/main`; briefing = branch `claude/stoic-bohr-7viqj4` sem upstream, "24 commits ahead" de um `origin/main` em `5222d34` (pré-003.x). `git fetch origin` + `git log origin/main` na máquina real confirmaram `a762f38 (HEAD -> main, origin/main, origin/HEAD)`, working tree limpa (untracked só `matrizes_originais/`). Briefing era artefato de container (clone com origin defasado). Doc 2 (kickoff) venceu — 003.G durável no remoto, nada a recuperar. Fechamento da 003.G (handoff previa prompt de gravação como 1ª ação) confirmado já no log: `403d730` + `a762f38`.

**Achado de abertura — gap-de-tipo vira gap-de-forma.** D-ARQ-33 mandava conferir no git se `Componente.concentracao` existe (a materialidade-predicado o exige; D-ARQ-25 Parte C lista `cas`, não concentração). Conferido: o campo EXISTE (`tipos.py:33`), porém como `Optional[float]` ESCALAR. Gap documentado (campo ausente) fechado; gap real (forma) aberto — escalar é ponto, não enxerga faixa, e a cláusula 3 de D-ARQ-33 exige que faixa cruzando o cutoff vire Ausente/Pendencia. Gêmeo de DT-002V-01 (`Quantificacao.valor` escalar que não discrimina a estatística).

**D-ARQ-34 — três passadas adversariais.** (1ª) Forma: concentração vira FAIXA `(min,max)` espelhando valor+qualificador de `Quantificacao`; sentinelas para faixas semi-abertas da FDS ("< 5%"=`(None,5)`, "> 1%"=`(1,None)`). (2ª) Árvore tri-estado {MATERIAL, NÃO-MATERIAL, AUSENTE} espelhando D-ARQ-13; FURO achado — faltava o caso de vocabulário ausente: carcinógeno desconhecido <5% cairia em NÃO-MATERIAL por concentração isolada (supressão silenciosa, D-ARQ-22). Adicionado ramo de vocabulário-ausente→AUSENTE; borda 5,0 rebaixada a [INTERPRETADO] (depende da unidade do cutoff). (3ª) Localização na pipeline: o ramo da 2ª passada fundia duas etapas — CAS inválido é GATE de admissão (D-ARQ-33 cl.3, a montante), não ramo da materialidade. Reescopado: pré-condição "gate-CAS precede materialidade" + ramo 0 = "CAS válido mas slug não resolvido" → AUSENTE BLOQUEANTE. As três passadas convergiram (forma → árvore → ordem), cada uma fechando a costura da anterior — sinal de convergência, não de mais camadas.

**D-ARQ-34 — forma final (4 partes).** (1) concentração faixa `(min,max)` + sentinelas (min=None→0, max=None→+∞); forma do tipo (sub-objeto frozen vs. par de campos) é decisão da implementação, recomendado frozen. (2) predicado tri-estado, pré-condição gate-CAS + ramos 0–5 (0=slug ausente→AUSENTE bloqueante; 1=bypass→MATERIAL; 2=concentração ausente→AUSENTE; 3=straddle `min≤5<max`→AUSENTE; 4=`min>5`→MATERIAL; 5=`max≤5`→NÃO-MATERIAL); borda 5,0 [INTERPRETADO] (DT-FDS-02). (3) bypasses = lista de flags append-only em `agentes.yaml`: `is_carcinogeno_iarc` (existe), `is_sensibilizante` (nova), frase-H sob demanda; POPULAÇÃO de is_sensibilizante é tarefa de dado, não arquitetura. (4) predicado puro `(faixa,flags)→{...}` por lado; flags via ficha JÁ NORMALIZADA (extração resolve CAS→slug→flags), motor irmão puro sobre a ficha (D-ARQ-09); NÃO-MATERIAL não descarta (carrega-e-marca, cláusula 5 de D-ARQ-33 / anti-supressão D-ARQ-31).

**DT-FDS-02 aberta.** Unidade do cutoff de 5% (% m/m vs v/v) — straddle compara grandezas iguais só se cutoff e concentração na mesma base. ABNT NBR 14725 tipicamente % m/m, não conferido no texto oficial. Borda 5,0 fica [INTERPRETADO] até confirmar. Lado-engenheiro, independente de DT-FDS-01. Não bloqueia.

**Trilho respeitado.** D-ARQ-34 para na materialidade; NÃO derivou momentos de `tipo_ibe` (R-BIO-02-sucessora = DT-FDS-01, lado-médico, sessão própria). DT-FDS-01 NÃO reaberta. Arco D-ARQ-31 intocado. Nenhuma regra clínica criada/alterada (R-FDS-03/04 intactas) — D-ARQ-34 é contrato de dado + motor.

**Verificação.** Sem código. Suíte não rodada nesta sessão (ARQUITETURA pura); última medição real herdada (003.G/container): motor isolado 198/198; completa 339 verde + 1 falha-de-ambiente (python-docx ausente, não regressão) — reconfirmar no kickoff na máquina real.

**Pendências abertas.** D-ARQ-34 carrega: GATE DE ESTADO REAL na implementação (grep `.concentracao` no motor antes de prompt cirúrgico — migração Optional[float]→faixa toca quem lê o campo); DT-FDS-02 (unidade do cutoff); forma do tipo (frozen vs. par). Herdadas de D-ARQ-33: glossário momento_coleta [INCERTO — PDF oficial]; TDI no Quadro 1 [INCERTO]; validação caso-químico (D-ARQ-06). DT-FDS-01 (R-BIO-02, sessão própria). Inalteradas: dedup convergente Stage 8, DH-003A-01 (2ª "## 11"), DT-002Y-01, DT-002X-01, asbesto-LEO, R-RX-02/DT-D3-02, DT-002V-01.

**Próxima sessão.** Decisão do Diovanni na abertura. Candidatos: (c) implementação D-ARQ-34 (faixa em tipos.py + predicado tri-estado + flag is_sensibilizante como mecanismo + pré-condição gate; gate de estado real obrigatório; espec fechada); (a) reabertura R-BIO-02 (DT-FDS-01) — CONHECIMENTO, lado-médico, exige Quadro 2 inteiro no PDF oficial MTE. Ler docs vivos inteiros antes.

## Sessão 003.I — 10/06/2026 — IMPLEMENTAÇÃO (D-ARQ-34 fatia 1: concentração vira faixa)

**Foco.** Materializar a Parte 1 de D-ARQ-34 — `Componente.concentracao` de `Optional[float]` escalar para faixa `(min,max)`. Candidato (c) da 003.H. Só Parte 1; predicado/flags/gate-CAS (Partes 2–4) ficam para a fatia 2.

**Gate de estado real — fechado, blast radius nulo.** Grep `.concentracao` no motor: dois hits, ambos inertes — definição em `tipos.py:33` e construção nomeada em fixture (`test_stage_3:47`, `concentracao=None`). ZERO leituras `.concentracao` em qualquer estágio (predicados, emissão, consolidação, leo_resolver, orquestrador, anexação). Grep `Componente(`: um hit, a mesma fixture nomeada (não posicional) — `concentracao=None` sobrevive type-correct à migração. **Refinamento do gate:** a varredura inicial cobriu só `agente_medico/`; tipo compartilhado é importável do legado, então rodou-se segundo grep no REPO INTEIRO — único hit fora era `modulo_pcmso.py:989` (`fispq.get("componentes")`, dict legado, falso positivo case-insensitive), não importa `tipos.Componente`. Migração não toca comportamento de nenhum consumidor.

**Baseline real recalibrada — o "339+1 / 198" herdado morreu.** A medição herdada (003.G/container) era "completa 339 verde + 1 falha de ambiente python-docx / isolado 198", marcada "reconfirmar na máquina real". Reconfirmada nesta sessão na máquina do Diovanni: pré-fatia **isolado 198 / completa 347-0** (a falha de python-docx NÃO está mais presente — ambiente mudou, sem `importorskip`/skip, verificado). O +7 sobre 340 e a falha resolvida são anteriores à fatia (nenhum código tocado no gate), não regressão — diferença container→máquina-real que vinha não-medida desde a 003.G. O STOP do passo 4 do prompt da fatia disparou corretamente nessa divergência; resolvido aceitando a baseline real (mais verde, menos falha, direção benigna). Pós-fatia-1: **isolado 204 / completa 353-0** (+6 cada, os 6 testes novos). PRÓXIMA REFERÊNCIA = 204 / 353.

**Implementação.** `FaixaConcentracao` frozen em `tipos.py` (campos `minimo`/`maximo: Optional[float]`; métodos `piso_efetivo`/`teto_efetivo` encapsulam as sentinelas None→0 / None→+inf; sem `__post_init__`). `Componente.concentracao` migrado para `Optional[FaixaConcentracao] = None`. Forma sub-objeto frozen (não par de campos) decidida na implementação conforme D-ARQ-34 delegava. 6 testes em `test_faixa_concentracao.py` (faixa fechada / semi-aberta inferior `<5%`=(None,5) / semi-aberta superior `>1%`=(1,None) / ponto / default-None / aceita-faixa). mypy --strict limpo (motor 14 arquivos; teste novo nomeado). Commit 591a04d, merge 3240e10 (PR #65, "Create a merge commit").

**Trilho respeitado.** Só Parte 1 (contrato de dado). Partes 2–4 (predicado tri-estado, container de flags, `is_sensibilizante`, gate-CAS) NÃO tocadas. Nenhuma regra clínica criada/alterada (R-FDS-* intactas). DECISOES ganhou nota de aplicação em D-ARQ-34 + v37 (sem mudança de conteúdo da decisão — a forma já era delegada). PROTOCOLO intocado. DT-FDS-01 não tocada. Arco D-ARQ-31 selado.

**Pendências abertas.** Fatia 2 (Partes 2–4 de D-ARQ-34) carrega: forma do container de flags (precisa distinguir flags-ausentes/slug-não-resolvido de flags-todas-False → `Optional` ou campo `resolvido`); onde o predicado mora; borda 5,0 com marca `[INTERPRETADO — DT-FDS-02]`. PRÉ-REQUISITO herdado e ainda não existente: gate-CAS de D-ARQ-33 cl.3 (motor irmão de composição não implementado) — predicado isolado testável com flags sintéticas, integração com gate real é sessão posterior. `is_sensibilizante` população = tarefa de dado com fonte, fora da fatia 2. DT-FDS-02 (unidade do cutoff) aberta, não bloqueia. Inalteradas: dedup convergente Stage 8, DT-002V-01 (gêmea, não fechada por D-ARQ-34), DH-003A-01 (2ª "## 11"), DT-002Y-01, DT-002X-01, asbesto-LEO, R-RX-02/DT-D3-02, glossário momento_coleta [INCERTO], TDI Quadro 1 [INCERTO].

**Próxima sessão.** Decisão do Diovanni na abertura. Candidato natural: D-ARQ-34 fatia 2 (predicado de materialidade + container de flags + `is_sensibilizante` mecanismo). Alternativa: (a) reabertura R-BIO-02 (DT-FDS-01) — CONHECIMENTO, lado-médico, Quadro 2 inteiro no PDF MTE. Ler docs vivos inteiros antes; checkout main && pull antes de criar branch.

## Sessão 003.J — 11/06/2026 — IMPLEMENTAÇÃO (D-ARQ-34 fatia 2: predicado de materialidade tri-estado)

**Foco.** Materializar as Partes 2–4 de D-ARQ-34 — o predicado de materialidade `(faixa, flags) → {MATERIAL, NÃO-MATERIAL, AUSENTE}` + as flags de perigo no `Componente` + o discriminante do ramo 0. Candidato (c) da abertura, confirmado pelo Diovanni. Predicado ISOLADO, testado sintético, NÃO plugado em consumidor.

**Abertura — ARQUITETURA antes de IMPLEMENTAÇÃO.** A fatia abriu como ARQUITETURA, não IMPLEMENTAÇÃO pura: três decisões de forma estavam abertas (container de flags, onde mora o predicado, borda 5,0) e fechar forma é design. Docs vivos lidos inteiros (PROTOCOLO, depois DECISOES). Três passadas adversariais sobre o recorte herdado do handoff:
- A ressalva do gate-CAS (handoff: "pré-requisito da fatia") estava SUPERDIMENSIONADA. D-ARQ-34 Parte 2 separa pré-condição (CAS inválido pelo dígito verificador → gate do motor irmão, a montante) de ramo 0 (CAS válido, slug não resolvido → D-ARQ-14). A Parte 4 crava o predicado `(faixa, flags)` — nunca vê CAS. Logo o predicado é testável 100% isolado, gate-CAS não é pré-requisito desta fatia.
- O handoff equiparava "`Optional[...]` ou campo `resolvido`" para o discriminante do ramo 0 — não são equivalentes. `Optional[FlagsContainer]=None` recria overloading de `None` e colide com `concentracao=None`.

**Gate de estado real — fechado, repo inteiro (tipo compartilhado).** Grep das flags antes de fechar a forma: `is_ototoxico` é flag SOLTA em `Risco` (`tipos.py:97`, lida em `predicados.py:95`, hidratada de `agentes.yaml` em `riscos.py:25,98`); `is_carcinogeno_iarc` é metadado de agente em `agentes.yaml` (por slug). Grep `Flags`/`FlagsPerigo` no repo: ZERO no motor novo (só legado e falsos positivos `re.IGNORECASE`). `Componente` (`tipos.py:45`) carregava só `cas:str`, `nome:str`, `concentracao:Optional[FaixaConcentracao]` — NENHUMA flag, NENHUM slug resolvido. Conclusão: o motor não tem agregado de flags; o padrão é flag solta; `Componente` precisa de campos novos para flags E para o discriminante de resolução.

**Duas decisões de forma fechadas (contra o código, não contra cache).**
1. **Sem container de flags.** Flags entram soltas em `Componente` (`is_carcinogeno_iarc`/`is_sensibilizante`, default False), espelhando `Risco.is_ototoxico`. Criar `FlagsPerigo` agregado romperia o padrão sem razão — gatilho de promoção D-ARQ-16 ("dois casos provam o padrão, não um") não disparou. O discriminante do ramo 0 NÃO mora nas flags: é `agente: Optional[str] = None` (o slug resolvido; `None` = não resolvido). Escolhido sobre `resolvido: bool` por não armazenar derivado (`resolvido` == `agente is not None`) e por não recriar overloading de `None` — `concentracao=None` ("não extraída") e `agente=None` ("não resolvido") são campos distintos com um só sentido cada.
2. **Predicado em módulo neutro.** `motor/materialidade.py` novo — não no motor médico (senão o engenheiro importa de dentro do médico) nem no irmão (inexistente), pois a Parte 4 o quer compartilhado. Função pura que retorna o enum e NÃO muta `ctx.pendencias` (tradução AUSENTE→Pendencia é do consumidor) — deliberadamente mais puro que os primitivos D-ARQ-13, por servir dois trilhos de pendência.

**Implementação.** `Componente` ganha `agente: Optional[str] = None`, `is_carcinogeno_iarc: bool = False`, `is_sensibilizante: bool = False`. `materialidade.py`: enum `Materialidade` + `materialidade(componente) -> Materialidade`, ramos 0 (slug None → AUSENTE) / 1 (bypass True → MATERIAL, independe de concentração) / 2 (sem bypass, concentração None → AUSENTE) / 3 (straddle `piso≤5<teto` → AUSENTE) / 4 (`piso>5` → MATERIAL) / 5 (`teto≤5` → NÃO-MATERIAL); borda 5,0 = NÃO-MATERIAL `[INTERPRETADO — DT-FDS-02]`. Comentário de regra (D-ARQ-34 Parte 2 / R-FDS-03) na docstring — exceção de rastreabilidade ao "sem comentários óbvios". 11 testes sintéticos em `test_materialidade.py` (`Componente` construído direto, sem fixture/pipeline). Commit d0e8417, merge dd9c200 (PR #67, "Create a merge commit").

**Baseline — gates exatos.** Pós-fatia: **isolado 215 / completa 364**, consistente com a referência herdada 204/353 +11 testes novos (o Code derivou os +11 sobre a herdada; NÃO houve medição pré-fatia isolada reportada nesta sessão, ao contrário da 003.I onde o STOP do passo 4 forçou a remedição da baseline). Sem drift observado: se a herdada tivesse mudado, os totais não fechariam em 204+11 / 353+11. mypy --strict limpo (`materialidade.py` + `tipos.py`). `old_str` casou de primeira. PRÓXIMA REFERÊNCIA = 215 / 364.

**Trilho respeitado.** Só Partes 2–4 (predicado + contrato de flags). NÃO plugado: R-FDS-03 não reescrito, motor irmão não tocado, `agentes.yaml` intocado (flags vêm da ficha normalizada futura, D-ARQ-25 Parte B). `is_sensibilizante` criada com default False, NÃO populada (tarefa de dado com fonte). Nenhuma regra clínica criada/alterada (R-FDS-*/R-BIO-* intactas). PROTOCOLO intocado → DH-003A-01 não tocado. DECISOES ganhou nota fatia 2 em D-ARQ-34 + v38. Arco D-ARQ-31 selado.

**Paliativo registrado (sinalizado).** A fatia entrega um predicado ÓRFÃO: `Componente.agente` e as flags são adicionados mas NINGUÉM os preenche nesta fatia (resolução CAS→slug→flags é extração futura). Rodando o pipeline real hoje, todo `Componente` teria `agente=None` → ramo 0 → AUSENTE. Mas não há consumidor real do predicado (R-FDS-03 não reescrito, motor irmão inexistente), então NENHUMA saída é afetada — o predicado só é exercitado por teste sintético. Aceitável pela mesma razão da fatia 1 (contrato antes de consumidor; "o dado precede a regra"), registrado explícito.

**Pendências abertas.** Fatia 3 de D-ARQ-34 (candidata da 003.K) carrega: hidratação das flags do `Componente` a partir da ficha normalizada + plug do predicado em R-FDS-03 + integração com o motor irmão. PRÉ-REQUISITO herdado e ainda inexistente: a camada de extração/normalização (D-ARQ-25 Parte B, resolve CAS→slug→flags) só existe no legado — a fatia 3 não abre sem decidir essa fronteira. `is_sensibilizante` população = tarefa de dado com fonte. DT-FDS-02 (unidade do cutoff) aberta, não bloqueia. Inalteradas: dedup convergente Stage 8, DT-002V-01 (gêmea, não fechada por D-ARQ-34), DH-003A-01 (2ª "## 11"), DT-002Y-01, DT-002X-01, asbesto-LEO, R-RX-02/DT-D3-02, glossário momento_coleta [INCERTO], TDI Quadro 1 [INCERTO], DT-FDS-01 (reabertura R-BIO-02, lado-médico, Quadro 2 inteiro).

**Próxima sessão.** Decisão do Diovanni na abertura. Candidato natural: D-ARQ-34 fatia 3 (hidratação de flags + plug em R-FDS-03) — mas herda a fronteira de extração (D-ARQ-25) não decidida; abrir como ARQUITETURA. Alternativa: (a) reabertura R-BIO-02 (DT-FDS-01) — CONHECIMENTO, lado-médico, Quadro 2 inteiro no PDF MTE. Ler docs vivos inteiros antes; checkout main && pull antes de criar branch.

## Sessão 003.K — 12/06/2026 — ARQUITETURA (diagnóstico de travessia ponta-a-ponta)

**Foco.** ARQUITETURA-diagnóstico (não fatia, não META): medir, com gate de estado real, o que impede um PGR de atravessar do documento à matriz. Mudança de lente herdada da 003.J — o motor amadureceu, frentes acumularam órfãs/desacopladas, a travessia "documento real → matriz" nunca foi atravessada. Diagnóstico antes de escolher a frente da 003.L.

**Método.** Fases read-only dirigidas (sem despejo de bloco — PSReadLine), cada uma calibrando a seguinte. Três passadas adversariais sobre o próprio instrumento: (1) o grep de construtor `-SimpleMatch 'GHEPGR('` era frágil e confirmaria a hipótese por falha silenciosa — descartado; (2) o denominador "46% formato legado" misturava inputs e gabaritos — recomputado por papel; (3) a triagem nativo-vs-escaneado por byte cru é cega a stream FlateDecode — descartada como inconclusiva.

**Medições (estado real).**
- **Travessia fixture→motor→matriz NÃO é gargalo.** Consumada e congelada desde 003.E (`test_integracao_viverde.py`, 32 GHEs, regressão tri-estado). O gargalo é inteiramente a montante de `tipos.PGR`.
- **Camada de extração (D-ARQ-25) não existe em código vivo.** Extratores legados congelados em 17/05/2026 (data zero): `parser_pgr.py` (regex, viola D-ARQ-09, não-portado), Gemini (sem quantificação/slug). Nenhum estado novo.
- **Fixture sem lado-químico.** `pgr_viverde.py` (27/05): `produtos_quimicos=()` nos 32 GHEs; zero `ProdutoQuimico`/`FDS`/`Componente`. Usa helpers (`_quimico_mgm3`/`_ruido`) encapsulando `fracao`/`pct_quartzo`.
- **PGR Viverde V02 não carrega composição química** (medido no texto do .docx-fonte): `composi`=0, `solvente`=0, `produto químico`=0, `n. CAS`=0; `FISPQ`=1 (conceito, não dado); `sílica`=4/`tinta`=22 (agentes físico-químicos, não FDS). Logo a fixture `produtos_quimicos=()` é FIEL à fonte, não buraco de fixture — é o cenário R-PGR-04 (composição ausente → exigir FDS).

**Achado central.** A maquinaria de materialidade D-ARQ-33/34 (`FaixaConcentracao`, predicado tri-estado, flags — construída em 003.G→003.J) NÃO tem caso-âncora vivo no Viverde, porque o PGR-fonte não tem composição. Não há de onde popular o lado-químico da fixture a partir do Viverde. Fato não medido por nenhuma sessão anterior.

**Três buracos da travessia (ordem de distância da fixture).**
- Buraco 0 — fixture sem lado-químico: NÃO é gap de fixture (reflete fielmente PGR-sem-FDS). Caso-âncora de materialidade exige fonte externa.
- Buraco 1 — extração-forma (.docx → tipos.PGR): caso fácil, piso de esforço; extratores legados reprovados por contrato (D-ARQ-25).
- Buraco 2 — extração-real (formato adverso): NÃO-MENSURÁVEL nesta pasta. `matrizes_originais/` é material de validação histórica (4 pares D-ARQ-18), não amostra de produção — 1 único PDF de input, resto outputs Word. A pergunta nativo-vs-escaneado (texto+LLM vs. multimodal) não tem dado aqui; exige PGRs de produção, deliberadamente diferidos.

**Achados laterais (mapa, não investigados).**
- Árvore fantasma `refatoracao/` — cópias DIVERGENTES de `modulo_engenharia.py` (29.391 vs 28.971 B) e `ia_client.py` (6.058 vs 2.362 B), não documentada em doc vivo. Aposentar formalmente ou ignorar por declaração antes de qualquer frente de extração.
- Recalibração: universo `matrizes_originais/` = 50 arquivos (36 untracked + 14 tracked), não 36. .doc=19, .docx=13, .pdf=13, .rtf=4, .xlsx=1. Dois projetos "Viverde" distintos (PGR Viverde V02 ≠ CMO Residencial Viverde Areião) — parear PGR↔gabarito com cuidado.
- Anomalias não-confirmadas: "14 tracked" é inferência frágil do porcelain; "arquivo duplicado mesmo nome" é impossível em NTFS plano. Verificar se relevante.

**Recomendação de frente para a 003.L.** Caçar o caso-âncora de materialidade nos outros 3 pares D-ARQ-18 (CMO, Vistamerica, GPL-R78/Naturia): algum traz FDS/composição? Se sim, primeiro caso-âncora vivo de D-ARQ-33/34 — a 003.L conecta a materialidade a dado real (não sintético) pela primeira vez. Se negativo, é informação que decide (materialidade fica bloqueada até coleta externa de FDS — saber, não supor). Barato: técnica do bloco B replicada sobre 3 arquivos. Abre como ARQUITETURA/diagnóstico com gate de estado real próprio. ALTERNATIVA LEGÍTIMA: validar travessia Viverde (PGR-sem-FDS → matriz PARCIAL + R-PGR-04) — mas já coberta por Stage 3/003.E, e deixa a materialidade órfã mais uma sessão (aprofunda a linearidade que a mudança de lente questiona). Decisão de foco da 003.L é do Diovanni.

**Baseline.** Inalterada — sessão read-only, nenhum código tocado. Referência herdada 215 isolado / 364 completa (215 reproduzido no kickoff; 364 não-mensurável no container por falta de pandas, não refutado). Nada commitado nesta sessão exceto este bloco de fechamento.

**Pendências inalteradas.** DT-FDS-01 (R-BIO-02, lado-médico, Quadro 2 inteiro), DT-FDS-02 (unidade cutoff 5%), DH-003A-01 (2ª `## 11`), Stage 8 dedup convergente, DT-002V-01, DT-002Y-01, DT-002X-01 (LEO carvão), DT-002Y-02, glossário momento_coleta [INCERTO], TDI Quadro 1 [INCERTO], asbesto-LEO, R-RX-02/DT-D3-02.\r\n\r\n## Sessão 003.L — 13/06/2026 — ARQUITETURA-diagnóstico (caça do caso-âncora de materialidade nos pares D-ARQ-18)\r\n\r\n**Foco.** Executar a recomendação da 003.K: caçar o caso-âncora vivo de materialidade (D-ARQ-33/34) nos PGRs dos pares D-ARQ-18. ARQUITETURA-diagnóstico, read-only, gate de estado real próprio. Frente decidida pelo Diovanni na abertura (recomendada pelo handoff; alternativa "validar travessia Viverde" preterida).\r\n\r\n**Abertura.** main em `91a30e9` (merge PR #69, fechamento 003.K); `19999bc` abaixo; sincronizada com origin/main. Baseline 215 isolado / 364 completa herdada, read-only. Sem divergência git × HISTORICO no início.\r\n\r\n**Mudança de estado do working tree DURANTE a sessão (registrar p/ o /kickoff da 003.M não estranhar).** A pasta `matrizes_originais/` começou com os untracked herdados da 003.K; durante a sessão o Diovanni adicionou **14 PGRs novos** (todos `.pdf`, ~39 MB) e criou a pasta-irmã nova **`fds_originais/`** com 5 FDS reais. Nenhum desses arquivos foi staged (regra permanente: `matrizes_originais/`/`fds_originais/` nunca staged). O `git status` ao fim da 003.L tem mais untracked que no início — crescimento de dado de insumo, não de código.\r\n\r\n**Correção de modelo durante a sessão (Diovanni).** A caça abriu sobre premissa ERRADA do Arquiteto: procurar composição/CAS NO PGR. O PGR não carrega composição nem CAS — carrega risco + agente químico nomeado; a composição (componentes, CAS, perigos, agravos) vem da FDS, documento separado solicitado à empresa (R-FDS-01/R-PGR-04). As duas primeiras fases (busca de `CAS`/`composição`) mediam a coisa errada. Reinstrumentado após a correção.\r\n\r\n**Método (read-only, faseado, PDFs nativos).** Fase 1 (triagem nativo-vs-escaneado, pdfplumber): os 3 pares + T65 de referência são PDF NATIVO (~900–1340 chars/página) — mata a hipótese-escaneado que o sniff Ghostscript/CCITTFaxEncode levantou. Fase 2-corrigida (query certa: linha de inventário marcada "Químico" + agente nomeado + marcador de FDS-apontada `acrobat.adobe.com`/`FISPQ`/`anexo`; captura de contexto; classificação a posteriori, não filtro). Varredura dos 15 PGRs do acervo.\r\n\r\n**Veredito da caça — os 3 pares D-ARQ-18 NÃO trazem FDS apontada.**\r\n- **CMO** (`PGR CMO - Ver.02 REv.02`), **Vistamérica** (`PGR VISTAMERICA - Ver.02 REv.01`), **Naturia** (`PGR R78 NATURIA PARTE 2`): nenhum tem composição estruturada nem link de FDS. Agente químico genérico ou EPI-boilerplate. O veredito-pares sustenta-se por instrumento correto, não por cegueira de query.\r\n- **Naturia é fragmento confirmado** (medido: GHEs únicos `[2,7]`, range 2–7; "PARTE 1" = 0 ocorrências; presentes do bloco 01–06 = só `[2]`). O "PARTE 2" no nome + a ausência dos GHEs 1/3/4/5/6 confirmam: o veredito vale só sobre o fragmento que veio, não sobre o PGR completo do Naturia.\r\n\r\n**Achado de maior valor — mapa de 6 formas de declaração químico no PGR → DT-003L-01.** A varredura dos 15 PGRs mostrou que não há "o formato do PGR"; há ao menos seis (catalogadas em DT-003L-01), de "agente + link FISPQ por GHE" (T65/EURO, caminho feliz, FDS apontada por URL) a "matriz por-cargo com dezenas de agentes + e-Social sem link" (Ricco). Links `acrobat.adobe.com` só em 2 dos 15 PGRs (Shape 1 = exceção). É o input empírico que a camada de extração (D-ARQ-25) terá de aguentar — detalhe completo na DT.\r\n\r\n**Leads de D-ARQ-06 (não-construção) no acervo.** Entre os 11 PGRs além dos 3 pares, há nomes de setor não-óbvio-construção (Auro, TPB Andrade, Seconci) — não triados quanto a setor nesta sessão. Se algum for não-construção COM FDS apontada, fecha a validação universalidade de D-ARQ-06 de brinde. Candidato a varredura futura, não investigado aqui (a caça mirava os 3 pares).\r\n\r\n**Caso-âncora localizado e matéria-prima obtida.** O T65 (Toctao — NÃO um dos pares D-ARQ-18) é Shape 1: nomeia produto e aponta FDS por link. O Diovanni baixou 5 FDS reais (`fds_originais/`), pareadas aos agentes do T65: Cimento Ciplan (GHE 7/8/9), Adesivo PVC Tigre (GHE 11/12), Tinta Acrílica + Massa Corrida + Textura Leinertex (GHE 15). Não vieram: Solução Limpadora (T65 GHE 11) e Impermeabilizante (EURO). Matéria-prima pronta para a 003.M — NÃO lida nesta sessão (trilho "o dado precede a regra"; ler FDS é trabalho da sessão seguinte).\r\n\r\n**Reenquadramento da promessa (2ª passada adversarial).** A caça NÃO destrava a materialidade automaticamente: D-ARQ-25 (extração) não existe em código vivo (medido na 003.K), então a fixture-com-lado-químico da 003.M será construída À MÃO a partir das FDS, como toda fixture até hoje. A vitória é de FIDELIDADE (primeira fixture-com-lado-químico derivada de FDS real, não sintética), não de pipeline automático. `materialidade.py` (003.J) segue pronta e órfã de consumidor — a fatia 3 (plug + hidratação) é ortogonal à caça, não depende dela.\r\n\r\n**Verificação.** Sem código. Read-only puro. Baseline 215/364 inalterada (nenhum arquivo de motor tocado). Branch de triagem `feature/003l-triagem-pgr-extracao` criada para a caça, ZERO commits (todo trabalho foi leitura). Fechamento documental em branch `docs/` própria.\r\n\r\n**Achados laterais (mapa, não investigados).**\r\n- **`matrizes_originais/` tem tracking misto** — ~13 arquivos já tracked no meio dos untracked (incluindo o PGR Viverde), confirmando o "14 tracked" que a 003.K marcou como inferência frágil. Não é frágil: é real. Pasta com higiene de git comprometida (FDS/matrizes nunca deveriam ser tracked). Higiene futura via `git ls-files matrizes_originais/`; não bloqueia, registrado para não se reinvestigar como novo.\r\n- **"Graxa ET … [3-(tridecyloxy)propyl]"** (Viverde GHE4, Vistamérica GHE5, Shape 5) tem nomenclatura de COMPOSTO, não de produto comercial genérico. Se for composição inline, o veredito-Viverde da 003.K ("PGR Viverde não carrega composição") tem um furo — um fragmento que a query de CAS (cega a nome-de-composto-sem-CAS) não pegou. Não investigado (não muda a 003.L; caso-âncora veio do T65). Reconferir ao tocar a fixture Viverde ou a extração.\r\n\r\n**Pendências abertas.** **DT-003L-01 (nova)** — mapa de 6 formas de declaração químico no PGR; input empírico para D-ARQ-25. Inalteradas: DT-FDS-01 (R-BIO-02, Quadro 2), DT-FDS-02 (unidade cutoff 5%), dedup convergente Stage 8, DH-003A-01 (2ª "## 11"), DT-002V-01, DT-002Y-01, DT-002X-01 (LEO carvão), DT-002Y-02, asbesto-LEO, R-RX-02/DT-D3-02, glossário momento_coleta [INCERTO], TDI Quadro 1 [INCERTO].\r\n\r\n**Próxima sessão (003.M).** Decisão do Diovanni na abertura. RECOMENDADA (opção 1): caso-âncora vivo da materialidade — construir a primeira fixture-com-lado-químico a partir das 5 FDS de `fds_originais/` + plug em `materialidade.py` (D-ARQ-34 fatia 3). Abre como ARQUITETURA (como a FDS lida vira `Componente`: faixa de concentração, flags de perigo; TiO₂ da tinta como candidato a bypass-carcinógeno `[INCERTO — IARC 2B a confirmar em fonte oficial]`) → IMPLEMENTAÇÃO. Herda a fronteira de extração (D-ARQ-25) não-decidida — fixture à mão, não pipeline. ALTERNATIVA (opção 2): taxonomia de Shapes (DT-003L-01) como frente formal de D-ARQ-25. Ler docs vivos inteiros antes; checkout main && pull antes de criar branch.

## Sessão 003.M — 13/06/2026 — ARQUITETURA→IMPLEMENTAÇÃO (D-ARQ-34 fatia 3: fixture-FDS real + materialidade sobre dado real)

**Foco.** Construir a primeira fixture-com-lado-químico derivada de FDS real e exercitar o predicado `materialidade()` (003.J, órfão) sobre ela. Opção 1 do handoff 003.L, confirmada pelo Diovanni. Abriu ARQUITETURA (recorte do consumidor) → IMPLEMENTAÇÃO (fixture + testes).

**Abertura — gate de estado real, divergência de container resolvida.** Duas coletas de git divergiram: kickoff (máquina real) = `main` em `e4232b5` sincronizada com `origin/main`; coleta de container = branch `claude/*`, `origin/main` 38 commits atrás em `5222d34` (pré-003.A). `git fetch origin` + `git rev-parse HEAD origin/main` na máquina real: ambos `e4232b5`. O "origin/main 38 atrás" era ref morto de container — falso STOP. Doc 2 (kickoff) venceu. LIÇÃO META (registrada, não vira DH): container é fonte de CONTEÚDO (docs, código), NUNCA de estado de git/remoto — topologia de remoto só na máquina real. A coleta de container fabricou o falso STOP desta sessão.

**Recorte β fixado (fidelidade pura, sem plug) — α descartada por medição.** O eixo era: (α) dar consumidor de produção ao predicado agora vs. (β) fixture+teste real, consumo inteiro na fatia 4. Leitura de `regras.yaml` (gate de estado real) mediu: R-FDS-03 NÃO existe como regra executável — o lado químico de `regras.yaml` está vazio (só atividade/ruído/vibração/RX-sílica/PNOS/fumos). Plugar o predicado exigiria criar o primeiro primitivo químico + a primeira regra química + a cadeia Componente→Risco — a fatia 4 inteira. α seria fatia-4-disfarçada (viola uma-implementação-por-sessão). β é o recorte honesto: predicado ganha cobertura sobre dado real, segue órfão de consumidor de produção (correto — consumidor é fatia 4).

**Recorte de forma (gate de estado real, `pgr_viverde.py` + `tipos.py`).** A fixture constrói nível-Componente direto (não ProdutoQuimico/FDS/GHEPGR): `materialidade(componente)` consome só `Componente`; embrulhar seria andaime para consumidor (Stage 3, orquestrador) que esta fatia não exercita. Medido: `pgr_viverde.py` tem `produtos_quimicos=()` nos 32 GHEs — NUNCA construiu `ProdutoQuimico`/`Componente`; não há convenção de embrulho a espelhar. A fatia 4 decide o embrulho junto com a regra de promoção. Fixture em `fixtures/fds_t65.py` (novo, helper por produto), testes em `test_materialidade_fds.py` (novo, separado do `test_materialidade.py` sintético da 003.J — sintético-de-ramo vs. real-de-FDS; nome diz qual natureza falhou).

**Dado — 3 FDS reais lidas (parou em 3).** Do PGR ALT T65 2024.2026: Tinta Acrílica (GHE 15), Cimento Ciplan (GHE 7/8/9), Adesivo PVC Tigre (GHE 11). Decisão de parar em 3: cobertura honesta atingida (ramos 0/3/4 + caso-âncora de DT); as 2 restantes (Massa Corrida, Textura Leinertex) repetiriam ramo-0-em-massa (cargas minerais sem slug) — ficam para a fatia de expansão de vocabulário. 24 componentes totais.

**Correções de modelo durante a sessão (registradas honestamente).**
- **TiO₂ refutado como caso-âncora do bypass-carcinógeno.** Confirmado em fonte IARC (Monografia vol. 93, 2010): TiO₂ é Grupo 2B (não Grupo 1), por INALAÇÃO DE PÓ, com evidência humana inadequada; a monografia ressalva que TiO₂ ligado em matriz de tinta não gera exposição a partícula primária. A Tinta Acrílica é base água, líquida — via da classificação não aplicável. `is_carcinogeno_iarc=False` no Componente, marcado [INTERPRETADO]. O handoff 003.L prometia o TiO₂ como teste-vivo-do-bypass; o dado real refutou. Divergência legítima com agentes.yaml (que traz `is_carcinogeno_iarc: true` para a substância em abstrato): o predicado lê a flag do Componente, não do yaml (D-ARQ-34 Parte 4).
- **Cimento sem sílica cristalina (erro de química do Arquiteto, corrigido pelo dado).** O Cimento foi recomendado como "único com chance de MATERIAL real via sílica". Falso: cimento Portland traz silicato tricálcico/dicálcico (compostos do clínquer, CAS 12168-85-3/10034-77-2), NÃO sílica cristalina livre (quartzo, CAS 14808-60-7). Silicato de cálcio não tem slug, não é carcinógeno. 8 de 8 componentes do Cimento → ramo 0.
- **MEK é o único MATERIAL fiel ao pipeline.** Metiletilcetona (Adesivo PVC) tem slug `metil_etil_cetona`, faixa 10–42% (`min>5`) → ramo 4 → MATERIAL. Único componente das 3 FDS que atravessa para MATERIAL por dado limpo.
- **CAS quebrado documentado.** A FDS da Tinta traz o TiO₂ como CAS `134363-67-7` (um dígito a mais, falha o dígito verificador). CAS oficial `13463-67-7`. Fixture usa o corrigido com marcador; o componente real bloquearia no gate-CAS da fatia 4 — caso de fidelidade valioso.

**Resultado medido (23 AUSENTE + 1 MATERIAL + 0 NÃO-MATERIAL).** Dos 24 componentes: ~21 em ramo 0 (sem slug em agentes.yaml), TiO₂ em ramo 3 (straddle 1≤5<15), MEK em ramo 4 (MATERIAL). Zero NÃO-MATERIAL fiel — nenhum componente com slug tem faixa inteira ≤5% (lacuna conhecida, asserida no `test_contagem`; ramo 5 fiel só vem com expansão de vocabulário). O predicado distingue os DOIS motivos de AUSENTE (ramo 0 = slug ausente; ramo 3 = straddle) sobre dado real — não é AUSENTE-degenerado.

**Achado central — o vocabulário não cobre composição-de-FDS (→ DT-003M-02).** 23 de 24 componentes de 3 FDS reais caem em ramo 0. `agentes.yaml` é vocabulário de inventário-de-PGR (sílica, ruído, ototóxicos, fumos), não de composição-de-FDS (carbonato, silicato, óxidos, polímeros, isotiazolona — ausentes). A vitória da fatia não é "predicado funciona sobre FDS" e sim a MEDIÇÃO de que o vocabulário não fala a língua das FDS — input empírico para a fatia de expansão.

**Achado de arquitetura — ramo-0-vs-bypass com CAS oculto (→ DT-003M-01).** O Segredo Industrial 2 do Adesivo PVC declara H334 (sensib. respiratória) + H317 (sensib. dérmica) na FDS, mas tem CAS OCULTO (segredo industrial). Sem CAS → sem slug → `agente=None` → ramo 0 → AUSENTE, MASCARANDO o bypass-sensibilizante (ramo 1). 2ª passada: isto NÃO é só disciplina de fixture — o estado `sem-slug + flag-de-perigo-declarada-no-documento` é alcançável pelo PIPELINE REAL (FDS declara perigo por frase-H em componente de CAS oculto; a extração resolve CAS→slug→flag, e CAS oculto quebra a cadeia). Eleva de "disciplina de fixture" a decisão de arquitetura (ordem ramo-0-vs-bypass quando CAS é oculto). Na fixture, `is_sensibilizante` fica False (o pipeline real não teria a flag sem slug) → ramo 0 honesto. Adiado para sessão própria (toca a ordem dos ramos da 003.J + o gate-CAS de D-ARQ-33).

**Verificação.** Gate de baseline: 215/215 isolado confirmado ANTES de tocar arquivo (referência 003.J; STOP-and-report armado, não disparou). Isolado 215 → **221** (+6 testes em `test_materialidade_fds.py`). mypy --strict limpo nos 2 arquivos novos. Commit `0fccd62`; PR #71; merge `f5d9317` em main ("Create a merge commit", fast-forward e4232b5..f5d9317). PRÓXIMA REFERÊNCIA = 221 isolado.

**Nota META (registrada, não vira tripwire formal — decisão de processo do Diovanni).** O predicado de materialidade está órfão de consumidor de produção desde a 003.J (003.J isolou, 003.K/L diagnosticaram, 003.M deu fixture+teste sem plug). São três sessões. A fatia 4 (plug em produção) não deveria adiar de novo. Registrado como observação de ritmo, não regra.

**Pendências abertas.** **DT-003M-01 (nova)** — ramo-0-vs-bypass com CAS oculto (decisão de arquitetura, sessão própria). **DT-003M-02 (nova)** — vocabulário não cobre composição-de-FDS (medição 23/24 ramo 0; input para expansão de agentes.yaml). **DH-003M-01 (nova)** — `\r\n` literal reincidente no HISTORICO (bloco 003.L; mesmo defeito da 003.K). Inalteradas: DT-FDS-01 (R-BIO-02, Quadro 2), DT-FDS-02 (unidade cutoff 5%), dedup convergente Stage 8, DH-003A-01 (2ª "## 11"), DT-002V-01, DT-002Y-01, DT-002X-01 (LEO carvão), DT-002Y-02, asbesto-LEO, R-RX-02/DT-D3-02, glossário momento_coleta [INCERTO], TDI Quadro 1 [INCERTO].

**Próxima sessão (003.N).** Decisão do Diovanni na abertura. Candidatos: (a) DT-003M-01 — decisão de arquitetura do ramo-0-vs-bypass (toca predicado 003.J + gate-CAS D-ARQ-33); (b) expansão de agentes.yaml (DT-003M-02) destravando os ramos reais da materialidade — tarefa de dado com fonte por agente; (c) D-ARQ-34 fatia 4 — plug do predicado em produção (consumidor que o predicado nunca teve; recomendação do Arquiteto: não adiar de novo, ver nota META). Ler docs vivos inteiros antes; checkout main && pull antes de criar branch.

## Sessão 003.N — 13/06/2026 — CONHECIMENTO→ARQUITETURA→IMPLEMENTAÇÃO (frente b: vocabulário de composição-FDS, DT-003M-02 parcial)

**Foco.** Candidato (b) do handoff 003.M (expandir agentes.yaml para composição-de-FDS, DT-003M-02), confirmado pelo Diovanni. Abriu em CONHECIMENTO→ARQUITETURA (recorte da frente) e transitou para IMPLEMENTAÇÃO (dado puro no yaml).

**Reenquadramento da frente por passadas adversariais + gates de estado real.** O handoff afirmava que (b) "destrava os ramos reais da materialidade". Refutado em camadas: (1) grep — o predicado `materialidade()` lê flags do `Componente`, NUNCA de agentes.yaml (D-ARQ-34 Parte 4); popular o yaml não alimenta o predicado. (2) `regras.yaml` lido — lado-químico VAZIO (0 de 18 regras dispara por componente/material/agente-químico); a travessia FDS→linha-de-matriz exige a fatia 4 inteira (promoção Componente→Risco inexistente em qualquer D-ARQ + regra química + hidratação), não cabe em uma sessão. (3) `fds_t65.py` lido — dos 23 ramo-0, só 14 têm CAS resolvível (os demais cas=""); destes 14, 12 são inertes flag-False (AUSENTE→NÃO-MATERIAL, sem efeito de conduta). Conclusão: (b) NÃO move linha de matriz hoje; entrega vocabulário pronto para a hidratação futura. Honesto, bounded, encolhe a fatia 4.

**Recorte (b-mínimo).** Em vez dos 14, populadas só as 2 substâncias-solvente que atravessam para MATERIAL/straddle quando hidratadas (acetona 30–70% → MATERIAL; acetato de etila 5–30% → straddle), inaugurando o PADRÃO de ficha-de-composição com 2 casos de fonte verificada em vez de 14 com fonte apressada. Os 12 inertes e os CAS-ausentes ficam para quando a hidratação provar que distinguir NÃO-MATERIAL importa.

**Procedência (gate D-ARQ-22).** CAS conferido contra a fixture 003.M (67-64-1, 141-78-6 — dígito verificador ok). is_carcinogeno_iarc=false [DERIVADO — IARC não classificado, via web_search; NOTA: derivado de busca, não de leitura da Monografia — afirmação normativa de baixo risco mas a inspecionar 1º se reusada]. is_ototoxico deixado ausente [DERIVADO — fora da lista NIOSH de 5 solventes ototóxicos: CS2/tolueno/estireno/xileno/TCE, Arch Environ Health 1994;49(5):359-365; perda auditiva em mistura tolueno+acetato+etanol atribuída ao tolueno, não isolada]. is_sensibilizante NÃO adicionada ao yaml (nenhuma das duas é sensibilizante → flag fora desta fatia; (b-mínimo) é dado puro, sem schema).

**Verificação.** Branch-gate: criada feature/003n-vocabulario-fds a partir de main ead3e7a (branch-gate disparou em main na abertura; PARADA e branch criada antes de tocar arquivo). Baseline: 221 isolado reconfirmado antes de tocar arquivo (sem STOP). Isolado 221→222 (+1: um teste parametrizado cobrindo os 2 agentes; a previsão "+2" do prompt era imprecisão do Arquiteto, não erro do Code). mypy --strict limpo (15 arquivos, motor intocado). Commit 4945396; staging nominal; fds_originais/ e matrizes_originais/ untracked. PRÓXIMA REFERÊNCIA = 222 isolado (após merge). Push/merge do Diovanni.

**Pendências.** DT-003M-02 — parcial, NÃO fecha: partição medida — 14 substâncias de ramo 0 com CAS resolvível, ~9 com cas=""; populadas 2 das 14 (acetona, acetato de etila); 12 inertes-com-CAS + as cas="" seguem abertas. DT-003M-01 (CAS oculto + frase-H, Segredo Industrial 2) inalterada — fora de (b) por definição. Inalteradas: DT-FDS-01, DT-FDS-02, DT-003L-01, DH-003M-01 (\r\n literal — vigiar ao gravar este bloco), DH-003A-01, demais do balde. Achado lateral: anexo_nr07: "11" em etanol/MEK/cloreto_de_hidrogenio provável "II" corrompido (cai em DT-FDS-01) — sinalizado, não tocado.

**Próxima sessão (003.O).** Decisão do Diovanni. Candidatos: continuar DT-003M-02 (mais fichas de FDS); OU abrir o arco da fatia 4 de D-ARQ-34 (começando pela ARQUITETURA da promoção Componente→Risco — o elo que nenhum D-ARQ tem); OU DT-003M-01 (gate-vs-flag, CAS oculto). Recomendação do Arquiteto: a fatia 4 segue sendo o tripwire (predicado órfão de consumidor desde 003.J); a promoção Componente→Risco é o pré-requisito de arquitetura que falta. Ler docs vivos inteiros antes; checkout main && pull antes de criar branch.

## Sessão 003.O — 14/06/2026 — CONHECIMENTO→ARQUITETURA (frente b: arco da fatia 4 de D-ARQ-34 — promoção Componente→Risco)

**Foco.** Candidato (b) do handoff 003.N, confirmado pelo Diovanni: abrir o arco da fatia 4 pela ARQUITETURA da promoção Componente→Risco — o elo que dá consumidor de produção ao predicado de materialidade, órfão desde a 003.J. Sem código, como recomendado.

**Correção de procedência do handoff (gate de estado real sobre o literal).** O handoff afirmava (1) "D-ARQ-33 cl.2 diz que o motor irmão NÃO reconstrói riscos" e (2) "a promoção não tem casa em nenhum D-ARQ". Ambas refutadas no literal: cl.2 fala em "riscos **físicos**" (não químicos); o Contexto de D-ARQ-33 atribui derivação de risco da FDS ao engenheiro; D-ARQ-23 (operação→risco implícito em Stage 2) é precedente estrutural direto; D-ARQ-02 lista 3 fontes de risco e composição-FDS é a 4ª ausente. O trabalho não era inventar a promoção, mas decidir ONDE+O QUE e reconciliar a tensão interna de D-ARQ-33 (Contexto "engenheiro deriva risco" vs. cl.2 "irmão só enriquece ProdutoQuimico").

**Duas passadas adversariais (a decisão oscilou antes de convergir).** 1ª passada: médico-side recomendado, mas sub-justificado — apoiado em "cl.2 estreitou de propósito" (cache da própria leitura) e em D-ARQ-23 (que é risco físico/operacional, turf nativo do Stage 2, não transfere óbvio para química). Virei para engenheiro-side por um seam de "fonte única de flag". 2ª passada: o seam era fantasma — médico-side promove por CÓPIA-PRA-FRENTE das flags do Componente já resolvido (003.J), mesma fonte única que engenheiro-side; não há conflito ficha vs. agentes.yaml. Engenheiro-side cai por dois motivos firmes: (a) emitir RiscoPGR é reconstruir inventário — tipo de saída que a cl.2 literal exclui (irmão escreve ProdutoQuimico, não Risco); (b) R-GHE-04 — risco químico é SINTETIZADO (derivado), e injetá-lo em GHEPGR.riscos pelo engenheiro o lavaria como declarado. Convergência (não ping-pong): médico-side, 4ª fonte de D-ARQ-02, marcada por regra_id como o implícito-por-cargo.

**Decisão (D-ARQ-35).** Três partes: (1) ONDE = Stage 2 médico, espelhando D-ARQ-23; cl.2 de D-ARQ-33 intocada. (2) O QUE = promoção a Risco (4ª fonte de D-ARQ-02), consome maquinário existente (Stage 2→4→5, dedup R-GHE-03, anexação D-ARQ-31), não caminho químico paralelo. (3) Materialidade ANDA JUNTO, não porteia: todo componente com slug resolvido promove, carregando materialidade+flags como dado do risco; só-MATERIAL-promove sumiria com NÃO-MATERIAL-ototóxico (viola D-ARQ-34 Parte 4 + anti-supressão D-ARQ-31). Marcas: Partes 1-2 [DERIVADO — analogia D-ARQ-23 / extensão D-ARQ-02]; Parte 3 [INTERPRETADO — prioridade na revisão de saída].

**Furo de flags sinalizado (decisão de fatia, não fechada aqui).** Componente carrega só is_carcinogeno_iarc + is_sensibilizante (003.J), NÃO is_ototoxico. Solvente ototóxico de FDS (tolueno) promovido por cópia-pra-frente perde gatilho de R-AUD-01. Saída na implementação: crescer flags de Componente OU re-hidratação determinística por-slug de agentes.yaml para flags que a ficha não carrega (por-slug ≠ conflito-de-fonte; é flag ausente na ficha, não divergente). Adiado conscientemente, com gate de estado real exigido antes.

**Estado / verificação.** Sessão de ARQUITETURA pura — sem branch de código, sem commit de motor, sem suíte (nenhum código tocado). Baseline herdado 222 isolado (não remedido nesta sessão; reconfirmar no kickoff da 003.P). main intocada nesta sessão (ARQUITETURA pura, sem código); SHA de abertura conforme kickoff. Gate de estado real para a IMPLEMENTAÇÃO futura: grep do Stage 2 médico (stage_2_riscos, merge de fontes de risco) + de quem constrói Risco a partir de fonte não-inventário, antes de qualquer prompt cirúrgico.

**Pendências.** Inalteradas: DT-FDS-01 (R-BIO-02, lado-médico), DT-FDS-02 (unidade cutoff 5%), DT-003L-01 (6 formas de declaração), DT-003M-01 (CAS oculto), DT-003M-02 (12 inertes-com-CAS + cas-vazio + regra que consome flag), DH-003M-01 (\r\n literal — vigiar ao gravar este bloco), DH-003A-01, demais do balde. D-ARQ-35 NÃO fecha DT-003M-02 — desenha a promoção que a consumirá; a hidratação CAS→slug→flags (D-ARQ-25 Parte B) segue inexistente.

**Próxima sessão (003.P).** Decisão do Diovanni. Candidatos naturais: (i) IMPLEMENTAÇÃO da fatia 1 de D-ARQ-35 (promoção Componente→Risco em Stage 2, isolável com componentes sintéticos como a 003.J fez com o predicado — o dado precede a regra); (ii) primeira regra química em regras.yaml (lado-químico vazio, consome o risco promovido); (iii) a hidratação CAS→slug→flags (D-ARQ-25 Parte B) que dá combustível real. Recomendação do Arquiteto: (i) — é o consumidor que torna o predicado de materialidade exercitável end-to-end, e isola sem depender da hidratação. Ler docs vivos inteiros antes; gate de estado real (grep Stage 2) antes do prompt cirúrgico; checkout main && pull antes de criar branch.

## Sessão 003.P — 14/06/2026 — ARQUITETURA→IMPLEMENTAÇÃO (D-ARQ-35 fatia 1: promoção Componente→Risco)

**Foco.** Candidato (i) do handoff 003.O, confirmado pelo Diovanni: fatia 1 de D-ARQ-35 — dar consumidor de produção ao predicado de materialidade, órfão desde 003.J, promovendo componente químico de FDS a `Risco` (4ª fonte) no Stage 2 médico. Abriu em ARQUITETURA curta (fechar a forma) e transitou para IMPLEMENTAÇÃO.

**Gate de estado real (tipo compartilhado → repo inteiro).** `git show` de `tipos.py`, `estagios/riscos.py`, `materialidade.py`. Achados que fecharam a forma: (1) `Risco.fonte: str` já é o discriminante das 3 fontes — 4ª fonte não exige campo novo, só novo valor (`"quimico_composicao"`). (2) `Risco.agente: str` obrigatório → componente ramo-0 (sem slug) não pode virar `Risco`, força não-promoção+pendência. (3) `Risco.is_ototoxico` existe (002.H) e o Stage 2 já o re-hidrata de agentes.yaml por-slug nas Fases A/B — o "furo de flags" do handoff não era decisão de fatia: o padrão vivo já tapava. (4) `Componente` e `Risco` têm flags disjuntas (materialidade no Componente, conduta-física no Risco) → cada flag tem origem única forçada. (5) ciclo de import (`tipos`↔`materialidade`) resolvido movendo o enum para `tipos`.

**Passada adversarial (1, decisiva) + correção de procedência.** A recomendação inicial incluía dedup de risco na Fase C "por consistência com a Fase B". A passada matou: a Fase B funde porque implícito-por-cargo e explícito são o MESMO risco por duas lentes; a Fase C promove fonte distinta com payload distinto (materialidade, quantificação None) — fundir contraria D-ARQ-16 literal ("convergência no Stage 8, nunca fusão de risco; fundir destrói audit trail") e seria mutação silenciosa de risco explícito por dado químico (classe D-ARQ-22). Correção: sem dedup, riscos coexistem por `fonte`. A passada também achou o furo dos ramos 2/3: promover com `materialidade=AUSENTE` sem pendência irmã entraria mudo — corrigido para promove+pendência bloqueante. Correção factual sobre o handoff/Base de D-ARQ-35: "espelhar D-ARQ-23" é analogia conceitual correta, mas D-ARQ-23 é PROPOSTA sem código — o molde real espelhado no `riscos.py` é R-GHE-02/Fase B (implícito-por-cargo) + hidratação por-slug D-ARQ-12. O "furo de flags" que o handoff 003.O marcou como decisão de fatia também se dissolveu: o gate de estado real mostrou as Fases A/B já re-hidratando `is_ototoxico` do yaml por-slug — não era decisão, era padrão vivo.

**Entrega.** Commit `cddf092`. `Risco` +3 campos; `Materialidade` em `tipos.py`; Fase C em `stage_2_riscos`; `test_promocao_quimico.py` (7 sintéticos: MATERIAL, NÃO-MATERIAL-promovido, carcinógeno-<5%, ramo-0, ramos-2/3-AUSENTE+pendência, re-hidratação-ototóxico por-slug, sem-dedup). Sem consumidor: `regras.yaml`/emissão intocados.

**Estado / verificação.** Baseline herdado da 003.N reconfirmado: 222 isolado verde (sem recalibração — bateu exato). Pós-fatia: 229 isolado (222 + 7). Completa não-mensurável no container (sem pandas/python-docx) — não cravada. mypy --strict limpo, 16 arquivos. Blast radius confirmado por `git show --stat`: só os 4 arquivos previstos (`tipos.py`, `materialidade.py`, `estagios/riscos.py`, `test_promocao_quimico.py`). Fase C verificada à mão contra a spec (três-caminhos, sem-dedup, origens-de-flag). Número desta sessão LIDO do HISTORICO (003.O → 003.P), não calculado. Branch `feature/003p-promocao-componente-risco`; main intocada pelo código até o merge do Diovanni (PR, "Create a merge commit"). Achado lateral verificado e benigno: `test_materialidade_fds.py` (003.M, mergeado) passa verde por re-export de `Materialidade` → DH-003P-01.

**Pendências.** DH-003P-01 nova (imports de `Materialidade` re-exportador). Inalteradas: DT-FDS-01 (R-BIO-02, lado-médico), DT-FDS-02 (unidade cutoff 5%), DT-003L-01 (6 formas de declaração), DT-003M-01 (CAS oculto), DT-003M-02 (12 inertes-com-CAS + cas-vazio + hidratação CAS→slug→flags), DH-003M-01 (`\r\n` literal), DH-003A-01, demais do balde. D-ARQ-35 fatia 1 NÃO fecha D-ARQ-35 — restam: regras químicas em `regras.yaml` (consumidor do risco promovido) e a hidratação CAS→slug→flags (D-ARQ-25 Parte B) que dá combustível real.

**Próxima sessão (003.Q).** Decisão do Diovanni. Candidatos: (i) primeira regra química em `regras.yaml` — consome o `Risco(fonte="quimico_composicao")` agora existente (lado-químico vazio: 0 de 18 regras dispara por componente/agente-químico). É o próximo elo lógico promoção→conduta; isola com componentes sintéticos como esta fatia, mas exercita só sobre dado sintético — não é travessia de produção. (ii) hidratação CAS→slug→flags (D-ARQ-25 Parte B, inexistente) — o gargalo real para dado de FDS de produção entrar; pré-requisito de qualquer validação Viverde com FDS real. (iii) DH-003P-01 + varredura de imports (sessão curta de higiene). Ressalva honesta: sem a hidratação (ii), os `Componente` com `agente`/flags preenchidos só existem em fixture sintética; (i) fecha o par promoção→conduta mas não torna nada "end-to-end de produção" — ambos rodam em isolamento sintético até (ii) existir. Recomendação do Arquiteto, leve: (i) por menor superfície e por fechar o par lógico que a 003.P deixou pela metade; mas (ii) é defensável abrir primeiro. Escolha do Diovanni entre dois caminhos parelhos. Ler docs vivos inteiros; gate de estado real (grep emissão + `regras.yaml`) antes do prompt cirúrgico; checkout main && pull antes de criar branch.

## Sessão 003.Q — 15/06/2026 — ARQUITETURA→IMPLEMENTAÇÃO (D-ARQ-35 fatia 2: primeira regra química — R-PKG-BZ consome a 4ª fonte)

**Foco.** Candidato (i) do handoff 003.P, confirmado pelo Diovanni: a primeira regra de conduta disparada por agente químico, consumindo o `Risco(fonte="quimico_composicao")` que a Fase C (003.P) promove. Abriu em ARQUITETURA (fechar a forma da regra + predicado, três decisões de procedência) e transitou para IMPLEMENTAÇÃO. Escolha de (i) sobre (ii) hidratação: (i) é o próximo elo lógico promoção→conduta, menor superfície, isola sintético como a 003.P; sinal fraco do `fds_originais/` novo no working tree (pró-(ii)) pesado e descartado — não inverte recomendação com handoff+HISTORICO atrás por um diretório untracked.

**Gate de estado real (escopo do motor — (i) não migra tipo compartilhado).** Lidos: `regras.yaml` inteiro (confirmado lado-químico VAZIO: 18 regras, 0 dispara por agente químico — todas físicas/atividade/RX; R-PKG-SOLD e R-PKG-ARMADOR existem só no protocolo, não materializados em regras.yaml), `predicados.py` (primitivos por-identidade leem `any(r.agente == "slug")` sem filtrar `fonte` → primitivo `benzeno` captura automaticamente o risco promovido), `estagios/riscos.py` (Fase C copia `is_carcinogeno_iarc`/`is_sensibilizante`/`materialidade` do Componente, não do yaml — só `is_ototoxico`/anexo vêm do yaml por-slug), `emissao.py` (`emite` suporta múltiplos exames — R-PKG-ATIVCRIT prova; `_validar_exames_em_regras` no `carregar()` levanta `ValueError` se regra referencia slug de exame inexistente → rede contra slug faltando), `exames.yaml` + `agentes.yaml` (medido o que falta). `protocolo.py` (loader): `agentes`/`exames` são `dict[str, Any]` sem schema tipado → `tem_lt: null` entra sem quebrar mypy; `protocolos_especiais` não é validado cross-ref.

**O que o gate mediu como faltante (a fatia é regra + 2 slugs + 1 agente, não só regra).** `hemograma` existia; `reticulocitos`, `acido_transmuconico`, `benzeno` NÃO existiam. Coeso (tudo serve a R-PKG-BZ, regra VALIDADO do protocolo), uma frente, gorda como 002.Y. Não recortado: emitir só hemograma quando o pacote manda três seria subdimensionamento silencioso (D-ARQ-22).

**Três passadas adversariais sobre o prompt (procedência).** (1) `tem_lt: false` cravado por inércia em benzeno — valor factual sem marca (gate D-ARQ-22). Grep `tem_lt` no motor: ZERO leituras → campo inerte; resolvido com `tem_lt: null` + comentário de procedência (eixo Quadro 1/2 / IBE = débito DT-FDS-01), não `false` cravado. (2) Caso-âncora trocado: o Teste 1 inicial usava `is_carcinogeno_iarc=True` (caminho fácil, bypass→MATERIAL sem pendência); reescopado para benzeno <5% sem carcinógeno → NÃO-MATERIAL + R-PKG-BZ dispara mesmo assim (caso literal de R-FDS-04, "carcinógeno independe de concentração"), com materialidade como dado, não porteira. Bypass-carcinógeno virou Teste 2 complementar. (3) Asserção reforçada: Teste 1 crava periodicidade+momentos dos TRÊS exames (não só hemograma), senão typo em `reticulocitos`/`acido_transmuconico` passaria verde.

**Procedência das periodicidades (gate D-ARQ-22).** hemograma 6M [adm/per/MR/dem] e t,t-mucônico 6M [per] = [VALIDADO — R-PKG-BZ] (protocolo crava). reticulócitos: protocolo dá momentos, NÃO periodicidade → 6M [DERIVADO — analogia hemograma R-PKG-BZ]. benzeno: `cas: "71-43-2"` [DERIVADO — CAS Registry], `is_carcinogeno_iarc: true` [DERIVADO — IARC grupo 1], `anexo_nr07: null`/`tem_lt: null` (débito DT-FDS-01; regra dispara por identidade, não por anexo/LT → null honesto). Slug `acido_transmuconico` é convenção interna de vocabulário (não termo normativo — não há "slug oficial" a derivar de NR); decisão de grafia do Diovanni. A conferência do IBE do benzeno no Anexo I vigente é DT-FDS-01 (lado-médico, sessão própria, pendência pré-existente desde 003.F) — fora de (i); (i) consome R-PKG-BZ como está, regra VALIDADO.

**Predicado agnóstico à fonte E à materialidade.** `benzeno` dispara por presença de slug em `ctx.riscos`, sem filtrar `fonte` (captura explícito do inventário OU promovido da composição — D-ARQ-02, status equivalente) nem `materialidade` (carrega como dado, D-ARQ-35 Parte 3, não porteia a conduta). O que (i) prova: um agente que SÓ chega via composição-FDS agora vira conduta.

**Entrega.** 5 arquivos previstos + 1 não-previsto (ver desvio): `agentes.yaml` (benzeno), `exames.yaml` (reticulocitos, acido_transmuconico), `predicados.py` (primitivo `benzeno`), `regras.yaml` (R-PKG-BZ, status VALIDADO), `test_regra_benzeno.py` (novo, 4 testes: <5%-dispara-via-4ª-fonte / bypass-carcinógeno-MATERIAL / benzeno-no-inventário-também-dispara / sem-benzeno-não-vaza). Pipeline Stage 2→Stage 5 nos testes (prova que a promoção da 003.P alimenta a emissão). Commit `ab1b386`, merge `1078baa` (PR #77, "Create a merge commit").

**Desvio de processo (Code aplicou correção de 6º arquivo antes de reportar).** `test_vocabulario_exames_carrega_com_7_slugs` (002.D1, asserção de contagem exata) quebrou por consequência mecânica direta do Arquivo 2 (2 slugs novos em `exames.yaml` → 7 viraram 9). Code renomeou para `_com_9_slugs`, somou os dois slugs ao conjunto esperado, aplicou e reportou DEPOIS — ordem aplicar→reportar, não reportar→decidir→aplicar. Correção certa e mínima, verificada à mão pós-merge (`git show ab1b386 -- test_vocabulario.py` + leitura integral: só a contagem mudou, nenhuma outra asserção tocada; slugs batem com `exames.yaml`; o teste-irmão `test_todo_exame_tem_nome_exibicao_e_categoria` valida que `laboratorial` dos dois slugs novos está na lista de categorias aceitas — passou, sem categoria fora do vocabulário). Aceita sem refação (reverter para reaplicar idêntico seria teatro). Mas teste pré-existente que quebra por consequência mecânica de arquivo autorizado AINDA é STOP-and-report — a regra "bloqueador = decisão do Arquiteto" já cobre; o caso bom é 002.H, onde a correção análoga (test_predicados_stage por R-AUD-02, 7º arquivo fora do plano) passou pelo Arquiteto ANTES de entrar. Sem D-ARQ novo (regra vigente endereça; 002.D1 manda não inflar D-ARQs com decisão de implementação). Reforço durável até onde o mecanismo permite: o handoff da 003.R carrega a instrução de que a verificação final do Code reporte teste pré-existente vermelho em vez de aplicar — o handoff sobrevive uma sessão; permanência além disso (linha no protocolo do Code) é decisão do Diovanni, não cravada aqui.

**Estado / verificação.** Baseline herdado da 003.P reconfirmado ANTES de codar: 229 isolado verde (sem recalibração — bateu exato). Pós-fatia: 233 isolado (229 + 4). Completa não-mensurável no container (sem pandas/python-docx) — não cravada, herdada não-mensurável. mypy --strict limpo (`predicados.py` + `test_regra_benzeno.py`, nomeados). Blast radius (`git show --stat`): 6 arquivos — os 5 previstos + `test_vocabulario.py` (ver desvio). Branch gate disparou (Code parou em `main`, `feature/003q-regra-benzeno` criada). Número desta sessão LIDO do HISTORICO (003.P → 003.Q), não calculado. Sinal de working tree: `fds_originais/` apareceu untracked junto de `matrizes_originais/` — nenhum staged (regra permanente), crescimento de insumo.

**Pendências.** Inalteradas: DH-003P-01 (imports de `Materialidade` re-exportador — não tocada), DT-FDS-01 (R-BIO-02 / a posição do benzeno no eixo Quadro 1/2 do Anexo I — pendência pré-existente desde 003.F, a 003.Q encostou e deixou aberta de propósito), DT-FDS-02 (unidade cutoff 5%), DT-003L-01 (6 formas de declaração), DT-003M-01 (CAS oculto), DT-003M-02 (12 inertes-com-CAS + cas-vazio + hidratação CAS→slug→flags), DH-003M-01 (`\r\n` literal — vigiar ao gravar este bloco), DH-003A-01, demais do balde. D-ARQ-35 fatia 2 NÃO fecha D-ARQ-35 — resta a hidratação CAS→slug→flags (D-ARQ-25 Parte B, inexistente) que dá combustível de produção; R-PKG-BZ roda só em sintético até ela existir.

**Próxima sessão (003.R).** Decisão do Diovanni. Candidatos: (i) hidratação CAS→slug→flags (D-ARQ-25 Parte B, inexistente) — o gargalo real para FDS de produção entrar; pré-requisito de qualquer validação com FDS real; fatia maior, abre como ARQUITETURA (a fronteira da extração LLM↔determinístico nunca foi decidida — D-ARQ-25/33 dão a topologia, falta a forma). (ii) mais conduta química em `regras.yaml`: materializar R-PKG-SOLD/R-PKG-ARMADOR (pacotes hoje só no protocolo) — atenção, esses disparam por cargo/fumos_metalicos (risco físico-químico de inventário), NÃO pela 4ª fonte de composição; molde distinto de R-PKG-BZ; continua sintético. (iii) higiene: DH-003P-01 + DH-003M-01 + varredura de imports `Materialidade`. Ressalva honesta: (i) é o único que move em direção a dado real — (ii) aprofunda o sintético que já fechou o par promoção→conduta. Recomendação do Arquiteto: inclinação leve para (i) — a fatia que falta para sair do sintético; o `fds_originais/` no working tree sugere que dado real pode ser o norte. Mas é fatia maior e a fronteira de extração (D-ARQ-25) nunca foi decidida — abrir como ARQUITETURA, não IMPLEMENTAÇÃO. Ler docs vivos inteiros; gate de estado real antes do prompt cirúrgico; checkout main && pull antes de criar branch.

## Sessão 003.R — 15/06/2026 — CONHECIMENTO→ARQUITETURA (D-ARQ-36: sub-camada determinística de resolução; gate-CAS é a fatia 1 de (i))

**Foco.** Candidato (i) do handoff 003.Q — hidratação CAS→slug→flags (D-ARQ-25 Parte B) — confirmado pelo Diovanni, aberto em ARQUITETURA. Recomendação do Arquiteto (i) sobre (ii)/(iii): única frente que sai do sintético; o predicado de materialidade está órfão de consumidor de produção desde a 003.J e (i) constrói a costura que D-ARQ-34 Parte 4 pressupõe pronta. Escopo estreitado por passada adversarial: (i) é arco, não fatia; a sessão fecha a FORMA da fronteira de extração + a fatia 1 (gate-CAS), não o arco.

**Gate de abertura.** Merge da 003.Q reconfirmado: fast-forward trouxe `11fc060` (PR #78, fechamento docs 003.Q) sobre `d8d2634`; main no topo do fechamento 003.Q. Baseline 233 isolado herdado (não medido — sessão ARQUITETURA, nenhum arquivo de código tocado). Docs vivos lidos inteiros (PROTOCOLO depois DECISOES) — metade-inicial obrigatória cumprida antes de qualquer D-ARQ.

**A contradição que virou a espinha da sessão.** Leitura literal expôs tensão D-ARQ-34 Parte 4 ("flags chegam pela ficha já normalizada, extração resolveu CAS→slug→flags") × 003.P (re-hidratou is_ototoxico/anexo_nr07 de agentes.yaml por-slug no Stage 2 médico). Hoje sintético, ninguém percebe; (i) é exatamente a fatia que constrói o "CAS→slug→flags" que D-ARQ-34 dá por pronto. A costura tinha de fechar primeiro, ou implementaria sobre contrato ambíguo.

**Três passadas adversariais sobre a forma (escopo).** (1ª) Proposta inicial empilhou quatro decisões de forma (DF-1 extração bicamada; DF-2 fonte canônica de flag = resolvedor, remover re-hidratação do médico; DF-3 honrar frase-H sem slug→MATERIAL; DF-4 4 ramos do gate). (2ª, a pedido do Diovanni) DF-3 caiu: inverte o ramo 0 da 003.J (`agente is None → AUSENTE`, justificado como anti-supressão-silenciosa) e É o enunciado de DT-003M-01 `[ABERTA]` — importei DT aberta como corolário; quebra "uma coisa por vez"; retirada, volta a sessão própria. DF-2 rebaixada: cravá-la decide destino de costura que a fatia 1 (gate-CAS) não toca; vira nota de não-conformidade diferida, não decisão. Correção factual: DF-1 não é leitura nova de D-ARQ-09 — é D-ARQ-33 cl.1 ("descoberta CAS via LLM a montante, preserva D-ARQ-09 nos dois lados") tornada explícita; parei de vendê-la como achado. (3ª, "seja crítico") confirmou: removidas DF-2/DF-3, o que sobra é só o gate-CAS — estreito, testável com CAS sintéticos, sem depender de nenhuma decisão diferida nem da reabertura do predicado.

**Decisão — D-ARQ-36 (nova ID; autorizada pelo Diovanni).** Sub-camada determinística de resolução de composição. Parte 1: extração = LLM-transcrição (nome/CAS/faixa/frases-H; na zona R-FDS-04 propõe CAS-candidato baixa-confiança→revisão humana) + resolvedor determinístico (valida CAS→CAS→slug→popula flags→monta Componente); fronteira LLM↔determinístico é "CAS transcrito"; releitura de D-ARQ-34 Parte 4 (ficha normalizada = saída do resolvedor); resolvedor só tem CAS→slug (name→slug fica indeciso em D-ARQ-25 Parte B). Parte 2: gate-CAS é a fatia 1, 4 ramos — (a) válido+slug→hidrata; (b) válido+sem-slug→Pendencia vocabulario_ausente não-bloqueante (D-ARQ-14), agente=None, bloqueio fica no predicado 003.J, não duplica; (c) inválido no dígito→Pendencia bloqueante (fantasmas 022-00-9/014-00-0 da 003.F caem aqui, dígito conferido); (d) oculto/ausente→Pendencia, oculto≠inválido (DT-003M-01), honrar frase-H reabre ramo 0 da 003.J→fora. Parte 3: unificação da fonte-de-flag é direção, não decisão; 003.P não tocada nesta sessão (gate-CAS não popula flags); remover re-hidratação do médico = item próprio, STOP-and-report, decidido pelo Diovanni; até lá redundância benigna idempotente.

**Dois limites honestos confirmados na passada final (recomendação: declarar e seguir, não adicionar mecanismo).** (1) Gate valida boa-formação, não correção-de-transcrição: CAS transcrito errado mas válido no dígito resolve pra slug errado, pego só pela revisão de saída (D-ARQ-22) / responsável técnico (D-ARQ-33 cl.4, R-PGR-01) — não pelo gate. Cross-check nome↔CAS descartado da fatia 1: pressupõe name→slug que a Parte 1 exclui do escopo; é outra coisa, pós-decisão de name→slug, não fatia futura do gate. (2) Ramo (b) não-bloqueante mantido: mover bloqueio pro gate duplica integridade que D-ARQ-17 centralizou e a 003.J materializou; o gate é lado-engenheiro, o predicado roda nos dois lados — bloquear cedo tiraria do médico a disciplina tri-estado (D-ARQ-13). Adicionar mecanismo em qualquer dos dois seria "parecer completo" vencendo "estar correto" (viés que D-ARQ-22 nomeia).

**Procedência.** Algoritmo do dígito CAS `[DERIVADO — check-digit CAS Registry; conferir contra fonte autoritativa na implementação antes de VALIDADO]` (benzeno 71-43-2 confere; fantasmas da 003.F falham). Topologia bicamada `[DERIVADO — D-ARQ-33 cl.1 literal]`. CAS-candidato LLM `[INTERPRETADO]` por construção (espelha D-ARQ-33 cl.4 — candidato, não classificação autônoma).

**Estado / verificação.** Sessão ARQUITETURA — nenhum arquivo de código tocado, suíte não medida (233 isolado herdado, intacto). Entrega documental: D-ARQ-36 em DECISOES (v42) + este bloco. Número desta sessão LIDO do HISTORICO (003.Q → 003.R), não calculado. Sem mexer em tipos.py/materialidade.py/regras.yaml/agentes.yaml.

**Pendências.** Inalteradas. DT-003M-01 (frase-H sem slug, ramo-0-vs-bypass) e DT-FDS-02 (unidade do cutoff 5%) explicitamente referenciadas por D-ARQ-36 como fora-de-escopo, sem mudança de status. DH-003P-01 (re-hidratação de Materialidade / imports) ganha contexto: a unificação da fonte-de-flag da Parte 3 é a fatia que a endereça. DH-003M-01 vigiada na gravação deste bloco. Demais do balde inalteradas.

**Próxima sessão (003.S).** Decisão do Diovanni. Candidato natural: fatia 1 de (i) — IMPLEMENTAÇÃO do gate-CAS (D-ARQ-36 Parte 2). Abre direto em IMPLEMENTAÇÃO (a forma está fechada), com gate de estado real obrigatório ANTES do prompt cirúrgico: grep do REPO INTEIRO (tipo compartilhado, refino 003.I) por quem produz/consome Componente/ProdutoQuimico/FaixaConcentracao + leitura de parser_pgr.py/ia_client.py (referência, não base a portar — D-ARQ-25 Parte A) + leitura literal de D-ARQ-33/36. Reconfirmar 233 isolado antes de tocar arquivo (STOP-and-report se divergir). Alternativas defensáveis: (ii) materializar R-PKG-SOLD/ARMADOR; (iii) higiene DH-003P-01/DH-003M-01. Ler docs vivos inteiros; checkout main && pull antes de criar branch.

## Sessão 003.S — 15/06/2026 — IMPLEMENTAÇÃO (D-ARQ-36 fatia 1: gate-CAS, resolvedor determinístico)

**Foco.** Fatia 1 do arco (i) — gate-CAS (D-ARQ-36 Parte 2), confirmada pelo Diovanni. Abriu DIRETO em IMPLEMENTAÇÃO: a forma fechou na 003.R, não se reabriu ARQUITETURA. Único vetor que sai do sintético; constrói a costura CAS→slug que D-ARQ-34 Parte 4 pressupõe pronta.

**Gate de abertura.** Merge da 003.R reconfirmado: `c8a1428` (Merge PR #79, fechamento docs 003.R) no topo de `main`, sincronizada com origin — o merge que o handoff dava como pendente já ocorrera. Branch `feature/003s-gate-cas` criada de `main` atualizada (gate de branch ✓). Baseline 233 isolado RECONFIRMADO por pytest real (não herdado) — sem divergência, STOP-and-report não disparou. Docs vivos lidos em literal (DECISOES D-ARQ-33/34/35/36 + tipos.py + materialidade.py + riscos.py) — paráfrase do Code recusada três vezes em favor do texto cru; a recusa pagou: o resumo omitira `Pendencia.destinatario`/`motivo` (obrigatórios) e dera o algoritmo do dígito como `[DERIVADO]` quando esta sessão já o promovera a `[VALIDADO]`.

**Três decisões de forma fechadas no kickoff (não reabertura de ARQUITETURA — mesmo tipo de decisão-de-implementação que a 003.I tomou sobre FaixaConcentracao).** (1) Retorno `tuple[Componente, Optional[Pendencia]]` — árvore de ramos exclusiva, no máximo uma pendência. (2) Ramo (d) não-bloqueante, por simetria com D-ARQ-33 cl.3 ("sem CAS resolvível → Pendencia" sem bloqueante, na mesma frase em que o straddle É bloqueante) e porque oculto≠inválido — o bloqueio mora downstream na Fase C. (3) Índice CAS→slug CONSTRUÍDO pelo gate, porque o índice inverso NÃO existia — grep confirmou `agentes.yaml` lido só por-slug; o gate inverte o vocabulário (colisão → ValueError, molde leo_resolver).

**Duas passadas adversariais (obrigatórias), ambas mantiveram a recomendação.** (a) "(d) deveria ser bloqueante por ser mais opaco que (b)?" → não: cl.3 trata ausência-de-CAS como não-bloqueante; gravidade capturada downstream; (c) é assimétrico de propósito (malformação ≠ ausência legítima). (b) "(a) não popular flags propaga is_carcinogeno_iarc errado pela cópia-pra-frente?" → real, mas só se plugado; a fatia 1 é isolada por construção, e a população de flags É a Parte 3 diferida. Ambas mantidas.

**Decisão de localização.** Módulo greenfield `agente_medico/motor/resolvedor.py`, plano (paralelo a materialidade.py), sem submódulo `engenharia/` — `ProdutoQuimico` não tem produtor de produção (grep: todos os hits fora de tipos.py são tests/), e o gatilho de promoção D-ARQ-16 ("dois casos provam o padrão") não disparou com um arquivo só.

**Entrega.** `resolvedor.py` (4 funções puras: `_so_digitos`, `cas_bem_formado`, `construir_indice_cas`, `gate_cas`) + `test_resolvedor.py` (13 testes sintéticos). Commit `5429954`, blast radius conferido por `git show --stat` = 2 arquivos / 223 inserções, ZERO vazamento para tipos.py/riscos.py/yaml. NÃO popula flags (Parte 3 diferida). Isolado, sem consumidor (espelha o predicado isolado da 003.J). Algoritmo do dígito verificador promovido `[DERIVADO]`→`[VALIDADO]`: CAS.org (fonte autoritativa primária) + Apache Commons Validator / Wikipedia / ThermInfo / R-httk; benzeno 71-43-2, água 7732-18-5, metanol 67-56-1 conferem; fantasmas 022-00-9/014-00-0 falham.

**Estado / verificação.** Suíte 233→246 isolado (+13). mypy --strict limpo (17 arquivos). Nenhum teste pré-existente vermelho. Os +13 (vs ~7 do prompt) = granularidade dentro dos ramos especificados, não escopo vazado — confirmado por `git show --stat`. Recalibração de baseline registrada: 246 é o novo número isolado. Número desta sessão LIDO do HISTORICO (003.R → 003.S), não calculado.

**Pendências.** Inalteradas. DH-003P-01 (re-hidratação por-slug do médico) NÃO tocada — é exatamente o que a Parte 3 de D-ARQ-36 endereça (próxima fatia natural). DT-003M-01 (frase-H sem slug / oculto-declarado) e DT-FDS-02 (unidade do cutoff) seguem fora de escopo, referenciadas por (d). Demais do balde inalteradas.

**Próxima sessão (003.T).** Decisão do Diovanni. Candidato natural: D-ARQ-36 Parte 3 — população de flags / unificação da fonte-de-flag, que pluga o gate-CAS num consumidor real e remove a re-hidratação por-slug da 003.P (endereça DH-003P-01); é o vetor que tira o is_carcinogeno_iarc errado da cópia-pra-frente. STOP-and-report, decisão do Diovanni. Alternativas: (ii) materializar R-PKG-SOLD/R-PKG-ARMADOR; (iii) higiene DH-003P-01/DH-003M-01. Abre em ARQUITETURA se a forma da Parte 3 não estiver fechada; gate de estado real + leitura literal antes de qualquer prompt. checkout main && pull antes de criar branch.

## Sessão 003.T — 16/06/2026 — IMPLEMENTAÇÃO (D-ARQ-36 Parte 3, fatia 2: gate-CAS popula is_carcinogeno_iarc)

**Foco.** Fatia carcinógeno da Parte 3 de D-ARQ-36 — gate-CAS passa a popular `is_carcinogeno_iarc` no `Componente` resolvido, fechando o `resolvedor.py:64` ("NÃO popula flags"). Decisão de foco precedida de 4 passadas de refinamento que estreitaram o escopo: a "Parte 3" do handoff era uma direção ampla (unificação de fonte-de-flag); leitura literal de `riscos.py` + `resolvedor.py` + dois greps de repo inteiro reduziram-na à única peça acionável hoje sem o motor irmão existir — popular no gate a flag que ele recusava popular.

**Gate de abertura.** main `3d2c161` reconfirmada (003.S no topo); working tree limpo; branch `feature/003t-gate-flags` de main atualizada. Docs vivos lidos em literal (PROTOCOLO v23 inteiro, depois DECISOES até D-ARQ-36/v43). Baseline 246 isolado reconfirmado.

**Refinamento de escopo (4 passadas).** (1) "Plugar o gate na Fase C" — DESCARTADO: atravessa a fronteira de ofícios (gate é lado-engenheiro a montante da mesa; Fase C é lado-médico a jusante), localiza o plug no lado errado. (2) Grep de flags revelou que NÃO há divergência de fonte (cada flag tem fonte única: carcinógeno/sensibilizante por cópia-pra-frente do Componente; ototóxico/anexo por re-hidratação por-slug — partição limpa, não competição). O "is_carcinogeno_iarc errado pela cópia-pra-frente" do handoff é incompletude (gate deixa a flag órfã → cópia-pra-frente propaga `False` falso), não divergência. (3) Recomendação inicial de incluir `is_sensibilizante` no `EntradaIndice` degradando para `False` com marca-comentário — REVERTIDA na 2ª passada (gatilho: pergunta do Diovanni): é fiação fantasma de dado inexistente, marca no código-fonte ≠ marca no dado, `False` tipado indistinguível de classificação (erro silencioso D-ARQ-22). (4) Gate de procedência sobre `agentes.yaml` confirmou `is_carcinogeno_iarc` presente/explícita em todos os agentes (benzeno `71-43-2`→`true`); `is_sensibilizante` AUSENTE → recortada (DT-003T-01).

**Decisão de forma (kickoff IMPLEMENTAÇÃO).** Forma (2) — índice rico `EntradaIndice` (frozen, slug+flag) substitui `dict[str,str]`; leitura do vocab uma vez na construção do índice, gate com um só argumento, fixture de teste com uma só estrutura. Recusadas (1) (espalha leitura do vocab por chamada, duplica fixture) e (3) (deixa o `:64` aberto).

**Entrega.** `resolvedor.py`: `EntradaIndice` novo; `construir_indice_cas` retorna `dict[str, EntradaIndice]` (colisão cita `entrada.slug`); `gate_cas` ramo (a) faz `replace(agente, is_carcinogeno_iarc)`, ramos b/c/d intactos; docstring atualizada (popula carcinógeno; sensibilizante fora por DT-003T-01; ototóxico/anexo no lado-médico). `test_resolvedor.py`: 3 testes pré-existentes corrigidos por consequência mecânica (forma do valor do índice) — REPORTADOS antes de corrigir (relatório de vermelhos contra o real: 2 de `construir_indice_cas` + 1 do ramo (a) por `_INDICE` desatualizado; `test_indice_colisao` ficou verde, não asserta forma do valor) — autorização explícita do Diovanni antes da correção; +2 testes novos (par benzeno-`True`/água-`False` provando população-do-dado, não `True` cravado). NÃO toca Fase C de `riscos.py` (gate segue órfão), nem `is_sensibilizante`, nem `tipos.py`/yaml. Commit `f308693`, merge `9058884` (PR #81, "Create a merge commit").

**Estado / verificação.** Suíte 246→248 isolado (+2). mypy --strict limpo (16 arquivos). Nenhum pré-existente vermelho após correção. Blast radius 2 arquivos (`git show --stat`). Parte 3 de D-ARQ-36 segue PARCIAL: fatia carcinógeno feita; unificação-de-fonte-de-flag e `is_sensibilizante` seguem abertas.

**Pendências.** DT-003T-01 nova (`is_sensibilizante` ausente do yaml). DH-003P-01 NÃO tocada. DT-003M-01 referenciada (cruza DT-003T-01). Demais do balde inalteradas.

**Próxima sessão (003.U).** Pauta declarada pelo Diovanni: META — disciplina de push/PR/merge. Avaliar `gh` CLI (hoje não instalado) para o Code PREPARAR o PR (criar/título/body) e PARAR antes do merge; fronteira "Code prepara, Diovanni mergeia" mantida. Recomendação do Arquiteto: reduzir fricção de PR sem mover o gate de merge para o Code — o merge é o ponto de não-retorno e a única revisão holística humana do ciclo; mover ao Code remove a fricção que pegou os erros de julgamento desta sessão. Decisão e forma do D-ARQ na própria 003.U, após resultado do Code (instalação/teste do `gh`).

## Sessão 003.U — 16/06/2026 — META (automação de fluxo Code: avaliada e ADIADA)

**Foco.** Pauta do Diovanni: dado que o fluxo Claude Code está maduro, mover push/PR/merge para o Code? Sessão META — não toca motor nem protocolo clínico.

**Decisão: ADIAR a frente inteira para pós-motor.** Não foi construído D-ARQ, CLAUDE.md, skill de fechamento nem formalização de disciplina. Razão (Diovanni, confirmada pelo Arquiteto em 2ª passada): o fluxo atual — Code commita + entrega título/body, Diovanni abre PR e mergeia no navegador — está funcionando sem problema observado; o valor desta própria sessão (003.T) e desta (003.U) esteve na FRICÇÃO que pegou erros de julgamento, não na execução. Automatizar o PR/merge removeria o gatilho que força a revisão (hoje o navegador põe o Diovanni na frente do diff; PR-create automático tornaria a revisão opcional — risco confirmado pelo Diovanni). Custo de oportunidade decisivo: sessões são o recurso escasso e o motor químico é o caminho crítico (gate-CAS órfão desde 003.S; Parte 3 de D-ARQ-36 parcial; hidratação CAS→slug→flags inexistente). Formalizar disciplina de fluxo agora seria congelar uma disciplina ainda em mudança (dado precede regra; gatilho de formalização não disparou).

**Achados registrados como pendência (não perdidos):**
- **DH-003U-01 (nova):** a disciplina de fluxo Code↔git↔PR (git add nominal; matrizes_originais/+fds_originais/ nunca staged; "Create a merge commit" nunca squash/rebase; push/merge do Diovanni; uma implementação por sessão; branch gate; teste pré-existente vermelho → reportar; verificação por git show --stat) vive SÓ no prompt de Arquiteto, NÃO versionada no repo (grep confirmou: 35 hits em docs/, todos registro de auditoria; zero regra; zero em .claude/). Dívida tácita-crítica, classe "estado/regra fora da fonte-de-verdade". NÃO-bloqueante (prompt recolado intacto a cada sessão, funcionando). Adiada para pós-motor: quando o projeto maduro for ganhar um CLAUDE.md (mecanismo canônico do Claude Code — carregado toda sessão, sobrevive a /compact, autoritativo), a disciplina entra junto, com o gate de revisão de diff como passo de uma skill de fechamento (cabe na exceção .claude/skills/ já aberta por D-ARQ-26) e o merge retido por escopo de permissão (allowed-tools sem gh pr merge). Forma já esboçada nesta sessão; gravação deliberadamente NÃO feita.
- **Nota Cowork (ferramenta, sem D-ARQ):** Cowork avaliável para frentes exploratórias-reversíveis (varredura dos PDFs em matrizes_originais/+fds_originais/ → input para DT-003L-01/extração D-ARQ-25; auditoria de consistência dos docs vivos; briefing de estado). NÃO para motor nem merge — Cowork não tem audit trail (sem Audit Log/Compliance API/Export, inadequado a dado regulado), colide com a rastreabilidade regulatória do PCMSO. Decisão de ferramenta, não de arquitetura.

**Estado.** Nenhuma mudança em código, motor, protocolo ou vocabulário. Baseline 248 isolado inalterado. main em `43a45a1` (003.T). Nenhum D-ARQ criado. PROTOCOLO e DECISOES intocados.

**Próxima sessão (003.V).** Decisão do Diovanni — recomendação: voltar ao motor (caminho crítico). Candidatos: (i) Parte 3 de D-ARQ-36 ainda-aberta (unificação de fonte-de-flag, que endereça DH-003P-01) ou o caminho para o motor irmão (consumidor do gate-CAS órfão); (ii) DT-FDS-01 — reabertura clínica de R-BIO-02 sobre o eixo Quadro 1/Quadro 2 (CONHECIMENTO, exige Quadro 2 inteiro, destrava o anexo_nr07 podre); (iii) hidratação CAS→slug→flags / camada de extração (D-ARQ-25 Parte B), o gargalo real de produção. STOP-and-report, decisão do Diovanni. Gate de estado real + leitura literal antes de qualquer prompt cirúrgico.

## Sessão 003.V — 16/06/2026 — ARQUITETURA (motor irmão mínimo: consumidor do gate-CAS + fonte-de-flag resolvida)

**Foco.** Candidato (i) do handoff 003.U, confirmado pelo Diovanni: dar consumidor de produção ao gate-CAS (isolado desde 003.S/003.T) e fechar a costura entre D-ARQ-34 Parte 4 e a aplicação real da 003.P. Mini-sessão de ARQUITETURA — sem código, fecha a forma da fatia que a 003.W implementa.

**Gate de abertura.** main em `c12bfe5` (Merge PR #83, fechamento docs 003.U), sincronizada com origin. Baseline 248 isolado herdado (não medido — sessão ARQUITETURA). Docs vivos lidos inteiros (PROTOCOLO v24 + DECISOES v44) antes de qualquer decisão. Divergência git×HISTORICO esperada e registrada no kickoff: bloco 003.U dizia "main em 43a45a1" (escrito durante a 003.U, antes do próprio merge `c12bfe5`) — artefato normal do protocolo de fechamento, não inconsistência.

**Três passadas de refinamento da recomendação de frente (registradas porque cada uma corrigiu a anterior).** (1ª) Recomendei a frente (i) como "ARQUITETURA da extração D-ARQ-25 Parte B" — IMPRECISO: D-ARQ-36 já fechou CAS→slug e 003.S/T já materializaram o `gate_cas`; o coração da hidratação não estava por construir, estava por CONECTAR. (2ª) Decompus (i) em A (motor irmão mínimo determinístico) / B (LLM-transcrição) / C (name→slug); recomendei A, mas chamei-a de "plug do gate" inflando-a como "motor irmão". (3ª, com o código na mão) o gate de estado real refutou duas afirmações minhas feitas de memória: a fixture `fds_t65` entrega `Componente` com `agente` JÁ populado à mão (não cru), e a Fase C NÃO chama o gate (lê `componente.agente` direto). Logo o gate está DUPLAMENTE órfão (sem produtor a montante e sem consumidor a jusante), e "plugar o gate" só tem valor não-tautológico se a fixture passar a entregar CRU. A decisão A/B colapsou ao ler dois arquivos — lição de método: as três passadas raciocinaram sobre a fixture sem tê-la lido.

**Gate de estado real (lido literal: `git log -10`, `git status`, `fds_t65.py`, `resolvedor.py`, `riscos.py`, `tipos.py`).** Achados que fecharam a forma: (1) `fds_t65` constrói `Componente(cas=..., agente="slug"|None)` — CAS cru presente E slug resolvido à mão; não passa pelo gate. (2) Fase C (`riscos.py`) lê `componente.agente` direto, NÃO invoca `gate_cas`; o elo `cas`→`agente` não existe no pipeline. (3) `tipos.py`: `Componente.is_carcinogeno_iarc: bool` (não `Optional[bool]`); embrulho `ProdutoQuimico(nome, fds: Optional[FDS])` → `FDS(composicao: tuple[Componente,...])` JÁ EXISTE e a Fase C já o lê — nenhuma extensão de tipo necessária. (4) gate ramo (a): `replace(agente=slug, is_carcinogeno_iarc=entrada.is_carcinogeno_iarc)` — sobrescreve sempre a flag pelo yaml.

**Decisão (a) — motor irmão mínimo `resolver_composicao`.** Função pura `(pgr, indice_cas) -> PGR` a montante de `executar()`. Aplica `gate_cas` por componente, remonta a cascata frozen (5 níveis) com composição resolvida. A remontagem via `dataclasses.replace` em cascata é DELIBERADA, não custo aceito a contragosto: mutar uma cópia ou afrouxar `frozen=True` foi rejeitado por quebrar a imutabilidade que sustenta a pureza do motor (D-ARQ-09); o preço em código de remontagem paga a garantia de que nenhum estágio a jusante observa `PGR` mutável. Preserva D-ARQ-33 cl.1/2 (engenheiro resolve, médico promove). Fase C e `executar()` intocados. Fixture `fds_t65` reescrita CRUA (`agente=None` em todos), gate resolve pelo CAS — exercita os 4 ramos sobre os CAS reais das 3 FDS, inclusive (c) TiO₂-CAS-errado `134363-67-7` e (d) Segredo Industrial CAS-oculto. Topologia que B (LLM-transcrição) vai alimentar sem ser desfeita. Nome físico do módulo (`motor/composicao.py` vs. `engenharia/`) deixado aberto para a abertura da 003.W — decisão de implementação (gatilho D-ARQ-16 com o código na mão), não de arquitetura. Honestidade de escopo: A NÃO tira de produção — move a fronteira do sintético para a entrada da transcrição; o salto de produção é B, e B sem A nasceria órfã.

**Decisão (b.2) — fonte-de-flag resolvida a favor da transcrição (STOP-and-report, autorizado pelo Diovanni).** O `gate_cas` deixa de sobrescrever `is_carcinogeno_iarc`: a flag é do componente-neste-produto (via de exposição, ligação em matriz), não da substância em abstrato — yaml dá identidade (slug), FDS dá periculosidade. Reverte a sobrescrita da 003.T no ramo (a); `EntradaIndice.is_carcinogeno_iarc` fica carregado mas inerte (Parte 3 plena = tri-estado + `is_sensibilizante`, sessão própria). Caso-âncora: TiO₂ da Tinta Acrílica (003.M) — yaml=`true` (substância, IARC 2B), Componente=`false` (este produto, base água); honrar o yaml apagaria a divergência substância-vs-produto que D-ARQ-34 Parte 4 protege. A 003.T populou do yaml por não ter consumidor que expusesse o conflito; a 003.V é o primeiro consumidor e ele prova yaml-como-fonte errado para o caso real — não é reversão arbitrária, é a 003.T encontrando o consumidor. Tri-estado `Optional[bool]` descartado (complexidade que a Parte 3 adiou). Precedente forte e recente: a própria 003.T já revertera incluir `is_sensibilizante` pela mesma razão (fiação fantasma, `False` indistinguível de classificação, erro silencioso D-ARQ-22).

**Forma do embrulho.** `resolver_composicao` opera sobre `ProdutoQuimico.fds.composicao` (já existe; Fase C já lê) — sem extensão de tipo. A fixture reescrita monta `ProdutoQuimico(FDS((componentes crus)))` em `GHEPGR.produtos_quimicos`.

**Trilho respeitado.** Nenhuma regra clínica criada/alterada (R-*/R-FDS-* intactas; PROTOCOLO segue v24, intocado). Arco D-ARQ-31 selado. DT-FDS-01 não tocada. DECISOES ganhou changelog 003.V em D-ARQ-36 + nota em D-ARQ-35 → v45.

**Estado / verificação.** Sessão ARQUITETURA pura — nenhum arquivo de código tocado, suíte não medida (248 isolado herdado, intacto). main intocada até o merge do fechamento doc. Número desta sessão LIDO do HISTORICO (003.U → 003.V), não calculado. Operando sob DH-003U-01 aberta (disciplina de fluxo não-versionada) — sem impacto na decisão.

**Pendências.** Inalteradas. DH-003P-01 ganha contexto: a fatia 003.W (motor irmão mínimo) é o produtor que conectará o gate; a unificação plena da fonte-de-flag (Parte 3) segue diferida. DT-003M-01 (frase-H sem slug / CAS oculto) e DT-FDS-02 (unidade cutoff) referenciadas, fora de escopo. DT-003T-01 (`is_sensibilizante` ausente do yaml) liga-se à Parte 3 plena. Demais do balde inalteradas. DH-003M-01 vigiada na gravação deste bloco (newlines reais).

**Próxima sessão (003.W).** IMPLEMENTAÇÃO da fatia: `resolver_composicao` (motor irmão mínimo) + fixture `fds_t65` reescrita crua + reversão da sobrescrita de `is_carcinogeno_iarc` no ramo (a) do `gate_cas` + testes dos 4 ramos sobre os CAS reais das 3 FDS (incl. (c) TiO₂-CAS-errado, (d) Segredo Industrial) + cadeia cru→resolver→Fase C→promoção fechando ponta-a-ponta sobre fixture. Gate de estado real obrigatório: reler `tipos.py`/`resolvedor.py`/`riscos.py`/`fds_t65.py` literais (linhas movem pós-merge); reconfirmar 248 isolado ANTES de tocar arquivo (STOP-and-report se divergir); grep repo inteiro de quem constrói `ProdutoQuimico`/`FDS`/`Componente`. Ler docs vivos inteiros; checkout main && pull antes de criar branch.

## Sessão 003.W — 16/06/2026 — IMPLEMENTAÇÃO (D-ARQ-36 fatia 3: motor irmão mínimo `resolver_composicao` + reversão da fonte-de-flag)

**Foco.** Materializar a forma fechada na 003.V: `resolver_composicao` (consumidor de produção do gate-CAS, isolado desde 003.S/T) + reversão da sobrescrita de `is_carcinogeno_iarc` + fixture crua + migração de testes. Uma leva coesa (decisão A autorizada pelo Diovanni — fixture crua e os testes que a consomem não separáveis sem baseline vermelho entre commits).

**Gate de abertura.** main em `7b378bf` (Merge PR #84), sincronizada. Baseline **248 isolado RECONFIRMADO por pytest real** (não herdado — gate de IMPLEMENTAÇÃO). Docs vivos lidos inteiros (PROTOCOLO v24 + DECISOES v45). Branch `feature/003w-resolver-composicao` criada de main limpa. Quatro literais de produção/fixture + dois de teste + `agentes.yaml` + `materialidade.py` relidos do disco antes de qualquer prompt. Grep de construtores (`ProdutoQuimico`/`FDS`/`Componente`) e de consumidores (`fds_t65`/`stage_2_riscos`/`resolver_composicao`/`executar`) no repo inteiro.

**Passadas adversariais antes do prompt (registradas porque cada uma corrigiu a anterior).** (1ª) Recomendei tratar TiO₂ como servindo ramo (c) E caso-âncora da reversão — IMPOSSÍVEL no mesmo componente (CAS único → ramo único); a arquitetura 003.V já resolvia melhor (CAS errado na fixture → ramo c; reversão provada em `test_resolvedor` com índice sintético). (2ª) Cravei vereditos de materialidade a partir da leitura do D-ARQ-34 no DECISOES, sem ler `materialidade.py` — erro de procedência (cravar valor cuja fonte não está na mão); rebaixados a `[CONFERIR]` e o literal pedido. (3ª) Temi vermelho de integração via Fase C promovendo acetona/acetato; grep de consumidores refutou — só `test_materialidade_fds` importa a fixture, blast radius confinado aos 6 testes da migração (404 legado intocado confirmou).

**Gate de procedência (D-ARQ-22) — `[CONFERIR]` resolvidos pelo Code, não cravados de memória.** `cas_bem_formado("134363-67-7")`=False → TiO₂ errado ramo (c) ✓. `cas_bem_formado("1242-78-3")`=False → aluminato ramo (c), NÃO (b) — o spec deixou em aberto, o Code mediu. `cas_bem_formado("9003-22-9")`=True, sem slug → copolímero PVC ramo (b) ✓. Chaves CAS-normalizadas conferidas com `_so_digitos`. Slugs confirmados em `agentes.yaml`: `metil_etil_cetona`, `acetona`, `acetato_de_etila`, `dioxido_de_titanio`.

**Mudanças (5, blast radius 5 arquivos).** (1) `resolvedor.py`: ramo (a) deixa de sobrescrever `is_carcinogeno_iarc`; docstring de `gate_cas` e `construir_indice_cas` marcam a flag inerte; `test_gate_ramo_a_popula_carcinogeno_true` renomeado/invertido para `test_gate_reversao_nao_sobrescreve_flag` (asserção `is True`→`is False`) — atualização do teste que codificava o comportamento revertido É parte da reversão, não conserto colateral (distinto do desvio 003.Q). (2) `motor/composicao.py` NOVO: `resolver_composicao` puro, remonta cascata frozen, isolado. (3) `fds_t65.py` crua: TiO₂ CAS `13463-67-7`→`134363-67-7`, MEK perde slug, todos `agente=None`. (4) `test_materialidade_fds.py` migrado para cadeia resolvida (`_IDX`+`_resolver`); contagem 1/23/0→2/22/0; loop ramo0 do adesivo `(0,2..6)`→`(2..6)` (acetona[0] resolve MATERIAL). (5) `test_resolvedor.py` +7 testes (reversão + 4 ramos sobre CAS reais, 2 deles ramo c).

**Estado / verificação.** Suíte 248→**255 isolado** (+7) / **404 total** (legado intocado — confirmado, ninguém fora de `test_materialidade_fds` consome a fixture). mypy --strict limpo (`composicao.py` + `resolvedor.py`). Teste da reversão discriminante (falha sob 003.T, passa pós). Número desta sessão LIDO do HISTORICO (003.V→003.W), não calculado. Commit `9029282`, merge `24c058d` (PR #85). PROTOCOLO v24 intocado (nenhuma R-* tocada); DECISOES → v46.

**Honestidade de escopo.** A fatia NÃO tira de produção: `resolver_composicao` nasce ISOLADO, sem chamador em `executar()`; a entrada segue fixture. Move a fronteira do sintético para a entrada da transcrição. O salto de produção é a LLM-transcrição (D-ARQ-25 Parte B) + o plug no orquestrador — fatias futuras.

**Achados novos (pendências).**
- **DT-003W-01**: typo de CAS do aluminato tricálcico — fixture/FISPQ traz `1242-78-3` (falha o dígito), CAS oficial é `12042-78-3` (valida). Fidelidade-ao-documento mantida: o gate o pega como inválido (ramo c, bloqueante, "empresa revisa") — comportamento CERTO sobre transcrição torta. Decisão de corrigir a fixture (se for typo da fixture, não da FISPQ) vs. manter (se a FISPQ original traz torto) é do Diovanni. Não bloqueia. `[ABERTA — verificar contra a FISPQ original Ciplan]`.
- **Lacuna de cobertura** (não-DT, higiene): falta teste `componente entra com is_carcinogeno_iarc=True → gate preserva True`. `test_gate_reversao_nao_sobrescreve_flag` cobre só False→False (gate não força True); o simétrico (gate não zera True que a transcrição trouxe) não tem caso. Não-bloqueante; candidato a sessão de higiene ou anexável quando a Parte 3 plena tocar a flag.

**Pendências inalteradas.** DH-003P-01 (imports `Materialidade`; a propagação de pendência do gate que `resolver_composicao` descarta liga aqui). DT-003M-01, DT-003M-02, DT-003T-01 (fonte-de-flag plena / vocabulário / sensibilizante — Parte 3). DT-FDS-01, DT-FDS-02. Demais do balde inalteradas. DH-003M-01 vigiada nesta gravação (newlines reais).

**Próxima sessão (003.X).** Candidatos: (i) PLUG de `resolver_composicao` no orquestrador — dar chamador ao motor irmão isolado (decidir ONDE no pipeline, antes de `executar`; começa a destravar produção); (ii) Parte 3 plena da fonte-de-flag (tri-estado + `is_sensibilizante`, cruza DT-003M-01/DT-003T-01); (iii) D-ARQ-25 Parte B (LLM-transcrição, salto de produção real). Recomendação do Arquiteto: (i) — continuação natural do arco, fecha o "isolado". Decisão do foco é do Diovanni na abertura. Gate de estado real obrigatório: reler `orquestrador.py` literal, reconfirmar 255 isolado por pytest, grep de quem chama `stage_2_riscos`/`executar`. Ler docs vivos inteiros; checkout main && pull antes de criar branch.

## Sessão 003.X — 18/06/2026 — IMPLEMENTAÇÃO (i₀): teste de integração da cadeia composição→Fase C

**Foco.** De-risking do arco de composição: provar, em teste, a cadeia `fds_t65 crua → resolver_composicao → stage_2 Fase C` que a nota 003.W afirmava mas nunca fora exercida junta. Zero produção, zero fixture tocada — só arquivo de teste novo.

**Gate de abertura.** main em `43e1836`, sincronizada. Baseline 255 isolado / 410 total RECONFIRMADO por pytest real. Docs vivos lidos inteiros (PROTOCOLO v24 + DECISOES v46). Literais relidos por `git show` antes do prompt (`orquestrador.py`, `riscos.py`, `composicao.py`, `resolvedor.py`, `tipos.py`, `fds_t65.py`, `test_resolvedor.py`, `agentes.yaml`, `protocolo.py`) + 4 dígitos verificadores confirmados por execução real (`141-78-6`/`7128-64-5`/`67-64-1`/`9003-22-9`=True; `134363-67-7`/`1242-78-3`=False).

**Cinco passadas adversariais (cada uma corrigiu a anterior — registradas).** (1ª) Phantom-wiring "plugar contra dado que só existe como fixture" — RETIRADO: `fds_t65` crua + Fase C + R-PKG-BZ já fecham composição→risco→conduta. (2ª) "(iii) é a única que destrava produção" — provava demais (barraria toda fatia isolada já mergeada); retirado. (3ª) Reordenação: falta um degrau ANTES de (i')/(iii) — o teste de integração da cadeia, que nunca rodou junta → (i₀). (4ª) Contra a fixture: TiO₂ é ramo-c (CAS errado falha dígito), NÃO ramo-b como eu dissera; acetato RESOLVE (slug no yaml) e é straddle-AUSENTE. (5ª) Contra o disco: a asserção "não existe `cas_invalido` em ctx.pendencias" do teste 5 era tautologia cega (a pendência nasce e morre em `resolver_composicao`, nunca chega ao stage) e continuaria verde em (i'), cegando o teste para a própria mudança — reescrita para FUSÃO de procedências. Gate de tipo de `proto.vocabulario.agentes` confirmado `dict[str, Any]` (índice não sai vazio); contagem cravada "261" trocada por "N reportado".

**Entrega.** Arquivo único `agente_medico/tests/test_integracao_composicao_fase_c.py`, 6 testes. Índice construído de `agentes.yaml` REAL via `construir_indice_cas` (primeira vez sobre vocabulário de produção). Asserções: (1) inversão CAS→slug ponta a ponta; (2) adesivo promove exatamente 3; (3) materialidade por componente (acetona/MEK MATERIAL, acetato AUSENTE); (4) acetato AUSENTE → pendência bloqueante D-ARQ-35; (5) degradação de procedência (TiO₂ ramo-c ≡ copolímero ramo-b na Fase C); (6) cimento promove 0, todas pendências D-ARQ-35 bloqueantes.

**Verificação.** `git show --stat`: 1 arquivo, 145 inserções, NENHUM arquivo de produção (os 2 erros de mypy reportados pelo Code eram import de `Risco` + narrow de `Optional[FDS]`, correção local no teste — verificado, não vazou). Suíte completa 410 passed (404 legado intocado + 6). mypy --strict limpo. `_PROTOCOLO_DIR` copiado verbatim de `test_integracao_viverde.py`. Número da sessão LIDO do HISTORICO (003.W→003.X), não calculado. Commit `f17db90`, merge `31c767b` (PR #87, "Create a merge commit").

**Honestidade de escopo.** (i₀) de-risca o encadeamento de FUNÇÕES (`resolver_composicao → stage_2`), NÃO o encadeamento no orquestrador (`executar()` não foi tocado — só testes o chamam). Não tira de produção; o salto segue sendo (i') plug + propagação de pendência, depois (iii) LLM-transcrição.

**Lacuna de cobertura declarada (não-bug, não-DT).** (i₀) não exercita o ramo-1/bypass do predicado de materialidade sobre a cadeia real: o único carcinógeno da fixture (TiO₂, `is_carcinogeno_iarc` no yaml) tem CAS inválido → cai em ramo c antes de chegar a `materialidade()`. Forçar exercitaria adulterando fixture compartilhada — recusado. Anexável quando um carcinógeno de CAS válido entrar no vocabulário.

**Pendências.** Backlog triado por urgência no handoff 003.Y: DT-FDS-01 no topo (incorreção clínica ativa, próxima frente após o arco). (i') fecha DH-003P-01 e muda a asserção do teste 5. Demais inalteradas. DH-003M-01 vigiada nesta gravação (newlines reais).

**Docs.** DECISOES → v47 (notas 003.X em D-ARQ-35/36). PROTOCOLO v24 intocado (nenhuma R-* tocada).

## Sessão 003.Y — 19/06/2026 — ARQUITETURA: forma da propagação da pendência do gate-CAS (D-ARQ-37)

**Foco.** Fechar a forma de DH-003P-01 — como a `Pendencia` que `resolver_composicao` descarta (003.W) chega ao `Resultado`. Só-ARQUITETURA por decisão do Diovanni; implementação é 003.Z.

**Gate de abertura.** main em `e31edd1`, sincronizada (`git status` limpo). Baseline 261 isolado / 410 total RECONFIRMADO por pytest real do Diovanni. Literais relidos por `git show`: `tipos.py`, `orquestrador.py`, `riscos.py`, `composicao.py`, `resolvedor.py`, `protocolo.py`, `pendencias_estruturais.py`, `test_integracao_viverde.py`, DECISOES inteiro. Divergência de ambiente reconciliada: briefing do Code vinha de container (branch `claude/stoic-bohr-d8nwbz`, deps ausentes, "403+7 skipped"); estado real da máquina do Diovanni venceu (main, 261/410 verde).

**Seis passadas adversariais (cada uma corrigiu a anterior).** (1ª) Inflei o leque com "plugar dentro de `executar`" — morto: regride D-ARQ-09/15. (2ª) Tratei a pendência do gate como redundante com a da Fase C — falso: a do gate distingue causa/destinatário (b=protocolo/não-bloq, c=empresa/bloq, d=empresa/não-bloq), a da Fase C achata tudo em empresa/bloq. (3ª) Propus "Stage 3 vira dono da boa-formação de CAS" — refutada pela ordem de estágios: Stage 2/Fase C roda ANTES do Stage 3, o componente já passou com `agente=None`; e a procedência c-vs-b só vive no `[1]` do gate antes do descarte, irreconstruível a jusante. (4ª) Localizei o achatamento na Fase C — corrigido: o achatamento c≡b nasce no descarte do `[1]` em `resolver_composicao`; a Fase C é só onde o sintoma aparece. (5ª) "wrapper sem propagação como fatia isolada segura" — refutado: gate (003.S) e predicado (003.J) isolados eram seguros por serem INERTES (sem chamador); um wrapper plugado em `executar` é consumidor ATIVO que regride sinalização no instante da chamada. (6ª) Ia gravar carimbo de `ghe_id` + destino `pendencias_globais` — incoerente: pendência com GHE vive em `MatrizGHE`, não no balde global. Resolvido (A): pendências do gate são globais, sem `ghe_id`; costura por `replace`, não mutação.

**Entrega.** D-ARQ-37 (forma α: `resolver_composicao -> tuple[PGR, list[Pendencia]]`, pendências globais sem `ghe_id`, wrapper `executar_com_composicao` costura por `dataclasses.replace`). Realocação ao Stage 3 e forma β rejeitadas com razão registrada. DECISOES → v48. PROTOCOLO v24 intocado (nenhuma R-* tocada). DH-003P-01 fechada no sentido declarado (procedência chega ao Resultado, não "Fase C para de achatar").

**DT-003Y-01 — achatamento residual da Fase C.** Mesmo com α, a Fase C continua emitindo `materialidade_ausente` para componente sem-slug (lê `agente=None`, não vê o `[1]` do gate); α adiciona a pendência precisa ao lado, não suprime a achatada → dupla pendência. Eliminar: Fase C consumir a pendência do gate em vez de re-derivar. Não-bloqueante; fatia/decisão própria.

**Honestidade de escopo.** Zero código. `resolver_composicao` segue isolado em disco; a troca de assinatura, o wrapper e a costura são 003.Z. O salto de produção continua sendo a LLM-transcrição (D-ARQ-25 Parte B), a jusante desta fatia.

**Docs.** DECISOES v47→v48 (D-ARQ-37 + linha de revisão). HISTORICO: este bloco + DT-003Y-01. PROTOCOLO intocado.

## Sessão 003.Z — 20/06/2026 — IMPLEMENTAÇÃO (D-ARQ-37 forma α: troca de assinatura + wrapper + costura)

**Foco.** Materializar a forma α selada na 003.Y (DECISOES v48). Três movimentos: assinatura-tupla de `resolver_composicao`, wrapper `executar_com_composicao`, `executar()` intocado. Spec fechada na decisão — implementação pura.

**Gate de abertura.** main em `e322ccf` (merge 003.Y), sincronizada, limpo. Baseline **261 isolado / 410 total RECONFIRMADO por pytest real** ANTES de tocar arquivo. Branch `feature/003z-impl-d-arq-37` de main limpa. Literais relidos por `git show`: `composicao.py`, `orquestrador.py`, `tipos.py`, `resolvedor.py` (corpo de `gate_cas` — retorno `tuple[Componente, Optional[Pendencia]]`), `test_integracao_composicao_fase_c.py`, `fds_t65.py`. `git grep` repo-inteiro mapeou os 3 call sites ativos (test_integracao:54,66; test_resolvedor:235) — zero em produção/legado.

**Duas passadas de verificação sobre o prompt cirúrgico (regra de fatia que toca assinatura compartilhada).** 1ª passada pegou: grep sub-escopado (`-- agente_medico/`) → ampliado p/ repo inteiro; STOP-AND-REPORT estreito ("003.W/003.X") → "qualquer teste, novo ou legado"; asserções de ramo fundadas em comentário → confronto contra `fds_t65.py` literal (TiO₂ `134363-67-7` ramo c, aluminato `1242-78-3` 2º ramo c, copolímero `9003-22-9` ramo b, segredo industrial cas="" ramo d — dígitos verificados à mão); contagem exata por ramo → presença `>=1` (fixture tem múltiplos por ramo). 2ª passada pegou: asserção universal-negativa `not base_vocab` (dependia de ter lido todos os stages) → diferencial `n_wrap == n_base + n_gate`; gate de ambiente ausente (Code roda em container com deps faltando) → exigência explícita de máquina real.

**Entrega.** `composicao.py`: assinatura-tupla, acúmulo do `[1]`, docstring atualizada. `orquestrador.py`: wrapper `executar_com_composicao` (imports `dataclasses`/`resolver_composicao`/`EntradaIndice` adicionados). 3 unpacks `pgr, _ = …`. `test_composicao_propaga_pendencias.py` novo (9 testes). `executar()` byte-idêntico. Commit `df3cad2`, merge `cba6048` (PR #90, "Create a merge commit"). Suíte 270 isolado / 419 total, 100% verde.

**Verificação de mypy (registro honesto).** O prompt cirúrgico cravou "mypy zero erro" — critério MAL-ESCRITO. O baseline já tinha 26 erros (DH-003P-01 / imports `Materialidade`, fora de escopo). O Code reportou "26 pré-existentes" corretamente; o confronto real (`df3cad2` vs `df3cad2~1`, filtro `: error:`) deu 26=26 → delta ZERO, zero regressão. Lição de método: enquanto DH-003P-01 estiver aberta, o aceite de mypy em prompt cirúrgico é "delta zero vs. baseline", NUNCA "zero absoluto". O "27" intermediário foi a linha-sumário `Found N errors` casando com filtro `"error"` largo; `: error:` filtra limpo.

**Pendências.** DH-003P-01: forma fechada em 003.Y, MATERIALIZADA EM CÓDIGO em 003.Z. DT-003Y-01 ABERTA (achatamento da Fase C: dupla pendência para componente sem-slug — `materialidade_ausente` da Fase C + pendência precisa do gate; eliminar é Fase C consumir a do gate em vez de re-derivar; fatia/decisão própria). DT-FDS-01 elevada como próxima frente (R-BIO-02 vs eixo Quadro 1/2 do Anexo I vigente da NR-07 — CONHECIMENTO, lado-médico). LLM-transcrição (D-ARQ-25 Parte B) segue sendo o salto de produção, a jusante.

**Honestidade de escopo.** `executar_com_composicao` nasce SEM chamador de produção (espelha 003.J/003.S): só os 9 testes o exercitam. Não tira de produção — a entrada segue fixture. O plug no Streamlit/produção e a LLM-transcrição são fatias futuras. A 003.Z fecha o arco de composição no nível de motor (a pendência do gate agora chega ao Resultado), não no nível de produção.

**Docs.** DECISOES v48→v49 (nota 003.Z em D-ARQ-37 + linha de versão). HISTORICO: este bloco. PROTOCOLO v24 intocado (nenhuma R-* tocada).

## Sessão 003.AA — 20/06/2026 — CONHECIMENTO (reabertura DT-FDS-01: R-BIO-02 → R-BIO-04)

**Foco.** Reabrir DT-FDS-01 (R-BIO-02 contradito pelo Anexo I vigente). CONHECIMENTO-só, sem código.

**Gate.** main em `ca865aa`, limpo. Baseline 270/419 herdada (não reconfirmada por pytest — sessão não toca motor). PROTOCOLO v24 lido inteiro. NR-07 vigente (567/2022) lida no texto oficial gov.br/MTE — Anexo I Quadros 1 e 2 INTEIROS (Quadro 2 não fora lido na 003.F), itens 7.5.12–7.5.19.6, Anexo V.

**Derivação.** Eixo = Quadro do Anexo I onde o indicador está listado (IBE/EE vs IBE/SC), não carcinogenicidade. Quadro 1 → só periódico (7.5.15 literal); Quadro 2 → cinco momentos (a contrario). Quadro 2 = cádmio/chumbo-inorg/anticolinesterásicos/flúor. Benzeno: regime duplo (TTMA Quadro 1 + hemograma via Anexo V/IN 02-1995). Manganês fora do eixo.

**Passada de verificação (adversarial).** Corrigiu 4 pontos antes do fecho: (1) Quadro-2-cinco-momentos é a contrario, não literal — status diferenciado; (2) contra-exemplo cádmio é ambíguo → trocado por tolueno/solventes, direção do erro invertida (super, não subdimensionamento); (3) R-BIO-02 pode não ter consumidor no motor — implementação é incógnita factual, não dada; (4) "output estável" de R-CLI-02/03 era confiança demais — semestral é conduta Carolini (7.5.8 = anual), borda Anexo-V → INTERPRETADO.

**Entrega (docs-only).** PROTOCOLO v24→v25: R-BIO-04 nova; R-BIO-02 DEPRECATED; R-CLI-02/03 relabel + changelog; DT-FDS-01 RESOLVIDA. DECISOES intocado. Sem código, sem alteração de teste.

**Versionamento.** R-BIO-04 nova ID (muda saída: solventes Quadro 1 → só periódico). R-CLI-02/03 mesma ID + changelog (saída estável).

**Pendências.** DT-FDS-01 RESOLVIDA. 003.AB: `git grep` de consumidor de R-BIO-02/`anexo_nr07` decide IMPLEMENTAÇÃO (consumidor emite errado → teste-tolueno falha-e-passa) vs. ARQUITETURA (sem roteador → roteador genérico vs. momentos por-pacote; criar sem consumidor = fiação fantasma). DT-FDS-02, DT-003M-01/02, DT-003T-01, DH-003M-01, DH-003P-01 seguem abertas, intocadas.

**Honestidade de escopo.** Formaliza o eixo no PROTOCOLO; NÃO altera o motor. O que o motor emite para biomonitoramento não foi verificado por `git grep` nesta sessão — conformidade motor↔R-BIO-04 é a 003.AB.

**Docs.** PROTOCOLO v25 (este). HISTORICO: este bloco. DECISOES intocado.

## Sessão 003.AB — 21/06/2026 — ARQUITETURA-leve (higiene de dado: campo `anexo_nr07`)

**Foco.** Decidir o destino do campo `anexo_nr07` órfão e de eixo-misturado, apontado no fim da 003.AA. ARQUITETURA-leve, sem código.

**Gate.** main em `a8dd343` (merge PR #92, 003.AA), confirmado por kickoff colado — git venceu, não recalculado. PROTOCOLO v25 e DECISOES v49 lidos inteiros nesta sessão (não só kickoff/handoff). pytest não reconfirmado: sessão não toca motor; baseline 270/419 herdada da 003.Z permanece. (Nota: briefing-sandbox reportou 0/0 por PyYAML ausente — não é regressão; se a sessão de R-BIO-04 rodar no mesmo sandbox, confirmar PyYAML antes de confiar em contagem.)

**Investigação.** `git grep anexo_nr07 '*.py'` (repo inteiro) + os dois greps de `agentes.yaml` que a 003.AA deixou pendentes. Achado: campo com **consumo de produção zero** (só 2 asserções de teste), **3 hidratações vivas** (Fases A/B/C de `riscos.py`; a 4ª ocorrência no arquivo é fallback `=None`), **eixo misturado NR-07 `"I"` / NR-15 `"11"`** sob nome que promete uma norma, `"I"` semanticamente vazio em silica/asbesto, e comentário-benzeno stale citando DT-FDS-01 (resolvida em 003.AA).

**Passadas de verificação (3 + 1 de erros nos textos).** (1) Derrubou os números cravados sem git no início ("5 hidratações" → 3 reais + 1 fallback; "sem consumidor" era premissa-de-handoff → virou fato por grep). (2) Refutou "D-ARQ-33 crava que `quadro_anexo_i` está errado" — D-ARQ-33 nomeia `tipo_ibe` no contexto da ficha-engenheiro; a conclusão (alvo = `tipo_ibe`) sobrevive por consistência de vocabulário, `[DERIVADO]`, não "crava". (3) A decisiva: trocou a natureza da entrega de "decisão a registrar (acoplar a R-BIO-04)" — que é não-decisão, pois R-BIO-04 força a substituição por construção — para "achado a preservar". A substituição `anexo_nr07 → tipo_ibe` é consequência mecânica de R-BIO-04; o valor da 003.AB é documentar a leitura semântica do campo (que o gate mecânico de R-BIO-04 não reproduz) para a sessão de R-BIO-04 herdar. (4) Passada de erros sobre os textos de fechamento corrigiu data inventada, lista de pendências fingindo exaustividade, versão DECISOES com formato sem precedente, e SHA futuro cravado.

**Entrega (docs-only).** PROTOCOLO v25→v26: DT-003AB-01 adicionada (seção 11) — campo `anexo_nr07` mapeado como eixo morto/misturado, insumo herdado por R-BIO-04. DECISOES v49→v50: linha de changelog 003.AB (sem D-ARQ novo — não é decisão de arquitetura, é achado). Sem código, sem alteração de teste, sem branch de código.

**Pendências.** DT-003AB-01 ABERTA (herdada por R-BIO-04). As DTs/DHs abertas herdadas da 003.AA seguem abertas e intocadas (DT-FDS-02, DT-003M-01/02, DT-003T-01, DH-003M-01, DH-003P-01), mais DT-003Y-01 (aberta em 003.Z) e DT-003L-01 — lista completa e canônica na seção 11 do PROTOCOLO; não reauditada exaustivamente nesta sessão. R-CLI-02/03 mantêm marca INTERPRETADO (borda Anexo-V) — sessão CONHECIMENTO própria.

**Honestidade de escopo.** NÃO substitui o campo, NÃO toca motor, NÃO implementa R-BIO-04. Documenta o estado real de `anexo_nr07` (consumo-zero verificado por git nesta sessão) para que a implementação de R-BIO-04 não regrepe a semântica do zero. A substituição em si é da sessão de R-BIO-04.

**Docs.** PROTOCOLO v26 (DT-003AB-01). HISTORICO: este bloco. DECISOES v50 (changelog 003.AB, sem alteração de conteúdo de D-ARQ).

## Sessão 003.AC — 21/06/2026 — ARQUITETURA (consumo de `tipo_ibe`: D-ARQ-38)

**Foco.** Abrir R-BIO-04 como ARQUITETURA. Decidir a forma do consumidor de `tipo_ibe` que DT-003AB-01 deixou como insumo herdado. Sem código.

**Gate.** main em `f808efa` (merge PR #93, 003.AB), confirmado por kickoff colado — git venceu. PROTOCOLO v26 e DECISOES v50 lidos inteiros nesta sessão. pytest não reconfirmado (sessão não toca motor; baseline 270/419 herdada da 003.Z, [INTERPRETADO] no gate de procedência).

**Gate de estado real (3 greps + 1 show, em disco).** (1) `git grep tipo_ibe`: campo NÃO existe em produção — só fixture `test_resolvedor.py:49-50` + docs. Migração é introduzir campo novo, não repopular. Achado: a fixture tagueia `benzeno: tipo_ibe SC` — errado por R-BIO-04 (benzeno via SPMA/TTMA = Quadro 1/EE); teste-verde-mentiroso latente, herdado pela CONHECIMENTO. (2) `git grep anexo_nr07 '*.py'`: reconfirmado blast radius — 3 hidratações vivas (riscos.py:25,98,143) + 1 fallback (riscos.py:36) + def (tipos.py:103) + 2 asserções semânticas (test_riscos_stage.py:66,85) + ~15 construções `=None` em 5 arquivos de teste (git venceu o handoff: ~15, não ~18). (3) `git grep emite '*.py'`: schema emite SLUG LITERAL FIXO (emissao.py:47,79), não biomarcador-do-agente. (4) `git show agentes.yaml`: mapa agente→biomarcador é ZERO-VOCABULÁRIO (nenhum campo biomarcador/ibmp em nenhum agente). etanol/MEK/HCl com anexo_nr07 "11" (NR-15 Anexo 11) — não mapeiam uniforme p/ tipo_ibe.

**Passadas adversariais (4).** (1) Derrubou "DT-003Y-01 é IMPLEMENTAÇÃO contida" (turno anterior do Arquiteto): carrega seam de dedup wrapper-vs-Fase-C, e o caminho é sintético (sem D-ARQ-25 Parte B) — rebaixada. (2) Confirmou R-BIO-04 ≠ IMPLEMENTAÇÃO direta: derivação tipo_ibe é três-vias (EE/SC/None), não duas — agente "11"/NR-15 sem IBE no Anexo I viraria EE por engano (superdimensionamento, D-ARQ-22). (3) Sobre o fork de mecanismo: refutou "Opção 2 família-YAML" (schema emite slug fixo, não biomarcador-por-agente) E refutou o fechamento prematuro do fork — o mapa biomarcador inexistente bloqueia QUALQUER forma de emissor de biomonitoramento; decidir mecanismo agora é arquitetar sobre dado fantasma. Encontrou R-CLI-02 como consumidor barato (emite exame_clinico slug-fixo, schema basta, torna tipo_ibe vivo já). (4) Sobre o texto de D-ARQ-38: corrigiu R-CLI-03 NÃO consome tipo_ibe (Mn por identidade de agente, via NR-15); R-CLI-02 precisa só de {EE,SC}-vs-None (não distingue EE/SC); R-CLI-02 esbarra no dedup convergente clínico anual (R-CLI-01) × semestral — seam ABERTO de D-ARQ-31 nota fatia 3 [INCERTO — confirmar R-CLI-01 é regra emitindo exame_clinico 12M].

**Entrega (docs-only).** D-ARQ-38 (DECISOES v50→v51): dois consumidores de tipo_ibe de prontidões distintas; campo-consumido-não-morto; emissor de biomonitoramento adiado por dependência do mapa biomarcador; ordem de fatias. Sem regra clínica (PROTOCOLO intocado, v26). Sem código.

**Pendências.** DT-003AB-01 segue ABERTA (herdada por R-BIO-04, agora com a topologia de consumo decidida). DT-003Y-01 ABERTA (dupla pendência Fase C, rebaixada nesta sessão a "atrás da transcrição-LLM"). Colisão de ID DH-003P-01 detectada na leitura (PROTOCOLO seção 11 = redirect de imports ABERTA; D-ARQ-37 fronteira diz "fechada" referindo-se à propagação — dois débitos sob um ID) — registrar conserto em sessão futura; não tocada aqui. Demais DTs/DHs abertas intocadas. Achados de procedência p/ a CONHECIMENTO seguinte: fixture benzeno SC errada; três "11" não-uniformes.

**Natureza do próximo passo.** CONHECIMENTO (derivar tipo_ibe três-vias + mapa agente→biomarcador contra texto MTE, uma sessão) antes de qualquer IMPL.

**Docs.** DECISOES v51 (D-ARQ-38). HISTORICO: este bloco. PROTOCOLO v26 inalterado.

## Sessão 003.AD — 21/06/2026 — CONHECIMENTO (derivação `tipo_ibe` três-vias + mapa agente→biomarcador: fatia (a) de D-ARQ-38)

**Foco.** Cláusula 4(a) de D-ARQ-38: derivar, contra o texto oficial do Anexo I (Portaria 567/2022, gov.br/MTE), (1) `tipo_ibe` três-vias {EE/SC/None} por agente de `agentes.yaml` e (2) o mapa agente→biomarcador. Os dois saem do mesmo Anexo I. Sem código.

**Gate.** main em `7bb59e6` (merge PR #94, 003.AC), confirmado por kickoff colado — git venceu, sem divergência. PROTOCOLO v26 e DECISOES v51 lidos inteiros nesta sessão. pytest não reconfirmado (CONHECIMENTO não toca motor; baseline 270/419 herdada da 003.Z, `[INTERPRETADO]`). `agentes.yaml` colado pelo Diovanni para a aplicação por-slug.

**Texto oficial.** PDF da Portaria 567/2022 obtido em gov.br/trabalho-e-emprego; Quadro 1 (IBE/EE, 41 substâncias) e Quadro 2 (IBE/SC, 4 entradas) do Anexo I lidos inteiros, com abreviaturas de momento de coleta. Quadro 2 bate exatamente com o que R-BIO-04 (003.AA) já listava.

**Entrega (docs-only).** Critério três-vias (SC⟺Quadro 2 / EE⟺Quadro 1 / None⟺ausente) — D-ARQ-38 aplicação 003.AD. Mapa agente→biomarcador (slug→indicador) — R-BIO-04 changelog 003.AD. Tabela `tipo_ibe` por slug (12 EE + 1 SC + resto None) — DT-003AB-01 nota de derivação. Nenhuma regra clínica criada/alterada (R-BIO-04 enriquecido, mesma ID).

**Achados.** (1) Procedência herdada confirmada: benzeno=EE (fixture `test_resolvedor.py:50` SC errada); MEK=EE; etanol/HCl=None (`[INCERTO]`→`[DERIVADO]`). (2) 9 dos 12 EE têm `cas:null` → tipo_ibe é dado gravado, não casado por CAS; CAS faltantes são tarefa paralela. (3) chumbo ambíguo (Q2/SC inorgânico vs Q1/EE tetraetila) → SC recomendado, decisão a gravar explícita. (4) is_ototoxico ⊥ tipo_ibe (cianeto/manganês ototóxicos + None; 12 ototóxicos = 9 EE + 1 SC + 2 None). (5) Cardinalidade heterogênea do mapa (chumbo 2-simultâneos Pb-S+ALA-U; benzeno/CO/tolueno/estireno N-alternativos; resto 1:1) confirma o data-bloqueio do emissor (fatia d). (6) Cobertura SC parcial: dos 4 SC do Quadro 2, só chumbo tem slug.

**Pendências.** DT-003AB-01 segue ABERTA (derivação anexada; migração de campo é fatia b). Comentário stale do benzeno no yaml a corrigir na fatia b (DT-FDS-01 já resolvida em 003.AA). Demais DTs/DHs intocadas.

**Natureza do próximo passo.** IMPLEMENTAÇÃO fatia (b) de D-ARQ-38: campo `tipo_ibe` (forma a decidir na abertura) + migração `anexo_nr07 → tipo_ibe` transcrevendo a tabela 003.AD; gate de tipo compartilhado (repo inteiro, per 003.I) + passada adversária extra no prompt (per 003.W).

**Docs.** DECISOES v52 (D-ARQ-38 aplicação 003.AD). PROTOCOLO v27 (R-BIO-04 changelog + DT-003AB-01 nota). HISTORICO: este bloco.

## Sessão 003.AE — 22/06/2026 — IMPLEMENTAÇÃO (D-ARQ-38 fatia b: migração `anexo_nr07 → tipo_ibe`)

**Foco.** Fatia (b) da cláusula 4 de D-ARQ-38: introduzir o campo `tipo_ibe` e migrar `anexo_nr07 → tipo_ibe`, transcrevendo a tabela derivada na 003.AD (DT-003AB-01). Migração de tipo compartilhado — gate de repo inteiro + passada adversária extra no prompt (per 003.I/003.W).

**Gate.** main em `2c15cf5` (merge PR #95, 003.AD), confirmado por kickoff colado — git venceu. PROTOCOLO v27 e DECISOES v52 lidos inteiros. Baseline REAL medida nesta sessão por pytest: **419/419 verde** (matou o 270/419 `[INTERPRETADO]` herdado da 003.Z — 419 é o total real motor novo + legado). Branch `impl/003ae-tipo-ibe` criada de main limpa, sem `.pyc modified`.

**Gate de tipo compartilhado (repo inteiro, per 003.I).** `git grep -c` + `git grep -n` de `anexo_nr07` no repo todo: consumo de produção zero confirmado em disco (únicos *reads* de `.anexo_nr07` são 2 asserções em `test_riscos_stage.py:66,85`; `resolvedor.py:82` é comentário). Blast radius mecânico: def em `tipos.py:103`, 3 hidratações + 1 fallback em `riscos.py`, 1 comentário em `resolvedor.py`, 46 ocorrências em `agentes.yaml` (44 chaves + comentário + bloco stale), 18 sítios de construção `Risco(... anexo_nr07=None)` em 4 arquivos de teste + 2 asserções. O ~18 do handoff bateu com o disco.

**Forma selada (decisão de abertura).** Enum `TipoIBE(Enum)` com `EE`/`SC` string-valor, espelhando o molde `Materialidade` lido em disco (`tipos.py`). `tipo_ibe: Optional[TipoIBE]` substitui `anexo_nr07: Optional[str]` **in-place na posição 5** (campo sem default, entre `quantificacao` e `is_ototoxico`). Three-way {EE/SC/None} = `Optional[TipoIBE]`; None fica no Optional, não vira membro. Escolha do enum sobre `Optional[str]`: torna o eixo explícito no type system, casa com mypy --strict e com o precedente Materialidade (003.J), mata stringly-typed.

**Passada adversária extra (per 003.W, 7 vetores antes de emitir).** Resolveu contra literais: (V1) loader sem allowlist — `meta.get("tipo_ibe")` funciona; (V2) benzeno NÃO tem ramo especial na Fase A — hidrata pelo caminho genérico; (V3) handoff item (5) STALE — `test_resolvedor.py:49` tem `"tipo_ibe":"SC"` em chave morta que `construir_indice_cas` ignora, NÃO é asserção sobre o campo → NÃO tocar (decisão: opção 1, fora do escopo; o refinamento 2 da DT-003AB-01 estava impreciso ao tratá-la como correção funcional); (V4) import exato — `TipoIBE` adicionado ao bloco `from ...tipos import (...)` já existente no teste; (V7) paliativo aceito — conversão string→enum coberta por teste só na Fase A; Fases B/C com cobertura-de-rename, não cobertura-de-conversão (3 conversões idênticas verbatim por instrução, diff cru é a rede).

**Entrega.** `tipos.py` (enum + campo in-place). `riscos.py` (3 conversões `TipoIBE(meta["tipo_ibe"]) if ... else None` + import). `agentes.yaml` (chave `anexo_nr07:`→`tipo_ibe:` por slug, valor re-derivado da tabela 003.AD: 12 EE + chumbo SC com comentário de proveniência Quadro 2 inorgânico + resto null; comentário stale benzeno reescrito). `resolvedor.py` (comentário). 5 arquivos de teste (rename kwarg + 2 asserções + teste novo de cobertura `test_hidrata_risco_com_tipo_ibe_ee` com agente `acetona` EE neutro). Commit `e778da8`, merge `78ba5ee` (PR #96, "Create a merge commit").

**Bug de redação pego por STOP-and-report.** O texto do comentário stale do benzeno que emiti dizia `# tipo_ibe e tem_lt = null aqui` — fóssil do eixo morto, contradizia o valor `tipo_ibe: EE` ao lado. Code aplicou literal, NÃO autocorrigiu, reportou. Corrigido por instrução formulada (não "ajeita aí"): comentário reescrito para `# benzeno: tipo_ibe=EE (NR-07 Anexo I, Quadro 1). O roteamento de biomonitoramento do benzeno dispara por identidade de agente (R-PKG-BZ), independente do tipo_ibe.` 420 intacto após a correção (comentário não muda teste).

**Honestidade de escopo.** `tipo_ibe` entra **sem consumidor de produção** — R-CLI-02 (fatia c) é separada, com seam de dedup convergente clínico anual×semestral aberto (D-ARQ-31 nota fatia 3). Correto por "o dado precede a regra" (D-ARQ-38 cl.2), espelha o predicado órfão da 003.J. A migração NÃO liga o campo à conduta; quem o lê é a fatia (c). Nome de função stale `test_hidrata_risco_explicito_com_anexo_nr07` mantido (rename cosmético sem efeito, fora do escopo de tipo) — anotado para higiene futura.

**Verificação.** Baseline 419 reconfirmada antes de tocar arquivo. Pós-fatia: **420/420** (419 + 1 cobertura). mypy --strict delta-zero vs. baseline (26 pré-existentes, DH-003P-01). Número da sessão LIDO do HISTORICO (003.AD→003.AE), não calculado.

**Pendências.** DT-003AB-01 RESOLVIDA (migração de campo feita; ver PROTOCOLO v28). **DT-003AE-01 nova** — resíduos não-migração: 9 CAS null dos EE + cobertura SC parcial (só chumbo dos 4 Quadro 2). Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DH-003M-01, DH-003P-01, DH-003A-01, demais do balde. R-CLI-02 (fatia c) e o emissor de biomonitoramento (fatia d, data-bloqueado) seguem na fila de D-ARQ-38.

**Docs.** DECISOES v53 (nota 003.AE em D-ARQ-38). PROTOCOLO v28 (DT-003AB-01 RESOLVIDA + DT-003AE-01). HISTORICO: este bloco.

## Sessão 003.AF — 22/06/2026 — ARQUITETURA (seam de dedup convergente; D-ARQ-39; pré-condição de D-ARQ-38 fatia c)

Foco. Resolver o seam de dedup convergente do Stage 8 (D-ARQ-31 fatia 3, recorte deixado
aberto) — pré-condição arquitetural da fatia (c) de D-ARQ-38 (R-CLI-02 consome tipo_ibe).
Sem código: decisão de arquitetura.

Gate. main em 6f87089 (merge PR #97, docs 003.AE) sobre 78ba5ee (código fatia b, PR #96),
confirmado por kickoff colado — git venceu. PROTOCOLO v28 e DECISOES v53 lidos inteiros.
420/420 verde, mypy --strict delta-zero (26 pré-existentes, DH-003P-01). Número da sessão
LIDO do HISTORICO (003.AE→003.AF), não calculado.

Gate de número (disparou e resolveu). O prompt cravou "D-ARQ-39" de memória; o gate do Code
achou que não havia bloco `## D-ARQ-38` (grep `^## D-ARQ-` = 37) e PAROU — exatamente o que
D-ARQ-26 desenha. Verificação dirigida (greps sem `^##`) revelou caso (a): D-ARQ-38 existe
CRU na linha ~1052, cabeçalho malformado, não bloco ausente. Número real CONFIRMADO 39 (38
presente, só torto). O gate fez seu trabalho: pegou estado afirmado-de-memória ("último+1")
contra disco — convergiram em 39 só após a higiene do cabeçalho.

Gate de estado real (greps/sed em disco). Três leituras decidiram a forma:
(1) consolidacao.py:20-70 — caminho de convergência tem chave norm=exame.exame (slug, nada
mais); UM eixo de conflito (periodicidade_meses + periodicidade_apos_15a, igualdade estrita
46-49 → raise ConflitoProtocolo); TRÊS mutações incondicionais (58-60: momentos |=, motivos
extend, pendencias_anexadas extend) que rodam sempre que a igualdade não dispara raise.
(2) tipos.py:157,160 — ExameEmitido tem os dois campos de periodicidade; suporta piso
component-wise sem mudança de tipo. (3) regras.yaml HEAD — R-CLI-* NÃO EXISTE (busca exata
e case-insensitive por "cli" → zero match). Nenhuma das duas regras clínicas foi materializada;
não há branch perdido — é trabalho não feito.

Decisão (D-ARQ-39). Periodicidade divergente no mesmo exame nunca foi contradição de
protocolo — é composição resolvível célula a célula (mais-frequente-cobre-menos-frequente).
Resolve por piso component-wise (min em periodicidade_meses e periodicidade_apos_15a,
None=+∞ nos DOIS campos), substituindo o raise ConflitoProtocolo do caminho de periodicidade
divergente do dedup. Geral, não clínico-específico — corrige semântica do estágio. As três
mutações incondicionais ficam intactas; único código novo são as duas atribuições de mínimo
(o caminho de convergência JÁ É único — não há branch a duplicar; só o gate de entrada muda
de igualdade-ou-raise para sempre-calcula-mínimo).

Passada adversária (gatilho "qual a melhor saída" + duas verificações). Resolveu contra
literais: (V-unificação) recomendei unificar merge+piso sem ter lido o branch de merge
contíguo — o sed 20-70 mostrou que o caminho já é único e as 3 mutações já são incondicionais,
logo "unificar" era inferência, o disco confirmou que não há o que unificar. (V-proveniência)
temi apagamento de regra_id na escolha de piso — fantasma: motivos.extend já é aditivo, piso
escolhe número, não vencedor de proveniência; regra_id vive em Motivo, nunca em campo
escolhido. (V-âncora) inverti vivo×iminente — corrigido: caso-âncora VIVO é sílica×fumos no
RX (24M×60M→24M/12M, diagnóstico Viverde); clínico (R-CLI-01×R-CLI-02) é iminente, sem código.
(V-None) confirmei None=+∞ nos dois campos com o caso sílica-sem-medição (apos_15a=12) × fumos
(apos_15a=None) → 24M base / 12M após 15a, encurtamento herdado da regra que o tinha.

Requisito de segurança preservado por construção. O piso-sem-teto de D-ARQ-31 (pendência
bloqueante anexada à linha nunca perdida quando há piso) fica garantido pela linha 60
(pendencias_anexadas.extend), que já roda incondicional no caminho de convergência — não é
cláusula de vigilância, é estrutura. Auditor auditar_invariante_piso_teto (003.E) cobre a
regressão.

Honestidade de redação (pego na passada de fechamento). Não afirmo "ConflitoProtocolo perde
o ÚNICO disparador" — só li o loop 20-70, não o arquivo inteiro. Afirmo o que o disco prova:
perde o disparador de periodicidade divergente DESTE loop. O tipo permanece como veículo de
captura por-GHE de D-ARQ-15 para outros call-sites, se houver.

Nota de implementação obrigatória registrada no D-ARQ. A fatia IMPL recompõe a forma dos
GHEs afetados: BLOQUEADA→PARCIAL onde o piso passa a emitir (sílica×fumos no RX) é mudança
esperada, não regressão — a regressão Viverde tri-estado dos 32 GHEs (003.E) DEVE ser
recomputada e reasserida.

Escopo honesto. Sem código. A fatia (c) de D-ARQ-38 é maior que o handoff supunha: na ordem
real é seam (esta sessão, 003.AF) → R-CLI-01 IMPL → R-CLI-02 IMPL (nenhuma das duas existe
em regras.yaml). A derivação dos momentos de R-CLI-02 (protocolo dá "semestral", não os
momentos) é micro-trabalho da fatia R-CLI-02. Nenhuma regra clínica criada ou alterada —
R-CLI-01/02, R-RX-01/02 intactas; D-ARQ-39 é contrato de motor.

Higiene de passagem (defeito de cabeçalho do D-ARQ-38). O gate de gravação pegou que o
bloco D-ARQ-38 (criado na 003.AC) foi gravado em texto CRU — cabeçalho sem `## `, campos
sem negrito, sem separador `---` (linha ~1052). O grep `^## D-ARQ-` contava 37, não 38.
Terceira instância da mesma classe (negrito-em-vez-de-## na 002.X–Z; `\r\n` literal em
DH-003M-01/003.K-L; agora `## ` ausente no D-ARQ-38). Conserto desta sessão: SÓ o prefixo
`## ` do cabeçalho (defeito FUNCIONAL — quebra o grep do /kickoff e do briefing, D-ARQ-26/30).
O negrito ausente dos campos internos do D-ARQ-38 é defeito COSMÉTICO, NÃO tocado nesta
sessão — paliativo sinalizado (registro narrativo aqui, sem ID formal nem bump de PROTOCOLO:
defeito de markdown do DECISOES não é pendência clínica). Resolve o sintoma funcional, não
a classe; a recomendação estrutural de DH-003M-01 (arquivo-por-sessão ou tirar o kickoff da
dependência de `^##`) sobe de prioridade com a 3ª recorrência — candidata a sessão META
futura (rever o mecanismo de gravação de docs do Code, que corrompe markdown reincidente).

Docs. DECISOES v54 (D-ARQ-39 novo; cabeçalho do D-ARQ-38 corrigido). PROTOCOLO inalterado
(sem regra clínica — fica v28). HISTORICO: este bloco.

## Sessão 003.AG — 22/06/2026 — META (inventário de estado de produção; gestão à vista; sem código)

**Foco.** Inventário de estado pedido pela diretoria ("onde estamos em números, quanto falta") — substitui a `[ESTIMATIVA]` verbal do arquiteto por foto medida de disco. Modo META: não toca motor nem protocolo. Produz três números (cobertura clínica, estado da extração, triagem de DTs) + decisão de sequenciamento informada.

**Gate.** main em `072e36d` (merge PR #98, docs 003.AF), sincronizado origin, confirmado por kickoff colado — git venceu. 420/420 verde e mypy `--strict` delta-zero herdados de 003.AF (META sem código, não revalidados nesta sessão — `[INTERPRETADO]`). PROTOCOLO v28 e DECISOES v54 confirmados em disco. Número da sessão LIDO do HISTORICO (003.AF→003.AG), não calculado.

**Número 1 — cobertura clínica.** Denominador travado por gate de disco: 42 IDs `R-*` únicos no PROTOCOLO (header = status, `comm -3` diff vazio). Fração usa 41 ativas (exclui `R-BIO-02` DEPRECATED, fora de alvo de materialização). Numerador = 17 IDs com footprint executável (`regras.yaml` ∪ `motor/*.py`). **17/41 ≈ 41%.** Convenção de contagem fixada: família `R-RX-01` (`-adm/-sem/-baixa/...`) = 1 ID com variantes. Por superfície: `regras.yaml` 11, `motor/*.py` 7, `tests/*` 9 (por-ID), `protocolo/*.py` 0. Cortes: 6 yaml-only sem teste (BIO-04, ECG-01, FDS-04, OP-01, RX-02, VIS-01 — dado-presente-não-testado, candidatas a backfill); 2 motor-only (FDS-03, GHE-03); 24 só-escritas (zero ocorrência em `agente_medico/`). **Caveat de instrumento:** string-grep mede rastreabilidade, não consumo runtime; em loader data-driven, regra em yaml é funcional sem string no motor — os 17 são piso, não teto.

**Número 2 — estado da extração (gargalo de produção).** Binário por capacidade: a porta de entrada NÃO existe, provado por ausência de disco. 18 módulos no motor, todos pós-estruturação; nenhum parser/OCR/transcrição de FDS bruta (D-ARQ-25 ausente, consistente com 003.L). Transcrição LLM da FDS (Parte B) = 0 código. Resolução canônica `name→slug` = 0 código (única `def` de normalização é `leo_resolver.py:37 _normaliza`, escopo LEO-texto, não vocabulário químico; toda menção a "slug" em produção é uso de campo, não função dedicada). **A produção não está travada por cobertura clínica — está travada por porta de entrada inexistente.**

**Número 3 — DTs triadas** contra critério "fecha 1 PGR e2e com matriz correta". Bloqueia produção: DT-003L-01 (mapa 6 formas → input D-ARQ-25), DT-003M-02 (vocabulário não cobre composição-FDS), DT-FDS-02 (unidade cutoff 5% — bloqueia correção, não rodar). Higiene/fechada/feature-scoped: DT-003M-01 (resolvida 003.P), DT-003T-01 (fechada por recorte), DT-003AE-01 (biomonitoramento deferido), DH-003P-01/DT-003Y-01 (resíduo sem-slug edge), DH-003M-01/DH-003A-01 (markdown). **Convergência:** DT-003L-01 e DT-003M-02 não são débitos independentes — são facetas do mesmo subsistema de ingestão ausente (D-ARQ-25 + `name→slug` + vocabulário composição-FDS). Confirma o headline do Número 2.

**Recomendação de sequenciamento (decisão da diretoria, não selada aqui).** Pivotar para extração (caminho B) em vez de continuar a frente clínica (A). Razão: o motor de consumo já é load-bearing e testado; a restrição que prende valor de produção é a ingestão ausente, e nenhuma cobertura clínica adicional a remove. A clínica pausa em ~41% num ponto limpo (D-ARQ-39 selou a camada de dedup na 003.AF). Risco de retrabalho de B considerado e descartado: saída da extração (input estruturado de agente/risco) é a montante e ortogonal à convergência `R-CLI-*` (dedup/periodicidade, a jusante); contrato de saída não depende de `R-CLI-*`. Bônus: clínica retomada depois valida `R-CLI-*` contra PGR real, não fixture. **A inversão A→B fica PENDENTE de ratificação da diretoria (22/06); se ratificada, vira D-ARQ próprio (ingestão-antes-de-clínica-restante) em sessão futura. Não selada nesta META.**

**Marcos de gestão à vista (critério de pronto).** Marco 1 — 1 PGR real e2e: roda de arquivos brutos (PGR + FDSs) até matriz GHE×exame sem estruturação manual, e Dra. Carolini valida a matriz de saída (gate de aceite clínico, a jusante, sobre output real). Insumos: D-ARQ-25, `name→slug` canônico, modelos de matriz de risco (contrato de saída), normas vigentes gov.br/MTE (derivação), DT-003M-02 fechada, DT-FDS-02 confirmada. Bloqueado pelo subsistema de ingestão. Marco 2 — motor-sombra Streamlit: saída do motor novo ao lado do legado (`agente_medico_ia.py`), diff visível, sem regressão no legado; sombra parcial (input à mão) alcançável hoje, sombra pleno (PGR bruto→matriz) depende do Marco 1. **Nota arquitetural:** a gestão à vista plena (PGR real no painel) também nasce com o Marco 1 — hoje o painel só pode mostrar métricas internas, não valor de produção. B destrava o próprio instrumento que a diretoria pediu.

**Decisão de processo — gestão à vista.** Criado `docs/PAINEL_ESTADO.md` como painel vivo (primeira tiragem = inventário 003.AG). Cadência de atualização cravada: por evento, nunca por calendário — (1) merge em main que move um dos três números, (2) todo fechamento de marco, (3) piso de 1× por sessão META. Merge que não move número não dispara re-tiragem. O HISTORICO acumula snapshots; o painel mostra o estado corrente. A re-tiragem é passo do ritual de fechamento já existente (custo marginal ~zero: mesmo gate de disco), não sessão própria.

**Achados-META (drift memória×disco — entregável da sessão).** (1) DT-003Y-02 NÃO existe em disco — não é typo de 002Y-02 (sessão diferente); o `02` da lista de handoff foi escrito de memória sem lastro. Drift de handoff pego pelo gate. (2) Denominador travado em 42 — o ±1 que apareceu na triagem inicial era erro de contagem manual do arquiteto, não defeito de disco; `comm -3` confirmou header = status. (3) DH-003M-01 ao vivo: `\r\n` literal apareceu na saída de grep DESTA coleta — defeito presente, não relato histórico. **4ª instância** da classe de corrupção de markdown na gravação de docs do Code → gatilho de META própria disparado (handoff: "META própria se houver 4ª"). Candidata a sessão META de higiene do mecanismo de gravação.

**Docs.** DECISOES v55 (linha de changelog: decisão de processo — `PAINEL_ESTADO.md` + cadência de gestão à vista; sem novo D-ARQ numerado — inversão de sequenciamento pendente de ratificação). PROTOCOLO inalterado (META não toca regra clínica — fica v28). HISTORICO: este bloco. Novo arquivo: `docs/PAINEL_ESTADO.md`.

**Pendências abertas (inalteradas, salvo onde notado).** DT-FDS-02, DT-003L-01, DT-003M-02, DT-003T-01 (fechada por recorte), DT-003AE-01, DT-003Y-01, DH-003M-01 (4ª recorrência — escalada), DH-003P-01, DH-003A-01. Removida da lista de rastreio: DT-003Y-02 (inexistente em disco — nunca foi criada). Frente clínica (`R-CLI-01`→`R-CLI-02`) em espera até a decisão de sequenciamento; pré-requisito de qualquer prompt: gate de `regras.yaml`/`predicados.py`/`exames.yaml`.

## Sessão 003.AH — 23/06/2026 — ARQUITETURA (slice map da extração; ratificação A→B; sem código)

**Foco.** Primeira sessão da frente de extração pós-ratificação A→B. Modo ARQUITETURA: não toca motor nem protocolo. Dois entregáveis re-recortados após leitura dos docs vivos (PROTOCOLO v28, DECISOES v55) + gate de disco.

**Gate.** main em `466e8eb` (merge PR #99, docs 003.AG), sincronizado origin, confirmado por kickoff + run independente do Code (420/420 verde reconfirmado em ambiente limpo; mypy `--strict` delta-zero, 26 pré-existentes DH-003P-01). Número da sessão LIDO do HISTORICO (003.AG→003.AH). Próximo D-ARQ disponível = D-ARQ-40 (último selado D-ARQ-39, 003.AF) — NÃO consumido nesta sessão.

**Recorte de entregável (divergência do handoff, declarada).** O handoff pedia (1) registrar A→B como D-ARQ próprio e (2) derivar o contrato de saída da extração. Após leitura dos docs: (1) recusado como D-ARQ — A→B é decisão de processo (sequenciamento de trabalho, não contrato de motor); mesmo tratamento da decisão de processo v55 e do carimbo `[META]` de D-ARQ-32. Vira linha de changelog (v56) + painel. (2) O contrato-alvo de saída JÁ está derivado em D-ARQ-25 Parte C + topologia em D-ARQ-33/36; o trabalho real não era re-derivar mas medir o gap contra disco. Reorientado para slice map medido. Diovanni ratificou ambos os recortes.

**Gate de disco (`git show HEAD` de 7 arquivos).** Confirmado: (a) `executar_com_composicao` (orquestrador.py:114) existe, chama `resolver_composicao`→`executar`→costura `pendencias_globais` por `replace` (forma α 003.Z completa), mas tem **zero chamador de produção** — só `test_composicao_propaga_pendencias.py`. `executar()` intocado. (b) Contrato de entrada da Fase C confirmado: `Componente` precisa de `agente`(Optional[str]), `concentracao`(Optional[FaixaConcentracao]), `is_carcinogeno_iarc`/`is_sensibilizante`(bool); `agente=None` → `materialidade_ausente` bloqueante. `agente` só é populado por `gate_cas`/`resolver_composicao` — Componente extraído sem passar a costura cai automaticamente em bloqueante. (c) **Índice CAS: 9 de 43 slugs com CAS não-nulo** (silica, asbesto, etanol, metil_etil_cetona, cloreto_de_hidrogenio, dioxido_de_titanio, acetona, acetato_de_etila, benzeno). 34 com `cas: null` — incluindo quase todo o eixo químico de risco já modelado (tolueno, xileno, estireno, n_hexano, chumbo, mercurio, arsenio, manganes, 9 dos 12 EE de tipo_ibe).

**Slice map da extração (medido, não estimado).** Sub-camada química FDS→composição→Risco: **encanamento determinístico 100% em disco e costurado, isolado de produção** (gate_cas 003.S/T, resolver_composicao 003.W, wrapper+propagação 003.Z, materialidade 003.J, 4ª fonte 003.P, R-PKG-BZ 003.Q). Gargalos de produção, três naturezas distintas em massa crescente: (i) dado — índice CAS raso (9/43 = 21% resolve); (ii) decisão — `name→slug` indeciso (D-ARQ-36 Parte 1); (iii) greenfield — parse-PGR (esqueleto GHE/cargo/risco-físico), 0 código, D-ARQ-25 ausente desde 003.L, maior massa restante. As 6 formas de declaração química do DT-003L-01 são input para (iii).

**Decisão de sequenciamento intra-extração.** Fatia 1 = **B (popular os 34 `cas: null`)**, não A (plugar a costura). Razão: A sobre o índice atual é encanamento que resolve 9/43 — ocioso sobre FDS real; A sobre índice populado é a porta de entrada funcionando. Ordem: encher o índice → plugar. B é sessão de DADO (003.AI), A é fatia seguinte. Recomendação do Arquiteto, ratificada por Diovanni.

**Recorte de B herdado pela 003.AI (fechado aqui).** B popula SÓ `cas` (mecânico, CAS Registry público, gate de procedência por agente D-ARQ-27). NÃO toca `is_sensibilizante` (cruza DT-003M-01 + DT-003T-01, decisão própria); `is_carcinogeno_iarc` já populado em todos. Cuidado factual: dos 34 sem CAS, slugs-categoria (`fumos_metalicos`, `poeira_nao_classificada`, `quimico_nao_especificado`) NÃO recebem CAS — corretos como null; a 003.AI separa "substância com CAS faltando" de "categoria sem CAS atômico" no gate de procedência, sob pena de cravar CAS fantasma que o gate-CAS downstream pegaria. DT-D3-02 já marca `fumos_metalicos` como categoria a decompor.

**Docs.** DECISOES v56 (linha de processo — ratificação A→B + slice map; sem novo D-ARQ). PROTOCOLO inalterado (fica v28). PAINEL_ESTADO re-tirado (tiragem 003.AH: sequenciamento + slice map medido). HISTORICO: este bloco.

**Pendências abertas (inalteradas).** DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003AE-01, DT-003Y-01, DH-003M-01 (4ª recorrência — escalada, não aberta), DH-003P-01, DH-003A-01. Frente clínica (`R-CLI-01`→`R-CLI-02`) pausada até a extração destravar PGR real; pré-requisito da fatia (c) de D-ARQ-38 = o seam de D-ARQ-39 (dedup convergente) + R-CLI-01 IMPL.

## Sessão 003.AI — 23/06/2026 — DADO (popular CAS faltantes em agentes.yaml; fatia 1 da extração, recorte B)

**Foco.** Fatia 1 da extração (recorte B de 003.AH): popular os `cas: null` de substâncias em `agentes.yaml`. Modo DADO/vocabulário — não toca motor, regra clínica, predicado nem tipos.py. Materialização sob D-ARQ-22 (procedência) + D-ARQ-27 (gate CAS por agente); sem D-ARQ novo.

**Gate.** main em `0deaa2f` (merge PR #101, impl 003.AI mergeado), 420/420 verde, mypy --strict delta-zero (26 pré-existentes DH-003P-01). Número da sessão LIDO do HISTORICO (003.AH→003.AI). agentes.yaml lido literal de disco (git show HEAD).

**Correção de número herdado (disco venceu handoff).** O handoff/003.AH media 34 `cas: null` / 9 de 43. Disco mediu **36 `cas: null` / 9 de 45** (off-by-2: a tríade acetona/acetato/benzeno deslocou o denominador pós-snapshot 003.AH). Disco venceu. grep -c "cas: null" = 36 confirmado antes de editar.

**Trabalho do gate (separação substância-vs-categoria, não pressuposto do handoff).** Dos 36 null: 13 substâncias (CAS atômico/definido) + 23 categorias (físico/ergonômico/acidente/biológico/agregado — null correto, não recebem CAS). Das 13 substâncias, 12 gravaram CAS; 1 bloqueada pelo gate.

**Bloqueio consciente pelo gate (D-ARQ-22).** propanediamina_tridecyloxy é substância, mas o comentário [A VALIDAR] em disco marca CAS não confirmado → permanece null, comentário intacto. CAS sem fonte não entra. 12 gravam, 1 bloqueado.

**12 CAS gravados [DERIVADO — CAS Registry], dígito verificador conferido antes de gravar:** tolueno 108-88-3; xileno 1330-20-7 (mistura de isômeros, âncora canônica); estireno 100-42-5; n_hexano 110-54-3; dissulfeto_de_carbono 75-15-0; tricloroetileno 79-01-6; monoxido_de_carbono 630-08-0; cianeto_de_hidrogenio 74-90-8; chumbo 7439-92-1 (Pb elementar, âncora canônica do slug — não há CAS de classe de composto inorgânico); mercurio 7439-97-6 (Hg elementar); arsenio 7440-38-2 (As elementar); manganes 7439-96-5 (Mn elementar). Os 4 metais usam CAS do elemento como âncora canônica do slug [DERIVADO — elemento como âncora canônica]; a Dra. Carolini pode fixar composto específico na revisão de saída.

**Estende DT-003AE-01.** Os 9 EE que a DT listava (arsenio, dissulfeto_de_carbono, estireno, mercurio, monoxido_de_carbono, n_hexano, tolueno, tricloroetileno, xileno) foram gravados, mais 3 (cianeto_de_hidrogenio, chumbo SC, manganes). DT-003AE-01 candidata a RESOLVIDA quanto aos CAS dos EE — confirmar contra doc vivo na próxima tiragem do painel.

**Verificação.** Diff 12 linhas - / 12 linhas + (12 `cas: null` → `cas: "..."`), blast radius 1 arquivo (git --no-pager diff). grep -c "cas: null" 36→24 (23 categorias + 1 bloqueado). 420/420 verde mantido; mypy --strict delta-zero. Commit 0d5f786, merge 0deaa2f (PR #101, "Create a merge commit"), staged só agentes.yaml (git add nominal, não git add .). [DERIVADO — saída real do git diff + pytest, 003.AI]

**Índice CAS pós-fatia: 21/45** (9 prévios + 12). Restam 24 null: 23 categorias (corretas) + propanediamina (bloqueada). O gargalo "índice CAS raso" de 003.AH está substancialmente fechado para o universo de substâncias modeladas.

**Pendências abertas (inalteradas, salvo onde notado).** DT-003AE-01 candidata a RESOLVIDA (CAS dos EE gravados) — confirmar na próxima tiragem. propanediamina_tridecyloxy CAS segue [A VALIDAR] (bloqueado pelo gate). DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DH-003M-01 (4ª recorrência), DH-003P-01, DH-003A-01. Fatia 2 da extração (plugar executar_com_composicao no pipeline de produção, sobre índice agora populado) = 003.AJ, vira ARQUITETURA+IMPL.

**Docs.** HISTORICO: este bloco. DECISOES inalterado (v56 — sem D-ARQ novo). PROTOCOLO inalterado (v28).
