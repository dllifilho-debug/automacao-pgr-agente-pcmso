"""R-PKG-ASF e R-PKG-ASF-CO — impermeabilização com asfalto. Precedente: 7/7 GHEs de
impermeabilização com asfalto em 6 matrizes do acervo (clínico 6M, hemograma 6M; COHb 6M
na manta a quente). Base: NR-07 Anexo V (cancerígeno sem avaliação ambiental), 7.5.8 e
7.5.18; NR-07 Anexo I Quadro 1 (CO → COHb). Sem pacote do benzeno (NR-15 Anexo 13-A).
Cada teste nomeia a reversão que o deixa vermelho."""

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


def _linhas(proto: Protocolo, *agentes: str) -> dict[str, ExameEmitido]:
    ghe = GHEPGR(
        id="GHE-22",
        nome="IMPERMEABILIZAÇÃO",
        cargos=("Aplicador de Asfalto",),
        riscos=tuple(
            RiscoPGR(tipo="", agente=a, quantificacao=None, severidade=None, nivel_risco="BAIXO")
            for a in agentes
        ),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return {e.exame: e for e in matriz.linhas}


def test_asfalto_da_clinico_e_hemograma_semestrais(proto: Protocolo) -> None:
    # Reversões que matam: tirar R-PKG-ASF de regras.yaml (clínico volta a 12M, sem
    # hemograma); tirar `asfalto` do `quando` (idem para o asfalto genérico).
    linhas = _linhas(proto, "asfalto")

    assert linhas["exame_clinico"].periodicidade_meses == 6
    assert linhas["hemograma"].periodicidade_meses == 6
    assert linhas["hemograma"].momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}
    assert "R-PKG-ASF" in {m.regra_id for m in linhas["hemograma"].motivos}


def test_asfalto_generico_nao_pede_carboxihemoglobina_nem_pacote_do_benzeno(proto: Protocolo) -> None:
    # Emulsão a frio não tem CO; asfalto não é mistura de benzeno ≥1%. Reversões que
    # matam: pôr `asfalto` no `quando` de R-PKG-ASF-CO; pôr t,t-mucônico ou
    # reticulócitos em R-PKG-ASF.
    linhas = _linhas(proto, "asfalto")

    assert "carboxihemoglobina" not in linhas
    assert "acido_transmuconico" not in linhas
    assert "reticulocitos" not in linhas


def test_cimento_asfaltico_soma_carboxihemoglobina_ao_pacote(proto: Protocolo) -> None:
    # Aurora GHE 22 (manta a quente, CO não inventariado). Reversões que matam: tirar
    # R-PKG-ASF-CO (sem COHb); tirar `cimento_asfaltico` do `quando` de R-PKG-ASF
    # (clínico volta a 12M, sem hemograma).
    linhas = _linhas(proto, "cimento_asfaltico")

    assert linhas["carboxihemoglobina"].periodicidade_meses == 6
    assert linhas["carboxihemoglobina"].momentos == {Momento.PER}
    assert linhas["exame_clinico"].periodicidade_meses == 6
    assert linhas["hemograma"].periodicidade_meses == 6
