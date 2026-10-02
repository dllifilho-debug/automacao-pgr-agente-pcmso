"""`destilados_petroleo_hidrotratados` (03/10/2026, opção b ajustada): o nome químico do
destilado de petróleo hidrotratado no PGR é reconhecido, sem exame e sem benzeno a confirmar.
Casos: Fascino 15.07.26 GHE 16 e WV Maldi 2026-07-22 GHE 20, solvente isolado, gabaritos sem o
pacote do benzeno. O CAS 64742-47-8 segue na aguarrás, como as FDS do acervo o nomeiam. Cada
teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim
from agente_medico.tests.test_contaminante_a_confirmar import (
    _a_confirmar,
    _com_produtos,
    _hidratar,
    _matrizes,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PACOTE = {"hemograma", "reticulocitos", "acido_transmuconico"}
_FASCINO = "Destilados (Petróleo) leves tratados com hidrogênio."
_MALDI = "Destilados (Petróleo) leves\ntratados com\nhidrogênio\n(Querosene\nhidratado)"
# Seção 3 da FDS "Fundo Zarcão- PINTURA ESMALTE SINTÉTICO- PINTOR.pdf" (acervo), destilados.
_FUNDO_ZARCAO = (
    BlocoVerbatim("10 - <50", (MembroVerbatim("64742-47-8", "Destilados de Petróleo levemente tratados com hidrogênio"),)),
)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.mark.parametrize("termo", [_FASCINO, _MALDI])
def test_destilado_hidrotratado_isolado_nao_pede_fds_nem_presume_benzeno(proto: Protocolo, termo: str) -> None:
    # Reversões que matam: (1) tirar o termo do slug — o risco sai sem agente; (2) devolver o
    # termo a aguarras_mineral ou dar `contaminantes_a_confirmar: [benzeno]` ao slug — sai a
    # pendência R-FDS-07 e o pacote presumido que os gabaritos não pedem.
    pgr, _ = _hidratar(proto, ("GHE 16 - PINTURA", (termo,)))
    (pintura,) = _matrizes(proto, pgr)

    assert pgr.ghes[0].riscos[0].agente == "destilados_petroleo_hidrotratados"
    assert _a_confirmar(pintura) == []
    assert not _PACOTE & {e.exame for e in pintura.linhas}


def test_fds_com_64742_47_8_continua_respondendo_pela_aguarras(proto: Protocolo) -> None:
    # PGR "Aguarrás" + FDS do acervo com 64742-47-8 sem benzeno: a FDS responde pela aguarrás.
    # Reversão que mata: tirar o CAS 64742-47-8 de aguarras_mineral — a aguarrás fica "sem
    # FDS" e voltam a pendência e o pacote presumido.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", ("Aguarrás",)))
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Fundo Zarcão", _FUNDO_ZARCAO)))

    assert _a_confirmar(pintura) == []
    assert not _PACOTE & {e.exame for e in pintura.linhas}
