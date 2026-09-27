"""Memorial de raciocínio da matriz (D-ARQ-87 fatia 2) — anexo para as médicas,
separado da matriz assinada: exame a exame, por que foi pedido, com que
periodicidade, com que base e com que grau de certeza, em linguagem clínica
(`resumo_clinico` de cada regra). Apresentação-pura sobre `MatrizGHE` (D-ARQ-72):
lê o que o motor grava em `Motivo` (fatia 1) e em `Observacao`, sem decisão
clínica nova. O fundamento técnico de auditoria (`base_normativa`) fica fora
do documento — está no protocolo e na revisão da tela.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Sequence

from docx import Document
from docx.enum.section import WD_ORIENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import Cm, Pt

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Motivo, Observacao
from agente_medico.superficie.documento_matriz import (
    _COR_DESTAQUE,
    _COR_DESTAQUE_HEX,
    _COR_TEXTO_SOBRE_DESTAQUE,
    CabecalhoDocumento,
    _aplicar_fundo,
    _chave_ordem_exame,
    _formatar_celula,
    _formatar_momentos,
    _sanitizar,
    nome_ghe_exibicao,
)

# Grau de certeza, do mais forte ao mais fraco (convenções de status do
# PROTOCOLO, D-ARQ-22 Parte A), com o rótulo que a médica lê.
_CERTEZA: dict[str, int] = {"VALIDADO": 3, "DERIVADO": 2, "INTERPRETADO": 1}
ROTULO_CERTEZA: dict[int, str] = {
    3: "Protocolo validado pela coordenação",
    2: "Norma ou matrizes de referência",
    1: "Interpretação do sistema — confirmar",
    0: "Sem classificação — confirmar",
}

# Página paisagem com margens de 1,5 cm: ~24,9 cm úteis por tabela.
_COLUNAS_GHE: tuple[tuple[str, float], ...] = (
    ("Exame", 5.2),
    ("Por que foi pedido", 12.4),
    ("Base", 3.8),
    ("Correção", 3.5),
)
_COLUNAS_REVISAR: tuple[tuple[str, float], ...] = (
    ("Decisão", 11.4),
    ("Onde aparece", 10.0),
    ("Correção", 3.5),
)


@dataclass(frozen=True)
class LinhaMemorial:
    codigo: str
    exame: str
    porque: str
    certeza: str


@dataclass(frozen=True)
class DecisaoARevisar:
    """Uma regra interpretada (ou sem status) e onde ela decide sozinha: a
    médica revisa a decisão uma vez, não a mesma regra em cada GHE."""
    regra_id: str
    resumo: str
    onde: tuple[str, ...]
    codigos: tuple[str, ...]


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
    contagem_certeza: tuple[tuple[str, int], ...]


def resumos_do_protocolo(regras: Sequence[Mapping[str, Any]]) -> dict[str, str]:
    return {str(r["id"]): str(r["resumo_clinico"]) for r in regras if "resumo_clinico" in r}


def _nome_exame(slug: str, exames_vocab: dict[str, Any]) -> str:
    return str(exames_vocab.get(slug, {}).get("nome_exibicao", slug))


def codigo_linha(ghe_id: str, exame: str, exames_vocab: dict[str, Any]) -> str:
    """Código da linha para a correção voltar: GHE e exame pelo nome que a
    médica vê na matriz (D-ARQ-87 cl.4, fatia 3)."""
    return f"{ghe_id} · {_nome_exame(exame, exames_vocab)}"


def _nivel(status: str | None) -> int:
    return _CERTEZA.get(status or "", 0)


def _componentes(exame: ExameEmitido) -> list[list[Motivo]]:
    """O que decide a linha: as regras que pedem a periodicidade final e, para
    cada momento, as regras que o pedem."""
    define = [m for m in exame.motivos if m.periodicidade_meses == exame.periodicidade_meses]
    return [define] + [[m for m in exame.motivos if momento in m.momentos] for momento in exame.momentos]


def nivel_de_certeza(exame: ExameEmitido) -> int:
    """O elo mais fraco do que decide a linha: em cada componente vale a regra
    mais forte que o pede; a linha fica com o pior componente. Uma regra
    INTERPRETADO que só repete o que uma VALIDADO já pede não rebaixa a linha;
    a que é a única a pedir o DEM, rebaixa."""
    return min(max((_nivel(m.status_regra) for m in c), default=0) for c in _componentes(exame))


def regras_fracas(exame: ExameEmitido) -> tuple[str, ...]:
    """As regras de um componente cujo melhor apoio é interpretado ou sem status."""
    fracas: dict[str, None] = {}
    for componente in _componentes(exame):
        if max((_nivel(m.status_regra) for m in componente), default=0) <= _CERTEZA["INTERPRETADO"]:
            fracas.update(dict.fromkeys(m.regra_id for m in componente))
    return tuple(fracas)


def _por_regra(exame: ExameEmitido) -> dict[str, Motivo]:
    unicos: dict[str, Motivo] = {}
    for m in exame.motivos:
        unicos.setdefault(m.regra_id, m)
    return unicos


def _porque(exame: ExameEmitido, resumos: Mapping[str, str]) -> str:
    regras = _por_regra(exame)
    varias = len(regras) > 1
    partes: list[str] = []
    for m in regras.values():
        texto = resumos.get(m.regra_id, "Regra sem resumo clínico — confirmar.")
        if varias and m.periodicidade_meses is not None:
            pedido = ExameEmitido(
                exame=exame.exame, periodicidade_meses=m.periodicidade_meses, momentos=set(m.momentos)
            )
            texto += f" [pede: {_formatar_momentos(pedido, True)}]"
        partes.append(f"{texto} (ref. {m.regra_id})")
    if varias and len({m.periodicidade_meses for m in regras.values()}) > 1:
        partes.append(
            f"Mais de uma regra pede este exame: vale a menor periodicidade "
            f"({exame.periodicidade_meses} meses) e a soma dos momentos."
        )
    return "\n".join(partes)


def _linha(
    ghe_id: str, exame: ExameEmitido, exames_vocab: dict[str, Any], resumos: Mapping[str, str]
) -> LinhaMemorial:
    return LinhaMemorial(
        codigo=codigo_linha(ghe_id, exame.exame, exames_vocab),
        exame=_formatar_celula(exame, exames_vocab),
        porque=_sanitizar(_porque(exame, resumos)),
        certeza=ROTULO_CERTEZA[nivel_de_certeza(exame)],
    )


def _nao_pedido(obs: Observacao, exames_vocab: dict[str, Any]) -> str:
    exames = ", ".join(_nome_exame(slug, exames_vocab) for slug in obs.exames_dispensados)
    motivo = f"{obs.agente.replace('_', ' ')} com risco {obs.nivel_risco.lower()} no PGR"
    if obs.medicao is not None:
        motivo += f" e medição abaixo do nível de ação ({obs.medicao})"
    return _sanitizar(
        f"{exames}: não pedido — {motivo}. NR-07, item 7.5.12, b: o indicador depende da "
        f"classificação do risco no PGR; fica a menção no PCMSO. (ref. {obs.regra_dispensa})"
    )


def _decisoes_a_revisar(
    matrizes: Sequence[MatrizGHE], exames_vocab: dict[str, Any], resumos: Mapping[str, str]
) -> tuple[DecisaoARevisar, ...]:
    ghes_por_exame: dict[str, dict[str, list[str]]] = {}
    codigos: dict[str, list[str]] = {}
    for matriz in matrizes:
        for exame in matriz.linhas:
            for regra_id in regras_fracas(exame):
                ghes_por_exame.setdefault(regra_id, {}).setdefault(exame.exame, []).append(matriz.ghe_id)
                codigos.setdefault(regra_id, []).append(codigo_linha(matriz.ghe_id, exame.exame, exames_vocab))
    return tuple(
        DecisaoARevisar(
            regra_id=regra_id,
            resumo=resumos.get(regra_id, "Regra sem resumo clínico — confirmar."),
            onde=tuple(
                f"{_nome_exame(slug, exames_vocab)}: {', '.join(ghes)}" for slug, ghes in por_exame.items()
            ),
            codigos=tuple(codigos[regra_id]),
        )
        for regra_id, por_exame in ghes_por_exame.items()
    )


def montar_memorial(
    matrizes: Sequence[MatrizGHE], exames_vocab: dict[str, Any], resumos: Mapping[str, str]
) -> Memorial:
    blocos: list[BlocoMemorial] = []
    niveis: Counter[int] = Counter()
    for matriz in matrizes:
        ordenadas = sorted(matriz.linhas, key=lambda e: _chave_ordem_exame(e.exame, exames_vocab))
        niveis.update(nivel_de_certeza(e) for e in ordenadas)
        blocos.append(
            BlocoMemorial(
                ghe_id=matriz.ghe_id,
                nome_ghe=nome_ghe_exibicao(matriz.nome_ghe),
                linhas=tuple(_linha(matriz.ghe_id, e, exames_vocab, resumos) for e in ordenadas),
                nao_pedidos=tuple(_nao_pedido(o, exames_vocab) for o in matriz.observacoes),
            )
        )
    return Memorial(
        revisar_primeiro=_decisoes_a_revisar(matrizes, exames_vocab, resumos),
        blocos=tuple(blocos),
        contagem_certeza=tuple((ROTULO_CERTEZA[n], niveis[n]) for n in sorted(ROTULO_CERTEZA, reverse=True) if niveis[n]),
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
                    run.font.size = Pt(9)
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
        "Anexo de conferência da matriz, não assinado. Para cada exame: por que foi pedido, com que "
        "base e com que grau de certeza. Quando mais de uma regra pede o mesmo exame, vale a menor "
        "periodicidade e a soma dos momentos. Para corrigir, escreva na coluna Correção; a correção volta "
        "para o sistema e ajusta a regra citada em \"ref.\"."
    )

    total = sum(n for _, n in memorial.contagem_certeza)
    documento.add_heading("Resumo", level=1)
    documento.add_paragraph(f"{total} exames na matriz, em {len(memorial.blocos)} GHEs. Base de cada um:")
    for rotulo, n in memorial.contagem_certeza:
        documento.add_paragraph(f"{rotulo}: {n}", style="List Bullet")
    nao_pedidos = sum(len(b.nao_pedidos) for b in memorial.blocos)
    if nao_pedidos:
        documento.add_paragraph(f"Exames dispensados pelo nível de risco do PGR: {nao_pedidos}", style="List Bullet")

    documento.add_heading("1. Confirmar primeiro — decisões sem base direta em norma ou protocolo", level=1)
    if memorial.revisar_primeiro:
        _tabela(
            documento,
            _COLUNAS_REVISAR,
            [(f"{d.resumo} (ref. {d.regra_id})", "\n".join(d.onde), "") for d in memorial.revisar_primeiro],
        )
    else:
        documento.add_paragraph("Nenhum exame depende só de interpretação do sistema.")

    documento.add_heading("2. Matriz completa, por GHE", level=1)
    for bloco in memorial.blocos:
        prefixo = "" if bloco.ghe_id.upper().startswith("GHE") else "GHE "
        cabecalho_ghe = documento.add_heading(f"{prefixo}{bloco.ghe_id} {bloco.nome_ghe}".strip(), level=2)
        if cabecalho_ghe.runs:
            cabecalho_ghe.runs[0].font.color.rgb = _COR_DESTAQUE
        _tabela(documento, _COLUNAS_GHE, [(l.exame, l.porque, l.certeza, "") for l in bloco.linhas])
        for texto in bloco.nao_pedidos:
            documento.add_paragraph(texto, style="List Bullet")
    documento.save(str(destino))
