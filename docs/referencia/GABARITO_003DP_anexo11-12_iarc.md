# Gabarito 003.DP — varredura `is_carcinogeno_iarc` / `tem_lt` (DT-003DL-01)

**Critério `is_carcinogeno_iarc`:** `true` para IARC Grupo 1 ou 2A; `false` para 2B, 3 e não-avaliados. Decidido em 003.DP.

**Critério `tem_lt`:** booleano; `true` se o agente consta do Anexo 11 (Quadro n.º 1) **vigente** ou tem LT em outro anexo da NR-15.

## Fontes

- IARC: `List_of_Classifications.pdf`, **Volumes 1–123 (2018)**. `[INCERTO — lista defasada]`: a vigente é vols 1–142 e é renderizada por JavaScript, não capturável por fetch simples. Reclassificações posteriores a 2018 não estão cobertas.
- IARC (corroboração, vigente): `Classifications_by_cancer_site.pdf`, vols 1–140, atualizado 21/11/2025 — usado para confirmar Grupo 1 de arsênio, tricloroetileno, óxido de etileno e fumos de solda.
- NR-15 Anexo 11: `nr-15-anexo-11.pdf` da página oficial de NRs vigentes (Quadro n.º 1, jornada 48h).
- **NÃO usado:** o PDF com Quadro I/LEO em `participamaisbrasil` é *proposta em consulta pública*, não norma vigente.

## A — Células que MUDAM (40 agentes)

| slug | iarc atual → novo | fonte IARC | tem_lt atual → novo | fonte NR-15 |
|---|---|---|---|---|
| `acetato_de_etila` | false → false | ausente da lista IARC (nunca avaliado) | false → true | Q1: Acetato de etila 310 ppm |
| `acetona` | false → false | ausente da lista IARC (nunca avaliado) | false → true | Q1: Acetona 780 ppm |
| `anilina` | false → false | Grupo 3 (vol 27, Sup 7) [INCERTO: vol 127/2021 reavaliou aminas aromaticas] | false → true | Q1: Anilina 4 ppm |
| `arsenio` | false → true | Grupo 1 - Arsenic and inorganic arsenic compounds | false → false | Q1 traz apenas Arsina; arsenio elementar ausente |
| `butadieno_13` | null → true | Grupo 1 - 1,3-Butadiene | null → true | Q1: 1,3 Butadieno 780 ppm |
| `butoxietanol_2` | null → false | Grupo 3 (vol 88) | null → true | Q1: Butil cellosolve 39 ppm (2-Butoxi etanol vide butil cellosolve) |
| `chumbo_tetraetila` | null → false | Lead compounds, organic - Grupo 3 | null → false | ausente do Q1 |
| `cianeto_de_hidrogenio` | false → false | ausente da lista IARC | false → true | Q1: Acido cianidrico 8 ppm |
| `ciclohexanona` | null → false | Grupo 3 (vol 47,71) | null → false | Q1 traz Ciclohexanol, nao ciclohexanona |
| `clorobenzeno` | null → false | ausente da lista IARC | null → true | Q1: Clorobenzeno 59 ppm |
| `diclorometano` | false → true | Grupo 2A (vol 110, 2017) | false → true | Q1: Cloreto de metileno 156 ppm |
| `dimetilacetamida` | null → false | ausente da lista IARC | null → true | Q1: Dimetilacetamida 8 ppm |
| `dimetilformamida` | null → true | Grupo 2A (vol 115, 2018) | null → true | Q1: Dimetiformamida 8 ppm |
| `dioxido_de_titanio` | true → false | Grupo 2B (vol 93, 2010) - abaixo do corte 1+2A | false → false | ausente do Q1 |
| `dissulfeto_de_carbono` | false → false | ausente da lista IARC | false → true | Q1: Dissulfeto de carbono 16 ppm |
| `estireno` | false → true | Grupo 2A (vol 121) | false → true | Q1: Estireno 78 ppm |
| `etilbenzeno` | false → false | Grupo 2B (vol 77) | false → true | Q1: Etilbenzeno 78 ppm |
| `etoxietanol` | null → false | ausente da lista IARC | null → true | Q1: 2-Etoxietanol 78 ppm |
| `etoxietilacetato` | null → false | ausente da lista IARC | null → true | Q1: Acetato de cellosolve 78 ppm |
| `fenol` | false → false | Grupo 3 (vol 47,71) | false → true | Q1: Fenol 4 ppm |
| `fluoretos` | false → false | Fluorides (inorganic, used in drinking-water) Grupo 3 | false → true | Q1: Acido fluoridrico 2,5 ppm [INCERTO: slug generico] |
| `furfural` | null → false | Grupo 3 (vol 63) | null → false | Q1 traz Alcool furfurilico, nao furfural |
| `hdi` | null → false | ausente da lista IARC | null → false | Q1 traz apenas TDI, nao HDI |
| `mercurio` | false → false | Mercury and inorganic mercury compounds - Grupo 3 | false → true | Q1: Mercurio (todas as formas exceto organicas) 0,04 mg/m3 |
| `metanol` | false → false | ausente da lista IARC | false → true | Q1: Alcool metilico 156 ppm |
| `metil_butil_cetona` | null → false | ausente da lista IARC | null → false | ausente do Q1 |
| `metoxietanol_2` | null → false | ausente da lista IARC | null → true | Q1: Metil cellosolve 20 ppm (2-Metoxi etanol vide metil cellosolve) |
| `metoxietilacetato_2` | null → false | ausente da lista IARC | null → false | ausente do Q1 |
| `mibk` | null → false | Grupo 2B - Methyl isobutyl ketone (vol 101) | null → false | Q1 traz Metil isobutilcarbinol (alcool), agente distinto [INCERTO] |
| `monoxido_de_carbono` | false → false | ausente da lista IARC | false → true | Q1: Monoxido de carbono 39 ppm |
| `n_metil_2_pirrolidona` | null → false | ausente da lista IARC | null → false | ausente do Q1 |
| `oxido_de_etileno` | null → true | Grupo 1 - Ethylene oxide | null → true | Q1: Oxido de etileno 39 ppm |
| `propanol_2` | null → false | Isopropyl alcohol Grupo 3 (o Grupo 1 e o PROCESSO 'isopropyl alcohol manufacture using strong acids') | null → true | Q1: Alcool isopropilico 310 ppm |
| `tdi` | null → false | 2,4-TDI Grupo 2B [INCERTO - nao confirmado no PDF lido] | null → true | Q1: 2,4 Diisocianato de tolueno (TDI) 0,016 ppm |
| `tetracloroetileno` | null → true | Grupo 2A - Tetrachloroethylene (vol 106, 2014) | null → true | Q1: Percloroetileno 78 ppm |
| `tetrahidrofurano` | null → false | Grupo 2B (vol 119) | null → true | Q1: Tetrahidrofurano 156 ppm |
| `tolueno` | false → false | Grupo 3 (vol 47,71) | false → true | Q1: Tolueno (toluol) 78 ppm |
| `tricloroetano_111` | null → false | Grupo 3 (vol 20, Sup 7, 71) | null → true | Q1: Metilclorofórmio 275 ppm (1,1,1 Tricloroetano vide metil clorofórmio) |
| `tricloroetileno` | false → true | Grupo 1 - Trichloroethylene (vol 106, 2014) | false → true | Q1: Tricloroetileno 78 ppm |
| `xileno` | false → false | Xylenes Grupo 3 (vol 47,71) | false → true | Q1: Xileno (xilol) 78 ppm |

## B — Escalar antes de gravar (5 agentes)

| slug | iarc atual → novo | fonte IARC | tem_lt atual → novo | fonte NR-15 |
|---|---|---|---|---|
| `benzeno` | true → true | Grupo 1 (vol 100F) | null → **ESCALAR** | excluido do Q1 pela Portaria 03/1994; regime proprio no Anexo 13-A (VRT, nao LT) [ESCALAR] |
| `chumbo` | false → **ESCALAR** | AMBIGUO: Lead (metal) 2B; Lead compounds, inorganic 2A -> criterio 1+2A daria True p/ inorganicos [ESCALAR] | false → true | Q1: Chumbo 0,1 mg/m3 |
| `etanol` | false → **ESCALAR** | ESCALAR: entrada IARC e 'Ethanol in alcoholic beverages' Grupo 1 (ingestao), nao exposicao ocupacional a etanol | true → true | Q1: Alcool etilico 780 ppm |
| `fumos_metalicos` | false → **ESCALAR** | ESCALAR: Welding fumes e Grupo 1 (vol 118, 2017), mas slug e 'fumos metalicos' generico, nao fumos de solda | true → true | MANTIDO do disco; nao localizado no Q1 [INCERTO] |
| `inseticidas_inibidores_colinesterase` | false → **ESCALAR** | ESCALAR: 'Non-arsenical insecticides (occupational exposures in spraying and application)' e Grupo 2A - classe adjacente | false → false | classe, sem LT proprio no Q1 |

## C — Já corretos, confirmados (11 agentes)

| slug | iarc atual → novo | fonte IARC | tem_lt atual → novo | fonte NR-15 |
|---|---|---|---|---|
| `asbesto` | true → true | Grupo 1 - Asbestos (all forms) | true → true | Anexo 12 (poeiras minerais/asbestos) |
| `cadmio` | true → true | Grupo 1 - Cadmium and cadmium compounds | false → false | ausente do Q1 |
| `cloreto_de_hidrogenio` | false → false | Hydrochloric acid - Grupo 3 | true → true | Q1: Acido cloridrico 4 ppm |
| `cobalto` | false → false | Grupo 2B (Cobalt and cobalt compounds) | false → false | ausente do Q1 |
| `cromo_hexavalente` | true → true | Grupo 1 - Chromium(VI) compounds | false → false | Q1 traz apenas Acido cromico (nevoa); Cr-VI nao nominal [INCERTO] |
| `indutores_metahemoglobina` | false → false | classe de agentes, sem entrada IARC propria | false → false | classe, sem LT proprio no Q1 |
| `manganes` | false → false | ausente da lista IARC | false → false | ausente do Q1 (Anexo 13 e qualitativo, nao LT) |
| `metil_etil_cetona` | false → false | ausente da lista IARC | true → true | Q1: metil etil cetona 155 ppm |
| `n_hexano` | false → false | ausente da lista IARC | false → false | AUSENTE do Q1 vigente - REFUTA a suspeita da DT (50 ppm so na proposta em consulta publica) |
| `nitrobenzeno` | false → false | Grupo 2B (vol 65) | false → false | ausente do Q1 |
| `silica` | true → true | Grupo 1 - Silica dust, crystalline (quartz/cristobalite) | true → true | Anexo 12 (poeiras minerais) |

## D - Fora do escopo de varredura, mas com achado (nao-quimicos)

Os 23 agentes nao-quimicos do vocabulario (`ruido`, `vibracao*`, `postura_inadequada`, `trabalho_altura`, ...) tem os 2 campos categoricamente inaplicaveis - IARC nao classifica postura, e LT de ruido/vibracao vive em anexo proprio. (Contagem: 23 nao-quimicos + 56 quimicos = 79 slugs; `fumos_metalicos` conta como quimico apesar de nao ter `cas`/`tipo_ibe`.) **Excecao encontrada:**

- **`radiacao_uv_ir`** esta `is_carcinogeno_iarc: false`, mas a radiacao ultravioleta e **IARC Grupo 1** (`Solar radiation`; `Ultraviolet-emitting tanning devices`; `Ultraviolet emissions from welding`, este ultimo com sitio ocular). O slug agrega UV e IR, que tem status distintos - **decisao de vocabulario, nao de varredura**: ou se separa UV de IR, ou se grava `true` com nota de que o gatilho vem do componente UV.

- Os demais 23 permanecem como estao. Recomendacao: `null` semantico em vez de `false`, para nao afirmar 'verificado, nao tem' sobre campo que nao se aplica. Fica como decisao propria, fora desta sessao.

---

# Adendo — passada de verificação por cruzamento programático

O Quadro 1 vigente foi parseado (205 registros, 235 formas indexadas, cadeias `vide` resolvidas) e cruzado contra os 56 slugs. **Ausência passou a ser resultado de busca, não de leitura visual.** 10 divergências contra o gabarito v1, julgadas abaixo.

## D.1 — Falsos positivos do fuzzy (v1 estava certo, v2 errado)

| slug | casou com | score | veredito |
|---|---|---|---|
| `ciclohexanona` | `Ciclohexano` | 0.917 | **rejeitar** — ciclohexanona ≠ ciclohexano ≠ ciclohexanol, três agentes distintos |
| `metil_butil_cetona` | `metil etil cetona` | 0.914 | **rejeitar** — MBK ≠ MEK |

Reprodução exata da lição de DT-003DM-01 numa ferramenta de análise: similaridade lexical alta entre agentes químicos distintos. Vale como 3ª testemunha do princípio.

## D.2 — Sinonímia química real que o fuzzy não alcança (v1 certo, mas era inferência não registrada)

| slug | entrada do Quadro 1 | observação |
|---|---|---|
| `cianeto_de_hidrogenio` | `Ácido cianídrico` (8 ppm) | HCN = ácido cianídrico; distância lexical grande, equivalência química sólida |
| `cloreto_de_hidrogenio` | `Ácido clorídrico` (4 ppm) | HCl = ácido clorídrico |
| `etoxietilacetato` | `Acetato de cellosolve` (78 ppm) | nome comercial histórico |

**Estas três eu havia resolvido de cabeça no v1, sem registrar.** São exatamente a matéria da Tier 1 de aliases — devem virar `termos:` explícitos com fonte, não decisão silenciosa de varredura.

## D.3 — Erro real do gabarito v1

- **`fluoretos`**: v1 gravava `true` via `Ácido fluorídrico`. **Fluoretos ≠ ácido fluorídrico.** Corrigir para `false`, ou tratar como agente que exige alias próprio.

## D.4 — Fora do alcance desta verificação

- **`asbesto`, `silica`**: v1 marca `true` via Anexo 12. O Anexo 12 **não foi lido** — a afirmação segue sem fonte verificada. `[INCERTO]`
- **`fumos_metalicos`**: sem entrada no Quadro 1; v1 apenas herdou `true` do disco. Segue em ESCALAR.
- **`benzeno`**: consta do Quadro 1 mas **excluído** pela Portaria 03/1994. Segue em ESCALAR.

## D.5 — Defeitos no PDF oficial do Anexo 11 (achado colateral)

O texto vigente publicado tem remissivas quebradas:

- `Etanol (vide acetaldeído)` — **remissiva factualmente errada**; etanol não é acetaldeído. Há uma segunda entrada `Etanol (vide etílico)`, truncada de "álcool etílico". O cruzamento automático resolve `etanol` para **Acetaldeído**, o que é errado; o valor correto vem de `Álcool etílico` (780 ppm).
- `Diclorometano (vide cloreto de metilino)` — typo de "metileno".
- `1,1,1 Tricloroetano (vide metil clorofórmio)` vs. entrada grafada `Metilclorofórmio`.

Consequência: **qualquer resolução automática sobre o Anexo 11 precisa de tratamento para essas três entradas**, senão grava valor errado com aparência de derivação limpa.

---

# Adendo 2 — Anexo 12 lido (fonte primária)

`nr-15-anexo-12.pdf`, página oficial de NRs vigentes. O Anexo 12 tem **três** blocos, não um:

| bloco | LT | efeito |
|---|---|---|
| **ASBESTO** (Portaria SSST 01/1991) | 2,0 f/cm³ para fibras respiráveis de crisotila (item 12) | `asbesto` → `tem_lt: true` **CONFIRMADO com fonte** |
| **SÍLICA LIVRE CRISTALIZADA** (Portaria DNSST 08/1992) | fórmula `8/(%quartzo+2)` mg/m³ para poeira respirável | `silica` → `tem_lt: true` **CONFIRMADO com fonte** |
| **MANGANÊS E SEUS COMPOSTOS** (Portaria DNSST 08/1992) | 5 mg/m³ (extração/moagem/transporte); 1 mg/m³ (metalurgia, eletrodos de solda, tintas) | **`manganes` → `tem_lt: true`** |

## Correção do gabarito v1

**`manganes` estava `false` no v1** — justificado como "ausente do Q1; Anexo 13 é qualitativo, não LT". **Errado.** O manganês tem LT numérico próprio, no Anexo 12. Vira `true`.

Segundo erro real do v1 encontrado por verificação (o primeiro foi `fluoretos`). Ambos vieram de eu ter afirmado ausência sem ler a fonte inteira.

## Achado colateral — matéria de PROTOCOLO, não de vocabulário

O item 18 do bloco ASBESTO fixa conduta clínica diretamente: exames **admissional, demissional e anual** com avaliação clínica + **telerradiografia de tórax** (padrão OIT-1980) + **espirometria**; e o item 19 obriga o empregador a manter exames periódicos por **30 anos após o fim do contrato**, com periodicidade escalonada por tempo de exposição (3 anos até 12 anos de exposição; 2 anos entre 12 e 20; anual acima de 20).

Isto é regra clínica derivável de fonte normativa primária, com periodicidade explícita — candidata a `R-*` própria. **Fora do escopo desta sessão**; registrar como dívida de CONHECIMENTO para verificar se o protocolo já a cobre (checar antes de criar ID nova).
