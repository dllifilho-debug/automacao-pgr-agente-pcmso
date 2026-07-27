from __future__ import annotations

from agente_medico.motor.estagios.consolidacao import stage_8_consolidacao
from agente_medico.motor.tipos import ExameEmitido, Momento, Motivo, Pendencia


def _motivo(regra_id: str) -> Motivo:
    return Motivo(regra_id=regra_id, predicado="teste", risco_origem=None, detalhe=None)


def _exame(
    nome: str,
    periodicidade: int,
    momentos: set[Momento],
    regra_id: str = "R-A",
    apos_15a: int | None = None,
    pendencias: list[Pendencia] | None = None,
) -> ExameEmitido:
    return ExameEmitido(
        exame=nome,
        periodicidade_meses=periodicidade,
        momentos=set(momentos),
        motivos=[_motivo(regra_id)],
        periodicidade_apos_15a=apos_15a,
        pendencias_anexadas=list(pendencias) if pendencias is not None else [],
    )


def test_dedup_simples_mesma_periodicidade_mesmos_momentos() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("Hemograma", 12, {Momento.ADM}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert len(result[0].motivos) == 2
    assert result[0].motivos[0].regra_id == "R-A"
    assert result[0].motivos[1].regra_id == "R-B"


def test_dedup_merge_momentos() -> None:
    entrada = [
        _exame("Audiometria", 12, {Momento.ADM, Momento.PER}, "R-A"),
        _exame("Audiometria", 12, {Momento.MR}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].momentos == {Momento.ADM, Momento.PER, Momento.MR}


def test_dedup_slug_canonico() -> None:
    """
    Dedup agora opera sobre slug canônico do vocabulário, não sobre
    normalização de string humana. Dois exames com o mesmo slug são
    deduplicados; slugs diferentes (mesmo que humanamente parecidos)
    são tratados como exames distintos.
    """
    exames = [
        ExameEmitido(
            exame="hemograma",
            periodicidade_meses=12,
            momentos={Momento.ADM},
            motivos=[Motivo(regra_id="R1", predicado="p1", risco_origem=None, detalhe=None)],
        ),
        ExameEmitido(
            exame="hemograma",
            periodicidade_meses=12,
            momentos={Momento.PER},
            motivos=[Motivo(regra_id="R2", predicado="p2", risco_origem=None, detalhe=None)],
        ),
    ]
    result = stage_8_consolidacao(exames)
    assert len(result) == 1
    assert result[0].momentos == {Momento.ADM, Momento.PER}
    assert len(result[0].motivos) == 2


def test_dedup_slugs_diferentes_nao_mergem() -> None:
    """
    Slugs diferentes (ex: 'hemograma' vs 'hemograma_completo') são exames
    distintos no vocabulário e não devem ser deduplicados, mesmo que
    humanamente pareçam o mesmo.
    """
    exames = [
        ExameEmitido(
            exame="hemograma",
            periodicidade_meses=12,
            momentos={Momento.ADM},
            motivos=[Motivo(regra_id="R1", predicado="p1", risco_origem=None, detalhe=None)],
        ),
        ExameEmitido(
            exame="hemograma_completo",
            periodicidade_meses=12,
            momentos={Momento.ADM},
            motivos=[Motivo(regra_id="R2", predicado="p2", risco_origem=None, detalhe=None)],
        ),
    ]
    result = stage_8_consolidacao(exames)
    assert len(result) == 2


def test_piso_periodicidade_base_convergente() -> None:
    """
    D-ARQ-39: periodicidade divergente no mesmo exame não é mais
    ConflitoProtocolo — resolve por piso (mínimo). 24M x 60M -> 24M.
    """
    entrada = [
        _exame("Raio-X torax", 24, {Momento.ADM}, "R-A"),
        _exame("Raio-X torax", 60, {Momento.PER}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].periodicidade_meses == 24


def test_piso_periodicidade_apos_15a_none_como_infinito() -> None:
    """
    Caso-âncora D-ARQ-39 cláusula 4: R-RX-01-sem (24, 12) x R-RX-02 (60, None)
    -> piso (24, 12). None em apenas um lado não derruba o piso do outro lado.
    """
    entrada = [
        _exame("Raio-X torax", 24, {Momento.ADM}, "R-RX-01-sem", apos_15a=12),
        _exame("Raio-X torax", 60, {Momento.PER}, "R-RX-02", apos_15a=None),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].periodicidade_meses == 24
    assert result[0].periodicidade_apos_15a == 12


def test_piso_apos_15a_ambos_none_permanece_none() -> None:
    """Ambos os lados com apos_15a=None -> resultado None, não 0, não erro."""
    entrada = [
        _exame("Hemograma", 24, {Momento.ADM}, "R-A", apos_15a=None),
        _exame("Hemograma", 60, {Momento.PER}, "R-B", apos_15a=None),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].periodicidade_apos_15a is None


def test_piso_preserva_pendencias_anexadas_dos_dois_lados() -> None:
    """
    Requisito piso-sem-teto de D-ARQ-31: pendência bloqueante anexada a
    qualquer um dos lados nunca é perdida no caminho de piso.
    """
    pend_a = Pendencia(tipo="teto", destinatario="RT", motivo="a", bloqueante=True)
    pend_b = Pendencia(tipo="teto", destinatario="RT", motivo="b", bloqueante=True)
    entrada = [
        _exame("Raio-X torax", 24, {Momento.ADM}, "R-A", pendencias=[pend_a]),
        _exame("Raio-X torax", 60, {Momento.PER}, "R-B", pendencias=[pend_b]),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert result[0].pendencias_anexadas == [pend_a, pend_b]


def test_piso_preserva_motivos_dos_dois_lados() -> None:
    """Proveniência (motivos) dos dois lados preservada no caminho de piso."""
    entrada = [
        _exame("Raio-X torax", 24, {Momento.ADM}, "R-A"),
        _exame("Raio-X torax", 60, {Momento.PER}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 1
    assert [m.regra_id for m in result[0].motivos] == ["R-A", "R-B"]


def test_exames_distintos_preservados() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}),
        _exame("Glicemia",  12, {Momento.ADM}),
        _exame("ECG",       12, {Momento.ADM}),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 3
    assert [e.exame for e in result] == ["Hemograma", "Glicemia", "ECG"]


def test_ordem_primeira_ocorrencia_preservada() -> None:
    entrada = [
        _exame("Hemograma", 12, {Momento.ADM}, "R-A"),
        _exame("Glicemia",  12, {Momento.ADM}, "R-A"),
        _exame("Hemograma", 12, {Momento.PER}, "R-B"),
    ]
    result = stage_8_consolidacao(entrada)
    assert len(result) == 2
    assert result[0].exame == "Hemograma"
    assert result[1].exame == "Glicemia"


def test_funcao_pura_nao_muta_entrada() -> None:
    e1 = _exame("Hemograma", 12, {Momento.ADM}, "R-A")
    e2 = _exame("Hemograma", 12, {Momento.PER}, "R-B")
    momentos_antes = set(e1.momentos)
    motivos_antes = list(e1.motivos)
    entrada = [e1, e2]

    stage_8_consolidacao(entrada)

    assert len(entrada) == 2
    assert entrada[0] is e1
    assert entrada[1] is e2
    assert e1.momentos == momentos_antes
    assert e1.motivos == motivos_antes
