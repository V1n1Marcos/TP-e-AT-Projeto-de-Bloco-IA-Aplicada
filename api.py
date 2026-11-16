from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
import pandas as pd
import logging
import os

# Configuração de Logs para diagnóstico técnico no servidor
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("API_Energia_Renovavel")

app = FastAPI(
    title="API de Energia Renovável + LLM Local",
    description="API RESTful com tratamento robusto de exceções HTTP, validação Pydantic e inferência HuggingFace offline.",
    version="4.0.0"
)

# ==============================================================================
# CARREGAMENTO DO MODELO HUGGINGFACE LOCAL (COM DIAGNÓSTICO DE FALHA)
# ==============================================================================
PASTA_MODELO = "./modelo_local"
nlp_pipeline = None
erro_carregamento_modelo: Optional[str] = None

if os.path.exists(PASTA_MODELO):
    try:
        tokenizer = AutoTokenizer.from_pretrained(PASTA_MODELO, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(PASTA_MODELO, local_files_only=True)
        nlp_pipeline = pipeline("sentiment-analysis", model=model, tokenizer=tokenizer)
        logger.info("Modelo HuggingFace local carregado com sucesso.")
    except Exception as e:
        erro_carregamento_modelo = f"Falha ao inicializar os pesos do modelo local: {str(e)}"
        logger.error(erro_carregamento_modelo)
else:
    erro_carregamento_modelo = f"Diretório '{PASTA_MODELO}' não encontrado no servidor."
    logger.warning(erro_carregamento_modelo)

# ==============================================================================
# SCHEMAS DE ENTRADA, SAÍDA E ERRO PADRONIZADO
# ==============================================================================
class ErroDetalhadoResponse(BaseModel):
    status: str = "Erro"
    codigo_http: int
    tipo_erro: str
    mensagem: str
    sugestao_resolucao: str

class NovoRegistroRequest(BaseModel):
    uf: str = Field(..., min_length=2, max_length=2, description="Sigla do estado (ex: BA, SP)")
    fonte: str = Field(..., min_length=3, description="Tipo de fonte energética (ex: Solar, Eólica)")
    capacidade_mw: float = Field(..., gt=0, description="Capacidade instalada em Megawatts (deve ser maior que 0)")
    ano: int = Field(..., ge=2000, le=2030, description="Ano de referência entre 2000 e 2030")

class TextoEntradaRequest(BaseModel):
    texto: str = Field(..., min_length=3, description="Texto em português para análise pelo modelo local")

class StatusResponse(BaseModel):
    status: str
    modelo_local_carregado: bool
    detalhe_modelo: str
    versao_api: str
    endpoints_disponiveis: List[str]

class CapacidadeResponse(BaseModel):
    status: str
    total_registros: int
    uf_filtrada: Optional[str] = None
    dados: List[Dict[str, Any]]

class TextoScrapingResponse(BaseModel):
    status: str
    fonte: str
    tamanho_caracteres: int
    amostra: str
    conteudo_completo: str

class RegistroResponse(BaseModel):
    status: str
    mensagem: str
    dados_validados: NovoRegistroRequest

class ResultadoAnalise(BaseModel):
    classificacao: str
    confianca: float
    confianca_percentual: str

class ProcessamentoTextoResponse(BaseModel):
    status: str
    tipo_analise: str
    modelo_utilizado: str
    caracteres_analisados: int
    texto_processado: str
    resultado: ResultadoAnalise

# ==============================================================================
# EXCEPTION HANDLERS GLOBAIS (PADRONIZAÇÃO PARA O CLIENTE)
# ==============================================================================

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Intercepta erros de validação (422) e devolve instruções claras ao usuário."""
    erros_formatados = []
    for err in exc.errors():
        campo = " -> ".join(str(loc) for loc in err["loc"] if loc != "body")
        erros_formatados.append(f"Campo '{campo}': {err['msg']}")
    
    detalhe_texto = "; ".join(erros_formatados)
    logger.warning(f"Erro de validação na rota {request.url.path}: {detalhe_texto}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErroDetalhadoResponse(
            codigo_http=422,
            tipo_erro="Dados de Entrada Inválidos",
            mensagem=f"Os dados enviados não atendem ao formato esperado: {detalhe_texto}",
            sugestao_resolucao="Verifique os tipos, tamanhos mínimos/máximos e campos obrigatórios no esquema da rota (/docs)."
        ).model_dump()
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Padroniza todas as HTTPExceptions lançadas intencionalmente nas rotas."""
    sugestoes = {
        400: "Corrija o conteúdo da requisição e tente novamente.",
        404: "Verifique se o parâmetro informado existe ou se os scripts de coleta (scrapping.py) foram executados.",
        500: "Erro interno no processamento de arquivos. Verifique a integridade dos dados em 'data/'.",
        503: "Execute 'python baixar_modelo.py' na raiz do projeto e reinicie o servidor FastAPI.",
        504: "O modelo demorou além do limite esperado. Tente enviar um texto menor."
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=ErroDetalhadoResponse(
            codigo_http=exc.status_code,
            tipo_erro=f"Erro HTTP {exc.status_code}",
            mensagem=str(exc.detail),
            sugestao_resolucao=sugestoes.get(exc.status_code, "Consulte a documentação da API em /docs.")
        ).model_dump()
    )

@app.exception_handler(Exception)
async def global_unexpected_exception_handler(request: Request, exc: Exception):
    """Captura falhas imprevistas (500) evitando exposição de stack trace bruto ao cliente."""
    logger.error(f"Erro inesperado em {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErroDetalhadoResponse(
            codigo_http=500,
            tipo_erro="Erro Interno do Servidor",
            mensagem="Ocorreu uma falha inesperada durante o processamento da requisição.",
            sugestao_resolucao="Verifique os logs do terminal onde o Uvicorn está rodando para detalhes técnicos."
        ).model_dump()
    )

# ==============================================================================
# ROTAS DA API
# ==============================================================================

@app.get("/", response_model=StatusResponse, summary="Status da API e diagnóstico do modelo local")
def home():
    detalhe = "Modelo carregado e pronto para inferência offline." if nlp_pipeline else f"Indisponível ({erro_carregamento_modelo})"
    return StatusResponse(
        status="API Online",
        modelo_local_carregado=nlp_pipeline is not None,
        detalhe_modelo=detalhe,
        versao_api="4.0.0",
        endpoints_disponiveis=["/docs", "/dados/capacidade", "/dados/resumo-texto", "/dados/registrar", "/processar_texto"]
    )

@app.get(
    "/dados/capacidade",
    response_model=CapacidadeResponse,
    responses={400: {"model": ErroDetalhadoResponse}, 404: {"model": ErroDetalhadoResponse}, 500: {"model": ErroDetalhadoResponse}},
    summary="Consulta capacidade instalada da ANEEL por UF"
)
def obter_capacidade(uf: Optional[str] = None):
    caminho_csv = "data/capacidade-instalada-geracao-uf.csv"
    if not os.path.exists(caminho_csv):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Base de dados 'capacidade-instalada-geracao-uf.csv' não encontrada na pasta 'data/'."
        )
    
    if uf and (len(uf.strip()) != 2 or not uf.strip().isalpha()):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"A sigla de UF '{uf}' é inválida. Informe exatamente 2 letras (ex: BA, SP, RJ)."
        )

    try:
        df = pd.read_csv(caminho_csv, encoding="latin1", sep=';')
        df = df.where(pd.notnull(df), None)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha ao ler ou decodificar o arquivo CSV da ANEEL: {str(e)}"
        )
    
    col_uf = [c for c in df.columns if 'SigUF' in c or 'UF' in c]
    if uf and col_uf:
        df = df[df[col_uf[0]].astype(str).str.upper() == uf.strip().upper()]
        if df.empty:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum registro de geração encontrado para a UF '{uf.upper()}'."
            )
        
    return CapacidadeResponse(
        status="Sucesso",
        total_registros=len(df),
        uf_filtrada=uf.upper() if uf else None,
        dados=df.head(100).to_dict(orient="records")
    )

@app.get(
    "/dados/resumo-texto",
    response_model=TextoScrapingResponse,
    responses={404: {"model": ErroDetalhadoResponse}, 500: {"model": ErroDetalhadoResponse}},
    summary="Retorna o corpus textual extraído via Web Scraping"
)
def obter_texto_scraping():
    caminho_txt = "data/textos_web.txt"
    if not os.path.exists(caminho_txt):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Arquivo 'data/textos_web.txt' não encontrado. Execute o pipeline de web scraping antes de consultar."
        )
    
    try:
        with open(caminho_txt, "r", encoding="utf-8") as f:
            conteudo = f.read()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de leitura no arquivo de texto extraído: {str(e)}"
        )

    if not conteudo.strip():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="O arquivo 'data/textos_web.txt' existe, mas está vazio."
        )
        
    return TextoScrapingResponse(
        status="Sucesso",
        fonte="UFPR - Revista Brasileira de Energias Renováveis",
        tamanho_caracteres=len(conteudo),
        amostra=conteudo[:500],
        conteudo_completo=conteudo
    )

@app.post(
    "/dados/registrar",
    response_model=RegistroResponse,
    responses={400: {"model": ErroDetalhadoResponse}, 422: {"model": ErroDetalhadoResponse}},
    summary="Registra e valida novos dados de potencial energético"
)
def registrar_dados(registro: NovoRegistroRequest):
    if not registro.uf.isalpha():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A sigla da UF deve conter apenas letras."
        )
    return RegistroResponse(
        status="Sucesso",
        mensagem=f"Registro validado e recebido para a UF {registro.uf.upper()}.",
        dados_validados=registro
    )

@app.post(
    "/processar_texto",
    response_model=ProcessamentoTextoResponse,
    responses={
        400: {"model": ErroDetalhadoResponse},
        422: {"model": ErroDetalhadoResponse},
        503: {"model": ErroDetalhadoResponse},
        504: {"model": ErroDetalhadoResponse}
    },
    summary="Executa análise de sentimento local via HuggingFace com proteção de timeout"
)
def processar_texto(payload: TextoEntradaRequest):
    # 1. Verificação de disponibilidade do modelo (503 Service Unavailable)
    if nlp_pipeline is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Serviço de IA indisponível no momento. Motivo: {erro_carregamento_modelo}"
        )
    
    # 2. Validação semântica do texto de entrada (400 Bad Request)
    texto_limpo = payload.texto.strip()
    if len(texto_limpo) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="O texto enviado contém menos de 3 caracteres válidos após remoção de espaços."
        )

    texto_cortado = texto_limpo[:512]

    # 3. Execução protegida por Timeout (504 Gateway Timeout)
    try:
        with ThreadPoolExecutor(max_workers=1) as executor:
            futuro = executor.submit(nlp_pipeline, texto_cortado)
            inferencia = futuro.result(timeout=15.0)[0]
    except FuturesTimeoutError:
        logger.error("Timeout na inferência do modelo local.")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="O modelo de linguagem excedeu o tempo limite de 15 segundos para processar o texto."
        )
    except Exception as e:
        logger.error(f"Erro durante a inferência do modelo: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha interna durante a execução do modelo HuggingFace: {str(e)}"
        )

    score_arredondado = round(float(inferencia["score"]), 4)

    return ProcessamentoTextoResponse(
        status="Processado com sucesso (Execução Local Offline)",
        tipo_analise="Classificação de Sentimento (NLP)",
        modelo_utilizado="distilbert-base-multilingual-cased-sentiments-student",
        caracteres_analisados=len(texto_cortado),
        texto_processado=texto_cortado,
        resultado=ResultadoAnalise(
            classificacao=inferencia["label"],
            confianca=score_arredondado,
            confianca_percentual=f"{score_arredondado * 100:.2f}%"
        )
    )