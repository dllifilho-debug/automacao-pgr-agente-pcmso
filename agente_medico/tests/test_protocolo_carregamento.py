import pytest
from pathlib import Path

from agente_medico.motor.protocolo import carregar


def _montar_estrutura_minima(base: Path) -> None:
    vocab_dir = base / "vocabulario"
    vocab_dir.mkdir()
    (base / "regimes").mkdir()
    (vocab_dir / "agentes.yaml").write_text("agentes: {}", encoding="utf-8")
    (vocab_dir / "cargos.yaml").write_text("cargos: {}", encoding="utf-8")
    (vocab_dir / "exames.yaml").write_text("exames: {}", encoding="utf-8")
    (vocab_dir / "epis.yaml").write_text("epis: {}", encoding="utf-8")
    (base / "predicados_compostos.yaml").write_text("predicados_compostos: {}", encoding="utf-8")
    (base / "regras.yaml").write_text("regras: []", encoding="utf-8")


def test_carrega_diretorio_minimo(tmp_path: Path) -> None:
    _montar_estrutura_minima(tmp_path)
    protocolo = carregar(tmp_path)
    assert protocolo.vocabulario.agentes == {}
    assert protocolo.vocabulario.cargos == {}
    assert protocolo.vocabulario.exames == {}
    assert protocolo.vocabulario.epis == {}
    assert protocolo.predicados_compostos == {}
    assert protocolo.regras == []
    assert protocolo.regimes == {}


def test_falha_se_diretorio_vocabulario_ausente(tmp_path: Path) -> None:
    with pytest.raises(FileNotFoundError, match="vocabulario"):
        carregar(tmp_path)
