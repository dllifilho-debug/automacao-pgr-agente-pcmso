"""Inventário psicossocial avaliado (R-PSY-06/R-PSY-08, solução D, 09/10/2026): conta só o
PGR com linha de fator "Psicossocial … nível", e o corte "moderado ou acima" decide a
saúde mental. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

import agente_medico.adaptadores.orquestracao_pgr as orq
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline
from agente_medico.motor.extracao_pgr import avaliar_inventario_psicossocial
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.io_pdf import PaginaLida
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import EnvelopeConfirmado, GHEVerbatim, RiscoVerbatim

_PROTOCOLO = carregar(Path(__file__).parent.parent / "protocolo")
_NIVEIS = _PROTOCOLO.vocabulario.niveis_risco

# Verbatim do PGR SPE QD. E-13 (30/09/2026, pág. 22): cita o inventário e o COPSOQ, sem avaliar.
_CITADO_SEM_AVALIACAO = (
    "INVENTÁRIO DE RISCOS PSICOSSOCIAIS POR GHE\n"
    "Avaliação de Riscos Psicossociais — Antecipação Técnica. Em conformidade com a Nota Técnica "
    "SSTmétrica n.º 02/2026, a avaliação dos fatores de risco psicossociais não foi realizada nesta "
    "fase da obra (COPSOQ II-BR ou AQUALI-RPS)."
)
# Linhas no formato do inventário da Vila Brasil escritório (06/10/2026, págs. 78–79).
_FATOR_BAIXO = "Psicossocial Demandas no trabalho Refere - se à intensidade das Transtorno mentais; 3 1 BAIXO"
_FATOR_MODERADO = "Psicossocial Conflitos família e Refere - se à interferência do trabalho 3 2 MODERADO"


def test_inventario_so_citado_nao_conta_como_avaliado() -> None:
    # Reversão que mata: `avaliado` voltar a ser só o marcador (detectar_psicossocial) —
    # o caso E-13/Verde Maris/Sinduscon/Seconci REV4 volta a dar Saúde Mental.
    inventario = avaliar_inventario_psicossocial([_CITADO_SEM_AVALIACAO], _NIVEIS)
    assert inventario == (False, False)


def test_inventario_so_com_fatores_baixos_e_avaliado_abaixo_do_corte() -> None:
    # Reversão que mata: `moderado_ou_acima` igual a `avaliado` (ignorar o nível).
    inventario = avaliar_inventario_psicossocial(["COPSOQ II-BR\n" + _FATOR_BAIXO], _NIVEIS)
    assert inventario == (True, False)


def test_inventario_com_um_fator_moderado_entre_baixos_passa_o_corte() -> None:
    # O fator moderado vem depois de um baixo, como nos PGRs do acervo. Reversão que mata:
    # olhar só o primeiro fator lido (`posicoes[0] == "corte"`).
    paginas = ["COPSOQ II-BR\n" + _FATOR_BAIXO, _FATOR_MODERADO]
    assert avaliar_inventario_psicossocial(paginas, _NIVEIS) == (True, True)


def test_linha_de_fator_sem_marcador_do_inventario_nao_conta() -> None:
    # Reversão que mata: tirar a exigência do marcador (detectar_psicossocial) da função.
    assert avaliar_inventario_psicossocial([_FATOR_MODERADO], _NIVEIS) == (False, False)


def test_hidratar_pgr_replica_o_corte_a_todos_os_ghe() -> None:
    # Reversões que matam: (1) não repassar `psicossocial_moderado` de hidratar_pgr a
    # hidratar_ghe; (2) não gravá-lo no GHEPGR.
    indice = construir_indice_termos(
        _PROTOCOLO.vocabulario.agentes, fracoes_sem_agente=_PROTOCOLO.vocabulario.fracoes_sem_agente
    )
    ghe = GHEVerbatim(nome="Setor", cargos=("Servente",), riscos=())
    pgr, _ = hidratar_pgr(
        (ghe, ghe), indice, date(2026, 9, 1), True, psicossocial=True, psicossocial_moderado=True
    )
    assert [(g.psicossocial, g.psicossocial_moderado) for g in pgr.ghes] == [(True, True), (True, True)]


_GHE = GHEVerbatim(
    nome="Setor Teste",
    cargos=("Servente",),
    riscos=(RiscoVerbatim(agente="Ruido", quantificacao="", fonte_geradora="Fonte X"),),
)


@pytest.mark.parametrize(
    ("inventario", "esperado"),
    [
        ("COPSOQ II-BR\n" + _FATOR_BAIXO + "\n" + _FATOR_MODERADO, (True, True)),
        (_CITADO_SEM_AVALIACAO, (False, False)),
    ],
)
def test_preparar_pgr_hidratado_le_o_inventario_avaliado(
    monkeypatch: pytest.MonkeyPatch, inventario: str, esperado: tuple[bool, bool]
) -> None:
    # Reversões que matam: (1) o orquestrador voltar a detectar_psicossocial — o PGR só
    # citado sai com inventário e o avaliado sai sem o corte; (2) repassar só
    # `inventario.avaliado` a hidratar_pgr — o corte fica False.
    leitura = (PaginaLida("GHE 1 - Setor Teste\nCargo A\n" + inventario, ()),)

    def _ler(caminho: Path, processos: int | None = None) -> tuple[PaginaLida, ...]:
        return leitura

    def _parsear(_: Any) -> tuple[GHEVerbatim, ...]:
        return (_GHE,)

    monkeypatch.setattr(orq, "ler_pdf", _ler)
    monkeypatch.setattr(orq, "parsear_leitura", _parsear)
    pgr, _ = orq.preparar_pgr_hidratado(
        Path("qualquer.pdf"),
        _PROTOCOLO,
        TranscritorGHEOffline(),
        TranscritorCardOffline(),
        EnvelopeConfirmado(validade=date(2026, 9, 1), assinatura_engenheiro=True),
    )
    assert pgr is not None
    assert (pgr.ghes[0].psicossocial, pgr.ghes[0].psicossocial_moderado) == esperado
