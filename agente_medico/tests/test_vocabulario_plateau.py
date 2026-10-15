"""Grafias do PGR Plateau D'Or rev 03 que o app não reconhecia e as médicas leram (PCMSO Mauá 28.09.26),
DT-(sessão `claude/pcmso-maua-fatia-2-cdd2e1`)-01 item 2. Cada teste olha o exame que sai, não só o termo, e nomeia
a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import MatrizGHE
from agente_medico.tests.test_contaminante_a_confirmar import _a_confirmar, _hidratar, _matrizes

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, *termos: str) -> MatrizGHE:
    pgr, _ = _hidratar(proto, ("GHE 18 - Impermeabilização", termos))
    (matriz,) = _matrizes(proto, pgr)
    return matriz


def _regras(matriz: MatrizGHE, exame: str) -> set[str]:
    return {m.regra_id for linha in matriz.linhas if linha.exame == exame for m in linha.motivos}


def test_hidrocarbonetos_da_impermeabilizacao_pedem_a_fds_sem_presumir_benzeno(proto: Protocolo) -> None:
    # Decisão do Diovanni (15/10/2026, opção b): só o pedido da FDS. Reversões que matam: (1) tirar "Hidrocarbonetos"
    # dos termos de `hidrocarbonetos_nao_especificados` — some a pendência; (2) tirar `contaminantes_a_confirmar` do
    # agente — idem; (3) tirar `presumir_contaminante: false` do agente, ou o filtro `r.presumir_contaminante` de
    # `_benzeno_a_confirmar` — o GHE ganha o pacote do benzeno presumido (reticulócitos pela R-PKG-BZ-PRES).
    matriz = _matriz(proto, "Hidrocarbonetos")
    (pendencia,) = _a_confirmar(matriz)
    assert pendencia.motivo.startswith("Hidrocarbonetos sem FDS")
    assert _regras(matriz, "reticulocitos") == set()


def test_aguarras_no_mesmo_ghe_continua_presumindo_benzeno(proto: Protocolo) -> None:
    # A chave vale por agente, não por GHE. Reversão que mata: descartar o GHE inteiro da presunção quando algum
    # agente tem `presumir_contaminante: false` — a aguarrás junto com os hidrocarbonetos perde o pacote.
    matriz = _matriz(proto, "Hidrocarbonetos", "Aguarrás")
    assert "R-PKG-BZ-PRES" in _regras(matriz, "reticulocitos")


def test_hidrocarboneto_alifatico_da_textura_nao_presume_benzeno(proto: Protocolo) -> None:
    # Plateau GHE 15 (textura), sem o pacote no Mauá. Reversão que mata: gravar "Hidrocarboneto Alifático" nos termos
    # de `hidrocarbonetos_nao_especificados` (ou trocar o termo exato por um fuzzy) — a pintura ganha o pacote.
    matriz = _matriz(proto, "Hidrocarboneto Alifático")
    assert _regras(matriz, "reticulocitos") == set()
    assert _a_confirmar(matriz) == []


@pytest.mark.parametrize("termo", ["Poeiras respiravel/silica", "Poeiras respiravel /silica"])
def test_poeiras_respiravel_silica_pede_rx_e_espirometria(proto: Protocolo, termo: str) -> None:
    # Reversão que mata: tirar "Poeiras respiravel/silica" dos termos de `silica` — o GHE sai sem RX OIT e sem
    # espirometria, como na rodada do Plateau.
    matriz = _matriz(proto, termo)
    assert _regras(matriz, "rx_torax_oit")
    assert _regras(matriz, "espirometria")


def test_operacoes_em_espaco_confinado_pedem_avaliacao_psicossocial(proto: Protocolo) -> None:
    # NR-33 33.5.19.1 pela R-PSY-06. Reversão que mata: tirar "Operações em espaço confinado" dos termos de
    # `espaco_confinado` — sem altura no GHE, a avaliação psicossocial some.
    matriz = _matriz(proto, "Operações em espaço confinado")
    assert "R-PSY-06" in _regras(matriz, "avaliacao_psicossocial")


def test_acidentes_de_transito_pedem_acuidade_e_audiometria(proto: Protocolo) -> None:
    # Reversão que mata: tirar "Acidentes de trânsito" dos termos de `transito_via_publica` — o GHE de transporte sai
    # só com o clínico, como na rodada do Plateau.
    matriz = _matriz(proto, "Acidentes de trânsito")
    assert "R-PKG-TRANSITO" in _regras(matriz, "acuidade_visual")
    assert "R-PKG-TRANSITO" in _regras(matriz, "audiometria")
