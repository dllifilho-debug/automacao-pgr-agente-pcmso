from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.estagios.consolidacao import ConflitoProtocolo
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


def _risco_nao_resolvido(causa: str) -> RiscoPGR:
    return RiscoPGR(
        tipo="", agente=None, quantificacao=None, severidade=None, causa_nao_resolucao=causa
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


# ---------------------------------------------------------------------------
# quando_ausente: {presumir_true: [...]} (D-ARQ-68 cl.5) — presunção protetiva
# sai de BLOQUEADA (linha determinada) mas nunca alcança VÁLIDA.
# ---------------------------------------------------------------------------


def test_presumir_true_sai_de_bloqueada_com_linha_de_risco() -> None:
    # Teste 10: reversão que mata — remover presumir_true da regra (volta ao
    # ramo Ausente simples, bloqueante, sem linha nenhuma).
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    protocolo = _protocolo_ausente(quando_ausente={"presumir_true": ["ruido_acima_acao"]})
    resultado = executar(pgr, protocolo, hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.status != "BLOQUEADA"
    assert len(linhas_de_risco(matriz.linhas)) >= 1


def test_presumir_true_nunca_sai_valida_mesmo_sem_outro_bloqueio() -> None:
    # Teste 11: reversão que mata — remover a guarda de 2c (orquestrador),
    # deixando `not tem_bloqueio` sozinho decidir VÁLIDA.
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    protocolo = _protocolo_ausente(quando_ausente={"presumir_true": ["ruido_acima_acao"]})
    resultado = executar(pgr, protocolo, hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.status == "PARCIAL"


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
    assert len(matriz.linhas) == 8
    nomes = {e.exame.strip().lower() for e in matriz.linhas}
    assert nomes == {
        "hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg", "exame_clinico",
        "avaliacao_psicossocial", "avaliacao_saude_mental",
    }
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


def _protocolo_ou_absorvido_sem_emite() -> Protocolo:
    return Protocolo(
        vocabulario=_vocab(),
        predicados_compostos={},
        regras=[
            {
                "id": "R-TESTE-ABSORVIDO-VAZIO",
                "quando": {"ou": ["ruido_acima_acao", "altura"]},
                "emite": [],
            }
        ],
        regimes={},
    )


def test_pendencia_nao_bloqueante_sem_match_fica_na_matriz_valida() -> None:
    # Estado que o pipeline real NUNCA produz: exames_alvo deriva de regra["emite"],
    # e a pendência só nasce quando a regra emite — logo a âncora sempre casa uma
    # linha presente. "Não-bloqueante com âncora que não casa" é estruturalmente
    # inalcançável em produção; fabricado aqui via 'emite: []' (mesma categoria de
    # test_violacao_fabricada_e_detectada em test_invariante_piso_teto.py, D-ARQ-31
    # fatia 4) — sem este caso sintético, o fallback de matriz (sem anexação) jamais
    # seria exercitado no vermelho.
    ghe = _ghe(riscos=(_risco("ruido"), _risco("trabalho_altura")))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ou_absorvido_sem_emite(), hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    assert matriz.status == "VÁLIDA"
    assert any(
        p.tipo == "perna_ausente_absorvida" and not p.bloqueante for p in matriz.pendencias
    )
    assert all(not ln.pendencias_anexadas for ln in matriz.linhas)


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
    # Usa vibração genérica (não ruído): desde D-ARQ-68 cl.5 (003.EZ), ruído
    # sem quantificação deixou de bloquear puro — R-AUD-01/02 presumem e emitem
    # (ver test_raud01_raud02_presuncao_promove_bloqueada_para_parcial_com_linha_de_risco).
    # Vibração genérica não tem quando_ausente.presumir_true declarado e segue
    # bloqueando puro — preserva o invariante original deste teste (c).
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=(_risco("vibracao"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "exame_clinico" in nomes, "linha do clínico deve estar presente"
    assert linhas_de_risco(matriz.linhas) == [], "nenhuma linha de risco determinada"
    assert matriz.status == "BLOQUEADA"


# ---------------------------------------------------------------------------
# D-ARQ-71 cl.2/cl.3 — pendência não-bloqueante anexada não derruba VÁLIDA
# ---------------------------------------------------------------------------


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
            }
        ],
        regimes={},
    )


def test_ghe_valida_com_pendencia_nao_bloqueante_anexada() -> None:
    # Sem o fix de tem_anexada (D-ARQ-71 cl.3), esta GHE cairia para PARCIAL só por
    # ter uma pendência não-bloqueante anexada — o bug latente nomeado pelo Arquiteto.
    ghe = _ghe(riscos=(_risco("ruido"), _risco("trabalho_altura")))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ou_absorvido(), hoje=HOJE)
    assert resultado.status == "OK"
    matriz = resultado.matrizes[0]
    assert matriz.status == "VÁLIDA"
    assert len(matriz.linhas) == 1
    audiometria = matriz.linhas[0]
    assert len(audiometria.pendencias_anexadas) == 1
    assert audiometria.pendencias_anexadas[0].tipo == "perna_ausente_absorvida"
    assert audiometria.pendencias_anexadas[0].bloqueante is False
    assert not any(p.bloqueante for p in matriz.pendencias)


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


# ---------------------------------------------------------------------------
# R-AUD-04 — audiometria como piso universal, com demissional (003.EX fatia 1).
# NR-07 Anexo II 4.1 crava 12M+adm+dem; universo estendido a todo trabalhador e
# MR incluído são [INTERPRETADO], apoiados em matriz-precedente (003.EX fatia 0).
# Usa o protocolo real porque R-AUD-04 é a regra sob teste, não um fixture
# sintético — e porque o teste 3 precisa do dedup real com R-PKG-ATIVCRIT.
# ---------------------------------------------------------------------------


# R-AUD-04 foi DEPRECATED em 003.EZ (D-ARQ-81 — fundamento refutado por
# DT-003EY-01: universalidade medida em 7/23 obras, não convergência). Os três
# testes que cravavam o piso incondicional (audiometria sem risco, DEM via
# R-AUD-04, dedup com R-PKG-ATIVCRIT+R-AUD-04) morrem por desenho — a conduta
# que eles protegiam foi retirada, não sucedida. O quarto inverte: ver abaixo.


def test_raud01_raud02_presuncao_promove_bloqueada_para_parcial_com_linha_de_risco() -> None:
    # Sucede test_raud04_nao_promove_bloqueada_para_parcial (003.EX/003.EZ).
    # Sob D-ARQ-68 cl.5, ruído sem quantificação deixou de bloquear R-AUD-01/02
    # — a presunção protetiva declarada em quando_ausente.presumir_true emite
    # audiometria (adm/per/MR/dem) com pendência não-bloqueante. As duas
    # asserções do teste antigo (linhas_de_risco == [] e status == "BLOQUEADA")
    # viram o contrário: reversão que mata — remover presumir_true de R-AUD-01
    # e R-AUD-02 no regras.yaml.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=(_risco("ruido"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    nomes = {ln.exame for ln in matriz.linhas}
    assert "audiometria" in nomes
    assert linhas_de_risco(matriz.linhas) != []
    assert matriz.status == "PARCIAL"
    assert any(
        p.tipo == "predicado_ausente_presumido"
        for ln in matriz.linhas
        for p in ln.pendencias_anexadas
    ) or any(p.tipo == "predicado_ausente_presumido" for p in matriz.pendencias)


# ---------------------------------------------------------------------------
# R-PSY-02 — psicossocial incondicional (003.EN). Sucede R-PSY-01 (DEPRECATED,
# condicionada). NR-01 1.5.3.1.4/1.5.3.2.1/1.5.4.4.5.3. Usa o protocolo real
# porque R-PSY-02 é a regra sob teste, não um fixture sintético.
# ---------------------------------------------------------------------------

_MOMENTOS_PSY = {Momento.ADM, Momento.PER, Momento.MR}


def test_rpsy02_emite_psicossocial_e_saude_mental_12m_sem_risco() -> None:
    # GHE sem nenhum risco: R-PSY-02 é incondicional, deve emitir mesmo assim.
    proto = carregar(_PROTOCOLO_DIR)
    ghe = _ghe(riscos=())
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, proto, hoje=HOJE)
    matriz = resultado.matrizes[0]
    psicossocial = next(ln for ln in matriz.linhas if ln.exame == "avaliacao_psicossocial")
    saude_mental = next(ln for ln in matriz.linhas if ln.exame == "avaliacao_saude_mental")
    for linha in (psicossocial, saude_mental):
        assert linha.periodicidade_meses == 12
        assert linha.momentos == _MOMENTOS_PSY
        assert any(m.regra_id == "R-PSY-02" for m in linha.motivos)


# ---------------------------------------------------------------------------
# 003.EO fatia 1 — MatrizGHE ganha nome_ghe/cargos (D-ARQ-73), populados no
# orquestrador a partir de ctx.pgr_ghe em todos os sítios de construção.
# ---------------------------------------------------------------------------


def test_matriz_ghe_carrega_cargos_do_pgr() -> None:
    # Reversão que mata: remover `cargos=ctx.pgr_ghe.cargos` (e `nome_ghe=...`)
    # do ramo `else` (sucesso) do orquestrador -> volta ao default `()`/"" ->
    # asserção falha.
    ghe1 = GHEPGR(
        id="GHE-01",
        nome="Estrutura de Concreto",
        cargos=("Carpinteiro", "Ajudante de Carpintaria"),
        riscos=(_risco("trabalho_altura"),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ghe2 = GHEPGR(
        id="GHE-02",
        nome="Elétrica",
        cargos=("Eletricista",),
        riscos=(_risco("trabalho_altura"),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = _pgr(ghes=(ghe1, ghe2))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)

    m1 = next(m for m in resultado.matrizes if m.ghe_id == "GHE-01")
    m2 = next(m for m in resultado.matrizes if m.ghe_id == "GHE-02")

    assert m1.nome_ghe == "Estrutura de Concreto"
    assert m1.cargos == ("Carpinteiro", "Ajudante de Carpintaria")
    assert m2.nome_ghe == "Elétrica"
    assert m2.cargos == ("Eletricista",)


def test_matriz_bloqueada_tambem_carrega_cargos(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: remover `cargos=ctx.pgr_ghe.cargos` (e `nome_ghe=...`)
    # do ramo `except ConflitoProtocolo` do orquestrador -> o teste do ramo
    # feliz (acima) continua verde e só este cai. Este é o motivo de existir
    # um 2º teste: o 1º não discrimina o sítio esquecido.
    #
    # DT-003EE-01: após D-ARQ-39, `stage_8_consolidacao` não levanta mais
    # `ConflitoProtocolo` em produção (grep `raise ConflitoProtocolo` = zero
    # no repo) — o ramo `except` do orquestrador é código morto alcançável só
    # por injeção controlada. Forçamos aqui via monkeypatch para exercitar o
    # ramo diretamente; não afirma que o pipeline real o alcança.
    def _consolidacao_explode(exames: list[Any]) -> list[Any]:
        raise ConflitoProtocolo("conflito fabricado para teste")

    monkeypatch.setattr(
        "agente_medico.motor.orquestrador.stage_8_consolidacao", _consolidacao_explode
    )

    ghe = GHEPGR(
        id="GHE-09",
        nome="Armação",
        cargos=("Armador",),
        riscos=(_risco("trabalho_altura"),),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)

    matriz = resultado.matrizes[0]
    assert matriz.status == "BLOQUEADA"
    assert matriz.nome_ghe == "Armação"
    assert matriz.cargos == ("Armador",)


# ---------------------------------------------------------------------------
# D-ARQ-82 — o selo VÁLIDA computa sobre a CAUSA da não-resolução de um termo,
# nunca sobre sua contagem. cl.1 exige ausência de LACUNA; cl.2 (emendada em
# 003.FC) fecha a lista de causas-acerto em fracao_sem_agente só.
# ---------------------------------------------------------------------------


def test_ghe_valida_com_unico_termo_nao_resolvido_por_fracao_sem_agente() -> None:
    # T2 (003.FC): reversão que mata — remover "fracao_sem_agente" do
    # frozenset CAUSAS_ACERTO_NAO_RESOLUCAO em orquestrador.py. É o teste que
    # D-ARQ-83 (Consequência) exige que exista.
    ghe = _ghe(riscos=(_risco_nao_resolvido("fracao_sem_agente"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    assert resultado.matrizes[0].status == "VÁLIDA"


def test_ghe_com_termo_lacuna_e_linha_de_risco_sai_parcial_nao_valida() -> None:
    # T3 (003.FC), cl.1: risco resolvido (trabalho_altura -> 5 linhas via
    # R-PKG-ATIVCRIT) + termo não resolvido por LACUNA (vocabulario_ausente)
    # na mesma GHE. Reversão que mata — remover `and not tem_lacuna` do gate
    # de VÁLIDA em orquestrador.py: sem ela este GHE sairia VÁLIDA (o
    # tem_bloqueio/tem_presumida antigos não veem essa lacuna).
    ghe = _ghe(
        riscos=(_risco("trabalho_altura"), _risco_nao_resolvido("vocabulario_ausente"))
    )
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert len(matriz.linhas) == 5
    assert matriz.status == "PARCIAL"


def test_ghe_so_com_termo_lacuna_sem_linha_de_risco_sai_bloqueada() -> None:
    # T4 (003.FC), cl.5 braço BLOQUEADA: termo declarado, não resolvido por
    # LACUNA, nenhuma linha de risco determinada (a regra do protocolo
    # sintético não dispara sem um risco resolvido). Reversão que mata —
    # mesma do T3: remover `and not tem_lacuna` faria este GHE sair VÁLIDA
    # em vez de BLOQUEADA (tem_bloqueio e tem_presumida são ambos False aqui).
    ghe = _ghe(riscos=(_risco_nao_resolvido("vocabulario_ausente"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.linhas == []
    assert matriz.status == "BLOQUEADA"


def test_ghe_sem_risco_declarado_segue_valida_vacuamente() -> None:
    # T5 (003.FC), cl.6: GHE sem risco algum satisfaz a cláusula 1
    # vacuamente. Reversão que mata — trocar
    # `tem_lacuna = any(... for r in ghe.riscos if r.agente is None)` por
    # `tem_lacuna = not ghe.riscos or any(...)`, tratando ausência de risco
    # como lacuna em vez de vacuidade.
    ghe = _ghe(riscos=())
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.status == "VÁLIDA"


def test_ghe_com_unico_termo_fuzzy_recusado_nao_sai_valida() -> None:
    # T6 (003.FC) — emenda 003.FC travada por teste: fuzzy_recusado é LACUNA,
    # não causa-acerto, desde a emenda que a medição de abertura do Fascino
    # forçou (caso Metiletilcetona -> R-BIO-04, conduta devida perdida se
    # este tipo voltasse a ser causa-acerto). Reversão que mata — devolver
    # "fuzzy_recusado" ao frozenset CAUSAS_ACERTO_NAO_RESOLUCAO.
    ghe = _ghe(riscos=(_risco_nao_resolvido("fuzzy_recusado"),))
    pgr = _pgr(ghes=(ghe,))
    resultado = executar(pgr, _protocolo_ativcrit(), hoje=HOJE)
    matriz = resultado.matrizes[0]
    assert matriz.status != "VÁLIDA"
    assert matriz.status == "BLOQUEADA"
