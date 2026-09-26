# Prompt cirurgico — imprimir periodicidade na celula da matriz (`DT-003EW-02`)

Modo: IMPLEMENTACAO. Alvo: apresentacao. **Nao toca motor, protocolo clinico nem R-*.**
Nota de aplicacao em `D-ARQ-73` (emissor de saida no formato do escritorio).

---

## Contexto

`ExameEmitido.periodicidade_meses: int` ja existe e ja e calculado pelo motor.
`documento_matriz.py::_formatar_celula` monta `f"{nome_exibicao} ({momentos})"` e **nunca le
esse campo** `[MEDIDO — 003.EY, nota aditiva de DT-003EW-02: `git grep -c periodicidade --
agente_medico/superficie/documento_matriz.py` = 0]`. A causa ja esta isolada: e apresentacao,
nao valor do motor.

## A regra — MEDIDA no acervo, nao derivada

`[MEDIDO — 28/08/2026, 6 gabaritos assinados: SPE 0030 08.07.26, VISTAMERICA 28.07.26,
ENTREVERDES 20.07.26, PORTO ARARAS 06.07.26, SPE T65 08.07.26, VILA BRASIL 26.08.26.
547 ocorrencias de periodicidade.]`

1. **O numero gruda sempre no momento `PER`.** 547 de 547 ocorrencias em `PER`;
   **zero** em ADM/MRO/RET/DEM. Formato literal: `PER 24 meses`.
2. **Imprime quando `periodicidade_meses != 12`.** Espirometria (24M) imprime em 190 de 190;
   biomonitoramento (6M) imprime sempre; Exame Clinico imprime `6 meses` quando cai para
   semestral por quimico, e sai sem numero quando e 12M.
3. **Excecao unica e nomeada: `rx_torax_oit` imprime sempre**, inclusive a 12M
   (12M em 31 + 60M em 2 no SPE 0030; 12M em 22 + 60M em 38 na Vistamerica). E o unico exame
   com periodicidade roteada por faixa que carrega o numero mesmo quando ele e 12.
4. **Sem `PER` na linha, sem numero** — `RX da Coluna Lombo-sacra` sai `(ADM, MRO)`.

Acerto da regra sobre o medido: **545 de 547 (99,6%)**. As 2 divergencias sao `Hemograma`
com `12 meses` explicito em ENTREVERDES (2 de 48 ocorrencias de Hemograma naquele documento),
dentro da classe de ruido de edicao ja catalogada. `[INTERPRETADO — prioridade na revisao de saida]`

## Implementacao — 3 arquivos

### 1. `agente_medico/protocolo/vocabulario/exames.yaml`

Acrescentar UM campo na entrada `rx_torax_oit` (linha 73), preservando os demais:

```yaml
  rx_torax_oit:
    nome_exibicao: "RX Torax OIT"
    categoria: imagem
    fonte_matriz: "SILICA / ASBESTO / POEIRAS"
    ordem_exibicao: 12
    periodicidade_sempre_visivel: true   # medido 28/08: unico exame que imprime o numero a 12M
```

Ausencia do campo = `false`. Nenhuma outra entrada recebe o campo nesta fatia.
(`D-ARQ-07`: protocolo e dado, nao codigo — a excecao mora no YAML, nao num literal no emissor.)

### 2. `agente_medico/superficie/documento_matriz.py`

`_formatar_momentos` passa a receber a periodicidade e um booleano:

```python
def _formatar_momentos(exame: ExameEmitido, mostrar_periodicidade: bool) -> str:
    presentes = [m for m in _ORDEM_MOMENTOS if m in exame.momentos]
    partes = []
    for m in presentes:
        rotulo = _ROTULO_MOMENTO[m]
        if m is Momento.PER and mostrar_periodicidade:
            rotulo = f"{rotulo} {exame.periodicidade_meses} meses"
        partes.append(rotulo)
    return ", ".join(partes)


def _formatar_celula(exame: ExameEmitido, exames_vocab: dict[str, Any]) -> str:
    entrada = exames_vocab.get(exame.exame, {})
    nome_exibicao = entrada.get("nome_exibicao", exame.exame)
    mostrar = exame.periodicidade_meses != 12 or bool(
        entrada.get("periodicidade_sempre_visivel", False)
    )
    return _sanitizar(f"{nome_exibicao} ({_formatar_momentos(exame, mostrar)})")
```

Manter type hints e o `_sanitizar` existente. Sem comentario obvio; o docstring do modulo ja
diz que e apresentacao-pura.

### 3. `agente_medico/tests/test_documento_matriz.py` — 6 testes

Cada um com a **reversao nomeada** no docstring (regra do projeto: teste sai com a reversao):

| # | Caso | Esperado | Reversao que o mata |
|---|---|---|---|
| 1 | espirometria, 24M, {ADM,PER,MR,DEM} | `Espirometria (ADM, PER 24 meses, MRO, DEM)` | `mostrar` fixo em False |
| 2 | audiometria, 12M, {ADM,PER,MR,DEM} | `Audiometria (ADM, PER, MRO, DEM)` — **sem numero** | `mostrar` fixo em True |
| 3 | rx_torax_oit, 12M, {ADM,PER,MR,DEM} | `... (ADM, PER 12 meses, MRO, DEM)` | remover `periodicidade_sempre_visivel` do YAML |
| 4 | exame_clinico, 6M, {ADM,PER,MR,RT,DEM} | `... (ADM, PER 6 meses, MRO, RET, DEM)` | trocar `!= 12` por `> 12` |
| 5 | rx_coluna_lombo_sacra, 24M, {ADM,MR} (sem PER) | `... (ADM, MRO)` — sem numero | grudar o numero fora do PER |
| 6 | computado sobre o YAML (`D-ARQ-67`) | todo slug com `periodicidade_sempre_visivel` existe em `exames.yaml` e o conjunto e exatamente `{rx_torax_oit}` | acrescentar o campo em outro exame sem medir |

## Fora de escopo — nomeado, nao esquecido

- **`periodicidade_apos_15a`** nao e impressa. O gabarito nao a mostra neste formato; imprimi-la
  exigiria medicao propria. Fica como esta.
- **Grafia divergente** (`Glicemia de Jejum` x `em Jejum`; `RX Torax OIT` x `RX de Torax OIT`;
  `RX Coluna Lombo-Sacra` x `RX da Coluna Lombo-sacra`) e `DT-003EO-02`. Sao duas linhas de
  `nome_exibicao` no mesmo YAML, mas entram em **fatia propria** — uma implementacao por sessao.
- Pacote soldador/armador nao disparando em Armador e Serralheiro: causa distinta
  (`R-GHE-05` / `R-PKG-ARMADOR`), medida em `MEDICAO_FASCINO_vs_GABARITO.md`, fatia propria.

## Verificacao

```
python -m pytest agente_medico/tests/test_documento_matriz.py
python -m pytest agente_medico/tests/ tests/
python -m mypy --strict agente_medico/superficie
```

Previsao de suite: **+6 testes, nenhum reescrito.** `[MEDIDO — 28/08 @ 5b4958b: o helper de
`test_documento_matriz.py` (linha 43) constroi todo `ExameEmitido` com
`momentos={Momento.ADM}`; nenhum teste existente monta uma celula com `PER`, logo nenhum
muda de saida com esta fatia.]`
