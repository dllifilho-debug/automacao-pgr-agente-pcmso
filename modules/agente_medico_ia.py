import json
import re
import unicodedata
from pathlib import Path

_BANCO_CACHE = None
_BANCO_PATH = Path(__file__).parent.parent / 'data' / 'banco_ghe_cargo_v1.json'


def _sem_acentos(texto):
    return unicodedata.normalize('NFKD', str(texto or '')).encode('ascii', 'ignore').decode('ascii')


def _norm_frag(texto):
    """Remove accents, uppercase, replace non-alphanumeric with spaces."""
    t = _sem_acentos(str(texto or '')).upper()
    return re.sub(r'[^A-Z0-9]+', ' ', t).strip()


def _norm_chave(texto):
    """Remove accents, uppercase, replace non-alphanumeric with underscores — for key comparison."""
    t = _sem_acentos(str(texto or '')).upper().strip()
    return re.sub(r'[^A-Z0-9]+', '_', t).strip('_')


def _banco():
    global _BANCO_CACHE
    if _BANCO_CACHE is None:
        with _BANCO_PATH.open('r', encoding='utf-8') as f:
            _BANCO_CACHE = json.load(f)
    return _BANCO_CACHE


# Each frozenset is a set of normalized risk keys that must ALL be present
# to trigger the corresponding GHE key.  Checked by subset matching against
# the risk set extracted from the PGR (works well for structured local output).
# When Gemini returns free-text risks, these signatures often fail (e.g. the
# PGR may say "Cromo" instead of "Manganês"), triggering the title-based
# fallback in processar_cargo_ia().
_ASSINATURAS_RISCO_GHE = {
    frozenset(['FUMOS_METALICOS', 'MANGANES']): 'GHE_ESTRUTURA_SERRALHERIA',
    frozenset(['FUMO_METALICO',   'MANGANES']): 'GHE_ESTRUTURA_SERRALHERIA',
    frozenset(['FUMOS_METALICOS', 'CROMO']):    'GHE_ESTRUTURA_SERRALHERIA',
    frozenset(['CROMO',           'MANGANES']): 'GHE_ESTRUTURA_SERRALHERIA',
    frozenset(['BENZENO',         'TOLUENO']):  'GHE_ESTRUTURA_PINTURA',
    frozenset(['TOLUENO',         'XILENO']):   'GHE_ESTRUTURA_PINTURA',
}

# Ordered list of (fragment, ghe_key).  More specific fragments come first
# so they take priority over shorter, more ambiguous ones.
_MAPA_GHE_CHAVE = [
    # Serralheria / Solda
    ('SOLDA',               'GHE_ESTRUTURA_SERRALHERIA'),
    ('SERRALHERIA',         'GHE_ESTRUTURA_SERRALHERIA'),
    ('SERRALHEIRO',         'GHE_ESTRUTURA_SERRALHERIA'),
    # Formas de concreto armado (carpinteiro de forma)
    ('FORMA DE PILAR',      'GHE_ESTRUTURA_FORMA'),
    ('EXECUCAO FORMA',      'GHE_ESTRUTURA_FORMA'),
    ('CONCRETO ARMADO',     'GHE_ESTRUTURA_FORMA'),
    # Betoneira
    ('BETONEIRA',           'GHE_ESTRUTURA_BETONEIRA'),
    ('ARGAMASSA',           'GHE_ESTRUTURA_BETONEIRA'),
    # Cremalheira (longer fragment first)
    ('ELEVADOR CREMALHEIRA','GHE_ESTRUTURA_CREMALHEIRA_MONT'),
    ('CREMALHEIRA',         'GHE_ESTRUTURA_CREMALHEIRA_MONT'),
    # Hidro-sanitárias (multiple forms)
    ('INST HIDRO',          'GHE_ESTRUTURA_HIDRO'),
    ('HIDRO SANIT',         'GHE_ESTRUTURA_HIDRO'),
    ('TUBULACAO',           'GHE_ESTRUTURA_HIDRO'),
    ('INSTALACAO HIDR',     'GHE_ESTRUTURA_HIDRO'),
]


def resolver_chave_ghe_semantico(riscos):
    """Return GHE key by matching normalized risk keywords against _ASSINATURAS_RISCO_GHE.

    Expects risks as a list of dicts (with 'nome_agente' key) OR a list of strings.
    Works reliably when the PGR local parser provides normalized risk names
    (e.g. 'FUMOS METALICOS', 'MANGANES').  Typically returns None when Gemini
    provides free-text risks (e.g. 'Cromo', 'Fumo metálico'), because the
    compound signature won't match — use resolver_chave_ghe() as fallback.
    """
    if not riscos:
        return None

    norm_riscos = set()
    for r in riscos:
        if isinstance(r, dict):
            nome = r.get('nome_agente') or r.get('nome') or ''
        else:
            nome = str(r)
        chave = _norm_chave(nome)
        if chave:
            norm_riscos.add(chave)

    for sig, ghe_key in _ASSINATURAS_RISCO_GHE.items():
        if sig.issubset(norm_riscos):
            return ghe_key

    return None


def resolver_chave_ghe(ghe_nome):
    """Return GHE key by matching fragments of the GHE title against _MAPA_GHE_CHAVE.

    Works for free-text GHE names returned by Gemini (e.g. 'Solda - Solda',
    'Preparação argamassa - Operação betoneira').
    """
    if not ghe_nome:
        return None

    norm = _norm_frag(ghe_nome)
    for frag, ghe_key in _MAPA_GHE_CHAVE:
        norm_frag = _norm_frag(frag)
        if norm_frag in norm:
            return ghe_key

    return None


def processar_cargo_ia(cargo, riscos, contexto, ghe_nome=None):
    """Resolve exames for a cargo/GHE using banco_ghe_cargo_v1.json (Camada 0A).

    Resolution order:
    1. resolver_chave_ghe_semantico(riscos)  — fast, works with structured risks
    2. resolver_chave_ghe(ghe_nome)          — fallback, works with Gemini titles

    Returns dict with keys: fonte_regra, chave_ghe, exames.
    """
    chave_ghe = resolver_chave_ghe_semantico(riscos) if riscos else None

    if not chave_ghe and ghe_nome:
        chave_ghe = resolver_chave_ghe(ghe_nome)

    if not chave_ghe:
        return {'fonte_regra': 'sem_regra', 'chave_ghe': None, 'exames': []}

    banco = _banco()
    regras = banco.get(chave_ghe)
    if not regras:
        return {'fonte_regra': 'chave_sem_dados', 'chave_ghe': chave_ghe, 'exames': []}

    return {
        'fonte_regra': 'banco_ghe_cargo_v1',
        'chave_ghe': chave_ghe,
        'exames': list(regras.get('exames', [])),
    }
