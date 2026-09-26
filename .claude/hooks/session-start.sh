#!/bin/bash
set -euo pipefail

# Ambiente de teste para sessão de Claude Code na web.
#
# Sem ele o container abre sem `pytest`, e a cláusula do CLAUDE.md — "nenhum
# prompt ou sessão dispensa a suíte", com o recorte "nunca zero" — fica sem
# instrumento. Medido em 10/09/2026: a sessão gastou instalação manual antes
# de conseguir rodar qualquer teste.
#
# Idempotente: `pip install` reinstala sem efeito e o pacote do LibreOffice é
# conferido por `dpkg -s` antes do `apt-get`.

if [ "${CLAUDE_CODE_REMOTE:-}" != "true" ]; then
  exit 0
fi

# `set -u` mata o hook se `CLAUDE_PROJECT_DIR` não vier — e um hook que morre
# abre a sessão sem ambiente em silêncio, que é o modo de falha que este
# arquivo existe para eliminar. O fallback deriva a raiz da posição do próprio
# script (`.claude/hooks/` → dois níveis acima).
cd "${CLAUDE_PROJECT_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)}"

# O `cryptography` que vem do apt nesta imagem está sem `_cffi_backend`:
# `import pdfplumber` morre com `pyo3_runtime.PanicException` antes de chegar
# ao `pdfminer`. O pip considera o requisito satisfeito pela versão do apt e
# não a substitui, então a instalação precisa ser explícita e vir antes.
# `--ignore-installed`: sem ele o pip tenta desinstalar o pacote do apt e morre
# em "Cannot uninstall cryptography 41.0.7, RECORD file not found" — o hook
# inteiro abortava ali (`set -e`) e a sessão abria sem pytest nem streamlit
# (medido em 25/09/2026, branch feat/ui-matriz-etapas-20260925).
python -m pip install --quiet --timeout 120 --retries 5 --ignore-installed cffi cryptography

python -m pip install --quiet --timeout 120 --retries 5 -r requirements-dev.txt

# `scripts/varrer_acervo_lgpd.py::_texto_legado` converte `.doc`/`.rtf` por
# `soffice --headless`. A imagem traz o binário e não traz o filtro Writer, e
# essa combinação é a pior das três: `shutil.which("soffice")` acha o binário,
# o `skipif` dos testes não dispara, e a conversão falha em bloco — o modo que
# 003.FI mediu em 28 dos 83 arquivos.
if ! dpkg -s libreoffice-writer >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y -qq libreoffice-writer
fi
