> **PENDÊNCIA DE VERSIONAMENTO — executar no fechamento do S2, não em sessão própria.**
> Este arquivo vive na pasta do Cowork, **fora do git**, e já carrega decisão citável
> (§S0: adiar deploy, com RAM/tempo medidos; correção da premissa do Streamlit).
> Doc de decisão fora do git não é auditável nem tem histórico — é a dívida já registrada
> como irmã de `DH-003EG-02` e `DT-003DX-02`.
>
> **Ação:** mover para `docs/PLANO_V1.md` como cláusula do fechamento do S2 (a sessão já
> toca docs; sessão própria só para mover arquivo não se paga). `git add` nominal. A partir
> daí, a pasta do Cowork deixa de ser fonte deste conteúdo — atualizações vão no git.
> Os `PROMPT_*.md` da pasta **não** migram: são insumo de sessão, descartáveis pós-merge.
>
> **Cumprida em 003.EO** (`docs/PLANO_V1.md`, `git add` nominal). A pasta do Cowork deixou
> de ser fonte deste conteúdo a partir daqui.

# Plano V1 — "projeto rodando num site"

**Definição de pronto (Diovanni, 01/08/2026):** um técnico insere um PGR de construção civil
num site e recebe a matriz de exames, com a explicação de como o sistema chegou nela,
exportável em HTML e Word para a Dra. Carolini validar.

**Restrição que manda:** prazo.

---

## O que já está pronto e não precisa ser construído

- **A explicação já existe nos dados.** D-ARQ-22 Parte B, materializada em 003.EG/003.EM:
  `Motivo.regra_id` + `predicado` (expressão real do `quando`) + `detalhe` + `status_regra`;
  `MatrizGHE.riscos_resolvidos` + `predicados_avaliados` + pendências anexadas por linha.
- **A matriz tem superfície própria** — `superficie/apresentacao_matriz.py` (D-ARQ-72, 003.EM),
  com coluna de status e bloco "inspecionar primeiro". **[ATUALIZADO — 003.EO]** Existe também
  `superficie/documento_matriz.py` (D-ARQ-73) — superfície DISTINTA: `apresentacao_matriz.py`
  é o render de diagnóstico (rastreabilidade completa, para a revisão regra-a-regra);
  `documento_matriz.py` é o documento do escritório (HTML/DOCX, sem rastreabilidade, é o que a
  Dra. Carolini assina). Não confundir as duas ao ler este plano.
- **O formato de saída não precisa ser desenhado** — está pronto em `matrizes_originais/`:
  cabeçalho `Empresa / Obra / tipo / Data`, corpo com uma tabela 2 colunas
  `FUNÇÃO | EXAMES SOLICITADOS` por GHE, rodapé com responsável e médica validadora.
  Texto de célula: `Nome do Exame (ADM, PER [N meses], MRO, RET, DEM)`. **[REFINADO — 003.EO,
  fatia 0]** O número de meses só aparece quando a periodicidade é ≠ 12M — **exceto RX Tórax
  OIT, que sempre traz o número**, mesmo quando vale 12. Regra por exame, não constante solta;
  materializada como `ordem_exibicao`/formatação em `documento_matriz.py`.
- **A ingestão determinística do Fascino atravessa** — 19/19 GHEs, sem LLM (003.EB, D-ARQ-65).

## A alavanca de prazo

Com justificativa por linha, **divergência contra o gabarito vira conversa, não erro**.
Não é preciso zerar o diff antes de mostrar à coordenadora — é preciso que cada célula
se defenda. Duas exceções que não se defendem sozinhas e por isso são caminho crítico:

- **Superemissão** — motor emite 6 exames/GHE em 16 GHEs, gabarito tem 4. `[A MEDIR]` desde 003.EG.
  **[REFUTADO — 003.EO, fatia 4, medição contra o Fascino real]** O eixo estava descrito ao
  contrário e a magnitude era outra: medido **4 células de superemissão em 2 GHEs** (GHE-10:
  `acetona_urina`/`mek_urina`; GHE-16: `ortocresol_urina`/`acido_metilhipurico` — DT-003EB-02) e
  **10 células de subemissão em 5 GHEs** (GHE-06/08/09/17/19). Não é caminho crítico do prazo
  na forma descrita aqui — cada célula divergente tem causa nomeada (DT-003EB-02, DT-003EI-01,
  DT-003EO-03), não é um bloco de 16 GHEs com 2 exames a mais cada. Registro anterior preservado
  acima por D-ARQ-06; não apagado, substituído em vigência por esta nota.
- **DT-003EG-01** — audiometria com motivo `R-PKG-ATIVCRIT` em 15/16 GHEs onde o gatilho real
  é ruído bloqueado. Exame certo, razão errada — e agora visível, porque a razão é impressa.

---

## Sequência

| # | Sessão | Estado |
|---|---|---|
| **S1** | Regra psicossocial — `R-PSY-02` sucede `R-PSY-01` (DEPRECATED) | **prompt pronto:** `PROMPT_003EN_psicossocial.md` |
| **S2** | Emissor Word + HTML no formato do escritório | **[ATUALIZADO — 003.EP] entregue** — emissores HTML e DOCX prontos e testados (D-ARQ-73); expansão GHE→cargo com os 41 cargos reais do Fascino, em produção (DT-003EO-04 fechada — ver §"S2 — o que falta"). Ressalva preservada, não é lacuna: cabeçalho/rodapé seguem seam humano por desenho (DT-003EO-01/D-ARQ-73 cl.5), resolvido no S3, não no S2 |
| **S3** | App: upload PGR → envelope → processa → matriz na tela → download | **[003.EQ] fatia 1 entregue** — `superficie/web_matriz.py`, rota determinística sem LLM, validada manualmente no host contra o Fascino real (19 GHEs, 41 cargos) e no caso de rejeição por R-PGR-01. Falta para o S3 completo: pré-preenchimento document-derived do envelope (plugar `preparar_envelope`, hoje 100% entrada do operador — paliativo sinalizado, D-ARQ-53 P2) e a rota LLM para famílias não cobertas pela rota determinística |
| **S0** | Decisão de hospedagem | **[003.ER] DECIDIDO por D-ARQ-75** — Railway Hobby (consumo, não tier; pico medido 904 MB derruba o piso de 2 GB), `st.login()` OIDC com client próprio + allowlist obrigatória, `requirements-app.txt` enxuto. Implementação em 003.ES |

### S2 — o que falta, nomeado

1. **Expansão GHE→cargo.** O motor produz `MatrizGHE` (19 linhas no Fascino); a matriz humana
   é por **cargo** (41 no Fascino). A expansão é apresentação — cada cargo do GHE herda a
   matriz do GHE — mas alguém tem que escrevê-la. ~~`GHEPGR` já carrega os cargos.~~
   **[CORRIGIDO — 003.EO, D-ARQ-06: registro do erro preservado, não apagado]** Esta frase
   estava **errada** e é a razão de o S2 não fechar em 003.EO: `GHEPGR` **não** carrega os
   cargos separados. Medido em 003.EO: `_extrair_cargos_da_linha`
   (`parser_familia_consciente.py`, D-ARQ-65 fatia 1) devolve uma tupla de **UM elemento** com
   a linha inteira da coluna Cargo/Função, delimitador inconsistente entre vírgula e
   ponto-e-vírgula. Pior: **6 dos 41 cargos nem chegam a existir** em `GHEPGR` — quebra de
   linha física na tabela do PDF perde o resto da lista em 2 de 19 GHEs (GHE-03, GHE-06).
   `montar_documento` (D-ARQ-73) expande corretamente o que recebe; o problema é o dado de
   entrada, não a expansão. Ver DT-003EO-04 (duas facetas, fecha em `003.EP`).
   **[FECHADO — 003.EP, D-ARQ-06: registro acima preservado, não apagado]** DT-003EO-04
   fechada nas duas facetas (PROTOCOLO §11) — `_extrair_cargos_da_linha` passa a capturar
   overflow por transição de banda (D-ARQ-65 cláusula 5) e a separar nome/CBO por entrada,
   CBO descartado. Os 41 cargos do gabarito chegam a `GHEPGR` e a `montar_documento` (e2e
   real medido: 41 `LinhaCargo`, os 6 antes perdidos presentes nominalmente). **Ressalva que
   NÃO fecha aqui, por desenho, não por lacuna:** cabeçalho/rodapé seguem sendo parâmetro
   humano do emissor (D-ARQ-73 cl.5 / DT-003EO-01) — é seam humano intencional (mesma classe
   de DT-003BV-01/confirmação-RT), resolvido quando o S3 (app) tiver onde capturar esse dado
   de um humano, não uma lacuna do S2.
2. **Emissor DOCX** — `python-docx` já está em `requirements.txt`. **[FEITO em 003.EO.]**
3. **Emissor HTML** sobre a mesma estrutura intermediária. **[FEITO em 003.EO.]**
4. **Decisão de arquitetura recomendada:** a explicação **não entra no Word da Dra.** O Word
   dela é o formato do escritório, limpo, do jeito que ela já assina. A rastreabilidade
   (regra, predicado, norma, status) vai na tela e num anexo separado. Misturar atrapalha
   a validação em vez de ajudar.

### S0 — hospedagem `[MEDIDO 01/08/2026 — decisão recomendada: adiar]`

**Correção de premissa.** "Streamlit Community Cloud não serve repo privado" é **falso** — ele
serve, via Deploy Key SSH + scope `repo` do OAuth. O limite do free tier é **1 app privado**.
`[fonte: docs.streamlit.io/deploy/streamlit-community-cloud/status]`

O diagnóstico correto do legado Seconci já existia desde 12/07/2026 e nunca disse
"impossível": *"Streamlit Cloud não usa PAT dos Secrets pra clonar — usa deploy key SSH
própria via OAuth do GitHub App (escopo `repo`); fix provável não testado é revoke+reconnect
completo em `github.com/settings/applications` + reautorizar em share.streamlit.io"*.
A leitura "não serve repo privado" foi degradação minha do registro, repetida várias vezes
antes de eu reabrir o arquivo. **O fix nunca foi testado** — continua sendo a primeira
tentativa mais barata, se o Community Cloud voltar a ser considerado.

**O gargalo real é RAM e tempo, não repo privado.** Medido: parse do PGR Fascino
(10,4 MB, 119 páginas) com pdfplumber — pág. 25 em 21s/142 MB RSS, pág. 50 em 39s/228 MB,
**>130s sem terminar**, extrapolação ~450-500 MB de pico. `flush_cache()` por página não
conteve o crescimento. `[MEDIDO em sandbox Linux — tempo é indicativo (hardware difere),
memória é mais transferível]`

Consequências:
- **1 GB do Community Cloud não fecha:** ~200-250 MB de Streamlit/libs + ~450-500 MB do parse
  = teto com **um** usuário. Dois simultâneos derrubam.
- **Render Starter ($7/mês, 512 MB) é insuficiente.** Piso viável ≈ 2 GB.
- **~2 min por PGR** exige barra de progresso (Streamlit aguenta — websocket, sem timeout HTTP).

**Recomendação: não hospedar na V1.** Rodar `streamlit run` local na máquina do escritório.
Tira do caminho crítico o item de maior incerteza; o valor que a Dra. valida está no **Word**,
não no site; e **não gera retrabalho** — é o mesmo app, o deploy vira empacotamento depois.

Se o site for exigido: **Railway** (~$5-20/mês, usage-based) ou **Render 2 GB** (~$25/mês).
Community Cloud como plano C.

**Duas perguntas abertas que travam qualquer opção paga:**
1. Quem usa? Só a equipe do escritório, ou técnicos das construtoras também sobem PGR?
   Se for só interno, local pode resolver de vez.
2. PGR de cliente pode ir para nuvem de terceiro? Se o SECONCI ou os contratos vedam,
   sobra servidor próprio — e o prazo do deploy dobra.

**[ATUALIZADO — 04/08/2026, respostas do Diovanni]** As duas perguntas abertas estão
respondidas: (1) uso interno apenas — engenharia valida ou elabora o PGR, a assessoria de
saúde monta a matriz; construtoras não terão acesso ao app; (2) PGR de cliente pode ir para
nuvem de terceiro. O resultado confirma a recomendação de adiar: "pode ir para nuvem" abre
a opção, "uso interno sem construtoras" não cria a necessidade. Fato novo não considerado
pelo plano original: o fluxo tem handoff entre duas equipes, e "rodar local na máquina do
escritório" assumia um operador único — requisito a resolver no S3 completo, não em S0.
`[A MEDIR — se engenharia e assessoria compartilham máquina/rede]`

**[ATUALIZADO — 10/08/2026, nota de progresso 003.ET] §S0 NÃO fecha — o destino do deploy
reabriu.** As fatias de empacotamento, acesso, build e memória foram entregues (D-ARQ-76,
D-ARQ-77, nota de aplicação em D-ARQ-75) — mecanismo de deploy pronto, `Dockerfile` +
`entrypoint.sh` + materializador de segredo, gate de acesso no núcleo puro. O que reabriu é a
**escolha de provedor**: a premissa de "provedor pago por consumo" (D-ARQ-75 cláusula 1) caiu
com a medição da fatia 2 — o pico de RAM do e2e do Fascino não é 904 MB, é cache de página do
pdfplumber nunca liberado; corrigido, o app roda na faixa de 250-350 MB somando o runtime do
Streamlit, dentro do teto de qualquer tier gratuito plausível. **Requisito declarado pelo
Diovanni no curso de 003.ET: custo zero.** A decisão original de provedor pago nunca teve essa
restrição checada com ele antes de ser arquitetada — a pergunta não foi feita em 003.ER.

Opções na mesa para a decisão de sessão própria: **Streamlit Community Cloud** (limite de 1 GB,
1 app privado por conta gratuita `[DERIVADO — docs.streamlit.io, conferido 09/08/2026]`),
**Google Cloud Run** (free tier permanente, consome o `Dockerfile` já pronto desta sessão) e
**Railway** (~$5/mês de assinatura, a escolha original de D-ARQ-75, agora sem a urgência do
pico de RAM que a motivou). `[A CONFIRMAR]` que decide o Community Cloud: ele instala
dependências a partir de `requirements.txt` na raiz — que é o do legado, não o
`requirements-app.txt` do app novo — e não se sabe se a plataforma permite apontar outro
arquivo. Sem Dockerfile para contornar (o builder do Community Cloud não é o Railpack/Railway
de D-ARQ-77), isso pode ser eliminatório para essa opção especificamente.

**[REVERTIDO — 05/08/2026. A recomendação de adiar CAI; o parágrafo acima fica como
registro, substituído em vigência por esta nota.]** Duas respostas novas do Diovanni:
(3) rede compartilhada, máquinas individuais; (4) **instalação de software exige
solicitação à TI**. O item (4) é o fato novo que reverte. A recomendação "rodar
`streamlit run` local na máquina do escritório" assumia que instalar era trivial — no
ambiente real é **um ticket de TI por máquina**, e o fluxo tem duas equipes. O custo da
opção local nunca foi técnico; é organizacional, e esse eixo não havia sido medido. A
decisão anterior estava correta para as premissas conhecidas e errada para as reais.

**Recomendação nova: hospedar, em nuvem paga de piso ~2 GB** (Railway usage-based
~$5-20/mês, ou Render 2 GB ~$25/mês — números do bloco original desta seção, não
re-medidos). Elimina a barreira de instalação por inteiro: navegador, nada por máquina.
Community Cloud segue descartado como principal pela medição de RAM já registrada.

Alternativa considerada e **não** recomendada: servidor único na rede interna. Resolve a
multiplicação de tickets e mantém o PGR na rede, mas ainda exige ticket, cria manutenção
interna e não cobre acesso fora do escritório — que a resposta (2) já liberou para nuvem.

**Requisito novo que a hospedagem cria e não existia no modo local: autenticação.** App
exposto na internet com PGR de cliente (razão social, obra, cargos) não pode ser aberto.
Mecanismo é decisão da fatia de deploy — conferir a documentação vigente do Streamlit
antes de cravar, não presumir. `[A DECIDIR]`

`[A MEDIR — pico real de RAM no ambiente-alvo; os ~450-500 MB são de sandbox Linux e o
próprio bloco original marca o eixo tempo como indicativo]`
`[A DECIDIR — "acesso em qualquer ambiente" = qualquer máquina do escritório, ou também
fora dele? Se só dentro, o servidor interno volta a ser competitivo]`

**[FECHADO — 003.ER, 05/08/2026 por D-ARQ-75. Os dois `[A DECIDIR]` e o `[A MEDIR]` de RAM
acima estão resolvidos; o "piso ~2 GB" da recomendação anterior fica como registro,
substituído em vigência por esta nota.]**

- **`[A DECIDIR]` escopo de acesso — RESOLVIDO:** inclui fora do escritório (resposta do
  Diovanni, 05/08). Servidor interno sai de vez; nuvem pública com autenticação é o caminho.
- **`[A MEDIR]` pico de RAM — MEDIDO:** `executar_rota_determinista` completo sobre o Fascino
  (10,4 MB, 119 págs) → **128,5s, pico RSS 904 MB**; `parsear_arquivo` isolado → 64,9s,
  731 MB. `[MEDIDO — 003.ER, sandbox Linux; tempo indicativo, memória transferível]` O piso de
  ~2 GB estava subdimensionado: 904 MB + runtime Streamlit ≈ teto de um usuário.
- **Provedor:** Railway Hobby — cobrança por consumo (RAM $10/GB/mês, teto 48 GB/serviço), não
  por tier fixo. ~$10-15/mês `[APROXIMADO]`.
- **`[A DECIDIR]` mecanismo de autenticação — RESOLVIDO:** `st.login()` com client OIDC do
  projeto (não do tenant do cliente) + allowlist de e-mails no app. OIDC autentica, não
  autoriza — a allowlist é obrigatória.

Ver **D-ARQ-75** para o corpo da decisão, as cláusulas subordinadas de auth e os
`[A CONFIRMAR]` remanescentes.

**[IMPLEMENTAÇÃO — 003.ES, 08/08/2026.]** Fatias 1 e 2 de D-ARQ-75 entregues:
`requirements-app.txt` medido por AST (5 terceiros) com teste que o guarda; entrypoint
`app_matriz.py` na raiz (lacuna que D-ARQ-75 não previa — `streamlit run` insere no `sys.path`
o diretório do script, não a raiz); gate de login + allowlist antes do parse, com a decisão em
núcleo puro (D-ARQ-76). Fatia 3 (deploy) não executada — vira 003.ET, por ter metade em ação
manual com credencial real e por depender de dois fatos da Railway ainda não medidos (injeção de
`PORT`; se o builder detecta `requirements-app.txt` em vez do `requirements.txt` do legado).

---

## Cortes explícitos da V1 (paliativos, sinalizados)

- **Universalidade multi-PGR: fora.** Só as famílias que já ingerem. O Marco 1 diz "um PGR
  nomeado" — D-ARQ-62 cl.1 já cravou o Fascino.
- **Fluxo de FDS/química: fora.** As 178 pendências `vocabulario_ausente` aparecem como
  pendência visível, não travam a entrega.
- **Cobertura clínica congelada em 21/42.** Nenhuma regra nova salvo o que a medição exigir.
  **[DESATUALIZADO — já em 003.EN]** R-PSY-02 moveu o número para **22/42** pelo instrumento
  (21/42 pela intenção do painel) antes mesmo desta migração; 003.EO não moveu de novo
  (nenhuma R-* tocada). Número corrente: ver `docs/PAINEL_ESTADO.md`, não este arquivo.
- **~20 DTs/DHs não-bloqueantes ficam abertas.**

## Fora de escopo da V1, nomeado

- **Periodicidade do RX Tórax OIT** (DT-003EC-01). Medido no acervo: 60M em 108 ocorrências,
  12M em 107, 24M em 3 — **bimodal**, provável discriminante de faixa de exposição
  (família `R-RX-01-*`). Exige medição própria cruzando com o risco do GHE.
- **Audiometria universal** — hipótese levantada e **refutada** pela medição (universal em
  1 de 19 documentos; o Fascino é outlier). O motor está correto ao tratá-la como condicional.
- **Gate mecânico contra medição concorrente.** 4ª ocorrência da classe em 6 sessões, com a
  lição já versionada em `CLAUDE.md` e reincidindo — inclusive dentro do fechamento cujo
  prompt a documentava. Documentar não previne; o controle é disciplina, não mecanismo.
  Correção estrutural: alvo de suíte que checa `git status` limpo ao iniciar e aborta se a
  árvore mudar durante. Barato, mas não bloqueia a V1.
