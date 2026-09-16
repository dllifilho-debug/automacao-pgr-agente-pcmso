# R-RX-03/R-ESP-03 — poeira de madeira, agente identificável fora dos dois
# quadros do Anexo III NR-07 (DT-003EJ-01, RESOLVIDA). SEM âncora normativa
# brasileira: RX 60M e Espirometria 24M vêm de 2 PGRs independentes, mesma
# médica (Dra. Patrícia Montalvo Moraes), mesmo cargo (Carpintaria) — GHE-08
# do PGR CONSCIENTE SPE 0030 FASCINO (15.07.26) e GHE-04 do PGR CMO
# Residencial Aurora Lago das Rosas (27.08.26), ambos com os mesmos valores.
from __future__ import annotations

from pathlib import Path

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEContext, GHEPGR, Momento, RiscoPGR

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

_MOMENTOS_ESPERADOS = {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}


def _proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _ctx_com_agente(agente: str | None) -> tuple[GHEContext, Protocolo]:
    proto = _proto()
    riscos = () if agente is None else (
        RiscoPGR(tipo="quimico", agente=agente, quantificacao=None, severidade=None),
    )
    ghe = GHEPGR(
        id="GHE-01",
        nome="Teste Poeira de Madeira",
        cargos=(),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return ctx, proto


def test_poeira_de_madeira_emite_rx_torax_60m() -> None:
    # Reversão: remover a regra R-RX-03 (ou o agente poeira_de_madeira) de
    # regras.yaml/agentes.yaml faz este teste falhar — rx_torax_oit não é
    # emitido, ou emitido sem o motivo R-RX-03.
    ctx, proto = _ctx_com_agente("poeira_de_madeira")
    exames = stage_5_emissao(ctx, proto)
    rx = next(e for e in exames if e.exame == "rx_torax_oit")
    assert rx.periodicidade_meses == 60
    assert rx.periodicidade_apos_15a is None
    assert _MOMENTOS_ESPERADOS.issubset(rx.momentos)
    assert any(m.regra_id == "R-RX-03" for m in rx.motivos)


def test_poeira_de_madeira_emite_espirometria_24m() -> None:
    # Reversão: remover a regra R-ESP-03 faz este teste falhar — espirometria
    # não é emitida para poeira_de_madeira (R-ESP-02 não cobre, é escopo
    # "poeira mineral", madeira é orgânica).
    ctx, proto = _ctx_com_agente("poeira_de_madeira")
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert esp.periodicidade_meses == 24
    assert esp.periodicidade_apos_15a is None
    assert _MOMENTOS_ESPERADOS.issubset(esp.momentos)
    assert any(m.regra_id == "R-ESP-03" for m in esp.motivos)


def test_sem_poeira_de_madeira_nao_emite_nenhum_dos_dois() -> None:
    ctx, proto = _ctx_com_agente(None)
    exames = stage_5_emissao(ctx, proto)
    assert [e for e in exames if e.exame == "rx_torax_oit"] == []
    assert [e for e in exames if e.exame == "espirometria"] == []


def test_poeira_de_madeira_nao_dispara_r_esp_02() -> None:
    # Confirma que R-ESP-02 (poeira mineral: sílica/asbesto/pnos) não
    # confunde madeira com mineral — R-ESP-03 é ID separada, não faixa nova
    # de R-ESP-02.
    ctx, proto = _ctx_com_agente("poeira_de_madeira")
    exames = stage_5_emissao(ctx, proto)
    esp = next(e for e in exames if e.exame == "espirometria")
    assert all(m.regra_id != "R-ESP-02" for m in esp.motivos)
