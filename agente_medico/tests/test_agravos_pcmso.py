"""Agravo do PCMSO por perigo (D-ARQ-96 cl.3). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from agente_medico.motor.protocolo import carregar
from agente_medico.superficie.agravos_pcmso import (
    OrigemAgravo,
    VocabularioAgravos,
    VocabularioAgravosInvalido,
    agravo_do_perigo,
    carregar_agravos,
)

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def agentes() -> dict[str, Any]:
    return carregar(PROTOCOLO_DIR).vocabulario.agentes


@pytest.fixture(scope="module")
def vocabulario(agentes: dict[str, Any]) -> VocabularioAgravos:
    return carregar_agravos(agentes)


# Reversão: em agravo_do_perigo, não consultar por_agente.
def test_perigo_que_resolve_em_agente_usa_o_texto_do_agente(vocabulario: VocabularioAgravos) -> None:
    agravo = agravo_do_perigo("Ruído", "texto do PGR", vocabulario)
    assert (agravo.origem, agravo.chave) == (OrigemAgravo.DICIONARIO, "ruido")
    assert "PAINPSE" in agravo.texto


# Reversão: em agravo_do_perigo, não consultar por_forma.
def test_perigo_sem_agente_usa_os_termos_do_vocabulario(vocabulario: VocabularioAgravos) -> None:
    agravo = agravo_do_perigo("Liderança", "Transtornos mentais.", vocabulario)
    assert (agravo.origem, agravo.chave) == (OrigemAgravo.DICIONARIO, "psicossocial")


# Reversão: devolver DICIONARIO (ou texto vazio) quando nada casa e o PGR tem agravo.
def test_fora_do_vocabulario_sai_o_agravo_do_pgr_para_conferir(vocabulario: VocabularioAgravos) -> None:
    agravo = agravo_do_perigo("Bisfenol A epoxi resina", " Provoca irritação ocular grave. ", vocabulario)
    assert agravo == agravo.__class__(texto="Provoca irritação ocular grave.", origem=OrigemAgravo.PGR_CONFERIR, chave=None)


# Reversão: devolver PGR_CONFERIR com texto vazio quando o PGR não tem agravo.
def test_sem_vocabulario_nem_pgr_o_agravo_fica_ausente(vocabulario: VocabularioAgravos) -> None:
    assert agravo_do_perigo("Bisfenol A epoxi resina", "  ", vocabulario).origem is OrigemAgravo.AUSENTE


# Reversão: apagar um termo ou trocar a chave de uma das formas medidas no Mauá e no R70.
@pytest.mark.parametrize(
    ("perigo", "chave"),
    [
        ("Queda em altura", "trabalho_altura"),
        ("Postura de pé por longos períodos", "postura_inadequada"),
        ("Sulfato de cálcio", "poeira_de_gesso"),
        ("Piso irregular ou em desnível", "queda_mesmo_nivel"),
        ("Arranjo físico inadequado (Perfuração)", "arranjo_fisico"),
        ("Choque Elétrico", "choque_eletrico"),
        ("Levantamento, transporte manual de pesos", "levantamento_de_peso"),
        ("Sentado por longos períodos", "postura_sentada"),
        ("Valores no local de trabalho", "psicossocial"),
        ("Uso Frequente de Escadas", "uso_de_escadas"),
    ],
)
def test_formas_medidas_casam_com_a_chave_esperada(vocabulario: VocabularioAgravos, perigo: str, chave: str) -> None:
    assert agravo_do_perigo(perigo, None, vocabulario).chave == chave


def _vocab(tmp_path: Path, corpo: str) -> Path:
    caminho = tmp_path / "agravos.yaml"
    caminho.write_text("agravos:\n" + corpo, encoding="utf-8")
    return caminho


# Reversão: tirar a recusa de termo que já resolve num agente (sinônimo de agente muda exame).
def test_termo_que_resolve_em_agente_recusa_o_vocabulario(tmp_path: Path, agentes: dict[str, Any]) -> None:
    caminho = _vocab(tmp_path, '  x:\n    texto: "t."\n    fonte: "f"\n    termos: ["Ruído"]\n')
    with pytest.raises(VocabularioAgravosInvalido, match="ruido"):
        carregar_agravos(agentes, caminho)


# Reversão: tirar a checagem de agente inexistente.
def test_agente_inexistente_recusa_o_vocabulario(tmp_path: Path, agentes: dict[str, Any]) -> None:
    caminho = _vocab(tmp_path, '  x:\n    texto: "t."\n    fonte: "f"\n    agente: agente_que_nao_existe\n')
    with pytest.raises(VocabularioAgravosInvalido, match="inexistente"):
        carregar_agravos(agentes, caminho)


# Reversão: tirar a checagem de termo repetido entre entradas.
def test_termo_em_duas_entradas_recusa_o_vocabulario(tmp_path: Path, agentes: dict[str, Any]) -> None:
    corpo = ('  a:\n    texto: "t."\n    fonte: "f"\n    termos: ["Perigo X"]\n'
             '  b:\n    texto: "t."\n    fonte: "f"\n    termos: ["perigo x"]\n')
    with pytest.raises(VocabularioAgravosInvalido, match="duas entradas"):
        carregar_agravos(agentes, _vocab(tmp_path, corpo))


# Reversão: aceitar entrada com 'agente' e 'termos' juntos.
def test_agente_e_termos_juntos_recusa_o_vocabulario(tmp_path: Path, agentes: dict[str, Any]) -> None:
    caminho = _vocab(tmp_path, '  x:\n    texto: "t."\n    fonte: "f"\n    agente: ruido\n    termos: ["Perigo X"]\n')
    with pytest.raises(VocabularioAgravosInvalido, match="não dos dois"):
        carregar_agravos(agentes, caminho)
