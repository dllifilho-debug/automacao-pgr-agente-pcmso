"""Tempo de processamento do PGR na tela: total, espera pela IA, motor e o resto
(leitura do PDF e montagem). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

import time
from collections.abc import Iterator, Sequence

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.tipos import ExameEmitido, GHEVerbatim, MatrizGHE, Momento, Resultado
from agente_medico.superficie.web_matriz import TempoProcessamento, _TranscritorContado, pagina_matriz, texto_tempo
from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario


def test_texto_separa_ia_leitura_e_motor() -> None:
    # Reversões que matam: (1) leitura e montagem calculada como total − IA,
    # sem descontar o motor; (2) trocar as parcelas de lugar.
    tempo = TempoProcessamento(total_s=52.4, ia_s=45.0, motor_s=1.2)
    assert texto_tempo(tempo, 18) == (
        "⏱ Processamento do PGR: 52 s — IA (Gemini): 45 s em 18 bloco(s) · "
        "leitura do PDF e montagem: 6,2 s · motor: 1,2 s"
    )


def test_sem_ia_o_texto_nao_fala_de_ia() -> None:
    # Rota determinística: nenhum bloco foi ao Gemini. Reversão que mata:
    # mostrar a parcela da IA sempre ("IA (Gemini): 0,0 s em 0 bloco(s)").
    tempo = TempoProcessamento(total_s=7.9, ia_s=0.0, motor_s=0.4)
    assert texto_tempo(tempo, 0) == "⏱ Processamento do PGR: 7,9 s — leitura do PDF e montagem: 7,5 s · motor: 0,4 s"


class _Lote:
    def transcrever(self, bloco: str) -> GHEVerbatim:
        return GHEVerbatim(nome=bloco, cargos=(), riscos=())

    def transcrever_lote(self, blocos: Sequence[str]) -> tuple[GHEVerbatim, ...]:
        return tuple(self.transcrever(b) for b in blocos)


def test_contador_soma_o_tempo_da_ia_no_lote(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: medir só `transcrever` e não `transcrever_lote` — o
    # caminho de produção (lote) daria 0 s de IA.
    relogio: Iterator[float] = iter([10.0, 13.5])
    monkeypatch.setattr(time, "perf_counter", lambda: next(relogio))
    contador = _TranscritorContado(interno=_Lote())
    contador.transcrever_lote(["A", "B"])
    assert (contador.chamadas, contador.segundos) == (2, 3.5)


def test_tela_mostra_o_tempo_depois_de_gerar(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões que matam: (1) não gravar `tempo` no cache; (2) não renderizar
    # a linha na conferência.
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    resultado = Resultado(status="OK", matrizes=[MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo",))])
    _mockar_parse_deterministico(monkeypatch, resultado)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert any(c.value.startswith("⏱ Processamento do PGR: ") for c in at.caption)
