from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

from agente_medico.motor.tipos import NIVEIS_RISCO_PXS


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
    _validar_lt_nr15(vocabulario.agentes)
    _validar_mencao_documental(vocabulario.agentes, regras)

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


def _validar_lt_nr15(agentes: dict[str, Any]) -> None:
    """`lt_nr15` (D-ARQ-86 cl.5): LT da NR-15 por unidade, com fonte. Valor
    malformado viraria dispensa de exame por conta errada — falha no carregamento."""
    for slug, meta in agentes.items():
        lt = (meta or {}).get("lt_nr15")
        if lt is None:
            continue
        valores = [lt.get(c) for c in ("ppm", "mg_m3")] if isinstance(lt, dict) else []
        if (
            not isinstance(lt, dict)
            or not set(lt) <= {"ppm", "mg_m3", "fonte"}
            or not isinstance(lt.get("fonte"), str)
            or not any(v is not None for v in valores)
            or not all(v is None or (isinstance(v, (int, float)) and v > 0) for v in valores)
        ):
            raise ValueError(
                f"Agente '{slug}': lt_nr15 exige 'fonte' e ao menos um de 'ppm'/'mg_m3' "
                f"positivo, recebido {lt!r}"
            )


def _validar_mencao_documental(
    agentes: dict[str, Any], regras: list[dict[str, Any]]
) -> None:
    """`mencao_documental` (R-BIO-05) troca o exame por menção quando todo risco
    do agente vem com nível P×S listado — só faz sentido se `quando` é o próprio
    slug do agente, e só com níveis que o parser produz."""
    for regra in regras:
        mencao = regra.get("mencao_documental")
        if mencao is None:
            continue
        regra_id = regra.get("id", "<sem id>")
        if (
            not isinstance(mencao, dict)
            or not {"regra", "niveis_risco"} <= set(mencao)
            or not set(mencao) <= {"regra", "niveis_risco", "niveis_com_medicao_abaixo_acao"}
        ):
            raise ValueError(
                f"Regra '{regra_id}': mencao_documental exige as chaves 'regra' e "
                f"'niveis_risco' (e aceita 'niveis_com_medicao_abaixo_acao'), recebido {mencao!r}"
            )
        quando = regra.get("quando")
        if not isinstance(quando, str) or quando not in agentes:
            raise ValueError(
                f"Regra '{regra_id}': mencao_documental exige 'quando' igual a um slug "
                f"de agente do vocabulário, recebido {quando!r}"
            )
        for chave in ("niveis_risco", "niveis_com_medicao_abaixo_acao"):
            if chave not in mencao:
                continue
            niveis = mencao[chave]
            if not isinstance(niveis, list) or not niveis or not set(niveis) <= set(NIVEIS_RISCO_PXS):
                raise ValueError(
                    f"Regra '{regra_id}': {chave} deve ser lista não-vazia de "
                    f"{list(NIVEIS_RISCO_PXS)}, recebido {niveis!r}"
                )
        if "niveis_com_medicao_abaixo_acao" in mencao and not isinstance(
            agentes[quando].get("lt_nr15"), dict
        ):
            raise ValueError(
                f"Regra '{regra_id}': niveis_com_medicao_abaixo_acao exige 'lt_nr15' no "
                f"agente '{quando}' — sem LT não há nível de ação (D-ARQ-86 cl.5)"
            )
