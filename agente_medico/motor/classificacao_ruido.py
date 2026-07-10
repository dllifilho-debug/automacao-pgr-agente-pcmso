"""Classificação dB(A) -> relacao_LT para ruído (D-ARQ-51 fatia 3, R-RUIDO-01).

Regra R-RUIDO-01 (docs/PROTOCOLO_AGENTE_MEDICO.md v43, seção 5.2): partição
disjunta e exaustiva do NEN (Nível de Exposição Normalizado) medido em dB(A)
em relacao_LT, bordas inferiores inclusivas:
    valor < 80        -> "abaixo_acao"
    80 <= valor < 85   -> "entre_acao_LT"
    valor >= 85        -> "acima_LT"
Fontes normativas: 85 dB(A)/8h = Limite de Tolerância, NR-15 Anexo 1; 80 dB(A)
= nível de ação, NR-09 c/c NHO-01 (item literal da NR-09 incerto). Este
classificador NUNCA emite "acima_acao" — esse é sinônimo-legado aceito só
pelo predicado (predicados.py), não uma saída válida daqui.

Ressalva de escopo (DT-003CB-01, irmã de DT-002V-01): o tipo Quantificacao não
discrimina NEN de outras métricas em dB(A) (SPL instantâneo, nível de pico);
valor é assumido já como NEN pronto — quem monta o NEN a partir de medições de
troca (q de troca) é etapa a montante, fora deste módulo. Escopo limitado a
ruído contínuo/intermitente (NR-15 Anexo 1); ruído de impacto (NR-15 Anexo 2)
está fora de escopo desta regra.
"""
from __future__ import annotations

import dataclasses

from agente_medico.motor.tipos import Quantificacao

_LIMITE_TOLERANCIA = 85.0
_NIVEL_ACAO = 80.0


def classificar_ruido(q: Quantificacao) -> Quantificacao:
    """Aplica R-RUIDO-01: dB(A) -> relacao_LT (abaixo_acao/entre_acao_LT/acima_LT).

    Só classifica quando valor is not None, unidade == "dB(A)", not
    apenas_qualitativa e relacao_LT is None (idempotente — não sobrescreve
    classificação já presente). Fora dessas condições, retorna q inalterada.
    """
    if q.valor is None:
        return q
    if q.unidade != "dB(A)":
        return q
    if q.apenas_qualitativa:
        return q
    if q.relacao_LT is not None:
        return q

    if q.valor >= _LIMITE_TOLERANCIA:
        relacao_LT = "acima_LT"
    elif q.valor >= _NIVEL_ACAO:
        relacao_LT = "entre_acao_LT"
    else:
        relacao_LT = "abaixo_acao"

    return dataclasses.replace(q, relacao_LT=relacao_LT)
