from contextlib import asynccontextmanager
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from functools import lru_cache
from typing import Any, Dict, List, Optional
import logging
import os

import pandas as pd
import torch
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from transformers import (
    AutoModelForSeq2SeqLM,
    AutoModelForSequenceClassification,
    AutoTokenizer,
    pipeline,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("API_Energia_Renovavel")

# ==============================================================================
# ESTADO GLOBAL GERENCIADO & POOL DE THREADS REUTILIZÁVEL
# ==============================================================================
PASTA_SENTIMENTO = "./modelo_local"
PASTA_SUMARIZACAO = "./modelo_sumarizacao"
CAMINHO_CSV_CAPACIDADE = "data/capacidade-instalada-geracao-uf.csv"
CAMINHO_TXT_SCRAPING = "data/textos_web.txt"

executor_ia = ThreadPoolExecutor(max_workers=2)
modelos_estado: Dict[str, Any] = {
    "sentimento": None,
    "erro_sentimento": None,
    "sumarizacao": None,
    "erro_sumarizacao": None,
}

def _carregar_pipeline(pasta: str, tarefa: str, classe_modelo: Any) -> tuple[Any, Optional[str]]:
    if not os.path.exists(pasta):
        return None, f"Diretório '{pasta}' não encontrado."
    try:
        tok = AutoTokenizer.from_pretrained(pasta, local_files_only=True)
        mod = classe_modelo.from_pretrained(pasta, local_files_only=True)
        return pipeline(tarefa, model=mod, tokenizer=tok), None
    except Exception as exc:
        return None, f"Falha ao inicializar modelo em '{pasta}': {exc}"

@asynccontextmanager
async def lifespan(app: FastAPI):
    modelos_estado["sentimento"], modelos_estado["erro_sentimento"] = _carregar_pipeline(
        PASTA_SENTIMENTO, "sentiment-analysis", AutoModelForSequenceClassification
    )
    modelos_estado["sumarizacao"], modelos_estado["erro_sumarizacao"] = _carregar_pipeline(
        PASTA_SUMARIZACAO, "summarization", AutoModelForSeq2SeqLM
    )
    logger.info(
        "Inicialização concluída | Sentimento: %s | Sumarização: %s",
        bool(modelos_estado["sentimento"]),
        bool(modelos_estado["sumarizacao"]),
    )
    yield
    executor_ia.shutdown(wait=False)
    modelos_estado.clear()

app = FastAPI(
    title="API de Energia Renovável + NLP & Sumarização Local",
    description="API RESTful otimizada com cache em memória, lifespan gerenciado e inferência HuggingFace offline.",
    version="5.1.0",
    lifespan=lifespan,
)

# ==============================================================================
# CACHE DE DADOS EM MEMÓRIA
# ==============================================================================
@lru_cache(maxsize=1)
def _ler_csv_capacidade_cached(mtime: float) -> pd.DataFrame:
    df = pd.read_csv(CAMINHO_CSV_CAPACIDADE, encoding="latin1", sep=";")
    return df.where(pd.notnull(df), None)

# ==============================================================================
# SCHEMAS DE ENTRADA, SAÍDA E ERRO PADRONIZADO (PYDANTIC)
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
    capacidade_mw: float = Field(..., gt=0, description="Capacidade instalada em Megawatts")
    ano: int = Field(..., ge=2000, le=2030, description="Ano de referência entre 2000 e 2030")

class TextoEntradaRequest(BaseModel):
    texto: str = Field(..., min_length=3, description="Texto em português para classificação de sentimento")

class SumarizacaoRequest(BaseModel):
    texto: str = Field(..., min_length=50, description="Artigo ou relatório técnico com no mínimo 50 caracteres")
    tamanho_maximo: int = Field(default=130, ge=30, le=300, description="Limite máximo de tokens do resumo")
    tamanho_minimo: int = Field(default=30, ge=10, le=150, description="Limite mínimo de tokens do resumo")

class StatusResponse(BaseModel):
    status: str
    modelo_sentimento_carregado: bool
    modelo_sumarizacao_carregado: bool
    detalhe_modelos: str
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

class SumarizacaoResponse(BaseModel):
    status: str
    tipo_analise: str
    modelo_utilizado: str
    caracteres_originais: int
    caracteres_resumo: int
    taxa_compressao_percentual: str
    resumo_gerado: str

# ==============================================================================
# EXCEPTION HANDLERS GLOBAIS
# ==============================================================================
SUGESTOES_ERRO = {
    400: "Corrija o conteúdo da requisição e tente novamente.",
    404: "Verifique se o parâmetro existe ou se 'python scrapping.py' foi executado.",
    500: "Erro interno no processamento. Verifique a integridade dos arquivos em 'data/'.",
    503: "Execute 'python baixar_modelo.py' na raiz do projeto e reinicie o servidor FastAPI.",
    504: "O modelo excedeu o tempo limite em CPU. Envie um texto menor.",
}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    detalhes = "; ".join(
        f"Campo '{' -> '.join(str(loc) for loc in err['loc'] if loc != 'body')}': {err['msg']}"
        for err in exc.errors()
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErroDetalhadoResponse(
            codigo_http=422,
            tipo_erro="Dados de Entrada Inválidos",
            mensagem=f"Os dados enviados não atendem ao formato esperado: {detalhes}",
            sugestao_resolucao="Verifique os tipos e tamanhos mínimos/máximos na documentação (/docs).",
        ).model_dump(),
    )

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErroDetalhadoResponse(
            codigo_http=exc.status_code,
            tipo_erro=f"Erro HTTP {exc.status_code}",
            mensagem=str(exc.detail),
            sugestao_resolucao=SUGESTOES_ERRO.get(exc.status_code, "Consulte /docs."),
        ).model_dump(),
    )

@app.exception_handler(Exception)
async def global_unexpected_exception_handler(request: Request, exc: Exception):
    logger.error("Erro inesperado em %s: %s", request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErroDetalhadoResponse(
            codigo_http=500,
            tipo_erro="Erro Interno do Servidor",
            mensagem="Ocorreu uma falha inesperada durante o processamento da requisição.",
            sugestao_resolucao="Verifique os logs do terminal onde o Uvicorn está rodando.",
        ).model_dump(),
    )

# ==============================================================================
# UTILITÁRIO DE INFERÊNCIA COM TIMEOUT E INFERENCE_MODE
# ==============================================================================
def _executar_inferencia(pipe: Any, entrada: str, timeout_seg: float, **kwargs) -> Any:
    def _rodar():
        with torch.inference_mode():
            return pipe(entrada, **kwargs)[0]

    try:
        return executor_ia.submit(_rodar).result(timeout=timeout_seg)
    except FuturesTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"O modelo excedeu o tempo limite de {int(timeout_seg)} segundos em CPU.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Falha interna durante a inferência local: {exc}",
        )

# ==============================================================================
# ROTAS DA API
# ==============================================================================
@app.get("/", response_model=StatusResponse, summary="Status da API e dos modelos locais")
def home():
    sent_ok = modelos_estado["sentimento"] is not None
    sum_ok = modelos_estado["sumarizacao"] is not None
    
    txt_sent = "Sentimento: OK" if sent_ok else f"Sentimento: Indisponível ({modelos_estado['erro_sentimento']})"
    txt_sum = "Sumarização: OK" if sum_ok else f"Sumarização: Indisponível ({modelos_estado['erro_sumarizacao']})"
    
    return StatusResponse(
        status="API Online",
        modelo_sentimento_carregado=sent_ok,
        modelo_sumarizacao_carregado=sum_ok,
        detalhe_modelos=f"{txt_sent} | {txt_sum}",
        versao_api="5.1.0",
        endpoints_disponiveis=[
            "/docs",
            "/dados/capacidade",
            "/dados/resumo-texto",
            "/dados/registrar",
            "/processar_texto",
            "/sumarizar_texto",
        ],
    )

@app.get("/dados/capacidade", response_model=CapacidadeResponse, summary="Consulta capacidade instalada da ANEEL por UF")
def obter_capacidade(uf: Optional[str] = None):
    if not os.path.exists(CAMINHO_CSV_CAPACIDADE):
        raise HTTPException(status_code=404, detail="Base 'capacidade-instalada-geracao-uf.csv' não encontrada.")

    uf_limpa = uf.strip().upper() if uf else None
    if uf_limpa and (len(uf_limpa) != 2 or not uf_limpa.isalpha()):
        raise HTTPException(status_code=400, detail=f"A sigla de UF '{uf}' é inválida. Informe 2 letras (ex: BA, SP).")

    df = _ler_csv_capacidade_cached(os.path.getmtime(CAMINHO_CSV_CAPACIDADE))
    col_uf = next((c for c in df.columns if "SigUF" in c or "UF" in c), None)

    if uf_limpa and col_uf:
        df = df[df[col_uf].astype(str).str.upper() == uf_limpa]
        if df.empty:
            raise HTTPException(status_code=404, detail=f"Nenhum registro encontrado para a UF '{uf_limpa}'.")

    return CapacidadeResponse(
        status="Sucesso",
        total_registros=len(df),
        uf_filtrada=uf_limpa,
        dados=df.head(100).to_dict(orient="records"),
    )

@app.get("/dados/resumo-texto", response_model=TextoScrapingResponse, summary="Retorna o corpus textual extraído via Web Scraping")
def obter_texto_scraping():
    if not os.path.exists(CAMINHO_TXT_SCRAPING):
        raise HTTPException(status_code=404, detail="Arquivo 'data/textos_web.txt' não encontrado.")

    with open(CAMINHO_TXT_SCRAPING, "r", encoding="utf-8") as f:
        conteudo = f.read()

    if not conteudo.strip():
        raise HTTPException(status_code=404, detail="O arquivo 'data/textos_web.txt' está vazio.")

    return TextoScrapingResponse(
        status="Sucesso",
        fonte="UFPR - Revista Brasileira de Energias Renováveis",
        tamanho_caracteres=len(conteudo),
        amostra=conteudo[:500],
        conteudo_completo=conteudo,
    )

@app.post("/dados/registrar", response_model=RegistroResponse, summary="Registra novos dados de potencial energético")
def registrar_dados(registro: NovoRegistroRequest):
    if not registro.uf.isalpha():
        raise HTTPException(status_code=400, detail="A sigla da UF deve conter apenas letras.")
    return RegistroResponse(
        status="Sucesso",
        mensagem=f"Registro validado para a UF {registro.uf.upper()}.",
        dados_validados=registro,
    )

@app.post("/processar_texto", response_model=ProcessamentoTextoResponse, summary="Classificação de sentimento local (DistilBERT)")
def processar_texto(payload: TextoEntradaRequest):
    pipe = modelos_estado["sentimento"]
    if pipe is None:
        raise HTTPException(status_code=503, detail=f"Serviço de sentimento indisponível: {modelos_estado['erro_sentimento']}")

    texto_limpo = payload.texto.strip()
    if len(texto_limpo) < 3:
        raise HTTPException(status_code=400, detail="O texto enviado contém menos de 3 caracteres válidos.")

    texto_cortado = texto_limpo[:512]
    inferencia = _executar_inferencia(pipe, texto_cortado, timeout_seg=15.0)
    score = round(float(inferencia["score"]), 4)

    return ProcessamentoTextoResponse(
        status="Processado com sucesso (Execução Local Offline)",
        tipo_analise="Classificação de Sentimento (NLP)",
        modelo_utilizado="distilbert-base-multilingual-cased-sentiments-student",
        caracteres_analisados=len(texto_cortado),
        texto_processado=texto_cortado,
        resultado=ResultadoAnalise(
            classificacao=inferencia["label"],
            confianca=score,
            confianca_percentual=f"{score * 100:.2f}%",
        ),
    )

@app.post(
    "/sumarizar_texto",
    response_model=SumarizacaoResponse,
    responses={400: {"model": ErroDetalhadoResponse}, 503: {"model": ErroDetalhadoResponse}, 504: {"model": ErroDetalhadoResponse}},
    summary="Automação de sumarização de artigos e relatórios (PTT5 Local)",
)
def sumarizar_texto(payload: SumarizacaoRequest):
    pipe = modelos_estado["sumarizacao"]
    if pipe is None:
        raise HTTPException(status_code=503, detail=f"Serviço de sumarização indisponível: {modelos_estado['erro_sumarizacao']}")

    texto_limpo = payload.texto.strip()
    if len(texto_limpo) < 50:
        raise HTTPException(status_code=400, detail="Envie um texto com pelo menos 50 caracteres válidos para gerar um resumo.")

    texto_entrada = texto_limpo[:1500]
    resultado = _executar_inferencia(
        pipe,
        f"resumir: {texto_entrada}",
        timeout_seg=30.0,
        max_length=payload.tamanho_maximo,
        min_length=payload.tamanho_minimo,
        do_sample=False,
    )

    resumo = resultado["summary_text"].strip()
    reducao = max(0.0, (1 - (len(resumo) / len(texto_entrada))) * 100)

    return SumarizacaoResponse(
        status="Sumarizado com sucesso (Execução Local Offline)",
        tipo_analise="Sumarização Abstrativa de Texto (LLM/Seq2Seq)",
        modelo_utilizado="recogna-nlp/ptt5-base-summ-cstnews",
        caracteres_originais=len(texto_entrada),
        caracteres_resumo=len(resumo),
        taxa_compressao_percentual=f"{reducao:.1f}%",
        resumo_gerado=resumo,
    )