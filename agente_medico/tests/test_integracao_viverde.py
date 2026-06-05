"""test_integracao_viverde.py — DT-002Y-02.

Sessão 002.Z: teste de integração do PGR Viverde contra o motor completo.
Verifica que a família R-RX-01-pnos-* roteia sem achatar no 60M único da
regra R-RX-01-pnos DEPRECATED, e que Adm-03 bloqueia pelo ruído pendente
(não por PNOS quebrado).

Anti-achatamento (par-chave):
  GHES_PNOS_LIMPO_MEDIDO → periodicidade_meses == 0 (ate10 ou 10a100)
  GHE_PNOS_SEM_MEDICAO   → periodicidade_meses == 60 (faixa sem)
"""
from __future__ import annotations

from datetime import date
from pathlib import Path

from agente_medico.motor.orquestrador import executar
from agente_medico.motor.protocolo import carregar
from agente_medico.motor.tipos import MatrizGHE, Resultado
from agente_medico.tests.fixtures.pgr_viverde import build_pgr_viverde

_PROTOCOLO_DIR = Path(__file__).parent.parent / "protocolo"

# GHEs com PNOS medido, sem sílica/MEK coabitando.
GHES_PNOS_LIMPO_MEDIDO = {"Est-01", "Est-06", "Est-11", "Acab-02", "Acab-04"}
# GHE com PNOS presente mas sem avaliação quantitativa (quantificacao=None).
GHE_PNOS_SEM_MEDICAO = "Est-02"
# GHEs com sílica ou MEK junto ao PNOS — descoberta, não asserção; ver diagnostico_zona_cinza().
GHES_PNOS_ZONA_CINZA = {"Est-07", "Acab-05", "Acab-06", "Acab-08", "Est-08"}
# PGR validade 10/01/2025; folga ~140d vs 730d do R-PGR-06 → sem rejeição; determinístico.
HOJE_FIXO = date(2025, 6, 1)


def _executar() -> Resultado:
    return executar(build_pgr_viverde(), carregar(_PROTOCOLO_DIR), hoje=HOJE_FIXO)


def test_integracao_viverde_pnos_roteia_sem_achatar() -> None:
    resultado = _executar()

    def _matriz(rid: str) -> MatrizGHE:
        matches = [m for m in resultado.matrizes if m.ghe_id == rid]
        assert len(matches) == 1, f"GHE '{rid}' não encontrado em resultado.matrizes"
        return matches[0]

    # --- status e contagem global ---
    assert resultado.status == "PRELIMINAR", (
        f"esperado PRELIMINAR (Adm-03 ruído pendente), got {resultado.status!r}"
    )
    assert len(resultado.matrizes) == 32, (
        f"esperado 32 GHEs, got {len(resultado.matrizes)}"
    )

    # --- PNOS com medição: 5 GHEs limpos (sem sílica coabitando) ---
    for rid in GHES_PNOS_LIMPO_MEDIDO:
        m = _matriz(rid)
        bloqueantes = [p for p in m.pendencias if p.bloqueante]
        assert bloqueantes == [], (
            f"{rid}: não deveria ter pendências bloqueantes, tem: {bloqueantes}"
        )
        rx_linhas = [ln for ln in m.linhas if ln.exame == "rx_torax_oit"]
        assert len(rx_linhas) >= 1, (
            f"{rid}: deveria ter ≥1 linha rx_torax_oit"
        )
        for ln in rx_linhas:
            assert ln.periodicidade_meses == 0, (
                f"{rid}: rx_torax_oit deveria ter periodicidade=0 "
                f"(faixas ate10 ou 10a100 do Quadro 2), got {ln.periodicidade_meses}"
            )

    # --- PNOS sem medição: Est-02 ---
    # Anti-achatamento: prova que as faixas discriminam e que R-RX-01-pnos DEPRECATED
    # (60M único) não está ativa — se estivesse, os 5 limpos acima teriam 60M também.
    m_sem = _matriz(GHE_PNOS_SEM_MEDICAO)
    bloqueantes_sem = [p for p in m_sem.pendencias if p.bloqueante]
    assert bloqueantes_sem == [], (
        f"{GHE_PNOS_SEM_MEDICAO}: PNOS sem medição não deve bloquear "
        f"(faixa 'sem' é válida no Quadro 2), tem: {bloqueantes_sem}"
    )
    rx_linhas_sem = [ln for ln in m_sem.linhas if ln.exame == "rx_torax_oit"]
    assert len(rx_linhas_sem) >= 1, (
        f"{GHE_PNOS_SEM_MEDICAO}: deveria ter ≥1 linha rx_torax_oit (faixa sem → 60M)"
    )
    for ln in rx_linhas_sem:
        assert ln.periodicidade_meses == 60, (
            f"{GHE_PNOS_SEM_MEDICAO}: rx_torax_oit deveria ter periodicidade=60 "
            f"(R-RX-01-pnos-sem), got {ln.periodicidade_meses}"
        )

    # --- Adm-03: bloqueante por ruído aguardando medição (não por PNOS quebrado) ---
    m_adm03 = _matriz("Adm-03")
    bloqueantes_adm03 = [p for p in m_adm03.pendencias if p.bloqueante]
    assert len(bloqueantes_adm03) >= 1, (
        "Adm-03: deveria ter ≥1 pendência bloqueante (ruído sem quantificação)"
    )
    assert any(
        "Ruído" in p.motivo or "ruido" in p.motivo.lower()
        for p in bloqueantes_adm03
    ), (
        f"Adm-03: bloqueio deveria referenciar ruído/quantificação, "
        f"motivos encontrados: {[p.motivo for p in bloqueantes_adm03]}"
    )


def diagnostico_zona_cinza() -> None:
    """Diagnóstico NÃO-assertivo dos GHEs com sílica ou MEK coabitando PNOS.

    Relata para cada GHE em GHES_PNOS_ZONA_CINZA:
    - se bloqueou (sim/não)
    - tipo + motivo + regra_origem de cada pendência bloqueante
    - nº de linhas rx_torax_oit emitidas e suas periodicidades

    Sem asserções. Saída: stdout. Rodar via:
        python agente_medico/tests/test_integracao_viverde.py
    """
    resultado = _executar()

    print("\n=== DIAGNÓSTICO ZONA CINZA (002.Z) ===")
    for rid in sorted(GHES_PNOS_ZONA_CINZA):
        m = next((x for x in resultado.matrizes if x.ghe_id == rid), None)
        if m is None:
            print(f"\n--- {rid}: NÃO ENCONTRADO ---")
            continue

        bloqueantes = [p for p in m.pendencias if p.bloqueante]
        rx_linhas = [ln for ln in m.linhas if ln.exame == "rx_torax_oit"]

        print(f"\n--- {rid} ---")
        print(f"  bloqueou: {len(bloqueantes) > 0}")
        for p in bloqueantes:
            print(f"  [BLOQUEANTE]")
            print(f"    tipo         : {p.tipo!r}")
            print(f"    regra_origem : {p.regra_origem!r}")
            print(f"    motivo       : {p.motivo}")
        print(f"  rx_torax_oit emitidos: {len(rx_linhas)}")
        for ln in rx_linhas:
            regras = [mo.regra_id for mo in ln.motivos]
            print(f"    periodicidade={ln.periodicidade_meses}M | regras={regras}")

    print("\n=== FIM DIAGNÓSTICO ===\n")


if __name__ == "__main__":
    diagnostico_zona_cinza()
