"""PCMSO gerado na rodada da matriz (D-ARQ-96 etapa 3, fatia 1). Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from docx import Document
from docx.oxml.ns import qn

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, MatrizGHE, Momento, RiscoPGR
from agente_medico.superficie.agravos_pcmso import OrigemAgravo, VocabularioAgravos, carregar_agravos
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.documento_pcmso import (
    EM_BRANCO,
    MODELO_PADRAO,
    AvisosPCMSO,
    DadosPCMSO,
    celulas_do_exame,
    dados_do_cabecalho,
    gerar_pcmso_docx,
    linhas_de_aviso,
    linhas_de_perigo,
    rotulo_exame,
    rotulo_grupo,
    valores_dos_campos,
)

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def protocolo() -> Any:
    return carregar(PROTOCOLO_DIR)


@pytest.fixture(scope="module")
def vocabulario(protocolo: Any) -> VocabularioAgravos:
    return carregar_agravos(protocolo.vocabulario.agentes)


def _risco(termo: str, tipo: str, agente: str | None, agravo: str = "") -> RiscoPGR:
    return RiscoPGR(tipo=tipo, agente=agente, quantificacao=None, severidade=None, termo=termo, agravo=agravo)


def _dados(**kw: str) -> DadosPCMSO:
    base = dict(razao_social="EMPRESA X LTDA", obra="OBRA Y", data_documento="15/10/2026",
                tipo_documento="Atualização", medico_nome="Dra. Z", medico_crm="00000/GO")
    base.update(kw)
    return DadosPCMSO(**base)


# Reversão: trocar Momento.RT por Momento.MR (ou o "-" fixo de "APÓS ADM." por "X").
def test_celulas_do_exame_seguem_as_colunas_do_modelo() -> None:
    exame = ExameEmitido("exame_clinico", 12, {Momento.ADM, Momento.PER, Momento.RT, Momento.DEM})
    assert celulas_do_exame(exame) == ("X", "-", "12 meses", "X", "-", "X")


# Reversão: escrever a periodicidade sem checar PER nos momentos.
def test_sem_periodico_a_coluna_fica_com_traco() -> None:
    assert celulas_do_exame(ExameEmitido("rx_torax_oit", 0, {Momento.ADM}))[2] == "-"


# Reversão: ignorar `codigo_seconci` ou inventar código para o exame sem campo.
def test_rotulo_do_exame_com_e_sem_codigo(protocolo: Any) -> None:
    avisos = AvisosPCMSO()
    assert rotulo_exame("exame_clinico", protocolo.vocabulario.exames, avisos) == "(0295) Exame Clínico"
    sem = rotulo_exame("arsenio_urina", protocolo.vocabulario.exames, avisos)
    assert not sem.startswith("(")
    assert avisos.exames_sem_codigo == [sem]


# Reversão: escrever o tipo cru do PGR ("QUIMICO") em vez do rótulo do modelo.
@pytest.mark.parametrize(("tipo", "rotulo"), [("QUIMICO", "Químico"), ("Físico", "Físico"),
                                              ("ERGONÔMICO", "Ergonômicos"), ("ACIDENTES", "Acidente")])
def test_grupo_sai_com_o_rotulo_do_modelo(tipo: str, rotulo: str) -> None:
    assert rotulo_grupo(tipo) == rotulo


# Reversões: não agrupar os psicossociais; não deduplicar o perigo repetido; agravo do dicionário trocado pelo do PGR.
def test_perigos_dedup_psicossocial_agrupado_e_origem(vocabulario: VocabularioAgravos) -> None:
    ghe = GHEPGR(id="GHE-01", nome="X", cargos=(), epis=(), produtos_quimicos=(), psicossocial=True, riscos=(
        _risco("Ruído", "FISICO", "ruido", "Perda auditiva"),
        _risco("Ruído", "FISICO", "ruido", "Perda auditiva"),
        _risco("Liderança", "ERGONOMICO", None),
        _risco("Demandas no trabalho", "ERGONOMICO", None),
        _risco("Bisfenol A", "QUIMICO", None, "Irritação ocular."),
        _risco("Perigo sem texto", "ACIDENTE", None, ""),
    ))
    avisos = AvisosPCMSO()
    linhas = linhas_de_perigo(ghe, vocabulario, avisos)
    assert [linha.perigo for linha in linhas] == [
        "Ruído", "Bisfenol A", "Perigo sem texto", "Fatores psicossociais: Liderança; Demandas no trabalho"]
    assert "PAINPSE" in linhas[0].agravo
    assert [linha.origem for linha in linhas[1:3]] == [OrigemAgravo.PGR_CONFERIR, OrigemAgravo.AUSENTE]
    assert (avisos.agravos_do_pgr, avisos.agravos_ausentes) == (1, 1)


# Reversão: deixar campo vazio sem EM_BRANCO ou sem aviso; cronograma sem virar o ano.
def test_campos_vazios_viram_branco_visivel_e_aviso() -> None:
    avisos = AvisosPCMSO()
    valores = valores_dos_campos(_dados(cnpj=""), avisos)
    assert valores["CNPJ"] == EM_BRANCO
    assert "CNPJ" in avisos.campos_em_branco
    assert (valores["CRONOGRAMA_MES_01"], valores["CRONOGRAMA_MES_04"], valores["CRONOGRAMA_MES_13"]) == (
        "OUT 2026", "JAN 2027", "OUT 2027")
    assert (valores["CRONOGRAMA_INICIO"], valores["CRONOGRAMA_FIM"]) == ("OUTUBRO DE 2026", "OUTUBRO DE 2027")
    assert valores["REVISAO_CONSIDERACOES"] == "Atualização do PCMSO"


# Reversão: tirar a remoção do prefixo "CRM" (sairia "CRM: CRM 00000/GO").
def test_dados_do_cabecalho_da_matriz() -> None:
    cab = CabecalhoDocumento(empresa="E", obra="O", tipo_documento="Adendo", data="01/02/2026",
                             medico_coordenador="Dra. Z", crm="00000/GO")
    dados = dados_do_cabecalho(cab)
    assert (dados.razao_social, dados.obra, dados.medico_crm) == ("E", "O", "00000/GO")


@pytest.fixture(scope="module")
def gerado(tmp_path_factory: pytest.TempPathFactory, protocolo: Any,
           vocabulario: VocabularioAgravos) -> tuple[Any, AvisosPCMSO]:
    ghe = GHEPGR(id="GHE-09", nome="HIDROSSANITÁRIO", cargos=("ENCANADOR",), epis=(), produtos_quimicos=(),
                 psicossocial=False, riscos=(_risco("Ruído", "FISICO", "ruido"),))
    matriz = MatrizGHE(ghe_id="GHE-09", nome_ghe="HIDROSSANITÁRIO", cargos=("ENCANADOR",), linhas=[
        ExameEmitido("audiometria", 12, {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM})])
    destino = tmp_path_factory.mktemp("pcmso") / "pcmso.docx"
    avisos = gerar_pcmso_docx([matriz], PGR(validade=date(2027, 1, 1), assinatura_engenheiro=True, ghes=(ghe,)),
                              protocolo.vocabulario.exames, vocabulario, _dados(), destino)
    return Document(str(destino)), avisos


def _texto(doc: Any) -> str:
    partes = [doc.element.body] + [s.header._element for s in doc.sections]
    return "\n".join("".join(t.text or "" for t in p.iter(qn("w:t"))) for parte in partes for p in parte.iter(qn("w:p")))


# Reversão: não substituir algum campo (no corpo ou no cabeçalho de página) ou deixar a marca {{BLOCOS_GHE}}.
def test_documento_gerado_sem_campo_do_modelo(gerado: tuple[Any, AvisosPCMSO]) -> None:
    texto = _texto(gerado[0])
    assert "{{" not in texto
    assert "EMPRESA X LTDA" in texto


# Reversão: não inserir o bloco do GHE (ou inseri-lo fora do lugar da marca, depois da seção 11).
def test_bloco_do_ghe_entra_antes_da_secao_11(gerado: tuple[Any, AvisosPCMSO]) -> None:
    texto = _texto(gerado[0])
    assert texto.index("Setor: GHE 09 - HIDROSSANITÁRIO") < texto.index("11. PROGRAMA DE VACINAÇÃO")
    assert "(0281) Audiometria" in texto
    assert "Cargo: ENCANADOR" in texto


# Reversão: gerar a partir do modelo de revisão (com realce e comentários) em vez do modelo sem marcas.
def test_modelo_de_geracao_sem_realce_nem_comentario() -> None:
    doc = Document(str(MODELO_PADRAO))
    assert not list(doc.element.body.iter(qn("w:highlight")))
    assert not list(doc.comments)


# Reversão: remover o `st.download_button` do PCMSO em pagina_matriz (ou não montar `pcmso_bytes`).
def test_tela_oferece_o_pcmso_com_os_exames_da_matriz(monkeypatch: pytest.MonkeyPatch) -> None:
    import io

    from streamlit.testing.v1 import AppTest

    from agente_medico.motor.tipos import Resultado
    from agente_medico.superficie.web_matriz import pagina_matriz
    from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario

    arquivos: dict[str, bytes] = {}

    def _download_espiao(rotulo: str, dados: Any, **kwargs: Any) -> bool:
        arquivos[str(kwargs.get("file_name"))] = dados
        return False

    monkeypatch.setattr("streamlit.download_button", _download_espiao)
    matriz = MatrizGHE(ghe_id="GHE-01", nome_ghe="ADMINISTRAÇÃO", cargos=("ASSISTENTE",), linhas=[
        ExameEmitido("exame_clinico", 12, {Momento.ADM, Momento.PER, Momento.MR, Momento.RT, Momento.DEM})])
    _mockar_parse_deterministico(monkeypatch, Resultado(status="OK", matrizes=[matriz]))

    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    nome = next(n for n in arquivos if n.startswith("PCMSO") or n == "pcmso.docx")
    texto = "\n".join(p.text for p in Document(io.BytesIO(arquivos[nome])).paragraphs)
    celulas = [c.text for t in Document(io.BytesIO(arquivos[nome])).tables for r in t.rows for c in r.cells]
    assert "(0295) Exame Clínico" in celulas
    assert "{{" not in texto


# Reversão: tirar a linha `avisos.cnpj_invalido = ...` de `valores_dos_campos` — o CNPJ com DV errado (PGR TPB
# Andrade) sai no PCMSO sem aviso; o válido continua sem aviso.
def test_cnpj_com_digito_errado_vira_aviso() -> None:
    avisos = AvisosPCMSO()
    valores_dos_campos(_dados(cnpj="50.055.341/0001-52"), avisos)
    assert avisos.cnpj_invalido
    assert any("dígito verificador" in linha for linha in linhas_de_aviso(avisos))
    avisos_ok = AvisosPCMSO()
    valores_dos_campos(_dados(cnpj="43.091.205/0001-32"), avisos_ok)
    assert not avisos_ok.cnpj_invalido
