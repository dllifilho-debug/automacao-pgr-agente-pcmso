"""Camada visual do app da matriz — só apresentação, nenhuma regra.

Um único ponto de ajuste: `aplicar_estilos()` injeta o CSS abaixo e é chamado
pelos entrypoints logo após `st.set_page_config`. As cores base também vivem
em `.streamlit/config.toml` (tema nativo); aqui ficam só os acabamentos que o
tema não cobre (sombras, stepper, dropzone, faixa de cabeçalho).

Seletores, do mais ao menos estável:
- `.st-key-<key>`: classe que o Streamlit põe em todo container com `key=`;
  as keys usadas aqui estão em web_matriz.py e o teste
  `test_estilos_so_referenciam_keys_existentes` trava a correspondência.
- `[data-testid="st..."]`: API semi-pública, estável entre minors, mas já
  mudou em majors (ex.: `stVerticalBlockBorderWrapper` sumiu na 1.4x).
- Seletores marcados `FRÁGIL` dependem da estrutura interna do DOM (ordem de
  irmãos, tags geradas) e são os primeiros a conferir num upgrade.
"""

import streamlit as st

PRIMARIA = "#0F4C5C"
PRIMARIA_ESCURA = "#0A3742"
ACENTO = "#1B998B"
FUNDO = "#F5F7FA"
CARTAO = "#FFFFFF"
TEXTO = "#1A2B33"
TEXTO_SUAVE = "#5B6B73"
BORDA = "#E3E8EE"
SUCESSO = "#1E7B4F"
ALERTA = "#9A6200"
ERRO = "#B42318"

# Ícones (traço 2px, estilo Lucide) aplicados por CSS mask — herdam a cor do tema.
_ICONE_DOCUMENTO = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M14 2H6a2 2 0 0 0-2 2v16a2 2 "
    "0 0 0 2 2h12a2 2 0 0 0 2-2V8z'/><path d='M14 2v6h6'/><path d='M8 13h8M8 17h8M8 9h2'/></svg>"
)
_ICONE_FRASCO = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><path d='M9 2h6M10 2v6.5L4.5 18a2 2 0 "
    "0 0 1.7 3h11.6a2 2 0 0 0 1.7-3L14 8.5V2'/><path d='M7 15h10'/></svg>"
)
_ICONE_CONFERENCIA = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='8' y='2' width='8' height='4' "
    "rx='1'/><path d='M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2'/>"
    "<path d='m9 14 2 2 4-4'/></svg>"
)
_ICONE_MATRIZ = (
    "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='black' "
    "stroke-width='2' stroke-linecap='round' stroke-linejoin='round'><rect x='3' y='3' width='18' "
    "height='18' rx='2'/><path d='M3 9h18M3 15h18M9 3v18'/></svg>"
)


def _svg_url(svg: str) -> str:
    # Data-URI sem base64: aspas simples no SVG, só `#` e `<>` precisam de escape.
    return "url(\"data:image/svg+xml;utf8," + svg.replace("#", "%23").replace("<", "%3C").replace(">", "%3E") + "\")"


def _css() -> str:
    return f"""
<style>

:root {{
  --pcmso-primaria: {PRIMARIA};
  --pcmso-primaria-escura: {PRIMARIA_ESCURA};
  --pcmso-acento: {ACENTO};
  --pcmso-fundo: {FUNDO};
  --pcmso-cartao: {CARTAO};
  --pcmso-texto: {TEXTO};
  --pcmso-texto-suave: {TEXTO_SUAVE};
  --pcmso-borda: {BORDA};
  --pcmso-sucesso: {SUCESSO};
  --pcmso-alerta: {ALERTA};
  --pcmso-erro: {ERRO};
  --pcmso-raio: 12px;
  --pcmso-sombra: 0 1px 2px rgba(16, 40, 48, .06), 0 2px 8px rgba(16, 40, 48, .05);
  --pcmso-sombra-alta: 0 4px 14px rgba(15, 76, 92, .22);
}}

/* ---------- Base ---------- */
[data-testid="stMainBlockContainer"] {{
  max-width: 1240px;
  padding-top: 2.25rem;
  padding-bottom: 4rem;
}}
[data-testid="stMain"] h1, [data-testid="stMain"] h2,
[data-testid="stMain"] h3, [data-testid="stMain"] h4 {{
  letter-spacing: -0.01em;
  color: var(--pcmso-texto);
}}
/* O Streamlit põe opacity .6 na legenda: com o cinza do tema dá ~2,6:1. Cor sólida
   #5B6B73 sem transparência fica em ~5,6:1 sobre branco (WCAG AA). */
[data-testid="stCaptionContainer"] {{ opacity: 1; }}
[data-testid="stCaptionContainer"], [data-testid="stCaptionContainer"] p {{ color: var(--pcmso-texto-suave); }}

/* ---------- Faixa de cabeçalho ----------
   FRÁGIL: assume que o único h1 da página é o st.title (vale para a tela
   principal e para as telas do gate de acesso). */
[data-testid="stElementContainer"]:has(> [data-testid="stHeading"] h1) {{
  background: linear-gradient(120deg, var(--pcmso-primaria) 0%, #136170 55%, var(--pcmso-acento) 140%);
  border-radius: var(--pcmso-raio);
  padding: 1.35rem 1.75rem;
  box-shadow: var(--pcmso-sombra);
}}
[data-testid="stElementContainer"]:has(> [data-testid="stHeading"] h1) h1 {{
  color: #FFFFFF;
  font-weight: 700;
  font-size: clamp(1.5rem, 2.4vw, 2.1rem);
  padding: 0;
}}
/* Esconde o ícone de âncora (link) que o Streamlit põe ao lado do título. */
[data-testid="stElementContainer"]:has(> [data-testid="stHeading"] h1) [data-testid="stHeaderActionElements"] {{
  display: none;
}}
/* FRÁGIL: legenda logo abaixo do título (irmão adjacente). */
[data-testid="stElementContainer"]:has(> [data-testid="stHeading"] h1)
  + [data-testid="stElementContainer"] [data-testid="stCaptionContainer"] {{
  font-size: .95rem;
  max-width: 95ch;
  margin-top: -.25rem;
}}

/* ---------- Stepper (keys em web_matriz.py: indicador_etapas, passo_N_ESTADO) ---------- */
.st-key-indicador_etapas [data-testid="stHorizontalBlock"] {{ gap: .75rem; align-items: stretch; }}
/* Passos com a mesma altura mesmo quando um rótulo quebra linha ("(opcional)").
   FRÁGIL: assume stColumn > stVerticalBlock > stLayoutWrapper > passo (1.64). */
.st-key-indicador_etapas [data-testid="stLayoutWrapper"]:has(> [class*="st-key-passo_"]) {{ flex: 1 1 auto; }}
[class*="st-key-passo_"] {{
  background: var(--pcmso-cartao);
  border: 1px solid var(--pcmso-borda);
  border-top: 4px solid var(--pcmso-borda);
  border-radius: 10px;
  padding: .7rem .9rem;
  min-height: 3.4rem;
  justify-content: center;
  transition: border-color .2s ease, box-shadow .2s ease;
}}
[class*="st-key-passo_"] p {{ margin: 0; font-size: .92rem; color: var(--pcmso-texto-suave); }}
/* O Streamlit compensa a margem do parágrafo com margin-bottom -1rem no container;
   com o parágrafo zerado acima, a compensação faz o texto vazar da caixa. */
[class*="st-key-passo_"] [data-testid="stMarkdownContainer"] {{ margin-bottom: 0; }}
[class*="st-key-passo_"] strong {{ font-weight: 600; }}
[class*="st-key-passo_"][class*="_ativo"] {{
  border-top-color: var(--pcmso-primaria);
  box-shadow: 0 0 0 3px rgba(15, 76, 92, .10);
}}
[class*="st-key-passo_"][class*="_ativo"] p {{ color: var(--pcmso-primaria); }}
[class*="st-key-passo_"][class*="_concluido"] {{
  border-top-color: var(--pcmso-sucesso);
  background: #F1F9F5;
}}
[class*="st-key-passo_"][class*="_concluido"] p {{ color: var(--pcmso-sucesso); }}
[class*="st-key-passo_"][class*="_bloqueado"] {{
  border-top-color: var(--pcmso-erro);
  background: #FDF3F2;
}}
[class*="st-key-passo_"][class*="_bloqueado"] p {{ color: var(--pcmso-erro); }}
[class*="st-key-passo_"][class*="_opcional"] {{
  border-top-style: dashed;
  border-top-color: var(--pcmso-acento);
}}

/* ---------- Cards das etapas ---------- */
.st-key-etapa_pgr, .st-key-etapa_fds, .st-key-caixa_conferencia, .st-key-caixa_matriz {{
  background: var(--pcmso-cartao);
  border: 1px solid var(--pcmso-borda) !important;
  border-radius: var(--pcmso-raio) !important;
  box-shadow: var(--pcmso-sombra);
  padding: 1.25rem 1.5rem 1.5rem !important;
}}
/* FRÁGIL: o primeiro filho do card é o st.subheader da etapa. */
.st-key-etapa_pgr > div:first-child h3,
.st-key-etapa_fds > div:first-child h3,
.st-key-caixa_conferencia > div:first-child h3,
.st-key-caixa_matriz > div:first-child h3 {{
  display: flex;
  align-items: center;
  gap: .7rem;
  font-size: 1.2rem;
  font-weight: 600;
  padding-bottom: .65rem;
  border-bottom: 1px solid var(--pcmso-borda);
}}
.st-key-etapa_pgr > div:first-child h3::before,
.st-key-etapa_fds > div:first-child h3::before,
.st-key-caixa_conferencia > div:first-child h3::before,
.st-key-caixa_matriz > div:first-child h3::before {{
  content: "";
  flex: 0 0 2.1rem;
  height: 2.1rem;
  border-radius: 50%;
  background-color: var(--pcmso-primaria);
  background-image: var(--pcmso-icone);
  background-repeat: no-repeat;
  background-position: center;
  background-size: 1.1rem;
}}
.st-key-etapa_pgr {{ --pcmso-icone: {_svg_url(_ICONE_DOCUMENTO.replace("stroke='black'", "stroke='white'"))}; }}
.st-key-etapa_fds {{ --pcmso-icone: {_svg_url(_ICONE_FRASCO.replace("stroke='black'", "stroke='white'"))}; }}
.st-key-caixa_conferencia {{ --pcmso-icone: {_svg_url(_ICONE_CONFERENCIA.replace("stroke='black'", "stroke='white'"))}; }}
.st-key-caixa_matriz {{ --pcmso-icone: {_svg_url(_ICONE_MATRIZ.replace("stroke='black'", "stroke='white'"))}; }}
/* Subtítulos internos (GHEs, Revisão) ficam um degrau abaixo do cabeçalho do card. */
.st-key-caixa_matriz h3 {{ font-size: 1.05rem; }}

/* Subtítulos `####` dentro dos cards (ex.: "Produtos anexados") abaixo do cabeçalho. */
.st-key-etapa_fds h4, .st-key-caixa_conferencia h4, .st-key-caixa_matriz h4 {{
  font-size: 1rem;
  font-weight: 600;
  color: var(--pcmso-primaria);
}}

/* Etapas 3 e 4 ainda indisponíveis (sem o card interno): legenda vira card "fantasma". */
.st-key-etapa_conferencia:not(:has(.st-key-caixa_conferencia)) [data-testid="stCaptionContainer"],
.st-key-etapa_matriz:not(:has(.st-key-caixa_matriz)) [data-testid="stCaptionContainer"] {{
  border: 1.5px dashed #C9D3DC;
  border-radius: var(--pcmso-raio);
  padding: 1rem 1.25rem;
  background: rgba(255, 255, 255, .55);
  font-size: .95rem;
}}

/* ---------- Formulário ---------- */
[data-testid="stForm"] {{
  border: 1px solid var(--pcmso-borda);
  border-radius: 10px;
  background: #FAFBFC;
  padding: 1.25rem;
}}
[data-testid="stTextInputRootElement"] {{
  border-radius: 8px;
  transition: box-shadow .15s ease;
}}
[data-testid="stTextInputRootElement"]:focus-within {{
  box-shadow: 0 0 0 3px rgba(27, 153, 139, .25);
}}

/* ---------- Botões ---------- */
[data-testid^="stBaseButton-primary"],
[data-testid^="stBaseButton-secondary"] {{
  border-radius: 8px;
  font-weight: 600;
  padding: .55rem 1.15rem;
  min-height: 2.75rem;
  transition: transform .15s ease, box-shadow .15s ease, background-color .15s ease;
}}
[data-testid^="stBaseButton-primary"] {{
  background: var(--pcmso-primaria);
  border: 1px solid var(--pcmso-primaria);
  color: #FFFFFF;
  box-shadow: 0 1px 2px rgba(15, 76, 92, .25);
}}
[data-testid^="stBaseButton-primary"]:hover {{
  background: var(--pcmso-primaria-escura);
  border-color: var(--pcmso-primaria-escura);
  color: #FFFFFF;
  transform: translateY(-1px);
  box-shadow: var(--pcmso-sombra-alta);
}}
[data-testid^="stBaseButton-secondary"] {{
  background: #FFFFFF;
  border: 1.5px solid var(--pcmso-primaria);
  color: var(--pcmso-primaria);
}}
[data-testid^="stBaseButton-secondary"]:hover {{
  background: #EEF5F6;
  border-color: var(--pcmso-primaria);
  color: var(--pcmso-primaria);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(15, 76, 92, .12);
}}
[data-testid^="stBaseButton-"]:focus-visible {{
  outline: 3px solid rgba(27, 153, 139, .45);
  outline-offset: 2px;
}}
[data-testid^="stBaseButton-"]:active {{ transform: translateY(0); }}
/* Downloads ocupam a coluna inteira: alvo de clique maior e linha alinhada.
   O limite de largura está no stElementContainer (largura "content" do
   Streamlit 1.4x+), não no botão — por isso o :has() no container. */
[data-testid="stElementContainer"]:has(> [data-testid="stDownloadButton"]),
[data-testid="stDownloadButton"],
[data-testid="stDownloadButton"] button {{ width: 100%; }}

/* ---------- Upload (dropzone) ---------- */
[data-testid="stFileUploaderDropzone"] {{
  border: 2px dashed #9CC9C3;
  border-radius: var(--pcmso-raio);
  background: #F3FAF9;
  padding: 1.4rem 1.25rem;
  transition: border-color .2s ease, background-color .2s ease;
}}
[data-testid="stFileUploaderDropzone"]:hover {{
  border-color: var(--pcmso-acento);
  background: #E8F5F3;
}}
[data-testid="stFileUploaderDropzone"] svg {{ color: var(--pcmso-acento); }}
[data-testid="stFileUploaderDropzoneInstructions"] span {{ font-weight: 600; color: var(--pcmso-texto); }}

/* ---------- Alertas ---------- */
/* Fundo e cor do tipo vêm do stAlertContainer (não do stAlertContent*, que é
   filho): por isso a paleta entra pelo :has() no container. */
[data-testid="stAlertContainer"] {{
  border-radius: 10px;
  border-left: 4px solid;
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentSuccess"]) {{
  background: #EAF6EF; border-left-color: var(--pcmso-sucesso);
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentWarning"]) {{
  background: #FDF5E6; border-left-color: var(--pcmso-alerta);
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentError"]) {{
  background: #FDECEA; border-left-color: var(--pcmso-erro);
}}
[data-testid="stAlertContainer"]:has([data-testid="stAlertContentInfo"]) {{
  background: #E7F0F2; border-left-color: var(--pcmso-primaria);
}}
[data-testid="stAlertContainer"] p {{ color: var(--pcmso-texto); }}

/* ---------- Expanders ---------- */
[data-testid="stExpander"] details {{
  border: 1px solid var(--pcmso-borda);
  border-radius: 10px;
  background: #FFFFFF;
}}
[data-testid="stExpander"] summary:hover {{ color: var(--pcmso-primaria); }}

/* ---------- Tabelas (revisão em markdown) e métricas ---------- */
[data-testid="stMarkdownContainer"] table {{
  border-collapse: separate;
  border-spacing: 0;
  width: 100%;
  border: 1px solid var(--pcmso-borda);
  border-radius: 10px;
  overflow: hidden;
  font-size: .9rem;
}}
[data-testid="stMarkdownContainer"] th {{
  background: #EAF1F3;
  color: var(--pcmso-primaria);
  font-weight: 600;
  text-align: left;
}}
[data-testid="stMarkdownContainer"] th, [data-testid="stMarkdownContainer"] td {{
  padding: .5rem .75rem;
  border: none;
  border-bottom: 1px solid var(--pcmso-borda);
}}
[data-testid="stMarkdownContainer"] tr:nth-child(even) td {{ background: #FAFBFC; }}
[data-testid="stMarkdownContainer"] tr:last-child td {{ border-bottom: none; }}
[data-testid="stMetric"] {{
  background: var(--pcmso-cartao);
  border: 1px solid var(--pcmso-borda);
  border-radius: 10px;
  padding: .9rem 1rem;
}}
[data-testid="stMetricValue"] {{ color: var(--pcmso-primaria); font-weight: 700; }}

/* ---------- Responsivo ---------- */
@media (max-width: 640px) {{
  [data-testid="stMainBlockContainer"] {{ padding-left: 1rem; padding-right: 1rem; }}
  /* min-height: auto, não 0: com 0 o item flex encolhe abaixo do texto e ele vaza. */
  [class*="st-key-passo_"] {{ min-height: auto; padding: .5rem .75rem; }}
  .st-key-etapa_pgr, .st-key-etapa_fds, .st-key-caixa_conferencia, .st-key-caixa_matriz {{
    padding: 1rem !important;
  }}
}}
@media (prefers-reduced-motion: reduce) {{
  * {{ transition: none !important; }}
  [data-testid^="stBaseButton-"]:hover {{ transform: none; }}
}}
</style>
"""


def aplicar_estilos() -> None:
    # st.html só com <style> não ocupa espaço na página (vai para o container de eventos).
    st.html(_css())
