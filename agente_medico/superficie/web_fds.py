"""Página web de revisão-RT do verbatim da FDS (D-ARQ-54 fatia 4).

Adaptador irmão de cli_fds.py sobre o MESMO contrato ida/volta de
motor/revisao_verbatim.py: o núcleo (montar_volta_verbatim) é apresentação-
-pura e não importa streamlit; a casca (pagina_fds) é o shell Streamlit que
coleta a revisão bloco a bloco / membro a membro via widgets em vez de
prompts de terminal. Lógica-de-domínio ZERO — a superfície consome o
artefato, não o reconstrói. gate_forma NÃO entra aqui — segue exclusivo de
montar_fds_revisado por decisão selada (mesma nota de cli_fds.py).
"""

from __future__ import annotations

from typing import Any

from agente_medico.motor.revisao_verbatim import desserializar_verbatim
from agente_medico.superficie.apresentacao import ArtefatoIdaIlegivel, emitir_volta

_CAMPOS_ENVELOPE = frozenset({"versao", "blocos"})

__all__ = ["ArtefatoIdaIlegivel", "montar_volta_verbatim", "pagina_fds"]


def montar_volta_verbatim(dados: dict[str, Any], blocos_revisados: list[dict[str, Any]]) -> str:
    """Recebe os dados já carregados do artefato-ida e a lista de blocos já
    revisados (mesma forma de bloco do artefato-ida: faixa + membros), e
    devolve o artefato-volta. Self-check final reutiliza
    desserializar_verbatim (anti-erro-silencioso D-ARQ-22)."""
    dados["blocos"] = blocos_revisados
    return emitir_volta(dados, desserializar_verbatim)


def pagina_fds() -> None:
    import streamlit as st

    from agente_medico.superficie.apresentacao import ArtefatoIdaIlegivel, carregar_artefato_ida
    from agente_medico.superficie.web_fds import _CAMPOS_ENVELOPE, montar_volta_verbatim

    st.title("Revisão-RT do verbatim da FDS")

    texto_ida = st.text_area("Artefato-ida (JSON)", height=200)
    if not texto_ida:
        return

    try:
        dados = carregar_artefato_ida(texto_ida, _CAMPOS_ENVELOPE)
    except ArtefatoIdaIlegivel as erro:
        st.error(str(erro))
        return

    blocos_revisados = []
    for i, bloco in enumerate(dados["blocos"], start=1):
        st.subheader(f"Bloco {i}")
        faixa = st.text_input(f"Faixa (bloco {i})", value=bloco["faixa"], key=f"faixa_{i}")

        membros_revisados = []
        for j, membro in enumerate(bloco["membros"], start=1):
            frases_h = " ".join(membro["frases_h"]) or "—"
            st.write(f"{j}. {membro['cas']} | {membro['nome']} | H: {frases_h}")
            acao = st.radio(
                f"Membro {j} (bloco {i})",
                options=("mantém", "edita", "remove"),
                index=0,
                key=f"acao_{i}_{j}",
            )
            if acao == "remove":
                continue
            if acao == "edita":
                cas = st.text_input(
                    f"CAS (bloco {i}, membro {j})", value=membro["cas"], key=f"cas_{i}_{j}"
                )
                nome = st.text_input(
                    f"Nome (bloco {i}, membro {j})", value=membro["nome"], key=f"nome_{i}_{j}"
                )
                frases_h_texto = st.text_input(
                    f"Frases-H (bloco {i}, membro {j})",
                    value=" ".join(membro["frases_h"]),
                    key=f"frases_h_{i}_{j}",
                )
                membros_revisados.append(
                    {"cas": cas, "nome": nome, "frases_h": frases_h_texto.split()}
                )
            else:
                membros_revisados.append(
                    {"cas": membro["cas"], "nome": membro["nome"], "frases_h": membro["frases_h"]}
                )

        blocos_revisados.append({"faixa": faixa, "membros": membros_revisados})

    if st.button("Emitir artefato-volta"):
        volta = montar_volta_verbatim(dados, blocos_revisados)
        st.code(volta, language="json")
        st.download_button("Baixar artefato-volta", volta, file_name="fds_volta.json")


if __name__ == "__main__":
    pagina_fds()
