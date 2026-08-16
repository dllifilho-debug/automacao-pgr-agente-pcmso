"""Testes de scripts/medir_cobertura_e_forma.py (003.EY fatia 0). Cada teste
tem reversão nomeada, verificada por varredura inversa antes da entrega."""

from __future__ import annotations

from pathlib import Path

from docx import Document

from agente_medico.motor.tipos import Momento
from scripts.medir_audiometria_dem import parsear_momentos, rotulos_nao_reconhecidos
from scripts.medir_cobertura_e_forma import (
    FORMA_ANOMALA,
    FORMA_GRUPO_SEPARADO,
    FORMA_INLINE,
    FORMA_SEM_NUMERO,
    CoberturaDocumento,
    RegistroCargoCompleto,
    agregar_universalidade,
    classificar_momento_dem,
    extrair_forma_periodicidade,
    extrair_registros_completos,
    gerar_relatorio,
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
    # Desde 003.EZ fatia 0b, parsear_momentos remove o sufixo de
    # periodicidade colado ao rótulo antes do lookup exato — DEM passa a
    # ser reconhecido aqui também (a extração de forma/meses, que já
    # funcionava, é independente e não regride).
    assert Momento.DEM in resultado.momentos


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


def _registro_completo(
    cargo: str,
    momentos: frozenset[Momento],
    rotulos_nao_reconhecidos: frozenset[str] = frozenset(),
    tem_audiometria: bool = True,
) -> RegistroCargoCompleto:
    return RegistroCargoCompleto(
        ghe="GHE-X",
        cargo=cargo,
        tem_audiometria=tem_audiometria,
        momentos_audiometria=momentos,
        rotulos_nao_reconhecidos_audiometria=rotulos_nao_reconhecidos,
        formas=(),
    )


def test_momento_dem_rotulo_nao_reconhecido_cai_em_indeterminado_nao_em_sem_dem() -> None:
    # Reversão que mata: fazer o balde sem_dem ser "tudo que não tem DEM" —
    # o registro ambíguo passaria a entrar em sem_dem além de (ou em vez de)
    # indeterminado, quebrando a recusa em adivinhar (D-ARQ-13 fora do motor).
    ambiguo = _registro_completo(
        "Cargo Ambíguo",
        frozenset({Momento.ADM, Momento.PER, Momento.MR}),
        frozenset({"DEM 12 meses"}),
    )
    com_dem, sem_dem, indeterminado = classificar_momento_dem([ambiguo])
    assert com_dem == []
    assert sem_dem == []
    assert indeterminado == [ambiguo]


def test_momento_dem_presente_vence_ambiguidade_do_resto_da_celula() -> None:
    # Reversão que mata: inverter a precedência, checando rótulos não
    # reconhecidos antes de DEM — mandaria este registro para indeterminado
    # mesmo com DEM presente e legível.
    misto = _registro_completo(
        "Cargo Misto",
        frozenset({Momento.DEM}),
        frozenset({"XPTO"}),
    )
    com_dem, sem_dem, indeterminado = classificar_momento_dem([misto])
    assert com_dem == [misto]
    assert sem_dem == []
    assert indeterminado == []


def test_momento_dem_baldes_particionam_sem_sobra_nem_sobreposicao() -> None:
    # Reversão que mata: permitir que um registro caia em dois baldes (ex.:
    # remover o "not" da condição de sem_dem, deixando-a independente da
    # condição de indeterminado) — a soma dos três baldes passaria a exceder
    # n_com_audiometria.
    registros = [
        _registro_completo("Com DEM", frozenset({Momento.DEM})),
        _registro_completo("Sem DEM limpo", frozenset({Momento.ADM})),
        _registro_completo("Indeterminado", frozenset(), frozenset({"XPTO"})),
        _registro_completo("Com DEM e rótulo ambíguo", frozenset({Momento.DEM}), frozenset({"XPTO"})),
        _registro_completo("Sem audiometria", frozenset(), frozenset(), tem_audiometria=False),
    ]
    com_audio = [r for r in registros if r.tem_audiometria]
    com_dem, sem_dem, indeterminado = classificar_momento_dem(registros)
    todos = com_dem + sem_dem + indeterminado
    assert len(todos) == len(com_audio)
    assert {id(r) for r in todos} == {id(r) for r in com_audio}


def test_agregado_universalidade_com_piso_distinto_do_bruto() -> None:
    # Reversão que mata: fixar o piso em 0 (ou remover o parâmetro) — o
    # documento pequeno passaria a contar como universal também com piso,
    # igualando universais_com_piso a universais_bruto.
    coberturas = {
        "grande.docx": CoberturaDocumento(
            nome_doc="grande.docx", n_cargos=20, n_com_audiometria=20, cargos_sem_audiometria=()
        ),
        "pequeno.docx": CoberturaDocumento(
            nome_doc="pequeno.docx", n_cargos=5, n_com_audiometria=5, cargos_sem_audiometria=()
        ),
    }
    agregado = agregar_universalidade(coberturas, piso=17)
    assert agregado.universais_bruto == 2
    assert agregado.universais_com_piso == 1
    assert agregado.universais_com_piso != agregado.universais_bruto


def test_relatorio_imprime_valor_do_piso_usado(tmp_path: Path) -> None:
    # Reversão que mata: imprimir o agregado sem o piso (remover o trecho
    # "N={piso}" das linhas de agregado bruto/canônico) — o piso usado
    # deixaria de ser rastreável no artefato.
    caminho = tmp_path / "sintetico.docx"
    _construir_docx_sintetico(caminho)
    relatorio = gerar_relatorio([caminho], _MAPA_NOMES, piso=17)
    assert "N=17" in relatorio


def _registro_completo_de_celula(celula: str) -> RegistroCargoCompleto:
    return RegistroCargoCompleto(
        ghe="GHE-X",
        cargo="Cargo",
        tem_audiometria=True,
        momentos_audiometria=parsear_momentos(celula),
        rotulos_nao_reconhecidos_audiometria=rotulos_nao_reconhecidos(celula),
        formas=(),
    )


def test_periodicidade_colada_ao_dem_move_cargo_de_indeterminado_para_com_dem() -> None:
    # Integração fatia 0b (003.EZ): cargo cujo único rótulo ilegível na
    # fatia 0 era "DEM 12 meses" tem que migrar de indeterminado para
    # com_dem depois do fix do parser. Reversão que mata: reverter a
    # Entrega 1 (remoção de sufixo de periodicidade em parsear_momentos /
    # rotulos_nao_reconhecidos) — o registro volta a cair em indeterminado.
    registro = _registro_completo_de_celula("Audiometria (ADM, PER, MRO, DEM 12 meses)")
    com_dem, sem_dem, indeterminado = classificar_momento_dem([registro])
    assert com_dem == [registro]
    assert sem_dem == []
    assert indeterminado == []


def test_periodicidade_colada_ao_mro_sem_dem_vai_para_sem_dem_nao_com_dem() -> None:
    # Reversão que mata: fazer o strip de sufixo resolver qualquer rótulo
    # colado a periodicidade para DEM (em vez do rótulo real que estava
    # colado) — este cargo não tem DEM na célula e tem que cair em sem_dem.
    registro = _registro_completo_de_celula("Audiometria (ADM, PER, MRO 12 meses)")
    com_dem, sem_dem, indeterminado = classificar_momento_dem([registro])
    assert com_dem == []
    assert sem_dem == [registro]
    assert indeterminado == []
