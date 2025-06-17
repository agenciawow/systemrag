"""
Cloudflare R2 Image Uploader

Faz upload de imagens base64 para Cloudflare R2 e substitui por URLs públicas.
"""
import requests
from typing import List, Dict, Any, Optional
from dataclasses import asdict

from ...models.data_models import EmbeddedChunk, UploadResult, ProcessingStatus
from ...utils.helpers import (
    decode_base64_image, clean_filename, extract_document_name,
    generate_unique_filename, safe_get_nested
)
from ...config.settings import settings


class CloudflareR2Uploader:
    """
    Componente para upload de imagens para Cloudflare R2
    
    Funcionalidades:
    - Upload de imagens base64 para R2
    - Geração de URLs públicas
    - Substituição de base64 por URLs
    - Limpeza de arquivos existentes
    """
    
    def __init__(self,
                 r2_endpoint: str,
                 auth_token: str,
                 timeout: int = 60,
                 replace_existing: bool = True,
                 keep_original_base64: bool = False):
        """
        Inicializa o uploader R2
        
        Args:
            r2_endpoint: Endpoint da API R2
            auth_token: Token de autenticação Bearer
            timeout: Timeout para requisições
            replace_existing: Deletar imagens existentes antes
            keep_original_base64: Manter base64 original
        """
        self.r2_endpoint = r2_endpoint.rstrip('/')
        self.auth_token = auth_token
        self.timeout = timeout
        self.replace_existing = replace_existing
        self.keep_original_base64 = keep_original_base64
        
        # Headers padrão
        self.headers = {
            "Authorization": f"Bearer {self.auth_token}"
        }
    
    def upload_chunk_images(self, 
                           embedded_chunks: List[EmbeddedChunk],
                           image_field: str = "image_base64",
                           filename_field: str = "image_filename",
                           doc_source_field: str = "document_name") -> Dict[str, Any]:
        """
        Faz upload das imagens dos chunks
        
        Args:
            embedded_chunks: Lista de chunks com embeddings
            image_field: Campo com imagem base64
            filename_field: Campo com nome do arquivo
            doc_source_field: Campo para gerar prefixos únicos
            
        Returns:
            Resultado do upload com estatísticas
        """
        if not embedded_chunks:
            return self._create_empty_result()
        
        # Extrair nome do documento
        document_name = self._get_document_name(embedded_chunks, doc_source_field)
        
        # Deletar existentes se configurado
        deletion_result = {}
        if self.replace_existing and document_name:
            deletion_result = self._delete_existing_images(document_name)
        
        # Processar uploads
        uploaded_chunks = []
        total_images_found = 0
        total_images_uploaded = 0
        
        for chunk in embedded_chunks:
            chunk_dict = asdict(chunk)
            
            # Verificar se tem imagem
            if image_field in chunk_dict and chunk_dict[image_field]:
                total_images_found += 1
                
                # Fazer upload
                upload_result = self._upload_single_image(
                    chunk_dict, image_field, filename_field, document_name
                )
                
                if upload_result:
                    total_images_uploaded += 1
                    # Atualizar chunk com URL
                    updated_chunk = self._update_chunk_with_url(chunk, upload_result)
                    uploaded_chunks.append(updated_chunk)
                else:
                    uploaded_chunks.append(chunk)
            else:
                uploaded_chunks.append(chunk)
        
        # Calcular taxa de sucesso
        success_rate = (total_images_uploaded / total_images_found * 100) if total_images_found > 0 else 100
        
        return {
            "documents": uploaded_chunks,
            "status": "completed",
            "summary": {
                "total_documents": len(embedded_chunks),
                "total_images_found": total_images_found,
                "total_images_uploaded": total_images_uploaded,
                "success_rate": f"{success_rate:.1f}%",
                "r2_endpoint": self.r2_endpoint,
                "document_name_used": document_name
            },
            "deletion_result": deletion_result
        }
    
    def _get_document_name(self, chunks: List[EmbeddedChunk], doc_source_field: str) -> str:
        """
        Extrai nome do documento dos chunks
        """
        if not chunks:
            return "unknown_document"
        
        # Tentar extrair do primeiro chunk
        first_chunk = asdict(chunks[0])
        
        # Tentar campo direto
        if doc_source_field in first_chunk and first_chunk[doc_source_field]:
            doc_name = first_chunk[doc_source_field]
        # Tentar em metadata
        elif "metadata" in first_chunk and first_chunk["metadata"]:
            doc_name = safe_get_nested(first_chunk["metadata"], doc_source_field, "")
        else:
            doc_name = "unknown_document"
        
        # Limpar nome do documento
        if doc_name:
            doc_name = extract_document_name(doc_name)
            doc_name = clean_filename(doc_name)
        
        return doc_name or "unknown_document"
    
    def _delete_existing_images(self, document_name: str) -> Dict[str, Any]:
        """
        Deleta imagens existentes do documento
        """
        try:
            delete_url = f"{self.r2_endpoint}/delete-doc/{document_name}"
            
            response = requests.delete(
                delete_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": f"Imagens do documento '{document_name}' deletadas",
                    "deleted_count": response.json().get("deleted_count", 0)
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro ao deletar: {response.status_code}",
                    "deleted_count": 0
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na deleção: {str(e)}",
                "deleted_count": 0
            }
    
    def _upload_single_image(self, 
                            chunk_dict: Dict[str, Any],
                            image_field: str,
                            filename_field: str,
                            document_name: str) -> Optional[UploadResult]:
        """
        Faz upload de uma única imagem
        """
        try:
            # Extrair dados da imagem
            image_base64 = chunk_dict[image_field]
            original_filename = chunk_dict.get(filename_field, "image.jpg")
            page_num = chunk_dict.get("page_number", 1)
            
            # Decodificar base64
            image_bytes = decode_base64_image(image_base64)
            
            # Gerar nome único
            unique_filename = generate_unique_filename(
                document_name, page_num, original_filename
            )
            
            # Fazer upload
            upload_url = f"{self.r2_endpoint}/upload/{unique_filename}"
            
            upload_headers = {
                **self.headers,
                "Content-Type": "application/octet-stream"
            }
            
            response = requests.put(
                upload_url,
                headers=upload_headers,
                data=image_bytes,
                timeout=self.timeout
            )
            
            if response.status_code in [200, 201]:
                # Gerar URL pública
                public_url = f"{self.r2_endpoint}/file/{unique_filename}"
                
                return UploadResult(
                    image_url=public_url,
                    image_filename_r2=unique_filename,
                    image_size_original=len(image_base64),
                    image_size_bytes=len(image_bytes),
                    document_name_used=document_name,
                    prefix_used=document_name,
                    success=True
                )
            else:
                return None
                
        except Exception:
            return None
    
    def _update_chunk_with_url(self, 
                              original_chunk: EmbeddedChunk,
                              upload_result: UploadResult) -> EmbeddedChunk:
        """
        Atualiza chunk com URL da imagem
        """
        # Criar cópia do chunk
        chunk_dict = asdict(original_chunk)
        updated_chunk = EmbeddedChunk(**chunk_dict)
        
        # Adicionar informações do upload
        updated_chunk.image_url = upload_result.image_url
        updated_chunk.image_filename_r2 = upload_result.image_filename_r2
        updated_chunk.image_size_original = upload_result.image_size_original
        updated_chunk.image_size_bytes = upload_result.image_size_bytes
        updated_chunk.document_name_used = upload_result.document_name_used
        updated_chunk.prefix_used = upload_result.prefix_used
        
        # Remover base64 se configurado
        if not self.keep_original_base64:
            updated_chunk.image_base64 = None
        
        return updated_chunk
    
    def _create_empty_result(self) -> Dict[str, Any]:
        """
        Cria resultado vazio para casos sem chunks
        """
        return {
            "documents": [],
            "status": "completed",
            "summary": {
                "total_documents": 0,
                "total_images_found": 0,
                "total_images_uploaded": 0,
                "success_rate": "100.0%",
                "r2_endpoint": self.r2_endpoint
            }
        }
    
    def test_connection(self) -> Dict[str, Any]:
        """
        Testa conexão com API R2
        """
        try:
            # Tentar obter estatísticas do bucket
            stats_url = f"{self.r2_endpoint}/stats"
            
            response = requests.get(
                stats_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "message": "Conexão com R2 estabelecida",
                    "stats": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro na conexão: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na conexão: {str(e)}"
            }
    
    def list_files(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        """
        Lista arquivos no bucket
        """
        try:
            if prefix:
                list_url = f"{self.r2_endpoint}/list/{prefix}"
            else:
                list_url = f"{self.r2_endpoint}/list"
            
            response = requests.get(
                list_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "success": True,
                    "files": response.json()
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro ao listar arquivos: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro ao listar arquivos: {str(e)}"
            }
    
    def delete_by_prefix(self, prefix: str) -> Dict[str, Any]:
        """
        Deleta arquivos por prefixo
        """
        try:
            delete_url = f"{self.r2_endpoint}/delete-doc/{prefix}"
            
            response = requests.delete(
                delete_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                return {
                    "success": True,
                    "deleted_count": result.get("deleted_count", 0),
                    "message": f"Arquivos com prefixo '{prefix}' deletados"
                }
            else:
                return {
                    "success": False,
                    "message": f"Erro na deleção: {response.status_code}"
                }
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Erro na deleção: {str(e)}"
            }


# Funções de conveniência
def upload_images_to_r2(embedded_chunks: List[EmbeddedChunk],
                       r2_endpoint: str,
                       auth_token: str,
                       **kwargs) -> Dict[str, Any]:
    """
    Função de conveniência para upload de imagens
    
    Args:
        embedded_chunks: Lista de chunks com embeddings
        r2_endpoint: Endpoint da API R2
        auth_token: Token de autenticação
        **kwargs: Parâmetros adicionais
        
    Returns:
        Resultado do upload
    """
    uploader = CloudflareR2Uploader(
        r2_endpoint=r2_endpoint,
        auth_token=auth_token,
        **kwargs
    )
    return uploader.upload_chunk_images(embedded_chunks)


def test_r2_connection(r2_endpoint: str, auth_token: str) -> Dict[str, Any]:
    """
    Função de conveniência para testar conexão R2
    
    Args:
        r2_endpoint: Endpoint da API R2
        auth_token: Token de autenticação
        
    Returns:
        Resultado do teste
    """
    uploader = CloudflareR2Uploader(
        r2_endpoint=r2_endpoint,
        auth_token=auth_token
    )
    return uploader.test_connection()