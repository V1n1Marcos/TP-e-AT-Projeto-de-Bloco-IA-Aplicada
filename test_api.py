import requests

BASE_URL = "http://127.0.0.1:8000"

print("1. Testando Status da API (GET /)...")
r1 = requests.get(f"{BASE_URL}/")
print(r1.status_code, r1.json())

print("\n2. Testando Inferência Local com Sucesso (POST /processar_texto)...")
r2 = requests.post(f"{BASE_URL}/processar_texto", json={
    "texto": "A energia solar e eólica trazem grande economia e sustentabilidade para o Brasil."
})
print(r2.status_code, r2.json())

print("\n3. Testando Tratamento de Erro - Texto Inválido (400/422)...")
r3 = requests.post(f"{BASE_URL}/processar_texto", json={"texto": "   "})
print(r3.status_code, r3.json())

print("\n4. Testando Tratamento de Erro - UF Inexistente (404)...")
r4 = requests.get(f"{BASE_URL}/dados/capacidade?uf=XX")
print(r4.status_code, r4.json())