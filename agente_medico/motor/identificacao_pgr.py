"""Dados da empresa lidos da página de identificação do PGR, para o cabeçalho do PCMSO (D-ARQ-96, fatia 2).

Medido em 15/10/2026 sobre os PGRs do acervo: os dados vêm como "Rótulo: valor" em linha ou numa tabela
CAMPO | INFORMAÇÃO; nos PGRs feitos pelo Seconci o bloco do elaborador vem antes do bloco do cliente; vários
trazem dois endereços (empresa e obra) e dois CNAEs; quando a célula do rótulo é centralizada, o texto do PDF
põe parte do valor na linha de cima. Tudo aqui é sugestão: a tela mostra cada campo para corrigir.
"""

from __future__ import annotations

import re
import unicodedata
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

PAGINAS_LIDAS = 10

_UFS = ("AC|AL|AP|AM|BA|CE|DF|ES|GO|MA|MT|MS|MG|PA|PB|PR|PE|PI|RJ|RN|RS|RO|RR|SC|SP|SE|TO")

_TITULO_NUMERADO = re.compile(r"^\s*\d+(?:\.\d+)*\s*[.\-–)]?\s+[A-ZÀ-Ú]")
_TITULO_ELABORADORA = re.compile(r"(?i)elaboradora|respons[áa]vel\s+t[ée]cnico")
# Rótulo no começo da linha: só letras, até cinco palavras, seguido de ":".
_ROTULO_GENERICO = re.compile(r"^[A-Za-zÀ-ú.º]+(?:\s+[A-Za-zÀ-ú.º/()]+){0,4}\s*:")
_ROTULOS = re.compile(
    r"(?i)^(?:raz[ãa]o\s+social|nome\s+empresarial|empresa|empregador|cnpj|cnae|atividade|grau\s+de\s+risco|"
    r"endere[çc]o|complemento|bairro|cidade|uf|cep|telefone|e-mail|hor[áa]rio|turno|obra|respons[áa]vel|"
    r"engenheiro|eng\.|in[íi]cio|previs[ãa]o|descri[çc][ãa]o|n[º°.]|data|fase|registro|contato|autor|filial)\b"
)

_ENDERECO = re.compile(
    r"(?i)^endere[çc]o\b(?!\s+eletr)"
    r"(?P<qualificador>(?:\s+(?:da|do)\s+(?:obra|empresa|estabelecimento)|\s+escrit[óo]rio|\s+completo)?)"
    r"\s*:?\s*(?P<valor>.*)$"
)
_LINHA_CEP = re.compile(r"(?i)^cep\b")
_CNPJ = re.compile(r"(?i)^cnpj\b\W*(?P<num>\d{2}\W?\d{3}\W?\d{3}\W?\d{4}\W?\d{2})")
_CNAE_LINHA = re.compile(r"(?i)^(?:cnae|atividade\s+principal)")
_CNAE_CODIGO = re.compile(r"(?<!\d)(\d{2})\.?(\d{2})\s*[-–]?\s*(\d)(?:\s*[/\-–]?\s*(\d{2}))?(?!\d)")
_GRAU = re.compile(r"(?i)^grau\s+de\s+risco\s*(?:\(?GR\)?)?\s*[:\-]?\s*0?(?P<grau>[1-4])\b")
_CEP = re.compile(r"(?i)(?:\bCEP\s*[:\-.]?\s*)?(?<!\d)(\d{2})\.?(\d{3})\s*[-.]?\s*(\d{3})(?!\d)\.?")
_CIDADE_UF = re.compile(
    rf"(?<![A-Za-zÀ-ú])(?P<cidade>[A-Za-zÀ-ú][A-Za-zÀ-ú ']{{1,40}}?)\s*[-–/]\s*(?P<uf>{_UFS})\b\.?"
)
_ESTADOS = {
    "ACRE": "AC", "ALAGOAS": "AL", "AMAPA": "AP", "AMAZONAS": "AM", "BAHIA": "BA", "CEARA": "CE",
    "DISTRITO FEDERAL": "DF", "ESPIRITO SANTO": "ES", "GOIAS": "GO", "MARANHAO": "MA", "MATO GROSSO": "MT",
    "MATO GROSSO DO SUL": "MS", "MINAS GERAIS": "MG", "PARA": "PA", "PARAIBA": "PB", "PARANA": "PR",
    "PERNAMBUCO": "PE", "PIAUI": "PI", "RIO DE JANEIRO": "RJ", "RIO GRANDE DO NORTE": "RN",
    "RIO GRANDE DO SUL": "RS", "RONDONIA": "RO", "RORAIMA": "RR", "SANTA CATARINA": "SC", "SAO PAULO": "SP",
    "SERGIPE": "SE", "TOCANTINS": "TO",
}
_SO_ROTULOS = re.compile(r"(?i)^(?:\s*(?:cep|bairro|cidade|uf|cnpj|complemento))+\s*$")


@dataclass(frozen=True)
class IdentificacaoPGR:
    cnpj: str = ""
    cnpj_valido: bool = False
    cnae: str = ""
    descricao_cnae: str = ""
    cnae_alternativo: str = ""
    grau_risco: str = ""
    endereco: str = ""
    complemento: str = ""
    bairro: str = ""
    cidade: str = ""
    uf: str = ""
    cep: str = ""
    endereco_alternativo: str = ""


def cnpj_valido(cnpj: str) -> bool:
    """Dígitos verificadores do CNPJ (módulo 11)."""
    d = [int(c) for c in re.sub(r"\D", "", cnpj)]
    if len(d) != 14 or len(set(d)) == 1:
        return False
    for n in (12, 13):
        pesos = list(range(n - 7, 1, -1)) + list(range(9, 1, -1))
        resto = sum(a * b for a, b in zip(d[:n], pesos)) % 11
        if d[n] != (0 if resto < 2 else 11 - resto):
            return False
    return True


def _formatar_cnpj(bruto: str) -> str:
    d = re.sub(r"\D", "", bruto)
    return f"{d[:2]}.{d[2:5]}.{d[5:8]}/{d[8:12]}-{d[12:]}"


def _rotulada(linha: str) -> bool:
    return bool(_ROTULOS.match(linha) or _ROTULO_GENERICO.match(linha))


def _sem_bloco_elaborador(linhas: list[str]) -> list[str]:
    saida: list[str] = []
    pulando = False
    for linha in linhas:
        if _TITULO_NUMERADO.match(linha):
            pulando = bool(_TITULO_ELABORADORA.search(linha))
        if not pulando:
            saida.append(linha)
    return saida


def _continua(valor: str, seguinte: str) -> bool:
    """A linha seguinte é resto do valor quebrado pelo leiaute, não outro campo."""
    if not seguinte or _rotulada(seguinte):
        return False
    return bool(re.search(r"[-–,/;:]\s*$", valor)) or seguinte[0].islower()


def _valor_do_rotulo(linhas: list[str], i: int, valor: str) -> str:
    """Valor na mesma linha (com quebras), ou, rótulo sozinho, as linhas vizinhas sem rótulo."""
    anterior = linhas[i - 1] if i > 0 else ""
    seguinte = linhas[i + 1] if i + 1 < len(linhas) else ""
    if _SO_ROTULOS.match(valor):
        return seguinte if seguinte and not _rotulada(seguinte) else ""
    if valor:
        partes = [valor]
        for prox in linhas[i + 1 : i + 3]:
            if not _continua(partes[-1], prox):
                break
            partes.append(prox)
        return " ".join(partes)
    partes = [p for p in (anterior, seguinte) if p and not _rotulada(p) and not _TITULO_NUMERADO.match(p)]
    return " ".join(partes)


def _cnae(linhas: list[str]) -> list[tuple[str, str, bool]]:
    """(código NNNN-N/NN, descrição, marcado como considerado para o PGR), na ordem do documento."""
    achados: list[tuple[str, str, bool]] = []
    for i, linha in enumerate(linhas):
        if not _CNAE_LINHA.match(linha):
            continue
        m = _CNAE_CODIGO.search(linha)
        if m is None:
            continue
        codigo = f"{m.group(1)}{m.group(2)}-{m.group(3)}" + (f"/{m.group(4)}" if m.group(4) else "")
        descricao = re.sub(r"\s*[-–]\s*grau\s+de\s+risco.*$", "", linha[m.end():], flags=re.I)
        descricao = descricao.strip(" -–).:")
        if i + 1 < len(linhas) and descricao and _continua(descricao, linhas[i + 1]):
            descricao = f"{descricao} {linhas[i + 1].strip()}"
        achados.append((codigo, descricao, "considerad" in linha.lower()))
    return achados


def _sem_acento(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def _estado_por_extenso(texto: str) -> str:
    """"Goiânia - Goiás" vira "Goiânia - GO" para a busca de cidade/UF."""
    m = re.search(r"[-–/,]\s*([A-Za-zÀ-ú ]+?)\s*[.,]?\s*$", texto)
    if m and (uf := _ESTADOS.get(_sem_acento(m.group(1)).upper().strip())):
        return f"{texto[: m.start(1)]}{uf}"
    return texto


def _separar_endereco(texto: str) -> tuple[str, str, str, str]:
    """(logradouro, cidade, UF, CEP) de um endereço numa linha só."""
    cep = ""
    m = _CEP.search(texto)
    if m:
        cep = f"{m.group(1)}{m.group(2)}-{m.group(3)}"
        texto = texto[: m.start()] + texto[m.end():]
    texto = _estado_por_extenso(texto)
    cidade = uf = ""
    ultimo = None
    for ultimo in _CIDADE_UF.finditer(texto):
        pass
    if ultimo is not None:
        cidade, uf = ultimo.group("cidade").strip(), ultimo.group("uf")
        texto = texto[: ultimo.start()] + texto[ultimo.end():]
    logradouro = re.sub(r"\s{2,}", " ", texto).strip(" ,.;-–/")
    return logradouro, cidade, uf, cep


def _campo_rotulado(linhas: list[str], rotulo: str) -> str:
    padrao = re.compile(rf"(?i)^{rotulo}\b\s*:?\s*(.*)$")
    for linha in linhas:
        m = padrao.match(linha)
        if m and m.group(1).strip() and not _SO_ROTULOS.match(m.group(1)):
            return m.group(1).strip()
    return ""


def _atividade_sem_codigo(linhas: list[str]) -> str:
    """Ricco: "Atividade principal: Construção de edifícios." numa linha e o código na linha "CNAE"."""
    atividade = _campo_rotulado(linhas, r"atividade\s+principal")
    return "" if re.search(r"\d", atividade) else atividade.strip(" .")


def ler_identificacao(paginas: Sequence[str]) -> IdentificacaoPGR:
    """Lê o bloco do cliente nas primeiras páginas do PGR; campo não achado sai vazio."""
    brutas = [ln.strip() for pagina in paginas[:PAGINAS_LIDAS] for ln in pagina.splitlines()]
    linhas = _sem_bloco_elaborador([ln for ln in brutas if ln])

    cnpj = next((m.group("num") for ln in linhas if (m := _CNPJ.match(ln))), "")
    grau = next((m.group("grau") for ln in linhas if (m := _GRAU.match(ln))), "")

    cnaes = _cnae(linhas)
    escolhido = next((c for c in cnaes if c[2]), cnaes[0] if cnaes else ("", "", False))
    alternativo = next((f"{c[0]} {c[1]}".strip() for c in cnaes if c[0] != escolhido[0]), "")

    enderecos: list[tuple[str, bool]] = []
    for i, linha in enumerate(linhas):
        m = _ENDERECO.match(linha)
        if m is None:
            continue
        valor = _valor_do_rotulo(linhas, i, m.group("valor").strip())
        if not valor:
            continue
        # O CEP na linha de baixo é deste endereço, não de outro bloco.
        for prox in linhas[i + 1 : i + 3]:
            if _LINHA_CEP.match(prox) and prox not in valor:
                valor = f"{valor} {prox}"
                break
        da_obra = "obra" in m.group("qualificador").lower() or any(
            re.match(r"(?i)^obra\b", ln) for ln in linhas[max(0, i - 4) : i]
        )
        enderecos.append((valor, da_obra))
    principal = next((e for e in enderecos if e[1]), enderecos[0] if enderecos else ("", False))
    alternativo_end = next((e[0] for e in enderecos if e[0] != principal[0]), "")
    logradouro, cidade, uf, cep = _separar_endereco(principal[0])

    cidade_rotulada = _campo_rotulado(linhas, "cidade")
    if cidade_rotulada and not cidade:
        m_uf = _CIDADE_UF.search(cidade_rotulada)
        cidade = m_uf.group("cidade").strip() if m_uf else cidade_rotulada
        uf = uf or (m_uf.group("uf") if m_uf else "")
    # Com dois endereços, um CEP solto no documento pode ser do outro; só vale quando há um endereço.
    if not cep and len(enderecos) <= 1:
        m_cep = _CEP.search(_campo_rotulado(linhas, "cep"))
        cep = f"{m_cep.group(1)}{m_cep.group(2)}-{m_cep.group(3)}" if m_cep else ""
    bairro = _CEP.split(_campo_rotulado(linhas, "bairro"))[0].strip(" ,.-")

    return IdentificacaoPGR(
        cnpj=_formatar_cnpj(cnpj) if cnpj else "",
        cnpj_valido=bool(cnpj) and cnpj_valido(cnpj),
        cnae=escolhido[0],
        descricao_cnae=escolhido[1] or _atividade_sem_codigo(linhas),
        cnae_alternativo=alternativo,
        grau_risco=grau,
        endereco=logradouro,
        complemento=_campo_rotulado(linhas, "complemento"),
        bairro=bairro,
        cidade=cidade,
        uf=uf or _campo_rotulado(linhas, "uf")[:2].upper(),
        cep=cep,
        endereco_alternativo=alternativo_end,
    )


def ler_identificacao_pdf(caminho: Path) -> IdentificacaoPGR:
    """Só as primeiras páginas; PDF ilegível ou só imagem devolve tudo vazio, para preencher na tela."""
    from agente_medico.motor.io_pdf import ler_faixa

    try:
        paginas = ler_faixa(caminho, 0, PAGINAS_LIDAS)
    except Exception:  # noqa: BLE001 — qualquer falha de leitura vira campos em branco, nunca derruba a tela
        return IdentificacaoPGR()
    return ler_identificacao([p.texto for p in paginas])
