from __future__ import annotations

import json
from datetime import date

from agente_medico.motor.tipos import CandidataValidade, EnvelopeConfirmado, EnvelopeVerbatim

# D-ARQ-53 P2/P3, D-ARQ-47 cl.4, R-PGR-01, R-PGR-06: seam de confirmação-RT do
# envelope do topo (molde revisao_verbatim.py — schema estrito, anti-erro-
# silencioso D-ARQ-22). serializar_envelope monta o artefato de ida com as
# candidatas resolvidas (resolvedor_topo.py) e a proposta "mais recente" já
# pré-preenchida em confirmacao.validade — o RT aceita como está ou edita o
# dia exato. confirmacao.assinatura_engenheiro NUNCA tem default: a
# assinatura no topo é imagem, não text-derivable (003.BV / D-ARQ-53 P2) —
# 100% CONFIRMAÇÃO-RT.


class EnvelopeRevisadoInvalido(ValueError):
    """Artefato de confirmação-RT do envelope ilegível ou adulterado além do
    schema (molde VerbatimInvalido, D-ARQ-47 cl.4)."""


_CAMPOS_ENVELOPE = {"versao", "candidatas", "proposta", "credencial", "confirmacao"}
_CAMPOS_CANDIDATA = {"texto", "data"}
_CAMPOS_CREDENCIAL = {"responsavel_tecnico", "titulo_rt", "registro_profissional"}
_CAMPOS_CONFIRMACAO = {"validade", "assinatura_engenheiro"}


def serializar_envelope(
    envelope: EnvelopeVerbatim,
    candidatas: tuple[CandidataValidade, ...],
    proposta: date | None,
) -> str:
    """Serializa o artefato de ida ao RT. candidatas = saída de
    resolver_validade (texto cru + data resolvida ou null — não-parseável
    vai EXPLÍCITO ao RT, nunca omitido). credencial = campos crus do
    envelope, SEM heurística de token "Eng."/"CREA" (decisão D5; juízo
    engenheiro-vs-técnico é 100% RT, anti-keyword "Técnico de Segurança do
    Trabalho 01" — 003.BV). confirmacao.validade pré-preenchido com a
    proposta (ISO ou null) para o RT aceitar-como-está ou editar o dia
    exato; confirmacao.assinatura_engenheiro SEM default (imagem, não
    text-derivable — 003.BV / D-ARQ-53 P2).
    """
    dados = {
        "versao": 1,
        "candidatas": [
            {"texto": c.texto, "data": c.data.isoformat() if c.data is not None else None}
            for c in candidatas
        ],
        "proposta": proposta.isoformat() if proposta is not None else None,
        "credencial": {
            "responsavel_tecnico": envelope.responsavel_tecnico,
            "titulo_rt": envelope.titulo_rt,
            "registro_profissional": envelope.registro_profissional,
        },
        "confirmacao": {
            "validade": proposta.isoformat() if proposta is not None else None,
            "assinatura_engenheiro": None,
        },
    }
    return json.dumps(dados, ensure_ascii=False, indent=2)


def desserializar_confirmacao(texto: str) -> EnvelopeConfirmado:
    """Desserializa o artefato de volta do RT. Schema ESTRITO: rejeita com
    EnvelopeRevisadoInvalido qualquer desvio — campo desconhecido em
    QUALQUER nível (envelope, candidatas[], credencial, confirmacao),
    versao != 1, confirmacao.validade ausente/null/não-ISO,
    confirmacao.assinatura_engenheiro ausente/null/não-bool. Sem default
    silencioso em nenhum campo. Garantia: artefato da ida com confirmacao
    preenchida pelo RT -> EnvelopeConfirmado byte-determinístico.
    """
    try:
        dados = json.loads(texto)
    except json.JSONDecodeError as erro:
        raise EnvelopeRevisadoInvalido(f"JSON inválido: {erro}") from erro

    if not isinstance(dados, dict):
        raise EnvelopeRevisadoInvalido(
            f"Envelope deve ser um objeto JSON, recebido {type(dados).__name__}"
        )

    campos_extra = set(dados) - _CAMPOS_ENVELOPE
    if campos_extra:
        raise EnvelopeRevisadoInvalido(
            f"Envelope com campo(s) desconhecido(s): {sorted(campos_extra)}"
        )
    for campo in _CAMPOS_ENVELOPE:
        if campo not in dados:
            raise EnvelopeRevisadoInvalido(f"Envelope sem campo obrigatório {campo!r}")

    versao = dados["versao"]
    if versao != 1:
        raise EnvelopeRevisadoInvalido(f"Versão de envelope não suportada: {versao!r} (esperado 1)")

    _validar_candidatas(dados["candidatas"])
    _validar_proposta(dados["proposta"])
    _validar_credencial(dados["credencial"])
    return _desserializar_confirmacao(dados["confirmacao"])


def _validar_candidatas(dado: object) -> None:
    if not isinstance(dado, list):
        raise EnvelopeRevisadoInvalido(
            f"'candidatas' deve ser uma lista, recebido {type(dado).__name__}"
        )
    for i, item in enumerate(dado):
        if not isinstance(item, dict):
            raise EnvelopeRevisadoInvalido(
                f"Candidata {i}: deve ser um objeto JSON, recebido {type(item).__name__}"
            )
        campos_extra = set(item) - _CAMPOS_CANDIDATA
        if campos_extra:
            raise EnvelopeRevisadoInvalido(
                f"Candidata {i}: campo(s) desconhecido(s): {sorted(campos_extra)}"
            )
        if "texto" not in item:
            raise EnvelopeRevisadoInvalido(f"Candidata {i}: campo obrigatório 'texto' ausente")
        if "data" not in item:
            raise EnvelopeRevisadoInvalido(f"Candidata {i}: campo obrigatório 'data' ausente")
        if not isinstance(item["texto"], str):
            raise EnvelopeRevisadoInvalido(
                f"Candidata {i}: 'texto' deve ser string, recebido {type(item['texto']).__name__}"
            )
        data_val = item["data"]
        if data_val is not None and not isinstance(data_val, str):
            raise EnvelopeRevisadoInvalido(
                f"Candidata {i}: 'data' deve ser string ISO ou null, recebido {type(data_val).__name__}"
            )


def _validar_proposta(dado: object) -> None:
    if dado is not None and not isinstance(dado, str):
        raise EnvelopeRevisadoInvalido(
            f"'proposta' deve ser string ISO ou null, recebido {type(dado).__name__}"
        )


def _validar_credencial(dado: object) -> None:
    if not isinstance(dado, dict):
        raise EnvelopeRevisadoInvalido(
            f"'credencial' deve ser um objeto JSON, recebido {type(dado).__name__}"
        )
    campos_extra = set(dado) - _CAMPOS_CREDENCIAL
    if campos_extra:
        raise EnvelopeRevisadoInvalido(
            f"'credencial': campo(s) desconhecido(s): {sorted(campos_extra)}"
        )
    for campo in _CAMPOS_CREDENCIAL:
        if campo not in dado:
            raise EnvelopeRevisadoInvalido(f"'credencial': campo obrigatório {campo!r} ausente")
        if not isinstance(dado[campo], str):
            raise EnvelopeRevisadoInvalido(
                f"'credencial.{campo}' deve ser string, recebido {type(dado[campo]).__name__}"
            )


def _desserializar_confirmacao(dado: object) -> EnvelopeConfirmado:
    if not isinstance(dado, dict):
        raise EnvelopeRevisadoInvalido(
            f"'confirmacao' deve ser um objeto JSON, recebido {type(dado).__name__}"
        )
    campos_extra = set(dado) - _CAMPOS_CONFIRMACAO
    if campos_extra:
        raise EnvelopeRevisadoInvalido(
            f"'confirmacao': campo(s) desconhecido(s): {sorted(campos_extra)}"
        )
    if "validade" not in dado:
        raise EnvelopeRevisadoInvalido("'confirmacao': campo obrigatório 'validade' ausente")
    if "assinatura_engenheiro" not in dado:
        raise EnvelopeRevisadoInvalido(
            "'confirmacao': campo obrigatório 'assinatura_engenheiro' ausente"
        )

    validade_bruta = dado["validade"]
    if not isinstance(validade_bruta, str):
        raise EnvelopeRevisadoInvalido(
            "'confirmacao.validade' ausente ou não preenchida pelo RT "
            f"(esperado string ISO 'AAAA-MM-DD', recebido {validade_bruta!r})"
        )
    try:
        validade = date.fromisoformat(validade_bruta)
    except ValueError as erro:
        raise EnvelopeRevisadoInvalido(
            f"'confirmacao.validade' não é data ISO válida: {validade_bruta!r}"
        ) from erro

    assinatura = dado["assinatura_engenheiro"]
    if not isinstance(assinatura, bool):
        raise EnvelopeRevisadoInvalido(
            "'confirmacao.assinatura_engenheiro' ausente ou não preenchida pelo RT "
            f"(esperado bool, recebido {assinatura!r})"
        )

    return EnvelopeConfirmado(validade=validade, assinatura_engenheiro=assinatura)
