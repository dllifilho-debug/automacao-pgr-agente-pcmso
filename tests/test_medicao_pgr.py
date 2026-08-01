"""Testes de scripts/medicao_pgr.py — _renderizar_relatorio sobre Resultado sintético."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Motivo, Pendencia, Resultado
from scripts.medicao_pgr import _formatar_pendencia, _renderizar_relatorio


def _resultado_com_diagnostico() -> Resultado:
    motivo = Motivo(
        regra_id="R-AUD-01",
        predicado="ou(ruido_acima_acao, motorista_equipamento_pesado, ototoxico)",
        risco_origem=None,
        detalhe="Emitido por regra R-AUD-01",
    )
    exame = ExameEmitido(
        exame="audiometria",
        periodicidade_meses=12,
        momentos={Momento.ADM, Momento.PER, Momento.MR},
        motivos=[motivo],
    )
    matriz = MatrizGHE(
        ghe_id="GHE-01",
        linhas=[exame],
        status="VÁLIDA",
        riscos_resolvidos=("ruido", "vibracao_corpo_inteiro"),
        predicados_avaliados=(("ruido_acima_acao", "True"), ("vibracao_corpo_inteiro", "True")),
    )
    return Resultado(status="OK", matrizes=[matriz])


def test_renderizar_relatorio_imprime_riscos_e_predicados_avaliados() -> None:
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), _resultado_com_diagnostico(), ())
    assert "- riscos_resolvidos: `ruido`, `vibracao_corpo_inteiro`" in relatorio
    assert "- predicados_avaliados: ruido_acima_acao=True; vibracao_corpo_inteiro=True" in relatorio


def test_renderizar_relatorio_tabela_tem_colunas_predicado_e_detalhe() -> None:
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), _resultado_com_diagnostico(), ())
    assert "| predicado | detalhe |" in relatorio
    assert "ou(ruido_acima_acao, motorista_equipamento_pesado, ototoxico)" in relatorio
    assert "Emitido por regra R-AUD-01" in relatorio


def test_formatar_pendencia_com_ghe_id_imprime_linha_ghe() -> None:
    pendencia = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="protocolo",
        motivo="termo 'X' não resolvido",
        ghe_id="GHE-12",
    )
    assert "ghe_id: `GHE-12`" in _formatar_pendencia(pendencia)


def test_formatar_pendencia_sem_ghe_id_nao_ganha_linha_vazia() -> None:
    pendencia = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="protocolo",
        motivo="termo 'X' não resolvido",
    )
    assert "ghe_id" not in _formatar_pendencia(pendencia)


def test_renderizar_relatorio_coluna_pendencias_anexadas_nenhuma() -> None:
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), _resultado_com_diagnostico(), ())
    assert "| pendências anexadas |" in relatorio
    assert "| (nenhuma) |" in relatorio


def test_renderizar_relatorio_coluna_pendencias_anexadas_com_conteudo() -> None:
    motivo = Motivo(
        regra_id="R-AUD-02",
        predicado="ou(ruido_acima_acao, altura)",
        risco_origem=None,
        detalhe="Emitido por regra R-AUD-02",
    )
    exame = ExameEmitido(
        exame="audiometria",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[motivo],
    )
    exame.pendencias_anexadas.append(
        Pendencia(
            tipo="perna_ausente_absorvida",
            destinatario="elaborador_pgr",
            motivo="Regra R-AUD-02: emitiu por outra perna, mas ruido_acima_acao ficou ausente",
            bloqueante=False,
            regra_origem="R-AUD-02",
            ghe_id="GHE-16",
            exames_alvo=("audiometria",),
        )
    )
    matriz = MatrizGHE(ghe_id="GHE-16", linhas=[exame], status="VÁLIDA")
    resultado = Resultado(status="OK", matrizes=[matriz])
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), resultado, ())
    assert "perna_ausente_absorvida (R-AUD-02, nao-bloqueante)" in relatorio


def test_renderizar_relatorio_sem_riscos_resolvidos_mostra_nenhum() -> None:
    matriz = MatrizGHE(ghe_id="GHE-02", linhas=[], status="BLOQUEADA")
    resultado = Resultado(status="PRELIMINAR", matrizes=[matriz])
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), resultado, ())
    assert "- riscos_resolvidos: (nenhum)" in relatorio


# ---------------------------------------------------------------------------
# D-ARQ-72 fatia 2 (003.EM): coluna "status regra" (2a) e bloco
# "inspecionar primeiro" (2b) — entrega de D-ARQ-22 Parte B na apresentação.
# ---------------------------------------------------------------------------


def _bloco_inspecionar_primeiro(relatorio: str) -> str:
    inicio = relatorio.index("- inspecionar primeiro:")
    fim = relatorio.index("\n\n", inicio)
    return relatorio[inicio:fim]


def test_status_regra_interpretado_aparece_na_coluna() -> None:
    # Reversão: remover a coluna "status regra" do render (2a) —
    # a sequência "R-RX-02 | INTERPRETADO | fumos_metalicos" some da linha.
    motivo = Motivo(
        regra_id="R-RX-02",
        predicado="fumos_metalicos",
        risco_origem=None,
        detalhe="Emitido por regra R-RX-02",
        status_regra="INTERPRETADO",
    )
    exame = ExameEmitido(
        exame="rx_torax",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[motivo],
    )
    matriz = MatrizGHE(ghe_id="GHE-20", linhas=[exame], status="VÁLIDA")
    resultado = Resultado(status="OK", matrizes=[matriz])
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), resultado, ())
    assert "| status regra |" in relatorio
    assert "R-RX-02 | INTERPRETADO | fumos_metalicos" in relatorio


def test_inspecionar_primeiro_lista_interpretado_nao_lista_validado() -> None:
    # Reversão: remover o bloco "inspecionar primeiro" (2b) do render.
    motivo_interp = Motivo(
        regra_id="R-RX-02",
        predicado="fumos_metalicos",
        risco_origem=None,
        detalhe="Emitido por regra R-RX-02",
        status_regra="INTERPRETADO",
    )
    exame_interp = ExameEmitido(
        exame="rx_torax",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[motivo_interp],
    )
    motivo_validado = Motivo(
        regra_id="R-AUD-01",
        predicado="ruido_acima_acao",
        risco_origem=None,
        detalhe="Emitido por regra R-AUD-01",
        status_regra="VALIDADO",
    )
    exame_validado = ExameEmitido(
        exame="audiometria",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[motivo_validado],
    )
    matriz = MatrizGHE(ghe_id="GHE-21", linhas=[exame_interp, exame_validado], status="VÁLIDA")
    resultado = Resultado(status="OK", matrizes=[matriz])
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), resultado, ())
    bloco = _bloco_inspecionar_primeiro(relatorio)
    assert "rx_torax (INTERPRETADO)" in bloco
    assert "audiometria" not in bloco


def test_inspecionar_primeiro_so_validado_diz_nenhuma() -> None:
    # Reversão: remover o bloco "inspecionar primeiro" (2b) — a string "(nenhuma)" some.
    motivo = Motivo(
        regra_id="R-AUD-01",
        predicado="ruido_acima_acao",
        risco_origem=None,
        detalhe="Emitido por regra R-AUD-01",
        status_regra="VALIDADO",
    )
    exame = ExameEmitido(
        exame="audiometria",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[motivo],
    )
    matriz = MatrizGHE(ghe_id="GHE-22", linhas=[exame], status="VÁLIDA")
    resultado = Resultado(status="OK", matrizes=[matriz])
    with patch("scripts.medicao_pgr._hash_commit", return_value="abc1234"):
        relatorio = _renderizar_relatorio(Path("fake.pdf"), resultado, ())
    bloco = _bloco_inspecionar_primeiro(relatorio)
    assert "(nenhuma)" in bloco
