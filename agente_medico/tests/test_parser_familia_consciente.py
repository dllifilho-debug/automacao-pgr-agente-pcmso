from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.parser_familia_consciente import PalavraPDF, parsear_arquivo, parsear_paginas
from agente_medico.motor.tipos import GHEVerbatim
from agente_medico.motor.transcritor_pgr import gate_forma_ghe

CAMINHO_PDF_FASCINO = Path(
    "matrizes_originais/PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"
)

# Harness de integração desta fatia (molde requer_pdfs de test_transcritor_pgr.py).
requer_pdfs = pytest.mark.skipif(
    not CAMINHO_PDF_FASCINO.exists(),
    reason="PDF Fascino ausente; harness integração 003.DZ indisponível",
)


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


# ---------------------------------------------------------------------------
# Núcleo puro — palavras sintéticas copiadas VERBATIM das linhas reais
# medidas no GHE 16 (PINTURA, PDF Fascino, págs. 75-76; medição 003.DZ).
# ---------------------------------------------------------------------------

_PAGINA_GHE16_EXCERTO: tuple[PalavraPDF, ...] = (
    # linha-âncora
    _p("GHE", 10.0, 10.0),
    _p("16", 30.0, 10.0),
    _p("\x00", 45.0, 10.0),
    _p("PINTURA", 50.0, 10.0),
    # cabeçalho da tabela (2 linhas físicas — medição 003.DZ)
    _p("PERIGO", 113.1, 20.0),
    _p("GRUPO", 57.0, 25.0),
    _p("FONTE", 177.5, 25.0),
    _p("AGRAVO", 344.1, 25.0),
    # risco 1: "Vibrações localizadas (mão e braço)" — multi-linha (3 linhas)
    _p("FISICO", 57.0, 365.7),
    _p("Vibrações", 113.1, 365.7),
    _p("Operação", 177.5, 365.7),
    _p("de", 211.9, 365.7),
    _p("máquinas", 222.3, 365.7),
    _p("e", 256.2, 365.7),
    _p("localizadas", 113.1, 376.2),
    _p("(mão", 152.0, 376.2),
    _p("eletroportáteis", 177.5, 376.2),
    _p("\x00Lixadeiras", 227.5, 376.2),
    _p("e", 113.1, 386.7),
    _p("braço)", 119.1, 386.7),
    _p("de", 177.5, 386.7),
    _p("Pintura", 187.8, 386.7),
    _p("Airless,", 213.1, 386.7),
    _p("Sopradores", 239.5, 386.7),
    # risco 2: "Sílica livre" — linha única
    _p("QUIMICO", 57.0, 450.0),
    _p("Sílica", 113.1, 450.0),
    _p("livre", 132.6, 450.0),
    _p("Poeiras", 177.5, 450.0),
    _p("geradas", 204.1, 450.0),
    _p("no", 232.9, 450.0),
    _p("processo", 243.2, 450.0),
    _p("produtivo", 275.9, 450.0),
    # risco 3: "Destilados \x00Petróleo) leves tratados com hidrogênio." — multi-linha (4 linhas)
    _p("QUIMICO", 57.0, 500.0),
    _p("Destilados", 113.1, 500.0),
    _p("Exposição", 177.5, 500.0),
    _p("a", 213.6, 500.0),
    _p("tintas", 219.5, 500.0),
    _p("e", 239.5, 500.0),
    _p("seus", 245.5, 500.0),
    _p("componentes.", 263.1, 500.0),
    _p("\x00Petróleo)", 113.1, 510.5),
    _p("leves", 147.5, 510.5),
    _p("tratados", 113.1, 521.0),
    _p("com", 142.3, 521.0),
    _p("hidrogênio.", 113.1, 531.5),
)


def test_nucleo_puro_extrai_nome_e_riscos_ghe16_verbatim() -> None:
    ghes = parsear_paginas([_PAGINA_GHE16_EXCERTO])
    assert len(ghes) == 1
    ghe = ghes[0]
    assert ghe.nome == "PINTURA"
    assert len(ghe.riscos) == 3

    vibracoes, silica, destilados = ghe.riscos

    assert vibracoes.agente == "Vibrações localizadas (mão e braço)"
    assert vibracoes.fonte_geradora == (
        "Operação de máquinas e eletroportáteis \x00Lixadeiras de Pintura Airless, Sopradores"
    )

    assert silica.agente == "Sílica livre"
    assert silica.fonte_geradora == "Poeiras geradas no processo produtivo"

    assert destilados.agente == "Destilados \x00Petróleo) leves tratados com hidrogênio."
    assert destilados.fonte_geradora == "Exposição a tintas e seus componentes."

    assert all(r.quantificacao == "" for r in ghe.riscos)


def test_nucleo_puro_saida_aprova_no_gate_forma_ghe() -> None:
    ghes = parsear_paginas([_PAGINA_GHE16_EXCERTO])
    aprovados, pendencias = gate_forma_ghe(ghes)
    assert aprovados == ghes
    assert pendencias == ()


# ---------------------------------------------------------------------------
# Calibração por bloco: cabeçalho deslocado (molde GHE 09/17 da medição
# 003.DZ, FONTE@198.5) — sob a constante fixa 177 abandonada pelo
# Arquiteto, a palavra 'Armadilha' (x0=180) cairia erradamente na banda
# FONTE; com calibração por bloco ela fica em AGENTE, porque a banda real
# deste bloco só começa em ~195.5 (198.5 - tolerância).
# ---------------------------------------------------------------------------

_PAGINA_CABECALHO_DESLOCADO: tuple[PalavraPDF, ...] = (
    _p("GHE", 10.0, 10.0),
    _p("09", 30.0, 10.0),
    _p("-", 45.0, 10.0),
    _p("TESTE", 50.0, 10.0),
    _p("PERIGO", 113.1, 20.0),
    _p("GRUPO", 57.0, 25.0),
    _p("FONTE", 198.5, 25.0),
    _p("AGRAVO", 296.8, 25.0),
    _p("FISICO", 57.0, 50.0),
    _p("Agente", 113.1, 50.0),
    _p("Armadilha", 180.0, 50.0),
    _p("FonteReal", 198.5, 50.0),
)


def test_calibracao_por_bloco_acompanha_cabecalho_deslocado() -> None:
    ghes = parsear_paginas([_PAGINA_CABECALHO_DESLOCADO])
    assert len(ghes) == 1
    (risco,) = ghes[0].riscos
    assert risco.agente == "Agente Armadilha"
    assert risco.fonte_geradora == "FonteReal"


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs) — PDF real do Fascino. parsear_arquivo
# roda pdfplumber.extract_words sobre as 119 páginas do documento (~1min,
# medido 003.DZ) — fixture de módulo evita repetir o custo por teste.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ghes_fascino() -> tuple[GHEVerbatim, ...]:
    return parsear_arquivo(CAMINHO_PDF_FASCINO)


@requer_pdfs
def test_parsear_arquivo_devolve_19_blocos(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    # 20º cabeçalho (GHE sem número, pág. 89) fica FORA — mesma regra do
    # recorte vigente, DT-003DS-01 inalterada (não é âncora reconhecida por
    # eh_cabecalho_ghe).
    assert len(ghes_fascino) == 19


@requer_pdfs
def test_parsear_arquivo_ghe16_pintura_contem_agentes_medidos(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    pintura = next(g for g in ghes_fascino if g.nome == "PINTURA")
    agentes = {r.agente for r in pintura.riscos}
    assert "Sílica livre" in agentes
    assert "Tolueno" in agentes
    assert "Etanol" in agentes


@requer_pdfs
def test_parsear_arquivo_toda_quantificacao_vazia(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    assert all(r.quantificacao == "" for g in ghes_fascino for r in g.riscos)


@requer_pdfs
def test_parsear_arquivo_gate_forma_aprova_os_19(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    aprovados, pendencias = gate_forma_ghe(ghes_fascino)
    assert aprovados == ghes_fascino
    assert pendencias == ()


@requer_pdfs
def test_invariante_fechamento_237_linhas_de_risco(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    """Medição 003.DZ (Arquiteto, texto linearizado págs. 28-92): 237
    linhas-de-risco ancoradas por token de categoria. Cada RiscoVerbatim
    corresponde a exatamente 1 linha-de-categoria (linha-âncora do risco);
    a soma sobre os 19 blocos tem de fechar com o total medido —
    divergência é BLOQUEADOR (reportar o par, não ajustar)."""
    total = sum(len(g.riscos) for g in ghes_fascino)
    assert total == 237
