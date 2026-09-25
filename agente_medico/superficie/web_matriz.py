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
from typing import Any, Sequence

from agente_medico.adaptadores.orquestracao_fds import preparar_composicao
from agente_medico.adaptadores.orquestracao_pgr import preparar_pgr_hidratado
from agente_medico.adaptadores.transcritor_gemini import TranscritorGemini
from agente_medico.adaptadores.transcritor_gemini_card import TranscritorGeminiCard
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import (
    FDS,
    PGR,
    BlocoVerbatim,
    EnvelopeConfirmado,
    GHEVerbatim,
    MatrizGHE,
    Pendencia,
    ProdutoQuimico,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_fds import TranscritorLLM
from agente_medico.motor.transcritor_pgr import TranscritorGHE
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
]


def montar_envelope(validade_iso: str, assinatura: bool) -> EnvelopeConfirmado:
    """Mesmo espelho de mensagem que montar_volta_envelope (web_envelope.py):
    ValueError na validade malformada, nunca coagida silenciosamente."""
    validade = date.fromisoformat(validade_iso)
    return EnvelopeConfirmado(validade=validade, assinatura_engenheiro=assinatura)


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
    existe mais — a casca avisa uma vez e limpa."""

    chave: str
    matrizes: tuple[MatrizGHE, ...] | None
    exames_vocab: dict[str, Any]
    pendencias: tuple[Pendencia, ...]
    status: str | None
    pendencias_globais: tuple[Pendencia, ...]
    chamadas_ia: int
    pgr_hidratado: PGR | None
    anexos_descartados: tuple[tuple[str, str], ...] = ()


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
    resultado = processar_pgr(pgr_atualizado, protocolo)
    return dataclasses.replace(
        cache,
        pgr_hidratado=pgr_atualizado,
        matrizes=tuple(resultado.matrizes),
        status=resultado.status,
        pendencias_globais=tuple(resultado.pendencias_globais),
    )


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

    from agente_medico.superficie.documento_matriz import (
        CabecalhoDocumento,
        RodapeDocumento,
        renderizar_docx,
    )
    from agente_medico.motor.tipos import BlocoVerbatim
    from agente_medico.superficie.revisao_matriz import montar_revisao, tabela_markdown
    from agente_medico.superficie.web_matriz import (
        TranscritorGemini,
        _protocolo_padrao,
        anexar_produto_em_ghes,
        executar_rota_determinista_cacheada,
        ghes_com_produto,
        listar_produtos_anexados,
        montar_envelope,
        montar_fds,
        preparar_composicao_cacheada,
        remover_produto_e_reprocessar,
    )

    st.title("Matriz de Exames — PCMSO")

    arquivo = st.file_uploader("PDF do PGR", type="pdf")

    # Cache lido AQUI (não só mais abaixo, junto do form) para que o bloco de
    # FDS avulsa, a seguir, saiba se há um PGR já carregado na tela (D-ARQ-49
    # Parte 2 fatia 2b) — mesmo objeto, sem novo fetch de session_state depois:
    # a mutação feita pelo botão "Anexar" abaixo tem que sobreviver até o
    # write final de st.session_state no fim da função, no MESMO rerun.
    cache: CacheMatrizes | None = st.session_state.get("web_matriz_cache")

    st.subheader("FDS/FISPQ dos produtos químicos (opcional)")
    st.caption(
        "Extrai CAS e frases-H de cada FDS enviada, com ou sem PGR. Para vincular uma "
        "FDS a GHEs: 1) envie o PGR e clique em Gerar matriz; 2) volte aqui — cada FDS "
        "passa a mostrar a escolha de GHEs e o botão Anexar (D-ARQ-49 Parte 2 fatia 2b)."
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

    for arquivo_fds in arquivos_fds or ():
        st.write(f"**{arquivo_fds.name}**")
        with tempfile.TemporaryDirectory() as tmp_fds:
            caminho_fds = Path(tmp_fds) / arquivo_fds.name
            conteudo_fds = arquivo_fds.getvalue()
            caminho_fds.write_bytes(conteudo_fds)
            with st.spinner(f"Lendo composição de {arquivo_fds.name}..."):
                blocos_fds, pendencias_fds = preparar_composicao_cacheada(
                    caminho_fds, conteudo_fds, TranscritorGemini(), cache_fds
                )
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
        # PGR já carregado (cache.pgr_hidratado not None) e composição extraída
        # (blocos_fds não-vazio) — sem PGR, comportamento idêntico ao de hoje.
        # A lista de GHEs só existe depois do parse do PGR (Gerar matriz). Sem
        # este aviso a FDS aparecia sem nenhuma forma de vínculo e sem dizer por quê.
        if blocos_fds and (cache is None or cache.pgr_hidratado is None):
            st.info("Gere a matriz para vincular esta FDS a um GHE.")
        if cache is not None and cache.pgr_hidratado is not None and blocos_fds:
            ghes_pgr = cache.pgr_hidratado.ghes
            rotulos_ghe = {ghe.id: f"{ghe.id} — {ghe.nome}".strip(" —") for ghe in ghes_pgr}
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
            assert cache.pgr_hidratado is not None
            anexada_em = ghes_com_produto(cache.pgr_hidratado, nome_produto)
            if anexada_em:
                st.caption(f"Status: anexada a {', '.join(anexada_em)}.")
            else:
                st.caption("Status: ainda não anexada a nenhum GHE.")

    if arquivo is not None and cache is not None and cache.pgr_hidratado is not None:
        st.subheader("Produtos anexados")
        # listar_produtos_anexados carrega o protocolo; sem produto não há o que resolver.
        produtos_anexados = (
            listar_produtos_anexados(cache.pgr_hidratado, _protocolo_padrao())
            if any(ghe.produtos_quimicos for ghe in cache.pgr_hidratado.ghes)
            else ()
        )
        if not produtos_anexados:
            st.caption("Nenhum produto anexado.")
        for produto_anexado in produtos_anexados:
            st.write(
                f"**{produto_anexado.ghe_id} — {produto_anexado.ghe_nome}** · {produto_anexado.nome}"
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

    if arquivo is None:
        st.session_state.pop("web_matriz_cache", None)
        return

    conteudo_pdf = arquivo.getvalue()

    with st.form("cabecalho_rodape_envelope"):
        st.subheader("Identificação do documento")
        empresa = st.text_input("Empresa")
        obra = st.text_input("Obra")
        tipo_documento = st.text_input("Tipo de documento")
        data_documento = st.text_input("Data")
        medico_coordenador = st.text_input("Médico coordenador")
        crm = st.text_input("CRM")

        st.subheader("Responsáveis")
        responsavel_preenchimento = st.text_input("Responsável pelo preenchimento")
        medico_validador = st.text_input("Médica validadora")
        data_pgr = st.text_input("Data do PGR")

        st.subheader("Dados do PGR")
        validade = st.text_input("Validade do PGR (AAAA-MM-DD)")
        assinatura = st.checkbox("Assinado por engenheiro de segurança")

        enviado = st.form_submit_button("Gerar matriz")

    if not enviado and cache is None:
        return

    try:
        envelope = montar_envelope(validade, assinatura)
    except ValueError:
        st.error(f"Data inválida: {validade!r}. Use o formato ISO (AAAA-MM-DD).")
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

        with st.spinner("Processando PGR — o parse do PDF pode levar alguns minutos..."):
            doc, html, pendencias, cache = executar_rota_determinista_cacheada(
                caminho_pdf, conteudo_pdf, envelope, cabecalho, rodape, cache
            )

        if cache.anexos_descartados:
            st.warning(
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
            st.error("PGR rejeitado — pendências bloqueantes impedem a emissão da matriz:")
            for p in cache.pendencias_globais:
                if p.bloqueante:
                    st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")
            # Elo D: nunca grava cache de um estado REJEITADO — a chave não
            # pode mascarar a rejeição num rerun (ex.: clique de download de
            # uma submissão anterior bem-sucedida ainda em session_state).
            st.session_state.pop("web_matriz_cache", None)
            return

        docx_bytes = None
        if doc is not None:
            destino_docx = Path(tmp) / "matriz.docx"
            renderizar_docx(doc, destino_docx)
            docx_bytes = destino_docx.read_bytes()

    st.session_state["web_matriz_cache"] = cache

    if doc is None or html is None:
        st.error("Parse total falho — nenhuma matriz gerada (D-ARQ-22).")
        for p in pendencias:
            st.write(f"- `{p.tipo}`: {p.motivo}")
        return

    # Elo B: pendências GLOBAIS (D-ARQ-08, prioridade visual) sempre entram
    # na tela, em bloco próprio, ANTES das pendências de extração/hidratação
    # — senão as centenas de vocabulario_ausente afogam a única que importa.
    if cache.pendencias_globais:
        st.subheader("Pendências (itens a confirmar)")
        for p in cache.pendencias_globais:
            st.write(f"- `{p.tipo}` ({p.regra_origem}): {p.motivo}")

    if pendencias:
        st.subheader("Pendências (itens a confirmar)")
        for p in pendencias:
            st.write(f"- `{p.tipo}`: {p.motivo}")

    # Elo C: guarda anti-documento-vazio, independente do gate — documento
    # assinável sem nenhuma linha de cargo (nenhum exame emitido) não sai da
    # máquina em hipótese nenhuma (D-ARQ-22).
    total_linhas_cargo = sum(len(bloco.linhas) for bloco in doc.blocos)
    if total_linhas_cargo == 0:
        st.error(
            "Documento sem nenhuma linha de cargo — nenhum exame emitido. "
            "Nenhum download oferecido (D-ARQ-22)."
        )
        return

    # Aviso de procedência (003.EW, D-ARQ-22 revisão de saída): a matriz muda
    # de proveniência quando algum bloco veio da rota LLM (família não
    # reconhecida pela rota determinística) — o operador precisa saber antes
    # de levar o documento para assinatura. Zero chamadas é o caminho normal
    # e não merece ruído na tela.
    if cache.chamadas_ia > 0:
        st.info(
            f"{cache.chamadas_ia} bloco(s) lido(s) por IA — layout não "
            "reconhecido pela rota determinística. Confira a matriz com "
            "atenção redobrada."
        )

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
            with st.expander(f"GHE {revisao.ghe_id} {revisao.nome_ghe}".strip()):
                # Tabela em markdown, não st.table: st.table importa pandas no
                # primeiro render da sessão (medido: +9 s a frio no container).
                st.markdown(tabela_markdown(revisao))
                st.caption("Decreto 3.048/1999, Anexo IV — referência previdenciária, não exame.")
                for enq in revisao.enquadramentos:
                    st.write(f"- {enq.agente}: {enq.enquadramento}")

    st.download_button("Baixar HTML", html, file_name="matriz.html", mime="text/html")
    if docx_bytes is not None:
        st.download_button(
            "Baixar DOCX",
            docx_bytes,
            file_name="matriz.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


if __name__ == "__main__":
    pagina_matriz()
