from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import extrair_texto_pgr, recortar_blocos_ghe
from agente_medico.motor.tipos import GHEVerbatim, Pendencia, RiscoVerbatim
from agente_medico.motor.transcritor_pgr import gate_forma_ghe, transcrever_ghes

CAMINHO_PGR = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")

# Harness de integração desta fatia (D-ARQ-49 P3/D-ARQ-50 C3, molde requer_pdfs
# de test_transcritor_fds.py) — ausência do PDF vira skip, não falha.
requer_pdfs = pytest.mark.skipif(
    not CAMINHO_PGR.exists(),
    reason="matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf ausente; harness integração 003.BN indisponível",
)

try:
    from agente_medico.tests.test_extracao_pgr import paginas  # noqa: F401
except ImportError:

    @pytest.fixture(scope="module")
    def paginas() -> list[str]:
        return extrair_texto_pgr(CAMINHO_PGR)


class MockTranscritorGHE:
    """Mock injetável (D-ARQ-49 P4: LLM SEMPRE mockado em teste, nunca API real).

    resultado fixo por bloco via overrides (bloco -> GHEVerbatim); padrao cobre
    blocos sem override explícito (usado no harness de integração, onde os 42
    blocos reais não têm gabarito de conteúdo nesta fatia-esqueleto). Captura
    a ordem e o conteúdo verbatim dos blocos recebidos em blocos_recebidos.
    """

    def __init__(
        self,
        padrao: GHEVerbatim,
        overrides: dict[str, GHEVerbatim] | None = None,
    ) -> None:
        self._padrao = padrao
        self._overrides = overrides or {}
        self.blocos_recebidos: list[str] = []

    def transcrever(self, bloco: str) -> GHEVerbatim:
        self.blocos_recebidos.append(bloco)
        return self._overrides.get(bloco, self._padrao)


def _ghe(
    nome: str = "Estrutura de concreto armado",
    cargos: tuple[str, ...] = (),
    riscos: tuple[RiscoVerbatim, ...] = (),
) -> GHEVerbatim:
    return GHEVerbatim(nome=nome, cargos=cargos, riscos=riscos)


def _risco(agente: str = "Ruído", quantificacao: str = "", fonte_geradora: str = "") -> RiscoVerbatim:
    return RiscoVerbatim(agente=agente, quantificacao=quantificacao, fonte_geradora=fonte_geradora)


# ---------------------------------------------------------------------------
# Núcleo — rodam sempre, sem PDF.
# ---------------------------------------------------------------------------


def test_transcrever_ghes_delega_ao_cliente_na_ordem_e_passa_bloco_verbatim() -> None:
    bloco1 = "SETOR/FUNÇÃO Um\nlinha A"
    bloco2 = "SETOR/FUNÇÃO Dois\nlinha B"
    resultado1 = _ghe(nome="Um")
    resultado2 = _ghe(nome="Dois")
    mock = MockTranscritorGHE(
        padrao=_ghe(nome="nao deveria ser usado"),
        overrides={bloco1: resultado1, bloco2: resultado2},
    )
    saida = transcrever_ghes([bloco1, bloco2], mock)
    assert saida == (resultado1, resultado2)
    assert mock.blocos_recebidos == [bloco1, bloco2]


def test_transcrever_ghes_lista_vazia_devolve_tupla_vazia() -> None:
    mock = MockTranscritorGHE(padrao=_ghe())
    assert transcrever_ghes([], mock) == ()
    assert mock.blocos_recebidos == []


def test_gate_forma_ghe_aprova_ghe_valido() -> None:
    ghe = _ghe(riscos=(_risco(),))
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == (ghe,)
    assert pendencias == ()


def test_gate_forma_ghe_reprova_nome_vazio() -> None:
    ghe = _ghe(nome="  ", riscos=(_risco(),))
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == ()
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert isinstance(pendencia, Pendencia)
    assert pendencia.tipo == "forma_verbatim_pgr"
    assert pendencia.bloqueante is True
    assert pendencia.destinatario == "extracao"
    assert pendencia.regra_origem == "D-ARQ-49"


def test_gate_forma_ghe_reprova_risco_com_agente_vazio() -> None:
    ghe = _ghe(riscos=(_risco(agente=" "),))
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_pgr"


def test_gate_forma_ghe_aprova_sem_cargos_e_com_risco_qualitativo() -> None:
    ghe = _ghe(cargos=(), riscos=(_risco(quantificacao=""),))
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == (ghe,)
    assert pendencias == ()


def test_multi_agente_mesmo_et_vira_riscos_separados_com_fonte_copiada() -> None:
    # Literais medidos 003.BK/003.BM (GHE 13 - Pintura, pág. 71).
    fonte = "Thinner/Zarcão"
    riscos = (
        _risco(agente="Etanol", quantificacao="4,4 ppm", fonte_geradora=fonte),
        _risco(agente="Acetato de Etila", quantificacao="1 ppm", fonte_geradora=fonte),
        _risco(agente="Tolueno", quantificacao="6,3 ppm", fonte_geradora=fonte),
    )
    ghe = _ghe(nome="Pintura", riscos=riscos)
    assert len(ghe.riscos) == 3
    assert {r.fonte_geradora for r in ghe.riscos} == {fonte}
    aprovados, pendencias = gate_forma_ghe([ghe])
    assert aprovados == (ghe,)
    assert pendencias == ()


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs; espelha test_transcritor_fds.py).
# ---------------------------------------------------------------------------


@requer_pdfs
def test_transcrever_ghes_recebe_os_42_blocos_com_ancora(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    resultado = _ghe(riscos=(_risco(),))
    mock = MockTranscritorGHE(padrao=resultado)
    transcrever_ghes(blocos, mock)
    assert len(mock.blocos_recebidos) == 42
    assert all(bloco.startswith("SETOR/FUNÇÃO") for bloco in mock.blocos_recebidos)
