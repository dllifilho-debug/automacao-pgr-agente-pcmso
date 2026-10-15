# Briefing — estrutura do PCMSO Mauá/Plateau D'Or como modelo do documento gerado pelo app

`[MEDIDO — 14/10/2026, sobre main 86f7115]` Levantamento para a sessão que decidir gerar o PCMSO no
app. Nada daqui foi implementado.

## O arquivo

`matrizes_originais/PCMSO(ATUALIZAÇÃO)MAUÁ PARTICIAPÇÕES ESTRUTURADAS SA PLATEUDOR 28.09.26.rtf.doc`
(PR #493). Apesar do `.doc`, é RTF: 36.572.860 bytes. Convertido com
`soffice --headless --convert-to docx` vira um `.docx` de 996.218 bytes, com o mesmo conteúdo: o RTF
guarda as imagens em hexadecimal. O modelo do app deve ser o `.docx`, não o RTF.

Forma: 1 seção, A4 retrato, margens laterais de 1,3 cm. 314 parágrafos, todos no estilo `Normal`
(nenhum estilo de título), 89 tabelas e 25 imagens. Quase todo o texto mora dentro de tabelas de 1
coluna; os títulos são numerados à mão, com campos `TC` para o índice. O índice da capa sai vazio
na conversão (campo não atualizado).

## Mesmo modelo de 2026 do Seconci-GO

Comparadas as linhas de 40 caracteres ou mais com os PCMSOs em PDF do acervo:

| Parte do Mauá | PCMSO R70 22.09.26 | Os outros 7 PCMSOs (2024–2026) |
|---|---|---|
| Seções 3–10, texto fixo (507 linhas) | 100% | 20% |
| Seções 11–16 e anexos (159 linhas) | 98% | 6–7% |
| Blocos por GHE (127 linhas) | 19% | 17–60% |

O texto fixo é o do modelo Seconci 2026, idêntico ao do PCMSO R70 (que tem matriz pareada no
acervo). Os PCMSOs anteriores seguem outro modelo.

## Par PGR ↔ PCMSO no acervo

`PGR_-_plateau Dor_assinado rev 03.pdf` (55 págs., 15/08/2026, mesma razão social e CNPJ, obra
Plateau D'Or) é o PGR deste PCMSO. O PGR tem `INVENTÁRIO DE RISCO GHE 01` a `GHE 20` (o 19 escrito
`GHE: 19`) e, na pág. 36, um segundo `GHE 01` com setor Contabilidade, que o PCMSO numerou como GHE 21.
É o mesmo erro de numeração do Soft Connect, mas com o número repetido no fim e sem lacuna:
`[A MEDIR — o que avaliar_numeracao_ghe faz com ele]`. Do PGR vêm:
- a descrição de cada cargo: 41 das 43 achadas no PGR (60 primeiros caracteres);
- o nome do perigo: 79 de 143 linhas.

O agravo da tabela de perigos é do Seconci, não o verbatim do PGR: só 14 de 143 achados no PGR. É
outro texto, diferente do `agravo` que o app já guarda (D-ARQ-93).

## Estrutura, em ordem

| # | Seção | Origem do conteúdo |
|---|---|---|
| — | Cabeçalho de página: logo, "PCMSO Programa de Controle Médico…", data | data do documento |
| — | Capa: logo, "PCMSO", razão social, data, "Versão: 1" | envelope |
| — | Índice | campo do Word |
| 1 | Identificação da Empresa: empresa (razão social + obra), endereço, CNPJ, CEP | PGR / envelope |
| 2 | Controle de revisão: data, revisão, considerações | operador |
| 3–8 | NR-7, Objetivo, Diretrizes, Planejamento, Desenvolvimento, Responsabilidades | fixo |
| 9 | Exame médico ocupacional: 9.1 ASO, 9.2 exames, 9.3 periodicidade laboratorial (Quadros 1 e 2 do Anexo I da NR-7 **em imagem**), benzeno, cancerígenos, radiações ionizantes, altura, espaço confinado, motoristas, NR-32, 9.4 audiometria (Anexo II), 9.5 RX (Anexo III), 9.6 espirometria, 9.7 gestantes, 9.8 manipuladores de alimento, 9.9 calor, 9.10 riscos psicossociais (SRQ-20) | fixo |
| 10 | Documentos: prontuário, relatório analítico | fixo |
| — | **"Unidade: <obra>" e um bloco por GHE (21 blocos)** | **app** |
| 11 | Programa de vacinação (salas de vacina em imagem) | fixo |
| 12 | Programa de conscientização em saúde preventiva (art. 169-A da CLT) | fixo |
| 13 | Cronograma de atividades | fixo |
| 14 | Lista de suprimentos de emergência | fixo |
| 15 | Termo de compromisso, com a razão social | envelope |
| 16 | Anexos: questionário OMS de epilepsia, fluxos de conduta, fluxograma de acidente com material biológico; assinatura do médico responsável (nome, CRM, NIT, CPF, especialidade, RQE) | fixo + cadastro do médico |

### Bloco por GHE (a parte que o app gera)

1. Tabela 1×1 — `Setor: GHE NN - <nome>` e linha "-".
2. Tabela de 3 colunas — para cada cargo, `Cargo: <nome>` e a descrição; em seguida,
   `Perigo / Fator de Risco | Grupo | Descrições dos perigos e possíveis lesões ou agravos à saúde`.
   Variações no próprio modelo: nos GHE 17 e 21, cargos e perigos estão em tabelas separadas; nos GHE
   11, 12 e 13, a 1ª linha da tabela sai vazia.
3. Tabela de 7 colunas — `Exames | ADMISSÃO | APÓS ADM. | PERIÓDICO | RET. TRAB | MUD. FUNÇ. |
   DEMISSÃO`. Exame com código Seconci entre parênteses, por exemplo `(0281) Audiometria` e
   `(0295) Exame Clínico`; o periódico é escrito em meses ("12 meses", "6 meses", "24 meses"), os
   outros momentos em `X` ou `-`.

Mapeamento para o motor: `Momento` tem ADM, PER, MR, RT e DEM. "APÓS ADM." não tem par (sai `-`
em todas as linhas medidas) e "MUD. FUNÇ." é o MR. O código Seconci não existe em `exames.yaml`.

## Defeitos do próprio modelo (corrigir antes de usar)

- Termo de compromisso (seção 15) com a razão social de outra empresa ("SPE INCORPORAÇÃO H6 LTDA"):
  sobra de um PCMSO anterior. O app tem de preencher esse campo.
- Nome da empresa em três formas: "ESTRUTURAS S/A" (capa), "ESTRUTURADAS S/A" (seção 1) e
  "Estruturadas LTDA" (PGR). Endereço do PCMSO (Rua T 65) diferente do endereço do PGR.
- "membros 37uperiors" (2 ocorrências, na tabela de perigos): "superiores" corrompido.
- Numeração: dois itens 9.3.4 (cancerígenos e radiações ionizantes); o texto da seção 8 remete aos
  fluxos como 11.2–11.4, mas eles estão em 16.1–16.3.
- Lei citada como "15.377/2026" em três lugares e "15337" num quarto.
- Texto de NR transcrito: itens da NR-32 (serviços de saúde) inteiros num PCMSO de obra, e
  Quadros 1 e 2 do Anexo I da NR-7 em imagem, que não se atualizam com a norma.

## Normas a conferir na fonte oficial antes de congelar o texto fixo

- NR-07 e Anexos I, II e III; NR-32; NR-35 item 35.4.4; NR-33: Gov.br/MTE, Normas
  Regulamentadoras Vigentes. Conferir vigência e eventuais revisões em consulta pública.
- Art. 169-A da CLT, incluído pela "Lei nº 15.377, de 2 de abril de 2026" segundo o modelo:
  conferida no Planalto pela captura do Diovanni (15/10/2026): Lei nº 15.377, de 2 de abril de 2026, DOU 6/4/2026. Fora da NR, e o número aparece de duas formas no próprio documento.

## Pontos de decisão (do Diovanni)

1. **Escopo do documento gerado.** (a) Só os blocos por GHE, para colar no modelo do Seconci; (b) o
   PCMSO inteiro, com o texto fixo das seções 3–16 guardado como modelo `.docx` no repositório e o
   app preenchendo identificação, revisão, blocos por GHE, termo e assinatura.
2. **Texto fixo.** Congelado como está, ou revisado agora (defeitos acima e NR-32 numa obra), já
   que vira a saída de todos os PCMSOs.
3. **Agravo da tabela de perigos.** O do PGR (verbatim, D-ARQ-93, já guardado), ou o texto padrão do
   Seconci por perigo. Este exige um vocabulário novo.
4. **Código Seconci dos exames.** Entra em `exames.yaml`, como campo de exibição, ou o PCMSO sai sem
   código.
5. **Relação com a matriz RQ.61** (D-ARQ-73). O PCMSO substitui a matriz assinada, ou os dois saem
   juntos.

## Gabarito para a sessão de implementação

O par PGR Plateau rev 03 ↔ este PCMSO dá conferência GHE a GHE (exames, momentos e periodicidade)
entre o que o app gera e o que a médica assinou. Rodar o app no PGR Plateau antes:
`[A MEDIR — rota e número de GHE aprovados]`.

## Decisões do Diovanni (14/10/2026)

1. **Escopo: PCMSO inteiro.** O texto fixo das seções 3–16 fica guardado como modelo `.docx` no
   repositório; o app preenche identificação, controle de revisão, blocos por GHE, termo de
   compromisso e assinatura.
2. **Texto fixo: corrigir os defeitos listados acima, marcados**, para o Diovanni ver o que mudou.
   Forma proposta: cada correção realçada em amarelo no modelo, mais uma lista "o que mudou e por
   quê"; depois da aprovação, o realce sai e o modelo congela. **NR-32 fica** — o Seconci é serviço de
   saúde e tem a NR-32 como base —, marcada só como **sugestão de alteração** (comentário no Word;
   ideia em aberto: condicionar ao risco biológico no PGR).
3. **Agravo: o do PCMSO das médicas, não o do PGR** — agravo à saúde é matéria médica; os engenheiros
   costumam falhar nesse item. Proposta a decidir: dicionário perigo → agravo extraído dos PCMSOs das
   médicas no modelo 2026 (Mauá, R70), casado pelo agente que o app já resolve (não pelo texto do
   PGR); perigo fora do dicionário sai com o agravo do PGR marcado "do PGR — conferir".
   `[MEDIDO — 14/10/2026, PCMSO Mauá]` 143 linhas, 54 perigos distintos: 45 com uma descrição só,
   9 com variação (a maioria erro do modelo: "Perda etergen induzida pelo ruído" ao lado de "Perda
   auditiva…", "membros 37uperiors", "Fraturas, luxações e morte" × "Óbitos, Fraturas e luxações") —
   a forma limpa de cada um é decisão do Diovanni.
4. **Código Seconci: manter**, no padrão "(0295) Exame Clínico", como campo de exibição em
   `exames.yaml`. Não há tabela oficial conhecida; a lista sai dos PCMSOs do acervo.
   `[MEDIDO — 14/10/2026]` 25 códigos distintos nos 8 PCMSOs em PDF do acervo + Mauá (0029, 0071,
   0102, 0113, 0116, 0133, 0281, 0289, 0295, 0296, 0300, 0364, 0391, 0467, 0531, 0562, 0658, 0693,
   0836, 0863, 0951, 1075, 1086, 1181, 1415). O texto dos PDFs embaralha as colunas: o par
   código ↔ exame `[A MEDIR — por tabela, PDF a PDF]`. Exame sem código conhecido sai sem código e
   com aviso, nunca com código inventado.
5. **Matriz RQ.61 e PCMSO saem juntos**, na mesma rodada do app e da mesma fonte — exames iguais
   por construção; as médicas conferem e validam os dois. Recomendação aceita: uma etapa só
   (não "validar a matriz, subir de novo e gerar o PCMSO"). Correção de regra volta como entrada e
   regenera os dois; correção pontual de um PGR, a médica faz nos dois. Se as pontuais ficarem
   frequentes, avaliar "subir a matriz corrigida → regenerar o PCMSO".

## Ordem combinada

1. Modelo `.docx` corrigido, com as marcações, para revisão do Diovanni; registro das 5 decisões
   numa D-ARQ nova (número lido do disco na sessão).
   **Feito em 15/10/2026 (D-ARQ-96), aguardando revisão:** `agente_medico/superficie/modelos/pcmso_seconci_2026_revisao.docx`,
   lista em `MODELO_PCMSO_CORRECOES.md`.
2. Dicionário de agravos (com as 9 variações para decisão) e tabela de códigos.
3. Geração do PCMSO junto com a matriz, conferida no par PGR Plateau rev 03 ↔ PCMSO Mauá.

## Pendência anterior (Soft Connect)

Rodar o PGR Soft Connect15 v04 no app depois do deploy do PR #497 e conferir: GHE 09 com RX anual
e a pendência bloqueante em vermelho; 21 GHE na matriz; download liberado. PENDENCIAS,
DT-(sessão `claude/admiring-maxwell-dhcgko`)-01. **Conferido em 15/10/2026: os três passam** (rodada 3 na DT).
