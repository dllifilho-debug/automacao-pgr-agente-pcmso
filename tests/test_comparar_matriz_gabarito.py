"""Testes do instrumento de comparação motor × gabarito — cada teste carrega,
junto, a reversão que deve deixá-lo vermelho.

Todos usam dado sintético com a forma medida no acervo. Nenhum abre PDF nem
converte `.doc`: o custo de reparse (`DH-003EC-02`) não entra aqui, e o que estes
testes protegem é a lógica de pareamento e classificação, não a extração.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.comparar_matriz_gabarito import (
    ConversaoIndisponivel,
    comparar,
    converter_para_docx,
    extrair_motor,
    gerar_relatorio,
    linhas_escopo,
    normalizar_cargo,
    resolver_slug,
)
from scripts.medir_cobertura_e_forma import FormaPeriodicidade, extrair_forma_periodicidade

# `exames.yaml` mapeia nome_exibicao → slug; aqui só o recorte que os testes usam.
MAPA = {
    "glicemia de jejum": "glicemia",
    "rx torax oit": "rx_torax_oit",
    "avaliacao psicossocial": "avaliacao_psicossocial",
    "exame clinico": "exame_clinico",
}


@dataclass(frozen=True)
class _Momento:
    name: str


@dataclass(frozen=True)
class _Emitido:
    exame: str
    periodicidade_meses: int | None
    momentos: frozenset[_Momento]


def _emitido(slug: str, meses: int | None, *momentos: str) -> _Emitido:
    return _Emitido(slug, meses, frozenset(_Momento(m) for m in momentos))


def _forma(slug: str, meses: int | None, *momentos: str) -> FormaPeriodicidade:
    return FormaPeriodicidade(slug, slug, meses, "inline", frozenset(_Momento(m) for m in momentos))


def test_anotacao_manuscrita_colada_ao_cargo_nao_impede_pareamento() -> None:
    """R1 — apagar `_ANOTACAO_COLADA` de `normalizar_cargo` mata este teste.

    Duas formas medidas no gabarito do SPE 0030: hífen
    (`Operador de Betoneiro- veja com a Segurança...`) e parêntese
    (`Encanador (Incluir no word do PCMSO...)`). Sem o corte, o cargo não pareia e
    a divergência aparece como cargo ausente, que é falso.
    """
    assert normalizar_cargo("Operador de Betoneiro- veja com a Segurança, acho que é betoneira.") == (
        "operador de betoneiro"
    )
    assert normalizar_cargo(
        "Aprendiz Administrativo de Obra- Incluir no WORD do PCMSI idade maior ou igual 18 anos."
    ) == "aprendiz administrativo de obra"
    assert normalizar_cargo("Encanador (Incluir no word do PCMSO, risco baixo)") == "encanador"
    assert normalizar_cargo("  Pedreiro  ") == "pedreiro"


def test_rotulo_de_momento_vazado_no_nome_ainda_resolve_slug() -> None:
    """R2 — apagar `_MOMENTO_NO_NOME` de `resolver_slug` mata este teste.

    O gabarito traz `Avaliação Psicossocial ADM, PER, MRO)` sem o parêntese de
    abertura, em todas as linhas. Sem a limpeza o nome não casa slug e a célula
    vira superemissão e subemissão falsas, uma por cargo.
    """
    bruta = extrair_forma_periodicidade("Avaliação Psicossocial ADM, PER, MRO)", MAPA)
    assert bruta.exame != "avaliacao_psicossocial", "premissa do teste mudou: já resolvia sozinho"
    assert resolver_slug(bruta, MAPA).exame == "avaliacao_psicossocial"


def test_grafia_divergente_do_gabarito_resolve_para_o_mesmo_slug() -> None:
    """R3 — apagar `_ALIAS_GRAFIA` mata este teste.

    `DT-003EO-02`: divergência de forma de saída, não decisão clínica. Se cair no
    nome cru, `Glicemia em Jejum` e `Glicemia de Jejum` viram exames diferentes.
    """
    for grafia, slug in (
        ("Glicemia em Jejum (ADM, PER)", "glicemia"),
        ("RX de Tórax OIT (ADM, PER 12 meses)", "rx_torax_oit"),
    ):
        bruta = extrair_forma_periodicidade(grafia, MAPA)
        assert resolver_slug(bruta, MAPA).exame == slug, grafia


def test_periodicidade_divergente_e_classificada() -> None:
    """R4 — apagar o ramo de `forma.meses != meses_motor` em `comparar` mata este
    teste. É a camada que a medição de 28/08 declarou NÃO cobrir, porque o app
    ainda não imprimia o número — só passou a imprimir em `deed9f6`."""
    motor = {"pedreiro": {"rx_torax_oit": _emitido("rx_torax_oit", 24, "ADM", "PER")}}
    gabarito = {"pedreiro": {"rx_torax_oit": _forma("rx_torax_oit", 12, "ADM", "PER")}}
    c = comparar(motor, gabarito)
    assert len(c.divergencia_periodicidade) == 1
    assert "24M" in c.divergencia_periodicidade[0].detalhe
    assert "12M" in c.divergencia_periodicidade[0].detalhe
    assert not c.superemissao and not c.subemissao


def test_momento_divergente_e_classificado_separado_da_identidade() -> None:
    """R5 — apagar o ramo de `mm != mg` em `comparar` mata este teste. Exame
    presente nos dois lados com conjunto de momentos diferente não é
    superemissão nem subemissão: é terceira classe."""
    motor = {"serralheiro": {"acuidade_visual": _emitido("acuidade_visual", 12, "ADM", "PER")}}
    gabarito = {"serralheiro": {"acuidade_visual": _forma("acuidade_visual", 12, "ADM", "PER", "DEM")}}
    c = comparar(motor, gabarito)
    assert len(c.divergencia_momentos) == 1
    assert not c.superemissao and not c.subemissao
    assert c.cargos_identicos == 1


def test_pareamento_zerado_vira_alerta_e_nao_relatorio_limpo() -> None:
    """R6 — apagar a guarda `if not pareados` em `comparar` mata este teste.

    Sem ela, pareamento quebrado produz `0 superemissão, 0 subemissão`, que lê
    como acervo perfeito. Mesma classe do "pasta inexistente produz relatório de
    zero arquivos parecendo limpo" de 003.FJ.
    """
    c = comparar({"pedreiro": {}}, {"encanador": {}})
    assert c.alertas, "pareamento zerado passou em silêncio"
    assert not c.cargos_pareados


def test_conversao_sem_saida_levanta_falha_nomeada(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R7 — apagar a checagem `if not convertido.exists()` de
    `converter_para_docx` mata este teste. Sem ela a função devolve um caminho
    que não existe e o erro aparece lá na frente, no `Document()`, sem nomear a
    causa (falta do filtro Writer do LibreOffice)."""
    origem = tmp_path / "gabarito.doc"
    origem.write_bytes(b"nao importa, o soffice e simulado")
    monkeypatch.setattr(
        "scripts.comparar_matriz_gabarito.shutil.which", lambda _nome: "/usr/bin/soffice"
    )
    monkeypatch.setattr(
        "scripts.comparar_matriz_gabarito.subprocess.run",
        lambda *_a, **_k: None,  # roda e não produz saída
    )
    with pytest.raises(ConversaoIndisponivel, match="conversao_sem_saida"):
        converter_para_docx(origem, tmp_path / "saida")


def test_relatorio_carrega_o_escopo_de_cada_numero() -> None:
    """R8 — apagar qualquer linha de `linhas_escopo` mata este teste.

    Invariante de saída herdada de 003.FJ: todo número que o instrumento imprime
    carrega, na mesma linha, o escopo que o produziu. Número solto em relatório
    de medição foi a raiz das rejeições de 003.FI.
    """
    motor = {"pedreiro": {"exame_clinico": _emitido("exame_clinico", 12, "ADM")}}
    gabarito = {"pedreiro": {"exame_clinico": _forma("exame_clinico", 12, "ADM")}}
    c = comparar(motor, gabarito)
    texto = "\n".join(linhas_escopo(c))
    for termo in ("cargos", "células", "idêntico", "superemissão", "subemissão", "periodicidade"):
        assert termo in texto, f"escopo ausente para {termo!r}"
    assert "cargo × exame" in texto, "unidade da contagem de células não declarada"

    relatorio = gerar_relatorio(c, Path("pgr.pdf"), Path("gabarito.doc"))
    assert "pgr.pdf" in relatorio and "gabarito.doc" in relatorio


def test_grafia_lombo_sacra_sem_hifen_resolve_slug() -> None:
    """R — apagar a entrada "rx de coluna lombo sacra" de `_ALIAS_GRAFIA` mata
    este teste. Grafia do gabarito Porto Araras 1 (06.07.26); sem o alias, 1
    superemissão + 1 subemissão falsas no operador de cremalheira."""
    mapa = {"rx coluna lombo-sacra": "rx_coluna_lombo_sacra"}
    bruta = extrair_forma_periodicidade("RX de Coluna Lombo Sacra (ADM, PER, MRO)", mapa)
    assert resolver_slug(bruta, mapa).exame == "rx_coluna_lombo_sacra"


def test_cargo_em_dois_ghes_nao_sobrescreve_a_primeira_ocorrencia() -> None:
    """R — voltar `extrair_motor` a um dict chaveado só pelo cargo (última
    ocorrência sobrescreve) mata este teste. Medido em Porto Araras I:
    `estagiário` em ADMINISTRAÇÃO e em SESMT, 7 subemissões falsas."""
    administracao = SimpleNamespace(
        linhas=(SimpleNamespace(exame="exame_clinico"),), cargos=("Estagiário",)
    )
    sesmt = SimpleNamespace(
        linhas=(SimpleNamespace(exame="exame_clinico"), SimpleNamespace(exame="audiometria")),
        cargos=("Estagiário",),
    )
    motor = extrair_motor([administracao, sesmt])  # type: ignore[list-item]
    assert set(motor) == {"estagiário [1/2]", "estagiário [2/2]"}
    assert set(motor["estagiário [1/2]"]) == {"exame_clinico"}
    assert set(motor["estagiário [2/2]"]) == {"exame_clinico", "audiometria"}

