"""D-ARQ-88 fatia 2 — o memorial nomeia o agente que disparou a regra pelo termo
do PGR (Q1), sem o NUL do PDF (Q2), com texto próprio para perna presumida (Q3);
o "não pedido" usa o mesmo termo (Q4). Caso de conferência: Aurora 27/08/26, GHE 11
(PGR p. 45). Cada teste nomeia a reversão de código que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import (
    GHEPGR,
    PGR,
    BlocoVerbatim,
    GHEVerbatim,
    MatrizGHE,
    MembroVerbatim,
    ProdutoQuimico,
    RiscoPGR,
    RiscoVerbatim,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.superficie.memorial_matriz import (
    BlocoMemorial,
    montar_memorial,
    resumos_do_protocolo,
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_HOJE = date(2026, 9, 29)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _pgr_hidratado(proto: Protocolo, *termos: tuple[str, str]) -> PGR:
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    ghe = GHEVerbatim(
        nome="INSTALAÇÕES HIDRO-SANITÁRIAS",
        cargos=("Encanador",),
        riscos=tuple(
            RiscoVerbatim(agente=t, quantificacao="", fonte_geradora="", avaliacao_qualitativa=a)
            for t, a in termos
        ),
    )
    pgr, _ = hidratar_pgr([ghe], indice, date(2030, 1, 1), True)
    return pgr


def _matriz(proto: Protocolo, pgr: PGR) -> MatrizGHE:
    (matriz,) = processar_pgr(pgr, proto, hoje=_HOJE).matrizes
    return matriz


def _bloco(proto: Protocolo, pgr: PGR) -> BlocoMemorial:
    memorial = montar_memorial(
        [_matriz(proto, pgr)], proto.vocabulario.exames, resumos_do_protocolo(proto.regras)
    )
    (bloco,) = memorial.blocos
    return bloco


def _porque(bloco: BlocoMemorial, exame: str) -> str:
    return next(linha.porque for linha in bloco.linhas if linha.exame.startswith(exame))


def test_hidratacao_guarda_o_termo_cru_e_ele_chega_a_origem(proto: Protocolo) -> None:
    # O motor guarda o verbatim, com o NUL do PDF (D-ARQ-22). Reversões que matam:
    # não passar `termo=` ao RiscoPGR no ramo EXATA da hidratação; não copiar
    # `termo` para o Risco em estagios/riscos.py.
    pgr = _pgr_hidratado(proto, ("Metiletilcetona \x00MEK\x00", "2 3 MODERADO"))
    (risco,) = pgr.ghes[0].riscos
    motivo = next(
        m for linha in _matriz(proto, pgr).linhas for m in linha.motivos
        if m.regra_id == "R-BIO-04-metil_etil_cetona"
    )

    assert risco.termo == "Metiletilcetona \x00MEK\x00"
    assert [o.termo for o in motivo.origens] == ["Metiletilcetona \x00MEK\x00"]


def test_aurora_ghe11_memorial_nomeia_os_tres_solventes(proto: Protocolo) -> None:
    # Reversão que mata: `_porque` ignorar `Motivo.origens` — o clínico semestral
    # voltaria a não dizer qual agente o disparou.
    bloco = _bloco(
        proto,
        _pgr_hidratado(
            proto,
            ("Ciclohexanona", "2 3 MODERADO"),
            ("Metiletilcetona \x00MEK\x00", "2 3 MODERADO"),
            ("Tetrahidrofurano", "2 3 MODERADO"),
        ),
    )

    (linha_cli05,) = [p for p in _porque(bloco, "Exame Clínico").split("\n") if "(ref. R-CLI-05)" in p]
    assert (
        "Origem: Ciclohexanona — PGR (nível MODERADO); Metiletilcetona MEK — PGR (nível "
        "MODERADO); Tetrahidrofurano — PGR (nível MODERADO)."
    ) in linha_cli05


def test_nul_entre_espacos_nao_deixa_espaco_duplo(proto: Protocolo) -> None:
    # Padrão medido no Vila Brasil (" \x00 " no lugar do hífen). Reversão que mata:
    # `_termo_exibicao` sem o `" ".join(...split())` — sobraria espaço duplo.
    bloco = _bloco(proto, _pgr_hidratado(proto, ("Metiletilcetona \x00 MEK", "2 3 MODERADO")))

    assert "Origem: Metiletilcetona MEK — PGR" in _porque(bloco, "Exame Clínico")


def test_origem_de_fds_e_nomeada_pela_propria_fonte(proto: Protocolo) -> None:
    # Reversão que mata: tirar o ramo `o.fonte.startswith("FDS")` de
    # `_descrever_origem` — sairia "xileno — FDS — componente…".
    fundo = ProdutoQuimico(
        nome="Fundo Zarcão",
        fds=montar_fds(
            (BlocoVerbatim(faixa="5 – 10", membros=(MembroVerbatim(cas="1330-20-7", nome="Xileno"),)),)
        ),
    )
    ghe = GHEPGR(
        id="GHE-18", nome="PINTURA", cargos=("Pintor",), riscos=(), epis=(),
        produtos_quimicos=(fundo,), psicossocial=False,
    )
    bloco = _bloco(proto, PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,)))

    assert "Origem: FDS — componente Xileno do produto Fundo Zarcão." in _porque(
        bloco, "Ácido metil-hipúrico"
    )


def test_perna_presumida_diz_que_foi_por_precaucao(proto: Protocolo) -> None:
    # Q3. Reversão que mata: `_descrever_origem` ignorar `presumida`.
    bloco = _bloco(proto, _pgr_hidratado(proto, ("Ruído", "2 4 MODERADO")))

    assert (
        "Origem: Ruído — PGR (nível MODERADO); sem medição no PGR; pedido por precaução."
    ) in _porque(bloco, "Audiometria")


def test_duas_grafias_do_mesmo_agente_aparecem_as_duas(proto: Protocolo) -> None:
    # Fascino: "Quartzo" e "Sílica livre" resolvem para `silica`. Reversão que mata:
    # `_origem` ficar só com a primeira origem de cada agente.
    bloco = _bloco(
        proto, _pgr_hidratado(proto, ("Quartzo", "1 1 BAIXO"), ("Sílica livre", "1 1 BAIXO"))
    )

    assert (
        "Origem: Quartzo — PGR (nível BAIXO); Sílica livre — PGR (nível BAIXO). (ref. R-ESP-02)"
    ) in _porque(bloco, "Espirometria")


def test_nao_pedido_usa_o_termo_do_pgr(proto: Protocolo) -> None:
    # Q4. Reversões que matam: voltar `_nao_pedido` ao `replace('_', ' ')` do slug
    # (sairia "xileno"); não preencher `Observacao.termos` em emissao.py.
    bloco = _bloco(proto, _pgr_hidratado(proto, ("Xileno", "1 1 IRRELEVANTE")))

    (nao_pedido,) = bloco.nao_pedidos
    assert "não pedido — Xileno com risco irrelevante no PGR" in nao_pedido


def test_sem_termo_cai_no_slug_legivel(proto: Protocolo) -> None:
    # Risco montado sem hidratação (termo None). Reversão que mata: tirar o
    # fallback `_agente_exibicao` — sairia só a fonte, sem o agente.
    risco = RiscoPGR(tipo="", agente="poeira_de_madeira", quantificacao=None, severidade=None, nivel_risco="BAIXO")
    ghe = GHEPGR(
        id="GHE-08", nome="CARPINTARIA", cargos=("Carpinteiro",), riscos=(risco,), epis=(),
        produtos_quimicos=(), psicossocial=False,
    )
    bloco = _bloco(proto, PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(ghe,)))

    assert "Origem: poeira de madeira — PGR (nível BAIXO)." in _porque(bloco, "Espirometria")
