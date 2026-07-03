from __future__ import annotations

from pathlib import Path
from unittest.mock import patch

from agente_medico.adaptadores.orquestracao_fds import preparar_composicao
from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.tipos import BlocoVerbatim, MembroVerbatim

_ALVO_EXTRACAO = "agente_medico.adaptadores.orquestracao_fds.extrair_texto_fds"


class MockTranscritor:
    def __init__(self, resultado: tuple[BlocoVerbatim, ...]) -> None:
        self._resultado = resultado
        self.texto_recebido: str = ""

    def transcrever(self, texto: str) -> tuple[BlocoVerbatim, ...]:
        self.texto_recebido = texto
        return self._resultado


class MockTranscritorIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, texto: str) -> tuple[BlocoVerbatim, ...]:
        raise TranscricaoIndisponivel(self._motivo)


def test_regiao_de_composicao_ausente_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=None):
        aprovados, pendencias = preparar_composicao(Path("qualquer.pdf"), MockTranscritor(()))

    assert aprovados == ()
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert pendencia.tipo == "composicao_ausente_fds"
    assert pendencia.destinatario == "extracao"
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-47"


def test_regiao_de_composicao_ausente_nao_chama_o_transcritor() -> None:
    mock = MockTranscritor((BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim("1-2-3", "X"),)),))
    with patch(_ALVO_EXTRACAO, return_value=None):
        preparar_composicao(Path("qualquer.pdf"), mock)
    assert mock.texto_recebido == ""


def test_fluxo_completo_ate_gate_forma_com_cliente_mock() -> None:
    bloco = BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim(cas="1-2-3", nome="X"),))
    mock = MockTranscritor((bloco,))
    with patch(_ALVO_EXTRACAO, return_value="texto da regiao de composicao"):
        aprovados, pendencias = preparar_composicao(Path("qualquer.pdf"), mock)

    assert mock.texto_recebido == "texto da regiao de composicao"
    assert aprovados == (bloco,)
    assert pendencias == ()


def test_bloco_reprovado_no_gate_de_forma_vira_pendencia() -> None:
    bloco_ruim = BlocoVerbatim(faixa="abc", membros=(MembroVerbatim(cas="1-2-3", nome="X"),))
    mock = MockTranscritor((bloco_ruim,))
    with patch(_ALVO_EXTRACAO, return_value="texto da regiao de composicao"):
        aprovados, pendencias = preparar_composicao(Path("qualquer.pdf"), mock)

    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_fds"


def test_mistura_blocos_bons_e_ruins_preserva_apenas_aprovados() -> None:
    bom = BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim(cas="1-2-3", nome="A"),))
    ruim = BlocoVerbatim(faixa="xyz", membros=(MembroVerbatim(cas="1-2-3", nome="B"),))
    mock = MockTranscritor((bom, ruim))
    with patch(_ALVO_EXTRACAO, return_value="texto"):
        aprovados, pendencias = preparar_composicao(Path("qualquer.pdf"), mock)

    assert aprovados == (bom,)
    assert len(pendencias) == 1


def test_transcricao_indisponivel_vira_pendencia_bloqueante_distinta() -> None:
    mock = MockTranscritorIndisponivel("CHAVE_API_GOOGLE ausente")
    with patch(_ALVO_EXTRACAO, return_value="texto da regiao de composicao"):
        aprovados, pendencias = preparar_composicao(Path("qualquer.pdf"), mock)

    assert aprovados == ()
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert pendencia.tipo == "transcricao_indisponivel_fds"
    assert pendencia.destinatario == "extracao"
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-47"
    assert "CHAVE_API_GOOGLE ausente" in pendencia.motivo


def test_regiao_ausente_e_transcricao_indisponivel_sao_pendencias_distintas() -> None:
    with patch(_ALVO_EXTRACAO, return_value=None):
        _, pend_regiao_ausente = preparar_composicao(
            Path("qualquer.pdf"), MockTranscritorIndisponivel("não deveria ser chamado")
        )
    with patch(_ALVO_EXTRACAO, return_value="texto"):
        _, pend_transcricao_indisponivel = preparar_composicao(
            Path("qualquer.pdf"), MockTranscritorIndisponivel("cascata Gemini sem 200")
        )

    assert pend_regiao_ausente[0].tipo == "composicao_ausente_fds"
    assert pend_transcricao_indisponivel[0].tipo == "transcricao_indisponivel_fds"
    assert pend_regiao_ausente[0].tipo != pend_transcricao_indisponivel[0].tipo
