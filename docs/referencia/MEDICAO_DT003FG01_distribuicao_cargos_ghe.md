# Medição — DT-003FG-01: distribuição de cargos por GHE (gabarito assinado × parse do motor)

`[MEDIDO — 23/09/2026, branch claude/hopeful-newton-yjv3k7, sobre main 9782074]`
Sessão de MEDIÇÃO apenas: nenhum código de produção, teste ou `.yaml` tocado.

## Pergunta

`DT-003FG-01` herdou do legado (`_suspeitar_distribuicao_incorreta`, `43a61bf`) dois critérios
sem proveniência: **(a)** algum GHE com ≥ 10 cargos; **(b)** > 30% dos GHEs com lista de cargos
idêntica. A DT exige medi-los contra o acervo antes de qualquer implementação: qual o máximo de
cargos por GHE num gabarito assinado, e qual a taxa real de GHEs com lista idêntica.

## Lado 1 — gabaritos assinados (`matrizes_originais/*.doc|*.docx`)

**Conjunto.** 41 arquivos Word. `.doc` → `.docx` por LibreOffice headless (caminho validado em
`VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`); `libreoffice-writer` instalado no container nesta sessão.
Excluídos por **não serem matriz** (corpo inteiro de PCMSO/PGR, sem cabeçalho de GHE por tabela):
`PCMSO Fazenda Jamaica` ×3, `PCMSO_Ricco_Construtora_Ltda.`, `PGR VIVERDE V02`, `PCMSO - NOVO
MODELO- SECONCI`. Removida 1 duplicata de conteúdo idêntico (`RICCO HETRIN 23.05.2025` = `(2)`).
**Restam 34 matrizes, 455 grupos com cargo, 1421 linhas de cargo.** Ressalva: o conjunto ainda
contém quase-duplicatas (as duas `CONSCIENTE RESERVA 0028`) e 1 cópia parcial
(`RICCO HETRIN 23.05.2025 (1)`, 5 cargos); nenhuma afeta as conclusões abaixo.

**Dois layouts de agrupamento, medidos.** 16 matrizes agrupam por `GHE NN`; 18 agrupam por
`SETOR:`. Em 5 das de `SETOR`, o agrupamento é plano (1–2 setores com 28–63 cargos:
`RICCO HETRIN` 63, `CONSCIENTE RESERVA 0028` 44, `TOCTAO PORTO ARARAS I` 33, `RICCO HETRIN
14.09.26` 28). Ou seja: **a própria matriz assinada nem sempre é organizada por GHE** — o GHE
mora no PGR, e a matriz pode ser uma lista cargo→exames.

### Critério (a) — ≥ 10 cargos num GHE: **REFUTADO**

| recorte | máx. cargos/grupo | grupos ≥ 10 | matrizes com algum ≥ 10 |
|---|---|---|---|
| só layout `GHE NN` (16 matrizes) | **19** | 7 | **4 de 16** |
| todos os layouts (34) | 63 | 19 de 455 | 13 de 34 |

Os grupos grandes em layout GHE são **administrativos legítimos**, nomeados cargo a cargo e
assinados: `VILA BRASIL` GHE 01 ADMINISTRAÇÃO 01 (19), `PORTO ARARAS 1` GHE 09 ADMINISTRAÇÃO
(16), `DINAMICA` GHE 06 ADMINISTRAÇÃO (15), `VILA BRASIL` GHE 04 MARKETING (13) e GHE 08
ADMINISTRAÇÃO 03 (12), `DINAMICA` GHE 03 PLANEJAMENTO (10), `SECONCI GOIÁS` GHE 11 MEDICINA (10). O limiar 10
dispararia em 4 de 16 matrizes corretas por construção.

### Critério (b) — > 30% dos GHEs com lista idêntica: **frágil, não discrimina**

Taxa de GHEs cuja lista de cargos repete a de outro GHE, nas 6 matrizes em que é > 0:

| matriz | % GHEs com lista idêntica |
|---|---|
| CMO VISTAMERICA 28.07.26 | **28,6%** (8/28) |
| CMO VARANDAS BUENO 11.08.25 | 25,6% (10/39) |
| TEC GRUA 05.04.2024 | 25,0% (2/8) |
| CMO FLORAMAZONIA 04.04.2025 | 18,2% (2/11) |
| DINÂMICA C239 MUY BUENO | 9,5% (2/21) |
| DINAMICA SOFT PEDRO LUDOVICO | 8,7% (2/23) |

A repetição é **legítima e estrutural**: construtoras (CMO) dividem a produção em GHEs por frente
de serviço com os mesmos cargos e riscos diferentes (`pedreiro/meio oficial de pedreiro/servente`
em PRODUÇÃO 01/02/04/05/…; `operador de grua` em GRUA 01 externo / GRUA 02 interno). O máximo
medido fica **1,4 p.p.** abaixo do limiar herdado — um GHE de produção a mais no Vistamerica
(9/29 = 31%) já dispararia.

## Lado 2 — parse do motor sobre os PGRs do acervo

**Método.** `preparar_ghes` (`agente_medico/adaptadores/orquestracao_pgr.py`) com
`TranscritorGHEOffline`/`TranscritorCardOffline` — rota determinística apenas, sem LLM
(D-ARQ-65). 29 PDFs de PGR em `matrizes_originais/`.

| desfecho | PGRs |
|---|---|
| bloqueado — `familia_nao_medida` + `transcricao_indisponivel_pgr` (iria para LLM) | 14 |
| bloqueado — `segmentacao_implausivel` (gate anti-Vistamérica, D-ARQ-57 peça 2) | 8 |
| bloqueado — `pgr_cargo_based` | 3 |
| bloqueado — `transcricao_indisponivel_pgr` (rota card) | 1 |
| **atravessa a rota determinística** | **3** |

Os 3 que atravessam: **Fascino** (19 GHEs, 41 cargos), **Vila Brasil Escritório** (4 GHEs, 5
cargos) e **Porto Araras I** (15 GHEs, 51 cargos).

### Achado — Porto Araras I atravessa com parse errado e sem pendência nenhuma

Conferido contra o texto do PDF (`pdfplumber`, 102 páginas) e contra o gabarito pareado
(`PAREAMENTO_ACERVO.md` par 6, confiança ALTA):

1. **GHE perdido.** O PDF tem 16 GHEs; o motor devolve 15. Falta `GHE - 14 PINTURA` (pág. 66,
   cargo `Pintor`), cuja forma tem o número **depois** do hífen. `eh_cabecalho_ghe("GHE - 14
   PINTURA")` → `False`, enquanto `"GHE 13 - …"` e `"GHE 15 - …"` → `True`. As duas rotas usam
   o mesmo reconhecedor, então as duas contam 15, a checagem `len(candidatos) == len(blocos)`
   passa e a rota determinística é aceita. O cargo `Pintor` — o que carrega os solventes
   (tolueno, xileno, metiletilcetona, acetona segundo a anotação do gabarito) — **some da
   matriz sem pendência**.
2. **Nomes de cargo truncados na quebra de linha.** 26 de 51 cargos terminam em preposição
   (`Operador de`, `Meio Oficial de`, `Encarregado de` ×5, `Técnico de Segurança do`, …) e
   outros saem cortados sem preposição final (`Analista`, `Engenheiro`, `Vigia` ×2, `Tecnico
   em`). Mesma classe do TOCTAO em `DH-003EW-02` — lá o sanity-check recusava a família; aqui
   **não recusa**.

É o modo de falha que `DH-003EW-02` chama de pior do sistema: matriz plausível e errada.

### Sinais que separam o parse ruim do gabarito correto

| sinal | gabaritos (1421 cargos, 34 matrizes) | Fascino + Vila Brasil (46 cargos) | Porto Araras (51 cargos) |
|---|---|---|---|
| (a) GHE com ≥ 10 cargos | 4/16 matrizes de layout GHE | 0 | 1 GHE (16, legítimo) |
| (b) % GHEs com lista idêntica | até 28,6% | 0% | 20% (3/15 — **efeito** do truncamento) |
| **cargo terminado em preposição** | **0** | **0** | **26** |
| **cargo repetido no mesmo GHE** | **1** (`assistente de vendas` ×2, Toctao — duplicata real do documento humano) | **0** | **6** |

Os dois sinais de baixo discriminam no acervo medido; os dois herdados não.

**Limite da evidência.** O lado motor tem **n = 1 parse ruim e n = 2 parses bons**. O sinal
de preposição não pega truncamento sem preposição final (`Analista`, `Vigia`), e nenhum dos
sinais pega o GHE perdido (item 1 acima), que é defeito do reconhecedor de cabeçalho, não de
distribuição. Qualquer limiar sai daqui como hipótese, não como número validado.

## Reprodução

Scripts de medição (descartáveis; o que vale é o método — versionar como instrumento é parte da
decisão de implementar):

```python
# agrupar2.py — gabarito .docx → {cabeçalho GHE/SETOR: [cargo normalizado]}
# reusa _PADRAO_GHE, _RODAPE, normalizar_cargo, _celulas_logicas de scripts/comparar_matriz_gabarito.py
def agrupar(p):
    d = Document(str(p)); ghes = {}; atual = None
    for t in d.tables:
        for r in t.rows:
            c = _celulas_logicas(r.cells)
            while c and not c[0]:          # layout GPL: 1ª coluna vazia
                c = c[1:]
            if not c:
                continue
            if _PADRAO_GHE.match(c[0]):
                atual = re.sub(r"\s+", " ", c[0]).strip(); ghes.setdefault(atual, []); continue
            if atual is None or len(c) < 2 or _RODAPE.match(c[0]):
                continue
            ghes[atual].append(normalizar_cargo(c[0]))
    return ghes
```

```python
# motor_dist.py — PGR .pdf → GHEVerbatim (rota determinística)
ghes, pend = preparar_ghes(pdf, TranscritorGHEOffline(), TranscritorCardOffline())
```

Sinal de preposição: `re.compile(r"\b(de|do|da|dos|das|em|e)\.?\s*$", re.I)` sobre o nome cru.
Repetição no GHE: `Counter` sobre o nome sem espaços nas pontas, contagem > 1.
