"""Emenda em D-ARQ-65 (10/10/2026): a tabela GRUPO/PERIGO/FONTE/AGRAVO com AGENTE em
x≈104, ≈113 e ≈122 e categoria em caixa mista; recusas que mandam o bloco para a IA em
vez de perder dado. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.parser_familia_consciente import (
    FamiliaNaoReconhecida,
    PalavraPDF,
    parsear_arquivo,
    parsear_paginas,
)

_TOKENS = {"FISICO", "QUIMICO", "ERGONOMICO", "ACIDENTE", "BIOLOGICO"}


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


def _cabecalho(agente_x: float, quantitativa_x: float | None = None) -> list[PalavraPDF]:
    # Deslocamentos medidos na ALT 65 (AGENTE 122): FONTE +57, AGRAVO +151, S +324, P +349,
    # MEDIDAS +428 em relação ao AGENTE.
    palavras = [
        _p("GHE", 52.0, 10.0),
        _p("01", 76.0, 10.0),
        _p("-", 91.0, 10.0),
        _p("TESTE", 98.0, 10.0),
        _p("PERIGO", agente_x, 20.0),
        _p("GRUPO", 57.0, 25.0),
        _p("FONTE", agente_x + 57, 25.0),
        _p("AGRAVO", agente_x + 151, 25.0),
        _p("S", agente_x + 324, 25.0),
        _p("P", agente_x + 349, 25.0),
        _p("MEDIDAS", agente_x + 428, 25.0),
        _p("ASPECTO", agente_x, 30.0),
    ]
    if quantitativa_x is not None:
        palavras.append(_p("QUANTITATIVA", quantitativa_x, 30.0))
    return palavras


def _risco(
    grupo: str, grupo_x: float, agente: str, agente_x: float, top: float, nivel: bool = True
) -> list[PalavraPDF]:
    palavras = [
        _p(grupo, grupo_x, top),
        _p(agente, agente_x, top),
        _p("Fonte", agente_x + 57, top),
        _p("Agravo", agente_x + 151, top),
    ]
    if nivel:
        palavras += [
            _p("2", agente_x + 324, top),
            _p("1", agente_x + 350, top),
            _p("BAIXO", agente_x + 383, top),
        ]
    return palavras


def test_familia_agente_122_com_categoria_em_caixa_mista_e_coluna_deslocada() -> None:
    # Reversões que matam: _X_AGENTE_MEDIDOS sem 122 (recusa pela posição);
    # _normalizar_coluna_grupo devolvendo as linhas intactas (0 riscos -> recusa).
    pagina = [
        *_cabecalho(122.0),
        *_risco("Ergonômico", 75.0, "Postural", 122.0, 50.0),
        *_risco("Acidentes", 57.0, "Queda", 122.0, 60.0),
        *_risco("Físico", 75.0, "Ruído", 122.0, 70.0),
    ]
    (ghe,) = parsear_paginas([pagina])
    assert [(r.grupo, r.agente) for r in ghe.riscos] == [
        ("ERGONOMICO", "Postural"),
        ("ACIDENTE", "Queda"),
        ("FISICO", "Ruído"),
    ]
    assert all(r.avaliacao_qualitativa == "2 1 BAIXO" for r in ghe.riscos)


def test_familia_agente_104_lida() -> None:
    # Reversão que mata: _X_AGENTE_MEDIDOS sem 104.
    pagina = [*_cabecalho(104.0), *_risco("Químico", 57.0, "Poeira", 104.0, 50.0)]
    (ghe,) = parsear_paginas([pagina])
    assert [(r.grupo, r.agente) for r in ghe.riscos] == [("QUIMICO", "Poeira")]


def test_categoria_fora_da_coluna_grupo_nao_abre_risco() -> None:
    # Quasar GHE 07: continuação da FONTE começa com "químico". Reversão que mata:
    # normalizar a 1ª palavra em qualquer coluna (sem o limite do AGENTE) -> 2 riscos.
    pagina = [
        *_cabecalho(104.0),
        *_risco("Químico", 57.0, "Ácido", 104.0, 50.0),
        _p("químico", 161.0, 60.0),
        _p("VEDACIT", 190.0, 60.0),
    ]
    (ghe,) = parsear_paginas([pagina])
    (risco,) = ghe.riscos
    assert risco.fonte_geradora == "Fonte químico VEDACIT"


def test_agente_fora_das_posicoes_medidas_recusa() -> None:
    # Reversão que mata: tirar a checagem de posição de _parsear_bloco.
    pagina = [*_cabecalho(140.0), *_risco("FISICO", 57.0, "Ruído", 140.0, 50.0)]
    with pytest.raises(FamiliaNaoReconhecida, match="sanity-check"):
        parsear_paginas([pagina])


def test_tabela_sem_linha_de_risco_recusa() -> None:
    # Reversão que mata: tirar o `if not riscos` de _parsear_bloco (GHE vazio aprovado
    # por gate_forma_ghe -> matriz vazia sem aviso).
    pagina = [*_cabecalho(113.0), _p("Página", 28.0, 50.0), _p("2", 40.0, 50.0)]
    with pytest.raises(FamiliaNaoReconhecida, match="nenhuma linha de risco"):
        parsear_paginas([pagina])


def test_linha_com_nivel_e_grupo_desconhecido_recusa() -> None:
    # Vistamerica 2026, GHE PRODUÇÃO 04: "Cimento Portland" escrito na coluna GRUPO.
    # Reversão que mata: tirar o ramo de grupo desconhecido de _motivo_recusa_tabela
    # (a linha seria fundida ao risco anterior).
    pagina = [
        *_cabecalho(122.0),
        *_risco("Físico", 75.0, "Ruído", 122.0, 50.0),
        *_risco("Cimento", 75.0, "Cimento", 122.0, 60.0),
    ]
    with pytest.raises(FamiliaNaoReconhecida, match="'Cimento'"):
        parsear_paginas([pagina])


def test_inventario_psicossocial_depois_da_legenda_nao_recusa() -> None:
    # As linhas "Psicossocial" com nível vêm depois da legenda (inventário do PGR).
    # Reversão que mata: não parar a varredura de _motivo_recusa_tabela na "Legenda".
    pagina = [
        *_cabecalho(113.0),
        *_risco("FISICO", 57.0, "Ruído", 113.0, 50.0),
        _p("Legenda", 59.0, 60.0),
        _p("(P", 97.0, 60.0),
        *_risco("Psicossocial", 57.0, "Demandas", 113.0, 70.0),
    ]
    (ghe,) = parsear_paginas([pagina])
    assert [r.agente for r in ghe.riscos] == ["Ruído"]


def test_valor_medido_na_coluna_quantitativa_recusa() -> None:
    # Quasar Bueno: "(NEN) = 82,28 dB(A)" — a rota grava quantificacao="".
    # Reversão que mata: tirar o ramo do valor quantitativo de _motivo_recusa_tabela.
    pagina = [
        *_cabecalho(104.0, quantitativa_x=637.0),
        *_risco("Físico", 57.0, "Ruido", 104.0, 50.0),
        _p("(NEN)", 637.0, 60.0),
        _p("=", 660.0, 60.0),
        _p("82,28", 670.0, 60.0),
        _p("dB(A).", 700.0, 60.0),
    ]
    with pytest.raises(FamiliaNaoReconhecida, match="quantitativa"):
        parsear_paginas([pagina])


def test_concentracao_fora_da_coluna_quantitativa_nao_recusa() -> None:
    # WV Maldi: "diluído a 0,1%" na coluna AGENTE não é medição. Reversão que mata:
    # procurar o valor na linha inteira, sem o limite x da coluna quantitativa.
    pagina = [
        *_cabecalho(113.0, quantitativa_x=637.0),
        *_risco("QUIMICO", 57.0, "Hipoclorito", 113.0, 50.0),
        _p("diluído", 113.0, 60.0),
        _p("0,1%", 143.0, 60.0),
        _p("Não", 637.0, 60.0),
        _p("aplicável", 652.0, 60.0),
    ]
    (ghe,) = parsear_paginas([pagina])
    assert ghe.riscos[0].agente == "Hipoclorito diluído 0,1%"


_ACERVO = Path("matrizes_originais")
_ALT65 = _ACERVO / "PGR - TOCTAO ALT 65.pdf"
_QUASAR = _ACERVO / "PGR - COOPERATIVA HABITACIONAL QUASAR BUENO.pdf"
_VISTAMERICA_2026 = _ACERVO / "PGR_CMO_CONSTRUTORA_RESIDENCIAL_VISTAMERICA_2026-07-28.pdf"


@pytest.mark.skipif(not _ALT65.exists(), reason="PDF ALT 65 ausente")
def test_alt65_real_18_ghes_141_riscos_61_cargos() -> None:
    # Contagem da coluna GRUPO medida em 09/10/2026; 61 cargos = rota da IA (13/08).
    # Reversões que matam: _X_AGENTE_MEDIDOS só com 113; sem _normalizar_coluna_grupo.
    ghes = parsear_arquivo(_ALT65)
    assert len(ghes) == 18
    assert sum(len(g.riscos) for g in ghes) == 141
    assert sum(len(g.cargos) for g in ghes) == 61
    assert {r.grupo for g in ghes for r in g.riscos} <= _TOKENS
    assert all(r.avaliacao_qualitativa for g in ghes for r in g.riscos)


@pytest.mark.skipif(not _QUASAR.exists(), reason="PDF Quasar ausente")
def test_quasar_real_segue_para_a_ia_pelo_ruido_medido() -> None:
    # Reversão que mata: tirar o ramo do valor quantitativo (os 12 GHEs seriam aceitos
    # e o NEN de 82,28 dB(A) da Carpintaria se perderia).
    with pytest.raises(FamiliaNaoReconhecida, match="quantitativa"):
        parsear_arquivo(_QUASAR)


@pytest.mark.skipif(not _VISTAMERICA_2026.exists(), reason="PDF Vistamerica 2026 ausente")
def test_vistamerica_2026_real_segue_para_a_ia_pelo_cimento_na_coluna_grupo() -> None:
    # Reversão que mata: tirar o ramo de grupo desconhecido de _motivo_recusa_tabela.
    with pytest.raises(FamiliaNaoReconhecida, match="'Cimento'"):
        parsear_arquivo(_VISTAMERICA_2026)
