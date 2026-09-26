"""test_integracao_composicao_fase_c.py — Sessão 003.X, fatia (i₀).

Teste de integração da cadeia determinística fds_t65 crua → resolver_composicao
→ stage_2_riscos Fase C.

Prova que o gate-CAS (4 ramos sobre CAS real) alimenta a 4ª fonte de risco
(D-ARQ-35) via composição resolvida, e TESTEMUNHA a degradação de procedência
que (i') / DH-003P-01 fechará.

NÃO toca executar(). NÃO toca produção. NÃO fecha DH-003P-01.
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    Componente, FDS, GHEPGR, PGR, ProdutoQuimico, GHEContext, Materialidade, Risco,
)
from agente_medico.tests.fixtures import bloco_de
from agente_medico.tests.fixtures.fds_t65 import (
    tinta_acrilica, cimento_ciplan, adesivo_pvc_tigre,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

_PROTO = carregar(_PROTOCOLO_DIR)
_INDICE = construir_indice_cas(_PROTO.vocabulario.agentes)


def _ghe_com_fds(ghe_id: str, componentes: tuple[Componente, ...]) -> GHEPGR:
    return GHEPGR(
        id=ghe_id, nome=ghe_id, cargos=(), riscos=(), epis=(),
        produtos_quimicos=(
            ProdutoQuimico(
                nome=ghe_id,
                fds=FDS(composicao=(), composicao_verbatim=tuple(bloco_de(c) for c in componentes)),
            ),
        ),
        psicossocial=False,
    )


def _pgr_cru() -> PGR:
    return PGR(
        validade=date(2025, 1, 1), assinatura_engenheiro=True,
        ghes=(
            _ghe_com_fds("adesivo", adesivo_pvc_tigre()),
            _ghe_com_fds("tinta", tinta_acrilica()),
            _ghe_com_fds("cimento", cimento_ciplan()),
        ),
    )


def _ctx_resolvido(ghe_id: str) -> GHEContext:
    pgr, _ = resolver_composicao(_pgr_cru(), _INDICE)
    ghe = next(g for g in pgr.ghes if g.id == ghe_id)
    ctx = GHEContext(pgr_ghe=ghe)
    stage_2_riscos(ctx, _PROTO)
    return ctx


def _quimicos(ctx: GHEContext) -> list[Risco]:
    return [r for r in ctx.riscos if r.fonte == "quimico_composicao"]


def test_resolver_composicao_resolve_slugs_do_vocabulario_real() -> None:
    pgr, _ = resolver_composicao(_pgr_cru(), _INDICE)
    adesivo = next(g for g in pgr.ghes if g.id == "adesivo")
    fds = adesivo.produtos_quimicos[0].fds
    assert fds is not None
    comp = {c.nome: c.agente for c in fds.composicao}

    assert comp["Acetona"] == "acetona"
    assert comp["Metiletilcetona (MEK)"] == "metil_etil_cetona"
    assert comp["Acetato de Etila"] == "acetato_de_etila"
    # CAS 9003-22-9 ganhou slug em DT-003M-02(A) (sessão `docs/003fg-...`) → ramo (a),
    # não mais ramo (b). Idem CAS 7128-64-5 (branqueador). Reversão que mata: reverter
    # a entrada `copolimero_de_pvc`/`branqueador_optico_fb184` de agentes.yaml.
    assert comp["Copolímero de PVC"] == "copolimero_de_pvc"
    assert comp["2,5-tiofenodiilbis(5-terc-butil-1,3-benzoxazole)"] == "branqueador_optico_fb184"
    # CAS oculto → ramo (d) → agente=None (nenhuma entrada de vocabulário resolve isso)
    assert comp["Segredo Industrial 1"] is None
    assert comp["Segredo Industrial 2"] is None


def test_adesivo_promove_cinco_riscos_quimicos() -> None:
    # 3 -> 5 em DT-003M-02(A) (sessão `docs/003fg-...`): copolímero de PVC e o
    # branqueador óptico ganharam slug e passam a promover também (Fase C não filtra
    # por materialidade, só por agente resolvido — MATERIAL e AUSENTE promovem igual,
    # ver test_adesivo_materialidade_por_componente). Reversão que mata: reverter as
    # 2 entradas novas de agentes.yaml usadas por este GHE.
    ctx = _ctx_resolvido("adesivo")
    q = _quimicos(ctx)

    assert len(q) == 5
    assert {r.agente for r in q} == {
        "acetona", "metil_etil_cetona", "acetato_de_etila",
        "copolimero_de_pvc", "branqueador_optico_fb184",
    }


def test_adesivo_materialidade_por_componente() -> None:
    ctx = _ctx_resolvido("adesivo")
    mat = {r.agente: r.materialidade for r in _quimicos(ctx)}

    assert mat["acetona"] == Materialidade.MATERIAL           # piso 30 > 5
    assert mat["metil_etil_cetona"] == Materialidade.MATERIAL  # piso 10 > 5
    assert mat["acetato_de_etila"] == Materialidade.AUSENTE    # straddle: piso 5 ≤ 5 < teto 30
    assert mat["copolimero_de_pvc"] == Materialidade.MATERIAL  # piso 15 > 5
    assert mat["branqueador_optico_fb184"] == Materialidade.AUSENTE  # straddle: piso 0 ≤ 5 < teto 10


def test_acetato_ausente_gera_pendencia_bloqueante() -> None:
    ctx = _ctx_resolvido("adesivo")
    p = [x for x in ctx.pendencias if x.tipo == "materialidade_ausente"
         and x.bloqueante and x.regra_origem == "D-ARQ-35"
         and "Acetato" in x.motivo]

    assert len(p) >= 1


def test_degradacao_procedencia_cas_invalido_vira_materialidade_ausente() -> None:
    # PROVA A DEGRADAÇÃO que (i')/DH-003P-01 fechará. NÃO usar asserção de ausência
    # de "cas_invalido" em ctx.pendencias — essa pendência NUNCA aparece no stage por
    # construção (nasce e morre dentro de resolver_composicao), seria tautologia cega.
    # A prova real é a FUSÃO de procedências: ramo-c (TiO2 CAS inválido) e ramo-b
    # (copolimero CAS válido sem slug) chegam à Fase C indistinguíveis. Pós D-ARQ-56/
    # R-FDS-06 (passo 2): nenhum dos dois tem frase-H TRANSCRITA na fixture (tinta:
    # frases-R europeias fora de escopo, medição PENDENTE — 003.CJ decisão 6) -> caem
    # no mesmo ramo (b) inerte-declarado, não-bloqueante — a fusão passou a ocorrer
    # sob R-FDS-06 em vez de D-ARQ-35.
    ctx_tinta = _ctx_resolvido("tinta")
    ctx_adesivo = _ctx_resolvido("adesivo")

    # TiO2 (ramo c) não promove: nenhum risco quimico com agente dioxido_de_titanio
    assert not any(r.agente == "dioxido_de_titanio" for r in _quimicos(ctx_tinta))

    # A pendência que o TiO2 (ramo c, ORIGEM cas_invalido/D-ARQ-36) gera na Fase C é
    # materialidade_ausente/R-FDS-06 — a procedência cas_invalido foi PERDIDA no descarte.
    pend_tio2 = [p for p in ctx_tinta.pendencias
                 if p.tipo == "materialidade_ausente" and p.regra_origem == "R-FDS-06"]
    assert pend_tio2
    assert all(not p.bloqueante for p in pend_tio2)

    # O copolimero PVC (ramo b, ORIGEM vocabulario_ausente/D-ARQ-36) gera na Fase C uma
    # pendência do MESMO tipo e MESMA regra_origem — procedências distintas (b vs c)
    # ACHATADAS no mesmo tipo após o descarte. Esta é a degradação observável.
    pend_copol = [p for p in ctx_adesivo.pendencias
                  if p.tipo == "materialidade_ausente" and p.regra_origem == "R-FDS-06"]
    assert pend_copol
    assert all(not p.bloqueante for p in pend_copol)

    # DH-003P-01 — quando resolver_composicao propagar a Pendencia do gate ao Resultado,
    # ramo-c e ramo-b deixarão de ser indistinguíveis.
    # (i') é a fatia seguinte; este teste muda de asserção lá.


def test_adesivo_segredo_industrial_2_bypass_sem_slug_bloqueante() -> None:
    # Segredo Industrial 2 (CAS oculto, ramo d) declara H334+H317 na FDS —
    # mapear_frases_h liga is_sensibilizante=True mesmo sem slug. D-ARQ-56: o
    # bypass é honrado e gera pendência bloqueante distinta (bypass_sem_slug),
    # em vez de ser mascarado pelo ramo-0 (fronteira fechada no passo 2).
    ctx = _ctx_resolvido("adesivo")
    pend = [p for p in ctx.pendencias
            if p.tipo == "bypass_sem_slug" and "Segredo Industrial 2" in p.motivo]
    assert len(pend) == 1
    assert pend[0].bloqueante is True
    assert pend[0].regra_origem == "D-ARQ-56"


def test_cimento_seis_componentes_promovem_pos_dt003m02a() -> None:
    # Antes de DT-003M-02(A) (sessão `docs/003fg-...`): nenhum dos 8 componentes do
    # cimento tinha slug (ramo b/c/d, nenhum a) — este teste se chamava
    # test_cimento_nenhum_componente_promove e afirmava `_quimicos(ctx) == []`.
    # A expansão do vocabulário deu slug a 6 dos 8 (só aluminato tricálcico, CAS
    # malformado na FDS/ramo c, e sulfato de cálcio, CAS oculto/ramo d, seguem sem).
    # Reversão que mata: reverter as 6 entradas novas de agentes.yaml usadas por
    # este GHE (silicato_tricalcico, silicato_dicalcico, ferro_aluminato_de_calcio,
    # carbonato_de_calcio, oxido_de_magnesio, oxido_de_calcio).
    ctx = _ctx_resolvido("cimento")
    mat = {r.agente: r.materialidade for r in _quimicos(ctx)}
    assert set(mat) == {
        "silicato_tricalcico", "silicato_dicalcico", "ferro_aluminato_de_calcio",
        "carbonato_de_calcio", "oxido_de_magnesio", "oxido_de_calcio",
    }
    assert mat["silicato_tricalcico"] == Materialidade.MATERIAL       # piso 20 > 5
    assert mat["silicato_dicalcico"] == Materialidade.MATERIAL        # piso 10 > 5
    assert mat["ferro_aluminato_de_calcio"] == Materialidade.AUSENTE  # straddle: piso 5 ≤5< teto 15
    assert mat["carbonato_de_calcio"] == Materialidade.NAO_MATERIAL   # teto 5 ≤ 5
    assert mat["oxido_de_magnesio"] == Materialidade.NAO_MATERIAL     # teto 4 < 5
    assert mat["oxido_de_calcio"] == Materialidade.NAO_MATERIAL       # teto 0,2 < 5

    # Aluminato tricálcico (CAS malformado na FDS, ramo c) e sulfato de cálcio (CAS
    # oculto, ramo d) seguem sem slug — nunca promovem (agente=None, Fase C pula) —,
    # mas geram pendência materialidade_ausente/R-FDS-06 não-bloqueante (inerte-
    # declarado, frases_h=() na fixture é MEDIÇÃO PENDENTE per 003.CJ decisão 6, não
    # afirmação de ausência na FDS real). O straddle do ferro-aluminato (AUSENTE, com
    # slug) gera a MESMA Pendencia tipo mas por D-ARQ-35 (bloqueante) — as duas
    # procedências coexistem, não se confundem por tipo sozinho.
    pend = [p for p in ctx.pendencias if p.tipo == "materialidade_ausente"]
    pend_rfds06 = [p for p in pend if p.regra_origem == "R-FDS-06"]
    pend_darq35 = [p for p in pend if p.regra_origem == "D-ARQ-35"]
    assert len(pend_rfds06) == 2
    assert all(not p.bloqueante for p in pend_rfds06)
    assert len(pend_darq35) == 1
    assert pend_darq35[0].bloqueante is True
