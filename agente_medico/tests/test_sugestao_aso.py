"""D-ARQ-91 — sugestão de exames para o ASO (R-ASO-01..06). Cada teste nomeia a
reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.sugestao_aso import RelatorioASO, SugestaoASO, sugerir_aso
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    ExameEmitido,
    Motivo,
    OrigemRisco,
    Quantificacao,
    Risco,
    RiscoPGR,
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


def _linha(exame: str, *motivos: tuple[str, tuple[str, ...]], presumida: bool = False) -> ExameEmitido:
    return ExameEmitido(
        exame=exame,
        periodicidade_meses=12,
        motivos=[
            Motivo(
                regra_id=regra,
                predicado="p",
                risco_origem=None,
                detalhe=None,
                origens=tuple(OrigemRisco("p", a, "PGR", presumida) for a in agentes),
            )
            for regra, agentes in motivos
        ],
    )


def _sugestao(
    vocab: dict[str, Any], linha: ExameEmitido, *riscos: Risco
) -> SugestaoASO:
    (s,) = sugerir_aso([linha], riscos, vocab).linhas
    return s


def _regras(s: SugestaoASO) -> set[str]:
    return {c.regra for c in s.criterios if c.veredito == s.veredito}


def test_exame_clinico_sempre_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo `linha.exame == EXAME_CLINICO` — R-CLI-01 não tem
    # risco de origem e a linha cai em CONFERIR.
    s = _sugestao(vocab, _linha("exame_clinico", ("R-CLI-01", ())))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-01"})


def test_poeira_mineral_anexo_iii_obrigatorio_mesmo_baixo_e_ate_10(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo `_PREFIXOS_ANEXO_III` — sílica BAIXO a 5% do LEO
    # sai NAO_OBRIGATORIO pelos critérios de cancerígeno e geral.
    linha = _linha("rx_torax_oit", ("R-RX-01-adm", ("silica",)))
    s = _sugestao(vocab, linha, _risco("silica", "BAIXO", _q(0.002, "mg/m3", pct_lt=5.0)))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-02"})


def test_altura_obrigatorio_e_consigna_aptidao(vocab: dict[str, Any]) -> None:
    # Reversões: remover `trabalho_altura` de `_APTIDAO_NR` (BAIXO → NAO_OBRIGATORIO);
    # remover o cálculo de `aptidoes` em sugerir_aso (tupla vazia).
    linha = _linha("hemograma", ("R-PKG-ATIVCRIT", ("trabalho_altura",)))
    relatorio = sugerir_aso([linha], [_risco("trabalho_altura", "BAIXO")], vocab)
    (s,) = relatorio.linhas
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-03"})
    assert len(relatorio.aptidoes) == 1 and "NR-35 item 35.4.4.1" in relatorio.aptidoes[0]


def test_motorista_segue_regra_geral(vocab: dict[str, Any]) -> None:
    # Reversão: incluir `motorista_equipamento_pesado` em `_APTIDAO_NR` — BAIXO
    # passaria a OBRIGATORIO.
    linha = _linha("hemograma", ("R-PKG-ATIVCRIT", ("motorista_equipamento_pesado",)))
    s = _sugestao(vocab, linha, _risco("motorista_equipamento_pesado", "BAIXO"))
    assert s.veredito == "NAO_OBRIGATORIO"
    assert "monitoramento desde a classificação baixa" in s.criterios[0].texto


def test_cancerigeno_sem_avaliacao_ambiental_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: remover a chamada a `_criterio_cancerigeno` — benzeno BAIXO sem
    # medição sai NAO_OBRIGATORIO pela regra geral.
    linha = _linha("hemograma", ("R-PKG-BZ", ("benzeno",)))
    s = _sugestao(vocab, linha, _risco("benzeno", "BAIXO"))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-04"})


def test_cancerigeno_acima_de_10_pct_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: subir `_PCT_CANCERIGENO` de 10 para 50 — 15% do limite deixa de obrigar.
    linha = _linha("hemograma", ("R-PKG-BZ", ("benzeno",)))
    s = _sugestao(vocab, linha, _risco("benzeno", "BAIXO", _q(0.15, "ppm", pct_lt=15.0)))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-04"})


def test_cancerigeno_ate_10_pct_nao_obriga_por_anexo_v(vocab: dict[str, Any]) -> None:
    # Reversão: tratar toda medição de cancerígeno como "sem avaliação ambiental"
    # (`_sem_avaliacao_ambiental` devolvendo True) — 8% passaria a OBRIGATORIO.
    linha = _linha("hemograma", ("R-PKG-BZ", ("benzeno",)))
    s = _sugestao(vocab, linha, _risco("benzeno", "BAIXO", _q(0.08, "ppm", pct_lt=8.0)))
    assert s.veredito == "NAO_OBRIGATORIO"


def test_quimico_baixo_com_medicao_acima_do_nivel_de_acao_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: remover a chamada a `_medicao_acima_nivel_acao` em `_criterio_geral`
    # — tolueno BAIXO a 64% do LT (50/78 ppm) sai NAO_OBRIGATORIO.
    linha = _linha("ortocresol_urina", ("R-BIO-04-tolueno", ("tolueno",)))
    s = _sugestao(vocab, linha, _risco("tolueno", "BAIXO", _q(50.0, "ppm")))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-06"})


def test_quimico_baixo_abaixo_do_nivel_de_acao_nao_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: inverter o teste de `abaixo_nivel_acao` em `_medicao_acima_nivel_acao`
    # — 26% do LT (20/78 ppm) passaria a OBRIGATORIO.
    linha = _linha("ortocresol_urina", ("R-BIO-04-tolueno", ("tolueno",)))
    s = _sugestao(vocab, linha, _risco("tolueno", "BAIXO", _q(20.0, "ppm")))
    assert s.veredito == "NAO_OBRIGATORIO"


def test_moderado_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: piso de `_NIVEL_MODERADO` em "ALTO" — MODERADO sai NAO_OBRIGATORIO.
    linha = _linha("ortocresol_urina", ("R-BIO-04-tolueno", ("tolueno",)))
    s = _sugestao(vocab, linha, _risco("tolueno", "MODERADO"))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-06"})


def test_aiha_sem_nivel_sai_conferir(vocab: dict[str, Any]) -> None:
    # Reversão: `_criterio_geral` tratar `nivel_risco is None` como NAO_OBRIGATORIO
    # — o risco do grid AIHA sumiria da conferência (D-ARQ-22).
    linha = _linha("ortocresol_urina", ("R-BIO-04-tolueno", ("tolueno",)))
    s = _sugestao(vocab, linha, _risco("tolueno", None, aiha=True))
    assert s.veredito == "CONFERIR"
    assert "AIHA" in s.criterios[0].texto


def test_origem_presumida_sai_conferir(vocab: dict[str, Any]) -> None:
    # Reversão: ignorar `origem.presumida` — o MODERADO do risco obrigaria sem
    # que o risco tenha sido declarado.
    linha = _linha("ortocresol_urina", ("R-BIO-04-tolueno", ("tolueno",)), presumida=True)
    s = _sugestao(vocab, linha, _risco("tolueno", "MODERADO"))
    assert s.veredito == "CONFERIR"


def test_ruido_baixo_com_ototoxico_obriga_audiometria(vocab: dict[str, Any]) -> None:
    # Reversão: tirar `and agravante` da perna BAIXO de `_criterio_ruido` (ou o
    # agravante inteiro) — ruído BAIXO + tolueno BAIXO sai NAO_OBRIGATORIO.
    linha = _linha("audiometria", ("R-AUD-01", ("tolueno",)))
    s = _sugestao(
        vocab, linha, _risco("ruido", "BAIXO"), _risco("tolueno", "BAIXO", ototoxico=True)
    )
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-05"})


def test_ruido_baixo_com_vibracao_obriga_audiometria(vocab: dict[str, Any]) -> None:
    # Reversão: tirar `r.agente in _VIBRACAO` do agravante — ruído BAIXO +
    # vibração BAIXO sai NAO_OBRIGATORIO.
    linha = _linha("audiometria", ("R-VIB-02", ("vibracao_mao_braco",)))
    s = _sugestao(vocab, linha, _risco("ruido", "BAIXO"), _risco("vibracao_mao_braco", "BAIXO"))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-05"})


def test_ruido_baixo_medido_em_80_obriga_audiometria(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo de medição (`relacao in _RUIDO_ACIMA_ACAO`) — 80 dB(A)
    # com classificação BAIXO e sem agravante sai NAO_OBRIGATORIO.
    linha = _linha("audiometria", ("R-AUD-01", ("ruido",)))
    s = _sugestao(vocab, linha, _risco("ruido", "BAIXO", _q(80.0, "dB(A)")))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-05"})


def test_ruido_baixo_isolado_nao_obriga(vocab: dict[str, Any]) -> None:
    # Reversão: na perna BAIXO, trocar `nivel == "BAIXO" and agravante` por
    # `nivel == "BAIXO"` — ruído BAIXO a 75 dB(A), sem agravante, passaria a OBRIGATORIO.
    linha = _linha("audiometria", ("R-AUD-01", ("ruido",)))
    s = _sugestao(vocab, linha, _risco("ruido", "BAIXO", _q(75.0, "dB(A)")))
    assert s.veredito == "NAO_OBRIGATORIO"


def test_vibracao_acima_do_nivel_de_acao_obriga(vocab: dict[str, Any]) -> None:
    # Reversão: remover o ramo `_NIVEL_ACAO_VIBRACAO` de `_medicao_acima_nivel_acao`
    # — aren 3 m/s² em mãos e braços com BAIXO sai NAO_OBRIGATORIO.
    linha = _linha("rx_coluna_lombo_sacra", ("R-VIB-01", ("vibracao_mao_braco",)))
    s = _sugestao(vocab, linha, _risco("vibracao_mao_braco", "BAIXO", _q(3.0, "m/s2")))
    assert (s.veredito, _regras(s)) == ("OBRIGATORIO", {"R-ASO-06"})


def test_conferir_prevalece_sobre_nao_obrigatorio(vocab: dict[str, Any]) -> None:
    # Reversão: trocar a ordem de CONFERIR e NAO_OBRIGATORIO em `_PRIORIDADE` — a
    # linha com um risco sem classificação sairia NAO_OBRIGATORIO.
    linha = _linha("audiometria", ("R-AUD-01", ("tolueno", "xileno")))
    s = _sugestao(vocab, linha, _risco("tolueno", "BAIXO"), _risco("xileno", None))
    assert s.veredito == "CONFERIR"


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

    assert matriz.sugestao_aso != RelatorioASO()
    assert [s.exame for s in matriz.sugestao_aso.linhas] == [ln.exame for ln in matriz.linhas]
    assert {s.exame: s.veredito for s in matriz.sugestao_aso.linhas}["exame_clinico"] == "OBRIGATORIO"
