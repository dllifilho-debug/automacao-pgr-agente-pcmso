"""Teste do entrypoint app_matriz.py (003.ES) — carrega, junto, a reversão
de código que deve deixá-lo vermelho."""

from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_entrypoint_carrega_a_pagina_sem_excecao() -> None:
    caminho = str(Path(__file__).resolve().parents[2] / "app_matriz.py")
    at = AppTest.from_file(caminho, default_timeout=30)
    at.run()
    assert not at.exception, f"exceções: {at.exception}"
    assert at.title[0].value == "Matriz de exames — rota determinística"
