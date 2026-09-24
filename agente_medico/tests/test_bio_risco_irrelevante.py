"""R-BIO-05 / DT-003EB-02 — agente do Quadro 1 (IBE/EE) com risco classificado
como IRRELEVANTE no PGR não gera indicador biológico: a linha de R-BIO-04 vira
observação de menção documental. BAIXO emite (decisão do Diovanni, 24/09/2026,
sobre a medição dos 3 pares). Cada teste nomeia a reversão de código ou dado
que o deixa vermelho."""

from __future__ import annotations

import shutil
from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.superficie.apresentacao_matriz import renderizar_matriz
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    RodapeDocumento,
    montar_documento,
)
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    ExameEmitido,
    GHEContext,
    MatrizGHE,
    Observacao,
    RiscoPGR,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 24)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _risco(agente: str, nivel: str | None) -> RiscoPGR:
    return RiscoPGR(tipo="", agente=agente, quantificacao=None, severidade=None, nivel_risco=nivel)


def _ghe(*riscos: RiscoPGR) -> GHEPGR:
    return GHEPGR(
        id="GHE-10",
        nome="HIDRÁULICA",
        cargos=("Encanador",),
        riscos=riscos,
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )


def _emitir(proto: Protocolo, *riscos: RiscoPGR) -> tuple[dict[str, ExameEmitido], GHEContext]:
    ctx = GHEContext(pgr_ghe=_ghe(*riscos))
    stage_2_riscos(ctx, proto)
    stage_4_predicados(ctx, proto)
    return {e.exame: e for e in stage_5_emissao(ctx, proto)}, ctx


def test_risco_irrelevante_troca_indicador_por_observacao(proto: Protocolo) -> None:
    # Caso Porto Araras I (GHE-14 PINTURA): 2-butoxietanol "irrelevante", gabarito
    # sem BAA. Reversão que mata: remover o desvio `_nivel_dispensa` de
    # stage_5_emissao (ou a chave mencao_documental de R-BIO-04-butoxietanol_2)
    # — o BAA volta a sair e nenhuma observação é gerada.
    exames, ctx = _emitir(proto, _risco("butoxietanol_2", "IRRELEVANTE"))

    assert "acido_butoxiacetico_urina" not in exames
    assert [(o.agente, o.nivel_risco, o.exames_dispensados, o.regra_dispensa) for o in ctx.observacoes] == [
        ("butoxietanol_2", "IRRELEVANTE", ("acido_butoxiacetico_urina",), "R-BIO-05"),
    ]


def test_risco_baixo_emite_indicador(proto: Protocolo) -> None:
    # Caso Porto Araras I / Vila Brasil: a Dra. Patrícia pede acetona e MEK com
    # risco BAIXO. Reversão que mata: voltar BAIXO para niveis_risco das
    # R-BIO-04 (regras.yaml), ou `_nivel_dispensa` dispensar sem olhar o nível.
    exames, ctx = _emitir(
        proto, _risco("acetona", "BAIXO"), _risco("metil_etil_cetona", "BAIXO")
    )

    assert exames["acetona_urina"].periodicidade_meses == 6
    assert exames["mek_urina"].periodicidade_meses == 6
    assert ctx.observacoes == []


def test_nivel_ausente_emite_indicador(proto: Protocolo) -> None:
    # PGR sem avaliação P×S na linha (rota LLM, card, outras famílias).
    # Reversão que mata: aceitar nivel_risco None como dispensável
    # (`n in permitidos or n is None`) — silêncio do PGR viraria dispensa.
    exames, ctx = _emitir(proto, _risco("acetona", None))

    assert "acetona_urina" in exames
    assert ctx.observacoes == []


def test_mesmo_agente_irrelevante_e_baixo_emite(proto: Protocolo) -> None:
    # Reversão que mata: trocar `all` por `any` em `_nivel_dispensa` — uma linha
    # IRRELEVANTE esconderia a linha BAIXO do mesmo agente.
    exames, ctx = _emitir(proto, _risco("xileno", "IRRELEVANTE"), _risco("xileno", "BAIXO"))

    assert "acido_metilhipurico" in exames
    assert ctx.observacoes == []


def test_observacao_carrega_o_maior_nivel_dispensado(tmp_path: Path) -> None:
    # Mecanismo, não a conduta vigente: com dois níveis dispensáveis, a
    # observação nomeia o maior. Reversão que mata: trocar `max` por `min` em
    # `_nivel_dispensa` — a menção diria "irrelevante" com linha BAIXO no PGR.
    regras = tmp_path / "protocolo" / "regras.yaml"
    shutil.copytree(_PROTOCOLO_DIR, tmp_path / "protocolo")
    texto = regras.read_text(encoding="utf-8")
    alvo = "    quando: tolueno\n    mencao_documental: {regra: R-BIO-05, niveis_risco: [IRRELEVANTE]}"
    assert alvo in texto
    regras.write_text(
        texto.replace(alvo, alvo.replace("[IRRELEVANTE]", "[IRRELEVANTE, BAIXO]")), encoding="utf-8"
    )

    _, ctx = _emitir(
        carregar(tmp_path / "protocolo"), _risco("tolueno", "IRRELEVANTE"), _risco("tolueno", "BAIXO")
    )

    assert [o.nivel_risco for o in ctx.observacoes] == ["BAIXO"]


def test_mencao_documental_so_nas_regras_do_quadro_1(proto: Protocolo) -> None:
    # Escopo da decisão: IBE/EE (Quadro 1), só IRRELEVANTE. O Quadro 2 (IBE/SC,
    # significado clínico) segue emitindo em qualquer nível. Computado do dado
    # (D-ARQ-67). Reversão que mata: tirar a chave de qualquer R-BIO-04 EE,
    # pô-la numa R-BIO-04 SC, ou acrescentar BAIXO a qualquer niveis_risco.
    agentes = proto.vocabulario.agentes
    bio04 = [r for r in proto.regras if str(r["id"]).startswith("R-BIO-04-")]
    com_chave = {r["id"] for r in bio04 if "mencao_documental" in r}
    ee = {r["id"] for r in bio04 if agentes[r["quando"]].get("tipo_ibe") == "EE"}

    assert com_chave == ee
    assert len(ee) == 42
    assert all(
        r["mencao_documental"] == {"regra": "R-BIO-05", "niveis_risco": ["IRRELEVANTE"]}
        for r in bio04
        if "mencao_documental" in r
    )


def _protocolo_com_regra_extra(tmp_path: Path, regra_yaml: str) -> Path:
    destino = tmp_path / "protocolo"
    shutil.copytree(_PROTOCOLO_DIR, destino)
    regras = destino / "regras.yaml"
    regras.write_text(regras.read_text(encoding="utf-8") + "\n" + regra_yaml, encoding="utf-8")
    return destino


def test_carregar_recusa_mencao_em_regra_que_nao_e_de_agente(tmp_path: Path) -> None:
    # Reversão que mata: remover a checagem de `quando` em
    # _validar_mencao_documental — a regra entraria e o desvio compararia
    # r.agente com um nome de predicado composto, dispensando nunca.
    diretorio = _protocolo_com_regra_extra(
        tmp_path,
        "  - id: R-TESTE-01\n"
        "    quando: atividade_critica\n"
        "    mencao_documental: {regra: R-BIO-05, niveis_risco: [BAIXO]}\n"
        "    emite:\n"
        "      - {exame: acetona_urina, periodicidade_meses: 6, momentos: [per]}\n"
        "    status: INTERPRETADO\n",
    )

    with pytest.raises(ValueError, match="slug\\s+de agente"):
        carregar(diretorio)


def test_carregar_recusa_nivel_que_o_parser_nao_produz(tmp_path: Path) -> None:
    # Reversão que mata: remover a checagem de niveis_risco — "Baixo" (grafia
    # do PGR, não do parser) nunca casaria e a dispensa ficaria inerte em silêncio.
    diretorio = _protocolo_com_regra_extra(
        tmp_path,
        "  - id: R-TESTE-01\n"
        "    quando: acetona\n"
        "    mencao_documental: {regra: R-BIO-05, niveis_risco: [Baixo]}\n"
        "    emite:\n"
        "      - {exame: acetona_urina, periodicidade_meses: 6, momentos: [per]}\n"
        "    status: INTERPRETADO\n",
    )

    with pytest.raises(ValueError, match="niveis_risco"):
        carregar(diretorio)


def test_orquestrador_leva_observacao_para_a_matriz(proto: Protocolo) -> None:
    # Reversão que mata: remover `matriz.observacoes = tuple(ctx.observacoes)`
    # de executar — a observação morre no contexto e não chega à saída.
    pgr = PGR(validade=date(2026, 7, 15), assinatura_engenheiro=True, ghes=(_ghe(_risco("acetona", "IRRELEVANTE")),))

    (matriz,) = executar(pgr, proto, hoje=_HOJE).matrizes

    assert [o.agente for o in matriz.observacoes] == ["acetona"]
    assert "acetona_urina" not in {ln.exame for ln in matriz.linhas}


def _matriz_com_observacao() -> MatrizGHE:
    return MatrizGHE(
        ghe_id="GHE-10",
        cargos=("Encanador",),
        observacoes=(
            Observacao(
                regra_id="R-BIO-04-acetona",
                regra_dispensa="R-BIO-05",
                agente="acetona",
                nivel_risco="IRRELEVANTE",
                exames_dispensados=("acetona_urina",),
            ),
        ),
    )


def test_documento_poe_a_observacao_na_linha_do_cargo(proto: Protocolo) -> None:
    # Reversão que mata: _celulas_da_matriz deixar de anexar as observações —
    # o documento assinável sai sem a menção que substitui o exame.
    doc = montar_documento(
        [_matriz_com_observacao()],
        proto.vocabulario.exames,
        CabecalhoDocumento("", "", "", "", "", ""),
        RodapeDocumento("", "", ""),
    )

    (linha,) = doc.blocos[0].linhas
    assert linha.celulas == (
        "Obs.: risco irrelevante no PGR para acetona — incluir menção no PCMSO; "
        "não solicitado: Acetona na urina",
    )


def test_apresentacao_de_revisao_lista_a_observacao() -> None:
    # Reversão que mata: remover o bloco de observações de renderizar_matriz —
    # a revisão de saída não veria por que o indicador sumiu.
    texto = "\n".join(renderizar_matriz(_matriz_com_observacao()))

    assert "`acetona` risco IRRELEVANTE → acetona_urina não emitido (R-BIO-04-acetona, R-BIO-05)" in texto
