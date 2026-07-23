from __future__ import annotations

import re
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Literal

import pdfplumber

from agente_medico.motor.tipos import Pendencia

# D-ARQ-57 peça 4 fatia 4d: rota de roteamento devolvida por avaliar_estrutura
# — só significativa quando a Pendencia acompanhante é None (documento
# bloqueado não chega a ser recortado/transcrito por nenhuma rota).
Rota = Literal["ghe", "card"]

# D-ARQ-57 peça 2 (gate anti-Vistamérica): limiares calibrados em 003.CP sobre
# os 15 PGRs de DT-003CM-01.
_LIMIAR_DENSIDADE_PCT = 40.0  # maior legítimo medido: 34,8% (ALT T65); implausíveis ≥ 44,4%
# Ricco-Adm legítimo (rota (i)/forma 5, medição 003.DD) mede 41,7% — fica
# GATED por decisão explícita, NÃO recalibrado: a margem contra os
# implausíveis (≥44,4%) seria de só 2,7pp, e o falso-positivo é aceito por
# design (revisão humana, mesma classe do Cjr — anti-supressão vence).
_LIMIAR_PAGINAS_DOC_MINIMO = 10  # piso de massa dos DOIS testes (contagem e
# densidade) — abaixo dele a segmentação não é julgada: ≤1 bloco ou bloco
# denso num doc pequeno não é implausível, só reflete o tamanho do doc.


def extrair_texto_pgr(caminho: Path) -> list[str]:
    """Parse-doc determinístico do parse-PGR (D-ARQ-49 P1; D-ARQ-50 P1):
    texto VERBATIM por página do PDF do PGR, via pdfplumber.extract_text
    (text-puro, camada de texto). Página sem texto -> "".

    Fronteira de página PRESERVADA (difere de extrair_tabelas_fds, que a
    descartou): blocos GHE cruzam páginas e o recorte futuro consome
    lista-por-página (mesmo shape do núcleo _recortar_composicao da FDS).

    NÃO localiza bloco GHE, NÃO separa agente/quantificação, NÃO transcreve,
    NÃO emite slug — tudo fatia futura (transcrição-LLM, D-ARQ-50 P2/C3).
    Sem LLM aqui (D-ARQ-09). Limites: PDF sem camada de texto (escaneado)
    devolve páginas vazias — detecção/contingência OCR é do chamador, fatia
    futura (D-ARQ-43 P1); .docx é cross-check/fallback futuro, não entrada
    primária (D-ARQ-50 P1).

    [DERIVADO — pdfplumber.extract_text puro; medição 003.BK sobre
    matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf, D-ARQ-50.]
    """
    with pdfplumber.open(caminho) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _reconhece_cabecalho_ghe_padrao(linha: str) -> bool:
    linha_normalizada = linha.strip()
    if len(linha_normalizada) > 80:
        return False
    # 003.DS / DT-003DR-01: separador entre número e título pode extrair como
    # U+0000 (NUL) além de "-" — glyph-mapping do separador medido no PGR
    # Fascino (Consciente SPE 0030), 19 cabeçalhos GHE 01–19, pdfplumber.
    # Classe análoga à perda de diacrítico [OÕ] de 003.DD. \s* flexível dos
    # dois lados cobre "GHE 01 \x00 TÍTULO" e "GHE 16\x00 TÍTULO" (sem espaço
    # antes do NUL, forma real medida). Alimenta R-GHE-01 (N:1, D-ARQ-57 peça 1).
    return re.fullmatch(
        r"(INVENTÁRIO DE RISCO )?GHE:? \d+(\s*[-\x00]\s*.+)?", linha_normalizada
    ) is not None


def _reconhece_cabecalho_informacoes_cargos_funcoes(linha: str) -> bool:
    # Classe [OÕ] cobre perda de diacrítico específica de fonte/glifo medida
    # em 003.DD sobre PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf: o "Õ" da 1ª
    # palavra extrai como "O" puro (codepoint 0x4f, confirmado por
    # hex(ord(c)) — não é artefato de terminal/console), enquanto o mesmo
    # caractere em "FUNÇÕES" extrai correto (0xd5). Verbatim real medido:
    # "INFORMAÇOES SOBRE CARGOS/FUNÇÕES 01"/"...02" (págs. 14/15); forma sã
    # "INFORMAÇÕES..." também aceita, sem normalização NFC/NFD (convenção
    # VERBATIM da peça 1 preservada).
    linha_normalizada = linha.strip()
    if len(linha_normalizada) > 80:
        return False
    return re.fullmatch(
        r"INFORMAÇ[OÕ]ES SOBRE CARGOS/FUNÇÕES \d+", linha_normalizada
    ) is not None


_RECONHECEDORES_GHE: tuple[Callable[[str], bool], ...] = (
    _reconhece_cabecalho_ghe_padrao,
    _reconhece_cabecalho_informacoes_cargos_funcoes,
)


def eh_cabecalho_ghe(linha: str) -> bool:
    """Reconhecedor de linha-âncora de bloco GHE (D-ARQ-57 peça 1, consome
    DT-003CM-01): função pura, verdadeiro sse ALGUM reconhecedor do
    repertório _RECONHECEDORES_GHE casar a linha.

    Substitui a âncora fixa _ANCORA_GHE = "SETOR/FUNÇÃO" (n=1, medição
    003.BM/003.BL). O repertório hoje cobre 5 formas de cabeçalho:
    1. "GHE 12" (Viverde)
    2. "GHE 12 - TÍTULO" (Vistamérica/CMO/Seconci/TPB/AURO)
    3. "INVENTÁRIO DE RISCO GHE 12" (ALT T65/EURO)
    4. "GHE: 07 - TÍTULO" (R78 Naturia)
    (formas 1-4 medidas em DT-003CM-01 sobre o acervo de 15 PGRs.)
    5. "INFORMAÇÕES SOBRE CARGOS/FUNÇÕES NN" (Ricco-Adm) — fonte:
       DT-003DB-01/decisão 003.DC rota (i), medição 003.DD sobre
       PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf. Header é ÂNCORA-DE-RECORTE
       GHE (N cargos slash-separados na linha CARGO/FUNÇÃO: compartilham 1
       inventário → casa R-GHE-01), revertendo a exclusão de 003.CQ (lá o
       header era tratado como sinal-de-família redundante, não âncora).
       O Ricco-Adm passa a ser reconhecido e recortado (2 blocos, D-ARQ-57
       peça 4 fatia 4a) mas fica GATED por densidade a jusante
       (avaliar_segmentacao: bloco 2 mede 41,7% > _LIMIAR_DENSIDADE_PCT) —
       revisão humana BY DESIGN, mesma classe do Cjr (decisão 003.DD,
       V2 de 003.DC), não um bug a corrigir.

    Estruturado como tupla de funções linha->bool em disjunção para
    extensão futura (novas formas de cabeçalho) sem tocar o consumidor
    (recortar_blocos_ghe/recortar_topo).
    """
    return any(reconhecedor(linha) for reconhecedor in _RECONHECEDORES_GHE)


def recortar_blocos_ghe(paginas: Sequence[str]) -> list[str]:
    """Núcleo puro (sem I/O) do recorte determinístico dos blocos GHE
    (esqueleto D-ARQ-49 P2; D-ARQ-50; âncora trocada por D-ARQ-57 peça 1).
    paginas = saída de extrair_texto_pgr, lista-por-página, na ordem do
    documento.

    Âncora: eh_cabecalho_ghe(linha) — repertório de reconhecedores de
    cabeçalho GHE (D-ARQ-57 peça 1, consome DT-003CM-01), VERBATIM — sem
    normalização de acento/caixa (difere do molde _recortar_composicao da
    FDS de propósito). A âncora "SETOR/FUNÇÃO" (n=1, medição 003.BM) sofria
    de conflação (D-ARQ-22): no Viverde ela também abre a 2ª seção
    PROCESSO/SUBPROCESSO, sem linha de cabeçalho GHE — essa 2ª seção deixa
    de casar com a nova âncora, por design (resolve a conflação em vez de
    contorná-la).

    As linhas de todas as páginas são achatadas numa sequência única, na
    ordem do documento (fronteira de página vira "\\n" na reconstrução do
    texto, como no molde _recortar_composicao). Bloco i = da linha da âncora
    i até a linha anterior à âncora i+1; o último bloco vai até a última
    linha do documento.

    Blocos são CONTÍGUOS e a sobre-inclusão é direção segura (D-ARQ-31/35):
    o grid de classificação I/O/T/probabilidade/severidade/grau-de-risco e a
    cauda do documento (rodapé, próximo processo/etapa) ficam dentro do
    bloco como RUÍDO — são descartados a jusante pela transcrição-LLM
    (D-ARQ-50 C3), nunca cortados finos aqui.

    Zero âncoras -> [] (falha explícita; quem transforma isso em Pendência é
    o chamador, fatia futura — nunca devolver o documento inteiro como
    fallback).

    Saída VERBATIM (acentos, caixa preservados) — sem I/O, sem LLM
    (D-ARQ-09), sem termo->slug.

    Limites (D-ARQ-22): repertório derivado de 15 PGRs (DT-003CM-01), gate
    de 31 blocos sobre o Viverde após a troca de âncora (regressão explícita
    de 42 para 31 em relação à âncora "SETOR/FUNÇÃO", pela resolução da
    conflação com a 2ª seção PROCESSO/SUBPROCESSO); conteúdo do documento
    ANTES da 1ª âncora (pág. 33) é descartado (fora de qualquer bloco); a
    cauda do ÚLTIMO bloco (última âncora na pág. 146 de 151) sobre-inclui as
    4 páginas finais do documento até o fim — medido no script descartável
    de 003.BM, nunca cortado fino aqui.

    NÃO separa cargo/risco/quantificação dentro do bloco, NÃO transcreve,
    NÃO classifica GHE — tudo isso é fatia futura (transcrição-LLM).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)]
    if not indices_ancora:
        return []
    limites = [*indices_ancora, len(linhas)]
    return [
        "\n".join(linhas[inicio:fim])
        for inicio, fim in zip(limites, limites[1:])
    ]


def recortar_topo(paginas: Sequence[str]) -> str | None:
    """Núcleo puro (sem I/O) do recorte-de-topo (D-ARQ-53 parte 1): inverso
    determinístico de recortar_blocos_ghe — devolve a região que aquele
    descarta, da 1ª linha do documento até a linha ANTERIOR à 1ª âncora de
    cabeçalho GHE. A transcrição-LLM do conteúdo do topo é fatia futura.

    paginas = saída de extrair_texto_pgr, lista-por-página, na ordem do
    documento. As linhas de todas as páginas são achatadas numa sequência
    única, na ordem do documento (fronteira de página vira "\\n" na
    reconstrução do texto), e juntadas com "\\n" — exatamente como em
    recortar_blocos_ghe. Reusa eh_cabecalho_ghe (D-ARQ-57 peça 1), VERBATIM,
    sem normalização.

    Zero âncoras -> None (falha explícita; quem transforma isso em Pendência
    é o chamador, fatia futura — nunca devolver o documento inteiro como
    fallback). 1ª âncora na 1ª linha do documento -> "" (topo genuinamente
    vazio). Caso contrário -> topo VERBATIM (acentos, caixa preservados).

    Limite herdado (classe D-ARQ-22): repertório de reconhecedores derivado
    de 15 PGRs (DT-003CM-01) como fronteira-fim do topo; generalização para
    novas formas de cabeçalho fora do acervo medido é requisito futuro.

    Sem I/O, sem LLM (D-ARQ-09), sem parse de conteúdo do topo (emissão, RT,
    validade = fatias 2-3, ADIADAS POR MEDIÇÃO — DT-003L-01).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)]
    if not indices_ancora:
        return None
    return "\n".join(linhas[: indices_ancora[0]])


def _reconhece_cargo_funcao_dois_pontos(linha: str) -> bool:
    linha_normalizada = linha.strip()
    return re.match(r"CARGO/FUNÇÃO:", linha_normalizada) is not None


def _reconhece_cargo_cbo(linha: str) -> bool:
    linha_normalizada = linha.strip()
    return re.match(r"CARGO\b.*\bCBO:? ?\d+", linha_normalizada) is not None


def _reconhece_funcao_grid_perigo_risco(linha: str) -> bool:
    linha_normalizada = linha.strip()
    return re.match(r"Função .*Perigo / Risco", linha_normalizada) is not None


def _reconhece_lotacao_escala_qtd(linha: str) -> bool:
    linha_normalizada = linha.strip()
    return (
        re.match(
            r"Lota[cç][aã]o:\s*.*Escala\s*de\s*Trabalho:\s*.*Qtde?:",
            linha_normalizada,
        )
        is not None
    )


_RECONHECEDORES_CARGO: tuple[Callable[[str], bool], ...] = (
    _reconhece_cargo_funcao_dois_pontos,
    _reconhece_cargo_cbo,
    _reconhece_funcao_grid_perigo_risco,
    _reconhece_lotacao_escala_qtd,
)


def eh_sinal_cargo(linha: str) -> bool:
    """Reconhecedor de SINAL DE FAMÍLIA cargo-based (D-ARQ-57 peça 3, consome
    DT-003CM-01): função pura, verdadeiro sse ALGUM reconhecedor do
    repertório _RECONHECEDORES_CARGO casar a linha.

    É sinal de família para DIAGNÓSTICO — distingue um PGR cuja unidade de
    bloco é cargo/função (sem cabeçalho GHE) de um PGR GHE-based — e NÃO é
    âncora de recorte: recorte-por-cargo é fatia futura própria (D-ARQ-57
    peça 3 / "fora da 1ª leva").

    Quatro formas medidas (003.CQ + 003.DA, pdfplumber sobre o acervo de
    DT-003CM-01/DT-003L-01 forma 6 e DT-003CS-01):
    1. "CARGO/FUNÇÃO:" (Ricco-Adm, 2x) — Ricco-Adm foi reclassificado
       GHE-based pela forma 5 do repertório GHE (_RECONHECEDORES_GHE,
       decisão 003.DC rota (i)/medição 003.DD); a forma 1 PERMANECE aqui
       no repertório cargo por anti-supressão — outros PGRs podem exibir
       "CARGO/FUNÇÃO:" sem o header N:1 que a forma 5 exige, e esses
       devem seguir diagnosticados como família cargo-based.
    2. "CARGO ... CBO: 123456" (Cjr, 1x)
    3. "Função ... Perigo / Risco" — cabeçalho de grid AIHA (Hetrin 37x /
       Serra Dourada 32x); linha longa, sem teto de 80 chars (difere de
       eh_cabecalho_ghe por design — o grid-header é naturalmente extenso).
    4. "Lotação: ... Escala de Trabalho: ... Qtd" — card cargo/lotação do
       template corporativo EBSERH PGR.SOST.001 (censo 003.CZ, n=2
       realizações: espaçada UFGD-v7.0 e colada HUMAP; reenquadramento de
       DT-003CS-01 — D-ARQ-57 peça 3), medido em 003.DA sobre
       matrizes_originais/PGR_EBSERH_UFGD_v7.pdf (184 pág., 105 casos) e
       PGR_EBSERH_HUMAP.pdf (368 pág., 140 casos); zero colisão sobre o
       legado GHES (PGR_EBSERH_UFGD_legado_GHES.pdf, 197 pág., 0 casos).

    linha_normalizada = linha.strip(). Casamento via re.match (início da
    linha), VERBATIM — sem normalização de acento/caixa (mesma convenção de
    eh_cabecalho_ghe).
    """
    return any(reconhecedor(linha) for reconhecedor in _RECONHECEDORES_CARGO)


_RECORTADORES_CARGO: tuple[Callable[[str], bool], ...] = (
    _reconhece_lotacao_escala_qtd,
    _reconhece_cargo_cbo,
)


def eh_ancora_card_cargo(linha: str) -> bool:
    """Reconhecedor de linha-âncora de card cargo-based, unidade 1:1
    (D-ARQ-57 peça 4 fatia 4b, decisão 003.DC): função pura, verdadeiro sse
    ALGUM reconhecedor do repertório _RECORTADORES_CARGO casar a linha.
    Espelho de eh_cabecalho_ghe, mas sobre o repertório de RECORTE 1:1, não
    o de sinal-de-família (_RECONHECEDORES_CARGO, peça 3).

    _RECORTADORES_CARGO tem EXATAMENTE 2 membros, reusando os predicados já
    definidos (nenhuma regex duplicada): `_reconhece_lotacao_escala_qtd`
    (card EBSERH, `Lotação: ... Escala de Trabalho: ... Qtd`) e
    `_reconhece_cargo_cbo` (Cjr, `CARGO ... CBO: NNNN`). FORA por decisão
    003.DC: `_reconhece_funcao_grid_perigo_risco` (grid-header AIHA,
    Hetrin/Serra Dourada) e `_reconhece_cargo_funcao_dois_pontos`
    (`CARGO/FUNÇÃO:`, Ricco-Adm — já migrou para âncora GHE na fatia 4a) —
    ambos são sinal-de-família, NÃO âncora-de-recorte: o grid AIHA não
    delimita um card individual (é cabeçalho de tabela compartilhada), e o
    `CARGO/FUNÇÃO:` do Ricco-Adm já recorta como GHE (forma 5,
    `_RECONHECEDORES_GHE`).
    """
    return any(reconhecedor(linha) for reconhecedor in _RECORTADORES_CARGO)


def recortar_cards_cargo(paginas: Sequence[str]) -> list[str]:
    """Núcleo puro (sem I/O) do recorte determinístico dos cards cargo-based
    1:1 (D-ARQ-57 peça 4 fatia 4b, decisão 003.DC — consome DT-003DB-01).
    Motor contract, espelho estrutural EXATO de recortar_blocos_ghe: mesmo
    achatamento de páginas em sequência única (fronteira de página vira
    "\\n"), mesma fronteira de card (card i = âncora i até a linha anterior
    à âncora i+1; último card até a última linha do documento), mesma
    saída VERBATIM (sem I/O, sem LLM, sem termo->slug), zero âncoras -> []
    (falha explícita; Pendência é do chamador — nunca devolver o documento
    inteiro como fallback).

    Âncora: eh_ancora_card_cargo(linha) — repertório _RECORTADORES_CARGO
    (Lotação-tripla + CARGO-CBO). Cards são CONTÍGUOS e a sobre-inclusão é
    direção segura (D-ARQ-31/35): a tabela `RISCOS AMBIENTAIS` embutida
    (EBSERH) e a cauda até a próxima âncora ficam DENTRO do card como
    conteúdo — o binding da tabela ao card é por POSIÇÃO dentro do span,
    NUNCA por contagem global de `RISCOS AMBIENTAIS` no documento (caveat 1
    de DT-003DB-01, morto por construção: a tabela sobreconta no texto
    plano — UFGD 122>105, HUMAP 159>140 — a tabela do card é a que segue a
    âncora DENTRO do span, não a N-ésima do documento).

    Gabarito real medido (003.DA/DF, reconhecedor-Lotação validado em
    003.CZ): UFGD-v7 105 cards, HUMAP 140 cards, Cjr 1 card (CARGO-CBO,
    único no documento — witness do RECORTE; no roteamento futuro, fatia
    4d, o Cjr fica GATED por design no gate de contagem de
    avaliar_segmentacao, classe V2/003.DC, não recalibrado por este
    witness).

    NÃO transcreve, NÃO separa cargo/risco, NÃO classifica — tudo isso é
    fatia futura (4c, transcrição do card). NÃO roteia nem pluga em
    preparar_ghes — isso é fatia futura (4d, só ali DT-003CS-01 fecha).
    avaliar_estrutura/avaliar_familia/avaliar_segmentacao inalterados por
    esta fatia.
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_ancora_card_cargo(linha)]
    if not indices_ancora:
        return []
    limites = [*indices_ancora, len(linhas)]
    return [
        "\n".join(linhas[inicio:fim])
        for inicio, fim in zip(limites, limites[1:])
    ]


_PADRAO_TITULO_CARGO = re.compile(r"\d{1,3}\.\d{1,3}\s+\S")
_PADRAO_DADOS_GERAIS = re.compile(r"DADOS\s*GERAIS")
_JANELA_DADOS_GERAIS = 3  # linhas seguintes ao candidato-título, limitadas pelo fim do vão


def _recuperar_titulo_do_vao(linhas: Sequence[str], inicio: int, fim: int) -> str:
    for indice in range(fim - 1, inicio - 1, -1):
        candidato = linhas[indice].strip()
        if not _PADRAO_TITULO_CARGO.match(candidato):
            continue
        fim_janela = min(indice + 1 + _JANELA_DADOS_GERAIS, fim)
        if any(
            _PADRAO_DADOS_GERAIS.search(linhas[j])
            for j in range(indice + 1, fim_janela)
        ):
            return candidato
    return ""


def recuperar_titulos_cargo(paginas: Sequence[str]) -> list[str]:
    """Recuperação determinística do título-de-cargo (D-ARQ-57 peça 4 fatia
    4c, decisão 003.DG-4): função pura, espelho estrutural EXATO de
    recortar_cards_cargo (mesmo achatamento de páginas em sequência única de
    linhas, mesmos índices de âncora via eh_ancora_card_cargo, mesma saída
    VERBATIM), sem I/O, sem LLM.

    Motivação (003.DG-4, ratificada): no template EBSERH-UFGD o nome do
    cargo fica FORA do span do card — a âncora da fatia 4b é a
    `Lotação:`-tripla, e o título de cada card cai na CAUDA do card
    anterior. Reabrir recortar_cards_cargo para incluir o título foi
    REJEITADO em 003.DG-4; esta função recupera o título do texto de página
    cheio, por trás da âncora, sem tocar o recorte.

    Para o card `i`, o VÃO é linhas[ancoras[i-1]:ancoras[i]]; para o card
    `0`, o vão é linhas[0:ancoras[0]] — o texto pré-âncora que
    recortar_cards_cargo descarta é exatamente onde vive o título do
    primeiro card. Zero âncoras -> [] (falha explícita, espelha o recorte).

    Dentro do vão, a varredura é PARA TRÁS (da última linha do vão até a
    primeira) e devolve a PRIMEIRA linha (== a mais próxima da âncora) que
    satisfizer o PAR: casa `^\\d{1,3}\\.\\d{1,3}\\s+\\S` (após strip()) E,
    dentro das 3 linhas seguintes (limitadas pelo fim do vão), existe linha
    que casa `DADOS\\s*GERAIS` (tolerante a espaço — o HUMAP extrai colado,
    `DADOSGERAIS`). Sem par no vão -> "" para aquele card — ausência
    EXPLÍCITA, nunca descartada da lista (filtrar desalinharia títulos e
    cards em silêncio, classe D-ARQ-22).

    Por que o PAR, e não só `NN.N` (medido em 003.DH, host, pdfplumber): a
    versão sem a adjacência a `DADOS GERAIS` produz FALSO-POSITIVO no HUMAP
    — casa "4.3 RESUMO FINAL DA IDENTIFICAÇÃO DOS RISCOS BIOLÓGICOS MAIS",
    título de SEÇÃO, não cargo. Exigir o par custa ZERO no
    verdadeiro-positivo (UFGD segue 105/105) e zera o falso-positivo (HUMAP
    1 -> 0).

    Saída VERBATIM (strip() de bordas apenas — não parseia número vs. nome,
    não normaliza; essa separação é concern da transcrição, fatia
    seguinte). O número do título NÃO é índice do card e nenhuma aritmética
    é feita sobre ele: o UFGD tem 105 cards com títulos indo até `13.106`
    (numeração do documento com lacuna).

    Gabarito real medido em 003.DH (host, pdfplumber): UFGD-v7 105 cards,
    105 títulos não-vazios, 105 distintos (primeiro `13.1 Advogado`, último
    `13.106 Terapeuta Ocupacional`); HUMAP 140 cards, 0 títulos não-vazios;
    Cjr 1 card, 0 títulos não-vazios — 0 é resultado LEGÍTIMO nesses dois
    documentos (o cargo vive na linha de valores do próprio card, não em
    título numerado).

    Invariante contratual: len(recuperar_titulos_cargo(p)) ==
    len(recortar_cards_cargo(p)) para todo p — a saída é paralela por
    ÍNDICE aos cards.

    Fora de escopo (declarado): não emite Pendencia (decisão do chamador),
    não separa cargo/risco, não transcreve, não classifica, não roteia; não
    pluga em preparar_ghes (fatia 4d).
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    indices_ancora = [i for i, linha in enumerate(linhas) if eh_ancora_card_cargo(linha)]
    if not indices_ancora:
        return []
    limites_vao = [0, *indices_ancora[:-1]]
    return [
        _recuperar_titulo_do_vao(linhas, inicio, fim)
        for inicio, fim in zip(limites_vao, indices_ancora)
    ]


def avaliar_familia(paginas: Sequence[str]) -> Pendencia | None:
    """Diagnóstico de família cargo-based (D-ARQ-57 peça 3): um PGR cuja
    unidade de bloco é cargo/função, não GHE — recorte-GHE (recortar_blocos_ghe
    / avaliar_segmentacao) é inaplicável a esse formato, e tentar aplicá-lo
    produziria "0 ou 1 bloco" indistinguível, a olho, de um doc genuinamente
    implausível.

    Mesmo achatamento por linhas dos irmãos (avaliar_segmentacao):
    documento é família cargo-based sse ZERO linhas casarem eh_cabecalho_ghe
    E pelo menos 1 linha casar eh_sinal_cargo. Presença de QUALQUER âncora
    GHE veta o diagnóstico (GHE-presente sempre vence) — mesmo se o
    documento também tiver sinais de cargo (ex.: boilerplate de assinatura).

    Pendência tipo "pgr_cargo_based", sempre bloqueante (anti-supressão:
    D-ARQ-31/35 — nunca silêncio), regra_origem "D-ARQ-57", ghe_id=None.
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]
    tem_ancora_ghe = any(eh_cabecalho_ghe(linha) for linha in linhas)
    if tem_ancora_ghe:
        return None

    n_sinais_cargo = sum(1 for linha in linhas if eh_sinal_cargo(linha))
    if n_sinais_cargo == 0:
        return None

    return Pendencia(
        tipo="pgr_cargo_based",
        destinatario="extracao",
        motivo=(
            f"PGR cargo-based: nenhum cabeçalho GHE e {n_sinais_cargo} "
            f"sinal(is) de bloco por cargo — unidade de bloco é cargo, "
            f"recorte-GHE inaplicável"
        ),
        bloqueante=True,
        regra_origem="D-ARQ-57",
        ghe_id=None,
    )


def avaliar_estrutura(paginas: Sequence[str]) -> tuple[Rota, Pendencia | None]:
    """Composto de diagnóstico + ROTEAMENTO de estrutura (D-ARQ-57 peça 4
    fatia 4d): devolve (rota, pendência). A rota só é significativa quando a
    pendência é None — um documento bloqueado não chega a ser
    recortado/transcrito por nenhuma rota.

    Precedência (específico vence genérico; âncora-de-recorte vence
    sinal-de-família):
    1. Alguma linha casa eh_cabecalho_ghe -> ("ghe", avaliar_segmentacao(paginas))
       — gate anti-Vistamérica de sempre, comportamento INALTERADO.
    2. Senão, alguma linha casa eh_ancora_card_cargo -> ("card",
       _avaliar_spans(paginas, eh_ancora_card_cargo, "card(s) cargo-based"))
       — mesmo gate de densidade+contagem da peça 2, aplicado à unidade card
       em vez de bloco GHE (D-ARQ-57 peça 4 fatia 4b, decisão 003.DC: card
       1:1 é a mesma classe de risco-de-recorte-implausível que bloco GHE).
    3. Senão -> reproduz avaliar_estrutura ATUAL na íntegra (família, senão
       gate de segmentação): tenta avaliar_familia (cargo-based via sinal,
       não âncora-de-recorte — ex.: grid AIHA Hetrin/Serra Dourada); se None,
       cai no MESMO fallback avaliar_segmentacao(paginas) de sempre. Este
       ramo 3 é EXATAMENTE o avaliar_estrutura pré-4d — o split desta fatia
       só INSERE o ramo 2 (card) entre a âncora GHE (ramo 1) e a família
       (ramo 3); nenhum documento sem âncora de recorte alguma muda de
       saída. Sem este fallback, um documento sem NENHUMA âncora reconhecível
       (nem GHE, nem card, nem sinal-de-família cargo) sairia ("ghe", None)
       — silêncio sobre doc âncora-zero, violação D-ARQ-22/anti-supressão
       D-ARQ-31/35 (achado do PASSO 0 desta sessão sobre o witness real
       PGR_EBSERH_UFGD_legado_GHES.pdf, 197 págs., corrigido antes de codar).

    Exclusão mútua preservada nos 3 ramos: cada documento cai em EXATAMENTE
    um, nunca dois diagnósticos concorrentes. Anti-supressão preservada em
    todos: documento sem âncora de recorte de nenhuma rota E sem sinal de
    família, mas com massa (> _LIMIAR_PAGINAS_DOC_MINIMO páginas), ainda
    bloqueia via segmentacao_implausivel (ramo 3, fallback); doc pequeno sem
    âncora nenhuma segue ("ghe", None) -> blocos_ausentes no chamador, como
    hoje.

    Não altera avaliar_familia, avaliar_segmentacao (assinatura/saída
    idênticas), recortar_blocos_ghe, recortar_topo, recortar_cards_cargo,
    recuperar_titulos_cargo nem os dois limiares.
    """
    linhas: list[str] = [linha for pagina in paginas for linha in pagina.splitlines()]

    if any(eh_cabecalho_ghe(linha) for linha in linhas):
        return "ghe", avaliar_segmentacao(paginas)

    if any(eh_ancora_card_cargo(linha) for linha in linhas):
        return "card", _avaliar_spans(paginas, eh_ancora_card_cargo, "card(s) cargo-based")

    pendencia_familia = avaliar_familia(paginas)
    if pendencia_familia is not None:
        return "ghe", pendencia_familia
    return "ghe", avaliar_segmentacao(paginas)


def _avaliar_spans(
    paginas: Sequence[str],
    eh_ancora: Callable[[str], bool],
    rotulo_unidade: str,
) -> Pendencia | None:
    """Núcleo do gate anti-Vistamérica (D-ARQ-57 peça 2), extraído de
    avaliar_segmentacao para reuso pela rota card (D-ARQ-57 peça 4 fatia 4d):
    mesma contagem + densidade, mesmos limiares _LIMIAR_* INALTERADOS, com o
    predicado de âncora (eh_ancora) e o substantivo do motivo (rotulo_unidade
    — "bloco(s) GHE" ou "card(s) cargo-based") parametrizados. Ver
    avaliar_segmentacao para a especificação completa do gate; este núcleo
    reproduz seu corpo byte-a-byte quando chamado com
    (paginas, eh_cabecalho_ghe, "bloco(s) GHE").

    rotulo_unidade traz o marcador de plural entre parênteses (ex.:
    "bloco(s) GHE"); a forma singular usada no motivo de densidade é
    derivada removendo "(s)" (ex.: "bloco GHE").
    """
    rotulo_singular = rotulo_unidade.replace("(s)", "")
    linhas_com_pagina: list[tuple[int, str]] = [
        (indice_pagina + 1, linha)
        for indice_pagina, pagina in enumerate(paginas)
        for linha in pagina.splitlines()
    ]
    indices_ancora = [
        i for i, (_, linha) in enumerate(linhas_com_pagina) if eh_ancora(linha)
    ]
    n_blocos = len(indices_ancora)
    total_paginas = len(paginas)

    if n_blocos <= 1 and total_paginas > _LIMIAR_PAGINAS_DOC_MINIMO:
        return Pendencia(
            tipo="segmentacao_implausivel",
            destinatario="extracao",
            motivo=(
                f"Segmentação implausível: {n_blocos} {rotulo_unidade} detectado(s) "
                f"em documento de {total_paginas} páginas"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-57",
            ghe_id=None,
        )

    if n_blocos == 0:
        return None

    limites = [*indices_ancora, len(linhas_com_pagina)]
    maior_extensao_paginas = max(
        linhas_com_pagina[fim - 1][0] - linhas_com_pagina[inicio][0] + 1
        for inicio, fim in zip(limites, limites[1:])
    )
    percentual_maior_bloco = (maior_extensao_paginas / total_paginas) * 100

    if (
        total_paginas > _LIMIAR_PAGINAS_DOC_MINIMO
        and percentual_maior_bloco > _LIMIAR_DENSIDADE_PCT
    ):
        return Pendencia(
            tipo="segmentacao_implausivel",
            destinatario="extracao",
            motivo=(
                f"Segmentação implausível: maior {rotulo_singular} ocupa "
                f"{maior_extensao_paginas} de {total_paginas} páginas "
                f"({percentual_maior_bloco:.1f}%)"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-57",
            ghe_id=None,
        )

    return None


def avaliar_segmentacao(paginas: Sequence[str]) -> Pendencia | None:
    """Gate anti-Vistamérica (D-ARQ-57 peça 2): detecta segmentação GHE
    implausível por densidade + contagem, sem depender de conteúdo — só da
    forma do recorte de recortar_blocos_ghe. Limiares calibrados em 003.CP
    sobre os 15 PGRs de DT-003CM-01, ratificado em 003.CN.

    Reproduz o mesmo achatamento e a mesma fronteira de bloco de
    recortar_blocos_ghe (âncora via eh_cabecalho_ghe, bloco i = âncora i até
    a linha anterior à âncora i+1, último bloco até o fim), mas rastreia a
    página 1-based de cada linha achatada para medir a extensão em páginas de
    cada bloco: pag(última linha do bloco) - pag(linha da âncora) + 1.

    Dois testes independentes, qualquer um decide implausibilidade:
    - Contagem: <= 1 bloco (inclui zero âncoras) num documento com mais de
      _LIMIAR_PAGINAS_DOC_MINIMO páginas — massa insuficiente para um único
      bloco cobrir o documento inteiro ser plausível.
    - Densidade: maior bloco ocupa mais de _LIMIAR_DENSIDADE_PCT% do total de
      páginas do documento — só avaliada em doc com mais de
      _LIMIAR_PAGINAS_DOC_MINIMO páginas; abaixo disso um bloco único
      legítimo satura o percentual por definição e seria falso-implausível
      (mesmo piso já presente no teste de contagem).

    Sem I/O, sem LLM (D-ARQ-09); não altera recortar_blocos_ghe/recortar_topo.

    Delegação para o núcleo _avaliar_spans (D-ARQ-57 peça 4 fatia 4d,
    extração para reuso pela rota card): saída byte-idêntica à versão
    pré-4d, eh_cabecalho_ghe e "bloco(s) GHE" fixos.
    """
    return _avaliar_spans(paginas, eh_cabecalho_ghe, "bloco(s) GHE")
