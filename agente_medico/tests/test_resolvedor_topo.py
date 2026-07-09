from __future__ import annotations

from datetime import date

from agente_medico.motor.estagios.gates import stage_1_gates
from agente_medico.motor.resolvedor_topo import resolver_candidata, resolver_validade
from agente_medico.motor.tipos import PGR, CandidataValidade, EnvelopeVerbatim


def _envelope(validade_textos: tuple[str, ...]) -> EnvelopeVerbatim:
    return EnvelopeVerbatim(
        validade_textos=validade_textos,
        responsavel_tecnico="Fulano de Tal",
        titulo_rt="Eng. de Segurança do Trabalho",
        registro_profissional="CREA – 000000",
    )


def _pgr(validade: date, assinatura: bool = True) -> PGR:
    return PGR(validade=validade, assinatura_engenheiro=assinatura, ghes=())


def test_gabarito_003bv_resolve_3_candidatas_proposta_mais_recente() -> None:
    envelope = _envelope(("FEVEREIRO 2023", "FEVEREIRO 2024", "FEVEREIRO 2025"))
    candidatas, proposta = resolver_validade(envelope)
    assert candidatas == (
        CandidataValidade(texto="FEVEREIRO 2023", data=date(2023, 2, 1)),
        CandidataValidade(texto="FEVEREIRO 2024", data=date(2024, 2, 1)),
        CandidataValidade(texto="FEVEREIRO 2025", data=date(2025, 2, 1)),
    )
    assert proposta == date(2025, 2, 1)


def test_caso_concreto_dt003bv01_gate_flip_com_validade_recente_nao_bloqueia() -> None:
    hoje = date(2026, 7, 8)
    pgr = _pgr(validade=date(2025, 2, 1))
    result = stage_1_gates(pgr, hoje=hoje)
    assert not any(p.regra_origem == "R-PGR-06" for p in result)


def test_caso_concreto_dt003bv01_gate_flip_com_validade_antiga_bloqueia() -> None:
    hoje = date(2026, 7, 8)
    pgr = _pgr(validade=date(2023, 2, 1))
    result = stage_1_gates(pgr, hoje=hoje)
    pendencias_r06 = [p for p in result if p.regra_origem == "R-PGR-06"]
    assert len(pendencias_r06) == 1
    assert pendencias_r06[0].bloqueante is True


def test_12_meses_por_extenso_resolvem_para_o_mes_correto() -> None:
    meses = [
        ("JANEIRO", 1),
        ("FEVEREIRO", 2),
        ("MARÇO", 3),
        ("ABRIL", 4),
        ("MAIO", 5),
        ("JUNHO", 6),
        ("JULHO", 7),
        ("AGOSTO", 8),
        ("SETEMBRO", 9),
        ("OUTUBRO", 10),
        ("NOVEMBRO", 11),
        ("DEZEMBRO", 12),
    ]
    for nome, numero in meses:
        candidata = resolver_candidata(f"{nome} 2024")
        assert candidata.data == date(2024, numero, 1), nome


def test_acentos_marco_com_e_sem_cedilha_resolvem_igual() -> None:
    assert resolver_candidata("MARÇO 2024").data == date(2024, 3, 1)
    assert resolver_candidata("MARCO 2024").data == date(2024, 3, 1)


def test_case_insensitive() -> None:
    assert resolver_candidata("fevereiro 2025").data == date(2025, 2, 1)


def test_prefixo_tolerado() -> None:
    assert resolver_candidata("GOIÂNIA, FEVEREIRO 2023").data == date(2023, 2, 1)


def test_formatos_nao_suportados_resolvem_para_data_none() -> None:
    assert resolver_candidata("03/02/2025").data is None
    assert resolver_candidata("PGR 2023").data is None
    assert resolver_candidata("").data is None


def test_envelope_so_com_nao_parseaveis_proposta_none() -> None:
    envelope = _envelope(("03/02/2025", "PGR 2023", ""))
    candidatas, proposta = resolver_validade(envelope)
    assert all(c.data is None for c in candidatas)
    assert proposta is None


def test_ambiguidade_dois_mes_ano_na_mesma_string_resolve_para_none() -> None:
    candidata = resolver_candidata("FEVEREIRO 2023 ATUALIZADO MARÇO 2024")
    assert candidata.data is None
