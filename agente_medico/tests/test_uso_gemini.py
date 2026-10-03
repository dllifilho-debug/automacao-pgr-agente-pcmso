"""Consumo de tokens do Gemini: qual modelo respondeu e quanto cada resposta
gastou, somado por processamento de PGR e mostrado na tela. Cada teste nomeia
a reversão que o deixa vermelho."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.adaptadores import transcritor_gemini
from agente_medico.adaptadores.transcritor_gemini import TranscritorGemini, UsoGemini, medir_uso
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Pendencia, PGR, Resultado
from agente_medico.superficie.web_matriz import ResumoUsoIA, pagina_matriz, resumir_uso, texto_uso
from agente_medico.tests.test_web_matriz import _pgr_sintetico, _submeter_formulario

_ALVO = "agente_medico.adaptadores.transcritor_gemini.requests.post"
_FDS_VAZIA: dict[str, list[Any]] = {"blocos": []}


def _resposta_200(
    texto: str,
    finish_reason: str = "STOP",
    uso: dict[str, Any] | None = None,
    modelo: str | None = None,
) -> Mock:
    corpo: dict[str, Any] = {
        "candidates": [{"content": {"parts": [{"text": texto}]}, "finishReason": finish_reason}]
    }
    if uso is not None:
        corpo["usageMetadata"] = uso
    if modelo is not None:
        corpo["modelVersion"] = modelo
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = corpo
    return resp


_USO = {"promptTokenCount": 1200, "candidatesTokenCount": 300, "thoughtsTokenCount": 512, "totalTokenCount": 2012}


def test_registra_modelo_respondido_e_tokens() -> None:
    # Reversões que matam: (1) tirar a chamada a _registrar_uso de
    # _chamar_gemini (lista vazia); (2) gravar o nome PEDIDO no lugar do
    # modelVersion respondido; (3) trocar promptTokenCount/candidatesTokenCount.
    resposta = _resposta_200(json.dumps(_FDS_VAZIA), uso=_USO, modelo="gemini-3.5-flash")
    with patch(_ALVO, return_value=resposta), medir_uso() as registros:
        TranscritorGemini(chave="fake").transcrever("texto")

    assert registros == [UsoGemini(modelo="gemini-3.5-flash", entrada=1200, saida=300, raciocinio=512, cache=0)]


def test_resposta_descartada_tambem_conta() -> None:
    # 1º modelo devolve 200 com MAX_TOKENS (descartado pela cascata), 2º
    # devolve STOP. Os dois consumiram tokens. Reversão que mata: registrar
    # depois do teste de finishReason — só a resposta aceita seria contada.
    descartada = _resposta_200("{", finish_reason="MAX_TOKENS", uso=_USO, modelo="gemini-3.5-flash")
    aceita = _resposta_200(json.dumps(_FDS_VAZIA), uso=_USO, modelo="gemini-2.5-flash")
    with patch(_ALVO, side_effect=[descartada, aceita]), medir_uso() as registros:
        TranscritorGemini(chave="fake").transcrever("texto")

    assert [r.modelo for r in registros] == ["gemini-3.5-flash", "gemini-2.5-flash"]


def test_repeticao_do_lote_por_json_invalido_tambem_conta() -> None:
    # _TENTATIVAS_LOTE: JSON cortado na 1ª resposta, completo na 2ª. Reversão
    # que mata: contar uso no TranscritorGeminiGHE só depois do parse bem
    # sucedido, e não em toda resposta 200 de _chamar_gemini.
    cortada = _resposta_200('[{"nome": "Pin', uso=_USO)
    completa = _resposta_200(json.dumps([{"nome": "Pintura", "cargos": [], "riscos": []}]), uso=_USO)
    with patch(_ALVO, side_effect=[cortada, completa]), medir_uso() as registros:
        TranscritorGeminiGHE(chave="fake").transcrever_lote(["SETOR/FUNÇÃO Pintura"])

    assert len(registros) == 2


def test_resposta_sem_metadados_conta_com_zeros_e_nao_derruba() -> None:
    # Reversões que matam: (1) indexar corpo["usageMetadata"] direto — o
    # KeyError cai no except da cascata, os três modelos "falham" e a
    # transcrição levanta TranscricaoIndisponivel; (2) não registrar a
    # resposta quando falta usageMetadata.
    with patch(_ALVO, return_value=_resposta_200(json.dumps(_FDS_VAZIA))), medir_uso() as registros:
        resultado = TranscritorGemini(chave="fake").transcrever("texto")

    assert resultado == ()
    assert registros == [UsoGemini(modelo="gemini-flash-latest", entrada=0, saida=0, raciocinio=0, cache=0)]


def test_fora_do_bloco_nada_e_coletado() -> None:
    # Reversão que mata: não restaurar o ContextVar no fim de medir_uso — a
    # chamada seguinte, fora do bloco, cairia na lista do processamento antigo.
    with patch(_ALVO, return_value=_resposta_200(json.dumps(_FDS_VAZIA), uso=_USO)):
        with medir_uso() as registros:
            TranscritorGemini(chave="fake").transcrever("texto")
        TranscritorGemini(chave="fake").transcrever("texto")

    assert len(registros) == 1


def test_resumo_soma_e_lista_modelos_na_ordem() -> None:
    # Reversões que matam: (1) guardar só o último registro em vez de somar;
    # (2) modelos via set (ordem instável) ou com repetição.
    registros = [
        UsoGemini("gemini-3.5-flash", 100, 10, 5, 0),
        UsoGemini("gemini-2.5-flash", 200, 20, 0, 50),
        UsoGemini("gemini-3.5-flash", 300, 30, 7, 0),
    ]
    assert resumir_uso(registros) == ResumoUsoIA(
        chamadas=3,
        modelos=("gemini-3.5-flash", "gemini-2.5-flash"),
        entrada=600,
        saida=60,
        raciocinio=12,
        cache=50,
    )


def test_texto_uso() -> None:
    # Reversões que matam: (1) omitir o raciocínio, que é cobrado como saída;
    # (2) mostrar "em cache 0"; (3) falar de consumo quando nada foi ao Gemini.
    uso = ResumoUsoIA(chamadas=4, modelos=("gemini-3.5-flash",), entrada=41200, saida=9800, raciocinio=2048, cache=0)
    assert texto_uso(uso) == (
        "🔢 Consumo da IA: 4 resposta(s) de gemini-3.5-flash — "
        "tokens: entrada 41.200 · saída 9.800 · raciocínio 2.048"
    )
    com_cache = ResumoUsoIA(chamadas=1, modelos=("a", "b"), entrada=10, saida=1, raciocinio=0, cache=8)
    assert texto_uso(com_cache) == (
        "🔢 Consumo da IA: 1 resposta(s) de a, b — tokens: entrada 10 · saída 1 · raciocínio 0 · em cache 8"
    )
    assert texto_uso(ResumoUsoIA(0, (), 0, 0, 0, 0)) is None


def test_tela_mostra_o_consumo_medido_no_processamento(monkeypatch: pytest.MonkeyPatch) -> None:
    # O preparar falso simula uma resposta do Gemini; o resto é o caminho real
    # da casca. Reversões que matam: (1) tirar o `with medir_uso()` de
    # _rodar_parse_deterministico (nada é coletado); (2) não renderizar a
    # linha de consumo na conferência.
    pgr = _pgr_sintetico()

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        transcritor_gemini._registrar_uso("models/gemini-flash-latest", {"usageMetadata": _USO, "modelVersion": "x-1"})
        return pgr, ()

    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    resultado = Resultado(status="OK", matrizes=[MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo",))])
    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    monkeypatch.setattr("agente_medico.superficie.web_matriz.processar_pgr", lambda *a, **k: resultado)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert any(
        c.value == "🔢 Consumo da IA: 1 resposta(s) de x-1 — tokens: entrada 1.200 · saída 300 · raciocínio 512"
        for c in at.caption
    )
