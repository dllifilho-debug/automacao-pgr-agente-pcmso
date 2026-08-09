"""Materializa `.streamlit/secrets.toml` a partir de variáveis de ambiente,
antes do `streamlit run` (D-ARQ-76 cláusula 4). Sem o bloco `[auth]`,
`app_matriz.py` quebra com `AttributeError` na primeira linha executável
sem dizer o motivo — este módulo falha explicito antes disso.
"""

from __future__ import annotations

import os
import sys
from collections.abc import Mapping
from pathlib import Path

_VARIAVEIS = (
    "PCMSO_OIDC_CLIENT_ID",
    "PCMSO_OIDC_CLIENT_SECRET",
    "PCMSO_COOKIE_SECRET",
    "PCMSO_REDIRECT_URI",
)

_SERVER_METADATA_URL = "https://accounts.google.com/.well-known/openid-configuration"


class SegredoInvalido(Exception):
    pass


def gerar_toml_auth(valores: Mapping[str, str]) -> str:
    for nome in _VARIAVEIS:
        valor = valores.get(nome)
        if not valor:
            raise SegredoInvalido(f"variável obrigatória ausente ou vazia: {nome}")
        if '"' in valor or "\n" in valor:
            raise SegredoInvalido(
                f"variável {nome} contém aspas duplas ou quebra de linha"
            )

    return (
        "[auth]\n"
        f'redirect_uri = "{valores["PCMSO_REDIRECT_URI"]}"\n'
        f'cookie_secret = "{valores["PCMSO_COOKIE_SECRET"]}"\n'
        f'client_id = "{valores["PCMSO_OIDC_CLIENT_ID"]}"\n'
        f'client_secret = "{valores["PCMSO_OIDC_CLIENT_SECRET"]}"\n'
        f'server_metadata_url = "{_SERVER_METADATA_URL}"\n'
    )


def main() -> int:
    valores = {nome: os.environ.get(nome, "") for nome in _VARIAVEIS}
    try:
        texto = gerar_toml_auth(valores)
    except SegredoInvalido as erro:
        print(str(erro), file=sys.stderr)
        return 1

    destino = Path(".streamlit/secrets.toml")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
