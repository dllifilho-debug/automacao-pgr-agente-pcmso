from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import (
    extrair_texto_pgr,
    recortar_cards_cargo,
    recuperar_titulos_cargo,
)
from agente_medico.motor.tipos import GHEVerbatim, Pendencia, RiscoVerbatim
from agente_medico.motor.transcritor_card import transcrever_cards
from agente_medico.motor.transcritor_pgr import gate_forma_ghe

CAMINHO_PGR_CJR = Path("matrizes_originais/pgr_Cjr Engenharia Ltda (M Construtora).pdf")

# Fixtures reais reusadas EXATAS de test_extracao_pgr.py (mesmos caminhos,
# mesma extração) — molde do harness de test_transcritor_pgr.py.
try:
    from agente_medico.tests.test_extracao_pgr import (  # noqa: F401
        paginas_ebserh_humap,
        paginas_ebserh_ufgd_v7,
    )
except ImportError:
    from agente_medico.tests.test_extracao_pgr import (
        CAMINHO_PGR_EBSERH_HUMAP,
        CAMINHO_PGR_EBSERH_UFGD_V7,
    )

    @pytest.fixture(scope="module")
    def paginas_ebserh_ufgd_v7() -> list[str]:
        return extrair_texto_pgr(CAMINHO_PGR_EBSERH_UFGD_V7)

    @pytest.fixture(scope="module")
    def paginas_ebserh_humap() -> list[str]:
        return extrair_texto_pgr(CAMINHO_PGR_EBSERH_HUMAP)


class MockTranscritorCard:
    """Mock injetável (D-ARQ-49 P4 molde: LLM SEMPRE mockado em teste, nunca
    API real). resultado fixo por (card, titulo) via overrides; padrao cobre
    pares sem override explícito. Captura pares_recebidos na ordem.
    """

    def __init__(
        self,
        padrao: GHEVerbatim,
        overrides: dict[tuple[str, str], GHEVerbatim] | None = None,
    ) -> None:
        self._padrao = padrao
        self._overrides = overrides or {}
        self.pares_recebidos: list[tuple[str, str]] = []

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        self.pares_recebidos.append((card, titulo))
        return self._overrides.get((card, titulo), self._padrao)


def _ghe(
    nome: str = "Advogado",
    cargos: tuple[str, ...] = (),
    riscos: tuple[RiscoVerbatim, ...] = (),
) -> GHEVerbatim:
    return GHEVerbatim(nome=nome, cargos=cargos, riscos=riscos)


def _risco(agente: str = "Ruído", quantificacao: str = "", fonte_geradora: str = "") -> RiscoVerbatim:
    return RiscoVerbatim(agente=agente, quantificacao=quantificacao, fonte_geradora=fonte_geradora)


# ---------------------------------------------------------------------------
# Núcleo — rodam sempre, sem PDF.
# ---------------------------------------------------------------------------


def test_transcrever_cards_delega_na_ordem_e_pareia_card_titulo_verbatim() -> None:
    card1 = "Lotação: Escala de Trabalho: Qtde: linha A\nconteudo 1"
    card2 = "Lotação: Escala de Trabalho: Qtde: linha B\nconteudo 2"
    titulo1 = "13.1 Advogado"
    titulo2 = "13.2 Analista"
    resultado1 = _ghe(nome="Um")
    resultado2 = _ghe(nome="Dois")
    mock = MockTranscritorCard(
        padrao=_ghe(nome="nao deveria ser usado"),
        overrides={(card1, titulo1): resultado1, (card2, titulo2): resultado2},
    )
    saida = transcrever_cards([card1, card2], [titulo1, titulo2], mock)
    assert saida == (resultado1, resultado2)
    assert mock.pares_recebidos == [(card1, titulo1), (card2, titulo2)]


def test_transcrever_cards_listas_vazias_devolve_tupla_vazia() -> None:
    mock = MockTranscritorCard(padrao=_ghe())
    assert transcrever_cards([], [], mock) == ()
    assert mock.pares_recebidos == []


def test_transcrever_cards_tamanhos_divergentes_levanta_value_error() -> None:
    mock = MockTranscritorCard(padrao=_ghe())
    with pytest.raises(ValueError):
        transcrever_cards(["card1", "card2"], ["titulo1"], mock)


def test_composicao_transcrever_cards_gate_forma_ghe_nome_vazio_reprova() -> None:
    mock = MockTranscritorCard(padrao=_ghe(nome="  ", riscos=(_risco(),)))
    candidatos = transcrever_cards(["card1"], ["titulo1"], mock)
    aprovados, pendencias = gate_forma_ghe(candidatos)
    assert aprovados == ()
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert isinstance(pendencia, Pendencia)
    assert pendencia.tipo == "forma_verbatim_pgr"
    assert pendencia.bloqueante is True


def test_composicao_card_todo_na_sem_riscos_aprova_no_gate() -> None:
    # Regressão 003.DG-3: card administrativo (todo N/A) é forma legítima —
    # GHEVerbatim(riscos=()) não reprova sozinho.
    mock = MockTranscritorCard(padrao=_ghe(nome="Cargo administrativo", riscos=()))
    candidatos = transcrever_cards(["card1"], ["titulo1"], mock)
    aprovados, pendencias = gate_forma_ghe(candidatos)
    assert aprovados == candidatos
    assert pendencias == ()


# ---------------------------------------------------------------------------
# Integração real (falha explícita, NÃO skip — precedente 003.DA; reusa
# exatamente os caminhos/fixtures dos testes reais de recortar_cards_cargo/
# recuperar_titulos_cargo já existentes em test_extracao_pgr.py).
# ---------------------------------------------------------------------------


def test_transcrever_cards_ufgd_v7_real_105_pares_titulos_extremos(
    paginas_ebserh_ufgd_v7: list[str],
) -> None:
    cards = recortar_cards_cargo(paginas_ebserh_ufgd_v7)
    titulos = recuperar_titulos_cargo(paginas_ebserh_ufgd_v7)
    mock = MockTranscritorCard(padrao=_ghe(riscos=(_risco(),)))
    transcrever_cards(cards, titulos, mock)
    assert len(mock.pares_recebidos) == 105
    assert mock.pares_recebidos[0][1] == "13.1 Advogado"
    assert mock.pares_recebidos[-1][1] == "13.106 Terapeuta Ocupacional"


def test_transcrever_cards_humap_real_140_pares_titulos_vazios(
    paginas_ebserh_humap: list[str],
) -> None:
    cards = recortar_cards_cargo(paginas_ebserh_humap)
    titulos = recuperar_titulos_cargo(paginas_ebserh_humap)
    mock = MockTranscritorCard(padrao=_ghe(riscos=(_risco(),)))
    transcrever_cards(cards, titulos, mock)
    assert len(mock.pares_recebidos) == 140
    assert all(titulo == "" for _, titulo in mock.pares_recebidos)


def test_transcrever_cards_cjr_real_1_par_titulo_vazio() -> None:
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    cards = recortar_cards_cargo(paginas_cjr)
    titulos = recuperar_titulos_cargo(paginas_cjr)
    mock = MockTranscritorCard(padrao=_ghe(riscos=(_risco(),)))
    transcrever_cards(cards, titulos, mock)
    assert len(mock.pares_recebidos) == 1
    assert mock.pares_recebidos[0][1] == ""
