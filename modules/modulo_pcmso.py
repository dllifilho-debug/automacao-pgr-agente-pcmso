# =============================================================================
# MÓDULO PCMSO v7.5 — OCR seletivo + parser 2 passagens + AgenteMedicoIA
# Funções públicas:
#   extrair_texto_pdf, extrair_pgr_com_fallback, enriquecer_pgr_com_fispq,
#   processar_pcmso, gerar_html_pcmso, gerar_docx_rq61
#
# v7.5 — parser em 2 passagens:
#   Passagem 1: coleta cargos da seção "FUNÇÕES EXISTENTES NO CANTEIRO" (antes dos GHEs)
#   Passagem 2: parseia GHEs e injeta os cargos coletados quando o GHE não tiver cargos próprios
#   Isso resolve PDFs no formato Viverde/CMO onde cargos aparecem ANTES dos blocos GHE
# =============================================================================

import io
import os
import re
import unicodedata
from copy import deepcopy
from datetime import date

import pandas as pd

VERSAO_MODULO_PCMSO = "7.5 (parser 2 passagens + OCR seletivo + AgenteMedicoIA)"

# ---------------------------------------------------------------------------
# Import do Agente Médico IA (opcional)
# ---------------------------------------------------------------------------
try:
    from modules.agente_medico_ia import processar_cargo_ia
    _AGENTE_IA_DISPONIVEL = True
except ImportError:
    try:
        from agente_medico_ia import processar_cargo_ia
        _AGENTE_IA_DISPONIVEL = True
    except ImportError:
        _AGENTE_IA_DISPONIVEL = False

try:
    from data.dicionario_cas import DICIONARIO_CAS
except ImportError:
    DICIONARIO_CAS = {}


# ============================================================================
# 1 — EXTRACAO DE TEXTO DO PDF  (pdfplumber → PyMuPDF → OCR)
# ============================================================================

_MIN_CHARS_POR_PAGINA = 150

_ASSINATURA_KEYWORDS = [
    "autenticação eletrônica",
    "autenticacao eletronica",
    "página de assinaturas",
    "pagina de assinaturas",
    "hash sha256",
    "identificador:",
    "clicksign",
    "docusign",
    "signatário",
    "signatario",
    "escaneie a imagem para verificar",
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
    """
    Fallback OCR com lazy imports.
    - Pula ultima pagina se for ClickSign/DocuSign.
    - DPI adaptativo: 200 para PDFs >50 paginas, 250 para menores.
    - Progresso via st.progress() quando Streamlit disponivel.
    """
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
        import numpy as np
        _cv2_ok = True
    except ImportError:
        pass

    for i, img in enumerate(paginas_processar):
        try:
            if _cv2_ok:
                img_array = __import__("numpy").array(img.convert("RGB"))
                cinza = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
                _, binaria = cv2.threshold(cinza, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
                from PIL import Image
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
    """
    3 camadas de extracao:
    1. pdfplumber
    2. PyMuPDF (fitz)
    3. OCR via pdf2image + pytesseract
    """
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
# 2 — PARSER LOCAL DE PGR  (v7.5 — 2 passagens para formato Viverde/CMO)
# ============================================================================

def _normalizar(texto: str) -> str:
    if not texto:
        return ""
    nfkd = unicodedata.normalize("NFKD", str(texto))
    return nfkd.encode("ASCII", "ignore").decode("ASCII").lower().strip()


# Cargos conhecidos de canteiro de obras (normalizados)
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
}

# Regex GHE: captura 'GHE 01-', 'GHE 01 -', 'GHE01:', 'GRUPO HOMOGENEO...'
_RE_GHE = re.compile(
    r"(?i)^(?:GHE\s*\d*\s*[-\u2013:]?\s*"
    r"|GRUPO\s+HOMOG[E\u00ca]NEO\s+DE\s+EXPOSI[\u00c7C][\u00c3A]O\s*[-\u2013:]?\s*)(.+)$"
)

# Regex agente: quimico, fisico, biologico, ergonomico, acidente
_RE_AGENTE = re.compile(
    r"(?i)^agente\s*(?:qu[i\u00ed]mico|f[i\u00ed]sico|biol[o\u00f3]gico"
    r"|ergon[o\u00f4]mico|de\s+acidente|de\s+risco)?\s*[:\-\u2013]?\s*(.+)$"
)

# Cabecalho da tabela de funcoes (marca inicio da secao de cargos globais)
_RE_SECAO_FUNCOES = re.compile(
    r"(?i)^(fun[c\u00e7][o\u00f5]es\s*(existentes)?\s*(no\s+canteiro)?|"
    r"fun[c\u00e7][o\u00f5]es\s+quantidade|"
    r"cargo[s]?\s+cbo|"
    r"fun[c\u00e7][o\u00f5]es\s+existentes)"
)

# Linhas que nunca sao cargos
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


def _identificar_cargo(linha: str) -> str | None:
    """
    Tenta identificar se a linha representa um cargo.
    Estrategia 1: cargo conhecido no _CARGOS_CANTEIRO
    Estrategia 2: 'NOME QTD' (ex: 'Pedreiro 15') -> remove QTD e verifica
    Estrategia 3: heuristica por formato (2-5 palavras, inicia maiuscula, sem pontuacao)
    """
    ls = linha.strip()
    if not ls:
        return None

    # Filtra linhas que definitivamente nao sao cargos
    if _RE_SKIP.match(_normalizar(ls)):
        return None

    # Ignora linhas de agente (tratadas separadamente)
    if re.match(r"(?i)^agente\s", ls):
        return None

    # Ignora linhas de risco/perigo/medida/NR
    if re.match(r"(?i)^(risco|perigo|medida|a[c\u00e7][a\u00e3]o|nr[-\s]\d|epis?\s|epc\s)", ls):
        return None

    # Remove numero do final: "Pedreiro 15" -> "Pedreiro", "Mestre de Obras 01" -> "Mestre de Obras"
    nome_sem_qtd = re.sub(r"\s+\d{1,3}\s*$", "", ls).strip()

    # Estrategia 1 + 2: verifica no set de cargos conhecidos
    nome_n = _normalizar(nome_sem_qtd)
    if nome_n in _CARGOS_CANTEIRO:
        return nome_sem_qtd

    # Tambem testa o nome original (sem remocao de numero) por seguranca
    if _normalizar(ls) in _CARGOS_CANTEIRO:
        return ls

    # Estrategia 3: heuristica
    palavras = nome_sem_qtd.split()
    if (
        2 <= len(palavras) <= 5
        and not re.search(r"[;:,./\(\)]", nome_sem_qtd)
        and not re.match(r"(?i)^(agente|risco|perigo|medida|acao|nr[-\s]|epi|epc|uso|utilize|verifique)", nome_sem_qtd)
        and re.match(r"^[A-Z\u00c0-\u00da][a-zA-Z\u00c0-\u00ff\s.]+$", nome_sem_qtd)
        and len(nome_sem_qtd) >= 5
    ):
        return nome_sem_qtd

    return None


def _coletar_cargos_globais(linhas: list) -> list:
    """
    PASSAGEM 1: Varre o texto ANTES dos GHEs e coleta todos os cargos
    da seção 'FUNÇÕES EXISTENTES NO CANTEIRO DE OBRAS'.
    Retorna lista de cargos encontrados (sem duplicatas).
    """
    cargos = []
    vistos = set()
    em_secao_funcoes = False

    for linha in linhas:
        ls = linha.strip()
        if not ls:
            continue

        # Detecta inicio da secao de funcoes
        if _RE_SECAO_FUNCOES.match(ls):
            em_secao_funcoes = True
            continue

        # Para de coletar ao encontrar o primeiro GHE
        if _RE_GHE.match(ls):
            break

        # Para se encontrar outra secao numerada principal (ex: "9. ...")
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
    """
    Parser em 2 passagens:
    1. Coleta cargos globais da seção FUNÇÕES antes dos GHEs
    2. Parseia blocos GHE e injeta cargos globais quando bloco não tem cargos próprios
    """
    linhas = texto.split("\n")

    # --- PASSAGEM 1: cargos globais ---
    cargos_globais = _coletar_cargos_globais(linhas)

    # --- PASSAGEM 2: blocos GHE ---
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

        # Testa agente primeiro
        m_ag = _RE_AGENTE.match(ls)
        if m_ag:
            bloco_atual["riscos_mapeados"].append(
                {"nome_agente": m_ag.group(1).strip(), "perigo_especifico": ""}
            )
            continue

        # Testa cargo dentro do proprio bloco GHE
        cargo = _identificar_cargo(ls)
        if cargo and cargo not in bloco_atual["cargos"]:
            bloco_atual["cargos"].append(cargo)

    if bloco_atual:
        blocos.append(bloco_atual)

    # --- INJECAO: distribui cargos globais para GHEs sem cargos proprios ---
    if cargos_globais:
        for bloco in blocos:
            if not bloco["cargos"]:
                bloco["cargos"] = list(cargos_globais)

    return blocos


def extrair_pgr_com_fallback(texto_pgr: str):
    try:
        from parser_pgr import parsear_pgr_texto
        resultado = parsear_pgr_texto(texto_pgr)
        if resultado:
            return resultado, "local"
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


def _resolver_exames_cargo(cargo, riscos_str, contexto, e_canteiro):
    if _AGENTE_IA_DISPONIVEL:
        resultado = processar_cargo_ia(
            cargo=cargo, riscos=riscos_str, contexto=contexto, e_canteiro=e_canteiro,
        )
        return resultado.get("exames", []), resultado.get("chave_mestra", "")
    base = deepcopy(_EXAMES_MINIMOS_CANTEIRO if e_canteiro else _EXAMES_MINIMOS_ESCRIT)
    return base, None


# ============================================================================
# 5 — processar_pcmso
# ============================================================================

def processar_pcmso(dados_ghe: list, tipo_ambiente: str = "canteiro") -> pd.DataFrame:
    linhas = []
    for ghe_item in dados_ghe:
        nome_ghe        = ghe_item.get("ghe") or ghe_item.get("nome_ghe") or "GHE sem nome"
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
            if exames_pre:
                exames_base = deepcopy(exames_pre) if isinstance(exames_pre[0], dict) else [
                    {"nome": str(e), "adm": True, "per": "12", "mro": True, "ret": False, "dem": False}
                    for e in exames_pre
                ]
                if _AGENTE_IA_DISPONIVEL:
                    res_ia = processar_cargo_ia(cargo=cargo, riscos=riscos_str, contexto=contexto, e_canteiro=e_canteiro)
                    nomes_ok = {_normalizar(e.get("nome", "")) for e in exames_base}
                    for ex in res_ia.get("exames", []):
                        if _normalizar(ex.get("nome", "")) not in nomes_ok:
                            exames_base.append(ex)
                            nomes_ok.add(_normalizar(ex.get("nome", "")))
                    fonte = f"banco+agente_ia:{res_ia.get('chave_mestra', '')}"
                else:
                    fonte = "banco_pre_definido"
                exames_finais = exames_base
            else:
                exames_finais, chave = _resolver_exames_cargo(cargo, riscos_str, contexto, e_canteiro)
                fonte = f"agente_ia:{chave}" if _AGENTE_IA_DISPONIVEL else "fallback_minimo"

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
    return pd.DataFrame(linhas) if linhas else pd.DataFrame(columns=cols)


# ============================================================================
# 6 — gerar_html_pcmso
# ============================================================================

def gerar_html_pcmso(df: pd.DataFrame, cabecalho: dict = None) -> str:
    if cabecalho is None:
        cabecalho = {}
    cs = "border:1px solid #ccc;padding:6px 8px;font-size:12px;"
    th = f"{cs}background:#084D22;color:white;text-align:center;"
    cols = ["GHE / Setor", "Cargo", "Exame", "ADM", "PER", "MRO", "RT", "DEM"]
    hoje = date.today().strftime("%d/%m/%Y")

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
      <thead><tr>{''.join(f'<th style="{th}">{c}</th>' for c in cols)}</tr></thead><tbody>
    """
    rows = "".join(
        "<tr>" + "".join(f"<td style='{cs}'>{row.get(c,'') if c in df.columns else ''}</td>" for c in cols) + "</tr>\n"
        for _, row in df.iterrows()
    )
    return f"<!DOCTYPE html><html><body>{cab_html}{rows}</tbody></table><p style='font-size:11px;color:#888;text-align:center;'>Gerado pelo Sistema SST Seconci GO | {hoje}</p></div></body></html>"


# ============================================================================
# 7 — gerar_docx_rq61
# ============================================================================

def gerar_docx_rq61(df: pd.DataFrame, cabecalho: dict = None) -> bytes:
    if cabecalho is None:
        cabecalho = {}
    try:
        from docx import Document
        from docx.shared import RGBColor, Cm
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

    colunas = ["GHE / Setor", "Cargo", "Exame", "ADM", "PER", "MRO", "RT", "DEM"]
    t = doc.add_table(rows=1, cols=len(colunas))
    t.style = "Table Grid"
    for i, col in enumerate(colunas):
        p = t.rows[0].cells[i].paragraphs[0]
        run = p.add_run(col)
        run.bold = True
        run.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
        tcp = t.rows[0].cells[i]._tc.get_or_add_tcPr()
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "084D22")
        shd.set(qn("w:color"), "auto")
        shd.set(qn("w:val"), "clear")
        tcp.append(shd)

    for _, row in df.iterrows():
        cells = t.add_row().cells
        for i, col in enumerate(colunas):
            cells[i].text = str(row.get(col, "")) if col in df.columns else ""

    buf = io.BytesIO()
    doc.save(buf)
    return buf.getvalue()
