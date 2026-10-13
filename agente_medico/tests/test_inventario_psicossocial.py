"""Inventário psicossocial avaliado (R-PSY-06/R-PSY-08, solução D, 09/10/2026): conta só o
PGR com linha de fator "Psicossocial … nível", e o corte "moderado ou acima" decide a
saúde mental. Cada teste nomeia a reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest

import agente_medico.adaptadores.orquestracao_pgr as orq
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline
from agente_medico.motor.extracao_pgr import (
    TIPO_INVENTARIO_PSICOSSOCIAL_SEM_NIVEL,
    InventarioPsicossocial,
    avaliar_inventario_psicossocial,
    avaliar_inventario_sem_nivel,
)
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.io_pdf import PaginaLida
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import EnvelopeConfirmado, GHEVerbatim, RiscoVerbatim

_PROTOCOLO = carregar(Path(__file__).parent.parent / "protocolo")
_NIVEIS = _PROTOCOLO.vocabulario.niveis_risco

# Verbatim do PGR SPE QD. E-13 (30/09/2026, pág. 22): cita o inventário e o COPSOQ, sem avaliar.
_CITADO_SEM_AVALIACAO = (
    "INVENTÁRIO DE RISCOS PSICOSSOCIAIS POR GHE\n"
    "Avaliação de Riscos Psicossociais — Antecipação Técnica. Em conformidade com a Nota Técnica "
    "SSTmétrica n.º 02/2026, a avaliação dos fatores de risco psicossociais não foi realizada nesta "
    "fase da obra (COPSOQ II-BR ou AQUALI-RPS)."
)
# Linhas no formato do inventário da Vila Brasil escritório (06/10/2026, págs. 78–79).
_FATOR_BAIXO = "Psicossocial Demandas no trabalho Refere - se à intensidade das Transtorno mentais; 3 1 BAIXO"
_FATOR_MODERADO = "Psicossocial Conflitos família e Refere - se à interferência do trabalho 3 2 MODERADO"


def _so_texto(*textos: str) -> list[PaginaLida]:
    return [PaginaLida(t, ()) for t in textos]


def test_inventario_so_citado_nao_conta_como_avaliado() -> None:
    # Reversão que mata: `avaliado` voltar a ser só o marcador (detectar_psicossocial) —
    # o caso E-13/Verde Maris/Sinduscon/Seconci REV4 volta a dar Saúde Mental.
    inventario = avaliar_inventario_psicossocial(_so_texto(_CITADO_SEM_AVALIACAO), _NIVEIS)
    assert inventario == (False, False)


def test_inventario_so_com_fatores_baixos_e_avaliado_abaixo_do_corte() -> None:
    # Reversão que mata: `moderado_ou_acima` igual a `avaliado` (ignorar o nível).
    inventario = avaliar_inventario_psicossocial(_so_texto("COPSOQ II-BR\n" + _FATOR_BAIXO), _NIVEIS)
    assert inventario == (True, False)


def test_inventario_com_um_fator_moderado_entre_baixos_passa_o_corte() -> None:
    # O fator moderado vem depois de um baixo, como nos PGRs do acervo. Reversão que mata:
    # olhar só o primeiro fator lido (`posicoes[0] == "corte"`).
    paginas = _so_texto("COPSOQ II-BR\n" + _FATOR_BAIXO, _FATOR_MODERADO)
    assert avaliar_inventario_psicossocial(paginas, _NIVEIS) == (True, True)


def test_linha_de_fator_sem_marcador_do_inventario_nao_conta() -> None:
    # Reversão que mata: tirar a exigência do marcador (detectar_psicossocial) da função.
    assert avaliar_inventario_psicossocial(_so_texto(_FATOR_MODERADO), _NIVEIS) == (False, False)


def test_hidratar_pgr_replica_o_corte_a_todos_os_ghe() -> None:
    # Reversões que matam: (1) não repassar `psicossocial_moderado` de hidratar_pgr a
    # hidratar_ghe; (2) não gravá-lo no GHEPGR.
    indice = construir_indice_termos(
        _PROTOCOLO.vocabulario.agentes, fracoes_sem_agente=_PROTOCOLO.vocabulario.fracoes_sem_agente
    )
    ghe = GHEVerbatim(nome="Setor", cargos=("Servente",), riscos=())
    pgr, _ = hidratar_pgr(
        (ghe, ghe), indice, date(2026, 9, 1), True, psicossocial=True, psicossocial_moderado=True
    )
    assert [(g.psicossocial, g.psicossocial_moderado) for g in pgr.ghes] == [(True, True), (True, True)]


_GHE = GHEVerbatim(
    nome="Setor Teste",
    cargos=("Servente",),
    riscos=(RiscoVerbatim(agente="Ruido", quantificacao="", fonte_geradora="Fonte X"),),
)


@pytest.mark.parametrize(
    ("inventario", "esperado"),
    [
        ("COPSOQ II-BR\n" + _FATOR_BAIXO + "\n" + _FATOR_MODERADO, (True, True)),
        (_CITADO_SEM_AVALIACAO, (False, False)),
    ],
)
def test_preparar_pgr_hidratado_le_o_inventario_avaliado(
    monkeypatch: pytest.MonkeyPatch, inventario: str, esperado: tuple[bool, bool]
) -> None:
    # Reversões que matam: (1) o orquestrador voltar a detectar_psicossocial — o PGR só
    # citado sai com inventário e o avaliado sai sem o corte; (2) repassar só
    # `inventario.avaliado` a hidratar_pgr — o corte fica False; (3) tirar de
    # preparar_pgr_hidratado o acréscimo de avaliar_inventario_sem_nivel às pendências.
    leitura = (PaginaLida("GHE 1 - Setor Teste\nCargo A\n" + inventario, ()),)

    def _ler(caminho: Path, processos: int | None = None) -> tuple[PaginaLida, ...]:
        return leitura

    def _parsear(_: Any) -> tuple[GHEVerbatim, ...]:
        return (_GHE,)

    monkeypatch.setattr(orq, "ler_pdf", _ler)
    monkeypatch.setattr(orq, "parsear_leitura", _parsear)
    pgr, pendencias = orq.preparar_pgr_hidratado(
        Path("qualquer.pdf"),
        _PROTOCOLO,
        TranscritorGHEOffline(),
        TranscritorCardOffline(),
        EnvelopeConfirmado(validade=date(2026, 9, 1), assinatura_engenheiro=True),
    )
    assert pgr is not None
    assert (pgr.ghes[0].psicossocial, pgr.ghes[0].psicossocial_moderado) == esperado
    avisos = [p for p in pendencias if p.tipo == TIPO_INVENTARIO_PSICOSSOCIAL_SEM_NIVEL]
    assert len(avisos) == (0 if esperado[0] else 1)


# Geometria medida no PGR Soft Connect15 v04 (pág. 42, 13/10/2026): o grupo "ERGONÔMICOS -
# PSICOSSOCIAL" em duas linhas visuais, o nível centrado na altura da linha da tabela, 4,3 pt
# acima de "PSICOSSOCIAL"; no texto, o nível cai na linha do fator ("(Divisão de tarefas e MÉDIO").
_TEXTO_SOFT = (
    "FRPRT\n"
    "ERGONÔMICOS - METODOLOGIA ANEXADA A ESTE\n"
    "(Divisão de tarefas e MÉDIO\n"
    "PSICOSSOCIAL OS RESULTADOS) – ENQUADRAMENTO REALIZADO"
)


def _linha_soft(topo: float, nivel: str, grupo: tuple[str, ...] = ("PSICOSSOCIAL",)) -> list[tuple[str, float, float]]:
    palavras = [("ERGONÔMICOS", 10.3, topo - 8.6), ("-", 57.0, topo - 8.6), ("METODOLOGIA", 300.0, topo - 8.6)]
    palavras.append((nivel, 786.3, topo - 4.3))
    x = 14.2
    for p in grupo:
        palavras.append((p, x, topo))
        x += 45.0
    palavras.append(("OS", 300.0, topo))
    return palavras


def test_nivel_fora_da_linha_do_fator_e_lido_pela_faixa_de_palavras() -> None:
    # Reversão que mata: tirar _niveis_por_faixa_de_palavras de avaliar_inventario_psicossocial
    # (o Soft Connect volta a avaliado=False).
    pagina = PaginaLida(_TEXTO_SOFT, tuple(_linha_soft(353.6, "MÉDIO")))
    assert avaliar_inventario_psicossocial([pagina], _NIVEIS) == (True, True)


def test_grupo_quebrado_com_hifen_antes_de_psicossocia_ainda_e_fator() -> None:
    # Variante "ERGONÔMIC / OS - PSICOSSOCIA / L" do Soft Connect (págs. 55, 177, 192).
    # Reversão que mata: tirar a exceção do "-" na âncora (`p not in ("-", "–")`).
    palavras = [("-", 15.0, 353.6), *_linha_soft(353.6, "BAIXO", grupo=("PSICOSSOCIA",))]
    palavras = [(p, x + 10.0 if p == "PSICOSSOCIA" else x, t) for p, x, t in palavras]
    assert avaliar_inventario_psicossocial([PaginaLida("FRPRT", tuple(palavras))], _NIVEIS) == (True, False)


def test_psicossocial_no_meio_de_frase_nao_e_linha_de_fator() -> None:
    # Prosa da pág. 342 do Soft Connect: "risco psicossocial classificados como Irrelevante
    # ou Baixo". Reversão que mata: tirar a exigência de que "psicossocia…" abra a linha visual.
    frase = ("risco", "psicossocial", "classificados", "como", "Baixo")
    palavras = tuple((p, 48.0 + 40.0 * i, 341.4) for i, p in enumerate(frase))
    assert avaliar_inventario_psicossocial([PaginaLida("FRPRT", palavras)], _NIVEIS) == (False, False)


def test_nivel_da_linha_seguinte_da_tabela_nao_entra_na_faixa() -> None:
    # Linha BAIXO e, 35 pt abaixo, a linha seguinte com MÉDIO, mas cujo fator não é
    # psicossocial (no Soft Connect, a linha seguinte começa a ≥ 31 pt). Reversão que mata:
    # _FAIXA_NIVEL_PSICOSSOCIAL_PT ≥ 31.
    vizinha = [("ERGONÔMICO", 10.3, 388.6 - 8.6), ("MÉDIO", 786.3, 388.6 - 4.3), ("Postural", 14.2, 388.6)]
    palavras = (*_linha_soft(353.6, "BAIXO"), *vizinha)
    assert avaliar_inventario_psicossocial([PaginaLida("FRPRT", palavras)], _NIVEIS) == (True, False)


def test_inventario_citado_sem_nivel_lido_avisa_sem_bloquear() -> None:
    # Reversão que mata: avaliar_inventario_sem_nivel devolver None sempre.
    aviso = avaliar_inventario_sem_nivel([_CITADO_SEM_AVALIACAO], InventarioPsicossocial(False, False))
    assert aviso is not None
    assert (aviso.tipo, aviso.bloqueante) == (TIPO_INVENTARIO_PSICOSSOCIAL_SEM_NIVEL, False)


def test_inventario_avaliado_nao_avisa() -> None:
    # Reversão que mata: tirar `inventario.avaliado` da condição (o aviso sairia nos 11 PGRs
    # avaliados do acervo).
    inventario = avaliar_inventario_psicossocial(_so_texto("COPSOQ II-BR\n" + _FATOR_BAIXO), _NIVEIS)
    assert avaliar_inventario_sem_nivel(["COPSOQ II-BR\n" + _FATOR_BAIXO], inventario) is None


def test_pgr_sem_marcador_nao_avisa() -> None:
    # Reversão que mata: tirar `detectar_psicossocial` da condição (o aviso sairia nos 38 PGRs
    # do acervo sem marcador).
    inventario = avaliar_inventario_psicossocial(_so_texto(_FATOR_MODERADO), _NIVEIS)
    assert avaliar_inventario_sem_nivel([_FATOR_MODERADO], inventario) is None
