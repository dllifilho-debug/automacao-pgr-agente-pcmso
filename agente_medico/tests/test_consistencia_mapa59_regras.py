from pathlib import Path
import re

from agente_medico.motor import protocolo
from agente_medico.motor.protocolo import Protocolo

_TESTS_DIR = Path(__file__).parent
_PROTOCOLO_DIR = _TESTS_DIR.parent / "protocolo"
_REPO_ROOT = _TESTS_DIR.parent.parent
_MAPA_DOC = _REPO_ROOT / "docs" / "PROTOCOLO_AGENTE_MEDICO.md"

_PREFIXO_REGRA_BIO = "R-BIO-04-"

# Agentes do mapa §5.9 roteados por PACOTE, não pela família R-BIO-04-*.
# Cada entrada exige o ID do pacote; o teste valida que o pacote existe em
# protocolo.regras (senão a exceção seria carimbo vazio).
# benzeno: TTMA/S-PMA semestral [per] via R-PKG-BZ (§6), fora da família por
# decisão de arquitetura (003.CY, aplicação de D-ARQ-59).
EXCECOES_PACOTE = {"benzeno": "R-PKG-BZ"}

# Reconciliação nome-de-exibição do §5.9 -> slug canônico do regras.yaml.
# A coluna "agente" do §5.9 é humana (prosa com qualificadores clínicos); o slug
# é a chave de máquina. Toda linha em prosa exige entrada aqui, ou o guardião
# vermelha (faltando). NÃO derivar por normalização — mapeamento é explícito.
APELIDOS_MAPA = {
    "chumbo (inorgânico)": "chumbo",
    "cromo hexavalente (comp. solúveis)": "cromo_hexavalente",
    "cádmio (inorgânico)": "cadmio",
    "flúor / HF / fluoretos inorgânicos": "fluoretos",
    "indutores de metahemoglobina (classe)": "indutores_metahemoglobina",
    "inseticidas inibidores da colinesterase": "inseticidas_inibidores_colinesterase",
}

_COL_QUADRO = re.compile(r"^\d+/(EE|SC)$")
_SEP = re.compile(r"^\|[\s:|-]+\|$")


def _slugs_bio(proto: Protocolo) -> set[str]:
    return {
        r["id"][len(_PREFIXO_REGRA_BIO):]
        for r in proto.regras
        if r["id"].startswith(_PREFIXO_REGRA_BIO)
    }


def _ids(proto: Protocolo) -> set[str]:
    return {r["id"] for r in proto.regras}


def _agentes_mapa_59(texto: str) -> set[str]:
    linhas = texto.splitlines()
    inicio = None
    for i, linha in enumerate(linhas):
        l = linha.lstrip("> ").rstrip()
        if l.startswith("#") and "5.9" in l:
            inicio = i
            break
    if inicio is None:
        return set()
    agentes: set[str] = set()
    apos_sep = False
    for linha in linhas[inicio + 1:]:
        l = linha.lstrip("> ").rstrip()
        if l.startswith("## "):
            break
        if _SEP.match(l):
            apos_sep = True
            continue
        if not apos_sep:
            continue
        if not l.startswith("|"):
            break
        cols = [c.strip() for c in l.strip("|").split("|")]
        if len(cols) < 3:
            continue
        agente, quadro = cols[0], cols[1]
        if _COL_QUADRO.match(quadro):
            agentes.add(APELIDOS_MAPA.get(agente, agente))
    return agentes


def test_mapa59_bijeta_com_regras_bio_modulo_excecoes() -> None:
    proto = protocolo.carregar(_PROTOCOLO_DIR)
    mapa = _agentes_mapa_59(_MAPA_DOC.read_text(encoding="utf-8"))
    regras = _slugs_bio(proto)

    faltando = mapa - regras - set(EXCECOES_PACOTE)
    assert not faltando, f"§5.9 sem R-BIO-04-* nem exceção: {sorted(faltando)}"

    orfas = regras - mapa
    assert not orfas, f"R-BIO-04-* sem linha no §5.9: {sorted(orfas)}"


def test_excecoes_pacote_apontam_para_regra_existente() -> None:
    proto = protocolo.carregar(_PROTOCOLO_DIR)
    ids = _ids(proto)
    for agente, pkg in EXCECOES_PACOTE.items():
        assert pkg in ids, f"exceção {agente!r} → pacote inexistente {pkg!r}"
