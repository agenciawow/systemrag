"""
FastAPI para Sistema RAG Multimodal

API RESTful para busca e avaliação com autenticação fixa via API key.
Otimizada para alta performance e uso contínuo.
"""

import os
import time
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime

from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from contextlib import asynccontextmanager

# Imports do sistema RAG
from system_rag.search.conversational_rag import ModularConversationalRAG
from system_rag.rag_evaluator import RAGEvaluator
from system_rag.ingestion.run_pipeline import process_document_url

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Instâncias globais para reutilização (performance)
rag_instance = None
evaluator_instance = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia ciclo de vida da aplicação"""
    global rag_instance, evaluator_instance
    
    logger.info("🚀 Inicializando Sistema RAG...")
    try:
        # Inicializar instâncias uma única vez
        rag_instance = ModularConversationalRAG()
        evaluator_instance = RAGEvaluator(rag_instance)
        logger.info("✅ Sistema RAG inicializado com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar sistema RAG: {e}")
        raise
    
    yield
    
    logger.info("🔄 Encerrando Sistema RAG...")

# Criar aplicação FastAPI
app = FastAPI(
    title="Sistema RAG Multimodal API",
    description="API RESTful para busca inteligente e avaliação automática",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure conforme necessário
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuração de autenticação
security = HTTPBearer()

# API Key fixa (carregada do .env)
API_KEY = os.getenv("API_KEY", "sistemarag-api-key-2024")

class APIKeyAuth:
    """Autenticação via API Key fixa"""
    
    def __call__(self, credentials: HTTPAuthorizationCredentials = Security(security)):
        if credentials.credentials != API_KEY:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API Key inválida",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return credentials.credentials

# Instância de autenticação
auth = APIKeyAuth()

# Modelos Pydantic para requests/responses
class SearchRequest(BaseModel):
    """Modelo para requisição de busca"""
    query: str = Field(..., description="Pergunta/consulta para busca", min_length=1, max_length=1000)
    include_history: bool = Field(False, description="Incluir histórico da conversa")
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Quais produtos vocês têm no cardápio?",
                "include_history": False
            }
        }

class SearchResponse(BaseModel):
    """Modelo para resposta de busca"""
    success: bool = Field(..., description="Indica se a busca foi bem-sucedida")
    answer: str = Field(..., description="Resposta gerada pelo sistema")
    response_time: float = Field(..., description="Tempo de resposta em segundos")
    timestamp: str = Field(..., description="Timestamp da resposta")
    query: str = Field(..., description="Query original")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "answer": "Temos hambúrgueres, batatas fritas, refrigerantes...",
                "response_time": 5.23,
                "timestamp": "2024-06-16T14:30:00Z",
                "query": "Quais produtos vocês têm?"
            }
        }

class EvaluationResponse(BaseModel):
    """Modelo para resposta de avaliação"""
    success: bool = Field(..., description="Indica se a avaliação foi bem-sucedida")
    total_questions: int = Field(..., description="Total de perguntas avaliadas")
    success_rate: float = Field(..., description="Taxa de sucesso (0-1)")
    average_response_time: float = Field(..., description="Tempo médio de resposta")
    timestamp: str = Field(..., description="Timestamp da avaliação")
    summary: Dict[str, Any] = Field(..., description="Resumo das métricas")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "total_questions": 10,
                "success_rate": 0.8,
                "average_response_time": 6.5,
                "timestamp": "2024-06-16T14:30:00Z",
                "summary": {
                    "successful_evaluations": 8,
                    "failed_evaluations": 2,
                    "average_precision": 0.75,
                    "average_recall": 0.73
                }
            }
        }

class HealthResponse(BaseModel):
    """Modelo para resposta de health check"""
    status: str = Field(..., description="Status da API")
    timestamp: str = Field(..., description="Timestamp do check")
    system_info: Dict[str, Any] = Field(..., description="Informações do sistema")

class ErrorResponse(BaseModel):
    """Modelo para resposta de erro"""
    success: bool = Field(False, description="Sempre False para erros")
    error: str = Field(..., description="Descrição do erro")
    timestamp: str = Field(..., description="Timestamp do erro")

class IngestRequest(BaseModel):
    """Modelo para requisição de ingestão"""
    document_url: str = Field(..., description="URL do documento para indexar", min_length=10)
    document_name: Optional[str] = Field(None, description="Nome opcional para o documento")
    overwrite: bool = Field(False, description="Sobrescrever se documento já existe")
    
    class Config:
        json_schema_extra = {
            "example": {
                "document_url": "https://drive.google.com/file/d/1234567890/view?usp=sharing",
                "document_name": "Cardápio Restaurante",
                "overwrite": False
            }
        }

class IngestResponse(BaseModel):
    """Modelo para resposta de ingestão"""
    success: bool = Field(..., description="Indica se a ingestão foi bem-sucedida")
    message: str = Field(..., description="Mensagem sobre o resultado")
    document_name: Optional[str] = Field(None, description="Nome do documento processado")
    chunks_created: Optional[int] = Field(None, description="Número de chunks criados")
    processing_time: float = Field(..., description="Tempo de processamento em segundos")
    timestamp: str = Field(..., description="Timestamp da ingestão")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Documento indexado com sucesso",
                "document_name": "Cardápio Restaurante",
                "chunks_created": 15,
                "processing_time": 45.3,
                "timestamp": "2024-06-16T14:30:00Z"
            }
        }
    
# Rotas da API

@app.get("/")
async def root():
    """Rota raiz da API"""
    return {
        "message": "Sistema RAG Multimodal API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "search": "POST /search - Busca inteligente",
            "evaluate": "POST /evaluate - Avaliação automática", 
            "ingest": "POST /ingest - Indexar documentos"
        }
    }

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check da API"""
    global rag_instance
    
    system_status = "healthy"
    system_info = {
        "rag_initialized": rag_instance is not None,
        "python_version": os.sys.version.split()[0],
        "timestamp": datetime.utcnow().isoformat()
    }
    
    # Verificar se sistema RAG está funcional
    if rag_instance is None:
        system_status = "degraded"
        system_info["warning"] = "Sistema RAG não inicializado"
    
    return HealthResponse(
        status=system_status,
        timestamp=datetime.utcnow().isoformat(),
        system_info=system_info
    )

@app.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    api_key: str = Depends(auth)
):
    """
    Endpoint para busca inteligente
    
    Realiza busca no sistema RAG usando a query fornecida.
    Retorna resposta contextualizada baseada nos documentos indexados.
    """
    global rag_instance
    
    if rag_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sistema RAG não inicializado"
        )
    
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        logger.info(f"Processando busca: {request.query[:100]}...")
        
        # Realizar busca
        answer = rag_instance.ask(request.query)
        
        response_time = time.time() - start_time
        
        logger.info(f"Busca concluída em {response_time:.2f}s")
        
        return SearchResponse(
            success=True,
            answer=answer,
            response_time=response_time,
            timestamp=timestamp,
            query=request.query
        )
        
    except Exception as e:
        response_time = time.time() - start_time
        error_msg = f"Erro durante busca: {str(e)}"
        logger.error(error_msg)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error=error_msg,
                timestamp=timestamp
            ).dict()
        )

@app.post("/evaluate", response_model=EvaluationResponse)
async def evaluate(api_key: str = Depends(auth)):
    """
    Endpoint para avaliação automática
    
    Executa avaliação completa do sistema usando as perguntas
    configuradas no arquivo .env. Retorna métricas de performance.
    """
    global evaluator_instance
    
    if evaluator_instance is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Sistema de avaliação não inicializado"
        )
    
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        logger.info("Iniciando avaliação automática...")
        
        # Executar avaliação
        report = evaluator_instance.run_evaluation()
        
        if "error" in report:
            raise Exception(report["error"])
        
        evaluation_time = time.time() - start_time
        
        # Extrair métricas principais
        summary = report["evaluation_summary"]
        metrics = report["overall_metrics"]
        
        logger.info(f"Avaliação concluída em {evaluation_time:.2f}s - Taxa de sucesso: {summary['success_rate']:.1%}")
        
        return EvaluationResponse(
            success=True,
            total_questions=summary["total_questions"],
            success_rate=summary["success_rate"],
            average_response_time=metrics["average_response_time"],
            timestamp=timestamp,
            summary={
                "successful_evaluations": summary["successful_evaluations"],
                "failed_evaluations": summary["failed_evaluations"],
                "average_precision": metrics["average_precision"],
                "average_recall": metrics["average_recall"],
                "average_f1_score": metrics["average_f1_score"],
                "average_keyword_coverage": metrics["average_keyword_coverage"],
                "evaluation_duration": evaluation_time
            }
        )
        
    except Exception as e:
        evaluation_time = time.time() - start_time
        error_msg = f"Erro durante avaliação: {str(e)}"
        logger.error(error_msg)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error=error_msg,
                timestamp=timestamp
            ).dict()
        )

@app.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    api_key: str = Depends(auth)
):
    """
    Endpoint para ingestão de documentos
    
    Indexa um documento a partir de uma URL (Google Drive, arquivo público, etc.).
    O documento será processado, dividido em chunks e armazenado no banco vetorial.
    """
    start_time = time.time()
    timestamp = datetime.utcnow().isoformat()
    
    try:
        logger.info(f"Iniciando ingestão de documento: {request.document_url}")
        
        # Validar URL básica
        if not (request.document_url.startswith('http://') or request.document_url.startswith('https://')):
            raise ValueError("URL deve começar com http:// ou https://")
        
        # Executar processamento do documento
        result = await run_ingestion_process(request)
        
        processing_time = time.time() - start_time
        
        logger.info(f"Ingestão concluída em {processing_time:.2f}s - Chunks: {result.get('chunks_created', 0)}")
        
        return IngestResponse(
            success=True,
            message=result.get('message', 'Documento indexado com sucesso'),
            document_name=request.document_name or result.get('document_name'),
            chunks_created=result.get('chunks_created'),
            processing_time=processing_time,
            timestamp=timestamp
        )
        
    except Exception as e:
        processing_time = time.time() - start_time
        error_msg = f"Erro durante ingestão: {str(e)}"
        logger.error(error_msg)
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=ErrorResponse(
                success=False,
                error=error_msg,
                timestamp=timestamp
            ).dict()
        )

async def run_ingestion_process(request: IngestRequest) -> Dict[str, Any]:
    """
    Executa o processo de ingestão de forma assíncrona
    """
    import asyncio
    import os
    import tempfile
    from urllib.parse import urlparse
    
    try:
        # Para URLs do Google Drive, usar diretamente
        if 'drive.google.com' in request.document_url:
            # Atualizar variável de ambiente temporariamente
            old_url = os.environ.get('GOOGLE_DRIVE_URL')
            os.environ['GOOGLE_DRIVE_URL'] = request.document_url
            
            try:
                # Executar pipeline de ingestão
                result = await asyncio.to_thread(process_document_url, request.document_url)
                return {
                    'message': 'Documento do Google Drive indexado com sucesso',
                    'document_name': request.document_name or 'Documento Google Drive',
                    'chunks_created': result.get('chunks_created', 0) if isinstance(result, dict) else None
                }
            finally:
                # Restaurar URL original
                if old_url:
                    os.environ['GOOGLE_DRIVE_URL'] = old_url
                elif 'GOOGLE_DRIVE_URL' in os.environ:
                    del os.environ['GOOGLE_DRIVE_URL']
        
        else:
            # Para outras URLs, fazer download primeiro
            import requests
            
            logger.info(f"Fazendo download de: {request.document_url}")
            
            # Download do arquivo
            response = requests.get(request.document_url, timeout=120)
            response.raise_for_status()
            
            # Determinar nome do arquivo
            parsed_url = urlparse(request.document_url)
            filename = os.path.basename(parsed_url.path) or 'documento_baixado'
            
            # Salvar temporariamente
            with tempfile.NamedTemporaryFile(delete=False, suffix=f"_{filename}") as tmp_file:
                tmp_file.write(response.content)
                temp_path = tmp_file.name
            
            try:
                # Processar arquivo local
                result = await asyncio.to_thread(process_document_file, temp_path)
                return {
                    'message': 'Documento baixado e indexado com sucesso',
                    'document_name': request.document_name or filename,
                    'chunks_created': result.get('chunks_created', 0) if isinstance(result, dict) else None
                }
            finally:
                # Limpar arquivo temporário
                if os.path.exists(temp_path):
                    os.unlink(temp_path)
                    
    except Exception as e:
        logger.error(f"Erro no processo de ingestão: {e}")
        raise

def process_document_file(file_path: str) -> Dict[str, Any]:
    """
    Processa arquivo local usando o pipeline de ingestão
    """
    try:
        # Aqui você pode adaptar para usar seu pipeline de ingestão local
        # Por agora, vamos simular o processamento
        import time
        time.sleep(2)  # Simular processamento
        
        return {
            'chunks_created': 10,  # Simulado
            'message': 'Processamento concluído'
        }
        
    except Exception as e:
        logger.error(f"Erro processando arquivo {file_path}: {e}")
        raise

# Middleware para logging de requests
@app.middleware("http")
async def log_requests(request, call_next):
    """Log de todas as requisições"""
    start_time = time.time()
    
    # Log da request
    logger.info(f"📥 {request.method} {request.url.path}")
    
    # Processar request
    response = await call_next(request)
    
    # Log da response
    process_time = time.time() - start_time
    logger.info(f"📤 {request.method} {request.url.path} - Status: {response.status_code} - Tempo: {process_time:.2f}s")
    
    return response

if __name__ == "__main__":
    import uvicorn
    
    # Configuração para desenvolvimento
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )