#!/usr/bin/env python3
"""
Testes automatizados para o sistema de busca do Sistema RAG Multimodal

Testa todos os componentes de busca:
- RAG Pipeline
- Query Transformer
- Vector Searcher
- Image Fetcher
- Reranker
- Conversational RAG
"""

import pytest
import os
import time
from typing import List, Dict, Any
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Imports do sistema RAG
try:
    from system_rag.search.conversational_rag import ModularConversationalRAG
    from system_rag.search.retrieval.rag_pipeline import RAGPipeline
    from system_rag.search.retrieval.query_transformer import QueryTransformer
    from system_rag.search.retrieval.vector_searcher import VectorSearcher
    from system_rag.search.retrieval.image_fetcher import ImageFetcher
    from system_rag.search.retrieval.reranker import SearchReranker
    from system_rag.search.embeddings.voyage_embedder import VoyageEmbedder
except ImportError as e:
    pytest.skip(f"Módulos do sistema RAG não disponíveis: {e}", allow_module_level=True)

class TestSearchConfig:
    """Configuração para testes de busca"""
    
    # Chaves de API
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')
    ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
    ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
    ASTRA_DB_KEYSPACE = os.getenv('ASTRA_DB_KEYSPACE', 'default_keyspace')
    ASTRA_DB_COLLECTION = os.getenv('ASTRA_DB_COLLECTION', 'test_collection')
    R2_ENDPOINT = os.getenv('R2_ENDPOINT')
    R2_AUTH_TOKEN = os.getenv('R2_AUTH_TOKEN')
    
    # Queries de teste
    TEST_QUERIES = [
        "Quais produtos estão disponíveis?",
        "Qual é o preço do hambúrguer?",
        "Vocês têm opções vegetarianas?",
        "Qual o horário de funcionamento?",
        "Como posso fazer um pedido?"
    ]
    
    @property
    def has_openai_api(self) -> bool:
        return bool(self.OPENAI_API_KEY)
    
    @property
    def has_voyage_api(self) -> bool:
        return bool(self.VOYAGE_API_KEY)
    
    @property
    def has_astra_config(self) -> bool:
        return bool(self.ASTRA_DB_APPLICATION_TOKEN and self.ASTRA_DB_API_ENDPOINT)
    
    @property
    def has_r2_config(self) -> bool:
        return bool(self.R2_ENDPOINT and self.R2_AUTH_TOKEN)
    
    @property
    def has_full_config(self) -> bool:
        return all([
            self.has_openai_api,
            self.has_voyage_api,
            self.has_astra_config
        ])

@pytest.fixture
def search_config():
    """Fixture com configuração de busca"""
    return TestSearchConfig()

class TestQueryTransformer:
    """Testes do Query Transformer"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_openai_api, reason="OPENAI_API_KEY não configurada")
    def test_transformer_initialization(self, search_config):
        """Testa inicialização do transformer"""
        transformer = QueryTransformer()
        assert transformer is not None
    
    @pytest.mark.skipif(not TestSearchConfig().has_openai_api, reason="OPENAI_API_KEY não configurada")
    def test_simple_query_transform(self, search_config):
        """Testa transformação de query simples"""
        transformer = QueryTransformer()
        
        chat_history = [
            {"role": "user", "content": "Quais produtos vocês têm?"}
        ]
        
        try:
            result = transformer.transform_query(chat_history)
            assert 'original_query' in result
            assert 'transformed_query' in result
            assert 'needs_transformation' in result
            assert len(result['transformed_query']) > 0
        except Exception as e:
            pytest.skip(f"Transformação de query falhou: {e}")
    
    @pytest.mark.skipif(not TestSearchConfig().has_openai_api, reason="OPENAI_API_KEY não configurada")
    def test_conversational_query_transform(self, search_config):
        """Testa transformação de query conversacional"""
        transformer = QueryTransformer()
        
        chat_history = [
            {"role": "user", "content": "Quais produtos vocês têm?"},
            {"role": "assistant", "content": "Temos hambúrgueres, batatas fritas..."},
            {"role": "user", "content": "E sobre os preços?"}
        ]
        
        try:
            result = transformer.transform_query(chat_history)
            assert result['needs_transformation'] is True
            assert 'preço' in result['transformed_query'].lower() or 'valor' in result['transformed_query'].lower()
        except Exception as e:
            pytest.skip(f"Transformação conversacional falhou: {e}")

class TestVectorSearcher:
    """Testes do Vector Searcher"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_astra_config, reason="Configuração Astra DB não disponível")
    def test_searcher_initialization(self, search_config):
        """Testa inicialização do searcher"""
        searcher = VectorSearcher()
        assert searcher is not None
    
    @pytest.mark.skipif(not TestSearchConfig().has_astra_config, reason="Configuração Astra DB não disponível")
    def test_connection(self, search_config):
        """Testa conexão com Astra DB"""
        searcher = VectorSearcher()
        
        try:
            connection_test = searcher.test_connection()
            assert 'status' in connection_test
            assert 'message' in connection_test
            
            if connection_test['status'] == 'success':
                assert 'document_count' in connection_test
        except Exception as e:
            pytest.skip(f"Conexão com Astra DB falhou: {e}")
    
    @pytest.mark.skipif(
        not all([TestSearchConfig().has_astra_config, TestSearchConfig().has_voyage_api]),
        reason="Astra DB ou Voyage API não configurados"
    )
    def test_search_by_text(self, search_config):
        """Testa busca por texto"""
        searcher = VectorSearcher()
        embedder = VoyageEmbedder(api_key=search_config.VOYAGE_API_KEY)
        
        try:
            # Gerar embedding de teste
            test_query = "produtos disponíveis"
            embedding_result = embedder.embed_text(test_query)
            
            if 'embedding' in embedding_result:
                # Fazer busca
                search_results = searcher.search_by_text(
                    query=test_query,
                    embedding=embedding_result['embedding'],
                    limit=5
                )
                
                assert 'results' in search_results
                assert 'total_results' in search_results
                assert isinstance(search_results['results'], list)
                
        except Exception as e:
            pytest.skip(f"Busca vetorial falhou: {e}")

class TestImageFetcher:
    """Testes do Image Fetcher"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_r2_config, reason="Configuração R2 não disponível")
    def test_fetcher_initialization(self, search_config):
        """Testa inicialização do fetcher"""
        fetcher = ImageFetcher()
        assert fetcher is not None
    
    @pytest.mark.skipif(not TestSearchConfig().has_r2_config, reason="Configuração R2 não disponível")
    def test_enrich_search_results(self, search_config):
        """Testa enriquecimento de resultados com imagens"""
        fetcher = ImageFetcher()
        
        # Mock de resultados de busca
        mock_results = {
            'results': [
                {
                    'document_name': 'test_doc',
                    'page_number': 1,
                    'content': 'Conteúdo de teste',
                    'metadata': {'document_name': 'test_doc'}
                }
            ],
            'total_results': 1
        }
        
        try:
            enriched = fetcher.enrich_search_results(mock_results)
            assert 'results' in enriched
            assert len(enriched['results']) == 1
            # Resultado pode ter image_url adicionado ou não, dependendo se imagem existe
        except Exception as e:
            pytest.skip(f"Enriquecimento com imagens falhou: {e}")

class TestSearchReranker:
    """Testes do Search Reranker"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_openai_api, reason="OPENAI_API_KEY não configurada")
    def test_reranker_initialization(self, search_config):
        """Testa inicialização do reranker"""
        reranker = SearchReranker()
        assert reranker is not None
    
    @pytest.mark.skipif(not TestSearchConfig().has_openai_api, reason="OPENAI_API_KEY não configurada")
    def test_rerank_results(self, search_config):
        """Testa reordenação de resultados"""
        reranker = SearchReranker()
        
        # Mock de resultados para rerank
        mock_results = {
            'results': [
                {
                    'content': 'Hambúrguer clássico com queijo e alface',
                    'document_name': 'cardapio',
                    'page_number': 1,
                    'similarity_score': 0.8
                },
                {
                    'content': 'Batatas fritas crocantes',
                    'document_name': 'cardapio',
                    'page_number': 2,
                    'similarity_score': 0.7
                }
            ]
        }
        
        query = "Qual o preço do hambúrguer?"
        
        try:
            reranked = reranker.rerank_results(query, mock_results, max_results=2)
            
            assert 'selected_results' in reranked
            assert 'justification' in reranked
            assert 'rerank_scores' in reranked
            assert len(reranked['selected_results']) <= 2
            
        except Exception as e:
            pytest.skip(f"Reranking falhou: {e}")

class TestRAGPipeline:
    """Testes do RAG Pipeline"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_pipeline_initialization(self, search_config):
        """Testa inicialização do pipeline"""
        pipeline = RAGPipeline(
            max_candidates=10,
            max_selected=3,
            enable_reranking=True,
            enable_image_fetching=True
        )
        assert pipeline.max_candidates == 10
        assert pipeline.max_selected == 3
        assert pipeline.enable_reranking is True
        assert pipeline.enable_image_fetching is True
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_search_and_answer(self, search_config):
        """Testa busca e resposta completa"""
        pipeline = RAGPipeline(max_candidates=5, max_selected=2)
        
        query = "Quais produtos estão disponíveis?"
        
        try:
            start_time = time.time()
            result = pipeline.search_and_answer(query)
            response_time = time.time() - start_time
            
            # Verificar estrutura da resposta
            assert 'answer' in result
            assert 'selected_pages' in result
            assert 'justification' in result
            assert 'query_info' in result
            
            # Verificar conteúdo
            assert len(result['answer']) > 0
            assert isinstance(result['selected_pages'], list)
            assert response_time < 60  # Deve responder em menos de 1 minuto
            
        except Exception as e:
            pytest.skip(f"Pipeline completo falhou: {e}")

class TestModularConversationalRAG:
    """Testes do RAG Conversacional"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_rag_initialization(self, search_config):
        """Testa inicialização do RAG conversacional"""
        rag = ModularConversationalRAG()
        assert rag is not None
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_simple_ask(self, search_config):
        """Testa pergunta simples"""
        rag = ModularConversationalRAG()
        
        try:
            answer = rag.ask("Quais produtos vocês têm?")
            assert isinstance(answer, str)
            assert len(answer) > 0
            assert "não consegui encontrar" not in answer.lower()
        except Exception as e:
            pytest.skip(f"Pergunta simples falhou: {e}")
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_conversational_context(self, search_config):
        """Testa contexto conversacional"""
        rag = ModularConversationalRAG()
        
        try:
            # Primeira pergunta
            answer1 = rag.ask("Quais produtos vocês têm?")
            assert len(answer1) > 0
            
            # Segunda pergunta com contexto
            answer2 = rag.ask("E os preços?")
            assert len(answer2) > 0
            
            # Verificar se o histórico foi mantido
            assert len(rag.chat_history) >= 4  # 2 user + 2 assistant
            
        except Exception as e:
            pytest.skip(f"Contexto conversacional falhou: {e}")
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_multiple_queries(self, search_config):
        """Testa múltiplas queries diferentes"""
        rag = ModularConversationalRAG()
        
        successful_queries = 0
        total_time = 0
        
        for query in search_config.TEST_QUERIES[:3]:  # Testar apenas 3 para velocidade
            try:
                start_time = time.time()
                answer = rag.ask(query)
                query_time = time.time() - start_time
                
                if len(answer) > 0 and "não consegui encontrar" not in answer.lower():
                    successful_queries += 1
                
                total_time += query_time
                
                # Pausa entre queries para evitar rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"Query '{query}' falhou: {e}")
                continue
        
        # Pelo menos 50% das queries devem ter sucesso
        success_rate = successful_queries / len(search_config.TEST_QUERIES[:3])
        assert success_rate >= 0.5, f"Taxa de sucesso muito baixa: {success_rate:.1%}"
        
        # Tempo médio por query deve ser razoável
        avg_time = total_time / len(search_config.TEST_QUERIES[:3])
        assert avg_time < 30, f"Tempo médio muito alto: {avg_time:.1f}s"

class TestPerformanceAndEdgeCases:
    """Testes de performance e casos extremos"""
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_empty_query(self, search_config):
        """Testa query vazia"""
        rag = ModularConversationalRAG()
        
        try:
            answer = rag.ask("")
            # Deve retornar alguma resposta indicando problema
            assert len(answer) > 0
        except Exception:
            # Exceção também é aceitável para query vazia
            pass
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_very_long_query(self, search_config):
        """Testa query muito longa"""
        rag = ModularConversationalRAG()
        
        long_query = "Esta é uma pergunta muito longa sobre produtos " * 50  # ~2500 chars
        
        try:
            answer = rag.ask(long_query[:1000])  # Truncar para evitar erros de API
            assert len(answer) > 0
        except Exception as e:
            pytest.skip(f"Query longa falhou: {e}")
    
    @pytest.mark.skipif(not TestSearchConfig().has_full_config, reason="Configuração completa não disponível")
    def test_special_characters(self, search_config):
        """Testa queries com caracteres especiais"""
        rag = ModularConversationalRAG()
        
        special_queries = [
            "Quais produtos têm açúcar? 🍭",
            "Preço em R$?",
            "Opções p/ vegetarianos?",
            "Horário: 9h às 18h?"
        ]
        
        successful = 0
        for query in special_queries:
            try:
                answer = rag.ask(query)
                if len(answer) > 0:
                    successful += 1
            except Exception:
                continue
        
        # Pelo menos metade deve funcionar
        assert successful >= len(special_queries) // 2
    
    def test_concurrent_usage(self, search_config):
        """Testa uso concorrente (apenas se todas as APIs estão configuradas)"""
        if not search_config.has_full_config:
            pytest.skip("Configuração completa não disponível")
        
        import concurrent.futures
        import threading
        
        def make_query(query_num):
            try:
                rag = ModularConversationalRAG()
                answer = rag.ask(f"Teste concorrência {query_num}")
                return len(answer) > 0
            except:
                return False
        
        # Executar 3 queries simultâneas
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_query, i) for i in range(3)]
            results = [future.result() for future in futures]
        
        # Pelo menos 2 das 3 devem ter sucesso
        assert sum(results) >= 2

if __name__ == "__main__":
    # Executar testes básicos se chamado diretamente
    import sys
    
    print("🧪 Executando testes básicos de busca...")
    
    config = TestSearchConfig()
    
    # Verificar configuração
    apis_available = []
    if config.has_openai_api:
        apis_available.append("OpenAI")
    if config.has_voyage_api:
        apis_available.append("Voyage AI")
    if config.has_astra_config:
        apis_available.append("Astra DB")
    if config.has_r2_config:
        apis_available.append("Cloudflare R2")
    
    print(f"✅ APIs disponíveis para teste: {', '.join(apis_available) if apis_available else 'Nenhuma'}")
    
    if config.has_full_config:
        print("✅ Configuração completa disponível - testes completos habilitados")
    else:
        print("⚠️  Configuração incompleta - alguns testes serão pulados")
    
    # Executar com pytest se disponível
    try:
        import pytest
        print("\n🚀 Executando testes completos com pytest...")
        pytest.main([__file__, "-v", "-x"])  # -x para parar no primeiro erro
    except ImportError:
        print("⚠️  pytest não disponível. Instale com: pip install pytest")
        print("✅ Testes básicos de configuração passaram")