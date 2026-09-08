"""Instrumento de varredura de dado pessoal no acervo (003.FJ, versiona o de 003.FI).

Não é código de produção: nenhuma regra clínica é lida ou alterada, o motor não
é importado, `regras.yaml` e `agentes.yaml` não são tocados. Responde a UMA
pergunta, a da cláusula de reabertura de `DH-003FE-01`:

    o acervo `matrizes_originais/` passou a conter dado de TRABALHADOR?

Signatário de documento (engenheiro, médica, representante da empresa) é dado
pessoal COMUM de profissional — LGPD art. 5º I — e não dispara a cláusula.
Trabalhador sob vigilância de saúde é outra classe: nome em relação de
empregados, matrícula, ASO preenchido, resultado de exame ligado a pessoa.
Distinguir os dois é o trabalho deste script; a decisão sobre o resultado é do
Arquiteto.

Origem: a varredura de 003.FI rodou em `/tmp` e morreu com o container, o que é
`DH-003EG-02` ("o instrumento que pauta a fila vive fora do git") reincidindo.
`DH-003FE-01` promete que a cláusula é testável; sem instrumento versionado a
promessa não se cumpre.

**Princípio de projeto, e ele vem de erro medido.** Todo número que este script
imprime carrega o escopo que o produziu, na mesma linha. As quatro rejeições do
Gauntlet em 003.FI tiveram a mesma raiz — um filtro virou universo porque o
filtro não foi escrito ao lado do número (`7` era certo para "literal único",
`40` para "não-PDF", `dois arquivos` para "com marcador", `28` para um rótulo
maior que o medido). Aqui isso é invariante de saída, não disciplina de quem
escreve: `RelatorioAcervo.linhas_escopo()` é obrigatória e os testes a matam se
sumir.

O texto extraido NUNCA e escrito no repositorio por padrao: a conversao do
LibreOffice vai para um `tempfile` fora da arvore, apagado ao fim da execucao.
`--tmp` existe para quem quiser inspecionar, e a ajuda do argumento diz o custo.

Uso:
    python -m scripts.varrer_acervo_lgpd
    python -m scripts.varrer_acervo_lgpd --pasta matrizes_originais --json saida.json

Dependências de extração, todas opcionais e declaradas na saída quando faltam:
`pdfplumber` (PDF), `zipfile` (OOXML, stdlib), LibreOffice headless (`.doc`,
`.rtf`). Ausência de qualquer uma vira `nao_extraido`, nunca silêncio — ver
`DH-003FE-01`, nota de instrumento: em 003.FI o container subiu sem
`libreoffice-writer` e 28 dos 83 arquivos falharam a extração na primeira
passada.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
import unicodedata
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Optional

# --------------------------------------------------------------------------
# Padrões de identificador pessoal
# --------------------------------------------------------------------------

_RE_CPF = re.compile(r"\b(\d{3})[.\s]?(\d{3})[.\s]?(\d{3})[-\s]?(\d{2})\b")
_RE_PIS = re.compile(r"\b\d{3}[.\s]?\d{5}[.\s]?\d{2}[-\s]?\d\b")
_RE_EMAIL = re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")
_RE_ASSINATURA = re.compile(r"assinad[oa]\s+(digital|eletronic)", re.I)
_RE_CRM = re.compile(r"\bCRM[\s/-]*[A-Z]{0,2}[\s:.-]*\d{3,7}\b", re.I)
_RE_CREA = re.compile(r"\bCREA[\s/-]*[A-Z]{0,2}[\s:.-]*[\d.\-/]{5,}\b", re.I)

# Marcadores de dado de TRABALHADOR — o eixo que decide a cláusula de
# DH-003FE-01. Casar marcador NÃO é achado: em 003.FI os 34 arquivos que
# casaram eram, sem exceção, prosa de procedimento e campo em branco de
# formulário ("Relação de empregados próprios, em planilha EXCEL,
# discriminando nome..." é a exigência que a empresa cumpre, não a lista).
# Por isso o relatório devolve CONTEXTO, nunca só a contagem.
_MARCADORES_TRABALHADOR = {
    "ASO": re.compile(r"\bASO\b|atestado de sa[uú]de ocupacional", re.I),
    "relacao_empregados": re.compile(
        r"rela[çc][ãa]o de (empregados|funcion[áa]rios|trabalhadores)", re.I
    ),
    "nome_trabalhador": re.compile(r"nome do (trabalhador|empregado|funcion[áa]rio)", re.I),
    "matricula": re.compile(r"\bmatr[íi]cula\s*:?\s*\d", re.I),
    "admissao": re.compile(r"data de admiss[ãa]o", re.I),
    "resultado_exame": re.compile(r"resultado do exame|\bapto\b|\binapto\b", re.I),
    "prontuario": re.compile(r"prontu[áa]rio", re.I),
}

# Valores de metadata que nomeiam equipamento ou conta genérica, não pessoa.
# Medido em 003.FI sobre os 83 arquivos: 27 valores distintos, 7 desta classe.
VALORES_NAO_PESSOA = frozenset(
    {"DELL", "CMO", "RIMA", "Computador", "Admin", "Usuario", "python-docx", "Microsoft Office Word"}
)

EXT_OOXML = frozenset({".docx", ".xlsx"})
EXT_LEGADO = frozenset({".doc", ".rtf"})
EXT_PDF = frozenset({".pdf"})

_MIN_TEXTO_UTIL = 200


def cpf_valido(digitos: str) -> bool:
    """Dígito verificador do CPF. Sem isto, número de protocolo e série de
    equipamento entram como achado — em 003.FI o padrão casou 19 vezes num
    arquivo onde só 17 eram CPF."""
    if len(digitos) != 11 or not digitos.isdigit():
        return False
    if len(set(digitos)) == 1:
        return False
    for pos in (9, 10):
        soma = sum(int(digitos[i]) * ((pos + 1) - i) for i in range(pos))
        if (soma * 10) % 11 % 10 != int(digitos[pos]):
            return False
    return True


@dataclass(frozen=True)
class Achados:
    """Identificadores encontrados no texto de UM arquivo.

    `cpfs` são validados por dígito verificador. `pis_candidatos` NÃO são
    validados e o nome diz isso: em 003.FI, 2 dos 3 candidatos eram número de
    série de calibrador de vazão e ruído de texto invertido. Promover candidato
    a achado sem conferir contexto é o defeito que o nome do campo impede.
    """

    cpfs: tuple[str, ...] = ()
    pis_candidatos: tuple[str, ...] = ()
    emails: tuple[str, ...] = ()
    assinatura_digital: bool = False
    crm: int = 0
    crea: int = 0


def achados_em_texto(texto: str) -> Achados:
    cpfs = tuple(
        sorted(
            {
                "".join(m.groups())
                for m in _RE_CPF.finditer(texto)
                if cpf_valido("".join(m.groups()))
            }
        )
    )
    return Achados(
        cpfs=cpfs,
        pis_candidatos=tuple(sorted(set(_RE_PIS.findall(texto)))),
        emails=tuple(sorted(set(_RE_EMAIL.findall(texto)))),
        assinatura_digital=bool(_RE_ASSINATURA.search(texto)),
        crm=len(set(_RE_CRM.findall(texto))),
        crea=len(set(_RE_CREA.findall(texto))),
    )


@dataclass(frozen=True)
class OcorrenciaMarcador:
    marcador: str
    contexto: str


def marcadores_com_contexto(texto: str, *, janela: int = 110) -> tuple[OcorrenciaMarcador, ...]:
    """Devolve marcador + trecho ao redor. Contagem de marcador é forma; o
    contexto é a prova, e sem ele o número vira alarme falso (003.FI)."""
    fora: list[OcorrenciaMarcador] = []
    for nome, padrao in _MARCADORES_TRABALHADOR.items():
        achado = padrao.search(texto)
        if achado is None:
            continue
        ini = max(0, achado.start() - janela)
        fim = min(len(texto), achado.end() + janela)
        fora.append(
            OcorrenciaMarcador(marcador=nome, contexto=re.sub(r"\s+", " ", texto[ini:fim]).strip())
        )
    return tuple(fora)


def nomes_de_pessoa(valores: Iterable[str]) -> tuple[str, ...]:
    """Separa nome de pessoa de conta genérica/equipamento. A exclusão é por
    lista explícita, nunca por heurística de forma — `RIMA` e `Guilherme` têm a
    mesma cara para um regex."""
    return tuple(sorted({v.strip() for v in valores if v.strip() and v.strip() not in VALORES_NAO_PESSOA}))


# --------------------------------------------------------------------------
# Extração — cada ramo declara sua falha, nenhuma vira silêncio
# --------------------------------------------------------------------------


def _texto_ooxml(caminho: Path) -> str:
    with zipfile.ZipFile(caminho) as pacote:
        alvos = [n for n in pacote.namelist() if n.endswith(".xml")]
        bruto = "\n".join(pacote.read(n).decode("utf-8", "ignore") for n in alvos)
    return re.sub(r"<[^>]+>", " ", bruto)


def _texto_pdf(caminho: Path) -> str:
    import pdfplumber

    partes: list[str] = []
    with pdfplumber.open(caminho) as documento:
        for pagina in documento.pages:
            partes.append(pagina.extract_text() or "")
            pagina.flush_cache()
    return "\n".join(partes)


def _texto_legado(caminho: Path, destino: Path) -> str:
    """`.doc`/`.rtf` via LibreOffice headless. Exige o pacote do filtro Writer:
    sem ele o `soffice` responde "source file could not be loaded" e a extração
    falha em bloco (003.FI, 28 de 83 na primeira passada)."""
    destino.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["soffice", "--headless", "--convert-to", "txt:Text", "--outdir", str(destino), str(caminho)],
        capture_output=True,
        timeout=180,
        check=False,
    )
    convertido = destino / (caminho.stem + ".txt")
    if not convertido.exists():
        raise RuntimeError("conversao_sem_saida (falta libreoffice-writer?)")
    return convertido.read_text("utf-8", "ignore")


def destino_temporario_padrao() -> Path:
    """Diretório de conversão do LibreOffice, FORA da árvore do repositório.

    O `.txt` que o LibreOffice escreve carrega o texto integral do documento —
    inclusive os CPFs que este script existe para encontrar. Nascer dentro da
    árvore o deixa ao alcance de um `git add`, e depender do `.gitignore` para
    isso é frágil: em 003.FJ o `echo >> .gitignore` colou numa linha sem newline
    final (`._eoltest`, herdada de 003.EH) e produziu o padrão inerte
    `._eoltest.varredura_tmp/`. O Gauntlet apanhou. A correção de fundo é não
    escrever no repositório, não escrever e torcer para o ignore pegar.
    """
    return Path(tempfile.mkdtemp(prefix="varredura_lgpd_"))


def extrair_texto(caminho: Path, destino_tmp: Path) -> str:
    extensao = caminho.suffix.lower()
    if extensao in EXT_PDF:
        return _texto_pdf(caminho)
    if extensao in EXT_OOXML:
        return _texto_ooxml(caminho)
    if extensao in EXT_LEGADO:
        return _texto_legado(caminho, destino_tmp)
    raise RuntimeError(f"extensao_sem_extrator: {extensao}")


def _metadata_ooxml(caminho: Path) -> dict[str, str]:
    campos: dict[str, str] = {}
    with zipfile.ZipFile(caminho) as pacote:
        if "docProps/core.xml" not in pacote.namelist():
            return campos
        xml = pacote.read("docProps/core.xml").decode("utf-8", "ignore")
    for tag, chave in (("dc:creator", "Author"), ("cp:lastModifiedBy", "Last Saved By")):
        achado = re.search(rf"<{tag}>([^<]*)</{tag}>", xml)
        if achado and achado.group(1).strip():
            campos[chave] = achado.group(1).strip()
    return campos


def _metadata_legado(caminho: Path) -> dict[str, str]:
    saida = subprocess.run(["file", "-b", str(caminho)], capture_output=True, text=True).stdout
    campos: dict[str, str] = {}
    for chave in ("Author", "Last Saved By"):
        achado = re.search(rf"{chave}: ([^,]+)", saida)
        if achado:
            campos[chave] = achado.group(1).strip()
    return campos


def _metadata_pdf(caminho: Path) -> dict[str, str]:
    import pdfplumber

    with pdfplumber.open(caminho) as documento:
        autor = (documento.metadata or {}).get("Author")
    return {"Author": str(autor).strip()} if autor and str(autor).strip() else {}


def extrair_metadata_autoria(caminho: Path) -> dict[str, str]:
    """`Author`/`Last Saved By` do cabeçalho do arquivo — OLE2, OOXML ou
    dicionário de informações do PDF. Este eixo (`DH-003FI-01`) não aparece em
    varredura de conteúdo e sobrevive a qualquer redação do corpo. Em 003.FI a
    primeira medição varreu só os 45 não-PDF e perdeu 8 nomes que só os PDFs
    tinham."""
    extensao = caminho.suffix.lower()
    if extensao in EXT_OOXML:
        return _metadata_ooxml(caminho)
    if extensao in EXT_LEGADO:
        return _metadata_legado(caminho)
    if extensao in EXT_PDF:
        return _metadata_pdf(caminho)
    return {}


# --------------------------------------------------------------------------
# Relatório — todo número sai com o escopo que o produziu
# --------------------------------------------------------------------------


@dataclass
class RegistroArquivo:
    nome: str
    extensao: str
    extraido: bool
    motivo_falha: Optional[str] = None
    achados: Achados = field(default_factory=Achados)
    marcadores: tuple[OcorrenciaMarcador, ...] = ()
    metadata: dict[str, str] = field(default_factory=dict)


@dataclass
class RelatorioAcervo:
    pasta: str
    registros: list[RegistroArquivo] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.registros)

    @property
    def extraidos(self) -> list[RegistroArquivo]:
        return [r for r in self.registros if r.extraido]

    @property
    def nao_extraidos(self) -> list[RegistroArquivo]:
        return [r for r in self.registros if not r.extraido]

    def por_extensao(self) -> dict[str, int]:
        contagem: dict[str, int] = {}
        for registro in self.registros:
            contagem[registro.extensao] = contagem.get(registro.extensao, 0) + 1
        return dict(sorted(contagem.items()))

    def cpfs_distintos(self) -> tuple[str, ...]:
        uniao: set[str] = set()
        for registro in self.extraidos:
            uniao.update(registro.achados.cpfs)
        return tuple(sorted(uniao))

    def nomes_na_metadata(self) -> tuple[str, ...]:
        return nomes_de_pessoa(v for r in self.registros for v in r.metadata.values())

    def linhas_escopo(self) -> list[str]:
        """Invariante de saída: nenhum número deste relatório aparece sem o
        escopo que o produziu. É a lição medida de 003.FI virada estrutura —
        ver o docstring do módulo."""
        por_ext = self.por_extensao()
        composicao = " + ".join(f"{n} {ext}" for ext, n in por_ext.items())
        falhas = self.nao_extraidos
        linhas = [
            f"escopo: {self.total} arquivos em {self.pasta}/ ({composicao})",
            f"extraidos: {len(self.extraidos)} de {self.total}"
            + (f"; NAO extraidos: {len(falhas)}" if falhas else "; nenhuma falha de extracao"),
        ]
        for registro in falhas:
            linhas.append(f"  nao_extraido\t{registro.nome}\t{registro.motivo_falha}")
        com_metadata = [r for r in self.registros if r.metadata]
        linhas.append(
            f"metadata de autoria: {len(com_metadata)} de {self.total} arquivos"
            f" (escopo: todas as extensoes, PDF incluido)"
        )
        com_cpf = [r for r in self.extraidos if r.achados.cpfs]
        linhas.append(
            f"CPF com DV valido: {len(self.cpfs_distintos())} distintos"
            f" em {len(com_cpf)} de {len(self.extraidos)} arquivos extraidos"
        )
        com_marcador = [r for r in self.extraidos if r.marcadores]
        linhas.append(
            f"arquivos com marcador de trabalhador: {len(com_marcador)}"
            f" de {len(self.extraidos)} extraidos"
            " — contagem e forma; o contexto abaixo e a prova"
        )
        linhas.append(
            f"nomes de pessoa na metadata: {len(self.nomes_na_metadata())} distintos"
            f" (excluidos {len(VALORES_NAO_PESSOA)} valores de conta generica/equipamento)"
        )
        return linhas


def varrer(pasta: Path, destino_tmp: Path) -> RelatorioAcervo:
    relatorio = RelatorioAcervo(pasta=pasta.name)
    for caminho in sorted(p for p in pasta.iterdir() if p.is_file()):
        metadata = {}
        try:
            metadata = extrair_metadata_autoria(caminho)
        except Exception:  # metadata ilegível não pode derrubar a varredura
            metadata = {}
        try:
            texto = extrair_texto(caminho, destino_tmp)
        except Exception as erro:
            relatorio.registros.append(
                RegistroArquivo(
                    nome=caminho.name,
                    extensao=caminho.suffix.lower(),
                    extraido=False,
                    motivo_falha=str(erro)[:120],
                    metadata=metadata,
                )
            )
            continue
        if len(texto.strip()) < _MIN_TEXTO_UTIL:
            relatorio.registros.append(
                RegistroArquivo(
                    nome=caminho.name,
                    extensao=caminho.suffix.lower(),
                    extraido=False,
                    motivo_falha=f"texto_insuficiente ({len(texto.strip())} chars) — provavel escaneado",
                    metadata=metadata,
                )
            )
            continue
        relatorio.registros.append(
            RegistroArquivo(
                nome=caminho.name,
                extensao=caminho.suffix.lower(),
                extraido=True,
                achados=achados_em_texto(texto),
                marcadores=marcadores_com_contexto(texto),
                metadata=metadata,
            )
        )
    return relatorio


def gerar_relatorio(relatorio: RelatorioAcervo) -> str:
    linhas = ["== VARREDURA DE DADO PESSOAL — matrizes_originais/ =="]
    linhas.extend(relatorio.linhas_escopo())
    linhas.append("")
    linhas.append("-- CPF com DV valido, por arquivo --")
    for registro in relatorio.extraidos:
        if registro.achados.cpfs:
            linhas.append(f"  {len(registro.achados.cpfs)}\t{registro.nome}")
    linhas.append("")
    linhas.append("-- marcador de trabalhador: contexto, arquivo a arquivo --")
    for registro in relatorio.extraidos:
        for ocorrencia in registro.marcadores:
            linhas.append(f"  {registro.nome}\t{ocorrencia.marcador}\t{ocorrencia.contexto}")
    linhas.append("")
    linhas.append("-- nomes de pessoa na metadata --")
    for nome in relatorio.nomes_na_metadata():
        linhas.append(f"  {nome}")
    return "\n".join(linhas)


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pasta", type=Path, default=Path("matrizes_originais"))
    parser.add_argument(
        "--tmp",
        type=Path,
        default=None,
        help="destino da conversao do LibreOffice; padrao = tempfile fora do repositorio,"
        " apagado ao fim. Apontar para dentro da arvore deixa texto extraido (com CPF)"
        " no working tree.",
    )
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    if not args.pasta.is_dir():
        print(f"pasta inexistente: {args.pasta}", file=sys.stderr)
        return 2

    efemero = args.tmp is None
    destino_tmp = destino_temporario_padrao() if efemero else args.tmp
    try:
        relatorio = varrer(args.pasta, destino_tmp)
        print(gerar_relatorio(relatorio))
    finally:
        if efemero:
            shutil.rmtree(destino_tmp, ignore_errors=True)

    if args.json is not None:
        args.json.write_text(
            json.dumps(
                {
                    "pasta": relatorio.pasta,
                    "total": relatorio.total,
                    "por_extensao": relatorio.por_extensao(),
                    "extraidos": len(relatorio.extraidos),
                    "nao_extraidos": [
                        {"nome": r.nome, "motivo": r.motivo_falha} for r in relatorio.nao_extraidos
                    ],
                    "cpfs_distintos": len(relatorio.cpfs_distintos()),
                    "nomes_metadata": list(relatorio.nomes_na_metadata()),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
