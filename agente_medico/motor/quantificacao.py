"""Parse determinístico de RiscoVerbatim.quantificacao -> Quantificacao (D-ARQ-51 seam 4, fatia 2).

Resolver-side (mesma camada de transcricao_fds.parsear_faixa, cujo molde de
número BR este módulo replica localmente, sem importar — natureza distinta:
faixa de FDS é concentração de componente, quantificacao de GHE é medição
ambiental, camadas separadas). O texto cru sobrevive intocado em
RiscoVerbatim; este módulo só decide se ele é interpretável.
"""
from __future__ import annotations

import re
from typing import Optional

from agente_medico.motor.tipos import Quantificacao

_UNIDADES_NORMALIZADAS = {
    "db(a)": "dB(A)",
    "mg/m³": "mg/m3",
    "mg/m3": "mg/m3",
    "ppm": "ppm",
}

_PADRAO = re.compile(r"^(\S+)\s+(\S+)$")


def _texto_para_float(token: str) -> Optional[float]:
    token_normalizado = token.strip().replace(",", ".")
    if not token_normalizado:
        return None
    try:
        return float(token_normalizado)
    except ValueError:
        return None


def parsear_quantificacao(texto: str) -> Optional[Quantificacao]:
    """Parseia "<número BR> <unidade>" em Quantificacao (D-ARQ-51 seam 4 fatia 2).

    Unidade ∈ {dB(A), mg/m³, mg/m3, ppm} (formatos medidos no Viverde,
    docs/MAPA_GHE_VIVERDE.md); "mg/m³" e "mg/m3" normalizam para "mg/m3"
    (convenção fixture/predicados), "dB(A)" e "ppm" ficam literais. Número:
    vírgula BR -> ponto. Vazio/whitespace, número ilegível ou unidade fora do
    conjunto -> None. Não distingue ausente de ininteligível — quem distingue
    é o chamador (hidratar_ghe compara contra o texto cru original).

    Saída sempre com relacao_LT=None, pct_LT=None, apenas_qualitativa=False:
    classificação dB->relação é regra clínica não formalizada (fatia futura).
    """
    bruto = texto.strip()
    if not bruto:
        return None

    m = _PADRAO.match(bruto)
    if m is None:
        return None

    valor = _texto_para_float(m.group(1))
    if valor is None:
        return None

    unidade = _UNIDADES_NORMALIZADAS.get(m.group(2).casefold())
    if unidade is None:
        return None

    return Quantificacao(
        valor=valor,
        unidade=unidade,
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
    )
