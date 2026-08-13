"""Guarda o fixture autouse de conftest.py (003.EW): nenhum teste pode ver a
CHAVE_API_GOOGLE, mesmo quando ela existe na máquina do operador via
.streamlit/secrets.toml ou variável de ambiente."""

from __future__ import annotations


def test_suite_nao_enxerga_chave_de_api() -> None:
    import os

    import streamlit as st

    assert not os.environ.get("CHAVE_API_GOOGLE")
    assert not dict(st.secrets).get("CHAVE_API_GOOGLE")
