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

*Entradas futuras abaixo desta linha*
