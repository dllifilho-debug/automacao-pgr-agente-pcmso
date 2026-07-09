from __future__ import annotations

from agente_medico.motor.quantificacao import parsear_quantificacao


def test_parsear_quantificacao_db_a() -> None:
    q = parsear_quantificacao("82,2 dB(A)")
    assert q is not None
    assert q.valor == 82.2
    assert q.unidade == "dB(A)"
    assert q.relacao_LT is None
    assert q.pct_LT is None
    assert q.apenas_qualitativa is False


def test_parsear_quantificacao_mg_m3_unicode() -> None:
    q = parsear_quantificacao("0,163 mg/m³")
    assert q is not None
    assert q.valor == 0.163
    assert q.unidade == "mg/m3"


def test_parsear_quantificacao_mg_m3_ascii() -> None:
    q = parsear_quantificacao("0,163 mg/m3")
    assert q is not None
    assert q.valor == 0.163
    assert q.unidade == "mg/m3"


def test_parsear_quantificacao_ppm() -> None:
    q = parsear_quantificacao("6,3 ppm")
    assert q is not None
    assert q.valor == 6.3
    assert q.unidade == "ppm"


def test_parsear_quantificacao_inteiro_ppm() -> None:
    q = parsear_quantificacao("1 ppm")
    assert q is not None
    assert q.valor == 1.0
    assert q.unidade == "ppm"


def test_parsear_quantificacao_vazio() -> None:
    assert parsear_quantificacao("") is None


def test_parsear_quantificacao_whitespace() -> None:
    assert parsear_quantificacao("   ") is None


def test_parsear_quantificacao_sem_unidade() -> None:
    assert parsear_quantificacao("82,2") is None


def test_parsear_quantificacao_unidade_fora_do_conjunto() -> None:
    assert parsear_quantificacao("82,2 dB") is None


def test_parsear_quantificacao_numero_ilegivel() -> None:
    assert parsear_quantificacao("abc ppm") is None
