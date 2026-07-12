# Painel de Estado — Projeto Agente Médico PCMSO
### Gestão à vista · estado corrente do produto

> **Painel vivo, não foto datada.** Mostra o estado corrente medido de disco (git), não estimativa.
> **Como este painel se mantém vivo (cadência de atualização):** re-tirado **por evento, nunca por calendário** —
> (1) a cada merge em `main` que move um dos três números abaixo, (2) em todo fechamento de marco,
> (3) no mínimo 1× por sessão META. Merge que não move número não dispara re-tiragem.
> A re-tiragem é passo do ritual de fechamento já existente (mesmo gate de disco — custo marginal ~zero).
> O `HISTORICO_OPERACIONAL.md` acumula os snapshots; este painel mostra só o presente.

---

**Tiragem corrente:** 003.CP · 11/07/2026
**Baseline:** main `81e9a9b` · 769 passed, 4 skipped · mypy `--strict` sem erro novo (46 pré-existentes em arquivos de teste — dívida de higiene anotada 003.CJ) · PROTOCOLO v52 · DECISOES v113

---

## Os três números

| Pergunta | Estado medido | Leitura |
|---|---|---|
| Quanto da regra clínica está no código? | **19 de 42** ativas (~45%) | R-FDS-06 entra no numerador (003.CJ: `mapear_frases_h` materializa a nota de aplicação — frase-H da FDS confiada por default → `is_sensibilizante`, docstring carrega o ID); antes dela, R-RUIDO-01 (003.CB/CC). Pausa da frente clínica segue vigente — ambas foram puxadas pela porta de entrada, não retomada da frente |
| A porta de entrada existe? | **Lado-FDS (química) CONSTRUÍDO e validado ao vivo** end-to-end (extração→LLM→gate→revisão-RT→montagem→resolvedor, 003.BD-BI); lado-PGR **CONSTRUÍDO e PLUGADO em produção** — `processar_arquivo_pgr` (D-ARQ-52, 003.BS) costura arquivo→Resultado fim-a-fim (extração→recorte→transcrição-LLM→gate→hidratação→motor), validado contra o PDF Viverde real (LLM mockado em teste); **perigo-transcrição implementada** (recorte B, D-ARQ-55/003.CJ: `frases_h` verbatim por-membro → revisão-RT → `Componente` → mapa {H334,H317}→`is_sensibilizante`; sensibilizante in-vocab <5% já vira MATERIAL; CAS-oculto carrega a flag; **passo 2 implementado** — D-ARQ-56/003.CK: bypass antes do slug-check, sensibilizante de CAS-oculto → MATERIAL + `bypass_sem_slug` bloqueante, inerte-declarado sem slug não-bloqueante) | Gargalo de produção migrou de novo: não é mais travessia — é **universalidade** (**superfície RT COMPLETA — D-ARQ-54 FECHADA (4/4)**: CLIs 003.CE/CF + contrato unificado 003.CG + web Streamlit 003.CL, pacote `superficie/`; resta peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor) + a rasura do vocabulário químico |
| Dívidas que travam produção? | **3** — mesmas facetas de sempre, recontadas pós-fechamento | DT-003L-01 (parse-PGR), DT-003M-02(A) (vocabulário-FDS raso — (B) FECHADA em 003.CK), DT-FDS-02 (unidade do cutoff) |

**Headline:** a produção **não está travada por falta de regra clínica, nem mais pelo transcritor-FDS, nem mais pela travessia do parse-PGR** (lado-químico fim-a-fim construído e validado ao vivo, 003.BH/BI; lado-PGR plugado em produção arquivo→Resultado, D-ARQ-52/003.BS) — está travada por **universalidade do parse-PGR** (transcrição-de-topo do envelope COMPLETA — D-ARQ-53, 4/4 fatias prontas (recorte `recortar_topo` 003.BU + contrato `EnvelopeVerbatim`/`TranscritorTopo`/`gate_forma_topo` 003.BW + resolvedor `resolvedor_topo.py`/seam `revisao_envelope.py` 003.BX + plug `preparar_envelope` em `processar_arquivo_pgr` 003.BY) + **cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV); origem de `validade`/`assinatura_engenheiro` agora document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado no nível do adaptador; **superfície RT COMPLETA — D-ARQ-54 FECHADA (4/4)** (CLIs 003.CE/CF + contrato 003.CG + web Streamlit 003.CL, pacote `superficie/`); resta peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor) e por **índice CAS/vocabulário químico raso** (a maioria dos componentes de FDS real ainda cai em ramo 0/AUSENTE por falta de slug, DT-003M-02). Nenhuma regra clínica nova move essa restrição. **003.CJ:** a rasura do vocabulário começou a ser contornada por dentro — a FDS agora declara o perigo direto ao motor (frases-H→flag, sem depender de slug para o sinal); **003.CK (D-ARQ-56) converteu o sinal em saída:** sensibilizante de CAS oculto → MATERIAL + `bypass_sem_slug` bloqueante nomeando as frases-H; carga inerte sem slug deixou de travar o GHE (não-bloqueante, R-FDS-06). DT-003M-01 e DT-003M-02(B) FECHADAS; exame ainda não dispara no CAS-oculto (promoção-sem-slug = DT-003CK-01, condicionada a regra clínica de sensibilizante genérico). **003.CL fechou a superfície RT** (D-ARQ-54 4/4: web envelope+FDS em Streamlit, adaptador irmão das CLIs sobre o mesmo contrato de artefato).

---

## CAMADA 1 — Diretoria · início, meio, fim

### Onde estamos, em uma frase
O **motor que decide os exames** (a partir de risco já estruturado) está ~41% construído e testado na espinha. Do lado da **porta de entrada**, o lado-FDS (química) está **construído e validado ao vivo, fim-a-fim** (PDF→extração de texto→transcritor-LLM→gate de forma→revisão-RT→montagem→resolvedor, 003.BD a 003.BI). O lado-PGR está **construído e PLUGADO em produção**: `adaptadores/orquestracao_pgr.py::processar_arquivo_pgr` (D-ARQ-52, 003.BS) costura arquivo→Resultado fim-a-fim (extração `extrair_texto_pgr` → recorte `recortar_blocos_ghe` → transcrição-LLM `transcrever_ghes`/`gate_forma_ghe` + `TranscritorGeminiGHE` → resolvedor `resolvedor_termos` → hidratação `hidratar_pgr` → motor `processar_pgr`), validado contra o PDF Viverde real (LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV): origem de `validade`/`assinatura_engenheiro` agora document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado no nível do adaptador. Falta para **universalidade**: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor (hoje Viverde-pontual; superfície RT COMPLETA — D-ARQ-54 FECHADA 4/4, web 003.CL) — e o vocabulário químico ainda raso (a maioria dos componentes de FDS real cai em ramo 0/AUSENTE por falta de slug em `agentes.yaml`, DT-003M-02) — juntos, o que ainda separa o sistema de rodar qualquer PGR real de ponta a ponta.

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
| Índice CAS raso | Dado | **21 de 45 slugs com CAS** (47%; 003.AI populou 12, restam 24 null — várias por categoria física sem CAS aplicável) |
| `name→slug` (string química sem CAS → slug) | Decisão de arquitetura | Indeciso (D-ARQ-36 Parte 1) |
| Superfície da revisão-RT | **COMPLETA — D-ARQ-54 FECHADA (4/4)** | CLIs (003.CE/CF) + contrato unificado (`apresentacao.py` 003.CG) + web Streamlit (`web_envelope.py`/`web_fds.py` 003.CL); adaptador FDS sem emissor do artefato-ida em produção (remanescente 003.CF, fora do escopo da D-ARQ) |
| Parse de PGR (esqueleto GHE/cargo/risco físico) | Plugado em produção; universalidade em aberto | arquivo→Resultado CONSTRUÍDO e PLUGADO (`processar_arquivo_pgr`, D-ARQ-52, 003.BS; travessia Viverde real fechada, LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY; origem document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, validado ao vivo 4/4 contra o gabarito 003.BV). Resta para universalidade: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor + população de aliases `termos:` (dado); superfície RT COMPLETA (D-ARQ-54 4/4, web 003.CL) |

**Fatia 1 da extração (popular CAS) parcialmente cumprida** (003.AI: 12 substâncias). Falta plugar a costura ao pipeline real (fatia A) e o parse-PGR (maior massa). Número corrigido nesta tiragem: o "9/43" citado nas sessões 003.BG-BI já estava defasado pela 003.AI (23/06/2026) — medido de disco (`agente_medico/protocolo/vocabulario/agentes.yaml`) como 21/45 nesta re-tiragem.

### Nota — a própria gestão à vista depende de B
Enquanto a ingestão não existir, este painel só pode mostrar **métricas internas** (cobertura de regra, DTs) — não **valor de produção** (PGRs rodados, matrizes validadas pela coordenadora clínica). O caminho B não só destrava produção; **destrava o próprio instrumento que a diretoria pediu.** A gestão à vista plena (PGR real no painel) nasce com o Marco 1.

---

## CAMADA 2 — Engenharia e arquitetura · malha rastreável

### Cobertura clínica — por superfície de disco
Instrumento: `git grep` de IDs de regra. Mede **rastreabilidade** (string presente), não consumo em runtime. Convenção: família `R-RX-01` (`-adm/-sem/-baixa/...`) = **1 ID** com variantes.

- **Denominador:** 42 IDs únicos no PROTOCOLO (header = status, `comm -3` diff vazio, travado). Fração usa **41 ativas** (exclui `R-BIO-02` DEPRECATED).
- **Numerador:** 17 IDs com footprint executável (`regras.yaml` ∪ `motor/*.py`).

| Superfície | n | IDs |
|---|---|---|
| `regras.yaml` (dado) | 11 | AUD-01/02, BIO-04, ECG-01, FDS-04, OP-01, RX-01, RX-02, VIB-01/02, VIS-01 |
| `motor/*.py` (lógica) | 7 | FDS-03, GHE-02/03, PGR-01/04/06, RX-01 |
| `tests/*` (teste por-ID) | 9 | AUD-01/02, GHE-02, PGR-01/04/06, RX-01, VIB-01/02 |
| `protocolo/*.py` | 0 | pasta sem lógica por-ID |
| **União (materializado)** | **17** | ~41% de 41 |

**Caveat de instrumento (não superinterpretar):** num loader data-driven, regra em `regras.yaml` é funcional **sem** string no motor. Os 17 são **piso de rastreabilidade**, não teto de função.

- **yaml-only** (dado existe, zero match em motor/teste): BIO-04, ECG-01, FDS-04, OP-01, RX-02, VIS-01 — 6 IDs, candidatas a backfill de teste, **não** mortas
- **motor-only** (lógica fora de yaml/teste por-ID): FDS-03, GHE-03 — 2 IDs
- **24 IDs** sem ocorrência em `agente_medico/` — só-escritas

**Re-conferência 003.BI:** mesmo método (`git grep` de header vs. `regras.yaml`/`motor/*.py`) reaplicado sobre o disco atual. Único commit em dado clínico desde 003.AH é `0d5f786` (003.AI, popula `cas` em 12 substâncias — não mexe em `protocolos_especiais`/ID de regra). Sessões 003.AI→003.BI foram todas extração (caminho B). **17/41 inalterado — frente clínica pausada (caminho B).**

**Re-conferência 003.CJ:** R-FDS-06 ganha footprint executável em `motor/*.py` (`mapear_frases_h`, PR #190) e teste-por-regra (`test_mapa_frases_h.py`) — união desta tabela 17→18; somada a R-RUIDO-01 (003.CC, posterior à tabela), o número-1 do topo vai a **19/42**. Tabela detalhada não re-medida linha a linha (próxima META).

### Estado da extração — binário, por capacidade
18 módulos no motor, **todos pós-estruturação**.

| Capacidade que destrava produção | Estado |
|---|---|
| Sub-camada química FDS→Risco (determinística) | **Construída e costurada, isolada** — sem chamador de produção (gate_cas 003.S/T → resolver_composicao 003.W → wrapper+propagação 003.Z; materialidade 003.J; 4ª fonte 003.P) |
| Transcrição LLM da FDS + revisão-RT (D-ARQ-47) | **CONSTRUÍDA e validada AO VIVO fim-a-fim** — `extrair_texto_fds` (003.BE) → `TranscritorGemini` real (003.BG) → `gate_forma` (003.BF) → `revisao_verbatim.montar_fds_revisado` (003.BI, cl.4) → `montar_fds`/`resolver_composicao`; 3/3 `@requer_api` passed vs. `fds_t65` (003.BH). **Fecha DT-003AS-01.** Sem chamador de produção plugado (CLI/Streamlit) — só harness/teste |
| Superfície da revisão-RT (onde o RT edita o verbatim) | **COMPLETA — D-ARQ-54 FECHADA (4/4)** — CLIs (003.CE/CF) + contrato unificado (003.CG) + web Streamlit (`web_envelope.py`/`web_fds.py`, 003.CL) sobre serializar/desserializar_verbatim; emissor do artefato-ida no adaptador ainda ausente (remanescente 003.CF) |
| Índice CAS (`construir_indice_cas`) | **21/45 slugs com CAS** (47%) — 003.AI populou 12; restam 24 null (parte por categoria física sem CAS aplicável, parte gargalo de dado) |
| Resolução canônica `name→slug` (string química → slug de agente) | **0 código** — decisão de arquitetura não tomada (D-ARQ-36 Parte 1); única `def` de normalização é `leo_resolver.py:37 _normaliza`, escopo LEO-texto, não vocabulário químico |
| Parse de PGR bruto → `tipos.PGR` (esqueleto GHE/cargo/risco físico) | **arquivo→Resultado CONSTRUÍDO e PLUGADO em produção** — `adaptadores/orquestracao_pgr.py::processar_arquivo_pgr` (D-ARQ-52, 003.BS, PR #162) costura extração→recorte→transcrição-LLM→gate→hidratação→motor num só chamador; primeiro e2e real do projeto (PDF Viverde, LLM mockado em teste). Transcrição-de-topo do envelope COMPLETA (D-ARQ-53, 4/4 fatias — recorte 003.BU, contrato 003.BW, resolvedor+seam 003.BX, plug `preparar_envelope` 003.BY; origem document-derived + confirmação-RT, paliativo D-ARQ-52 seam 3 fechado) **+ cliente-LLM real do topo pronto** (`TranscritorGeminiTopo`, 003.CA, PR #176, validado ao vivo 4/4 contra o gabarito 003.BV). Falta para **universalidade**: peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor (Viverde-pontual); superfície RT COMPLETA (D-ARQ-54 4/4, 003.CL) |

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
7. ~~**6ª/7ª/8ª fatia do parse-PGR — hidratação (1a contrato de tipo + 1b `hidratar_ghe`) + costura plural `hidratar_pgr` + plug de produção arquivo→Resultado**~~ — **CUMPRIDO** (003.BQ 1a: `RiscoPGR.agente` Optional[str] + guard, D-ARQ-51 seams 2/3, PR #156; 003.BQ 1b: `hidratar_ghe`, seams 1/4, PR #158; 003.BR: costura plural `hidratar_pgr`, PR #160; 003.BS: plug de produção `processar_arquivo_pgr`, D-ARQ-52, PR #162). Travessia Viverde arquivo→Resultado fecha fim-a-fim (LLM mockado em teste). **Resta para universalidade:** transcrição-de-topo do envelope + peças 1–2 de D-ARQ-57 implementadas (repertório de reconhecedores + gate de segmentação); resta peça 3 (família cargo-based) e medição multi-setor.
8. ~~**Cliente-LLM real do topo do envelope**~~ — **CUMPRIDO** (003.CA, `TranscritorGeminiTopo` em `adaptadores/transcritor_gemini_topo.py`, molde `TranscritorGeminiGHE`/D-ARQ-53; validado ao vivo 4/4 contra o gabarito 003.BV, PR #176). D-ARQ-53 fecha "cliente real ✓"; **superfície RT COMPLETA (D-ARQ-54 FECHADA 4/4 — contrato 003.CG, web 003.CL)**.
9. **Fatia A:** plugar `executar_com_composicao`/`montar_fds_revisado` no pipeline real (CLI/Streamlit), sobre índice CAS populado.
10. **`name→slug`:** decisão de arquitetura a tomar (D-ARQ-36 Parte 1) — destrava agentes sem CAS atômico.
11. **META higiene DH-003M-01:** 4ª recorrência de markdown cru, ainda pendente.

---
*Gestão à vista. Vive ao lado da produção, não a substitui. Próxima tiragem: ao próximo merge que mover um número, fechamento de marco, ou sessão META.*
