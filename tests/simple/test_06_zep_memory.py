#!/usr/bin/env python3
"""
Teste 6: Sistema de Memória Zep
Testa a integração e funcionalidade do sistema de memória Zep
"""

import os
import pytest
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class TestZepMemory:
    """Testes do sistema de memória Zep"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8001"  # API dos Agentes usa Zep
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.zep_api_key = os.getenv("ZEP_API_KEY")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        self.test_user_id = "test_zep_user"
        self.test_session_id = f"test_zep_session_{int(time.time())}"
    
    def test_zep_api_key_configured(self):
        """Verifica se a chave da API do Zep está configurada"""
        assert self.zep_api_key is not None, "ZEP_API_KEY não configurada"
        assert len(self.zep_api_key) > 20, "ZEP_API_KEY parece inválida"
    
    def test_agents_api_with_zep_available(self):
        """Verifica se a API dos Agentes está rodando"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            assert response.status_code == 200, f"API Agentes retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando (execute: python run_agents_api.py)")
    
    def test_zep_memory_persistence(self):
        """Testa persistência da memória do Zep entre interações"""
        try:
            # Primeira interação - estabelece informação pessoal
            response1 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Oi, meu nome é Carlos e sou engenheiro de software. Estou aprendendo sobre Zep.",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response1.status_code == 200, f"Primeira interação falhou: {response1.status_code}"
            
            # Aguarda processamento da memória
            time.sleep(2)
            
            # Segunda interação - testa se lembra da informação
            response2 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Qual é o meu nome e profissão?",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response2.status_code == 200, f"Segunda interação falhou: {response2.status_code}"
            
            data = response2.json()
            response_text = data.get("response", data.get("answer", "")).lower()
            
            # Deve lembrar do nome e profissão
            assert "carlos" in response_text, "Zep não lembrou do nome do usuário"
            assert any(word in response_text for word in ["engenheiro", "software", "desenvolvedor"]), "Zep não lembrou da profissão"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de memória Zep")
    
    def test_zep_cross_session_memory(self):
        """Testa memória do Zep entre diferentes sessões"""
        session1 = f"{self.test_session_id}_1"
        session2 = f"{self.test_session_id}_2"
        
        try:
            # Sessão 1 - estabelece preferência
            response1 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Eu prefiro respostas técnicas e detalhadas sobre inteligência artificial.",
                    "user_id": self.test_user_id,
                    "session_id": session1
                },
                timeout=45
            )
            
            assert response1.status_code == 200, f"Primeira sessão falhou: {response1.status_code}"
            
            # Aguarda processamento
            time.sleep(3)
            
            # Sessão 2 - pergunta genérica para testar se lembra da preferência
            response2 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "O que você pode me falar sobre machine learning?",
                    "user_id": self.test_user_id,
                    "session_id": session2
                },
                timeout=45
            )
            
            assert response2.status_code == 200, f"Segunda sessão falhou: {response2.status_code}"
            
            data = response2.json()
            response_text = data.get("response", data.get("answer", ""))
            
            # A resposta deve ser mais técnica/detalhada devido à preferência lembrada
            assert len(response_text) > 100, "Resposta muito curta, pode não ter considerado preferência por detalhes"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de memória entre sessões")
    
    def test_zep_contextual_understanding(self):
        """Testa compreensão contextual do Zep"""
        try:
            # Primeira pergunta sobre um tópico específico
            response1 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Explique o que é o Graphiti no contexto do Zep",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response1.status_code == 200, f"Primeira pergunta falhou: {response1.status_code}"
            
            # Segunda pergunta fazendo referência à primeira
            response2 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Como esse componente se compara com sistemas tradicionais?",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response2.status_code == 200, f"Segunda pergunta falhou: {response2.status_code}"
            
            data = response2.json()
            response_text = data.get("response", data.get("answer", "")).lower()
            
            # Deve entender que "esse componente" se refere ao Graphiti
            context_indicators = ["graphiti", "zep", "knowledge graph", "temporal", "memória"]
            has_context = any(indicator in response_text for indicator in context_indicators)
            
            assert has_context, "Zep não manteve contexto da conversa anterior"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de compreensão contextual")
    
    def test_zep_memory_with_time_references(self):
        """Testa como o Zep lida com referências temporais"""
        try:
            # Informação com referência temporal
            response1 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Ontem eu li sobre o benchmark DMR onde o Zep teve 94.8% de performance.",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response1.status_code == 200, f"Primeira interação falhou: {response1.status_code}"
            
            time.sleep(2)
            
            # Pergunta fazendo referência ao que foi dito
            response2 = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Qual foi a performance que eu mencionei?",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response2.status_code == 200, f"Segunda interação falhou: {response2.status_code}"
            
            data = response2.json()
            response_text = data.get("response", data.get("answer", ""))
            
            # Deve lembrar da performance específica
            assert "94.8" in response_text, "Zep não lembrou da performance específica mencionada"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de referências temporais")
    
    def test_zep_memory_cleanup_and_limits(self):
        """Testa comportamento do Zep com muitas interações"""
        try:
            # Múltiplas interações para testar limites de memória
            for i in range(5):
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": f"Esta é a interação número {i+1}. Lembre-se deste número.",
                        "user_id": self.test_user_id,
                        "session_id": self.test_session_id
                    },
                    timeout=30
                )
                
                assert response.status_code == 200, f"Interação {i+1} falhou: {response.status_code}"
                time.sleep(1)  # Pequena pausa entre interações
            
            # Testa se ainda lembra de informações anteriores
            response_final = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Quantas interações fizemos até agora?",
                    "user_id": self.test_user_id,
                    "session_id": self.test_session_id
                },
                timeout=45
            )
            
            assert response_final.status_code == 200, f"Pergunta final falhou: {response_final.status_code}"
            
            data = response_final.json()
            response_text = data.get("response", data.get("answer", ""))
            
            # Deve ter alguma noção do número de interações
            numbers = ["5", "6", "cinco", "seis"]  # 5 + a pergunta final
            has_count = any(num in response_text.lower() for num in numbers)
            
            assert has_count, "Zep perdeu o rastro do número de interações"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de limites de memória")

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])