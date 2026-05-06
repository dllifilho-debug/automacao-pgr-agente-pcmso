#!/usr/bin/env python3
"""
scripts/migrar_pdf_rq61.py

Parseia o PDF RQ.61 (MATRIZ DE EXAMES CMO VIVERDE AREIAO 06.03.2025)
e grava data/banco_ghe_cargo_v1.json com entradas:

  "GHE_ESTRUTURA_FORMA:CARPINTEIRO": {
      "ghe_descricao": "Estrutura de concreto armado - Execução fôrma de pilar e laje",
      "cargo":         "Carpinteiro",
      "exames":        [...],
      "fonte":         "RQ.61 Viverde 06.03.2025"
  }

Uso:
  python scripts/migrar_pdf_rq61.py
"""

import re
import json
import unicodedata
from pathlib import Path

import pdfplumber

# ─── Paths ────────────────────────────────────────────────────────────────────

ROOT      = Path(__file__).resolve().parent.parent
PDF_PATH  = ROOT / "matrizes_originais" / "MATRIZ DE EXAMES(ATUALIZAÇÃO)CMO VIVERDE AREIAO 06.03.2025.pdf"
JSON_PATH = ROOT / "data" / "banco_ghe_cargo_v1.json"

# ─── Helpers ──────────────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Lowercase + strip accents."""
    if not s:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(s).lower().strip())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ─── Mapa GHE título → chave semântica ───────────────────────────────────────
# Cada entrada: ([keywords normalizadas TODAS presentes em norm(titulo)], chave)
# Mais específico (mais keywords) antes do mais genérico.

_MAPA_GHE_SECAO = [
    # ── Estrutura — mais específico primeiro ───────────────────────────────
    # GHE 02: "Execução de viga, pilar e laje" → ARMACAO (must precede FORMA)
    (["estrutura", "viga"],                         "GHE_ESTRUTURA_ARMACAO"),
    # GHE 01: "Execução fôrma de pilar e laje" → FORMA
    (["estrutura", "laje", "pilar"],                "GHE_ESTRUTURA_FORMA"),
    (["estrutura", "forma"],                        "GHE_ESTRUTURA_FORMA"),
    (["estrutura", "cremalheira", "monta"],         "GHE_ESTRUTURA_CREMALHEIRA_MONT"),
    (["estrutura", "cremalheira", "manut"],         "GHE_ESTRUTURA_CREMALHEIRA_MONT"),
    (["estrutura", "cremalheira", "desmonta"],      "GHE_ESTRUTURA_CREMALHEIRA_MONT"),
    (["estrutura", "cremalheira"],                  "GHE_ESTRUTURA_CREMALHEIRA_OP"),
    (["estrutura", "grua", "opera"],                "GHE_ESTRUTURA_GRUA_OPERACAO"),
    (["estrutura", "grua"],                         "GHE_ESTRUTURA_GRUA_SINALIZACAO"),
    # Prumada (desenergizada) must come before generic "energizada" check
    (["estrutura", "prumada"],                      "GHE_ESTRUTURA_PRUMADA"),
    (["estrutura", "eletrica", "tempor"],           "GHE_ESTRUTURA_ELETRICA_TEMP"),
    # "desenergizada" contains "energizada" — so prumada must be matched first ↑
    (["estrutura", "energizada"],                   "GHE_ESTRUTURA_ELETRICA_TEMP"),
    (["estrutura", "hidro"],                        "GHE_ESTRUTURA_HIDRO"),
    (["estrutura", "tubulac"],                      "GHE_ESTRUTURA_HIDRO"),
    (["estrutura", "argamassa"],                    "GHE_ESTRUTURA_BETONEIRA"),
    (["estrutura", "betoneira"],                    "GHE_ESTRUTURA_BETONEIRA"),
    (["estrutura", "alvenaria"],                    "GHE_ESTRUTURA_ALVENARIA"),
    (["estrutura", "serralheria"],                  "GHE_ESTRUTURA_SERRALHERIA"),
    (["estrutura", "pintura"],                      "GHE_ESTRUTURA_PINTURA"),
    (["estrutura", "limpeza"],                      "GHE_ESTRUTURA_LIMPEZA"),
    # "gerais" ≠ contains "geral" (different string), so use "servic" only
    (["estrutura", "servic"],                       "GHE_ESTRUTURA_SERVICOS_GERAIS"),
    (["estrutura", "portaria"],                     "GHE_ESTRUTURA_PORTARIA"),
    # ── Acabamento ─────────────────────────────────────────────────────────
    (["acabamento", "manta"],                       "GHE_ACABAMENTO_MANTA_ASFALTICA"),
    (["acabamento", "asfaltic"],                    "GHE_ACABAMENTO_MANTA_ASFALTICA"),
    (["acabamento", "assentamento"],                "GHE_ACABAMENTO_ASSENTAMENTO"),
    (["acabamento", "rejunte"],                     "GHE_ACABAMENTO_REJUNTE"),
    (["acabamento", "revestimento"],                "GHE_ACABAMENTO_REVESTIMENTO"),
    (["acabamento", "impermeabilizac"],             "GHE_ACABAMENTO_IMPERMEABILIZACAO"),
    (["acabamento", "contrapiso"],                  "GHE_ACABAMENTO_CONTRAPISO"),
    (["acabamento", "reboco"],                      "GHE_ACABAMENTO_REBOCO"),
    (["acabamento", "gesso"],                       "GHE_ACABAMENTO_GESSO"),
    (["acabamento", "pintura"],                     "GHE_ACABAMENTO_PINTURA"),
    # ── Administração de campo ─────────────────────────────────────────────
    (["administrac", "engenharia"],                 "GHE_ADMIN_ENGENHARIA"),
    (["administrac", "planejamento"],               "GHE_ADMIN_ENGENHARIA"),
    (["administrac", "seguranca"],                  "GHE_ADMIN_SST"),
    (["administrac", "supervisao"],                 "GHE_ADMIN_SUPERVISAO_REJUNTE"),
    (["administrac", "execucao"],                   "GHE_ADMIN_EXECUCAO"),
    (["administrac", "administrativo"],             "GHE_ADMIN_ADMINISTRATIVO"),
    (["administrac", "almoxarifado"],               "GHE_ADMIN_ALMOXARIFADO"),
]


def _detectar_chave_ghe(titulo: str) -> str | None:
    t = _norm(titulo)
    for keywords, chave in _MAPA_GHE_SECAO:
        if all(kw in t for kw in keywords):
            return chave
    return None


# ─── Mapa cargo normalizado → chave mestra ───────────────────────────────────

_MAPA_CARGO: dict[str, str] = {
    "engenheiro civil":                        "ENGENHEIRO",
    "engenheiro":                              "ENGENHEIRO",
    "estagiario de engenharia":                "ESTAGIARIO",
    "estagiario":                              "ESTAGIARIO",
    "estagiaria":                              "ESTAGIARIO",
    "tecnico de seguranca do trabalho":        "TECNICO_SST",
    "tecnico de seguranca":                    "TECNICO_SST",
    "mestre de obra":                          "MESTRE_OBRA",
    "mestre de obras":                         "MESTRE_OBRA",
    "encarregado de pedreiro":                 "ENCARREGADO_GERAL",
    "encarregado de pintor":                   "ENCARREGADO_GERAL",
    "encarregado de eletricista":              "ENCARREGADO_GERAL",
    "encarregado de encanador":                "ENCARREGADO_GERAL",
    "encarregado de serralheiro":              "ENCARREGADO_GERAL",
    "encarregado de carpinteiro":              "ENCARREGADO_GERAL",
    "encarregado de armador":                  "ENCARREGADO_GERAL",
    "encarregado de impermeabilizacao":        "IMPERMEABILIZADOR",
    "encarregado":                             "ENCARREGADO_SUPERVISAO",
    "administrativo de obra":                  "AUXILIAR_ADMINISTRATIVO",
    "administrativo de obras":                 "AUXILIAR_ADMINISTRATIVO",
    "auxiliar administrativo de obras":        "AUXILIAR_ADMINISTRATIVO",
    "auxiliar administrativo":                 "AUXILIAR_ADMINISTRATIVO",
    "assistente administrativo":               "AUXILIAR_ADMINISTRATIVO",
    "jovem aprendiz":                          "JOVEM_APRENDIZ",
    "aprendiz":                                "JOVEM_APRENDIZ",
    "almoxarife":                              "ALMOXARIFE",
    "porteiro vigia":                          "PORTEIRO_VIGIA",
    "porteiro":                                "PORTEIRO_VIGIA",
    "vigia":                                   "PORTEIRO_VIGIA",
    "meio oficial de carpinteiro":             "CARPINTEIRO",
    "meio of. carpinteiro":                    "CARPINTEIRO",
    "meio of carpinteiro":                     "CARPINTEIRO",
    "carpinteiro":                             "CARPINTEIRO",
    "meio oficial de armador":                 "ARMADOR",
    "meio of. armador":                        "ARMADOR",
    "meio of armador":                         "ARMADOR",
    "armador":                                 "ARMADOR",
    "meio oficial de pedreiro":                "PEDREIRO",
    "meio of. pedreiro":                       "PEDREIRO",
    "meio of pedreiro":                        "PEDREIRO",
    "pedreiro":                                "PEDREIRO",
    "servente de obras":                       "SERVENTE_CANTEIRO",
    "servente de obra":                        "SERVENTE_CANTEIRO",
    "servente":                                "SERVENTE_CANTEIRO",
    "meio oficial de pintor":                  "PINTOR",
    "pintor de obras":                         "PINTOR",
    "pintor":                                  "PINTOR",
    "meio oficial de serralheiro":             "SERRALHEIRO",
    "serralheiro":                             "SERRALHEIRO",
    "meio oficial de eletricista":             "ELETRICISTA",
    "eletricista industrial":                  "ELETRICISTA_ENERGIZADO",
    "eletricista energizado":                  "ELETRICISTA_ENERGIZADO",
    "eletricista":                             "ELETRICISTA",
    "meio oficial de encanador":               "ENCANADOR",
    "meio of. encanador":                      "ENCANADOR",
    "meio of encanador":                       "ENCANADOR",
    "encanador":                               "ENCANADOR",
    "meio oficial de gesseiro":                "GESSEIRO",
    "gesseiro":                                "GESSEIRO",
    "impermeabilizador":                       "IMPERMEABILIZADOR",
    "aplicador de asfalto impermeabilizante":  "IMPERMEABILIZADOR",
    "aplicador asfalto impermeabilizante":     "IMPERMEABILIZADOR",
    "operador de betoneira":                   "OPERADOR_BETONEIRA",
    "operador de grua":                        "OPERADOR_GRUA",
    "operador de elevador de cremalheira":     "OPERADOR_CREMALHEIRA",
    "operador de guincho":                     "OPERADOR_CREMALHEIRA",
    "operador de cremalheira":                 "OPERADOR_CREMALHEIRA",
    "sinaleiro":                               "SINALEIRO",
    "motorista":                               "MOTORISTA",
    "mecanico de manutencao":                  "MECANICO_MANUTENCAO",
    "mecanico":                                "MECANICO_MANUTENCAO",
    "soldador":                                "SOLDADOR",
}


def _detectar_cargo_chave(cargo: str) -> str | None:
    n = _norm(cargo)
    # Exact match first
    if n in _MAPA_CARGO:
        return _MAPA_CARGO[n]
    # Longest prefix match
    for key in sorted(_MAPA_CARGO, key=len, reverse=True):
        if n.startswith(key) or key == n:
            return _MAPA_CARGO[key]
    return None


# ─── Cargos conhecidos para regex de detecção ────────────────────────────────

_CARGOS_LISTA = [
    # Ordem: mais longo/específico primeiro (evita match parcial)
    "Aplicador de asfalto impermeabilizante",
    "Operador de elevador de cremalheira",
    "Meio Oficial de Carpinteiro", "Meio oficial de carpinteiro",
    "Meio Of. Carpinteiro",        "Meio Of Carpinteiro",
    "Meio Oficial de Armador",     "Meio oficial de armador",
    "Meio Of. Armador",            "Meio Of Armador",
    "Meio Oficial De Pedreiro",    "Meio Oficial de Pedreiro", "Meio oficial de pedreiro",
    "Meio Of. Pedreiro",           "Meio Of Pedreiro",
    "Meio Oficial de Encanador",   "Meio Oficial De Encanador", "Meio oficial de encanador",
    "Meio Of. Encanador",
    "Meio Oficial de Serralheiro", "Meio oficial de serralheiro",
    "Meio Oficial De Pintor",      "Meio Oficial de Pintor",    "Meio oficial de pintor",
    "Meio Oficial de Gesseiro",    "Meio oficial de gesseiro",
    "Meio Oficial de Eletricista", "Meio oficial de eletricista",
    "Auxiliar administrativo de obras",
    "Auxiliar administrativo",     "Auxiliar Administrativo",
    "Administrativo de obra",      "Administrativo de obras",
    "Técnico de segurança do trabalho", "Técnico de Segurança do Trabalho",
    "Tecnico de seguranca do trabalho",
    "Técnico de segurança",        "Técnico de Segurança",
    "Mestre de obra",              "Mestre de obras",
    "Encarregado de pedreiro",     "Encarregado de Pedreiro",
    "Encarregado de pintor",       "Encarregado de Pintor",
    "Encarregado de Eletricista",  "Encarregado de eletricista",
    "Encarregado de Encanador",    "Encarregado de encanador",
    "Encarregado de serralheiro",  "Encarregado de carpinteiro",
    "Encarregado de armador",
    "Encarregado",
    "Operador de betoneira",       "Operador de Betoneira",
    "Operador de Grua",            "Operador de grua",
    "Operador de cremalheira",
    "Jovem aprendiz",
    "Engenheiro civil",            "Engenheiro Civil",        "Engenheiro",
    "Estagiário",                  "Estagiária",
    "Carpinteiro",
    "Armador",
    "Pedreiro",
    "Servente",
    "Serralheiro",
    "Eletricista industrial",   # must precede "Eletricista"
    "Eletricista",
    "Encanador",
    "Pintor",
    "Gesseiro",
    "Impermeabilizador",
    "Almoxarife",
    "Porteiro",
    "Vigia",
    "Sinaleiro",
    "Motorista",
    "Mecânico de manutenção",   # must precede "Mecânico"
    "Mecanico de manutencao",
    "Mecânico",
    "Mecanico",
    "Soldador",
    "Aprendiz",
]

# Sorted longest-first to avoid partial matches
_CARGOS_LISTA.sort(key=len, reverse=True)

_CARGO_RE = re.compile(
    r"^(" + "|".join(re.escape(c) for c in _CARGOS_LISTA) + r")\s+",
    re.IGNORECASE | re.UNICODE,
)


# ─── Parsing de exames ────────────────────────────────────────────────────────

# Matches exam entries in the format:
#   ExamName (N meses) (ADM, PER, MRO, ...)
#   ExamName (N meses), (ADM, PER, MRO, ...)
#   ExamName semestral-P
#   ExamName (N meses, P)
_RE_EXAME = re.compile(
    # Exam name: starts with capital/accented letter, not a momentos abbreviation
    r"(?<![a-záéíóúâêîôûãõàèùçñ])"
    r"([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÙÇÑ]"
    r"(?!DM\b|EM\b|RO\b|ET\b)[^\n]*?)"
    r"\s*"
    # Period: (N meses) or (0N meses)
    r"(?:"
        r"\(\s*(0?[0-9]+)\s*meses?\s*\)"
        r"|semestral"
        r"|anual"
    r")"
    # Optional momentos
    r"(?:[,\s]*\(?([^)\n]{1,200})\))?",
    re.IGNORECASE | re.UNICODE,
)

# Momentos pattern
_RE_MOMENTOS = re.compile(r"\b(ADM|PER|MRO|MUD|RET|RT|DEM|P)\b", re.IGNORECASE)


def _parse_momentos(s: str) -> dict:
    if not s:
        return {"adm": False, "mro": False, "ret": False, "dem": False}
    tokens = {t.upper() for t in _RE_MOMENTOS.findall(s)}
    only_p = tokens == {"P"}
    return {
        "adm": "ADM" in tokens and not only_p,
        "mro": ("MRO" in tokens or "MUD" in tokens) and not only_p,
        "ret": ("RET" in tokens or "RT" in tokens) and not only_p,
        "dem": "DEM" in tokens and not only_p,
    }


def _normalizar_texto_exames(text: str) -> str:
    """
    Pre-process exam text to normalize unusual formats before regex matching.

    1. "(N meses, P)" → "(N meses) (P)"    [combined period+moment parens]
    2. "semestral-P" → "(6 meses) (P)"     [semestral keyword]
    3. "anual" (isolated) → "(12 meses)"   [anual keyword]
    4. Lines starting with lowercase note-words but ending in momentos
       → keep only the momentos fragment at end.
    """
    # Normalize combined paren: (6 meses, P) → (6 meses) (P)
    text = re.sub(
        r"\(\s*(\d+)\s*meses?,?\s*([APMROD,\s]{1,30})\)",
        lambda m: f"({m.group(1)} meses) ({m.group(2).strip()})",
        text, flags=re.IGNORECASE,
    )
    # semestral-P  or  semestral (P) → (6 meses) (P)
    text = re.sub(r"\bsemestral\s*[-–]\s*P\.?\b", "(6 meses) (P)", text, flags=re.IGNORECASE)
    text = re.sub(r"\bsemestral\b", "(6 meses)", text, flags=re.IGNORECASE)
    # Note-lines starting with lowercase that end with momentos+closing paren
    # e.g.: "abaixo de 10 % limite de tolerância da ACGIH MRO, DEM);"
    # → keep only the trailing momentos fragment.
    # CRITICAL: never strip lines that contain "(N meses)" — those have real exam content.
    def _strip_note_prefix(m):
        line = m.group(0)
        # Guard: presence of "(N meses)" means real exam content — never alter it
        if re.search(r"\(\d+\s*meses?\)", line, re.IGNORECASE):
            return " " + line
        # Pure note line: keep only the trailing momentos fragment
        tail = re.search(r"((?:ADM|PER|MRO|RET|DEM|RT)[^)]*\))", line, re.IGNORECASE)
        if tail:
            return " " + tail.group(1)
        return " " + line
    text = re.sub(
        r"(?m)^[a-z\xe0-\xff][^\n]{10,}",
        _strip_note_prefix,
        text,
    )
    return text


def _parse_exames(text: str) -> list:
    """Extract exam entries from a cargo section text block."""
    # Pre-process to normalize formats
    text = _normalizar_texto_exames(text)

    exames = []
    vistos: set[str] = set()

    for m in _RE_EXAME.finditer(text):
        nome_raw = m.group(1).strip().rstrip(",;: ")
        per_str  = m.group(2)
        mom_str  = m.group(3) or ""

        # Determine period
        if per_str:
            per = str(int(per_str))          # strip leading zeros: "06" → "6"
        else:
            hit = m.group(0).lower()
            per = "6" if "semestral" in hit else "12"

        # Clean name: remove parenthetical fragments and trailing junk
        nome = re.sub(r"\([^)]*\)", "", nome_raw).strip().rstrip(",;:")
        nome = re.sub(r"\s{2,}", " ", nome).strip()

        # Skip bogus names
        if len(nome) < 3:
            continue
        # Skip if name starts with momentos abbreviations
        if re.match(r"^(?:DEM|ADM|PER|MRO|RET|RT|MUD)\b", nome, re.IGNORECASE):
            continue
        # Skip parenthetical fragments
        if nome.startswith("("):
            continue
        # Skip if name is clearly a note or instruction
        if re.match(r"(?i)^(ruido|incluir|nota|obs|risco|abaixo|nivel|acao)", nome):
            continue

        momentos = _parse_momentos(mom_str)
        chave_dedup = _norm(nome)
        if chave_dedup in vistos:
            continue
        vistos.add(chave_dedup)

        exames.append({
            "nome": nome,
            "adm":  momentos["adm"],
            "per":  per,
            "mro":  momentos["mro"],
            "ret":  momentos["ret"],
            "dem":  momentos["dem"],
        })

    return exames


# ─── Extração e pré-processamento do PDF ─────────────────────────────────────

# Cabeçalho que se repete em cada página — remove APENAS as 6 linhas do header,
# NÃO o conteúdo que vem depois (que pode ser continuação de exames de página anterior).
#
# Estrutura exata do header:
#   SISTEMA DE GESTÃO DA QUALIDADE - NBR ISO 9001:2015
#   RQ – REGISTRO DA QUALIDADE
#   Identificação: Página:
#   MATRIZ FUNÇÃO – EXAMES PCMSO RQ.61 N / 15
#   Revisão: Versão:
#   11/11/2024 05
_RE_HEADER = re.compile(
    r"SISTEMA DE GEST[AÃ]O DA QUALIDADE[^\n]*\n"
    r"RQ[^\n]*\n"
    r"Identifica[^\n]*\n"
    r"MATRIZ[^\n]*\n"
    r"Revis[^\n]*\n"
    r"\d{2}/\d{2}/\d{4}[^\n]*\n",
    re.IGNORECASE,
)


def extrair_texto_pdf(pdf_path: Path) -> str:
    """Concatenate and clean text from all pages."""
    paginas = []
    with pdfplumber.open(pdf_path) as pdf:
        for pg in pdf.pages:
            t = pg.extract_text() or ""
            paginas.append(t)

    texto = "\n".join(paginas)

    # Remove the 6-line page header that repeats on every page.
    # IMPORTANT: only removes the header block itself, NOT subsequent content
    # (which may be exam continuations from the previous page).
    texto = _RE_HEADER.sub("\n", texto)

    # Remove page 1 intro block (company info, doctor name, etc.)
    # Everything before the first GHE header
    m_first_ghe = re.search(r"GHE\s+\d+\s*:", texto, re.IGNORECASE)
    if m_first_ghe:
        texto = texto[m_first_ghe.start():]

    return texto


# ─── Regex para encontrar headers de GHE ──────────────────────────────────────

_RE_GHE_HEADER = re.compile(
    r"(?m)^GHE\s+\d+\s*[:\-–—]\s*(.+?)$",
    re.UNICODE,
)

# Lines to skip inside GHE blocks (column header, page numbers, etc.)
_RE_SKIP_LINE = re.compile(
    r"(?i)^("
    r"fun[cç][aã]o\s+exames"
    r"|exames\s+solicitados"
    r"|fun[cç][aã]o"
    r"|\d+\s*/\s*\d+"              # page numbers like "1 / 15"
    r"|revisao|revisão"
    r"|vers[aã]o"
    r")\s*:?\s*$"
)


def _preprocessar_linha(linha: str, current_exame_text: str) -> str:
    """
    Handle the two-column layout where left-column notes appear before
    right-column exam continuation on the same extracted line.

    Returns the text to append to current_exame_text, or "" to skip.
    """
    stripped = linha.strip()

    if not stripped:
        return ""

    # Skip column header and page info lines
    if _RE_SKIP_LINE.match(stripped):
        return ""

    # Lines starting with '(' are left-column parenthetical notes
    # e.g.: "(Ruído abaixo do nível de ação). DEM), Acuidade Visual (12 meses)"
    # Extract everything after "). " (right column content)
    if stripped.startswith("("):
        m = re.search(r"\)\s*\.?\s+(.+)$", stripped)
        if m:
            return " " + m.group(1)
        return ""  # pure note with no right-column content

    # Lines starting with "Incluir" / "Incluir no PCMSO" are left-column instructions
    # e.g.: "Incluir no PCMSO em word-Risco Cromo DEM), Acuidade Visual (12 meses)"
    if re.match(r"(?i)^(incluir|nota\s*:|obs\.?:?)", stripped):
        # Try to find right-column content: momentos fragment or capitalized exam
        m = re.search(
            r"(?:DEM|ADM|MRO|RET)\s*\)[\s,]*(.+)$",
            stripped, re.IGNORECASE,
        )
        if m:
            return " DEM) " + m.group(1)   # prepend the momentos fragment
        # Look for a capitalized exam name starting mid-line
        m = re.search(
            r"\.\s+([A-ZÁÉÍÓÚÂÊÎÔÛÃÕÀÈÙÇÑ][a-záéíóúâêîôûãõàèùçñ].+(?:\d+\s*mes|\d+\s*meses)).*$",
            stripped, re.IGNORECASE,
        )
        if m:
            return " " + m.group(1)
        return ""

    return " " + stripped


# ─── Parser de blocos GHE ────────────────────────────────────────────────────

def parsear_ghe_blocos(texto: str) -> list[tuple[str, str]]:
    """Split text into GHE blocks. Returns [(titulo, block_text), ...]."""
    headers = list(_RE_GHE_HEADER.finditer(texto))
    blocos = []
    for i, m in enumerate(headers):
        titulo = m.group(1).strip()
        start  = m.end()
        end    = headers[i + 1].start() if i + 1 < len(headers) else len(texto)
        blocos.append((titulo, texto[start:end]))
    return blocos


# ─── Parser de seções de cargo ───────────────────────────────────────────────

def parsear_cargo_secoes(block_text: str) -> list[tuple[str, str]]:
    """
    Split a GHE block into cargo sections using line-by-line state machine.
    Returns [(cargo_raw, joined_exame_text), ...].
    """
    linhas = block_text.split("\n")
    secoes: list[tuple[str, str]] = []
    current_cargo: str | None     = None
    current_text:  str            = ""

    for linha in linhas:
        stripped = linha.strip()
        if not stripped:
            continue

        # Try to match a cargo name at the start of the line
        m = _CARGO_RE.match(stripped)
        if m:
            if current_cargo is not None:
                secoes.append((current_cargo, current_text.strip()))
            current_cargo = m.group(1)
            # Rest of line after the cargo name = first exam fragment
            rest = stripped[m.end():].strip()
            current_text  = rest
            continue

        if current_cargo is None:
            continue

        extra = _preprocessar_linha(linha, current_text)
        current_text += extra

    if current_cargo is not None:
        secoes.append((current_cargo, current_text.strip()))

    return secoes


# ─── Migração principal ───────────────────────────────────────────────────────

def migrar(
    pdf_path:  Path = PDF_PATH,
    json_path: Path = JSON_PATH,
) -> dict:
    """Parse PDF and write banco_ghe_cargo_v1.json. Returns the banco dict."""
    print(f"📄 Lendo PDF: {pdf_path.name}")
    texto  = extrair_texto_pdf(pdf_path)
    blocos = parsear_ghe_blocos(texto)
    print(f"   GHE blocks encontrados: {len(blocos)}")

    banco:           dict = {}
    sem_chave_ghe:   list = []
    sem_chave_cargo: list = []

    for titulo, block_text in blocos:
        chave_ghe = _detectar_chave_ghe(titulo)
        if not chave_ghe:
            sem_chave_ghe.append(titulo)
            continue

        secoes = parsear_cargo_secoes(block_text)
        for cargo_raw, exame_text in secoes:
            chave_cargo = _detectar_cargo_chave(cargo_raw)
            if not chave_cargo:
                sem_chave_cargo.append(f"[{chave_ghe}] {cargo_raw!r}")
                continue

            chave = f"{chave_ghe}:{chave_cargo}"
            exames = _parse_exames(exame_text)

            if not exames:
                # Log but don't skip – keep entry so tests can detect missing data
                print(f"   ⚠️  Sem exames parseados: {chave}")

            # Merge: se chave já existe, consolida exames (evita sobrescrever
            # a versão mais completa quando cargo aparece em dois GHEs com mesmo nome)
            if chave in banco:
                nomes_atuais = {_norm(e["nome"]) for e in banco[chave]["exames"]}
                for ex in exames:
                    if _norm(ex["nome"]) not in nomes_atuais:
                        banco[chave]["exames"].append(ex)
            else:
                banco[chave] = {
                    "ghe_descricao": titulo,
                    "cargo":         cargo_raw,
                    "exames":        exames,
                    "fonte":         "RQ.61 Viverde 06.03.2025",
                }

    # Report unmapped items
    if sem_chave_ghe:
        print(f"\n⚠️  GHEs sem chave semântica ({len(sem_chave_ghe)}):")
        for t in sem_chave_ghe:
            print(f"   • {t!r}")

    if sem_chave_cargo:
        print(f"\n⚠️  Cargos sem chave ({len(sem_chave_cargo)}):")
        for c in sem_chave_cargo:
            print(f"   • {c}")

    print(f"\n✅ Total de entradas geradas: {len(banco)}")

    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(banco, f, ensure_ascii=False, indent=2)
    print(f"💾 Gravado em: {json_path}")

    return banco


if __name__ == "__main__":
    migrar()
