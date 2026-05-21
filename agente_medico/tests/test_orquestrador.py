from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, Vocabulario, carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

HOJE = date(2026, 5, 21)


def _pgr(
    validade: date = HOJE - timedelta(days=30),
    assinatura: bool = True,
    ghes: tuple[GHEPGR, ...] = (),
) -> PGR:
    return PGR(validade=validade, assinatura_engenheiro=assinatura, ghes=ghes)


def _ghe(ghe_id: str = "GHE-01", riscos: tuple[RiscoPGR, ...] = ()) -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome="Teste",
        cargos=(),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _risco(agente: str) -> RiscoPGR:
    return RiscoPGR(tipo="fisico", agente=agente, quantificacao=None, severidade=None)


def _vocab() -> Vocabulario:
    return Vocabulario(agentes={}, cargos={}, exames={}, epis={})


def _protocolo_ativcrit() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "maquina_pesada"]}
        },
        regras=[
            {
                "id": "R-PKG-ATIVCRIT",
                "quando": "atividade_critica",
                "emite": [
                    {"exame": "hemograma", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "glicemia", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "audiometria", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "acuidade_visual", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "ecg", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                ],
            }
        ],
        regimes={},
    )


def _protocolo_ausente(quando_ausente: Any = None) -> Protocolo:
    regra: dict[str, Any] = {
        "id": "R-TESTE-AUSENTE",
        "quando": "ruido_acima_acao",
        "emite": [{"exame": "audiometria", "periodicidade_meses": 12, "momentos": ["adm"]}],
    }
    if quando_ausente is not None:
        regra["quando_ausente"] = quando_ausente
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[regra],
        regimes={},
    )


def _protocolo_misto() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "maquina_pesada"]}
        },
        regras=[
            {
                "id": "R-PKG-ATIVCRIT",
                "quando": "atividade_critica",
                "emite": [
                    {"exame": "hemograma", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "glicemia", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "audiometria", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "acuidade_visual", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                    {"exame": "ecg", "periodicidade_meses": 12, "momentos": ["adm", "per", "MR"]},
                ],
            },
            {
                "id": "R-TESTE-AUSENTE",
                "quando": "ruido_acima_acao",
                "emite": [{"exame": "audiometria", "periodicidade_meses": 12, "momentos": ["adm"]}],
            },
        ],
        regimes={},
    )


def _protocolo_conflito() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[
            {
                "id": "R-CONFLITO-A",
                "quando": "altura",
                "emite": [{"exame": "hemograma", "periodicidade_meses": 12, "momentos": ["adm"]}],
            },
            {
                "id": "R-CONFLITO-B",
                "quando": "altura",
                "emite": [{"exame": "hemograma", "periodicidade_meses": 6, "momentos": ["per"]}],
            },
        ],
        regimes={},
    )


# ---------------------------------------------------------------------------
# Testes de rejeição (Stage 1)
# ---------------------------------------------------------------------------


def test_pgr_nao_assinado_rejeitado() -> None:
    pgr = _pgr(assinatura=False, ghes=(_ghe(riscos=(_risco("trabalho_altura"),)),))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    assert resultado.status == "REJEITADO"
    assert resultado.matrizes == []
    assert any(p.tipo == "assinatura_invalida" for p in resultado.pendencias_globais)
    assert resultado.motivo_rejeicao is not None
    assert "assinatura_invalida" not in resultado.motivo_rejeicao or "PGR" in resultado.motivo_rejeicao


def test_pgr_vencido_rejeitado() -> None:
    pgr = _pgr(validade=HOJE - timedelta(days=730), ghes=(_ghe(),))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    assert resultado.status == "REJEITADO"
    assert resultado.matrizes == []
    assert resultado.motivo_rejeicao is not None
    assert any(p.tipo == "pgr_vencido" for p in resultado.pendencias_globais)


# ---------------------------------------------------------------------------
# Testes de fluxo normal (Stages 2-8)
# ---------------------------------------------------------------------------


def test_ghe_sem_bloqueio_ok() -> None:
    ghe = _ghe(riscos=(_risco("trabalho_altura"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    assert resultado.status == "OK"
    assert len(resultado.matrizes) == 1
    assert len(resultado.matrizes[0].linhas) == 5
    assert resultado.motivo_rejeicao is None


def test_predicado_ausente_bloqueia_ghe() -> None:
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ausente(), hoje=HOJE)
    assert resultado.status == "PRELIMINAR"
    assert len(resultado.matrizes) == 1
    matriz = resultado.matrizes[0]
    assert matriz.linhas == []
    assert any(p.bloqueante and p.tipo == "predicado_ausente" for p in matriz.pendencias)


def test_quando_ausente_false_nao_bloqueia() -> None:
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ausente(quando_ausente=False), hoje=HOJE)
    assert resultado.status == "OK"
    assert len(resultado.matrizes) == 1
    assert not any(p.bloqueante for p in resultado.matrizes[0].pendencias)


def test_dois_ghes_um_bloqueia() -> None:
    ghe1 = _ghe(ghe_id="GHE-01", riscos=(_risco("trabalho_altura"),))
    ghe2 = _ghe(ghe_id="GHE-02", riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe1, ghe2))
    resultado = executar(pgr, _protocolo_misto(), hoje=HOJE)

    assert resultado.status == "PRELIMINAR"
    assert len(resultado.matrizes) == 2

    m1 = next(m for m in resultado.matrizes if m.ghe_id == "GHE-01")
    m2 = next(m for m in resultado.matrizes if m.ghe_id == "GHE-02")

    assert len(m1.linhas) == 5
    assert not any(p.bloqueante for p in m1.pendencias)

    assert m2.linhas == []
    assert any(p.bloqueante for p in m2.pendencias)


# ---------------------------------------------------------------------------
# Teste de integração end-to-end (protocolo real em disco)
# ---------------------------------------------------------------------------


def test_integracao_end_to_end() -> None:
    ghe = GHEPGR(
        id="GHE-01",
        nome="Trabalho em estrutura",
        cargos=("carpinteiro",),
        riscos=(RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(
        validade=HOJE - timedelta(days=30),
        assinatura_engenheiro=True,
        ghes=(ghe,),
    )
    proto = carregar(_PROTOCOLO_DIR)
    resultado = executar(pgr, proto, hoje=HOJE)

    assert resultado.status == "OK"
    assert len(resultado.matrizes) == 1
    matriz = resultado.matrizes[0]
    assert len(matriz.linhas) == 5
    nomes = {e.exame.strip().lower() for e in matriz.linhas}
    assert nomes == {"hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg"}
    for e in matriz.linhas:
        assert e.periodicidade_meses == 12


# ---------------------------------------------------------------------------
# Teste de conflito de protocolo
# ---------------------------------------------------------------------------


def test_conflito_protocolo_vira_pendencia() -> None:
    ghe = _ghe(riscos=(_risco("trabalho_altura"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_conflito(), hoje=HOJE)

    assert resultado.status == "PRELIMINAR"
    assert len(resultado.matrizes) == 1
    matriz = resultado.matrizes[0]
    assert matriz.linhas == []
    assert any(p.tipo == "conflito_protocolo" and p.bloqueante for p in matriz.pendencias)
