"""Smoke visual do app da matriz — confere no navegador o que a suíte não vê.

A suíte trava nomes (keys, data-testid, fonte local), mas não a ESTRUTURA do
DOM do Streamlit: um upgrade que reorganize os containers some com o estilo
sem erro nenhum. Este script sobe o app com o parse do PGR mockado, abre num
Chromium (Playwright) e mede o resultado renderizado em 3 cenários × 2 larguras.

Uso:
    python -m playwright install chromium     # uma vez por máquina
    python -m scripts.smoke_visual
    python -m scripts.smoke_visual --chromium /caminho/do/chrome

Quando rodar: antes de cada deploy e sempre que a versão do Streamlit mudar.
Fora da suíte de propósito: precisa de navegador e leva ~1 min.

Código de saída: 0 tudo ok · 1 alguma verificação falhou · 2 infraestrutura
(Playwright ausente, app não subiu, cenário não carregou).

Screenshots e log do servidor vão para `relatorios/smoke_visual/<data-hora>/`
(ignorado pelo git).

Medição (`_medir`, navegador) e avaliação (`avaliar`, função pura) ficam
separadas: a avaliação é testada sem navegador em tests/test_smoke_visual.py.
"""

from __future__ import annotations

import argparse
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, BinaryIO

from agente_medico.superficie import estilos

_RAIZ = Path(__file__).resolve().parent.parent

LARGURAS = {"desktop": 1280, "mobile": 420}
CENARIOS = ("inicial", "bloqueio", "matriz")

# Tolerâncias em px: diferença de arredondamento de subpixel entre navegadores.
TOL_ALTURA = 1.5
TOL_CONTEUDO = 1.5
TOL_CENTRO = 2.5

# Estado do passo do stepper → cor da borda superior (estilos.py, regras passo_*).
COR_DO_ESTADO = {
    "ativo": estilos.PRIMARIA,
    "concluido": estilos.SUCESSO,
    "bloqueado": estilos.ERRO,
    "opcional": estilos.ACENTO,
    "pendente": estilos.BORDA,
}
COR_DO_ALERTA = {
    "stAlertContentSuccess": estilos.SUCESSO,
    "stAlertContentWarning": estilos.ALERTA,
    "stAlertContentError": estilos.ERRO,
    "stAlertContentInfo": estilos.PRIMARIA,
}
CARDS = ("etapa_pgr", "etapa_fds", "caixa_conferencia", "caixa_matriz")

# O que precisa estar na tela para o cenário contar como atingido — sem isto,
# um cenário que não carregou passaria com as checagens vazias.
ESPERADO_NO_CENARIO: dict[str, tuple[str, ...]] = {
    "inicial": ("passo_1_ativo",),
    "bloqueio": ("passo_1_bloqueado",),
    "matriz": ("passo_1_concluido", "passo_3_concluido", "passo_4_concluido"),
}


def rgb(hexa: str) -> str:
    """`#0F4C5C` → `rgb(15, 76, 92)`, o formato de getComputedStyle."""
    h = hexa.lstrip("#")
    return f"rgb({int(h[0:2], 16)}, {int(h[2:4], 16)}, {int(h[4:6], 16)})"


def avaliar(medidas: dict[str, Any], cenario: str) -> list[str]:
    """Falhas encontradas nas medidas de um cenário; lista vazia = ok."""
    falhas: list[str] = []

    if not medidas["css_aplicado"]:
        # Reversão real que cai aqui: `<p>` num comentário do CSS (o DOMPurify
        # descarta o <style> inteiro) ou entrypoint sem aplicar_estilos().
        falhas.append("CSS do app ausente na página (estilos.py não aplicado)")

    if medidas["fonte_status"] != 200:
        falhas.append(f"fonte local respondeu {medidas['fonte_status']} em app/static/fonts")
    if not medidas["inter_carregada"]:
        falhas.append("fonte Inter não carregou")
    if not str(medidas["familia_texto"]).startswith("Inter"):
        falhas.append(f"texto não está em Inter: {medidas['familia_texto']}")
    if medidas["hosts_externos"]:
        falhas.append(f"requisição a terceiros: {sorted(medidas['hosts_externos'])}")

    passos: list[dict[str, Any]] = medidas["passos"]
    chaves = {p["key"] for p in passos}
    for esperado in ESPERADO_NO_CENARIO[cenario]:
        if esperado not in chaves:
            falhas.append(f"cenário '{cenario}' não atingido: falta {esperado} (há {sorted(chaves)})")
    if len(passos) != 4:
        falhas.append(f"stepper com {len(passos)} passos, esperado 4")
    else:
        alturas = [p["base"] - p["topo"] for p in passos]
        if max(alturas) - min(alturas) > TOL_ALTURA:
            falhas.append(f"passos do stepper com alturas diferentes: {[round(a) for a in alturas]}")
    for p in passos:
        if p["texto_topo"] < p["topo"] - TOL_CONTEUDO or p["texto_base"] > p["base"] + TOL_CONTEUDO:
            falhas.append(
                f"{p['key']}: texto vaza da caixa "
                f"(texto {round(p['texto_topo'])}–{round(p['texto_base'])}, "
                f"caixa {round(p['topo'])}–{round(p['base'])})"
            )
        estado = p["key"].rsplit("_", 1)[-1]
        esperado_cor = COR_DO_ESTADO.get(estado)
        if esperado_cor is not None and p["cor_topo"] != rgb(esperado_cor):
            falhas.append(f"{p['key']}: cor {p['cor_topo']}, esperada {rgb(esperado_cor)} ({estado})")

    faixa = medidas["faixa"]
    if faixa is None:
        falhas.append("faixa de cabeçalho (h1) não encontrada")
    else:
        if "gradient" not in faixa["fundo"]:
            falhas.append("faixa de cabeçalho sem o degradê")
        if abs(faixa["folga_topo"] - faixa["folga_base"]) > TOL_CENTRO:
            falhas.append(
                f"título fora do centro da faixa (folga {round(faixa['folga_topo'])}px acima, "
                f"{round(faixa['folga_base'])}px abaixo)"
            )

    for card in medidas["cards"]:
        if card["sombra"] == "none" or card["raio"] < 10:
            falhas.append(f"card {card['key']} sem sombra/canto arredondado")

    for estilo in medidas["dropzones"]:
        if estilo != "dashed":
            falhas.append(f"dropzone com borda '{estilo}', esperada tracejada")

    for d in medidas["downloads"]:
        if d["largura"] < d["coluna"] - TOL_ALTURA:
            falhas.append(f"download '{d['rotulo']}' com {round(d['largura'])}px numa coluna de {round(d['coluna'])}px")
    if cenario == "matriz" and len(medidas["downloads"]) != 3:
        falhas.append(f"{len(medidas['downloads'])} botões de download, esperados 3")

    alturas_botoes = [b["altura"] for b in medidas["botoes"]]
    if alturas_botoes and max(alturas_botoes) - min(alturas_botoes) > TOL_ALTURA:
        falhas.append(
            "botões com alturas diferentes: "
            + ", ".join(f"{b['rotulo']}={round(b['altura'])}" for b in medidas["botoes"])
        )

    for alerta in medidas["alertas"]:
        esperado_cor = COR_DO_ALERTA.get(alerta["tipo"])
        if esperado_cor is not None and alerta["borda"] != rgb(esperado_cor):
            falhas.append(f"alerta {alerta['tipo']}: borda {alerta['borda']}, esperada {rgb(esperado_cor)}")
    if cenario == "bloqueio" and not any(a["tipo"] == "stAlertContentError" for a in medidas["alertas"]):
        falhas.append("cenário 'bloqueio' sem o alerta de erro")

    return falhas


# ---------------------------------------------------------------------------
# Execução (servidor + navegador)
# ---------------------------------------------------------------------------

# Roda o entrypoint de desenvolvimento DE VERDADE (runpy), só com o parse do PGR
# trocado: se o entrypoint perder aplicar_estilos(), o smoke vê.
_APP_MOCK = """
import runpy, sys
from datetime import date
sys.path.insert(0, {raiz!r})
import agente_medico.superficie.web_matriz as wm
from agente_medico.motor.tipos import GHEPGR, PGR, ExameEmitido, MatrizGHE, Momento, Resultado

_ghe = GHEPGR(id="GHE-01", nome="", cargos=("Pedreiro",), riscos=(), epis=(),
              produtos_quimicos=(), psicossocial=False)
_pgr = PGR(validade=date(2030, 1, 1), assinatura_engenheiro=True, ghes=(_ghe,))
_matriz = MatrizGHE(ghe_id="GHE-01", cargos=("Pedreiro",), linhas=[
    ExameEmitido(exame="exame_clinico", periodicidade_meses=12, momentos={{Momento.ADM}})])
wm.preparar_pgr_hidratado = lambda *a, **k: (_pgr, ())
wm.processar_pgr = lambda *a, **k: Resultado(status="OK", matrizes=[_matriz])
runpy.run_path({entrypoint!r}, run_name="__main__")
"""

_JS_MEDIR = """
async () => {
  await document.fonts.ready;
  const r = (e) => e.getBoundingClientRect();
  const cs = (e) => getComputedStyle(e);
  const visivel = (e) => r(e).width > 0 && r(e).height > 0;
  const passos = [...document.querySelectorAll('[class*="st-key-passo_"]')].map((e) => {
    const p = e.querySelector('p');
    const key = [...e.classList].find((c) => c.startsWith('st-key-passo_')).slice('st-key-'.length);
    return {key, topo: r(e).top, base: r(e).bottom, texto_topo: p ? r(p).top : r(e).top,
            texto_base: p ? r(p).bottom : r(e).bottom, cor_topo: cs(e).borderTopColor};
  });
  const h1 = document.querySelector('h1');
  const caixa = h1 ? h1.closest('[data-testid="stElementContainer"]') : null;
  const faixa = caixa ? {fundo: cs(caixa).backgroundImage, folga_topo: r(h1).top - r(caixa).top,
                         folga_base: r(caixa).bottom - r(h1).bottom} : null;
  const cards = ['etapa_pgr', 'etapa_fds', 'caixa_conferencia', 'caixa_matriz']
    .map((k) => [k, document.querySelector('.st-key-' + k)]).filter(([, e]) => e)
    .map(([k, e]) => ({key: k, sombra: cs(e).boxShadow, raio: parseFloat(cs(e).borderTopLeftRadius)}));
  const botoes = [...document.querySelectorAll('[data-testid^="stBaseButton-primary"], [data-testid^="stBaseButton-secondary"]')]
    .filter(visivel).map((b) => ({rotulo: b.innerText.trim(), altura: r(b).height}));
  // Só os visíveis: o Streamlit mantém no DOM cópias ocultas (0 px) de elementos do rerun anterior.
  const downloads = [...document.querySelectorAll('[data-testid="stDownloadButton"] button')].filter(visivel).map((b) => {
    const col = b.closest('[data-testid="stColumn"]');
    return {rotulo: b.innerText.trim(), largura: r(b).width, coluna: col ? r(col).width : r(b).width};
  });
  const alertas = [...document.querySelectorAll('[data-testid="stAlertContainer"]')].map((a) => {
    const conteudo = a.querySelector('[data-testid^="stAlertContent"]');
    return {tipo: conteudo ? conteudo.getAttribute('data-testid') : '', borda: cs(a).borderLeftColor};
  });
  const texto = document.querySelector('[data-testid="stMarkdownContainer"] p');
  return {
    css_aplicado: [...document.querySelectorAll('style')].some((s) => s.textContent.includes('--pcmso-primaria')),
    inter_carregada: [...document.fonts].some((f) => f.family.replace(/"/g, '') === 'Inter' && f.status === 'loaded'),
    familia_texto: texto ? cs(texto).fontFamily : '',
    passos, faixa, cards, botoes, downloads, alertas,
    dropzones: [...document.querySelectorAll('[data-testid="stFileUploaderDropzone"]')].map((d) => cs(d).borderTopStyle),
  };
}
"""

# PDF mínimo: o parse é mockado, o arquivo só precisa existir para o uploader.
_PDF_FALSO = b"%PDF-1.4\n%%EOF\n"


class ErroInfra(Exception):
    """Falha de ambiente (não do visual): Playwright, servidor, cenário."""


@dataclass(frozen=True)
class ResultadoCenario:
    largura: str
    cenario: str
    falhas: tuple[str, ...]
    screenshot: Path


def _porta_livre() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        porta: int = s.getsockname()[1]
        return porta


def _subir_app(pasta_app: Path, porta: int, log: BinaryIO) -> subprocess.Popen[bytes]:
    script = pasta_app / "app_smoke.py"
    script.write_text(
        _APP_MOCK.format(raiz=str(_RAIZ), entrypoint=str(_RAIZ / "app_matriz_local.py")),
        encoding="utf-8",
    )
    # O Streamlit procura static/ ao lado do script principal, não no cwd.
    shutil.copytree(_RAIZ / "static", pasta_app / "static")
    # cwd na raiz: é dali que o Streamlit lê .streamlit/config.toml (tema e fonte).
    processo = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(script),
         "--server.port", str(porta), "--server.headless", "true",
         "--browser.gatherUsageStats", "false"],
        cwd=_RAIZ, stdout=log, stderr=subprocess.STDOUT,
    )
    limite = time.monotonic() + 90
    while time.monotonic() < limite:
        if processo.poll() is not None:
            raise ErroInfra(f"o Streamlit encerrou ao subir — ver {log.name}")
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{porta}/_stcore/health", timeout=2) as resp:
                if resp.status == 200:
                    return processo
        except (urllib.error.URLError, ConnectionError, TimeoutError):
            pass
        time.sleep(0.5)
    processo.terminate()
    raise ErroInfra(f"o Streamlit não respondeu em 90 s — ver {log.name}")


def _executar_cenario(pagina: Any, cenario: str) -> None:
    if cenario == "inicial":
        return
    pagina.locator('[data-testid="stFileUploaderDropzoneInput"]').first.set_input_files(
        {"name": "pgr.pdf", "mimeType": "application/pdf", "buffer": _PDF_FALSO}
    )
    pagina.get_by_label("Médico coordenador").fill("Dra. Teste", timeout=30_000)
    pagina.get_by_label("CRM").fill("CRM-GO 0000")
    emissao = date.today() + (timedelta(days=200) if cenario == "bloqueio" else -timedelta(days=30))
    pagina.get_by_label("Data de emissão do PGR (AAAA-MM-DD)").fill(emissao.isoformat())
    pagina.get_by_text("Assinado por engenheiro de segurança").click()
    pagina.get_by_role("button", name="Gerar matriz").click()
    alvo = ".st-key-passo_1_bloqueado" if cenario == "bloqueio" else "text=Baixar HTML"
    pagina.wait_for_selector(alvo, timeout=60_000)


def _rodar(saida: Path, chromium: str | None) -> list[ResultadoCenario]:
    try:
        from playwright.sync_api import Error as ErroPlaywright
        from playwright.sync_api import sync_playwright
    except ImportError as erro:
        raise ErroInfra("Playwright ausente: pip install -r requirements-dev.txt") from erro

    porta = _porta_livre()
    base = f"http://127.0.0.1:{porta}"
    resultados: list[ResultadoCenario] = []
    with tempfile.TemporaryDirectory() as tmp, (saida / "streamlit.log").open("wb") as log:
        processo = _subir_app(Path(tmp), porta, log)
        try:
            with sync_playwright() as pw:
                try:
                    navegador = pw.chromium.launch(executable_path=chromium)
                except ErroPlaywright as erro:
                    raise ErroInfra(
                        "Chromium não abriu — rode `python -m playwright install chromium` "
                        f"ou passe --chromium. Detalhe: {str(erro).splitlines()[0]}"
                    ) from erro
                try:
                    for largura, px in LARGURAS.items():
                        for cenario in CENARIOS:
                            resultados.append(_medir(navegador, base, largura, px, cenario, saida))
                finally:
                    navegador.close()
        finally:
            processo.terminate()
            processo.wait(timeout=30)
    return resultados


def _medir(navegador: Any, base: str, largura: str, px: int, cenario: str, saida: Path) -> ResultadoCenario:
    from playwright.sync_api import Error as ErroPlaywright

    pagina = navegador.new_page(viewport={"width": px, "height": 2400})
    respostas: list[tuple[str, int]] = []
    # Hosts saem das REQUISIÇÕES: uma chamada a terceiro bloqueada pela rede não
    # gera resposta, e contar só respostas a deixaria passar.
    requisicoes: list[str] = []
    pagina.on("request", lambda r: requisicoes.append(r.url))
    pagina.on("response", lambda r: respostas.append((r.url, r.status)))
    try:
        pagina.goto(base)
        pagina.wait_for_selector("h1", timeout=60_000)
        _executar_cenario(pagina, cenario)
        pagina.wait_for_timeout(1_500)
        medidas: dict[str, Any] = pagina.evaluate(_JS_MEDIR)
    except ErroPlaywright as erro:
        raise ErroInfra(f"[{largura}] cenário '{cenario}' não carregou: {str(erro).splitlines()[0]}") from erro
    screenshot = saida / f"{largura}_{cenario}.png"
    pagina.screenshot(path=str(screenshot))
    pagina.close()

    fonte = [status for url, status in respostas if url.startswith(base) and "/app/static/fonts/" in url]
    medidas["fonte_status"] = fonte[0] if fonte else None
    medidas["hosts_externos"] = sorted(
        {url.split("/")[2] for url in requisicoes if url.startswith("http") and not url.startswith(base)}
    )
    return ResultadoCenario(largura, cenario, tuple(avaliar(medidas, cenario)), screenshot)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--saida", type=Path, default=None, help="pasta dos screenshots e do log")
    parser.add_argument(
        "--chromium",
        default=os.environ.get("PCMSO_SMOKE_CHROMIUM"),
        help="executável do Chromium (padrão: o instalado pelo Playwright; env PCMSO_SMOKE_CHROMIUM)",
    )
    args = parser.parse_args(argv)
    saida: Path = args.saida or _RAIZ / "relatorios" / "smoke_visual" / datetime.now().strftime("%Y-%m-%d_%H%M%S")
    saida.mkdir(parents=True, exist_ok=True)

    import streamlit

    print(f"Smoke visual - Streamlit {streamlit.__version__}")
    try:
        resultados = _rodar(saida, args.chromium)
    except ErroInfra as erro:
        print(f"ERRO DE INFRAESTRUTURA: {erro}")
        return 2

    for r in resultados:
        situacao = "ok" if not r.falhas else f"{len(r.falhas)} FALHA(S)"
        print(f"[{r.largura:7}] {r.cenario:9} {situacao}")
        for falha in r.falhas:
            # ASCII: no Windows, saída redirecionada usa cp1252, que não tem "✗".
            print(f"    x {falha}")
    total = sum(len(r.falhas) for r in resultados)
    print(f"Screenshots: {saida}")
    print("RESULTADO: ok" if total == 0 else f"RESULTADO: {total} falha(s)")
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
