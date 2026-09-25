from __future__ import annotations

import io
import json
from datetime import date
from typing import Any, TextIO

import pytest

from agente_medico.superficie.apresentacao import (
    ArtefatoIdaIlegivel,
    EmissaoFuturaError,
    carregar_artefato_ida,
    conduzir_revisao,
    ler_resposta,
    prompt_enter_mantem,
    validar_data_emissao,
)


def test_carregar_artefato_ida_json_invalido_levanta_erro() -> None:
    with pytest.raises(ArtefatoIdaIlegivel):
        carregar_artefato_ida("não é json", frozenset({"a"}))


def test_carregar_artefato_ida_nao_dict_levanta_erro() -> None:
    with pytest.raises(ArtefatoIdaIlegivel):
        carregar_artefato_ida(json.dumps([1, 2]), frozenset({"a"}))


def test_carregar_artefato_ida_campo_ausente_levanta_erro() -> None:
    with pytest.raises(ArtefatoIdaIlegivel):
        carregar_artefato_ida(json.dumps({"a": 1}), frozenset({"a", "b"}))


def test_ler_resposta_eof_levanta_eof_com_contexto_na_mensagem() -> None:
    entrada = io.StringIO("")
    with pytest.raises(EOFError, match="contexto-teste"):
        ler_resposta(entrada, "contexto-teste")


def test_prompt_enter_mantem_enter_retorna_valor_atual() -> None:
    entrada = io.StringIO("\n")
    saida = io.StringIO()

    resultado = prompt_enter_mantem("Rótulo", "atual", "contexto-teste", entrada, saida)

    assert resultado == "atual"
    assert "Rótulo [Enter mantém: atual]: " in saida.getvalue()


def test_prompt_enter_mantem_resposta_retorna_resposta() -> None:
    entrada = io.StringIO("novo valor\n")
    saida = io.StringIO()

    resultado = prompt_enter_mantem("Rótulo", "atual", "contexto-teste", entrada, saida)

    assert resultado == "novo valor"


def test_conduzir_revisao_self_check_e_chamado_com_a_volta_serializada() -> None:
    chamadas: list[str] = []

    def revisar(dados: dict[str, Any], entrada: TextIO, saida: TextIO) -> dict[str, Any]:
        dados["b"] = "editado"
        return dados

    def self_check(volta: str) -> None:
        chamadas.append(volta)

    ida = json.dumps({"a": 1, "b": "original"})
    volta = conduzir_revisao(
        ida, frozenset({"a", "b"}), revisar, self_check, io.StringIO(), io.StringIO()
    )

    assert chamadas == [volta]
    assert json.loads(volta) == {"a": 1, "b": "editado"}


def test_validar_data_emissao_recusa_futuro_e_aceita_hoje() -> None:
    # Reversões que matam: (1) tirar a checagem `emissao > hoje` — o vencimento
    # digitado passaria e R-PGR-06 não dispararia; (2) trocar `>` por `>=` — a
    # emissão de hoje seria recusada.
    hoje = date(2026, 9, 25)
    with pytest.raises(EmissaoFuturaError):
        validar_data_emissao("2026-09-26", hoje)
    assert validar_data_emissao("2026-09-25", hoje) == hoje
