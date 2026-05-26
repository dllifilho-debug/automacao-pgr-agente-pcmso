# Mapa de GHE — PGR Viverde (CMO Residencial Viverde Areião SPE LTDA)

**Origem:** PGR VIVERDE V02 — 03.02.25 (PGR/GRO 2023/2025, Rev.02).
**Sessão:** 002.L (estruturar PGR Viverde).
**Princípio (D-ARQ-21, a registrar):** o agrupamento em GHE é **canônico** — transcrevo
o agrupamento que a CMO declarou nos cabeçalhos `ETAPA`/`SETOR-FUNÇÃO`, **sem re-agrupar**.
A Carolini respeita o agrupamento do PGR; o motor também.

**Convenção de quantificação (Opção 1, sessão 002.L0):**
- Ruído com dB(A) → `valor + unidade="dB(A)"`.
- Sílica/PNOS/químicos em mg/m³ ou ppm → `valor + unidade`, **`pct_LT=None`** → cai em
  pendência de conversão mg/m³→%LEO (DT a abrir — ver fim do doc).
- Altura, esforço, acidente → `quantificacao=None`.
- Riscos ergonômicos e de acidente **entram no fixture** (inventário é canônico, R-GHE-04)
  mas não disparam exame no motor hoje.

**Validade do PGR:** 2023/2025, Rev. 10/01/2025. Verificar contra a regra "< 2 anos"
(R-PGR-01) — provável que precise renovação; registrar como dado, não bloquear aqui.

---

## ESTRUTURA (etapa 003) — 16 GHEs declarados

### GHE Est-01 — Estrutura de concreto armado (carpinteiro)
**Cargos:** carpinteiro, meio of. carpinteiro, servente
**Tarefas:** ET01–ET06 (execução de fôrma de pilar e laje)
**Riscos:**
- Ruído 82,2 dB(A)
- PNOS/PNOR 0,163 mg/m³
- Trabalho em altura
- Esforço físico (ergonômico)
- Acidente: disco serra circular; objeto pontiagudo (prego)
**EPI:** protetor auditivo NRRsf≥15; respirador PFF2; cinto/linha de vida; botina antiperfurante; avental raspa; protetor facial

### GHE Est-01b — Estrutura de concreto armado (armador)
**Cargos:** armador, meio of. armador, servente
**Tarefas:** ET07–ET09 (execução de viga, pilar e laje; montagem de ferragem)
**Riscos:**
- Trabalho em altura
- Esforço físico (transporte de aço)
- Movimento repetitivo (turquesa)
**EPI:** cinto/linha de vida
**Nota:** mesmo nº de GHE da CMO (Estrutura 01) mas cargo distinto (armador). Separado de Est-01 — cada cargo é GHE próprio. **Sem ruído nem químico declarados** ("não opera policorte").

### GHE Est-02 — Preparação argamassa (betoneira)
**Cargos:** op. betoneira, servente
**Tarefas:** ET11–ET14
**Riscos:**
- PNOS/PNOR (habitual, sem medição numérica nesta linha)
- Umidade
- Ruído 89,6 dB(A)
- Esforço físico
**EPI:** protetor auditivo NRRsf≥15; respirador 5N11; luvas/avental/bota PVC; óculos

### GHE Est-03 — Montagem/manutenção elevador cremalheira e grua
**Cargos:** eletricista industrial, mecânico de manutenção, eletricista
**Tarefas:** ET15–ET19
**Riscos:**
- Ruído 72,4 dB(A)
- Eletricidade (teste de tensão)
- Trabalho em altura
- Esforço físico
- Químico: 1,3-Propanediamine, N-[3-(tridecyloxy)propyl] (graxa/betume) — sem mg/m³ declarado
**EPI:** respirador PFF3 SL; luvas químicas; creme protetor; cinto/linha de vida
**Nota:** PGR cita "Monitoramento Biológico através do PCMSO" para o químico.

### GHE Est-04 — Operação elevador cremalheira
**Cargos:** op. elevador cremalheira, servente
**Tarefas:** ET20–ET21
**Riscos:**
- Ruído 79,2 dB(A)
- Esforço físico
**EPI:** protetor auditivo NRRsf≥15

### GHE Est-05 — Içamento de materiais (grua)
**Cargos:** sinaleiro, servente
**Tarefas:** ET22–ET24
**Riscos:**
- Queda de material
- Trabalho em altura
- Ruído 77,5 dB(A)
**EPI:** protetor auditivo; cinto/linha de vida

### GHE Est-06 — Alvenaria
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** ET25–ET28
**Riscos:**
- Trabalho em altura
- Ruído 78,8 dB(A)
- Movimento repetitivo e esforço físico
- PNOS/PNOR 0,735 mg/m³
**EPI:** protetor auditivo NRRsf≥15; respirador PFF2 (uso voluntário); luvas impermeáveis; óculos

### GHE Est-07 — Prumada elétrica / instalação elétrico-telefônica (desenergizada)
**Cargos:** eletricista, meio of. eletricista, servente
**Tarefas:** ET29–ET33
**Riscos:**
- Trabalho em altura
- Ruído 82,8 dB(A)
- PNOS/PNOR 0,376 mg/m³
- **Sílica 0,0071 mg/m³** → pendência de conversão
- Acidente: disco talhadeira sem proteção
**EPI:** PFF2; cinto/linha de vida
**Nota:** "NÃO TRABALHA COM REDE ENERGIZADA" — distinguir da Est-16 (energizada).

### GHE Est-08 — Tubulação parede/teto / instalação hidro-sanitária
**Cargos:** encanador, meio of. encanador, servente
**Tarefas:** ET34–ET37
**Riscos:**
- Trabalho em altura
- Ruído 83,3 dB(A)
- PNOS/PNOR 0,202 mg/m³
- **Metil Etil Cetona 10,1 ppm**
**EPI:** PFF2; luvas nítrica; óculos

### GHE Est-09 — Solda / serralheria
**Cargos:** serralheiro, meio of. serralheiro, servente
**Tarefas:** ET38–ET42 (solda eletrodo, corte de ferragem)
**Riscos:**
- Trabalho em altura
- Ruído 88,7 dB(A)
- Radiação não-ionizante (solda)
- **Dióxido de Titânio 0,008 mg/m³** (solda com eletrodo revestido)
- Acidente: disco policorte/lixadeira
**EPI:** máscara automática de solda; respirador semifacial filtro 2078 P95; luvas vaqueta; avental vaqueta; protetor solar FPS60; cinto/linha de vida
**⚠ PONTO CRÍTICO (DT-002K-02 / D-ARQ-18):** o serralheiro **solda** (tarefa declarada → exposição confirmada documentalmente, R-GHE-05 satisfeita). MAS o agente químico medido é **Dióxido de Titânio**, não cromo/manganês. A nota da RQ.61 (002.K) dizia "Cromo <10% LT" — o **PGR não confirma cromo nem Mn**. Divergência PGR↔RQ.61 a resolver na 002.M. O fixture reflete o PGR (TiO₂), não a nota da matriz. O "pacote soldador" (Mn/CO/cromo) **não é disparado** pelo agente declarado neste PGR.

### GHE Est-10 — Limpeza (área de vivência)
**Cargos:** servente
**Tarefas:** ET43–ET45
**Riscos:**
- Queda (piso molhado)
- Microrganismos (bactérias, fungos)
- Produtos domissanitários (detergente, água sanitária)
**EPI:** luvas látex; avental PVC; bota PVC; PFF2; protetor auditivo NRRsf≥6

### GHE Est-11 — Serviços gerais
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** ET46–ET49 (carga/descarga, valas, varrição, concretagem com vibrador)
**Riscos:**
- Trabalho em altura
- PNOS/PNOR 0,735 mg/m³
- Esforço físico
- Ruído 71,6 dB(A)
**EPI:** cinto/linha de vida; óculos; luvas nítrica; PFF2; protetor auditivo NRRsf≥10
**Nota:** 2º GHE de pedreiro (o 1º é Est-06 Alvenaria). CMO separa pedreiro por atividade — respeitado.

### GHE Est-12 — Pintura (peças metálicas, estrutura)
**Cargos:** pintor, meio of. pintor, servente
**Tarefas:** ET50–ET52
**Riscos:**
- Ruído 78,8 dB(A)
- **Etanol 4,4 ppm** (thinner/zarcão/esmalte sintético)
- Esforço físico
**EPI:** respirador semifacial cartucho vapores orgânicos; óculos; luvas PVC; protetor auditivo NRRsf≥10
**Nota:** 1º GHE de pintor (estrutura). O 2º é Acab-05 (pintura interna/externa).

### GHE Est-13 — Portaria
**Cargos:** porteiro, vigia
**Tarefas:** ET53
**Riscos:**
- Queda (piso molhado)
**EPI:** calçado antiderrapante
**Nota:** porteiro tem regra própria no protocolo (R-PKG-PORT, R-VIS-02 — acuidade visual adm/per/MR). Cargo relevante.

### GHE Est-14 — Operação de grua
**Cargos:** op. grua
**Tarefas:** ET54
**Riscos:**
- Trabalho em altura
**EPI:** cinto/linha de vida; óculos; luvas nítrica
**Nota:** sem ruído próprio declarado (distinto do içamento Est-05).

### GHE Est-16 — Instalação elétrica temporária (energizada)
**Cargos:** eletricista
**Tarefas:** ET55–ET56
**Riscos:**
- Eletricidade (energizada — teste de tensão em pontos energizados)
- Trabalho em altura
**EPI:** cinto/linha de vida; óculos; luvas nítrica
**Nota:** ⚠ distinto do Est-07 (desenergizada). Este trabalha **com rede energizada** → atividade crítica (R-ECG-01, R-VIS-01). CMO não numerou como "15"; o "15" foi Operação Grua (Est-14). Numeração da CMO tem saltos — preservo o nome, não forço sequência.

---

## ACABAMENTO (etapa 04) — 9 GHEs declarados

### GHE Acab-01 — Reboco interno e externo
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** AB01–AB05
**Riscos:**
- Trabalho em altura
- Movimento repetitivo; esforço físico
- Argamassa (dermatite de contato)
- Ruído 78,8 dB(A)
**EPI:** protetor auditivo NRRsf≥8; luvas impermeáveis

### GHE Acab-02 — Contrapiso
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** AB06–AB10
**Riscos:**
- PNOS/PNOR 0,088 mg/m³
- Trabalho em altura
- Movimento repetitivo e esforço físico
- Umidade
- Ruído 76,5 dB(A)
**EPI:** protetor auditivo NRRsf≥8; bota PVC; luvas impermeáveis

### GHE Acab-03 — Impermeabilização cristalizante
**Cargos:** servente
**Tarefas:** AB11
**Riscos:**
- Químico: primer, cimento polimérico, mastique (sem mg/m³)
**EPI:** respirador semifacial cartucho vapores orgânicos; óculos; luvas PVC

### GHE Acab-04 — Gesso corrido e placa
**Cargos:** gesseiro, meio of. gesseiro, servente
**Tarefas:** AB12–AB15
**Riscos:**
- Trabalho em altura
- PNOS/PNOR 0,08 mg/m³
- Movimento repetitivo
- Ruído 73,6 dB(A)
**EPI:** PFF2; óculos; luvas PVC; protetor auditivo NRRsf≥8

### GHE Acab-05 — Pintura interna e externa
**Cargos:** pintor, meio of. pintor, servente
**Tarefas:** AB16–AB21
**Riscos:**
- Trabalho em altura
- Tinta base d'água (dermatite)
- **PNOS/PNOR 21,94 mg/m³** (lixar parede — valor alto)
- Movimento repetitivo
- Ruído 78,8 dB(A)
- **Sílica <0,0050 mg/m³** → pendência de conversão
**EPI:** PFF2; óculos; luvas PVC; protetor auditivo NRRsf≥8
**Nota:** 2º GHE de pintor (acabamento).

### GHE Acab-06 — Revestimento / assentamento de cerâmica
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** AB22–AB27
**Riscos:**
- Trabalho em altura
- Acidente: disco serra mármore
- Ruído 78,3 dB(A)
- **Sílica 0,0050 mg/m³** → pendência de conversão
- PNOS/PNOR 1,27 mg/m³
- Movimento repetitivo
**EPI:** PFF2; óculos; luvas PVC; protetor auditivo NRRsf≥8

### GHE Acab-07 — Rejunte e limpeza grossa e fina
**Cargos:** servente
**Tarefas:** AB28–AB32
**Riscos:**
- Trabalho em altura
- Movimento repetitivo
- Queda
- **Cloreto de Hidrogênio <0,01 ppm**
- Argamassa (rejunte — dermatite)
**EPI:** PFF2; óculos; luvas/avental/bota PVC

### GHE Acab-08 — Assentamento de bancada
**Cargos:** pedreiro, meio of. pedreiro, servente
**Tarefas:** AB33–AB38
**Riscos:**
- Acidente: disco serra mármore
- Ruído 89,3 dB(A)
- PNOS/PNOR 1,4 mg/m³
- **Estireno 1,7 ppm**
- Esforço físico
- **Sílica 0,005 mg/m³** → pendência de conversão
**EPI:** PFF2; óculos; luvas; protetor auditivo NRRsf≥17

### GHE Acab-09 — Impermeabilização manta asfáltica
**Cargos:** encarregado, aplicador de asfalto impermeabilizante, servente
**Tarefas:** AB39–AB44
**Riscos:**
- Trabalho em altura
- Caldeira/maçarico (queimadura)
- **Monóxido de Carbono** (manta a quente)
- Químico: argamassa polimérica em **espaço confinado** (reservatório); asfalto + 4-nonilfenol etoxilado + 5-cloro-2-metil-isotiazolinona; primer/cimento polimérico/mastique
- Ruído 75,9 dB(A)
**EPI:** respirador semifacial cartucho gases + filtro 5N11; óculos; luvas vaqueta cano longo; extintor
**Nota:** ⚠ **espaço confinado** declarado (AB43) → predicado R-PSY-01 (avaliação psicossocial) + R-PKG-ATIVCRIT. Monóxido de carbono → carboxihemoglobina (precedente na Matriz Patrícia).

---

## ADMINISTRAÇÃO DE CAMPO (etapa 05) — 6 GHEs declarados

### GHE Adm-01 — Engenharia / planejamento de obra
**Cargos:** engenheiro, estagiário
**Tarefas:** ADC01–ADC04
**Riscos:**
- Trabalho em altura (eventual — liberação/recebimento em periferia)
- Queda de materiais
- Postura inadequada (ergonômico)
- Ruído 65,1 dB(A)
**Nota:** ruído abaixo do nível de ação; perfil administrativo.

### GHE Adm-02 — Segurança do trabalho
**Cargos:** técnico de segurança do trabalho, estagiário
**Tarefas:** ADC05–ADC08
**Riscos:**
- Trabalho em altura (eventual)
- Queda de materiais
- Postura inadequada
- Ruído 65,1 dB(A)

### GHE Adm-03 — Mestre de obra / execução de obra
**Cargos:** mestre de obra, encarregado
**Tarefas:** ADC09–ADC12
**Riscos:**
- Trabalho em altura (intermitente)
- Queda de materiais
- Postura inadequada
- Ruído (aguardando medição) → **pendência: medição ausente (R-PGR-04)**

### GHE Adm-04 — Supervisão rejunte/limpeza
**Cargos:** encarregado
**Tarefas:** ADC13–ADC14
**Riscos:**
- Piso escorregadio
- Queda de materiais

### GHE Adm-05 — Administrativo
**Cargos:** administrativo de obra, aux. administrativo, jovem aprendiz
**Tarefas:** ADC15–ADC16
**Riscos:**
- Queda de materiais
- Movimento repetitivo (computador/mobiliário — ergonômico)

### GHE Adm-06 — Almoxarifado
**Cargos:** almoxarife, servente
**Tarefas:** (recebimento de materiais — verificar inventário ADC próprio)
**Riscos:** a confirmar (provável: movimento/esforço, queda de materiais)

---

## LACUNAS E PONTOS DE ATENÇÃO (para a 002.M)

1. **GHE de Fundação ausente do inventário.** A matriz cargo×tarefa declara op. retroescavadeira, op. escavadeira, motorista (caçamba), op. perfuratriz na etapa Fundação — mas **não há bloco de risco ET próprio** para eles. Lacuna R-PGR-04. No fixture: GHE-FUN com `riscos=()` → pendência estrutural (Stage 3). Não inventar riscos.

2. **Sílica sempre em mg/m³, nunca em %LEO.** Todas as 4 ocorrências (Est-07, Acab-05, Acab-06, Acab-08) têm concentração medida baixíssima (0,005–0,0071 mg/m³). Pela Opção 1, `pct_LT=None` → pendência de conversão. **DT a abrir:** "conversão mg/m³ → %LEO para rotear faixa de RX (R-RX-01) — qual LEO/fonte? Carolini." Sem isso, sílica não emite RX no motor.

3. **Serralheiro = TiO₂, não cromo/Mn** (Est-09). Divergência com a nota da RQ.61 (DT-002K-02). O PGR não confirma o pacote-soldador. Resolver na 002.M (D-ARQ-18: bug ou lacuna).

4. **Gás e Marceneiro sem bloco de risco** — citados na matriz cargo×tarefa (gás: mecânico industrial; portas: marceneiro) mas sem inventário ET/AB próprio que eu tenha localizado. Possível lacuna R-PGR-04 a confirmar, ou tarefas absorvidas por outro GHE.

5. **Ruído "aguardando medição"** em Adm-03 (ADC12) → pendência de medição (R-PGR-04).

6. **Numeração de GHE da CMO tem saltos e repetições** (Est-01 aparece para carpinteiro E armador; "15" é grua; "16" é elétrica temporária). Preservo os nomes/cargos declarados; não forço sequência limpa. O `id` do GHEPGR no fixture pode ser `GHE-EST-09` etc. (estável para teste), com `nome` = SETOR/FUNÇÃO da CMO.

7. **PNOS com valores muito díspares** (0,08 a 21,94 mg/m³) todos rotulados PNOS/PNOR. Pela R-RX-01-pnos → 60M independente do valor. Não exige conversão.

8. **Validade do PGR** (2023/2025) — verificar regra "<2 anos" (R-PGR-01). Registrar como dado do PGR.

---

## RESUMO PARA O FIXTURE (002.L-fixture)

- **~28 GHEs** (16 Estrutura + 9 Acabamento + 6 Administração + 1 Fundação-pendência).
- Cada `GHEPGR`: `id` estável, `nome` = SETOR/FUNÇÃO da CMO, `cargos`, `riscos` (RiscoPGR com quantificação conforme convenção), `epis`, `psicossocial` (True só em Acab-09 — espaço confinado).
- Cargos novos para `cargos.yaml` (cascata esperada): carpinteiro, armador, op. betoneira, eletricista industrial, mecânico de manutenção, op. elevador, sinaleiro, pedreiro, eletricista, encanador, serralheiro, op. grua, pintor, porteiro, vigia, gesseiro, aplicador de asfalto, engenheiro, técnico de segurança, mestre de obra, encarregado, administrativo, almoxarife, marceneiro, mecânico industrial, op. retroescavadeira, op. escavadeira, motorista, op. perfuratriz.
- Agentes novos para `agentes.yaml` (cascata esperada): ruido (já existe?), pnos (=poeira_nao_classificada, já existe), silica (já existe), metil_etil_cetona, etanol, estireno, dioxido_de_titanio, monoxido_de_carbono, cloreto_de_hidrogenio, 1,3-propanediamine, espaco_confinado (já existe), eletricidade, trabalho_altura (já existe).
