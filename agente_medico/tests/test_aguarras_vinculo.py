"""DT-(sessão claude/keen-curie-xdm7kb)-01: a FISPQ da aguarrás (CAS 64742-82-1) sugere o
GHE 18 PINTURA do Aurora, que declara "Aguarrás" e "Destilados de Petróleo levemente
tratados com hidrogênio" — critério de aceite da D-ARQ-90 fatia 1. Cada teste nomeia a
reversão que o deixa vermelho."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest

from agente_medico.motor.hidratacao import hidratar_pgr
from agente_medico.motor.protocolo import Protocolo, carregar
from agente_medico.motor.resolvedor import construir_indice_cas
from agente_medico.motor.resolvedor_termos import construir_indice_termos
from agente_medico.motor.tipos import BlocoVerbatim, GHEVerbatim, MembroVerbatim, RiscoVerbatim
from agente_medico.superficie.sugestao_vinculo import sugerir_ghes

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

# Seção 3 da FISPQ fispq-quim-sol-alif-aguarras-mineral.pdf, como declarada.
_FISPQ_AGUARRAS = (
    BlocoVerbatim("0 - 100", (MembroVerbatim("64742-82-1", "Nafta hidrodessulfurizada pesada"),)),
    BlocoVerbatim("0 - 100", (MembroVerbatim("8008-20-6", "Querosene"),)),
    BlocoVerbatim("<0,1", (MembroVerbatim("71-43-2", "Benzeno"),)),
)


@pytest.fixture(scope="module")
def proto() -> Protocolo:
    return carregar(_PROTOCOLO_DIR)


def test_fispq_da_aguarras_sugere_o_ghe_da_pintura(proto: Protocolo) -> None:
    # Reversões que matam: (1) tirar "Aguarrás" dos termos de aguarras_mineral — o
    # GHE não declara o agente; (2) tirar "64742-82-1" de cas_adicionais, ou
    # (3) construir_indice_cas ignorar cas_adicionais — a FDS não tem o agente;
    # (4) tirar o CAS 8008-20-6 do slug `querosene` (03/10/2026) — o querosene da FISPQ
    # volta a sair sem agente e o GHE perde o vínculo pelo querosene.
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    pgr, _ = hidratar_pgr(
        [
            GHEVerbatim(
                nome="GHE 18 - PINTURA",
                cargos=("Pintor",),
                riscos=(
                    RiscoVerbatim(agente="Aguarrás", quantificacao="", fonte_geradora="Atividade com pinturas"),
                    RiscoVerbatim(agente="Querosene (petróleo)", quantificacao="", fonte_geradora="Atividade com pintura"),
                ),
            ),
            GHEVerbatim(
                nome="GHE 01 - ADMINISTRAÇÃO",
                cargos=("Administrativo",),
                riscos=(RiscoVerbatim(agente="Ruído", quantificacao="", fonte_geradora="Escritório"),),
            ),
        ],
        indice,
        date(2030, 1, 1),
        True,
    )

    sugestao = sugerir_ghes(_FISPQ_AGUARRAS, pgr, proto.vocabulario.agentes)

    assert [(g.ghe_nome, [a.slug for a in g.agentes]) for g in sugestao.ghes] == [
        ("GHE 18 - PINTURA", ["aguarras_mineral", "querosene"])
    ]
    assert sugestao.componentes_sem_slug == ()


def test_nome_quimico_do_cas_resolve_para_destilados_hidrotratados(proto: Protocolo) -> None:
    # "Destilados de petróleo levemente tratados com hidrogênio" é o nome do CAS
    # 64742-47-8. Desde 03/10/2026 (opção b ajustada) o termo do PGR vai para
    # `destilados_petroleo_hidrotratados`, sem benzeno a confirmar; o CAS segue na
    # aguarrás. Reversão que mata: devolver o termo a aguarras_mineral.
    indice = construir_indice_termos(
        proto.vocabulario.agentes, fracoes_sem_agente=proto.vocabulario.fracoes_sem_agente
    )
    pgr, _ = hidratar_pgr(
        [
            GHEVerbatim(
                nome="GHE 18 - PINTURA",
                cargos=("Pintor",),
                riscos=(
                    RiscoVerbatim(
                        agente="Destilados de Petróleo levemente tratados com hidrogênio",
                        quantificacao="",
                        fonte_geradora="Atividade com pintura",
                    ),
                ),
            )
        ],
        indice,
        date(2030, 1, 1),
        True,
    )
    assert pgr.ghes[0].riscos[0].agente == "destilados_petroleo_hidrotratados"


def test_cas_adicional_que_colide_com_outro_agente_e_erro() -> None:
    # Integridade do vocabulário: o mesmo CAS não aponta para dois agentes, venha
    # de `cas` ou de `cas_adicionais`. Reversão que mata: indexar cas_adicionais
    # sem a checagem de colisão.
    vocab = {
        "a": {"cas": "64742-82-1"},
        "b": {"cas": "50-00-0", "cas_adicionais": ["64742-82-1"]},
    }
    with pytest.raises(ValueError, match="Colisão de CAS"):
        construir_indice_cas(vocab)
