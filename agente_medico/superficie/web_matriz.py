"""Página web da matriz — rota determinística, S3 fatia 1 (003.EQ).

Mesma topologia de web_envelope.py: núcleo puro que não importa streamlit +
casca pagina_matriz() que importa streamlit dentro da função. Costura
processar_arquivo_pgr (adaptadores/orquestracao_pgr.py) até
montar_documento/renderizar_html/renderizar_docx (documento_matriz.py) —
lógica de domínio zero, a superfície não reimplementa expansão GHE→cargo
nem ordenação de exame.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Sequence

from agente_medico.motor.tipos import EnvelopeConfirmado, MatrizGHE
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    DocumentoMatriz,
    RodapeDocumento,
    montar_documento,
    renderizar_html,
)

__all__ = ["gerar_documento", "montar_envelope", "pagina_matriz"]


def montar_envelope(validade_iso: str, assinatura: bool) -> EnvelopeConfirmado:
    """Mesmo espelho de mensagem que montar_volta_envelope (web_envelope.py):
    ValueError na validade malformada, nunca coagida silenciosamente."""
    validade = date.fromisoformat(validade_iso)
    return EnvelopeConfirmado(validade=validade, assinatura_engenheiro=assinatura)


def gerar_documento(
    matrizes: Sequence[MatrizGHE],
    exames_vocab: dict[str, Any],
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
) -> tuple[DocumentoMatriz, str]:
    """Delega a montar_documento + renderizar_html — não reimplementa
    expansão GHE→cargo nem ordenação de exame."""
    doc = montar_documento(matrizes, exames_vocab, cabecalho, rodape)
    return doc, renderizar_html(doc)


def pagina_matriz() -> None:
    import tempfile
    from pathlib import Path

    import streamlit as st

    from agente_medico.adaptadores.orquestracao_pgr import processar_arquivo_pgr
    from agente_medico.adaptadores.transcritor_offline import (
        TranscritorCardOffline,
        TranscritorGHEOffline,
    )
    from agente_medico.motor.protocolo import carregar
    from agente_medico.superficie.apresentacao_matriz import renderizar_matriz
    from agente_medico.superficie.documento_matriz import renderizar_docx

    st.title("Matriz de exames — rota determinística")

    arquivo = st.file_uploader("PDF do PGR", type="pdf")
    if arquivo is None:
        return

    with st.form("cabecalho_rodape_envelope"):
        st.subheader("Cabeçalho")
        empresa = st.text_input("Empresa")
        obra = st.text_input("Obra")
        tipo_documento = st.text_input("Tipo de documento")
        data_documento = st.text_input("Data")
        medico_coordenador = st.text_input("Médico coordenador")
        crm = st.text_input("CRM")

        st.subheader("Rodapé")
        responsavel_preenchimento = st.text_input("Responsável pelo preenchimento")
        medico_validador = st.text_input("Médica validadora")
        data_pgr = st.text_input("Data do PGR")

        st.subheader("Envelope")
        validade = st.text_input("Validade do PGR (AAAA-MM-DD)")
        assinatura = st.checkbox("Assinado por engenheiro de segurança")

        enviado = st.form_submit_button("Gerar matriz")

    if not enviado:
        return

    try:
        envelope = montar_envelope(validade, assinatura)
    except ValueError:
        st.error(f"Data inválida: {validade!r}. Use o formato ISO (AAAA-MM-DD).")
        return

    cabecalho = CabecalhoDocumento(
        empresa=empresa,
        obra=obra,
        tipo_documento=tipo_documento,
        data=data_documento,
        medico_coordenador=medico_coordenador,
        crm=crm,
    )
    rodape = RodapeDocumento(
        responsavel_preenchimento=responsavel_preenchimento,
        medico_validador=medico_validador,
        data_pgr=data_pgr,
    )

    with tempfile.TemporaryDirectory() as tmp:
        caminho_pdf = Path(tmp) / arquivo.name
        caminho_pdf.write_bytes(arquivo.getvalue())

        with st.spinner("Processando PGR — o parse do PDF pode levar alguns minutos..."):
            protocolo = carregar(Path(__file__).resolve().parent.parent / "protocolo")
            resultado, pendencias = processar_arquivo_pgr(
                caminho_pdf,
                protocolo,
                TranscritorGHEOffline(),
                TranscritorCardOffline(),
                envelope,
            )

        if resultado is None:
            st.error("Parse total falho — nenhuma matriz gerada (D-ARQ-22).")
            for p in pendencias:
                st.write(f"- `{p.tipo}`: {p.motivo}")
            return

        if pendencias:
            st.subheader("Pendências")
            for p in pendencias:
                st.write(f"- `{p.tipo}`: {p.motivo}")

        for matriz in resultado.matrizes:
            st.markdown("\n".join(renderizar_matriz(matriz)))

        doc, html = gerar_documento(
            resultado.matrizes, protocolo.vocabulario.exames, cabecalho, rodape
        )

        st.download_button("Baixar HTML", html, file_name="matriz.html", mime="text/html")

        destino_docx = Path(tmp) / "matriz.docx"
        renderizar_docx(doc, destino_docx)
        st.download_button(
            "Baixar DOCX",
            destino_docx.read_bytes(),
            file_name="matriz.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    pagina_matriz()
