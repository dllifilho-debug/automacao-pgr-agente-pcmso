"""Teste do entrypoint app_matriz.py (003.ES) — carrega, junto, a reversão
de código que deve deixá-lo vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest
import streamlit
from streamlit.testing.v1 import AppTest


class _UserFalso(dict):
    @property
    def is_logged_in(self) -> bool:
        return False


class _UserLogadoNaoBooleano(dict):
    @property
    def is_logged_in(self) -> str:
        return "sim"


def test_entrypoint_sem_login_para_no_gate(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PCMSO_ALLOWLIST", raising=False)
    monkeypatch.setattr(streamlit, "user", _UserFalso())
    caminho = str(Path(__file__).resolve().parents[2] / "app_matriz.py")
    at = AppTest.from_file(caminho, default_timeout=30)
    at.run()

    assert not at.exception, f"exceções: {at.exception}"
    assert any(b.label == "Entrar com Google" for b in at.button)
    assert not any(t.value == "Matriz de exames — rota determinística" for t in at.title)


def test_is_logged_in_nao_booleano_e_tratado_como_nao_logado(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("PCMSO_ALLOWLIST", raising=False)
    monkeypatch.setattr(streamlit, "user", _UserLogadoNaoBooleano())
    caminho = str(Path(__file__).resolve().parents[2] / "app_matriz.py")
    at = AppTest.from_file(caminho, default_timeout=30)
    at.run()

    assert not at.exception, f"exceções: {at.exception}"
    assert any(b.label == "Entrar com Google" for b in at.button)
