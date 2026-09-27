"""D-ARQ-87 fatia 2 — memorial de raciocínio da matriz em linguagem clínica: resumo
clínico por regra (nunca o fundamento de auditoria), certeza pelo elo mais fraco que
decide a linha, decisões a confirmar agrupadas por regra, o que cada regra pediu quando
há mais de uma, exames não pedidos, e o download na tela. Cada teste nomeia a reversão
que o deixa vermelho."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pytest
from docx import Document
from streamlit.testing.v1 import AppTest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Motivo, Observacao, Resultado
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    ROTULO_CERTEZA,
    montar_memorial,
    nivel_de_certeza,
    renderizar_memorial_docx,
)
from agente_medico.superficie.web_matriz import pagina_matriz

_PROTOCOLO = carregar(Path(__file__).parent.parent / "protocolo")
_EXAMES = _PROTOCOLO.vocabulario.exames
_ADM_PER_MR = frozenset({Momento.ADM, Momento.PER, Momento.MR})
_COM_DEM = _ADM_PER_MR | {Momento.DEM}
_RESUMOS = {r: f"resumo de {r}" for r in ("R-VAL", "R-INT", "R-PSY", "R-ESP-DER", "R-ESP-INT", "R-CLI-01", "R-PKG-ASF")}


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


def test_toda_regra_ativa_tem_resumo_clinico() -> None:
    # Reversão que mata: apagar o `resumo_clinico` de qualquer regra ativa em regras.yaml
    # (o memorial cairia em "Regra sem resumo clínico").
    sem = [r["id"] for r in _PROTOCOLO.regras if not str(r.get("resumo_clinico", "")).strip()]
    assert sem == []


def test_certeza_e_o_elo_mais_fraco_que_decide_a_linha() -> None:
    # Reversões que matam: certeza = pior status entre TODOS os motivos (o primeiro
    # caso vira interpretação); certeza = melhor status entre todos (o segundo vira validado).
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

    assert ROTULO_CERTEZA[nivel_de_certeza(repete)] == "Protocolo validado pela coordenação"
    assert ROTULO_CERTEZA[nivel_de_certeza(unico_dem)] == "Interpretação do sistema — confirmar"


def test_confirmar_primeiro_agrupa_por_regra_e_ignora_regra_redundante() -> None:
    # Reversões que matam: uma entrada por linha em vez de por regra (duas entradas de
    # R-PSY); `regras_fracas` pegar qualquer motivo INTERPRETADO (R-ESP-INT entraria,
    # embora R-ESP-DER já sustente a linha).
    psy = _motivo("R-PSY", "INTERPRETADO", 12, _ADM_PER_MR)
    esp = (_motivo("R-ESP-DER", "DERIVADO", 24, _COM_DEM), _motivo("R-ESP-INT", "INTERPRETADO", 24, _COM_DEM))
    matrizes = [
        MatrizGHE(ghe_id="GHE-01", linhas=[_exame("avaliacao_psicossocial", psy)]),
        MatrizGHE(ghe_id="GHE-16", linhas=[_exame("avaliacao_psicossocial", psy), _exame("espirometria", *esp)]),
    ]

    memorial = montar_memorial(matrizes, _EXAMES, _RESUMOS)

    (decisao,) = memorial.revisar_primeiro
    assert decisao.regra_id == "R-PSY"
    assert decisao.resumo == "resumo de R-PSY"
    assert decisao.onde == ("Avaliação Psicossocial: GHE-01, GHE-16",)
    assert decisao.codigos == ("GHE-01 · Avaliação Psicossocial", "GHE-16 · Avaliação Psicossocial")


def test_porque_usa_o_resumo_e_mostra_o_que_cada_regra_pediu() -> None:
    # Reversões que matam: usar `base_normativa` no lugar do resumo; tirar o "[pede: ...]"
    # por regra; tirar a frase da menor periodicidade quando as regras divergem.
    clinico = _exame(
        "exame_clinico",
        _motivo("R-CLI-01", "VALIDADO", 12, _ADM_PER_MR),
        _motivo("R-PKG-ASF", "DERIVADO", 6, frozenset({Momento.PER})),
    )
    (bloco,) = montar_memorial([MatrizGHE(ghe_id="GHE-22", linhas=[clinico])], _EXAMES, _RESUMOS).blocos
    (linha,) = bloco.linhas

    assert "resumo de R-CLI-01 [pede: ADM, PER 12 meses, MRO] (ref. R-CLI-01)" in linha.porque
    assert "resumo de R-PKG-ASF [pede: PER 6 meses] (ref. R-PKG-ASF)" in linha.porque
    assert "vale a menor periodicidade (6 meses)" in linha.porque
    assert "fundamento de" not in linha.porque


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
    (bloco,) = montar_memorial([matriz], _EXAMES, _RESUMOS).blocos

    (texto,) = bloco.nao_pedidos
    assert texto.startswith("Ácido metil-hipúrico na urina: não pedido — xileno com risco irrelevante")


def test_docx_tem_confirmar_primeiro_e_tabela_por_ghe_sem_fundamento_tecnico(tmp_path: Path) -> None:
    # Reversões que matam: tirar a tabela "confirmar primeiro"; tirar a coluna Correção;
    # voltar a pôr o fundamento de auditoria (`base_normativa`) no documento.
    psy = _motivo("R-PSY", "INTERPRETADO", 12, _ADM_PER_MR)
    matrizes = [MatrizGHE(ghe_id="GHE-01", linhas=[_exame("avaliacao_psicossocial", psy)])]
    destino = tmp_path / "memorial.docx"
    cab = CabecalhoDocumento("E", "O", "Atualização", "27/09/2026", "Dra. X", "CRM")

    renderizar_memorial_docx(montar_memorial(matrizes, _EXAMES, _RESUMOS), cab, destino)

    documento = Document(str(destino))
    confirmar, ghe = documento.tables
    assert confirmar.rows[1].cells[0].text == "resumo de R-PSY (ref. R-PSY)"
    assert ghe.rows[0].cells[-1].text == "Correção"
    assert ghe.rows[1].cells[-1].text == ""
    textos = [p.text for p in documento.paragraphs] + [c.text for t in documento.tables for r in t.rows for c in r.cells]
    assert not any("fundamento de" in t for t in textos)


def test_tela_oferece_o_memorial_com_os_resumos_do_protocolo(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões que matam: remover o `st.download_button` do memorial; passar resumos
    # vazios a `montar_memorial` em pagina_matriz (sai "Regra sem resumo clínico").
    from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario

    arquivos: dict[str, bytes] = {}

    def _download_espiao(rotulo: str, dados: Any, **kwargs: Any) -> bool:
        arquivos[str(kwargs.get("file_name"))] = dados
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)
    exame = _exame("exame_clinico", _motivo("R-CLI-01", "VALIDADO", 12, _ADM_PER_MR))
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Teste",))
    _mockar_parse_deterministico(monkeypatch, Resultado(status="OK", matrizes=[matriz]))

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    documento = Document(io.BytesIO(arquivos["memorial.docx"]))
    celulas = [c.text for t in documento.tables for r in t.rows for c in r.cells]
    resumo = next(str(r["resumo_clinico"]) for r in _PROTOCOLO.regras if r["id"] == "R-CLI-01")
    assert any(resumo in c for c in celulas)
