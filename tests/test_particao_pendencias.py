"""Testes da partição do §11 do PROTOCOLO para docs/PENDENCIAS_CLINICAS.md (003.ET fatia 0).

Cada caso tem reversão nomeada: caso A morre devolvendo qualquer header DT-/DH- ao
PROTOCOLO; caso B morre movendo um header R-* para PENDENCIAS_CLINICAS.md, discriminado
por dois caminhos — o piso do denominador de medir_cobertura_clinica() (perda cai abaixo
de 42; crescimento normal não quebra o teste) e a ausência de header R-* no arquivo novo."""

from __future__ import annotations

import re
from pathlib import Path

from scripts.medir_painel import medir_cobertura_clinica

_RAIZ = Path(__file__).resolve().parent.parent
_CAMINHO_PENDENCIAS = _RAIZ / "docs" / "PENDENCIAS_CLINICAS.md"
_CAMINHO_PROTOCOLO = _RAIZ / "docs" / "PROTOCOLO_AGENTE_MEDICO.md"
_REGEX_HEADER_DIVIDA = re.compile(r"^#{2,4}\s+((?:DT|DH)-\S+)", re.MULTILINE)
_REGEX_HEADER_REGRA = re.compile(r"^#{2,4}\s+R-[A-Z]+-[0-9]+\b", re.MULTILINE)


def test_dividas_todas_no_arquivo_novo_nenhuma_no_protocolo() -> None:
    ids_pendencias = set(_REGEX_HEADER_DIVIDA.findall(_CAMINHO_PENDENCIAS.read_text(encoding="utf-8")))
    ids_protocolo = set(_REGEX_HEADER_DIVIDA.findall(_CAMINHO_PROTOCOLO.read_text(encoding="utf-8")))

    assert ids_pendencias, "regex de header DT-/DH- não casou nada em PENDENCIAS_CLINICAS.md"
    assert ids_protocolo == set()


def test_particao_nao_moveu_regra_clinica() -> None:
    _, denominador = medir_cobertura_clinica()
    assert denominador >= 42

    ids_regra_pendencias = set(_REGEX_HEADER_REGRA.findall(_CAMINHO_PENDENCIAS.read_text(encoding="utf-8")))
    assert ids_regra_pendencias == set()
