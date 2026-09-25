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
    caminho = Path(__file__).resolve().parents[2] / "requirements.txt"
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


def test_piso_de_streamlit_e_o_medido() -> None:
    # Reversão que mata: voltar o piso para 1.42.0 (ou qualquer valor abaixo de
    # 1.56.0) — versão em que `st.user` (gate de D-ARQ-76) ou
    # `AppTest.file_uploader` (testes de casca) não existem. Valor exato, não >=:
    # subir o piso também tem de ser medido (D-ARQ-75, nota de 25/09/2026).
    declaradas = _distribuicoes_declaradas()
    linha = declaradas[_normalizar("streamlit")]
    trecho = linha.split(">=", 1)[1].split(",", 1)[0].strip()
    piso = tuple(int(parte) for parte in trecho.split("."))
    assert piso == (1, 56, 0), f"piso de streamlit é {piso}, esperado (1, 56, 0)"


def test_piso_de_pdfplumber_garante_close_e_flush_cache() -> None:
    # Diferente do piso de streamlit (1.56.0 é a versão exata medida em que app
    # e testes de casca rodam — snapshot com significado normativo), 0.11.9 é só a versão
    # medida no host onde Page.close/Page.flush_cache foram confirmados
    # presentes (003.ET fatia 2). Não há razão para travar o piso exato:
    # >= mantém a garantia que importa (ninguém baixa o pin abaixo da versão
    # confirmada) sem quebrar se o piso subir no futuro.
    declaradas = _distribuicoes_declaradas()
    linha = declaradas[_normalizar("pdfplumber")]
    trecho = linha.split(">=", 1)[1].split(",", 1)[0].strip()
    piso = tuple(int(parte) for parte in trecho.split("."))
    assert piso >= (0, 11, 9), f"piso de pdfplumber é {piso}, esperado >= (0, 11, 9)"
