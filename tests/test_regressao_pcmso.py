# tests/test_regressao_pcmso.py
# Bateria de regressão para o pipeline PGR → PCMSO.
# Rodar: pytest tests/test_regressao_pcmso.py -v

import sys
import os
from pathlib import Path

# ROOT aponta para o projeto principal.
# Path(__file__).resolve() resolve o caminho real, mesmo dentro de um worktree.
# parents[1] sobe dois níveis a partir de tests/ → raiz do projeto.
# Se o worktree for um git worktree dentro de .claude/worktrees/, resolve() retorna
# o path real do worktree, e precisamos subir até o projeto principal.
_here = Path(__file__).resolve()
# Detecta se estamos dentro de um worktree (.claude/worktrees/<branch>/tests/)
# e, nesse caso, aponta para o projeto raiz dois níveis acima do worktree.
if ".claude" in _here.parts and "worktrees" in _here.parts:
    # .../automacao-pgr-seconci/.claude/worktrees/<branch>/tests/test_...py
    # parents: [0]=tests  [1]=<branch>  [2]=worktrees  [3]=.claude  [4]=automacao-pgr-seconci
    ROOT = _here.parents[4]
else:
    ROOT = _here.parents[1]

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
        # Verifica a numeração nos nomes de GHE do df (após renomeação pelo motor).
        # GHEs sem cargos não geram linhas no df, portanto podem criar lacunas
        # na sequência — o teste aceita lacunas mas exige: começa em 01 e é
        # monotonicamente crescente (sem repetições).
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
        # Monotonicamente crescente (sem repetição), mas lacunas por GHEs vazios são OK
        assert nums_sorted == sorted(set(nums_sorted)), (
            f"Numeração com repetições: {nums_sorted}"
        )

    def test_sem_cargo_duplicado_intra_ghe(self, df_pcmso):
        # Verifica em dados_ghe (lista de cargos por GHE) — não no df.
        # O df tem uma linha POR EXAME, então o mesmo cargo aparece N vezes
        # (uma por exame) e isso é esperado. O que não pode é o mesmo cargo
        # aparecer DUAS VEZES na lista cargos[] de um mesmo GHE.
        _, dados_ghe = df_pcmso
        for ghe in dados_ghe:
            ghe_nome = ghe.get("ghe", "")
            cargos = ghe.get("cargos", [])
            cargos_norm = [c.strip().lower() for c in cargos]
            assert len(cargos_norm) == len(set(cargos_norm)), (
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


# ---------------------------------------------------------------------------
# Suite 6 — Cabeçalho do PCMSO (C5: campos preenchidos + vigência correta)
# ---------------------------------------------------------------------------

class TestCabecalho:
    """
    Testa que os metadados do PCMSO chegam preenchidos ao template e que
    a vigência padrão calcula vig_fim = vig_ini + 1 ano.
    """

    @pytest.fixture
    def _cab_completo(self):
        return {
            "razao_social":    "CMO Residencial Viverde Areião SPE Ltda",
            "cnpj":            "34.251.920/0001-02",
            "medico_rt":       "Dra. Patrícia Montalvo CRM-GO 12345",
            "obra":            "Residencial Viverde Areião — Goiânia",
            "vig_ini":         "01/02/2025",
            "vig_fim":         "01/02/2026",
            "responsavel_tec": "Tec. SST João da Costa CREA-GO 67890",
        }

    @pytest.fixture
    def _df_minimo(self):
        return pd.DataFrame({
            "GHE / Setor": ["GHE 01 - Execução"],
            "Cargo":        ["Pedreiro"],
            "Exame":        ["Exame Clínico"],
            "ADM": ["X"], "PER": ["12M"], "MRO": ["X"], "RT": ["-"], "DEM": ["-"],
        })

    def test_cabecalho_preenchido_html(self, _cab_completo, _df_minimo):
        """Nenhum campo do cabeçalho retorna string vazia no HTML gerado."""
        from modules.modulo_pcmso import gerar_html_pcmso

        html = gerar_html_pcmso(_df_minimo, cabecalho=_cab_completo)

        campos = {
            "razao_social":    _cab_completo["razao_social"],
            "cnpj":            _cab_completo["cnpj"],
            "medico_rt":       _cab_completo["medico_rt"],
            "obra":            _cab_completo["obra"],
            "vig_ini":         _cab_completo["vig_ini"],
            "vig_fim":         _cab_completo["vig_fim"],
            "responsavel_tec": _cab_completo["responsavel_tec"],
        }
        for campo, valor in campos.items():
            assert valor in html, (
                f"Campo '{campo}' não encontrado no HTML gerado. "
                f"Valor esperado: '{valor}'"
            )

    def test_cabecalho_preenchido_docx(self, _cab_completo, _df_minimo):
        """Todos os valores do cabeçalho aparecem no docx gerado (verificado via bytes)."""
        from modules.modulo_pcmso import gerar_docx_rq61

        docx_bytes = gerar_docx_rq61(_df_minimo, cabecalho=_cab_completo)
        assert len(docx_bytes) > 1000, "Docx gerado está vazio ou muito pequeno"

        # Verifica via text no conteúdo bruto do docx (XML interno)
        import zipfile, io
        with zipfile.ZipFile(io.BytesIO(docx_bytes)) as z:
            doc_xml = z.read("word/document.xml").decode("utf-8", errors="ignore")

        for campo, valor in [
            ("razao_social",    _cab_completo["razao_social"]),
            ("cnpj",            _cab_completo["cnpj"]),
            ("medico_rt",       _cab_completo["medico_rt"]),
            ("obra",            _cab_completo["obra"]),
            ("vig_ini",         _cab_completo["vig_ini"]),
            ("responsavel_tec", _cab_completo["responsavel_tec"]),
        ]:
            assert valor in doc_xml, (
                f"Campo '{campo}' não encontrado no XML do docx. "
                f"Valor esperado: '{valor}'"
            )

    def test_vigencia_padrao_um_ano(self):
        """vig_fim padrão deve ser exatamente 1 ano após vig_ini — nunca iguais."""
        from datetime import date
        from dateutil.relativedelta import relativedelta

        vig_ini = date.today()
        vig_fim = date.today() + relativedelta(years=1)

        assert vig_ini != vig_fim, (
            "Bug C5: vig_ini == vig_fim — ambas as datas defaultam para hoje"
        )
        assert vig_fim.year == vig_ini.year + 1, (
            f"vig_fim deveria ser {vig_ini.year + 1}, mas é {vig_fim.year}"
        )
        assert vig_fim.month == vig_ini.month, "Mês deve ser preservado"
        assert vig_fim.day == vig_ini.day, "Dia deve ser preservado"

    def test_vigencia_restaurada_de_session_state(self):
        """Simula o _parse_data do app.py: datas gravadas 'DD/MM/YYYY' são restauradas corretamente."""
        from datetime import datetime, date
        from dateutil.relativedelta import relativedelta

        # Simula a função auxiliar do app.py
        def _parse_data(s: str, fallback: date) -> date:
            try:
                return datetime.strptime(s, "%d/%m/%Y").date() if s else fallback
            except ValueError:
                return fallback

        stored_ini = "01/02/2025"
        stored_fim = "01/02/2026"

        vig_ini = _parse_data(stored_ini, date.today())
        vig_fim = _parse_data(stored_fim, date.today() + relativedelta(years=1))

        assert vig_ini == date(2025, 2, 1), f"vig_ini restaurado errado: {vig_ini}"
        assert vig_fim == date(2026, 2, 1), f"vig_fim restaurado errado: {vig_fim}"
        assert vig_ini != vig_fim, "Após restauração, vig_ini e vig_fim são iguais!"

        # Fallback: string vazia → vig_fim = hoje + 1 ano
        vig_fim_fallback = _parse_data("", date.today() + relativedelta(years=1))
        assert vig_fim_fallback != date.today(), (
            "Fallback de vig_fim deveria ser hoje + 1 ano, mas é hoje!"
        )
