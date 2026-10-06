# Medição — 1º e2e da rota grid no app: Hetrin REV06 × matriz 14.09.26

`[MEDIDO — 05/10/2026, sessão branch claude/gifted-cerf-0loir2]`

## Entrada e proveniência

- **PGR:** `matrizes_originais/PGR_RICCO_2026_REV06.pdf` (= Hetrin set-2026, págs. 0-196, + adendo de funções faltantes, págs. 197-216).
- **Rodado por:** Diovanni, no app de produção (Streamlit Cloud), sobre `main 3207c80` (PR #450 — rota grid ligada, sem os aliases do PR #451).
- **Saída do app, versionada aqui sem alteração** (sha256 conferido contra o arquivo recebido):
  - `e2e_hetrin_rev06_20261005/matriz_app.docx` — `21e78127d1fc7ee2…`
  - `e2e_hetrin_rev06_20261005/memorial_app.docx` — `43f1d70328039ce1…`
- **Tela do app (print):** "30 bloco(s) lido(s) por IA"; processamento 106 s (IA 67 s em 30 blocos; leitura do PDF e montagem 38 s; motor 0,0 s); 5 respostas de `gemini-3.8-flash`, tokens de entrada 38.797, de saída 25.823.
- **Gabarito:** `matrizes_originais/MATRIZ DE EXAMES(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.doc` (Dra. Patrícia Montalvo Moraes), par 17 do `PAREAMENTO_ACERVO.md`.

## Resultado do app

**Leitura (rota grid, `D-ARQ-57` peça 5): funcionou.** 30 grupos (22 do corpo + 8 do adendo), na ordem do PGR. Nomes com o espaçamento da extração consertado ("CARPINTEIRO", "ENCARREGADO DE ENCANADOR", "ENCARREGADO DE INSTALAÇÕES ELÉTRICA E HIDROSSANITÁRIAS"). Cargos separados como na matriz: 5 no grupo N:1 da pág. 14 (com "APONTADOR ADMINISTRATIVO DE OBRA" como um cargo), 2 em "AUXILIAR DE SERVIÇOS GERAIS/ SERVIÇOS GERAIS", 2 em "VIGIA DIURNO/ VIGIA NOTURNO".

**Matriz: pobre.** 40 exames em 30 GHEs; a maioria só com o Exame Clínico. Memorial: **514 riscos não reconhecidos, 47 grafias distintas**. Quatro grafias que disparam exame não casavam com o vocabulário:

| Grafia (transcrição do app) | Grupos | Slug esperado |
|---|---|---|
| RUÍDO CONTÍNUO OU INTERMITENTE | 29 de 30 | `ruido` |
| POEIRA - PNOS | 29 | `poeira_nao_classificada` |
| QUEDAS DE ALTURA | 28 | `trabalho_altura` |
| VIBRAÇÕES LOCALIZADAS (MÃOS E BRAÇOS) / (BRAÇO E MÃOS) | 1 cada | `vibracao_mao_braco` |

Correção: aliases ancorados em norma, PR #451 (`D-ARQ-70`, nota de aplicação; DECISOES v243).

## Replay (estimativa do efeito dos aliases)

**Método.** Para cada GHE, os riscos foram reconstruídos do memorial do app: os termos "não reconhecidos" mais a "Origem" dos exames emitidos. Cada GHE virou um `GHEVerbatim` com esses termos, passou por `hidratar_pgr` e `processar_pgr` (motor real, protocolo do repositório), e o conjunto de exames de cada cargo foi comparado com o da matriz 14.09.26 (conversão do `.doc` por `soffice --convert-to txt`), nas 22 funções do corpo. Script no apêndice.

**Limites.** (1) Estimativa, não teste no app: o replay não refaz a transcrição. (2) Compara só presença do exame; periodicidade e momentos não. (3) A conversão para `txt` é a que distorce célula (ver `VALIDACAO_LIBREOFFICE_vs_WORDCOM.md`); o instrumento versionado, `scripts/comparar_matriz_gabarito.py`, lê `.docx` como tabela e não tem essa ressalva, mas ainda não aceita a matriz exportada pelo app como entrada. (4) Ruído do comparador: o nome do RX de coluna difere entre os lados, e linhas como "(Obs no corpo do email)" entram como exame.

| | Células do gabarito ausentes | Células a mais |
|---|---|---|
| Vocabulário de `main 3207c80` (antes) | 195 | 2 |
| Com os aliases do PR #451 (depois) | 29 (6 de ruído do comparador) | 26 (24 de `avaliacao_psicossocial`, `R-PSY-04`; 2 de ruído) |

O que diverge depois dos aliases está em `PENDENCIAS_CLINICAS.md`, `DT-(sessão claude/gifted-cerf-0loir2)-01`.

## Comparação pelo instrumento versionado (matriz do app × 14.09.26)

`[MEDIDO — 06/10/2026, branch claude/kind-bardeen-ajkpnr, sobre main 11748c3]`

```
python -m scripts.comparar_matriz_gabarito --matriz-app \
    docs/referencia/e2e_hetrin_rev06_20261005/matriz_app.docx \
    "matrizes_originais/MATRIZ DE EXAMES(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.doc" <relatorio.md>
```

- cargos: app 36, gabarito 28, pareados por nome 26
- células (cargo × exame): app 46, gabarito 241
- cargos com conjunto de exames idêntico: 0 de 26
- células do gabarito reproduzidas por identidade de exame: 52 = 21,6%
- superemissão: 0 · subemissão: 189 · divergência de momentos: 7 · de periodicidade: 0

Subemissão por exame: `ecg`, `espirometria`, `glicemia`, `hemograma`, `rx_torax_oit` 26 cada; `acuidade_visual` 25; `audiometria` 19; `acetona_urina`, `ciclohexanol_urina`, `mek_urina`, `tetrahidrofurano_urina` 3 cada (almoxarife, encanador, montador); `manganes_sangue` 2; `carboxihemoglobina` 1. Momentos: as 7 são audiometria sem `DEM` no app (gabarito com `DEM`). Periodicidade 0 porque o app não imprimiu prazo em nenhuma célula desta matriz — não é concordância.

**Cargos sem par** (visíveis, não contados como divergência): só no gabarito `encarregado`, `engenheiro presidente`; só no app `encarregados`, `engenheiro residente` e os 8 grupos do adendo (`auxiliar administratvo`, `encarregado de armação`, `… de carpinteiro`, `… de eletricista`, `… de encanador`, `… de instalações elétrica e hidrossanitárias`, `… de obra`, `menos aprendiz`), que a matriz 14.09.26 não tem.

**Contra o "antes" do replay (195 ausentes / 2 a mais, 22 funções).** Mesma ordem de grandeza, número diferente: 189 / 0 em 26 cargos pareados. Fontes de diferença conhecidas: tabela em vez de `txt`, pareamento por cargo em vez de por nome de GHE, e o ruído que o replay registrou (nome do RX de coluna, linhas "Obs" como exame). Reconciliação célula a célula `[A MEDIR]` — não foi feita; o número do instrumento é o que vale daqui em diante.

**Grafias do gabarito que o instrumento passou a resolver nesta sessão** (`_ALIAS_GRAFIA`, forma de saída, não decisão clínica): "Acetona" → `acetona_urina`, "Metiletilcetona" → `mek_urina`, "Manganês Sanguíneo" → `manganes_sangue`. Sem elas, 8 células saíam com nome cru e virariam super + sub falsas assim que o app emitir esses IBEs (2º teste, FDS do adesivo).

## Próximo passo

1. ~~Estender `scripts/comparar_matriz_gabarito.py` para aceitar a matriz DOCX exportada pelo app.~~ Feito (`--matriz-app`), seção acima.
2. 2º teste no app, com os aliases em produção e a FDS do adesivo PVC anexada na etapa 2. Comparar pelo instrumento do passo 1. Fecha `DT-(sessão claude/youthful-lamport-3kfkog)-02`.

## Apêndice — script do replay

Rodado da raiz do repositório com `PYTHONPATH=.`. `SP` apontava para o diretório com `memorial.txt` (texto do `memorial_app.docx`, um parágrafo por linha com prefixo `P: ` e uma linha por célula de tabela com prefixo `T<n>: `) e com a conversão `txt` do gabarito.

```python
import re,sys
from datetime import date
from pathlib import Path
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim
SP="/tmp/claude-0/-home-user-automacao-pgr-agente-pcmso/a7d75656-a80a-5d54-bc16-4a6400cb2c6f/scratchpad/"
L=[l.rstrip("\n") for l in open(SP+"e2e/memorial.txt",encoding="utf-8")]
ghes=[];atual=None
for l in L:
    m=re.match(r"P: (GHE-\d+) — (.+)$",l)
    if m: atual=[m.group(2),[]]; ghes.append(atual); continue
    m=re.match(r"P: (.+?): (sem correspondência|parece )",l)
    if m and atual: atual[1].append(m.group(1))
for l in L:
    m=re.match(r"T(\d+): .*?Origem: (.+?) — PGR",l)
    if m:
        for o in re.findall(r"Origem: (.+?) — PGR",l): 
            for t in o.split("; "): 
                if t not in ghes[int(m.group(1))][1]: ghes[int(m.group(1))][1].append(t)
p=carregar(Path("agente_medico/protocolo"))
idx=construir_indice_termos(p.vocabulario.agentes, fracoes_sem_agente=p.vocabulario.fracoes_sem_agente)
vs=[GHEVerbatim(nome=n,cargos=(n,),riscos=tuple(RiscoVerbatim(t,"","") for t in rs)) for n,rs in ghes]
pgr,_=hidratar_pgr(vs,idx,date.today(),True)
res=processar_pgr(pgr,p)
for (n,_),m in zip(ghes,res.matrizes):
    print(n[:45].ljust(46), sorted({e.exame for e in m.linhas}))

import subprocess
txt=subprocess.run(["iconv","-f","latin1","-t","utf-8",SP+"doc/MATRIZ DE EXAMES(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.txt"],capture_output=True,text=True).stdout
MAP={"Exame Clínico":"exame_clinico","Audiometria":"audiometria","Acuidade Visual":"acuidade_visual","ECG":"ecg","Glicemia de Jejum":"glicemia","Hemograma":"hemograma","Espirometria":"espirometria","RX de Tórax OIT":"rx_torax_oit"}
gab={};f=None
for l in [x.strip() for x in txt.splitlines() if x.strip()]:
    nome=l.split(" (")[0]
    if nome in MAP: gab[f].add(MAP[nome]); continue
    if "(" in l and f: gab[f].add("OUTRO:"+nome); continue
    if l in ("FUNÇÃO","EXAMES SOLICITADOS") or ":" in l or "Obs" in l: continue
    f=l.lower(); gab[f]=set()
print("\n== diferenças por função (gabarito 14.09.26 × replay) ==")
import unicodedata
def k(s): return unicodedata.normalize("NFKD",s.lower()).encode("ascii","ignore").decode().replace(" ","")
emit={}
for (n,_),m in zip(ghes[:22],res.matrizes[:22]):
    for c in n.split("/"): emit[k(c.strip())]=({e.exame for e in m.linhas})
fal=sob=0
for f,ex in gab.items():
    e=emit.get(k(f.rstrip()))
    if e is None: print("SEM PAR:",f); continue
    falta=sorted(x for x in ex if x not in e); sobra=sorted(e-{x for x in ex})
    fal+=len(falta); sob+=len(sobra)
    if falta or sobra: print(f"{f[:34]:35} falta={falta} sobra={sobra}")
print("células faltando:",fal,"sobrando:",sob)
```
