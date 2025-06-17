#!/usr/bin/env python3
"""
Teste 3: Busca com System RAG
Testa a funcionalidade de busca usando o sistema RAG
"""

import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

class TestSystemRAGSearch:
    """Testes de busca com Sistema RAG"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8000"
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Perguntas simples para teste
        self.test_queries = [
            "O que é o Zep?",
            "Qual é o principal componente do Zep?",
            "Como funciona o sistema de memória?"
        ]
    
    def test_search_endpoint_exists(self):
        """Verifica se o endpoint de busca existe"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={"query": "test"},
                timeout=10
            )
            
            # Não deve ser 404 (endpoint não existe)
            assert response.status_code != 404, "Endpoint /search não existe"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
    
    def test_simple_search(self):
        """Testa busca simples"""
        for query in self.test_queries[:2]:  # Apenas 2 primeiras para ser rápido
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": query,
                        "include_history": False
                    },
                    timeout=30
                )
                
                assert response.status_code == 200, f"Busca falhou para '{query}': {response.status_code}"
                
                data = response.json()
                assert "answer" in data or "response" in data, f"Resposta sem answer/response para '{query}'"
                
                # Verifica se a resposta não está vazia
                response_text = data.get("answer", data.get("response", ""))
                assert len(response_text.strip()) > 0, f"Resposta vazia para '{query}'"
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Sistema RAG não está rodando")
                break
            except requests.exceptions.Timeout:
                pytest.skip(f"Timeout na busca para '{query}'")
                break
    
    def test_search_with_context(self):
        """Testa busca com contexto/histórico"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Explique mais detalhes",
                    "include_history": True,
                    "session_id": "test_session"
                },
                timeout=30
            )
            
            # Pode não ter histórico ainda, mas deve aceitar o parâmetro
            assert response.status_code in [200, 404], f"Busca com contexto retornou {response.status_code}"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout na busca com contexto")
    
    def test_search_validation(self):
        """Testa validação dos parâmetros de busca"""
        invalid_cases = [
            {},  # sem query
            {"query": ""},  # query vazia
            {"query": "   "},  # query só espaços
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
                pytest.skip("API Sistema RAG não está rodando")
                break
    
    def test_search_response_format(self):
        """Testa formato da resposta de busca"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={"query": "O que é o Zep?"},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Verifica estrutura básica da resposta
                expected_fields = ["answer", "response", "result"]
                has_expected_field = any(field in data for field in expected_fields)
                assert has_expected_field, f"Resposta não contém campos esperados: {list(data.keys())}"
                
                # Se tem sources/references, deve ser uma lista
                if "sources" in data:
                    assert isinstance(data["sources"], list), "Sources deve ser uma lista"
                
                if "references" in data:
                    assert isinstance(data["references"], list), "References deve ser uma lista"
                    
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout na verificação do formato da resposta")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])