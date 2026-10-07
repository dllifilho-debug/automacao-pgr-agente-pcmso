"""D-ARQ-92 fatia 1 — agravos à saúde (frases H3xx) lidos da FDS, só exibição. Cada
teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from agente_medico.motor.extracao_fds import extrair_agravos_saude, extrair_agravos_saude_pdf
from agente_medico.motor.tipos import FDS, GHEPGR, PGR, FraseH, MatrizGHE, ProdutoQuimico
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    TITULO_AGRAVOS,
    agravos_do_ghe,
    montar_memorial,
    renderizar_memorial_docx,
)
from agente_medico.superficie.relatorio_aso import montar_relatorio_aso, renderizar_relatorio_aso_docx
from agente_medico.superficie import web_matriz
from agente_medico.superficie.web_matriz import (
    AVISO_SEM_AGRAVOS,
    extrair_agravos_cacheado,
    linhas_agravos,
    pagina_matriz,
)

_AGUARRAS = Path(__file__).resolve().parents[2] / "fds_originais" / "fispq-quim-sol-alif-aguarras-mineral.pdf"


def _textos(*paginas: str) -> dict[str, str]:
    return {f.codigo: f.texto for f in extrair_agravos_saude(paginas)}


def test_formatos_de_separador_do_acervo() -> None:
    # Reversão: remover `_SEPARADOR_INICIAL.sub` de `_texto_apos` — o texto começa por
    # ":" ou "–", não por maiúscula, e as frases saem vazias.
    textos = _textos(
        "- H319: Provoca irritação ocular grave.\n"
        "H303 – Pode ser nocivo se ingerido\n"
        "H335 - Pode provocar irritação das vias respiratórias."
    )
    assert textos == {
        "H303": "Pode ser nocivo se ingerido",
        "H319": "Provoca irritação ocular grave.",
        "H335": "Pode provocar irritação das vias respiratórias.",
    }


def test_so_frases_de_saude_h3xx() -> None:
    # Reversão: trocar `(3\d{2})` por `(\d{3})` em `_CODIGO_H_SAUDE` — perigo físico
    # (H226) e ambiental (H400) entram como agravo à saúde.
    textos = _textos("H226 Líquido e vapores inflamáveis.\nH400 Muito tóxico para os organismos aquáticos.\nH315 Provoca irritação à pele.")
    assert list(textos) == ["H315"]


def test_outra_coluna_fundida_na_linha_fica_fora() -> None:
    # Reversão: remover o corte em `_FIM_DE_FRASE` — o texto leva junto a outra coluna
    # do PDF ("Lave com água e sabão.").
    textos = _textos("- Número ONU: UN 1133. - H315: Provoca irritação à pele. Lave com água e sabão.")
    assert textos == {"H315": "Provoca irritação à pele."}


def test_duas_frases_na_mesma_linha_nao_se_misturam() -> None:
    # Reversão: remover o corte no próximo código H (`seguinte`) — a frase do H302
    # engole a do H312.
    textos = _textos("H302 Nocivo se ingerido H312 Nocivo em contato com a pele")
    assert textos == {"H302": "Nocivo se ingerido", "H312": "Nocivo em contato com a pele"}


def test_entre_ocorrencias_vale_a_completa() -> None:
    # Reversão: escolher a primeira ocorrência (`opcoes[0]`) em vez do `max(...)` —
    # sai a frase cortada "Pode provocar".
    textos = _textos("H317 Pode provocar\n", "Frases de perigo: H317 Pode provocar reações alérgicas na pele.")
    assert textos == {"H317": "Pode provocar reações alérgicas na pele."}


def test_codigo_sem_texto_aparece_e_ordem_crescente() -> None:
    # Reversão: descartar código sem texto (`if opcoes` no gerador) — o H351, só listado,
    # some (D-ARQ-22).
    frases = extrair_agravos_saude(["Classificação: H351, H302.", "H302 Nocivo se ingerido."])
    assert frases == (FraseH("H302", "Nocivo se ingerido."), FraseH("H351", ""))


def test_frase_quebrada_nao_junta_a_linha_seguinte() -> None:
    # Reversão: juntar a linha seguinte quando ela começa em minúscula — volta o
    # resíduo de coluna medido no acervo ("…de asma ou for fácil.").
    textos = _textos("H334 Quando inalado pode provocar sintomas alérgicos, de asma ou\nfor fácil. Caso a irritação persista")
    assert textos == {"H334": "Quando inalado pode provocar sintomas alérgicos, de asma ou"}


def test_fds_real_aguarras_le_a_secao_2() -> None:
    # Reversão: ler só a região de composição (`extrair_texto_fds`) em
    # `extrair_agravos_saude_pdf` — no aguarrás os H estão na seção 2 e nada sai.
    frases = extrair_agravos_saude_pdf(_AGUARRAS)
    assert [f.codigo for f in frases] == ["H304", "H315", "H320", "H335", "H336", "H373"]
    assert FraseH("H315", "Provoca irritação à pele.") in frases


def test_tela_sem_frase_mostra_aviso() -> None:
    # Reversão: `linhas_agravos` devolver `()` sem frase — a FDS sem H3xx some calada.
    assert linhas_agravos(()) == (AVISO_SEM_AGRAVOS,)
    assert linhas_agravos((FraseH("H351", ""),)) == ("- H351 (texto não legível na FDS)",)


def test_cache_pelo_conteudo_nao_rele_o_pdf(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    # Reversão: tirar o `if chave not in cache` de `extrair_agravos_cacheado` — o PDF é
    # relido a cada rerun.
    chamadas: list[Path] = []

    def _falso(caminho: Path) -> tuple[FraseH, ...]:
        chamadas.append(caminho)
        return (FraseH("H315", "Provoca irritação à pele."),)

    monkeypatch.setattr(web_matriz, "extrair_agravos_saude_pdf", _falso)
    cache: dict[str, tuple[FraseH, ...]] = {}
    for _ in range(2):
        assert extrair_agravos_cacheado(tmp_path / "f.pdf", b"mesmo conteudo", cache)[0].codigo == "H315"
    assert len(chamadas) == 1


def test_pdf_ilegivel_nao_derruba_a_tela(tmp_path: Path) -> None:
    # Reversão: tirar o `try/except PdfminerException` de `extrair_agravos_cacheado` —
    # o PdfminerException sobe e a tela da FDS cai (os testes de tela com FDS falsa caíram
    # assim, 25 falhas medidas em 07/10/2026).
    caminho = tmp_path / "f.pdf"
    caminho.write_bytes(b"conteudo qualquer")
    cache: dict[str, tuple[FraseH, ...]] = {}
    assert extrair_agravos_cacheado(caminho, b"conteudo qualquer", cache) == ()


def test_tela_da_fds_mostra_os_agravos(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão: remover o bloco "Agravos à saúde" do expander da FDS em pagina_matriz —
    # as frases não aparecem na tela.
    monkeypatch.setattr(web_matriz, "preparar_composicao_cacheada", lambda *a, **k: ((), ()))
    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[1].set_value([(_AGUARRAS.name, _AGUARRAS.read_bytes(), "application/pdf")]).run()

    assert not at.exception
    texto = "\n".join(el.value for el in at.markdown)
    assert "Agravos à saúde" in texto
    assert "H315 — Provoca irritação à pele." in texto


_AGRAVOS_AGUARRAS = (
    FraseH("H304", "Pode ser fatal se ingerido e penetrar nas vias respiratórias."),
    FraseH("H351", ""),
)


def _ghe(*produtos: ProdutoQuimico) -> GHEPGR:
    return GHEPGR(
        id="GHE-01", nome="PINTURA", cargos=("Pintor",), riscos=(), epis=(),
        produtos_quimicos=produtos, psicossocial=False,
    )


def test_agravo_em_texto_com_codigo_entre_parenteses() -> None:
    # Reversões: inverter para "código — texto" (o agravo deixa de vir primeiro);
    # tirar o ramo de FDS sem frase (o produto vinculado some calado, D-ARQ-22);
    # incluir produto sem FDS (o produto declarado só no PGR viraria linha vazia).
    ghe = _ghe(
        ProdutoQuimico("Aguarrás", FDS(composicao=(), agravos=_AGRAVOS_AGUARRAS)),
        ProdutoQuimico("Cimento", FDS(composicao=())),
        ProdutoQuimico("Óleo do PGR", None),
    )
    assert agravos_do_ghe(ghe) == (
        "Aguarrás: Pode ser fatal se ingerido e penetrar nas vias respiratórias (H304); "
        "H351 (texto não legível na FDS).",
        "Cimento: a FDS não traz frase H de saúde legível — conferir a seção 2.",
    )


def test_agravos_saem_no_memorial_e_no_relatorio_do_aso(tmp_path: Path) -> None:
    # Reversões: não passar `agravos=` em montar_memorial ou em montar_relatorio_aso;
    # remover o bloco `if bloco.agravos` de um dos dois renderizadores.
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(
        _ghe(ProdutoQuimico("Aguarrás", FDS(composicao=(), agravos=_AGRAVOS_AGUARRAS))),
    ))
    matriz = MatrizGHE(ghe_id="GHE-01", nome_ghe="PINTURA", cargos=("Pintor",))
    cab = CabecalhoDocumento("CMO", "AURORA", "Adendo", "2026-10-07", "Dra. X", "CRM")
    memorial = tmp_path / "memorial.docx"
    renderizar_memorial_docx(montar_memorial([matriz], {}, {}, pgr=pgr), cab, memorial)
    aso = tmp_path / "riscos_aso.docx"
    renderizar_relatorio_aso_docx(montar_relatorio_aso([matriz], {}, pgr=pgr), cab, aso)

    for caminho in (memorial, aso):
        paragrafos = [p.text for p in Document(str(caminho)).paragraphs]
        assert TITULO_AGRAVOS in paragrafos
        assert any(p.startswith("Aguarrás: Pode ser fatal se ingerido") for p in paragrafos)


def test_anexar_grava_os_agravos_no_produto_sem_mudar_a_matriz(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões: não passar `agravos_fds` nos `args` do botão Anexar (ou não fazer o
    # `dataclasses.replace(..., agravos=...)` em `_anexar`) — o produto chega sem agravos.
    # A matriz sai igual à do mesmo anexo sem agravos: o motor não lê o campo.
    from agente_medico.tests.test_web_matriz import (
        _FDS_TOLUENO,
        _ghe_pgr,
        _pgr_sintetico,
        _submeter_formulario,
    )

    pgr_sintetico = _pgr_sintetico(_ghe_pgr(ghe_id="GHE-01", nome="Pintura", cargos=("Pintor",)))
    monkeypatch.setattr(web_matriz, "preparar_pgr_hidratado", lambda *a, **k: (pgr_sintetico, ()))
    monkeypatch.setattr(web_matriz, "preparar_composicao", lambda *a, **k: ((_FDS_TOLUENO,), ()))

    def _anexar_com(agravos: tuple[FraseH, ...]) -> tuple[Any, list[MatrizGHE]]:
        monkeypatch.setattr(web_matriz, "extrair_agravos_saude_pdf", lambda caminho: agravos)
        at = AppTest.from_function(pagina_matriz)
        at.run()
        _submeter_formulario(at)
        at.file_uploader[1].set_value([("fds.pdf", b"conteudo qualquer", "application/pdf")]).run()
        at.multiselect(key="ghe_destino_fds.pdf").set_value(["GHE-01"]).run()
        at.button(key="anexar_fds_fds.pdf").click().run()
        assert not at.exception
        cache = at.session_state["web_matriz_cache"]
        return cache.pgr_hidratado.ghes[0].produtos_quimicos[0], list(cache.matrizes)

    produto, matrizes = _anexar_com(_AGRAVOS_AGUARRAS)
    _, matrizes_sem = _anexar_com(())
    assert produto.fds.agravos == _AGRAVOS_AGUARRAS
    assert matrizes == matrizes_sem

