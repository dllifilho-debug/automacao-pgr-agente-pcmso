from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol

from agente_medico.motor.tipos import BlocoVerbatim, Pendencia
from agente_medico.motor.transcricao_fds import parsear_faixa

# [DERIVADO — D-ARQ-47, contrato de invocação e gate do transcritor-LLM-FDS]
# Invocação injetável (cl.2) + gate de forma (cl.3) sob o candidato verbatim
# (cl.1). A revisão-RT sobre o verbatim (cl.4) é a admissão do candidato —
# por isso este módulo NÃO compõe transcrever_fds -> gate_forma -> montar_fds
# fim-a-fim; isso criaria bypass do ponto de revisão. Composição fim-a-fim
# só existe em teste (harness mockado).


class TranscritorLLM(Protocol):
    """Contrato do cliente-LLM injetável (D-ARQ-47 cl.1/2).

    Recebe o TEXTO da região de composição (saída de extrair_texto_fds,
    003.BE) e emite o verbatim CANDIDATO — tuple[BlocoVerbatim, ...]. NÃO
    emite Componente, não resolve slug, não explode multi-CAS, não ordena
    faixa, não classifica perigo (isso é montagem/resolver, a jusante).

    Princípio de implementação real (cl.5, roteamento por formato-de-token):
    o triplo nome+CAS+faixa é a âncora semântica; a ordem de coluna no
    documento é irrelevante (varia por fabricante, medição 003.BD); linha
    sem CAS+faixa não é composição (ruído descartável). O texto do prompt
    fica para a fatia do cliente real — este é só o contrato de forma.
    """

    def transcrever(self, texto: str) -> tuple[BlocoVerbatim, ...]: ...


def transcrever_fds(texto: str, cliente: TranscritorLLM) -> tuple[BlocoVerbatim, ...]:
    """Ponto único de invocação do transcritor-LLM (D-ARQ-47 cl.2): o cliente
    entra por parâmetro tipado, nunca importado no módulo — testável com mock,
    sem bater em API/SDK real. Delega sem retry/telemetria nesta fatia
    (instrumentação futura entra aqui, não nos chamadores). Saída é CANDIDATA:
    a admissão é da revisão-RT (cl.4), não deste ponto.
    """
    return cliente.transcrever(texto)


def gate_forma(
    blocos: Sequence[BlocoVerbatim],
) -> tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]:
    """Gate de FORMA, não de conteúdo (D-ARQ-47 cl.3), antes do candidato
    entrar em montar_fds. Bloco APROVADO se: (a) tem >=1 membro com
    nome.strip() != ""; e (b) faixa.strip() == "" (vazia -> sentinela AUSENTE
    a jusante, D-ARQ-34 P1) OU parsear_faixa(faixa) is not None. Reusa a MESMA
    parsear_faixa da montagem (transcricao_fds.py) — consistência gate<->
    montagem por construção, zero duplicação.

    Bloco REPROVADO é EXCLUÍDO dos aprovados e vira Pendencia bloqueante:
    sem o gate, uma faixa não-vazia-e-ininteligível viraria concentracao=None
    na montagem, indistinguível de ausência legítima (erro silencioso, classe
    D-ARQ-22). NÃO valida CAS (é do gate_cas a jusante, D-ARQ-36), não decide
    materialidade, não corrige. Ordem e identidade dos aprovados preservadas.
    """
    aprovados: list[BlocoVerbatim] = []
    pendencias: list[Pendencia] = []
    for bloco in blocos:
        tem_membro_nomeado = any(m.nome.strip() != "" for m in bloco.membros)
        faixa = bloco.faixa.strip()
        forma_valida = tem_membro_nomeado and (
            faixa == "" or parsear_faixa(bloco.faixa) is not None
        )
        if forma_valida:
            aprovados.append(bloco)
        else:
            nomes = ", ".join(m.nome.strip() for m in bloco.membros) or "(sem membros)"
            pendencias.append(
                Pendencia(
                    tipo="forma_verbatim_fds",
                    destinatario="extracao",
                    motivo=(
                        f"Bloco verbatim reprovado no gate de forma: "
                        f"faixa={bloco.faixa!r}, membros=[{nomes}]"
                    ),
                    bloqueante=True,
                    regra_origem="D-ARQ-47",
                )
            )
    return tuple(aprovados), tuple(pendencias)
