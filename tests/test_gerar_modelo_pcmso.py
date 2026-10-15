"""Testes de scripts/gerar_modelo_pcmso.py (D-ARQ-96): mecânica da troca em documento sintético e
invariantes do modelo de revisão gravado no repositório."""

from __future__ import annotations

import re
from pathlib import Path

import pytest
from docx import Document
from docx.oxml.ns import qn

from scripts.gerar_modelo_pcmso import (
    CAMPOS,
    SAIDA_REVISAO,
    ModeloInesperado,
    Troca,
    _aplicar,
    _todos_paragrafos,
)


def _doc_com_runs(tmp_path: Path, partes: list[str]) -> Path:
    doc = Document()
    paragrafo = doc.add_paragraph()
    for parte in partes:
        paragrafo.add_run(parte)
    caminho = tmp_path / "entrada.docx"
    doc.save(str(caminho))
    return caminho


def test_troca_que_atravessa_runs_preserva_as_pontas(tmp_path: Path) -> None:
    doc = Document(str(_doc_com_runs(tmp_path, ["Assumo, em nome da Empresa SPE ", "INCORPORAÇÃO H6", " LTDA o compromisso"])))
    troca = Troca("SPE INCORPORAÇÃO H6 LTDA", "{{RAZAO_SOCIAL}}", "C-01", "motivo")

    _aplicar(doc, _todos_paragrafos(doc), troca, marcar=True)

    paragrafo = doc.paragraphs[0]
    assert paragrafo.text == "Assumo, em nome da Empresa {{RAZAO_SOCIAL}} o compromisso"
    realcados = [r.text for r in paragrafo.runs if r.font.highlight_color is not None]
    assert realcados == ["{{RAZAO_SOCIAL}}"]
    assert [c.text for c in doc.comments] == ["C-01 — motivo"]


def test_contagem_diferente_da_esperada_nao_grava(tmp_path: Path) -> None:
    doc = Document(str(_doc_com_runs(tmp_path, ["(Anexo 11.1) e (Anexo 11.1)"])))
    doc.add_paragraph("(Anexo 11.1)")

    with pytest.raises(ModeloInesperado):
        _aplicar(doc, _todos_paragrafos(doc), Troca("(Anexo 11.1)", "(Anexo 16)", "C-04", "m", vezes=3), marcar=True)


def test_sugestao_so_comenta(tmp_path: Path) -> None:
    doc = Document(str(_doc_com_runs(tmp_path, ["Portanto, qualquer alteração ocorrida no PGR/PCMAT, o médico"])))

    _aplicar(doc, _todos_paragrafos(doc), Troca("PGR/PCMAT", "PGR", "S-03", "sugestão"), marcar=True)

    assert doc.paragraphs[0].text == "Portanto, qualquer alteração ocorrida no PGR/PCMAT, o médico"
    assert all(r.font.highlight_color is None for r in doc.paragraphs[0].runs)
    assert len(list(doc.comments)) == 1


def test_modo_limpo_sem_realce_nem_comentario(tmp_path: Path) -> None:
    doc = Document(str(_doc_com_runs(tmp_path, ["VI. No Exame Demissional"])))

    _aplicar(doc, _todos_paragrafos(doc), Troca("VI. No Exame", "V. No Exame", "C-07", "m"), marcar=False)

    assert doc.paragraphs[0].text == "V. No Exame Demissional"
    assert all(r.font.highlight_color is None for r in doc.paragraphs[0].runs)
    assert len(list(doc.comments)) == 0


@pytest.fixture(scope="module")
def modelo() -> tuple[str, list[str]]:
    doc = Document(str(SAIDA_REVISAO))
    textos = "\n".join(p.text for p in _todos_paragrafos(doc))
    return textos, [c.text for c in doc.comments]


@pytest.mark.parametrize(
    "resto",
    ["SPE INCORPORAÇÃO H6", "MAUÁ PARTICIPAÇÕES", "PLATEAU", "002.631.081-39", "Patrícia Montalvo",
     "Setor: GHE", 'TC "', "15337", "(Anexo 11.", "11.2 Fluxo", "9.3.4- Radiações"],
)
def test_modelo_sem_resto_do_pcmso_de_origem(modelo: tuple[str, list[str]], resto: str) -> None:
    assert resto not in modelo[0]


def test_modelo_tem_todos_os_campos(modelo: tuple[str, list[str]]) -> None:
    presentes = set(re.findall(r"\{\{([A-Z0-9_]+)\}\}", modelo[0]))
    assert presentes == set(CAMPOS)


def test_toda_correcao_amarela_tem_comentario() -> None:
    doc = Document(str(SAIDA_REVISAO))
    amarelos = sum(1 for h in doc.element.body.iter(qn("w:highlight")) if h.get(qn("w:val")) == "yellow")
    correcoes = sum(1 for c in doc.comments if c.text.startswith("C-"))
    assert amarelos == correcoes > 0
