# Ritual de fechamento de sessão

Checklist fixo para o fechamento de qualquer sessão que toque código ou docs vivos.
O prompt de fechamento de cada sessão é **instanciação** deste ritual, não redação livre —
foi na redação livre (dispensa da suíte por um prompt "docs-only") que a lacuna medida em
DH-003EG-03 entrou. Origem: emenda 003.EG, `CLAUDE.md` seção "Verificação".

1. Conferir a última linha do changelog de `docs/PROTOCOLO_AGENTE_MEDICO.md` e de
   `docs/DECISOES_ARQUITETURAIS.md` contra o que a sessão espera encontrar. Divergência é
   bloqueador — parar e reportar, nunca ajustar para bater.
2. Gravar as pendências novas no §11 do PROTOCOLO, respeitando a convenção `DH-*` (higiene de
   instrumento/método) / `DT-*` (dívida técnica ou de conhecimento). ID novo nunca reinventa ID
   existente.
3. Gravar DECISOES (nota de aplicação em D-ARQ existente, ou D-ARQ nova). Se este passo tocou
   `docs/DECISOES_ARQUITETURAIS.md`, regenerar `docs/INDICE_DARQ.md`
   (`python -m scripts.gerar_indice_darq`) antes de commitar — passo obrigatório, não
   condicional a "sessão é docs-only".
4. Gravar o bloco da sessão no `docs/HISTORICO_OPERACIONAL.md`: foco, commits, número da
   suíte (com a árvore/commit em que foi medida), pendências na íntegra, lições de método.
5. Avaliar re-tiragem do `docs/PAINEL_ESTADO.md`: só se um dos 3 números clínicos se moveu, um
   marco fechou, ou a sessão é META. Declarar a decisão explicitamente no HISTORICO, mesmo
   quando for "não re-tirar".
6. Rodar o subconjunto de testes que cobre os derivados tocados por esta sessão; suíte
   completa (`python -m pytest agente_medico/tests/ tests/`) se a sessão tocou código. Nenhum
   prompt dispensa este passo — recorte nunca é zero.
7. Commit por doc/arquivo, nominal (`git add` de cada arquivo, nunca `git add .`). Push só com
   autorização explícita do turno.
