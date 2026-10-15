"""Dados da empresa lidos do PGR para o PCMSO (D-ARQ-96, fatia 2). Cada teste nomeia a reversão que o deixa vermelho.

Os trechos são o texto que o pdfplumber extrai dos PGRs do acervo (medido em 15/10/2026), cortados ao bloco de
identificação.
"""

from __future__ import annotations

from pathlib import Path

from agente_medico.motor.identificacao_pgr import (
    cnpj_valido,
    ler_identificacao,
    ler_identificacao_pdf,
)

ACERVO = Path(__file__).resolve().parents[2] / "matrizes_originais"

# PGR — CMO AURORA, pág. 3: bloco do elaborador (Seconci) antes do bloco do cliente.
_CMO_AURORA = """2. DADOS DA EMPRESA ELABORADORA / RESPONSÁVEL TÉCNICO
CAMPO INFORMAÇÃO
Razão Social Serviço Social da Indústria da Construção no Estado de Goiás – SECONCI GO
CNPJ 36.863.637/0001-59
Endereço Rua C 136 Nº 681 Qd 3037 – Lotes 20 e 21 – Jardim América – Goiânia/GO
Telefone (62) 3250-7544
3. DADOS DO ESTABELECIMENTO / CLIENTE
CAMPO INFORMAÇÃO
Razão Social CMO RESIDENCIAL AURORA LAGO DAS ROSAS SPE LTDA
CNPJ 46.299.916/0001-95
Atividade Principal / CNA 4110-7/00 - Incorporação de empreendimentosimobiliários
Grau de Risco (GR) 3
Endereço Rua. R-5, Quadra R7, Lote 02/04-24 - Setor Oeste,Goiânia-GO
Horário de Trabalho Seg à Qui: 07h-17h | Sex: 07h-16h"""

# PGR_-_plateau Dor_assinado rev 03, pág. 3: endereço da empresa e da obra; CNPJ com vírgula no lugar do ponto.
_PLATEAU = """1. APRESENTAÇÃO
Razão Social: MAUÁ Participações Estruturadas LTDA
CNPJ: 02.689,014/0001-90
Endereço: Av. Jamel Cecílio, com rua 56 nº 2929 (Brookfild Towers)
Responsável pela empresa: Geraldo Magela da Silva e Alan de Alvarenga Menezes
CNAE: 41.20-4-00 - Construção de edifícios
Grau de Risco: 03
Obra: PLATEAU D’OR
Endereço: Avenida Parque Cidade, loteamento Plateau D‘or
Engenheiro responsável pela obra: Matheus Peixoto"""

# [PGR] Soft Connect15 v04, pág. 4: dois CNAEs, o "considerado para este" quebrado em duas linhas.
_SOFT_CONNECT = """4. IDENTIFICAÇÃO DO ESTABELECIMENTO / LOCALIZAÇÃO
Razão Social SERRINHA 201 DEL EMPREENDIMENTOS IMOBILIARIOS LTDA
CNPJ: 43.091.205/0001-32
Atividade Principal/CNAE : 41.10-7-00 - Incorporação de empreendimentos imobiliários
CNAE/Atividade secundária considerada para este: 41.20-4-00 - Construção
de edifícios
Grau de Risco: 3
Endereço: R. Córdoba, Quadra 250 - Lotes 16/19 - Parque Amazônia, Goiânia -
GO, 74835-030
Turno de segunda a segunda a Horas extras: Negociadas em casos de"""

# PGR - EURO Setor C, pág. 3: rótulo centralizado na célula — o valor sai metade acima, metade abaixo.
_EURO = """Obra: EUROPARK SETOR C
Avenida PL 3 com PL 2 e com PL 4 Quadra H5 Park
Endereço:
Lozandes. CEP- 74.884-115
Engenheiro responsável pela"""

# PGR_RICCO_2026_REV06, pág. 4: sumário com "GRAU DE RISCO" antes; CEP de cada endereço na linha de baixo.
_RICCO = """4.2 - EXIGÊNCIAS MÍNIMAS QUANTO AO GRAU DE RISCO 4
1 - IDENTIFICAÇÃO DA EMPRESA E DA OBRA
Empresa: Ricco Construtora Ltda.
CNPJ: 12.350.844/0001-41.
Atividade principal: Construção de edifícios.
CNAE: 41.20-4-00.
Grau de risco: 3.
Endereço Escritório: Al. Alcides de Araújo Romão, nº 1116, Qd. 63, Lt. 4, Loteamento Faiçalville, Goiânia – GO.
CEP: 74.350-030.
Telefone: (62) 3087-7333.
Endereço da obra: Rua Maria Pedro Jesus Q A, nº 281, Qd. 04, Lt. 10, Jardim Primavera, Trindade – GO.
CEP: 75.380-000.
Data de retomada da obra: 21/03/2025."""


def test_bloco_do_elaborador_nao_entra() -> None:
    # Reversão que mata: tirar a chamada a `_sem_bloco_elaborador` em `ler_identificacao` — o CNPJ e o endereço
    # do Seconci (elaborador) vêm primeiro e passam a ser os da empresa.
    r = ler_identificacao([_CMO_AURORA])
    assert r.cnpj == "46.299.916/0001-95"
    assert r.endereco.startswith("Rua. R-5")


def test_endereco_da_obra_e_o_do_pcmso_e_o_da_empresa_fica_como_alternativa() -> None:
    # Reversão que mata: escolher `enderecos[0]` em vez do primeiro marcado como da obra — sai o endereço do
    # escritório (Av. Jamel Cecílio). Decisão do Diovanni, 15/10/2026.
    r = ler_identificacao([_PLATEAU])
    assert r.endereco == "Avenida Parque Cidade, loteamento Plateau D‘or"
    assert r.endereco_alternativo.startswith("Av. Jamel Cecílio")


def test_cnpj_com_separador_trocado_sai_normalizado_e_valido() -> None:
    # Reversão que mata: devolver o CNPJ como achado, sem `_formatar_cnpj` — sai "02.689,014/0001-90".
    r = ler_identificacao([_PLATEAU])
    assert r.cnpj == "02.689.014/0001-90"
    assert r.cnpj_valido


def test_cnpj_com_digito_errado_e_marcado() -> None:
    # Reversão que mata: `cnpj_valido` sem a conferência dos dígitos (só o comprimento) — o CNPJ do PGR TPB
    # Andrade, com DV errado no próprio documento, passaria como válido.
    assert not cnpj_valido("50.055.341/0001-52")
    assert cnpj_valido("43.091.205/0001-32")


def test_cnae_considerado_para_o_pgr_vence_o_principal() -> None:
    # Reversão que mata: `escolhido = cnaes[0]` — sai 4110-7/00 (incorporação), o principal da empresa. Decisão do
    # Diovanni, 15/10/2026; o outro fica em `cnae_alternativo`.
    r = ler_identificacao([_SOFT_CONNECT])
    assert r.cnae == "4120-4/00"
    assert r.descricao_cnae == "Construção de edifícios"
    assert r.cnae_alternativo.startswith("4110-7/00")


def test_endereco_quebrado_em_duas_linhas_separa_cidade_uf_e_cep() -> None:
    # Reversão que mata: tirar o ramo de continuação de `_valor_do_rotulo` (só a linha do rótulo) — "GO, 74835-030"
    # fica de fora e saem sem UF e sem CEP.
    r = ler_identificacao([_SOFT_CONNECT])
    assert (r.endereco, r.cidade, r.uf, r.cep) == (
        "R. Córdoba, Quadra 250 - Lotes 16/19 - Parque Amazônia", "Goiânia", "GO", "74835-030"
    )


def test_rotulo_sozinho_junta_as_linhas_de_cima_e_de_baixo() -> None:
    # Reversão que mata: rótulo sem valor na linha devolver "" em `_valor_do_rotulo` — o endereço do EURO some.
    r = ler_identificacao([_EURO])
    assert r.endereco == "Avenida PL 3 com PL 2 e com PL 4 Quadra H5 Park Lozandes"
    assert r.cep == "74884-115"


def test_grau_de_risco_do_sumario_nao_conta() -> None:
    # Reversão que mata: tirar o `^` de `_GRAU` e usar `search` — o "4" do sumário (item 4.2) vira o grau.
    assert ler_identificacao([_RICCO]).grau_risco == "3"


def test_cep_da_linha_de_baixo_e_do_endereco_da_obra() -> None:
    # Reversão que mata: tirar o laço "O CEP na linha de baixo é deste endereço" — a obra fica sem CEP (e, sem a
    # trava de um endereço só, levaria o CEP do escritório, 74350-030).
    r = ler_identificacao([_RICCO])
    assert r.cidade == "Trindade"
    assert r.cep == "75380-000"


def test_estado_por_extenso_vira_uf() -> None:
    # Reversão que mata: tirar a chamada a `_estado_por_extenso` em `_separar_endereco` — "Goiânia - Goiás" sai
    # sem cidade e sem UF (PGR Vila Brasil).
    r = ler_identificacao(["Endereço: Avenida Deputado Jamel Cecilio, 2929, Jardim Goiás, Goiânia - Goiás"])
    assert (r.cidade, r.uf) == ("Goiânia", "GO")


def test_arquivo_que_nao_e_pdf_devolve_campos_vazios(tmp_path: Path) -> None:
    # Reversão que mata: tirar o try/except de `ler_identificacao_pdf` — a tela cai com exceção ao receber um PDF
    # ilegível, em vez de deixar os campos para preencher.
    falso = tmp_path / "pgr.pdf"
    falso.write_bytes(b"conteudo qualquer")
    r = ler_identificacao_pdf(falso)
    assert r.cnpj == r.endereco == r.cnae == ""


def test_pgr_plateau_real() -> None:
    # Reversão que mata: a mesma do teste do endereço da obra, agora sobre o PDF real do par Plateau ↔ PCMSO Mauá.
    r = ler_identificacao_pdf(ACERVO / "PGR_-_plateau Dor_assinado rev 03.pdf")
    assert (r.cnpj, r.cnae, r.grau_risco) == ("02.689.014/0001-90", "4120-4/00", "3")
    assert r.endereco == "Avenida Parque Cidade, loteamento Plateau D‘or"
