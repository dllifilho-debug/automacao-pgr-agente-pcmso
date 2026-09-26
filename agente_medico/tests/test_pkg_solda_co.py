"""R-PKG-SOLD-CO — carboxihemoglobina 6M PER na solda. Precedente: CMO Aurora GHE 16 e
Varandas Flamboyant GHE 17, sem CO no inventário do PGR. Base: NR-07 Anexo I Quadro 1
(CO → COHb). Cada teste nomeia a reversão que o deixa vermelho."""

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


def _cohb(proto: Protocolo, *agentes: str) -> ExameEmitido | None:
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
    return next((e for e in matriz.linhas if e.exame == "carboxihemoglobina"), None)


@pytest.mark.parametrize("agente", ["manganes", "fumos_metalicos"])
def test_solda_da_carboxihemoglobina_semestral_no_periodico(proto: Protocolo, agente: str) -> None:
    # Aurora GHE 16 (manganês do eletrodo, CO não inventariado). Reversões que matam: tirar
    # R-PKG-SOLD-CO (sem COHb); trocar a periodicidade ou os momentos.
    linha = _cohb(proto, agente)

    assert linha is not None
    assert linha.periodicidade_meses == 6
    assert linha.momentos == {Momento.PER}
    assert "R-PKG-SOLD-CO" in {m.regra_id for m in linha.motivos}


def test_sem_solda_nao_ha_carboxihemoglobina(proto: Protocolo) -> None:
    # Reversão que mata: `quando: todo_trabalhador` (ou qualquer gatilho mais largo que
    # `solda_indicador`) em R-PKG-SOLD-CO.
    assert _cohb(proto, "ferro") is None
