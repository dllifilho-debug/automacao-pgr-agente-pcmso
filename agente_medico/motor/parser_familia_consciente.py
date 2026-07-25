from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path
from typing import NamedTuple, Optional

import pdfplumber

from agente_medico.motor.extracao_pgr import eh_cabecalho_ghe
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


def _extrair_titulo_ancora(linha_texto: str) -> str:
    """nome = resto da linha-âncora, VERBATIM (U+0000 preservado)."""
    m = _PADRAO_TITULO_ANCORA.match(linha_texto)
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


def _extrair_cargos_da_linha(linha: _Linha) -> tuple[str, ...]:
    """cargos = resto da linha de rótulo "Cargo / Função", VERBATIM, UMA
    entrada — separação fina de CBO/cargo individual não é desta fatia
    (D-ARQ-65 fatia 1). LIMITE CONHECIDO: cargo cuja lista dá quebra de
    linha na tabela (medido no GHE 03 — "Encarregado" seguido de "de
    Pintor..." na linha física seguinte) não é recuperado; só a linha
    física do próprio rótulo é capturada, por instrução explícita da
    sessão 003.DZ — não um bug, um escopo declarado."""
    resto = " ".join(p.text for p in linha.palavras[3:]).strip()
    return (resto,) if resto else ()


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
    for linha in linhas_bloco[1:]:
        if _eh_linha_rotulo_cargo(linha):
            cargos = _extrair_cargos_da_linha(linha)
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
    with pdfplumber.open(caminho) as pdf:
        paginas = [
            tuple(
                PalavraPDF(text=w["text"], x0=w["x0"], top=w["top"])
                for w in page.extract_words()
            )
            for page in pdf.pages
        ]
    return parsear_paginas(paginas)
