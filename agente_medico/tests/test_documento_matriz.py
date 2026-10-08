from __future__ import annotations

import time
from datetime import date
from pathlib import Path

import pytest
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from docx.shared import Pt

from agente_medico.adaptadores.orquestracao_pgr import processar_arquivo_pgr
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import EnvelopeConfirmado, ExameEmitido, GHEVerbatim, MatrizGHE, Momento
from agente_medico.superficie.documento_matriz import (
    _COR_FAIXA_GHE_HEX,
    _ROTULO_MOMENTO,
    TITULO_MATRIZ,
    CabecalhoDocumento,
    RodapeDocumento,
    montar_documento,
    nome_ghe_exibicao,
    renderizar_docx,
    renderizar_html,
    titulo_ghe,
    titulo_ghe_rq61,
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


def _exame(
    slug: str, periodicidade: int = 12, momentos: set[Momento] | None = None
) -> ExameEmitido:
    return ExameEmitido(
        exame=slug,
        periodicidade_meses=periodicidade,
        momentos=momentos if momentos is not None else {Momento.ADM},
    )


# ---------------------------------------------------------------------------
# 003.EO EMENDA 1 — ordem_exibicao (2 dos 3 testes; a unicidade mora em
# test_vocabulario.py por ser checagem pura de yaml).
# ---------------------------------------------------------------------------


def test_ordem_das_celulas_segue_ordem_exibicao_do_vocabulario() -> None:
    # Reversão que mata: ordenar por `exame.exame` (slug alfabético) em vez de
    # por `ordem_exibicao`. "zebra" (ordem 1) vem alfabeticamente DEPOIS de
    # "abacate" (ordem 2) — só a ordem_exibicao acerta a posição.
    vocab = {
        "zebra": {"nome_exibicao": "Zebra", "ordem_exibicao": 1},
        "abacate": {"nome_exibicao": "Abacate", "ordem_exibicao": 2},
    }
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[_exame("abacate"), _exame("zebra")],
        cargos=("Cargo Único",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celulas = doc.blocos[0].linhas[0].celulas
    assert celulas[0].startswith("Zebra")
    assert celulas[1].startswith("Abacate")


def test_exame_sem_ordem_exibicao_vai_para_o_fim() -> None:
    # Reversão que mata: fallback devolver 0 em vez de sentinela-por-tag alta
    # -> "aaa_sem_ordem" (sem campo) subiria para o topo por ser 0 == menor
    # ordem_exibicao possível. Aqui ele tem que ficar depois de "so_com_ordem"
    # (ordem_exibicao=5) mesmo perdendo no alfabeto.
    vocab = {
        "so_com_ordem": {"nome_exibicao": "Com Ordem", "ordem_exibicao": 5},
        "aaa_sem_ordem": {"nome_exibicao": "Sem Ordem"},
    }
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[_exame("aaa_sem_ordem"), _exame("so_com_ordem")],
        cargos=("Cargo Único",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celulas = doc.blocos[0].linhas[0].celulas
    assert celulas[0].startswith("Com Ordem")
    assert celulas[1].startswith("Sem Ordem")


# ---------------------------------------------------------------------------
# Fatia 2 do prompt original — expansão GHE→cargo + emissor HTML.
# ---------------------------------------------------------------------------


def test_expansao_ghe_cargo_replica_celulas() -> None:
    # Reversão que mata: só o primeiro cargo recebe as células (ex.: `linhas =
    # (LinhaCargo(matriz.cargos[0], celulas),)` em vez de um por cargo).
    vocab = {
        "exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1},
        "audiometria": {"nome_exibicao": "Audiometria", "ordem_exibicao": 2},
        "hemograma": {"nome_exibicao": "Hemograma", "ordem_exibicao": 3},
    }
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[_exame("exame_clinico"), _exame("audiometria"), _exame("hemograma")],
        cargos=("Carpinteiro", "Ajudante", "Encarregado", "Estagiário"),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    bloco = doc.blocos[0]
    assert len(bloco.linhas) == 4
    celulas_esperadas = bloco.linhas[0].celulas
    assert len(celulas_esperadas) == 3
    for linha in bloco.linhas:
        assert linha.celulas == celulas_esperadas


def test_ghe_sem_cargos_nao_inventa_linha() -> None:
    # Reversão que mata: inserir um placeholder "(sem cargo)" no ramo vazio.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=())
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    assert doc.blocos[0].linhas == ()


def test_mapa_momentos_cobre_todos_os_membros_do_enum() -> None:
    # Reversão que mata: remover uma entrada do mapa (ex.: RT).
    assert set(_ROTULO_MOMENTO.keys()) == set(Momento)


def test_celula_usa_nome_exibicao_do_vocabulario() -> None:
    # Reversão que mata: usar exame.exame (o slug) em vez do nome_exibicao.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(
        ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("Cargo",)
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert "Exame Clínico" in celula
    assert "exame_clinico" not in celula


# DT-003EW-02 — periodicidade impressa na celula. Regra de 003.EO, medida
# contra o acervo em 29/08/2026 (28 documentos, instrumento
# scripts/medir_cobertura_e_forma.py): 2896 confirmam / 122 contrariam nos
# 10 documentos de 2026, contra 1323/1681 nos de 2025. E a convencao
# corrente do escritorio, nao invariante do acervo historico — o app emite
# documento novo, logo emite a convencao corrente.
# Medicao, corte por documento e ressalvas em
# docs/referencia/MEDICAO_003FE_regra_forma_periodicidade.md.


def test_periodicidade_diferente_de_12_meses_imprime_o_numero() -> None:
    # Reversão que mata: `mostrar` fixo em False (nunca imprime o número).
    vocab = {"espirometria": {"nome_exibicao": "Espirometria"}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[
            _exame(
                "espirometria",
                periodicidade=24,
                momentos={Momento.ADM, Momento.PER, Momento.MR, Momento.DEM},
            )
        ],
        cargos=("Cargo",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert celula == "Espirometria (ADM, PER 24 meses, MRO, DEM)"


def test_periodicidade_de_12_meses_nao_imprime_o_numero() -> None:
    # Reversão que mata: `mostrar` fixo em True (sempre imprime o número).
    vocab = {"audiometria": {"nome_exibicao": "Audiometria"}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[
            _exame(
                "audiometria",
                periodicidade=12,
                momentos={Momento.ADM, Momento.PER, Momento.MR, Momento.DEM},
            )
        ],
        cargos=("Cargo",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert celula == "Audiometria (ADM, PER, MRO, DEM)"


def test_rx_torax_oit_imprime_periodicidade_mesmo_a_12_meses() -> None:
    # Reversão que mata: remover o termo `or bool(entrada.get(
    # "periodicidade_sempre_visivel", False))` de `_formatar_celula` — sem ele a
    # exceção não existe e rx_torax_oit a 12M sai sem número. (Apagar o campo do
    # YAML mata o teste 6, não este: aqui o vocabulário é literal.)
    vocab = {"rx_torax_oit": {"nome_exibicao": "RX Tórax OIT", "periodicidade_sempre_visivel": True}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[
            _exame(
                "rx_torax_oit",
                periodicidade=12,
                momentos={Momento.ADM, Momento.PER, Momento.MR, Momento.DEM},
            )
        ],
        cargos=("Cargo",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert celula == "RX Tórax OIT (ADM, PER 12 meses, MRO, DEM)"


def test_exame_clinico_semestral_imprime_seis_meses() -> None:
    # Reversão que mata: trocar `!= 12` por `> 12` — 6 é menor que 12, ficaria
    # mudo justo no caso que a regra existe para cobrir.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico"}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[
            _exame(
                "exame_clinico",
                periodicidade=6,
                momentos={Momento.ADM, Momento.PER, Momento.MR, Momento.RT, Momento.DEM},
            )
        ],
        cargos=("Cargo",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert celula == "Exame Clínico (ADM, PER 6 meses, MRO, RET, DEM)"


def test_numero_so_gruda_no_momento_per() -> None:
    # Reversão que mata: grudar o número no primeiro momento presente em vez
    # de especificamente no PER — aqui não há PER, então nenhum número sai.
    vocab = {"rx_coluna_lombo_sacra": {"nome_exibicao": "RX Coluna Lombo-Sacra"}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[
            _exame(
                "rx_coluna_lombo_sacra",
                periodicidade=24,
                momentos={Momento.ADM, Momento.MR},
            )
        ],
        cargos=("Cargo",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    celula = doc.blocos[0].linhas[0].celulas[0]
    assert celula == "RX Coluna Lombo-Sacra (ADM, MRO)"


def test_periodicidade_sempre_visivel_e_exatamente_rx_torax_oit() -> None:
    # Reversão que mata: acrescentar o campo em outro exame do vocabulário
    # real sem medir a exceção — computado sobre o YAML de produção (D-ARQ-67).
    from agente_medico.motor.protocolo import carregar

    protocolo = carregar(Path(__file__).parent.parent / "protocolo")
    marcados = {
        slug
        for slug, entrada in protocolo.vocabulario.exames.items()
        if entrada.get("periodicidade_sempre_visivel")
    }
    assert marcados == {"rx_torax_oit"}


def test_html_escapa_conteudo_de_dado() -> None:
    # Reversão que mata: remover a chamada de escape (montar a célula/cargo
    # direto na f-string do HTML).
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[_exame("exame_clinico")],
        cargos=("<script>alert(1)</script>",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())
    saida = renderizar_html(doc)
    assert "<script>alert(1)</script>" not in saida
    assert "&lt;script&gt;" in saida


# ---------------------------------------------------------------------------
# Fatia 3 — emissor DOCX. Mesma DocumentoMatriz da fatia 2, não recalcula nada.
# ---------------------------------------------------------------------------


def _docx(tmp_path: Path, documento: object) -> DocxDocument:  # type: ignore[valid-type]
    destino = tmp_path / "matriz.docx"
    renderizar_docx(documento, destino)  # type: ignore[arg-type]
    return DocxDocument(str(destino))


def _fundo(celula: object) -> str | None:
    tcPr = celula._tc.tcPr  # type: ignore[attr-defined]
    sombreado = None if tcPr is None else tcPr.find(qn("w:shd"))
    return None if sombreado is None else str(sombreado.get(qn("w:fill"))).upper()


def test_docx_ghes_numa_tabela_continua_com_faixa_azul_por_ghe(tmp_path: Path) -> None:
    # D-ARQ-73, emenda de 07/10/2026: leiaute das matrizes RQ.61 das médicas — a
    # identificação e, abaixo, uma tabela contínua em que cada GHE abre com a faixa
    # azul mesclada. Reversões que matam: (1) voltar a uma tabela por GHE — o corpo
    # sai com 4 tabelas; (2) tirar `_aplicar_fundo` da faixa — sem cor; (3) não mesclar
    # a faixa — a 2ª célula da linha deixa de ser a mesma.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matrizes = [
        MatrizGHE(ghe_id=f"GHE-0{n}", linhas=[_exame("exame_clinico")], cargos=(c,))
        for n, c in ((1, "A"), (2, "B"), (3, "C"))
    ]
    reaberto = _docx(tmp_path, montar_documento(matrizes, vocab, _cabecalho(), _rodape()))

    assert len(reaberto.tables) == 2
    faixas = [linha for linha in reaberto.tables[1].rows if linha.cells[0].text.startswith("GHE ")]
    assert [f.cells[0].text for f in faixas] == ["GHE 01", "GHE 02", "GHE 03"]
    assert all(_fundo(f.cells[0]) == _COR_FAIXA_GHE_HEX for f in faixas)
    assert all(f.cells[0]._tc is f.cells[1]._tc for f in faixas)


def test_docx_celula_de_exames_preserva_quebra_por_exame(tmp_path: Path) -> None:
    # Reversão que mata: juntar os exames com ", ".join(...) num parágrafo só
    # em vez de um add_paragraph() por exame -> a célula teria 1 parágrafo
    # para N exames, não N. Este é o teste que discrimina de verdade: um
    # emissor ingênuo passaria em "uma tabela por GHE" e erraria aqui.
    vocab = {
        "exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1},
        "audiometria": {"nome_exibicao": "Audiometria", "ordem_exibicao": 2},
        "hemograma": {"nome_exibicao": "Hemograma", "ordem_exibicao": 3},
    }
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[_exame("exame_clinico"), _exame("audiometria"), _exame("hemograma")],
        cargos=("Carpinteiro",),
    )
    doc = montar_documento([matriz], vocab, _cabecalho(), _rodape())

    destino = tmp_path / "matriz.docx"
    renderizar_docx(doc, destino)

    reaberto = DocxDocument(str(destino))
    tabela = reaberto.tables[1]
    celula_exames = tabela.rows[2].cells[1]
    assert len(celula_exames.paragraphs) == 3
    textos = [p.text for p in celula_exames.paragraphs]
    assert textos[0].startswith("Exame Clínico")
    assert textos[1].startswith("Audiometria")
    assert textos[2].startswith("Hemograma")


# ---------------------------------------------------------------------------
# D-ARQ-73, emenda de 07/10/2026 — leiaute das matrizes RQ.61 das médicas
# (Vila Brasil 24/09, T65 24/09, Engeseg 22/09, Varandas 16/09/2026), sem o logo
# da empresa. Substitui o estilo verde portado do legado; conteúdo inalterado.
# ---------------------------------------------------------------------------


def test_docx_tabelas_usam_estilo_com_borda(tmp_path: Path) -> None:
    # Reversão que mata: tirar `tabela.style = "Table Grid"` da identificação ou da
    # tabela dos GHEs -> volta ao estilo default do python-docx (sem borda visível).
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("A",))
    reaberto = _docx(tmp_path, montar_documento([matriz], vocab, _cabecalho(), _rodape()))

    assert [t.style.name for t in reaberto.tables] == ["Table Grid", "Table Grid"]


def test_docx_cabecalho_de_coluna_em_negrito_sem_fundo(tmp_path: Path) -> None:
    # Como no modelo: FUNÇÃO | EXAMES SOLICITADOS em negrito, centralizado, sem cor.
    # Reversões que matam: (1) voltar o fundo verde e o texto branco do legado; (2)
    # tirar o negrito.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("A",))
    reaberto = _docx(tmp_path, montar_documento([matriz], vocab, _cabecalho(), _rodape()))

    cabecalho_colunas = reaberto.tables[1].rows[1].cells
    assert [c.text for c in cabecalho_colunas] == ["FUNÇÃO", "EXAMES SOLICITADOS"]
    for celula in cabecalho_colunas:
        assert _fundo(celula) is None
        run = celula.paragraphs[0].runs[0]
        assert run.bold is True
        assert run.font.color.rgb is None


def test_docx_cabecalho_de_pagina_do_rq61(tmp_path: Path) -> None:
    # Cabeçalho repetido em toda página: faixa do sistema da qualidade (sem o logo) e
    # o quadro do título com identificação, página (campos PAGE/NUMPAGES), revisão e
    # versão. Reversões que matam: (1) não chamar `_cabecalho_de_pagina` — o
    # cabeçalho sai vazio; (2) escrever o número da página como texto fixo em vez do
    # campo; (3) tirar o itálico/Arial 16 do título.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("A",))
    reaberto = _docx(tmp_path, montar_documento([matriz], vocab, _cabecalho(), _rodape()))

    cabecalho = reaberto.sections[0].header
    faixa, quadro = cabecalho.tables
    assert faixa.rows[0].cells[0].text == "SISTEMA DE GESTÃO DA QUALIDADE - NBR ISO 9001:2015\nRQ – REGISTRO DA QUALIDADE"
    assert faixa.rows[0].cells[1].text == ""
    # Espaço do logo sem moldura. Reversão que mata: tirar `_sem_bordas(logo)`.
    bordas_logo = faixa.rows[0].cells[1]._tc.tcPr.find(qn("w:tcBorders"))
    assert bordas_logo is not None and bordas_logo.find(qn("w:top")).get(qn("w:val")) == "nil"
    titulo = quadro.cell(0, 0)
    assert titulo.text == TITULO_MATRIZ and titulo._tc is quadro.cell(1, 0)._tc
    run = titulo.paragraphs[0].runs[0]
    assert (run.bold, run.italic, run.font.name, run.font.size) == (True, True, "Arial", Pt(16))
    assert [quadro.cell(0, 1).text, quadro.cell(1, 1).text, quadro.cell(1, 2).text] == [
        "Identificação:\nRQ.61", "Revisão:\n20/10/2024", "Versão:\n06",
    ]
    campos = [c.get(qn("w:instr")) for c in quadro.cell(0, 2)._tc.iter(qn("w:fldSimple"))]
    assert campos == ["PAGE", "NUMPAGES"]


def test_docx_fonte_e_margens_do_modelo(tmp_path: Path) -> None:
    # Calibri 11 no corpo, A4 com as margens do modelo. Reversões que matam: tirar a
    # fonte do estilo Normal (volta ao tema do python-docx); voltar margens de 2 cm.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("A",))
    reaberto = _docx(tmp_path, montar_documento([matriz], vocab, _cabecalho(), _rodape()))

    normal = reaberto.styles["Normal"]
    assert (normal.font.name, normal.font.size) == ("Calibri", Pt(11))
    secao = reaberto.sections[0]
    assert (round(secao.top_margin.cm, 2), round(secao.bottom_margin.cm, 2)) == (1.35, 1.2)


# ---------------------------------------------------------------------------
# 003.EP fatia 3 — e2e real: PDF Fascino -> parse determinístico -> hidratação
# -> processar_arquivo_pgr -> montar_documento. Fecha o critério de pronto do
# S2 (D-ARQ-65 fatia 1/2, 003.EP): os 41 cargos (não mais 19 células
# combinadas) têm de sobreviver até a estrutura que o emissor HTML/DOCX
# consome — as fatias 1-2 mediram só até GHEVerbatim, nunca até aqui.
# ---------------------------------------------------------------------------

_MATRIZES_DIR = Path(__file__).parent.parent.parent / "matrizes_originais"
_PDF_FASCINO = (
    _MATRIZES_DIR / "PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"
)
_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

requer_pdfs = pytest.mark.skipif(
    not _PDF_FASCINO.exists(),
    reason="PDF Fascino ausente; harness integração e2e (003.EP fatia 3) indisponível",
)


class _TranscritorGHENuncaChamado:
    """Cliente-bomba (molde MockTranscritorGHENuncaChamado, test_orquestracao_pgr.py):
    a rota determinística (D-ARQ-65) tem que ser aceita para o Fascino sem
    invocar LLM — falha alto e explícito em vez de mascarar em silêncio uma
    invocação indevida."""

    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise AssertionError("cliente LLM GHE não deveria ser invocado — rota determinística aceita")


class _TranscritorCardNuncaChamado:
    """Dummy para a rota ghe (molde MockTranscritorCardNuncaChamado): se
    processar_arquivo_pgr chamar cliente_card fora da rota card, é bug de
    roteamento."""

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        raise AssertionError("cliente_card não deveria ser invocado na rota ghe")


@requer_pdfs
def test_pipeline_real_fascino_ate_documento_41_linhas_cargo() -> None:
    protocolo = carregar(_PROTOCOLO_DIR)
    envelope = EnvelopeConfirmado(validade=date.today(), assinatura_engenheiro=True)

    inicio = time.monotonic()
    resultado, _pendencias = processar_arquivo_pgr(
        _PDF_FASCINO,
        protocolo,
        _TranscritorGHENuncaChamado(),
        _TranscritorCardNuncaChamado(),
        envelope=envelope,
    )
    assert resultado is not None

    doc = montar_documento(
        resultado.matrizes, protocolo.vocabulario.exames, _cabecalho(), _rodape()
    )
    duracao = time.monotonic() - inicio
    if duracao > 150:
        print(f"AVISO 003.EP fatia 3: pipeline e2e Fascino levou {duracao:.1f}s (> 150s)")

    total_linhas_cargo = sum(len(bloco.linhas) for bloco in doc.blocos)
    assert total_linhas_cargo == 41

    cargos_extraidos = {linha.cargo for bloco in doc.blocos for linha in bloco.linhas}
    for cargo_recuperado in (
        "Encarregado de Pintor",
        "Encarregado de Carpinteiro",
        "Supervisor de Instalações Elétricas",
        "Auxiliar de Obra",
        "Aprendiz Administrativo de Obra",
        "Assistente Administrativo de Obras",
    ):
        assert cargo_recuperado in cargos_extraidos

    assert all(linha.cargo != "" for bloco in doc.blocos for linha in bloco.linhas)


# Vila Brasil GHE 23: o PDF imprime "MANUTENÇÃO - ENERGIZADA", mas o hífen da
# fonte Inter-Thin sai do pdfplumber como NUL.
_NOME_GHE_23 = "ASSISTENCIA TECNICA MANUTENÇÃO \x00 ENERGIZADA"


@pytest.mark.parametrize(
    ("nome", "exibido"),
    [
        # Reversão que mata: voltar a só remover o NUL — "MANUTENÇÃO  ENERGIZADA".
        (_NOME_GHE_23, "ASSISTENCIA TECNICA MANUTENÇÃO - ENERGIZADA"),
        # Reversão que mata: trocar todo NUL por hífen — NUL colado em texto não
        # tem glifo conhecido (é parêntese no CBO "\x004121\x0005\x00").
        ("INSTALAÇÕES HIDRO\x00SANITÁRIAS", "INSTALAÇÕES HIDROSANITÁRIAS"),
    ],
)
def test_nome_ghe_exibicao(nome: str, exibido: str) -> None:
    assert nome_ghe_exibicao(nome) == exibido


def test_docx_mostra_hifen_no_nome_do_ghe_com_nul(tmp_path: Path) -> None:
    # Reversões que matam: (1) montar_documento usar _sanitizar no nome — o
    # título sai "MANUTENÇÃO  ENERGIZADA"; (2) passar o nome verbatim — o
    # python-docx recusa o NUL (ValueError) e o download do Vila Brasil quebra.
    matriz = MatrizGHE(
        ghe_id="GHE 23", linhas=[_exame("exame_clinico")], nome_ghe=_NOME_GHE_23, cargos=("Eletricista",)
    )
    doc = montar_documento([matriz], carregar(_PROTOCOLO_DIR).vocabulario.exames, _cabecalho(), _rodape())
    destino = tmp_path / "matriz.docx"
    renderizar_docx(doc, destino)

    texto = "\n".join(c.text for t in DocxDocument(str(destino)).tables for r in t.rows for c in r.cells)
    assert "ASSISTENCIA TECNICA MANUTENÇÃO - ENERGIZADA" in texto


# DT-(sessão claude/keen-curie-xdm7kb)-03, forma do documento: título do RQ.61 e
# código do GHE uma vez só (T65: "GHE GHE-01 GHE 01 - ENGENHARIA/PRODUÇÃO").

_VOCAB_CLINICO = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}


def _documento_t65(tipo: str = "Atualização") -> object:
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        nome_ghe="GHE 01 - ENGENHARIA/PRODUÇÃO",
        linhas=[_exame("exame_clinico")],
        cargos=("Engenheiro Civil",),
    )
    cabecalho = CabecalhoDocumento("E", "O", tipo, "01/10/2026", "Dra. Teste", "CRM-GO 0000")
    return montar_documento([matriz], _VOCAB_CLINICO, cabecalho, _rodape())


def test_html_tem_titulo_rq61_e_tipo_em_linha_propria() -> None:
    # Reversões que matam: (1) tirar o <h1> do TITULO_MATRIZ — a matriz volta a
    # sair sem o título do formulário; (2) imprimir o tipo cru, sem o rótulo
    # "Tipo:" — o texto digitado volta a parecer título.
    saida = renderizar_html(_documento_t65())  # type: ignore[arg-type]

    assert f"<h1>{TITULO_MATRIZ}</h1>" in saida
    assert "<p>Tipo: Atualização</p>" in saida


def _identificacao(tmp_path: Path, documento: object) -> list[list[str]]:
    tabela = _docx(tmp_path, documento).tables[0]
    return [[c.text for c in linha.cells] for linha in tabela.rows]


def test_docx_tipo_marca_a_opcao_do_rq61(tmp_path: Path) -> None:
    # O tipo digitado marca (X) uma das quatro opções do formulário, como o modelo;
    # o título segue o do RQ.61. Reversões que matam: (1) não marcar o X; (2) casar
    # com acento — "atualizacao" digitado não marcaria.
    linhas = _identificacao(tmp_path, _documento_t65(tipo="atualizacao"))

    assert linhas[0][2] == "Obra Nova (  )      Atualização (X)\nAdendo (  )      Funções Iniciais (  )"
    assert linhas[0][0] == "Empresa:\nE"
    assert linhas[1][0] == "Obra: O" and linhas[1][2] == "Data: 01/10/2026"


def test_docx_tipo_fora_das_opcoes_nao_some(tmp_path: Path) -> None:
    # D-ARQ-22: texto que não casa com nenhuma opção sai como "Outro:". Reversão que
    # mata: tirar o ramo `marcado is None` — o tipo digitado some do documento.
    linhas = _identificacao(tmp_path, _documento_t65(tipo="Revisão anual"))

    assert "(X)" not in linhas[0][2]
    assert linhas[0][2].endswith("Outro: Revisão anual")


def test_tipo_vazio_nao_gera_linha_sem_valor(tmp_path: Path) -> None:
    # Reversões que matam: emitir "Tipo:" no HTML sem a condição; no Word, tratar o
    # vazio como "Outro:" (rótulo sem valor) ou marcar uma opção.
    documento = _documento_t65(tipo="  ")

    assert "Tipo:" not in renderizar_html(documento)  # type: ignore[arg-type]
    tipos = _identificacao(tmp_path, documento)[0][2]
    assert "(X)" not in tipos and "Outro" not in tipos


def test_cabecalho_do_ghe_nao_repete_o_codigo(tmp_path: Path) -> None:
    # Reversões que matam: voltar a `f"GHE {ghe_id} {nome_ghe}"` no HTML ou no Word —
    # sai "GHE GHE-01 GHE 01 - ENGENHARIA/PRODUÇÃO"; usar `titulo_ghe` no Word — sai
    # "GHE-01 — …", fora da grafia do modelo ("GHE 01 - …").
    documento = _documento_t65()

    assert "<h2>GHE-01 — ENGENHARIA/PRODUÇÃO</h2>" in renderizar_html(documento)  # type: ignore[arg-type]
    faixa = _docx(tmp_path, documento).tables[1].rows[0].cells[0]
    assert faixa.text == "GHE 01 - ENGENHARIA/PRODUÇÃO"


def test_titulo_tira_o_numero_do_ghe_escrito_sem_a_palavra_ghe() -> None:
    # Vila Brasil escritório (08/10/2026): o PGR chama o GHE de "01 - ADMINISTRAÇÃO 01" e
    # saía "GHE 01 - 01 - ADMINISTRAÇÃO 01". Reversões que matam: (1) tirar o 2º `re.sub`
    # de `_nome_sem_codigo` (o número fica); (2) aceitar o número sem hífen ("10 PAVIMENTOS"
    # perde o "10"); (3) não comparar com o número do GHE ("10 - X" no GHE-01 perde o "10").
    assert titulo_ghe_rq61("GHE-01", "01 - ADMINISTRAÇÃO 01") == "GHE 01 - ADMINISTRAÇÃO 01"
    assert titulo_ghe("GHE-01", "01 - ADMINISTRAÇÃO 01") == "GHE-01 — ADMINISTRAÇÃO 01"
    assert titulo_ghe_rq61("GHE-10", "10 PAVIMENTOS") == "GHE 10 - 10 PAVIMENTOS"
    assert titulo_ghe_rq61("GHE-01", "10 - X") == "GHE 01 - 10 - X"


def test_rodape_sai_com_os_rotulos_do_rq61(tmp_path: Path) -> None:
    # DT-(sessão claude/keen-curie-xdm7kb)-03, rodapé. Reversões que matam: voltar a
    # emitir só o valor, sem rótulo, no HTML ou no Word — três linhas soltas que a
    # médica não sabe a que se referem (T65 em produção, 01/10/2026).
    documento = _documento_t65()
    destino = tmp_path / "matriz.docx"
    renderizar_docx(documento, destino)  # type: ignore[arg-type]

    esperado = [
        "Responsável pelo preenchimento: Teste",
        "Médico(a) Responsável pela validação: Dra. Teste",
        "Data do PGR: 01/01/2026",
    ]
    saida = renderizar_html(documento)  # type: ignore[arg-type]
    assert all(f"<p>{linha}</p>" in saida for linha in esperado)
    rodape = DocxDocument(str(destino)).paragraphs[-3:]
    assert [p.text for p in rodape] == esperado
    # Negrito, como no modelo. Reversão que mata: escrever o rodapé sem negrito.
    assert all(run.bold for p in rodape for run in p.runs)


def test_rodape_em_branco_mantem_o_rotulo() -> None:
    # Gabaritos ENGESEG 24.04.25: "Médico(a) Responsável pela validação:" em branco,
    # para preencher à mão. Reversão que mata: omitir a linha quando o valor é vazio.
    assert RodapeDocumento("", "", "").linhas() == (
        "Responsável pelo preenchimento:",
        "Médico(a) Responsável pela validação:",
        "Data do PGR:",
    )


@pytest.mark.parametrize(
    "medico,crm,esperado",
    [
        ("DRA. PATRÍCIA", "14949", "Médico(a) Coordenador(a) do PCMSO: DRA. PATRÍCIA — CRM 14949"),
        ("DRA. PATRÍCIA", "CRM-GO 14.949", "Médico(a) Coordenador(a) do PCMSO: DRA. PATRÍCIA — CRM-GO 14.949"),
        ("", "", "Médico(a) Coordenador(a) do PCMSO:"),
    ],
)
def test_linha_do_coordenador_tem_rotulo_e_crm(medico: str, crm: str, esperado: str) -> None:
    # DT-(sessão claude/keen-curie-xdm7kb)-03, cabeçalho. Reversões que matam: (1) tirar
    # o rótulo — volta "DRA. X | 14949" (T65 em produção); (2) prefixar "CRM" sempre —
    # o 2º caso vira "CRM CRM-GO"; (3) não prefixar — o 1º sai com o número solto.
    assert CabecalhoDocumento("E", "O", "", "", medico, crm).linha_coordenador() == esperado


def test_html_e_word_trazem_coordenador_e_crm(tmp_path: Path) -> None:
    # Reversões que matam: voltar a f"{medico} | {crm}" no HTML; no Word, imprimir o
    # CRM cru — "14949" sem o prefixo.
    documento = _documento_t65()
    linha = "Médico(a) Coordenador(a) do PCMSO: Dra. Teste — CRM-GO 0000"
    assert f"<p>{linha}</p>" in renderizar_html(documento)  # type: ignore[arg-type]

    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[_exame("exame_clinico")], cargos=("A",))
    cabecalho = CabecalhoDocumento("E", "O", "", "", "DRA. PATRÍCIA", "14949")
    coordenador = _identificacao(tmp_path, montar_documento([matriz], _VOCAB_CLINICO, cabecalho, _rodape()))[2]
    assert coordenador[0] == "Médico(a) Coordenador(a) do PCMSO"
    assert coordenador[1] == "DRA. PATRÍCIA\nCRM 14949"


# D-ARQ-73, nota de 01/10/2026 (decisão do Diovanni): ordem e nomes medidos em 32
# gabaritos de matriz de 2026.

_EXAMES_REAIS = carregar(Path(__file__).parent.parent / "protocolo").vocabulario.exames


def test_indicador_biologico_fica_entre_os_laboratoriais_e_espirometria_rx_e_avaliacoes() -> None:
    # Reversões que matam: (1) ignorar `bloco_exibicao` na chave — o MEK volta para
    # depois do RX, onde nenhum gabarito o põe; (2) devolver Saúde Mental/Psicossocial
    # para antes de Espirometria/RX no exames.yaml (ordem do SPE 0030); (3) inverter
    # Saúde Mental e Psicossocial no exames.yaml.
    matriz = MatrizGHE(
        ghe_id="GHE-11",
        linhas=[
            _exame(slug)
            for slug in (
                "avaliacao_psicossocial",
                "rx_torax_oit",
                "mek_urina",
                "avaliacao_saude_mental",
                "espirometria",
                "ecg",
                "exame_clinico",
            )
        ],
        cargos=("Encanador",),
    )
    (bloco,) = montar_documento([matriz], _EXAMES_REAIS, _cabecalho(), _rodape()).blocos
    nomes = [celula.split(" (")[0] for celula in bloco.linhas[0].celulas]
    assert nomes == [
        "Exame Clínico",
        "ECG",
        "Metil-etil-cetona",
        "Espirometria",
        "RX de Tórax OIT",
        "Av. Médica de Saúde Mental",
        "Avaliação Psicossocial",
    ]


@pytest.mark.parametrize(
    "slug,nome",
    [
        ("rx_torax_oit", "RX de Tórax OIT"),
        ("carboxihemoglobina", "Carboxihemoglobina"),
        ("rx_coluna_lombo_sacra", "RX de Coluna Lombo-Sacra"),
    ],
)
def test_nome_de_exibicao_segue_a_grafia_majoritaria_dos_gabaritos(slug: str, nome: str) -> None:
    # Reversão que mata cada caso: voltar o nome_exibicao do slug em exames.yaml
    # ("RX Tórax OIT", "Carboxihemoglobina no sangue", "RX Coluna Lombo-Sacra").
    assert _EXAMES_REAIS[slug]["nome_exibicao"] == nome
