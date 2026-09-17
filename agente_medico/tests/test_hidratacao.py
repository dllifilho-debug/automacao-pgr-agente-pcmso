from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_ghe, hidratar_pgr
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import IndiceTermos, construir_indice_termos
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim
from agente_medico.tests.fixtures.pgr_viverde import build_pgr_viverde

PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def indice_real() -> IndiceTermos:
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(p.vocabulario.agentes)


@pytest.fixture(scope="module")
def indice_real_com_fracoes() -> IndiceTermos:
    # D-ARQ-82 cl.3 / D-ARQ-83: distinto de `indice_real` acima (que não passa
    # fracoes_sem_agente) porque T1 precisa da causa fracao_sem_agente real no
    # corpus — sem ela, "Poeira respirável" cairia em vocabulario_ausente.
    p = carregar(PROTOCOLO_DIR)
    return construir_indice_termos(
        p.vocabulario.agentes, fracoes_sem_agente=p.vocabulario.fracoes_sem_agente
    )


def _ghe_verbatim(*, riscos: tuple[RiscoVerbatim, ...]) -> GHEVerbatim:
    return GHEVerbatim(nome="Teste", cargos=("servente",), riscos=riscos)


# ---------------------------------------------------------------------------
# tri-estado do resolver
# ---------------------------------------------------------------------------

def test_exata_resolve_slug_sem_pendencia(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente == "ruido"
    assert pendencias == []


def test_fuzzy_resolve_slug_com_pendencia_nao_bloqueante(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Microrganismo", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente == "microrganismos"

    assert len(pendencias) == 1
    pend = pendencias[0]
    assert pend.tipo == "resolucao_fuzzy"
    assert pend.bloqueante is False
    assert pend.ghe_id == "GHE-01"


def test_nao_resolvido_agente_none_com_pendencia_e_risco_preservado(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Thinner", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    # anti-supressão: risco presente na saída mesmo sem slug resolvido.
    assert len(ghe_pgr.riscos) == 1
    assert ghe_pgr.riscos[0].agente is None

    assert len(pendencias) == 1
    pend = pendencias[0]
    assert pend.tipo == "vocabulario_ausente"
    assert pend.ghe_id == "GHE-01"


# ---------------------------------------------------------------------------
# parse de quantificacao (D-ARQ-51 fatia 2)
# ---------------------------------------------------------------------------

def test_quantificacao_parseavel_preenchida_sem_pendencia(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    quantificacao = ghe_pgr.riscos[0].quantificacao
    assert quantificacao is not None
    assert quantificacao.valor == 82.2
    assert quantificacao.unidade == "dB(A)"
    assert [p for p in pendencias if p.tipo == "quantificacao_nao_parseada"] == []


def test_quantificacao_ininteligivel_vira_none_com_pendencia_nao_bloqueante(
    indice_real: IndiceTermos,
) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="lixo qualquer", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert ghe_pgr.riscos[0].quantificacao is None

    pendencias_quantificacao = [p for p in pendencias if p.tipo == "quantificacao_nao_parseada"]
    assert len(pendencias_quantificacao) == 1
    pend = pendencias_quantificacao[0]
    assert pend.bloqueante is False
    assert pend.ghe_id == "GHE-01"


def test_quantificacao_vazia_vira_none_sem_pendencia(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=1)

    assert ghe_pgr.riscos[0].quantificacao is None
    assert [p for p in pendencias if p.tipo == "quantificacao_nao_parseada"] == []


# ---------------------------------------------------------------------------
# classificação dB(A) -> relacao_LT (D-ARQ-51 fatia 3, R-RUIDO-01)
# ---------------------------------------------------------------------------

def test_ruido_abaixo_acao_classifica_relacao_lt(indice_real: IndiceTermos) -> None:
    # âncora Viverde: 78,8 dB(A) < 80 -> abaixo_acao.
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="78,8 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    quantificacao = ghe_pgr.riscos[0].quantificacao
    assert quantificacao is not None
    assert quantificacao.relacao_LT == "abaixo_acao"


def test_ruido_acima_lt_classifica_relacao_lt(indice_real: IndiceTermos) -> None:
    # âncora Viverde: 89,6 dB(A) >= 85 -> acima_LT.
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="89,6 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    quantificacao = ghe_pgr.riscos[0].quantificacao
    assert quantificacao is not None
    assert quantificacao.relacao_LT == "acima_LT"


def test_risco_nao_ruido_com_dba_nao_classifica(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Thinner", quantificacao="89,6 dB(A)", fonte_geradora=""),)
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    quantificacao = ghe_pgr.riscos[0].quantificacao
    assert quantificacao is not None
    assert quantificacao.relacao_LT is None


def test_ruido_sem_quantificacao_nao_classifica(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora=""),)
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    assert ghe_pgr.riscos[0].quantificacao is None


# ---------------------------------------------------------------------------
# id posicional (D-ARQ-51 seam 1)
# ---------------------------------------------------------------------------

def test_id_posicional_formatado_e_deterministico(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(riscos=())

    ghe_pgr_a, _ = hidratar_ghe(ghe, indice_real, posicao=1)
    ghe_pgr_b, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    assert ghe_pgr_a.id == "GHE-01"
    assert ghe_pgr_a.id == ghe_pgr_b.id


# ---------------------------------------------------------------------------
# pareamento agente=None <-> pendência (D-ARQ-51 seam 3)
# ---------------------------------------------------------------------------

def test_todo_agente_none_tem_pendencia_correspondente(indice_real: IndiceTermos) -> None:
    ghe = _ghe_verbatim(
        riscos=(
            RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora=""),
            RiscoVerbatim(agente="Thinner", quantificacao="", fonte_geradora=""),
            RiscoVerbatim(agente="Eaquipamento desprotegido", quantificacao="", fonte_geradora=""),
        )
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real, posicao=3)

    riscos_none = [r for r in ghe_pgr.riscos if r.agente is None]
    pendencias_vocab_ausente = [p for p in pendencias if p.tipo == "vocabulario_ausente"]
    assert len(riscos_none) == len(pendencias_vocab_ausente) == 2
    assert all(p.ghe_id == "GHE-03" for p in pendencias_vocab_ausente)


# ---------------------------------------------------------------------------
# gabarito de forma (D-ARQ-50 C1) — compara forma, não contagem 42vs32
# ---------------------------------------------------------------------------

def test_gabarito_de_forma_ghepgr(indice_real: IndiceTermos) -> None:
    # D-ARQ-50 C1: molda o GHEVerbatim sintético num GHE real da fixture Viverde
    # (nome/cargos copiados de Est-01) — compara FORMA do GHEPGR produzido, não
    # contagem 42vs32 (o re-agrupamento MAPA é fatia downstream).
    ghe_real = build_pgr_viverde().ghes[0]
    ghe = GHEVerbatim(
        nome=ghe_real.nome,
        cargos=ghe_real.cargos,
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),),
    )
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1)

    # identidade preenchida
    assert isinstance(ghe_pgr.id, str) and ghe_pgr.id
    assert ghe_pgr.nome == ghe.nome
    assert ghe_pgr.cargos == ghe.cargos
    assert len(ghe_pgr.riscos) == len(ghe.riscos)
    assert all(r.tipo == "" for r in ghe_pgr.riscos)
    assert ghe_pgr.riscos[0].quantificacao is not None
    assert ghe_pgr.riscos[0].quantificacao.valor == 82.2
    assert ghe_pgr.riscos[0].quantificacao.unidade == "dB(A)"
    assert all(r.severidade is None for r in ghe_pgr.riscos)

    # epis/produtos_quimicos/cenario diferidos em default (D-ARQ-49 P2);
    # psicossocial (R-PSY-03) tem extrator, mas hidratar_ghe só repassa o
    # parâmetro — sem argumento aqui, fica no default False.
    assert ghe_pgr.epis == ()
    assert ghe_pgr.produtos_quimicos == ()
    assert ghe_pgr.psicossocial is False
    assert ghe_pgr.cenario is None


def test_hidratar_ghe_psicossocial_true_repassado_ao_ghe_pgr(indice_real: IndiceTermos) -> None:
    # R-PSY-03: hidratar_ghe repassa o parâmetro psicossocial ao GHEPGR em vez
    # do hardcoded False. Reversão que mata: voltar `psicossocial=psicossocial`
    # para `psicossocial=False` na construção do GHEPGR (hidratacao.py).
    ghe = _ghe_verbatim(riscos=())
    ghe_pgr, _ = hidratar_ghe(ghe, indice_real, posicao=1, psicossocial=True)
    assert ghe_pgr.psicossocial is True


# ---------------------------------------------------------------------------
# costura plural: hidratar_pgr (D-ARQ-51 seam 1, consumidor de hidratar_ghe)
# ---------------------------------------------------------------------------

def test_hidratar_pgr_ids_posicionais_ordem_preservada(indice_real: IndiceTermos) -> None:
    ghe_a = _ghe_verbatim(riscos=())
    ghe_b = _ghe_verbatim(riscos=())

    pgr, _ = hidratar_pgr(
        (ghe_a, ghe_b), indice_real, validade=date(2025, 1, 1), assinatura_engenheiro=True
    )

    assert [g.id for g in pgr.ghes] == ["GHE-01", "GHE-02"]
    assert pgr.ghes[0].nome == ghe_a.nome
    assert pgr.ghes[1].nome == ghe_b.nome


def test_hidratar_pgr_psicossocial_true_replicado_a_todos_os_ghe(
    indice_real: IndiceTermos,
) -> None:
    # R-PSY-03: psicossocial é sinal de PGR inteiro (D-ARQ-49 P2 aplicado) —
    # hidratar_pgr replica o mesmo valor para todo GHEPGR do documento.
    # Reversão que mata: não repassar `psicossocial` na chamada a
    # hidratar_ghe dentro do loop de hidratar_pgr (hidratacao.py).
    ghe_a = _ghe_verbatim(riscos=())
    ghe_b = _ghe_verbatim(riscos=())

    pgr, _ = hidratar_pgr(
        (ghe_a, ghe_b),
        indice_real,
        validade=date(2025, 1, 1),
        assinatura_engenheiro=True,
        psicossocial=True,
    )

    assert all(g.psicossocial is True for g in pgr.ghes)


def test_hidratar_pgr_agrega_pendencias_com_ghe_id_correto(indice_real: IndiceTermos) -> None:
    ghe_fuzzy = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Microrganismo", quantificacao="", fonte_geradora=""),)
    )
    ghe_nao_resolvido = _ghe_verbatim(
        riscos=(RiscoVerbatim(agente="Thinner", quantificacao="", fonte_geradora=""),)
    )

    pgr, pendencias = hidratar_pgr(
        (ghe_fuzzy, ghe_nao_resolvido),
        indice_real,
        validade=date(2025, 1, 1),
        assinatura_engenheiro=True,
    )

    assert len(pendencias) == 2
    assert pendencias[0].tipo == "resolucao_fuzzy"
    assert pendencias[0].ghe_id == "GHE-01"
    assert pendencias[1].tipo == "vocabulario_ausente"
    assert pendencias[1].ghe_id == "GHE-02"


def test_hidratar_pgr_repassa_envelope_verbatim(indice_real: IndiceTermos) -> None:
    validade = date(2026, 3, 15)

    pgr, _ = hidratar_pgr((), indice_real, validade=validade, assinatura_engenheiro=False)

    assert pgr.validade == validade
    assert pgr.assinatura_engenheiro is False


def test_hidratar_pgr_sequencia_vazia_legitima(indice_real: IndiceTermos) -> None:
    pgr, pendencias = hidratar_pgr(
        (), indice_real, validade=date(2025, 1, 1), assinatura_engenheiro=True
    )

    assert pgr.ghes == ()
    assert pendencias == []


def test_hidratar_pgr_e2e_sintetico_processar_pgr(indice_real: IndiceTermos) -> None:
    # D-ARQ-50 C1: GHEVerbatim moldado no Est-01 do Viverde (forma emprestada da
    # fixture); asserção de forma (matriz produzida), não de contagem.
    ghe_real = build_pgr_viverde().ghes[0]
    ghe = GHEVerbatim(
        nome=ghe_real.nome,
        cargos=ghe_real.cargos,
        riscos=(RiscoVerbatim(agente="Ruído", quantificacao="82,2 dB(A)", fonte_geradora=""),),
    )

    pgr, _ = hidratar_pgr(
        (ghe,), indice_real, validade=date(2025, 1, 1), assinatura_engenheiro=True
    )
    protocolo = carregar(PROTOCOLO_DIR)
    resultado = processar_pgr(pgr, protocolo, date(2025, 1, 1))

    assert resultado.matrizes[0].ghe_id == "GHE-01"
    assert len(resultado.matrizes) == 1


# ---------------------------------------------------------------------------
# D-ARQ-82 cl.3 — causa_nao_resolucao pareia 1:1 com o tipo da Pendencia do
# termo não resolvido, computado do índice real (não digitado).
# ---------------------------------------------------------------------------


def test_causa_nao_resolucao_pareia_com_tipo_da_pendencia_no_corpus_real(
    indice_real_com_fracoes: IndiceTermos,
) -> None:
    # T1 (003.FC): reversão que mata — em hidratacao.py, trocar
    # `causa_nao_resolucao=resolucao.pendencia.tipo` por um valor fixo (ex.:
    # "vocabulario_ausente") faz o Counter da esquerda parar de bater com o
    # da direita para as formas de fracoes_sem_agente (que esperam
    # "fracao_sem_agente") e para o termo-lixo (que espera
    # "vocabulario_ausente" mesmo, mas por coincidência só nesse caso —
    # trocar por "fracao_sem_agente" no lugar do fixo já denuncia a troca).
    #
    # Corpus computado do índice, nunca digitado: toda forma de
    # fracoes_sem_agente (espera causa fracao_sem_agente), toda forma de
    # slug_por_forma (resolve EXATA, agente is not None, causa None) e 1
    # termo-lixo fixo (espera vocabulario_ausente — não existe no índice
    # real nem tem vizinho fuzzy a distância <=2, checado abaixo).
    termo_lixo = "zzz_termo_garantidamente_ausente_do_vocabulario_zzz"
    assert termo_lixo not in indice_real_com_fracoes.slug_por_forma
    assert termo_lixo not in indice_real_com_fracoes.fracoes_sem_agente

    formas = (
        list(indice_real_com_fracoes.fracoes_sem_agente)
        + list(indice_real_com_fracoes.slug_por_forma.keys())
        + [termo_lixo]
    )
    ghe = _ghe_verbatim(
        riscos=tuple(
            RiscoVerbatim(agente=forma, quantificacao="", fonte_geradora="") for forma in formas
        )
    )
    ghe_pgr, pendencias = hidratar_ghe(ghe, indice_real_com_fracoes, posicao=1)

    causas_dos_riscos_nao_resolvidos = Counter(
        r.causa_nao_resolucao for r in ghe_pgr.riscos if r.agente is None
    )
    # ARMADILHA: filtro por tipo obrigatório — quantificacao_nao_parseada e
    # resolucao_fuzzy saem na mesma lista de pendências e não pareiam com
    # agente=None (um risco pode gerar 2 pendências: agente=None +
    # quantificação ilegível). Sem o filtro, o teste nasce vermelho pela
    # razão errada.
    tipos_das_pendencias_de_termo = Counter(
        p.tipo
        for p in pendencias
        if p.tipo in {"vocabulario_ausente", "fuzzy_recusado", "fracao_sem_agente"}
    )
    assert causas_dos_riscos_nao_resolvidos == tipos_das_pendencias_de_termo

    # confirma que o corpus de fato exercitou fracao_sem_agente e
    # vocabulario_ausente (corpus computado não é vazio nem degenerado).
    assert causas_dos_riscos_nao_resolvidos["fracao_sem_agente"] == len(
        indice_real_com_fracoes.fracoes_sem_agente
    )
    assert causas_dos_riscos_nao_resolvidos["vocabulario_ausente"] >= 1

    # invariante de pareamento 1:1 (D-ARQ-51 seam 3), sobre o mesmo corpus.
    riscos_none = [r for r in ghe_pgr.riscos if r.agente is None]
    assert len(riscos_none) == sum(tipos_das_pendencias_de_termo.values())

    # toda forma de slug_por_forma resolve EXATA: agente is not None, causa None.
    for risco in ghe_pgr.riscos:
        if risco.agente is not None:
            assert risco.causa_nao_resolucao is None
