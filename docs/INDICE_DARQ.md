# ÍNDICE D-ARQ — DERIVADO, NÃO EDITAR À MÃO

Gerado por `scripts/gerar_indice_darq.py` a partir de
`docs/DECISOES_ARQUITETURAIS.md`. Editar este arquivo à mão faz
`tests/test_gerar_indice_darq.py` falhar.

Fonte: DECISOES_ARQUITETURAIS.md v204 · 85 decisões

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
| D-ARQ-22 | Modelo de qualidade: erro-zero, revisão de saída e PDCA |  | 441 | 5405 |
| D-ARQ-23 | Operação/atividade é dado de primeira classe do GHE | PROPOSTA | 507 | 1720 |
| D-ARQ-24 | Origem do LEO é resolvida por agente e cenário, separada do regime do PCMSO |  | 537 | 7492 |
| D-ARQ-25 | Camada de extração: contrato LLM→motor e normalização de vocabulário a montante |  | 573 | 8319 |
| D-ARQ-26 | Ritual de abertura de sessão é uma skill /kickoff: coletor de estado determinístico, julgamento no Arquiteto |  | 654 | 5794 |
| D-ARQ-27 | Método de construção: derivação normativa via PDCA, Carolini valida saídas (não método) |  | 688 | 2009 |
| D-ARQ-28 | Caminho declarativo regra→lembrete operacional (PROPOSTA, não implementada) | PROPOSTA | 704 | 1682 |
| D-ARQ-29 | Fração do PNOS é invariante normativa: helper injeta RESPIRAVEL, não bloqueia |  | 718 | 2183 |
| D-ARQ-30 | Rotina de briefing diário é informativa; /kickoff permanece o gate de abertura |  | 735 | 3039 |
| D-ARQ-31 | Bloqueio é por-risco/por-linha, não por-GHE: MatrizGHE tri-estado (VÁLIDA/PARCIAL/BLOQUEADA) com pendência anexada à linha |  | 757 | 14006 |
| D-ARQ-32 | Handoff de sessão é a 4ª entrega do ritual de encerramento |  | 812 | 1734 |
| D-ARQ-33 | Lado-engenheiro é motor irmão de resolução de composição química; conduta permanece no lado-médico | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 828 | 8972 |
| D-ARQ-34 | Materialidade do lado-engenheiro: concentração é faixa, materialidade é predicado tri-estado compartilhado | DECISÃO DE ARQUITETURA | 887 | 11523 |
| D-ARQ-35 | Risco químico de composição é a 4ª fonte de risco, promovida no Stage 2 médico; o motor irmão não a produz | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 929 | 14193 |
| D-ARQ-36 | Extração de composição é bicamada (LLM-transcrição + resolvedor determinístico); "CAS transcrito" é a fronteira; gate-CAS é a fatia 1 | DECISÃO DE ARQUITETURA (CONHECIMENTO→ARQUITETURA) | 974 | 21239 |
| D-ARQ-37 | Propagação da pendência do gate-CAS ao Resultado é via retorno-tupla do motor irmão, como pendência global, não realocação para o Stage 3 | DECISÃO DE ARQUITETURA | 1037 | 9661 |
| D-ARQ-38 | `tipo_ibe` tem dois consumidores de prontidões distintas; o campo entra para ser consumido; a forma do emissor de biomonitoramento é adiada por dependência do mapa agente→biomarcador |  | 1068 | 15722 |
| D-ARQ-39 | Convergência de mesmo-exame com periodicidades distintas resolve por piso component-wise, não por ConflitoProtocolo | IMPLEMENTADA (003 | 1112 | 13644 |
| D-ARQ-40 | Ponto de entrada de produção do motor novo é uma fachada que esconde a construção do índice CAS; harness, não travessia de PGR real | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1208 | 10091 |
| D-ARQ-41 | Camada de extração é bicamada (transcritor-LLM + resolvedor determinístico); a fronteira é um contrato transcrito tipado; parse-PGR e transcrição-FDS são duas instâncias do mesmo padrão | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1254 | 8088 |
| D-ARQ-42 | Transcritor-FDS é a camada-LLM da instância-FDS de D-ARQ-41; contrato de saída é `tuple[Componente,...]` cravado; recorte (A) identidade+concentração; mecanismo adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1289 | 25203 |
| D-ARQ-43 | Medição dos 6 PDFs de FDS fecha fronteira-OCR e critério-de-nome do transcritor; catálogo de patologias da seção 3 é input da IMPL | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1348 | 9073 |
| D-ARQ-44 | `.gitattributes` `*.md text eol=lf`: terminador de markdown blindado na origem |  | 1386 | 2583 |
| D-ARQ-45 | Explosão de bloco "Derivados de:" multi-CAS mora no resolvedor (1→N a montante do gate-CAS); cada sub-componente herda a faixa inteira do bloco |  | 1404 | 16260 |
| D-ARQ-46 | Contrato do verbatim transcrito da FDS: o LLM-transcritor emite verbatim cru (texto por campo); `tuple[Componente,...]` é saída da montagem determinística, não do LLM | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1436 | 12685 |
| D-ARQ-47 | Contrato de invocação e gate do transcritor-LLM-FDS: candidato verbatim revisado pelo RT é a fronteira LLM↔determinístico | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1484 | 18306 |
| D-ARQ-48 | Fronteira de impureza: adaptador-LLM fora do motor, invariante de pureza testável | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003 | 1542 | 1778 |
| D-ARQ-49 | Contrato do parse-PGR: instância-PGR de D-ARQ-41; recorte esqueleto-GHE (cargos+riscos+quantificação crus + FDS apontadas); mecanismo termo→slug adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1556 | 24980 |
| D-ARQ-50 | Medição do PGR Viverde fecha parse-doc e mecanismo termo→slug do parse-PGR; irmão de D-ARQ-43 do lado-PGR | DECISÃO DE ARQUITETURA (CONHECIMENTO/medição → ARQUITETURA) | 1628 | 17767 |
| D-ARQ-51 | Hidratação GHEVerbatim → tipos.PGR: consumidor de produção do resolver termo→slug; id posicional, agente tri-estado→Optional, None-agente não-bloqueante | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO por fatias | 1677 | 13159 |
| D-ARQ-52 | Plug de produção lado-PGR: costura arquivo→Resultado; envelope RT-supplied; atravessa a hidratação (assimetria não-bloqueante vs. FDS) | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (003 | 1721 | 5516 |
| D-ARQ-53 | Transcrição-de-topo do envelope: instância-envelope de D-ARQ-41; pré-preenchimento document-derived + confirmação-RT no gate eliminatório (molde revisão-RT D-ARQ-47 cl.4); mecanismo adiado por medição | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1751 | 11767 |
| D-ARQ-54 | Superfície RT como apresentação-pura sobre o contrato ida/volta; CLI primeiro, web herda o mesmo artefato; escopo = os dois seams de confirmação (envelope + FDS) | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1799 | 11480 |
| D-ARQ-55 | Recorte (B) da transcrição-FDS: verbatim-de-perigo é por-membro (H-code cru); mapa frase-H→flag é determinístico resolver-side (só sensibilização); confiança ancora em R-FDS-06 + revisão-RT | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1919 | 11308 |
| D-ARQ-56 | Passo 2 do cluster-FDS: bypass antes do slug-check em `materialidade()`; Fase C tripartida no sem-slug; promoção-sem-slug deferida (DT-003CK-01) |  | 1962 | 3751 |
| D-ARQ-57 | Localizador de blocos GHE: repertório determinístico de âncoras medidas + gate de segmentação; família cargo-based é fronteira de escopo sinalizada, não variação de âncora | DECISÃO DE ARQUITETURA (ARQUITETURA) | 1984 | 81151 |
| D-ARQ-58 | Resolução de predicado por identidade de agente: fallback genérico no avaliador, não um primitivo dedicado por agente | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (mesma sessão 003 | 2230 | 2132 |
| D-ARQ-59 | O refactor família R-BIO-04 → "estágio genérico" é gatilho falso; a família é a forma final, o limiar ~25 aposentado | DECISÃO DE ARQUITETURA (ARQUITETURA, sessão 003 | 2242 | 4817 |
| D-ARQ-60 | Reconciliação nome-de-exibição §5.9 → slug canônico mora no guardião (registro explícito), não no doc; §5.9 é fonte humana, `regras.yaml` a chave de máquina | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (sessão 003 | 2274 | 3530 |
| D-ARQ-61 | Critério de escolha do indicador canônico quando o Anexo I oferece múltiplas opções ("ou") | DECISÃO DE ARQUITETURA (sessão 003 | 2298 | 3566 |
| D-ARQ-62 | Redirecionamento de foco pós-003.DQ: Marco 1 via caso-âncora real; recorte construção civil como sequenciamento, não arquitetura | DECISÃO DE FOCO (sessão 003 | 2334 | 4921 |
| D-ARQ-63 | Gate de abertura em dois níveis: índice derivado + eixo nomeado |  | 2361 | 9410 |
| D-ARQ-64 | Ramo FUZZY opt-in por allowlist de dado: o veto é do resultado, nunca filtro de candidato |  | 2508 | 5616 |
| D-ARQ-65 | Extração determinística por família de template; LLM rebaixado a acelerador para família não-medida; manual é corretivo, não rotina |  | 2590 | 11046 |
| D-ARQ-66 | Emissão incondicional é regra de primeira classe; o tri-estado de D-ARQ-31 computa sobre contribuições de risco, não sobre linhas emitidas |  | 2739 | 2159 |
| D-ARQ-67 | Literal de vocabulário em código é contrato verificado por teste computado do dado |  | 2778 | 1815 |
| D-ARQ-68 | Silêncio documental mapeia para o ramo normativo de ausência quando a norma o define; sem esse ramo, D-ARQ-13 prevalece |  | 2808 | 7446 |
| D-ARQ-69 | Regra clínica escrita antes da sessão não é materializada sem conferir o texto vigente da norma que ela mesma cita |  | 2857 | 3755 |
| D-ARQ-70 | Alias de corpus medido entra no vocabulário só ancorado em literal normativo, com fonte dupla e teste anti-FP |  | 2897 | 3464 |
| D-ARQ-71 | Perna `Ausente` absorvida por `ou` verdadeiro gera pendência não-bloqueante anexada à linha; o tri-estado não se move |  | 2917 | 5506 |
| D-ARQ-72 | Apresentação-de-saída da matriz é superfície própria em `superficie/`, apresentação-pura herdando D-ARQ-54 P1; o status de validação da regra atravessa até `Motivo` | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (fatias 0-2, sessão 003 | 2942 | 2928 |
| D-ARQ-73 | Emissor de saída no formato do escritório: estrutura intermediária única com N renderizadores; expansão GHE→cargo é apresentação; ordem de exibição é dado cravado, não literal solto; cabeçalho/rodapé são seam humano | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (fatias 1-3, sessão 003 | 2967 | 7766 |
| D-ARQ-74 | Superfície que emite artefato assinável lê o status do Resultado e nunca emite documento sem conteúdo clínico | DECISÃO DE ARQUITETURA + IMPLEMENTAÇÃO (sessão 003 | 3071 | 3033 |
| D-ARQ-75 | Hospedagem por consumo, não por tier; autenticação é gate com allowlist própria; o que sobe é o app novo, com dependências medidas | DECISÃO DE ARQUITETURA | 3123 | 12120 |
| D-ARQ-76 | O gate de acesso mora no entrypoint; a decisão é núcleo puro; a fronteira do provedor de identidade normaliza antes de decidir | DECISÃO DE ARQUITETURA | 3294 | 5109 |
| D-ARQ-77 | Mecanismo de build é o Dockerfile; o segredo é materializado antes do servidor | DECISÃO DE ARQUITETURA | 3369 | 4842 |
| D-ARQ-78 | Destino do deploy é o Streamlit Community Cloud; o nome do arquivo de dependências é contrato da plataforma; o gate próprio permanece porque a allowlist nativa é transitiva | DECISÃO DE ARQUITETURA | 3443 | 7609 |
| D-ARQ-79 | Entrypoint de desenvolvimento sem gate é porta deliberada, travada por teste no entrypoint de produção | DECISÃO DE ARQUITETURA | 3550 | 1691 |
| D-ARQ-80 | No nível gratuito o gargalo é requisição, não token: a unidade de invocação do transcritor é o lote | DECISÃO DE ARQUITETURA | 3581 | 7663 |
| D-ARQ-81 | Precedente de corpus enviesado não amplia universo normativo; regra refutada é estado próprio, distinto de sucedida |  | 3693 | 2897 |
| D-ARQ-82 | O selo `VÁLIDA` computa sobre a CAUSA da não-resolução, nunca sobre sua contagem; não-resolução que é acerto do motor não rebaixa a matriz |  | 3737 | 14411 |
| D-ARQ-83 | Termo reconhecido-como-não-agente é categoria própria do vocabulário: entra para NÃO resolver, com pendência de causa e destinatário próprios |  | 3947 | 9623 |
| D-ARQ-84 | Conferência factual é obrigação sem declaração; julgamento permanece gate declarado — os dois instrumentos separam-se pela natureza da falha, não pelo momento | DECISÃO DE MÉTODO (META) | 3996 | 10201 |
| D-ARQ-85 | Baseline e números clínicos do painel têm relógios distintos: o que envelhece a cada commit é re-tirado a cada fechamento | DECISÃO DE MÉTODO (META) | 4045 | 4834 |
