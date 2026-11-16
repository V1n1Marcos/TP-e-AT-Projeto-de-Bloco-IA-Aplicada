# 📊 Data Summary Report (v1.0)

**Projeto:** Análise do Potencial de Energia Renovável no Brasil  
**Fase:** TP3 — Integração de APIs, Web Scraping e Preparação para LLMs  
**Diretório de Armazenamento:** `data/`

---

## 1. Visão Geral das Fontes de Dados
Nesta versão do relatório, o ecossistema de dados do projeto foi expandido para contemplar **dados estruturados governamentais (ANEEL)**, **dados textuais não estruturados extraídos via Web Scraping (UFPR)** e **interfaces programáticas de acesso via API (FastAPI)**.

| Fonte / Artefato | Tipo de Dado | Formato | Origem / Mecanismo de Coleta | Armazenamento / Rota |
| :--- | :--- | :--- | :--- | :--- |
| **Capacidade Instalada por UF** | Estruturado (Tabular) | CSV (`;`, `latin1`) | Portal Dados Abertos ANEEL (Download direto) | `data/capacidade-instalada-geracao-uf.csv` |
| **Empreendimentos SIGA Diário** | Estruturado (Tabular) | CSV (`;`, `utf-8`) | Portal Dados Abertos ANEEL (Download direto) | `data/siga-empreendimentos-geracao-diario.csv` |
| **Artigo Energia Eólica (UFPR)** | Não Estruturado (Textual) | TXT (`utf-8`) | Web Scraping estático (`requests` + `BeautifulSoup`) | `data/textos_web.txt` |
| **Serviço de Dados RESTful** | Semi-estruturado (JSON) | API REST | Backend `FastAPI` (`api.py`) | Endpoints `/dados/*` |

---

## 2. Detalhamento das Bases Estruturadas (ANEEL)

### 2.1. Capacidade Instalada de Geração por Unidade da Federação
- **Arquivo:** `data/capacidade-instalada-geracao-uf.csv`
- **Cobertura Temporal:** Série histórica de 2006 a 2026.
- **Principais Atributos Utilizados:**
  - `SigUF` / Unidade Federativa: Identificação geográfica do estado brasileiro (utilizada como chave de filtro na interface e na API).
  - `AnoReferencia`: Ano base do registro da capacidade instalada (distinto da data de geração/extração do arquivo).
  - Matriz / Fonte Energética e Potência Instalada (kW / MW).
- **Tratamento Aplicado:** Leitura com encoding `latin1` e separador ponto-e-vírgula (`;`), remoção de valores nulos nos filtros de seleção e cacheamento em memória via `@st.cache_data`.

### 2.2. Empreendimentos de Geração Diária (SIGA)
- **Arquivo:** `data/siga-empreendimentos-geracao-diario.csv`
- **Descrição:** Base granular contendo usinas e empreendimentos de geração elétrica em operação, construção ou outorgados no Brasil.
- **Tratamento Aplicado:** Leitura em `utf-8`, indexação por sigla estadual (`SigUF`) para cruzamento regional na interface multipáginas.

---

## 3. Detalhamento da Coleta via Web Scraping (Dados Não Estruturados)
- **Script Responsável:** `scrapping.py`
- **Fonte Alvo:** Revista Brasileira de Energias Renováveis — Universidade Federal do Paraná (UFPR) (`https://revistas.ufpr.br/rber/article/view/65759`).
- **Método de Extração:** Requisição HTTP GET com cabeçalho `User-Agent` simulando navegador padrão, seguida de parsing HTML via `BeautifulSoup4` buscando tags semânticas (`<p>`, `<div>`, `<section>`) com filtro de tamanho mínimo (>20 caracteres) para eliminação de ruídos de navegação.
- **Artefato Gerado:** `data/textos_web.txt` (codificado em `utf-8`).
- **Mecanismo de Resiliência:** O pipeline conta com rotina de fallback técnico sobre matriz eólica e solar no Nordeste brasileiro caso o servidor acadêmico apresente instabilidade temporária.
- **Uso Atual e Futuro:** Alimenta a visualização de frequência lexical (Nuvem de Palavras) no Streamlit e servirá como base documental para tarefas de sumarização e RAG com LLMs.

---

## 4. Camada de Exposição e Ingestão via API (`FastAPI`)
Para padronizar o consumo dos dados descritos acima, o arquivo `api.py` expõe os seguintes contratos de dados:
- `GET /dados/capacidade?uf={SIGLA}`: Serializa registros da base histórica da ANEEL em formato JSON filtrados por estado.
- `GET /dados/resumo-texto`: Disponibiliza o conteúdo integral e metadados (contagem de caracteres) do arquivo `data/textos_web.txt` para consumo direto por pipelines de NLP/LLMs.
- `POST /dados/registrar`: Valida via `Pydantic` (`uf`, `fonte`, `capacidade_mw`, `ano`) e recebe novos registros de potencial energético.