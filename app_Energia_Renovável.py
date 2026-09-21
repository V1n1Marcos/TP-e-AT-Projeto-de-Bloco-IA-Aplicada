import streamlit as st
import pandas as pd
import plotly.express as px

st.title("Projeto: Energia Renovável")
st.subheader("Este projeto tem como objetivo analisar o potencial de energia renovável em diferentes regiões do Brasil.")
st.write("## Metas do Projeto")
st.write("* Desenvolver uma análise dos dados energéticos e geográficos disponíveis.")
st.write("* Identificar oportunidades de adoção de fontes renováveis, especialmente solar residencial.")
st.write("* Criar recomendações práticas para redução do consumo e do impacto ambiental doméstico.")
st.write("* Estimular a conscientização de consumidores residenciais sobre eficiência energética.")
st.write("* Meta inicial: elaborar um painel ou relatório com indicadores de consumo, potencial sustentável e recomendações por estado brasileiro.")
st.write("Link para a fonte de dados utilizada neste projeto")
st.write("Aneel arquivo.csv pública Link 1: https://dadosabertos.aneel.gov.br/dataset/capacidade-instalada-por-unidade-da-federacao/resource/6fbee0f8-2617-4879-a69a-6b7892f12dad")
st.write("Aneel arquivo.csv pública Link 2: https://dadosabertos.aneel.gov.br/dataset/6d90b77c-c5f5-4d81-bdec-7bc619494bb9/resource/2f65a1b0-19b8-4360-8238-b34ab4693d55/download/siga-empreendimentos-geracao-diario.csv")

df_energia1 = pd.read_csv("data/capacidade-instalada-geracao-uf.csv", encoding="latin1", sep=';')
st.write("## Capacidade de Geração por UF's \ 2006-2026")
st.dataframe(df_energia1)

df_energia2 = pd.read_csv("data/siga-empreendimentos-geracao-diario.csv", encoding="utf-8", sep=';')
st.write("## Empreendimento Geração Diário \ 2026")
st.dataframe(df_energia2)