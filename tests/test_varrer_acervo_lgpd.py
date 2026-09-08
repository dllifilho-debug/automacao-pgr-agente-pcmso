"""Testes de scripts/varrer_acervo_lgpd.py (003.FJ). Cada teste tem reversão
nomeada, verificada por varredura inversa antes da entrega.

O instrumento existe para responder à cláusula de reabertura de `DH-003FE-01`.
Os testes cobrem o que a varredura de 003.FI errou na prosa e o que ela acertou
na medição — em particular, que todo número sai com o escopo que o produziu.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from scripts.varrer_acervo_lgpd import (
    VALORES_NAO_PESSOA,
    Achados,
    RegistroArquivo,
    RelatorioAcervo,
    achados_em_texto,
    cpf_valido,
    destino_temporario_padrao,
    extrair_metadata_autoria,
    gerar_relatorio,
    marcadores_com_contexto,
    nomes_de_pessoa,
)

# CPFs válidos usados como fixture: gerados para teste, não são de pessoa real.
_CPF_VALIDO = "52998224725"
_CPF_DV_ERRADO = "52998224726"


def test_cpf_valido_rejeita_digito_verificador_errado() -> None:
    """Reversão que mata: remover o laço `for pos in (9, 10)` de `cpf_valido`,
    fazendo-a devolver True para qualquer sequência de 11 dígitos. Sem o DV,
    número de protocolo e série de equipamento entram como CPF — foi assim que
    003.FI mediu 19 ocorrências do padrão num arquivo com 17 CPFs.
    """
    assert cpf_valido(_CPF_VALIDO) is True
    assert cpf_valido(_CPF_DV_ERRADO) is False


def test_cpf_valido_rejeita_sequencia_repetida() -> None:
    """Reversão que mata: remover `if len(set(digitos)) == 1: return False`.
    `111.111.111-11` passa nos dois dígitos verificadores pela aritmética e só a
    guarda explícita o barra. Discriminante contra o teste acima: aquele morre
    removendo o laço do DV, este morre removendo a guarda de repetição.
    """
    assert cpf_valido("11111111111") is False
    assert cpf_valido("00000000000") is False


def test_achados_nao_promove_cpf_invalido() -> None:
    """Reversão que mata: em `achados_em_texto`, tirar a chamada a `cpf_valido`
    do set-comprehension e aceitar todo casamento do padrão.
    """
    texto = f"CPF: {_CPF_VALIDO} e o protocolo {_CPF_DV_ERRADO} do equipamento"
    achados = achados_em_texto(texto)
    assert achados.cpfs == (_CPF_VALIDO,)


def test_pis_sai_como_candidato_e_nao_como_achado() -> None:
    """Reversão que mata: renomear `Achados.pis_candidatos` para `pis` — o nome
    do campo é o que impede promover candidato a achado. Em 003.FI, 2 dos 3
    candidatos eram número de série de calibrador de vazão (`41461832041`) e
    ruído de texto invertido; só 1 era NIT de verdade, e a diferença veio de
    ler o contexto, não o padrão.
    """
    serie = "Calibrador de Vazao: numero de serie: 414.61832.04-1"
    achados = achados_em_texto(serie)
    assert achados.pis_candidatos, "o padrão casa — é candidato, não achado"
    assert not hasattr(achados, "pis"), "candidato não pode ter nome de achado"
    assert "candidato" in type(achados).__dataclass_fields__["pis_candidatos"].name


def test_marcador_de_trabalhador_devolve_contexto_e_nao_so_contagem() -> None:
    """Reversão que mata: fazer `marcadores_com_contexto` devolver só o nome do
    marcador, sem a fatia de texto ao redor. Contagem de marcador é forma; foi
    o contexto que mostrou, em 003.FI, que os 34 arquivos casados eram prosa de
    procedimento — *"Relação de empregados próprios, em planilha EXCEL,
    discriminando nome…"* é a exigência que a empresa cumpre, não a lista.
    """
    texto = (
        "O contratante devera apresentar Relacao de empregados proprios, em planilha "
        "EXCEL, discriminando nome, idade e data de admissao dos envolvidos."
    )
    ocorrencias = marcadores_com_contexto(texto)
    nomes = {o.marcador for o in ocorrencias}
    assert "relacao_empregados" in nomes
    achado = next(o for o in ocorrencias if o.marcador == "relacao_empregados")
    assert "planilha" in achado.contexto
    assert len(achado.contexto) > len("relacao_empregados")


def test_nomes_de_pessoa_exclui_conta_generica_por_lista_explicita() -> None:
    """Reversão que mata: remover o filtro `not in VALORES_NAO_PESSOA` de
    `nomes_de_pessoa`. `RIMA` e `Guilherme` têm a mesma forma para um regex — a
    separação é por lista, nunca por heurística.
    """
    valores = ["Guilherme", "RIMA", "DELL", "Ana Claudia Petry", "python-docx", "  "]
    assert nomes_de_pessoa(valores) == ("Ana Claudia Petry", "Guilherme")
    assert "RIMA" in VALORES_NAO_PESSOA


def _relatorio_sintetico() -> RelatorioAcervo:
    return RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(
                nome="a.pdf",
                extensao=".pdf",
                extraido=True,
                achados=Achados(cpfs=(_CPF_VALIDO,)),
                metadata={"Author": "Ana Claudia Petry"},
            ),
            RegistroArquivo(
                nome="b.doc",
                extensao=".doc",
                extraido=False,
                motivo_falha="conversao_sem_saida (falta libreoffice-writer?)",
                metadata={"Author": "DELL"},
            ),
        ],
    )


def test_relatorio_declara_escopo_de_todo_numero_que_imprime() -> None:
    """Reversão que mata: apagar qualquer linha de `RelatorioAcervo.linhas_escopo`
    que anexa o denominador — por exemplo, trocar
    `"CPF com DV valido: N distintos em X de Y arquivos extraidos"` por
    `"CPF com DV valido: N"`.

    É a lição medida de 003.FI virada invariante: as quatro rejeições do
    Gauntlet tiveram a mesma raiz — um filtro virou universo porque não estava
    escrito ao lado do número.
    """
    linhas = _relatorio_sintetico().linhas_escopo()
    texto = "\n".join(linhas)
    assert "escopo: 2 arquivos em acervo/ (1 .doc + 1 .pdf)" in texto
    assert "extraidos: 1 de 2" in texto
    assert "em 1 de 1 arquivos extraidos" in texto, "CPF sem denominador"
    assert "de 2 arquivos (escopo: todas as extensoes, PDF incluido)" in texto
    assert "excluidos" in texto, "contagem de nomes sem declarar a exclusão"


def test_relatorio_nomeia_cada_arquivo_nao_extraido() -> None:
    """Reversão que mata: em `linhas_escopo`, remover o laço
    `for registro in falhas` que imprime nome e motivo de cada falha.

    Discriminante contra o teste acima: aquele morre tirando um denominador e
    este segue verde; este morre tirando a lista nominal de falhas. Em 003.FI a
    primeira passada falhou em 28 de 83 e reportar só o total teria dito "limpo"
    sobre 55 arquivos com cara de resultado completo.
    """
    texto = "\n".join(_relatorio_sintetico().linhas_escopo())
    assert "nao_extraido\tb.doc\tconversao_sem_saida (falta libreoffice-writer?)" in texto


_PDF_COM_AUTOR = Path("matrizes_originais") / "PGR_EBSERH_UFGD_v7.pdf"


@pytest.mark.skipif(not _PDF_COM_AUTOR.exists(), reason="acervo ausente (DH-003ET-01)")
def test_metadata_de_autoria_le_o_ramo_pdf() -> None:
    """Reversão que mata: em `extrair_metadata_autoria`, remover o ramo
    `if extensao in EXT_PDF: return _metadata_pdf(caminho)` — a função passa a
    devolver `{}` para todo PDF.

    Chama o extrator num PDF **rastreado**, não em fixture sintética: uma versão
    anterior deste teste montava o `RegistroArquivo` com metadata já preenchida
    e por isso sobrevivia à reversão que dizia cobrir. Varredura inversa pegou,
    e é a classe 003.EK — unidade sobre função que nunca leu o campo.

    Foi esse buraco de escopo que fez 003.FI publicar "40 arquivos / 16 nomes"
    medindo só os 45 não-PDF, quando o real era 64 / 20 sobre os 83: oito nomes
    só existiam nos PDFs.
    """
    campos = extrair_metadata_autoria(_PDF_COM_AUTOR)
    assert campos.get("Author") == "Flavio Felipe Soares da Silva"
    assert nomes_de_pessoa(campos.values()) == ("Flavio Felipe Soares da Silva",)


def test_gerar_relatorio_abre_pelo_escopo() -> None:
    """Reversão que mata: em `gerar_relatorio`, remover
    `linhas.extend(relatorio.linhas_escopo())`. O relatório passaria a listar
    achados sem nunca dizer sobre quantos arquivos eles foram medidos.
    """
    saida = gerar_relatorio(_relatorio_sintetico())
    assert saida.splitlines()[1].startswith("escopo: 2 arquivos")


def test_destino_do_texto_extraido_fica_fora_do_repositorio() -> None:
    """Reversão que mata: fazer `destino_temporario_padrao` devolver
    `Path(".varredura_tmp")` — ou qualquer caminho relativo, que resolve dentro
    da árvore.

    O `.txt` do LibreOffice carrega o texto integral do documento, inclusive os
    CPFs que este script existe para achar. Nascer dentro da árvore o deixa ao
    alcance de `git add`. Em 003.FJ a proteção era só o `.gitignore`, e ela
    falhou: o `echo >>` colou numa linha sem newline final (`._eoltest`) e
    produziu o padrão inerte `._eoltest.varredura_tmp/`. O Gauntlet apanhou, e a
    correção de fundo é esta — não escrever no repositório, em vez de escrever e
    depender do ignore.
    """
    destino = destino_temporario_padrao()
    try:
        assert destino.is_absolute(), "caminho relativo resolve dentro da árvore"
        assert Path.cwd() not in destino.resolve().parents
        assert destino.resolve() != (Path.cwd() / ".varredura_tmp").resolve()
    finally:
        shutil.rmtree(destino, ignore_errors=True)


def _docx_minimo(destino: Path, corpo: str) -> None:
    """OOXML mínimo que `_texto_ooxml` consegue ler — evita depender do
    LibreOffice, que não está em todo container (`DH-003FE-01`, nota de
    instrumento)."""
    import zipfile

    with zipfile.ZipFile(destino, "w") as pacote:
        pacote.writestr("docProps/core.xml", "<cp><dc:creator>Ana Claudia Petry</dc:creator></cp>")
        pacote.writestr("word/document.xml", f"<w:document><w:t>{corpo}</w:t></w:document>")


def test_main_apaga_o_destino_efemero_do_texto_extraido(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reversão que mata: em `main`, trocar `efemero = args.tmp is None` por
    `efemero = False`, ou remover o bloco `finally: shutil.rmtree(...)`.

    Exercita `main` de ponta a ponta com o destino efêmero substituído por um
    caminho observável — sem isso o teste mediria `shutil.rmtree`, que é
    stdlib, e sobreviveria à reversão que diz cobrir (classe 003.EK; a mesma
    armadilha já custou um teste refeito nesta sessão).

    Discriminante contra o teste acima: aquele morre mudando o *destino*; este
    morre mantendo o destino certo e não o *apagando*. O `.txt` que fica carrega
    o texto integral do documento, com os CPFs.
    """
    import scripts.varrer_acervo_lgpd as modulo

    destino = tmp_path / "efemero"
    destino.mkdir()
    monkeypatch.setattr(modulo, "destino_temporario_padrao", lambda: destino)

    pasta = tmp_path / "acervo"
    pasta.mkdir()
    _docx_minimo(pasta / "a.docx", "conteudo de teste " * 30)

    assert modulo.main(["--pasta", str(pasta)]) == 0
    assert not destino.exists(), "destino efêmero sobreviveu ao fim de main"


def test_main_preserva_destino_quando_o_usuario_o_nomeia(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reversão que mata: apagar sempre, ignorando `--tmp` — trocar
    `if efemero:` por um `shutil.rmtree` incondicional no `finally`.

    `--tmp` existe para inspeção; apagar o que o usuário nomeou destrói o objeto
    da inspeção. Discriminante contra o teste acima: aquele exige apagar, este
    exige NÃO apagar, e a mesma implementação tem de satisfazer os dois.
    """
    import scripts.varrer_acervo_lgpd as modulo

    nomeado = tmp_path / "nomeado"
    nomeado.mkdir()
    sentinela = nomeado / "inspecao.txt"
    sentinela.write_text("conteudo que o usuario quer inspecionar", encoding="utf-8")

    pasta = tmp_path / "acervo"
    pasta.mkdir()
    _docx_minimo(pasta / "a.docx", "conteudo de teste " * 30)

    assert modulo.main(["--pasta", str(pasta), "--tmp", str(nomeado)]) == 0
    assert sentinela.exists(), "o script apagou o destino que o usuário nomeou"
