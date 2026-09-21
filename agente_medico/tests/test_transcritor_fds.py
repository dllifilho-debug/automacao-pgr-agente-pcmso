from __future__ import annotations

import unicodedata
from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.composicao import resolver_composicao
from agente_medico.motor.extracao_fds import extrair_texto_fds
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.tipos import (
    FDS,
    GHEPGR,
    PGR,
    BlocoVerbatim,
    MembroVerbatim,
    ProdutoQuimico,
)
from agente_medico.motor.transcricao_fds import montar_fds
from agente_medico.motor.transcritor_fds import gate_forma, transcrever_fds
from agente_medico.tests.fixtures.fds_t65 import cimento_ciplan, tinta_acrilica
from agente_medico.tests.fixtures.fds_verbatim_leinertex import (
    leinertex_derivados_verbatim,
)
from agente_medico.tests.fixtures.fds_verbatim_t65 import (
    cimento_ciplan_verbatim,
    tinta_acrilica_verbatim,
)

PASTA = Path("fds_originais")
TINTA = PASTA / "tinta_acrilica.pdf"
CIPLAN = PASTA / "01 - FISPQ_cimento - Ciplan.pdf"

# Harness de integração cobre só tinta acrílica + Ciplan (fixtures verbatim
# existentes, 003.AZ). Adesivo Tigre fica fora (D-ARQ-22): a medição 003.BD
# provou transcritível (7/7), mas a fixture verbatim do Tigre é dado de
# julgamento humano (Arquiteto), fora do recorte desta fatia.
requer_pdfs = pytest.mark.skipif(
    not TINTA.exists() or not CIPLAN.exists(),
    reason="PDFs de fds_originais/ ausentes (untracked); harness integração 003.BF indisponível",
)

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)
_INDICE = construir_indice_cas(_PROTO.vocabulario.agentes)


class MockTranscritor:
    def __init__(self, resultado: tuple[BlocoVerbatim, ...]) -> None:
        self._resultado = resultado
        self.texto_recebido: str = ""

    def transcrever(self, texto: str) -> tuple[BlocoVerbatim, ...]:
        self.texto_recebido = texto
        return self._resultado


def _normalizar(texto: str) -> str:
    sem_acento = "".join(
        c for c in unicodedata.normalize("NFD", texto) if not unicodedata.combining(c)
    )
    return sem_acento.upper()


def _pgr_com_fds(fds: FDS) -> PGR:
    return PGR(
        validade=date(2026, 1, 1),
        assinatura_engenheiro=True,
        ghes=(
            GHEPGR(
                id="G1",
                nome="GHE 1",
                cargos=("c",),
                riscos=(),
                epis=(),
                produtos_quimicos=(ProdutoQuimico(nome="Produto", fds=fds),),
                psicossocial=False,
            ),
        ),
    )


# ---------------------------------------------------------------------------
# Núcleo — rodam sempre, sem PDF.
# ---------------------------------------------------------------------------


def test_transcrever_fds_delega_ao_cliente_e_recebe_o_texto() -> None:
    resultado = tinta_acrilica_verbatim()
    mock = MockTranscritor(resultado)
    saida = transcrever_fds("texto de entrada", mock)
    assert saida == resultado
    assert mock.texto_recebido == "texto de entrada"


def test_gate_forma_aprova_integralmente_as_fixtures_existentes() -> None:
    for fixture in (
        tinta_acrilica_verbatim(),
        cimento_ciplan_verbatim(),
        leinertex_derivados_verbatim(),
    ):
        aprovados, pendencias = gate_forma(fixture)
        assert aprovados == fixture
        assert pendencias == ()


def test_faixa_vazia_com_membro_nomeado_e_aprovada() -> None:
    bloco = BlocoVerbatim(faixa="", membros=(MembroVerbatim(cas="", nome="Solvente"),))
    aprovados, pendencias = gate_forma([bloco])
    assert aprovados == (bloco,)
    assert pendencias == ()


def test_faixa_ininteligivel_e_reprovada_com_pendencia_bloqueante() -> None:
    bloco = BlocoVerbatim(faixa="abc", membros=(MembroVerbatim(cas="123-45-6", nome="X"),))
    aprovados, pendencias = gate_forma([bloco])
    assert aprovados == ()
    assert len(pendencias) == 1
    pendencia = pendencias[0]
    assert pendencia.tipo == "forma_verbatim_fds"
    assert pendencia.bloqueante is True
    assert pendencia.destinatario == "extracao"
    assert pendencia.regra_origem == "D-ARQ-47"


def test_bloco_sem_membro_nomeado_e_reprovado() -> None:
    sem_membros = BlocoVerbatim(faixa="1 - 2", membros=())
    nome_em_branco = BlocoVerbatim(
        faixa="1 - 2", membros=(MembroVerbatim(cas="1-2-3", nome=" "),)
    )
    for bloco in (sem_membros, nome_em_branco):
        aprovados, pendencias = gate_forma([bloco])
        assert aprovados == ()
        assert len(pendencias) == 1
        assert pendencias[0].tipo == "forma_verbatim_fds"


def test_gate_nao_valida_cas() -> None:
    bloco = BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim(cas="LIXO-TOTAL", nome="X"),))
    aprovados, pendencias = gate_forma([bloco])
    assert aprovados == (bloco,)
    assert pendencias == ()


def test_mistura_bom_ruim_bom_preserva_ordem_dos_aprovados() -> None:
    bom1 = BlocoVerbatim(faixa="1 - 2", membros=(MembroVerbatim(cas="1-2-3", nome="A"),))
    ruim = BlocoVerbatim(faixa="xyz", membros=(MembroVerbatim(cas="1-2-3", nome="B"),))
    bom2 = BlocoVerbatim(faixa="3 - 4", membros=(MembroVerbatim(cas="1-2-3", nome="C"),))
    aprovados, pendencias = gate_forma([bom1, ruim, bom2])
    assert aprovados == (bom1, bom2)
    assert len(pendencias) == 1


def test_faixas_semiabertas_e_endash_sao_aprovadas() -> None:
    for faixa in ("< 5", "> 1", "10 – 42"):
        bloco = BlocoVerbatim(faixa=faixa, membros=(MembroVerbatim(cas="1-2-3", nome="X"),))
        aprovados, pendencias = gate_forma([bloco])
        assert aprovados == (bloco,)
        assert pendencias == ()


def test_faixas_reais_sem_hifen_sao_aprovadas() -> None:
    # DT-(sessão branch docs/003fi-achado-gate-forma-faixa)-01: antes do
    # fallback de _SEPARADOR_FAIXA, estes 3 blocos reais reprovavam no gate
    # de forma (bloqueante) mesmo com CAS/nome íntegros.
    for faixa in ("15 19", "30 70", "35 a 50"):
        bloco = BlocoVerbatim(faixa=faixa, membros=(MembroVerbatim(cas="1-2-3", nome="X"),))
        aprovados, pendencias = gate_forma([bloco])
        assert aprovados == (bloco,)
        assert pendencias == ()


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs; espelha test_extrair_texto_fds.py).
# Composição fim-a-fim (transcrever_fds -> gate_forma -> montar_fds ->
# resolver_composicao) SÓ existe aqui, nunca em função de produção (D-ARQ-47
# cl.4 — a revisão-RT é a admissão do candidato).
# ---------------------------------------------------------------------------


@requer_pdfs
def test_tinta_harness_mockado_bate_gabarito_cas_e_concentracao() -> None:
    texto = extrair_texto_fds(TINTA)
    assert texto is not None

    mock = MockTranscritor(tinta_acrilica_verbatim())
    candidato = transcrever_fds(texto, mock)
    assert "COMPOSICAO E INFORMACOES SOBRE" in _normalizar(mock.texto_recebido)

    aprovados, pendencias = gate_forma(candidato)
    assert pendencias == ()

    fds = montar_fds(aprovados)
    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), _INDICE)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    comps = resolvido.composicao
    gabarito = tinta_acrilica()

    assert len(comps) == len(gabarito)
    for c, g in zip(comps, gabarito):
        assert c.cas == g.cas
        assert c.concentracao == g.concentracao


@requer_pdfs
def test_ciplan_harness_mockado_bate_gabarito_cas_e_concentracao() -> None:
    texto = extrair_texto_fds(CIPLAN)
    assert texto is not None

    mock = MockTranscritor(cimento_ciplan_verbatim())
    candidato = transcrever_fds(texto, mock)
    assert "COMPOSICAO E INFORMACOES SOBRE" in _normalizar(mock.texto_recebido)

    aprovados, pendencias = gate_forma(candidato)
    assert pendencias == ()

    fds = montar_fds(aprovados)
    pgr_out, _pend = resolver_composicao(_pgr_com_fds(fds), _INDICE)
    resolvido = pgr_out.ghes[0].produtos_quimicos[0].fds
    assert resolvido is not None
    comps = resolvido.composicao
    gabarito = cimento_ciplan()

    assert len(comps) == len(gabarito)
    for c, g in zip(comps, gabarito):
        assert c.cas == g.cas
        assert c.concentracao == g.concentracao
