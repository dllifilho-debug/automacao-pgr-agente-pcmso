"""
agente_medico_nr7.py  —  v1.0
Agente médico baseado na Matriz NR-7 validada pela Dra. Patricia (06/2025).

Resolve: riscos_do_ghe (lista de strings) → exames com adm/per/rt/dem
Sem chamada de API. 100% local.
"""

import json
import os
import re
import unicodedata
from typing import Optional

# ── Carregamento do banco ──────────────────────────────────────
_BANCO_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "banco_riscos_nr7.json")


def _carregar_banco() -> dict:
    with open(_BANCO_PATH, encoding="utf-8") as f:
        return json.load(f)["riscos"]


_BANCO: dict = _carregar_banco()


# ── Normalização ───────────────────────────────────────────────
def _norm(texto: str) -> str:
    s = unicodedata.normalize("NFD", texto)
    s = "".join(c for c in s if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", s.lower().strip())


# ── Match de riscos ────────────────────────────────────────────
def _match_risco(texto_risco: str) -> list:
    texto_n = _norm(texto_risco)
    matches = []
    for chave, dados in _BANCO.items():
        for kw in dados.get("keywords", []):
            if _norm(kw) in texto_n:
                matches.append(chave)
                break
    return matches


def _resolver_riscos(riscos: list) -> list:
    chaves = set()
    for risco in riscos:
        for chave in _match_risco(risco):
            chaves.add(chave)
    if not chaves:
        chaves.add("ASO PADRÃO")
    return sorted(chaves)


# ── Periodicidade mais restritiva ──────────────────────────────
def _per_menor(a: Optional[str], b: Optional[str]) -> Optional[str]:
    if a is None:
        return b
    if b is None:
        return a
    try:
        return str(min(int(a), int(b)))
    except ValueError:
        return a


# ── Montagem de exames (API pública) ──────────────────────────
def montar_exames_ghe(riscos: list) -> list:
    """
    Recebe lista de strings de riscos do GHE (extraídas do PGR).
    Retorna lista de exames deduplicados, periodicidade mais restritiva.

    Exemplo de retorno:
      [{"nome": "Audiometria", "adm": True, "per": "12", "rt": True, "dem": True}, ...]
    """
    chaves = _resolver_riscos(riscos)
    exames_map = {}

    for chave in chaves:
        for exame in _BANCO[chave]["exames"]:
            nome = exame["nome"]
            if nome not in exames_map:
                exames_map[nome] = {
                    "nome":          nome,
                    "adm":           exame.get("adm", False),
                    "per":           exame.get("per"),
                    "mud":           exame.get("mud", False),
                    "rt":            exame.get("rt", False),
                    "dem":           exame.get("dem", False),
                    "riscos_origem": [chave],
                }
            else:
                e = exames_map[nome]
                e["adm"] = e["adm"] or exame.get("adm", False)
                e["per"] = _per_menor(e["per"], exame.get("per"))
                e["mud"] = e["mud"] or exame.get("mud", False)
                e["rt"]  = e["rt"]  or exame.get("rt",  False)
                e["dem"] = e["dem"] or exame.get("dem", False)
                e["riscos_origem"].append(chave)

    return list(exames_map.values())


# ── Auditoria cruzada (API pública) ───────────────────────────
def auditar_exames_ghe(riscos: list, exames_gerados: list) -> dict:
    """
    Compara exames já presentes no GHE com o que a matriz NR-7 indica.

    Retorna:
      {
        "ok":            [...],  # exames corretos
        "faltando":      [...],  # previstos mas ausentes
        "extra":         [...],  # presentes mas não previstos
        "divergencias":  [...],  # periodicidade / flags diferentes
      }
    """
    esperados = {e["nome"]: e for e in montar_exames_ghe(riscos)}
    gerados   = {e["nome"]: e for e in exames_gerados}

    ok, faltando, extra, divergencias = [], [], [], []

    for nome in set(esperados) & set(gerados):
        esp, ger = esperados[nome], gerados[nome]
        divs = [
            {"campo": c, "esperado": esp.get(c), "gerado": ger.get(c)}
            for c in ("adm", "per", "rt", "dem")
            if str(esp.get(c)) != str(ger.get(c))
        ]
        if divs:
            divergencias.append({"nome": nome, "divergencias": divs})
        else:
            ok.append(nome)

    for nome in set(esperados) - set(gerados):
        faltando.append(esperados[nome])
    for nome in set(gerados) - set(esperados):
        extra.append(gerados[nome])

    return {"ok": ok, "faltando": faltando, "extra": extra, "divergencias": divergencias}


def listar_riscos_reconhecidos() -> list:
    return sorted(_BANCO.keys())
