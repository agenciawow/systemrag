"""
Cliente Zep para gerenciamento de memória e sessões

Integração com a API Zep para:
- Gerenciar usuários
- Gerenciar sessões
- Buscar memória e histórico de mensagens
- Adicionar novas mensagens
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

# Zep official SDK imports
from zep_cloud.client import Zep
from zep_cloud.types import Message

logger = logging.getLogger(__name__)

@dataclass
class ZepMessage:
    """Estrutura de uma mensagem no Zep"""
    content: str
    role_type: str = "norole"  # pode ser "user", "assistant", ou "system"
    timestamp: Optional[str] = None

@dataclass
class ZepSession:
    """Estrutura de uma sessão no Zep"""
    session_id: str
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class ZepUser:
    """Estrutura de um usuário no Zep"""
    user_id: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ZepClient:
    """
    Cliente para integração com a API Zep usando o SDK oficial
    
    Funcionalidades:
    - Gerenciamento de usuários
    - Gerenciamento de sessões
    - Busca de memória e histórico
    - Adição de mensagens
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Inicializa o cliente Zep com o SDK oficial
        
        Args:
            api_key: Chave da API Zep (usa variável de ambiente se não fornecida)
        """
        self.api_key = api_key or os.getenv("ZEP_API_KEY")
        if not self.api_key or not self.api_key.strip():
            raise ValueError("ZEP_API_KEY não encontrada ou está vazia nas variáveis de ambiente")
        
        # Inicializar cliente oficial do Zep
        self.client = Zep(api_key=self.api_key)
        
        logger.info(f"Cliente Zep oficial inicializado")
    
    
    def get_user(self, user_id: str) -> Optional[ZepUser]:
        """
        Busca um usuário por ID usando o SDK oficial
        
        Args:
            user_id: ID do usuário
            
        Returns:
            ZepUser se encontrado, None caso contrário
        """
        logger.info(f"Buscando usuário: {user_id}")
        
        try:
            user = self.client.user.get(user_id=user_id)
            
            return ZepUser(
                user_id=user.user_id,
                created_at=str(user.created_at) if user.created_at else None,
                updated_at=str(user.updated_at) if user.updated_at else None
            )
        except Exception as e:
            logger.info(f"Usuário {user_id} não encontrado: {e}")
            return None
    
    def create_user(self, user_id: str) -> ZepUser:
        """
        Cria um novo usuário usando o SDK oficial
        
        Args:
            user_id: ID do usuário a ser criado
            
        Returns:
            ZepUser criado
        """
        logger.info(f"Criando usuário: {user_id}")
        
        try:
            user = self.client.user.add(user_id=user_id)
            
            return ZepUser(
                user_id=user.user_id,
                created_at=str(user.created_at) if user.created_at else None,
                updated_at=str(user.updated_at) if user.updated_at else None
            )
        except Exception as e:
            # Se usuário já existe, tentar buscá-lo
            if "already exists" in str(e).lower():
                logger.info(f"Usuário {user_id} já existe, buscando...")
                existing_user = self.get_user(user_id)
                if existing_user:
                    return existing_user
            raise e
    
    def ensure_user_exists(self, user_id: str) -> ZepUser:
        """
        Garante que um usuário existe, criando se necessário
        
        Args:
            user_id: ID do usuário
            
        Returns:
            ZepUser existente ou criado
        """
        user = self.get_user(user_id)
        if user is None:
            logger.info(f"Usuário {user_id} não existe, criando...")
            user = self.create_user(user_id)
        else:
            logger.info(f"Usuário {user_id} já existe")
        
        return user
    
    def get_session_memory(self, session_id: str, last_n: Optional[int] = None, min_rating: Optional[float] = None) -> Dict[str, Any]:
        """
        Busca a memória de uma sessão usando o SDK oficial
        
        Args:
            session_id: ID da sessão
            last_n: Número de entradas mais recentes
            min_rating: Rating mínimo para filtrar fatos
            
        Returns:
            Memória da sessão
        """
        logger.info(f"Buscando memória da sessão: {session_id}")
        
        try:
            memory = self.client.memory.get(session_id=session_id, lastn=last_n, min_rating=min_rating)
            
            # Converter o objeto Memory para dict
            result = {"summary": "", "facts": [], "entities": []}
            
            if hasattr(memory, 'summary') and memory.summary:
                result["summary"] = memory.summary
            
            if hasattr(memory, 'facts') and memory.facts:
                result["facts"] = [fact.fact if hasattr(fact, 'fact') else str(fact) for fact in memory.facts]
            
            if hasattr(memory, 'entities') and memory.entities:
                result["entities"] = [entity.name if hasattr(entity, 'name') else str(entity) for entity in memory.entities]
            
            return result
            
        except Exception as e:
            logger.info(f"Memória da sessão {session_id} não encontrada: {e}")
            return {"summary": "", "facts": [], "entities": []}
    
    def get_session_messages(self, session_id: str, limit: int = 10, cursor: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Busca mensagens de uma sessão usando o SDK oficial
        
        Args:
            session_id: ID da sessão
            limit: Limite de mensagens a retornar
            cursor: Cursor para paginação
            
        Returns:
            Lista de mensagens
        """
        logger.info(f"Buscando mensagens da sessão: {session_id} (limite: {limit})")
        
        try:
            messages_response = self.client.memory.get_session_messages(
                session_id=session_id,
                limit=limit,
                cursor=cursor
            )
            
            # Converter mensagens para formato dict compatível
            messages = []
            for msg in messages_response.messages:
                message_dict = {
                    "content": msg.content,
                    "role_type": msg.role_type,
                    "created_at": str(msg.created_at) if msg.created_at else None,
                    "uuid": str(getattr(msg, 'uuid', None)) if hasattr(msg, 'uuid') and getattr(msg, 'uuid', None) else None
                }
                messages.append(message_dict)
            
            return messages
            
        except Exception as e:
            logger.info(f"Mensagens da sessão {session_id} não encontradas: {e}")
            return []
    
    def add_memory_to_session(self, session_id: str, messages: List[ZepMessage], user_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Adiciona memória a uma sessão usando o SDK oficial
        
        Args:
            session_id: ID da sessão
            messages: Lista de mensagens a adicionar
            user_id: ID do usuário (necessário para criar sessão se não existir)
            
        Returns:
            Resposta da API
        """
        logger.info(f"Adicionando {len(messages)} mensagens à sessão: {session_id}")
        
        # Garantir que a sessão existe com o user_id correto
        if user_id:
            self._ensure_session_exists(session_id, user_id)
        
        # Converter mensagens para o formato SDK
        sdk_messages = []
        for msg in messages:
            sdk_message = Message(
                content=msg.content,
                role_type=msg.role_type
            )
            sdk_messages.append(sdk_message)
        
        # Adicionar mensagens usando o SDK
        result = self.client.memory.add(session_id=session_id, messages=sdk_messages)
        
        return {"success": True, "result": str(result)}
    
    def ensure_session_context(self, session_id: str, user_id: str) -> Tuple[str, List[Dict[str, Any]], bool]:
        """
        Garante que usuário e sessão existem e busca contexto completo
        
        Fluxo exato:
        1. Verificar se usuário existe → se não, criar
        2. Verificar se sessão existe (via Get Messages) → se não, será criada na primeira mensagem
        3. Buscar contexto: Get Session Memory + Get Messages for Session (limite 10)
        
        Args:
            session_id: ID da sessão
            user_id: ID do usuário
            
        Returns:
            Tupla (contexto_memoria, mensagens_recentes, is_new_session)
        """
        logger.info(f"🔄 Iniciando fluxo Zep para usuário {user_id}, sessão {session_id}")
        
        # 1. Verificar se usuário existe, se não existir criar
        logger.info(f"👤 Verificando usuário: {user_id}")
        user = self.get_user(user_id)
        if user is None:
            logger.info(f"👤 Usuário {user_id} não existe, criando...")
            user = self.create_user(user_id)
            logger.info(f"✅ Usuário {user_id} criado")
        else:
            logger.info(f"✅ Usuário {user_id} já existe")
        
        # 2. Verificar se sessão existe (tentando buscar mensagens)
        logger.info(f"💬 Verificando sessão: {session_id}")
        messages = self.get_session_messages(session_id, limit=10)
        is_new_session = len(messages) == 0
        
        if is_new_session:
            logger.info(f"🆕 Sessão {session_id} é nova (0 mensagens)")
        else:
            logger.info(f"✅ Sessão {session_id} já existe ({len(messages)} mensagens)")
        
        # 3. Buscar memória da sessão
        logger.info(f"🧠 Buscando memória da sessão: {session_id}")
        memory = self.get_session_memory(session_id, last_n=5)
        
        # Construir contexto de memória
        memory_context = ""
        if memory and not is_new_session:
            # Tratar caso onde memory pode ser string ou objeto
            if isinstance(memory, str):
                memory_context += f"Resumo da conversa: {memory}\n\n"
            elif isinstance(memory, dict):
                summary = memory.get("summary", "")
                facts = memory.get("facts", [])
                
                if summary:
                    memory_context += f"Resumo da conversa: {summary}\n\n"
                
                if facts:
                    memory_context += "Fatos importantes:\n"
                    for fact in facts[:5]:  # Últimos 5 fatos
                        if isinstance(fact, dict):
                            memory_context += f"- {fact.get('fact', '')}\n"
                        else:
                            memory_context += f"- {fact}\n"
                    memory_context += "\n"
        
        logger.info(f"📊 Contexto preparado: {len(memory_context)} chars de memória, {len(messages)} mensagens, nova_sessão={is_new_session}")
        
        return memory_context, messages, is_new_session
    
    def _ensure_session_exists(self, session_id: str, user_id: str) -> None:
        """
        Garante que uma sessão existe com o user_id correto
        
        Args:
            session_id: ID da sessão
            user_id: ID do usuário
        """
        try:
            # Tentar buscar a sessão para verificar se existe
            session = self.client.memory.get_session(session_id=session_id)
            logger.info(f"Sessão {session_id} já existe para usuário {session.user_id}")
        except Exception:
            # Se não existir, criar sessão explicitamente com user_id
            logger.info(f"Criando sessão {session_id} para usuário {user_id}")
            try:
                result = self.client.memory.add_session(
                    session_id=session_id,
                    user_id=user_id
                )
                logger.info(f"✅ Sessão {session_id} criada para usuário {user_id}: {result.session_id}")
            except Exception as e:
                logger.warning(f"Erro ao criar sessão {session_id}: {e} - será criada implicitamente")
    
    def save_conversation_turn(self, session_id: str, user_message: str, assistant_response: str, user_id: Optional[str] = None) -> None:
        """
        Salva uma volta de conversa (pergunta + resposta) na sessão
        
        Args:
            session_id: ID da sessão
            user_message: Mensagem do usuário
            assistant_response: Resposta do assistente
            user_id: ID do usuário (necessário para criar sessão se não existir)
        """
        messages = [
            ZepMessage(content=user_message, role_type="user"),
            ZepMessage(content=assistant_response, role_type="assistant")
        ]
        
        try:
            self.add_memory_to_session(session_id, messages, user_id)
            logger.info(f"Conversa salva na sessão {session_id}")
        except Exception as e:
            logger.error(f"Erro ao salvar conversa na sessão {session_id}: {e}")
            # Não falha se não conseguir salvar


# Instância global do cliente
zep_client = None

def get_zep_client() -> ZepClient:
    """
    Obtém instância global do cliente Zep
    
    Returns:
        Instância do ZepClient
    """
    global zep_client
    
    if zep_client is None:
        try:
            zep_client = ZepClient()
            logger.info("Cliente Zep inicializado com sucesso")
        except ValueError as e:
            # Erro de configuração - crítico
            logger.error(f"Erro de configuração do Zep: {e}")
            raise e
        except Exception as e:
            # Outros erros - warning mas não falha
            logger.warning(f"Não foi possível inicializar cliente Zep: {e}")
            zep_client = None
    
    return zep_client

def is_zep_available() -> bool:
    """
    Verifica se o Zep está disponível e configurado
    
    Returns:
        True se Zep estiver disponível
    """
    return get_zep_client() is not None