"""Camada visual (estilos.py + keys de container em web_matriz.py) — só trava o
que, quebrado, some sem erro na tela."""

from __future__ import annotations

import re
from datetime import date, timedelta
from pathlib import Path
from typing import Any

import pytest
import streamlit
from streamlit.testing.v1 import AppTest

from agente_medico.motor.tipos import ExameEmitido, MatrizGHE, Momento, Resultado
from agente_medico.superficie import estilos
from agente_medico.superficie.web_matriz import pagina_matriz
from agente_medico.tests.test_web_matriz import _mockar_parse_deterministico, _submeter_formulario

_RAIZ = Path(__file__).resolve().parents[2]


def test_css_nao_tem_texto_com_cara_de_tag() -> None:
    # Reversão que mata: voltar o comentário do stepper para
    # `passo_<n>_<estado>` — o DOMPurify do frontend descarta o <style>
    # inteiro quando o texto contém `<letra` (medido: página sem nenhum estilo).
    css = estilos._css()
    corpo = css.split("<style>", 1)[1].rsplit("</style>", 1)[0]
    assert not re.search(r"<[/\w]", corpo)


def test_estilos_so_referenciam_keys_existentes() -> None:
    # Reversão que mata: renomear `key="etapa_pgr"` (ou o prefixo `passo_`) em
    # web_matriz.py — o seletor `.st-key-...` deixa de casar e o card perde o
    # estilo sem nenhum erro.
    fonte = (_RAIZ / "agente_medico" / "superficie" / "web_matriz.py").read_text(encoding="utf-8")
    referenciadas = set(re.findall(r"st-key-([a-z0-9_]+)", estilos._css()))
    assert referenciadas
    # Seletor terminado em `_` é prefixo (`passo_` → `key=f"passo_1_..."`); o resto é key exata.
    ausentes = [
        k for k in referenciadas
        if not re.search(r'key=f?"' + re.escape(k) + ("" if k.endswith("_") else '"'), fonte)
    ]
    assert not ausentes, ausentes


@pytest.mark.parametrize("entrypoint", ["app_matriz.py", "app_matriz_local.py"])
def test_entrypoints_aplicam_estilos(monkeypatch: pytest.MonkeyPatch, entrypoint: str) -> None:
    # Reversão que mata: remover a chamada `aplicar_estilos()` do entrypoint.
    chamadas: list[None] = []
    monkeypatch.setattr(estilos, "aplicar_estilos", lambda: chamadas.append(None))
    monkeypatch.delenv("PCMSO_ALLOWLIST", raising=False)
    monkeypatch.setattr(streamlit, "user", {})
    at = AppTest.from_file(str(_RAIZ / entrypoint), default_timeout=30)
    at.run()

    assert not at.exception, f"exceções: {at.exception}"
    assert chamadas


def test_css_nao_carrega_nada_de_terceiros() -> None:
    # Reversão que mata: pôr um `@import url('https://fonts.googleapis.com/...')`
    # no CSS — reabre a requisição a terceiro que o fontFaces local eliminou.
    # `xmlns='http://www.w3.org/2000/svg'` dos ícones é namespace, não requisição.
    css_sem_namespace = re.sub(r"xmlns='[^']*'", "", estilos._css())
    assert "://" not in css_sem_namespace


# Nomes que o frontend monta por template (`stAlertContent${tipo}`,
# `stBaseButton-${kind}`): no bundle só aparece o prefixo seguido de `${`.
_PREFIXOS_TEMPLATE = ("stAlertContent", "stBaseButton-")


def test_data_testids_do_css_existem_no_streamlit_instalado() -> None:
    # Reversão que mata: trocar no CSS `stFileUploaderDropzone` por um nome que
    # o frontend não emite (ex.: `stFileDropzone`) — o seletor deixa de casar
    # e a dropzone perde o estilo sem erro. Pega renomeação de testid num
    # upgrade do Streamlit; mudança de ESTRUTURA do DOM (seletores FRÁGIL) não.
    pasta_js = Path(streamlit.__file__).parent / "static" / "static" / "js"
    bundle = "".join(js.read_text(encoding="utf-8", errors="ignore") for js in pasta_js.glob("*.js"))
    usados = set(re.findall(r'data-testid\^?="(st[A-Za-z-]+)"', estilos._css()))
    assert usados

    def _existe(testid: str) -> bool:
        prefixo = next((p for p in _PREFIXOS_TEMPLATE if testid.startswith(p)), None)
        if prefixo is not None:
            return f"{prefixo}${{" in bundle
        return any(f"{q}{testid}{q}" in bundle for q in '`"\'')

    ausentes = sorted(t for t in usados if not _existe(t))
    assert not ausentes, f"data-testid ausentes no Streamlit {streamlit.__version__}: {ausentes}"
    assert "st-key-" in bundle


def _passos(at: AppTest) -> dict[str, str]:
    """Key do container `passo_*` → texto do markdown dentro dele."""
    achados: dict[str, str] = {}

    def _andar(no: Any, key: str | None) -> None:
        for filho in getattr(no, "children", {}).values():
            proto_id = getattr(getattr(filho, "proto", None), "id", "")
            chave = proto_id.rsplit("-", 1)[-1] if isinstance(proto_id, str) and "-passo_" in proto_id else key
            if type(filho).__name__ == "Markdown" and chave is not None:
                achados[chave] = filho.value
            _andar(filho, chave)

    _andar(at._tree, None)
    return achados


def test_cor_do_passo_acompanha_o_icone_sem_pgr() -> None:
    # Reversão que mata: trocar `key=f"passo_1_{estado_1}"` por uma key fixa
    # (ex.: "passo_1_concluido") — a cor diria concluído com o ícone ⬜.
    at = AppTest.from_function(pagina_matriz)
    at.run()

    assert not at.exception
    assert _passos(at) == {
        "passo_1_ativo": "⬜ **1. PGR e identificação**",
        "passo_2_opcional": "➖ **2. FDS/FISPQ e medições** (opcional)",
        "passo_3_pendente": "⬜ **3. Conferência**",
        "passo_4_pendente": "⬜ **4. Matriz e downloads**",
    }


def test_cor_do_passo_acompanha_o_icone_com_bloqueio() -> None:
    # Reversão que mata: calcular `estado_1` sem o ramo `bloqueado` — o passo 1
    # ficaria com a cor de "ativo" enquanto a etapa está bloqueada.
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at, validade=(date.today() + timedelta(days=200)).isoformat())

    assert not at.exception
    assert _passos(at)["passo_1_bloqueado"] == "⛔ **1. PGR e identificação**"


def test_cor_do_passo_acompanha_o_icone_com_matriz(monkeypatch: pytest.MonkeyPatch) -> None:
    # Reversão que mata: fixar `estado_seguinte = "pendente"` — os passos 3 e 4
    # mostrariam ✅ com a cor de pendente.
    exame = ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={Momento.ADM})
    matriz = MatrizGHE(ghe_id="GHE-01", linhas=[exame], cargos=("Cargo Teste",))
    _mockar_parse_deterministico(monkeypatch, Resultado(status="OK", matrizes=[matriz]))
    at = AppTest.from_function(pagina_matriz)
    at.run()
    _submeter_formulario(at)

    assert not at.exception
    passos = _passos(at)
    assert passos["passo_1_concluido"] == "✅ **1. PGR e identificação**"
    assert passos["passo_3_concluido"] == "✅ **3. Conferência**"
    assert passos["passo_4_concluido"] == "✅ **4. Matriz e downloads**"
