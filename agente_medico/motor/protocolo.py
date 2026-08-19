from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class Vocabulario:
    agentes: dict[str, Any]
    cargos: dict[str, Any]
    exames: dict[str, Any]
    epis: dict[str, Any]
    fracoes_sem_agente: tuple[str, ...] = ()


@dataclass(frozen=True)
class Protocolo:
    vocabulario: Vocabulario
    predicados_compostos: dict[str, Any]
    regras: list[dict[str, Any]]
    regimes: dict[str, Any]


def _load_yaml(path: Path) -> Any:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _exigir_chave(data: Any, chave: str, origem: Path) -> Any:
    if not isinstance(data, dict) or chave not in data:
        raise ValueError(f"Chave raiz '{chave}' ausente em {origem}")
    return data[chave]


def carregar(diretorio: Path | str) -> Protocolo:
    raiz = Path(diretorio)
    vocab_dir = raiz / "vocabulario"
    regimes_dir = raiz / "regimes"

    if not raiz.exists():
        raise FileNotFoundError(f"Diretório não encontrado: {raiz}")
    if not vocab_dir.exists():
        raise FileNotFoundError(f"Diretório vocabulario ausente: {vocab_dir}")

    agentes_yaml = _load_yaml(vocab_dir / "agentes.yaml")
    vocabulario = Vocabulario(
        agentes=_exigir_chave(agentes_yaml, "agentes", vocab_dir / "agentes.yaml") or {},
        cargos=_exigir_chave(_load_yaml(vocab_dir / "cargos.yaml"), "cargos", vocab_dir / "cargos.yaml") or {},
        exames=_exigir_chave(_load_yaml(vocab_dir / "exames.yaml"), "exames", vocab_dir / "exames.yaml") or {},
        epis=_exigir_chave(_load_yaml(vocab_dir / "epis.yaml"), "epis", vocab_dir / "epis.yaml") or {},
        fracoes_sem_agente=tuple(agentes_yaml.get("fracoes_sem_agente") or ()),
    )

    pred_path = raiz / "predicados_compostos.yaml"
    predicados_compostos: dict[str, Any] = (
        _exigir_chave(_load_yaml(pred_path), "predicados_compostos", pred_path) or {}
    )

    regras_path = raiz / "regras.yaml"
    regras_raw = _exigir_chave(_load_yaml(regras_path), "regras", regras_path)
    # Regras marcadas status: DEPRECATED são excluídas do motor de avaliação.
    # Mantidas no YAML por contrato de ID e rastreabilidade histórica (PCMSO).
    regras: list[dict[str, Any]] = [
        r for r in (regras_raw or []) if r.get("status") != "DEPRECATED"
    ]

    regimes: dict[str, Any] = {}
    if regimes_dir.exists():
        for yaml_file in sorted(regimes_dir.glob("*.yaml")):
            regimes[yaml_file.stem] = _load_yaml(yaml_file) or {}

    _validar_exames_em_regras(vocabulario.exames, regras)

    return Protocolo(
        vocabulario=vocabulario,
        predicados_compostos=predicados_compostos,
        regras=regras,
        regimes=regimes,
    )


def _validar_exames_em_regras(
    exames: dict[str, Any], regras: list[dict[str, Any]]
) -> None:
    slugs = set(exames.keys())
    for regra in regras:
        regra_id = regra.get("id", "<sem id>")
        for item in regra.get("emite", []):
            slug = item["exame"]
            if slug not in slugs:
                slugs_disponiveis = sorted(slugs)
                raise ValueError(
                    f"Exame '{slug}' referenciado pela regra '{regra_id}' não existe no vocabulário.\n"
                    f"Slugs disponíveis: {slugs_disponiveis}"
                )
