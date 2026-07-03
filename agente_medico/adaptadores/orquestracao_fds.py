from __future__ import annotations

from pathlib import Path

from agente_medico.motor.extracao_fds import extrair_texto_fds
from agente_medico.motor.tipos import BlocoVerbatim, Pendencia
from agente_medico.motor.transcritor_fds import TranscritorLLM, gate_forma, transcrever_fds

# [DERIVADO — D-ARQ-47 cl.1-3] Costura de I/O (extração de texto -> invocação
# do transcritor-LLM -> gate de forma) para uso em produção. Para em gate_forma
# DELIBERADAMENTE: NÃO chama montar_fds (cl.4) — a admissão do candidato
# verbatim é a revisão-RT, que fica fora deste adaptador. Compor até
# montar_fds/resolver_composicao só existe em harness de teste (mockado),
# nunca em código de produção (motor/transcritor_fds.py, nota de topo).


def preparar_composicao(
    caminho: Path, cliente: TranscritorLLM
) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
    """extrair_texto_fds -> transcrever_fds -> gate_forma. Região de composição
    ausente (extrair_texto_fds devolve None) vira Pendencia bloqueante em vez
    de propagar None adiante (anti-supressão D-ARQ-31/35: ausência de FDS
    legível nunca deve virar composição vazia silenciosa)."""
    texto = extrair_texto_fds(caminho)
    if texto is None:
        return (), (
            Pendencia(
                tipo="composicao_ausente_fds",
                destinatario="extracao",
                motivo=f"Região de composição não localizada em {caminho}",
                bloqueante=True,
                regra_origem="D-ARQ-47",
            ),
        )
    candidato = transcrever_fds(texto, cliente)
    return gate_forma(candidato)
