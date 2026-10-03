"""Testes de scripts/medir_painel.py — importam as funções diretamente
(sem subprocess); pisos, não valores exatos (os números crescem)."""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from scripts.medir_painel import (
    _ids_ativos_protocolo,
    main,
    medir_cas,
    medir_cobertura_clinica,
    medir_indice_darq,
    medir_suite,
)


def test_numerador_regras_e_subconjunto_dos_ativos() -> None:
    numerador, denominador = medir_cobertura_clinica()
    ativos = _ids_ativos_protocolo()
    assert numerador <= denominador
    assert denominador == len(ativos)


def test_denominador_ativo_tem_piso_42() -> None:
    _, denominador = medir_cobertura_clinica()
    assert denominador >= 42


def test_cas_total_tem_piso_57() -> None:
    populados, total = medir_cas()
    assert total >= 57
    assert populados <= total


def test_medir_suite_verde_devolve_passed_e_skipped() -> None:
    fake = MagicMock(returncode=0, stdout="3 passed, 2 skipped in 1.02s\n")
    with patch("scripts.medir_painel.subprocess.run", return_value=fake):
        assert medir_suite() == (3, 2)


def test_medir_suite_vermelho_levanta_runtime_error() -> None:
    fake = MagicMock(returncode=1, stdout="1 failed, 5 passed in 0.77s\n")
    with patch("scripts.medir_painel.subprocess.run", return_value=fake):
        try:
            medir_suite()
        except RuntimeError as erro:
            assert "vermelha" in str(erro)
            assert "1 failed" in str(erro)
        else:
            raise AssertionError("medir_suite() deveria ter levantado RuntimeError")


def test_medir_suite_saida_irreconhecivel_levanta_runtime_error() -> None:
    fake = MagicMock(returncode=0, stdout="output inesperado sem contagens\n")
    with patch("scripts.medir_painel.subprocess.run", return_value=fake):
        try:
            medir_suite()
        except RuntimeError as erro:
            assert "não reconhecida" in str(erro)
        else:
            raise AssertionError("medir_suite() deveria ter levantado RuntimeError")


def test_medir_indice_darq_sincronizado_com_o_disco() -> None:
    assert medir_indice_darq() is True


def test_medir_indice_darq_detecta_divergencia() -> None:
    with patch("scripts.medir_painel.gerar_indice", return_value="conteúdo divergente"):
        assert medir_indice_darq() is False


def test_main_sem_flag_suite_imprime_5_linhas_no_formato_esperado() -> None:
    saida = io.StringIO()
    with patch("sys.argv", ["medir_painel.py"]), redirect_stdout(saida):
        main()
    linhas = saida.getvalue().splitlines()
    assert len(linhas) == 5
    assert re.fullmatch(r"baseline: [0-9a-f]+", linhas[0])
    assert re.fullmatch(r"regras: \d+/\d+ ativas \(\d+%\)", linhas[1])
    assert re.fullmatch(r"cas: \d+/\d+ slugs \(\d+%\)", linhas[2])
    assert linhas[3] in (
        "indice: sincronizado",
        "indice: DIVERGENTE — rode python -m scripts.gerar_indice_darq",
    )
    assert linhas[4] == "suite: não medida (use --suite)"


def _medir_em(tmp_path: Path, protocolo: str, regras: str, monkeypatch: pytest.MonkeyPatch) -> tuple[int, int]:
    (tmp_path / "PROTOCOLO.md").write_text(protocolo, encoding="utf-8")
    (tmp_path / "regras.yaml").write_text(regras, encoding="utf-8")
    (tmp_path / "motor").mkdir()
    monkeypatch.setattr("scripts.medir_painel._CAMINHO_PROTOCOLO", tmp_path / "PROTOCOLO.md")
    monkeypatch.setattr("scripts.medir_painel._CAMINHO_REGRAS", tmp_path / "regras.yaml")
    monkeypatch.setattr("scripts.medir_painel._DIR_MOTOR", tmp_path / "motor")
    return medir_cobertura_clinica()


def test_pacote_com_sufixo_de_letras_conta(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: voltar a regex para `R-[A-Z]+-[0-9]+` — o pacote some do
    # numerador e do denominador e o resultado vira (1, 1).
    protocolo = "### R-PKG-BZ-PRES — Pacote\n### R-RX-01 — RX\n"
    regras = "- id: R-PKG-BZ-PRES\n- id: R-RX-01-adm\n"
    assert _medir_em(tmp_path, protocolo, regras, monkeypatch) == (2, 2)


def test_variante_minuscula_colapsa_na_familia(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: aceitar minúsculas no sufixo (`R-[A-Z]+-[A-Za-z0-9-]+`) —
    # `R-BIO-04-cobalto` deixa de contar como `R-BIO-04` e o numerador cai para 0.
    protocolo = "### R-BIO-04 — Indicadores biológicos\n"
    regras = "- id: R-BIO-04-cobalto\n"
    assert _medir_em(tmp_path, protocolo, regras, monkeypatch) == (1, 1)


def test_pacote_longo_nao_conta_o_prefixo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: aceitar um só segmento de letras (`R-[A-Z]+-[A-Z]+`) — os dois
    # headers viram `R-PKG-SOLD` e o resultado cai para (1, 1).
    protocolo = "### R-PKG-SOLD — Soldador\n### R-PKG-SOLD-CO — Carboxi-hemoglobina\n"
    regras = "- id: R-PKG-SOLD-CO\n"
    assert _medir_em(tmp_path, protocolo, regras, monkeypatch) == (1, 2)
