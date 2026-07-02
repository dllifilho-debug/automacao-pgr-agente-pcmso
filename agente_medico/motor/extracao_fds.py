from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from pathlib import Path
from typing import Optional

import pdfplumber


def extrair_tabelas_fds(caminho: Path) -> list[list[list[Optional[str]]]]:
    """DEPRECATED (003.BA): entrada de composição migrou para texto-puro (D-ARQ-42);
    mantida para rastreabilidade, sem consumidor no motor.

    Parse-PDF determinístico da transcrição-FDS (D-ARQ-42 Parte 1).

    Devolve as tabelas CRUAS de extract_tables() de todas as páginas, achatadas numa
    única lista (fronteira de página DESCARTADA nesta fatia — a composição aparece em
    páginas variáveis: pág 0 em Ciplan/Tigre/tinta, pág 2 em Leinertex/Massa; o
    consumidor varre todas as tabelas procurando o header de composição, não "a tabela
    da página X").

    NÃO localiza a região de composição, NÃO interpreta coluna, NÃO desambigua o \\n
    (separador-multi-CAS vs quebra-de-render intra-token), NÃO mapeia grafias de
    CAS-ausente, NÃO monta Componente. Tudo isso é transcrição (DT-003AS-01), fatia
    seguinte. Aqui só extração bruta: bytes -> tabelas cruas, células str | None
    exatamente como o pdfplumber as devolve.

    [DERIVADO — page.extract_tables() puro, medição 003.AS sobre os 6 PDFs de
    fds_originais/; D-ARQ-43 Parte 1 (parse-PDF é camada de texto, sem OCR).]
    """
    tabelas: list[list[list[Optional[str]]]] = []
    with pdfplumber.open(caminho) as pdf:
        for page in pdf.pages:
            tabelas.extend(page.extract_tables())
    return tabelas


def _normalizar_linha(linha: str) -> str:
    """NFD + remoção de combining marks + maiúsculas — só para LOCALIZAR
    âncora/título-fim; nunca aplicada ao texto de saída (saída é VERBATIM)."""
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", linha) if not unicodedata.combining(c)
    )
    return sem_acento.upper()


_ANCORA_COMPOSICAO = "COMPOSICAO E INFORMACOES SOBRE"

# Sufixo `(OS )?INGREDIENTES` omitido de propósito: instável no acervo medido
# (Ciplan omite "OS"; Tigre quebra o título em 2 linhas intercaladas com o
# endereço da empresa — 003.BE). O trecho fixo acima já é suficiente para achar
# a âncora sem depender do sufixo.
_TITULO_FIM = re.compile(
    r"\d+\s*[–\-.]?\s*(IDENTIFICACAO DE PERIGOS|MEDIDAS DE PRIMEIROS[ -]SOCORROS)"
)


def _achar_ancora(paginas: Sequence[str]) -> Optional[tuple[int, int]]:
    for i_pag, pagina in enumerate(paginas):
        for i_ln, linha in enumerate(pagina.splitlines()):
            if _ANCORA_COMPOSICAO in _normalizar_linha(linha):
                return i_pag, i_ln
    return None


def _achar_pagina_titulo_fim(paginas: Sequence[str], pag_a: int, ln_a: int) -> int:
    linhas_pag_a = paginas[pag_a].splitlines()
    for linha in linhas_pag_a[ln_a + 1 :]:
        if _TITULO_FIM.search(_normalizar_linha(linha)):
            return pag_a
    for i_pag in range(pag_a + 1, len(paginas)):
        for linha in paginas[i_pag].splitlines():
            if _TITULO_FIM.search(_normalizar_linha(linha)):
                return i_pag
    return len(paginas) - 1


def _recortar_composicao(paginas: Sequence[str]) -> Optional[str]:
    """Núcleo puro (sem I/O) do recorte âncora-por-título da região de
    composição (D-ARQ-47 consequência; 003.AT/AX/AY — âncora-por-título sob
    entrada texto-puro, sucessora de extrair_tabelas_fds/DEPRECATED). paginas
    = extract_text() por página, na ordem do documento.

    Início: primeira linha cuja normalização contém _ANCORA_COMPOSICAO.
    Ausente -> None (falha explícita; quem transforma em Pendencia é o
    chamador, fatia futura — nunca devolver o documento inteiro como
    fallback).

    Fim por SOBRE-INCLUSÃO (003.BE): a região vai até o FIM DA PÁGINA que
    contém o primeiro título-fim (_TITULO_FIM) encontrado a partir da linha
    seguinte à âncora — NUNCA até a linha do título-fim. Medido no Tigre
    (grid fundido): "2. IDENTIFICAÇÃO DE PERIGOS" aparece ANTES de 6 dos 7
    triplos CAS/nome/faixa da composição, intercalado nas linhas seguintes;
    um corte fino na linha do título suprimiria composição em silêncio
    (anti-supressão D-ARQ-31/35; classe de erro D-ARQ-22). O ruído
    sobre-incluído é descartado a jusante pelo LLM via disciplina do triplo
    (D-ARQ-47 cláusula 5). Título-fim não encontrado -> região vai até a
    última página do documento (sobre-inclusão, direção segura — não é
    chute).

    Saída VERBATIM: linhas originais (acentos, caixa preservados),
    normalização é só para localizar. Páginas juntadas com "\\n".

    Limites (D-ARQ-22): âncora e títulos-fim derivados de n=6 (NBR 14725 BR);
    FDS escaneada fica fora (OCR é contingência D-ARQ-43 P1); FDS cuja seção
    seguinte à composição use outro título cai no ramo sobre-inclusão-até-o-fim.
    """
    ancora = _achar_ancora(paginas)
    if ancora is None:
        return None
    pag_a, ln_a = ancora
    pag_f = _achar_pagina_titulo_fim(paginas, pag_a, ln_a)

    linhas: list[str] = list(paginas[pag_a].splitlines()[ln_a:])
    for i_pag in range(pag_a + 1, pag_f + 1):
        linhas.extend(paginas[i_pag].splitlines())
    return "\n".join(linhas)


def extrair_texto_fds(caminho: Path) -> Optional[str]:
    """Wrapper de I/O de _recortar_composicao (D-ARQ-47 consequência):
    devolve o TEXTO VERBATIM da região de composição de um PDF de FDS, entrada
    de transcrever_fds (D-ARQ-47 cláusula 1, fatia futura). Sem LLM aqui.
    """
    with pdfplumber.open(caminho) as pdf:
        paginas = [page.extract_text() or "" for page in pdf.pages]
    return _recortar_composicao(paginas)
