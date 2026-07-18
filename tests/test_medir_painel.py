"""Testes de scripts/medir_painel.py — importam as funções diretamente
(sem subprocess); pisos, não valores exatos (os números crescem)."""

from __future__ import annotations

import io
import re
from contextlib import redirect_stdout
from unittest.mock import patch

from scripts.medir_painel import (
    _ids_ativos_protocolo,
    main,
    medir_cas,
    medir_cobertura_clinica,
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


def test_main_sem_flag_suite_imprime_4_linhas_no_formato_esperado() -> None:
    saida = io.StringIO()
    with patch("sys.argv", ["medir_painel.py"]), redirect_stdout(saida):
        main()
    linhas = saida.getvalue().splitlines()
    assert len(linhas) == 4
    assert re.fullmatch(r"baseline: [0-9a-f]+", linhas[0])
    assert re.fullmatch(r"regras: \d+/\d+ ativas \(\d+%\)", linhas[1])
    assert re.fullmatch(r"cas: \d+/\d+ slugs \(\d+%\)", linhas[2])
    assert linhas[3] == "suite: não medida (use --suite)"
