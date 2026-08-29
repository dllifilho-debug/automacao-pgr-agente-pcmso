# Ritual de fechamento de sessão

Checklist fixo para o fechamento de qualquer sessão que toque código ou docs vivos.
O prompt de fechamento de cada sessão é **instanciação** deste ritual, não redação livre —
foi na redação livre (dispensa da suíte por um prompt "docs-only") que a lacuna medida em
DH-003EG-03 entrou. Origem: emenda 003.EG, `CLAUDE.md` seção "Verificação".

1. Conferir a última linha do changelog de `docs/PROTOCOLO_AGENTE_MEDICO.md` e de
   `docs/DECISOES_ARQUITETURAIS.md` contra o que a sessão espera encontrar. Divergência é
   bloqueador — parar e reportar, nunca ajustar para bater.
2. Gravar as pendências novas em `docs/PENDENCIAS_CLINICAS.md`, respeitando a convenção `DH-*`
   (higiene de instrumento/método) / `DT-*` (dívida técnica ou de conhecimento). ID novo nunca
   reinventa ID existente.
3. Gravar DECISOES (nota de aplicação em D-ARQ existente, ou D-ARQ nova). Se este passo tocou
   `docs/DECISOES_ARQUITETURAIS.md`, regenerar `docs/INDICE_DARQ.md`
   (`python -m scripts.gerar_indice_darq`) antes de commitar — passo obrigatório, não
   condicional a "sessão é docs-only".
4. Gravar o bloco da sessão no `docs/HISTORICO_OPERACIONAL.md`: foco, commits, número da
   suíte (com a árvore/commit em que foi medida), pendências na íntegra, lições de método.
5. Re-tirar o `docs/PAINEL_ESTADO.md` em **duas cadências distintas** (`D-ARQ-85`):
   - **Bloco Baseline** — re-tirado em TODO fechamento que produza commit: hash, contagem de
     suíte com o commit em que foi medida, e versões de `PROTOCOLO`/`DECISOES`. Sessão que não
     mediu a suíte grava a contagem herdada **com o commit de origem visível**, nunca como corrente.
   - **Os três números clínicos** — regra intacta: só se um deles se moveu, um marco fechou, ou a
     sessão é META. Declarar a decisão explicitamente no HISTORICO, mesmo quando for "não re-tirar".
   - Parágrafos de tiragem ("Instrumento oficial nesta tiragem", "Nota de escopo desta tiragem") são
     registro histórico e **não** são reescritos por re-tiragem de Baseline.
6. Rodar o subconjunto de testes que cobre os derivados tocados por esta sessão; suíte
   completa (`python -m pytest agente_medico/tests/ tests/`) se a sessão tocou código. Nenhum
   prompt dispensa este passo — recorte nunca é zero.
7. Commit por doc/arquivo, nominal (`git add` de cada arquivo, nunca `git add .`). Push só com
   autorização explícita do turno.
8. Antes de emitir qualquer artefato que crave fato (prompt cirúrgico, corpo de D-ARQ, bloco de
   sessão do HISTORICO, re-tiragem do painel, spec de dado): rodar `/conferir` sobre ele
   (`D-ARQ-84` cl.1). `DIVERGE` material é bloqueador — corrigir e re-conferir antes de emitir
   (cl.3). Não há declaração de gate para este passo, por desenho (cl.2): a evidência é o
   relatório, referenciado no bloco da sessão.
9. Depois do merge em `main`, varrer branch orfa: `git branch --merged main` (e a listagem
   remota equivalente). Toda branch ja mergeada, local e remota, e apagada com `git branch -d`
   (minusculo — recusa apagar o que nao esta mergeado; `-D` nunca, sem decisao explicita) e
   `git push origin --delete`. Apagar remoto conta como escrita no remoto: exige a mesma
   autorizacao explicita do passo 7. Motivo medido: em 003.FD a branch
   `fix/003fd-emenda-gauntlet` sobreviveu ao merge e so foi encontrada em 003.FE, uma sessao
   depois — segunda ocorrencia da mesma classe, e nenhum passo do ritual a varria.
