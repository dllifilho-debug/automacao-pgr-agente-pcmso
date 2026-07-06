# Painel de Estado — Projeto Agente Médico PCMSO
### Gestão à vista · estado corrente do produto

> **Painel vivo, não foto datada.** Mostra o estado corrente medido de disco (git), não estimativa.
> **Como este painel se mantém vivo (cadência de atualização):** re-tirado **por evento, nunca por calendário** —
> (1) a cada merge em `main` que move um dos três números abaixo, (2) em todo fechamento de marco,
> (3) no mínimo 1× por sessão META. Merge que não move número não dispara re-tiragem.
> A re-tiragem é passo do ritual de fechamento já existente (mesmo gate de disco — custo marginal ~zero).
> O `HISTORICO_OPERACIONAL.md` acumula os snapshots; este painel mostra só o presente.

---

**Tiragem corrente:** 003.BI · 05/07/2026
**Baseline:** main `0b89904` · 557 passed, 3 skipped · mypy `--strict` delta-zero (46 pré-existentes) · PROTOCOLO v41 · DECISOES v83

---

## Os três números

| Pergunta | Estado medido | Leitura |
|---|---|---|
| Quanto da regra clínica está no código? | **17 de 41** ativas (~41%) — inalterado desde 003.AH (frente clínica pausada, caminho B) | Espinha do motor de decisão de pé; cauda clínica ainda em prosa |
| A porta de entrada existe? | **Lado-FDS (química) CONSTRUÍDO e validado ao vivo** end-to-end (extração→LLM→gate→revisão-RT→montagem→resolvedor, 003.BD-BI); lado-PGR **0 código** | Gargalo de produção migrou: não é mais o transcritor-FDS — é o parse-PGR + a rasura do vocabulário químico |
| Dívidas que travam produção? | **3** — mesmas facetas de sempre, recontadas pós-fechamento | DT-003L-01 (parse-PGR), DT-003M-02 (vocabulário-FDS raso), DT-FDS-02 (unidade do cutoff) |

**Headline:** a produção **não está travada por falta de regra clínica nem mais pelo transcritor-FDS** (lado-químico fim-a-fim construído e validado ao vivo, 003.BH/BI) — está travada por **parse de PGR** (esqueleto GHE/cargo/risco físico, 0 código, D-ARQ-25) e por **índice CAS/vocabulário químico raso** (a maioria dos componentes de FDS real ainda cai em ramo 0/AUSENTE por falta de slug, DT-003M-02). Nenhuma regra clínica nova move essa restrição.

---

## CAMADA 1 — Diretoria · início, meio, fim

### Onde estamos, em uma frase
O **motor que decide os exames** (a partir de risco já estruturado) está ~41% construído e testado na espinha. Do lado da **porta de entrada**, o lado-FDS (química) está **construído e validado ao vivo, fim-a-fim** (PDF→extração de texto→transcritor-LLM→gate de forma→revisão-RT→montagem→resolvedor, 003.BD a 003.BI). Falta o lado-PGR: parse do esqueleto GHE/cargo/risco físico (D-ARQ-25, 0 código — maior massa restante) e o vocabulário químico ainda raso (a maioria dos componentes de FDS real cai em ramo 0/AUSENTE por falta de slug em `agentes.yaml`, DT-003M-02) — juntos, o que ainda separa o sistema de rodar um PGR real de ponta a ponta.

### A decisão que a diretoria precisa tomar
Hoje a fila assume "continuar a frente clínica" por inércia. O painel torna a escolha informada:

| Caminho | Entrega | **Não** entrega |
|---|---|---|
| **A — continuar clínica** | Cobertura 17→19/41; fecha camada de dedup | Não move o gargalo; PGR e2e segue impossível |
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
| UI da revisão-RT (Streamlit) | Greenfield | 0 código — `montar_fds_revisado` (003.BI) existe, sem tela onde o RT edita o verbatim |
| Parse de PGR (esqueleto GHE/cargo/risco físico) | Greenfield | 0 código (D-ARQ-25, ausente desde 003.L) — maior massa |

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

### Estado da extração — binário, por capacidade
18 módulos no motor, **todos pós-estruturação**.

| Capacidade que destrava produção | Estado |
|---|---|
| Sub-camada química FDS→Risco (determinística) | **Construída e costurada, isolada** — sem chamador de produção (gate_cas 003.S/T → resolver_composicao 003.W → wrapper+propagação 003.Z; materialidade 003.J; 4ª fonte 003.P) |
| Transcrição LLM da FDS + revisão-RT (D-ARQ-47) | **CONSTRUÍDA e validada AO VIVO fim-a-fim** — `extrair_texto_fds` (003.BE) → `TranscritorGemini` real (003.BG) → `gate_forma` (003.BF) → `revisao_verbatim.montar_fds_revisado` (003.BI, cl.4) → `montar_fds`/`resolver_composicao`; 3/3 `@requer_api` passed vs. `fds_t65` (003.BH). **Fecha DT-003AS-01.** Sem chamador de produção plugado (CLI/Streamlit) — só harness/teste |
| UI da revisão-RT (onde o RT edita o verbatim) | **0 código** — `serializar_verbatim`/`montar_fds_revisado` existem (motor puro); tela/costura ficam para fatia futura |
| Índice CAS (`construir_indice_cas`) | **21/45 slugs com CAS** (47%) — 003.AI populou 12; restam 24 null (parte por categoria física sem CAS aplicável, parte gargalo de dado) |
| Resolução canônica `name→slug` (string química → slug de agente) | **0 código** — decisão de arquitetura não tomada (D-ARQ-36 Parte 1); única `def` de normalização é `leo_resolver.py:37 _normaliza`, escopo LEO-texto, não vocabulário químico |
| Parse de PGR bruto → `tipos.PGR` (esqueleto GHE/cargo/risco físico) | **0 código** — D-ARQ-25, maior massa restante |

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

**Convergência crítica (recontada pós-fechamento DT-003AS-01):** ainda **3** dívidas travam produção — DT-003L-01, DT-003M-02, DT-FDS-02 — mas a natureza da restrição migrou: não é mais "falta transcritor-FDS" (fechado nesta sessão), é "falta parse-PGR + vocabulário químico populado". Não são débitos independentes — são facetas do mesmo subsistema de ingestão (D-ARQ-25 + `name→slug` + vocabulário de composição-FDS).

### Risco de retrabalho de B — considerado e descartado
Construir extração contra camada clínica incompleta → retrabalho se `R-CLI-*` mudar a forma do que a extração produz. **Descartado:** a saída da extração (input estruturado de agente/risco) é a montante e **ortogonal** à convergência `R-CLI-*` (dedup/periodicidade, a jusante). Contrato de saída não depende de `R-CLI-*` estar pronto. Bônus: clínica retomada depois valida `R-CLI-*` contra **PGR real, não fixture**.

---

## CAMADA 3 — Marcos · critério de pronto + gate de aceite

### Marco 1 — 1 PGR real end-to-end (matriz correta)
**Pronto =** um PGR nomeado roda de **arquivos brutos** (PGR + FDSs) até matriz GHE×exame **sem estruturação manual**, e a **coordenadora clínica valida a matriz de exames de saída**.

- **Gate de aceite clínico:** a validação clínica entra **aqui** — sobre a matriz que sai, não sobre cobertura de regra interna. Olho clínico opera sobre output real, a jusante.
- **Insumos materiais:** D-ARQ-25 parse-PGR (transcrição-FDS já entregue, D-ARQ-47/003.BI), `name→slug` canônico, **modelos de matriz de risco** (contrato de saída da extração), **normas vigentes gov.br/MTE** (ancoram a derivação), DT-003M-02 fechada, DT-FDS-02 confirmada, UI da revisão-RT plugada.
- **Estado:** **bloqueado pelo parse-PGR + vocabulário químico** (lado-FDS já construído e validado ao vivo) — é o que o caminho B ainda constrói.

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
3. **A declarar no kickoff (proposta do Arquiteto, 003.BI):** parse de PGR (D-ARQ-25 — esqueleto GHE/cargo/risco, maior massa restante, 0 código) **ou** costura da UI de revisão-RT (Streamlit) sobre `revisao_verbatim.py`.
4. **Fatia A:** plugar `executar_com_composicao`/`montar_fds_revisado` no pipeline real (CLI/Streamlit), sobre índice CAS populado.
5. **`name→slug`:** decisão de arquitetura a tomar (D-ARQ-36 Parte 1) — destrava agentes sem CAS atômico.
6. **META higiene DH-003M-01:** 4ª recorrência de markdown cru, ainda pendente.

---
*Gestão à vista. Vive ao lado da produção, não a substitui. Próxima tiragem: ao próximo merge que mover um número, fechamento de marco, ou sessão META.*
