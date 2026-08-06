"""Entrypoint do app da matriz — alvo de `streamlit run app_matriz.py`.

Existe para que a resolução de `agente_medico.*` não dependa da forma de
invocação: `streamlit run` insere no sys.path o diretório DO SCRIPT, e o
módulo real vive em agente_medico/superficie/. Com o entrypoint na raiz,
é a raiz que entra no path — sem depender do cwd nem de `python -m`.

Sem guarda `if __name__ == "__main__"` de propósito: o Streamlit executa o
script, e a chamada de topo é o que o AppTest do teste exercita.
"""

from agente_medico.superficie.web_matriz import pagina_matriz

pagina_matriz()
