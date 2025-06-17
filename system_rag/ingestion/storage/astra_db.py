"""
Astra DB Optimized Inserter

Insere documentos no Astra DB com otimizações para evitar limites de tamanho.
"""
import requests
import json
from typing import List, Dict, Any, Optional, Generator
from dataclasses import asdict

from ...models.data_models import EmbeddedChunk, InsertionResult, ProcessingStatus
from ...utils.helpers import (
    clean_base64_from_dict, truncate_text, safe_get_nested,
    chunk_list
)
from ...config.settings import settings


class AstraDBInserter:
    """
    Componente para inserção otimizada no Astra DB
    
    Funcionalidades:
    - Inserção em lotes otimizados
    - Limpeza automática de campos base64
    - Truncamento de texto para evitar limites
    - Substituição de documentos existentes
    """
    
    def __init__(self,
                 api_endpoint: str,
                 auth_token: str,
                 keyspace: str = "default_keyspace",
                 collection_name: str = "agenciawow",
                 replace_existing: bool = True,
                 batch_size: int = 50,
                 max_text_length: int = 7000,
                 timeout: int = 60):
        """
        Inicializa o inserter Astra DB
        
        Args:
            api_endpoint: Endpoint base do Astra DB
            auth_token: Token de aplicação Astra (AstraCS...)
            keyspace: Nome do keyspace
            collection_name: Nome da coleção
            replace_existing: Substituir documentos existentes
            batch_size: Documentos por lote (máx: 100)
            max_text_length: Tamanho máximo de campos texto
            timeout: Timeout para requisições
        """
        self.api_endpoint = api_endpoint.rstrip('/')
        self.auth_token = auth_token
        self.keyspace = keyspace
        self.collection_name = collection_name
        self.replace_existing = replace_existing
        self.batch_size = min(batch_size, 100)  # Astra DB limita a 100
        self.max_text_length = max_text_length
        self.timeout = timeout
        
        # URL completa da API
        self.collection_url = f"{self.api_endpoint}/api/json/v1/{self.keyspace}/{self.collection_name}"
        
        # Headers padrão (conforme documentação oficial)
        self.headers = {
            "Token": self.auth_token,
            "Content-Type": "application/json"
        }
    
    def insert_chunks(self, embedded_chunks: List[EmbeddedChunk]) -> Dict[str, Any]:
        """
        Insere chunks no Astra DB
        
        Args:
            embedded_chunks: Lista de chunks com embeddings
            
        Returns:
            Resultado da inserção
        """
        if not embedded_chunks:
            return self._create_empty_result()
        
        # Preparar documentos para inserção
        prepared_docs = self._prepare_documents(embedded_chunks)
        
        # Substituir documentos existentes se configurado
        replacement_result = {}
        if self.replace_existing:
            replacement_result = self._replace_existing_documents(prepared_docs)
        
        # Inserir em lotes
        insertion_result = self._insert_in_batches(prepared_docs)
        
        return {
            "status": "completed",
            "insertion_result": insertion_result,
            "replacement_result": replacement_result,
            "summary": {
                "total_documents_prepared": len(prepared_docs),
                "total_documents_inserted": insertion_result.inserted_count,
                "success_rate": f"{(insertion_result.inserted_count / len(prepared_docs) * 100):.1f}%" if prepared_docs else "100.0%",
                "total_data_size_kb": self._calculate_total_size_kb(prepared_docs),
                "uses_image_urls": self._uses_image_urls(prepared_docs),
                "optimization": "enabled"
            }
        }
    
    def _prepare_documents(self, embedded_chunks: List[EmbeddedChunk]) -> List[Dict[str, Any]]:
        """
        Prepara documentos para inserção otimizada
        """
        prepared_docs = []
        
        for chunk in embedded_chunks:
            # Converter para dict
            chunk_dict = asdict(chunk)
            
            # Limpeza de base64 (crítico para Astra DB)
            cleaned_dict = clean_base64_from_dict(chunk_dict)
            
            # Criar documento otimizado
            astra_doc = {
                "_id": chunk.chunk_id,
                "content": self._truncate_text_field(chunk.content),
                "$vector": chunk.embedding,
                "document_name": chunk.document_name,
                "page_number": chunk.page_number,
                "char_count": chunk.char_count,
                "source": chunk.source,
                "merge_strategy": chunk.merge_strategy,
                "model": chunk.model,
                "dimension": chunk.dimension
            }
            
            # Adicionar campos de imagem (URLs, não base64)
            if hasattr(chunk, 'image_url') and chunk.image_url:
                astra_doc["image_url"] = chunk.image_url
            if hasattr(chunk, 'image_filename_r2') and chunk.image_filename_r2:
                astra_doc["image_filename_r2"] = chunk.image_filename_r2
            if hasattr(chunk, 'image_size_bytes') and chunk.image_size_bytes:
                astra_doc["image_size_bytes"] = chunk.image_size_bytes
            
            # Adicionar metadados otimizados
            if chunk.metadata:
                cleaned_metadata = clean_base64_from_dict(chunk.metadata)
                # Garantir document_name em metadata
                cleaned_metadata["document_name"] = chunk.document_name
                astra_doc["metadata"] = cleaned_metadata
            else:
                astra_doc["metadata"] = {"document_name": chunk.document_name}
            
            prepared_docs.append(astra_doc)
        
        return prepared_docs
    
    def _truncate_text_field(self, text: str) -> str:
        """
        Trunca campo de texto se necessário
        """
        if not text:
            return ""
        
        return truncate_text(text, self.max_text_length)
    
    def _replace_existing_documents(self, prepared_docs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Remove documentos existentes antes da inserção
        """
        if not prepared_docs:
            return {"total_deleted": 0, "sources_processed": []}
        
        # Obter lista de document_names únicos
        document_sources = set()
        for doc in prepared_docs:
            if "document_name" in doc:
                document_sources.add(doc["document_name"])
            # Também verificar em metadata
            if "metadata" in doc and "document_name" in doc["metadata"]:
                document_sources.add(doc["metadata"]["document_name"])
        
        total_deleted = 0
        
        # Deletar por cada fonte
        for source in document_sources:
            deleted_count = self._delete_by_source(source)
            total_deleted += deleted_count
        
        return {
            "total_deleted": total_deleted,
            "sources_processed": list(document_sources)
        }
    
    def _delete_by_source(self, source: str) -> int:
        """
        Deleta documentos por fonte específica
        """
        delete_filters = [
            {"document_name": source},
            {"metadata.document_name": source}
        ]
        
        total_deleted = 0
        
        for filter_criteria in delete_filters:
            try:
                payload = {
                    "deleteMany": {
                        "filter": filter_criteria
                    }
                }
                
                response = requests.post(
                    self.collection_url,
                    headers=self.headers,
                    json=payload,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    deleted_count = result.get("status", {}).get("deletedCount", 0)
                    total_deleted += deleted_count
                
            except Exception:
                continue  # Continuar com próximo filtro se falhar
        
        return total_deleted
    
    def _insert_in_batches(self, prepared_docs: List[Dict[str, Any]]) -> InsertionResult:
        """
        Insere documentos em lotes
        """
        inserted_ids = []
        total_batches = 0
        
        # Processar em lotes
        for batch in chunk_list(prepared_docs, self.batch_size):
            batch_list = list(batch)  # Converter generator para lista
            batch_result = self._insert_batch(batch_list)
            
            if batch_result:
                inserted_ids.extend(batch_result)
            
            total_batches += 1
        
        return InsertionResult(
            inserted_count=len(inserted_ids),
            inserted_ids=inserted_ids,
            total_batches=total_batches,
            success=len(inserted_ids) > 0
        )
    
    def _insert_batch(self, batch_docs: List[Dict[str, Any]]) -> Optional[List[str]]:
        """
        Insere um lote de documentos
        """
        try:
            payload = {
                "insertMany": {
                    "documents": batch_docs
                }
            }
            
            # Log de debug (sem dados sensíveis)
            batch_size_kb = len(json.dumps(payload).encode('utf-8')) / 1024
            logger.info(f"Inserindo lote: {len(batch_docs)} documentos ({batch_size_kb:.1f}KB)")
            
            # Log sample document structure (sem dados sensíveis)
            if batch_docs:
                sample_doc = batch_docs[0].copy()
                if "$vector" in sample_doc:
                    sample_doc["$vector"] = f"[{len(sample_doc['$vector'])} dimensions]"
                logger.debug(f"Estrutura do documento: {list(sample_doc.keys())}")
            
            response = requests.post(
                self.collection_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            logger.debug(f"Status da resposta: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                logger.debug(f"Resposta JSON recebida: {list(result.keys())}")
                
                # Verificar se há erros na resposta
                if "errors" in result and result["errors"]:
                    logger.error(f"Erros do Astra DB: {result['errors']}")
                    return None
                
                status = result.get("status", {})
                inserted_ids = status.get("insertedIds", [])
                logger.info(f"IDs inseridos: {len(inserted_ids)}")
                return inserted_ids
            else:
                logger.error(f"Erro HTTP {response.status_code}: {response.text[:200]}...")  # Trunca resposta longa
                return None
                
        except Exception as e:
            logger.error(f"Erro na inserção: {e}")
            return None
    
    def _calculate_total_size_kb(self, docs: List[Dict[str, Any]]) -> float:
        """
        Calcula tamanho total dos dados em KB
        """
        try:
            total_size = len(json.dumps(docs).encode('utf-8'))
            return round(total_size / 1024, 2)
        except:
            return 0.0
    
    def _uses_image_urls(self, docs: List[Dict[str, Any]]) -> bool:
        """
        Verifica se documentos usam URLs de imagem
        """
        for doc in docs:
            if "image_url" in doc and doc["image_url"]:
                return True
        return False
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        Cria resultado vazio
        """
        return {
            "status": "completed",
            "insertion_result": InsertionResult(
                inserted_count=0,
                inserted_ids=[],
                total_batches=0,
                success=True
            ),
            "replacement_result": {
                "total_deleted": 0,
                "sources_processed": []
            },
            "summary": {
                "total_documents_prepared": 0,
                "total_documents_inserted": 0,
                "success_rate": "100.0%",
                "total_data_size_kb": 0.0,
                "uses_image_urls": False,
                "optimization": "enabled"
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com Astra DB
        """
        try:
            # Fazer uma consulta simples
            payload = {
                "find": {
                    "options": {"limit": 1}
                }
            }
            
            response = requests.post(
                self.collection_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Conexão com Astra DB estabelecida",
                    "collection_accessible": True,
                    "keyspace": self.keyspace,
                    "collection": self.collection_name
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro na conexão: {response.status_code}",
                    "collection_accessible": False
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na conexão: {str(e)}",
                "collection_accessible": False
            }
    
    def count_documents(self, filter_criteria: Optional[Dict[str, Any]] = None) -> int:
        """
        Conta documentos na coleção
        """
        try:
            payload = {"countDocuments": {}}
            if filter_criteria:
                payload["countDocuments"]["filter"] = filter_criteria
            
            response = requests.post(
                self.collection_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("status", {}).get("count", 0)
            
        except Exception:
            pass
        
        return 0
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas da coleção
        """
        try:
            total_docs = self.count_documents()
            
            # Tentar obter amostra de documentos
            payload = {
                "find": {
                    "options": {"limit": 5}
                }
            }
            
            response = requests.post(
                self.collection_url,
                headers=self.headers,
                json=payload,
                timeout=self.timeout
            )
            
            sample_docs = []
            if response.status_code == 200:
                result = response.json()
                sample_docs = result.get("data", {}).get("documents", [])
            
            return {
                "total_documents": total_docs,
                "collection_name": self.collection_name,
                "keyspace": self.keyspace,
                "sample_documents": len(sample_docs),
                "has_vector_data": any("$vector" in doc for doc in sample_docs)
            }
            
        except Exception as e:
            return {
                "error": str(e),
                "total_documents": 0
            }


# Funções de conveniência
def insert_to_astra_db(embedded_chunks: List[EmbeddedChunk],
                      api_endpoint: str,
                      auth_token: str,
                      collection_name: str,
                      **kwargs) -> Dict[str, Any]:
    """
    Função de conveniência para inserção no Astra DB
    
    Args:
        embedded_chunks: Lista de chunks com embeddings
        api_endpoint: Endpoint da API Astra
        auth_token: Token de autenticação
        collection_name: Nome da coleção
        **kwargs: Parâmetros adicionais
        
    Returns:
        Resultado da inserção
    """
    inserter = AstraDBInserter(
        api_endpoint=api_endpoint,
        auth_token=auth_token,
        collection_name=collection_name,
        **kwargs
    )
    return inserter.insert_chunks(embedded_chunks)


def test_astra_connection(api_endpoint: str,
                         auth_token: str,
                         collection_name: str,
                         **kwargs) -> Dict[str, Any]:
    """
    Função de conveniência para testar conexão Astra DB
    
    Args:
        api_endpoint: Endpoint da API Astra
        auth_token: Token de autenticação
        collection_name: Nome da coleção
        **kwargs: Parâmetros adicionais
        
    Returns:
        Resultado do teste
    """
    inserter = AstraDBInserter(
        api_endpoint=api_endpoint,
        auth_token=auth_token,
        collection_name=collection_name,
        **kwargs
    )
    return inserter.test_connection()