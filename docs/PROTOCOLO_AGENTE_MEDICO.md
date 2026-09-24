# PROTOCOLO DO AGENTE PCMSO

**Fonte primária:** Entrevista assíncrona com Dra. Carolini Polesso (Coordenadora PCMSO), 47 áudios em 16/05/2026 + segunda rodada de validação em 17/05/2026.
**Caso de referência:** PGR Viverde V02 (03.02.2025) + Matriz RQ.61 Viverde (06.03.2025) — **validada como correta** pela Dra. Carolini.
**Status:** Protocolo validado. Pendências de v1 fechadas.

Cada regra tem ID estável (`R-CATEGORIA-NN`). O ID **não muda** entre versões — alterações de conteúdo geram nota de revisão na própria regra.

Convenções de status:
- `[VALIDADO]` — extraído diretamente da entrevista com a Dra. Carolini (16-17/05/2026),
  sem ambiguidade. CONGELADO a partir de 002.M: a fonte primária não faz mais validação
  prévia. Regras `[VALIDADO]` são base estável; não reabrem exceto por norma vigente que
  as contradiga.
- `[INFERIDO]` — deduzido de outras respostas da entrevista. Não será mais promovido pela
  Dra. Carolini; resolução segue a hierarquia de D-ARQ-22.
- `[A VALIDAR — Carolini]` — DESCONTINUADO a partir de 002.M. Itens reclassificados em
  `[DERIVADO]` ou `[INTERPRETADO]`.
- `[DERIVADO — fonte]` — resolvido após 002.M por fonte objetiva, seguindo a hierarquia de
  4 níveis de D-ARQ-22 Parte A (parar no primeiro que resolver): (1) norma vigente conferida
  no site oficial do MTE → `[DERIVADO — NR-x item y]`; (2) matriz validada como precedente
  (RQ.61 Carolini / matriz Patrícia) → `[DERIVADO — RQ.61/Patrícia]`; (3) analogia direta com
  regra `[VALIDADO]` → `[DERIVADO — analogia R-XXX]`. Alta confiança; a fonte é nomeada NO
  PRÓPRIO MARCADOR, não apenas no corpo. O nível 4 (norma/matriz/analogia não resolvem) produz
  `[INTERPRETADO]`, abaixo — saída da mesma árvore de decisão, não um estado paralelo.
- `[INTERPRETADO — prioridade na revisão de saída]` — decisão do Arquiteto onde norma/
  matriz/analogia não foram conclusivas. NÃO houve crivo clínico prévio. É a categoria que
  a revisão de saída (médica lendo a matriz gerada) deve inspecionar PRIMEIRO. Não é um
  buraco permanente: é o item de maior incerteza no ciclo PDCA, marcado para atenção.

---

## 1. GATES DE ACEITAÇÃO DO PGR

São condições eliminatórias. Se qualquer gate falhar, o PGR é rejeitado e a matriz não é montada.

### R-PGR-01 — Assinatura por engenheiro `[VALIDADO]`
PGR deve ser assinado por **engenheiro de segurança do trabalho**. Assinatura apenas por técnico → rejeitado.
**Base normativa:** NR-18 (conforme citado pela Dra. Carolini).

### R-PGR-06 — Validade vigente `[VALIDADO]`
PGR com validade emitida há **2 anos ou mais** → rejeitado. Solicitar atualização à empresa.

---

## 2. ORDEM DE LEITURA DO PGR

### R-PGR-02 — Sequência de leitura `[VALIDADO]`
A leitura é **sequencial e gera a matriz em paralelo** (não há leitura prévia completa antes de montar):

1. **Cabeçalho** — verificar gates (R-PGR-01 e R-PGR-06)
2. **Inventário de riscos** — riscos identificados por GHE
3. **Agravos à saúde** — efeitos associados a cada risco
4. **EPIs indicados por GHE** — sinal indireto de risco (ver R-PGR-03)
5. **Padronização final** — aplicar NR-07 + NR-15 + protocolos especiais

A **fonte geradora do risco** é consultada apenas quando necessária para esclarecer dúvida.

### R-PGR-03 — Sinal indireto via EPI `[VALIDADO]`
Quando o PGR exige **máscara de proteção respiratória (PFF2, PFF3 ou facial)** mas **não declara risco químico no inventário** → presumir exposição química respiratória.

**Consequência mínima:** incluir espirometria (ver R-ESP-02).

**Base normativa:** NR-07, item de espirometria. Confirmado pela Dra. Carolini como exigência normativa, não conduta clínica isolada.

### R-PGR-04 — Informação crítica ausente `[VALIDADO]`
Se a **descrição da composição de produtos químicos** estiver ausente ou inadequada → exigir FDS antes de montar a matriz. Sem composição química resolvida, a matriz não pode ser fechada.

### R-PGR-05 — PGR mal escrito `[VALIDADO]`
PGR com riscos genéricos, sem quantificação, sem agentes especificados:
1. Solicitar FDS dos produtos à empresa
2. Conversar com o elaborador do PGR para esclarecer

Não rejeitar o PGR por essa razão.

**Nota de aplicação 003.EJ — fração declarada sem agente é caso de R-PGR-05, não de vocabulário ausente.** `[DERIVADO — NR-07 Anexo III Quadros 1 e 2 (Portaria MTP 567/2022), texto oficial MTE conferido em 29/07/2026]`

Nos dois quadros do Anexo III a **fração é o que se mede** e o **agente é o que a poeira contém**: o Quadro 1 é "poeira contendo sílica, asbesto ou carvão mineral"; o Quadro 2 é "poeiras contendo partículas insolúveis ou pouco solúveis de baixa toxicidade e não classificadas de outra forma", com o ramo "empresas com medições quantitativas periódicas **de poeira respirável**". O roteamento entre os dois quadros depende exclusivamente da identidade e das propriedades da substância contida — nunca da fração.

Logo, PGR que declara só a fração (`Poeira respirável`, `Poeiras Respiráveis/Metálicas`) **não permite rotear**: as três condições do rodapé do Quadro 2 (não possuir LEO definido; ser insolúvel ou pouco solúvel; ter baixa toxicidade, não sensibilizante) são predicados sobre o material, e nenhuma é verificável sem a substância. Mapear a fração para `poeira_nao_classificada` inventa a classificação PNOS; mapeá-la para `silica` presume o agente mais severo sem evidência documental (é o que a matriz humana faz — ver DT-003EC-01) e contradiz `test_termos_silicato_e_poeira_nao_resolvem_para_silica`.

**D-ARQ-68 não se aplica:** os quadros têm ramo exaustivo para ausência de **medição**, dentro de um quadro já escolhido; não há ramo para ausência de **identidade do agente**. Vale a cláusula 2 — D-ARQ-13 prevalece, a resolução falha e a pendência permanece.

A conduta já está prescrita por esta regra: solicitar FDS, conversar com o elaborador, **não rejeitar o PGR**. O destinatário correto da pendência é o elaborador do PGR, não o vocabulário do protocolo. Nenhuma regra nova; ID e semântica de R-PGR-05 intactas.

**Medido no Fascino (003.EJ):** `Poeira respirável` em 14 GHEs, dos quais **13 já declaram sílica** e já recebem RX 24M + espirometria — o valor clínico incremental de resolvê-la é praticamente nulo no caso medido. Consequência estrutural (bloquear ou seguir com ressalva) segue em **DT-002I-01**, ABERTA.

---

## 3. MODELO DE GHE

### R-GHE-01 — Unidade de análise `[VALIDADO]`
A análise é feita **GHE a GHE**. Todas as funções dentro de um mesmo GHE recebem **matriz idêntica de exames e periodicidade**. Não há diferenciação por cargo dentro do mesmo GHE.

### R-GHE-02 — Risco implícito pelo cargo `[VALIDADO]`
Cargos cuja **operação geradora de risco é indissociável da função-fim** recebem os exames desse risco **mesmo quando o inventário do PGR não declara explicitamente** a exposição.

**Critério de aplicabilidade (refino 002.L-estudo).** O risco implícito por cargo só vale quando a operação causadora é a atividade-fim do cargo — nunca pela mera denominação. A NR-01/NR-07 (Portaria 567/2022) não reconhece "risco por denominação de cargo"; o risco é definido pela exposição real classificada no PGR. Quando a operação de risco é **contingente** (pode ou não ocorrer na função), o risco não é atribuído automaticamente — recai em confirmação documental (ver R-GHE-05).

**Caso âncora — soldador (industrial):** soldar é a atividade-fim → fumos metálicos são indissociáveis. Mesmo sem o inventário citar, a presença do cargo implica exposição. Aplicar protocolo de fumos metálicos (ver R-PKG-SOLD).

**Contra-exemplo — serralheiro de obra:** solda é contingente (a função pode ser só corte a frio, dobra, gradil, esquadria). NÃO atribuir fumos/Mn/CO por cargo. Ver R-GHE-05.

Esta regra é a expressão clínica do princípio *"não existe solda sem fumos metálicos"* — **desde que soldar seja a atividade-fim**. O sistema aceita risco implícito por cargo como cidadão de primeira classe, condicionado ao critério de indissociabilidade.

**Base:** Dra. Carolini, R1 (05/2025); NR-01/NR-07 (Portaria 567/2022).

### R-GHE-03 — Múltiplos riscos, mesmo exame `[VALIDADO]`
Quando o mesmo exame é exigido por riscos distintos no mesmo GHE → **linha única** na matriz. A periodicidade não se altera em função do número de riscos que pedem o exame.

**Nota de aplicação 003.EE.** O dedup de R-GHE-03 passa a compor periodicidade por piso
component-wise (D-ARQ-39 IMPLEMENTADA), não mais por igualdade estrita. As regras permanecem
distintas — o piso é dedup, não fusão. Sem mudança de semântica clínica.

### R-GHE-04 — Risco listado mas não convincente `[VALIDADO]`
Quando o PGR lista um risco que parece não realista para o GHE, a Dra. Carolini **segue o inventário** sem reinterpretar nem rejeitar. O documento é a fonte de verdade do escopo de risco.

**Implicação para o agente:** não implementar lógica de "filtragem clínica de riscos do PGR". O inventário é canonical.

### R-GHE-05 — Risco contingente exige confirmação documental `[VALIDADO]`
Cargo cuja operação de risco é **contingente** (não indissociável da função-fim) não recebe o risco por atribuição implícita. O risco entra como **pendência de confirmação documental**: solicitar PGR/FDS que confirme a operação (ver R-FDS-01, R-PGR-04, R-PGR-05).

- **PGR/FDS confirma a operação de risco** (ex.: serralheiro que solda — MIG/TIG/eletrodo) → aciona exatamente os exames do risco confirmado (ex.: pacote de fumos metálicos, idêntico ao soldador).
- **PGR/FDS descreve apenas operações sem o risco** (ex.: serralheiro só com corte a frio, dobra, fixação de gradil, montagem de esquadria) → não aciona os exames daquele risco.

**Caso âncora — serralheiro de obra.** No caso Viverde (RQ.61, GHE 10), o pacote de fumos/Mn disparou porque o PCMSO declarava agente medido ("Risco Cromo abaixo de 10% LT da ACGIH") — exposição confirmada documentalmente, não atribuição por cargo.

**Implicação para a taxonomia (`cargos.yaml.riscos_implicitos`, D-ARQ-02/D-ARQ-12):** o campo `riscos_implicitos` só contém riscos indissociáveis. Serralheiro NÃO recebe `{solda, fumos_metalicos, manganes}` ali. (O hardcode `serralheiro → cromo` do motor legado em `modules/agente_medico_ia.py` está obsoleto e contradiz esta regra — não replicar no motor novo.)

**Nota de implementação (002.M).** R-GHE-05 é clinicamente completa, mas depende de um
dado que o motor ainda não modela: a **operação confirmada** do GHE. `GHEPGR` (`tipos.py`)
carrega `cargos`, `riscos` (agentes), `epis`, `produtos_quimicos`, `psicossocial` — não
carrega operações/tarefas. Sem isso o motor não avalia "a operação de solda foi confirmada".
Endereçado por D-ARQ-23 (operação como dado de primeira classe). Até lá, R-GHE-05 não é
executável no motor novo.

**Caso âncora documentado — serralheiro Viverde (Est-09).** O PGR Viverde declara, para o
serralheiro, os agentes `radiacao_uv_ir` (solda) e `dioxido_de_titanio` (0,008 mg/m³), além
de ruído e acidente; descreve nas tarefas ET38-ET42 "solda com eletrodo revestido". NÃO
declara `fumos_metalicos` nem cromo no inventário de entrada. O cromo ("Risco Cromo abaixo
de 10% LT da ACGIH") aparece só na RQ.61, que é a matriz de SAÍDA validada — não na entrada.
Logo, o motor processando o PGR puro vê marcadores de solda (radiação UV de solda + TiO2,
constituinte do revestimento rutílico do eletrodo) mas nenhum agente que dispare R-PKG-SOLD/
R-RX-02 (gatilho `fumos_metalicos`). Sem modelar a operação (D-ARQ-23), o motor NÃO reproduz
o pacote de fumos da RQ.61 — divergência esperada e rastreada, não erro do fixture. Fundamento
técnico: fumo de solda de eletrodo revestido é mistura (Fe, Mn, Cr, Ni + constituintes do
revestimento como TiO2 e fluoretos); TiO2 e cromo são dois constituintes do mesmo fumo, não
agentes contraditórios; Mn está presente em praticamente todo eletrodo (R-FDS-05). Fontes
técnicas: OSHA FS-3647; literatura de composição de eletrodo revestido.

**Base:** Dra. Carolini, R1 (05/2025); NR-01/NR-07 (Portaria 567/2022). Resolve DT-002K-02.

---

## 4. INTERPRETAÇÃO DE FDS

### R-FDS-01 — Quando exigir FDS `[VALIDADO]`
Solicitar FDS à empresa quando:
- A composição química está ausente ou genérica no PGR
- O cargo pressupõe exposição química não inventariada (ex: pintor, soldador)
- O PGR é mal escrito (ver R-PGR-05)

### R-FDS-02 — Priorização de leitura `[VALIDADO]`
Ao ler uma FDS, priorizar nesta ordem:
1. **Composição** (seção 2 / 3)
2. **Toxicologia** (seção 11)
3. **EPIs recomendados** (seção 8)

### R-FDS-03 — Cutoff por concentração `[VALIDADO]`
- **Componentes com concentração > 5%** → considerar e pedir biomonitoramento
- **Componentes cancerígenos** (classificados pela IARC) → considerar **independente da concentração**

### R-FDS-04 — FDS com descrição genérica `[VALIDADO]`
FDS com termo genérico (ex: "hidrocarbonetos aromáticos") sem especificar o componente → resolver pelo **CAS** de cada constituinte.

**Caso âncora — benzeno:** se o CAS revelar presença de benzeno, **independente da concentração**, aplicar protocolo benzeno (ver R-PKG-BZ).

#### Nota de procedência — cutoff de 5% e carcinógeno-independe (003.G) `[INTERPRETADO]`
O limiar **5%** de R-FDS-03 é conduta da Dra. Carolini alinhada a GHS/ABNT 14725, **sem âncora em NR** — mantém-se `[VALIDADO]` como conduta, **não** `[DERIVADO]`. A cláusula "carcinógeno independe de concentração" (R-FDS-03 IARC; R-FDS-04 benzeno via CAS) é boa prática INCA/Anexo V, `[INTERPRETADO]` — não é ">0%" escrito na norma. Por D-ARQ-33 (caminho C), o 5% é **limiar-dado** (constante de protocolo) e a materialidade é **predicado tri-estado derivado** consumido por cada lado da mesa (médico via R-FDS-03; engenheiro via protocolo-engenheiro futuro); os bypasses do cutoff são uma **lista** (carcinógeno IARC, sensibilizante, demais perigos da frase-H), não um critério binário. IDs R-FDS-03/04 inalteradas, semântica intacta — esta nota é só procedência.

### R-FDS-05 — Eletrodo de solda `[VALIDADO]`
O metal de adição do eletrodo só é identificável pela FDS específica do eletrodo. **Solicitar à empresa.** Praticamente todos os eletrodos contêm manganês → presumir Mn na ausência de informação contrária.

### R-FDS-06 — Confiança na FDS `[VALIDADO]`
Não há classe de produto químico em que a Dra. Carolini sistematicamente desconfia da FDS. O único cenário de desconfiança é a **FDS com descrição genérica** (R-FDS-04), resolvido via CAS.

**Implicação para o agente:** confiar nos dados de FDS é o default; investigação adicional só é disparada por genericidade da descrição.

**Nota de aplicação (003.CI, D-ARQ-55).** R-FDS-06 ganha consumidor executável no recorte (B) da transcrição-FDS: a frase-H declarada na FDS é confiada por default (sem desconfiança por classe), transcrita verbatim em `Componente.frases_h` e admitida pelo RT (D-ARQ-47 cl.4) → mapa determinístico resolver-side {H334, H317} → `is_sensibilizante`. O gate é de FORMA (`H\d{3}`), não de conteúdo — coerente com "confiar na FDS é o default; investigação só por genericidade (R-FDS-04)". Semântica de R-FDS-06 intacta; ID preservada. **Implementada (003.CJ, PR #190):** `mapear_frases_h` (`agente_medico/motor/resolvedor.py`, docstring carrega o ID), teste-por-regra em `test_mapa_frases_h.py` (cada caso falha sem a fatia). **Segunda aplicação (003.CK, D-ARQ-56, PR #192):** a articulação "ausência de frase-H ⇒ inerte-declarado" (`[INTERPRETADO — prioridade na revisão de saída]`, sem norma literal) materializada na Fase C — componente sem slug e `frases_h == ()` gera pendência NÃO-bloqueante com `regra_origem="R-FDS-06"` (`estagios/riscos.py`); teste-por-regra em `test_promocao_quimico.py`. Semântica e ID intactas.

---

## 5. REGRAS POR TIPO DE EXAME

### 5.1 Exame Clínico

#### R-CLI-01 — Default anual `[VALIDADO]`
Exame clínico **anual** é o piso — vale inclusive para administrativo sem risco.
**Justificativa clínica:** trabalhadores com doença crônica devem ter clínico anual; como não há triagem prévia, padroniza-se anual para todos.

> **Nota de implementação (003.EC, mesma ID).** Materializada em `regras.yaml` via
> primitivo incondicional `todo_trabalhador` (D-ARQ-66); slug `exame_clinico` novo em
> `exames.yaml`; 12M em `[adm, per, MR, RT, dem]`. Momentos `[DERIVADO — R-TEMP-01 (5
> momentos) + medição da matriz humana Fascino 08/07/26, 19/19 GHEs em
> ADM/PER/MRO/RET/DEM]`. Quatro testes falha-sem/passa-com em `test_orquestrador.py`.
> Conteúdo clínico inalterado.

#### R-CLI-02 — Quadro 1 e Quadro 2 do Anexo I (NR-07) `[VALIDADO]`
Exposição a agente biomonitorado do Anexo I (Quadro 1 ou Quadro 2) demanda clínico **semestral**. Quando exposto a agentes de **ambos os Quadros**, registrar em **uma única linha** semestral (não duplicar).

> **Changelog 003.AA (mesma ID — relabel sem mudança de saída).** "Anexo I / Anexo II" → "Quadro 1 / Quadro 2 do Anexo I" (567/2022; "Anexo II" da NR-07 é ruído, não químico-com-LT). O conjunto de agentes que dispara o semestral não muda → saída estável → ID preservada.
> **Ressalva `[INTERPRETADO — prioridade na revisão de saída]`:** o semestral é conduta da Dra. Carolini, não a NR-07 — item 7.5.8 fixa clínico **anual** para exposto (menor a critério médico). A borda "carcinógeno só de Anexo V, sem indicador no Anexo I, dispara semestral?" não está cravada (fonte primária congelada desde 002.M) — inspecionar na revisão de saída.

#### R-CLI-03 — Manganês fora do Anexo I `[VALIDADO]`
O **manganês** é o único agente fora do Anexo I (Quadros 1 e 2) da NR-07 que dispara clínico semestral. Base: NR-15 — exposição a Mn exige avaliação biológica independente do limite de tolerância.

> **Changelog 003.AA (mesma ID).** "fora dos Anexos I e II" → "fora do Anexo I (Quadros 1 e 2)": Mn não consta em nenhum Quadro do Anexo I; o antigo "Anexo II" era o balde químico-com-LT (vocabulário pré-567), hoje inexistente nesse sentido. Conteúdo inalterado. A unicidade sob o eixo novo segue `[VALIDADO]`; reconfirmar de passagem se algum agente de Anexo V a altera (`[INTERPRETADO — revisão de saída]`).

#### R-CLI-04 — Risco físico isolado `[VALIDADO]`
**Nenhum** risco físico (ruído, calor, vibração) isoladamente justifica clínico semestral. O default anual prevalece.

### 5.2 Audiometria

#### R-RUIDO-01 — Classificação de exposição a ruído contínuo/intermitente vs. nível de ação e LT `[DERIVADO — NR-15 Anexo 1 + NR-09 nível de ação c/c NHO-01]`

Converte a medição de ruído (`Quantificacao` com `unidade="dB(A)"`, `valor` = NEN) na classificação `relacao_LT` que os predicados de audiometria consomem. Destrava a fatia 3 de D-ARQ-51 (`dB(A)→relacao_LT`, até 003.BZ sempre `None`).

Partição disjunta e exaustiva sobre o NEN:

| Faixa (NEN) | `relacao_LT` |
|---|---|
| valor < 80 dB(A) | `abaixo_acao` |
| 80 ≤ valor < 85 dB(A) | `entre_acao_LT` |
| valor ≥ 85 dB(A) | `acima_LT` |

**Limiares (fonte normativa):**
- **85 dB(A)** = limite de tolerância para exposição de 8h — NR-15 Anexo 1 (contínuo/intermitente). Teto absoluto 115 dB(A) sem proteção. `[DERIVADO — NR-15 Anexo 1, texto vigente conferido gov.br/MTE 2025]`
- **80 dB(A)** = nível de ação = dose de 0,5 = NLI (nível limiar de integração) da NHO-01/Fundacentro. `[DERIVADO — NR-09 nível de ação c/c NHO-01]`; nº do item literal da NR-09 vigente `[INCERTO — confirmar na Portaria 6.735/2020 antes de citar no comentário do código]`.

**Ressalvas `[INTERPRETADO — prioridade na revisão de saída]`:**
1. `valor` DEVE ser o NEN (normalizado p/ 8h), não SPL instantâneo nem pico. Comparar leitura pontual ao LT de 85 é erro clínico silencioso (classe D-ARQ-22). Análogo direto a DT-002V-01 (`Quantificacao.valor` não discrimina a estatística — lá CLSC, aqui NEN). Laudo com pico/média simples → pendência, não classificação. Ver **DT-003CB-01**.
2. A taxa de troca q=5 (NR-15) vs q=3 (NHO-01) afeta o **cálculo** do NEN/dose, não a classificação por limiar. O motor **consome o NEN pronto, não calcula dose** — mesma separação NR-07-consome/NR-09-produz de DT-002V-01. O `q` vive no laudo, fora do motor.
3. Ruído de impacto (NR-15 Anexo 2, teto ~130 dB(C)) é agente distinto — fora do escopo desta regra. Só contínuo/intermitente.

**Borda:** limites inferiores inclusivos (≥80, ≥85) — a insalubridade começa *em* 85. Direção inversa das bordas `≤` de R-RX-01; confirmar na revisão de saída.

**Vocabulário `relacao_LT`:** o classificador emite apenas os 3 valores disjuntos acima. `acima_acao` permanece sinônimo-legado aceito pelo predicado `_ruido_acima_acao`, nunca **produzido** pelo classificador (evita ambiguidade com `entre_acao_LT`).

**Consumidor existente (inalterado):** `_ruido_acima_acao` já dispara `True` para `{entre_acao_LT, acima_LT}` → R-AUD-01 (12M adm/per/MR) e R-AUD-02 (demissional "acima do nível de ação"). R-RUIDO-01 alimenta esses predicados sem tocar as R-AUD-*.

**Cobertura de teste (exigida antes de "implementada"):** um teste por faixa que falhe sem a regra — 79→`abaixo_acao`, 80→`entre_acao_LT`, 84→`entre_acao_LT`, 85→`acima_LT`, 90→`acima_LT`; mais NEN-ausente/pico → pendência (não classifica). Âncora Viverde (`MAPA_GHE_VIVERDE.md`): 78,8 dB(A)→`abaixo_acao`; 89,6 dB(A)→`acima_LT`.

**Universalidade:** o LT de ruído da NR-15 vale construção civil, indústria química e saúde igualmente — regra universal, não caso Viverde.

**Implementação (003.CC).** Materializada em `motor/classificacao_ruido.py` (`classificar_ruido`), aplicada em `hidratar_ghe` pós-resolução (slug "ruido", EXATA/FUZZY). Cobertura por faixa exigida: cumprida (15 testes, incl. bordas 80/85 e âncoras Viverde 78,8/89,6). Commit `9500c2a`, PR #179. R-RUIDO-01 passa de "escrita" a "implementada" (regra com teste que falha sem ela). DT-003CB-01 segue ABERTA (documentada no docstring do classificador).

**Changelog (003.EZ) — `[INCERTO]` de 003.CB FECHADO.** O item literal do nível de ação é a
**NR-09 9.6.1 alínea "c"** (*"como nível de ação para o agente físico ruído, a metade da
dose"*) — disposição **transitória**: *"Enquanto não forem estabelecidos os Anexos a esta
Norma..."*, com a definição de dose em **9.6.1.2**. A NR-09 vigente incorpora a **Portaria MTE
nº 105, de 29/01/2026**; tem Anexo I (Vibração) e Anexo III (Calor), e **nenhum Anexo de
Ruído**. Os limiares 80/85 dB(A) e a partição de `relacao_LT` acima ficam **inalterados** — a
mudança é só de proveniência normativa do nível de ação, que era `[INCERTO]` e passa a
`[DERIVADO — NR-09 9.6.1 "c" c/c 9.6.1.2, disposição transitória]`. Registro para a revisão de
saída: o nível de ação de ruído é hoje **transitório** por desenho da própria norma — publicado
um Anexo de Ruído específico, esta regra reabre para conferir se ele redefine o nível de ação
ou a partição.

#### R-AUD-01 — Indicações para 12M (adm/per/MR) `[VALIDADO]`
Audiometria **12 meses** em **adm/per/MR** quando houver pelo menos uma das condições:
- Ruído (qualquer nível, mesmo abaixo do nível de ação, **se combinado** com outras condições abaixo)
- Motorista de equipamento pesado
- Trabalho em altura
- Espaço confinado
- Exposição a ototóxicos
- Exposição a vibração (corpo inteiro ou mãos-braços)

**Changelog (003.EZ), mesma ID.** A perna do ruído ganha âncora normativa:
`[DERIVADO — NR-07 Anexo II itens 2 e 4.1 "a"/"b"; momento MR por 7.5.6 "d" + 7.5.7, a contrario
7.5.15]`. As pernas `motorista_equipamento_pesado` e `ototoxico` seguem `[VALIDADO]` **sem**
âncora normativa própria — conduta da Dra. Carolini além do item 2, agora escrita como tal.
**Silêncio do PGR sobre a quantificação do ruído** (NR-09 9.4.1/9.4.2, avaliação quantitativa
condicional) passa a admitir presunção protetiva declarada por primitivo
(`quando_ausente: {presumir_true: [ruido_acima_acao]}`, D-ARQ-68 cl.5): a linha emite com
pendência não-bloqueante nomeando o primitivo presumido, e esse trecho da regra fica
`[INTERPRETADO — prioridade na revisão de saída]`.

#### R-AUD-02 — Audiometria no demissional `[VALIDADO]`
Demissional **é executado** apenas quando:
- **Ruído acima do nível de ação**, OU
- Combinação **ruído + ototóxico + vibração**

Para trabalho em altura, equip. pesada e espaço confinado **sem ruído**: faz adm/per/MR, **não faz** demissional.

**Changelog (003.EZ), mesma ID.** O demissional sob ruído acima do nível de ação ganha âncora
`[DERIVADO — NR-07 Anexo II item 4.1 "c"]`. A perna `e(ruido, ototoxico, vibracao_qualquer)`
segue `[VALIDADO]` sem âncora. Mesma presunção protetiva de R-AUD-01 sobre `ruido_acima_acao`,
mesma marca `[INTERPRETADO — prioridade na revisão de saída]` (D-ARQ-68 cl.5) — a perna `e`
**não** está na allowlist de presunção: ausência ali (ex.: vibração não-qualificada) continua
bloqueante, mesmo com ruído presumido.

#### R-AUD-03 — Validade do demissional `[VALIDADO]` `[DERIVADO — NR-07 Anexo II item 4.1.1, texto oficial MTE conferido em 14/08/2026]`
Audiometria realizada há **mais de 120 dias** → refazer no demissional.

#### R-AUD-04 — Audiometria como piso universal, com demissional `[DEPRECATED — fundamento refutado por DT-003EY-01, sem sucessora — D-ARQ-81]`

> **Redação original preservada para rastreabilidade (não remover — auditoria histórica do
> PCMSO):** `[DERIVADO — matriz-precedente: Carolini 07/2026 (SPE 0030) + Patrícia 04/2025
> (RESERVA 0028); periodicidade e momento demissional em NR-07 Anexo II 4.1]`

**Por que caiu (003.EZ, D-ARQ-81).** O fundamento era matriz-precedente `n=2` concordante
(D-ARQ-22 Parte A nível 2). 003.EY mediu **23 obras** e refutou: universalidade em **7/23**
(6/23 com piso `n_cargos ≥ 17`), distribuição larga entre as não-universais. As duas matrizes de
003.EX eram justamente as duas em que a médica estendeu ao administrativo — artefato de
amostra, não convergência. `D-ARQ-81` cl.1 (c) fecha a lacuna que permitiu isto: quando a norma
já **define** o universo (item 2 do Anexo II), precedente não autoriza ampliá-lo — só confirma
conduta dentro dele. **Sem sucessora**: o momento `DEM` que esta regra cravava incondicional
passa a sair pela **presunção protetiva de R-AUD-02** (D-ARQ-68 cl.5, medido em 003.EZ) quando o
PGR está silencioso sobre a quantificação do ruído — não há conduta nova a herdar, há conduta a
retirar.

Todo trabalhador recebe **audiometria, 12 meses, em `[adm, per, MRO, dem]`**, independentemente
de risco declarado no PGR. Piso por baixo — não substitui nem depreca `R-AUD-01`/`R-AUD-02`;
convive com elas (molde `R-CLI-01`×`R-CLI-02`), e a linha carrega os motivos de todas as regras
que dispararam (dedup `R-GHE-03`/D-ARQ-39 concatena, não substitui).

**Base normativa, em duas partes com forças diferentes.**
*O que a norma crava* `[DERIVADO — NR-07 Anexo II itens 4.1 e 4.1.1, texto oficial MTE conferido
em 14/08/2026]`: item 4.1 — *"O exame audiométrico deve ser realizado, no mínimo: a) na
admissão; b) anualmente, tendo como referência o exame da alínea 'a' acima; c) na demissão."* —
a periodicidade de 12M e a presença de `adm`/`dem` têm âncora literal.
*O que a norma NÃO crava* `[INTERPRETADO — prioridade na revisão de saída]`: o **universo** — o
item 2 do Anexo II delimita a obrigação a quem está "acima dos níveis de ação, conforme
informado no PGR", e o **momento MRO**, que não aparece no item 4.1 e vem só do precedente.
Estender a todo trabalhador é conduta **além** da norma — mais protetiva, nunca contrária, mas
não derivada dela.

**Medição que sustenta o precedente** `[MEDIDO — 003.EX, Word COM]`: audiometria em 41/41 (SPE
0030) e 44/44 (RESERVA 0028); demissional confirmado em 38/41 (93%, Carolini) e 42/42 confirmados
+ 2 indeterminados por forma ambígua de célula (95–100%, Patrícia). Duas médicas, dois clientes,
lados opostos do corte de vigência da NR-01 (26/05/2026) — e convergem. Detalhe nominal em
`docs/referencia/GABARITO_003EX_audiometria_dem.md`.

**Limitação de escopo, declarada.** Os dois documentos são construção civil, e o acervo inteiro
é de construtoras — limitação estrutural da amostra, não de tamanho. Reinspecionar no primeiro
PGR de hospital, indústria química ou setor administrativo puro; se a conduta não se sustentar,
a regra ganha condição de escopo — ID nova, não emenda (D-ARQ-06).

**Fronteiras.** `DT-003EG-01` (audiometria pelo motivo errado) não é agravada nem fechada por
esta regra — motivos concatenam, não substituem; a causa (`ruido_acima_acao` resolvendo
`Ausente`) continua intacta. `D-ARQ-68` intacto — esta regra não muda como ausência vira estado,
emite por outro gatilho, ao lado. Veículo: `D-ARQ-66` (emissão incondicional, primitivo
`todo_trabalhador`) — a linha incondicional não conta para o tri-estado (cl.2); GHE sem nenhum
risco resolvido continua BLOQUEADA.

### 5.3 Espirometria

#### R-ESP-01 — Default e exceção via EPI `[DEPRECATED — sucedida por R-ESP-02 em 003.EI]`

> **Redação original preservada para rastreabilidade (não remover — auditoria histórica do PCMSO):**
> - **Default** = 24 meses (adm/per/MR/dem) — exposição a químico respiratório, fumos metálicos
> - **Exceção (sinal por EPI):** PGR exige máscara (PFF2/PFF3) sem risco químico declarado → espirometria **adm + MR apenas** (sem periódico, sem demissional)
>
> **Base normativa:** NR-07, item de espirometria. Confirmado pela Dra. Carolini como exigência normativa.

**Motivo da depreciação.** O default ("químico respiratório, fumos metálicos") e a exceção-EPI ("adm + MR apenas") não têm âncora no texto vigente do Anexo III; os itens 3.2 e 3.3 condicionam esses casos a sinais/sintomas respiratórios. Escopo de aplicação alterado → nova ID (regra de versionamento do projeto; precedente R-BIO-02→R-BIO-04). Sucessora: R-ESP-02.

#### R-ESP-02 — Espirometria ocupacional por exposição a poeira mineral `[DERIVADO — NR-07 Anexo III item 3.1 (Portaria MTP 567/2022), texto oficial MTE conferido em 003.EI]`

Sucede R-ESP-01. Trabalhador exposto a poeira mineral indicada no inventário de riscos do PGR → espirometria 24 meses em [adm, per, MR, dem].

- Gatilho e periodicidade `[DERIVADO — NR-07 Anexo III 3.1, literal: "devem ser submetidos a espirometria nos exames médicos admissional e a cada dois anos"]`.
- Momentos MR e dem `[DERIVADO — matriz-precedente: Carolini 07/2026 (Fascino) e Patrícia 04/2025 (Reserva 0028), ambas (ADM, PER, MRO, DEM)]`. A norma crava só admissional + periódico; os dois momentos extras são conduta convergente em duas matrizes, nível 2 de D-ARQ-22 Parte A.
- Poeira mineral = sílica, asbesto e PNOS. Carvão mineral fica fora até DT-002X-01 (LEO não resolvido).
- NÃO depende de quantificação: o item 3.1 não roteia por faixa. Presença no inventário basta. Contrasta deliberadamente com R-RX-01, que faixa por CLSC/LEO no mesmo anexo.
- Bloqueio bloqueante do RX por medição incompleta (D-ARQ-31, bloqueio por-risco/por-linha) não se propaga à espirometria: o mesmo GHE com sílica sem laudo completo bloqueia `rx_torax_oit` e emite `espirometria` normalmente — assimetria intencional, travada por teste.

Alcançabilidade em produção `[MEDIDO — 003.EI]`: dos três slugs do composto `poeira_mineral`, apenas `silica` tem chave `termos:` em `agentes.yaml`. `asbesto` e `poeira_nao_classificada` não têm — os primitivos correspondentes nascem verdes na suíte e inalcançáveis em produção, mesma classe de D-ARQ-67 (literal órfão) e da consequência registrada em D-ARQ-68 ("regra materializada e verde pode estar inalcançável quando o campo que seu predicado lê não é escrito por produtor real"). Não bloqueia: `silica` alcança e responde pela cobertura prevista. Fechar exige popular `termos:` com grafia normativa por fonte — classe (2) de DT-003EB-01, sessão de dado própria, junto com `fumos_metalicos` (resíduo já nomeado em 003.EH).

Fora do escopo do motor (D-ARQ-09 — o motor é função pura sobre o PGR, não vê dado clínico individual nem resultado de exame):
- 3.2 (outros agentes agressores pulmonares — "sensibilizantes e/ou irritantes pelos critérios do GHS") → espirometria só se desenvolverem sinais ou sintomas respiratórios.
- 3.3 (funções com indicação de EPI respiratório) → só empregados com histórico de doença respiratória crônica ou sinais/sintomas.
- 3.4 (alteração espirométrica → conduta) → condicionado a resultado; mesma classe de DT-002X-03.
- 3.5 (pós-demissional asbesto, periodicidade igual à do RX) → DT-002X-02, já aberta.

#### R-ESP-03 — Espirometria por exposição a poeira de madeira `[INTERPRETADO]`

Cargo com exposição a poeira de madeira → espirometria **24 meses** em adm/per/MR/dem.

**Ressalva normativa.** O item 3.1 do Anexo III (base de R-ESP-02) dispara por "poeira mineral" — madeira é orgânica, fora do escopo textual da regra. ID separada de R-ESP-02 por mudança de escopo de substância (mineral → madeira), não faixa nova da mesma regra (mesmo critério de versionamento que separou R-RX-02 de R-RX-01). Mesmo par de PGRs de R-RX-03 (GHE-08 Carpintaria Fascino, GHE-04 Carpintaria Aurora), mesma médica, mesmo valor: Espirometria 24M nos dois. Parte da resolução de DT-003EJ-01 — ver R-RX-03 acima.

### 5.4 Raio-X de Tórax (OIT)

#### R-RX-01 — RX de tórax OIT (sílica/asbesto e PNOS) `[VALIDADO]`
Periodicidade do RX de tórax padrão OIT conforme **Anexo III da NR-07 (Portaria 567/2022)**. Depende de: agente, faixa de exposição vs. LEO, existência de avaliação quantitativa e tempo de exposição acumulado.

**Sílica / asbesto — COM avaliação quantitativa periódica:**

| Faixa (CLSC vs. LEO) | RX tórax OIT |
|---|---|
| ≤ 10% LEO | admissional apenas |
| 10% < CLSC ≤ 50% LEO | adm + 60M até 15 anos → 36M após |
| 50% < CLSC ≤ 100% LEO | adm + 36M até 15 anos → **24M** após |
| > 100% LEO | adm + 12M desde o início |

**Sílica / asbesto — SEM avaliação quantitativa** (canteiro sem laudo de higienista; caso mais comum):
- adm + **24M** até 15 anos de exposição → 12M após.

**Sílica — SEM avaliação quantitativa, COM avaliação qualitativa P×S no PGR** `[INTERPRETADO — prioridade na revisão de saída]` (DT-003EC-01):
- adm + **12M** constante, `[adm, per, MR, dem]`. Ver "Nota de aplicação (DT-003EC-01)" abaixo.

**PNOS** (poeiras de menor toxicidade), com ou sem medição:
- adm + **60M**. Nunca 24M.

**Notas:**
- "Sem avaliação quantitativa" é estado distinto de "qualitativa": dispara **24M**, não 12M. Corrige A-VAL-06 (v2), que simplificou demais. **Desde DT-003EC-01** o motor distingue os dois estados na extração: PGR silencioso → 24M (R-RX-01-sem); sílica com avaliação qualitativa P×S declarada → 12M (R-RX-01-qual).
- A periodicidade da **espirometria** (24M, R-ESP-02) é independente da do RX, apesar de os dois exames compartilharem o gatilho (poeira mineral, Anexo III). O RX roteia por faixa do Quadro 1 — 24M é a faixa sem-avaliação-quantitativa; a espirometria é 24M sempre, por força do item 3.1, que não roteia por faixa. Coincidência de valor em 24M, não dependência: quando o PGR traz medição, o RX muda de faixa e a espirometria não muda. `[003.EI]`
- O corte de 15 anos é **tempo de exposição acumulado** → resolvido pelo agendador, não pelo motor (ver D-ARQ-19).

**Implementação (002.L0, D-ARQ-20).** R-RX-01 é implementada como família de regras de periodicidade constante em `regras.yaml`, uma por faixa:

| Entrada | Predicado (`quando`) | Periodicidade | Encurtamento (>15a) |
|---|---|---|---|
| R-RX-01-adm | silica_asbesto_leo_ate_10 | só admissional | — |
| R-RX-01-sem | silica_asbesto_sem_medicao | 24M | → 12M |
| R-RX-01-qual | silica_qualitativa | 12M | — |
| R-RX-01-baixa | silica_asbesto_leo_10_50 | 60M | → 36M |
| R-RX-01-media | silica_asbesto_leo_50_100 | 36M | → 24M |
| R-RX-01-alta | silica_asbesto_leo_acima_100 | 12M | — |
| R-RX-01-pnos-ate10 | pnos_leo_ate_10 | só admissional | — |
| R-RX-01-pnos-10a100 | pnos_leo_10_100 | só admissional (motor) | — |
| R-RX-01-pnos-acima100 | pnos_leo_acima_100 | 60M | — |
| R-RX-01-pnos-sem | pnos_sem_medicao | 60M | — |

`R-RX-01` permanece o ID clínico estável; as entradas `R-RX-01-*` são implementação (D-ARQ-20). **Estado contraditório:** se o PGR declara `pct_LT` e ausência de avaliação quantitativa ao mesmo tempo, o motor emite pendência bloqueante (não escolhe faixa) — input incoerente vira pedido de correção, não chute (D-ARQ-08/13). **Valores conferidos `[DERIVADO — NR-7 Anexo III Quadro 1]`:** periodicidades, limiares e corte de 15 anos conferidos contra o texto literal do Anexo III da NR-07, Quadro 1 (Portaria MTP 567/2022), no site do MTE (002.N). Faixas fechadas com limite superior inclusivo (`≤`): >10 e ≤50; >50 e ≤100; >100. Variável de roteamento é o CLSC = limite superior do IC 95% da média aritmética (distribuição lognormal), conforme definição literal do Quadro 1 — NÃO é percentil 95. NOTA 2 do Quadro 1: trabalhador com exposição reduzida que esteve em concentração maior por ≥1 ano mantém o intervalo do período de maior exposição (a modelar — ver DT). PNOS segue o Quadro 2, não o Quadro 1 (ver R-RX-01-pnos e DT própria).

**PNOS — refinamento do Quadro 2 (002.X).** A entrada única `R-RX-01-pnos` (60M constante) está DEPRECATED, sucedida pela família de 4 faixas acima (mesma razão de D-ARQ-20 já usada no Quadro 1). Texto literal do Quadro 2 conferido (Anexo III NR-07, Portaria 567/2022, site MTE):
- pnos_leo_ate_10 (CLSC ≤ 10% LEO) → só admissional.
- pnos_leo_10_100 (10% < CLSC ≤ 100% LEO) → admissional; RX único **após 5 anos** de exposição (gatilho de tempo acumulado → agendador, D-ARQ-19, em Motivo.detalhe); **repetir a critério clínico** (não-periódico → lembrete operacional, D-ARQ-05). NÃO é 60M recorrente. `[DERIVADO — NR-7 Anexo III Quadro 2 (Portaria 567/2022)]`; a modelagem "evento único + lembrete" (vs. periodicidade) é `[INTERPRETADO]`.
- pnos_leo_acima_100 / pnos_sem_medicao → adm + 60M ("a cada 5 anos").
Fração do PNOS é sempre RESPIRAVEL (Quadro 2 mede "poeira respirável"); sem ramo TOTAL.

**PNOS — implementação (002.Y).** A família `R-RX-01-pnos-*` foi materializada em código (PR #49, commit 9bb243e): predicados de faixa `pnos_leo_ate_10`/`pnos_leo_10_100`/`pnos_leo_acima_100`/`pnos_sem_medicao` (predicados.py) + ramo PNOS no LEO-resolver (3 mg/m³ resp, nível 4) + 4 entradas em regras.yaml (status INTERPRETADO) + `R-RX-01-pnos` única marcada DEPRECATED (mantida por contrato de ID; carregador passa a filtrar DEPRECATED). Periodicidades: ate_10 e 10_100 → só admissional; acima_100 e sem_medicao → adm + 60M. O roteamento de PNOS medido em mg/m³ usa injeção de fração RESPIRAVEL (D-ARQ-29). Pendências abertas: lembrete "repetir após 5 anos a critério clínico" da faixa 10_100 não materializado (DT-002Y-01); validação contra Viverde real adiada (DT-002Y-02).

**LEO do PNOS — reconciliação (002.X).** O rodapé do Quadro 2 define PNOS pela condição "não possuir um LEO definido", mas a tabela roteia por % do LEO. Reconciliação: o material é PNOS porque não tem LEO *próprio*; o roteamento usa o LEO *genérico* de PNOS = TLV-PNOS da ACGIH = **3 mg/m³ (respirável)**, via NR-09 item 9.6.1.1 (nível 4 do LEO-resolver, D-ARQ-24). `[DERIVADO — ACGIH TLV-PNOS, via NR-9 9.6.1.1]` no valor; `[INTERPRETADO]` na articulação "este genérico alimenta o Quadro 2" — não está escrita na norma; é o item de maior incerteza desta sessão, inspecionar PRIMEIRO na revisão de saída (D-ARQ-27).

**Pré-requisito para o predicado `pnos` ser computável.** Para o motor classificar um agente como PNOS, `agentes.yaml` precisa carregar as 3 condições ACGIH 2017 (rodapé do Quadro 2): (a) sem LEO próprio definido; (b) insolúvel/pouco solúvel; (c) baixa toxicidade (não citotóxico/genotóxico/reativo, não radioativo, não sensibilizante). Sem esse metadado o predicado `pnos` não tem como ser decidido. Implementação futura.

**Asbesto — origem do LEO (002.X).** A periodicidade do asbesto NÃO muda: o Quadro 1 já o cobre nas mesmas faixas de sílica. O que faltava era a origem do LEO. Resolvido: não há LEO setorial de mineração para asbesto (nível 1 vazio); LEO = nível (3) do resolver = LT da NR-15 Anexo 12 = **2,0 f/cm³** (fibras respiráveis), FIXO (não fórmula), unidade f/cm³ (não mg/m³), fração sempre respirável, pct_quartzo irrelevante. Fibra respirável = Ø<3µm, comprimento>5µm, razão L/D>3:1. Anfibólios (crocidolita/amosita/etc.) proibidos, sem LT. `[DERIVADO — NR-15 Anexo 12 itens 12/12.1 (Portaria SSST 1/1991 e 22/1994); confirmar texto oficial MTE antes de considerar VALIDADO]`. Detalhe arquitetural em D-ARQ-24 changelog 002.X.

**Carvão mineral — lacuna (002.X).** O Quadro 1 vigente é "Sílica, Asbesto **ou Carvão Mineral**" (incluído pela 567/2022). O predicado `silica_asbesto_*` cobre 2 dos 3 agentes do Quadro 1 — fere D-ARQ-06. Ver DT-002X-01 (LEO do carvão a resolver). Até lá o carvão não entra na família de roteamento.

**Demissional condicional do Quadro 1 (002.X) — dado para o agendador.** A norma adiciona demissional condicionado ao reaproveitamento (D-ARQ-11/19): último exame há mais de **2 anos** nas faixas ≤10% e 10–50%; há mais de **1 ano** nas faixas 50–100%, >100% e **sem-avaliação**. A fronteira é em 50%; sem-avaliação usa 1 ano. Motor emite a faixa-base; o agendador aplica o demissional condicional com essa granularidade.

**Base normativa:** Anexo III da NR-07 (Portaria 567/2022). Validação clínica: Dra. Carolini, 05/2025.

**TODO normativo — RESOLVIDO em 002.N `[DERIVADO]`:** faixas, periodicidades e corte de 15 anos do Quadro 1 (sílica/asbesto) conferidos contra o texto literal do Anexo III (Portaria 567/2022, site do MTE). Resíduos abertos: (a) classificador de faixa deve rotear por CLSC e tratar bordas com `≤` (fix de código); (b) PNOS achata o Quadro 2 (DT); (c) R-RX-02 fumos sem âncora no Anexo III (DT).

**Nota de aplicação (003.EH, mesma ID)** — ausência de laudo é ramo do Quadro 1, não pendência. O Quadro 1 do Anexo III parte as empresas em dois ramos exaustivos: "Empresas com medições quantitativas periódicas" (as 4 faixas por LSC/LEO) e "Empresas sem avaliações quantitativas" ("na admissão; a cada 2 anos até 15 anos de exposição, e, após, a cada ano; e na demissão, se o último exame foi realizado há mais de 1 ano"). Não há terceiro ramo — toda empresa cai em um dos dois, e nos dois o RX é emitido. `[DERIVADO — NR-07 Anexo III Quadro 1 (Portaria MTP 567/2022), texto oficial MTE, conferido em 003.EH]`

Até 003.EG o motor mantinha um terceiro estado sem correspondente normativo: `_helper_silica_asbesto` devolvia `Ausente` bloqueante quando o risco chegava sem `quantificacao`, e `R-RX-01-sem` — que já prescrevia o ramo correto desde a v6 — era inalcançável em produção: `sem_avaliacao_quantitativa=True` só era escrito por fixture, `parsear_quantificacao` nunca o seta `[VERIFICADO — git grep, 003.EH]`. Corrigido em `7dd68e6`: o ramo `q is None` devolve `Quantificacao(sem_avaliacao_quantitativa=True)`, espelhando `_helper_pnos`/Quadro 2. Conduta clínica inalterada — a regra sempre prescreveu 24M (12M após 15 anos) para sem-avaliação; muda o mapeamento input→estado, que é camada de motor. Mesma ID; precedente R-PKG-ATIVCRIT (003.ED).

Ponte `[INTERPRETADO — prioridade na revisão de saída]`: a norma fala de empresa sem avaliações; o motor só vê o documento. Ler "PGR silencioso" como "empresa sem avaliação" é leitura do Arquiteto. Risco nomeado: empresa que tem laudo omitido do PGR recebe 24M onde a faixa real poderia ser 12M (>100% LEO) — subdimensionamento. A mitigação (sinal não-bloqueante de confirmação) depende de D-ARQ-28 — ver DT-003EH-01.

Fronteira preservada: afirmação incompleta continua bloqueando (ramos (c)/(d) do helper) — `pct_LT` junto com `sem_avaliacao_quantitativa`, ou `valor` sem `pct_quartzo`/`fracao`. Ali a empresa se declara no ramo "com medições" e escolher faixa inventaria número (D-ARQ-08/13). Generalização da regra de mapeamento em D-ARQ-68.

Efeito medido (Fascino, `rodar-offline` @ `37cdda6`): 14 dos 19 GHEs passam a emitir `rx_torax_oit` 24M / `periodicidade_apos_15a` 12 / `[adm, per, MR, dem]` / `R-RX-01-sem`; pendências `predicado_ausente` de `silica_asbesto_*` 70 → 0; linhas de exame 104 → 118; status 2 VÁLIDA / 15 PARCIAL / 2 BLOQUEADA → 2 / 16 / 1 (GHE-12 BLOQUEADA→PARCIAL, único a mudar).

**Nota de aplicação (DT-003EC-01, mesma ID — ramo novo `R-RX-01-qual`).** `[INTERPRETADO — prioridade na revisão de saída]`

*Conduta.* Sílica sem avaliação quantitativa **com** avaliação qualitativa P×S declarada pelo PGR na linha do risco → RX tórax OIT **12M** constante, `[adm, per, MR, dem]`. PGR silencioso segue em `R-RX-01-sem` (24M → 12M após 15 anos). Decisão do Diovanni em 23/09/2026 ("12M, o motivo deve ser a sílica qualitativa"), sobre a conduta convergente das médicas nos 4 pares pareados.

*Por que não é `[DERIVADO]`.* O literal do Quadro 1 tem dois ramos exaustivos, e a avaliação só qualitativa cai no ramo "sem avaliações quantitativas" (24M). 12M é intervalo **menor** que o desse ramo: mais protetivo, não contrário ao Quadro. O fundamento é matriz-precedente, e pela cl.1 de D-ARQ-81 o viés vai declarado: construção civil, 2 médicas (Patrícia: Porto Araras I 06/07/26, Vila Brasil Escritório 26/08/26; Carolini: SPE 0030 Fascino 08/07/26); 24M aparece em 15 das 34 matrizes assinadas do acervo, sem PGR completo para conferir o estado da sílica. Não amplia universo (cl.1 c): mesmos trabalhadores, mesmo exame, intervalo menor. Conferência do texto vigente do Quadro 1 (D-ARQ-69) **refeita em 24/09/2026** no PDF `nr-07-atualizada-2022-1_4.pdf` fornecido pelo Diovanni em 24/09/2026 (39 p., sha256 `f27b63bb…938b63`; cabeçalho lista alterações até a Portaria MTP n.º 567, de 10/03/2022 — conferência contra o texto, não contra a listagem da página, per nota 003.FA de D-ARQ-69): Quadro 1 do Anexo III com os mesmos dois ramos lidos em 003.EH — "Empresas sem avaliações quantitativas: na admissão; a cada 2 anos até 15 anos de exposição, e, após, a cada ano; e na demissão, se o último exame foi realizado há mais de 1 ano". Nenhum ramo para avaliação qualitativa; 12M segue abaixo do intervalo do ramo aplicável (mais protetivo), marcador `[INTERPRETADO]` mantido.

*Sinal de extração.* "Avaliação qualitativa" = colunas **S · P · NÍVEL DE RISCO** preenchidas na própria linha do risco (matriz P×S: Irrelevante/Baixo/Moderado/Alto/Crítico). Medido nos 3 PGRs da família Consciente: 587/587 linhas de risco com a banda capturada; toda linha de sílica com nível (BAIXO/MODERADO). Os PGRs declaram a leitura no próprio bloco — Porto Araras, NOTA 2: "até que seja executada a medição esta avaliação será qualitativa por julgamento técnico"; Vila Brasil, coluna AVALIAÇÃO QUANTITATIVA: "⚠ Avaliação ainda qualitativa — resultado quantitativo pendente de medição". "NÃO DEFINIDO" (8/172 em Porto Araras, só em "Ausência de agente nocivo") é declaração de não-avaliação, não nível.

*Escopo.* Só sílica. Asbesto qualitativo segue em `R-RX-01-sem` — sem caso medido nem decisão. Só a rota determinística (`parser_familia_consciente`) extrai a avaliação; a rota LLM (`transcritor_gemini_pgr`) e a rota card deixam `avaliacao_qualitativa=""`, e a sílica ali segue em 24M — recorte declarado, não esquecido.

*Efeito medido* (`scripts/comparar_matriz_gabarito`, antes = worktree `main cadcd33`, depois = working tree): divergência de periodicidade RX OIT 24M×12M **27 → 0** (Porto Araras I), **8 → 0** (Vila Brasil Escritório), **31 → 0** (Fascino); todas as demais células idênticas antes/depois nos três pares.

Nota de procedência — LSC vs. CLSC. O literal do Quadro 1 é LSC ("Limite superior do intervalo de confiança da média aritmética estimada para uma distribuição lognormal com confiança estatística de 95%"). Este protocolo, D-ARQ-24, DT-002V-01 e DT-003CB-01 escrevem "CLSC" para a mesma grandeza, com definição idêntica. Rótulo divergente do texto oficial, semântica intacta; os sítios históricos ficam preservados para rastreabilidade.

#### R-RX-02 — Fumos metálicos `[INTERPRETADO — prioridade na revisão de saída]`
Cargo com exposição a fumos metálicos (incluindo soldador) → RX **60 meses** em adm/per/MR/dem.
**Ressalva normativa (002.N):** o 60M NÃO tem âncora no Anexo III da NR-07 — fumos metálicos não são poeira mineral (Quadro 1) nem PNOS (Quadro 2). O valor provém da matriz Patrícia ou de analogia, não de norma vigente conferida. Além disso, DT-002K-02 (resolvida) firmou que o risco é por exposição real ao metal individual (Mn, Cr⁶⁺...), não pela categoria genérica "fumos metálicos". O roteamento correto de RX por fumos depende da decomposição em metais individuais — ver DT-D3-02. Até lá, R-RX-02 mantém o caso âncora (soldador) funcional, mas o 60M é [INTERPRETADO], não [VALIDADO].

**Implementação (002.L0).** R-RX-02 passou a existir como regra executável em `regras.yaml` (`quando: fumos_metalicos → RX 60M`). Até a 002.L0 constava apenas como `protocolos_especiais` documental em `agentes.yaml`, sem regra correspondente — fumos metálicos não emitia RX no motor.

#### R-RX-03 — Poeira de madeira `[INTERPRETADO]`

Cargo com exposição a poeira de madeira → RX **60 meses** em adm/per/MR/dem.

**Ressalva normativa.** O 60M NÃO tem âncora no Anexo III da NR-07 — poeira de madeira não é sílica/asbesto/carvão mineral (Quadro 1) nem PNOS (Quadro 2, "não especificado de outra maneira": madeira tem nome e classificação próprios, não é resíduo residual do Quadro). `is_carcinogeno_iarc: true` em `agentes.yaml` `[DERIVADO — IARC Monographs Vol. 62 (1995), "Wood Dust and Formaldehyde", Grupo 1; reafirmado no Vol. 100C (2012); fonte internacional, não gov.br/MTE — a NR-07/NHO brasileiras remetem carcinógenos ao Anexo V, sem lista própria]`. O valor 60M vem de matriz-precedente, não de norma brasileira conferida: medido em **2 PGRs independentes**, mesma médica (Dra. Patrícia Montalvo Moraes), mesmo cargo (Carpintaria) — GHE-08 (PGR CONSCIENTE SPE 0030 FASCINO, 15.07.26) e GHE-04 (PGR CMO Residencial Aurora Lago das Rosas, 27.08.26), ambos RX 60M. Sensibilização respiratória (asma ocupacional por poeiras de madeira) segue `[INCERTO — não conferido em fonte primária]`; não bloqueia esta regra porque o regime não depende dessa faceta.

**Origem — DT-003EJ-01 (RESOLVIDA).** Aberta em 003.EJ pela ausência de RX em GHE-08 (Carpintaria) do Fascino: o motor não emitia porque "Poeira de madeira" ficava `vocabulario_ausente` (comportamento correto, por desenho, até a decisão de slug próprio ser tomada). Resolvida nesta implementação com o 2º PGR medido (Aurora) confirmando o mesmo valor da matriz humana — gatilho de reabertura satisfeito, ver `docs/PENDENCIAS_CLINICAS.md`.

### 5.5 ECG

#### R-ECG-01 — Indicação `[VALIDADO]`
ECG em **adm/per/MR**, periodicidade conforme periódico da matriz, **sem restrição etária**, para:
- Operador de máquinas pesadas
- Trabalho em altura
- Espaço confinado
- Exposição à eletricidade

### 5.6 Acuidade Visual

#### R-VIS-01 — Atividades críticas `[VALIDADO]`
Acuidade visual em **adm/per/MR** para toda atividade crítica:
- Eletricista
- Trabalho em altura
- Motorista
- Espaço confinado
- Soldador

**Exceção do soldador:** soldador é o **único caso** que tem acuidade visual também **no demissional**.

#### R-VIS-02 — Porteiro `[VALIDADO]`
Porteiro também recebe acuidade visual em **adm/per/MR**, **sem demissional**.

### 5.7 Avaliação Psicossocial

#### R-PSY-01 — Indicações `[DEPRECATED — sucedida por R-PSY-02]`
- **Espaço confinado** → sempre
- **Trabalho em altura** → somente se houver **atividade crítica concomitante** (ex: operação de máquina pesada) **E** o PGR reconheça risco psicossocial
- **Risco psicossocial classificado como moderado** (ou superior) no PGR → sempre, independente da atividade

#### R-PSY-02 — Avaliação Psicossocial + Av. Médica de Saúde Mental, incondicional `[DEPRECATED — fundamento refutado por n=2 pós-protocolo-de-setembro/2026, sucedida por R-PSY-03]`
Todo trabalhador, sem condição de risco, recebia **Avaliação Psicossocial** e **Av. Médica de Saúde Mental**, 12 meses, em **adm/per/MR**.

**Base normativa** `[DERIVADO — texto oficial MTE, conferido 31/07/2026]`: NR-01 itens 1.5.3.1.4, 1.5.3.2.1 e 1.5.4.4.5.3 (redação dada pela Portaria MTE nº 1.419, de 27/08/2024; entrada em vigor em 26/05/2026 pela Portaria MTE nº 765, de 15/05/2025) obrigam **inventariar e gerenciar** o fator de risco psicossocial relacionado ao trabalho (FRPRT) — nenhum dos itens **prescreve exame**. A conduta (quais exames, qual periodicidade) era derivada da prática medida no corpus, não da norma.

**Medição do acervo** (`matrizes_originais/`, 31/07/2026): matrizes **anteriores** a 26/05/2026 (13 docs, 575 cargos) emitem Avaliação Psicossocial em 1% e Av. Saúde Mental em 0%; matrizes **posteriores** a 26/05/2026 (6 docs, 284 cargos, 5 clientes distintos, 2 médicas distintas — Carolini e Patrícia) emitem os dois em 99%. Confundidor "preferência da médica" testado e descartado: ambas assinam documentos dos dois lados do corte. Grafia medida nos 6 documentos pós-vigência: `Avaliação Psicossocial (ADM, PER, MRO)` e `Av. Médica de Saúde Mental (ADM, PER, MRO)`, 271 de 283 ocorrências cada; periodicidade explícita, quando aparece (13 ocorrências), é sempre 12 meses.

**Por que era incondicional, não condicionado à declaração no PGR:** desenho candidato (gatilho = inventário psicossocial presente no PGR) testado e refutado à época — o PGR "Ricco 2026 Administração" não declara FRPRT (0 ocorrências de "FRPRT"/"Inventário de Riscos Psicossociais") e sua matriz correspondente emitia os dois exames em 100% dos 12 cargos mesmo assim. Silêncio documental não desobrigava — mesma postura de D-ARQ-68.

**Sucede R-PSY-01** (`[DEPRECATED]` acima): mudança de escopo de aplicação (condicionada → incondicional) exigiu ID nova; corpo de R-PSY-01 preservado por rastreabilidade histórica.

**Fundamento refutado (17/09/2026), sucedida por R-PSY-03.** 2 matrizes reais pós-protocolo-de-setembro/2026, desfechos opostos: Ricco Hetrin 14/09 (validada) sai com **zero** exame psicossocial em 28/28 cargos — PGR correspondente lido por completo (197 páginas), zero ocorrência de marcador de inventário psicossocial, inclusive no Pedreiro com risco de altura documentado no próprio PGR (refuta a hipótese de cascata por atividade crítica). CMO Residencial Varandas Flamboyant 16/09 (validada) sai incondicional em todo GHE, marcador presente no PGR. Confirmado pelo Diovanni: quem decide é o **engenheiro que elabora o PGR** (inclui ou não a seção de inventário psicossocial), não classificação de risco nem atividade — o corpus de 31/07/2026 que fundamentava a incondicionalidade estava medindo prática anterior a esta distinção ficar visível. Mesmo padrão de `D-ARQ-81`/`R-AUD-04` (precedente de corpus enviesado não amplia universo normativo), com uma diferença do molde da cl.2: aqui HÁ sucessora, porque a norma segue obrigando inventariar o FRPRT (não desaparece), só a condição de disparo do exame muda. Corpo preservado por rastreabilidade histórica.

#### R-PSY-03 — Avaliação Psicossocial + Av. Médica de Saúde Mental, condicionada ao PGR `[INTERPRETADO]`
Trabalhador de GHE cujo PGR documenta a seção de inventário de risco psicossocial (marcador "Inventário de Riscos Psicossociais"/COPSOQ/FRPRT, `detectar_psicossocial` em `extracao_pgr.py`) recebe **Avaliação Psicossocial** e **Av. Médica de Saúde Mental**, 12 meses, em **adm/per/MR** — mesma conduta de R-PSY-02, condição de disparo diferente.

**Base normativa:** mesma de R-PSY-02 — NR-01 itens 1.5.3.1.4, 1.5.3.2.1 e 1.5.4.4.5.3, que obrigam inventariar/gerenciar o FRPRT sem prescrever exame.

**Por que condicionada ao PGR, não mais incondicional:** ver "Fundamento refutado" em R-PSY-02, acima. A granularidade medida é por PGR inteiro — o sinal não varia por GHE dentro do mesmo documento nos 2 casos-âncora.

**Risco residual, não resolvido `[INTERPRETADO — n=2, mesma classe de obra nos dois PGRs (construção civil)]`:** não sabemos ainda se a granularidade é sempre por PGR inteiro ou se pode variar por GHE quando o elaborador documenta parcialmente. Detalhe em `DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-01`, `PENDENCIAS_CLINICAS.md`.

**Sucede R-PSY-02** (`[DEPRECATED]` acima): mudança de escopo de aplicação (incondicional → condicionada) exige ID nova, mesma convenção de R-PSY-01→R-PSY-02.

### 5.8 Vibração

#### R-VIB-01 — RX de coluna lombo-sacra `[VALIDADO]`
Exposição confirmada a **vibração de corpo inteiro** → RX coluna **lombo-sacra** em **adm + MR**.
**Justificativa clínica:** vibração agrava patologia preexistente de coluna.
**Observação:** essa é a única conduta da Dra. Carolini que ela mesma considerou "fora do que as normas explicitamente exigem".

#### R-VIB-02 — Vibração ativa audiometria `[VALIDADO]`
Qualquer vibração (corpo inteiro ou mãos-braços) → **audiometria 12M**, mesmo com ruído abaixo do nível de ação. Ver R-AUD-01.

**Nota de aplicação 003.EJ.** A regra existia em `regras.yaml` desde 002.G, mas só era alcançável por `vibracao_corpo_inteiro` — e mesmo essa perna só por coincidência ortográfica (`Vibração (corpo inteiro)` normaliza para o próprio slug, sem alias). Com os aliases Tier 1-C de D-ARQ-70 (VMB/VCI + grafias de corpus), a perna mão-braço passa a ser alcançável pela primeira vez.

Efeito medido no Fascino (003.EJ, rodada offline determinística): a pendência `vocabulario_ausente` de `Vibrações localizadas (mão e braço)` cai de 9 para 0. GHE-12 (Betoneira), que hoje não emitia nenhuma audiometria (`atividade_critica=False`, `ruido_acima_acao=AUSENTE`), ganha 1 linha nova de audiometria 12M [ADM, PER, MR] por R-VIB-02. Os outros 8 GHEs (07, 08, 09, 10, 11, 16, 17, 18) já emitiam audiometria por `R-PKG-ATIVCRIT`/`R-AUD-01` e passam a somar R-VIB-02 como motivo adicional, sem linha nova (dedup por piso, R-GHE-03/D-ARQ-39). Total de linhas de exame na matriz: 132 → 133 (+1, a linha de GHE-12).

Um desses 8 (GHE-16) expôs um efeito de segunda ordem em R-AUD-02, não previsto antes da medição — ver **DT-003EJ-02**. Conteúdo clínico de R-VIB-02 inalterado; nenhuma R-* criada ou modificada.

### 5.9 Biomonitoramento Químico

#### R-BIO-01 — Periodicidade fixa `[VALIDADO]`
Todo exame de biomonitoramento de agente químico = **6 meses**. Sem exceção.

#### R-BIO-02 — Matriz temporal por Anexo NR-07 `[DEPRECATED — sucedida por R-BIO-04 em 003.AA; ver DT-FDS-01]`

> **Redação original preservada para rastreabilidade (não remover — auditoria histórica do PCMSO):**
> - Anexo I (carcinógenos sem LT seguro) → biomonitoramento apenas no periódico
> - Anexo II (com LT) → biomonitoramento em adm + per + RT + MR + dem

**Motivo da depreciação.** O critério "Anexo I/II = carcinógeno-sem-LT / com-LT" contradiz o Anexo I vigente (567/2022): o eixo é Quadro 1 (IBE/EE) vs Quadro 2 (IBE/SC) e "Anexo II" da NR-07 é ruído. A reclassificação muda a saída temporal de agentes de alta frequência (solventes) → exigiu nova ID. Sucessora: R-BIO-04.

#### R-BIO-03 — Manganês `[VALIDADO]`
Qualquer exposição confirmada a Mn → **manganês sanguíneo semestral em adm + per + MR**. Base: NR-15, independente do LT.

#### R-BIO-04 — Matriz temporal por Quadro do Anexo I (NR-07) `[DERIVADO — NR-07 Anexo I + itens 7.5.13/7.5.15/7.5.19.4/7.5.19.5, Portaria MTP 567/2022, texto oficial MTE]`

Sucede R-BIO-02. O eixo do biomonitoramento químico é o **Quadro do Anexo I onde o indicador da substância está listado** (natureza do indicador: IBE/EE vs IBE/SC) — NÃO carcinogenicidade nem presença de LT.

- **Quadro 1 — IBE/EE** (exposição excessiva; sem caráter diagnóstico, afere absorção e sinaliza exposição acima do LEO): biomonitoramento **6M, obrigatório apenas no periódico**. `[DERIVADO — literal 7.5.15]` Alteração → médico informa o PGR para reavaliação dos riscos (7.5.19.4); não é conduta clínica individual.
- **Quadro 2 — IBE/SC** (significado clínico; evidencia disfunção orgânica): biomonitoramento **6M em adm + per + RT + MR + dem**. `[DERIVADO — 7.5.15 a contrario: o item exime só o Quadro 1; o Quadro 2 segue a obrigação geral de 7.5.6/7.5.12. Inferência expressio-unius, não frase literal afirmativa — inspecionar na revisão de saída]` Alteração → CAT/afastamento/Previdência/reavaliação PGR (7.5.19.5).

Ambos a 6M ±45d (7.5.13). "Obrigatório apenas no periódico" não impede o médico de solicitar exame extra em outro momento (7.5.18).

**Roteamento substância→Quadro** (leitura direta da tabela do Anexo I, não da carcinogenicidade):
- **Quadro 2 (IBE/SC), 4 entradas:** cádmio e compostos inorgânicos; chumbo e compostos inorgânicos (Pb-S + ALA-U); inseticidas inibidores da colinesterase; flúor, ácido fluorídrico e fluoretos inorgânicos.
- **Quadro 1 (IBE/EE):** todo o restante da tabela — solventes (tolueno, xilenos, MEK, acetona, n-hexano, estireno…), Cr⁶⁺, CO, benzeno (via SPMA/TTMA), etc.

**Carcinógenos têm regime próprio no Anexo V** (gatilho: exposição >10% do LEO ou sem avaliação ambiental; prontuário 40 anos; benzeno remetido a IN SSST 02/1995 + Portaria de Consolidação 5/MS). A carcinogenicidade **não** desloca a substância para "só periódico" — o momento é decidido pelo Quadro do indicador.

**Caso-âncora da mudança de saída (motiva nova ID, não R-BIO-02 corrigido):** o **tolueno** e os solventes comuns (xileno, MEK, acetona — os agentes mais frequentes nas matrizes reais) têm LT, não são carcinógenos, e o indicador é IBE/EE (Quadro 1) → **só periódico**. O critério de R-BIO-02 ("com LT → cinco momentos") os emitia em adm+per+RT+MR+dem → **superdimensionamento**. Como muda a matriz temporal de agentes de alta frequência → nova ID. (Cádmio NÃO serve de contra-exemplo: carcinógeno E com LT ao mesmo tempo, ambíguo nos dois baldes do critério antigo.)

R-BIO-01 (6M) e R-BIO-03 (manganês, fora do Anexo I, via NR-15) inalterados quanto a conteúdo.

> **Changelog 003.AD (mesma ID — mapa biomarcador + confirmação da lista contra texto oficial).** Quadro 1 (41 substâncias) e Quadro 2 (4) conferidos inteiros no texto oficial (Portaria 567/2022, gov.br/MTE). Quadro 2 confirmado: cádmio e comp. inorg. (cádmio urina); chumbo e comp. inorg. (Pb-S **e** ALA-U — dois indicadores simultâneos); inseticidas inibidores da colinesterase (acetilcolinesterase eritrocitária *ou* butilcolinesterase plasma/soro); flúor/HF/fluoretos inorg. (fluoreto urinário). Cardinalidade não-uniforme (1:1 / N-alternativos / 2-simultâneos) é o que mantém a forma do emissor adiada (D-ARQ-38 cl.3). Dos 4 agentes SC do Quadro 2, o vocabulário modela só chumbo; dos 41 EE do Quadro 1, modela 12. `[DERIVADO — NR-07 Anexo I Quadros 1/2, Portaria 567/2022, texto oficial MTE]`

Mapa agente→biomarcador dos agentes do vocabulário (insumo para o emissor de biomonitoramento, fatia d de D-ARQ-38 — mecanismo ainda data-bloqueado):

| agente | Quadro | biomarcador (Anexo I) |
|---|---|---|
| acetona | 1/EE | acetona urina |
| arsenio | 1/EE | As inorg. + metabólitos metilados urina (exceto arsina/arsenato de gálio) |
| benzeno | 1/EE | S-PMA *ou* TTMA urina |
| dissulfeto_de_carbono | 1/EE | TTCA urina ("Sulfeto de carbono" no Anexo) |
| estireno | 1/EE | ác. mandélico+fenilglioxílico *ou* estireno urina |
| mercurio | 1/EE | mercúrio urina ("Mercúrio metálico"; orgânico fora) |
| metil_etil_cetona | 1/EE | MEK urina |
| monoxido_de_carbono | 1/EE | COHb *ou* CO ar exalado |
| n_hexano | 1/EE | 2,5-hexanodiona urina |
| tolueno | 1/EE | tolueno sangue/urina *ou* o-cresol urina |
| tricloroetileno | 1/EE | ác. tricloroacético *ou* tricloroetanol |
| xileno | 1/EE | ác. metilhipúrico urina |
| cromo hexavalente (comp. solúveis) | 1/EE | cromo urina (FJFS 25 µg/L; alt. aumento-na-jornada 10 µg/L, mesmo analito) |
| cobalto | 1/EE | cobalto urina |
| fenol | 1/EE | fenol urina |
| metanol | 1/EE | metanol urina |
| diclorometano | 1/EE | diclorometano urina |
| etilbenzeno | 1/EE | soma mandélico+fenilglioxílico urina (mesmo analito do estireno) |
| anilina | 1/EE | metahemoglobina sangue *ou* p-aminofenol urina |
| nitrobenzeno | 1/EE | metahemoglobina sangue |
| indutores de metahemoglobina (classe) | 1/EE | metahemoglobina sangue |
| chumbo (inorgânico) | 2/SC | Pb-S **e** ALA-U |
| cádmio (inorgânico) | 2/SC | cádmio urina |
| flúor / HF / fluoretos inorgânicos | 2/SC | fluoreto urinário |
| inseticidas inibidores da colinesterase | 2/SC | acetilcolinesterase eritrocitária *ou* butirilcolinesterase plasma/soro |
| tricloroetano_111 | 1/EE | ácido tricloroacético urina (canônico entre 4 opções; exame compartilhado com tricloroetileno) |
| butadieno_13 | 1/EE | 1,2-dihidro-4-(N-acetilcisteína)butano urina |
| hdi | 1/EE | 1,6-hexametilenodiamina urina |
| metoxietanol_2 | 1/EE | ácido 2-metoxiacético urina (compartilhado com metoxietilacetato_2) |
| metoxietilacetato_2 | 1/EE | ácido 2-metoxiacético urina (compartilhado com metoxietanol_2) |
| propanol_2 | 1/EE | acetona urina (exame compartilhado com acetona) |
| tdi | 1/EE | isômeros 2,4 e 2,6 toluenodiamino urina (soma dos isômeros) |
| butoxietanol_2 | 1/EE | ácido butoxiacético urina (BAA) |
| chumbo_tetraetila | 1/EE | chumbo urina |
| ciclohexanona | 1/EE | ciclohexanol urina (canônico entre 2 opções) |
| clorobenzeno | 1/EE | 4-clorocatecol urina (canônico entre 2 opções) |
| etoxietanol | 1/EE | ácido etoxiacético urina (compartilhado com etoxietilacetato) |
| etoxietilacetato | 1/EE | ácido etoxiacético urina (compartilhado com etoxietanol) |
| furfural | 1/EE | ácido furóico urina |
| metil_butil_cetona | 1/EE | 2,5-hexanodiona urina (exame compartilhado com n_hexano) |
| mibk | 1/EE | MIBK urina |
| n_metil_2_pirrolidona | 1/EE | 5-hidroxi-N-metil-2-pirrolidona urina |
| dimetilacetamida | 1/EE | N-metilacetamida urina |
| dimetilformamida | 1/EE | N-metilformamida total urina (canônico entre 2 opções) |
| oxido_de_etileno | 1/EE | adutos HEV em hemoglobina |
| tetracloroetileno | 1/EE | tetracloroetileno sangue (canônico entre 2 opções) |
| tetrahidrofurano | 1/EE | tetrahidrofurano urina |

> **Changelog 003.CU (mesma ID — materialização + correção de biomarcador do tolueno).** A família `R-BIO-04-<agente>` foi materializada em `regras.yaml`/`exames.yaml` (D-ARQ-38 fatia d, 12 regras). Entre os agentes multi-opção do mapa acima, o emissor adotou o canônico da Matriz Dra. Patrícia 06/2025, confirmado contra NR-7 vigente: **tolueno → o-cresol na urina** (`ortocresol_urina`), CO → COHb, TCE → ác. tricloroacético, estireno → soma mandélico+fenilglioxílico (exame único). Correção rastreável: a spec de 003.CT havia escolhido "tolueno urina" (`tolueno_urina`) — **erro**: não é IBE; o indicador vigente é o-cresol (Portaria SEPRT 2020, alinhada ACGIH; ácido hipúrico é o antigo). Corrigido antes da implementação; `tolueno_urina` nunca esteve em produção. Saída afetada (novo slug emitido) mas mesma ID — a família materializa R-BIO-04, não cria regra nova. `[DERIVADO — NR-07 Anexo I Quadro 1 rev.2020; Matriz Patrícia 06/2025]`

> **Changelog 003.CV (mesma ID — Quadro 2/SC completo).** A família `R-BIO-04-<agente>` ganhou os 3 agentes restantes do Quadro 2 (IBE/SC): **cádmio** (cádmio urina), **flúor/HF/fluoretos inorgânicos** (fluoreto urinário) e **inseticidas inibidores da colinesterase** (acetilcolinesterase eritrocitária) — todos `[adm,per,RT,MR,dem]` 6M. Quadro 2 passa de 1/4 (só chumbo) a **4/4**. Biomarcadores confirmados contra a Matriz Dra. Patrícia 06/2025 (aba "Periodicidade Exames"), que também confirmou empiricamente o eixo de R-BIO-04: os agentes EE aparecem só com periódico, os 4 SC com os 5 momentos. O inseticida tem indicador **"OU"** (acetilcolinesterase eritrocitária *ou* butirilcolinesterase plasma/soro) → adotado o 1º canônico (listado primeiro no Quadro 2, enzima-alvo específica); `[INTERPRETADO — escolha do canônico, prioridade na revisão de saída]`. Modelado como slug-classe único (não por praga), alinhado a Anexo I + Matriz. Mesma ID — a família materializa R-BIO-04, sem regra nova. `[DERIVADO — NR-07 Anexo I Quadro 2, Portaria 567/2022; Matriz Patrícia 06/2025]`

> **Changelog 003.CW (mesma ID — Quadro 1/EE lote 1).** A família `R-BIO-04-<agente>` ganhou 9 agentes IBE/EE do Quadro 1, todos `[per]` 6M / um exame: **cromo hexavalente** (cromo urina), **cobalto**, **fenol**, **metanol**, **diclorometano**, **etilbenzeno** (soma mandélico+fenilglioxílico — reusa o slug do estireno), e o cluster metahemoglobina: **anilina**, **nitrobenzeno** e a classe **indutores de metahemoglobina** (metahemoglobina no sangue, exame compartilhado pelas 3 regras). Biomarcadores conferidos linha a linha no texto oficial do Anexo I Quadro 1 (Portaria 567/2022, gov.br/MTE). Anilina tem indicador "OU" (metahemoglobina *ou* p-aminofenol urina) → canônico = metahemoglobina, alinhando o cluster num exame só e coerente com a Matriz Patrícia; `[INTERPRETADO — escolha do canônico, revisão de saída]`. Cromo: um exame (mesmo analito, dois critérios de amostragem — FJFS 25 vs aumento-na-jornada 10, não dois exames). EE do Quadro 1 passa de 12/41 a **21/41**; total de regras R-BIO-04 = **24**. Mesma ID — família materializa R-BIO-04, sem regra nova. `[DERIVADO — NR-07 Anexo I Quadro 1, Portaria 567/2022, texto oficial MTE; Matriz Patrícia 06/2025]`

> **Changelog 003.DL (mesma ID — Quadro 1/EE lote 2, fecha o Quadro).** A família `R-BIO-04-<agente>` ganhou os 22 agentes restantes do Quadro 1 (IBE/EE), todos `[per]` 6M / um exame cada: 1,1,1-tricloroetano (ác. tricloroacético, canônico entre 4 opções, exame reusado de tricloroetileno), 1,3-butadieno, HDI, 2-metoxietanol + acetato de 2-metoxietila (par que converge no mesmo metabólito urinário), 2-propanol (acetona urina, exame reusado da acetona), TDI (agente-classe, 2 CAS no Anexo), 2-butoxietanol, chumbo tetraetila (chumbo urina — nota anti-confusão bilateral com R-BIO-04-chumbo, Quadro 2/SC, gravada nas duas `base_normativa`), ciclohexanona e clorobenzeno (canônico entre 2 opções cada), etoxietanol + etoxietilacetato (par convergente; CAS do etoxietanol ausente no Anexo, `null` explícito), furfural, metil-butil-cetona (2,5-hexanodiona, exame reusado do n-hexano), MIBK, N-metil-2-pirrolidona, N,N-dimetilacetamida, N,N-dimetilformamida (canônico entre 2 opções), óxido de etileno (adutos HEV), tetracloroetileno (canônico entre 2 opções) e tetrahidrofurano. Biomarcadores e opções descartadas conferidos linha a linha no texto oficial do Anexo I Quadro 1 (Portaria 567/2022, gov.br/MTE). **Quadro 1/EE fecha em 41/41; total de regras R-BIO-04 = 46.** `is_carcinogeno_iarc`/`tem_lt` gravados `null` explícito nos 22 (não verificados nesta sessão data-only — ver DT-003DL-01, varredura própria contra IARC Monographs + NR-15 Anexo 11). Mesma ID — família materializa R-BIO-04, sem regra nova. `[DERIVADO — NR-07 Anexo I Quadro 1, Portaria 567/2022, texto oficial MTE]`

#### R-BIO-05 — Risco irrelevante no PGR dispensa o indicador IBE/EE: menção documental no lugar do exame `[INTERPRETADO — prioridade na revisão de saída]`

Agente do **Quadro 1 (IBE/EE)** cujo risco o PGR classifica como **IRRELEVANTE** na avaliação qualitativa P×S da própria linha → o indicador biológico de R-BIO-04 **não é emitido**; a matriz leva, na linha do cargo, a observação *"risco irrelevante no PGR para <agente> — incluir menção no PCMSO; não solicitado: <exame>"*, uma por agente. **Risco BAIXO emite o indicador normalmente.**

- **Condição de dispensa:** todo risco do agente no GHE traz nível IRRELEVANTE. Basta uma linha do mesmo agente em BAIXO ou acima, ou sem nível (PGR sem avaliação P×S, rota LLM/card, risco implícito, componente de FDS), para o indicador sair. Silêncio do PGR nunca vira dispensa.
- **Escopo:** só Quadro 1 (IBE/EE, 42 regras `R-BIO-04-*`). O Quadro 2 (IBE/SC — chumbo, cádmio, fluoretos, inseticidas inibidores da colinesterase) segue emitindo em qualquer nível: ali o indicador tem significado clínico (7.5.19.5), e nenhum caso medido o dispensa. Fora também `R-BIO-03` (manganês, via NR-15) e `R-PKG-BZ` (benzeno, carcinógeno).

**Origem.** `DT-003EB-02`. A decisão de 23/09/2026 ("segue o da Dra. Carolini", dispensa em risco baixo) foi implementada e medida contra os 3 gabaritos pareados antes de entrar: superemissão 7→0 (Fascino SPE 0030, Dra. Carolini, 08/07/26) e 1→0 (Porto Araras I), mas **subemissão 0→6 (Porto Araras I, Dra. Patrícia, 06/07/26) e 9→13 (Vila Brasil Escritório, Dra. Patrícia, 26/08/26)** — a Dra. Patrícia pede o indicador com risco BAIXO em 10/10 células medidas (acetona, tolueno, xileno, MEK, ciclohexanona; encanador, meio oficial hidráulico, pintor, instalador de manutenção). O nível IRRELEVANTE é o único em que as duas médicas concordam: Porto Araras I, pintor, 2-butoxietanol anotado "irrelevante", gabarito sem BAA. **Decisão do Diovanni (24/09/2026), sobre essa medição: dispensa só em IRRELEVANTE.**

**Conduta da Dra. Carolini não reproduzida, declarada (D-ARQ-81 cl.1).** A anotação do gabarito Fascino — *"Encanador (Incluir no word do PCMSO, risco baixo no PGR para acetona e metiletilcetona)"*, *"Pintor (Incluir no word do PCMSO, risco baixo no PGR para destilados-petróleo, tolueno, metiletilcetona e xileno)"* — fica fora desta regra: nessas 7 células o motor emite o indicador e ela não. Entre as duas condutas, a regra fica com a que emite, que é a mais protetiva; as duas são compatíveis com o 7.5.12 "b" (ver abaixo). Viés: construção civil, 2 médicas, 3 PGRs pareados, n=1 caso de IRRELEVANTE.

**Relação com a norma `[CONFERIDO — D-ARQ-69, 24/09/2026]`.** Conferida no PDF `nr-07-atualizada-2022-1_4.pdf` fornecido pelo Diovanni em 24/09/2026 (39 p., sha256 `f27b63bb…938b63`; cabeçalho lista alterações até a Portaria MTP n.º 567, de 10/03/2022 — conferência contra o texto, não contra a listagem da página, per nota 003.FA de D-ARQ-69). O literal que decide é o **7.5.12**: os exames complementares laboratoriais da NR *"são obrigatórios quando: a) o levantamento preliminar do PGR indicar a necessidade de medidas de prevenção imediatas; b) houver exposições ocupacionais acima dos níveis de ação determinados na NR-09 ou se a classificação de riscos do PGR indicar"*; e o **7.5.1**: *"O PCMSO deve ser elaborado considerando os riscos ocupacionais identificados e classificados pelo PGR"*. A norma, portanto, **condiciona** a obrigação do indicador à classificação do PGR — dispensar quando o PGR classifica o risco como irrelevante (e não há medição acima do nível de ação) é compatível com o texto, não abaixo dele. O 7.5.15 só exime o Quadro 1 dos momentos adm/RT/MR/dem; a periodicidade semestral vem do 7.5.13. A nota do Quadro 1 confirma a natureza do indicador: IBE/EE *"não têm caráter diagnóstico ou significado clínico"*, indicam *"a possibilidade de exposição acima dos limites de exposição ocupacional"*.

*Por que segue `[INTERPRETADO]`, não `[DERIVADO]`.* A norma não diz **qual** nível da classificação "indica" o exame. Fixar o corte em IRRELEVANTE (e não em BAIXO) é leitura sobre o precedente das duas médicas, não literal. Consequência lateral registrada, não tratada aqui: pelo 7.5.12 "b", R-BIO-04 — que emite pela simples presença do agente — fica **acima** do mínimo normativo quando o PGR classifica o risco como baixo; é conduta mais protetiva, não contrária, e é a conduta da Dra. Patrícia.

**Implementação.** Chave `mencao_documental: {regra: R-BIO-05, niveis_risco: [IRRELEVANTE]}` nas 42 `R-BIO-04-*` do Quadro 1 (`regras.yaml`); desvio em `stage_5_emissao` (`_nivel_dispensa`, `motor/estagios/emissao.py`); `Observacao` em `MatrizGHE.observacoes` (`motor/tipos.py`); célula de observação em `documento_matriz.py` e linha na apresentação de revisão (`apresentacao_matriz.py`). O carregador recusa a chave em regra cujo `quando` não é slug de agente ou com nível que o parser não produz. Nível vem de `RiscoPGR.nivel_risco` — hoje só a rota determinística (família Consciente) o preenche (DT-003EC-01); nas demais rotas o indicador segue saindo. R-BIO-04 mantém ID e status: a família continua sendo a regra, esta é a exceção por nível.

---

## 6. PACOTES POR CARGO / ATIVIDADE

Pacotes são conjuntos pré-formalizados de exames que disparam em bloco quando o predicado se torna verdadeiro.

### R-PKG-ATIVCRIT — Pacote Atividade Crítica `[VALIDADO]`
**Predicado:** trabalhador exposto a **trabalho em altura, espaço confinado ou operação de máquina pesada** (qualquer um dos três).

**Exames (12M em adm/per/MR):**
- Hemograma
- Glicemia
- Audiometria
- Acuidade visual
- ECG

**Observação arquitetural:** hemograma e glicemia entram aqui como **rastreio de comorbidade** (não como biomonitoramento). A lógica é: comorbidade não detectada contraindica atividade crítica.

> **Nota de implementação (003.ED, mesma ID).** A regra existia em `regras.yaml` desde
> 002.C mas era inalcançável por duas das três pernas de `atividade_critica`. Corrigido:
> (a) `trabalho_altura` ganhou alias Tier 1 `"Trabalho em Altura"` — antes o termo que o PGR
> escreve não resolvia (dist 3 do slug, fora do raio fuzzy). Fonte: NR-35, título e item
> 35.2.1, redação Portaria MTP 4.218/2022, texto vigente conferido `nr-35-atualizada-2025-1.pdf`
> (última alteração Portaria MTE 1.680, de 02/10/2025). `[DERIVADO — NR-35 título e 35.2.1]`
> (b) o primitivo `maquina_pesada` comparava slug inexistente; `atividade_critica` passa a
> referenciar `motorista_equipamento_pesado` (D-ARQ-67).
> **Efeito medido (Fascino, rodada offline determinística, D-ARQ-65):** 16 dos 19 GHEs
> passaram a emitir as 5 linhas da regra; cruzamento NOMINAL contra o gabarito
> `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` (Hemograma/Glicemia/ECG
> em 16/19) deu interseção 16 e conjuntos "só no motor" e "só no gabarito" VAZIOS — mesmos IDs,
> não apenas mesma contagem. As 16 pendências `vocabulario_ausente` de 'Trabalho em Altura'
> desapareceram.
> **Ressalva `[INTERPRETADO — prioridade na revisão de saída]`.** Identificar "operação de
> máquina pesada" (R-PKG-ATIVCRIT) com "motorista de equipamento pesado" (R-AUD-01) é leitura
> do Arquiteto: o protocolo usa os dois rótulos e não declara que denotam o mesmo conceito.
> Nível 4 de D-ARQ-22 — norma não cobre, matriz-precedente não medida, não é analogia. A
> consequência prevista (GHE com esse risco isolado passa a receber o pacote completo) é REAL
> no motor e **NÃO exercitada por nenhum caso do acervo**: medição isolada dos três primitivos
> por GHE no Fascino deu `trabalho_altura` 16, `motorista_equipamento_pesado` **0**,
> `espaco_confinado` **0**, sobreposição 0 (soma fecha 16). Inspecionar na primeira matriz
> gerada para PGR que declare o risco.
> Conteúdo clínico inalterado; nenhuma R-* criada ou alterada.

### R-PKG-SOLD — Pacote Soldador `[VALIDADO]`
**Predicado:** cargo "soldador" presente, ou exposição a fumos metálicos declarada.

**Exames:**
- RX tórax 60M (adm/per/MR/dem)
- Espirometria 24M (adm/per/MR/dem)
- Carboxihemoglobina semestral (per)
- Manganês sanguíneo semestral (adm/per/MR) — assumindo Mn no eletrodo (ver R-FDS-05)
- Acuidade visual adm/per/MR/dem (caso único com demissional — ver R-VIS-01)
- **TODO operacional:** solicitar FDS do eletrodo para confirmar/adicionar metais (R-OP-01)

### R-PKG-BZ — Pacote Benzeno `[VALIDADO]`
**Predicado:** benzeno identificado na composição (via FDS, mesmo em concentração < 5%, mesmo via CAS de hidrocarbonetos aromáticos genéricos).

**Exames:**
- Hemograma semestral (adm/per/MR/dem)
- Reticulócitos (adm/per/MR/dem)
- Ácido trans-trans-mucônico semestral (per)

### R-PKG-ARMADOR — Pacote Armador com Policorte `[VALIDADO]`
**Predicado:** armador (construção civil) com exposição a policorte.

**Exames:**
- RX tórax 60M (adm/per/MR/dem)
- Espirometria 24M (adm/per/MR/dem)
- Carboxihemoglobina semestral (per)

### R-PKG-TRANSITO — Pacote Trânsito (deslocamento/condução em via pública) `[INTERPRETADO — prioridade na revisão de saída]`
**Predicado:** o PGR declara o risco de acidente **"Bater contra ou ser atingido por (trânsito)"** (slug `transito_via_publica`, só a frase completa — "trânsito" sozinho aparece no acervo como circulação a pé e não entra).

**Exames (12M em adm/per/MR):**
- Acuidade visual
- Audiometria

**Origem.** `DT-003EB-01` classe (4). Decisão do Diovanni (24/09/2026), sobre medição: nos 3 PGRs pareados da família Consciente, **3/3 GHEs** que declaram o risco recebem os dois exames no gabarito — Vila Brasil Escritório (Dra. Patrícia, 26/08/26): DIREÇÃO ("conduz carro de pequeno porte") e PATRIMÔNIO ("dirige veículos leves"); Fascino SPE 0030 (Dra. Carolini, 08/07/26): VENDAS. Nenhum dos outros 58 GHEs recebe o par por esse motivo. A alternativa "ver na descrição do cargo" foi medida e descartada: acertava só a DIREÇÃO, e palavras como "dirigem"/"conduzir" davam falso positivo em FINANCEIRO, ADMINISTRAÇÃO, SUPERVISÃO e VENDAS.

**Por que ID nova, não R-VIS-01/R-AUD-01.** R-VIS-01 lista "motorista" como atividade crítica e R-AUD-01 tem a perna `motorista_equipamento_pesado`, ambas `[VALIDADO]`. Aqui o gatilho é o **risco declarado**, não o cargo, e o veículo é leve — escopo diferente, ID nova (regra de versionamento do projeto).

**Sem âncora normativa.** Nível 4 de D-ARQ-22. Viés declarado (D-ARQ-81 cl.1): construção civil, 2 médicas, n=3 GHEs. Não amplia universo definido por norma — nenhuma NR delimita acuidade/audiometria para condução de veículo leve.

**Fora de escopo, aberto.** VIGILÂNCIA (acuidade) e PLANEJAMENTO (acuidade + audiometria) de Vila Brasil não têm risco de trânsito nem direção no bloco — seguem classe (4). Rota LLM (ex.: PGRs Seconci, mesma grafia no texto) depende de o transcritor emitir a frase completa `[A MEDIR]`.

### R-PKG-PORT — Pacote Porteiro `[VALIDADO]`
**Predicado:** cargo "porteiro".

**Exames:**
- Acuidade visual adm/per/MR (ver R-VIS-02)

---

## 7. MATRIZ TEMPORAL E REAPROVEITAMENTO

### R-TEMP-01 — Momentos do exame médico ocupacional `[VALIDADO]`
- **Admissional** (adm)
- **Periódico** (per)
- **Mudança de Risco Ocupacional** (MRO ou MR) — *substitui "mudança de função"*
- **Retorno ao Trabalho** (RT)
- **Demissional** (dem)

### R-MRO-01 — Mudança de Risco Ocupacional `[VALIDADO]`
"Mudança de função" **não existe mais** como categoria. O conceito atual é **Mudança de Risco Ocupacional (MRO)**. Na MRO, aplica-se a matriz do **novo cargo**.

### R-REAPR-01 — Reaproveitamento de químicos `[VALIDADO]`
Exames de biomonitoramento químico têm **validade de 6 meses**. Repete-se apenas se o último exame foi realizado há ≥ 6 meses.

### R-REAPR-02 — Audiometria no demissional `[VALIDADO]`
Audiometria com mais de **120 dias** → refazer no demissional. Ver R-AUD-03.

---

## 8. REGIMES REGULATÓRIOS ESPECIALIZADOS

### R-REG-ANAC — Aviadores `[VALIDADO]`
Tripulação aeronáutica → aplicar **normativa ANAC**, que demanda exames adicionais à NR-07. A NR-07 não é o regime aplicável principal.

**Confirmação v2:** a Dra. Carolini confirmou que **ANAC é o único regime regulatório setorial** que ela aplica sobrescrevendo a NR-07. Categorias como ferroviário, marítimo, eletricistas de alta tensão, profissionais de saúde e mineração seguem **NR-07 padrão** no protocolo dela.

**Decisão arquitetural relacionada:** D-ARQ-04 (ver `DECISOES_ARQUITETURAIS.md`).

---

## 9. LEMBRETES OPERACIONAIS (TODOs da matriz)

### R-OP-01 — FDS do eletrodo `[VALIDADO]`
Em toda matriz com soldador, registrar item operacional:
> *"Verificar metais liberados pelo eletrodo usado pela empresa — solicitar FDS específica."*

Esse item **não é exame** — é um TODO para quem executa o PCMSO confirmar metais antes de fechar a matriz.

**Decisão arquitetural relacionada:** D-ARQ-05.

---

## 10. METODOLOGIA — COMO ENSINAR A UMA MÉDICA NOVA

Síntese narrativa fornecida pela Dra. Carolini em resposta a 10.1:

1. Verificar **validade** do PGR (< 2 anos)
2. Verificar **assinatura** por engenheiro de segurança do trabalho
3. Ler o **inventário** — riscos, agravos e EPIs indicados
4. **Padronizar** conforme NR-07 e NR-15 (para Mn)
5. Para químicos: Anexo I → periódico semestral; Anexo II → semestral em adm/per/MR/RT/dem
6. Para atividades críticas (altura, espaço confinado, máq. pesada): aplicar R-PKG-ATIVCRIT
7. Para soldador: aplicar R-PKG-SOLD
8. Para porteiro: aplicar R-PKG-PORT
9. Para exposição a poeiras: aplicar R-RX-01
10. Exames clínicos sempre anuais como base (ver R-CLI-01)
11. Exceções regulatórias (ex: aviadores → ANAC) sobrescrevem a NR-07

---

## 11. PENDÊNCIAS CLÍNICAS EM ABERTO

Movidas para `docs/PENDENCIAS_CLINICAS.md` em 003.ET (fatia 0, D-ARQ-63). Este documento
não carrega mais o corpo das dívidas; a seção permanece como âncora de numeração.

---

## 12. PONTOS VALIDADOS NA SEGUNDA RODADA (17/05/2026)

Todas as 6 lacunas levantadas na v1 foram resolvidas pela Dra. Carolini:

| ID | Tema | Resposta | Regra atualizada |
|----|------|----------|------------------|
| A-VAL-01 | Risco do PGR não convincente | Segue inventário sem reinterpretar | R-GHE-04 → VALIDADO |
| A-VAL-02 | Classes de FDS desconfiadas | Não existem além de FDS genérica | R-FDS-06 → VALIDADO |
| A-VAL-03 | Espirometria por máscara — clínica ou normativa? | **Normativa** — NR-07, item espirometria | R-ESP-01, R-PGR-03 → base normativa |
| A-VAL-04 | Revisão da matriz Viverde | Matriz correta, sem alterações | Bloco 9 fechado |
| A-VAL-05 | Outros regimes regulatórios | Só aviação (ANAC) | R-REG-ANAC, D-ARQ-04 → simplificada |
| A-VAL-06 | RX sílica ≥ 10% LT | 12 meses, conforme NR-07 | R-RX-01 → VALIDADO |

**Nenhuma lacuna remanescente** no protocolo a partir desta versão.

---

## Histórico de revisões

| Versão | Data | Alterações |
|--------|------|------------|
| v1 | 17/05/2026 | Versão inicial — consolidação dos 47 áudios da Dra. Carolini |
| v2 | 17/05/2026 | Segunda rodada — 6 lacunas (A-VAL-01 a A-VAL-06) fechadas; R-GHE-04 e R-FDS-06 promovidas a VALIDADO; R-RX-01 saiu de INFERIDO para VALIDADO; bases normativas confirmadas em R-ESP-01, R-PGR-03 e R-RX-01; matriz Viverde validada como correta; ANAC confirmada como único regime regulatório sobreposto |
| v3 | 19/05/2026 | Sessão 002.D3: seção 11 "Pendências clínicas em aberto" adicionada com DT-D3-02 (granularidade de fumos_metalicos a refinar com Dra. Carolini) |
| v4 | 23/05/2026 | Sessão 002.I: DT-002I-01 adicionada (limiar de genericidade de R-PGR-05) |
| v5 | 24/05/2026 | Sessão 002.K: DT-002K-01 (gatilho de RX 24M ausente em R-RX-01) e DT-002K-02 (serralheiro e pacote de fumos metálicos) adicionadas — ambas para sessão CONHECIMENTO, originadas da auditoria da RQ.61 contra o protocolo |
| v6 | 25/05/2026 | Sessão 002.L-estudo: DT-002K-01 e DT-002K-02 RESOLVIDAS. R-GHE-02 refinada (indissociável vs. contingente); R-GHE-05 nova (risco contingente → confirmação documental); R-RX-01 refinada com tabela do Anexo III (4 faixas %LEO + estado sem-medição = gatilho do 24M; PNOS 60M). |
| v7 | 25/05/2026 | Sessão 002.L0: R-RX-01 implementada como família R-RX-01-* (D-ARQ-20); R-RX-02 virou regra executável; estado contraditório de quantificação → pendência bloqueante. |
| v8 | 25/05/2026 | Sessão 002.L: DT-002L-01 adicionada (conversão mg/m³ → %LEO para rotear faixa de RX — pergunta de método para a Carolini, originada da estruturação do PGR Viverde) |
| v9 | 28/05/2026 | Sessão 002.M: fonte primária congelada; validação migra para revisão de saída (erro-zero + PDCA, D-ARQ-22). Convenções de status revisadas. Nota de implementação em R-GHE-05 (depende de D-ARQ-23). DT-D3-02/002I-01/002L-01 reclassificadas. Divergência serralheiro Est-09 documentada. |
| v10 | 29/05/2026 | Sessão 002.N: R-RX-01 sílica/asbesto sai de a-conferir → [DERIVADO] (NR-7 Anexo III Quadro 1, 567/2022; bordas ≤, CLSC, NOTA 2); DT-002L-01 RESOLVIDA (LEO sourcing NR-9/NR-15/NR-22); D-ARQ-24 (LEO-resolver); DT-002N-01 aberta (PNOS achata Quadro 2); R-RX-01-pnos e R-RX-02 rebaixados VALIDADO→INTERPRETADO. |
| v11 | 29/05/2026 | Sessão 002.O (META): DT-002N-02 resolvida. Convenção `[DERIVADO]` alinhada a D-ARQ-22 Parte A — fonte vai no marcador (`[DERIVADO — NR-x item y]` etc.), não só no corpo. R-RX-01 "Valores conferidos" passa a `[DERIVADO — NR-7 Anexo III Quadro 1]`. Sem reclassificação de regra. |
| v12 | 01/06/2026 | Sessão 002.V (CONHECIMENTO/ARQUITETURA): DT-002V-01 adicionada — `Quantificacao.valor` não discrimina se o número é o CLSC; premissa "motor consome CLSC, não calcula" a validar com Carolini. Sem reclassificação de regra. |
| v13 | 02/06/2026 | Sessão 002.W: DT-002L-01 e DT-002N-02 resolvidas (marca de pendência removida do título, Status RESOLVIDA no corpo); higiene de conformidade da dívida 002.V. |
| v14 | 03/06/2026 | Sessão 002.X (CONHECIMENTO): DT-002N-01 RESOLVIDA (PNOS Quadro 2: 4 faixas + LEO ACGIH 3 mg/m³ resp; faixa 10–100% = evento único + critério clínico, não 60M); R-RX-01-pnos DEPRECATED → família R-RX-01-pnos-* (ID clínico R-RX-01 inalterado); asbesto LEO 2,0 f/cm³ (f/cm³, fixo, NR-15 Anexo 12); DT-002X-01 (LEO carvão), DT-002X-02 (pós-ocupacional asbesto 30a), DT-002X-03 (NOTA 1) adicionadas. Nada implementado — especificação para sessão de código. |
| v15 | 04/06/2026 | Sessão 002.Y (IMPLEMENTAÇÃO): família R-RX-01-pnos-* materializada em código (predicados de faixa + ramo PNOS no resolver + 4 regras INTERPRETADO + R-RX-01-pnos DEPRECATED); D-ARQ-29 (injeção fração RESPIRAVEL); DT-002Y-01 (lembrete 10–100% não materializado, depende de D-ARQ-28) e DT-002Y-02 (validação Viverde real adiada p/ integração) adicionadas. Suíte 315→327. PR #49, commit 9bb243e. |
| v16 | 05/06/2026 | Sessão 003.A (CONHECIMENTO→ARQUITETURA): DT-002Z-01 catalogada na seção 11 e RESOLVIDA — orquestrador all-or-nothing por GHE resolvido por fonte documental (NR-07 7.5.5/7.6.4), virou D-ARQ-31 (bloqueio por-risco/por-linha, MatrizGHE tri-estado, pendência anexada à linha). Sem reclassificação nem regra clínica nova. |
| v17 | 07/06/2026 | Sessão 003.F (CONHECIMENTO): frente FDS aberta. DT-FDS-01 adicionada — R-BIO-02 [VALIDADO] contradito pelo Anexo I vigente (eixo Quadro 1/IBE-EE vs Quadro 2/IBE-SC, não "Anexo I/II"; conferido no texto oficial MTE, 567/2022). Reabertura adiada para sessão própria (exige Quadro 2 inteiro). R-CLI-02/03 sob suspeita do mesmo rótulo. Nenhuma regra alterada nesta sessão. |
| v18 | 08/06/2026 | Sessão 003.G: nota de procedência em R-FDS-03/04 (cutoff 5% = [VALIDADO] conduta Carolini sem âncora NR; carcinógeno-independe = [INTERPRETADO] INCA/Anexo V; ligação com D-ARQ-33 caminho C). Mesma ID, semântica intacta. Nenhuma regra criada/alterada. |
| v19 | 09/06/2026 | Sessão 003.H (ARQUITETURA): DT-FDS-02 adicionada — unidade do cutoff de 5% (% m/m a confirmar em ABNT NBR 14725); borda 5,0 de D-ARQ-34 fica [INTERPRETADO] até confirmar. Lado-engenheiro, independente de DT-FDS-01. Nenhuma regra criada/alterada. |\r\n| v20 | 13/06/2026 | Sessão 003.L: DT-003L-01 adicionada (mapa de 6 formas de declaração químico no PGR — input empírico para D-ARQ-25; varredura read-only de 15 PGRs). Achados laterais (HISTORICO): tracking misto em matrizes_originais/; "Graxa ET" possível composição inline (veredito-Viverde sob suspeita). Caça do caso-âncora — sem código, sem regra clínica alterada. |
| v21 | 13/06/2026 | Sessão 003.M: DT-003M-01 (ramo-0-vs-bypass com CAS oculto — decisão de arquitetura), DT-003M-02 (vocabulário não cobre composição-de-FDS; medição 23/24 ramo 0) e DH-003M-01 (`\r\n` literal reincidente no HISTORICO) adicionadas. Fatia 3 de D-ARQ-34 (fixture-FDS real) — sem regra clínica criada/alterada. |
| v22 | 13/06/2026 | Sessão 003.N: nota de andamento em DT-003M-02 (frente b-mínimo — 2 solventes de FDS populados em agentes.yaml: acetona, acetato_de_etila; DT segue ABERTA). Sem regra clínica alterada. |
| v23 | 14/06/2026 | Sessão 003.P (IMPLEMENTAÇÃO): DH-003P-01 adicionada (imports de `Materialidade` apontam p/ módulo re-exportador, não `tipos` canônico — higiene de código). Nenhuma regra clínica criada/alterada (`regras.yaml` intocado; fatia 1 de D-ARQ-35 é contrato de risco, não conduta). |
| v24 | 16/06/2026 | Sessão 003.T: DT-003T-01 adicionada (`is_sensibilizante` ausente do `agentes.yaml`; gate-CAS popula só `is_carcinogeno_iarc`; introduzi-la é sessão de dado própria, cruza DT-003M-01). Fatia 2 de D-ARQ-36 Parte 3 — sem regra clínica criada/alterada (gate materializa D-ARQ, não R-*). |
| v25 | 20/06/2026 | Sessão 003.AA (CONHECIMENTO): DT-FDS-01 RESOLVIDA. R-BIO-04 nova (eixo Quadro 1/IBE-EE só-periódico [7.5.15 literal] vs Quadro 2/IBE-SC cinco-momentos [a contrario]; carcinógeno = Anexo V, não desloca momento; caso-âncora tolueno/solventes — superdimensionamento); R-BIO-02 DEPRECATED. R-CLI-02/03 relabel "Anexo I/II" → "Quadro 1/2 do Anexo I" (mesma ID; semestral = conduta Carolini, não 7.5.8; borda Anexo-V [INTERPRETADO]). Quadro 2 lido inteiro (MTE). Sem código. |
| v26 | 21/06/2026 | Sessão 003.AB (ARQUITETURA-leve): DT-003AB-01 adicionada (seção 11) — campo `anexo_nr07` mapeado como eixo morto (consumo-zero verificado por git) e misturado (NR-07 "I" / NR-15 "11"), insumo herdado pela implementação de R-BIO-04 (substituição → `tipo_ibe`, D-ARQ-33). Sem regra clínica criada/alterada; sem código. |
| v27 | 21/06/2026 | Sessão 003.AD (CONHECIMENTO): R-BIO-04 changelog 003.AD (mapa agente→biomarcador + confirmação Quadro 1/2 contra texto oficial; mesma ID); DT-003AB-01 nota de derivação (tabela tipo_ibe por slug que a fatia b transcreve; benzeno=EE corrige fixture+comentário stale; chumbo=SC; 9 CAS null; cobertura SC parcial). DT-003AB-01 segue ABERTA. Sem regra criada/alterada; sem código. |
| v28 | 22/06/2026 | Sessão 003.AE (IMPLEMENTAÇÃO): DT-003AB-01 RESOLVIDA (migração `anexo_nr07 → tipo_ibe` materializada — enum `TipoIBE`, valor por slug, fixture/comentário corrigidos, 419→420). DT-003AE-01 adicionada (resíduos de dado: 9 CAS null dos EE + cobertura SC parcial do Quadro 2 — sessão de dado própria). Sem regra clínica criada/alterada. |
| v29 | 26/06/2026 | Sessão 003.AN (CONHECIMENTO/medição): DT-003AN-01 adicionada (seção 11) — granularidade do "Derivados de:" multi-CAS na transcrição de FDS (explode em N `Componente` vs. agrega; cruza D-ARQ-35), input para a IMPL do transcritor-FDS, originada da medição dos 6 PDFs de `fds_originais/`. Sem regra clínica criada/alterada. Sem código. |
| v30 | 26/06/2026 | Sessão 003.AO (META/higiene): DH-003AO-01 adicionada e RESOLVIDA (seção 11) — `.gitattributes` `*.md text eol=lf` blinda terminador de markdown na origem (independe de `core.autocrlf`); distinta de DH-003M-01 (`\r\n` literal-conteúdo, segue ABERTA). Doc-only, sem código, sem regra clínica. |
| v31 | 27/06/2026 | Sessão 003.AQ (ARQUITETURA): DT-003AN-01 RESOLVIDA por D-ARQ-45 (seção 11) — fork explode-vs-agrega resolvido a favor de explode (bloco multi-CAS explode em N `Componente` no resolvedor, herança-α da faixa inteira); nota da distinção empilhado-vs-linhas-soltas herdada pela IMPL do transcritor-FDS. Nenhuma R-* tocada (P1 não cria/altera conduta). Sem código. |
| v32 | 29/06/2026 | Sessão 003.AS (IMPLEMENTAÇÃO): DT-003AS-01 adicionada (seção 11) — patologias de layout/transcrição da tabela de composição de FDS, expostas pela medição `extract_tables` dos 6 PDFs ao construir a camada parse-PDF (`extrair_tabelas_fds`, D-ARQ-42 Parte 1): composição-não-isolável (Ciplan/Tigre, grid fundido), coluna-deslocada (Tigre), `\n`-intra-token (TiO₂), grafias-de-ausente, separador de faixa `-`/`–`, coluna-de-perigo-europeia (descartada por recorte A). Seção da composição "2", não 3 — a confirmar contra NBR 14725 vigente. Input para a fatia de transcrição-FDS. Nenhuma R-* criada/alterada (fatia é parse-PDF, não conduta). |
| v33 | 29/06/2026 | Sessão 003.AU (IMPLEMENTAÇÃO): nota de andamento em DT-003AS-01 — patologias 3/4/5 materializadas (`transcricao_fds.py`, funções puras); P3 refinada; patologias 1/2 seguem abertas. DT ABERTA. Sem regra clínica alterada. |
| v34 | 30/06/2026 | Sessão 003.AW (IMPLEMENTAÇÃO): DT-003AW-01 adicionada (seção 11) — grafia-de-ausente quebrada por `\n` de render (`"Segredo\nIndustrial"`) escapa a `desambiguar_cas`+`normalizar_cas_ausente` (junta sem espaço → não casa `_GRAFIAS_CAS_AUSENTE`); ambas as ordens P3/P4 falham igual, logo não é eixo de ordem; não-medida (D-ARQ-22), não-bloqueante. Exposta pela passada adversária da montagem `verbatim → Componente` (D-ARQ-46, 003.AW). Nenhuma R-* criada/alterada. |
| v35 | 30/06/2026 | Sessão 003.AX (ARQUITETURA): andamento em DT-003AS-01 (patologias 1/2 decididas como camada-LLM + entrada `extract_text`, não bbox; IMPL futura) + DT-003AX-01 adicionada (seção 11) — a virada tabelas→texto reabre o mecanismo de explosão multi-CAS do D-ARQ-45 (`\n`-célula, não a decisão) e o papel do `extrair_tabelas_fds` da 003.AS; reconciliação texto-puro vs híbrido é passada dedicada. Decisão registrada como nota 003.AX em D-ARQ-42 (DECISOES v71). Nenhuma R-* criada/alterada. Sem código. |
| v36 | 30/06/2026 | Sessão 003.AY (CONHECIMENTO/medição → ARQUITETURA): DT-003AX-01 RESOLVIDA (reconciliação) — entrada do transcritor-FDS TEXTO-PURO (`extract_text`, não híbrido; híbrido = paliativo); explosão multi-CAS migra de `\n`-split (003.AR) p/ expansão-de-grupo no resolvedor (decisão D-ARQ-45 preservada, só o mecanismo muda, cardinalidade fora do LLM); `extrair_tabelas_fds` (003.AS) deixa de ser entrada → candidato DEPRECATED/cross-check. Andamento em DT-003AS-01 (entrada texto-puro cravada). Detalhe em DECISOES (nota 003.AY em D-ARQ-42 + D-ARQ-45, v72). Aberto p/ IMPL: forma do verbatim-grupo + destino de `_explodir_multi_cas`/`extrair_tabelas_fds`. Nenhuma R-* criada/alterada. Sem código. |
| v37 | 01/07/2026 | Sessão 003.AZ (IMPLEMENTAÇÃO — fatia i): andamento em DT-003AS-01 — montagem-de-grupo materializada. Forma FECHADA: `BlocoVerbatim` aninhado (`ComponenteVerbatim` aposentado; singleton = bloco de 1). Destinos ratificados p/ fatia ii: `_explodir_multi_cas` aposentar, `extrair_tabelas_fds` DEPRECATED. Detalhe em DECISOES (nota 003.AZ em D-ARQ-46 + D-ARQ-45, v73). Suíte 488→489; mypy delta-zero. Commit `9a4eaf3`. Nenhuma R-* criada/alterada. |
| v38 | 02/07/2026 | Sessão 003.BD (CONHECIMENTO/medição → ARQUITETURA): andamento em DT-003AS-01 — patologia 1 (grid fundido Ciplan/Tigre) MEDIDA e DESBLOQUEADA. Transcrição por sentido sobre `extract_text` âncora-por-título contra `fds_t65`: Tigre 7/7, Ciplan 8/8 (cas + concentração). Fusão = interleave de coluna (não perda de dado); ordem de coluna inverte por fabricante → roteia por formato-de-token, confirma anti-bbox (003.AX). Reenquadra o limite de D-ARQ-46. Contrato de invocação+gate do transcritor-LLM em D-ARQ-47 (DECISOES v78). DT segue ABERTA (IMPL do transcritor-LLM + `extrair_texto_fds` greenfield); DT-003M-01 intocada (recorte A). Sem código. |
| v39 | 02/07/2026 | Sessão 003.BE (IMPLEMENTAÇÃO): andamento em DT-003AS-01 — `extrair_texto_fds` materializada (D-ARQ-47 consequência, recorte âncora-por-título com sobre-inclusão). DT segue ABERTA. Nenhuma R-* criada/alterada. |
| v40 | 02/07/2026 | Sessão 003.BF (IMPLEMENTAÇÃO): andamento em DT-003AS-01 — invocação injetável (`TranscritorLLM` Protocol + `transcrever_fds`) + `gate_forma` (cl.3) + harness mockado tinta/Ciplan sobre `extrair_texto_fds` real. DT segue ABERTA. Nenhuma R-* criada/alterada. |
| v41 | 05/07/2026 | Sessão 003.BI (IMPLEMENTAÇÃO fatia (e2)): DT-003AS-01 FECHADA (seção 11) — revisão-RT (cl.4) + serialização verbatim ida/volta materializadas (`motor/revisao_verbatim.py`, D-ARQ-47); cadeia extração→LLM→gate→revisão-RT→montagem→resolvedor completa (003.AX/AU/BD/BE/BF/BG/BH/BI). Residuais que NÃO reabrem a DT: DT-003M-01, DT-003BG-01 (gabarito 3/6), DT-003AW-01, UI da revisão-RT. Nenhuma R-* criada/alterada. |
| v42 | 08/07/2026 | Sessão 003.BV (CONHECIMENTO/medição): DT-003BV-01 adicionada (seção 11) — formato de validade no topo do PGR (mês-ano, multi-candidata, sem `dd/mm/aaaa`; insight confirmação-RT de D-ARQ-53 P2 validado com caso concreto Viverde FEV/2025 vs FEV/2023). Medição do topo Viverde via `recortar_topo` (D-ARQ-53 P4): 33 págs texto nativo, OCR não recorre; responsável por âncora-título (R-PGR-01 satisfeito, evidência Título+CREA; assinatura-imagem não text-derivable); gabarito `EnvelopeVerbatim` semeado p/ a fatia 2. Correção de rótulo: medição do topo NÃO é DT-003L-01 (mapa químico); topo nunca medido, sessão própria. Nenhuma R-* criada/alterada. Sem código. |
| v43 | 09/07/2026 | Sessão 003.CB (CONHECIMENTO): **R-RUIDO-01 nova** (seção 5.2) — classificação de exposição a ruído contínuo/intermitente `dB(A)→relacao_LT` sobre o NEN: <80 `abaixo_acao`, 80–85 `entre_acao_LT`, ≥85 `acima_LT`. Limiares `[DERIVADO]`: 85 dB(A) = LT NR-15 Anexo 1 (teto 115), 80 dB(A) = nível de ação NR-09 c/c NLI da NHO-01 (item literal NR-09 `[INCERTO]`). Ressalvas `[INTERPRETADO]`: valor=NEN não SPL/pico (DT-003CB-01); q=5 vs q=3 é cálculo, não limiar (motor consome NEN); ruído de impacto fora de escopo. Destrava a fatia 3 de D-ARQ-51 (`relacao_LT` sempre `None` até 003.BZ); consumidor `_ruido_acima_acao` inalterado. DT-003CB-01 adicionada (NEN vs SPL, irmã de DT-002V-01). Normas conferidas via web (D-ARQ-27). Sem código. |
| v44 | 09/07/2026 | Sessão 003.CC (IMPLEMENTAÇÃO): nota de implementação em R-RUIDO-01 (classificador em código, PR #179). Nenhuma regra criada/alterada. |
| v45 | 10/07/2026 | Sessão 003.CH (CONHECIMENTO/ARQUITETURA): reframe de DT-003M-02 — andamento 003.N corrigido (hidratação CAS→slug→flags FOI construída em 003.S/V/W/BI; não "inexistente"). Achado `[VERIFICADO — git grep]`: flags de perigo do `Componente` NÃO populadas em produção (transcritor não classifica perigo, recorte B excluído de D-ARQ-42) → "sem flag" = "não extraímos", não "FDS sem perigo". Logo "sem slug → bloqueia" é o estado conservador-CORRETO; (B) NÃO é resolvível isolada — pré-requisito duro = perigo-transcrição (recorte B). Cluster DT-003M-01 + DT-003M-02(B) + DT-003T-01 unificado sob "extrair perigo → reordenar ramo-0". Sequência ratificada pelo Diovanni: perigo-transcrição primeiro; digitação de vocabulário/lista-de-inertes = paliativo. Nota 003.CH em D-ARQ-42. Nenhuma R-* criada/alterada. Sem código. |

| v46 | 10/07/2026 | Sessão 003.CI (ARQUITETURA): **nota de aplicação em R-FDS-06** (seção 4) — recorte (B) da transcrição-FDS dá a R-FDS-06 consumidor executável (frase-H confiada por default, transcrita verbatim `Componente.frases_h`, admitida pelo RT, mapa {H334,H317}→`is_sensibilizante`; gate de FORMA). Semântica de R-FDS-06 intacta, ID preservada. **DT-003T-01 FECHA** (sensibilização vem da FDS, não do vocabulário); notas 003.CI em DT-003M-01 e DT-003M-02 (pré-condição escrita, fecham no passo 2). **DT-003CI-01 adicionada** (seção 11) — carcinógeno-via-frase-H (H350/H351 GHS≠IARC) deferido, futura `is_carcinogeno_ghs`. Decisão de arquitetura em D-ARQ-55 (DECISOES). Nenhuma R-* criada/alterada. Sem código. |
| v47 | 10/07/2026 | Sessão 003.CJ (IMPLEMENTAÇÃO): nota de aplicação de R-FDS-06 **implementada** — `mapear_frases_h` em `resolvedor.py` (PR #190): mapa {H334,H317}→`is_sensibilizante`, gate de FORMA `H\d{3}`, pendência não-bloqueante em token malformado; teste-por-regra `test_mapa_frases_h.py`. Nenhuma R-* criada/alterada; semântica e ID de R-FDS-06 intactas. Detalhe em DECISOES v108 e HISTORICO 003.CJ. |
| v48 | 10/07/2026 | Sessão 003.CK (ARQUITETURA→IMPLEMENTAÇÃO): **DT-003M-01 FECHADA** e **DT-003M-02(B) FECHADA** por D-ARQ-56 (passo 2 do cluster: bypass antes do slug-check em `materialidade()`; Fase C tripartida no sem-slug — `bypass_sem_slug` bloqueante / inerte-declarado não-bloqueante via R-FDS-06 / não-mapeado bloqueante D-ARQ-35). **2ª nota de aplicação em R-FDS-06** (inerte-declarado materializado, `regra_origem="R-FDS-06"` em `riscos.py`). **DT-003CK-01 adicionada** (promoção-sem-slug, condicionada a regra clínica de sensibilizante genérico). Nenhuma R-* criada/alterada. PR #192, suite 740→744. Detalhe em DECISOES v109 e HISTORICO 003.CK. |
| v49 | 11/07/2026 | Sessão 003.CM (CONHECIMENTO/medição): **DT-003CM-01 adicionada** (seção 11) — mapa de cabeçalhos de bloco GHE multi-PGR (medição dos 15 PGRs do acervo, prevista na NOTA 003.BM): âncora `SETOR/FUNÇÃO` cobre 1/15; 5 formas de cabeçalho; caso-Vistamérica (1 âncora → bloco único de ~137 págs., lixo silencioso, classe D-ARQ-22); Viverde conflaciona inventário por-GHE com quadro por-atividade; família cargo-based 4/15 fora do alcance de âncora-GHE. Input obrigatório da sessão ARQ do req. (b) da 003.BS. Nenhuma R-* criada/alterada. Sem código. |
| v50 | 11/07/2026 | Sessão 003.CN (ARQUITETURA): **nota em DT-003CM-01** — consumida por **D-ARQ-57** (localizador de blocos GHE: repertório determinístico de reconhecedores + gate de segmentação densidade+contagem + família cargo-based reconhecer-sinalizar). DT segue ABERTA (D-ARQ-57 a consome, não a fecha). Detalhe em DECISOES v111 e HISTORICO 003.CN. Nenhuma R-* criada/alterada. Sem código. |
| v51 | 11/07/2026 | Sessão 003.CO (IMPLEMENTAÇÃO): **nota em DT-003CM-01** — forma 1 refinada (Viverde também traz `"GHE NN-"`, traço colado, medido no PDF real na IMPL da fatia 1; reconhecedor tolera espaçamento variável no traço). Fatia 1 de D-ARQ-57 implementada (PR #198). DT segue ABERTA (fatias 2–3). Nenhuma R-* criada/alterada. |
| v52 | 11/07/2026 | Sessão 003.CP (IMPLEMENTAÇÃO): **nota em DT-003CM-01** — calibração X=40/N=10 medida diretamente sobre os 15 PGRs do acervo (legítimos ≤34,8%, ALT T65; implausíveis ≥44,4%, TPB); divergência registrada Seconci REV3/REV4 (pypdf 15/16 vs censo "18×" 003.CM). Fatia 2 de D-ARQ-57 implementada (PR #200). DT segue ABERTA (fatia 3). Nenhuma R-* criada/alterada. |
| v53 | 12/07/2026 | Sessão 003.CQ (IMPLEMENTAÇÃO): **DT-003CM-01 FECHADA** — 1ª leva de D-ARQ-57 completa (3/3); caveat pypdf Hetrin/SD resolvido; refino do censo (sinal cargo-based = grid-header AIHA). Nenhuma R-* criada/alterada. |
| v54 | 13/07/2026 | Sessão 003.CU (IMPLEMENTAÇÃO): **R-BIO-04 materializada** (família `R-BIO-04-<agente>`, 12 regras, D-ARQ-38 fatia d) + changelog de correção do biomarcador do tolueno (`tolueno_urina`→`ortocresol_urina`; NR-7 rev.2020 o-cresol, Matriz Patrícia). Mesma ID (família materializa; sem R- nova). |
| v55 | 13/07/2026 | Sessão 003.CV (IMPLEMENTAÇÃO): **R-BIO-04 Quadro 2/SC completo** — +3 agentes (cádmio, flúor/HF/fluoretos, inseticidas inibidores da colinesterase), `[adm,per,RT,MR,dem]` 6M; Quadro 2 fecha 4/4. Biomarcadores da Matriz Patrícia 06/2025; inseticida→acetilcolinesterase eritrocitária `[INTERPRETADO]` (butirilcolinesterase é a alternativa OU); slug-classe único. Mesma ID (família materializa; sem R- nova). |
| v56 | 17/07/2026 | Sessão 003.DB (CONHECIMENTO/medição): DT-003DB-01 adicionada (§11) — anatomia do bloco-cargo medida em 4 witnesses trackeados; a família cargo-based (D-ARQ-57 peça 3) parte em N:1 grupo-GHE (Ricco-Adm) vs 1:1 card-por-cargo (Cjr; UFGD 105 / HUMAP 140). Achado: ambas reduzem a `GHEPGR` → recorte-por-cargo não é 2ª unidade de bloco, é reconhecedores de recorte + binding-por-posição. Gabarito + caveats + fork (Ricco-Adm N:1 → GHE-recorte estendido vs cargo) para a ARQUITETURA da peça 4. Nenhuma R-* criada/alterada. Sem código. |
| v57 | 17/07/2026 | Sessão 003.DC (ARQUITETURA): nota em DT-003DB-01 (§11) — fork N:1 resolvido **rota (i)**: `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` entra na peça 1 (`_RECONHECEDORES_GHE`); Ricco-Adm ingere como GHE (R-GHE-01 [VALIDADO]); recorte-por-cargo genuíno = só 1:1 (Cjr+EBSERH). DT segue ABERTA (fecha na IMPL peça 4, fatias 4a-4d). Detalhe em DECISOES v126 (andamento 003.DC em D-ARQ-57). Nenhuma R-* criada/alterada. Sem código. |
| v58 | 17/07/2026 | Sessão 003.DD (IMPLEMENTAÇÃO): nota em DT-003DB-01 (§11) — forma documentada `INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN` é a VISUAL; o verbatim extraído por pdfplumber perde o til da 1ª palavra (`INFORMAÇOES`, Õ→O, glifo/fonte, confirmado por codepoint em 003.DD) — o reconhecedor da forma 5 cobre ambas via classe `[OÕ]`. Fatia 4a de D-ARQ-57 mergeada (PR #222). Detalhe em DECISOES v127. Nenhuma R-* criada/alterada. Sem código nesta nota (código já em PR #222). |
| v59 | 19/07/2026 | Sessão 003.DL (IMPLEMENTAÇÃO): **R-BIO-04 Quadro 1/EE lote 2 — Quadro FECHA em 41/41.** Família ganha os 22 agentes restantes (mapa §5.9 +22 linhas + changelog 003.DL). Mesma ID — a família materializa R-BIO-04, sem regra nova. `is_carcinogeno_iarc`/`tem_lt` `null` explícito nos 22 (DT-003DL-01). Canônico das 5 com "ou" por D-ARQ-61. Detalhe em DECISOES v135 e HISTORICO 003.DL. |
| v60 | 21/07/2026 | Sessão 003.DQ (META): reclassificação de endereçamento em DT-002V-01, DT-003BV-01, DT-003CB-01 — "pergunta de método à Carolini" → derivação normativa (D-ARQ-27; Carolini valida saídas prontas, não método). Mesma ID nas 3 (mudança de redação; semântica da pergunta intacta). Nenhuma R-* criada/alterada. Sem código. |
| v61 | 22/07/2026 | Sessão 003.DT (IMPLEMENTAÇÃO/MEDIÇÃO): nota de medição de topo Fascino anexada a DT-003BV-01 (mesma ID, aditiva) — rodada `ida` ao vivo confirma mm/aaaa como formato REAL (antes hipótese) e mede LACUNA nova: `_MES_ANO` não casa extenso com "de" ("15 de junho de 2026"). `proposta=None`, validade delegada ao RT. Credencial RT aprovada no `gate_forma_topo` (1º run LLM ao vivo do topo). Nenhuma R-* criada/alterada. Sem código de motor. |
| v62 | 23/07/2026 | Sessão 003.DU (IMPLEMENTAÇÃO): nota de resolução em DT-003BV-01 — faceta "de" FECHADA (`_MES_ANO` com `(?:de\s+)?`; "JUNHO DE 2026"/"15 DE JUNHO DE 2026" → 1º dia do mês). Mesma ID (aditiva; R-PGR-06 sem mudança de semântica — só cobertura do parser). mm/aaaa (D2) e a pergunta de método seguem abertos. Commit `63edefe`, merge PR #250 `3470111`. Detalhe em DECISOES v144. |
| v63 | 23/07/2026 | Sessão 003.DV (MEDIÇÃO): **DT-003DV-01 adicionada** (§11) — 1ª rodada `rodar` ao vivo (Fascino, 19 GHEs): resolução de sílica com falso negativo ('Sílica livre'/'Quartzo'/'Poeira respirável' ausentes; R-RX-01* acionou em 1/19 GHEs) e falso positivo potencial (fuzzy 'Silício'→'silica'). Correção de header defasado em DT-003CM-01 (FECHADA em 003.CQ; changelog v53 já registrava). Nenhuma R-* criada/alterada. Sem código. |
| v64 | 24/07/2026 | Sessão 003.DW (CONHECIMENTO/dado): DT-003DV-01 **faceta A RESOLVIDA** — `silica.termos` com 6 grafias de sílica cristalina livre (NR-15 Anexo 12 / NR-07 Anexo III Quadro 1); critério Tier 1 estendido a fonte-por-natureza-do-agente. Registro anti-FP dos não-sílica (silicatos/poeira respirável/poeira de madeira → `vocabulario_ausente`). Faceta B (fuzzy `Silício`→`silica`) deferida a 003.DX. Índice 99→105, slugs 79 inalterado. Commit `8363fcb`, PR #253 (`862fd57`). Nenhuma R-* criada/alterada. |
| v65 | 24/07/2026 | Sessão 003.DX (META): **DT-003DX-01 adicionada** (§11) — migrar acreção pós-decisão do DECISOES_ARQUITETURAIS.md para satélites `docs/darq/` (três frentes: acreção geral 39%/177k chars, D-ARQ-57 sozinho 13,2%/59.755 chars, tabela de revisões 16%/87.328 chars). Não-bloqueante — D-ARQ-63 (gate de dois níveis + índice derivado) já resolve o custo de leitura. Nenhuma R-* criada/alterada. Sem código de motor. |
| v66 | 25/07/2026 | Sessão 003.DY (IMPLEMENTAÇÃO): **DT-003DV-01 faceta B RESOLVIDA — DT inteira FECHADA** (§11) — ramo FUZZY opt-in por allowlist de dado (D-ARQ-64, DECISOES v147): `fuzzy_permitido: true` em 18 slugs de cauda; `silica` fora → `Silício`/`Silicio` recusados com pendência `fuzzy_recusado` nomeando termo/slug/distância; veto de resultado, não filtro de candidato. Suíte 945→949 passed, 6 skipped. Nenhuma R-* criada/alterada. |
| v67 | 25/07/2026 | Sessão 003.EB (MEDIÇÃO): **DT-003EB-01 e DT-003EB-02 adicionadas** (§11) — 1ª rodada `rodar-offline` (D-ARQ-65) no Fascino, 19/19 GHEs, zero invocação LLM, + diff contra a matriz humana validada (Marco 1): DT-003EB-01 (pacote-base incondicional de 10 exames em 19/19 GHEs sem conceito no motor, ~190 de ~194 células do diff) e DT-003EB-02 (R-BIO-04 emite indicador biológico onde a matriz humana pede só menção documental em risco baixo, GHE-10/16). Higiene: header da DT-003DV-01 corrigido para `[FECHADA — facetas A (003.DW) e B (003.DY)]`, coerente com o corpo. Nenhuma R-* criada/alterada. Sem código de motor. |
| v68 | 26/07/2026 | Sessão 003.EC (IMPLEMENTAÇÃO): **R-CLI-01 materializada** — nota de implementação (mesma ID, §5.1): primitivo incondicional `todo_trabalhador` (D-ARQ-66), slug `exame_clinico` novo em `exames.yaml`, 12M em `[adm, per, MR, RT, dem]`. **DT-003EB-01 REENQUADRADA** (não fechada) — premissa "pacote-base ~190/~194 células" REFUTADA por medição direta do gabarito Fascino: medido 4 exames em 19/19 (não ~190), GHE-06 Administração recebe 4/GHE-19 Vendas recebe 5 (oposto de "pacote incondicional universal"); gap decomposto em 4 classes (regras órfãs / lacuna de vocabulário / divergência de periodicidade / conceito ausente), 003.EC fecha a maior fatia da classe (1); resíduo ABERTO = classe (4) (`Av. Médica de Saúde Mental` + Avaliação Psicossocial incondicional vs R-PSY-01 condicionada), gatilho de formalização = 2º PGR no acervo (D-ARQ-06), não n=1; ressalva sobre anotações de rascunho no corpo do gabarito (D-ARQ-18); correção factual 003.EB (RX 60m também em GHE-08, não só GHE-09). **DT-003EC-01 CRIADA (ABERTA, não-bloqueante)** — RX Tórax OIT 12M no gabarito onde R-RX-01 sem-medição prescreve 24M, pergunta de método (D-ARQ-27); resolve de passagem o pré-registro de DT-003DV-01/003.DW ('Poeira respirável' tratada como sílica-like, não PNOS). Suíte 963→967 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Commit `f175e76`. |
| v69 | 26/07/2026 | Sessão 003.EC (META): re-tiragem do `PAINEL_ESTADO.md` pós-merge do PR #263 (main `e3cba55`) — regras 20/42 pelo instrumento (48%) / 19/42 pela intenção do painel (R-TEMP-01 é citação, não regra executável), vocabulário/CAS 50/79 (63%, substitui a medição manual 003.AI de 21/45, obsoleta desde 003.EC), suíte 967 passed/6 skipped (1366s). **DH-003EC-01 e DH-003EC-02 adicionadas** (§11) — higiene do instrumento `scripts/medir_painel.py` (cegueira a suíte vermelha, ID citado em prosa contando como implementado, `INDICE_DARQ.md` sem vigilância de divergência) e higiene de suíte (79% do tempo é reparse de PDF real em setup por-teste, candidato a fixture `scope="session"`). Nenhuma regra clínica criada ou alterada. |
| v70 | 26/07/2026 | Sessão 003.ED (IMPLEMENTAÇÃO): nota de implementação em R-PKG-ATIVCRIT (mesma ID, §6) — alias Tier 1 `"Trabalho em Altura"` (NR-35 título + item 35.2.1, Portaria MTP 4.218/2022) e substituição do primitivo órfão `maquina_pesada` por `motorista_equipamento_pesado` (D-ARQ-67) em `atividade_critica`; efeito medido no Fascino: 16/19 GHEs passam a emitir R-PKG-ATIVCRIT, cruzamento nominal contra o gabarito com interseção 16 e conjuntos "só motor"/"só gabarito" vazios. Ressalva `[INTERPRETADO]` registrada — os dois rótulos ("máquina pesada" vs "motorista de equipamento pesado") não são declarados como o mesmo conceito pelo protocolo; consequência não exercitada por nenhum caso do acervo (0 GHEs via `motorista_equipamento_pesado`, 0 via `espaco_confinado`). **DT-003ED-01 CRIADA (ABERTA)** (§11) — grafia natural com preposição não resolve contra slug sem preposição (atinge R-VIB-01/02 e a perna de máquina pesada). **DH-003ED-01 CRIADA (ABERTA)** (§11) — relatório do harness não carrega slugs resolvidos nem o átomo do predicado composto disparador. **DT-003DV-01: observação de instrumento REFUTADA por medição** — o relatório TEM identidade por GHE. **DT-003EB-01: nota adicionada** — classe (2) perdeu a maior fatia; achado novo `[A MEDIR]` sobre GHE-19 (Vendas, `ctx.riscos == []`). Suíte 967→968 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Commit `7b2e65d`. Nenhuma R-* criada/alterada; conteúdo clínico inalterado. |
| v71 | 26/07/2026 | Sessão 003.EE (IMPLEMENTAÇÃO): **DT-003EE-01 CRIADA** (`ConflitoProtocolo` sem disparador após D-ARQ-39; decisão MANTER). Nota de aplicação 003.EE em R-GHE-03 — dedup compõe periodicidade por piso, mesma ID, sem mudança de semântica clínica. Nenhuma R-* criada ou alterada. Detalhe em DECISOES v153 e HISTORICO 003.EE. |
| v72 | 26/07/2026 | Sessão 003.EF (IMPLEMENTAÇÃO): **DH-003EC-01 PARCIALMENTE RESOLVIDA** (§11) — facetas (a) cegueira a falha e (c) derivado sem vigilância FECHADAS (`medir_suite()` lê `returncode` e levanta em suíte vermelha; `INDICE_DARQ.md` regenerado e seu estado exposto como 4ª linha do painel); faceta (b) ID citado conta como implementado segue ABERTA. Nenhuma R-* nem D-ARQ criada/alterada. Sem código de motor. Detalhe em HISTORICO 003.EF. |
| v73 | 27/07/2026 | Sessão 003.EG (IMPLEMENTAÇÃO): **DH-003ED-01 PARCIALMENTE RESOLVIDA** (§11) — facetas `riscos_resolvidos` (slugs por GHE) e `predicado` (expressão real, fim do literal `"<composto>"`) FECHADAS; faceta `risco_origem` segue ABERTA (exigiria mudar a assinatura de `predicados.avaliar`, recorte deixado fora por decisão do Arquiteto). **DT-003EG-01 CRIADA (ABERTA)** — audiometria emitida em 16/19 GHEs com motivo `R-PKG-ATIVCRIT` em 15 deles onde o gatilho clínico real é ruído bloqueado por `predicado_ausente` (exame certo, razão errada), só visível porque o motivo por linha passou a ser impresso. **DH-003EG-01 CRIADA (ABERTA — higiene de instrumento)** — 122 bytes NUL do verbatim do PGR vazam para `motivo` de pendências `vocabulario_ausente` no relatório, `grep` classifica-o como binário; `\r\n` recorrente (classe DH-003M-01). **DH-003EG-02 CRIADA (ABERTA — higiene de método)** — `relatorios/` inteiro fora do git (`.gitignore:42` — a linha citada na v73 era `:26`, âncora errada, corrigida na v92), o diff motor×gabarito que pauta a fila desde D-ARQ-62 envelheceu 4 sessões sem sinal em `git log` (mesma classe de DT-003DX-02). Medição Fascino (`5a2d15b`): 19 GHEs → 2 VÁLIDA / 15 PARCIAL / 2 BLOQUEADA, 104 linhas de exame (baseline 003.EB: 14 BLOQUEADA / 3 PARCIAL / 2 VÁLIDA, 7 linhas — divergência esperada, motor mudou em 4 sessões desde então). Suíte 977→982 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Commits `94a5720`, `76f1afa`, `5a2d15b`. Nenhuma R-* criada/alterada. Detalhe em DECISOES v155 e HISTORICO 003.EG. |
| v74 | 27/07/2026 | Sessão 003.EG (EMENDA — correção de método): **DH-003EG-03 CRIADA (ABERTA)** (§11) — vigilância do `INDICE_DARQ` (003.EF) existe mas o ritual não a invoca em sessão docs-only; o commit `186150e` desta mesma sessão ficou defasado 94 linhas por a suíte ter sido dispensada por instrução ("docs-only"), corrigido em `973a343`; 2ª ocorrência da classe em 2 sessões (1ª: `c89f569`, 003.EF). Causa nomeada no Arquiteto, não no Code. Correção instalada: `CLAUDE.md` na raiz (NOVO) — regras de método versionadas e lidas pelo Code, endereça DT-003DX-02 — e `docs/RITUAL_FECHAMENTO.md` (NOVO) — checklist fixo de 7 passos que substitui redação livre do prompt de fechamento. Resíduo ABERTO: ambas dependem de leitura humana/agente, sem mecanismo que impeça 3ª ocorrência; hook de pre-commit é candidato, com ressalva de que `core.hooksPath` não é versionado. Suíte inalterada nesta emenda (nenhum código tocado). Detalhe em DECISOES v156 e HISTORICO 003.EG. |
| v75 | 28/07/2026 | Sessão 003.EH (FECHAMENTO — docs): nota de aplicação em R-RX-01 (mesma ID — ausência de laudo é ramo do Quadro 1, não pendência; ponte `[INTERPRETADO]`; efeito medido 14/19, 70→0, 104→118, 2/16/1); nota de procedência LSC vs. CLSC. **DT-003EH-01 CRIADA (ABERTA)** e **DH-003EH-01 CRIADA (ABERTA)** (§11). Nota aditiva em DT-003EC-01 (divergência 24M×12M medida em 14 GHEs). **D-ARQ-68 CRIADA** em DECISOES v157. Nenhuma R-* criada ou alterada. Detalhe em HISTORICO 003.EH. |
| v76 | 28/07/2026 | Sessão 003.EI (CONHECIMENTO — docs): **R-ESP-02 CRIADA** `[DERIVADO — NR-07 Anexo III item 3.1, Portaria MTP 567/2022]` — espirometria 24M (adm/per/MR/dem) por exposição a poeira mineral (sílica/asbesto/PNOS) do inventário do PGR, sem depender de quantificação; momentos MR/dem `[DERIVADO — matrizes Carolini 07/2026 e Patrícia 04/2025]`. **R-ESP-01 → DEPRECATED** (sucedida por R-ESP-02; default e exceção-EPI sem âncora no Anexo III vigente, itens 3.2/3.3 condicionam a sinal/sintoma). Call-site de R-PGR-03 (§2) reapontado para R-ESP-02. **DT-003EI-01 CRIADA (ABERTA)** (§11) — R-PKG-SOLD/R-PKG-ARMADOR prescrevem espirometria incondicional sob agentes do item 3.2 (condicionado a sintoma), não materializadas em `regras.yaml`. Detalhe em HISTORICO 003.EI. |
| v77 | 28/07/2026 | Sessão 003.EI (EMENDA do Arquiteto — docs): nota de alcançabilidade em produção em R-ESP-02 (mesma ID) — `asbesto`/`poeira_nao_classificada` sem chave `termos:` em `agentes.yaml`, primitivos verdes na suíte porém inalcançáveis em produção, classe D-ARQ-67/D-ARQ-68; `silica` alcança e cobre. Nota de assimetria RX×espirometria em R-ESP-02, citando D-ARQ-31 (bloqueio bloqueante do RX não se propaga à espirometria, intencional). **DH-003EI-01 CRIADA (ABERTA)** (§11) — campo `status` de `regras.yaml` sem enum validado (`DERIVADO` é o 4º valor, só `DEPRECATED` é distinguido pelo carregador) e divergente da convenção do PROTOCOLO (regras `[DERIVADO]` gravadas como `VALIDADO`; campo não alcança `ExameEmitido`/`Motivo`, D-ARQ-22 Parte B segue descumprida neste eixo). Medido (não alterado): `protocolos_especiais` em `agentes.yaml` segue sem consumidor em runtime (`motor/`, `adaptadores/`, `superficie/`, `scripts/` — zero grep), confirma PAINEL_ESTADO/D-ARQ v140; não tocado. Nenhuma R-* criada/alterada. Detalhe em HISTORICO 003.EI. |
| v78 | 28-29/07/2026 | Sessão 003.EI (FECHAMENTO — docs): correção de 4 achados da passada de verificação do Arquiteto. **DH-003EI-02 CRIADA (ABERTA)** (§11) — taxonomia de `categoria` de exame diverge entre D-ARQ-12/validador/dado (achado que a redação da DH-003EI-01 original perdeu ao ser reescrita para o eixo `status`; restaurado em DH própria). Nota de R-RX-01 reescrita (periodicidade da espirometria independe da faixa do RX, mesmo compartilhando o gatilho poeira mineral — coincidência de valor em 24M, não dependência). Nota aditiva em DT-002K-01 (veredito tinta/RX de 002.L-estudo desatualizado sob R-ESP-02, preservado como registro histórico). Docstring de `_pnos` corrigida (`predicados.py`) — único consumidor em runtime é R-ESP-02, R-RX-01-pnos é DEPRECATED. Nenhuma R-* criada/alterada. Detalhe em HISTORICO 003.EI. |
| v79 | 30/07/2026 | Sessão 003.EJ (IMPLEMENTAÇÃO + MEDIÇÃO): nota de aplicação em R-PGR-05 (mesma ID) — fração declarada sem agente (`Poeira respirável`, `Poeiras Respiráveis/Metálicas`) não permite rotear Quadro 1/2 do Anexo III, D-ARQ-68 não se aplica; medido no Fascino, 14 GHEs, 13 já com sílica. Nota de aplicação em R-VIB-02 (mesma ID) — aliases de D-ARQ-70 destravam a perna mão-braço; efeito medido: 9→0 pendências, GHE-12 ganha audiometria nova, 8 GHEs somam R-VIB-02 como motivo, 132→133 linhas. **DT-003ED-01 PARCIALMENTE RESOLVIDA** (§11) — faceta vibração RESOLVIDA (NR-09 Anexo I 1.1/2.1, VMB/VCI); faceta máquina pesada segue ABERTA. Correção (não-apagamento) em DT-003EC-01 — GHE-08/GHE-09 não são lacuna de vocabulário (Poeira de madeira fora dos Quadros; Poeiras Respiráveis/Metálicas é R-PGR-05). **DT-003EJ-01 CRIADA (ABERTA)** — poeira de madeira agente identificável fora dos dois quadros. **DT-003EJ-02 CRIADA `[A DECIDIR]`** — GHE-16 do Fascino vai PARCIAL→VÁLIDA quando a perna Ausente de R-AUD-02 é absorvida por um `ou` verdadeiro; tri-estado de D-ARQ-31 computa sobre pendências/linhas, não sobre predicados avaliados. Detalhe em HISTORICO 003.EJ. |
| v80 | 30/07/2026 | Sessão 003.EJ (EMENDA — verificação de aceite pré-push do Arquiteto): **DH-003EJ-01 CRIADA (§11)** — instrumento do harness (`scripts/medicao_pgr.py`) tem duas facetas do mesmo eixo (pendência não atribuída/anexada no relatório): (a) `ghe_id` não impresso, RESOLVIDA (003.EJ, commit `afb8889`); (b) `ExameEmitido.pendencias_anexadas` não impressas na tabela de exames, ABERTA — foi o que exigiu rerun in-process para diagnosticar GHE-16 (DT-003EJ-02). Corrige rótulo impreciso do commit `afb8889` (citava DH-003ED-01, eixo distinto) sem alterar DH-003ED-01. Nenhum código tocado, só docs. |
| v81 | 31/07/2026 | Sessão 003.EK (FECHAMENTO — docs): **DT-003EJ-02 RESOLVIDA** (§11) por D-ARQ-71 — correção sem apagar "a informação já está disponível no ponto da avaliação": vale só para a perna avaliada antes do primeiro `True` do `ou`, registro do erro preservado (D-ARQ-06). **DH-003EJ-01 RESOLVIDA** (§11) — faceta (b) fechada pela 8ª coluna do relatório (commit `823d467`). Nota aditiva em DT-003EG-01 (§11) — segue ABERTA, mas o eixo ganhou instrumento (coluna nova + pendência de perna absorvida tornam a causa visível). Nenhuma R-* criada ou alterada. |
| v82 | 31/07/2026 | Sessão 003.EM (FECHAMENTO — docs): **DH-003EI-01 PARCIALMENTE RESOLVIDA** (§11) — faceta 2 (campo `status` não alcançava `ExameEmitido`/`Motivo`) RESOLVIDA por D-ARQ-72 (`Motivo.status_regra` populado de `regra.get("status")`, renderizado por exame); faceta 1 (enum não validado) segue ABERTA, medido 65 regras (`VALIDADO` 58 / `INTERPRETADO` 5 / `DERIVADO` 1 / `DEPRECATED` 1). **DH-003EM-01 CRIADA** (§11, achado da revisão do Arquiteto) — `_STATUS_INSPECIONAR_PRIMEIRO` em `superficie/apresentacao_matriz.py:13` é literal de vocabulário digitado em código sem teste computado do dado (classe D-ARQ-67), ABERTA. **DH-003EM-02 CRIADA** (§11) — bloco "inspecionar primeiro" nunca exercitado no nível `INTERPRETADO` no Fascino (0 ocorrências em 19 GHEs, apesar de 5 regras `INTERPRETADO` existirem), ABERTA, não é defeito. **D-ARQ-72 CRIADA** (DECISOES v161, 72 decisões) — apresentação-de-saída da matriz extraída para `superficie/apresentacao_matriz.py`, apresentação-pura herdando D-ARQ-54 P1; status de validação da regra atravessa até `Motivo`. Nenhuma R-* criada ou alterada. Detalhe em HISTORICO 003.EM. |
| v83 | 01/08/2026 | Sessão 003.EN (CONHECIMENTO → IMPLEMENTAÇÃO → MEDIÇÃO): **R-PSY-02 CRIADA** (§5.7) — Avaliação Psicossocial + Av. Médica de Saúde Mental, incondicional via `todo_trabalhador` (D-ARQ-66), 12M em `[adm, per, MR]`; base normativa NR-01 1.5.3.1.4/1.5.3.2.1/1.5.4.4.5.3 (Portaria MTE 1.419/2024, vigência 26/05/2026 pela Portaria MTE 765/2025) — a norma obriga inventariar/gerenciar o FRPRT, não prescreve exame; conduta `[DERIVADO]` do corpus (6 matrizes pós-vigência, 5 clientes, 2 médicas, 284 cargos, 99% de cobertura, contra ~0% em 13 matrizes pré-vigência). **R-PSY-01 marcada `[DEPRECATED — sucedida por R-PSY-02]`**, corpo preservado. **DT-003EB-01 classe (4) FECHADA** — gatilho "2º PGR atualizado no acervo" satisfeito e medido; classes (2) e (3) seguem ABERTAS. Slugs `avaliacao_psicossocial`/`avaliacao_saude_mental` novos em `exames.yaml`. Nova instância de DH-003EC-01(b) registrada (§11) — citação "R-PSY-01 (DEPRECATED)" na `base_normativa` de R-PSY-02 não infla o painel, verificado por script. Medição Fascino (`rodar-offline`, `relatorios/003en_fascino_rodar.md`, gitignored): linhas de exame 133→171 (+2×19 GHEs), status 3 VÁLIDA/15 PARCIAL/1 BLOQUEADA inalterado, GHE-06/GHE-19 passam a receber os 2 exames sem mudar de status, pendências 154 inalterado, bloco "inspecionar primeiro" não-vazio 14/19→19/19 GHEs, status por motivo VALIDADO 130 inalterado/DERIVADO 14→52. Painel: regras 21/42→22/42 pelo instrumento (20/42→21/42 pela intenção). Suíte 1025→1027 passed, 6 skipped; `mypy --strict agente_medico/motor agente_medico/tests/invariantes.py` delta-zero. Detalhe em HISTORICO 003.EN. |
| v84 | 01/08/2026 | Sessão 003.EO + EMENDAs 1-4 (IMPLEMENTAÇÃO + MEDIÇÃO): emissor de saída no formato do escritório — `agente_medico/superficie/documento_matriz.py` (D-ARQ-73, DECISOES v162), `MatrizGHE.nome_ghe`/`cargos` aditivos, `ordem_exibicao` cravado em `exames.yaml` (decisão do Arquiteto após a fatia 0 medir que a ordem de exame não é constante entre GHEs — bloqueador nomeado, resolvido na EMENDA 1). Medição contra o Fascino real confirma exatamente a tabela corrigida da EMENDA 1 (12/19 GHEs idênticos; 4 células de superemissão GHE-10/16; 10 de subemissão GHE-06/08/09/17/19). **DT-003EO-01 CRIADA** (cabeçalho/rodapé sem casa no modelo). **DT-003EO-02 CRIADA** (grafia Glicemia/RX indecisa, D-ARQ-06, yaml intocado). **DT-003EO-03 CRIADA** (clínico semestral do pacote Mn sem alcance, confirma raiz de DT-003EI-01; **R-BIO-03 `[VALIDADO]` verificado como não-materializável** — manganês sem slug em `exames.yaml`, `grep` em `regras.yaml` = zero em qualquer forma). **DT-003EO-04 CRIADA e refinada em duas facetas** (EMENDA 3: `GHEPGR.cargos` do parser da família Consciente, `parser_familia_consciente.py`/D-ARQ-65 fatia 1 — (a) concatenação, cosmética; (b) perda por quebra de linha física na tabela, silenciosa, medida em **2/19 GHEs e 6/41 cargos** nomeados — GHE-03 4/8, GHE-06 2/5, 2º caso não citado na medição original de 003.DZ, docstring corrigido). **Decisão do Arquiteto (EMENDA 4): fecha em `003.EP`**, não nesta sessão — recuperar linha física reverte escopo declarado de 003.DZ (exige D-ARQ própria); separador não é decidível sem desenho (delimitador vírgula/ponto-e-vírgula inconsistente + CBO colado ao nome com NUL); paliativo via `Pendencia` avaliado e rejeitado (detecção é o problema em aberto, não a pendência). `docs/PLANO_V1.md` migrado da pasta do Cowork e corrigido contra premissa refutada pela própria sessão (linha 44: "motor emite 6/GHE em 16, gabarito 4" — `[A MEDIR]` desde 003.EG — REFUTADO, o eixo estava descrito ao contrário; medido 4 células de superemissão em 2 GHEs, 10 de subemissão). S2 **parcialmente entregue** — emissores HTML/DOCX prontos e testados; expansão GHE→cargo correta para o dado que recebe, sem efeito em produção até DT-003EO-04 fechar. Suíte 1027→1039 passed, 6 skipped (+12 testes); `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, 42 arquivos (não comparável ao baseline 34 — o comando desta sessão passou a incluir `superficie/` pela primeira vez, não é crescimento de escopo anterior). Nenhuma R-* criada, alterada ou depreciada. Detalhe em HISTORICO 003.EO. |
| v85 | 03/08/2026 | Sessão 003.EP fatias 0-4 (MEDIÇÃO + IMPLEMENTAÇÃO + FECHAMENTO): **DT-003EO-04 FECHADA** (§11), ambas as facetas — célula "Cargo / Função" passa a render um nome por cargo (CBO descartado, precedente 003.DG-1), e os 6 cargos perdidos por quebra de linha física (GHE-03 4; GHE-06 2) chegam a `GHEPGR`; evidência: gate nominal 0 divergências contra os 41 nomes de `003eo_emenda3_cargos_perdidos.md`, e2e real (`test_pipeline_real_fascino_ate_documento_41_linhas_cargo`) com 41 `LinhaCargo` em `montar_documento`. Correção de premissa preservada (D-ARQ-06): a EMENDA 4 atribuía a indecisão a delimitador+CBO-colado como dois problemas; medido na fatia 0 que são o mesmo glifo-hífen (`\x00`≡`-`) já catalogado em `_PADRAO_TITULO_ANCORA`/`'HIDRO\x00SANITÁRIAS'`, e os dois grupos de dígitos são 1 código CBO-2002 só. **DT-003EP-01 CRIADA** (§11) — R-GHE-02 inalcançável em produção: `cargos_vocab.get(cargo)` (`riscos.py:61`) é lookup exato contra slugs minúsculos, sem resolver; pendências R-GHE-02 19→41 medido; `soldador` (único cargo com `riscos_implicitos` não-vazio) só não dispara por acidente de caixa. Não é conserto desta fatia — muda conduta clínica. **DT-003EP-02 CRIADA** (§11) — dois caminhos de silêncio remanescentes no parser (entrada sem CBO vira cargo fantasma, medido 36 na reversão da fatia 1 com split ativo; rótulo sem valor na própria linha devolve zero cargos): nenhum alcançável no Fascino, não é "impossível" na família. **DH-003EP-01 CRIADA** (§11) — `_sanitizar` apaga (não converte) o glifo-hífen `\x00` no documento assinado, confirmado (`HIDRO\x00SANITÁRIAS`→`HIDROSANITÁRIAS`); mapeamento correto incerto. **Nota aditiva em DH-003EG-01** — segue ABERTA, mas bytes NUL no relatório do harness 122→18 (fatia 2 removeu 85% como colateral; resíduo de outra origem, não investigado). **D-ARQ-65 cláusula 5 NOVA** (DECISOES v163) — bloco da família é formulário de 2 colunas fixas, não só tabela de riscos; `x0` idênticos bit-a-bit nos 19/19 blocos, continuações com desvio 0,0pt exato; critério de fim de célula é transição de banda, nunca o literal do próximo campo. Medição de não-regressão (`relatorios/003ep_fascino_rodar.md` vs. `003eo_fascino_rodar.md`): linhas de exame 171→171 e status por GHE idênticos nos 19 — único movimento é a pendência não-bloqueante R-GHE-02 (DT-003EP-01). `docs/PLANO_V1.md`: **S2 fecha** (ressalva preservada — cabeçalho/rodapé seguem seam humano por desenho, DT-003EO-01, resolvido no S3, não lacuna do S2); próximo da fila S3 (app), S0 (hospedagem) ainda não decidido, risco de prazo. Suíte 1039→**1048 passed, 6 skipped**; `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, 42 arquivos. Nenhuma R-* criada, alterada ou depreciada — painel 22/42 não se move. Commits `aaa9eca`/`486d54d`/`7f19cf4` (código+testes) + fatia 4 (docs). Detalhe em HISTORICO 003.EP. |
| v86 | 04/08/2026 | Sessão 003.EQ (S3 fatia 1 + emendas 1-3, FECHAMENTO — docs): app de matriz da rota determinística entregue (`superficie/web_matriz.py`), validado no host real do Diovanni contra o Fascino (19 GHEs, 41 cargos) e no caso de rejeição por R-PGR-01. **D-ARQ-74 CRIADA** (DECISOES v164) — superfície que emite artefato assinável lê `resultado.status` e nunca emite documento sem conteúdo clínico; caso-âncora medido em dois ambientes (sandbox e host): `Resultado(status="REJEITADO", matrizes=[])` passava reto pelo guard `doc is None` (`matrizes=()` não é `None`), produzindo `matriz.html` de 187 bytes e `matriz.docx` com zero `<w:tbl>` — documento assinável sem uma linha de exame. **DH-003EQ-01 CRIADA** (§11) — preservação-em-download da casca sem cobertura automatizada, `AppTest` do Streamlit instalado não expõe `download_button`; contornado por teste de unidade sobre a decisão de reuso + passada manual (confirmada 04/08/2026). **DT-003EQ-01 CRIADA** (§11) — lixo de recorte/transcrição vazando como termo de agente, faceta de DT-003L-01. **DT-003EQ-02 CRIADA** (§11) — `Maganês`→`manganes` recusado pelo fuzzy (D-ARQ-64 funcionando como desenhado), custo clínico real medido, candidato a alias sob D-ARQ-70. **DT-003EQ-03 CRIADA** (§11) — status `PRELIMINAR` não é marcado no documento assinado, irmã de DT-003EO-01; fronteira explícita com D-ARQ-74 cl.1 (que cobre só `REJEITADO`). Nota aditiva em DH-003EP-01 (glifo-hífen confirmado na saída real, GHE-10) e em DT-003EO-04 (fechamento confirmado em produção real, 41 cargos/19 GHEs, 6 cargos antes perdidos presentes). Registro de caminho não-ocorrente: cargo com zero células, não medido no Fascino (todo cargo recebe os 3 incondicionais). Violação de método autodeclarada: uma rodada de suíte foi medida concorrente com mutação de arquivo durante varredura inversa — rodadas limpas posteriores confirmaram ausência de defeito real. Suíte 1048→**1062 passed, 6 skipped** (+14); `mypy --strict agente_medico/motor agente_medico/superficie agente_medico/tests/invariantes.py` limpo, 43 arquivos. Nenhuma R-* criada, alterada ou depreciada. Commits `1eb32af`/`380fe59`/`5a0d02e`/`4b0a541`. Detalhe em HISTORICO 003.EQ. |
| v87 | 08/08/2026 | Sessão 003.ES (IMPLEMENTAÇÃO, fatias 1-2): abre **DH-003ES-01** (§11) — ramos `NEGAR` e `LIBERAR` do gate de acesso sem cobertura de casca; os três desfechos têm teste de unidade, mas só `PEDIR_LOGIN` é exercitado pelo `AppTest`. Não-bloqueante e alcançável (a sonda 2 de 003.ES mediu que `monkeypatch` sobre `streamlit.user` chega ao script). **Nenhuma regra clínica criada, alterada ou depreciada** — decisão de arquitetura da sessão está em D-ARQ-76. Detalhe em HISTORICO 003.ES. |
| v88 | 10/08/2026 | Sessão 003.ET fatia 0 (partição realizada 08/08/2026, linha de changelog registrada agora, 10/08/2026 — a fatia 0 fez a partição sem gravar linha de changelog, e esta v88 corrige o resíduo, omissão do prompt do Arquiteto, não do Code, D-ARQ-06): §11 (dívidas técnicas `DT-`/`DH-`) movido inteiro para `docs/PENDENCIAS_CLINICAS.md`; documento cai de **274.752 para 113.007 caracteres**; numeração duplicada `## 11.` corrigida para `## 12.`; consumidores de método atualizados (skill `/kickoff` item 5, `RITUAL_FECHAMENTO` passo 2, `CLAUDE.md` da raiz). **Nenhuma regra clínica tocada** — a versão sobe por mudança estrutural do documento, não de conteúdo. Detalhe em HISTORICO 003.ET. |
| v89 | 15/08/2026 | Sessão 003.EX fatias 0-1 (MEDIÇÃO + IMPLEMENTAÇÃO): **R-AUD-04 CRIADA** (§5.2) — audiometria como piso universal, 12M `[adm, per, MR, dem]`, incondicional via `todo_trabalhador` (D-ARQ-66); base normativa NR-07 Anexo II 4.1 `[DERIVADO]` crava 12M+adm+dem, universo estendido a todo trabalhador e MRO incluído são `[INTERPRETADO]`, apoiados em matriz-precedente (fatia 0: SPE 0030 41/41 audiometria, 38/41 DEM confirmado; RESERVA 0028 44/44, 42/42 confirmado + 2 indeterminados). `R-AUD-01`/`R-AUD-02` **não tocadas** — piso por baixo, molde `R-CLI-01`×`R-CLI-02`; dedup concatena motivos, não substitui. **`R-AUD-03` ganha marcador de fonte** `[DERIVADO — NR-07 Anexo II item 4.1.1]` (mesma ID, changelog). **DT-003EW-01 FECHADA** (`PENDENCIAS_CLINICAS.md`) — reenquadrada como resolução de saída, não da raiz (`ruido_acima_acao = Ausente` continua intacta). **DT-003EG-01 segue ABERTA**, nota aditiva — não agravada nem fechada (motivos concatenam). **DH-003EX-01 CRIADA (ABERTA)** — heurística de forma no extrator do gabarito (`medir_audiometria_dem.py`) assume no máximo 2 grupos após "Audiometria", não testada contra 3. Efeito medido no Fascino (`rodar-offline`, mesmo PDF/envelope de sessões anteriores): GHEs com audiometria **17/19 → 19/19** (medição fresca desta sessão — diverge do "16/19" herdado de `DT-003EG-01`; causa nomeável, não baseline cega: a diferença é GHE-12/Betoneira, que passou a emitir audiometria em 003.EJ por `R-VIB-02` — aliases de D-ARQ-70 destravaram a perna mão-braço; 16+1=17, divergência explicada); GHE-06 (Administração) e GHE-19 (Vendas) ganham a linha nova nesta sessão (as duas únicas sem audiometria antes de `R-AUD-04`); linhas de exame **171 → 173** (+2, exatamente GHE-06/GHE-19); linhas de audiometria com `DEM` **1/17 → 19/19**; status **3 VÁLIDA / 15 PARCIAL / 1 BLOQUEADA inalterado, confirmado GHE a GHE** (não só no agregado) — bate exatamente com a previsão D-ARQ-66 cl.2. 4 testes novos com reversão nomeada, varredura inversa 4/4 confirmada (`test_orquestrador.py`). 4 quebras legítimas de teste de integração corrigidas com explicação nomeada (não silenciadas): `test_rvib02_vmb_sozinho_emite_audiometria` (pré-dedup, duas entradas "audiometria" agora, busca deixa de usar `next()` sozinho), `test_execucao_dedup_audiometria_tres_motivos_sem_conflito` (3→4 motivos), `test_execucao_ototoxico_via_agente_status_ok_sem_r_aud_02` (renomeado — "sem demissional" deixou de ser observável via ausência de `DEM`; invariante real que o nome agora descreve — R-AUD-02 não dispara por ototóxico isolado — checado direto), `test_pipeline_gates_emissao_consolidacao_atividade_critica` (audiometria sai do loop genérico de momentos, ganha checagem própria). Suíte **1104→1108 passed, 6 skipped**; `mypy --strict` delta-zero, **48 arquivos**. Detalhe em HISTORICO 003.EX. |
| v90 | 16/08/2026 | Sessão 003.EZ fatia 1 (ARQUITETURA + IMPLEMENTAÇÃO): **R-AUD-04 DEPRECATED** (§5.2) — fundamento refutado por `DT-003EY-01`/D-ARQ-81: 003.EY mediu 23 obras, universalidade em 7/23 (6/23 com piso `n_cargos ≥ 17`); as duas matrizes-precedente de 003.EX eram artefato de amostra, não convergência. Sem sucessora — o momento `DEM` que o piso cravava incondicional passa a sair pela presunção protetiva de `R-AUD-02` (D-ARQ-68 cl.5) quando o PGR está silencioso sobre a quantificação do ruído. **`R-AUD-01`/`R-AUD-02`**, changelog de mesma ID: perna do ruído ganha âncora `[DERIVADO — NR-07 Anexo II itens 2 e 4.1 "a"/"b"/"c"; momento MR por 7.5.6 "d" + 7.5.7, a contrario 7.5.15]`; pernas `motorista_equipamento_pesado`/`ototoxico`/`e(ruido, ototoxico, vibracao_qualquer)` seguem `[VALIDADO]` sem âncora; silêncio do PGR sobre a quantificação do ruído (NR-09 9.4.1/9.4.2, avaliação condicional) admite presunção protetiva declarada por primitivo (`quando_ausente: {presumir_true: [ruido_acima_acao]}`), regra marcada `[INTERPRETADO — prioridade na revisão de saída]` nesse trecho; a perna `e` de R-AUD-02 **não** entra na allowlist — ausência ali continua bloqueante. **`R-RUIDO-01`**, changelog de mesma ID: `[INCERTO]` de 003.CB **FECHADO** — nível de ação é **NR-09 9.6.1 "c"** (disposição transitória, definição em 9.6.1.2); a NR-09 vigente (Portaria MTE 105/29-01-2026) não tem Anexo de Ruído; limiares 80/85 dB(A) inalterados, nível de ação registrado como transitório (reabre com Anexo próprio). Motor: `predicados.pernas_ausentes` (irmã de `pernas_ausentes_absorvidas`, sem gate `alguma_true` no `ou`, coleta primitivo/composto string por si); `emissao.stage_5_emissao` aceita `quando_ausente: {presumir_true: [...]}` (emite + `Pendencia(tipo="predicado_ausente_presumido", bloqueante=False)` por primitivo presumido, ou bloqueia se algum nome ficar fora da lista ou o conjunto vier vazio); `orquestrador.executar` ganha guarda: matriz com pendência `predicado_ausente_presumido` (anexada ou solta) nunca sai `VÁLIDA`, cai para `PARCIAL`. 14 testes novos com reversão nomeada, varredura inversa 14/14 confirmada. Quebras legítimas corrigidas com explicação nomeada (não silenciadas), 8 previstas + 4 adicionais medidos na reconferência em `7c7ec10` (mesma classe — ruído sem quantificação deixou de ser "risco que nada determina"): `test_orquestrador.py::test_raud04_*` (3, morrem por desenho — R-AUD-04 retirado, não sucedido) e `test_raud04_nao_promove_bloqueada_para_parcial` (inverte, renomeado); `test_orquestrador.py::test_rcli01_unico_risco_bloqueado_com_clinico_presente_fecha_bloqueada` (troca ruído por vibração genérica, preserva o invariante original); `test_exposicao_fisica.py::test_raud01_ruido_sem_quantificacao_gera_pendencia_bloqueante` (renomeado, inverte), `test_execucao_dedup_audiometria_tres_motivos_sem_conflito` (4→3 motivos), `test_execucao_ototoxico_via_agente_status_ok_sem_r_aud_02` (renomeado de volta a `..._sem_demissional`), `test_rvib02_vmb_sozinho_emite_audiometria` (reverte para `next()` único); `test_integracao_002c.py::test_pipeline_gates_emissao_consolidacao_atividade_critica` (audiometria volta ao loop genérico); `test_regra_biomonitoramento.py::test_sem_agente_nao_emite_biomonitoramento` (checagem por família `R-BIO-04*`, não por linhas de risco genéricas); `test_integracao_viverde.py::test_integracao_viverde_pnos_roteia_sem_achatar` (Adm-03: pendência `predicado_ausente_presumido` não-bloqueante anexada à linha, matriz `PARCIAL`, em vez de pendência bloqueante). **Medição Fascino** (`rodar-offline`, árvore parada, `relatorios/003ez_fascino_rodar.md`, commit `d218556`): **17 GHEs declaram `ruido`, todos com `ruido_acima_acao = AUSENTE`**, e os **17** passam a carregar `R-AUD-01`/`R-AUD-02` na coluna de motivos da linha de audiometria — contra **1** na baseline 003.EX (fecha `DT-003EG-01` — raiz, não só manifestação). Os 2 GHEs restantes não declaram ruído: GHE-14 recebe audiometria por atividade crítica (sem `DEM`, correto) e GHE-19 não recebe audiometria. **17/18** linhas de audiometria com `DEM` (a exceção é GHE-14); pendências `predicado_ausente_presumido` **32** (16 GHEs × 2 regras — o 17º GHE com ruído, GHE-16, resolve por `perna_ausente_absorvida`/D-ARQ-71 cl.2, nota de fronteira em D-ARQ-68 cl.5); status **3 VÁLIDA / 16 PARCIAL / 0 BLOQUEADA** (de 3/15/1 na baseline 003.EX — o GHE antes BLOQUEADA moveu para PARCIAL sob presunção); linhas de exame **173 → 172 (−1)** contra `main` em `7c7ec10` (com `R-AUD-04` ativa) — decomposto: −2 (GHE-06 e GHE-19 perdem a linha que `R-AUD-04` emitia incondicionalmente) +1 (GHE-06 a reganha, agora derivada de risco, por `R-AUD-01`/`R-AUD-02` sob presunção); contra a baseline pré-`R-AUD-04` (171, 003.EH) o saldo é +1, pela mesma linha de GHE-06. Suíte **1137 passed, 6 skipped** (árvore parada); `mypy --strict` limpo, **48 arquivos** (alvo canônico, delta-zero). Detalhe em HISTORICO 003.EZ. |
| v91 | 21/08/2026 | Sessão 003.FC (FECHAMENTO — higiene de documento): o H1 declarava "v2" enquanto a tabela de revisões estava em v90 — 88 versões de defasagem, achada quando o Crítico de IMPLEMENTAÇÃO declarou `PROTOCOLO v2` na linha de gate (leitura fiel de um título errado). Número removido do título; a versão passa a viver só na tabela, alinhando à convenção dos demais docs vivos. **DH-003FC-03** aberta e resolvida nesta sessão. Nenhuma R-* criada, alterada ou depreciada; nenhum conteúdo clínico tocado. |
| v92 | 10/09/2026 | Correção de âncora (higiene de documento): a linha da **v73** citava `.gitignore:26` como o ponto que ignora `relatorios/`; a entrada está na **linha 42** — a 26 é linha de comentário sobre LGPD art. 5º II. A âncora vinha propagada desde 003.EG sem re-medição e o mesmo erro estava em `PENDENCIAS_CLINICAS.md` (`Situação` e nota de reincidência de `DH-003EG-02`) e no bloco 003.FJ de `HISTORICO_OPERACIONAL.md`, corrigidos em `0147e14`. `DH-003EG-02` segue **ABERTA**: `git ls-files relatorios/` continua vazio. Nenhuma `R-*` criada, alterada ou depreciada; nenhum conteúdo clínico tocado. |
| v93 | 16/09/2026 | Sessão atual (branch `claude/festive-gates-soy0fr`, número não atribuído; IMPLEMENTAÇÃO): **`R-RX-03` CRIADA** (§5.4) e **`R-ESP-03` CRIADA** (§5.3) — poeira de madeira, agente identificável fora dos dois quadros do Anexo III NR-07 (não é sílica/asbesto/carvão do Quadro 1, nem PNOS do Quadro 2). RX 60M e Espirometria 24M, ambas `[INTERPRETADO]` — sem âncora normativa brasileira, origem IARC Monographs Vol. 62/1995 e 100C/2012 (Grupo 1, carcinogênico p/ humanos) + matriz-precedente: 2 PGRs independentes, mesma médica (Dra. Patrícia Montalvo Moraes), mesmo cargo (Carpintaria), mesmos valores — GHE-08 (PGR CONSCIENTE SPE 0030 FASCINO, 15.07.26) e GHE-04 (PGR CMO Residencial Aurora Lago das Rosas, 27.08.26). Novo agente `poeira_de_madeira` em `agentes.yaml` (`is_carcinogeno_iarc: true`, sem `termos:` — o próprio slug normaliza igual ao literal "Poeira de madeira" do PGR) e novo primitivo homônimo em `predicados.py`. **`DT-003EJ-01` RESOLVIDA** (`docs/PENDENCIAS_CLINICAS.md`) — decisão tomada (slug próprio, não `vocabulario_ausente`), autorizada pelo Diovanni após confirmação de que a validação humana das matrizes é reconferência linha a linha, não sign-off superficial. Sensibilização respiratória segue `[INCERTO]`, não bloqueia. 7 testes novos com reversão nomeada (varredura inversa 7/7 confirmada): 3 parametrizados de resolução de termo + guard de inventário (`test_resolvedor_termos.py`, 124→125) e 4 de emissão (`agente_medico/tests/test_poeira_de_madeira.py`, novo arquivo). Suíte **1233 passed, 6 skipped**; `mypy --strict` alvo canônico limpo, 48 arquivos, delta-zero. Detalhe em HISTORICO (bloco desta sessão). |
| v94 | 17/09/2026 | Sessão atual (branch `claude/fervent-brown-7dcc0y`, número não atribuído; IMPLEMENTAÇÃO, autorizada pelo Diovanni): **`R-PSY-02` DEPRECATED** (§5.7) — fundamento refutado por n=2 pós-protocolo-de-setembro/2026 (Ricco Hetrin 14/09 × CMO Varandas Flamboyant 16/09, desfechos opostos), mesmo padrão de `D-ARQ-81`/`R-AUD-04`, exceto que HÁ sucessora. **`R-PSY-03` CRIADA** (§5.7) — mesma conduta (Avaliação Psicossocial + Av. Médica de Saúde Mental, 12M, adm/per/MR), `quando: psicossocial` em vez de `todo_trabalhador`. Extrator novo `detectar_psicossocial` (`extracao_pgr.py`) lê o texto cru do PGR por 3 marcadores ("Inventário de Riscos Psicossociais"/COPSOQ/FRPRT, case-insensitive) e popula `GHEPGR.psicossocial` (campo existente desde `D-ARQ-49` P2, nunca extraído — nota de aplicação em `D-ARQ-49`, `DECISOES_ARQUITETURAIS.md`); `hidratar_ghe`/`hidratar_pgr` ganham parâmetro `psicossocial: bool = False`; `processar_arquivo_pgr` roda uma 3ª leitura de `extrair_texto_pgr` sobre o mesmo arquivo (mesma classe da duplicação já documentada entre `preparar_envelope`/`preparar_ghes`). Primitivo `psicossocial` novo em `predicados.py`. `[INTERPRETADO]` — n=2, mesma classe de obra (construção civil); risco residual (granularidade por PGR inteiro vs. por GHE) não resolvido, registrado na DT. **`DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-01` RESOLVIDA** (`docs/PENDENCIAS_CLINICAS.md`). 13 testes novos com reversão nomeada, varredura inversa 13/13 confirmada (`test_extracao_pgr.py`/`test_hidratacao.py`/`test_predicados.py`/`test_orquestrador.py`); 2 quebras legítimas corrigidas com causa nomeada (`test_orquestrador.py`/`test_integracao_002c.py` — perdem as 2 linhas que só saíam por R-PSY-02 incondicional). Suíte **1247 passed, 6 skipped, 2 failed** (falhos são ambiente, `libreoffice-writer` ausente, pré-existente — não desta sessão), delta +13 sobre o baseline de PR #337 (1236); `mypy --strict` alvo canônico limpo, 48 arquivos, delta-zero. `PAINEL_ESTADO.md` re-tirado: regras 25/44 (57%), cas 50/80 (62%), inalterados (troca 1-por-1). Detalhe em HISTORICO (bloco desta sessão). |
| v95 | 24/09/2026 | Sessão atual (branch `claude/inspiring-turing-0ylkmk`, número não atribuído; IMPLEMENTAÇÃO, decisão do Diovanni de 23/09/2026): **`R-RX-01` ganha o ramo `R-RX-01-qual`** (§5.4, mesma ID clínica, D-ARQ-20) — sílica sem avaliação quantitativa **com** avaliação qualitativa P×S no PGR → RX OIT 12M `[adm, per, MR, dem]`, `[INTERPRETADO — prioridade na revisão de saída]`. Fecha `DT-003EC-01`. Extração: campo verbatim `RiscoVerbatim.avaliacao_qualitativa` (banda S·P·NÍVEL, rota determinística) → `RiscoPGR.nivel_risco`/`Risco.nivel_risco`. Asbesto e rota LLM fora, declarados. Efeito medido: divergência RX 24M×12M 27→0 (Porto Araras I), 8→0 (Vila Brasil), 31→0 (Fascino). |
| v96 | 24/09/2026 | Mesma branch (`claude/inspiring-turing-0ylkmk`, pós-merge do PR #366; IMPLEMENTAÇÃO, decisão do Diovanni de 24/09/2026): **`R-PKG-TRANSITO` CRIADA** (§6) — risco declarado "Bater contra ou ser atingido por (trânsito)" → acuidade visual + audiometria 12M adm/per/MR, `[INTERPRETADO]`. Slug novo `transito_via_publica` em `agentes.yaml`. Parte de `DT-003EB-01` classe (4): DIREÇÃO/PATRIMÔNIO (Vila Brasil) e VENDAS (Fascino); vigia e planejamento seguem abertos. Efeito medido: subemissão 13→9 (Vila Brasil), 9→5 (Fascino), Porto Araras inalterado, zero superemissão nova. |
| v97 | 24/09/2026 | Branch `claude/eager-fermat-txbn7h` (IMPLEMENTAÇÃO, decisões do Diovanni de 23/09 e 24/09/2026): **`R-BIO-05` CRIADA** (§5.9) — agente do Quadro 1 (IBE/EE) com todo risco classificado IRRELEVANTE na matriz P×S do PGR → indicador de R-BIO-04 não emitido; observação de menção documental na linha do cargo, uma por agente. BAIXO emite. `[INTERPRETADO]`, conferência da NR-07 vigente `[A CONFERIR — D-ARQ-69]` (gov.br negado pela rede). Fecha `DT-003EB-02`. Escopo reduzido de BAIXO+IRRELEVANTE para só IRRELEVANTE depois da medição: dispensar em BAIXO zerava a superemissão do Fascino (7) mas criava 10 subemissões nos gabaritos da Dra. Patrícia. Quadro 2 (IBE/SC), R-BIO-03 e R-PKG-BZ fora. Efeito medido (`comparar_matriz_gabarito`, `main 657ccda` × working tree): Porto Araras I superemissão **1→0** (BAA do pintor, GHE-14 vira observação); Fascino e Vila Brasil **idênticos** em todas as células; nenhuma subemissão nova. |
| v98 | 24/09/2026 | Branch `claude/eager-fermat-txbn7h` (CONHECIMENTO — conferência normativa, D-ARQ-69): NR-07 conferida no PDF fornecido pelo Diovanni (cabeçalho até Portaria MTP 567/2022). **`R-BIO-05`**: `[A CONFERIR]` fechado — 7.5.12 "b" condiciona a obrigatoriedade dos exames laboratoriais à classificação de riscos do PGR; regra compatível com a norma, marcador `[INTERPRETADO]` mantido (o corte IRRELEVANTE não é literal); corrigida a leitura de 7.5.15 no corpo (exime momentos, não fixa obrigatoriedade). **`R-RX-01-qual`**: `[A CONFERIR]` fechado — Quadro 1 do Anexo III idêntico à leitura de 003.EH; 12M abaixo do ramo sem-avaliação (24M), `[INTERPRETADO]` mantido. Nenhuma regra criada, alterada ou depreciada; nenhum código tocado. |
