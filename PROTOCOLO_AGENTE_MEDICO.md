# Protocolo do Agente Médico PCMSO

**Propósito:** registrar as regras clínicas extraídas da Dra. Carolini
Polesso (coordenadora PCMSO) que vão alimentar o agente médico universal.

**Fonte primária:** entrevistas com a Dra. Carolini.
**Fontes complementares:** NR-07/NR-09/NR-15, Matriz Excel Dra. Patrícia
06/2025, jurisprudência clínica de medicina do trabalho.

---

## Como usar este documento

- Cada regra tem ID único (REGRA-XXX) e é permanente
- Regras são organizadas por **categoria clínica**, não por ordem cronológica
- Status indica maturidade: `hipótese` → `em validação` → `validada`
- Toda regra precisa de **exemplo concreto** (não fica abstrato)
- Toda regra precisa declarar **escopo de aplicação** (universal vs setorial)

---

## Status do Protocolo

| Categoria | Total de Regras | Validadas | Em Validação | Hipóteses |
|---|---|---|---|---|
| Leitura do PGR | 0 | 0 | 0 | 0 |
| Identificação de Riscos | 0 | 0 | 0 | 0 |
| Integração de FDS | 0 | 0 | 0 | 0 |
| Definição de Exames | 0 | 0 | 0 | 0 |
| Periodicidade | 0 | 0 | 0 | 0 |
| Casos-Fronteira | 0 | 0 | 0 | 0 |
| **TOTAL** | **0** | **0** | **0** | **0** |

---

## Categoria A — Leitura do PGR

*Como a Dra. Carolini lê um PGR pela primeira vez. Ordem de leitura,
pontos de atenção, sinais de qualidade do documento.*

<!-- Regras serão adicionadas aqui à medida que extraídas -->

---

## Categoria B — Identificação de Riscos Relevantes

*Como ela decide quais riscos do PGR são "relevantes" para a matriz e
quais podem ser ignorados.*

<!-- Regras serão adicionadas aqui -->

---

## Categoria C — Integração de FDS

*Como ela usa FDS quando estão disponíveis, e como compensa a ausência
delas. Conhecimento mais valioso e mais tácito do método.*

<!-- Regras serão adicionadas aqui -->

---

## Categoria D — Definição de Exames

*Como ela sai do risco identificado e chega ao exame específico. Inclui
exames básicos NR-07 e ajustes por contexto.*

<!-- Regras serão adicionadas aqui -->

---

## Categoria E — Periodicidade e Ajustes Clínicos

*As decisões de 6M vs 12M vs 24M. Por que reduzir? Quando? Em que
exposição? Decisões mais tácitas e menos normativas.*

<!-- Regras serão adicionadas aqui -->

---

## Categoria F — Casos-Fronteira e Exceções

*Situações ambíguas, conflito entre regras, riscos não-mapeados na
NR-07, decisões discricionárias.*

<!-- Regras serão adicionadas aqui -->

---

## Modelo de Regra (para referência)

```markdown
### REGRA-XXX — Título curto da regra

**Categoria:** [A/B/C/D/E/F]
**Status:** [hipótese | em validação | validada]
**Escopo:** [universal | setor X | obra Y]

**Enunciado:**
Descrição clara e acionável da regra. Deve ser codificável.

**Exemplo concreto:**
Caso real onde a regra foi aplicada. Sem isso, a regra não é validável.

**Fonte:**
- Origem: entrevista Dra. Carolini, áudio YYYY-MM-DD, bloco/pergunta
- Validação: matriz Viverde GHE XX, ou outra evidência documental
- Normativa relacionada: NR-XX, anexo Y (se houver)

**Implementação esperada:**
Como essa regra deve aparecer no código. Pseudocódigo ou descrição.

**Conflitos conhecidos:**
Outras regras que podem entrar em conflito com essa, e como resolver.
```

---

## Lacunas Identificadas

*Regras que sabemos que existem mas ainda não foram formalizadas.
Esta seção cresce e diminui ao longo do projeto.*

<!-- Exemplo:
- Como ela trata risco psicossocial em obras grandes vs pequenas?
- Critério dela para incluir Avaliação Oftalmológica em motoristas
-->

---

## Histórico de Versões

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-05-15 | Documento criado, estrutura inicial |
