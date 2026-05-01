# =============================================================================
# AGENTE MÉDICO IA v2.2 — Motor universal de PCMSO
# Metodologia: CMO / Dra. Patrícia Montalvo / Dra. Carolini Polesso
#
# Novidades v2.0:
#   F1 — auditar_pcmso()              : checklist NR-7 antes da assinatura
#   F2 — registrar_cargo_desconhecido(): banco de aprendizado de cargos novos
#   F3 — MATRIZ_RISCO_EXAME_IA        : expandida com NR-7 Anexos I e II completos
#   F4 — enriquecer_contexto_por_riscos(): leitura de riscos do PGR → contexto
#   F5 — relatorio_qualidade_pgr()    : avalia completude do PGR antes de processar
#   F6 — gerar_justificativa_ghe()    : gera parágrafo técnico por GHE
#
# Novidades v2.1:
#   Camada 0 — banco_ghe_cargo_v1.json: lookup GHE+Cargo preciso (base RQ.61)
#   resolver_chave_ghe()              : resolve fragmento do nome do GHE → chave
#   _MAPA_GHE_CHAVE                   : 60+ fragmentos de nomes de GHE mapeados
#   processar_cargo_ia retorna 'chave_ghe' no dict de saída
#
# Novidades v2.2:
#   Camada 2 — integração agente_medico_nr7: enriquece exames via riscos NR-7
#   Exames 'faltando' da NR-7 são adicionados com fonte='nr7_complemento'
#   Periodicidade mais restritiva aplicada para divergências detectadas
#   processar_cargo_ia retorna 'auditoria_nr7' no dict de saída
#   Degradação graciosa: se agente_medico_nr7 indisponível, fluxo continua normal
# =============================================================================

import json
import os
import re
from copy import deepcopy
from datetime import datetime

VERSAO_AGENTE = "2.2"  # Camadas 0-2: GHE+Cargo (RQ.61) + Cargo genérico + NR-7 por risco (agente_medico_nr7)

# ---------------------------------------------------------------------------
# Mapa de sinônimos de cargos → chave-mestra do banco
# ---------------------------------------------------------------------------
MAPA_CARGO_CHAVE = {
    # Administrativos / Técnicos
    'engenheiro': 'ENGENHEIRO',
    'engenheiro civil': 'ENGENHEIRO',
    'estagiario de engenharia': 'ESTAGIARIO',
    'estagiario': 'ESTAGIARIO',
    'tecnico de seguranca': 'TECNICO_SST',
    'tecnico de seguranca do trabalho': 'TECNICO_SST',
    'tecnico seguranca trabalho': 'TECNICO_SST',
    'tecnico sst': 'TECNICO_SST',
    'tst': 'TECNICO_SST',
    'estagiario de seguranca': 'ESTAGIARIO',
    'mestre de obra': 'MESTRE_OBRA',
    'mestre de obras': 'MESTRE_OBRA',
    'mestre obra': 'MESTRE_OBRA',
    # Encarregados
    'encarregado de pedreiro': 'ENCARREGADO_GERAL',
    'encarregado de pintor': 'ENCARREGADO_GERAL',
    'encarregado de eletricista': 'ENCARREGADO_GERAL',
    'encarregado de encanador': 'ENCARREGADO_GERAL',
    'encarregado de serralheiro': 'ENCARREGADO_GERAL',
    'encarregado de carpinteiro': 'ENCARREGADO_GERAL',
    'encarregado de armador': 'ENCARREGADO_GERAL',
    'encarregado de obra': 'ENCARREGADO_GERAL',
    'encarregado de obras': 'ENCARREGADO_GERAL',
    'encarregado de impermeabilizacao': 'IMPERMEABILIZADOR',
    'encarregado impermeabilizacao': 'IMPERMEABILIZADOR',
    'encarregado': 'ENCARREGADO_SUPERVISAO',
    # Administrativos de obra
    'administrativo de obra': 'AUXILIAR_ADMINISTRATIVO',
    'administrativo de obras': 'AUXILIAR_ADMINISTRATIVO',
    'aux adm de obras': 'AUXILIAR_ADMINISTRATIVO',
    'auxiliar administrativo de obras': 'AUXILIAR_ADMINISTRATIVO',
    'auxiliar administrativo': 'AUXILIAR_ADMINISTRATIVO',
    'assistente administrativo': 'AUXILIAR_ADMINISTRATIVO',
    'assistente adm': 'AUXILIAR_ADMINISTRATIVO',
    'jovem aprendiz': 'JOVEM_APRENDIZ',
    'aprendiz': 'JOVEM_APRENDIZ',
    'almoxarife': 'ALMOXARIFE',
    'porteiro': 'PORTEIRO_VIGIA',
    'vigia': 'PORTEIRO_VIGIA',
    'porteiro vigia': 'PORTEIRO_VIGIA',
    'vigilante': 'PORTEIRO_VIGIA',
    # Operacionais canteiro
    'carpinteiro': 'CARPINTEIRO',
    'meio oficial de carpinteiro': 'CARPINTEIRO',
    'meio of carpinteiro': 'CARPINTEIRO',
    'meio of. carpinteiro': 'CARPINTEIRO',
    'armador': 'ARMADOR',
    'meio oficial de armador': 'ARMADOR',
    'meio of armador': 'ARMADOR',
    'meio of. armador': 'ARMADOR',
    'pedreiro': 'PEDREIRO',
    'meio oficial de pedreiro': 'PEDREIRO',
    'meio of pedreiro': 'PEDREIRO',
    'meio of. pedreiro': 'PEDREIRO',
    'servente': 'SERVENTE_CANTEIRO',
    'servente de obra': 'SERVENTE_CANTEIRO',
    'servente de obras': 'SERVENTE_CANTEIRO',
    'pintor': 'PINTOR',
    'pintor de obras': 'PINTOR',
    'meio oficial de pintor': 'PINTOR',
    'encarregado de pintura': 'PINTOR',
    'serralheiro': 'SERRALHEIRO',
    'meio oficial de serralheiro': 'SERRALHEIRO',
    'eletricista': 'ELETRICISTA',
    'meio oficial de eletricista': 'ELETRICISTA',
    'eletricista industrial': 'ELETRICISTA_ENERGIZADO',
    'eletricista energizado': 'ELETRICISTA_ENERGIZADO',
    'encanador': 'ENCANADOR',
    'meio oficial de encanador': 'ENCANADOR',
    'meio of encanador': 'ENCANADOR',
    'meio of. encanador': 'ENCANADOR',
    'gesseiro': 'GESSEIRO',
    'meio oficial de gesseiro': 'GESSEIRO',
    'impermeabilizador': 'IMPERMEABILIZADOR',
    'aplicador de asfalto': 'IMPERMEABILIZADOR',
    'aplicador asfalto impermeabilizante': 'IMPERMEABILIZADOR',
    'operador de betoneira': 'OPERADOR_BETONEIRA',
    'operador betoneira': 'OPERADOR_BETONEIRA',
    'operador de grua': 'OPERADOR_GRUA',
    'operador grua': 'OPERADOR_GRUA',
    'operador de cremalheira': 'OPERADOR_CREMALHEIRA',
    'operador de elevador de cremalheira': 'OPERADOR_CREMALHEIRA',
    'operador de guincho': 'OPERADOR_CREMALHEIRA',
    'operador guincho': 'OPERADOR_CREMALHEIRA',
    'sinaleiro': 'SINALEIRO',
    'motorista': 'MOTORISTA',
    'mecanico de manutencao': 'MECANICO_MANUTENCAO',
    'mecanico manutencao': 'MECANICO_MANUTENCAO',
    'mecanico': 'MECANICO_MANUTENCAO',
    'soldador': 'SOLDADOR',
    'calceteiro': 'SERVENTE_CANTEIRO',
    'topografo': 'ENGENHEIRO',
    'azulejista': 'PEDREIRO',
    'assentador de ceramica': 'PEDREIRO',
}

# ---------------------------------------------------------------------------
# F3 — MATRIZ DE RISCO/AGENTE → EXAMES (NR-7 Anexos I e II expandidos)
# ---------------------------------------------------------------------------
MATRIZ_RISCO_EXAME_IA = {
    # ── Agentes Químicos ────────────────────────────────────────────────────
    'benzeno': [
        {'nome': 'Ácido Trans-trans Mucônico', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Contagem de Reticulócitos', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
    ],
    'tolueno': [
        {'nome': 'Ortocresol na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'xileno': [
        {'nome': 'Ácido Metil-hipúrico na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'estireno': [
        {'nome': 'Ácido Mandélico', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
        {'nome': 'Ácido Fenilglioxílico', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'manganês': [
        {'nome': 'Manganês Sanguíneo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': False},
    ],
    'manganes': [
        {'nome': 'Manganês Sanguíneo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': False},
    ],
    'monoxido de carbono': [
        {'nome': 'Carboxiemoglobina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'monóxido de carbono': [
        {'nome': 'Carboxiemoglobina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'tricloroetileno': [
        {'nome': 'Ácido tricloroacético na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
        {'nome': 'TGO/TGP', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': False},
    ],
    'fluoreto': [
        {'nome': 'Fluoreto Urinário', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
    ],
    'fluoreto de hidrogenio': [
        {'nome': 'Fluoreto Urinário', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
    ],
    'acetona': [
        {'nome': 'Acetona na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'metil etil cetona': [
        {'nome': 'Metil-Etil-Cetona', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'n-hexano': [
        {'nome': '2,5-Hexanodiona na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'chumbo': [
        {'nome': 'Chumbo Sanguíneo', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
        {'nome': 'Ác. Delta Amino Levulínico na urina (ALA-U)', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
    ],
    'mercurio': [
        {'nome': 'Mercúrio na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'mercúrio': [
        {'nome': 'Mercúrio na urina', 'adm': False, 'per': '6', 'mro': False, 'ret': False, 'dem': False},
    ],
    'organofosforado': [
        {'nome': 'Colinesterase Eritrocitária', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
        {'nome': 'Colinesterase Plasmática', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
    ],
    'pesticida': [
        {'nome': 'Colinesterase Eritrocitária', 'adm': True, 'per': '6', 'mro': True, 'ret': True, 'dem': True},
    ],
    'dioxido de nitrogenio': [
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'dióxido de nitrogênio': [
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'acido sulfurico': [
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    # ── Poeiras Minerais ───────────────────────────────────────────────────
    'silica': [
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'sílica': [
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'asbesto': [
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
    ],
    'amianto': [
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
    ],
    'cimento': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '60', 'mro': True, 'ret': False, 'dem': True},
    ],
    'cal': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'poeira mineral': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '60', 'mro': True, 'ret': False, 'dem': True},
    ],
    # ── Agentes Físicos ────────────────────────────────────────────────────
    'ruido': [
        {'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
    ],
    'ruído': [
        {'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
    ],
    'vibracao': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Exame de Membros Superiores', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'vibração': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Exame de Membros Superiores', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'calor': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Creatinina', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    # ── Fumos Metálicos / Solda ────────────────────────────────────────────
    'fumo metalico': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'fumo metálico': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'solda': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '6', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Espirometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
    ],
    # ── Biológicos ─────────────────────────────────────────────────────────
    'biologico': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'TGO/TGP', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'biológico': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'TGO/TGP', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'esgoto': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'TGO/TGP', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Urina Rotina (EAS)', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'leptospirose': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Urina Rotina (EAS)', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    # ── Situações Especiais ────────────────────────────────────────────────
    'espaco confinado': [
        {'nome': 'Avaliação Psicossocial', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'espaço confinado': [
        {'nome': 'Avaliação Psicossocial', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'trabalho em altura': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Acuidade Visual', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Avaliação Psicossocial', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'eletricidade': [
        {'nome': 'Acuidade Visual', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'noturno': [
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    # ── Tintas / Névoas / Impermeabilização ───────────────────────────────
    'nevoas': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'névoas': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'tinta': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
        {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
    ],
    'impermeabilizacao': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
    'impermeabilização': [
        {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
    ],
}

# ---------------------------------------------------------------------------
# F4 — Palavras-chave de risco no texto do PGR → flags de contexto
# ---------------------------------------------------------------------------
_RISCOS_CONTEXTO_KW = {
    'altura':         ['altura', 'nr-35', 'nr35', 'andaime', 'cremalheira', 'grua',
                       'telhado', 'trabalho em altura', 'queda'],
    'eletricidade':   ['eletric', 'nr-10', 'nr10', 'energizado', 'choque', 'tensao'],
    'confinado':      ['confinado', 'espaco confinado', 'cisterna', 'poco', 'nr-33', 'nr33'],
    'maquinas_pesadas':['betoneira', 'guindaste', 'grua', 'cremalheira', 'maquina', 'equipamento'],
    'poeira_mineral': ['poeira', 'cimento', 'cal', 'silica', 'areia', 'concreto', 'reboco'],
    'solda':          ['solda', 'fumo metalico', 'fumo metálico', 'soldagem'],
    'vibracao':       ['vibracao', 'vibração', 'perfuratriz', 'compactador', 'martelete'],
    'calor':          ['calor', 'ambiente quente', 'forno', 'exposicao ao calor'],
    'biologico':      ['esgoto', 'leptospirose', 'biologico', 'biológico', 'agente biologico'],
    'noturno':        ['noturno', 'turno noturno', 'trabalho noturno'],
    'organofosforado':['organofosforado', 'pesticida', 'herbicida', 'agrotoxico'],
}


# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    if not texto:
        return ''
    return texto.lower().strip()


def _remover_acentos_simples(texto: str) -> str:
    subs = {
        'á': 'a', 'â': 'a', 'ã': 'a', 'à': 'a',
        'é': 'e', 'ê': 'e',
        'í': 'i', 'î': 'i',
        'ó': 'o', 'ô': 'o', 'õ': 'o',
        'ú': 'u', 'û': 'u',
        'ç': 'c',
    }
    for k, v in subs.items():
        texto = texto.replace(k, v)
    return texto


def _norm(texto: str) -> str:
    return _remover_acentos_simples(_normalizar(texto))


def _exame_ja_existe(lista: list, nome: str) -> bool:
    n = _norm(nome)
    return any(_norm(e.get('nome', '')) == n for e in lista)


def _merge_exame(lista: list, novo: dict) -> list:
    """Adiciona exame se não existir; se existir, mantém periodicidade menor (mais conservadora)."""
    n_novo = _norm(novo['nome'])
    for e in lista:
        if _norm(e.get('nome', '')) == n_novo:
            per_atual = int(e.get('per') or 99)
            per_novo = int(novo.get('per') or 99)
            if per_novo < per_atual:
                e['per'] = str(per_novo)
            for flag in ('adm', 'mro', 'ret', 'dem'):
                e[flag] = e.get(flag, False) or novo.get(flag, False)
            return lista
    lista.append(deepcopy(novo))
    return lista


# ---------------------------------------------------------------------------
# Carregamento do banco de perfis
# ---------------------------------------------------------------------------

_BANCO_CACHE = None


def carregar_banco() -> dict:
    global _BANCO_CACHE
    if _BANCO_CACHE is not None:
        return _BANCO_CACHE


_BANCO_GHE_CACHE = None
_BANCO_GHE_PATH = os.path.join(os.path.dirname(__file__), '..', 'data', 'banco_ghe_cargo_v1.json')


def carregar_banco_ghe() -> dict:
    """Carrega banco GHE+Cargo (base Dra. Patrícia / RQ.61) — prioridade máxima no lookup."""
    global _BANCO_GHE_CACHE
    if _BANCO_GHE_CACHE is not None:
        return _BANCO_GHE_CACHE
    try:
        with open(_BANCO_GHE_PATH, encoding='utf-8') as f:
            _BANCO_GHE_CACHE = json.load(f)
    except Exception:
        _BANCO_GHE_CACHE = {}
    return _BANCO_GHE_CACHE


# Mapa de fragmentos do nome do GHE → chave canônica do banco GHE+Cargo
_MAPA_GHE_CHAVE = {
    # Estrutura
    'forma de pilar': 'GHE_ESTRUTURA_FORMA',
    'forma pilar':    'GHE_ESTRUTURA_FORMA',
    'execucao forma': 'GHE_ESTRUTURA_FORMA',
    'viga pilar':     'GHE_ESTRUTURA_ARMACAO',
    'execucao de viga': 'GHE_ESTRUTURA_ARMACAO',
    'armacao':        'GHE_ESTRUTURA_ARMACAO',
    'preparacao argamassa': 'GHE_ESTRUTURA_BETONEIRA',
    'operacao betoneira':   'GHE_ESTRUTURA_BETONEIRA',
    'betoneira':            'GHE_ESTRUTURA_BETONEIRA',
    'cremalheira montagem': 'GHE_ESTRUTURA_CREMALHEIRA_MONT',
    'cremalheira manutencao': 'GHE_ESTRUTURA_CREMALHEIRA_MONT',
    'montagem desmontagem': 'GHE_ESTRUTURA_CREMALHEIRA_MONT',
    'elevador cremalheira': 'GHE_ESTRUTURA_CREMALHEIRA_OP',
    'operador cremalheira': 'GHE_ESTRUTURA_CREMALHEIRA_OP',
    'grua sinalizacao': 'GHE_ESTRUTURA_GRUA_SINALIZACAO',
    'estrutura grua':   'GHE_ESTRUTURA_GRUA_SINALIZACAO',
    'alvenaria interna': 'GHE_ESTRUTURA_ALVENARIA',
    'alvenaria externa': 'GHE_ESTRUTURA_ALVENARIA',
    'alvenaria':         'GHE_ESTRUTURA_ALVENARIA',
    'prumada eletrica':  'GHE_ESTRUTURA_PRUMADA',
    'eletricidade desenergizada': 'GHE_ESTRUTURA_PRUMADA',
    'tubulacao de parede': 'GHE_ESTRUTURA_HIDRO',
    'hidro sanitaria': 'GHE_ESTRUTURA_HIDRO',
    'hidro-sanitaria': 'GHE_ESTRUTURA_HIDRO',
    'serralheria':     'GHE_ESTRUTURA_SERRALHERIA',
    'estrutura limpeza': 'GHE_ESTRUTURA_LIMPEZA',
    'limpeza estrutura': 'GHE_ESTRUTURA_LIMPEZA',
    'servico gerais':  'GHE_ESTRUTURA_SERVICOS_GERAIS',
    'servicos gerais': 'GHE_ESTRUTURA_SERVICOS_GERAIS',
    'pintura estrutura': 'GHE_ESTRUTURA_PINTURA',
    'estrutura pintura': 'GHE_ESTRUTURA_PINTURA',
    'portaria':        'GHE_ESTRUTURA_PORTARIA',
    'operacao grua':   'GHE_ESTRUTURA_GRUA_OPERACAO',
    'instalacao eletrica temporaria': 'GHE_ESTRUTURA_ELETRICA_TEMP',
    'eletricidade energizada': 'GHE_ESTRUTURA_ELETRICA_TEMP',
    # Acabamento
    'reboco interno': 'GHE_ACABAMENTO_REBOCO',
    'reboco externo': 'GHE_ACABAMENTO_REBOCO',
    'reboco':         'GHE_ACABAMENTO_REBOCO',
    'contrapiso':     'GHE_ACABAMENTO_CONTRAPISO',
    'impermeabilizacao acabamento': 'GHE_ACABAMENTO_IMPERMEABILIZACAO',
    'gesso corrido':  'GHE_ACABAMENTO_GESSO',
    'gesso placa':    'GHE_ACABAMENTO_GESSO',
    'gesso':          'GHE_ACABAMENTO_GESSO',
    'pintura interna': 'GHE_ACABAMENTO_PINTURA',
    'pintura externa': 'GHE_ACABAMENTO_PINTURA',
    'acabamento pintura': 'GHE_ACABAMENTO_PINTURA',
    'revestimento':   'GHE_ACABAMENTO_REVESTIMENTO',
    'rejunte':        'GHE_ACABAMENTO_REJUNTE',
    'limpeza grossa': 'GHE_ACABAMENTO_REJUNTE',
    'limpeza fina':   'GHE_ACABAMENTO_REJUNTE',
    'assentamento bancada': 'GHE_ACABAMENTO_ASSENTAMENTO',
    'manta asfaltica': 'GHE_ACABAMENTO_MANTA_ASFALTICA',
    'impermeabilizacao manta': 'GHE_ACABAMENTO_MANTA_ASFALTICA',
    # Administração
    'engenharia planejamento': 'GHE_ADMIN_ENGENHARIA',
    'planejamento de obra':    'GHE_ADMIN_ENGENHARIA',
    'seguranca do trabalho':   'GHE_ADMIN_SST',
    'execucao de obra admin':  'GHE_ADMIN_EXECUCAO',
    'supervisao rejunte':      'GHE_ADMIN_SUPERVISAO_REJUNTE',
    'supervisao limpeza':      'GHE_ADMIN_SUPERVISAO_REJUNTE',
    'administrativo de campo': 'GHE_ADMIN_ADMINISTRATIVO',
    'almoxarifado':            'GHE_ADMIN_ALMOXARIFADO',
}


def resolver_chave_ghe(ghe_nome: str) -> str | None:
    """Resolve o nome do GHE → chave canônica do banco GHE+Cargo."""
    gn = _norm(ghe_nome)
    # Busca do fragmento mais específico (maior) para o mais genérico
    for frag in sorted(_MAPA_GHE_CHAVE.keys(), key=len, reverse=True):
        if frag in gn:
            return _MAPA_GHE_CHAVE[frag]
    return None

    caminho = os.path.join(os.path.dirname(__file__), '..', 'data', 'banco_matrizes_v2.json')
    caminho = os.path.normpath(caminho)
    if os.path.exists(caminho):
        with open(caminho, 'r', encoding='utf-8') as f:
            _BANCO_CACHE = json.load(f)
    else:
        _BANCO_CACHE = {}
    return _BANCO_CACHE


# ---------------------------------------------------------------------------
# F2 — Registro automático de cargos desconhecidos
# ---------------------------------------------------------------------------

_DESCONHECIDOS_PATH = os.path.normpath(
    os.path.join(os.path.dirname(__file__), '..', 'data', 'cargos_desconhecidos.json')
)


def registrar_cargo_desconhecido(cargo: str, contexto_ghe: str = '') -> None:
    """
    Salva cargo não reconhecido em data/cargos_desconhecidos.json para
    revisão posterior e enriquecimento do MAPA_CARGO_CHAVE.
    """
    try:
        registros = []
        if os.path.exists(_DESCONHECIDOS_PATH):
            with open(_DESCONHECIDOS_PATH, 'r', encoding='utf-8') as f:
                registros = json.load(f)
        # Evita duplicatas
        cargos_ja_registrados = {r.get('cargo', '').lower() for r in registros}
        if cargo.lower() not in cargos_ja_registrados:
            registros.append({
                'cargo': cargo,
                'contexto_ghe': contexto_ghe,
                'data': datetime.now().strftime('%Y-%m-%d'),
                'chave_sugerida': None,
            })
            os.makedirs(os.path.dirname(_DESCONHECIDOS_PATH), exist_ok=True)
            with open(_DESCONHECIDOS_PATH, 'w', encoding='utf-8') as f:
                json.dump(registros, f, ensure_ascii=False, indent=2)
    except Exception:
        pass  # Nunca travar o fluxo principal por falha de log


def carregar_cargos_desconhecidos() -> list:
    """Retorna lista de cargos não reconhecidos registrados."""
    try:
        if os.path.exists(_DESCONHECIDOS_PATH):
            with open(_DESCONHECIDOS_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return []


# ---------------------------------------------------------------------------
# Camada 1 — Resolução de chave-mestra
# ---------------------------------------------------------------------------

def resolver_chave_mestra(cargo: str, contexto_ghe: str = '') -> str:
    """
    Mapeia cargo → chave-mestra do banco_matrizes_v2.
    Registra automaticamente em cargos_desconhecidos.json se não encontrar.
    """
    n = _norm(cargo)
    # 1. Tentativa direta
    if n in MAPA_CARGO_CHAVE:
        return MAPA_CARGO_CHAVE[n]
    # 2. Busca parcial (substring)
    for k, v in MAPA_CARGO_CHAVE.items():
        if k in n or n in k:
            return v
    # 3. Heurísticas por palavras-chave fortes
    tokens = set(n.split())
    if {'engenheiro'} & tokens:
        return 'ENGENHEIRO'
    if {'tecnico', 'seguranca'} <= tokens or {'tecnico', 'sst'} <= tokens:
        return 'TECNICO_SST'
    if {'mestre'} & tokens:
        return 'MESTRE_OBRA'
    if {'almoxarife', 'almoxarifado'} & tokens:
        return 'ALMOXARIFE'
    if {'porteiro', 'vigia', 'vigilante'} & tokens:
        return 'PORTEIRO_VIGIA'
    if {'carpinteiro'} & tokens:
        return 'CARPINTEIRO'
    if {'armador'} & tokens:
        return 'ARMADOR'
    if {'pedreiro'} & tokens:
        return 'PEDREIRO'
    if {'gesseiro'} & tokens:
        return 'GESSEIRO'
    if {'servente'} & tokens:
        return 'SERVENTE_CANTEIRO'
    if {'pintor'} & tokens:
        return 'PINTOR'
    if {'serralheiro'} & tokens:
        return 'SERRALHEIRO'
    if {'impermeabilizador', 'impermeabilizacao', 'asfalto', 'manta'} & tokens:
        return 'IMPERMEABILIZADOR'
    if {'eletricista', 'eletrico'} & tokens:
        if 'energizado' in n or 'industrial' in n:
            return 'ELETRICISTA_ENERGIZADO'
        return 'ELETRICISTA'
    if {'encanador', 'hidraulico', 'hidro'} & tokens:
        return 'ENCANADOR'
    if {'grua'} & tokens:
        return 'OPERADOR_GRUA'
    if {'betoneira'} & tokens:
        return 'OPERADOR_BETONEIRA'
    if {'cremalheira', 'elevador'} & tokens:
        return 'OPERADOR_CREMALHEIRA'
    if {'guincho'} & tokens:
        return 'OPERADOR_CREMALHEIRA'
    if {'sinaleiro'} & tokens:
        return 'SINALEIRO'
    if {'motorista'} & tokens:
        return 'MOTORISTA'
    if {'mecanico', 'manutencao'} & tokens:
        return 'MECANICO_MANUTENCAO'
    if {'soldador', 'solda'} & tokens:
        return 'SOLDADOR'
    if {'encarregado'} & tokens:
        return 'ENCARREGADO_GERAL'
    if {'administrativo', 'auxiliar', 'assistente', 'escriturario'} & tokens:
        return 'AUXILIAR_ADMINISTRATIVO'
    if {'aprendiz'} & tokens:
        return 'JOVEM_APRENDIZ'
    # Não encontrado — registra para aprendizado
    registrar_cargo_desconhecido(cargo, contexto_ghe)
    return None


# ---------------------------------------------------------------------------
# Camada 2 — Ajustes por contexto
# ---------------------------------------------------------------------------

def _aplicar_ajustes_contexto(exames: list, contexto: dict) -> list:
    if contexto.get('altura') or contexto.get('maquinas_pesadas'):
        for ex_novo in [
            {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'Acuidade Visual', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        ]:
            exames = _merge_exame(exames, ex_novo)
    if contexto.get('eletricidade'):
        for ex_novo in [
            {'nome': 'Acuidade Visual', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        ]:
            exames = _merge_exame(exames, ex_novo)
    if contexto.get('confinado'):
        exames = _merge_exame(exames, {
            'nome': 'Avaliação Psicossocial', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False
        })
    if contexto.get('vibracao'):
        exames = _merge_exame(exames, {
            'nome': 'Exame de Membros Superiores', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False
        })
    if contexto.get('noturno'):
        for ex_novo in [
            {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        ]:
            exames = _merge_exame(exames, ex_novo)
    if contexto.get('poeira_mineral'):
        for ex_novo in [
            {'nome': 'Espirometria', 'adm': True, 'per': '24', 'mro': True, 'ret': False, 'dem': True},
            {'nome': 'RX de Tórax OIT', 'adm': True, 'per': '60', 'mro': True, 'ret': False, 'dem': True},
        ]:
            exames = _merge_exame(exames, ex_novo)
    if contexto.get('biologico'):
        for ex_novo in [
            {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
            {'nome': 'TGO/TGP', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
        ]:
            exames = _merge_exame(exames, ex_novo)
    return exames


# ---------------------------------------------------------------------------
# Camada 3 — Injeção de IBE / NR-7 por agente químico
# ---------------------------------------------------------------------------

def _aplicar_riscos_quimicos(exames: list, riscos: list) -> list:
    for risco in riscos:
        risco_n = _norm(risco)
        for chave, novos_exames in MATRIZ_RISCO_EXAME_IA.items():
            if chave in risco_n or risco_n in chave:
                for ex in novos_exames:
                    exames = _merge_exame(exames, ex)
    return exames


# ---------------------------------------------------------------------------
# Camada 4 — Validação universal NR-7
# ---------------------------------------------------------------------------

def _validacao_universal(exames: list, e_canteiro: bool = True) -> list:
    if not _exame_ja_existe(exames, 'Exame Clínico'):
        exames.insert(0, {'nome': 'Exame Clínico', 'adm': True, 'per': '12', 'mro': True, 'ret': True, 'dem': True})
    if e_canteiro and not _exame_ja_existe(exames, 'Audiometria'):
        exames = _merge_exame(exames, {
            'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False
        })
    return exames


# ---------------------------------------------------------------------------
# F4 — Enriquecimento de contexto por texto de riscos do PGR
# ---------------------------------------------------------------------------

def enriquecer_contexto_por_riscos(riscos: list, contexto: dict = None) -> dict:
    """
    Lê a lista de strings de riscos/agentes do PGR e enriquece o dict de
    contexto com flags adicionais (vibracao, noturno, poeira_mineral, etc.).
    Complementa _contexto_do_ghe() do modulo_pcmso que já detecta altura/eletricidade.
    """
    if contexto is None:
        contexto = {}
    texto = ' '.join(riscos).lower()
    texto_n = _norm(texto)
    for flag, keywords in _RISCOS_CONTEXTO_KW.items():
        if not contexto.get(flag):
            contexto[flag] = any(kw in texto_n for kw in keywords)
    return contexto


# ---------------------------------------------------------------------------
# Motor principal: processar_cargo_ia
# ---------------------------------------------------------------------------

def processar_cargo_ia(
    cargo: str,
    riscos: list = None,
    contexto: dict = None,
    e_canteiro: bool = True,
    ghe_nome: str = '',
) -> dict:
    """
    Motor principal do Agente Médico IA v2.0.
    Retorna dict com exames, chave_mestra, fonte_regra, cargo_normalizado.

    Lookup em 5 camadas (ordem de prioridade):
      Camada 0 — banco_ghe_cargo_v1  (GHE + Cargo, base RQ.61 Dra. Patrícia)
      Camada 1 — banco_matrizes_v2   (Cargo genérico — fallback)
      Camada 2 — agente_medico_nr7   (Riscos NR-7 → exames IBE complementares)
      Camada 3 — _aplicar_ajustes_contexto (altura, energizado, grávida etc.)
      Camada 4 — _aplicar_riscos_quimicos  (IBE laboratorial por agente)
      Camada 5 — _validacao_universal      (Exame Clínico + Audiometria obrigatórios)
    """
    if riscos is None:
        riscos = []
    if contexto is None:
        contexto = {}

    # F4 — enriquece contexto com flags lidos dos riscos do PGR
    contexto = enriquecer_contexto_por_riscos(riscos, contexto)

    banco_ghe = carregar_banco_ghe()
    banco = carregar_banco()
    chave = resolver_chave_mestra(cargo, ghe_nome)
    exames = []
    fonte = 'agente_ia_sem_perfil'

    # ── Camada 0: Lookup composto GHE + Cargo (máxima precisão) ────────────
    chave_ghe = resolver_chave_ghe(ghe_nome) if ghe_nome else None
    if chave_ghe and chave:
        chave_composta = f"{chave_ghe}:{chave}"
        if chave_composta in banco_ghe:
            perfil = banco_ghe[chave_composta]
            exames = deepcopy(perfil.get('exames', []))
            fonte = f'banco_ghe_cargo:{chave_composta}'

    # ── Camada 1: Fallback — perfil genérico por cargo ──────────────────────
    if not exames:
        if chave and chave in banco:
            perfil = banco[chave]
            exames = deepcopy(perfil.get('exames', []))
            fonte = f'banco_perfil:{chave}'
        else:
            if e_canteiro:
                exames = [
                    {'nome': 'Exame Clínico', 'adm': True, 'per': '12', 'mro': True, 'ret': True, 'dem': True},
                    {'nome': 'Audiometria', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': True},
                    {'nome': 'Acuidade Visual', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
                    {'nome': 'Hemograma Completo', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
                    {'nome': 'Glicemia em Jejum', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
                    {'nome': 'ECG', 'adm': True, 'per': '12', 'mro': True, 'ret': False, 'dem': False},
                ]
            else:
                exames = [
                    {'nome': 'Exame Clínico', 'adm': True, 'per': '12', 'mro': True, 'ret': True, 'dem': True},
                ]
            fonte = f'heuristica_base:sem_perfil_para_{cargo}'

    # ── Camada 2: Enriquecimento NR-7 via agente_medico_nr7 ────────────────
    auditoria_nr7 = {}
    if riscos:
        try:
            from modules.agente_medico_nr7 import montar_exames_ghe as _nr7_montar
            from modules.agente_medico_nr7 import auditar_exames_ghe as _nr7_auditar
            exames_nr7 = _nr7_montar(riscos)
            auditoria_nr7 = _nr7_auditar(riscos, exames)
            # Adiciona exames que NR-7 exige mas a Camada 0/1 não trouxe
            nomes_atuais = {_norm(e['nome']) for e in exames}
            for ex_faltando in auditoria_nr7.get('faltando', []):
                if _norm(ex_faltando['nome']) not in nomes_atuais:
                    exames.append({
                        'nome':  ex_faltando['nome'],
                        'adm':   ex_faltando.get('adm', False),
                        'per':   ex_faltando.get('per'),
                        'mro':   ex_faltando.get('rt', False),   # nr7 usa 'rt' = mudança de função
                        'ret':   False,
                        'dem':   ex_faltando.get('dem', False),
                        'fonte': 'nr7_complemento',
                    })
                    nomes_atuais.add(_norm(ex_faltando['nome']))
            # Aplica periodicidade mais restritiva para exames divergentes
            for div in auditoria_nr7.get('divergencias', []):
                nome_n = _norm(div['nome'])
                per_nr7 = next(
                    (d['esperado'] for d in div.get('divergencias', []) if d['campo'] == 'per'),
                    None
                )
                if per_nr7:
                    for ex in exames:
                        if _norm(ex['nome']) == nome_n:
                            try:
                                per_atual = ex.get('per')
                                if per_atual and int(per_nr7) < int(per_atual):
                                    ex['per'] = per_nr7
                            except (ValueError, TypeError):
                                pass
        except (ImportError, FileNotFoundError):
            pass  # agente_medico_nr7 indisponível — degradação graciosa

    # ── Camada 3: Ajustes por contexto ──────────────────────────────────────
    exames = _aplicar_ajustes_contexto(exames, contexto)
    # ── Camada 4: Riscos químicos / IBE laboratorial ──────────────────────
    exames = _aplicar_riscos_quimicos(exames, riscos)
    # ── Camada 5: Validação universal NR-7 ───────────────────────────────
    exames = _validacao_universal(exames, e_canteiro=e_canteiro)

    return {
        'cargo':             cargo,
        'cargo_normalizado': _norm(cargo),
        'chave_mestra':      chave,
        'chave_ghe':         chave_ghe,
        'fonte_regra':       fonte,
        'e_canteiro':        e_canteiro,
        'exames':            exames,
        'auditoria_nr7':     auditoria_nr7,  # ← NOVO v2.2: divergências detectadas pela NR-7
    }




# ---------------------------------------------------------------------------
# F1 — Auditoria NR-7 do PCMSO gerado
# ---------------------------------------------------------------------------

_EXAMES_OBRIGATORIOS_CANTEIRO = ['exame clinico', 'audiometria']
_EXAMES_OBRIGATORIOS_ADM = ['exame clinico']

_CARGOS_ALTURA = ['carpinteiro', 'armador', 'pedreiro', 'servente', 'pintor',
                  'impermeabilizador', 'gesseiro', 'serralheiro', 'operador']
_CARGOS_ELETRICO = ['eletricista']


def auditar_pcmso(df, dados_ghe: list = None) -> dict:
    """
    F1 — Auditoria de conformidade NR-7 no DataFrame do PCMSO.
    Retorna dict com: pendencias (críticas), avisos (atenção), aprovado (bool),
    resumo (texto para exibição).
    """
    pendencias = []
    avisos = []

    try:
        ghe_col = 'GHE / Setor'
        cargo_col = 'Cargo'
        exame_col = 'Exame'
        per_col = 'PER'

        for ghe in df[ghe_col].unique():
            df_ghe = df[df[ghe_col] == ghe]
            exames_ghe = [_norm(e) for e in df_ghe[exame_col].tolist()]
            ghe_n = _norm(ghe)
            is_adm = any(x in ghe_n for x in ['administrativo', 'engenharia', 'planejamento', 'gerencia'])

            obrig = _EXAMES_OBRIGATORIOS_ADM if is_adm else _EXAMES_OBRIGATORIOS_CANTEIRO
            for ex_ob in obrig:
                if not any(ex_ob in e for e in exames_ghe):
                    pendencias.append(f"❌ {ghe}: '{ex_ob.title()}' ausente (NR-7 obrigatório)")

            # Cargos com risco de altura sem exames específicos
            for cargo in df_ghe[cargo_col].unique():
                cargo_n = _norm(cargo)
                if any(kw in cargo_n for kw in _CARGOS_ALTURA):
                    df_cargo = df_ghe[df_ghe[cargo_col] == cargo]
                    exames_cargo = [_norm(e) for e in df_cargo[exame_col].tolist()]
                    if not any('acuidade' in e for e in exames_cargo):
                        avisos.append(f"⚠️ {ghe} / {cargo}: Acuidade Visual ausente (risco de altura)")
                    if not any('ecg' in e for e in exames_cargo):
                        avisos.append(f"⚠️ {ghe} / {cargo}: ECG ausente (risco de altura)")
                if any(kw in cargo_n for kw in _CARGOS_ELETRICO):
                    df_cargo = df_ghe[df_ghe[cargo_col] == cargo]
                    exames_cargo = [_norm(e) for e in df_cargo[exame_col].tolist()]
                    if not any('acuidade' in e for e in exames_cargo):
                        avisos.append(f"⚠️ {ghe} / {cargo}: Acuidade Visual ausente (NR-10)")

        # Periodicidades fora do padrão NR-7 (6M a 60M)
        for _, row in df.iterrows():
            per = str(row.get(per_col, '')).replace('M', '').strip()
            try:
                val = int(per)
                if val < 6:
                    avisos.append(f"⚠️ Periodicidade muito curta ({val}M): {row[cargo_col]} — {row[exame_col]}")
                elif val > 60:
                    avisos.append(f"⚠️ Periodicidade muito longa ({val}M): {row[cargo_col]} — {row[exame_col]}")
            except Exception:
                pass

        # GHEs sem cargos
        if dados_ghe:
            for ghe in dados_ghe:
                if not ghe.get('cargos'):
                    pendencias.append(f"❌ {ghe.get('ghe', 'GHE?')}: sem cargos atribuídos")

    except Exception as e:
        avisos.append(f"⚠️ Erro na auditoria: {e}")

    aprovado = len(pendencias) == 0
    resumo = (
        f"✅ PCMSO aprovado na auditoria NR-7 ({len(avisos)} aviso(s))."
        if aprovado else
        f"❌ {len(pendencias)} pendência(s) crítica(s) e {len(avisos)} aviso(s). Revisar antes de assinar."
    )
    return {
        'aprovado': aprovado,
        'pendencias': pendencias,
        'avisos': avisos,
        'resumo': resumo,
    }


# ---------------------------------------------------------------------------
# F5 — Relatório de qualidade do PGR recebido
# ---------------------------------------------------------------------------

def relatorio_qualidade_pgr(dados_ghe: list, texto_pgr: str = '') -> dict:
    """
    F5 — Avalia a completude do PGR antes de gerar o PCMSO.
    Retorna dict com: problemas (lista), score (0-100), apto_para_pcmso (bool).
    """
    problemas = []
    score = 100

    if not dados_ghe:
        return {'problemas': ['PGR sem GHEs extraídos'], 'score': 0, 'apto_para_pcmso': False}

    ghe_sem_cargos = [g['ghe'] for g in dados_ghe if not g.get('cargos')]
    ghe_sem_riscos = [g['ghe'] for g in dados_ghe if not g.get('riscos_mapeados')]

    if ghe_sem_cargos:
        problemas.append(f"GHEs sem cargos: {', '.join(ghe_sem_cargos)}")
        score -= 20 * len(ghe_sem_cargos)

    if ghe_sem_riscos:
        problemas.append(f"GHEs sem agentes de risco: {', '.join(ghe_sem_riscos)} — PCMSO pode ficar incompleto")
        score -= 10 * len(ghe_sem_riscos)

    # Verifica se o PGR parece desatualizado (menciona datas antigas)
    if texto_pgr:
        anos_antigos = re.findall(r'\b(201[0-9]|202[0-2])\b', texto_pgr)
        if anos_antigos and not re.search(r'\b202[3-9]\b|\b20[3-9]\d\b', texto_pgr):
            problemas.append(f"PDF pode estar desatualizado — anos encontrados: {sorted(set(anos_antigos))}")
            score -= 5

    # Verifica cargos desconhecidos registrados
    desconhecidos = carregar_cargos_desconhecidos()
    if desconhecidos:
        nomes = [d['cargo'] for d in desconhecidos]
        problemas.append(f"{len(desconhecidos)} cargo(s) não reconhecido(s) no banco: {', '.join(nomes)}")
        score -= 5 * len(desconhecidos)

    score = max(0, min(100, score))
    apto = score >= 50 and not ghe_sem_cargos

    return {
        'problemas': problemas,
        'score': score,
        'apto_para_pcmso': apto,
        'total_ghes': len(dados_ghe),
        'total_cargos': sum(len(g.get('cargos', [])) for g in dados_ghe),
    }


# ---------------------------------------------------------------------------
# F6 — Geração de justificativa técnica por GHE
# ---------------------------------------------------------------------------

_JUSTIFICATIVA_RISCO_TEXTO = {
    'ruido':           'ruído acima do LEQ (NR-7 Anexo I)',
    'silica':          'exposição à sílica livre (NR-7 Anexo I)',
    'cimento':         'poeiras minerais (cimento/cal) com risco pneumoconiogênico',
    'tinta':           'névoas de tinta com solventes orgânicos',
    'altura':          'trabalho em altura (NR-35)',
    'eletricidade':    'trabalho com eletricidade (NR-10)',
    'confinado':       'trabalho em espaço confinado (NR-33)',
    'vibracao':        'exposição a vibração de membro superior',
    'calor':           'exposição a calor (ambiente quente)',
    'biologico':       'agentes biológicos (esgoto/leptospirose)',
    'solda':           'fumos metálicos de soldagem',
}

_EXAME_BASE_TEXTO = {
    'exame clinico':        'Exame Clínico (NR-7 §7.4)',
    'audiometria':          'Audiometria (NR-7 Anexo I)',
    'espirometria':         'Espirometria (NR-7 §6.3)',
    'rx de torax oit':      'RX de Tórax OIT (NR-7 §6.3)',
    'ecg':                  'ECG',
    'acuidade visual':      'Acuidade Visual',
    'hemograma completo':   'Hemograma Completo',
    'avaliacao psicossocial': 'Avaliação Psicossocial (NR-35/NR-33)',
}


def gerar_justificativa_ghe(
    ghe_nome: str,
    cargos: list,
    riscos: list,
    exames_nomes: list,
) -> str:
    """
    F6 — Gera parágrafo técnico de justificativa para o GHE,
    pronto para inserção no documento PCMSO assinado pelo médico.
    """
    contexto = enriquecer_contexto_por_riscos(riscos)

    # Identifica riscos relevantes do contexto e da lista de riscos
    riscos_texto = []
    for flag, descricao in _JUSTIFICATIVA_RISCO_TEXTO.items():
        if contexto.get(flag):
            riscos_texto.append(descricao)
    for risco in riscos:
        risco_n = _norm(risco)
        for chave, descricao in _JUSTIFICATIVA_RISCO_TEXTO.items():
            if chave in risco_n and descricao not in riscos_texto:
                riscos_texto.append(descricao)

    # Exames relevantes
    exames_texto = []
    for ex in exames_nomes:
        ex_n = _norm(ex)
        for chave, desc in _EXAME_BASE_TEXTO.items():
            if chave in ex_n and desc not in exames_texto:
                exames_texto.append(desc)
        if not any(chave in ex_n for chave in _EXAME_BASE_TEXTO):
            exames_texto.append(ex)

    cargos_str = ', '.join(cargos) if cargos else 'cargos não especificados'
    riscos_str = (', '.join(riscos_texto) if riscos_texto
                  else 'riscos ocupacionais inerentes ao canteiro de obras')
    exames_str = (', '.join(exames_texto[:6]) if exames_texto
                  else 'exames mínimos NR-7')

    justificativa = (
        f"Para o {ghe_nome}, os trabalhadores ({cargos_str}) estão expostos a "
        f"{riscos_str}, justificando a realização periódica de: {exames_str}. "
        f"Os exames e periodicidades foram definidos com base na NR-7 (Portaria MTE 1.031/2018), "
        f"Anexos I e II, e na metodologia de avaliação de risco do Programa de Gerenciamento "
        f"de Riscos vigente."
    )
    return justificativa


# ---------------------------------------------------------------------------
# Interface: processar_ghe_ia
# ---------------------------------------------------------------------------

def processar_ghe_ia(
    ghe_nome: str,
    cargos: list,
    riscos_ghe: list = None,
    contexto_ghe: dict = None,
) -> list:
    """Processa todos os cargos de um GHE e retorna lista de resultados."""
    if riscos_ghe is None:
        riscos_ghe = []
    if contexto_ghe is None:
        contexto_ghe = {}

    nome_n = _norm(ghe_nome)
    e_canteiro = not any(x in nome_n for x in [
        'administrativo', 'engenharia', 'planejamento', 'escritorio', 'gerencia', 'direcao'
    ])
    if 'almoxarifado' in nome_n:
        e_canteiro = True

    resultados = []
    for cargo in cargos:
        resultado = processar_cargo_ia(
            cargo=cargo,
            riscos=riscos_ghe,
            contexto=deepcopy(contexto_ghe),
            e_canteiro=e_canteiro,
        )
        resultado['ghe'] = ghe_nome
        resultados.append(resultado)
    return resultados
