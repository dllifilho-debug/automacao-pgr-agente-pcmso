"""Testes do núcleo puro de web_matriz.py (003.EQ S3 fatia 1) — cada teste
carrega, junto, a reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

import ast
from collections.abc import Sequence
from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    PGR,
    BlocoVerbatim,
    EnvelopeConfirmado,
    ExameEmitido,
    GHEPGR,
    GHEVerbatim,
    MatrizGHE,
    MembroVerbatim,
    Momento,
    Pendencia,
    Resultado,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_pgr import transcrever_ghes
from agente_medico.superficie.documento_matriz import CabecalhoDocumento, LinhaCargo, RodapeDocumento
from agente_medico.superficie.web_matriz import (
    CacheMatrizes,
    _TranscritorContado,
    anexar_produto_e_reprocessar,
    deve_reprocessar,
    executar_rota_determinista,
    executar_rota_determinista_cacheada,
    gerar_documento,
    montar_envelope,
    pagina_matriz,
    preparar_composicao_cacheada,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _ghe_pgr(
    *,
    ghe_id: str = "GHE-01",
    nome: str = "",
    cargos: tuple[str, ...] = (),
) -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome=nome,
        cargos=cargos,
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _pgr_sintetico(*ghes: GHEPGR) -> PGR:
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=ghes or (_ghe_pgr(),))


def _mockar_parse_deterministico(
    monkeypatch: pytest.MonkeyPatch,
    resultado: Resultado,
    pendencias_extracao: tuple[Pendencia, ...] = (),
    pgr: PGR | None = None,
) -> None:
    """Substitui a dupla preparar_pgr_hidratado + processar_pgr (D-ARQ-49
    fatia 2a) — equivalente ao antigo mock único de processar_arquivo_pgr,
    decomposto porque a fatia 2a expôs o PGR intermediário."""
    pgr_sintetico = pgr if pgr is not None else _pgr_sintetico()

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr_sintetico, pendencias_extracao

    def _processar_pgr_falso(*args: Any, **kwargs: Any) -> Resultado:
        return resultado

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    monkeypatch.setattr("agente_medico.superficie.web_matriz.processar_pgr", _processar_pgr_falso)


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

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[None, tuple[Pendencia, ...]]:
        return None, (pendencia,)

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso
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
    # (contagem de chamadas à parte CARA — preparar_pgr_hidratado — viraria
    # 2, não 1).
    chamadas: list[int] = []
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Único",))
    resultado_sintetico = Resultado(status="OK", matrizes=[matriz])
    pgr_sintetico = _pgr_sintetico()

    def _preparar_espiao(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        chamadas.append(1)
        return pgr_sintetico, ()

    def _processar_pgr_falso(*args: Any, **kwargs: Any) -> Resultado:
        return resultado_sintetico

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_espiao
    )
    monkeypatch.setattr("agente_medico.superficie.web_matriz.processar_pgr", _processar_pgr_falso)

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

    _mockar_parse_deterministico(monkeypatch, resultado_rejeitado)

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

    _mockar_parse_deterministico(monkeypatch, resultado, pendencias_extracao=(pendencia_extracao,))

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

    _mockar_parse_deterministico(monkeypatch, resultado)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert at.error
    assert chamadas_download == []


# ---------------------------------------------------------------------------
# 003.EW — _TranscritorContado (contador de blocos lidos por IA) + aviso de
# procedência na tela.
# ---------------------------------------------------------------------------


class _TranscritorFalso:
    def transcrever(self, bloco: str) -> GHEVerbatim:
        return GHEVerbatim(nome="GHE Falso", cargos=("Cargo Falso",), riscos=())


class _TranscritorQueLevanta:
    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")


def test_transcritor_contado_conta_cada_invocacao() -> None:
    # Reversão que mata: remover `self.chamadas += 1` do wrapper.
    contado = _TranscritorContado(interno=_TranscritorFalso())
    assert contado.chamadas == 0
    contado.transcrever("bloco 1")
    contado.transcrever("bloco 2")
    assert contado.chamadas == 2


def test_transcritor_contado_propaga_transcricao_indisponivel() -> None:
    # Reversão que mata: envolver o `return` num try/except que devolve
    # GHEVerbatim vazio — é o que impede o wrapper de virar um mascarador de
    # falha.
    contado = _TranscritorContado(interno=_TranscritorQueLevanta())
    with pytest.raises(TranscricaoIndisponivel):
        contado.transcrever("bloco")
    assert contado.chamadas == 1


# ---------------------------------------------------------------------------
# 003.EW emenda (Arquiteto) — _TranscritorContado.transcrever_lote: sem ele,
# transcrever_ghes não enxerga o lote por duck-typing através do wrapper, e o
# caminho de produção volta a uma requisição por bloco (o problema original
# da fatia 2: 18 de 20 da cota diária).
# ---------------------------------------------------------------------------


class _TranscritorFalsoComLote:
    """Duplo cujo interno OFERECE transcrever_lote — prova que o wrapper
    delega ao lote em vez de cair no unitário quando o interno o tem."""

    def __init__(self) -> None:
        self.lotes_recebidos: list[list[str]] = []
        self.chamadas_unitarias = 0

    def transcrever(self, bloco: str) -> GHEVerbatim:
        self.chamadas_unitarias += 1
        return GHEVerbatim(nome="nao deveria ser chamado", cargos=(), riscos=())

    def transcrever_lote(self, blocos: Sequence[str]) -> tuple[GHEVerbatim, ...]:
        self.lotes_recebidos.append(list(blocos))
        return tuple(GHEVerbatim(nome=f"GHE {i}", cargos=(), riscos=()) for i in range(len(blocos)))


def test_transcritor_contado_delega_lote_quando_interno_o_tem() -> None:
    # Reversão que mata: remover transcrever_lote do wrapper —
    # transcrever_ghes deixa de enxergar o lote por duck-typing (getattr não
    # encontra o método) e volta ao caminho unitário: o duplo interno
    # registraria N chamadas unitárias em vez de UMA chamada em lote.
    interno = _TranscritorFalsoComLote()
    contado = _TranscritorContado(interno=interno)
    blocos = ["bloco 1", "bloco 2", "bloco 3"]

    resultado = transcrever_ghes(blocos, contado)

    assert len(resultado) == 3
    assert interno.lotes_recebidos == [blocos]
    assert interno.chamadas_unitarias == 0
    assert contado.chamadas == len(blocos)


def test_transcritor_contado_cai_no_unitario_quando_interno_nao_tem_lote() -> None:
    # Reversão que mata: remover o ramo de fallback (`return
    # tuple(self.interno.transcrever(b) for b in blocos)`) — sem ele, o
    # wrapper levanta TypeError/AttributeError ao tentar chamar
    # transcrever_lote inexistente no interno (_TranscritorFalso só tem
    # transcrever).
    interno = _TranscritorFalso()
    contado = _TranscritorContado(interno=interno)
    blocos = ["bloco 1", "bloco 2"]

    resultado = transcrever_ghes(blocos, contado)

    esperado = GHEVerbatim(nome="GHE Falso", cargos=("Cargo Falso",), riscos=())
    assert resultado == (esperado, esperado)
    assert contado.chamadas == len(blocos)


def test_zero_chamadas_ia_nao_mostra_aviso_de_procedencia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: trocar `if cache.chamadas_ia > 0` por `>= 0` na
    # casca — a mensagem "lido(s) por IA" passaria a aparecer sempre, mesmo
    # com a rota determinística cobrindo 100% dos blocos.
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Teste",))
    resultado = Resultado(status="OK", matrizes=[matriz])

    _mockar_parse_deterministico(monkeypatch, resultado)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert not at.info
    textos = [el.value for el in at.markdown]
    assert not any("lido(s) por IA" in t for t in textos)


# ---------------------------------------------------------------------------
# FDS/FISPQ avulsa (fatia "só FDS") — upload opcional, independente do PGR.
# ---------------------------------------------------------------------------


def test_pagina_matriz_fds_avulsa_sem_pgr_mostra_composicao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: mover o bloco de upload/processamento de FDS pra
    # DEPOIS do `if arquivo is None: return` — sem PGR, a função retornaria
    # antes de processar a FDS, e o CAS/frases-H nunca apareceriam na tela.
    bloco = BlocoVerbatim(
        faixa="1-5%",
        membros=(MembroVerbatim(cas="71-43-2", nome="Benzeno", frases_h=("H350", "H340")),),
    )

    def _preparar_falso(
        *args: Any, **kwargs: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        return (bloco,), ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_falso)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[1].set_value([("fds.pdf", b"conteudo qualquer", "application/pdf")]).run()

    assert not at.exception
    textos = [el.value for el in at.markdown]
    assert any("71-43-2" in t and "Benzeno" in t for t in textos)
    assert any("H350" in t and "H340" in t for t in textos)


def test_pagina_matriz_sem_fds_nao_chama_preparar_composicao(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: trocar `for arquivo_fds in arquivos_fds or ()` por
    # algo que itere mesmo com arquivos_fds vazio/None — preparar_composicao
    # seria chamada sem nenhum upload de FDS.
    chamadas: list[int] = []

    def _preparar_espiao(
        *args: Any, **kwargs: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        chamadas.append(1)
        return (), ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_espiao)

    at = AppTest.from_function(pagina_matriz)
    at.run()

    assert not at.exception
    assert chamadas == []


def test_pagina_matriz_fds_avulsa_mostra_pendencias(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: remover o laço `for p in pendencias_fds: st.write(...)`
    # — pendência bloqueante da FDS (ex. composição ausente) desapareceria da
    # tela, violando D-ARQ-22/31 (nunca silenciar pendência).
    pendencia = Pendencia(
        tipo="composicao_ausente_fds",
        destinatario="extracao",
        motivo="Região de composição não localizada",
        bloqueante=True,
        regra_origem="D-ARQ-47",
    )

    def _preparar_falso(
        *args: Any, **kwargs: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        return (), (pendencia,)

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_falso)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[1].set_value([("fds.pdf", b"conteudo qualquer", "application/pdf")]).run()

    assert not at.exception
    textos = [el.value for el in at.markdown]
    assert any("composicao_ausente_fds" in t for t in textos)


def test_pagina_matriz_fds_avulsa_com_pgr_nao_interfere_no_fluxo_pgr(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: qualquer mudança que faça o upload de FDS estourar
    # ou pular o fluxo normal do PGR antes do `if arquivo is None` — o
    # formulário do PGR deixaria de aparecer mesmo com o PGR enviado.
    def _preparar_falso(
        *args: Any, **kwargs: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        return (), ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_falso)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    at.file_uploader[1].set_value([("fds.pdf", b"conteudo qualquer", "application/pdf")]).run()

    assert not at.exception
    assert at.button  # formulário do PGR renderizou normalmente (form_submit_button)


# ---------------------------------------------------------------------------
# D-ARQ-49 Parte 2 fatia 2b — casamento manual FDS<->produto: RT escolhe o
# GHE e nomeia o produto na tela; anexar_produto_e_reprocessar roda
# processar_pgr de novo sobre o PGR já hidratado, sem tocar PDF/LLM.
# ---------------------------------------------------------------------------

_FDS_TOLUENO = BlocoVerbatim(
    faixa="6-10%",
    membros=(MembroVerbatim(cas="108-88-3", nome="Tolueno", frases_h=()),),
)


def test_anexar_produto_e_reprocessar_promove_componente_fase_c() -> None:
    # Reversão que mata: fazer anexar_produto_e_reprocessar devolver o cache
    # original sem rodar processar_pgr sobre o PGR mutado (ou sem de fato
    # anexar o ProdutoQuimico ao GHE certo) — "tolueno" nunca apareceria em
    # riscos_resolvidos: a promoção Fase C (estagios/riscos.py, componentes
    # de FDS -> Risco, via resolver_composicao dentro de processar_pgr) nunca
    # rodaria sobre o produto novo. composicao_verbatim (não composicao) é o
    # que anexar_produto_e_reprocessar planta no PGR anexado — a resolução
    # (gate_cas) é sempre recalculada dentro de processar_pgr, nunca
    # persistida de volta em cache.pgr_hidratado (mesma invariante de
    # resolver_composicao: puro, refeito a cada chamada).
    protocolo = carregar(_PROTOCOLO_DIR)
    ghe = _ghe_pgr(ghe_id="GHE-01", nome="Pintura", cargos=("Pintor",))
    pgr = _pgr_sintetico(ghe)
    cache = CacheMatrizes(
        chave="chave-teste",
        matrizes=(),
        exames_vocab=protocolo.vocabulario.exames,
        pendencias=(),
        status="OK",
        pendencias_globais=(),
        chamadas_ia=0,
        pgr_hidratado=pgr,
    )
    fds_extraida = montar_fds((_FDS_TOLUENO,))

    cache_novo = anexar_produto_e_reprocessar(cache, protocolo, "GHE-01", "Tinta Fascino", fds_extraida)

    assert cache_novo.pgr_hidratado is not None
    produto = cache_novo.pgr_hidratado.ghes[0].produtos_quimicos[0]
    assert produto.nome == "Tinta Fascino"
    assert produto.fds is not None
    assert produto.fds.composicao_verbatim[0].membros[0].cas == "108-88-3"
    assert cache_novo.matrizes is not None
    assert "tolueno" in cache_novo.matrizes[0].riscos_resolvidos
    # chamadas_ia preservado do cache original — anexar não reprocessa PDF/LLM.
    assert cache_novo.chamadas_ia == 0


def test_anexar_produto_e_reprocessar_anexa_so_no_ghe_escolhido() -> None:
    # Reversão que mata: trocar o filtro `ghe.id == ghe_id` por algo que
    # anexe o produto em todo GHE (ou no primeiro, ignorando ghe_id) — o
    # componente promovido apareceria também no GHE-02, que nunca recebeu FDS.
    protocolo = carregar(_PROTOCOLO_DIR)
    ghe1 = _ghe_pgr(ghe_id="GHE-01", nome="Pintura", cargos=("Pintor",))
    ghe2 = _ghe_pgr(ghe_id="GHE-02", nome="Almoxarifado", cargos=("Almoxarife",))
    pgr = _pgr_sintetico(ghe1, ghe2)
    cache = CacheMatrizes(
        chave="chave-teste",
        matrizes=(),
        exames_vocab=protocolo.vocabulario.exames,
        pendencias=(),
        status="OK",
        pendencias_globais=(),
        chamadas_ia=0,
        pgr_hidratado=pgr,
    )
    fds_extraida = montar_fds((_FDS_TOLUENO,))

    cache_novo = anexar_produto_e_reprocessar(cache, protocolo, "GHE-01", "Tinta Fascino", fds_extraida)

    assert cache_novo.pgr_hidratado is not None
    ghe1_novo, ghe2_novo = cache_novo.pgr_hidratado.ghes
    assert len(ghe1_novo.produtos_quimicos) == 1
    assert ghe2_novo.produtos_quimicos == ()


def test_pagina_matriz_fds_anexada_persiste_entre_reruns_sem_chamada_ia(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: não persistir o PGR mutado em st.session_state após
    # o clique em "Anexar ao GHE selecionado" — o próximo rerun do Streamlit
    # (aqui, um 2º at.run() sem tocar em nenhum widget) buscaria de novo o
    # cache ANTIGO de session_state e o componente prometido some.
    pgr_sintetico = _pgr_sintetico(_ghe_pgr(ghe_id="GHE-01", nome="Pintura", cargos=("Pintor",)))

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr_sintetico, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    # processar_pgr NÃO é mockado aqui — a promoção Fase C precisa rodar de
    # verdade para "tolueno" aparecer em riscos_resolvidos.

    def _preparar_composicao_falso(
        *args: Any, **kwargs: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        return (_FDS_TOLUENO,), ()

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_composicao", _preparar_composicao_falso
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    assert not at.exception

    cache_antes = at.session_state["web_matriz_cache"]
    assert cache_antes.pgr_hidratado is not None
    assert cache_antes.pgr_hidratado.ghes[0].produtos_quimicos == ()

    at.file_uploader[1].set_value([("fds.pdf", b"conteudo qualquer", "application/pdf")]).run()
    assert not at.exception

    at.button(key="anexar_fds_fds.pdf").click().run()
    assert not at.exception

    cache_depois = at.session_state["web_matriz_cache"]
    produto = cache_depois.pgr_hidratado.ghes[0].produtos_quimicos[0]
    assert produto.fds.composicao_verbatim[0].membros[0].cas == "108-88-3"
    assert "tolueno" in cache_depois.matrizes[0].riscos_resolvidos
    assert cache_depois.chamadas_ia == 0

    # Reversão-alvo: rerun seguinte, sem tocar em nenhum widget — se a casca
    # não persistiu em st.session_state, este 2º .run() perderia o produto.
    at.run()
    assert not at.exception
    cache_rerun = at.session_state["web_matriz_cache"]
    assert cache_rerun.pgr_hidratado.ghes[0].produtos_quimicos != ()
    assert "tolueno" in cache_rerun.matrizes[0].riscos_resolvidos
    assert cache_rerun.chamadas_ia == 0


# ---------------------------------------------------------------------------
# Memoização da transcrição de FDS por conteúdo — antes, cada rerun do
# Streamlit re-transcrevia todas as FDS (HTTP 429 em produção) e o clique em
# "Anexar" se perdia quando a cota estourava no rerun do próprio clique.
# ---------------------------------------------------------------------------

_PENDENCIA_429 = Pendencia(
    tipo="transcricao_indisponivel_fds",
    destinatario="extracao",
    motivo="cascata Gemini sem resposta íntegra (200 + STOP) — HTTP 429",
    bloqueante=True,
    regra_origem="D-ARQ-47",
)


def test_preparar_composicao_cacheada_nao_retranscreve_mesmo_conteudo(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Reversão que mata: remover o `if chave in cache: return cache[chave]`
    # de preparar_composicao_cacheada — a 2ª chamada com os mesmos bytes
    # invocaria o transcritor de novo (chamadas == 2).
    chamadas: list[Path] = []

    def _preparar_espiao(caminho: Path, cliente: Any) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        chamadas.append(caminho)
        return (_FDS_TOLUENO,), ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_espiao)
    cache: dict[str, Any] = {}
    primeira = preparar_composicao_cacheada(tmp_path / "a.pdf", b"fds", object(), cache)  # type: ignore[arg-type]
    segunda = preparar_composicao_cacheada(tmp_path / "b.pdf", b"fds", object(), cache)  # type: ignore[arg-type]

    assert len(chamadas) == 1
    assert primeira == segunda == ((_FDS_TOLUENO,), ())


def test_preparar_composicao_cacheada_nao_memoiza_falha_de_invocacao(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Reversão que mata: memoizar incondicionalmente (remover o guard de
    # `transcricao_indisponivel_fds`) — o 429 ficaria gravado e a 2ª chamada
    # devolveria a pendência em vez de tentar de novo e obter a composição.
    respostas = iter([((), (_PENDENCIA_429,)), ((_FDS_TOLUENO,), ())])

    def _preparar_falso(caminho: Path, cliente: Any) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        return next(respostas)

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", _preparar_falso)
    cache: dict[str, Any] = {}
    primeira = preparar_composicao_cacheada(tmp_path / "a.pdf", b"fds", object(), cache)  # type: ignore[arg-type]
    segunda = preparar_composicao_cacheada(tmp_path / "a.pdf", b"fds", object(), cache)  # type: ignore[arg-type]

    assert primeira == ((), (_PENDENCIA_429,))
    assert segunda == ((_FDS_TOLUENO,), ())


def test_pagina_matriz_anexar_fds_nao_retranscreve_e_sobrevive_a_429(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reproduz o caso de produção (PGR CMO Aurora, 23/09/2026): cota estoura
    # depois da 1ª leitura. Reversão que mata: a casca voltar a chamar
    # preparar_composicao direto, ou não persistir o cache de FDS em
    # st.session_state (dict novo a cada rerun) — o rerun do clique
    # re-transcreve, recebe o 429, o botão some e o produto não é anexado.
    pgr_sintetico = _pgr_sintetico(_ghe_pgr(ghe_id="GHE-18", nome="PINTURA", cargos=("Pintor",)))

    def _preparar_pgr_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr_sintetico, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_pgr_falso)
    chamadas: list[str] = []

    def _preparar_composicao_com_cota(
        caminho: Path, cliente: Any
    ) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
        chamadas.append(caminho.name)
        if len(chamadas) > 2:
            return (), (_PENDENCIA_429,)
        return (_FDS_TOLUENO,), ()

    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_composicao", _preparar_composicao_com_cota
    )

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    at.file_uploader[1].set_value(
        [("f0.pdf", b"fds zero", "application/pdf"), ("f1.pdf", b"fds um", "application/pdf")]
    ).run()
    assert not at.exception
    assert chamadas == ["f0.pdf", "f1.pdf"]

    at.button(key="anexar_fds_f0.pdf").click().run()
    assert not at.exception

    assert chamadas == ["f0.pdf", "f1.pdf"]
    produtos = at.session_state["web_matriz_cache"].pgr_hidratado.ghes[0].produtos_quimicos
    assert [produto.nome for produto in produtos] == ["f0"]
