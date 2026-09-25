"""Revisão na tela: origem do risco por exame (`Motivo.risco_origem`, recorte
atômico de D-ARQ-22 Parte B) e enquadramento no Decreto 3.048/1999, Anexo IV.
Origem medida: Aurora Lago das Rosas, 24/09/2026 — a aguarrás anexada ao GHE
errado gerou ácido t,t-mucônico ao serralheiro sem que a tela dissesse de onde.
Cada teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    BlocoVerbatim,
    ExameEmitido,
    MatrizGHE,
    MembroVerbatim,
    Momento,
    Motivo,
    Pendencia,
    ProdutoQuimico,
    Resultado,
    RiscoPGR,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.superficie.revisao_matriz import (
    NAO_CONFERIDO_3048,
    NAO_CONSTA_3048,
    enquadramento_3048,
    montar_revisao,
    tabela_markdown,
)
from agente_medico.superficie.web_matriz import pagina_matriz

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _pgr(riscos: tuple[RiscoPGR, ...], produtos: tuple[ProdutoQuimico, ...] = ()) -> PGR:
    ghe = GHEPGR(
        id="GHE-18",
        nome="PINTURA",
        cargos=("Pintor",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=produtos,
        psicossocial=False,
    )
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,))


def _linha(pgr: PGR, proto: Protocolo, exame: str) -> ExameEmitido:
    (matriz,) = processar_pgr(pgr, proto).matrizes
    return next(e for e in matriz.linhas if e.exame == exame)


def test_risco_origem_nomeia_pgr_e_fds_na_regra_de_agente(proto: Protocolo) -> None:
    # Reversão que mata: voltar `risco_origem=None` em _emitir_regra, ou filtrar
    # ctx.riscos só pela fonte "explicito" — a FDS some da origem.
    fundo_zarcao = ProdutoQuimico(
        nome="Fundo Zarcão",
        fds=montar_fds(
            (BlocoVerbatim(faixa="5 – 10", membros=(MembroVerbatim(cas="1330-20-7", nome="Xileno"),)),)
        ),
    )
    risco_pgr = RiscoPGR(tipo="", agente="xileno", quantificacao=None, severidade=None, nivel_risco="BAIXO")

    linha = _linha(_pgr((risco_pgr,), (fundo_zarcao,)), proto, "acido_metilhipurico")

    assert [m.risco_origem for m in linha.motivos] == [
        "xileno ← PGR (nível BAIXO) | FDS — componente Xileno do produto Fundo Zarcão"
    ]


def test_risco_origem_fica_vazio_em_regra_sem_agente_direto(proto: Protocolo) -> None:
    # Reversão que mata: tirar a guarda `if not fontes: return None` de
    # _risco_origem — o exame clínico (R-CLI-01, primitivo todo_trabalhador)
    # sairia com uma origem vazia "todo_trabalhador ← ".
    risco_pgr = RiscoPGR(tipo="", agente="xileno", quantificacao=None, severidade=None, nivel_risco="BAIXO")

    linha = _linha(_pgr((risco_pgr,)), proto, "exame_clinico")

    assert all(m.risco_origem is None for m in linha.motivos)


def test_enquadramento_3048_distingue_nao_conferido_de_nao_consta(proto: Protocolo) -> None:
    # Reversão que mata: ler o campo com `meta.get("enquadramento_3048")` sem
    # checar a chave — agente nunca conferido sairia como "não consta".
    agentes = proto.vocabulario.agentes
    assert "enquadramento_3048" not in agentes["poeira_de_madeira"]

    assert enquadramento_3048("ruido", agentes) == "item 2.0.1 — 25 anos"
    assert enquadramento_3048("xileno", agentes) == NAO_CONSTA_3048
    assert enquadramento_3048("poeira_de_madeira", agentes) == NAO_CONFERIDO_3048


def _matriz_com_origem() -> MatrizGHE:
    com_origem = ExameEmitido(
        exame="acido_transmuconico",
        periodicidade_meses=6,
        momentos={Momento.PER},
        motivos=[
            Motivo(
                regra_id="R-BIO-04-benzeno",
                predicado="benzeno",
                risco_origem="benzeno ← FDS — componente Benzeno do produto aguarrás",
                detalhe=None,
                status_regra="VALIDADO",
            )
        ],
    )
    sem_origem = ExameEmitido(
        exame="exame_clinico",
        periodicidade_meses=12,
        momentos={Momento.ADM},
        motivos=[
            Motivo(
                regra_id="R-CLI-01",
                predicado="todo_trabalhador",
                risco_origem=None,
                detalhe=None,
                status_regra="VALIDADO",
            )
        ],
    )
    return MatrizGHE(
        ghe_id="GHE-16",
        linhas=[com_origem, sem_origem],
        riscos_resolvidos=("benzeno",),
        nome_ghe="SERRALHERIA",
        cargos=("Serralheiro",),
    )


def test_revisao_mostra_origem_ou_predicado_e_escapa_barra_vertical(proto: Protocolo) -> None:
    # Reversões que matam: (1) _origem devolver sempre o predicado — a origem
    # da FDS não aparece; (2) tirar o escape de "|" em _celula — a origem com
    # duas fontes quebraria a linha da tabela em colunas a mais.
    (revisao,) = montar_revisao(
        [_matriz_com_origem()], proto.vocabulario.exames, proto.vocabulario.agentes
    )
    origens = [linha.origem for linha in revisao.linhas]
    assert origens == [
        "benzeno ← FDS — componente Benzeno do produto aguarrás",
        "predicado: todo_trabalhador",
    ]

    duas_fontes = montar_revisao(
        [
            MatrizGHE(
                ghe_id="G",
                linhas=[
                    ExameEmitido(
                        exame="acido_metilhipurico",
                        periodicidade_meses=6,
                        momentos={Momento.PER},
                        motivos=[
                            Motivo(
                                regra_id="R-BIO-04-xileno",
                                predicado="xileno",
                                risco_origem="xileno ← PGR | FDS — x",
                                detalhe=None,
                            )
                        ],
                    )
                ],
            )
        ],
        proto.vocabulario.exames,
        proto.vocabulario.agentes,
    )[0]
    linha_tabela = tabela_markdown(duas_fontes).splitlines()[2]
    assert linha_tabela.replace("\\|", "").count("|") == 6


def test_pagina_matriz_mostra_revisao_com_origem_e_decreto_3048(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Reversão que mata: remover o bloco "Revisão — origem dos exames" de
    # pagina_matriz — nem a origem nem o enquadramento aparecem na tela.
    pgr = _pgr(())

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    def _processar_falso(*args: Any, **kwargs: Any) -> Resultado:
        return Resultado(status="OK", matrizes=[_matriz_com_origem()])

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    monkeypatch.setattr("agente_medico.superficie.web_matriz.processar_pgr", _processar_falso)

    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    at.text_input[len(at.text_input) - 1].set_value("2026-12-31").run()
    at.checkbox[0].set_value(True).run()
    at.button[0].click().run()
    assert not at.exception

    textos = [m.value for m in at.markdown]
    assert any("benzeno ← FDS — componente Benzeno do produto aguarrás" in t for t in textos)
    assert "- benzeno: item 1.0.3 — 25 anos" in textos
