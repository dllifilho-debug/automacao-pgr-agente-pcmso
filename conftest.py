"""Blindagem de rede da suíte (003.EW): nenhum teste pode alcançar o Gemini.

Depois que a superfície passou a injetar o transcritor real, a única coisa que
separa a suíte de uma chamada HTTP é a ausência de chave — e a chave passou a
existir em .streamlit/secrets.toml na máquina do operador. Este fixture remove
as duas fontes que _obter_chave() consulta (st.secrets e os.environ).

Opt-out explícito por marcador nomeado (`ao_vivo`), não por arquivo/módulo:
os testes que já existiam para chamar a API de verdade (`requer_api` em
test_transcritor_gemini*.py) precisam da chave real para funcionar como
desenhados — a blindagem global os quebraria (skipif avalia no collect, este
fixture agiria no setup, removendo a chave antes do corpo do teste rodar).
"""

from __future__ import annotations

import pytest


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "ao_vivo: chama API externa de verdade; isento da blindagem de rede"
    )


@pytest.fixture(autouse=True)
def _sem_chave_de_api(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    if request.node.get_closest_marker("ao_vivo"):
        return

    monkeypatch.delenv("CHAVE_API_GOOGLE", raising=False)
    import streamlit as st

    monkeypatch.setattr(st, "secrets", {}, raising=False)
