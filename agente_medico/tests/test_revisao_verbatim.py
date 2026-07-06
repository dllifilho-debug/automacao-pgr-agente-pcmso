from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.revisao_verbatim import (
    VerbatimInvalido,
    desserializar_verbatim,
    montar_fds_revisado,
    serializar_verbatim,
)
from agente_medico.motor.tipos import (
    FDS,
    GHEPGR,
    PGR,
    BlocoVerbatim,
    MembroVerbatim,
    ProdutoQuimico,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.tests.fixtures.fds_t65 import tinta_acrilica
from agente_medico.tests.fixtures.fds_verbatim_t65 import tinta_acrilica_verbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)
_INDICE = construir_indice_cas(_PROTO.vocabulario.agentes)


def _pgr_com_fds(fds: FDS) -> PGR:
    return PGR(
        validade=date(2026, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="G1",
                nome="GHE 1",
                cargos=("c",),
                riscos=(),
                epis=(),
                produtos_quimicos=(ProdutoQuimico(nome="Produto", fds=fds),),
                psicossocial=False,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Round-trip identidade: desserializar(serializar(x)) == x
# ---------------------------------------------------------------------------


def test_round_trip_quebra_de_linha_intra_token_no_nome_e_no_cas() -> None:
    blocos = (
        BlocoVerbatim(
            faixa="1 - 15",
            membros=(MembroVerbatim(cas="134363-67-\n7", nome="Dióxido de\nTitânio"),),
        ),
    )
    assert desserializar_verbatim(serializar_verbatim(blocos)) == blocos


def test_round_trip_faixa_vazia() -> None:
    blocos = (BlocoVerbatim(faixa="", membros=(MembroVerbatim(cas="", nome="Solvente"),)),)
    assert desserializar_verbatim(serializar_verbatim(blocos)) == blocos


def test_round_trip_multi_membro() -> None:
    blocos = (
        BlocoVerbatim(
            faixa="0,2 – 0,05",
            membros=(
                MembroVerbatim(cas="2634-33-5", nome="A"),
                MembroVerbatim(cas="55965-84-9", nome="B"),
            ),
        ),
    )
    assert desserializar_verbatim(serializar_verbatim(blocos)) == blocos


def test_round_trip_acentos_unicode() -> None:
    blocos = (
        BlocoVerbatim(
            faixa="0,1 - 1",
            membros=(MembroVerbatim(cas="1336-21-6", nome="Hidróxido de amônia (24°Bé)"),),
        ),
    )
    assert desserializar_verbatim(serializar_verbatim(blocos)) == blocos


def test_round_trip_tupla_vazia() -> None:
    blocos: tuple[BlocoVerbatim, ...] = ()
    assert desserializar_verbatim(serializar_verbatim(blocos)) == blocos


# ---------------------------------------------------------------------------
# Rejeições — cada uma diz O QUE falhou (anti-erro-silencioso, D-ARQ-22)
# ---------------------------------------------------------------------------


def test_rejeita_json_invalido() -> None:
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim("{isso nao e json")


def test_rejeita_envelope_sem_versao() -> None:
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(json.dumps({"blocos": []}))


def test_rejeita_versao_desconhecida() -> None:
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(json.dumps({"versao": 2, "blocos": []}))


def test_rejeita_bloco_sem_faixa() -> None:
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(json.dumps({"versao": 1, "blocos": [{"membros": []}]}))


def test_rejeita_membro_sem_nome() -> None:
    texto = json.dumps(
        {"versao": 1, "blocos": [{"faixa": "1 - 2", "membros": [{"cas": "1-2-3"}]}]}
    )
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(texto)


def test_rejeita_campo_extra_em_bloco() -> None:
    texto = json.dumps(
        {"versao": 1, "blocos": [{"faixa": "1 - 2", "membros": [], "extra": "x"}]}
    )
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(texto)


def test_rejeita_campo_extra_em_membro() -> None:
    texto = json.dumps(
        {
            "versao": 1,
            "blocos": [
                {
                    "faixa": "1 - 2",
                    "membros": [{"cas": "1-2-3", "nome": "X", "extra": "y"}],
                }
            ],
        }
    )
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(texto)


def test_rejeita_blocos_nao_lista() -> None:
    with pytest.raises(VerbatimInvalido):
        desserializar_verbatim(json.dumps({"versao": 1, "blocos": "não é lista"}))


# ---------------------------------------------------------------------------
# montar_fds_revisado — mesmo gate_forma de transcritor_fds.py, D-ARQ-47 cl.4
# ---------------------------------------------------------------------------


def test_montar_fds_revisado_blocos_validos_bate_montar_fds_sem_pendencia() -> None:
    blocos = tinta_acrilica_verbatim()
    fds, pendencias = montar_fds_revisado(blocos)
    assert fds == montar_fds(blocos)
    assert pendencias == ()


def test_montar_fds_revisado_mistura_valido_invalido() -> None:
    bom = BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim(cas="1-2-3", nome="A"),))
    ruim = BlocoVerbatim(faixa="xyz", membros=(MembroVerbatim(cas="1-2-3", nome="B"),))
    fds, pendencias = montar_fds_revisado((bom, ruim))
    assert fds == montar_fds((bom,))
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_fds"
    assert pendencias[0].bloqueante is True


# ---------------------------------------------------------------------------
# Fim-a-fim com revisão simulada (mock, sem API): verbatim -> serializar ->
# desserializar -> montar_fds_revisado -> resolver_composicao == fds_t65.
# ---------------------------------------------------------------------------


def test_fim_a_fim_tinta_com_revisao_simulada_bate_gabarito_cas_e_concentracao() -> None:
    candidato = tinta_acrilica_verbatim()
    revisado = desserializar_verbatim(serializar_verbatim(candidato))

    fds, pendencias = montar_fds_revisado(revisado)
    assert pendencias == ()

    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), _INDICE)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    comps = resolvido.composicao
    gabarito = tinta_acrilica()

    assert len(comps) == len(gabarito)
    for c, g in zip(comps, gabarito):
        assert c.cas == g.cas
        assert c.concentracao == g.concentracao
        # nome é texto-livre-de-LLM, não-== (D-ARQ-42 P4)


def test_revisao_efetiva_edicao_do_rt_no_json_muda_a_saida() -> None:
    # Prova que a revisão MUDA o dado, não é decorativa: o RT corrige um CAS
    # errado ("134363-67-7", que falha o dígito verificador) para o oficial.
    candidato = (
        BlocoVerbatim(
            faixa="1 - 15", membros=(MembroVerbatim(cas="134363-67-7", nome="Dióxido de Titânio"),)
        ),
    )
    texto_candidato = serializar_verbatim(candidato)
    assert '"134363-67-7"' in texto_candidato

    texto_revisado = texto_candidato.replace("134363-67-7", "13463-67-7")
    revisado = desserializar_verbatim(texto_revisado)

    assert revisado[0].membros[0].cas == "13463-67-7"
    assert revisado != candidato
