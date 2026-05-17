from agente_medico.motor.tipos import (
    Ausente,
    GHEContext,
    GHEPGR,
    Momento,
    Pendencia,
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
