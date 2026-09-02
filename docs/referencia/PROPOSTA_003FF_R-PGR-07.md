# Proposta 003.FF — `R-PGR-07` para `PROTOCOLO_AGENTE_MEDICO.md`

Artefato pronto para o Crítico. **Não inserido no documento vivo** — a inserção acontece depois
do julgamento (gate de fechamento, modo CONHECIMENTO).

Verificação de ID `[MEDIDO — `git show HEAD:docs/PROTOCOLO_AGENTE_MEDICO.md`, 31/08/2026]`:
`R-PGR-01` a `R-PGR-06` existem; **`R-PGR-07` não existe**. Nenhuma R-* é alterada ou
depreciada por esta proposta.

Sítio de inserção: **§2 ORDEM DE LEITURA DO PGR**, imediatamente após o bloco de `R-PGR-05`
(antes do separador `---` que abre a §3). Vizinha natural: `R-PGR-05` trata de PGR mal escrito;
esta trata de PGR bem escrito com nomenclatura própria.

---

## Texto a inserir

### R-PGR-07 — Nomenclatura de perigo não é padronizada `[DERIVADO — observação de campo do Diovanni (31/08/2026), corroborada por medição do acervo em 003.FF]`

Elaboradores de PGR **não seguem uma nomenclatura comum**. O mesmo perigo aparece escrito de
formas diferentes entre documentos, entre consultorias e **dentro do mesmo documento**. Não há
norma que padronize esses nomes: a NR-01 exige inventário de riscos, não um léxico controlado.

Caso âncora: **"Queda em altura" e "Trabalho em altura" designam o mesmo perigo.** O primeiro
nomeia a consequência, o segundo a exposição; engenheiros usam os dois indistintamente. A NR-35
define trabalho em altura como atividade acima de 2 m com risco de queda — o PGR que escreve
"Queda em altura" está declarando trabalho em altura.

**Consequências para a leitura, em ordem de importância:**

1. **Divergência de nomenclatura não é ausência de risco.** Termo do PGR que não casa o
   vocabulário é, até prova em contrário, **lacuna de cobertura do vocabulário** — nunca
   evidência de que o risco não existe. Ler o não-casamento como ausência inverte o sentido
   seguro da leitura (D-ARQ-31/35) e produz omissão de exame.
2. **Sinônimo não é erro de digitação.** Correção ortográfica (distância de edição) resolve
   `"Ergnômico"` → `"Ergonômico"`; **não** resolve `"Queda em altura"` → `trabalho_altura`.
   São dois problemas distintos e exigem dois mecanismos distintos. Tratar sinonímia com
   tolerância ortográfica só a torna mais permissiva sem alcançá-la.
3. **Variação de forma inclui prefixo, sufixo e ordem, não só a palavra-núcleo.** O mesmo
   conceito aparece qualificado (`"Sílica Livre - Poeira respirável"`), estendido
   (`"Levantamento e transporte manual de cargas ou volumes"`) ou circunstanciado
   (`"Trabalho sentado em computador com mobiliários sem meios de regulagem de ajuste"`).
   Comparação de string inteira contra uma lista curta de literais falha em todos os três.
4. **Nunca inferir o agente por proximidade de texto.** A conduta diante de termo não resolvido
   permanece a de `R-PGR-05` e `D-ARQ-14`: pendência nomeada, com o termo verbatim, endereçada a
   quem pode resolvê-la. Escolher um slug por semelhança é escolha de identidade silenciosa
   (D-ARQ-22) — o custo de errar o agente é exame errado emitido ou exame certo omitido.
5. **A sinonímia é do domínio, não de um setor.** Vale para construção civil, indústria química
   e saúde igualmente: o que muda entre setores é o repertório de perigos, não a ausência de
   padronização ao nomeá-los.

**Corroboração medida (003.FF, PGR ALT T65, 46 pág., 16 GHEs):** 98 ocorrências de termo não
resolvido, 45 formas distintas. Dessas, **57 ocorrências (58%) correspondem a 9 slugs que já
existem** em `agentes.yaml` — o vocabulário não carecia dos conceitos, carecia das formas. No
mesmo documento, `postura_inadequada` é escrito em **6 formas distintas** e
`"Sílica Livre - Poeira respirável"` em **3 grafias de caixa**. Detalhe em
`docs/referencia/MEDICAO_003FF_par_T65.md` §7.

**Efeito clínico medido do não-casamento, no mesmo documento:** `"Queda em altura"` (13
ocorrências) não resolveu para `trabalho_altura`, o predicado `altura` ficou `False` em todos os
GHEs, `R-PKG-ATIVCRIT` não disparou e **175 células de exame do gabarito assinado deixaram de ser
emitidas** — acuidade visual, hemograma, glicemia e ECG. A pendência `vocabulario_ausente` que
acompanha a omissão é **não-bloqueante**: o documento segue emitível com o exame faltando.
Se essa combinação (omissão de exame + pendência não-bloqueante) é a direção segura correta é
**decisão em aberto**, nomeada em `DT-003FF-04` — esta regra não a resolve, só a expõe.

---

## Linha de changelog a acrescentar na tabela de revisões

| v92 | <data da inserção> | Sessão 003.FF (CONHECIMENTO): **`R-PGR-07` CRIADA** (§2) — nomenclatura de perigo no PGR não é padronizada; o mesmo conceito aparece em formas distintas entre documentos e dentro do mesmo documento. Caso âncora `"Queda em altura"` ≡ `"Trabalho em altura"` (NR-35, atividade acima de 2 m com risco de queda). Cinco consequências de leitura: divergência de nomenclatura não é ausência de risco; sinônimo não é typo (mecanismos distintos); variação inclui prefixo/sufixo/ordem; nunca inferir agente por proximidade de texto (conduta segue `R-PGR-05`/`D-ARQ-14`); a sinonímia é do domínio, não de um setor. `[DERIVADO — observação de campo do Diovanni, corroborada por medição]`: no PGR ALT T65, 57 de 98 ocorrências não resolvidas (58%) correspondem a 9 slugs já existentes; `postura_inadequada` em 6 formas e `"Sílica Livre - Poeira respirável"` em 3 grafias, no mesmo documento. Efeito medido: `"Queda em altura"` (13×) não resolveu, `R-PKG-ATIVCRIT` não disparou, 175 células do gabarito não emitidas, com pendência não-bloqueante — direção segura dessa combinação fica em `DT-003FF-04`. Nenhuma R-* alterada ou depreciada; nenhum D-ARQ novo. |

---

## O que esta proposta NÃO faz, declarado

- **Não popula alias nenhum.** `agentes.yaml` não é tocado. Popular `termos:` é sessão de dado,
  e a própria regra diz por que a enumeração não fecha.
- **Não altera o critério de resolução.** `resolver_termo` (Levenshtein ≤ 2, `fuzzy_permitido`
  opt-in por slug) fica intacto. A cláusula 2 explica por que ele não é o instrumento da
  sinonímia; trocá-lo é decisão de arquitetura própria.
- **Não decide o bloqueio.** Se `vocabulario_ausente` que suprime exame deve continuar
  não-bloqueante é `DT-003FF-04`.
- **Não tem teste no motor, e não deveria ter.** A cobertura de teste por regra vale para regra
  que muda saída do motor. `R-PGR-07` é regra de **leitura** — governa como o Arquiteto e o
  elaborador interpretam divergência de nomenclatura, não um predicado. O teste aparece quando a
  cobertura de termo for implementada (fatia de dado), como reversão nomeada por slug.

## Pendências que esta proposta nomeia

- **`DT-003FF-04`** `[ABERTA — decisão de direção segura]` — `vocabulario_ausente` é
  não-bloqueante e, quando suprime um predicado de pacote, remove exame do documento emitido sem
  bloquear. Medido: 175 células no T65. Ou a pendência bloqueia quando alimenta predicado de
  pacote, ou a direção segura do projeto aceita omissão silenciosa nesse caminho — hoje aceita
  por omissão, não por decisão.
