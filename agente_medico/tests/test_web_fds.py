from __future__ import annotations

import json

from streamlit.testing.v1 import AppTest

from agente_medico.motor.revisao_verbatim import desserializar_verbatim, serializar_verbatim
from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim
from agente_medico.superficie.web_fds import montar_volta_verbatim, pagina_fds
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
        membros=(MembroVerbatim(cas="1336-21-6", nome="Hidróxido de amônia"),),
    ),
)


def test_montar_volta_verbatim_mantem_tudo_roundtrip() -> None:
    blocos = tinta_acrilica_verbatim()
    ida = serializar_verbatim(blocos)
    dados = json.loads(ida)

    blocos_revisados = [
        {
            "faixa": bloco["faixa"],
            "membros": [
                {"cas": m["cas"], "nome": m["nome"], "frases_h": m["frases_h"]}
                for m in bloco["membros"]
            ],
        }
        for bloco in dados["blocos"]
    ]

    volta = montar_volta_verbatim(dados, blocos_revisados)
    revisado = desserializar_verbatim(volta)

    assert revisado == blocos


def test_montar_volta_verbatim_edicao_e_remocao_refletidas() -> None:
    ida = serializar_verbatim(_BLOCOS_PADRAO)
    dados = json.loads(ida)

    blocos_revisados = [
        {
            "faixa": dados["blocos"][0]["faixa"],
            "membros": [
                {"cas": "13463-67-7", "nome": "Dióxido de Titânio", "frases_h": []},
            ],
        },
        {
            "faixa": dados["blocos"][1]["faixa"],
            "membros": [
                {
                    "cas": m["cas"],
                    "nome": m["nome"],
                    "frases_h": m["frases_h"],
                }
                for m in dados["blocos"][1]["membros"]
            ],
        },
    ]

    volta = montar_volta_verbatim(dados, blocos_revisados)
    revisado = desserializar_verbatim(volta)

    assert revisado[0].membros == (MembroVerbatim(cas="13463-67-7", nome="Dióxido de Titânio"),)
    assert revisado[1] == _BLOCOS_PADRAO[1]


def test_pagina_fds_fluxo_mantem_tudo() -> None:
    at = AppTest.from_function(pagina_fds)
    at.run()

    ida = serializar_verbatim(_BLOCOS_PADRAO)
    at.text_area[0].set_value(ida).run()
    at.button[0].click().run()

    assert not at.exception
    assert at.code
    revisado = desserializar_verbatim(at.code[0].value)
    assert revisado == _BLOCOS_PADRAO


def test_pagina_fds_artefato_ilegivel_mostra_erro() -> None:
    at = AppTest.from_function(pagina_fds)
    at.run()

    at.text_area[0].set_value("não é json").run()

    assert not at.exception
    assert at.error
    assert not at.code
