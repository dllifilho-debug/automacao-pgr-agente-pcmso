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
    varrer,
    extrair_texto,
    gerar_relatorio,
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

    # Comportamento, não nome: o número de série tem de SAIR na varredura, e sair
    # rotulado CANDIDATO — nunca somado aos achados validados por DV. A versão
    # anterior deste teste asseria
    # `"candidato" in __dataclass_fields__["pis_candidatos"].name`, que é
    # tautologia — assert estruturalmente inalcançável, apanhado pela 6ª rodada
    # do /critico.
    relatorio = RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(nome="a.pdf", extensao=".pdf", extraido=True, achados=achados)
        ],
    )
    assert relatorio.pis_candidatos_distintos() == ("414.61832.04-1",)
    assert relatorio.cpfs_distintos() == (), "candidato não pode entrar na conta de CPF"
    texto = "\n".join(relatorio.linhas_escopo())
    assert "PIS/NIT: 1 CANDIDATOS distintos em 1 de 1 extraidos" in texto


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
    assert "excluidos NESTA medicao" in texto, "contagem de nomes sem declarar a exclusão"


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


def test_exclusao_de_conta_generica_e_medida_e_nao_o_tamanho_da_lista() -> None:
    """Reversão que mata: em `linhas_escopo`, trocar `len(excluidos)` por
    `len(VALORES_NAO_PESSOA)` — isto é, publicar o tamanho da lista do filtro no
    lugar do que foi de fato excluído nesta varredura.

    A distinção não é cosmética. Em 003.FI a lista tinha 8 entradas e só 7
    apareceram no acervo (`Microsoft Office Word` nunca ocorreu), então o número
    publicado fazia `20 nomes + 8 excluídos = 28` contra **27** valores medidos.
    Era o invariante de escopo sendo violado pelo próprio script que o instala —
    número emitido sem o escopo que o produziu —, e o Gauntlet apanhou na 3ª
    rodada. A conta agora tem de fechar: `distintos = pessoas + excluídos`.

    Discriminante contra `test_relatorio_declara_escopo_de_todo_numero_que_imprime`:
    aquele morre tirando um denominador qualquer e sobreviveria a esta troca,
    porque só olhava a substring "excluidos"; este morre exatamente na troca.
    """
    relatorio = RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(
                nome="a.doc",
                extensao=".doc",
                extraido=True,
                metadata={"Author": "Ana Claudia Petry", "Last Saved By": "DELL"},
            ),
        ],
    )
    # A lista do filtro tem 8 entradas; só `DELL` aparece nesta medição.
    assert len(VALORES_NAO_PESSOA) == 8
    assert relatorio.excluidos_nesta_medicao() == ("DELL",)
    assert relatorio.valores_de_autoria() == ("Ana Claudia Petry", "DELL")

    texto = "\n".join(relatorio.linhas_escopo())
    assert "valores distintos no campo de autoria: 2 = 1 nomes de pessoa + 1 de conta" in texto
    assert "a lista do filtro VALORES_NAO_PESSOA tem 8 entradas" in texto


def test_toda_classe_coletada_chega_a_saida() -> None:
    """Reversão que mata: remover de `linhas_escopo` qualquer uma das linhas que
    publicam `pis_candidatos`, `emails`, `assinatura_digital` ou o par
    `crm`/`crea`.

    **Guarda estrutural, não enumeração.** O teste itera os campos de `Achados`
    por `__dataclass_fields__`, então um campo novo que nasça sem caminho de
    saída falha aqui sem ninguém lembrar de estender o teste.

    Origem medida: até `4e67ef2`, cinco das seis classes que `achados_em_texto`
    coleta — `pis_candidatos`, `emails`, `assinatura_digital`, `crm`, `crea` —
    não eram lidas por `linhas_escopo`, `gerar_relatorio` nem `--json`. Um
    e-mail ou PIS de trabalhador no acervo era encontrado e **descartado em
    silêncio**, e o relatório saía limpo no eixo em que a cláusula de
    `DH-003FE-01` decide. É a classe 003.EK do `CLAUDE.md` aplicada ao campo em
    vez de ao teste: dado que nenhuma saída consome.
    """
    relatorio = RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(
                nome="a.pdf",
                extensao=".pdf",
                extraido=True,
                achados=Achados(
                    cpfs=(_CPF_VALIDO,),
                    pis_candidatos=("203.69644.09-8",),
                    emails=("rt@construtora.com.br",),
                    assinatura_digital=True,
                    crm=1,
                    crea=2,
                ),
            )
        ],
    )
    texto = "\n".join(relatorio.linhas_escopo())
    rotulo_por_campo = {
        "cpfs": "CPF com DV valido",
        "pis_candidatos": "PIS/NIT",
        "emails": "e-mail",
        "assinatura_digital": "assinatura digital",
        "crm": "registro profissional",
        "crea": "registro profissional",
    }
    assert set(rotulo_por_campo) == set(Achados.__dataclass_fields__), (
        "campo novo em Achados sem rótulo de saída declarado neste teste"
    )
    for campo, rotulo in rotulo_por_campo.items():
        assert rotulo in texto, f"{campo} coletado mas ausente da saída"


def test_saida_declara_que_pis_nao_e_validado() -> None:
    """Reversão que mata: em `linhas_escopo`, apagar o trecho
    `"nao validados por digito verificador"` da linha de PIS/NIT.

    A seção Fronteira promete "não valida PIS/NIT: devolve candidatos". Até
    `4e67ef2` isso era **falso na única interface do instrumento** — nenhum
    candidato saía. Agora saem, e a saída tem de dizer que não passaram por
    validação, senão o leitor os lê como achado.

    Discriminante contra o teste acima: aquele morre se a linha de PIS sumir;
    este morre com a linha presente e a ressalva removida.
    """
    relatorio = RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(
                nome="a.pdf",
                extensao=".pdf",
                extraido=True,
                achados=Achados(pis_candidatos=("203.69644.09-8",)),
            )
        ],
    )
    texto = "\n".join(relatorio.linhas_escopo())
    assert "CANDIDATOS" in texto
    assert "nao validados por digito verificador" in texto


# ---------------------------------------------------------------------------
# Os três ramos de FALHA de `varrer()`. Até `ff7203d` nenhum tinha teste: a
# suíte só exercitava `varrer` por dentro de `main`, com um `.docx` que extrai
# bem, e todo `RegistroArquivo(extraido=False)` era montado à mão. Logo o
# número `83 de 83 extraidos` que `PENDENCIAS_CLINICAS.md` publica era
# reversível com a suíte verde. Achado pela 5ª rodada do `/critico`.
# ---------------------------------------------------------------------------


def test_pdf_escaneado_sai_nao_extraido_e_nunca_limpo(tmp_path: Path) -> None:
    """Reversão que mata: remover a guarda
    `if len(texto.strip()) < _MIN_TEXTO_UTIL:` de `varrer`.

    Sem ela o escaneado conta como **extraído e limpo** — medido e descartado em
    silêncio, no eixo em que a cláusula de `DH-003FE-01` decide. A seção
    Fronteira promete "não faz OCR — PDF escaneado sai como `nao_extraido` com o
    motivo, nunca como 'limpo'", e a promessa não tinha teste.

    Simulado por um `.docx` cujo corpo tem menos de `_MIN_TEXTO_UTIL` caracteres
    — mesmo ramo, sem depender de um PDF sem camada de texto no acervo.
    """
    pasta = tmp_path / "acervo"
    pasta.mkdir()
    _docx_minimo(pasta / "escaneado.docx", "pouco texto")

    relatorio = varrer(pasta, tmp_path / "tmp")

    assert relatorio.total == 1
    assert relatorio.extraidos == []
    (falha,) = relatorio.nao_extraidos
    assert falha.nome == "escaneado.docx"
    assert "texto_insuficiente" in (falha.motivo_falha or "")
    assert "escaneado" in (falha.motivo_falha or "")
    texto = "\n".join(relatorio.linhas_escopo())
    assert "extraidos: 0 de 1" in texto
    assert "nao_extraido\tescaneado.docx" in texto


def test_extensao_sem_extrator_sai_nomeada_e_nao_silenciosa(tmp_path: Path) -> None:
    """Reversão que mata: remover o `raise RuntimeError("extensao_sem_extrator: ...")`
    de `extrair_texto`, devolvendo `""` para extensão desconhecida.

    Discriminante contra o teste acima: aquele morre tirando a guarda de
    tamanho; este morre com a guarda intacta e a extensão desconhecida
    silenciada. Um `.odt` ou `.pages` no acervo não pode virar "limpo".
    """
    pasta = tmp_path / "acervo"
    pasta.mkdir()
    (pasta / "estranho.odt").write_text("conteudo " * 60, encoding="utf-8")

    relatorio = varrer(pasta, tmp_path / "tmp")

    (falha,) = relatorio.nao_extraidos
    assert "extensao_sem_extrator" in (falha.motivo_falha or "")
    assert ".odt" in (falha.motivo_falha or "")


def test_arquivo_corrompido_vira_falha_nomeada_e_nao_derruba_a_varredura(
    tmp_path: Path,
) -> None:
    """Reversão que mata: remover o `try/except Exception` de `varrer` que
    converte erro de extração em `RegistroArquivo(extraido=False, motivo_falha=...)`.

    Sem ele um único arquivo corrompido aborta a varredura inteira — e o
    operador fica sem relatório algum, que é pior que o relatório incompleto.
    Discriminante contra os dois acima: o `.docx` aqui é um ZIP inválido, então
    a guarda de tamanho nunca é alcançada e a extensão É conhecida.

    Cobre também o invariante de que a varredura **continua**: o segundo arquivo
    da pasta tem de ser medido apesar da falha do primeiro.
    """
    pasta = tmp_path / "acervo"
    pasta.mkdir()
    (pasta / "a_corrompido.docx").write_bytes(b"nao sou um zip")
    _docx_minimo(pasta / "b_ok.docx", "conteudo de teste " * 30)

    relatorio = varrer(pasta, tmp_path / "tmp")

    assert relatorio.total == 2
    (falha,) = relatorio.nao_extraidos
    assert falha.nome == "a_corrompido.docx"
    assert falha.motivo_falha, "falha sem motivo nomeado"
    (ok,) = relatorio.extraidos
    assert ok.nome == "b_ok.docx", "a varredura parou no primeiro erro"


_DOC_COM_AUTOR = Path("matrizes_originais") / "MATRIZ DE EXAME(ADENDO)ENGESEG ESTRUTURAL LTDA 24.04.25.doc"


def test_metadata_de_autoria_le_o_ramo_ooxml(tmp_path: Path) -> None:
    """Reversão que mata: em `extrair_metadata_autoria`, remover
    `if extensao in EXT_OOXML: return _metadata_ooxml(caminho)`.

    Sem esse ramo, todo `.docx`/`.xlsx` devolve `{}` e os nomes que só existem no
    `docProps/core.xml` **somem em silêncio** — no eixo que decide a cláusula de
    `DH-003FE-01` e que `DH-003FI-01` publica (20 dos 27 valores). Até `1003182`
    o ramo não tinha teste: a metadata era montada à mão em todos os casos menos
    o de PDF, que é o padrão que o docstring do teste vizinho condena como classe
    003.EK. Apanhado pela 6ª rodada do `/critico`.

    Discriminante contra `test_metadata_de_autoria_le_o_ramo_pdf`: aquele morre
    removendo o ramo de PDF e este segue verde, e vice-versa.
    """
    alvo = tmp_path / "a.docx"
    _docx_minimo(alvo, "corpo irrelevante")
    campos = extrair_metadata_autoria(alvo)
    assert campos.get("Author") == "Ana Claudia Petry"
    assert nomes_de_pessoa(campos.values()) == ("Ana Claudia Petry",)


@pytest.mark.skipif(not _DOC_COM_AUTOR.exists(), reason="acervo ausente (DH-003ET-01)")
def test_metadata_de_autoria_le_o_ramo_legado_ole2() -> None:
    """Reversão que mata: em `extrair_metadata_autoria`, remover
    `if extensao in EXT_LEGADO: return _metadata_legado(caminho)`.

    `.doc` e `.rtf` são 31 dos 83 arquivos do acervo, e o cabeçalho OLE2 é onde
    vivem `Author` e `Last Saved By`. Sem o ramo, esses 31 devolvem `{}`.

    Usa um `.doc` **rastreado** porque OLE2 não se fabrica com `zipfile`, e a
    versão sintética não exercitaria `file -b`, que é o mecanismo real.
    Discriminante contra os dois testes de metadata acima: cada um morre com a
    remoção do seu próprio ramo.
    """
    campos = extrair_metadata_autoria(_DOC_COM_AUTOR)
    assert campos.get("Author") == "Roberto"
    assert campos.get("Last Saved By") == "Amanda da Silva Rodrigues"
    assert "Amanda da Silva Rodrigues" in nomes_de_pessoa(campos.values())


# ---------------------------------------------------------------------------
# Cobertura dos ramos que dependem de ambiente. Sem estes, `_texto_pdf` e
# `_texto_legado` — os dois extratores que produzem o texto onde os CPFs são
# procurados — ficam sem execução alguma na suíte.
# ---------------------------------------------------------------------------

_PDF_PEQUENO = Path("matrizes_originais") / "PGR R78 NATURIA PARTE 2 12.11.25.pdf"


@pytest.mark.skipif(not _PDF_PEQUENO.exists(), reason="acervo ausente (DH-003ET-01)")
def test_extrair_texto_le_pdf_de_verdade(tmp_path: Path) -> None:
    """Reversão que mata: em `extrair_texto`, remover
    `if extensao in EXT_PDF: return _texto_pdf(caminho)`.

    `_texto_pdf` é onde nasce o texto em que os CPFs são procurados nos 38 PDFs
    do acervo, e não tinha execução alguma na suíte — só era exercitado quando
    alguém rodava o script à mão.
    """
    texto = extrair_texto(_PDF_PEQUENO, tmp_path / "tmp")
    assert len(texto.strip()) > 200, "PDF com camada de texto deve render conteúdo"


def test_extrair_texto_le_ooxml_de_verdade(tmp_path: Path) -> None:
    """Reversão que mata: em `extrair_texto`, remover
    `if extensao in EXT_OOXML: return _texto_ooxml(caminho)`.

    Discriminante contra o de PDF: cada um morre com a remoção do seu ramo.
    """
    alvo = tmp_path / "a.docx"
    _docx_minimo(alvo, "conteudo mensuravel " * 20)
    texto = extrair_texto(alvo, tmp_path / "tmp")
    assert "conteudo mensuravel" in texto


def test_json_carrega_as_mesmas_classes_do_relatorio(tmp_path: Path) -> None:
    """Reversão que mata: em `main`, remover o bloco `if args.json is not None`.

    O `--json` é a interface que outra sessão consome; sem ele o instrumento só
    fala com quem lê o terminal.
    """
    import json

    pasta = tmp_path / "acervo"
    pasta.mkdir()
    _docx_minimo(pasta / "a.docx", "conteudo de teste " * 30)
    destino = tmp_path / "saida.json"

    import scripts.varrer_acervo_lgpd as modulo

    assert modulo.main(["--pasta", str(pasta), "--json", str(destino)]) == 0

    dados = json.loads(destino.read_text("utf-8"))
    assert dados["total"] == 1
    assert dados["por_extensao"] == {".docx": 1}
    assert dados["extraidos"] == 1
    for chave in (
        "cpfs_distintos",
        "pis_candidatos_distintos",
        "emails_distintos",
        "com_assinatura_digital",
        "com_registro_profissional",
        "nomes_metadata",
        "nao_extraidos",
    ):
        assert chave in dados, f"--json perdeu a classe {chave}"


def test_pasta_inexistente_sai_com_codigo_2_e_nao_relatorio_vazio(tmp_path: Path) -> None:
    """Reversão que mata: em `main`, remover a guarda `if not args.pasta.is_dir()`.

    Sem ela, apontar para pasta errada produz um relatório de **zero arquivos**
    que parece uma varredura limpa. É a mesma classe do PDF escaneado: ausência
    lida como ausência de achado.
    """
    import scripts.varrer_acervo_lgpd as modulo

    assert modulo.main(["--pasta", str(tmp_path / "nao_existe")]) == 2


def test_gerar_relatorio_lista_marcador_e_nomes_por_arquivo() -> None:
    """Reversão que mata: em `gerar_relatorio`, remover o laço que imprime
    `ocorrencia.marcador` e `ocorrencia.contexto` por arquivo.

    A contagem de marcadores sai em `linhas_escopo`; o contexto, que é a prova,
    sai só aqui — e era o único trecho de `gerar_relatorio` sem execução.
    """
    relatorio = RelatorioAcervo(
        pasta="acervo",
        registros=[
            RegistroArquivo(
                nome="a.pdf",
                extensao=".pdf",
                extraido=True,
                achados=Achados(cpfs=(_CPF_VALIDO,), emails=("x@y.com",)),
                marcadores=marcadores_com_contexto(
                    "documento cita Relacao de empregados proprios em planilha EXCEL"
                ),
                metadata={"Author": "Ana Claudia Petry"},
            )
        ],
    )
    saida = gerar_relatorio(relatorio)
    assert "relacao_empregados" in saida
    assert "planilha EXCEL" in saida
    assert "Ana Claudia Petry" in saida
    assert "emails=['x@y.com']" in saida


def test_cpf_valido_rejeita_comprimento_e_nao_digito() -> None:
    """Reversão que mata: remover a guarda
    `if len(digitos) != 11 or not digitos.isdigit(): return False` de `cpf_valido`.

    Sem ela, uma sequência curta estoura `IndexError` dentro do laço do DV — e o
    `except Exception` de `varrer` transformaria isso em `nao_extraido`, ou seja,
    o arquivo inteiro sairia como falha de extração por causa de um número mal
    formado no texto. Discriminante contra os dois testes de DV: aqueles morrem
    tirando aritmética, este tirando a validação de forma.
    """
    assert cpf_valido("529") is False
    assert cpf_valido("5299822472a") is False
    assert cpf_valido("") is False


def test_ooxml_sem_core_xml_devolve_metadata_vazia(tmp_path: Path) -> None:
    """Reversão que mata: em `_metadata_ooxml`, remover
    `if "docProps/core.xml" not in pacote.namelist(): return campos`.

    Sem a guarda, um `.docx` sem `docProps/core.xml` levanta `KeyError` no
    `pacote.read`, e o `except` de `varrer` engoliria o arquivo como falha de
    extração — quando o correto é "sem metadata de autoria", que é informação
    diferente de "não consegui ler".
    """
    import zipfile

    alvo = tmp_path / "sem_props.docx"
    with zipfile.ZipFile(alvo, "w") as pacote:
        pacote.writestr("word/document.xml", "<w:document><w:t>corpo</w:t></w:document>")

    assert extrair_metadata_autoria(alvo) == {}


@pytest.mark.skipif(shutil.which("soffice") is None, reason="LibreOffice ausente no ambiente")
def test_extrair_texto_le_legado_via_libreoffice(tmp_path: Path) -> None:
    """Reversão que mata: em `extrair_texto`, remover
    `if extensao in EXT_LEGADO: return _texto_legado(caminho, destino_tmp)`.

    `_texto_legado` cobre 31 dos 83 arquivos do acervo e não tinha execução
    alguma na suíte — era o maior bloco sem cobertura do script. Usa um `.rtf`
    fabricado, não do acervo: RTF é texto plano com marcação, então o arquivo
    cabe no teste e o caminho exercitado é o mesmo (`soffice --convert-to`).

    O `skipif` é honesto e não cosmético: sem `libreoffice-writer` o ramo falha
    em bloco, e foi exatamente isso que aconteceu em 003.FI (28 de 83 na
    primeira passada). Ver `DH-003FE-01`, nota de instrumento.
    """
    alvo = tmp_path / "documento.rtf"
    corpo = "Empresa exemplo com texto suficiente para passar do piso. " * 8
    alvo.write_text(r"{\rtf1\ansi " + corpo + "}", encoding="utf-8")

    texto = extrair_texto(alvo, tmp_path / "tmp")
    assert "Empresa exemplo" in texto


def test_libreoffice_sem_saida_levanta_falha_nomeada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reversão que mata: em `_texto_legado`, remover
    `if not convertido.exists(): raise RuntimeError("conversao_sem_saida ...")`.

    Sem ele, LibreOffice sem o filtro Writer faz o `.txt` nunca aparecer e o
    `read_text` estoura `FileNotFoundError` — que o `except` de `varrer`
    converte num motivo genérico, perdendo a pista de que **falta pacote**.
    Foi exatamente este ramo que disparou em 003.FI: 28 dos 83 arquivos, e o
    motivo nomeado é o que permitiu diagnosticar em vez de adivinhar.

    Simula o `soffice` que roda e não produz saída, sem depender de desinstalar
    o pacote.
    """
    import scripts.varrer_acervo_lgpd as modulo

    monkeypatch.setattr(modulo.subprocess, "run", lambda *a, **k: None)
    alvo = tmp_path / "documento.rtf"
    alvo.write_text("qualquer coisa", encoding="utf-8")

    with pytest.raises(RuntimeError, match="conversao_sem_saida"):
        extrair_texto(alvo, tmp_path / "tmp")
