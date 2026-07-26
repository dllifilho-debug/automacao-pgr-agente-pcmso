from __future__ import annotations

from dataclasses import dataclass

from agente_medico.motor.predicados import PRIMITIVOS_INCONDICIONAIS
from agente_medico.motor.tipos import ExameEmitido, Resultado


def linhas_de_risco(exames: list[ExameEmitido]) -> list[ExameEmitido]:
    """Exclui linhas de regra incondicional (R-CLI-01, piso universal, 003.EC) —
    isola o que a exposição/risco sob teste efetivamente contribuiu para a matriz.

    Uma linha é de origem incondicional quando TODOS os seus Motivo.predicado
    pertencem a PRIMITIVOS_INCONDICIONAIS (ex.: 'todo_trabalhador'). Helper
    compartilhado — não duplicar por arquivo de teste."""
    return [
        e for e in exames
        if any(m.predicado not in PRIMITIVOS_INCONDICIONAIS for m in e.motivos)
    ]


@dataclass(frozen=True)
class ViolacaoPisoSemTeto:
    """D-ARQ-31 cláusula 3: uma linha emitida carrega piso sem o teto pendente visível.

    Campos só imutáveis (str/Optional[str]) — ExameEmitido é mutável (list de
    pendencias_anexadas), não serve como campo de dataclass frozen com == estável.
    A linha violada identifica-se pelo par (ghe_id, exame).
    """
    ghe_id: str
    exame: str
    regra_origem: str | None
    motivo: str


def auditar_invariante_piso_teto(resultado: Resultado) -> list[ViolacaoPisoSemTeto]:
    """Afirma a invariante D-ARQ-31 cláusula 3 sobre o Resultado inteiro.

    Violação = Pendencia bloqueante COM âncora (exames_alvo) que ficou SOLTA no nível
    da MatrizGHE, embora uma linha emitida desse mesmo GHE case essa âncora. Significa
    que a anexação não rodou (ou regrediu): o piso (linha) está sem o teto (pendência)
    ao lado. Por construção (anexar_pendencias) isto NUNCA ocorre sobre saída real do
    orquestrador — o auditor é a rede contra regressão futura na anexação.

    Retorna lista de violações (vazia = invariante mantida). Estruturado, nunca bool:
    quando dispara, diz qual GHE e qual exame achatou.
    """
    violacoes: list[ViolacaoPisoSemTeto] = []
    for m in resultado.matrizes:
        emitidos = {ln.exame for ln in m.linhas}
        for p in m.pendencias:
            if not p.bloqueante or not p.exames_alvo:
                continue
            casantes = set(p.exames_alvo) & emitidos
            for exame in sorted(casantes):
                violacoes.append(
                    ViolacaoPisoSemTeto(
                        ghe_id=m.ghe_id,
                        exame=exame,
                        regra_origem=p.regra_origem,
                        motivo=p.motivo,
                    )
                )
    return violacoes
