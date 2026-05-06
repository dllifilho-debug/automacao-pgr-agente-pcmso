"""
tests/test_banco_ghe_cargo.py

Testes de regressão para data/banco_ghe_cargo_v1.json gerado por
scripts/migrar_pdf_rq61.py.

Para gerar/regenerar o banco antes de rodar:
  python -X utf8 scripts/migrar_pdf_rq61.py
"""

import json
import pytest
from pathlib import Path

ROOT      = Path(__file__).resolve().parent.parent
JSON_PATH = ROOT / "data" / "banco_ghe_cargo_v1.json"


# ─── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def banco() -> dict:
    """Load banco_ghe_cargo_v1.json; skip if missing or empty (CI without PDF)."""
    if not JSON_PATH.exists() or JSON_PATH.stat().st_size == 0:
        pytest.skip(
            "banco_ghe_cargo_v1.json não existe ou está vazio — "
            "execute: python -X utf8 scripts/migrar_pdf_rq61.py"
        )
    with open(JSON_PATH, encoding="utf-8") as f:
        return json.load(f)


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _exame_por_nome(exames: list, fragmento: str) -> dict | None:
    """Return first exam whose name contains *fragmento* (case-insensitive)."""
    frag = fragmento.lower()
    return next(
        (e for e in exames if frag in e.get("nome", "").lower()),
        None,
    )


# ─── Testes ───────────────────────────────────────────────────────────────────

def test_banco_nao_vazio(banco):
    """Banco deve ter pelo menos 30 entradas (31 GHEs × ~2 cargos cada)."""
    assert len(banco) >= 30, (
        f"Esperado >= 30 entradas no banco, encontrado {len(banco)}. "
        "Regenere com: python -X utf8 scripts/migrar_pdf_rq61.py"
    )


def test_serralheiro_exame_clinico_6m(banco):
    """
    RQ.61 Viverde — GHE Serralheria: Serralheiro com risco de cromo hexavalente
    tem Exame Clínico SEMESTRAL (6M), diferente do padrão anual da maioria.
    """
    chave = "GHE_ESTRUTURA_SERRALHERIA:SERRALHEIRO"
    assert chave in banco, (
        f"Chave {chave!r} não encontrada no banco. "
        f"Chaves disponíveis com SERRALHERIA: "
        f"{[k for k in banco if 'SERRALHERIA' in k]}"
    )
    exames = banco[chave]["exames"]
    clinico = _exame_por_nome(exames, "clinico")
    assert clinico is not None, (
        f"'Exame Clínico' não encontrado em {chave}. "
        f"Exames presentes: {[e['nome'] for e in exames]}"
    )
    assert clinico["per"] == "6", (
        f"Periodicidade do Exame Clínico para Serralheiro: "
        f"esperado '6', obtido '{clinico['per']}'"
    )
    assert clinico["adm"] is True, "Exame Clínico do Serralheiro deve ter adm=True"


def test_betoneira_sem_acuidade_visual(banco):
    """
    Operador de Betoneira não tem Acuidade Visual no protocolo RQ.61
    (diferente de outros operadores de máquinas que têm).
    """
    chave = "GHE_ESTRUTURA_BETONEIRA:OPERADOR_BETONEIRA"
    assert chave in banco, (
        f"Chave {chave!r} não encontrada. "
        f"Chaves com BETONEIRA: {[k for k in banco if 'BETONEIRA' in k]}"
    )
    exames = banco[chave]["exames"]
    nomes  = [e["nome"].lower() for e in exames]
    assert not any("acuidade" in n for n in nomes), (
        f"Acuidade Visual NÃO deve constar no protocolo de Operador de Betoneira, "
        f"mas foi encontrada. Exames: {[e['nome'] for e in exames]}"
    )


def test_carpinteiro_rx_oit_24m(banco):
    """
    Carpinteiro em GHE Estrutura-Forma tem RX de Tórax OIT a cada 24 meses
    (exposição a poeira de madeira — periodicidade bienal, não semestral).
    """
    chave = "GHE_ESTRUTURA_FORMA:CARPINTEIRO"
    assert chave in banco, (
        f"Chave {chave!r} não encontrada. "
        f"Chaves com FORMA: {[k for k in banco if 'FORMA' in k]}"
    )
    exames = banco[chave]["exames"]
    rx = _exame_por_nome(exames, "raio") or _exame_por_nome(exames, "torax")
    assert rx is not None, (
        f"'Raio X / Tórax' não encontrado em {chave}. "
        f"Exames presentes: {[e['nome'] for e in exames]}"
    )
    assert rx["per"] == "24", (
        f"Periodicidade RX Tórax OIT para Carpinteiro: "
        f"esperado '24', obtido '{rx['per']}'"
    )


def test_pintor_acabamento_clinico_6m(banco):
    """
    Pintor em GHE Acabamento-Pintura (tolueno/xileno/estireno como ototóxicos)
    tem Exame Clínico SEMESTRAL — mais restritivo que pintor de estrutura.
    """
    chave = "GHE_ACABAMENTO_PINTURA:PINTOR"
    assert chave in banco, (
        f"Chave {chave!r} não encontrada. "
        f"Chaves com PINTURA: {[k for k in banco if 'PINTURA' in k]}"
    )
    exames = banco[chave]["exames"]
    clinico = _exame_por_nome(exames, "clinico")
    assert clinico is not None, (
        f"'Exame Clínico' não encontrado em {chave}. "
        f"Exames: {[e['nome'] for e in exames]}"
    )
    assert clinico["per"] == "6", (
        f"Periodicidade Exame Clínico para Pintor Acabamento: "
        f"esperado '6', obtido '{clinico['per']}'"
    )


# ─── Testes de sanidade estrutural ────────────────────────────────────────────

def test_todas_entradas_tem_exames(banco):
    """Nenhuma entrada do banco pode ter lista de exames vazia."""
    vazias = [k for k, v in banco.items() if not v.get("exames")]
    assert not vazias, (
        f"{len(vazias)} entradas sem exames: {vazias[:5]}..."
    )


def test_todas_entradas_tem_campos_obrigatorios(banco):
    """Cada entrada deve ter: ghe_descricao, cargo, exames, fonte."""
    campos = {"ghe_descricao", "cargo", "exames", "fonte"}
    problemas = []
    for chave, entrada in banco.items():
        faltando = campos - set(entrada.keys())
        if faltando:
            problemas.append(f"{chave}: faltando {faltando}")
    assert not problemas, "\n".join(problemas)


def test_chaves_canonicas_presentes(banco):
    """
    Verifica presença das chaves canônicas mais importantes para o Viverde,
    garantindo cobertura mínima dos GHEs do PDF RQ.61.
    """
    chaves_esperadas = [
        "GHE_ESTRUTURA_FORMA:CARPINTEIRO",
        "GHE_ESTRUTURA_ARMACAO:ARMADOR",
        "GHE_ESTRUTURA_BETONEIRA:OPERADOR_BETONEIRA",
        "GHE_ESTRUTURA_SERRALHERIA:SERRALHEIRO",
        "GHE_ESTRUTURA_HIDRO:ENCANADOR",
        "GHE_ACABAMENTO_PINTURA:PINTOR",
        "GHE_ACABAMENTO_MANTA_ASFALTICA:IMPERMEABILIZADOR",
        "GHE_ADMIN_ENGENHARIA:ENGENHEIRO",
        "GHE_ADMIN_ALMOXARIFADO:ALMOXARIFE",
    ]
    faltando = [c for c in chaves_esperadas if c not in banco]
    assert not faltando, (
        f"Chaves canônicas ausentes no banco ({len(faltando)}): {faltando}"
    )


def test_exames_tem_campos_obrigatorios(banco):
    """Cada exame deve ter: nome, adm, per, mro, ret, dem."""
    campos = {"nome", "adm", "per", "mro", "ret", "dem"}
    problemas = []
    for chave, entrada in banco.items():
        for ex in entrada.get("exames", []):
            faltando = campos - set(ex.keys())
            if faltando:
                problemas.append(f"{chave}/{ex.get('nome','?')}: faltando {faltando}")
    assert not problemas, "\n".join(problemas[:10])


def test_periodicidade_valores_validos(banco):
    """Periodicidade deve ser string de número inteiro (ex: '6', '12', '24', '60')."""
    invalidos = []
    for chave, entrada in banco.items():
        for ex in entrada.get("exames", []):
            per = ex.get("per", "")
            if not str(per).isdigit():
                invalidos.append(f"{chave}/{ex.get('nome','?')}: per={per!r}")
    assert not invalidos, (
        f"{len(invalidos)} exames com periodicidade inválida: {invalidos[:5]}"
    )
