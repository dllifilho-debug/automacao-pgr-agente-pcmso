"""D-ARQ-91 (emenda de 07/10/2026) — riscos que constam no ASO, por risco do GHE
(R-ASO-02..07). Cada teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.sugestao_aso import sugerir_aso
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    ExameEmitido,
    Motivo,
    OrigemRisco,
    Quantificacao,
    RelatorioASO,
    Risco,
    RiscoPGR,
    SugestaoASO,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 7, 1)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def vocab(proto: Protocolo) -> dict[str, Any]:
    return proto.vocabulario.agentes


def _q(valor: float | None, unidade: str | None, pct_lt: float | None = None) -> Quantificacao:
    return Quantificacao(
        valor=valor, unidade=unidade, relacao_LT=None, pct_LT=pct_lt, apenas_qualitativa=False
    )


def _risco(
    agente: str,
    nivel: str | None = None,
    q: Quantificacao | None = None,
    *,
    aiha: bool = False,
    ototoxico: bool = False,
) -> Risco:
    return Risco(
        agente=agente,
        fonte="explicito",
        detalhe=None,
        quantificacao=q,
        tipo_ibe=None,
        is_ototoxico=ototoxico,
        nivel_risco=nivel,
        avaliacao_qualitativa_aiha=aiha,
    )


def _relatorio(vocab: dict[str, Any], *riscos: Risco, riscos_pgr: tuple[RiscoPGR, ...] = ()) -> RelatorioASO:
    return sugerir_aso([], riscos, riscos_pgr, vocab)


def _do(relatorio: RelatorioASO, risco: str) -> SugestaoASO:
    (s,) = [s for s in relatorio.riscos if s.risco == risco]
    return s


def _regras(s: SugestaoASO) -> set[str]:
    return {c.regra for c in s.criterios if c.veredito == s.veredito}


def test_poeira_mineral_consta_mesmo_baixo_e_ate_10(vocab: dict[str, Any]) -> None:
    # Reversão: tirar a sílica de `_POEIRA_MINERAL` — sílica BAIXO a 5% do LEO
    # sai NAO_CONSTA pelos critérios de cancerígeno e geral.
    s = _do(_relatorio(vocab, _risco("silica", "BAIXO", _q(0.002, "mg/m3", pct_lt=5.0))), "silica")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-02"})


def test_altura_consta_e_consigna_aptidao(vocab: dict[str, Any]) -> None:
    # Reversões: remover `trabalho_altura` de `_APTIDAO_NR` (BAIXO → NAO_CONSTA);
    # remover o cálculo de `aptidoes` em sugerir_aso (tupla vazia).
    relatorio = _relatorio(vocab, _risco("trabalho_altura", "BAIXO"))
    s = _do(relatorio, "trabalho_altura")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-03"})
    assert len(relatorio.aptidoes) == 1 and "NR-35 item 35.4.4.1" in relatorio.aptidoes[0]


def test_motorista_segue_regra_geral(vocab: dict[str, Any]) -> None:
    # Reversão: incluir `motorista_equipamento_pesado` em `_APTIDAO_NR` — BAIXO
    # passaria a CONSTA.
    s = _do(_relatorio(vocab, _risco("motorista_equipamento_pesado", "BAIXO")), "motorista_equipamento_pesado")
    assert s.veredito == "NAO_CONSTA"
    assert "monitoramento desde a classificação baixa" in s.criterios[0].texto


def test_acidente_moderado_consta_pela_leitura_literal(vocab: dict[str, Any]) -> None:
    # Reversão: restringir `_criterio_geral` a agentes com exame na matriz (ou a
    # agentes químicos) — eletricidade MODERADO, sem exame, sairia NAO_CONSTA.
    s = _do(_relatorio(vocab, _risco("eletricidade", "MODERADO")), "eletricidade")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-06"})
    assert s.exames == ()


def test_cancerigeno_sem_avaliacao_ambiental_consta(vocab: dict[str, Any]) -> None:
    # Reversão: remover a chamada a `_criterio_cancerigeno` — benzeno BAIXO sem
    # medição sai NAO_CONSTA pela regra geral.
    s = _do(_relatorio(vocab, _risco("benzeno", "BAIXO")), "benzeno")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-04"})


def test_cancerigeno_acima_de_10_pct_consta(vocab: dict[str, Any]) -> None:
    # Reversão: subir `_PCT_CANCERIGENO` de 10 para 50 — 15% do limite deixa de constar.
    s = _do(_relatorio(vocab, _risco("benzeno", "BAIXO", _q(0.15, "ppm", pct_lt=15.0))), "benzeno")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-04"})


def test_cancerigeno_ate_10_pct_nao_consta_por_anexo_v(vocab: dict[str, Any]) -> None:
    # Reversão: tratar toda medição de cancerígeno como "sem avaliação ambiental"
    # (`_sem_avaliacao_ambiental` devolvendo True) — 8% passaria a CONSTA.
    s = _do(_relatorio(vocab, _risco("benzeno", "BAIXO", _q(0.08, "ppm", pct_lt=8.0))), "benzeno")
    assert s.veredito == "NAO_CONSTA"


def test_quimico_baixo_com_medicao_acima_do_nivel_de_acao_consta(vocab: dict[str, Any]) -> None:
    # Reversão: remover a chamada a `_medicao_acima_nivel_acao` em `_criterio_geral`
    # — tolueno BAIXO a 64% do LT (50/78 ppm) sai NAO_CONSTA.
    s = _do(_relatorio(vocab, _risco("tolueno", "BAIXO", _q(50.0, "ppm"))), "tolueno")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-06"})


def test_quimico_baixo_abaixo_do_nivel_de_acao_nao_consta(vocab: dict[str, Any]) -> None:
    # Reversão: inverter o teste de `abaixo_nivel_acao` em `_medicao_acima_nivel_acao`
    # — 26% do LT (20/78 ppm) passaria a CONSTA.
    s = _do(_relatorio(vocab, _risco("tolueno", "BAIXO", _q(20.0, "ppm"))), "tolueno")
    assert s.veredito == "NAO_CONSTA"


def test_moderado_consta(vocab: dict[str, Any]) -> None:
    # Reversão: piso de `_NIVEL_MODERADO` em "ALTO" — MODERADO sai NAO_CONSTA.
    s = _do(_relatorio(vocab, _risco("tolueno", "MODERADO")), "tolueno")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-06"})


def test_aiha_sem_nivel_sai_conferir(vocab: dict[str, Any]) -> None:
    # Reversão: `_criterio_geral` tratar `nivel_risco is None` como NAO_CONSTA
    # — o risco do grid AIHA sumiria da conferência (D-ARQ-22).
    s = _do(_relatorio(vocab, _risco("tolueno", None, aiha=True)), "tolueno")
    assert s.veredito == "CONFERIR"
    assert "AIHA" in s.criterios[0].texto


def test_varias_linhas_do_mesmo_agente_basta_uma_constar(vocab: dict[str, Any]) -> None:
    # Reversão: avaliar só o primeiro risco do agente em `_criterios_do_agente`
    # (ou deixar NAO_CONSTA à frente de CONSTA em `_PRIORIDADE`) — a linha
    # MODERADO, segunda do PGR, deixaria de fazer o tolueno constar.
    relatorio = _relatorio(vocab, _risco("tolueno", "BAIXO"), _risco("tolueno", "MODERADO"))
    assert [s.risco for s in relatorio.riscos] == ["tolueno"]
    assert relatorio.riscos[0].veredito == "CONSTA"


def test_ruido_baixo_com_ototoxico_consta(vocab: dict[str, Any]) -> None:
    # Reversão: tirar `and agravante` da perna BAIXO de `_criterio_ruido` (ou o
    # agravante inteiro) — ruído BAIXO + tolueno BAIXO sai NAO_CONSTA.
    relatorio = _relatorio(vocab, _risco("ruido", "BAIXO"), _risco("tolueno", "BAIXO", ototoxico=True))
    s = _do(relatorio, "ruido")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-05"})


def test_ruido_baixo_com_vibracao_consta(vocab: dict[str, Any]) -> None:
    # Reversão: tirar `r.agente in _VIBRACAO` do agravante — ruído BAIXO +
    # vibração BAIXO sai NAO_CONSTA.
    relatorio = _relatorio(vocab, _risco("ruido", "BAIXO"), _risco("vibracao_mao_braco", "BAIXO"))
    s = _do(relatorio, "ruido")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-05"})


def test_ruido_baixo_medido_em_80_consta(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo de medição (`relacao in _RUIDO_ACIMA_ACAO`) — 80 dB(A)
    # com classificação BAIXO e sem agravante sai NAO_CONSTA.
    s = _do(_relatorio(vocab, _risco("ruido", "BAIXO", _q(80.0, "dB(A)"))), "ruido")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-05"})


def test_ruido_baixo_isolado_nao_consta(vocab: dict[str, Any]) -> None:
    # Reversão: na perna BAIXO, trocar `nivel == "BAIXO" and agravante` por
    # `nivel == "BAIXO"` — ruído BAIXO a 75 dB(A), sem agravante, passaria a CONSTA.
    s = _do(_relatorio(vocab, _risco("ruido", "BAIXO", _q(75.0, "dB(A)"))), "ruido")
    assert s.veredito == "NAO_CONSTA"


def test_vibracao_acima_do_nivel_de_acao_consta(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo `_NIVEL_ACAO_VIBRACAO` de `_medicao_acima_nivel_acao`
    # — aren 3 m/s² em mãos e braços com BAIXO sai NAO_CONSTA.
    s = _do(_relatorio(vocab, _risco("vibracao_mao_braco", "BAIXO", _q(3.0, "m/s2"))), "vibracao_mao_braco")
    assert (s.veredito, _regras(s)) == ("CONSTA", {"R-ASO-06"})


def test_termo_nao_reconhecido_sai_conferir(vocab: dict[str, Any]) -> None:
    # Reversão: remover o laço dos `riscos_pgr` com `agente is None` em sugerir_aso
    # — o termo some do relatório (D-ARQ-22).
    termo = RiscoPGR(tipo="", agente=None, quantificacao=None, severidade=None, termo="Poeira de gesso acartonado")
    relatorio = _relatorio(vocab, _risco("tolueno", "BAIXO"), riscos_pgr=(termo,))
    s = _do(relatorio, "Poeira de gesso acartonado")
    assert (s.reconhecido, s.veredito) == (False, "CONFERIR")


def test_inexistencia_so_quando_tudo_nao_consta(vocab: dict[str, Any]) -> None:
    # Reversões: `inexistencia = True` fixo (o 2º relatório, com um CONFERIR, a
    # afirmaria sem prova); `inexistencia = False` fixo (o 1º não a sugeriria).
    assert _relatorio(vocab, _risco("tolueno", "BAIXO")).inexistencia is True
    assert _relatorio(vocab, _risco("tolueno", "BAIXO"), _risco("xileno", None)).inexistencia is False


def test_exames_informativos_vem_da_origem_na_matriz(vocab: dict[str, Any]) -> None:
    # Reversão: `exames = ()` fixo em sugerir_aso — o ortocresol do tolueno some.
    linha = ExameEmitido(
        exame="ortocresol_urina",
        periodicidade_meses=12,
        motivos=[Motivo("R-BIO-04-tolueno", "tolueno", None, None, origens=(OrigemRisco("tolueno", "tolueno", "PGR"),))],
    )
    relatorio = sugerir_aso([linha], [_risco("tolueno", "MODERADO")], (), vocab)
    assert _do(relatorio, "tolueno").exames == ("ortocresol_urina",)


def test_orquestrador_leva_sugestao_para_a_matriz(proto: Protocolo) -> None:
    # Reversão: remover a atribuição de `matriz.sugestao_aso` em executar — a
    # matriz sai com o RelatorioASO vazio do default.
    ghe = GHEPGR(
        id="GHE-01",
        nome="ALVENARIA",
        cargos=("Pedreiro",),
        riscos=(
            RiscoPGR(tipo="", agente="ruido", quantificacao=None, severidade=None, nivel_risco="MODERADO"),
        ),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2026, 12, 31), assinatura_engenheiro=True, ghes=(ghe,))

    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes

    s = _do(matriz.sugestao_aso, "ruido")
    assert s.veredito == "CONSTA"
    assert "audiometria" in s.exames
