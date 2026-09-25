"""Página web da matriz — rota determinística, S3 fatia 1 (003.EQ + emendas).

Mesma topologia de web_envelope.py: núcleo puro que não importa streamlit +
casca pagina_matriz() que importa streamlit dentro da função. O núcleo
carrega o trabalho (D-ARQ-54 P1, molde web_envelope.py).

executar_rota_determinista_cacheada separa o CARO (processar_arquivo_pgr —
parse do PDF, minutos) do BARATO (gerar_documento — montagem/render sobre
matrizes já calculadas, milissegundos): deve_reprocessar decide, por uma
chave que deriva do CONTEÚDO do PDF + do envelope (nunca de cabeçalho/
rodapé — apresentação não é identidade do parse, D-ARQ-22: trocar só o
cabeçalho não pode mascarar reuso de matriz de outro PDF, nem forçar reparse
por um campo cosmético), se o cache pode ser reaproveitado. A casca guarda
o CacheMatrizes em st.session_state e chama a rota cacheada a cada rerun —
inclusive o rerun disparado por clique em st.download_button (comportamento
padrão do Streamlit, on_click="rerun") — sem nunca reprocessar o PDF fora
de uma mudança real de conteúdo/envelope. Lógica de domínio zero na casca.
"""

from __future__ import annotations

import dataclasses
import hashlib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Callable, Sequence

from agente_medico.adaptadores.orquestracao_fds import preparar_composicao
from agente_medico.adaptadores.orquestracao_pgr import preparar_pgr_hidratado
from agente_medico.adaptadores.transcritor_gemini import TranscritorGemini
from agente_medico.adaptadores.transcritor_gemini_card import TranscritorGeminiCard
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.leo_resolver import limite_quimico
from agente_medico.motor.medicoes import aplicar_medicoes
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import (
    FDS,
    PGR,
    BlocoVerbatim,
    EnvelopeConfirmado,
    GHEVerbatim,
    MatrizGHE,
    MedicaoInformada,
    Pendencia,
    ProdutoQuimico,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_fds import TranscritorLLM
from agente_medico.motor.transcritor_pgr import TranscritorGHE
from agente_medico.superficie.apresentacao import EmissaoFuturaError, validar_data_emissao
from agente_medico.superficie.documento_matriz import (
    CabecalhoDocumento,
    DocumentoMatriz,
    RodapeDocumento,
    montar_documento,
    renderizar_html,
)

__all__ = [
    "CacheMatrizes",
    "ComponenteAnexado",
    "EmissaoFuturaError",
    "ProdutoAnexado",
    "TranscritorGemini",
    "anexar_produto_e_reprocessar",
    "anexar_produto_em_ghes",
    "calcular_chave_cache",
    "deve_reprocessar",
    "executar_rota_determinista",
    "executar_rota_determinista_cacheada",
    "gerar_documento",
    "ghes_com_produto",
    "listar_produtos_anexados",
    "montar_envelope",
    "montar_fds",
    "pagina_matriz",
    "preparar_composicao",
    "preparar_composicao_cacheada",
    "remover_produto_e_reprocessar",
    "responsavel_pcmso_incompleto",
]


def montar_envelope(
    validade_iso: str, assinatura: bool, hoje: date | None = None
) -> EnvelopeConfirmado:
    """Mesmo espelho de mensagem que montar_volta_envelope (web_envelope.py):
    ValueError na validade malformada, nunca coagida silenciosamente;
    EmissaoFuturaError para emissão posterior a hoje (R-PGR-06 —
    validar_data_emissao)."""
    validade = validar_data_emissao(validade_iso, hoje)
    return EnvelopeConfirmado(validade=validade, assinatura_engenheiro=assinatura)


def responsavel_pcmso_incompleto(medico_coordenador: str, crm: str) -> tuple[str, ...]:
    """Campos do médico responsável pelo PCMSO que impedem gerar o documento
    (NR-7: o PCMSO tem médico responsável identificado). CRM sem nenhum dígito
    conta como ausente — não há número de registro a conferir."""
    faltando: list[str] = []
    if not medico_coordenador.strip():
        faltando.append("Médico coordenador")
    if not any(c.isdigit() for c in crm):
        faltando.append("CRM")
    return tuple(faltando)


def gerar_documento(
    matrizes: Sequence[MatrizGHE],
    exames_vocab: dict[str, Any],
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
) -> tuple[DocumentoMatriz, str]:
    """Delega a montar_documento + renderizar_html — não reimplementa
    expansão GHE→cargo nem ordenação de exame."""
    doc = montar_documento(matrizes, exames_vocab, cabecalho, rodape)
    return doc, renderizar_html(doc)


@dataclass
class _TranscritorContado:
    """Envolve um TranscritorGHE contando invocações — a casca precisa saber
    quantos blocos foram lidos por IA para exibir na tela (003.EW). Não altera
    comportamento: delega e propaga exceção.

    transcrever_lote (003.EW emenda) é o que faz transcrever_ghes
    (motor/transcritor_pgr.py) enxergar o lote por duck-typing através do
    wrapper: sem este método, o wrapper intercepta o getattr e o caminho de
    produção volta a uma requisição por bloco (o problema original da fatia
    2 — 18 de 20 da cota diária). Conta BLOCOS ENVIADOS à IA, não
    requisições HTTP — é o que a tela informa ao operador."""

    interno: TranscritorGHE
    chamadas: int = 0

    def transcrever(self, bloco: str) -> GHEVerbatim:
        self.chamadas += 1
        return self.interno.transcrever(bloco)

    def transcrever_lote(self, blocos: Sequence[str]) -> tuple[GHEVerbatim, ...]:
        """Delega o lote quando o interno o oferece (TranscritorGeminiGHE) e
        cai no unitário quando não (clientes offline e duplos de teste).
        Conta BLOCOS ENVIADOS à IA — não requisições HTTP —, que é o que a
        tela informa ao operador. Sem este método, transcrever_ghes não
        enxerga o lote no wrapper e o caminho de produção volta a uma
        requisição por bloco (003.EW: 18 de 20 da cota diária).
        """
        self.chamadas += len(blocos)
        em_lote = getattr(self.interno, "transcrever_lote", None)
        if callable(em_lote):
            return tuple(em_lote(blocos))
        return tuple(self.interno.transcrever(b) for b in blocos)


def _protocolo_padrao() -> Protocolo:
    """Carrega o protocolo do diretório do pacote — via `__file__` DESTE
    módulo (web_matriz.py), nunca do `__file__` de quem chama: dentro de
    pagina_matriz(), AppTest.from_function copia o CORPO da função para um
    script temporário, e `__file__` ali resolveria para esse script, não
    para este arquivo (achado da fatia 2b). Único ponto de carregamento —
    _rodar_parse_deterministico e pagina_matriz (ao anexar produto) usam
    este helper, nunca Path(__file__) direto."""
    return carregar(Path(__file__).resolve().parent.parent / "protocolo")


def _rodar_parse_deterministico(
    caminho_pdf: Path, envelope: EnvelopeConfirmado
) -> tuple[
    PGR | None,
    tuple[MatrizGHE, ...] | None,
    dict[str, Any],
    tuple[Pendencia, ...],
    str | None,
    tuple[Pendencia, ...],
    int,
]:
    """Devolve, além de matrizes/exames_vocab/pendencias (extração+hidratação),
    resultado.status e resultado.pendencias_globais — sem esses dois campos a
    casca não consegue distinguir um gate eliminatório (R-PGR-01/R-PGR-06,
    Resultado(status="REJEITADO", matrizes=[])) de um parse legitimamente
    vazio (achado 003.EQ emenda 3: `matrizes=[]` não é None, então esse ramo
    passava reto pelo guard `doc is None`). Sexto campo: quantos blocos GHE
    foram lidos por IA (003.EW) — 0 quando a rota determinística cobriu tudo.
    Primeiro campo (D-ARQ-49 Parte 2 fatia 2b): o PGR hidratado, exposto para a
    casca anexar produtos_quimicos via anexar_produto_e_reprocessar sem
    reprocessar PDF/LLM. Decompõe o que antes era 1 chamada a
    processar_arquivo_pgr em preparar_pgr_hidratado (caro) + processar_pgr
    (barato, D-ARQ-49 fatia 2a) — MESMO comportamento externo, o intermediário
    só fica visível para quem chama esta função."""
    protocolo = _protocolo_padrao()
    contador = _TranscritorContado(interno=TranscritorGeminiGHE())
    pgr_hidratado, pendencias = preparar_pgr_hidratado(
        caminho_pdf,
        protocolo,
        contador,
        TranscritorGeminiCard(),
        envelope,
    )
    if pgr_hidratado is None:
        return None, None, protocolo.vocabulario.exames, pendencias, None, (), contador.chamadas
    resultado = processar_pgr(pgr_hidratado, protocolo)
    return (
        pgr_hidratado,
        tuple(resultado.matrizes),
        protocolo.vocabulario.exames,
        pendencias,
        resultado.status,
        tuple(resultado.pendencias_globais),
        contador.chamadas,
    )


def executar_rota_determinista(
    caminho_pdf: Path,
    envelope: EnvelopeConfirmado,
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
) -> tuple[DocumentoMatriz | None, str | None, tuple[Pendencia, ...]]:
    """Carrega o protocolo e roda a costura arquivo->PGR->Resultado com os
    clientes reais (D-ARQ-65 fatia 2, roteamento determinístico-primeiro): a
    rota por coordenadas é tentada antes, e o cliente LLM só é invocado quando
    a família não é reconhecida (FamiliaNaoReconhecida ou contagem
    divergente). Com Resultado não-None, gera o documento. Parse total falho
    devolve (None, None, pendencias) — nunca inventa matriz (D-ARQ-22).
    Primitiva sem cache — executar_rota_determinista_cacheada é a versão que a
    casca usa de fato."""
    _pgr_hidratado, matrizes, exames_vocab, pendencias, _status, _pendencias_globais, _chamadas_ia = (
        _rodar_parse_deterministico(caminho_pdf, envelope)
    )
    if matrizes is None:
        return None, None, pendencias
    doc, html = gerar_documento(matrizes, exames_vocab, cabecalho, rodape)
    return doc, html, pendencias


@dataclass(frozen=True)
class CacheMatrizes:
    """Resultado cacheado da parte CARA (preparar_pgr_hidratado + processar_pgr)
    da rota determinística. `chave` vem de calcular_chave_cache — PDF + envelope,
    nunca cabeçalho/rodapé. `status`/`pendencias_globais` espelham
    Resultado — a casca usa `status == "REJEITADO"` para parar duro
    (003.EQ emenda 3, elo A). `chamadas_ia` (003.EW, campo aditivo) é quantos
    blocos GHE foram lidos por IA — não entra em calcular_chave_cache: é
    resultado do parse, não identidade dele. `pgr_hidratado` (D-ARQ-49 Parte 2
    fatia 2b, campo aditivo, molde chamadas_ia) é o PGR hidratado por
    preparar_pgr_hidratado — também NÃO entra em calcular_chave_cache (é
    resultado do parse, não identidade dele); anexar_produto_e_reprocessar o
    consome para plugar um ProdutoQuimico sem reprocessar PDF/LLM.
    `anexos_descartados` (GHE, produto): anexos do cache anterior que não
    puderam ser reaplicados depois de um reparse do MESMO PDF porque o GHE não
    existe mais — a casca avisa uma vez e limpa. `medicoes` (D-ARQ-86 cl.8):
    avaliações quantitativas informadas na tela; ficam FORA de pgr_hidratado e
    são reaplicadas a cada processar_pgr, então remover uma medição devolve o
    valor do PGR."""

    chave: str
    matrizes: tuple[MatrizGHE, ...] | None
    exames_vocab: dict[str, Any]
    pendencias: tuple[Pendencia, ...]
    status: str | None
    pendencias_globais: tuple[Pendencia, ...]
    chamadas_ia: int
    pgr_hidratado: PGR | None
    anexos_descartados: tuple[tuple[str, str], ...] = ()
    medicoes: tuple[MedicaoInformada, ...] = ()


def calcular_chave_cache(conteudo_pdf: bytes, envelope: EnvelopeConfirmado) -> str:
    """Chave de invalidação do cache: hash do CONTEÚDO do PDF (bytes reais,
    não o nome do arquivo) + envelope. Cabeçalho/rodapé nunca entram — são
    apresentação, não identidade do parse (ver docstring do módulo)."""
    digest = hashlib.sha256(conteudo_pdf).hexdigest()
    return f"{digest}:{envelope.validade.isoformat()}:{envelope.assinatura_engenheiro}"


def deve_reprocessar(chave_atual: str, chave_em_cache: str | None) -> bool:
    """True quando o cache (se existir) não corresponde ao PDF/envelope
    atuais — processar_arquivo_pgr (caro) precisa rodar de novo. False
    reaproveita o cache (mesmo PDF, mesmo envelope)."""
    return chave_atual != chave_em_cache


def executar_rota_determinista_cacheada(
    caminho_pdf: Path,
    conteudo_pdf: bytes,
    envelope: EnvelopeConfirmado,
    cabecalho: CabecalhoDocumento,
    rodape: RodapeDocumento,
    cache: CacheMatrizes | None,
) -> tuple[DocumentoMatriz | None, str | None, tuple[Pendencia, ...], CacheMatrizes]:
    """Cacheia o CARO (processar_arquivo_pgr, via deve_reprocessar sobre a
    chave de calcular_chave_cache), regenera o BARATO (gerar_documento)
    incondicionalmente — mesmo no cache-hit, cabeçalho/rodapé ATUAIS valem,
    nunca os do momento em que o cache foi gravado. Devolve sempre o
    CacheMatrizes vigente (novo, no miss; o mesmo, no hit) para a casca
    persistir em st.session_state.

    No miss com o MESMO PDF (só o envelope mudou), os produtos anexados no
    cache anterior são reaplicados ao PGR recém-hidratado — antes sumiam sem
    aviso. PDF diferente é outro documento: nada é carregado."""
    chave_atual = calcular_chave_cache(conteudo_pdf, envelope)
    if cache is None or deve_reprocessar(chave_atual, cache.chave):
        anteriores = _produtos_a_carregar(cache, chave_atual)
        medicoes_anteriores = (
            cache.medicoes if cache is not None and _mesmo_pdf(cache.chave, chave_atual) else ()
        )
        pgr_hidratado, matrizes, exames_vocab, pendencias, status, pendencias_globais, chamadas_ia = (
            _rodar_parse_deterministico(caminho_pdf, envelope)
        )
        cache = CacheMatrizes(
            chave=chave_atual,
            matrizes=matrizes,
            exames_vocab=exames_vocab,
            pendencias=pendencias,
            status=status,
            pendencias_globais=pendencias_globais,
            chamadas_ia=chamadas_ia,
            pgr_hidratado=pgr_hidratado,
        )
        if anteriores and cache.pgr_hidratado is not None and cache.status != "REJEITADO":
            cache = _reaplicar_produtos(cache, _protocolo_padrao(), anteriores)
        if medicoes_anteriores and cache.pgr_hidratado is not None and cache.status != "REJEITADO":
            cache = _reprocessar(
                dataclasses.replace(cache, medicoes=medicoes_anteriores),
                _protocolo_padrao(),
                cache.pgr_hidratado,
            )

    if cache.matrizes is None:
        return None, None, cache.pendencias, cache
    doc, html = gerar_documento(cache.matrizes, cache.exames_vocab, cabecalho, rodape)
    return doc, html, cache.pendencias, cache


def _mesmo_pdf(chave_a: str, chave_b: str) -> bool:
    return chave_a.split(":", 1)[0] == chave_b.split(":", 1)[0]


def _produtos_a_carregar(
    cache: CacheMatrizes | None, chave_atual: str
) -> tuple[tuple[str, ProdutoQuimico], ...]:
    if cache is None or cache.pgr_hidratado is None or not _mesmo_pdf(cache.chave, chave_atual):
        return ()
    return tuple(
        (ghe.id, produto) for ghe in cache.pgr_hidratado.ghes for produto in ghe.produtos_quimicos
    )


def _reaplicar_produtos(
    cache: CacheMatrizes,
    protocolo: Protocolo,
    produtos: tuple[tuple[str, ProdutoQuimico], ...],
) -> CacheMatrizes:
    assert cache.pgr_hidratado is not None
    ids = {ghe.id for ghe in cache.pgr_hidratado.ghes}
    ghes_novos = tuple(
        dataclasses.replace(
            ghe,
            produtos_quimicos=(
                *ghe.produtos_quimicos,
                *(produto for ghe_id, produto in produtos if ghe_id == ghe.id),
            ),
        )
        for ghe in cache.pgr_hidratado.ghes
    )
    reprocessado = _reprocessar(
        cache, protocolo, dataclasses.replace(cache.pgr_hidratado, ghes=ghes_novos)
    )
    return dataclasses.replace(
        reprocessado,
        anexos_descartados=tuple(
            (ghe_id, produto.nome) for ghe_id, produto in produtos if ghe_id not in ids
        ),
    )


def anexar_produto_e_reprocessar(
    cache: CacheMatrizes,
    protocolo: Protocolo,
    ghe_id: str,
    nome_produto: str,
    fds: FDS,
) -> CacheMatrizes:
    """Anexa um ProdutoQuimico(nome, fds) ao GHE `ghe_id` do PGR já hidratado
    em `cache.pgr_hidratado` (D-ARQ-49 Parte 2 fatia 2b) e roda processar_pgr
    de novo sobre o PGR mutado — SEM reprocessar o PDF, SEM nova chamada LLM
    (preparar_pgr_hidratado, a parte CARA, não é chamado aqui). `fds` precisa
    chegar com composicao_verbatim populada (nunca fds=None órfão — o slot só
    nasce com FDS anexada, então R-PGR-04 não dispara por esta via, D-ARQ-49
    v199); a composição resolvida/promovida (gate_cas + Fase C,
    resolver_composicao/estagios/riscos.py) nasce de processar_pgr, não daqui.
    Preserva chave/exames_vocab/pendencias/chamadas_ia do cache original — só
    pgr_hidratado e os campos derivados de Resultado (matrizes/status/
    pendencias_globais) mudam. Precondição (responsabilidade da casca):
    cache.pgr_hidratado is not None."""
    return anexar_produto_em_ghes(cache, protocolo, (ghe_id,), nome_produto, fds)


def anexar_produto_em_ghes(
    cache: CacheMatrizes,
    protocolo: Protocolo,
    ghe_ids: Sequence[str],
    nome_produto: str,
    fds: FDS,
) -> CacheMatrizes:
    """Mesmo contrato de anexar_produto_e_reprocessar para N GHEs de uma vez
    (FDS "GHE 04 e 05"), com um único processar_pgr. Filtrar GHE que já tem o
    produto é responsabilidade da casca (ghes_com_produto)."""
    assert cache.pgr_hidratado is not None
    produto = ProdutoQuimico(nome=nome_produto, fds=fds)
    destinos = set(ghe_ids)
    ghes_novos = tuple(
        dataclasses.replace(ghe, produtos_quimicos=(*ghe.produtos_quimicos, produto))
        if ghe.id in destinos
        else ghe
        for ghe in cache.pgr_hidratado.ghes
    )
    return _reprocessar(cache, protocolo, dataclasses.replace(cache.pgr_hidratado, ghes=ghes_novos))


def remover_produto_e_reprocessar(
    cache: CacheMatrizes,
    protocolo: Protocolo,
    ghe_id: str,
    nome_produto: str,
) -> CacheMatrizes:
    """Inverso de anexar_produto_e_reprocessar: tira do GHE `ghe_id` todo
    produto chamado `nome_produto` e roda processar_pgr de novo, sem PDF/LLM.
    Os demais GHEs ficam intactos, mesmo com produto de mesmo nome.
    Precondição (responsabilidade da casca): cache.pgr_hidratado is not None."""
    assert cache.pgr_hidratado is not None
    ghes_novos = tuple(
        dataclasses.replace(
            ghe,
            produtos_quimicos=tuple(p for p in ghe.produtos_quimicos if p.nome != nome_produto),
        )
        if ghe.id == ghe_id
        else ghe
        for ghe in cache.pgr_hidratado.ghes
    )
    return _reprocessar(cache, protocolo, dataclasses.replace(cache.pgr_hidratado, ghes=ghes_novos))


def _reprocessar(cache: CacheMatrizes, protocolo: Protocolo, pgr_atualizado: PGR) -> CacheMatrizes:
    pgr_com_medicoes, pendencias_medicao = aplicar_medicoes(
        pgr_atualizado, cache.medicoes, protocolo.vocabulario.agentes
    )
    resultado = processar_pgr(pgr_com_medicoes, protocolo)
    return dataclasses.replace(
        cache,
        pgr_hidratado=pgr_atualizado,
        matrizes=tuple(resultado.matrizes),
        status=resultado.status,
        pendencias_globais=(*resultado.pendencias_globais, *pendencias_medicao),
    )


def registrar_medicao_e_reprocessar(
    cache: CacheMatrizes, protocolo: Protocolo, medicao: MedicaoInformada
) -> CacheMatrizes:
    """D-ARQ-86 cl.1: uma medição por (GHE, agente) — a nova substitui a anterior.
    Precondição (responsabilidade da casca): cache.pgr_hidratado is not None."""
    assert cache.pgr_hidratado is not None
    outras = tuple(
        m for m in cache.medicoes if (m.ghe_id, m.agente) != (medicao.ghe_id, medicao.agente)
    )
    return _reprocessar(
        dataclasses.replace(cache, medicoes=(*outras, medicao)), protocolo, cache.pgr_hidratado
    )


def remover_medicao_e_reprocessar(
    cache: CacheMatrizes, protocolo: Protocolo, ghe_id: str, agente: str
) -> CacheMatrizes:
    assert cache.pgr_hidratado is not None
    restantes = tuple(m for m in cache.medicoes if (m.ghe_id, m.agente) != (ghe_id, agente))
    return _reprocessar(
        dataclasses.replace(cache, medicoes=restantes), protocolo, cache.pgr_hidratado
    )


AGENTES_POEIRA_MEDIVEIS: dict[str, tuple[str, ...]] = {
    "silica": ("mg/m3",),
    "poeira_nao_classificada": ("mg/m3",),
}


def agentes_mensuraveis(pgr: PGR, ghe_id: str, protocolo: Protocolo) -> dict[str, tuple[str, ...]]:
    """Agentes do GHE (riscos do PGR) com LT da NR-15 no vocabulário, mais
    sílica e PNOS (LEO do resolver, R-RX-01 — D-ARQ-86 fatia 2) → unidades
    aceitas. Agente fora daqui não recebe medição na tela: sem risco no PGR a
    medição não teria onde entrar, e sem LT não decide nada (D-ARQ-86 cl.5).
    Asbesto fica fora: o resolver não tem o LEO dele (decisão do Diovanni)."""
    agentes_vocab = protocolo.vocabulario.agentes
    ghe = next((g for g in pgr.ghes if g.id == ghe_id), None)
    if ghe is None:
        return {}
    mensuraveis: dict[str, tuple[str, ...]] = {}
    for risco in ghe.riscos:
        if risco.agente is None or risco.agente in mensuraveis:
            continue
        unidades = AGENTES_POEIRA_MEDIVEIS.get(risco.agente) or tuple(
            u for u in ("ppm", "mg/m3") if limite_quimico(risco.agente, u, agentes_vocab) is not None
        )
        if unidades:
            mensuraveis[risco.agente] = unidades
    return mensuraveis


@dataclass(frozen=True)
class ComponenteAnexado:
    """Componente de FDS como o motor o resolveu: `agente` é o slug do
    vocabulário, ou None quando o CAS não está lá (vira pendência, não risco)."""

    cas: str
    nome: str
    agente: str | None


@dataclass(frozen=True)
class ProdutoAnexado:
    ghe_id: str
    ghe_nome: str
    nome: str
    componentes: tuple[ComponenteAnexado, ...]


def ghes_com_produto(pgr: PGR, nome_produto: str) -> tuple[str, ...]:
    """IDs dos GHEs que já têm um produto com este nome — base do status da
    FDS na tela e da recusa de anexo duplicado."""
    return tuple(
        ghe.id for ghe in pgr.ghes if any(p.nome == nome_produto for p in ghe.produtos_quimicos)
    )


def listar_produtos_anexados(pgr: PGR, protocolo: Protocolo) -> tuple[ProdutoAnexado, ...]:
    """Produtos anexados por GHE, com cada componente já resolvido pelo mesmo
    resolver_composicao que processar_pgr usa — a tela mostra o agente que o
    motor de fato enxergou, não a transcrição crua da FDS."""
    pgr_resolvido, _ = resolver_composicao(pgr, construir_indice_cas(protocolo.vocabulario.agentes))
    return tuple(
        ProdutoAnexado(
            ghe_id=ghe.id,
            ghe_nome=ghe.nome,
            nome=produto.nome,
            componentes=tuple(
                ComponenteAnexado(cas=c.cas, nome=c.nome, agente=c.agente)
                for c in produto.fds.composicao
            ),
        )
        for ghe in pgr_resolvido.ghes
        for produto in ghe.produtos_quimicos
        if produto.fds is not None
    )


ComposicaoFDS = tuple[tuple[BlocoVerbatim, ...], tuple[Pendencia, ...]]


def preparar_composicao_cacheada(
    caminho: Path,
    conteudo: bytes,
    cliente: TranscritorLLM,
    cache: dict[str, ComposicaoFDS],
) -> ComposicaoFDS:
    """preparar_composicao memoizado pelo hash do CONTEÚDO da FDS. Sem isto a
    casca re-transcrevia TODAS as FDS enviadas a cada rerun do Streamlit
    (qualquer widget, inclusive o clique em "Anexar") — N chamadas LLM por
    interação, 429 da cascata inteira, e no rerun do clique a composição
    vinha vazia, o botão não era renderizado e o anexo se perdia.
    `transcricao_indisponivel_fds` é falha transitória de invocação (cota,
    rede) e NÃO é memoizada — o próximo rerun tenta de novo; composição
    extraída e `composicao_ausente_fds` são determinísticas sobre o conteúdo."""
    chave = hashlib.sha256(conteudo).hexdigest()
    if chave in cache:
        return cache[chave]
    resultado = preparar_composicao(caminho, cliente)
    if not any(p.tipo == "transcricao_indisponivel_fds" for p in resultado[1]):
        cache[chave] = resultado
    return resultado


def pagina_matriz() -> None:
    import dataclasses
    import tempfile
    from pathlib import Path

    import streamlit as st
    from streamlit.delta_generator import DeltaGenerator

    from agente_medico.superficie.documento_matriz import (
        CabecalhoDocumento,
        RodapeDocumento,
        nome_ghe_exibicao,
        renderizar_docx,
    )
    from agente_medico.motor.tipos import BlocoVerbatim, Fracao, MedicaoInformada, ProcedenciaMedicao
    from agente_medico.superficie.revisao_matriz import montar_revisao, tabela_markdown
    from agente_medico.superficie.apresentacao import (
        MENSAGEM_EMISSAO_FUTURA,
        EmissaoFuturaError,
    )
    from agente_medico.superficie.web_matriz import (
        CacheMatrizes,
        TranscritorGemini,
        _protocolo_padrao,
        agentes_mensuraveis,
        anexar_produto_em_ghes,
        executar_rota_determinista_cacheada,
        ghes_com_produto,
        listar_produtos_anexados,
        montar_envelope,
        montar_fds,
        preparar_composicao_cacheada,
        registrar_medicao_e_reprocessar,
        remover_medicao_e_reprocessar,
        remover_produto_e_reprocessar,
        responsavel_pcmso_incompleto,
    )

    st.title("Matriz de Exames — PCMSO")
    st.caption(
        "Envie o PGR, preencha a identificação e gere a matriz. Com a matriz gerada, "
        "vincule FDS/FISPQ e medições aos GHEs (opcional), confira as pendências e "
        "baixe o documento."
    )

    # As etapas são criadas aqui, na ordem de LEITURA, e preenchidas mais abaixo
    # na ordem de EXECUÇÃO de sempre: callbacks, leitura do cache e returns
    # antecipados não mudam. AppTest indexa widgets pela posição na tela, então
    # esta ordem é contrato dos testes (file_uploader[0] = PGR, button[0] =
    # Gerar matriz; antes de gerar a matriz, text_input[-1] = validade).
    indicador = st.empty()
    etapa_pgr = st.container(border=True)
    etapa_fds = st.container(border=True)
    etapa_conferencia = st.container()
    etapa_matriz = st.container()
    caixa_conferencia: DeltaGenerator | None = None
    caixa_matriz: DeltaGenerator | None = None
    matriz_gerada = False
    bloqueio: str | None = None
    renderizar_vinculos: Callable[[CacheMatrizes | None], None] | None = None

    with etapa_pgr:
        st.subheader("1. PGR e identificação do documento")
        arquivo = st.file_uploader("PDF do PGR", type="pdf")

    # Cache lido AQUI (não só mais abaixo, junto do form) para que o bloco de
    # FDS avulsa, a seguir, saiba se há um PGR já carregado na tela (D-ARQ-49
    # Parte 2 fatia 2b) — mesmo objeto, sem novo fetch de session_state depois:
    # a mutação feita pelo botão "Anexar" abaixo tem que sobreviver até o
    # write final de st.session_state no fim da função, no MESMO rerun.
    cache: CacheMatrizes | None = st.session_state.get("web_matriz_cache")

    try:
        with etapa_fds:
            st.subheader("2. FDS/FISPQ dos produtos químicos e medições (opcional)")
            st.caption(
                "Extrai CAS e frases-H de cada FDS enviada, com ou sem PGR. Com a matriz "
                "gerada na etapa 1, cada FDS passa a mostrar a escolha de GHEs e o botão "
                "Anexar (D-ARQ-49 Parte 2 fatia 2b)."
            )
            arquivos_fds = st.file_uploader(
                "PDF(s) da FDS/FISPQ", type="pdf", accept_multiple_files=True, key="fds_avulsas"
            )
        cache_fds: dict[str, ComposicaoFDS] = st.session_state.setdefault("web_matriz_cache_fds", {})

        # Anexar/Remover rodam em on_click: o Streamlit executa o callback ANTES do
        # rerun. Inline, o clique só era processado quando o script chegava ao
        # botão — se o rerun era interrompido antes (página lenta com 16 FDS e o
        # usuário já mexendo no widget seguinte), o clique se perdia sem aviso
        # (medido em produção, Aurora, 25/09/2026: aguarrás não anexada).
        def _anexar(nome_arquivo: str, blocos: tuple[BlocoVerbatim, ...]) -> None:
            atual: CacheMatrizes | None = st.session_state.get("web_matriz_cache")
            if atual is None or atual.pgr_hidratado is None:
                return
            escolhidos: list[str] = st.session_state.get(f"ghe_destino_{nome_arquivo}", [])
            nome: str = st.session_state.get(f"nome_produto_{nome_arquivo}", Path(nome_arquivo).stem)
            ja_anexada = set(ghes_com_produto(atual.pgr_hidratado, nome))
            repetidos = [g for g in escolhidos if g in ja_anexada]
            novos = [g for g in escolhidos if g not in ja_anexada]
            mensagens: list[tuple[str, str]] = []
            if not escolhidos:
                mensagens.append(("warning", "Escolha ao menos um GHE antes de anexar."))
            if repetidos:
                mensagens.append(
                    ("warning", f"'{nome}' já está anexado a {', '.join(repetidos)} — mantido como está.")
                )
            if novos:
                st.session_state["web_matriz_cache"] = anexar_produto_em_ghes(
                    atual, _protocolo_padrao(), novos, nome, montar_fds(blocos)
                )
                mensagens.append(("success", f"Produto '{nome}' anexado a {', '.join(novos)}."))
            st.session_state[f"anexo_mensagens_{nome_arquivo}"] = mensagens

        def _remover(ghe_id: str, nome: str) -> None:
            atual: CacheMatrizes | None = st.session_state.get("web_matriz_cache")
            if atual is None or atual.pgr_hidratado is None:
                return
            st.session_state["web_matriz_cache"] = remover_produto_e_reprocessar(
                atual, _protocolo_padrao(), ghe_id, nome
            )

        def _registrar_medicao() -> None:
            atual: CacheMatrizes | None = st.session_state.get("web_matriz_cache")
            if atual is None or atual.pgr_hidratado is None:
                return
            ghe_id: str = st.session_state["medicao_ghe"]
            agente: str = st.session_state["medicao_agente"]
            valor: float = st.session_state["medicao_valor"]
            laudo: str = st.session_state["medicao_laudo"].strip()
            if valor <= 0 or not laudo:
                st.session_state["medicao_mensagem"] = (
                    "warning",
                    "Informe valor maior que zero e a identificação do laudo.",
                )
                return
            fracao: Fracao | None = None
            pct_quartzo: float | None = None
            if agente == "silica":
                # Anexo 12 da NR-15: sem %quartzo não há LT; a fração escolhe a fórmula.
                pct_quartzo = st.session_state["medicao_quartzo"]
                if pct_quartzo is None or pct_quartzo <= 0:
                    st.session_state["medicao_mensagem"] = (
                        "warning",
                        "Sílica: informe o % de quartzo do laudo (NR-15 Anexo 12).",
                    )
                    return
                fracao = Fracao(st.session_state["medicao_fracao"])
            elif agente == "poeira_nao_classificada":
                fracao = Fracao.RESPIRAVEL
            medicao = MedicaoInformada(
                ghe_id=ghe_id,
                agente=agente,
                valor=valor,
                unidade=st.session_state[f"medicao_unidade_{agente}"],
                procedencia=ProcedenciaMedicao(
                    origem="informada",
                    laudo=laudo,
                    data=st.session_state["medicao_data"],
                    metodo=st.session_state["medicao_metodo"].strip(),
                    informante=st.session_state["medicao_informante"].strip(),
                ),
                fracao=fracao,
                pct_quartzo=pct_quartzo,
            )
            st.session_state["web_matriz_cache"] = registrar_medicao_e_reprocessar(
                atual, _protocolo_padrao(), medicao
            )
            st.session_state["medicao_mensagem"] = (
                "success",
                f"Medição de {agente} registrada em {ghe_id}.",
            )

        def _remover_medicao(ghe_id: str, agente: str) -> None:
            atual: CacheMatrizes | None = st.session_state.get("web_matriz_cache")
            if atual is None or atual.pgr_hidratado is None:
                return
            st.session_state["web_matriz_cache"] = remover_medicao_e_reprocessar(
                atual, _protocolo_padrao(), ghe_id, agente
            )

        # Desenhada no `finally`, com o cache DESTE rerun: lida no topo, a etapa 2
        # só mostrava vínculo, produtos e medições na interação seguinte ao clique
        # em Gerar matriz. A posição na tela é a do container etapa_fds.
        def _renderizar_vinculos(cache_vinculo: CacheMatrizes | None) -> None:
            for arquivo_fds in arquivos_fds or ():
                with etapa_fds:
                    with tempfile.TemporaryDirectory() as tmp_fds:
                        caminho_fds = Path(tmp_fds) / arquivo_fds.name
                        conteudo_fds = arquivo_fds.getvalue()
                        caminho_fds.write_bytes(conteudo_fds)
                        with st.spinner(f"Lendo composição de {arquivo_fds.name}..."):
                            blocos_fds, pendencias_fds = preparar_composicao_cacheada(
                                caminho_fds, conteudo_fds, TranscritorGemini(), cache_fds
                            )
                    # Rótulo fixo: rótulo que muda (ex.: com o status do anexo) faz o
                    # Streamlit tratar o expander como outro elemento e fechá-lo no
                    # rerun do próprio clique em Anexar.
                    expander_fds = st.expander(arquivo_fds.name, expanded=len(arquivos_fds) == 1)
                with expander_fds:
                    for bloco_fds in blocos_fds:
                        st.write(f"Faixa: {bloco_fds.faixa}")
                        for membro in bloco_fds.membros:
                            frases_h = ", ".join(membro.frases_h) or "—"
                            st.write(f"- CAS {membro.cas} | {membro.nome} | H: {frases_h}")
                    for p in pendencias_fds:
                        st.write(f"- `{p.tipo}`: {p.motivo}")

                    # Casamento manual FDS<->produto (D-ARQ-49 Parte 2 fatia 2b, decisão
                    # ratificada v199/v200: RT escolhe o GHE e nomeia o produto na tela —
                    # NUNCA extração automática por fonte_geradora/agente/heurística,
                    # descartada por medição real contra o PGR Fascino). Só aparece com
                    # PGR já carregado (cache_vinculo.pgr_hidratado not None) e composição extraída
                    # (blocos_fds não-vazio) — sem PGR, comportamento idêntico ao de hoje.
                    # A lista de GHEs só existe depois do parse do PGR (Gerar matriz). Sem
                    # este aviso a FDS aparecia sem nenhuma forma de vínculo e sem dizer por quê.
                    if blocos_fds and (cache_vinculo is None or cache_vinculo.pgr_hidratado is None):
                        st.info("Gere a matriz para vincular esta FDS a um GHE.")
                    if cache_vinculo is not None and cache_vinculo.pgr_hidratado is not None and blocos_fds:
                        ghes_pgr = cache_vinculo.pgr_hidratado.ghes
                        rotulos_ghe = {
                            ghe.id: f"{ghe.id} — {nome_ghe_exibicao(ghe.nome)}".strip(" —") for ghe in ghes_pgr
                        }
                        # Sem GHE pré-marcado: o selectbox anterior sempre tinha um valor, e
                        # o clique anexava em algum GHE mesmo sem escolha consciente.
                        ghes_escolhidos = st.multiselect(
                            f"Anexar {arquivo_fds.name} a quais GHEs?",
                            options=list(rotulos_ghe),
                            format_func=lambda gid: rotulos_ghe[gid],
                            key=f"ghe_destino_{arquivo_fds.name}",
                        )
                        nome_produto = st.text_input(
                            "Nome do produto",
                            value=Path(arquivo_fds.name).stem,
                            key=f"nome_produto_{arquivo_fds.name}",
                        )
                        st.button(
                            "Anexar aos GHEs selecionados",
                            key=f"anexar_fds_{arquivo_fds.name}",
                            on_click=_anexar,
                            args=(arquivo_fds.name, blocos_fds),
                        )
                        for tipo, texto in st.session_state.pop(f"anexo_mensagens_{arquivo_fds.name}", []):
                            (st.success if tipo == "success" else st.warning)(texto)
                        assert cache_vinculo.pgr_hidratado is not None
                        anexada_em = ghes_com_produto(cache_vinculo.pgr_hidratado, nome_produto)
                        if anexada_em:
                            st.caption(f"Status: anexada a {', '.join(anexada_em)}.")
                        else:
                            st.caption("Status: ainda não anexada a nenhum GHE.")

            if arquivo is not None and cache_vinculo is not None and cache_vinculo.pgr_hidratado is not None:
                with etapa_fds:
                    st.markdown("#### Produtos anexados")
                    # listar_produtos_anexados carrega o protocolo; sem produto não há o que resolver.
                    produtos_anexados = (
                        listar_produtos_anexados(cache_vinculo.pgr_hidratado, _protocolo_padrao())
                        if any(ghe.produtos_quimicos for ghe in cache_vinculo.pgr_hidratado.ghes)
                        else ()
                    )
                    if not produtos_anexados:
                        st.caption("Nenhum produto anexado.")
                    for produto_anexado in produtos_anexados:
                        st.write(
                            f"**{produto_anexado.ghe_id} — {nome_ghe_exibicao(produto_anexado.ghe_nome)}**"
                            f" · {produto_anexado.nome}"
                        )
                        for componente in produto_anexado.componentes:
                            agente = componente.agente or "não reconhecido no vocabulário"
                            st.write(f"- CAS {componente.cas or '—'} | {componente.nome} → {agente}")
                        st.button(
                            "Remover",
                            key=f"remover_{produto_anexado.ghe_id}_{produto_anexado.nome}",
                            on_click=_remover,
                            args=(produto_anexado.ghe_id, produto_anexado.nome),
                        )

            if arquivo is not None and cache_vinculo is not None and cache_vinculo.pgr_hidratado is not None:
                # D-ARQ-86: medição informada por (GHE, agente). Sem medição a matriz não muda.
                with etapa_fds:
                    st.markdown("#### Avaliações quantitativas")
                    st.caption(
                        "Valor representativo do laudo (média ou CLSC) de um agente no GHE. Químico: "
                        "com risco BAIXO no PGR e medição abaixo do nível de ação (metade do LT da "
                        "NR-15, NR-09 9.6.1), o indicador biológico vira menção no PCMSO; "
                        "cancerígenos sempre recebem o indicador. Sílica e poeira não classificada: "
                        "a medição define a periodicidade do RX OIT (NR-07 Anexo III)."
                    )
                    rotulos_medicao = {
                        ghe.id: f"{ghe.id} — {nome_ghe_exibicao(ghe.nome)}".strip(" —")
                        for ghe in cache_vinculo.pgr_hidratado.ghes
                    }
                    col_agente, col_laudo = st.columns(2)
                    with col_agente:
                        ghe_medicao = st.selectbox(
                            "GHE",
                            options=list(rotulos_medicao),
                            format_func=lambda gid: rotulos_medicao[gid],
                            key="medicao_ghe",
                        )
                    mensuraveis = agentes_mensuraveis(cache_vinculo.pgr_hidratado, ghe_medicao, _protocolo_padrao())
                    if not mensuraveis:
                        st.caption("Nenhum agente deste GHE tem limite no Anexo 11 da NR-15.")
                    else:
                        with col_agente:
                            agente_medicao = st.selectbox(
                                "Agente", options=list(mensuraveis), key="medicao_agente"
                            )
                            st.selectbox(
                                "Unidade",
                                options=list(mensuraveis[agente_medicao]),
                                format_func=lambda u: "mg/m³" if u == "mg/m3" else u,
                                key=f"medicao_unidade_{agente_medicao}",
                            )
                            st.number_input("Valor medido", min_value=0.0, format="%.4f", key="medicao_valor")
                            if agente_medicao == "silica":
                                st.selectbox(
                                    "Fração",
                                    options=[Fracao.RESPIRAVEL.value, Fracao.TOTAL.value],
                                    format_func=lambda f: "Respirável" if f == Fracao.RESPIRAVEL.value else "Total",
                                    key="medicao_fracao",
                                )
                                st.number_input(
                                    "% de quartzo (sílica livre cristalizada)",
                                    min_value=0.0,
                                    max_value=100.0,
                                    format="%.2f",
                                    key="medicao_quartzo",
                                )
                            elif agente_medicao == "poeira_nao_classificada":
                                st.caption("Poeira não classificada: fração respirável (NR-07 Anexo III, Quadro 2).")
                        with col_laudo:
                            st.date_input("Data da medição", format="DD/MM/YYYY", key="medicao_data")
                            st.text_input("Laudo (número ou elaborador)", key="medicao_laudo")
                            st.text_input("Método (ex.: NHO-08)", key="medicao_metodo")
                            st.text_input("Informado por", key="medicao_informante")
                        st.button("Registrar medição", key="registrar_medicao", on_click=_registrar_medicao)
                    mensagem_medicao = st.session_state.pop("medicao_mensagem", None)
                    if mensagem_medicao is not None:
                        tipo_msg, texto_msg = mensagem_medicao
                        (st.success if tipo_msg == "success" else st.warning)(texto_msg)
                    for medicao_registrada in cache_vinculo.medicoes:
                        unidade_exibida = "mg/m³" if medicao_registrada.unidade == "mg/m3" else medicao_registrada.unidade
                        detalhe_poeira = ""
                        if medicao_registrada.fracao is not None:
                            detalhe_poeira = " (" + ("respirável" if medicao_registrada.fracao is Fracao.RESPIRAVEL else "total")
                            if medicao_registrada.pct_quartzo is not None:
                                detalhe_poeira += f", {medicao_registrada.pct_quartzo:g}% quartzo"
                            detalhe_poeira += ")"
                        st.write(
                            f"**{medicao_registrada.ghe_id}** · {medicao_registrada.agente}: "
                            f"{medicao_registrada.valor:g} {unidade_exibida}{detalhe_poeira} — laudo "
                            f"{medicao_registrada.procedencia.laudo}, "
                            f"{medicao_registrada.procedencia.data:%d/%m/%Y}"
                        )
                        st.button(
                            "Remover",
                            key=f"remover_medicao_{medicao_registrada.ghe_id}_{medicao_registrada.agente}",
                            on_click=_remover_medicao,
                            args=(medicao_registrada.ghe_id, medicao_registrada.agente),
                        )

        renderizar_vinculos = _renderizar_vinculos

        if arquivo is None:
            st.session_state.pop("web_matriz_cache", None)
            return

        conteudo_pdf = arquivo.getvalue()

        with etapa_pgr, st.form("cabecalho_rodape_envelope"):
            col_documento, col_responsaveis, col_pgr = st.columns(3)
            with col_documento:
                st.markdown("**Identificação do documento**")
                empresa = st.text_input("Empresa")
                obra = st.text_input("Obra")
                tipo_documento = st.text_input("Tipo de documento")
                data_documento = st.text_input("Data")
                medico_coordenador = st.text_input("Médico coordenador")
                crm = st.text_input("CRM")

            with col_responsaveis:
                st.markdown("**Responsáveis**")
                responsavel_preenchimento = st.text_input("Responsável pelo preenchimento")
                medico_validador = st.text_input("Médica validadora")
                data_pgr = st.text_input("Data do PGR no rodapé (texto livre)")

            with col_pgr:
                st.markdown("**Dados do PGR**")
                validade = st.text_input("Data de emissão do PGR (AAAA-MM-DD)")
                st.caption(
                    "Data em que o PGR foi emitido, não a de vencimento. PGR emitido há "
                    "2 anos ou mais é rejeitado (R-PGR-06)."
                )
                assinatura = st.checkbox("Assinado por engenheiro de segurança")

            enviado = st.form_submit_button("Gerar matriz", type="primary")

        if not enviado and cache is None:
            return

        faltando_responsavel = responsavel_pcmso_incompleto(medico_coordenador, crm)
        if faltando_responsavel:
            etapa_pgr.error(
                "Preencha " + " e ".join(faltando_responsavel)
                + " antes de gerar a matriz — o documento do PCMSO sai com o médico responsável."
            )
            bloqueio = "preencha médico coordenador e CRM na etapa 1"
            return

        try:
            envelope = montar_envelope(validade, assinatura)
        except EmissaoFuturaError:
            etapa_pgr.error(MENSAGEM_EMISSAO_FUTURA.format(validade))
            bloqueio = "corrija a data de emissão do PGR na etapa 1"
            return
        except ValueError:
            etapa_pgr.error(f"Data inválida: {validade!r}. Use o formato ISO (AAAA-MM-DD).")
            bloqueio = "corrija a data de emissão do PGR na etapa 1"
            return

        cabecalho = CabecalhoDocumento(
            empresa=empresa,
            obra=obra,
            tipo_documento=tipo_documento,
            data=data_documento,
            medico_coordenador=medico_coordenador,
            crm=crm,
        )
        rodape = RodapeDocumento(
            responsavel_preenchimento=responsavel_preenchimento,
            medico_validador=medico_validador,
            data_pgr=data_pgr,
        )

        with tempfile.TemporaryDirectory() as tmp:
            caminho_pdf = Path(tmp) / arquivo.name
            caminho_pdf.write_bytes(conteudo_pdf)

            with etapa_pgr, st.spinner("Processando PGR — o parse do PDF pode levar alguns minutos..."):
                doc, html, pendencias, cache = executar_rota_determinista_cacheada(
                    caminho_pdf, conteudo_pdf, envelope, cabecalho, rodape, cache
                )

            if cache.anexos_descartados:
                etapa_pgr.warning(
                    "PGR reprocessado: anexos não reaplicados porque o GHE não existe mais — "
                    + "; ".join(f"{nome} ({ghe_id})" for ghe_id, nome in cache.anexos_descartados)
                )
                cache = dataclasses.replace(cache, anexos_descartados=())

            # Elo A (003.EQ emenda 3): gate eliminatório (R-PGR-01/R-PGR-06) é
            # parada dura — Resultado(status="REJEITADO", matrizes=[]) tem
            # matrizes=() != None, então o guard `doc is None` mais abaixo NUNCA
            # pegava esse ramo; documento vazio assinável saía com os dois
            # downloads. Checa ANTES de gerar docx/gravar cache.
            if cache.status == "REJEITADO":
                with etapa_pgr:
                    st.error("PGR rejeitado — pendências bloqueantes impedem a emissão da matriz:")
                    for p in cache.pendencias_globais:
                        if p.bloqueante:
                            st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")
                # Elo D: nunca grava cache de um estado REJEITADO — a chave não
                # pode mascarar a rejeição num rerun (ex.: clique de download de
                # uma submissão anterior bem-sucedida ainda em session_state).
                st.session_state.pop("web_matriz_cache", None)
                bloqueio = "PGR rejeitado — veja o motivo na etapa 1"
                return

            docx_bytes = None
            if doc is not None:
                destino_docx = Path(tmp) / "matriz.docx"
                renderizar_docx(doc, destino_docx)
                docx_bytes = destino_docx.read_bytes()

        st.session_state["web_matriz_cache"] = cache

        if doc is None or html is None:
            with etapa_pgr:
                st.error("Parse total falho — nenhuma matriz gerada (D-ARQ-22).")
                for p in pendencias:
                    st.write(f"- `{p.tipo}`: {p.motivo}")
            bloqueio = "nenhuma matriz gerada — veja a etapa 1"
            return

        caixa_conferencia = etapa_conferencia.container(border=True)
        caixa_conferencia.subheader("3. Conferência — pendências")

        # Elo B: pendências GLOBAIS (D-ARQ-08, prioridade visual) sempre entram
        # na tela, em bloco próprio, ANTES das pendências de extração/hidratação
        # — senão as centenas de vocabulario_ausente afogam a única que importa.
        if cache.pendencias_globais:
            with caixa_conferencia:
                st.markdown("**Pendências (itens a confirmar)**")
                for p in cache.pendencias_globais:
                    st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")

        if pendencias:
            with caixa_conferencia.expander(f"Pendências de extração e vocabulário ({len(pendencias)})"):
                for p in pendencias:
                    st.write(f"- `{p.tipo}`: {p.motivo}")

        if not cache.pendencias_globais and not pendencias:
            caixa_conferencia.caption("Nenhuma pendência a confirmar.")

        # Elo C: guarda anti-documento-vazio, independente do gate — documento
        # assinável sem nenhuma linha de cargo (nenhum exame emitido) não sai da
        # máquina em hipótese nenhuma (D-ARQ-22).
        total_linhas_cargo = sum(len(bloco.linhas) for bloco in doc.blocos)
        if total_linhas_cargo == 0:
            etapa_pgr.error(
                "Documento sem nenhuma linha de cargo — nenhum exame emitido. "
                "Nenhum download oferecido (D-ARQ-22)."
            )
            bloqueio = "documento sem linha de cargo — veja a etapa 1"
            return

        # Aviso de procedência (003.EW, D-ARQ-22 revisão de saída): a matriz muda
        # de proveniência quando algum bloco veio da rota LLM (família não
        # reconhecida pela rota determinística) — o operador precisa saber antes
        # de levar o documento para assinatura. Zero chamadas é o caminho normal
        # e não merece ruído na tela.
        if cache.chamadas_ia > 0:
            caixa_conferencia.info(
                f"{cache.chamadas_ia} bloco(s) lido(s) por IA — layout não "
                "reconhecido pela rota determinística. Confira a matriz com "
                "atenção redobrada."
            )

        matriz_gerada = True
        caixa_matriz = etapa_matriz.container(border=True)
        with caixa_matriz:
            st.subheader("4. Matriz e downloads")
            # Chamada via `st.download_button` dentro de `with coluna`, nunca
            # `coluna.download_button`: os testes espionam o atributo do módulo.
            col_docx, col_html = st.columns(2)
            if docx_bytes is not None:
                with col_docx:
                    st.download_button(
                        "Baixar DOCX",
                        docx_bytes,
                        file_name="matriz.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        type="primary",
                    )
            with col_html:
                st.download_button("Baixar HTML", html, file_name="matriz.html", mime="text/html")

            for bloco in doc.blocos:
                st.subheader(f"GHE {bloco.ghe_id} {bloco.nome_ghe}".strip())
                for linha in bloco.linhas:
                    st.write(f"**{linha.cargo}**: {', '.join(linha.celulas)}")

            if cache.matrizes:
                st.subheader("Revisão — origem dos exames (não entra no documento)")
                revisoes = montar_revisao(
                    cache.matrizes, cache.exames_vocab, _protocolo_padrao().vocabulario.agentes
                )
                for revisao in revisoes:
                    with st.expander(f"GHE {revisao.ghe_id} {nome_ghe_exibicao(revisao.nome_ghe)}".strip()):
                        # Tabela em markdown, não st.table: st.table importa pandas no
                        # primeiro render da sessão (medido: +9 s a frio no container).
                        st.markdown(tabela_markdown(revisao))
                        st.caption("Decreto 3.048/1999, Anexo IV — referência previdenciária, não exame.")
                        for enq in revisao.enquadramentos:
                            st.write(f"- {enq.agente}: {enq.enquadramento}")
    finally:
        # Preenchido por último (inclusive após os returns antecipados) para
        # refletir o estado deste rerun, não o do anterior.
        if renderizar_vinculos is not None:
            renderizar_vinculos(st.session_state.get("web_matriz_cache"))
        if bloqueio is not None:
            pendente = f"bloqueada: {bloqueio}."
        elif arquivo is None:
            pendente = "envie o PDF do PGR na etapa 1."
        else:
            pendente = "preencha a identificação e clique em Gerar matriz na etapa 1."
        if caixa_conferencia is None:
            etapa_conferencia.caption(f"**3. Conferência — pendências** · {pendente}")
        if caixa_matriz is None:
            etapa_matriz.caption(f"**4. Matriz e downloads** · {pendente}")
        with indicador.container():
            col_1, col_2, col_3, col_4 = st.columns(4)
            col_1.markdown(("✅" if matriz_gerada else "⛔" if bloqueio else "⬜") + " **1. PGR e identificação**")
            col_2.markdown("➖ **2. FDS/FISPQ e medições** (opcional)")
            col_3.markdown(("✅" if matriz_gerada else "⬜") + " **3. Conferência**")
            col_4.markdown(("✅" if matriz_gerada else "⬜") + " **4. Matriz e downloads**")


if __name__ == "__main__":
    pagina_matriz()
