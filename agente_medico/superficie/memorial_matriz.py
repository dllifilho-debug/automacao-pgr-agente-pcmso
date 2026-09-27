"""Memorial de raciocínio da matriz (D-ARQ-87 fatia 2) — anexo separado da
matriz assinada que explica, exame a exame, qual regra pediu o quê, por que a
periodicidade ficou a que ficou e com que grau de certeza. Apresentação-pura
sobre `MatrizGHE` (D-ARQ-72): lê o que o motor já grava em `Motivo` (fatia 1)
e em `Observacao`, sem decisão clínica nova.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Motivo, Observacao
from agente_medico.superficie.documento_matriz import (
    _COR_DESTAQUE,
    _COR_DESTAQUE_HEX,
    _COR_TEXTO_SOBRE_DESTAQUE,
    _ORDEM_MOMENTOS,
    _ROTULO_MOMENTO,
    CabecalhoDocumento,
    _aplicar_fundo,
    _chave_ordem_exame,
    _sanitizar,
    nome_ghe_exibicao,
)

# Grau de certeza, do mais forte ao mais fraco (convenções de status do
# PROTOCOLO, D-ARQ-22 Parte A). Regra sem status conta como a mais fraca.
_CERTEZA: dict[str, int] = {"VALIDADO": 3, "DERIVADO": 2, "INTERPRETADO": 1}
SEM_STATUS = "(sem status)"

# Página paisagem com margens de 1,5 cm: ~24,9 cm úteis por tabela.
_COLUNAS_GHE: tuple[tuple[str, float], ...] = (
    ("Código", 4.2),
    ("Exame", 4.6),
    ("O que cada regra pediu", 10.1),
    ("Certeza", 3.0),
    ("Correção", 3.0),
)
_COLUNAS_REVISAR: tuple[tuple[str, float], ...] = (
    ("Regra", 3.4),
    ("Onde", 6.5),
    ("Fundamento", 12.0),
    ("Correção", 3.0),
)
_COLUNAS_REGRAS: tuple[tuple[str, float], ...] = (
    ("Regra", 3.4),
    ("Certeza", 3.0),
    ("Fundamento", 18.5),
)


@dataclass(frozen=True)
class LinhaMemorial:
    codigo: str
    exame: str
    regras: str
    certeza: str


@dataclass(frozen=True)
class DecisaoARevisar:
    """Uma regra interpretada (ou sem status) e onde ela decide sozinha: a
    médica revisa a decisão uma vez, não a mesma regra em cada GHE."""
    regra_id: str
    status: str
    onde: tuple[str, ...]
    codigos: tuple[str, ...]


@dataclass(frozen=True)
class RegraCitada:
    regra_id: str
    status: str
    fundamento: str


@dataclass(frozen=True)
class BlocoMemorial:
    ghe_id: str
    nome_ghe: str
    linhas: tuple[LinhaMemorial, ...]
    nao_pedidos: tuple[str, ...]


@dataclass(frozen=True)
class Memorial:
    revisar_primeiro: tuple[DecisaoARevisar, ...]
    blocos: tuple[BlocoMemorial, ...]
    regras: tuple[RegraCitada, ...]


def codigo_linha(ghe_id: str, exame: str) -> str:
    """Código estável da linha: a correção da médica cita o código e volta
    apontando GHE e exame sem ambiguidade (D-ARQ-87 cl.4, fatia 3)."""
    return f"{ghe_id}/{exame}"


def _nivel(status: str | None) -> int:
    return _CERTEZA.get(status or "", 0)


def _rotulo_status(nivel: int) -> str:
    return next((s for s, n in _CERTEZA.items() if n == nivel), SEM_STATUS)


def _componentes(exame: ExameEmitido) -> list[list[Motivo]]:
    """O que decide a linha: as regras que pedem a periodicidade final e, para
    cada momento, as regras que o pedem."""
    define = [m for m in exame.motivos if m.periodicidade_meses == exame.periodicidade_meses]
    return [define] + [[m for m in exame.motivos if momento in m.momentos] for momento in exame.momentos]


def grau_de_certeza(exame: ExameEmitido) -> str:
    """O elo mais fraco do que decide a linha: em cada componente vale a regra
    mais forte que o pede; a linha fica com o pior componente. Uma regra
    INTERPRETADO que só repete o que uma VALIDADO já pede não rebaixa a linha;
    a que é a única a pedir o DEM, rebaixa."""
    niveis = [max((_nivel(m.status_regra) for m in c), default=0) for c in _componentes(exame)]
    return _rotulo_status(min(niveis))


def regras_fracas(exame: ExameEmitido) -> tuple[str, ...]:
    """As regras de um componente cujo melhor apoio é interpretado ou sem status."""
    fracas: dict[str, None] = {}
    for componente in _componentes(exame):
        if max((_nivel(m.status_regra) for m in componente), default=0) <= _CERTEZA["INTERPRETADO"]:
            fracas.update(dict.fromkeys(m.regra_id for m in componente))
    return tuple(fracas)


def _momentos(momentos: frozenset[Momento] | set[Momento]) -> str:
    return ", ".join(_ROTULO_MOMENTO[m] for m in _ORDEM_MOMENTOS if m in momentos)


def _nome_exame(slug: str, exames_vocab: dict[str, Any]) -> str:
    return str(exames_vocab.get(slug, {}).get("nome_exibicao", slug))


def _descrever_regra(motivo: Motivo, define: bool) -> str:
    pedido = f"{motivo.periodicidade_meses} meses" if motivo.periodicidade_meses is not None else "?"
    gatilho = motivo.risco_origem or f"predicado {motivo.predicado}"
    texto = f"{motivo.regra_id}: {pedido}; {_momentos(motivo.momentos)} — gatilho: {gatilho}"
    return texto + (" — define a periodicidade" if define else "")


def _por_regra(exame: ExameEmitido) -> dict[str, Motivo]:
    unicos: dict[str, Motivo] = {}
    for m in exame.motivos:
        unicos.setdefault(m.regra_id, m)
    return unicos


def _linha(ghe_id: str, exame: ExameEmitido, exames_vocab: dict[str, Any]) -> LinhaMemorial:
    disputa = len({m.periodicidade_meses for m in exame.motivos}) > 1
    regras = "\n".join(
        _descrever_regra(m, disputa and m.periodicidade_meses == exame.periodicidade_meses)
        for m in _por_regra(exame).values()
    )
    nome = _nome_exame(exame.exame, exames_vocab)
    return LinhaMemorial(
        codigo=codigo_linha(ghe_id, exame.exame),
        exame=_sanitizar(f"{nome} — {exame.periodicidade_meses} meses; {_momentos(exame.momentos)}"),
        regras=_sanitizar(regras),
        certeza=grau_de_certeza(exame),
    )


def _nao_pedido(obs: Observacao, exames_vocab: dict[str, Any]) -> str:
    exames = ", ".join(_nome_exame(slug, exames_vocab) for slug in obs.exames_dispensados)
    motivo = f"risco {obs.nivel_risco.lower()} no PGR para {obs.agente.replace('_', ' ')}"
    if obs.medicao is not None:
        motivo += f" e medição abaixo do nível de ação ({obs.medicao})"
    return _sanitizar(f"{exames} — não pedido por {obs.regra_dispensa} ({obs.regra_id}): {motivo}.")


def _decisoes_a_revisar(
    matrizes: Sequence[MatrizGHE], exames_vocab: dict[str, Any], status: dict[str, str]
) -> tuple[DecisaoARevisar, ...]:
    ghes_por_exame: dict[str, dict[str, list[str]]] = {}
    codigos: dict[str, list[str]] = {}
    for matriz in matrizes:
        for exame in matriz.linhas:
            for regra_id in regras_fracas(exame):
                ghes_por_exame.setdefault(regra_id, {}).setdefault(exame.exame, []).append(matriz.ghe_id)
                codigos.setdefault(regra_id, []).append(codigo_linha(matriz.ghe_id, exame.exame))
    return tuple(
        DecisaoARevisar(
            regra_id=regra_id,
            status=status[regra_id],
            onde=tuple(
                f"{_nome_exame(slug, exames_vocab)}: {', '.join(ghes)}" for slug, ghes in por_exame.items()
            ),
            codigos=tuple(codigos[regra_id]),
        )
        for regra_id, por_exame in ghes_por_exame.items()
    )


def montar_memorial(matrizes: Sequence[MatrizGHE], exames_vocab: dict[str, Any]) -> Memorial:
    blocos: list[BlocoMemorial] = []
    citadas: dict[str, Motivo] = {}
    for matriz in matrizes:
        ordenadas = sorted(matriz.linhas, key=lambda e: _chave_ordem_exame(e.exame, exames_vocab))
        for exame in ordenadas:
            for regra_id, motivo in _por_regra(exame).items():
                citadas.setdefault(regra_id, motivo)
        blocos.append(
            BlocoMemorial(
                ghe_id=matriz.ghe_id,
                nome_ghe=nome_ghe_exibicao(matriz.nome_ghe),
                linhas=tuple(_linha(matriz.ghe_id, e, exames_vocab) for e in ordenadas),
                nao_pedidos=tuple(_nao_pedido(o, exames_vocab) for o in matriz.observacoes),
            )
        )
    status = {r: m.status_regra or SEM_STATUS for r, m in citadas.items()}
    regras = tuple(
        RegraCitada(
            regra_id=r,
            status=status[r],
            fundamento=_sanitizar(" ".join((m.base_normativa or "").split())),
        )
        for r, m in sorted(citadas.items())
    )
    return Memorial(
        revisar_primeiro=_decisoes_a_revisar(matrizes, exames_vocab, status),
        blocos=tuple(blocos),
        regras=regras,
    )


def _tabela(documento: Any, colunas: Sequence[tuple[str, float]], linhas: Sequence[Sequence[str]]) -> None:
    tabela = documento.add_table(rows=1, cols=len(colunas))
    tabela.style = "Table Grid"
    tabela.autofit = False
    for celula, (rotulo, _) in zip(tabela.rows[0].cells, colunas):
        celula.text = rotulo
        paragrafo = celula.paragraphs[0]
        paragrafo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        paragrafo.runs[0].bold = True
        paragrafo.runs[0].font.color.rgb = _COR_TEXTO_SOBRE_DESTAQUE
        _aplicar_fundo(celula, _COR_DESTAQUE_HEX)
    for linha in linhas:
        for celula, texto in zip(tabela.add_row().cells, linha):
            celula.text = texto
            for paragrafo in celula.paragraphs:
                for run in paragrafo.runs:
                    run.font.size = Pt(8)
    # O LibreOffice lê a grade (gridCol) e o Word lê a célula: as duas levam a largura.
    for coluna, (_, largura) in zip(tabela.columns, colunas):
        coluna.width = Cm(largura)
    for linha_tabela in tabela.rows:
        for celula, (_, largura) in zip(linha_tabela.cells, colunas):
            celula.width = Cm(largura)


def renderizar_memorial_docx(memorial: Memorial, cabecalho: CabecalhoDocumento, destino: Path) -> None:
    documento = Document()
    for secao in documento.sections:
        secao.orientation = WD_ORIENT.LANDSCAPE
        secao.page_width, secao.page_height = secao.page_height, secao.page_width
        secao.top_margin = secao.bottom_margin = Cm(1.5)
        secao.left_margin = secao.right_margin = Cm(1.5)

    titulo = documento.add_paragraph()
    titulo.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = titulo.add_run("Memorial de raciocínio da matriz de exames")
    run.bold = True
    run.font.size = Pt(16)
    run.font.color.rgb = _COR_DESTAQUE
    documento.add_paragraph(f"Empresa: {cabecalho.empresa} · Obra: {cabecalho.obra} · Data: {cabecalho.data}")
    documento.add_paragraph(
        "Anexo de conferência, não assinado. Para cada exame da matriz: as regras que o pediram, o que "
        "cada uma pediu e o grau de certeza (VALIDADO, DERIVADO, INTERPRETADO). Quando mais de uma regra "
        "pede o mesmo exame, vale a menor periodicidade e a soma dos momentos. O fundamento de cada regra "
        "está no apêndice. Para corrigir, escreva na coluna Correção ou cite o código da linha."
    )

    documento.add_heading("1. Revisar primeiro — decisões interpretadas ou sem status", level=1)
    if memorial.revisar_primeiro:
        fundamento = {r.regra_id: r.fundamento for r in memorial.regras}
        _tabela(
            documento,
            _COLUNAS_REVISAR,
            [
                (f"{d.regra_id}\n{d.status}", "\n".join(d.onde), fundamento[d.regra_id], "")
                for d in memorial.revisar_primeiro
            ],
        )
    else:
        documento.add_paragraph("Nenhuma linha depende só de regra interpretada.")

    documento.add_heading("2. Matriz completa, por GHE", level=1)
    for bloco in memorial.blocos:
        cabecalho_ghe = documento.add_heading(f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip(), level=2)
        if cabecalho_ghe.runs:
            cabecalho_ghe.runs[0].font.color.rgb = _COR_DESTAQUE
        _tabela(
            documento,
            _COLUNAS_GHE,
            [(l.codigo, l.exame, l.regras, l.certeza, "") for l in bloco.linhas],
        )
        for texto in bloco.nao_pedidos:
            documento.add_paragraph(texto, style="List Bullet")

    documento.add_heading("Apêndice — regras citadas e fundamento", level=1)
    _tabela(documento, _COLUNAS_REGRAS, [(r.regra_id, r.status, r.fundamento) for r in memorial.regras])
    documento.save(str(destino))
