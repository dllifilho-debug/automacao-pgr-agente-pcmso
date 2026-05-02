"""
Automacao SST - Seconci GO
app.py v9.3 — fix: preserva cargos do parser_pgr ao montar dados_ghe_raw
               v9.2 — login visual: fundo verde escuro, card branco, st.form (Enter submete),
               logo acima do form + rodapé de versão
               v5.27 fix: enriquecer_ghe_com_banco só processa GHEs com cargos reais
               v5.26 fix: _distribuir_cargos_por_ghe chamada corretamente no caminho parser_pgr
               v5.25 fix: sidebar sempre visível via CSS (força translateX(0))
               header oculto mas toggle preservado
               v5.24 initial_sidebar_state=expanded
               v5.23 ghe_mapper Supabase
               v5.22 detecção correta GHE sem cargo
"""
import json
import os
import re
import traceback
from datetime import date

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

from config.db import (
    get_supabase,
    salvar_historico,
    carregar_historico,
    carregar_html_historico,
)
from modules.modulo_pcmso import (
    extrair_texto_pdf,
    extrair_pgr_com_fallback,
    enriquecer_pgr_com_fispq,
    processar_pcmso,
    gerar_html_pcmso,
    gerar_docx_rq61,
    _distribuir_cargos_por_ghe,
    _coletar_cargos_globais,
)

st.set_page_config(
    page_title="Automacao SST - Seconci GO",
    layout="wide",
    page_icon=":shield:",
    initial_sidebar_state="expanded",
)

# ── CSS CUSTOMIZADO ────────────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  .block-container{padding-top:1.4rem;padding-bottom:2rem;max-width:1400px;}
  #MainMenu {visibility: hidden;}
  footer    {visibility: hidden;}
  /* NÃO ocultar header para preservar toggle da sidebar */
  header    {visibility: hidden; height: 0; min-height: 0;}

  /* ── SIDEBAR SEMPRE VISÍVEL ── */
  [data-testid="stSidebar"] {
    transform: translateX(0) !important;
    min-width: 14rem !important;
    width: 14rem !important;
    display: block !important;
    visibility: visible !important;
  }
  [data-testid="stSidebar"] > div:first-child {
    width: 14rem !important;
  }
  /* Botão de toggle da sidebar - garante visibilidade */
  [data-testid="collapsedControl"] {
    display: none !important;
  }

  [data-testid="stAppViewContainer"]{background:#F0F2F5;}
  [data-testid="stSidebar"]{background:#F7F9FB !important;border-right:1px solid #E4E8EE;}
  [data-testid="stSidebar"] *{color:#1A1D23;}
  [data-testid="stFileUploadDropzone"]{border:2px dashed #1AA04B;border-radius:16px;background:#FBFFFC;padding:1rem;}
  .stButton>button{background:linear-gradient(135deg,#084D22,#0E6B31);color:white;border-radius:10px;border:none;box-shadow:0 8px 18px rgba(8,77,34,.16);transition:all .2s ease;font-weight:700;padding:.62rem 1rem;}
  .stButton>button:hover{background:linear-gradient(135deg,#0E6B31,#1AA04B);transform:translateY(-1px);}
  .stDownloadButton>button{border-radius:10px;font-weight:700;}
  h1,h2,h3{color:#084D22!important;letter-spacing:-0.02em;}
  .stAlert{border-radius:12px;border:1px solid #E6EBF1;box-shadow:0 4px 10px rgba(15,23,42,.04);}
  .kaiju-card{background:#FFFFFF;border:1px solid #E6EBF1;border-radius:18px;padding:1.2rem 1.2rem;box-shadow:0 10px 30px rgba(15,23,42,.06);margin-bottom:1rem;}
  .kaiju-card-title{font-size:.92rem;font-weight:700;color:#5B6472;text-transform:uppercase;letter-spacing:.04em;margin-bottom:.35rem;}
  .kaiju-hero{background:linear-gradient(135deg,#084D22 0%,#1AA04B 100%);border-radius:22px;padding:1.3rem 1.4rem;color:white;box-shadow:0 18px 40px rgba(8,77,34,.20);margin-bottom:1rem;}
  .kaiju-hero h2{color:white!important;margin:0 0 .25rem 0;}
  .kaiju-hero p{margin:0;opacity:.96;font-size:0.98rem;}
  div[data-testid="metric-container"] {
    background-color: #ffffff;
    border: 1px solid #e0e0e0;
    padding: 15px;
    border-radius: 8px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
    border-left: 5px solid #084D22;
  }
  div[data-testid="metric-container"] label{font-weight:700;color:#5B6472;}
  div[data-testid="stDataFrame"] {
    border-radius: 8px;
    box-shadow: 2px 2px 10px rgba(0,0,0,0.05);
  }
  .audit-panel{background:#FFFFFF;border:1px solid #E6EBF1;border-radius:18px;padding:1rem 1.1rem;box-shadow:0 10px 28px rgba(15,23,42,.05);}
  .stTabs [data-baseweb="tab-list"]{gap:.5rem;}
  .stTabs [data-baseweb="tab"]{background:#EAF3ED;border-radius:10px;padding:.55rem .95rem;font-weight:700;}
  .stTabs [aria-selected="true"]{background:#084D22!important;color:white!important;}
</style>
""", unsafe_allow_html=True)


def card_inicio(titulo: str, texto: str):
    st.markdown(
        f"""
        <div class="kaiju-card">
            <div class="kaiju-card-title">{titulo}</div>
            <div>{texto}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_auditoria_metrics(resultado_auditoria: dict):
    total = int(resultado_auditoria.get("total_divergencias", 0))
    faltando = len(resultado_auditoria.get("exames_faltando", []))
    excedente = len(resultado_auditoria.get("exames_excedentes", []))
    cargo_faltando = len(resultado_auditoria.get("cargo_faltando", []))

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Divergencias", total)
    c2.metric("Exames faltando", faltando)
    c3.metric("Exames excedentes", excedente)
    c4.metric("Cargos sem match", cargo_faltando)


def _extrair_nome_cargo(nome_secao: str) -> str:
    m = re.match(
        r'^CARGO\s+(.+?)(?:\s*[-–]\s*CBO[:\s]*\d+)?\s*$',
        nome_secao.strip(),
        re.IGNORECASE,
    )
    return m.group(1).strip() if m else nome_secao.strip()


_RE_NOME_GHE = re.compile(r'^GHE\s*\d+', re.IGNORECASE)

def _cargos_sao_apenas_ghe_names(cargos: list) -> bool:
    if not cargos:
        return True
    return all(_RE_NOME_GHE.match(c.strip()) for c in cargos)


def _normalizar_dados_ghe_para_auditor(dados_ghe):
    """
    Normaliza dados_ghe para o formato de lista de dicionários esperado pelo auditor.

    IMPORTANTE (v9.3): se o item já vier com 'cargos' preenchidos (lista não-vazia
    de cargos reais), preserva esses cargos em vez de derivar do nome da seção.
    Isso garante que os cargos extraídos pelo parser_pgr via SETOR/FUNCAO não
    sejam descartados.
    """
    if isinstance(dados_ghe, list):
        for ghe in dados_ghe:
            riscos_raw = ghe.get('riscos_mapeados', [])
            ghe['riscos_mapeados'] = [
                r if isinstance(r, dict) else {'nome_agente': str(r), 'perigo_especifico': ''}
                for r in riscos_raw
            ]
        return dados_ghe

    resultado = []
    for nome_secao, info in dados_ghe.items():
        riscos_raw = info.get('riscos', [])
        riscos_mapeados = [
            r if isinstance(r, dict) else {'nome_agente': str(r), 'perigo_especifico': ''}
            for r in riscos_raw
        ]

        # v9.3 FIX: usa cargos já extraídos pelo parser_pgr se disponíveis e reais;
        # só deriva do nome_secao como fallback quando não há cargos reais.
        cargos_raw = info.get('cargos', [])
        if cargos_raw and not _cargos_sao_apenas_ghe_names(cargos_raw):
            cargos = cargos_raw
        else:
            nome_cargo = _extrair_nome_cargo(nome_secao)
            cargos = [nome_cargo]

        resultado.append({
            'ghe': nome_secao,
            'cargos': cargos,
            'riscos_mapeados': riscos_mapeados,
            'exames': info.get('exames', []),
        })
    return resultado


# ── Autenticacao ──────────────────────────────────────────────────────────────────────────────
def check_password():
    if st.session_state.get("autenticado", False):
        return True

    # CSS exclusivo da tela de login — sobrepõe o CSS global acima
    st.markdown("""
    <style>
      /* Fundo escuro com gradiente de marca */
      [data-testid="stAppViewContainer"] {
        background: linear-gradient(150deg, #021608 0%, #053d18 55%, #0a6629 100%) !important;
        min-height: 100vh;
      }
      /* Oculta sidebar na tela de login */
      [data-testid="stSidebar"] { display: none !important; }
      /* Remove padding lateral padrão do Streamlit */
      .block-container { padding-top: 3rem !important; max-width: 480px !important; margin: 0 auto !important; }
      /* Card branco do formulário via stForm */
      [data-testid="stForm"] {
        background: #FFFFFF;
        border-radius: 24px;
        padding: 2.4rem 2rem 2rem !important;
        box-shadow: 0 40px 100px rgba(0,0,0,.45);
        margin-top: .5rem;
      }
      /* Inputs com foco verde */
      [data-testid="stForm"] input:focus {
        border-color: #084D22 !important;
        box-shadow: 0 0 0 3px rgba(8,77,34,.12) !important;
      }
      /* Botão de submit no card */
      [data-testid="stForm"] .stButton > button,
      [data-testid="stForm"] [data-testid="stFormSubmitButton"] > button {
        background: linear-gradient(135deg, #084D22, #0E6B31) !important;
        color: white !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        margin-top: .6rem;
        box-shadow: 0 8px 18px rgba(8,77,34,.25) !important;
      }
      /* Rodapé de versão */
      .login-footer {
        text-align: center;
        color: rgba(255,255,255,.40);
        font-size: 0.76rem;
        margin-top: 1.4rem;
        letter-spacing: .03em;
      }
      /* Logo / ícone acima do card */
      .login-header {
        text-align: center;
        margin-bottom: 1rem;
      }
      .login-header h3 {
        color: white !important;
        font-size: 1.1rem;
        font-weight: 600;
        margin: .5rem 0 0;
        letter-spacing: .06em;
        opacity: .85;
      }
    </style>
    """, unsafe_allow_html=True)

    # Logo ou ícone acima do card
    for logo in ("logo.png", "logo.jpg"):
        if os.path.exists(logo):
            st.image(logo, width=140)
            break
    else:
        st.markdown(
            "<div class='login-header'>"
            "<span style='font-size:3rem;'>🛡️</span>"
            "<h3>SECONCI GO</h3>"
            "</div>",
            unsafe_allow_html=True,
        )

    # Formulário — Enter submete automaticamente
    with st.form("login_form"):
        st.markdown(
            "<h3 style='text-align:center;color:#084D22;margin:0 0 1.2rem;font-size:1.25rem;'>"
            "Entrar no Sistema</h3>",
            unsafe_allow_html=True,
        )
        usr = st.text_input("Usuário", key="username_input")
        pwd = st.text_input("Senha", type="password", key="password_input")
        submitted = st.form_submit_button("Entrar", use_container_width=True)

    if submitted:
        usr_correto = st.secrets.get("USUARIO_SISTEMA", "diovanni")
        pwd_correta = st.secrets.get("SENHA_SISTEMA", "seconci123")
        if usr == usr_correto and pwd == pwd_correta:
            st.session_state["autenticado"] = True
            st.rerun()
        else:
            st.session_state["autenticado"] = False

    if "autenticado" in st.session_state and not st.session_state["autenticado"]:
        st.error("Usuário ou senha incorretos.")

    st.markdown(
        "<div class='login-footer'>"
        "Sistema SST Seconci GO &nbsp;·&nbsp; v9.3 &nbsp;·&nbsp; Acesso monitorado"
        "</div>",
        unsafe_allow_html=True,
    )

    return False


if not check_password():
    st.stop()


# ── Sidebar ──────────────────────────────────────────────────────────────────────────────
for logo in ("logo.png", "logo.jpg"):
    if os.path.exists(logo):
        st.sidebar.image(logo, width=220)
        break
else:
    st.sidebar.markdown(
        "<h2 style='text-align:center;color:#084D22;'>SECONCI-GO</h2>",
        unsafe_allow_html=True,
    )

st.sidebar.markdown("---")
st.sidebar.title("Modulos do Sistema")
modulo = st.sidebar.radio(
    "Selecione a funcionalidade:",
    [
        "Dashboard",
        "Engenharia: FISPQ / FDS - PGR",
        "Medicina: PGR - PCMSO",
        "Construtor Visual de GHEs",
    ],
)

st.sidebar.markdown("---")
if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state["autenticado"] = False
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.title("Historico de Laudos")
historico = carregar_historico()
historico_html = None

if historico:
    opcoes = ["Selecione um projeto salvo..."] + [
        f"{r['id']} - {r['nome_projeto']} ({r['data_salvamento']})"
        for r in historico
    ]
    sel = st.sidebar.selectbox("Carregar projeto:", opcoes)
    if sel != "Selecione um projeto salvo...":
        id_sel = int(sel.split(" - ")[0])
        historico_html = carregar_html_historico(id_sel)
        if historico_html:
            st.sidebar.success("Projeto carregado.")
else:
    st.sidebar.write("Nenhum projeto salvo ainda.")


# ── Banco de matrizes ─────────────────────────────────────────────────────────────────────────────────
banco_path = os.path.join("data", "banco_matrizes_v1_1.json")
banco_matrizes = {}

if os.path.exists(banco_path):
    try:
        with open(banco_path, "r", encoding="utf-8") as f:
            banco_matrizes = json.load(f)
    except Exception as e:
        st.sidebar.warning(f"Banco de matrizes nao carregado: {e}")

_banco_ativo = bool(banco_matrizes)


# ── Roteamento ─────────────────────────────────────────────────────────────────────────────────
if historico_html:
    st.title("Laudo Carregado do Historico")
    components.html(historico_html, height=700, scrolling=True)

elif modulo == "Dashboard":
    st.title("Dashboard - Sistema Integrado SST")
    try:
        sb = get_supabase()
        total     = sb.table("historico_laudos").select("id", count="exact").execute().count or 0
        total_cas = sb.table("dicionario_dinamico").select("cas", count="exact").execute().count or 0
    except Exception:
        total, total_cas = 0, 0
    c1, c2, c3 = st.columns(3)
    c1.metric("Laudos Gerados", total)
    c2.metric("CAS no Banco Dinamico", total_cas)
    c3.metric("Modulos Ativos", 4)
    st.info("Use o menu lateral para acessar os modulos.")

elif modulo == "Engenharia: FISPQ / FDS - PGR":
    try:
        from modules.modulo_engenharia import render_engenharia
        render_engenharia()
    except ImportError:
        st.warning("modulo_engenharia.py nao encontrado.")

elif modulo == "Construtor Visual de GHEs":
    try:
        from modules.modulo_construtor_visual import render_construtor_visual
        render_construtor_visual()
    except Exception as e:
        st.error(f"❌ Erro no Construtor Visual: {type(e).__name__}: {e}")
        st.code(traceback.format_exc(), language="python")

elif modulo == "Medicina: PGR - PCMSO":
    st.markdown("""
        <div class="kaiju-hero">
            <h2>🩺 Módulo Médico — Importador de PGR e Gerador de PCMSO</h2>
            <p>Fluxo guiado em 3 etapas: upload e extração, auditoria clínica e aprovação final.</p>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs([
        "📂 Passo 1: Upload e Extração",
        "🔍 Passo 2: Conferência de Cargos",
        "✅ Passo 3: Aprovação e Download",
    ])

    with tab1:
        card_inicio(
            "Motor de extração",
            "parser_pgr v2: detecta automaticamente formato GHE ou CARGO/CBO. "
            "Fallback para IA Gemini somente se necessario.",
        )

        fispq_carregados = st.session_state.get("fispq_resultados_medicos", [])
        if fispq_carregados:
            st.success(
                f"🧪 {len(fispq_carregados)} agente(s) da FISPQ em memoria — serão injetados automaticamente no PCMSO apos a extracao."
            )

        if _banco_ativo:
            st.info(
                "📚 Banco de matrizes tecnicas ativo — os exames de cada cargo serao preenchidos "
                "automaticamente com base no padrao validado, **independente do nome do arquivo**."
            )

        with st.container():
            st.markdown("<div class='kaiju-card'>", unsafe_allow_html=True)
            st.markdown("### Dados de Identificacao do PCMSO")
            st.caption("NR-07 item 7.5.19.1")
            col1, col2 = st.columns(2)
            cab = st.session_state.get("pcmso_cabecalho", {})
            with col1:
                razao_social = st.text_input("Razao Social da Empresa *", value=cab.get("razao_social", ""))
                cnpj = st.text_input("CNPJ *", value=cab.get("cnpj", ""))
                medico_rt = st.text_input("Medico Responsavel RT (Nome + CRM) *", value=cab.get("medico_rt", ""))
            with col2:
                vig_ini = st.date_input("Vigencia - Inicio", value=date.today())
                vig_fim = st.date_input("Vigencia - Fim", value=date.today())
                resp_tec = st.text_input("Tecnico SST Responsavel (opcional)", value=cab.get("responsavel_tec", ""))
                obra = st.text_input("Obra / Unidade (opcional)", value=cab.get("obra", ""))
            st.markdown("---")
            st.markdown("**Tipo de Ambiente da Obra** *(define o pacote de exames)*")
            opcoes_amb = {
                "🏗️ Canteiro de Obras / Obra": "canteiro",
                "🏢 Escritório Corporativo": "escritorio",
                "🔀 Misto (Canteiro + Escritório no mesmo PGR)": "misto",
            }
            label_amb = st.radio(
                "Selecione o tipo:",
                list(opcoes_amb.keys()),
                index=1,
                horizontal=True,
            )
            tipo_ambiente = opcoes_amb[label_amb]
            st.markdown("</div>", unsafe_allow_html=True)

        st.session_state["pcmso_cabecalho"] = {
            "razao_social": razao_social,
            "cnpj": cnpj,
            "medico_rt": medico_rt,
            "vig_ini": vig_ini.strftime("%d/%m/%Y"),
            "vig_fim": vig_fim.strftime("%d/%m/%Y"),
            "responsavel_tec": resp_tec,
            "obra": obra,
        }
        st.session_state["tipo_ambiente"] = tipo_ambiente

        st.markdown("<div class='kaiju-card'>", unsafe_allow_html=True)
        pdf_file = st.file_uploader("Arraste o PDF do PGR aqui", type=["pdf"])
        if pdf_file:
            st.session_state["nome_pdf_atual"] = pdf_file.name

        def _marcar_extracao():
            st.session_state["_executar_extracao"] = True

        st.button(
            "Extrair Riscos e Gerar PCMSO",
            use_container_width=True,
            on_click=_marcar_extracao,
        )
        st.markdown("</div>", unsafe_allow_html=True)

        if st.session_state.pop("_executar_extracao", False):
            if not pdf_file:
                st.error("Faca upload do PDF do PGR antes de continuar.")
                st.stop()

            with st.spinner("Extraindo texto do PDF..."):
                texto_pgr = extrair_texto_pdf(pdf_file)
            st.success(f"Texto extraido: {len(texto_pgr):,} caracteres em {pdf_file.name}")

            with st.expander("DEBUG: Primeiras 100 linhas do PDF"):
                for i, linha in enumerate(texto_pgr.split("\n")[:100], 1):
                    st.text(f"{i:3}: {linha}")

            with st.spinner("Identificando GHEs / Cargos e riscos..."):
                _resultado_pgr = None
                try:
                    from parser_pgr import parsear_pgr as _parsear_pgr
                    pdf_file.seek(0)
                    _resultado_pgr = _parsear_pgr(pdf_file.read(), regras={})
                except Exception as _e_parser:
                    st.warning(
                        f"⚠️ parser_pgr falhou ({type(_e_parser).__name__}: {_e_parser}) — "
                        "usando fallback local."
                    )

            if _resultado_pgr and _resultado_pgr.get("ghe_blocos"):
                _fmt    = _resultado_pgr["formato"]
                _n_sec  = len(_resultado_pgr["ghe_blocos"])
                _metodo = _resultado_pgr["metodo_extracao"]
                st.success(
                    f"✅ Formato detectado: **{_fmt}** | "
                    f"**{_n_sec}** seções encontradas | "
                    f"Extração: **{_metodo}**"
                )
                if _resultado_pgr.get("aviso"):
                    st.warning(_resultado_pgr["aviso"])

                # ── v9.3 FIX ──────────────────────────────────────────────────────
                # O parser_pgr já extrai cargos reais via SETOR/FUNCAO e os devolve
                # em ghe_blocos[nome]["cargos"]. Incluímos essa chave no raw dict
                # para que _normalizar_dados_ghe_para_auditor os preserve em vez de
                # derivar o cargo a partir do nome genérico do GHE.
                # ──────────────────────────────────────────────────────────────────
                dados_ghe_raw = {}
                for _nome_sec, _info in _resultado_pgr["ghe_blocos"].items():
                    dados_ghe_raw[_nome_sec] = {
                        "cargo":  _nome_sec,
                        "cargos": _info.get("cargos", []),   # ← NOVO: preserva cargos reais
                        "riscos": _info["riscos_identificados"],
                        "exames": [_e["exame"] if isinstance(_e, dict) else str(_e)
                                   for _e in _info.get("exames_gerados", [])],
                    }
                dados_ghe = _normalizar_dados_ghe_para_auditor(dados_ghe_raw)
                fonte = "local"

                # Conta quantos GHEs ainda ficaram sem cargo real após a normalização
                _ghe_sem_cargo_real = [
                    g for g in dados_ghe
                    if _cargos_sao_apenas_ghe_names(g.get("cargos", []))
                ]

                if _ghe_sem_cargo_real:
                    # Fallback: tenta coletar cargos globais da seção FUNÇÕES do PDF
                    try:
                        _cargos_globais = _coletar_cargos_globais(texto_pgr.split("\n"))
                        if _cargos_globais:
                            _distribuir_cargos_por_ghe(_cargos_globais, _ghe_sem_cargo_real)
                            n_dist = sum(len(g.get("cargos", [])) for g in _ghe_sem_cargo_real)
                            st.info(
                                f"ℹ️ {len(_cargos_globais)} cargo(s) reais coletados da seção FUNÇÕES "
                                f"e distribuídos por tipo para {len(_ghe_sem_cargo_real)} GHE(s) "
                                f"({n_dist} atribuições no total)."
                            )
                        else:
                            st.warning("⚠️ Seção FUNÇÕES não encontrada no PDF — tentando Supabase...")
                    except Exception as _e_inj:
                        st.warning(f"⚠️ Injeção de cargos reais falhou: {_e_inj}")
                else:
                    # Todos os GHEs já vieram com cargos reais do parser_pgr ✅
                    _n_cargos_total = sum(len(g.get("cargos", [])) for g in dados_ghe)
                    st.info(
                        f"✅ {_n_cargos_total} cargo(s) reais extraídos diretamente pelo parser_pgr "
                        f"via campo SETOR/FUNCAO — nenhuma distribuição necessária."
                    )

            else:
                st.info("🔁 parser_pgr nao encontrou secoes — usando pipeline local (extrair_pgr_local)...")
                _dados_list, fonte = extrair_pgr_com_fallback(texto_pgr)
                dados_ghe = _normalizar_dados_ghe_para_auditor(_dados_list)

            # ── Supabase ghe_mapper (fallback para GHEs ainda sem cargo real) ──
            _ghe_ainda_sem_cargo = [
                g for g in dados_ghe
                if _cargos_sao_apenas_ghe_names(g.get("cargos", []))
            ]
            if _ghe_ainda_sem_cargo:
                try:
                    from utils.ghe_mapper import carregar_mapeamentos, buscar_match as _buscar_match_ghe
                    _mapeamentos_sb = carregar_mapeamentos()
                    if _mapeamentos_sb:
                        _matches_ok = 0
                        _sem_match = []
                        for _ghe in _ghe_ainda_sem_cargo:
                            _desc = _ghe.get("ghe", "")
                            _desc_clean = re.split(r'GHE\s*\d+[-–\s]+', _desc, maxsplit=1, flags=re.IGNORECASE)
                            _desc_clean = _desc_clean[-1].strip() if len(_desc_clean) > 1 else _desc
                            _match = _buscar_match_ghe(_desc_clean, _mapeamentos_sb)
                            if _match and _match.get("cargos"):
                                _ghe["cargos"] = _match["cargos"]
                                _matches_ok += 1
                            else:
                                _sem_match.append(_desc_clean)
                        if _matches_ok:
                            st.success(f"✅ {_matches_ok} GHE(s) enriquecido(s) com cargos reais do Supabase!")
                        if _sem_match:
                            st.warning(
                                f"⚠️ {len(_sem_match)} GHE(s) sem match no Supabase — "
                                f"exames gerados pela matriz interna: {', '.join(_sem_match)}"
                            )
                    else:
                        st.info("ℹ️ ghe_mapper: tabela Supabase vazia ou indisponível — usando matriz interna.")
                except Exception as _e_mapper:
                    st.warning(f"⚠️ ghe_mapper indisponível: {_e_mapper}")

            st.session_state["dados_ghe_processados"] = dados_ghe

            if fonte == "local":
                st.success("Dados extraidos localmente — sem consumo de IA!")
            elif fonte == "ia":
                st.info("Dados extraidos via IA (Gemini).")
            else:
                st.warning("Extracao parcial — revise os resultados.")

            if not dados_ghe:
                st.error("Nenhum GHE / Cargo identificado. Verifique se o PDF e um PGR valido.")
                st.stop()

            resultados_fispq = st.session_state.get("fispq_resultados_medicos", [])
            if resultados_fispq:
                st.success(f"🧪 {len(resultados_fispq)} Agente(s) Químico(s) da FISPQ detectados! Injetando no PGR...")
                dados_ghe = enriquecer_pgr_com_fispq(dados_ghe, resultados_fispq)

            rel_banco = None
            if _banco_ativo:
                from modules.modulo_auditor_v1_1 import enriquecer_ghe_com_banco
                with st.spinner("Aplicando padrao tecnico de exames por cargo..."):
                    # Apenas GHEs que já têm cargos reais confirmados recebem
                    # enriquecimento pelo banco; os demais usam a matriz interna
                    # para não sobrescrever exames com pacotes genéricos.
                    _ghe_com_cargo_real = [
                        g for g in dados_ghe
                        if not _cargos_sao_apenas_ghe_names(g.get("cargos", []))
                    ]
                    _ghe_sem_cargo_final = [
                        g for g in dados_ghe
                        if _cargos_sao_apenas_ghe_names(g.get("cargos", []))
                    ]
                    if _ghe_com_cargo_real:
                        _enriquecidos, rel_banco = enriquecer_ghe_com_banco(_ghe_com_cargo_real, banco_matrizes)
                        dados_ghe = _enriquecidos + _ghe_sem_cargo_final
                    else:
                        rel_banco = {"cargos_enriquecidos": [], "cargos_mantidos": [], "mapa_exames_banco": {}}

                n_enr = len(rel_banco['cargos_enriquecidos'])
                n_man = len(rel_banco['cargos_mantidos'])
                if n_enr:
                    st.success(
                        f"✅ {n_enr} cargo(s) preenchidos com padrao tecnico do banco: "
                        f"{', '.join(dict.fromkeys(rel_banco['cargos_enriquecidos']))}"
                    )
                if n_man:
                    st.warning(
                        f"⚠️ {n_man} cargo(s) nao encontrados no banco — exames gerados pela matriz interna: "
                        f"{', '.join(dict.fromkeys(rel_banco['cargos_mantidos']))}"
                    )

            tipo_amb = st.session_state.get("tipo_ambiente", "escritorio")
            with st.spinner(f"Gerando matriz PCMSO ({tipo_amb})..."):
                try:
                    df_pcmso = processar_pcmso(dados_ghe, tipo_ambiente=tipo_amb)
                except Exception as e:
                    st.error(f"❌ Erro em processar_pcmso(): {type(e).__name__}: {e}")
                    st.code(traceback.format_exc(), language="python")
                    st.stop()

            if df_pcmso.empty:
                st.warning("PCMSO gerado vazio — nenhum cargo/exame identificado.")
                st.stop()

            st.success(f"PCMSO gerado com {len(df_pcmso)} linhas de exames. Revise no Passo 2.")
            st.session_state["df_pcmso_gerado"] = df_pcmso
            st.session_state["relatorio_banco"] = rel_banco
            st.session_state.pop("med_xml_s2240_bytes", None)

    with tab2:
        st.markdown("<div class='audit-panel'>", unsafe_allow_html=True)
        st.markdown("### Conferência de Cargos e Exames")

        rel_banco = st.session_state.get("relatorio_banco")
        if rel_banco:
            enr = list(dict.fromkeys(rel_banco.get('cargos_enriquecidos', [])))
            man = list(dict.fromkeys(rel_banco.get('cargos_mantidos', [])))
            c1, c2 = st.columns(2)
            c1.metric("✅ Cargos com padrao tecnico aplicado", len(enr))
            c2.metric("⚠️ Cargos sem match no banco", len(man))
            if enr:
                with st.expander("Cargos preenchidos pelo banco de matrizes", expanded=True):
                    for c in enr:
                        st.markdown(f"- ✅ {c}")
            if man:
                with st.expander("Cargos sem match (exames gerados pela matriz interna)"):
                    for c in man:
                        st.markdown(f"- ⚠️ {c} — considere adicionar ao banco de matrizes")
        elif "df_pcmso_gerado" in st.session_state:
            st.info("Matriz gerada sem banco de matrizes ativo. Revise os exames manualmente no Passo 3.")
        else:
            st.info("Extraia um PGR no Passo 1 para preencher este painel.")
        st.markdown("</div>", unsafe_allow_html=True)

    with tab3:
        st.markdown("<div class='kaiju-card'>", unsafe_allow_html=True)
        st.markdown("### Aprovacao e Download")
        if "df_pcmso_gerado" in st.session_state:
            st.info(
                "Revise a matriz abaixo. Voce pode corrigir nomes, alterar periodicidades, "
                "marcar ou desmarcar ADM/PER/DEM, excluir linhas e adicionar novos exames."
            )

            df_atual = st.session_state["df_pcmso_gerado"].copy()
            total_linhas = len(df_atual)
            colunas_df = list(df_atual.columns)

            with st.expander("➕ Inserir nova linha em posicao especifica", expanded=False):
                st.caption(f"Matriz tem {total_linhas} linha(s). A nova linha sera inserida ANTES da posicao escolhida (1 = inicio, {total_linhas + 1} = final).")
                col_pos, col_ghe_n, col_cargo_n, col_exame_n = st.columns([1, 2, 2, 3])
                with col_pos:
                    pos_inserir = st.number_input(
                        "Posicao",
                        min_value=1,
                        max_value=total_linhas + 1,
                        value=total_linhas + 1,
                        step=1,
                        key="ins_posicao",
                    )
                with col_ghe_n:
                    ghe_opcoes = list(df_atual["GHE / Setor"].unique()) if "GHE / Setor" in df_atual.columns else []
                    ghe_novo = st.selectbox("GHE / Setor", options=ghe_opcoes + ["-- Novo --"], key="ins_ghe")
                    if ghe_novo == "-- Novo --":
                        ghe_novo = st.text_input("Nome do GHE", key="ins_ghe_custom")
                with col_cargo_n:
                    cargo_opcoes = list(df_atual["Cargo"].unique()) if "Cargo" in df_atual.columns else []
                    cargo_novo = st.selectbox("Cargo", options=cargo_opcoes + ["-- Novo --"], key="ins_cargo")
                    if cargo_novo == "-- Novo --":
                        cargo_novo = st.text_input("Nome do Cargo", key="ins_cargo_custom")
                with col_exame_n:
                    exame_novo = st.text_input("Exame", key="ins_exame")

                col_adm_n, col_per_n, col_mro_n, col_rt_n, col_dem_n, col_just_n = st.columns(6)
                adm_novo  = col_adm_n.selectbox("ADM",  ["-", "X"], key="ins_adm")
                per_novo  = col_per_n.text_input("PER",  value="12M", key="ins_per")
                mro_novo  = col_mro_n.selectbox("MRO",  ["X", "-"], key="ins_mro")
                rt_novo   = col_rt_n.selectbox("RT",   ["-", "X"], key="ins_rt")
                dem_novo  = col_dem_n.selectbox("DEM",  ["-", "X"], key="ins_dem")
                just_novo = col_just_n.text_input("Justificativa", value="Inserido manualmente", key="ins_just")

                if st.button("➕ Confirmar insercao", key="btn_inserir_linha", use_container_width=True):
                    if not exame_novo.strip():
                        st.warning("Informe o nome do exame antes de inserir.")
                    else:
                        nova_linha = {
                            "GHE / Setor": ghe_novo or "",
                            "Cargo": cargo_novo or "",
                            "Exame": exame_novo.strip(),
                            "ADM": adm_novo,
                            "PER": per_novo.upper().strip(),
                            "MRO": mro_novo,
                            "RT": rt_novo,
                            "DEM": dem_novo,
                            "Justificativa": just_novo,
                        }
                        for col in colunas_df:
                            if col not in nova_linha:
                                nova_linha[col] = ""

                        idx = int(pos_inserir) - 1
                        parte_antes = df_atual.iloc[:idx]
                        parte_depois = df_atual.iloc[idx:]
                        df_inserida = pd.concat(
                            [parte_antes, pd.DataFrame([nova_linha]), parte_depois],
                            ignore_index=True,
                        )
                        st.session_state["df_pcmso_gerado"] = df_inserida
                        st.success(f"✅ Linha inserida na posicao {int(pos_inserir)}: {exame_novo} — {cargo_novo}")
                        st.rerun()

            df_editado = st.data_editor(
                st.session_state["df_pcmso_gerado"],
                num_rows="dynamic",
                use_container_width=True,
                key="editor_matriz_pcmso",
                height=500,
            )

            if not df_editado.equals(st.session_state["df_pcmso_gerado"]):
                st.session_state["df_pcmso_gerado"] = df_editado

            st.markdown("---")

            if st.button("✅ Aprovar Matriz e Gerar Documentos", type="primary", use_container_width=True):
                cabecalho_atual = st.session_state["pcmso_cabecalho"]
                razao_social_ap = cabecalho_atual.get("razao_social", "")
                medico_rt_ap    = cabecalho_atual.get("medico_rt", "")
                with st.spinner("Consolidando correcoes e gerando laudos oficiais..."):
                    try:
                        html_pcmso = gerar_html_pcmso(df_editado, cabecalho=cabecalho_atual)
                        bytes_docx = gerar_docx_rq61(df_editado, cabecalho=cabecalho_atual)
                    except Exception as e:
                        st.error(f"❌ Erro na geracao dos documentos: {type(e).__name__}: {e}")
                        st.code(traceback.format_exc(), language="python")
                        st.stop()

                st.session_state["html_pcmso_aprovado"] = html_pcmso
                st.session_state["bytes_docx_aprovado"] = bytes_docx
                st.session_state["nome_arq_aprovado"] = (
                    razao_social_ap.replace(" ", "_")[:30] if razao_social_ap else "PCMSO"
                )

                if razao_social_ap and medico_rt_ap:
                    nome_proj = f"PCMSO - {razao_social_ap[:40]} ({date.today().strftime('%d/%m/%Y')})"
                    salvar_historico(nome_proj, html_pcmso)
                    st.success("✅ Laudo aprovado e salvo no historico com sucesso!")
                else:
                    st.warning("Preencha Razao Social e Medico RT para salvar no historico.")

            if "html_pcmso_aprovado" in st.session_state:
                nome_arq = st.session_state.get("nome_arq_aprovado", "PCMSO")
                st.markdown("### ⬇️ Documentos Prontos para Download")
                col_html, col_docx = st.columns(2)
                with col_html:
                    st.download_button(
                        label="📄 Baixar PCMSO (.html)",
                        data=st.session_state["html_pcmso_aprovado"].encode("utf-8"),
                        file_name=f"PCMSO_{nome_arq}.html",
                        mime="text/html",
                        use_container_width=True,
                    )
                with col_docx:
                    st.download_button(
                        label="📝 Baixar PCMSO (.docx)",
                        data=st.session_state["bytes_docx_aprovado"],
                        file_name=f"PCMSO_{nome_arq}.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                    )
                with st.expander("👁️ Preview do PCMSO gerado", expanded=False):
                    components.html(st.session_state["html_pcmso_aprovado"], height=600, scrolling=True)

            from modules.modulo_esocial_xml import render_botao_xml
            render_botao_xml(
                df_editado,
                st.session_state.get("pcmso_cabecalho", {}),
                dados_pgr=st.session_state.get("dados_ghe_processados"),
                key_prefix="med",
            )

        else:
            st.info("A matriz aprovada aparecera aqui apos a extracao do Passo 1.")
        st.markdown("</div>", unsafe_allow_html=True)
