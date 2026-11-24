import requests

BASE_URL = "http://127.0.0.1:8000"

print("1. Testando Status da API (GET /)...")
r1 = requests.get(f"{BASE_URL}/")
print(r1.status_code, r1.json())

print("\n2. Testando Classificação de Sentimento Local (POST /processar_texto)...")
r2 = requests.post(f"{BASE_URL}/processar_texto", json={
    "texto": "A energia solar e eólica trazem grande economia e sustentabilidade para o Brasil."
})
print(r2.status_code, r2.json())

print("\n3. Testando Automação de Sumarização Local (POST /sumarizar_texto)...")
texto_longo = (
    "A transição energética no Brasil tem sido impulsionada pelo crescimento acelerado das fontes "
    "solar fotovoltaica e eólica, especialmente na região Nordeste. Estudos acadêmicos apontam que "
    "a diversificação da matriz elétrica reduz a vulnerabilidade hídrica em períodos de seca, diminui "
    "o acionamento de usinas termelétricas movidas a combustíveis fósseis e barateia o custo marginal "
    "de operação, beneficiando diretamente consumidores residenciais e industriais."
)
r3 = requests.post(f"{BASE_URL}/sumarizar_texto", json={"texto": texto_longo})
print(r3.status_code, r3.json())

print("\n4. Testando Tratamento de Erro - Texto Curto na Sumarização (422)...")
r4 = requests.post(f"{BASE_URL}/sumarizar_texto", json={"texto": "Texto curto"})
print(r4.status_code, r4.json())

print("\n5. Testando Tratamento de Erro - UF Inexistente (404)...")
r5 = requests.get(f"{BASE_URL}/dados/capacidade?uf=XX")
print(r5.status_code, r5.json())