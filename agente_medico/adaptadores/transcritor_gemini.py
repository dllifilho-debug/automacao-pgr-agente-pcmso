from __future__ import annotations

import json
import re

import requests

from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim

# [DERIVADO — D-ARQ-47 cl.1/2/5, D-ARQ-48] Implementação REAL do TranscritorLLM
# (motor/transcritor_fds.py). Fica FORA do motor (D-ARQ-09): é o único lugar do
# sistema que fala com requests/API-key/JSON-de-rede para este contrato. O
# motor recebe só o tuple[BlocoVerbatim, ...] já desembrulhado — nunca sabe que
# existe HTTP, cascata de modelo ou chave.
#
# Cascata de modelos e formato de payload são um MOLDE de utils/ia_client.py
# (mesma família de decisão: 1º HTTP 200 vence, sem retry por modelo),
# reescrito aqui — não importado do legado, para não acoplar este adaptador
# novo a um módulo em refatoração alheio à fatia (e1) de DT-003AS-01.

_MODELOS: tuple[str, ...] = (
    "models/gemini-2.5-flash",
    "models/gemini-2.5-pro",
    "models/gemini-2.0-flash-001",
    "models/gemini-2.0-flash",
)

_URL = "https://generativelanguage.googleapis.com/v1beta/{modelo}:generateContent?key={chave}"

_PROMPT = """Você é um especialista em Fichas de Dados de Segurança (FDS/FISPQ) conforme a ABNT NBR 14725.

Abaixo está o texto VERBATIM da seção "Composição e informações sobre os ingredientes" de uma \
FDS, extraído por leitura de texto de PDF. O texto pode conter ruído de outras seções (ex.: \
tabela de Limite de Tolerância em ppm), quebras de linha no meio de um nome ou de um número de \
CAS, e colunas em ordens diferentes conforme o fabricante.

Sua tarefa é TRANSCREVER — nunca traduzir, corrigir ou normalizar — cada linha da tabela de \
composição que contenha o triplo NOME + CAS + FAIXA DE CONCENTRAÇÃO.

Regras:
1. A ORDEM DAS COLUNAS no documento é irrelevante. Identifique cada campo pelo FORMATO DO \
TOKEN, não pela posição:
   - CAS: dígitos-dígitos-dígito (ex.: "64-17-5", "134363-67-7").
   - FAIXA: dois números separados por hífen/en-dash (ex.: "1 - 5", "0,1 – 0,4"), ou \
semiaberta ("< 5", "> 1"). NÃO inclua o símbolo "%" no valor da faixa.
2. Uma linha SEM CAS reconhecível E SEM faixa reconhecível não é composição — é ruído (ex.: \
tabela de Limite de Tolerância em ppm de outra seção). DESCARTE essa linha.
3. Se o CAS estiver oculto no documento (grafias como "ND", "NA", "*", "**", "****", \
"vários", "Segredo Industrial", "Informação confidencial", ou célula vazia), emita "cas": "" \
— não copie a grafia literal.
4. Se um NOME estiver quebrado em múltiplas linhas pela renderização do PDF, reagrupe-o em \
uma única string, na ordem de leitura, por SENTIDO.
5. Um grupo do tipo "Derivados de:" com múltiplos CAS empilhados sob a MESMA faixa é UM \
bloco com múltiplos membros — a faixa é escrita uma única vez no bloco.
6. Preserve o texto do NOME e do CAS exatamente como aparecem no documento (acentos, \
maiúsculas/minúsculas) — é transcrição verbatim, não normalização.

Retorne APENAS JSON válido, sem markdown, sem texto adicional, neste formato exato:
{{"blocos": [{{"faixa": "1 - 5", "membros": [{{"cas": "64-17-5", "nome": "Etanol"}}]}}]}}

Texto da FDS:
{texto}
"""


class TranscricaoIndisponivel(Exception):
    """Falha de INVOCAÇÃO do transcritor-LLM (chave ausente, cascata de
    modelos sem 200, JSON de resposta ininteligível) — distinta de "LLM
    respondeu e afirmou composição vazia" (blocos=[] é resultado legítimo,
    não erro). Levantada em vez de devolver () silenciosamente: anti-
    supressão D-ARQ-31/35 — o chamador (orquestracao_fds) traduz para
    Pendencia bloqueante, nunca deixa a falha virar composição vazia muda."""

    def __init__(self, motivo: str) -> None:
        super().__init__(motivo)
        self.motivo = motivo


def _obter_chave() -> str:
    """CHAVE_API_GOOGLE: st.secrets primeiro, os.environ depois. Nunca lança
    (try/except em volta de streamlit — pode não estar instalado/configurado
    fora do app). Molde de modules/modulo_pcmso.tentar_gemini_para_ghes_sem_cargo.
    """
    chave = ""
    try:
        import streamlit as st

        chave = str(st.secrets.get("CHAVE_API_GOOGLE", "")).strip()
    except Exception:
        chave = ""
    if not chave:
        import os

        chave = os.environ.get("CHAVE_API_GOOGLE", "").strip()
    return chave


def _chamar_gemini(prompt: str, chave: str) -> str | None:
    """Cascata de modelos: primeiro HTTP 200 vence, sem retry por modelo.
    Qualquer exceção de rede/timeout num modelo passa para o próximo."""
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0, "maxOutputTokens": 8192},
    }
    for modelo in _MODELOS:
        try:
            r = requests.post(_URL.format(modelo=modelo, chave=chave), json=payload, timeout=120)
            if r.status_code == 200:
                resultado = r.json()["candidates"][0]["content"]["parts"][0]["text"]
                return str(resultado)
        except Exception:
            continue
    return None


def _limpar_json(texto: str) -> str:
    return re.sub(r"^```json\s*|^```\s*|\s*```$", "", texto.strip(), flags=re.IGNORECASE).strip()


def _parsear_blocos(texto: str) -> tuple[BlocoVerbatim, ...]:
    dados = json.loads(_limpar_json(texto))
    blocos_raw = dados.get("blocos", [])
    blocos: list[BlocoVerbatim] = []
    for bloco_raw in blocos_raw:
        membros = tuple(
            MembroVerbatim(
                cas=str(membro_raw.get("cas", "") or ""),
                nome=str(membro_raw.get("nome", "") or ""),
            )
            for membro_raw in bloco_raw.get("membros", [])
        )
        blocos.append(BlocoVerbatim(faixa=str(bloco_raw.get("faixa", "") or ""), membros=membros))
    return tuple(blocos)


class TranscritorGemini:
    """Implementação real de TranscritorLLM (motor/transcritor_fds.py, D-ARQ-47
    cl.1/2). Injetável: quem monta o cliente decide a chave; produção usa
    _obter_chave() (padrão st.secrets -> os.environ, nunca lança)."""

    def __init__(self, chave: str | None = None) -> None:
        self._chave = chave

    def transcrever(self, texto: str) -> tuple[BlocoVerbatim, ...]:
        chave = self._chave if self._chave is not None else _obter_chave()
        if not chave:
            raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")
        resposta = _chamar_gemini(_PROMPT.format(texto=texto), chave)
        if not resposta:
            raise TranscricaoIndisponivel("cascata Gemini sem 200")
        try:
            return _parsear_blocos(resposta)
        except Exception as e:
            raise TranscricaoIndisponivel(f"JSON inválido: {e}") from e
