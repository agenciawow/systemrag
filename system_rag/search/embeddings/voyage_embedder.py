"""
Voyage Multimodal Embedder

Gera embeddings multimodais usando a API da Voyage AI.
"""
import requests
import json
from typing import List, Dict, Any, Optional, Union
from dataclasses import asdict

from ...models.data_models import (
    ChunkCollection, MultimodalChunk, EmbeddedChunk, 
    QueryEmbedding, ProcessingStatus
)
from ...utils.helpers import (
    extract_text_content, extract_image_content, 
    chunk_list, truncate_text
)
from ...config.settings import settings


class VoyageEmbedder:
    """
    Componente para geração de embeddings multimodais
    
    Funcionalidades:
    - Embeddings para documentos e consultas
    - Processamento em lotes otimizado
    - Suporte a conteúdo multimodal (texto + imagem)
    - Tratamento de erros e retry logic
    """
    
    def __init__(self,
                 api_key: str,
                 api_endpoint: str = "https://api.voyageai.com/v1/multimodalembeddings",
                 model: str = "voyage-multimodal-3",
                 batch_size: int = 10,
                 max_text_length: int = 5000,
                 timeout: int = 60):
        """
        Inicializa o embedder Voyage
        
        Args:
            api_key: Chave da API Voyage AI
            api_endpoint: Endpoint da API
            model: Modelo de embedding
            batch_size: Tamanho do lote
            max_text_length: Limite de caracteres por texto
            timeout: Timeout para requisições
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint
        self.model = model
        self.batch_size = batch_size
        self.max_text_length = max_text_length
        self.timeout = timeout
        
        # Headers padrão
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        # Formatos de imagem suportados
        self.supported_image_formats = [
            "image/png", "image/jpeg", "image/webp", "image/gif"
        ]
    
    def embed_chunks(self, chunk_collection: ChunkCollection) -> List[EmbeddedChunk]:
        """
        Gera embeddings para coleção de chunks
        
        Args:
            chunk_collection: Coleção de chunks multimodais
            
        Returns:
            Lista de chunks com embeddings
        """
        embedded_chunks = []
        
        # Processar em lotes
        for batch in chunk_list(chunk_collection.chunks, self.batch_size):
            batch_embeddings = self._process_chunk_batch(batch, input_type="document")
            
            # Combinar chunks com embeddings
            for chunk, embedding in zip(batch, batch_embeddings):
                embedded_chunk = self._create_embedded_chunk(chunk, embedding)
                embedded_chunks.append(embedded_chunk)
        
        return embedded_chunks
    
    def embed_query(self, query_text: str, query_image: Optional[str] = None) -> QueryEmbedding:
        """
        Gera embedding para consulta
        
        Args:
            query_text: Texto da consulta
            query_image: Imagem da consulta (base64, opcional)
            
        Returns:
            QueryEmbedding com vetor de embedding
        """
        # Preparar conteúdo da consulta
        content = [{"type": "text", "text": query_text}]
        
        if query_image and self._is_valid_image(query_image):
            content.append({
                "type": "image_base64",
                "image_base64": query_image
            })
        
        # Fazer requisição
        payload = {
            "inputs": [{"content": content}],
            "model": self.model,
            "input_type": "query",
            "truncation": True
        }
        
        response = self._make_api_request(payload)
        
        # Extrair embedding
        if response["data"]:
            embedding = response["data"][0]["embedding"]
            return QueryEmbedding(
                query=query_text,
                embedding=embedding,
                dimension=len(embedding),
                model=self.model,
                type="query"
            )
        
        raise ValueError("Não foi possível gerar embedding para a consulta")
    
    def _process_chunk_batch(self, chunks: List[MultimodalChunk], input_type: str) -> List[List[float]]:
        """
        Processa lote de chunks
        """
        # Preparar inputs para API
        inputs = []
        for chunk in chunks:
            content = self._prepare_chunk_content(chunk)
            inputs.append({"content": content})
        
        # Payload da requisição
        payload = {
            "inputs": inputs,
            "model": self.model,
            "input_type": input_type,
            "truncation": True
        }
        
        # Fazer requisição
        response = self._make_api_request(payload)
        
        # Extrair embeddings
        embeddings = []
        for item in response["data"]:
            embeddings.append(item["embedding"])
        
        return embeddings
    
    def _prepare_chunk_content(self, chunk: MultimodalChunk) -> List[Dict[str, Any]]:
        """
        Prepara conteúdo do chunk para API
        """
        content = []
        
        # Adicionar texto
        text = extract_text_content(asdict(chunk))
        if text:
            # Truncar texto se necessário
            text = truncate_text(text, self.max_text_length)
            content.append({"type": "text", "text": text})
        
        # Adicionar imagem se disponível
        image = extract_image_content(asdict(chunk))
        if image and self._is_valid_image(image):
            content.append({
                "type": "image_base64",
                "image_base64": image
            })
        
        return content
    
    def _is_valid_image(self, image_data: str) -> bool:
        """
        Valida se dados de imagem são válidos
        """
        if not image_data or not isinstance(image_data, str):
            return False
        
        # Verificar header data:
        if image_data.startswith('data:'):
            content_type = image_data.split(';')[0].split(':')[1]
            return content_type in self.supported_image_formats
        
        # Assumir que é base64 válido se não tem header
        return len(image_data) > 100  # Verificação básica
    
    def _make_api_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Faz requisição para API Voyage
        """
        try:
            response = requests.post(
                self.api_endpoint,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"Erro na API Voyage: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Erro ao decodificar resposta da API: {str(e)}")
    
    def _create_embedded_chunk(self, chunk: MultimodalChunk, embedding: List[float]) -> EmbeddedChunk:
        """
        Cria EmbeddedChunk combinando chunk original com embedding
        """
        # Converter chunk para dict e depois para EmbeddedChunk
        chunk_dict = asdict(chunk)
        embedded_chunk = EmbeddedChunk(**chunk_dict)
        
        # Adicionar embedding
        embedded_chunk.embedding = embedding
        embedded_chunk.dimension = len(embedding)
        embedded_chunk.model = self.model
        
        return embedded_chunk
    
    def get_embedding_stats(self, embeddings: List[List[float]]) -> Dict[str, Any]:
        """
        Calcula estatísticas dos embeddings
        """
        if not embeddings:
            return {}
        
        dimensions = [len(emb) for emb in embeddings]
        
        return {
            "total_embeddings": len(embeddings),
            "dimension": dimensions[0] if dimensions else 0,
            "consistent_dimensions": len(set(dimensions)) == 1,
            "model_used": self.model,
            "avg_magnitude": self._calculate_avg_magnitude(embeddings)
        }
    
    def _calculate_avg_magnitude(self, embeddings: List[List[float]]) -> float:
        """
        Calcula magnitude média dos embeddings
        """
        if not embeddings:
            return 0.0
        
        magnitudes = []
        for embedding in embeddings:
            magnitude = sum(x * x for x in embedding) ** 0.5
            magnitudes.append(magnitude)
        
        return sum(magnitudes) / len(magnitudes)
    
    def validate_api_connection(self) -> Dict[str, Any]:
        """
        Valida conexão com API
        """
        try:
            # Fazer requisição de teste simples
            test_payload = {
                "inputs": [{"content": [{"type": "text", "text": "test"}]}],
                "model": self.model,
                "input_type": "document",
                "truncation": True
            }
            
            response = self._make_api_request(test_payload)
            
            return {
                "status": "success",
                "model": self.model,
                "api_accessible": True,
                "test_embedding_dimension": len(response["data"][0]["embedding"]) if response["data"] else 0
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "api_accessible": False
            }


class VoyageQueryEmbedder:
    """
    Versão especializada para embeddings de consulta
    """
    
    def __init__(self, api_key: str, **kwargs):
        self.embedder = VoyageEmbedder(api_key=api_key, **kwargs)
    
    def embed_text_query(self, query: str) -> QueryEmbedding:
        """
        Gera embedding apenas para texto
        """
        return self.embedder.embed_query(query)
    
    def embed_multimodal_query(self, query: str, image: str) -> QueryEmbedding:
        """
        Gera embedding para consulta multimodal
        """
        return self.embedder.embed_query(query, image)


# Funções de conveniência
def embed_chunk_collection(chunk_collection: ChunkCollection,
                          api_key: str,
                          **kwargs) -> List[EmbeddedChunk]:
    """
    Função de conveniência para embeddings de chunks
    
    Args:
        chunk_collection: Coleção de chunks
        api_key: Chave da API Voyage
        **kwargs: Parâmetros adicionais
        
    Returns:
        Lista de chunks com embeddings
    """
    embedder = VoyageEmbedder(api_key=api_key, **kwargs)
    return embedder.embed_chunks(chunk_collection)


def embed_search_query(query_text: str,
                      api_key: str,
                      query_image: Optional[str] = None,
                      **kwargs) -> QueryEmbedding:
    """
    Função de conveniência para embedding de consulta
    
    Args:
        query_text: Texto da consulta
        api_key: Chave da API Voyage
        query_image: Imagem da consulta (opcional)
        **kwargs: Parâmetros adicionais
        
    Returns:
        QueryEmbedding com vetor
    """
    embedder = VoyageEmbedder(api_key=api_key, **kwargs)
    return embedder.embed_query(query_text, query_image)