from __future__ import annotations

from agente_medico.motor.tipos import Componente, Materialidade


def materialidade(componente: Componente) -> Materialidade:
    """Predicado tri-estado de materialidade do lado-engenheiro.

    R-FDS-03 / D-ARQ-34 Parte 2. Função pura (faixa, flags) -> estado.
    Pré-condição (não é ramo): CAS válido pelo dígito verificador é gate do motor
    irmão (D-ARQ-33 cl.3), a montante — o componente que chega aqui já passou.
    """
    # Ramo 1 (bypass): qualquer bypass do cutoff True -> MATERIAL, independe de
    # concentração (inclusive concentracao=None) e independe de slug (D-ARQ-56 +
    # DT-003M-01): a flag agora vem da FDS via frases_h (D-ARQ-55), não do slug;
    # honrada mesmo com agente=None (CAS oculto). Bypasses = lista append-only
    # (D-ARQ-33 cl.5).
    if componente.is_carcinogeno_iarc or componente.is_sensibilizante:
        return Materialidade.MATERIAL

    # Ramo 0: sem slug E sem flag de bypass (D-ARQ-14). Sem slug não há flags
    # confiáveis por si só; não decidir NÃO-MATERIAL por concentração (carcinógeno
    # desconhecido <5% viraria supressão silenciosa — D-ARQ-22). is_carcinogeno_iarc
    # continua slug-dependente (DT-003CI-01) — decidir por concentração aqui seria
    # supressão D-ARQ-22.
    if componente.agente is None:
        return Materialidade.AUSENTE

    faixa = componente.concentracao
    # Ramo 2: sem bypass e concentração não extraída -> AUSENTE.
    if faixa is None:
        return Materialidade.AUSENTE

    piso = faixa.piso_efetivo()
    teto = faixa.teto_efetivo()

    # Ramo 3: faixa cruza o cutoff (straddle) -> AUSENTE/Pendencia (D-ARQ-33 cl.3).
    if piso <= 5.0 < teto:
        return Materialidade.AUSENTE
    # Ramo 4: faixa inteira acima do cutoff -> MATERIAL.
    if piso > 5.0:
        return Materialidade.MATERIAL
    # Ramo 5: faixa inteira no cutoff ou abaixo -> NÃO-MATERIAL.
    # Borda 5,0 exata: R-FDS-03 diz "> 5%", logo 5,0 é não-material (min>5 estrito,
    # max<=5 inclusivo). [INTERPRETADO — DT-FDS-02] enquanto a unidade do cutoff
    # (% m/m vs v/v, ABNT NBR 14725) não for confirmada.
    return Materialidade.NAO_MATERIAL
