import streamlit as st
import pandas as pd
import plotly.express as px
import os

# 1. Configuração inicial da página
st.set_page_config(page_title="Dashboard Energia Renovável", layout="wide")

st.title("🌱 Projeto: Energia Renovável")
st.subheader("Análise do potencial de energia renovável em diferentes regiões do Brasil.")

# 2. Cache para otimizar o carregamento dos CSVs
@st.cache_data
def carregar_dados():
    try:
        df1 = pd.read_csv("data/capacidade-instalada-geracao-uf.csv", encoding="latin1", sep=';')
        df2 = pd.read_csv("data/siga-empreendimentos-geracao-diario.csv", encoding="utf-8", sep=';')
        return df1, df2
    except FileNotFoundError:
        st.error("Arquivos CSV não encontrados na pasta 'data/'.")
        return pd.DataFrame(), pd.DataFrame()

df_energia1, df_energia2 = carregar_dados()

# 3. Estado de Sessão (Session State) para persistir uploads
if 'dados_usuario' not in st.session_state:
    st.session_state.dados_usuario = None

# 4. Interface Dinâmica com Abas
aba1, aba2, aba3, aba4 = st.tabs(["Metas do Projeto", "Visualização de Dados", "Upload/Download", "Nuvem de Palavras"])

with aba1:
    st.write("## Metas do Projeto")
    st.write("* Criar recomendações práticas para redução do consumo e do impacto ambiental doméstico.")
    st.write("* Estimular a conscientização de consumidores residenciais sobre eficiência energética.")
    
    st.info("Fontes de Dados (ANEEL): [Link 1](https://dadosabertos.aneel.gov.br/dataset/capacidade-instalada-por-unidade-da-federacao/resource/6fbee0f8-2617-4879-a69a-6b7892f12dad) | [Link 2](https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/2f65a1b0-19b8-4360-8238-b34ab4693d55/download/siga-empreendimentos-geracao-diario.csv)")

with aba2:
    st.write("## 🔍 Explorador e Filtros de Dados")
    
    tabela_selecionada = st.radio("Escolha a base de dados para filtrar:", ["Capacidade por UF (2006-2026)", "Empreendimentos Diários"])
    
    if tabela_selecionada == "Capacidade por UF (2006-2026)" and not df_energia1.empty:
        col_filtro1, col_filtro2 = st.columns(2)
        
        # Identification da Coluna de UF
        colunas_uf = [col for col in df_energia1.columns if 'SigUF' in col or 'UF' in col or 'Estado' in col]
        coluna_uf = colunas_uf[0] if colunas_uf else df_energia1.columns[0]
        
        # Identificação Específica da Coluna de Ano de Referência
        colunas_ano_ref = [col for col in df_energia1.columns if 'AnoReferencia' in col or 'AnoRef' in col or 'Ano_Referencia' in col]
        
        # Se não achar com nome exato de referência, busca genérico que não seja 'DataGeracao'
        if not colunas_ano_ref:
            colunas_ano_ref = [col for col in df_energia1.columns if ('Ano' in col or 'ano' in col) and 'Geracao' not in col]
            
        coluna_ano = colunas_ano_ref[0] if colunas_ano_ref else None

        # Filtro de Estado (UF)
        estados_disponiveis = sorted(df_energia1[coluna_uf].dropna().unique())
        with col_filtro1:
            ufs_selecionadas = st.multiselect("Filtrar por Estado (UF):", options=estados_disponiveis, default=[])
            
        # Filtro de Ano de Referência
        if coluna_ano:
            anos_disponiveis = sorted(df_energia1[coluna_ano].dropna().unique())
            with col_filtro2:
                anos_selecionados = st.multiselect(f"Filtrar por Ano de Referência ({coluna_ano}):", options=anos_disponiveis, default=[])
        else:
            anos_selecionados = []

        # Aplicação dos Filtros
        df_filtrado = df_energia1.copy()
        if ufs_selecionadas:
            df_filtrado = df_filtrado[df_filtrado[coluna_uf].isin(ufs_selecionadas)]
        if anos_selecionados and coluna_ano:
            df_filtrado = df_filtrado[df_filtrado[coluna_ano].isin(anos_selecionados)]

        st.write(f"Exibindo **{len(df_filtrado)}** registros encontrados:")
        st.dataframe(df_filtrado, use_container_width=True)

    elif tabela_selecionada == "Empreendimentos Diários" and not df_energia2.empty:
        colunas_uf2 = [col for col in df_energia2.columns if 'SigUF' in col or 'UF' in col]
        coluna_uf2 = colunas_uf2[0] if colunas_uf2 else df_energia2.columns[0]
        
        estados_disponiveis2 = sorted(df_energia2[coluna_uf2].dropna().unique())
        ufs_selecionadas2 = st.multiselect("Filtrar por Estado (UF):", options=estados_disponiveis2, default=[])

        df_filtrado2 = df_energia2.copy()
        if ufs_selecionadas2:
            df_filtrado2 = df_filtrado2[df_filtrado2[coluna_uf2].isin(ufs_selecionadas2)]

        st.write(f"Exibindo **{len(df_filtrado2)}** registros encontrados:")
        st.dataframe(df_filtrado2, use_container_width=True)

with aba3:
    st.write("## 📂 Serviço de Upload e Download")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("### Enviar Arquivo (Upload)")
        arquivo_upload = st.file_uploader("Faça upload de um arquivo CSV complementar", type=["csv"])
        
        if arquivo_upload is not None:
            st.session_state.dados_usuario = pd.read_csv(arquivo_upload)
            st.success("Arquivo carregado com sucesso!")
            
        if st.session_state.dados_usuario is not None:
            st.write("Pré-visualização dos seus dados:")
            st.dataframe(st.session_state.dados_usuario.head())

    with col2:
        st.write("### Baixar Dados (Download)")
        st.write("Faça o download dos dados processados da ANEEL.")
        
        if not df_energia1.empty:
            csv_download = df_energia1.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Baixar Capacidade de Geração (CSV)",
                data=csv_download,
                file_name='capacidade_geracao_aneel.csv',
                mime='text/csv',
            )

with aba4:
    st.write("## ☁️ Nuvem de Palavras (Dados Extraídos da Web)")
    st.write("Nuvem gerada a partir do texto extraído pelo **Beautiful Soup** na Wikipédia.")
    
    caminho_txt = "data/textos_web.txt"
    if os.path.exists(caminho_txt):
        with open(caminho_txt, "r", encoding="utf-8") as f:
            texto_web = f.read()
            
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt
            
            # Gerando a imagem da nuvem de palavras
            wordcloud = WordCloud(width=800, height=400, 
                                  background_color='white', 
                                  colormap='Greens').generate(texto_web)
            
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis("off")
            st.pyplot(fig)
            
            with st.expander("Ver amostra do texto extraído"):
                st.write(texto_web[:1000] + "...")
        except ImportError:
            st.error("Instale as bibliotecas necessárias rodando: `pip install wordcloud matplotlib`")
    else:
        st.error("⚠️ O arquivo 'data/textos_web.txt' não foi encontrado. Execute o script de scraping primeiro.")