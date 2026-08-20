---
name: conferir
description: Conferidor factual — extrai TODA afirmação factual de um artefato e confere cada uma contra o repo, devolvendo achados com âncora e comando que reproduz. Não julga design, não corrige, não aprova. Roda antes de o artefato virar trabalho do Code. Invocação manual.
disable-model-invocation: true
allowed-tools: Bash(git show *) Bash(git grep *) Bash(git log *) Read Grep
---

# /conferir — conferência factual, não julgamento

Invocação: `/conferir <caminho do artefato>` — um pacote de docs, um prompt cirúrgico, um bloco de D-ARQ, uma spec de dado. Só artefato que **crava fato**. Discussão conceitual não passa por aqui.

## Regra zero — o papel

Você **confere**, não julga e não conserta. Proibido: avaliar se a decisão é boa, se é universal, se o desenho é o melhor (isso é `/critico`); propor correção ou redação; reescrever; emitir veredito.

Você também **não emite selo**. Nunca escreva "está tudo certo" ou "conferido, aprovado" — escreva o número de afirmações extraídas, quantas conferem, quantas divergem e quantas não foram verificáveis. Achado reproduzível em segundos é auditável; selo não é.

**Não escreva nada.** Nem arquivo, nem edição, nem redirecionamento de saída (`>`, `>>`, `tee`) — nem para scratch, nem para "salvar o relatório". O `allowed-tools` não barra um `>` dentro de um comando permitido; esta regra barra. Se um comando ficar longo demais para a tela, quebre a leitura em faixas, não em arquivo.

Leia por `git show <rev>:<path>` e localize por `git grep`, nunca do working tree. **Não use `git status`** — pelo mount ele deixa `.git/index.lock` órfão (`DH-003FB-02`). Declare o hash contra o qual conferiu: fato envelhece, e um relatório sem âncora de revisão não vale na sessão seguinte.

## Passo 1 — extrair, exaustivamente

Numere **toda** afirmação factual do artefato. Não amostre. Conta como afirmação factual:

- número, contagem, percentual, previsão de suíte;
- versão de documento, hash, número de linha, âncora de inserção;
- nome de arquivo, função, campo, slug, ID de regra ou de decisão, nome de teste;
- assinatura de função e valor de campo;
- **citação literal** de norma, de documento vivo ou de código;
- **afirmação sobre o que outro documento diz** ("D-ARQ-31 cl.1 parte os estados por…", "a nota 003.EJ prescreve…");
- afirmação de existência ou de ausência ("esse tipo não existe", "zero consumidores", "1 chamador em produção").

**Toda contagem é recontada, sem exceção** — inclusive as que parecem secundárias, incidentais ou fora do assunto principal do artefato. Contagem citada de passagem, dentro de um parêntese ou numa cláusula que não é o foco, é onde o erro sobrevive: o artefato inteiro parece conferido porque os números do tema central bateram. `[MEDIDO — 003.FB: numa rodada de teste com 6 defeitos plantados, o único que escapou foi uma contagem de uso citada de passagem, enquanto as contagens do tema central foram todas pegas.]`

Se o artefato for grande demais para extrair tudo, **declare quantas linhas ficaram de fora e por quê**. Recorte silencioso é a falha que esta skill existe para impedir.

## Passo 2 — conferir uma a uma

Cada afirmação recebe **CONFERE**, **DIVERGE** ou **NÃO VERIFICÁVEL**, com o comando que reproduz o resultado.

`NÃO VERIFICÁVEL` é **achado**, não passe livre. Use quando a conferência exigir rodar a suíte inteira (`DH-003EC-02` mediu **1366s / 22min46 para 973 testes**, 79% em reparse de PDF; a suíte hoje é maior), parse de YAML/AST, execução de script, medição em documento fora do repo, ou fonte externa. Diga o que seria preciso para verificar — o `allowed-tools` desta skill é estreito por desenho, e conferência que exige executar algo além de `git show`/`git grep` sai como achado, não como conferida.

Ausência nunca vira inexistência: "não achei em X" é `NÃO VERIFICÁVEL`, não `CONFERE` para uma afirmação de ausência — a menos que você tenha varrido o escopo inteiro e diga qual foi.

## Classes de erro medidas neste projeto — cace por desenho

Não são hipóteses; cada uma ocorreu e custou uma correção.

1. **Número herdado citado como corrente.** Valor medido na *abertura* de uma sessão, repetido depois como estado atual (`55` slugs sem `termos:` quando a própria entrega daquela sessão levou a `53`; baseline de painel três sessões atrás). Confira todo número contra o `HEAD`, não contra o documento que o cita.
2. **Afirmação sobre o que outra decisão diz.** Abra o texto real da D-ARQ/regra citada e compare frase a frase. Ocorreu com `D-ARQ-31` cl.1: o artefato afirmava que ela não mencionava bloqueio, e ela menciona.
3. **Citação literal não transcrita.** Trecho de norma ou de doc apresentado entre aspas ou em caixa alta vindo de leitura assistida, não de transcrição. Marque `NÃO VERIFICÁVEL` se você não conseguir casar o literal caractere a caractere na fonte.
4. **Âncora que envelheceu.** Número de linha, "após o bloco X", "última linha da tabela" — reconfira no `HEAD`; linhas se movem a cada commit.
5. **Contagem de suíte prevista.** `+N testes` sem descontar teste reescrito ou reaproveitado.
6. **Nome ou assinatura que não existe.** Função, campo, slug, teste ou parâmetro citado — confirme que existe e que a assinatura é a citada.
7. **Contagem de uso ("1 chamador", "5 usos no motor").** Recontar, e conferir o **escopo**: produção e teste não são a mesma coisa (`elaborador_pgr` era 3 em produção e 5 no pacote).
8. **Mecanismo plausível afirmado sem medição.** "Isto aconteceria se…" — se o artefato usa um cenário para justificar uma escolha, verifique se o cenário ocorre no dado real. Um caso foi justificado por uma colisão fuzzy que o índice real não produz (distância > 2 para todas as formas).
9. **Literal de código contra o dado** (`D-ARQ-67`) e **campo sem consumidor** (precedente 003.DG-1): slug comparado em código que não existe no YAML; campo novo cujo consumidor não entra na mesma fatia.

## Saída — formato fechado

```
Conferido contra: <hash> · <N> afirmações extraídas (<M> linhas fora do escopo, se houver)
Resultado: <x> CONFERE · <y> DIVERGE · <z> NÃO VERIFICÁVEL

INVENTÁRIO (uma linha por afirmação, na ordem do artefato)
 1. CONFERE — <afirmação em até ~10 palavras>
 2. DIVERGE — <afirmação em até ~10 palavras>
 3. NÃO VERIFICÁVEL — <afirmação em até ~10 palavras>
 ...

DIVERGE — detalhe
 2. <afirmação, citada do artefato>
    real: <o que o repo diz>
    reproduz: <comando>

NÃO VERIFICÁVEL — detalhe
 3. <afirmação>
    falta: <o que seria preciso>
```

O **inventário é obrigatório e cobre 100% das afirmações extraídas**, `CONFERE` inclusive — é ele que permite auditar se a extração foi exaustiva. Sem ele, uma afirmação que escapou da extração fica indistinguível de uma que foi conferida, e o relatório passa a esconder o que deveria expor. `[MEDIDO — 003.FB: a ausência do inventário deixou invisível o único defeito que escapou numa rodada de teste.]`

**Só `DIVERGE` e `NÃO VERIFICÁVEL` ganham detalhe.** `CONFERE` fica na linha do inventário e nada mais.

Se não houver divergência, saem a contagem e o inventário, e nada mais. Não comente a qualidade do artefato, não elogie, não recomende.

## Fronteira com `/critico`

Esta skill não substitui o Gauntlet e não conta como julgamento. Artefato factualmente limpo pode ser arquitetonicamente ruim. A ordem é: `/conferir` antes de o artefato virar trabalho do Code; `/critico` sobre o artefato pronto, contra a barra do modo.
