#!/usr/bin/env python3
"""
Testes de integração com Zep Memory Management

Este módulo testa a integração completa com o Zep para gerenciamento de memória,
incluindo criação de usuários, sessões, e persistência de mensagens.
"""

import pytest
import logging
import os
from datetime import datetime
from typing import Optional

from agents.core.zep_client import get_zep_client, is_zep_available, ZepMessage, ZepClient
from agents.core.operator import agent_operator

logger = logging.getLogger(__name__)

# Fixtures
@pytest.fixture
def zep_client() -> Optional[ZepClient]:
    """Fixture para cliente Zep"""
    if not is_zep_available():
        pytest.skip("Zep não disponível - configure ZEP_API_KEY")
    return get_zep_client()

@pytest.fixture
def unique_user_id() -> str:
    """Fixture para ID único de usuário"""
    timestamp = int(datetime.now().timestamp())
    return f"test_user_{timestamp}"

@pytest.fixture
def unique_session_id() -> str:
    """Fixture para ID único de sessão"""
    timestamp = int(datetime.now().timestamp())
    return f"test_session_{timestamp}"

# Testes básicos do Zep Client
class TestZepClient:
    """Testes básicos do cliente Zep"""
    
    def test_zep_available(self):
        """Testa se Zep está disponível"""
        # Se não tiver API key, deve retornar False
        if not os.getenv("ZEP_API_KEY"):
            assert not is_zep_available()
        else:
            assert is_zep_available()
    
    def test_client_initialization(self, zep_client):
        """Testa inicialização do cliente"""
        assert zep_client is not None
        assert hasattr(zep_client, 'client')
    
    def test_user_creation(self, zep_client, unique_user_id):
        """Testa criação de usuário"""
        # Criar usuário
        user = zep_client.create_user(unique_user_id)
        assert user.user_id == unique_user_id
        assert user.created_at is not None
        
        # Verificar se usuário existe
        existing_user = zep_client.get_user(unique_user_id)
        assert existing_user is not None
        assert existing_user.user_id == unique_user_id
    
    def test_user_already_exists(self, zep_client, unique_user_id):
        """Testa tratamento de usuário já existente"""
        # Criar usuário
        user1 = zep_client.create_user(unique_user_id)
        
        # Tentar criar novamente (deve retornar usuário existente)
        user2 = zep_client.create_user(unique_user_id)
        assert user2.user_id == unique_user_id
    
    def test_session_creation_with_user_binding(self, zep_client, unique_user_id, unique_session_id):
        """Testa criação de sessão com vinculação correta ao usuário"""
        # Criar usuário primeiro
        user = zep_client.create_user(unique_user_id)
        
        # Criar sessão vinculada ao usuário
        zep_client._ensure_session_exists(unique_session_id, unique_user_id)
        
        # Verificar se sessão foi criada corretamente
        session = zep_client.client.memory.get_session(session_id=unique_session_id)
        assert session.session_id == unique_session_id
        assert session.user_id == unique_user_id
    
    def test_message_persistence(self, zep_client, unique_user_id, unique_session_id):
        """Testa persistência de mensagens"""
        # Criar usuário e sessão
        user = zep_client.create_user(unique_user_id)
        
        # Adicionar mensagens
        messages = [
            ZepMessage(content="Olá, meu nome é João", role_type="user"),
            ZepMessage(content="Olá João! Como posso ajudar?", role_type="assistant")
        ]
        
        result = zep_client.add_memory_to_session(unique_session_id, messages, unique_user_id)
        assert result["success"] is True
        
        # Verificar se mensagens foram salvas
        saved_messages = zep_client.get_session_messages(unique_session_id, limit=10)
        assert len(saved_messages) >= 2
        
        # Verificar conteúdo das mensagens
        user_msg = next((msg for msg in saved_messages if msg["role_type"] == "user"), None)
        assistant_msg = next((msg for msg in saved_messages if msg["role_type"] == "assistant"), None)
        
        assert user_msg is not None
        assert "João" in user_msg["content"]
        assert assistant_msg is not None
        assert "João" in assistant_msg["content"]
    
    def test_memory_generation(self, zep_client, unique_user_id, unique_session_id):
        """Testa geração de memória"""
        # Criar usuário
        user = zep_client.create_user(unique_user_id)
        
        # Adicionar algumas mensagens para gerar memória
        messages = [
            ZepMessage(content="Meu nome é Maria Silva e sou desenvolvedora", role_type="user"),
            ZepMessage(content="Prazer em conhecê-la, Maria!", role_type="assistant"),
            ZepMessage(content="Trabalho com Python e Machine Learning", role_type="user"),
            ZepMessage(content="Que interessante! Python é uma excelente linguagem.", role_type="assistant")
        ]
        
        for i in range(0, len(messages), 2):
            batch = messages[i:i+2]
            zep_client.add_memory_to_session(unique_session_id, batch, unique_user_id)
        
        # Dar tempo para o Zep processar
        import time
        time.sleep(2)
        
        # Buscar memória
        memory = zep_client.get_session_memory(unique_session_id)
        assert memory is not None
        
        # Verificar se memória contém informações relevantes
        if isinstance(memory, dict) and memory.get("summary"):
            summary = memory["summary"]
            if isinstance(summary, str):
                assert "maria" in summary.lower() or "desenvolvedora" in summary.lower()
    
    def test_context_retrieval(self, zep_client, unique_user_id, unique_session_id):
        """Testa recuperação de contexto completo"""
        # Criar usuário
        user = zep_client.create_user(unique_user_id)
        
        # Adicionar mensagens
        messages = [
            ZepMessage(content="Sou chef de cozinha", role_type="user"),
            ZepMessage(content="Que legal! Deve ser uma profissão interessante.", role_type="assistant")
        ]
        
        zep_client.add_memory_to_session(unique_session_id, messages, unique_user_id)
        
        # Recuperar contexto
        memory_context, session_messages, is_new = zep_client.ensure_session_context(unique_session_id, unique_user_id)
        
        assert is_new is False  # Sessão já existe
        assert len(session_messages) >= 2
        assert isinstance(memory_context, str)

# Testes de integração com agentes
class TestZepAgentIntegration:
    """Testes de integração Zep com agentes"""
    
    def test_agent_with_zep_flow(self, unique_user_id, unique_session_id):
        """Testa fluxo completo de agente com Zep"""
        if not is_zep_available():
            pytest.skip("Zep não disponível")
        
        # Obter agente
        agent = agent_operator.get_agent("rag-search")
        
        # Primeira mensagem - deve criar usuário e sessão
        response1 = agent.ask(
            "Olá! Meu nome é Pedro e sou engenheiro.", 
            user_id=unique_user_id, 
            session_id=unique_session_id
        )
        assert response1 is not None
        assert len(response1) > 0
        
        # Segunda mensagem - deve usar contexto
        response2 = agent.ask(
            "Você se lembra do meu nome?", 
            user_id=unique_user_id, 
            session_id=unique_session_id
        )
        assert response2 is not None
        # O agente deve mencionar o nome ou confirmar que lembra
        # (pode não funcionar imediatamente devido ao tempo de processamento do Zep)
    
    def test_agent_memory_persistence(self, unique_user_id, unique_session_id):
        """Testa persistência de memória entre chamadas do agente"""
        if not is_zep_available():
            pytest.skip("Zep não disponível")
        
        agent = agent_operator.get_agent("rag-search")
        
        # Sequência de mensagens para testar persistência
        messages = [
            "Meu nome é Ana e trabalho como designer",
            "Gosto muito de cores vibrantes",
            "Trabalho principalmente com identidade visual"
        ]
        
        responses = []
        for msg in messages:
            response = agent.ask(msg, user_id=unique_user_id, session_id=unique_session_id)
            responses.append(response)
            assert response is not None
        
        # Verificar se mensagens foram persistidas no Zep
        zep_client = get_zep_client()
        if zep_client:
            session_messages = zep_client.get_session_messages(unique_session_id, limit=10)
            # Deve haver pelo menos 6 mensagens (3 user + 3 assistant)
            assert len(session_messages) >= 6

# Testes de robustez
class TestZepRobustness:
    """Testes de robustez e casos extremos"""
    
    def test_invalid_session_handling(self, zep_client):
        """Testa tratamento de sessão inválida"""
        # Tentar buscar sessão que não existe
        messages = zep_client.get_session_messages("sessao_inexistente", limit=10)
        assert messages == []
        
        memory = zep_client.get_session_memory("sessao_inexistente")
        assert memory == {"summary": "", "facts": [], "entities": []}
    
    def test_empty_message_handling(self, zep_client, unique_user_id, unique_session_id):
        """Testa tratamento de mensagens vazias"""
        user = zep_client.create_user(unique_user_id)
        
        # Tentar adicionar mensagem vazia
        empty_messages = [ZepMessage(content="", role_type="user")]
        result = zep_client.add_memory_to_session(unique_session_id, empty_messages, unique_user_id)
        assert result["success"] is True
    
    def test_large_message_handling(self, zep_client, unique_user_id, unique_session_id):
        """Testa tratamento de mensagens grandes"""
        user = zep_client.create_user(unique_user_id)
        
        # Criar mensagem grande (mas não excessiva)
        large_content = "Esta é uma mensagem longa. " * 100  # ~2700 chars
        large_messages = [ZepMessage(content=large_content, role_type="user")]
        
        result = zep_client.add_memory_to_session(unique_session_id, large_messages, unique_user_id)
        assert result["success"] is True
        
        # Verificar se foi salva
        saved_messages = zep_client.get_session_messages(unique_session_id, limit=10)
        assert len(saved_messages) >= 1

# Configuração de testes
def test_zep_configuration():
    """Testa configuração do Zep"""
    # Verificar se variáveis de ambiente necessárias estão configuradas
    api_key = os.getenv("ZEP_API_KEY")
    if api_key:
        assert len(api_key) > 10  # API key deve ter tamanho razoável
        assert not api_key.startswith("your-")  # Não deve ser placeholder

if __name__ == "__main__":
    # Executar testes se chamado diretamente
    pytest.main([__file__, "-v"])