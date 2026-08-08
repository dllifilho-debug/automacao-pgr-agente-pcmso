"""Testes de agente_medico/superficie/autorizacao.py (003.ES fatia 2) — cada
teste carrega, junto, a reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

from agente_medico.superficie.autorizacao import (
    GateAcesso,
    decidir_acesso,
    esta_autorizado,
)


def test_allowlist_vazia_nega_qualquer_email() -> None:
    assert esta_autorizado("quem@quer.com", frozenset()) is False


def test_email_fora_da_allowlist_e_negado() -> None:
    assert esta_autorizado("fora@empresa.com", frozenset({"dentro@empresa.com"})) is False


def test_email_autorizado_ignora_caixa_e_espaco() -> None:
    assert esta_autorizado("  Fulano@Empresa.COM ", frozenset({"fulano@empresa.com"})) is True


def test_email_ausente_e_negado() -> None:
    allowlist = frozenset({"alguem@empresa.com"})
    assert esta_autorizado(None, allowlist) is False
    assert esta_autorizado("", allowlist) is False


def test_nao_logado_pede_login() -> None:
    allowlist = frozenset({"fulano@empresa.com"})
    assert decidir_acesso(False, "fulano@empresa.com", allowlist) is GateAcesso.PEDIR_LOGIN


def test_logado_fora_da_allowlist_e_negado() -> None:
    allowlist = frozenset({"fulano@empresa.com"})
    assert decidir_acesso(True, "estranho@empresa.com", allowlist) is GateAcesso.NEGAR


def test_logado_e_autorizado_libera() -> None:
    allowlist = frozenset({"fulano@empresa.com"})
    assert decidir_acesso(True, "fulano@empresa.com", allowlist) is GateAcesso.LIBERAR
