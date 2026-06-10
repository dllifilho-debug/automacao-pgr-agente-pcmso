from agente_medico.motor.tipos import Componente, FaixaConcentracao


def test_faixa_fechada_preserva_limites() -> None:
    faixa = FaixaConcentracao(1.0, 5.0)
    assert faixa.piso_efetivo() == 1.0
    assert faixa.teto_efetivo() == 5.0


def test_faixa_semiaberta_inferior() -> None:
    # "< 5%" da FDS -> (None, 5.0)
    faixa = FaixaConcentracao(None, 5.0)
    assert faixa.piso_efetivo() == 0.0
    assert faixa.teto_efetivo() == 5.0


def test_faixa_semiaberta_superior() -> None:
    # "> 1%" da FDS -> (1.0, None)
    faixa = FaixaConcentracao(1.0, None)
    assert faixa.piso_efetivo() == 1.0
    assert faixa.teto_efetivo() == float("inf")


def test_faixa_ponto() -> None:
    # "2%" exato da FDS -> (2.0, 2.0)
    faixa = FaixaConcentracao(2.0, 2.0)
    assert faixa.piso_efetivo() == 2.0
    assert faixa.teto_efetivo() == 2.0


def test_componente_concentracao_default_none() -> None:
    # migração introduz default None; antes da fatia, faltaria argumento (TypeError)
    comp = Componente(cas="64-17-5", nome="etanol")
    assert comp.concentracao is None


def test_componente_aceita_faixa() -> None:
    comp = Componente(cas="71-43-2", nome="benzeno",
                      concentracao=FaixaConcentracao(None, 5.0))
    assert comp.concentracao is not None
    assert comp.concentracao.teto_efetivo() == 5.0
