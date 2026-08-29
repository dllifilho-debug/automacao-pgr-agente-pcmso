"""Estrutura intermediária + emissor HTML da matriz de saída no formato do
escritório (D-ARQ-73). Mora em superficie/, ao lado de apresentacao_matriz.py
(D-ARQ-72 cl.2). Apresentação-pura sobre MatrizGHE + vocabulário de exames,
lógica-de-domínio zero (D-ARQ-54 P1 / D-ARQ-72, herdadas) — nenhuma regra
clínica nova, nenhum R-* tocado.
"""

from __future__ import annotations

import html
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from docx import Document

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento

# D-ARQ-73: rótulo de apresentação por Momento (escritório) — MR->MRO, RT->RET,
# os demais idênticos ao enum. D-ARQ-67: guardado por teste computado do dado
# (test_mapa_momentos_cobre_todos_os_membros_do_enum) — todo Momento novo tem
# que ganhar entrada aqui, senão o teste cai.
_ROTULO_MOMENTO: dict[Momento, str] = {
    Momento.ADM: "ADM",
    Momento.PER: "PER",
    Momento.MR: "MRO",
    Momento.RT: "RET",
    Momento.DEM: "DEM",
}

# DH-003EG-01 ("bytes NUL do PGR vazam para o artefato de saída", correção
# candidata: "sanitizar na renderização... não no dado"): cargo verbatim do
# PGR Fascino carrega \x00 (glifo de CBO quebrado, mesma origem de
# DT-003DR-01). Sanitiza só aqui — MatrizGHE.cargos permanece verbatim, é
# evidência. Remove controle ASCII exceto tab/CR/LF.
_LIMPAR_CONTROLE = str.maketrans(
    "", "", "".join(chr(c) for c in list(range(0, 9)) + [11, 12] + list(range(14, 32)))
)


def _sanitizar(texto: str) -> str:
    return texto.translate(_LIMPAR_CONTROLE)


# Medição 0a (003.EO, gabarito Fascino 08/07/26, sequência majoritária de
# 17/19 GHEs): ordem de exibição dos momentos dentro da célula.
_ORDEM_MOMENTOS: tuple[Momento, ...] = (
    Momento.ADM,
    Momento.PER,
    Momento.MR,
    Momento.RT,
    Momento.DEM,
)


@dataclass(frozen=True)
class CabecalhoDocumento:
    empresa: str
    obra: str
    tipo_documento: str
    data: str
    medico_coordenador: str
    crm: str


@dataclass(frozen=True)
class LinhaCargo:
    cargo: str
    celulas: tuple[str, ...]


@dataclass(frozen=True)
class BlocoGHE:
    ghe_id: str
    nome_ghe: str
    linhas: tuple[LinhaCargo, ...]


@dataclass(frozen=True)
class RodapeDocumento:
    responsavel_preenchimento: str
    medico_validador: str
    data_pgr: str


@dataclass(frozen=True)
class DocumentoMatriz:
    cabecalho: CabecalhoDocumento
    blocos: tuple[BlocoGHE, ...]
    rodape: RodapeDocumento


def _chave_ordem_exame(slug: str, exames_vocab: dict[str, Any]) -> tuple[int, int, str]:
    # 003.EO EMENDA 1: ordem_exibicao é opcional no vocabulário — só os slugs
    # medidos no gabarito o carregam. Quem tem vai primeiro (tag 0, por valor);
    # quem não tem vai depois (tag 1), desempatado por slug alfabético — nunca
    # por um sentinela numérico solto (isso reabriria a classe D-ARQ-67: um
    # `.get(..., 0)` faria o exame sem ordem subir para o topo).
    ordem = exames_vocab.get(slug, {}).get("ordem_exibicao")
    if ordem is not None:
        return (0, ordem, slug)
    return (1, 0, slug)


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


def _celulas_da_matriz(
    matriz: MatrizGHE, exames_vocab: dict[str, Any]
) -> tuple[str, ...]:
    ordenadas = sorted(matriz.linhas, key=lambda e: _chave_ordem_exame(e.exame, exames_vocab))
    return tuple(_formatar_celula(e, exames_vocab) for e in ordenadas)


def montar_documento(
    matrizes: Sequence[MatrizGHE],
    exames_vocab: dict[str, Any],
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
) -> DocumentoMatriz:
    """Expansão GHE→cargo (R-GHE-01, D-ARQ-21): cada cargo de matriz.cargos
    recebe a MESMA tupla de células — herança pura, não recálculo. GHE com
    cargos == () emite bloco com linhas == () — nunca inventa placeholder.
    Cabeçalho/rodapé são parâmetro, não derivados de MatrizGHE (DT-003EO-01:
    empresa/obra/tipo-de-documento não existem no modelo do motor).
    """
    blocos: list[BlocoGHE] = []
    for matriz in matrizes:
        celulas = _celulas_da_matriz(matriz, exames_vocab)
        linhas = tuple(
            LinhaCargo(cargo=_sanitizar(cargo), celulas=celulas) for cargo in matriz.cargos
        )
        blocos.append(
            BlocoGHE(ghe_id=matriz.ghe_id, nome_ghe=_sanitizar(matriz.nome_ghe), linhas=linhas)
        )
    return DocumentoMatriz(cabecalho=cabecalho, blocos=tuple(blocos), rodape=rodape)


def renderizar_html(doc: DocumentoMatriz) -> str:
    """Um arquivo, sem CSS externo, sem JS. Tabela de 2 colunas por GHE
    (FUNÇÃO | EXAMES SOLICITADOS), no formato do gabarito. Todo conteúdo
    vindo de dado (cargo, célula, nomes do cabeçalho/rodapé) é escapado.
    """
    c = doc.cabecalho
    r = doc.rodape
    partes: list[str] = [
        "<div>",
        f"<p>Empresa: {html.escape(c.empresa)}</p>",
        f"<p>Obra: {html.escape(c.obra)}</p>",
        f"<p>{html.escape(c.tipo_documento)}</p>",
        f"<p>Data: {html.escape(c.data)}</p>",
        f"<p>{html.escape(c.medico_coordenador)} | {html.escape(c.crm)}</p>",
    ]
    for bloco in doc.blocos:
        titulo = f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip()
        partes.append(f"<h2>{html.escape(titulo)}</h2>")
        partes.append("<table>")
        partes.append("<tr><th>FUNÇÃO</th><th>EXAMES SOLICITADOS</th></tr>")
        for linha in bloco.linhas:
            celulas_html = " | ".join(html.escape(cel) for cel in linha.celulas)
            partes.append(
                f"<tr><td>{html.escape(linha.cargo)}</td><td>{celulas_html}</td></tr>"
            )
        partes.append("</table>")
    partes.extend(
        [
            f"<p>{html.escape(r.responsavel_preenchimento)}</p>",
            f"<p>{html.escape(r.medico_validador)}</p>",
            f"<p>{html.escape(r.data_pgr)}</p>",
            "</div>",
        ]
    )
    return "\n".join(partes)


def renderizar_docx(doc: DocumentoMatriz, destino: Path) -> None:
    """Mesma DocumentoMatriz da fatia 2 — não recalcula nada, só renderiza.
    Uma tabela por GHE (2 colunas, FUNÇÃO | EXAMES SOLICITADOS); a forma do
    gabarito é um exame por PARÁGRAFO dentro da célula, não uma célula-frase
    concatenada por vírgula — um emissor ingênuo (`", ".join(...)`) passaria
    numa checagem de "tem uma tabela por GHE" mas erraria a forma real.
    """
    c = doc.cabecalho
    r = doc.rodape
    documento = Document()
    documento.add_paragraph(f"Empresa: {c.empresa}")
    documento.add_paragraph(f"Obra: {c.obra}")
    documento.add_paragraph(c.tipo_documento)
    documento.add_paragraph(f"Data: {c.data}")
    documento.add_paragraph(f"{c.medico_coordenador} | {c.crm}")

    for bloco in doc.blocos:
        titulo = f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip()
        documento.add_heading(titulo, level=2)
        tabela = documento.add_table(rows=1, cols=2)
        cabecalho_linha = tabela.rows[0].cells
        cabecalho_linha[0].text = "FUNÇÃO"
        cabecalho_linha[1].text = "EXAMES SOLICITADOS"
        for linha in bloco.linhas:
            celulas_linha = tabela.add_row().cells
            celulas_linha[0].text = linha.cargo
            celula_exames = celulas_linha[1]
            if linha.celulas:
                celula_exames.paragraphs[0].text = linha.celulas[0]
                for exame_formatado in linha.celulas[1:]:
                    celula_exames.add_paragraph(exame_formatado)

    documento.add_paragraph(r.responsavel_preenchimento)
    documento.add_paragraph(r.medico_validador)
    documento.add_paragraph(r.data_pgr)
    documento.save(str(destino))
