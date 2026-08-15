# Gabarito 003.EX — audiometria com DEM, universo `R-AUD-04`

Medição de fato sobre dois gabaritos humanos assinados por médicas do trabalho: a audiometria
sai com `DEM` (momento demissional) para quem não tem exposição a ruído declarada no PGR?
Sustenta a base normativa do `R-AUD-04` (§5.2 do `PROTOCOLO_AGENTE_MEDICO.md`). Medido em
003.EX; congelado aqui porque `relatorios/` (onde a medição bruta viveu) é gitignored — esta é a
versão que sobrevive ao fechamento da sessão.

## Fontes

- `MATRIZ DE EXAMES(ATUALIZAÇÃO)CONSCIENTE SPE 0030 LTDA 08.07.26.doc` — Dra. Carolini, gabarito
  do Fascino (já usado em 003.ED/003.EO).
- `MATRIZ DE EXAMES (ATUALIZAÇÃO ) CONSCIENTE RESERVA 0028.doc` — Dra. Patrícia, 28/04/2025.
- `MATRIZ DE EXAMES (ATUALIZAÇÃO ) CONSCIENTE RESERVA 0028 (1).doc` — mesma obra, cópia
  posterior (ver "Os dois arquivos RESERVA 0028 divergem", abaixo). **Gabarito de referência
  recomendado para `R-AUD-04`: esta cópia `(1)`, não a base.**
- Conversão `.doc` → `.docx` via Word COM automation (`pywin32`), leitura célula a célula via
  `python-docx`. Instrumento: `scripts/medir_audiometria_dem.py`, testes em
  `tests/test_medir_audiometria_dem.py` (5 testes, todos com reversão nomeada e varredura
  inversa confirmada nesta sessão).

## Resposta ao corte que decide `R-AUD-04`, nominal

**Gabarito Fascino (SPE 0030), estrutura por GHE — os únicos dois GHEs medidos por 003.ED como
fora do pacote de atividade crítica divergem entre si:**

- **GHE 06 (Administração) — 5/5 cargos recebem Audiometria COM DEM.** Analista, Assistente e
  Auxiliar de Administração de Pessoal, Aprendiz Administrativo de Obra, Assistente
  Administrativo de Obras.
- **GHE 19 (Vendas) — 0/2 cargos recebem DEM.** Recepcionista Demonstradora e Recepcionista
  Comercial saem com `Audiometria (ADM, PER, MRO)` — sem `DEM`. Único GHE do documento, junto
  com GHE 14 (Operação de Grua, 1 cargo), sem DEM na audiometria.

**GHE 12 (Betoneira), fora do discriminante** — tem `vibracao_mao_braco` resolvido desde
003.EJ, recebe audiometria por `R-VIB-02`, não é cargo sem risco. Medido (1/1 cargo com DEM),
não contado como evidência de emissão incondicional.

**Nem "DEM acompanha o ruído" puro nem "DEM incondicional" puro explicam os dois GHEs
isoladamente.** GHE-06 não tem risco de ruído resolvido — mesma situação de GHE-19 — e ainda
assim recebe DEM. Se fosse "acompanha o ruído", GHE-06 não deveria receber; se fosse
"incondicional", GHE-19 deveria receber.

**Gabarito RESERVA 0028 não tem GHE-19 nem cargo equivalente a "Vendas".** Os cargos
administrativos existentes recebem DEM em todos os casos confirmados (ver tabela abaixo) —
reforça que administrativo-sem-ruído não suprime o DEM, mas não há, neste gabarito, nenhum
cargo que reproduza a ausência de GHE-19.

**Leitura:** o corte não é "tem ruído" nem "é administrativo" — é mais estreito. Vendas (GHE-19)
é o único ponto de dado que efetivamente nega DEM; não há, nos dois gabaritos, um segundo cargo
limpo que replique essa ausência. n=1 cargo-tipo (Vendas, 2 ocorrências no mesmo GHE) não
calibra um corte geral.

## Números agregados

**Três colunas, não duas.** Rótulo não reconhecido na própria linha de audiometria vai para
`indeterminado`, não para `sem DEM` — ausência de leitura não é negação de conduta (mesma classe
de erro de `D-ARQ-13`, fora do motor).

| Documento | Total cargos | Com audiometria | Com DEM | Indeterminado | Sem DEM (confirmado) |
|---|---|---|---|---|---|
| SPE 0030 (Fascino, Dra. Carolini, 07/2026) | 41 | 41 | 38 | 0 | 3 |
| RESERVA 0028 (base, Dra. Patrícia, 04/2025) | 44 | 43 | 42 | 1 | 0 |
| RESERVA 0028 (1) | 44 | 44 | 42 | 2 | 0 |

**Nos dois RESERVA, `sem DEM` confirmado é zero** — todo cargo com linha de audiometria recebe
DEM ou fica em `indeterminado` por forma ambígua (nunca uma negação limpa). No SPE 0030, os 3
`sem DEM` são forma limpa (`Audiometria (ADM, PER, MRO)`, sem rótulo não reconhecido) —
confirmados, não indeterminados.

Audiometria em 41/41 (SPE 0030) e 44/44 (RESERVA). Demissional confirmado em 38/41 (93%,
Carolini) e 42/42 + 2 indeterminados prováveis (95–100%, Patrícia). Duas médicas, dois clientes,
lados opostos do corte de vigência da NR-01 (26/05/2026) — e convergem. Contraste no mesmo par
de documentos: espirometria 12/43 contra 32/40 (fator ~3, divergente) e psicossocial 0/43 contra
41/41 (divergência total, resolvida só pelo corte de vigência) — nesses dois eixos o gabarito foi
desqualificado como fonte; neste, não.

**Limitação de escopo, declarada.** Os dois documentos são construção civil, e o acervo inteiro
é de construtoras — limitação estrutural da amostra, não de tamanho. Reinspecionar no primeiro
PGR de hospital, indústria química ou setor administrativo puro.

Referência herdada de 003.EI (conversão LibreOffice→txt, com ressalva de reconferência): 40
(SPE 0030) e 43 (RESERVA 0028). Esta medição (Word COM, célula a célula) diverge em +1 cargo em
ambos — divergência esperada e nomeada no prompt de 003.EX, não bloqueador.

## Os dois arquivos RESERVA 0028 divergem

Não são idênticos — hashes MD5 diferentes, tamanhos diferentes (59.717 B vs 61.459 B
convertidos). O arquivo `(1)` é revisão posterior: adiciona anotações de risco/idade em 4 cargos
(Encanador, Auxiliar de Encanador, Aprendiz Administrativo de Obra, Engenheiro de Controle de
Obra) e diverge em **dois cargos independentes** quanto à linha de audiometria:

- **SERRALHEIRO**: a célula de exames da cópia base está **truncada** — o texto começa
  abruptamente em `"\n\nCarboxihemoglobina no sangue..."`, sem Exame Clínico, Acuidade Visual,
  Hemograma, ECG **nem Audiometria**. A cópia `(1)` tem a lista completa, com `Audiometria (12
  meses), (ADM, PER, MRO, DEM);`. Não é artefato de parser — é o conteúdo real da célula no
  `.doc` de origem; a base perdeu o início do texto (erro de edição), `(1)` corrige. É o cargo
  que explica "com audiometria" subir de 43 (base) para 44 `(1)`.
- **SUPERVISOR DE INSTALAÇÕES HIDRÁULICAS**: o inverso — base tem `Audiometria (12 meses), (ADM,
  PER, MRO, DEM);` (DEM presente, forma limpa); `(1)` tem `Audiometria (12 meses) ADM, PER, MRO,
  DEM);` — falta o `(` de abertura do segundo grupo, typo introduzido nessa revisão. Classificado
  `indeterminado`, não `sem DEM`.

Os dois efeitos se cancelam na contagem agregada de "com DEM" (42 nas duas cópias, por
coincidência), mas a composição nominal difere. **A evidência do Serralheiro confirma que `(1)`
é a cópia posterior/corrigida** — corrobora as 4 anotações extras.

**Operador de Elevador de Carga não diverge** entre as cópias: base e `(1)` batem em conteúdo de
audiometria (`(ADM, PER, MRO, DEM)`, DEM presente nas duas); a diferença é só uma linha de "Rx de
coluna lombo-sacra" colada sem separador no `(1)`, que não afeta a leitura de audiometria.

## Forma real das células — desvios do formato `Exame (MOMENTO, MOMENTO, ...)`

1. **Periodicidade em grupo separado antes dos momentos** (RESERVA, ambos arquivos):
   `Audiometria (12 meses), (ADM, PER, MRO, DEM)`. O extrator captura até dois grupos após
   "Audiometria" e usa o último como o de momentos.
2. **Periodicidade embutida no rótulo do momento** (RESERVA, cargo "Assistente Administrativo de
   Segurança do Trabalho", ambos arquivos): `Audiometria (ADM, PER, MRO, DEM 12 meses)`. O
   rótulo `DEM 12 meses` não bate com `DEM` exato — classificado `indeterminado`. Mesma classe de
   desvio de `DT-003EW-02`.
3. **Audiometria colada ao exame anterior, sem separador de linha** (RESERVA, cargo "Operador de
   Betoneira", ambos arquivos): `Exame Clinico (...), Audiometria (12 meses), (ADM, PER, MRO,
   DEM);\n...`.
4. **Parêntese de abertura ausente** (SPE 0030, "Avaliação Psicossocial ADM, PER, MRO)"; RESERVA
   `(1)`, "Audiometria (12 meses) ADM, PER, MRO, DEM)"): célula genuinamente malformada no
   documento de origem — reportada como rótulo não reconhecido, não forçada.

## Verificação estrutural — coluna FUNÇÃO com anotação da médica (SPE 0030)

A coluna FUNÇÃO às vezes carrega anotação da médica na mesma célula do cargo, em parágrafo
separado. Verificado diretamente na estrutura da tabela via Word COM (maior fidelidade que
conversão LibreOffice→txt):

- **GHE 16 Pintura**: uma única linha de tabela, `cell[0] = "Pintor\n(Incluir no word do PCMSO,
  risco baixo no PGR para destilados-petróleo, tolueno, metiletilcetona e xileno)"`, `cell[1]`
  com **um** bloco de exames — sem ambiguidade estrutural, sem absorção de cargo vizinho.
- **GHE 06 Administração**: uma única linha, `cell[0] = "Aprendiz Administrativo de Obra-
  Incluir no WORD do PCMSI idade maior ou igual 18 anos."`, `cell[1]` com um bloco de exames
  limpo. Mesmo padrão.

Nenhuma heurística de texto foi usada para separar anotação de cargo — cada linha da tabela já é
um cargo com sua própria célula de exames; a anotação é conteúdo textual dentro dela, tratado
como parte do nome do cargo (`\n` embutido vira `" / "` só na exibição do relatório).
**Contagem final: 41 cargos, 41 com linha de audiometria.**

## Nominal — SPE 0030 (Fascino, Dra. Carolini)

**Com DEM (38):**

Auxiliar de Engenharia, Estagiário de Engenharia, Assistente de Engenharia, Estagiário de Obra
(GHE 01); Técnico de Segurança do Trabalho, Supervisor de Segurança do Trabalho (GHE 02); Mestre
de Obras, Encarregado de Pedreiro, Encarregado de Hidráulica, Encarregado de Elétrica,
Encarregado de Pintor, Encarregado de Carpinteiro, Supervisor de Instalações Elétricas, Auxiliar
de Obra (GHE 03); Almoxarife, Auxiliar de Almoxarifado, Assistente de Almoxarifado, Supervisor
de Almoxarifado (GHE 04); Auxiliar de Limpeza e Conservação (GHE 05); Analista de Administração
de Pessoal, Assistente de Administração de Pessoal, Auxiliar de Administração de Pessoal,
Aprendiz Administrativo de Obra, Assistente Administrativo de Obras (GHE 06); Pedreiro, Ajudante
de Produção Civil (GHE 07); Carpinteiro (GHE 08); Armador (GHE 09); Encanador, Auxiliar de
Encanador (GHE 10); Eletricista, Auxiliar de Eletricista (GHE 11); Operador de Betoneira (GHE
12 — fora do discriminante, vide acima); Sinaleiro (GHE 13); Operador de Elevador de Carga (GHE
15); Pintor (GHE 16); Serralheiro (GHE 17); Montador (GHE 18).

**Sem DEM, confirmado (3):** Operador de Grua (GHE 14); Recepcionista Demonstradora,
Recepcionista Comercial (GHE 19).

**Indeterminado:** nenhum.

## Nominal — RESERVA 0028 (1), cópia de referência

**Com DEM (42):** Armador, Carpinteiro, Ajudante de Produção Civil, Pedreiro, Eletricista,
Encanador, Auxiliar de Eletricista, Auxiliar de Encanador, Operador de Betoneira, Técnico de
Segurança do Trabalho, Mestre de Obras, Aprendiz Administrativo de Obra, Engenheiro de Obra,
Assistente Administrativo de Obras, Almoxarife, Auxiliar de Almoxarifado, Supervisor de
Instalações Elétricas, Assistente de Engenharia, Supervisor de Segurança do Trabalho, Estagiário
de Engenharia, Encarregado de Pedreiro, Pintor, Analista de Administração de Pessoal,
Serralheiro, Auxiliar de Administração de Pessoal, Encarregado de Hidráulica, Assistente de
Administração de Pessoal, Auxiliar de Engenharia, Auxiliar de Limpeza e Conservação, Encarregado
de Elétrica, Encarregado de Pintor, Auxiliar Administrativo de Obra, Engenheiro de Controle de
Obra, Operador de Grua, Sinaleiro, Encarregado de Carpinteiro, Auxiliar Administrativo de
Segurança do Trabalho, Estagiário de Obra, Auxiliar de Obra, Operador de Elevador de Carga,
Assistente de Almoxarifado, Supervisor de Almoxarifado.

**Indeterminado (2):** Supervisor de Instalações Hidráulicas (parêntese de abertura ausente —
DEM presente na cópia base); Assistente Administrativo de Segurança do Trabalho (periodicidade
colada ao rótulo `DEM`).

**Sem DEM, confirmado:** nenhum.

## Rótulos não reconhecidos (verbatim)

- `['DEM 12 meses']` em `'Audiometria (ADM, PER, MRO, DEM 12 meses),'` — Assistente
  Administrativo de Segurança do Trabalho, ambas as cópias RESERVA.
- `['12 meses']` em `'Audiometria (12 meses)'` — Supervisor de Instalações Hidráulicas, só na
  cópia `(1)`.

## Interpretação dos indeterminados — decisão humana, fora do instrumento

O script (`classificar_dem`) permanece neutro: não decide se `indeterminado` conta como DEM
presente. A leitura usada para `R-AUD-04` foi: `"DEM 12 meses"` contém o rótulo `DEM` com
periodicidade colada (mesma família de defeito de `DT-003EW-02`); o caso do Supervisor de
Instalações Hidráulicas está corroborado pela cópia base, que tem a mesma linha com DEM íntegro.
Ambos tratados como DEM presente na especificação de `R-AUD-04` — decisão registrada aqui, não
no instrumento.

## Achados laterais, sem padrão

- **Operador de Grua (GHE-14, SPE 0030) não tem anotação manual na célula** — `cell[0] =
  'Operador de Grua'`, limpa. A ausência de DEM não tem explicação documental; é o cargo com
  maior chance de estar acima do nível de ação em todo o documento, e ainda assim sai sem
  demissional, enquanto Analista de Administração de Pessoal recebe.
- As três exceções do SPE 0030 (Operador de Grua, Recepcionista Demonstradora, Recepcionista
  Comercial) não espelham nenhum grupo do RESERVA. Nenhuma condição negativa é derivável disso —
  entram como divergência conhecida contra o gabarito, não como regra.

## Proveniência

Medido em 003.EX (branch `feat/003ex-medicao-audiometria-dem`), Word COM sobre o host, árvore
parada. `.docx` convertidos e relatório bruto viveram em `relatorios/003ex/` (gitignored); este
documento é a extração nominal versionada — a evidência bruta de `R-AUD-04` sobrevive aqui, não
em `relatorios/`.
