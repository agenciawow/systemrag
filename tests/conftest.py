"""
Configuração global para testes do Sistema RAG Multimodal

Define fixtures, marcadores e configurações compartilhadas entre todos os testes.
"""

import pytest
import os
import sys
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def pytest_configure(config):
    """Configuração do pytest"""
    
    # Registrar marcadores customizados
    config.addinivalue_line(
        "markers", "slow: marca testes que demoram mais de 30 segundos para executar"
    )
    config.addinivalue_line(
        "markers", "api: marca testes que requerem API externa funcionando"
    )
    config.addinivalue_line(
        "markers", "integration: marca testes de integração end-to-end"
    )
    config.addinivalue_line(
        "markers", "requires_all_apis: marca testes que precisam de todas as APIs configuradas"
    )

def pytest_collection_modifyitems(config, items):
    """Modifica itens de teste coletados"""
    
    # Adicionar marcador 'slow' automaticamente para testes de integração
    for item in items:
        if "integration" in item.nodeid or "test_integration" in item.nodeid:
            item.add_marker(pytest.mark.slow)
        
        # Adicionar marcador 'api' para testes que usam APIs externas
        if any(keyword in item.nodeid for keyword in ["api", "search", "evaluation", "ingestion"]):
            item.add_marker(pytest.mark.api)

@pytest.fixture(scope="session")
def test_config():
    """Configuração global de testes"""
    return {
        "base_url": os.getenv("TEST_API_URL", "http://localhost:8000"),
        "api_key": os.getenv("API_KEY", "sistemarag-api-key-secure-2024"),
        "timeout_short": 30,
        "timeout_long": 300,
        "has_openai": bool(os.getenv("OPENAI_API_KEY")),
        "has_voyage": bool(os.getenv("VOYAGE_API_KEY")),
        "has_astra": bool(os.getenv("ASTRA_DB_APPLICATION_TOKEN") and os.getenv("ASTRA_DB_API_ENDPOINT")),
        "has_r2": bool(os.getenv("R2_ENDPOINT") and os.getenv("R2_AUTH_TOKEN")),
        "has_llamaparse": bool(os.getenv("LLAMA_CLOUD_API_KEY"))
    }

@pytest.fixture(scope="session")
def api_requirements():
    """Verifica se APIs necessárias estão configuradas"""
    required_apis = {
        "openai": os.getenv("OPENAI_API_KEY"),
        "voyage": os.getenv("VOYAGE_API_KEY"),
        "astra_token": os.getenv("ASTRA_DB_APPLICATION_TOKEN"),
        "astra_endpoint": os.getenv("ASTRA_DB_API_ENDPOINT")
    }
    
    missing_apis = [name for name, value in required_apis.items() if not value]
    
    if missing_apis:
        pytest.skip(f"APIs não configuradas: {', '.join(missing_apis)}")
    
    return required_apis

@pytest.fixture
def skip_if_no_apis(test_config):
    """Pula teste se APIs críticas não estão configuradas"""
    if not (test_config["has_openai"] and test_config["has_voyage"] and test_config["has_astra"]):
        pytest.skip("APIs críticas não configuradas (OpenAI, Voyage, Astra DB)")

@pytest.fixture
def skip_if_no_api_server(test_config):
    """Pula teste se servidor da API não está rodando"""
    import requests
    
    try:
        response = requests.get(f"{test_config['base_url']}/health", timeout=10)
        if response.status_code != 200:
            pytest.skip(f"API não está respondendo corretamente em {test_config['base_url']}")
    except:
        pytest.skip(f"API não está acessível em {test_config['base_url']}")

# Configurações específicas por tipo de teste
@pytest.fixture
def ingestion_requirements(test_config):
    """Requisitos para testes de ingestão"""
    required = ["has_llamaparse", "has_voyage", "has_r2", "has_astra"]
    missing = [req for req in required if not test_config[req]]
    
    if missing:
        pytest.skip(f"Serviços necessários para ingestão não configurados: {missing}")

@pytest.fixture
def search_requirements(test_config):
    """Requisitos para testes de busca"""
    required = ["has_openai", "has_voyage", "has_astra"]
    missing = [req for req in required if not test_config[req]]
    
    if missing:
        pytest.skip(f"Serviços necessários para busca não configurados: {missing}")

@pytest.fixture
def evaluation_requirements(test_config):
    """Requisitos para testes de avaliação"""
    required = ["has_openai", "has_voyage", "has_astra"]
    missing = [req for req in required if not test_config[req]]
    
    if missing:
        pytest.skip(f"Serviços necessários para avaliação não configurados: {missing}")

# Fixtures de dados de teste
@pytest.fixture
def sample_queries():
    """Queries de exemplo para testes"""
    return [
        "Quais produtos estão disponíveis?",
        "Qual é o preço do hambúrguer?",
        "Vocês têm opções vegetarianas?",
        "Qual o horário de funcionamento?",
        "Como posso fazer um pedido?"
    ]

@pytest.fixture
def sample_documents():
    """URLs de documentos de exemplo para testes"""
    return {
        "pdf_test": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
        "google_drive": os.getenv("GOOGLE_DRIVE_URL", ""),
    }

@pytest.fixture
def evaluation_config():
    """Configuração para testes de avaliação"""
    return {
        "questions": [
            "Quais produtos estão disponíveis?",
            "Qual é o preço do hambúrguer?",
            "Vocês têm opções vegetarianas?"
        ],
        "keywords": [
            ["produtos", "disponível", "cardápio"],
            ["preço", "valor", "hambúrguer"],
            ["vegetariano", "vegano", "opção"]
        ],
        "categories": ["catalog", "pricing", "dietary"]
    }

# Configuração de logging para testes
@pytest.fixture(autouse=True)
def configure_test_logging():
    """Configura logging para testes"""
    import logging
    
    # Reduzir verbosidade de logs durante testes
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    
    # Manter logs importantes do sistema RAG
    logging.getLogger("system_rag").setLevel(logging.INFO)

def pytest_addoption(parser):
    """Adiciona opções de linha de comando customizadas"""
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="executar testes marcados como lentos"
    )
    parser.addoption(
        "--api-url",
        action="store",
        default="http://localhost:8000",
        help="URL base para testes da API"
    )
    parser.addoption(
        "--skip-external",
        action="store_true",
        default=False,
        help="pular testes que requerem APIs externas"
    )

def pytest_runtest_setup(item):
    """Setup executado antes de cada teste"""
    
    # Pular testes lentos se não especificado
    if "slow" in item.keywords and not item.config.getoption("--run-slow"):
        pytest.skip("teste lento pulado (use --run-slow para executar)")
    
    # Pular testes de API externa se especificado
    if "api" in item.keywords and item.config.getoption("--skip-external"):
        pytest.skip("teste de API externa pulado (--skip-external especificado)")

# Helpers para testes
class TestHelpers:
    """Classe com métodos auxiliares para testes"""
    
    @staticmethod
    def wait_for_api(base_url, timeout=30):
        """Aguarda API ficar disponível"""
        import requests
        import time
        
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    return True
            except:
                pass
            time.sleep(1)
        return False
    
    @staticmethod
    def create_test_document(content="Documento de teste", name="test_doc"):
        """Cria documento de teste temporário"""
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(content)
            return f.name
    
    @staticmethod
    def cleanup_test_files(*file_paths):
        """Remove arquivos de teste"""
        import os
        
        for path in file_paths:
            try:
                if os.path.exists(path):
                    os.unlink(path)
            except:
                pass

@pytest.fixture
def helpers():
    """Fixture com métodos auxiliares"""
    return TestHelpers()

# Configuração de environment para testes
@pytest.fixture(autouse=True)
def test_environment():
    """Configura ambiente de teste"""
    
    # Definir que estamos em modo de teste
    os.environ["TESTING"] = "true"
    
    # Configurar timeouts menores para testes
    os.environ["TEST_MODE"] = "true"
    
    yield
    
    # Cleanup
    if "TESTING" in os.environ:
        del os.environ["TESTING"]
    if "TEST_MODE" in os.environ:
        del os.environ["TEST_MODE"]