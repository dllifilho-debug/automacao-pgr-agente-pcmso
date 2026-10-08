"""Rótulo de nível de risco escrito no PGR → posição em relação ao corte "moderado ou
acima" (D-ARQ-95), pelo vocabulário `niveis_risco.yaml`. Só a sugestão do ASO usa; o
`nivel_risco` da escala P×S, que o motor de emissão lê, não passa por aqui."""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Mapping
from typing import Any, Literal, NamedTuple

PosicaoNivel = Literal["abaixo", "corte"]


class NivelPGR(NamedTuple):
    rotulo: str
    posicao: PosicaoNivel


def _normalizar(texto: str) -> str:
    sem_acento = "".join(c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento.upper())


def classificar_nivel_pgr(texto: str, niveis: Mapping[str, Any]) -> NivelPGR | None:
    """Acha os rótulos do vocabulário no texto, do mais longo ao mais curto, sem deixar
    um rótulo casar dentro de outro já achado ("MUITO ALTO" não conta também "ALTO";
    "NÃO TOLERÁVEL" não conta "TOLERÁVEL"). Nenhum rótulo, ou rótulos em posições
    diferentes no mesmo texto: None — a sugestão sai conferir, nunca adivinha."""
    resto = _normalizar(texto)
    achados: list[tuple[int, str, PosicaoNivel]] = []
    for rotulo in sorted(niveis, key=len, reverse=True):
        padrao = re.compile(rf"\b{re.escape(_normalizar(rotulo))}\b")
        for m in padrao.finditer(resto):
            achados.append((m.start(), rotulo, niveis[rotulo]["posicao"]))
        resto = padrao.sub(lambda m: " " * len(m.group(0)), resto)
    if not achados or len({posicao for _, _, posicao in achados}) > 1:
        return None
    _, rotulo, posicao = min(achados)
    return NivelPGR(rotulo, posicao)
