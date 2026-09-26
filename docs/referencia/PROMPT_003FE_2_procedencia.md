# Prompt cirurgico #2 — procedencia da regra de forma (responde a rejeicao do Gauntlet)

Modo: IMPLEMENTACAO (comentario + doc vivo). **Nao toca logica, motor, protocolo clinico
nem nenhum R-*.** Branch existente: `fix/003fe-periodicidade-celula`, topo `15dec76`.

## Por que este prompt existe

O Gauntlet rejeitou `5b4958b..15dec76`. Gap: o comentario do teste funda a regra num arquivo
que nunca foi commitado, enquanto `DT-003EW-02` registra no git uma contradicao da mesma regra
e diz *"Refino pendente antes de implementar a formatacao"*. O diff implementava sem endereçar.

O refino agora existe e esta medido. Esta fatia **nao muda uma linha de logica** — torna a
procedencia verificavel e reconcilia a DT com o codigo.

---

## Fatia 1 — os 4 arquivos de medicao entram no git

`git add` nominal, um commit proprio, **antes** das fatias 2 e 3:

```
docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md
docs/referencia/VALIDACAO_LIBREOFFICE_vs_WORDCOM.md
docs/referencia/MEDICAO_FASCINO_vs_GABARITO.md
docs/referencia/PAREAMENTO_ACERVO.md
```

`docs/referencia/PROMPT_003FE_periodicidade.md` e este arquivo **NAO entram** — spec de sessao
segue fora do git por decisao vigente.

Mensagem sugerida:
`docs(003fe): medicoes do acervo — regra de forma, validacao de conversao, Fascino x gabarito, pareamento`

## Fatia 2 — comentario do teste passa a citar fonte versionada

`agente_medico/tests/test_documento_matriz.py`, **linhas 150-151** (ancora por conteudo, nao
por numero: o comentario que hoje diz *"6 gabaritos assinados, 547 ocorrencias; ver
PROMPT_003FE_periodicidade.md"*). Substituir o comentario inteiro por:

```python
# DT-003EW-02 — periodicidade impressa na celula. Regra de 003.EO, medida
# contra o acervo em 29/08/2026 (28 documentos, instrumento
# scripts/medir_cobertura_e_forma.py): 2896 confirmam / 122 contrariam nos
# 10 documentos de 2026, contra 1323/1681 nos de 2025. E a convencao
# corrente do escritorio, nao invariante do acervo historico — o app emite
# documento novo, logo emite a convencao corrente.
# Medicao, corte por documento e ressalvas em
# docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md.
```

E `agente_medico/protocolo/vocabulario/exames.yaml`, **linha 78**, trocar o comentario
`# medido 28/08: unico exame que imprime o numero a 12M` por:

```yaml
    periodicidade_sempre_visivel: true   # unico exame que imprime o numero a 12M — ver docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md
```

## Fatia 3 — reconciliar `DT-003EW-02` com o codigo

`docs/PENDENCIAS_CLINICAS.md`. Duas edicoes no bloco `### DT-003EW-02`:

**(a)** A linha `**Status:** ABERTA — medicao pendente antes de qualquer correcao.` passa a:

```
**Status:** ABERTA — faceta de leitura RESOLVIDA (003.EZ); faceta de escrita IMPLEMENTADA em
003.FE apos o refino que esta DT exigia (ver nota aditiva 003.FE abaixo). Segue ABERTA pelos
4% residuais de 2026, nao investigados nominalmente.
```

**(b)** Inserir, **imediatamente apos o fim da nota aditiva de 003.EZ** (o paragrafo que termina
em *"nenhum codigo de producao foi tocado nesta sessao."*) e antes do proximo header `###`:

```
**Nota aditiva (003.FE) — o refino exigido foi feito; a regra e da convencao corrente.**
`[MEDIDO — 29/08/2026, 28 documentos MATRIZ* de matrizes_originais/, instrumento scripts/medir_cobertura_e_forma.py com a correcao 6f2e9f0 aplicada]`

A nota de 003.EY registrava 2853 contradicoes contra 4366 confirmacoes e concluia que a regra
"nao sobrevive fora do par Fascino/RESERVA que a originou". A remedicao devolve **4281 confirmam
/ 1805 contrariam** — e o agregado enganava, porque a contradicao **nao esta distribuida**.
Por ano do documento:

| Ano | Docs | Confirma | Contraria | % contra |
|---|---|---|---|---|
| 2026 | 10 | 2896 | 122 | **4,0%** |
| 2025 | 11 | 1323 | 1681 | **55,9%** |

O bucket 2025 inclui os dois CONSCIENTE RESERVA 0028, reatribuidos de "sem data no nome" para
04/2025 pela tabela de docs/referencia/GABARITO_003EX_audiometria_dem.md.

A regra de 003.EO descreve a **convencao corrente do escritorio**, nao uma invariante do acervo
historico. As contradicoes de 2025 sao a forma antiga — 542 ocorrencias de `grupo_separado`
no corpus, do tipo "Audiometria (12 meses), (ADM, PER...)". Como o emissor produz documento
**novo**, reproduzir a convencao abandonada nao e requisito, e a implementacao de `deed9f6`
esta correta para o que o app deve emitir.

**Nao fecha esta DT:** os 4% residuais de 2026 (122 ocorrencias) nao foram investigados
nominalmente `[INTERPRETADO — prioridade na revisao de saida]`. Corte por documento e ressalvas
em docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md.

```

Commit proprio, nominal.

## Fatia 4 — passo 9 do ritual de fechamento (varredura de branch)

`docs/RITUAL_FECHAMENTO.md`. Acrescentar como **item 9**, ao fim da lista numerada, logo apos
o item 8 (o que termina em *"a evidencia e o relatorio, referenciado no bloco da sessao."*):

```
9. Depois do merge em `main`, varrer branch orfa: `git branch --merged main` (e a listagem
   remota equivalente). Toda branch ja mergeada, local e remota, e apagada com `git branch -d`
   (minusculo — recusa apagar o que nao esta mergeado; `-D` nunca, sem decisao explicita) e
   `git push origin --delete`. Apagar remoto conta como escrita no remoto: exige a mesma
   autorizacao explicita do passo 7. Motivo medido: em 003.FD a branch
   `fix/003fd-emenda-gauntlet` sobreviveu ao merge e so foi encontrada em 003.FE, uma sessao
   depois — segunda ocorrencia da mesma classe, e nenhum passo do ritual a varria.
```

Nada mais no arquivo e alterado; os itens 1-8 ficam intactos.

## Verificacao

```
python -m pytest agente_medico/tests/test_documento_matriz.py
python -m pytest agente_medico/tests/ tests/
```

Previsao: **1160 passed, 6 skipped — inalterado.** Esta fatia so toca comentario e markdown;
nenhum comportamento muda. Se a contagem se mover, e bloqueador — pare e reporte.

`mypy` **nao se aplica**: nenhuma linha de logica foi alterada.
`gerar_indice_darq` **nao se aplica**: nenhuma D-ARQ criada ou tocada (a edicao e em
`PENDENCIAS_CLINICAS.md`, nao em `DECISOES_ARQUITETURAIS.md`).

Push depois dos commits, com autorizacao. Nao mergear — o Gauntlet rejulga
`5b4958b..HEAD` em sessao nova.
