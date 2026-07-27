from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, Vocabulario, carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    Momento,
    PGR,
    RiscoPGR,
)
from agente_medico.tests.invariantes import linhas_de_risco

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
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}
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
            "atividade_critica": {"ou": ["altura", "espaco_confinado", "motorista_equipamento_pesado"]}
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
    assert len(matriz.linhas) == 6
    nomes = {e.exame.strip().lower() for e in matriz.linhas}
    assert nomes == {"hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg", "exame_clinico"}
    for e in matriz.linhas:
        assert e.periodicidade_meses == 12


# ---------------------------------------------------------------------------
# Teste de periodicidade divergente no mesmo exame (D-ARQ-39: piso, não conflito)
# ---------------------------------------------------------------------------


def test_periodicidade_divergente_resolve_por_piso() -> None:
    """
    D-ARQ-39: duas regras convergindo no mesmo exame com periodicidades
    distintas (R-CONFLITO-A 12M / R-CONFLITO-B 6M) não bloqueiam mais o GHE
    via ConflitoProtocolo — resolvem por piso (mínimo). Substitui
    test_conflito_protocolo_vira_pendencia (comportamento antigo removido).
    """
    ghe = _ghe(riscos=(_risco("trabalho_altura"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_conflito(), hoje=HOJE)

    assert resultado.status == "OK"
    assert len(resultado.matrizes) == 1
    matriz = resultado.matrizes[0]
    assert matriz.status == "VÁLIDA"
    assert not any(p.tipo == "conflito_protocolo" for p in matriz.pendencias)
    assert len(matriz.linhas) == 1
    linha = matriz.linhas[0]
    assert linha.exame == "hemograma"
    assert linha.periodicidade_meses == 6
    assert linha.momentos == {Momento.ADM, Momento.PER}


# ---------------------------------------------------------------------------
# D-ARQ-31 fatia 2 — produtor de status tri-estado por-GHE
# ---------------------------------------------------------------------------


def test_ghe_status_valida() -> None:
    # D-ARQ-31 fatia 2: GHE sem bloqueio → VÁLIDA.
    ghe = _ghe(riscos=(_risco("trabalho_altura"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    assert resultado.matrizes[0].status == "VÁLIDA"


def test_ghe_status_bloqueada_sem_linhas() -> None:
    # D-ARQ-31 fatia 2: bloqueio + nenhum exame determinável → BLOQUEADA.
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ausente(), hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.linhas == []
    assert matriz.status == "BLOQUEADA"


def test_ghe_parcial_linhas_presentes_com_bloqueio() -> None:
    # D-ARQ-31 fatia 2 (falha-sem/passa-com): risco emissor (trabalho_altura →
    # R-PKG-ATIVCRIT, 5 exames) + risco bloqueante (ruido → ruido_acima_acao
    # Ausente) na MESMA GHE. Antes: linhas zeradas (BLOQUEADA falso).
    # Depois: PARCIAL com linhas. Fixtures ancoradas em test_ghe_sem_bloqueio_ok
    # (trabalho_altura→5 linhas) + test_dois_ghes_um_bloqueia (ruido→Ausente).
    ghe = _ghe(riscos=(_risco("trabalho_altura"), _risco("ruido")))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_misto(), hoje=HOJE)
    assert resultado.status == "PRELIMINAR"
    assert len(resultado.matrizes) == 1
    matriz = resultado.matrizes[0]
    assert len(matriz.linhas) == 5
    assert matriz.status == "PARCIAL"
    # fatia 3: bloqueante do ruído anexado à linha audiometria, não solto na matriz
    audiometria = next(ln for ln in matriz.linhas if ln.exame == "audiometria")
    assert any(p.bloqueante for p in audiometria.pendencias_anexadas)
    assert not any(p.bloqueante for p in matriz.pendencias)


# ---------------------------------------------------------------------------
# R-CLI-01 — piso universal (003.EC). Usa o protocolo real (regras.yaml em
# disco) porque R-CLI-01 é a regra sob teste, não um fixture sintético.
# ---------------------------------------------------------------------------

_TODOS_MOMENTOS = {Momento.ADM, Momento.PER, Momento.MR, Momento.RT, Momento.DEM}


def test_rcli01_emite_exame_clinico_12m_5_momentos_sem_risco() -> None:
    # (a) GHE sem nenhum risco: R-CLI-01 é incondicional, deve emitir mesmo assim.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=())
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    clinico = next(ln for ln in matriz.linhas if ln.exame == "exame_clinico")
    assert clinico.periodicidade_meses == 12
    assert clinico.momentos == _TODOS_MOMENTOS
    assert matriz.status == "VÁLIDA"


def test_rcli01_emite_tambem_em_ghe_com_risco() -> None:
    # (b) R-CLI-01 não é exclusivo do GHE sem risco: convive com linhas de risco.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=(_risco("trabalho_altura"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "exame_clinico" in nomes
    assert len(linhas_de_risco(matriz.linhas)) >= 1, "deveria ter linhas de risco além do clínico"
    assert matriz.status == "VÁLIDA"


def test_rcli01_unico_risco_bloqueado_com_clinico_presente_fecha_bloqueada() -> None:
    # (c) fatia 2 (003.EC): a linha do clínico nunca falta, mas ela sozinha não
    # basta para tirar o GHE de BLOQUEADA quando o único risco não determinou nada.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "exame_clinico" in nomes, "linha do clínico deve estar presente"
    assert linhas_de_risco(matriz.linhas) == [], "nenhuma linha de risco determinada"
    assert matriz.status == "BLOQUEADA"


def test_rcli01_um_risco_determinado_mais_um_bloqueado_segue_parcial() -> None:
    # (d) mistura: trabalho_altura determina (R-PKG-ATIVCRIT, 5 linhas) e ruído
    # bloqueia (R-AUD-01 Ausente) na mesma GHE — o clínico soma, mas o status
    # continua PARCIAL, não VÁLIDA nem BLOQUEADA.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=(_risco("trabalho_altura"), _risco("ruido")))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "exame_clinico" in nomes
    assert len(linhas_de_risco(matriz.linhas)) >= 1
    assert matriz.status == "PARCIAL"
