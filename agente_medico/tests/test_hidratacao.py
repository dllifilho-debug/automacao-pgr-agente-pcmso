from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.hidratacao import hidratar_ghe
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def indice_real() -> dict[str, str]:
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(p.vocabulario.agentes)


def _ghe_verbatim(*, riscos: tuple[RiscoVerbatim, ...]) -> GHEVerbatim:
    return GHEVerbatim(nome="Teste", cargos=("servente",), riscos=riscos)


# ---------------------------------------------------------------------------
# tri-estado do resolver
# ---------------------------------------------------------------------------

def test_exata_resolve_slug_sem_pendencia(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente == "ruido"
    assert pendencias == []


def test_fuzzy_resolve_slug_com_pendencia_nao_bloqueante(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Microrganismo", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente == "microrganismos"

    assert len(pendencias) == 1
    pend = pendencias[0]
    assert pend.tipo == "resolucao_fuzzy"
    assert pend.bloqueante is False
    assert pend.ghe_id == "GHE-01"


def test_nao_resolvido_agente_none_com_pendencia_e_risco_preservado(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Thinner", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    # anti-supressão: risco presente na saída mesmo sem slug resolvido.
    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente is None

    assert len(pendencias) == 1
    pend = pendencias[0]
    assert pend.tipo == "vocabulario_ausente"
    assert pend.ghe_id == "GHE-01"


# ---------------------------------------------------------------------------
# id posicional (D-ARQ-51 seam 1)
# ---------------------------------------------------------------------------

def test_id_posicional_formatado_e_deterministico(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(riscos=())

    ghe_pgr_a, _ = hidratar_ghe(ghe, indice_real, posicao=1)
    ghe_pgr_b, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    assert ghe_pgr_a.id == "GHE-01"
    assert ghe_pgr_a.id == ghe_pgr_b.id


# ---------------------------------------------------------------------------
# pareamento agente=None <-> pendência (D-ARQ-51 seam 3)
# ---------------------------------------------------------------------------

def test_todo_agente_none_tem_pendencia_correspondente(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(
        riscos=(
            RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora=""),
            RiscoVerbatim(agente="Thinner", quantificacao="", fonte_geradora=""),
            RiscoVerbatim(agente="Eaquipamento desprotegido", quantificacao="", fonte_geradora=""),
        )
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=3)

    riscos_none = [r for r in ghe_pgr.riscos if r.agente is None]
    pendencias_vocab_ausente = [p for p in pendencias if p.tipo == "vocabulario_ausente"]
    assert len(riscos_none) == len(pendencias_vocab_ausente) == 2
    assert all(p.ghe_id == "GHE-03" for p in pendencias_vocab_ausente)


# ---------------------------------------------------------------------------
# gabarito de forma (D-ARQ-50 C1) — compara forma, não contagem 42vs32
# ---------------------------------------------------------------------------

def test_gabarito_de_forma_ghepgr(indice_real: dict[str, str]) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    # identidade preenchida
    assert isinstance(ghe_pgr.id, str) and ghe_pgr.id
    assert ghe_pgr.nome == ghe.nome
    assert ghe_pgr.cargos == ghe.cargos
    assert len(ghe_pgr.riscos) == len(ghe.riscos)
    assert all(r.tipo == "" for r in ghe_pgr.riscos)
    assert all(r.quantificacao is None for r in ghe_pgr.riscos)
    assert all(r.severidade is None for r in ghe_pgr.riscos)

    # diferidos em default (D-ARQ-49 P2)
    assert ghe_pgr.epis == ()
    assert ghe_pgr.produtos_quimicos == ()
    assert ghe_pgr.psicossocial is False
    assert ghe_pgr.cenario is None
