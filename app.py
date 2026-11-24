from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, Optional, Tuple
import os

import pandas as pd
import requests
import streamlit as st

# ==============================================================================
# CONFIGURAÇÃO GLOBAL ÚNICA & CONSTANTES
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Final - Energia Renovável & IA",
    page_icon="🌱",
    layout="wide",
)

API_BASE_URL = "http://127.0.0.1:8000"
CAMINHO_CAPACIDADE = "data/capacidade-instalada-geracao-uf.csv"
CAMINHO_SIGA = "data/siga-empreendimentos-geracao-diario.csv"
CAMINHO_TEXTO_WEB = "data/textos_web.txt"

TEXTO_FALLBACK_ARTIGO = (
    "A expansão da geração distribuída por meio de sistemas solares fotovoltaicos no Brasil "
    "tem transformado o perfil de consumo energético residencial. Com a redução nos custos dos "
    "equipamentos e a regulamentação da compensação de energia elétrica pela ANEEL, consumidores "
    "passaram a gerar sua própria eletricidade, reduzindo a dependência de termelétricas fósseis "
    "e aliviando a sobrecarga do sistema interligado nacional em períodos de estiagem."
)

# ==============================================================================
# RECURSOS EM CACHE & CLIENTE HTTP CENTRALIZADO
# ==============================================================================
@st.cache_resource
def obter_sessao_http() -> requests.Session:
    return requests.Session()

@st.cache_data
def carregar_dados() -> Tuple[pd.DataFrame, pd.DataFrame]:
    try:
        df1 = pd.read_csv(CAMINHO_CAPACIDADE, encoding="latin1", sep=";")
        df2 = pd.read_csv(CAMINHO_SIGA, encoding="utf-8", sep=";")
        return df1, df2
    except FileNotFoundError:
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data
def carregar_texto_scraping() -> str:
    if os.path.exists(CAMINHO_TEXTO_WEB):
        with open(CAMINHO_TEXTO_WEB, "r", encoding="utf-8") as f:
            return f.read()
    return ""

@st.cache_data(ttl=10)
def verificar_status_api() -> Tuple[bool, Dict[str, Any]]:
    try:
        resp = obter_sessao_http().get(f"{API_BASE_URL}/", timeout=2)
        if resp.status_code == 200:
            return True, resp.json()
    except requests.RequestException:
        pass
    return False, {}

def chamar_api_post(endpoint: str, payload: Dict[str, Any], timeout: int = 30) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Centraliza requisições POST e padroniza retorno (dados_sucesso, erro_estruturado)."""
    try:
        resp = obter_sessao_http().post(f"{API_BASE_URL}{endpoint}", json=payload, timeout=timeout)
        if resp.status_code == 200:
            return resp.json(), None
        return None, {"status_code": resp.status_code, **resp.json()}
    except requests.exceptions.ConnectionError:
        return None, {
            "status_code": 0,
            "tipo_erro": "Servidor Offline",
            "mensagem": f"Não foi possível conectar ao servidor FastAPI em `{API_BASE_URL}`.",
            "sugestao_resolucao": "Abra um terminal na raiz do projeto e execute `uvicorn api:app --reload`.",
        }
    except requests.exceptions.Timeout:
        return None, {
            "status_code": 504,
            "tipo_erro": "Timeout no Cliente",
            "mensagem": f"O servidor demorou mais de {timeout}s para responder.",
            "sugestao_resolucao": "Tente enviar um texto mais curto.",
        }
    except Exception as exc:
        return None, {
            "status_code": 500,
            "tipo_erro": "Erro Inesperado",
            "mensagem": str(exc),
            "sugestao_resolucao": "Verifique os logs da aplicação.",
        }

def exibir_erro_api(erro: Dict[str, Any]) -> None:
    st.error(f"**{erro.get('tipo_erro', 'Erro')} (HTTP {erro.get('status_code', '?')}):** {erro.get('mensagem')}")
    if "sugestao_resolucao" in erro:
        st.info(f"💡 **Como resolver:** {erro['sugestao_resolucao']}")

def detectar_coluna_uf(df: pd.DataFrame) -> str:
    return next((c for c in df.columns if "SigUF" in c or "UF" in c), df.columns[0])

def detectar_coluna_ano(df: pd.DataFrame) -> Optional[str]:
    col = next((c for c in df.columns if "AnoReferencia" in c or "AnoRef" in c), None)
    if not col:
        col = next((c for c in df.columns if ("Ano" in c or "ano" in c) and "Geracao" not in c), None)
    return col

st.session_state.setdefault("dados_usuario", None)
st.session_state.setdefault("historico_ia", [])

# ==============================================================================
# PÁGINA 1: DASHBOARD EXECUTIVO (CICLO COMPLETO DE CIÊNCIA DE DADOS & IA)
# ==============================================================================
def pagina_dashboard_executivo():
    st.title("🌱 Dashboard Executivo: Inteligência em Energia Renovável")
    st.markdown("**Ciclo Completo TDSP:** Aquisição de Dados (ANEEL + Web Scraping UFPR) $\\rightarrow$ Processamento via API (`FastAPI`) $\\rightarrow$ Insights com Modelos Locais (`PTT5` & `DistilBERT`).")

    df1, df2 = carregar_dados()
    texto_ufpr = carregar_texto_scraping()
    api_online, _ = verificar_status_api()

    st.subheader("1. Monitoramento do Pipeline de Dados e Modelos")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Registros Históricos (ANEEL)", f"{len(df1):,}".replace(",", "."))
    k2.metric("Empreendimentos SIGA", f"{len(df2):,}".replace(",", "."))
    k3.metric("Corpus Científico (UFPR)", f"{len(texto_ufpr):,} chars".replace(",", "."))
    k4.metric(
        "Backend FastAPI + Modelos IA",
        "ONLINE (2 Modelos)" if api_online else "OFFLINE",
        delta="100% Local / CPU" if api_online else "Inicie o Uvicorn",
        delta_color="normal" if api_online else "inverse",
    )

    st.divider()

    col_graf1, col_graf2 = st.columns(2)
    with col_graf1:
        st.subheader("2. Distribuição Regional dos Dados Coletados (ANEEL)")
        if not df1.empty:
            col_uf = detectar_coluna_uf(df1)
            st.bar_chart(df1[col_uf].value_counts().head(10), color="#2E7D32")
            st.caption("Top 10 Unidades Federativas por volume de registros na base histórica de capacidade instalada.")
        else:
            st.warning("Base da ANEEL não encontrada em 'data/'.")

    with col_graf2:
        st.subheader("3. Performance e Insights dos Modelos de IA")
        if st.session_state.historico_ia:
            df_hist = pd.DataFrame(st.session_state.historico_ia).set_index("Execução")
            st.bar_chart(df_hist[["Confiança Sentimento (%)", "Compressão Resumo (%)"]])
            st.caption("Comparativo em tempo real entre confiança do classificador e taxa de compressão da sumarização.")
        else:
            df_bench = pd.DataFrame({
                "Etapa / Modelo IA": ["Sentimento (DistilBERT)", "Sumarização UFPR (PTT5)"],
                "Eficiência (%)": [86.9, 64.5],
            }).set_index("Etapa / Modelo IA")
            st.bar_chart(df_bench, color="#1565C0")
            st.caption("Referência: Confiança média do classificador (86,9%) e redução textual média do sumarizador (64,5%).")

    st.divider()

    st.subheader("4. Laboratório Interativo: Transformando Dados Coletados em Insights")
    col_int1, col_int2 = st.columns([1, 2])

    with col_int1:
        fonte_contexto = st.radio(
            "Fonte de dados para alimentar a IA:",
            ["Artigo Científico Raspado (UFPR)", "Cenário Regional (Base ANEEL)", "Texto Personalizado (ESG/Energia)"],
        )
        uf_escolhida = "BA"
        if fonte_contexto == "Cenário Regional (Base ANEEL)" and not df1.empty:
            col_uf = detectar_coluna_uf(df1)
            ufs_disp = sorted(df1[col_uf].dropna().unique())
            uf_escolhida = st.selectbox("Escolha a UF para diagnóstico:", ufs_disp, index=ufs_disp.index("BA") if "BA" in ufs_disp else 0)

    with col_int2:
        if fonte_contexto == "Artigo Científico Raspado (UFPR)":
            texto_base = texto_ufpr[:1200] if texto_ufpr else TEXTO_FALLBACK_ARTIGO
        elif fonte_contexto == "Cenário Regional (Base ANEEL)" and not df1.empty:
            col_uf = detectar_coluna_uf(df1)
            qtd_reg = int((df1[col_uf] == uf_escolhida).sum())
            texto_base = (
                f"O estado de {uf_escolhida} possui {qtd_reg} registros históricos consolidados na base de capacidade "
                f"instalada da ANEEL, demonstrando forte potencial para expansão de fontes renováveis como solar "
                f"fotovoltaica e eólica. A adoção de microgeração distribuída neste estado reduz custos tarifários "
                f"residenciais, mitiga emissões de carbono e fortalece a segurança energética regional alinhada aos ODS 7 e 13."
            )
        else:
            texto_base = "Investimentos em governança ambiental e transição para matriz solar reduzem riscos regulatórios e custos operacionais."

        texto_editavel = st.text_area("Contexto enviado aos modelos locais:", value=texto_base, height=130)

        if st.button("🚀 Processar com IA (Execução Paralela: Sumarizar + Classificar)", type="primary"):
            with st.spinner("Executando modelos PTT5 e DistilBERT simultaneamente..."):
                with ThreadPoolExecutor(max_workers=2) as pool:
                    fut_sum = pool.submit(chamar_api_post, "/sumarizar_texto", {"texto": texto_editavel}, 35)
                    fut_sent = pool.submit(chamar_api_post, "/processar_texto", {"texto": texto_editavel}, 20)
                    (d_sum, err_sum), (d_sent, err_sent) = fut_sum.result(), fut_sent.result()

                if err_sum:
                    exibir_erro_api(err_sum)
                elif err_sent:
                    exibir_erro_api(err_sent)
                elif d_sum and d_sent:
                    res_sent = d_sent["resultado"]
                    comp_val = float(d_sum["taxa_compressao_percentual"].replace("%", ""))
                    idx = len(st.session_state.historico_ia) + 1
                    st.session_state.historico_ia.append({
                        "Execução": f"#{idx} ({fonte_contexto[:10]})",
                        "Confiança Sentimento (%)": round(res_sent["confianca"] * 100, 1),
                        "Compressão Resumo (%)": comp_val,
                    })

                    res_c1, res_c2 = st.columns(2)
                    with res_c1:
                        st.success(f"**Resumo Executivo (Compressão de {d_sum['taxa_compressao_percentual']}):**\n\n{d_sum['resumo_gerado']}")
                    with res_c2:
                        classe = res_sent["classificacao"].upper()
                        recomendacoes = {
                            "POSITIVE": "✅ **Recomendação:** Cenário favorável para expansão de projetos fotovoltaicos e eficiência energética.",
                            "NEGATIVE": "⚠️ **Recomendação:** Ponto de atenção regulatório ou de custo; priorizar mitigação de riscos e auditoria tarifária.",
                        }
                        rec = recomendacoes.get(classe, "ℹ️ **Recomendação:** Cenário técnico neutro; aprofundar análise granular por empreendimento na base SIGA.")
                        st.info(f"**Sentimento Detectado:** {classe} ({res_sent['confianca_percentual']} de confiança)\n\n{rec}")

# ==============================================================================
# PÁGINA 2: VISUALIZAÇÃO E FILTROS DE DADOS (ANEEL)
# ==============================================================================
def pagina_visualizacao():
    st.title("📊 Exploração Granular das Bases (ANEEL)")
    df_energia1, df_energia2 = carregar_dados()

    if df_energia1.empty and df_energia2.empty:
        st.error("Arquivos CSV não encontrados na pasta 'data/'.")
        return

    tabela_selecionada = st.radio(
        "Selecione a base de dados para análise:",
        ["Capacidade Instalada por UF", "Empreendimentos de Geração Diária"],
        horizontal=True,
    )

    if tabela_selecionada == "Capacidade Instalada por UF" and not df_energia1.empty:
        col1, col2 = st.columns(2)
        coluna_uf = detectar_coluna_uf(df_energia1)
        coluna_ano = detectar_coluna_ano(df_energia1)

        with col1:
            ufs_sel = st.multiselect("Filtrar por Estado (UF):", options=sorted(df_energia1[coluna_uf].dropna().unique()))
        with col2:
            anos_sel = (
                st.multiselect(f"Filtrar por Ano de Referência ({coluna_ano}):", options=sorted(df_energia1[coluna_ano].dropna().unique()))
                if coluna_ano else []
            )

        mascara = pd.Series(True, index=df_energia1.index)
        if ufs_sel:
            mascara &= df_energia1[coluna_uf].isin(ufs_sel)
        if anos_sel and coluna_ano:
            mascara &= df_energia1[coluna_ano].isin(anos_sel)

        df_filtrado = df_energia1[mascara]
        st.metric("Total de Registros Filtrados", len(df_filtrado))
        if not df_filtrado.empty:
            st.bar_chart(df_filtrado[coluna_uf].value_counts(), color="#2E7D32")
        st.dataframe(df_filtrado, use_container_width=True)

    elif tabela_selecionada == "Empreendimentos de Geração Diária" and not df_energia2.empty:
        coluna_uf2 = detectar_coluna_uf(df_energia2)
        ufs_sel2 = st.multiselect("Filtrar por Estado (UF):", options=sorted(df_energia2[coluna_uf2].dropna().unique()))
        df_filtrado2 = df_energia2[df_energia2[coluna_uf2].isin(ufs_sel2)] if ufs_sel2 else df_energia2

        st.metric("Total de Empreendimentos Filtrados", len(df_filtrado2))
        if not df_filtrado2.empty:
            st.bar_chart(df_filtrado2[coluna_uf2].value_counts().head(15), color="#00838F")
        st.dataframe(df_filtrado2, use_container_width=True)

# ==============================================================================
# PÁGINA 3: UPLOAD E DOWNLOAD
# ==============================================================================
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
            st.download_button(
                label="📥 Baixar Base Capacidade por UF (CSV)",
                data=df_energia1.to_csv(index=False).encode("utf-8"),
                file_name="capacidade_geracao_aneel.csv",
                mime="text/csv",
            )
        else:
            st.warning("Base de dados não disponível para exportação.")

# ==============================================================================
# PÁGINA 4: NUVEM DE PALAVRAS (WEB SCRAPING)
# ==============================================================================
def pagina_nuvem_palavras():
    st.title("☁️ Análise Textual (Web Scraping - UFPR)")
    st.write("Nuvem de palavras gerada a partir da extração estática (`BeautifulSoup`) do artigo científico da Revista Brasileira de Energias Renováveis (UFPR).")

    texto_web = carregar_texto_scraping()
    if texto_web.strip():
        try:
            from wordcloud import WordCloud
            import matplotlib.pyplot as plt

            wordcloud = WordCloud(width=900, height=400, background_color="white", colormap="Greens").generate(texto_web)
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.imshow(wordcloud, interpolation="bilinear")
            ax.axis("off")
            st.pyplot(fig)

            with st.expander("Visualizar texto bruto extraído"):
                st.write(texto_web[:1500] + "...")
        except ImportError:
            st.error("Bibliotecas ausentes. Execute: `pip install wordcloud matplotlib`")
    else:
        st.error("Arquivo 'data/textos_web.txt' não encontrado ou vazio. Execute `python scrapping.py`.")

# ==============================================================================
# PÁGINA 5: LABORATÓRIO DETALHADO DE IA (SUMARIZAÇÃO & SENTIMENTO)
# ==============================================================================
def pagina_llm_api():
    st.title("🤖 Modelos Locais de IA (FastAPI + HuggingFace)")
    st.write("Execução 100% offline em CPU com validação Pydantic e tratamento padronizado de exceções HTTP.")

    aba_resumo, aba_sentimento = st.tabs([
        "📝 Automação de Sumarização (PTT5)",
        "💬 Classificação de Sentimento (DistilBERT)",
    ])

    with aba_resumo:
        st.subheader("Síntese Automática de Literatura Científica e Relatórios")
        st.caption("Modelo: `recogna-nlp/ptt5-base-summ-cstnews` | Rota: `POST /sumarizar_texto`")

        texto_ufpr = carregar_texto_scraping()
        texto_artigo = texto_ufpr[:1500] if texto_ufpr else TEXTO_FALLBACK_ARTIGO
        texto_para_resumir = st.text_area("Texto técnico ou artigo raspado (UFPR):", value=texto_artigo, height=180)

        col_s1, col_s2 = st.columns(2)
        min_len = col_s1.slider("Tamanho mínimo do resumo (tokens):", 20, 100, 35)
        max_len = col_s2.slider("Tamanho máximo do resumo (tokens):", 60, 250, 120)

        if st.button("Gerar Resumo Executivo", type="primary"):
            with st.spinner("Sintetizando texto com modelo PTT5 local..."):
                dados, erro = chamar_api_post(
                    "/sumarizar_texto",
                    {"texto": texto_para_resumir, "tamanho_minimo": min_len, "tamanho_maximo": max_len},
                    timeout=35,
                )
                if erro:
                    exibir_erro_api(erro)
                elif dados:
                    st.success("Resumo gerado com sucesso!")
                    st.info(f"**Resumo Executivo:**\n\n{dados['resumo_gerado']}")

                    m1, m2, m3 = st.columns(3)
                    m1.metric("Caracteres Originais", dados["caracteres_originais"])
                    m2.metric("Caracteres do Resumo", dados["caracteres_resumo"])
                    m3.metric("Taxa de Compressão", dados["taxa_compressao_percentual"])

                    with st.expander("Ver Response Model JSON completo"):
                        st.json(dados)

    with aba_sentimento:
        st.subheader("Classificação de Sentimento sobre Matriz Energética")
        st.caption("Modelo: `distilbert-base-multilingual-cased-sentiments-student` | Rota: `POST /processar_texto`")

        texto_padrao = "A instalação de painéis solares residenciais reduziu drasticamente o valor da conta de luz e trouxe excelente retorno sustentável."
        texto_usuario = st.text_area("Texto para análise de sentimento:", value=texto_padrao, height=120)

        if st.button("Analisar Sentimento"):
            with st.spinner("Classificando texto no modelo DistilBERT local..."):
                dados, erro = chamar_api_post("/processar_texto", {"texto": texto_usuario}, timeout=20)
                if erro:
                    exibir_erro_api(erro)
                elif dados:
                    resultado = dados["resultado"]
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Classificação", resultado["classificacao"].upper())
                    col2.metric("Confiança", resultado["confianca_percentual"])
                    col3.metric("Caracteres Analisados", dados["caracteres_analisados"])
                    with st.expander("Ver Response Model JSON completo"):
                        st.json(dados)

# ==============================================================================
# ROTEAMENTO E MENU DE NAVEGAÇÃO (st.navigation)
# ==============================================================================
pg = st.navigation([
    st.Page(pagina_dashboard_executivo, title="Dashboard Executivo (IA)", icon="🌱"),
    st.Page(pagina_visualizacao, title="Exploração ANEEL", icon="📊"),
    st.Page(pagina_upload_download, title="Upload & Download", icon="📂"),
    st.Page(pagina_nuvem_palavras, title="Nuvem de Palavras", icon="☁️"),
    st.Page(pagina_llm_api, title="Laboratório Modelos IA", icon="🤖"),
])

pg.run()