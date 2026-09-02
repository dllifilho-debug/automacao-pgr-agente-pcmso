# Medicao 003.FF — par T65: o motor atravessou, e o gargalo NAO e o parser

`[MEDIDO — 31/08/2026, rodada ao vivo `medicao_pgr rodar` @ `c9db9cc`]`
PGR: `matrizes_originais/PGR - ALT T65 2024.2026.pdf` (46 pag., 16 GHEs).
Gabarito: `MATRIZ DE EXAMES(ATUALIZACAO)SPE T65 EMPREENDIMENTO IMOBILIARIO LTDA 08.07.26.doc`,
Dra. Patricia Montalvo Moraes, data 03/07/2026. Conversao `soffice --convert-to docx` +
`python-docx` (instrumento validado em 003.FE).
Relatorio bruto: `relatorios/003ff_t65_rodada.md`. Quarta medicao externa do projeto.

## 1. O T65 atravessou pela rota LLM, sem uma linha de parser nova

16/16 GHEs transcritos, **zero pendencia bloqueante**. 13 `PARCIAL`, 3 `BLOQUEADA`
(GHE-03, GHE-04, GHE-14). `familia_nao_medida` apareceu como esperado — nao-bloqueante.

Isso confirma a leitura de `MEDICAO_003FF_gargalo_T65.md` secao 5: o que impediu o T65 em
003.FE foi o HTTP 503, nao a ausencia da familia 2.

## 2. Acerto contra o gabarito: 48,4%

| Metrica | Valor |
|---|---|
| Linhas do gabarito | 61 (18 GHEs) |
| Linhas pareaveis | **56** — GHE 17 e 18 existem no gabarito e nao no PGR (ver ressalva 5) |
| Celulas do gabarito nas linhas pareaveis | 440 |
| **Celulas reproduzidas** | **213 = 48,4%** |
| Linhas com conjunto de exames IDENTICO | **8 de 56** |
| Celulas SOBRANDO | 6 (`acetona_urina` 3, `mek_urina` 3 — GHE-11) |

Contraste com os pares anteriores: **Fascino 97,0%**, **Ricco ADM 91,1%**, **T65 48,4%**.

As 227 celulas faltantes, por exame:

| Exame | Faltantes |
|---|---|
| `acuidade_visual` | 46 |
| `hemograma` | 43 |
| `ecg` | 43 |
| `glicemia` | 43 |
| `rx_torax_oit` | 26 |
| `espirometria` | 26 |

**`audiometria`: zero faltante.** Onde o gabarito pede, o motor emite.

## 3. A causa: cobertura de termo no vocabulario, nao regra ausente nem parser

O gabarito da Dra. Patricia **nao** emite pacote-base ampliado incondicional. O padrao separa
limpo por GHE:

| GHE | Setor | ECG/Hemog/Glic/Acuid | Espiro/RX |
|---|---|---|---|
| 03, 04 | Administracao, Almoxarifado | nao | nao |
| 01, 02, 12, 13 | Engenharia, Elevador, Icamento | **sim** | nao |
| 05, 06, 07, 09, 10, 11, 15, 16 | Eletrica…Gesso | **sim** | **sim** |
| **08** | **Central de Argamassa** | **nao** | **sim** |

`GHE-08` e a testemunha decisiva: poeira **sem** altura. Os dois grupos sao independentes e
correspondem exatamente a `R-PKG-ATIVCRIT` (altura / espaco confinado / maquina pesada) e ao
pacote de poeira. **As regras do motor estao certas.** `DT-003EB-01` (pacote-base incondicional)
nao explica este documento.

O que falha e a resolucao termo -> slug. Medido em `agentes.yaml`: **53 de 79 slugs sem
`termos:`**. Os dois casos que produzem as 227 celulas:

1. **`trabalho_altura` tem UM termo: `"Trabalho em Altura"`** (NR-35, titulo). O T65 escreve
   **`"Queda em altura"` (13 ocorrencias)**. Nao casa -> predicado `altura=False` em todos os
   GHEs -> `R-PKG-ATIVCRIT` nunca dispara -> **175 celulas** (acuidade+hemograma+ecg+glicemia).
2. **`silica` tem 6 termos, todos nus** (`"Silica livre"`, `"Quartzo"`…). O T65 escreve
   **`"Silica Livre - Poeira respiravel"`**, em **tres grafias de caixa distintas**. Nao casa ->
   **52 celulas** (`rx_torax_oit` + `espirometria`). Esta e literalmente a classe de `D-ARQ-83`
   (fracao declarada sem agente: "poeira **contendo** X") e a mesma classe do alias com
   qualificador ja registrado (`"Metiletilcetona (MEK)"` nao cobre a grafia nua).

**Duas entradas de vocabulario respondem por 227 das 227 celulas faltantes.** Nenhuma delas e
parser, nenhuma e regra clinica nova.

`[A VALIDAR — pendencia clinica]` Se `"Queda em altura"` deve resolver para `trabalho_altura` e
juizo clinico, nao mecanico: queda em altura e a consequencia, trabalho em altura e a exposicao.
A derivacao normativa favorece: a NR-35 define trabalho em altura acima de 2m, e o proprio T65
escreve na coluna de exposicao *"Na execucao das atividades a cima de dois metros com risco de
queda"* — o criterio da norma, verbatim. Mas cadastrar alias que muda saida do motor exige
decisao, nao inferencia do Arquiteto.

## 4. Os 45 termos nao resolvidos (98 ocorrencias)

Alem dos dois acima, o T65 expoe familias inteiras sem slug: acidentes (`"Queda de mesmo nivel"`
14, `"Choque Eletrico"` 4, `"Objetos cortantes e/ou perfurocortantes"` 5, `"Intemperies"` 5),
ergonomia (`"Postura incorreta de trabalho"` 7, `"Levantamento e transporte manual de cargas"`,
`"Postura de pe por longos periodos"` em 2 grafias) e quimicos de tinta/gesso (`"Oxido de Ferro
Amarelo"`, `"Carbonato de Calcio ppt"`, `"Silicato de Aluminio Hidratado"`, `"Po de madeira"`,
`"Cimento portland"`). Lista integral no relatorio bruto.

Nota de grafia: varios termos aparecem em 2-3 formas no MESMO documento (`"Postura de pe por
longos periodo"` / `"…periodos"`; tres caixas de `"Silica Livre - Poeira respiravel"`). Qualquer
solucao por alias literal tem de aguentar isso.

## 5. Ressalvas

- **Descompasso de versao.** O gabarito e de 03/07/2026 e tem 18 GHEs; o PGR e "ALT T65
  2024.2026", Revisao 00 de 18/03/2024, com 16 GHEs. As 5 linhas de GHE 17/18 foram excluidas do
  denominador. Nao verifiquei se os 16 GHEs comuns mudaram de conteudo entre as versoes —
  divergencia residual pode ter origem ali, nao no motor. `[A MEDIR]`
- **Pareamento por GHE, nao por linha.** O motor decide o pacote por GHE; comparei o conjunto do
  GHE contra cada linha do gabarito daquele GHE. Onde a medica diferenciou cargos DENTRO de um
  GHE (ha marcas disso: `"Meio Oficial de Armador (Nao opera policorte)"`), este metodo nao
  captura. Difere do pareamento por linha usado no Ricco. `[INTERPRETADO]`
- **Rota LLM, nao deterministica.** O numero mistura erro de transcricao com erro de regra. Uma
  segunda rodada pode dar numero diferente.
- **Erro do Arquiteto durante esta medicao, corrigido antes de publicar:** afirmei que o slug
  `altura` estava ausente do vocabulario. Falso — procurei pelo nome do PREDICADO
  (`predicados.py:42 @primitivo("altura")`) e nao pelo slug do AGENTE (`trabalho_altura`), que
  existe. O defeito real e cobertura de termo, nao ausencia de slug.

## 6. Consequencia para a fila

`DT-003FE-01` (familia 2 do parser) **nao e o maior movimento**. Mesmo com a familia 2 escrita e
o mapeamento coluna->`RiscoVerbatim` resolvido, o T65 continuaria proximo de 48%: os termos que
o parser entregaria continuariam sem casar no vocabulario. A alavanca medida e a cobertura de
termo.

## 7. Adendo — 58% do residuo tem slug esperando `[MEDIDO + INTERPRETADO]`

Fato clinico trazido pelo Diovanni (31/08): **"queda em altura" e "trabalho em altura" sao
sinonimos usados por engenheiros; nao ha padrao de nomenclatura — cada um escreve o mesmo
conceito com nome diferente.** Fecha o `[A VALIDAR]` da secao 3 e generaliza o problema.

Cruzando os 98 termos nao resolvidos contra os 79 slugs de `agentes.yaml` (contagem MEDIDA;
o mapeamento termo->slug e classificacao do Arquiteto, `[INTERPRETADO]`):

| | |
|---|---|
| Ocorrencias com slug **ja existente** esperando | **57 de 98 (58%)** — 24 termos distintos -> **9 slugs** |
| Ocorrencias sem slug obvio | 41 (21 distintos) |

Os 9 slugs: `postura_inadequada` 19, `trabalho_altura` 13, `esforco_fisico` 8,
`acidente_perfurocortante` 5, `eletricidade` 5, `silica` 3, `acidente_disco_corte` 2,
`movimento_repetitivo` 1, `queda_de_materiais` 1.

**O modo de falha nao e "falta slug".** Dois casos que provam:

- `esforco_fisico` **ja tem alias**: `"Levantamento e Transporte Manual de cargas"`. O T65
  escreve `"Levantamento e transporte manual de cargas ou volumes"`. Falha pelo **sufixo**.
- `postura_inadequada` tem o alias `"Postural"` — inutil contra as **6 formas** distintas que o
  T65 usa para o mesmo conceito.

E `fuzzy_permitido: true` ja esta ligado em 7 dos 9 slugs. Nao alcanca: `resolver_termo` compara
**string inteira** com Levenshtein <= 2 (`PISO_FUZZY` 4, bilateral). Isso cobre **typo**, nao
sinonimo nem prefixo/sufixo — e esta correto por desenho, nao e defeito.

`trabalho_altura` e `silica`, os dois que valem as 227 celulas, **nao** tem `fuzzy_permitido`.

### Fronteira que ninguem no pipeline cruza

O transcritor-LLM normaliza linguisticamente (D-ARQ-50 P2: "tire qualificador solto, quebre
composto, corrija typo obvio") **sem conhecer o vocabulario**; o resolvedor **conhece** o
vocabulario mas so compara string. Sinonimo exige as duas coisas juntas, e a fronteira
`D-ARQ-41`/`D-ARQ-50 P2` ("LLM NUNCA emite slug") existe justamente para impedir escolha de
identidade silenciosa. Qualquer solucao tem de respeitar essa fronteira ou reabri-la
explicitamente.

### Nota sobre o prompt do transcritor

`_PROMPT_GHE` e calibrado para a familia Consciente/Fascino e foi aplicado ao T65 assim mesmo:
crava a ancora `"SETOR/FUNCAO ..."` (que o T65 nao tem) e manda ignorar o cabecalho
`"Cod. Atividades Perigo Exposicao Fonte geradora Doenca do Dano..."` (que e do Fascino). A
regra 3c manda **transcrever o proprio texto do perigo como agente** quando nao ha quantificacao
— no Fascino e excecao, no T65 e a regra geral. E a origem direta dos 45 termos descritivos.
`[MEDIDO — leitura de `transcritor_gemini_pgr.py`]`
