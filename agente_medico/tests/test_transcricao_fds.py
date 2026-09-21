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


# ---------------------------------------------------------------------------
# parsear_faixa — fallback de separador (DT-(sessão branch
# docs/003fi-achado-gate-forma-faixa)-01). Os 3 casos abaixo são reais, medidos
# via extrair_texto_fds sobre o acervo (Água Sanitária Zulu, Adesivo PVC Tigre,
# Impermeabilizante) — pdfplumber perde o hífen visual da tabela na extração
# por posição. Reversão nomeada: reverter _SEPARADOR_FAIXA_FALLBACK (ou
# esvaziar o fallback em parsear_faixa) derruba exatamente estes 3 testes,
# sem tocar nenhum outro caso desta suíte.
# ---------------------------------------------------------------------------


def test_parsear_faixa_fallback_espaco_puro_hipoclorito() -> None:
    assert parsear_faixa("15 19") == FaixaConcentracao(minimo=15.0, maximo=19.0)


def test_parsear_faixa_fallback_espaco_puro_acetona() -> None:
    assert parsear_faixa("30 70") == FaixaConcentracao(minimo=30.0, maximo=70.0)


def test_parsear_faixa_fallback_literal_a_asfalto() -> None:
    assert parsear_faixa("35 a 50") == FaixaConcentracao(minimo=35.0, maximo=50.0)


def test_parsear_faixa_fallback_nao_compete_com_hifen() -> None:
    # Hífen presente vence o fallback por construção (fallback só roda quando
    # o separador primário não acha 2 partes) — não uma coincidência de valor.
    assert parsear_faixa("0,2 – 0,05") == FaixaConcentracao(minimo=0.2, maximo=0.05)


def test_parsear_faixa_fallback_nao_resgata_lixo_sem_espaco() -> None:
    # "indisponível" não tem espaço nem hífen — fallback não acha 2 partes,
    # continua None. Confirma que o fallback não amplia demais.
    assert parsear_faixa("indisponível") is None
