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
# 003.EP fatia 1 — overflow da célula "Cargo / Função": sintético com DUAS
# linhas de continuação na banda do valor, seguidas por uma linha na banda
# do rótulo (simula "Qt. Trabalhadores") e então OUTRA linha de volta na
# banda do valor (simula continuação de um campo seguinte, ex. "Descrição
# das Atividades" — medição 003.EP fatia 0 mostrou que essa banda não é
# exclusiva da célula de cargo). Nunca exercitado nos 19 blocos reais do
# Fascino (só têm 0 ou 1 linha de overflow) — cobre o item 1 dos "abertos"
# de 003ep_anatomia_cargo.md.
# ---------------------------------------------------------------------------

_PAGINA_CARGO_OVERFLOW_DUPLO: tuple[PalavraPDF, ...] = (
    _p("GHE", 10.0, 10.0),
    _p("99", 30.0, 10.0),
    _p("-", 45.0, 10.0),
    _p("TESTE", 50.0, 10.0),
    _p("PERIGO", 113.1, 20.0),
    _p("GRUPO", 57.0, 25.0),
    _p("FONTE", 177.5, 25.0),
    _p("AGRAVO", 296.8, 25.0),
    # rótulo "Cargo / Função" + 1ª palavra do valor (banda do valor = x0=279.2)
    _p("Cargo", 58.5, 50.0),
    _p("/", 68.0, 50.0),
    _p("Função", 72.0, 50.0),
    _p("PrimeiroCargo", 279.2, 50.0),
    # continuação 1 — banda do valor, DEVE entrar
    _p("SegundoCargo", 279.2, 60.0),
    # continuação 2 — banda do valor, DEVE entrar
    _p("TerceiroCargo", 279.2, 70.0),
    # linha na banda do RÓTULO (simula "Qt. Trabalhadores") — encerra a célula
    _p("Qt.", 58.5, 80.0),
    _p("Trabalhadores", 68.0, 80.0),
    _p("05", 120.0, 80.0),
    # de volta à banda do valor — NÃO deve entrar (já encerrou em cima)
    _p("NaoDeveEntrar", 279.2, 90.0),
)


def test_celula_cargo_para_ao_voltar_para_banda_do_rotulo() -> None:
    ghes = parsear_paginas([_PAGINA_CARGO_OVERFLOW_DUPLO])
    assert len(ghes) == 1
    (celula,) = ghes[0].cargos
    assert "PrimeiroCargo" in celula
    assert "SegundoCargo" in celula
    assert "TerceiroCargo" in celula
    assert "NaoDeveEntrar" not in celula


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs) — PDF real do Fascino. parsear_arquivo
# roda pdfplumber.extract_words sobre as 119 páginas do documento (~1min,
# medido 003.DZ) — fixture de módulo evita repetir o custo por teste.
# ---------------------------------------------------------------------------


@pytest.fixture(scope="module")
def ghes_fascino() -> tuple[GHEVerbatim, ...]:
    return parsear_arquivo(CAMINHO_PDF_FASCINO)


@requer_pdfs
def test_celula_cargo_captura_overflow_ghe03_real(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    # GHE-03 (003.EP fatia 0, M1/M2): único bloco (com GHE-06) cuja lista de
    # cargos quebra em 2 linhas físicas na tabela — "Encarregado" no fim do
    # rótulo, "de Pintor..." na continuação (quebra no MEIO da palavra).
    supervisao = next(
        g for g in ghes_fascino if g.nome == "SUPERVISÃO DE ATIVIDADES EM OBRA"
    )
    (celula,) = supervisao.cargos
    assert "Encarregado de Pintor" in celula
    assert "Auxiliar de Obra" in celula


@requer_pdfs
def test_ghes_sem_overflow_inalterados_real(ghes_fascino: tuple[GHEVerbatim, ...]) -> None:
    # Os 17 blocos SEM overflow (todos exceto GHE-03/GHE-06, 003.EP fatia 0
    # M1) mantêm a célula byte-a-byte igual ao baseline pré-fatia-1: só
    # `palavras[3:]` da própria linha de rótulo, verbatim (\x00 incluso).
    esperado_por_nome = {
        "ENGENHARIA": (
            "Auxiliar de Engenharia \x003121\x0005\x00, Estagiário de "
            "Engenharia \x004110\x0010\x00, Assistente de Engenharia "
            "\x003121\x0005\x00, Estagiário de Obra \x004110\x0010\x00"
        ),
        "SESMT": (
            "Técnico de Segurança do Trabalho \x003516\x0005\x00, "
            "Supervisor de Segurança do Trabalho \x004101\x0005\x00"
        ),
        "ALMOXARIFADO": (
            "Almoxarife \x004141\x0005\x00, Auxiliar de Almoxarifado "
            "\x004141\x0005\x00, Assistente de Almoxarifado \x004141\x0005\x00, "
            "Supervisor de Almoxarifado \x004141\x0005\x00"
        ),
        "LIMPEZA": "Auxiliar de limpeza e conservação \x005143\x0020\x00",
        "PRODUÇÃO": (
            "Pedreiro \x007152\x0010\x00; Ajudante de produção civil "
            "\x007170\x0020\x00"
        ),
        "CARPINTARIA": "Carpinteiro \x007155\x0005\x00",
        "ARMAÇÃO": "Armador \x007153\x0015\x00",
        "INSTALAÇÕES HIDRO\x00SANITÁRIAS": (
            "Encanador \x007241\x0010\x00, Auxiliar de Encanador \x007241\x0010\x00"
        ),
        "ELÉTRICA": (
            "Eletricista \x007156\x0015\x00, Auxiliar de eletricista "
            "\x007156\x0015\x00"
        ),
        "BETONEIRA": "Operador de Betoneiro \x007154\x0005\x00",
        "SINALIZAÇÃO DE GRUA": "Sinaleiro \x007821\x0045\x00",
        "OPERAÇÃO DE GRUA": "Operador de grua \x007821\x0010\x00.",
        "OPERAÇÃO COM ELEVADOR DE CARGA": (
            "Operador de Elevador de carga \x007822\x0005\x00"
        ),
        "PINTURA": "Pintor \x007166\x0010\x00",
        "SERRALHERIA": "Serralheiro \x007244\x0040\x00",
        "MONTAGEM": "Montador \x007251\x0005\x00",
        "VENDAS": (
            "Recepcionista Demonstradora \x004221\x0005\x00, Recepcionista "
            "Comercial \x004221\x0005\x00"
        ),
    }
    assert len(esperado_por_nome) == 17
    for ghe in ghes_fascino:
        if ghe.nome not in esperado_por_nome:
            continue
        (celula,) = ghe.cargos
        assert celula == esperado_por_nome[ghe.nome], ghe.nome


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
