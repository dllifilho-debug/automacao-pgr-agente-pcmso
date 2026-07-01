from __future__ import annotations

from agente_medico.motor.tipos import FaixaConcentracao
from agente_medico.motor.transcricao_fds import (
    desambiguar_cas,
    normalizar_cas_ausente,
    parsear_faixa,
)


# ---------------------------------------------------------------------------
# desambiguar_cas (P3 — DT-003AS-01 patologia 3)
# ---------------------------------------------------------------------------

def test_desambiguar_cas_junta_quebra_intra_token_tio2() -> None:
    # Âncora: TiO₂ da FISPQ da tinta. CAS já errado no documento (falha o
    # dígito verificador, ramo (c) do gate a jusante) — ainda assim a quebra
    # é intra-token, não separador, então junta.
    assert desambiguar_cas("134363-67-\n7") == "134363-67-7"


def test_desambiguar_cas_preserva_multi_cas_legitimo() -> None:
    # Âncora: bloco "Derivados de:" com dois CAS válidos empilhados —
    # preserva o '\n' para o resolvedor explodir (_explodir_bloco).
    assert desambiguar_cas("2634-33-5\n55965-84-9") == "2634-33-5\n55965-84-9"


def test_desambiguar_cas_no_op_em_cas_ja_limpo() -> None:
    assert desambiguar_cas("71-43-2") == "71-43-2"


def test_desambiguar_cas_whitespace_de_fronteira_junta() -> None:
    assert desambiguar_cas("134363-67- \n 7") == "134363-67-7"


def test_desambiguar_cas_whitespace_de_fronteira_preserva_multi_cas() -> None:
    # Preserva intocado: ambos fragmentos bem-formados isoladamente, mesmo
    # com espaço de fronteira ao redor do '\n'.
    assert desambiguar_cas("2634-33-5 \n 55965-84-9") == "2634-33-5 \n 55965-84-9"


# ---------------------------------------------------------------------------
# normalizar_cas_ausente (P4 — DT-003AS-01 patologia 4)
# ---------------------------------------------------------------------------

def test_normalizar_cas_ausente_varios() -> None:
    assert normalizar_cas_ausente("vários") == ""


def test_normalizar_cas_ausente_nd() -> None:
    assert normalizar_cas_ausente("ND") == ""


def test_normalizar_cas_ausente_na() -> None:
    assert normalizar_cas_ausente("NA") == ""


def test_normalizar_cas_ausente_um_asterisco() -> None:
    assert normalizar_cas_ausente("*") == ""


def test_normalizar_cas_ausente_dois_asteriscos() -> None:
    assert normalizar_cas_ausente("**") == ""


def test_normalizar_cas_ausente_quatro_asteriscos() -> None:
    assert normalizar_cas_ausente("****") == ""


def test_normalizar_cas_ausente_segredo_industrial() -> None:
    assert normalizar_cas_ausente("Segredo Industrial") == ""


def test_normalizar_cas_ausente_informacao_confidencial() -> None:
    assert normalizar_cas_ausente("Informação confidencial") == ""


def test_normalizar_cas_ausente_preserva_cas_real() -> None:
    assert normalizar_cas_ausente("71-43-2") == "71-43-2"


# ---------------------------------------------------------------------------
# parsear_faixa (P5 — D-ARQ-43 P2 / D-ARQ-34 P1)
# ---------------------------------------------------------------------------

def test_parsear_faixa_ancora_par_invertido() -> None:
    assert parsear_faixa("0,2 – 0,05") == FaixaConcentracao(minimo=0.2, maximo=0.05)


def test_parsear_faixa_ancora_piso_textual() -> None:
    assert parsear_faixa("00 – 10") == FaixaConcentracao(minimo=0.0, maximo=10.0)


def test_parsear_faixa_ancora_piso_textual_decimal() -> None:
    assert parsear_faixa("00 – 0,5") == FaixaConcentracao(minimo=0.0, maximo=0.5)


def test_parsear_faixa_ancora_par_invertido_decimal() -> None:
    assert parsear_faixa("0,01 – 0,008") == FaixaConcentracao(minimo=0.01, maximo=0.008)


def test_parsear_faixa_separador_hifen_comum() -> None:
    assert parsear_faixa("1 - 15") == FaixaConcentracao(minimo=1.0, maximo=15.0)


def test_parsear_faixa_separador_en_dash() -> None:
    assert parsear_faixa("1 – 15") == FaixaConcentracao(minimo=1.0, maximo=15.0)


def test_parsear_faixa_semi_aberta_inferior() -> None:
    assert parsear_faixa("< 5") == FaixaConcentracao(minimo=None, maximo=5.0)


def test_parsear_faixa_semi_aberta_superior() -> None:
    assert parsear_faixa("> 1") == FaixaConcentracao(minimo=1.0, maximo=None)


def test_parsear_faixa_vazio_retorna_none() -> None:
    assert parsear_faixa("") is None


def test_parsear_faixa_so_espaco_retorna_none() -> None:
    assert parsear_faixa("   ") is None


def test_parsear_faixa_ininteligivel_retorna_none() -> None:
    assert parsear_faixa("indisponível") is None


def test_parsear_faixa_nao_ordena_par_invertido() -> None:
    # Confirma explicitamente que NÃO ordena: par invertido sai invertido
    # (a ordenação é responsabilidade de _normalizar_faixa no resolvedor).
    faixa = parsear_faixa("0,2 – 0,05")
    assert faixa is not None
    assert faixa.minimo is not None and faixa.maximo is not None
    assert faixa.minimo > faixa.maximo
