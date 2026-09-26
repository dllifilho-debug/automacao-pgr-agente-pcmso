"""Portão de cobertura de `scripts/varrer_acervo_lgpd.py` (003.FJ).

**Por que este arquivo existe.** Duas rodadas seguidas do Gauntlet acharam a
mesma classe de defeito — ramo de código que nenhum teste alcança — em alvos
diferentes: os três ramos de falha de `varrer()` (5ª rodada) e dois dos três
ramos de `extrair_metadata_autoria` (6ª). Nos dois casos o número publicado em
`PENDENCIAS_CLINICAS.md` era reversível com a suíte verde, e nos dois casos a
detecção veio de fora. **Corrigir o caso nomeado não fecha a classe**; este
portão fecha.

Não é métrica de vaidade: 100% aqui significa que **toda linha do instrumento
que decide a cláusula de `DH-003FE-01` é executada por algum teste**. Linha
deliberadamente fora do alcance carrega `# pragma: no cover` com a razão
escrita ao lado, e a lista de pragmas é conferida abaixo — para que "excluir da
cobertura" seja decisão declarada, nunca silêncio.

Roda `coverage` em subprocesso porque medir cobertura de dentro de uma sessão
de `coverage` não é confiável.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_RAIZ = Path(__file__).resolve().parents[1]
_ALVO = _RAIZ / "scripts" / "varrer_acervo_lgpd.py"
_TESTES = _RAIZ / "tests" / "test_varrer_acervo_lgpd.py"

_PRAGMAS_ESPERADOS = {
    'if __name__ == "__main__":  # pragma: no cover — entrypoint; `main` e testada direto',
}


def test_pragmas_de_exclusao_sao_os_declarados() -> None:
    """Reversão que mata: acrescentar um `# pragma: no cover` novo ao script sem
    declará-lo aqui.

    Sem esta trava, o portão de 100% abaixo seria contornável pelo caminho mais
    barato — marcar como não-coberto o ramo que dá trabalho testar. A exclusão
    passa a exigir edição consciente de duas linhas, em dois arquivos.
    """
    linhas_com_pragma = {
        linha.strip()
        for linha in _ALVO.read_text("utf-8").splitlines()
        if "pragma: no cover" in linha
    }
    assert linhas_com_pragma == _PRAGMAS_ESPERADOS


@pytest.mark.skipif(shutil.which("soffice") is None, reason="ramo legado exige LibreOffice")
def test_instrumento_de_varredura_tem_cobertura_total() -> None:
    """Reversão que mata: apagar qualquer teste de
    `tests/test_varrer_acervo_lgpd.py` cuja remoção deixe uma linha do script
    sem execução — por exemplo `test_extrair_texto_le_pdf_de_verdade`, e o bloco
    de `_texto_pdf` fica descoberto.

    É o portão que as 5ª e 6ª rodadas do Gauntlet tornaram necessário: ele falha
    **nomeando a linha** que ficou órfã, em vez de esperar alguém perguntar
    "quem chama esta função?".

    O `skipif` é honesto: sem LibreOffice o ramo `_texto_legado` não roda e a
    cobertura cai por ausência de ambiente, não por ausência de teste. Nesse
    caso o portão se declara pulado em vez de mentir verde — e a nota de
    instrumento de `DH-003FE-01` registra que o container de 003.FI subiu
    exatamente assim.
    """
    resultado = subprocess.run(
        [
            sys.executable, "-m", "coverage", "run",
            "--source=scripts.varrer_acervo_lgpd",
            "-m", "pytest", str(_TESTES), "-q",
        ],
        cwd=_RAIZ, capture_output=True, text=True,
    )
    assert resultado.returncode == 0, f"a suíte do instrumento falhou:\n{resultado.stdout[-2000:]}"

    relatorio = subprocess.run(
        [sys.executable, "-m", "coverage", "report", "-m", "--include=*varrer_acervo_lgpd*"],
        cwd=_RAIZ, capture_output=True, text=True,
    )
    linha = next(
        (l for l in relatorio.stdout.splitlines() if "varrer_acervo_lgpd.py" in l), ""
    )
    assert linha, f"coverage nao reportou o alvo:\n{relatorio.stdout}"

    campos = linha.split()
    faltando = int(campos[2])
    nao_cobertas = linha.split("%", 1)[1].strip() if "%" in linha else ""
    assert faltando == 0, (
        f"{faltando} linha(s) de {_ALVO.name} sem execucao: {nao_cobertas}\n"
        "Toda linha do instrumento que decide a clausula de DH-003FE-01 tem de "
        "ser exercitada, ou levar `# pragma: no cover` com a razao escrita e "
        "declarada em _PRAGMAS_ESPERADOS."
    )
