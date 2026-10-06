from __future__ import annotations

from collections.abc import Sequence

import pytest

from agente_medico.motor.parser_familia_grid_aiha import GrupoFuncaoAIHA, PalavraPDF, _Linha
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim
from agente_medico.motor.transcritor_grid import EntradaGrid, transcrever_grupos_grid


def _linha(texto: str, top: float) -> _Linha:
    return _Linha(tuple(PalavraPDF(text=p, x0=100.0 + 10 * i, top=top) for i, p in enumerate(texto.split())))


def _grupo(nome: str, *linhas: str) -> GrupoFuncaoAIHA:
    return GrupoFuncaoAIHA(nome=nome, linhas=tuple(_linha(t, 100.0 + 10 * i) for i, t in enumerate(linhas)))


class _ClienteEco:
    """Devolve um GHE por entrada, com o nome verbatim e um risco cuja
    avaliacao_qualitativa vem preenchida — registra o que recebeu."""

    def __init__(self, faltar: int = 0) -> None:
        self.recebido: list[EntradaGrid] = []
        self.chamadas = 0
        self._faltar = faltar

    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]:
        self.chamadas += 1
        self.recebido.extend(entradas)
        saida = tuple(
            GHEVerbatim(
                nome=e.nome_verbatim,
                cargos=(e.nome_verbatim,),
                riscos=(RiscoVerbatim("RUÍDO", "", "", avaliacao_qualitativa="1 - IRRELEVANTE"),),
            )
            for e in entradas
        )
        return saida[: len(saida) - self._faltar]


def test_cliente_recebe_nome_verbatim_e_texto_das_linhas_na_ordem() -> None:
    # Reversão que mata: entrada_do_grupo montar o texto sem o nome
    # verbatim (nome_verbatim="") ou com as linhas fora de ordem.
    cliente = _ClienteEco()
    transcrever_grupos_grid(
        [_grupo("CARPINTEIR O", "RUÍDO CONTÍNUO", "—"), _grupo("PINTOR", "UMIDADE")], cliente
    )
    assert cliente.recebido == [
        EntradaGrid("CARPINTEIR O", "RUÍDO CONTÍNUO\n—"),
        EntradaGrid("PINTOR", "UMIDADE"),
    ]


def test_saida_mais_curta_que_a_entrada_levanta_value_error() -> None:
    # Reversão que mata: tirar a checagem de comprimento — a tupla curta
    # passaria e desalinharia grupo e GHE a jusante.
    with pytest.raises(ValueError, match="alinhamento"):
        transcrever_grupos_grid([_grupo("A", "x"), _grupo("B", "y")], _ClienteEco(faltar=1))


def test_avaliacao_qualitativa_sai_vazia_mesmo_com_irrelevante_no_grid() -> None:
    # "1 - IRRELEVANTE" é da coluna Classificação do grid AIHA, não da
    # matriz P×S. Reversão que mata: devolver o resultado do cliente sem
    # _avaliacao_aiha.
    (ghe,) = transcrever_grupos_grid([_grupo("PINTOR", "UMIDADE 1 - IRRELEVANTE")], _ClienteEco())
    assert [r.avaliacao_qualitativa for r in ghe.riscos] == [""]
    assert [r.agente for r in ghe.riscos] == ["RUÍDO"]


def test_sem_grupos_nao_invoca_o_cliente() -> None:
    # Reversão que mata: tirar o retorno antecipado — o cliente seria
    # chamado com lista vazia (uma requisição gasta à toa no nível gratuito).
    cliente = _ClienteEco()
    assert transcrever_grupos_grid([], cliente) == ()
    assert cliente.chamadas == 0

