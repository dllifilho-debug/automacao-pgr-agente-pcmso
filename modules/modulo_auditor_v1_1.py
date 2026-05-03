import json
import re
import unicodedata
from pathlib import Path
from collections import defaultdict


def _strip(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', str(texto or ''))
                   if unicodedata.category(c) != 'Mn')


def norm(texto):
    s = _strip(texto).upper().strip()
    s = re.sub(r'[\-\.\'\`]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()


def normalizar_exame(nome):
    s = norm(nome)
    mapa = {
        'EXAME CLINICO': 'Exame Clinico',
        'EXAME CLINICO SEMESTRAL': 'Exame Clinico',
        'AUDIOMETRIA': 'Audiometria',
        'AUDIOMETRIA TONAL': 'Audiometria',
        'AUDIOMETRIA TONAL PTA': 'Audiometria',
        'ACUIDADE VISUAL': 'Acuidade Visual',
        'AVALIACAO OFTALMOLOGICA': 'Acuidade Visual',
        'HEMOGRAMA': 'Hemograma',
        'HEMOGRAMA COMPLETO': 'Hemograma',
        'GLICEMIA EM JEJUM': 'Glicemia em Jejum',
        'GLICEMIA DE JEJUM': 'Glicemia em Jejum',
        'ECG': 'ECG',
        'ELETROCARDIOGRAMA': 'ECG',
        'ELETROCARDIOGRAMA ECG': 'ECG',
        'ESPIROMETRIA': 'Espirometria',
        'ESPIROMETRIA (SOMENTE)': 'Espirometria',
        'RX DE TORAX OIT': 'RX de Tórax OIT',
        'RX TORAX OIT': 'RX de Tórax OIT',
        'RAIO X TORAX OIT': 'RX de Tórax OIT',
        'RX DE TORAX': 'RX de Tórax OIT',
        'RX DE COLUNA LOMBO SACRA': 'RX de coluna lombo-sacra',
        'RX COLUNA LOMBO SACRA': 'RX de coluna lombo-sacra',
        'RAIO X COLUNA LOMBO SACRA': 'RX de coluna lombo-sacra',
        'AVALIACAO PSICOSSOCIAL': 'Avaliação Psicossocial',
        'AVALIACAO PSICOSSOCIAL NR 35': 'Avaliação Psicossocial',
        'CARBOXIEMOGLOBINA': 'Carboxiemoglobina',
        'CARBOXIHEMOGLOBINA': 'Carboxiemoglobina',
        'CARBOXIHEMOGLOBINA NO SANGUE': 'Carboxiemoglobina',
        'CARBOXIEMOGLOBINA NO SANGUE': 'Carboxiemoglobina',
        'MANGANES SANGUINEO': 'Manganês sanguíneo',
        'MANGANES NO SANGUE': 'Manganês sanguíneo',
        'CONTAGEM DE RETICULOCITOS': 'Contagem de Reticulócitos',
        'RETICULOCITOS': 'Contagem de Reticulócitos',
        'ACIDO TRANS TRANS MUCONICO': 'Ácido trans-trans mucônico',
        'ACIDO TRANS TRANS MUCONICO NA URINA': 'Ácido trans-trans mucônico',
        'AC TRANS TRANS MUCONICO NA URINA': 'Ácido trans-trans mucônico',
        'AC TRANS TRANS MUCONICO': 'Ácido trans-trans mucônico',
        'ACIDO TRICLOROACETICO NA URINA': 'Ácido tricloroacético na urina',
        'AC TRICLOROACETICO NA URINA': 'Ácido tricloroacético na urina',
        'ACIDO TRICLOROACETICO': 'Ácido tricloroacético na urina',
        'ACETONA NA URINA': 'Acetona na urina',
        'ORTOCRESOL NA URINA': 'Ortocresol na urina',
        'METIL ETIL CETONA': 'Metil-Etil-Cetona',
        'METIL ETIL CETONA NA URINA': 'Metil-Etil-Cetona',
        'METILETILCETONA NA URINA': 'Metil-Etil-Cetona',
        'MEK NA URINA': 'Metil-Etil-Cetona',
        'METIL ETIL CETONA (MEK) NA URINA': 'Metil-Etil-Cetona',
        'ACIDO METIL HIPURICO NA URINA': 'Ác. Metil-hipúrico na urina',
        'AC METIL HIPURICO NA URINA': 'Ác. Metil-hipúrico na urina',
        'AC  METIL HIPURICO NA URINA': 'Ác. Metil-hipúrico na urina',
        'CICLOHEXANOL NA URINA': 'Ciclohexanol na urina',
        'CICLOHEXANOL H NA URINA': 'Ciclohexanol na urina',
        'TETRAHIDROFURNANO NA URINA': 'Tetrahidrofurnano na urina',
        'TETRAHIDROFURANO NA URINA': 'Tetrahidrofurnano na urina',
        'EPF (COPROPARASITOLOGICO) + ANTI HBS': 'EPF (Coproparasitológico) + Anti-HBs',
        'EPF COPROPARASITOLOGICO + ANTI HBS': 'EPF (Coproparasitológico) + Anti-HBs',
    }
    return mapa.get(s, nome.strip())


# Aliases para mapear cargos normalizados em formas canônicas que casam com o
# banco. As chaves estão em forma JÁ NORMALIZADA (lowercase, sem acento, sem
# pontuação) — o resultado de normalizar_cargo() ANTES da resolução de alias.
_ALIASES_CARGO_NORM = {
    # Meio oficial → cargo principal (banco_matrizes_v2 só tem o cargo principal)
    'meio oficial de pedreiro':            'pedreiro',
    'meio oficial de armador':             'armador',
    'meio oficial de carpinteiro':         'carpinteiro',
    'meio oficial de eletricista':         'eletricista',
    'meio oficial de eletrica':            'eletricista',
    'meio oficial eletrica':               'eletricista',
    'meio oficial de encanador':           'encanador',
    'meio oficial hidraulico':             'encanador',
    'meio oficial de serralheiro':         'serralheiro',
    'meio oficial de pintor':              'pintor',
    'meio oficial de gesseiro':            'gesseiro',
    'meio oficial de impermeabilizador':   'impermeabilizador',

    # Técnico SST e variantes → forma plena (TECNICO_SST no banco)
    'tecnico de seguranca':                'tecnico de seguranca do trabalho',
    'tecnico em seguranca do trabalho':    'tecnico de seguranca do trabalho',
    'tecnico sst':                         'tecnico de seguranca do trabalho',
    'tst':                                 'tecnico de seguranca do trabalho',

    # Eletricista variantes
    'eletricista industrial':              'eletricista energizado',

    # Servente variantes
    'servente de obra':                    'servente',
    'servente de obras':                   'servente',
    'servente de armador':                 'servente',
    'servente de carpinteiro':             'servente',
    'auxiliar de limpeza':                 'servente',
    'auxiliar de servicos gerais':         'servente',

    # Auxiliares
    'auxiliar de almoxarife':              'almoxarife',
    'auxiliar administrativo':             'assistente administrativo',
    'aux administrativo':                  'assistente administrativo',
    'aux adm':                             'assistente administrativo',
    'auxiliar de engenharia':              'estagiario de engenharia',

    # Engenharia
    'engenheiro civil':                    'engenheiro',
    'estagiario de engenharia civil':      'estagiario de engenharia',
    'estagiario':                          'estagiario de engenharia',

    # Mestre/Vigia
    'mestre de obras':                     'mestre de obra',
    'vigia diurno':                        'vigia',
    'vigia noturno':                       'vigia',

    # Encarregados
    'encarregado de acabamento':           'encarregado de pedreiro',
    'encarregado de armacao':              'encarregado de pedreiro',
    'encarregado de forma':                'encarregado de carpinteiro',
    'encarregado de instalacoes':          'encarregado de encanador',
    'encarregado administrativo de obras': 'auxiliar administrativo de obras',
}


def normalizar_cargo(nome) -> str:
    """
    Normaliza nome de cargo para comparação ESTRITA contra o banco de exames.

    Aplica em sequência:
      1. .strip() + .lower()
      2. Remove acentos (equivalente a unidecode via unicodedata)
      3. Remove prefixo "X:" (mantém só o texto DEPOIS do ":")
         Ex: "Manutenção: Eletricista industrial" → "eletricista industrial"
      4. Expande "meio of." e "meio of " → "meio oficial de "
         Ex: "meio of. de pedreiro" → "meio oficial de pedreiro"
      5. Remove pontuação isolada e espaços duplos
      6. Resolve alias canônico via _ALIASES_CARGO_NORM
         Ex: "tecnico de seguranca" → "tecnico de seguranca do trabalho"

    Retorna string lowercase sem acentos. DEVE ser aplicada em AMBOS os lados
    (input e chave do banco) para garantir igualdade simétrica.
    """
    if not nome:
        return ""

    s = str(nome).strip().lower()

    # 2. Remove acentos
    s = ''.join(
        c for c in unicodedata.normalize('NFD', s)
        if unicodedata.category(c) != 'Mn'
    )

    # 3. Remove prefixo "X:" (mantém só texto depois)
    if ':' in s:
        s = s.split(':', 1)[1].strip()

    # 4. Expande "meio of." e variantes em "meio oficial de "
    s = re.sub(r'\bmeio\s+of\.?\s+', 'meio oficial de ', s)
    # Corrige "de de" duplicado que surge de "meio of. de pedreiro"
    s = re.sub(r'\bde\s+de\b', 'de', s)

    # 5. Remove pontuação isolada (-, ., ', `) e normaliza espaços
    s = re.sub(r"[\-\.\'\`]", ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()

    # 6. Resolve alias canônico
    return _ALIASES_CARGO_NORM.get(s, s)


# ───────────────────────────────────────────────────────────────────────────
# MAPA: nome do GHE → chave do banco_matrizes_v2
# Usado quando o parser_pgr retorna o nome do GHE como "cargo"
# ───────────────────────────────────────────────────────────────────────────
_MAPA_GHE_PARA_BANCO_KEY = {
    # Engenharia / Planejamento
    'GHE 01': 'ENGENHEIRO',
    'ENGENHARIA': 'ENGENHEIRO',
    'ENGENHARIA PLANEJAMENTO': 'ENGENHEIRO',
    'PLANEJAMENTO DE OBRA': 'ENGENHEIRO',
    # SST / Segurança do Trabalho
    'GHE 02': 'TECNICO_SST',
    'SEGURANCA DO TRABALHO': 'TECNICO_SST',
    'TECNICO SST': 'TECNICO_SST',
    'TECNICO DE SEGURANCA': 'TECNICO_SST',
    # Execução de obra (genérico → PRODUCAO_GERAL como fallback)
    'GHE 03': 'PRODUCAO_GERAL',
    'EXECUCAO DE OBRA': 'PRODUCAO_GERAL',
    'EXECUCAO': 'PRODUCAO_GERAL',
    # Supervisão rejunte/limpeza
    'GHE 04': 'ENCARREGADO_SUPERVISAO',
    'SUPERVISAO REJUNTE': 'ENCARREGADO_SUPERVISAO',
    'SUPERVISAO REJUNTE LIMPEZA': 'ENCARREGADO_SUPERVISAO',
    'SUPERVISAO': 'ENCARREGADO_SUPERVISAO',
    # Administração de campo
    'GHE 05': 'ADMINISTRATIVO',
    'ADMINISTRACAO DE CAMPO': 'ADMINISTRATIVO',
    'ADMINISTRACAO': 'ADMINISTRATIVO',
    # Almoxarifado
    'GHE 06': 'ALMOXARIFE',
    'ALMOXARIFADO': 'ALMOXARIFE',
}


def _chave_banco_v2_por_nome_ghe(nome: str) -> str | None:
    """
    Tenta resolver o nome de um GHE (ex: 'GHE 03 - Execução de obra')
    para a chave correspondente no banco_matrizes_v2 (ex: 'PRODUCAO_GERAL').
    """
    s = norm(nome)
    # Tenta match direto
    if s in _MAPA_GHE_PARA_BANCO_KEY:
        return _MAPA_GHE_PARA_BANCO_KEY[s]
    # Tenta apenas o número do GHE (ex: 'GHE 03')
    m = re.match(r'GHE\s*(\d{1,2})', s)
    if m:
        chave_num = f'GHE {int(m.group(1)):02d}'
        if chave_num in _MAPA_GHE_PARA_BANCO_KEY:
            return _MAPA_GHE_PARA_BANCO_KEY[chave_num]
    # Tenta match parcial por token
    for token, chave in _MAPA_GHE_PARA_BANCO_KEY.items():
        if token in s:
            return chave
    return None


# ───────────────────────────────────────────────────────────────────────────
# MAPA CBO → cargo canônico (fallback quando nome não bate no banco)
# ───────────────────────────────────────────────────────────────────────────

_MAPA_CBO: dict = {}


def _carregar_mapa_cbo():
    global _MAPA_CBO
    if _MAPA_CBO:
        return _MAPA_CBO
    candidatos = [
        Path(__file__).parent.parent / 'data' / 'mapa_cbo_cargo.json',
        Path('data') / 'mapa_cbo_cargo.json',
    ]
    for p in candidatos:
        if p.exists():
            with p.open('r', encoding='utf-8') as f:
                raw = json.load(f)
            _MAPA_CBO = {k: v for k, v in raw.items() if not k.startswith('_')}
            return _MAPA_CBO
    return {}


def _extrair_cbo(nome_cargo: str) -> str | None:
    """Extrai código CBO de strings como 'CARGO PEDREIRO - CBO: 715210'."""
    m = re.search(r'CBO[:\s]*(\d{6})', str(nome_cargo), re.IGNORECASE)
    return m.group(1) if m else None


def cargo_canonico_por_cbo(cbo: str) -> str | None:
    """Retorna o nome canônico do cargo para um CBO, ou None se não encontrado."""
    mapa = _carregar_mapa_cbo()
    return mapa.get(str(cbo).strip())


def carregar_banco_matrizes(caminho):
    with Path(caminho).open('r', encoding='utf-8') as f:
        return json.load(f)


def _norm_bool(v):
    if isinstance(v, bool):
        return v
    return norm(str(v)) in {'X', 'SIM', 'TRUE', '1'}


def _norm_per(v):
    if v is None:
        return None
    s = str(v).strip().upper()
    if s in ('', 'NONE', 'FALSE', '-', 'NULL'):
        return None
    m = re.search(r'(\d+)', s)
    return m.group(1) if m else None


def _exam_obj(nome, dados=None):
    d = dados or {}
    return {
        'nome': normalizar_exame(nome),
        'adm': _norm_bool(d.get('adm')),
        'per': _norm_per(d.get('per')),
        'mro': _norm_bool(d.get('mro')),
        'ret': _norm_bool(d.get('ret')),
        'dem': _norm_bool(d.get('dem')),
    }


def _lista_de_exames(payload):
    if isinstance(payload, list):
        out = []
        for item in payload:
            if isinstance(item, str):
                out.append(_exam_obj(item))
            elif isinstance(item, dict):
                nome = item.get('nome') or item.get('Exame') or item.get('exame') or ''
                out.append(_exam_obj(nome, item))
        return out
    if isinstance(payload, dict):
        return [_exam_obj(payload.get('nome', ''), payload)]
    return []


# ───────────────────────────────────────────────────────────────────────────
# Detecta formato do banco (v2 flat vs v1 obras_referencia)
# ───────────────────────────────────────────────────────────────────────────

def _banco_e_v2(banco: dict) -> bool:
    """
    Retorna True se o banco usa estrutura flat do v2
    (chaves diretas como 'PINTOR', 'PEDREIRO', cada uma com 'exames': [...]).
    Retorna False se usa a estrutura legada v1 com 'obras_referencia'.
    """
    if 'obras_referencia' in banco:
        return False
    # Verifica se pelo menos uma chave tem 'exames' diretamente
    for v in banco.values():
        if isinstance(v, dict) and 'exames' in v:
            return True
    return False


# ───────────────────────────────────────────────────────────────────────────
# REFERENCIA TECNICA POR CARGO
# ───────────────────────────────────────────────────────────────────────────

def buscar_exames_por_cargo(nome_cargo: str, banco: dict) -> list | None:
    """
    Busca exames pelo nome canônico do cargo no banco.
    Suporta banco_matrizes_v2 (estrutura flat) e v1 (obras_referencia).

    Ordem de tentativas:
      1. Match direto pela chave normalizada do banco v2
      2. Resolução via mapa GHE → chave banco v2 (para nomes como 'GHE 03 - Execução de obra')
      3. Match pelo nome normalizado na estrutura v1 (obras_referencia)
      4. Via CBO embutido no nome
    """
    if _banco_e_v2(banco):
        # ── Banco v2: estrutura flat {CHAVE: {exames: [...]}} ──────────────
        # Normalização ESTRITA aplicada em AMBOS os lados (input + chave do banco)
        cargo_norm = normalizar_cargo(nome_cargo)

        # Tentativa 1: match direto (ambos os lados normalizados via normalizar_cargo)
        for chave, perfil in banco.items():
            if not isinstance(perfil, dict):
                continue
            if normalizar_cargo(chave.replace('_', ' ')) == cargo_norm:
                return perfil.get('exames')

        # Tentativa 2: resolve nome do GHE para chave do banco
        chave_ghe = _chave_banco_v2_por_nome_ghe(nome_cargo)
        if chave_ghe and chave_ghe in banco:
            return banco[chave_ghe].get('exames')

        # Tentativa 3: match parcial — o nome do cargo contém a chave do banco
        for chave, perfil in banco.items():
            if not isinstance(perfil, dict):
                continue
            chave_n = normalizar_cargo(chave.replace('_', ' '))
            if chave_n and chave_n in cargo_norm:
                return perfil.get('exames')

        # Tentativa 4: via CBO
        cbo = _extrair_cbo(nome_cargo)
        if cbo:
            nome_canonico = cargo_canonico_por_cbo(cbo)
            if nome_canonico:
                return buscar_exames_por_cargo(nome_canonico, banco)

        return None

    else:
        # ── Banco v1: estrutura obras_referencia > obra > ghe > cargos ─────
        def _buscar_nome_v1(cargo_n):
            melhor = None
            for obra in banco.get('obras_referencia', {}).values():
                for ghe in obra.values():
                    for cargo_ref, exames_ref in ghe.get('cargos', {}).items():
                        if normalizar_cargo(cargo_ref) == cargo_n:
                            candidato = list(exames_ref)
                            if melhor is None or len(candidato) > len(melhor):
                                melhor = candidato
            return melhor

        resultado = _buscar_nome_v1(normalizar_cargo(nome_cargo))
        if resultado:
            return resultado

        cbo = _extrair_cbo(nome_cargo)
        if cbo:
            nome_canonico = cargo_canonico_por_cbo(cbo)
            if nome_canonico:
                resultado = _buscar_nome_v1(normalizar_cargo(nome_canonico))
                if resultado:
                    return resultado

        return None


def enriquecer_ghe_com_banco(dados_ghe: list, banco: dict) -> tuple:
    """
    Recebe dados_ghe no formato:
        [{'ghe': str, 'cargos': [str, ...], 'riscos_mapeados': [...]}, ...]

    Para cada cargo tenta match no banco (v2 ou v1):
      1. Pelo nome normalizado / chave direta
      2. Pelo nome do GHE → mapa GHE→chave banco (novo, para Viverde e similares)
      3. Pelo CBO extraído do nome original (se presente)

    Retorna (dados_ghe_enriquecido, relatorio).
    O dados_ghe retornado tem o campo 'exames_banco' preenchido nos GHEs que deram match,
    para que processar_pcmso possa usar os exames corretos.
    """
    cargos_enriquecidos = []
    cargos_mantidos = []
    mapa_exames_banco = {}

    for ghe in dados_ghe:
        ghe_nome_original = ghe.get('ghe', '')

        for cargo in ghe.get('cargos', []):
            nome_cargo = str(cargo)
            cargo_norm = normalizar_cargo(nome_cargo)

            ja_processado = (
                cargo_norm in mapa_exames_banco
                or cargo_norm in [normalizar_cargo(c) for c in cargos_mantidos]
            )
            if ja_processado:
                continue

            # Tenta pelo nome do cargo
            exames_banco = buscar_exames_por_cargo(nome_cargo, banco)

            # Se não achou, tenta pelo nome completo do GHE
            if not exames_banco and ghe_nome_original and ghe_nome_original != nome_cargo:
                exames_banco = buscar_exames_por_cargo(ghe_nome_original, banco)

            if exames_banco:
                mapa_exames_banco[cargo_norm] = exames_banco
                # Injeta exames no GHE para que processar_pcmso os use
                ghe['exames_banco'] = exames_banco
                cargos_enriquecidos.append(nome_cargo)
            else:
                cargos_mantidos.append(nome_cargo)

    relatorio = {
        'cargos_enriquecidos': cargos_enriquecidos,
        'cargos_mantidos': cargos_mantidos,
        'mapa_exames_banco': mapa_exames_banco,
    }
    return dados_ghe, relatorio


# ───────────────────────────────────────────────────────────────────────────
# Funcoes legadas mantidas para compatibilidade
# ───────────────────────────────────────────────────────────────────────────

def pcmso_df_para_dict(df) -> dict:
    resultado = {}
    for _, row in df.iterrows():
        ghe_raw = str(row.get('GHE / Setor', '')).strip()
        cargo   = str(row.get('Cargo', '')).strip()
        exame   = str(row.get('Exame', '')).strip()
        if not ghe_raw or not cargo or not exame:
            continue
        m = re.search(r'GHE\s*(\d{1,2})', ghe_raw, re.IGNORECASE)
        ghe_key = f"GHE {int(m.group(1)):02d}" if m else ghe_raw
        resultado.setdefault(ghe_key, {})
        resultado[ghe_key].setdefault(cargo, [])
        resultado[ghe_key][cargo].append({
            'nome': exame,
            'adm':  row.get('ADM', '-'),
            'per':  row.get('PER', '-'),
            'mro':  row.get('MRO', '-'),
            'ret':  row.get('RT',  '-'),
            'dem':  row.get('DEM', '-'),
        })
    return resultado


def auditar_pcmso(dados_pcmso, banco, obra_id=None):
    divergencias = []
    resumo = defaultdict(int)
    obras = banco.get('obras_referencia', {})
    if obra_id:
        obras = {obra_id: obras.get(obra_id, {})}

    for obra_key, ghes in obras.items():
        for ghe_id, ghe_ref in ghes.items():
            saida_ghe = dados_pcmso.get(ghe_id) or dados_pcmso.get(ghe_id.replace(' ', '')) or {}
            cargos_saida = {normalizar_cargo(k): v for k, v in (saida_ghe or {}).items()}

            for cargo_ref, exames_ref in ghe_ref.get('cargos', {}).items():
                cargo_n = normalizar_cargo(cargo_ref)
                payload_saida = cargos_saida.get(cargo_n)

                if payload_saida is None:
                    divergencias.append({'obra': obra_key, 'ghe': ghe_id, 'cargo': cargo_n,
                                         'tipo': 'cargo_faltando', 'detalhe': 'cargo ausente'})
                    resumo['cargo_faltando'] += 1
                    continue

                mapa_saida = {normalizar_exame(x['nome']): x
                              for x in _lista_de_exames(payload_saida)}
                mapa_ref   = {normalizar_exame(e['nome']): e for e in exames_ref}

                for nome in sorted(set(mapa_ref) - set(mapa_saida)):
                    divergencias.append({'obra': obra_key, 'ghe': ghe_id, 'cargo': cargo_n,
                                         'tipo': 'exame_faltando', 'detalhe': nome})
                    resumo['exame_faltando'] += 1

                for nome in sorted(set(mapa_saida) - set(mapa_ref)):
                    divergencias.append({'obra': obra_key, 'ghe': ghe_id, 'cargo': cargo_n,
                                         'tipo': 'exame_excedente', 'detalhe': nome})
                    resumo['exame_excedente'] += 1

                for nome in sorted(set(mapa_ref) & set(mapa_saida)):
                    r, s = mapa_ref[nome], mapa_saida[nome]
                    for flag in ('adm', 'mro', 'ret', 'dem'):
                        rv = _norm_bool(r.get(flag))
                        sv = _norm_bool(s.get(flag))
                        if rv != sv:
                            divergencias.append({
                                'obra': obra_key, 'ghe': ghe_id, 'cargo': cargo_n,
                                'tipo': 'flag_incorreta',
                                'detalhe': f'{nome}::{flag} esperado={rv} atual={sv}'
                            })
                            resumo['flag_incorreta'] += 1
                    rp = _norm_per(r.get('per'))
                    sp = _norm_per(s.get('per'))
                    if rp != sp:
                        divergencias.append({
                            'obra': obra_key, 'ghe': ghe_id, 'cargo': cargo_n,
                            'tipo': 'periodicidade_incorreta',
                            'detalhe': f'{nome}::per esperado={rp} atual={sp}'
                        })
                        resumo['periodicidade_incorreta'] += 1

    return {
        'ok': not divergencias,
        'total_divergencias': len(divergencias),
        'resumo': dict(resumo),
        'divergencias': divergencias,
    }


def formatar_relatorio_auditoria(resultado):
    linhas = [f"Auditoria concluída — {resultado.get('total_divergencias', 0)} divergência(s) detectada(s)."]
    linhas.append('')
    linhas.append(f"Total de divergencias: {resultado.get('total_divergencias', 0)}")
    for k, v in sorted(resultado.get('resumo', {}).items()):
        linhas.append(f'  {k}: {v}')
    if resultado.get('divergencias'):
        linhas.append('')
        linhas.append('Detalhes:')
        for d in resultado['divergencias']:
            linhas.append(f"  [{d['obra']}] {d['ghe']} | {d['cargo']} | {d['tipo']} | {d['detalhe']}")
    return '\n'.join(linhas)


def obra_tem_matriz(banco: dict, obra_id: str) -> bool:
    obras = banco.get("obras_referencia", {})
    return obra_id in obras and bool(obras[obra_id])
