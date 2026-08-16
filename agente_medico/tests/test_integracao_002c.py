from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

from agente_medico.motor.estagios.consolidacao import stage_8_consolidacao
from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    GHEContext,
    GHEPGR,
    Momento,
    PGR,
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
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)

    stage_4_predicados(ctx, proto)

    assert ctx.predicados["atividade_critica"] is True
    assert ctx.predicados["altura"] is True
    # espaco_confinado não entra no cache porque o `ou` de atividade_critica
    # curto-circuita após altura=True. Ver docs/HISTORICO_OPERACIONAL.md § Sessão 002.D2.
    # R-VIB-01, R-AUD-01, R-AUD-02, R-VIB-02 adicionam vibracao_corpo_inteiro, ruido_acima_acao, ruido
    # ao cache a partir de 002.E.
    assert {"altura", "atividade_critica"}.issubset(ctx.predicados.keys())
    assert "espaco_confinado" not in ctx.predicados
    # motorista_equipamento_pesado (003.ED, substitui maquina_pesada em
    # atividade_critica.ou) ENTRA no cache apesar do curto-circuito acima,
    # porque R-AUD-01 também o referencia diretamente em seu "quando".
    assert "motorista_equipamento_pesado" in ctx.predicados

    exames = stage_5_emissao(ctx, proto)

    exames_final = stage_8_consolidacao(exames)

    nomes = {e.exame.strip().lower() for e in exames_final}
    # Superconjunto, não contagem exata: R-CLI-01 (piso universal, 003.EC) e
    # R-PSY-02 (psicossocial incondicional, 003.EN) somam exames a toda
    # matriz; cravar contagem fixa quebraria na próxima regra incondicional.
    assert {"hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg"}.issubset(nomes)
    assert "exame_clinico" in nomes
    assert {"avaliacao_psicossocial", "avaliacao_saude_mental"}.issubset(nomes)

    # R-AUD-04 (piso incondicional todo_trabalhador) foi DEPRECATED em 003.EZ
    # (D-ARQ-81 — fundamento refutado por DT-003EY-01). Este GHE não tem risco
    # ruído, então R-AUD-01/02 não disparam (nem emitem, nem bloqueiam) — a
    # audiometria volta a sair só por R-PKG-ATIVCRIT (adm/per/MR, sem dem) e
    # cai no loop genérico abaixo, junto dos outros 4 exames do pacote.
    _INCONDICIONAIS = {"exame_clinico", "avaliacao_psicossocial", "avaliacao_saude_mental"}
    exames_ativcrit = [e for e in exames_final if e.exame.strip().lower() not in _INCONDICIONAIS]
    for e in exames_ativcrit:
        assert e.periodicidade_meses == 12
        assert e.momentos == {Momento.ADM, Momento.PER, Momento.MR}
        assert e.motivos[0].regra_id == "R-PKG-ATIVCRIT"

    # carpinteiro cadastrado na 002.L1 — nao gera mais pendencia de cargo
    assert ctx.pendencias == []
