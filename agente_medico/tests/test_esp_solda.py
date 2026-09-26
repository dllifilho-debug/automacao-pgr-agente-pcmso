"""R-ESP-04 — espirometria 24M na solda, [INTERPRETADO] via NR-07 7.5.18 (fumos metálicos
estão no item 3.2 do Anexo III, não no 3.1). Precedente: planilha Dra. Patrícia atualizada e
26/26 serralherias de set/2026. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, Momento, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 26)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _espirometria(proto: Protocolo, *agentes: str) -> ExameEmitido | None:
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
    return next((e for e in matriz.linhas if e.exame == "espirometria"), None)


@pytest.mark.parametrize("agente", ["manganes", "fumos_metalicos"])
def test_solda_sem_poeira_da_espirometria_24m(proto: Protocolo, agente: str) -> None:
    # Serralheria cujo PGR não traz poeira mineral. Reversões que matam: tirar R-ESP-04
    # (sem espirometria); trocar a periodicidade; tirar `dem` dos momentos.
    linha = _espirometria(proto, agente)

    assert linha is not None
    assert linha.periodicidade_meses == 24
    assert linha.momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}
    assert "R-ESP-04" in {m.regra_id for m in linha.motivos}


def test_sem_solda_nem_poeira_nao_ha_espirometria(proto: Protocolo) -> None:
    # Reversão que mata: `quando: todo_trabalhador` (ou gatilho mais largo) em R-ESP-04.
    assert _espirometria(proto, "ferro") is None
