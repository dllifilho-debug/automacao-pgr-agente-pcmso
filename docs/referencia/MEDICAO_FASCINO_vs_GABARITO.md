# Medicao: saida do app x matriz assinada — obra FASCINO (Consciente SPE 0030)

> Duas tiragens, preservadas as duas (`D-ARQ-06`). A **2ª tiragem** abaixo é a corrente e
> foi produzida por instrumento versionado; a **1ª tiragem**, de 28/08/2026, segue íntegra
> no fim do arquivo porque é ela que registra o achado original das anotações da médica.

---

# 2ª tiragem — `[MEDIDO — 11/09/2026]`, instrumento versionado

**Produzida por** `python -m scripts.comparar_matriz_gabarito`, commit `eab9a0c`, rota
determinística sem LLM. Substitui o script descartável da 1ª tiragem — é a `DH-003EG-02`
paga para este instrumento.

- **Entrada:** `PGR - CONSCIENTE ... SPE 0030 - FASCINO (15.07.26).pdf`
- **Gabarito:** `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc`
- **Conversão:** `.doc → .docx` por LibreOffice, lido como **tabela** por `python-docx`.
  É o caminho que `VALIDACAO_LIBREOFFICE_vs_WORDCOM.md` mediu como idêntico ao Word COM,
  no próprio SPE 0030. **A ressalva 1 da 1ª tiragem ("número a reconferir") cai aqui.**

## Resultado

| Métrica | Valor |
|---|---|
| Cargos no gabarito | 41 |
| Cargos na saída do motor | 41 |
| Cargos pareados por nome | **41** |
| Células (cargo × exame) no gabarito | 368 |
| Células emitidas pelo motor | 363 |
| Cargos com conjunto de exames idêntico | **33 de 41** |
| Células do gabarito reproduzidas por identidade | **357 = 97,0%** |
| … reproduzidas também nos momentos | 356 = 96,7% |
| … reproduzidas também na periodicidade | 323 = 87,8% |

Aritmética fecha nas duas pontas: `363 − 6 = 357 = 368 − 11`.

## Superemissão — 6 células, e a médica escreveu a regra

| GHE | Cargo | Exames |
|---|---|---|
| GHE-10 | Encanador | acetona na urina, metil-etil-cetona |
| GHE-10 | Auxiliar de Encanador | acetona na urina, metil-etil-cetona |
| GHE-16 | Pintor | ortocresol na urina, ácido metil-hipúrico na urina |

São exatamente os três cargos que carregam anotação manuscrita da Dra. Carolini:

- Encanador e Auxiliar: *"Incluir no word do PCMSO, risco baixo no PGR para acetona e
  metiletilcetona"*
- Pintor: *"Incluir no word do PCMSO, risco baixo no PGR para destilados-petróleo, tolueno,
  metiletilcetona e xileno"*

**O motor não errou.** Ela reconhece o risco, classifica como baixo e manda incluir no PCMSO.
A divergência é de **onde** o exame aparece, não de se ele cabe. Superemissão clínica real,
nesta obra: **zero**. Sustenta a candidata a `R-*` que a 1ª tiragem já propunha.

## Subemissão — 11 células

| GHE | Cargo | Exames |
|---|---|---|
| GHE-08 | Carpinteiro | espirometria, RX tórax OIT |
| GHE-09 | Armador | carboxihemoglobina, espirometria, RX tórax OIT |
| GHE-17 | Serralheiro | carboxihemoglobina, manganês no sangue |
| GHE-19 | Recepcionista Demonstradora | acuidade visual, audiometria |
| GHE-19 | Recepcionista Comercial | acuidade visual, audiometria |

Divergência de momento, 1 célula: acuidade visual do Serralheiro tem `DEM` no gabarito e não
no motor.

## Periodicidade — camada medida pela primeira vez

A 1ª tiragem declarava **não cobrir periodicidade**, porque o app não imprimia o número
(`DT-003EW-02`). O commit `deed9f6` (28/08, 17:51) passou a imprimir — e a saída daquela
tiragem foi gerada às 08:46, **antes** dele. Esta é a primeira medição da camada.

| Exame | Motor | Gabarito | Ocorrências |
|---|---|---|---|
| RX Tórax OIT | PER 24 meses | PER 12 meses | **31**, em 31 cargos e 14 GHEs |
| Exame clínico | sem número (12) | PER 6 meses | 2 — Armador e Serralheiro |

**`[BLOQUEADOR — reportado, não ajustado]` O RX Tórax OIT diverge em 100% das ocorrências.**
`R-RX-01-sem` está `VALIDADO` e cita NR-07 Anexo III Quadro 1 (Portaria MTP 567/2022),
emitindo `periodicidade_meses: 24` com `periodicidade_apos_15a: 12`. A coordenadora assina
**12 meses direto**, sem o corte de 15 anos, em todos os 31 cargos.

Não é defeito de código: é divergência entre a norma como o protocolo a leu e a prática que a
médica assina. As duas leituras são defensáveis — ou ela aplica 12M por precaução ignorando o
corte, ou o 24M lê o Quadro 1 errado. **Conferir na fonte oficial do MTE (Normas
Regulamentadoras Vigentes) antes de arbitrar. Decisão do Arquiteto, possivelmente da própria
Dra. Carolini.** A tabela acima não foi ajustada para bater.

Os 2 casos de exame clínico semestral caem em Armador e Serralheiro — os mesmos cargos da
subemissão. Ela trata os dois como exposição mais alta do que o motor atribui.

## Reconciliação com a 1ª tiragem

Os **97,0%** batem exatamente. As contagens brutas diferem e a causa é conhecida:

| | 1ª tiragem (28/08) | 2ª tiragem (11/09) | Causa |
|---|---|---|---|
| Células do gabarito | 364 | 368 | extrator: `txt` × tabela `docx` |
| Superemissão | 4 | 6 | unidade: tipos de exame × células (cargo × exame) |
| Cargos pareados | 40 de 41 | 41 de 41 | corte da anotação colada ao nome |

## Ressalvas desta tiragem

1. As anotações manuscritas da médica são cortadas do nome do cargo para parear
   (`_ANOTACAO_COLADA`), e preservadas como dado. Duas formas medidas: parêntese em linha
   própria e hífen na mesma linha.
2. Três grafias divergentes entre gabarito e `exames.yaml` são resolvidas por alias **no
   instrumento**, não no vocabulário — `DT-003EO-02` é forma de saída, e mexer no
   vocabulário exigiria revisão de `R-*`.
3. `Avaliação Psicossocial ADM, PER, MRO)` segue sem parêntese de abertura no gabarito. O
   instrumento limpa o rótulo vazado antes de mapear o slug, com teste próprio (R2). Sem
   isso, 3 exames por cargo viram superemissão e subemissão falsas.

---

# 1ª tiragem — `[MEDIDO — 28/08/2026]`, script descartável


`[MEDIDO — 28/08/2026]` Primeira comparacao ponta-a-ponta entre a saida do motor e uma
matriz humana assinada. **Nao commitado** — gerado pelo Arquiteto para revisao.

- **Entrada:** `PGR - CONSCIENTE ... SPE 0030 - FASCINO (15.07.26).pdf`
- **Saida do app:** `matriz (3).html`, gerada 28/08/2026 08:46 por `app_matriz_local.py`
- **Gabarito:** `MATRIZ DE EXAMES(ATUALIZACAO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc`
  — Dra. Carolini Miranda Polesso Lisita, CRM-GO 14.864; preenchimento Ana Paula;
  data do documento 16/07/2026; data do PGR 15/07/2026.

## Resultado

| Metrica | Valor |
|---|---|
| Funcoes no gabarito | 41 |
| Funcoes na saida do app | 41 |
| Funcoes pareadas por nome | 40 |
| **Funcoes com conjunto de exames IDENTICO** | **32 / 40 (80%)** |
| Celulas exame-funcao no gabarito | 364 |
| Celulas emitidas pelo app | 359 |
| **Celulas do gabarito reproduzidas** | **353 = 97,0%** |

**A comparacao cobre identidade do exame e momentos (ADM/PER/MRO/RET/DEM). NAO cobre
periodicidade** — o app nao imprime periodicidade (`DT-003EW-02`), o gabarito imprime.

## As 11 celulas que faltam — uma causa

Concentradas em **duas funcoes: Armador e Serralheiro**.

- 2x carboxihemoglobina, 2x espirometria, 2x rx torax, 2x audiometria, 2x acuidade,
  1x manganes no sangue.
- 1 divergencia de momento: acuidade do Serralheiro tem DEM no gabarito
  (`R-VIS-01`, excecao do soldador) e nao tem no app.

Regras que existem no protocolo e nao dispararam: `R-PKG-ARMADOR` (armador com policorte)
e `R-PKG-SOLD` via `R-GHE-05` (serralheiro = risco contingente; sem `fumos_metalicos` no
inventario o motor nao atribui). O caso do serralheiro ja esta documentado em `R-GHE-05`
como divergencia esperada.

## As 4 celulas que sobram — outra causa, e a medica escreveu a regra

O motor emitiu biomonitoramento quimico que a medica nao pediu: acetona na urina,
metil-etil-cetona na urina (Encanador, Auxiliar de Encanador) e ortocresol / acido
metil-hipurico na urina (Pintor).

**Anotacoes manuais da medica, transcritas verbatim da coluna FUNCAO do gabarito:**

- `Encanador (Incluir no word do PCMSO, risco baixo no PGR para acetona e metiletilcetona)`
- `Auxiliar de Encanador (Incluir no word do PCMSO, risco baixo no PGR para acetona e metiletilcetona)`
- `Pintor (Incluir no word do PCMSO, risco baixo no PGR para destilados-petroleo, tolueno, metiletilcetona e xileno)`
- `Operador de Betoneiro- veja com a Seguranca, acho que e betoneira.`

Regra implicita, ainda nao formalizada no protocolo: **agente quimico com risco declarado
BAIXO no PGR nao gera biomonitoramento — gera mencao no texto do PCMSO.** Candidata a
R-* nova. Contrasta com `R-FDS-03` (cutoff de 5%), que o motor aplica hoje.

## Ressalvas da propria medicao

1. O `.doc` foi convertido por LibreOffice, que **distorce celula** — a leitura fiel exige
   Word COM no host (ver `scripts/medir_audiometria_dem.py`). Numero a reconferir.
2. O gabarito tem ruido de edicao ja catalogado: `Avaliacao Psicossocial ADM, PER, MRO)`
   aparece **sem parentese de abertura** em todas as linhas. A primeira passada desta
   medicao contou isso como "36 exames que o motor emitiu a mais" — **falso**, era defeito
   do extrator. Corrigido antes de publicar. Classe: ambiguo nunca vira negativo.
3. 1 funcao nao pareou por anotacao concatenada ao nome (`Aprendiz Administrativo de Obra`).
4. Grafias divergentes normalizadas na comparacao: `Glicemia de Jejum` (app) x
   `Glicemia em Jejum` (gabarito); `RX Torax OIT` x `RX de Torax OIT`;
   `RX Coluna Lombo-Sacra` x `RX da Coluna Lombo-Sacra`. Sao divergencia real de saida,
   nao de decisao clinica — `DT-003EO-02`.
