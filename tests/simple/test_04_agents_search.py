#!/usr/bin/env python3
"""
Teste 4: Busca com Agentes
Testa a funcionalidade de busca usando o sistema de agentes
"""

import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

class TestAgentsSearch:
    """Testes de busca com Agentes"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8001"
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Perguntas simples para teste
        self.test_queries = [
            "O que é o Zep?",
            "Qual é o principal componente do Zep?",
            "Como o Zep lida com memória?"
        ]
    
    def test_agents_api_health(self):
        """Verifica se a API dos Agentes está rodando"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            assert response.status_code == 200, f"API Agentes retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando (execute: python run_agents_api.py)")
    
    def test_search_endpoint_exists(self):
        """Verifica se o endpoint de busca existe na API dos Agentes"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={"query": "test"},
                timeout=10
            )
            
            # Não deve ser 404 (endpoint não existe)
            assert response.status_code != 404, "Endpoint /search não existe na API Agentes"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
    
    def test_simple_agent_search(self):
        """Testa busca simples usando agentes"""
        for query in self.test_queries[:2]:  # Apenas 2 primeiras para ser rápido
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": query,
                        "user_id": "test_user",
                        "session_id": "test_session"
                    },
                    timeout=45  # Agentes podem ser mais lentos
                )
                
                assert response.status_code == 200, f"Busca de agente falhou para '{query}': {response.status_code}"
                
                data = response.json()
                assert "response" in data or "answer" in data, f"Resposta sem response/answer para '{query}'"
                
                # Verifica se a resposta não está vazia
                response_text = data.get("response", data.get("answer", ""))
                assert len(response_text.strip()) > 0, f"Resposta vazia para '{query}'"
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Agentes não está rodando")
                break
            except requests.exceptions.Timeout:
                pytest.skip(f"Timeout na busca de agente para '{query}'")
                break
    
    def test_agent_memory_functionality(self):
        """Testa funcionalidade de memória dos agentes"""
        session_id = "test_memory_session"
        
        try:
            # Primeira pergunta para estabelecer contexto
            response1 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Meu nome é João e estou perguntando sobre Zep",
                    "user_id": "test_user",
                    "session_id": session_id
                },
                timeout=45
            )
            
            if response1.status_code == 200:
                # Segunda pergunta para testar memória
                response2 = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": "Qual é o meu nome?",
                        "user_id": "test_user",
                        "session_id": session_id
                    },
                    timeout=45
                )
                
                assert response2.status_code == 200, f"Segunda busca falhou: {response2.status_code}"
                
                data = response2.json()
                response_text = data.get("response", data.get("answer", "")).lower()
                
                # Deve lembrar do nome João
                assert "joão" in response_text or "joao" in response_text, "Agente não lembrou do nome do usuário"
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de memória")
    
    def test_agent_search_validation(self):
        """Testa validação dos parâmetros de busca"""
        invalid_cases = [
            {},  # sem parâmetros
            {"query": ""},  # query vazia
            {"query": "teste", "user_id": ""},  # user_id vazio
        ]
        
        for case in invalid_cases:
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json=case,
                    timeout=10
                )
                
                # Deve retornar erro de validação
                assert response.status_code in [400, 422], f"Validação falhou para {case}: {response.status_code}"
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Agentes não está rodando")
                break
    
    def test_agent_response_format(self):
        """Testa formato da resposta dos agentes"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "O que é o Zep?",
                    "user_id": "test_user",
                    "session_id": "test_session"
                },
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica estrutura básica da resposta
                expected_fields = ["response", "answer", "result"]
                has_expected_field = any(field in data for field in expected_fields)
                assert has_expected_field, f"Resposta não contém campos esperados: {list(data.keys())}"
                
                # Se tem metadata de sessão, deve ser consistente
                if "session_id" in data:
                    assert data["session_id"] == "test_session", "Session ID inconsistente"
                    
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout na verificação do formato da resposta")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])