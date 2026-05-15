# Histórico Operacional — Agente Médico PCMSO

**Propósito:** registro cronológico de bugs corrigidos, commits, sprints e
status técnico das sessões. Vida útil **rotativa** — o que tem mais de 3
meses pode ser arquivado.

**Para conhecimento clínico permanente** → ver `PROTOCOLO_AGENTE_MEDICO.md`
**Para decisões de design permanentes** → ver `DECISOES_ARQUITETURAIS.md`

**Renomeado de `CONTEXTO_SESSAO.md` em 2026-05-15** como parte da
reestruturação documental (ver ADR-003).

---

# Contexto do Projeto PGR → PCMSO
**Projeto:** Automação PGR → PCMSO | Diovanni Lisita — Seconci-GO
**Stack:** Python, Streamlit, GitHub, Gemini API, Supabase
**Última atualização:** 04/05/2026 — fix alias + bateria de regressão pytest criada e verde

---

## Bugs resolvidos em sessões anteriores (NÃO mexa)
- Bug #1: Erro de importação no fluxo principal ✅
- Bug #2: Falha na leitura de riscos ✅
- Bug #3: Fallback distribuindo 23 cargos em todos os GHEs ✅
- Delimitação de blocos GHE ✅
- Allowlist/Blocklist de cargos ✅
- Dicionário semântico ✅

---

## Status das correções desta sprint

### ✅ Prompt 1 — Normalização pré-match
- Função `normalizar_cargo(nome: str) -> str` implementada
- Expande "meio of." → "meio oficial de"
- Remove prefixos com ":" (ex: "Manutenção: Eletricista" → "Eletricista")
- Aplica unidecode() + lower() + strip()
- ✅ Implementado | ✅ Testado | ✅ Commitado

✅ CORREÇÃO DO ALIAS APLICADA (commit 660d60e):
`normalizar_cargo()` agora normaliza APENAS GRAFIA (steps 1–5) — SEM colapso alias.
"meio oficial de pintor" permanece como cargo separado na deduplicação.
Nova função `resolver_alias_cargo(s)` criada para lookup explícito no banco v1.
Banco v2 já resolve via Tentativa 3 (match parcial) sem precisar de alias.

---

### ✅ Prompt 5 — Ampliar banco de cargos
- 9 cargos novos adicionados ao banco com exames definidos:
  meio oficial de pintor, meio oficial de gesseiro, Encarregado,
  Encarregado de obra, Administrativo, Administrativo De Obra,
  Porteiro, Vigia, Aprendiz, Operador de Guincho,
  aplicador de asfalto impermeabilizante
- ✅ Implementado | ✅ Testado | ✅ Commitado

---

### ✅ Prompt 2 — Filtro de labels de contexto
- Função `is_cargo_valido(texto, titulo_ghe) -> bool` implementada
- Commit: 6903e23
- Blocklist cobre: estrutura, concreto armado, argamassa, contrapiso,
  impermeabilização, montagem, gesso corrido, alvenaria, fundação,
  escavação, revestimento, pintura externa, preparação
- Exceção funcionando: "operador de X" e "aplicador de X" passam
- ✅ Implementado | ✅ Testado (19/19) | ✅ Commitado

---

### ✅ Prompt 3 — Título descritivo dos GHEs
- Helper `_renumerar_ghe_sequencial(nome_original, novo_num)` implementado
- Commit: 82fbda9
- Cobre separadores: -, :, –, —
- Numeração sequencial via enumerate(start=1) — sem estado global
- Fallback: "GHE [N] - Atividade não identificada" se título vazio
- Renderização no .docx funcionando sem mudanças adicionais
- ✅ Implementado | ✅ Testado (6/6) | ✅ Commitado

---

### ✅ Prompt 4 — Deduplicação de cargos por GHE
- Função `_consolidar_cargos_dados_ghe()` implementada
- Commit: 7d3ac72
- Dedup intra-GHE usando normalizar_cargo() como chave
- Servente preservado entre GHEs diferentes ✅
- Redistribuição de cargos admin para GHE de destino ✅
- ✅ Implementado | ✅ Testado (4/4) | ✅ Commitado
- ✅ BUG DO ALIAS CORRIGIDO: "meio oficial de pintor" não colapsa mais (ver Prompt 1)

---

## Testes de regressão
- Arquivo: `tests/test_regressao_pcmso.py`
- Comando: `pytest tests/test_regressao_pcmso.py -v`
- 5 suites: Normalização, FiltroLabels, BancoCargos, IntegridadeOutput, CasosCriticos
- ✅ RESULTADO: **53 passed, 5 skipped** (commit 660d60e)
- Os 5 skips são de TestIntegridadeOutput — ativam automaticamente quando
  `matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf` for adicionado ao projeto

---

## Auditoria final (Opus)
- ⏳ Próximo passo — pytest verde, pronto para iniciar
- Usar modelo Opus (não Sonnet) para esta etapa
- 5 camadas: Estrutura GHEs, Integridade Cargos, Cobertura Exames,
  Periodicidades, Qualidade Word

### Pontos críticos para a auditoria não esquecer:
- ✅ Serralheiro: Exame Clínico **6M** confirmado pelo pytest
- ⚠️ Operador de betoneira: NÃO tem Acuidade Visual nem ECG
- ⚠️ Eletricista industrial: deve ter Ácido tricloroacético na urina (semestral-P)
- ⚠️ Encanador: nota de risco Metietilcetona deve aparecer no Word
- ⚠️ Campos de cabeçalho do .docx (Empresa, CNPJ, Médico RT) não podem estar vazios
- ⚠️ Vigência: data início ≠ data fim (bug no formulário Streamlit — não no motor)

---

## Pontos de atenção (decisões autônomas desta sessão)
- **Separação de concerns em normalizar_cargo()**: a função agora faz APENAS grafia.
  Alias resolution foi extraída para `resolver_alias_cargo()`. Callers do banco v1
  agora fazem `resolver_alias_cargo(normalizar_cargo(nome))`. Banco v2 usa Tentativa 3
  (substring match) sem precisar de alias.
- **TestIntegridadeOutput usa skip gracioso**: se o PDF PGR não existir, os 5 testes
  da suite pulam em vez de falhar. Isso permite o CI passar enquanto o PDF não é
  incluído no repositório.
- **36 cargos testados no TestBancoCargos** (spec dizia "34" mas a lista tinha 36).

---

## Como retomar em nova sessão

**Atualizado em 2026-05-15** — Cole no início do Claude Code:

> "Leia HISTORICO_OPERACIONAL.md, PROTOCOLO_AGENTE_MEDICO.md e
> DECISOES_ARQUITETURAIS.md, depois me diga em qual modo vamos trabalhar:
> CONHECIMENTO, ARQUITETURA ou IMPLEMENTAÇÃO."
