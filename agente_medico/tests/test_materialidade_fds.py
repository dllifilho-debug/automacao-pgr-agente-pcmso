from __future__ import annotations

from agente_medico.motor.materialidade import Materialidade, materialidade
from agente_medico.tests.fixtures.fds_t65 import (
    adesivo_pvc_tigre,
    cimento_ciplan,
    tinta_acrilica,
)


def test_mek_material() -> None:
    # adesivo_pvc_tigre[1] MEK (10,42): piso 10 > 5 -> ramo4 -> MATERIAL
    assert materialidade(adesivo_pvc_tigre()[1]) is Materialidade.MATERIAL


def test_tio2_straddle_ausente() -> None:
    # tinta_acrilica[1] TiO2 (1,15): piso 1 <= 5 < teto 15 -> ramo3 straddle -> AUSENTE
    assert materialidade(tinta_acrilica()[1]) is Materialidade.AUSENTE


def test_tinta_acrilica_ramo0_ausente() -> None:
    componentes = tinta_acrilica()
    # [0] e [2..8]: agente=None -> ramo0 -> AUSENTE.
    # [1] TiO2 é o caso-straddle (ramo3), coberto em test_tio2_straddle_ausente.
    for i in (0, 2, 3, 4, 5, 6, 7, 8):
        assert materialidade(componentes[i]) is Materialidade.AUSENTE


def test_cimento_ciplan_ramo0_ausente() -> None:
    # todos os 8 componentes: agente=None (nenhum slug em agentes.yaml) -> ramo0 -> AUSENTE
    for componente in cimento_ciplan():
        assert materialidade(componente) is Materialidade.AUSENTE


def test_adesivo_pvc_ramo0_ausente() -> None:
    componentes = adesivo_pvc_tigre()
    # [0] e [2..6]: agente=None -> ramo0 -> AUSENTE.
    # [6] Segredo Industrial 2 é o caso-âncora da DT (CAS oculto + H334/H317
    # declarados na FDS, sem slug -> ramo0 honesto, não bypass-sensibilizante).
    # [1] MEK é o caso-material (ramo4), coberto em test_mek_material.
    for i in (0, 2, 3, 4, 5, 6):
        assert materialidade(componentes[i]) is Materialidade.AUSENTE


def test_contagem() -> None:
    # 9 (tinta) + 8 (cimento) + 7 (adesivo) = 24 componentes.
    # Exatamente 1 MATERIAL (MEK), 23 AUSENTE, 0 NÃO-MATERIAL.
    componentes = tinta_acrilica() + cimento_ciplan() + adesivo_pvc_tigre()
    assert len(componentes) == 24
    resultados = [materialidade(c) for c in componentes]
    assert resultados.count(Materialidade.MATERIAL) == 1
    assert resultados.count(Materialidade.AUSENTE) == 23
    assert resultados.count(Materialidade.NAO_MATERIAL) == 0
