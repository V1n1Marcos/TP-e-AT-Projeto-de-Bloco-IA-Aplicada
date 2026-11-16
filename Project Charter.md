# 📜 Project Charter — Plataforma de Análise e Inteligência em Energia Renovável

**Versão:** 2.0 (Fase TP3)  
**Responsável Técnico / Analista:** Vinicius Marcos de Oliveira  
**Orientador / Stakeholder Avaliador:** Prof. Renan Silva Santos  
**Metodologia:** CRISP-DM (Cross-Industry Standard Process for Data Mining)

---

## 1. Reavaliação do Problema de Negócio (Visão TP3)
A matriz energética cotidiana ainda apresenta forte dependência de fontes tradicionais e combustíveis fósseis, gerando vulnerabilidade tarifária e impactos ambientais. Inicialmente concebido apenas como um painel descritivo estático, o projeto foi reavaliado à luz de arquiteturas modernas de engenharia de dados e APIs (`FastAPI`). 

O novo problema de negócio consiste não apenas em exibir dados históricos, mas em **desacoplar a camada de dados da interface visual**, criando um ecossistema interoperável onde dados públicos (ANEEL) e literatura técnica (UFPR) possam ser consumidos via endpoints RESTful tanto por aplicações web quanto por futuros agentes baseados em Modelos de Linguagem (LLMs) para traduzir indicadores complexos em recomendações acessíveis ao consumidor residencial.

---

## 2. Objetivos e Metas Ajustadas
- **Objetivo Geral:** Prover uma plataforma analítica escalável e orientada a serviços que democratize o acesso a dados sobre geração de energia renovável no Brasil, alinhada aos **ODS 7, 12 e 13 da ONU**.
- **Metas Específicas (Atualizadas):**
  1. **Desacoplamento de Arquitetura:** Disponibilizar os dados tratados através de uma API RESTful (`FastAPI`) com rotas documentadas de leitura (`GET`) e ingestão (`POST`).
  2. **Experiência Interativa Multipáginas:** Estruturar a interface em `Streamlit` com navegação nativa (`st.navigation`), filtros dinâmicos por UF e Ano de Referência, cache e persistência de sessão.
  3. **Extração Otimizada de Conhecimento:** Coletar e estruturar literatura acadêmica sobre energias renováveis para análise lexical e futura indexação semântica.
  4. **Preparação para IA Generativa:** Estruturar payloads JSON e corpus textuais prontos para integração com LLMs na fase final do projeto.

---

## 3. Decisões Arquiteturais e Justificativa Técnica (Web Scraping)
### Por que o Selenium NÃO foi utilizado?
Durante a etapa de coleta de dados não estruturados, avaliou-se o uso do `Selenium` para automação de navegador. Contudo, após inspeção do código-fonte e do comportamento de rede da fonte alvo — o portal da **Revista Brasileira de Energias Renováveis (UFPR)** baseado no sistema OJS (*Open Journal Systems*) — constatou-se que **a página é renderizada de forma estática no servidor (SSR/HTML puro)**, sem dependência de execução de JavaScript assíncrono (SPA) ou interação com formulários dinâmicos para exibir títulos, resumos e metadados.

Dessa forma, seguindo o princípio de engenharia de manter a simplicidade e eficiência computacional, optou-se pela combinação de **`requests` (com headers de User-Agent) + `BeautifulSoup4`**, eliminando a sobrecarga de memória e dependências de WebDrivers externos que o Selenium exigiria em ambiente de produção/deploy.

---

## 4. Casos de Uso Planejados para LLMs (Próxima Fase)
A estrutura atual de dados e rotas da API foi desenhada para viabilizar quatro frentes de IA Generativa na etapa subsequente:
1. **Sumarização Automática (Text Summarization):** Utilização de LLMs conectadas ao endpoint `GET /dados/resumo-texto` para sintetizar artigos acadêmicos longos em linguagem simples voltada a consumidores residenciais.
2. **Perguntas e Respostas sobre Dados Energéticos (RAG / Q&A):** Combinação dos registros tabulares da ANEEL (`GET /dados/capacidade`) com embeddings textuais para permitir consultas em linguagem natural sobre o potencial solar e eólico de cada estado.
3. **Geração Automatizada de Insights e Relatórios:** Criação de diagnósticos personalizados por Unidade Federativa, cruzando capacidade instalada histórica com dicas práticas de eficiência energética.
4. **Classificação de Sentimentos e Feedbacks:** Análise automatizada de percepções e relatos de consumidores submetidos à plataforma através da rota `POST /dados/registrar`.

---

## 5. Escopo e Entregáveis da Fase Atual
- **Incluído no Escopo:** Aplicação Streamlit multipáginas (`app.py`), Backend RESTful (`api.py`), Pipeline de Web Scraping estático (`scrapping.py`), Base de dados local organizada (`data/`), `Project Charter` e `Data Summary Report v1.0`.
- **Fora do Escopo (Previsto para Fase 4 / AT):** Inferência ativa de modelos LLM em produção e deploy em nuvem pública.