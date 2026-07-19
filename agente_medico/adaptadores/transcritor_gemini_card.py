from __future__ import annotations

from agente_medico.adaptadores.transcritor_gemini import (
    TranscricaoIndisponivel,
    _chamar_gemini,
    _obter_chave,
)
from agente_medico.adaptadores.transcritor_gemini_pgr import _parsear_ghe
from agente_medico.motor.tipos import GHEVerbatim

# [DERIVADO — D-ARQ-57 peça 4 fatia 4c-iii; decisões 003.DG-1/2/3, 003.DI-1;
# molde D-ARQ-48/49/53] Implementação REAL de TranscritorCard
# (motor/transcritor_card.py). Fica FORA do motor (D-ARQ-09): é o único lugar
# do sistema que fala com requests/API-key/JSON-de-rede para este contrato do
# lado-card. O motor recebe só o GHEVerbatim já desembrulhado — nunca sabe
# que existe HTTP, cascata de modelo ou chave.
#
# _obter_chave/_chamar_gemini/TranscricaoIndisponivel são REUSADOS por import
# intra-pacote do adaptador FDS (mesma família Gemini, mesma cascata de
# modelos). _parsear_ghe é REUSADO do adaptador GHE-PGR: a saída deste
# contrato é reuso ESTRITO de GHEVerbatim (003.DG-1) — mesma forma JSON
# {"nome","cargos","riscos"} — duplicar o parser aqui seria o mesmo código
# reescrito, não uma decisão nova desta fatia.

_PROMPT_CARD = """Você é um especialista em Programas de Gerenciamento de Riscos (PGR/GRO) conforme a NR-01.

Abaixo está o texto VERBATIM de um card cargo-based de um PGR do template corporativo EBSERH \
(PGR.SOST.001), extraído por leitura de texto de PDF. A âncora do card é a linha-tripla de \
labels puros "Lotação: Escala de Trabalho: Qtde:" (ou variação com espaçamento colapsado, ex.: \
"Lotação: EscaladeTrabalho: Qtd:"). O texto pode ter palavras coladas pelo extrator (ex.: \
"SetorJurídico", "DADOSGERAIS") e a tabela de riscos pode ter células quebradas em várias linhas \
soltas, fora da ordem visual.

Você também recebe o TÍTULO do card (pode ser "" quando ausente no documento): um título \
numerado verbatim, por exemplo "13.1 Advogado" ou "13.17 Biólogo".

Sua tarefa é TRANSCREVER — nunca traduzir, corrigir ou normalizar além do bounded abaixo — os \
dados deste card.

Regras:
1. nome = a lotação/setor da linha SEGUINTE à linha-âncora de labels — NUNCA a própria linha de \
labels. Essa linha seguinte mistura lotação + escala de trabalho + quantidade; extraia só a \
parte da LOTAÇÃO/SETOR, descarte carga horária e quantidade de vagas. Exemplo: da linha \
"Setor Jurídico 40hs/ semana 2 – Efetivos" -> nome = "Setor Jurídico". Quando a linha vem com \
espaçamento colapsado e o cargo embutido após dois-pontos (ex.: "SetorJurídico: ADVOGADO \
40hs/semana VerTab."), desglue as palavras coladas (D-ARQ-50 P2: recompor "SetorJurídico" -> \
"Setor Jurídico") e pare no dois-pontos -> nome = "Setor Jurídico" (o texto após o dois-pontos é \
o CARGO, não o nome — vai para a regra 2, não para o nome).
2. cargos = lista com EXATAMENTE 1 item (o card é 1 cargo : 1 tabela de riscos).
   a. Se o TÍTULO fornecido for não-vazio, o cargo é o título SEM o prefixo numérico: \
"13.1 Advogado" -> cargos = ["Advogado"]; "13.17 Biólogo" -> cargos = ["Biólogo"]. Transcreva o \
restante do título verbatim (não corrija, não traduza). NUNCA faça aritmética sobre o número do \
título — a numeração do documento tem lacunas.
   b. Se o TÍTULO fornecido for "", o cargo está embutido no corpo do card, na mesma linha da \
lotação, após dois-pontos (ex.: "SetorJurídico: ADVOGADO 40hs/semana VerTab." -> cargos = \
["ADVOGADO"]; "UnidadedeClínicaCirúrgica:MÉDICO–ANESTESIOLOGIA 24hs/semana VerTab." -> cargos = \
["MÉDICO–ANESTESIOLOGIA"]). Transcreva verbatim, sem mudar maiúsculas/minúsculas.
3. riscos: a seção "RISCOS AMBIENTAIS" tem até 5 categorias de linha (FÍSICO, QUÍMICO, \
BIOLÓGICO, ERGONOMICO, ACIDENTES) e colunas FATOR DE RISCO / FONTE GERADORA / VIAS DE \
TRANSMISSÃO / CATEGORIA-NÍVEL / TIPO DE EXPOSIÇÃO (a ordem exata das colunas varia entre \
documentos). Para cada categoria que TEM dado (não é inteiramente "N/A"), gere UM item de risco:
   a. agente = o texto da coluna FATOR DE RISCO daquela linha (ex.: "Postura inadequada", \
"Produtos químicos", "Vírus, Bactérias, Protozoários", o texto do perigo de acidente). Aplique a \
mesma normalização linguística BOUNDED do transcritor-GHE (D-ARQ-50 P2): tire qualificador \
solto, corrija typo óbvio, NUNCA emita código/slug, NUNCA traduza.
   b. fonte_geradora = o texto cru da coluna FONTE GERADORA daquela linha (ex.: "Mobiliário \
inadequado" na linha ERGONOMICO acima). Deixe "" quando a coluna estiver ausente ou ilegível.
   c. quantificacao = texto cru COM unidade quando existir valor numérico mensurável (ex.: \
"82,2 dB(A)"); deixe "" quando o risco é qualitativo, "N/A" ou sem valor no documento — é o caso \
mais comum neste template.
   d. Categoria que é INTEIRAMENTE "N/A" nas 5 colunas (ex.: linha "FÍSICO N/A N/A N/A N/A N/A") \
NÃO gera item de risco — pule essa categoria.
4. Palavras coladas pelo extrator (space-collapse) devem ser desgludas de forma BOUNDED \
(D-ARQ-50 P2): recompor a palavra provável quando ela for texto de campo (ex.: \
"Mobiliárioinadequado" -> "Mobiliário inadequado"). NUNCA emita código/slug, NUNCA traduza para \
outro idioma.
5. RUÍDO — NÃO transcreva como campo (mas USE para segmentar linhas): a categoria em si (FÍSICO, \
QUÍMICO, BIOLÓGICO, ERGONOMICO, ACIDENTES), o nível/categoria-de-risco (ex.: "3 Crítica", \
"2 De Atenção"), o tipo de exposição (Permanente/Intermitente/Eventual), as vias de transmissão \
(ex.: "Corpo", "Mucosas expostas"), a seção "EQUIPAMENTOS DE TRABALHO", EPI/EPC \
("EQUIPAMENTOS... INDIVIDUAL/COLETIVA EXISTENTES"), "RECOMENDAÇÕES PARA MEDIDAS DE CONTROLE", e \
o cabeçalho/rodapé de página (razão social, numeração de página, "PROGRAMA DE GERENCIAMENTO DE \
RISCOS - PGR", "DADOS GERAIS" do card seguinte).
6. Card administrativo sem NENHUM risco ocupacional (as 5 categorias inteiramente "N/A") é \
resultado LEGÍTIMO: riscos = [].
7. Retorne APENAS JSON válido, sem markdown, sem texto adicional, neste formato exato:
{{"nome": "Setor Jurídico", "cargos": ["Advogado"], "riscos": [{{"agente": "Postura \
inadequada", "quantificacao": "", "fonte_geradora": "Mobiliário inadequado"}}]}}

Título do card (pode ser vazio): {titulo}

Texto do card:
{card}
"""


class TranscritorGeminiCard:
    """Implementação real de TranscritorCard (motor/transcritor_card.py,
    D-ARQ-57 peça 4 fatia 4c-iii). Injetável: quem monta o cliente decide a
    chave; produção usa _obter_chave() (padrão st.secrets -> os.environ,
    nunca lança).

    Contrato de 2 argumentos (decisão 003.DI-1): o prompt recebe card e
    titulo separadamente — a montagem-do-input é concern desta fatia, o
    cliente não concatena o título no span.

    riscos=[] no JSON de resposta é resultado legítimo (card administrativo
    sem risco ocupacional passa o gate de forma — observação 003.DG-3), não
    uma falha de invocação.
    """

    def __init__(self, chave: str | None = None) -> None:
        self._chave = chave

    def transcrever(self, card: str, titulo: str) -> GHEVerbatim:
        chave = self._chave if self._chave is not None else _obter_chave()
        if not chave:
            raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")
        resposta = _chamar_gemini(_PROMPT_CARD.format(card=card, titulo=titulo), chave)
        if not resposta:
            raise TranscricaoIndisponivel("cascata Gemini sem resposta íntegra (200 + STOP)")
        try:
            return _parsear_ghe(resposta)
        except Exception as e:
            raise TranscricaoIndisponivel(f"JSON inválido: {e}") from e
