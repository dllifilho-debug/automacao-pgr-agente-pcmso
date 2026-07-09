from __future__ import annotations

import json

from agente_medico.adaptadores.transcritor_gemini import (
    TranscricaoIndisponivel,
    _chamar_gemini,
    _limpar_json,
    _obter_chave,
)
from agente_medico.motor.tipos import EnvelopeVerbatim

# [DERIVADO — D-ARQ-53; molde D-ARQ-48/49] Implementação REAL do TranscritorTopo
# (motor/transcritor_topo.py). Fica FORA do motor (D-ARQ-09): é o único lugar do
# sistema que fala com requests/API-key/JSON-de-rede para este contrato do topo
# do envelope. O motor recebe só o EnvelopeVerbatim já desembrulhado — nunca sabe
# que existe HTTP, cascata de modelo ou chave.
#
# _obter_chave/_chamar_gemini/_limpar_json/TranscricaoIndisponivel são REUSADOS
# por import intra-pacote (nomes privados) do adaptador FDS: mesma família
# Gemini, mesma cascata de modelos, mesma limpeza de markdown-fence — duplicar
# essa cascata aqui seria o mesmo código reescrito, não uma decisão nova desta
# fatia.

_PROMPT_TOPO = """Você é um especialista em Programas de Gerenciamento de Riscos (PGR/GRO) conforme a NR-01.

Abaixo está o texto VERBATIM do TOPO de um PGR, extraído por leitura de texto de PDF. Sua tarefa é \
TRANSCREVER — nunca traduzir, corrigir, normalizar ou deduzir — os dados abaixo.

Regras:
1. validade_textos: TODAS as candidatas de data de vigência/emissão/atualização do documento (mês-ano \
ou dia), na ordem em que aparecem no texto, texto cru (ex.: "FEVEREIRO 2025"). NUNCA converta em data, \
NUNCA escolha a candidata "mais recente", NUNCA deduza uma candidata que não esteja escrita no \
documento. Se não houver nenhuma candidata, emita lista vazia.
2. responsavel_tecnico / titulo_rt / registro_profissional: texto cru do bloco de responsabilidade \
técnica do documento. A âncora desse bloco pode vir com typo de origem (ex.: "RESPONSABILIDADE \
TÉNICA", sem o C) — reconheça variações próximas dessa âncora, mas TRANSCREVA os VALORES exatamente \
como aparecem, sem corrigir o typo. registro_profissional é texto cru — não assuma que é CREA, o \
documento pode citar outro conselho profissional.
3. NÃO julgue se o responsável é engenheiro ou técnico. NÃO emita campo de assinatura — a assinatura \
é imagem, não é texto extraível. NÃO calcule nem normalize nenhuma data.
4. Campo ausente no documento: emita "" (string vazia) para campos de texto, ou [] para \
validade_textos.

Retorne APENAS JSON válido, sem markdown, sem texto adicional, neste formato exato:
{{"validade_textos": ["FEVEREIRO 2023"], "responsavel_tecnico": "Fulano de Tal", "titulo_rt": \
"Eng. de Segurança do Trabalho", "registro_profissional": "CREA - 000000"}}

Texto do topo do PGR:
{topo}
"""


def _parsear_envelope(texto: str) -> EnvelopeVerbatim:
    dados = json.loads(_limpar_json(texto))
    validade_textos = tuple(str(item or "") for item in dados.get("validade_textos", []) or [])
    return EnvelopeVerbatim(
        validade_textos=validade_textos,
        responsavel_tecnico=str(dados.get("responsavel_tecnico", "") or ""),
        titulo_rt=str(dados.get("titulo_rt", "") or ""),
        registro_profissional=str(dados.get("registro_profissional", "") or ""),
    )


class TranscritorGeminiTopo:
    """Implementação real de TranscritorTopo (motor/transcritor_topo.py,
    D-ARQ-53 P2/P3). Injetável: quem monta o cliente decide a chave; produção
    usa _obter_chave() (padrão st.secrets -> os.environ, nunca lança).
    """

    def __init__(self, chave: str | None = None) -> None:
        self._chave = chave

    def transcrever(self, topo: str) -> EnvelopeVerbatim:
        chave = self._chave if self._chave is not None else _obter_chave()
        if not chave:
            raise TranscricaoIndisponivel("CHAVE_API_GOOGLE ausente")
        resposta = _chamar_gemini(_PROMPT_TOPO.format(topo=topo), chave)
        if not resposta:
            raise TranscricaoIndisponivel("cascata Gemini sem resposta íntegra (200 + STOP)")
        try:
            return _parsear_envelope(resposta)
        except Exception as e:
            raise TranscricaoIndisponivel(f"JSON inválido: {e}") from e
