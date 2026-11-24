from transformers import AutoTokenizer, AutoModelForSequenceClassification, AutoModelForSeq2SeqLM
import os

# 1. Modelo de Classificação de Sentimento (TP4)
MODELO_SENTIMENTO = "lxyuan/distilbert-base-multilingual-cased-sentiments-student"
PASTA_SENTIMENTO = "./modelo_local"

print(f"1/2 - Verificando/baixando modelo de sentimento '{MODELO_SENTIMENTO}'...")
os.makedirs(PASTA_SENTIMENTO, exist_ok=True)
AutoTokenizer.from_pretrained(MODELO_SENTIMENTO).save_pretrained(PASTA_SENTIMENTO)
AutoModelForSequenceClassification.from_pretrained(MODELO_SENTIMENTO).save_pretrained(PASTA_SENTIMENTO)
print(f"✅ Salvo em: {os.path.abspath(PASTA_SENTIMENTO)}\n")

# 2. Modelo de Sumarização Abstrativa em Português (AT - Opção 2)
MODELO_SUMARIZACAO = "recogna-nlp/ptt5-base-summ-cstnews"
PASTA_SUMARIZACAO = "./modelo_sumarizacao"

print(f"2/2 - Baixando modelo de sumarização '{MODELO_SUMARIZACAO}' para o ambiente local...")
os.makedirs(PASTA_SUMARIZACAO, exist_ok=True)
AutoTokenizer.from_pretrained(MODELO_SUMARIZACAO).save_pretrained(PASTA_SUMARIZACAO)
AutoModelForSeq2SeqLM.from_pretrained(MODELO_SUMARIZACAO).save_pretrained(PASTA_SUMARIZACAO)
print(f"✅ Salvo em: {os.path.abspath(PASTA_SUMARIZACAO)}")