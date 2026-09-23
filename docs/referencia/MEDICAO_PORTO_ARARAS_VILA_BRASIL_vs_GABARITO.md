# Medição — matriz do motor × gabarito assinado: Porto Araras I e Vila Brasil Escritório

`[MEDIDO — 23/09/2026, branch claude/hopeful-newton-yjv3k7, sobre main c1acdd8]`
Fecha o `[A MEDIR]` de `DT-(sessão claude/hopeful-newton-yjv3k7)-01`. Sessão de medição: nenhum
código, teste ou `.yaml` tocado.

## Pares e método

| PGR (entrada) | Gabarito assinado | Médica |
|---|---|---|
| `PGR — PORTO ARARAS I SPE EMPREENDIMENTOS IMOBILIARIOS LTDA.pdf` (vigência 04/2026–04/2027, Rev. 01) | `MATRIZ DE EXAMES(ATUALIZAÇÃO)PORTO ARARAS 1 SPE EMPREEND. IMOB 06.07.26.doc` | Dra. Patrícia Montalvo Moraes, CRM-GO 14.949 |
| `PGR ADENDO - VILA BRASIL ESCRITORIO 25.08.26.pdf` (vigência 07/2026–07/2027, Rev. 3.2) | `MATRIZ DE EXAMES(ADENDO)VILA BRASIL ENGENHARIA E PARTICIPAÇÕES 26.08.26.doc` | Dra. Patrícia Montalvo Moraes, CRM-GO 14.949 |

Instrumento versionado `scripts/comparar_matriz_gabarito.py` (D-ARQ-62), rota determinística,
clientes offline.

**Envelope do topo — não é confirmação-RT.** `EnvelopeVerbatim` montado a partir do texto do topo
de cada PDF (`Vigência: MM/AAAA – MM/AAAA`; RT Eng. Adriano Augusto Gonçalves de Oliveira, CREA-GO
101672344D) e serializado por `serializar_envelope`. `resolver_validade` devolve `proposta = null`
para a vigência nesse formato (faceta `mm/aaaa` de `DT-003BV-01`), então `confirmacao.validade`
foi preenchida com o último dia da vigência (2027-04-30 e 2027-07-31).
`confirmacao.assinatura_engenheiro = true` é **suposição da medição**: a assinatura é imagem,
não verificável por texto. O envelope só alimenta os gates eliminatórios do PGR (R-PGR-01/06), não a
escolha de exame por GHE.

## Resultado bruto

| | Porto Araras | Vila Brasil |
|---|---|---|
| cargos pareados por nome | 43 | 71 |
| células do gabarito reproduzidas | 368/380 (96,8%) | 329/346 (95,1%) |
| superemissão | 1 | 0 |
| subemissão | 12 | 17 |
| divergência de momentos | 0 | 12 |
| divergência de periodicidade | 24 | 8 |
| status das matrizes | todas PARCIAL | todas PARCIAL |

Cargos não pareados (9 e 12): todos por grafia humana ou anotação da médica colada ao nome
(`pintor incluir no word do pcmso …`, `jr ll` × `JR II`, acento), mais os 2 resíduos do PDF de
Vila Brasil (`\x00CBO`, `\x002524`). Nenhum cargo real ausente de um dos lados.

## Classificação das 74 células divergentes

| classe | PA | VB | onde está registrado |
|---|---|---|---|
| **RX tórax OIT 24M (motor) × 12M (gabarito)** | 24 | 8 | `DT-003EC-01` — 3º e 4º PGR com a divergência |
| **Artefato do instrumento** | 9 | 12 | `DH-(sessão claude/hopeful-newton-yjv3k7)-01` (nova) |
| **Acuidade/audiometria em GHE só com risco postural/trânsito** | — | 10 | `DT-003EB-01` classe (4) |
| **Termo "produto + agente" não resolvido** (`Adesivo CPVC Ciclohexanona`/`… Metiletilcetona`) | — | 6 | `DT-(sessão claude/hopeful-newton-yjv3k7)-02` (nova) |
| **Alias ausente** (`Poeira da madeira` × `poeira_de_madeira`, `fuzzy_recusado`) | 4 | — | `DT-003EJ-01` (nota) |
| **Termo não resolvido** (`Produtos DomissanItários` → espirometria) | — | 1 | `vocabulario_ausente` visível; sem DT nova |

Artefatos do instrumento (21 células):
- **PA, 7 células — cargo repetido em dois GHEs.** `estagiário` está em ADMINISTRAÇÃO e em SESMT; o
  dicionário do instrumento é chaveado só por cargo e guarda o último, então o estagiário de
  ADMINISTRAÇÃO do motor é comparado ao de SESMT do gabarito.
- **PA, 2 células — grafia de exame.** `rx de coluna lombo sacra` não tem alias para
  `rx_coluna_lombo_sacra` (1 superemissão + 1 subemissão que se anulam).
- **VB, 12 células — erro de digitação no gabarito.** `ECG (ADM PER, MRO)`, sem vírgula entre ADM e
  PER; o instrumento lê só `MRO`. Com a vírgula, motor e gabarito coincidem (ADM, PER, MR).

**Nenhuma lacuna silenciosa.** Toda subemissão real tem pendência nomeada no GHE ou no documento
(`vocabulario_ausente`, `fuzzy_recusado`), e as matrizes saem PARCIAL.

## Remedição após alias + correções do instrumento

`[MEDIDO — 23/09/2026, mesma branch, sobre main 182a473 + alias "Poeira da madeira" + 3 correções
de `DH-(sessão claude/hopeful-newton-yjv3k7)-01`]`

| | Porto Araras | Vila Brasil |
|---|---|---|
| cargos pareados | 42 | 74 |
| células do gabarito reproduzidas | **383/383 (100%)** | 338/355 (95,2%) |
| superemissão | 0 | 0 |
| subemissão | 0 | 17 |
| divergência de momentos | 0 | 0 |
| divergência de periodicidade | 24 (RX OIT, `DT-003EC-01`) | 8 (RX OIT, `DT-003EC-01`) |

Porto Araras: o `estagiário` fica sem par dos dois lados (motor lê um deles como `Estagiario.`;
1 ocorrência × 2 no gabarito) — explícito em "não parearam", não mais subemissão falsa. Vila
Brasil: as 17 subemissões restantes são as 10 da classe (4) de `DT-003EB-01`, as 6 do termo
"produto + agente" e a 1 de `Produtos DomissanItários`.

