import re
import io
import unicodedata
from pathlib import Path


TERMOS_PARA_CHAVE = {
    r"ru[ii]do": "RUIDO",
    r"vibra.{0,10}corpo.*inteiro": "VIBRACAO_CORPO_INTEIRO",
    r"trabalho em altura": "TRABALHO_EM_ALTURA_ESPACO_CONFINADO_MOTORISTA",
    r"espaco confinado": "ESPACO_CONFINADO",
    r"eletricidade|energia eletrica|choque eletrico": "PORTEIRO_ELETRICIDADE_ALTURA_MOTORISTA",
    r"risco psicossocial|psicossocial": "TRABALHO_EM_ALTURA_MAQUINAS_PESADAS_PSICOSSOCIAL",
    r"poeira.*madeira|madeira.*poeira": "POEIRA_PNOS_GESSO_MADEIRA_METALICA",
    r"poeira.*gesso|gesso.*poeira": "POEIRA_PNOS_GESSO_MADEIRA_METALICA",
    r"poeira.*metalica|fumos metalicos|fumo metalico": "POEIRA_PNOS_GESSO_MADEIRA_METALICA",
    r"pnos|fibra.*vidro|talco\b": "POEIRA_PNOS_GESSO_MADEIRA_METALICA",
    r"silica|quartzo|abesto|amianto": "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA",
    r"operador.*betoneira|betoneira": "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA",
    r"azulej": "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA",
    r"poeira.*mineral": "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA",
    r"tinta[s]?\b|nevoa|neblina": "NEVOAS_TINTAS_COLAS_IMPERMEABILIZACAO",
    r"cola[s]?\b|adesivo\b": "NEVOAS_TINTAS_COLAS_IMPERMEABILIZACAO",
    r"impermeabiliz": "NEVOAS_TINTAS_COLAS_IMPERMEABILIZACAO",
    r"cimento.*sem.*silica": "CONTATO_QUIMICOS_AGRESSORES_PULMONARES",
    r"mascara.*respiratoria.*epi": "USO_MASCARA_EPI_SEM_RISCO_QUIMICO",
    r"tricloroetileno|tricloroetano": "TRICLOROETILENO",
    r"benzeno\b": "BENZENO",
    r"tolueno\b": "TOLUENO",
    r"xileno\b": "XILENO",
    r"estireno\b": "ESTIRENO",
    r"fenol\b": "FENOL",
    r"monoxido.*carbono": "MONOXIDO_DE_CARBONO",
    r"manganes\b": "MANGANES",
    r"cromo.*hexavalente|cromo.*vi\b": "CROMO_HEXAVALENTE",
    r"fluoreto|acido fluoridrico": "FLUOR_ACIDO_FLUORIDRICO_FLUORETOS",
    r"metil.etil.cetona|mek\b": "METIL_ETIL_CETONA",
    r"acetona\b": "ACETONA",
    r"tetrahidrofurano|thf\b": "TETRAHIDROFURANO",
    r"cicloexanona|ciclohexanona": "CICLOEXANONA",
    r"policorte|corte.*plasma|plasma.*corte|solda\b": "POLICORTE_SOLDA",
    r"trabalhad.*saude|saude.*trabalhad": "TRABALHADORES_DA_SAUDE",
    r"manipul.*alimento|alimento.*manipul": "MANIPULAR_ALIMENTOS",
}

OTOTOXICOS_COM_BIOLOGICO = {
    "TOLUENO", "XILENO", "ESTIRENO",
    "TRICLOROETILENO", "MONOXIDO_DE_CARBONO", "MANGANES",
}

# Codigos eSocial -> chave interna
ESOCIAL_PARA_CHAVE = {
    "02.01.001": "RUIDO",
    "02.01.002": "RUIDO",
    "02.03.001": "VIBRACAO_CORPO_INTEIRO",
    "02.03.002": "VIBRACAO_CORPO_INTEIRO",
    "01.18.001": "POEIRA_MINERAL_SILICA_QUARTZO_OPERADOR_BETONEIRA",
    "01.02.001": "NEVOAS_TINTAS_COLAS_IMPERMEABILIZACAO",
    "01.06.001": "BENZENO",
    "01.06.002": "TOLUENO",
    "01.06.003": "XILENO",
    "01.06.004": "ESTIRENO",
    "01.06.011": "MONOXIDO_DE_CARBONO",
    "01.06.019": "MANGANES",
    "01.06.020": "CROMO_HEXAVALENTE",
    "01.06.031": "TRICLOROETILENO",
    "01.06.040": "FENOL",
    "01.06.048": "FLUOR_ACIDO_FLUORIDRICO_FLUORETOS",
}


# ------------------------------------------------------------------------------
# EXTRACAO DE TEXTO
# ------------------------------------------------------------------------------
def _eh_pdf_bloqueado(paginas_texto: list, limite_chars_media: int = 30) -> bool:
    chars = sum(len(t.strip()) for t in paginas_texto)
    return (chars / max(len(paginas_texto), 1)) < limite_chars_media


def _texto_via_pdfplumber(pdf_bytes: bytes) -> tuple:
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
            paginas = [pg.extract_text() or "" for pg in pdf.pages]
        bloqueado = _eh_pdf_bloqueado(paginas)
        return "\n".join(paginas), not bloqueado
    except Exception:
        return "", False


def _texto_via_ocr(pdf_bytes: bytes, lang: str = "por") -> str:
    try:
        import pytesseract
        from pdf2image import convert_from_bytes
        imagens = convert_from_bytes(pdf_bytes, dpi=200)
        return "\n".join(pytesseract.image_to_string(img, lang=lang) for img in imagens)
    except ImportError as e:
        raise RuntimeError(
            f"OCR indisponivel: {e}\n"
            "Instale: pip install pytesseract pdf2image\n"
            "Tesseract: https://github.com/UB-Mannheim/tesseract/wiki"
        )


def extrair_texto_pgr(pdf_bytes: bytes, forcar_ocr: bool = False) -> dict:
    """
    Extrai texto do PGR com deteccao automatica de PDF bloqueado.
    Retorna: {texto, metodo, bloqueado, aviso}
    """
    if not forcar_ocr:
        texto, sucesso = _texto_via_pdfplumber(pdf_bytes)
        if sucesso and texto.strip():
            return {"texto": texto, "metodo": "pdfplumber", "bloqueado": False, "aviso": None}
        aviso = (
            "PDF com texto bloqueado ou digitalizado detectado. "
            "Usando OCR automatico (pode ser mais lento)..."
        )
    else:
        aviso = "OCR forcado pelo usuario."
    texto = _texto_via_ocr(pdf_bytes)
    return {"texto": texto, "metodo": "ocr", "bloqueado": True, "aviso": aviso}


# ------------------------------------------------------------------------------
# DETECCAO DE FORMATO
# ------------------------------------------------------------------------------
def detectar_formato(texto: str) -> str:
    """Retorna 'GHE' ou 'CARGO' conforme o padrao dominante no documento."""
    n_ghe   = len(re.findall(r"\bGHE\s*\d+", texto, re.IGNORECASE))
    n_cargo = len(re.findall(r"\bCARGO\s+[A-Za-z\u00C0-\u00FF]", texto, re.IGNORECASE))
    return "CARGO" if n_cargo >= n_ghe else "GHE"


# ------------------------------------------------------------------------------
# NORMALIZACAO
# ------------------------------------------------------------------------------
def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


# ------------------------------------------------------------------------------
# EXTRACAO DE CARGOS DO CAMPO SETOR/FUNCAO (formato tabular Viverde/SistemaEso)
# ------------------------------------------------------------------------------
# Palavras que NAO sao cargos reais — evita poluir a lista com rubricas da tabela
_PALAVRAS_EXCLUIR_CARGO = re.compile(
    r"^(?:"
    r"estrutura\b|concreto\b|armado\b|processo\b|etapa\b|atividade[s]?\b|"
    r"inventario\b|classificacao\b|riscos\b|ocupacionais\b|pgr\b|gro\b|"
    r"versao\b|revisao\b|data\b|pagina\b|responsavel\b|avaliador\b|"
    r"atividade\s+detalhada|cbo\b|trabalho\b|habitual\b|administracao\b"
    r")$",
    re.IGNORECASE | re.UNICODE,
)


# Padr\u00E3o A: SETOR/FUNCAO (formato Viverde) \u2014 separador N\u00C3O obrigat\u00F3rio,
# j\u00E1 que o pdfplumber extrai como "SETOR/FUNCAO  Pedreiro/Servente"
_PADRAO_SETOR_FUNCAO = re.compile(
    r"SETOR[/\\]?FUN[CG\u00C7][A\u00C3]?[O\u00D5]E?S?\s+([^\n]+)",
    re.IGNORECASE,
)

# Padr\u00E3o B: cabe\u00E7alho gen\u00E9rico (Fun\u00E7\u00F5es, Cargos, Trabalhadores, etc.)
# REQUER separador (`:`, `-`, `.`) \u2014 evita falsos positivos em prosa como
# "profissionais como pedreiro" que n\u00E3o \u00E9 uma lista estruturada.
_PADRAO_CABECALHO_GENERICO = re.compile(
    r"(?:"
    r"FUN[CG\u00C7][A\u00C3]?[O\u00D5]E?S?"
    r"|CARGO[S]?"
    r"|TRABALHADOR(?:ES)?"
    r"|EMPREGADOS?"
    r"|PROFISSION(?:AL|AIS|\u00C1IS)"
    r")"
    r"(?:\s+\w+){0,3}"        # at\u00E9 3 palavras opcionais (envolvidos, existentes, etc.)
    r"\s*[:.\-\u2013]\s*"           # separador OBRIGAT\u00D3RIO
    r"([^\n]+)",
    re.IGNORECASE,
)

# Cargos conhecidos para busca por keyword no texto livre (fallback Camada 3)
_CARGOS_KEYWORDS = (
    "pedreiro", "servente", "carpinteiro", "armador", "ajudante",
    "pintor", "azulejista", "gesseiro", "encanador", "eletricista",
    "serralheiro", "soldador", "impermeabilizador",
    "almoxarife", "porteiro", "vigia", "sinaleiro", "motorista",
    "engenheiro", "estagiario", "tecnico", "encarregado", "mestre",
    "administrativo", "assistente", "auxiliar", "aprendiz",
    "topografo", "calceteiro", "mecanico", "operador",
)


def _split_e_limpar_cargos(valor: str) -> list:
    """Quebra string de cargos por / , ; ou ' e ', limpa CBO e devolve lista."""
    out = []
    partes = re.split(r"[/,;]|\s+e\s+", valor)
    for parte in partes:
        parte_limpa = re.sub(r"\b\d{5,6}\b", "", parte).strip()
        parte_limpa = re.sub(r"\s{2,}", " ", parte_limpa).strip()
        parte_limpa = parte_limpa.rstrip(".,;:")
        if 4 <= len(parte_limpa) <= 60 and not _PALAVRAS_EXCLUIR_CARGO.match(parte_limpa):
            out.append(parte_limpa)
    return out


def _extrair_cargos_do_bloco_ghe(conteudo: str) -> list:
    """
    Extrai cargos do bloco de um GHE em tr\u00EAs passadas, sempre usando APENAS
    a PRIMEIRA ocorr\u00EAncia de cada cabe\u00E7alho (evita vazamento entre blocos
    quando a delimita\u00E7\u00E3o do PDF n\u00E3o est\u00E1 limpa):

      1. Cabe\u00E7alho 'SETOR/FUNCAO' (formato Viverde, sem separador obrigat\u00F3rio)
      2. Cabe\u00E7alho gen\u00E9rico ('FUN\u00C7\u00D5ES:', 'CARGOS:', 'TRABALHADORES:', etc.)
      3. Fallback: busca por keywords de cargos conhecidos no texto livre

    A busca \u00E9 limitada aos primeiros 2000 caracteres do conteudo, j\u00E1 que o
    SETOR/FUNCAO de um GHE quase sempre aparece logo ap\u00F3s o header \u2014 qualquer
    cargo encontrado mais adiante provavelmente vazou de outro GHE.
    """
    # Limita a janela de busca aos primeiros 2000 chars (~30 linhas)
    janela = conteudo[:2000]
    cargos = []

    # Passada 1: SETOR/FUNCAO (formato Viverde) \u2014 APENAS PRIMEIRA ocorr\u00EAncia
    m = _PADRAO_SETOR_FUNCAO.search(janela)
    if m:
        cargos = _split_e_limpar_cargos(m.group(1).strip()[:200])

    # Passada 2: cabe\u00E7alho gen\u00E9rico \u2014 s\u00F3 se SETOR/FUNCAO n\u00E3o deu match
    if not cargos:
        m = _PADRAO_CABECALHO_GENERICO.search(janela)
        if m:
            cargos = _split_e_limpar_cargos(m.group(1).strip()[:200])

    # Passada 3: fallback por keyword (s\u00F3 se nenhum cabe\u00E7alho trouxe nada)
    if not cargos:
        texto_n = _normalizar(janela)
        for kw in _CARGOS_KEYWORDS:
            for match in re.finditer(
                rf"\b{re.escape(kw)}\b(?:\s+de\s+[a-z\u00E0-\u00FF]+\b)?",
                texto_n,
            ):
                valor = match.group(0).strip()
                valor = " ".join(w.capitalize() for w in valor.split())
                if 5 <= len(valor) <= 60 and valor not in cargos:
                    cargos.append(valor)

    return list(dict.fromkeys(cargos))


# ------------------------------------------------------------------------------
# EXTRATORES DE BLOCOS
# ------------------------------------------------------------------------------
def extrair_blocos_ghe(texto: str) -> dict:
    """
    Divide o texto em blocos por GHE.

    Suporta dois formatos:
      1. Formato inline:  "GHE 01 - Almoxarifado"  (nome na mesma linha)
      2. Formato tabular: "GHE  01" em linha propria, nome/cargos no campo SETOR/FUNCAO

    Retorna dict: {chave_ghe -> {"conteudo": str, "cargos": list}}
    """
    # Aceita: GHE 01, GHE  01, GHE01 — com ou sem nome inline
    padrao = re.compile(
        r"(GHE\s*\d+(?:\s*[-:\u2013\u2014]+\s*[^\n]{3,80})?)",
        re.IGNORECASE,
    )
    # NOTE: o split-by-regex foi substituído por parsing LINHA-A-LINHA abaixo.
    # Mantemos `padrao` sem uso para registro histórico do bug; será removido
    # quando confirmarmos estabilidade do novo método em produção.
    _ = padrao

    re_ghe_inicio_linha = re.compile(
        r"^[\s\d.•*\-]*?(GHE)\s*(\d+)\s*([-:–—][^\n]{0,200})?\s*$",
        re.IGNORECASE,
    )

    blocos_ord = []
    nome_atual = None
    conteudo_atual = []

    def fechar_bloco():
        nonlocal nome_atual, conteudo_atual
        if nome_atual is None:
            return
        conteudo = "\n".join(conteudo_atual)
        cargos = _extrair_cargos_do_bloco_ghe(conteudo)
        blocos_ord.append((nome_atual, conteudo, cargos))
        nome_atual = None
        conteudo_atual = []

    for linha in texto.split("\n"):
        m = re_ghe_inicio_linha.match(linha)
        if m:
            fechar_bloco()
            num = int(m.group(2))
            desc_raw = (m.group(3) or "").strip()
            desc = re.sub(r"^[-:–—\s]+", "", desc_raw).strip()[:200]
            nome_atual = f"GHE {num:02d}" + (f" - {desc}" if desc else "")
            nome_atual = re.sub(r"\s{2,}", " ", nome_atual).strip()
            continue
        if nome_atual is not None:
            conteudo_atual.append(linha)

    fechar_bloco()

    # Consolida duplicatas: mesmo "GHE NN" aparecendo 2x agora JUNTA conteúdo
    # e cargos, em vez de sobrescrever (que perdia o primeiro bloco silenciosamente).
    blocos = {}
    for nome, conteudo, cargos in blocos_ord:
        if nome in blocos:
            blocos[nome]["conteudo"] += "\n" + conteudo
            blocos[nome]["cargos"] = list(
                dict.fromkeys(blocos[nome]["cargos"] + cargos)
            )
        else:
            blocos[nome] = {"conteudo": conteudo, "cargos": cargos}
    return blocos


def extrair_blocos_cargo(texto: str) -> dict:
    """
    Divide o texto em blocos por CARGO <NOME> (formato CARGO/CBO).
    Retorna dict: {chave_cargo -> {"conteudo": str, "cargos": list}}
    """
    padrao = re.compile(
        r"(CARGO[ \t]+[A-Za-z\u00C0-\u00FF][A-Za-z\u00C0-\u00FF \t\/\-]*?"
        r"(?:[ \t]*[-\u2013][ \t]*CBO[: \t]*\d{6})?)[ \t]*[\r\n]",
        re.IGNORECASE,
    )
    partes = padrao.split(texto)
    blocos = {}
    for i in range(1, len(partes), 2):
        nome = re.sub(r"\s+", " ", partes[i]).strip()
        conteudo = partes[i + 1] if i + 1 < len(partes) else ""
        # No formato CARGO, o proprio nome ja e o cargo
        cargo_limpo = re.sub(r"(?i)CARGO\s+", "", nome).split(" - CBO")[0].strip()
        blocos[nome] = {"conteudo": conteudo, "cargos": [cargo_limpo] if cargo_limpo else []}
    return blocos


# ------------------------------------------------------------------------------
# IDENTIFICACAO DE RISCOS
# ------------------------------------------------------------------------------
def identificar_riscos(texto_bloco: str) -> list:
    texto_norm = _normalizar(texto_bloco)
    chaves = set()

    for cod, chave in ESOCIAL_PARA_CHAVE.items():
        if cod in texto_bloco:
            chaves.add(chave)
            if chave in OTOTOXICOS_COM_BIOLOGICO:
                chaves.add("SUBSTANCIA_OTOTOXICA")

    for padrao, chave in TERMOS_PARA_CHAVE.items():
        if re.search(padrao, texto_norm):
            chaves.add(chave)
            if chave in OTOTOXICOS_COM_BIOLOGICO:
                chaves.add("SUBSTANCIA_OTOTOXICA")

    return sorted(chaves)


# ------------------------------------------------------------------------------
# GERACAO DE EXAMES
# ------------------------------------------------------------------------------
def gerar_exames_por_riscos(lista_riscos: list, regras: dict) -> list:
    vistos = set()
    lista = []
    for risco in lista_riscos:
        if risco not in regras:
            continue
        r = regras[risco]
        itens = r.get("exames", [r])
        for item in itens:
            nome = item.get("exame") or r.get("exame", "")
            if nome and nome not in vistos:
                vistos.add(nome)
                lista.append({
                    "exame": nome,
                    "periodicidade_meses": item.get("periodicidade_meses", r.get("periodicidade_meses")),
                    "momentos": item.get("momentos", r.get("momentos", [])),
                    "origem_risco": risco,
                })
    return lista


# ------------------------------------------------------------------------------
# FUNCAO PRINCIPAL
# ------------------------------------------------------------------------------
def parsear_pgr(fonte, regras: dict, forcar_ocr: bool = False) -> dict:
    """
    Parseia um PGR e retorna blocos com riscos, exames e cargos.

    Aceita:
      - bytes do PDF
      - caminho str/Path para o arquivo
      - texto puro str

    Detecta automaticamente o formato: GHE (tabular ou inline) ou CARGO/CBO.

    Retorna:
        {
            "metodo_extracao": str,
            "bloqueado":       bool,
            "aviso":           str | None,
            "formato":         str,
            "ghe_blocos":      dict,
                # chave = nome do GHE ou CARGO
                # valor = {
                #   "riscos_identificados": list,
                #   "exames_gerados":       list,
                #   "cargos":               list,  <- NOVO: cargos reais do SETOR/FUNCAO
                # }
        }
    """
    if isinstance(fonte, str) and ("\n" in fonte or len(fonte) > 300):
        texto = fonte
        metodo, bloqueado, aviso = "texto_direto", False, None
    elif isinstance(fonte, (bytes, bytearray)):
        r = extrair_texto_pgr(bytes(fonte), forcar_ocr)
        texto, metodo, bloqueado, aviso = r["texto"], r["metodo"], r["bloqueado"], r["aviso"]
    elif isinstance(fonte, (str, Path)):
        with open(fonte, "rb") as f:
            pdf_bytes = f.read()
        r = extrair_texto_pgr(pdf_bytes, forcar_ocr)
        texto, metodo, bloqueado, aviso = r["texto"], r["metodo"], r["bloqueado"], r["aviso"]
    else:
        raise ValueError("fonte deve ser bytes, caminho de arquivo ou texto string.")

    formato = detectar_formato(texto)
    blocos  = extrair_blocos_cargo(texto) if formato == "CARGO" else extrair_blocos_ghe(texto)

    ghe_resultado = {}
    for nome, info in blocos.items():
        conteudo = info["conteudo"]
        riscos   = identificar_riscos(conteudo)
        exames   = gerar_exames_por_riscos(riscos, regras)
        ghe_resultado[nome] = {
            "riscos_identificados": riscos,
            "exames_gerados":       exames,
            "cargos":               info.get("cargos", []),
        }

    return {
        "metodo_extracao": metodo,
        "bloqueado":       bloqueado,
        "aviso":           aviso,
        "formato":         formato,
        "ghe_blocos":      ghe_resultado,
    }
