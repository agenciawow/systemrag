"""
Componentes de Retrieval para Sistema RAG

Este módulo contém todos os componentes necessários para busca e recuperação
de informações no sistema RAG multimodal.
"""

from .query_transformer import QueryTransformer, transform_conversational_query
from .vector_searcher import VectorSearcher, search_documents
from .image_fetcher import ImageFetcher, fetch_image_from_r2, enrich_results_with_images
from .reranker import SearchReranker, SimpleReranker, rerank_search_results
from .rag_pipeline import RAGPipeline, create_rag_pipeline, search_and_answer

__all__ = [
    # Classes principais
    'QueryTransformer',
    'VectorSearcher', 
    'ImageFetcher',
    'SearchReranker',
    'SimpleReranker',
    'RAGPipeline',
    
    # Funções de conveniência
    'transform_conversational_query',
    'search_documents',
    'fetch_image_from_r2',
    'enrich_results_with_images',
    'rerank_search_results',
    'create_rag_pipeline',
    'search_and_answer'
]