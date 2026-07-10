from __future__ import annotations

import io

import pytest

from agente_medico.motor.revisao_verbatim import (
    desserializar_verbatim,
    montar_fds_revisado,
    serializar_verbatim,
)
from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim
from agente_medico.superficie.cli_fds import ArtefatoIdaIlegivel, revisar_verbatim
from agente_medico.tests.fixtures.fds_verbatim_t65 import tinta_acrilica_verbatim

_BLOCOS_PADRAO = (
    BlocoVerbatim(
        faixa="1 - 15",
        membros=(
            MembroVerbatim(cas="134363-67-\n7", nome="Dióxido de\nTitânio"),
            MembroVerbatim(cas="51274-00-1", nome="Óxido de Ferro Amarelo"),
        ),
    ),
    BlocoVerbatim(
        faixa="0,1 - 1",
        membros=(
            MembroVerbatim(cas="1336-21-6", nome="Hidróxido de amônia"),
            MembroVerbatim(cas="", nome="Segredo Industrial"),
            MembroVerbatim(cas="7128-64-5", nome="X"),
        ),
    ),
)


def _ida_padrao() -> str:
    return serializar_verbatim(_BLOCOS_PADRAO)


def test_enter_em_tudo_roundtrip_byte_exato() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\n\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos == _BLOCOS_PADRAO


def test_editar_cas_de_um_membro_so_ele_muda() -> None:
    ida = _ida_padrao()
    # bloco 1: faixa Enter; membro 1 "e" -> cas novo, Enter no nome; membro 2 Enter
    # bloco 2: faixa Enter; membros 1..3 Enter
    entrada = io.StringIO("\ne\n13463-67-7\n\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos[0].membros[0].cas == "13463-67-7"
    assert blocos[0].membros[0].nome == "Dióxido de\nTitânio"
    assert blocos[0].membros[1] == _BLOCOS_PADRAO[0].membros[1]
    assert blocos[1] == _BLOCOS_PADRAO[1]


def test_editar_nome_enter_no_cas_mantem_cas() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\ne\n\nDióxido de Titânio Corrigido\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos[0].membros[0].cas == "134363-67-\n7"
    assert blocos[0].membros[0].nome == "Dióxido de Titânio Corrigido"


def test_editar_faixa_de_um_bloco_so_ela_muda() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("2 - 20\n\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos[0].faixa == "2 - 20"
    assert blocos[0].membros == _BLOCOS_PADRAO[0].membros
    assert blocos[1] == _BLOCOS_PADRAO[1]


def test_remover_membro_ausente_na_volta_demais_intactos() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\nr\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos[0].membros == (_BLOCOS_PADRAO[0].membros[1],)
    assert blocos[1] == _BLOCOS_PADRAO[1]


def test_opcao_invalida_no_prompt_de_membro_reprompta() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\nx\n\n\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos == _BLOCOS_PADRAO
    assert "Opção inválida" in saida.getvalue()


def test_remocao_de_todos_os_membros_de_um_bloco_aceita_vazio() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\nr\nr\n\n\n\n\n")
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    blocos = desserializar_verbatim(volta)

    assert blocos[0].membros == ()
    assert blocos[1] == _BLOCOS_PADRAO[1]


def test_ida_json_invalido_levanta_erro() -> None:
    with pytest.raises(ArtefatoIdaIlegivel):
        revisar_verbatim("não é json", io.StringIO(), io.StringIO())


def test_ida_sem_blocos_ou_sem_versao_levanta_erro() -> None:
    import json

    with pytest.raises(ArtefatoIdaIlegivel):
        revisar_verbatim(json.dumps({"versao": 1}), io.StringIO(), io.StringIO())

    with pytest.raises(ArtefatoIdaIlegivel):
        revisar_verbatim(json.dumps({"blocos": []}), io.StringIO(), io.StringIO())


def test_eof_no_prompt_de_faixa_levanta_eof() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("")
    saida = io.StringIO()

    with pytest.raises(EOFError):
        revisar_verbatim(ida, entrada, saida)


def test_eof_no_prompt_de_membro_levanta_eof() -> None:
    ida = _ida_padrao()
    entrada = io.StringIO("\n")
    saida = io.StringIO()

    with pytest.raises(EOFError):
        revisar_verbatim(ida, entrada, saida)


def test_gabarito_tinta_acrilica_verbatim_fim_a_fim() -> None:
    blocos = tinta_acrilica_verbatim()
    ida = serializar_verbatim(blocos)
    entrada = io.StringIO("\n\n" * len(blocos))
    saida = io.StringIO()

    volta = revisar_verbatim(ida, entrada, saida)
    revisado = desserializar_verbatim(volta)
    assert revisado == blocos

    fds, _pendencias = montar_fds_revisado(revisado)

    assert fds.composicao_verbatim != ()
