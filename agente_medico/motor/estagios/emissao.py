from __future__ import annotations

from typing import Any

from agente_medico.motor.leo_resolver import AvaliacaoLimiteQuimico, avaliar_medicao_quimica
from agente_medico.motor.predicados import (
    ResultadoPredicado,
    avaliar,
    pernas_ausentes,
    pernas_ausentes_absorvidas,
    serializar_predicado,
)
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import (
    NIVEIS_RISCO_PXS,
    Ausente,
    ExameEmitido,
    GHEContext,
    Momento,
    Motivo,
    Observacao,
    Pendencia,
    ProcedenciaMedicao,
    Risco,
)

_MOMENTOS: dict[str, Momento] = {m.name: m for m in Momento}


def _converter_momento(raw: str, regra_id: str, exame: str) -> Momento:
    key = raw.upper()
    if key not in _MOMENTOS:
        raise ValueError(
            f"Momento inválido '{raw}' na regra '{regra_id}', exame '{exame}'"
        )
    return _MOMENTOS[key]


def _descrever_fonte(risco: Risco) -> str:
    if risco.fonte == "explicito":
        descricao = "PGR" if risco.nivel_risco is None else f"PGR (nível {risco.nivel_risco})"
        return descricao if risco.detalhe is None else f"{descricao}; {risco.detalhe}"
    if risco.fonte == "quimico_composicao":
        return f"FDS — {risco.detalhe}"
    return risco.detalhe or risco.fonte


def _risco_origem(regra: dict[str, Any], ctx: GHEContext) -> str | None:
    """D-ARQ-22 Parte B, faceta `risco_origem` (DH-003ED-01), recorte atômico:
    só a regra cujo `quando` é o próprio slug do agente (R-BIO-04-*) sabe de
    qual risco veio sem rastrear o átomo dentro de `predicados.avaliar`.
    Composto ou primitivo que não é agente do GHE → None, como antes."""
    quando = regra["quando"]
    if not isinstance(quando, str):
        return None
    fontes = list(dict.fromkeys(_descrever_fonte(r) for r in ctx.riscos if r.agente == quando))
    if not fontes:
        return None
    return f"{quando} ← " + " | ".join(fontes)


def _emitir_regra(
    regra: dict[str, Any], ctx: GHEContext, protocolo: Protocolo, emitidos: list[ExameEmitido]
) -> None:
    for nome, ausente in pernas_ausentes_absorvidas(regra["quando"], ctx, protocolo):
        ctx.pendencias.append(
            Pendencia(
                tipo="perna_ausente_absorvida",
                destinatario="elaborador_pgr",
                motivo=(
                    f"Regra {regra['id']}: emitiu por outra perna do predicado, mas "
                    f"'{nome}' não pôde ser avaliado — {ausente.mensagem}"
                ),
                bloqueante=False,
                regra_origem=str(regra["id"]),
                ghe_id=ctx.pgr_ghe.id,
                exames_alvo=tuple(str(item["exame"]) for item in regra["emite"]),
            )
        )

    predicado_str = serializar_predicado(regra["quando"])
    motivo = Motivo(
        regra_id=str(regra["id"]),
        predicado=predicado_str,
        risco_origem=_risco_origem(regra, ctx),
        detalhe=f"Emitido por regra {regra['id']}",
        status_regra=regra.get("status"),
    )

    for item in regra["emite"]:
        momentos: set[Momento] = {
            _converter_momento(str(m), str(regra["id"]), str(item["exame"]))
            for m in item["momentos"]
        }
        emitidos.append(
            ExameEmitido(
                exame=str(item["exame"]),
                periodicidade_meses=int(item["periodicidade_meses"]),
                momentos=momentos,
                motivos=[motivo],
                periodicidade_apos_15a=item.get("periodicidade_apos_15a"),
            )
        )


def _nivel_dispensa(regra: dict[str, Any], ctx: GHEContext) -> str | None:
    """R-BIO-05 (DT-003EB-02, [INTERPRETADO]): o nível P×S que troca o exame por
    menção documental, ou None se a regra deve emitir. Dispensa só quando TODO
    risco do agente traz nível listado em `niveis_risco` — nível ausente (rota
    sem avaliação, risco implícito, composição de FDS) ou acima da lista emite."""
    mencao = regra.get("mencao_documental")
    if mencao is None:
        return None
    niveis = [r.nivel_risco for r in ctx.riscos if r.agente == regra["quando"]]
    permitidos = set(mencao["niveis_risco"])
    if not niveis or not all(n in permitidos for n in niveis):
        return None
    return max((str(n) for n in niveis), key=NIVEIS_RISCO_PXS.index)


def _numero(valor: float) -> str:
    return f"{valor:.4g}".replace(".", ",")


def _descrever_medicao(
    avaliacao: AvaliacaoLimiteQuimico, procedencia: ProcedenciaMedicao | None
) -> str:
    unidade = "mg/m³" if avaliacao.unidade == "mg/m3" else avaliacao.unidade
    texto = (
        f"{_numero(avaliacao.valor)} {unidade}, {_numero(avaliacao.pct_limite)}% do LT de "
        f"{_numero(avaliacao.limite)} {unidade} — {avaliacao.fonte_normativa}"
    )
    if procedencia is None:
        return f"{texto}; medição transcrita do PGR"
    return f"{texto}; laudo {procedencia.laudo}, {procedencia.data:%d/%m/%Y}"


def _dispensa_por_medicao(
    regra: dict[str, Any], ctx: GHEContext, agentes_vocab: dict[str, Any]
) -> tuple[str, str] | None:
    """R-BIO-05 emenda D-ARQ-86 cl.6 (NR-07 7.5.12 "b" c/c NR-09 9.6.1 "b"):
    nível em `niveis_com_medicao_abaixo_acao` dispensa só com medição do agente
    no GHE abaixo do nível de ação (50% do LT). Várias medições: vale a maior.
    Risco sem nível só passa se vier de composição de FDS — a medição ambiental
    do agente cobre a fonte; risco implícito ou linha do PGR sem avaliação emite.
    Devolve (nível, descrição da medição) ou None se a regra deve emitir."""
    mencao = regra["mencao_documental"]
    com_medicao = set(mencao.get("niveis_com_medicao_abaixo_acao", ()))
    if not com_medicao:
        return None
    riscos = [r for r in ctx.riscos if r.agente == regra["quando"]]
    classificados = [r.nivel_risco for r in riscos if r.nivel_risco is not None]
    aceitos = com_medicao | set(mencao["niveis_risco"])
    if (
        not classificados
        or any(r.nivel_risco is None and r.fonte != "quimico_composicao" for r in riscos)
        or not all(n in aceitos for n in classificados)
    ):
        return None
    avaliacoes = [
        (avaliacao, r.quantificacao.procedencia)
        for r in riscos
        if r.quantificacao is not None
        and (avaliacao := avaliar_medicao_quimica(r.agente, r.quantificacao, agentes_vocab))
        is not None
    ]
    if not avaliacoes:
        return None
    maior, procedencia = max(avaliacoes, key=lambda par: par[0].pct_limite)
    if not maior.abaixo_nivel_acao:
        return None
    nivel = max((str(n) for n in classificados), key=NIVEIS_RISCO_PXS.index)
    return nivel, _descrever_medicao(maior, procedencia)


def stage_5_emissao(ctx: GHEContext, protocolo: Protocolo) -> list[ExameEmitido]:
    """
    Para cada regra em protocolo.regras:
      1. Avaliar expressão `quando` via avaliar(expr, ctx, protocolo).
      2. Se True  → emitir todos os itens de `emite` como ExameEmitido.
      3. Se False → não emite, sem pendência.
      4. Se Ausente:
          - Se regra tem `quando_ausente: false` → trata como False (não emite, sem pendência)
          - Se regra tem `quando_ausente: {presumir_true: [primitivos]}` (D-ARQ-68 cl.5):
            coletar pernas_ausentes(regra["quando"], ctx, protocolo); se o conjunto for
            vazio ou tiver nome fora da lista → bloqueia como abaixo; se todo nome
            coletado estiver na lista → emitir normalmente (mesmo caminho do ramo True)
            e anexar Pendencia(tipo="predicado_ausente_presumido", bloqueante=False) por
            primitivo presumido.
          - Caso contrário → adiciona Pendencia(bloqueante=True) ao ctx.pendencias e não emite
      5. Se True e a regra tem `mencao_documental` (R-BIO-05) e todo risco do agente
         traz nível P×S listado → não emite; anexa Observacao a ctx.observacoes.
         Mesmo desvio quando o nível está em `niveis_com_medicao_abaixo_acao` e há
         medição do agente abaixo do nível de ação (D-ARQ-86); a Observacao leva
         a medição.
    Retorna lista de ExameEmitido na ordem em que foram emitidos.
    Não muta ctx exceto ctx.pendencias e ctx.observacoes.
    """
    emitidos: list[ExameEmitido] = []

    for regra in protocolo.regras:
        resultado: ResultadoPredicado = avaliar(regra["quando"], ctx, protocolo)

        if isinstance(resultado, Ausente):
            quando_ausente = regra.get("quando_ausente")
            if quando_ausente is False:
                continue

            if isinstance(quando_ausente, dict) and "presumir_true" in quando_ausente:
                primitivos_presumidos = set(quando_ausente["presumir_true"])
                faltantes = pernas_ausentes(regra["quando"], ctx, protocolo)
                nomes_faltantes = {nome for nome, _ in faltantes}
                if nomes_faltantes and nomes_faltantes <= primitivos_presumidos:
                    _emitir_regra(regra, ctx, protocolo, emitidos)
                    exames_alvo_presumido = tuple(
                        str(item["exame"]) for item in regra["emite"]
                    )
                    for nome, ausente in faltantes:
                        ctx.pendencias.append(
                            Pendencia(
                                tipo="predicado_ausente_presumido",
                                destinatario="elaborador_pgr",
                                motivo=(
                                    f"Regra {regra['id']}: emitido sob presunção "
                                    f"protetiva do primitivo '{nome}' — {ausente.mensagem}"
                                ),
                                bloqueante=False,
                                regra_origem=str(regra["id"]),
                                ghe_id=ctx.pgr_ghe.id,
                                exames_alvo=exames_alvo_presumido,
                            )
                        )
                    continue

            exames_alvo = tuple(str(item["exame"]) for item in regra["emite"])
            ctx.pendencias.append(
                Pendencia(
                    tipo="predicado_ausente",
                    destinatario="elaborador_pgr",
                    motivo=(
                        f"Regra {regra['id']}: predicado '{regra['quando']}' "
                        f"não pôde ser avaliado — {resultado.mensagem}"
                    ),
                    bloqueante=True,
                    regra_origem=str(regra["id"]),
                    ghe_id=ctx.pgr_ghe.id,
                    exames_alvo=exames_alvo,
                )
            )
            continue

        if not resultado:
            continue

        nivel = _nivel_dispensa(regra, ctx)
        medicao: str | None = None
        if nivel is None and "mencao_documental" in regra:
            por_medicao = _dispensa_por_medicao(regra, ctx, protocolo.vocabulario.agentes)
            if por_medicao is not None:
                nivel, medicao = por_medicao
        if nivel is not None:
            ctx.observacoes.append(
                Observacao(
                    regra_id=str(regra["id"]),
                    regra_dispensa=str(regra["mencao_documental"]["regra"]),
                    agente=str(regra["quando"]),
                    nivel_risco=nivel,
                    exames_dispensados=tuple(str(item["exame"]) for item in regra["emite"]),
                    medicao=medicao,
                )
            )
            continue

        _emitir_regra(regra, ctx, protocolo, emitidos)

    return emitidos
