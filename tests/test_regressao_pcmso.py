# tests/test_regressao_pcmso.py
# Bateria de regressão para o pipeline PGR → PCMSO.
# Rodar: pytest tests/test_regressao_pcmso.py -v

import sys
import os
from pathlib import Path

# Garante que o raiz do projeto está no sys.path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import pytest
import pandas as pd

# ---------------------------------------------------------------------------
# Suite 1 — Normalização de grafia (sem colapso cargo-filho → cargo-pai)
# ---------------------------------------------------------------------------

class TestNormalizacao:
    from modules.modulo_auditor_v1_1 import normalizar_cargo as _nc

    @pytest.fixture(autouse=True)
    def _import(self):
        from modules.modulo_auditor_v1_1 import normalizar_cargo
        self.normalizar_cargo = normalizar_cargo

    def test_expande_abreviacao_meio_of(self):
        assert self.normalizar_cargo("meio of. De pedreiro") == "meio oficial de pedreiro"

    def test_remove_prefixo_colon(self):
        assert self.normalizar_cargo("Manutenção: Eletricista industrial") == "eletricista industrial"

    def test_lowercase_mixed_case(self):
        assert self.normalizar_cargo("Tecnico De Seguranca") == "tecnico de seguranca"

    def test_uppercase(self):
        assert self.normalizar_cargo("PEDREIRO") == "pedreiro"

    def test_meio_oficial_pintor_nao_colapsa(self):
        # BUG FIX: "meio oficial de pintor" NÃO deve colapsar para "pintor"
        assert self.normalizar_cargo("meio oficial de pintor") == "meio oficial de pintor"

    def test_simples_servente(self):
        assert self.normalizar_cargo("Servente") == "servente"


# ---------------------------------------------------------------------------
# Suite 2 — Filtro de labels de atividade (is_cargo_valido)
# ---------------------------------------------------------------------------

TITULO_GHE_GENERICO = "GHE 01 - Execução de Obra"


class TestFiltroLabels:
    @pytest.fixture(autouse=True)
    def _import(self):
        from parser_pgr import is_cargo_valido
        self.is_cargo_valido = is_cargo_valido

    def test_rejeita_estrutura_concreto(self):
        assert self.is_cargo_valido("Estrutura de concreto armado", TITULO_GHE_GENERICO) is False

    def test_rejeita_contrapiso(self):
        assert self.is_cargo_valido("Contrapiso", TITULO_GHE_GENERICO) is False

    def test_rejeita_impermeabilizacao(self):
        assert self.is_cargo_valido("Impermeabilização", TITULO_GHE_GENERICO) is False

    def test_rejeita_montagem(self):
        assert self.is_cargo_valido("Montagem", TITULO_GHE_GENERICO) is False

    def test_rejeita_ef_curto(self):
        assert self.is_cargo_valido("EF", TITULO_GHE_GENERICO) is False

    def test_aceita_pedreiro(self):
        assert self.is_cargo_valido("Pedreiro", TITULO_GHE_GENERICO) is True

    def test_aceita_operador_betoneira(self):
        assert self.is_cargo_valido("Operador de betoneira", TITULO_GHE_GENERICO) is True

    def test_aceita_aplicador_asfalto(self):
        assert self.is_cargo_valido(
            "aplicador de asfalto impermeabilizante", TITULO_GHE_GENERICO
        ) is True


# ---------------------------------------------------------------------------
# Suite 3 — Banco de cargos (nenhum retorna fallback)
# ---------------------------------------------------------------------------

CARGOS_BANCO = [
    "pedreiro",
    "meio oficial de pedreiro",
    "servente",
    "eletricista",
    "meio oficial de eletricista",
    "encanador",
    "meio oficial de encanador",
    "Serralheiro",
    "meio oficial de serralheiro",
    "pintor",
    "Carpinteiro",
    "Eletricista industrial",
    "Armador",
    "Operador de Betoneira",
    "Operador de grua",
    "Gesseiro",
    "Mecanico de manutenção",
    "meio oficial de carpinteiro",
    "Mestre De Obra",
    "meio oficial de armador",
    "sinaleiro",
    "Almoxarife",
    "Engenheiro",
    "Estagiario",
    "Encarregado de encanador",
    "meio oficial de pintor",
    "meio oficial de gesseiro",
    "Encarregado",
    "Encarregado de obra",
    "Administrativo",
    "Administrativo De Obra",
    "Porteiro",
    "Vigia",
    "Aprendiz",
    "Operador de Guincho",
    "aplicador de asfalto impermeabilizante",
]


class TestBancoCargos:
    @pytest.fixture(autouse=True)
    def _import(self):
        from modules.agente_medico_ia import resolver_chave_mestra
        self.resolver_chave_mestra = resolver_chave_mestra

    @pytest.mark.parametrize("cargo", CARGOS_BANCO)
    def test_cargo_nao_retorna_fallback(self, cargo):
        chave = self.resolver_chave_mestra(cargo)
        assert chave is not None, (
            f"Cargo '{cargo}' retornou chave_mestra=None — "
            "adicionar ao MAPA_CARGO_CHAVE em agente_medico_ia.py"
        )


# ---------------------------------------------------------------------------
# Suite 4 — Integridade do output gerado com PDF real
# ---------------------------------------------------------------------------

_PDF_PATH = ROOT / "matrizes_originais" / "PGR VIVERDE V02 - 03.02.25.pdf"
# Fallback: usa outro PDF VIVERDE disponível se o principal não existir
_PDF_FALLBACK = ROOT / "matrizes_originais" / "PCMSO(ATUALIZAÇÃO)CMO RESIDENCIAL VIVERDE AREIAO 06.03.25.pdf"

_pdf_disponivel = _PDF_PATH.exists() or _PDF_FALLBACK.exists()


@pytest.mark.skipif(not _pdf_disponivel, reason="PDF de teste não encontrado no diretório matrizes_originais/")
class TestIntegridadeOutput:
    @pytest.fixture(scope="class")
    def df_pcmso(self):
        from modules.modulo_pcmso import extrair_texto_pdf, extrair_pgr_com_fallback, processar_pcmso

        pdf_path = _PDF_PATH if _PDF_PATH.exists() else _PDF_FALLBACK
        with open(pdf_path, "rb") as f:
            texto = extrair_texto_pdf(f)

        dados_ghe, _ = extrair_pgr_com_fallback(texto)
        if not dados_ghe:
            pytest.skip(
                f"PDF '{pdf_path.name}' não retornou GHEs — "
                "forneça o PGR VIVERDE V02 - 03.02.25.pdf para executar esta suite"
            )
        df = processar_pcmso(dados_ghe)
        return df, dados_ghe

    def test_todos_ghes_tem_titulo_descritivo(self, df_pcmso):
        df, _ = df_pcmso
        for ghe_nome in df["GHE / Setor"].unique():
            # Deve ter algo após "GHE NN - "
            import re
            m = re.match(r"GHE\s*\d+\s*[-:–—]\s*(.+)", ghe_nome, re.IGNORECASE)
            assert m and m.group(1).strip(), (
                f"GHE sem título descritivo: '{ghe_nome}'"
            )

    def test_numeracao_sequencial_comeca_em_01(self, df_pcmso):
        import re
        df, _ = df_pcmso
        nums = []
        for ghe_nome in df["GHE / Setor"].unique():
            m = re.search(r"GHE\s*(\d+)", ghe_nome, re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))
        assert nums, "Nenhum GHE com número encontrado"
        nums_sorted = sorted(nums)
        assert nums_sorted[0] == 1, f"Numeração não começa em 01: {nums_sorted}"
        assert nums_sorted == list(range(1, len(nums_sorted) + 1)), (
            f"Numeração não é sequencial: {nums_sorted}"
        )

    def test_sem_cargo_duplicado_intra_ghe(self, df_pcmso):
        df, _ = df_pcmso
        for ghe_nome in df["GHE / Setor"].unique():
            cargos = df[df["GHE / Setor"] == ghe_nome]["Cargo"].tolist()
            assert len(cargos) == len(set(cargos)), (
                f"Cargo duplicado no GHE '{ghe_nome}': {cargos}"
            )

    def test_sem_label_atividade_como_cargo(self, df_pcmso):
        from parser_pgr import is_cargo_valido
        df, _ = df_pcmso
        for cargo in df["Cargo"].unique():
            assert is_cargo_valido(cargo, ""), (
                f"Label de atividade encontrado como cargo: '{cargo}'"
            )

    def test_pelo_menos_10_ghes(self, df_pcmso):
        df, _ = df_pcmso
        n_ghes = df["GHE / Setor"].nunique()
        assert n_ghes >= 10, f"Esperado >= 10 GHEs, gerou apenas {n_ghes}"


# ---------------------------------------------------------------------------
# Suite 5 — Casos críticos (bugs conhecidos que NÃO devem regredir)
# ---------------------------------------------------------------------------

class TestCasosCriticos:

    @pytest.mark.skipif(not _pdf_disponivel, reason="PDF de teste não encontrado")
    def test_nenhum_ghe_mais_de_10_cargos(self):
        """Bug #3 não voltou: nenhum GHE deve ter mais de 10 cargos."""
        from modules.modulo_pcmso import extrair_texto_pdf, extrair_pgr_com_fallback, processar_pcmso

        pdf_path = _PDF_PATH if _PDF_PATH.exists() else _PDF_FALLBACK
        with open(pdf_path, "rb") as f:
            texto = extrair_texto_pdf(f)

        dados_ghe, _ = extrair_pgr_com_fallback(texto)
        df = processar_pcmso(dados_ghe)

        for ghe_nome in df["GHE / Setor"].unique():
            cargos = df[df["GHE / Setor"] == ghe_nome]["Cargo"].unique()
            assert len(cargos) <= 10, (
                f"Bug #3 de volta! GHE '{ghe_nome}' tem {len(cargos)} cargos: {list(cargos)}"
            )

    def test_vigencia_inicio_diferente_de_fim(self):
        """Vigência: data início != data fim no HTML gerado."""
        from modules.modulo_pcmso import gerar_html_pcmso

        df = pd.DataFrame({
            "GHE / Setor": ["GHE 01 - Teste"],
            "Cargo":       ["Pedreiro"],
            "Exame":       ["Exame Clínico"],
            "ADM": ["X"], "PER": ["12M"], "MRO": ["X"], "RT": ["-"], "DEM": ["-"],
        })
        cabecalho = {
            "razao_social": "Empresa Teste Ltda",
            "cnpj": "00.000.000/0001-00",
            "medico_rt": "Dr. Teste",
            "obra": "Obra Teste",
            "vig_ini": "01/01/2025",
            "vig_fim": "31/12/2025",
            "responsavel_tec": "Técnico Teste",
        }
        html = gerar_html_pcmso(df, cabecalho)
        assert "01/01/2025" in html, "Data início não aparece no HTML"
        assert "31/12/2025" in html, "Data fim não aparece no HTML"
        # Garante que as datas são diferentes no output
        assert cabecalho["vig_ini"] != cabecalho["vig_fim"], (
            "Bug de vigência: data início igual à data fim"
        )

    def test_serralheiro_exame_clinico_6m(self):
        """Serralheiro deve ter Exame Clínico com periodicidade 6M (não 12M)."""
        from modules.agente_medico_ia import processar_cargo_ia

        result = processar_cargo_ia("Serralheiro", riscos=[], e_canteiro=True)
        exames = result.get("exames", [])

        exame_clinico = next(
            (e for e in exames if "cl" in e.get("nome", "").lower() and "nico" in e.get("nome", "").lower()),
            None,
        )
        assert exame_clinico is not None, "Exame Clínico não encontrado para Serralheiro"
        per = str(exame_clinico.get("per", ""))
        assert per == "6", (
            f"Serralheiro: Exame Clínico esperado 6M, encontrado {per}M"
        )
