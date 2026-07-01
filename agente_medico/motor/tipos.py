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
    sem_avaliacao_quantitativa: bool = False
    pct_quartzo: Optional[float] = None  # denominador da fórmula do Anexo 12 NR-15 (D-ARQ-24 / R-RX-01)
    fracao: Optional[Fracao] = None  # R-RX-01 / D-ARQ-24: fração da medição (respirável/total), decide fórmula Anexo 12 NR-15


@dataclass(frozen=True)
class RiscoPGR:
    tipo: str
    agente: str
    quantificacao: Optional[Quantificacao]
    severidade: Optional[str]


@dataclass(frozen=True)
class FaixaConcentracao:
    # D-ARQ-34 Parte 1: composição da FDS é faixa, não escalar (ABNT NBR 14725 seção 3).
    # Sentinelas de leitura: minimo None -> piso 0; maximo None -> teto +inf.
    # Validação min<=max NÃO mora aqui (erro de integridade -> Stage 3 / D-ARQ-17).
    minimo: Optional[float]
    maximo: Optional[float]

    def piso_efetivo(self) -> float:
        return self.minimo if self.minimo is not None else 0.0

    def teto_efetivo(self) -> float:
        return self.maximo if self.maximo is not None else float("inf")


@dataclass(frozen=True)
class MembroVerbatim:
    cas: str
    nome: str


@dataclass(frozen=True)
class BlocoVerbatim:
    """D-ARQ-46 (refinado 003.AZ): verbatim cru AGRUPADO. Faixa única por bloco
    (medição 003.AY: no bloco 'Derivados de:' a faixa é escrita 1×). Singleton = bloco de 1 membro.
    Fronteira LLM↔determinístico. NÃO carrega FaixaConcentracao parseada, flags, explosão nem
    herança-α — tudo a jusante. Recorte A (D-ARQ-42 P3)."""
    faixa: str
    membros: tuple[MembroVerbatim, ...]


@dataclass(frozen=True)
class BlocoComponente:
    """Saída da montagem determinística, entrada da expansão-de-grupo (resolver,
    fatia ii). membros são Componente com concentracao=None: a herança-α da faixa do bloco é
    RESOLVER-SIDE (D-ARQ-45 P1/P2). concentracao do bloco = faixa parseada 1×."""
    concentracao: Optional[FaixaConcentracao]
    membros: tuple[Componente, ...]


@dataclass(frozen=True)
class Componente:
    cas: str
    nome: str
    concentracao: Optional[FaixaConcentracao] = None
    # D-ARQ-34 Parte 2/3: agente=None -> CAS válido mas slug não resolvido no vocabulário
    # (D-ARQ-14) -> ramo 0 do predicado de materialidade -> AUSENTE. Preenchido pela ficha
    # normalizada (D-ARQ-25 Parte B, extração futura). Flags de perigo (bypasses do cutoff
    # de 5%, R-FDS-03): default False, populadas pela ficha — NÃO desta fatia.
    agente: Optional[str] = None
    is_carcinogeno_iarc: bool = False
    is_sensibilizante: bool = False


@dataclass(frozen=True)
class FDS:
    composicao: tuple[Componente, ...]
    composicao_verbatim: tuple[BlocoComponente, ...] = ()


@dataclass(frozen=True)
class ProdutoQuimico:
    nome: str
    fds: Optional[FDS]


@dataclass(frozen=True)
class CenarioExposicao:
    # Dados fáticos do PGR por GHE; alimentam o LEO-resolver (D-ARQ-24).
    # Não carrega derivação normativa (ex.: é_mineração) — decidido downstream.
    cnae: Optional[str] = None
    atividade: Optional[str] = None
    local: Optional[str] = None


@dataclass(frozen=True)
class GHEPGR:
    id: str
    nome: str
    cargos: tuple[str, ...]
    riscos: tuple[RiscoPGR, ...]
    epis: tuple[str, ...]
    produtos_quimicos: tuple[ProdutoQuimico, ...]
    psicossocial: bool
    cenario: Optional[CenarioExposicao] = None  # contexto fático p/ LEO-resolver (D-ARQ-24)


@dataclass(frozen=True)
class PGR:
    validade: date
    assinatura_engenheiro: bool
    ghes: tuple[GHEPGR, ...]


class TipoIBE(Enum):
    EE = "EE"
    SC = "SC"


@dataclass(frozen=True)
class Risco:
    agente: str
    fonte: str
    detalhe: Optional[str]
    quantificacao: Optional[Quantificacao]
    tipo_ibe: Optional[TipoIBE]
    is_ototoxico: bool = False
    # D-ARQ-35 Parte 3: 4ª fonte de risco (químico de composição). materialidade = atributo
    # do risco, não filtro de existência. Flags de materialidade copiadas-pra-frente do
    # Componente (003.J).
    materialidade: Optional[Materialidade] = None
    is_carcinogeno_iarc: bool = False
    is_sensibilizante: bool = False


@dataclass(frozen=True)
class Ausente:
    mensagem: str


class Momento(Enum):
    ADM = "ADM"
    PER = "PER"
    MR = "MR"
    RT = "RT"
    DEM = "DEM"


class Fracao(Enum):
    RESPIRAVEL = "respiravel"
    TOTAL = "total"


class CenarioNormativo(Enum):
    MINERACAO = "mineracao"
    GERAL = "geral"


class Materialidade(Enum):
    MATERIAL = "MATERIAL"
    NAO_MATERIAL = "NAO_MATERIAL"
    AUSENTE = "AUSENTE"


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
    periodicidade_apos_15a: Optional[int] = None
    pendencias_anexadas: list[Pendencia] = field(default_factory=list)  # D-ARQ-31 fatia 3: pendência bloqueante que pode escalar a periodicidade desta linha


@dataclass(frozen=True)
class Pendencia:
    tipo: str
    destinatario: str
    motivo: str
    bloqueante: bool = False
    regra_origem: Optional[str] = None
    ghe_id: Optional[str] = None
    exames_alvo: tuple[str, ...] = ()  # D-ARQ-31 fatia 3: slugs que a pendência pode escalar; casa contra ExameEmitido.exame na anexação


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
    # D-ARQ-31: status tri-estado da matriz por-GHE. Campo inerte nesta fatia
    # (default VÁLIDA); produtor de status (PARCIAL/BLOQUEADA) entra na fatia 2
    # junto com o fim do zeramento de linhas no orquestrador.
    status: Literal["VÁLIDA", "PARCIAL", "BLOQUEADA"] = "VÁLIDA"


@dataclass
class Resultado:
    status: Literal["OK", "PRELIMINAR", "REJEITADO"]
    matrizes: list[MatrizGHE] = field(default_factory=list)
    pendencias_globais: list[Pendencia] = field(default_factory=list)
    motivo_rejeicao: Optional[str] = None
