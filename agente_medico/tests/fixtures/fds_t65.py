"""Fixture FDS-real do T65 — 3 FDS pareadas a produtos do acervo (D-ARQ-34 fatia 3).

Fonte: PGR - ALT T65 2024.2026 (matrizes_originais/). Pareamento produto -> GHE do T65:
- Cimento Ciplan (FISPQ Ciplan, Cimento Portland NBR 14725) = T65 GHE 7/8/9.
- Adesivo PVC Tigre (FISPQ Tigre rev.05, 2018, GHS NBR 14725-4) = T65 GHE 11.
- Tinta Acrílica (FISPQ 004/2008, Nova Rocha, notação europeia símbolos/frases R) =
  T65 GHE 15.

Fixture CRUA: todos os componentes têm agente=None (default). Slug resolvido pelo
gate_cas (resolver_composicao), não à mão. [DERIVADO — D-ARQ-36 nota 003.V (a)].

Convenção de faixa (D-ARQ-34 Parte 1): "X - Y%" -> FaixaConcentracao(X, Y);
"0 - Y%" -> FaixaConcentracao(0.0, Y).
CAS ND/NA/oculto/vários no documento -> cas="".
"""
from __future__ import annotations

from agente_medico.motor.tipos import Componente, FaixaConcentracao


def tinta_acrilica() -> tuple[Componente, ...]:
    # FISPQ 004/2008, Nova Rocha. Notação europeia (símbolos/frases R). 9 componentes.
    # Só dióxido de titânio tem slug em agentes.yaml.
    return (
        Componente(cas="", nome="Derivados Isotiazolonas e Semi-Acetais",
                   concentracao=FaixaConcentracao(0.1, 0.4), agente=None),
        # TiO2: CAS na FISPQ é 134363-67-7 — FALHA o dígito verificador (ramo c do gate).
        # CAS oficial correto = 13463-67-7. Fixture crua traz o CAS ERRADO do documento,
        # exercitando explicitamente o ramo (c). [DERIVADO — FISPQ 004/2008 + D-ARQ-36 nota 003.V].
        Componente(cas="134363-67-7", nome="Dióxido de Titânio",
                   concentracao=FaixaConcentracao(1.0, 15.0)),
        Componente(cas="51274-00-1", nome="Óxido de Ferro Amarelo",
                   concentracao=FaixaConcentracao(0.1, 3.0), agente=None),
        Componente(cas="", nome="Carbonato de Cálcio ppt",
                   concentracao=FaixaConcentracao(5.0, 15.0), agente=None),
        Componente(cas="1332-58-7", nome="Silicato de Alumínio hidratado",
                   concentracao=FaixaConcentracao(5.0, 15.0), agente=None),
        Componente(cas="", nome="Carbonato de cálcio natural",
                   concentracao=FaixaConcentracao(5.0, 15.0), agente=None),
        Componente(cas="1336-21-6", nome="Hidróxido de amônia (24°Bé)",
                   concentracao=FaixaConcentracao(0.1, 1.0), agente=None),
        Componente(cas="", nome="Polímeros acrílicos aquosos",
                   concentracao=FaixaConcentracao(3.0, 30.0), agente=None),
        Componente(cas="", nome="Alquil Lauril Éter",
                   concentracao=FaixaConcentracao(0.1, 1.2), agente=None),
    )


def cimento_ciplan() -> tuple[Componente, ...]:
    # FISPQ Ciplan, Cimento Portland (NBR 14725). 8 componentes. NENHUM tem slug.
    # NOTA: silicato tricálcico/dicálcico NÃO é sílica cristalina (silica = CAS
    # 14808-60-7, quartzo). São compostos do clínquer, sem slug, não-carcinógenos. Ramo 0.
    return (
        Componente(cas="12168-85-3", nome="Silicato tricálcico",
                   concentracao=FaixaConcentracao(20.0, 70.0), agente=None),
        Componente(cas="10034-77-2", nome="Silicato dicálcico",
                   concentracao=FaixaConcentracao(10.0, 60.0), agente=None),
        Componente(cas="12068-35-8", nome="Ferro-aluminato de cálcio",
                   concentracao=FaixaConcentracao(5.0, 15.0), agente=None),
        Componente(cas="", nome="Sulfato de cálcio",
                   concentracao=FaixaConcentracao(2.0, 10.0), agente=None),
        Componente(cas="1242-78-3", nome="Aluminato tricálcico",
                   concentracao=FaixaConcentracao(1.0, 15.0), agente=None),
        Componente(cas="1317-65-3", nome="Carbonato de cálcio",
                   concentracao=FaixaConcentracao(0.0, 5.0), agente=None),
        Componente(cas="1309-48-4", nome="Óxido de magnésio",
                   concentracao=FaixaConcentracao(0.0, 4.0), agente=None),
        Componente(cas="1305-78-8", nome="Óxido de cálcio",
                   concentracao=FaixaConcentracao(0.0, 0.2), agente=None),
    )


def adesivo_pvc_tigre() -> tuple[Componente, ...]:
    # FISPQ Tigre rev.05 (2018, GHS NBR 14725-4). 7 componentes. Só MEK tem slug.
    return (
        Componente(cas="67-64-1", nome="Acetona",
                   concentracao=FaixaConcentracao(30.0, 70.0), agente=None),
        # MEK: CAS "78-93-3" válido; slug resolvido pelo gate (metil_etil_cetona). min 10 > 5 → MATERIAL.
        Componente(cas="78-93-3", nome="Metiletilcetona (MEK)",
                   concentracao=FaixaConcentracao(10.0, 42.0)),
        Componente(cas="9003-22-9", nome="Copolímero de PVC",
                   concentracao=FaixaConcentracao(15.0, 35.0), agente=None),
        Componente(cas="141-78-6", nome="Acetato de Etila",
                   concentracao=FaixaConcentracao(5.0, 30.0), agente=None),
        Componente(cas="7128-64-5", nome="2,5-tiofenodiilbis(5-terc-butil-1,3-benzoxazole)",
                   concentracao=FaixaConcentracao(0.0, 10.0), agente=None),
        Componente(cas="", nome="Segredo Industrial 1",
                   concentracao=FaixaConcentracao(0.0, 1.0), agente=None),
        # CAS oculto. H334 (sensib. respiratória) + H317 (sensib. dérmica) DECLARADOS na FDS.
        # CASO-ÂNCORA da DT da 003.M (ramo-0-vs-bypass com CAS oculto): flag-de-perigo-no-
        # documento + CAS-oculto → sem slug → agente=None → ramo 0 → AUSENTE, mascarando o
        # bypass-sensibilizante. D-ARQ-55: o dado cru agora É CARREGADO (frases_h abaixo);
        # is_sensibilizante permanece False NESTA fixture CRUA — quem liga a flag é
        # mapear_frases_h no resolver, não a montagem. O ramo-0 ainda mascara a saída
        # (AUSENTE) até o passo 2 (reordenação, fora de escopo desta fatia).
        Componente(cas="", nome="Segredo Industrial 2",
                   concentracao=FaixaConcentracao(0.0, 0.5), agente=None,
                   frases_h=("H334", "H317")),
    )
