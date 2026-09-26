"""R-CLI-05 — clínico semestral (sucede R-CLI-02): (a) cancerígeno IARC 1/2A com
indicador biológico no Anexo I da NR-07, qualquer nível; (b) agente com indicador
biológico MODERADO ou acima no PGR. Precedente: matriz da Dra. Patrícia, Aurora
27/08/26 (GHE 11 e 18 em 6M; poeira/sílica MODERADO e Anexo I BAIXO em 12M). Cada
teste nomeia a reversão de código ou dado que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, Momento, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 26)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _clinico(proto: Protocolo, *riscos: RiscoPGR) -> ExameEmitido:
    ghe = GHEPGR(
        id="GHE-11",
        nome="INSTALAÇÕES HIDRO-SANITÁRIAS",
        cargos=("Encanador",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    (linha,) = [e for e in matriz.linhas if e.exame == "exame_clinico"]
    return linha


def _risco(agente: str, nivel: str | None) -> RiscoPGR:
    return RiscoPGR(tipo="", agente=agente, quantificacao=None, severidade=None, nivel_risco=nivel)


def test_agente_do_anexo_i_moderado_da_clinico_semestral(proto: Protocolo) -> None:
    # Aurora GHE 11. Reversões que matam: tirar `agente_ibe_moderado_ou_acima` do
    # `quando` de R-CLI-05, ou a regra inteira — o clínico fica em 12M.
    linha = _clinico(proto, _risco("metil_etil_cetona", "MODERADO"))

    assert linha.periodicidade_meses == 6
    assert linha.momentos == {Momento.ADM, Momento.PER, Momento.MR, Momento.RT, Momento.DEM}
    assert {m.regra_id for m in linha.motivos} == {"R-CLI-01", "R-CLI-05"}


def test_agente_do_anexo_i_baixo_mantem_clinico_anual(proto: Protocolo) -> None:
    # Porto Araras I GHE-13/14 e Vila Brasil GHE-23/26 (12M no gabarito). Reversão
    # que mata: incluir BAIXO em `_NIVEIS_MODERADO_OU_ACIMA`.
    linha = _clinico(proto, _risco("metil_etil_cetona", "BAIXO"))

    assert linha.periodicidade_meses == 12


def test_silica_moderado_sem_indicador_biologico_mantem_clinico_anual(proto: Protocolo) -> None:
    # A proposta refutada na medição: "químico MODERADO+" sem exigir indicador
    # biológico dava 6M a 8 GHEs de Porto Araras I só por sílica. Reversão que mata:
    # tirar `r.tipo_ibe is not None` do primitivo.
    linha = _clinico(proto, _risco("silica", "MODERADO"))

    assert linha.periodicidade_meses == 12


@pytest.mark.parametrize(
    "agente",
    [
        "arsenio",
        "benzeno",
        "butadieno_13",
        "cadmio",
        "cromo_hexavalente",
        "diclorometano",
        "dimetilformamida",
        "estireno",
        "oxido_de_etileno",
        "tetracloroetileno",
        "tricloroetileno",
    ],
)
def test_cancerigeno_com_indicador_biologico_da_semestral_em_qualquer_nivel(
    proto: Protocolo, agente: str
) -> None:
    # Aurora GHE 18 (benzeno). Reversões que matam: tirar `cancerigeno_com_ibe` do
    # `quando` de R-CLI-05 (todos os casos) ou tirar o agente da lista do composto
    # (o caso dele).
    linha = _clinico(proto, _risco(agente, "BAIXO"))

    assert linha.periodicidade_meses == 6


def test_chumbo_escalado_no_003dp_so_entra_pela_perna_b(proto: Protocolo) -> None:
    # 003.DP deixou chumbo ESCALAR (metal 2B, compostos inorgânicos 2A). Reversão
    # que mata: pôr `chumbo` no composto `cancerigeno_com_ibe`.
    linha = _clinico(proto, _risco("chumbo", "BAIXO"))

    assert linha.periodicidade_meses == 12
