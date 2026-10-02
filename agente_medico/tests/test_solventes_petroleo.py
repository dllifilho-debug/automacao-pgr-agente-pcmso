"""Querosene e solvente de nafta (PGRs CMO Aurora 27.08.26 e Vistamerica 2026-07-28, pintura):
slugs sem exame (sem LT no NR-15 Anexo 11, sem IBE no NR-07 Anexo I) que alimentam a R-FDS-07
(benzeno a confirmar na FDS). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.tests.test_contaminante_a_confirmar import (
    _FISPQ_AGUARRAS,
    _a_confirmar,
    _com_produtos,
    _hidratar,
    _matrizes,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_QUEROSENE = "Querosene (petróleo)"
_NAFTA = "Solvente de nafta (petróleo)"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def test_querosene_e_nafta_do_pgr_pedem_a_fds_cada_um(proto: Protocolo) -> None:
    # Reversões que matam: (1) tirar `contaminantes_a_confirmar` de `querosene` ou de
    # `solvente_de_nafta`; (2) tirar o termo com "(petróleo)" de qualquer dos dois —
    # o risco sai sem agente e a pendência some; (3) dar regra de exame a um deles.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_QUEROSENE, _NAFTA)))
    (pintura,) = _matrizes(proto, pgr)

    assert [r.agente for r in pgr.ghes[0].riscos] == ["querosene", "solvente_de_nafta"]
    motivos = [p.motivo for p in _a_confirmar(pintura)]
    assert len(motivos) == 2
    assert motivos[0].startswith("Querosene (petróleo) sem FDS") and motivos[1].startswith(_NAFTA + " sem FDS")
    sem_os_dois, _ = _hidratar(proto, ("GHE 18 - PINTURA", ()))
    (referencia,) = _matrizes(proto, sem_os_dois)
    assert sorted((e.exame, e.periodicidade_meses) for e in pintura.linhas) == sorted(
        (e.exame, e.periodicidade_meses) for e in referencia.linhas
    )


def test_querosene_da_fispq_e_risco_material_nao_inerte(proto: Protocolo) -> None:
    # FISPQ da aguarrás: querosene "0 - 100" atravessa o corte de 5% → materialidade
    # indeterminada, bloqueante (D-ARQ-35), igual à nafta da mesma FISPQ.
    # Reversão que mata: tirar `cas: "8008-20-6"` de `querosene` — o componente volta a
    # cair como inerte-declarado (R-FDS-06, não bloqueante).
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", ("Aguarrás",)))
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Aguarrás mineral", _FISPQ_AGUARRAS)))

    querosene = [p for p in pintura.pendencias if "'Querosene'" in p.motivo]
    assert [(p.tipo, p.bloqueante, p.regra_origem) for p in querosene] == [
        ("materialidade_ausente", True, "D-ARQ-35")
    ]
