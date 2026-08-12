"""Entrypoint de DESENVOLVIMENTO — roda o app sem gate de acesso.

Existe para `streamlit run app_matriz_local.py` funcionar na máquina do
operador sem o bloco `[auth]` (OAuth do Google), que o entrypoint de produção
exige por D-ARQ-76. NUNCA é o entrypoint publicado: o container roda
`app_matriz.py`, e `tests/test_deploy_artefatos.py` trava isso.
"""

import streamlit as st

from agente_medico.superficie.web_matriz import pagina_matriz

st.set_page_config(
    page_title="Matriz de Exames — PCMSO",
    page_icon="🩺",
    layout="wide",
)

pagina_matriz()
