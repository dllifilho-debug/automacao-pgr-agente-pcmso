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


def test_gate_ramo_a_popula_carcinogeno_true() -> None:
    comp, pend = gate_cas(_comp("71-43-2", "benzeno"), _INDICE)
    assert comp.agente == "benzeno"
    assert comp.is_carcinogeno_iarc is True
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
