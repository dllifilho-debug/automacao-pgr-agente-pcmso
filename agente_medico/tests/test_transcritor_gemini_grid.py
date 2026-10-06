from __future__ import annotations

import json
from typing import Any
from unittest.mock import Mock, patch

import pytest

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.adaptadores.transcritor_gemini_grid import TranscritorGeminiGrid
from agente_medico.motor.transcritor_grid import EntradaGrid

# Mesmo ponto de mock de test_transcritor_gemini_card.py: a cascata HTTP
# (_chamar_gemini) mora no adaptador FDS e é reusada por import.
_ALVO = "agente_medico.adaptadores.transcritor_gemini.requests.post"


def _resposta_200(texto: str) -> Mock:
    resp = Mock()
    resp.status_code = 200
    resp.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": texto}]}, "finishReason": "STOP"}]
    }
    return resp


def _ghe_json(nome: str) -> dict[str, Any]:
    return {
        "nome": nome,
        "cargos": [nome],
        "riscos": [{"agente": "RUÍDO CONTÍNUO OU INTERMITENTE", "quantificacao": "", "fonte_geradora": ""}],
    }


def _resposta_lote(nomes: list[str]) -> Mock:
    return _resposta_200(json.dumps([_ghe_json(n) for n in nomes]))


def _eco_do_lote(*args: Any, **kwargs: Any) -> Mock:
    """Responde a cada requisição com um GHE por grupo do prompt, lendo os
    nomes da linha "FUNÇÃO (como está no PDF):" — é o que um lote de
    tamanho qualquer precisa para sair com o comprimento certo."""
    prompt = kwargs["json"]["contents"][0]["parts"][0]["text"]
    nomes = [
        linha.split(": ", 1)[1]
        for linha in prompt.splitlines()
        if linha.startswith("FUNÇÃO (como está no PDF): ")
    ]
    return _resposta_lote(nomes)


def _prompt_da_chamada(mock_post: Mock, indice: int = 0) -> str:
    texto: str = mock_post.call_args_list[indice].kwargs["json"]["contents"][0]["parts"][0]["text"]
    return texto


def test_prompt_traz_o_nome_verbatim_e_as_linhas_de_cada_grupo_na_ordem() -> None:
    # Reversão que mata: _montar_prompt_lote sem a linha "FUNÇÃO (como está
    # no PDF): ..." — o LLM perde o nome lido da coluna Função, que não
    # está nas LINHAS.
    entradas = [
        EntradaGrid("CARPINTEIR O", "RUÍDO CONTÍNUO OU\nINTERMITENTE"),
        EntradaGrid("VIGIA DIURNO/ VIGIA NOTURNO", "UMIDADE"),
    ]
    with patch(_ALVO, return_value=_resposta_lote(["CARPINTEIRO", "VIGIA DIURNO/ VIGIA NOTURNO"])) as post:
        ghes = TranscritorGeminiGrid(chave="fake").transcrever_lote(entradas)
    prompt = _prompt_da_chamada(post)
    assert (
        "--- GRUPO 1 ---\nFUNÇÃO (como está no PDF): CARPINTEIR O\nLINHAS:\nRUÍDO CONTÍNUO OU\nINTERMITENTE" in prompt
    )
    assert "--- GRUPO 2 ---\nFUNÇÃO (como está no PDF): VIGIA DIURNO/ VIGIA NOTURNO\nLINHAS:\nUMIDADE" in prompt
    assert [g.nome for g in ghes] == ["CARPINTEIRO", "VIGIA DIURNO/ VIGIA NOTURNO"]


def test_oito_grupos_viram_duas_requisicoes_e_saem_na_ordem() -> None:
    # Lote de 6 (D-ARQ-80: o gargalo do nível gratuito é requisição).
    # Reversão que mata: mandar todas as entradas numa requisição só, sem
    # fatiar por _GRUPOS_POR_LOTE. Os lotes vão em paralelo, então a ordem das
    # chamadas HTTP não é fixa — a do resultado é.
    entradas = [EntradaGrid(f"FUNCAO {i}", "RUÍDO") for i in range(8)]
    with patch(_ALVO, side_effect=_eco_do_lote) as post:
        ghes = TranscritorGeminiGrid(chave="fake").transcrever_lote(entradas)
    assert post.call_count == 2
    prompts = [_prompt_da_chamada(post, i) for i in range(2)]
    (segundo,) = [p for p in prompts if "FUNÇÃO (como está no PDF): FUNCAO 6" in p]
    assert "FUNÇÃO (como está no PDF): FUNCAO 5" not in segundo
    assert [g.nome for g in ghes] == [f"FUNCAO {i}" for i in range(8)]


def test_json_cortado_na_primeira_chamada_e_retentado_uma_vez() -> None:
    # Reversão que mata: _TENTATIVAS_LOTE = 1 — o JSON cortado vira
    # TranscricaoIndisponivel sem a 2ª chamada.
    respostas = [_resposta_200('[{"nome": "PINTOR", "cargos": ['), _resposta_lote(["PINTOR"])]
    with patch(_ALVO, side_effect=respostas) as post:
        (ghe,) = TranscritorGeminiGrid(chave="fake").transcrever_lote([EntradaGrid("PINTOR", "UMIDADE")])
    assert post.call_count == 2
    assert ghe.nome == "PINTOR"


def test_sem_chave_levanta_sem_chamar_http() -> None:
    # Reversão que mata: tirar a guarda `if not chave` — a requisição sai
    # com chave vazia.
    with patch(_ALVO, return_value=_resposta_lote(["PINTOR"])) as post:
        with pytest.raises(TranscricaoIndisponivel, match="CHAVE_API_GOOGLE"):
            TranscritorGeminiGrid(chave="").transcrever_lote([EntradaGrid("PINTOR", "UMIDADE")])
    assert post.call_count == 0
