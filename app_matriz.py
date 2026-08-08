"""Entrypoint do app da matriz — alvo de `streamlit run app_matriz.py`.

Existe para que a resolução de `agente_medico.*` não dependa da forma de
invocação: `streamlit run` insere no sys.path o diretório DO SCRIPT, e o
módulo real vive em agente_medico/superficie/. Com o entrypoint na raiz,
é a raiz que entra no path — sem depender do cwd nem de `python -m`.

Sem guarda `if __name__ == "__main__"` de propósito: o Streamlit executa o
script, e a chamada de topo é o que o AppTest do teste exercita.

Gate de acesso (D-ARQ-75 cláusula 2): login OIDC + allowlist. OIDC autentica
mas não autoriza — com client próprio, qualquer conta Google do mundo
completa o login, então a allowlist é o gate real. Roda ANTES de
pagina_matriz() porque o parse do PGR custa ~904 MB de pico (medição 003.ER)
e não pode ser disparado por não-autorizado.
"""

import os

import streamlit as st

from agente_medico.superficie.autorizacao import (
    GateAcesso,
    carregar_allowlist,
    decidir_acesso,
)
from agente_medico.superficie.web_matriz import pagina_matriz

_decisao = decidir_acesso(
    st.user.is_logged_in,
    st.user.get("email"),
    carregar_allowlist(os.environ.get("PCMSO_ALLOWLIST")),
)

if _decisao is GateAcesso.PEDIR_LOGIN:
    st.title("Acesso restrito")
    st.write("Entre com a conta autorizada para usar o aplicativo.")
    st.button("Entrar com Google", on_click=st.login)
    st.stop()

if _decisao is GateAcesso.NEGAR:
    st.error("Conta autenticada, mas sem autorização de acesso a este aplicativo.")
    st.button("Sair", on_click=st.logout)
    st.stop()

pagina_matriz()
