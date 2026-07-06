from __future__ import annotations

import json

from agente_medico.adaptadores.transcritor_gemini import (
    TranscricaoIndisponivel,
    _chamar_gemini,
    _limpar_json,
    _obter_chave,
)
from agente_medico.motor.tipos import GHEVerbatim, RiscoVerbatim

# [DERIVADO — D-ARQ-49 P3, D-ARQ-50 C3/P2; molde D-ARQ-48/transcritor_gemini.py]
# Implementação REAL do TranscritorGHE (motor/transcritor_pgr.py). Fica FORA do
# motor (D-ARQ-09): é o único lugar do sistema que fala com requests/API-key/
# JSON-de-rede para este contrato do lado-PGR. O motor recebe só o
# tuple[GHEVerbatim, ...] já desembrulhado — nunca sabe que existe HTTP,
# cascata de modelo ou chave.
#
# _obter_chave/_chamar_gemini/_limpar_json/TranscricaoIndisponivel são
# REUSADOS por import intra-pacote (nomes privados) do adaptador FDS: mesma
# família Gemini, mesma cascata de modelos, mesma limpeza de markdown-fence —
# duplicar essa cascata aqui seria o mesmo código reescrito, não uma decisão
# nova desta fatia.

_PROMPT_GHE = """Você é um especialista em Programas de Gerenciamento de Riscos (PGR/GRO) conforme a NR-01.

Abaixo está o texto VERBATIM de um bloco GHE (Grupo Homogêneo de Exposição) de um PGR, extraído por \
leitura de texto de PDF. A âncora do bloco é a linha "SETOR/FUNÇÃO ...". O texto pode conter ruído de \
diagramação: colunas de uma tabela intercaladas em linhas soltas, quebras de linha no meio de uma célula, \
e a ordem visual das colunas nem sempre é a ordem em que o extrator devolveu o texto.

Sua tarefa é TRANSCREVER — nunca traduzir, corrigir ou normalizar além do bounded abaixo — os dados deste \
bloco.

Regras:
1. nome = texto do setor/função da linha-âncora "SETOR/FUNÇÃO ...", verbatim (ex.: da linha \
"SETOR/FUNÇÃO Pintura/ pintor/ meio oficial de pintor/ servente" -> nome = "Pintura").
2. cargos = lista de cargos/funções do cabeçalho do bloco, após o setor/função da âncora, um item por \
cargo, verbatim (ex.: mesma linha acima -> cargos = ["pintor", "meio oficial de pintor", "servente"]).
3. riscos: um item por AGENTE de risco do grid de "Caracterização do Perigo" (ignore o cabeçalho de \
tabela "Cód. Atividades Perigo Exposição Fonte geradora Doença do Dano..."). Regras de leitura:
   a. Quando agente e valor de quantificação estão fundidos na mesma célula (ex.: "Ruído ... 82,2 \
dB(A)"), pareie-os num único item.
   b. Quando o mesmo código de atividade (ex.: "ET 51") lista múltiplos agentes (ex.: "Etanol 4,4 ppm", \
"Acetato de Etila 1 ppm", "Tolueno 6,3 ppm"), gere um item de risco POR agente, cada um com a MESMA \
fonte_geradora daquele código copiada.
   c. Quando um risco não tem valor de quantificação numérico (ex.: um perigo de acidente como "Contato \
com o disco desprotegido" ou "Trabalho em periferia da laje"), transcreva o próprio texto do perigo como \
agente e deixe quantificacao = "".
4. agente: normalização linguística BOUNDED (D-ARQ-50 P2) — tire qualificador solto, quebre nome \
composto quando o documento lista mais de um agente na mesma célula, corrija typo óbvio de digitação. \
NUNCA emita um código/slug (ex.: nunca "ruido" ou "RUIDO_82DB"), NUNCA traduza para outro idioma.
5. quantificacao = texto cru, COM a unidade, exatamente como no documento (ex.: "82,2 dB(A)", "6,3 ppm", \
"0,163 mg/m³"). Deixe "" quando o risco é qualitativo ou não tem valor no documento. NÃO calcule, NÃO \
converta unidade, NÃO arredonde.
6. fonte_geradora = texto cru da coluna "Fonte geradora" daquele código de atividade (ex.: \
"Thinner/Zarcão e tinta esmalte sintético", "Manuseio serra circular, Furadeira"). Deixe "" quando a \
coluna estiver ausente ou ilegível para aquele código.
7. RUÍDO — NÃO transcreva: o grid de classificação de risco (colunas de letras/números \
I/O/T/EP/PE/EC/CP/P/GV/EA/S, probabilidade/severidade/grau-de-risco/classe do risco), a lista de \
EPIs/controles ("CONTROLE DOS RISCOS", "RISCO FÍSICO:" e afins), o cabeçalho/rodapé repetido de página \
(razão social, CNPJ, "INVENTÁRIO E CLASSIFICAÇÃO DOS RISCOS OCUPACIONAIS", numeração de página) e o \
"Escore de risco (ER)" de fechamento do bloco.

Retorne APENAS JSON válido, sem markdown, sem texto adicional, neste formato exato:
{{"nome": "Pintura", "cargos": ["pintor", "meio oficial de pintor", "servente"], "riscos": \
[{{"agente": "Etanol", "quantificacao": "4,4 ppm", "fonte_geradora": "Thinner/Zarcão"}}]}}

Texto do bloco GHE:
{bloco}
"""


def _parsear_ghe(texto: str) -> GHEVerbatim:
    dados = json.loads(_limpar_json(texto))
    cargos = tuple(str(cargo or "") for cargo in dados.get("cargos", []) or [])
    riscos = tuple(
        RiscoVerbatim(
            agente=str(risco_raw.get("agente", "") or ""),
            quantificacao=str(risco_raw.get("quantificacao", "") or ""),
            fonte_geradora=str(risco_raw.get("fonte_geradora", "") or ""),
        )
        for risco_raw in dados.get("riscos", []) or []
    )
    return GHEVerbatim(nome=str(dados.get("nome", "") or ""), cargos=cargos, riscos=riscos)


class TranscritorGeminiGHE:
    """Implementação real de TranscritorGHE (motor/transcritor_pgr.py, D-ARQ-49
    P3/D-ARQ-50 C3). Injetável: quem monta o cliente decide a chave; produção
    usa _obter_chave() (padrão st.secrets -> os.environ, nunca lança).

    riscos=[] no JSON de resposta é resultado legítimo (GHE sem riscos passa o
    gate de forma — limite documentado 003.BN), não uma falha de invocação.
    """

    def __init__(self, chave: str | None = None) -> None:
        self._chave = chave

    def transcrever(self, bloco: str) -> GHEVerbatim:
        chave = self._chave if self._chave is not None else _obter_chave()
        if not chave:
            raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")
        resposta = _chamar_gemini(_PROMPT_GHE.format(bloco=bloco), chave)
        if not resposta:
            raise TranscricaoIndisponivel("cascata Gemini sem resposta íntegra (200 + STOP)")
        try:
            return _parsear_ghe(resposta)
        except Exception as e:
            raise TranscricaoIndisponivel(f"JSON inválido: {e}") from e
