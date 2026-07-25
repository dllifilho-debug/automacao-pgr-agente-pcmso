from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from unittest.mock import patch

import pytest

from agente_medico.adaptadores.orquestracao_pgr import (
    preparar_envelope,
    preparar_ghes,
    processar_arquivo_pgr,
)
from agente_medico.adaptadores.transcritor_gemini import TranscricaoIndisponivel
from agente_medico.motor.extracao_pgr import eh_cabecalho_ghe
from agente_medico.motor.parser_familia_consciente import FamiliaNaoReconhecida
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.motor.tipos import EnvelopeConfirmado, EnvelopeVerbatim, GHEVerbatim, RiscoVerbatim

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_PROTO = carregar(_PROTOCOLO_DIR)

_MATRIZES_DIR = Path(__file__).parent.parent.parent / "matrizes_originais"
_PDF_VIVERDE = _MATRIZES_DIR / "PGR VIVERDE V02 - 03.02.25.pdf"
_PDF_EBSERH_UFGD_V7 = _MATRIZES_DIR / "PGR_EBSERH_UFGD_v7.pdf"
_PDF_EBSERH_HUMAP = _MATRIZES_DIR / "PGR_EBSERH_HUMAP.pdf"
_PDF_CJR = _MATRIZES_DIR / "pgr_Cjr Engenharia Ltda (M Construtora).pdf"
_PDF_FASCINO = _MATRIZES_DIR / "PGR - CONSCIENTE CONSTRUTORA E INCORPORADORA SPE 0030 - FASCINO  (15.07.26).pdf"

# Harness de integração da rota determinística (molde requer_pdfs de
# test_parser_familia_consciente.py, 003.DZ).
requer_pdfs = pytest.mark.skipif(
    not (_PDF_FASCINO.exists() and _PDF_VIVERDE.exists()),
    reason="PDF Fascino/Viverde ausente; harness integração 003.EA indisponível",
)

_ALVO_EXTRACAO = "agente_medico.adaptadores.orquestracao_pgr.extrair_texto_pgr"
_ALVO_PARSER_DETERMINISTICO = "agente_medico.adaptadores.orquestracao_pgr.parsear_arquivo"

_GHE_VALIDO = GHEVerbatim(
    nome="Setor Teste",
    cargos=("pintor",),
    riscos=(RiscoVerbatim(agente="Ruido", quantificacao="82,2 dB(A)", fonte_geradora="Fonte X"),),
)
_GHE_INVALIDO = GHEVerbatim(nome="", cargos=(), riscos=())

_ENVELOPE_PADRAO = EnvelopeConfirmado(validade=date.today(), assinatura_engenheiro=True)


def _paginas_com_bloco(nome_setor: str = "Setor Teste") -> list[str]:
    return [f"GHE 1 - {nome_setor}\nCargo A\nOutraLinha"]


def _paginas_com_card() -> list[str]:
    return ["Lotação: Escala de Trabalho: Qtde:\nSetor Teste 40hs/semana 1 - Efetivo\nCargo A"]


class MockTranscritorConstante:
    """Devolve o MESMO GHEVerbatim canned para todo bloco recebido."""

    def __init__(self, resposta: GHEVerbatim) -> None:
        self._resposta = resposta
        self.blocos_recebidos: list[str] = []

    def transcrever(self, bloco: str) -> GHEVerbatim:
        self.blocos_recebidos.append(bloco)
        return self._resposta


class MockTranscritorSequencial:
    """Devolve um GHEVerbatim distinto por chamada, na ordem dada."""

    def __init__(self, respostas: tuple[GHEVerbatim, ...]) -> None:
        self._respostas = respostas
        self.blocos_recebidos: list[str] = []

    def transcrever(self, bloco: str) -> GHEVerbatim:
        resposta = self._respostas[len(self.blocos_recebidos)]
        self.blocos_recebidos.append(bloco)
        return resposta


class MockTranscritorIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel(self._motivo)


class MockTranscritorGHENuncaChamado:
    """Cliente-bomba: se a rota determinística for aceita (D-ARQ-65 fatia 2),
    preparar_ghes NUNCA deve invocar o cliente LLM — falha alto e explícito
    em vez de mascarar em silêncio uma invocação indevida (molde
    MockTranscritorCardNuncaChamado)."""

    def transcrever(self, bloco: str) -> GHEVerbatim:
        raise AssertionError("cliente LLM não deveria ser invocado — rota determinística aceita")


class MockTranscritorCardConstante:
    """Devolve o MESMO GHEVerbatim canned para todo par (card, titulo)
    recebido — molde MockTranscritorConstante, D-ARQ-57 peça 4 fatia 4d."""

    def __init__(self, resposta: GHEVerbatim) -> None:
        self._resposta = resposta
        self.pares_recebidos: list[tuple[str, str]] = []

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        self.pares_recebidos.append((card, titulo))
        return self._resposta


class MockTranscritorCardIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        raise TranscricaoIndisponivel(self._motivo)


class MockTranscritorCardNuncaChamado:
    """Dummy para a rota ghe: se preparar_ghes chamar cliente_card fora da
    rota card, isso é bug de roteamento — falha alto e explícito em vez de
    devolver silenciosamente um GHEVerbatim válido."""

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        raise AssertionError("cliente_card não deveria ser invocado na rota ghe")


_CLIENTE_CARD_NUNCA_CHAMADO = MockTranscritorCardNuncaChamado()


class MockTranscritorTopoConstante:
    """Devolve o MESMO EnvelopeVerbatim canned para todo topo recebido."""

    def __init__(self, resposta: EnvelopeVerbatim) -> None:
        self._resposta = resposta
        self.topos_recebidos: list[str] = []

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        self.topos_recebidos.append(topo)
        return self._resposta


class MockTranscritorTopoIndisponivel:
    def __init__(self, motivo: str) -> None:
        self._motivo = motivo

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        raise TranscricaoIndisponivel(self._motivo)


def test_e2e_arquivo_real_ate_resultado_com_transcritor_mockado() -> None:
    mock = MockTranscritorConstante(_GHE_VALIDO)
    resultado, pendencias = processar_arquivo_pgr(
        _PDF_VIVERDE, _PROTO, mock, _CLIENTE_CARD_NUNCA_CHAMADO, envelope=_ENVELOPE_PADRAO
    )

    assert resultado is not None
    assert len(mock.blocos_recebidos) > 0
    assert resultado.matrizes[0].ghe_id == "GHE-01"


def test_blocos_ausentes_vira_none_e_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=["página sem âncora nenhuma"]):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "blocos_ausentes"
    assert pendencias[0].bloqueante is True


def test_cargo_based_bloqueia_antes_da_transcricao() -> None:
    paginas = ["CARGO/FUNÇÃO: Pintor\nlinha\n"] * 3
    mock = MockTranscritorConstante(_GHE_VALIDO)
    with patch(_ALVO_EXTRACAO, return_value=paginas):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            mock,
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "pgr_cargo_based"
    assert pendencias[0].bloqueante is True
    assert pendencias[0].regra_origem == "D-ARQ-57"
    assert mock.blocos_recebidos == []


def test_segmentacao_implausivel_bloqueia_antes_da_transcricao() -> None:
    paginas = (
        ["GHE 1 - Setor A\nCargo A", "GHE 2 - Setor B\nCargo B"]
        + ["conteudo\n"] * 10
    )
    mock = MockTranscritorConstante(_GHE_VALIDO)
    with patch(_ALVO_EXTRACAO, return_value=paginas):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            mock,
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "segmentacao_implausivel"
    assert pendencias[0].bloqueante is True
    assert mock.blocos_recebidos == []


def test_doc_grande_sem_ancora_emite_segmentacao_nao_blocos_ausentes() -> None:
    paginas = ["linha qualquer\n"] * 12
    with patch(_ALVO_EXTRACAO, return_value=paginas):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "segmentacao_implausivel"


def test_transcricao_indisponivel_vira_none_e_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorIndisponivel("CHAVE_API_GOOGLE ausente"),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is None
    assert len(pendencias) == 2
    pendencia_bloqueante = next(p for p in pendencias if p.bloqueante)
    assert pendencia_bloqueante.tipo == "transcricao_indisponivel_pgr"
    assert "CHAVE_API_GOOGLE ausente" in pendencia_bloqueante.motivo
    pendencia_familia = next(p for p in pendencias if p.tipo == "familia_nao_medida")
    assert pendencia_familia.bloqueante is False
    assert pendencia_familia.regra_origem == "D-ARQ-65"


def test_aprovacao_parcial_processa_aprovados_e_carrega_pendencia_de_forma() -> None:
    paginas = [
        "GHE 1 - Setor Bom\nCargo A\n"
        "GHE 2 - Setor Ruim\nCargo B"
    ]
    mock = MockTranscritorSequencial((_GHE_VALIDO, _GHE_INVALIDO))
    with patch(_ALVO_EXTRACAO, return_value=paginas), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        resultado, pendencias = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            mock,
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=_ENVELOPE_PADRAO,
        )

    assert resultado is not None
    assert len(resultado.matrizes) == 1
    tipos_pendencia = [p.tipo for p in pendencias]
    assert "forma_verbatim_pgr" in tipos_pendencia
    assert "familia_nao_medida" in tipos_pendencia
    pendencia_forma = next(p for p in pendencias if p.tipo == "forma_verbatim_pgr")
    assert pendencia_forma.bloqueante is True


def test_envelope_validade_atravessa_ate_o_gate_r_pgr_06() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=EnvelopeConfirmado(validade=date(2025, 1, 1), assinatura_engenheiro=True),
            hoje=date(2027, 1, 1),
        )

    assert resultado is not None
    assert resultado.status == "REJEITADO"
    assert any(p.regra_origem == "R-PGR-06" for p in resultado.pendencias_globais)


# ---------------------------------------------------------------------------
# preparar_envelope — ida completa do envelope (D-ARQ-53 fatia 4)
# ---------------------------------------------------------------------------


_ENVELOPE_VIVERDE_GABARITO = EnvelopeVerbatim(
    validade_textos=("GOIÂNIA, FEVEREIRO 2023",),
    responsavel_tecnico="Fulano",
    titulo_rt="Engenheiro de Segurança",
    registro_profissional="CREA-GO 123",
)


def test_preparar_envelope_pdf_real_viverde_gera_artefato_com_proposta_pre_preenchida() -> None:
    mock = MockTranscritorTopoConstante(_ENVELOPE_VIVERDE_GABARITO)
    artefato, pendencias = preparar_envelope(_PDF_VIVERDE, mock)

    assert artefato is not None
    assert pendencias == ()
    assert len(mock.topos_recebidos) == 1
    topo_recebido = mock.topos_recebidos[0]
    # Inverso determinístico de recortar_blocos_ghe: nenhuma linha do topo
    # recebido é (ou vem depois d)a âncora de bloco GHE.
    assert not any(eh_cabecalho_ghe(linha) for linha in topo_recebido.splitlines())

    dados = json.loads(artefato)
    assert dados["confirmacao"]["validade"] == "2023-02-01"


def test_preparar_envelope_sem_ancora_de_topo_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=["página sem âncora nenhuma"]):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(_ENVELOPE_VIVERDE_GABARITO)
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "topo_ausente"
    assert pendencias[0].bloqueante is True


def test_preparar_envelope_transcricao_indisponivel_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoIndisponivel("CHAVE_API_GOOGLE ausente")
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_topo"
    assert pendencias[0].bloqueante is True
    assert "CHAVE_API_GOOGLE ausente" in pendencias[0].motivo


def test_preparar_envelope_integralmente_vazio_vira_pendencia_de_forma() -> None:
    envelope_vazio = EnvelopeVerbatim(
        validade_textos=(), responsavel_tecnico="", titulo_rt="", registro_profissional=""
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()):
        artefato, pendencias = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_vazio)
        )

    assert artefato is None
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "forma_verbatim_topo"
    assert pendencias[0].bloqueante is True


# ---------------------------------------------------------------------------
# Ida-e-volta completa: preparar_envelope -> confirmação-RT simulada ->
# processar_arquivo_pgr. Caso concreto DT-003BV-01 / R-PGR-06 (003.BX).
# ---------------------------------------------------------------------------


def test_ida_e_volta_validade_antiga_gera_pendencia_r_pgr_06_bloqueante() -> None:
    envelope_bruto = EnvelopeVerbatim(
        validade_textos=("FEVEREIRO 2023",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        artefato, pend_envelope = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_bruto)
        )
        assert pend_envelope == ()
        assert artefato is not None

        dados = json.loads(artefato)
        assert dados["confirmacao"]["validade"] == "2023-02-01"
        dados["confirmacao"]["assinatura_engenheiro"] = True
        envelope_confirmado = desserializar_confirmacao(json.dumps(dados))

        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=envelope_confirmado,
            hoje=date(2026, 7, 8),
        )

    assert resultado is not None
    pendencias_r06 = [p for p in resultado.pendencias_globais if p.regra_origem == "R-PGR-06"]
    assert len(pendencias_r06) == 1
    assert pendencias_r06[0].bloqueante is True


def test_ida_e_volta_validade_recente_nao_gera_pendencia_r_pgr_06() -> None:
    envelope_bruto = EnvelopeVerbatim(
        validade_textos=("FEVEREIRO 2025",),
        responsavel_tecnico="Fulano",
        titulo_rt="Eng.",
        registro_profissional="CREA 1",
    )
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        artefato, _ = preparar_envelope(
            Path("qualquer.pdf"), MockTranscritorTopoConstante(envelope_bruto)
        )
        assert artefato is not None

        dados = json.loads(artefato)
        assert dados["confirmacao"]["validade"] == "2025-02-01"
        dados["confirmacao"]["assinatura_engenheiro"] = True
        envelope_confirmado = desserializar_confirmacao(json.dumps(dados))

        resultado, _ = processar_arquivo_pgr(
            Path("qualquer.pdf"),
            _PROTO,
            MockTranscritorConstante(_GHE_VALIDO),
            _CLIENTE_CARD_NUNCA_CHAMADO,
            envelope=envelope_confirmado,
            hoje=date(2026, 7, 8),
        )

    assert resultado is not None
    assert not any(p.regra_origem == "R-PGR-06" for p in resultado.pendencias_globais)


# ---------------------------------------------------------------------------
# preparar_ghes — rota card plugada (D-ARQ-57 peça 4 fatia 4d, FECHA
# DT-003CS-01). e2e com PDFs reais trackeados, falha explícita, sem skip
# (precedente 003.DA/DI: PDF ausente é falha, não skip).
# ---------------------------------------------------------------------------


def test_preparar_ghes_ufgd_real_105_invocacoes_card_titulo_e_gate_aprova() -> None:
    cliente_ghe = MockTranscritorConstante(_GHE_VALIDO)
    cliente_card = MockTranscritorCardConstante(_GHE_VALIDO)
    aprovados, pendencias = preparar_ghes(_PDF_EBSERH_UFGD_V7, cliente_ghe, cliente_card)

    assert cliente_ghe.blocos_recebidos == []
    assert len(cliente_card.pares_recebidos) == 105
    assert cliente_card.pares_recebidos[0][1] == "13.1 Advogado"
    assert pendencias == ()
    assert len(aprovados) == 105


def test_preparar_ghes_humap_real_gated_por_densidade_nenhum_cliente_invocado() -> None:
    # Witness de gate (correção do Arquiteto/Diovanni pós-medição): a última
    # das 140 âncoras card do HUMAP fica na pág. 186/368 — a cauda depois
    # dela é bloco de assinatura do documento, não outro card, e infla o
    # span do "último card" a 183/368 págs. (49,7% > 40,0%) — mesma classe
    # 003.DD-2 (Ricco-Adm), 2ª testemunha, lado card. segmentacao_
    # implausivel bloqueia ANTES de qualquer cliente ser invocado — nem o
    # GHE nem o card são chamados. O pareamento real 140/140 (titulos todos
    # "") já está coberto em test_transcritor_card.py (4c-ii) e no PASSO 0
    # desta sessão; não duplicado aqui.
    cliente_ghe = MockTranscritorConstante(_GHE_VALIDO)
    cliente_card = MockTranscritorCardConstante(_GHE_VALIDO)
    aprovados, pendencias = preparar_ghes(_PDF_EBSERH_HUMAP, cliente_ghe, cliente_card)

    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "segmentacao_implausivel"
    assert pendencias[0].bloqueante is True
    assert cliente_ghe.blocos_recebidos == []
    assert cliente_card.pares_recebidos == []


def test_preparar_ghes_cjr_real_gated_por_contagem_nenhum_cliente_invocado() -> None:
    # Cjr (18 págs.) tem âncora de RECORTE card (CARGO-CBO), migra para a
    # rota card (flip 1-por-1 espelhado em test_extracao_pgr.py), mas 1
    # único card em doc >10 págs. dispara o gate de contagem —
    # segmentacao_implausivel bloqueia ANTES de qualquer cliente ser
    # invocado (mesma classe GATED-by-design do V2/003.DC).
    cliente_ghe = MockTranscritorConstante(_GHE_VALIDO)
    cliente_card = MockTranscritorCardConstante(_GHE_VALIDO)
    aprovados, pendencias = preparar_ghes(_PDF_CJR, cliente_ghe, cliente_card)

    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "segmentacao_implausivel"
    assert cliente_ghe.blocos_recebidos == []
    assert cliente_card.pares_recebidos == []


def test_preparar_ghes_rota_card_transcricao_indisponivel_vira_pendencia_bloqueante() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_card()):
        aprovados, pendencias = preparar_ghes(
            Path("qualquer.pdf"),
            MockTranscritorConstante(_GHE_VALIDO),
            MockTranscritorCardIndisponivel("CHAVE_API_GOOGLE ausente"),
        )

    assert aprovados == ()
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "transcricao_indisponivel_pgr"
    assert pendencias[0].bloqueante is True
    assert pendencias[0].regra_origem == "D-ARQ-57"
    assert "CHAVE_API_GOOGLE ausente" in pendencias[0].motivo


# ---------------------------------------------------------------------------
# preparar_ghes — rota "ghe", roteamento determinístico-primeiro (D-ARQ-65
# fatia 2): parsear_arquivo tentado ANTES do cliente LLM; aceito só sob as
# duas condições (sem FamiliaNaoReconhecida E contagem == blocos), senão
# fallback LLM inalterado + Pendencia não-bloqueante "familia_nao_medida".
# ---------------------------------------------------------------------------


def test_preparar_ghes_rota_deterministica_aceita_sem_invocar_cliente_llm() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, return_value=(_GHE_VALIDO,)
    ):
        aprovados, pendencias = preparar_ghes(
            Path("qualquer.pdf"), MockTranscritorGHENuncaChamado(), _CLIENTE_CARD_NUNCA_CHAMADO
        )

    assert aprovados == (_GHE_VALIDO,)
    assert pendencias == ()


def test_preparar_ghes_rota_deterministica_recusada_por_excecao_aciona_fallback_llm() -> None:
    mock = MockTranscritorConstante(_GHE_VALIDO)
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        aprovados, pendencias = preparar_ghes(Path("qualquer.pdf"), mock, _CLIENTE_CARD_NUNCA_CHAMADO)

    assert len(mock.blocos_recebidos) == 1
    assert aprovados == (_GHE_VALIDO,)
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "familia_nao_medida"
    assert pendencias[0].bloqueante is False
    assert pendencias[0].regra_origem == "D-ARQ-65"
    assert "família não medida (teste)" in pendencias[0].motivo


def test_preparar_ghes_rota_deterministica_recusada_e_llm_indisponivel_ambas_pendencias() -> None:
    with patch(_ALVO_EXTRACAO, return_value=_paginas_com_bloco()), patch(
        _ALVO_PARSER_DETERMINISTICO, side_effect=FamiliaNaoReconhecida("família não medida (teste)")
    ):
        aprovados, pendencias = preparar_ghes(
            Path("qualquer.pdf"),
            MockTranscritorIndisponivel("CHAVE_API_GOOGLE ausente"),
            _CLIENTE_CARD_NUNCA_CHAMADO,
        )

    assert aprovados == ()
    assert len(pendencias) == 2
    pendencia_bloqueante = next(p for p in pendencias if p.bloqueante)
    assert pendencia_bloqueante.tipo == "transcricao_indisponivel_pgr"
    assert "CHAVE_API_GOOGLE ausente" in pendencia_bloqueante.motivo
    pendencia_familia = next(p for p in pendencias if p.tipo == "familia_nao_medida")
    assert pendencia_familia.bloqueante is False


def test_preparar_ghes_rota_deterministica_recusada_por_contagem_divergente() -> None:
    paginas = ["GHE 1 - Setor Bom\nCargo A\nGHE 2 - Setor Ruim\nCargo B"]
    mock = MockTranscritorSequencial((_GHE_VALIDO, _GHE_VALIDO))
    with patch(_ALVO_EXTRACAO, return_value=paginas), patch(
        _ALVO_PARSER_DETERMINISTICO, return_value=(_GHE_VALIDO,)
    ):
        aprovados, pendencias = preparar_ghes(Path("qualquer.pdf"), mock, _CLIENTE_CARD_NUNCA_CHAMADO)

    assert len(mock.blocos_recebidos) == 2
    assert len(aprovados) == 2
    assert len(pendencias) == 1
    assert pendencias[0].tipo == "familia_nao_medida"
    assert pendencias[0].bloqueante is False
    assert "1 blocos" in pendencias[0].motivo
    assert "2 blocos" in pendencias[0].motivo


# ---------------------------------------------------------------------------
# Integração (marcador requer_pdfs) — PDFs reais Fascino (família medida,
# D-ARQ-65) e Viverde (família NÃO medida — testemunha negativa).
# ---------------------------------------------------------------------------


@requer_pdfs
def test_preparar_ghes_fascino_real_rota_deterministica_aceita_zero_invocacao_llm() -> None:
    aprovados, pendencias = preparar_ghes(
        _PDF_FASCINO, MockTranscritorGHENuncaChamado(), _CLIENTE_CARD_NUNCA_CHAMADO
    )

    assert len(aprovados) == 19
    assert pendencias == ()


@requer_pdfs
def test_preparar_ghes_viverde_real_familia_nao_reconhecida_aciona_fallback_llm() -> None:
    mock = MockTranscritorConstante(_GHE_VALIDO)
    aprovados, pendencias = preparar_ghes(_PDF_VIVERDE, mock, _CLIENTE_CARD_NUNCA_CHAMADO)

    assert len(mock.blocos_recebidos) > 0
    assert aprovados == tuple(_GHE_VALIDO for _ in mock.blocos_recebidos)
    tipos_pendencia = [p.tipo for p in pendencias]
    assert "familia_nao_medida" in tipos_pendencia
    pendencia_familia = next(p for p in pendencias if p.tipo == "familia_nao_medida")
    assert pendencia_familia.bloqueante is False
    assert pendencia_familia.regra_origem == "D-ARQ-65"
