# Medicao: saida do app x matriz assinada — obra FASCINO (Consciente SPE 0030)

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
