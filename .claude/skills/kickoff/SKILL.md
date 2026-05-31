---
name: kickoff
description: Coletor de estado de abertura de sessão (git + fim do HISTORICO). Reporta verbatim; não decide foco nem calcula numeração. Invocação manual.
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git status *) Read
---

# /kickoff — coletor de estado de abertura

Coleta e **reporta** estado factual. Não decide foco/prioridade/recorte, não calcula o número da próxima sessão, não cria branch, não escreve arquivo, não lê docs da raiz (cópias-fantasma) — só `docs/`.

## Coleta (rodar e reportar verbatim)
1. `git log --oneline -10` e `git status`.
2. Fim de `docs/HISTORICO_OPERACIONAL.md`: ler da última linha que casa `^## Sess` até o fim. Reportar o último bloco de sessão e, integral, seu bloco de pendências/dívidas. Não resumir, não escolher "o relevante".
3. Nº de testes verdes herdado: o valor declarado nesse bloco, com a origem citada.

## Verificação (antes de entregar)
- Cruzar git × último bloco do HISTORICO: o commit do topo do log corresponde ao declarado na última sessão? branch e sincronia batem? Em **qualquer** divergência, a divergência é o relato principal — não silenciar escolhendo git nem HISTORICO.
- Todo valor que não veio direto de git ou do HISTORICO lido recebe `[INTERPRETADO]`.
- Saída só em tela. Foco, prioridade e numeração da próxima sessão são do Arquiteto no chat.

Gate de procedência factual: ver D-ARQ-22 vivo (não fixar versão).
