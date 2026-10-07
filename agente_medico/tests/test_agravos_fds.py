"""D-ARQ-92 fatia 1 — agravos à saúde (frases H3xx) lidos da FDS, só exibição. Cada
teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.extracao_fds import extrair_agravos_saude, extrair_agravos_saude_pdf
from agente_medico.motor.tipos import FraseH
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
