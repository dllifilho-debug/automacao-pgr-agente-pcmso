from __future__ import annotations

from pathlib import Path

import pytest

from agente_medico.motor.protocolo import carregar


PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"


def test_vocabulario_exames_carrega_com_slugs_esperados() -> None:
    # Teste-guardião: adição de slug ao vocabulário é deliberada — atualizar
    # este conjunto é o comportamento pretendido (não afrouxar para superconjunto).
    p = carregar(PROTOCOLO_DIR)
    assert set(p.vocabulario.exames.keys()) == {
        "exame_clinico",
        "avaliacao_psicossocial", "avaliacao_saude_mental",
        "hemograma", "glicemia", "audiometria", "acuidade_visual", "ecg",
        "rx_coluna_lombo_sacra", "rx_torax_oit", "espirometria",
        "reticulocitos", "acido_transmuconico",
        "acetona_urina", "arsenio_urina", "ttca_urina",
        "acido_mandelico_fenilglioxilico", "mercurio_urina", "mek_urina",
        "carboxihemoglobina", "hexanodiona_urina", "ortocresol_urina",
        "acido_tricloroacetico", "acido_metilhipurico",
        "chumbo_sangue", "ala_urinario",
        "cadmio_urina", "fluoreto_urinario", "acetilcolinesterase_eritrocitaria",
        "cromo_urina", "cobalto_urina", "fenol_urina", "metanol_urina",
        "diclorometano_urina", "metahemoglobina_sangue",
        "dihidro_acetilcisteina_butano_urina", "hexametilenodiamina_urina",
        "acido_metoxiacetico_urina", "toluenodiamino_urina",
        "acido_butoxiacetico_urina", "chumbo_urina", "ciclohexanol_urina",
        "clorocatecol_urina", "acido_etoxiacetico_urina", "acido_furoico_urina",
        "mibk_urina", "hidroxi_metil_pirrolidona_urina", "metilacetamida_urina",
        "metilformamida_urina", "aduto_hev_hemoglobina",
        "tetracloroetileno_sangue", "tetrahidrofurano_urina",
    }


def test_todo_exame_tem_nome_exibicao_e_categoria() -> None:
    p = carregar(PROTOCOLO_DIR)
    categorias_validas = {"clinico", "ocupacional", "laboratorial", "imagem"}
    for slug, meta in p.vocabulario.exames.items():
        assert isinstance(meta, dict), f"Meta de '{slug}' não é dict"
        assert meta.get("nome_exibicao", "").strip(), f"'{slug}' sem nome_exibicao"
        assert meta.get("categoria") in categorias_validas, (
            f"'{slug}' tem categoria inválida: {meta.get('categoria')}"
        )


def test_vocabulario_psicossocial_tem_nome_exibicao_byte_exato() -> None:
    # Grafia medida no gabarito (271/283 ocorrências pós-vigência NR-01 26/05/2026,
    # 003.EN). Reversão: alterar qualquer nome_exibicao ou remover uma das chaves.
    p = carregar(PROTOCOLO_DIR)
    exames = p.vocabulario.exames
    assert "avaliacao_psicossocial" in exames
    assert exames["avaliacao_psicossocial"]["nome_exibicao"] == "Avaliação Psicossocial"
    assert "avaliacao_saude_mental" in exames
    assert exames["avaliacao_saude_mental"]["nome_exibicao"] == "Av. Médica de Saúde Mental"


def test_regra_ativcrit_referencia_apenas_slugs_validos() -> None:
    p = carregar(PROTOCOLO_DIR)
    slugs = set(p.vocabulario.exames.keys())
    regra = next(r for r in p.regras if r["id"] == "R-PKG-ATIVCRIT")
    for item in regra["emite"]:
        assert item["exame"] in slugs, (
            f"Regra R-PKG-ATIVCRIT referencia slug inexistente: '{item['exame']}'"
        )


def test_vocabulario_agentes_inclui_solventes_fds_t65() -> None:
    p = carregar(PROTOCOLO_DIR)
    agentes = p.vocabulario.agentes
    for slug, cas in [("acetona", "67-64-1"), ("acetato_de_etila", "141-78-6")]:
        assert slug in agentes
        assert agentes[slug]["cas"] == cas
        assert agentes[slug]["is_carcinogeno_iarc"] is False


def test_carregar_falha_quando_regra_referencia_slug_inexistente(tmp_path: Path) -> None:
    """
    Cria um protocolo temporário com regra referenciando exame que não
    existe no vocabulário e verifica que carregar() levanta ValueError.
    """
    proto = tmp_path / "protocolo"
    (proto / "vocabulario").mkdir(parents=True)
    (proto / "vocabulario" / "exames.yaml").write_text(
        "exames:\n  hemograma:\n    nome_exibicao: Hemograma\n"
        "    categoria: laboratorial\n    fonte_matriz: teste\n",
        encoding="utf-8",
    )
    (proto / "vocabulario" / "agentes.yaml").write_text("agentes: {}\n", encoding="utf-8")
    (proto / "vocabulario" / "cargos.yaml").write_text("cargos: {}\n", encoding="utf-8")
    (proto / "vocabulario" / "epis.yaml").write_text("epis: {}\n", encoding="utf-8")
    (proto / "predicados_compostos.yaml").write_text(
        "predicados_compostos: {}\n", encoding="utf-8"
    )
    (proto / "regras.yaml").write_text(
        "regras:\n"
        "  - id: R-TESTE\n"
        "    quando: sempre\n"
        "    emite:\n"
        "      - {exame: exame_que_nao_existe, periodicidade_meses: 12, momentos: [adm]}\n"
        "    base_normativa: teste\n"
        "    status: VALIDADO\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        carregar(proto)

    msg = str(exc_info.value)
    assert "exame_que_nao_existe" in msg
    assert "R-TESTE" in msg
    assert "hemograma" in msg  # mostra os disponíveis


def test_carregar_aceita_vocabulario_vazio_se_nenhuma_regra_referencia_exame(tmp_path: Path) -> None:
    """
    Vocabulário vazio + regras sem campo 'emite' (ou emite vazio) deve carregar OK.
    Garante que a validação só dispara quando há referência real.
    """
    proto = tmp_path / "protocolo"
    (proto / "vocabulario").mkdir(parents=True)
    for nome, raiz in [("exames", "exames"), ("agentes", "agentes"),
                        ("cargos", "cargos"), ("epis", "epis")]:
        (proto / "vocabulario" / f"{nome}.yaml").write_text(
            f"{raiz}: {{}}\n", encoding="utf-8"
        )
    (proto / "predicados_compostos.yaml").write_text(
        "predicados_compostos: {}\n", encoding="utf-8"
    )
    (proto / "regras.yaml").write_text("regras: []\n", encoding="utf-8")

    p = carregar(proto)
    assert p.vocabulario.exames == {}
    assert p.regras == []
