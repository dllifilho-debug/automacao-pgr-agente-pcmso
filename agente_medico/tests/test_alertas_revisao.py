"""Alertas para a revisão médica, sem mudar exame (07/10/2026, decisão do Diovanni):
R-PSY-07 — PGR emitido a partir de 26/05/2026 sem inventário psicossocial (NR-01 item
1.5.3.1.4); R-AUD-05 — PGR declara ruído para menor aprendiz (adendo Hetrin, pág. 8).
Cada teste nomeia a reversão que o deixa vermelho."""

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
from agente_medico.motor.tipos import PGR, GHEVerbatim, Pendencia, Resultado, RiscoVerbatim
from agente_medico.superficie.documento_matriz import CabecalhoDocumento
from agente_medico.superficie.memorial_matriz import (
    montar_memorial,
    renderizar_memorial_docx,
    resumos_do_protocolo,
)
from agente_medico.superficie.web_matriz import pagina_matriz
from agente_medico.tests.test_web_matriz import _submeter_formulario

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 10, 7)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _pgr(
    proto: Protocolo,
    cargos: tuple[str, ...] = ("Servente",),
    termos: tuple[str, ...] = ("Ruído",),
    emissao: date = date(2026, 9, 3),
    psicossocial: bool = False,
) -> tuple[PGR, list[Pendencia]]:
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    ghe = GHEVerbatim(
        nome="GHE 08 - APRENDIZ",
        cargos=cargos,
        riscos=tuple(
            # Ruído medido: sem a presunção protetiva (D-ARQ-68 cl.5) a matriz pode sair
            # VÁLIDA, e só um alerta bloqueante a derrubaria.
            RiscoVerbatim(
                agente=t, quantificacao="85 dB(A)" if t == "Ruído" else "", fonte_geradora="",
                avaliacao_qualitativa="2 2 MODERADO (4)",
            )
            for t in termos
        ),
    )
    return hidratar_pgr([ghe], indice, emissao, True, psicossocial=psicossocial)


def _resultado(proto: Protocolo, pgr: PGR) -> Resultado:
    return processar_pgr(pgr, proto, hoje=_HOJE)


def _alertas_nr01(resultado: Resultado) -> list[Pendencia]:
    return [p for p in resultado.pendencias_globais if p.regra_origem == "R-PSY-07"]


def _alertas_menor(resultado: Resultado) -> list[Pendencia]:
    return [p for m in resultado.matrizes for p in m.pendencias if p.regra_origem == "R-AUD-05"]


# --- R-PSY-07 ---------------------------------------------------------------


def test_pgr_pos_vigencia_sem_inventario_gera_alerta_sem_bloquear(proto: Protocolo) -> None:
    # Reversões que matam: (1) tirar o bloco R-PSY-07 de stage_1_gates — sem alerta;
    # (2) `bloqueante=True` — o PGR seria rejeitado.
    resultado = _resultado(proto, _pgr(proto)[0])

    (alerta,) = _alertas_nr01(resultado)
    assert not alerta.bloqueante and "1.5.3.1.4" in alerta.motivo and "03/09/2026" in alerta.motivo
    assert resultado.status != "REJEITADO" and resultado.matrizes


def test_pgr_com_inventario_nao_gera_alerta(proto: Protocolo) -> None:
    # Reversão que mata: tirar `not any(g.psicossocial ...)` da condição.
    assert _alertas_nr01(_resultado(proto, _pgr(proto, psicossocial=True)[0])) == []


@pytest.mark.parametrize(("emissao", "alerta"), [(date(2026, 5, 25), False), (date(2026, 5, 26), True)])
def test_alerta_vale_a_partir_da_vigencia(proto: Protocolo, emissao: date, alerta: bool) -> None:
    # Reversões que matam: (1) tirar a condição de data — o PGR de 25/05 ganharia o
    # alerta; (2) `>` no lugar de `>=` — o de 26/05 (dia da vigência) o perderia.
    assert bool(_alertas_nr01(_resultado(proto, _pgr(proto, emissao=emissao)[0]))) is alerta


# --- R-AUD-05 ---------------------------------------------------------------


@pytest.mark.parametrize("cargo", ["MENOS APRENDIZ", "Menor Aprendiz (menor ou igual a 18 anos)"])
def test_menor_aprendiz_com_ruido_alerta_e_mantem_audiometria(proto: Protocolo, cargo: str) -> None:
    # "MENOS APRENDIZ" é a grafia do adendo Hetrin. Reversões que matam: (1) tirar a
    # chamada de `_menor_aprendiz_com_ruido` no estágio 3; (2) regex só com "menor" — a
    # grafia do adendo escapa; (3) `bloqueante=True` — a matriz cairia para PARCIAL.
    resultado = _resultado(proto, _pgr(proto, cargos=(cargo,), psicossocial=True)[0])

    (alerta,) = _alertas_menor(resultado)
    assert not alerta.bloqueante and cargo in alerta.motivo
    (matriz,) = resultado.matrizes
    assert "audiometria" in {ln.exame for ln in matriz.linhas}
    assert matriz.status == "VÁLIDA"


def test_jovem_aprendiz_com_ruido_nao_alerta(proto: Protocolo) -> None:
    # Reversão que mata: regex só com "aprendiz" — o jovem aprendiz (18 anos ou mais,
    # R70 22/09/2026) ganharia o alerta de menor.
    assert _alertas_menor(_resultado(proto, _pgr(proto, cargos=("Jovem Aprendiz",))[0])) == []


def test_menor_aprendiz_sem_ruido_nao_alerta(proto: Protocolo) -> None:
    # Menor aprendiz só no escritório, sem risco (R70 22/09/2026). Reversão que mata:
    # tirar a condição de ruído — o alerta sairia sem exposição declarada.
    pgr, _ = _pgr(proto, cargos=("Menor Aprendiz",), termos=("Postura inadequada",))
    assert _alertas_menor(_resultado(proto, pgr)) == []


# --- Memorial e tela ---------------------------------------------------------


def test_memorial_traz_os_dois_alertas(proto: Protocolo, tmp_path: Path) -> None:
    # Reversões que matam: (1) montar_memorial não preencher `alertas` ou `avisos_pgr`;
    # (2) não renderizar a lista no GHE ou o aviso no Resumo.
    from docx import Document

    pgr, pendencias = _pgr(proto, cargos=("MENOS APRENDIZ",))
    resultado = _resultado(proto, pgr)
    memorial = montar_memorial(
        resultado.matrizes,
        proto.vocabulario.exames,
        resumos_do_protocolo(proto.regras),
        pgr=pgr,
        pendencias=pendencias,
        pendencias_globais=resultado.pendencias_globais,
    )
    (bloco,) = memorial.blocos
    (aviso,) = memorial.avisos_pgr
    assert bloco.alertas[0].endswith("(ref. R-AUD-05)") and aviso.endswith("(ref. R-PSY-07)")

    destino = tmp_path / "memorial.docx"
    renderizar_memorial_docx(memorial, CabecalhoDocumento("RICCO", "HETRIN", "Adendo", "30/09/2026", "Dra. X", "CRM"), destino)
    paragrafos = [p.text for p in Document(str(destino)).paragraphs]
    assert bloco.alertas[0] in paragrafos and aviso in paragrafos
    assert any(p.startswith("Alertas para a revisão médica:") and bloco.ghe_id in p for p in paragrafos)


def test_tela_mostra_alerta_do_menor_e_aviso_da_nr01(monkeypatch: pytest.MonkeyPatch, proto: Protocolo) -> None:
    # Reversão que mata: tirar o bloco `if alertas:` da conferência (o aviso da NR-01 já
    # sai pelas pendências globais).
    pgr, pendencias = _pgr(proto, cargos=("MENOS APRENDIZ",))
    pgr = dataclasses.replace(pgr, validade=date(2026, 9, 3))
    monkeypatch.setattr(
        "agente_medico.superficie.web_matriz.preparar_pgr_hidratado", lambda *a, **k: (pgr, tuple(pendencias))
    )
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)
    assert not at.exception

    textos = [el.value for el in at.markdown]
    assert "**Alertas para a revisão médica**" in textos
    assert any("R-AUD-05" in t and "MENOS APRENDIZ" in t for t in textos)
    escritos = [str(el.value) for el in at.markdown] + [str(getattr(el, "value", "")) for el in at.main]
    assert any("R-PSY-07" in t for t in escritos)
