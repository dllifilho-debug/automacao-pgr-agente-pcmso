"""Guarda os artefatos de deploy (003.ET) — Dockerfile, materializar_secrets.py
e entrypoint.sh. Casos Python puro; nenhum executa shell (o host de CI é
Windows/PowerShell, sem bash)."""

from __future__ import annotations

from pathlib import Path

import pytest
import toml  # type: ignore[import-untyped]

from agente_medico.superficie.materializar_secrets import (
    SegredoInvalido,
    gerar_toml_auth,
)

_RAIZ = Path(__file__).parent.parent
_DOCKERFILE = _RAIZ / "Dockerfile"
_ENTRYPOINT = _RAIZ / "entrypoint.sh"
_CONFIG_STREAMLIT = _RAIZ / ".streamlit" / "config.toml"

_VALORES_TESTE = {
    "PCMSO_OIDC_CLIENT_ID": "id-de-teste",
    "PCMSO_OIDC_CLIENT_SECRET": "segredo-de-teste",
    "PCMSO_COOKIE_SECRET": "cookie-de-teste",
    "PCMSO_REDIRECT_URI": "https://exemplo.example/oauth2callback",
}


def _tokens_por_linha(texto: str) -> list[list[str]]:
    return [linha.split() for linha in texto.splitlines()]


def test_dockerfile_instala_o_requirements_do_app_nao_o_do_legado() -> None:
    texto = _DOCKERFILE.read_text(encoding="utf-8")
    assert texto.strip(), "Dockerfile vazio"

    linhas = _tokens_por_linha(texto)
    assert any("requirements.txt" in tokens for tokens in linhas)
    assert not any("requirements-legado.txt" in tokens for tokens in linhas)


def test_toml_gerado_tem_as_cinco_chaves_do_bloco_auth() -> None:
    texto = gerar_toml_auth(_VALORES_TESTE)

    assert texto.startswith("[auth]")
    for chave in (
        "redirect_uri",
        "cookie_secret",
        "client_id",
        "client_secret",
        "server_metadata_url",
    ):
        assert f"{chave} = " in texto
    for valor in _VALORES_TESTE.values():
        assert valor in texto


@pytest.mark.parametrize("valor_cookie_secret", [None, ""])
def test_variavel_ausente_ou_vazia_levanta_erro_nomeando_qual(
    valor_cookie_secret: str | None,
) -> None:
    valores = dict(_VALORES_TESTE)
    if valor_cookie_secret is None:
        del valores["PCMSO_COOKIE_SECRET"]
    else:
        valores["PCMSO_COOKIE_SECRET"] = valor_cookie_secret

    with pytest.raises(SegredoInvalido, match="PCMSO_COOKIE_SECRET"):
        gerar_toml_auth(valores)


def test_valor_com_aspas_duplas_nao_produz_toml_quebrado() -> None:
    valores = dict(_VALORES_TESTE)
    valores["PCMSO_REDIRECT_URI"] = 'https://exemplo.example/"; client_id = "forjado'

    with pytest.raises(SegredoInvalido):
        gerar_toml_auth(valores)


def test_entrypoint_de_producao_nao_usa_o_entrypoint_local() -> None:
    texto = _ENTRYPOINT.read_text(encoding="utf-8")
    assert "app_matriz.py" in texto
    assert "app_matriz_local.py" not in texto


def test_entrypoint_materializa_segredo_antes_do_streamlit_run() -> None:
    linhas = _ENTRYPOINT.read_text(encoding="utf-8").splitlines()

    linha_materializador = next(
        i for i, linha in enumerate(linhas) if "materializar_secrets" in linha
    )
    linha_streamlit = next(
        i for i, linha in enumerate(linhas) if "streamlit run" in linha
    )

    assert linha_materializador < linha_streamlit
    assert "exec" in linhas[linha_streamlit]
    assert "PORT" in linhas[linha_streamlit]


def test_dockerfile_copia_a_pasta_static() -> None:
    # Reversão que mata: remover `COPY static/ ./static/` do Dockerfile — em
    # produção app/static/ responde 404 e o tema cai na fonte padrão sem erro.
    linhas = _tokens_por_linha(_DOCKERFILE.read_text(encoding="utf-8"))
    assert ["COPY", "static/", "./static/"] in linhas


def test_fonte_do_tema_e_servida_pelo_app_sem_terceiros() -> None:
    # Reversão que mata: voltar `font = "Inter:https://fonts.googleapis.com/..."`,
    # apontar o fontFaces para um arquivo que não existe em static/, desligar
    # enableStaticServing ou apagar a licença OFL que acompanha a fonte.
    # `toml`, não `tomllib`: é o parser que o próprio Streamlit usa no config.toml
    # (dependência dele desde a 1.56) e roda em Python 3.10, onde tomllib não existe.
    config = toml.loads(_CONFIG_STREAMLIT.read_text(encoding="utf-8"))
    tema = config["theme"]

    assert config["server"]["enableStaticServing"] is True
    for chave in ("font", "headingFont"):
        assert "://" not in tema[chave], f"{chave} carrega fonte de terceiro"
    faces = tema["fontFaces"]
    assert faces
    for face in faces:
        url = face["url"]
        assert url.startswith("app/static/"), url
        arquivo = _RAIZ / "static" / url.removeprefix("app/static/")
        assert arquivo.is_file(), arquivo
        assert (arquivo.parent / "LICENSE-Inter.txt").is_file()
