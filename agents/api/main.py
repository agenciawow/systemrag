"""
API principal para agentes do sistema RAG

API separada que mantém a API atual intacta e adiciona funcionalidade de agentes.
"""

import os
from fastapi import FastAPI, HTTPException, Depends, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from .routes.v1_router import router as v1_router

# Configurar logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuração de autenticação (mesma da API atual)
security = HTTPBearer()

# API Key fixa (carregada do .env, mesma da API atual)
API_KEY = os.getenv("API_KEY", "sistemarag-api-key-2024")

class APIKeyAuth:
    """Autenticação via API Key fixa (mesma da API atual)"""
    
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

# Criar app FastAPI
app = FastAPI(
    title="Sistema RAG - API de Agentes",
    description="API para interação com agentes inteligentes de busca em documentos",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especificar domínios
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Incluir roteadores
app.include_router(v1_router, prefix="/v1")


@app.get("/")
async def root(api_key: str = Depends(auth)):
    """Endpoint raiz da API de agentes"""
    return {
        "message": "Sistema RAG - API de Agentes",
        "version": "1.0.0",
        "docs": "/docs",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/auth-info")
async def auth_info():
    """Informações sobre autenticação (endpoint público)"""
    return {
        "message": "API protegida por autenticação Bearer Token",
        "header_required": "Authorization: Bearer {api_key}",
        "api_key_env": "API_KEY",
        "default_key": "sistemarag-api-key-2024",
        "docs": "/docs (requer autenticação)"
    }


@app.get("/health")
async def health_check(api_key: str = Depends(auth)):
    """Health check da API de agentes"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "api": "agents"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)