import streamlit as st
import pandas as pd
import requests
import os

# ==============================================================================
# CONFIGURAÇÃO GLOBAL ÚNICA (Evita o erro de múltiplas chamadas de page_config)
# ==============================================================================
st.set_page_config(
    page_title="Energia Renovável Brasil",
    page_icon="🌱",
    layout="wide"
)

# ==============================================================================
# FUNÇÕES DE CARREGAMENTO E CACHE
# ==============================================================================
@st.cache_data
def carregar_dados():
    try:
        df1 = pd.read_csv("data/capacidade-instalada-geracao-uf.csv", encoding="latin1", sep=';')
        df2 = pd.read_csv("data/siga-empreendimentos-geracao-diario.csv", encoding="utf-8", sep=';')
        return df1, df2
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

if 'dados_usuario' not in st.session_state:
    st.session_state.dados_usuario = None

# ==============================================================================
# DEFINIÇÃO DAS PÁGINAS (Para o st.navigation)
# ==============================================================================

def pagina_home():
    st.title("🌱 Projeto: Análise de Energia Renovável no Brasil")
    st.subheader("Plataforma Integrada de Dados, APIs (FastAPI) e Preparação para LLMs")
    
    st.markdown("""
    ### Visão Geral da Arquitetura
    Esta aplicação foi estruturada seguindo o framework **CRISP-DM**, evoluindo de um painel estático para uma arquitetura orientada a serviços pronta para inteligência artificial generativa.
    
    **Navegue pelo menu lateral para acessar os módulos:**
    - **📊 Visualização de Dados:** Exploração interativa com filtros por Unidade Federativa (UF) e Ano de Referência nas bases abertas da ANEEL.
    - **📂 Upload e Download:** Ingestão dinâmica de bases complementares em CSV (com persistência em sessão) e exportação de dados tratados.
    - **☁️ Nuvem de Palavras:** Análise de frequência lexical extraída via Web Scraping (`BeautifulSoup`) de produção científica sobre energia eólica (UFPR).
    - **🤖 Integração API & LLMs:** Consumo em tempo real dos endpoints RESTful (`FastAPI`) e demonstração dos fluxos preparados para modelos de linguagem.
    """)
    
    st.info("💡 **Status do Backend:** Para testar a integração na aba de IA/API, certifique-se de que o servidor FastAPI está rodando (`uvicorn api:app --reload`).")

def pagina_visualizacao():
    st.title("📊 Visualização e Filtros de Dados (ANEEL)")
    df_energia1, df_energia2 = carregar_dados()

    if df_energia1.empty and df_energia2.empty:
        st.error("Arquivos CSV não encontrados na pasta 'data/'. Verifique o diretório.")
        return

    tabela_selecionada = st.radio(
        "Selecione a base de dados para análise:",
        ["Capacidade Instalada por UF", "Empreendimentos de Geração Diária"],
        horizontal=True
    )

    if tabela_selecionada == "Capacidade Instalada por UF" and not df_energia1.empty:
        col1, col2 = st.columns(2)

        colunas_uf = [col for col in df_energia1.columns if 'SigUF' in col or 'UF' in col]
        coluna_uf = colunas_uf[0] if colunas_uf else df_energia1.columns[0]

        colunas_ano_ref = [col for col in df_energia1.columns if 'AnoReferencia' in col or 'AnoRef' in col]
        if not colunas_ano_ref:
            colunas_ano_ref = [col for col in df_energia1.columns if ('Ano' in col or 'ano' in col) and 'Geracao' not in col]
        coluna_ano = colunas_ano_ref[0] if colunas_ano_ref else None

        with col1:
            ufs = sorted(df_energia1[coluna_uf].dropna().unique())
            ufs_sel = st.multiselect("Filtrar por Estado (UF):", options=ufs)

        with col2:
            if coluna_ano:
                anos = sorted(df_energia1[coluna_ano].dropna().unique())
                anos_sel = st.multiselect(f"Filtrar por Ano de Referência ({coluna_ano}):", options=anos)
            else:
                anos_sel = []

        df_filtrado = df_energia1.copy()
        if ufs_sel:
            df_filtrado = df_filtrado[df_filtrado[coluna_uf].isin(ufs_sel)]
        if anos_sel and coluna_ano:
            df_filtrado = df_filtrado[df_filtrado[coluna_ano].isin(anos_sel)]

        st.metric("Total de Registros Filtrados", len(df_filtrado))
        st.dataframe(df_filtrado, use_container_width=True)

    elif tabela_selecionada == "Empreendimentos de Geração Diária" and not df_energia2.empty:
        colunas_uf2 = [col for col in df_energia2.columns if 'SigUF' in col or 'UF' in col]
        coluna_uf2 = colunas_uf2[0] if colunas_uf2 else df_energia2.columns[0]

        ufs2 = sorted(df_energia2[coluna_uf2].dropna().unique())
        ufs_sel2 = st.multiselect("Filtrar por Estado (UF):", options=ufs2)

        df_filtrado2 = df_energia2.copy()
        if ufs_sel2:
            df_filtrado2 = df_filtrado2[df_filtrado2[coluna_uf2].isin(ufs_sel2)]

        st.metric("Total de Empreendimentos Filtrados", len(df_filtrado2))
        st.dataframe(df_filtrado2, use_container_width=True)

def pagina_upload_download():
    st.title("📂 Serviço de Upload e Download")
    df_energia1, _ = carregar_dados()

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Upload de Dados Complementares")
        arquivo_upload = st.file_uploader("Envie um arquivo CSV para análise na sessão", type=["csv"])
        if arquivo_upload is not None:
            st.session_state.dados_usuario = pd.read_csv(arquivo_upload)
            st.success("Arquivo carregado e persistido no Session State!")

        if st.session_state.dados_usuario is not None:
            st.write("Pré-visualização dos dados carregados:")
            st.dataframe(st.session_state.dados_usuario.head(), use_container_width=True)

    with col2:
        st.subheader("Exportação de Dados Tratados")
        st.write("Baixe a base consolidada de capacidade instalada da ANEEL.")
        if not df_energia1.empty:
            csv = df_energia1.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Base Capacidade por UF (CSV)",
                data=csv,
                file_name="capacidade_geracao_aneel.csv",
                mime="text/csv"
            )
        else:
            st.warning("Base de dados não disponível para exportação.")

def pagina_nuvem_palavras():
    st.title("☁️ Análise Textual (Web Scraping - UFPR)")
    st.write("Nuvem de palavras gerada a partir da extração estática (`BeautifulSoup`) do artigo científico da Revista Brasileira de Energias Renováveis (UFPR).")

    caminho_txt = "data/textos_web.txt"
    if os.path.exists(caminho_txt):
        with open(caminho_txt, "r", encoding="utf-8") as f:
            texto_web = f.read()

        if len(texto_web.strip()) == 0:
            st.warning("O arquivo textos_web.txt está vazio. Execute `python scrapping.py` novamente.")
            return

        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            wordcloud = WordCloud(width=900, height=400, background_color='white', colormap='Greens').generate(texto_web)
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)

            with st.expander("Visualizar texto bruto extraído"):
                st.write(texto_web[:1500] + "...")
        except ImportError:
            st.error("Bibliotecas ausentes. Execute: `pip install wordcloud matplotlib`")
    else:
        st.error("Arquivo 'data/textos_web.txt' não encontrado. Execute `python scrapping.py`.")

def pagina_llm_api():
    st.title("🤖 Integração FastAPI & Modelo HuggingFace Local")

    st.subheader("🧠 Testar Inferência Local (POST /processar_texto)")
    st.write("Envie um texto sobre energia renovável ou carregue o trecho extraído da UFPR para classificação de sentimento via modelo HuggingFace rodando 100% offline.")

    texto_padrao = "A instalação de painéis solares residenciais reduziu drasticamente o valor da conta de luz e trouxe excelente retorno sustentável."
    
    if st.button("Carregar amostra do texto raspado da UFPR"):
        if os.path.exists("data/textos_web.txt"):
            with open("data/textos_web.txt", "r", encoding="utf-8") as f:
                texto_padrao = f.read()[:450]
        else:
            st.warning("Arquivo 'data/textos_web.txt' não encontrado localmente.")

    texto_usuario = st.text_area("Texto para análise do modelo local:", value=texto_padrao, height=130)

    if st.button("Analisar Texto via FastAPI Local", type="primary"):
        with st.spinner("Processando texto no modelo local..."):
            try:
                resposta = requests.post(
                    "http://127.0.0.1:8000/processar_texto",
                    json={"texto": texto_usuario},
                    timeout=20
                )
                
                if resposta.status_code == 200:
                    dados = resposta.json()
                    resultado = dados["resultado"]
                    
                    st.caption(f"**Tipo de Análise:** {dados['tipo_analise']} | **Modelo:** `{dados['modelo_utilizado']}`")
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Classificação", resultado["classificacao"].upper())
                    col2.metric("Confiança", resultado["confianca_percentual"])
                    col3.metric("Caracteres Analisados", dados["caracteres_analisados"])
                    
                    with st.expander("Ver Response Model JSON completo validado"):
                        st.json(dados)
                else:
                    # Exibe o ErroDetalhadoResponse estruturado da API
                    erro_json = resposta.json()
                    st.error(f"**{erro_json.get('tipo_erro', 'Erro')} (HTTP {resposta.status_code}):** {erro_json.get('mensagem', 'Falha desconhecida.')}")
                    if "sugestao_resolucao" in erro_json:
                        st.info(f"💡 **Como resolver:** {erro_json['sugestao_resolucao']}")
                        
            except requests.exceptions.ConnectionError:
                st.error("🔌 **Falha de Conexão:** Não foi possível alcançar o servidor FastAPI em `http://127.0.0.1:8000`.")
                st.info("💡 **Como resolver:** Abra um terminal na pasta do projeto e execute `uvicorn api:app --reload`.")
            except requests.exceptions.Timeout:
                st.error("⏱️ **Timeout na Requisição:** O servidor demorou mais de 20 segundos para responder.")
                st.info("💡 **Como resolver:** Tente enviar um texto mais curto ou verifique o consumo de CPU da sua máquina.")
            except Exception as e:
                st.error(f"⚠️ **Erro Inesperado no Cliente:** {str(e)}")

# ==============================================================================
# ROTEAMENTO E MENU DE NAVEGAÇÃO (st.navigation)
# ==============================================================================
pg = st.navigation([
    st.Page(pagina_home, title="Início & Arquitetura", icon="🌱"),
    st.Page(pagina_visualizacao, title="Visualização de Dados", icon="📊"),
    st.Page(pagina_upload_download, title="Upload & Download", icon="📂"),
    st.Page(pagina_nuvem_palavras, title="Nuvem de Palavras", icon="☁️"),
    st.Page(pagina_llm_api, title="API & Preparação LLM", icon="🤖"),
])

pg.run()