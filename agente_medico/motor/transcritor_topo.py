from __future__ import annotations

from typing import Protocol

from agente_medico.motor.tipos import EnvelopeVerbatim, Pendencia

# [DERIVADO — D-ARQ-53 P2/P3; molde D-ARQ-47/D-ARQ-49 (transcritor_pgr.py)]
# Invocação injetável + gate de forma sob o candidato verbatim, espelhando o
# transcritor-LLM-GHE. Terceira fronteira transcrita (após "CAS transcrito" e
# "PGR transcrita") — a instância-envelope de D-ARQ-41. Resolvedor
# validade_texto->date, evidência-de-credencial e a confirmação-RT (D-ARQ-53
# P2) ficam para a fatia 3 — aqui só o contrato de forma.


class TranscritorTopo(Protocol):
    """Contrato do cliente-LLM injetável do topo do envelope (D-ARQ-53 P2/P3).

    Recebe o TOPO inteiro (saída de recortar_topo, 003.BU) e emite o
    candidato EnvelopeVerbatim. Transcreve as candidatas de validade
    (mês-ano ou dia, na ordem do documento) e o bloco de responsabilidade
    técnica. NÃO converte texto em `date`, NÃO escolhe a candidata "mais
    recente", NÃO julga credencial (engenheiro vs. técnico), NÃO emite
    `bool` de assinatura — assinatura é imagem, 100% confirmação-RT.
    """

    def transcrever(self, topo: str) -> EnvelopeVerbatim: ...


def transcrever_topo(topo: str, cliente: TranscritorTopo) -> EnvelopeVerbatim:
    """Ponto único de invocação do transcritor-LLM do topo (molde
    transcrever_ghes/transcrever_fds): o cliente entra por parâmetro tipado,
    nunca importado no módulo — testável com mock, sem bater em API/SDK
    real. Saída é CANDIDATA: a admissão (gate + confirmação-RT) é
    responsabilidade de gate_forma_topo e da fatia 3.
    """
    return cliente.transcrever(topo)


def gate_forma_topo(
    envelope: EnvelopeVerbatim,
) -> tuple[EnvelopeVerbatim | None, tuple[Pendencia, ...]]:
    """Gate de FORMA, não de conteúdo (molde gate_forma_ghe, D-ARQ-47 cl.3).

    REPROVADO (devolve None + Pendencia bloqueante) se: (a) qualquer
    elemento de validade_textos tem strip() == ""; ou (b) o envelope está
    INTEIRAMENTE vazio (validade_textos == () e os 3 campos de texto == "")
    — transcrição vazia em silêncio é classe D-ARQ-22.

    Campos individuais vazios (ex.: registro_profissional ausente no
    documento) NÃO reprovam sozinhos: ausência pontual é forma legítima
    (o documento pode não trazer aquele dado); julgamento de conteúdo é da
    confirmação-RT, fatia 3.
    """
    candidata_vazia = any(texto.strip() == "" for texto in envelope.validade_textos)
    integralmente_vazio = envelope.validade_textos == () and (
        envelope.responsavel_tecnico == ""
        and envelope.titulo_rt == ""
        and envelope.registro_profissional == ""
    )
    if candidata_vazia or integralmente_vazio:
        pendencia = Pendencia(
            tipo="forma_verbatim_topo",
            destinatario="extracao",
            motivo=(
                f"Envelope verbatim reprovado no gate de forma: "
                f"validade_textos={envelope.validade_textos!r}, "
                f"responsavel_tecnico={envelope.responsavel_tecnico!r}"
            ),
            bloqueante=True,
            regra_origem="D-ARQ-53",
        )
        return None, (pendencia,)
    return envelope, ()
