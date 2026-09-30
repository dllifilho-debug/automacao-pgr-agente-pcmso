"""D-ARQ-90 fatia 1 — sugestão de vínculo FDS↔GHE por agente em comum. Cada
teste carrega, junto, a reversão de código que deve deixá-lo vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    BlocoVerbatim,
    MembroVerbatim,
    Pendencia,
    RiscoPGR,
)
from agente_medico.superficie.sugestao_vinculo import AVISO_SEM_CASAMENTO, sugerir_ghes
from agente_medico.superficie.web_matriz import pagina_matriz
from agente_medico.tests.test_web_matriz import _submeter_formulario

_AGENTES = carregar(Path(__file__).parent.parent / "protocolo").vocabulario.agentes


def _ghe(ghe_id: str, nome: str, *agentes: str | None, cargos: tuple[str, ...] = ()) -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome=nome,
        cargos=cargos,
        riscos=tuple(RiscoPGR(tipo="quimico", agente=a, quantificacao=None, severidade=None) for a in agentes),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _pgr(*ghes: GHEPGR) -> PGR:
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=ghes)


def _fds(*membros: tuple[str, str]) -> tuple[BlocoVerbatim, ...]:
    return (BlocoVerbatim(faixa="1-10%", membros=tuple(MembroVerbatim(cas=c, nome=n) for c, n in membros)),)


_TOLUENO = ("108-88-3", "Tolueno")
_XILENO = ("1330-20-7", "Xileno")
_ASFALTO = ("8052-42-4", "Asfalto")
# CAS válido fora do vocabulário (nafta da FISPQ de aguarrás do acervo).
_NAFTA = ("64742-82-1", "Nafta hidrodessulfurizada pesada")


def test_ghe_com_mais_agentes_em_comum_vem_primeiro() -> None:
    # Reversão que mata: tirar o sort por número de agentes — o GHE-02, 1º na
    # ordem do PGR com 1 agente, ficaria à frente do GHE-11 com 2.
    pgr = _pgr(_ghe("GHE-02", "Almoxarifado", "tolueno"), _ghe("GHE-11", "Hidro", "tolueno", "xileno"))

    sugestao = sugerir_ghes(_fds(_TOLUENO, _XILENO), pgr, _AGENTES)

    assert [(g.ghe_id, [a.slug for a in g.agentes]) for g in sugestao.ghes] == [
        ("GHE-11", ["tolueno", "xileno"]),
        ("GHE-02", ["tolueno"]),
    ]


def test_ghe_com_um_so_agente_em_comum_nao_some() -> None:
    # Reversão que mata: corte por limiar (ex. `if len(em_comum) >= 2`) — o
    # GHE-02, com 1 agente em comum, sumiria da sugestão (cl.2: sem limiar).
    pgr = _pgr(_ghe("GHE-02", "Almoxarifado", "tolueno"), _ghe("GHE-11", "Hidro", "tolueno", "xileno"))

    sugestao = sugerir_ghes(_fds(_TOLUENO, _XILENO), pgr, _AGENTES)

    assert "GHE-02" in [g.ghe_id for g in sugestao.ghes]


def test_componente_sem_slug_nao_conta_mas_aparece() -> None:
    # Reversão que mata: descartar o membro sem slug em vez de listá-lo — a
    # contagem "N componentes sem correspondência" (cl.1) sairia vazia e a FDS
    # só de nafta pareceria sem composição.
    pgr = _pgr(_ghe("GHE-18", "Pintura", "xileno", None))

    sugestao = sugerir_ghes(_fds(_NAFTA, ("", "Segredo industrial")), pgr, _AGENTES)

    assert sugestao.sem_casamento
    assert sugestao.componentes_sem_slug == (
        "64742-82-1 | Nafta hidrodessulfurizada pesada",
        "— | Segredo industrial",
    )


def _pagina(monkeypatch: pytest.MonkeyPatch, nome_fds: str, blocos: tuple[BlocoVerbatim, ...]) -> AppTest:
    """PGR de 3 GHEs processado de verdade e uma FDS enviada, sem anexo."""
    pgr = _pgr(
        _ghe("GHE-02", "Almoxarifado", "tolueno", cargos=("Almoxarife",)),
        _ghe("GHE-18", "Pintura", "xileno", cargos=("Pintor",)),
        _ghe("GHE-22", "Impermeabilização", "asfalto", cargos=("Impermeabilizador",)),
    )

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_composicao", lambda *a, **k: (blocos, ())
    )
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    at.file_uploader[1].set_value([(nome_fds, b"conteudo qualquer", "application/pdf")]).run()
    assert not at.exception
    return at


def _linhas_de_ghe(at: AppTest) -> list[str]:
    return [m.value for m in at.markdown if m.value.startswith("- GHE-")]


def test_fds_pintor_sugere_impermeabilizacao_e_nao_pintura(monkeypatch: pytest.MonkeyPatch) -> None:
    # Caso Aurora: "FDS PINTOR" é impermeabilizante asfáltico. Reversão que
    # mata: sugerir pelo nome do arquivo ou pelo cargo (casar "PINTOR" com o
    # cargo Pintor do GHE-18) — a sugestão apontaria a Pintura.
    at = _pagina(monkeypatch, "FDS PINTOR.pdf", _fds(_ASFALTO))

    assert _linhas_de_ghe(at) == ["- GHE-22 — Impermeabilização — 1 em comum: Asfalto"]


def test_marcar_sugeridos_so_preenche_a_selecao(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões que matam: (1) pré-marcar o multiselect com os sugeridos — a
    # seleção não começaria vazia (cl.3); (2) botão sem efeito — a seleção
    # continuaria vazia depois do clique; (3) o botão anexar em vez de só
    # marcar — o produto entraria no GHE e a matriz mudaria.
    at = _pagina(monkeypatch, "fds.pdf", _fds(_TOLUENO, _XILENO))
    matrizes_antes = at.session_state["web_matriz_cache"].matrizes
    assert at.multiselect(key="ghe_destino_fds.pdf").value == []

    at.button(key="marcar_sugeridos_fds.pdf").click().run()
    assert not at.exception

    assert at.multiselect(key="ghe_destino_fds.pdf").value == ["GHE-02", "GHE-18"]
    cache = at.session_state["web_matriz_cache"]
    assert all(g.produtos_quimicos == () for g in cache.pgr_hidratado.ghes)
    assert cache.matrizes == matrizes_antes


def test_fds_sem_agente_do_pgr_ganha_aviso_e_continua_anexavel(monkeypatch: pytest.MonkeyPatch) -> None:
    # Caso Aurora: desmoldante sem o ácido oleico que o PGR declara. Reversões
    # que matam: (1) tirar o st.warning do ramo sem casamento; (2) tratar a
    # divergência como bloqueio, escondendo o botão Anexar (cl.4: não bloqueia).
    at = _pagina(monkeypatch, "fds.pdf", _fds(_NAFTA))

    assert AVISO_SEM_CASAMENTO in [w.value for w in at.warning]
    assert at.button(key="anexar_fds_fds.pdf") is not None
    assert _linhas_de_ghe(at) == []
