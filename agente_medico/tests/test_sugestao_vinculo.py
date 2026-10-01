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
from agente_medico.superficie.sugestao_vinculo import (
    AVISO_SEM_CASAMENTO,
    AVISO_SEM_COMPONENTE_RECONHECIDO,
    AVISO_SEM_INGREDIENTE_DECLARADO,
    sugerir_ghes,
)
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
_BENZENO = ("71-43-2", "Benzeno")
# CAS válido fora do vocabulário (querosene da FISPQ de aguarrás do acervo; a nafta
# da mesma FISPQ passou a ser aguarras_mineral, DT-(sessão claude/keen-curie-xdm7kb)-01).
_QUEROSENE = ("8008-20-6", "Querosene")


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

    sugestao = sugerir_ghes(_fds(_QUEROSENE, ("", "Segredo industrial")), pgr, _AGENTES)

    assert sugestao.ghes == ()
    assert sugestao.componentes_sem_slug == (
        "8008-20-6 | Querosene",
        "— | Segredo industrial",
    )


def _pagina(
    monkeypatch: pytest.MonkeyPatch,
    nome_fds: str | tuple[str, ...],
    blocos: tuple[BlocoVerbatim, ...],
    pendencias_fds: tuple[Pendencia, ...] = (),
) -> AppTest:
    """PGR de 3 GHEs processado de verdade e FDS enviadas, sem anexo."""
    pgr = _pgr(
        _ghe("GHE-02", "Almoxarifado", "tolueno", cargos=("Almoxarife",)),
        _ghe("GHE-18", "Pintura", "tolueno", "xileno", cargos=("Pintor",)),
        _ghe("GHE-22", "Impermeabilização", "asfalto", cargos=("Impermeabilizador",)),
    )

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_composicao", lambda *a, **k: (blocos, pendencias_fds)
    )
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    nomes = (nome_fds,) if isinstance(nome_fds, str) else nome_fds
    at.file_uploader[1].set_value([(n, n.encode(), "application/pdf") for n in nomes]).run()
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
    # marcar — o produto entraria no GHE e a matriz mudaria; (4) marcar todos
    # os sugeridos em vez do topo — o GHE-02, com só tolueno, entraria junto.
    at = _pagina(monkeypatch, "fds.pdf", _fds(_TOLUENO, _XILENO))
    matrizes_antes = at.session_state["web_matriz_cache"].matrizes
    assert at.multiselect(key="ghe_destino_fds.pdf").value == []

    at.button(key="marcar_sugeridos_fds.pdf").click().run()
    assert not at.exception

    assert at.multiselect(key="ghe_destino_fds.pdf").value == ["GHE-18"]
    cache = at.session_state["web_matriz_cache"]
    assert all(g.produtos_quimicos == () for g in cache.pgr_hidratado.ghes)
    assert cache.matrizes == matrizes_antes


def test_empate_no_topo_marca_os_empatados(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: marcar só o 1º da lista (ghes[0]) — no empate a ordem
    # do PGR decidiria sozinha e o GHE-18, empatado com o GHE-02, ficaria fora.
    at = _pagina(monkeypatch, "fds.pdf", _fds(_TOLUENO))

    at.button(key="marcar_sugeridos_fds.pdf").click().run()

    assert at.multiselect(key="ghe_destino_fds.pdf").value == ["GHE-02", "GHE-18"]


def test_fds_sem_agente_do_pgr_ganha_aviso_e_continua_anexavel(monkeypatch: pytest.MonkeyPatch) -> None:
    # Caso Aurora (aguarrás): o único componente reconhecido é o benzeno, que
    # nenhum GHE declara. Reversões que matam: (1) tirar o st.warning do ramo
    # sem casamento; (2) tratar a divergência como bloqueio, escondendo o
    # botão Anexar (cl.4: não bloqueia).
    at = _pagina(monkeypatch, "fds.pdf", _fds(_QUEROSENE, _BENZENO))

    assert [w.value for w in at.warning] == [AVISO_SEM_CASAMENTO]
    assert at.button(key="anexar_fds_fds.pdf") is not None
    assert _linhas_de_ghe(at) == []


def test_fds_sem_componente_reconhecido_culpa_o_vocabulario(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: um aviso só para os dois casos — a FDS só de nafta
    # (CAS fora do vocabulário) mandaria o RT conferir o PGR, que não tem culpa.
    at = _pagina(monkeypatch, "fds.pdf", _fds(_QUEROSENE))

    assert [w.value for w in at.warning] == [AVISO_SEM_COMPONENTE_RECONHECIDO]
    assert at.button(key="anexar_fds_fds.pdf") is not None


def test_vocabulario_carregado_uma_vez_por_renderizacao(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: chamar _protocolo_padrao() dentro do laço das FDS —
    # com 3 FDS a página carregaria o protocolo 2 vezes a mais que com 1
    # (~160 ms cada, medido em 30/09/2026).
    import agente_medico.superficie.web_matriz as web_matriz

    original = web_matriz._protocolo_padrao
    chamadas: list[int] = []

    def _contado() -> Any:
        chamadas.append(1)
        return original()

    def _cargas_no_rerun(nomes: tuple[str, ...]) -> int:
        at = _pagina(monkeypatch, nomes, _fds(_TOLUENO))
        monkeypatch.setattr(web_matriz, "_protocolo_padrao", _contado)
        chamadas.clear()
        at.run()
        monkeypatch.setattr(web_matriz, "_protocolo_padrao", original)
        return len(chamadas)

    assert _cargas_no_rerun(("a.pdf", "b.pdf", "c.pdf")) == _cargas_no_rerun(("a.pdf",))


# DT-(sessão claude/keen-curie-xdm7kb)-02: FDS CARPINTEIRO (Desmoldante Quartzolit), seção 3
# "Não apresenta ingredientes ou impurezas que contribuam para o perigo".


def test_fds_sem_ingrediente_declarado_ganha_aviso_proprio_e_seletor(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversões que matam: (1) voltar a exigir composição não vazia para abrir o
    # vínculo (`and blocos_fds`) — nem aviso nem seletor aparecem; (2) mandar a
    # composição vazia para sugerir_ghes — sai o aviso de lacuna de vocabulário,
    # que culpa o vocabulário por uma FDS que não declarou nada.
    at = _pagina(monkeypatch, "FDS CARPINTEIRO.pdf", ())

    assert [w.value for w in at.warning] == [AVISO_SEM_INGREDIENTE_DECLARADO]
    assert at.multiselect(key="ghe_destino_FDS CARPINTEIRO.pdf").value == []
    assert at.button(key="anexar_fds_FDS CARPINTEIRO.pdf") is not None
    assert _linhas_de_ghe(at) == []


def test_fds_sem_ingrediente_declarado_anexa_no_ghe_escolhido(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: guarda em _anexar que descarta composição vazia
    # (`if not blocos: return`) — o seletor aparece e o clique não anexa nada.
    at = _pagina(monkeypatch, "FDS CARPINTEIRO.pdf", ())

    at.multiselect(key="ghe_destino_FDS CARPINTEIRO.pdf").set_value(["GHE-02"]).run()
    at.button(key="anexar_fds_FDS CARPINTEIRO.pdf").click().run()
    assert not at.exception

    ghes = {g.id: g for g in at.session_state["web_matriz_cache"].pgr_hidratado.ghes}
    assert [p.nome for p in ghes["GHE-02"].produtos_quimicos] == ["FDS CARPINTEIRO"]
    assert ghes["GHE-18"].produtos_quimicos == ()


def test_composicao_vazia_com_pendencia_nao_vira_fds_sem_ingrediente(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: decidir "sem ingrediente" só por `not blocos_fds` — a FDS
    # cuja seção 3 não foi achada ganharia o aviso e o seletor, e o RT anexaria
    # como "sem ingrediente perigoso" uma FDS que o sistema não leu.
    ausente = Pendencia(
        tipo="composicao_ausente_fds",
        destinatario="extracao",
        motivo="Região de composição não localizada",
        bloqueante=True,
        regra_origem="D-ARQ-47",
    )
    at = _pagina(monkeypatch, "fds.pdf", (), (ausente,))

    assert AVISO_SEM_INGREDIENTE_DECLARADO not in [w.value for w in at.warning]
    assert not at.multiselect


def test_fds_sem_ingrediente_antes_de_gerar_a_matriz_diz_como_vincular(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: deixar o st.info do ramo sem PGR processado condicionado
    # a `blocos_fds` — antes de gerar, a FDS sem ingrediente volta a não mostrar nada.
    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_composicao", lambda *a, **k: ((), ()))
    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    at.file_uploader[1].set_value([("FDS CARPINTEIRO.pdf", b"x", "application/pdf")]).run()
    assert not at.exception

    assert "Gere a matriz para vincular esta FDS a um GHE." in [i.value for i in at.info]
