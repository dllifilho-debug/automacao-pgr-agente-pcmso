import dataclasses

from agente_medico.motor.tipos import (
    Ausente,
    CenarioExposicao,
    GHEContext,
    GHEPGR,
    MatrizGHE,
    Momento,
    Pendencia,
    Quantificacao,
    Risco,
)


def test_momento_enum_completo() -> None:
    assert len(Momento) == 5
    assert {m.value for m in Momento} == {"ADM", "PER", "MR", "RT", "DEM"}


def test_pendencia_bloqueante_default_false() -> None:
    p = Pendencia(tipo="solicitar_fds", destinatario="empresa", motivo="composição ausente")
    assert p.bloqueante is False


def test_ghe_context_aceita_riscos_vazios() -> None:
    ghe = GHEPGR(
        id="GHE-01",
        nome="Administrativo",
        cargos=(),
        riscos=(),
        epis=(),
        produtos_quimicos=(),
        psicossocial=False,
    )
    ctx = GHEContext(pgr_ghe=ghe)
    assert ctx.riscos == []
    assert ctx.predicados == {}
    assert ctx.pendencias == []


def test_pct_quartzo_default_none() -> None:
    q = Quantificacao(valor=0.1, unidade="mg/m3", relacao_LT=None,
                      pct_LT=None, apenas_qualitativa=False)
    assert q.pct_quartzo is None


def test_pct_quartzo_aceita_valor() -> None:
    q = Quantificacao(valor=0.1, unidade="mg/m3", relacao_LT=None,
                      pct_LT=None, apenas_qualitativa=False, pct_quartzo=12.5)
    assert q.pct_quartzo == 12.5


def test_cenario_exposicao_construcao() -> None:
    c = CenarioExposicao(cnae="0710-3/01", atividade="lavra", local="frente de mina")
    assert (c.cnae, c.atividade, c.local) == ("0710-3/01", "lavra", "frente de mina")


def test_ghepgr_cenario_default_none() -> None:
    g = GHEPGR(id="GHE-1", nome="x", cargos=(), riscos=(), epis=(),
               produtos_quimicos=(), psicossocial=False)
    assert g.cenario is None


def test_ghepgr_com_cenario_serializa() -> None:
    c = CenarioExposicao(cnae="0710-3/01", atividade="lavra", local="frente de mina")
    g = GHEPGR(id="GHE-1", nome="x", cargos=(), riscos=(), epis=(),
               produtos_quimicos=(), psicossocial=False, cenario=c)
    d = dataclasses.asdict(g)
    assert d["cenario"] == {"cnae": "0710-3/01", "atividade": "lavra", "local": "frente de mina"}


def test_matriz_ghe_status_default_valida() -> None:
    m = MatrizGHE(ghe_id="GHE-01")
    assert m.status == "VÁLIDA"


def test_matriz_ghe_status_aceita_tri_estado() -> None:
    for s in ("VÁLIDA", "PARCIAL", "BLOQUEADA"):
        m = MatrizGHE(ghe_id="GHE-01", status=s)
        assert m.status == s
