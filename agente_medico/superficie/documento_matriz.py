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
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Observacao

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


# D-ARQ-73, nota de aplicação desta sessão: paleta reaproveitada de
# `modules/modulo_pcmso.py::gerar_docx_rq61`
# (v9.5, já em produção no legado) — não é identidade visual de terceiro, é só a
# cor que o escritório já usa; troca-se em um lugar só se decidirem por outra.
_COR_DESTAQUE = RGBColor(0x08, 0x4D, 0x22)
_COR_DESTAQUE_HEX = "084D22"
_COR_TEXTO_SOBRE_DESTAQUE = RGBColor(0xFF, 0xFF, 0xFF)


def _aplicar_fundo(celula: Any, cor_hex: str) -> None:
    """Cor de fundo de célula via XML — python-docx não expõe shading na API
    pública. Mesma técnica de `modulo_pcmso.py::_set_cell_background`."""
    propriedades = celula._tc.get_or_add_tcPr()
    sombreado = OxmlElement("w:shd")
    sombreado.set(qn("w:fill"), cor_hex)
    sombreado.set(qn("w:color"), "auto")
    sombreado.set(qn("w:val"), "clear")
    propriedades.append(sombreado)


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


def _formatar_observacao(obs: Observacao, exames_vocab: dict[str, Any]) -> str:
    # Forma da anotação do gabarito Fascino ("Incluir no word do PCMSO, risco
    # baixo no PGR para acetona e metiletilcetona"), uma por agente.
    exames = ", ".join(
        exames_vocab.get(slug, {}).get("nome_exibicao", slug) for slug in obs.exames_dispensados
    )
    agente = obs.agente.replace("_", " ")
    if obs.medicao is not None:
        # D-ARQ-86 cl.6: a dispensa em BAIXO vem da medição, e a célula leva o laudo.
        return _sanitizar(
            f"Obs.: risco {obs.nivel_risco.lower()} no PGR e medição abaixo do nível de ação "
            f"para {agente} ({obs.medicao}) — incluir menção no PCMSO; não solicitado: {exames}"
        )
    return _sanitizar(
        f"Obs.: risco {obs.nivel_risco.lower()} no PGR para {agente} — incluir menção "
        f"no PCMSO; não solicitado: {exames}"
    )


def _celulas_da_matriz(
    matriz: MatrizGHE, exames_vocab: dict[str, Any]
) -> tuple[str, ...]:
    ordenadas = sorted(matriz.linhas, key=lambda e: _chave_ordem_exame(e.exame, exames_vocab))
    return tuple(_formatar_celula(e, exames_vocab) for e in ordenadas) + tuple(
        _formatar_observacao(o, exames_vocab) for o in matriz.observacoes
    )


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

    Estilo (D-ARQ-73, nota de aplicação desta sessão): borda, cabeçalho de
    coluna com fundo e texto brancos, título e cabeçalho de GHE coloridos —
    portado de `modulo_pcmso.py::gerar_docx_rq61` (legado). Conteúdo e
    contagem de tabelas/linhas idênticos às fatias 1-3; só a aparência muda.
    """
    c = doc.cabecalho
    r = doc.rodape
    documento = Document()

    for secao in documento.sections:
        secao.top_margin = secao.bottom_margin = Cm(2)
        secao.left_margin = secao.right_margin = Cm(2)

    titulo_documento = documento.add_paragraph()
    titulo_documento.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run_titulo = titulo_documento.add_run(c.tipo_documento)
    run_titulo.bold = True
    run_titulo.font.size = Pt(16)
    run_titulo.font.color.rgb = _COR_DESTAQUE

    documento.add_paragraph(f"Empresa: {c.empresa}")
    documento.add_paragraph(f"Obra: {c.obra}")
    documento.add_paragraph(f"Data: {c.data}")
    documento.add_paragraph(f"{c.medico_coordenador} | {c.crm}")

    for bloco in doc.blocos:
        titulo = f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip()
        cabecalho_ghe = documento.add_heading(titulo, level=2)
        if cabecalho_ghe.runs:
            cabecalho_ghe.runs[0].font.color.rgb = _COR_DESTAQUE

        tabela = documento.add_table(rows=1, cols=2)
        tabela.style = "Table Grid"
        cabecalho_linha = tabela.rows[0].cells
        for indice, rotulo in enumerate(("FUNÇÃO", "EXAMES SOLICITADOS")):
            celula = cabecalho_linha[indice]
            celula.text = rotulo
            paragrafo = celula.paragraphs[0]
            paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if paragrafo.runs:
                paragrafo.runs[0].bold = True
                paragrafo.runs[0].font.color.rgb = _COR_TEXTO_SOBRE_DESTAQUE
            _aplicar_fundo(celula, _COR_DESTAQUE_HEX)
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
