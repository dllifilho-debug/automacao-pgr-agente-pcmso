"""Testes do núcleo puro de web_matriz.py (003.EQ S3 fatia 1) — cada teste
carrega, junto, a reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.tipos import (
    EnvelopeConfirmado,
    ExameEmitido,
    MatrizGHE,
    Momento,
    Pendencia,
    Resultado,
)
from agente_medico.superficie.documento_matriz import CabecalhoDocumento, LinhaCargo, RodapeDocumento
from agente_medico.superficie.web_matriz import (
    deve_reprocessar,
    executar_rota_determinista,
    executar_rota_determinista_cacheada,
    gerar_documento,
    montar_envelope,
    pagina_matriz,
)


def _cabecalho() -> CabecalhoDocumento:
    return CabecalhoDocumento(
        empresa="Empresa Teste",
        obra="Obra Teste",
        tipo_documento="Atualização",
        data="01/08/2026",
        medico_coordenador="Dra. Teste",
        crm="CRM-GO 0000",
    )


def _rodape() -> RodapeDocumento:
    return RodapeDocumento(
        responsavel_preenchimento="Teste",
        medico_validador="Dra. Teste",
        data_pgr="01/01/2026",
    )


def test_nucleo_web_matriz_nao_importa_streamlit() -> None:
    # Reversão que mata: inserir `import streamlit` no topo do arquivo — o
    # AST do módulo passaria a ter um Import/ImportFrom com "streamlit" fora
    # de qualquer FunctionDef.
    caminho = Path(__file__).parent.parent / "superficie" / "web_matriz.py"
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Import):
            assert not any("streamlit" in alias.name for alias in no.names)
        if isinstance(no, ast.ImportFrom):
            assert no.module is None or "streamlit" not in no.module


def test_montar_envelope_usa_a_validade_informada() -> None:
    # Reversão que mata: trocar date.fromisoformat(validade_iso) por
    # date.today() — a validade cravada (2030-01-01, bem longe de "hoje")
    # deixaria de bater.
    envelope = montar_envelope("2030-01-01", True)
    assert envelope.validade == date(2030, 1, 1)
    assert envelope.assinatura_engenheiro is True


def test_montar_envelope_recusa_validade_malformada() -> None:
    # Reversão que mata: remover a chamada date.fromisoformat (ou envolvê-la
    # num try/except que engole o erro) — a validade malformada deixaria de
    # levantar ValueError.
    with pytest.raises(ValueError):
        montar_envelope("31/12/2023", True)


def test_gerar_documento_expande_ghe_em_cargos() -> None:
    # Reversão que mata: fazer gerar_documento devolver DocumentoMatriz com
    # blocos=() — nenhum LinhaCargo por cargo, nenhum nome de cargo no HTML.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    m1 = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Carpinteiro", "Ajudante"))
    m2 = MatrizGHE(ghe_id="GHE-02", linhas=[exame], cargos=("Encarregado",))

    doc, html = gerar_documento([m1, m2], vocab, _cabecalho(), _rodape())

    assert len(doc.blocos) == 2
    assert doc.blocos[0].linhas == (
        LinhaCargo(cargo="Carpinteiro", celulas=doc.blocos[0].linhas[0].celulas),
        LinhaCargo(cargo="Ajudante", celulas=doc.blocos[0].linhas[1].celulas),
    )
    assert doc.blocos[1].linhas[0].cargo == "Encarregado"
    assert "Carpinteiro" in html
    assert "Ajudante" in html
    assert "Encarregado" in html


# ---------------------------------------------------------------------------
# Emenda 003.EQ — testes de casca (AppTest, molde test_web_envelope.py) +
# executar_rota_determinista (núcleo, extraído para engordar o núcleo e
# emagrecer a casca).
# ---------------------------------------------------------------------------


def test_executar_rota_determinista_sem_matriz_devolve_pendencias(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Reversão que mata: fazer o ramo `resultado is None` chamar
    # gerar_documento mesmo assim, em vez de devolver (None, None, pendencias)
    # direto — quebraria D-ARQ-22 (nunca inventa matriz sobre parse falho).
    pendencia = Pendencia(
        tipo="blocos_ausentes",
        destinatario="extracao",
        motivo="teste sintético",
        bloqueante=True,
        regra_origem="D-ARQ-52",
    )

    def _processar_falso(*args: Any, **kwargs: Any) -> tuple[None, tuple[Pendencia, ...]]:
        return None, (pendencia,)

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.processar_arquivo_pgr", _processar_falso
    )

    envelope = EnvelopeConfirmado(validade=date(2030, 1, 1), assinatura_engenheiro=True)
    resultado = executar_rota_determinista(
        tmp_path / "fake.pdf", envelope, _cabecalho(), _rodape()
    )

    assert resultado == (None, None, (pendencia,))


def test_pagina_matriz_validade_invalida_mostra_erro_e_nao_processa(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: remover o try/except ValueError em torno de
    # montar_envelope dentro de pagina_matriz() — a validade malformada
    # deixaria de virar st.error e passaria a estourar exceção não tratada
    # (at.exception, não at.error), e o espião abaixo teria sido chamado.
    chamadas: list[int] = []

    def _rota_espia(*args: Any, **kwargs: Any) -> tuple[None, None, tuple[Pendencia, ...], None]:
        chamadas.append(1)
        return None, None, (), None  # type: ignore[return-value]

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.executar_rota_determinista_cacheada", _rota_espia
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()

    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()

    indice_validade = len(at.text_input) - 1
    at.text_input[indice_validade].set_value("31/12/2023").run()
    at.button[0].click().run()

    assert not at.exception
    assert at.error
    assert chamadas == []


# ---------------------------------------------------------------------------
# Emenda 003.EQ (2ª) — cache do CARO (processar_arquivo_pgr) por chave de
# PDF+envelope; regeneração incondicional do BARATO (gerar_documento).
# download_button não é simulável por AppTest nesta versão de Streamlit
# (element_tree.py sem case para "download_button" -> UnknownElement,
# não-Widget; sem accessor em dir(AppTest)) — decisão do Arquiteto foi
# cobrir a decisão de reuso por teste de unidade sobre o núcleo, não pela
# casca. O fio real clique-de-download -> não-reprocessamento segue sem
# cobertura automatizada (DH-003EQ-01, registrada no fechamento).
# ---------------------------------------------------------------------------


def test_deve_reprocessar_quando_o_pdf_muda() -> None:
    # Reversão que mata: fazer deve_reprocessar ignorar a chave e devolver
    # False sempre — o cache de um PDF diferente seria reaproveitado.
    assert deve_reprocessar("chave-pdf-novo", "chave-pdf-velho") is True


def test_nao_reprocessa_quando_a_chave_e_identica() -> None:
    # Reversão que mata: devolver True sempre — todo rerun reprocessaria,
    # inclusive quando PDF e envelope não mudaram.
    assert deve_reprocessar("mesma-chave", "mesma-chave") is False


def test_troca_de_cabecalho_regenera_documento_sem_reprocessar(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Reversão que mata: incluir cabeçalho/rodapé na chave de
    # calcular_chave_cache — a segunda chamada, com cabeçalho diferente mas
    # MESMO pdf/envelope, passaria a divergir do cache e reprocessaria
    # (contagem de chamadas ao processar_arquivo_pgr viraria 2, não 1).
    chamadas: list[int] = []
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Único",))
    resultado_sintetico = Resultado(status="OK", matrizes=[matriz])

    def _processar_espiao(*args: Any, **kwargs: Any) -> tuple[Resultado, tuple[Pendencia, ...]]:
        chamadas.append(1)
        return resultado_sintetico, ()

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.processar_arquivo_pgr", _processar_espiao
    )

    envelope = EnvelopeConfirmado(validade=date(2030, 1, 1), assinatura_engenheiro=True)
    conteudo_pdf = b"conteudo qualquer do pdf"
    caminho_pdf = tmp_path / "fake.pdf"

    cabecalho1 = _cabecalho()
    doc1, html1, _pendencias1, cache = executar_rota_determinista_cacheada(
        caminho_pdf, conteudo_pdf, envelope, cabecalho1, _rodape(), None
    )

    cabecalho2 = CabecalhoDocumento(
        empresa="Outra Empresa",
        obra="Outra Obra",
        tipo_documento="Outro Tipo",
        data="02/08/2026",
        medico_coordenador="Outro Médico",
        crm="CRM-GO 1111",
    )
    doc2, html2, _pendencias2, cache2 = executar_rota_determinista_cacheada(
        caminho_pdf, conteudo_pdf, envelope, cabecalho2, _rodape(), cache
    )

    assert len(chamadas) == 1
    assert doc1 is not None and doc2 is not None
    assert doc1.cabecalho.empresa == "Empresa Teste"
    assert doc2.cabecalho.empresa == "Outra Empresa"
    assert cache2.chave == cache.chave


# ---------------------------------------------------------------------------
# Emenda 003.EQ (3ª) — bloqueador do documento vazio assinável. Achado real
# (upload nativo, máquina do Diovanni): Resultado(status="REJEITADO",
# matrizes=[]) tem matrizes=() != None, então o guard `doc is None` nunca
# pegava esse ramo — a casca montava e oferecia um documento sem tabela
# nenhuma para download. Quatro elos corrigidos: A) parada dura no gate
# eliminatório; B) pendencias_globais sempre na tela, antes das de extração
# (D-ARQ-08); C) guarda anti-documento-vazio independente do gate (D-ARQ-22);
# D) estado REJEITADO nunca grava cache.
# ---------------------------------------------------------------------------


def _submeter_formulario(at: AppTest, validade: str = "2026-12-31") -> None:
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    indice_validade = len(at.text_input) - 1
    at.text_input[indice_validade].set_value(validade).run()
    at.checkbox[0].set_value(True).run()
    at.button[0].click().run()


def test_status_rejeitado_mostra_motivo_e_nao_oferece_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: trocar `cache.status == "REJEITADO"` por
    # `cache.status is None` — status de um Resultado REJEITADO de verdade é
    # a STRING "REJEITADO", nunca None, então o guard revertido nunca
    # dispara e o motivo do gate (R-PGR-01/NR-18) nunca aparece na tela — só
    # a guarda genérica anti-vazio (elo C) pegaria o caso, com outro texto.
    chamadas_download: list[int] = []

    def _download_espiao(*args: Any, **kwargs: Any) -> bool:
        chamadas_download.append(1)
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)

    pendencia_gate = Pendencia(
        tipo="assinatura_invalida",
        destinatario="empresa",
        motivo="PGR não assinado por engenheiro de segurança do trabalho (NR-18)",
        bloqueante=True,
        regra_origem="R-PGR-01",
    )
    resultado_rejeitado = Resultado(
        status="REJEITADO",
        matrizes=[],
        pendencias_globais=[pendencia_gate],
        motivo_rejeicao=pendencia_gate.motivo,
    )

    def _processar_falso(*args: Any, **kwargs: Any) -> tuple[Resultado, tuple[Pendencia, ...]]:
        return resultado_rejeitado, ()

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.processar_arquivo_pgr", _processar_falso
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert at.error
    # Especificamente a mensagem do elo A ("PGR rejeitado...") — não basta o
    # motivo aparecer em algum lugar da tela: o elo B (pendencias_globais
    # sempre visíveis) também renderiza o mesmo motivo, então checar só
    # "R-PGR-01 in texto" não discrimina a reversão (ela ainda passaria pelo
    # elo B + pela guarda genérica do elo C).
    assert any("PGR rejeitado" in e.value for e in at.error)
    texto_markdown = "\n".join(el.value for el in at.markdown)
    assert "R-PGR-01" in texto_markdown
    assert "NR-18" in texto_markdown
    assert chamadas_download == []


def test_pendencias_globais_aparecem_antes_das_de_extracao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: remover o bloco `if cache.pendencias_globais: ...`
    # — o marcador MOTIVO-GLOBAL-UNICO some do texto renderizado.
    pendencia_global = Pendencia(
        tipo="pgr_informativo_global",
        destinatario="empresa",
        motivo="MOTIVO-GLOBAL-UNICO",
        bloqueante=False,
        regra_origem="R-PGR-99",
    )
    pendencia_extracao = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="extracao",
        motivo="MOTIVO-EXTRACAO-UNICO",
        bloqueante=False,
        regra_origem="D-ARQ-14",
    )
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Teste",))
    resultado = Resultado(status="OK", matrizes=[matriz], pendencias_globais=[pendencia_global])

    def _processar_falso(*args: Any, **kwargs: Any) -> tuple[Resultado, tuple[Pendencia, ...]]:
        return resultado, (pendencia_extracao,)

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.processar_arquivo_pgr", _processar_falso
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    textos = [el.value for el in at.markdown]
    idx_global = next(i for i, t in enumerate(textos) if "MOTIVO-GLOBAL-UNICO" in t)
    idx_extracao = next(i for i, t in enumerate(textos) if "MOTIVO-EXTRACAO-UNICO" in t)
    assert idx_global < idx_extracao


def test_documento_sem_linha_cargo_nao_e_oferecido_para_download(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: remover o bloco `if total_linhas_cargo == 0: ...
    # return` — o documento sem nenhuma LinhaCargo (GHE com cargos=())
    # passaria a oferecer os dois downloads mesmo vazio.
    chamadas_download: list[int] = []

    def _download_espiao(*args: Any, **kwargs: Any) -> bool:
        chamadas_download.append(1)
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)

    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=())
    resultado = Resultado(status="OK", matrizes=[matriz])

    def _processar_falso(*args: Any, **kwargs: Any) -> tuple[Resultado, tuple[Pendencia, ...]]:
        return resultado, ()

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.processar_arquivo_pgr", _processar_falso
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert at.error
    assert chamadas_download == []
