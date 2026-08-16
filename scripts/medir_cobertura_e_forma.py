"""Instrumento de medição (003.EY fatia 0): duas perguntas sobre os gabaritos
humanos, respondidas na mesma varredura de tabela. Não é código de produção
— nenhuma regra clínica é lida ou alterada aqui, `regras.yaml` e
`exames.yaml` não são tocados (só lidos, para nomear exames).

Pergunta A (reconciliação, `R-AUD-04` × `docs/PLANO_V1.md:258-259`): em cada
gabarito, que fração das linhas de cargo recebe audiometria?

Pergunta B (insumo `DT-003EW-02`): em cada gabarito, quais exames trazem o
número de meses impresso na célula, com qual valor e em qual forma?

Reuso obrigatório (D-ARQ-67), por import, nunca redigitado:
- `_ROTULO_MOMENTO` de `agente_medico/superficie/documento_matriz.py`
  (invertido para rótulo->Momento), via `scripts.medir_audiometria_dem`;
- de `scripts/medir_audiometria_dem.py`: `parsear_momentos`,
  `rotulos_nao_reconhecidos`, `_linha_e_cargo`, `_cargo_para_exibicao` — a
  lista mínima do prompt — e, adicionalmente (mesma classe de reuso,
  declarado aqui por transparência): `_extrair_linha_audiometria` e
  `_PADRAO_GHE`, porque redigitá-los para rastrear GHE atual e isolar a
  linha de audiometria repetiria exatamente o código que D-ARQ-67 proíbe
  duplicar; `_celulas_logicas` também, desde 003.EZ fatia 0 (DH-003EY-01), e
  `_PADRAO_MESES` desde 003.EZ fatia 0b — as duas definições migraram para
  `medir_audiometria_dem.py` (módulo a montante, evita import circular),
  este módulo importa em vez de manter cópia.

Duas armadilhas medidas em 003.EX ao generalizar de "audiometria" para
"qualquer exame" — nenhuma vira descarte silencioso (`DH-003EX-01`):
1. célula com 3+ grupos entre parênteses para o mesmo exame é reportada como
   forma anômala, nunca truncada para os 2 primeiros em silêncio;
2. parêntese de abertura ausente (ex.: "Avaliação Psicossocial ADM, PER,
   MRO)") é reportado como forma anômala própria (`sem_parentese`), não
   engolido.
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml
from docx import Document

from agente_medico.motor.tipos import Momento
from scripts.medir_audiometria_dem import (
    _PADRAO_GHE,
    _PADRAO_MESES,
    _cargo_para_exibicao,
    _celulas_logicas,
    _extrair_linha_audiometria,
    _linha_e_cargo,
    parsear_momentos,
    rotulos_nao_reconhecidos,
)

_CAMINHO_EXAMES_YAML = (
    Path(__file__).resolve().parent.parent
    / "agente_medico"
    / "protocolo"
    / "vocabulario"
    / "exames.yaml"
)

_PADRAO_GRUPO_PARENTESE = re.compile(r"\(([^)]*)\)")
_PADRAO_SETOR = re.compile(r"^SETOR\s*:?", re.IGNORECASE)


FORMA_INLINE = "inline"
FORMA_GRUPO_SEPARADO = "grupo_separado"
FORMA_SEM_NUMERO = "sem_numero"
FORMA_ANOMALA = "anomala"
FORMA_SEM_PARENTESE = "sem_parentese"


def _normalizar(texto: str) -> str:
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(c for c in sem_acento if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sem_acento).strip().casefold()


def carregar_mapa_nome_para_slug(caminho: Path = _CAMINHO_EXAMES_YAML) -> dict[str, str]:
    with caminho.open(encoding="utf-8") as f:
        dados = yaml.safe_load(f)
    exames: dict[str, Any] = dados["exames"]
    return {
        _normalizar(info["nome_exibicao"]): slug
        for slug, info in exames.items()
        if isinstance(info, dict) and "nome_exibicao" in info
    }


def _extrair_meses(texto: str) -> int | None:
    match = _PADRAO_MESES.search(texto)
    return int(match.group(1)) if match else None


@dataclass(frozen=True)
class FormaPeriodicidade:
    nome_bruto: str
    exame: str  # slug quando reconhecido no vocabulário; senão, nome normalizado
    meses: int | None
    forma: str
    momentos: frozenset[Momento] = field(default_factory=frozenset)
    texto_bruto: str = ""


def extrair_forma_periodicidade(
    segmento: str, mapa_nomes: dict[str, str] | None = None
) -> FormaPeriodicidade:
    """Analisa um segmento já isolado a um único exame (nome + até N grupos
    entre parênteses) e devolve exame/meses/forma. Generaliza
    `_extrair_linha_audiometria` (que isola o segmento) para qualquer exame:
    esta função assume o isolamento já feito, mesma divisão de
    responsabilidade do script herdado.
    """
    mapa_nomes = mapa_nomes or {}
    grupos = _PADRAO_GRUPO_PARENTESE.findall(segmento)
    fim_nome = segmento.find("(")
    nome_bruto = (segmento if fim_nome == -1 else segmento[:fim_nome]).strip(" \n\t;,.")
    nome_normalizado = _normalizar(nome_bruto)
    exame = mapa_nomes.get(nome_normalizado, nome_normalizado)

    if not grupos:
        return FormaPeriodicidade(
            nome_bruto, exame, None, FORMA_SEM_PARENTESE, frozenset(), segmento.strip()
        )
    if len(grupos) >= 3:
        return FormaPeriodicidade(
            nome_bruto, exame, None, FORMA_ANOMALA, frozenset(), segmento.strip()
        )

    momentos = parsear_momentos(segmento)
    if len(grupos) == 1:
        meses = _extrair_meses(grupos[0])
        forma = FORMA_INLINE if meses is not None else FORMA_SEM_NUMERO
        return FormaPeriodicidade(nome_bruto, exame, meses, forma, momentos, segmento.strip())

    # len(grupos) == 2: primeiro grupo é o candidato a periodicidade separada.
    meses = _extrair_meses(grupos[0])
    return FormaPeriodicidade(
        nome_bruto, exame, meses, FORMA_GRUPO_SEPARADO, momentos, segmento.strip()
    )


def segmentar_exames(texto_celula: str) -> list[str]:
    """Divide o texto de uma célula "EXAMES SOLICITADOS" em segmentos, um por
    exame — nome + os grupos entre parênteses que imediatamente o seguem
    (separados só por espaço/vírgula, sem texto de outro nome entre eles).
    Generaliza a captura de `_extrair_linha_audiometria` (que faz o mesmo
    só para o trecho após "Audiometria") para a célula inteira, com
    qualquer exame.

    Texto sem nenhum parêntese (armadilha do parêntese de abertura ausente,
    medida no SPE 0030) sai como segmento próprio — `extrair_forma_periodicidade`
    o classifica como `sem_parentese`, não descarta.
    """
    grupos = list(_PADRAO_GRUPO_PARENTESE.finditer(texto_celula))
    segmentos: list[str] = []
    pos = 0
    i = 0
    while i < len(grupos):
        # Região de nome antes deste grupo: pode conter um ')' solto de um
        # exame anterior com parêntese de abertura ausente (ex.: "Avaliação
        # Psicossocial ADM, PER, MRO)" colado ao nome do exame seguinte). O
        # ')' solto vira segmento próprio (sem_parentese); só o texto depois
        # dele é o nome real do exame deste grupo.
        regiao_nome = texto_celula[pos : grupos[i].start()]
        idx_parentese_solto = regiao_nome.rfind(")")
        if idx_parentese_solto != -1:
            quebrado = regiao_nome[: idx_parentese_solto + 1].strip(" \n\t;,.")
            if quebrado:
                segmentos.append(quebrado)
            inicio_segmento = pos + idx_parentese_solto + 1
        else:
            inicio_segmento = pos
        j = i
        fim_cluster = grupos[i].end()
        while j + 1 < len(grupos):
            entre = texto_celula[grupos[j].end() : grupos[j + 1].start()]
            if re.fullmatch(r"[\s,]*", entre):
                j += 1
                fim_cluster = grupos[j].end()
            else:
                break
        segmento = texto_celula[inicio_segmento:fim_cluster].strip(" \n\t;,.")
        if segmento:
            segmentos.append(segmento)
        pos = fim_cluster
        i = j + 1
    resto = texto_celula[pos:]
    idx_parentese_solto = resto.rfind(")")
    if idx_parentese_solto != -1:
        quebrado = resto[: idx_parentese_solto + 1].strip(" \n\t;,.")
        if quebrado:
            segmentos.append(quebrado)
        resto_final = resto[idx_parentese_solto + 1 :].strip(" \n\t;,.")
    else:
        resto_final = resto.strip(" \n\t;,.")
    if resto_final:
        segmentos.append(resto_final)
    return segmentos


@dataclass(frozen=True)
class RegistroCargoCompleto:
    ghe: str
    cargo: str
    tem_audiometria: bool
    momentos_audiometria: frozenset[Momento]
    rotulos_nao_reconhecidos_audiometria: frozenset[str]
    formas: tuple[FormaPeriodicidade, ...]


def extrair_registros_completos(
    caminho: Path, mapa_nomes: dict[str, str] | None = None
) -> tuple[list[RegistroCargoCompleto], list[str]]:
    documento = Document(str(caminho))
    registros: list[RegistroCargoCompleto] = []
    suspeitas: list[str] = []
    ghe_atual = "(sem agrupamento GHE)"
    for tabela in documento.tables:
        for linha in tabela.rows:
            celulas_logicas = _celulas_logicas(linha.cells)
            cargo = celulas_logicas[0].strip() if celulas_logicas else ""
            if _PADRAO_GHE.match(cargo) or _PADRAO_SETOR.match(cargo):
                ghe_atual = re.sub(r"\s+", " ", cargo)
                continue
            if not _linha_e_cargo(cargo) or len(celulas_logicas) < 2:
                continue
            texto_celula = celulas_logicas[1]

            linha_audio = _extrair_linha_audiometria(texto_celula)
            if linha_audio is None:
                tem_audio = False
                momentos_audio: frozenset[Momento] = frozenset()
                desconhecidos: frozenset[str] = frozenset()
            else:
                tem_audio = True
                momentos_audio = parsear_momentos(linha_audio)
                desconhecidos = rotulos_nao_reconhecidos(linha_audio)
                if desconhecidos:
                    suspeitas.append(
                        f"[{ghe_atual}] {cargo}: rótulo(s) não reconhecido(s) "
                        f"{sorted(desconhecidos)} em {linha_audio!r}"
                    )

            formas = tuple(
                extrair_forma_periodicidade(seg, mapa_nomes)
                for seg in segmentar_exames(texto_celula)
            )

            registros.append(
                RegistroCargoCompleto(
                    ghe_atual, cargo, tem_audio, momentos_audio, desconhecidos, formas
                )
            )
    return registros, suspeitas


@dataclass(frozen=True)
class CoberturaDocumento:
    nome_doc: str
    n_cargos: int
    n_com_audiometria: int
    cargos_sem_audiometria: tuple[str, ...]

    @property
    def fracao(self) -> float:
        if self.n_cargos == 0:
            return 0.0
        return self.n_com_audiometria / self.n_cargos

    @property
    def universal(self) -> bool:
        return self.n_cargos > 0 and self.fracao == 1.0


def medir_cobertura(nome_doc: str, registros: list[RegistroCargoCompleto]) -> CoberturaDocumento:
    com_audio = [r for r in registros if r.tem_audiometria]
    sem_audio = [r for r in registros if not r.tem_audiometria]
    return CoberturaDocumento(
        nome_doc=nome_doc,
        n_cargos=len(registros),
        n_com_audiometria=len(com_audio),
        cargos_sem_audiometria=tuple(
            f"[{r.ghe}] {_cargo_para_exibicao(r.cargo)}" for r in sem_audio
        ),
    )


def classificar_momento_dem(
    registros: list[RegistroCargoCompleto],
) -> tuple[list[RegistroCargoCompleto], list[RegistroCargoCompleto], list[RegistroCargoCompleto]]:
    """Separa os cargos com audiometria em três baldes, nunca dois — mesma
    regra de `scripts.medir_audiometria_dem.classificar_dem`, adaptada ao
    campo `rotulos_nao_reconhecidos_audiometria` de `RegistroCargoCompleto`
    (nome de atributo diferente do `RegistroCargo` de origem, por isso não é
    diretamente importável sob D-ARQ-67). Célula com rótulo não reconhecido
    na própria linha de audiometria não é negativa — é ilegível, e ilegível
    tem balde próprio (`indeterminado`), nunca cai em `sem_dem` por omissão
    (D-ARQ-13 aplicado fora do motor: ausência de leitura não é negação de
    conduta — achado nomeado em 003.EX/003.EY, generalizado aqui). A
    presença de `DEM` vence a ambiguidade do resto da célula: um cargo com
    `DEM` e um rótulo não reconhecido no mesmo grupo cai em `com_dem`, não em
    `indeterminado`.
    """
    com_audio = [r for r in registros if r.tem_audiometria]
    com_dem = [r for r in com_audio if Momento.DEM in r.momentos_audiometria]
    sem_dem = [
        r
        for r in com_audio
        if Momento.DEM not in r.momentos_audiometria
        and not r.rotulos_nao_reconhecidos_audiometria
    ]
    indeterminado = [
        r
        for r in com_audio
        if Momento.DEM not in r.momentos_audiometria and r.rotulos_nao_reconhecidos_audiometria
    ]
    return com_dem, sem_dem, indeterminado


@dataclass(frozen=True)
class MomentoDemDocumento:
    nome_doc: str
    n_com_dem: int
    n_sem_dem: int
    n_indeterminado: int
    cargos_indeterminados: tuple[str, ...]


def medir_momento_dem(
    nome_doc: str, registros: list[RegistroCargoCompleto]
) -> MomentoDemDocumento:
    com_dem, sem_dem, indeterminado = classificar_momento_dem(registros)
    return MomentoDemDocumento(
        nome_doc=nome_doc,
        n_com_dem=len(com_dem),
        n_sem_dem=len(sem_dem),
        n_indeterminado=len(indeterminado),
        cargos_indeterminados=tuple(
            f"[{r.ghe}] {_cargo_para_exibicao(r.cargo)}" for r in indeterminado
        ),
    )


@dataclass(frozen=True)
class AgregadoUniversalidade:
    total: int
    piso: int
    universais_bruto: int
    universais_com_piso: int


def agregar_universalidade(
    coberturas: dict[str, CoberturaDocumento], piso: int
) -> AgregadoUniversalidade:
    """Piso é escolha editorial, não medição (`DH-003EY-02`) — sai sempre
    declarado ao lado do agregado, nunca calculado à mão a partir da tabela
    bruta.
    """
    universais = [c for c in coberturas.values() if c.universal]
    com_piso = [c for c in universais if c.n_cargos >= piso]
    return AgregadoUniversalidade(
        total=len(coberturas),
        piso=piso,
        universais_bruto=len(universais),
        universais_com_piso=len(com_piso),
    )


_RX_TORAX_SLUG = "rx_torax_oit"


def confere_regra_003eo(formas: list[FormaPeriodicidade]) -> tuple[list[str], list[str]]:
    """Regra de 003.EO: o número só aparece impresso quando a periodicidade
    é != 12M, exceto RX Tórax OIT, que sempre traz. Devolve (confirmam,
    contrariam), cada item um texto nomeável (exame + doc + valor).
    """
    confirmam: list[str] = []
    contrariam: list[str] = []
    for f in formas:
        if f.forma not in (FORMA_INLINE, FORMA_GRUPO_SEPARADO, FORMA_SEM_NUMERO):
            continue  # anômala/sem_parentese não participam do teste de regra
        tem_numero = f.meses is not None
        e_rx_torax = f.exame == _RX_TORAX_SLUG
        descricao = f"{f.exame} ({f.nome_bruto!r}): meses={f.meses}, forma={f.forma}"
        if e_rx_torax:
            (confirmam if tem_numero else contrariam).append(descricao)
        else:
            if tem_numero and f.meses == 12:
                contrariam.append(descricao)
            else:
                confirmam.append(descricao)
    return confirmam, contrariam


_PADRAO_SUFIXO_COPIA = re.compile(r"\s*\(\d+\)(?=\.\w+$|$)")


def chave_obra(nome_arquivo: str) -> str:
    """Normaliza o nome do arquivo para agrupar cópias da mesma obra: remove
    sufixo numérico entre parênteses (`" (1)"`, `" (2)"`) e a extensão.
    Regra do Arquiteto (EMENDA 2): cópias são o mesmo documento quando têm
    mesma obra e mesma data no nome — na prática do acervo, isso é o nome do
    arquivo sem o sufixo de cópia.
    """
    sem_extensao = re.sub(r"\.docx?$", "", nome_arquivo, flags=re.IGNORECASE)
    return _PADRAO_SUFIXO_COPIA.sub("", sem_extensao).strip()


def agrupar_por_obra(nomes: list[str]) -> dict[str, list[str]]:
    grupos: dict[str, list[str]] = {}
    for nome in nomes:
        grupos.setdefault(chave_obra(nome), []).append(nome)
    return grupos


@dataclass(frozen=True)
class ColapsoObra:
    chave: str
    membros: tuple[str, ...]
    canonico: str
    status: str


def selecionar_canonico(coberturas: dict[str, CoberturaDocumento]) -> list[ColapsoObra]:
    """Escolhe a cópia de referência de cada obra pela regra do Arquiteto: a
    mais completa (a que não perde linha de exame por truncamento — critério
    aplicado ao par RESERVA, onde a `(1)` corrige o SERRALHEIRO truncado na
    base). Completude é medida em duas etapas — mais cargos captados, e
    entre esses, mais cargos com audiometria — porque um truncamento de
    tabela perde cargos inteiros antes de perder só a linha de audiometria
    de um cargo presente. Se as duas métricas discordarem entre membros (uma
    cópia com mais cargos, outra com mais audiometria), não há "mais
    completa" — reporta `colapso indeciso`, não escolhe.
    """
    grupos = agrupar_por_obra(list(coberturas.keys()))
    resultado: list[ColapsoObra] = []
    for chave, membros in grupos.items():
        if len(membros) == 1:
            resultado.append(ColapsoObra(chave, tuple(membros), membros[0], "único"))
            continue
        max_cargos = max(coberturas[m].n_cargos for m in membros)
        no_topo_cargos = [m for m in membros if coberturas[m].n_cargos == max_cargos]
        max_audio_no_topo = max(coberturas[m].n_com_audiometria for m in no_topo_cargos)
        fora_do_topo_supera_audio = any(
            coberturas[m].n_com_audiometria > max_audio_no_topo
            for m in membros
            if m not in no_topo_cargos
        )
        if fora_do_topo_supera_audio:
            resultado.append(ColapsoObra(chave, tuple(sorted(membros)), sorted(membros)[0], "colapso indeciso"))
            continue
        candidatos = sorted(m for m in no_topo_cargos if coberturas[m].n_com_audiometria == max_audio_no_topo)
        if len(candidatos) == 1:
            status = "completude estrita"
        else:
            status = "empate — escolha arbitrária, cobertura idêntica"
        resultado.append(ColapsoObra(chave, tuple(sorted(membros)), candidatos[0], status))
    return resultado


def gerar_relatorio(caminhos: list[Path], mapa_nomes: dict[str, str], piso: int = 17) -> str:
    coberturas: dict[str, CoberturaDocumento] = {}
    momentos_por_doc: dict[str, MomentoDemDocumento] = {}
    todas_formas: dict[str, list[FormaPeriodicidade]] = {}
    todas_suspeitas: dict[str, list[str]] = {}
    anomalias: list[tuple[str, str, FormaPeriodicidade]] = []

    for caminho in caminhos:
        registros, suspeitas = extrair_registros_completos(caminho, mapa_nomes)
        coberturas[caminho.name] = medir_cobertura(caminho.name, registros)
        momentos_por_doc[caminho.name] = medir_momento_dem(caminho.name, registros)
        formas_doc: list[FormaPeriodicidade] = []
        for r in registros:
            for f in r.formas:
                formas_doc.append(f)
                if f.forma in (FORMA_ANOMALA, FORMA_SEM_PARENTESE):
                    anomalias.append((caminho.name, _cargo_para_exibicao(r.cargo), f))
        todas_formas[caminho.name] = formas_doc
        todas_suspeitas[caminho.name] = suspeitas

    colapsos = selecionar_canonico(coberturas)
    canonicos = {c.canonico for c in colapsos}

    linhas: list[str] = [
        "# Cobertura de audiometria e forma da periodicidade — 003.EY",
        "",
        "## Bloco A — cobertura de audiometria",
        "",
        "### Denominador bruto (26 arquivos, um por arquivo)",
        "",
        "| Arquivo | n_cargos | n_com_audiometria | fração | universal |",
        "|---|---|---|---|---|",
    ]
    for nome, cov in coberturas.items():
        linhas.append(
            f"| {nome} | {cov.n_cargos} | {cov.n_com_audiometria} | {cov.fracao:.4f} | {cov.universal} |"
        )
    agregado_bruto = agregar_universalidade(coberturas, piso)
    linhas.append("")
    linhas.append(
        f"**Agregado bruto:** {agregado_bruto.universais_bruto}/{agregado_bruto.total} documentos "
        f"universais (fração == 1.0). Com piso `n_cargos >= N={agregado_bruto.piso}`: "
        f"{agregado_bruto.universais_com_piso}/{agregado_bruto.total}."
    )
    linhas.append("")
    fracoes_nao_universais = sorted(c.fracao for c in coberturas.values() if not c.universal)
    linhas.append(f"Distribuição das frações dos não-universais: {[f'{f:.3f}' for f in fracoes_nao_universais]}")
    linhas.append("")

    linhas.append("### Denominador canônico (colapsando cópias da mesma obra)")
    linhas.append("")
    linhas.append("Regra de colapso: mesmo nome de obra + data → mesmo documento; cópia de")
    linhas.append("referência = mais cargos captados e, entre esses, mais cargos com")
    linhas.append("audiometria (não perde linha por truncamento). Empate sem conflito de")
    linhas.append("métricas → escolha arbitrária nomeada, sem efeito no número. Conflito de")
    linhas.append("métricas → `colapso indeciso`, nenhuma cópia escolhida.")
    linhas.append("")
    linhas.append("| Obra | Membros | Canônico | Status |")
    linhas.append("|---|---|---|---|")
    for c in sorted(colapsos, key=lambda x: x.chave):
        linhas.append(f"| {c.chave} | {len(c.membros)} | {c.canonico} | {c.status} |")
    linhas.append("")

    coberturas_canonico = {nome: coberturas[nome] for nome in canonicos}
    agregado_canonico = agregar_universalidade(coberturas_canonico, piso)
    linhas.append(
        f"**Agregado canônico:** {agregado_canonico.universais_bruto}/{agregado_canonico.total} obras "
        f"distintas universais (colapsando {len(coberturas)} arquivos em {len(canonicos)} obras). "
        f"Com piso `n_cargos >= N={agregado_canonico.piso}`: "
        f"{agregado_canonico.universais_com_piso}/{agregado_canonico.total}."
    )
    linhas.append("")
    fracoes_canonico_nao_universal = sorted(
        coberturas[nome].fracao for nome in canonicos if not coberturas[nome].universal
    )
    linhas.append(
        f"Distribuição das frações canônicas dos não-universais: "
        f"{[f'{f:.3f}' for f in fracoes_canonico_nao_universal]}"
    )
    linhas.append("")

    linhas.append("### Cargos sem audiometria, por documento não-universal (nominal)")
    linhas.append("")
    for nome, cov in coberturas.items():
        if cov.universal or not cov.cargos_sem_audiometria:
            continue
        linhas.append(f"**{nome}** ({cov.n_com_audiometria}/{cov.n_cargos}):")
        linhas.extend(f"- {c}" for c in cov.cargos_sem_audiometria)
        linhas.append("")

    linhas.append("## Bloco D — momento DEM na audiometria (003.EZ)")
    linhas.append("")
    linhas.append(
        "Nos cargos que **recebem** audiometria, três baldes (nunca dois): `com_dem` "
        "(`Momento.DEM` presente), `sem_dem` (DEM ausente e sem rótulo não reconhecido, forma "
        "limpa confirmada), `indeterminado` (rótulo não reconhecido no grupo de momentos — "
        "ilegível, não é negativo). Recorte separado entre obras não-universais e universais "
        "para contrastar com a convergência n=2 de 003.EX (SPE 0030 e RESERVA 0028, ambas "
        "universais)."
    )
    linhas.append("")

    def _tabela_momento_dem(nomes: list[str]) -> tuple[list[str], tuple[int, int, int]]:
        linhas_tabela = ["| Obra (canônico) | fração | n_com_audiometria | com_dem | sem_dem | indeterminado |", "|---|---|---|---|---|---|"]
        soma_com_dem = soma_sem_dem = soma_indeterminado = 0
        for nome in sorted(nomes):
            cov = coberturas[nome]
            mom = momentos_por_doc[nome]
            linhas_tabela.append(
                f"| {nome} | {cov.fracao:.4f} | {cov.n_com_audiometria} | {mom.n_com_dem} | "
                f"{mom.n_sem_dem} | {mom.n_indeterminado} |"
            )
            soma_com_dem += mom.n_com_dem
            soma_sem_dem += mom.n_sem_dem
            soma_indeterminado += mom.n_indeterminado
        return linhas_tabela, (soma_com_dem, soma_sem_dem, soma_indeterminado)

    canonicos_nao_universais = [nome for nome in canonicos if not coberturas[nome].universal]
    canonicos_universais = [nome for nome in canonicos if coberturas[nome].universal]

    linhas.append("### Obras não-universais (fração < 1.0), denominador canônico")
    linhas.append("")
    tabela_nao_universal, (cd_nu, sd_nu, ind_nu) = _tabela_momento_dem(canonicos_nao_universais)
    linhas.extend(tabela_nao_universal)
    linhas.append("")
    linhas.append(
        f"**Agregado não-universais:** com_dem={cd_nu}, sem_dem={sd_nu}, indeterminado={ind_nu} "
        f"(total com audiometria: {cd_nu + sd_nu + ind_nu})."
    )
    linhas.append("")

    linhas.append("### Obras universais (fração == 1.0), denominador canônico — contraste com 003.EX")
    linhas.append("")
    tabela_universal, (cd_u, sd_u, ind_u) = _tabela_momento_dem(canonicos_universais)
    linhas.extend(tabela_universal)
    linhas.append("")
    linhas.append(
        f"**Agregado universais:** com_dem={cd_u}, sem_dem={sd_u}, indeterminado={ind_u} "
        f"(total com audiometria: {cd_u + sd_u + ind_u})."
    )
    linhas.append("")

    linhas.append("### Cargos indeterminados, por obra não-universal (nominal)")
    linhas.append("")
    for nome in sorted(canonicos_nao_universais):
        mom = momentos_por_doc[nome]
        if not mom.cargos_indeterminados:
            continue
        linhas.append(f"**{nome}**:")
        linhas.extend(f"- {c}" for c in mom.cargos_indeterminados)
        linhas.append("")

    linhas.append("## Bloco B — forma da periodicidade")
    linhas.append("")
    contagem_forma: dict[str, int] = {}
    todas_formas_flat: list[FormaPeriodicidade] = [f for lst in todas_formas.values() for f in lst]
    for f in todas_formas_flat:
        contagem_forma[f.forma] = contagem_forma.get(f.forma, 0) + 1
    linhas.append("### Distribuição agregada de formas (todos os exames, 26 documentos)")
    linhas.append("")
    for forma, n in sorted(contagem_forma.items(), key=lambda kv: -kv[1]):
        linhas.append(f"- `{forma}`: {n}")
    linhas.append("")

    linhas.append("### Regra de 003.EO — número só aparece quando periodicidade != 12M, exceto RX Tórax OIT")
    linhas.append("")
    confirmam, contrariam = confere_regra_003eo(todas_formas_flat)
    linhas.append(f"- confirmam: {len(confirmam)}")
    linhas.append(f"- contrariam: {len(contrariam)}")
    linhas.append("")
    if contrariam:
        linhas.append("Ocorrências que contrariam a regra:")
        linhas.extend(f"- {c}" for c in sorted(set(contrariam)))
        linhas.append("")

    linhas.append("## Bloco C — formas anômalas (texto verbatim)")
    linhas.append("")
    if not anomalias:
        linhas.append("(vazio — nenhuma forma anômala detectada)")
    else:
        for nome_doc, cargo, f in anomalias:
            linhas.append(f"- [{nome_doc}] {cargo}: `{f.forma}` — {f.texto_bruto!r}")
    linhas.append("")

    linhas.append("### Rótulos não reconhecidos na linha de audiometria (por documento)")
    linhas.append("")
    for nome, suspeitas in todas_suspeitas.items():
        if suspeitas:
            linhas.append(f"**{nome}**:")
            linhas.extend(f"- {s}" for s in suspeitas)
            linhas.append("")

    linhas.append("## Notas de escopo e limitações (nomeadas, não silenciosas)")
    linhas.append("")
    linhas.append(
        "- **Fora do escopo desta fatia, nomeado (EMENDA 1):** 5 `.pdf` que são matrizes "
        "(extração de PDF é outro problema); 4 `.rtf`; 1 `.xlsx` (`Matriz função- risco-exames "
        "- validado Dra. Patrícia 06.2025.xlsx`); 11 PCMSO completos + 1 PGR em `.doc`/`.docx` "
        "(não são matrizes de 2 colunas, não inspecionados — dívida de amostra registrada, não "
        "verificado se contêm matriz embutida). Denominador honesto do acervo-matriz "
        "identificável: 26 de 36."
    )
    linhas.append(
        "- **Mesclagem de células (achado estrutural, corrigido nesta sessão):** ATZUM, CJR e "
        "outros documentos de tabela única têm FUNÇÃO/EXAMES SOLICITADOS mesclados em mais de "
        "1 coluna física (ATZUM: 13 colunas físicas, FUNÇÃO em 0-3, EXAMES em 4-9). Indexação "
        "fixa `celulas[0]`/`celulas[1]` lê a própria mesclagem de FUNÇÃO como coluna de exames "
        "nesses casos e zera a audiometria em silêncio (ATZUM media 0/47 antes da correção). "
        "`_celulas_logicas` colapsa células adjacentes de texto idêntico antes de indexar — "
        "checkpoints SPE 0030/RESERVA 0028 (base e `(1)`) confirmados inalterados após a "
        "correção."
    )
    linhas.append(
        "- **Artefato isolado:** `MATRIZ DE EXAMES(ADENDO )ENGESEG ESTRUTURAL LTDA FILIAL - "
        "21.11.24.docx` tem uma célula de cabeçalho/rodapé (`'12'`, provável numeração de "
        "página do template original) que não bate nenhum padrão de metadado reconhecido e "
        "entra como pseudo-cargo sem exames (1 de 34 linhas nesse documento). Não filtrado por "
        "heurística ad-hoc — reportado aqui, não escondido. Efeito no agregado: desprezível "
        "(1 linha em 26 documentos)."
    )
    linhas.append(
        "- **CJR ENGENHARIA LTDA** (único fora do padrão de nome, EMENDA 1): estrutura de "
        "tabela diverge dos demais 25 (3 colunas físicas, vocabulário de rótulo próprio — "
        "`Mud`/`Rett` em vez de `MRO`/`RET`, não reconhecidos por `_ROTULO_MOMENTO`) mas "
        "genuinamente tem 1 só cargo (`TECNÓLOGO EM EDIFICAÇÕES`) — confirmado por leitura "
        "direta da tabela, não é falha de parser."
    )
    linhas.append(
        "- **RICCO HETRIN 23.05.2025, 3 cópias:** `(1)` é adendo parcial genuíno (5 cargos, "
        "declarado 'Renovação' como as outras duas — não um tipo de documento diferente, só "
        "menor); base e `(2)` têm cobertura de audiometria idêntica (61/62, mesmo cargo faltante "
        "'Vigia Noturno'), divergindo só em anotação textual no nome de um cargo "
        "('Almoxarife') — tratadas como empate na escolha de cópia canônica, sem efeito no "
        "número."
    )
    linhas.append(
        "- **RESERVA 0028, 2 cópias:** checkpoint corrigido pela EMENDA 2 contra "
        "`docs/referencia/GABARITO_003EX_audiometria_dem.md` — base 43/44 (SERRALHEIRO "
        "truncado, erro de edição no `.doc` de origem, não artefato de parser), `(1)` 44/44 "
        "(cópia de referência). Os dois desvios de forma documentados no gabarito para esse "
        "par (periodicidade em grupo separado; periodicidade embutida no rótulo do momento, "
        "cargo 'Assistente Administrativo de Segurança do Trabalho') foram reproduzidos "
        "identicamente pelo instrumento novo."
    )
    linhas.append("")

    return "\n".join(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("docx", nargs="+", type=Path)
    parser.add_argument("--saida", type=Path, required=True)
    parser.add_argument(
        "--piso",
        type=int,
        default=17,
        help="Piso editorial de n_cargos para o agregado 'universal com piso' (DH-003EY-02).",
    )
    args = parser.parse_args()

    mapa_nomes = carregar_mapa_nome_para_slug()
    conteudo = gerar_relatorio(args.docx, mapa_nomes, piso=args.piso)

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text(conteudo, encoding="utf-8")
    print(f"Relatório gravado em {args.saida}", file=sys.stderr)


if __name__ == "__main__":
    main()
