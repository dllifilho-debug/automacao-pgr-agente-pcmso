"""R-PGR-07 — GHE com armador e sem poeira no inventário do PGR: pedido ao
elaborador para incluir a poeira do corte e dobra de aço, sem exame (NR-07
7.5.18 e Anexo III). Caso: Plateau rev 03, GHE 09 ARMAÇÃO. Cada teste nomeia a
reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.estagios.pendencias_estruturais import TIPO_POEIRA_NAO_INVENTARIADA
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, MatrizGHE, RiscoPGR
from agente_medico.superficie.memorial_matriz import pedidos_ao_elaborador

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 10, 16)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, cargos: tuple[str, ...], *agentes: str) -> MatrizGHE:
    ghe = GHEPGR(
        id="GHE-09",
        nome="Armação/Produção",
        cargos=cargos,
        riscos=tuple(
            RiscoPGR(tipo="", agente=a, quantificacao=None, severidade=None) for a in agentes
        ),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))
    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes
    return matriz


def _pedidos(matriz: MatrizGHE) -> list[str]:
    return [p.motivo for p in matriz.pendencias if p.tipo == TIPO_POEIRA_NAO_INVENTARIADA]


def test_armador_sem_poeira_gera_pedido_e_nenhum_exame(proto: Protocolo) -> None:
    # Reversões que matam: tirar a chamada de `_armacao_sem_poeira` do stage 3; ou
    # casar o cargo sem normalizar a caixa ("Meio Oficial de Armador" não casa).
    matriz = _matriz(proto, ("Meio Oficial de Armador", "Servente"), "ruido")

    (motivo,) = _pedidos(matriz)
    assert "Meio Oficial de Armador" in motivo
    exames = {e.exame for e in matriz.linhas}
    assert "espirometria" not in exames
    assert "rx_torax_oit" not in exames


def test_pedido_aparece_no_anexo_do_memorial(proto: Protocolo) -> None:
    # Reversão que mata: tirar TIPO_POEIRA_NAO_INVENTARIADA do filtro de
    # `pedidos_ao_elaborador` — o pedido fica fora da tela e do memorial.
    matriz = _matriz(proto, ("Armador",), "ruido")

    (texto,) = pedidos_ao_elaborador(matriz)
    assert "(ref. R-PGR-07)" in texto


def test_armador_com_poeira_no_pgr_nao_gera_pedido(proto: Protocolo) -> None:
    # Reversão que mata: tirar a checagem de `_AGENTES_POEIRA` — o pedido sairia mesmo
    # com a poeira declarada (e os exames já saindo pela R-ESP-02/R-RX-01).
    assert not _pedidos(_matriz(proto, ("Armador",), "poeira_nao_classificada"))


def test_ghe_sem_armador_nao_gera_pedido(proto: Protocolo) -> None:
    # Reversão que mata: tirar a condição `not cargos` — todo GHE sem poeira pediria.
    assert not _pedidos(_matriz(proto, ("Carpinteiro", "Servente"), "ruido"))
