"""Lotes do Gemini em paralelo (D-ARQ-80, nota de 06/10/2026): rotas GHE e grid.
Nenhum teste toca a rede — `_chamar_gemini` ou `requests.post` simulados. Cada
teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

import json
import re
import threading
import time
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agente_medico.adaptadores import transcritor_gemini
from agente_medico.adaptadores.transcritor_gemini import (
    TranscricaoIndisponivel,
    _mapear_lotes,
    medir_uso,
)
from agente_medico.adaptadores.transcritor_gemini_grid import TranscritorGeminiGrid
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.transcritor_grid import EntradaGrid

_CHAMAR_GHE = "agente_medico.adaptadores.transcritor_gemini_pgr._chamar_gemini"
_POST = "agente_medico.adaptadores.transcritor_gemini.requests.post"


def _blocos_do_prompt(prompt: str) -> list[str]:
    return re.findall(r"bloco (\d+)", prompt)


def _resposta_ghe(prompt: str) -> str:
    return json.dumps([{"nome": f"N{n}", "cargos": [], "riscos": []} for n in _blocos_do_prompt(prompt)])


def test_lotes_sao_chamados_ao_mesmo_tempo(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: _mapear_lotes voltar a um laço em série
    # (`[funcao(lote) for lote in lotes]` sempre) — a barreira exige as 3
    # chamadas em curso juntas e quebra por tempo esgotado.
    barreira = threading.Barrier(3, timeout=5)

    def _chamar(prompt: str, chave: str) -> str:
        barreira.wait()
        return _resposta_ghe(prompt)

    monkeypatch.setattr(_CHAMAR_GHE, _chamar)
    resultado = TranscritorGeminiGHE(chave="fake").transcrever_lote([f"bloco {i}" for i in range(13)])

    assert len(resultado) == 13


def test_resultado_sai_na_ordem_dos_blocos_mesmo_com_lote_lento(monkeypatch: pytest.MonkeyPatch) -> None:
    # O 1º lote responde por último. Reversão que mata: montar o resultado na
    # ordem de conclusão (`as_completed`) e não na de envio — o GHE de cada
    # bloco iria para a posição de outro (D-ARQ-80 cl.2, o pior modo de falha).
    def _chamar(prompt: str, chave: str) -> str:
        if "bloco 0\n" in prompt or prompt.rstrip().endswith("bloco 0"):
            time.sleep(0.3)
        return _resposta_ghe(prompt)

    monkeypatch.setattr(_CHAMAR_GHE, _chamar)
    resultado = TranscritorGeminiGHE(chave="fake").transcrever_lote([f"bloco {i}" for i in range(13)])

    assert [g.nome for g in resultado] == [f"N{i}" for i in range(13)]


def test_consumo_das_chamadas_em_paralelo_entra_na_conta() -> None:
    # Reversão que mata: submeter a tarefa sem copy_context() — thread de pool
    # não herda a ContextVar de medir_uso, nada é registrado e a tela mostra
    # consumo zero sem erro.
    def _eco(*args: Any, **kwargs: Any) -> Mock:
        prompt = kwargs["json"]["contents"][0]["parts"][0]["text"]
        nomes = [l.split(": ", 1)[1] for l in prompt.splitlines() if l.startswith("FUNÇÃO (como está no PDF): ")]
        resp = Mock()
        resp.status_code = 200
        resp.json.return_value = {
            "candidates": [
                {
                    "content": {"parts": [{"text": json.dumps([{"nome": n, "cargos": [n], "riscos": []} for n in nomes])}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"promptTokenCount": 100, "candidatesTokenCount": 10},
        }
        return resp

    entradas = [EntradaGrid(f"FUNCAO {i}", "RUÍDO") for i in range(14)]
    with patch(_POST, side_effect=_eco), medir_uso() as registros:
        ghes = TranscritorGeminiGrid(chave="fake").transcrever_lote(entradas)

    assert len(ghes) == 14
    assert len(registros) == 3
    assert sum(r.entrada for r in registros) == 300


def test_concorrencia_respeita_o_teto() -> None:
    # Reversão que mata: max_workers=len(lotes) — 12 lotes sairiam todos de uma
    # vez, acima de _LOTES_SIMULTANEOS.
    em_curso = 0
    pico = 0
    trava = threading.Lock()

    def _lento(lote: int) -> int:
        nonlocal em_curso, pico
        with trava:
            em_curso += 1
            pico = max(pico, em_curso)
        time.sleep(0.05)
        with trava:
            em_curso -= 1
        return lote

    assert _mapear_lotes(_lento, list(range(12))) == list(range(12))
    assert pico == transcritor_gemini._LOTES_SIMULTANEOS


def test_falha_de_um_lote_propaga(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: engolir a exceção do futuro (try/except devolvendo
    # lote vazio) — a falha de invocação viraria resultado parcial silencioso,
    # contra o contrato de transcrever_lote.
    def _chamar(prompt: str, chave: str) -> str:
        if "bloco 7" in prompt:
            raise TranscricaoIndisponivel("HTTP 503")
        return _resposta_ghe(prompt)

    monkeypatch.setattr(_CHAMAR_GHE, _chamar)
    with pytest.raises(TranscricaoIndisponivel, match="HTTP 503"):
        TranscritorGeminiGHE(chave="fake").transcrever_lote([f"bloco {i}" for i in range(13)])
