#!/usr/bin/env python3
"""
Teste 5: Stress Test FastAPI
Testa requisições assíncronas e simultâneas para estressar a API
"""

import os
import pytest
import asyncio
import aiohttp
import time
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv

load_dotenv()

class TestFastAPIStress:
    """Testes de stress para FastAPI"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.system_api_url = "http://localhost:8000"
        self.agents_api_url = "http://localhost:8001"
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def test_api_availability(self):
        """Verifica se as APIs estão disponíveis antes dos testes de stress"""
        import requests
        
        try:
            # Testa Sistema RAG
            response = requests.get(f"{self.system_api_url}/health", timeout=5)
            system_api_ok = response.status_code == 200
        except:
            system_api_ok = False
            
        try:
            # Testa Agentes
            response = requests.get(f"{self.agents_api_url}/health", timeout=5)
            agents_api_ok = response.status_code == 200
        except:
            agents_api_ok = False
        
        if not system_api_ok and not agents_api_ok:
            pytest.skip("Nenhuma API está rodando para testes de stress")
        
        if not system_api_ok:
            pytest.skip("API Sistema RAG não está rodando")
        
        if not agents_api_ok:
            pytest.skip("API Agentes não está rodando")
    
    @pytest.mark.asyncio
    async def test_concurrent_health_checks(self):
        """Testa múltiplas verificações de saúde simultâneas"""
        async def check_health(session, url):
            try:
                async with session.get(f"{url}/health", timeout=10) as response:
                    return response.status == 200
            except:
                return False
        
        async with aiohttp.ClientSession() as session:
            tasks = []
            
            # 20 requisições simultâneas para cada API
            for _ in range(20):
                tasks.append(check_health(session, self.system_api_url))
                tasks.append(check_health(session, self.agents_api_url))
            
            start_time = time.time()
            results = await asyncio.gather(*tasks, return_exceptions=True)
            end_time = time.time()
            
            # Verifica se a maioria das requisições foi bem-sucedida
            successful = sum(1 for r in results if r is True)
            total = len(results)
            success_rate = successful / total
            
            print(f"Health checks: {successful}/{total} successful ({success_rate:.1%})")
            print(f"Time taken: {end_time - start_time:.2f}s")
            
            # Pelo menos 80% das requisições devem ser bem-sucedidas
            assert success_rate >= 0.8, f"Taxa de sucesso muito baixa: {success_rate:.1%}"
    
    def test_sequential_requests_performance(self):
        """Testa performance de requisições sequenciais"""
        import requests
        
        try:
            requests.get(f"{self.system_api_url}/health", timeout=5)
        except:
            pytest.skip("API Sistema RAG não está rodando")
        
        num_requests = 10
        start_time = time.time()
        
        successful = 0
        for i in range(num_requests):
            try:
                response = requests.get(f"{self.system_api_url}/health", timeout=10)
                if response.status_code == 200:
                    successful += 1
            except:
                pass
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time = total_time / num_requests
        
        print(f"Sequential requests: {successful}/{num_requests} successful")
        print(f"Total time: {total_time:.2f}s, Average: {avg_time:.3f}s per request")
        
        # Pelo menos 90% deve ser bem-sucedido
        assert successful / num_requests >= 0.9, "Muitas falhas em requisições sequenciais"
        
        # Tempo médio deve ser razoável (menos de 1 segundo por health check)
        assert avg_time < 1.0, f"Tempo médio muito alto: {avg_time:.3f}s"
    
    def test_concurrent_simple_searches(self):
        """Testa buscas simultâneas simples"""
        import requests
        
        try:
            requests.get(f"{self.system_api_url}/health", timeout=5)
        except:
            pytest.skip("API Sistema RAG não está rodando")
        
        def make_search_request(query_id):
            try:
                response = requests.post(
                    f"{self.system_api_url}/search",
                    headers=self.headers,
                    json={"query": f"O que é Zep? (requisição {query_id})"},
                    timeout=30
                )
                return response.status_code == 200
            except:
                return False
        
        # Usa ThreadPoolExecutor para requisições simultâneas
        num_concurrent = 5
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=num_concurrent) as executor:
            futures = [executor.submit(make_search_request, i) for i in range(num_concurrent)]
            results = [future.result() for future in futures]
        
        end_time = time.time()
        total_time = end_time - start_time
        successful = sum(results)
        
        print(f"Concurrent searches: {successful}/{num_concurrent} successful")
        print(f"Total time: {total_time:.2f}s")
        
        # Pelo menos 60% deve ser bem-sucedido (buscas são mais pesadas)
        assert successful / num_concurrent >= 0.6, "Muitas falhas em buscas simultâneas"
        
        # Deve processar em menos de 60 segundos
        assert total_time < 60, f"Tempo total muito alto: {total_time:.2f}s"
    
    def test_memory_usage_stability(self):
        """Testa estabilidade de uso de memória com múltiplas requisições"""
        import requests
        import psutil
        import os
        
        try:
            requests.get(f"{self.system_api_url}/health", timeout=5)
        except:
            pytest.skip("API Sistema RAG não está rodando")
        
        # Medição inicial de memória
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Faz várias requisições
        for i in range(20):
            try:
                requests.get(f"{self.system_api_url}/health", timeout=5)
            except:
                pass
        
        # Medição final de memória
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        print(f"Memory usage: {initial_memory:.1f}MB -> {final_memory:.1f}MB (+{memory_increase:.1f}MB)")
        
        # Aumento de memória deve ser razoável (menos de 100MB)
        assert memory_increase < 100, f"Aumento de memória muito alto: {memory_increase:.1f}MB"
    
    def test_error_handling_under_load(self):
        """Testa tratamento de erros sob carga"""
        import requests
        
        try:
            requests.get(f"{self.system_api_url}/health", timeout=5)
        except:
            pytest.skip("API Sistema RAG não está rodando")
        
        def make_invalid_request():
            try:
                # Requisição inválida propositalmente
                response = requests.post(
                    f"{self.system_api_url}/search",
                    headers=self.headers,
                    json={"invalid": "data"},
                    timeout=10
                )
                # Deve retornar erro de validação, não erro de servidor
                return 400 <= response.status_code < 500
            except:
                return False
        
        # Múltiplas requisições inválidas simultâneas
        num_requests = 10
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_invalid_request) for _ in range(num_requests)]
            results = [future.result() for future in futures]
        
        successful_error_handling = sum(results)
        
        print(f"Error handling: {successful_error_handling}/{num_requests} handled correctly")
        
        # Pelo menos 80% deve retornar erros apropriados (não crashes)
        assert successful_error_handling / num_requests >= 0.8, "API não está tratando erros adequadamente sob carga"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])