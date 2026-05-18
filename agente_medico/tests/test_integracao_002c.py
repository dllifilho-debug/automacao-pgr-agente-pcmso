from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from agente_medico.motor.estagios.consolidacao import stage_8_consolidacao
from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    GHEContext,
    GHEPGR,
    Momento,
    PGR,
    Risco,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def test_pipeline_gates_emissao_consolidacao_atividade_critica() -> None:
    pgr = PGR(
        validade=date.today() - timedelta(days=30),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="GHE-01",
                nome="Trabalho em estrutura",
                cargos=("carpinteiro",),
                riscos=(
                    RiscoPGR(
                        tipo="fisico",
                        agente="trabalho_altura",
                        quantificacao=None,
                        severidade=None,
                    ),
                ),
                epis=(),
                produtos_quimicos=(),
                psicossocial=False,
            ),
        ),
    )

    proto = carregar(_PROTOCOLO_DIR)

    pendencias_globais = stage_1_gates(pgr)
    assert pendencias_globais == []

    ghe = pgr.ghes[0]
    ctx = GHEContext(
        pgr_ghe=ghe,
        riscos=[
            Risco(
                agente="trabalho_altura",
                fonte="explicito",
                detalhe=None,
                quantificacao=None,
                anexo_nr07=None,
            )
        ],
    )

    exames = stage_5_emissao(ctx, proto)
    assert len(exames) == 5

    exames_final = stage_8_consolidacao(exames)
    assert len(exames_final) == 5

    nomes = {e.exame.strip().lower() for e in exames_final}
    assert nomes == {"hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg"}

    for e in exames_final:
        assert e.periodicidade_meses == 12
        assert e.momentos == {Momento.ADM, Momento.PER, Momento.MR}
        assert e.motivos[0].regra_id == "R-PKG-ATIVCRIT"

    assert ctx.pendencias == []
