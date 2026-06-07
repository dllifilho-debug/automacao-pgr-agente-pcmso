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
from agente_medico.tests.invariantes import auditar_invariante_piso_teto
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
    # Fatia 3 (D-ARQ-31 cláusula 3): a pendência do ruído tem âncora 'audiometria',
    # que é emitida → anexa à linha, não fica solta na matriz. Asserção mira a linha.
    m_adm03 = _matriz("Adm-03")
    anexadas_adm03 = [
        p
        for ln in m_adm03.linhas
        if ln.exame == "audiometria"
        for p in ln.pendencias_anexadas
        if p.bloqueante
    ]
    assert len(anexadas_adm03) >= 1, (
        "Adm-03: linha audiometria deveria carregar ≥1 pendência bloqueante anexada "
        "(ruído sem quantificação)"
    )
    assert any(
        "Ruído" in p.motivo or "ruido" in p.motivo.lower()
        for p in anexadas_adm03
    ), (
        f"Adm-03: bloqueio anexado deveria referenciar ruído/quantificação, "
        f"motivos: {[p.motivo for p in anexadas_adm03]}"
    )
    # espelho do Acab-05: a pendência do ruído NÃO resta solta na matriz (moveu p/ linha)
    soltas_ruido_adm03 = [
        p for p in m_adm03.pendencias
        if p.bloqueante and ("ruído" in p.motivo.lower() or "ruido" in p.motivo.lower())
    ]
    assert soltas_ruido_adm03 == [], (
        f"Adm-03: pendência de ruído não deveria restar solta na matriz: "
        f"{[p.regra_origem for p in soltas_ruido_adm03]}"
    )


def test_acab05_pendencia_silica_anexada_a_linha_rx() -> None:
    # D-ARQ-31 fatia 3, caso-âncora Acab-05. Saída real diagnostico_zona_cinza (003.D):
    # sílica sem fração → 5 pendências família R-RX-01-{adm,sem,baixa,media,alta};
    # PNOS >100% LEO → 1 linha rx_torax_oit 60M (R-RX-01-pnos-acima100).
    # Fatia 3: as 5 pendências saem da matriz e anexam-se à linha de RX.
    resultado = _executar()
    m = next(x for x in resultado.matrizes if x.ghe_id == "Acab-05")
    rx = [ln for ln in m.linhas if ln.exame == "rx_torax_oit"]
    assert len(rx) == 1
    linha = rx[0]
    assert linha.periodicidade_meses == 60

    familia_silica = {
        "R-RX-01-adm", "R-RX-01-sem", "R-RX-01-baixa",
        "R-RX-01-media", "R-RX-01-alta",
    }
    anexadas = {p.regra_origem for p in linha.pendencias_anexadas if p.bloqueante}
    assert familia_silica <= anexadas, (
        f"Acab-05: pendências da sílica deveriam estar anexadas à linha RX, "
        f"anexadas: {anexadas}"
    )
    # e NÃO restam soltas no nível da matriz
    soltas = {
        p.regra_origem for p in m.pendencias
        if p.bloqueante and p.regra_origem in familia_silica
    }
    assert soltas == set(), f"Acab-05: família sílica não deveria estar solta: {soltas}"
    assert m.status == "PARCIAL"


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
        print(f"  status   : {m.status}")
        print(f"  bloqueou (solto na matriz): {len(bloqueantes) > 0}")
        for p in bloqueantes:
            print(f"  [BLOQUEANTE SOLTO]")
            print(f"    tipo         : {p.tipo!r}")
            print(f"    regra_origem : {p.regra_origem!r}")
            print(f"    motivo       : {p.motivo}")
        print(f"  rx_torax_oit emitidos: {len(rx_linhas)}")
        for ln in rx_linhas:
            regras = [mo.regra_id for mo in ln.motivos]
            anexadas = [p.regra_origem for p in ln.pendencias_anexadas if p.bloqueante]
            print(f"    periodicidade={ln.periodicidade_meses}M | regras={regras}")
            print(f"    pendencias_anexadas (bloqueantes): {anexadas}")

    print("\n=== FIM DIAGNÓSTICO ===\n")


# === D-ARQ-31 FATIA 4 — auditor da invariante + regressão tri-estado ===

GHES_SILICA_ANEXADA = {"Acab-06", "Acab-08", "Est-07"}
FAMILIA_SILICA = {
    "R-RX-01-adm", "R-RX-01-sem", "R-RX-01-baixa",
    "R-RX-01-media", "R-RX-01-alta",
}


def test_auditor_invariante_piso_teto_global_viverde() -> None:
    # D-ARQ-31 cláusula 3: rede global sobre o Resultado inteiro. Sobre saída real
    # é sempre [] (anexar_pendencias garante por construção); dispara só se uma
    # fatia futura regredir a anexação. Rede contra regressão silenciosa.
    resultado = _executar()
    violacoes = auditar_invariante_piso_teto(resultado)
    assert violacoes == [], (
        f"invariante piso-sem-teto violada em: "
        f"{[(v.ghe_id, v.exame, v.regra_origem) for v in violacoes]}"
    )


def test_tri_estado_32_ghes_forma() -> None:
    # Congela a forma do vetor tri-estado dos 32 GHEs pós-fatia-3. Determinístico:
    # motor puro (D-ARQ-09) + fixture e HOJE_FIXO congelados. Assere invariantes
    # derivadas do diagnóstico real (003.E), não números cegos de 27 GHEs não medidos:
    #   - soma dos três estados == 32 (todo GHE tem exatamente um status)
    #   - PARCIAL >= 4 (Acab-05/06/08, Est-07 — sílica anexada à linha rx)
    #   - VÁLIDA >= 1 (Est-08 — controle PNOS sem sílica)
    #   - BLOQUEADA == 0 (PRELIMINAR global vem de PARCIAL; sem bloqueio solto medido)
    resultado = _executar()
    contagem = {"VÁLIDA": 0, "PARCIAL": 0, "BLOQUEADA": 0}
    for m in resultado.matrizes:
        contagem[m.status] += 1
    assert sum(contagem.values()) == 32, f"esperado 32 GHEs, got {contagem}"
    assert contagem["PARCIAL"] >= 4, (
        f"esperado >=4 PARCIAL (zona cinza sílica×PNOS), got {contagem}"
    )
    assert contagem["VÁLIDA"] >= 1, (
        f"esperado >=1 VÁLIDA (Est-08 controle), got {contagem}"
    )
    assert contagem["BLOQUEADA"] == 0, (
        f"esperado 0 BLOQUEADA (PRELIMINAR vem de PARCIAL), got {contagem}"
    )


def test_zona_cinza_silica_anexada_a_linha_rx() -> None:
    # Generaliza test_acab05_pendencia_silica_anexada_a_linha_rx aos demais GHEs
    # sílica×PNOS. Asserção ESTRUTURAL (linha presente + família anexada + não-solta
    # + PARCIAL), SEM cravar periodicidade — 0M/60M só Acab-05 testa.
    resultado = _executar()
    for rid in sorted(GHES_SILICA_ANEXADA):
        m = next((x for x in resultado.matrizes if x.ghe_id == rid), None)
        assert m is not None, f"GHE {rid} não encontrado"
        rx = [ln for ln in m.linhas if ln.exame == "rx_torax_oit"]
        assert len(rx) >= 1, f"{rid}: deveria ter >=1 linha rx_torax_oit"
        anexadas = {
            p.regra_origem
            for ln in rx
            for p in ln.pendencias_anexadas
            if p.bloqueante
        }
        assert FAMILIA_SILICA <= anexadas, (
            f"{rid}: família sílica deveria estar anexada à linha rx, got {anexadas}"
        )
        soltas = {
            p.regra_origem for p in m.pendencias
            if p.bloqueante and p.regra_origem in FAMILIA_SILICA
        }
        assert soltas == set(), (
            f"{rid}: família sílica não deveria restar solta na matriz, got {soltas}"
        )
        assert m.status == "PARCIAL", f"{rid}: esperado PARCIAL, got {m.status}"


def test_est08_controle_pnos_sem_silica_valida() -> None:
    # Est-08: PNOS sem sílica coabitando. Emite linha rx pela faixa branda
    # (pnos-ate10), MAS sem família sílica anexada → VÁLIDA. Prova que a anexação
    # é dirigida por sílica, não por PNOS (a linha rx existe nos dois; a família
    # anexada só onde há sílica).
    resultado = _executar()
    m = next((x for x in resultado.matrizes if x.ghe_id == "Est-08"), None)
    assert m is not None, "GHE Est-08 não encontrado"
    rx = [ln for ln in m.linhas if ln.exame == "rx_torax_oit"]
    assert len(rx) >= 1, "Est-08: deveria ter >=1 linha rx_torax_oit (faixa PNOS branda)"
    anexadas = {
        p.regra_origem
        for ln in rx
        for p in ln.pendencias_anexadas
        if p.bloqueante
    }
    assert anexadas == set(), (
        f"Est-08: linha rx não deveria ter família sílica anexada, got {anexadas}"
    )
    bloqueantes_soltos = [p for p in m.pendencias if p.bloqueante]
    assert bloqueantes_soltos == [], (
        f"Est-08: não deveria ter bloqueante solto, got {bloqueantes_soltos}"
    )
    assert m.status == "VÁLIDA", f"Est-08: esperado VÁLIDA, got {m.status}"


if __name__ == "__main__":
    diagnostico_zona_cinza()
