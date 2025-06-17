"""
Rotas para agentes com descoberta automática

Inspirado no padrão do framework Agno para descoberta dinâmica.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any, List, Optional
from pydantic import BaseModel
import logging
import inspect
from datetime import datetime

from agents.core.operator import agent_operator
from ..auth import get_api_key

logger = logging.getLogger(__name__)

router = APIRouter()


class AgentRequest(BaseModel):
    """Request para interação com agente"""
    message: str
    user_id: str  # OBRIGATÓRIO para Zep
    session_id: str  # OBRIGATÓRIO para Zep
    clear_history: bool = False


class AgentResponse(BaseModel):
    """Response do agente"""
    agent_id: str
    response: str
    session_id: Optional[str] = None
    timestamp: str
    metadata: Dict[str, Any] = {}


@router.get("/agents")
async def list_available_agents(api_key: str = Depends(get_api_key)):
    """
    Lista todos os agentes disponíveis
    
    Descoberta automática de agentes na pasta agents/
    """
    try:
        agents = agent_operator.list_agents()
        return {
            "agents": agents,
            "count": len(agents),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Erro ao listar agentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/agents/{agent_id}")
async def get_agent_info(agent_id: str, api_key: str = Depends(get_api_key)):
    """
    Obtém informações sobre um agente específico
    
    Args:
        agent_id: ID do agente
    """
    try:
        if not agent_operator.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")
        
        agent_info = agent_operator.get_agent_info(agent_id)
        
        # Obter estatísticas do agente se possível
        try:
            agent = agent_operator.get_agent(agent_id)
            if hasattr(agent, 'get_agent_stats'):
                stats = agent.get_agent_stats()
                agent_info['stats'] = stats
        except Exception as e:
            agent_info['stats_error'] = str(e)
        
        return {
            "agent": agent_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter info do agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/agents/{agent_id}/ask")
async def ask_agent(agent_id: str, request: AgentRequest, api_key: str = Depends(get_api_key)):
    """
    Faz uma pergunta para um agente específico
    
    Args:
        agent_id: ID do agente
        request: Dados da pergunta
    """
    try:
        # Validar parâmetros obrigatórios do Zep
        if not request.user_id or not request.user_id.strip() or len(request.user_id.strip()) < 3:
            raise HTTPException(status_code=400, detail="user_id é obrigatório e deve ter pelo menos 3 caracteres")
        if not request.session_id or not request.session_id.strip() or len(request.session_id.strip()) < 3:
            raise HTTPException(status_code=400, detail="session_id é obrigatório e deve ter pelo menos 3 caracteres")
        
        # Validar caracteres alfanuméricos (segurança)
        if not request.user_id.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail="user_id deve conter apenas letras, números, hífens e underscores")
        if not request.session_id.replace("-", "").replace("_", "").isalnum():
            raise HTTPException(status_code=400, detail="session_id deve conter apenas letras, números, hífens e underscores")
        
        if not agent_operator.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")
        
        # Obter instância do agente
        agent = agent_operator.get_agent(agent_id)
        
        # Limpar histórico se solicitado
        if request.clear_history and hasattr(agent, 'clear_history'):
            agent.clear_history()
        
        # Fazer pergunta ao agente COM Zep (sempre)
        if hasattr(agent, 'ask'):
            # Verificar se o agente suporta user_id e session_id
            sig = inspect.signature(agent.ask)
            
            if 'user_id' in sig.parameters and 'session_id' in sig.parameters:
                # Agente suporta Zep - usar parâmetros validados
                response_text = agent.ask(
                    request.message, 
                    user_id=request.user_id, 
                    session_id=request.session_id
                )
                logger.info(f"✅ Pergunta enviada ao agente '{agent_id}' com Zep (user: {request.user_id}, session: {request.session_id})")
            else:
                # Agente não suporta Zep
                raise HTTPException(
                    status_code=500, 
                    detail=f"Agente '{agent_id}' não suporta user_id/session_id. Atualize o agente para usar Zep."
                )
        else:
            raise HTTPException(status_code=500, detail=f"Agente '{agent_id}' não tem método 'ask'")
        
        # Obter metadados se disponível
        metadata = {}
        if hasattr(agent, 'get_chat_history'):
            history = agent.get_chat_history()
            metadata['chat_history_length'] = len(history)
        
        response = AgentResponse(
            agent_id=agent_id,
            response=response_text,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat(),
            metadata=metadata
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao processar pergunta para agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento: {str(e)}")


@router.post("/agents/{agent_id}/clear")
async def clear_agent_history(agent_id: str, api_key: str = Depends(get_api_key)):
    """
    Limpa o histórico de um agente
    
    Args:
        agent_id: ID do agente
    """
    try:
        if not agent_operator.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")
        
        agent = agent_operator.get_agent(agent_id)
        
        if hasattr(agent, 'clear_history'):
            agent.clear_history()
            return {
                "message": f"Histórico do agente '{agent_id}' limpo com sucesso",
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Agente '{agent_id}' não suporta limpeza de histórico")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao limpar histórico do agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/agents/{agent_id}/history")
async def get_agent_history(agent_id: str, api_key: str = Depends(get_api_key)):
    """
    Obtém o histórico de conversa de um agente
    
    Args:
        agent_id: ID do agente
    """
    try:
        if not agent_operator.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")
        
        agent = agent_operator.get_agent(agent_id)
        
        if hasattr(agent, 'get_chat_history'):
            history = agent.get_chat_history()
            return {
                "agent_id": agent_id,
                "history": history,
                "length": len(history),
                "timestamp": datetime.now().isoformat()
            }
        else:
            raise HTTPException(status_code=400, detail=f"Agente '{agent_id}' não suporta histórico")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao obter histórico do agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.get("/agents/{agent_id}/test")
async def test_agent(agent_id: str, api_key: str = Depends(get_api_key)):
    """
    Testa a funcionalidade de um agente
    
    Args:
        agent_id: ID do agente
    """
    try:
        if not agent_operator.agent_exists(agent_id):
            raise HTTPException(status_code=404, detail=f"Agente '{agent_id}' não encontrado")
        
        agent = agent_operator.get_agent(agent_id)
        
        if hasattr(agent, 'test_agent'):
            test_result = agent.test_agent()
            return {
                "agent_id": agent_id,
                "test_result": test_result,
                "timestamp": datetime.now().isoformat()
            }
        else:
            return {
                "agent_id": agent_id,
                "test_result": {
                    "status": "limited",
                    "message": "Agente não implementa teste completo"
                },
                "timestamp": datetime.now().isoformat()
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao testar agente {agent_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@router.post("/agents/refresh")
async def refresh_agents(api_key: str = Depends(get_api_key)):
    """
    Recarrega a descoberta de agentes
    
    Útil para desenvolvimento quando novos agentes são adicionados
    """
    try:
        agent_operator.refresh_agents()
        agents = agent_operator.list_agents()
        
        return {
            "message": "Agentes recarregados com sucesso",
            "agents_found": len(agents),
            "agents": agents,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Erro ao recarregar agentes: {e}")
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")