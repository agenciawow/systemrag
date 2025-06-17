"""
Pipeline RAG Completo

Orquestra todo o processo de busca e geração de respostas.
"""
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI

from .query_transformer import QueryTransformer
from .vector_searcher import VectorSearcher
from .image_fetcher import ImageFetcher
from .reranker import SearchReranker
from ...models.data_models import SearchResults, RerankedResult, ProcessingStatus
from ...config.settings import settings
from ..embeddings.voyage_embedder import VoyageEmbedder

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    Pipeline completo de Retrieval-Augmented Generation
    
    Funcionalidades:
    - Transformação de queries conversacionais
    - Busca vetorial multimodal
    - Re-ranking inteligente
    - Geração de respostas contextuais
    - Suporte a imagens do R2
    """
    
    def __init__(self,
                 openai_client: OpenAI = None,
                 max_candidates: int = 10,
                 max_selected: int = 2,
                 enable_reranking: bool = True,
                 enable_image_fetching: bool = True):
        """
        Inicializa o pipeline RAG
        
        Args:
            openai_client: Cliente OpenAI
            max_candidates: Máximo de candidatos da busca vetorial
            max_selected: Máximo de documentos selecionados
            enable_reranking: Habilitar re-ranking com IA
            enable_image_fetching: Habilitar busca de imagens
        """
        self.openai_client = openai_client or OpenAI(api_key=settings.api.openai_api_key)
        self.max_candidates = max_candidates
        self.max_selected = max_selected
        self.enable_reranking = enable_reranking
        self.enable_image_fetching = enable_image_fetching
        
        # Inicializar componentes
        self.query_transformer = QueryTransformer(self.openai_client)
        self.embedder = VoyageEmbedder(api_key=settings.api.voyage_api_key)
        self.vector_searcher = VectorSearcher(max_results=max_candidates)
        self.reranker = SearchReranker(self.openai_client, max_candidates=max_candidates)
        
        if enable_image_fetching:
            self.image_fetcher = ImageFetcher()
        
        logger.info("Pipeline RAG inicializado")
    
    def search_and_answer(self, 
                         query: str,
                         chat_history: List[Dict[str, str]] = None) -> Dict[str, Any]:
        """
        Executa pipeline completo de busca e resposta
        
        Args:
            query: Query do usuário
            chat_history: Histórico da conversa (opcional)
            
        Returns:
            Resultado completo com resposta e metadados
        """
        try:
            logger.info(f"=== INICIANDO PIPELINE RAG ===")
            logger.info(f"Query: '{query}'")
            
            # ETAPA 1: Transformar query conversacional
            if chat_history:
                # Adicionar query atual ao histórico
                current_history = chat_history + [{"role": "user", "content": query}]
                transformed_query = self.query_transformer.transform_query(current_history)
            else:
                transformed_query = query
            
            logger.info(f"Query transformada: '{transformed_query}'")
            
            # Verificar se precisa fazer RAG
            if not self.query_transformer.needs_rag(transformed_query):
                logger.info("Query não precisa de RAG, gerando resposta simples")
                return self._generate_simple_response(query)
            
            # ETAPA 2: Gerar embedding da query
            logger.info("Gerando embedding da query...")
            query_embedding = self.embedder.embed_query(transformed_query)
            
            if not query_embedding:
                return {"error": "Falha ao gerar embedding da query"}
            
            # ETAPA 3: Busca vetorial
            logger.info("Executando busca vetorial...")
            search_results = self.vector_searcher.search_similar(
                query_embedding,
                limit=self.max_candidates
            )
            
            if not search_results.documents:
                return {"error": "Nenhum documento relevante encontrado"}
            
            logger.info(f"Encontrados {len(search_results.documents)} candidatos")
            
            # ETAPA 4: Buscar imagens (se habilitado)
            candidates = search_results.documents
            if self.enable_image_fetching:
                logger.info("Buscando imagens dos candidatos...")
                candidates = self.image_fetcher.enrich_search_results(candidates)
            
            # ETAPA 5: Re-ranking (se habilitado)
            if self.enable_reranking:
                logger.info("Executando re-ranking...")
                rerank_result = self.reranker.rerank_results(
                    transformed_query,
                    candidates,
                    max_selected=self.max_selected
                )
                selected_docs = rerank_result.selected_docs
                justification = rerank_result.justification
            else:
                # Seleção simples pelos top resultados
                selected_docs = candidates[:self.max_selected]
                justification = f"Top {len(selected_docs)} resultados por similaridade"
            
            logger.info(f"Selecionados {len(selected_docs)} documentos finais")
            
            # ETAPA 6: Verificar relevância
            logger.info("Verificando relevância...")
            is_relevant = self._verify_relevance(transformed_query, selected_docs)
            
            if not is_relevant:
                return {
                    "error": "A informação solicitada não foi encontrada de forma explícita nos documentos"
                }
            
            # ETAPA 7: Gerar resposta final
            logger.info("Gerando resposta final...")
            answer = self._generate_contextual_answer(transformed_query, selected_docs)
            
            # Preparar resultado completo
            result = self._build_complete_result(
                original_query=query,
                transformed_query=transformed_query,
                selected_docs=selected_docs,
                answer=answer,
                justification=justification,
                total_candidates=len(search_results.documents)
            )
            
            logger.info("=== PIPELINE RAG COMPLETADO ===")
            return result
            
        except Exception as e:
            logger.error(f"Erro no pipeline RAG: {e}")
            return {"error": f"Erro interno: {str(e)}"}
    
    def _generate_simple_response(self, query: str) -> Dict[str, Any]:
        """Gera resposta simples para queries que não precisam de RAG"""
        greetings = ["oi", "olá", "hello", "hi", "boa tarde", "bom dia", "boa noite"]
        thanks = ["obrigado", "obrigada", "thanks", "valeu"]
        
        if any(greeting in query.lower() for greeting in greetings):
            answer = "Olá! Sou seu assistente para consultas sobre documentos. Como posso ajudar você hoje?"
        elif any(thank in query.lower() for thank in thanks):
            answer = "De nada! Fico feliz em ajudar. Há mais alguma coisa que gostaria de saber?"
        else:
            answer = "Como posso ajudar você com consultas sobre os documentos? Faça uma pergunta específica e eu buscarei as informações relevantes."
        
        return {
            "query": query,
            "answer": answer,
            "requires_rag": False,
            "type": "simple_response"
        }
    
    def _verify_relevance(self, query: str, selected_docs: List[Any]) -> bool:
        """Verifica se os documentos selecionados são relevantes para a query"""
        if not selected_docs:
            return False
        
        try:
            # Combinar conteúdo dos documentos
            context_text = "\n\n".join(
                f"=== PÁGINA {doc.page_number} ===\n{doc.content}"
                for doc in selected_docs
            )
            
            prompt = (
                f"Analise o conteúdo para responder: \"{query}\"\n\n"
                f"Conteúdo:\n---\n{context_text}\n---\n\n"
                "O conteúdo contém informação factual para responder a pergunta? "
                "Responda apenas 'Sim' ou 'Não'."
            )
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_models.query_transform_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=5,
                temperature=0.0
            )
            
            verification_result = response.choices[0].message.content or ""
            logger.debug(f"Verificação de relevância: '{verification_result}'")
            
            return "sim" in verification_result.lower()
            
        except Exception as e:
            logger.error(f"Erro na verificação de relevância: {e}")
            return True  # Fallback conservador
    
    def _generate_contextual_answer(self, query: str, selected_docs: List[Any]) -> str:
        """Gera resposta contextual baseada nos documentos selecionados"""
        try:
            # Instrução para não usar markdown
            no_md = "NÃO use formatação Markdown como **, _, #. Escreva texto corrido natural."
            
            if len(selected_docs) == 1:
                # Resposta baseada em um documento
                doc = selected_docs[0]
                
                prompt = (
                    f"Assistente especializado em documentos acadêmicos.\n"
                    f"Pergunta: {query}\n\n"
                    f"Use APENAS o documento '{doc.document_name}', página {doc.page_number}.\n"
                    f"Conteúdo:\n{doc.content}\n\n"
                    f"Instruções: resposta clara e direta. Cite: documento '{doc.document_name}', página {doc.page_number}.\n"
                    f"{no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                # Adicionar imagem se disponível
                if doc.image_base64:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{doc.image_base64}"}
                    })
            
            else:
                # Resposta baseada em múltiplos documentos
                pages_str = " e ".join(
                    f"{doc.document_name} p.{doc.page_number}"
                    for doc in selected_docs
                )
                combined_text = "\n\n".join(
                    f"=== PÁGINA {doc.page_number} ===\n{doc.content}"
                    for doc in selected_docs
                )
                
                prompt = (
                    f"Pergunta: {query}\n\n"
                    f"Use os documentos: {pages_str}\n"
                    f"Conteúdo:\n{combined_text}\n\n"
                    f"Integre as informações e cite as fontes. {no_md}"
                )
                content = [{"type": "text", "text": prompt}]
                
                # Adicionar imagens se disponíveis
                for doc in selected_docs:
                    if doc.image_base64:
                        content.append({"type": "text", "text": f"\n--- PÁGINA {doc.page_number} ---"})
                        content.append({
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{doc.image_base64}"}
                        })
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_models.answer_generation_model,
                messages=[{"role": "user", "content": content}],
                max_tokens=2048,
                temperature=settings.openai_models.answer_generation_temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Erro ao processar resposta: {e}"
    
    def _build_complete_result(self,
                              original_query: str,
                              transformed_query: str,
                              selected_docs: List[Any],
                              answer: str,
                              justification: str,
                              total_candidates: int) -> Dict[str, Any]:
        """Constrói resultado completo do pipeline"""
        # Detalhes dos documentos selecionados
        selected_details = [
            {
                "document": doc.document_name,
                "page_number": doc.page_number,
                "similarity_score": doc.similarity,
                "has_image": doc.has_image
            }
            for doc in selected_docs
        ]
        
        selected_str = " + ".join(
            f"{detail['document']} (p.{detail['page_number']})"
            for detail in selected_details
        )
        
        return {
            "query": original_query,
            "transformed_query": transformed_query,
            "answer": answer,
            "selected_pages": selected_str,
            "selected_pages_details": selected_details,
            "selected_pages_count": len(selected_docs),
            "justification": justification,
            "total_candidates": total_candidates,
            "pipeline_config": {
                "max_candidates": self.max_candidates,
                "max_selected": self.max_selected,
                "reranking_enabled": self.enable_reranking,
                "image_fetching_enabled": self.enable_image_fetching
            }
        }
    
    def test_pipeline(self) -> ProcessingStatus:
        """
        Testa todos os componentes do pipeline
        
        Returns:
            Status dos testes
        """
        test_results = {}
        
        # Testar embedder
        try:
            test_embedding = self.embedder.embed_query("teste")
            test_results["embedder"] = bool(test_embedding)
        except Exception as e:
            test_results["embedder"] = f"Erro: {e}"
        
        # Testar vector searcher
        try:
            connection_test = self.vector_searcher.test_connection()
            test_results["vector_searcher"] = connection_test.success
        except Exception as e:
            test_results["vector_searcher"] = f"Erro: {e}"
        
        # Testar image fetcher
        if self.enable_image_fetching:
            try:
                image_test = self.image_fetcher.test_connection()
                test_results["image_fetcher"] = image_test.success
            except Exception as e:
                test_results["image_fetcher"] = f"Erro: {e}"
        
        # Determinar status geral
        all_success = all(
            result is True for result in test_results.values() 
            if isinstance(result, bool)
        )
        
        return ProcessingStatus(
            success=all_success,
            message="Pipeline testado com sucesso" if all_success else "Alguns componentes falharam",
            details=test_results
        )
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do pipeline
        
        Returns:
            Estatísticas dos componentes
        """
        stats = {
            "pipeline_config": {
                "max_candidates": self.max_candidates,
                "max_selected": self.max_selected,
                "reranking_enabled": self.enable_reranking,
                "image_fetching_enabled": self.enable_image_fetching
            },
            "query_transformer": self.query_transformer.get_cache_stats()
        }
        
        # Estatísticas do vector searcher
        try:
            stats["vector_database"] = self.vector_searcher.get_collection_stats()
        except Exception as e:
            stats["vector_database"] = {"error": str(e)}
        
        # Estatísticas do image fetcher
        if self.enable_image_fetching:
            try:
                stats["image_cache"] = self.image_fetcher.get_cache_stats()
            except Exception as e:
                stats["image_cache"] = {"error": str(e)}
        
        return stats


def create_rag_pipeline(**kwargs) -> RAGPipeline:
    """
    Função de conveniência para criar pipeline RAG
    
    Args:
        **kwargs: Argumentos para RAGPipeline
        
    Returns:
        Pipeline RAG configurado
    """
    return RAGPipeline(**kwargs)


def search_and_answer(query: str,
                     chat_history: List[Dict[str, str]] = None,
                     **kwargs) -> Dict[str, Any]:
    """
    Função de conveniência para busca e resposta
    
    Args:
        query: Query do usuário
        chat_history: Histórico da conversa
        **kwargs: Argumentos para o pipeline
        
    Returns:
        Resultado da busca e resposta
    """
    pipeline = RAGPipeline(**kwargs)
    return pipeline.search_and_answer(query, chat_history)