from __future__ import annotations

import dataclasses
from typing import Any

from agente_medico.motor.materialidade import materialidade
from agente_medico.motor.protocolo import Protocolo
from agente_medico.motor.tipos import GHEContext, Materialidade, Pendencia, Risco, TipoIBE


def stage_2_riscos(ctx: GHEContext, proto: Protocolo) -> None:
    agentes_vocab: dict[str, Any] = proto.vocabulario.agentes
    cargos_vocab: dict[str, Any] = proto.vocabulario.cargos

    # Fase A — hidratar riscos explícitos do PGR
    for risco_pgr in ctx.pgr_ghe.riscos:
        if risco_pgr.agente is None:
            # D-ARQ-51: termo não resolvido a slug (hidratação 1b) chega com agente=None.
            # Não promove a Risco (Risco.agente: str; inventar slug = D-ARQ-22) e NÃO bloqueia
            # (D-ARQ-14 + D-ARQ-50 P2: cauda não-resolvida é baixa-criticidade → revisão, não
            # erro silencioso). Assimetria intencional com o materialidade_ausente bloqueante do
            # lado-FDS (molde D-ARQ-29). Sem pendência nova: o None vem pareado com a
            # vocabulario_ausente que o resolver já emitiu na hidratação (invariante de 1b) —
            # evita o duplo de DT-003Y-01.
            continue
        meta = agentes_vocab.get(risco_pgr.agente)
        if meta is not None:
            ctx.riscos.append(
                Risco(
                    agente=risco_pgr.agente,
                    fonte="explicito",
                    detalhe=None,
                    quantificacao=risco_pgr.quantificacao,
                    tipo_ibe=TipoIBE(meta["tipo_ibe"]) if meta.get("tipo_ibe") else None,
                    is_ototoxico=meta.get("is_ototoxico", False),
                )
            )
        else:
            ctx.riscos.append(
                Risco(
                    agente=risco_pgr.agente,
                    fonte="explicito",
                    detalhe=None,
                    quantificacao=risco_pgr.quantificacao,
                    tipo_ibe=None,
                )
            )
            ctx.pendencias.append(
                Pendencia(
                    tipo="vocabulario_ausente",
                    destinatario="protocolo",
                    motivo=f"agente '{risco_pgr.agente}' ausente do vocabulário — hidratado com defaults",
                    bloqueante=False,
                    regra_origem=None,
                    ghe_id=ctx.pgr_ghe.id,
                )
            )

    # Fase B — expandir riscos implícitos por cargo (R-GHE-02)
    for cargo in ctx.pgr_ghe.cargos:
        cargo_meta = cargos_vocab.get(cargo)
        if cargo_meta is None:
            ctx.pendencias.append(
                Pendencia(
                    tipo="vocabulario_ausente",
                    destinatario="protocolo",
                    motivo=f"cargo '{cargo}' sem mapeamento de riscos implícitos no vocabulário",
                    bloqueante=False,
                    regra_origem="R-GHE-02",
                    ghe_id=ctx.pgr_ghe.id,
                )
            )
            continue

        for agente_implicito in cargo_meta.get("riscos_implicitos", []):
            idx = next(
                (i for i, r in enumerate(ctx.riscos) if r.agente == agente_implicito),
                None,
            )
            if idx is not None:
                existente = ctx.riscos[idx]
                novo_detalhe = (
                    f"também implícito pelo cargo {cargo}"
                    if existente.detalhe is None
                    else f"{existente.detalhe}; também implícito pelo cargo {cargo}"
                )
                ctx.riscos[idx] = dataclasses.replace(existente, detalhe=novo_detalhe)
            else:
                meta = agentes_vocab.get(agente_implicito)
                if meta is None:
                    ctx.pendencias.append(
                        Pendencia(
                            tipo="vocabulario_ausente",
                            destinatario="protocolo",
                            motivo=f"agente '{agente_implicito}' ausente do vocabulário — hidratado com defaults",
                            bloqueante=False,
                            regra_origem=None,
                            ghe_id=ctx.pgr_ghe.id,
                        )
                    )
                ctx.riscos.append(
                    Risco(
                        agente=agente_implicito,
                        fonte="implicito_cargo",
                        detalhe=f"derivado do cargo {cargo}",
                        quantificacao=None,
                        tipo_ibe=TipoIBE(meta["tipo_ibe"]) if meta is not None and meta.get("tipo_ibe") else None,
                        is_ototoxico=meta.get("is_ototoxico", False) if meta is not None else False,
                    )
                )

    # Fase C — promoção de componentes químicos de FDS (D-ARQ-35 Parte 3, 4ª fonte de risco).
    # Sem dedup: cada componente promovido vira um Risco próprio com
    # fonte="quimico_composicao", mesmo que o slug já exista em ctx.riscos por outra
    # fonte (D-ARQ-16 — convergência resolvida na consolidação, nunca por fusão de risco).
    for produto in ctx.pgr_ghe.produtos_quimicos:
        if produto.fds is None:
            continue
        for componente in produto.fds.composicao:
            if componente.agente is None:
                ctx.pendencias.append(
                    Pendencia(
                        tipo="materialidade_ausente",
                        destinatario="empresa",
                        motivo=f"componente '{componente.nome}' (produto {produto.nome}) sem slug resolvido — materialidade indeterminável",
                        bloqueante=True,
                        regra_origem="D-ARQ-35",
                        ghe_id=ctx.pgr_ghe.id,
                    )
                )
                continue

            mat = materialidade(componente)
            meta = agentes_vocab.get(componente.agente)
            if meta is None:
                ctx.pendencias.append(
                    Pendencia(
                        tipo="vocabulario_ausente",
                        destinatario="protocolo",
                        motivo=f"agente '{componente.agente}' ausente do vocabulário — hidratado com defaults",
                        bloqueante=False,
                        regra_origem=None,
                        ghe_id=ctx.pgr_ghe.id,
                    )
                )
            ctx.riscos.append(
                Risco(
                    agente=componente.agente,
                    fonte="quimico_composicao",
                    detalhe=f"componente {componente.nome} do produto {produto.nome}",
                    quantificacao=None,
                    tipo_ibe=TipoIBE(meta["tipo_ibe"]) if meta is not None and meta.get("tipo_ibe") else None,
                    is_ototoxico=meta.get("is_ototoxico", False) if meta is not None else False,
                    materialidade=mat,
                    is_carcinogeno_iarc=componente.is_carcinogeno_iarc,
                    is_sensibilizante=componente.is_sensibilizante,
                )
            )

            if mat == Materialidade.AUSENTE:
                ctx.pendencias.append(
                    Pendencia(
                        tipo="materialidade_ausente",
                        destinatario="empresa",
                        motivo=f"componente '{componente.nome}' (produto {produto.nome}) com slug resolvido mas materialidade indeterminada (concentração ausente ou cruzando o cutoff de 5%)",
                        bloqueante=True,
                        regra_origem="D-ARQ-35",
                        ghe_id=ctx.pgr_ghe.id,
                    )
                )
