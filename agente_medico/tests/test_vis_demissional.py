"""R-VIS-01-solda e R-VIS-03 — acuidade visual também no demissional para solda e para
manta asfáltica a quente. Sem norma que exija (NR-07 7.5.18); precedente RQ.61 Viverde
(GHE 10 serralheria, GHE 09 manta asfáltica) e PCMSO-modelo da Dra. Carolini. Cada teste
nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, Momento, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 26)
_COM_DEM = {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _acuidade(proto: Protocolo, *agentes: str) -> ExameEmitido | None:
    ghe = GHEPGR(
        id="GHE-16",
        nome="SERRALHERIA",
        cargos=("Serralheiro",),
        riscos=tuple(
            RiscoPGR(tipo="", agente=a, quantificacao=None, severidade=None, nivel_risco="MODERADO")
            for a in agentes
        ),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return next((e for e in matriz.linhas if e.exame == "acuidade_visual"), None)


@pytest.mark.parametrize("agente", ["manganes", "fumos_metalicos"])
def test_solda_da_acuidade_visual_com_demissional(proto: Protocolo, agente: str) -> None:
    # Aurora GHE 16, Fascino GHE 17. Reversões que matam: tirar R-VIS-01-solda (sem
    # acuidade); tirar `dem` dos momentos; tirar o agente de `solda_indicador` (o caso dele).
    linha = _acuidade(proto, agente)

    assert linha is not None
    assert linha.momentos == _COM_DEM
    assert linha.periodicidade_meses == 12


def test_manta_asfaltica_a_quente_da_acuidade_visual_com_demissional(proto: Protocolo) -> None:
    # RQ.61 Viverde GHE 09, Aurora GHE 22. Reversão que mata: tirar R-VIS-03.
    linha = _acuidade(proto, "cimento_asfaltico")

    assert linha is not None
    assert linha.momentos == _COM_DEM


@pytest.mark.parametrize("agente", ["asfalto", "xileno"])
def test_sem_solda_nem_manta_nao_ha_acuidade_no_demissional(proto: Protocolo, agente: str) -> None:
    # Emulsão a frio e pintura (Aurora 18: DEM fora do padrão das demais matrizes).
    # Reversões que matam: pôr `asfalto` no `quando` de R-VIS-03; `quando:
    # todo_trabalhador` em qualquer das duas regras.
    linha = _acuidade(proto, agente)

    assert linha is None or Momento.DEM not in linha.momentos


def _acuidade_por_cargo(proto: Protocolo, cargo: str) -> ExameEmitido | None:
    ghe = GHEPGR(
        id="GHE-19",
        nome="PORTARIA",
        cargos=(cargo,),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return next((e for e in matriz.linhas if e.exame == "acuidade_visual"), None)


@pytest.mark.parametrize("cargo", ["Porteiro", "PORTEIRA", "Porteiro Noturno"])
def test_porteiro_recebe_acuidade_visual_sem_demissional(proto: Protocolo, cargo: str) -> None:
    # Aurora GHE 19 (app sem acuidade; gabarito ADM, PER, MRO). Reversões que matam:
    # tirar R-VIS-02 (sem acuidade); pôr `dem` nos momentos; comparar o cargo sem
    # normalizar caixa (PORTEIRA some).
    linha = _acuidade_por_cargo(proto, cargo)

    assert linha is not None
    assert linha.momentos == {Momento.ADM, Momento.PER, Momento.MR}


def test_cargo_que_nao_e_porteiro_nao_recebe_acuidade(proto: Protocolo) -> None:
    # "Portaria" é o setor, não o cargo. Reversão que mata: `quando:
    # todo_trabalhador` em R-VIS-02.
    assert _acuidade_por_cargo(proto, "Auxiliar de Portaria Administrativo") is None
