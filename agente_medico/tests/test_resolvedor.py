from __future__ import annotations

import pytest

from agente_medico.motor.resolvedor import (
    EntradaIndice,
    cas_bem_formado,
    construir_indice_cas,
    gate_cas,
)
from agente_medico.motor.tipos import Componente


# ---------------------------------------------------------------------------
# cas_bem_formado
# ---------------------------------------------------------------------------

def test_cas_bem_formado_benzeno() -> None:
    assert cas_bem_formado("71-43-2") is True


def test_cas_bem_formado_agua() -> None:
    assert cas_bem_formado("7732-18-5") is True


def test_cas_bem_formado_metanol() -> None:
    assert cas_bem_formado("67-56-1") is True


def test_cas_fantasma_022_falha() -> None:
    assert cas_bem_formado("022-00-9") is False


def test_cas_fantasma_014_falha() -> None:
    assert cas_bem_formado("014-00-0") is False


def test_cas_curto_demais_falha() -> None:
    # Menos de 5 dígitos -> impossível ter corpo + verificador válidos.
    assert cas_bem_formado("123") is False


# ---------------------------------------------------------------------------
# construir_indice_cas
# ---------------------------------------------------------------------------

def test_indice_pula_agente_sem_cas() -> None:
    vocab = {
        "ruido": {"tipo_ibe": "EE"},
        "benzeno": {"cas": "71-43-2", "tipo_ibe": "SC", "is_carcinogeno_iarc": True},
    }
    indice = construir_indice_cas(vocab)
    assert indice == {"71432": EntradaIndice(slug="benzeno", is_carcinogeno_iarc=True)}


def test_indice_normaliza_hifens() -> None:
    vocab = {"agua": {"cas": "7732-18-5", "is_carcinogeno_iarc": False}}
    indice = construir_indice_cas(vocab)
    assert indice.get("7732185") == EntradaIndice(slug="agua", is_carcinogeno_iarc=False)


def test_indice_colisao_levanta_value_error() -> None:
    vocab = {
        "slug_a": {"cas": "71-43-2"},
        "slug_b": {"cas": "71-43-2"},
    }
    with pytest.raises(ValueError, match="Colisão"):
        construir_indice_cas(vocab)


# ---------------------------------------------------------------------------
# gate_cas
# ---------------------------------------------------------------------------

_INDICE: dict[str, EntradaIndice] = {
    "71432": EntradaIndice("benzeno", True),
    "7732185": EntradaIndice("agua", False),
}


def _comp(cas: str, nome: str = "teste") -> Componente:
    return Componente(cas=cas, nome=nome)


def test_gate_ramo_a_slug_resolvido() -> None:
    comp, pend = gate_cas(_comp("71-43-2", "benzeno"), _INDICE)
    assert comp.agente == "benzeno"
    assert pend is None


def test_gate_ramo_a_nao_sobrescreve_flag_cru_false() -> None:
    # Reversão 003.V: gate NÃO propaga is_carcinogeno_iarc do índice.
    # Componente tem flag=False (default); índice benzeno=True; flag deve continuar False.
    comp, pend = gate_cas(_comp("71-43-2", "benzeno"), _INDICE)
    assert comp.agente == "benzeno"
    assert comp.is_carcinogeno_iarc is False
    assert pend is None


def test_gate_ramo_a_nao_carcinogeno_fica_false() -> None:
    comp, pend = gate_cas(_comp("7732-18-5", "agua"), _INDICE)
    assert comp.agente == "agua"
    assert comp.is_carcinogeno_iarc is False
    assert pend is None


def test_gate_ramo_b_vocabulario_ausente() -> None:
    # 7664-41-7 = amônia: CAS válido no dígito, ausente do índice de teste.
    comp, pend = gate_cas(_comp("7664-41-7", "amonia"), _INDICE)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "vocabulario_ausente"
    assert pend.bloqueante is False
    assert pend.destinatario == "protocolo"


def test_gate_ramo_c_cas_invalido() -> None:
    comp, pend = gate_cas(_comp("022-00-9", "fantasma"), _INDICE)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "cas_invalido"
    assert pend.bloqueante is True
    assert pend.destinatario == "empresa"


def test_gate_ramo_d_cas_ausente() -> None:
    comp, pend = gate_cas(_comp("", "segredo industrial"), _INDICE)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "cas_ausente"
    assert pend.bloqueante is False
    assert pend.destinatario == "empresa"


# ---------------------------------------------------------------------------
# MUDANÇA 5a: reversão fonte-de-flag (D-ARQ-36 nota 003.V)
# ---------------------------------------------------------------------------

def test_gate_reversao_nao_sobrescreve_flag() -> None:
    # gate_cas NÃO propaga is_carcinogeno_iarc do índice para o Componente.
    # FALHA sob 003.T (sobrescrevia via entrada.is_carcinogeno_iarc),
    # PASSA pós-reversão (D-ARQ-36 nota 003.V).
    # Índice tem dioxido_de_titanio=True; componente tem is_carcinogeno_iarc=False → deve ficar False.
    _idx_reversao = {"13463677": EntradaIndice("dioxido_de_titanio", True)}
    comp_cru = Componente(cas="13463-67-7", nome="TiO2", is_carcinogeno_iarc=False)
    comp, pend = gate_cas(comp_cru, _idx_reversao)
    assert comp.agente == "dioxido_de_titanio"
    assert comp.is_carcinogeno_iarc is False   # gate NÃO sobrescreveu, apesar do índice True
    assert pend is None


# ---------------------------------------------------------------------------
# MUDANÇA 5b: ramos sobre CAS reais (índice de teste à mão; padrão _INDICE existente)
# ---------------------------------------------------------------------------

_INDICE_T65: dict[str, EntradaIndice] = {
    "78933": EntradaIndice("metil_etil_cetona", False),  # MEK 78-93-3
    "67641": EntradaIndice("acetona", False),            # acetona 67-64-1
}


def test_gate_ramo_a_mek() -> None:
    # MEK CAS "78-93-3" → válido + slug → ramo(a)
    comp, pend = gate_cas(_comp("78-93-3", "MEK"), _INDICE_T65)
    assert comp.agente == "metil_etil_cetona"
    assert pend is None


def test_gate_ramo_a_acetona() -> None:
    # acetona CAS "67-64-1" → válido + slug → ramo(a)
    comp, pend = gate_cas(_comp("67-64-1", "acetona"), _INDICE_T65)
    assert comp.agente == "acetona"
    assert pend is None


def test_gate_ramo_c_tio2_cas_errado() -> None:
    # TiO2 CAS da FISPQ "134363-67-7" falha o dígito verificador → ramo(c)
    comp, pend = gate_cas(_comp("134363-67-7", "TiO2 fispq"), _INDICE_T65)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "cas_invalido"
    assert pend.bloqueante is True


def test_gate_ramo_b_copolimero_pvc() -> None:
    # CAS "9003-22-9" (copolímero PVC): válido no dígito, sem slug no índice → ramo(b)
    comp, pend = gate_cas(_comp("9003-22-9", "Copolimero PVC"), _INDICE_T65)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "vocabulario_ausente"
    assert pend.bloqueante is False


def test_gate_ramo_c_aluminato_cas_invalido() -> None:
    # CAS "1242-78-3" (aluminato tricálcico da fixture cimento): falha o dígito → ramo(c).
    # [CONFERIR confirmado]: cas_bem_formado("1242-78-3") is False.
    comp, pend = gate_cas(_comp("1242-78-3", "aluminato"), _INDICE_T65)
    assert comp.agente is None
    assert pend is not None
    assert pend.tipo == "cas_invalido"
    assert pend.bloqueante is True


# ---------------------------------------------------------------------------
# MUDANÇA 5c: cadeia resolver_composicao — recorte mínimo (NÃO executar, NÃO Fase C)
# ---------------------------------------------------------------------------

def test_resolver_composicao_hidrata_mek() -> None:
    from datetime import date

    from agente_medico.motor.composicao import resolver_composicao
    from agente_medico.motor.tipos import FDS, GHEPGR, PGR, ProdutoQuimico
    from agente_medico.tests.fixtures import bloco_de

    pgr_cru = PGR(
        validade=date(2025, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="ghe_test",
                nome="GHE teste",
                cargos=(),
                riscos=(),
                epis=(),
                produtos_quimicos=(
                    ProdutoQuimico(
                        nome="Adesivo MEK",
                        fds=FDS(
                            composicao=(),
                            composicao_verbatim=(bloco_de(Componente(cas="78-93-3", nome="MEK")),),
                        ),
                    ),
                ),
                psicossocial=False,
            ),
        ),
    )
    idx = {"78933": EntradaIndice("metil_etil_cetona", False)}
    pgr_resolvido, _ = resolver_composicao(pgr_cru, idx)
    assert pgr_resolvido.ghes[0].produtos_quimicos[0].fds.composicao[0].agente == "metil_etil_cetona"
