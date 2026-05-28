"""Fixture do PGR Viverde — caso de teste âncora do motor.

Fonte: docs/MAPA_GHE_VIVERDE.md (32 GHEs declarados pela CMO Residencial
Viverde Areião SPE LTDA, PGR V02 de 03.02.2025, Rev. 10/01/2025).

Decisões de modelagem: 1-12 (sessões 002.L1 partes 1 e 2 — ver HISTORICO).

Convenção de quantificação (MAPA linhas 9-15):
- Ruído com dB(A): valor + unidade, classificação por relacao_LT (string).
- Químico em mg/m³ ou ppm: valor + unidade, pct_LT=None (pendência conversão
  mg/m³→%LEO é problema do Stage subsequente, não do fixture).
- Altura, esforço, acidente, eletricidade, umidade, microrganismos, dermatite,
  queimadura, postura, espaço_confinado, radiação UV-IR: quantificacao=None.
- Adm-03 ruído aguardando medição (decisão 5): apenas_qualitativa=True,
  todos os campos numéricos None — Stage 4 deve gerar Ausente bloqueante.

Tipo do RiscoPGR (NR-09):
- fisico: ruido, trabalho_altura, eletricidade, umidade, radiacao_uv_ir
- quimico: todos os químicos + dermatite_contato + quimico_nao_especificado
- biologico: microrganismos
- ergonomico: esforco_fisico, movimento_repetitivo, postura_inadequada
- acidente: espaco_confinado, queda_de_materiais, piso_escorregadio,
  acidente_disco_corte, acidente_perfurocortante, queimadura_termica
"""
from __future__ import annotations

from datetime import date

from agente_medico.motor.tipos import GHEPGR, PGR, Quantificacao, RiscoPGR


def _ruido(valor_dB: float) -> Quantificacao:
    """Convenção NR-15: <80 abaixo da ação; 80-84 acima da ação; >=85 acima do LT.

    Pendência aberta: validar grafia exata de relacao_LT contra predicados.py
    quando Stage 4 consumir este fixture.
    """
    if valor_dB < 80:
        rel = "abaixo_acao"
    elif valor_dB < 85:
        rel = "acima_acao"
    else:
        rel = "acima_LT"
    return Quantificacao(
        valor=valor_dB,
        unidade="dB(A)",
        relacao_LT=rel,
        pct_LT=None,
        apenas_qualitativa=False,
    )


def _quimico_mgm3(valor: float) -> Quantificacao:
    return Quantificacao(
        valor=valor,
        unidade="mg/m3",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
    )


def _quimico_ppm(valor: float) -> Quantificacao:
    return Quantificacao(
        valor=valor,
        unidade="ppm",
        relacao_LT=None,
        pct_LT=None,
        apenas_qualitativa=False,
    )


_RUIDO_AGUARDANDO_MEDICAO = Quantificacao(
    valor=None,
    unidade=None,
    relacao_LT=None,
    pct_LT=None,
    apenas_qualitativa=True,
)


def build_pgr_viverde() -> PGR:
    """Constrói o PGR Viverde V02 (03.02.2025) conforme docs/MAPA_GHE_VIVERDE.md.

    32 GHEs canônicos: 16 Estrutura + 9 Acabamento + 6 Admin + 1 Fundação.
    Numeração CMO preservada (Est-01b existe; Est-15 não existe — salto declarado).
    """
    return PGR(
        validade=date(2025, 1, 10),
        assinatura_engenheiro=True,
        ghes=_ghes_estrutura() + _ghes_acabamento() + _ghes_admin_fundacao(),
    )


def _ghes_estrutura() -> tuple[GHEPGR, ...]:
    return (
        GHEPGR(
            id="Est-01",
            nome="Estrutura de concreto armado (carpinteiro)",
            cargos=("carpinteiro", "meio_oficial_carpinteiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(82.2), severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.163), severidade=None),
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="acidente_disco_corte", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="acidente_perfurocortante", quantificacao=None, severidade=None),
            ),
            epis=(
                "protetor auditivo NRRsf>=15",
                "respirador PFF2",
                "cinto/linha de vida",
                "botina antiperfurante",
                "avental raspa",
                "protetor facial",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-01b",
            nome="Estrutura de concreto armado (armador)",
            cargos=("armador", "meio_oficial_armador", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
            ),
            epis=("cinto/linha de vida",),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-02",
            nome="Preparação argamassa (betoneira)",
            cargos=("operador_betoneira", "servente"),
            riscos=(
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="umidade", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(89.6), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
            ),
            epis=(
                "protetor auditivo NRRsf>=15",
                "respirador 5N11",
                "luvas/avental/bota PVC",
                "óculos",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-03",
            nome="Montagem/manutenção elevador cremalheira e grua",
            cargos=("eletricista_industrial", "mecanico_de_manutencao", "eletricista"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(72.4), severidade=None),
                RiscoPGR(tipo="fisico", agente="eletricidade", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="propanediamina_tridecyloxy", quantificacao=None, severidade=None),  # decisão 12
            ),
            epis=(
                "respirador PFF3 SL",
                "luvas químicas",
                "creme protetor",
                "cinto/linha de vida",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-04",
            nome="Operação elevador cremalheira",
            cargos=("operador_elevador_cremalheira", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(79.2), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
            ),
            epis=("protetor auditivo NRRsf>=15",),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-05",
            nome="Içamento de materiais (grua)",
            cargos=("sinaleiro", "servente"),
            riscos=(
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(77.5), severidade=None),
            ),
            epis=("protetor auditivo", "cinto/linha de vida"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-06",
            nome="Alvenaria",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(78.8), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.735), severidade=None),
            ),
            epis=(
                "protetor auditivo NRRsf>=15",
                "respirador PFF2 (uso voluntário)",
                "luvas impermeáveis",
                "óculos",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-07",
            nome="Prumada elétrica / instalação elétrico-telefônica (desenergizada)",
            cargos=("eletricista", "meio_oficial_eletricista", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(82.8), severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.376), severidade=None),
                RiscoPGR(tipo="quimico", agente="silica", quantificacao=_quimico_mgm3(0.0071), severidade=None),
                RiscoPGR(tipo="acidente", agente="acidente_disco_corte", quantificacao=None, severidade=None),
            ),
            epis=("PFF2", "cinto/linha de vida"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-08",
            nome="Tubulação parede/teto / instalação hidro-sanitária",
            cargos=("encanador", "meio_oficial_encanador", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(83.3), severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.202), severidade=None),
                RiscoPGR(tipo="quimico", agente="metil_etil_cetona", quantificacao=_quimico_ppm(10.1), severidade=None),
            ),
            epis=("PFF2", "luvas nítrica", "óculos"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-09",
            nome="Solda / serralheria",
            cargos=("serralheiro", "meio_oficial_serralheiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(88.7), severidade=None),
                RiscoPGR(tipo="fisico", agente="radiacao_uv_ir", quantificacao=None, severidade=None),  # decisão 8
                RiscoPGR(tipo="quimico", agente="dioxido_de_titanio", quantificacao=_quimico_mgm3(0.008), severidade=None),
                RiscoPGR(tipo="acidente", agente="acidente_disco_corte", quantificacao=None, severidade=None),
            ),
            epis=(
                "máscara automática de solda",
                "respirador semifacial filtro 2078 P95",
                "luvas vaqueta",
                "avental vaqueta",
                "protetor solar FPS60",
                "cinto/linha de vida",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-10",
            nome="Limpeza (área de vivência)",
            cargos=("servente",),
            riscos=(
                RiscoPGR(tipo="acidente", agente="piso_escorregadio", quantificacao=None, severidade=None),
                RiscoPGR(tipo="biologico", agente="microrganismos", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="quimico_nao_especificado", quantificacao=None, severidade=None),  # decisão 12
            ),
            epis=(
                "luvas látex",
                "avental PVC",
                "bota PVC",
                "PFF2",
                "protetor auditivo NRRsf>=6",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-11",
            nome="Serviços gerais",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.735), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(71.6), severidade=None),
            ),
            epis=(
                "cinto/linha de vida",
                "óculos",
                "luvas nítrica",
                "PFF2",
                "protetor auditivo NRRsf>=10",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-12",
            nome="Pintura (peças metálicas, estrutura)",
            cargos=("pintor", "meio_oficial_pintor", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(78.8), severidade=None),
                RiscoPGR(tipo="quimico", agente="etanol", quantificacao=_quimico_ppm(4.4), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
            ),
            epis=(
                "respirador semifacial cartucho vapores orgânicos",
                "óculos",
                "luvas PVC",
                "protetor auditivo NRRsf>=10",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-13",
            nome="Portaria",
            cargos=("porteiro", "vigia"),
            riscos=(
                RiscoPGR(tipo="acidente", agente="piso_escorregadio", quantificacao=None, severidade=None),
            ),
            epis=("calçado antiderrapante",),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-14",
            nome="Operação de grua",
            cargos=("operador_grua",),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
            ),
            epis=("cinto/linha de vida", "óculos", "luvas nítrica"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Est-16",
            nome="Instalação elétrica temporária (energizada)",
            cargos=("eletricista",),
            riscos=(
                RiscoPGR(tipo="fisico", agente="eletricidade", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
            ),
            epis=("cinto/linha de vida", "óculos", "luvas nítrica"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
    )


def _ghes_acabamento() -> tuple[GHEPGR, ...]:
    return (
        GHEPGR(
            id="Acab-01",
            nome="Reboco interno e externo",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="dermatite_contato", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(78.8), severidade=None),
            ),
            epis=("protetor auditivo NRRsf>=8", "luvas impermeáveis"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-02",
            nome="Contrapiso",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.088), severidade=None),
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="umidade", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(76.5), severidade=None),
            ),
            epis=("protetor auditivo NRRsf>=8", "bota PVC", "luvas impermeáveis"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-03",
            nome="Impermeabilização cristalizante",
            cargos=("servente",),
            riscos=(
                RiscoPGR(tipo="quimico", agente="quimico_nao_especificado", quantificacao=None, severidade=None),  # decisão 12
            ),
            epis=(
                "respirador semifacial cartucho vapores orgânicos",
                "óculos",
                "luvas PVC",
            ),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-04",
            nome="Gesso corrido e placa",
            cargos=("gesseiro", "meio_oficial_gesseiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(0.08), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(73.6), severidade=None),
            ),
            epis=("PFF2", "óculos", "luvas PVC", "protetor auditivo NRRsf>=8"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-05",
            nome="Pintura interna e externa",
            cargos=("pintor", "meio_oficial_pintor", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="dermatite_contato", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(21.94), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(78.8), severidade=None),
                RiscoPGR(tipo="quimico", agente="silica", quantificacao=_quimico_mgm3(0.0050), severidade=None),
            ),
            epis=("PFF2", "óculos", "luvas PVC", "protetor auditivo NRRsf>=8"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-06",
            nome="Revestimento / assentamento de cerâmica",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="acidente_disco_corte", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(78.3), severidade=None),
                RiscoPGR(tipo="quimico", agente="silica", quantificacao=_quimico_mgm3(0.0050), severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(1.27), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
            ),
            epis=("PFF2", "óculos", "luvas PVC", "protetor auditivo NRRsf>=8"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-07",
            nome="Rejunte e limpeza grossa e fina",
            cargos=("servente",),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="piso_escorregadio", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="cloreto_de_hidrogenio", quantificacao=_quimico_ppm(0.01), severidade=None),
                RiscoPGR(tipo="quimico", agente="dermatite_contato", quantificacao=None, severidade=None),
            ),
            epis=("PFF2", "óculos", "luvas/avental/bota PVC"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-08",
            nome="Assentamento de bancada",
            cargos=("pedreiro", "meio_oficial_pedreiro", "servente"),
            riscos=(
                RiscoPGR(tipo="acidente", agente="acidente_disco_corte", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(89.3), severidade=None),
                RiscoPGR(tipo="quimico", agente="poeira_nao_classificada", quantificacao=_quimico_mgm3(1.4), severidade=None),
                RiscoPGR(tipo="quimico", agente="estireno", quantificacao=_quimico_ppm(1.7), severidade=None),
                RiscoPGR(tipo="ergonomico", agente="esforco_fisico", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="silica", quantificacao=_quimico_mgm3(0.005), severidade=None),
            ),
            epis=("PFF2", "óculos", "luvas", "protetor auditivo NRRsf>=17"),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Acab-09",
            nome="Impermeabilização manta asfáltica",
            cargos=("encarregado", "aplicador_de_asfalto", "servente"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="queimadura_termica", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="monoxido_de_carbono", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="espaco_confinado", quantificacao=None, severidade=None),
                RiscoPGR(tipo="quimico", agente="quimico_nao_especificado", quantificacao=None, severidade=None),  # decisão 12
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(75.9), severidade=None),
            ),
            epis=(
                "respirador semifacial cartucho gases + filtro 5N11",
                "óculos",
                "luvas vaqueta cano longo",
                "extintor",
            ),
            produtos_quimicos=(),
            psicossocial=True,
        ),
    )


def _ghes_admin_fundacao() -> tuple[GHEPGR, ...]:
    return (
        GHEPGR(
            id="Adm-01",
            nome="Engenharia / planejamento de obra",
            cargos=("engenheiro", "estagiario"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="postura_inadequada", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(65.1), severidade=None),
            ),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Adm-02",
            nome="Segurança do trabalho",
            cargos=("tecnico_de_seguranca", "estagiario"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="postura_inadequada", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_ruido(65.1), severidade=None),
            ),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Adm-03",
            nome="Mestre de obra / execução de obra",
            cargos=("mestre_de_obra", "encarregado"),
            riscos=(
                RiscoPGR(tipo="fisico", agente="trabalho_altura", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="postura_inadequada", quantificacao=None, severidade=None),
                RiscoPGR(tipo="fisico", agente="ruido", quantificacao=_RUIDO_AGUARDANDO_MEDICAO, severidade=None),  # decisão 5
            ),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Adm-04",
            nome="Supervisão rejunte/limpeza",
            cargos=("encarregado",),
            riscos=(
                RiscoPGR(tipo="acidente", agente="piso_escorregadio", quantificacao=None, severidade=None),
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
            ),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Adm-05",
            nome="Administrativo",
            cargos=("administrativo", "auxiliar_administrativo", "jovem_aprendiz"),
            riscos=(
                RiscoPGR(tipo="acidente", agente="queda_de_materiais", quantificacao=None, severidade=None),
                RiscoPGR(tipo="ergonomico", agente="movimento_repetitivo", quantificacao=None, severidade=None),
            ),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="Adm-06",
            nome="Almoxarifado",
            cargos=("almoxarife", "servente"),
            riscos=(),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
        GHEPGR(
            id="GHE-FUN",
            nome="Fundação",
            cargos=(
                "operador_retroescavadeira",
                "operador_escavadeira",
                "motorista",
                "operador_perfuratriz",
            ),
            riscos=(),
            epis=(),
            produtos_quimicos=(),
            psicossocial=False,
        ),
    )
