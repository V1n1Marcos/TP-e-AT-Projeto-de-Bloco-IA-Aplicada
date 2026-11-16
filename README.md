# 🌱 Projeto: Análise do Potencial de Energia Renovável no Brasil (Fase 3 - TP3)

Plataforma analítica e orientada a serviços desenvolvida sob a metodologia **CRISP-DM** para análise da matriz elétrica renovável brasileira, integrando **Streamlit (Multipáginas)**, **FastAPI**, **Web Scraping (BeautifulSoup)** e preparação para **LLMs**.

## 📑 Documentação Oficial do Projeto
- 📜 **[Project Charter](PROJECT_CHARTER.md):** Escopo, reavaliação do problema de negócio, justificativa técnica sobre o não uso de Selenium e roadmap de IA Generativa.
- 📊 **[Data Summary Report (v1.0)](DATA_SUMMARY_REPORT.md):** Dicionário e detalhamento técnico das bases da ANEEL, pipeline de scraping da UFPR e contratos JSON da API.

## 🏗️ Estrutura do Repositório
```text
├── app.py                   # Aplicação principal Streamlit com st.navigation
├── api.py                   # Backend RESTful com FastAPI (4 rotas documentadas)
├── scrapping.py             # Extração estática de artigos científicos (UFPR)
├── PROJECT_CHARTER.md       # Termo de Abertura e Decisões Arquiteturais
├── DATA_SUMMARY_REPORT.md   # Relatório Técnico das Fontes de Dados
├── requirements.txt         # Dependências do ambiente
└── data/                    # Diretório de armazenamento local (CSVs e TXT)