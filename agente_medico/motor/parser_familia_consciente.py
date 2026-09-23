from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, Optional

from agente_medico.motor.extracao_pgr import eh_cabecalho_ghe
from agente_medico.motor.io_pdf import paginas_liberadas
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim

# [DERIVADO — D-ARQ-65 fatia 1; molde D-ARQ-49/50 (verbatim tipado) +
# D-ARQ-57 peça 1 (repertório de âncora GHE, reusado sem duplicação)]
#
# Parser determinístico da família de template Consciente/Fascino (D-ARQ-65):
# rota alternativa à camada-LLM (D-ARQ-41) para família com estrutura MEDIDA,
# emitindo o MESMO verbatim tipado (GHEVerbatim/RiscoVerbatim) que a rota LLM
# entregaria, sob o MESMO gate de forma (gate_forma_ghe, transcritor_pgr.py) —
# o consumidor a jusante não distingue a origem.
#
# Módulo motor (D-ARQ-09): determinístico e puro sobre sequências de
# palavras pré-extraídas (parsear_paginas); o único I/O (pdfplumber) fica
# isolado no wrapper `parsear_arquivo`, no fim do arquivo.
#
# ESTA FATIA (1 de 2, D-ARQ-65): só o parser isolado, sem plug em
# `preparar_ghes`. Roteamento por família (medida→determinístico /
# não-reconhecida→LLM-se-disponível) e procedência no verbatim
# (`deterministico:<familia>`|`llm`|`manual`) são D-ARQ-65 fatia 2.
#
# CALIBRAÇÃO POR BLOCO (correção do Arquiteto ao bloqueador de bandas
# fixas, D-ARQ-65 fatia 1): a medição inicial de bandas fixas (AGENTE@[113,
# 177), FONTE@177+) divergiu na varredura real — x0 de "FONTE" varia
# 168.3–198.5pt entre os 19 blocos (indentação depende do conteúdo da
# célula AGENTE, não de grade de tabela rígida). A fronteira real usada
# aqui é MEDIDA POR BLOCO a partir da própria linha de cabeçalho da tabela
# de riscos (GRUPO/PERIGO-ASPECTO/FONTE/AGRAVO) — ver
# `_localizar_cabecalho_tabela`. GRUPO@~57 e AGENTE-início(PERIGO/ASPECTO)
# @~113 são estáveis nas 19 páginas-âncora medidas (003.DZ) e servem só de
# SANITY-CHECK contra família errada, nunca de fronteira de atribuição.
_X_GRUPO_ESPERADO = 57.0
_X_AGENTE_ESPERADO = 113.0
_TOLERANCIA_SANITY_PT = 5.0

# Tolerância de atribuição de coluna: varredura-invariante sobre os 19
# blocos (003.DZ, script de medição ad-hoc) mediu desalinhamento máximo
# 0,00pt entre a 1ª palavra de cada célula de dado e o x0 do cabeçalho do
# próprio bloco — 3pt é folga sobre o pior caso medido (GHE16, dado@177.0
# vs. header@177.5), não recalibrar sem nova medição.
_TOLERANCIA_COLUNA_PT = 3.0

# Tolerância de agrupamento de palavras em linha (mesma técnica da
# varredura-invariante 003.DZ).
_TOLERANCIA_LINHA_PT = 2.5

_TOKENS_CATEGORIA = frozenset(
    {"FISICO", "QUIMICO", "ERGONOMICO", "ACIDENTE", "BIOLOGICO"}
)


class FamiliaNaoReconhecida(ValueError):
    """Bloco não casa a forma medida da família Consciente/Fascino (D-ARQ-65
    fatia 2) — sinal de roteamento para o caller decidir o fallback LLM,
    distinto de ValueError genérico."""


class PalavraPDF(NamedTuple):
    """Palavra pré-extraída de uma página do PDF — contrato mínimo que o
    núcleo puro consome (texto + posição), independente do extrator real
    (pdfplumber no wrapper `parsear_arquivo`)."""

    text: str
    x0: float
    top: float


class _Linha(NamedTuple):
    """Palavras da mesma linha física, ordenadas por x0 (ordem de leitura
    esquerda→direita) — necessário tanto para reconstrução de texto
    (âncoras, rótulos) quanto para atribuição de coluna por x0."""

    palavras: tuple[PalavraPDF, ...]

    @property
    def texto(self) -> str:
        return " ".join(p.text for p in self.palavras)


def _agrupar_linhas(palavras: Sequence[PalavraPDF]) -> list[_Linha]:
    """Agrupa palavras de UMA página em linhas por tolerância de `top`.
    Nova linha quando o `top` foge mais que _TOLERANCIA_LINHA_PT do `top`
    da linha corrente — mesma técnica da varredura-invariante 003.DZ que
    validou a calibração por bloco (max|delta|=0,00pt em todos os 19
    blocos, 237/237 linhas-de-categoria contadas)."""
    ordenadas = sorted(palavras, key=lambda p: p.top)
    linhas: list[list[PalavraPDF]] = []
    topo_atual: Optional[float] = None
    for p in ordenadas:
        if topo_atual is None or abs(p.top - topo_atual) > _TOLERANCIA_LINHA_PT:
            linhas.append([])
            topo_atual = p.top
        linhas[-1].append(p)
    return [_Linha(tuple(sorted(grupo, key=lambda p: p.x0))) for grupo in linhas]


# Extração do título — NÃO duplica o reconhecimento de âncora (eh_cabecalho_ghe,
# extracao_pgr.py, D-ARQ-57 peça 1); só recorta o que sobra depois do "GHE NN"
# reconhecido. Separador de layout (espaço/traço/NUL) imediatamente após o
# número é descartado; U+0000 embutido no título em si (ex.: "HIDRO\x00SANITÁRIAS",
# GHE 10) SOBREVIVE — não é normalização, é o mesmo glifo-de-fonte já
# documentado em D-ARQ-57 peça 1 / 003.DS.
_PADRAO_TITULO_ANCORA = re.compile(r"GHE:?\s*\d+\s*[-\x00]\s*(?P<titulo>.+)")
# Forma 6 de eh_cabecalho_ghe (separador ANTES do número, título pode vir só
# após espaço): "GHE - 14 PINTURA", "GHE\x00 01 \x00 ADMINISTRAÇÃO 01" —
# DT-(sessão claude/hopeful-newton-yjv3k7)-01. Padrão à parte para não
# alargar o de cima, que exige separador depois do número.
_PADRAO_TITULO_ANCORA_SEPARADOR_ANTES = re.compile(
    r"GHE\s*[-\x00]\s*\d+(?:\s*[-\x00]\s*|\s+)(?P<titulo>.+)"
)


def _extrair_titulo_ancora(linha_texto: str) -> str:
    """nome = resto da linha-âncora, VERBATIM (U+0000 preservado)."""
    m = _PADRAO_TITULO_ANCORA.match(linha_texto) or (
        _PADRAO_TITULO_ANCORA_SEPARADOR_ANTES.match(linha_texto)
    )
    if m is None:
        return ""
    return m.group("titulo").strip()


def _eh_linha_rotulo_cargo(linha: _Linha) -> bool:
    palavras = linha.palavras
    return (
        len(palavras) >= 3
        and palavras[0].text == "Cargo"
        and palavras[1].text == "/"
        and palavras[2].text.startswith("Fun")
    )


# Separador ENTRE entradas de cargo da célula (003.EP fatia 2, M3): vírgula
# na maioria dos blocos, ponto-e-vírgula em GHE-07/PRODUÇÃO (medição 41
# entradas / 19 blocos). NUNCA \x00 — o glifo ocorre DENTRO de nome
# composto (classe já registrada em HIDRO\x00SANITÁRIAS, D-ARQ-57 peça 1),
# dividir por ele quebraria um nome ao meio.
_PADRAO_DELIMITADOR_ENTRADAS = re.compile(r"[,;]")

# Código CBO-2002 dentro da célula: família de 4 dígitos (5 em 1/41 do
# Fascino, "Encarregado de Elétrica 99501\x0005\x00", DT-003EO-04) +
# ocupação de 2, com glifos-separadores (\x00, espaço, hífen) em volta.
# Exige dígito: a versão anterior (`[\d\x00\s-]+`, corrida final) casava
# espaço puro e, em cargo SEM CBO, cortava a última palavra ("Operador de
# Betoneira" -> "Operador de", 26/51 cargos em Porto Araras I). O código
# também separa entradas: no Vila Brasil Escritório a vírgula entre dois
# cargos falta e só o CBO os divide ("Analista de Produtos SR l
# \x001423\x0030\x00 Coordenador de Marketing"). DT-(sessão
# claude/hopeful-newton-yjv3k7)-01.
_PADRAO_CBO = re.compile(r"[\s\x00-]*\d{4,5}[\s\x00-]*\d{2}[\s\x00-]*")


def _separar_cargos_da_celula(celula: str) -> tuple[str, ...]:
    """Um nome por cargo: entradas separadas por vírgula/ponto-e-vírgula e
    por código CBO; o CBO é DESCARTADO (003.EP fatia 2 — nenhum consumidor
    a jusante lê CBO; candidato natural é a faceta de máquina pesada,
    DT-003ED-01). \x00 interno ao nome sobrevive; só as bordas são
    aparadas. Trecho sem letra não é cargo (o "." final após o CBO do GHE
    OPERAÇÃO DE GRUA do Fascino)."""
    nomes = (
        trecho.strip(" \x00-")
        for entrada in _PADRAO_DELIMITADOR_ENTRADAS.split(celula)
        for trecho in _PADRAO_CBO.split(entrada)
    )
    return tuple(nome for nome in nomes if any(c.isalpha() for c in nome))


def _extrair_cargos_da_linha(
    linhas_bloco: Sequence[_Linha], idx_rotulo: int
) -> tuple[str, ...]:
    """cargos = nomes distintos da célula "Cargo / Função" — rótulo MAIS as
    linhas físicas seguintes cuja 1ª palavra cai na banda do valor
    (overflow, 003.EP fatia 1), separados entrada a entrada e com a cauda
    CBO removida (003.EP fatia 2). Uma tupla por cargo distinto, não mais
    uma célula inteira como string única.

    Banda do valor = x0 de `palavras[3]` da própria linha de rótulo, com a
    mesma `_TOLERANCIA_COLUNA_PT` da banda AGENTE/FONTE (calibração por
    bloco, não constante fixa). Medição 003.EP fatia 0 (`relatorios/
    003ep_anatomia_cargo.md`, M1/M2, 19/19 blocos do Fascino): onde existe
    continuação real (2/19 blocos — GHE-03, GHE-06), o desvio contra a
    banda do valor é 0,0pt exato; a linha que encerra a célula tem x0 na
    banda do RÓTULO (não na do valor) — por isso o critério de parada é a
    própria condição do laço (sai da banda do valor), sem ancorar no
    literal do próximo rótulo (que nunca foi verificado contra o
    repertório de campos do formulário).

    LIMITE QUE A FATIA 1 FECHOU (D-ARQ-65 fatia 1 / DT-003EO-04): antes
    desta função só lia a linha do próprio rótulo — 6 dos 41 cargos do
    gabarito (GHE-03: 4; GHE-06: 2) se perdiam por quebra de linha física
    na tabela (ex.: "Encarregado" no fim do rótulo + "de Pintor..." na
    continuação). Junção entre linhas físicas é espaço simples (medido).
    Separação de entradas e descarte do CBO: ver `_separar_cargos_da_celula`
    / `_PADRAO_CBO`."""
    linha_rotulo = linhas_bloco[idx_rotulo]
    palavras_rotulo = linha_rotulo.palavras
    partes = [p.text for p in palavras_rotulo[3:]]
    if len(palavras_rotulo) > 3:
        x0_valor = palavras_rotulo[3].x0
        for linha in linhas_bloco[idx_rotulo + 1 :]:
            x0_primeira = linha.palavras[0].x0
            if abs(x0_primeira - x0_valor) > _TOLERANCIA_COLUNA_PT:
                break
            partes.append(linha.texto)
    celula = " ".join(partes).strip()
    return _separar_cargos_da_celula(celula) if celula else ()


def _localizar_cabecalho_tabela(
    linhas: Sequence[_Linha],
) -> Optional[tuple[float, float, float, float]]:
    """Localiza, dentro do bloco, os x0 medidos do cabeçalho da tabela de
    riscos DESTE bloco (grupo, agente, fonte, agravo) — a calibração por
    bloco que substitui as constantes de banda fixas (correção do
    Arquiteto ao bloqueador de bandas, D-ARQ-65 fatia 1). None se
    não-localizável — BLOQUEADOR (bloco sem cabeçalho de tabela é forma
    inesperada para a família, não um dado a tolerar em silêncio).

    Cabeçalho real mede DUAS linhas físicas (top≈341.7 "PERIGO / ..." e
    top≈347.0 "GRUPO ... FONTE ... AGRAVO ..."; medição 003.DZ) — GRUPO,
    FONTE e AGRAVO são exigidos na MESMA linha (âncora robusta); PERIGO
    (ou sua continuação "ASPECTO") é buscado separadamente em qualquer
    linha do bloco, por ser estável (~113, sanity-check) e não partilhar
    linha física com os outros três.
    """
    grupo_fonte_agravo: Optional[tuple[float, float, float]] = None
    for linha in linhas:
        textos = {p.text for p in linha.palavras}
        if {"GRUPO", "FONTE", "AGRAVO"} <= textos:
            grupo_x = next(p.x0 for p in linha.palavras if p.text == "GRUPO")
            fonte_x = next(p.x0 for p in linha.palavras if p.text == "FONTE")
            agravo_x = next(p.x0 for p in linha.palavras if p.text == "AGRAVO")
            grupo_fonte_agravo = (grupo_x, fonte_x, agravo_x)
            break
    if grupo_fonte_agravo is None:
        return None

    agente_x: Optional[float] = None
    for linha in linhas:
        for p in linha.palavras:
            if p.text in ("PERIGO", "ASPECTO"):
                agente_x = p.x0
                break
        if agente_x is not None:
            break
    if agente_x is None:
        return None

    grupo_x, fonte_x, agravo_x = grupo_fonte_agravo
    return grupo_x, agente_x, fonte_x, agravo_x


def _banda(
    x0: float, agente_x: float, fonte_x: float, agravo_x: float
) -> Optional[str]:
    if agente_x - _TOLERANCIA_COLUNA_PT <= x0 < fonte_x - _TOLERANCIA_COLUNA_PT:
        return "agente"
    if fonte_x - _TOLERANCIA_COLUNA_PT <= x0 < agravo_x - _TOLERANCIA_COLUNA_PT:
        return "fonte"
    return None


def _extrair_riscos(
    linhas: Sequence[_Linha], agente_x: float, fonte_x: float, agravo_x: float
) -> tuple[RiscoVerbatim, ...]:
    """Uma RiscoVerbatim por linha iniciada por token de categoria
    (FISICO|QUIMICO|ERGONOMICO|ACIDENTE|BIOLOGICO) na banda GRUPO.

    agente/fonte_geradora agregam palavras da banda correspondente ao
    longo de TODAS as linhas do risco — a linha-âncora do risco + linhas de
    continuação na mesma banda — até a próxima linha de categoria ou o fim
    do bloco. Medição 003.DZ confirmou o caso multi-linha real: GHE 16
    "Destilados \x00Petróleo) leves tratados com hidrogênio." (3 linhas de
    continuação em AGENTE) e "Vibrações localizadas (mão e braço)" (2
    linhas de continuação); em ambos a banda FONTE de um risco de agente
    curto (ex.: GHE 01 "Ruido") segue continuando várias linhas além do
    fim do agente — por isso o span do risco não termina quando uma banda
    específica pára, só quando NENHUMA das duas tem conteúdo na linha.
    """
    riscos: list[RiscoVerbatim] = []
    i = 0
    n = len(linhas)
    while i < n:
        primeira = linhas[i].palavras[0] if linhas[i].palavras else None
        if primeira is None or primeira.text not in _TOKENS_CATEGORIA:
            i += 1
            continue
        agente_palavras: list[str] = []
        fonte_palavras: list[str] = []
        j = i
        while j < n:
            linha_j = linhas[j]
            if j != i:
                primeira_j = linha_j.palavras[0] if linha_j.palavras else None
                if primeira_j is not None and primeira_j.text in _TOKENS_CATEGORIA:
                    break
            tem_conteudo = False
            for p in linha_j.palavras:
                banda = _banda(p.x0, agente_x, fonte_x, agravo_x)
                if banda == "agente":
                    agente_palavras.append(p.text)
                    tem_conteudo = True
                elif banda == "fonte":
                    fonte_palavras.append(p.text)
                    tem_conteudo = True
            if j != i and not tem_conteudo:
                break
            j += 1
        riscos.append(
            RiscoVerbatim(
                agente=" ".join(agente_palavras).strip(),
                # família qualitativa — zero quantificação numérica medida
                # nas 237 linhas-de-risco dos 19 blocos (003.DZ).
                quantificacao="",
                fonte_geradora=" ".join(fonte_palavras).strip(),
            )
        )
        i = j
    return tuple(riscos)


def _parsear_bloco(linhas_bloco: Sequence[_Linha]) -> GHEVerbatim:
    ancora = linhas_bloco[0]
    nome = _extrair_titulo_ancora(ancora.texto)

    cargos: tuple[str, ...] = ()
    for idx_linha, linha in enumerate(linhas_bloco[1:], start=1):
        if _eh_linha_rotulo_cargo(linha):
            cargos = _extrair_cargos_da_linha(linhas_bloco, idx_linha)
            break

    cabecalho = _localizar_cabecalho_tabela(linhas_bloco)
    if cabecalho is None:
        raise FamiliaNaoReconhecida(
            f"Bloco {nome!r}: cabeçalho de tabela (GRUPO/PERIGO/FONTE/AGRAVO) "
            "não localizado — bloqueador de calibração por bloco (D-ARQ-65 fatia 1)"
        )
    grupo_x, agente_x, fonte_x, agravo_x = cabecalho
    if (
        abs(grupo_x - _X_GRUPO_ESPERADO) > _TOLERANCIA_SANITY_PT
        or abs(agente_x - _X_AGENTE_ESPERADO) > _TOLERANCIA_SANITY_PT
    ):
        raise FamiliaNaoReconhecida(
            f"Bloco {nome!r}: cabeçalho fora do sanity-check GRUPO~57/AGENTE~113 "
            f"(medido grupo={grupo_x}, agente={agente_x}) — família pode não ser "
            "Consciente/Fascino (D-ARQ-65 fatia 1)"
        )

    riscos = _extrair_riscos(linhas_bloco, agente_x, fonte_x, agravo_x)
    return GHEVerbatim(nome=nome, cargos=cargos, riscos=riscos)


def parsear_paginas(paginas: Sequence[Sequence[PalavraPDF]]) -> tuple[GHEVerbatim, ...]:
    """Núcleo puro do parser determinístico da família Consciente/Fascino
    (D-ARQ-65 fatia 1). Recebe palavras pré-extraídas por página (ordem do
    documento) e devolve um GHEVerbatim por bloco.

    Segmentação por bloco reusa eh_cabecalho_ghe (extracao_pgr.py, D-ARQ-57
    peça 1) — mesmo repertório de âncora da rota LLM, sem regex duplicada.
    Zero âncoras -> tupla vazia (falha explícita; Pendencia é decisão do
    roteamento, D-ARQ-65 fatia 2, fora desta fatia).
    """
    todas_linhas: list[_Linha] = []
    indices_ancora: list[int] = []
    for palavras_pagina in paginas:
        for linha in _agrupar_linhas(palavras_pagina):
            if eh_cabecalho_ghe(linha.texto):
                indices_ancora.append(len(todas_linhas))
            todas_linhas.append(linha)

    ghes: list[GHEVerbatim] = []
    for k, inicio in enumerate(indices_ancora):
        fim = indices_ancora[k + 1] if k + 1 < len(indices_ancora) else len(todas_linhas)
        ghes.append(_parsear_bloco(todas_linhas[inicio:fim]))
    return tuple(ghes)


def parsear_arquivo(caminho: Path) -> tuple[GHEVerbatim, ...]:
    """Wrapper de I/O (D-ARQ-09): único ponto do módulo que toca disco.
    pdfplumber.extract_words -> PalavraPDF -> parsear_paginas (núcleo
    puro)."""
    paginas = [
        tuple(
            PalavraPDF(text=w["text"], x0=w["x0"], top=w["top"])
            for w in page.extract_words()
        )
        for page in paginas_liberadas(caminho)
    ]
    return parsear_paginas(paginas)
