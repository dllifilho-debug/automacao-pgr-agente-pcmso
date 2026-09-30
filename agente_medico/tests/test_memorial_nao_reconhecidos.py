"""T65 (auditoria de 30/09/2026 contra o gabarito RQ.61 de 24/09/26): o PNOS com
"outramaneira" no GHE 18 resolve por alias, e o memorial lista, por GHE, os
riscos do PGR que não viraram agente. Cada teste nomeia a reversão que o deixa
vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import PGR, GHEVerbatim, MatrizGHE, Pendencia, RiscoVerbatim
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    montar_memorial,
    renderizar_memorial_docx,
    resumos_do_protocolo,
)
from agente_medico.superficie.web_matriz import pagina_matriz
from agente_medico.tests.test_web_matriz import _submeter_formulario

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 30)

# Termos como o PGR TOCTAO ALT 65 (Rev. 01, 06/2026) os escreve.
_PNOS_OUTRAMANEIRA = "Particulados (insolúveis ou de baixa solubilidade) não especificados de outramaneira (PNOS)"
_GESSO = "Sulfato de cálcio — Gesso"


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
                cargos=("Servente",),
                riscos=tuple(
                    RiscoVerbatim(agente=t, quantificacao="", fonte_geradora="", avaliacao_qualitativa="2 1 BAIXO (2)")
                    for t in termos
                ),
            )
            for nome, termos in ghes
        ],
        indice,
        date(2030, 1, 1),
        True,
    )


def _matrizes(proto: Protocolo, pgr: PGR) -> list[MatrizGHE]:
    return processar_pgr(pgr, proto, hoje=_HOJE).matrizes


def test_pnos_com_outramaneira_gera_espirometria_e_rx_do_gabarito(proto: Protocolo) -> None:
    # GHE 18 COPA do T65: o gabarito pede Espirometria (PER 24) e RX OIT (PER 60).
    # Reversão que mata: tirar o alias "…outramaneira (PNOS)" de agentes.yaml —
    # o termo volta a sair como fuzzy_recusado e os dois exames somem.
    pgr, _ = _hidratar(proto, ("COPA", (_PNOS_OUTRAMANEIRA,)))
    (matriz,) = _matrizes(proto, pgr)

    periodicidade = {e.exame: e.periodicidade_meses for e in matriz.linhas}
    assert pgr.ghes[0].riscos[0].agente == "poeira_nao_classificada"
    assert (periodicidade.get("espirometria"), periodicidade.get("rx_torax_oit")) == (24, 60)


def test_memorial_lista_o_que_o_pgr_declara_e_nao_virou_agente(proto: Protocolo) -> None:
    # Reversões que matam: (1) montar_memorial ignorar `pgr` — a lista sai vazia;
    # (2) listar também os riscos resolvidos — a sílica apareceria; (3) texto
    # único para toda causa — a fração deixaria de pedir a FDS ao elaborador.
    pgr, pendencias = _hidratar(proto, ("GESSO", ("Sílica livre", _GESSO, "Poeira respirável")))
    memorial = montar_memorial(
        _matrizes(proto, pgr),
        proto.vocabulario.exames,
        resumos_do_protocolo(proto.regras),
        pgr=pgr,
        pendencias=pendencias,
    )

    (bloco,) = memorial.blocos
    assert bloco.nao_reconhecidos == (
        "Sulfato de cálcio — Gesso: sem correspondência no vocabulário de agentes.",
        "Poeira respirável: nomeia fração ou medida sem a substância; pedir a FDS ao "
        "elaborador do PGR (R-PGR-05).",
    )


def test_recusa_por_aproximacao_nomeia_o_agente_vizinho(proto: Protocolo) -> None:
    # Caso-âncora da D-ARQ-64: "Silício" fica a distância 2 de sílica e é recusado.
    # Reversão que mata: não cruzar com a pendência fuzzy_recusado do GHE — o
    # memorial diria só "grafia aproximada", sem nomear o agente a conferir.
    pgr, pendencias = _hidratar(proto, ("ARMAÇÃO", ("Silício",)))
    memorial = montar_memorial(
        _matrizes(proto, pgr),
        proto.vocabulario.exames,
        resumos_do_protocolo(proto.regras),
        pgr=pgr,
        pendencias=pendencias,
    )

    (bloco,) = memorial.blocos
    assert bloco.nao_reconhecidos == (
        "Silício: parece silica, mas grafia aproximada não é aceita para agente que dispara "
        "exame; conferir a grafia no PGR.",
    )


def test_docx_do_memorial_mostra_a_lista_no_resumo_e_no_ghe(proto: Protocolo, tmp_path: Path) -> None:
    # Reversões que matam: (1) não renderizar a lista no bloco do GHE; (2) tirar
    # a contagem do Resumo — a médica só veria a lacuna rolando GHE a GHE.
    from docx import Document

    pgr, pendencias = _hidratar(proto, ("GESSO", (_GESSO,)))
    memorial = montar_memorial(
        _matrizes(proto, pgr),
        proto.vocabulario.exames,
        resumos_do_protocolo(proto.regras),
        pgr=pgr,
        pendencias=pendencias,
    )
    destino = tmp_path / "memorial.docx"
    cab = CabecalhoDocumento("CMO", "T65", "Adendo", "2026-09-30", "Dra. X", "CRM")
    renderizar_memorial_docx(memorial, cab, destino)

    paragrafos = [p.text for p in Document(str(destino)).paragraphs]
    assert "Sulfato de cálcio — Gesso: sem correspondência no vocabulário de agentes." in paragrafos
    assert any(
        p.startswith("Riscos do PGR que o sistema não reconheceu — nenhum exame sai deles: 1, em GHE-01.")
        for p in paragrafos
    )


def test_tela_passa_pgr_e_pendencias_ao_memorial(monkeypatch: pytest.MonkeyPatch, proto: Protocolo) -> None:
    # Reversão que mata: a casca chamar montar_memorial só com as matrizes — o
    # memorial baixado sairia sem a lista, mesmo com o núcleo correto.
    import agente_medico.superficie.memorial_matriz as memorial_mod

    pgr, pendencias = _hidratar(proto, ("GESSO", (_GESSO,)))
    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_pgr_hidratado", lambda *a, **k: (pgr, tuple(pendencias))
    )
    original = memorial_mod.montar_memorial
    chamadas: list[dict[str, Any]] = []

    def _espia(*args: Any, **kwargs: Any) -> Any:
        chamadas.append(kwargs)
        return original(*args, **kwargs)

    monkeypatch.setattr(memorial_mod, "montar_memorial", _espia)
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    assert not at.exception

    assert chamadas
    assert chamadas[-1]["pgr"] is at.session_state["web_matriz_cache"].pgr_hidratado
    assert chamadas[-1]["pendencias"] == tuple(pendencias)
