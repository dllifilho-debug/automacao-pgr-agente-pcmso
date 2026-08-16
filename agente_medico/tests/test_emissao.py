from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.predicados import PredicadoDesconhecido
from agente_medico.motor.protocolo import Protocolo, Vocabulario, carregar
from agente_medico.motor.tipos import (
    Ausente,
    GHEContext,
    GHEPGR,
    Momento,
    PGR,
    Quantificacao,
    Risco,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def _ghe(ghe_id: str = "GHE-01") -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome="Teste",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _vocab() -> Vocabulario:
    return Vocabulario(agentes={}, cargos={}, exames={}, epis={})


def _protocolo_ativcrit() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}
        },
        regras=[
            {
                "id": "R-PKG-ATIVCRIT",
                "quando": "atividade_critica",
                "emite": [
                    {"exame": "hemograma",       "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "glicemia",        "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "audiometria",     "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "acuidade_visual", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "ecg",             "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                ],
                "base_normativa": "Protocolo Dra. Carolini",
                "status": "VALIDADO",
            }
        ],
        regimes={},
    )


def _protocolo_ausente(quando_ausente: Any = None) -> Protocolo:
    regra: dict[str, Any] = {
        "id": "R-TESTE-AUSENTE",
        "quando": "ruido_acima_acao",
        "emite": [
            {"exame": "teste", "periodicidade_meses": 12, "momentos": ["adm"]}
        ],
        "base_normativa": "teste",
        "status": "VALIDADO",
    }
    if quando_ausente is not None:
        regra["quando_ausente"] = quando_ausente
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[regra],
        regimes={},
    )


def _ctx_com_risco(agente: str, ghe_id: str = "GHE-01") -> GHEContext:
    risco = Risco(agente=agente, fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None)
    return GHEContext(pgr_ghe=_ghe(ghe_id), riscos=[risco])


def _ctx_ruido_sem_quantificacao(ghe_id: str = "GHE-01") -> GHEContext:
    risco = Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None)
    return GHEContext(pgr_ghe=_ghe(ghe_id), riscos=[risco])


def _protocolo_ou_absorvido() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[
            {
                "id": "R-TESTE-ABSORVIDO",
                "quando": {"ou": ["ruido_acima_acao", "altura"]},
                "emite": [
                    {"exame": "audiometria", "periodicidade_meses": 12, "momentos": ["adm"]}
                ],
                "base_normativa": "teste",
                "status": "VALIDADO",
            }
        ],
        regimes={},
    )


def _ctx_ruido_sem_quant_e_altura(ghe_id: str = "GHE-01") -> GHEContext:
    riscos = [
        Risco(agente="ruido", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
        Risco(agente="trabalho_altura", fonte="pgr", detalhe=None, quantificacao=None, tipo_ibe=None),
    ]
    return GHEContext(pgr_ghe=_ghe(ghe_id), riscos=riscos)


_MOMENTOS_ESPERADOS = {Momento.ADM, Momento.PER, Momento.MR}


def test_emite_pacote_atividade_critica_quando_altura_presente() -> None:
    ctx = _ctx_com_risco("trabalho_altura")
    result = stage_5_emissao(ctx, _protocolo_ativcrit())
    assert len(result) == 5
    for exame in result:
        assert exame.motivos[0].regra_id == "R-PKG-ATIVCRIT"
        assert exame.periodicidade_meses == 12
        assert exame.momentos == _MOMENTOS_ESPERADOS
    assert ctx.pendencias == []


def test_emite_pacote_atividade_critica_quando_espaco_confinado() -> None:
    ctx = _ctx_com_risco("espaco_confinado")
    result = stage_5_emissao(ctx, _protocolo_ativcrit())
    assert len(result) == 5
    for exame in result:
        assert exame.motivos[0].regra_id == "R-PKG-ATIVCRIT"
        assert exame.periodicidade_meses == 12
        assert exame.momentos == _MOMENTOS_ESPERADOS
    assert ctx.pendencias == []


def test_nao_emite_quando_nenhum_risco_critico() -> None:
    ctx = _ctx_com_risco("ruido")
    result = stage_5_emissao(ctx, _protocolo_ativcrit())
    assert result == []
    assert ctx.pendencias == []


def test_ausente_gera_pendencia_bloqueante_e_nao_emite() -> None:
    ctx = _ctx_ruido_sem_quantificacao()
    result = stage_5_emissao(ctx, _protocolo_ausente())
    assert result == []
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.tipo == "predicado_ausente"
    assert p.bloqueante is True
    assert p.regra_origem == "R-TESTE-AUSENTE"
    assert p.ghe_id == "GHE-01"


def test_quando_ausente_false_silencia_pendencia() -> None:
    ctx = _ctx_ruido_sem_quantificacao()
    result = stage_5_emissao(ctx, _protocolo_ausente(quando_ausente=False))
    assert result == []
    assert ctx.pendencias == []


# ---------------------------------------------------------------------------
# quando_ausente: {presumir_true: [...]} (D-ARQ-68 cl.5) — presunção protetiva
# declarada por primitivo nomeado.
# ---------------------------------------------------------------------------


def test_presumir_true_emite_e_pendencia_nao_bloqueante_nomeia_primitivo() -> None:
    # Teste 6: a linha emite e carrega Pendencia(tipo="predicado_ausente_presumido",
    # bloqueante=False) nomeando o primitivo presumido.
    ctx = _ctx_ruido_sem_quantificacao()
    proto = _protocolo_ausente(quando_ausente={"presumir_true": ["ruido_acima_acao"]})
    result = stage_5_emissao(ctx, proto)
    assert len(result) == 1
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.tipo == "predicado_ausente_presumido"
    assert p.bloqueante is False
    assert p.regra_origem == "R-TESTE-AUSENTE"
    assert p.ghe_id == "GHE-01"
    assert "ruido_acima_acao" in p.motivo


def test_presumir_true_com_pernas_ausentes_vazio_bloqueia(monkeypatch: pytest.MonkeyPatch) -> None:
    # Teste 8: conjunto vazio de pernas_ausentes não presume no escuro — bloqueia
    # como o ramo Ausente de sempre. Reversão que mata: presumir quando o
    # conjunto é vazio (remover a checagem `if nomes_faltantes and ...`).
    import agente_medico.motor.estagios.emissao as emissao_mod

    monkeypatch.setattr(emissao_mod, "pernas_ausentes", lambda expr, ctx, protocolo: ())
    ctx = _ctx_ruido_sem_quantificacao()
    proto = _protocolo_ausente(quando_ausente={"presumir_true": ["ruido_acima_acao"]})
    result = stage_5_emissao(ctx, proto)
    assert result == []
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.tipo == "predicado_ausente"
    assert p.bloqueante is True


def test_afirmacao_incompleta_silica_sem_fracao_continua_bloqueando() -> None:
    # Teste 9 (cl.3 permanece e vence): sílica com valor e pct_quartzo afirmados
    # mas fração ausente é afirmação incompleta, não silêncio — R-RX-01-adm não
    # declara presumir_true, então segue bloqueando como sempre (D-ARQ-68 cl.2/3
    # intactas; a presunção de cl.5 não se estende a regras sem a declaração).
    protocolo = carregar(_PROTOCOLO_DIR)
    q = Quantificacao(
        valor=1.0,
        unidade="mg/m3",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        pct_quartzo=5.0,
        fracao=None,
    )
    risco = Risco(agente="silica", fonte="pgr", detalhe=None, quantificacao=q, tipo_ibe=None)
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[risco])
    stage_5_emissao(ctx, protocolo)
    pendencias_rx = [p for p in ctx.pendencias if p.regra_origem == "R-RX-01-adm"]
    assert len(pendencias_rx) == 1
    assert pendencias_rx[0].tipo == "predicado_ausente"
    assert pendencias_rx[0].bloqueante is True


def test_predicado_desconhecido_propaga_excecao() -> None:
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=[])
    proto = Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[{
            "id": "R-TESTE",
            "quando": "predicado_inexistente",
            "emite": [{"exame": "teste", "periodicidade_meses": 12, "momentos": ["adm"]}],
        }],
        regimes={},
    )
    with pytest.raises(PredicadoDesconhecido):
        stage_5_emissao(ctx, proto)


# ---------------------------------------------------------------------------
# perna_ausente_absorvida (D-ARQ-71 cl.1): regra emite por outra perna do `ou`,
# mas a perna Ausente some do tri-estado — visibilidade via pendência não-bloqueante.
# ---------------------------------------------------------------------------


def test_perna_ausente_absorvida_gera_pendencia_nao_bloqueante() -> None:
    ctx = _ctx_ruido_sem_quant_e_altura()
    result = stage_5_emissao(ctx, _protocolo_ou_absorvido())
    assert len(result) == 1  # a regra emitiu — a perna 'altura' resolveu True
    assert len(ctx.pendencias) == 1
    p = ctx.pendencias[0]
    assert p.tipo == "perna_ausente_absorvida"
    assert p.bloqueante is False
    assert p.regra_origem == "R-TESTE-ABSORVIDO"
    assert p.ghe_id == "GHE-01"
    assert p.exames_alvo == ("audiometria",)


def test_perna_ausente_absorvida_motivo_nomeia_a_perna() -> None:
    # Teste 14: a pendência de emissao.py carrega o nome do predicado ausente no
    # motivo — não só a mensagem genérica de 823d467.
    ctx = _ctx_ruido_sem_quant_e_altura()
    stage_5_emissao(ctx, _protocolo_ou_absorvido())
    assert len(ctx.pendencias) == 1
    assert "'ruido_acima_acao'" in ctx.pendencias[0].motivo


def test_conversao_momento_case_insensitive() -> None:
    ctx = _ctx_com_risco("trabalho_altura")
    proto = Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura"]}
        },
        regras=[{
            "id": "R-TESTE-CI",
            "quando": "atividade_critica",
            "emite": [
                {"exame": "teste", "periodicidade_meses": 12, "momentos": ["ADM", "Per", "mr"]}
            ],
        }],
        regimes={},
    )
    result = stage_5_emissao(ctx, proto)
    assert len(result) == 1
    assert result[0].momentos == {Momento.ADM, Momento.PER, Momento.MR}


# ---------------------------------------------------------------------------
# Motivo.status_regra (D-ARQ-22 Parte B / DH-003EI-01 faceta 2, 003.EM fatia 0)
# ---------------------------------------------------------------------------


def test_protocolo_real_todo_motivo_tem_status_regra_valido() -> None:
    # Reversão que mata: remover status_regra=regra.get("status") de emissao.py
    # (todo Motivo emitido volta a ter status_regra is None).
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
    assert stage_1_gates(pgr) == []

    ghe = pgr.ghes[0]
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    result = stage_5_emissao(ctx, proto)

    assert len(result) > 0
    for exame in result:
        for motivo in exame.motivos:
            assert motivo.status_regra is not None
            assert motivo.status_regra in {"VALIDADO", "DERIVADO", "INTERPRETADO"}


def test_status_regra_propaga_valor_da_regra() -> None:
    # Reversão que mata: mesma de acima — remover a propagação em emissao.py.
    ctx = _ctx_com_risco("trabalho_altura")
    proto = Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}
        },
        regras=[
            {
                "id": "R-TESTE-INTERPRETADO",
                "quando": "atividade_critica",
                "emite": [
                    {"exame": "hemograma", "periodicidade_meses": 12, "momentos": ["adm"]},
                ],
                "base_normativa": "teste",
                "status": "INTERPRETADO",
            }
        ],
        regimes={},
    )
    result = stage_5_emissao(ctx, proto)
    assert len(result) == 1
    assert result[0].motivos[0].status_regra == "INTERPRETADO"


def test_status_regra_ausente_na_regra_nao_levanta() -> None:
    # Guarda: NÃO discrimina comportamento novo, passa com ou sem a fatia 0.
    # Existe para travar o contrato do default (status_regra: Optional[str] = None).
    ctx = _ctx_com_risco("trabalho_altura")
    proto = Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}
        },
        regras=[
            {
                "id": "R-TESTE-SEM-STATUS",
                "quando": "atividade_critica",
                "emite": [
                    {"exame": "hemograma", "periodicidade_meses": 12, "momentos": ["adm"]},
                ],
                "base_normativa": "teste",
            }
        ],
        regimes={},
    )
    result = stage_5_emissao(ctx, proto)
    assert len(result) == 1
    assert result[0].motivos[0].status_regra is None
