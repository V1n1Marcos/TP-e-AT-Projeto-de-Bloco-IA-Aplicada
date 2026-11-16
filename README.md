# 🌱 Projeto: Análise e Inteligência em Energia Renovável no Brasil (TP4)

Plataforma analítica orientada a serviços desenvolvida sob a metodologia **CRISP-DM** para análise da matriz elétrica renovável brasileira, integrando **Streamlit (Multipáginas)**, **FastAPI**, **Web Scraping (BeautifulSoup)** e **Processamento de Linguagem Natural (NLP) offline com HuggingFace Transformers**.

---

## 📑 Documentação Oficial do Projeto
- 📜 **[Project Charter](Project%20Charter.md):** Escopo, reavaliação do problema de negócio, justificativa técnica sobre o não uso de Selenium e roadmap de IA.
- 📊 **[Data Summary Report (v1.0)](Data%20Summary%20Report.md):** Dicionário e detalhamento técnico das bases da ANEEL, pipeline de scraping da UFPR e contratos JSON da API.

---

## 🧠 Arquitetura de IA Local (TP4)
- **Modelo Utilizado:** `lxyuan/distilbert-base-multilingual-cased-sentiments-student`
- **Justificativa Técnica:** Arquitetura leve (~540 MB) baseada em DistilBERT multilíngue com suporte nativo ao português, permitindo inferência rápida diretamente em CPU sem dependência de GPUs dedicadas ou serviços externos em nuvem (`local_files_only=True`).
- **Validação Estrita (Pydantic):** Todas as rotas utilizam *Request* e *Response Models* tipados (`ProcessamentoTextoResponse`, `CapacidadeResponse`, etc.).
- **Tratamento Robusto de Erros:** Exception handlers globais padronizam respostas de erro (`ErroDetalhadoResponse`) com diagnóstico e sugestão de correção para códigos `400`, `404`, `422`, `500`, `503` (modelo não carregado) e `504` (timeout de inferência).

---

## 🏗️ Estrutura do Repositório
```text
├── app.py                     # Interface principal Streamlit com st.navigation
├── api.py                     # Backend RESTful FastAPI com NLP local e Exception Handlers
├── baixar_modelo.py           # Script para download e persistência offline do modelo HF
├── scrapping.py               # Coleta estática de artigos científicos (UFPR)
├── test_api.py                # Suíte automatizada de testes de rotas e exceções HTTP
├── Project Charter.md         # Termo de Abertura e Decisões Arquiteturais
├── Data Summary Report.md     # Relatório Técnico das Fontes de Dados
├── requirements.txt           # Dependências do projeto
└── data/                      # Armazenamento local (CSVs da ANEEL e corpus TXT)