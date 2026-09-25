"""D-ARQ-86 fatia 1 — R-BIO-05 em BAIXO só com medição abaixo do nível de ação
(NR-07 7.5.12 "b" c/c NR-09 9.6.1 "b": metade do LT da NR-15 Anexo 11), medição
informada na tela com procedência de laudo. Cada teste nomeia a reversão de
código ou dado que o deixa vermelho."""

from __future__ import annotations

import shutil
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.estagios.emissao import stage_5_emissao
from agente_medico.motor.estagios.predicados_stage import stage_4_predicados
from agente_medico.motor.estagios.riscos import stage_2_riscos
from agente_medico.motor.medicoes import aplicar_medicoes
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    EnvelopeConfirmado,
    ExameEmitido,
    GHEContext,
    MatrizGHE,
    MedicaoInformada,
    Observacao,
    Pendencia,
    ProcedenciaMedicao,
    Quantificacao,
    Risco,
    RiscoPGR,
)
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    RodapeDocumento,
    montar_documento,
)
from agente_medico.superficie.web_matriz import (
    CacheMatrizes,
    executar_rota_determinista_cacheada,
    pagina_matriz,
    registrar_medicao_e_reprocessar,
    remover_medicao_e_reprocessar,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_LAUDO = ProcedenciaMedicao(origem="informada", laudo="L-07", data=date(2026, 5, 10), metodo="NHO-08")
_MHA = "acido_metilhipurico"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _medida(valor: float, unidade: str = "ppm") -> Quantificacao:
    return Quantificacao(
        valor=valor,
        unidade=unidade,
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
        procedencia=_LAUDO,
    )


def _risco_pgr(agente: str, nivel: str | None, q: Quantificacao | None = None) -> RiscoPGR:
    return RiscoPGR(tipo="Químico", agente=agente, quantificacao=q, severidade=None, nivel_risco=nivel)


def _ghe(*riscos: RiscoPGR, ghe_id: str = "GHE-18") -> GHEPGR:
    return GHEPGR(
        id=ghe_id,
        nome="PINTURA",
        cargos=("Pintor",),
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


def _emitir_riscos(proto: Protocolo, *riscos: Risco) -> tuple[dict[str, ExameEmitido], GHEContext]:
    ctx = GHEContext(pgr_ghe=_ghe(), riscos=list(riscos))
    stage_4_predicados(ctx, proto)
    return {e.exame: e for e in stage_5_emissao(ctx, proto)}, ctx


def _risco_motor(fonte: str, nivel: str | None, q: Quantificacao | None) -> Risco:
    return Risco(agente="xileno", fonte=fonte, detalhe=None, quantificacao=q, tipo_ibe=None, nivel_risco=nivel)


# --- Motor: R-BIO-05 com medição ------------------------------------------------


def test_baixo_sem_medicao_emite(proto: Protocolo) -> None:
    # Caso Aurora GHE 18: xileno BAIXO, "avaliação ainda qualitativa". Reversão que
    # mata: em _dispensa_por_medicao, tratar lista de avaliações vazia como
    # dispensa (BAIXO sem medição volta a ser dispensado, o que D-ARQ-86 cl.7 veda).
    exames, ctx = _emitir(proto, _risco_pgr("xileno", "BAIXO"))

    assert _MHA in exames
    assert ctx.observacoes == []


def test_baixo_com_medicao_abaixo_do_nivel_de_acao_dispensa_com_laudo(proto: Protocolo) -> None:
    # 30 ppm = 38,46% do LT de 78 ppm. Reversão que mata: tirar
    # niveis_com_medicao_abaixo_acao de R-BIO-04-xileno em regras.yaml (ou a
    # chamada a _dispensa_por_medicao em stage_5_emissao) — o exame volta.
    exames, ctx = _emitir(proto, _risco_pgr("xileno", "BAIXO", _medida(30)))

    assert _MHA not in exames
    (obs,) = ctx.observacoes
    assert (obs.agente, obs.nivel_risco, obs.exames_dispensados) == ("xileno", "BAIXO", (_MHA,))
    assert obs.medicao == (
        "30 ppm, 38,46% do LT de 78 ppm — NR-15 Anexo 11, Quadro n.º 1 — Xileno (xilol); "
        "laudo L-07, 10/05/2026"
    )


def test_medicao_exatamente_no_nivel_de_acao_emite(proto: Protocolo) -> None:
    # 39 ppm = 50% do LT: o nível de ação já não é "abaixo". Reversão que mata:
    # trocar `<` por `<=` em abaixo_nivel_acao, ou comparar com o LT (100%) em
    # vez do nível de ação (50%) — as duas dispensariam.
    exames, ctx = _emitir(proto, _risco_pgr("xileno", "BAIXO", _medida(39)))

    assert _MHA in exames
    assert ctx.observacoes == []


def test_moderado_com_medicao_baixa_emite(proto: Protocolo) -> None:
    # Q1 ratificada: MODERADO emite mesmo com medição abaixo do nível de ação.
    # Reversão que mata: incluir MODERADO em niveis_com_medicao_abaixo_acao do
    # xileno, ou tirar o `all(n in aceitos ...)` de _dispensa_por_medicao.
    exames, _ = _emitir(proto, _risco_pgr("xileno", "MODERADO", _medida(5)))

    assert _MHA in exames


def test_cancerigeno_com_medicao_baixa_emite(proto: Protocolo) -> None:
    # Decisão do Diovanni (25/09/2026): cancerígeno IARC 1/2A sempre recebe o
    # indicador. Reversão que mata: acrescentar niveis_com_medicao_abaixo_acao a
    # R-BIO-04-tricloroetileno — 1 ppm (1,3% do LT) dispensaria o TCA.
    exames, ctx = _emitir(proto, _risco_pgr("tricloroetileno", "BAIXO", _medida(1)))

    assert "acido_tricloroacetico" in exames
    assert ctx.observacoes == []


def test_medicao_em_mg_m3_compara_com_o_lt_em_mg_m3(proto: Protocolo) -> None:
    # 100 mg/m³ = 29% do LT de 340 mg/m³ → dispensa; contra o LT em ppm (78)
    # seriam 128%. Reversão que mata: limite_quimico ignorar a unidade e devolver
    # sempre o LT em ppm.
    exames, ctx = _emitir(proto, _risco_pgr("xileno", "BAIXO", _medida(100, "mg/m3")))

    assert _MHA not in exames
    assert ctx.observacoes[0].medicao is not None
    assert ctx.observacoes[0].medicao.startswith("100 mg/m³, 29,41% do LT de 340 mg/m³")


def test_composicao_de_fds_sem_nivel_e_coberta_pela_medicao(proto: Protocolo) -> None:
    # Aurora GHE 18: xileno BAIXO no PGR e xileno do Fundo Zarcão anexado (risco de
    # composição, sem nível). Reversão que mata: exigir nível em todo risco do
    # agente (tirar a exceção de fonte "quimico_composicao") — voltaria a emitir.
    exames, ctx = _emitir_riscos(
        proto,
        _risco_motor("explicito", "BAIXO", _medida(10)),
        _risco_motor("quimico_composicao", None, None),
    )

    assert _MHA not in exames
    assert len(ctx.observacoes) == 1


def test_risco_implicito_sem_nivel_emite_mesmo_com_medicao(proto: Protocolo) -> None:
    # Risco inferido do cargo não tem classificação no PGR. Reversão que mata:
    # aceitar nível ausente de qualquer fonte (não só de composição de FDS).
    exames, _ = _emitir_riscos(
        proto,
        _risco_motor("explicito", "BAIXO", _medida(10)),
        _risco_motor("implicito_cargo", None, None),
    )

    assert _MHA in exames


def test_maior_medicao_decide(proto: Protocolo) -> None:
    # Duas linhas de xileno no PGR, uma a 10 ppm e outra a 60 ppm (77%). Reversão
    # que mata: usar min() (ou a primeira medição) em vez de max() em
    # _dispensa_por_medicao — a medição baixa dispensaria.
    exames, _ = _emitir(
        proto,
        _risco_pgr("xileno", "BAIXO", _medida(10)),
        _risco_pgr("xileno", "BAIXO", _medida(60)),
    )

    assert _MHA in exames


# --- Carregador do protocolo --------------------------------------------------


def _copiar_protocolo(tmp_path: Path) -> Path:
    destino = tmp_path / "protocolo"
    shutil.copytree(_PROTOCOLO_DIR, destino)
    return destino


def test_carregador_recusa_dispensa_por_medicao_em_agente_sem_lt(tmp_path: Path) -> None:
    # Ciclohexanona não está no Anexo 11. Reversão que mata: tirar de
    # _validar_mencao_documental a exigência de lt_nr15 — a chave carregaria e
    # nunca dispensaria, sem aviso.
    destino = _copiar_protocolo(tmp_path)
    regras = destino / "regras.yaml"
    texto = regras.read_text(encoding="utf-8")
    alvo = "    quando: ciclohexanona\n    mencao_documental: {regra: R-BIO-05, niveis_risco: [IRRELEVANTE]}"
    assert alvo in texto
    regras.write_text(
        texto.replace(
            alvo,
            "    quando: ciclohexanona\n    mencao_documental: {regra: R-BIO-05, niveis_risco: "
            "[IRRELEVANTE], niveis_com_medicao_abaixo_acao: [BAIXO]}",
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="exige 'lt_nr15'"):
        carregar(destino)


def test_carregador_recusa_lt_nao_positivo(tmp_path: Path) -> None:
    # LT zero ou negativo viraria divisão por zero ou dispensa por conta errada.
    # Reversão que mata: tirar a chamada a _validar_lt_nr15 de carregar().
    destino = _copiar_protocolo(tmp_path)
    agentes = destino / "vocabulario" / "agentes.yaml"
    texto = agentes.read_text(encoding="utf-8")
    alvo = "lt_nr15: {ppm: 78, mg_m3: 340, fonte: \"NR-15 Anexo 11, Quadro n.º 1 — Xileno (xilol)\"}"
    assert alvo in texto
    agentes.write_text(texto.replace(alvo, alvo.replace("ppm: 78", "ppm: 0")), encoding="utf-8")

    with pytest.raises(ValueError, match="lt_nr15"):
        carregar(destino)


# --- Aplicação das medições ao PGR (cl.2/cl.4) ---------------------------------


def _pgr(*ghes: GHEPGR) -> PGR:
    return PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=ghes)


def _medicao(valor: float, agente: str = "xileno", ghe_id: str = "GHE-18") -> MedicaoInformada:
    return MedicaoInformada(ghe_id=ghe_id, agente=agente, valor=valor, unidade="ppm", procedencia=_LAUDO)


def test_divergencia_com_o_pgr_gera_pendencia_e_fica_o_maior(proto: Protocolo) -> None:
    # PGR diz 50 ppm (64%), laudo informado diz 10 ppm (13%). Reversão que mata:
    # _escolher devolver sempre a informada — o valor baixo esconderia a medição
    # alta do PGR e dispensaria o exame.
    pgr = _pgr(_ghe(_risco_pgr("xileno", "BAIXO", Quantificacao(50.0, "ppm", None, None, False))))

    novo, pendencias = aplicar_medicoes(pgr, (_medicao(10),), proto.vocabulario.agentes)

    assert novo.ghes[0].riscos[0].quantificacao is not None
    assert novo.ghes[0].riscos[0].quantificacao.valor == 50.0
    assert [p.tipo for p in pendencias] == ["medicao_divergente"]


def test_medicao_sem_risco_do_agente_nao_aplica_e_avisa(proto: Protocolo) -> None:
    # Reversão que mata: tirar o guard `if not any(r.agente == ...)` de
    # aplicar_medicoes — a medição sumiria sem pendência.
    pgr = _pgr(_ghe(_risco_pgr("tolueno", "BAIXO")))

    novo, pendencias = aplicar_medicoes(pgr, (_medicao(10),), proto.vocabulario.agentes)

    assert novo == pgr
    assert [(p.tipo, p.ghe_id) for p in pendencias] == [("medicao_sem_risco", "GHE-18")]


# --- Documento ----------------------------------------------------------------


def test_celula_da_observacao_leva_medicao_e_laudo(proto: Protocolo) -> None:
    # Reversão que mata: tirar o ramo `obs.medicao is not None` de
    # _formatar_observacao — a célula diria só "risco baixo", sem o laudo que
    # sustenta a dispensa (D-ARQ-86 cl.3).
    matriz = MatrizGHE(
        ghe_id="GHE-18",
        cargos=("Pintor",),
        observacoes=(
            Observacao(
                regra_id="R-BIO-04-xileno",
                regra_dispensa="R-BIO-05",
                agente="xileno",
                nivel_risco="BAIXO",
                exames_dispensados=(_MHA,),
                medicao="30 ppm, 38,46% do LT de 78 ppm — NR-15; laudo L-07, 10/05/2026",
            ),
        ),
    )
    doc = montar_documento(
        [matriz],
        proto.vocabulario.exames,
        CabecalhoDocumento("e", "o", "t", "d", "m", "c"),
        RodapeDocumento("r", "m", "d"),
    )

    (linha,) = doc.blocos[0].linhas
    (celula,) = linha.celulas
    assert celula.startswith(
        "Obs.: risco baixo no PGR e medição abaixo do nível de ação para xileno "
        "(30 ppm, 38,46% do LT de 78 ppm — NR-15; laudo L-07, 10/05/2026)"
    )


# --- Tela: cache e reprocessamento (cl.8) ---------------------------------------


def _cache(proto: Protocolo, pgr: PGR) -> CacheMatrizes:
    return CacheMatrizes(
        chave="sha:2026-12-31:True",
        matrizes=(),
        exames_vocab=proto.vocabulario.exames,
        pendencias=(),
        status="OK",
        pendencias_globais=(),
        chamadas_ia=0,
        pgr_hidratado=pgr,
    )


def _exames(cache: CacheMatrizes) -> set[str]:
    assert cache.matrizes is not None
    return {e.exame for e in cache.matrizes[0].linhas}


def test_registrar_e_remover_medicao_refazem_a_matriz(proto: Protocolo) -> None:
    # Reversão que mata: _reprocessar passar pgr_atualizado direto a
    # processar_pgr, sem aplicar_medicoes — a medição registrada não mudaria nada.
    cache = _cache(proto, _pgr(_ghe(_risco_pgr("xileno", "BAIXO"))))

    com = registrar_medicao_e_reprocessar(cache, proto, _medicao(10))
    sem = remover_medicao_e_reprocessar(com, proto, "GHE-18", "xileno")

    assert _MHA not in _exames(com)
    assert _MHA in _exames(sem)
    assert sem.medicoes == ()
    assert com.pgr_hidratado == cache.pgr_hidratado


def test_nova_medicao_do_mesmo_agente_substitui_a_anterior(proto: Protocolo) -> None:
    # Laudo novo com 60 ppm (77%) substitui o de 10 ppm. Reversão que mata:
    # registrar sem filtrar a medição anterior do mesmo (GHE, agente) — as duas
    # ficariam e a de 60 ppm venceria só por acaso de ordem, não por substituição.
    cache = _cache(proto, _pgr(_ghe(_risco_pgr("xileno", "BAIXO"))))

    cache = registrar_medicao_e_reprocessar(cache, proto, _medicao(60))
    cache = registrar_medicao_e_reprocessar(cache, proto, _medicao(10))

    assert [m.valor for m in cache.medicoes] == [10]
    assert _MHA not in _exames(cache)


def _rodar(
    monkeypatch: pytest.MonkeyPatch, conteudo: bytes, validade: date, cache: CacheMatrizes | None
) -> CacheMatrizes:
    pgr = _pgr(_ghe(_risco_pgr("xileno", "BAIXO")))

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    _doc, _html, _pend, novo = executar_rota_determinista_cacheada(
        Path("pgr.pdf"),
        conteudo,
        EnvelopeConfirmado(validade=validade, assinatura_engenheiro=True),
        CabecalhoDocumento("e", "o", "t", "d", "m", "c"),
        RodapeDocumento("r", "m", "d"),
        cache,
    )
    return novo


def test_medicao_sobrevive_ao_reprocessamento_do_mesmo_pdf(
    proto: Protocolo, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Trocar a validade refaz o parse do mesmo PDF. Reversão que mata: tirar o
    # repasse de medicoes_anteriores em executar_rota_determinista_cacheada.
    cache = _rodar(monkeypatch, b"mesmo pdf", date(2026, 12, 31), None)
    cache = registrar_medicao_e_reprocessar(cache, proto, _medicao(10))

    cache = _rodar(monkeypatch, b"mesmo pdf", date(2027, 6, 30), cache)

    assert [m.valor for m in cache.medicoes] == [10]
    assert _MHA not in _exames(cache)


def test_pdf_diferente_nao_herda_medicao(proto: Protocolo, monkeypatch: pytest.MonkeyPatch) -> None:
    # Laudo de uma obra não vale para o PGR de outra. Reversão que mata: tirar a
    # checagem _mesmo_pdf do repasse de medições.
    cache = _rodar(monkeypatch, b"pgr da obra A", date(2026, 12, 31), None)
    cache = registrar_medicao_e_reprocessar(cache, proto, _medicao(10))

    cache = _rodar(monkeypatch, b"pgr da obra B", date(2026, 12, 31), cache)

    assert cache.medicoes == ()
    assert _MHA in _exames(cache)


def _pagina_com_pgr(monkeypatch: pytest.MonkeyPatch) -> AppTest:
    pgr = _pgr(_ghe(_risco_pgr("xileno", "BAIXO"), _risco_pgr("ciclohexanona", "BAIXO")))

    def _preparar_falso(*args: Any, **kwargs: Any) -> tuple[PGR, tuple[Pendencia, ...]]:
        return pgr, ()

    monkeypatch.setattr("agente_medico.superficie.web_matriz.preparar_pgr_hidratado", _preparar_falso)
    at = AppTest.from_function(pagina_matriz)
    at.run()
    at.file_uploader[0].set_value(("pgr.pdf", b"conteudo qualquer", "application/pdf")).run()
    next(t for t in at.text_input if t.label == "Médico coordenador").set_value("Dra. Teste").run()
    next(t for t in at.text_input if t.label == "CRM").set_value("CRM-GO 0000").run()
    at.text_input[len(at.text_input) - 1].set_value((date.today() - timedelta(days=30)).isoformat()).run()
    at.checkbox[0].set_value(True).run()
    at.button[0].click().run()
    # O painel lê o cache no topo da página: aparece no rerun seguinte ao
    # "Gerar matriz", como o de produtos anexados.
    at.run()
    assert not at.exception
    return at


def test_tela_registra_medicao_com_procedencia(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: o callback _registrar_medicao não gravar o cache novo em
    # st.session_state — o rerun relê o cache antigo e a medição some.
    at = _pagina_com_pgr(monkeypatch)
    assert at.selectbox(key="medicao_agente").options == ["xileno"]

    at.number_input(key="medicao_valor").set_value(10.0)
    at.text_input(key="medicao_laudo").set_value("L-07")
    at.button(key="registrar_medicao").click().run()
    assert not at.exception

    (medicao,) = at.session_state["web_matriz_cache"].medicoes
    assert (medicao.ghe_id, medicao.agente, medicao.valor, medicao.unidade) == ("GHE-18", "xileno", 10.0, "ppm")
    assert (medicao.procedencia.origem, medicao.procedencia.laudo) == ("informada", "L-07")


def test_tela_recusa_medicao_sem_laudo(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: tirar a checagem de laudo vazio de _registrar_medicao —
    # entraria dispensa sem procedência (D-ARQ-86 cl.1, laudo obrigatório).
    at = _pagina_com_pgr(monkeypatch)

    at.number_input(key="medicao_valor").set_value(10.0)
    at.button(key="registrar_medicao").click().run()

    assert at.session_state["web_matriz_cache"].medicoes == ()
    assert [w.value for w in at.warning] == ["Informe valor maior que zero e a identificação do laudo."]
