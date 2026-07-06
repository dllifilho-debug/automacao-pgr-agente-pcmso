from __future__ import annotations

import json
from collections.abc import Sequence

from agente_medico.motor.tipos import FDS, BlocoVerbatim, MembroVerbatim, Pendencia
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_fds import gate_forma


class VerbatimInvalido(ValueError):
    """Artefato de revisão-RT ilegível ou adulterado além do schema (D-ARQ-47 cl.4)."""


_CAMPOS_ENVELOPE = {"versao", "blocos"}
_CAMPOS_BLOCO = {"faixa", "membros"}
_CAMPOS_MEMBRO = {"cas", "nome"}


def serializar_verbatim(blocos: Sequence[BlocoVerbatim]) -> str:
    """Serializa o verbatim para o artefato de ida ao RT. Preserva byte-exato
    (inclusive '\\n' intra-token do nome/CAS): nenhum campo é normalizado aqui.
    """
    envelope = {
        "versao": 1,
        "blocos": [
            {
                "faixa": bloco.faixa,
                "membros": [{"cas": m.cas, "nome": m.nome} for m in bloco.membros],
            }
            for bloco in blocos
        ],
    }
    return json.dumps(envelope, ensure_ascii=False, indent=2)


def desserializar_verbatim(texto: str) -> tuple[BlocoVerbatim, ...]:
    """Desserializa o artefato de volta do RT. Rejeita com VerbatimInvalido
    qualquer desvio do schema — inclusive campo desconhecido (anti-erro-silencioso,
    classe D-ARQ-22): um artefato adulterado não deve ser aceito parcialmente.
    Garantia: desserializar_verbatim(serializar_verbatim(x)) == x.
    """
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise VerbatimInvalido(f"JSON inválido: {erro}") from erro

    if not isinstance(dados, dict):
        raise VerbatimInvalido(
            f"Envelope deve ser um objeto JSON, recebido {type(dados).__name__}"
        )

    campos_extra = set(dados) - _CAMPOS_ENVELOPE
    if campos_extra:
        raise VerbatimInvalido(f"Envelope com campo(s) desconhecido(s): {sorted(campos_extra)}")
    if "versao" not in dados:
        raise VerbatimInvalido("Envelope sem campo obrigatório 'versao'")
    if "blocos" not in dados:
        raise VerbatimInvalido("Envelope sem campo obrigatório 'blocos'")

    versao = dados["versao"]
    if versao != 1:
        raise VerbatimInvalido(f"Versão de verbatim não suportada: {versao!r} (esperado 1)")

    blocos_dados = dados["blocos"]
    if not isinstance(blocos_dados, list):
        raise VerbatimInvalido(
            f"'blocos' deve ser uma lista, recebido {type(blocos_dados).__name__}"
        )

    return tuple(_desserializar_bloco(b, i) for i, b in enumerate(blocos_dados))


def _desserializar_bloco(dado: object, indice: int) -> BlocoVerbatim:
    if not isinstance(dado, dict):
        raise VerbatimInvalido(
            f"Bloco {indice}: deve ser um objeto JSON, recebido {type(dado).__name__}"
        )
    campos_extra = set(dado) - _CAMPOS_BLOCO
    if campos_extra:
        raise VerbatimInvalido(f"Bloco {indice}: campo(s) desconhecido(s): {sorted(campos_extra)}")
    if "faixa" not in dado:
        raise VerbatimInvalido(f"Bloco {indice}: campo obrigatório 'faixa' ausente")
    if "membros" not in dado:
        raise VerbatimInvalido(f"Bloco {indice}: campo obrigatório 'membros' ausente")

    faixa = dado["faixa"]
    if not isinstance(faixa, str):
        raise VerbatimInvalido(
            f"Bloco {indice}: 'faixa' deve ser string, recebido {type(faixa).__name__}"
        )

    membros_dados = dado["membros"]
    if not isinstance(membros_dados, list):
        raise VerbatimInvalido(
            f"Bloco {indice}: 'membros' deve ser uma lista, recebido {type(membros_dados).__name__}"
        )

    membros = tuple(
        _desserializar_membro(m, indice, j) for j, m in enumerate(membros_dados)
    )
    return BlocoVerbatim(faixa=faixa, membros=membros)


def _desserializar_membro(dado: object, indice_bloco: int, indice_membro: int) -> MembroVerbatim:
    prefixo = f"Bloco {indice_bloco}, membro {indice_membro}"
    if not isinstance(dado, dict):
        raise VerbatimInvalido(f"{prefixo}: deve ser um objeto JSON, recebido {type(dado).__name__}")
    campos_extra = set(dado) - _CAMPOS_MEMBRO
    if campos_extra:
        raise VerbatimInvalido(f"{prefixo}: campo(s) desconhecido(s): {sorted(campos_extra)}")
    if "cas" not in dado:
        raise VerbatimInvalido(f"{prefixo}: campo obrigatório 'cas' ausente")
    if "nome" not in dado:
        raise VerbatimInvalido(f"{prefixo}: campo obrigatório 'nome' ausente")

    cas = dado["cas"]
    nome = dado["nome"]
    if not isinstance(cas, str):
        raise VerbatimInvalido(f"{prefixo}: 'cas' deve ser string, recebido {type(cas).__name__}")
    if not isinstance(nome, str):
        raise VerbatimInvalido(f"{prefixo}: 'nome' deve ser string, recebido {type(nome).__name__}")

    return MembroVerbatim(cas=cas, nome=nome)


def montar_fds_revisado(
    blocos: Sequence[BlocoVerbatim],
) -> tuple[FDS, tuple[Pendencia, ...]]:
    """Porta de composição de PRODUÇÃO pós-revisão-RT (D-ARQ-47 cl.4). A entrada é
    o verbatim JÁ REVISADO pelo responsável técnico — a admissão do candidato-LLM
    ancora em R-PGR-01/D-ARQ-33 cl.4, não neste módulo — nunca o candidato bruto de
    transcrever_fds; por isso esta composição NÃO viola a nota de transcritor_fds.py
    (que proíbe compor transcrever_fds -> gate_forma -> montar_fds em produção: aqui
    a entrada já passou pelo RT, o bypass que aquela nota veda não se aplica).
    Re-passar por gate_forma é deliberado, não redundante: a edição do RT pode
    introduzir forma inválida (ex.: apagar um nome); rodar o MESMO gate mantém
    consistência por construção entre o caminho revisado e o caminho de teste.
    """
    aprovados, pendencias = gate_forma(blocos)
    return montar_fds(aprovados), pendencias
