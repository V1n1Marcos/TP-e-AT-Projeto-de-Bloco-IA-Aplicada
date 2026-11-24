# 🌱 Plataforma de Inteligência em Energia Renovável & Sustentabilidade (TDSP / AT)

Solução analítica ponta a ponta desenvolvida sob os frameworks **TDSP (Team Data Science Process)** e **CRISP-DM** para democratizar o acesso a indicadores da matriz elétrica renovável brasileira e sintetizar literatura científica sobre transição energética. O sistema integra dados públicos reais da **ANEEL**, coleta automatizada via **Web Scraping (UFPR)**, serviços RESTful em **FastAPI**, modelos de **IA Local (HuggingFace Transformers)** e um **Dashboard Executivo Multipáginas em Streamlit**.

---

## 📑 Documentação Oficial e Evidências
- 📜 **[Project Charter (v3.0)](Project%20Charter.md):** Definição do problema de negócio, alinhamento aos ODS/ESG, ciclo completo do TDSP e justificativa técnica sobre o uso de IA e Engenharia de Prompts.
- 📊 **[Data Summary Report (v2.0)](Data%20Summary%20Report.md):** Inventário das bases reais da ANEEL, pipeline de Web Scraping da UFPR, contratos JSON e fluxo de transformação de dados em insights.
- 🧪 **[Evidência de Testes Automatizados](evidencia_test_api.txt):** Registro real da execução do `test_api.py` validando inferências locais e tratamento de exceções HTTP (`200`, `400`, `404`, `422`).

---

## 🎯 Argumentação da Solução: Problema de Negócio, ESG e ODS

### O Problema de Negócio
Embora o Brasil possua uma das matrizes elétricas mais limpas do mundo, os dados oficiais de capacidade instalada (ANEEL) e os estudos acadêmicos sobre viabilidade fotovoltaica e eólica encontram-se dispersos em arquivos CSV técnicos de difícil leitura e artigos científicos extensos. Essa barreira informacional dificulta a tomada de decisão de consumidores residenciais, pequenos gestores e pesquisadores que buscam reduzir custos tarifários e mitigar impactos ambientais.

### Como a Solução Resolve o Problema e Gera Valor (ESG & ODS)
1. **Ambiental (Environmental — ODS 7 e ODS 13):** Ao cruzar dados reais de expansão solar/eólica por Unidade Federativa com resumos executivos de pesquisas científicas, a plataforma incentiva a adoção de energia limpa e a redução da dependência de termelétricas fósseis.
2. **Social (Social — ODS 7 e ODS 12):** Traduz indicadores complexos em linguagem acessível, permitindo que o cidadão compreenda o potencial energético do seu estado e tome decisões conscientes de consumo e microgeração distribuída.
3. **Governança (Governance):** Implementa rastreabilidade completa dos dados, contratos estritos de validação (`Pydantic`), diagnóstico padronizado de falhas e execução 100% local (*on-premise/offline*), garantindo privacidade, reprodutibilidade e independência de serviços proprietários em nuvem.

---

## 🔄 Ciclo Completo de Ciência de Dados Aplicado (TDSP)

| Etapa do Ciclo | Implementação Técnica | Valor Gerado na Solução |
| :--- | :--- | :--- |
| **1. Coleta e Aquisição** | Ingestão de bases abertas da ANEEL (`capacidade-instalada-geracao-uf.csv` e `siga-empreendimentos-geracao-diario.csv`) + Web Scraping estático (`scrapping.py` via `BeautifulSoup4`) na Revista Brasileira de Energias Renováveis (UFPR). | Combina dados quantitativos oficiais (2006–2026) com embasamento qualitativo científico real. |
| **2. Limpeza e Preparação** | Tratamento de encodings (`latin1`/`utf-8`), conversão de `NaN` para `None` para serialização JSON, desambiguação da coluna `AnoReferencia` e filtragem de ruídos HTML (`<p>`, `<div>`, `<section>`). | Garante integridade referencial, elimina falhas de serialização e otimiza leitura com `@st.cache_data`. |
| **3. Arquitetura de Serviços** | Backend assíncrono em `FastAPI` (`api.py` v5.0.0) com *Response Models* tipados (`Pydantic`) e *Exception Handlers* globais (`400`, `404`, `422`, `500`, `503`, `504`). | Desacopla a lógica de dados e IA da interface visual, permitindo consumo padronizado e seguro. |
| **4. Modelagem e IA Local** | Integração offline de dois modelos HuggingFace: **`PTT5`** (`recogna-nlp/ptt5-base-summ-cstnews`) para sumarização abstrativa (`POST /sumarizar_texto`) e **`DistilBERT`** (`lxyuan/distilbert-base-multilingual-cased-sentiments-student`) para classificação de sentimento (`POST /processar_texto`). | Transforma textos acadêmicos extensos em resumos executivos claros e classifica percepções em tempo real sem custos de nuvem. |
| **5. Apresentação e Decisão** | Dashboard Executivo Multipáginas em `Streamlit` (`st.navigation`) com KPIs do pipeline, gráficos comparativos por UF, Nuvem de Palavras e Laboratório Interativo de IA. | Une simplicidade de navegação com profundidade analítica para apoiar decisões baseadas em dados. |

---

## 🛠️ Bibliotecas Principais e Requisitos de Hardware

### Stack Tecnológica
- **Backend & Validação:** `fastapi`, `uvicorn`, `pydantic`
- **IA & NLP Local:** `transformers`, `torch`, `sentencepiece`, `protobuf`
- **Dados & Visualização:** `pandas`, `streamlit`, `wordcloud`, `matplotlib`
- **Coleta Web & Testes:** `requests`, `beautifulsoup4`

### Hardware, Memória e Desempenho (CPU vs. GPU)
- **Processamento (CPU vs. GPU):** Ambos os modelos operam integralmente em **CPU** (processadores x86_64 modernos), dispensando GPU dedicada.
- **Armazenamento e Memória RAM:**
  - `modelo_local/` (DistilBERT): **~540 MB** em disco.
  - `modelo_sumarizacao/` (PTT5-base): **~890 MB** em disco.
  - **Consumo total em RAM:** Aproximadamente **2,4 GB a 3,0 GB de RAM** com os dois modelos carregados simultaneamente no `Uvicorn`, rodando confortavelmente em máquinas com **8 GB de RAM**.
- **Latência:** Inicialização (*cold start*) em **5 a 8 segundos**; inferência de sentimento em **< 250 ms** e sumarização abstrativa em **1,5 s a 4 s** em CPU (protegidos por timeouts de 15s e 30s).

### Justificativa Comparativa dos Modelos
- **Sumarização (`recogna-nlp/ptt5-base-summ-cstnews`):** Arquitetura T5 pré-treinada e ajustada especificamente para o português brasileiro (corpus CSTNews), entregando alta coerência gramatical na síntese de textos técnicos sob licença aberta no HuggingFace Hub, com pegada de memória muito inferior a LLMs generativos de 7B+ parâmetros (como Llama-3 ou Mistral via Ollama, que exigiriam 8–16 GB de RAM/VRAM).
- **Sentimento (`lxyuan/distilbert-base-multilingual-cased-sentiments-student`):** Modelo destilado sob licença **Apache 2.0**, pronto para uso (*out-of-the-box*) em português, superando alternativas como o `BERTimbau Large` em velocidade de resposta e menor consumo de RAM sem exigir *fine-tuning* adicional.

---

## 🚀 Passo a Passo de Execução

1. **Criar e ativar o ambiente virtual:**
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1