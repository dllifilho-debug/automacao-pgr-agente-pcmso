"""Testes de scripts/medir_audiometria_dem.py (003.EX fatia 0) — parsear_momentos
sobre células de gabarito isoladas à linha de Audiometria."""

from __future__ import annotations

from agente_medico.motor.tipos import Momento
from agente_medico.superficie.documento_matriz import _ROTULO_MOMENTO
from scripts.medir_audiometria_dem import (
    RegistroCargo,
    classificar_dem,
    parsear_momentos,
    rotulos_nao_reconhecidos,
)


def test_parsear_momentos_le_os_quatro() -> None:
    # Reversão que mata: fazer parsear_momentos retornar só o primeiro rótulo casado.
    resultado = parsear_momentos("Audiometria (ADM, PER, MRO, DEM)")
    assert resultado == {Momento.ADM, Momento.PER, Momento.MR, Momento.DEM}


def test_parsear_momentos_sem_dem_nao_inventa_dem() -> None:
    # Reversão que mata: devolver set(Momento) sempre que casar qualquer rótulo.
    resultado = parsear_momentos("Audiometria (ADM, PER, MRO)")
    assert Momento.DEM not in resultado
    assert resultado == {Momento.ADM, Momento.PER, Momento.MR}


def test_rotulo_desconhecido_nao_vira_momento_e_e_reportado() -> None:
    # Reversão que mata: engolir o desconhecido em silêncio (continue sem registrar) —
    # aplicada a rotulos_nao_reconhecidos, que passaria a sempre devolver frozenset() vazio.
    celula = "Audiometria (ADM, XPTO)"
    assert parsear_momentos(celula) == {Momento.ADM}
    assert rotulos_nao_reconhecidos(celula) == {"XPTO"}


def test_parsear_momentos_cobre_todo_par_da_inversao_computado_do_dado() -> None:
    # Reversão que mata: trocar _ROTULO_PARA_MOMENTO (a inversão importada de
    # _ROTULO_MOMENTO) por um dict literal redigitado no script, omitindo RET.
    for momento, rotulo in _ROTULO_MOMENTO.items():
        assert parsear_momentos(f"Audiometria ({rotulo})") == {momento}


def test_classificar_dem_separa_indeterminado_de_sem_dem_confirmado() -> None:
    # Reversão que mata: fazer a agregação somar célula com rótulo não
    # reconhecido em sem_dem (indeterminado sempre vazio) — dobra a recusa
    # do parser em adivinhar numa negação silenciosa na agregação.
    limpo = RegistroCargo(
        ghe="GHE-X",
        cargo="Cargo Limpo",
        tem_audiometria=True,
        momentos_audiometria=frozenset({Momento.ADM, Momento.PER, Momento.MR}),
        rotulos_nao_reconhecidos=frozenset(),
    )
    ambiguo = RegistroCargo(
        ghe="GHE-Y",
        cargo="Cargo Ambíguo",
        tem_audiometria=True,
        momentos_audiometria=frozenset({Momento.ADM, Momento.PER, Momento.MR}),
        rotulos_nao_reconhecidos=frozenset({"DEM 12 meses"}),
    )
    com_dem, indeterminado, sem_dem = classificar_dem([limpo, ambiguo])
    assert com_dem == []
    assert indeterminado == [ambiguo]
    assert sem_dem == [limpo]
