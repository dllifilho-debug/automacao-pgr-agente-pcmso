"""R-PKG-BZ-PRES [INTERPRETADO] (D-ARQ-68 cl.5, DT-(sessão claude/cool-planck-niq4le)-04):
solvente de petróleo no PGR sem a FDS dele e sem benzeno identificado → pacote do benzeno
sob presunção protetiva, pendência anexada às linhas e matriz PARCIAL. Caso: Aurora
27.08.26 GHE 18 PINTURA sem FDS; 21 de 41 pinturas do acervo com o pacote. Cada teste nomeia
a reversão que o deixa vermelho."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import BlocoVerbatim, MatrizGHE, MembroVerbatim
from agente_medico.tests.test_contaminante_a_confirmar import (
    _AGUARRAS,
    _FISPQ_AGUARRAS,
    _com_produtos,
    _hidratar,
    _matrizes,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PACOTE = {"hemograma", "reticulocitos", "acido_transmuconico"}


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _regras_por_exame(matriz: MatrizGHE) -> dict[str, set[str]]:
    return {e.exame: {m.regra_id for m in e.motivos} for e in matriz.linhas}


def test_aguarras_sem_fds_emite_o_pacote_presumido(proto: Protocolo) -> None:
    # Reversões que matam: (1) tirar a R-PKG-BZ-PRES de regras.yaml; (2) tirar
    # `quando_ausente` — vira pendência bloqueante e nada sai; (3) o primitivo
    # devolver False no lugar de Ausente; (4) mudar exames, periodicidade ou momentos
    # do pacote; (5) status diferente de INTERPRETADO.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    (pintura,) = _matrizes(proto, pgr)

    linhas = {e.exame: e for e in pintura.linhas}
    esperado = {
        "hemograma": (6, {"ADM", "PER", "MR", "DEM"}),
        "reticulocitos": (6, {"ADM", "PER", "MR", "DEM"}),
        "acido_transmuconico": (6, {"PER"}),
    }
    for exame, (meses, momentos) in esperado.items():
        assert (linhas[exame].periodicidade_meses, {m.value for m in linhas[exame].momentos}) == (meses, momentos)
        (motivo,) = linhas[exame].motivos
        assert (motivo.regra_id, motivo.status_regra) == ("R-PKG-BZ-PRES", "INTERPRETADO")
        assert [p.tipo for p in linhas[exame].pendencias_anexadas] == ["predicado_ausente_presumido"]
    assert linhas["exame_clinico"].periodicidade_meses == 6
    assert "R-PKG-BZ-PRES" in _regras_por_exame(pintura)["exame_clinico"]
    assert pintura.status == "PARCIAL"


def test_fds_da_aguarras_sem_benzeno_afasta_a_presuncao(proto: Protocolo) -> None:
    # Reversão que mata: o primitivo ignorar as FDS anexadas — o pacote sai mesmo
    # com a FDS do próprio solvente respondendo.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Aguarrás mineral", (_FISPQ_AGUARRAS[0],))))

    assert not _PACOTE & {e.exame for e in pintura.linhas}


def test_benzeno_identificado_usa_a_regra_validada_nao_a_presumida(proto: Protocolo) -> None:
    # Reversão que mata: o primitivo não checar o benzeno entre os riscos — as duas
    # regras emitem e a linha ganha a pendência de presunção sem razão.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    thinner = (BlocoVerbatim("<0,1", (MembroVerbatim("71-43-2", "Benzeno"),)),)
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Thinner", thinner)))

    regras = _regras_por_exame(pintura)
    assert all(regras[e] == {"R-PKG-BZ"} for e in _PACOTE)
    assert not any(p.tipo == "predicado_ausente_presumido" for e in pintura.linhas for p in e.pendencias_anexadas)


def test_pintura_so_com_tinta_nao_presume(proto: Protocolo) -> None:
    # Vistamerica 2026-07-28 GHE 22 (só tinta): sem pacote no gabarito.
    # Reversão que mata: o primitivo devolver Ausente sem solvente marcado.
    pgr, _ = _hidratar(proto, ("GHE 22 - PINTURA", ("Ruído",)))
    (pintura,) = _matrizes(proto, pgr)

    assert not _PACOTE & {e.exame for e in pintura.linhas}


def test_solvente_irrelevante_nao_presume(proto: Protocolo) -> None:
    # Porto Araras I GHE-14: "Querosene" IRRELEVANTE; gabaritos de 06.07.26 e 24.09.26 sem o
    # pacote. Mesmo corte da R-BIO-05 para cancerígeno. Reversões que matam: (1) tirar o
    # corte por IRRELEVANTE do primitivo; (2) cortar também BAIXO — o caso do Aurora
    # (BAIXO, test_aguarras_sem_fds_emite_o_pacote_presumido) perde o pacote.
    pgr, _ = _hidratar(proto, ("GHE - 14 PINTURA", ("Querosene",)))
    pgr = dataclasses.replace(
        pgr,
        ghes=(
            dataclasses.replace(
                pgr.ghes[0],
                riscos=tuple(dataclasses.replace(r, nivel_risco="IRRELEVANTE") for r in pgr.ghes[0].riscos),
            ),
        ),
    )
    (pintura,) = _matrizes(proto, pgr)

    assert pgr.ghes[0].riscos[0].agente == "querosene"
    assert not _PACOTE & {e.exame for e in pintura.linhas}
