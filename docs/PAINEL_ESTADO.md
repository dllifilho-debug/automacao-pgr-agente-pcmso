# Painel de Estado — Projeto Agente Médico PCMSO
### Gestão à vista · estado corrente do produto

> **Painel vivo, não foto datada.** Mostra o estado corrente medido de disco (git), não estimativa.
> **Como este painel se mantém vivo (cadência de atualização):** re-tirado **por evento, nunca por calendário** —
> (1) a cada merge em `main` que move um dos três números abaixo, (2) em todo fechamento de marco,
> (3) no mínimo 1× por sessão META. Merge que não move número não dispara re-tiragem.
> A re-tiragem é passo do ritual de fechamento já existente (mesmo gate de disco — custo marginal ~zero).
> O `HISTORICO_OPERACIONAL.md` acumula os snapshots; este painel mostra só o presente.
>
> **Duas cadências (`D-ARQ-85`):** o que está acima vale para os **três números clínicos**. O bloco
> **Baseline** — hash, contagem de suíte, versões de doc — é re-tirado em **todo fechamento que
> produza commit**, porque envelhece por commit e não por evento clínico.

---

**Tiragem corrente:** 003.EZ · 16/08/2026 — **não re-tirada em 003.FH, 003.FI, 003.FJ, 003.FK nem 003.FL**, e a decisão é declarada, não omissão (`D-ARQ-85` cl.1). **A sequência termina na sessão atual** (branch `claude/festive-gates-soy0fr`, mesma sessão que fez os PRs #332/#333/#334) — ver "Re-tiragem sessão atual" na Camada 2 e o bloco "Tiragem desta sessão" abaixo: `R-RX-03`/`R-ESP-03` movem regras de verdade, pela primeira vez desde 003.EZ. Em 003.FI: nenhuma `R-*` criada, alterada ou depreciada, e `git diff --name-only eb94b06 e27754c -- '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml'` devolve **vazio** — medido, não inferido; a sessão mexeu em acervo e docs, não em conceito. Em 003.FH: a fatia de 003.FH popula `termos:`, que é forma e não conceito. Medido nos dois lados: `cas: 50/79 slugs (63%)` **antes e depois** da fatia — mesmo resultado que 003.EI já havia registrado ao popular `termos:`. Nenhuma `R-*` criada, alterada ou depreciada. Em 003.FJ e 003.FK, mesma decisão e pela mesma prova: `git diff --name-only 74139b5 e0b8c9b -- '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml' '*agentes.yaml' '*exames.yaml'` devolve **vazio**, e o mesmo diff em `e0b8c9b 6dfb137` devolve **só o `PROTOCOLO`**, cuja mudança inteira são duas linhas da tabela de revisões (a âncora errada da v73 e a linha nova da v92) — changelog, não conceito. Medido, não inferido; nenhuma seção de regra e nenhum `.yaml` tocados. `python -m scripts.medir_painel` em `6dfb137` devolve `regras 23/42` e `cas 50/79`, os mesmos valores da tiragem 003.EZ. Em **003.FL** (PR #330, `75959d9`/merge `96fd0ea`): `git diff --name-only d1f9df6 96fd0ea -- '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml' '*agentes.yaml' '*exames.yaml'` devolve só `agentes.yaml`, e a mudança é `termos:` (alias PNOS/PNOR → `poeira_nao_classificada`, achado da comparação Viverde), não `cas:` nem slug novo — mesma classe de 003.FH. `python -m scripts.medir_painel --suite` em `96fd0ea`: `regras 23/42 (55%)`, `cas 50/79 (63%)`, `índice: sincronizado`, valores idênticos à tiragem 003.EZ. **Entre `6dfb137` (baseline de 003.FK) e `d1f9df6` (pai de 003.FL), três PRs mergearam sem bloco de Baseline próprio** — `#327` (`45c362a`), `#328` (`7376220`) e `#329` (`5414b96`). Medido: `git diff --name-only 6dfb137 d1f9df6 -- '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml' '*agentes.yaml' '*exames.yaml' '*DECISOES_ARQUITETURAIS.md'` devolve **vazio** — nenhum dos três tocou regra clínica, vocabulário ou decisão de arquitetura; a suíte deles soma ao delta do Baseline abaixo, não aos três números clínicos. Na **sessão atual** (PR #332, `f519721`/`7b69d52`, merge `7c58d25`): `git diff --name-only 96fd0ea 7c58d25 -- '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml' '*agentes.yaml' '*exames.yaml'` devolve só `agentes.yaml`, mudança em `termos:` (4ª forma de PNOS por extenso, achado da comparação Aurora Lago das Rosas), não `cas:` nem slug novo — mesma classe de 003.FH/003.FL. `python -m scripts.medir_painel --suite` em `7c58d25`: `regras 23/42 (55%)`, `cas 50/79 (63%)`, `índice: sincronizado`, valores idênticos à tiragem 003.EZ.

> **`[BLOQUEADOR — reportado, não ajustado]` Instrumento diverge do painel em uma regra, e a divergência PRECEDE esta sessão.** `python -m scripts.medir_painel` devolve **`regras: 23/42 ativas (55%)`**; a tabela abaixo declara **22 de 42 (52%)** desde a tiragem 003.EZ. Medido em worktree isolado: **23/42 já em `eb94b06`**, antes do commit desta sessão — a fatia de 003.FH não moveu o número. Entre a tiragem 003.EZ e o HEAD, o único commit que tocou `PROTOCOLO`/`regras.yaml` é `6895958` (003.FC).
>
> **Qual regra explica o +1 fica `[A MEDIR]`, deliberadamente.** Identificá-la exige entender as internas de `medir_painel.py`, e `DH-003EC-01` faceta **(b) segue ABERTA** dizendo que esse instrumento "reporta verde sobre vermelho, conta prosa como implementação e não vigia derivados". Arbitrar entre painel e instrumento quando o instrumento tem DH aberta sobre contagem seria escolher um número por conveniência. A tabela **não foi ajustada para bater**. Decisão do Arquiteto.
>
> **O `+1` persiste, inalterado por esta sessão `[MEDIDO — 16/09/2026]`.** `R-RX-03`/`R-ESP-03` são regras novas, plenamente executáveis (`quando`/`emite`), então somam igualmente ao instrumento e à intenção do painel — a lacuna acima não cresce nem fecha. Instrumento pós-sessão: **25/44 (57%)**; tabela "Os três números" pós-sessão: **24/44 (55%)** — mesma folga de 1 já documentada acima, agora sobre denominador maior. Não investigado nesta sessão; fora do escopo do achado que motivou a implementação.

> **Tiragem de fechamento `[MEDIDO — 18-19/09/2026]` (branch `claude/dreamy-mayer-os6jce`, número
> não atribuído; ARQUITETURA + docs — D-ARQ-57 peça 5 + DT do relatório de rastreabilidade da
> matriz, PRs #339/#340, merges `67705b5`/`a2ae366`).** Nenhuma `R-*` criada, alterada ou
> depreciada; nenhum `.yaml` de regra/vocabulário tocado — `git diff --name-only 0f168b4 b3f5e62 --
> '*PROTOCOLO_AGENTE_MEDICO.md' '*regras.yaml' '*agentes.yaml' '*exames.yaml'` devolve **vazio**
> (`0f168b4` = checkpoint da tiragem R-PSY-02/R-PSY-03 abaixo). `python -m scripts.medir_painel
> --suite` em `b3f5e62` (== `main a2ae366`; `git diff --stat b3f5e62 origin/main` vazio,
> confirmado): **`regras: 25/44 (57%)`**, **`cas: 50/80 (62%)`**, **`índice: sincronizado`** — os
> três idênticos à tiragem anterior. `mypy --strict` alvo canônico: limpo, **48 arquivos**,
> delta-zero. Suíte completa (`agente_medico/tests/ tests/`, árvore parada): **1261 passed, 6
> skipped, 0 failed**. Delta **+12 exato** contra o checkpoint anterior (`0f168b4`: 1247 passed + 2
> failed = 1249 não-skip): os 12 testes de `62a2aa1` (PR #338, fix do reconhecedor de cabeçalho
> grid-AIHA fragmentado — fora desta sessão; 4 parametrizados de fragmentação + 1 de equivalência +
> 3 anti-falso-positivo + 1 sintético + 2 reais + 1 de não-regressão, per HISTORICO daquela sessão)
> **+** os 2 que eram `failed` por ambiente (`libreoffice-writer` ausente) e passam a `passed`
> neste container — mesma classe já registrada em 003.FK (pacote pré-instalado pelo hook de
> sessão, não mudança de código): `1247 + 2 + 12 = 1261`, reconciliado exato. PR #338 nunca ganhou
> bloco de Baseline próprio — mesmo padrão já documentado acima para `#327`/`#328`/`#329`. Esta
> sessão em si: só docs — `DECISOES_ARQUITETURAIS.md` (novo andamento "ARQUITETURA da peça 5" sob
> `D-ARQ-57`; sem D-ARQ novo, contagem de decisões intacta em **85**), `PENDENCIAS_CLINICAS.md`
> (1 nota em `DT-(sessão claude/youthful-lamport-3kfkog)-02` + 1 DT nova aberta,
> `DT-(sessão claude/dreamy-mayer-os6jce)-01`), `HISTORICO_OPERACIONAL.md` (2 blocos de sessão),
> `INDICE_DARQ.md` regenerado. `DECISOES v190→v191` (pela nota de andamento); `PROTOCOLO v94`
> inalterado. Nenhuma fatia de D-ARQ-57 peça 5 implementada — decisão fica como ARQUITETURA
> proposta, sem ratificação formal do Diovanni registrada neste turno (ver nota em `D-ARQ-57`).
> Escrita autorizada pelo usuário desta sessão ("fecha o dia, atualiza o PAINEL_ESTADO.md").

> **`R-PSY-02`/`R-PSY-03` `[MEDIDO — 17/09/2026]` (branch `claude/fervent-brown-7dcc0y`, número não
> atribuído; IMPLEMENTAÇÃO — `R-PSY-03`, autorizada pelo Diovanni).** `R-PSY-02` sai `DEPRECATED`
> (fundamento refutado), `R-PSY-03` nova a sucede — troca 1-por-1, sem gatilho de re-tiragem por
> D-ARQ-85 cl.1 (merge que não move número não dispara re-tiragem). Confirmado por medição, não
> presumido: `python -m scripts.medir_painel` devolve **`regras: 25/44 (57%)`**,
> **`cas: 50/80 (62%)`**, **`índice: sincronizado`** — os três idênticos ao valor pós-`R-RX-03`/
> `R-ESP-03` acima. A folga de `+1` entre instrumento e tabela "Os três números" (nota acima)
> também persiste inalterada — nenhuma das duas regras tocadas nesta sessão é a que explica o `+1`.
> `mypy --strict` alvo canônico: limpo, **48 arquivos**, delta-zero. Suíte completa
> (`agente_medico/tests/ tests/`, árvore parada): **1247 passed, 6 skipped, 2 failed** — os 2
> falhos são ambiente (`libreoffice-writer` ausente no container, `test_varrer_acervo_lgpd.py`/
> `test_cobertura_varrer_acervo.py`), mesma classe já registrada em 003.FI (nota de container,
> acima) e confirmados pré-existentes (nenhum arquivo tocado nesta sessão pertence a
> `scripts/varrer_acervo_lgpd.py`). Delta **+13** exato contra o baseline de PR #337 (`1236` —
> `f15744a`): 7 testes novos em `test_extracao_pgr.py` (extrator `detectar_psicossocial`,
> 1 parametrizado ×3), 2 em `test_hidratacao.py`, 2 em `test_predicados.py`, 2 líquidos em
> `test_orquestrador.py` (1 removido/3 novos — troca registrada, redação antiga preservada em
> HISTORICO). Varredura inversa: cada reversão nomeada (extrator, threading, primitivo, `quando`/
> `status` da regra) aplicada e restaurada isoladamente, confirmando exatamente os testes previstos
> em vermelho — detalhe em HISTORICO (bloco desta sessão). Detalhe completo em HISTORICO e
> `DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-01` RESOLVIDA em
> `PENDENCIAS_CLINICAS.md`.

> **Tiragem desta sessão `[MEDIDO — 21/09/2026]` (branch `claude/nice-fermat-xahkji`, número
> não atribuído; IMPLEMENTAÇÃO — fix de `_SEPARADOR_FAIXA`, fecha
> `DT-(sessão branch docs/003fi-achado-gate-forma-faixa)-01`).** **Não re-tirada** — nenhuma
> `R-*` criada, alterada ou depreciada; nenhum `.yaml` de vocabulário tocado; decisão
> declarada, não omissão (`D-ARQ-85` cl.1). O fix é FORMA do gate de composição de FDS
> (`motor/transcricao_fds.py::parsear_faixa`, fallback de separador para espaço puro/`" a "`
> quando hífen/en-dash não bate), não regra clínica nem CAS/slug — mesma classe de decisão
> já usada em 003.FH/003.FI/003.FJ/003.FK/003.FL. `regras`/`cas` inalterados desde a última
> tiragem que os moveu (festive-gates, `R-RX-03`/`R-ESP-03`). Detalhe completo (causa raiz,
> testes, varredura inversa) em `PENDENCIAS_CLINICAS.md` (DT fechada) e HISTORICO_OPERACIONAL.md
> (bloco desta sessão).

> **Tiragem desta sessão, parte 2 `[MEDIDO — 21/09/2026]` (mesma branch
> `claude/nice-fermat-xahkji`, continuação pós-merge do PR #354; IMPLEMENTAÇÃO — faixa
> dupla-desigualdade, fecha `DT-(sessão claude/nice-fermat-xahkji, achado pós-PR #354)-01`).**
> **Não re-tirada** — mesma decisão, mesma prova (`D-ARQ-85` cl.1): nenhuma `R-*`
> criada/alterada/depreciada, nenhum `.yaml` de vocabulário tocado. Achado veio de teste real
> do Diovanni (PGR/FDS "CMO Residencial Verdes Mares", PDFs subidos ao acervo,
> `fds_originais/`) — `DESMOLD SIKA` reprovava o bloco do dazomete (`faixa='>= 0.1 - < 1'`),
> notação de desigualdade dupla que `parsear_faixa` não reconhecia (capturada errado pelo ramo
> de semi-aberta simples de D-ARQ-34 P1). Fix + 5 testes + varredura inversa (4/5
> discriminantes) na mesma sessão, sem handoff. Detalhe em `PENDENCIAS_CLINICAS.md` (DT
> criada e resolvida na mesma entrada) e HISTORICO_OPERACIONAL.md (bloco desta sessão).

> **Tiragem desta sessão, parte 3 `[MEDIDO — 21/09/2026]` (mesma branch
> `claude/nice-fermat-xahkji`, continuação pós-merge do PR #355; IMPLEMENTAÇÃO — faixa
> composta assimétrica, 2ª leva da mesma DT da parte 2).** **Não re-tirada** — mesma
> decisão, mesma prova (`D-ARQ-85` cl.1). Diovanni subiu mais FDS reais (PGR "CMO
> Residencial Aurora") — dedup por hash achou 8 duplicatas do Verdes Mares, 4 arquivos de
> conteúdo genuinamente novo. `Fundo Zarcão-...-PINTOR.pdf` reprovava "Destilados de
> Petróleo" (`faixa='10 - <50'`) — faixa composta com operador só de UM lado (o teto), que
> o `_FAIXA_COMPOSTA` da parte 2 (exigia os dois lados) não cobria. Regex generalizado para
> operador opcional em cada lado independentemente, gated por presença de `'<'`/`'>'` na
> string. Fix + 3 testes + varredura inversa (3/3) na mesma sessão. Detalhe em
> `PENDENCIAS_CLINICAS.md` (nota adicional na mesma DT) e HISTORICO_OPERACIONAL.md (bloco
> desta sessão).

**Baseline `[MEDIDO — 25/09/2026, anexos persistentes e multi-GHE]`:** branch
`claude/determined-fermi-xxah3h` sobre `main 48ea7ec` (merge do PR #373; IMPLEMENTAÇÃO — fatia C,
fecha `DT-(sessão claude/determined-fermi-xxah3h)-01`) · **1380 passed, 6 skipped, 0 failed** *(MEDIDO, árvore parada, 695.74s — 1374 + 6
testes novos)* · `mypy --strict` alvo canônico **limpo, 50 arquivos** · PROTOCOLO inalterado
(v100) · DECISOES v216→**v217** (nota em D-ARQ-49; índice regenerado, 85 decisões).
`medir_painel`: `regras 26/45`, `cas 78/109`, `índice sincronizado` — inalterados; três números
clínicos não re-tirados (D-ARQ-85 cl.1).

**Baseline `[MEDIDO — 25/09/2026, revisão com origem dos exames]`:** branch
`claude/determined-fermi-xxah3h` sobre `main e9962a6` (merge do PR #372; IMPLEMENTAÇÃO — fatia B
de `DT-(sessão claude/determined-fermi-xxah3h)-01`) · **1374 passed, 6 skipped, 0 failed** *(MEDIDO, árvore parada, 721.83s — 1369 + 5 testes
novos)* · `mypy --strict` alvo canônico **limpo, 50 arquivos** (+1, `superficie/revisao_matriz.py`)
· PROTOCOLO v99→**v100** · DECISOES v215→**v216** (notas em D-ARQ-22 e D-ARQ-12; índice
regenerado, 85 decisões). `medir_painel`: `regras 26/45`, `cas 78/109`, `índice sincronizado` —
inalterados; três números clínicos não re-tirados (D-ARQ-85 cl.1): nenhuma `R-*` nem `.yaml`
tocados.

**Baseline `[MEDIDO — 24/09/2026, painel de produtos anexados]`:** branch
`claude/determined-fermi-xxah3h` sobre `main bc2c54a` (merge do PR #371; IMPLEMENTAÇÃO de
superfície — fatia A de `DT-(sessão claude/determined-fermi-xxah3h)-01`) · **1369 passed, 6 skipped, 0 failed** *(MEDIDO, árvore parada,
778.61s — 1364 + 5 testes novos)* · `mypy --strict` alvo canônico **limpo, 49 arquivos** ·
PROTOCOLO e DECISOES inalterados. `medir_painel`: `regras 26/45`, `cas 78/109`, `índice
sincronizado` — inalterados; três números clínicos **não re-tirados** (D-ARQ-85 cl.1): nenhuma
`R-*` nem `.yaml` tocados. Entre o baseline anterior e este, o PR #371 (só docs, medição do Gemini
no Aurora) mergeou sem bloco próprio — suíte não afetada.

**Baseline `[MEDIDO — 24/09/2026, nível P×S na rota LLM]`:** branch `claude/eager-fermat-txbn7h`
sobre `main 5540c15` (merge do PR #369; IMPLEMENTAÇÃO — rota LLM transcreve S·P·NÍVEL, guarda
determinística restringe à escala P×S) · **1364 passed, 6 skipped, 0 failed** *(MEDIDO, árvore
parada, 691.15s — 1358 + 6 testes novos)* · `mypy --strict` alvo canônico **limpo, 49 arquivos** ·
PROTOCOLO v98→**v99** (notas de aplicação, sem regra nova) · DECISOES v214→**v215** (nota em
D-ARQ-49; índice regenerado, 85 decisões). `medir_painel`: `regras 26/45`, `cas 78/109`, `índice
sincronizado` — inalterados (D-ARQ-85 cl.1). Guarda medida no acervo: 109/109 blocos P×S aceitos,
0/318 de escore somado. Saída real do Gemini `[A MEDIR]` (sem chave no container).

**Tiragem `[MEDIDO — 24/09/2026, conferência NR-07]` (branch `claude/eager-fermat-txbn7h` sobre
`main ee241f6`; CONHECIMENTO — docs-only).** Fecha os dois `[A CONFERIR — D-ARQ-69]` de R-BIO-05 e
R-RX-01-qual contra o PDF da NR-07 fornecido pelo Diovanni (cabeçalho até Portaria MTP 567/2022).
**Não re-tirada** (D-ARQ-85 cl.1): nenhuma `R-*` criada, alterada ou depreciada, nenhum código,
teste ou `.yaml` tocado; PROTOCOLO v97→**v98** (só procedência), DECISOES v214 inalterado. Suíte
completa **não re-rodada** — recorte que cobre os derivados tocados (todo teste que lê
PROTOCOLO/regras/PENDENCIAS/HISTORICO/PAINEL): **359 passed**, 237.09s. Baseline de suíte segue o
de R-BIO-05 abaixo (1358/6/0 em código idêntico).

**Baseline `[MEDIDO — 24/09/2026, R-BIO-05]`:** branch `claude/eager-fermat-txbn7h` sobre
`main 657ccda` (merge do PR #367; IMPLEMENTAÇÃO — `R-BIO-05`, risco IRRELEVANTE no PGR troca o
indicador IBE/EE por menção documental, fecha `DT-003EB-02`) · **1358 passed, 6 skipped, 0 failed**
*(MEDIDO, árvore parada, 724.85s — 1347 + 11 testes novos)* · `mypy --strict` alvo canônico
**limpo, 49 arquivos** · PROTOCOLO v96→**v97** · DECISOES v213→**v214** (notas em D-ARQ-59 e
D-ARQ-73; índice regenerado, 85 decisões). `medir_painel`: **`regras 26/45`** (R-BIO-05 é header
novo e está materializada — soma ao numerador e ao denominador), `cas 78/109`, `índice
sincronizado`. Escopo reduzido de BAIXO+IRRELEVANTE para só IRRELEVANTE por decisão do Diovanni,
depois da medição contra os 3 gabaritos (detalhe em `DT-003EB-02`). O bloqueador `cas 50/80` ×
`78/109` da tabela segue reportado, não ajustado.

**Baseline anterior `[MEDIDO — 24/09/2026, R-PKG-TRANSITO]`:** branch `claude/inspiring-turing-0ylkmk` sobre
`main 5977bf5` (merge do PR #366; IMPLEMENTAÇÃO — `R-PKG-TRANSITO`, risco de trânsito → acuidade +
audiometria 12M, parte de `DT-003EB-01` classe 4; fix da legenda colada ao último risco no parser)
· **1347 passed, 6 skipped, 0 failed** *(MEDIDO, árvore parada, 701.35s — 1343 + 4 testes novos; guarda de inventário 166→168 renomeada, não é teste novo)* · `mypy --strict` alvo canônico **limpo, 49 arquivos** · PROTOCOLO v95→**v96** ·
DECISOES v213 inalterado. `medir_painel`: `regras 25/44`, `cas 78/109` (+1 slug sem CAS,
`transito_via_publica`), `índice sincronizado`. **Achado do instrumento, não corrigido:** o regex de
ID (`R-[A-Z]+-[0-9]+`) não casa `R-PKG-*` — nenhum dos pacotes (`ATIVCRIT`, `SOLD`, `BZ`,
`TRANSITO`…) entra no numerador nem no denominador de `regras`; e uma citação em prosa de
`R-VIS-01` na `base_normativa` fez o numerador subir para 26 sem materialização — citação
retirada do YAML, mesma classe de `DH-003EC-01(b)`. O bloqueador `cas 50/80` × `78/109` da tabela
segue reportado, não ajustado.

**Baseline anterior `[MEDIDO — 24/09/2026, R-RX-01-qual]`:** branch `claude/inspiring-turing-0ylkmk` sobre
`main cadcd33` (merge do PR #365; IMPLEMENTAÇÃO — ramo `R-RX-01-qual`, sílica com avaliação
qualitativa P×S → RX OIT 12M, fecha `DT-003EC-01`) · **1343 passed, 6 skipped, 0 failed**
*(MEDIDO, árvore parada, 718.53s — 1334 + 9 testes novos)* · `mypy --strict` alvo canônico
**limpo, 49 arquivos** · PROTOCOLO v94→**v95** · DECISOES v212→**v213** (notas em D-ARQ-19 e
D-ARQ-49; índice regenerado, 85 decisões). `medir_painel`: `regras 25/44`, `cas 78/108`, `índice
sincronizado` — `regras` não move porque `R-RX-01-qual` é entrada de implementação da mesma ID
clínica `R-RX-01` (D-ARQ-20), não regra nova. O bloqueador `cas 50/80` × `78/108` da tabela segue
reportado, não ajustado.

**Baseline anterior `[MEDIDO — 24/09/2026, cache de FDS na tela]`:** branch `claude/inspiring-turing-0ylkmk`
sobre `main 0eef391` (merge do PR #364; memoização da transcrição de FDS em `web_matriz.py`, fecha
`DT-(sessão claude/inspiring-turing-0ylkmk)-01`) · **1334 passed, 6 skipped, 0 failed** *(MEDIDO,
árvore parada, 682.35s — 1331 + 3 testes novos)* · `mypy --strict` alvo canônico **limpo, 49
arquivos** · PROTOCOLO v94 e DECISOES v212 inalterados. Três números clínicos não re-tirados:
nenhuma `R-*` nem `.yaml` tocado (D-ARQ-85 cl.1).

**Baseline anterior `[MEDIDO — 23/09/2026, aliases produto + agente]`:** branch `claude/hopeful-newton-yjv3k7`
sobre `main 619a6ef` (merge do PR #362; 12 aliases em `agentes.yaml` `termos:`, 2 correções de
grafia no comparador, testemunha do T7 trocada) · **1331 passed, 6 skipped, 0 failed** *(MEDIDO,
árvore parada, 707.38s — 1317 + 14 testes novos)* · `mypy --strict` alvo canônico **limpo, 49
arquivos** · PROTOCOLO v94 (inalterado) · DECISOES v211→**v212** (nota de aplicação em D-ARQ-82;
índice regenerado, 85 decisões). `medir_painel`: `regras 25/44`, `cas 78/108`, `índice
sincronizado` — iguais à tiragem anterior (alias é forma, não slug; D-ARQ-85 cl.1). O bloqueador
`cas 50/80` × `78/108` da tabela segue reportado, não ajustado.

**Baseline anterior `[MEDIDO — 23/09/2026, alias + instrumento]`:** branch `claude/hopeful-newton-yjv3k7`
sobre `main 182a473` (merge do PR #361; alias `Poeira da madeira` em `agentes.yaml` `termos:` +
3 correções de `comparar_matriz_gabarito`/`medir_audiometria_dem`) · **1317 passed, 6 skipped,
0 failed** *(MEDIDO, árvore parada, 680.22s — 1312 + 5 testes novos)* · `mypy --strict` alvo
canônico **limpo, 49 arquivos** · PROTOCOLO v94 e DECISOES v211 inalterados. Três números
clínicos **não movidos por esta sessão**, medido nos dois lados: `python -m scripts.medir_painel`
em `main 182a473` (worktree isolado) e no working tree final dá o mesmo `regras 25/44 (57%)`,
`cas 78/108 (72%)`, `índice sincronizado` — alias é forma, não slug (D-ARQ-85 cl.1).
**`[BLOQUEADOR — reportado, não ajustado]`** a tabela "Os três números" e as tiragens acima ainda
citam `cas 50/80`; o instrumento dá `78/108` já em `182a473`, antes desta sessão (slugs de
composição-de-FDS de `DT-003M-02(A)`, 1ª e 2ª levas, segundo o comentário do guard de inventário
em `test_resolvedor_termos.py`). Re-tirada da tabela é decisão do Arquiteto.

**Baseline anterior `[MEDIDO — 23/09/2026, gate de numeração]`:** branch `claude/hopeful-newton-yjv3k7`
sobre `main 85003bc` (merge do PR #359; IMPLEMENTAÇÃO — gate de número de GHE saltado) ·
**1312 passed, 6 skipped, 0 failed** *(MEDIDO, árvore parada, 840.72s — 1307 + 5 testes novos)* ·
`mypy --strict` alvo canônico **limpo, 49 arquivos** · PROTOCOLO v94 (inalterado) · DECISOES
v210→**v211** (andamento em D-ARQ-57; índice regenerado, 85 decisões). Três números clínicos
**não re-tirados**: nenhuma `R-*` nem `.yaml` tocado (D-ARQ-85 cl.1).

**Baseline anterior `[MEDIDO — 23/09/2026]`:** branch `claude/hopeful-newton-yjv3k7` sobre `main 365b571`
(merge do PR #358; IMPLEMENTAÇÃO — forma 6 do repertório GHE + separação de cargos por CBO, fecha
`DT-(sessão claude/hopeful-newton-yjv3k7)-01`) · **1307 passed, 6 skipped, 0 failed** *(MEDIDO,
árvore parada, 853.93s — 1296 + 9 testes novos + 2 que falhavam por ambiente)* · `mypy --strict`
alvo canônico **limpo, 49 arquivos** · PROTOCOLO v94 (inalterado) · DECISOES v209→**v210**
(andamento em D-ARQ-57; índice regenerado, 85 decisões). Três números clínicos **não
re-tirados**: nenhuma `R-*` nem `.yaml` tocado (D-ARQ-85 cl.1).

**Baseline `[MEDIDO — 22/09/2026, parte 3]`:** branch `claude/nice-fermat-xahkji` sobre
`main 1f4e3f9` (merge do PR #355 — faixa dupla-desigualdade simétrica; esta sessão
IMPLEMENTOU um 3º fix na mesma área/mesma DT, código de produção tocado de novo; branch
restaurada de `origin/main` outra vez porque a PR anterior da mesma branch, #355, também já
estava mergeada) · **1295 passed, 6 skipped, 0 failed** *(MEDIDO nesta sessão, árvore
parada, 747.13s — delta **+3** exato contra o Baseline da parte 2 — 1292 — os 3 testes
novos desta parte)* · `mypy --strict` alvo canônico **limpo, 49 arquivos** *(MEDIDO nesta
sessão, delta-zero)* · PROTOCOLO v94 (inalterado) · DECISOES v207→**v208** (nota de
aplicação em D-ARQ-34 P1, nenhuma cláusula alterada; índice D-ARQ regenerado, 85 decisões,
contagem intacta).

**Deslize de processo, auto-reportado.** A 1ª tentativa de medir a suíte completa desta
parte (747.58s) achou **2 failed** — índice D-ARQ não regenerado antes da corrida
(esqueci `python -m scripts.gerar_indice_darq` após escrever a linha v208; cláusula fixa
do CLAUDE.md, precedente `c89f569`/003.EF e `973a343`/003.EG). Corrigido (índice
regenerado v207→v208) e suíte refeita do zero, limpa — o número acima é da 2ª corrida.

**Baseline da parte 2 `[MEDIDO — 21/09/2026, parte 2]`:** branch `claude/nice-fermat-xahkji` sobre
`main b75388d` (merge do PR #354 — fix do separador de faixa; esta sessão IMPLEMENTOU um 2º
fix na mesma área, código de produção tocado de novo; branch restaurada de `origin/main`
outra vez porque a PR anterior da mesma branch, #354, também já estava mergeada) ·
**1292 passed, 6 skipped, 0 failed** *(MEDIDO nesta sessão, árvore parada, 746.98s — delta
**+5** exato contra o Baseline da parte 1 — 1287 — os 5 testes novos desta parte; suíte
100% mockada, confirmado via `conftest.py::_sem_chave_de_api`, nenhuma chamada real ao
Gemini)* · `mypy --strict` alvo canônico **limpo, 49 arquivos** *(MEDIDO nesta sessão,
delta-zero)* · PROTOCOLO v94 (inalterado) · DECISOES v206→**v207** (nota de aplicação em
D-ARQ-34 P1, nenhuma cláusula alterada; índice D-ARQ regenerado, 85 decisões, contagem
intacta, `test_gerar_indice_darq.py`: 6 passed).

**Baseline da parte 1 `[MEDIDO — 21/09/2026]`:** branch `claude/nice-fermat-xahkji` sobre
`main d05b328` (merge do PR #353 — achado do gate de forma, docs-only; esta sessão
IMPLEMENTOU o fix, código de produção tocado; branch restaurada de `origin/main` nesta
sessão porque a PR anterior da mesma branch, #353, já estava mergeada) · **1287 passed, 6
skipped, 0 failed** *(MEDIDO nesta sessão, árvore parada, 764.80s — delta **+6** exato
contra o Baseline herdado de 003fh/`3ac98fc` — 1281 — os 6 testes novos desta sessão)* ·
`mypy --strict` alvo canônico **limpo, 49 arquivos** *(MEDIDO nesta sessão, delta-zero
contra 003fh/003fi)* · PROTOCOLO v94 (inalterado) · DECISOES v205→**v206** (nota de
aplicação em D-ARQ-34/D-ARQ-43, nenhuma cláusula alterada; índice D-ARQ regenerado, 85
decisões, contagem intacta). **Nota de proveniência:** entre este Baseline e o anterior
(v201, `64e744b`), cinco sessões de código/dado (v202-v205 + a validação ao vivo v203)
mergearam sem atualizar esta linha em disco — mesma classe de defasagem já registrada como
`DH-003FB-03` (ABERTA, Baseline envelhece por desenho entre re-tiragens de número clínico);
corrigido agora por ser esta sessão a próxima a produzir commit (D-ARQ-85 cl.2), não por ter
isolado a causa daquela DH.

> **Tiragem desta sessão, parte 2 `[MEDIDO — 16/09/2026]` (branch `claude/festive-gates-soy0fr`,
> IMPLEMENTAÇÃO — `R-RX-03`/`R-ESP-03`).** Suíte **1233 passed, 6 skipped, 0 failed**, árvore
> parada — `python -m scripts.medir_painel --suite`, commit pendente. Delta **+7** exato contra a
> parte 1 desta mesma sessão (`1226`): 4 testes novos (`agente_medico/tests/test_poeira_de_madeira.py`)
> + 3 parametrizados novos (`test_poeira_de_madeira_resolve_para_slug_proprio`); o guard de
> inventário foi renomeado de novo (`..._124_entradas` → `..._125_entradas`), mesmo teste, não conta
> como novo; um teste anti-FP existente (`test_poeira_de_madeira_anti_fp_segue_vocabulario_ausente`)
> foi reescrito para `test_poeira_de_madeira_nao_e_fracao_sem_agente` porque a asserção antiga
> (NAO_RESOLVIDO) descrevia exatamente o comportamento que esta sessão resolveu — troca registrada,
> não apagamento silencioso (D-ARQ-06), redação antiga preservada em HISTORICO. **Números clínicos
> se movem pela primeira vez desde 003.EZ:** `regras 23/42 → 25/44` pelo instrumento (55%→57%),
> `cas 50/79 → 50/80` (63%→62%, denominador cresce com o slug novo `poeira_de_madeira`, `cas: null`
> — numerador de CAS não muda), `índice: sincronizado`. `mypy --strict` alvo canônico limpo, 48
> arquivos, delta-zero. `DT-003EJ-01` RESOLVIDA (`docs/PENDENCIAS_CLINICAS.md`). Varredura inversa:
> `git stash` do código-fonte (mantendo os testes) derruba exatamente 7/7 testes novos, nada mais —
> restaurado e reconfirmado verde. Detalhe em HISTORICO (bloco desta sessão).

> **Tiragem desta sessão, parte 1 `[MEDIDO — 16/09/2026]` (branch `claude/festive-gates-soy0fr`, número não
> atribuído).** Suíte **1226 passed, 6 skipped, 0 failed** em `7c58d25`, árvore parada —
> `python -m scripts.medir_painel --suite`. Contra o Baseline escrito de 003.FL (`1223` em
> `96fd0ea`), delta **+3** exato: os 3 casos novos do teste parametrizado
> `test_pnos_por_extenso_resolve_para_poeira_nao_classificada` (achado 1); o guard de inventário foi
> renomeado (`..._123_entradas` → `..._124_entradas`), mesmo teste, não conta como novo.
> **Nota de container, não de código.** A medição em pré-merge desta mesma sessão (`pytest` puro,
> container anterior, sem o hook de reprovisionamento ter rodado ainda) viu **1224 passed, 6
> skipped, 2 failed** na mesma árvore de código — os 2 falhos eram ambiente sem `libreoffice-writer`
> (`test_varrer_acervo_lgpd.py`/`test_cobertura_varrer_acervo.py`), confirmados pré-existentes via
> `git stash` contra a árvore anterior a esta sessão (ver HISTORICO): `1223` (base 003.FL) `+ 3`
> (achado 1) `= 1226` testes não-`skip`; com o pacote ausente, 2 desses 1226 falham em vez de passar
> (`1224 passed + 2 failed = 1226`). O container atual trouxe `libreoffice-writer` pré-instalado
> pelo hook de sessão, os mesmos 2 testes passam aqui, e o total fecha em **1226 passed, 0 failed**
> — efeito de container, não de código; os 3 testes novos são os mesmos nas duas medições. Recorte que cobre os derivados tocados pelo achado 1
> (`test_resolvedor_termos`, `test_vocabulario`, `test_espirometria_poeira_mineral`,
> `test_rx_periodicidade`, `test_integracao_viverde`): **137 passed**, rodado à parte antes da suíte
> completa. `regras: 23/42 (55%)`, `cas: 50/79 (63%)`, `índice: sincronizado` — inalterados contra
> 003.FL. Detalhe (achados 1/2/3/4 da comparação Aurora Lago das Rosas, varredura inversa) em
> HISTORICO (bloco desta sessão).

> **Tiragem de 003.FL `[MEDIDO — 15/09/2026]`.** Suíte **1223 passed, 6 skipped** em `96fd0ea`,
> árvore parada — delta **+15** contra o Baseline escrito de 003.FK (`1208` em `d7bb344`), não
> decomposto entre os três merges não documentados (`#327`/`#328`/`#329`, nenhum tocando os arquivos
> de regra/vocabulário — ver nota da Tiragem corrente acima) e os **5** casos novos desta sessão
> (`test_sigla_pnos_pnor_resolve_para_poeira_nao_classificada`, parametrizado). Recorte que cobre os
> derivados tocados pelo achado 2 (`test_resolvedor_termos`, `test_vocabulario`,
> `test_espirometria_poeira_mineral`, `test_rx_periodicidade`, `test_integracao_viverde`): **134
> passed**, rodado à parte antes da suíte completa. `regras: 23/42 (55%)`, `cas: 50/79 (63%)`,
> `índice: sincronizado` — inalterados contra 003.FK. Detalhe (achados 2/4/5 da comparação Viverde,
> varredura inversa) em HISTORICO 003.FL.

> **Tiragem de 003.FK `[MEDIDO — 10/09/2026]`.** Duas medições na sessão, as duas com árvore
> parada. A primeira em `09d80dd` deu **1201 passed, 6 skipped, 0 failed**, `1207` coletados,
> 524.55s — delta-zero contra 003.FJ, esperado, porque `e0b8c9b..09d80dd` é docs-only. A segunda,
> que é a que este Baseline registra, na árvore de `d7bb344`: **1208 passed**, 504.25s, com
> `1201 + 7 = 1208` — os sete de `tests/test_ambiente_de_teste.py`.
>
> **As duas rodaram com o ambiente instalado à mão, antes de o hook existir.** O container não o
> trazia: faltavam `pytest`, `mypy`, `coverage`, `cffi` e o pacote `libreoffice-writer`, sem o qual
> `_texto_legado` falha em bloco. É o que a entrega 2 de 003.FK versionou. O tempo contra os
> 429.62s de 003.FJ é container diferente, não conjunto diferente.
>
> **O bloqueador do instrumento segue vivo e inalterado `[MEDIDO — 10/09/2026]`.**
> `python -m scripts.medir_painel` em `09d80dd` devolve `regras: 23/42 ativas (55%)` e
> `cas: 50/79 slugs (63%)` — os mesmos valores da nota acima. A tabela continua **não ajustada
> para bater**, e qual regra explica o `+1` continua `[A MEDIR]`.

> **Delta de 003.FI para 003.FJ: `+32` exato `[MEDIDO — 003.FJ]`.** `1175` coletados em `4d1bc01`
> mais **30** de `tests/test_varrer_acervo_lgpd.py` e **2** do portão de cobertura
> `tests/test_cobertura_varrer_acervo.py` = **1207**, e `1201 + 6 = 1207`.
> Progressão por rodada do Gauntlet: **10** na entrega (`4c86f18`), **13** no 1º gap (`cc62333`,
> destino do texto extraído), **14** no 3º (`9b0d496`, exclusão medida × tamanho de lista), **16**
> no 4º (`4d85c35`, classes coletadas sem caminho de saída), **19** no 5º (`b4580d5`, os três
> ramos de falha de `varrer()`), **21** no 6º (`dc77b28`, dois dos três ramos de
> `extrair_metadata_autoria`) e **32** no fecho de classe (`3fb98e2`, portão de cobertura: o script
> passa de 91% para **100%**, com o único `# pragma: no cover` declarado e conferido por teste).
> Cada rodada somou teste, e o Baseline nomeia o commit de cada medição.
> `skipped` inalterado em 6; nenhum vermelho em nenhuma das duas pontas. O script novo vive em
> `scripts/`, fora do alvo canônico do `mypy` — medido em separado, limpo, 1 arquivo.
>
> **Os 8 vermelhos sumiram, e a causa nomeada por 003.FH era a certa `[MEDIDO — 003.FI]`.**
> O PR #322 levou `matrizes_originais/` de **17 para 83 arquivos** rastreados. Os **8** arquivos do
> acervo referenciados pelos testes passam a existir em disco, conferidos um a um. Medidos por
> casamento de **nome de arquivo do acervo contra o texto dos testes**, com normalização NFC — e não
> por `git grep` de caminho literal, que mede literais de string e não aberturas: em
> `tests/test_regressao_pcmso.py:168` o caminho é montado partido
> (`ROOT / "matrizes_originais" / "…"`) e escapa ao grep (`Correção 003.FI-C2`).
> A tiragem foi de **1145/8/21** para **1169/6/0** sem uma linha de código mudar entre as duas.
>
> **A reconciliação é por coletados, que é invariante a ambiente:** `1166` (003.FE e a tiragem de
> partida de 003.FH, idênticos) `+ 8` (fatia 003.FH) `+ 1` (correção 003.FH-C3) = **1175**, e
> `1169 + 6 = 1175`. Nenhum teste criado ou perdido em nenhum ponto da cadeia. O `1160 passed,
> 6 skipped @ deed9f6` deixa de ser "o único número de acervo completo" — agora há um medido no
> repositório, e ele é reproduzível por quem clonar.
>
> `DH-003FH-02` **FECHADA** por esta medição. `DH-003ET-01` (fixtures de PDF não versionadas) segue
> ABERTA: a classe não foi resolvida, só deixou de se manifestar neste acervo.

**Três números clínicos avaliados, não re-tirados nesta tiragem** — 003.FE é IMPLEMENTAÇÃO de apresentação: nenhuma R-* criada, alterada ou depreciada; vocabulário/CAS intocado; as 3 dívidas que travam produção seguem as mesmas. Nenhum dos três se moveu. Decisão declarada sob `D-ARQ-85` cl.1.

---

## Os três números

| Pergunta | Estado medido | Leitura |
|---|---|---|
| Quanto da regra clínica está no código? | **24 de 44** ativas pelo instrumento (55%) — **23 pela intenção do painel**, medido por `scripts/medir_painel.py` | Movimento 22→24 (instrumento) e 21→23 (intenção) na sessão atual: `R-RX-03`/`R-ESP-03` CRIADAS (poeira de madeira, DT-003EJ-01 RESOLVIDA) — as duas somam ao numerador **e** ao denominador igualmente (regras plenamente executáveis, não citação em prosa). A folga de `+1` entre instrumento e esta tabela **persiste, não fechada por esta sessão** — ver nota `[MEDIDO — 16/09/2026]` acima do Baseline. Histórico anterior: movimento 23→22 (instrumento) e 22→21 (intenção) desde 003.EX: `R-AUD-04` sai `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]` (D-ARQ-81) — fundamento (matriz-precedente n=2) refutado pela varredura de 23 obras de `DT-003EY-01` (universalidade 7/23). Denominador caiu 43→42 na mesma sessão — o instrumento ignora header cuja linha contém "DEPRECATED" (`_ids_ativos_protocolo`) |
| A porta de entrada existe? | **Lado-FDS (química) CONSTRUÍDO e validado ao vivo** end-to-end (extração→LLM→gate→revisão-RT→montagem→resolvedor, 003.BD-BI); lado-PGR **CONSTRUÍDO e PLUGADO em produção** — `processar_arquivo_pgr` (D-ARQ-52, 003.BS) costura arquivo→Resultado fim-a-fim (extração→recorte→transcrição-LLM→gate→hidratação→motor), validado contra o PDF Viverde real (LLM mockado em teste); **perigo-transcrição implementada** (recorte B, D-ARQ-55/003.CJ: `frases_h` verbatim por-membro → revisão-RT → `Componente` → mapa {H334,H317}→`is_sensibilizante`; sensibilizante in-vocab <5% já vira MATERIAL; CAS-oculto carrega a flag; **passo 2 implementado** — D-ARQ-56/003.CK: bypass antes do slug-check, sensibilizante de CAS-oculto → MATERIAL + `bypass_sem_slug` bloqueante, inerte-declarado sem slug não-bloqueante) | Gargalo de produção migrou de novo: não é mais travessia — é **universalidade** (**superfície RT COMPLETA — D-ARQ-54 FECHADA (4/4)**: CLIs 003.CE/CF + contrato unificado 003.CG + web Streamlit 003.CL, pacote `superficie/`; D-ARQ-57 COMPLETO (peças 1–3, 003.CO/CP/CQ + peça 4 fatias 4a-4d, 003.DD–003.DK): localizador + gate de segmentação + família cargo-based + recorte/transcrição/roteamento de card cargo-based; EBSERH-vigente (rede federal de HUs) INGERE em produção (e2e UFGD, rota card); HUMAP/Cjr/Ricco-Adm gated by design → revisão humana (DT-003DK-01); DT-003CS-01 FECHADA) + a rasura do vocabulário químico |
| Dívidas que travam produção? | **3** — mesmas facetas de sempre, recontadas pós-fechamento | DT-003L-01 (parse-PGR), DT-003M-02(A) (vocabulário-FDS raso — (B) FECHADA em 003.CK), DT-FDS-02 (unidade do cutoff); DT-003CM-01 **FECHADA em 003.CQ** (insumo do parse-PGR consumido integralmente por D-ARQ-57, 1ª leva 3/3); DT-003CS-01 **FECHADA em 003.DK** (EBSERH ingere pela rota card); DT-003DK-01 **ABERTA em 003.DK**, **não-bloqueante** (fronteira-fim do último span — gated by design vai a revisão humana, não trava ingestão); DT-003DR-01 **FECHADA em 003.DS** (reconhecedor aceita separador U+0000; medição determinística Fascino: 19 âncoras, rota ghe, densidade sem pendência); DT-003DS-01 **ABERTA em 003.DS**, não-bloqueante (GHE sem número pág. 89, faceta de DT-003L-01) |

**Instrumento oficial nesta tiragem (disco, branch `docs/003ez-fechamento` sobre `main a8bb4d1`):** regras **23/43→22/42** ativas pelo instrumento (53%→52%) / **22/43→21/42** pela intenção do painel — `R-AUD-04` sai `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]` (D-ARQ-81, D-ARQ-68 cl.5); **denominador cai junto** (43→42) porque o instrumento ignora header `DEPRECATED` por desenho (`_ids_ativos_protocolo`). Previsão do prompt de fechamento (23/43 → 22/42) confirmada pelo instrumento (`python -m scripts.medir_painel`, sem ajustar para bater). · vocabulário/CAS **50/79** slugs (63%), **inalterado** · índice D-ARQ **sincronizado** — regenerado nesta sessão (DECISOES v172→v173, correção de rótulo + fechamento; contagem de decisões intacta em 81; carimbo `Fonte:` mudou v172→v173, ver lição de método 003.EZ) · suíte **1137 passed, 6 skipped** (`--suite`, árvore parada, `a8bb4d1`), inalterada desde `010abbe` (docs-only); `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py app_matriz.py app_matriz_local.py` limpo, **48 arquivos**, inalterado.

**Headline:** a produção **não está travada por falta de regra clínica, nem mais pelo transcritor-FDS, nem mais pela travessia do parse-PGR** (lado-químico fim-a-fim construído e validado ao vivo, 003.BH/BI; lado-PGR plugado em produção arquivo→Resultado, D-ARQ-52/003.BS) — está travada por **universalidade do parse-PGR** (transcrição-de-topo do envelope COMPLETA — D-ARQ-53, 4/4 fatias prontas (recorte `recortar_topo` 003.BU + contrato `EnvelopeVerbatim`/`TranscritorTopo`/`gate_forma_topo` 003.BW + resolvedor `resolvedor_topo.py`/seam `revisao_envelope.py` 003.BX + plug `preparar_envelope` em `processar_arquivo_pgr` 003.BY) + **cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV); origem de `validade`/`assinatura_engenheiro` agora document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado no nível do adaptador; **superfície RT COMPLETA — D-ARQ-54 FECHADA (4/4)** (CLIs 003.CE/CF + contrato 003.CG + web Streamlit 003.CL, pacote `superficie/`); resta peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); D-ARQ-57 COMPLETO (1ª leva 3/3 — repertório + gate + família cargo-based, 003.CO/CP/CQ); peça 4 COMPLETA (recorte+transcrição+roteamento cargo-based, 003.DD–003.DK; EBSERH ingere, DT-003CS-01 FECHADA)) e por **índice CAS/vocabulário químico raso** (a maioria dos componentes de FDS real ainda cai em ramo 0/AUSENTE por falta de slug, DT-003M-02). Nenhuma regra clínica nova move essa restrição. **003.CJ:** a rasura do vocabulário começou a ser contornada por dentro — a FDS agora declara o perigo direto ao motor (frases-H→flag, sem depender de slug para o sinal); **003.CK (D-ARQ-56) converteu o sinal em saída:** sensibilizante de CAS oculto → MATERIAL + `bypass_sem_slug` bloqueante nomeando as frases-H; carga inerte sem slug deixou de travar o GHE (não-bloqueante, R-FDS-06). DT-003M-01 e DT-003M-02(B) FECHADAS; exame ainda não dispara no CAS-oculto (promoção-sem-slug = DT-003CK-01, condicionada a regra clínica de sensibilizante genérico). **003.CL fechou a superfície RT** (D-ARQ-54 4/4: web envelope+FDS em Streamlit, adaptador irmão das CLIs sobre o mesmo contrato de artefato). **003.DD–003.DK (peça 4 de D-ARQ-57):** o parse-PGR deixou de ser Viverde-pontual — GHE-based, N:1 e card cargo-based (EBSERH/saúde) roteiam e ingerem; o que não ingere bloqueia nomeado para revisão humana (anti-supressão), nunca silencioso. **003.DR (D-ARQ-62):** foco redirecionado para Marco 1 via caso-âncora real (Fascino, construção civil como sequenciamento); 1ª medição bloqueou nomeado em `topo_ausente` (DT-003DR-01) — a fila passa a ser pautada pelos achados de medição. **003.DS:** separador U+0000 do Fascino corrigido (DT-003DR-01 fechada); a ingestão determinística do Fascino atravessa (19 âncoras, rota ghe, segmentação sem pendência) — o próximo instrumento é a rodada ao vivo com LLM. **003.EB:** 1ª rodada e2e real OFFLINE (Fascino 19/19 determinístico, zero invocação LLM) + diff contra a matriz humana — Marco 1 instrumentado; lacuna dominante medida = pacote-base clínico (DT-003EB-01, ~190 de ~194 células).

---

## CAMADA 1 — Diretoria · início, meio, fim

### Onde estamos, em uma frase
O **motor que decide os exames** (a partir de risco já estruturado) está ~41% construído e testado na espinha. Do lado da **porta de entrada**, o lado-FDS (química) está **construído e validado ao vivo, fim-a-fim** (PDF→extração de texto→transcritor-LLM→gate de forma→revisão-RT→montagem→resolvedor, 003.BD a 003.BI). O lado-PGR está **construído e PLUGADO em produção**: `adaptadores/orquestracao_pgr.py::processar_arquivo_pgr` (D-ARQ-52, 003.BS) costura arquivo→Resultado fim-a-fim (extração `extrair_texto_pgr` → recorte `recortar_blocos_ghe` → transcrição-LLM `transcrever_ghes`/`gate_forma_ghe` + `TranscritorGeminiGHE` → resolvedor `resolvedor_termos` → hidratação `hidratar_pgr` → motor `processar_pgr`), validado contra o PDF Viverde real (LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV): origem de `validade`/`assinatura_engenheiro` agora document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado no nível do adaptador. Falta para **universalidade**: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); D-ARQ-57 COMPLETO (1ª leva 3/3 — repertório + gate + família cargo-based, 003.CO/CP/CQ); peça 4 COMPLETA (recorte+transcrição+roteamento cargo-based, 003.DD–003.DK; EBSERH ingere, DT-003CS-01 FECHADA) (hoje Viverde-pontual; superfície RT COMPLETA — D-ARQ-54 FECHADA 4/4, web 003.CL) — e o vocabulário químico ainda raso (a maioria dos componentes de FDS real cai em ramo 0/AUSENTE por falta de slug em `agentes.yaml`, DT-003M-02) — juntos, o que ainda separa o sistema de rodar qualquer PGR real de ponta a ponta.

### A decisão que a diretoria precisa tomar
Hoje a fila assume "continuar a frente clínica" por inércia. O painel torna a escolha informada:

| Caminho | Entrega | **Não** entrega |
|---|---|---|
| **A — continuar clínica** | Cobertura 19 de 42; fecha camada de dedup | Não move o gargalo; PGR e2e segue impossível |
| **B — virar para extração** ⟵ *ratificado (22/06)* | Constrói a porta de entrada; destrava o 1º PGR real | Clínica congela em ~41% temporariamente |

**Recomendação: caminho B.** O motor de decisão já é load-bearing e testado; a restrição que prende o valor de produção é a ingestão ausente, e nenhuma cobertura clínica adicional a remove. Ponto de pausa da clínica é limpo — a camada de dedup foi selada nesta semana (D-ARQ-39).

> **Status da decisão:** **RATIFICADA pela diretoria (22/06).** Caminho B selado como decisão de processo (linha DECISOES v56 + esta tiragem), não D-ARQ numerado — sequenciamento de trabalho, não contrato de motor. Frente clínica pausada em ~41% num ponto limpo (D-ARQ-39 selou o dedup).

### "Quanto falta" — slice map medido (003.AH, atualizado 003.BI)
O subsistema de ingestão foi medido de disco. A sub-camada **química** (FDS→composição→Risco) tem **todo o encanamento determinístico construído e costurado** — e desde 003.BD-BI ganhou a **camada de transcrição real fim-a-fim**: `extrair_texto_fds` (003.BE) → `TranscritorGemini`/`transcrever_fds` (003.BF/BG) → `gate_forma` (003.BF) → revisão-RT `revisao_verbatim.montar_fds_revisado` (003.BI) → `montar_fds`/`resolver_composicao` (003.BC/W). Validada AO VIVO 3/3 contra `fds_t65` (003.BH). Ainda **sem chamador de produção** plugado (CLI/Streamlit) — `executar_com_composicao`/`montar_fds_revisado` seguem só em teste/harness.

Gargalos restantes, em massa crescente:

| Gargalo | Natureza | Estado |
|---|---|---|
| Índice CAS raso | Dado | **50 de 80 slugs com CAS** (62%, medido por `scripts/medir_painel.py`; denominador subiu de 79 na sessão atual com o slug novo `poeira_de_madeira`, `cas: null`; substitui a medição manual 003.AI de 21/45, obsoleta desde 003.EC) |
| `name→slug` (string química sem CAS → slug) | Decisão de arquitetura | Indeciso (D-ARQ-36 Parte 1) |
| Superfície da revisão-RT | **COMPLETA — D-ARQ-54 FECHADA (4/4)** | CLIs (003.CE/CF) + contrato unificado (`apresentacao.py` 003.CG) + web Streamlit (`web_envelope.py`/`web_fds.py` 003.CL); adaptador FDS sem emissor do artefato-ida em produção (remanescente 003.CF, fora do escopo da D-ARQ) |
| Parse de PGR (esqueleto GHE/cargo/risco físico) | Plugado em produção; universalidade em aberto | arquivo→Resultado CONSTRUÍDO e PLUGADO (`processar_arquivo_pgr`, D-ARQ-52, 003.BS; travessia Viverde real fechada, LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY; origem document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV). Resta para universalidade: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); D-ARQ-57 COMPLETO (1ª leva 3/3 — repertório + gate + família cargo-based, 003.CO/CP/CQ); peça 4 COMPLETA (recorte+transcrição+roteamento cargo-based, 003.DD–003.DK; EBSERH ingere, DT-003CS-01 FECHADA) + população de aliases `termos:` (dado); superfície RT COMPLETA (D-ARQ-54 4/4, web 003.CL) |

**Fatia 1 da extração (popular CAS) parcialmente cumprida** (003.AI: 12 substâncias). Falta plugar a costura ao pipeline real (fatia A) e o parse-PGR (maior massa). Número corrigido nesta tiragem (003.EC): a medição manual 003.AI (21/45, 23/06/2026) estava defasada 5 sessões contra o instrumento — número medido de disco por `scripts/medir_painel.py` é **50/79** (63%).

### Nota — a própria gestão à vista depende de B
Enquanto a ingestão não existir, este painel só pode mostrar **métricas internas** (cobertura de regra, DTs) — não **valor de produção** (PGRs rodados, matrizes validadas pela coordenadora clínica). O caminho B não só destrava produção; **destrava o próprio instrumento que a diretoria pediu.** A gestão à vista plena (PGR real no painel) nasce com o Marco 1.

---

## CAMADA 2 — Engenharia e arquitetura · malha rastreável

### Cobertura clínica — por superfície de disco
Instrumento: `git grep` de IDs de regra. Mede **rastreabilidade** (string presente), não consumo em runtime. Convenção: família `R-RX-01` (`-adm/-sem/-baixa/...`) = **1 ID** com variantes.

- **Denominador:** 44 IDs ativos no PROTOCOLO (header = status; `R-AUD-04` sai — `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]`, D-ARQ-81; `R-RX-03`/`R-ESP-03` entram — CRIADAS na sessão atual, `DT-003EJ-01` RESOLVIDA; 42→44). Medido por `scripts/medir_painel.py` (003.DE), instrumento oficial desde então.
- **Numerador (instrumento):** 24 IDs casados por `git grep` de `R-[A-Z]+-[0-9]+` em `regras.yaml` ∪ `motor/*.py` — **24/44 (55%)**.
- **Numerador (intenção do painel):** 23 IDs com footprint **executável** — R-TEMP-01 sai (citação em prosa de `base_normativa`, sem `quando`/`emite`, não roda; ver DH-003EC-01(b)) — **23/44 (52%)**.

| Superfície | n | IDs |
|---|---|---|
| `regras.yaml` (dado) | 14 | AUD-01/02, BIO-04, CLI-01, CLI-02, ESP-02/03, FDS-04, PSY-02, RX-01/02/03, VIB-01/02 |
| `regras.yaml` (citação em prosa, sem `quando`/`emite` — não executa) | 1 | TEMP-01 |
| `motor/*.py` (lógica) | 14 | BIO-04, ESP-02/03, FDS-03, FDS-06, GHE-01/02/03, PGR-01/04/06, RUIDO-01, RX-01/03 |
| `tests/*` (teste por-ID) | 14 | AUD-01/02, BIO-04, ESP-03, FDS-06, GHE-02, PGR-01/04/06, RUIDO-01, RX-01/03, VIB-01/02 |
| `protocolo/*.py` | 0 | pasta sem lógica por-ID |
| `agentes.yaml` `protocolos_especiais` (dado, sem consumidor em runtime — fora do numerador) | 3 | ECG-01, OP-01, VIS-01 |
| **União (instrumento)** | **24** | 55% de 44 |
| **União (intenção do painel, exclui TEMP-01)** | **23** | 52% de 44 |

**Caveat de instrumento (não superinterpretar):** num loader data-driven, regra em `regras.yaml` é funcional **sem** string no motor. Os 24 (ou 23) são **piso de rastreabilidade**, não teto de função. E, desde 003.EC, o instrumento também não distingue `id:` de citação em prosa dentro do mesmo arquivo — ver DH-003EC-01(b).

- **yaml-only** (dado existe, zero match em motor/teste): CLI-01, CLI-02, FDS-04, RX-02 — 4 IDs, candidatas a backfill de teste, **não** mortas. `R-RX-03`/`R-ESP-03` (novas) NÃO entram nesta lista — `test_poeira_de_madeira.py` casa os dois IDs por `git grep`, cobertura própria desde a criação
- **motor-only** (lógica fora de yaml/teste por-ID): FDS-03, GHE-01, GHE-03 — 3 IDs
- **20 IDs** sem ocorrência em `agente_medico/` — só-escritas (44 ativos − 24 no instrumento)

**Re-tiragem sessão atual (branch `claude/festive-gates-soy0fr`):** `R-RX-03`/`R-ESP-03` CRIADAS por IMPLEMENTAÇÃO (`regras.yaml` `id: R-RX-03`/`id: R-ESP-03` + `motor/predicados.py::_poeira_de_madeira`, DT-003EJ-01 RESOLVIDA) — 22→24 no instrumento, 21→23 na intenção do painel; denominador 42→44 (sobe junto, as duas são regras ativas novas, não substituem nada). Teste próprio (`test_poeira_de_madeira.py`, 4 testes) cobre as duas por-ID, incluindo o teste anti-confusão com R-ESP-02.

**Re-tiragem 003.EZ:** `R-AUD-04` sai `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]` (D-ARQ-81) — 23→22 no instrumento, 22→21 na intenção do painel; denominador 43→42 (cai junto, header `DEPRECATED` excluído de `_ids_ativos_protocolo`). `R-AUD-01`/`R-AUD-02` seguem ativas — a saída do `DEM` migra para presunção protetiva sob essas duas (D-ARQ-68 cl.5), sem regra nova; `AUD-04` sai das listas `regras.yaml` e `tests/*` acima, corpo do arquivo preservado.

**Re-tiragem 003.EI:** R-ESP-02 entra por IMPLEMENTAÇÃO (`regras.yaml` `id: R-ESP-02` + `motor/predicados.py::_pnos`, D-ARQ-69) — 20→21 no instrumento, 19→20 na intenção do painel. Verificado de disco (não assumido): R-ESP-01 — DEPRECATED, citado na `base_normativa` de R-ESP-02 — **não** entra no numerador, porque o filtro de header do instrumento (`_ids_ativos_protocolo`) descarta qualquer ID cujo header contenha "DEPRECATED" antes de casar contra `ids_codigo`; checado por script (`R-ESP-01 in ativos` = `False`, `R-ESP-01 in interseção` = `False`). R-TEMP-01 segue o único caso vivo da classe DH-003EC-01(b).

**Re-conferência 003.BI:** mesmo método (`git grep` de header vs. `regras.yaml`/`motor/*.py`) reaplicado sobre o disco atual. Único commit em dado clínico desde 003.AH é `0d5f786` (003.AI, popula `cas` em 12 substâncias — não mexe em `protocolos_especiais`/ID de regra). Sessões 003.AI→003.BI foram todas extração (caminho B). **17/41 inalterado — frente clínica pausada (caminho B).**

**Re-conferência 003.CJ:** R-FDS-06 ganha footprint executável em `motor/*.py` (`mapear_frases_h`, PR #190) e teste-por-regra (`test_mapa_frases_h.py`) — união desta tabela 17→18; somada a R-RUIDO-01 (003.CC, posterior à tabela), o número-1 do topo vai a 19/42. Tabela detalhada não re-medida linha a linha até 003.DE.

**Re-tiragem 003.EC:** R-CLI-01 entra por IMPLEMENTAÇÃO (`regras.yaml` + primitivo `todo_trabalhador`, D-ARQ-66, 4 testes falha-sem/passa-com) — 18→19. R-TEMP-01 entra pelo instrumento por CITAÇÃO na `base_normativa` de R-CLI-01, não por footprint executável — 19→20 no instrumento, mas a intenção do painel (regra que roda) fica em **19**. Ver DH-003EC-01(b) para a correção candidata do instrumento (casar só o campo `id:`).

**Re-tiragem 003.DE→003.DK (`scripts/medir_painel.py`, instrumento oficial):** medição direta de disco expôs **drift de rótulo** herdado das re-conferências manuais — a linha "`regras.yaml` (dado)" citava R-ECG-01/R-OP-01/R-VIS-01, que nunca estiveram em `regras.yaml` (zero grep em `motor/` também); vivem só em `agentes.yaml` campo `protocolos_especiais`, superfície de dado sem consumidor em runtime, agora linha própria e **fora do numerador**. Entram no numerador R-CLI-02 (003.CU, `regras.yaml`) e R-GHE-01 (003.DD, `motor/extracao_pgr.py`, header N:1 D-ARQ-57 peça 4a). Resultado líquido: **18/42** (~43%), medido nesta tiragem (003.DK) contra `main a249ea5`.

### Estado da extração — binário, por capacidade
18 módulos no motor, **todos pós-estruturação**.

| Capacidade que destrava produção | Estado |
|---|---|
| Sub-camada química FDS→Risco (determinística) | **Construída e costurada, isolada** — sem chamador de produção (gate_cas 003.S/T → resolver_composicao 003.W → wrapper+propagação 003.Z; materialidade 003.J; 4ª fonte 003.P) |
| Transcrição LLM da FDS + revisão-RT (D-ARQ-47) | **CONSTRUÍDA e validada AO VIVO fim-a-fim** — `extrair_texto_fds` (003.BE) → `TranscritorGemini` real (003.BG) → `gate_forma` (003.BF) → `revisao_verbatim.montar_fds_revisado` (003.BI, cl.4) → `montar_fds`/`resolver_composicao`; 3/3 `@requer_api` passed vs. `fds_t65` (003.BH). **Fecha DT-003AS-01.** Sem chamador de produção plugado (CLI/Streamlit) — só harness/teste |
| Superfície da revisão-RT (onde o RT edita o verbatim) | **COMPLETA — D-ARQ-54 FECHADA (4/4)** — CLIs (003.CE/CF) + contrato unificado (003.CG) + web Streamlit (`web_envelope.py`/`web_fds.py`, 003.CL) sobre serializar/desserializar_verbatim; emissor do artefato-ida no adaptador ainda ausente (remanescente 003.CF) |
| Índice CAS (`construir_indice_cas`) | **50/80 slugs com CAS** (62%, medido por `scripts/medir_painel.py`; denominador 79→80 na sessão atual, slug novo `poeira_de_madeira` com `cas: null`) — substitui a medição manual 003.AI (21/45), obsoleta desde 003.EC |
| Resolução canônica `name→slug` (string química → slug de agente) | **0 código** — decisão de arquitetura não tomada (D-ARQ-36 Parte 1); única `def` de normalização é `leo_resolver.py:37 _normaliza`, escopo LEO-texto, não vocabulário químico |
| Parse de PGR bruto → `tipos.PGR` (esqueleto GHE/cargo/risco físico) | **arquivo→Resultado CONSTRUÍDO e PLUGADO em produção** — `adaptadores/orquestracao_pgr.py::processar_arquivo_pgr` (D-ARQ-52, 003.BS, PR #162) costura extração→recorte→transcrição-LLM→gate→hidratação→motor num só chamador; primeiro e2e real do projeto (PDF Viverde, LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY; origem document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, PR #176, validado ao vivo 4/4 contra o gabarito 003.BV). Falta para **universalidade**: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); D-ARQ-57 COMPLETO (1ª leva 3/3 — repertório + gate + família cargo-based, 003.CO/CP/CQ); peça 4 COMPLETA (recorte+transcrição+roteamento cargo-based, 003.DD–003.DK; EBSERH ingere, DT-003CS-01 FECHADA) (Viverde-pontual); superfície RT COMPLETA (D-ARQ-54 4/4, 003.CL) |

Toda menção a "slug" em produção é **uso de campo** (lookup direto), não função dedicada.

### DTs — triagem contra "fecha 1 PGR e2e com matriz correta"

| Bloqueia produção | Higiene / fechada / feature-scoped |
|---|---|
| **DT-003L-01** — mapa 6 formas de declaração química → input D-ARQ-25 | DT-003AS-01 — **FECHADA (003.BI)**, cadeia FDS completa |
| **DT-003M-02** — vocabulário não cobre composição-de-FDS | DT-003M-01 — resolvida por design (003.P) |
| **DT-FDS-02** — unidade cutoff 5% (bloqueia *correção*, não *rodar*) | DT-003T-01 — fechada por recorte |
| | DT-003AE-01 — biomonitoramento deferido |
| | DT-003BG-01 — gabarito 3/6 (Leinertex/Massa/Amanco), não-bloqueante |
| | DT-003AW-01 — grafia-de-ausente `\n`, não-medida, não-bloqueante |
| | DH-003P-01 / DT-003Y-01 — resíduo sem-slug (edge) |
| | DH-003M-01 / DH-003A-01 — corrupção/cosmético de markdown |
| | DT-003CS-01 — **FECHADA (003.DK)**, EBSERH ingere |
| | DT-003DK-01 — fronteira-fim do último span, não-bloqueante (gated→revisão humana) |
| | DT-003DL-01 — REENQUADRADA/DEFERIDA (003.DP), campos sem consumidor |

**Convergência crítica (recontada pós-fechamento DT-003AS-01):** ainda **3** dívidas travam produção — DT-003L-01, DT-003M-02, DT-FDS-02 — mas a natureza da restrição migrou de novo: não é mais "falta transcritor-FDS" (fechado 003.BI) nem "falta a travessia do parse-PGR" (fechada 003.BS, D-ARQ-52) — é "falta universalidade do parse-PGR (envelope document-derived + âncora multi-PGR) + vocabulário químico populado". Não são débitos independentes — são facetas do mesmo subsistema de ingestão (D-ARQ-25 + `name→slug` + vocabulário de composição-FDS).

### Risco de retrabalho de B — considerado e descartado
Construir extração contra camada clínica incompleta → retrabalho se `R-CLI-*` mudar a forma do que a extração produz. **Descartado:** a saída da extração (input estruturado de agente/risco) é a montante e **ortogonal** à convergência `R-CLI-*` (dedup/periodicidade, a jusante). Contrato de saída não depende de `R-CLI-*` estar pronto. Bônus: clínica retomada depois valida `R-CLI-*` contra **PGR real, não fixture**.

---

## CAMADA 3 — Marcos · critério de pronto + gate de aceite

### Marco 1 — 1 PGR real end-to-end (matriz correta)
**Pronto =** um PGR nomeado roda de **arquivos brutos** (PGR + FDSs) até matriz GHE×exame **sem estruturação manual**, e a **coordenadora clínica valida a matriz de exames de saída**.

- **Gate de aceite clínico:** a validação clínica entra **aqui** — sobre a matriz que sai, não sobre cobertura de regra interna. Olho clínico opera sobre output real, a jusante.
- **Insumos materiais:** D-ARQ-25 parse-PGR (transcrição-FDS já entregue, D-ARQ-47/003.BI), `name→slug` canônico, **modelos de matriz de risco** (contrato de saída da extração), **normas vigentes gov.br/MTE** (ancoram a derivação), DT-003M-02 fechada, DT-FDS-02 confirmada, UI da revisão-RT plugada.
- **Estado:** **bloqueado pela universalidade do parse-PGR + vocabulário químico** — a travessia arquivo→Resultado já fecha (Viverde real, D-ARQ-52/003.BS), o envelope document-derived já tem cliente-LLM real (`TranscritorGeminiTopo`, 003.CA), mas falta superfície RT (UI/CLI) + generalização multi-PGR da âncora (lado-FDS já construído e validado ao vivo) — é o que o caminho B ainda constrói.

### Marco 2 — motor-sombra no Streamlit
**Pronto =** para N inputs reais, saída do motor novo capturada ao lado do legado (`agente_medico_ia.py`), diff visível, sem regressão no legado.

- **Sombra parcial** (input estruturado à mão, só consumo): **alcançável hoje** — motor de consumo roda e é testado.
- **Sombra pleno** (PGR bruto → matriz): depende do Marco 1.

---

## Achados-META da tiragem 003.AG (drift memória×disco)
1. **DT-003Y-02 não existe** em disco — não é typo de 002Y-02 (sessão diferente); o `02` da lista de handoff foi escrito de memória sem lastro. Removida do rastreio.
2. **Denominador travado em 42** — o ±1 anterior era erro de contagem manual, não defeito de disco (`comm -3` confirmou header = status).
3. **DH-003M-01 ao vivo** — `\r\n` literal apareceu na saída de grep desta coleta. **4ª instância** da classe de corrupção de markdown na gravação de docs do Code → gatilho de META própria de higiene disparado.

---

## Próximos passos
1. ~~**003.AI (DADO):** popular `cas: null` de `agentes.yaml`~~ — **parcialmente cumprido** (12 substâncias, 003.AI); restam 24 null.
2. ~~**Transcritor-FDS + revisão-RT**~~ — **CUMPRIDO** (003.BE-BI, D-ARQ-47); DT-003AS-01 fechada.
3. ~~**2ª fatia do parse-PGR — recorte determinístico dos blocos GHE**~~ — **CUMPRIDO** (003.BM, `recortar_blocos_ghe`, D-ARQ-49 P2).
4. ~~**3ª fatia do parse-PGR — transcritor-LLM do bloco GHE (esqueleto)**~~ — **CUMPRIDO** (003.BN, `GHEVerbatim`/`RiscoVerbatim` + `transcrever_ghes` + `gate_forma_ghe`, D-ARQ-49 P3/D-ARQ-50 C3; LLM sempre mockado).
5. ~~**4ª fatia do parse-PGR — cliente-LLM real do transcritor-GHE**~~ — **CUMPRIDO** (003.BO, `TranscritorGeminiGHE`, molde `TranscritorGemini`/D-ARQ-48; validado ao vivo contra o Viverde, PR #152).
6. ~~**5ª fatia do parse-PGR — resolvedor determinístico termo→slug**~~ — **CUMPRIDO** (003.BP, `resolvedor_termos.py`, D-ARQ-50 P2; PR #154).
7. ~~**6ª/7ª/8ª fatia do parse-PGR — hidratação (1a contrato de tipo + 1b `hidratar_ghe`) + costura plural `hidratar_pgr` + plug de produção arquivo→Resultado**~~ — **CUMPRIDO** (003.BQ 1a: `RiscoPGR.agente` Optional[str] + guard, D-ARQ-51 seams 2/3, PR #156; 003.BQ 1b: `hidratar_ghe`, seams 1/4, PR #158; 003.BR: costura plural `hidratar_pgr`, PR #160; 003.BS: plug de produção `processar_arquivo_pgr`, D-ARQ-52, PR #162). Travessia Viverde arquivo→Resultado fecha fim-a-fim (LLM mockado em teste). **Resta para universalidade:** transcrição-de-topo do envelope + peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); D-ARQ-57 COMPLETO (1ª leva 3/3 — repertório + gate + família cargo-based, 003.CO/CP/CQ); peça 4 COMPLETA (recorte+transcrição+roteamento cargo-based, 003.DD–003.DK; EBSERH ingere, DT-003CS-01 FECHADA).
8. ~~**Cliente-LLM real do topo do envelope**~~ — **CUMPRIDO** (003.CA, `TranscritorGeminiTopo` em `adaptadores/transcritor_gemini_topo.py`, molde `TranscritorGeminiGHE`/D-ARQ-53; validado ao vivo 4/4 contra o gabarito 003.BV, PR #176). D-ARQ-53 fecha "cliente real ✓"; **superfície RT COMPLETA (D-ARQ-54 FECHADA 4/4 — contrato 003.CG, web 003.CL)**.
9. **Fatia A:** plugar `executar_com_composicao`/`montar_fds_revisado` no pipeline real (CLI/Streamlit), sobre índice CAS populado.
10. **`name→slug`:** decisão de arquitetura a tomar (D-ARQ-36 Parte 1) — destrava agentes sem CAS atômico.
11. **META higiene DH-003M-01:** 4ª recorrência de markdown cru, ainda pendente.

---

**Nota de escopo desta tiragem (003.DQ — META).** Re-tiragem obrigatória de META: números re-medidos pelo instrumento oficial + suíte no host; critério de numerador selado (DECISOES v140). O refresh integral da prosa longa da Camada 1, prometido na tiragem 003.DK "para a próxima META", foi DEFERIDO DE NOVO por decisão explícita desta sessão — paliativo sinalizado, não esquecimento: a prosa acumula estados 003.BI→003.DK e será reescrita numa passada dedicada, não como apêndice de fechamento.

**Nota de escopo desta tiragem (003.DX — META).** Sessão focada no gate de abertura, não em código de motor. **D-ARQ-63** redesenha o gate em dois níveis (nível 1 sempre integral — PROTOCOLO + índice + transversais D-ARQ-06/09/22; nível 2 por eixo nomeado); novo artefato derivado `docs/INDICE_DARQ.md` (`scripts/gerar_indice_darq.py`) entra no ritual de abertura a partir desta sessão. **DT-003DX-01** (migrar acreção pós-decisão do DECISOES para satélites `docs/darq/`) e **DT-003DX-02** (a regra do gate mora fora do git, em `CLAUDE.md` do projeto Cowork, não versionado) abertas, ambas não-bloqueantes. Três PRs: #255 (índice, peça 1), #256 (D-ARQ-63 + DT-003DX-01/02, docs), #257 (fix — Status de subseção `### ` aninhada vazava para o D-ARQ dono do bloco, alcance 1/63). O refresh integral da prosa longa da Camada 1 foi DEFERIDO pela **terceira** vez (003.DK → 003.DQ → 003.DX) — sem autorização explícita do Diovanni neste turno; a contagem visível é o que impede virar dívida silenciosa.

**Nota de escopo desta tiragem (003.ED — pós-merge do PR de `feat/003ed-altura-atividade-critica`, `main 513f486`).** Regras (20/42) e vocabulário/CAS (50/79) **inalterados** — 003.ED não criou regra clínica nem slug novo, só alias Tier 1 de termo (`trabalho_altura.termos`, índice de resolução 105→106) e substituição do primitivo órfão `maquina_pesada` por `motorista_equipamento_pesado` em `atividade_critica` (**D-ARQ-67 criada** — literal de vocabulário em código de motor é contrato verificado por teste computado do dado, não lista digitada). **DT-003ED-01** (grafia natural com preposição não resolve contra slug sem preposição — atinge R-VIB-01/02 e a perna de máquina pesada) e **DH-003ED-01** (relatório do harness `rodar-offline` não carrega o gatilho por linha nem os slugs resolvidos por GHE) abertas no PROTOCOLO §11 (v70). Nenhum dos três números do painel se move nesta tiragem.

**Nota de escopo desta tiragem (003.EI — FECHAMENTO, branch `feat/003ei-fechamento-docs` sobre `main 6edee2c`, PR #272 já mergeado).** Regras: **20/42 (48%) → 21/42 (50%)** pelo instrumento, **19/42 → 20/42** pela intenção do painel — R-ESP-02 materializada (`regras.yaml` + `motor/predicados.py`, D-ARQ-69), R-ESP-01 sucedida e corretamente excluída do numerador (header `DEPRECATED`, verificado de disco, não assumido). Vocabulário/CAS **50/79 (63%) inalterado** — 003.EI populou `termos:` de vocabulário (silica/asbesto/poeira_nao_classificada), não o campo `cas`. Índice D-ARQ **sincronizado** (regenerado nesta tiragem, `python -m scripts.gerar_indice_darq`, DECISOES v157→v158, D-ARQ-69 nova). Suíte **984→990 passed, 6 skipped** (medida no fechamento da fatia 1, árvore parada); `mypy --strict` delta-zero, 34 arquivos. **Baseline desta tiragem não é o merge desta própria branch** — o hash `pós-merge do fechamento` pedido pelo prompt de fechamento não existe ainda (o PR desta branch depende de aprovação do Diovanni); usei `main 6edee2c` (última fusão real, já contém R-ESP-02) mais as versões reais de PROTOCOLO/DECISOES desta branch (v78/v158) — divergência sinalizada, não escolhida em silêncio (cláusula de CLAUDE.md). Correção aritmética de passagem: "23 IDs sem ocorrência" (linha da Camada 2) não fechava contra 42−20; recalculado para 21 (=42−21) nesta tiragem.

**Nota de escopo desta tiragem (003.EN — CONHECIMENTO → IMPLEMENTAÇÃO → MEDIÇÃO, branch `feat/003en-psicossocial` sobre `main a04986e`, PR #277 já mergeado).** Regras: **21/42 (50%) → 22/42 (52%)** pelo instrumento, **20/42 → 21/42** pela intenção do painel — R-PSY-02 materializada (`regras.yaml`, incondicional via `todo_trabalhador`, D-ARQ-66), sucede R-PSY-01 (agora `[DEPRECATED]`, corretamente excluído do denominador antes de entrar, checado por script — nova instância de DH-003EC-01(b)). Fecha a classe (4) de DT-003EB-01 (gatilho satisfeito: 2º grupo de PGRs atualizados no acervo, 6 documentos pós-26/05/2026, 5 clientes, 2 médicas, 99% de cobertura em 284 cargos contra ~0% em 13 documentos anteriores). Vocabulário/CAS **50/79 (63%) inalterado** — 2 slugs de exame novos em `exames.yaml` (`avaliacao_psicossocial`, `avaliacao_saude_mental`), sem campo `cas` aplicável (categoria `ocupacional`, não `laboratorial`). Índice D-ARQ **sincronizado, inalterado** — esta sessão não cria D-ARQ, não toca `DECISOES_ARQUITETURAIS.md`, não dispara regeneração. Medição contra o gabarito Fascino (`rodar-offline`, `relatorios/003en_fascino_rodar.md`, gitignored): linhas de exame **133→171** (+2 em cada um dos 19 GHEs, aritmética fechada); status **3 VÁLIDA / 15 PARCIAL / 1 BLOQUEADA**, inalterado; GHE-06 (Administração, BLOQUEADA) e GHE-19 (Vendas, VÁLIDA) passam a receber os 2 exames incondicionais sem mudar de status (D-ARQ-66 cl.2, tri-estado computa sobre `linhas_com_risco`); total de pendências **154, inalterado** (a regra não lê risco); bloco "inspecionar primeiro" (D-ARQ-72) não-vazio em **14/19 → 19/19** GHEs; contagem de status por motivo: VALIDADO **130, inalterado**, DERIVADO **14 → 52** (+38). Todas as 7 previsões do prompt de abertura bateram com a medição — nenhum bloqueador. Suíte **1025→1027 passed, 6 skipped** (+2 testes novos); `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. PROTOCOLO v82→v83 (R-PSY-02 criada em §5.7, R-PSY-01 marcada `[DEPRECATED]`, corpo preservado; DT-003EB-01 classe (4) FECHADA, classes (2)/(3) seguem ABERTAS).

**Nota de escopo desta tiragem (003.EO + EMENDAs 1-4 — IMPLEMENTAÇÃO + MEDIÇÃO, branch `feat/003eo-emissor` sobre `main 2b7efe4`, PR #278 já mergeado).** Os três números do painel **não se movem** — 003.EO é sessão de apresentação-de-saída (emissor Word/HTML), não de regra clínica nem de extração/porta-de-entrada. Regras: **22/42 (52%) / 21/42 inalterado**, nenhuma R-* tocada. Vocabulário/CAS: **50/79 (63%) inalterado**. Entregue: `agente_medico/superficie/documento_matriz.py` — estrutura intermediária única (`DocumentoMatriz`) + `renderizar_html`/`renderizar_docx`, expansão GHE→cargo (R-GHE-01/D-ARQ-21), ordem de exibição cravada em `exames.yaml` (`ordem_exibicao`, decisão do Arquiteto na EMENDA 1). `MatrizGHE` ganha `nome_ghe`/`cargos` aditivos (fatia 1). **D-ARQ-73 CRIADA** (índice regenerado, DECISOES v161→v162). Quatro DTs abertas no PROTOCOLO §11 (v83→v84): DT-003EO-01 (cabeçalho/rodapé sem casa no modelo), DT-003EO-02 (grafia Glicemia/RX indecisa, D-ARQ-06), DT-003EO-03 (clínico semestral do pacote Mn — ganhou parágrafo R-BIO-03 verificado por grep como não-materializável sem o slug de manganês), **DT-003EO-04** (refinada nas EMENDAs 3-4: duas facetas — (a) concatenação cosmética, (b) perda silenciosa por quebra de linha, medida em **6/41 cargos perdidos, 2/19 GHEs** — GHE-03 e GHE-06; **fecha em `003.EP`**, não nesta sessão; header não-bloqueante para o motor mas explicitamente "o S2 não fecha sem ela"). Medição contra o Fascino real (fatia 4): tabela da EMENDA 1 confirmada **exatamente** — 12/19 GHEs com exames idênticos, 4 células de superemissão (GHE-10/16), 10 de subemissão (GHE-06/08/09/17/19); achados de periodicidade confirmados (RX 12M×24M em 14 GHEs, clínico 6M×12M em GHE-09/17). Bloqueador original da fatia 0 do prompt (contagem de cargos do gabarito, 40/37) **retirado** pela EMENDA 1 — medição do Code (41 linhas, todas reais) aceita, causa (parser do Arquiteto) nomeada. `docs/PLANO_V1.md` migrado da pasta do Cowork e corrigido em 5 pontos (EMENDA 3) — o mais grave, a premissa de superemissão "6/GHE em 16 GHEs" (`[A MEDIR]` desde 003.EG), estava descrita ao contrário e foi marcada REFUTADA. **S2 permanece parcialmente entregue** (emissores prontos; expansão correta mas sem efeito em produção até DT-003EO-04 fechar) — nunca "concluído". Suíte **1027→1039 passed, 6 skipped** (+12 testes novos), medida com árvore parada; `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, 42 arquivos (novo baseline — comando passou a incluir `superficie/` pela 1ª vez, não é crescimento não-contabilizado). Três commits: `9bb3839` (código), `d826f46` (docstring), commit de docs a seguir. Corrige resíduo herdado da tiragem 003.EN: o hash do merge, antes "pendente", é `2b7efe4` (PR #278).

**Nota de escopo desta tiragem (003.EP fatias 0-4 — MEDIÇÃO → IMPLEMENTAÇÃO → FECHAMENTO, branch `feat/003ep-celula-cargo` sobre `main d3de91e`, PR ainda não aberto/aprovado).** Regras: **22/42 (52%) / 21/42 inalterado** — nenhuma R-* criada, alterada ou depreciada; 003.EP é sessão de parser/apresentação, não de regra clínica. Vocabulário/CAS: **50/79 (63%) inalterado** — `cargos.yaml` não foi tocado (fora do escopo, `riscos.py`/`cargos.yaml` explicitamente não tocados nesta sessão). Entregue: **DT-003EO-04 FECHADA** nas duas facetas (PROTOCOLO §11) — célula "Cargo / Função" passa a render 1 nome por cargo (CBO descartado), os 6 cargos perdidos por quebra de linha física chegam a `GHEPGR`; evidência = gate nominal 0 divergências (41 nomes) + e2e real (41 `LinhaCargo`, `test_documento_matriz.py`). **D-ARQ-65 Cláusula 5 NOVA** (DECISOES v163) — bloco da família é formulário de 2 colunas fixas, `x0` idênticos bit-a-bit nos 19/19 blocos; não abriu D-ARQ nova (extensão de recorte medido). Três dívidas novas no PROTOCOLO §11 (v84→v85): **DT-003EP-01** (R-GHE-02 inalcançável em produção — `cargos_vocab.get(cargo)` sem resolver, pendências medidas 19→41; não é conserto de passagem, muda conduta clínica) e **DT-003EP-02** (dois caminhos de silêncio remanescentes no parser, não exercitados no Fascino), ambas ABERTAS não-bloqueantes; **DH-003EP-01** (`_sanitizar` apaga glifo-hífen no documento assinado), higiene de instrumento. Medição de não-regressão contra o Fascino real (`relatorios/003ep_fascino_rodar.md` vs. `003eo_fascino_rodar.md`): linhas de exame **171→171**, status por GHE **idêntico nos 19/19** — único movimento é a pendência não-bloqueante R-GHE-02 (efeito colateral esperado de cargos reais chegarem ao vocabulário, não regressão de conduta). `docs/PLANO_V1.md`: **S2 fecha** — tabela de sequência atualizada, ressalva de cabeçalho/rodapé preservada (seam humano por desenho, D-ARQ-73 cl.5/DT-003EO-01, resolve no S3); S3 marcado próximo da fila; S0 (hospedagem) segue não decidido, risco de prazo. Suíte **1039→1048 passed, 6 skipped** (+9 testes — 3 fatia 1, 5 fatia 2, 1 fatia 3), medida com árvore parada; `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, **42 arquivos**, mesmo baseline de 003.EO. Três commits de código/teste (`aaa9eca`, `486d54d`, `7f19cf4`) + commit de docs a seguir. **Hash de merge não gravado** — a sessão não conhece o hash de um merge que ainda não aconteceu; esta tiragem usa o hash real do topo da branch (`7f19cf4`), não um placeholder nem um valor fabricado. **Correção retroativa (003.EQ, 04/08/2026):** o merge aconteceu e o hash é conhecido — `9867e5f` (PR #280). 3ª recorrência da classe "hash de merge desconhecido registrado como tal, corrigido só na tiragem seguinte" — a correção é esta linha.

**Nota de escopo desta tiragem (003.EQ — IMPLEMENTAÇÃO + MEDIÇÃO → FECHAMENTO, branch `feat/003eq-app-matriz` sobre `main 9867e5f`, PR #280 já mergeado).** Regras: **22/42 (52%) / 21/42 inalterado** — nenhuma R-* criada, alterada ou depreciada; 003.EQ é sessão de superfície de aplicação, não de regra clínica. Vocabulário/CAS: **50/79 (63%) inalterado**. Entregue: **S3 fatia 1** — `superficie/web_matriz.py`, app de upload PGR → envelope → processa (rota determinística, zero LLM) → matriz na tela → download HTML/DOCX. **D-ARQ-74 CRIADA** (DECISOES v163→v164, índice 73→74) — superfície que emite artefato assinável lê `resultado.status` e nunca emite documento sem conteúdo clínico; caso-âncora: `Resultado(status="REJEITADO", matrizes=[])` do gate R-PGR-01 produzia documento assinável vazio (187 bytes de HTML, zero `<w:tbl>` no DOCX), medido em dois ambientes independentes. Quatro dívidas novas no PROTOCOLO §11 (v85→v86): **DH-003EQ-01** (preservação-em-download sem cobertura automatizada — `AppTest` não expõe `download_button`, lacuna de ferramenta), **DT-003EQ-01** (lixo de recorte/transcrição vazando como termo de agente, faceta de DT-003L-01), **DT-003EQ-02** (`Maganês`→`manganes` recusado pelo fuzzy, D-ARQ-64 correto por desenho, custo clínico real), **DT-003EQ-03** (`PRELIMINAR` não marcado no documento assinado, irmã de DT-003EO-01). Nota aditiva em DH-003EP-01 (glifo-hífen confirmado na saída real) e DT-003EO-04 (fechamento confirmado em produção real). Violação de método autodeclarada: uma rodada de suíte foi medida concorrente com mutação de arquivo durante varredura inversa — rodadas limpas subsequentes confirmaram ausência de defeito real, registrada por disciplina de processo. **Verificação manual (Diovanni, host real, upload nativo, 04/08/2026):** primeira fatia do S3 validada contra o Fascino real — 19 GHEs, 41 cargos com assinatura marcada; banner de rejeição sem downloads sem assinatura. O defeito que essa verificação pegou (documento vazio assinável, fechado por D-ARQ-74) **não era detectável pela suíte**, que estava 1059 verde com o defeito vivo — a cobertura automatizada por si só não teria pego este bloqueador. Suíte **1048→1062 passed, 6 skipped** (+14 testes: 2 emenda 1, 3 emenda 2, 3 emenda 3, mais os herdados do move de transcritores offline), medida com árvore parada; `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, **43 arquivos** (+1, `web_matriz.py`). `docs/PLANO_V1.md`: S3 passa de "não começou" para "fatia 1 entregue"; S0 ganha nota aditiva com as duas perguntas respondidas pelo Diovanni (uso interno, nuvem de terceiro permitida), confirma a recomendação de adiar hospedagem. Quatro commits de código/teste (`1eb32af`, `380fe59`, `5a0d02e`, `4b0a541`) + commit de docs a seguir.

**Nota de escopo desta tiragem (003.EX fatias 0-1 — MEDIÇÃO + IMPLEMENTAÇÃO, branch `feat/003ex-medicao-audiometria-dem` sobre `main 64b9b84`, PR ainda não aberto/aprovado).** Primeiro gatilho de re-tiragem desde 003.EQ — 003.ER-EW não moveram nenhum dos três números (plumbing de transcrição/casca/docs). Regras: **22/42 (52%) → 23/43 (53%)** pelo instrumento, **21/42 → 22/43** pela intenção do painel — **R-AUD-04 CRIADA** (`regras.yaml`, piso universal de audiometria via `todo_trabalhador`, D-ARQ-66; NR-07 Anexo II 4.1 `[DERIVADO]` crava 12M+adm+dem, universo estendido a todo trabalhador e MRO incluído são `[INTERPRETADO]`, apoiados em matriz-precedente da fatia 0). **Denominador sobe 42→43** — R-AUD-04 é aditiva, não sucede nenhum ID (diferente do padrão R-PSY-01→R-PSY-02, que manteve o denominador estável); `R-AUD-01`/`R-AUD-02`/`R-AUD-03` não tocadas. Vocabulário/CAS: **50/79 (63%) inalterado**. Fatia 0 (medição, sem código de produção): instrumento `scripts/medir_audiometria_dem.py` + `docs/referencia/GABARITO_003EX_audiometria_dem.md` (extração versionada, `relatorios/` é gitignored) — corrige a contagem herdada de 003.EI (40→41 cargos no SPE 0030, corroborado por teste pré-existente do pacote). Efeito medido no Fascino (`rodar-offline`, "antes" via `git worktree` isolado): GHEs com audiometria **17/19 → 19/19** (17/19 é a medição fresca desta sessão — diverge do "16/19" herdado de `DT-003EG-01`; causa nomeável, não baseline cega: a diferença é GHE-12/Betoneira, que passou a emitir audiometria em 003.EJ por `R-VIB-02`/aliases D-ARQ-70; 16+1=17); linhas de exame **171 → 173** (+2, GHE-06 Administração e GHE-19 Vendas ganham a linha nova — os dois GHEs que a fatia 0 identificou como fora do pacote de atividade crítica); linhas de audiometria com `DEM` **1/17 → 19/19**; status **3 VÁLIDA / 15 PARCIAL / 1 BLOQUEADA inalterado, confirmado GHE a GHE** (D-ARQ-66 cl.2). **DT-003EW-01 FECHADA** (reenquadrada como 3ª manifestação de `ruido_acima_acao = Ausente`, junto com DT-003EG-01 e o caso GHE-16 de D-ARQ-71 — fecha a saída, não a raiz); **DT-003EG-01 segue ABERTA**, nota aditiva; **DH-003EX-01 CRIADA** (ABERTA, higiene de instrumento — heurística de forma no extrator não testada contra 3+ grupos). **Nenhum D-ARQ novo** — `docs/DECISOES_ARQUITETURAIS.md` não tocado, índice **sincronizado, inalterado**; candidato registrado, não decidido: "quando precedente de corpus setorialmente enviesado autoriza universalizar" (prematuro com n=1 caso, os dois gabaritos medidos são ambos construção civil). Suíte **1099→1104 (fatia 0)→1108 passed, 6 skipped** (+9: 5 do instrumento de medição, 4 de R-AUD-04 — mais 4 quebras legítimas de teste de integração corrigidas com reporte nomeado, precedente `R-CLI-01` 963→967); `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py app_matriz.py app_matriz_local.py` limpo, **48 arquivos**, inalterado. Commits: `39e2caa`/`cad5987`/`70ad4a6`/`5b3f59f` (fatia 0), `24992d5` regra+testes/`bf2ed58` docs (fatia 1).

**Nota de escopo desta tiragem (003.EZ — FECHAMENTO, branch `docs/003ez-fechamento` sobre `main a8bb4d1`, PR #300+#301 já mergeados).** Gatilho: `R-AUD-04` sai `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora]` (D-ARQ-81, D-ARQ-68 cl.5) — move os 3 números clínicos, dispara re-tiragem. Regras: **23/43 (53%) → 22/42 (52%)** pelo instrumento, **22/43 → 21/42** pela intenção do painel — previsão do prompt de fechamento (23/43 → 22/42) confirmada pelo instrumento, não copiada. Denominador cai junto (43→42) porque `_ids_ativos_protocolo` ignora header `DEPRECATED` por desenho — a regra sai do numerador **e** do denominador ao mesmo tempo, não só do numerador. `R-AUD-01`/`R-AUD-02` seguem `[VALIDADO]`, ativas — a saída do `DEM` migra para presunção protetiva sob essas duas (D-ARQ-68 cl.5), sem `R-AUD-05` nem qualquer regra nova. Vocabulário/CAS: **50/79 (63%) inalterado**. Índice D-ARQ: **regenerado, mudou** — carimbo `Fonte:` v172→v173 (correção de rótulo em v171 "na fatia 2"→"no Commit 2 da fatia 1"; sessão só teve fatias 0, 0b e 1); contagem de decisões intacta em **81**. A previsão do prompt de fechamento ("índice não deve mudar") estava errada — o carimbo deriva da tabela de revisões por desenho do gerador, embora a tabela seja excluída do conteúdo do índice; divergência reportada e não ajustada, decisão do Diovanni de manter v173 e seguir (ver lição de método, HISTORICO 003.EZ). Suíte **1137 passed, 6 skipped** (`python -m scripts.medir_painel --suite`, árvore parada, `a8bb4d1`), inalterada desde `010abbe` — sessão é docs-only a partir daí (EMENDA 1 + fechamento não tocam motor). `mypy --strict` alvo canônico limpo, **48 arquivos**, inalterado. Detalhe completo (fatias, PRs, conferência normativa D-ARQ-69, medições Fascino/23-obras, 8 lições de método) em HISTORICO_OPERACIONAL.md, bloco 003.EZ.

---
*Gestão à vista. Vive ao lado da produção, não a substitui. Próxima tiragem: ao próximo merge que mover um número, fechamento de marco, ou sessão META.*
