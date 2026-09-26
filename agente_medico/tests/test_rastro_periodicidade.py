"""D-ARQ-87 fatia 1 — cada Motivo guarda o que a própria regra pediu (periodicidade,
momentos, base normativa), antes do piso da consolidação. Caso: impermeabilização com
asfalto, onde o clínico sai 6M porque R-PKG-ASF (6M) vence R-CLI-01 (12M). Cada teste
nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, MatrizGHE, Momento, RiscoPGR
from agente_medico.superficie.revisao_matriz import montar_revisao

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 26)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def matriz(proto: Protocolo) -> MatrizGHE:
    ghe = GHEPGR(
        id="GHE-22",
        nome="IMPERMEABILIZAÇÃO",
        cargos=("Aplicador de Asfalto",),
        riscos=(RiscoPGR(tipo="", agente="asfalto", quantificacao=None, severidade=None, nivel_risco="BAIXO"),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (m,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return m


def _linha(matriz: MatrizGHE, exame: str) -> ExameEmitido:
    return next(e for e in matriz.linhas if e.exame == exame)


def test_motivo_guarda_a_periodicidade_que_a_regra_pediu(matriz: MatrizGHE) -> None:
    # Reversões que matam: não passar `periodicidade_meses` ao Motivo em emissao.py
    # (fica None); passar a periodicidade da linha consolidada em vez da do item.
    clinico = _linha(matriz, "exame_clinico")

    assert clinico.periodicidade_meses == 6
    pedidas = {m.regra_id: m.periodicidade_meses for m in clinico.motivos}
    assert pedidas["R-CLI-01"] == 12
    assert pedidas["R-PKG-ASF"] == 6


def test_motivo_guarda_os_momentos_do_proprio_item(matriz: MatrizGHE) -> None:
    # R-PKG-ASF pede clínico só em [per] e hemograma em [adm, per, MR, dem]. Reversões
    # que matam: um Motivo só por regra, montado antes do laço dos itens (os dois
    # exames passam a carregar os mesmos momentos); não passar `momentos`.
    def momentos(exame: str) -> frozenset[Momento]:
        return next(m.momentos for m in _linha(matriz, exame).motivos if m.regra_id == "R-PKG-ASF")

    assert momentos("exame_clinico") == {Momento.PER}
    assert momentos("hemograma") == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}


def test_motivo_carrega_a_base_normativa_da_regra(proto: Protocolo, matriz: MatrizGHE) -> None:
    # Reversão que mata: não passar `base_normativa` ao Motivo.
    regra = next(r for r in proto.regras if r["id"] == "R-PKG-ASF")
    motivo = next(m for m in _linha(matriz, "hemograma").motivos if m.regra_id == "R-PKG-ASF")

    assert motivo.base_normativa == regra["base_normativa"]


def test_revisao_mostra_a_periodicidade_pedida_por_regra(proto: Protocolo, matriz: MatrizGHE) -> None:
    # Reversão que mata: `_regras` voltar a listar só o regra_id.
    (revisao,) = montar_revisao([matriz], proto.vocabulario.exames, proto.vocabulario.agentes)
    clinico = next(l for l in revisao.linhas if "R-PKG-ASF" in l.regras and "R-CLI-01" in l.regras)

    assert clinico.periodicidade == "6 meses"
    assert clinico.regras == "R-CLI-01 (12 meses), R-PKG-ASF (6 meses)"
