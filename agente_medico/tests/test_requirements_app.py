"""Testes de requirements-app.txt (003.ES) — cada teste carrega, junto, a
reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

MAPA_IMPORT_PARA_DISTRIBUICAO: dict[str, str] = {
    "docx": "python-docx",
    "pdfplumber": "pdfplumber",
    "requests": "requests",
    "streamlit": "streamlit",
    "yaml": "PyYAML",
}

DIRETORIOS_VARRIDOS: list[str] = [
    "agente_medico/motor",
    "agente_medico/superficie",
    "agente_medico/adaptadores",
]


def _normalizar(nome: str) -> str:
    return re.sub(r"[-_.]+", "-", nome).lower()


def _terceiros_importados() -> set[str]:
    raiz = Path(__file__).resolve().parents[2]
    stdlib = sys.stdlib_module_names
    terceiros: set[str] = set()
    for diretorio in DIRETORIOS_VARRIDOS:
        for arquivo in (raiz / diretorio).glob("**/*.py"):
            arvore = ast.parse(arquivo.read_text(encoding="utf-8"))
            for no in ast.walk(arvore):
                modulo: str | None = None
                if isinstance(no, ast.Import):
                    for alias in no.names:
                        modulo = alias.name.split(".")[0]
                        if (
                            modulo not in stdlib
                            and modulo != "agente_medico"
                            and modulo != "__future__"
                        ):
                            terceiros.add(modulo)
                elif isinstance(no, ast.ImportFrom):
                    if no.level == 0 and no.module:
                        modulo = no.module.split(".")[0]
                        if (
                            modulo not in stdlib
                            and modulo != "agente_medico"
                            and modulo != "__future__"
                        ):
                            terceiros.add(modulo)
    return terceiros


def _distribuicoes_declaradas() -> dict[str, str]:
    caminho = Path(__file__).resolve().parents[2] / "requirements-app.txt"
    declaradas: dict[str, str] = {}
    for linha in caminho.read_text(encoding="utf-8").splitlines():
        linha = linha.strip()
        if not linha or linha.startswith("#"):
            continue
        linha = linha.split("#", 1)[0].strip()
        corte = len(linha)
        for separador in (">=", "==", "<", "~", "!", "["):
            posicao = linha.find(separador)
            if posicao != -1:
                corte = min(corte, posicao)
        posicao_espaco = linha.find(" ")
        if posicao_espaco != -1:
            corte = min(corte, posicao_espaco)
        nome = linha[:corte].strip()
        if nome:
            declaradas[_normalizar(nome)] = linha
    return declaradas


def test_todo_terceiro_importado_esta_declarado() -> None:
    terceiros = _terceiros_importados()
    sem_mapa = terceiros - set(MAPA_IMPORT_PARA_DISTRIBUICAO)
    assert not sem_mapa, f"terceiro novo sem entrada no mapa: {sem_mapa}"

    declaradas = _distribuicoes_declaradas()
    for modulo in terceiros:
        distribuicao = MAPA_IMPORT_PARA_DISTRIBUICAO[modulo]
        assert _normalizar(distribuicao) in declaradas, (
            f"import {modulo!r} (distribuição {distribuicao!r}) não declarado "
            f"em requirements-app.txt"
        )


def test_nada_declarado_a_mais_do_que_o_importado() -> None:
    terceiros = _terceiros_importados()
    distribuicoes_esperadas = {
        _normalizar(MAPA_IMPORT_PARA_DISTRIBUICAO[modulo]) for modulo in terceiros
    }
    declaradas = _distribuicoes_declaradas()
    a_mais = set(declaradas) - distribuicoes_esperadas
    assert not a_mais, f"declarado em requirements-app.txt mas não importado: {a_mais}"


def test_piso_de_streamlit_garante_st_login() -> None:
    declaradas = _distribuicoes_declaradas()
    linha = declaradas[_normalizar("streamlit")]
    trecho = linha.split(">=", 1)[1].split(",", 1)[0].strip()
    piso = tuple(int(parte) for parte in trecho.split("."))
    assert piso == (1, 42, 0), f"piso de streamlit é {piso}, esperado (1, 42, 0)"


def test_piso_de_pdfplumber_garante_close_e_flush_cache() -> None:
    declaradas = _distribuicoes_declaradas()
    linha = declaradas[_normalizar("pdfplumber")]
    trecho = linha.split(">=", 1)[1].split(",", 1)[0].strip()
    piso = tuple(int(parte) for parte in trecho.split("."))
    assert piso == (0, 11, 9), f"piso de pdfplumber é {piso}, esperado (0, 11, 9)"
