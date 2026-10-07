"""Estrutura intermediária + emissor HTML da matriz de saída no formato do
escritório (D-ARQ-73). Mora em superficie/, ao lado de apresentacao_matriz.py
(D-ARQ-72 cl.2). Apresentação-pura sobre MatrizGHE + vocabulário de exames,
lógica-de-domínio zero (D-ARQ-54 P1 / D-ARQ-72, herdadas) — nenhuma regra
clínica nova, nenhum R-* tocado.
"""

from __future__ import annotations

import html
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

import unicodedata

from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_ROW_HEIGHT_RULE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor, Twips

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


def nome_ghe_exibicao(nome: str) -> str:
    """Nome do GHE para tela e documento; MatrizGHE.nome_ghe segue verbatim.
    NUL entre espaços é o hífen separador que a fonte do PGR não mapeia para
    Unicode (Vila Brasil GHE 23, "MANUTENÇÃO \\x00 ENERGIZADA" impresso
    "MANUTENÇÃO - ENERGIZADA"); NUL colado em texto pode ser outro glifo
    (parêntese no CBO) e só é removido."""
    return _sanitizar(nome.replace(" \x00 ", " - "))


def titulo_ghe(ghe_id: str, nome_ghe: str) -> str:
    """Código do GHE uma vez só: o nome que o PGR escreve com o próprio código na
    frente ("GHE 01 - ADMINISTRAÇÃO" no GHE-01) perde a repetição."""
    codigo = ghe_id if ghe_id.upper().startswith("GHE") else f"GHE {ghe_id}"
    numero = re.search(r"\d+", ghe_id)
    nome = nome_ghe
    if numero:
        nome = re.sub(rf"^GHE[\s-]*0*{int(numero[0])}(?!\d)\s*[-–—]?\s*", "", nome_ghe, flags=re.IGNORECASE)
    return f"{codigo} — {nome}" if nome else codigo


def titulo_ghe_rq61(ghe_id: str, nome_ghe: str) -> str:
    """Faixa do GHE como as matrizes RQ.61 a escrevem ("GHE 01 - BETONEIRA"): código
    com espaço e número, hífen, nome sem repetir o código."""
    numero = re.search(r"\d+", ghe_id)
    codigo = f"GHE {numero[0]}" if numero else ghe_id
    nome = nome_ghe
    if numero:
        nome = re.sub(rf"^GHE[\s-]*0*{int(numero[0])}(?!\d)\s*[-–—]?\s*", "", nome_ghe, flags=re.IGNORECASE)
    return f"{codigo} - {nome}" if nome else codigo


# D-ARQ-73, nota de aplicação desta sessão: paleta reaproveitada de
# `modules/modulo_pcmso.py::gerar_docx_rq61`
# (v9.5, já em produção no legado) — não é identidade visual de terceiro, é só a
# cor que o escritório já usa; troca-se em um lugar só se decidirem por outra.
# Título do formulário RQ.61 do escritório, como o cabeçalho das matrizes do acervo o escreve.
TITULO_MATRIZ = "MATRIZ FUNÇÃO – EXAMES PCMSO"

_COR_DESTAQUE = RGBColor(0x08, 0x4D, 0x22)
_COR_DESTAQUE_HEX = "084D22"
_COR_TEXTO_SOBRE_DESTAQUE = RGBColor(0xFF, 0xFF, 0xFF)

# D-ARQ-73, emenda de 07/10/2026: a matriz Word segue o leiaute das matrizes RQ.61 das
# médicas (medido em 4 de setembro/2026: Vila Brasil 24/09, T65 24/09, Engeseg 22/09,
# Varandas 16/09). O memorial e o relatório do ASO seguem com a paleta acima.
# Larguras em twips, como no modelo; o logo da empresa fica fora (célula vazia).
_COR_FAIXA_GHE_HEX = "83CAEB"
_FONTE_CORPO = "Calibri"
_FONTE_CABECALHO = "Arial"
_FAIXA_QUALIDADE = ("SISTEMA DE GESTÃO DA QUALIDADE - NBR ISO 9001:2015", "RQ – REGISTRO DA QUALIDADE")
_IDENTIFICACAO_RQ61 = "RQ.61"
_REVISAO_RQ61 = "20/10/2024"
_VERSAO_RQ61 = "06"
_TIPOS_DOCUMENTO = ("Obra Nova", "Atualização", "Adendo", "Funções Iniciais")
_LARGURAS_FAIXA = (7292, 2347)
_LARGURAS_TITULO = (7300, 1417, 1068)
_LARGURAS_IDENTIFICACAO = (4931, 598, 4110)
_LARGURAS_GHE = (4962, 4677)


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

    def crm_formatado(self) -> str:
        """O CRM digitado só com o número ganha o prefixo "CRM", sem duplicar quando já
        vem escrito ("CRM-GO 14.949")."""
        crm = self.crm.strip()
        if crm and not crm.upper().startswith("CRM"):
            crm = f"CRM {crm}"
        return crm

    def linha_coordenador(self) -> str:
        """Rótulo das matrizes RQ.61 do acervo."""
        crm = self.crm_formatado()
        identificacao = " — ".join(parte for parte in (self.medico_coordenador.strip(), crm) if parte)
        return f"Médico(a) Coordenador(a) do PCMSO: {identificacao}".rstrip()


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

    def linhas(self) -> tuple[str, ...]:
        """Rótulos do rodapé das matrizes RQ.61 do acervo; o rótulo fica mesmo com o
        valor em branco, para preenchimento à mão, como nos gabaritos."""
        return tuple(
            f"{rotulo} {valor}".rstrip()
            for rotulo, valor in (
                ("Responsável pelo preenchimento:", self.responsavel_preenchimento),
                ("Médico(a) Responsável pela validação:", self.medico_validador),
                ("Data do PGR:", self.data_pgr),
            )
        )


@dataclass(frozen=True)
class DocumentoMatriz:
    cabecalho: CabecalhoDocumento
    blocos: tuple[BlocoGHE, ...]
    rodape: RodapeDocumento


def _chave_ordem_exame(slug: str, exames_vocab: dict[str, Any]) -> tuple[int, int, int, str]:
    # 003.EO EMENDA 1: ordem_exibicao é opcional no vocabulário — só os slugs
    # medidos no gabarito o carregam. Quem tem vai primeiro (tag 0, por valor);
    # quem não tem vai depois (tag 1), desempatado por slug alfabético — nunca
    # por um sentinela numérico solto (isso reabriria a classe D-ARQ-67: um
    # `.get(..., 0)` faria o exame sem ordem subir para o topo).
    # D-ARQ-73, nota de 01/10/2026: `bloco_exibicao: fim` põe o exame depois dos
    # sem ordem (os indicadores biológicos ficam entre os laboratoriais e
    # Espirometria/RX/Saúde Mental/Psicossocial, como nos gabaritos de 2026).
    entrada = exames_vocab.get(slug, {})
    bloco = 1 if entrada.get("bloco_exibicao") == "fim" else 0
    ordem = entrada.get("ordem_exibicao")
    if ordem is not None:
        return (bloco, 0, ordem, slug)
    return (bloco, 1, 0, slug)


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
            BlocoGHE(ghe_id=matriz.ghe_id, nome_ghe=nome_ghe_exibicao(matriz.nome_ghe), linhas=linhas)
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
        f"<h1>{html.escape(TITULO_MATRIZ)}</h1>",
        f"<p>Empresa: {html.escape(c.empresa)}</p>",
        f"<p>Obra: {html.escape(c.obra)}</p>",
        *([f"<p>Tipo: {html.escape(c.tipo_documento)}</p>"] if c.tipo_documento.strip() else []),
        f"<p>Data: {html.escape(c.data)}</p>",
        f"<p>{html.escape(c.linha_coordenador())}</p>",
    ]
    for bloco in doc.blocos:
        partes.append(f"<h2>{html.escape(titulo_ghe(bloco.ghe_id, bloco.nome_ghe))}</h2>")
        partes.append("<table>")
        partes.append("<tr><th>FUNÇÃO</th><th>EXAMES SOLICITADOS</th></tr>")
        for linha in bloco.linhas:
            celulas_html = " | ".join(html.escape(cel) for cel in linha.celulas)
            partes.append(
                f"<tr><td>{html.escape(linha.cargo)}</td><td>{celulas_html}</td></tr>"
            )
        partes.append("</table>")
    partes.extend(f"<p>{html.escape(linha)}</p>" for linha in r.linhas())
    partes.append("</div>")
    return "\n".join(partes)


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)).casefold()


def _tipo_marcado(tipo_documento: str) -> str | None:
    """Qual das quatro opções do RQ.61 o tipo digitado marca; None se nenhuma."""
    digitado = _sem_acento(tipo_documento.strip())
    if not digitado:
        return None
    return next((t for t in _TIPOS_DOCUMENTO if digitado.startswith(_sem_acento(t))), None)


def _larguras(tabela: Any, larguras: Sequence[int]) -> None:
    tabela.autofit = False
    grade = tabela._tbl.tblGrid
    for coluna, largura in zip(grade.findall(qn("w:gridCol")), larguras):
        coluna.set(qn("w:w"), str(largura))
    for linha in tabela.rows:
        for celula, largura in zip(linha.cells, larguras):
            celula.width = Twips(largura)


def _altura(linha: Any, twips: int, regra: WD_ROW_HEIGHT_RULE = WD_ROW_HEIGHT_RULE.AT_LEAST) -> None:
    linha.height = Twips(twips)
    linha.height_rule = regra


def _sem_bordas(celula: Any) -> None:
    bordas = OxmlElement("w:tcBorders")
    for lado in ("top", "right", "bottom"):
        borda = OxmlElement(f"w:{lado}")
        borda.set(qn("w:val"), "nil")
        bordas.append(borda)
    celula._tc.get_or_add_tcPr().append(bordas)


def _escrever(
    paragrafo: Any,
    texto: str,
    *,
    negrito: bool = False,
    italico: bool = False,
    tamanho: float | None = None,
    fonte: str | None = None,
) -> Any:
    run = paragrafo.add_run(texto)
    run.bold = negrito
    run.italic = italico
    if tamanho is not None:
        run.font.size = Pt(tamanho)
    if fonte is not None:
        run.font.name = fonte
    return run


def _campo(paragrafo: Any, instrucao: str, *, tamanho: float, fonte: str) -> None:
    """Campo do Word (PAGE / NUMPAGES), recalculado ao abrir o documento."""
    campo = OxmlElement("w:fldSimple")
    campo.set(qn("w:instr"), instrucao)
    run = _escrever(paragrafo, "1", negrito=True, tamanho=tamanho, fonte=fonte)
    run._r.addprevious(campo)
    campo.append(run._r)


def _celula_rotulo_valor(celula: Any, rotulo: str, valor: str, *, campo_pagina: bool = False) -> None:
    celula.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    _escrever(celula.paragraphs[0], rotulo, tamanho=9, fonte=_FONTE_CABECALHO)
    paragrafo = celula.add_paragraph()
    paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if campo_pagina:
        _campo(paragrafo, "PAGE", tamanho=9, fonte=_FONTE_CABECALHO)
        _escrever(paragrafo, " / ", negrito=True, tamanho=9, fonte=_FONTE_CABECALHO)
        _campo(paragrafo, "NUMPAGES", tamanho=9, fonte=_FONTE_CABECALHO)
    else:
        _escrever(paragrafo, valor, negrito=True, tamanho=9, fonte=_FONTE_CABECALHO)


def _cabecalho_de_pagina(secao: Any) -> None:
    """Cabeçalho repetido em toda página, como o RQ.61: faixa do sistema da qualidade
    (o espaço do logo fica vazio — a empresa varia) e o quadro do título com
    identificação, página, revisão e versão do formulário."""
    cabecalho = secao.header
    cabecalho.is_linked_to_previous = False
    paragrafo_final = cabecalho.paragraphs[0]

    faixa = cabecalho.add_table(rows=1, cols=2, width=Twips(sum(_LARGURAS_FAIXA)))
    faixa.style = "Table Grid"
    _larguras(faixa, _LARGURAS_FAIXA)
    _altura(faixa.rows[0], 846, WD_ROW_HEIGHT_RULE.EXACTLY)
    caixa, logo = faixa.rows[0].cells
    caixa.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    for indice, texto in enumerate(_FAIXA_QUALIDADE):
        paragrafo = caixa.paragraphs[0] if indice == 0 else caixa.add_paragraph()
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        _escrever(paragrafo, texto, negrito=indice == 0, tamanho=11, fonte=_FONTE_CABECALHO)
    _sem_bordas(logo)

    espaco = cabecalho.add_paragraph()
    espaco.paragraph_format.line_spacing = Pt(6)

    quadro = cabecalho.add_table(rows=2, cols=3, width=Twips(sum(_LARGURAS_TITULO)))
    quadro.style = "Table Grid"
    _larguras(quadro, _LARGURAS_TITULO)
    for linha in quadro.rows:
        _altura(linha, 420)
    titulo = quadro.cell(0, 0).merge(quadro.cell(1, 0))
    titulo.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
    titulo.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _escrever(titulo.paragraphs[0], TITULO_MATRIZ, negrito=True, italico=True, tamanho=16, fonte=_FONTE_CABECALHO)
    _celula_rotulo_valor(quadro.cell(0, 1), "Identificação:", _IDENTIFICACAO_RQ61)
    _celula_rotulo_valor(quadro.cell(0, 2), "Página:", "", campo_pagina=True)
    _celula_rotulo_valor(quadro.cell(1, 1), "Revisão:", _REVISAO_RQ61)
    _celula_rotulo_valor(quadro.cell(1, 2), "Versão:", _VERSAO_RQ61)

    # O cabeçalho do Word termina num parágrafo: o vazio que já vem nele vai para o fim.
    cabecalho._element.append(paragrafo_final._p)


def _tabela_identificacao(documento: Any, c: CabecalhoDocumento) -> None:
    tabela = documento.add_table(rows=3, cols=3)
    tabela.style = "Table Grid"
    _larguras(tabela, _LARGURAS_IDENTIFICACAO)
    for linha, altura in zip(tabela.rows, (425, 425, 692)):
        _altura(linha, altura)
        for celula in linha.cells:
            celula.vertical_alignment = WD_ALIGN_VERTICAL.CENTER

    empresa = tabela.cell(0, 0).merge(tabela.cell(0, 1))
    _escrever(empresa.paragraphs[0], "Empresa:", negrito=True)
    _escrever(empresa.add_paragraph(), c.empresa, negrito=True)

    marcado = _tipo_marcado(c.tipo_documento)
    tipos = tabela.cell(0, 2)
    for indice, par_de_tipos in enumerate((_TIPOS_DOCUMENTO[:2], _TIPOS_DOCUMENTO[2:])):
        paragrafo = tipos.paragraphs[0] if indice == 0 else tipos.add_paragraph()
        for posicao, tipo in enumerate(par_de_tipos):
            if posicao:
                _escrever(paragrafo, "      ")
            _escrever(paragrafo, f"{tipo} ({'X' if tipo == marcado else '  '})", negrito=tipo == marcado)
    # Tipo digitado fora das quatro opções do formulário não some (D-ARQ-22).
    if c.tipo_documento.strip() and marcado is None:
        _escrever(tipos.add_paragraph(), f"Outro: {c.tipo_documento.strip()}", negrito=True)

    obra = tabela.cell(1, 0).merge(tabela.cell(1, 1))
    _escrever(obra.paragraphs[0], f"Obra: {c.obra}".rstrip(), negrito=True)
    data = tabela.cell(1, 2)
    data.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _escrever(data.paragraphs[0], f"Data: {c.data}".rstrip(), negrito=True)

    _escrever(tabela.cell(2, 0).paragraphs[0], "Médico(a) Coordenador(a) do PCMSO", negrito=True)
    medico = tabela.cell(2, 1).merge(tabela.cell(2, 2))
    medico.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
    _escrever(medico.paragraphs[0], c.medico_coordenador.strip())
    crm = medico.add_paragraph()
    crm.alignment = WD_ALIGN_PARAGRAPH.CENTER
    _escrever(crm, c.crm_formatado())


def _tabela_ghes(documento: Any, blocos: Sequence[BlocoGHE]) -> None:
    """Uma tabela contínua, como as matrizes das médicas: por GHE, a faixa azul com o
    nome, o cabeçalho FUNÇÃO | EXAMES SOLICITADOS e um cargo por linha, um exame por
    parágrafo."""
    tabela = documento.add_table(rows=0, cols=2)
    tabela.style = "Table Grid"
    for bloco in blocos:
        faixa = tabela.add_row().cells
        celula_ghe = faixa[0].merge(faixa[1])
        celula_ghe.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        celula_ghe.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
        _escrever(celula_ghe.paragraphs[0], titulo_ghe_rq61(bloco.ghe_id, bloco.nome_ghe), negrito=True)
        _aplicar_fundo(celula_ghe, _COR_FAIXA_GHE_HEX)

        cabecalho_colunas = tabela.add_row().cells
        for celula, rotulo in zip(cabecalho_colunas, ("FUNÇÃO", "EXAMES SOLICITADOS")):
            celula.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            celula.paragraphs[0].alignment = WD_ALIGN_PARAGRAPH.CENTER
            _escrever(celula.paragraphs[0], rotulo, negrito=True)

        for linha in bloco.linhas:
            celula_cargo, celula_exames = tabela.add_row().cells
            celula_cargo.text = linha.cargo
            if linha.celulas:
                celula_exames.paragraphs[0].text = linha.celulas[0]
                for exame_formatado in linha.celulas[1:]:
                    celula_exames.add_paragraph(exame_formatado)
    _larguras(tabela, _LARGURAS_GHE)


def renderizar_docx(doc: DocumentoMatriz, destino: Path) -> None:
    """Mesma DocumentoMatriz da fatia 2 — não recalcula nada, só renderiza, no leiaute
    das matrizes RQ.61 das médicas (D-ARQ-73, emenda de 07/10/2026): cabeçalho de
    página com o quadro do formulário, tabela de identificação (empresa, tipo,
    obra, data, coordenador) e uma tabela contínua com os GHEs. A forma é um exame
    por PARÁGRAFO dentro da célula, não uma frase concatenada por vírgula.
    """
    documento = Document()

    normal = documento.styles["Normal"]
    normal.font.name = _FONTE_CORPO
    normal.font.size = Pt(11)
    normal.paragraph_format.space_before = Pt(0)
    normal.paragraph_format.space_after = Pt(0)
    normal.paragraph_format.line_spacing = 1.0

    for secao in documento.sections:
        secao.page_width, secao.page_height = Cm(21), Cm(29.7)
        secao.left_margin = secao.right_margin = Cm(2)
        secao.top_margin, secao.bottom_margin = Cm(1.35), Cm(1.2)
        secao.header_distance = Cm(1.25)
        _cabecalho_de_pagina(secao)

    _tabela_identificacao(documento, doc.cabecalho)
    documento.add_paragraph()
    _tabela_ghes(documento, doc.blocos)
    documento.add_paragraph()

    for linha_rodape in doc.rodape.linhas():
        _escrever(documento.add_paragraph(), linha_rodape, negrito=True)
    documento.save(str(destino))
