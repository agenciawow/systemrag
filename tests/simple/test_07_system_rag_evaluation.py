#!/usr/bin/env python3
"""
Teste 7: Avaliação do System RAG
Testa a qualidade das respostas do sistema RAG usando perguntas específicas
"""

import os
import pytest
import requests
import time
from dotenv import load_dotenv

load_dotenv()

class TestSystemRAGEvaluation:
    """Testes de avaliação do Sistema RAG"""
    
    def setup_method(self):
        """Configuração para cada teste"""
        self.api_url = "http://localhost:8000"
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
        
    def test_evaluation_setup(self):
        """Verifica se as perguntas de avaliação estão configuradas"""
        assert len(self.questions) > 0, "EVAL_QUESTIONS não configuradas"
        assert len(self.keywords) > 0, "EVAL_KEYWORDS não configuradas"
        assert len(self.categories) > 0, "EVAL_CATEGORIES não configuradas"
        
        # Verifica se o número de perguntas, palavras-chave e categorias é consistente
        assert len(self.questions) == len(self.keywords), "Número de perguntas e palavras-chave inconsistente"
        assert len(self.questions) == len(self.categories), "Número de perguntas e categorias inconsistente"
    
    def test_system_rag_api_available(self):
        """Verifica se a API do Sistema RAG está disponível"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            assert response.status_code == 200, f"API Sistema RAG retornou {response.status_code}"
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando (execute: python run_system_api.py)")
    
    def test_basic_questions_accuracy(self):
        """Testa as perguntas básicas (primeiras 3)"""
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
                        "include_history": False
                    },
                    timeout=30
                )
                
                assert response.status_code == 200, f"Pergunta {i+1} falhou: {response.status_code}"
                
                data = response.json()
                answer = data.get("answer", data.get("response", "")).lower()
                
                # Verifica se a resposta não está vazia
                assert len(answer.strip()) > 0, f"Resposta vazia para pergunta {i+1}"
                
                # Verifica se contém pelo menos uma palavra-chave esperada
                found_keywords = [kw for kw in expected_keywords if kw.lower() in answer]
                keyword_score = len(found_keywords) / len(expected_keywords)
                
                results.append({
                    "question": question,
                    "answer_length": len(answer),
                    "keyword_score": keyword_score,
                    "found_keywords": found_keywords
                })
                
                print(f"Pergunta {i+1}: {question}")
                print(f"  Palavras-chave encontradas: {found_keywords}")
                print(f"  Score: {keyword_score:.2f}")
                
                # Pelo menos 30% das palavras-chave devem estar presentes
                assert keyword_score >= 0.3, f"Poucas palavras-chave encontradas para pergunta {i+1}: {keyword_score:.2f}"
                
                time.sleep(1)  # Evita sobrecarga
                
            except requests.exceptions.ConnectionError:
                pytest.skip("API Sistema RAG não está rodando")
                break
            except requests.exceptions.Timeout:
                pytest.skip(f"Timeout na pergunta {i+1}")
                break
        
        # Calcula score geral
        if results:
            avg_keyword_score = sum(r["keyword_score"] for r in results) / len(results)
            print(f"\nScore médio de palavras-chave: {avg_keyword_score:.2f}")
            
            # Score médio deve ser pelo menos 0.4
            assert avg_keyword_score >= 0.4, f"Score médio muito baixo: {avg_keyword_score:.2f}"
    
    def test_intermediate_questions_accuracy(self):
        """Testa perguntas de dificuldade intermediária (4-7)"""
        if len(self.questions) < 7:
            pytest.skip("Não há perguntas intermediárias suficientes configuradas")
        
        intermediate_questions = self.questions[3:7]
        intermediate_keywords = self.keywords[3:7]
        
        results = []
        
        for i, (question, expected_keywords) in enumerate(zip(intermediate_questions, intermediate_keywords)):
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": question,
                        "include_history": False
                    },
                    timeout=45
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", data.get("response", "")).lower()
                    
                    if len(answer.strip()) > 0:
                        found_keywords = [kw for kw in expected_keywords if kw.lower() in answer]
                        keyword_score = len(found_keywords) / len(expected_keywords)
                        
                        results.append({
                            "question": question,
                            "keyword_score": keyword_score,
                            "found_keywords": found_keywords
                        })
                        
                        print(f"Pergunta intermediária {i+4}: {question}")
                        print(f"  Palavras-chave encontradas: {found_keywords}")
                        print(f"  Score: {keyword_score:.2f}")
                
                time.sleep(1)
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                continue
        
        if results:
            avg_score = sum(r["keyword_score"] for r in results) / len(results)
            print(f"\nScore médio intermediário: {avg_score:.2f}")
            
            # Para perguntas intermediárias, aceita score um pouco menor
            assert avg_score >= 0.25, f"Score intermediário muito baixo: {avg_score:.2f}"
    
    def test_response_quality_metrics(self):
        """Testa métricas de qualidade das respostas"""
        try:
            response = requests.post(
                f"{self.api_url}/search",
                headers=self.headers,
                json={
                    "query": self.questions[0] if self.questions else "O que é o Zep?",
                    "include_history": False
                },
                timeout=30
            )
            
            assert response.status_code == 200, f"Erro na consulta: {response.status_code}"
            
            data = response.json()
            answer = data.get("answer", data.get("response", ""))
            
            # Métricas de qualidade
            word_count = len(answer.split())
            char_count = len(answer)
            sentence_count = answer.count('.') + answer.count('!') + answer.count('?')
            
            print(f"Métricas de qualidade:")
            print(f"  Palavras: {word_count}")
            print(f"  Caracteres: {char_count}")
            print(f"  Sentenças: {sentence_count}")
            
            # Verifica se a resposta tem tamanho adequado
            assert word_count >= 10, f"Resposta muito curta: {word_count} palavras"
            assert word_count <= 500, f"Resposta muito longa: {word_count} palavras"
            assert sentence_count >= 1, "Resposta sem pontuação adequada"
            
        except requests.exceptions.ConnectionError:
            pytest.skip("API Sistema RAG não está rodando")
        except requests.exceptions.Timeout:
            pytest.skip("Timeout no teste de qualidade")
    
    def test_consistency_across_requests(self):
        """Testa consistência das respostas para a mesma pergunta"""
        if not self.questions:
            pytest.skip("Nenhuma pergunta configurada")
        
        question = self.questions[0]
        responses = []
        
        # Faz a mesma pergunta 3 vezes
        for i in range(3):
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers=self.headers,
                    json={
                        "query": question,
                        "include_history": False
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    data = response.json()
                    answer = data.get("answer", data.get("response", ""))
                    responses.append(answer.lower())
                
                time.sleep(2)  # Pausa entre requisições
                
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                break
        
        if len(responses) >= 2:
            # Verifica se as respostas têm alguma similaridade
            # (não devem ser completamente diferentes)
            
            first_words = set(responses[0].split()[:20])  # Primeiras 20 palavras
            
            similarities = []
            for response in responses[1:]:
                response_words = set(response.split()[:20])
                intersection = len(first_words.intersection(response_words))
                union = len(first_words.union(response_words))
                similarity = intersection / union if union > 0 else 0
                similarities.append(similarity)
            
            avg_similarity = sum(similarities) / len(similarities)
            print(f"Similaridade média entre respostas: {avg_similarity:.2f}")
            
            # Deve ter pelo menos 30% de similaridade (palavras em comum)
            assert avg_similarity >= 0.3, f"Respostas muito inconsistentes: {avg_similarity:.2f}"

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])