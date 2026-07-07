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

## Sessão 003.AJ — 23/06/2026 — ARQUITETURA (ponto de entrada de produção do motor novo)

**Foco.** Decidir o ponto de entrada de produção que chama `executar_com_composicao` — recorte da fatia A da extração (003.AH ratificada A→B), separado em ARQUITETURA isolada porque o ponto de entrada é a decisão de design, não encanamento. IMPL de plugar fica para 003.AK. Modo ARQUITETURA puro confirmado por Diovanni após o gate. Número lido do HISTORICO (003.AI → 003.AJ, não calculado).

**Gate.** main em `13cb639` (merge PR #102, docs 003.AI), branch sincronizada com origin. Baseline herdada 420/420 verde, mypy --strict delta-zero (26 pré-existentes DH-003P-01). PROTOCOLO v28 + DECISOES v56 lidos inteiros, cruzados contra a coleta /kickoff — sem divergência git × docs. Untracked `fds_originais/` + `matrizes_originais/` (52 arq.) corretos como não rastreados.

**Achado de disco que reescreveu o foco (três greps, gate de estado real).** O handoff pedia "plugar `executar_com_composicao` no pipeline de produção". Os greps mostraram que não há pipeline de produção onde plugar:
- `executar()` sem chamador de produção; hits em `app.py` são `_executar_extracao` (flag session_state Streamlit), falso positivo.
- `executar_com_composicao` com chamador único: `test_composicao_propaga_pendencias.py`.
- Zero ponto de entrada do motor novo (`__main__`/argparse/main/click ausentes de produção em `agente_medico/`); único hit é `__main__` de teste manual em `test_integracao_viverde.py`. `app.py` é o legado Streamlit, aposentado por D-ARQ-25.
Logo a sessão não decide *onde* o wrapper encaixa — decide se o motor novo **ganha** ponto de entrada agora. `[DERIVADO — saída real dos três greps, 003.AJ]`.

**Decisão (D-ARQ-40, DECISOES v57).** Ponto de entrada = fachada fina `processar_pgr` em módulo greenfield `agente_medico/motor/entrada.py`, sobre o wrapper existente. Quatro cláusulas: (1) duas portas — wrapper intocado (índice explícito, testável, ponto de injeção da transcrição-LLM) + `processar_pgr` que esconde a construção do índice do chamador; (2) a decisão é o princípio "fachada esconde a mecânica do índice", NÃO a assinatura concreta (esta é exemplo provisório, condicionada ao disco da AK); (3) contrato de entrada `tipos.PGR` cru (D-ARQ-25 Parte A); `processar_pgr` é a tomada onde a transcrição-LLM (Parte B) injeta, assinatura estável a essa injeção; (4) rótulo cravado — harness de produção, não travessia de PGR real (entrada por fixture até Parte B existir; salto de produção real declarado a jusante). CLI = extensão futura condicionada a parse de PGR real. Greenfield — legado `app.py` intocado.

**Recorte da sessão (por que ARQUITETURA isolada, não ARQUITETURA+IMPL).** O handoff recomendava ARQUITETURA+IMPL. Empurrado para ARQUITETURA isolada porque o IMPL estava bloqueado por um dado de disco (qual o ponto de entrada hoje) que, medido, virou uma decisão de design própria (não há ponto de entrada — criar é arquitetura). Decidir a forma do ponto de entrada no meio de uma sessão com a mão no código arrisca escolher pela conveniência de plugar, não pela universalidade (D-ARQ-06). IMPL vira 003.AK com alvo estável.

**Passadas adversariais (2, sobre a síntese — toca caminho compartilhado, per 003.W).** 1ª: rebaixou "greenfield de entrada.py" e "origem do índice" de afirmações a condicionais de disco da AK. 2ª: corrigiu três "parece decidido" vencendo "está decidido" — (i) "duas portas" é recomendação do Arquiteto não-objetada, NÃO decisão validada do Diovanni (marcado `[INTERPRETADO]`, não `[VALIDADO]`); (ii) a assinatura concreta `(pgr, protocolo, hoje=None)` saiu do corpo da decisão para exemplo provisório — cravá-la seria literal sem fonte de disco (D-ARQ-22); (iii) o encaixe do arquivo `entrada.py` é questão de design da AK (existe `motor/__init__` re-exportando API?), não só de colisão de nome. Resultado: direção intacta, três contornos de forma corretamente amolecidos.

**Higiene confrontada (não fechada).** DT-003AE-01: o handoff sugeria candidata a RESOLVIDA quanto aos CAS dos EE (gravados na 003.AI). Não fechável contra o doc vivo em mãos (PROTOCOLO v28 = 003.AE, anterior à gravação dos CAS da 003.AI). A DT tem dois resíduos (9 CAS null + cobertura SC parcial do Quadro 2); o resíduo CAS está coberto pela 003.AI, o resíduo SC **não** foi tocado. DT segue ABERTA pelo resíduo SC. Confirmar texto exato contra PROTOCOLO pós-003.AI. Sem divergência com o handoff (que dizia "quanto aos CAS", não "RESOLVIDA").

**Procedência de "duas portas".** Item "uma vs. duas portas" colocado a Diovanni e não contestado; Diovanni cravou o nome (`processar_pgr`/`entrada.py`) e não objetou a estrutura de duas portas. Registrado como recomendação do Arquiteto não-objetada, não decisão validada — para o handoff futuro não afirmar procedência que não houve.

**Pendências abertas (inalteradas).** DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01 (resíduo SC), DH-003M-01 (4ª recorrência), DH-003P-01, DH-003A-01.

**Próxima (003.AK) = IMPL de D-ARQ-40.** Gate de estado real obrigatório: grep de `processar_pgr`/`entrada.py` (greenfield: colisão E encaixe); origem do `indice_cas` (deriva do `Protocolo`? — pode revisar a assinatura); forma da construção do índice. Passada adversarial extra sobre o prompt cirúrgico (orquestrador + ponto de entrada). Reconfirmar 420/420 antes de tocar arquivo.

**Docs.** HISTORICO: este bloco. DECISOES: D-ARQ-40 (v57). PROTOCOLO inalterado (v28 — nenhuma regra clínica tocada). PAINEL_ESTADO: re-tiragem adiada para a 003.AK (esta sessão não move código nem número de marco; o evento que move a extração é a AK plugando).


## Sessão 003.AK — 24/06/2026 — IMPLEMENTAÇÃO (ponto de entrada de produção: processar_pgr)

**Foco.** Materializar a fachada `processar_pgr` decidida em D-ARQ-40 (DECISOES v57) — IMPL da fatia A da extração. Número lido do HISTORICO (003.AJ → 003.AK, não calculado).

**Gate de abertura.** main em `13cb639` (merge PR #102, docs 003.AI), branch sincronizada com origin. Baseline 420/420 verde RECONFIRMADA por pytest real antes de tocar arquivo; mypy --strict delta-zero (26 pré-existentes, DH-003P-01). PROTOCOLO v28 + DECISOES v57 lidos inteiros. Branch gate disparou — Code parou em `main`, `feature/003ak-entrada-processar-pgr` criada com autorização. Untracked `fds_originais/` + `matrizes_originais/` corretos como não rastreados.

**Gate de estado real (5 verificações, todas confirmaram o que o prompt assumia).**
1. G1 — `git grep processar_pgr`: zero em código (13 hits = prosa em docs). Greenfield confirmado.
2. G2 (o gate que podia revisar a assinatura) — `construir_indice_cas(agentes_vocab: dict[str,Any])` em `resolvedor.py:36` recebe vocabulário; chamadores reais o alimentam de `Protocolo.vocabulario.agentes`. Índice DERIVÁVEL do `Protocolo` → assinatura `processar_pgr(pgr, protocolo, hoje=None) -> Resultado` se sustenta sem parâmetro extra. Cláusula 2 de D-ARQ-40 resolvida a favor da forma ilustrativa.
3. G3 — `entrada.py` inexistente; `motor/__init__.py` vazio (sem fachada parcial a respeitar).
4. G4 (CONTRADIÇÃO de invariante, registrada) — `git ls-files matrizes_originais/`: 14 arquivos JÁ RASTREADOS (commits antigos b59a714/18e6211/b48e0b6) + lote novo `??` não-rastreado; `fds_originais/` 100% não-rastreado. A invariante "matrizes/fds permanentemente não-rastreadas" é FALSA para `matrizes_originais/` (já catalogado em DT-003L-01). Trava cravada: `git add` NOMINAL por arquivo, nunca `git add .`.
5. G5 — 420/420 verde reconfirmado.

**Correção de rumo (G4).** Na abertura descartei (errado) o alarme do container sobre matrizes_originais/ como artefato de shallow clone; o `git ls-files` mostrou tracking real misto. Corrigido antes de qualquer staging.

**Implementação.** Commit `a378999c4a80086821198a2345306f7a7e366ea6`:
- `agente_medico/motor/entrada.py` (novo): `processar_pgr(pgr, protocolo, hoje=None) -> Resultado`, corpo = `executar_com_composicao(pgr, protocolo, construir_indice_cas(protocolo.vocabulario.agentes), hoje)`. Sem try/except (ValueError de colisão CAS propaga).
- `agente_medico/motor/__init__.py`: item B (re-export canônico) — `from .entrada import processar_pgr` + `__all__`. `[INTERPRETADO]` não-objetado.
- `agente_medico/tests/test_entrada_processar_pgr.py` (novo): 4 testes — fachada constrói o índice; equivalência ao wrapper por `status`+contagens (NÃO por `==` de `Resultado` mutável); repasse de `hoje`; import canônico.
- Wrapper, `executar()`, `resolver_composicao`, `gate_cas`, legado `app.py` INTOCADOS.

**Testes — desvio reportado (próprio do teste, não regressão).** 1ª versão de `test_processar_pgr_repassa_hoje` usou diferença de 1 dia esperando mudança de status; R-PGR-06 (`gates.py:33`) exige `(hoje - validade) >= 730 dias`. Corrigido para `date(2027,1,1)` → REJEITADO. Amarração ao limiar 730d registrada como DT-003AK-01 (dívida de teste, não-bloqueante).

**Verificação.** 420→424 verde (suíte completa). mypy --strict: 26 pré-existentes (DH-003P-01), delta-zero confirmado por diff vs. baseline; `entrada.py`/`__init__.py` limpos. `git diff` revisado — 3 arquivos. Commit `a378999c4a80086821198a2345306f7a7e366ea6`, merge `ee233b4` (PR #104, "Create a merge commit"), sem push direto. Branch de impl deletada pós-merge (local + remoto).

**Higiene confrontada (não fechada).** DH-003M-01: ao reler o PROTOCOLO inteiro, o `\r\n` literal tem ocorrência VIVA no changelog v20 da tabela de revisões do PROTOCOLO — não só no HISTORICO. Amplia a classe para o 2º doc vivo; a 4ª recorrência já era gatilho de META.

**Honestidade de escopo.** `processar_pgr` é harness de produção, NÃO travessia de PGR real — entrada por fixture, salto de produção segue em D-ARQ-25 Parte B (transcrição-LLM, zero código), a jusante. A fachada esconde a mecânica do índice do chamador; o wrapper retém o índice explícito como ponto de injeção da transcrição.

**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01 (resíduo SC), DT-003AK-01 (nova — dívida de teste, aprovada), DH-003M-01 (4ª recorrência, agora em 2 docs vivos), DH-003P-01, DH-003A-01.

**Próxima (003.AL).** Decisão do Diovanni no kickoff. Candidatas: (i) plugar `processar_pgr` em consumidor real/CLI — bloqueada por D-ARQ-25 Parte B (parse-PGR, zero código); (ii) sessão META de DH-003M-01 (gatilho disparado, 2 docs vivos); (iii) retomar a frente clínica pausada (R-CLI-01 → R-CLI-02, seam de dedup D-ARQ-39 selado). Gate de estado real obrigatório antes do prompt.

**Docs.** HISTORICO: este bloco. DECISOES: nota de aplicação 003.AK em D-ARQ-40 (v58). PROTOCOLO inalterado (v28 — nenhuma regra clínica tocada). PAINEL_ESTADO: re-tiragem na 003.AL (a AK não move número de marco — fachada sobre fixture, não travessia real).

## Sessão 003.AL — 25/06/2026 — ARQUITETURA (camada de extração: padrão bicamada e fronteira do parse-PGR — D-ARQ-41)

**Foco.** Decidir a forma de D-ARQ-25 Parte B (transcrição-LLM / camada de extração) — o gargalo de produção ratificado pela diretoria (inversão A→B, v56). Número lido do HISTORICO (003.AK → 003.AL, não calculado). Modo ARQUITETURA — sem código, sem gate de estado real de código (conceitual; o gate vale antes do prompt cirúrgico de implementação, fatia futura).

**Recorte.** D-ARQ-25 Parte B é guarda-chuva (nunca decidiu mecanismo de `name→slug`; parse-PGR greenfield). Uma sessão não fecha tudo. O que fecha honestamente: o **padrão da camada de extração** e a **fronteira do parse-PGR** — o nó que D-ARQ-36 empurrou ("resolvedor só resolve CAS→slug; `name→slug` em D-ARQ-25 Parte B"). Fora: prompt, forma do campo de sinônimos, as 6 formas de DT-003L-01, gates validade/assinatura.

**Decisão (D-ARQ-41).** Padrão bicamada: transcritor-LLM (estrutura o documento heterogêneo, termos crus) + resolvedor determinístico (`termo→slug`, gate de pendência D-ARQ-14). Fronteira LLM↔determinístico = contrato transcrito tipado (a "PGR transcrita": `GHEPGR`-shaped, termos em linguagem natural, FDS apontadas — NÃO `tipos.PGR`, que sai do resolvedor). Generaliza D-ARQ-36 (instância-FDS) ao padrão de toda extração. Recusa monocamada (LLM cospe slug em silêncio → erro silencioso plausível, D-ARQ-22).

**Adiado por medição (declarado, não chutado).** O mecanismo fino do `name→slug` e a granularidade da fronteira (quanto o LLM normaliza antes de entregar) ficam abertos — três saídas candidatas (a) verbatim+normalização-agressiva+sinônimos / (b) LLM normaliza p/ conceito / (c) híbrido com candidato-LLM de baixa confiança. CAS é token rígido (índice exato funciona); termo de risco é texto fluido (casamento exato → falso `vocabulario_ausente`). Escolha sai de medir sobre os PGRs de DT-003L-01. Molde de adiamento-por-dado de D-ARQ-38 (emissor de biomonitoramento esperou o mapa).

**Três passadas adversariais.** (1ª) bicamada simétrica a D-ARQ-36. (2ª) achou a assimetria de peso: o resolvedor do PGR é quase-vazio (`dict.get`), a peça nova é o **contrato transcrito**, não a topologia — tratar topologia como a decisão enterraria a peça. (3ª) corrigiu honestidade de escopo: `name→slug` tem mecanismo adiado por medição (não "fechado", como uma redação anterior vendia); e a metade quase-pronta da extração é a **FDS** (resolvedor `gate_cas`/`resolver_composicao` já existe e costurado, 003.S/T/W/Z), não a PGR — relevante para a ordem da próxima implementação.

**Honestidade de escopo.** D-ARQ-41 fecha topologia + fronteira + princípio do gate de slug. NÃO fecha: ordem de implementação parse-PGR vs. transcrição-FDS; mecanismo do `name→slug`; prompt; forma do campo de sinônimos; as 6 formas de DT-003L-01.

**Pendências abertas:** DT-FDS-02, DT-003L-01 (insumo direto de D-ARQ-41), DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01 (resíduo SC), DT-003AK-01, DH-003M-01 (4ª recorrência, 2 docs vivos), DH-003P-01, DH-003A-01.

**Próxima (003.AM).** Decisão do Diovanni no kickoff. Candidatas: (i) transcrição-FDS — IMPL do transcritor-LLM (resolvedor pronto, menor caminho até dado real no motor); (ii) parse-PGR fatia 1 (greenfield; exige CONHECIMENTO/medição da granularidade antes da forma da "PGR transcrita"); (iii) frente clínica R-CLI-01 → R-CLI-02 (desbloqueada, seam D-ARQ-39; conduta nova end-to-end; Marco 1). Gate de estado real obrigatório antes do prompt.

**Docs.** HISTORICO: este bloco. DECISOES: D-ARQ-41 + changelog v59. PROTOCOLO inalterado (v28 — nenhuma regra clínica tocada). PAINEL_ESTADO: não re-tirado (AL não move número de marco nem fecha marco; cadência por-evento v55 não dispara) — opcional registrar "extração saiu de 0-forma para padrão+fronteira decididos" se o Diovanni quiser visibilidade.

## Sessão 003.AM — 25/06/2026 — ARQUITETURA (transcritor-FDS: padrão, contrato e recorte — D-ARQ-42)

**Foco.** Decidir o padrão e o contrato da camada de transcrição-FDS (a metade quase-pronta da extração: resolvedor FDS já existe e costurado, falta o transcritor a montante do "CAS transcrito"). Modo ARQUITETURA. Número lido do HISTORICO (003.AL → 003.AM, não calculado).

**Gate de estado real (mesmo em ARQUITETURA — decisão sobre fronteira de código existente).** main em `493114c` (merge PR #106). Quatro literais/greps em disco: (1) `tipos.py` — `Componente` cru é o contrato de saída do transcritor, sem tipo intermediário; (2) `composicao.py` — `resolver_composicao` consome `tuple[Componente,...]` de `produto.fds.composicao`, roda `gate_cas` por componente; (3) grep `pdfplumber|pypdf|fitz|ia_client|extrair.*gemini` em `agente_medico/`+`scripts/` → zero hits (transcritor greenfield); (4) `fds_t65.py` — fixture é o output-esperado transcrito à mão de 3 FDS reais, NÃO a entrada. PDFs-fonte confirmados em `fds_originais/` (Ciplan / Adesivo Tigre / Tinta Acrílica). Suíte 424/424 herdada da 003.AK (não reconfirmada — ARQUITETURA, sem toque em código).

**Decisão (D-ARQ-42).** Transcritor-FDS = camada-LLM da instância-FDS de D-ARQ-41. (1) Bicamada interna: parse-PDF determinístico → transcrição-LLM, fronteira interna = "texto extraído". (2) Contrato de saída `tuple[Componente,...]` cravado em disco — transcritor não inventa tipo, não resolve slug, não corrige CAS, não classifica perigo. (3) Recorte (A): transcreve identidade+concentração; flags de perigo no default-por-ausência **com autor declarado** (não "perigo fora" — D-ARQ-22). (4) Gabarito por-campo: `cas`/`concentracao` ancoram deterministicamente; `nome` é texto-livre-de-LLM, não `==`. Mecanismo fino + fronteira-OCR + critério-de-`nome` adiados por medição (003.AN).

**Três passadas adversariais sobre a síntese (cada uma corrigiu a anterior).** (1ª) "(A) não toca o tipo" — corrigido: (A) grava `is_*=False` por ausência, mas com autor novo (o transcritor); `False` tipado ≡ "classificado não-perigoso" é o erro silencioso plausível de D-ARQ-22; mesma defesa de DT-003T-01 (default-por-ausência declarado). (2ª) "gabarito = saída == fixture" — refutado: a fixture carrega anotação humana (o "CAS correto" do TiO₂ que o transcritor não conhece) e `nome` é texto-livre-de-LLM (grafias divergentes do mesmo PDF) → gabarito é por-campo, `nome` precisa critério próprio. (3ª) "fatia 1 de IMPL" — refutado: a forma do transcritor depende de medir os 3 PDFs (texto-vs-scan, ruído OCR, regularidade das 3 notações); cravar antes de medir é o erro que D-ARQ-41 evitou para o PGR → mecanismo adiado para CONHECIMENTO (003.AN).

**Fronteira-OCR (achado da medição-de-segunda-mão).** Triagem-LLM dos 3 PDFs (Perplexity/GPT, print colado): os 3 têm camada de texto; `01-Ciplan` é escaneado-com-OCR com ruído explícito ("Start of OCR for page 1"), Adesivo Tigre e Tinta Acrílica são texto nativo. Tratado como **pista, não fato** (D-ARQ-30, aponta-não-afirma); confirmar por extração determinística na 003.AN. Consequência: o parse-PDF entrega texto sujo para 1 de 3 casos do gabarito — nomeia a fronteira-OCR (LLM absorve vs. limpeza determinística), aberta, resolvida pela medição. Sem o print, eu teria cravado "transcritor recebe texto limpo" — errado para 1/3 no dia 1.

**Recorte da sessão.** Recorte 1 (escolhido pelo Diovanni): fecha padrão+contrato+recorte(A)+princípio-de-gabarito; adia mecanismo/OCR/`nome` para medição. Recorte 2 (medir os 3 PDFs nesta sessão) inviável — os bytes estão na máquina do Diovanni, não no ambiente do Arquiteto; medição vira 003.AN.

**Entrega.** D-ARQ-42 + changelog v60. PROTOCOLO v28 intocado (nenhuma R-* tocada). HISTORICO: este bloco. PAINEL_ESTADO: não re-tirado (AM não move número de marco nem fecha marco; cadência por-evento v55 não dispara) — opcional registrar "transcrição-FDS saiu de 0-forma para padrão+contrato decididos" se o Diovanni quiser visibilidade.

**Honestidade de escopo.** Zero código. A transcrição-FDS ganha sua decisão de fronteira, não sua implementação. O salto de produção real (PDF → `Componente[]` no motor) segue a jusante: medição (003.AN) → IMPL do transcritor → plug. NÃO tira de produção.

**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (referenciada por D-ARQ-42 Parte 3, sem mudança de status), DT-003M-02, DT-003T-01 (idem), DT-003Y-01, DT-003AE-01 (resíduo SC), DT-003AK-01, DH-003M-01 (4ª recorrência, 2 docs vivos), DH-003P-01, DH-003A-01.

**Próxima (003.AN).** Decisão do Diovanni no kickoff. Candidata forte: CONHECIMENTO/medição dos 3 PDFs de `fds_originais/` (destrava o mecanismo do transcritor adiado por D-ARQ-42) — pré-requisito da IMPL do transcritor. Alternativas vivas: frente clínica R-CLI-01 → R-CLI-02 (Marco 1, desbloqueada seam D-ARQ-39); parse-PGR (greenfield, exige medição de DT-003L-01 antes). Gate de estado real obrigatório; reconfirmar 424 por pytest antes de tocar código.

## Sessão 003.AN — 26/06/2026 — CONHECIMENTO/medição (6 PDFs de FDS — fecha fronteira-OCR e critério-nome do transcritor — D-ARQ-43)

**Foco.** Medir os PDFs reais de `fds_originais/` por extração determinística (pdfplumber) para destravar os pontos que D-ARQ-42 adiou "por medição": fronteira-OCR, critério de `nome`, regularidade da seção 3.

**Gate de estado real.** main em `8952f16` (= `409b093`, D-ARQ-42/v60), tree limpa (untracked: `fds_originais/`, `matrizes_originais/*`, `medir_fds.py`). Suíte 424/424 herdada da 003.AK — não reconfirmada (CONHECIMENTO/medição, sem toque em motor). mypy não rodado (idem).

**O que a medição entregou.**
- **6 PDFs em `fds_originais/`, não 3** — corrige a Base de D-ARQ-42 (inspeção da 003.AM escopou aos 3 do fixture). 3 do gabarito `fds_t65` (Ciplan, Adesivo Tigre, Tinta Acrílica) + 3 de acervo sem par (Amanco solução limpadora, Leinertex textura, Massa-Corrida).
- **Nenhum é escaneado.** Triagem-LLM da 003.AM (Ciplan OCR) REFUTADA por medição: Ciplan é nativo (3340/3202 chars, tabela limpa, zero marcador OCR). Os 6 têm camada de texto (geradores: Ghostscript, Word, PDFCreator). → fronteira-OCR fechada (sem OCR; D-ARQ-43 Parte 1).
- **Casamento dos 3 do fixture confirmado** abrindo cada tabela: Ciplan 8 componentes; Tigre acetona/MEK/copolímero/acetato + 2 Segredos; Tinta com TiO₂ de CAS errado `134363-67-7` **na fonte** (parte `134363-67-\n7`) — prova que o erro está no documento, não na transcrição à mão (ramo c do gate por construção).
- **3 patologias da seção 3 catalogadas** (D-ARQ-43 Parte 3): P1 CAS plural "Derivados de:" (→ DT-003AN-01); P2 faixa invertida-P2a + piso-textual-00-P2b (→ normalização min/max no resolvedor); P3 CAS oculto 3 sabores (→ ramo d do gate; DT-003M-01 viva, H334+H317 no Segredo Industrial 2 do Tigre).

**Entregas.** D-ARQ-43 (DECISOES v61); DT-003AN-01 (PROTOCOLO seção 11, v29); este bloco (HISTORICO). Nenhuma regra clínica criada/alterada. Sem código. `medir_fds.py` descartável, não commitado.

**Próxima (003.AO).** DH-003M-01 estrutural (`.gitattributes *.md text eol=lf`) — META cravada. Gatilho de troca: se a gravação do bloco 003.AN reincidir CRLF, 003.AO já era. Caso contrário, AO segue por agenda. Alternativas vivas: IMPL do transcritor-FDS (fatia 1, com catálogo P1–P3); frente clínica R-CLI-01→R-CLI-02 (seam D-ARQ-39 selado).

## Sessão 003.AO — 26/06/2026 — META/higiene (`.gitattributes` blinda terminador de markdown — D-ARQ-44, DH-003AO-01)

**Foco.** Fechar a fragilidade de terminador CRLF dos `.md` medida na 003.AN (gravação 100% CRLF no working tree, salva como LF só porque `core.autocrlf` renormalizou). Doc-only.

**Gate de estado real.** main em `5676cf9` (#108 = `8604a1f`, D-ARQ-43/v61). Tree sem modified (untracked: `fds_originais/`, `matrizes_originais/*`, `medir_fds.py` — corretos). 424/424 herdada, NÃO reconfirmada (META, não toca motor). mypy idem. `.gitattributes` AUSENTE (Test-Path). Último D-ARQ=43, último changelog PROTOCOLO=v29 — lidos do disco.

**Entrega.** `.gitattributes` `*.md text eol=lf`, cobrindo `docs/`, `agente_medico/`, `.claude/skills/kickoff/` [DERIVADO — `git ls-files '*.md'`]. D-ARQ-44 (DECISOES v62). DH-003AO-01 adicionada e RESOLVIDA (PROTOCOLO seção 11, v30). Este bloco.

**Correção de rótulo (gate-before-label).** O handoff tratava a fragilidade como "5ª reincidência de DH-003M-01"; refutado contra disco (PROTOCOLO, entrada DH-003M-01). DH-003M-01 é `\r\n` literal como conteúdo (quebra `grep "^## Sess"`); o medido na 003.AN é o terminador `0x0D 0x0A` autocrlf-dependente. Defeitos distintos. DH nova aberta+fechada; DH-003M-01 permanece ABERTA, intocada.

**Escopo cirúrgico.** `*.md`, não `*` global — evita reescrita de `.py`/fixtures num repo de 424 testes. O `.py`/cp1252 fica para uma META futura. Renormalização retroativa (`--renormalize`) não executada.

**Próxima (003.AP).** IMPL transcritor-FDS P2 (normalização min/max no resolvedor — fatia mais limpa, destravada, alinhada à prioridade A→B ratificada) ou frente clínica R-CLI-01→R-CLI-02 (move Marco 1). Decisão no kickoff.

## Sessão 003.AP — 27/06/2026 — IMPLEMENTAÇÃO (P2: normalização min/max de faixa no resolvedor — D-ARQ-43)

**Foco.** Materializar a patologia P2 do catálogo da 003.AN (D-ARQ-43 Parte 3): normalização de ordem da faixa de concentração no resolvedor de composição. Fatia mais limpa do transcritor-FDS (testável sem LLM), alinhada à inversão A→B ratificada (v56). IMPLEMENTAÇÃO.

**Gate de estado real.** main em `dc2b7bd` (#109 = `25df935`, D-ARQ-44/v62, DH-003AO-01). Tree limpa (untracked: `fds_originais/`, `matrizes_originais/*`, `medir_fds.py` — corretos). **Suíte 424/424 reconfirmada por pytest real** antes de tocar arquivo (161s) — primeira reconfirmação desde a 003.AK (003.AN/003.AO foram doc-only). Leitura literal de `composicao.py` + `tipos.py` via `Get-Content -Encoding UTF8`; `git grep` de `FaixaConcentracao`/`piso_efetivo`/`teto_efetivo` no repo inteiro (tipo compartilhado, per 003.I). Passada adversária sobre a forma e o prompt contra os literais (per 003.W) antes de emitir.

**Decisão de forma (gate de disco).** Normalização mora no resolvedor (`composicao.py`), não no tipo: botá-la no `__post_init__` de `FaixaConcentracao` reverteria a decisão da 003.I (tipo sem `__post_init__`) e tornaria `min>max` inalcançável, apagando o trilho de integridade do Stage 3 (D-ARQ-17) em silêncio. Helper aplicado **antes** do `gate_cas` (faixa canônica é pré-condição do que o downstream lê; ortogonal ao ramo do CAS; mantém `resolvedor.py` intocado, blast radius menor).

**Entrega.** `_normalizar_faixa` em `composicao.py` (guarda dupla de `None`; `min/max` sem ramo condicional cobre P2a invertida e P2b piso-textual; idempotente; frozen via `replace`). `test_normalizacao_faixa.py` (8 testes). `tipos.py` INTOCADO. Blast radius: 2 arquivos. D-ARQ-43 nota de aplicação 003.AP (DECISOES v63). Este bloco. PROTOCOLO intocado (P2 não cria/altera R-\*; contrato de resolvedor). Commit `534f239`, merge `ec60c60` (PR #110, "Create a merge commit"). Suíte 424→432; mypy --strict limpo em `composicao.py`.

**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (viva — H334+H317 no Segredo Industrial 2 do Tigre, CAS oculto → ramo d), DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AN-01 (granularidade P1 "Derivados de:" multi-CAS, cruza D-ARQ-35), DH-003M-01 (segue ABERTA — `\r\n` literal-conteúdo; terreno `.py`/cp1252), DH-003P-01, DH-003A-01.

**Próxima (003.AQ).** Decisão do Diovanni no kickoff. Candidatas vivas: IMPL transcritor-FDS — próxima fatia (P1 "Derivados de:" multi-CAS exige decidir DT-003AN-01 explode-vs-agrega antes, cruza D-ARQ-35; ou a camada de transcrição-LLM propriamente, D-ARQ-25 Parte B / D-ARQ-42, maior salto); frente clínica R-CLI-01→R-CLI-02 (move Marco 1, seam D-ARQ-39 selado, rema contra A→B ratificada); parse-PGR greenfield (D-ARQ-25, exige ARQUITETURA). Gate de estado real obrigatório; reconfirmar suíte por pytest antes de tocar código.

## Sessão 003.AQ — 27/06/2026 — ARQUITETURA (P1: explosão de bloco "Derivados de:" multi-CAS no resolvedor — D-ARQ-45)
**Foco.** Fechar o fork explode-vs-agrega de DT-003AN-01 (patologia P1 do catálogo da 003.AN — D-ARQ-43 Parte 3): blocos "Derivados de:" que agrupam 2–3 sub-componentes com CAS empilhados numa célula na seção 3 das FDS. ARQUITETURA, sem código.
**Gate de estado real.** main em `3dc350b` (#111 = `7cba69e`, docs 003.AP / D-ARQ-43 P2 / DECISOES v63 / PROTOCOLO v30). Tree limpa (untracked: `fds_originais/`, `matrizes_originais/*`, `medir_fds.py` — corretos). Suíte de referência 432 (003.AP); não reconfirmada por pytest — sessão sem código. Leitura literal de `composicao.py`/`tipos.py` e dos consumidores da Fase C (D-ARQ-35 / 003.P-Q) para aferir decidibilidade. Decidibilidade confirmada sem o transcritor (greenfield): o consumidor médico que governa a granularidade já está construído e estável.
**Decisão (arco P1, duas partes) — D-ARQ-45.** (1) A explosão 1→N mora no resolvedor (`composicao.py`), a montante do `gate_cas`, downstream do transcritor verbatim — `Componente.cas: str` é singular (CAS-plural é mal-formado por construção, não sobrevive ao gate) e partir o separador é normalização determinística (lado determinístico, não LLM — D-ARQ-09/41); testável sinteticamente já, como a P2. (2) Cada sub-`Componente` herda a faixa inteira do bloco (α) — fiel ao documento, sobre-materializa na direção segura (anti-supressão D-ARQ-31/33 cl.5/35 P3), reusa `FaixaConcentracao`/`piso_efetivo`/`teto_efetivo` (003.I) sem mecanismo novo; β (repartir → inventa número, D-ARQ-22) e γ (AUSENTE → sub-supressão) rejeitadas. Dois limites declarados: (a) a sobre-materialização de α não é marcável no tipo (herdada ≡ medida) → risco residual "erro silencioso plausível", mitigado pela revisão de saída (D-ARQ-22); marcador de proveniência de concentração-herdada adiado por falta de consumo vivo (lógica de DT-003T-01 / D-ARQ-36-003.V); (b) a forma do trânsito CAS-plural transcritor→resolvedor é decisão de IMPL (gêmeo da forma de `FaixaConcentracao` da P2). Duas passadas adversariais: a 1ª quebrou o paralelo com a P2 por cardinalidade (1→N ≠ endomorfismo 1→1), forçando o argumento do contrato `cas: str` singular; a 2ª eliminou β e γ por princípios selados e adiou o marcador.
**Entrega.** D-ARQ-45 (DECISOES v64). DT-003AN-01 FECHADA (fork resolvido a favor de explode). PROTOCOLO v31 — só status de DT-003AN-01 → RESOLVIDA, com a nota da distinção empilhado-numa-célula vs. linhas-de-tabela-separadas herdada pela IMPL do transcritor-FDS; nenhuma R-* tocada (P1 não cria/altera conduta — cria contrato de resolvedor). Este bloco. Sem código.
**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (viva — H334+H317 no Segredo Industrial 2 do Tigre, CAS oculto → ramo d), DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DH-003M-01 (segue ABERTA), DH-003P-01, DH-003A-01. DT-003AN-01 FECHADA por D-ARQ-45.
**Nota de gravação.** Os docs desta sessão (D-ARQ-45 + status DT-003AN-01 + este bloco) foram gravados na 003.AR: o chat 003.AQ estourou o limite de contexto antes da gravação. A divergência git×HISTORICO na abertura da 003.AR (main sem PR de docs 003.AQ, HISTORICO fechando em 003.AP) foi gravação pendente, não defeito de processo.
**Próxima (003.AR).** Após gravar os docs da 003.AQ (esta PR de docs), decidir foco no kickoff. Candidatas vivas: P1 IMPL (materializar D-ARQ-45 — explosão multi-CAS + forma do trânsito CAS-plural + testes sintéticos; espelha 003.AP/P2; toca tipo compartilhado `Componente` → grep no repo inteiro per 003.I, passada adversária per 003.W; reconfirmar 432 por pytest antes de tocar código); camada-LLM do transcritor (D-ARQ-42 / D-ARQ-25 Parte B — salto que tira do sintético, maximamente destravado com P1 fechado); DT-003M-01 (CAS oculto + frase-H, lado-FDS); frente clínica R-CLI-01→R-CLI-02 (Marco 1, rema contra A→B); parse-PGR greenfield (D-ARQ-41, exige ARQUITETURA).

## Sessão 003.AR — 28/06/2026 — IMPLEMENTAÇÃO (P1: explosão de bloco "Derivados de:" multi-CAS no resolvedor — D-ARQ-45)
**Foco.** Materializar D-ARQ-45 P1: a explosão 1→N de bloco "Derivados de:" multi-CAS no resolvedor (`composicao.py`), a montante do `gate_cas`, com herança-α da faixa inteira. Fatia sintética, espelha a P2/003.AP. IMPLEMENTAÇÃO. Esta sessão abriu gravando os docs pendentes da 003.AQ (D-ARQ-45 + DT-003AN-01 RESOLVIDA + DECISOES v64 + PROTOCOLO v31 + bloco HISTORICO 003.AQ, PR #112 `4de49b4`) — o chat 003.AQ estourou contexto antes de gravar; a gravação foi o primeiro ato da 003.AR.
**Gate de estado real.** main em `4de49b4` (#112, docs 003.AQ). Tree limpa (untracked: `fds_originais/`, `matrizes_originais/*`, `medir_fds.py` — corretos). Suíte 432/432 reconfirmada por pytest (106s) antes de tocar arquivo. Quatro leituras literais via `Get-Content -Encoding UTF8` / `git grep`: `tipos.py` inteiro (contrato `Componente.cas: str` singular), `composicao.py` inteiro (loop de `resolver_composicao`, ordem `_normalizar_faixa`→`gate_cas`), `git grep "Componente("` (todos os construtores em `tests/`, zero em produção), `git grep "\.cas\b" motor/` (5 leitores, todos a jusante do ponto de explosão). Passada adversária do prompt contra os literais (per 003.W).
**Decisão de forma (cravada de disco).** Trânsito CAS-plural = opção (a) de D-ARQ-45 — separador no campo `cas`, não tipo de bloco novo (opção (b) reabriria D-ARQ-42 / contrato `tuple[Componente,...]` sem intermediário). Explosão como primeira operação do loop, a montante de `_normalizar_faixa` e `gate_cas`: o `\n` é consumido pelo split e nunca alcança `cas_bem_formado` (neutraliza a fragilidade anotada em D-ARQ-45). Ordem explodir→normalizar→gate: herança-α primeiro, normalização P2 por sub-CAS depois. Separador = `\n` literal [DERIVADO — 003.AN, único medido]; vírgula/`;`/`/` fora de escopo (critério de transcrição, herdado pela IMPL do transcritor). Três ataques adversariais materializados em teste: single-CAS no-op preserva identidade (`is`); `cas=""`/só-espaço não some (piso de 1, anti-supressão); `strip` de espaços internos.
**Entrega.** `_explodir_multi_cas` em `composicao.py` (split-`\n`, `strip`, descarta vazios, piso de 1 via `[componente]`; herança-α por `replace(cas=...)` que preserva nome/concentracao/flags). Loop de `resolver_composicao` itera `_explodir_multi_cas(c)` antes de normalizar/gatear. `test_explosao_multi_cas.py` (11 testes: 8 isolados + 3 integração — explosão+gate, explosão+normalização-P2 compondo, single-CAS inalterado). `resolvedor.py`/`tipos.py`/orquestrador/`fds_t65` INTOCADOS. Blast radius: 2 arquivos. D-ARQ-45 nota de aplicação 003.AR (DECISOES v65). PROTOCOLO intocado (P1 não cria/altera R-*; contrato de resolvedor). Este bloco. Commit `a04da18`, merge `f89abb3` (PR #113, "Create a merge commit"). Suíte 432→443; mypy --strict delta-zero em `composicao.py`.
**Nota de método (DT-003AR-01).** O anchor da EDIÇÃO 1 do prompt cirúrgico cruzava a fronteira entre duas top-level defs, onde vivem duas linhas em branco PEP8; o `Get-Content` cujo output montou o anchor colapsou-as no render do terminal, e o `old_str` saiu sem as blank lines. O Claude Code fez STOP-and-report (anchor mismatch), não improvisou — correção do anchor preservando o estilo PEP8 (opção 1), e a fatia seguiu. Lição: anchor que cruza fronteira de top-level def exige `git show` byte-exato ou `Select-String -Context` que preserve blank lines, nunca render de terminal. A passada adversária per 003.W deve incluir verificação de whitespace de fronteira para anchors inter-def. Dívida de processo, não de domínio clínico — fica no HISTORICO, não na seção 11 do PROTOCOLO.
**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (viva), DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01 (nova — anchor inter-def vs. whitespace PEP8), DH-003M-01 (segue ABERTA), DH-003P-01, DH-003A-01. DT-003AN-01 FECHADA (003.AQ).
**Próxima (003.AS).** Decisão do Diovanni no kickoff. Candidatas vivas: camada-LLM do transcritor-FDS (D-ARQ-42 / D-ARQ-25 Parte B — o salto que tira do sintético; com P1 fechado o contrato `tuple[Componente,...]` está completo quanto à granularidade, P1–P3 todo decidido/implementado exceto DT-003M-01; arco multi-sessão, onde A→B paga); DT-003M-01 (CAS oculto + frase-H, lado-FDS, decisão de arquitetura própria); parse-PGR greenfield (D-ARQ-41, maior massa, name→slug adiado por DT-003L-01, exige ARQUITETURA); frente clínica R-CLI-01→R-CLI-02 (Marco 1, rema contra A→B). Gate de estado real obrigatório; reconfirmar suíte por pytest antes de tocar código.

## Sessão 003.AS — 29/06/2026 — IMPLEMENTAÇÃO (camada parse-PDF determinística do transcritor-FDS — D-ARQ-42 Parte 1)

**Foco.** Abrir a camada-LLM do transcritor-FDS (D-ARQ-42), começando pela camada de baixo da bicamada interna: o parse-PDF determinístico. Modo ARQUITETURA confirmado no kickoff (candidata 1, A→B ratificado v56); a leitura dos docs vivos mostrou que D-ARQ-41/42/43 já fecharam padrão/contrato/recorte/fronteira-OCR — o que restava era IMPL com medição, não design aberto. Fatia: `extrair_tabelas_fds`, isolada, sem consumidor.

**Gate de estado real.** main em `a5961e4` → reconfirmada 443/443 por pytest (111s) antes de tocar arquivo. `git grep` de PDF-libs em `agente_medico/`+`scripts/`: 3 hits, todos fora do caminho (comentário em `composicao.py:33`; `scripts/migrar_*` legados) — transcritor greenfield confirmado em disco. `git show` de `composicao.py` (fronteira `produto.fds.composicao` que a `tuple[Componente,...]` alimenta) e `tipos.py` (`Componente`/`FaixaConcentracao`) lidos crus. `fds_originais/` = 6 PDFs; `fds_t65` = 3 transcritos à mão (gabarito de 3 dos 6).

**Reframe forçado pela medição.** O recorte da fatia DESCEU duas vezes contra o disco. (1) `extract_tables` ≠ texto corrido: o `\n`-empilhado de `_explodir_multi_cas` vem de célula de tabela, logo o parser tem de expor `extract_tables`, não só `extract_text`. (2) Medição dos 6 PDFs (`pdfplumber.extract_tables()` puro) provou que em Ciplan/Tigre a composição NÃO é tabela isolável — vem fundida num grid multi-seção. A "fatia mínima = extrai a tabela de composição" era impossível de satisfazer deterministicamente (não há tabela de composição isolada nesses dois); o recorte desceu para "extrai as tabelas cruas da página", com asserção literal forte só onde a composição é isolada (tinta/Leinertex/Massa) e fraca onde fundida (Ciplan/Tigre). A localização-de-composição e toda interpretação (coluna, `\n`-intra-token, grafias-de-ausente, `-`/`–`) viraram DT-003AS-01, lado-transcrição.

**Entrega.** `extrair_tabelas_fds(caminho) -> list[list[list[Optional[str]]]]` em módulo greenfield `agente_medico/motor/extracao_fds.py` (`pdfplumber.extract_tables()` cru sobre todas as páginas, achatadas; fronteira de página descartada). `test_extracao_fds.py`: 8 testes (5 parametrize ≥1-tabela-roda-sem-erro + tinta header/9-linhas/`\n`-intra-token literal + Leinertex/Massa `\n`-empilhado literal + Ciplan `vários` célula crua), `skipif` quando os PDFs untracked ausentes. NÃO importa `Componente` (fronteira D-ARQ-42 Parte 1 limpa). `composicao.py`/`tipos.py`/`resolvedor.py`/orquestrador/fixture INTOCADOS. Blast radius: 2 arquivos novos. D-ARQ-42 nota de aplicação 003.AS (DECISOES v66). DT-003AS-01 (PROTOCOLO v32). Este bloco. Commit `8da2fed`, merge `567454e` (PR #115, "Create a merge commit"). Suíte 443→451; mypy --strict limpo em `extracao_fds.py`.

**Nota de método 1 — output cru de medição vence síntese.** Duas vezes na sessão a síntese do Code (resumo em vez de colagem crua) teria me feito cravar âncora errada: a contagem "8/7 linhas de composição" que eu ia asserir não existe para Ciplan/Tigre (composição fundida, não isolável) — só o `medir_fds_gabarito_output.txt` cru revelou; e o shape de `extract_tables` (coluna-deslocada na Tigre, `\n`-intra-token no TiO₂) só apareceu no output literal, não na síntese. Gêmeo de DT-003AR-01 (anchor de síntese vs anchor de disco), aplicado a shape de medição: para cravar asserção de teste, exigir output cru de disco, nunca síntese do Code.

**Nota de método 2 — prompt cirúrgico omitiu o passo de branch.** O prompt da fatia tinha `git add`/`commit` mas NÃO o `git checkout -b` da branch — o Code, executando literalmente, commitou em `main` local (nada pushado). **Falha de prompt do Arquiteto, não do Code:** o Code aplica o que está escrito; omissão no prompt é decisão silenciosa. Corrigido por branch retroativa pré-push (`git branch feat/003as-parse-pdf` no commit → `git reset --hard origin/main` → push da branch → PR #115 "Create a merge commit"). Emenda permanente ao protocolo de prompt cirúrgico: todo prompt que commita abre com `git checkout -b` da branch, antes de add/commit. Dívida de processo, não de domínio — fica no HISTORICO.

**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (viva), DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AS-01 (nova — patologias de layout/transcrição de FDS), DH-003M-01 (segue ABERTA), DH-003P-01, DH-003A-01.

**Próxima (003.AT).** Decisão do Diovanni no kickoff. Candidata natural: a fatia de transcrição-FDS que consome DT-003AS-01 (grade crua → `tuple[Componente,...]`, onde entra a decisão LLM-vs-heurística e as 6 patologias). Gate de estado real obrigatório; reconfirmar suíte por pytest antes de tocar código.

## Sessão 003.AT — 29/06/2026 — ARQUITETURA (mecanismo do transcritor-LLM: localização, nome, gabarito — D-ARQ-42)

**Foco.** Transcrição-FDS, camada-LLM do transcritor (D-ARQ-42 Parte 2 / D-ARQ-25 Parte B). Decisão de mecanismo. ARQUITETURA pura — sem código, sem gate de pytest.

**Abertura.** main `c89ec6c`, sync `origin/main`, working tree limpo. HISTORICO fechava em 003.AS; cruzamento git × HISTORICO sem divergência. Suíte de referência 451 (não reconfirmada por pytest — ARQUITETURA não toca arquivo). Modo/foco confirmados pelo Diovanni.

**Pré-requisito factual fechado.** "Seção de composição 2 vs 3" (`[A CONFIRMAR — NBR 14725]`, DT-003AS-01) resolvido por web_search: composição é seção 3 na NBR 14725:2023, **título normativo estável**, numeração de fabricante varia. Decorrência: âncora de localização por título, não por número. Texto oficial ABNT é pago (não conferido) — convergência de fontes secundárias + FDS reais sustenta; status frouxo da numeração não enfraquece a âncora-por-título.

**Decisão (aplicação de D-ARQ-42, não ID nova).** Três cláusulas: (1) localização por título normativo, robusta à renumeração, com limite declarado em grid-fundido (localiza início, não isola grade — patologia 2 remanesce); opera na camada-LLM sobre texto, `extracao_fds.py` intocado; keyed na NBR-BR. (2) `nome` transcrito informativo, não-`==`. (3) gabarito por par PDF↔`fds_t65` em disco, LLM mockado, nunca testa API. Recorte (A) mantido (frase-H fora; Segredo Industrial 2 → ramo d → AUSENTE, DT-003M-01). Adiados para IMPL por medição (molde D-ARQ-41 P3): prompt; `\n`-regex (patologia 3); grafias-de-ausente (patologia 4); separador `-`/`–` (patologia 5).

**Método.** Duas passadas adversariais a pedido do Diovanni pegaram 6 furos antes da selagem: cláusula 1 superestimava ("resolve" patologia 1 → corrigido para "localiza, não isola grade"); mistura camada-LLM vs parse-PDF (marcado: opera sobre texto, `extracao_fds.py` intocado); `[DERIVADO]` forte demais sobre fonte ABNT paga (rebaixado); cláusula esvaziada (decisão = âncora-por-título-não-número, resto é eco de DT); confronto faltante contra patologia 1 (grid não-isolável → limite declarado); marca de escopo D-ARQ-06 ausente (keyed na NBR-BR). Terceira passada dispensada — retorno marginal.

**Sem código. Sem regra clínica tocada. Nenhuma DT nova** (DT-003AS-01 já cobre as patologias adiadas).

**Pendências abertas:** DT-FDS-02, DT-003L-01, DT-003M-01 (viva), DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AS-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Entregas (D-ARQ-32):** DECISOES (aplicação 003.AT em D-ARQ-42 + changelog v67); PROTOCOLO intocado (R-* intactas, DT-003AS-01 já registra as patologias); este bloco; handoff 003.AT→003.AU.

**Próxima (003.AU).** Decisão do Diovanni no kickoff. Candidata natural: IMPL do transcritor-LLM, fatia 1 — transcrição sobre o texto extraído (camada acima de `extracao_fds.py`), produzindo `tuple[Componente,...]` cru que `resolver_composicao` consome. Gate de estado real obrigatório (pytest 451, `git grep` de extracao_fds/transcritor, leitura dos 3 PDFs↔fixture); LLM mockado no teste, nunca a API. Prompt cirúrgico que commita abre com `git checkout -b` (003.AS) e, se tocar tipo/fixture, passada adversária extra com verificação de whitespace de fronteira (003.AR/003.AS).

## Sessão 003.AU — 29/06/2026 — IMPLEMENTAÇÃO (fatia 1 da normalização do verbatim-FDS — D-ARQ-42)

Foco. Camada determinística de normalização do verbatim transcrito da FDS: patologias 3/4/5 de DT-003AS-01 como funções puras. Fatia 1 do transcritor-FDS pós-parse-PDF (003.AS).

Recorte (ARQUITETURA-leve no início). LLM-verbatim-mockado + montagem em `Componente` + contrato do verbatim (tipo intermediário, gêmeo "PGR transcrita" D-ARQ-41 P2) FORA — fatia futura. Fatia 1 = só normalização determinística, testável sem mock de API (molde isolado 003.AP/003.S/003.AS).

Entregue. `agente_medico/motor/transcricao_fds.py` greenfield: `desambiguar_cas` (P3), `normalizar_cas_ausente` (P4), `parsear_faixa` (P5, sem ordenar). Isolado, sem consumidor. `tipos.py`/`composicao.py`(`_explodir_multi_cas`)/`extracao_fds.py`/`resolvedor.py` intocados (só importa `cas_bem_formado`).

Achado — heurística P3 corrigida. Spec do prompt tinha buraco: validado em disco, `134363-67-` passa o dígito isoladamente (coincidência) mas a junção `134363-67-7` falha (CAS real e errado da tinta, ramo c do gate) → TiO₂ indefinido na regra dupla. Corrigido: preserva só se AMBOS fragmentos bem-formados; senão junta, sem exigir junção válida (validade é do gate, D-ARQ-36). Limite residual (D-ARQ-22): falso-preserva em coincidência dupla (sem caso medido). Causa-raiz: a passada adversária do prompt mirou whitespace, não a regra de decisão.

Possível DT futura. `cas_bem_formado` aceita `134363-67-` (sem último dígito) — validador tolerante à estrutura de hífen. Fora de escopo; o gate funciona nas âncoras.

Verificação. 26 testes; suíte 451→477, 100% verde; mypy --strict limpo. Passada adversária de whitespace de fronteira no `\n` (tab+newline, espaços assimétricos, vazio) — OK.

Git. Commit `0135754`, merge `f3452bb`, PR #118. Branch feat deletada, main sincronizado.

## Sessão 003.AV — 29/06/2026 — ARQUITETURA (contrato do verbatim transcrito da FDS — D-ARQ-46)

**Foco.** Selar a forma do tipo intermediário do verbatim transcrito da FDS (saída do LLM-transcritor = entrada da normalização P3/P4/P5) e como a montagem `verbatim → tuple[Componente,...]` compõe P3/P4/P5. Gêmeo-FDS da "PGR transcrita" de D-ARQ-41 P2, aberto desde 003.AU.

**Gate de abertura.** main `851040a` (PR #119), working tree limpo, untracked = clutter pré-existente (`fds_originais/`, `matrizes_originais/`, `medir_fds*.py`). Sem divergência git × HISTORICO. Docs vivos lidos inteiros (PROTOCOLO v33 + DECISOES v68). Gate de estado real por greps + `Get-Content` de `transcricao_fds.py` e `tipos.py`: verbatim-type inexistente; P3/P4/P5 puras sobre strings cruas; `Componente.concentracao` é `FaixaConcentracao` já parseada (sem casa para texto cru de faixa); `_explodir_multi_cas`/`_normalizar_faixa` no resolvedor.

**Decisão (D-ARQ-46).** O LLM-transcritor emite o verbatim cru (cas/nome/faixa como texto, por componente); `tuple[Componente,...]` é saída da montagem determinística (P3/P4/P5), não do LLM. Fronteira LLM↔determinístico = o verbatim. Montagem 1→1 (explosão multi-CAS e ordenação min/max ficam no resolvedor). Crava semântica + fronteira; dataclass-form e local-de-módulo descem para a IMPL (003.AW).

**Achado da passada crítica (o eixo da sessão).** A 1ª passada amaciou como "refino" o que é contradição: D-ARQ-42 P2 diz na letra que o transcritor produz `Componente(concentracao=<FaixaConcentracao transcrita>)` — mas P5 (`parsear_faixa`, 003.AU) recebe texto cru; se o LLM já entregasse `FaixaConcentracao`, P5 é morto. A 003.AU criou o split em silêncio; 003.AV o formaliza e corrige D-ARQ-42 P2 explicitamente. A passada também pegou overreach: "tipo frozen dedicado" e "montagem em `transcricao_fds.py`" rebaixados de crava-de-arquitetura para recomendação (precedente: ARQUITETURA crava semântica, IMPL crava forma — D-ARQ-34→003.I, D-ARQ-42→003.V→003.W).

**Git.** Sessão de ARQUITETURA — sem código. Gravação doc-only (D-ARQ-46 + changelog v69 + este bloco). Suíte 477 intocada.

**Pendências/dívidas.** Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AS-01 (patologias 1/2), DH-003M-01, DH-003P-01, DH-003A-01. Recorte (A) e patologia 1 (producibilidade do verbatim) seguem barrando FDS de grid não-isolável.

**Próxima (003.AW — IMPLEMENTAÇÃO).** Montagem `verbatim → tuple[Componente,...]` + LLM-transcritor mockado, sobre o contrato D-ARQ-46. Decide com gate: forma do verbatim (dataclass frozen recomendada), local da montagem (`transcricao_fds.py` recomendado), ordem P3→P4, nomes de campo. Gabarito = par PDF↔`fds_t65` (D-ARQ-42 P4 / 003.AT), LLM mockado, nunca testa API. Reconfirmar 477 por pytest antes de tocar arquivo.

## Sessão 003.AW — 30/06/2026 — IMPLEMENTAÇÃO (montagem verbatim → `tuple[Componente,...]` + LLM-transcritor mockado — D-ARQ-46)

**Foco.** Materializar a montagem determinística `verbatim → tuple[Componente,...]` sobre o contrato D-ARQ-46, com o LLM-transcritor mockado. Decidir as formas que D-ARQ-46 rebaixou a recomendação (forma do verbatim, local da montagem, nomes de campo) com gate de estado real e código na mão.

**Gate de abertura.** main `60df3fd` (PR #120). Ambiente: Cowork com o repo montado (não o PowerShell habitual). Divergência aparente git × handoff — working tree inteiro como `M` — diagnosticada como **só EOL** (CRLF↔LF; `git diff --ignore-all-space` vazio; `.gitattributes` no topo): conteúdo limpo, bate com o handoff. Gate de estado real rodado no próprio ambiente: pytest **477** (motor novo 328 + legada 149), `git grep` confirmou `Componente` construído só em testes/fixtures, releitura literal de `transcricao_fds.py`/`tipos.py`/`composicao.py`/`fds_t65.py`. Docs vivos lidos inteiros (PROTOCOLO v33 + DECISOES v69), D-ARQ-46 literal.

**Decisão de forma (003.AW).** (1) `ComponenteVerbatim(cas/nome/faixa: str)` frozen em `tipos.py` — dado no lar dos dataclasses; campo `faixa` ≠ `concentracao` marca texto cru. (2) `montar_componente` (1→1) + `montar_composicao(Sequence)` em `transcricao_fds.py`. (3) Ordem `normalizar_cas_ausente(desambiguar_cas(cas))` (cravada D-ARQ-46 Parte 4). Recomendações de D-ARQ-46 confirmadas, não revertidas.

**Achado da passada crítica.** Material de medição untracked (`medir_fds_gabarito_output.txt`) traz o texto cru real extraído dos 6 PDFs — usado para tornar o verbatim mockado **fiel à medição**, não inventado (evita teste tautológico). Tinta (9 comp.) e Ciplan (8 comp.) reproduzem `cas`+`concentracao` do `fds_t65`; Adesivo Tigre fica fora do gabarito verde — patologia 1 (grid fundido, MEK/Acetato sem faixa na linha) barra a producibilidade do verbatim. A passada adversária (toca tipo compartilhado `tipos.py`) expôs DT-003AW-01 (grafia-ausente quebrada por `\n`).

**Nota de ambiente (META).** O mount do Cowork proíbe `unlink`/`rm`: Edit/Write truncaram arquivos editados; contornado escrevendo via `/tmp`+`cp` (validado por `py_compile`), EOL por `sed`+`cp`, locks git órfãos por `mv`, commit com `core.autocrlf=false` e `git add` explícito (nunca `-A`, arrastaria o ruído EOL). Registrado em memória do agente para sessões futuras neste ambiente. Resíduos a limpar no `.git` (host): `*.lock.old*`, `index.lock.orphan`.

**Verificação.** 11 testes (`test_montagem_verbatim.py`); suíte 477→488, 100% verde (motor novo 339; legada 149 intocada); mypy --strict limpo nos 4 arquivos. Diff sem ruído EOL (`git add` seletivo). Passada adversária extra por tocar `tipos.py` (molde 003.I/003.W).

**Git.** Commit `ec3b225`, merge `8054f5b`, PR #121, "Create a merge commit". Branch feat deletada, main sincronizado em `8054f5b`. Identidade git setada local no sandbox (a confirmar/ajustar no host).

**Pendências/dívidas.** Inalteradas, + DT-003AW-01 (nova, ABERTA, não-bloqueante): DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AS-01 (patologias 1/2), DT-003AW-01, DH-003M-01, DH-003P-01, DH-003A-01. Recorte (A) e patologia 1 seguem barrando FDS de grid não-isolável.

**Próxima.** Candidatas: patologias 1/2 de DT-003AS-01 (localização por header/bbox, camada-LLM) — desbloqueiam a producibilidade do verbatim para Ciplan/Tigre; ou plugar `montar_composicao` no pipeline (hoje nasce sem chamador, espelha 003.J/003.S/003.AR). Modo+foco e numeração: do Diovanni.

---

## Sessão 003.AX — 30/06/2026 — ARQUITETURA (patologias 1/2 de DT-003AS-01: mecanismo e representação-de-entrada do transcritor-FDS)

**Ambiente.** Cowork com o repo `automacao-pgr-pcmso` montado (não o PowerShell habitual). Abertura barrada por `.git/HEAD` corrompido (24 bytes `NUL` após `ref: refs/heads/main\n`, truncamento do mount) → git acusava "invalid HEAD", árvore inteira como `A`. Diagnóstico: `refs/heads/main` (`0fce362`), `packed-refs`, `config` e objetos íntegros (`fsck` só com erros derivados do HEAD); única corrupção no HEAD. Correção não-destrutiva (`printf 'ref: refs/heads/main\n' > /tmp/HEAD_fix && cp /tmp/HEAD_fix .git/HEAD`, autorizada). Pós-fix: `main @ 0fce362`, `fsck` limpo, working tree só com EOL cosmético (`git diff --ignore-all-space` vazio nos ~130 `M`). Locks órfãos do mount limpos por rename same-dir (cross-device pra `/tmp` é bloqueado). Achados de ambiente (HEAD-NUL, distinção rename same-dir vs cross-device) salvos em memória do agente.

**Foco e pivô.** Modo declarado IMPLEMENTAÇÃO (Cand. 2: plugar `montar_composicao`). O gate de leitura derrubou a premissa: `montar_composicao` e `resolver_composicao` não se tocam — a cadeia é `extrair_tabelas → [GAP transcrição] → montar_composicao → FDS.composicao → resolver_composicao`; o GAP (tabelas→verbatim) é a Cand. 1, e nenhum código de produção constrói `FDS.composicao` (só fixtures; `entrada.py` é fachada fina). Logo Cand. 2 depende da Cand. 1 — o "independente" do handoff estava errado. Pivô para Cand. 1 (ARQUITETURA), autorizado.

**Gate de estado real (ARQUITETURA).** Docs vivos lidos inteiros (PROTOCOLO v34 + DECISOES v70); D-ARQ-42/43/45/46 + DT-003AS-01 literais; `git grep` da cadeia composição (`montar_composicao`/`resolver_composicao`/`FDS(`); medição read-only `extract_text`/`extract_words` Ciplan+Tigre+Leinertex (espelha 003.AN/AS, não toca motor).

**Decisão (nota 003.AX em D-ARQ-42).** (1) Patologias 1/2 = camada-LLM semântica, não bbox determinístico (D-ARQ-41/42 + universalidade + a patologia-2 como evidência pró-LLM). (2) Entrada do LLM = `extract_text` da região âncora-por-título, não `extract_tables`: medido que o título-âncora some no `extract_tables` do Tigre e sobrevive no texto, e que a patologia 2 (faixa perdida) é artefato do `extract_tables` (no texto MEK/Acetato voltam com faixa `10 – 42` / `05 – 30`). (3) DT-003AX-01 aberta: a virada tabelas→texto reabre o mecanismo de explosão multi-CAS (D-ARQ-45 `\n`-célula, não a decisão) e o papel do `extrair_tabelas_fds` (003.AS) — reconciliação texto-puro vs híbrido é passada dedicada.

**Achado da passada crítica.** O ripple em D-ARQ-45 é de MECANISMO, não de decisão (explodir + herança-α permanece, cruza D-ARQ-35); a associação faixa↔componente no bloco "Derivados de:" é ambígua em texto linear (faixa em linha própria, não colada ao CAS), o que REFORÇA adiar a reconciliação em vez de cramá-la aqui. Segundo ripple (papel do `extrair_tabelas_fds`) entrelaçado com o primeiro — um só DT.

**Verificação.** Sem código, sem pytest (ARQUITETURA). Decisão DERIVADA de medição read-only em disco, não de especulação (anti-D-ARQ-22). Duas passadas: a 2ª afinou "mata D-ARQ-45" → "mata o mecanismo `\n`-célula do D-ARQ-45" e expôs o 2º ripple (`extrair_tabelas_fds`).

**Git.** Sem commit de código. Docs vivos atualizados: DECISOES v71 (nota 003.AX em D-ARQ-42), PROTOCOLO v35 (andamento DT-003AS-01 + DT-003AX-01), este bloco. EOL normalizado a LF nos 3 docs tocados (alinha `.gitattributes`/HEAD; diff limpo só com adições). Commit/PR/merge: do Diovanni.

**Pendências/dívidas.** + DT-003AX-01 (nova, ABERTA, não-bloqueante). DT-003AS-01: patologias 1/2 saem de "abertas" para "decididas como camada-LLM + entrada `extract_text`" (IMPL futura); DT segue ABERTA (IMPL pendente). Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** Candidatas: (1) reconciliação DT-003AX-01 (texto-puro vs híbrido; explosão multi-CAS sem `\n`-célula; associação faixa↔componente — provável CONHECIMENTO/medição + ARQUITETURA); (2) IMPL do LLM-transcritor sobre a entrada-texto decidida (depende de (1) para o multi-CAS). Modo+foco e numeração: do Diovanni.

## Sessão 003.AY — 30/06/2026 — CONHECIMENTO/medição → ARQUITETURA (reconciliação DT-003AX-01: representação-de-entrada do transcritor-FDS + mecanismo de explosão multi-CAS)

**Ambiente.** Cowork com o repo `automacao-pgr-pcmso` montado. Abertura limpa — `.git/HEAD` íntegro (`ref: refs/heads/main`, sem bytes NUL), `git log` topo `811d704` (merge PR #123), working tree só com EOL cosmético (`git diff --ignore-all-space` vazio nos ~130 `M`). Sem correção de HEAD necessária. Docs editados via Python→`/tmp`→`cp` com `newline="\n"` (o mount trunca Edit/Write e re-corrompe HEAD em escrita via host↔mount).

**Foco.** Modo declarado pelo Diovanni: CONHECIMENTO/medição + ARQUITETURA, Candidata 1 — reconciliação DT-003AX-01.

**Gate de estado real (ARQUITETURA).** Docs vivos lidos inteiros (PROTOCOLO v35 + DECISOES v71); D-ARQ-33/34/35/36/41/42/43/45/46 + DT-003AS-01/AN-01/AX-01 literais; medição read-only `extract_text`/`extract_tables` sobre os 6 PDFs de `fds_originais/` (espelha 003.AN/AS/AX, não toca motor). Sem pytest (ARQUITETURA, sem código) — 488 herdado não reconfirmado, será reconfirmado ANTES de tocar arquivo na IMPL.

**Medição (disco).** (a) Bloco "Derivados de:" no `extract_text` (Leinertex/Massa): conteúdo sobrevive (header + N CAS + faixa única), mas a estrutura de linha morre — CAS em linhas separadas (sem token empilhado `"2634-33-5\n55965-84-9"`), POSIÇÃO da faixa instável entre FDS (Leinertex blk1: faixa entre os 2 CAS; blk2: colada ao componente do meio; Massa: 1ª linha antes dos nomes). (b) Mesmo bloco no `extract_tables`: linha perfeita — `cell[1]="2634-33-5\n55965-84-9"` (`\n`-célula do `_explodir_multi_cas`/003.AR) + `cell[2]` com a faixa: agrupamento + α de graça. (c) DISJUNÇÃO no acervo: blocos multi-CAS "Derivados de:" SÓ em Leinertex/Massa (table-isolável-limpo); Ciplan/Tigre (grid-fundido, que forçaram a virada p/ texto na 003.AX) não têm bloco multi-CAS.

**Decisão (notas de aplicação 003.AY em D-ARQ-42 e D-ARQ-45).** (1) Entrada do transcritor = TEXTO-PURO (`extract_text` âncora-por-título), não híbrido. Híbrido sinalizado como PALIATIVO: reusa `_explodir_multi_cas` intacto mas exige roteador por-FDS (classificação nova, superfície de erro silencioso, D-ARQ-22) e aposta na disjunção do acervo ser estrutural (D-ARQ-06) — uma FDS grid-fundida COM multi-CAS quebra-o. Texto-puro é universal e não adiciona paradigma (agrupamento semântico já selado em D-ARQ-41/42); a instabilidade de posição da faixa torna parser-textual-determinístico inseguro, reforçando o agrupamento-LLM. (2) Explosão migra de `\n`-split (003.AR) p/ expansão-de-grupo no resolvedor — DECISÃO do D-ARQ-45 (explodir 1→N + herança-α, resolvedor-side, cardinalidade fora do LLM, D-ARQ-45 P1) preservada, só o mecanismo muda; o LLM emite o bloco como grupo verbatim (CAS + faixa única), o resolvedor expande. (3) `extrair_tabelas_fds` (003.AS) deixa de ser entrada do transcritor → candidato DEPRECATED ou cross-check determinístico (IMPL decide).

**Passada crítica.** 2ª passada confirmou: (a) não reabre D-ARQ-45 — só o mecanismo de 003.AR cai, a decisão fica; (b) o agrupamento que o LLM passa a ler (faixa única no escopo do bloco) é carga semântica BOUNDED, defensável como transcrição (faixa escrita uma vez por bloco); o LLM não parte/copia/computa α nem decide N (resolvedor-side) — resíduo candidato-revisado-pelo-RT (D-ARQ-33 cl.4), não novo; (c) "Derivados de:" como delimitador é DERIVADO de 3 blocos em 2 FDS (n pequeno), mas o agrupamento-semântico é robusto a variação de string literal — argumento pró texto-puro, não contra. Universalidade (D-ARQ-06): texto-puro + agrupamento-LLM lê construção (Leinertex/Massa medidos), química (matéria-prima agrupada) e saúde (impurezas agrupadas) por sentido; híbrido exigiria roteador por-setor.

**Verificação.** Sem código, sem pytest (ARQUITETURA). Decisão DERIVADA de medição read-only em disco (anti-D-ARQ-22), não de especulação. Duas passadas.

**Git.** Sem commit de código. Docs vivos atualizados: DECISOES v72 (nota de aplicação 003.AY em D-ARQ-42 + nota 003.AY em D-ARQ-45), PROTOCOLO v36 (DT-003AX-01 RESOLVIDA + andamento DT-003AS-01), este bloco. EOL normalizado a LF nos 3 docs tocados (diff limpo só com adições). Commit/PR/merge: do Diovanni.

**Pendências/dívidas.** DT-003AX-01 → RESOLVIDA (reconciliação; IMPL pendente, não-bloqueante). DT-003AS-01 segue ABERTA (patologia 1 IMPL pendente; entrada texto-puro cravada). Novos itens ABERTOS p/ IMPL (forma/IMPL, precedente "Aberto para a IMPL" de D-ARQ-45): forma do verbatim-grupo (`BlocoVerbatim` vs `ComponenteVerbatim`+`grupo_id`); `_explodir_multi_cas` aposentar vs generalizar; destino de `extrair_tabelas_fds`. Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01, DT-003M-02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** Candidata natural: IMPL do transcritor-FDS sobre a entrada texto-puro decidida — fatia que materializa (i) o verbatim-grupo + parse-PDF `extract_text` âncora-por-título e (ii) a expansão-de-grupo no resolvedor substituindo o `\n`-split. Gate de estado real obrigatório (reconfirmar 488 por pytest ANTES de tocar arquivo; reler literais de `composicao.py`/`transcricao_fds.py`/`extracao_fds.py`/`tipos.py`; tocar tipo compartilhado → passada adversária + grep repo-inteiro). Modo+foco e numeração: do Diovanni.

## Sessão 003.AZ — 01/07/2026 — IMPLEMENTAÇÃO (fatia i do transcritor-FDS: forma do verbatim-grupo `BlocoVerbatim` + montagem-de-grupo)

**Ambiente.** Kickoff + gate + decisão de forma no Cowork (mount read/pytest); IMPL executada pelo Claude Code no host. Abertura: `main` em `0b548ef` (PR #124), sincronizada com `origin/main`; working tree só com EOL cosmético.

**Foco.** IMPL declarada pelo Diovanni. Fatia (i) da IMPL do transcritor-FDS sob a entrada texto-puro selada na 003.AY.

**Gate de estado real.** pytest **488 verde reconfirmado** (motor novo 339 + legada 149) ANTES de tocar arquivo — a suíte legada é lenta no sandbox por fixture class-scoped re-parseando PDF real, não por lógica; rodada por classe confirma 98/98 do `test_regressao_pcmso`. Literais relidos: `transcricao_fds.py`, `composicao.py`, `tipos.py`, `extracao_fds.py`. Grep de produtores/consumidores: `ComponenteVerbatim`/`montar_*` só em `transcricao_fds.py` + fixture + teste; `_explodir_multi_cas` consumido só por `resolver_composicao`; `extrair_tabelas_fds` sem consumidor no motor (só testes).

**Decisão de forma (ratificada pelo Diovanni).** (1) verbatim-grupo = `BlocoVerbatim` aninhado (não flat+grupo_id); (2) `_explodir_multi_cas` = aposentar+reescrever `_explodir_bloco` (não generalizar); (3) `extrair_tabelas_fds` = DEPRECATED (não cross-check); (4) escopo desta sessão = só fatia (i) tipo+montagem. Detalhe em DECISOES (nota 003.AZ em D-ARQ-46 + D-ARQ-45).

**IMPL (Code).** `tipos.py`: +`MembroVerbatim`/`BlocoVerbatim`/`BlocoComponente`, −`ComponenteVerbatim`. `transcricao_fds.py`: `_montar_membro`/`montar_bloco`/`montar_composicao` substituindo `montar_componente`/`montar_composicao`; P3/P4/P5 intocadas. Fixtures: `fds_verbatim_t65` → BlocoVerbatim-singleton; `fds_verbatim_leinertex` nova (bloco multi-CAS real N=2/N=3, medição 003.AN/AY). `test_montagem_verbatim.py` migrado + teste de preservação-de-grupo (membros single-CAS, `concentracao=None`, faixa do bloco não-ordenada).

**Verificação.** Suíte 488→**489**; mypy --strict **delta-zero** (46 pré-existentes, arquivos não-tocados); `git grep ComponenteVerbatim` vazio em `*.py`. Cobertura da regra-de-grupo: teste novo falha sem `BlocoVerbatim`, passa com.

**Git.** Commit `9a4eaf3` na branch `feat-003az-blocoverbatim-montagem`, 5 arquivos nominais. `composicao.py`/`_explodir_multi_cas`/`resolvedor.py`/`extracao_fds.py` intocados. Sem push/PR (do Diovanni). Docs: DECISOES v73, PROTOCOLO v37, este bloco.

**Pendências.** Fatia (ii)/003.BA: `_explodir_bloco` no resolver (expansão 1→N + herança-α) + aposentar `_explodir_multi_cas` + `extrair_tabelas_fds` DEPRECATED. Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DH-003M-01, DH-003P-01, DH-003A-01. DT-003AS-01 avança (fatia i feita).

**Próxima.** 003.BA — IMPL fatia (ii): expansão-de-grupo no resolver. Gate de estado real obrigatório (reconfirmar 489 por pytest; reler `composicao.py`/`tipos.py`; grep de quem consome `BlocoComponente`/`_explodir_multi_cas`).

## Sessão 003.BA — 01/07/2026 — IMPLEMENTAÇÃO (fatia ii do transcritor-FDS: expansão-de-grupo `_explodir_bloco`, recorte enxuto)

**Ambiente.** IMPL executada pelo Claude Code no host. Abertura: `main` em `5ab6086` (merge PR #125), sincronizada com `origin/main`; working tree limpa (só untracked de sempre, fora do escopo).

**Foco.** IMPL declarada pelo Diovanni. Fatia (ii) da IMPL do transcritor-FDS — expansão-de-grupo, recorte ratificado como adição ISOLADA: só `_explodir_bloco` (sem gate, sem chamador) + `extrair_tabelas_fds` DEPRECATED. Aposentadoria de `_explodir_multi_cas`, wiring em `resolver_composicao` e migração de `test_explosao_multi_cas.py` explicitamente FORA de escopo (fatia iii).

**Gate de estado real.** pytest **489 verde reconfirmado** ANTES de tocar arquivo. Branch nova `feat-003ba-explodir-bloco` a partir de `main` atualizada.

**IMPL (Code).** `composicao.py`: `_explodir_bloco(bloco: BlocoComponente) -> tuple[Componente, ...]` adicionado ao lado de `_explodir_multi_cas` (import de `BlocoComponente` somado a `tipos`) — expande os membros do bloco, cada um herdando a `FaixaConcentracao` do bloco via `dataclasses.replace` (só troca `concentracao`) e canonicalizado por `_normalizar_faixa` (D-ARQ-43 P2); sem `gate_cas` dentro (exige `indice_cas`, responsabilidade do resolver — fatia iii); sem chamador em `resolver_composicao`. `extracao_fds.py`: docstring de `extrair_tabelas_fds` prefixada com `DEPRECATED (003.BA): entrada de composição migrou para texto-puro (D-ARQ-42); mantida para rastreabilidade, sem consumidor no motor.` — corpo intocado. `test_explodir_bloco.py` novo: 6 testes (2/3/1 membros por cardinalidade; herança-α com faixa invertida normalizada; bloco sem faixa → membros sem faixa; cas/nome/flags do membro preservados), cada um falha sem `_explodir_bloco` e passa com.

**Nota de higiene.** `composicao.py` e `extracao_fds.py` vieram do disco em CRLF (convenção mista no repo, por arquivo); a edição inicial produziu diff de arquivo inteiro por causa disso. Normalizados de volta a LF (o que já tinham no HEAD) antes de comitar — diff final mínimo (28 e 5 linhas), suíte e mypy reconfirmados depois da normalização.

**Verificação.** Suíte 489→**495** (6 testes novos, delta exato); mypy --strict **delta-zero** em `composicao.py` (limpo) — 46 erros pré-existentes em arquivos não-tocados, inalterados. `git grep _explodir_multi_cas|resolver_composicao` só mostra ocorrências pré-existentes (definição + uso em `resolver_composicao`/`orquestrador.py`/comentários de `transcricao_fds.py`) — nada novo. `git diff --stat` vs `main`: só `composicao.py`, `extracao_fds.py`, `test_explodir_bloco.py`.

**Git.** Commit `add384f` na branch `feat-003ba-explodir-bloco`, push para `origin` (autorizado pelo Diovanni). `_explodir_multi_cas`, `resolver_composicao`, `FDS.composicao`, `test_explosao_multi_cas.py` intocados. Sem PR/merge nesta etapa. Docs: DECISOES v74 (nota 003.BA em D-ARQ-45), este bloco. `PROTOCOLO_AGENTE_MEDICO.md`/`PAINEL_ESTADO.md` deliberadamente NÃO tocados (fora do escopo desta rodada de docs).

**Pendências.** Fatia (iii)/003.BB: aposentar `_explodir_multi_cas`, plugar `_explodir_bloco` em `resolver_composicao` (wiring real no pipeline), migrar/atualizar `test_explosao_multi_cas.py`. Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DH-003M-01, DH-003P-01, DH-003A-01. DT-003AS-01 segue ABERTA (patologia 1 do transcritor, não desta fatia).

**Próxima.** 003.BB — IMPL fatia (iii): aposentadoria de `_explodir_multi_cas` + wiring de `_explodir_bloco` no resolver + migração de testes. Gate de estado real obrigatório (reconfirmar 495 por pytest; reler `composicao.py`/`resolvedor.py`; tocar `resolver_composicao` exige passada adversária, per precedente de tipo/função compartilhada).

### Adenda 003.BA — 01/07/2026 — discussão de escopo (pós-merge, sem código)

**Gatilho.** Diovanni comparou a saída completa do legado (módulo Engenharia: Anexo I do PGR — NR-01 + NR-15/09 + NR-07 + Dec 3.048 + eSocial Tab 24) e perguntou se o motor novo deve reproduzi-la ("completo pro engenheiro ver") ou seguir a rota atual.

**Achado (disco, 937209c).** Resultado do motor novo emite só o lado-médico (GHE×ExameEmitido). Zero previdenciário/eSocial em agente_medico/ (git grep vazio; vivem no legado). A tela é lado-ENGENHEIRO (Anexo I) = INPUT (tipos.PGR), não produto do agente médico.

**Decisão (Arquiteto recomenda, Diovanni ratifica).** Continuar a rota atual (ingestão + lado-médico). Não replicar o Anexo I do engenheiro no motor novo agora. Previdenciário+eSocial+engenharia = frente de emissão separada perto do cutover (paridade p/ desligar Streamlit). Prova de vida = Marco 1 já cravado (não criar marco novo).

**Entregas.** DECISOES v75 + DT-003BA-01. PAINEL não tocado (Marco 1 já cobre; DT-003BA-01 a triar na próxima re-tiragem). PROTOCOLO intocado (sem regra clínica). Sem git de código.

## Sessão 003.BB — 01/07/2026 — IMPLEMENTAÇÃO (fatia iii do transcritor-FDS: wiring de `_explodir_bloco` no resolver + aposentadoria de `_explodir_multi_cas`)

**Ambiente.** IMPL executada pelo Claude Code no host. Abertura: `main` em `f399961` (merge PR #127), sincronizada com `origin/main`; working tree limpa.

**Foco.** IMPL declarada pelo Diovanni. Fatia (iii): fecha as três pendências abertas do bloco 003.BA. Fork de modelo de dados (forma do trânsito bloco→resolver) ratificado pelo Arquiteto+Diovanni ANTES do prompt cirúrgico: **opção B** (campo `composicao_verbatim` separado) + **manter** o verbatim na saída. Opções C e D descartadas com razão registrada em D-ARQ-45 (aplicação 003.BB).

**Gate de estado real.** pytest **495 verde reconfirmado** ANTES de tocar arquivo. Leitura real de `composicao.py`, `tipos.py`, `transcricao_fds.py`, `test_explosao_multi_cas.py` e dos 5 arquivos de teste que fluem pelo resolver. Branch nova `feat/003bb-plugar-explodir-bloco` a partir de `main` atualizada. Passada adversária (toca tipo compartilhado `tipos.py` + função `resolver_composicao`).

**IMPL (Code).** `tipos.py`: `FDS` ganha `composicao_verbatim: tuple[BlocoComponente, ...] = ()`. `composicao.py`: `_explodir_multi_cas` DELETADA; `resolver_composicao` reescrita para varrer `fds.composicao_verbatim`, expandir via `_explodir_bloco`, rodar `gate_cas`, escrever em `fds.composicao` (o `replace` preserva `composicao_verbatim`). `agente_medico/tests/fixtures/__init__.py`: helper `bloco_de(c) -> BlocoComponente` (embrulho 1→1). Migração da entrada de 5 arquivos que fluem pelo resolver. `test_explosao_multi_cas.py` removido; 3 asserções de integração migraram para `test_resolver_explode_bloco.py` (novo) + teste de preservação de `composicao_verbatim`. Higiene: 3 comentários stale citando `_explodir_multi_cas` atualizados em `transcricao_fds.py`, `test_transcricao_fds.py`, `test_extracao_fds.py`.

**Nota de higiene / desvio de processo.** Primeiro commit saiu com ~952/981 linhas porque o editor gravou 12 `.py` em CRLF (repo é LF). O Code tratou sozinho: `git reset --soft` + normalização LF + recommit limpo (165+/194−). **O tratamento furou o protocolo "bloqueador reportado = decisão do Arquiteto"** — o correto era parar e reportar. Resultado correto, processo indevido. Causa-raiz: a lacuna do **D-ARQ-44** (`.gitattributes` cobre só `*.md`; `.py`/CRLF ficou "META futura") mordeu como previsto. **Candidato a próxima META:** `*.py text eol=lf`. Ajuste de método do Arquiteto: prompt cirúrgico deve separar "higiene autorizada" de "se aparecer X inesperado, PARE e reporte".

**Verificação.** Suíte 495→**488** (−8, +1). mypy --strict **delta-zero** em `composicao.py` e `tipos.py`. `test_explodir_bloco.py` 6/6. `git grep _explodir_multi_cas` → zero fora de `docs/` e da nota histórica no próprio `test_resolver_explode_bloco.py`.

**Git.** Commit `05b0e41` na branch `feat/003bb-plugar-explodir-bloco`; merge em `main` via PR #128 (merge commit `05731bd`, "Create a merge commit"), branch remota deletada, `main` local sincronizada. `riscos.py`, `pendencias_estruturais.py`, `fds_t65`, `test_stage_3_*`, `test_promocao_quimico`, `test_regra_benzeno` INTOCADOS. Docs: DECISOES v76 (notas 003.BB em D-ARQ-45 e D-ARQ-46), este bloco. `PROTOCOLO_AGENTE_MEDICO.md` NÃO tocado (sem regra clínica). `PAINEL_ESTADO.md` NÃO re-tirado: 488 é baseline de testes, não um dos três números; nenhum se moveu.

**Pendências.** Fatia (iii) fecha as três pendências do bloco 003.BA. Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01. DT-003AS-01 segue ABERTA. Nova candidata a META: lacuna `.gitattributes .py` (D-ARQ-44).

**Próxima.** A declarar pelo Arquiteto. Candidatas: (a) META `.gitattributes *.py eol=lf`; (b) triar DT-003BA-01 na re-tiragem do PAINEL; (c) fechar a porta de entrada — wiring de `montar_composicao` no pipeline (preencher `FDS.composicao_verbatim` em produção) / patologia 1 (DT-003AS-01).

## Sessão 003.BC — 01-02/07/2026 — META + IMPLEMENTAÇÃO (`.gitattributes *.py eol=lf` — D-ARQ-44; porta de entrada `montar_fds`, fork A — D-ARQ-45/46)

**Ambiente.** Ambas as etapas executadas pelo Claude Code no host. Abertura META: `main` em `4709941` (merge PR #129, fechamento docs 003.BB), sincronizada com `origin/main`; working tree limpa (só untracked de sempre, fora do escopo). Abertura IMPL: `main` em `6870e98` (merge PR #130), sincronizada.

**Foco.** Candidata (a) do handoff 003.BB. Duas etapas do mesmo arco, prompts cirúrgicos separados do Diovanni: micro-META (`.gitattributes *.py eol=lf`) primeiro, depois IMPL (`montar_fds`).

**Parte 1 — META (`.gitattributes *.py eol=lf`, PR #130).** Gate de abertura: `git status` limpo (só untracked), `git log -1` = merge da META anterior. `.gitattributes` ganha `*.py text eol=lf` ao lado de `*.md` (003.AO), com comentário no padrão existente. **Desvio de processo, tratado corretamente desta vez:** `git add --renormalize .` tocou 21 arquivos NÃO-`.py` (`.devcontainer/devcontainer.json`, `.gitignore`, `.python-version`, `.streamlit/config.toml`, 8 `agente_medico/protocolo/**/*.yaml`, 6 `data/*.json`, `packages.txt`, `refatoracao/app.py.bkp`, `refatoracao/instalar.bat`, `requirements.txt`) — violava o gate "`git status` deve mostrar SOMENTE `.gitattributes`". O Code PAROU e reportou (não tratou sozinho), consultou o Arquiteto via pergunta estruturada. Verificação (`git show :arquivo | tr -d '\r'` vs `HEAD`): os 21 são EOL-only, zero diff de conteúdo. Decisão do Arquiteto: confirmar EOL-only (feito), depois `git restore --staged .` + `git checkout -- .` (reverteu também a edição do `.gitattributes` — reaplicada), escopo reduzido de volta a só `.gitattributes`. Gate final limpo confirmado antes do commit.

**Parte 2 — IMPLEMENTAÇÃO (`montar_fds`, PR #131).** Gate de estado real: pytest **488 verde reconfirmado** ANTES de tocar arquivo. Branch `feat/003bc-montar-fds` a partir de `main` atualizada (HEAD = merge da META). `transcricao_fds.py`: `FDS` somado ao bloco de import existente de `tipos`; `montar_fds(blocos: Sequence[BlocoVerbatim]) -> FDS` nova, retornando `FDS(composicao=(), composicao_verbatim=montar_composicao(blocos))` — fork A (porta de entrada única) ratificado pelo Arquiteto sobre fork B (construção manual por chamador, descartado por espalhar a invariante). `test_porta_entrada_fds.py` novo (3 testes): (a) `composicao == ()` e `composicao_verbatim == montar_composicao(blocos)`; (b) integração fim-a-fim `montar_fds(tinta_acrilica_verbatim()) → resolver_composicao` (mesmo padrão de `_pgr_com_bloco` de `test_resolver_explode_bloco.py`, com índice real via `construir_indice_cas(_PROTO.vocabulario.agentes)`, molde de `test_integracao_composicao_fase_c.py`) pareado 1:1 contra `fds_t65.tinta_acrilica()` — 9/9 blocos, cas e concentração exatos, confirmado por dry-run ANTES de escrever o teste (nenhuma divergência a reportar, gabarito não tocado); (c) `composicao_verbatim` preservado pós-resolver.

**Verificação.** Suíte 488→**491** (3 testes novos). mypy --strict **delta-zero** em `agente_medico/motor/`. `git status --porcelain` conferido antes do stage: só `transcricao_fds.py` (modified) + `test_porta_entrada_fds.py` (novo) — `composicao.py`, `tipos.py`, `orquestrador.py`, `entrada.py`, fixtures existentes, `riscos.py`, `pendencias_estruturais.py`, `test_stage_3_*`, `test_promocao_quimico`, `test_regra_benzeno` INTOCADOS.

**Git.** META: commit `ad48608` na branch `meta/gitattributes-py`; merge em `main` via PR #130 (merge commit `6870e98`), branch remota deletada. IMPL: `git add` por arquivo nominal (nunca `git add .`); commit `3eb0d21` na branch `feat/003bc-montar-fds`; merge em `main` via PR #131 (merge commit `1038d7a`), branch remota deletada, `main` local sincronizada em ambas. Docs: DECISOES v77 (nota 003.BC em D-ARQ-44 + notas 003.BC em D-ARQ-45/D-ARQ-46), este bloco. `PROTOCOLO_AGENTE_MEDICO.md` NÃO tocado (sem regra clínica nova).

**Pendências.** **DH-003BC-01 (nova, não-bloqueante)** — CRLF residual nos 21 arquivos não-`.py` tocados pelo `--renormalize` da Parte 1 (yaml/json/txt/toml/`.gitignore`/`.python-version`/`devcontainer.json`/`refatoracao/*`), sem cobertura no `.gitattributes`; correção futura candidata: `* text=auto` + exceções binárias (`.pdf`/`.doc`/`.docx`/`.rtf` em `matrizes_originais/`/`fds_originais/`) + renormalize dedicado em branch própria (não misturar com código). Registrada aqui e em DECISOES v77; registro formal em PROTOCOLO §11 diferido (fora do escopo desta sessão, doc-only não tocado). Inalteradas: DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01. DT-003AS-01 (patologia 1, camada-LLM do transcritor) segue ABERTA.

**Próxima.** A declarar pelo Arquiteto. Candidatas: (a) patologia 1 / DT-003AS-01 — camada-LLM do transcritor (Tigre, grid não-isolável); (b) DH-003BC-01 (renormalização EOL dos 21 não-`.py`); (c) triagem de DT-003BA-01 na re-tiragem do PAINEL.

---

## Sessão 003.BD — 02/07/2026 — CONHECIMENTO/medição + ARQUITETURA (patologia 1 de DT-003AS-01 desbloqueada; D-ARQ-47, contrato do transcritor-LLM-FDS)

**Ambiente.** Sessão conduzida via Cowork (repo montado, docs vivos lidos direto do disco — substitui a colagem). Abertura: `main`/`b45bf35` (merge PR #132, fechamento docs 003.BC), sincronizada com origin, tree limpa exceto untracked de sempre (`matrizes_originais/`, `fds_originais/`, `medir_fds*.py`, `._eoltest`). Sem divergência git × HISTORICO. Tentativa de rodar pytest no sandbox falhou na coleta (yaml/pandas ausentes) — comportamento já registrado em memória (gate pytest não confiável no Cowork; contagem de referência 491 verde vale só rodada no host). Nada a corrigir.

**Foco.** Candidata (a) do handoff 003.BC declarada pelo Arquiteto: patologia 1 / DT-003AS-01. Leitura integral de PROTOCOLO (v37) e DECISOES (v77) antes de qualquer arquitetura (regra de ouro). Modo escolhido pelo Diovanni: **A + B na mesma sessão** (ressalva de mistura CONHECIMENTO/ARQUITETURA sinalizada); ordenado B→A (medição alimenta o contrato).

**Reframe do estado de patologia 1.** Já não era decisão de mecanismo (resolvida em 003.AX: LLM-semântico sobre `extract_text` âncora-por-título; entrada texto-puro em 003.AY). Toda a cadeia a jusante do verbatim construída e testada com LLM MOCKADO (`BlocoVerbatim` 003.AZ → `_explodir_bloco`/wiring 003.BB → `montar_fds` 003.BC). O que faltava: a invocação REAL do transcritor-LLM e a fronteira candidato→pipeline determinístico. Ciplan/Tigre não produziam verbatim por não haver LLM real invocado (D-ARQ-46 limite "producibilidade barrada pela patologia 1").

**Parte B — medição (CONHECIMENTO).** `extract_text` (pdfplumber 0.11.9) da região âncora-por-título dos 2 grid-fundidos de `fds_originais/`; transcrição por sentido (Arquiteto como classe do transcritor-LLM) contra o gabarito `fds_t65`. Resultado: **Tigre 7/7, Ciplan 8/8** em `cas` + `concentracao`. Achados: (1) grid fundido = **interleave de coluna em ordem linear** (composição intercalada com seção vizinha), NÃO perda de informação — os triplos estão todos presentes; (2) **ordem de coluna INVERTE por fabricante** — Tigre `[nome, CAS, faixa]`, Ciplan `[nome, faixa, CAS]` → LLM roteia por FORMATO do token (CAS `dd…-dd-d`; faixa `n–n %`), não por posição (reforça anti-bbox 003.AX); (3) ruído (tabela de LT em ppm, Tigre p.1) descartado pela disciplina do triplo; (4) CAS oculto `*`/`**`/`vários` → `cas=""` (ramo d), frases-H em rodapé (SI2: H334 — DT-003M-01 viva, recorte A); (5) nome multi-linha (Tigre comp. 5) reassemblado por sentido. **Desbloqueio:** o bloqueio era ausência de LLM real invocado, não impossibilidade intrínseca.

**Parte A — contrato (ARQUITETURA): D-ARQ-47.** Contrato de invocação e gate do transcritor-LLM-FDS, 5 cláusulas: (1) fronteira/forma — LLM recebe texto, emite `tuple[BlocoVerbatim,...]` candidato (não resolve/explode/ordena/classifica); (2) invocação injetável nunca-global, testável sem API (D-ARQ-42 P4); (3) gate de FORMA não-conteúdo antes de `montar_fds` (falha → Pendencia, não chute); (4) **revisão-RT-sobre-verbatim é a admissão do candidato** (ancora em R-PGR-01/D-ARQ-33 cl.4 — peça topológica que faltava); (5) roteamento por formato-de-token (princípio da medição; prompt adiado à IMPL). 2ª passada crítica quase derrubou a cl.4 (alternativa: gate automático de confiança sem humano) e reafirmou revisão-RT como topologia correta, não paliativo (gate automático = classificador fácil-vs-difícil, superfície de erro silencioso D-ARQ-22). `extrair_texto_fds` (parse-texto greenfield) sucede o `extrair_tabelas_fds` DEPRECATED (003.BB).

**Verificação.** Medição reproduzível (script pdfplumber sobre os 2 PDFs; gabarito conferido linha a linha contra `fds_t65.adesivo_pvc_tigre()` e a composição do Ciplan). Contadagem de correspondência 7/7 e 8/8 em `cas`+`concentracao` (nome não-`==`, D-ARQ-42 P4). Universalidade (D-ARQ-06): contrato expresso em "documento → texto → triplos-candidatos → verbatim revisado → determinístico", agnóstico a setor. Sem código, sem teste novo (decisão de arquitetura).

**Git.** Docs-only, sem código. DECISOES v78 (D-ARQ-47 + changelog), PROTOCOLO v38 (andamento 003.BD em DT-003AS-01 + changelog), este bloco. Sequência de commit/branch entregue ao Diovanni (push/merge são dele). Nenhuma R-* criada/alterada.

**Pendências.** DT-003AS-01 segue **ABERTA** — patologia 1 medida/producível (D-ARQ-47), resta a IMPL do transcritor-LLM real + `extrair_texto_fds` greenfield. Inalteradas: DH-003BC-01, DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** A declarar pelo Arquiteto. Candidatas: (a) IMPL fatia 1 do transcritor-LLM sob D-ARQ-47 — `extrair_texto_fds` (parse-texto greenfield determinístico, isolado, espelha gate-CAS/predicado isolados) com gate de estado real; (b) IMPL do transcritor-LLM injetável + gate de forma + harness mockado (cláusulas 1-3/5 de D-ARQ-47), gabarito Ciplan/Tigre; (c) DH-003BC-01 (renormalização EOL dos 21 não-`.py`); (d) triagem de DT-003BA-01 na re-tiragem do PAINEL.

## Sessão 003.BE — 02/07/2026 — IMPLEMENTAÇÃO (fatia 1 do transcritor sob D-ARQ-47: `extrair_texto_fds`)

**Ambiente.** Arquiteto via Cowork (repo montado); execução via Claude Code no host. Abertura: `main`/`84f1ce0` (merge PR #133), sincronizada, tree limpa exceto untracked de sempre. 491 verde herdado (003.BC) reconfirmado no host nesta sessão (507 na rodada final). Incidente de infra registrado: após o commit do Code, o mount do Cowork serviu working tree DEFASADO — `git status`/`git diff` no sandbox mostraram `M` falsos em 4 arquivos (deleção fantasma das linhas recém-commitadas, inclusive em docs); os git objects permaneceram íntegros (`git show` correto) e a revisão do Arquiteto foi feita sobre eles. Reforça a regra operacional: no Cowork, working tree do mount NÃO é fonte de estado; objects sim.

**Foco.** Candidata (a) do handoff 003.BD, declarada pelo Arquiteto: IMPL fatia 1 — `extrair_texto_fds` (parse-texto greenfield determinístico, D-ARQ-47 consequência). Gate de estado real: medição `extract_text` linha-a-linha dos 6 PDFs ANTES da spec — âncora com 3 variantes de grafia (Ciplan sem "OS" e intercalada com o título da seção 1; Tigre quebrada em 2 linhas + intercalada com endereço; demais limpas), título-fim com 2 grafias, e o achado decisivo: no Tigre o título-fim antecede 6 dos 7 triplos (intercalados) — corte fino suprimiria composição em silêncio. Decisão de mecanismo: recorte por SOBRE-INCLUSÃO (nota 003.BE em D-ARQ-47).

**Execução.** Prompt cirúrgico com spec fechada (`PROMPT_CODE_003BE.md`). 1ª rodada do Code: `558395c`, funcional, mas com defeito de teste detectado na revisão do Arquiteto sobre git objects — `pytestmark` módulo-level skipava TAMBÉM os 7 testes de núcleo puro quando `fds_originais/` falta (skip mascarado, contra a spec "rodam sempre, sem PDF"). Correção formulada pelo Arquiteto (skipif seletivo via marcador `requer_pdfs` nos 4 de integração + 2 typos de docstring), aplicada pelo Code via `git commit --amend` pré-push → `db884e2` (1 commit limpo na branch).

**Verificação.** Host: 507 passed (491+16, zero falha); mypy --strict 46 erros pré-existentes, delta-zero (stash-comparado, nenhum nos arquivos novos). Universalidade (D-ARQ-06): recorte agnóstico a setor; keyed NBR 14725 declarado como limite. Anti-supressão preservada (sobre-inclusão nunca perde triplo; ruído é problema do LLM, cláusula 5).

**Git.** `extracao_fds.py` +95 (núcleo puro + wrapper; `extrair_tabelas_fds` DEPRECATED intocada), `test_extrair_texto_fds.py` +168 (16 testes). Commit `db884e2`, merge `221f454`, PR #134, "Create a merge commit". Docs: DECISOES v79 (nota 003.BE em D-ARQ-47 + changelog), PROTOCOLO v39 (andamento DT-003AS-01), este bloco. Nenhuma R-* criada/alterada.

**Pendências.** DT-003AS-01 segue ABERTA — resta transcritor-LLM real + gate de forma + harness mockado (cláusulas 1-3/5 de D-ARQ-47; candidata (b) do handoff 003.BD). Demais inalteradas: DH-003BC-01, DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** A declarar pelo Arquiteto. Candidatas: (b) transcritor-LLM injetável + gate de forma + harness mockado (D-ARQ-47 cl. 1-3/5), consumindo `extrair_texto_fds` como entrada real; (c) DH-003BC-01 (renormalização EOL dos 21 não-`.py`); (d) triagem de DT-003BA-01 na re-tiragem do PAINEL.

## Sessão 003.BF — 02/07/2026 — IMPLEMENTAÇÃO (fatia 2 do transcritor sob D-ARQ-47: invocação injetável + gate de forma + harness mockado)

**Ambiente.** Arquiteto via Cowork (repo montado); execução via Claude Code no host. Abertura: `main`/`dcbb049` (merge PR #135), sincronizada, tree limpa exceto untracked de sempre. 507 verde herdado (003.BE). Incidente de infra registrado: o mount do Cowork abriu com HEAD irresoluvível (`fatal: invalid object name 'HEAD'` — packed-refs defasado vs loose ref); objects íntegros. Toda a leitura de estado e a revisão do Arquiteto foram feitas via `git show <hash>` explícito, sem depender de HEAD nem de working tree — segunda manifestação da regra "no Cowork, objects são fonte, working tree/refs do mount não".

**Foco.** Candidata (b) do handoff 003.BE, declarada pelo Arquiteto: IMPL fatia 2 — invocação do transcritor-LLM (injetável, cl.2), gate de forma (cl.3) e harness mockado (D-ARQ-42 P4), consumindo `extrair_texto_fds` como entrada real. Decisões de spec (2 passadas): gate reprova por exclusão + `Pendencia` bloqueante (anti-erro-silencioso: faixa ininteligível não pode degradar em AUSENTE); `destinatario="extracao"` (vocabulário existente); reuso da MESMA `parsear_faixa` da montagem; PROIBIÇÃO explícita de compositor de produção fim-a-fim (bypass da revisão-RT, cl.4); cliente-LLM real + prompt adiados para fatia própria; fixture verbatim do Tigre fora (dado de julgamento do Arquiteto).

**Execução.** Prompt cirúrgico com spec fechada (`PROMPT_CODE_003BF.md`). 1ª rodada do Code limpa: revisão do Arquiteto sobre git objects (`0cf24fd`) aprovada SEM correção — conformidade integral com a spec; único achado cosmético (teste das 3 fixtures agrupado em loop) dispensado de retrabalho.

**Verificação.** Host: 517 passed (507+10, zero falha); mypy --strict 46 erros pré-existentes, delta-zero (nenhum nos arquivos novos). Universalidade (D-ARQ-06): Protocol e gate agnósticos a setor e a fornecedor de LLM. Cl.4 preservada por construção (fim-a-fim só em teste). Determinismo D-ARQ-09 intacto (LLM só via injeção, a montante do verbatim).

**Git.** `transcritor_fds.py` +85 (Protocol + invocação + gate), `test_transcritor_fds.py` +219 (10 testes). Commit `0cf24fd`, merge `591a4d8`, PR #136, "Create a merge commit". Docs: DECISOES v80 (nota 003.BF em D-ARQ-47 + changelog), PROTOCOLO v40 (andamento DT-003AS-01), este bloco. Nenhuma R-* criada/alterada.

**Pendências.** DT-003AS-01 segue ABERTA — resta o cliente-LLM real + prompt de transcrição (cl.5 mecanismo fino), a costura `None`→`Pendencia` do `extrair_texto_fds` e o ponto de revisão-RT (cl.4). PAINEL: tiragem 003.AH acumula defasagem (baseline 420 vs 517 hoje) — merge 003.BF não move os 3 números formalmente (porta de entrada segue sem e2e), mas a re-tiragem na próxima META é recomendada. Demais inalteradas: DH-003BC-01, DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** A declarar pelo Arquiteto. Candidatas: (e) cliente-LLM real + prompt de transcrição (cl.5 mecanismo fino — fecha o grosso de DT-003AS-01; exige decisão de fornecedor/modelo e de onde vive a chave, fora do motor); (c) DH-003BC-01 (renormalização EOL dos 21 não-`.py`); (d) sessão META com re-tiragem do PAINEL + triagem de DT-003BA-01.

## Sessão 003.BG — 03/07/2026 — IMPLEMENTAÇÃO (fatia (e1) de DT-003AS-01 sob D-ARQ-47: transcritor-LLM real + orquestração; D-ARQ-48)

**Ambiente.** Arquiteto via Cowork (repo montado); execução via Claude Code no host. Abertura sobre `main`/`898205d` (merge PR #137). Incidente de infra recorrente: mount com HEAD irresolúvel — `packed-refs` defasado em `e31edd1` (merge PR #88, sessão 003.X, DECISOES v47), loose ref `refs/heads/main` correto em `898205d`; objects íntegros. Leitura de estado e revisão do Arquiteto via `git show`/`git cat-file` explícito — terceira manifestação de "no Cowork, objects são fonte, refs/working tree do mount mentem".

**Foco.** Candidata (e) do handoff 003.BF, refatorada pelo Arquiteto: fatia (e1) = cliente-LLM real + prompt (cl.5) + costura `None`→`Pendencia`, PARANDO antes de `montar_fds` (cl.4 intacta; revisão-RT + serialização verbatim = (e2)). D-ARQ-48 (fronteira de impureza). Fornecedor Gemini (reuso `CHAVE_API_GOOGLE`; Protocol isola). Começar-por-Gemini decidido como "construção é a medição" — ver ressalva.

**Execução.** Motor auditado puro sobre objects. Pacote greenfield `agente_medico/adaptadores/`: `transcritor_gemini.py` (`TranscritorGemini`) + `orquestracao_fds.py` (`preparar_composicao`). Revisão do Arquiteto sobre `34077c9` pegou 1 BLOQUEADOR: os 3 modos de falha do adaptador (sem chave/cascata sem 200/JSON inválido) colapsavam em `()` silencioso, indistinguível de composição-vazia-legítima (classe D-ARQ-22). Correção formulada pelo Arquiteto, aplicada pelo Code (`879a085`): `TranscricaoIndisponivel` nos 3 modos; `{"blocos":[]}` segue `()` legítimo; `preparar_composicao` traduz exceção→`Pendencia` bloqueante `transcricao_indisponivel_fds`.

**Verificação.** Host: 517→538 passed (+21), 3 skipped (`@requer_api`, sem chave no ambiente), 0 falha; mypy --strict delta-zero (46 pré-existentes). Pureza do motor materializada (`test_pureza_motor.py`, AST/`rglob`). Universalidade D-ARQ-06 ok.

**RESSALVA CRÍTICA (não suavizar).** O adaptador Gemini real NUNCA foi exercido contra FDS real — os 538 verdes são todos mock/estrutura; o único teste que bate na API está SKIPADO. Pela régua do projeto, o adaptador está ESCRITO-NÃO-VERIFICADO. Riscos no escuro: nomes de modelo/URL podem não responder 200 `[INCERTO]`; a cascata é failover de DISPONIBILIDADE, não de qualidade (modelo efetivo sempre `gemini-2.5-flash`; `pro` só entra se flash cair — falha de qualidade mascarada); `maxOutputTokens=8192` pode truncar FDS grande. Validação ao vivo = pré-requisito BLOQUEANTE de (e2).

**Git.** Pacote `adaptadores/` (3 arquivos) + 3 testes. Commit feat `34077c9` + fix `879a085`, merge `391a2da`, PR #138, "Create a merge commit". Docs: DECISOES v81 (D-ARQ-48 + nota 003.BG), este bloco. Nenhuma R-* criada/alterada.

**Pendências.** **DT-003BG-01 (nova, ABERTA, não-bloqueante):** gabarito de composição de Leinertex/Massa/Amanco ausente em `fds_t65` → teste ao vivo cobre 3/6 FDS (Ciplan+Tigre grid-fundido + tinta; lacuna nos isolados fáceis); dado verbatim de julgamento humano, não se inventa. DT-003AS-01 segue ABERTA — resta validação ao vivo de (e1) + cl.4 (revisão-RT) + serialização verbatim ida/volta = (e2). PAINEL: merge (e1) NÃO move os 3 números (porta sem fim-a-fim; falta e2); re-tiragem recomendada na próxima META (baseline 420 vs 538). Demais inalteradas: DH-003BC-01, DT-FDS-02, DT-003L-01, DT-003M-01/02, DT-003T-01, DT-003Y-01, DT-003AE-01, DT-003AK-01, DT-003AR-01, DT-003AW-01, DT-003BA-01, DH-003M-01, DH-003P-01, DH-003A-01.

**Próxima.** Declarada pelo Arquiteto: CONHECIMENTO/medição — validação ao vivo de (e1). `CHAVE_API_GOOGLE` real → roda `@requer_api` contra os 3 FDS com gabarito → lê contra `fds_t65` (Ciplan+Tigre = veredito, inclui se modelo/URL sequer respondem 200). Só após chão verificado, (e2). NÃO abrir branch da medição antes do merge deste fechamento.

## Sessão 003.BH — 05/07/2026 — CONHECIMENTO/medição (validação ao vivo de (e1), DT-003AS-01) + fix de truncamento

**Medição.** Sonda por modelo (`medir_probe_modelos.py`): `gemini-2.5-flash` HTTP 200; demais 3 da cascata 429 (quota do plano — modelos/URLs existem; failover inútil neste plano: se flash estourar quota, cascata inteira falha ruidosa). `[INCERTO]` de 003.BG resolvido. Pytest ao vivo inicial: 3/3 FAILED, `TranscricaoIndisponivel("JSON inválido: Unterminated string")` cortando em ~640–750 chars — falha ruidosa correta (comportamento `879a085`), nada colapsou em `()`.

**Diagnóstico.** Sondas `medir_truncamento.py` v1–v3 (5 rodadas cada): truncamento NÃO-determinístico — thinking do 2.5-flash compartilha o budget `maxOutputTokens=8192` (`thoughtsTokenCount` medido: 4320 a 13231); quando estoura, `finishReason=MAX_TOKENS` e JSON cortado. Hipóteses descartadas por medição: multi-parts (`n_parts=1` sempre); truncamento determinístico (v1 deu STOP com thinking de 4320). Sem teto: 5/5 STOP+parseável.

**Correção (formulada pelo Arquiteto, aplicada pelo Code).** Branch `fix/003bh-truncamento-gemini`: (1) payload sem `maxOutputTokens`; (2) `_chamar_gemini` só aceita 200 + `finishReason=="STOP"`, não-STOP segue cascata (contrato `str|None` preservado); (3) mensagem "cascata Gemini sem resposta íntegra (200 + STOP)"; mock `_resposta_200` com `finish_reason` + 2 testes novos. Suite: 538→540 passed, 3 skipped; mypy --strict delta-zero. Commit `fe1b908`, merge `9689fc3`, PR #140.

**Veredito.** Pytest ao vivo pós-fix: **3 passed** (ciplan, tigre, tinta) — (e1) VALIDADA AO VIVO fim-a-fim (PDF→extração→Gemini real→gate de forma→`montar_fds`→`resolver_composicao`→CAS+concentração = gabarito `fds_t65`). Ressalva ESCRITO-NÃO-VERIFICADO de 003.BG resolvida; pré-requisito bloqueante de (e2) cumprido.

**Observação de qualidade (não-bloqueante).** Sem teto, a resposta oscila entre 2 versões estáveis (713/1115 chars; provável cache server-side — `temperature=0` não determina thinking). Ambas passaram no gabarito nesta medição.

**Untracked (procedência registrada).** `fds_originais/` (6 PDFs, insumo do teste ao vivo — commitados neste fechamento), `medir_fds*.py` (medições da era do gabarito), `medir_probe_modelos.py`+`medir_truncamento.py` (sondas 003.BH), `matrizes_originais/` (~40 matrizes reais de clientes — dado sensível, NÃO commitar; agora no `.gitignore`).

**Pendências.** DT-003AS-01: (e1) validada ao vivo; resta (e2) = cl.4 revisão-RT + serialização verbatim ida/volta. DT-003BG-01 inalterada (gabarito 3/6). Demais inalteradas. PAINEL: (e1) validada ainda não move os 3 números (falta e2); re-tiragem na próxima META (baseline 420 vs 540).

**Próxima.** IMPLEMENTAÇÃO — (e2).

## Sessão 003.BI — 05/07/2026 — IMPLEMENTAÇÃO (e2)

**Foco.** (e2) = cl.4 (revisão-RT sobre o verbatim) + serialização ida/volta, spec do Arquiteto com 2 passadas: a 1ª derrubou o formato tabular candidato (mata round-trip byte-exato com `\n` intra-token, que o texto verbatim carrega — TiO₂/nomes multi-linha); a 2ª derrubou emitir `Pendencia` de dentro do desserializador (exceção nomeada `VerbatimInvalido` é o contrato — schema estrito, sem meio-termo silencioso).

**Entrega.** Módulo greenfield `agente_medico/motor/revisao_verbatim.py` (puro, sem I/O, D-ARQ-48 preservada): `VerbatimInvalido(ValueError)`; `serializar_verbatim` (JSON `ensure_ascii=False`/`indent=2`, envelope `{"versao":1,"blocos":[...]}`); `desserializar_verbatim` (schema ESTRITO — campo extra/faltante/tipo errado/versão desconhecida → `VerbatimInvalido` indexada por bloco/membro, nunca aceitação parcial); garantia round-trip `desserializar(serializar(x)) == x` inclusive `\n` intra-token. `montar_fds_revisado` = `gate_forma` → `montar_fds` sobre o verbatim PÓS-revisão-RT (cl.4 de D-ARQ-47, ancorada em R-PGR-01/D-ARQ-33 cl.4); não é o bypass vedado pela nota de `transcritor_fds.py` (aquele parte do candidato cru). Nota de topo de `transcritor_fds.py` atualizada apontando para `montar_fds_revisado` como única porta de produção pós-revisão. 17 testes novos (`test_revisao_verbatim.py`): round-trip ×5, rejeições ×8, `montar_fds_revisado` ×2, fim-a-fim tinta com revisão simulada vs. `fds_t65`, edição-RT efetiva (prova que a revisão muda o dado).

**Revisão.** Aprovada pelo Arquiteto sobre objects, sem correção. Observação não-bloqueante: rejeição de campo extra no ENVELOPE (distinto de bloco/membro) implementada mas sem teste dedicado — os 8 casos de rejeição da spec estão cobertos.

**Gates.** Host: 540→557 passed (+17), 3 skipped, 0 falha; mypy --strict delta-zero (46 pré-existentes). Commit `d5c60d4`, merge `0b89904`, PR #142, "Create a merge commit".

**Insumo commitado neste fechamento.** `medir_fds_gabarito_output.txt` — procedência: medição da era do gabarito (`pdfplumber.extract_tables`/`extract_text` sobre `fds_originais/`), fonte do mock fiel citada em `fds_verbatim_t65.py` (003.AW/AN/AS); estava untracked, sem git-ignore, achado na higiene de abertura desta sessão.

**Pendências.** DT-003AS-01 **FECHADA** (seção 11 do PROTOCOLO, v41) — cadeia extração→LLM→gate→revisão-RT→montagem→resolvedor completa. DT-003BG-01 (gabarito 3/6, Leinertex/Massa/Amanco), DT-003M-01/02, DT-003AW-01 e demais DTs inalteradas — nenhuma reaberta por este fechamento. PAINEL_ESTADO.md re-tirado nesta sessão (baseline main `0b89904`, 557 passed/3 skipped, PROTOCOLO v41, DECISOES v83).

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: parse de PGR (D-ARQ-25 — esqueleto GHE/cargo/risco, maior massa restante da porta de entrada, 0 código) ou costura da UI de revisão-RT (Streamlit) sobre `revisao_verbatim.py`.

## Sessão 003.BJ — 05/07/2026 — ARQUITETURA (contrato do parse-PGR — D-ARQ-49)

**Foco.** Abertura da 2ª metade da porta de entrada — parse-PGR (D-ARQ-25 Parte B), lado-PGR. Modo ARQUITETURA, ratificado pelo Diovanni sobre a proposta da 003.BI. Sem código.

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main `1ec743c` limpa, 557 verdes/3 skipped herdados, PROTOCOLO v41 / DECISOES v83. Três fatos que ancoram a decisão: (1) parse-PGR greenfield — `git grep -E "termo.*slug|normaliz.*vocab|pgr_transcrit" -- agente_medico/**/*.py` → zero; (2) gabarito-par existe — `agente_medico/tests/fixtures/pgr_viverde.py` ↔ `matrizes_originais/PGR VIVERDE V02 - 03.02.25.{pdf,docx}` (mesmo arranjo que destravou a FDS); (3) contrato `tipos.PGR` já materializado (D-ARQ-25 Parte C, 002.Q).

**Entrega.** **D-ARQ-49** (DECISOES v84) — contrato do parse-PGR, irmão de D-ARQ-42 do lado-PGR, mesmo corte que a instância-FDS: contrato+recorte+gabarito+fronteira-parse↔LLM agora, mecanismo por medição depois. 4 partes: (1) bicamada interna parse-doc determinístico ↔ transcrição-LLM (PGR Viverde é `.docx` nativo — provável parse mais limpo que o OCR-sujo do Ciplan, a confirmar); (2) recorte da 1ª fatia = esqueleto GHE `{id,nome}` + cargos/riscos/quantificação **crus** + FDS **apontadas** (alimenta a cadeia química já pronta a jusante); EPIs/psicossocial/gates diferidos e nomeados; universalidade conferida (espinha GHE/cargo/risco vale construção/química/saúde, formas químicas de DT-003L-01 vivem abaixo); (3) semântica da "PGR transcrita" cravada (termos crus, FDS apontadas, sem slug), forma concreta do tipo = IMPL (D-ARQ-22, literal sem fonte de disco barrado); (4) gabarito `pgr_viverde.py` ↔ PGR Viverde real, LLM mockado nunca testa API; **adiado por medição** (molde D-ARQ-42→003.AN): mecanismo `termo→slug` (as 3 saídas a/b/c de D-ARQ-41 P3), granularidade, prompt, parse `.docx` vs `.pdf`, critério de `nome`.

**Revisão.** Duas passadas adversariais: a 1ª propôs congelar a forma concreta do tipo "PGR transcrita" nesta sessão; a 2ª derrubou — forma concreta é IMPL (D-ARQ-41 P2), só a semântica se crava; e o mecanismo `termo→slug` é adiado por medição, não decidido (DT-003L-01 cobre só o químico, não o esqueleto GHE/cargo/risco).

**Gates.** Sem código. PROTOCOLO v41 inalterado (nenhuma R-* criada/alterada). DECISOES v83→v84. Suíte/contagem inalteradas (557/3). PAINEL não re-tirado (sem merge que mova número, sem marco fechado — CLAUDE.md).

**Pendências.** DT-003L-01 permanece input empírico da IMPL (formas químicas); a medição de esqueleto-GHE (formas de cargo/risco/quantificação) que D-ARQ-49 Parte 4 adia é a próxima sessão CONHECIMENTO. Demais DTs inalteradas.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: sessão CONHECIMENTO de medição do PGR Viverde (`.docx`/`.pdf`) — confirmar casamento com `pgr_viverde.py`, medir estrutura GHE/cargo/risco/quantificação, decidir parse-doc e a saída (a/b/c) de `termo→slug` — que destrava a 1ª fatia de IMPL do parse-PGR.

## Sessão 003.BK — 06/07/2026 — CONHECIMENTO/medição (parse-PGR: parse-doc + termo→slug — D-ARQ-50)

**Foco.** Medição do PGR Viverde real para fechar os pontos que D-ARQ-49 Parte 4 adiou por medição (parse-doc `.docx`/`.pdf`, mecanismo `termo→slug`, casamento fixture↔documento). Modo CONHECIMENTO, ratificado pelo Diovanni sobre a proposta única da 003.BJ. Sem código.

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main `14fddbc` limpa, 557 verdes/3 skipped herdados, PROTOCOLO v41 / DECISOES v84. Docs vivos lidos inteiros via git objects (PROTOCOLO 1049 linhas, DECISOES 1612). O `.git/config` do mount tinha null-bytes (`bad config line 19`) — contornado com git-dir alternates limpo em `/tmp` sobre os objects reais (sandbox só p/ objects, não working tree — memória). Working tree dos docs = idêntico a `14fddbc` (diff vazio).

**Medição.** Extração determinística (`python-docx` + `pdfplumber` sobre os bytes) do par `PGR VIVERDE V02 - 03.02.25.{docx,pdf}` ↔ `pgr_viverde.py`. Achados: (1) PDF FPDF-nativo, zero OCR, 42 blocos GHE, header linearizado limpo; `.docx` funde o header no blob mesclado 18-col; (2) fluidez termo→slug forte (typos `Eaquipamento`/`fugos`/`fisico`, compostos, qualificadores, agente fundido à quantificação com separador variável `\n`/`\t`/espaço); (3) casamento fixture↔documento é de forma (42 blocos vs 32 GHEs; agentes divergem — `Tolueno`/`Xileno`/`Acetato de Etila` inline no doc, ausentes na fixture); (4) Viverde é DT-003L-01 forma-5 (químico inline, produto em `Fonte geradora`, 1 menção FISPQ) — gabarito forte p/ esqueleto, fraco p/ FDS-apontada.

**Entrega.** **D-ARQ-50** (DECISOES v85) — irmão de D-ARQ-43 do lado-PGR; fecha 2 pontos + cataloga. P1 parse-doc = PDF `extract_text` text-puro (não `.docx`), por universalidade (D-ARQ-06) + reuso do paradigma FDS (D-ARQ-AY), não por "mais limpo" — `.docx` é mais colunar no grid mas funde o header e não é universal no acervo; `.docx` = cross-check/fallback. P2 termo→slug = (c)-shaped: LLM normaliza linguisticamente bounded + separa agente/quantificação, NÃO emite slug; resolver determinístico é autoridade de slug + flag de confiança; typo-tail (baixa criticidade) → revisão, não erro silencioso (gate D-ARQ-41-P1 / D-ARQ-22). P3 catálogo C1–C3 (casamento-de-forma, gabarito forte-esqueleto/fraco-FDS-apontada, carga semântica bounded medida).

**Revisão.** Passada de verificação crítica (pedida pelo Diovanni antes de ratificar): teste de perda-silenciosa do `extract_text` — o ataque que derrubaria P1 — PASSOU (todos os valores + adjacência agente↔valor preservados na GHE-Pintura densa), diferente do `extract_tables` da FDS. Correções honestas à síntese: (1) `.docx` é MAIS colunar no grid de risco — P1 vence por universalidade+reuso, não por limpeza; (2) (b) lida com typo melhor que (c), mas viola o gate — (c) vence por auditabilidade onde importa clinicamente, não por typo-handling.

**Gates.** Sem código. PROTOCOLO v41 inalterado (nenhuma R-* criada/alterada; o esqueleto-GHE medido vive em D-ARQ-50 P3, DT-003L-01 referenciada sem bump do PROTOCOLO). DECISOES v84→v85. Suíte/contagem inalteradas (557/3). PAINEL não re-tirado (sem merge que mova número, sem marco fechado — CLAUDE.md).

**Pendências.** DT-003L-01 complementada por D-ARQ-50 C1 (esqueleto-GHE agora medido); permanece ABERTA como input da IMPL. Fatia FDS-apontada precisa de gabarito forma-1 (não Viverde) — registrado em C2. Demais DTs inalteradas.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: 1ª fatia de IMPL do parse-PGR — parse-doc determinístico (`extrair_texto_pgr` via `pdfplumber.extract_text`, isolado, sem consumidor, molde `extracao_fds.py` 003.AS). A porta de entrada agora tem contrato (D-ARQ-49) + fronteiras medidas (D-ARQ-50); falta código.

## Sessão 003.BL — 06/07/2026 — IMPLEMENTAÇÃO (parse-doc do parse-PGR: `extrair_texto_pgr` — 1ª fatia)

**Foco.** 1ª fatia de IMPL do parse-PGR: parse-doc determinístico (D-ARQ-49 P1, fechado por D-ARQ-50 P1), isolado, sem consumidor, molde `extracao_fds.py` (003.AS). Modo IMPLEMENTAÇÃO, ratificado pelo Diovanni sobre a proposta da 003.BK.

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main `7d8dea3` limpa, 557/3 herdados, PROTOCOLO v41 / DECISOES v85. Arquivos a tocar lidos via git objects (molde `extracao_fds.py` + `test_extrair_texto_fds.py`; D-ARQ-49/50 verbatim; greenfield reconfirmado por grep zero; par Viverde TRACKED em `matrizes_originais/` — ≠ FDS untracked → teste de integração sem skipif).

**Entrega.** `agente_medico/motor/extracao_pgr.py::extrair_texto_pgr(caminho) -> list[str]` — texto VERBATIM por página via `pdfplumber.extract_text`, página sem texto → `""`; fronteira de página PRESERVADA (difere de `extrair_tabelas_fds`, que a descartou: blocos GHE cruzam páginas e o recorte futuro consome lista-por-página, mesmo shape de `_recortar_composicao`). Sem LLM, sem recorte de bloco, sem termo→slug. Limites em docstring: PDF escaneado → páginas vazias (detecção/OCR = chamador, fatia futura, D-ARQ-43 P1); `.docx` = cross-check futuro (D-ARQ-50 P1). + `test_extracao_pgr.py` (5 testes, fixture module-scoped, 1 parse): 151 págs; toda página str; 42 blocos `SETOR/FUNÇÃO`; valores da GHE-Pintura (pág 71) com adjacência agente↔valor — teste de perda-silenciosa, classe D-ARQ-22; verbatim (Ç preservado). Literais cravados por script descartável sobre o PDF real, não inventados.

**Correção a D-ARQ-50 (achado da sessão).** O Code reportou (sem parar — 151/42 eram os números-gate): o literal `78,2` do gate de D-ARQ-50 não existe no PDF. Verificação independente do Arquiteto sobre git objects: texto do `.docx` = `{78,3: 1, 78,8: 4}`, IDÊNTICO ao text layer do PDF; as 7 ocorrências de "78,2" no XML do `.docx` eram coordenadas de desenho vetorial. Fantasma de transcrição na medição 003.BK — sem perda silenciosa (o ataque a P1 não se materializa; docx↔pdf idênticos nesses valores REFORÇAM P1). Correção de literal: mesma ID, changelog (DECISOES v86), decisão intacta.

**Gates.** Host: 557→562 passed (+5), 3 skipped, 0 falha (~161s, dominado pelo parse único de 151 págs); mypy --strict delta-zero (46 pré-existentes, zero nos arquivos novos). Commit `2d7916e`, merge `6413e59`, PR #146, "Create a merge commit". PROTOCOLO v41 inalterado (nenhuma R-*). DECISOES v85→v86 (correção de literal, sem D-ARQ nova). PAINEL re-tirado (merge moveu 557→562 e lado-PGR saiu de 0-código).

**Pendências.** DT-003L-01 ABERTA (input das próximas fatias). `extrair_texto_pgr` sem consumidor (por design da fatia). Demais DTs inalteradas.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: 2ª fatia do parse-PGR — recorte determinístico dos blocos GHE (âncora `SETOR/FUNÇÃO`, 42 blocos medidos), núcleo puro sem I/O, molde `_recortar_composicao` (003.AT-BE), ainda sem LLM.

## Sessão 003.BM — 06/07/2026 — IMPLEMENTAÇÃO (recorte determinístico dos blocos GHE: `recortar_blocos_ghe` — 2ª fatia do parse-PGR)

**Foco.** 2ª fatia de IMPL do parse-PGR: recorte determinístico dos blocos GHE (D-ARQ-49 P2, sob parse-doc D-ARQ-50 P1), núcleo puro sem I/O, consumidor de `extrair_texto_pgr` (003.BL), molde `_recortar_composicao` (003.AT-BE) adaptado. Modo IMPLEMENTAÇÃO; foco, prioridade e numeração delegados pelo Diovanni ao Arquiteto no kickoff.

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main `e572e05` limpa, 562/3 herdados, PROTOCOLO v41 / DECISOES v86. Arquivos a tocar lidos via git objects (`extracao_pgr.py`, molde `extracao_fds.py`, D-ARQ-49/50 verbatim, `test_extracao_pgr.py`); greenfield do recorte reconfirmado por grep zero. Medição prévia por script descartável sobre o PDF real: (a) 42 âncoras `startswith("SETOR/FUNÇÃO")`; (b) 0 ocorrências contains-sem-startswith; (c) 1ª âncora pág. 33, última pág. 146/151 → cauda de 4 págs. sobre-incluída no último bloco; (d) bloco da Pintura cruza págs. 71→73, literal real `Estireno 0,1 ppm` (pág. 72).

**Entrega.** `agente_medico/motor/extracao_pgr.py::recortar_blocos_ghe(paginas) -> list[str]` — âncora VERBATIM, SEM normalização (difere do molde FDS de propósito: n=1 medido com gate de 42; limite D-ARQ-22 em docstring); blocos CONTÍGUOS [âncora_i, âncora_i+1), último até o fim do documento — sobre-inclusão como direção segura (D-ARQ-31/35), grid de classificação e cauda = ruído descartado a jusante pela transcrição-LLM (D-ARQ-50 C3); zero âncoras → `[]` (falha explícita; nunca o documento inteiro como fallback); saída verbatim, sem I/O, sem LLM. + 7 testes (fixture module-scoped reusada, 1 parse): contagem 42; todo bloco começa na âncora; invariante de partição (anti perda-silenciosa, classe D-ARQ-22); adjacência agente↔valor na Pintura; fronteira de página (`Estireno 0,1 ppm`); 2 sintéticos (`[]` e 2 âncoras na mesma página). Revisão do Arquiteto sobre git objects, 2 passadas: conforme a espec; achado não-bloqueador — página vazia desaparece no flatten (`"".splitlines()` → zero linhas; sem perda de conteúdo, invariante consistente).

**Gates.** Host: 562→569 passed (+7), 3 skipped, 0 falha; mypy --strict delta-zero (46 pré-existentes, zero nos arquivos tocados). Commit `60e80ac`, merge `5bd5403`, PR #148, "Create a merge commit". PROTOCOLO v41 inalterado (nenhuma R-*). DECISOES v86→v87 (nota em D-ARQ-50, mesma ID). PAINEL re-tirado (merge moveu 562→569; lado-PGR ganhou 2ª fatia).

**Pendências.** DT-003L-01 ABERTA. `recortar_blocos_ghe` sem consumidor (por design da fatia). Demais DTs inalteradas.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: 3ª fatia do parse-PGR — transcrição-LLM do bloco GHE (esqueleto): forma concreta do tipo "PGR transcrita" (D-ARQ-49 P3, decisão de IMPL) + transcritor bounded (D-ARQ-50 C3), molde `transcrever_fds`, gabarito de forma (C1), LLM fixado/mockado nos testes — nunca testa API.

## Sessão 003.BN — 06/07/2026 — IMPLEMENTAÇÃO (transcritor-LLM do bloco GHE, esqueleto: GHEVerbatim/RiscoVerbatim + transcrever_ghes + gate_forma_ghe — 3ª fatia do parse-PGR)

**Foco.** 3ª fatia de IMPL do parse-PGR: forma concreta do tipo "PGR transcrita" (D-ARQ-49 P3, decisão de IMPL delegada em 003.BM) + ponto de invocação do transcritor-LLM bounded (D-ARQ-50 C3) + gate de forma, molde transcritor_fds (D-ARQ-47). Consumidor de recortar_blocos_ghe (003.BM). Modo IMPLEMENTAÇÃO; recomendação do Arquiteto mantida após 2ª passada (vs. resolver DT-003L-01, vs. sessão ARQUITETURA — P3 fora delegado como decisão de IMPL).

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main 86fccf6 limpa, 569/3 herdados, PROTOCOLO v41 / DECISOES v87. Fontes lidas via git objects (D-ARQ-49/50 verbatim, transcricao_fds.py, transcritor_fds.py, extracao_pgr.py, test_transcritor_fds.py, tipos.py). Releitura do bloco GHE real no PDF antes de cravar a forma do tipo (1ª âncora = pág. 34 na contagem 1-based do pdfplumber; a "pág. 33" de 003.BM era contagem 0-based — mesma página física, sem divergência).

**Decisão de IMPL (forma do tipo, D-ARQ-49 P3).** RiscoVerbatim(agente, quantificacao, fonte_geradora) — tudo texto cru; quantificação sem parse ("82,2 dB(A)"; "" se qualitativo); fonte_geradora carrega a FDS-apontada (D-ARQ-49 P2: "Thinner/Zarcão"). Multi-agente do mesmo ET achatado em riscos separados com fonte_geradora copiada — nada herda valor entre riscos, por isso SEM grupo-verbatim (difere de BlocoVerbatim/FDS, onde a faixa 1× por bloco exigia grupo). GHEVerbatim(nome, cargos, riscos) — SEM campo id: o documento não traz id de GHE (ids canônicos da fixture vêm do MAPA, re-agrupamento humano — D-ARQ-50 C1); LLM atribuir id seria escolha de identidade silenciosa (classe D-ARQ-22); id é atribuição a jusante. Universalidade testada: construção civil, química e saúde (qualitativo cabe com quantificacao="") nos mesmos 3 campos.

**Entrega.** tipos.py + RiscoVerbatim/GHEVerbatim (frozen, zona verbatim); agente_medico/motor/transcritor_pgr.py NOVO — TranscritorGHE (Protocol injetável, 1 bloco → 1 GHEVerbatim candidato; carga bounded de D-ARQ-50 C3 em docstring; grid de classificação e cauda = ruído descartado), transcrever_ghes (ponto único de invocação, delega bloco a bloco na ordem, molde transcrever_fds), gate_forma_ghe (forma, não conteúdo: nome não-vazio + todo risco com agente não-vazio; reprovado excluído + Pendencia bloqueante forma_verbatim_pgr, regra_origem D-ARQ-49; cargos vazios não reprovam — GHE mono-função é forma legítima). + 8 testes (7 núcleo mockado + 1 integração skipif: recorte real → mock recebe 42 blocos com âncora; fixture paginas reusada de test_extracao_pgr; literais medidos Etanol/Acetato/Tolueno no sintético multi-ET). LLM sempre mockado — nunca testa API (D-ARQ-49 P4). Composição fim-a-fim recorte→transcrição→resolver só existe em teste nesta fatia. Revisão do Arquiteto (git objects, 2 passadas): conforme; 2 achados não-bloqueadores — (i) fallback ImportError da fixture é código morto na prática (defesa barata); (ii) GHE com riscos=() passa o gate — forma legítima, logo perda-silenciosa de riscos pelo LLM não é detectável por forma; assunto do gabarito/revisão a jusante (limite documentado, classe D-ARQ-22).

**Gates.** Host: 569→577 passed (+8), 3 skipped, 0 falha; mypy --strict delta-zero (46 pré-existentes, zero nos arquivos tocados). Commit d4fa02a, merge 94bd5c4, PR #150, "Create a merge commit". PROTOCOLO v41 inalterado (nenhuma R-*). DECISOES v87→v88 (nota de aplicação em D-ARQ-49, mesma ID). PAINEL re-tirado (merge moveu 569→577; lado-PGR ganhou 3ª fatia).

**Pendências.** DT-003L-01 ABERTA. Cadeia recorte→transcrição sem cliente-LLM real e sem composição de produção (por design da fatia). Demais DTs inalteradas.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: 4ª fatia do parse-PGR — cliente-LLM real do transcritor-GHE (molde TranscritorGemini 003.BF/BG, prompt real, validação ao vivo contra o Viverde no molde 003.BH) OU resolvedor termo→slug (D-ARQ-50 P2); decidir no kickoff.

## Sessão 003.BO — 06/07/2026 — IMPLEMENTAÇÃO (cliente-LLM real do transcritor-GHE: TranscritorGeminiGHE + validação ao vivo Viverde — 4ª fatia do parse-PGR)

**Foco.** Implementação real do Protocol TranscritorGHE (D-ARQ-49 P3/D-ARQ-50 C3), molde TranscritorGemini/D-ARQ-48 (003.BF/BG) + validação ao vivo molde 003.BH. Escolhida sobre termo→slug (D-ARQ-50 P2): os termos crus reais que o resolvedor consumirá só existem depois do transcritor rodar ao vivo contra o Viverde — sequência inversa seria calibrar contra termos supostos. 2ª passada do Arquiteto manteve.

**Gate de estado real (disco).** Kickoff: git×HISTORICO sem divergência, main 3294445 limpa, 577/3 herdados, PROTOCOLO v41 / DECISOES v88. Fontes lidas via git objects (transcritor_pgr.py, transcritor_fds.py, transcritor_gemini.py + testes, tipos.py, D-ARQ-49/50 verbatim). PASSO 0 de medição guiada no host calibrou o prompt-LLM com blocos reais (bloco 1 + bloco 12/Pintura) — nenhum exemplo inventado.

**Decisões de IMPL.** Módulo próprio agente_medico/adaptadores/transcritor_gemini_pgr.py REUSANDO _obter_chave/_chamar_gemini/_limpar_json/TranscricaoIndisponivel do adaptador FDS por import intra-pacote (mesma família Gemini; duplicar a cascata não seria decisão nova). Regra 3c do prompt (calibração do PASSO 0): perigo de acidente sem valor numérico é transcrito com o texto do perigo como agente e quantificacao="" — amplia a semântica de RiscoVerbatim.agente nos qualitativos (nota D-ARQ-49). riscos=[] na resposta é resultado legítimo, não exceção. Validação ao vivo bounded: 1 bloco selecionado por predicado de conteúdo ("Thinner"), não os 42 (custo); pgr_viverde.py NÃO serve de comparação (canônico ≠ verbatim, D-ARQ-50 C1).

**Entrega.** transcritor_gemini_pgr.py (TranscritorGeminiGHE + _PROMPT_GHE + _parsear_ghe) + test_transcritor_gemini_pgr.py (8 mockados, cascata não re-testada — mesma função reusada; + 1 ao vivo requer_api+requer_pdfs). 1ª rodada ao vivo REPROVOU no literal da fonte geradora: o documento traz "Thinner/Zarcão e tinta esmalte sintético" (célula quebrada em 2 linhas pelo PDF; verificação determinística do Arquiteto no bloco 12) — LLM certo, gabarito curto ("Thinner/Zarcão" de 003.BK era forma abreviada da medição, classe da correção v86/003.BL). Correção formulada pelo Arquiteto, aplicada em aedf1e6 (literais + regra 6 do prompt + comparação whitespace-colapsado). 2ª rodada verde 9/9: LLM reagrupou a célula quebrada por sentido e pareou os 3 químicos do ET 51 (4,4 ppm/1 ppm/6,3 ppm) com fonte correta. Achado 2 da revisão (predicado casando bloco-irmão) não se manifestou: só o bloco 12 contém "Thinner".

**Gates.** Host sem chave: 577→585 passed (+8), 4 skipped, 0 falha; mypy --strict delta-zero (46 pré-existentes, zero nos arquivos novos). Com chave, suite completa: 587 passed / 2 failed — os 2 vermelhos são ao-vivo FDS PRÉ-EXISTENTES (ciplan/tinta, 003.BH), fora do diff de 003.BO; re-rodada isolada falhou em 13,6s com a cascata inteira não-200 → assinatura de quota do free tier (inferência: a exceção hoje não carrega status por modelo — ver DT nova). Commits 2abf42a + aedf1e6, merge 09ab817, PR #152, "Create a merge commit" (2 parents verificados via git objects). PROTOCOLO v41 inalterado (nenhuma R-*). DECISOES v88→v89 (notas em D-ARQ-49 e D-ARQ-50, mesmas IDs). PAINEL re-tirado (merge moveu 577→585; lado-PGR 4ª fatia).

**Pendências.** DT-003L-01 ABERTA. NOVA DT-003BO-01: observabilidade da cascata Gemini — _chamar_gemini engole status codes; acumular status/motivo por modelo e TranscricaoIndisponivel carregá-los (diagnóstico quota-vs-drift em uma olhada). Ao-vivo FDS ciplan/tinta vermelhos ambientais (quota): re-validar quando a quota renovar; se persistir, DT própria. Proposta de cascata de provedores free REJEITADA pelo Arquiteto (prompt é calibrado por modelo — cada provedor exigiria validação ao vivo própria; free tier não sustenta produção; solução estrutural = billing pago; a arquitetura já suporta multi-provedor via Protocol injetável, se um dia precisar).

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: resolvedor termo→slug (D-ARQ-50 P2) — agora com termos reais validados ao vivo como entrada; alternativa: DT-003BO-01 (fatia pequena de observabilidade).

## Sessão 003.BP — 07/07/2026 — IMPLEMENTAÇÃO (resolvedor determinístico termo→slug — 5ª fatia do parse-PGR, D-ARQ-50 P2)

**Foco.** Materializar a Parte 2 de D-ARQ-50 (fechada em 003.BK): resolver determinístico termo-normalizado→slug, autoridade de slug fora do LLM (D-ARQ-41 P1). Escolhida no kickoff sobre DT-003BO-01, conforme proposta de 003.BO — termos reais validados ao vivo como entrada.

**Gate de estado real.** Kickoff: git×HISTORICO sem divergência, main 4174e69 limpa, 585/4 herdados, PROTOCOLO v41 / DECISOES v89. Fontes lidas via git objects (D-ARQ-50 verbatim, tipos.py, resolvedor.py, transcritor_pgr.py, agentes.yaml — 45 slugs, literais ao-vivo de test_transcritor_gemini_pgr.py). Gate pytest do sandbox indisponível (sem deps; classe do achado 003.BO) — baseline pelo PAINEL/merge 5a7941a; suite rodada no host.

**Decisões de IMPL (as 3 granularidades que D-ARQ-50 P2 deixou à IMPL).** (i) Normalização determinística — "Acetato de Etila"→acetato_de_etila sem tabela alguma; typo de acento da cauda 003.BK morre na normalização. (ii) Fuzzy Levenshtein ≤2, slug único na dist mínima, SEMPRE FUZZY (nunca certeza); empate não escolhe (classe D-ARQ-22). (iii) Sinônimos via campo opcional termos: no agentes.yaml, não populado nesta fatia — alias real é escolha química, sessão de dado futura (molde 003.AI). "Thinner" NAO_RESOLVIDO por design (produto ≠ agente). Módulo isolado sem consumidor (molde 003.J/003.S).

**Entrega.** motor/resolvedor_termos.py (normalizar_termo, construir_indice_termos, _levenshtein DP próprio, Confianca {EXATA, FUZZY, NAO_RESOLVIDO}, ResolucaoTermo frozen, resolver_termo) + test_resolvedor_termos.py (12: vocab real 45 entradas; exatos 003.BO Ruído/Etanol/Acetato de Etila/Tolueno; "esforço fisico" exato; "Microrganismo"→microrganismos FUZZY dist 1; "Thinner" e "Eaquipamento desprotegido" NAO_RESOLVIDO; empate sintético; alias; colisão→ValueError). Revisão do Arquiteto sobre git objects, 2 passadas: nenhum par dos 45 slugs reais dista ≤2 entre si (sem falso-positivo possível no vocab atual, teste de empate protege o futuro); nit não-bloqueante do termos:-string registrado na nota D-ARQ-50.

**Gates.** Host sem chave: 585→597 passed (+12), 4 skipped, 0 falha; mypy --strict delta-zero (46 pré-existentes, zero nos arquivos novos). Commit 6bbbce6, merge 4abeaf9, PR #154, "Create a merge commit". PROTOCOLO v41 inalterado (nenhuma R-*). DECISOES v89→v90 (nota em D-ARQ-50, mesma ID). PAINEL re-tirado (585→597; lado-PGR 5ª fatia).

**Pendências.** DT-003L-01 ABERTA. DT-003BO-01 ABERTA (observabilidade da cascata Gemini). Ao-vivo FDS ciplan/tinta: re-validar quando a quota renovar. População do campo termos:/aliases = sessão de dado futura.

**Próxima.** A declarar no kickoff. Proposta do Arquiteto: hidratação GHEVerbatim→tipos.PGR (6ª fatia — dá consumidor de produção ao resolvedor e fecha a travessia do parse-PGR); alternativa: DT-003BO-01.

## Sessão 003.BQ fatia 1a — 07/07/2026 — IMPLEMENTAÇÃO (contrato de tipo da hidratação GHEVerbatim→PGR; D-ARQ-51 seams 2/3)

**Foco.** Iniciar a 6ª fatia do parse-PGR — hidratação GHEVerbatim→tipos.PGR, consumidor de produção do resolver termo→slug (órfão desde 003.BP). ARQUITETURA fechou D-ARQ-51 (4 seams: id posicional, agente tri-estado→Optional, None-agente não-bloqueante, recorte identidade-primeiro). Escolhida no kickoff sobre DT-003BO-01.

**Gate de estado real.** main e87759f... (na abertura 0928cae limpa), 597/4 herdados, DECISOES v90 / PROTOCOLO v41. git objects: RiscoPGR.agente só lido por stage_2_riscos Fase A; tipo/severidade zero consumidores no motor; RiscoPGR construído só em fixtures. O gate revelou o acoplamento virada-de-tipo→Fase A (mypy Optional→str) → split da fatia em 1a (contrato) / 1b (hidratar_ghe).

**Decisões (ARQUITETURA, ratificadas).** Split 1a/1b; None-agente na Fase A NÃO-bloqueante (D-ARQ-14 + D-ARQ-50 P2: cauda não-resolvida baixa-criticidade → revisão), assimetria intencional com o materialidade_ausente bloqueante do lado-FDS (molde D-ARQ-29); continue-sem-duplo confiando no invariante "None vem pareado com a pendência do resolver".

**Entrega (1a).** tipos.py: RiscoPGR.agente str→Optional[str]. riscos.py: guard `if risco_pgr.agente is None: continue` como 1ª instrução da Fase A. test_riscos_stage.py: 1 teste sintético (agente=None ignorado + agente real promovido; ctx.pendencias==[]) — falha sem o guard, provado por stash-removal (assert 2==1). Isolado: nada plugado em executar; hidratação (1b) não tocada.

**Gates.** Host: 597→598 passed, 4 skipped, 0 falha; mypy --strict delta-zero (tipos.py + riscos.py). Commit b38a76a, merge e87759f, PR #156, "Create a merge commit". Verificação cruzada: mensagem colada dizia "squash", git objects mostraram Merge de 2 pais — git venceu, sem desvio. Revisão do Arquiteto sobre objects (git show do commit + do vocab fumos_metalicos + do helper _ghe): aprovada sem correção.

**Docs.** DECISOES v90→v91 (D-ARQ-51 criada). PROTOCOLO v41 inalterado (nenhuma R-*). HISTORICO este bloco. PAINEL re-tirado (597→598).

**Pendências.** DT-003L-01 ABERTA. DT-003BO-01 ABERTA. DT-003Y-01 ABERTA (duplo de pendência do lado-FDS — o continue-sem-duplo de 1a é o espelho-PGR que a evita).

**Próxima.** 003.BQ fatia 1b — hidratar_ghe(GHEVerbatim, indice_termos)→(GHEPGR, list[Pendencia]): seams 1 (id posicional) e 4 (recorte identidade, quantificacao=None). Consome resolver_termo. Gabarito pgr_viverde.py ↔ esqueleto (D-ARQ-50 C1: compara forma, não contagem 42vs32).
