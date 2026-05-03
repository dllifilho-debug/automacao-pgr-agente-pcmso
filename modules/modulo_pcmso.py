# =============================================================================
# MÓDULO PCMSO v9.6 — Motor completo com Agente Médico IA v2.2
# Novidades v9.6:
#   FIX CRÍTICO _distribuir_cargos_por_ghe:
#     - quando _tipo_do_ghe() retorna None (GHE sem keyword reconhecida),
#       em vez de copiar TODOS os 23 cargos para aquele GHE, tenta inferir
#       os cargos relevantes a partir dos riscos mapeados no próprio bloco.
#     - Se riscos também não ajudam, usa a lista completa (comportamento
#       anterior) mas só como último recurso — agora logado explicitamente.
#     - Adiciona _RISCOS_PARA_TIPOS: mapa de palavras no risco → tipos de GHE
#       para enriquecer a inferência de tipo sem depender apenas do nome do GHE.
# Novidades v9.5:
#   FIX gerar_docx_rq61: células GHE/Cargo mergeadas verticalmente por bloco
#   FIX gerar_html_pcmso: rowspan correto em GHE e Cargo (sem repetição)
#   Formato final idêntico ao modelo de referência (PDF VIVERDE)
# Novidades v9.4:
#   FIX CRÍTICO: ghe_nome passado para processar_cargo_ia() — Camada 0 ativada
#   FIX: auditoria_nr7 exibida em expander por GHE no app
#   UPD: versão referenciada atualizada para AgenteMedicoIA v2.2
# Novidades v9.3:
#   Remove bloco DEBUG v9.2 de _parsear_pgr_local após validação
#   da distribuição inteligente de cargos por GHE (PDF Viverde confirmado).
# Novidades v9.2:
#   FIX _distribuir_cargos_por_ghe: verificava bloco.get("cargos") antes de
#   distribuir — mas blocos vindos do parser_pgr chegam com cargos=["GHE 01-..."],
#   que é truthy → pulava todos os blocos → 1 cargo/GHE (o nome do GHE).
#   Agora verifica se os cargos são REAIS (não nomes de GHE) antes de pular.
# =============================================================================

import io
import os
import re
import unicodedata
from copy import deepcopy
from datetime import date

import pandas as pd

VERSAO_MODULO_PCMSO = "9.6 (AgenteMedicoIA v2.2 + distribuição inteligente por risco)"

# ---------------------------------------------------------------------------
# Import do Agente Médico IA v2.0
# ---------------------------------------------------------------------------
try:
    from modules.agente_medico_ia import (
        processar_cargo_ia,
        resolver_chave_mestra as _resolver_chave,
        auditar_pcmso,
        relatorio_qualidade_pgr,
        gerar_justificativa_ghe,
        enriquecer_contexto_por_riscos,
        carregar_cargos_desconhecidos,
    )
    _AGENTE_IA_DISPONIVEL = True
except ImportError:
    try:
        from agente_medico_ia import (
            processar_cargo_ia,
            resolver_chave_mestra as _resolver_chave,
            auditar_pcmso,
            relatorio_qualidade_pgr,
            gerar_justificativa_ghe,
            enriquecer_contexto_por_riscos,
            carregar_cargos_desconhecidos,
        )
        _AGENTE_IA_DISPONIVEL = True
    except ImportError:
        _AGENTE_IA_DISPONIVEL = False
        _resolver_chave = None
        auditar_pcmso = None
        relatorio_qualidade_pgr = None
        gerar_justificativa_ghe = None
        enriquecer_contexto_por_riscos = None
        carregar_cargos_desconhecidos = None

try:
    from data.dicionario_cas import DICIONARIO_CAS
except ImportError:
    DICIONARIO_CAS = {}

# Importa normalizar_cargo (Prompt 1) para deduplicação intra-GHE
try:
    from modules.modulo_auditor_v1_1 import normalizar_cargo as _normalizar_cargo_aud
except ImportError:
    try:
        from modulo_auditor_v1_1 import normalizar_cargo as _normalizar_cargo_aud
    except ImportError:
        _normalizar_cargo_aud = None


# ============================================================================
# 1 — EXTRAÇÃO DE TEXTO DO PDF
# ============================================================================

_MIN_CHARS_POR_PAGINA = 150

_ASSINATURA_KEYWORDS = [
    "autenticação eletrônica", "autenticacao eletronica",
    "página de assinaturas", "pagina de assinaturas",
    "hash sha256", "identificador:", "clicksign", "docusign",
    "signatário", "signatario", "escaneie a imagem para verificar",
]


def _texto_esta_vazio(texto: str, num_paginas: int) -> bool:
    if not texto or not texto.strip():
        return True
    return (len(texto) / max(num_paginas, 1)) < _MIN_CHARS_POR_PAGINA


def _e_pagina_assinatura(texto_pagina: str) -> bool:
    if not texto_pagina:
        return False
    t = texto_pagina.lower()
    return any(kw in t for kw in _ASSINATURA_KEYWORDS)


def _extrair_ocr(data: bytes, num_paginas_total: int = 0) -> str:
    texto = ""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError as e:
        return f"[OCR indisponivel: {e}]"

    dpi = 200 if num_paginas_total > 50 else 250
    try:
        paginas = convert_from_bytes(data, dpi=dpi)
    except Exception as e:
        return f"[OCR: falha na conversao de paginas: {e}]"

    total = len(paginas)
    paginas_processar = paginas
    if total > 1:
        try:
            import pytesseract
            ultima_texto = pytesseract.image_to_string(paginas[-1], lang="por+eng", config="--psm 6 --oem 3")
            if _e_pagina_assinatura(ultima_texto):
                paginas_processar = paginas[:-1]
                total = len(paginas_processar)
        except Exception:
            pass

    config_tess = "--psm 6 --oem 3"
    _progress_bar = None
    _status_ctx = None
    try:
        import streamlit as st
        _status_ctx = st.status(f"🔍 OCR em andamento — {total} páginas (DPI={dpi})...", expanded=False)
        _status_ctx.__enter__()
        _progress_bar = st.progress(0, text="Iniciando OCR...")
    except Exception:
        pass

    _cv2_ok = False
    try:
        import cv2
        _cv2_ok = True
    except ImportError:
        pass

    for i, img in enumerate(paginas_processar):
        try:
            if _cv2_ok:
                import numpy as np
                from PIL import Image
                img_array = np.array(img.convert("RGB"))
                cinza = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                _, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                img_proc = Image.fromarray(binaria)
            else:
                img_proc = img
            t = pytesseract.image_to_string(img_proc, lang="por+eng", config=config_tess)
            if t and t.strip():
                texto += t + "\n"
        except Exception:
            try:
                t = pytesseract.image_to_string(img, lang="por+eng", config=config_tess)
                texto += (t or "") + "\n"
            except Exception:
                pass
        if _progress_bar is not None:
            try:
                _progress_bar.progress(int((i + 1) / total * 100), text=f"OCR: página {i + 1}/{total}")
            except Exception:
                pass

    if _status_ctx is not None:
        try:
            _progress_bar.progress(100, text="OCR concluído ✅")
            _status_ctx.__exit__(None, None, None)
        except Exception:
            pass

    return texto


def extrair_texto_pdf(pdf_file) -> str:
    if hasattr(pdf_file, "read"):
        pdf_file.seek(0)
        data = pdf_file.read()
    else:
        data = bytes(pdf_file)

    num_paginas = 1
    texto = ""

    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(data)) as pdf:
            num_paginas = max(len(pdf.pages), 1)
            for page in pdf.pages:
                t = page.extract_text()
                if t:
                    texto += t + "\n"
        if not _texto_esta_vazio(texto, num_paginas):
            return texto
    except Exception:
        pass

    texto_fitz = ""
    try:
        import fitz
        doc = fitz.open(stream=data, filetype="pdf")
        num_paginas = max(len(doc), 1)
        for page in doc:
            t = page.get_text()
            if t:
                texto_fitz += t + "\n"
        if not _texto_esta_vazio(texto_fitz, num_paginas):
            return texto_fitz
    except Exception:
        pass

    texto_ocr = _extrair_ocr(data, num_paginas_total=num_paginas)
    return texto_ocr if texto_ocr.strip() else (texto or texto_fitz or "")


# ============================================================================
# 2 — PARSER LOCAL DE PGR (v9.6)
# ============================================================================

def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return nfkd.encode("ASCII", "ignore").decode("ASCII").lower().strip()


# ---------------------------------------------------------------------------
# Mapa de tipos de GHE: palavras-chave no nome do GHE → tipo
# ---------------------------------------------------------------------------
_TIPOS_GHE_KW = {
    "engenharia":    ["engenharia", "planejamento", "projeto", "coordenacao", "direcao", "gerencia"],
    "seguranca":     ["seguranca", "sst", "prevencao"],
    "execucao":      ["execucao", "obra", "operacao", "estrutura", "alvenaria",
                      "fundacao", "construcao", "canteiro", "servicos"],
    "supervisao":    ["supervisao", "rejunte", "limpeza", "acabamento", "pintura", "revestimento"],
    "administracao": ["administracao", "campo", "gestao", "administrativo", "apoio"],
    "almoxarifado":  ["almoxarifado", "deposito", "estoque", "material"],
}

# ---------------------------------------------------------------------------
# v9.6 — Mapa de riscos → tipos de GHE (para inferência quando nome do GHE
# não contém keywords conhecidas)
# ---------------------------------------------------------------------------
_RISCOS_PARA_TIPOS = {
    "ruido":            {"execucao", "supervisao", "almoxarifado"},
    "vibracao":         {"execucao"},
    "altura":           {"execucao", "supervisao"},
    "confinado":        {"execucao"},
    "eletric":          {"execucao", "seguranca"},
    "quimico":          {"execucao", "supervisao"},
    "poeira":           {"execucao", "supervisao", "almoxarifado"},
    "solda":            {"execucao"},
    "tinta":            {"execucao", "supervisao"},
    "ergon":            {"execucao", "administracao", "almoxarifado"},
    "psicossocial":     {"administracao", "seguranca", "engenharia"},
    "biologico":        {"execucao"},
}

# ---------------------------------------------------------------------------
# Mapa de cargos: palavras-chave no NOME DO CARGO → tipos de GHE que aceitam
# ---------------------------------------------------------------------------
_CARGO_TIPOS = [
    (["engenheiro"],                                                      {"engenharia"}),
    (["tecnico de seguranca", "tecnico seguranca", " tst"],               {"engenharia", "seguranca"}),
    (["estagiario", "estagiaria"],                                        {"engenharia", "seguranca"}),
    (["mestre"],                                                          {"administracao"}),
    (["aux adm", "auxiliar adm", "assistente adm",
      "assistente administrativo", "administrativo"],                     {"administracao"}),
    (["porteiro", "vigia"],                                               {"administracao"}),
    (["aprendiz"],                                                        {"administracao"}),
    (["almoxarife"],                                                       {"almoxarifado"}),
    (["pintor"],                                                          {"supervisao", "execucao"}),
    (["gesseiro"],                                                        {"supervisao", "execucao"}),
    (["pedreiro"],                                                        {"execucao", "supervisao"}),
    (["servente"],                                                        {"execucao", "supervisao"}),
    (["encarregado", "supervisor de"],                                    {"execucao", "supervisao"}),
    (["azulejista", "assentador de ceramica"],                            {"execucao", "supervisao"}),
    (["carpinteiro"],                                                     {"execucao"}),
    (["eletricista"],                                                     {"execucao"}),
    (["armador"],                                                         {"execucao"}),
    (["encanador"],                                                       {"execucao"}),
    (["serralheiro"],                                                     {"execucao"}),
    (["impermeabilizador"],                                               {"execucao"}),
    (["operador"],                                                        {"execucao"}),
    (["sinaleiro"],                                                       {"execucao"}),
    (["motorista"],                                                       {"execucao"}),
    (["mecanico"],                                                        {"execucao"}),
    (["soldador"],                                                        {"execucao"}),
    (["calceteiro", "topografo"],                                         {"execucao"}),
]

# Regex para detectar nomes de GHE usados como cargo falso
_RE_CARGO_EH_GHE = re.compile(r'^GHE\s*\d+', re.IGNORECASE)


def _tipos_do_cargo(cargo: str) -> set:
    cn = _normalizar(cargo)
    for keywords, tipos in _CARGO_TIPOS:
        if any(kw in cn for kw in keywords):
            return tipos
    return set()


def _tipo_do_ghe(nome_ghe: str) -> str | None:
    gn = _normalizar(nome_ghe)
    melhor_tipo = None
    melhor_score = 0
    for tipo, kws in _TIPOS_GHE_KW.items():
        score = sum(1 for kw in kws if kw in gn)
        if score > melhor_score:
            melhor_score = score
            melhor_tipo = tipo
    return melhor_tipo if melhor_score > 0 else None


def _tipos_do_ghe_por_riscos(riscos_mapeados: list) -> set:
    """
    v9.6 — Infere tipos de GHE compatíveis a partir dos riscos mapeados no bloco.
    Usado como fallback quando _tipo_do_ghe() retorna None.
    """
    tipos = set()
    for risco in riscos_mapeados:
        if isinstance(risco, dict):
            texto_risco = _normalizar(
                (risco.get("nome_agente") or "") + " " + (risco.get("perigo_especifico") or "")
            )
        else:
            texto_risco = _normalizar(str(risco))
        for kw, tipos_risco in _RISCOS_PARA_TIPOS.items():
            if kw in texto_risco:
                tipos.update(tipos_risco)
    return tipos


# ---------------------------------------------------------------------------
# v9.8 — Mapa SEMÂNTICO CONSERVADOR: apenas associações de ALTA CERTEZA.
#
# REVISÃO: o mapa anterior espalhava 'pedreiro' em GHEs com keywords
# ambíguas como 'estrutura', 'concreto', 'fundacao', 'reboco', 'rejunte',
# 'contrapiso', 'acabamento'. Removidos esses mapeamentos genéricos.
# Mantidas apenas associações 1:1 onde o nome da etapa indica
# inequivocamente um único cargo.
#
# Para GHEs com nomes ambíguos (ex: 'Estrutura de concreto'), prefere-se
# deixar VAZIO e exigir edição manual — em vez de errar com 4 cargos
# falsos. O parser_pgr é a fonte de verdade; este mapa é fallback.
# ---------------------------------------------------------------------------
_GHE_NOME_PARA_CARGO_KEYWORDS = {
    # 1:1 inequívocas (atividade → cargo único)
    "alvenaria":         ["pedreiro"],
    "carpintaria":       ["carpinteiro"],
    "armacao":           ["armador"],
    "ferragem":          ["armador"],
    "pintura":           ["pintor"],
    "gesso":             ["gesseiro"],
    "impermeabilizacao": ["impermeabilizador"],
    "manta asfaltica":   ["impermeabilizador"],
    "ceramica":          ["azulejista"],
    "azulej":            ["azulejista"],
    "eletrica":          ["eletricista"],
    "eletricidade":      ["eletricista"],
    "hidraulica":        ["encanador"],
    "hidrossanitaria":   ["encanador"],
    "encanamento":       ["encanador"],
    "tubulacao":         ["encanador"],
    "serralheria":       ["serralheiro"],
    "solda":             ["soldador"],
    "almoxarifado":      ["almoxarife"],
    "deposito":          ["almoxarife"],
    "estoque":           ["almoxarife"],
    "portaria":          ["porteiro", "vigia"],
    "vigilancia":        ["porteiro", "vigia"],
    "engenharia":        ["engenheiro"],
    "planejamento":      ["engenheiro"],
    "seguranca do trabalho": ["tecnico de seguranca", "tst"],
    "sst":               ["tecnico de seguranca", "tst"],

    # Forma de pilar/laje/viga é trabalho de carpinteiro (madeira para concreto)
    "forma de pilar":    ["carpinteiro"],
    "forma de laje":     ["carpinteiro"],
    "forma de viga":     ["carpinteiro"],
    "execucao forma":    ["carpinteiro"],
    "forma":             ["carpinteiro"],

    # Equipamentos específicos
    "operacao grua":     ["operador de grua", "sinaleiro"],
    "operacao cremalheira": ["operador de cremalheira"],
    "sinalizacao":       ["sinaleiro"],

    # Administrativo (palavra completa, não substring de "administracao de obra")
    "administrativo":    ["administrativo", "assistente", "auxiliar"],

    # NÃO MAPEADOS (ambíguos demais, propagavam 'pedreiro' incorretamente):
    # "estrutura", "concreto", "fundacao", "reboco", "rejunte",
    # "contrapiso", "acabamento", "revestimento", "execucao",
    # "supervisao", "limpeza", "apoio", "servicos gerais",
    # "mestre", "encarregado", "betoneira", "metalica"
}


def _associar_cargos_por_nome_ghe(nome_ghe: str, cargos_globais: list) -> list:
    """
    v9.8 — Cross-match CONSERVADOR: usa apenas a keyword MAIS ESPECÍFICA
    encontrada no nome do GHE (evita misturar cargos de múltiplas keywords
    que poderiam dar falsos positivos).

    Exemplo: GHE "Forma de pilar e laje" → keyword mais específica é
    "forma de pilar" → retorna apenas Carpinteiro.

    Se o nome do GHE não contiver nenhuma keyword conhecida (ou só
    keywords ambíguas removidas do mapa), retorna lista vazia — preferindo
    obrigar revisão manual a inserir cargos errados.
    """
    nome_n = _normalizar(nome_ghe)
    # Ordena por especificidade DECRESCENTE: maior keyword primeiro
    for kw_ghe in sorted(_GHE_NOME_PARA_CARGO_KEYWORDS, key=len, reverse=True):
        if kw_ghe in nome_n:
            kws_cargo = _GHE_NOME_PARA_CARGO_KEYWORDS[kw_ghe]
            cargos_match = []
            for cargo in cargos_globais:
                cargo_n = _normalizar(cargo)
                if any(kw in cargo_n for kw in kws_cargo):
                    cargos_match.append(cargo)
            return cargos_match
    return []


def _distribuir_cargos_por_ghe(cargos_globais: list, blocos: list) -> None:
    """
    v9.7 — Distribui cargos globais (extraídos da seção FUNÇÕES) por GHE com
    lógica em 4 camadas. NUNCA atribui todos os cargos a um GHE como fallback.

    Bug #3 RESOLVIDO: removido o `bloco["cargos"] = list(cargos_globais)` que
    duplicava os 23 cargos em todos os GHEs quando nenhuma camada acertava,
    e removido o fallback equivalente da Camada 2 (tipo do GHE × tipo do cargo).

    Camadas (ordem de prioridade — para na primeira que produzir match):
      1. Cross-match nome do GHE × keywords de cargo (mais específico, novo)
      2. Tipo do GHE pelo nome × tipo do cargo (existente, agora SEM fallback)
      3. Tipo do GHE inferido pelos riscos × tipo do cargo (existente)
      4. Indeterminado: deixa cargos vazios e registra warning para revisão manual
    """
    if not cargos_globais:
        return

    indeterminados = []
    for bloco in blocos:
        cargos_atuais = bloco.get("cargos", [])
        tem_cargos_reais = bool(cargos_atuais) and not all(
            _RE_CARGO_EH_GHE.match(c.strip()) for c in cargos_atuais
        )
        if tem_cargos_reais:
            continue
        bloco["cargos"] = []
        nome_ghe = bloco.get("ghe", "")

        # --- Camada 1: cross-match direto por keyword (NOVO, mais específico) ---
        cargos_match = _associar_cargos_por_nome_ghe(nome_ghe, cargos_globais)
        if cargos_match:
            bloco["cargos"] = cargos_match
            continue

        # --- Camada 2: tipo do GHE pelo nome × tipo do cargo ---
        tipo_ghe = _tipo_do_ghe(nome_ghe)
        if tipo_ghe:
            cargos_filtrados = [
                c for c in cargos_globais
                if tipo_ghe in _tipos_do_cargo(c)
            ]
            if cargos_filtrados:
                bloco["cargos"] = cargos_filtrados
                continue
            # FIX Bug #3: removido fallback `else list(cargos_globais)` aqui

        # --- Camada 3: tipos inferidos pelos riscos do bloco ---
        tipos_por_risco = _tipos_do_ghe_por_riscos(bloco.get("riscos_mapeados", []))
        if tipos_por_risco:
            cargos_filtrados = [
                c for c in cargos_globais
                if _tipos_do_cargo(c) & tipos_por_risco
            ]
            if cargos_filtrados:
                bloco["cargos"] = cargos_filtrados
                continue

        # --- Camada 4: indeterminado — NÃO duplica todos os cargos ---
        # FIX Bug #3 RAIZ: removido `bloco["cargos"] = list(cargos_globais)`
        indeterminados.append(nome_ghe)

    # Log GHEs sem cargo associado para revisão manual no Passo 3
    if indeterminados:
        try:
            import streamlit as st
            preview = ", ".join(indeterminados[:5])
            extra = f" (+{len(indeterminados) - 5} outros)" if len(indeterminados) > 5 else ""
            st.warning(
                f"⚠️ {len(indeterminados)} GHE(s) sem cargos associados automaticamente. "
                f"Adicione manualmente no Passo 3 ou ajuste o nome do GHE no PGR para conter "
                f"keywords reconhecidas (ex: alvenaria, hidráulica, pintura, almoxarifado): "
                f"{preview}{extra}"
            )
        except Exception:
            pass


# ── Regex e helpers do parser ────────────────────────────────────────────────

_CARGOS_CANTEIRO = {
    "carpinteiro", "meio oficial carpinteiro", "meio of carpinteiro",
    "pedreiro", "meio oficial pedreiro", "meio of pedreiro",
    "eletricista", "eletricista industrial",
    "servente", "servente de obras",
    "armador", "meio oficial armador", "meio of armador",
    "encanador", "meio oficial encanador", "meio of encanador",
    "serralheiro",
    "mestre de obras", "mestre",
    "tecnico de seguranca do trabalho", "tecnico seguranca trabalho", "tst",
    "engenheiro civil", "engenheiro",
    "administrativo de obras", "aux adm de obras", "auxiliar administrativo de obras",
    "auxiliar administrativo", "aux administrativo",
    "almoxarife",
    "pintor", "pintor de obras",
    "azulejista", "assentador de ceramica",
    "gesseiro",
    "impermeabilizador",
    "operador de cremalheira", "operador de equipamento", "operador",
    "soldador",
    "porteiro", "vigia", "porteiro vigia",
    "sinaleiro",
    "mecanico", "mecanico de manutencao",
    "estagiario", "estagiaria",
    "jovem aprendiz", "aprendiz",
    "encarregado", "encarregado de obras", "supervisor",
    "ajudante", "ajudante geral",
    "calceteiro", "topografo", "motorista",
    "assistente administrativo",
}

_RE_GHE = re.compile(
    r"(?i)^(?:GHE\s*\d*\s*[-\u2013:]?\s*"
    r"|GRUPO\s+HOMOG[E\u00ca]NEO\s+DE\s+EXPOSI[\u00c7C][\u00c3A]O\s*[-\u2013:]?\s*)(.+)$"
)

_RE_AGENTE = re.compile(
    r"(?i)^agente\s*(?:qu[i\u00ed]mico|f[i\u00ed]sico|biol[o\u00f3]gico"
    r"|ergon[o\u00f4]mico|de\s+acidente|de\s+risco)?\s*[:\-\u2013]?\s*(.+)$"
)

# Captura riscos em bullet points e listas numeradas (Bug #2)
_RE_RISCO_BULLET = re.compile(r"^[-\u2022\u2023\u2043*]\s+(.{5,120})$")
_RE_RISCO_NUMERADO = re.compile(r"^\d{1,2}[.)]\s+(.{5,120})$")

# Keywords m\u00ednimas para confirmar que uma linha descreve um risco ocupacional
_TERMOS_RISCO_KW = re.compile(
    r"(?i)\b("
    r"ru[i\u00ed]do|vibra[c\u00e7][a\u00e3]o|calor|frio|radia[c\u00e7][a\u00e3]o"
    r"|poeira|silica|s[i\u00ed]lica|amianto|asbesto|fibra"
    r"|benzeno|tolueno|xileno|estireno|fenol|acetona|mek|solvente"
    r"|chumbo|mercur[i\u00ed]o|manganes|mangan\u00eas|cromo|fluor"
    r"|monoxido|fumo\s+met[a\u00e1]lico|fumos\s+met[a\u00e1]licos"
    r"|biol[o\u00f3]gico|esgoto|leptospiro|hepatite|sangue"
    r"|ergon[o\u00f4]mico|postura|levantamento|esfor[c\u00e7]o"
    r"|altura|confinado|eletric|psicossocial"
    r")\b"
)

_RE_SECAO_FUNCOES = re.compile(
    r"(?i)^(fun[c\u00e7][o\u00f5]es\s*(existentes)?\s*(no\s+canteiro)?|"
    r"fun[c\u00e7][o\u00f5]es\s+quantidade|"
    r"cargo[s]?\s+cbo|"
    r"fun[c\u00e7][o\u00f5]es\s+existentes)"
)

_RE_SKIP = re.compile(
    r"(?i)^("
    r"ef$|ef\s|\d+$|\*|^-+$|^\s*$"
    r"|fun[c\u00e7][o\u00f5]es\s*(quantidade)?$"
    r"|quantidade$"
    r"|raz[a\u00e3]o\s+social|endere[c\u00e7]o|complemento|bairro|cidade|cep|cnpj|cnae"
    r"|grau\s+de\s+risco|telefone|contato"
    r"|\d+\.\s+.+|fase\s+|servi[c\u00e7]os?\s+|hor[a\u00e1]rio|in[i\u00ed]cio|previs[a\u00e3]o"
    r"|n[u\u00fa]mero\s+total|programa\s+de|goiania|goiânia|atualizado|fevereiro|março|janeiro"
    r"|subsolo|t[e\u00e9]rreo|garagem|pavimento|apartamento|penthouse"
    r"|segunda|sexta|s[a\u00e1]bado|\d{2}h"
    r")"
)


# Allowlist + blocklist locais (espelham parser_pgr para fallback _parsear_pgr_local).
# Garante que strings gen\u00e9ricas como "Estrutura de concreto armado", "Contrapiso",
# "Impermeabiliza\u00e7\u00e3o", "Alvenaria" N\u00c3O entrem no campo Cargo.
_CARGOS_ALLOWLIST_KW = re.compile(
    r"(?i)\b("
    r"pedreiro|servente|carpinteiro|armador|ajudante"
    r"|pintor|azulejista|gesseiro|encanador|eletricista"
    r"|serralheiro|soldador|impermeabilizador|aplicador"
    r"|almoxarife|porteiro|vigia|sinaleiro|motorista"
    r"|engenheiro|estagi[a\u00e1]ri[oa]|t[e\u00e9]cnico|encarregado|mestre"
    r"|administrativo|assistente|auxiliar|aprendiz"
    r"|top[o\u00f3]grafo|calceteiro|mec[a\u00e2]nico|operador"
    r"|supervisor|coordenador|gerente|montador|monitor"
    r"|copeir[oa]|cozinheir[oa]|recepcionist[ae]|secret[a\u00e1]ri[oa]"
    r"|escritur[a\u00e1]ri[oa]|vigilante"
    r")\b"
)

_CARGOS_BLOCKLIST_ETAPAS = re.compile(
    r"(?i)^("
    r"estrutura|concreto|alvenaria|fundac[a\u00e3]o|forma\s+de"
    r"|impermeabilizac?[a\u00e3]o|contrapiso|reboco|revestimento|rejunte"
    r"|acabamento|pintura\s+(interna|externa)|gesso\s+corrido|cer[a\u00e2]mica"
    r"|manta\s+asf[a\u00e1]ltica|hidr[a\u00e1]ulica|hidrossanit[a\u00e1]ria"
    r"|el[e\u00e9]trica|prumada|carpintaria|serralheria|armac[a\u00e3]o\s+de"
    r"|atividade|processo|etapa|tarefa|servi[c\u00e7]os?\s+gerais"
    r"|execuc?[a\u00e3]o\s+de|supervis[a\u00e3]o\s+de"
    r")"
)


def _identificar_cargo(linha: str) -> str | None:
    ls = linha.strip()
    if not ls:
        return None
    if _RE_SKIP.match(_normalizar(ls)):
        return None
    if re.match(r"(?i)^agente\s", ls):
        return None
    if re.match(r"(?i)^(risco|perigo|medida|a[c\u00e7][a\u00e3]o|nr[-\s]\d|epis?\s|epc\s)", ls):
        return None
    # BLOCKLIST: rejeita nomes de etapas/processos da obra
    if _CARGOS_BLOCKLIST_ETAPAS.match(ls):
        return None
    nome_sem_qtd = re.sub(r"\s+\d{1,3}\s*$", "", ls).strip()
    nome_n = _normalizar(nome_sem_qtd)
    if nome_n in _CARGOS_CANTEIRO:
        return nome_sem_qtd
    if _normalizar(ls) in _CARGOS_CANTEIRO:
        return ls
    palavras = nome_sem_qtd.split()
    if (
        2 <= len(palavras) <= 5
        and not re.search(r"[;:,./\(\)]", nome_sem_qtd)
        and not re.match(r"(?i)^(agente|risco|perigo|medida|acao|nr[-\s]|epi|epc|uso|utilize|verifique)", nome_sem_qtd)
        and re.match(r"^[A-Z\u00c0-\u00da][a-zA-Z\u00c0-\u00ff\s.]+$", nome_sem_qtd)
        and len(nome_sem_qtd) >= 5
        # ALLOWLIST: precisa conter keyword de cargo conhecido
        and _CARGOS_ALLOWLIST_KW.search(nome_sem_qtd)
    ):
        return nome_sem_qtd
    return None


def _coletar_cargos_globais(linhas: list) -> list:
    cargos = []
    vistos = set()
    em_secao_funcoes = False
    for linha in linhas:
        ls = linha.strip()
        if not ls:
            continue
        if _RE_SECAO_FUNCOES.match(ls):
            em_secao_funcoes = True
            continue
        if _RE_GHE.match(ls):
            break
        if re.match(r"^\d+\.\s+[A-Z]", ls) and em_secao_funcoes:
            em_secao_funcoes = False
            continue
        if not em_secao_funcoes:
            continue
        cargo = _identificar_cargo(ls)
        if cargo:
            cargo_n = _normalizar(cargo)
            if cargo_n not in vistos:
                vistos.add(cargo_n)
                cargos.append(cargo)
    return cargos


def _parsear_pgr_local(texto: str) -> list:
    linhas = texto.split("\n")

    # --- Passagem 1: cargos globais ---
    cargos_globais = _coletar_cargos_globais(linhas)

    # --- Passagem 2: blocos GHE ---
    blocos = []
    bloco_atual = None
    em_ghe = False

    for linha in linhas:
        ls = linha.strip()
        if not ls:
            continue
        m_ghe = _RE_GHE.match(ls)
        if m_ghe:
            if bloco_atual:
                blocos.append(bloco_atual)
            nome_ghe_raw = m_ghe.group(1).strip()
            num_match = re.search(r"\d+", ls)
            num_ghe = num_match.group() if num_match else str(len(blocos) + 1)
            nome_desc = re.sub(r"^\d+\s*[-\u2013]?\s*", "", nome_ghe_raw).strip()
            bloco_atual = {
                "ghe": f"GHE {num_ghe.zfill(2)} - {nome_desc}" if nome_desc else f"GHE {num_ghe}",
                "cargos": [],
                "riscos_mapeados": [],
            }
            em_ghe = True
            continue
        if not em_ghe or bloco_atual is None:
            continue
        m_ag = _RE_AGENTE.match(ls)
        if m_ag:
            bloco_atual["riscos_mapeados"].append(
                {"nome_agente": m_ag.group(1).strip(), "perigo_especifico": ""}
            )
            continue

        # Bullet points / listas numeradas com keyword de risco (Bug #2)
        m_bullet = _RE_RISCO_BULLET.match(ls) or _RE_RISCO_NUMERADO.match(ls)
        if m_bullet and _TERMOS_RISCO_KW.search(ls):
            conteudo = m_bullet.group(1).strip()
            _vistos = {r.get("nome_agente") for r in bloco_atual["riscos_mapeados"]}
            if conteudo not in _vistos:
                bloco_atual["riscos_mapeados"].append(
                    {"nome_agente": conteudo, "perigo_especifico": ""}
                )
            continue

        cargo = _identificar_cargo(ls)
        if cargo and cargo not in bloco_atual["cargos"]:
            bloco_atual["cargos"].append(cargo)

    if bloco_atual:
        blocos.append(bloco_atual)

    # --- Distribuição inteligente v9.6 ---
    if cargos_globais:
        _distribuir_cargos_por_ghe(cargos_globais, blocos)

    # --- F5: Relatório de qualidade do PGR ---
    if _AGENTE_IA_DISPONIVEL:
        try:
            import streamlit as st
            rel = relatorio_qualidade_pgr(blocos, texto)
            icon = "✅" if rel["apto_para_pcmso"] else "⚠️"
            expandido = not rel["apto_para_pcmso"]
            with st.expander(
                f"{icon} Qualidade do PGR recebido — Score: {rel['score']}/100",
                expanded=expandido,
            ):
                c1, c2, c3 = st.columns(3)
                c1.metric("GHEs extraídos", rel["total_ghes"])
                c2.metric("Cargos mapeados", rel["total_cargos"])
                c3.metric("Score", f"{rel['score']}/100")
                if rel["problemas"]:
                    st.warning("**Pontos de atenção antes de gerar o PCMSO:**")
                    for p in rel["problemas"]:
                        st.write(f"• {p}")
                else:
                    st.success("PGR completo — sem problemas identificados.")
                if carregar_cargos_desconhecidos:
                    desconhecidos = carregar_cargos_desconhecidos()
                    if desconhecidos:
                        st.divider()
                        st.warning(f"📋 {len(desconhecidos)} cargo(s) não reconhecido(s) registrado(s) para revisão:")
                        for d in desconhecidos:
                            st.code(
                                f"{d['cargo']}  →  GHE: {d.get('contexto_ghe','?')}  "
                                f"| data: {d.get('data','?')}",
                                language=None,
                            )
        except Exception:
            pass

    return blocos


# ============================================================================
# 2b — TRADUÇÃO DE CHAVES INTERNAS → TEXTO EM PORTUGUÊS NATURAL
# ============================================================================

_CHAVE_PARA_RISCO_TEXTO = {
    "RUIDO":                                             "Ruído",
    "VIBRACAO_CORPO_INTEIRO":                            "Vibração de corpo inteiro",
    "VIBRACAO_MAOS_BRACOS":                              "Vibração em mãos e braços",
    "TRABALHO_EM_ALTURA_ESPACO_CONFINADO_MOTORISTA":     "Trabalho em altura",
    "ESPACO_CONFINADO":                                  "Espaço confinado",
    "PORTEIRO_ELETRICIDADE_ALTURA_MOTORISTA":            "Eletricidade / energia elétrica",
    "TRABALHO_EM_ALTURA_MAQUINAS_PESADAS_PSICOSSOCIAL":  "Risco psicossocial / trabalho em altura",
    "POEIRA_PNOS_GESSO_MADEIRA_METALICA":                "Poeira de madeira, gesso e fumos metálicos (PNOS)",
    "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA":  "Poeira mineral contendo sílica / quartzo",
    "NEVOAS_TINTAS_COLAS_IMPERMEABILIZACAO":             "Névoas de tintas, colas e impermeabilizantes",
    "CONTATO_QUIMICOS_AGRESSORES_PULMONARES":            "Contato com agentes químicos agressores pulmonares",
    "USO_MASCARA_EPI_SEM_RISCO_QUIMICO":                 "Uso de máscara respiratória (sem risco químico específico)",
    "TRICLOROETILENO":                                   "Tricloroetileno",
    "BENZENO":                                           "Benzeno",
    "TOLUENO":                                           "Tolueno",
    "XILENO":                                            "Xileno",
    "ESTIRENO":                                          "Estireno",
    "FENOL":                                             "Fenol",
    "MONOXIDO_DE_CARBONO":                               "Monóxido de carbono",
    "MANGANES":                                          "Manganês",
    "CROMO_HEXAVALENTE":                                 "Cromo hexavalente",
    "FLUOR_ACIDO_FLUORIDRICO_FLUORETOS":                 "Flúor / Ácido fluorídrico / Fluoretos",
    "METIL_ETIL_CETONA":                                 "Metil-etil-cetona (MEK)",
    "ACETONA":                                           "Acetona",
    "TETRAHIDROFURANO":                                  "Tetrahidrofurano",
    "CICLOEXANONA":                                      "Cicloexanona",
    "POLICORTE_SOLDA":                                   "Fumos metálicos de solda / policorte",
    "TRABALHADORES_DA_SAUDE":                            "Agente biológico (trabalhadores da saúde)",
    "MANIPULAR_ALIMENTOS":                               "Agente biológico (manipulação de alimentos)",
    "SUBSTANCIA_OTOTOXICA":                              "Substância ototóxica (potencial perda auditiva)",
}


def _traduzir_chave_para_texto(chave: str) -> str:
    """
    Converte chave interna do parser_pgr (ex: 'RUIDO') para texto em
    português natural (ex: 'Ruído') que o Agente Médico IA consegue processar.
    Fallback: substitui underscores por espaços e aplica Title Case.
    """
    return _CHAVE_PARA_RISCO_TEXTO.get(chave, chave.replace("_", " ").title())


def _converter_ghe_blocos_para_lista(ghe_blocos: dict) -> list:
    """
    Converte o formato dict de parser_pgr.parsear_pgr() para a lista de dicts
    esperada por processar_pcmso() e _normalizar_dados_ghe_para_auditor().
    Aplica _traduzir_chave_para_texto() em cada risco para que o Agente IA
    receba texto legível ('Ruído') em vez de chaves internas ('RUIDO').
    """
    resultado = []
    for nome_ghe, info in ghe_blocos.items():
        riscos_raw = info.get("riscos_identificados", [])
        riscos_mapeados = [
            {
                "nome_agente": (
                    _traduzir_chave_para_texto(r)
                    if isinstance(r, str)
                    else (r.get("nome_agente") or "")
                ),
                "perigo_especifico": r.get("perigo_especifico", "") if isinstance(r, dict) else "",
            }
            for r in riscos_raw
            if r
        ]
        exames = [
            e["exame"] if isinstance(e, dict) else str(e)
            for e in info.get("exames_gerados", [])
        ]
        resultado.append({
            "ghe":             nome_ghe,
            "cargos":          info.get("cargos", []),
            "riscos_mapeados": riscos_mapeados,
            "exames":          exames,
        })
    return resultado


def extrair_pgr_com_fallback(texto_pgr: str):
    # Bug #1 corrigido: parser_pgr exporta parsear_pgr(), não parsear_pgr_texto()
    try:
        from parser_pgr import parsear_pgr as _parsear_pgr_ext
        resultado = _parsear_pgr_ext(texto_pgr, regras={})
        if resultado and resultado.get("ghe_blocos"):
            dados = _converter_ghe_blocos_para_lista(resultado["ghe_blocos"])
            if dados:
                return dados, "local"
    except Exception:
        pass
    dados = _parsear_pgr_local(texto_pgr)
    fonte = "local" if dados else "vazio"
    return dados, fonte


# ============================================================================
# 3 — ENRIQUECIMENTO COM FISPQ
# ============================================================================

def enriquecer_pgr_com_fispq(dados_ghe: list, resultados_fispq: list) -> list:
    agentes = []
    for fispq in resultados_fispq:
        nome = fispq.get("nome_produto") or fispq.get("produto") or ""
        cas  = fispq.get("cas") or ""
        if nome:
            agentes.append({"nome_agente": nome, "perigo_especifico": cas})
        for comp in fispq.get("componentes", []):
            nc = comp.get("nome") or comp.get("substancia") or ""
            cc = comp.get("cas") or ""
            if nc:
                agentes.append({"nome_agente": nc, "perigo_especifico": cc})
    for ghe in dados_ghe:
        existentes = {r.get("nome_agente", "").lower() for r in ghe.get("riscos_mapeados", [])}
        for ag in agentes:
            if ag["nome_agente"].lower() not in existentes:
                ghe.setdefault("riscos_mapeados", []).append(ag)
    return dados_ghe


# ============================================================================
# 4 — MOTOR DE EXAMES
# ============================================================================

_EXAMES_MINIMOS_CANTEIRO = [
    {"nome": "Exame Clínico",      "adm": True,  "per": "12", "mro": True,  "ret": True,  "dem": True},
    {"nome": "Audiometria",        "adm": True,  "per": "12", "mro": True,  "ret": False, "dem": True},
    {"nome": "Acuidade Visual",    "adm": True,  "per": "12", "mro": True,  "ret": False, "dem": False},
    {"nome": "Hemograma Completo", "adm": True,  "per": "12", "mro": True,  "ret": False, "dem": False},
    {"nome": "Glicemia em Jejum",  "adm": True,  "per": "12", "mro": True,  "ret": False, "dem": False},
    {"nome": "ECG",                "adm": True,  "per": "12", "mro": True,  "ret": False, "dem": False},
    {"nome": "Espirometria",       "adm": True,  "per": "24", "mro": True,  "ret": False, "dem": True},
    {"nome": "RX de Tórax OIT",   "adm": True,  "per": "60", "mro": True,  "ret": False, "dem": True},
]

_EXAMES_MINIMOS_ESCRIT = [
    {"nome": "Exame Clínico", "adm": True, "per": "12", "mro": True, "ret": True, "dem": True},
]


def _bool_para_x(val) -> str:
    if isinstance(val, bool):
        return "X" if val else "-"
    if isinstance(val, str):
        return val.upper().strip() or "-"
    return "-"


def _per_para_str(per) -> str:
    try:
        return f"{int(per)}M"
    except (TypeError, ValueError):
        return str(per).upper().strip() if per else ""


def _riscos_para_lista_str(riscos_mapeados: list) -> list:
    resultado = []
    for r in riscos_mapeados:
        if isinstance(r, dict):
            nome = r.get("nome_agente") or r.get("nome") or ""
            perigo = r.get("perigo_especifico") or ""
            s = " ".join(filter(None, [nome, perigo])).strip()
            if s:
                resultado.append(s)
        elif isinstance(r, str) and r.strip():
            resultado.append(r.strip())
    return resultado


def _contexto_do_ghe(ghe_nome: str, riscos_str: list) -> dict:
    t = _normalizar(ghe_nome + " " + " ".join(riscos_str))
    return {
        "altura": any(x in t for x in ["altura", "nr-35", "nr35", "andaime", "cremalheira", "grua", "telhado"]),
        "confinado": any(x in t for x in ["confinado", "cisterna", "poco"]),
        "eletricidade": any(x in t for x in ["eletric", "nr-10", "nr10", "energizado", "choque"]),
        "maquinas_pesadas": any(x in t for x in ["maquina", "betoneira", "guindaste", "grua", "cremalheira"]),
    }


def _resolver_exames_cargo(cargo, riscos_str, contexto, e_canteiro, ghe_nome=""):
    if _AGENTE_IA_DISPONIVEL:
        resultado = processar_cargo_ia(
            cargo=cargo, riscos=riscos_str, contexto=contexto,
            e_canteiro=e_canteiro, ghe_nome=ghe_nome,
        )
        return resultado.get("exames", []), resultado.get("chave_mestra", ""), resultado.get("auditoria_nr7", {})
    base = deepcopy(_EXAMES_MINIMOS_CANTEIRO if e_canteiro else _EXAMES_MINIMOS_ESCRIT)
    return base, None, {}


# ============================================================================
# 5 — processar_pcmso
# ============================================================================

# Padrão para extrair número e título de um nome de GHE existente.
# Aceita "GHE 01 - Foo", "GHE 7: Bar", "GHE 12 — Baz", etc.
_RE_GHE_PREFIX = re.compile(
    r'^\s*GHE\s*(\d+)\s*[-:–—]?\s*',
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Prompt 7 — Deduplicação intra-GHE + redistribuição admin/técnico
# ---------------------------------------------------------------------------
# Keywords (forma normalizada) que identificam cargos administrativos.
# Usadas para mover cargos admin de GHEs técnicos para GHE administrativo.
_ADMIN_CARGO_KEYS = (
    'administrativo', 'aprendiz', 'engenheiro',
    'estagiari', 'assistente administrativo',
)

# Tipos de GHE considerados administrativos pelo _tipo_do_ghe()
_TIPOS_GHE_ADMIN = {'engenharia', 'seguranca', 'administracao', 'almoxarifado'}


def _norm_cargo_para_dedup(cargo: str) -> str:
    """Wrapper: usa normalizar_cargo() do Prompt 1 com fallback para _normalizar."""
    if not cargo:
        return ""
    if _normalizar_cargo_aud is not None:
        try:
            return _normalizar_cargo_aud(cargo)
        except Exception:
            pass
    return _normalizar(cargo).strip()


def _consolidar_cargos_dados_ghe(dados_ghe: list) -> None:
    """
    Pré-processamento IN PLACE de dados_ghe (Prompt 7):

      1. DEDUP intra-GHE: remove cargos duplicados dentro de cada GHE,
         comparando pela forma normalizada via normalizar_cargo() do Prompt 1.
         Preserva a primeira ocorrência (forma original para exibição).
         "Servente" pode aparecer em múltiplos GHEs diferentes — apenas
         duplicatas DENTRO do mesmo GHE são removidas.

      2. REDISTRIBUIÇÃO: cargos administrativos (Administrativo,
         Administrativo De Obra, Aprendiz, Engenheiro, Estagiário) que
         aparecem em GHEs técnicos (Pintura, Serralheria, etc.) são
         movidos para o primeiro GHE administrativo encontrado. Se não
         houver GHE admin de destino, cargos permanecem onde estão
         (preferível a perda silenciosa).

    Aplicado no início de processar_pcmso() — antes da geração do DataFrame.
    """
    if not dados_ghe:
        return

    # ── Etapa 1: dedup intra-GHE ─────────────────────────────────────────
    for ghe in dados_ghe:
        cargos_orig = list(ghe.get('cargos', []))
        seen = set()
        cargos_dedup = []
        for c in cargos_orig:
            norm = _norm_cargo_para_dedup(c)
            if norm and norm not in seen:
                seen.add(norm)
                cargos_dedup.append(c)  # preserva forma ORIGINAL para exibição
        ghe['cargos'] = cargos_dedup

    # ── Etapa 2: redistribuir cargos admin de GHEs técnicos ──────────────
    # Identifica primeiro GHE administrativo como destino
    ghe_destino = None
    for ghe in dados_ghe:
        if _tipo_do_ghe(ghe.get('ghe', '')) in _TIPOS_GHE_ADMIN:
            ghe_destino = ghe
            break
    if ghe_destino is None:
        return  # sem GHE admin → não move (mantém integridade)

    # Conjunto de cargos já presentes no destino (forma normalizada)
    nomes_no_destino = {
        _norm_cargo_para_dedup(c) for c in ghe_destino.get('cargos', [])
    }

    for ghe in dados_ghe:
        if ghe is ghe_destino:
            continue
        if _tipo_do_ghe(ghe.get('ghe', '')) in _TIPOS_GHE_ADMIN:
            continue  # outro GHE admin existente — não mexe

        # GHE técnico — extrai cargos admin
        cargos = list(ghe.get('cargos', []))
        cargos_kept = []
        for c in cargos:
            c_norm = _norm_cargo_para_dedup(c)
            is_admin = any(kw in c_norm for kw in _ADMIN_CARGO_KEYS)
            if is_admin:
                # Move para destino se ainda não está lá
                if c_norm and c_norm not in nomes_no_destino:
                    ghe_destino.setdefault('cargos', []).append(c)
                    nomes_no_destino.add(c_norm)
            else:
                cargos_kept.append(c)
        ghe['cargos'] = cargos_kept


def _renumerar_ghe_sequencial(nome_original: str, novo_num: int) -> str:
    """
    Reconstrói o nome do GHE com numeração sequencial (1, 2, 3, ...) e
    título descritivo preservado a partir do nome original.

    Comportamento:
      - "GHE 07: Estrutura - Alvenaria"  -> "GHE 01 - Estrutura - Alvenaria"
      - "GHE 03 - Forma de pilar"        -> "GHE 02 - Forma de pilar"
      - "GHE 99" (sem descrição)         -> "GHE 03 - Atividade não identificada"
      - ""                               -> "GHE 04 - Atividade não identificada"

    Garante que o nome NUNCA fica em branco (sempre tem título), conforme
    spec do Prompt 6 (Parte A — fallback obrigatório).
    """
    titulo = _RE_GHE_PREFIX.sub('', str(nome_original or ''), count=1).strip()
    if not titulo:
        titulo = "Atividade não identificada"
    return f"GHE {novo_num:02d} - {titulo}"


def processar_pcmso(dados_ghe: list, tipo_ambiente: str = "canteiro") -> pd.DataFrame:
    # Prompt 7: dedup intra-GHE + redistribuição cargos admin/técnico.
    # Modifica dados_ghe in place ANTES de gerar o DataFrame.
    _consolidar_cargos_dados_ghe(dados_ghe)

    linhas = []
    # Renumera GHEs sequencialmente por posição na lista (Parte B do Prompt 6).
    # `enumerate(start=1)` reinicia a cada chamada — sem estado global.
    for idx, ghe_item in enumerate(dados_ghe, start=1):
        nome_original   = ghe_item.get("ghe") or ghe_item.get("nome_ghe") or ""
        nome_ghe        = _renumerar_ghe_sequencial(nome_original, idx)
        cargos          = ghe_item.get("cargos", [])
        riscos_mapeados = ghe_item.get("riscos_mapeados", [])
        riscos_str      = _riscos_para_lista_str(riscos_mapeados)
        exames_pre      = ghe_item.get("exames", [])

        if tipo_ambiente == "canteiro":
            e_canteiro = True
        elif tipo_ambiente == "escritorio":
            e_canteiro = False
        else:
            nome_n = _normalizar(nome_ghe)
            e_canteiro = not any(
                x in nome_n for x in ["escritorio", "administrativo", "engenharia", "planejamento", "gerencia"]
            )
            if "almoxarifado" in nome_n:
                e_canteiro = True

        contexto = _contexto_do_ghe(nome_ghe, riscos_str)

        for cargo in cargos:
            auditoria_nr7_cargo = {}
            if exames_pre:
                exames_base = deepcopy(exames_pre) if isinstance(exames_pre[0], dict) else [
                    {"nome": str(e), "adm": True, "per": "12", "mro": True, "ret": False, "dem": False}
                    for e in exames_pre
                ]
                if _AGENTE_IA_DISPONIVEL:
                    res_ia = processar_cargo_ia(
                        cargo=cargo, riscos=riscos_str, contexto=contexto,
                        e_canteiro=e_canteiro, ghe_nome=nome_ghe,
                    )
                    nomes_ok = {_normalizar(e.get("nome", "")) for e in exames_base}
                    for ex in res_ia.get("exames", []):
                        if _normalizar(ex.get("nome", "")) not in nomes_ok:
                            exames_base.append(ex)
                            nomes_ok.add(_normalizar(ex.get("nome", "")))
                    fonte = f"banco+agente_ia:{res_ia.get('chave_mestra', '')}|ghe:{res_ia.get('chave_ghe','')}"
                    auditoria_nr7_cargo = res_ia.get("auditoria_nr7", {})
                else:
                    fonte = "banco_pre_definido"
                    auditoria_nr7_cargo = {}
                exames_finais = exames_base
            else:
                exames_finais, chave, auditoria_nr7_cargo = _resolver_exames_cargo(
                    cargo, riscos_str, contexto, e_canteiro, ghe_nome=nome_ghe
                )
                fonte = f"agente_ia:{chave}|ghe:{nome_ghe}" if _AGENTE_IA_DISPONIVEL else "fallback_minimo"

            for ex in exames_finais:
                nome_ex = ex.get("nome", "") if isinstance(ex, dict) else str(ex)
                adm = _bool_para_x(ex.get("adm", True) if isinstance(ex, dict) else True)
                per = _per_para_str(ex.get("per", "12") if isinstance(ex, dict) else "12")
                mro = _bool_para_x(ex.get("mro", True) if isinstance(ex, dict) else True)
                ret = _bool_para_x(ex.get("ret", False) if isinstance(ex, dict) else False)
                dem = _bool_para_x(ex.get("dem", False) if isinstance(ex, dict) else False)
                linhas.append({
                    "GHE / Setor": nome_ghe, "Cargo": cargo, "Exame": nome_ex,
                    "ADM": adm, "PER": per, "MRO": mro, "RT": ret, "DEM": dem,
                    "Justificativa": fonte,
                })

    cols = ["GHE / Setor", "Cargo", "Exame", "ADM", "PER", "MRO", "RT", "DEM", "Justificativa"]
    df_final = pd.DataFrame(linhas) if linhas else pd.DataFrame(columns=cols)

    # --- v9.4: Auditoria NR-7 por cargo (agente_medico_ia v2.2) ---
    if _AGENTE_IA_DISPONIVEL and not df_final.empty:
        try:
            import streamlit as st
            divergencias_total = []
            for idx_aud, ghe_item in enumerate(dados_ghe, start=1):
                # Usa o nome renumerado para que a auditoria exiba o mesmo
                # número que aparece no PCMSO gerado (Parte B do Prompt 6).
                nome_ghe_exp = _renumerar_ghe_sequencial(ghe_item.get("ghe", ""), idx_aud)
                riscos_str_exp = _riscos_para_lista_str(ghe_item.get("riscos_mapeados", []))
                contexto_exp = _contexto_do_ghe(nome_ghe_exp, riscos_str_exp)
                e_canteiro_exp = tipo_ambiente == "canteiro"
                for cargo_exp in ghe_item.get("cargos", []):
                    _, _, aud = _resolver_exames_cargo(
                        cargo_exp, riscos_str_exp, contexto_exp, e_canteiro_exp, ghe_nome=nome_ghe_exp
                    )
                    faltando = aud.get("faltando", [])
                    divs = aud.get("divergencias", [])
                    if faltando or divs:
                        divergencias_total.append({
                            "ghe": nome_ghe_exp,
                            "cargo": cargo_exp,
                            "faltando": faltando,
                            "divergencias": divs,
                        })
            if divergencias_total:
                with st.expander(
                    f"⚠️ Auditoria NR-7 por cargo — {len(divergencias_total)} divergência(s) detectada(s)",
                    expanded=False,
                ):
                    for item in divergencias_total:
                        st.markdown(f"**{item['ghe']} → {item['cargo']}**")
                        if item["faltando"]:
                            st.warning("Faltando: " + ", ".join(e["nome"] for e in item["faltando"]))
                        if item["divergencias"]:
                            for d in item["divergencias"]:
                                divs_str = ", ".join(
                                    f"{dd['campo']}: esperado={dd['esperado']} gerado={dd['gerado']}"
                                    for dd in d.get("divergencias", [])
                                )
                                st.info(f"↔ {d['nome']}: {divs_str}")
        except Exception:
            pass

    # --- F1: Auditoria NR-7 ---
    if _AGENTE_IA_DISPONIVEL and not df_final.empty:
        try:
            import streamlit as st
            audit = auditar_pcmso(df_final, dados_ghe)
            icon = "✅" if audit["aprovado"] else "❌"
            expanded_audit = not audit["aprovado"]
            with st.expander(
                f"{icon} Auditoria NR-7 — {audit['resumo']}",
                expanded=expanded_audit,
            ):
                if audit["pendencias"]:
                    st.error("**Pendências críticas — corrigir antes de assinar:**")
                    for p in audit["pendencias"]:
                        st.write(p)
                if audit["avisos"]:
                    st.warning("**Avisos de conformidade:**")
                    for a in audit["avisos"]:
                        st.write(a)
                if not audit["pendencias"] and not audit["avisos"]:
                    st.success("Nenhuma pendência ou aviso encontrado. PCMSO pronto para assinatura.")
        except Exception:
            pass

    # --- F6: Justificativas técnicas por GHE (expander colapsado) ---
    if _AGENTE_IA_DISPONIVEL and dados_ghe:
        try:
            import streamlit as st
            justificativas = gerar_justificativas_pcmso(dados_ghe)
            if justificativas:
                with st.expander("📝 Justificativas técnicas por GHE (para o médico RT)", expanded=False):
                    for j in justificativas:
                        st.markdown(f"**{j['ghe']}**")
                        st.info(j["justificativa"])
        except Exception:
            pass

    return df_final


# ============================================================================
# 6 — gerar_justificativas_pcmso  (F6 — função pública)
# ============================================================================

def gerar_justificativas_pcmso(dados_ghe: list) -> list:
    if not _AGENTE_IA_DISPONIVEL:
        return []
    resultado = []
    # Renumera consistentemente com processar_pcmso (Parte B do Prompt 6)
    for idx_just, ghe_item in enumerate(dados_ghe, start=1):
        nome_ghe = _renumerar_ghe_sequencial(ghe_item.get("ghe", ""), idx_just)
        cargos = ghe_item.get("cargos", [])
        riscos_str = _riscos_para_lista_str(ghe_item.get("riscos_mapeados", []))
        try:
            texto_j = gerar_justificativa_ghe(
                ghe_nome=nome_ghe,
                cargos=cargos,
                riscos=riscos_str,
                exames_nomes=[],
            )
        except Exception:
            texto_j = f"Justificativa não disponível para {nome_ghe}."
        resultado.append({"ghe": nome_ghe, "justificativa": texto_j})
    return resultado


# ============================================================================
# 7 — gerar_html_pcmso  (v9.5 — rowspan em GHE e Cargo)
# ============================================================================

def gerar_html_pcmso(df: pd.DataFrame, cabecalho: dict = None) -> str:
    """
    v9.5 — Gera HTML com células GHE e Cargo mergeadas (rowspan) para
    eliminar a repetição linha a linha.
    Estrutura: GHE (rowspan = total de linhas do GHE) |
               Cargo (rowspan = total de exames do cargo) |
               Exame | ADM | PER | MRO | RT | DEM
    """
    if cabecalho is None:
        cabecalho = {}

    cs       = "border:1px solid #ccc;padding:6px 8px;font-size:12px;vertical-align:top;"
    cs_ghe   = f"{cs}background:#084D22;color:white;font-weight:bold;text-align:center;"
    cs_cargo = f"{cs}font-weight:bold;"
    th       = f"{cs}background:#084D22;color:white;text-align:center;font-weight:bold;"
    cols_vis = ["GHE / Setor", "Cargo", "Exame", "ADM", "PER", "MRO", "RT", "DEM"]
    hoje     = date.today().strftime("%d/%m/%Y")

    cab_html = f"""
    <div style="font-family:Arial,sans-serif;margin:0 auto;max-width:1100px;padding:20px;">
    <h2 style="color:#084D22;text-align:center;">PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL</h2>
    <h3 style="color:#084D22;text-align:center;">NR-07 — PCMSO</h3>
    <table style="width:100%;border-collapse:collapse;margin-bottom:20px;font-size:13px;">
      <tr><td><b>Empresa:</b> {cabecalho.get('razao_social','')}</td><td><b>CNPJ:</b> {cabecalho.get('cnpj','')}</td></tr>
      <tr><td><b>Médico RT:</b> {cabecalho.get('medico_rt','')}</td><td><b>Obra:</b> {cabecalho.get('obra','')}</td></tr>
      <tr><td><b>Vigência:</b> {cabecalho.get('vig_ini','')} a {cabecalho.get('vig_fim','')}</td><td><b>Resp. SST:</b> {cabecalho.get('responsavel_tec','')}</td></tr>
      <tr><td colspan="2"><b>Gerado em:</b> {hoje} — {VERSAO_MODULO_PCMSO}</td></tr>
    </table>
    <table style="width:100%;border-collapse:collapse;">
      <thead><tr>{''.join(f'<th style="{th}">{c}</th>' for c in cols_vis)}</tr></thead><tbody>
    """

    rows_html = []
    if not df.empty:
        ghes = df["GHE / Setor"].unique() if "GHE / Setor" in df.columns else []
        for ghe_nome in ghes:
            df_ghe = df[df["GHE / Setor"] == ghe_nome]
            rowspan_ghe = len(df_ghe)
            cargos = df_ghe["Cargo"].unique() if "Cargo" in df_ghe.columns else []
            primeira_linha_ghe = True
            for cargo in cargos:
                df_cargo = df_ghe[df_ghe["Cargo"] == cargo]
                rowspan_cargo = len(df_cargo)
                primeira_linha_cargo = True
                for _, row in df_cargo.iterrows():
                    tr = "<tr>"
                    if primeira_linha_ghe:
                        tr += f'<td style="{cs_ghe}" rowspan="{rowspan_ghe}">{ghe_nome}</td>'
                        primeira_linha_ghe = False
                    if primeira_linha_cargo:
                        tr += f'<td style="{cs_cargo}" rowspan="{rowspan_cargo}">{cargo}</td>'
                        primeira_linha_cargo = False
                    for col in ["Exame", "ADM", "PER", "MRO", "RT", "DEM"]:
                        val = row.get(col, "") if col in df.columns else ""
                        tr += f'<td style="{cs}">{val}</td>'
                    tr += "</tr>\n"
                    rows_html.append(tr)

    return (
        f"<!DOCTYPE html><html><body>{cab_html}"
        + "".join(rows_html)
        + f"</tbody></table>"
        + f"<p style='font-size:11px;color:#888;text-align:center;'>Gerado pelo Sistema SST Seconci GO | {hoje}</p>"
        + "</div></body></html>"
    )


# ============================================================================
# 8 — gerar_docx_rq61  (v9.5 — merge vertical de células GHE e Cargo)
# ============================================================================

def _set_cell_background(cell, hex_color: str) -> None:
    """Aplica cor de fundo a uma célula .docx via XML."""
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    tcp = cell._tc.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:fill"), hex_color)
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:val"), "clear")
    tcp.append(shd)


def _merge_cells_vertical(table, col_idx: int, start_row: int, end_row: int) -> None:
    """
    Faz merge vertical de células em `col_idx` de `start_row` até `end_row` (inclusive).
    Usa a API nativa do python-docx: merge() entre primeira e última célula.
    """
    if end_row <= start_row:
        return
    a = table.rows[start_row].cells[col_idx]
    b = table.rows[end_row].cells[col_idx]
    a.merge(b)


def gerar_docx_rq61(df: pd.DataFrame, cabecalho: dict = None) -> bytes:
    """
    v9.5 — Gera .docx com células GHE e Cargo mergeadas verticalmente.
    Estrutura idêntica ao modelo de referência (PDF VIVERDE):
      - Linha de cabeçalho GHE: célula mergeada horizontalmente (todas as colunas),
        fundo verde escuro, texto centralizado.
      - Para cada cargo: célula "Cargo" mergeada verticalmente pelo nº de exames,
        exames em linhas separadas.
    """
    if cabecalho is None:
        cabecalho = {}
    try:
        from docx import Document
        from docx.shared import RGBColor, Cm, Pt
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.oxml.ns import qn
        from docx.oxml import OxmlElement
    except ImportError:
        return df.to_csv(index=False).encode("utf-8")

    doc = Document()
    for section in doc.sections:
        section.top_margin = section.bottom_margin = Cm(2)
        section.left_margin = section.right_margin = Cm(2)

    h1 = doc.add_heading("PROGRAMA DE CONTROLE MÉDICO DE SAÚDE OCUPACIONAL", level=1)
    h1.alignment = WD_ALIGN_PARAGRAPH.CENTER
    if h1.runs:
        h1.runs[0].font.color.rgb = RGBColor(0x08, 0x4D, 0x22)
    doc.add_heading("NR-07 — PCMSO", level=2).alignment = WD_ALIGN_PARAGRAPH.CENTER

    meta = [
        ("Empresa", cabecalho.get("razao_social", "")),
        ("CNPJ", cabecalho.get("cnpj", "")),
        ("Médico RT", cabecalho.get("medico_rt", "")),
        ("Obra/Unidade", cabecalho.get("obra", "")),
        ("Vigência", f"{cabecalho.get('vig_ini','')} a {cabecalho.get('vig_fim','')}"),
        ("Resp. SST", cabecalho.get("responsavel_tec", "")),
        ("Gerado em", date.today().strftime("%d/%m/%Y") + f" — {VERSAO_MODULO_PCMSO}"),
    ]
    t_meta = doc.add_table(rows=len(meta), cols=2)
    t_meta.style = "Table Grid"
    for i, (k, v) in enumerate(meta):
        t_meta.rows[i].cells[0].text = k
        t_meta.rows[i].cells[1].text = v
    doc.add_paragraph()

    COLS = ["FUNÇÃO", "EXAMES SOLICITADOS", "ADM", "PER", "MRO", "RT", "DEM"]
    COL_MAP = {
        "FUNÇÃO":            "Cargo",
        "EXAMES SOLICITADOS": "Exame",
        "ADM": "ADM", "PER": "PER", "MRO": "MRO", "RT": "RT", "DEM": "DEM",
    }

    if df.empty:
        buf = io.BytesIO()
        doc.save(buf)
        return buf.getvalue()

    ghes_ordem = list(dict.fromkeys(df["GHE / Setor"].tolist())) if "GHE / Setor" in df.columns else []

    estrutura = []
    for ghe_nome in ghes_ordem:
        df_ghe = df[df["GHE / Setor"] == ghe_nome]
        cargos_ordem = list(dict.fromkeys(df_ghe["Cargo"].tolist())) if "Cargo" in df_ghe.columns else []
        estrutura.append(("ghe_header", ghe_nome))
        estrutura.append(("col_header", None))
        for cargo in cargos_ordem:
            df_cargo = df_ghe[df_ghe["Cargo"] == cargo]
            rows_cargo = list(df_cargo.itertuples(index=False))
            for idx, row in enumerate(rows_cargo):
                estrutura.append(("cargo_exame", (cargo, row, idx == 0, len(rows_cargo))))

    num_linhas = len(estrutura)
    t = doc.add_table(rows=num_linhas, cols=len(COLS))
    t.style = "Table Grid"

    row_idx = 0
    merge_ops = []

    for tipo, dados in estrutura:
        cells = t.rows[row_idx].cells

        if tipo == "ghe_header":
            merged = cells[0]
            for ci in range(1, len(COLS)):
                merged = merged.merge(cells[ci])
            merged.text = dados
            p = merged.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            if p.runs:
                p.runs[0].bold = True
                p.runs[0].font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            else:
                run = p.add_run(dados)
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            _set_cell_background(merged, "084D22")

        elif tipo == "col_header":
            for ci, col in enumerate(COLS):
                p = cells[ci].paragraphs[0]
                run = p.add_run(col)
                run.bold = True
                run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                _set_cell_background(cells[ci], "084D22")

        elif tipo == "cargo_exame":
            cargo, row, is_first, rowspan = dados

            if is_first:
                cells[0].text = cargo
                if rowspan > 1:
                    merge_ops.append((0, row_idx, row_idx + rowspan - 1))

            exame_val = getattr(row, "Exame", "") if hasattr(row, "Exame") else ""
            adm_val   = getattr(row, "ADM",   "") if hasattr(row, "ADM")   else ""
            per_val   = getattr(row, "PER",   "") if hasattr(row, "PER")   else ""
            mro_val   = getattr(row, "MRO",   "") if hasattr(row, "MRO")   else ""
            rt_val    = getattr(row, "RT",    "") if hasattr(row, "RT")    else ""
            dem_val   = getattr(row, "DEM",   "") if hasattr(row, "DEM")   else ""

            cells[1].text = str(exame_val)
            cells[2].text = str(adm_val)
            cells[3].text = str(per_val)
            cells[4].text = str(mro_val)
            cells[5].text = str(rt_val)
            cells[6].text = str(dem_val)

        row_idx += 1

    for col_idx, start_row, end_row in merge_ops:
        _merge_cells_vertical(t, col_idx, start_row, end_row)

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
