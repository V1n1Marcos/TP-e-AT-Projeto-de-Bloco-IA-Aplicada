import streamlit as st
import pandas as pd
import requests
import os


st.set_page_config(page_title="Portal Energia Renovável", page_icon="🌱", layout="wide")

st.title("🌱 Projeto: Análise de Energia Renovável no Brasil")
st.subheader("Plataforma Integrada de Dados, APIs e Inteligência Energética")

st.markdown("""
### Bem-vindo ao Portal de Energia Renovável!
Esta aplicação evoluiu para uma arquitetura multipáginas e integrada a serviços de API para análise da transição energética no Brasil.

Utilize o **menu lateral esquerdo** para navegar entre as diferentes seções do sistema:

- 📊 **Visualização de Dados:** Filtros interativos por UF e Ano de Referência nas bases da ANEEL.
- 📂 **Upload e Download:** Envio de dados complementares e download de arquivos em CSV.
- ☁️ **Nuvem de Palavras:** Análise textual extraída da web via Beautiful Soup.
- 🤖 **Preparação para LLMs:** Visão geral e testes de integração com a API FastAPI para apoio a modelos de IA.
""")

st.info("💡 **Dica de Desenvolvimento (FastAPI):** Inicie o servidor backend executando `uvicorn api:app --reload` no terminal para habilitar todos os endpoints de consulta de dados.")




# PÁGINA 1 Visualização de Dados

st.set_page_config(page_title="Visualização de Dados", page_icon="📊", layout="wide")

st.title("📊 Visualização e Filtros de Dados")

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

tabela_selecionada = st.radio("Escolha a base de dados para filtrar:", ["Capacidade por UF", "Empreendimentos Diários"])

if tabela_selecionada == "Capacidade por UF" and not df_energia1.empty:
    col1, col2 = st.columns(2)
    
    colunas_uf = [col for col in df_energia1.columns if 'SigUF' in col or 'UF' in col]
    coluna_uf = colunas_uf[0] if colunas_uf else df_energia1.columns[0]
    
    colunas_ano_ref = [col for col in df_energia1.columns if 'AnoReferencia' in col or 'AnoRef' in col]
    if not colunas_ano_ref:
        colunas_ano_ref = [col for col in df_energia1.columns if ('Ano' in col or 'ano' in col) and 'Geracao' not in col]
    coluna_ano = colunas_ano_ref[0] if colunas_ano_ref else None

    with col1:
        ufs = sorted(df_energia1[coluna_uf].dropna().unique())
        ufs_sel = st.multiselect("Filtrar por UF:", options=ufs)

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

    st.write(f"Registros encontrados: **{len(df_filtrado)}**")
    st.dataframe(df_filtrado, use_container_width=True)

elif tabela_selecionada == "Empreendimentos Diários" and not df_energia2.empty:
    colunas_uf2 = [col for col in df_energia2.columns if 'SigUF' in col or 'UF' in col]
    coluna_uf2 = colunas_uf2[0] if colunas_uf2 else df_energia2.columns[0]
    
    ufs2 = sorted(df_energia2[coluna_uf2].dropna().unique())
    ufs_sel2 = st.multiselect("Filtrar por UF:", options=ufs2)

    df_filtrado2 = df_energia2.copy()
    if ufs_sel2:
        df_filtrado2 = df_filtrado2[df_filtrado2[coluna_uf2].isin(ufs_sel2)]

    st.write(f"Registros encontrados: **{len(df_filtrado2)}**")
    st.dataframe(df_filtrado2, use_container_width=True)




# PÁGINA 2 Upload_Download

st.set_page_config(page_title="Upload e Download", page_icon="📂", layout="wide")

st.title("📂 Serviço de Upload e Download de Dados")

if 'dados_usuario' not in st.session_state:
    st.session_state.dados_usuario = None

col1, col2 = st.columns(2)

with col1:
    st.subheader("Upload de Arquivos Complementares")
    arquivo_upload = st.file_uploader("Envie um arquivo CSV", type=["csv"])
    if arquivo_upload is not None:
        st.session_state.dados_usuario = pd.read_csv(arquivo_upload)
        st.success("Arquivo carregado e armazenado na sessão!")
        
    if st.session_state.dados_usuario is not None:
        st.write("Pré-visualização:")
        st.dataframe(st.session_state.dados_usuario.head())

with col2:
    st.subheader("Download de Dados Tratados")
    try:
        df = pd.read_csv("data/capacidade-instalada-geracao-uf.csv", encoding="latin1", sep=';')
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Baixar Base Capacidade por UF (CSV)",
            data=csv,
            file_name="capacidade_geracao_aneel.csv",
            mime="text/csv"
        )
    except FileNotFoundError:
        st.warning("Base de dados não encontrada para download.")



# PÁGINA 3 Nuvem_de_Palavras

st.set_page_config(page_title="Nuvem de Palavras", page_icon="☁️", layout="wide")

st.title("☁️ Análise Textual (Web Scraping)")

caminho_txt = "data/textos_web.txt"
if os.path.exists(caminho_txt):
    with open(caminho_txt, "r", encoding="utf-8") as f:
        texto_web = f.read()

    try:
        from wordcloud import WordCloud
        import matplotlib.pyplot as plt

        wordcloud = WordCloud(width=800, height=400, background_color='white', colormap='Greens').generate(texto_web)
        
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.imshow(wordcloud, interpolation='bilinear')
        ax.axis("off")
        st.pyplot(fig)

        with st.expander("Exibir amostra do texto raspado da Web"):
            st.write(texto_web[:1200] + "...")

    except ImportError:
        st.error("Execute: `pip install wordcloud matplotlib` no seu terminal.")
else:
    st.error("Arquivo 'data/textos_web.txt' não encontrado. Execute o script `scrapping.py` primeiro.")


    
# PÁGINA 4 Preparacao_LLM

st.set_page_config(page_title="Preparação para LLMs & API", page_icon="🤖", layout="wide")

st.title("🤖 Integração com API & Preparação para LLMs")

st.markdown("""
### 🎯 Casos de Uso com LLMs para a Próxima Fase:
1. **Análise de Texto Gerado (Resumos):** Gerar resumos automáticos dos artigos acadêmicos raspados pela ferramenta de web scraping.
2. **Classificação de Sentimentos:** Avaliar a percepção da população sobre tarifas e energias renováveis em notícias do setor.
3. **Perguntas e Respostas (Q&A / RAG):** Permitir que o usuário faça perguntas em linguagem natural sobre a capacidade energética de seu estado.
""")

st.divider()
st.subheader("🔗 Teste de Conectividade com a FastAPI")

url_api = "http://127.0.0.1:8000/dados/resumo-texto"

if st.button("Consultar Endpoint da API (/dados/resumo-texto)"):
    try:
        resposta = requests.get(url_api, timeout=5)
        if resposta.status_code == 200:
            st.json(resposta.json())
        else:
            st.error(f"A API respondeu com código de erro: {resposta.status_code}")
    except Exception as e:
        st.warning("Não foi possível conectar à API. Certifique-se de que rodou `uvicorn api:app --reload` no terminal.")