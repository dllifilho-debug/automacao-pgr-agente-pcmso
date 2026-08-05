"""Testes do núcleo puro de web_matriz.py (003.EQ S3 fatia 1) — cada teste
carrega, junto, a reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

import ast
from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento
from agente_medico.superficie.documento_matriz import CabecalhoDocumento, LinhaCargo, RodapeDocumento
from agente_medico.superficie.web_matriz import gerar_documento, montar_envelope


def _cabecalho() -> CabecalhoDocumento:
    return CabecalhoDocumento(
        empresa="Empresa Teste",
        obra="Obra Teste",
        tipo_documento="Atualização",
        data="01/08/2026",
        medico_coordenador="Dra. Teste",
        crm="CRM-GO 0000",
    )


def _rodape() -> RodapeDocumento:
    return RodapeDocumento(
        responsavel_preenchimento="Teste",
        medico_validador="Dra. Teste",
        data_pgr="01/01/2026",
    )


def test_nucleo_web_matriz_nao_importa_streamlit() -> None:
    # Reversão que mata: inserir `import streamlit` no topo do arquivo — o
    # AST do módulo passaria a ter um Import/ImportFrom com "streamlit" fora
    # de qualquer FunctionDef.
    caminho = Path(__file__).parent.parent / "superficie" / "web_matriz.py"
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    for no in arvore.body:
        if isinstance(no, ast.Import):
            assert not any("streamlit" in alias.name for alias in no.names)
        if isinstance(no, ast.ImportFrom):
            assert no.module is None or "streamlit" not in no.module


def test_montar_envelope_usa_a_validade_informada() -> None:
    # Reversão que mata: trocar date.fromisoformat(validade_iso) por
    # date.today() — a validade cravada (2030-01-01, bem longe de "hoje")
    # deixaria de bater.
    envelope = montar_envelope("2030-01-01", True)
    assert envelope.validade == date(2030, 1, 1)
    assert envelope.assinatura_engenheiro is True


def test_montar_envelope_recusa_validade_malformada() -> None:
    # Reversão que mata: remover a chamada date.fromisoformat (ou envolvê-la
    # num try/except que engole o erro) — a validade malformada deixaria de
    # levantar ValueError.
    with pytest.raises(ValueError):
        montar_envelope("31/12/2023", True)


def test_gerar_documento_expande_ghe_em_cargos() -> None:
    # Reversão que mata: fazer gerar_documento devolver DocumentoMatriz com
    # blocos=() — nenhum LinhaCargo por cargo, nenhum nome de cargo no HTML.
    vocab = {"exame_clinico": {"nome_exibicao": "Exame Clínico", "ordem_exibicao": 1}}
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    m1 = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Carpinteiro", "Ajudante"))
    m2 = MatrizGHE(ghe_id="GHE-02", linhas=[exame], cargos=("Encarregado",))

    doc, html = gerar_documento([m1, m2], vocab, _cabecalho(), _rodape())

    assert len(doc.blocos) == 2
    assert doc.blocos[0].linhas == (
        LinhaCargo(cargo="Carpinteiro", celulas=doc.blocos[0].linhas[0].celulas),
        LinhaCargo(cargo="Ajudante", celulas=doc.blocos[0].linhas[1].celulas),
    )
    assert doc.blocos[1].linhas[0].cargo == "Encarregado"
    assert "Carpinteiro" in html
    assert "Ajudante" in html
    assert "Encarregado" in html
