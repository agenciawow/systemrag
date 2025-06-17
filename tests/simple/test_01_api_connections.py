#!/usr/bin/env python3
"""
Teste 1: APIs e Conexões
Testa conectividade básica com todas as APIs necessárias
"""

import os
import pytest
import requests
from dotenv import load_dotenv

load_dotenv()

class TestAPIConnections:
    """Testes de conectividade com APIs"""
    
    def test_openai_api_key_exists(self):
        """Verifica se a chave da OpenAI está configurada"""
        api_key = os.getenv("OPENAI_API_KEY")
        assert api_key is not None, "OPENAI_API_KEY não configurada"
        assert api_key.startswith("sk-"), "OPENAI_API_KEY com formato inválido"
    
    def test_voyage_api_key_exists(self):
        """Verifica se a chave da Voyage está configurada"""
        api_key = os.getenv("VOYAGE_API_KEY")
        assert api_key is not None, "VOYAGE_API_KEY não configurada"
        assert len(api_key) > 10, "VOYAGE_API_KEY muito curta"
    
    def test_llama_cloud_api_key_exists(self):
        """Verifica se a chave do Llama Cloud está configurada"""
        api_key = os.getenv("LLAMA_CLOUD_API_KEY")
        assert api_key is not None, "LLAMA_CLOUD_API_KEY não configurada"
        assert api_key.startswith("llx-"), "LLAMA_CLOUD_API_KEY com formato inválido"
    
    def test_zep_api_key_exists(self):
        """Verifica se a chave do Zep está configurada"""
        api_key = os.getenv("ZEP_API_KEY")
        assert api_key is not None, "ZEP_API_KEY não configurada"
        assert len(api_key) > 20, "ZEP_API_KEY muito curta"
    
    def test_astra_db_configuration(self):
        """Verifica se o Astra DB está configurado"""
        token = os.getenv("ASTRA_DB_APPLICATION_TOKEN")
        endpoint = os.getenv("ASTRA_DB_API_ENDPOINT")
        keyspace = os.getenv("ASTRA_DB_KEYSPACE")
        collection = os.getenv("ASTRA_DB_COLLECTION")
        
        assert token is not None, "ASTRA_DB_APPLICATION_TOKEN não configurado"
        assert endpoint is not None, "ASTRA_DB_API_ENDPOINT não configurado"
        assert keyspace is not None, "ASTRA_DB_KEYSPACE não configurado"
        assert collection is not None, "ASTRA_DB_COLLECTION não configurado"
        
        assert token.startswith("AstraCS:"), "Token Astra DB com formato inválido"
        assert endpoint.startswith("https://"), "Endpoint Astra DB com formato inválido"
    
    def test_cloudflare_r2_configuration(self):
        """Verifica se o Cloudflare R2 está configurado"""
        endpoint = os.getenv("R2_ENDPOINT")
        token = os.getenv("R2_AUTH_TOKEN")
        
        assert endpoint is not None, "R2_ENDPOINT não configurado"
        assert token is not None, "R2_AUTH_TOKEN não configurado"
        assert endpoint.startswith("https://"), "R2_ENDPOINT com formato inválido"
    
    def test_system_rag_api_health(self):
        """Testa se a API do Sistema RAG está respondendo"""
        try:
            response = requests.get("http://localhost:8000/health", timeout=5)
            assert response.status_code == 200, f"API Sistema RAG retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando (execute: python run_system_api.py)")
    
    def test_agents_api_health(self):
        """Testa se a API dos Agentes está respondendo"""
        try:
            response = requests.get("http://localhost:8001/health", timeout=5)
            assert response.status_code == 200, f"API Agentes retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando (execute: python run_agents_api.py)")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])