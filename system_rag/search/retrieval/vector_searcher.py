"""
Buscador Vetorial para Sistema RAG

Realiza busca de similaridade em bancos de dados vetoriais.
"""
import logging
from typing import List, Dict, Any, Optional
from astrapy import DataAPIClient

from ...models.data_models import QueryEmbedding, SearchResult, SearchResults, ProcessingStatus
from ...config.settings import settings

logger = logging.getLogger(__name__)


class VectorSearcher:
    """
    Buscador vetorial para documentos multimodais
    
    Funcionalidades:
    - Busca por similaridade vetorial
    - Suporte a múltiplos tipos de documentos
    - Filtros por metadata
    - Estatísticas de busca
    """
    
    def __init__(self,
                 astra_db_token: str = None,
                 astra_db_endpoint: str = None,
                 collection_name: str = None,
                 max_results: int = 10):
        """
        Inicializa o buscador vetorial
        
        Args:
            astra_db_token: Token do Astra DB
            astra_db_endpoint: Endpoint do Astra DB
            collection_name: Nome da coleção
            max_results: Número máximo de resultados
        """
        self.astra_db_token = astra_db_token or settings.api.astra_db_token
        self.astra_db_endpoint = astra_db_endpoint or settings.api.astra_db_api_endpoint
        self.collection_name = collection_name or settings.astra_db.collection_name
        self.max_results = max_results
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Inicializa conexão com o banco vetorial"""
        try:
            logger.info("Conectando ao Astra DB...")
            
            self.client = DataAPIClient(self.astra_db_token)
            self.database = self.client.get_database_by_api_endpoint(self.astra_db_endpoint)
            self.collection = self.database.get_collection(self.collection_name)
            
            # Teste de conectividade
            try:
                count = self.collection.estimated_document_count()
                logger.info(f"Conectado ao Astra DB - Coleção '{self.collection_name}' com ~{count} documentos")
            except Exception as test_error:
                logger.warning(f"Teste de conectividade falhou: {test_error}")
                
        except Exception as e:
            logger.error(f"Falha ao conectar ao Astra DB: {e}")
            raise
    
    def search_similar(self, 
                      query_embedding: QueryEmbedding,
                      limit: int = None,
                      similarity_threshold: float = 0.0,
                      document_filter: Optional[str] = None,
                      metadata_filters: Optional[Dict[str, Any]] = None) -> SearchResults:
        """
        Busca documentos similares baseado em embedding
        
        Args:
            query_embedding: Embedding da query
            limit: Limite de resultados (None = usar max_results)
            similarity_threshold: Threshold mínimo de similaridade
            document_filter: Filtro por nome do documento
            metadata_filters: Filtros adicionais por metadata
            
        Returns:
            Resultados da busca vetorial
        """
        try:
            logger.debug(f"Iniciando busca vetorial para: '{query_embedding.query}'")
            
            # Preparar filtros
            search_filters = {}
            if document_filter:
                search_filters["document_name"] = document_filter
            if metadata_filters:
                search_filters.update(metadata_filters)
            
            # Determinar limite
            search_limit = limit or self.max_results
            
            logger.debug(f"Buscando no Astra DB com limite de {search_limit}...")
            
            # Executar busca
            cursor = self.collection.find(
                filter=search_filters if search_filters else {},
                sort={"$vector": query_embedding.embedding},
                limit=search_limit,
                include_similarity=True,
                projection={
                    "_id": True,
                    "content": True,
                    "document_name": True,
                    "page_number": True,
                    "image_url": True,
                    "image_filename_r2": True,
                    "image_base64": True,
                    "metadata": True
                }
            )
            
            # Processar resultados
            documents = []
            similarities = []
            
            for doc in cursor:
                similarity = doc.get("$similarity", 0.0)
                
                # Aplicar threshold de similaridade
                if similarity < similarity_threshold:
                    continue
                
                # Criar resultado
                search_result = SearchResult(
                    document_id=str(doc.get("_id", "")),
                    content=doc.get("content", ""),
                    document_name=doc.get("document_name", ""),
                    page_number=doc.get("page_number"),
                    similarity=similarity,
                    image_url=doc.get("image_url"),
                    image_filename_r2=doc.get("image_filename_r2"),
                    image_base64=doc.get("image_base64"),
                    has_image=bool(doc.get("image_url") or doc.get("image_base64")),
                    metadata=doc.get("metadata", {})
                )
                
                documents.append(search_result)
                similarities.append(similarity)
            
            # Calcular estatísticas
            similarity_stats = {}
            if similarities:
                similarity_stats = {
                    "min_similarity": min(similarities),
                    "max_similarity": max(similarities),
                    "avg_similarity": sum(similarities) / len(similarities),
                    "threshold_applied": similarity_threshold
                }
            
            logger.info(f"Busca completada: {len(documents)} documentos encontrados")
            
            return SearchResults(
                documents=documents,
                total_results=len(documents),
                query_text=query_embedding.query,
                similarity_stats=similarity_stats
            )
            
        except Exception as e:
            logger.error(f"Erro na busca vetorial: {e}")
            return SearchResults(
                documents=[],
                total_results=0,
                query_text=query_embedding.query,
                similarity_stats={"error": str(e)}
            )
    
    def search_by_text(self,
                      query_text: str,
                      embedding: List[float],
                      **kwargs) -> SearchResults:
        """
        Busca por texto usando embedding fornecido
        
        Args:
            query_text: Texto da query
            embedding: Embedding da query
            **kwargs: Argumentos para search_similar
            
        Returns:
            Resultados da busca
        """
        query_embedding = QueryEmbedding(
            query=query_text,
            embedding=embedding
        )
        
        return self.search_similar(query_embedding, **kwargs)
    
    def get_document_by_id(self, document_id: str) -> Optional[SearchResult]:
        """
        Busca documento específico por ID
        
        Args:
            document_id: ID do documento
            
        Returns:
            Documento encontrado ou None
        """
        try:
            doc = self.collection.find_one({"_id": document_id})
            
            if not doc:
                return None
            
            return SearchResult(
                document_id=str(doc.get("_id", "")),
                content=doc.get("content", ""),
                document_name=doc.get("document_name", ""),
                page_number=doc.get("page_number"),
                similarity=1.0,  # Busca exata
                image_url=doc.get("image_url"),
                image_filename_r2=doc.get("image_filename_r2"),
                image_base64=doc.get("image_base64"),
                has_image=bool(doc.get("image_url") or doc.get("image_base64")),
                metadata=doc.get("metadata", {})
            )
            
        except Exception as e:
            logger.error(f"Erro ao buscar documento por ID: {e}")
            return None
    
    def list_documents(self,
                      document_filter: Optional[str] = None,
                      limit: int = 50) -> List[Dict[str, Any]]:
        """
        Lista documentos na coleção
        
        Args:
            document_filter: Filtro por nome do documento
            limit: Número máximo de documentos
            
        Returns:
            Lista de informações dos documentos
        """
        try:
            # Preparar filtro
            search_filter = {}
            if document_filter:
                search_filter["document_name"] = document_filter
            
            # Buscar documentos
            cursor = self.collection.find(
                filter=search_filter,
                limit=limit,
                projection={
                    "_id": True,
                    "document_name": True,
                    "page_number": True,
                    "has_image": True,
                    "char_count": True
                }
            )
            
            documents = []
            for doc in cursor:
                documents.append({
                    "id": str(doc.get("_id", "")),
                    "document_name": doc.get("document_name", ""),
                    "page_number": doc.get("page_number"),
                    "has_image": doc.get("has_image", False),
                    "char_count": doc.get("char_count", 0)
                })
            
            return documents
            
        except Exception as e:
            logger.error(f"Erro ao listar documentos: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas da coleção
        
        Returns:
            Estatísticas da coleção
        """
        try:
            # Contagem total estimada
            total_count = self.collection.estimated_document_count()
            
            # Documentos únicos
            pipeline = [
                {"$group": {"_id": "$document_name", "pages": {"$sum": 1}}},
                {"$group": {"_id": None, "unique_docs": {"$sum": 1}, "total_pages": {"$sum": "$pages"}}}
            ]
            
            agg_result = list(self.collection.aggregate(pipeline))
            
            stats = {
                "total_chunks": total_count,
                "collection_name": self.collection_name
            }
            
            if agg_result:
                result = agg_result[0]
                stats.update({
                    "unique_documents": result.get("unique_docs", 0),
                    "total_pages": result.get("total_pages", 0)
                })
            
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas: {e}")
            return {
                "error": str(e),
                "collection_name": self.collection_name
            }
    
    def test_connection(self) -> ProcessingStatus:
        """
        Testa conexão com o banco de dados
        
        Returns:
            Status da conexão
        """
        try:
            # Tentar operação simples
            count = self.collection.estimated_document_count()
            
            return ProcessingStatus(
                success=True,
                message=f"Conexão estabelecida - {count} documentos na coleção '{self.collection_name}'",
                details={"document_count": count}
            )
            
        except Exception as e:
            return ProcessingStatus(
                success=False,
                message=f"Erro na conexão: {str(e)}",
                details={"error": str(e)}
            )


def search_documents(query_text: str,
                    embedding: List[float],
                    limit: int = 10,
                    **kwargs) -> SearchResults:
    """
    Função de conveniência para buscar documentos
    
    Args:
        query_text: Texto da query
        embedding: Embedding da query
        limit: Número máximo de resultados
        **kwargs: Argumentos adicionais
        
    Returns:
        Resultados da busca
    """
    searcher = VectorSearcher(max_results=limit)
    return searcher.search_by_text(query_text, embedding, **kwargs)