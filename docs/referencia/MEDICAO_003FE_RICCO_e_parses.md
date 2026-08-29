# Medicao 2: Ricco Administracao, e por que dois PGRs nao atravessaram

`[MEDIDO — 29/08/2026]` Segunda e terceira medicoes externas do projeto, sobre o app rodando
local (`app_matriz_local.py`, branch com `deed9f6`). **Nao commitado** ate revisao.

## Par 2 — Ricco Construtora Administracao (PGR 10.07.26 x matriz 10.07.26, mesma data)

| Metrica | Valor |
|---|---|
| Linhas de cargo | 12 no gabarito, **12 no app** |
| Funcoes com conjunto de exames IDENTICO | **11 de 12** |
| Celulas do gabarito reproduzidas | **41 de 45 = 91,1%** |
| Celulas emitidas a mais (SOBRA) | **0** |

**Pareamento por LINHA, nao por nome.** `Recepcionista` aparece em dois GHEs (GHE-01 e GHE-02)
com pacotes diferentes — audiometria so no segundo. A primeira medicao pareou por nome
normalizado, colapsou as duas e devolveu 89,7%; pareando por linha o numero e **91,1%**.
Cargo repetido entre GHEs e legitimo (`R-GHE-01`/`D-ARQ-21`, precedente Viverde: pedreiro em 6
GHEs) — quem mede matriz humana tem de parear por linha.

**As 4 celulas faltantes** estao numa unica funcao: ECG, hemograma, glicemia e acuidade — o
pacote de atividade critica (`R-PKG-ATIVCRIT`).

**Divergencia sistematica, 11 de 12 cargos:** `Avaliacao Psicossocial` sai `(ADM, MRO)` no
gabarito e `(ADM, MRO, PER)` no app. `R-PSY-02` prescreve adm/per/MR incondicional; a Dra.
Patricia nao pede periodico neste documento. E conduta, nao defeito de parser — ver `DT-003FE-02`.

**Grafia preservada corretamente:** o app emite `GERENTE ADMNISTRATIVO` (typo do PGR, verbatim);
o gabarito humano escreve `Gerente Administrativo`. O motor esta certo em nao corrigir a fonte.

## Pares 3 e 4 — nao atravessaram, por causas distintas

Varredura das ancoras que `extracao_pgr.py` usa para localizar bloco
(`DADOS GERAIS` + titulo no formato `N.N`):

| PGR | Paginas | `DADOS GERAIS` | `fonte geradora` | titulos `N.N` | Resultado |
|---|---|---|---|---|---|
| **Ricco ADM** | 25 | **1** | 2 | 9 | matriz gerada, 91,1% |
| Sinduscon 27.08.26 | 59 | 0 | 0 | 5 | `segmentacao_implausivel` — 0 blocos |
| T65 ALT 2024.2026 | 46 | 0 | 0 | 0 | `familia_nao_medida` |
| Toctao ALT 65 | 106 | 0 | 0 | 31 | (nao rodado no app) |

**`DADOS GERAIS` e o discriminante** — presente so no que atravessou. E existe **uma unica
familia de parser** no repo: `agente_medico/motor/parser_familia_consciente.py`.

**O T65 tem estrutura melhor que a do Fascino e o motor nao a enxerga.** 16 blocos ancorados em
`GHE 01`..`GHE 16`, cada um com cargo, atividade e perigos nomeados:

```
GHE 01
Possivel quantidade de colaboradores expostos: 00
Descricao da atividade
  [texto]
Auxiliar de engenharia
Perigo
  Perda auditiva induzida pelo ruido
  Origem do Risco: Mobiliario defeituoso ou sem regulagem
```

A ancora e literalmente `GHE` + numero. Nao e limitacao de conteudo: e uma familia de parser
que ninguem escreveu. Ver `DT-003FE-01`.

**Toctao e Sinduscon sao casos proprios.** O Toctao tem 31 titulos `N.N` e 34 mencoes a GHE,
todas em prosa metodologica — nao ha ancora de bloco. O Sinduscon tem 5 titulos e 1 mencao a GHE
em 59 paginas. Os dois exigem medicao propria; o T65 nao.

**Falha de infra concorrente (T65):** a cascata Gemini devolveu **HTTP 503 nos tres modelos**
(`gemini-flash-latest`, `gemini-2.5-flash`, `gemini-flash-lite-latest`), entao o fallback-LLM
tambem nao estava disponivel. Nao e defeito do codigo; e ruido a descontar na leitura.

## Ressalva de instrumento

A varredura de ancoras usou `pdftotext`; o motor extrai com `pdfplumber`. A forma exata da
ancora `GHE NN` tem de ser medida no extrator do motor antes de virar regex — `pdftotext -layout`
e o modo padrao ja discordaram entre si nesta medicao. `[INTERPRETADO — prioridade na revisao]`
