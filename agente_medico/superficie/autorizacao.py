"""Decisão de autorização do gate de acesso (D-ARQ-75 cláusula 2a) — puro,
sem streamlit, sem os.environ, sem I/O. A doc oficial de `st.user` é
explícita: "OIDC supports authentication, but not authorization" — login
OIDC prova quem a pessoa é, não que ela pode usar este aplicativo. Com um
client OAuth próprio, qualquer conta Google do mundo completa o login; a
allowlist é o gate real, e mora aqui porque é a única parte da lógica que o
harness de teste alcança sem subir um servidor Streamlit.
"""

from __future__ import annotations

from enum import Enum


class GateAcesso(Enum):
    PEDIR_LOGIN = "pedir_login"
    NEGAR = "negar"
    LIBERAR = "liberar"


def carregar_allowlist(bruto: str | None) -> frozenset[str]:
    if not bruto:
        return frozenset()
    return frozenset(
        normalizado
        for entrada in bruto.split(",")
        if (normalizado := entrada.strip().lower())
    )


def esta_autorizado(email: str | None, allowlist: frozenset[str]) -> bool:
    if not allowlist:
        return False
    if email is None or not email.strip():
        return False
    return email.strip().lower() in allowlist


def decidir_acesso(esta_logado: bool, email: str | None, allowlist: frozenset[str]) -> GateAcesso:
    if not esta_logado:
        return GateAcesso.PEDIR_LOGIN
    if not esta_autorizado(email, allowlist):
        return GateAcesso.NEGAR
    return GateAcesso.LIBERAR
