"""
Roteador principal v1 da API de agentes
"""

from fastapi import APIRouter, Depends
from .agents import router as agents_router

# Função de autenticação (será passada do main.py)
def get_auth_dependency():
    """Retorna dependência de autenticação (será injetada pelo main.py)"""
    return None

router = APIRouter()

# Incluir rotas de agentes
router.include_router(agents_router, tags=["Agentes"])

@router.get("/")
async def v1_root():
    """Endpoint raiz da v1"""
    return {
        "message": "Sistema RAG - API de Agentes v1",
        "available_endpoints": {
            "agents": "/agents - Listar agentes disponíveis",
            "agent_info": "/agents/{agent_id} - Informações do agente",
            "ask_agent": "/agents/{agent_id}/ask - Fazer pergunta",
            "clear_history": "/agents/{agent_id}/clear - Limpar histórico",
            "get_history": "/agents/{agent_id}/history - Obter histórico",
            "test_agent": "/agents/{agent_id}/test - Testar agente"
        }
    }