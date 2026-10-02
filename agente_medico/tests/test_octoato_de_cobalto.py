"""R-BIO-06 [INTERPRETADO]: octoato de cobalto (sal orgânico, fora do Quadro 1 da NR-07) —
menção no PCMSO em IRRELEVANTE/BAIXO, cobalto na urina 6M acima disso (NR-07 7.5.18).
Caso: Aurora 27.08.26 GHE 18 PINTURA, "Octoato de Cobalto" BAIXO; 7 matrizes CMO anotam a
menção. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import GHEVerbatim, MatrizGHE, RiscoVerbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 10, 3)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, termo: str, nivel: str) -> MatrizGHE:
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    pgr, _ = hidratar_pgr(
        [
            GHEVerbatim(
                nome="GHE 18 - PINTURA",
                cargos=("Pintor",),
                riscos=(
                    RiscoVerbatim(
                        agente=termo, quantificacao="", fonte_geradora="Atividade com pintura",
                        avaliacao_qualitativa=nivel,
                    ),
                ),
            )
        ],
        indice,
        date(2030, 1, 1),
        True,
    )
    (matriz,) = processar_pgr(pgr, proto, hoje=_HOJE).matrizes
    return matriz


def test_octoato_baixo_vira_mencao_sem_exame(proto: Protocolo) -> None:
    # Aurora: "Octoato de\nCobalto" (quebra de linha da célula do PDF), BAIXO.
    # Reversões que matam: (1) tirar a R-BIO-06 de regras.yaml — sem observação;
    # (2) tirar a chave mencao_documental — o exame sai; (3) tirar BAIXO de
    # niveis_risco — o exame sai; (4) apelidar o octoato de `cobalto` em vez de
    # slug próprio — a observação vem da R-BIO-04-cobalto.
    matriz = _matriz(proto, "Octoato de\nCobalto", "3 1 BAIXO (3)")

    assert "cobalto_urina" not in {e.exame for e in matriz.linhas}
    assert [(o.regra_id, o.agente, o.nivel_risco, o.exames_dispensados) for o in matriz.observacoes] == [
        ("R-BIO-06", "octoato_de_cobalto", "BAIXO", ("cobalto_urina",))
    ]


def test_octoato_moderado_pede_cobalto_na_urina_interpretado(proto: Protocolo) -> None:
    # Sem caso no acervo; vai para "Confirmar primeiro" pelo status.
    # Reversões que matam: (1) mudar periodicidade ou momentos da emissão;
    # (2) pôr MODERADO em niveis_risco — vira menção; (3) status diferente de
    # INTERPRETADO — o memorial deixa de pôr o exame para conferir primeiro.
    matriz = _matriz(proto, "Octoato de Cobalto", "3 2 MODERADO (6)")

    (linha,) = [e for e in matriz.linhas if e.exame == "cobalto_urina"]
    assert (linha.periodicidade_meses, {m.value for m in linha.momentos}) == (6, {"PER"})
    (motivo,) = [m for m in linha.motivos if m.regra_id == "R-BIO-06"]
    assert motivo.status_regra == "INTERPRETADO"
    assert matriz.observacoes == ()


def test_cas_da_fds_resolve_para_o_octoato(proto: Protocolo) -> None:
    # Reversão que mata: tirar `cas: "136-52-7"` do slug — componente de FDS
    # cairia em vocabulario_ausente.
    indice = construir_indice_cas(proto.vocabulario.agentes)
    assert indice["136527"].slug == "octoato_de_cobalto"
