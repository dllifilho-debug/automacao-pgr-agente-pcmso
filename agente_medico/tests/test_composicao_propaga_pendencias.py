from __future__ import annotations

from datetime import date
from pathlib import Path
import inspect

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.orquestrador import executar, executar_com_composicao
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    Componente, FDS, GHEPGR, PGR, ProdutoQuimico,
)
from agente_medico.tests.fixtures import bloco_de
from agente_medico.tests.fixtures.fds_t65 import (
    tinta_acrilica, cimento_ciplan, adesivo_pvc_tigre,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)
_INDICE = construir_indice_cas(_PROTO.vocabulario.agentes)
_HOJE = date(2025, 1, 1)  # pina o gate de validade; PGR.validade da fixture = 2025-01-01


def _ghe_com_fds(ghe_id: str, componentes: tuple[Componente, ...]) -> GHEPGR:
    return GHEPGR(
        id=ghe_id, nome=ghe_id, cargos=(), riscos=(), epis=(),
        produtos_quimicos=(
            ProdutoQuimico(
                nome=ghe_id,
                fds=FDS(composicao=(), composicao_verbatim=tuple(bloco_de(c) for c in componentes)),
            ),
        ),
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


# ---- MOV 1: resolver_composicao retorna pendências do gate distinguíveis por ramo ----
# Varre os 3 GHEs (adesivo+tinta+cimento). [1] agregado contém:
#   ramo (c) cas_invalido bloq  — TiO2 (tinta, 134363-67-7) e aluminato (cimento, 1242-78-3)
#   ramo (b) vocabulario_ausente não-bloq dest protocolo — copolimero PVC (adesivo, 9003-22-9) etc.
#   ramo (d) cas_ausente não-bloq — Segredo Industrial 1/2 (adesivo, cas="")
# Asserções por PRESENÇA (>=1 por tipo). NUNCA igualdade de contagem (fixture tem
# múltiplos de cada ramo; contagem exata é frágil a edição futura de fixture).

def test_resolver_composicao_retorna_tupla() -> None:
    out = resolver_composicao(_pgr_cru(), _INDICE)
    assert isinstance(out, tuple) and len(out) == 2
    pgr_resolvido, pend = out
    assert isinstance(pgr_resolvido, PGR)
    assert isinstance(pend, list)


def test_pendencias_gate_contem_ramo_c_bloqueante() -> None:
    _, pend = resolver_composicao(_pgr_cru(), _INDICE)
    c = [p for p in pend if p.tipo == "cas_invalido"]
    assert len(c) >= 1
    assert all(p.bloqueante for p in c)
    assert all(p.destinatario == "empresa" for p in c)


def test_pendencias_gate_contem_ramo_b_nao_bloqueante() -> None:
    _, pend = resolver_composicao(_pgr_cru(), _INDICE)
    b = [p for p in pend if p.tipo == "vocabulario_ausente"]
    assert len(b) >= 1
    assert all(not p.bloqueante for p in b)
    assert all(p.destinatario == "protocolo" for p in b)


def test_pendencias_gate_contem_ramo_d_nao_bloqueante() -> None:
    _, pend = resolver_composicao(_pgr_cru(), _INDICE)
    d = [p for p in pend if p.tipo == "cas_ausente"]
    assert len(d) >= 1
    assert all(not p.bloqueante for p in d)


def test_pendencias_gate_sem_ghe_id() -> None:
    _, pend = resolver_composicao(_pgr_cru(), _INDICE)
    assert pend  # garante não-vazio (senão all() é vácuo-verdadeiro)
    assert all(p.ghe_id is None for p in pend)


def test_tres_procedencias_coexistem_distinguiveis() -> None:
    _, pend = resolver_composicao(_pgr_cru(), _INDICE)
    tipos = {p.tipo for p in pend}
    assert {"cas_invalido", "vocabulario_ausente", "cas_ausente"} <= tipos


# ---- MOV 2: executar_com_composicao costura o [1] do gate em pendencias_globais ----
# Baseline = executar() sobre o MESMO pgr JÁ resolvido (isola a costura do gate de
# qualquer efeito da resolução). hoje pinado nos dois lados. NÃO asserir status
# (PGR validade=2025-01-01; ramo do gate de validade não importa p/ a costura).

def test_wrapper_costura_pendencias_gate_no_global() -> None:
    pgr_cru = _pgr_cru()
    pgr_resolvido, pend_gate = resolver_composicao(pgr_cru, _INDICE)
    base = executar(pgr_resolvido, _PROTO, _HOJE)
    wrap = executar_com_composicao(pgr_cru, _PROTO, _INDICE, _HOJE)
    # objetos distintos — remontagem, não o mesmo Resultado
    assert wrap is not base
    # toda pendência original de executar() permanece (anexação, não substituição)
    for p in base.pendencias_globais:
        assert p in wrap.pendencias_globais
    # o [1] do gate foi anexado: len(base + pend_gate) == len(base) + len(pend_gate)
    # (identidade de concatenação; testa que o wrapper fez base+pend_gate e nada mais)
    assert len(wrap.pendencias_globais) == len(base.pendencias_globais) + len(pend_gate)


def test_wrapper_discriminante_copolimero_vocabulario_ausente() -> None:
    # Ancorado no ramo (b) não-bloqueante. Asserção é DIFERENCIAL (wrap = base + gate por
    # tipo), não universal-negativa: não depende de nenhum stage do motor médico jamais
    # cunhar "vocabulario_ausente" — só exige que o wrapper ACRESCENTE as do gate além
    # do que executar() sozinho traz.
    pgr_cru = _pgr_cru()
    pgr_resolvido, pend_gate = resolver_composicao(pgr_cru, _INDICE)
    base = executar(pgr_resolvido, _PROTO, _HOJE)
    wrap = executar_com_composicao(pgr_cru, _PROTO, _INDICE, _HOJE)
    n_base = sum(1 for p in base.pendencias_globais if p.tipo == "vocabulario_ausente")
    n_wrap = sum(1 for p in wrap.pendencias_globais if p.tipo == "vocabulario_ausente")
    n_gate = sum(1 for p in pend_gate if p.tipo == "vocabulario_ausente")
    assert n_gate >= 1            # pré-condição: a fixture exercita o ramo (b)
    assert n_wrap == n_base + n_gate


# ---- MOV 3: executar() preserva assinatura (sentinela de regressão, não falha-sem) ----
def test_executar_nao_recebe_indice_cas() -> None:
    params = list(inspect.signature(executar).parameters)
    assert params == ["pgr", "protocolo", "hoje"]
    assert "indice_cas" not in params
