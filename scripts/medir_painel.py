"""Medidor dos 3 números da Camada 2 do PAINEL_ESTADO.md, direto do disco.

Replica o método ali descrito: `git grep` de IDs de regra (`R-[A-Z]+-[0-9]+`,
família colapsada — `R-RX-01-adm` conta como `R-RX-01`) mede rastreabilidade
(string presente em `regras.yaml`/`motor/**/*.py`), não consumo em runtime;
é piso de rastreabilidade, não teto de função executada.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import yaml

_RAIZ = Path(__file__).resolve().parent.parent
_REGEX_ID = re.compile(r"R-[A-Z]+-[0-9]+")
_REGEX_HEADER_ID = re.compile(r"^(#{2,4}\s+(R-[A-Z]+-[0-9]+)\b.*)$", re.MULTILINE)

_CAMINHO_PROTOCOLO = _RAIZ / "docs" / "PROTOCOLO_AGENTE_MEDICO.md"
_CAMINHO_REGRAS = _RAIZ / "agente_medico" / "protocolo" / "regras.yaml"
_CAMINHO_AGENTES = _RAIZ / "agente_medico" / "protocolo" / "vocabulario" / "agentes.yaml"
_DIR_MOTOR = _RAIZ / "agente_medico" / "motor"


def _ids_ativos_protocolo() -> set[str]:
    # Header = status: o ID conta como ativo sse existir um header (##-####)
    # cujo próprio sujeito (token logo após os #s) é o ID e a linha não
    # contém "DEPRECATED". Menção ao ID em prosa de outro header (ex. uma
    # DT que só cita o ID no título) não conta.
    texto = _CAMINHO_PROTOCOLO.read_text(encoding="utf-8")
    ativos: set[str] = set()
    for linha, id_ in _REGEX_HEADER_ID.findall(texto):
        if "DEPRECATED" not in linha:
            ativos.add(id_)
    return ativos


def medir_cobertura_clinica() -> tuple[int, int]:
    ativos = _ids_ativos_protocolo()
    ids_codigo = set(_REGEX_ID.findall(_CAMINHO_REGRAS.read_text(encoding="utf-8")))
    for caminho in _DIR_MOTOR.rglob("*.py"):
        ids_codigo |= set(_REGEX_ID.findall(caminho.read_text(encoding="utf-8")))
    return len(ativos & ids_codigo), len(ativos)


def medir_cas() -> tuple[int, int]:
    dados = yaml.safe_load(_CAMINHO_AGENTES.read_text(encoding="utf-8"))
    agentes = dados["agentes"]
    populados = sum(1 for valores in agentes.values() if valores.get("cas") is not None)
    return populados, len(agentes)


def medir_suite() -> tuple[int, int]:
    resultado = subprocess.run(
        [sys.executable, "-m", "pytest", "agente_medico/tests/", "tests/", "-q", "--tb=no"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
    )
    contagens = {
        palavra: int(numero)
        for numero, palavra in re.findall(r"(\d+) (passed|failed|skipped|error)", resultado.stdout)
    }
    if not contagens:
        raise RuntimeError(f"saída do pytest não reconhecida:\n{resultado.stdout}")
    if resultado.returncode != 0:
        raise RuntimeError(
            f"suite vermelha (returncode {resultado.returncode}): "
            f"{contagens.get('failed', 0)} failed, {contagens.get('error', 0)} error, "
            f"{contagens.get('passed', 0)} passed, {contagens.get('skipped', 0)} skipped\n"
            f"{resultado.stdout[-2000:]}"
        )
    return contagens.get("passed", 0), contagens.get("skipped", 0)


def _baseline() -> str:
    resultado = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
        check=True,
    )
    return resultado.stdout.strip()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--suite", action="store_true")
    args = parser.parse_args()

    print(f"baseline: {_baseline()}")

    numerador_regras, denominador_regras = medir_cobertura_clinica()
    percentual_regras = 100 * numerador_regras / denominador_regras
    print(f"regras: {numerador_regras}/{denominador_regras} ativas ({percentual_regras:.0f}%)")

    numerador_cas, denominador_cas = medir_cas()
    percentual_cas = 100 * numerador_cas / denominador_cas
    print(f"cas: {numerador_cas}/{denominador_cas} slugs ({percentual_cas:.0f}%)")

    if args.suite:
        passed, skipped = medir_suite()
        print(f"suite: {passed} passed, {skipped} skipped")
    else:
        print("suite: não medida (use --suite)")


if __name__ == "__main__":
    main()
