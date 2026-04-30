# utils/ghe_mapper.py
"""
Mapeamento PGR GHE → Matriz PCMSO via Supabase.
Fallback automático para fuzzy local se Supabase indisponível.

Fluxo:
  1. Match exato por pgr_descricao ou pgr_aliases (score 1.0)
  2. Match fuzzy por subtítulo após "–"/"-" (score ≥ 0.75)
  3. None → caller usa matriz interna + salva pendência no Supabase
"""
from __future__ import annotations

import os
import unicodedata
import re
from difflib import SequenceMatcher
from typing import Optional

try:
    import streamlit as st
    _STREAMLIT = True
except ImportError:
    _STREAMLIT = False


# ── cliente Supabase ──────────────────────────────────────────────────────────

def _get_supabase():
    try:
        from supabase import create_client
        if _STREAMLIT:
            url = st.secrets.get("SUPABASE_URL") or os.getenv("SUPABASE_URL")
            key = st.secrets.get("SUPABASE_KEY") or os.getenv("SUPABASE_KEY")
        else:
            url = os.getenv("SUPABASE_URL")
            key = os.getenv("SUPABASE_KEY")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None


def _sb_cached():
    """Retorna cliente Supabase com cache Streamlit (se disponível)."""
    if _STREAMLIT:
        if "sb_client" not in st.session_state:
            st.session_state["sb_client"] = _get_supabase()
        return st.session_state["sb_client"]
    return _get_supabase()


# ── carregamento de mapeamentos ───────────────────────────────────────────────

def carregar_mapeamentos(forcar_reload: bool = False) -> list[dict]:
    """
    Carrega mapeamentos confirmados do Supabase.
    Usa cache de sessão para evitar múltiplas requisições.
    """
    cache_key = "_ghe_mapeamentos_cache"

    if _STREAMLIT and not forcar_reload and cache_key in st.session_state:
        return st.session_state[cache_key]

    sb = _sb_cached()
    if sb is None:
        return []

    try:
        res = (
            sb.table("ghe_mapeamentos")
            .select("pgr_descricao, pgr_aliases, matriz_titulo, matriz_secao, cargos")
            .eq("confirmado", True)
            .execute()
        )
        dados = res.data or []
        if _STREAMLIT:
            st.session_state[cache_key] = dados
        return dados
    except Exception:
        return []


# ── normalização de texto ─────────────────────────────────────────────────────

def _normalizar(texto: str) -> str:
    """Remove acentos, lowercase, remove caracteres especiais."""
    t = unicodedata.normalize("NFKD", texto.lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9 ]", " ", t).strip()


def _score_sim(a: str, b: str) -> float:
    return SequenceMatcher(None, _normalizar(a), _normalizar(b)).ratio()


def _extrair_subtitulo(titulo_matriz: str) -> str:
    """Extrai parte após '–' ou '-' do título da Matriz."""
    for sep in ["–", "-"]:
        if sep in titulo_matriz:
            return titulo_matriz.split(sep, 1)[-1].strip()
    return titulo_matriz


# ── busca de match ────────────────────────────────────────────────────────────

def buscar_match(
    pgr_desc: str,
    mapeamentos: Optional[list[dict]] = None,
) -> Optional[dict]:
    """
    Busca mapeamento para um GHE do PGR.

    Retorna dict com chaves originais + 'score' (float) + 'metodo' (str),
    ou None se não encontrar match confiável.

    Exemplo de retorno:
        {
          "pgr_descricao": "engenharia planejamento de obra",
          "matriz_titulo": "GHE 01: Administração de campo – Engenharia...",
          "matriz_secao":  "Administração de campo",
          "cargos":        ["Engenheiro", "Estagiário"],
          "score":         1.0,
          "metodo":        "exato"
        }
    """
    if mapeamentos is None:
        mapeamentos = carregar_mapeamentos()
    if not mapeamentos:
        return None

    norm_pgr = _normalizar(pgr_desc)

    # 1. Match exato — pgr_descricao ou aliases
    for m in mapeamentos:
        candidatos = [m.get("pgr_descricao", "")] + (m.get("pgr_aliases") or [])
        if norm_pgr in [_normalizar(c) for c in candidatos if c]:
            return {**m, "score": 1.0, "metodo": "exato"}

    # 2. Match fuzzy — compara com subtítulo e com pgr_descricao
    melhor, melhor_score = None, 0.0

    for m in mapeamentos:
        # compara com subtítulo da Matriz
        subtitulo = _extrair_subtitulo(m.get("matriz_titulo", ""))
        s1 = _score_sim(pgr_desc, subtitulo)

        # compara diretamente com pgr_descricao
        s2 = _score_sim(pgr_desc, m.get("pgr_descricao", ""))

        s = max(s1, s2)
        if s > melhor_score:
            melhor, melhor_score = m, s

    if melhor and melhor_score >= 0.75:
        return {**melhor, "score": round(melhor_score, 3), "metodo": "fuzzy"}

    return None


# ── persistência de novos mapeamentos ────────────────────────────────────────

def salvar_mapeamento(
    pgr_desc: str,
    matriz_titulo: str,
    matriz_secao: str,
    cargos: list[str],
    obra: str,
    confirmado: bool = False,
) -> bool:
    """
    Persiste novo mapeamento no Supabase.
    confirmado=False → aparece como sugestão pendente de revisão.
    Retorna True se salvou com sucesso.
    """
    sb = _sb_cached()
    if sb is None:
        return False
    try:
        sb.table("ghe_mapeamentos").insert({
            "pgr_descricao":   _normalizar(pgr_desc),
            "pgr_aliases":     [],
            "matriz_titulo":   matriz_titulo,
            "matriz_secao":    matriz_secao,
            "cargos":          cargos,
            "score_confianca": 1.0 if confirmado else 0.85,
            "confirmado":      confirmado,
            "obra_origem":     obra,
        }).execute()
        # invalida cache
        if _STREAMLIT and "_ghe_mapeamentos_cache" in st.session_state:
            del st.session_state["_ghe_mapeamentos_cache"]
        return True
    except Exception:
        return False


def confirmar_mapeamento(pgr_desc: str) -> bool:
    """Marca mapeamento como confirmado por humano (score 1.0)."""
    sb = _sb_cached()
    if sb is None:
        return False
    try:
        sb.table("ghe_mapeamentos").update({
            "confirmado":      True,
            "score_confianca": 1.0,
        }).eq("pgr_descricao", _normalizar(pgr_desc)).execute()
        if _STREAMLIT and "_ghe_mapeamentos_cache" in st.session_state:
            del st.session_state["_ghe_mapeamentos_cache"]
        return True
    except Exception:
        return False
