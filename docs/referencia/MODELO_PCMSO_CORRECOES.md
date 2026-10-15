# Modelo do PCMSO (Seconci 2026) — o que mudou e por quê

`[MEDIDO — 15/10/2026, branch claude/eager-newton-qw5a0u sobre main bb9dddf]` Etapa 1 da ordem combinada em
`BRIEFING_MODELO_PCMSO_MAUA.md`; decisão em D-ARQ-96. **Para revisão do Diovanni** — nada aqui foi aprovado.

- Modelo de revisão: `agente_medico/superficie/modelos/pcmso_seconci_2026_revisao.docx` (67 páginas no LibreOffice).
- Gerador: `python -m scripts.gerar_modelo_pcmso <maua.docx>`, sobre o `.docx` que o
  `soffice --headless --convert-to docx` faz do RTF do acervo. `--limpo` grava `pcmso_seconci_2026.docx` sem realces nem
  comentários — o modelo congelado, depois da aprovação.
- O gerador para sem gravar se algum texto esperado não estiver no documento, ou estiver em número diferente de
  parágrafos: as correções são do texto deste PCMSO, não regras genéricas.

## Convenção no `.docx`

| Marca | Significa |
|---|---|
| Amarelo + comentário `C-NN` | correção de texto (47 trechos, todos com comentário) |
| Só comentário `S-NN` | sugestão: o texto ficou como estava |
| Turquesa `{{NOME}}` | campo que o app preenche (lista em `CAMPOS` do gerador) |

O amarelo original do Seconci (52 trechos: período e meses do cronograma, empresa do 13.1, "NOV/26", "Inserir Tema",
"MÊS/XX") foi retirado para não se confundir com as correções — ver S-08.

## Correções (`C-NN`)

| ID | Onde | Antes → depois | Fonte |
|---|---|---|---|
| C-01 | 13.1 (empresa e local) e 15 (termo) | "SPE INCORPORAÇÃO H6 LTDA" → `{{RAZAO_SOCIAL}}` / `{{OBRA}}` | sobra de um PCMSO anterior (briefing) |
| C-02 | 12, passo 6 | "Lei 15337" → "Lei nº 15.377/2026" | o próprio documento escreve 15.377 três vezes; **número e data `[A CONFERIR — Planalto]`** |
| C-03 | 6, alínea c) | remissões 11.2/11.3/11.4 → 16.1/16.2/16.3 | os fluxos estão nos anexos 16.1–16.3 |
| C-04 | 9.3.6, 9.3.7, 9.3.8, 9.3.9.5 | "(Anexo 11.1)" → "(Anexo 16)" (3×); "(Anexo 11.5)" → "(Anexo 16.4)" | questionário OMS em 16; fluxograma de acidente biológico em 16.4 |
| C-05 | 9.3.4 em diante | dois 9.3.4: Radiações Ionizantes → 9.3.5; altura 9.3.6; espaço confinado 9.3.7; motoristas 9.3.8; NR-32 9.3.9 e 9.3.9.1–9.3.9.5 | numeração |
| C-06 | 9.3, "caberá à organização", alínea c) | cópia do parágrafo do laboratório → "encaminhar o empregado à Previdência Social, quando houver afastamento … superior a 15 (quinze) dias …" | NR-07 7.5.19.5 c) |
| C-07 | 9.2 | "VI. No Exame Demissional" → "V." | sequência I–IV, VI |
| C-08 | 9.2 | "centro e trinta e cinco" → "cento e trinta e cinco" | grafia; **o erro está no próprio texto do MTE** (NR-07 7.5.11) |
| C-09 | 9.3 a) | "levantamento preliminar de o PGR" → "do PGR" | NR-07 7.5.12 a) |
| C-10 | 9.4, Anexo II 3.2.1.1 | fim corrompido ("…decibéis).ienos constantes das alíneas ma …") removido | NR-07 Anexo II 3.2.1.1 |
| C-11 | 9.5, nota do PNOS | "**" → "***"; "fluído" → "fluido"; "não se emitir" → "não ser emissor de"; "defeitos tóxicos além da inflamação" → "efeitos tóxicos além de inflamação" | NR-07 Anexo III, nota *** do Quadro 2 |
| C-12 | 9.9 | "item 4.2.3 da NR 9" → "item 4.2.3 do Anexo III da NR-09"; "item 4 do Anexo da NR-09" → "do Anexo III" | NR-09 Anexo III 4.2.3 e 4.2.3.1 |
| C-13 | 8, item 2 | parágrafo sem letra → "i)"; "J)" → "j)" | sequência a)–h) |
| C-14 | 3 | "Portaria SEPRT n.º 6.734, de 10/03/2020" → "de 09/03/2020" | tabela de publicação da NR-07 (DOU 13/03/2020). **A própria NR-07 escreve "10 de março" na linha "Redação dada" — decisão do Diovanni** |
| C-15 | vários | "Química" → "Químicas" (9.3.4); "do tipo do tipo" → "do tipo" (3×); "diagnostico" → "diagnóstico" (3×); `trabalhador">` → `trabalhador."` (NR-35 35.4.4.1); "empegados" → "empregados" (10.2); "iscos" → "riscos" (2×, 16.3); "imunoglobina" → "imunoglobulina" (16.3) | grafia; NR-35 conferida |

Normas conferidas nas cópias de `normas/` (vigência declarada pelo Diovanni em 13/10/2026, `normas/README.md`): NR-01
1.5.4.4.6, NR-07 (corpo e Anexos II, III e V), NR-09 Anexo III, NR-18 18.17.1, NR-33 33.2.2, NR-35 35.4.4. O Gov.br/MTE
e o Planalto não abriram: a rede do ambiente bloqueia os dois hosts.

## Correções sem marca (não há onde pôr o realce)

| ID | O quê |
|---|---|
| K-01 | 11 títulos com `TC "título"` **visível** antes do título (ex.: `TC "4 - OBJETIVO"4 - OBJETIVO`): defeito da conversão RTF → `.docx`, não do original. Viraram campos TC de novo (ocultos). |
| K-02 | Blocos por GHE (65 tabelas) trocados pelo campo `{{BLOCOS_GHE}}`, logo após "Unidade: `{{OBRA}}`"; 55 entradas de GHE e cargo saíram do índice. Os defeitos que moravam nesses blocos ("membros 37uperiors", "Perda etergen", "etergents de gesso/chapas") saem com eles; o agravo vai para o dicionário da etapa 2. |
| K-03 | Campos `{{...}}` na capa, nos cabeçalhos de página, nas seções 1 e 2, no cronograma (período e os 13 meses) e na assinatura. Resolve o nome da empresa em três formas e o endereço do PCMSO diferente do PGR (briefing): os dois passam a vir do envelope. |
| K-04 | O Word atualiza os campos ao abrir (`updateFields`): o índice se refaz com os GHE gerados. |

## Sugestões (`S-NN`, texto intacto)

| ID | Onde | Sugestão |
|---|---|---|
| S-01 | 9.3.9 (NR-32) | Fica (decisão de 14/10/2026). Em aberto: condicionar a seção ao risco biológico no PGR. Vai no comentário do C-05 do título. |
| S-02 | 9.3.1 e 9.3.2 | Quadros 1 e 2 do Anexo I da NR-07 em imagem, que não acompanham a norma: remissão à NR-07 vigente ou tabela de texto conferida. |
| S-03 | 6 | "PGR/PCMAT" → "PGR": o PCMAT só vale para obra iniciada antes da NR-18 revisada (18.17.1). |
| S-04 | 9.3, observações | "A monitoração … ficará a critério do PGR da empresa" contradiz a NR-07: o PGR classifica o risco, o médico responsável define os exames (7.5.12, 7.5.18). Redação a decidir. |
| S-06 | 13 | "(OBS: ADENDO NÃO PRECISA DESSE ITEM)" é nota de edição visível: tirar do texto e virar regra do app. |
| S-07 | 16.1 | **A figura do "Fluxo geral" é a mesma do 16.2** (fluxo do Anexo I, Quadros 1 e 2) — mesmo arquivo de imagem. O fluxo geral não está no documento; falta a figura do Seconci. |
| S-08 | 13.2 | Datas e temas das palestras continuam manuais (o amarelo original foi retirado). Decidir se o app preenche. |

S-05 (índice sem as seções 1 e 11, e "SALAS DE VACINAS" duas vezes) não foi marcado no `.docx`: o índice é campo do Word
e se refaz ao abrir; corrigir pede campos TC novos — decidir junto com a etapa 3.

## Fora desta etapa

- Formato dos blocos por GHE (tabelas de cargo/perigo e de exames): etapa 3. O RTF original no acervo continua sendo a
  referência de leiaute.
- Dicionário de agravos (com as 9 variações) e tabela de códigos Seconci: etapa 2.
