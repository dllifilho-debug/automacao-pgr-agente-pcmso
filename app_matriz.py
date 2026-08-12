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

`st.user` devolve `str | bool | TokensProxy | None` para qualquer atributo
(streamlit 1.56.0, `user_info.py`) — sem tipo próprio para `is_logged_in`
nem `.get("email")`. A normalização estrita para `bool`/`str | None`
acontece aqui, na fronteira de I/O, antes do núcleo puro de autorizacao.py.

Sem o bloco `[auth]` em secrets, `st.user.is_logged_in` nem existe — o ramo
`_identidade_do_provedor() is None` distingue esse caso ("mal configurado")
de "configurado mas não logado", e para com mensagem em vez de estourar.
"""

import os

import streamlit as st

from agente_medico.superficie.autorizacao import (
    GateAcesso,
    carregar_allowlist,
    decidir_acesso,
)
from agente_medico.superficie.web_matriz import pagina_matriz

st.set_page_config(
    page_title="Matriz de Exames — PCMSO",
    page_icon="🩺",
    layout="wide",
)


def _identidade_do_provedor() -> tuple[bool, str | None] | None:
    """None = provedor de identidade não configurado (bloco `[auth]` ausente).

    `st.user.is_logged_in` não existe sem `[auth]` (medição 1 de D-ARQ-76); sem
    este ramo o script estoura AttributeError, e o Community Cloud força
    showErrorDetails=false — erro em produção sem causa visível.
    """
    try:
        logado = st.user.is_logged_in is True
        email_bruto = st.user.get("email")
    except AttributeError:
        return None
    return logado, email_bruto if isinstance(email_bruto, str) else None


_identidade = _identidade_do_provedor()

if _identidade is None:
    st.title("Aplicativo mal configurado")
    st.write(
        "O provedor de identidade não está configurado (bloco `[auth]` ausente "
        "em secrets). O acesso está bloqueado."
    )
    st.stop()

_logado, _email = _identidade

_decisao = decidir_acesso(
    _logado,
    _email,
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
