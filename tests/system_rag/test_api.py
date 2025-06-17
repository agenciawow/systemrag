#!/usr/bin/env python3
"""
Testes automatizados para a API REST do Sistema RAG Multimodal

Testa todos os endpoints da FastAPI:
- Health check
- Autenticação
- Busca (/search)
- Avaliação (/evaluate)
- Ingestão (/ingest)
"""

import pytest
import requests
import time
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class TestAPIConfig:
    """Configuração para testes da API"""
    
    BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
    TIMEOUT_SHORT = 30  # 30 segundos para operações rápidas
    TIMEOUT_LONG = 300  # 5 minutos para operações longas
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
    
    @property
    def invalid_headers(self) -> Dict[str, str]:
        return {
            "Authorization": "Bearer chave-invalida-para-teste",
            "Content-Type": "application/json"
        }

@pytest.fixture
def api_config():
    """Fixture com configuração da API"""
    return TestAPIConfig()

@pytest.fixture(scope="session", autouse=True)
def check_api_server():
    """Verifica se o servidor da API está rodando antes dos testes"""
    config = TestAPIConfig()
    
    try:
        response = requests.get(f"{config.BASE_URL}/", timeout=10)
        if response.status_code != 200:
            pytest.fail(f"API não está respondendo corretamente. Status: {response.status_code}")
    except requests.exceptions.RequestException as e:
        pytest.fail(f"API não está acessível. Certifique-se de que está rodando em {config.BASE_URL}. Erro: {e}")

class TestHealthAndBasics:
    """Testes básicos de saúde da API"""
    
    def test_root_endpoint(self, api_config):
        """Testa endpoint raiz"""
        response = requests.get(f"{api_config.BASE_URL}/", timeout=api_config.TIMEOUT_SHORT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "message" in data
        assert "version" in data
        assert "endpoints" in data
        assert "search" in data["endpoints"]
        assert "evaluate" in data["endpoints"]
        assert "ingest" in data["endpoints"]
    
    def test_health_check(self, api_config):
        """Testa health check"""
        response = requests.get(f"{api_config.BASE_URL}/health", timeout=api_config.TIMEOUT_SHORT)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "status" in data
        assert "timestamp" in data
        assert "system_info" in data
        assert data["status"] in ["healthy", "degraded"]
        
        if data["status"] == "healthy":
            assert data["system_info"]["rag_initialized"] is True
    
    def test_docs_endpoint(self, api_config):
        """Testa se documentação automática está disponível"""
        response = requests.get(f"{api_config.BASE_URL}/docs", timeout=api_config.TIMEOUT_SHORT)
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

class TestAuthentication:
    """Testes de autenticação"""
    
    def test_valid_authentication(self, api_config):
        """Testa autenticação válida"""
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"query": "teste auth", "include_history": False},
            timeout=api_config.TIMEOUT_LONG
        )
        
        # Deve ser 200 (sucesso) ou 503 (sistema não inicializado)
        assert response.status_code in [200, 503]
    
    def test_invalid_authentication(self, api_config):
        """Testa rejeição de autenticação inválida"""
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.invalid_headers,
            json={"query": "teste auth", "include_history": False},
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 401
    
    def test_missing_authentication(self, api_config):
        """Testa rejeição quando não há autenticação"""
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            json={"query": "teste auth", "include_history": False},
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 403

class TestSearchEndpoint:
    """Testes do endpoint de busca"""
    
    def test_search_basic(self, api_config):
        """Testa busca básica"""
        start_time = time.time()
        
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"query": "Quais produtos estão disponíveis?", "include_history": False},
            timeout=api_config.TIMEOUT_LONG
        )
        
        response_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estrutura da resposta
        assert "success" in data
        assert "answer" in data
        assert "response_time" in data
        assert "timestamp" in data
        assert "query" in data
        
        assert data["success"] is True
        assert len(data["answer"]) > 0
        assert data["query"] == "Quais produtos estão disponíveis?"
        
        # Verificar performance
        assert response_time < 60  # Deve responder em menos de 1 minuto
    
    def test_search_with_history(self, api_config):
        """Testa busca com histórico"""
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"query": "E sobre as sobremesas?", "include_history": True},
            timeout=api_config.TIMEOUT_LONG
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
    
    def test_search_invalid_data(self, api_config):
        """Testa busca com dados inválidos"""
        # Query vazia
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"query": "", "include_history": False},
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 422  # Validation error
        
        # JSON malformado
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"invalid_field": "test"},
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 422

class TestEvaluationEndpoint:
    """Testes do endpoint de avaliação"""
    
    def test_evaluation_basic(self, api_config):
        """Testa avaliação básica"""
        start_time = time.time()
        
        response = requests.post(
            f"{api_config.BASE_URL}/evaluate",
            headers=api_config.headers,
            timeout=api_config.TIMEOUT_LONG
        )
        
        evaluation_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estrutura da resposta
        assert "success" in data
        assert "total_questions" in data
        assert "success_rate" in data
        assert "average_response_time" in data
        assert "timestamp" in data
        assert "summary" in data
        
        assert data["success"] is True
        assert data["total_questions"] > 0
        assert 0 <= data["success_rate"] <= 1
        assert data["average_response_time"] > 0
        
        # Verificar summary
        summary = data["summary"]
        assert "successful_evaluations" in summary
        assert "failed_evaluations" in summary
        assert "evaluation_duration" in summary
        
        # Verificar performance
        assert evaluation_time < 300  # Deve completar em menos de 5 minutos

class TestIngestionEndpoint:
    """Testes do endpoint de ingestão"""
    
    def test_ingestion_basic(self, api_config):
        """Testa ingestão básica com URL de teste"""
        # URL de teste - PDF público pequeno
        test_url = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
        
        start_time = time.time()
        
        response = requests.post(
            f"{api_config.BASE_URL}/ingest",
            headers=api_config.headers,
            json={
                "document_url": test_url,
                "document_name": "Documento de Teste Automatizado",
                "overwrite": True
            },
            timeout=api_config.TIMEOUT_LONG
        )
        
        processing_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        
        # Verificar estrutura da resposta
        assert "success" in data
        assert "message" in data
        assert "document_name" in data
        assert "chunks_created" in data
        assert "processing_time" in data
        assert "timestamp" in data
        
        assert data["success"] is True
        assert len(data["message"]) > 0
        assert data["chunks_created"] >= 0
        
        # Verificar performance
        assert processing_time < 300  # Deve completar em menos de 5 minutos
    
    def test_ingestion_invalid_url(self, api_config):
        """Testa ingestão com URL inválida"""
        response = requests.post(
            f"{api_config.BASE_URL}/ingest",
            headers=api_config.headers,
            json={
                "document_url": "invalid-url-format",
                "document_name": "Teste Inválido",
                "overwrite": True
            },
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 500  # Internal server error
        data = response.json()
        assert "detail" in data
        assert data["detail"]["success"] is False
    
    def test_ingestion_missing_data(self, api_config):
        """Testa ingestão com dados obrigatórios ausentes"""
        response = requests.post(
            f"{api_config.BASE_URL}/ingest",
            headers=api_config.headers,
            json={
                "document_name": "Sem URL"
            },
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code == 422  # Validation error

class TestPerformanceAndLimits:
    """Testes de performance e limites"""
    
    def test_concurrent_searches(self, api_config):
        """Testa múltiplas buscas simultâneas"""
        import concurrent.futures
        import threading
        
        def make_search(query_num):
            try:
                response = requests.post(
                    f"{api_config.BASE_URL}/search",
                    headers=api_config.headers,
                    json={"query": f"Teste concorrência {query_num}", "include_history": False},
                    timeout=api_config.TIMEOUT_LONG
                )
                return response.status_code == 200
            except:
                return False
        
        # Executar 3 buscas simultâneas
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_search, i) for i in range(3)]
            results = [future.result() for future in futures]
        
        # Pelo menos 2 das 3 devem ter sucesso
        assert sum(results) >= 2
    
    def test_large_query(self, api_config):
        """Testa busca com query muito longa"""
        long_query = "Esta é uma pergunta muito longa " * 50  # ~1500 caracteres
        
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers=api_config.headers,
            json={"query": long_query[:1000], "include_history": False},  # Truncar para limite
            timeout=api_config.TIMEOUT_LONG
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_malformed_json(self, api_config):
        """Testa JSON malformado"""
        response = requests.post(
            f"{api_config.BASE_URL}/search",
            headers={"Authorization": f"Bearer {api_config.API_KEY}"},
            data="{'invalid': json}",  # JSON inválido
            timeout=api_config.TIMEOUT_SHORT
        )
        
        assert response.status_code in [400, 422]
    
    def test_timeout_handling(self, api_config):
        """Testa comportamento com timeout muito baixo"""
        try:
            response = requests.post(
                f"{api_config.BASE_URL}/search",
                headers=api_config.headers,
                json={"query": "Teste timeout", "include_history": False},
                timeout=0.001  # Timeout muito baixo
            )
        except requests.exceptions.Timeout:
            # Timeout esperado
            pass
        except requests.exceptions.RequestException:
            # Outras exceções de rede também são aceitáveis
            pass

if __name__ == "__main__":
    # Executar testes básicos se chamado diretamente
    import sys
    
    print("🧪 Executando testes básicos da API...")
    
    config = TestAPIConfig()
    
    # Teste de conectividade
    try:
        response = requests.get(f"{config.BASE_URL}/", timeout=10)
        if response.status_code == 200:
            print("✅ API acessível")
        else:
            print(f"❌ API retornou status {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Erro ao conectar com API: {e}")
        sys.exit(1)
    
    # Executar com pytest se disponível
    try:
        import pytest
        print("\n🚀 Executando testes completos com pytest...")
        pytest.main([__file__, "-v"])
    except ImportError:
        print("⚠️  pytest não disponível. Instale com: pip install pytest")
        print("✅ Testes básicos de conectividade passaram")