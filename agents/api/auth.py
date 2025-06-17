"""
Autenticação para API de agentes

Sistema idêntico ao da API atual para manter compatibilidade.
"""

import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuração de autenticação
security = HTTPBearer()

# API Key fixa (carregada do .env, mesma da API atual)
API_KEY = os.getenv("API_KEY", "sistemarag-api-key-2024")
if not API_KEY or not API_KEY.strip():
    API_KEY = "sistemarag-api-key-2024"
    print("⚠️ API_KEY não encontrada no .env, usando valor padrão")

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

# Função de conveniência para usar como dependência
def get_api_key(credentials: HTTPAuthorizationCredentials = Security(security)) -> str:
    """
    Dependência de autenticação para usar nos endpoints
    
    Args:
        credentials: Credenciais do header Authorization
        
    Returns:
        API key validada
        
    Raises:
        HTTPException: Se API key for inválida
    """
    return auth(credentials)