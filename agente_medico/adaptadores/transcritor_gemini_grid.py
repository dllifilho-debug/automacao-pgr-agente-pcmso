from __future__ import annotations

from collections.abc import Sequence

from agente_medico.adaptadores.transcritor_gemini import (
    TranscricaoIndisponivel,
    _chamar_gemini,
    _obter_chave,
)
from agente_medico.adaptadores.transcritor_gemini_pgr import _parsear_ghes_lote
from agente_medico.motor.tipos import GHEVerbatim
from agente_medico.motor.transcritor_grid import EntradaGrid

# [DERIVADO — D-ARQ-57 peça 5, fatia G2 (sessão claude/gifted-cerf-0loir2);
# molde TranscritorGeminiCard (peça 4) e TranscritorGeminiGHE.transcrever_lote
# (003.EW)] Implementação real de TranscritorGrid, fora do motor (D-ARQ-09).
# _parsear_ghes_lote é reusado do adaptador GHE: a saída é a mesma forma
# JSON {"nome","cargos","riscos"} em array, com o mesmo contrato de
# comprimento (faltante vira GHEVerbatim vazio, nunca tupla curta).

_GRUPOS_POR_LOTE = 6  # mesmo valor da rota GHE (003.EW); grupo do grid tem ~2-3 mil caracteres
_TENTATIVAS_LOTE = 2  # mesma razão medida na rota GHE: JSON cortado com finishReason STOP

_PROMPT_GRID_LOTE = """Você é um especialista em Programas de Gerenciamento de Riscos (PGR/GRO) conforme a NR-01.

Abaixo estão VÁRIOS grupos de função de um PGR cujo inventário de riscos é uma tabela única \
(grid de avaliação de risco por função). Cada grupo vem delimitado por "--- GRUPO N ---" (N começa \
em 1) e traz duas partes:
- "FUNÇÃO (como está no PDF):" — o nome da coluna FUNÇÃO, já separado por leitura de coluna. Pode \
vir com espaço quebrado pela extração do PDF (ex.: "CARPINTEIR O", "EN C AR R E G A D O D E EN C A N A D O R").
- "LINHAS:" — as linhas das outras colunas da tabela, na ordem vertical da página. As colunas se \
intercalam na mesma linha e uma célula pode quebrar em várias linhas.

Colunas da tabela, da esquerda para a direita: TIPO DE RISCO (uma letra: F físico, Q químico, \
B biológico, E ergonômico, A acidente — às vezes sozinha numa linha); IDENTIFICAÇÃO DE PERIGO/RISCO \
(o agente ou perigo, ex.: "RUÍDO CONTÍNUO OU INTERMITENTE", "POEIRA - PNOS", "QUEDAS DE ALTURA"); \
CÓDIGO eSocial (ex.: "02.01.001", ou "—"); TEMPO DE EXPOSIÇÃO ("HABITUAL/ PERMANENTE", "EVENTUAL/ \
INTERMITENTE"); MEIO DE PROPAGAÇÃO ("CONTATO", "SONORA", "RESPIRATÓRIA", "CULTÂNEA"); PROBABILIDADE \
("2 - MODERADA", "POUCA IMPORTÂNCIA"); EFEITO ("PREOCUPANTE", "BAIXO"); NÍVEL DE RISCO \
("MODERADO", "1 - BAIXO"); CLASSIFICAÇÃO ("2 - DE ATENÇÃO", "1 - IRRELEVANTE"); ELIMINAÇÃO OU \
CONTROLE EXISTENTE (EPIs e medidas: "PROTETOR AURICULAR TIPO PLUG", "BOTINA", "TREINAMENTO").

Sua tarefa é TRANSCREVER — nunca traduzir nem inventar — os dados de CADA grupo, de forma \
INDEPENDENTE (um grupo nunca herda dado de outro).

Regras (aplicam a cada grupo individualmente):
1. nome = o nome da FUNÇÃO do grupo com o espaçamento consertado e nada mais (ex.: "CARPINTEIR O" -> \
"CARPINTEIRO"; "EN C AR R E G A D O D E EN C A N A D O R" -> "ENCARREGADO DE ENCANADOR"). Mantenha \
maiúsculas/minúsculas e a grafia do documento, inclusive erro de digitação (ex.: "ADMINISTRATVO" fica \
como está). Quando o nome junta várias funções separadas por "/", o nome é o texto inteiro, com as barras.
2. cargos = as funções do grupo, um item por função, com o espaçamento consertado como na regra 1:
   a. Separe nas barras "/" quando cada parte é uma função distinta (ex.: "ENGENHEIRO CIVIL/ \
ENGENHEIRO RESIDENTE/ ESTAGIÁRIO DE ENGENHARIA/ APONTADOR ADMINISTRATIVO DE OBRA/ TÉCNICO DE \
SEGURANÇA DO TRABALHO" -> 5 cargos, sendo um deles "APONTADOR ADMINISTRATIVO DE OBRA"; "VIGIA DIURNO/ \
VIGIA NOTURNO" -> 2 cargos).
   b. NÃO separe quando a barra une o masculino e o feminino do mesmo cargo (ex.: "Comprador / \
Compradora" -> 1 cargo "Comprador / Compradora") ou duas palavras de um mesmo título (ex.: "Engenheiro \
Civil / Planejamento" -> 1 cargo; "Encarregado de Encanador/Hidráulica" -> 1 cargo).
   c. Sem barra, o grupo tem 1 cargo, igual ao nome.
   d. NUNCA crie cargo que não está escrito no nome da FUNÇÃO, e nunca separe onde não há barra.
3. riscos: um item por linha da tabela, isto é, por perigo da coluna IDENTIFICAÇÃO DE PERIGO/RISCO:
   a. agente = o texto do perigo, inteiro, juntando as linhas em que a célula quebrou (ex.: \
"POSIÇÕES FORÇADAS -" + "SENTADO POR LONGOS" + "PERÍODOS" -> "POSIÇÕES FORÇADAS - SENTADO POR \
LONGOS PERÍODOS"; "RADIAÇÃO" + "ULTRAVIOLETA" -> "RADIAÇÃO ULTRAVIOLETA"). Conserte só espaço quebrado \
pela extração. NUNCA emita código/slug, NUNCA traduza, NUNCA junte dois perigos num item.
   b. quantificacao = texto cru COM unidade quando a linha traz valor medido (ex.: "82,2 dB(A)"); "" \
quando não traz — o caso normal desta tabela. Não calcule nem converta.
   c. fonte_geradora = "" (esta tabela não tem coluna de fonte geradora).
   d. avaliacao_qualitativa = "" sempre.
4. RUÍDO — use para separar as linhas, mas NÃO transcreva como campo: a letra do TIPO DE RISCO, o \
CÓDIGO eSocial, TEMPO DE EXPOSIÇÃO, MEIO DE PROPAGAÇÃO, PROBABILIDADE, EFEITO, NÍVEL DE RISCO, \
CLASSIFICAÇÃO, os EPIs e medidas de controle, o travessão "—", e cabeçalho/rodapé de página \
("PGR | PROGRAMA DE GERENCIAMENTO DE RISCOS", "Matriz de Risco AIHA").
5. Grupo sem nenhuma linha de perigo é resultado legítimo: riscos = [].

Retorne APENAS um array JSON válido, sem markdown, sem texto adicional, com EXATAMENTE um objeto por \
grupo, NA MESMA ORDEM dos grupos abaixo (posição 1 do array = GRUPO 1, e assim por diante), neste \
formato exato:
[{{"nome": "VIGIA DIURNO/ VIGIA NOTURNO", "cargos": ["VIGIA DIURNO", "VIGIA NOTURNO"], "riscos": \
[{{"agente": "RUÍDO CONTÍNUO OU INTERMITENTE", "quantificacao": "", "fonte_geradora": "", \
"avaliacao_qualitativa": ""}}]}}]

Grupos:
{grupos}
"""


def _montar_prompt_lote(lote: Sequence[EntradaGrid]) -> str:
    grupos = "\n\n".join(
        f"--- GRUPO {i} ---\nFUNÇÃO (como está no PDF): {entrada.nome_verbatim}\nLINHAS:\n{entrada.texto}"
        for i, entrada in enumerate(lote, start=1)
    )
    return _PROMPT_GRID_LOTE.format(grupos=grupos)


class TranscritorGeminiGrid:
    """Implementação real de TranscritorGrid (motor/transcritor_grid.py).
    Injetável: quem monta o cliente decide a chave; produção usa
    _obter_chave() (st.secrets -> os.environ, nunca lança)."""

    def __init__(self, chave: str | None = None) -> None:
        self._chave = chave

    def transcrever_lote(self, entradas: Sequence[EntradaGrid]) -> tuple[GHEVerbatim, ...]:
        """Fatia `entradas` em lotes de _GRUPOS_POR_LOTE. Cada lote tem até
        _TENTATIVAS_LOTE chamadas se o JSON vier malformado ou vazio; só a
        última falha levanta, como TranscricaoIndisponivel — mesmo
        tratamento de TranscritorGeminiGHE._transcrever_um_lote."""
        chave = self._chave if self._chave is not None else _obter_chave()
        if not chave:
            raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")
        resultado: list[GHEVerbatim] = []
        for inicio in range(0, len(entradas), _GRUPOS_POR_LOTE):
            lote = entradas[inicio : inicio + _GRUPOS_POR_LOTE]
            resultado.extend(self._transcrever_um_lote(lote, chave))
        return tuple(resultado)

    def _transcrever_um_lote(self, lote: Sequence[EntradaGrid], chave: str) -> tuple[GHEVerbatim, ...]:
        ultimo_erro: Exception | None = None
        for _ in range(_TENTATIVAS_LOTE):
            resposta = _chamar_gemini(_montar_prompt_lote(lote), chave)
            try:
                return _parsear_ghes_lote(resposta, len(lote))
            except Exception as e:
                ultimo_erro = e
        raise TranscricaoIndisponivel(f"JSON inválido (lote do grid): {ultimo_erro}") from ultimo_erro
