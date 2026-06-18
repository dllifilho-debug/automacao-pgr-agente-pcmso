from __future__ import annotations

from agente_medico.motor.materialidade import Materialidade, materialidade
from agente_medico.motor.resolvedor import EntradaIndice, gate_cas
from agente_medico.motor.tipos import Componente
from agente_medico.tests.fixtures.fds_t65 import (
    adesivo_pvc_tigre,
    cimento_ciplan,
    tinta_acrilica,
)

# Índice de teste à mão — não carrega Protocolo (padrão _INDICE de test_resolvedor).
# Chaves = _so_digitos(CAS). is_carcinogeno_iarc inerte pós-reversão 003.V (não propagada
# pelo gate; mantida no EntradaIndice para futura Parte 3 plena).
_IDX: dict[str, EntradaIndice] = {
    "78933":    EntradaIndice("metil_etil_cetona",  False),  # MEK 78-93-3
    "67641":    EntradaIndice("acetona",            False),  # 67-64-1
    "141786":   EntradaIndice("acetato_de_etila",   False),  # 141-78-6
    "13463677": EntradaIndice("dioxido_de_titanio", True),   # TiO2 correto (não exercitado pela fixture crua: CAS errado)
}


def _resolver(c: Componente) -> Componente:
    return gate_cas(c, _IDX)[0]


def test_mek_material() -> None:
    # MEK (10,42): gate resolve slug metil_etil_cetona → piso 10 > 5 → ramo4 → MATERIAL
    assert materialidade(_resolver(adesivo_pvc_tigre()[1])) is Materialidade.MATERIAL


def test_tio2_straddle_ausente() -> None:
    # TiO2 CAS errado (134363-67-7): gate ramo(c) → agente=None → ramo0 → AUSENTE
    # (era ramo3-straddle antes da fixture crua; veredito AUSENTE preservado, mas via ramo0)
    assert materialidade(_resolver(tinta_acrilica()[1])) is Materialidade.AUSENTE


def test_tinta_acrilica_ramo0_ausente() -> None:
    componentes = tinta_acrilica()
    # [0] e [2..8]: CAS vários ramos (d/b/c) → agente=None → ramo0 → AUSENTE.
    # [1] TiO2 coberto em test_tio2_straddle_ausente.
    for i in (0, 2, 3, 4, 5, 6, 7, 8):
        assert materialidade(_resolver(componentes[i])) is Materialidade.AUSENTE


def test_cimento_ciplan_ramo0_ausente() -> None:
    # todos os 8: CAS sem slug no índice (ramos b/d/c) → agente=None → ramo0 → AUSENTE
    for componente in cimento_ciplan():
        assert materialidade(_resolver(componente)) is Materialidade.AUSENTE


def test_adesivo_pvc_ramo0_ausente() -> None:
    componentes = adesivo_pvc_tigre()
    # [0] acetona: gate resolve → MATERIAL (coberto em test_contagem)
    # [1] MEK: coberto em test_mek_material
    # [2..6]: sem slug no índice (ramos b/d) → agente=None → ramo0 → AUSENTE
    # [6] Segredo Industrial 2: caso-âncora da DT (CAS oculto + H334/H317 declarados
    #     na FDS, sem slug → ramo0 honesto, não bypass-sensibilizante).
    for i in (2, 3, 4, 5, 6):
        assert materialidade(_resolver(componentes[i])) is Materialidade.AUSENTE


def test_contagem() -> None:
    # 9 (tinta) + 8 (cimento) + 7 (adesivo) = 24 componentes.
    # Cadeia resolvida via _resolver (gate_cas + materialidade):
    #   MATERIAL=2 (MEK piso10>5, acetona piso30>5), AUSENTE=22, NÃO-MATERIAL=0.
    # Contagem anterior (1/23/0) desatualizada: acetona ganhou slug em 003.N.
    componentes = tinta_acrilica() + cimento_ciplan() + adesivo_pvc_tigre()
    assert len(componentes) == 24
    resultados = [materialidade(_resolver(c)) for c in componentes]
    assert resultados.count(Materialidade.MATERIAL) == 2
    assert resultados.count(Materialidade.AUSENTE) == 22
    assert resultados.count(Materialidade.NAO_MATERIAL) == 0
