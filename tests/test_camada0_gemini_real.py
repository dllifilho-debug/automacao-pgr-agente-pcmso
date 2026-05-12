"""
Testes Camada 0A — resolução de GHE via título (fallback Gemini).

Cenário: o Gemini retorna GHEs com títulos descritivos (texto livre) e
riscos em linguagem natural.  resolver_chave_ghe_semantico() falha
(riscos não correspondem a nenhuma assinatura estruturada), então
resolver_chave_ghe(ghe_nome) é acionado como fallback.
"""
import pytest
from modules.agente_medico_ia import processar_cargo_ia


def test_serralheiro_via_solda_titulo():
    """GHE 'Solda - Solda' deve mapear para GHE_ESTRUTURA_SERRALHERIA."""
    r = processar_cargo_ia(
        cargo='serralheiro',
        riscos=[],
        contexto={},
        ghe_nome='GHE 25 - Solda - Solda',
    )
    assert r['chave_ghe'] == 'GHE_ESTRUTURA_SERRALHERIA', (
        f"chave_ghe esperada 'GHE_ESTRUTURA_SERRALHERIA', obtida '{r['chave_ghe']}'"
    )


def test_betoneira_via_argamassa_titulo():
    """GHE 'Preparação argamassa - Operação betoneira' → GHE_ESTRUTURA_BETONEIRA."""
    r = processar_cargo_ia(
        cargo='Operador de Betoneira',
        riscos=[],
        contexto={},
        ghe_nome='Preparação argamassa - Operação betoneira',
    )
    assert r['chave_ghe'] == 'GHE_ESTRUTURA_BETONEIRA', (
        f"chave_ghe esperada 'GHE_ESTRUTURA_BETONEIRA', obtida '{r['chave_ghe']}'"
    )


def test_serralheiro_ec_6m_via_titulo_solda():
    """Camada 0A via título 'Solda': EC deve ter periodicidade semestral (per='6')."""
    r = processar_cargo_ia(
        cargo='serralheiro',
        riscos=['Ruído', 'Cromo', 'Fumo metálico'],
        contexto={},
        ghe_nome='GHE 25 - Solda - Solda',
    )
    assert r['fonte_regra'] == 'banco_ghe_cargo_v1', (
        f"fonte_regra esperada 'banco_ghe_cargo_v1', obtida '{r['fonte_regra']}'"
    )
    assert r['chave_ghe'] == 'GHE_ESTRUTURA_SERRALHERIA'

    nomes_lower = [e['nome'].lower() for e in r['exames']]
    ec_list = [e for e in r['exames'] if 'cl' in e['nome'].lower() and 'nico' in e['nome'].lower()]
    assert ec_list, (
        f"Exame Clínico não encontrado. Exames retornados: {[e['nome'] for e in r['exames']]}"
    )
    assert ec_list[0]['per'] == '6', (
        f"EC per esperado '6', obtido '{ec_list[0]['per']}'"
    )


def test_betoneira_apenas_4_exames_via_titulo():
    """Betoneira deve retornar exatamente [EC, Audiometria, Espirometria, RX OIT]."""
    r = processar_cargo_ia(
        cargo='Operador de Betoneira',
        riscos=[],
        contexto={},
        ghe_nome='Preparação argamassa - Operação betoneira',
    )
    assert r['chave_ghe'] == 'GHE_ESTRUTURA_BETONEIRA'

    exames = r['exames']
    nomes = [e['nome'] for e in exames]
    assert len(nomes) == 4, (
        f"Esperados 4 exames, obtidos {len(nomes)}: {nomes}"
    )

    nomes_lower = [n.lower() for n in nomes]
    assert any('cl' in n and 'nico' in n for n in nomes_lower), \
        f"Exame Clínico ausente em {nomes}"
    assert any('audiometria' in n for n in nomes_lower), \
        f"Audiometria ausente em {nomes}"
    assert any('espirometria' in n for n in nomes_lower), \
        f"Espirometria ausente em {nomes}"
    assert any('torax' in n or 't' + chr(243) + 'rax' in n for n in nomes_lower), \
        f"RX de Tórax OIT ausente em {nomes}"
