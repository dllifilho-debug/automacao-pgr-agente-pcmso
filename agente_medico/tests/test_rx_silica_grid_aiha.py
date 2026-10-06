"""R-RX-01-qual na rota grid (D-ARQ-57 peça 5, nota de 06/10/2026): a linha da
tabela AIHA é avaliação qualitativa, e sílica sem medição com avaliação sai 12M.
A escala AIHA não vira nivel_risco — R-BIO-05 e a dispensa por IRRELEVANTE não
a leem. Caso medido: azulejista do Hetrin REV06 ("POEIRA – SILICA", NÍVEL DE
RISCO 2 – DE ATENÇÃO), matriz 14.09.26 com RX OIT PER 12 meses. Cada teste
nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.hidratacao import hidratar_ghe
from agente_medico.motor.parser_familia_grid_aiha import GrupoFuncaoAIHA
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import IndiceTermos, construir_indice_termos
from agente_medico.motor.tipos import ExameEmitido, GHEContext, GHEPGR, GHEVerbatim, RiscoVerbatim
from agente_medico.motor.transcritor_grid import EntradaGrid, transcrever_grupos_grid

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def indice(proto: Protocolo) -> IndiceTermos:
    return construir_indice_termos(proto.vocabulario.agentes)


class _ClienteGrid:
    """Devolve o que o Gemini do grid devolveria para o azulejista — e, para que a
    guarda da escala seja testável, uma avaliação que o prompt manda não preencher
    e que, se passasse, o parser P×S leria como nível ("1 1 IRRELEVANTE": colunas
    PROBABILIDADE e CLASSIFICAÇÃO do grid lidas como P e NÍVEL)."""

    def __init__(self, agente: str) -> None:
        self._agente = agente

    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]:
        return tuple(
            GHEVerbatim(
                nome=e.nome_verbatim,
                cargos=(e.nome_verbatim,),
                riscos=(
                    RiscoVerbatim(self._agente, "", "", avaliacao_qualitativa="1 1 IRRELEVANTE"),
                ),
            )
            for e in entradas
        )


def _ghe_pgr_pela_rota_grid(indice: IndiceTermos, agente: str) -> GHEPGR:
    (verbatim,) = transcrever_grupos_grid(
        [GrupoFuncaoAIHA(nome="AZULEJISTA", linhas=())], _ClienteGrid(agente)
    )
    ghe_pgr, _ = hidratar_ghe(verbatim, indice, posicao=1)
    return ghe_pgr


def _rx(proto: Protocolo, ghe_pgr: GHEPGR) -> ExameEmitido:
    ctx = GHEContext(pgr_ghe=ghe_pgr)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return next(e for e in stage_5_emissao(ctx, proto) if e.exame == "rx_torax_oit")


def test_silica_do_grid_sai_12m_por_r_rx_01_qual(proto: Protocolo, indice: IndiceTermos) -> None:
    # Reversões que matam, cada uma sozinha: (a) _avaliacao_aiha não marcar
    # avaliacao_qualitativa_aiha=True; (b) hidratar_ghe não passar o campo ao
    # RiscoPGR; (c) stage_2_riscos não copiá-lo para Risco; (d) _helper_silica_asbesto
    # voltar a ler só nivel_risco. Em todas, o azulejista volta a 24M (R-RX-01-sem).
    rx = _rx(proto, _ghe_pgr_pela_rota_grid(indice, "POEIRA – SILICA"))

    assert rx.periodicidade_meses == 12
    assert [m.regra_id for m in rx.motivos] == ["R-RX-01-qual"]


def test_escala_aiha_nao_vira_nivel_de_risco(indice: IndiceTermos) -> None:
    # Reversão que mata: _avaliacao_aiha deixar de esvaziar avaliacao_qualitativa
    # — o "IRRELEVANTE" da coluna Classificação viraria nivel_risco e
    # alimentaria R-BIO-05 e a dispensa por IRRELEVANTE, que são da escala P×S.
    (risco,) = _ghe_pgr_pela_rota_grid(indice, "POEIRA – SILICA").riscos

    assert risco.agente == "silica"
    assert risco.nivel_risco is None
    assert risco.avaliacao_qualitativa_aiha is True


def test_asbesto_do_grid_segue_24m(proto: Protocolo, indice: IndiceTermos) -> None:
    # A decisão de 23/09 (R-RX-01-qual) é só sobre sílica. Reversão que mata:
    # escrever o helper como `(agente == "silica" and nivel_risco is not None)
    # or avaliacao_qualitativa_aiha` — o asbesto do grid cairia em 12M.
    rx = _rx(proto, _ghe_pgr_pela_rota_grid(indice, "ASBESTO"))

    assert rx.periodicidade_meses == 24
    assert [m.regra_id for m in rx.motivos] == ["R-RX-01-sem"]
