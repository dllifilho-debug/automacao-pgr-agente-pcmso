"""
integracao_pcmso_nr7.py  —  v1.0
Camada de integração do agente_medico_nr7 com o fluxo existente do PCMSO.

Modo de uso: AUDITORIA PARALELA (não substitui o fluxo atual).
Roda em paralelo ao banco_matrizes_v1_1 → mostra divergências no app.py.
Quando validado, pode ser promovido a gerador principal.

Snippet de uso no app.py:

    from modules.integracao_pcmso_nr7 import enriquecer_ghe_com_nr7

    dados_ghe, rel_nr7 = enriquecer_ghe_com_nr7(dados_ghe)
    st.session_state["relatorio_nr7"] = rel_nr7

    if rel_nr7.get("ghe_com_divergencia"):
        with st.expander("⚠️ Auditoria NR-7 — Divergências encontradas", expanded=False):
            for item in rel_nr7["ghe_com_divergencia"]:
                ghe_data = next((g for g in dados_ghe if g.get("id") == item["ghe"]), {})
                st.markdown(f"**{item['ghe']}** — {ghe_data.get('nome', '')}:")
                col1, col2, col3 = st.columns(3)
                col1.metric("Exames faltando", item["faltando"])
                col2.metric("Exames a mais",   item["extra"])
                col3.metric("Periodicidade \u2260", item["divergencias"])
                audit = ghe_data.get("auditoria_nr7", {})
                if audit.get("faltando"):
                    st.warning("Faltando: " + ", ".join(e["nome"] for e in audit["faltando"]))
                if audit.get("extra"):
                    st.info("Não previstos pela NR-7: " + ", ".join(e["nome"] for e in audit["extra"]))
    elif rel_nr7.get("ghe_ok"):
        st.success(f"✅ NR-7: todos os {len(rel_nr7['ghe_ok'])} GHEs validados pela Matriz Dra. Patricia.")

    if rel_nr7.get("ghe_sem_riscos"):
        st.warning(f"⚠️ GHEs sem riscos extraídos: {', '.join(rel_nr7['ghe_sem_riscos'])}")
"""

from modules.agente_medico_nr7 import montar_exames_ghe, auditar_exames_ghe


def enriquecer_ghe_com_nr7(dados_ghe: list) -> tuple:
    """
    Para cada GHE:
      1. Pega riscos já extraídos pelo parser (campo "riscos")
      2. Gera exames pela matriz NR-7 (sem API)
      3. Se GHE já tem exames (gerados pelo banco V1_1), faz auditoria cruzada
      4. Adiciona campos "exames_nr7" e "auditoria_nr7" ao GHE

    Retorno
    -------
    dados_ghe : list[dict]  (enriquecido)
    relatorio : dict        (resumo da auditoria)
    """
    relatorio = {
        "ghe_ok": [],
        "ghe_com_divergencia": [],
        "ghe_sem_riscos": [],
    }

    for ghe in dados_ghe:
        ghe_id = ghe.get("id", "?")
        riscos = ghe.get("riscos", [])

        if not riscos:
            relatorio["ghe_sem_riscos"].append(ghe_id)
            ghe["exames_nr7"]    = []
            ghe["auditoria_nr7"] = {"status": "sem_riscos"}
            continue

        exames_nr7 = montar_exames_ghe(riscos)
        ghe["exames_nr7"] = exames_nr7

        exames_existentes = ghe.get("exames", [])
        if exames_existentes:
            auditoria = auditar_exames_ghe(riscos, exames_existentes)
            ghe["auditoria_nr7"] = auditoria
            tem_div = (
                auditoria["faltando"]
                or auditoria["extra"]
                or auditoria["divergencias"]
            )
            if tem_div:
                relatorio["ghe_com_divergencia"].append({
                    "ghe":          ghe_id,
                    "faltando":     len(auditoria["faltando"]),
                    "extra":        len(auditoria["extra"]),
                    "divergencias": len(auditoria["divergencias"]),
                })
            else:
                relatorio["ghe_ok"].append(ghe_id)
        else:
            # Sem exames anteriores: NR-7 vira fonte primária
            ghe["exames"]        = exames_nr7
            ghe["auditoria_nr7"] = {"status": "gerado_pelo_nr7"}
            relatorio["ghe_ok"].append(ghe_id)

    return dados_ghe, relatorio
