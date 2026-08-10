# Regras de método — projeto Agente Médico PCMSO

Fonte de verdade, em ordem: (1) git log/status reais, (2) docs vivos em `docs/`
(PROTOCOLO_AGENTE_MEDICO.md, DECISOES_ARQUITETURAIS.md, HISTORICO_OPERACIONAL.md,
PENDENCIAS_CLINICAS.md),
(3) qualquer cache. Nunca afirmar número de sessão, D-ARQ, hash ou contagem de testes
de memória — ler do disco.

## Verificação (regras duras, sem exceção por conveniência)

- Nenhum prompt ou sessão dispensa a suíte. Se a suíte inteira é cara (DH-003EC-02: ~79% do
  tempo é reparse de PDF real), o recorte é o subconjunto que cobre os derivados tocados —
  **nunca zero**.
- Sessão que toca `docs/DECISOES_ARQUITETURAIS.md` **regenera** `docs/INDICE_DARQ.md`
  (`python -m scripts.gerar_indice_darq`) e roda `python -m pytest tests/test_gerar_indice_darq.py`.
  Cláusula fixa. Violá-la já custou duas sessões: `c89f569` (003.EF) e `973a343` (003.EG).
- Instrução que remove uma checagem existente exige justificativa com custo medido. Sem
  número, a checagem fica.
- Número ou estado não medido na sessão corrente sai marcado `[A MEDIR]` ou não sai.
- Prompt que pede teste novo nomeia, junto, a reversão de código que deve deixá-lo vermelho.
  Teste cuja reversão não é nomeável não entra. Antes de entregar, a verificação é a varredura
  inversa (teste a teste, qual reversão o mata) — grep de símbolos é checagem de sintaxe, não
  verificação. Origem medida: 003.EK, 5 testes especificados que não tocavam o comportamento
  que diziam cobrir (aninhamento literal em vez de composto nomeado; unidade sobre função que
  nunca leu o campo; estado inalcançável; caminho estruturalmente inalcançável). Varredura
  inversa da fatia 1 deu 7/12 discriminantes; da emenda, 4/6. Causa nomeada no Arquiteto, não
  no Code.

## Git

- `git add` por arquivo nominal, nunca `git add .`
- Branch por sessão: `git checkout -b feat/<sessao>-<nome>` a partir de `main` atualizada
- Push exige autorização explícita por turno. Merge é do Diovanni, via PR, "Create a merge commit"
- Não criar a branch da próxima sessão antes do merge da atual
- Não fabricar estados de commit com `git hash-object`/`update-index`: todo commit deve ter
  existido como working tree. Se a separação exigir isso, **pare e reporte** — a decisão é do
  Arquiteto (precedente: `94a5720`/`76f1afa`, 003.EG)
- Bloqueador reportado = decisão do Arquiteto. Divergência entre medição real e valor esperado
  no prompt = bloqueador: parar e reportar, nunca ajustar para bater

## Comandos padrão

- `python -m pytest` / `python -m mypy --strict` — nunca `pytest`/`mypy` direto
- **Alvo canônico do mypy, literal** — não usar `<pasta>` genérico:
  `python -m mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py app_matriz.py`
  Referência medida em 003.EU (10/08/2026) sobre `6d3c723`: limpo, **47
  arquivos**. Subiu de 45 (003.ES) porque 003.ET criou `motor/io_pdf.py` e
  `superficie/materializar_secrets.py`, e o fechamento de 003.ET não re-mediu
  (nenhum `.py` tocado). É referência, não gabarito eterno: prompt que cravar
  esse número como bloqueador tem de medi-lo na sessão corrente.
  **`agente_medico/` inteiro NÃO é o alvo:** puxa a pasta de testes e 47 erros pré-existentes que
  nenhum gate olha. Erro do Arquiteto 2×, mesmo diagnóstico (003.EC e 003.ES) — o alvo fica escrito
  aqui justamente para não depender de memória.
- Suíte completa: `python -m pytest agente_medico/tests/ tests/` (motor novo + legada)
- Medição de suíte nunca concorrente com escrita — árvore parada, ou o número não tem
  proveniência (precedente: 003.EF)

## Código

Sem comentários óbvios. Exceção: código que materializa regra clínica carrega, em comentário
ou docstring, o ID da regra (`R-CATEGORIA-NN`) e a fonte normativa quando aplicável —
auditoria de PCMSO precisa rastrear da linha até a norma.
