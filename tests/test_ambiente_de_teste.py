"""Testes do ambiente de teste versionado — cada teste carrega, junto, a
reversão que deve deixá-lo vermelho.

Origem medida (10/09/2026): o container de sessão remota abria sem `pytest`,
`mypy` nem `coverage`, e nenhum arquivo do repositório os declarava; o binário
`soffice` estava presente e o filtro Writer não, combinação que faz o `skipif`
de `tests/test_varrer_acervo_lgpd.py` não disparar e a conversão falhar em
bloco. A cláusula "nenhum prompt ou sessão dispensa a suíte" ficava sem
instrumento.

O que estes testes NÃO fazem: repetir a lista de `requirements-dev.txt`. Um
teste que só reafirme o conteúdo do manifesto é checagem de sintaxe, não
verificação. Cada asserção abaixo deriva o esperado de outra fonte do
repositório — o `CLAUDE.md` para os comandos padrão, a varredura de `tests/` e
`scripts/` para as ferramentas geradas em subprocesso, e o próprio hook para o
que a sessão instala.

Os pisos de `types-PyYAML` e `types-requests` ficam declarados no manifesto sem
teste próprio, deliberadamente: a reversão que os mataria exige rodar
`mypy --strict` seguindo imports transitivos para fora do alvo canônico
(`adaptadores/transcritor_gemini.py` não está no alvo e é quem importa
`requests`). Teste cuja reversão não é nomeável não entra.
"""

from __future__ import annotations

import json
import re
import stat
import subprocess
from pathlib import Path

_RAIZ = Path(__file__).resolve().parents[1]
_MANIFESTO = _RAIZ / "requirements-dev.txt"
_HOOK = _RAIZ / ".claude" / "hooks" / "session-start.sh"
_SETTINGS = _RAIZ / ".claude" / "settings.json"

# Módulos de primeira parte: aparecem como `python -m ...` no CLAUDE.md mas são
# código deste repositório, não distribuição a declarar.
_PRIMEIRA_PARTE = ("scripts.", "agente_medico")

# Nome de import → nome de distribuição, quando divergem. Identidade é o padrão.
_MAPA_IMPORT_PARA_DISTRIBUICAO: dict[str, str] = {}


def _normalizar(nome: str) -> str:
    return re.sub(r"[-_.]+", "-", nome).lower()


def _distribuicao(modulo: str) -> str:
    return _MAPA_IMPORT_PARA_DISTRIBUICAO.get(modulo, modulo)


def _declaradas() -> set[str]:
    declaradas: set[str] = set()
    for linha in _MANIFESTO.read_text(encoding="utf-8").splitlines():
        linha = linha.split("#", 1)[0].strip()
        if not linha or linha.startswith("-"):
            continue
        corte = len(linha)
        for separador in (">=", "==", "<", "~", "!", "[", " "):
            posicao = linha.find(separador)
            if posicao != -1:
                corte = min(corte, posicao)
        nome = linha[:corte].strip()
        if nome:
            declaradas.add(_normalizar(nome))
    return declaradas


def _ferramentas_dos_comandos_padrao() -> set[str]:
    texto = (_RAIZ / "CLAUDE.md").read_text(encoding="utf-8")
    achadas = set(re.findall(r"python -m ([A-Za-z_][A-Za-z0-9_.]*)", texto))
    return {
        modulo
        for modulo in achadas
        if not modulo.startswith(_PRIMEIRA_PARTE)
    }


def _ferramentas_geradas_em_subprocesso() -> set[str]:
    """Varre `tests/` e `scripts/` por `"-m", "<ferramenta>"` em lista de
    subprocesso. O `-m` usado como flag (`coverage report -m --include=...`) não
    casa porque o token seguinte começa com `-`."""
    padrao = re.compile(r'"-m",\s*"([A-Za-z_][A-Za-z0-9_.]*)"')
    achadas: set[str] = set()
    for pasta in ("tests", "scripts"):
        for arquivo in (_RAIZ / pasta).glob("**/*.py"):
            if arquivo.resolve() == Path(__file__).resolve():
                continue
            achadas.update(padrao.findall(arquivo.read_text(encoding="utf-8")))
    return {modulo for modulo in achadas if not modulo.startswith(_PRIMEIRA_PARTE)}


def test_comando_padrao_do_claude_md_tem_ferramenta_declarada() -> None:
    """R1 — apagar a linha `mypy` de `requirements-dev.txt` mata este teste."""
    ferramentas = _ferramentas_dos_comandos_padrao()
    assert ferramentas, "nenhum `python -m` encontrado no CLAUDE.md — varredura quebrou"
    declaradas = _declaradas()
    faltando = {
        modulo
        for modulo in ferramentas
        if _normalizar(_distribuicao(modulo)) not in declaradas
    }
    assert not faltando, (
        f"comando padrão do CLAUDE.md invoca {faltando}, não declarado em "
        f"requirements-dev.txt"
    )


def test_ferramenta_gerada_em_subprocesso_esta_declarada() -> None:
    """R2 — apagar a linha `coverage` de `requirements-dev.txt` mata este teste."""
    ferramentas = _ferramentas_geradas_em_subprocesso()
    assert "coverage" in ferramentas, (
        "a varredura não achou o `python -m coverage` do portão de cobertura — "
        "instrumento quebrado, não ambiente limpo"
    )
    declaradas = _declaradas()
    faltando = {
        modulo
        for modulo in ferramentas
        if _normalizar(_distribuicao(modulo)) not in declaradas
    }
    assert not faltando, (
        f"a suíte gera {faltando} em subprocesso, não declarado em "
        f"requirements-dev.txt"
    )


def test_ambiente_de_teste_inclui_o_do_app() -> None:
    """R3 — apagar a linha `-r requirements.txt` de `requirements-dev.txt` mata
    este teste. Sem ela o ambiente de teste deixa de ser superconjunto do ambiente
    do app, e a suíte roda contra dependências que o deploy não tem."""
    linhas = [
        linha.split("#", 1)[0].strip()
        for linha in _MANIFESTO.read_text(encoding="utf-8").splitlines()
    ]
    assert "-r requirements.txt" in linhas, (
        "requirements-dev.txt não inclui requirements.txt"
    )


def _linhas_de_comando(prefixo: str) -> list[str]:
    """Linhas executáveis do hook que invocam `prefixo`. Comentário não conta —
    citar a dependência em prosa não a instala."""
    linhas: list[str] = []
    for linha in _HOOK.read_text(encoding="utf-8").splitlines():
        sem_comentario = linha.split("#", 1)[0]
        if prefixo in sem_comentario:
            linhas.append(sem_comentario)
    return linhas


def test_hook_de_sessao_instala_o_manifesto_de_desenvolvimento() -> None:
    """R4 — apagar do hook a linha que instala `requirements-dev.txt` mata este
    teste."""
    instalacoes = _linhas_de_comando("pip install")
    assert any("requirements-dev.txt" in linha for linha in instalacoes), (
        f"nenhum `pip install` do hook instala requirements-dev.txt: {instalacoes}"
    )


def test_hook_de_sessao_instala_o_filtro_writer_do_extrator_legado() -> None:
    """R5 — apagar `libreoffice-writer` do hook mata este teste.

    `scripts/varrer_acervo_lgpd.py::_texto_legado` converte `.doc`/`.rtf` por
    `soffice --headless` e o pacote do filtro Writer é separado do binário. Com
    binário presente e filtro ausente, `shutil.which("soffice")` acha o binário,
    o `skipif` de `tests/test_varrer_acervo_lgpd.py` não dispara e a conversão
    falha em bloco — o modo que 003.FI mediu em 28 dos 83 arquivos.
    """
    instalacoes = _linhas_de_comando("apt-get install")
    assert any("libreoffice-writer" in linha for linha in instalacoes), (
        f"nenhum `apt-get install` do hook instala libreoffice-writer: {instalacoes}"
    )


def test_hook_esta_registrado_e_executavel() -> None:
    """R6 — apagar a entrada `SessionStart` de `.claude/settings.json` mata este
    teste. Hook versionado que o harness não invoca é instrumento fora do git com
    outro nome."""
    settings = json.loads(_SETTINGS.read_text(encoding="utf-8"))
    comandos = [
        gancho["command"]
        for entrada in settings.get("hooks", {}).get("SessionStart", [])
        for gancho in entrada.get("hooks", [])
        if gancho.get("type") == "command"
    ]
    assert comandos, ".claude/settings.json não registra hook de SessionStart"

    relativo = _HOOK.relative_to(_RAIZ).as_posix()
    assert any(relativo in comando for comando in comandos), (
        f"o SessionStart registrado não aponta para {relativo}: {comandos}"
    )
    assert _HOOK.exists(), f"{relativo} registrado mas ausente"
    assert _HOOK.stat().st_mode & stat.S_IXUSR, f"{relativo} não é executável"


def test_hook_e_settings_nao_estao_ignorados_pelo_git() -> None:
    """R7 — apagar `!.claude/hooks/` ou `!.claude/settings.json` do `.gitignore`
    mata este teste.

    O `.gitignore` traz `.claude/*` com exceção para `skills/`; sem exceção
    própria, o hook e o `settings.json` que o registra ficam fora do git — o
    ambiente volta a existir só no container de quem o montou. É `DH-003EG-02`
    de novo, com outro instrumento: versionar o hook e deixá-lo ignorado não
    versiona nada.
    """
    for caminho in (_HOOK, _SETTINGS):
        relativo = caminho.relative_to(_RAIZ).as_posix()
        resultado = subprocess.run(
            ["git", "check-ignore", "-q", relativo],
            cwd=_RAIZ,
            capture_output=True,
        )
        assert resultado.returncode != 0, (
            f"{relativo} está ignorado pelo .gitignore — instrumento fora do git"
        )


def test_hook_instala_cryptography_por_cima_do_pacote_do_apt() -> None:
    """R8 — tirar `--ignore-installed` da instalação de `cryptography` no hook
    mata este teste.

    O `cryptography` do apt nesta imagem não tem arquivo RECORD, e o pip, sem a
    flag, tenta desinstalá-lo antes de instalar: "Cannot uninstall cryptography
    41.0.7, RECORD file not found". Com `set -e` o hook aborta nessa linha, e a
    sessão abre sem pytest nem streamlit (medido em 25/09/2026).
    """
    instalacoes = [
        linha for linha in _linhas_de_comando("pip install") if "cryptography" in linha.split()
    ]
    assert instalacoes, "nenhum `pip install` do hook instala cryptography"
    assert all("--ignore-installed" in linha.split() for linha in instalacoes), (
        f"`pip install` de cryptography sem --ignore-installed: {instalacoes}"
    )
