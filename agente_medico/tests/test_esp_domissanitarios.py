"""R-ESP-05 (NR-07 Anexo III item 3.2; decisão do Diovanni, 08/10/2026, opção B): produtos
domissanitários no PGR não pedem espirometria de rotina — a matriz leva a condição da norma
em observação, que sai quando outra regra já pede o exame. Cada teste nomeia a reversão que o
deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.entrada import processar_pgr
from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor_termos import construir_indice_termos, resolver_termo
from agente_medico.motor.tipos import GHEVerbatim, MatrizGHE, RiscoVerbatim
from agente_medico.superficie.documento_matriz import CabecalhoDocumento, RodapeDocumento, montar_documento
from agente_medico.superficie.memorial_matriz import montar_memorial

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"
_CONDICAO = "espirometria somente se houver sinais ou sintomas respiratórios (NR-07 Anexo III item 3.2)"


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def _matriz(proto: Protocolo, termos: tuple[str, ...]) -> MatrizGHE:
    indice = construir_indice_termos(proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente)
    ghe = GHEVerbatim(
        nome="GHE 07 - SERVIÇOS GERAIS",
        cargos=("Auxiliar de Serviços Gerais",),
        riscos=tuple(
            RiscoVerbatim(agente=t, quantificacao="", fonte_geradora="", avaliacao_qualitativa="2 1 BAIXO (2)")
            for t in termos
        ),
    )
    pgr, _ = hidratar_pgr([ghe], indice, date(2026, 8, 25), True, psicossocial=True)
    (matriz,) = processar_pgr(pgr, proto, hoje=date(2026, 10, 8)).matrizes
    return matriz


def test_domissanitario_sem_poeira_nao_pede_espirometria_e_leva_a_condicao(proto: Protocolo) -> None:
    # Vila Brasil escritório GHE 07. Reversões que matam: (1) tirar o ramo `mencao_condicional`
    # de emitir_exames (a espirometria sairia de rotina); (2) tirar R-ESP-05 de regras.yaml (a
    # observação some); (3) devolver à observação o texto de R-BIO-05 em _formatar_observacao.
    matriz = _matriz(proto, ("Produtos DomissanItários", "Postura inadequada"))

    assert "espirometria" not in {ln.exame for ln in matriz.linhas}
    (obs,) = matriz.observacoes
    assert obs.regra_id == "R-ESP-05" and obs.condicao is not None and _CONDICAO in obs.condicao
    documento = montar_documento([matriz], proto.vocabulario.exames, CabecalhoDocumento("", "", "", "", "", ""), RodapeDocumento("", "", ""))
    celulas = [c for bloco in documento.blocos for linha in bloco.linhas for c in linha.celulas]
    assert any(c.startswith("Obs.: produtos domissanitários no PGR") and _CONDICAO in c for c in celulas)


def test_com_silica_a_espirometria_sai_por_r_esp_02_e_a_condicao_some(proto: Protocolo) -> None:
    # Fascino e Porto Araras GHE-05. Reversão que mata: tirar o filtro do orquestrador — a
    # matriz pediria a espirometria e diria, na mesma célula, que ela só vale com sintomas.
    matriz = _matriz(proto, ("Produtos DomissanItários", "Sílica livre"))

    assert "espirometria" in {ln.exame for ln in matriz.linhas}
    assert matriz.observacoes == ()


def test_memorial_explica_o_nao_pedido_pela_norma(proto: Protocolo) -> None:
    # Reversão que mata: tirar o ramo `condicao` de _nao_pedido — o memorial diria "risco  no
    # PGR" (sem nível) e citaria o item 7.5.12 "b", que é da R-BIO-05.
    matriz = _matriz(proto, ("Produtos DomissanItários",))
    (bloco,) = montar_memorial([matriz], proto.vocabulario.exames, {}).blocos
    (texto,) = bloco.nao_pedidos
    assert texto.startswith("Espirometria: não pedido de rotina") and "3.2" in texto and "7.5.12" not in texto


@pytest.mark.parametrize("termo", ["Produtos DomissanItários", "Produtos Domissantários", "Produtos Saneantes e Domissanitários"])
def test_grafias_do_acervo_resolvem(proto: Protocolo, termo: str) -> None:
    # Grafias medidas no censo de 08/10/2026. Reversão que mata: tirar o termo de agentes.yaml.
    indice = construir_indice_termos(proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente)
    assert resolver_termo(termo, indice).slug == "domissanitarios"
