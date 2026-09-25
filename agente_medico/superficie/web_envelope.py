"""Página web de confirmação-RT do envelope do topo (D-ARQ-54 fatia 4).

Adaptador irmão de cli_envelope.py sobre o MESMO contrato ida/volta de
motor/revisao_envelope.py: o núcleo (montar_volta_envelope) é apresentação-
-pura e não importa streamlit; a casca (pagina_envelope) é o shell Streamlit
que coleta validade + assinatura_engenheiro via widgets em vez de prompts de
terminal. Lógica-de-domínio ZERO — a superfície consome o artefato, não o
reconstrói.
"""

from __future__ import annotations

from datetime import date
from typing import Any

from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.superficie.apresentacao import (
    ArtefatoIdaIlegivel,
    emitir_volta,
    validar_data_emissao,
)

_CAMPOS_RENDERIZACAO = frozenset({"candidatas", "proposta", "credencial", "confirmacao"})

__all__ = ["ArtefatoIdaIlegivel", "montar_volta_envelope", "pagina_envelope"]


def montar_volta_envelope(
    dados: dict[str, Any], validade: str, assinatura: bool, hoje: date | None = None
) -> str:
    """Recebe os dados já carregados do artefato-ida, a validade escolhida
    (data de EMISSÃO do PGR, ISO AAAA-MM-DD) e a assinatura do RT, e devolve o
    artefato-volta. Levanta ValueError se `validade` não for uma data ISO
    válida e EmissaoFuturaError se for posterior a hoje (R-PGR-06 —
    validar_data_emissao) — mesmo espelho de mensagem que o prompt da CLI.
    Self-check final reutiliza desserializar_confirmacao (anti-erro-silencioso
    D-ARQ-22)."""
    validar_data_emissao(validade, hoje)

    dados["confirmacao"]["validade"] = validade
    dados["confirmacao"]["assinatura_engenheiro"] = assinatura

    return emitir_volta(dados, desserializar_confirmacao)


def pagina_envelope() -> None:
    import streamlit as st

    from agente_medico.superficie.apresentacao import (
        MENSAGEM_EMISSAO_FUTURA,
        ArtefatoIdaIlegivel,
        EmissaoFuturaError,
        carregar_artefato_ida,
        validar_data_emissao,
    )
    from agente_medico.superficie.web_envelope import _CAMPOS_RENDERIZACAO, montar_volta_envelope

    st.title("Confirmação-RT do envelope do topo")

    texto_ida = st.text_area("Artefato-ida (JSON)", height=200)
    if not texto_ida:
        return

    try:
        dados = carregar_artefato_ida(texto_ida, _CAMPOS_RENDERIZACAO)
    except ArtefatoIdaIlegivel as erro:
        st.error(str(erro))
        return

    credencial = dados["credencial"]
    st.subheader("Credencial")
    st.write(f"Responsável técnico: {credencial['responsavel_tecnico']}")
    st.write(f"Título RT: {credencial['titulo_rt']}")
    st.write(f"Registro profissional: {credencial['registro_profissional']}")

    st.subheader("Candidatas de data de emissão (capa do PGR)")
    for i, candidata in enumerate(dados["candidatas"], start=1):
        data_texto = candidata["data"] if candidata["data"] is not None else "(não-parseável)"
        st.write(f"{i}. {candidata['texto']} -> {data_texto}")

    proposta = dados["proposta"]
    proposta_texto = proposta if proposta is not None else "(nenhuma)"
    st.write(f"Proposta: {proposta_texto}")

    validade = st.text_input(
        "Data de emissão do PGR (AAAA-MM-DD)", value=(proposta if proposta is not None else "")
    )
    assinatura_escolha = st.radio(
        "Assinatura do engenheiro confirmada?", options=("s", "n"), index=None
    )

    if st.button("Emitir artefato-volta"):
        if assinatura_escolha is None:
            st.error("Escolha 's' ou 'n' para a assinatura do engenheiro.")
            return
        try:
            validar_data_emissao(validade)
        except EmissaoFuturaError:
            st.error(MENSAGEM_EMISSAO_FUTURA.format(validade))
            return
        except ValueError:
            st.error(f"Data inválida: {validade!r}. Use o formato ISO (AAAA-MM-DD).")
            return

        volta = montar_volta_envelope(dados, validade, assinatura_escolha == "s")

        st.code(volta, language="json")
        st.download_button("Baixar artefato-volta", volta, file_name="envelope_volta.json")


if __name__ == "__main__":
    pagina_envelope()
