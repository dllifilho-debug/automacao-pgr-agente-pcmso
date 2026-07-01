from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_fds import extrair_tabelas_fds

PASTA = Path("fds_originais")

CIPLAN = PASTA / "01 - FISPQ_cimento - Ciplan.pdf"
TIGRE = PASTA / "270 -FISPQ -  Adesivo PVC Incolor Tigre.pdf"
TINTA = PASTA / "tinta_acrilica.pdf"
LEINERTEX = PASTA / "70 - FISPQ_textura textucril - Leinertex.pdf"
MASSA = PASTA / "Massa-Corrida.pdf"

TODOS = [CIPLAN, TIGRE, TINTA, LEINERTEX, MASSA]

# Os PDFs vivem em fds_originais/ (untracked). Sem eles, a fatia não é exercitável —
# skip explícito, não falha mascarada.
pytestmark = pytest.mark.skipif(
    not all(p.exists() for p in TODOS),
    reason="PDFs de fds_originais/ ausentes (untracked); medição 003.AS indisponível",
)


@pytest.mark.parametrize("caminho", TODOS, ids=lambda p: p.name)
def test_extrai_ao_menos_uma_tabela_sem_erro(caminho: Path) -> None:
    # Forma bruta verificável sobre os 5: roda sem erro, devolve >=1 tabela.
    # Asserção fraca onde a composição NÃO está isolada (Ciplan/Tigre — grid
    # multi-seção fundido, DT-003AS-01); asserção forte é por-arquivo abaixo.
    tabelas = extrair_tabelas_fds(caminho)
    assert isinstance(tabelas, list)
    assert len(tabelas) >= 1
    for tab in tabelas:
        assert isinstance(tab, list)


def test_tinta_header_composicao_literal() -> None:
    # Tinta: composição ISOLADA com gabarito -> asserção literal forte.
    # Header e 9 linhas de dado, byte a byte do extract_tables() puro (medição 003.AS).
    tabelas = extrair_tabelas_fds(TINTA)
    primeira = tabelas[0]
    assert primeira[0] == [
        "", "Nome Químico", "CAS\nNumber",
        "Faixa de\nConcentração (%)", "Símbolo", "Frases R",
    ]
    # 1 header + 9 componentes = 10 linhas.
    assert len(primeira) == 10
    # CAS do TiO2 vem com \n INTRA-token (quebra de render, não separador multi-CAS):
    # prova literal da patologia que a transcrição (DT-003AS-01) terá de desambiguar.
    assert primeira[2][2] == "134363-67-\n7"


def test_leinertex_massa_cas_empilhado_literal() -> None:
    # Leinertex e Massa: composição ISOLADA, bloco "Derivados de:" com CAS multi-linha.
    # Prova literal do \n-empilhado que a montagem de bloco (D-ARQ-45/46) consome.
    for caminho in (LEINERTEX, MASSA):
        tabelas = extrair_tabelas_fds(caminho)
        primeira = tabelas[0]
        assert primeira[0] == ["Nome Químico", "Nº CAS", "Faixa de Concentração (%)"]
        # Primeira linha de dado: "Derivados de:" com 2 CAS empilhados por \n numa célula.
        assert primeira[1][1] == "2634-33-5\n55965-84-9"


def test_ciplan_composicao_fundida_celula_crua() -> None:
    # Ciplan: composição NÃO isolada — fundida com seção 1 num grid de 8 colunas
    # (DT-003AS-01). Asserção fraca + uma célula crua literal que prova a grafia
    # CAS-ausente "vários" (uma das grafias que a transcrição mapeará p/ cas="").
    tabelas = extrair_tabelas_fds(CIPLAN)
    assert len(tabelas) >= 1
    # "vários" aparece como CAS cru do Sulfato de cálcio na tabela fundida da pág 0.
    achatado = [celula for tab in tabelas for linha in tab for celula in linha]
    assert "vários" in achatado
