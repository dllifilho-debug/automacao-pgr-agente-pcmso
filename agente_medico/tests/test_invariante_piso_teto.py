from __future__ import annotations

from agente_medico.motor.tipos import (
    ExameEmitido,
    MatrizGHE,
    Pendencia,
    Resultado,
)
from agente_medico.tests.invariantes import (
    ViolacaoPisoSemTeto,
    auditar_invariante_piso_teto,
)


def _resultado(matrizes: list[MatrizGHE]) -> Resultado:
    return Resultado(status="PRELIMINAR", matrizes=matrizes)


def test_violacao_fabricada_e_detectada() -> None:
    # Estado que o pipeline real NUNCA produz (a anexação impede): bloqueante com
    # âncora 'rx_torax_oit' SOLTA na matriz, embora a linha rx_torax_oit exista.
    # Sem este caso sintético o auditor jamais é exercitado no vermelho.
    linha = ExameEmitido(exame="rx_torax_oit", periodicidade_meses=60)
    pend = Pendencia(
        tipo="exame_ausente",
        destinatario="higienista",
        motivo="sílica sem fração",
        bloqueante=True,
        regra_origem="R-RX-01-baixa",
        exames_alvo=("rx_torax_oit",),
    )
    m = MatrizGHE(ghe_id="X-01", linhas=[linha], pendencias=[pend], status="PARCIAL")
    violacoes = auditar_invariante_piso_teto(_resultado([m]))
    assert violacoes == [
        ViolacaoPisoSemTeto(
            ghe_id="X-01",
            exame="rx_torax_oit",
            regra_origem="R-RX-01-baixa",
            motivo="sílica sem fração",
        )
    ]


def test_pendencia_corretamente_anexada_nao_viola() -> None:
    # Estado correto pós-fatia-3: a bloqueante está NA linha (pendencias_anexadas),
    # não solta na matriz. Sem pendência solta → sem violação.
    linha = ExameEmitido(exame="rx_torax_oit", periodicidade_meses=60)
    linha.pendencias_anexadas.append(
        Pendencia(
            tipo="exame_ausente",
            destinatario="higienista",
            motivo="sílica sem fração",
            bloqueante=True,
            regra_origem="R-RX-01-baixa",
            exames_alvo=("rx_torax_oit",),
        )
    )
    m = MatrizGHE(ghe_id="X-01", linhas=[linha], pendencias=[], status="PARCIAL")
    assert auditar_invariante_piso_teto(_resultado([m])) == []


def test_bloqueada_sem_linha_nao_viola() -> None:
    # BLOQUEADA: bloqueante com âncora solta, mas NENHUMA linha emitida no GHE.
    # Não há piso sem teto — não há piso. Fora do escopo desta invariante.
    pend = Pendencia(
        tipo="exame_ausente",
        destinatario="higienista",
        motivo="único risco bloqueado",
        bloqueante=True,
        regra_origem="R-RX-01-sem",
        exames_alvo=("rx_torax_oit",),
    )
    m = MatrizGHE(ghe_id="X-02", linhas=[], pendencias=[pend], status="BLOQUEADA")
    assert auditar_invariante_piso_teto(_resultado([m])) == []


def test_pendencia_sem_ancora_nao_viola() -> None:
    # Tipo A: bloqueante SEM exames_alvo (não tem onde escalar). Fica solta na matriz
    # legitimamente — não é piso-sem-teto, é pendência de nível de GHE.
    linha = ExameEmitido(exame="audiometria", periodicidade_meses=12)
    pend = Pendencia(
        tipo="vocabulario_ausente",
        destinatario="extracao",
        motivo="agente sem slug",
        bloqueante=True,
        regra_origem=None,
        exames_alvo=(),
    )
    m = MatrizGHE(ghe_id="X-03", linhas=[linha], pendencias=[pend], status="PARCIAL")
    assert auditar_invariante_piso_teto(_resultado([m])) == []
