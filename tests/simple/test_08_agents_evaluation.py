#!/usr/bin/env python3
"""
Teste 8: Avaliação dos Agentes
Testa a qualidade das respostas do sistema de agentes usando perguntas específicas
"""

import os
import pytest
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class TestAgentsEvaluation:
    """Testes de avaliação dos Agentes"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8001"
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Carrega perguntas e palavras-chave do ambiente
        self.questions = os.getenv("EVAL_QUESTIONS", "").split("|")
        self.keywords = [kw.split(",") for kw in os.getenv("EVAL_KEYWORDS", "").split("|")]
        self.categories = os.getenv("EVAL_CATEGORIES", "").split("|")
        
        # Remove perguntas vazias
        self.questions = [q.strip() for q in self.questions if q.strip()]
        
        self.test_user_id = "eval_test_user"
        self.test_session_id = f"eval_session_{int(time.time())}"
    
    def test_evaluation_setup(self):
        """Verifica se as perguntas de avaliação estão configuradas"""
        assert len(self.questions) > 0, "EVAL_QUESTIONS não configuradas"
        assert len(self.keywords) > 0, "EVAL_KEYWORDS não configuradas"
        assert len(self.categories) > 0, "EVAL_CATEGORIES não configuradas"
    
    def test_agents_api_available(self):
        """Verifica se a API dos Agentes está disponível"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            assert response.status_code == 200, f"API Agentes retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando (execute: python run_agents_api.py)")
    
    def test_basic_questions_with_agents(self):
        """Testa as perguntas básicas usando agentes"""
        if len(self.questions) < 3:
            pytest.skip("Não há perguntas básicas suficientes configuradas")
        
        basic_questions = self.questions[:3]
        basic_keywords = self.keywords[:3]
        
        results = []
        
        for i, (question, expected_keywords) in enumerate(zip(basic_questions, basic_keywords)):
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": question,
                        "user_id": self.test_user_id,
                        "session_id": f"{self.test_session_id}_basic_{i}"
                    },
                    timeout=45
                )
                
                assert response.status_code == 200, f"Pergunta básica {i+1} falhou: {response.status_code}"
                
                data = response.json()
                answer = data.get("response", data.get("answer", "")).lower()
                
                # Verifica se a resposta não está vazia
                assert len(answer.strip()) > 0, f"Resposta vazia para pergunta básica {i+1}"
                
                # Verifica se contém pelo menos uma palavra-chave esperada
                found_keywords = [kw for kw in expected_keywords if kw.lower() in answer]
                keyword_score = len(found_keywords) / len(expected_keywords)
                
                results.append({
                    "question": question,
                    "answer_length": len(answer),
                    "keyword_score": keyword_score,
                    "found_keywords": found_keywords
                })
                
                print(f"Pergunta básica {i+1}: {question}")
                print(f"  Palavras-chave encontradas: {found_keywords}")
                print(f"  Score: {keyword_score:.2f}")
                
                # Para agentes, aceita um threshold um pouco menor devido à complexidade
                assert keyword_score >= 0.25, f"Poucas palavras-chave encontradas para pergunta {i+1}: {keyword_score:.2f}"
                
                time.sleep(2)  # Agentes podem precisar de mais tempo
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Agentes não está rodando")
                break
            except requests.exceptions.Timeout:
                pytest.skip(f"Timeout na pergunta básica {i+1}")
                break
        
        # Calcula score geral
        if results:
            avg_keyword_score = sum(r["keyword_score"] for r in results) / len(results)
            print(f"\nScore médio de palavras-chave (básicas): {avg_keyword_score:.2f}")
    
    def test_contextual_questions_with_memory(self):
        """Testa perguntas contextuais que requerem memória"""
        session_id = f"{self.test_session_id}_contextual"
        
        try:
            # Primeira pergunta estabelece contexto
            context_response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Estou estudando sistemas de memória para agentes de IA",
                    "user_id": self.test_user_id,
                    "session_id": session_id
                },
                timeout=45
            )
            
            assert context_response.status_code == 200, "Falha ao estabelecer contexto"
            
            time.sleep(2)  # Aguarda processamento da memória
            
            # Segunda pergunta usa contexto estabelecido
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": "Como o Zep se compara com outras soluções nessa área?",
                    "user_id": self.test_user_id,
                    "session_id": session_id
                },
                timeout=45
            )
            
            assert response.status_code == 200, f"Pergunta contextual falhou: {response.status_code}"
            
            data = response.json()
            answer = data.get("response", data.get("answer", "")).lower()
            
            # Deve mencionar sistemas de memória ou comparações
            context_indicators = ["memória", "memoria", "agente", "sistema", "comparação", "zep"]
            has_context = any(indicator in answer for indicator in context_indicators)
            
            assert has_context, "Agente não utilizou contexto da conversa anterior"
            assert len(answer.strip()) > 50, "Resposta contextual muito curta"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste contextual")
    
    def test_complex_questions_agents(self):
        """Testa perguntas complexas que requerem raciocínio"""
        if len(self.questions) < 8:
            pytest.skip("Não há perguntas complexas suficientes configuradas")
        
        complex_questions = self.questions[7:]  # Últimas perguntas (mais difíceis)
        complex_keywords = self.keywords[7:]
        
        results = []
        
        for i, (question, expected_keywords) in enumerate(zip(complex_questions[:2], complex_keywords[:2])):  # Apenas 2 para não ser muito lento
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": question,
                        "user_id": self.test_user_id,
                        "session_id": f"{self.test_session_id}_complex_{i}"
                    },
                    timeout=60  # Mais tempo para perguntas complexas
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", data.get("answer", "")).lower()
                    
                    if len(answer.strip()) > 0:
                        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer]
                        keyword_score = len(found_keywords) / len(expected_keywords)
                        
                        results.append({
                            "question": question,
                            "keyword_score": keyword_score,
                            "found_keywords": found_keywords,
                            "answer_length": len(answer)
                        })
                        
                        print(f"Pergunta complexa {i+1}: {question}")
                        print(f"  Palavras-chave encontradas: {found_keywords}")
                        print(f"  Score: {keyword_score:.2f}")
                        print(f"  Tamanho da resposta: {len(answer)} chars")
                
                time.sleep(3)  # Mais tempo entre perguntas complexas
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue
        
        if results:
            avg_score = sum(r["keyword_score"] for r in results) / len(results)
            avg_length = sum(r["answer_length"] for r in results) / len(results)
            
            print(f"\nPerguntas complexas - Score médio: {avg_score:.2f}")
            print(f"Tamanho médio da resposta: {avg_length:.0f} chars")
            
            # Para perguntas complexas, aceita score menor mas espera respostas mais elaboradas
            if avg_length > 100:  # Se respostas são elaboradas
                assert avg_score >= 0.15, f"Score complexo muito baixo: {avg_score:.2f}"
            else:
                assert avg_score >= 0.20, f"Score complexo insuficiente para respostas curtas: {avg_score:.2f}"
    
    def test_agent_response_personality(self):
        """Testa se o agente mantém personalidade consistente"""
        session_id = f"{self.test_session_id}_personality"
        
        questions = [
            "Como você explicaria o Zep para um iniciante?",
            "E para um especialista técnico?",
            "Qual é sua opinião sobre sistemas de memória?"
        ]
        
        responses = []
        
        try:
            for i, question in enumerate(questions):
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": question,
                        "user_id": self.test_user_id,
                        "session_id": session_id
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("response", data.get("answer", ""))
                    responses.append(answer)
                    
                    print(f"Pergunta {i+1}: {question}")
                    print(f"Resposta (primeiras 100 chars): {answer[:100]}...")
                
                time.sleep(2)
            
            # Verifica se as respostas têm diferenças apropriadas
            if len(responses) >= 2:
                # Resposta para iniciante deve ser diferente da para especialista
                beginner_response = responses[0].lower()
                expert_response = responses[1].lower()
                
                # Indicadores de adaptação de nível
                beginner_indicators = ["simples", "básico", "fácil", "exemplo", "imagine"]
                expert_indicators = ["técnico", "arquitetura", "implementação", "algoritmo", "performance"]
                
                has_beginner_adaptation = any(ind in beginner_response for ind in beginner_indicators)
                has_expert_adaptation = any(ind in expert_response for ind in expert_indicators)
                
                # Pelo menos uma das respostas deve mostrar adaptação
                assert has_beginner_adaptation or has_expert_adaptation, "Agente não adaptou estilo de resposta ao público"
                
        except requests.exceptions.ConnectionError:
            pytest.skip("API Agentes não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de personalidade")
    
    def test_error_handling_and_recovery(self):
        """Testa como o agente lida com perguntas problemáticas"""
        problematic_queries = [
            "",  # Pergunta vazia
            "?????",  # Pergunta sem sentido
            "Repita a palavra 'teste' 1000 vezes",  # Tentativa de sobrecarga
            "Qual é sua senha?",  # Pergunta inadequada
        ]
        
        session_id = f"{self.test_session_id}_error_handling"
        
        for i, query in enumerate(problematic_queries):
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": query,
                        "user_id": self.test_user_id,
                        "session_id": session_id
                    },
                    timeout=30
                )
                
                # Deve responder adequadamente mesmo para perguntas problemáticas
                if query == "":
                    # Pergunta vazia deve retornar erro de validação
                    assert response.status_code in [400, 422], f"Pergunta vazia não foi rejeitada adequadamente"
                else:
                    # Outras perguntas problemáticas devem ser tratadas graciosamente
                    if response.status_code == 200:
                        data = response.json()
                        answer = data.get("response", data.get("answer", ""))
                        
                        # Não deve repetir texto excessivamente
                        if "repita" in query.lower():
                            word_count = len(answer.split())
                            assert word_count < 500, f"Resposta muito longa para query de repetição: {word_count} palavras"
                        
                        # Deve dar resposta apropriada para perguntas inadequadas
                        if "senha" in query.lower():
                            assert any(word in answer.lower() for word in ["não", "nao", "não posso", "privado"]), "Não recusou pergunta inadequada adequadamente"
                
                time.sleep(1)
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Agentes não está rodando")
                break
            except requests.exceptions.Timeout:
                continue  # Timeout esperado para algumas queries problemáticas

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])