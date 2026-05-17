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

*Entradas futuras abaixo desta linha*
