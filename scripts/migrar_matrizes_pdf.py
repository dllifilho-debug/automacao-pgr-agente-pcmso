import fitz  # PyMuPDF
import re
import json
import os

# Caminho para um dos PDFs padrão RQ.61 que você enviou
CAMINHO_PDF = "MATRIZ DE EXAMES(ATUALIZAÇÃO)CMO RESIDENCIAL VISTAMERICA 08.12.25.pdf"
CAMINHO_JSON = "data/banco_matrizes_v2.json"

def normalizar_texto(texto):
    if not texto: return ""
    # Remove acentos e caracteres especiais para padronizar a chave
    texto = re.sub(r'[^\w\s]', '', texto)
    return texto.strip().upper().replace(" ", "_")

def extrair_matriz_do_pdf(caminho_pdf):
    print(f"Lendo o documento: {caminho_pdf}...")
    doc = fitz.open(caminho_pdf)
    texto_completo = ""
    
    for pagina in doc:
        texto_completo += pagina.get_text("text") + "\n"
        
    doc.close()

    # Padrões Regex para identificar GHEs e os Exames
    # Procura por "GHE XX - NOME DO GHE"
    padrao_ghe = re.compile(r'(GHE\s+\d+\s*[-–]\s*[^\n]+)', re.IGNORECASE)
    
    banco_atualizado = {}
    blocos = padrao_ghe.split(texto_completo)
    
    ghe_atual = None

    for bloco in blocos:
        bloco = bloco.strip()
        if not bloco:
            continue
            
        # Se o bloco for o título do GHE (ex: "GHE 01 - BETONEIRA")
        if padrao_ghe.match(bloco):
            ghe_atual = normalizar_texto(bloco)
            continue
            
        # Se for o conteúdo abaixo do GHE (Cargos e Exames)
        if ghe_atual and "Exame Clinico" in bloco:
            # Divide por linhas para tentar isolar os cargos. 
            # Como o PDF tem "Cargo Exame Clínico (ADM...)", separamos antes do "Exame"
            linhas = re.split(r'(?=[A-Z][a-z]+\s*Exame Clinico|Exame Clínico)', bloco)
            
            for linha in linhas:
                if "Exame " not in linha:
                    continue
                
                # O cargo geralmente é o texto antes de "Exame Clinico"
                partes = re.split(r'Exame Cl[ií]nico', linha, maxsplit=1)
                cargo_bruto = partes[0].strip().split('\n')[-1] # Pega a última linha antes do exame
                
                if not cargo_bruto or len(cargo_bruto) < 3:
                    continue
                    
                cargo_norm = normalizar_texto(cargo_bruto)
                chave_composta = f"{ghe_atual}_{cargo_norm}"
                
                # Estrutura base de exames (podemos sofisticar o regex para extrair os outros, 
                # mas aqui garantimos o esqueleto)
                exames = [
                    {"nome": "Exame Clínico", "adm": True, "per": "12", "mro": True, "ret": True, "dem": True}
                ]
                
                if "Audiometria" in partes[1]:
                    exames.append({"nome": "Audiometria", "adm": True, "per": "12", "mro": True, "ret": False, "dem": True})
                if "Espirometria" in partes[1]:
                    exames.append({"nome": "Espirometria", "adm": True, "per": "24", "mro": True, "ret": False, "dem": True})
                if "RX de Tórax" in partes[1] or "Raio X" in partes[1]:
                    exames.append({"nome": "Radiografia de Tórax (OIT)", "adm": True, "per": "12", "mro": True, "ret": False, "dem": True})

                # Injeta no dicionário
                banco_atualizado[chave_composta] = {
                    "descricao": f"Importado via PDF RQ.61 - {cargo_bruto.title()}",
                    "riscos_base": ["Riscos a validar com PGR"],
                    "exames": exames
                }

    return banco_atualizado

def atualizar_banco(novos_dados):
    # Carrega o JSON existente
    if os.path.exists(CAMINHO_JSON):
        with open(CAMINHO_JSON, 'r', encoding='utf-8') as f:
            try:
                banco_atual = json.load(f)
            except json.JSONDecodeError:
                banco_atual = {}
    else:
        banco_atual = {}

    # Mescla os dados
    banco_atual.update(novos_dados)

    # Salva
    with open(CAMINHO_JSON, 'w', encoding='utf-8') as f:
        json.dump(banco_atual, f, indent=2, ensure_ascii=False)
    
    print(f"Sucesso! {len(novos_dados)} chaves compostas injetadas no banco.")

if __name__ == "__main__":
    dados_extraidos = extrair_matriz_do_pdf(CAMINHO_PDF)
    atualizar_banco(dados_extraidos)
