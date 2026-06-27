import dataclasses

from agente_medico.motor.composicao import _normalizar_faixa
from agente_medico.motor.tipos import Componente, FaixaConcentracao


def _comp(faixa):
    return Componente(cas="71-43-2", nome="x", concentracao=faixa)


def test_p2a_par_invertido_normaliza():
    out = _normalizar_faixa(_comp(FaixaConcentracao(0.2, 0.05)))
    assert out.concentracao == FaixaConcentracao(0.05, 0.2)


def test_p2b_piso_textual_zero_nao_inverte():
    out = _normalizar_faixa(_comp(FaixaConcentracao(0.0, 10.0)))
    assert out.concentracao == FaixaConcentracao(0.0, 10.0)


def test_faixa_ja_ordenada_intocada():
    out = _normalizar_faixa(_comp(FaixaConcentracao(1.0, 5.0)))
    assert out.concentracao == FaixaConcentracao(1.0, 5.0)


def test_semiaberta_inferior_none_nao_quebra():
    # min(None, 5.0) seria TypeError — guarda obrigatória
    out = _normalizar_faixa(_comp(FaixaConcentracao(None, 5.0)))
    assert out.concentracao == FaixaConcentracao(None, 5.0)


def test_semiaberta_superior_none_nao_quebra():
    out = _normalizar_faixa(_comp(FaixaConcentracao(1.0, None)))
    assert out.concentracao == FaixaConcentracao(1.0, None)


def test_concentracao_ausente_intocada():
    out = _normalizar_faixa(_comp(None))
    assert out.concentracao is None


def test_ponto_intocado():
    out = _normalizar_faixa(_comp(FaixaConcentracao(2.0, 2.0)))
    assert out.concentracao == FaixaConcentracao(2.0, 2.0)


def test_idempotente():
    uma = _normalizar_faixa(_comp(FaixaConcentracao(0.2, 0.05)))
    duas = _normalizar_faixa(uma)
    assert duas.concentracao == FaixaConcentracao(0.05, 0.2)
