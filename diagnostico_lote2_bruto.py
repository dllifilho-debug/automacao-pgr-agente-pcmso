"""Diagnóstico único: refaz a chamada do LOTE 2 do PGR Viverde direto na API
do Gemini (sem passar por _chamar_gemini, que só devolve o texto), para
inspecionar a resposta HTTP inteira — finishReason, quantas 'parts' o
candidate tem, e uso de tokens. Objetivo: descobrir se a resposta vem
partida em mais de uma 'part' (e o código de produção só lê parts[0]) ou
se é truncamento por token/safety de verdade.

Uso (na raiz do repo, com CHAVE_API_GOOGLE no ambiente):
    CHAVE_API_GOOGLE="sua-chave" python diagnostico_lote2_bruto.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

RAIZ_REPO = Path.cwd()
sys.path.insert(0, str(RAIZ_REPO))

import requests

from agente_medico.motor.extracao_pgr import extrair_texto_pgr, recortar_blocos_ghe
from agente_medico.adaptadores.transcritor_gemini import _MODELOS, _URL, _THINKING_BUDGET
from agente_medico.adaptadores.transcritor_gemini_pgr import _BLOCOS_POR_LOTE, _montar_prompt_lote

CAMINHO_PGR = RAIZ_REPO / "matrizes_originais" / "PGR VIVERDE V02 - 03.02.25.pdf"


def main() -> None:
    chave = os.environ.get("CHAVE_API_GOOGLE", "").strip()
    if not chave:
        print("Defina CHAVE_API_GOOGLE no ambiente antes de rodar.", file=sys.stderr)
        sys.exit(1)

    paginas = extrair_texto_pgr(CAMINHO_PGR)
    blocos = recortar_blocos_ghe(paginas)

    # lote 2 = segundo grupo de _BLOCOS_POR_LOTE blocos (índice 1, 0-based)
    inicio = _BLOCOS_POR_LOTE
    lote2 = blocos[inicio : inicio + _BLOCOS_POR_LOTE]
    print(f"lote 2: blocos {inicio+1} a {inicio+len(lote2)} de {len(blocos)}\n")

    prompt = _montar_prompt_lote(lote2)
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0,
            "thinkingConfig": {"thinkingBudget": _THINKING_BUDGET},
        },
    }

    for modelo in _MODELOS:
        print(f"=== modelo: {modelo} ===")
        r = requests.post(_URL.format(modelo=modelo, chave=chave), json=payload, timeout=120)
        print(f"HTTP {r.status_code}")
        if r.status_code != 200:
            print(r.text[:2000])
            print()
            continue

        corpo = r.json()
        candidato = corpo["candidates"][0]
        print(f"finishReason: {candidato.get('finishReason')}")
        partes = candidato.get("content", {}).get("parts", [])
        print(f"quantidade de parts: {len(partes)}")
        for i, p in enumerate(partes):
            txt = p.get("text", "")
            print(f"  part[{i}]: {len(txt)} chars, thought={p.get('thought')}")
        uso = corpo.get("usageMetadata", {})
        print(f"usageMetadata: {json.dumps(uso, ensure_ascii=False)}")

        texto_so_parts0 = partes[0].get("text", "") if partes else ""
        texto_todas_partes = "".join(p.get("text", "") for p in partes if not p.get("thought"))
        print(f"\ntamanho lendo só parts[0]: {len(texto_so_parts0)} chars")
        print(f"tamanho concatenando todas as parts (exceto thought): {len(texto_todas_partes)} chars")
        print(f"\núltimos 200 chars de parts[0]:\n{texto_so_parts0[-200:]!r}")
        if len(partes) > 1:
            print(f"\núltimos 200 chars de todas as parts concatenadas:\n{texto_todas_partes[-200:]!r}")
        print()
        break  # achou resposta 200, não precisa cair para o próximo modelo


if __name__ == "__main__":
    main()
