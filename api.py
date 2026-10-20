from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pandas as pd
import os

app = FastAPI(
    title="API de Energia Renovável",
    description="API para consulta de dados de capacidade instalada da ANEEL e submissão de dados/feedbacks.",
    version="1.0.0"
)

# Modelo Pydantic para validação do POST
class NovoRegistro(BaseModel):
    uf: str
    fonte: str
    capacidade_mw: float
    ano: int

# Rota 1 (GET): Boas-vindas e status da API
@app.get("/")
def home():
    return {
        "status": "API Online",
        "mensagem": "Bem-vindo à API de Energia Renovável no Brasil",
        "endpoints": ["/docs", "/dados/capacidade", "/dados/resumo-texto"]
    }

# Rota 2 (GET): Consulta de dados filtrados por UF
@app.get("/dados/capacidade")
def obter_capacidade(uf: str = None):
    caminho_csv = "data/capacidade-instalada-geracao-uf.csv"
    if not os.path.exists(caminho_csv):
        raise HTTPException(status_code=404, detail="Arquivo de dados não encontrado.")
    
    df = pd.read_csv(caminho_csv, encoding="latin1", sep=';')
    
    # Procura coluna de UF na tabela
    col_uf = [c for c in df.columns if 'SigUF' in c or 'UF' in c]
    if uf and col_uf:
        df = df[df[col_uf[0]].str.upper() == uf.upper()]
        
    return {
        "total_registros": len(df),
        "uf_filtrada": uf,
        "dados": df.head(100).to_dict(orient="records")
    }

# Rota 3 (GET): Retorna o texto coletado via Web Scraping (Apoio para futura LLM)
@app.get("/dados/resumo-texto")
def obter_texto_scraping():
    caminho_txt = "data/textos_web.txt"
    if not os.path.exists(caminho_txt):
        raise HTTPException(status_code=404, detail="Texto extraído não encontrado.")
    
    with open(caminho_txt, "r", encoding="utf-8") as f:
        conteudo = f.read()
        
    return {
        "tamanho_caracteres": len(conteudo),
        "amostra": conteudo[:500],
        "conteudo_completo": conteudo
    }

# Rota 4 (POST): Envio de novos dados de potencial energético
@app.post("/dados/registrar")
def registrar_dados(registro: NovoRegistro):
    return {
        "status": "Sucesso",
        "mensagem": f"Registro recebido com sucesso para a UF {registro.uf}.",
        "dados_recebidos": registro
    }