"""
Autenticação para API de agentes

Sistema idêntico ao da API atual para manter compatibilidade.
"""

import os
from fastapi import HTTPException, Security, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Configuração de autenticação
security = HTTPBearer()

# API Key obrigatória do ambiente
API_KEY = os.getenv("API_KEY")
if not API_KEY or not API_KEY.strip():
    raise ValueError("❌ API_KEY environment variable is required and not set. Please configure it in your .env file.")

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