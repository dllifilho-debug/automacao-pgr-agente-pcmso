"""Harness de medição de rodada REAL do pipeline PGR (D-ARQ-62).

Genérico por construção: recebe o caminho do PDF por argumento, não
hard-coda literal de empresa/cliente/setor. Subcomandos:

  ida <pdf> <saida_ida>
      preparar_envelope (TranscritorGeminiTopo) -> artefato JSON de ida ao
      RT, ou pendências (achado de medição, não erro do script).

  rodar <pdf> <artefato_volta> <relatorio_md>
      desserializar_confirmacao (volta já revisada pelo RT) ->
      processar_arquivo_pgr (TranscritorGeminiGHE + TranscritorGeminiCard)
      -> relatório markdown com pendências e matrizes decididas.

  rodar-offline <pdf> <artefato_volta> <relatorio_md>
      mesma trilha de `rodar`, mas com clientes-bomba (TranscritorGHEOffline
      + TranscritorCardOffline) no lugar dos clientes Gemini: qualquer
      invocação ao LLM vira pendência bloqueante transcricao_indisponivel_pgr
      nomeada, nunca mock silencioso (D-ARQ-65).

CHAVE_API_GOOGLE é exigida nos subcomandos ao vivo (`ida`, `rodar`) —
ausência é STOP-and-report, nunca mock nem chave inventada. `rodar-offline`
não exige a chave, por design.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

from agente_medico.adaptadores.orquestracao_pgr import preparar_envelope, processar_arquivo_pgr
from agente_medico.adaptadores.transcritor_gemini_card import TranscritorGeminiCard
from agente_medico.adaptadores.transcritor_gemini_pgr import TranscritorGeminiGHE
from agente_medico.adaptadores.transcritor_gemini_topo import TranscritorGeminiTopo
from agente_medico.adaptadores.transcritor_offline import TranscritorCardOffline, TranscritorGHEOffline
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.revisao_envelope import desserializar_confirmacao
from agente_medico.motor.tipos import Pendencia, Resultado
from agente_medico.motor.transcritor_card import TranscritorCard
from agente_medico.motor.transcritor_pgr import TranscritorGHE
from agente_medico.superficie.apresentacao_matriz import renderizar_matriz

_RAIZ = Path(__file__).resolve().parent.parent


def _exigir_chave() -> None:
    if not os.environ.get("CHAVE_API_GOOGLE"):
        print("STOP-and-report: variável de ambiente CHAVE_API_GOOGLE ausente.", file=sys.stderr)
        sys.exit(1)


def _hash_commit() -> str:
    resultado = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=_RAIZ,
        capture_output=True,
        text=True,
        check=True,
    )
    return resultado.stdout.strip()


def _formatar_pendencia(p: Pendencia) -> str:
    linha_ghe = f"  ghe_id: `{p.ghe_id}`\n" if p.ghe_id is not None else ""
    return (
        f"- tipo: `{p.tipo}`\n"
        f"  destinatario: `{p.destinatario}`\n"
        f"  motivo: {p.motivo}\n"
        f"  bloqueante: {p.bloqueante}\n"
        f"  regra_origem: {p.regra_origem}\n"
        f"{linha_ghe}"
    )


def cmd_ida(args: argparse.Namespace) -> None:
    _exigir_chave()
    pdf = Path(args.pdf)
    cliente = TranscritorGeminiTopo()
    artefato, pendencias = preparar_envelope(pdf, cliente)
    if artefato is None:
        print("Pendências (envelope não gerado):")
        for p in pendencias:
            print(_formatar_pendencia(p))
        sys.exit(1)
    Path(args.saida_ida).write_text(artefato, encoding="utf-8")
    print(f"Artefato de ida gravado em {args.saida_ida}")


def _renderizar_relatorio(pdf: Path, resultado: Resultado | None, pendencias: tuple[Pendencia, ...]) -> str:
    linhas = [
        "# Relatório de medição PGR",
        "",
        f"- pdf: `{pdf}`",
        f"- data: {date.today().isoformat()}",
        f"- commit: `{_hash_commit()}`",
        "",
        "## Pendências",
        "",
    ]
    if pendencias:
        for p in pendencias:
            linhas.append(_formatar_pendencia(p))
    else:
        linhas.append("(nenhuma)")
    linhas.append("")

    linhas.append("## Resultado")
    linhas.append("")
    if resultado is None:
        linhas.append("`resultado` é `None` — parse total falho, sem matrizes.")
        return "\n".join(linhas) + "\n"

    linhas.append(f"- status: `{resultado.status}`")
    if resultado.motivo_rejeicao is not None:
        linhas.append(f"- motivo_rejeicao: {resultado.motivo_rejeicao}")
    linhas.append("")

    if resultado.pendencias_globais:
        linhas.append("### Pendências globais")
        linhas.append("")
        for p in resultado.pendencias_globais:
            linhas.append(_formatar_pendencia(p))
        linhas.append("")

    for matriz in resultado.matrizes:
        linhas.extend(renderizar_matriz(matriz))

    return "\n".join(linhas) + "\n"


def _rodar(pdf: Path, artefato_volta: Path, relatorio_md: Path, cliente: TranscritorGHE, cliente_card: TranscritorCard) -> None:
    texto_volta = artefato_volta.read_text(encoding="utf-8")
    envelope = desserializar_confirmacao(texto_volta)
    protocolo = carregar(_RAIZ / "agente_medico" / "protocolo")
    resultado, pendencias = processar_arquivo_pgr(pdf, protocolo, cliente, cliente_card, envelope)
    relatorio = _renderizar_relatorio(pdf, resultado, pendencias)
    relatorio_md.write_text(relatorio, encoding="utf-8")
    print(f"Relatório gravado em {relatorio_md}")
    if resultado is None:
        sys.exit(1)


def cmd_rodar(args: argparse.Namespace) -> None:
    _exigir_chave()
    _rodar(
        Path(args.pdf),
        Path(args.artefato_volta),
        Path(args.relatorio_md),
        TranscritorGeminiGHE(),
        TranscritorGeminiCard(),
    )


def cmd_rodar_offline(args: argparse.Namespace) -> None:
    _rodar(
        Path(args.pdf),
        Path(args.artefato_volta),
        Path(args.relatorio_md),
        TranscritorGHEOffline(),
        TranscritorCardOffline(),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="comando", required=True)

    p_ida = subparsers.add_parser("ida")
    p_ida.add_argument("pdf")
    p_ida.add_argument("saida_ida")
    p_ida.set_defaults(func=cmd_ida)

    p_rodar = subparsers.add_parser("rodar")
    p_rodar.add_argument("pdf")
    p_rodar.add_argument("artefato_volta")
    p_rodar.add_argument("relatorio_md")
    p_rodar.set_defaults(func=cmd_rodar)

    p_rodar_offline = subparsers.add_parser("rodar-offline")
    p_rodar_offline.add_argument("pdf")
    p_rodar_offline.add_argument("artefato_volta")
    p_rodar_offline.add_argument("relatorio_md")
    p_rodar_offline.set_defaults(func=cmd_rodar_offline)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
