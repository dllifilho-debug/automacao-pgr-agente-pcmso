from __future__ import annotations

import unicodedata
from pathlib import Path

import pytest

from agente_medico.motor.extracao_fds import _recortar_composicao, extrair_texto_fds

PASTA = Path("fds_originais")

CIPLAN = PASTA / "01 - FISPQ_cimento - Ciplan.pdf"
TIGRE = PASTA / "270 -FISPQ -  Adesivo PVC Incolor Tigre.pdf"
TINTA = PASTA / "tinta_acrilica.pdf"
AMANCO = PASTA / "44 - FISPQ_solução limpadora - Amanco.pdf"
LEINERTEX = PASTA / "70 - FISPQ_textura textucril - Leinertex.pdf"
MASSA = PASTA / "Massa-Corrida.pdf"

TODOS = [CIPLAN, TIGRE, TINTA, AMANCO, LEINERTEX, MASSA]

# Os PDFs vivem em fds_originais/ (untracked). Sem eles, os testes de integração
# não são exercitáveis — skip explícito, não falha mascarada (espelha test_extracao_fds.py).
requer_pdfs = pytest.mark.skipif(
    not all(p.exists() for p in TODOS),
    reason="PDFs de fds_originais/ ausentes (untracked); medição 003.BE indisponível",
)


# ---------------------------------------------------------------------------
# Núcleo puro (_recortar_composicao) — rodam sempre, sem PDF.
# ---------------------------------------------------------------------------


def test_ancora_e_titulo_fim_mesma_pagina_inclui_ruido_pos_titulo() -> None:
    # Espelho sintético do Tigre: título-fim intercalado ANTES de um triplo
    # CAS posterior — sobre-inclusão deve preservar o ruído, não cortar nele.
    pagina = "\n".join(
        [
            "1. IDENTIFICAÇÃO",
            "3. COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES",
            "Acetona 67-64-1 30 – 70",
            "2. IDENTIFICAÇÃO DE PERIGOS",
            "Metiletilcetona (MEK) 78-93-3 10 – 42",
        ]
    )
    resultado = _recortar_composicao([pagina])
    assert resultado is not None
    assert "Acetona 67-64-1 30 – 70" in resultado
    assert "2. IDENTIFICAÇÃO DE PERIGOS" in resultado
    assert "Metiletilcetona (MEK) 78-93-3 10 – 42" in resultado


def test_ancora_quebrada_em_duas_linhas_intercalada_com_endereco() -> None:
    # Espelho Tigre: título quebrado em 2 linhas, sufixo intercalado com endereço.
    pagina = "\n".join(
        [
            "ENDEREÇO: RUA X, 84 – DISTRITO / 3. COMPOSIÇÃO E INFORMAÇÕES SOBRE OS",
            "JOINVILLE – SC. INGREDIENTES",
            "Acetona 67-64-1 30 – 70",
            "2. IDENTIFICAÇÃO DE PERIGOS",
        ]
    )
    resultado = _recortar_composicao([pagina])
    assert resultado is not None
    assert resultado.startswith("ENDEREÇO: RUA X, 84 – DISTRITO / 3. COMPOSIÇÃO E INFORMAÇÕES SOBRE OS")


def test_ancora_sem_os_intercalada_com_outro_titulo_na_mesma_linha() -> None:
    # Espelho Ciplan: grafia sem "OS", e a própria linha-âncora contém o
    # título "1 IDENTIFICAÇÃO..." antes dela — a busca do fim só começa na
    # linha SEGUINTE à âncora, então esta linha não pode casar como fim.
    pagina = "\n".join(
        [
            "1 IDENTIFICAÇÃO DO PRODUTO E DA EMPRESA 2 COMPOSIÇÃO E INFORMAÇÕES SOBRE INGREDIENTES",
            "Silicato tricálcico 20 - 70 12168-85-3",
            "3 IDENTIFICAÇÃO DE PERIGOS 4 MEDIDAS DE PRIMEIROS SOCORROS",
        ]
    )
    resultado = _recortar_composicao([pagina])
    assert resultado is not None
    assert "Silicato tricálcico 20 - 70 12168-85-3" in resultado
    assert "3 IDENTIFICAÇÃO DE PERIGOS 4 MEDIDAS DE PRIMEIROS SOCORROS" in resultado


def test_ancora_ausente_devolve_none() -> None:
    pagina = "1. IDENTIFICAÇÃO DO PRODUTO\nNada de composição aqui."
    assert _recortar_composicao([pagina]) is None


def test_ancora_fim_pagina_a_titulo_fim_pagina_b_inclui_pagina_b_inteira() -> None:
    # Espelho Massa: âncora no fim da página A, título-fim na página B —
    # região = resto de A + página B INTEIRA (mesmo linhas pós-título-fim).
    pagina_a = "\n".join(
        [
            "Frases de precaução: ...",
            "3 – COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES",
        ]
    )
    pagina_b = "\n".join(
        [
            "Derivados de: 2634-33-5",
            "55965-84-9",
            "4 – MEDIDAS DE PRIMEIROS-SOCORROS",
            "Inalação: tratamento sintomático.",
        ]
    )
    resultado = _recortar_composicao([pagina_a, pagina_b])
    assert resultado is not None
    assert "3 – COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES" in resultado
    assert "Frases de precaução" not in resultado
    assert "Inalação: tratamento sintomático." in resultado


def test_titulo_fim_ausente_vai_ate_ultima_pagina() -> None:
    pagina_a = "3 – COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES\nAcetona 67-64-1"
    pagina_b = "mais texto sem título-fim nenhum"
    resultado = _recortar_composicao([pagina_a, pagina_b])
    assert resultado is not None
    assert "mais texto sem título-fim nenhum" in resultado


def test_saida_verbatim_preserva_acento_e_caixa() -> None:
    pagina = "3 – COMPOSIÇÃO E INFORMAÇÕES SOBRE OS INGREDIENTES\nAcetona"
    resultado = _recortar_composicao([pagina])
    assert resultado is not None
    assert "COMPOSIÇÃO" in resultado


# ---------------------------------------------------------------------------
# Integração (skipif espelhando test_extracao_fds.py; PDFs untracked).
# ---------------------------------------------------------------------------


def _normalizar(linha: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", linha) if not unicodedata.combining(c)
    )
    return sem_acento.upper()


@requer_pdfs
@pytest.mark.parametrize("caminho", TODOS, ids=lambda p: p.name)
def test_extrai_regiao_com_ancora_em_todos_os_pdfs(caminho: Path) -> None:
    resultado = extrair_texto_fds(caminho)
    assert resultado is not None
    primeira_linha = resultado.splitlines()[0]
    assert "COMPOSICAO E INFORMACOES SOBRE" in _normalizar(primeira_linha)


@requer_pdfs
def test_tigre_preserva_triplos_intercalados_pos_titulo_fim() -> None:
    resultado = extrair_texto_fds(TIGRE)
    assert resultado is not None
    for cas in ("67-64-1", "78-93-3", "9003-22-9", "141-78-6", "7128-64-5"):
        assert cas in resultado
    assert "30 – 70" in resultado


@requer_pdfs
def test_ciplan_cas_e_grafia_ausente_presentes() -> None:
    resultado = extrair_texto_fds(CIPLAN)
    assert resultado is not None
    assert "12168-85-3" in resultado
    assert "vários" in resultado


@requer_pdfs
def test_massa_bloco_derivados_cruza_pagina() -> None:
    resultado = extrair_texto_fds(MASSA)
    assert resultado is not None
    assert "2634-33-5" in resultado
    assert "55965-84-9" in resultado
