import pandas as pd
import json
import os
import re

# Caminho do arquivo Excel na raiz (ajuste se mudou o nome)
CAMINHO_EXCEL = "Matriz função- risco-exames - validado Dra. Patrícia 06.2025.xlsx"
CAMINHO_JSON_RISCOS = "data/banco_riscos_nr7.json"

def limpar_texto(t):
    if pd.isna(t): return ""
    return str(t).strip().upper()

def extrair_meses(texto):
    if not texto: return "12"
    nums = re.findall(r'\d+', str(texto))
    return nums[0] if nums else "12"

def migrar_riscos():
    print(f"Lendo regras de riscos do Excel: {CAMINHO_EXCEL}...")
    
    # Lendo a aba específica de periodicidade
    # Nota: Se der erro de 'Sheet not found', verifique o nome exato da aba no seu Excel
    try:
        df = pd.read_excel(CAMINHO_EXCEL, sheet_name='Periodicidade Exames', skiprows=3)
    except:
        # Fallback caso o nome da aba seja diferente
        df = pd.read_excel(CAMINHO_EXCEL, skiprows=3)

    banco_riscos = {}

    for _, row in df.iterrows():
        risco_raw = limpar_texto(row.get('RISCOS'))
        exame = limpar_texto(row.get('EXAME'))
        
        if not risco_raw or not exame:
            continue

        # Normaliza o risco (ex: 'TRABALHO EM ALTURA/ESPAÇO CONFINADO' vira lista)
        nomes_risco = [r.strip() for r in risco_raw.replace('/', ',').split(',')]
        
        for nome in nomes_risco:
            if nome not in banco_riscos:
                banco_riscos[nome] = []
            
            # Monta a regra do exame para este risco
            regra = {
                "exame": exame.title(),
                "adm": True if limpar_texto(row.get('ADM')) == 'X' else False,
                "per": extrair_meses(row.get('PERIODICO')),
                "dem": True if limpar_texto(row.get('DEMISSIONAL')) == 'X' else False,
                "mro": True if limpar_texto(row.get('MUD. R. OCUP.')) == 'X' else False
            }
            
            banco_riscos[nome].append(regra)

    # Salva o banco de riscos
    os.makedirs(os.path.dirname(CAMINHO_JSON_RISCOS), exist_ok=True)
    with open(CAMINHO_JSON_RISCOS, 'w', encoding='utf-8') as f:
        json.dump(banco_riscos, f, indent=2, ensure_ascii=False)
    
    print(f"Sucesso! {len(banco_riscos)} regras de riscos mapeadas em {CAMINHO_JSON_RISCOS}.")

if __name__ == "__main__":
    migrar_riscos()