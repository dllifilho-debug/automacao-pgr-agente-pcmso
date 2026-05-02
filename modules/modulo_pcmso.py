# =============================================================================
# MÓDULO PCMSO v9.7 — Motor completo com Agente Médico IA v2.2
# Novidades v9.7:
#   FIX _TIPOS_GHE_KW: expandido com keywords de obra civil (concreto, armado,
#   eletrica, hidraulica, cobertura, gesso, instalacao, etc.) para que GHEs
#   reais de canteiro (ex: "GHE 01 - Estrutura de Concreto Armado") sejam
#   reconhecidos e não caiam no fallback total (todos os 23 cargos por GHE).
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

VERSAO_MODULO_PCMSO = "9.7 (AgenteMedicoIA v2.2 + _TIPOS_GHE_KW expandido para obra civil)"

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
