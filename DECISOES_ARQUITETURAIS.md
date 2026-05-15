# Decisões Arquiteturais — Agente Médico PCMSO

**Propósito:** registrar decisões de design do sistema. Cada decisão é
um ADR (Architecture Decision Record) — permanente, datada, com contexto
e consequências.

**Princípio:** decisões aqui registradas só são revertidas com novo ADR
que explicitamente substitui o anterior. Não se "muda silenciosamente"
uma decisão arquitetural.

---

## Como usar este documento

- Cada decisão tem ID único (ADR-XXX) e é permanente
- Decisões são organizadas em ordem **cronológica** (mais recente embaixo)
- Status: `proposta` → `aceita` → `superada por ADR-YYY`
- ADRs superadas **não são removidas** — ficam como histórico
- Toda decisão precisa declarar **alternativas consideradas** (mesmo que
  rejeitadas), pra que futuro leitor entenda o porquê da escolha

---

## Modelo de ADR (para referência)

```markdown
### ADR-XXX — Título da decisão

**Status:** [proposta | aceita | superada por ADR-YYY]
**Data:** YYYY-MM-DD

**Contexto:**
O problema que motivou a decisão. Por que precisava decidir?

**Decisão:**
O que foi decidido, em uma frase clara.

**Alternativas consideradas:**
1. Alternativa A — por que foi rejeitada
2. Alternativa B — por que foi rejeitada
3. Alternativa escolhida — por que foi aceita

**Consequências:**
- Positivas: ...
- Negativas: ...
- Trade-offs aceitos: ...

**Referências:**
- Conversas, documentos, normas que embasaram
```

---

## ADRs Aceitas

### ADR-001 — Sistema deve ser universal, não específico para Viverde

**Status:** aceita
**Data:** 2026-05-15

**Contexto:**
Durante 6+ meses de desenvolvimento, o sistema foi construído com base
no PGR da Viverde como caso primário. O banco `banco_ghe_cargo_v1.json`
foi gerado a partir da matriz RQ.61 da Viverde, e o motor de exames
faz lookup nesse banco como fonte primária.

Testes com 3 outros PGRs (Seconci, TPB Andrade, Ricco Hetrin) mostraram
que o sistema falha consistentemente fora do contexto Viverde:
- TPB: parser captura apenas 1 seção em 74k chars
- Ricco: detecta formato CARGO mas extrai "Assinatura" como cargo
- Seconci: 10 cargos não mapeados (vocabulário não-canteiro)

**Decisão:**
O objetivo final do projeto é processar **qualquer PGR de qualquer
empresa de qualquer setor**, não apenas construção civil ou apenas
Viverde. Toda decisão arquitetural futura deve priorizar universalidade.

**Alternativas consideradas:**
1. Manter foco em construção civil e ampliar banco com mais clientes
   do setor — rejeitado: replica o problema em escala maior, não resolve
2. Criar bancos separados por cliente — rejeitado: insustentável, cria
   N sistemas em vez de um
3. Reconstruir como agente médico universal — **aceito**: alinha com
   visão de longo prazo do Diovanni

**Consequências:**
- Positivas: sistema pode atender múltiplos setores, escalabilidade real,
  conhecimento clínico fica explícito (vs implícito no banco)
- Negativas: maior complexidade inicial, dependência de extração de
  conhecimento da Dra. Carolini, prazo maior de entrega (6-8 semanas
  estimadas)
- Trade-offs aceitos: aceitar que operação atual com Viverde continua
  funcionando durante a transição, sem regressões

**Referências:**
- Conversa de 2026-05-15 entre Diovanni e Arquiteto sobre futuro do projeto
- Resultados de teste empírico com 4 PGRs distintos

---

### ADR-002 — Hierarquia de fontes de verdade do sistema

**Status:** aceita
**Data:** 2026-05-15

**Contexto:**
O sistema atualmente usa múltiplas fontes de regras clínicas sem
hierarquia clara:
- `banco_ghe_cargo_v1.json` (Viverde, lookup GHE+Cargo)
- `banco_matrizes_v2.json` (cargo genérico, fallback)
- `banco_riscos_nr7.json` (gerado da Matriz Excel da Dra. Patrícia,
  com bugs de migração)
- Hardcoded em `agente_medico_ia.py` (regras Python em CARGOS_RISCO_QUIMICO_6M,
  _EXAMES_RISCO_POR_CARGO, etc.)

A ausência de hierarquia formal causa decisões inconsistentes e
dependência de código (não-clínico) para regras clínicas.

**Decisão:**
Estabelecer hierarquia formal de fontes de verdade, em ordem decrescente
de autoridade:

1. **Protocolo clínico da Dra. Carolini** (em construção, documento
   `PROTOCOLO_AGENTE_MEDICO.md`)
2. **NR-07, NR-09, NR-15** e normas correlatas
3. **Matriz Excel validada pela Dra. Patrícia** (referência, não gabarito)
4. **PGR Viverde** (caso de teste, não caso de uso final)

Regras hardcoded em Python (CARGOS_RISCO_QUIMICO_6M, etc.) devem ser
migradas para fonte declarativa (PROTOCOLO_AGENTE_MEDICO.md) ao longo
do refactor.

**Alternativas consideradas:**
1. Manter regras hardcoded em Python — rejeitado: opaco para a Dra.
   Carolini revisar, viola separação entre conhecimento e código
2. Banco único Supabase com todas as regras — rejeitado prematuramente:
   pode ser destino final, mas hoje aumenta complexidade
3. Hierarquia em documento Markdown + código gera regras a partir
   do documento — **aceito**: legível pela médica, versionável em git,
   migrável para banco depois

**Consequências:**
- Positivas: Dra. Carolini consegue revisar regras sem ler código,
  regras viram unidade de teste isolável, sistema fica auditável
- Negativas: requer disciplina de manter documento atualizado, sincronização
  documento ↔ código vira responsabilidade do dev
- Trade-offs aceitos: aceitar duplicação temporária (regra existe no
  documento E no código) durante refactor

**Referências:**
- Estrutura `PROTOCOLO_AGENTE_MEDICO.md` criada nesta data
- Conversa sobre separação de conhecimento clínico e implementação

---

### ADR-003 — Três documentos separados para gestão do projeto

**Status:** aceita
**Data:** 2026-05-15

**Contexto:**
O arquivo `CONTEXTO_SESSAO.md` original mistura três naturezas de
informação distintas:
- Bugs operacionais ("Bug do alias resolvido no commit 660d60e")
- Decisões de design ("decidimos separar grafia de alias resolution")
- Regras clínicas implícitas ("Serralheiro tem EC 6M")

Essa mistura dificulta consulta futura e impede que o conhecimento
clínico (que tem vida útil permanente) seja preservado quando bugs
forem esquecidos (vida útil curta).

**Decisão:**
Separar a gestão do projeto em três documentos com naturezas distintas:

1. `PROTOCOLO_AGENTE_MEDICO.md` — conhecimento clínico (permanente)
2. `DECISOES_ARQUITETURAIS.md` — decisões de design (permanente)
3. `HISTORICO_OPERACIONAL.md` — bugs, commits, sessões (rotativo)

Ao final de cada sessão, o Arquiteto pergunta explicitamente em qual(is)
documento(s) a sessão gerou registro.

**Alternativas consideradas:**
1. Manter documento único — rejeitado: já provou ser ruim
2. Dois documentos (técnico + clínico) — rejeitado: decisões de design
   misturadas com bugs continuam dificultando consulta
3. Três documentos com naturezas separadas — **aceito**

**Consequências:**
- Positivas: cada documento tem vida útil clara, busca futura mais fácil,
  preservação de conhecimento clínico independente de rotatividade
- Negativas: três arquivos para manter atualizados, requer disciplina
  de classificação ao final de cada sessão
- Trade-offs aceitos: alguma sobreposição é OK (decisão arquitetural
  pode referenciar regra clínica)

**Referências:**
- Conversa de 2026-05-15 sobre estruturação do projeto

---

## ADRs Superadas

*Vazio. Quando uma ADR for substituída, ela move para esta seção e
permanece como histórico.*

---

## Lacunas e Decisões Pendentes

*Decisões arquiteturais que sabemos que precisam ser tomadas mas
ainda não foram. Cresce e diminui ao longo do projeto.*

- **Como o Gemini será usado no novo sistema:** apenas para extração
  de PGR? Também para inferência de exames? Cascade de fallback?
- **Onde ficam as regras clínicas no código:** YAML, JSON, Python
  declarativo, banco Supabase?
- **Como o auditor genérico funciona:** Camada de validação separada
  ou integrada ao motor principal?
- **Multitenancy:** sistema atende múltiplas Seconcis ou apenas Seconci-GO?
- **API ou apenas Streamlit:** sistema vira API consumível por terceiros?

---

## Histórico de Versões

| Versão | Data | Mudança |
|---|---|---|
| 0.1 | 2026-05-15 | Documento criado, ADRs 001-003 retroativas |
