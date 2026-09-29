"""Grafias de vibração do PGR CMO Aurora 27.08.26 chegam às regras de vibração
pela hidratação real (resolver_termo -> hidratar_pgr -> processar_pgr).
Caso de conferência: GHE 12 OPERAÇÃO COM ELEVADOR DE CARGA — o PGR declara
"Vibração de corpo inteiro" e o gabarito da Dra. Patrícia pede "RX de Coluna Lombo
Sacra (ADM, MRO)" (R-VIB-01). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import GHEVerbatim, MatrizGHE, RiscoVerbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, agente: str) -> MatrizGHE:
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    ghe = GHEVerbatim(
        nome="OPERAÇÃO COM ELEVADOR DE CARGA",
        cargos=("Operador de Elevador de Cremalheira",),
        riscos=(RiscoVerbatim(agente=agente, quantificacao="", fonte_geradora=""),),
    )
    pgr, _ = hidratar_pgr([ghe], indice, date(2030, 1, 1), True)
    (matriz,) = processar_pgr(pgr, proto, hoje=date(2026, 9, 29)).matrizes
    return matriz


def _regras(matriz: MatrizGHE, exame: str) -> set[str]:
    return {m.regra_id for e in matriz.linhas if e.exame == exame for m in e.motivos}


def test_vibracao_de_corpo_inteiro_emite_rx_coluna_lombo_sacra(proto: Protocolo) -> None:
    # R-VIB-01. Reversão que mata: tirar "Vibração de corpo inteiro" dos termos de
    # vibracao_corpo_inteiro em agentes.yaml — o termo fica NAO_RESOLVIDO e nada sai.
    matriz = _matriz(proto, "Vibração de corpo inteiro")

    assert "R-VIB-01" in _regras(matriz, "rx_coluna_lombo_sacra")
    assert "R-VIB-02" in _regras(matriz, "audiometria")


@pytest.mark.parametrize("agente", ["Vibração localizada", "Vibrações localizadas"])
def test_vibracao_localizada_emite_audiometria_sem_rx_lombo_sacra(
    proto: Protocolo, agente: str
) -> None:
    # R-VIB-02 via vibracao_mao_braco. Reversões que matam: tirar o termo de
    # vibracao_mao_braco (R-VIB-02 não sai); movê-lo para vibracao_corpo_inteiro
    # (sai o RX lombo-sacra, que é só de corpo inteiro).
    matriz = _matriz(proto, agente)

    assert "R-VIB-02" in _regras(matriz, "audiometria")
    assert "rx_coluna_lombo_sacra" not in {e.exame for e in matriz.linhas}
