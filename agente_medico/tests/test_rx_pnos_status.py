"""R-RX-01-pnos-* — status pela hierarquia de D-ARQ-22 (decisão do Diovanni, 29/09/2026).
NR-07 Anexo III Quadro 2 dá a periodicidade; mudança de risco e demissional vêm do
precedente (Patrícia/Aurora 27.08.26, faixa sem medição) ou da analogia com a faixa de
sílica equivalente (>100% LEO). A faixa 10–100% segue INTERPRETADO: emite menos que o
Quadro 2 (DT-002Y-01). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import GHEPGR, PGR, RiscoPGR
from agente_medico.superficie.memorial_matriz import ROTULO_CERTEZA, montar_memorial, resumos_do_protocolo

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


@pytest.mark.parametrize(
    "regra_id,status",
    [
        ("R-RX-01-pnos-sem", "DERIVADO"),
        ("R-RX-01-pnos-acima100", "DERIVADO"),
        ("R-RX-01-pnos-ate10", "DERIVADO"),
        ("R-RX-01-pnos-10a100", "INTERPRETADO"),
    ],
)
def test_status_das_faixas_pnos(proto: Protocolo, regra_id: str, status: str) -> None:
    # Reversões que matam: voltar qualquer uma das três a INTERPRETADO; subir a
    # 10a100, que ainda não emite o RX aos 5 anos do Quadro 2.
    (regra,) = [r for r in proto.regras if r["id"] == regra_id]
    assert regra["status"] == status


def test_pnos_sem_medicao_sai_de_confirmar_primeiro(proto: Protocolo) -> None:
    # Caminho real: PNOS sem medição → R-RX-01-pnos-sem → memorial. Reversão que mata:
    # R-RX-01-pnos-sem de volta a INTERPRETADO (a regra volta a "Confirmar primeiro" e a
    # linha a "Interpretação do sistema").
    risco = RiscoPGR(tipo="", agente="poeira_nao_classificada", quantificacao=None, severidade=None, nivel_risco="MODERADO")
    ghe = GHEPGR(id="GHE-01", nome="ADMINISTRAÇÃO", cargos=("Administrativo",), riscos=(risco,), epis=(),
                 produtos_quimicos=(), psicossocial=False)
    (matriz,) = executar(PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,)), proto,
                         hoje=date(2026, 9, 29)).matrizes
    assert [m.regra_id for e in matriz.linhas if e.exame == "rx_torax_oit" for m in e.motivos] == ["R-RX-01-pnos-sem"]

    memorial = montar_memorial([matriz], proto.vocabulario.exames, resumos_do_protocolo(proto.regras))

    assert "R-RX-01-pnos-sem" not in {d.regra_id for d in memorial.revisar_primeiro}
    (rx,) = [linha for bloco in memorial.blocos for linha in bloco.linhas if linha.exame.startswith("RX Tórax")]
    assert rx.certeza == ROTULO_CERTEZA[2]
