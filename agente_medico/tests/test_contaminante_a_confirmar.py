"""R-FDS-07: aguarrás declarada no PGR sem a FDS dela no GHE → pendência ao elaborador
para confirmar o benzeno, sem emitir o pacote do benzeno (R-PKG-BZ só com o agente
identificado; NR-07 Anexo V 2.1 e NR-15 Anexo 13-A item 2). Caso: Aurora 27.08.26,
GHE 18 PINTURA, rodado sem a FISPQ da aguarrás em 01/10/2026. Cada teste nomeia a
reversão que o deixa vermelho."""

from __future__ import annotations

import dataclasses
from datetime import date
from pathlib import Path

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import (
    PGR,
    BlocoVerbatim,
    GHEVerbatim,
    MatrizGHE,
    MembroVerbatim,
    Pendencia,
    ProdutoQuimico,
    RiscoVerbatim,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    montar_memorial,
    renderizar_memorial_docx,
    resumos_do_protocolo,
)
from agente_medico.superficie.web_matriz import pagina_matriz
from agente_medico.tests.test_web_matriz import _submeter_formulario

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 10, 2)
_AGUARRAS = "Aguarrás"
_DESTILADOS = "Destilados de Petróleo levemente tratados com hidrogênio"

# Seção 3 da FISPQ fispq-quim-sol-alif-aguarras-mineral.pdf, como declarada.
_FISPQ_AGUARRAS = (
    BlocoVerbatim("0 - 100", (MembroVerbatim("64742-82-1", "Nafta hidrodessulfurizada pesada"),)),
    BlocoVerbatim("0 - 100", (MembroVerbatim("8008-20-6", "Querosene"),)),
    BlocoVerbatim("<0,1", (MembroVerbatim("71-43-2", "Benzeno"),)),
)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _hidratar(proto: Protocolo, *ghes: tuple[str, tuple[str, ...]]) -> tuple[PGR, list[Pendencia]]:
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    return hidratar_pgr(
        [
            GHEVerbatim(
                nome=nome,
                cargos=("Pintor",),
                riscos=tuple(
                    RiscoVerbatim(
                        agente=t, quantificacao="", fonte_geradora="Atividade com pintura",
                        avaliacao_qualitativa="3 1 BAIXO (3)",
                    )
                    for t in termos
                ),
            )
            for nome, termos in ghes
        ],
        indice,
        date(2030, 1, 1),
        True,
    )


def _com_produtos(pgr: PGR, *blocos_por_produto: tuple[str, tuple[BlocoVerbatim, ...]]) -> PGR:
    produtos = tuple(ProdutoQuimico(nome=nome, fds=montar_fds(blocos)) for nome, blocos in blocos_por_produto)
    ghe = dataclasses.replace(pgr.ghes[0], produtos_quimicos=produtos)
    return dataclasses.replace(pgr, ghes=(ghe, *pgr.ghes[1:]))


def _matrizes(proto: Protocolo, pgr: PGR) -> list[MatrizGHE]:
    return processar_pgr(pgr, proto, hoje=_HOJE).matrizes


def _a_confirmar(matriz: MatrizGHE) -> list[Pendencia]:
    return [p for p in matriz.pendencias if p.regra_origem == "R-FDS-07"]


def test_aguarras_sem_fds_pede_a_fds_e_nao_emite_o_pacote(proto: Protocolo) -> None:
    # Reversões que matam: (1) tirar `contaminantes_a_confirmar` da aguarras_mineral em
    # agentes.yaml; (2) tirar a chamada de _contaminantes_a_confirmar do stage 3;
    # (3) pendência bloqueante — derruba a matriz de VÁLIDA; (4) disparar para todo
    # agente sem olhar o vocabulário — o GHE de ruído ganha pendência.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)), ("GHE 01 - ADM", ("Ruído",)))
    pintura, adm = _matrizes(proto, pgr)

    (pendencia,) = _a_confirmar(pintura)
    assert pendencia.tipo == "contaminante_a_confirmar"
    assert not pendencia.bloqueante
    assert "Aguarrás" in pendencia.motivo and "benzeno" in pendencia.motivo
    assert pintura.status == "VÁLIDA"
    assert not {"acido_transmuconico", "reticulocitos"} & {e.exame for e in pintura.linhas}
    assert _a_confirmar(adm) == []


def test_fispq_com_benzeno_emite_o_pacote_sem_pendencia(proto: Protocolo) -> None:
    # Com a FISPQ do acervo anexada o pacote sai (R-PKG-BZ) e a pendência some.
    # Reversão que mata: ignorar as FDS anexadas e os riscos presentes (disparar
    # só pelo PGR) — a pendência continua depois de a FDS responder.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Aguarrás mineral", _FISPQ_AGUARRAS)))

    assert _a_confirmar(pintura) == []
    assert {"acido_transmuconico", "reticulocitos"} <= {e.exame for e in pintura.linhas}


def test_fds_da_aguarras_sem_benzeno_encerra_a_pendencia(proto: Protocolo) -> None:
    # Aguarrás desaromatizada: a FDS dela foi anexada e não declara benzeno.
    # Reversão que mata: tirar o `if risco.agente in com_fds: continue`.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    fds_sem_benzeno = (_FISPQ_AGUARRAS[0],)
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Aguarrás mineral", fds_sem_benzeno)))

    assert _a_confirmar(pintura) == []


def test_benzeno_de_outra_fds_encerra_a_pendencia(proto: Protocolo) -> None:
    # O benzeno já está no GHE por outro produto; o pacote sai e não há o que confirmar.
    # Reversão que mata: tirar o `contaminante in presentes` do filtro.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    thinner = (BlocoVerbatim("<0,1", (MembroVerbatim("71-43-2", "Benzeno"),)),)
    (pintura,) = _matrizes(proto, _com_produtos(pgr, ("Thinner", thinner)))

    assert _a_confirmar(pintura) == []
    assert "acido_transmuconico" in {e.exame for e in pintura.linhas}


def test_dois_termos_da_aguarras_geram_uma_pendencia(proto: Protocolo) -> None:
    # O Aurora declara "Aguarrás" e "Destilados de petróleo…" — mesmo slug.
    # Reversão que mata: tirar o conjunto `vistos` — saem duas pendências iguais.
    pgr, _ = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS, _DESTILADOS)))
    (pintura,) = _matrizes(proto, pgr)

    assert len(_a_confirmar(pintura)) == 1


def test_memorial_lista_a_fds_a_pedir_no_resumo_e_no_ghe(proto: Protocolo, tmp_path: Path) -> None:
    # Reversões que matam: (1) montar_memorial não preencher `a_confirmar`; (2) não
    # renderizar a lista no bloco do GHE; (3) tirar a linha do Resumo.
    from docx import Document

    pgr, pendencias = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)), ("GHE 01 - ADM", ("Ruído",)))
    memorial = montar_memorial(
        _matrizes(proto, pgr),
        proto.vocabulario.exames,
        resumos_do_protocolo(proto.regras),
        pgr=pgr,
        pendencias=pendencias,
    )
    pintura, adm = memorial.blocos
    assert len(pintura.a_confirmar) == 1 and pintura.a_confirmar[0].endswith("(ref. R-FDS-07)")
    assert adm.a_confirmar == ()

    destino = tmp_path / "memorial.docx"
    cab = CabecalhoDocumento("CMO", "Aurora", "Adendo", "2026-08-27", "Dra. X", "CRM")
    renderizar_memorial_docx(memorial, cab, destino)
    paragrafos = [p.text for p in Document(str(destino)).paragraphs]
    assert pintura.a_confirmar[0] in paragrafos
    assert any(
        p.startswith("FDS a pedir ao elaborador do PGR para confirmar contaminante:") and pintura.ghe_id in p
        for p in paragrafos
    )


def test_tela_mostra_a_fds_a_pedir_na_conferencia(monkeypatch: pytest.MonkeyPatch, proto: Protocolo) -> None:
    # A pendência é do GHE (MatrizGHE.pendencias), que a tela não listava.
    # Reversão que mata: tirar o bloco `if a_confirmar:` da conferência.
    pgr, pendencias = _hidratar(proto, ("GHE 18 - PINTURA", (_AGUARRAS,)))
    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_pgr_hidratado", lambda *a, **k: (pgr, tuple(pendencias))
    )
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    assert not at.exception

    textos = [el.value for el in at.markdown]
    assert "**FDS a pedir ao elaborador do PGR (contaminante a confirmar)**" in textos
    assert any("R-FDS-07" in t and "benzeno" in t for t in textos)
