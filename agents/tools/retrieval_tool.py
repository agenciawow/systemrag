"""
Tool de Retrieval para Agentes

Tool que encapsula o sistema de busca atual (etapas 1-6 do pipeline) 
retornando documentos selecionados para que o agente gere a resposta.
"""

import os
from typing import List, Dict, Any, Optional

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Fallback se pydantic não estiver disponível
    class BaseModel:
        pass
    def Field(**kwargs):
        return None

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv():
        pass

from system_rag.search.retrieval import RAGPipeline


class RetrievalResult(BaseModel):
    """Resultado da busca para o agente"""
    success: bool = Field(description="Se a busca foi bem-sucedida")
    documents: List[Dict[str, Any]] = Field(default=[], description="Documentos encontrados")
    query_info: Dict[str, Any] = Field(default={}, description="Informações sobre a query")
    error: Optional[str] = Field(default=None, description="Erro se houver")


class RetrievalTool:
    """
    Tool de busca que encapsula o pipeline RAG até o reranking
    
    Funcionalidades:
    - Transformação de queries conversacionais
    - Busca vetorial multimodal  
    - Re-ranking inteligente
    - Verificação de relevância
    - Retorna documentos selecionados (sem gerar resposta)
    """
    
    def __init__(self,
                 max_candidates: int = 10,
                 max_selected: int = 2,
                 enable_reranking: bool = True,
                 enable_image_fetching: bool = True):
        """
        Inicializa a tool de retrieval
        
        Args:
            max_candidates: Máximo de candidatos da busca vetorial
            max_selected: Máximo de documentos selecionados  
            enable_reranking: Habilitar re-ranking com IA
            enable_image_fetching: Habilitar busca de imagens
        """
        load_dotenv()
        
        # Validação de ambiente
        required_vars = [
            "VOYAGE_API_KEY", "OPENAI_API_KEY",
            "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var) or not os.getenv(var).strip()]
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente ausentes: {missing_vars}")
        
        self.max_candidates = max_candidates
        self.max_selected = max_selected
        self.enable_reranking = enable_reranking
        self.enable_image_fetching = enable_image_fetching
        
        # Inicializar pipeline RAG
        self._initialize_pipeline()
    
    def _initialize_pipeline(self):
        """Inicializa o pipeline RAG"""
        try:
            self.rag_pipeline = RAGPipeline(
                max_candidates=self.max_candidates,
                max_selected=self.max_selected,
                enable_reranking=self.enable_reranking,
                enable_image_fetching=self.enable_image_fetching
            )
        except Exception as e:
            raise RuntimeError(f"Falha ao inicializar pipeline RAG: {e}")
    
    def search_documents(self, 
                        query: str,
                        chat_history: List[Dict[str, str]] = None) -> RetrievalResult:
        """
        Busca documentos relevantes para uma query
        
        Args:
            query: Query do usuário
            chat_history: Histórico da conversa (opcional)
            
        Returns:
            RetrievalResult com documentos encontrados
        """
        try:
            # ETAPA 1: Transformar query conversacional
            if chat_history:
                current_history = chat_history + [{"role": "user", "content": query}]
                transformed_query = self.rag_pipeline.query_transformer.transform_query(current_history)
            else:
                transformed_query = query
            
            # Verificar se precisa fazer RAG
            if not self.rag_pipeline.query_transformer.needs_rag(transformed_query):
                return RetrievalResult(
                    success=True,
                    documents=[],
                    query_info={
                        "original_query": query,
                        "transformed_query": transformed_query,
                        "needs_rag": False,
                        "type": "simple_query"
                    }
                )
            
            # ETAPA 2: Gerar embedding da query
            query_embedding = self.rag_pipeline.embedder.embed_query(transformed_query)
            
            if not query_embedding:
                return RetrievalResult(
                    success=False,
                    error="Falha ao gerar embedding da query"
                )
            
            # ETAPA 3: Busca vetorial
            search_results = self.rag_pipeline.vector_searcher.search_similar(
                query_embedding,
                limit=self.max_candidates
            )
            
            if not search_results.documents:
                return RetrievalResult(
                    success=False,
                    error="Nenhum documento relevante encontrado"
                )
            
            # ETAPA 4: Buscar imagens (se habilitado)
            candidates = search_results.documents
            if self.enable_image_fetching:
                candidates = self.rag_pipeline.image_fetcher.enrich_search_results(candidates)
            
            # ETAPA 5: Re-ranking (se habilitado)
            if self.enable_reranking:
                rerank_result = self.rag_pipeline.reranker.rerank_results(
                    transformed_query,
                    candidates,
                    max_selected=self.max_selected
                )
                selected_docs = rerank_result.selected_docs
                justification = rerank_result.justification
            else:
                selected_docs = candidates[:self.max_selected]
                justification = f"Top {len(selected_docs)} resultados por similaridade"
            
            # ETAPA 6: Verificar relevância
            is_relevant = self._verify_relevance(transformed_query, selected_docs)
            
            if not is_relevant:
                return RetrievalResult(
                    success=False,
                    error="A informação solicitada não foi encontrada de forma explícita nos documentos"
                )
            
            # Preparar documentos para o agente
            formatted_docs = []
            for doc in selected_docs:
                doc_data = {
                    "document_name": doc.document_name,
                    "page_number": doc.page_number,
                    "content": doc.content,
                    "similarity_score": doc.similarity,
                    "has_image": doc.has_image
                }
                
                # Adicionar imagem se disponível
                if hasattr(doc, 'image_base64') and doc.image_base64:
                    doc_data["image_base64"] = doc.image_base64
                
                formatted_docs.append(doc_data)
            
            # Informações sobre a query
            query_info = {
                "original_query": query,
                "transformed_query": transformed_query,
                "needs_rag": True,
                "total_candidates": len(search_results.documents),
                "selected_count": len(selected_docs),
                "justification": justification,
                "reranking_enabled": self.enable_reranking,
                "image_fetching_enabled": self.enable_image_fetching
            }
            
            return RetrievalResult(
                success=True,
                documents=formatted_docs,
                query_info=query_info
            )
            
        except Exception as e:
            return RetrievalResult(
                success=False,
                error=f"Erro na busca: {str(e)}"
            )
    
    def _verify_relevance(self, query: str, selected_docs: List[Any]) -> bool:
        """Verifica se os documentos selecionados são relevantes para a query"""
        if not selected_docs:
            return False
        
        try:
            # Usar o método do pipeline original
            return self.rag_pipeline._verify_relevance(query, selected_docs)
        except Exception:
            return True  # Fallback conservador
    
    def test_connection(self) -> Dict[str, Any]:
        """Testa conexão com todos os componentes"""
        try:
            test_result = self.rag_pipeline.test_pipeline()
            return {
                "success": test_result.success,
                "message": test_result.message,
                "details": test_result.details
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro no teste: {e}",
                "details": {}
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas da tool"""
        try:
            pipeline_stats = self.rag_pipeline.get_pipeline_stats()
            pipeline_stats["tool_config"] = {
                "max_candidates": self.max_candidates,
                "max_selected": self.max_selected,
                "reranking_enabled": self.enable_reranking,
                "image_fetching_enabled": self.enable_image_fetching
            }
            return pipeline_stats
        except Exception as e:
            return {"error": str(e)}


# Funções de conveniência para uso direto
def search_documents(query: str, 
                    chat_history: List[Dict[str, str]] = None,
                    **kwargs) -> RetrievalResult:
    """
    Função de conveniência para busca de documentos
    
    Args:
        query: Query do usuário
        chat_history: Histórico da conversa
        **kwargs: Argumentos para RetrievalTool
        
    Returns:
        Resultado da busca
    """
    tool = RetrievalTool(**kwargs)
    return tool.search_documents(query, chat_history)


def test_retrieval_tool() -> Dict[str, Any]:
    """Testa a tool de retrieval"""
    try:
        tool = RetrievalTool()
        return tool.test_connection()
    except Exception as e:
        return {
            "success": False,
            "message": f"Erro ao inicializar tool: {e}",
            "details": {}
        }