# ÍNDICE D-ARQ — DERIVADO, NÃO EDITAR À MÃO

Gerado por `scripts/gerar_indice_darq.py` a partir de
`docs/DECISOES_ARQUITETURAIS.md`. Editar este arquivo à mão faz
`tests/test_gerar_indice_darq.py` falhar.

Fonte: DECISOES_ARQUITETURAIS.md v151 · 66 decisões

| ID | Título | Status | Linha | Chars |
|---|---|---|---|---|
| D-ARQ-01 | Matriz tem duas dimensões independentes |  | 9 | 842 |
| D-ARQ-02 | Sinais indiretos e risco implícito são regras de primeira classe |  | 22 | 1035 |
| D-ARQ-03 | "Atividade crítica" é um predicado pivô |  | 46 | 1003 |
| D-ARQ-04 | Regime regulatório especializado como exceção controlada |  | 65 | 1433 |
| D-ARQ-05 | Lembretes operacionais são saída de primeira classe |  | 86 | 903 |
| D-ARQ-06 | Universalidade tem prioridade sobre cobertura completa do Viverde |  | 102 | 1103 |
| D-ARQ-07 | Protocolo é dado, não código |  | 119 | 861 |
| D-ARQ-08 | Pendência tem nível: bloqueante vs operacional |  | 139 | 1068 |
| D-ARQ-09 | Motor é determinístico; LLM fica fora do caminho crítico |  | 154 | 820 |
| D-ARQ-10 | Predicados: primitivos em código, compostos em YAML |  | 168 | 1602 |
| D-ARQ-11 | Reaproveitamento de exames é responsabilidade do agendador, não do motor |  | 187 | 788 |
| D-ARQ-12 | Vocabulário é dado tipado de primeira classe |  | 200 | 1762 |
| D-ARQ-13 | Predicados são tri-estado: True / False / Ausente |  | 222 | 1287 |
| D-ARQ-14 | Vocabulário ausente em runtime gera Pendencia, não exceção nem persistência |  | 244 | 2126 |
| D-ARQ-15 | Orquestrador compõe os estágios e define o status do Resultado |  | 268 | 2283 |
| D-ARQ-16 | Arquétipo de exposição física qualificável; subtipo via identidade de agente |  | 289 | 5185 |
| D-ARQ-17 | Stage 3: pendências estruturais (integridade do input por-GHE) |  | 344 | 4073 |
| D-ARQ-18 | Estratégia de validação Viverde: gabarito é a RQ.61 (PDF/DOCX), não o banco extraído |  | 367 | 5580 |
| D-ARQ-19 | Periodicidade dependente de tempo de exposição acumulado é do agendador, não do motor |  | 393 | 1757 |
| D-ARQ-20 | Periodicidade condicional via família de regras por faixa, não via schema de regra estendido |  | 408 | 1669 |
| D-ARQ-21 | O agrupamento em GHE é canônico: o motor respeita o GHE do PGR, não re-agrupa |  | 424 | 1851 |
| D-ARQ-22 | Modelo de qualidade: erro-zero, revisão de saída e PDCA |  | 441 | 4411 |
| D-ARQ-23 | Operação/atividade é dado de primeira classe do GHE | PROPOSTA | 495 | 1720 |
| D-ARQ-24 | Origem do LEO é resolvida por agente e cenário, separada do regime do PCMSO |  | 525 | 7492 |
| D-ARQ-25 | Camada de extração: contrato LLM→motor e normalização de vocabulário a montante |  | 561 | 8319 |
| D-ARQ-26 | Ritual de abertura de sessão é uma skill /kickoff: coletor de estado determinístico, julgamento no Arquiteto |  | 642 | 5794 |
| D-ARQ-27 | Método de construção: derivação normativa via PDCA, Carolini valida saídas (não método) |  | 676 | 2009 |
| D-ARQ-28 | Caminho declarativo regra→lembrete operacional (PROPOSTA, não implementada) | PROPOSTA | 692 | 1682 |
| D-ARQ-29 | Fração do PNOS é invariante normativa: helper injeta RESPIRAVEL, não bloqueia |  | 706 | 2183 |
| D-ARQ-30 | Rotina de briefing diário é informativa; /kickoff permanece o gate de abertura |  | 723 | 3039 |
| D-ARQ-31 | Bloqueio é por-risco/por-linha, não por-GHE: MatrizGHE tri-estado (VÁLIDA/PARCIAL/BLOQUEADA) com pendência anexada à linha |  | 745 | 14006 |
| D-ARQ-32 | Handoff de sessão é a 4ª entrega do ritual de encerramento |  | 800 | 1734 |
| D-ARQ-33 | Lado-engenheiro é motor irmão de resolução de composição química; conduta permanece no lado-médico | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 816 | 8972 |
| D-ARQ-34 | Materialidade do lado-engenheiro: concentração é faixa, materialidade é predicado tri-estado compartilhado | DECISÃO DE ARQUITETURA | 875 | 11523 |
| D-ARQ-35 | Risco químico de composição é a 4ª fonte de risco, promovida no Stage 2 médico; o motor irmão não a produz | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 917 | 14193 |
| D-ARQ-36 | Extração de composição é bicamada (LLM-transcrição + resolvedor determinístico); "CAS transcrito" é a fronteira; gate-CAS é a fatia 1 | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 962 | 21239 |
| D-ARQ-37 | Propagação da pendência do gate-CAS ao Resultado é via retorno-tupla do motor irmão, como pendência global, não realocação para o Stage 3 | DECISÃO DE ARQUITETURA | 1025 | 9661 |
| D-ARQ-38 | `tipo_ibe` tem dois consumidores de prontidões distintas; o campo entra para ser consumido; a forma do emissor de biomonitoramento é adiada por dependência do mapa agente→biomarcador |  | 1056 | 15722 |
| D-ARQ-39 | Convergência de mesmo-exame com periodicidades distintas resolve por piso component-wise, não por ConflitoProtocolo | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1100 | 8982 |
| D-ARQ-40 | Ponto de entrada de produção do motor novo é uma fachada que esconde a construção do índice CAS; harness, não travessia de PGR real | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1145 | 10091 |
| D-ARQ-41 | Camada de extração é bicamada (transcritor-LLM + resolvedor determinístico); a fronteira é um contrato transcrito tipado; parse-PGR e transcrição-FDS são duas instâncias do mesmo padrão | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1191 | 8088 |
| D-ARQ-42 | Transcritor-FDS é a camada-LLM da instância-FDS de D-ARQ-41; contrato de saída é `tuple[Componente,...]` cravado; recorte (A) identidade+concentração; mecanismo adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1226 | 25203 |
| D-ARQ-43 | Medição dos 6 PDFs de FDS fecha fronteira-OCR e critério-de-nome do transcritor; catálogo de patologias da seção 3 é input da IMPL | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1285 | 9073 |
| D-ARQ-44 | `.gitattributes` `*.md text eol=lf`: terminador de markdown blindado na origem |  | 1323 | 2583 |
| D-ARQ-45 | Explosão de bloco "Derivados de:" multi-CAS mora no resolvedor (1→N a montante do gate-CAS); cada sub-componente herda a faixa inteira do bloco |  | 1341 | 16260 |
| D-ARQ-46 | Contrato do verbatim transcrito da FDS: o LLM-transcritor emite verbatim cru (texto por campo); `tuple[Componente,...]` é saída da montagem determinística, não do LLM | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1373 | 12685 |
| D-ARQ-47 | Contrato de invocação e gate do transcritor-LLM-FDS: candidato verbatim revisado pelo RT é a fronteira LLM↔determinístico | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1421 | 15654 |
| D-ARQ-48 | Fronteira de impureza: adaptador-LLM fora do motor, invariante de pureza testável | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003 | 1477 | 1778 |
| D-ARQ-49 | Contrato do parse-PGR: instância-PGR de D-ARQ-41; recorte esqueleto-GHE (cargos+riscos+quantificação crus + FDS apontadas); mecanismo termo→slug adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1491 | 10474 |
| D-ARQ-50 | Medição do PGR Viverde fecha parse-doc e mecanismo termo→slug do parse-PGR; irmão de D-ARQ-43 do lado-PGR | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1539 | 17767 |
| D-ARQ-51 | Hidratação GHEVerbatim → tipos.PGR: consumidor de produção do resolver termo→slug; id posicional, agente tri-estado→Optional, None-agente não-bloqueante | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO por fatias | 1588 | 13159 |
| D-ARQ-52 | Plug de produção lado-PGR: costura arquivo→Resultado; envelope RT-supplied; atravessa a hidratação (assimetria não-bloqueante vs. FDS) | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003 | 1632 | 5516 |
| D-ARQ-53 | Transcrição-de-topo do envelope: instância-envelope de D-ARQ-41; pré-preenchimento document-derived + confirmação-RT no gate eliminatório (molde revisão-RT D-ARQ-47 cl.4); mecanismo adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1662 | 11767 |
| D-ARQ-54 | Superfície RT como apresentação-pura sobre o contrato ida/volta; CLI primeiro, web herda o mesmo artefato; escopo = os dois seams de confirmação (envelope + FDS) | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1710 | 11480 |
| D-ARQ-55 | Recorte (B) da transcrição-FDS: verbatim-de-perigo é por-membro (H-code cru); mapa frase-H→flag é determinístico resolver-side (só sensibilização); confiança ancora em R-FDS-06 + revisão-RT | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1830 | 11308 |
| D-ARQ-56 | Passo 2 do cluster-FDS: bypass antes do slug-check em `materialidade()`; Fase C tripartida no sem-slug; promoção-sem-slug deferida (DT-003CK-01) |  | 1873 | 3751 |
| D-ARQ-57 | Localizador de blocos GHE: repertório determinístico de âncoras medidas + gate de segmentação; família cargo-based é fronteira de escopo sinalizada, não variação de âncora | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1895 | 59570 |
| D-ARQ-58 | Resolução de predicado por identidade de agente: fallback genérico no avaliador, não um primitivo dedicado por agente | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (mesma sessão 003 | 2085 | 2132 |
| D-ARQ-59 | O refactor família R-BIO-04 → "estágio genérico" é gatilho falso; a família é a forma final, o limiar ~25 aposentado | DECISÃO DE ARQUITETURA (ARQUITETURA, sessão 003 | 2097 | 4817 |
| D-ARQ-60 | Reconciliação nome-de-exibição §5.9 → slug canônico mora no guardião (registro explícito), não no doc; §5.9 é fonte humana, `regras.yaml` a chave de máquina | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (sessão 003 | 2129 | 3530 |
| D-ARQ-61 | Critério de escolha do indicador canônico quando o Anexo I oferece múltiplas opções ("ou") | DECISÃO DE ARQUITETURA (sessão 003 | 2153 | 3566 |
| D-ARQ-62 | Redirecionamento de foco pós-003.DQ: Marco 1 via caso-âncora real; recorte construção civil como sequenciamento, não arquitetura | DECISÃO DE FOCO (sessão 003 | 2189 | 4921 |
| D-ARQ-63 | Gate de abertura em dois níveis: índice derivado + eixo nomeado |  | 2216 | 8398 |
| D-ARQ-64 | Ramo FUZZY opt-in por allowlist de dado: o veto é do resultado, nunca filtro de candidato |  | 2351 | 5616 |
| D-ARQ-65 | Extração determinística por família de template; LLM rebaixado a acelerador para família não-medida; manual é corretivo, não rotina |  | 2433 | 6970 |
| D-ARQ-66 | Emissão incondicional é regra de primeira classe; o tri-estado de D-ARQ-31 computa sobre contribuições de risco, não sobre linhas emitidas |  | 2530 | 2159 |
