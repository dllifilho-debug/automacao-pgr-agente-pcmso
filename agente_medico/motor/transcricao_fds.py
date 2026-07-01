from __future__ import annotations

import re
from collections.abc import Sequence
from typing import Optional

from agente_medico.motor.resolvedor import cas_bem_formado
from agente_medico.motor.tipos import (
    BlocoComponente,
    BlocoVerbatim,
    Componente,
    FaixaConcentracao,
    MembroVerbatim,
)

# [DERIVADO — DT-003AS-01 / D-ARQ-43 P2, medição 003.AN/AS; refinado 003.AZ]
# Camada de normalização determinística do verbatim de FDS, a montante de
# resolver_composicao (D-ARQ-42 camada-LLM). Funções puras, sem I/O, sem LLM.
# Fronteira é BlocoVerbatim (D-ARQ-46, refinado 003.AZ): o mecanismo \n-célula
# (003.AR) foi substituído por grupo verbatim explícito — o LLM-transcritor já
# entrega os N CAS de um bloco "Derivados de:" como membros separados, faixa
# escrita 1× por bloco. FRONTEIRA D-ARQ-45: _explodir_multi_cas (composicao.py)
# é INTOCADA — a expansão-de-grupo e a herança-α da faixa do bloco continuam
# sendo do resolvedor. Este módulo só conserta a quebra de render intra-token a
# montante, nunca decide expansão nem herança.

_GRAFIAS_CAS_AUSENTE = frozenset(
    {
        "vários",
        "nd",
        "na",
        "*",
        "**",
        "****",
        "segredo industrial",
        "informação confidencial",
    }
)


def desambiguar_cas(cas_bruto: str) -> str:
    """Decide, para cada '\\n' do CAS bruto, se é quebra-de-render intra-token
    (junta) ou separador multi-CAS legítimo (preserva).

    Critério (DT-003AS-01 patologia 3): preserva o '\\n' SÓ quando os dois
    fragmentos vizinhos são, cada um isoladamente, CAS bem-formado (reusa
    cas_bem_formado de resolvedor.py) — caso multi-CAS real (D-ARQ-45/003.AN:
    '2634-33-5\\n55965-84-9', dois CAS válidos empilhados). Em qualquer outro
    caso, junta os fragmentos (stripped, sem espaço).

    Não exige que a JUNÇÃO em si seja bem-formada: a FISPQ da tinta traz TiO₂
    com CAS já errado no próprio documento ('134363-67-7', falha o dígito
    verificador — D-ARQ-33 cl.3, ramo (c) do gate a jusante). A quebra ainda
    é intra-token (o fragmento '7' isolado nem chega a ter 5 dígitos para ser
    avaliável), e desfazê-la é operação de FORMA, não de validade — validade
    é exclusivamente assunto do gate_cas a jusante.
    """
    if "\n" not in cas_bruto:
        return cas_bruto

    partes = cas_bruto.split("\n")
    resultado = [partes[0]]
    for parte in partes[1:]:
        esquerda = resultado[-1].strip()
        direita = parte.strip()
        if cas_bem_formado(esquerda) and cas_bem_formado(direita):
            resultado.append(parte)
        else:
            resultado[-1] = esquerda + direita
    return "\n".join(resultado)


def normalizar_cas_ausente(cas_bruto: str) -> str:
    """Mapeia as grafias medidas de CAS-ausente para "" (convenção da fixture).

    Grafias medidas (DT-003AS-01 patologia 4): 'vários' (Ciplan), 'ND'/'NA'/
    '*'/'**'/'****' (Tigre/tinta), 'Segredo Industrial'/'Informação
    confidencial' (Leinertex/Massa). Mapa explícito, comparação por
    strip + casefold (case/acentuação tolerantes; sem regex solta). CAS real
    é preservado intocado (retorna o original, não o strip) quando não bate
    nenhuma grafia da lista.
    """
    candidato = cas_bruto.strip().casefold()
    if candidato in _GRAFIAS_CAS_AUSENTE:
        return ""
    return cas_bruto


_SEPARADOR_FAIXA = re.compile(r"[-–]")


def _texto_para_float(token: str) -> Optional[float]:
    token_normalizado = token.strip().replace(",", ".")
    if not token_normalizado:
        return None
    try:
        return float(token_normalizado)
    except ValueError:
        return None


def parsear_faixa(texto: str) -> Optional[FaixaConcentracao]:
    """Parseia o texto bruto da faixa de concentração em FaixaConcentracao,
    SEM ordenar (a ordenação min/max é do resolvedor — _normalizar_faixa,
    003.AP; não duplicada aqui).

    Separadores: hífen '-' e en-dash '–' (DT-003AS-01 patologia 5). Decimal
    BR vírgula -> ponto. Piso textual "00" cai em float("00") = 0.0 sem
    tratamento especial. Semi-abertas (D-ARQ-34 P1): '< 5' -> (None, 5.0);
    '> 1' -> (1.0, None). Vazio ou ininteligível -> None.

    Âncoras (D-ARQ-43 P2, medição 003.AN/AS): '0,2 – 0,05' -> (0.2, 0.05);
    '00 – 10' -> (0.0, 10.0); '00 – 0,5' -> (0.0, 0.5);
    '0,01 – 0,008' -> (0.01, 0.008) — pares invertidos saem invertidos.
    """
    bruto = texto.strip()
    if not bruto:
        return None

    if bruto.startswith("<"):
        teto = _texto_para_float(bruto[1:])
        if teto is None:
            return None
        return FaixaConcentracao(minimo=None, maximo=teto)

    if bruto.startswith(">"):
        piso = _texto_para_float(bruto[1:])
        if piso is None:
            return None
        return FaixaConcentracao(minimo=piso, maximo=None)

    partes = _SEPARADOR_FAIXA.split(bruto, maxsplit=1)
    if len(partes) != 2:
        return None

    minimo = _texto_para_float(partes[0])
    maximo = _texto_para_float(partes[1])
    if minimo is None or maximo is None:
        return None
    return FaixaConcentracao(minimo=minimo, maximo=maximo)


def _montar_membro(m: MembroVerbatim) -> Componente:
    """Monta um Componente determinístico a partir de um membro-verbatim (D-ARQ-46 Parte 4).

    Montagem 1→1: P3 (desambiguar_cas) → P4 (normalizar_cas_ausente) no cas cru, strip no
    nome. concentracao=None: a faixa é do bloco (herança-α é resolver-side, D-ARQ-45 P1/P2).
    agente=None e flags de perigo no default (recorte A, D-ARQ-42 Parte 3).
    """
    cas = normalizar_cas_ausente(desambiguar_cas(m.cas))
    return Componente(cas=cas, nome=m.nome.strip())


def montar_bloco(bloco: BlocoVerbatim) -> BlocoComponente:
    """Monta um BlocoComponente a partir de um BlocoVerbatim (D-ARQ-46, refinado 003.AZ).

    Faixa parseada 1× por bloco (P5); NÃO explode (D-ARQ-45 P1), NÃO ordena (003.AP),
    NÃO aplica a faixa aos membros — expansão-de-grupo e herança-α ficam no resolver
    (fatia ii). Cada membro é montado 1→1 por _montar_membro.
    """
    return BlocoComponente(
        concentracao=parsear_faixa(bloco.faixa),
        membros=tuple(_montar_membro(m) for m in bloco.membros),
    )


def montar_composicao(blocos: Sequence[BlocoVerbatim]) -> tuple[BlocoComponente, ...]:
    """FDS inteira: sequência de blocos-verbatim → tuple[BlocoComponente, ...]
    (D-ARQ-46 Parte 2/4, refinado 003.AZ).

    Saída do LLM-transcritor (mockado nesta fatia) montada 1→1 por bloco; expansão-de-grupo
    e herança-α ficam no resolver (resolver_composicao), que consome esta tupla.
    """
    return tuple(montar_bloco(b) for b in blocos)
