# 🌱 Projeto: Análise e Inteligência em Energia Renovável no Brasil

Plataforma analítica orientada a serviços desenvolvida sob a metodologia **CRISP-DM** para análise da matriz elétrica renovável brasileira, integrando **Streamlit (Multipáginas)**, **FastAPI**, **Web Scraping (BeautifulSoup)** e **Processamento de Linguagem Natural (NLP) offline com HuggingFace Transformers**.

---

## 📑 Documentação Oficial do Projeto
- 📜 **[Project Charter](Project%20Charter.md):** Escopo, reavaliação do problema de negócio, justificativa técnica sobre o não uso de Selenium e roadmap de IA.
- 📊 **[Data Summary Report (v1.0)](Data%20Summary%20Report.md):** Dicionário e detalhamento técnico das bases da ANEEL, pipeline de scraping da UFPR e contratos JSON da API.
- 🧪 **[Evidência de Testes da API](evidencia_test_api.txt):** Log de execução automatizada validando rotas de sucesso e exceções HTTP (`200`, `400`, `404`).

---

## 🛠️ Bibliotecas Principais Utilizadas

| Biblioteca | Versão Mínima | Papel na Arquitetura |
| :--- | :--- | :--- |
| **`fastapi`** | `0.110+` | Framework web assíncrono responsável pela camada de serviços RESTful e documentação OpenAPI (`/docs`). |
| **`uvicorn`** | `0.28+` | Servidor ASGI de alta performance utilizado para hospedar e executar a aplicação FastAPI localmente. |
| **`pydantic`** | `2.0+` | Validação estrita de contratos de entrada (*Request Models*), saída (*Response Models*) e erros padronizados. |
| **`transformers`** | `4.40+` | Biblioteca da HuggingFace usada para baixar, salvar localmente e carregar o tokenizador e o modelo NLP offline. |
| **`torch` (PyTorch)** | `2.2+` | Motor de computação tensorial responsável por executar a inferência da rede neural em CPU ou GPU. |
| **`streamlit`** | `1.35+` | Framework de interface web interativa multipáginas (`st.navigation`) com cache e gerenciamento de sessão. |
| **`pandas`** | `2.0+` | Manipulação, limpeza e filtragem dos datasets públicos da ANEEL em formato CSV. |
| **`beautifulsoup4`** & **`requests`** | `4.12+` / `2.31+` | Coleta e parsing HTML estático de literatura científica sobre energias renováveis (UFPR). |

---

## 💻 Requisitos de Hardware e Desempenho (CPU vs. GPU)

A escolha da arquitetura local foi calibrada para rodar em ambientes de desenvolvimento convencionais sem exigir hardware especializado:

- **CPU vs. GPU:** O modelo adotado utiliza arquitetura destilada (*DistilBERT*), operando com alta eficiência diretamente em **CPU** (processadores x86_64 modernos de 4+ núcleos). Caso uma GPU NVIDIA com suporte a CUDA esteja disponível, o PyTorch acelera a inferência em lote, mas ela **não é obrigatória** para o funcionamento em tempo real desta API.
- **Memória RAM Necessária:**
  - *Armazenamento em disco:* ~540 MB para os pesos (`model.safetensors`) e arquivos de vocabulário na pasta `modelo_local/`.
  - *Consumo em memória RAM:* O processo Python + Uvicorn + modelo carregado consome aproximadamente **1,2 GB a 1,6 GB de RAM**, permitindo execução confortável em máquinas com **8 GB de RAM** totais (mesmo rodando simultaneamente com o navegador e o Streamlit).
- **Tempo de Carga e Inferência:**
  - *Cold Start (Inicialização do Uvicorn):* Entre **2 e 5 segundos** para ler os pesos do disco local (`local_files_only=True`) e instanciar o `pipeline` em memória.
  - *Tempo de Inferência por Requisição:* Entre **80 ms e 250 ms** por texto (até 512 caracteres) em CPU, muito abaixo do limite de segurança configurado no servidor (`timeout = 15s`).

---

## 🧠 Justificativa Técnica e Comparativo do Modelo Local

### Modelo Escolhido: `lxyuan/distilbert-base-multilingual-cased-sentiments-student`
- **Qualidade para a Tarefa:** Trata-se de um modelo *student* destilado via *knowledge distillation* a partir de um professor *zero-shot* (`MoritzLaurer/mDeBERTa-v3-base-mnli-xnli`), treinado especificamente para classificação de sentimentos em múltiplos idiomas, incluindo **Português**. Para textos curtos e médios sobre percepção energética, tarifas e sustentabilidade, entrega alta acurácia sem necessidade de *fine-tuning* adicional.
- **Licença e Disponibilidade:** Disponível publicamente no **HuggingFace Model Hub** sob licença **Apache 2.0**, o que garante liberdade de uso acadêmico e comercial, reprodutibilidade e download integral dos pesos para operação 100% offline (`local_files_only=True`).

### Comparativo com Alternativas Avaliadas

| Critério | `distilbert-multilingual-sentiments` (Escolhido) | `neuralmind/bert-large-portuguese-cased` (BERTimbau Large) | LLMs Generativos Locais via Ollama (ex: `Llama-3 8B` / `Mistral 7B`) |
| :--- | :--- | :--- | :--- |
| **Tamanho em Disco** | **~540 MB** | ~1,34 GB | ~4,7 GB a 8 GB (quantizado Q4) |
| **Consumo de RAM/VRAM** | **~1,5 GB RAM** | ~3,5 GB RAM | 8 GB a 16 GB RAM/VRAM |
| **Latência em CPU** | **< 250 ms** | ~600 ms a 1,5 s | 10 s a 45 s por resposta |
| **Prontidão para Sentimento** | **Pronto para uso (*out-of-the-box*)** | Requer *fine-tuning* supervisonado (cabeça de classificação) | Requer *prompt engineering* e parsing de texto livre |
| **Veredito Arquitetural** | **Ideal para classificação rápida, leve e determinística em API.** | Excelente para português, mas exige treino adicional e mais RAM. | Mais indicado para geração de texto livre/RAG (próxima etapa), pesado para classificação simples. |

---

## 🚀 Passo a Passo para Configuração e Execução

Siga a ordem exata abaixo no terminal (PowerShell ou Bash) a partir da raiz do projeto:

### 1. Criar e Ativar o Ambiente Virtual (`.venv`)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1