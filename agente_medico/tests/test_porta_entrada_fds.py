"""Testes de test_porta_entrada_fds.py — 003.BC, fork A (D-ARQ-45/46).

montar_fds é a porta de entrada única de produção: verbatim (BlocoVerbatim) → FDS
com composicao VAZIA e composicao_verbatim preenchida. Quem resolve composicao é
resolver_composicao (herança-α + gate_cas, resolver-side); nenhum chamador constrói
FDS de verbatim na mão.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import FDS, GHEPGR, PGR, ProdutoQuimico
from agente_medico.motor.transcricao_fds import montar_composicao, montar_fds
from agente_medico.tests.fixtures.fds_t65 import tinta_acrilica
from agente_medico.tests.fixtures.fds_verbatim_t65 import tinta_acrilica_verbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)
_INDICE = construir_indice_cas(_PROTO.vocabulario.agentes)


def test_montar_fds_composicao_vazia_e_verbatim_montado() -> None:
    blocos = tinta_acrilica_verbatim()
    fds = montar_fds(blocos)
    assert fds.composicao == ()
    assert fds.composicao_verbatim == montar_composicao(blocos)


def _pgr_com_fds(fds: FDS) -> PGR:
    return PGR(
        validade=date(2026, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="G1",
                nome="GHE 1",
                cargos=("c",),
                riscos=(),
                epis=(),
                produtos_quimicos=(ProdutoQuimico(nome="Tinta", fds=fds),),
                psicossocial=False,
            ),
        ),
    )


def test_montar_fds_fim_a_fim_resolver_composicao_reproduz_gabarito() -> None:
    fds = montar_fds(tinta_acrilica_verbatim())
    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), _INDICE)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    comps = resolvido.composicao
    gabarito = tinta_acrilica()

    assert len(comps) == len(gabarito)
    for c, g in zip(comps, gabarito):
        assert c.cas == g.cas
        assert c.concentracao == g.concentracao


def test_montar_fds_composicao_verbatim_preservado_pos_resolver() -> None:
    fds = montar_fds(tinta_acrilica_verbatim())
    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), _INDICE)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    assert resolvido.composicao_verbatim == fds.composicao_verbatim
