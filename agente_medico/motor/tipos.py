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
    # D-ARQ-51: None = termo não resolvido a slug pela hidratação (D-ARQ-50 P2 / D-ARQ-14).
    # Espelha Componente.agente: Optional[str]. Risco NUNCA descartado; None vira revisão, não slug inventado (D-ARQ-22).
    agente: Optional[str]
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
    # H-codes GHS transcritos VERBATIM por membro, sem classificar — D-ARQ-55 P1;
    # () = FDS declarou sem H-phrase para o membro.
    frases_h: tuple[str, ...] = ()


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
    # H-code cru sobrevive à montagem espelhando cas — D-ARQ-55 P1; anti-supressão
    # D-ARQ-22 (H-code não-mapeado não some).
    frases_h: tuple[str, ...] = ()


@dataclass(frozen=True)
class RiscoVerbatim:
    """Risco cru transcrito do bloco GHE (D-ARQ-49 P3: semântica cravada — termos
    crus, sem slug, quantificação NÃO normalizada). agente = termo com normalização
    linguística bounded do LLM (D-ARQ-50 P2: tira qualificador, quebra composto,
    corrige typo óbvio — NUNCA emite slug); quantificacao = texto como transcrito
    ("82,2 dB(A)", "6,3 ppm"; "" se qualitativo/ausente) — parse é resolver-side,
    fatia futura; fonte_geradora = texto cru da coluna homônima ("" se ausente) —
    carrega a FDS-apontada de D-ARQ-49 P2 (produto: "Thinner/Zarcão"), que alimenta
    a cadeia química existente a jusante, não a reconstrói. Multi-agente sob o mesmo
    ET (D-ARQ-50 C3) vira riscos separados com fonte_geradora copiada — cópia, não
    perda; nenhum campo é herdado entre riscos (difere de BlocoVerbatim/FDS, onde a
    faixa 1× por bloco exigia grupo)."""
    agente: str
    quantificacao: str
    fonte_geradora: str


@dataclass(frozen=True)
class GHEVerbatim:
    """Bloco GHE transcrito — a "PGR transcrita" da 1ª fatia (esqueleto, D-ARQ-49 P2).
    Fronteira LLM↔determinístico do lado-PGR (D-ARQ-41). nome = setor/função cru da
    linha-âncora ("Estrutura de concreto armado"); cargos = crus, separados da âncora
    pelo LLM (leitura bounded, D-ARQ-50 C3). SEM campo id: o documento não traz id de
    GHE (ids canônicos da fixture vêm do MAPA, re-agrupamento humano — D-ARQ-50 C1);
    LLM atribuir id seria escolha de identidade silenciosa (classe D-ARQ-22) — id é
    atribuição a jusante. FICAM FORA (diferidos, D-ARQ-49 P2): EPIs, psicossocial,
    campos-de-topo de gate. NÃO é tipos.PGR nem GHEPGR — conversão termo→slug é do
    resolvedor, fatia futura (D-ARQ-50 P2)."""
    nome: str
    cargos: tuple[str, ...]
    riscos: tuple[RiscoVerbatim, ...]


@dataclass(frozen=True)
class EnvelopeVerbatim:
    """Envelope do topo transcrito — instância-envelope de D-ARQ-41 (D-ARQ-53
    P3: semântica cravada — texto CRU, sem `date`, sem `bool`, sem juízo de
    "engenheiro vs. técnico"). validade_textos = candidatas CRUAS na ordem do
    documento — plural porque a medição 003.BV achou 3 candidatas mês-ano no
    topo Viverde (emissão + 2 atualizações); a política "mais recente" é
    RESOLVER-SIDE (fatia 3), não transcrição. responsavel_tecnico/titulo_rt/
    registro_profissional = texto cru da linha-âncora "RESPONSABILIDADE
    TÉCNICA" ("" se ausente; achado 003.BW: no Viverde a camada de texto
    traz o typo de origem "TÉNICA", sem o C — âncora de fatia 3 não pode
    exigir match exato do título); registro_profissional é texto cru — não
    assume CREA (universalidade NR-01, outros conselhos possíveis). SEM
    campo de assinatura: a assinatura no topo Viverde é IMAGEM (003.BV) —
    o `bool` de R-PGR-01 é 100% CONFIRMAÇÃO-RT (D-ARQ-53 P2), não
    text-derivable. Consumidores finais R-PGR-01/R-PGR-06 só via
    confirmação-RT (molde revisão-RT D-ARQ-47 cl.4), fatia 3."""
    validade_textos: tuple[str, ...]
    responsavel_tecnico: str
    titulo_rt: str
    registro_profissional: str


@dataclass(frozen=True)
class CandidataValidade:
    """Candidata crua de validade + resolução determinística (D-ARQ-53 P3).
    texto = elemento cru de EnvelopeVerbatim.validade_textos; data = resolução
    mês-ano PT-BR (resolvedor_topo.py), ou None quando não-parseável nesta
    fatia. data=None NÃO bloqueia — a decisão final é da confirmação-RT
    (DT-003BV-01), não deste tipo."""
    texto: str
    data: Optional[date]


@dataclass(frozen=True)
class EnvelopeConfirmado:
    """Saída da confirmação-RT do envelope (molde revisão-RT D-ARQ-47 cl.4,
    D-ARQ-53 P2/P3): exatamente os dois parâmetros hoje RT-supplied de
    processar_arquivo_pgr (troca de origem é fatia 4). Consumidores:
    R-PGR-01/R-PGR-06 (estagios/gates.py)."""
    validade: date
    assinatura_engenheiro: bool


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
    # D-ARQ-22 Parte B: rastreabilidade do exame emitido — regra de origem,
    # gatilho e status de validação. riscos_resolvidos espelha ctx.riscos
    # (slugs resolvidos para o GHE); predicados_avaliados espelha ctx.predicados
    # (cache nome→valor populado por avaliar_predicado), serializado para diagnóstico.
    riscos_resolvidos: tuple[str, ...] = ()
    predicados_avaliados: tuple[tuple[str, str], ...] = ()


@dataclass
class Resultado:
    status: Literal["OK", "PRELIMINAR", "REJEITADO"]
    matrizes: list[MatrizGHE] = field(default_factory=list)
    pendencias_globais: list[Pendencia] = field(default_factory=list)
    motivo_rejeicao: Optional[str] = None
