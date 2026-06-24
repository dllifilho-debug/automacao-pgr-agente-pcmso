from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.orquestrador import executar_com_composicao
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ProdutoQuimico, FDS, Componente
from agente_medico.tests.fixtures.fds_t65 import (
    tinta_acrilica, cimento_ciplan, adesivo_pvc_tigre,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)
_HOJE = date(2025, 1, 1)


def _ghe_com_fds(ghe_id: str, componentes: tuple[Componente, ...]) -> GHEPGR:
    return GHEPGR(
        id=ghe_id, nome=ghe_id, cargos=(), riscos=(), epis=(),
        produtos_quimicos=(ProdutoQuimico(nome=ghe_id, fds=FDS(composicao=componentes)),),
        psicossocial=False,
    )


def _pgr_cru() -> PGR:
    return PGR(
        validade=date(2025, 1, 1), assinatura_engenheiro=True,
        ghes=(
            _ghe_com_fds("adesivo", adesivo_pvc_tigre()),
            _ghe_com_fds("tinta", tinta_acrilica()),
            _ghe_com_fds("cimento", cimento_ciplan()),
        ),
    )


def test_processar_pgr_constroi_indice_internamente() -> None:
    resultado = processar_pgr(_pgr_cru(), _PROTO)
    assert resultado.status in ("OK", "PRELIMINAR", "REJEITADO")


def test_processar_pgr_equivale_ao_wrapper() -> None:
    pgr_cru = _pgr_cru()
    indice = construir_indice_cas(_PROTO.vocabulario.agentes)
    esperado = executar_com_composicao(pgr_cru, _PROTO, indice, _HOJE)
    obtido = processar_pgr(pgr_cru, _PROTO, _HOJE)
    assert obtido.status == esperado.status
    assert len(obtido.matrizes) == len(esperado.matrizes)
    n_linhas_obtido = sum(len(m.linhas) for m in obtido.matrizes)
    n_linhas_esperado = sum(len(m.linhas) for m in esperado.matrizes)
    assert n_linhas_obtido == n_linhas_esperado
    assert len(obtido.pendencias_globais) == len(esperado.pendencias_globais)


def test_processar_pgr_repassa_hoje() -> None:
    # R-PGR-06 (gates.py): (hoje - pgr.validade) >= 730 dias -> REJEITADO.
    pgr_cru = _pgr_cru()
    resultado_dentro_validade = processar_pgr(pgr_cru, _PROTO, date(2025, 1, 1))
    resultado_pgr_vencido = processar_pgr(pgr_cru, _PROTO, date(2027, 1, 1))
    assert resultado_dentro_validade.status != "REJEITADO"
    assert resultado_pgr_vencido.status == "REJEITADO"


def test_import_canonico() -> None:
    from agente_medico.motor import processar_pgr as processar_pgr_canonico
    assert processar_pgr_canonico is processar_pgr
