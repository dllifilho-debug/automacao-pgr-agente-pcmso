"""D-ARQ-95 — nível de risco do PGR em qualquer escala, para a sugestão do ASO: vocabulário
`niveis_risco.yaml` (censo de 08/10/2026), rótulo levado das rotas até o Risco, e a
sugestão usando-o quando não há nível P×S. A matriz de exames não lê nada disto. Cada teste
nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

from agente_medico.adaptadores.transcritor_gemini_grid import _PROMPT_GRID_LOTE
from agente_medico.adaptadores.transcritor_gemini_pgr import _PROMPT_GHE, _PROMPT_GHE_LOTE, _ghe_de_dict
from agente_medico.motor.hidratacao import hidratar_ghe
from agente_medico.motor.niveis_pgr import NivelPGR, classificar_nivel_pgr
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, _carregar_niveis_risco, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.sugestao_aso import sugerir_aso
from agente_medico.motor.tipos import GHEPGR, PGR, GHEVerbatim, Risco, RiscoPGR, RiscoVerbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def niveis(proto: Protocolo) -> dict[str, Any]:
    return proto.vocabulario.niveis_risco


# --- Vocabulário e resolução -------------------------------------------------


@pytest.mark.parametrize(
    ("texto", "esperado"),
    [
        ("2 - MODERADO", NivelPGR("MODERADO", "corte")),  # AIHA Ricco
        ("Tolerável", NivelPGR("TOLERÁVEL", "abaixo")),  # BS 8800
        ("2 3 SUBSTANCIAL (6)", NivelPGR("SUBSTANCIAL", "corte")),
        ("Médio", NivelPGR("MÉDIO", "corte")),  # Sinduscon-GO, Ricco Administração [INTERPRETADO]
        ("NÃO TOLERÁVEL", NivelPGR("NÃO TOLERÁVEL", "corte")),
        ("4 - muito alto", NivelPGR("MUITO ALTO", "corte")),
    ],
)
def test_rotulos_do_censo_tem_posicao(niveis: dict[str, Any], texto: str, esperado: NivelPGR) -> None:
    # Reversões que matam: (1) tirar a entrada do rótulo do yaml (ex.: MÉDIO) — sai None;
    # (2) trocar a posição de TOLERÁVEL para corte; (3) casar sem ordenar do mais longo ao
    # mais curto — "NÃO TOLERÁVEL" vira o TOLERÁVEL de dentro dele, abaixo.
    assert classificar_nivel_pgr(texto, niveis) == esperado


def test_rotulos_em_posicoes_diferentes_nao_decidem(niveis: dict[str, Any]) -> None:
    # Reversão que mata: devolver o primeiro achado em vez de None quando as posições
    # divergem — a sugestão escolheria um lado sem fundamento.
    assert classificar_nivel_pgr("1 - BAIXO 2 - MODERADO", niveis) is None


@pytest.mark.parametrize("texto", ["2 - DE ATENÇÃO", "", "Classe C"])
def test_texto_sem_rotulo_conhecido_nao_decide(niveis: dict[str, Any], texto: str) -> None:
    # A classificação de prioridade AIHA ("DE ATENÇÃO") não é nível. Reversão que mata:
    # pôr "DE ATENÇÃO" no vocabulário.
    assert classificar_nivel_pgr(texto, niveis) is None


def test_vocabulario_com_posicao_invalida_falha_no_carregamento(tmp_path: Path) -> None:
    # Reversão que mata: tirar a validação de `_carregar_niveis_risco`.
    arquivo = tmp_path / "niveis_risco.yaml"
    arquivo.write_text("niveis_risco:\n  MODERADO:\n    posicao: meio\n", encoding="utf-8")
    with pytest.raises(ValueError, match="MODERADO"):
        _carregar_niveis_risco(arquivo)


# --- O rótulo chega ao risco ---------------------------------------------------


def test_hidratacao_guarda_o_rotulo_do_campo_ou_da_avaliacao(proto: Protocolo) -> None:
    # Reversões que matam: (1) não passar `nivel_pgr=` na hidratação; (2) tirar o
    # `or avaliacao_qualitativa` — o rótulo das rotas que só preenchem a avaliação some.
    indice = construir_indice_termos(proto.vocabulario.agentes)
    ghe = GHEVerbatim(
        nome="T",
        cargos=("Servente",),
        riscos=(
            RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora="", nivel_pgr="Tolerável"),
            RiscoVerbatim(agente="Piso irregular", quantificacao="", fonte_geradora="", avaliacao_qualitativa="1 2 BAIXO (2)"),
        ),
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice, posicao=1)
    assert [(r.nivel_pgr, r.nivel_risco) for r in ghe_pgr.riscos] == [("Tolerável", None), ("1 2 BAIXO (2)", "BAIXO")]


def test_resposta_da_ia_traz_nivel_e_letra_do_tipo() -> None:
    # Reversões que matam: (1) não ler `nivel_pgr` em _ghe_de_dict; (2) não converter a
    # letra do TIPO DE RISCO em grupo (ou aceitar letra desconhecida).
    ghe = _ghe_de_dict({
        "nome": "PEDREIRO",
        "cargos": ["PEDREIRO"],
        "riscos": [
            {"agente": "POEIRA - PNOS", "nivel_pgr": "2 - MODERADO", "tipo_risco": "q"},
            {"agente": "INCÊNDIO", "nivel_pgr": "1 - BAIXO", "tipo_risco": "X"},
        ],
    })
    assert [(r.nivel_pgr, r.grupo) for r in ghe.riscos] == [("2 - MODERADO", "QUIMICO"), ("1 - BAIXO", "")]


def test_prompts_pedem_o_nivel_e_o_grid_pede_a_letra() -> None:
    # Reversões que matam: tirar o campo nivel_pgr do formato pedido no prompt GHE (unitário
    # ou em lote, o de produção) ou no do grid; tirar tipo_risco do prompt do grid.
    assert '"nivel_pgr"' in _PROMPT_GHE and '"nivel_pgr"' in _PROMPT_GHE_LOTE
    assert '"nivel_pgr"' in _PROMPT_GRID_LOTE and '"tipo_risco"' in _PROMPT_GRID_LOTE


# --- Sugestão do ASO -------------------------------------------------------------


def _risco(agente: str, nivel_pgr: str = "", nivel_risco: str | None = None, ototoxico: bool = False) -> Risco:
    return Risco(
        agente=agente, fonte="explicito", detalhe=None, quantificacao=None, tipo_ibe=None,
        is_ototoxico=ototoxico, nivel_risco=nivel_risco, nivel_pgr=nivel_pgr,
    )


def _veredito(proto: Protocolo, *riscos: Risco, agente: str) -> str:
    relatorio = sugerir_aso([], riscos, (), proto.vocabulario.agentes, proto.vocabulario.niveis_risco)
    (s,) = [s for s in relatorio.riscos if s.risco == agente]
    return s.veredito


@pytest.mark.parametrize(
    ("nivel_pgr", "veredito"),
    [("SUBSTANCIAL", "CONSTA"), ("2 - MODERADO", "CONSTA"), ("Tolerável", "NAO_CONSTA"), ("Classe C", "CONFERIR")],
)
def test_regra_geral_usa_o_rotulo_sem_nivel_pxs(proto: Protocolo, nivel_pgr: str, veredito: str) -> None:
    # Reversão que mata: `_nivel` ignorar `nivel_pgr` — tudo sai CONFERIR.
    assert _veredito(proto, _risco("queda_de_materiais", nivel_pgr), agente="queda_de_materiais") == veredito


def test_nivel_pxs_decide_antes_do_rotulo(proto: Protocolo) -> None:
    # Reversão que mata: consultar o vocabulário antes do nível P×S.
    risco = _risco("queda_de_materiais", nivel_pgr="MODERADO", nivel_risco="BAIXO")
    assert _veredito(proto, risco, agente="queda_de_materiais") == "NAO_CONSTA"


def test_ruido_de_outra_escala(proto: Protocolo) -> None:
    # Reversões que matam: (1) `baixo` só com nível P×S BAIXO — Tolerável com ototóxico
    # sairia não consta; (2) o ruído ignorar `nivel_pgr` — MODERADO sairia conferir.
    assert _veredito(proto, _risco("ruido", "MODERADO"), agente="ruido") == "CONSTA"
    assert _veredito(proto, _risco("ruido", "Tolerável"), agente="ruido") == "NAO_CONSTA"
    assert _veredito(proto, _risco("ruido", "Tolerável"), _risco("tolueno", ototoxico=True), agente="ruido") == "CONSTA"


def test_ruido_pxs_irrelevante_com_agravante_segue_nao_consta(proto: Protocolo) -> None:
    # A escala P×S não muda: o "mesmo baixo" do e-mail é BAIXO, não IRRELEVANTE. Reversão
    # que mata: `baixo = nivel is not None` (todo nível abaixo do corte, também na P×S).
    riscos = (_risco("ruido", nivel_risco="IRRELEVANTE"), _risco("tolueno", ototoxico=True))
    assert _veredito(proto, *riscos, agente="ruido") == "NAO_CONSTA"


@pytest.mark.parametrize(("nivel_pgr", "veredito"), [("2 - MODERADO", "CONSTA"), ("1 - BAIXO", "NAO_CONSTA")])
def test_termo_nao_reconhecido_usa_o_rotulo(proto: Protocolo, nivel_pgr: str, veredito: str) -> None:
    # Reversão que mata: `_criterio_termo` ignorar `nivel_pgr` — os dois saem CONFERIR.
    termo = RiscoPGR(tipo="ACIDENTE", agente=None, quantificacao=None, severidade=None, termo="INCÊNDIO", nivel_pgr=nivel_pgr)
    relatorio = sugerir_aso([], [], (termo,), proto.vocabulario.agentes, proto.vocabulario.niveis_risco)
    assert relatorio.riscos[0].veredito == veredito


def test_orquestrador_leva_o_rotulo_ate_a_sugestao(proto: Protocolo) -> None:
    # Reversões que matam: (1) não passar o vocabulário de níveis em `executar`; (2) não
    # copiar `nivel_pgr` para o Risco no estágio 2.
    ghe = GHEPGR(
        id="GHE-01", nome="ALVENARIA", cargos=("Pedreiro",),
        riscos=(RiscoPGR(tipo="", agente="queda_de_materiais", quantificacao=None, severidade=None, nivel_pgr="SUBSTANCIAL"),),
        epis=(), produtos_quimicos=(), psicossocial=True,
    )
    (matriz,) = executar(PGR(validade=date(2026, 9, 1), assinatura_engenheiro=True, ghes=(ghe,)), proto, hoje=date(2026, 10, 8)).matrizes
    (s,) = [s for s in matriz.sugestao_aso.riscos if s.risco == "queda_de_materiais"]
    assert s.veredito == "CONSTA"
