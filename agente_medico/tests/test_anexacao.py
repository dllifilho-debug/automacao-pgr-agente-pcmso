from __future__ import annotations

from agente_medico.motor.estagios.anexacao import anexar_pendencias
from agente_medico.motor.tipos import ExameEmitido, Pendencia


def _linha(exame: str) -> ExameEmitido:
    return ExameEmitido(exame=exame, periodicidade_meses=0)


def _pend(regra: str, alvo: tuple[str, ...]) -> Pendencia:
    return Pendencia(
        tipo="predicado_ausente",
        destinatario="elaborador_pgr",
        motivo=f"bloqueio {regra}",
        bloqueante=True,
        regra_origem=regra,
        exames_alvo=alvo,
    )


def test_anexa_quando_slug_casa() -> None:
    linhas = [_linha("rx_torax_oit")]
    p = _pend("R-RX-01-adm", ("rx_torax_oit",))
    linhas, restantes = anexar_pendencias(linhas, [p])
    assert restantes == []
    assert linhas[0].pendencias_anexadas == [p]


def test_sem_match_volta_para_matriz() -> None:
    linhas = [_linha("audiometria")]
    p = _pend("R-RX-01-adm", ("rx_torax_oit",))
    linhas, restantes = anexar_pendencias(linhas, [p])
    assert restantes == [p]
    assert linhas[0].pendencias_anexadas == []


def test_ancora_vazia_nao_anexa() -> None:
    linhas = [_linha("rx_torax_oit")]
    p = _pend("R-X", ())
    linhas, restantes = anexar_pendencias(linhas, [p])
    assert restantes == [p]
    assert linhas[0].pendencias_anexadas == []


def test_interseccao_parcial_anexa_so_o_presente() -> None:
    linhas = [_linha("rx_torax_oit")]
    p = _pend("R-X", ("rx_torax_oit", "espirometria"))
    linhas, restantes = anexar_pendencias(linhas, [p])
    assert restantes == []
    assert linhas[0].pendencias_anexadas == [p]


def test_piso_nunca_sem_teto_visivel() -> None:
    # Requisito de segurança D-ARQ-31: linha com âncora-casando NUNCA sai sem a
    # pendência anexada. Cinco pendências (família sílica) sobre uma linha de RX.
    linhas = [_linha("rx_torax_oit")]
    fam = ["R-RX-01-adm", "R-RX-01-sem", "R-RX-01-baixa", "R-RX-01-media", "R-RX-01-alta"]
    pends = [_pend(r, ("rx_torax_oit",)) for r in fam]
    linhas, restantes = anexar_pendencias(linhas, pends)
    assert restantes == []
    assert len(linhas[0].pendencias_anexadas) == 5
    assert {p.regra_origem for p in linhas[0].pendencias_anexadas} == set(fam)
