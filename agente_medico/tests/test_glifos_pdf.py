"""D-ARQ-89 fatia 2 — glifos que o gerador do PDF deixa sem Unicode (U+0000)
são restaurados na extração pela tabela verificada; glifo fora dela segue NUL.
Caso real: PGR Fascino 15.07.26 (fonte Type3 "Inter-Thin"). Cada teste nomeia a
reversão de código que o deixa vermelho."""

from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor import glifos_pdf
from agente_medico.motor.glifos_pdf import GLIFOS_RESTAURADOS, nome_da_fonte
from agente_medico.motor.io_pdf import paginas_liberadas
from agente_medico.motor.parser_familia_consciente import _separar_cargos_da_celula

_RAIZ = Path(__file__).resolve().parents[2]
_FASCINO = _RAIZ / "matrizes_originais" / "PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"

# Os 13 nomes medidos em 29/09/2026 nos 3 PGRs com NUL (5.879 ocorrências).
_MEDIDOS = {"g14B", "g14C", "g14D", "g14E", "g15C", "g15D", "g15E", "g16E", "g17E", "g17F", "g181", "g183", "g18B"}

requer_fascino = pytest.mark.skipif(not _FASCINO.exists(), reason="PGR Fascino fora do checkout")


def _pagina_2_do_fascino() -> str:
    for numero, pagina in enumerate(paginas_liberadas(_FASCINO), 1):
        if numero == 2:
            return pagina.extract_text() or ""
    raise AssertionError("Fascino sem página 2")


def test_tabela_cobre_os_13_glifos_medidos_com_caractere_imprimivel() -> None:
    # Reversão que mata: tirar uma entrada da tabela (o glifo voltaria a NUL).
    assert {glifo for fonte, glifo in GLIFOS_RESTAURADOS if fonte == "Inter-Thin"} == _MEDIDOS
    assert all(g.caractere.isprintable() and len(g.caractere) == 1 for g in GLIFOS_RESTAURADOS.values())
    assert all(g.procedencia for g in GLIFOS_RESTAURADOS.values())


def test_nome_da_fonte_tira_o_prefixo_de_subconjunto() -> None:
    # Reversão que mata: casar a chave pelo nome cru ("BBAAAA+Inter-Thin") — a
    # tabela nunca casaria, porque o prefixo muda a cada subconjunto.
    assert nome_da_fonte("BBAAAA+Inter-Thin") == "Inter-Thin"
    assert nome_da_fonte("Inter-Thin") == "Inter-Thin"


@requer_fascino
def test_pagina_real_sai_com_o_caractere_impresso() -> None:
    # Fascino p. 2: "Psicossociais (FRPRT)" e "CIPA — Comissão" saíam com NUL.
    # Reversão que mata: não injetar `GerenciadorComGlifos` em `paginas_liberadas`.
    texto = _pagina_2_do_fascino()

    assert "\x00" not in texto
    assert "(FRPRT)" in texto
    assert "CIPA —" in texto


@requer_fascino
def test_glifo_fora_da_tabela_continua_nul(monkeypatch: pytest.MonkeyPatch) -> None:
    # D-ARQ-89 cl.2: sem palpite. Reversão que mata: um fallback que troca NUL
    # não tabelado por outro caractere (ou o apaga) em `restaurar_glifos`.
    sem_parentese = {k: v for k, v in GLIFOS_RESTAURADOS.items() if k[1] != "g14B"}
    monkeypatch.setattr(glifos_pdf, "GLIFOS_RESTAURADOS", sem_parentese)

    texto = _pagina_2_do_fascino()

    assert "\x00FRPRT)" in texto


def test_cbo_entre_parenteses_sai_do_nome_do_cargo() -> None:
    # D-ARQ-89 cl.4. Reversões que matam: classe de _PADRAO_CBO sem "(" antes do
    # código (sobra "(" no nome); com ")" antes do código (engole o ")" de
    # "(Betoneira)"); sem o "CBO:" opcional (sobra "(CBO:", Vila Brasil GHE 20).
    celula = (
        "Encarregado de Elétrica (4110-10), Operador (Betoneira) (7152-10); "
        "Analista jurídico júnior (CBO: 2410-40)"
    )

    assert _separar_cargos_da_celula(celula) == (
        "Encarregado de Elétrica",
        "Operador (Betoneira)",
        "Analista jurídico júnior",
    )
