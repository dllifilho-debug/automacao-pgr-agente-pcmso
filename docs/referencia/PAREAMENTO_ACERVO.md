# Pareamento do acervo — PGR (entrada) x Matriz/PCMSO (saida validada)

`[MEDIDO — 27/08/2026, listagem de matrizes_originais/ (79 arquivos), pareamento por
empresa/obra e data no NOME do arquivo. NAO conferido contra o conteudo dos documentos.]`

**Nao commitado.** Arquivo gerado pelo Arquiteto para revisao do Diovanni.

Criterio de confianca:
- **ALTA** — mesma obra/empresa identificavel no nome, e a matriz e igual ou posterior ao PGR.
- **MEDIA** — mesma obra, mas a data da matriz e ANTERIOR a do PGR (matriz pode vir de versao
  anterior do PGR), ou o PGR nao traz data no nome. Exige conferencia no conteudo antes de usar
  como gabarito.

---

## PARES (PGR -> matriz da mesma obra) — 14

| # | Obra / empresa | PGR (entrada) | Matriz / PCMSO (saida validada) | Conf. |
|---|---|---|---|---|
| 1 | CMO Viverde Areiao | PGR VIVERDE V02 - 03.02.25 (pdf+docx) | MATRIZ(ATUALIZACAO) CMO VIVERDE AREIAO 06.03.2025 + PCMSO 06.03.25 | ALTA |
| 2 | Consciente SPE 0030 / Fascino | PGR ... SPE 0030 - FASCINO (15.07.26) | MATRIZ(ATUALIZACAO) CONSCIENTE SPE 0030 LTDA 08.07.26 | MEDIA (matriz 7d antes) |
| 3 | Ricco Administracao / Escritorio | PGR RICCO-2026-ADMINISTRACAO 10.07.26 | MATRIZ(ATUALIZACAO) RICCO CONSTRUTORA LTDA ESCRITORIO 10.07.26 | ALTA (mesma data) |
| 4 | Ricco Hetrin | 01. PGR RICCO HETRIN - MAR25 | MATRIZ(ATUALIZACAO) RICCO HETRIN 23.05.2025 (3 copias) | ALTA |
| 5 | GPL / R78 Naturia | PGR R78 NATURIA PARTE 2 12.11.25 | MATRIZ(ATUALIZACAO) GPL R78 SPE 12.11.25 + MATRIZ(ADENDO) 14.08.2025 + PCMSO R78 NATURIA 12.11.25 | ALTA (mesma data) |
| 6 | Porto Araras I (Toctao) | PGR - PORTO ARARAS I SPE | MATRIZ(ATUALIZACAO) PORTO ARARAS 1 06.07.26 + MATRIZ(ADENDO) TOCTAO PORTO ARARAS I 15.08.25 | ALTA |
| 7 | CMO Vistamerica | PGR_CMO_...VISTAMERICA_2026-07-28 + PGR VISTAMERICA Ver.02 Rev.01 | MATRIZ(ADENDO) CMO VISTAMERICA 28.07.26 + MATRIZ(ATUALIZACAO) 08.12.25 + PCMSO 08.12.25 | ALTA (mesma data) |
| 8 | SPE T65 (Toctao) | PGR - ALT T65 2024.2026 + PGR - TOCTAO ALT 65 | MATRIZ(ATUALIZACAO) SPE T65 08.07.26 + PCMSO TOCTAO SPE_T65 18.03.2024 [assinado] | ALTA |
| 9 | CJR Engenharia | pgr_Cjr Engenharia Ltda (M Construtora) | Matriz de Exames (Obra Nova) - CJR ENGENHARIA LTDA | ALTA |
| 10 | CMO Floramazonia | PGR - CMO Residencial Floramazonia SPE | MATRIZ(OBRA NOVA) CMO RESIDENCIAL FLORAMAZONIA 04.04.2025 | ALTA |
| 11 | WVM 05 Entreverdes | PGR_WV_MALDI_ENTREVERDES_2026-07-22 | MATRIZ(ADENDO) WVM 05 ENTREVERDES 20.07.26 | MEDIA (matriz 2d antes) |
| 12 | Seconci Goias | PGR Seconci R02AA REV3 + REV4 | MATRIZ(ATUALIZACAO) SECONCI GOIAS 20.03.26 + PCMSO NOVO MODELO SECONCI (Dra. Carolini, maio 2024) | ALTA |
| 13 | CMO Construtora ADM | PGR CMO - Ver.02 Rev.02 | MATRIZ(ADENDO) CMO CONSTRUTORA ADM 03.12.25 + PCMSO 06.03.2025 | MEDIA (PGR sem data no nome) |
| 14 | Euro Park Setor C | PGR - EURO Setor C 2024.2026 | PCMSO(ATUALIZACAO) EURO PARK C 15.04.2024 (so PCMSO, sem matriz separada) | MEDIA |

**10 de 14 em ALTA confianca.**

### Adendo 28/08/2026 — 2 pares novos (acervo passa a 83 arquivos)

| # | Obra / empresa | PGR (entrada) | Matriz assinada | Conf. |
|---|---|---|---|---|
| 15 | Vila Brasil Engenharia (escritorio) | PGR ADENDO - VILA BRASIL ESCRITORIO 25.08.26 | MATRIZ(ADENDO) VILA BRASIL ENGENHARIA E PARTICIPACOES 26.08.26 | ALTA (matriz 1d depois) |
| 16 | Sinduscon-GO | PGR - Programa de Gerenciamento de Riscos 27.08.26 | MATRIZ(ATUALIZACAO) SINDICATO DA INDUSTRIA DA CONSTRUCAO DO ESTADO DE GOIAS 27.08.26 | ALTA (mesma data) |

**16 pares, 12 em ALTA confianca.** O par 15 e o SEGUNDO caso de escritorio/administrativo
puro do acervo (o outro e Ricco Escritorio) — contraste util contra canteiro.
O par 16 e o unico do acervo que nao e construtora, e sim entidade setorial.

Contraste util no conjunto: os pares 3 e 13 sao **administrativo/escritorio**; os demais sao
**canteiro de obra**. Serve para separar o pacote-base incondicional do pacote por risco.

---

## MATRIZES ORFAS — saida validada sem o PGR correspondente (~12)

Consciente Reserva 0028 (2 copias) · Engeseg Estrutural · Engeseg Estrutural Filial (2 docs) ·
Engeseg Metalurgica Goiana · Engeseg Engenharia · Oliveira Melo Horus Marista ·
Atzum Bossa OM · CMO Varandas Bueno · Dinamica Engenharia · Porto Jacaranda ·
Art Acabamentos · Tec Grua (PCMSO)

**Uso:** extrair regra clinica (o que a medica emite para qual cargo/risco).
**Nao servem** para medir acerto do parser — falta a entrada.

---

## PGRs ORFAOS — entrada sem matriz correspondente (~5)

01. PGR RICCO SERRA DOURADA - MAI.24 · PGR AURO · PGR TPB ANDRADE ·
PGR_EBSERH_HUMAP · PGR_EBSERH_UFGD (v7 e legado_GHES)

**Uso:** testar o parser (ingestao, segmentacao, reconhecimento de risco).
**Nao servem** para medir acerto clinico — falta o gabarito.
Os tres EBSERH sao **saude**, nao construcao civil.

---

## PCMSOs ORFAOS (documento completo, sem par)

Fazenda Jamaica JBJ (3 revisoes) · Passarela Estadio Serra Dourada ·
Muy Bueno / C239 (2) · Consciente Fazenda Santa Luzia (2 copias) · Envolt T1 206 ·
GCB 2F Engenharia · Quasar Flamboyant · Soft Pedro Ludovico

**Uso:** forma do documento final (o que o escritorio entrega ao cliente), nao a regra.

---

## Proximo passo

Extrair, dos 10 pares de ALTA confianca, a tupla `(cargo, riscos do PGR) -> (exames,
periodicidade, momentos)` e comparar com a saida do motor. O par 2 (Fascino) ja atravessa o
motor 19/19 offline — e o marco zero da medicao.

Ressalva de instrumento: `.doc` (Word 97) exige Word COM no host; LibreOffice->txt distorce
celula. Ver `scripts/medir_audiometria_dem.py`, que ja faz essa leitura.
