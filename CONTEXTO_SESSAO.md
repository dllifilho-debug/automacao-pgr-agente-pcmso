# Contexto do Projeto PGR → PCMSO
**Projeto:** Automação PGR → PCMSO | Diovanni Lisita — Seconci-GO  
**Stack:** Python, Streamlit, GitHub, Gemini API, Supabase  
**Última atualização:** 03/05/2026 — sessão interrompida por limite de contexto

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

⚠️ PROBLEMA PENDENTE NESTA FUNÇÃO:
O alias está colapsando "meio oficial de pintor" → "pintor" durante
a deduplicação do Prompt 4. Isso remove a linha do cargo-filho do PCMSO.
CORREÇÃO NECESSÁRIA: normalizar_cargo() deve normalizar GRAFIA apenas
(ex: "meio of." → "meio oficial de"), mas NÃO colapsar para o cargo-pai.
"meio oficial de pintor" deve continuar como cargo separado no PCMSO.

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

⚠️ EFEITO COLATERAL DO ALIAS (precisa corrigir antes de prosseguir):
"meio oficial de pintor" está sendo colapsado para "pintor" na dedup
porque normalizar_cargo() usa aliases que mapeiam cargo-filho → cargo-pai.
Ver correção pendente no Prompt 1 acima.

---

## Testes de regressão
- Arquivo: `tests/test_regressao_pcmso.py`
- Comando: `pytest tests/test_regressao_pcmso.py -v`
- 5 suites: Normalização, FiltroLabels, BancoCargos, IntegridadeOutput, CasosCriticos
- Status: ⚠️ NÃO RODADO ainda na sessão atual — rodar após corrigir alias

---

## Auditoria final (Opus)
- ⏳ Aguardando pytest 100% verde
- Usar modelo Opus (não Sonnet) para esta etapa
- 5 camadas: Estrutura GHEs, Integridade Cargos, Cobertura Exames,
  Periodicidades, Qualidade Word

### Pontos críticos para a auditoria não esquecer:
- ⚠️ Serralheiro: Exame Clínico deve ser **6M** (não 12M)
- ⚠️ Operador de betoneira: NÃO tem Acuidade Visual nem ECG
- ⚠️ Eletricista industrial: deve ter Ácido tricloroacético na urina (semestral-P)
- ⚠️ Encanador: nota de risco Metietilcetona deve aparecer no Word
- ⚠️ Campos de cabeçalho do .docx (Empresa, CNPJ, Médico RT) não podem estar vazios
- ⚠️ Vigência: data início ≠ data fim (bug conhecido)

---

## Como retomar em nova sessão
Cole no início do Claude Code:
"Leia o arquivo CONTEXTO_SESSAO.md e me diga qual é o próximo
passo pendente com base nos status marcados."