from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os

# Modelo leve (~540MB), rápido em CPU e com suporte nativo ao Português
MODELO_HF = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
PASTA_LOCAL = "./modelo_local"

print(f"Baixando o modelo '{MODELO_HF}' para o ambiente local...")
os.makedirs(PASTA_LOCAL, exist_ok=True)

tokenizer = AutoTokenizer.from_pretrained(MODELO_HF)
model = AutoModelForSequenceClassification.from_pretrained(MODELO_HF)

# Salva os arquivos físicos no disco para execução 100% offline
tokenizer.save_pretrained(PASTA_LOCAL)
model.save_pretrained(PASTA_LOCAL)

print(f"Sucesso! Modelo salvo localmente em: {os.path.abspath(PASTA_LOCAL)}")