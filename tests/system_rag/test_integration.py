#!/usr/bin/env python3
"""
Testes de integração end-to-end para o Sistema RAG Multimodal

Testa cenários completos:
- Pipeline completo (ingestão → busca)
- API + sistema de busca
- Avaliação automática
- Casos de uso reais
"""

import pytest
import os
import time
import requests
import asyncio
import tempfile
import shutil
from typing import Dict, List, Any
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class TestIntegrationConfig:
    """Configuração para testes de integração"""
    
    # APIs e serviços
    API_BASE_URL = os.getenv("TEST_API_URL", "http://localhost:8000")
    API_KEY = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
    
    # URLs de teste
    TEST_PDF_URL = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    
    # Configuração de tempo
    INGESTION_TIMEOUT = 300  # 5 minutos
    SEARCH_TIMEOUT = 60     # 1 minuto
    EVALUATION_TIMEOUT = 300 # 5 minutos
    
    # Queries de teste para diferentes cenários
    TEST_SCENARIOS = {
        "basic_search": [
            "Quais produtos estão disponíveis?",
            "Qual é o preço do hambúrguer?",
            "Vocês têm opções vegetarianas?"
        ],
        "conversational": [
            "Quais produtos vocês têm?",
            "E os preços?",
            "Tem desconto?"
        ],
        "complex_queries": [
            "Quero um hambúrguer vegetariano com batata frita, quanto fica?",
            "Qual a diferença entre o hambúrguer clássico e o especial?",
            "Vocês fazem entrega e qual o tempo de espera?"
        ]
    }
    
    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.API_KEY}",
            "Content-Type": "application/json"
        }
    
    @property
    def has_api_running(self) -> bool:
        try:
            response = requests.get(f"{self.API_BASE_URL}/health", timeout=10)
            return response.status_code == 200
        except:
            return False

@pytest.fixture(scope="session")
def integration_config():
    """Fixture com configuração de integração"""
    return TestIntegrationConfig()

@pytest.fixture(scope="session", autouse=True)
def check_prerequisites(integration_config):
    """Verifica pré-requisitos para testes de integração"""
    
    # Verificar se API está rodando
    if not integration_config.has_api_running:
        pytest.fail(f"API não está rodando em {integration_config.API_BASE_URL}. Inicie com: python run_system_api.py")
    
    # Verificar variáveis críticas
    required_vars = ['OPENAI_API_KEY', 'VOYAGE_API_KEY', 'ASTRA_DB_APPLICATION_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        pytest.fail(f"Variáveis de ambiente ausentes: {', '.join(missing_vars)}")

class TestEndToEndPipeline:
    """Testes end-to-end do pipeline completo"""
    
    @pytest.mark.slow
    def test_ingest_and_search_workflow(self, integration_config):
        """Testa workflow completo: ingestão → busca → verificação"""
        
        # 1. Ingestão de documento
        print("📥 Iniciando ingestão...")
        ingest_response = requests.post(
            f"{integration_config.API_BASE_URL}/ingest",
            headers=integration_config.headers,
            json={
                "document_url": integration_config.TEST_PDF_URL,
                "document_name": "Documento E2E Test",
                "overwrite": True
            },
            timeout=integration_config.INGESTION_TIMEOUT
        )
        
        assert ingest_response.status_code == 200
        ingest_data = ingest_response.json()
        assert ingest_data["success"] is True
        assert ingest_data["chunks_created"] >= 0
        
        print(f"✅ Ingestão concluída: {ingest_data['chunks_created']} chunks criados")
        
        # 2. Aguardar um pouco para sincronização
        time.sleep(5)
        
        # 3. Busca para verificar se documento foi indexado
        print("🔍 Testando busca após ingestão...")
        search_response = requests.post(
            f"{integration_config.API_BASE_URL}/search",
            headers=integration_config.headers,
            json={"query": "conteúdo do documento", "include_history": False},
            timeout=integration_config.SEARCH_TIMEOUT
        )
        
        assert search_response.status_code == 200
        search_data = search_response.json()
        assert search_data["success"] is True
        assert len(search_data["answer"]) > 0
        
        print(f"✅ Busca funcionou: resposta de {len(search_data['answer'])} caracteres")
    
    @pytest.mark.slow
    def test_multiple_queries_performance(self, integration_config):
        """Testa performance com múltiplas queries sequenciais"""
        
        results = []
        total_time = 0
        
        for scenario_name, queries in integration_config.TEST_SCENARIOS.items():
            print(f"🎯 Testando cenário: {scenario_name}")
            
            for i, query in enumerate(queries):
                start_time = time.time()
                
                try:
                    response = requests.post(
                        f"{integration_config.API_BASE_URL}/search",
                        headers=integration_config.headers,
                        json={"query": query, "include_history": False},
                        timeout=integration_config.SEARCH_TIMEOUT
                    )
                    
                    query_time = time.time() - start_time
                    total_time += query_time
                    
                    if response.status_code == 200:
                        data = response.json()
                        if data["success"]:
                            results.append({
                                "scenario": scenario_name,
                                "query": query,
                                "time": query_time,
                                "answer_length": len(data["answer"]),
                                "success": True
                            })
                        else:
                            results.append({
                                "scenario": scenario_name,
                                "query": query,
                                "time": query_time,
                                "success": False,
                                "error": "API returned success=false"
                            })
                    else:
                        results.append({
                            "scenario": scenario_name,
                            "query": query,
                            "time": query_time,
                            "success": False,
                            "error": f"HTTP {response.status_code}"
                        })
                
                except Exception as e:
                    query_time = time.time() - start_time
                    total_time += query_time
                    results.append({
                        "scenario": scenario_name,
                        "query": query,
                        "time": query_time,
                        "success": False,
                        "error": str(e)
                    })
                
                # Pausa entre queries para evitar sobrecarga
                time.sleep(2)
        
        # Análise dos resultados
        successful_queries = [r for r in results if r["success"]]
        success_rate = len(successful_queries) / len(results)
        avg_response_time = sum(r["time"] for r in successful_queries) / len(successful_queries) if successful_queries else 0
        
        print(f"📊 Resultados: {len(successful_queries)}/{len(results)} queries com sucesso")
        print(f"⏱️ Tempo médio: {avg_response_time:.2f}s")
        print(f"📈 Taxa de sucesso: {success_rate:.1%}")
        
        # Assertions
        assert success_rate >= 0.7, f"Taxa de sucesso muito baixa: {success_rate:.1%}"
        assert avg_response_time < 30, f"Tempo médio muito alto: {avg_response_time:.2f}s"

class TestConversationalFlow:
    """Testes de fluxo conversacional"""
    
    def test_conversational_context(self, integration_config):
        """Testa manutenção de contexto em conversação"""
        
        # Sequência de perguntas que dependem de contexto
        conversation = [
            "Quais produtos vocês têm?",
            "E os preços deles?",
            "Tem desconto para estudantes?",
            "Qual o horário de funcionamento?"
        ]
        
        responses = []
        
        for i, query in enumerate(conversation):
            print(f"💬 Pergunta {i+1}: {query}")
            
            response = requests.post(
                f"{integration_config.API_BASE_URL}/search",
                headers=integration_config.headers,
                json={"query": query, "include_history": True},
                timeout=integration_config.SEARCH_TIMEOUT
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            
            responses.append({
                "query": query,
                "answer": data["answer"],
                "time": data["response_time"]
            })
            
            print(f"✅ Resposta: {data['answer'][:100]}...")
        
        # Verificar que as respostas fazem sentido no contexto
        assert len(responses) == len(conversation)
        
        # Segunda pergunta deve referenciar produtos da primeira
        second_answer = responses[1]["answer"].lower()
        assert any(word in second_answer for word in ["preço", "valor", "custa", "r$"])
        
        print("✅ Contexto conversacional mantido")

class TestErrorRecovery:
    """Testes de recuperação de erros"""
    
    def test_api_error_handling(self, integration_config):
        """Testa tratamento de erros da API"""
        
        # Query muito longa
        long_query = "Esta é uma pergunta muito longa " * 100  # ~3000 chars
        
        response = requests.post(
            f"{integration_config.API_BASE_URL}/search",
            headers=integration_config.headers,
            json={"query": long_query[:1000], "include_history": False},  # Truncar
            timeout=integration_config.SEARCH_TIMEOUT
        )
        
        # Deve funcionar mesmo com query longa (truncada)
        assert response.status_code == 200
        
        # Query vazia
        response = requests.post(
            f"{integration_config.API_BASE_URL}/search",
            headers=integration_config.headers,
            json={"query": "", "include_history": False},
            timeout=integration_config.SEARCH_TIMEOUT
        )
        
        # Deve retornar erro de validação
        assert response.status_code == 422
    
    def test_invalid_ingestion_recovery(self, integration_config):
        """Testa recuperação de erro na ingestão"""
        
        # URL inválida
        response = requests.post(
            f"{integration_config.API_BASE_URL}/ingest",
            headers=integration_config.headers,
            json={
                "document_url": "https://invalid-url-that-does-not-exist.com/file.pdf",
                "document_name": "Teste Inválido",
                "overwrite": True
            },
            timeout=30  # Timeout menor para URL inválida
        )
        
        # Deve retornar erro
        assert response.status_code == 500
        data = response.json()
        assert "detail" in data
        assert data["detail"]["success"] is False
        
        # Após erro, sistema deve continuar funcionando
        search_response = requests.post(
            f"{integration_config.API_BASE_URL}/search",
            headers=integration_config.headers,
            json={"query": "teste após erro", "include_history": False},
            timeout=integration_config.SEARCH_TIMEOUT
        )
        
        assert search_response.status_code == 200

class TestSystemStress:
    """Testes de stress do sistema"""
    
    @pytest.mark.slow
    def test_concurrent_requests(self, integration_config):
        """Testa requisições concorrentes"""
        import concurrent.futures
        import threading
        
        def make_search_request(query_num):
            try:
                response = requests.post(
                    f"{integration_config.API_BASE_URL}/search",
                    headers=integration_config.headers,
                    json={"query": f"Teste concorrência {query_num}", "include_history": False},
                    timeout=integration_config.SEARCH_TIMEOUT
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return data["success"]
                return False
            except:
                return False
        
        # Executar 5 requisições simultâneas
        print("🚀 Executando 5 requisições simultâneas...")
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_search_request, i) for i in range(5)]
            results = [future.result() for future in futures]
        
        successful_requests = sum(results)
        success_rate = successful_requests / len(results)
        
        print(f"✅ {successful_requests}/5 requisições com sucesso ({success_rate:.1%})")
        
        # Pelo menos 60% deve ter sucesso
        assert success_rate >= 0.6, f"Taxa de sucesso baixa em concorrência: {success_rate:.1%}"
    
    @pytest.mark.slow
    def test_evaluation_stress(self, integration_config):
        """Testa stress do sistema de avaliação"""
        
        print("📊 Iniciando avaliação completa...")
        start_time = time.time()
        
        response = requests.post(
            f"{integration_config.API_BASE_URL}/evaluate",
            headers=integration_config.headers,
            timeout=integration_config.EVALUATION_TIMEOUT
        )
        
        evaluation_time = time.time() - start_time
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        print(f"✅ Avaliação concluída em {evaluation_time:.1f}s")
        print(f"📈 Taxa de sucesso: {data['success_rate']:.1%}")
        print(f"📝 Total de perguntas: {data['total_questions']}")
        
        # Verificações
        assert data["success_rate"] >= 0.5  # Pelo menos 50% de sucesso
        assert evaluation_time < integration_config.EVALUATION_TIMEOUT
        assert data["total_questions"] > 0

class TestRealWorldScenarios:
    """Testes de cenários do mundo real"""
    
    def test_restaurant_use_case(self, integration_config):
        """Testa caso de uso de restaurante"""
        
        restaurant_queries = [
            "Qual o prato mais popular?",
            "Vocês têm opções sem glúten?",
            "Qual o tempo de entrega?",
            "Aceita cartão de crédito?",
            "Qual o horário de funcionamento?",
            "Tem promoção hoje?"
        ]
        
        successful_queries = 0
        relevant_responses = 0
        
        for query in restaurant_queries:
            print(f"🍽️ Pergunta: {query}")
            
            response = requests.post(
                f"{integration_config.API_BASE_URL}/search",
                headers=integration_config.headers,
                json={"query": query, "include_history": False},
                timeout=integration_config.SEARCH_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    successful_queries += 1
                    answer = data["answer"].lower()
                    
                    # Verificar se resposta parece relevante
                    if (len(answer) > 20 and 
                        "não consegui encontrar" not in answer and
                        "desculpe" not in answer):
                        relevant_responses += 1
                        print(f"✅ Resposta relevante: {data['answer'][:100]}...")
                    else:
                        print(f"⚠️ Resposta genérica: {data['answer'][:100]}...")
            
            time.sleep(1)  # Pausa entre queries
        
        success_rate = successful_queries / len(restaurant_queries)
        relevance_rate = relevant_responses / len(restaurant_queries)
        
        print(f"📊 Resultados do caso de uso:")
        print(f"   Taxa de sucesso: {success_rate:.1%}")
        print(f"   Taxa de relevância: {relevance_rate:.1%}")
        
        assert success_rate >= 0.7, f"Taxa de sucesso baixa: {success_rate:.1%}"
        assert relevance_rate >= 0.4, f"Taxa de relevância baixa: {relevance_rate:.1%}"
    
    def test_customer_support_simulation(self, integration_config):
        """Simula atendimento ao cliente"""
        
        # Simulação de conversa de atendimento
        customer_conversation = [
            "Olá, gostaria de fazer um pedido",
            "Quais hambúrgueres vocês têm?",
            "Qual a diferença entre o clássico e o especial?",
            "Quero um especial com batata, quanto fica?",
            "Vocês entregam na região central?",
            "Qual o tempo de entrega?",
            "Ok, como faço o pedido?"
        ]
        
        conversation_results = []
        
        for i, message in enumerate(customer_conversation):
            print(f"👤 Cliente: {message}")
            
            response = requests.post(
                f"{integration_config.API_BASE_URL}/search",
                headers=integration_config.headers,
                json={"query": message, "include_history": True},
                timeout=integration_config.SEARCH_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                if data["success"]:
                    print(f"🤖 Sistema: {data['answer'][:150]}...")
                    conversation_results.append({
                        "turn": i + 1,
                        "query": message,
                        "response_time": data["response_time"],
                        "answer_length": len(data["answer"]),
                        "success": True
                    })
                else:
                    conversation_results.append({
                        "turn": i + 1,
                        "success": False,
                        "error": "API success=false"
                    })
            else:
                conversation_results.append({
                    "turn": i + 1,
                    "success": False,
                    "error": f"HTTP {response.status_code}"
                })
            
            time.sleep(2)  # Simular tempo de leitura
        
        # Análise da conversa
        successful_turns = [r for r in conversation_results if r.get("success")]
        conversation_success_rate = len(successful_turns) / len(conversation_results)
        avg_response_time = sum(r["response_time"] for r in successful_turns) / len(successful_turns) if successful_turns else 0
        
        print(f"📞 Simulação de atendimento:")
        print(f"   Turnos com sucesso: {len(successful_turns)}/{len(conversation_results)}")
        print(f"   Taxa de sucesso: {conversation_success_rate:.1%}")
        print(f"   Tempo médio de resposta: {avg_response_time:.2f}s")
        
        assert conversation_success_rate >= 0.8, f"Muitas falhas na conversa: {conversation_success_rate:.1%}"
        assert avg_response_time < 20, f"Respostas muito lentas para atendimento: {avg_response_time:.2f}s"

if __name__ == "__main__":
    # Executar testes básicos se chamado diretamente
    import sys
    
    print("🧪 Executando testes de integração...")
    
    config = TestIntegrationConfig()
    
    # Verificar pré-requisitos
    if not config.has_api_running:
        print(f"❌ API não está rodando em {config.API_BASE_URL}")
        print("   Inicie com: python run_system_api.py")
        sys.exit(1)
    
    print("✅ API está rodando")
    
    # Verificar variáveis de ambiente
    required_vars = ['OPENAI_API_KEY', 'VOYAGE_API_KEY', 'ASTRA_DB_APPLICATION_TOKEN']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Variáveis ausentes: {', '.join(missing_vars)}")
        print("   Alguns testes podem falhar")
    else:
        print("✅ Variáveis de ambiente configuradas")
    
    # Executar com pytest se disponível
    try:
        import pytest
        print("\n🚀 Executando testes de integração com pytest...")
        # -v para verbose, -s para não capturar print, --tb=short para tracebacks curtos
        pytest.main([__file__, "-v", "-s", "--tb=short"])
    except ImportError:
        print("⚠️  pytest não disponível. Instale com: pip install pytest")
        print("✅ Verificações básicas passaram")