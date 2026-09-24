"""Rota LLM do lado-PGR transcreve o nível P×S da linha do risco
(`avaliacao_qualitativa`, DT-003EC-01/DT-003EB-02), e o motor só o aceita de
bloco cuja legenda é a escala P×S (Irrelevante…Crítico). Cada teste nomeia a
reversão que o deixa vermelho."""

from __future__ import annotations

import json
from collections.abc import Sequence

import pytest

from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim
from agente_medico.motor.transcritor_pgr import transcrever_ghes

_ALVO_CHAMADA = "agente_medico.adaptadores.transcritor_gemini_pgr._chamar_gemini"

# Trechos reais: linha de risco + legenda do GHE 03 do PGR TOCTAO ALT 65
# (escala P×S), e linha do ET05 do PGR Viverde V02 (escore somado).
_BLOCO_PXS = (
    "GHE 03 - ADMINISTRAÇÃO\n"
    "Acidentes Queda de Pisos escorregadios, Fraturas, lesões diversas, possibilidade "
    "1 1 IRRELEVANTE Manter área de circulação livre de Calçado antiderrapante\n"
    "Legenda (P × S): Irrelevante (1) Baixo (2–4) Moderado (4–12) Alto (10–16) Crítico (20–25)"
)
_BLOCO_ESCORE = (
    "SETOR/FUNÇÃO Estrutura/ carpinteiro\n"
    "ET05 fôrma de pilar Intermitente Q D N C 1 2 1 2 6 2 1 3 18 Trivial\n"
    "ET03 fôrma de pilar Habitual A D N C 3 2 2 1 8 2 3 5 40 Moderado"
)


def _ghe_com_nivel(nivel: str) -> GHEVerbatim:
    return GHEVerbatim(
        nome="X",
        cargos=(),
        riscos=(RiscoVerbatim(agente="Sílica", quantificacao="", fonte_geradora="", avaliacao_qualitativa=nivel),),
    )


class _ClienteUnitario:
    def __init__(self, ghe: GHEVerbatim) -> None:
        self._ghe = ghe

    def transcrever(self, bloco: str) -> GHEVerbatim:
        return self._ghe


class _ClienteLote(_ClienteUnitario):
    def transcrever_lote(self, blocos: Sequence[str]) -> tuple[GHEVerbatim, ...]:
        return tuple(self._ghe for _ in blocos)


def test_adaptador_desembrulha_avaliacao_qualitativa(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: tirar `avaliacao_qualitativa=` de _ghe_de_dict — o
    # campo do JSON é ignorado e o risco sai com "".
    payload = [{"nome": "ADM", "cargos": [], "riscos": [
        {"agente": "Queda de mesmo nível", "quantificacao": "", "fonte_geradora": "",
         "avaliacao_qualitativa": "1 1 IRRELEVANTE"}]}]
    monkeypatch.setattr(_ALVO_CHAMADA, lambda prompt, chave: json.dumps(payload))

    (ghe,) = TranscritorGeminiGHE(chave="fake").transcrever_lote([_BLOCO_PXS])

    assert ghe.riscos[0].avaliacao_qualitativa == "1 1 IRRELEVANTE"


def test_prompt_de_lote_pede_s_p_nivel(monkeypatch: pytest.MonkeyPatch) -> None:
    # Produção usa o lote (003.EW). Reversão que mata: tirar a regra 6b de
    # _PROMPT_GHE_LOTE — o modelo segue tratando o nível como ruído (regra 7).
    prompts: list[str] = []

    def _chamar(prompt: str, chave: str) -> str:
        prompts.append(prompt)
        return json.dumps([{"nome": "X", "cargos": [], "riscos": []}])

    monkeypatch.setattr(_ALVO_CHAMADA, _chamar)
    TranscritorGeminiGHE(chave="fake").transcrever_lote([_BLOCO_PXS])

    assert "avaliacao_qualitativa = texto cru das colunas \"S\", \"P\" e \"NÍVEL DE RISCO\"" in prompts[0]


def test_prompt_unitario_pede_s_p_nivel(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: tirar a regra 6b de _PROMPT_GHE (o unitário segue
    # em uso fora de transcrever_ghes).
    prompts: list[str] = []

    def _chamar(prompt: str, chave: str) -> str:
        prompts.append(prompt)
        return json.dumps({"nome": "X", "cargos": [], "riscos": []})

    monkeypatch.setattr(_ALVO_CHAMADA, _chamar)
    TranscritorGeminiGHE(chave="fake").transcrever(_BLOCO_PXS)

    assert "avaliacao_qualitativa = texto cru das colunas \"S\", \"P\" e \"NÍVEL DE RISCO\"" in prompts[0]


def test_bloco_da_escala_pxs_mantem_o_nivel() -> None:
    # Reversão que mata: _restringir_avaliacao_a_escala_pxs descartar sempre
    # (ex.: inverter o teste da legenda) — a rota LLM nunca entregaria nível.
    (ghe,) = transcrever_ghes([_BLOCO_PXS], _ClienteLote(_ghe_com_nivel("1 1 IRRELEVANTE")))

    assert ghe.riscos[0].avaliacao_qualitativa == "1 1 IRRELEVANTE"


def test_bloco_de_escore_descarta_o_nivel_no_lote() -> None:
    # Escore somado: "5 40 Moderado" casaria o padrão S·P·NÍVEL e levaria a
    # sílica ao R-RX-01-qual. Reversão que mata: tirar a chamada de
    # _restringir_avaliacao_a_escala_pxs de transcrever_ghes.
    (ghe,) = transcrever_ghes([_BLOCO_ESCORE], _ClienteLote(_ghe_com_nivel("5 40 Moderado")))

    assert ghe.riscos[0].avaliacao_qualitativa == ""


def test_bloco_de_escore_descarta_o_nivel_no_caminho_unitario() -> None:
    # Reversão que mata: aplicar a restrição só no ramo de lote de
    # transcrever_ghes — o cliente sem transcrever_lote passaria o nível.
    (ghe,) = transcrever_ghes([_BLOCO_ESCORE], _ClienteUnitario(_ghe_com_nivel("5 40 Moderado")))

    assert ghe.riscos[0].avaliacao_qualitativa == ""
