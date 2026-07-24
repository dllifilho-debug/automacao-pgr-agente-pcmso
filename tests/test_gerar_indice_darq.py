"""Testes de scripts/gerar_indice_darq.py — importam gerar_indice() direto
(sem subprocess); pisos, não valores exatos onde o número cresce."""

from __future__ import annotations

import re

from scripts.gerar_indice_darq import _CAMINHO_DECISOES, _CAMINHO_INDICE, gerar_indice

_TEXTO_DECISOES = _CAMINHO_DECISOES.read_text(encoding="utf-8")


def test_indice_em_disco_nao_divergiu() -> None:
    assert gerar_indice() == _CAMINHO_INDICE.read_text(encoding="utf-8")


def test_todo_header_darq_entrou() -> None:
    fim_historico = re.search(r"^## Histórico de revisões$", _TEXTO_DECISOES, re.MULTILINE)
    limite = fim_historico.start() if fim_historico is not None else len(_TEXTO_DECISOES)
    texto_antes_historico = _TEXTO_DECISOES[:limite]
    headers = re.findall(r"^## D-ARQ-\d+ — ", texto_antes_historico, re.MULTILINE)

    linhas_dados = [
        linha for linha in gerar_indice().splitlines() if linha.startswith("| D-ARQ-")
    ]
    assert len(linhas_dados) == len(headers)


def test_piso_de_decisoes() -> None:
    linhas_dados = [
        linha for linha in gerar_indice().splitlines() if linha.startswith("| D-ARQ-")
    ]
    assert len(linhas_dados) >= 62


def test_ids_sem_buraco_nem_duplicata() -> None:
    ids = re.findall(r"^\| (D-ARQ-\d+) \|", gerar_indice(), re.MULTILINE)
    assert len(ids) == len(set(ids))


def test_historico_de_revisoes_nao_virou_decisao() -> None:
    assert "Histórico de revisões" not in gerar_indice()
