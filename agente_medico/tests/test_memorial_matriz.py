"""D-ARQ-87 fatia 2 — memorial de raciocínio da matriz: grau de certeza pelo elo
mais fraco que decide a linha, decisões interpretadas agrupadas por regra, regra
que define a periodicidade, exames não pedidos, documento com coluna de correção
e apêndice, e o download na tela. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Motivo, Observacao, Resultado
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    grau_de_certeza,
    montar_memorial,
    renderizar_memorial_docx,
)
from agente_medico.superficie.web_matriz import pagina_matriz

_EXAMES = carregar(Path(__file__).parent.parent / "protocolo").vocabulario.exames
_ADM_PER_MR = frozenset({Momento.ADM, Momento.PER, Momento.MR})
_COM_DEM = _ADM_PER_MR | {Momento.DEM}


def _motivo(regra: str, status: str, meses: int, momentos: frozenset[Momento]) -> Motivo:
    return Motivo(
        regra_id=regra,
        predicado="p",
        risco_origem=None,
        detalhe=None,
        status_regra=status,
        periodicidade_meses=meses,
        momentos=momentos,
        base_normativa=f"fundamento de {regra}",
    )


def _exame(slug: str, *motivos: Motivo) -> ExameEmitido:
    momentos: set[Momento] = set()
    for m in motivos:
        momentos |= m.momentos
    return ExameEmitido(
        exame=slug,
        periodicidade_meses=min(m.periodicidade_meses or 0 for m in motivos),
        momentos=momentos,
        motivos=list(motivos),
    )


def test_certeza_e_o_elo_mais_fraco_que_decide_a_linha() -> None:
    # Reversões que matam: certeza = pior status entre TODOS os motivos (o
    # primeiro caso vira INTERPRETADO); certeza = melhor status entre todos (o
    # segundo vira VALIDADO).
    repete = _exame(
        "espirometria",
        _motivo("R-VAL", "VALIDADO", 24, _COM_DEM),
        _motivo("R-INT", "INTERPRETADO", 24, _COM_DEM),
    )
    unico_dem = _exame(
        "acuidade_visual",
        _motivo("R-VAL", "VALIDADO", 12, _ADM_PER_MR),
        _motivo("R-INT", "INTERPRETADO", 12, _COM_DEM),
    )

    assert grau_de_certeza(repete) == "VALIDADO"
    assert grau_de_certeza(unico_dem) == "INTERPRETADO"


def test_revisar_primeiro_agrupa_por_regra_e_ignora_regra_redundante() -> None:
    # Reversões que matam: uma entrada por linha em vez de por regra (duas
    # entradas de R-PSY); `regras_fracas` pegar qualquer motivo INTERPRETADO
    # (R-ESP-INT entraria, embora R-ESP-DER já sustente a linha).
    psy = _motivo("R-PSY", "INTERPRETADO", 12, _ADM_PER_MR)
    esp = (_motivo("R-ESP-DER", "DERIVADO", 24, _COM_DEM), _motivo("R-ESP-INT", "INTERPRETADO", 24, _COM_DEM))
    matrizes = [
        MatrizGHE(ghe_id="GHE-01", linhas=[_exame("avaliacao_psicossocial", psy)]),
        MatrizGHE(ghe_id="GHE-16", linhas=[_exame("avaliacao_psicossocial", psy), _exame("espirometria", *esp)]),
    ]

    memorial = montar_memorial(matrizes, _EXAMES)

    assert [d.regra_id for d in memorial.revisar_primeiro] == ["R-PSY"]
    (decisao,) = memorial.revisar_primeiro
    assert decisao.codigos == ("GHE-01/avaliacao_psicossocial", "GHE-16/avaliacao_psicossocial")
    assert decisao.onde == ("Avaliação Psicossocial: GHE-01, GHE-16",)


def test_linha_marca_so_a_regra_que_define_a_periodicidade() -> None:
    # Reversões que matam: tirar o marcador; marcar toda regra da linha; o código
    # da linha usar o nome de exibição em vez do slug.
    clinico = _exame(
        "exame_clinico",
        _motivo("R-CLI-01", "VALIDADO", 12, _ADM_PER_MR),
        _motivo("R-PKG-ASF", "DERIVADO", 6, frozenset({Momento.PER})),
    )
    (bloco,) = montar_memorial([MatrizGHE(ghe_id="GHE-22", linhas=[clinico])], _EXAMES).blocos
    (linha,) = bloco.linhas

    assert linha.codigo == "GHE-22/exame_clinico"
    regras = dict(r.split(":", 1) for r in linha.regras.split("\n"))
    assert "define a periodicidade" in regras["R-PKG-ASF"]
    assert "define a periodicidade" not in regras["R-CLI-01"]


def test_memorial_lista_os_exames_nao_pedidos() -> None:
    # Reversão que mata: não levar `matriz.observacoes` para `nao_pedidos`.
    obs = Observacao(
        regra_id="R-BIO-04-xileno",
        regra_dispensa="R-BIO-05",
        agente="xileno",
        nivel_risco="IRRELEVANTE",
        exames_dispensados=("acido_metilhipurico",),
    )
    matriz = MatrizGHE(
        ghe_id="GHE-18",
        linhas=[_exame("exame_clinico", _motivo("R-CLI-01", "VALIDADO", 12, _ADM_PER_MR))],
        observacoes=(obs,),
    )
    (bloco,) = montar_memorial([matriz], _EXAMES).blocos

    assert len(bloco.nao_pedidos) == 1
    assert "R-BIO-05" in bloco.nao_pedidos[0] and "xileno" in bloco.nao_pedidos[0]


def test_docx_tem_revisao_uma_tabela_por_ghe_e_apendice_com_correcao_em_branco(tmp_path: Path) -> None:
    # Reversões que matam: tirar a tabela de "revisar primeiro"; tirar o apêndice;
    # tirar a coluna Correção da tabela do GHE.
    psy = _motivo("R-PSY", "INTERPRETADO", 12, _ADM_PER_MR)
    matrizes = [MatrizGHE(ghe_id="GHE-01", linhas=[_exame("avaliacao_psicossocial", psy)])]
    destino = tmp_path / "memorial.docx"
    cab = CabecalhoDocumento("E", "O", "Atualização", "27/09/2026", "Dra. X", "CRM")

    renderizar_memorial_docx(montar_memorial(matrizes, _EXAMES), cab, destino)

    revisar, ghe, apendice = Document(str(destino)).tables
    assert revisar.rows[1].cells[0].text.startswith("R-PSY")
    assert ghe.rows[0].cells[-1].text == "Correção"
    assert ghe.rows[1].cells[-1].text == ""
    assert apendice.rows[1].cells[2].text == "fundamento de R-PSY"


def test_tela_oferece_o_memorial_para_download(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: remover o `st.download_button` do memorial em pagina_matriz.
    from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario

    arquivos: list[str] = []

    def _download_espiao(*args: Any, **kwargs: Any) -> bool:
        arquivos.append(str(kwargs.get("file_name")))
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)
    exame = _exame("exame_clinico", _motivo("R-CLI-01", "VALIDADO", 12, _ADM_PER_MR))
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Teste",))
    _mockar_parse_deterministico(monkeypatch, Resultado(status="OK", matrizes=[matriz]))

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    assert "memorial.docx" in arquivos
