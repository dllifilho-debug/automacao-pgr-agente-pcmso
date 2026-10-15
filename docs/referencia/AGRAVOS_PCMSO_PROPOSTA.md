# Dicionário de agravos do PCMSO — medição e proposta (etapa 2)

`[MEDIDO — 15/10/2026, branch claude/eager-newton-qw5a0u sobre main 91a20c1]` D-ARQ-96 cl.3: o agravo da tabela
"Perigo / Fator de Risco | Grupo | Descrições dos perigos e possíveis lesões ou agravos à saúde" vem dos PCMSOs das
médicas no modelo 2026, casado pelo agente que o app resolve; fora do dicionário, o agravo do PGR marcado "do PGR —
conferir". As decisões estão no fim.

**Aprovado pelo Diovanni em 15/10/2026, pela recomendação técnica dada na sessão. Implementado no mesmo dia:**
`vocabulario/agravos.yaml` (23 agentes, 22 chaves de perigo sem agente) e `superficie/agravos_pcmso.py`. Cobertura
medida nas duas fontes: Mauá 131 de 140 linhas (94%), R70 315 de 378 (83%); o resto sai com o agravo do PGR para
conferir — os sinônimos de agente com exame (decisão 6, ainda a medir) e produtos de FDS. Como ficou cada decisão:
1. curto; 2. PAINPSE + extra-auditivos; 3. as 9 formas, sílica com silicose `[INTERPRETADO]`; 4. chave de perigo sem
agente — nenhum termo pode resolver num agente (o carregamento recusa); 5. um agravo psicossocial único; 6. não
implementado: medir os sinônimos de vibração mão-braço e sílica nos PGRs pareados; "Radiação não ionizante" vira
pendência ao elaborador, sem casar com UV/IR; 7. "(0113/0102)" numa linha, a gravar com a etapa 3. Componentes de FDS
do cimento recebem o agravo do produto (precedente do R70).

## Fontes e método

| Fonte | Extração | Linhas de perigo | Textos de perigo distintos | GHE |
|---|---|---|---|---|
| PCMSO Mauá/Plateau D'Or 28.09.26 (RTF → `.docx`) | células das tabelas de 3 colunas dos blocos por GHE | 140 | 51 | 21 |
| PCMSO R70 (adendo) 22.09.26, PDF assinado | `pdftotext -layout`, colunas pela posição do cabeçalho e do grupo; continuação de página tratada | 378 | 66 | 20 |

O briefing de 14/10 registrou 143 linhas e 54 perigos no Mauá. A medição de hoje no `.docx` dá 140 e 51, e todas as
linhas de 3 colunas com grupo foram contadas. O método de 14/10 não foi registrado; as 9 variações batem (abaixo).
Em 2 linhas do R70 o parser juntou dois perigos numa célula ("Objetos cortantes … Pisos, passagens …") e quebrou
"Liderança" em "L": ruído de extração, que não muda nada abaixo.

Resolução pelo app: `resolver_termo` (só casamento EXATO conta) sobre o vocabulário de `agentes.yaml` atual.

## Achado 1 — as duas fontes não usam o mesmo texto

O agravo **não é um texto padrão do Seconci**: Mauá e R70 escrevem textos diferentes para o mesmo agente. O Mauá é
curto ("Perda auditiva induzida pelo ruído."); o R70 é descritivo, quase sempre um parágrafo. Exemplos:

| Agente | Mauá | R70 |
|---|---|---|
| ruído | Perda auditiva induzida pelo ruído. (15×) | A exposição ao ruído excessivo pode apresentar diversos sintomas no organismo como irritabilidade, ansiedade, dor de cabeça, zumbido, tontura, estresse, falta de concentração, perda de memória, dificuldades no entendimento da fala e de comunicação, insônia, doenças cardiovasculares e, em um estágio mais gravoso, perda auditiva irreversível (15×, mais 3 variações) |
| trabalho em altura | Fraturas e luxações. (10×) e 4 variações | Múltiplas lesões possíveis, na cabeça é comum que ocorra fratura craniana deprimida, contusão cerebral e hemorragia intracraniana; no tórax … (12×) |
| esforço físico | Prejudicar a coluna, músculos, nervos e ossos de diversas partes do corpo. (3×) | Lesões no seu sistema musculoesquelético, dores intensas na coluna, na região lombar, nos ombros, nos braços e nos pulsos, incidência de Ler e Dort. (10×) |
| queda de materiais | Fraturas, lesões ou óbito. | Hemorragias, perfuração de órgãos internos, lesões permanentes, deficiência física, incapacitantes (18×) |
| vibração de corpo inteiro | Problemas no sistema circulatorio, urologico, ortomuscular e nervoso central. | Efeitos adversos na coluna vertebral, devido à exposição à VCI, como lombalgia, degeneração precoce da região lombar e hérnia de disco, dores musculares, náuseas, entre outros. |
| poeira de gesso ("Sulfato de cálcio") | Irritação das vias respiratórias, ressecamento e irritação da pele. | texto do **cimento** ("A exposição ao pó de cimento …"): no R70 o sulfato de cálcio é componente da FDS do cimento |

No R70 os componentes de uma FDS (aluminato tricálcico, silicatos, sulfato de cálcio, óxido de cálcio…) repetem o
agravo do **produto**. Chavear pelo agente devolveria o agravo do componente, não o do produto.

## Achado 2 — o agente cobre menos da metade das linhas

| Fonte | Linhas resolvidas (EXATA) | Cobertura |
|---|---|---|
| Mauá | 61 de 140 | 44% |
| R70 | 87 de 378 | 23% |

Agentes que casaram: acetato de etila, acetona, aluminato tricálcico, cimento Portland, domissanitários, esforço físico,
ferro-aluminato de cálcio, MEK, poeira de gesso, poeira de madeira, postura inadequada, queda de materiais, ruído,
sílica, silicatos di/tricálcico, trabalho em altura, vibração de corpo inteiro.

O que fica de fora (370 linhas, 86 formas), pela frequência nas duas fontes:

| Linhas | Perigo (forma normalizada) | Grupo | Agravo nas fontes |
|---|---|---|---|
| 184 | 9 fatores psicossociais do R70 (relações interpessoais, comportamentos ofensivos, conflitos família-trabalho, demandas, influência e desenvolvimento, liderança, satisfação, significado e compromisso, valores) — 24 de "relações interpessoais" contando o Mauá | Ergonômicos | "Transtornos mentais." (em 2 deles: "Transtorno mentais; LER … e DORT …") |
| 19 | queda de mesmo nível | Acidente | Fraturas e escoriações. |
| 18 | piso irregular ou em desnível | Acidente | Fraturas, lesões diversas, inclusive com possibilidade de serem incapacitantes. |
| 17 | arranjo físico inadequado (perfuração) | Acidente | Infecções bacterianas, lesões dermatológicas e até mesmo consequências mais graves. |
| 15 | radiação não ionizante | Físico | Exaustão ao calor; Sudorese; Desidratação. Nos olhos podem causar ceratites, conjuntivites e cataratas. |
| 14 | poeira total e sílica livre | Químico | Quando há ação de substâncias irritantes, como a poeira, … chiado no peito, falta de ar e tosse. |
| 6 | máquinas e equipamentos | Acidente | Fraturas, cortes, perfurações e amputação de membros. |
| 5 cada | objetos cortantes/perfurocortantes; intempéries; choque elétrico | — | ver variações |
| 4 | vibração localizada (mão-braço) | Físico | síndrome dos dedos brancos … |
| ≤ 3 | 70 formas restantes | — | — |

## Achado 3 — formas que hoje não chegam ao agente que tem exame

Não é agravo, é emissão de exame; fica registrado para decisão à parte (muda regra, D-ARQ-22). Nos dois PCMSOs, estas
formas de PGR não resolvem em `agentes.yaml`:

- "Vibração Localizadas (Mão- Braço)" (R70, 4 GHE): existe agente de vibração de mãos e braços (D-ARQ-16).
- "Poeira total e Sílica livre" (R70, 14 GHE) e "Poeiras respirável / sílica" (Mauá, 2): o agente `silica` existe.
- "Radiação não ionizante" (R70, 15 GHE; também no Soft Connect15 v04, expander de 14/10): existe `radiacao_uv_ir`
  (R-VIS-01). Se o PGR não disser UV/IR (solda), o casamento é interpretação.

Medir o efeito desses aliases nos PGRs pareados antes de decidir.

## As 9 variações do Mauá — forma limpa proposta

| Perigo | Formas no Mauá (vezes) | Proposta |
|---|---|---|
| Choque elétrico | "Queimaduras cutâneas, Lesões a órgãos internos e outros tecidos brandos, arritmias e parada respiratória." (3); idem com "outrostecidos" (1); "Queimaduras, e lesões múltiplas." (1) | Queimaduras cutâneas, lesões de órgãos internos e de outros tecidos moles, arritmias e parada respiratória. |
| Queda de mesmo nível | "Fraturas e escoriações." (17); "Fraturas, escoriações e perfuração." (1) | Fraturas e escoriações. |
| Queda em altura | "Fraturas e luxações." (10); "Fraturas, luxações e morte." (3); "Óbitos, Fraturas e luxações." (1); "Lesões diversas, Traumatismo e morte." (1) | Fraturas, luxações e morte. — o desfecho fatal é o motivo da NR-35 |
| Postura de pé por longos períodos | "Lombalgias e fadigas." (3); "Dores lombares ou lombalgias que podem desenvolver graves lesões da coluna." (2); "Cansaço e dores musculares." (1) | Lombalgia, fadiga e dores musculares. |
| Postura sentada por longos períodos | "Inflamações nas mãos, braços, ombros, dores nas costas, problemas circulatórios." (2); "Lombalgias, dores nos membros 37uperiors e inferiores" (1) | Lombalgia, dores nos membros superiores e inferiores e problemas circulatórios. |
| Intempéries | "Insolações, desidratações." (3); "Insolações, desidratações, descargas atmosféricas." (2) | Insolação, desidratação e lesões por descarga atmosférica. |
| Ruído | "Perda auditiva induzida pelo ruído." (15); "Perda etergen induzida pelo ruído." (1) | Perda auditiva induzida por ruído (PAIR). — ver decisão 2 sobre os efeitos extra-auditivos do R70 |
| Poeiras respirável / sílica | "Irritações nos olhos e pele, e danos ao sistema respiratório." (1); "Podem afetar as vias respiratórias e atingir o pulmão, ocasionando desde crises alérgicas, como a rinite, até o desenvolviment o de asma ocupacional, e pneumoconioses." (1) | Podem afetar as vias respiratórias e os pulmões, desde rinite alérgica até asma ocupacional e pneumoconioses. |
| Sílica livre — poeira respirável | "Danos nas vias respiratórias." (2); "Problemas nas vias respiratórias." (1) | Silicose e outros danos às vias respiratórias. `[INTERPRETADO]` — o texto das fontes não nomeia a silicose; a alternativa sem interpretação é "Danos nas vias respiratórias." |

A proposta segue o estilo curto do Mauá: uma linha por perigo, que cabe na coluna da tabela.

## Desenho proposto para a chave

1. **Agente do app**, quando o perigo resolve (EXATA) em `agentes.yaml` — como decidido.
2. **Chave de perigo sem exame**, para os perigos de acidente, ergonômicos e psicossociais: entradas novas num
   vocabulário próprio (`vocabulario/agravos.yaml`), com `termos` de sinônimos como em `agentes.yaml`, e casamento
   pelo mesmo `resolver_termo`. Não é o texto do PGR: é uma forma conhecida, listada e revisada. Medido sobre as duas fontes:
   as 20 formas mais frequentes fora do agente (as da tabela acima, 9 delas psicossociais) somam 295 linhas; com elas a
   cobertura passaria de 148 para 443 das 518 linhas (86%), se cada forma ganhar sua chave.
3. **Produto de FDS** (componentes do cimento etc.): o agravo do produto, não o de cada componente. Pede a ligação
   componente → produto que a FDS já dá no app (D-ARQ-63) `[A MEDIR — quantos PGRs listam componentes]`.
4. Fora do dicionário: o agravo do PGR (D-ARQ-93), marcado "do PGR — conferir".

## Decisões do Diovanni

1. **Estilo do texto**: curto (Mauá) ou descritivo (R70)? Recomendação: curto, uma linha, com os efeitos principais.
2. **Ruído**: só PAIR, como o Mauá, ou PAIR mais os efeitos extra-auditivos que o R70 lista (zumbido, irritabilidade,
   distúrbios do sono, efeitos cardiovasculares)? Recomendação: "Perda auditiva induzida por ruído (PAIR), zumbido e
   efeitos extra-auditivos (irritabilidade, distúrbios do sono, alterações cardiovasculares)."
3. **As 9 formas limpas** da tabela acima.
4. **Chave de perigo sem exame** (desenho, item 2): aprova o vocabulário novo?
5. **Psicossocial**: um agravo só para os fatores psicossociais ("Transtornos mentais relacionados ao trabalho.")
   ou por fator?
6. **Aliases do achado 3**: medir o efeito nos PGRs pareados (mudam exame).
7. **Mandélico + fenilglioxílico**: o Seconci tem dois códigos (0113 e 0102) para o que no app é um exame (a soma, NR-07
   Anexo I Quadro 1). Exibir "(0113/0102)", separar em duas linhas no PCMSO, ou sem código?

## Já implementado nesta etapa — códigos Seconci

`codigo_seconci` em `exames.yaml` (decisão 4 de 14/10/2026), só de exibição. O par código ↔ exame foi medido pelas
linhas inteiras de tabela (código, nome e os 6 momentos na mesma linha) dos 8 PCMSOs em PDF do acervo, mais o `.docx`
do Mauá. Resultado: 26 códigos, nenhum código com dois exames.

| Código | Exame no app | Fontes |
|---|---|---|
| 0029 | 2,5-hexanodiona na urina | 1 |
| 0071 | Acetona na urina | 2 |
| 0102 + 0113 | Soma dos ácidos mandélico e fenilglioxílico | 2 + 2 — **sem campo, decisão 7** |
| 0116 | Ácido metil-hipúrico na urina | 2 |
| 130 | Ácido trans-trans-mucônico | 6 (3 dígitos em todos) |
| 0133 | Ácido tricloroacético na urina | 1 |
| 0281 | Audiometria | 7 |
| 0289 | Av. Médica de Saúde Mental | 1 |
| 0295 | Exame Clínico | 9 |
| 0296 | Acuidade Visual | 7 |
| 0300 | Avaliação Psicossocial | 5 (o Mauá escreve "300") |
| 0364 | Carboxihemoglobina | 5 |
| 0391 | Ciclohexanol na urina | 1, fora de linha inteira |
| 0467 | Cromo na urina | 2 |
| 0531 | ECG | 7 |
| 0562 | Espirometria | 7 |
| 0658 | Glicemia de Jejum | 7 |
| 0693 | Hemograma | 7 |
| 0836 | Manganês no sangue | 4 |
| 0863 | Metil-etil-cetona (MEK) na urina | 3 |
| 0951 | Ortocresol na urina | 4 |
| 1075 | RX de Coluna Lombo-Sacra | 4 |
| 1086 | Reticulócitos | 6 |
| 1181 | Tetrahidrofurano na urina | 1 |
| 1415 | RX de Tórax OIT | 7 |

Exames do app sem código conhecido (saem sem código e com aviso, na etapa 3): os outros 28 de `exames.yaml` (arsênio,
TTCA, mercúrio, chumbo, cádmio etc.). Teste: `test_codigo_seconci_e_o_medido_no_acervo`, varredura inversa 3/3.
