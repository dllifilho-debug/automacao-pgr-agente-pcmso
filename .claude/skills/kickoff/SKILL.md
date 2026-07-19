---
name: kickoff
description: Coletor de estado de abertura de sessão (git + fim do HISTORICO + versões reais dos docs + dívidas abertas). Reporta verbatim; não decide foco nem calcula numeração. Invocação manual.
disable-model-invocation: true
allowed-tools: Bash(git log *) Bash(git status *) Read
---

# /kickoff — coletor de estado de abertura

Coleta e **reporta** estado factual. Não decide foco/prioridade/recorte, não calcula o número da próxima sessão, não cria branch, não escreve arquivo, não lê docs da raiz (cópias-fantasma) — só `docs/`.

## Coleta (rodar e reportar verbatim)
1. `git log --oneline -10` e `git status`.
2. Fim de `docs/HISTORICO_OPERACIONAL.md`: ler da última linha que casa `^## Sess` até o fim. Reportar o último bloco de sessão e, integral, seu bloco de pendências/dívidas. Não resumir, não escolher "o relevante".
3. Nº de testes verdes herdado: o valor declarado nesse bloco, com a origem citada.
4. **Versões REAIS dos docs vivos** — ler o arquivo, não aceitar o que o HISTORICO declara: última linha da tabela de revisões de `docs/DECISOES_ARQUITETURAIS.md` e de `docs/PROTOCOLO_AGENTE_MEDICO.md`; linhas "Tiragem corrente" e "Baseline" de `docs/PAINEL_ESTADO.md`.
5. **Dívidas abertas** — listar os IDs `DT-*` marcados `[ABERTA]` em `docs/DECISOES_ARQUITETURAIS.md`, uma linha cada. Só os abertos. A fila do HISTORICO é da última sessão e pode não citar dívida aberta antes dela.

## Verificação (antes de entregar)
- Cruzar git × último bloco do HISTORICO: o commit do topo do log corresponde ao declarado na última sessão? branch e sincronia batem? Em **qualquer** divergência, a divergência é o relato principal — não silenciar escolhendo git nem HISTORICO.
- Cruzar **HISTORICO × docs reais**: a linha "Docs:" do último bloco declara versões (ex.: "DECISOES v135, PROTOCOLO v59"). Conferir contra o que foi lido no item 4. Declarado ≠ real é relato principal, mesma regra acima. *(Motivo: em 003.DL o changelog da §5.9 entrou mas a tabela de revisões do PROTOCOLO não foi incrementada — o declarado batia consigo mesmo e nada cruzava com o arquivo.)*
- Todo valor que não veio direto de git ou dos docs lidos recebe `[INTERPRETADO]`.
- Saída só em tela. Foco, prioridade e numeração da próxima sessão são do Arquiteto no chat.

Gate de procedência factual: ver D-ARQ-22 vivo (não fixar versão).
