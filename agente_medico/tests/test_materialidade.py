from agente_medico.motor.tipos import Componente, FaixaConcentracao
from agente_medico.motor.materialidade import materialidade, Materialidade


def _comp(agente="benzeno", concentracao=None, carc=False, sens=False):
    return Componente(
        cas="71-43-2", nome="x", concentracao=concentracao,
        agente=agente, is_carcinogeno_iarc=carc, is_sensibilizante=sens,
    )


def test_ramo0_slug_nao_resolvido_ausente():
    assert materialidade(_comp(agente=None, concentracao=FaixaConcentracao(10.0, 20.0))) is Materialidade.AUSENTE


def test_ramo1_carcinogeno_bypass_material_independe_concentracao():
    assert materialidade(_comp(carc=True, concentracao=FaixaConcentracao(0.1, 0.5))) is Materialidade.MATERIAL


def test_ramo1_bypass_com_concentracao_none_material():
    assert materialidade(_comp(sens=True, concentracao=None)) is Materialidade.MATERIAL


def test_ramo2_sem_bypass_sem_concentracao_ausente():
    assert materialidade(_comp(concentracao=None)) is Materialidade.AUSENTE


def test_ramo3_straddle_cruza_cutoff_ausente():
    assert materialidade(_comp(concentracao=FaixaConcentracao(2.0, 10.0))) is Materialidade.AUSENTE


def test_ramo3_semiaberta_inferior_menor_5_nao_material():
    # "< 5%" = (None, 5.0): teto 5.0, piso 0 -> 0<=5<5 falso -> não straddle -> ramo 5
    assert materialidade(_comp(concentracao=FaixaConcentracao(None, 5.0))) is Materialidade.NAO_MATERIAL


def test_ramo3_semiaberta_superior_maior_1_straddle():
    # "> 1%" = (1.0, None): teto +inf, piso 1 -> 1<=5<inf -> straddle -> AUSENTE
    assert materialidade(_comp(concentracao=FaixaConcentracao(1.0, None))) is Materialidade.AUSENTE


def test_ramo4_faixa_acima_cutoff_material():
    assert materialidade(_comp(concentracao=FaixaConcentracao(6.0, 10.0))) is Materialidade.MATERIAL


def test_ramo5_faixa_abaixo_cutoff_nao_material():
    assert materialidade(_comp(concentracao=FaixaConcentracao(1.0, 4.0))) is Materialidade.NAO_MATERIAL


def test_borda_5_0_exata_nao_material():
    # ponto 5,0: piso=teto=5 -> straddle 5<=5<5 falso; piso>5 falso; max<=5 verdadeiro -> NÃO-MATERIAL
    assert materialidade(_comp(concentracao=FaixaConcentracao(5.0, 5.0))) is Materialidade.NAO_MATERIAL


def test_borda_piso_5_faixa_5_10_straddle():
    # "5-10%" = (5.0, 10.0): 5<=5<10 -> straddle -> AUSENTE (RT resolve na admissão)
    assert materialidade(_comp(concentracao=FaixaConcentracao(5.0, 10.0))) is Materialidade.AUSENTE
