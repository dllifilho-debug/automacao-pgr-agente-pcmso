from __future__ import annotations

from datetime import date

import pytest
from streamlit.testing.v1 import AppTest

from agente_medico.motor.revisao_envelope import desserializar_confirmacao, serializar_envelope
from agente_medico.motor.tipos import CandidataValidade, EnvelopeVerbatim
from agente_medico.superficie.web_envelope import montar_volta_envelope, pagina_envelope

_ENVELOPE_VIVERDE_GABARITO = EnvelopeVerbatim(
    validade_textos=("GOIÂNIA, FEVEREIRO 2023",),
    responsavel_tecnico="Fulano",
    titulo_rt="Engenheiro de Segurança",
    registro_profissional="CREA-GO 123",
)


def _ida_viverde() -> str:
    candidatas = (CandidataValidade(texto="GOIÂNIA, FEVEREIRO 2023", data=date(2023, 2, 1)),)
    return serializar_envelope(_ENVELOPE_VIVERDE_GABARITO, candidatas, proposta=date(2023, 2, 1))


def test_montar_volta_envelope_aceita_gabarito_viverde() -> None:
    ida = _ida_viverde()
    import json

    dados = json.loads(ida)

    volta = montar_volta_envelope(dados, "2023-02-01", True)
    confirmado = desserializar_confirmacao(volta)

    assert confirmado.validade == date(2023, 2, 1)
    assert confirmado.assinatura_engenheiro is True


def test_montar_volta_envelope_validade_nao_iso_levanta_erro() -> None:
    import json

    dados = json.loads(_ida_viverde())

    with pytest.raises(ValueError):
        montar_volta_envelope(dados, "31/12/2023", True)


def test_pagina_envelope_fluxo_feliz() -> None:
    at = AppTest.from_function(pagina_envelope)
    at.run()

    ida = _ida_viverde()
    at.text_area[0].set_value(ida).run()
    at.text_input[0].set_value("2023-02-01").run()
    at.radio[0].set_value("s").run()
    at.button[0].click().run()

    assert not at.exception
    assert at.code
    confirmado = desserializar_confirmacao(at.code[0].value)
    assert confirmado.validade == date(2023, 2, 1)
    assert confirmado.assinatura_engenheiro is True


def test_pagina_envelope_artefato_ilegivel_mostra_erro() -> None:
    at = AppTest.from_function(pagina_envelope)
    at.run()

    at.text_area[0].set_value("não é json").run()

    assert not at.exception
    assert at.error
    assert not at.code


def test_pagina_envelope_sem_assinatura_nao_emite() -> None:
    at = AppTest.from_function(pagina_envelope)
    at.run()

    ida = _ida_viverde()
    at.text_area[0].set_value(ida).run()
    at.text_input[0].set_value("2023-02-01").run()
    at.button[0].click().run()

    assert not at.exception
    assert at.error
    assert not at.code
