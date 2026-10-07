"""D-ARQ-93 fatia 1 — agravo à saúde do PGR guardado por risco (rota por coordenadas) e
levado ao relatório do ASO e ao memorial. Cada teste nomeia a reversão de código que o
deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.motor.parser_familia_consciente import PalavraPDF, parsear_paginas
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    Criterio,
    MatrizGHE,
    RelatorioASO,
    RiscoPGR,
    SugestaoASO,
)
from agente_medico.superficie.memorial_matriz import agravos_pgr_do_ghe
from agente_medico.superficie.relatorio_aso import montar_relatorio_aso

_PGR_FASCINO = (
    Path(__file__).resolve().parents[2]
    / "matrizes_originais"
    / "PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"
)


def _p(text: str, x0: float, top: float) -> PalavraPDF:
    return PalavraPDF(text=text, x0=x0, top=top)


def _bloco(*, com_avaliacao: bool = True) -> tuple[PalavraPDF, ...]:
    cabecalho = [
        _p("GHE", 10.0, 10.0), _p("01", 30.0, 10.0), _p("-", 45.0, 10.0), _p("ALVENARIA", 50.0, 10.0),
        _p("PERIGO", 113.0, 20.0),
        _p("GRUPO", 57.0, 25.0), _p("FONTE", 177.5, 25.0), _p("AGRAVO", 300.0, 25.0),
    ]
    if com_avaliacao:
        cabecalho += [_p("S", 450.0, 25.0), _p("P", 470.0, 25.0), _p("MEDIDAS", 560.0, 25.0)]
    return (
        *cabecalho,
        # risco 1: agente/fonte numa linha; o agravo continua por mais 3 linhas, uma delas
        # só com conteúdo na coluna MEDIDAS.
        _p("FISICO", 57.0, 100.0), _p("Ruido", 113.0, 100.0), _p("Serra", 177.5, 100.0),
        _p("Perda", 300.0, 100.0), _p("4", 450.0, 100.0), _p("1", 470.0, 100.0),
        _p("auditiva", 300.0, 110.0),
        _p("Protetor", 560.0, 120.0),
        _p("induzida.", 300.0, 130.0),
        # risco 2
        _p("QUIMICO", 57.0, 200.0), _p("Cimento", 113.0, 200.0), _p("Massa", 177.5, 200.0),
        _p("Dermatite", 300.0, 200.0),
        # legenda colada, começando na coluna GRUPO
        _p("Legenda", 57.0, 300.0), _p("ignorar", 300.0, 300.0),
    )


def _riscos(**kw: bool) -> list[tuple[str, str, str]]:
    (ghe,) = parsear_paginas([_bloco(**kw)])
    return [(r.agente, r.fonte_geradora, r.agravo) for r in ghe.riscos]


def test_agravo_pega_a_linha_inteira_da_tabela_sem_mudar_agente_e_fonte() -> None:
    # Reversões: limitar o agravo ao recorte de agente/fonte (só a 1ª linha, "Perda");
    # parar o agravo na linha só com MEDIDAS ("Perda auditiva").
    assert _riscos() == [
        ("Ruido", "Serra", "Perda auditiva induzida."),
        ("Cimento", "Massa", "Dermatite"),
    ]


def test_agravo_para_na_proxima_categoria_e_na_legenda() -> None:
    # Reversão: tirar a parada na linha que começa na coluna GRUPO — o risco 1 engole
    # "Dermatite" (próxima categoria) e o risco 2, o "ignorar" da legenda.
    agravos = [a for _, _, a in _riscos()]
    assert agravos == ["Perda auditiva induzida.", "Dermatite"]


def test_sem_avaliacao_localizada_agravo_vazio() -> None:
    # Reversão: sem limite direito, pegar tudo à direita de AGRAVO — o agravo sai com o
    # que estiver nas colunas de avaliação e medidas.
    assert [a for _, _, a in _riscos(com_avaliacao=False)] == ["", ""]


def test_pgr_real_fascino_todo_risco_com_agravo() -> None:
    # Reversão: não passar `agravo=` no RiscoVerbatim de `_extrair_riscos` — os 237
    # riscos do Fascino saem sem agravo.
    from agente_medico.motor.parser_familia_consciente import parsear_arquivo

    riscos = [r for g in parsear_arquivo(_PGR_FASCINO) for r in g.riscos]
    assert len(riscos) == 237
    assert all(r.agravo for r in riscos)
    assert riscos[0].agravo.startswith("A exposição ao ruído excessivo")


def _pgr(*riscos: RiscoPGR) -> PGR:
    ghe = GHEPGR(
        id="GHE-01", nome="ALVENARIA", cargos=("Pedreiro",), riscos=riscos, epis=(),
        produtos_quimicos=(), psicossocial=False,
    )
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))


def _risco_pgr(agente: str | None, termo: str, agravo: str) -> RiscoPGR:
    return RiscoPGR(tipo="", agente=agente, quantificacao=None, severidade=None, termo=termo, agravo=agravo)


def _matriz(*sugestoes: SugestaoASO) -> MatrizGHE:
    return MatrizGHE(ghe_id="GHE-01", nome_ghe="ALVENARIA", cargos=("Pedreiro",), sugestao_aso=RelatorioASO(sugestoes))


def _sug(risco: str, reconhecido: bool = True) -> SugestaoASO:
    return SugestaoASO(risco, reconhecido, "CONSTA", (Criterio("CONSTA", "R-ASO-06", "x"),))


def test_relatorio_casa_agravo_pelo_agente_e_pelo_termo() -> None:
    # Reversões: casar só pelo agente (o termo não reconhecido sai "—"); casar só pelo
    # termo (o ruído, resolvido para "ruido" com termo "Ruido", sai "—"); não juntar as
    # duas linhas do PGR do mesmo agente (só uma das frases sai).
    pgr = _pgr(
        _risco_pgr("ruido", "Ruido", "Perda auditiva."),
        _risco_pgr("ruido", "Ruído contínuo", "Zumbido."),
        _risco_pgr(None, "Poeira de gesso", "Irritação respiratória."),
    )
    relatorio = montar_relatorio_aso([_matriz(_sug("ruido"), _sug("Poeira de gesso", reconhecido=False))], {}, pgr=pgr)
    agravos = {ln.risco: ln.agravo for ln in relatorio.blocos[0].linhas}
    assert agravos["ruido"] == "Perda auditiva.\nZumbido."
    assert agravos["Poeira de gesso (termo do PGR)"] == "Irritação respiratória."


def test_relatorio_sem_agravo_lido_mostra_traco() -> None:
    # Reversão: `_agravo_pgr` devolver "" em vez de "—" — a célula fica em branco e não se
    # distingue de erro de leitura.
    relatorio = montar_relatorio_aso([_matriz(_sug("ruido"))], {}, pgr=_pgr(_risco_pgr("ruido", "Ruido", "")))
    assert relatorio.blocos[0].linhas[0].agravo == "—"


def test_memorial_lista_agravo_por_risco_sem_repetir() -> None:
    # Reversões: tirar o `dict.fromkeys` (a mesma frase do PGR sai duas vezes); incluir
    # risco sem agravo (linha "Umidade: " vazia).
    ghe = _pgr(
        _risco_pgr("ruido", "Ruido", "Perda auditiva."),
        _risco_pgr("ruido", "Ruido", "Perda auditiva."),
        _risco_pgr("umidade", "Umidade", ""),
    ).ghes[0]
    assert agravos_pgr_do_ghe(ghe) == ("Ruido: Perda auditiva.",)
