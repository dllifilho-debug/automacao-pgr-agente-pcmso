"""Cliente isolado para Gemini com cascata de modelos."""
import re
import json
import requests

_MODELOS: list = [
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-2.0-flash-001",
    "models/gemini-2.0-flash",
]

_URL = "https://generativelanguage.googleapis.com/v1beta/{modelo}:generateContent?key={chave}"


def _chamar_gemini(prompt: str, chave: str, max_tokens: int = 8192) -> str | None:
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.1, "maxOutputTokens": max_tokens},
    }
    for modelo in _MODELOS:
        try:
            r = requests.post(_URL.format(modelo=modelo, chave=chave), json=payload, timeout=120)
            if r.status_code == 200:
                return r.json()["candidates"][0]["content"]["parts"][0]["text"]
        except Exception:
            continue
    return None


def _limpar_json(texto: str) -> str:
    return re.sub(r"^```json\s*|^```\s*|\s*```$", "", texto.strip(), flags=re.IGNORECASE).strip()


def buscar_dados_cas_ia(cas: str, texto_fispq: str, chave: str) -> dict | None:
    prompt = f"""
Voce e um especialista em SST brasileiro.
Para o agente CAS {cas}, retorne APENAS JSON valido:
{{
  "agente": "Nome",
  "nr15_lt": "Limite de Tolerancia NR-15",
  "nr09_acao": "Nivel de Acao NR-09 (50% do LT)",
  "nr07_ibe": "Indicador Biologico de Exposicao NR-07",
  "dec_3048": "Aposentadoria Especial Decreto 3.048/99",
  "esocial_24": "Codigo eSocial Tabela 24"
}}
Trecho da FISPQ:
{texto_fispq[:3000]}
"""
    texto = _chamar_gemini(prompt, chave)
    if not texto:
        return None
    try:
        return json.loads(_limpar_json(texto))
    except Exception:
        return None


def extrair_pgr_via_ia(texto_pgr: str, chave: str) -> list:
    prompt = f"""
Extraia os GHEs do PGR abaixo. Retorne APENAS JSON valido:
[
  {{
    "ghe": "Nome do GHE",
    "cargos": ["Cargo 1", "Cargo 2"],
    "riscos_mapeados": [
      {{"nome_agente": "Agente", "perigo_especifico": "Descricao", "nivel_risco": "MODERADO"}}
    ]
  }}
]
Texto do PGR:
{texto_pgr[:30000]}
"""
    texto = _chamar_gemini(prompt, chave)
    if not texto:
        return []
    try:
        return json.loads(_limpar_json(texto))
    except Exception:
        return []


def extrair_pgr_estruturado_via_gemini(texto_pgr: str, chave: str) -> list | None:
    """
    Envia texto do PGR para o Gemini e retorna lista de GHEs estruturados.
    Retorna None se a API falhar, a chave estiver vazia ou o JSON for inválido.

    O prompt exige o schema:
      {"ghes": [{"numero": "01", "titulo": "...", "cargos": [...], "riscos": [...]}]}

    Retorno convertido para list[dict_ghe]:
    [
        {
            "ghe": "GHE 01 - Estrutura de concreto armado",
            "cargos": ["Carpinteiro", "Servente"],
            "riscos_mapeados": [
                {"nome_agente": "Ruído", "perigo_especifico": ""}
            ],
            "exames": []   # resolvido depois por processar_cargo_ia()
        }
    ]

    Nunca lança exceção para o chamador — qualquer falha retorna None.
    """
    if not chave:
        return None

    prompt = (
        "Você é um especialista em Saúde e Segurança do Trabalho (SST) brasileiro.\n"
        "Analise o texto do PGR (Programa de Gerenciamento de Riscos) abaixo e extraia "
        "todos os Grupos Homogêneos de Exposição (GHEs).\n\n"
        "Retorne APENAS JSON válido, sem texto adicional, markdown ou explicações, "
        "neste formato exato:\n"
        '{\n'
        '  "ghes": [\n'
        '    {\n'
        '      "numero": "01",\n'
        '      "titulo": "Estrutura de concreto armado - Execução fôrma",\n'
        '      "cargos": ["Carpinteiro", "Meio Oficial de Carpinteiro", "Servente"],\n'
        '      "riscos": ["Ruído", "Poeira de madeira", "Trabalho em altura"]\n'
        '    }\n'
        '  ]\n'
        '}\n\n'
        "Regras obrigatórias:\n"
        '- "numero" deve ser o número do GHE com dois dígitos (ex: "01", "07")\n'
        '- "titulo" é a descrição do GHE sem o prefixo "GHE NN -" ou "GHE NN:"\n'
        '- "cargos" são APENAS funções humanas (ex: Pedreiro, Eletricista, Carpinteiro) —'
        ' NÃO inclua etapas, processos ou atividades da obra como cargos'
        ' (NÃO inclua Alvenaria, Estrutura, Contrapiso, Impermeabilização, Pintura)\n'
        '- "riscos" são os agentes de risco em linguagem natural\n'
        '- Se não encontrar GHEs, retorne {"ghes": []}\n\n'
        f"Texto do PGR:\n{texto_pgr}"
    )

    try:
        texto = _chamar_gemini(prompt, chave, max_tokens=32768)
        if not texto:
            return None

        dados = json.loads(_limpar_json(texto))

        ghes_raw = dados.get("ghes")
        if not isinstance(ghes_raw, list) or len(ghes_raw) == 0:
            return None

        resultado = []
        for item in ghes_raw:
            if not isinstance(item, dict):
                continue

            numero = str(item.get("numero", "")).strip().zfill(2)
            titulo = str(item.get("titulo", "")).strip()
            ghe_nome = (
                f"GHE {numero} - {titulo}" if titulo else f"GHE {numero}"
            )

            cargos = [
                str(c).strip()
                for c in item.get("cargos", [])
                if str(c).strip()
            ]

            riscos_mapeados = [
                {"nome_agente": str(r).strip(), "perigo_especifico": ""}
                for r in item.get("riscos", [])
                if str(r).strip()
            ]

            resultado.append({
                "ghe":             ghe_nome,
                "cargos":          cargos,
                "riscos_mapeados": riscos_mapeados,
                "exames":          [],
            })

        return resultado if resultado else None

    except Exception:
        return None
