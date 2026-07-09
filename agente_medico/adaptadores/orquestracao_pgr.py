from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.extracao_pgr import extrair_texto_pgr, recortar_blocos_ghe, recortar_topo
from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.resolvedor_topo import resolver_validade
from agente_medico.motor.revisao_envelope import serializar_envelope
from agente_medico.motor.tipos import EnvelopeConfirmado, GHEVerbatim, Pendencia, Resultado
from agente_medico.motor.transcritor_pgr import TranscritorGHE, gate_forma_ghe, transcrever_ghes
from agente_medico.motor.transcritor_topo import TranscritorTopo, gate_forma_topo, transcrever_topo

# [DERIVADO — D-ARQ-52/D-ARQ-53; molde D-ARQ-47/orquestracao_fds.py]
# Costura de I/O do lado-PGR fim-a-fim: extração -> recorte -> transcrição-LLM
# -> gate de forma -> hidratação -> motor. Adaptador impuro (I/O + LLM) fora
# do motor (D-ARQ-48). processar_pgr (motor/entrada.py) NÃO é tocado — é o
# ponto de entrada puro que este adaptador alimenta com um PGR já hidratado.
# preparar_envelope (D-ARQ-53 fatia 4) costura a ida do envelope do topo até
# o artefato de confirmação-RT; consumidores finais R-PGR-01/R-PGR-06
# (estagios/gates.py) só recebem validade/assinatura via EnvelopeConfirmado,
# nunca direto do artefato — a volta (desserializar_confirmacao) é chamada
# pelo caller, fora deste adaptador (seam humano, molde D-ARQ-47 cl.4).


def preparar_envelope(
    caminho: Path, cliente: TranscritorTopo
) -> tuple[str | None, tuple[Pendencia, ...]]:
    """extrair_texto_pgr -> recortar_topo -> transcrever_topo -> gate_forma_topo
    -> resolver_validade -> serializar_envelope (D-ARQ-53 fatia 4; consumidores
    finais R-PGR-01/R-PGR-06).

    PARA DELIBERADAMENTE no artefato JSON de ida ao RT: a confirmação-RT
    (desserializar_confirmacao) fica FORA deste adaptador (molde
    orquestracao_fds.py, que para em gate_forma — revisão-RT é humana, não
    compõe em produção).

    Topo == "" (âncora na 1ª linha do documento, topo genuinamente vazio)
    NÃO ganha short-circuit aqui: flui até gate_forma_topo, que já reprova o
    envelope integralmente vazio — ponto único de reprovação, sem duplicar
    o critério.

    Cada ramo de falha devolve (None, (Pendencia,)) bloqueante, nunca ()
    silencioso (anti-supressão D-ARQ-31/35): ausência de âncora de topo
    (recortar_topo -> None) é "topo_ausente"; falha de INVOCAÇÃO do
    transcritor-LLM é "transcricao_indisponivel_topo"; reprovação de forma
    repassa a Pendencia de gate_forma_topo ("forma_verbatim_topo") tal como
    preparar_ghes repassa a de gate_forma_ghe.
    """
    paginas = extrair_texto_pgr(caminho)
    topo = recortar_topo(paginas)
    if topo is None:
        return None, (
            Pendencia(
                tipo="topo_ausente",
                destinatario="extracao",
                motivo=f"Nenhuma âncora de topo localizada em {caminho}",
                bloqueante=True,
                regra_origem="D-ARQ-53",
            ),
        )
    try:
        candidato = transcrever_topo(topo, cliente)
    except TranscricaoIndisponivel as e:
        return None, (
            Pendencia(
                tipo="transcricao_indisponivel_topo",
                destinatario="extracao",
                motivo=str(e),
                bloqueante=True,
                regra_origem="D-ARQ-53",
            ),
        )
    aprovado, pend_forma = gate_forma_topo(candidato)
    if aprovado is None:
        return None, pend_forma
    candidatas, proposta = resolver_validade(aprovado)
    return serializar_envelope(aprovado, candidatas, proposta), ()


def preparar_ghes(
    caminho: Path, cliente: TranscritorGHE
) -> tuple[tuple[GHEVerbatim, ...], tuple[Pendencia, ...]]:
    """extrair_texto_pgr -> recortar_blocos_ghe -> transcrever_ghes -> gate_forma_ghe.

    Zero blocos (recortar_blocos_ghe devolve []) vira Pendencia bloqueante
    aqui — quem transforma ausência de âncora em Pendencia é o chamador,
    como documentado em recortar_blocos_ghe (anti-supressão D-ARQ-31/35).
    """
    paginas = extrair_texto_pgr(caminho)
    blocos = recortar_blocos_ghe(paginas)
    if not blocos:
        return (), (
            Pendencia(
                tipo="blocos_ausentes",
                destinatario="extracao",
                motivo=f"Nenhum bloco GHE localizado em {caminho}",
                bloqueante=True,
                regra_origem="D-ARQ-52",
            ),
        )
    try:
        candidatos = transcrever_ghes(blocos, cliente)
    except TranscricaoIndisponivel as e:
        return (), (
            Pendencia(
                tipo="transcricao_indisponivel_pgr",
                destinatario="extracao",
                motivo=str(e),
                bloqueante=True,
                regra_origem="D-ARQ-52",
            ),
        )
    return gate_forma_ghe(candidatos)


def processar_arquivo_pgr(
    caminho: Path,
    protocolo: Protocolo,
    cliente: TranscritorGHE,
    envelope: EnvelopeConfirmado,
    hoje: date | None = None,
) -> tuple[Resultado | None, tuple[Pendencia, ...]]:
    """Costura completa arquivo -> Resultado (D-ARQ-52/D-ARQ-53).

    envelope.validade e envelope.assinatura_engenheiro alimentam
    hidratar_pgr, consumidos por R-PGR-06/R-PGR-01 (estagios/gates.py). A
    origem desses campos agora é document-derived + confirmação-RT: o
    caller monta o EnvelopeConfirmado a partir de preparar_envelope (ida) +
    desserializar_confirmacao (volta, após revisão-RT humana no artefato) —
    o paliativo RT-supplied de D-ARQ-52 seam 3 fecha aqui, no nível do
    adaptador. Consequência estrutural (não paliativo): extrair_texto_pgr
    roda 2x sobre o mesmo arquivo — uma vez em preparar_envelope (ida do
    envelope), outra em preparar_ghes/aqui dentro (volta dos GHEs) — porque
    o seam de confirmação-RT entre as duas invocações é humano, não
    componível numa única passada de I/O.

    Aprovação PARCIAL no gate de forma (alguns GHE reprovados) processa os
    aprovados normalmente e CARREGA as pendências bloqueantes dos reprovados
    na lista final devolvida — zeramento de linha por bloqueio de GHE é
    D-ARQ-31 fatia 2, fora de escopo aqui.
    """
    aprovados, pend_forma = preparar_ghes(caminho, cliente)
    if not aprovados:
        # Parse total falho (blocos ausentes, transcrição indisponível, ou
        # todos os GHE reprovados no gate): sem verbatim para hidratar, não
        # inventa PGR (D-ARQ-22).
        return None, pend_forma
    indice = construir_indice_termos(protocolo.vocabulario.agentes)
    pgr, pend_hidr = hidratar_pgr(
        aprovados, indice, envelope.validade, envelope.assinatura_engenheiro
    )
    resultado = processar_pgr(pgr, protocolo, hoje)
    return resultado, (*pend_forma, *tuple(pend_hidr))
