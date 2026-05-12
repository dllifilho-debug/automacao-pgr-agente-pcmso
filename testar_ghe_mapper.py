"""
testar_ghe_mapper.py
Rode localmente ou no terminal do Streamlit Cloud:

    python testar_ghe_mapper.py

Requisitos:
    SUPABASE_URL e SUPABASE_KEY nas variáveis de ambiente
    (ou num arquivo .env na raiz do projeto)
"""
import os
import sys

# --- tenta carregar .env local se existir
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

URL = os.getenv("SUPABASE_URL")
KEY = os.getenv("SUPABASE_KEY")

# ─────────────────────────────────────────────────
# 1. Verifica credenciais
# ─────────────────────────────────────────────────
print("\n=== TESTE GHE MAPPER ===")
print(f"SUPABASE_URL : {'✅ ' + URL[:40] + '...' if URL else '❌ NÃO DEFINIDA'}")
print(f"SUPABASE_KEY : {'✅ definida (' + str(len(KEY)) + ' chars)' if KEY else '❌ NÃO DEFINIDA'}")

if not URL or not KEY:
    print("\n❌ Configure SUPABASE_URL e SUPABASE_KEY antes de rodar.")
    sys.exit(1)

# ─────────────────────────────────────────────────
# 2. Conecta ao Supabase
# ─────────────────────────────────────────────────
try:
    from supabase import create_client
    sb = create_client(URL, KEY)
    print("\n✅ Conexão com Supabase OK")
except Exception as e:
    print(f"\n❌ Falha ao conectar: {e}")
    sys.exit(1)

# ─────────────────────────────────────────────────
# 3. Lê tabela ghe_mapeamentos
# ─────────────────────────────────────────────────
try:
    res = sb.table("ghe_mapeamentos").select("*").execute()
    registros = res.data or []
    print(f"✅ Tabela ghe_mapeamentos acessível — {len(registros)} registro(s) encontrado(s)")
except Exception as e:
    print(f"❌ Erro ao ler ghe_mapeamentos: {e}")
    sys.exit(1)

if not registros:
    print("⚠️  Tabela vazia — rode o seed SQL novamente.")
    sys.exit(1)

# ─────────────────────────────────────────────────
# 4. Testa buscar_match com os 6 GHEs do Viverde
# ─────────────────────────────────────────────────
sys.path.insert(0, os.path.dirname(__file__))
from utils.ghe_mapper import buscar_match, carregar_mapeamentos

# Simula Streamlit ausente
mapeamentos = registros  # usa direto sem cache

TESTE_GHE = [
    "GHE 01- Engenharia planejamento de obra",
    "GHE 02 - Segurança do trabalho",
    "GHE 03 - Execução de obra",
    "GHE 04 - Supervisão Rejunte/limpeza",
    "GHE 05 - Administração de campo",
    "GHE 06 - Almoxarifado",
]

print("\n--- Resultados de buscar_match() ---")
ok = 0
fail = 0
for desc in TESTE_GHE:
    # Remove prefixo "GHE XX - " para testar só o nome
    nome = desc.split("-", 1)[-1].strip() if "-" in desc else desc
    match = buscar_match(nome, mapeamentos)
    if match:
        print(f"  ✅ '{nome}'")
        print(f"       → {match['matriz_titulo']}")
        print(f"       → cargos: {match['cargos']}")
        print(f"       → score: {match['score']} [{match['metodo']}]")
        ok += 1
    else:
        print(f"  ❌ '{nome}' → SEM MATCH")
        fail += 1

print(f"\n=== RESULTADO: {ok}/6 matches ({'✅ TUDO OK' if fail == 0 else '⚠️ ' + str(fail) + ' falha(s)'}) ===")
