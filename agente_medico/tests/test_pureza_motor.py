from __future__ import annotations

import ast
from pathlib import Path

# [DERIVADO — D-ARQ-09/D-ARQ-48] Materializa em teste a invariante "motor é
# puro, LLM fica fora do caminho crítico": nenhum módulo de agente_medico/motor
# importa requests/streamlit/google.generativeai (a camada-LLM entra só via
# TranscritorLLM injetado, motor/transcritor_fds.py), nem lê os.environ
# diretamente (leitura de chave é do adaptador, D-ARQ-47/48).

_MOTOR_DIR = Path(__file__).parent.parent / "motor"

_MODULOS_PROIBIDOS = {"requests", "streamlit", "google.generativeai", "genai"}


def _nomes_importados(caminho: Path) -> set[str]:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    nomes: set[str] = set()
    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            nomes.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            nomes.add(node.module)
    return nomes


def _le_os_environ(caminho: Path) -> bool:
    arvore = ast.parse(caminho.read_text(encoding="utf-8"), filename=str(caminho))
    for node in ast.walk(arvore):
        if (
            isinstance(node, ast.Attribute)
            and node.attr == "environ"
            and isinstance(node.value, ast.Name)
            and node.value.id == "os"
        ):
            return True
    return False


def test_motor_nao_importa_camada_llm() -> None:
    arquivos = sorted(_MOTOR_DIR.rglob("*.py"))
    assert arquivos, "motor/ vazio — teste de pureza sem alvo"
    for caminho in arquivos:
        nomes = _nomes_importados(caminho)
        proibidos = {
            n for n in nomes if n in _MODULOS_PROIBIDOS or n.split(".")[0] in _MODULOS_PROIBIDOS
        }
        assert not proibidos, f"{caminho.name} importa módulo proibido no motor: {proibidos}"


def test_motor_nao_le_os_environ() -> None:
    arquivos = sorted(_MOTOR_DIR.rglob("*.py"))
    for caminho in arquivos:
        assert not _le_os_environ(caminho), f"{caminho.name} lê os.environ dentro do motor"
