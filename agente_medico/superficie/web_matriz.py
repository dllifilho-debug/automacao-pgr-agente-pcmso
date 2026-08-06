"""Página web da matriz — rota determinística, S3 fatia 1 (003.EQ + emendas).

Mesma topologia de web_envelope.py: núcleo puro que não importa streamlit +
casca pagina_matriz() que importa streamlit dentro da função. O núcleo
carrega o trabalho (D-ARQ-54 P1, molde web_envelope.py).

executar_rota_determinista_cacheada separa o CARO (processar_arquivo_pgr —
parse do PDF, minutos) do BARATO (gerar_documento — montagem/render sobre
matrizes já calculadas, milissegundos): deve_reprocessar decide, por uma
chave que deriva do CONTEÚDO do PDF + do envelope (nunca de cabeçalho/
rodapé — apresentação não é identidade do parse, D-ARQ-22: trocar só o
cabeçalho não pode mascarar reuso de matriz de outro PDF, nem forçar reparse
por um campo cosmético), se o cache pode ser reaproveitado. A casca guarda
o CacheMatrizes em st.session_state e chama a rota cacheada a cada rerun —
inclusive o rerun disparado por clique em st.download_button (comportamento
padrão do Streamlit, on_click="rerun") — sem nunca reprocessar o PDF fora
de uma mudança real de conteúdo/envelope. Lógica de domínio zero na casca.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Sequence

from agente_medico.adaptadores.orquestracao_pgr import processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import EnvelopeConfirmado, MatrizGHE, Pendencia
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    DocumentoMatriz,
    RodapeDocumento,
    montar_documento,
    renderizar_html,
)

__all__ = [
    "CacheMatrizes",
    "calcular_chave_cache",
    "deve_reprocessar",
    "executar_rota_determinista",
    "executar_rota_determinista_cacheada",
    "gerar_documento",
    "montar_envelope",
    "pagina_matriz",
]


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


def _rodar_parse_deterministico(
    caminho_pdf: Path, envelope: EnvelopeConfirmado
) -> tuple[
    tuple[MatrizGHE, ...] | None,
    dict[str, Any],
    tuple[Pendencia, ...],
    str | None,
    tuple[Pendencia, ...],
]:
    """Devolve, além de matrizes/exames_vocab/pendencias (extração+hidratação),
    resultado.status e resultado.pendencias_globais — sem esses dois campos a
    casca não consegue distinguir um gate eliminatório (R-PGR-01/R-PGR-06,
    Resultado(status="REJEITADO", matrizes=[])) de um parse legitimamente
    vazio (achado 003.EQ emenda 3: `matrizes=[]` não é None, então esse ramo
    passava reto pelo guard `doc is None`)."""
    protocolo = carregar(Path(__file__).resolve().parent.parent / "protocolo")
    resultado, pendencias = processar_arquivo_pgr(
        caminho_pdf,
        protocolo,
        TranscritorGHEOffline(),
        TranscritorCardOffline(),
        envelope,
    )
    matrizes = tuple(resultado.matrizes) if resultado is not None else None
    status = resultado.status if resultado is not None else None
    pendencias_globais = tuple(resultado.pendencias_globais) if resultado is not None else ()
    return matrizes, protocolo.vocabulario.exames, pendencias, status, pendencias_globais


def executar_rota_determinista(
    caminho_pdf: Path,
    envelope: EnvelopeConfirmado,
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
) -> tuple[DocumentoMatriz | None, str | None, tuple[Pendencia, ...]]:
    """Carrega o protocolo, roda processar_arquivo_pgr pela rota
    determinística (clientes-bomba offline, cliente LLM nunca invocado) e,
    com Resultado não-None, gera o documento. Parse total falho devolve
    (None, None, pendencias) — nunca inventa matriz (D-ARQ-22). Primitiva
    sem cache — executar_rota_determinista_cacheada é a versão que a casca
    usa de fato."""
    matrizes, exames_vocab, pendencias, _status, _pendencias_globais = _rodar_parse_deterministico(
        caminho_pdf, envelope
    )
    if matrizes is None:
        return None, None, pendencias
    doc, html = gerar_documento(matrizes, exames_vocab, cabecalho, rodape)
    return doc, html, pendencias


@dataclass(frozen=True)
class CacheMatrizes:
    """Resultado cacheado da parte CARA (processar_arquivo_pgr) da rota
    determinística. `chave` vem de calcular_chave_cache — PDF + envelope,
    nunca cabeçalho/rodapé. `status`/`pendencias_globais` espelham
    Resultado — a casca usa `status == "REJEITADO"` para parar duro
    (003.EQ emenda 3, elo A)."""

    chave: str
    matrizes: tuple[MatrizGHE, ...] | None
    exames_vocab: dict[str, Any]
    pendencias: tuple[Pendencia, ...]
    status: str | None
    pendencias_globais: tuple[Pendencia, ...]


def calcular_chave_cache(conteudo_pdf: bytes, envelope: EnvelopeConfirmado) -> str:
    """Chave de invalidação do cache: hash do CONTEÚDO do PDF (bytes reais,
    não o nome do arquivo) + envelope. Cabeçalho/rodapé nunca entram — são
    apresentação, não identidade do parse (ver docstring do módulo)."""
    digest = hashlib.sha256(conteudo_pdf).hexdigest()
    return f"{digest}:{envelope.validade.isoformat()}:{envelope.assinatura_engenheiro}"


def deve_reprocessar(chave_atual: str, chave_em_cache: str | None) -> bool:
    """True quando o cache (se existir) não corresponde ao PDF/envelope
    atuais — processar_arquivo_pgr (caro) precisa rodar de novo. False
    reaproveita o cache (mesmo PDF, mesmo envelope)."""
    return chave_atual != chave_em_cache


def executar_rota_determinista_cacheada(
    caminho_pdf: Path,
    conteudo_pdf: bytes,
    envelope: EnvelopeConfirmado,
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
    cache: CacheMatrizes | None,
) -> tuple[DocumentoMatriz | None, str | None, tuple[Pendencia, ...], CacheMatrizes]:
    """Cacheia o CARO (processar_arquivo_pgr, via deve_reprocessar sobre a
    chave de calcular_chave_cache), regenera o BARATO (gerar_documento)
    incondicionalmente — mesmo no cache-hit, cabeçalho/rodapé ATUAIS valem,
    nunca os do momento em que o cache foi gravado. Devolve sempre o
    CacheMatrizes vigente (novo, no miss; o mesmo, no hit) para a casca
    persistir em st.session_state."""
    chave_atual = calcular_chave_cache(conteudo_pdf, envelope)
    if cache is None or deve_reprocessar(chave_atual, cache.chave):
        matrizes, exames_vocab, pendencias, status, pendencias_globais = _rodar_parse_deterministico(
            caminho_pdf, envelope
        )
        cache = CacheMatrizes(
            chave=chave_atual,
            matrizes=matrizes,
            exames_vocab=exames_vocab,
            pendencias=pendencias,
            status=status,
            pendencias_globais=pendencias_globais,
        )

    if cache.matrizes is None:
        return None, None, cache.pendencias, cache
    doc, html = gerar_documento(cache.matrizes, cache.exames_vocab, cabecalho, rodape)
    return doc, html, cache.pendencias, cache


def pagina_matriz() -> None:
    import tempfile
    from pathlib import Path

    import streamlit as st

    from agente_medico.superficie.documento_matriz import (
        CabecalhoDocumento,
        RodapeDocumento,
        renderizar_docx,
    )
    from agente_medico.superficie.web_matriz import (
        executar_rota_determinista_cacheada,
        montar_envelope,
    )

    st.title("Matriz de exames — rota determinística")

    arquivo = st.file_uploader("PDF do PGR", type="pdf")
    if arquivo is None:
        st.session_state.pop("web_matriz_cache", None)
        return

    conteudo_pdf = arquivo.getvalue()

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

    cache = st.session_state.get("web_matriz_cache")
    if not enviado and cache is None:
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
        caminho_pdf.write_bytes(conteudo_pdf)

        with st.spinner("Processando PGR — o parse do PDF pode levar alguns minutos..."):
            doc, html, pendencias, cache = executar_rota_determinista_cacheada(
                caminho_pdf, conteudo_pdf, envelope, cabecalho, rodape, cache
            )

        # Elo A (003.EQ emenda 3): gate eliminatório (R-PGR-01/R-PGR-06) é
        # parada dura — Resultado(status="REJEITADO", matrizes=[]) tem
        # matrizes=() != None, então o guard `doc is None` mais abaixo NUNCA
        # pegava esse ramo; documento vazio assinável saía com os dois
        # downloads. Checa ANTES de gerar docx/gravar cache.
        if cache.status == "REJEITADO":
            st.error("PGR rejeitado — pendências bloqueantes impedem a emissão da matriz:")
            for p in cache.pendencias_globais:
                if p.bloqueante:
                    st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")
            # Elo D: nunca grava cache de um estado REJEITADO — a chave não
            # pode mascarar a rejeição num rerun (ex.: clique de download de
            # uma submissão anterior bem-sucedida ainda em session_state).
            st.session_state.pop("web_matriz_cache", None)
            return

        docx_bytes = None
        if doc is not None:
            destino_docx = Path(tmp) / "matriz.docx"
            renderizar_docx(doc, destino_docx)
            docx_bytes = destino_docx.read_bytes()

    st.session_state["web_matriz_cache"] = cache

    if doc is None or html is None:
        st.error("Parse total falho — nenhuma matriz gerada (D-ARQ-22).")
        for p in pendencias:
            st.write(f"- `{p.tipo}`: {p.motivo}")
        return

    # Elo B: pendências GLOBAIS (D-ARQ-08, prioridade visual) sempre entram
    # na tela, em bloco próprio, ANTES das pendências de extração/hidratação
    # — senão as centenas de vocabulario_ausente afogam a única que importa.
    if cache.pendencias_globais:
        st.subheader("Pendências globais")
        for p in cache.pendencias_globais:
            st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")

    if pendencias:
        st.subheader("Pendências")
        for p in pendencias:
            st.write(f"- `{p.tipo}`: {p.motivo}")

    # Elo C: guarda anti-documento-vazio, independente do gate — documento
    # assinável sem nenhuma linha de cargo (nenhum exame emitido) não sai da
    # máquina em hipótese nenhuma (D-ARQ-22).
    total_linhas_cargo = sum(len(bloco.linhas) for bloco in doc.blocos)
    if total_linhas_cargo == 0:
        st.error(
            "Documento sem nenhuma linha de cargo — nenhum exame emitido. "
            "Nenhum download oferecido (D-ARQ-22)."
        )
        return

    for bloco in doc.blocos:
        st.subheader(f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip())
        for linha in bloco.linhas:
            st.write(f"**{linha.cargo}**: {', '.join(linha.celulas)}")

    st.download_button("Baixar HTML", html, file_name="matriz.html", mime="text/html")
    if docx_bytes is not None:
        st.download_button(
            "Baixar DOCX",
            docx_bytes,
            file_name="matriz.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    pagina_matriz()
