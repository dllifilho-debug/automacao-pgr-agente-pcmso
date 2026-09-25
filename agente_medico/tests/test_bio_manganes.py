"""R-BIO-03 — manganês no sangue semestral (adm/per/MR) para qualquer exposição
confirmada a Mn, fora do Anexo I da NR-07 e portanto fora de R-BIO-05. Caso de
conferência: Aurora Lago das Rosas 27.08.26, GHE 16 SERRALHERIA — gabarito da
Dra. Patrícia pede "Manganês no sangue (ADM, PER 6 meses, MRO)". Cada teste
nomeia a reversão de código ou dado que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, MatrizGHE, Momento, RiscoPGR
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    RodapeDocumento,
    montar_documento,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 25)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, *riscos: RiscoPGR) -> MatrizGHE:
    ghe = GHEPGR(
        id="GHE-16",
        nome="SERRALHERIA",
        cargos=("Serralheiro",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return matriz


def _risco(agente: str, nivel: str | None) -> RiscoPGR:
    return RiscoPGR(tipo="", agente=agente, quantificacao=None, severidade=None, nivel_risco=nivel)


def test_manganes_emite_manganes_no_sangue_semestral_em_adm_per_mr(proto: Protocolo) -> None:
    # Reversões que matam: tirar R-BIO-03 de regras.yaml (nada é emitido);
    # trocar periodicidade_meses ou momentos (a linha diverge do gabarito).
    matriz = _matriz(proto, _risco("manganes", "MODERADO"))

    (linha,) = [e for e in matriz.linhas if e.exame == "manganes_sangue"]
    assert linha.periodicidade_meses == 6
    assert linha.momentos == {Momento.ADM, Momento.PER, Momento.MR}
    assert [m.regra_id for m in linha.motivos] == ["R-BIO-03"]


def test_sem_manganes_nao_emite(proto: Protocolo) -> None:
    # Reversão que mata: `quando: todo_trabalhador` (ou qualquer predicado que
    # não seja o agente) em R-BIO-03 — o exame sairia para todo GHE.
    matriz = _matriz(proto, _risco("xileno", "MODERADO"))

    assert "manganes_sangue" not in {e.exame for e in matriz.linhas}


def test_manganes_irrelevante_nao_vira_mencao_documental(proto: Protocolo) -> None:
    # Mn não está no Anexo I da NR-07: a dispensa de R-BIO-05 (só Quadro 1) não
    # se aplica. Reversão que mata: dar a R-BIO-03 a chave mencao_documental —
    # o exame some e vira observação.
    matriz = _matriz(proto, _risco("manganes", "IRRELEVANTE"))

    assert "manganes_sangue" in {e.exame for e in matriz.linhas}
    assert matriz.observacoes == ()


def test_documento_mostra_a_grafia_do_gabarito(proto: Protocolo) -> None:
    # Reversão que mata: mudar nome_exibicao de manganes_sangue em exames.yaml —
    # a célula deixa de bater com "Manganês no sangue (ADM, PER 6 meses, MRO)".
    doc = montar_documento(
        [_matriz(proto, _risco("manganes", "MODERADO"))],
        proto.vocabulario.exames,
        CabecalhoDocumento("", "", "", "", "", ""),
        RodapeDocumento("", "", ""),
    )

    (linha,) = doc.blocos[0].linhas
    assert "Manganês no sangue (ADM, PER 6 meses, MRO)" in linha.celulas
