# Medição — PCMSO no acervo: inventário, modelos, origem das seções e proposta de arquitetura

`[MEDIDO — 13/10/2026, branch claude/busy-cerf-tqxkmg sobre main 582a786]` Sessão só de medição,
sem código. Texto extraído com `pdftotext` (PDF) e LibreOffice headless (DOC/DOCX/RTF → PDF e TXT),
no scratchpad da sessão, fora da árvore. Páginas de DOC/DOCX/RTF = render do LibreOffice (o
`docProps/app.xml` do Word vai entre parênteses quando diverge). Scripts de medição ficaram fora do
repositório; os números estão aqui.

> **Decisões do Diovanni (13/10/2026), depois da 1ª versão deste relatório:**
> 1. **As normas de `normas/` estão na última versão.** A vigência da NR-07 deixa de ser `[A MEDIR]` (§6).
> 2. **O modelo do PCMSO é o de 2026, o mais recente; os antigos não precisam.** Em 2026 o acervo tem dois
>    PCMSO: **T1 206 (17/03/2026), modelo A**, e **R70 (22/09/2026), modelo B**. O mais recente é o B,
>    e a troca A→B aconteceu entre essas duas datas (o controle de revisão do R70 tem a rev. 01 em
>    28/07/2026). Referência daqui em diante: **modelo B, testemunha R70**, e o Mauá Plateu d'Or 28.09.26
>    quando subir. Modelos A e C (§2) ficam registrados como histórico e saem do escopo. O §2.1 mede o R70
>    contra a matriz dele.

---

## 1. Inventário — os 24 arquivos com "PCMSO" no nome

**Achado 1: 8 dos 24 não são PCMSO, são matrizes RQ 61/01 com "PCMSO" no nome** (o título da RQ 61 é
"MATRIZ FUNÇÃO/EXAMES PCMSO"). **Achado 2: 1 é saída de gerador anterior, não documento da clínica.**
Sobram **15 PCMSO de verdade** (16 arquivos, porque Santa Luzia tem 2 versões).

| # | Arquivo (abreviado) | Data | Empresa / obra | Págs. | O que é | Modelo |
|---|---|---|---|---|---|---|
| P02 | PCMSO (OBRA NOVA) PASSARELA ESTADIO SERRA DOURADA.rtf | 13/05/2024 | Ricco Construtora | 141 | PCMSO | A |
| P03 | PCMSO - NOVO MODELO- SECONCI - Dra. Carolini maio 2024.docx | maio/2024 | **em branco** ("Nome da empresa", "data", "xxxx") | 70 (72) | **modelo vazio** | B |
| P04 | PCMSO Fazenda Jamaica -JBJ - rev 00- novembro 2022.docx | nov/2022 | JBJ Agropecuária | 114 (107) | PCMSO | C |
| P05 | PCMSO Fazenda Jamaica ... setembro 2022 (1).docx | set/2022 | JBJ Agropecuária | 86 | PCMSO | C |
| P06 | PCMSO Fazenda Jamaica ... setembro 2022.docx | set/2022 | JBJ Agropecuária | 57 | PCMSO | C |
| P07 | PCMSO OBRA NOVA TOCTAO SPE_T65_ 18.03.2024 [assinado].pdf | 18/03/2024 | SPE T65 (Toctao) | 63 | PCMSO | A |
| P08 | PCMSO renovação - C239 MUY_BUENO 04.04.2024.pdf | 04/04/2024 | C239 América (Muy Bueno) | 55 | PCMSO | A |
| P09 | PCMSO(ADENDO)SPE R70 ... 22.09.26 assinado.pdf | 22/09/2026 | SPE R70 | 89 | PCMSO | **B** |
| P10 | PCMSO(ATUALIZAÇÃO)CMO CONSTRUTORA ADM 06.03.2025.pdf | 06/03/2025 | CMO Construtora (sede) | 64 | PCMSO | A |
| P11 | PCMSO(ATUALIZAÇÃO)CMO RESIDENCIAL VISTAMERICA 08.12.25.pdf | 08/12/2025 | CMO Res. Vistamerica | 127 | PCMSO | A |
| P12 | PCMSO(ATUALIZAÇÃO)CMO RESIDENCIAL VIVERDE AREIAO 06.03.25.pdf | 06/03/2025 | CMO Res. Viverde Areião | 70 | PCMSO | A |
| P13 | PCMSO(ATUALIZAÇÃO)CONSCIENTE SPE 027 CASA BRASILEIRA 16.09.26.doc | 16/09/2026 | Consciente SPE 27 | 1 | **matriz** | — |
| P14 | PCMSO(ATUALIZAÇÃO)INCORPORAÇÃO R78 NATURIA 12.11.25.pdf | 12/11/2025 | Incorporação R78 | 95 | PCMSO | A |
| P15 | PCMSO(ATUALIZAÇÃO)SPE INCORPORAÇÃO EURO PARK SETOR C ... 15.04.2024.docx | 15/04/2024 | Euro Park C (Toctao) | 5 | **matriz** | — |
| P16 | PCMSO(ATUALIZAÇÃO)T1 206 EMPREEND. IMOB. ENVOLT 17.03.26.pdf | 17/03/2026 | T1 206 (Envolt) | 66 | PCMSO | A |
| P17 | PCMSO(OBRA NOVA)VISTAMÉRICA RESIDENCIAL SPE LTDA 19.06.2024.rtf | 19/06/2024 | CMO Res. Vistamerica | 87 | PCMSO | A |
| P18 | PCMSO(RENOVAÇÃO)CONSCIENTE CONST FAZENDA SANTA LUZIA (1).rtf | 27/03/2024 | Consciente Construtora | 88 | PCMSO | A |
| P19 | PCMSO(RENOVAÇÃO)CONSCIENTE CONST FAZENDA SANTA LUZIA.rtf | 27/03/2024 | Consciente Construtora | 88 | PCMSO (versão de P18; 145 tokens diferentes — riscos/exames) | A |
| P20 | PCMSO(RENOVAÇÃO)DINÂMICA - C239 ... MUY BUENO - 04.04.2024.docx | 04/04/2024 | C239 América (Muy Bueno) | 3 | **matriz** | — |
| P21 | PCMSO- DINAMICA- SOFT PEDRO LUDOVICO ... 06.04.20231 (3).docx | 06/04/2024 | Soft Pedro Ludovico 198 | 4 | **matriz** | — |
| P22 | PCMSO-OBRA NOVA-GCB 2F ENGENHARIA ... 05.04.2024.docx | 05/04/2024 | GCB / 2F Engenharia | 2 | **matriz** | — |
| P23 | PCMSO_Ricco_Construtora_Ltda..docx | 19/04/2026 | Ricco | 52 (1) | **saída de gerador anterior** (tabela GHE×exame com "Justificativa"; "cargos" são nomes e telefones lidos errado) | — |
| P24 | RENOVAÇÃO(PCMSO)-COOP.HAB.PQ FLAMBOYANT-QUASAR FLAMBOYANT 31.03.2024.docx | 31/03/2024 | Coop. Hab. Pq. Flamboyant | 6 (5) | **matriz** | — |
| P01 | ATUALIZAÇÃO-PCMSO-TEC GRUA ... 05.04.2024.docx | 05/04/2024 | Tec Grua | 2 | **matriz** | — |

P23 entrou no acervo no merge `ecbb4fb` (PR #447). Não é gabarito: não usar como saída validada.

### 1.1 Pareamento com PGR e matriz — por conteúdo, não só por nome

Critério: CNPJ do PCMSO encontrado no texto do PGR (`pdftotext`, todos os 36 PDFs de PGR do acervo),
mais data e lista de GHE. Onde o `PAREAMENTO_ACERVO.md` (feito por nome) diverge, está marcado.

| PCMSO | PGR no acervo | Matriz no acervo | Situação |
|---|---|---|---|
| P12 Viverde 06/03/2025 | PGR VIVERDE V02 (rev. 10/01/2025), CNPJ confere | MATRIZ CMO VIVERDE AREIAO 06.03.2025 (mesma data) | **Trio completo.** 15 GHE do PCMSO = 15 da matriz |
| P14 R78 12/11/2025 | PGR R78 NATURIA PARTE 2 — **só o GHE 07** (19 p., sem CNPJ) | MATRIZ GPL R78 12.11.25 (mesma data) | Trio **parcial no PGR**. 18/18 GHE do PCMSO = matriz |
| P11 Vistamerica 08/12/2025 | 2 PGR com o CNPJ, nenhum contemporâneo: Ver.02 Rev.01 (14/06/2024) e 2026-07-28 | MATRIZ CMO VISTAMERICA 08.12.25 (mesma data) | PCMSO+matriz; PGR de outra versão |
| P17 Vistamerica 19/06/2024 | PGR VISTAMERICA Ver.02 Rev.01 (14/06/2024), CNPJ confere | nenhuma de 2024 | **Par novo** (PCMSO+PGR) — não estava no PAREAMENTO |
| P02 Passarela/Ricco 13/05/2024 | 01. PGR RICCO SERRA DOURADA - MAI.24: CNPJ, data 13/05/2024 e "PASSARELA" no texto | nenhuma | **Par novo** — o PAREAMENTO lista os dois como órfãos |
| P07 T65 18/03/2024 | PGR - ALT T65 2024.2026 e PGR - TOCTAO ALT 65 (CNPJ confere) | MATRIZ SPE T65 08.07.26 e 24.09.26 (posteriores) | PCMSO+PGR; matriz de outra versão |
| P10 CMO ADM 06/03/2025 | PGR CMO Ver.02 Rev.02 (01/02/2024), CNPJ confere | MATRIZ ADENDO CMO ADM 03.12.25 (posterior) | PCMSO+PGR; matriz de outra versão |
| P09 R70 22/09/2026 | **nenhum** (CNPJ em nenhum PGR) | MATRIZ R70 22.09.26 (.doc e .pdf) | PCMSO+matriz |
| P08 Muy Bueno 04/04/2024 | nenhum | P20 (matriz com "PCMSO" no nome, mesma data) | PCMSO+matriz |
| P16 T1 206, P18/P19 Santa Luzia, P04–P06 Jamaica | nenhum | nenhuma (Santa Luzia: só adendo de 18.09.26, outra versão) | órfãos |
| P03 Seconci "novo modelo" | — | — | **Não é PCMSO da Seconci-empresa**: é o modelo em branco. O par 12 do PAREAMENTO ("PCMSO NOVO MODELO SECONCI") não se sustenta |

Correções a levar ao `PAREAMENTO_ACERVO.md` (não feitas nesta sessão — decisão do Diovanni): par 12 sem
PCMSO; par 14 (Euro Park C) é matriz, não PCMSO; P02↔Serra Dourada e P17↔Vistamerica Ver.02 Rev.01 são
pares; "Muy Bueno/C239 (2)" são 1 PCMSO + 1 matriz; Tec Grua, GCB, Soft Pedro Ludovico, Quasar
Flamboyant e Casa Brasileira são matrizes.

---

## 2. Modelo — um só ou vários?

**Três modelos, não um.** O ponto de partida ("Vistamerica 08.12.25, R70 22.09.26 e T1 206 17.03.26
têm o mesmo cabeçalho") se confirma **só no cabeçalho de página**. O corpo é de dois modelos diferentes.

Similaridade de texto (difflib sobre palavras, seções equivalentes):

| Comparação | Trecho | Razão |
|---|---|---|
| T1 206 × 9 PCMSO do modelo A (2024→2026) | "Norma Regulamentadora" → "Relatório Analítico" | **0,958 – 0,974** |
| T1 206 × 9 PCMSO do modelo A | "Programa de Vacinação" → "Termo de Compromisso" | 0,828 – 0,925 |
| R70 × Seconci "novo modelo" | "Norma Regulamentadora" → 1º GHE | **0,740** |
| R70 × T1 206 | mesmo trecho | 0,368 |
| Jamaica set/22 × nov/22 | do "Objetivo" ao fim | 0,71 |

- **Modelo A — legado Seconci (11 PCMSO, mar/2024 → mar/2026):** P02, P07, P08, P10, P11, P12, P14,
  P16, P17, P18, P19. Capa com "Portaria 3214/78 ... SEPRT 6.734/2020"; seções sem número: Identificação
  (quadro CNPJ/CNAE/grau de risco), Norma Regulamentadora NR-7, Objetivo, Diretrizes, Planejamento,
  Desenvolvimento, Responsabilidades, Exame Médico Ocupacional (ASO; exames; periodicidade Quadros 1 e 2
  do Anexo I; benzeno; altura no demissional; avaliação psicossocial), Documentos (prontuário; relatório
  analítico), **bloco por cargo** ("Unidade / Setor: GHE / Cargo"), Programa de Vacinação, Cronograma de
  Atividades / Programação das Ações, kit de primeiros socorros, Termo de Compromisso.
- **Modelo B — "novo modelo" da Dra. Carolini (mai/2024), em uso no R70 (set/2026):** seções numeradas.
  Seconci: 1 Identificação · 2 Cronograma de revisão · 3 NR-7 · 4 Objetivo · 5 Diretrizes · 6 Planejamento
  · 7 Desenvolvimento · 8 Responsabilidades · 9 Exame médico ocupacional (9.3.x Quadros 1/2, benzeno,
  cancerígenos, radiações ionizantes, altura, espaço confinado, NR-32; 9.4 audiometria; 9.5 RX; 9.6
  espirometria; 9.7 gestantes/lactantes; 9.8 manipuladores de alimento; 9.9 calor e aclimatação) · 10
  Documentação · Programa de vacinação (com salas de vacina de Goiânia) · 11 Anexos (questionário OMS de
  epilepsia, fluxos de conduta, acidente com material biológico, relatório analítico). O R70 acrescenta
  "9.10 Riscos psicossociais", o bloco por GHE (após 10), 12 Programa de conscientização em saúde, 13
  Cronograma, 14 Suprimentos de emergência, 15 Termo de compromisso, 16 Anexos. **No R70 o bloco é por GHE
  (riscos uma vez por GHE, cargos listados); no modelo A é por cargo (riscos repetidos em cada cargo).**
- **Modelo C — Fazenda Jamaica (agro, 2022):** índice próprio (1 Identificação com profissionais do PGR
  e médico; 5.2 agrotóxicos; aclimatização; kit de primeiros socorros). Fora da construção civil; não
  serve de referência para a frente.

O Mauá Plateu d'Or (28.09.26) é posterior ao R70; a hipótese é que seja modelo B — **`[A MEDIR]` quando o
arquivo chegar.**

### 2.1 R70 (modelo B, 2026) × matriz R70 22.09.26 — o que a matriz decide no PCMSO

`[MEDIDO — 13/10/2026]` O PGR do R70 não está no acervo; a medição é PCMSO × matriz.

- **GHE: 21/21 iguais**, mesma numeração (o R70 também pula o GHE 14), diferenças só de grafia
  ("MÁQUINAS"/"MAQUINAS", "- DESENERGIZADO"/"(DESENERGIZADO)").
- **As notas "Incluir no word do PCMSO" da matriz foram feitas.** A matriz pede "risco baixo no PGR para
  Copolímero de estireno e butadieno" (3×) e "acetona"; os dois aparecem como risco químico, com agravo, no
  bloco de GHE do PCMSO. A lista de riscos do PCMSO = riscos do PGR + o que a médica manda incluir.
- **O nome do exame no PCMSO não é o da matriz.** A matriz diz "Avaliação Psicossocial" (43×); o PCMSO lista
  `(0289) Avaliação Médica de Saúde Mental` (20 GHE). O PCMSO usa nome e código do SOC: 12 exames distintos
  com código (`(0295) Exame Clínico` 21×, `(0281) Audiometria` 18×, `(0562) Espirometria` 17×, `(1415)
  Radiografia de tórax` 16×, ..., `(0467) Cromo Urinário` 1×). Gerar o bloco exige o mapa
  slug do app → código/nome SOC `[A DECIDIR]`.
- No modelo B o bloco é **por GHE** (descrição do ambiente, cargos com descrição, riscos uma vez só, exames)
  — 40% das palavras do R70.

### 2.2 O que faz um PCMSO pesar — medido nos RTF, hipótese para o Mauá

Os 4 RTF têm 62–64 MB para ~90–140 páginas. **92–95% dos bytes são imagem em hexadecimal** (P02: 58,5 de
61,9 MB; P17: 58,4 de 63,4 MB): 8 figuras, das quais 2 metarquivos WMF de página inteira (~45×70 cm em
`picwgoal`, fundo de capa/página) — o RTF guarda imagem em hex (2 bytes por byte). No DOCX do modelo B
(P03) as imagens somam 0,45 MB. **Hipótese para os 35 MB do Mauá: imagem de fundo/capa sem compressão
ou colada várias vezes (cabeçalho por seção).** Conferir com `unzip -l` em `word/media/` quando chegar.
Implicação: o modelo não deve entrar no git cru se tiver 35 MB — ver §5.

---

## 3. Origem de cada seção (Viverde P12 e R78 P14, modelo A; R70 P09, modelo B)

Prova de origem usada: texto literal presente nas duas fontes, incluindo erros (o erro de digitação
"Peneumoconiose" do PGR Viverde aparece 5× no PGR e 15× no PCMSO).

| Seção | Classe | Evidência medida |
|---|---|---|
| Capa: empresa, nome da obra, data | (b)+(d) | Razão social/CNPJ do PGR; data = data da matriz (Viverde, R78, R70: mesma data) |
| Identificação (endereço, CNPJ, CNAE, grau de risco, descrição CNAE) | (b) | CNPJ do PCMSO encontrado no PGR em 6 PCMSO (P02, P07, P10, P11, P12, P17); o PGR parcial do R78 não traz CNPJ |
| Controle de revisão (só B) | (d) | Datas e "considerações" (R70: "Inclusão dos riscos psicossociais") escritas à mão |
| NR-7, Objetivo, Diretrizes, Planejamento, Desenvolvimento, Responsabilidades, Exame médico (ASO, tipos de exame, periodicidade, Quadros 1/2, benzeno, altura, psicossocial), Documentos | (c) | Razão 0,96–0,97 entre 10 PCMSO de 7 empresas e 2 anos |
| Bloco por GHE — nome do GHE, lista de GHE | (a) | 15/15 (Viverde) e 18/18 (R78) GHE iguais aos da matriz |
| Bloco por GHE — descrição do ambiente e do cargo | (b) | Literal do PGR: "Serviço com solda eletrodo na confecção de grades..." (Viverde), "Cortar conforme projeto as peças..." (R78 GHE 07) |
| Bloco por GHE — perigo/fator de risco e grupo | (b) **editado pela médica** | 6 matrizes PDF trazem notas "Incluir no word do PCMSO, risco trivial/baixo no PGR para Éter monobutílico de etilenoglicol / Copolímero de estireno e butadieno / acetona", "Risco Cromo abaixo de 10% do LT da ACGIH" — a lista de riscos do PCMSO **não é** a do PGR filtrada mecanicamente |
| Bloco por GHE — agravos à saúde | (b) **ou biblioteca** | Viverde: literal do PGR. R78/T1 206/Vistamerica/R70: texto longo ("A exposição ao ruído excessivo pode apresentar...") que está em 10 PGRs do acervo mas **não** no PGR parcial do R78 — biblioteca comum `[INFERIDO]` |
| Bloco por GHE — exames com código, admissão/periódico/retorno/mudança/demissão, periodicidade | (a) | Códigos `(0281) Audiometria`, `(0295) Exame Clínico`... são do sistema SOC (o R70 cita "Sistema SOC"); os exames e momentos seguem a matriz. Conferência exame a exame `[A MEDIR]` — a quebra de página da matriz PDF impede comparação automática limpa |
| Programa de vacinação | (c) | Razão 0,83–0,93 |
| Cronograma de atividades / Programação das ações (13.1 no B) | (d) | Meses e "X" preenchidos por obra; local ("MEDITERRANÈ") à mão |
| Kit de primeiros socorros / suprimentos de emergência | (c) com quantidades (d) | Quantidades variam por obra |
| Termo de compromisso | (c)+(b) | Texto fixo com o nome da empresa |
| Médico responsável, CRM, RQE, assinatura | (d) | Dra. Patrícia Montalvo Moraes, CRM-GO 14.949, RQE 9.662; assinatura digital: BRy em 4 PDFs (P09–P12, metadado `Producer`), plataforma de assinatura eletrônica no P07 |
| Relatório analítico (NR-07 7.6.2) | (d) | Só o texto fixo que o descreve; nenhum PCMSO traz relatório preenchido |
| Anexos (OMS epilepsia, fluxos de conduta) — só B | (c) | Mesmos títulos em P03 e P09; trecho "Programa de Vacinação"→fim com razão 0,63 entre eles (o R70 acrescenta seções 12–15) |

**Peso de cada parte:** o bloco por GHE é **49–68% das palavras** no modelo A (8 PCMSO medidos) e **40%**
no R70. É a parte (a)+(b) — a que o app já tem quase toda.

---

## 4. O que o app já produz e o que falta

Já produz (código em `agente_medico/superficie/`, todos em DOCX via `python-docx`, montados do zero):

| Produto | Arquivo | Cobre no PCMSO |
|---|---|---|
| Matriz RQ 61 | `documento_matriz.py` (D-ARQ-73) | GHE, cargos, exames, momentos, periodicidade — (a) inteiro |
| Memorial de raciocínio | `memorial_matriz.py` (D-ARQ-87) | Não entra no PCMSO; é anexo das médicas |
| Riscos para o ASO | `relatorio_aso.py` (D-ARQ-91, D-ARQ-95) | Lista de riscos por GHE com veredito (consta / conferir / não consta) — é exatamente a decisão que hoje vira nota "Incluir no word do PCMSO" |
| Agravo do PGR por risco, verbatim | D-ARQ-93 | Coluna "agravos à saúde" (NR-07 7.5.4 a) |
| Cabeçalho | `CabecalhoDocumento` | empresa, obra, tipo, data, médico coordenador, CRM (digitados) |

Falta, por classe:

- **(b) dados da empresa:** `tipos.PGR` guarda só `validade`, `assinatura_engenheiro` e `ghes`. **Não há
  CNPJ, endereço, CNAE, grau de risco nem descrição do CNAE** no modelo (só `CenarioExposicao.cnae`, para o
  LEO-resolver). Extração nova no parser, por família de PGR.
- **(b) descrição do ambiente do GHE e do cargo:** `GHEPGR.cargos` é `tuple[str, ...]` (só nome). Falta o
  texto descritivo.
- **(c) texto fixo:** nenhum. ~3.400 palavras (A) a ~13.000 (B, com anexos) a versionar ou herdar do modelo.
- **(d) campos manuais:** controle de revisão, cronograma (meses/ações), quantidades do kit, RQE, termo,
  assinatura. Formulário na tela ou campo em branco no documento.
- **Códigos SOC dos exames** (`(0295)` etc.): o vocabulário `exames.yaml` não tem. Se o PCMSO gerado tiver
  de casar com o SOC, é campo novo no vocabulário `[A DECIDIR]`.

---

## 5. Proposta de arquitetura — para decisão

Ponto central: **preencher o modelo Word da clínica** ou **montar do zero**.

### Opção 1 — Montar do zero (python-docx, como matriz/memorial/relatório ASO)

Texto fixo versionado no repo (YAML/Markdown por seção, cada parágrafo com o item da NR-07 que o sustenta).

- **A favor:** mesma pilha e mesmos testes dos três documentos que já existem; texto fixo auditável por
  item normativo (alinha com a exigência de rastrear linha → norma do CLAUDE.md); sem dependência de
  arquivo binário de 35 MB; LibreOffice/Word renderizam igual ao que já é validado (`VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`).
- **Contra:** reescrever ~3.400–13.000 palavras e a diagramação (capa, cabeçalho por página, sumário); o
  documento não fica igual ao da clínica e as médicas revisam um formato novo; toda edição que a clínica
  fizer no Word dela não chega ao app — manutenção dupla, e o texto diverge com o tempo.

### Opção 2 — Preencher o modelo Word com marcadores em todos os campos (docxtpl/Jinja)

Uma cópia do modelo ganha `{{ empresa.cnpj }}`, `{% for ghe in ghes %}`... e o app renderiza.

- **A favor:** sai idêntico ao que a clínica entrega; texto fixo e estilo mantidos pela clínica, no Word.
- **Contra:** marcar o modelo é trabalho manual e frágil (o Word quebra `{{...}}` em vários *runs*); o
  laço por GHE com tabelas dentro de tabela é o ponto mais frágil do docxtpl; a cada revisão do modelo pela
  clínica, remarcar; o binário de 35 MB no git (cada versão soma 35 MB ao histórico — exigiria Git LFS ou
  modelo fora do repo); teste de regressão vira comparação de DOCX.

### Opção 3 — Híbrida: o modelo da clínica é a casca, o app gera só os blocos variáveis (recomendada)

O modelo Word entra com **poucos marcadores de posição** (um parágrafo-âncora por bloco: `IDENTIFICACAO`,
`CONTROLE_REVISAO`, `BLOCOS_GHE`, `CRONOGRAMA`) e campos simples de capa/cabeçalho. O app abre o modelo com
`python-docx`, substitui as âncoras por conteúdo que ele mesmo monta (o mesmo código de tabela da matriz e
do relatório ASO) e salva. Texto fixo, capa, estilos e imagens ficam com a clínica.

- **A favor:** o bloco por GHE — 40–68% do documento e a parte (a)+(b) — sai do motor, com o mesmo código e
  os mesmos testes; a parte (c) continua sendo da clínica, no Word, sem reescrita; trocar o modelo exige só
  recolocar 4–6 âncoras, não remarcar o documento inteiro; o PCMSO sai no formato que as médicas já revisam.
- **Contra:** ainda depende do binário do modelo (mesmo problema de peso — resolver comprimindo as
  imagens, `[A MEDIR]` quanto cai, ou guardando o modelo fora do git e informando o caminho/upload na tela);
  o texto fixo não fica rastreável por item da NR-07 dentro do repo; a fidelidade de estilo da tabela
  inserida ao estilo do modelo precisa ser conferida no smoke visual.

### Fatiamento sugerido (qualquer opção, começa pelo que já existe)

1. **Bloco por GHE em DOCX avulso** — riscos (relatório ASO + agravo D-ARQ-93), exames/momentos/periodicidade
   (matriz). A clínica cola no Word dela: é o mesmo passo que as notas "Incluir no word do PCMSO" pedem hoje.
   Formato do modelo B (por GHE). Gabarito: R70 P09 × matriz R70 (2026). P12 Viverde e P14 R78 (modelo A,
   mas trios com PGR) servem só para conferir a origem PGR → descrição/agravo. Não depende do Mauá.
2. **Extração de dados da empresa e da descrição de GHE/cargo do PGR** (CNPJ, endereço, CNAE, grau de risco)
   — classe (b), por família de PGR, sob o gate de D-ARQ-65.
3. **Casca** — Opção 1 ou 3, decidida depois de medir o modelo Mauá (igual ao B? quanto pesa e por quê).
4. **Campos (d)** na tela: controle de revisão, cronograma, kit, responsável. Revisão das médicas igual à da
   matriz: elas corrigem o DOCX gerado, a correção volta como entrada.

**Recomendação:** Opção 3 com a fatia 1 primeiro. Razão: a fatia 1 entrega a parte cara do PCMSO sem decidir
casca, e a decisão de casca fica com o dado que falta (o Mauá). Se o Mauá for modelo B e tiver o peso em
imagem, a Opção 3 com imagem recomprimida resolve; se a clínica quiser texto fixo auditável por item da
NR-07, a Opção 1 vira a escolha e a fatia 1 é reaproveitada inteira.

---

## 6. Normas

- **NR-07:** cópia de trabalho `normas/nr-07-atualizada-2022-1 .pdf` (39 p.), última alteração listada:
  Portaria MTP n.º 567, de 10/03/2022. **Vigente: o Diovanni confirmou em 13/10/2026 que as normas da pasta
  estão na última versão** (antes, 06/10/2026 no `normas/README.md`). O container não alcança `www.gov.br`
  (política de rede, proxy 403), então a conferência desta sessão é essa declaração, não leitura do portal.
- Itens que o PCMSO tem de conter (NR-07 7.5.4): a) agravos por risco do PGR; b) planejamento de exames
  conforme anexos; c) critérios de interpretação e condutas; d) conhecido pelos médicos examinadores;
  e) relatório analítico (7.6.2). Os itens a e b são o bloco por GHE.
- **Divergência no texto fixo:** a capa e o "Objetivo" do modelo A, e o texto "Norma Regulamentadora - NR7"
  do R70 (modelo B), citam "Portaria SEPRT n.º 6.734, de 10/03/2020"; a cópia vigente registra "de 09 de
  março de 2020" e lista ainda SEPRT 1.295/2021, 8.873/2021 e MTP 567/2022. Vale para qualquer opção em que
  o app reproduza ou revise o texto fixo.

---

## 7. LGPD — `scripts/varrer_acervo_lgpd.py` sobre os 24 arquivos

`python -m scripts.varrer_acervo_lgpd --pasta <cópia dos 24>`: **24 de 24 extraídos**, 4 min 18 s.

- **Nenhuma relação de trabalhadores.** Os marcadores de trabalhador (17 arquivos) são todos texto
  normativo ("constar em ASO", "prontuário médico individual").
- **CPF com DV válido: 2 distintos, só no P07 (T65)** — página de assinatura eletrônica: o representante
  da empresa signatário e a conta da clínica que criou o documento, com IP. Dado pessoal comum de
  signatário (LGPD art. 5º I), não de trabalhador sob vigilância.
- E-mails: 5 distintos em 12 arquivos (institucionais da clínica e 1 da construtora). Metadata de
  autoria: 9 nomes de pessoa.
- **Não pego pelo instrumento:** P23 (saída de gerador anterior) traz nomes próprios e telefones de
  profissionais da obra lidos como "cargo". Não é dado de saúde, mas é dado pessoal; decisão sobre manter
  o arquivo no acervo é do Diovanni.

---

## 8. Pendências desta medição

- Modelo Mauá Plateu d'Or 28.09.26: igual ao B? onde estão os 35 MB? — `[A MEDIR]` quando subir.
- Conferência exame a exame PCMSO × matriz do R70 (modelo B) — `[A MEDIR]` com leitor de tabela, não `pdftotext`.
- Correções do `PAREAMENTO_ACERVO.md` listadas em §1.1 — aguardam decisão.
