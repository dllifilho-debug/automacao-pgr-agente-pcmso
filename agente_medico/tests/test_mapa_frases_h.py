from __future__ import annotations

from datetime import date

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.materialidade import Materialidade, materialidade
from agente_medico.motor.resolvedor import EntradaIndice, mapear_frases_h
from agente_medico.motor.tipos import (
    FDS,
    GHEPGR,
    PGR,
    Componente,
    FaixaConcentracao,
    ProdutoQuimico,
)
from agente_medico.tests.fixtures import bloco_de


def _comp(frases_h: tuple[str, ...], is_sensibilizante: bool = False) -> Componente:
    return Componente(
        cas="71-43-2", nome="teste", frases_h=frases_h, is_sensibilizante=is_sensibilizante
    )


# ---------------------------------------------------------------------------
# mapear_frases_h — unit (a-g)
# ---------------------------------------------------------------------------


def test_h334_liga_sensibilizante() -> None:
    comp, pend = mapear_frases_h(_comp(("H334",)))
    assert comp.is_sensibilizante is True
    assert pend is None
    assert comp.frases_h == ("H334",)


def test_h317_liga_sensibilizante() -> None:
    comp, pend = mapear_frases_h(_comp(("H317",)))
    assert comp.is_sensibilizante is True
    assert pend is None


def test_h334_e_h317_juntas_ligam_sensibilizante_sem_pendencia() -> None:
    comp, pend = mapear_frases_h(_comp(("H334", "H317")))
    assert comp.is_sensibilizante is True
    assert pend is None


def test_h350_forma_valida_fora_do_mapa_preserva_cru_sem_flag_sem_pendencia() -> None:
    comp, pend = mapear_frases_h(_comp(("H350",)))
    assert comp.is_sensibilizante is False
    assert comp.frases_h == ("H350",)
    assert pend is None
    assert comp.is_carcinogeno_iarc is False


def test_tokens_malformados_geram_pendencia_nao_bloqueante_flag_false_cru_preservado() -> None:
    comp, pend = mapear_frases_h(_comp(("334", "HXXX", "h334")))
    assert comp.is_sensibilizante is False
    assert comp.frases_h == ("334", "HXXX", "h334")
    assert pend is not None
    assert pend.tipo == "frase_h_malformada"
    assert pend.bloqueante is False
    assert pend.destinatario == "empresa"
    assert pend.regra_origem == "D-ARQ-55"


def test_frases_h_vazio_sem_flag_sem_pendencia() -> None:
    comp, pend = mapear_frases_h(_comp(()))
    assert comp.is_sensibilizante is False
    assert pend is None


def test_flag_ja_true_permanece_true_com_frase_fora_do_mapa() -> None:
    comp, pend = mapear_frases_h(_comp(("H999",), is_sensibilizante=True))
    assert comp.is_sensibilizante is True
    assert pend is None


# ---------------------------------------------------------------------------
# resolver_composicao — travessia (h, i)
# ---------------------------------------------------------------------------


def _pgr_de(componentes: tuple[Componente, ...]) -> PGR:
    return PGR(
        validade=date(2025, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="ghe_teste",
                nome="GHE teste",
                cargos=(),
                riscos=(),
                epis=(),
                produtos_quimicos=(
                    ProdutoQuimico(
                        nome="Produto teste",
                        fds=FDS(
                            composicao=(),
                            composicao_verbatim=tuple(bloco_de(c) for c in componentes),
                        ),
                    ),
                ),
                psicossocial=False,
            ),
        ),
    )


def test_cas_in_vocab_com_h317_e_faixa_abaixo_de_5pct_e_material_via_bypass() -> None:
    idx = {"71432": EntradaIndice("benzeno", False)}
    comp = Componente(
        cas="71-43-2", nome="benzeno com sensibilizante",
        concentracao=FaixaConcentracao(1.0, 2.0), frases_h=("H317",),
    )
    pgr_resolvido, _pend = resolver_composicao(_pgr_de((comp,)), idx)
    resolvido = pgr_resolvido.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    (comp_out,) = resolvido.composicao
    assert comp_out.is_sensibilizante is True
    assert materialidade(comp_out) is Materialidade.MATERIAL


def test_cas_oculto_com_h334_h317_carrega_flag_mas_materialidade_ainda_ausente() -> None:
    comp = Componente(
        cas="", nome="segredo industrial", frases_h=("H334", "H317"),
    )
    pgr_resolvido, pend = resolver_composicao(_pgr_de((comp,)), {})
    resolvido = pgr_resolvido.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    (comp_out,) = resolvido.composicao
    # flag CARREGADA no componente (D-ARQ-55 P4) mesmo com CAS oculto
    assert comp_out.is_sensibilizante is True
    # pendência do gate_cas (ramo d, cas_ausente) preservada
    assert any(p.tipo == "cas_ausente" for p in pend)
    # saída ainda AUSENTE via ramo-0 (sem slug) — fronteira do passo 2, fora de escopo
    assert materialidade(comp_out) is Materialidade.AUSENTE
