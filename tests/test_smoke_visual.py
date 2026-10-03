"""Avaliação do smoke visual (scripts/smoke_visual.py) sem navegador.

A medição precisa de Chromium e fica fora da suíte; a avaliação é função pura
sobre as medidas e é aqui que se trava o que ela acusa. Cada teste parte de
medidas boas, estraga UM aspecto e exige a falha correspondente — e carrega a
reversão de `avaliar` que o deixa vermelho.
"""

from __future__ import annotations

import copy
from typing import Any

import pytest

from agente_medico.superficie import estilos
from scripts.smoke_visual import CENARIOS, ESPERADO_NO_CENARIO, avaliar, rgb


def _passo(key: str, topo: float, cor: str) -> dict[str, Any]:
    return {"key": key, "topo": topo, "base": topo + 58, "texto_topo": topo + 17,
            "texto_base": topo + 41, "cor_topo": rgb(cor)}


def _medidas_ok(cenario: str) -> dict[str, Any]:
    estados = {
        "inicial": ("ativo", "pendente"),
        "bloqueio": ("bloqueado", "pendente"),
        "matriz": ("concluido", "concluido"),
    }[cenario]
    cor = {"ativo": estilos.PRIMARIA, "bloqueado": estilos.ERRO,
           "pendente": estilos.BORDA, "concluido": estilos.SUCESSO}
    passos = [
        _passo(f"passo_1_{estados[0]}", 100, cor[estados[0]]),
        _passo("passo_2_opcional", 100, estilos.ACENTO),
        _passo(f"passo_3_{estados[1]}", 100, cor[estados[1]]),
        _passo(f"passo_4_{estados[1]}", 100, cor[estados[1]]),
    ]
    matriz = cenario == "matriz"
    return {
        "css_aplicado": True,
        "fonte_status": 200,
        "inter_carregada": True,
        "familia_texto": 'Inter, "Source Sans", sans-serif',
        "hosts_externos": [],
        "passos": passos,
        "faixa": {"fundo": "linear-gradient(120deg, ...)", "folga_topo": 22.0, "folga_base": 22.0},
        "cards": [{"key": "etapa_pgr", "sombra": "rgba(0,0,0,.06) 0px 1px 2px", "raio": 12.0}],
        "dropzones": ["dashed", "dashed"],
        "botoes": [{"rotulo": "Gerar matriz", "altura": 44.0}, {"rotulo": "Upload", "altura": 44.0}],
        "downloads": [{"rotulo": f"d{i}", "largura": 349.0, "coluna": 349.0} for i in range(3)] if matriz else [],
        "alertas": [{"tipo": "stAlertContentError", "borda": rgb(estilos.ERRO)}] if cenario == "bloqueio" else [],
    }


def _falhas_com(cenario: str, alterar: Any) -> list[str]:
    medidas = copy.deepcopy(_medidas_ok(cenario))
    alterar(medidas)
    return avaliar(medidas, cenario)


@pytest.mark.parametrize("cenario", CENARIOS)
def test_medidas_boas_nao_geram_falha(cenario: str) -> None:
    # Reversão que mata: inverter qualquer condição de `avaliar` (ex.:
    # `if medidas["css_aplicado"]:`) — falso alarme num app saudável faz o
    # smoke ser ignorado, que é pior que não tê-lo.
    assert avaliar(_medidas_ok(cenario), cenario) == []


def test_css_ausente_falha() -> None:
    # Reversão que mata: remover a checagem de `css_aplicado` em `avaliar`.
    # Caso real: `<p>` num comentário do CSS — o DOMPurify descarta o <style>.
    falhas = _falhas_com("inicial", lambda m: m.update(css_aplicado=False))
    assert any("CSS do app ausente" in f for f in falhas)


def test_requisicao_a_terceiro_falha() -> None:
    # Reversão que mata: remover a checagem de `hosts_externos` em `avaliar`.
    falhas = _falhas_com("inicial", lambda m: m.update(hosts_externos=["fonts.googleapis.com"]))
    assert any("fonts.googleapis.com" in f for f in falhas)


def test_fonte_fora_da_inter_falha() -> None:
    # Reversão que mata: remover a checagem de `familia_texto` em `avaliar`.
    falhas = _falhas_com("inicial", lambda m: m.update(familia_texto='"Source Sans", sans-serif'))
    assert any("não está em Inter" in f for f in falhas)


def test_passos_com_alturas_diferentes_falham() -> None:
    # Reversão que mata: remover a comparação de alturas do stepper — o caso do
    # passo "(opcional)" com duas linhas mais alto que os outros.
    def alterar(m: dict[str, Any]) -> None:
        m["passos"][1]["base"] += 4

    assert any("alturas diferentes" in f for f in _falhas_com("inicial", alterar))


def test_texto_vazando_do_passo_falha() -> None:
    # Reversão que mata: remover a checagem texto-dentro-da-caixa — o caso real
    # do mobile com `min-height: 0` (caixa de 27 px, texto de 24 px deslocado).
    def alterar(m: dict[str, Any]) -> None:
        m["passos"][0]["texto_base"] = m["passos"][0]["base"] + 7

    assert any("texto vaza da caixa" in f for f in _falhas_com("inicial", alterar))


def test_cor_do_passo_que_contradiz_o_estado_falha() -> None:
    # Reversão que mata: remover a checagem de `cor_topo` — passo bloqueado com
    # a cor de "ativo" (a regra `_bloqueado` do CSS deixou de casar).
    def alterar(m: dict[str, Any]) -> None:
        m["passos"][0]["cor_topo"] = rgb(estilos.PRIMARIA)

    assert any("passo_1_bloqueado: cor" in f for f in _falhas_com("bloqueio", alterar))


def test_cenario_nao_atingido_falha() -> None:
    # Reversão que mata: remover o laço sobre ESPERADO_NO_CENARIO — um cenário
    # de bloqueio que não bloqueou passaria medindo a tela inicial.
    def alterar(m: dict[str, Any]) -> None:
        m["passos"][0]["key"] = "passo_1_ativo"
        m["passos"][0]["cor_topo"] = rgb(estilos.PRIMARIA)

    falhas = _falhas_com("bloqueio", alterar)
    assert any("não atingido" in f for f in falhas)
    assert ESPERADO_NO_CENARIO["bloqueio"] == ("passo_1_bloqueado",)


def test_titulo_fora_do_centro_da_faixa_falha() -> None:
    # Reversão que mata: remover a comparação de folgas da faixa — o caso real da
    # margem negativa do stMarkdownContainer (título colado embaixo).
    def alterar(m: dict[str, Any]) -> None:
        m["faixa"]["folga_base"] = 6.0

    assert any("fora do centro" in f for f in _falhas_com("inicial", alterar))


def test_download_mais_estreito_que_a_coluna_falha() -> None:
    # Reversão que mata: remover a checagem de largura dos downloads — o caso real
    # do `width: 100%` sem efeito (111 px numa coluna de 349 px).
    def alterar(m: dict[str, Any]) -> None:
        m["downloads"][0]["largura"] = 111.0

    assert any("numa coluna de 349px" in f for f in _falhas_com("matriz", alterar))


def test_botoes_com_alturas_diferentes_falham() -> None:
    # Reversão que mata: remover a comparação de alturas dos botões — download
    # 46 px ao lado de "Anexar" 42 px.
    def alterar(m: dict[str, Any]) -> None:
        m["botoes"][0]["altura"] = 48.0

    assert any("botões com alturas diferentes" in f for f in _falhas_com("inicial", alterar))


@pytest.mark.parametrize(
    ("tipo", "cor_errada"),
    [
        ("stAlertContentSuccess", "rgb(21, 130, 55)"),
        ("stAlertContentWarning", "rgb(146, 108, 5)"),
        ("stAlertContentError", "rgb(189, 64, 67)"),
        ("stAlertContentInfo", "rgb(0, 84, 163)"),
    ],
)
def test_alerta_com_cor_padrao_do_streamlit_falha(tipo: str, cor_errada: str) -> None:
    # Reversão que mata: remover a checagem de cor dos alertas. As cores erradas
    # são as padrão do Streamlit, medidas quando o :has() da paleta não pegava.
    # Sucesso, aviso e info não aparecem nos 3 cenários do smoke: este teste é
    # a única trava deles.
    def alterar(m: dict[str, Any]) -> None:
        m["alertas"].append({"tipo": tipo, "borda": cor_errada})

    assert any(f"alerta {tipo}" in f for f in _falhas_com("bloqueio", alterar))


def test_rgb_converte_hex_no_formato_do_navegador() -> None:
    # Reversão que mata: trocar a ordem dos canais em `rgb` — toda comparação de
    # cor do smoke passaria a falhar num app correto.
    assert rgb("#0F4C5C") == "rgb(15, 76, 92)"
