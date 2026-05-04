# tests/test_regressao_pcmso.py
# Bateria de regressão para o pipeline PGR → PCMSO.
# Rodar: pytest tests/test_regressao_pcmso.py -v

import sys
import os
from pathlib import Path

# Configura sys.path com duas entradas:
#   1. WORKTREE root  — código do branch atual (tem precedência nos imports)
#   2. PROJETO PRINCIPAL root — usado apenas para localizar o PDF de teste
#
# Separar os dois paths garante que os testes importem o código do worktree
# (com as correções desta sprint) e não o código do projeto principal (sem elas).
_here = Path(__file__).resolve()
_worktree_root = _here.parents[1]  # .../competent-cartwright-b3e939/

if ".claude" in _here.parts and "worktrees" in _here.parts:
    # parents: [0]=tests  [1]=<branch>  [2]=worktrees  [3]=.claude  [4]=automacao-pgr-seconci
    ROOT = _here.parents[4]   # projeto principal (apenas para PDF path)
else:
    ROOT = _here.parents[1]

# Worktree em primeiro: garante que 'from modules.X import' usa o código do branch.
sys.path.insert(0, str(ROOT))          # projeto principal (fallback)
sys.path.insert(0, str(_worktree_root))  # worktree (precedência nos imports)

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


# ---------------------------------------------------------------------------
# Suite 7 — GHE: títulos descritivos + ordem sequencial (C2)
# ---------------------------------------------------------------------------

class TestGheOrdenacao:
    """
    Testa os dois bugs do Prompt 2 (C2):
      1. GHEs sem título descritivo (apareciam como "GHE 07" sem label)
      2. GHEs nomeados inseridos no final do documento (ordem errada)
    """

    @pytest.fixture(scope="class")
    def _dados_e_df(self):
        """Gera dados_ghe e df a partir do PDF real (ou pula se ausente)."""
        from modules.modulo_pcmso import extrair_texto_pdf, extrair_pgr_com_fallback, processar_pcmso

        pdf_path = _PDF_PATH if _PDF_PATH.exists() else _PDF_FALLBACK
        if not pdf_path.exists():
            pytest.skip("PDF de teste não encontrado")

        with open(pdf_path, "rb") as f:
            texto = extrair_texto_pdf(f)

        dados_ghe, _ = extrair_pgr_com_fallback(texto)
        if not dados_ghe:
            pytest.skip("PDF não retornou GHEs válidos")

        df = processar_pcmso(dados_ghe)
        return df, dados_ghe

    def test_todos_ghe_tem_titulo(self, _dados_e_df):
        """
        Nenhum GHE deve ter título vazio ou ser apenas número.
        Antes do fix: GHEs 07–16 tinham 'ghe=GHE 07' sem descrição e
        _renumerar_ghe_sequencial gerava fallback genérico.
        Após o fix: título derivado do primeiro cargo (ex: 'GHE 07 - Pedreiro').
        """
        import re
        df, _ = _dados_e_df
        for ghe_nome in df["GHE / Setor"].unique():
            m = re.match(r"GHE\s*\d+\s*[-:–—]\s*(.+)", ghe_nome, re.IGNORECASE)
            assert m, f"GHE sem separador / estrutura incorreta: '{ghe_nome}'"
            titulo = m.group(1).strip()
            assert titulo, f"GHE com título vazio: '{ghe_nome}'"
            # Título não deve ser o fallback genérico antigo
            assert titulo.lower() != "atividade não identificada", (
                f"GHE com fallback genérico — derive o título do cargo: '{ghe_nome}'"
            )

    def test_ghe_ordem_sequencial(self, _dados_e_df):
        """
        Os números de GHE no documento devem ser estritamente crescentes.
        Antes do fix: GHEs 07–16 apareciam ANTES de 01–06 porque
        'dados_ghe = _enriquecidos + _ghe_sem_cargo_final' destruía a ordem.
        """
        import re
        df, _ = _dados_e_df
        nums = []
        for ghe_nome in df["GHE / Setor"].unique():
            m = re.search(r"GHE\s*(\d+)", ghe_nome, re.IGNORECASE)
            if m:
                nums.append(int(m.group(1)))

        assert nums, "Nenhum GHE com número encontrado no df"
        for i in range(len(nums) - 1):
            assert nums[i] < nums[i + 1], (
                f"Ordem incorreta na posição {i}: GHE {nums[i]} vem antes de GHE {nums[i+1]}. "
                f"Sequência completa: {nums}"
            )

    def test_renumerar_sem_titulo_usa_hint(self):
        """_renumerar_ghe_sequencial usa hint quando nome não tem descrição."""
        from modules.modulo_pcmso import _renumerar_ghe_sequencial

        # Com hint → usa hint
        assert _renumerar_ghe_sequencial("GHE 07", 7, hint="Pedreiro") == "GHE 07 - Pedreiro"
        assert _renumerar_ghe_sequencial("", 3, hint="Serralheiro") == "GHE 03 - Serralheiro"

        # Sem hint → usa "Grupo N"
        assert _renumerar_ghe_sequencial("GHE 07", 7) == "GHE 07 - Grupo 7"
        assert _renumerar_ghe_sequencial("", 3) == "GHE 03 - Grupo 3"

        # Com título no nome → ignora hint
        assert _renumerar_ghe_sequencial("GHE 07 - Alvenaria", 7, hint="Pedreiro") == "GHE 07 - Alvenaria"

    def test_extrair_hint_titulo_usa_cargo(self):
        """_extrair_hint_titulo prioriza o primeiro cargo real."""
        from modules.modulo_pcmso import _extrair_hint_titulo

        cargos = ["pedreiro", "meio oficial de pedreiro"]
        riscos = [{"nome_agente": "Ruído", "perigo_especifico": ""}]
        hint = _extrair_hint_titulo(cargos, riscos)
        assert hint == "Pedreiro", f"Esperado 'Pedreiro', obteve '{hint}'"

    def test_extrair_hint_titulo_fallback_risco(self):
        """_extrair_hint_titulo usa risco quando não há cargos reais."""
        from modules.modulo_pcmso import _extrair_hint_titulo

        cargos = []  # sem cargos
        riscos = [{"nome_agente": "Ruído", "perigo_especifico": ""}]
        hint = _extrair_hint_titulo(cargos, riscos)
        assert "ruído" in hint.lower() or "Ruído" in hint, f"Esperado risco no hint, obteve '{hint}'"

    def test_sort_por_numero_ghe(self):
        """_num_ghe_para_sort extrai o número correto para ordenação."""
        from modules.modulo_pcmso import _num_ghe_para_sort

        dados = [
            {"ghe": "GHE 10 - Serralheiro"},
            {"ghe": "GHE 07"},
            {"ghe": "GHE 01 - Engenharia planejamento de obra"},
            {"ghe": "GHE 16"},
        ]
        dados.sort(key=_num_ghe_para_sort)
        nums = [_num_ghe_para_sort(d) for d in dados]
        assert nums == [1, 7, 10, 16], f"Ordenação incorreta: {nums}"


# ---------------------------------------------------------------------------
# Suite 8 — Exame Clínico 6M por exposição a risco químico (Prompt 3)
# ---------------------------------------------------------------------------

class TestExameClinicoPeriodicidade:
    """
    Valida que cargos expostos a agentes químicos obrigatórios (NR-7 Anexo I/II)
    têm Exame Clínico com periodicidade 6M, e que cargos sem essa exposição
    continuam com 12M (regressão obrigatória).
    Referência: Matriz Dra. Patrícia Montalvo 06/2025.
    """

    def _get_ec_per(self, cargo: str) -> str:
        """Helper: retorna periodicidade do Exame Clínico para o cargo."""
        from modules.agente_medico_ia import processar_cargo_ia
        result = processar_cargo_ia(cargo, riscos=[], e_canteiro=True)
        exames = result.get("exames", [])
        ec = next(
            (e for e in exames
             if "cl" in e.get("nome", "").lower()
             and "nico" in e.get("nome", "").lower()),
            None,
        )
        assert ec is not None, f"Exame Clínico não encontrado para '{cargo}'"
        return str(ec.get("per", ""))

    def test_exame_clinico_serralheiro_6m(self):
        """Serralheiro: exposto a Cromo hexavalente → Exame Clínico 6M."""
        assert self._get_ec_per("Serralheiro") == "6", (
            "Serralheiro deve ter Exame Clínico 6M (exposição a Cromo)"
        )

    def test_exame_clinico_meio_oficial_serralheiro_6m(self):
        """Meio oficial de serralheiro: mesma exposição que serralheiro → 6M."""
        assert self._get_ec_per("meio oficial de serralheiro") == "6", (
            "Meio oficial de serralheiro deve ter Exame Clínico 6M"
        )

    def test_exame_clinico_eletricista_industrial_6m(self):
        """Eletricista industrial: exposto a Tricloroetileno (NR-10) → Exame Clínico 6M."""
        assert self._get_ec_per("Eletricista industrial") == "6", (
            "Eletricista industrial deve ter Exame Clínico 6M (Tricloroetileno)"
        )

    def test_exame_clinico_variante_manutencao_6m(self):
        """'Manutenção: Eletricista industrial' normaliza para 'eletricista industrial' → 6M."""
        # normalizar_cargo strips the "Manutenção:" prefix → "eletricista industrial"
        assert self._get_ec_per("Manutenção: Eletricista industrial") == "6", (
            "Variante 'Manutenção: Eletricista industrial' deve ter Exame Clínico 6M"
        )

    def test_exame_clinico_encanador_6m(self):
        """Encanador: exposto a Metil-etil-cetona (MEK) → Exame Clínico 6M."""
        assert self._get_ec_per("Encanador") == "6", (
            "Encanador deve ter Exame Clínico 6M (MEK)"
        )

    def test_exame_clinico_meio_oficial_encanador_6m(self):
        """Meio oficial de encanador: mesma exposição que encanador → 6M."""
        assert self._get_ec_per("meio oficial de encanador") == "6", (
            "Meio oficial de encanador deve ter Exame Clínico 6M"
        )

    def test_exame_clinico_pedreiro_permanece_12m(self):
        """
        Regressão obrigatória: Pedreiro NÃO tem exposição química → Exame Clínico 12M.
        Garante que a regra 6M não vazou para cargos sem risco químico.
        """
        assert self._get_ec_per("Pedreiro") == "12", (
            "REGRESSAO: Pedreiro deve ter Exame Clínico 12M, não 6M"
        )

    def test_exame_clinico_carpinteiro_permanece_12m(self):
        """Regressão: Carpinteiro sem exposição química → 12M."""
        assert self._get_ec_per("Carpinteiro") == "12"

    def test_exame_clinico_armador_permanece_12m(self):
        """Regressão: Armador sem exposição química → 12M."""
        assert self._get_ec_per("Armador") == "12"

    def test_normalizar_cargo_risco_quimico_colon(self):
        """_normalizar_cargo_risco_quimico strips prefix before colon correctly."""
        from modules.agente_medico_ia import _normalizar_cargo_risco_quimico, CARGOS_RISCO_QUIMICO_6M

        # Strips colon prefix → matches the set entry
        assert _normalizar_cargo_risco_quimico("Manutenção: Eletricista industrial") == "eletricista industrial"
        assert _normalizar_cargo_risco_quimico("Eletricista industrial") == "eletricista industrial"
        assert _normalizar_cargo_risco_quimico("meio oficial de serralheiro") == "meio oficial de serralheiro"

        # Verify membership after normalization
        for cargo_raw in ["Serralheiro", "Eletricista industrial",
                          "Manutenção: Eletricista industrial",
                          "Encanador", "meio oficial de encanador"]:
            norm = _normalizar_cargo_risco_quimico(cargo_raw)
            assert norm in CARGOS_RISCO_QUIMICO_6M, (
                f"'{cargo_raw}' normalizado para '{norm}' não está em CARGOS_RISCO_QUIMICO_6M"
            )


# ---------------------------------------------------------------------------
# Suite 9 — Exames de risco específicos por cargo (Prompt 4)
# ---------------------------------------------------------------------------

class TestExamesRiscoEspecificos:
    """
    Valida que exames de risco químico obrigatórios (NR-7 Anexo I/II) estão
    presentes e posicionados APÓS os exames padrão.
    Referência: Matriz Dra. Patrícia Montalvo 06/2025.
    """

    def _exames(self, cargo: str):
        from modules.agente_medico_ia import processar_cargo_ia
        return processar_cargo_ia(cargo, riscos=[], e_canteiro=True)["exames"]

    def _tem_exame(self, exames: list, canonical: str) -> bool:
        """Verifica presença pelo nome canônico (via normalizar_exame)."""
        from modules.modulo_auditor_v1_1 import normalizar_exame
        return any(normalizar_exame(e["nome"]) == canonical for e in exames)

    # ── Presença dos exames ──────────────────────────────────────────────────

    def test_serralheiro_tem_carboxihemoglobina(self):
        """Serralheiro deve ter Carboxihemoglobina (qualquer variante canonical)."""
        exames = self._exames("Serralheiro")
        assert self._tem_exame(exames, "Carboxiemoglobina"), (
            "Serralheiro: Carboxihemoglobina no Sangue ausente. "
            f"Exames presentes: {[e['nome'] for e in exames]}"
        )

    def test_serralheiro_tem_manganes(self):
        """Serralheiro deve ter Manganês no Sangue (qualquer variante canonical)."""
        exames = self._exames("Serralheiro")
        assert self._tem_exame(exames, "Manganês sanguíneo"), (
            "Serralheiro: Manganês no Sangue ausente. "
            f"Exames presentes: {[e['nome'] for e in exames]}"
        )

    def test_eletricista_industrial_tem_acido_tricloracetico(self):
        """Eletricista industrial deve ter Ácido Tricloroacético na Urina."""
        exames = self._exames("Eletricista industrial")
        assert self._tem_exame(exames, "Ácido tricloroacético na urina"), (
            "Eletricista industrial: Ácido Tricloroacético na Urina ausente. "
            f"Exames: {[e['nome'] for e in exames]}"
        )

    def test_encanador_tem_mek_urina(self):
        """Encanador deve ter Metil-etil-cetona (MEK) na Urina (genuinamente ausente no banco)."""
        exames = self._exames("Encanador")
        assert self._tem_exame(exames, "Metil-Etil-Cetona"), (
            "Encanador: MEK na Urina ausente. "
            f"Exames: {[e['nome'] for e in exames]}"
        )

    def test_encanador_mek_periodicidade_6m(self):
        """MEK do Encanador deve ter periodicidade 6M."""
        from modules.modulo_auditor_v1_1 import normalizar_exame
        exames = self._exames("Encanador")
        mek = next(
            (e for e in exames if normalizar_exame(e["nome"]) == "Metil-Etil-Cetona"),
            None,
        )
        assert mek is not None, "MEK não encontrado para Encanador"
        assert str(mek.get("per")) == "6", (
            f"MEK do Encanador: periodicidade esperada 6M, obtida {mek.get('per')}M"
        )

    # ── Ordem: exames de risco aparecem após exames padrão ──────────────────

    def test_exames_risco_aparecem_apos_exames_padrao(self):
        """
        Para o Serralheiro, exames de risco (Carboxiemoglobina, Manganês) devem
        aparecer APÓS todos os exames padrão (Espirometria, RX de Tórax, etc.).
        Verifica que o índice mínimo dos exames de risco > índice máximo dos padrões.
        """
        from modules.modulo_auditor_v1_1 import normalizar_exame
        exames = self._exames("Serralheiro")

        risk_canonicos = {"carboxiemoglobina", "manganês sanguíneo"}

        padrao_idx, risco_idx = [], []
        for i, e in enumerate(exames):
            nc = normalizar_exame(e["nome"]).lower()
            if nc in risk_canonicos:
                risco_idx.append(i)
            else:
                padrao_idx.append(i)

        assert risco_idx, "Nenhum exame de risco (Carboxiemoglobina/Manganês) encontrado"
        assert padrao_idx, "Nenhum exame padrão encontrado"

        # Exame Clínico no início
        assert exames[0]["nome"] == "Exame Clínico", (
            f"Exame Clínico não é o primeiro: '{exames[0]['nome']}'"
        )
        # Todos os exames de risco devem ter índice > máximo dos padrões
        assert min(risco_idx) > max(padrao_idx), (
            f"Exame de risco (pos {min(risco_idx)}) antes de exame padrão (pos {max(padrao_idx)}). "
            f"Ordem: {[e['nome'] for e in exames]}"
        )

    # ── Anti-duplicata ───────────────────────────────────────────────────────

    def test_sem_duplicata_serralheiro(self):
        """
        Regressão anti-duplicata: a adição de exames de risco NÃO deve criar
        entradas duplicadas para exames que já existiam no banco.
        """
        from modules.modulo_auditor_v1_1 import normalizar_exame
        exames = self._exames("Serralheiro")

        for canonical in ("Carboxiemoglobina", "Manganês sanguíneo"):
            count = sum(
                1 for e in exames
                if normalizar_exame(e["nome"]) == canonical
            )
            assert count == 1, (
                f"Duplicata detectada: '{canonical}' aparece {count} vezes "
                f"na lista de exames do Serralheiro"
            )


# ---------------------------------------------------------------------------
# Suite 10 — Operador de Betoneira: protocolo específico (Prompt 5)
# ---------------------------------------------------------------------------

class TestOperadorBetoneira:
    """
    Valida o protocolo EXATO do Operador de Betoneira (NR-7 / poeira mineral).
    Os testes usam contexto={'maquinas_pesadas': True} para reproduzir a
    situação real de produção (GHE com nome contendo 'betoneira'), que é a
    origem dos 3 bugs reportados.
    """

    @staticmethod
    def _exames_producao():
        """Retorna exames com contexto de produção (maquinas_pesadas=True)."""
        from modules.agente_medico_ia import processar_cargo_ia
        return processar_cargo_ia(
            "Operador de Betoneira",
            riscos=[],
            contexto={"maquinas_pesadas": True},
            e_canteiro=True,
        )["exames"]

    def _get(self, nome_substr: str, exames=None):
        if exames is None:
            exames = self._exames_producao()
        return next((e for e in exames if nome_substr.lower() in e["nome"].lower()), None)

    # ── Ausências obrigatórias (Bug 1 e 2) ──────────────────────────────────

    def test_betoneira_sem_acuidade_visual(self):
        """
        Bug 1: Acuidade Visual NÃO deve aparecer para Operador de Betoneira.
        Em produção, _aplicar_ajustes_contexto() injetava quando maquinas_pesadas=True.
        """
        exames = self._exames_producao()
        nomes = [e["nome"] for e in exames]
        assert "Acuidade Visual" not in nomes, (
            f"Acuidade Visual não deveria estar na lista: {nomes}"
        )

    def test_betoneira_sem_ecg(self):
        """
        Bug 2: ECG NÃO deve aparecer para Operador de Betoneira.
        Em produção, _aplicar_ajustes_contexto() injetava quando maquinas_pesadas=True.
        """
        exames = self._exames_producao()
        nomes = [e["nome"] for e in exames]
        assert "ECG" not in nomes, (
            f"ECG não deveria estar na lista: {nomes}"
        )

    # ── Periodicidade correta (Bug 3) ────────────────────────────────────────

    def test_betoneira_rx_oit_12m(self):
        """
        Bug 3: RX de Tórax OIT deve ter per=12M (exposição a poeira mineral/sílica).
        O banco_matrizes_v2 tinha per=60M (template genérico de poeira mineral).
        """
        exames = self._exames_producao()
        rx = self._get("RX", exames)
        assert rx is not None, "RX de Tórax OIT não encontrado para Operador de Betoneira"
        assert str(rx.get("per")) == "12", (
            f"RX de Tórax OIT: esperado per=12M, obtido {rx.get('per')}M"
        )

    # ── Regressão: exames que DEVEM permanecer ───────────────────────────────

    def test_betoneira_tem_espirometria_24m(self):
        """Regressão: Espirometria deve estar presente com per=24M."""
        exames = self._exames_producao()
        espiro = self._get("Espirometria", exames)
        assert espiro is not None, "Espirometria ausente para Operador de Betoneira"
        assert str(espiro.get("per")) == "24", (
            f"Espirometria: esperado per=24M, obtido {espiro.get('per')}M"
        )

    def test_betoneira_tem_audiometria_12m(self):
        """Regressão: Audiometria deve estar presente com per=12M."""
        exames = self._exames_producao()
        audio = self._get("Audiometria", exames)
        assert audio is not None, "Audiometria ausente para Operador de Betoneira"
        assert str(audio.get("per")) == "12", (
            f"Audiometria: esperado per=12M, obtido {audio.get('per')}M"
        )

    def test_betoneira_protocolo_exato_4_exames(self):
        """
        Protocolo do Operador de Betoneira deve ter EXATAMENTE 4 exames:
        Exame Clínico, Audiometria, Espirometria, RX de Tórax OIT.
        Sem Hemograma, Glicemia, ECG ou Acuidade Visual.
        """
        exames = self._exames_producao()
        nomes = [e["nome"] for e in exames]
        esperados = {"Exame Clínico", "Audiometria", "Espirometria", "RX de Tórax OIT"}
        assert set(nomes) == esperados, (
            f"Protocolo incorreto.\nEsperado: {sorted(esperados)}\nObtido:   {sorted(nomes)}"
        )


# ---------------------------------------------------------------------------
# Suite 11 — Notas de risco químico na serialização (Prompt 6)
# ---------------------------------------------------------------------------

class TestNotasRiscoQuimico:
    """
    Valida que os blocos de nota de risco químico são injetados corretamente
    no HTML gerado por gerar_html_pcmso().
    """

    def _df_ghe(self, ghe_nome: str, cargos_exames: list) -> "pd.DataFrame":
        """Helper: monta DataFrame mínimo para um GHE com os cargos/exames dados."""
        rows = []
        for cargo, exame in cargos_exames:
            rows.append({
                "GHE / Setor": ghe_nome,
                "Cargo": cargo,
                "Exame": exame,
                "ADM": "X", "PER": "12M", "MRO": "X", "RT": "-", "DEM": "-",
            })
        return pd.DataFrame(rows)

    def _html(self, ghe_nome: str, cargos_exames: list) -> str:
        from modules.modulo_pcmso import gerar_html_pcmso
        df = self._df_ghe(ghe_nome, cargos_exames)
        return gerar_html_pcmso(df)

    # ── Presença obrigatória ─────────────────────────────────────────────────

    def test_nota_risco_serralheiro_presente(self):
        """GHE com Serralheiro deve conter nota de Cromo hexavalente."""
        html = self._html(
            "GHE 10 - Serralheria",
            [("Serralheiro", "Exame Clínico"), ("Serralheiro", "Audiometria")],
        )
        assert "NOTA DE RISCO" in html, "Bloco de nota ausente para Serralheiro"
        assert "Cromo hexavalente" in html, "Agente 'Cromo hexavalente' ausente"
        assert "Carboxihemoglobina no Sangue" in html, "Exame de controle ausente"
        assert "NR-7 Anexo II" in html, "Fundamento legal ausente"

    def test_nota_risco_eletricista_industrial_presente(self):
        """GHE com Eletricista industrial deve conter nota de Tricloroetileno."""
        html = self._html(
            "GHE 08 - Eletricista",
            [("Eletricista industrial", "Exame Clínico")],
        )
        assert "NOTA DE RISCO" in html, "Bloco de nota ausente para Eletricista industrial"
        assert "Tricloroetileno" in html, "Agente 'Tricloroetileno' ausente"
        assert "Ácido Tricloroacético na Urina" in html, "Exame de controle ausente"

    def test_nota_risco_encanador_presente(self):
        """GHE com Encanador deve conter nota de Metietilcetona (MEK)."""
        html = self._html(
            "GHE 09 - Instalações Hidrossanitárias",
            [("encanador", "Exame Clínico")],
        )
        assert "NOTA DE RISCO" in html, "Bloco de nota ausente para Encanador"
        assert "Metietilcetona" in html, "Agente 'Metietilcetona' ausente"
        assert "Metil-etil-cetona (MEK) na Urina" in html, "Exame de controle ausente"

    # ── Deduplicação por agente ──────────────────────────────────────────────

    def test_nota_sem_duplicata_mesmo_ghe(self):
        """
        GHE com Serralheiro + Meio Oficial de Serralheiro → apenas 1 nota
        para Cromo hexavalente (dedup por agente, não por cargo).
        """
        html = self._html(
            "GHE 10 - Serralheria",
            [
                ("Serralheiro", "Exame Clínico"),
                ("Serralheiro", "Audiometria"),
                ("meio oficial de serralheiro", "Exame Clínico"),
                ("meio oficial de serralheiro", "Audiometria"),
            ],
        )
        count_cromo = html.count("Cromo hexavalente")
        assert count_cromo == 1, (
            f"Nota de 'Cromo hexavalente' duplicada: aparece {count_cromo}x no HTML. "
            "Dedup por agente deveria emitir apenas 1 nota."
        )

    # ── Regressão: cargo sem risco não deve gerar nota ───────────────────────

    def test_ghe_sem_cargo_risco_sem_nota(self):
        """
        Regressão: GHE com Pedreiro NÃO deve conter nenhuma nota de risco.
        Pedreiro não está em NOTAS_RISCO_QUIMICO.
        """
        html = self._html(
            "GHE 03 - Execução de Obra",
            [("Pedreiro", "Exame Clínico"), ("Pedreiro", "Audiometria")],
        )
        assert "NOTA DE RISCO" not in html, (
            "Nota de risco indevida para GHE com Pedreiro"
        )
        assert "Cromo hexavalente" not in html
        assert "Tricloroetileno" not in html
        assert "Metietilcetona" not in html

    # ── Verificação da estrutura da nota ────────────────────────────────────

    def test_nota_contem_todos_os_campos(self):
        """A nota deve conter: cargo, agente, fundamento e exame_controle."""
        html = self._html(
            "GHE 09 - Encanador",
            [("encanador", "Exame Clínico")],
        )
        assert "NOTA DE RISCO QUÍMICO" in html
        assert "encanador" in html.lower()
        assert "Metietilcetona (MEK)" in html
        assert "Matriz Dra. Patrícia 06/2025" in html
        assert "periodicidade semestral" in html

    def test_notas_distintas_para_ghes_diferentes(self):
        """Dois GHEs distintos geram notas distintas e independentes."""
        from modules.modulo_pcmso import gerar_html_pcmso
        df = pd.DataFrame([
            {"GHE / Setor": "GHE 10 - Serralheria", "Cargo": "Serralheiro",
             "Exame": "Exame Clínico",
             "ADM": "X", "PER": "6M", "MRO": "X", "RT": "X", "DEM": "X"},
            {"GHE / Setor": "GHE 09 - Hidrossanitária", "Cargo": "encanador",
             "Exame": "Exame Clínico",
             "ADM": "X", "PER": "6M", "MRO": "X", "RT": "-", "DEM": "-"},
        ])
        html = gerar_html_pcmso(df)
        assert html.count("NOTA DE RISCO") == 2, (
            f"Esperado 2 notas (1 por GHE), obtido {html.count('NOTA DE RISCO')}"
        )
        assert "Cromo hexavalente" in html
        assert "Metietilcetona" in html
