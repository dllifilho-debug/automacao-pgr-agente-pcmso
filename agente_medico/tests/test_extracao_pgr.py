from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.extracao_pgr import (
    _reconhece_funcao_grid_perigo_risco_fragmentado,
    _reconhece_lotacao_escala_qtd,
    avaliar_estrutura,
    avaliar_familia,
    avaliar_segmentacao,
    detectar_psicossocial,
    eh_ancora_card_cargo,
    eh_cabecalho_ghe,
    eh_sinal_cargo,
    extrair_texto_pgr,
    recortar_blocos_ghe,
    recortar_cards_cargo,
    recortar_topo,
    recuperar_titulos_cargo,
)

# PDF é tracked no git (matrizes_originais/) — ausência é falha explícita,
# não skip (espelha a decisão de test_extracao_fds.py para o acervo untracked,
# mas aqui o arquivo está sob controle de versão: 003.BL / D-ARQ-50).
CAMINHO_PGR = Path("matrizes_originais/PGR VIVERDE V02 - 03.02.25.pdf")

# Revisão de 14/09/2026 do PGR Hetrin (grid AIHA, cabeçalho fragmentado em
# caixa alta) — DT-(sessão não numerada, branch claude/youthful-lamport-3kfkog)-02.
CAMINHO_PGR_HETRIN_SET26 = Path(
    "matrizes_originais/PGR(ATUALIZAÇÃO)RICCO CONSTRUTORA HETRIN 14.09.26.pdf"
)


@pytest.fixture(scope="module")
def paginas() -> list[str]:
    # 151 páginas é caro para parsear por teste — uma extração para a suíte inteira.
    return extrair_texto_pgr(CAMINHO_PGR)


def test_numero_de_paginas(paginas: list[str]) -> None:
    assert len(paginas) == 151


def test_toda_pagina_e_str(paginas: list[str]) -> None:
    assert all(isinstance(pagina, str) for pagina in paginas)


def test_contagem_de_linhas_setor_funcao_no_texto(paginas: list[str]) -> None:
    n_blocos = sum(
        1
        for pagina in paginas
        for linha in pagina.splitlines()
        if linha.startswith("SETOR/FUNÇÃO")
    )
    assert n_blocos == 42


def test_ghe_pintura_preserva_adjacencia_agente_valor(paginas: list[str]) -> None:
    # GHE 13 - Pintura (pág. 71), medido em 003.BL: teste de perda-silenciosa
    # (classe D-ARQ-22) para os valores da quantificação por agente.
    pagina_pintura = paginas[71]
    assert "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in pagina_pintura
    assert "78,8 dB(A) em funcionamento" in pagina_pintura
    assert "Etanol 4,4 ppm" in pagina_pintura
    # "Acetato de Etila" quebra em 2 linhas na extração desta página (verbatim,
    # sem reconstrução de layout — isso é fatia futura de transcrição-LLM).
    assert "Acetato de" in pagina_pintura
    assert "Etila 1 ppm" in pagina_pintura
    assert "Tolueno 6,3 ppm" in pagina_pintura


def test_saida_verbatim_preserva_acento_e_caixa(paginas: list[str]) -> None:
    pagina_pintura = paginas[71]
    assert "SETOR/FUNÇÃO" in pagina_pintura
    assert "SETOR/FUNCAO" not in pagina_pintura


def test_recorte_blocos_ghe_contagem(paginas: list[str]) -> None:
    assert len(recortar_blocos_ghe(paginas)) == 31


def test_recorte_blocos_ghe_todo_bloco_comeca_com_ancora(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    assert all(eh_cabecalho_ghe(bloco.splitlines()[0]) for bloco in blocos)


def test_recorte_blocos_ghe_invariante_de_particao(paginas: list[str]) -> None:
    # Anti perda-silenciosa (classe D-ARQ-22): juntar os blocos de volta
    # reproduz exatamente o texto do documento da 1ª âncora até o fim —
    # nenhuma linha é duplicada ou descartada no recorte.
    blocos = recortar_blocos_ghe(paginas)
    linhas = [linha for pagina in paginas for linha in pagina.splitlines()]
    i_primeira_ancora = next(
        i for i, linha in enumerate(linhas) if eh_cabecalho_ghe(linha)
    )
    texto_esperado = "\n".join(linhas[i_primeira_ancora:])
    assert "\n".join(blocos) == texto_esperado


def test_recorte_blocos_ghe_pintura_preserva_agente_valor(paginas: list[str]) -> None:
    blocos = recortar_blocos_ghe(paginas)
    (bloco_pintura,) = [
        bloco
        for bloco in blocos
        if "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in bloco
    ]
    assert "78,8 dB(A) em funcionamento" in bloco_pintura
    assert "Etanol 4,4 ppm" in bloco_pintura
    assert "Tolueno 6,3 ppm" in bloco_pintura


def test_recorte_blocos_ghe_pintura_cruza_fronteira_de_pagina(paginas: list[str]) -> None:
    # Literal REAL cravado na medição 003.BM (pág. 72, linha 3): pertence ao
    # bloco da Pintura (âncora na pág. 71) mas está na página SEGUINTE —
    # prova que o recorte não trava na fronteira de página.
    blocos = recortar_blocos_ghe(paginas)
    (bloco_pintura,) = [
        bloco
        for bloco in blocos
        if "SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" in bloco
    ]
    assert "Estireno 0,1 ppm" in bloco_pintura


def test_recorte_blocos_ghe_sem_ancora_devolve_lista_vazia() -> None:
    assert recortar_blocos_ghe(["sem ancora aqui", ""]) == []


def test_recorte_blocos_ghe_duas_ancoras_mesma_pagina() -> None:
    pagina = "GHE 1\nlinha A\nGHE 2\nlinha B"
    blocos = recortar_blocos_ghe([pagina])
    assert blocos == ["GHE 1\nlinha A", "GHE 2\nlinha B"]


def test_recorte_topo_termina_antes_da_primeira_ancora(paginas: list[str]) -> None:
    topo = recortar_topo(paginas)
    assert topo is not None
    assert not any(eh_cabecalho_ghe(linha) for linha in topo.splitlines())


def test_recorte_topo_nao_vazio_no_viverde(paginas: list[str]) -> None:
    topo = recortar_topo(paginas)
    assert isinstance(topo, str)
    assert topo != ""


def test_recorte_topo_invariante_de_particao(paginas: list[str]) -> None:
    # Anti perda-silenciosa (classe D-ARQ-22): topo + blocos reconstrói
    # exatamente o texto do documento inteiro — nenhuma linha duplicada
    # ou descartada entre topo e blocos.
    topo = recortar_topo(paginas)
    assert topo is not None
    blocos = recortar_blocos_ghe(paginas)
    linhas = [linha for pagina in paginas for linha in pagina.splitlines()]
    texto_esperado = "\n".join(linhas)
    assert topo + "\n" + "\n".join(blocos) == texto_esperado


def test_recorte_topo_sem_ancora_devolve_none() -> None:
    assert recortar_topo(["sem ancora aqui", ""]) is None


def test_recorte_topo_ancora_na_primeira_linha_devolve_vazio() -> None:
    assert recortar_topo(["GHE 1\nlinha A"]) == ""


# ---------------------------------------------------------------------------
# eh_cabecalho_ghe — repertório de reconhecedores (D-ARQ-57 peça 1,
# DT-003CM-01): formas 1-4 medidas sobre o acervo de 15 PGRs.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "linha",
    [
        "GHE 12",
        "GHE 12 - OBRAS",
        "INVENTÁRIO DE RISCO GHE 3",
        "GHE: 07 - ADMINISTRATIVO",
        # Forma 5 (Ricco-Adm, D-ARQ-57 peça 4 fatia 4a): verbatim REAL medido
        # em 003.DD (perda de diacrítico específica de fonte/glifo — "Õ" ->
        # "O" na 1ª palavra, confirmado por codepoint) e a forma sã com "Õ" —
        # ambas devem casar (classe [OÕ], sem normalização NFC/NFD).
        "INFORMAÇOES SOBRE CARGOS/FUNÇÕES 01",
        "INFORMAÇÕES SOBRE CARGOS/FUNÇÕES 01",
        # Forma 6 (003.DS): separador U+0000 (NUL), medido no PGR Fascino
        # (Consciente SPE 0030), 19 cabeçalhos GHE 01-19, pdfplumber.
        "GHE 01 \x00 ENGENHARIA",  # forma dominante (17 de 19)
        "GHE 16\x00 PINTURA",  # sem espaço antes do NUL (forma real)
        "GHE 10 \x00 INSTALAÇÕES HIDRO\x00SANITÁRIAS",  # NUL embutido no título, preservado
        # Separador ANTES do número, DT-(sessão claude/hopeful-newton-yjv3k7)-01:
        # verbatim real de Porto Araras I (pág. 66) e Vila Brasil Escritório (GHEs 01-22).
        "GHE - 14 PINTURA",
        "GHE\x00 01 \x00 ADMINISTRAÇÃO 01",
    ],
)
def test_eh_cabecalho_ghe_reconhece_cada_forma_medida(linha: str) -> None:
    assert eh_cabecalho_ghe(linha)


@pytest.mark.parametrize(
    "linha",
    [
        "SETOR/FUNÇÃO Pintura/ pintor",
        "Quantidade de Funcionários expostos neste GHE: 08",
        "Fisioterapia do GHE 17 para GHE 11",
        # Forma 5 (003.DD): sem número (fullmatch exige \d+) e com sufixo
        # após o número (fullmatch rejeita qualquer coisa além do número).
        "INFORMAÇÕES SOBRE CARGOS/FUNÇÕES",
        "INFORMAÇÕES SOBRE CARGOS/FUNÇÕES 01 - QUALQUER SUFIXO",
        # 003.DS (PGR Fascino): armadilhas do separador U+0000.
        "GHE\x00 TÉCNICO ADM / OPERACIONAL",  # GHE sem número -> DT-003DS-01 (deferido)
        "GHE Grupo Homogêneo de Exposição: trabalhadores com perfil de exposição similar a determinados agentes",  # linha-glossário (102 char, guard de 80 rejeita)
        # Separador antes do número exige título separado do número: sem isto
        # o \d+ recua e o último dígito vira "título".
        "GHE - 14",
    ],
)
def test_eh_cabecalho_ghe_rejeita_armadilhas_medidas(linha: str) -> None:
    assert not eh_cabecalho_ghe(linha)


def test_recorte_blocos_ghe_conflacao_viverde_nao_gera_bloco_por_processo_subprocesso(
    paginas: list[str],
) -> None:
    # Conflação D-ARQ-22: a 2ª seção do Viverde (PROCESSO/SUBPROCESSO) também
    # começava com "SETOR/FUNÇÃO" mas não tem linha de cabeçalho GHE — a
    # troca de âncora (D-ARQ-57 peça 1) resolve isso por design, deixando de
    # gerar bloco para essa seção.
    blocos = recortar_blocos_ghe(paginas)
    assert not any("PROCESSO/SUBPROCESSO" in bloco.splitlines()[0] for bloco in blocos)


# ---------------------------------------------------------------------------
# avaliar_segmentacao — gate anti-Vistamérica, densidade + contagem
# (D-ARQ-57 peça 2, limiares calibrados em 003.CP sobre DT-003CM-01).
# ---------------------------------------------------------------------------


def _construir_paginas(total_paginas: int, ancoras: dict[int, str]) -> list[str]:
    # 1 linha por página: "GHE n" nas páginas-âncora (1-based), filler nas
    # demais — controla exatamente a extensão em páginas de cada bloco.
    return [
        ancoras.get(pagina, f"linha comum pág. {pagina}")
        for pagina in range(1, total_paginas + 1)
    ]


def test_avaliar_segmentacao_uma_ancora_doc_grande_e_pendencia_por_contagem() -> None:
    paginas = _construir_paginas(20, {5: "GHE 1"})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_zero_ancoras_doc_grande_e_pendencia_por_contagem() -> None:
    paginas = _construir_paginas(20, {})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_doc_pequeno_uma_ancora_e_none() -> None:
    # 8 páginas está abaixo de _LIMIAR_PAGINAS_DOC_MINIMO=10 — 1 bloco
    # cobrindo o documento inteiro é plausível num doc pequeno.
    paginas = _construir_paginas(8, {8: "GHE 1"})
    assert avaliar_segmentacao(paginas) is None


def test_avaliar_segmentacao_doc_pequeno_ancora_no_topo_e_none() -> None:
    # Âncora na pág. 1 -> bloco único satura 100% num doc pequeno; sem o
    # piso de páginas na densidade seria falso-implausível (regressão 003.CR).
    paginas = _construir_paginas(3, {1: "GHE 1"})
    assert avaliar_segmentacao(paginas) is None


def test_avaliar_segmentacao_bloco_denso_e_pendencia_por_densidade() -> None:
    # Âncoras nas págs. 1,2,3,4,12 -> blocos de 1,1,1,8,9 páginas (últ. bloco
    # vai até a pág. 20) — o bloco de 9 págs. excede 40% de 20 (=8 págs.).
    paginas = _construir_paginas(
        20, {1: "GHE 1", 2: "GHE 2", 3: "GHE 3", 4: "GHE 4", 12: "GHE 5"}
    )
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_segmentacao_blocos_distribuidos_e_none() -> None:
    # Âncoras nas págs. 1,5,9,13,17 -> todo bloco tem 4 páginas (<= 40% de 20).
    paginas = _construir_paginas(
        20, {1: "GHE 1", 5: "GHE 2", 9: "GHE 3", 13: "GHE 4", 17: "GHE 5"}
    )
    assert avaliar_segmentacao(paginas) is None


def test_avaliar_segmentacao_pendencia_e_bloqueante_com_regra_origem_darq57() -> None:
    paginas = _construir_paginas(20, {})
    pendencia = avaliar_segmentacao(paginas)
    assert pendencia is not None
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-57"


def test_avaliar_segmentacao_viverde_e_none(paginas: list[str]) -> None:
    # Medição 003.CP: Viverde 151 págs., 31 blocos, maior bloco 29 págs.
    # (= 19,2%) — bem abaixo dos dois limiares.
    assert avaliar_segmentacao(paginas) is None


# ---------------------------------------------------------------------------
# eh_sinal_cargo / avaliar_familia / avaliar_estrutura — família cargo-based
# (D-ARQ-57 peça 3, DT-003CM-01): 3 formas medidas em 003.CQ sobre o acervo.
# ---------------------------------------------------------------------------

CAMINHO_PGR_RICCO_ADM = Path("matrizes_originais/PGR RICCO-2025-ADMINISTRAÇÃO (1).pdf")
CAMINHO_PGR_CJR = Path("matrizes_originais/pgr_Cjr Engenharia Ltda (M Construtora).pdf")


@pytest.mark.parametrize(
    "linha",
    [
        "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas",
        "CARGO TECNÓLOGO EM EDIFICAÇÕES - CBO: 214280",
        "Função Identificação de Perigo / Risco Tempo de Meio de Nível de "
        "Eliminação ou Controle Existente",
        "Lotação: Escala de Trabalho: Qtde:",
        "Lotação: EscaladeTrabalho: Qtd:",
    ],
)
def test_eh_sinal_cargo_reconhece_cada_forma_medida(linha: str) -> None:
    assert eh_sinal_cargo(linha)


@pytest.mark.parametrize(
    "linha",
    [
        "Função/Cargo:",
        "cargo estão expostos.",
        "XXVIII - Seguro contra acidentes de trabalho, á cargo do empregador, "
        "sem excluir, a indenização",
        "SETOR/FUNÇÃO: PRODUÇÃO",
        "Lotação: UTI ADULTO",
        "Escala de Trabalho: 12x36",
    ],
)
def test_eh_sinal_cargo_rejeita_armadilhas_medidas(linha: str) -> None:
    assert not eh_sinal_cargo(linha)


def test_avaliar_familia_sem_ghe_com_sinal_cargo_e_pendencia() -> None:
    paginas = ["linha comum", "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    pendencia = avaliar_familia(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-57"
    assert pendencia.ghe_id is None


def test_avaliar_familia_com_ancora_ghe_e_sinal_cargo_e_none() -> None:
    paginas = ["GHE 1", "CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    assert avaliar_familia(paginas) is None


def test_avaliar_familia_sem_ghe_e_sem_sinal_e_none() -> None:
    paginas = ["linha comum", "outra linha comum"]
    assert avaliar_familia(paginas) is None


# ---------------------------------------------------------------------------
# _reconhece_funcao_grid_perigo_risco_fragmentado — cabeçalho grid AIHA
# quebrado em 2 linhas (Hetrin 14/09/2026). Ver DT-(sessão não numerada,
# branch claude/youthful-lamport-3kfkog)-02 em PENDENCIAS_CLINICAS.md.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "linha_a,linha_b",
    [
        ("FUNÇÃO (quando MEIO DE", "RISCO PERIGO/ RISCO TEMPO DE PROBABILIDAD NÍVEL DE CLASSIFICAÇÃ CONTROLE EXISTENTE"),
        ("FUNÇÃO (quando", "RISCO PERIGO/ RISCO TEMPO DE MEIO DE NÍVEL DE CONTROLE EXISTENTE"),
        ("FUNÇÃO DE PERIGO/ MEIO DE", "RISCO (quando aplicável) TEMPO DE PROBABILIDAD NÍVEL DE CLASSIFICAÇÃ CONTROLE EXISTENTE"),
        ("FUNÇÃO", "RISCO PERIGO/ RISCO (quando TEMPO DE MEIO DE NÍVEL DE CONTROLE EXISTENTE"),
    ],
)
def test_reconhece_funcao_grid_perigo_risco_fragmentado_formas_reais_hetrin(
    linha_a: str, linha_b: str
) -> None:
    # 4 formas medidas direto no PGR Hetrin 14/09/2026 (wrap de coluna do
    # pdfplumber varia por página). Reversão que mata: exigir as 3 palavras
    # numa linha só em vez de no par concatenado.
    assert _reconhece_funcao_grid_perigo_risco_fragmentado(linha_a, linha_b) is True


def test_reconhece_funcao_grid_perigo_risco_fragmentado_linha_unica_tambem_casa() -> None:
    # A forma de linha única (março/2025) também satisfaz o par (linha_b
    # vazia) — o fragmentado é um superconjunto, não substitui o original.
    assert (
        _reconhece_funcao_grid_perigo_risco_fragmentado(
            "Função Identificação de Perigo / Risco Tempo de Meio de...", ""
        )
        is True
    )


@pytest.mark.parametrize(
    "linha_a,linha_b",
    [
        # Prosa real do próprio PGR Hetrin (linhas 561-562, fora da tabela):
        # os 3 termos só aparecem no plural — nem "função" singular ocorre.
        ("O Inventário de Riscos Ocupacionais reúne os", "perigos e riscos identificados nas atividades e funções"),
        # "função"/"perigo" singulares presentes; só "risco" pluralizado —
        # isola a fronteira de palavra especificamente sobre "risco": sem
        # \b, "risco" casaria como substring de "riscos" e o par passaria.
        ("Toda função tem perigo e riscos variados", "nada de tabela aqui"),
        # "função"/"risco" singulares presentes; só "perigo" pluralizado —
        # isola a fronteira sobre "perigo" (mesmo raciocínio, termo trocado).
        ("A função avalia perigos diversos", "mas o risco não aparece na tabela"),
    ],
)
def test_reconhece_funcao_grid_perigo_risco_fragmentado_rejeita_prosa_no_plural(
    linha_a: str, linha_b: str
) -> None:
    # Anti-falso-positivo: "riscos"/"perigos" no plural não podem casar —
    # \b falha logo após o 's' ("função"→"funções" já não bate nem sem \b,
    # o acento muda: ã→õ). Reversão que mata: trocar \b por substring
    # simples (in) sem fronteira de palavra — casos 2 e 3 viram True.
    assert _reconhece_funcao_grid_perigo_risco_fragmentado(linha_a, linha_b) is False


def test_avaliar_familia_grid_aiha_fragmentado_sintetico_e_pgr_cargo_based() -> None:
    # Reversão que mata: remover a soma de n_sinais_cargo com o loop de
    # pares adjacentes em avaliar_familia (extracao_pgr.py).
    paginas = ["linha comum", "FUNÇÃO (quando", "RISCO PERIGO/ RISCO TEMPO DE MEIO DE"]
    pendencia = avaliar_familia(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"


def test_avaliar_familia_pgr_hetrin_set26_real_e_pgr_cargo_based_nao_segmentacao() -> None:
    # Documento real: antes deste fix, avaliar_familia devolvia None (0
    # linhas casavam o regex de linha única) e o app bloqueava com a
    # pendência ERRADA (segmentacao_implausivel, sugere doc anômalo).
    # Reversão que mata: qualquer uma das duas de cima.
    paginas = extrair_texto_pgr(CAMINHO_PGR_HETRIN_SET26)
    pendencia = avaliar_familia(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
    assert pendencia.bloqueante is True


def test_avaliar_estrutura_pgr_hetrin_set26_real_diagnostico_correto() -> None:
    # Nível de avaliar_estrutura (o que o app realmente consulta em
    # preparar_ghes): mesma pendência correta, não segmentacao_implausivel.
    paginas = extrair_texto_pgr(CAMINHO_PGR_HETRIN_SET26)
    _rota, pendencia = avaliar_estrutura(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"


def test_avaliar_familia_pgr_hetrin_mar25_real_permanece_pgr_cargo_based() -> None:
    # Não-regressão: a forma de linha única (março/2025) já funcionava
    # (123 casos) e continua funcionando depois do fix.
    caminho_mar25 = Path("matrizes_originais/01. PGR RICCO HETRIN - MAR25.pdf")
    paginas = extrair_texto_pgr(caminho_mar25)
    pendencia = avaliar_familia(paginas)
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"


def test_avaliar_estrutura_cargo_based_grande_e_pgr_cargo_based_nao_segmentacao() -> None:
    # Doc grande (>10 págs.), 0 âncoras GHE, com sinal-cargo (CARGO/FUNÇÃO:
    # NÃO é âncora-de-recorte card, só sinal-de-família — 003.DC): cai no
    # 3º ramo de avaliar_estrutura (rota "ghe", avaliar_familia). Sem a
    # peça 3 este caso cairia no gate genérico e emitiria
    # segmentacao_implausivel (contagem: 0 blocos em doc >10 págs.) — a
    # peça 3 sela a exclusão mútua.
    paginas = _construir_paginas(20, {}) + ["CARGO/FUNÇÃO: JORNADA TRABALHO: 08 horas"]
    rota, pendencia = avaliar_estrutura(paginas)
    assert rota == "ghe"
    assert pendencia is not None
    assert pendencia.tipo == "pgr_cargo_based"
    assert pendencia.tipo != "segmentacao_implausivel"


def test_avaliar_estrutura_ghe_implausivel_delega_segmentacao() -> None:
    paginas = _construir_paginas(20, {5: "GHE 1"})
    rota, pendencia = avaliar_estrutura(paginas)
    assert rota == "ghe"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_estrutura_viverde_e_none(paginas: list[str]) -> None:
    rota, pendencia = avaliar_estrutura(paginas)
    assert rota == "ghe"
    assert pendencia is None


def test_avaliar_estrutura_ricco_adm_real_e_segmentacao_implausivel() -> None:
    # Flip deliberado (decisão 003.DD, não regressão): a forma 5 do
    # repertório GHE (D-ARQ-57 peça 4 fatia 4a) reclassifica o Ricco-Adm de
    # cargo-based para GHE-based (2 blocos reconhecidos), mas o bloco 2 mede
    # 10/24 págs. = 41,7% > _LIMIAR_DENSIDADE_PCT (40,0%) — gated por
    # densidade a jusante, revisão humana BY DESIGN (mesma classe do Cjr,
    # falso-positivo aceito, decisão 003.DD sobre medição real; NÃO
    # recalibrar _LIMIAR_DENSIDADE_PCT). Rota "ghe" inalterada pela fatia 4d
    # (medido no PASSO 0 da 003.DK): Ricco-Adm tem âncora GHE forma 5, o
    # split card nunca é consultado (ramo 1 vence por precedência).
    paginas_ricco = extrair_texto_pgr(CAMINHO_PGR_RICCO_ADM)
    rota, pendencia = avaliar_estrutura(paginas_ricco)
    assert rota == "ghe"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"
    assert pendencia.bloqueante is True
    assert pendencia.tipo != "pgr_cargo_based"


def test_recorte_blocos_ghe_ricco_adm_real() -> None:
    # Witness de que reconhecedor+recorte funcionam apesar do gate a
    # jusante (avaliar_estrutura): 2 blocos, cada um começando na âncora
    # forma 5 (D-ARQ-57 peça 4 fatia 4a, medição 003.DD).
    paginas_ricco = extrair_texto_pgr(CAMINHO_PGR_RICCO_ADM)
    blocos = recortar_blocos_ghe(paginas_ricco)
    assert len(blocos) == 2
    assert all(eh_cabecalho_ghe(bloco.splitlines()[0]) for bloco in blocos)


# ---------------------------------------------------------------------------
# avaliar_estrutura — split de roteamento ghe/card (D-ARQ-57 peça 4 fatia 4d,
# FECHA DT-003CS-01). Sintéticos de fronteira + precedência; molde
# _construir_paginas dos testes de avaliar_segmentacao acima.
# ---------------------------------------------------------------------------


def test_avaliar_estrutura_card_distribuido_e_none() -> None:
    # Espelho de test_avaliar_segmentacao_blocos_distribuidos_e_none: 5
    # âncoras card (CARGO-CBO) nas págs. 1,5,9,13,17 de 20 -> todo card tem
    # 4 páginas (<= 40% de 20) -> sem pendência.
    paginas = _construir_paginas(
        20,
        {
            1: "CARGO A - CBO: 111111",
            5: "CARGO B - CBO: 222222",
            9: "CARGO C - CBO: 333333",
            13: "CARGO D - CBO: 444444",
            17: "CARGO E - CBO: 555555",
        },
    )
    rota, pendencia = avaliar_estrutura(paginas)
    assert rota == "card"
    assert pendencia is None


def test_avaliar_estrutura_card_gated_por_contagem() -> None:
    # Espelho de test_avaliar_segmentacao_uma_ancora_doc_grande_e_pendencia_
    # por_contagem: 1 card único num doc de 20 págs. (> _LIMIAR_PAGINAS_DOC_
    # MINIMO) -- mesmo gate de contagem da peça 2, via _avaliar_spans reusado.
    paginas = _construir_paginas(20, {5: "CARGO A - CBO: 111111"})
    rota, pendencia = avaliar_estrutura(paginas)
    assert rota == "card"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_avaliar_estrutura_precedencia_ghe_vence_card() -> None:
    # Doc com as duas âncoras: eh_cabecalho_ghe casa primeiro -> ramo 1
    # sempre vence, eh_ancora_card_cargo nunca é sequer consultado.
    paginas = _construir_paginas(20, {1: "GHE 1", 2: "CARGO A - CBO: 111111"})
    rota, _pendencia = avaliar_estrutura(paginas)
    assert rota == "ghe"


def test_avaliar_estrutura_precedencia_card_vence_familia() -> None:
    # Doc com sinal-de-família grid-AIHA (eh_sinal_cargo, NÃO
    # eh_ancora_card_cargo) E âncora-de-recorte card (Lotação-tripla): a
    # âncora-de-recorte vence o sinal-de-família — ramo 2, não ramo 3.
    paginas = _construir_paginas(
        20,
        {
            1: (
                "Função Identificação de Perigo / Risco Tempo de Meio de "
                "Nível de Eliminação ou Controle Existente"
            ),
            5: "Lotação: Escala de Trabalho: Qtde:",
        },
    )
    rota, _pendencia = avaliar_estrutura(paginas)
    assert rota == "card"


def test_avaliar_estrutura_cjr_real_e_card_gated_por_contagem() -> None:
    # FLIP 1-por-1 (D-ARQ-57 peça 4 fatia 4d, nomeado no relatório da
    # sessão): pré-4d o Cjr saía ("pgr_cargo_based", peça 3 — CARGO-CBO era
    # só sinal-de-família). O Cjr TEM âncora-de-recorte card (mesma linha
    # CARGO-CBO também está em _RECORTADORES_CARGO/eh_ancora_card_cargo,
    # 003.DC) — a fatia 4d insere o ramo 2 ANTES da família, então o Cjr
    # migra para rota "card". 1 card em doc de 18 págs. (> _LIMIAR_PAGINAS_
    # DOC_MINIMO=10) -> gate de contagem (mesmos limiares da peça 2, via
    # _avaliar_spans reusado) -> segmentacao_implausivel. GATED by design,
    # mesma classe do V2/003.DC — witness do recorte, não recalibrado.
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    rota, pendencia = avaliar_estrutura(paginas_cjr)
    assert rota == "card"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


# ---------------------------------------------------------------------------
# Lotação/Escala de Trabalho/Qtd — card cargo-based do template corporativo
# EBSERH PGR.SOST.001 (D-ARQ-57 peça 3, censo 003.CZ, medição 003.DA).
# ---------------------------------------------------------------------------

CAMINHO_PGR_EBSERH_UFGD_V7 = Path("matrizes_originais/PGR_EBSERH_UFGD_v7.pdf")
CAMINHO_PGR_EBSERH_LEGADO_GHES = Path(
    "matrizes_originais/PGR_EBSERH_UFGD_legado_GHES.pdf"
)
CAMINHO_PGR_EBSERH_HUMAP = Path("matrizes_originais/PGR_EBSERH_HUMAP.pdf")


@pytest.fixture(scope="module")
def paginas_ebserh_ufgd_v7() -> list[str]:
    # 184 páginas — uma extração para a suíte inteira (molde da fixture paginas).
    return extrair_texto_pgr(CAMINHO_PGR_EBSERH_UFGD_V7)


@pytest.fixture(scope="module")
def paginas_ebserh_legado_ghes() -> list[str]:
    # 197 páginas — uma extração para a suíte inteira (molde da fixture paginas).
    return extrair_texto_pgr(CAMINHO_PGR_EBSERH_LEGADO_GHES)


@pytest.fixture(scope="module")
def paginas_ebserh_humap() -> list[str]:
    # 368 páginas — uma extração para a suíte inteira (molde da fixture paginas).
    return extrair_texto_pgr(CAMINHO_PGR_EBSERH_HUMAP)


def test_avaliar_estrutura_ebserh_ufgd_v7_e_card_sem_pendencia(
    paginas_ebserh_ufgd_v7: list[str],
) -> None:
    # FLIP 1-por-1 (D-ARQ-57 peça 4 fatia 4d): 105 âncoras card (Lotação-
    # tripla) >> gate de contagem/densidade (mesmos limiares da peça 2, via
    # _avaliar_spans reusado) -- sem pendência, EBSERH-UFGD entra em
    # produção pela rota card.
    rota, pendencia = avaliar_estrutura(paginas_ebserh_ufgd_v7)
    assert rota == "card"
    assert pendencia is None


def test_avaliar_estrutura_ebserh_humap_e_card_gated_por_densidade(
    paginas_ebserh_humap: list[str],
) -> None:
    # Witness da classe 003.DD-2 no lado card (achado do PASSO 0 desta
    # sessão, correção do Arquiteto ratificada pelo Diovanni): a última das
    # 140 âncoras Lotação-tripla está na pág. 186 de 368 — depois dela vem
    # um bloco de ASSINATURA/aprovação do documento inteiro ("Assinado
    # eletronicamente", nomes, matrículas SIAPE), não outro card. Por
    # construção (mesma sobre-inclusão-de-cauda de recortar_blocos_ghe/
    # recortar_cards_cargo, D-ARQ-22), esse apêndice de 183/368 páginas
    # (49,7%) vira o span do "último card" -> excede _LIMIAR_DENSIDADE_PCT
    # (40,0%) -> segmentacao_implausivel. GATED by design, 2ª testemunha da
    # mesma classe do Ricco-Adm (003.DD-2, lado GHE) — limiares INTOCADOS,
    # revisão humana bloqueante, anti-supressão D-ARQ-22/31/35 vence.
    rota, pendencia = avaliar_estrutura(paginas_ebserh_humap)
    assert rota == "card"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"
    assert pendencia.bloqueante is True
    assert pendencia.regra_origem == "D-ARQ-57"
    assert "card" in pendencia.motivo


def test_avaliar_estrutura_ebserh_legado_ghes_e_segmentacao_implausivel(
    paginas_ebserh_legado_ghes: list[str],
) -> None:
    # Witness de REGRESSÃO do bloqueador achado no PASSO 0 desta sessão
    # (003.DK): o legado GHES (197 págs.) não tem NENHUMA âncora
    # reconhecível — nem GHE numerado, nem card (eh_ancora_card_cargo), nem
    # sinal-de-família cargo (eh_sinal_cargo; 003.CZ já confirmou zero
    # colisão do reconhecedor-Lotação sobre este doc). Cai inteiro no 3º
    # ramo de avaliar_estrutura: avaliar_familia devolve None (sem sinal),
    # e o fallback para avaliar_segmentacao PRECISA disparar — sem ele, um
    # doc âncora-zero sairia ("ghe", None) em silêncio, violação D-ARQ-22/
    # anti-supressão D-ARQ-31/35. Corrigido pelo Arquiteto ANTES da IMPL
    # (achado do PASSO 0, MUDANÇA 1c re-medida antes de codar).
    rota, pendencia = avaliar_estrutura(paginas_ebserh_legado_ghes)
    assert rota == "ghe"
    assert pendencia is not None
    assert pendencia.tipo == "segmentacao_implausivel"


def test_reconhecedor_lotacao_zero_matches_no_ghes_legado(
    paginas_ebserh_legado_ghes: list[str],
) -> None:
    # Não-colisão medida em 003.CZ: o formato legado GHES não usa o card
    # Lotação/Escala/Qtd — o reconhecedor não mislabela esse acervo.
    linhas = [linha for pagina in paginas_ebserh_legado_ghes for linha in pagina.splitlines()]
    n_casos = sum(1 for linha in linhas if _reconhece_lotacao_escala_qtd(linha))
    assert n_casos == 0


# ---------------------------------------------------------------------------
# recortar_cards_cargo — recorte 1:1 ISOLADO, unidade = card cargo-based
# (D-ARQ-57 peça 4 fatia 4b, decisão 003.DC; consome DT-003DB-01).
# ---------------------------------------------------------------------------


def test_recortar_cards_cargo_duas_ancoras_lotacao_fronteiras_corretas() -> None:
    pagina = (
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1\n"
        "Lotação: Escala de Trabalho: Qtde: linha B\n"
        "conteudo 2"
    )
    cards = recortar_cards_cargo([pagina])
    assert cards == [
        "Lotação: Escala de Trabalho: Qtde: linha A\nconteudo 1",
        "Lotação: Escala de Trabalho: Qtde: linha B\nconteudo 2",
    ]


def test_recortar_cards_cargo_duas_ancoras_cargo_cbo_fronteiras_corretas() -> None:
    pagina = (
        "CARGO PEDREIRO - CBO: 711205\n"
        "conteudo A\n"
        "CARGO SERVENTE - CBO: 841205\n"
        "conteudo B"
    )
    cards = recortar_cards_cargo([pagina])
    assert cards == [
        "CARGO PEDREIRO - CBO: 711205\nconteudo A",
        "CARGO SERVENTE - CBO: 841205\nconteudo B",
    ]


def test_recortar_cards_cargo_sem_ancora_devolve_lista_vazia() -> None:
    assert recortar_cards_cargo(["sem ancora aqui", ""]) == []


def test_recortar_cards_cargo_grid_aiha_nao_ancora_card() -> None:
    # Teste negativo do RECORTE (003.DC): o grid-header AIHA é sinal-de-
    # família (eh_sinal_cargo/_RECONHECEDORES_CARGO), mas NÃO é âncora de
    # recorte 1:1 — não delimita um card individual.
    linha_grid = (
        "Função Identificação de Perigo / Risco Tempo de Meio de Nível de "
        "Eliminação ou Controle Existente"
    )
    assert not eh_ancora_card_cargo(linha_grid)
    assert recortar_cards_cargo([linha_grid, "conteudo"]) == []


def test_recortar_cards_cargo_ufgd_v7_real_105_cards(
    paginas_ebserh_ufgd_v7: list[str],
) -> None:
    cards = recortar_cards_cargo(paginas_ebserh_ufgd_v7)
    assert len(cards) == 105


def test_recortar_cards_cargo_humap_real_140_cards(
    paginas_ebserh_humap: list[str],
) -> None:
    cards = recortar_cards_cargo(paginas_ebserh_humap)
    assert len(cards) == 140


def test_recortar_cards_cargo_cjr_real_1_card() -> None:
    # Cjr é witness do RECORTE (1 card, CARGO-CBO) — no roteamento (fatia
    # 4d) ele fica GATED por design no gate de contagem de
    # avaliar_segmentacao (classe V2/003.DC), sem recalibrar o gate por
    # este witness.
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    cards = recortar_cards_cargo(paginas_cjr)
    assert len(cards) == 1


# ---------------------------------------------------------------------------
# recuperar_titulos_cargo — recuperação determinística do título-de-cargo
# (D-ARQ-57 peça 4 fatia 4c, decisão 003.DG-4). Título fora do span do card
# (003.DG-4): recuperado da cauda do card ANTERIOR, no texto de página cheia.
# ---------------------------------------------------------------------------


def test_recuperar_titulos_cargo_par_presente_recupera_titulo_duas_ancoras() -> None:
    pagina = (
        "13.1 Advogado\n"
        "DADOS GERAIS\n"
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1\n"
        "13.2 Analista\n"
        "DADOS GERAIS\n"
        "Lotação: Escala de Trabalho: Qtde: linha B\n"
        "conteudo 2"
    )
    titulos = recuperar_titulos_cargo([pagina])
    assert titulos == ["13.1 Advogado", "13.2 Analista"]


def test_recuperar_titulos_cargo_sem_dados_gerais_adjacente_e_vazio() -> None:
    # Discriminador — regressão do falso-positivo medido no HUMAP (003.DH):
    # "4.3 RESUMO FINAL DA IDENTIFICAÇÃO DOS RISCOS BIOLÓGICOS MAIS" casa
    # `NN.N Nome` mas é título de SEÇÃO, não de cargo — sem `DADOS GERAIS`
    # adjacente, exigir o PAR rejeita.
    pagina = (
        "4.3 RESUMO FINAL DA IDENTIFICAÇÃO DOS RISCOS BIOLÓGICOS MAIS\n"
        "outra linha qualquer, sem o marcador esperado por perto\n"
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1"
    )
    titulos = recuperar_titulos_cargo([pagina])
    assert titulos == [""]


def test_recuperar_titulos_cargo_dados_gerais_colado_recupera() -> None:
    # Regressão do space-collapse — o HUMAP extrai colado (DADOSGERAIS).
    pagina = (
        "13.1 Advogado\n"
        "DADOSGERAIS\n"
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1"
    )
    titulos = recuperar_titulos_cargo([pagina])
    assert titulos == ["13.1 Advogado"]


def test_recuperar_titulos_cargo_sem_ancora_devolve_lista_vazia() -> None:
    assert recuperar_titulos_cargo(["sem ancora aqui", ""]) == []


def test_recuperar_titulos_cargo_card_0_recupera_do_texto_pre_ancora() -> None:
    pagina = (
        "13.1 Advogado\n"
        "DADOS GERAIS\n"
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1"
    )
    titulos = recuperar_titulos_cargo([pagina])
    assert titulos == ["13.1 Advogado"]


def test_recuperar_titulos_cargo_titulo_alem_da_janela_e_vazio() -> None:
    # `DADOS GERAIS` existe no vão, mas a mais de 3 linhas do candidato-título.
    pagina = (
        "13.1 Advogado\n"
        "linha de enchimento 1\n"
        "linha de enchimento 2\n"
        "linha de enchimento 3\n"
        "DADOS GERAIS\n"
        "Lotação: Escala de Trabalho: Qtde: linha A\n"
        "conteudo 1"
    )
    titulos = recuperar_titulos_cargo([pagina])
    assert titulos == [""]


def test_recuperar_titulos_cargo_ufgd_v7_real_105_titulos(
    paginas_ebserh_ufgd_v7: list[str],
) -> None:
    # Gabarito medido em 003.DH (host, pdfplumber).
    titulos = recuperar_titulos_cargo(paginas_ebserh_ufgd_v7)
    assert len(titulos) == 105
    nao_vazios = [t for t in titulos if t]
    assert len(nao_vazios) == 105
    assert len(set(nao_vazios)) == 105
    assert titulos[0] == "13.1 Advogado"
    assert titulos[-1] == "13.106 Terapeuta Ocupacional"


def test_recuperar_titulos_cargo_humap_real_140_entradas_0_nao_vazias(
    paginas_ebserh_humap: list[str],
) -> None:
    # 0 é resultado LEGÍTIMO neste documento (003.DH): o cargo vive na linha
    # de valores do próprio card, não em título numerado.
    titulos = recuperar_titulos_cargo(paginas_ebserh_humap)
    assert len(titulos) == 140
    assert len([t for t in titulos if t]) == 0


def test_recuperar_titulos_cargo_cjr_real_1_entrada_0_nao_vazias() -> None:
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    titulos = recuperar_titulos_cargo(paginas_cjr)
    assert len(titulos) == 1
    assert len([t for t in titulos if t]) == 0


def test_recuperar_titulos_cargo_invariante_paralelismo_ufgd_v7(
    paginas_ebserh_ufgd_v7: list[str],
) -> None:
    assert len(recuperar_titulos_cargo(paginas_ebserh_ufgd_v7)) == len(
        recortar_cards_cargo(paginas_ebserh_ufgd_v7)
    )


def test_recuperar_titulos_cargo_invariante_paralelismo_humap(
    paginas_ebserh_humap: list[str],
) -> None:
    assert len(recuperar_titulos_cargo(paginas_ebserh_humap)) == len(
        recortar_cards_cargo(paginas_ebserh_humap)
    )


def test_recuperar_titulos_cargo_invariante_paralelismo_cjr() -> None:
    paginas_cjr = extrair_texto_pgr(CAMINHO_PGR_CJR)
    assert len(recuperar_titulos_cargo(paginas_cjr)) == len(
        recortar_cards_cargo(paginas_cjr)
    )


# ---------------------------------------------------------------------------
# detectar_psicossocial (R-PSY-03) — marcadores medidos no Hetrin 14/09 (zero
# ocorrência) e Varandas Flamboyant 16/09 (presente); ver DT-(sessão não
# numerada, branch claude/youthful-lamport-3kfkog)-01 em PENDENCIAS_CLINICAS.md
# ---------------------------------------------------------------------------


def test_detectar_psicossocial_ausente_sem_marcador() -> None:
    # Reversão que mata: `return True` fixo em detectar_psicossocial.
    paginas = ["PGR CONSTRUTORA HETRIN\nQUEDAS DE ALTURA\nCinto paraquedista"]
    assert detectar_psicossocial(paginas) is False


@pytest.mark.parametrize(
    "marcador",
    [
        "Inventário de Riscos Psicossociais",
        "COPSOQ",
        "FRPRT",
    ],
)
def test_detectar_psicossocial_presente_por_marcador(marcador: str) -> None:
    # Reversão que mata: remover o marcador de _MARCADORES_PSICOSSOCIAL.
    paginas = ["Texto de abertura do PGR", f"Seção — {marcador} — inventário"]
    assert detectar_psicossocial(paginas) is True


def test_detectar_psicossocial_case_insensitive() -> None:
    # Cabeçalho em caixa alta (mesma classe de variação do bug Hetrin/parser
    # AIHA) não pode apagar o sinal.
    paginas = ["INVENTÁRIO DE RISCOS PSICOSSOCIAIS"]
    assert detectar_psicossocial(paginas) is True


def test_detectar_psicossocial_marcador_na_segunda_pagina() -> None:
    # Reversão que mata: checar só paginas[0] em vez de varrer a lista inteira.
    paginas = ["Página de abertura, sem marcador", "FRPRT aparece só aqui"]
    assert detectar_psicossocial(paginas) is True


def test_detectar_psicossocial_paginas_vazias() -> None:
    assert detectar_psicossocial(["", "", ""]) is False
