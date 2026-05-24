from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from enum import Enum
from typing import Literal, Optional, Union


@dataclass(frozen=True)
class Quantificacao:
    valor: Optional[float]
    unidade: Optional[str]
    relacao_LT: Optional[str]
    pct_LT: Optional[float]
    apenas_qualitativa: bool


@dataclass(frozen=True)
class RiscoPGR:
    tipo: str
    agente: str
    quantificacao: Optional[Quantificacao]
    severidade: Optional[str]


@dataclass(frozen=True)
class Componente:
    cas: str
    nome: str
    concentracao: Optional[float]


@dataclass(frozen=True)
class FDS:
    composicao: tuple[Componente, ...]


@dataclass(frozen=True)
class ProdutoQuimico:
    nome: str
    fds: Optional[FDS]


@dataclass(frozen=True)
class GHEPGR:
    id: str
    nome: str
    cargos: tuple[str, ...]
    riscos: tuple[RiscoPGR, ...]
    epis: tuple[str, ...]
    produtos_quimicos: tuple[ProdutoQuimico, ...]
    psicossocial: bool


@dataclass(frozen=True)
class PGR:
    validade: date
    assinatura_engenheiro: bool
    ghes: tuple[GHEPGR, ...]


@dataclass(frozen=True)
class Risco:
    agente: str
    fonte: str
    detalhe: Optional[str]
    quantificacao: Optional[Quantificacao]
    anexo_nr07: Optional[str]
    is_ototoxico: bool = False


@dataclass(frozen=True)
class Ausente:
    mensagem: str


class Momento(Enum):
    ADM = "ADM"
    PER = "PER"
    MR = "MR"
    RT = "RT"
    DEM = "DEM"


@dataclass(frozen=True)
class Motivo:
    regra_id: str
    predicado: str
    risco_origem: Optional[str]
    detalhe: Optional[str]


@dataclass
class ExameEmitido:
    exame: str
    periodicidade_meses: int
    momentos: set[Momento] = field(default_factory=set)
    motivos: list[Motivo] = field(default_factory=list)


@dataclass(frozen=True)
class Pendencia:
    tipo: str
    destinatario: str
    motivo: str
    bloqueante: bool = False
    regra_origem: Optional[str] = None
    ghe_id: Optional[str] = None


@dataclass
class GHEContext:
    pgr_ghe: GHEPGR
    riscos: list[Risco] = field(default_factory=list)
    predicados: dict[str, Union[bool, Ausente]] = field(default_factory=dict)
    regime: Optional[str] = None
    pendencias: list[Pendencia] = field(default_factory=list)


@dataclass
class MatrizGHE:
    ghe_id: str
    linhas: list[ExameEmitido] = field(default_factory=list)
    pendencias: list[Pendencia] = field(default_factory=list)
    regime_aplicado: Optional[str] = None


@dataclass
class Resultado:
    status: Literal["OK", "PRELIMINAR", "REJEITADO"]
    matrizes: list[MatrizGHE] = field(default_factory=list)
    pendencias_globais: list[Pendencia] = field(default_factory=list)
    motivo_rejeicao: Optional[str] = None
