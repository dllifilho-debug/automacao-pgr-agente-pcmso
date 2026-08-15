"""Testes de scripts/medir_cobertura_e_forma.py (003.EY fatia 0). Cada teste
tem reversão nomeada, verificada por varredura inversa antes da entrega."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from agente_medico.motor.tipos import Momento
from scripts.medir_cobertura_e_forma import (
    FORMA_ANOMALA,
    FORMA_GRUPO_SEPARADO,
    FORMA_INLINE,
    FORMA_SEM_NUMERO,
    extrair_forma_periodicidade,
    extrair_registros_completos,
    medir_cobertura,
)

_MAPA_NOMES = {"espirometria": "espirometria", "audiometria": "audiometria"}


def test_periodicidade_inline_no_grupo_de_momentos() -> None:
    # Reversão que mata: fazer o extrator devolver None de meses quando o
    # número está dentro do grupo de momentos (em vez de buscar o padrão
    # numérico em todo o grupo, restringir a busca a um grupo dedicado).
    resultado = extrair_forma_periodicidade(
        "Espirometria (ADM, PER 24 meses, MRO, DEM)", _MAPA_NOMES
    )
    assert resultado.exame == "espirometria"
    assert resultado.meses == 24
    assert resultado.forma == FORMA_INLINE


def test_periodicidade_em_grupo_separado_preserva_momentos() -> None:
    # Reversão que mata: tratar o 1º grupo ("12 meses") como grupo de
    # momentos em vez do 2º — perde os 4 momentos e/ou o número.
    resultado = extrair_forma_periodicidade(
        "Audiometria (12 meses), (ADM, PER, MRO, DEM)", _MAPA_NOMES
    )
    assert resultado.meses == 12
    assert resultado.forma == FORMA_GRUPO_SEPARADO
    assert resultado.momentos == frozenset(
        {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}
    )


def test_sem_numero_nao_inventa_periodicidade() -> None:
    # Reversão que mata: devolver 12 como default quando não há número
    # impresso na célula (a ausência de número não é o valor 12 — é
    # ausência, ponto que a Pergunta B existe para não presumir).
    resultado = extrair_forma_periodicidade("Audiometria (ADM, PER, MRO, DEM)", _MAPA_NOMES)
    assert resultado.meses is None
    assert resultado.forma == FORMA_SEM_NUMERO


def test_tres_grupos_e_forma_anomala_nao_truncada() -> None:
    # Reversão que mata: restaurar o limite de 2 grupos de DH-003EX-01 sem o
    # reporte — capturaria só os 2 primeiros grupos em silêncio (meses=12,
    # forma=grupo_separado), engolindo o 3º.
    resultado = extrair_forma_periodicidade("X (12 meses), (faixa), (ADM, PER)", _MAPA_NOMES)
    assert resultado.forma == FORMA_ANOMALA
    assert resultado.meses is None


def test_numero_no_rotulo_do_momento_nao_vira_sem_numero() -> None:
    # Gabarito 003.EX (docs/referencia/GABARITO_003EX_audiometria_dem.md,
    # "Forma real das células" #2): "Audiometria (ADM, PER, MRO, DEM 12
    # meses)" — periodicidade embutida no rótulo do momento, não num grupo
    # próprio. Reversão que mata: casar o rótulo por prefixo conhecido
    # (ADM/PER/MRO/RET/DEM) e descartar o restante do token — engoliria o
    # "12 meses" e devolveria sem_numero com momento DEM limpo, em vez de
    # inline com meses=12.
    resultado = extrair_forma_periodicidade(
        "Audiometria (ADM, PER, MRO, DEM 12 meses)", _MAPA_NOMES
    )
    assert resultado.exame == "audiometria"
    assert resultado.meses == 12
    assert resultado.forma == FORMA_INLINE
    # DEM com periodicidade colada não bate rótulo exato — fica fora de
    # `momentos`, mesma classe de desvio de DT-003EW-02 (documentado, não
    # escondido pelo instrumento).
    assert Momento.DEM not in resultado.momentos


def _construir_docx_sintetico(caminho: Path) -> None:
    documento = Document()
    tabela = documento.add_table(rows=0, cols=2)
    linha_ghe = tabela.add_row().cells
    linha_ghe[0].text = "GHE 01 TESTE"
    linha_ghe[1].text = "GHE 01 TESTE"
    linha_cabecalho = tabela.add_row().cells
    linha_cabecalho[0].text = "FUNÇÃO"
    linha_cabecalho[1].text = "EXAMES SOLICITADOS"
    cargos = [
        ("Cargo A", "Audiometria (ADM, PER, MRO, DEM)"),
        ("Cargo B", "Audiometria (ADM, PER, MRO, DEM)"),
        ("Cargo C", "Audiometria (ADM, PER, MRO, DEM)"),
        ("Cargo D", "Exame Clinico (ADM, PER, MRO, DEM)"),
    ]
    for nome_cargo, exames in cargos:
        linha = tabela.add_row().cells
        linha[0].text = nome_cargo
        linha[1].text = exames
    documento.save(str(caminho))


def test_n_cargos_conta_linhas_de_cargo_nao_celulas_da_coluna_funcao(tmp_path: Path) -> None:
    # Reversão que mata: contar n_cargos como número de células da coluna
    # FUNÇÃO em vez de linhas de cargo filtradas (_linha_e_cargo) — incluiria
    # a linha de GHE e a linha de cabeçalho FUNÇÃO/EXAMES SOLICITADOS,
    # 6 em vez de 4, e a fração cairia para 3/6=0.5 em vez de 3/4=0.75
    # (armadilha nomeada na EMENDA 1 de 003.EX).
    caminho = tmp_path / "sintetico.docx"
    _construir_docx_sintetico(caminho)
    registros, _ = extrair_registros_completos(caminho, _MAPA_NOMES)
    cobertura = medir_cobertura(caminho.name, registros)
    assert cobertura.n_cargos == 4
    assert cobertura.n_com_audiometria == 3
    assert cobertura.fracao == 0.75
    assert cobertura.universal is False
