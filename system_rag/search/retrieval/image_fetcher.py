"""
Buscador de Imagens do Cloudflare R2

Busca e recupera imagens armazenadas no R2 baseado em URLs.
"""
import logging
import base64
import requests
from typing import Optional, Dict, Any, List
from PIL import Image
from io import BytesIO

from ...models.data_models import SearchResult, ProcessingStatus
from ...config.settings import settings

logger = logging.getLogger(__name__)


class ImageFetcher:
    """
    Buscador de imagens do Cloudflare R2
    
    Funcionalidades:
    - Download de imagens por URL
    - Conversão para base64
    - Cache de imagens
    - Validação de formato
    """
    
    def __init__(self,
                 r2_endpoint: str = None,
                 auth_token: str = None,
                 timeout: int = 30,
                 cache_enabled: bool = True,
                 max_cache_size: int = 100):
        """
        Inicializa o buscador de imagens
        
        Args:
            r2_endpoint: Endpoint do R2
            auth_token: Token de autenticação
            timeout: Timeout para requisições
            cache_enabled: Habilitar cache
            max_cache_size: Tamanho máximo do cache
        """
        self.r2_endpoint = (r2_endpoint or settings.api.r2_endpoint).rstrip('/')
        self.auth_token = auth_token or settings.api.r2_auth_token
        self.timeout = timeout
        self.cache_enabled = cache_enabled
        self.max_cache_size = max_cache_size
        
        # Cache de imagens
        self.image_cache: Dict[str, str] = {}
        
        # Headers para requisições
        self.headers = {}
        if self.auth_token:
            self.headers["Authorization"] = f"Bearer {self.auth_token}"
    
    def fetch_image_as_base64(self, image_url: str) -> Optional[str]:
        """
        Busca imagem e retorna como base64
        
        Args:
            image_url: URL da imagem
            
        Returns:
            Imagem em base64 ou None se erro
        """
        try:
            # Verificar cache
            if self.cache_enabled and image_url in self.image_cache:
                logger.debug(f"Cache hit para imagem: {image_url}")
                return self.image_cache[image_url]
            
            logger.debug(f"Fazendo download da imagem: {image_url}")
            
            # Fazer download
            response = requests.get(
                image_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                logger.warning(f"Erro ao baixar imagem: {response.status_code}")
                return None
            
            # Validar se é uma imagem válida
            try:
                image = Image.open(BytesIO(response.content))
                image.verify()  # Verifica se a imagem é válida
            except Exception as img_error:
                logger.warning(f"Arquivo não é uma imagem válida: {img_error}")
                return None
            
            # Converter para base64
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            
            # Adicionar ao cache
            if self.cache_enabled:
                self._cache_image(image_url, image_base64)
            
            logger.debug(f"Imagem baixada com sucesso: {len(image_base64)} chars")
            return image_base64
            
        except Exception as e:
            logger.error(f"Erro ao buscar imagem {image_url}: {e}")
            return None
    
    def fetch_multiple_images(self, image_urls: List[str]) -> Dict[str, Optional[str]]:
        """
        Busca múltiplas imagens
        
        Args:
            image_urls: Lista de URLs das imagens
            
        Returns:
            Dicionário {url: base64} ou {url: None} se erro
        """
        results = {}
        
        for url in image_urls:
            if url:
                results[url] = self.fetch_image_as_base64(url)
            else:
                results[url] = None
        
        success_count = sum(1 for v in results.values() if v is not None)
        logger.info(f"Imagens baixadas: {success_count}/{len(image_urls)}")
        
        return results
    
    def enrich_search_results(self, search_results: List[SearchResult]) -> List[SearchResult]:
        """
        Enriquece resultados de busca com imagens do R2
        
        Args:
            search_results: Lista de resultados de busca
            
        Returns:
            Resultados enriquecidos com imagens
        """
        enriched_results = []
        
        for result in search_results:
            enriched_result = result
            
            # Se tem URL da imagem mas não tem base64, buscar
            if result.image_url and not result.image_base64:
                logger.debug(f"Buscando imagem para documento: {result.document_name}")
                
                image_base64 = self.fetch_image_as_base64(result.image_url)
                if image_base64:
                    # Criar nova instância com imagem
                    enriched_result = SearchResult(
                        document_id=result.document_id,
                        content=result.content,
                        document_name=result.document_name,
                        page_number=result.page_number,
                        similarity=result.similarity,
                        image_url=result.image_url,
                        image_filename_r2=result.image_filename_r2,
                        image_base64=image_base64,
                        has_image=True,
                        metadata=result.metadata
                    )
            
            enriched_results.append(enriched_result)
        
        return enriched_results
    
    def _cache_image(self, url: str, image_base64: str):
        """Adiciona imagem ao cache com controle de tamanho"""
        if len(self.image_cache) >= self.max_cache_size:
            # Remove o item mais antigo
            oldest_url = next(iter(self.image_cache))
            del self.image_cache[oldest_url]
            logger.debug(f"Cache: removido {oldest_url}")
        
        self.image_cache[url] = image_base64
        logger.debug(f"Cache: adicionado {url}")
    
    def clear_cache(self):
        """Limpa o cache de imagens"""
        cache_size = len(self.image_cache)
        self.image_cache.clear()
        logger.info(f"Cache limpo: {cache_size} imagens removidas")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do cache
        
        Returns:
            Estatísticas do cache
        """
        total_size = sum(len(img) for img in self.image_cache.values())
        
        return {
            "cached_images": len(self.image_cache),
            "max_cache_size": self.max_cache_size,
            "total_size_chars": total_size,
            "cache_enabled": self.cache_enabled
        }
    
    def test_connection(self) -> ProcessingStatus:
        """
        Testa conexão com o R2
        
        Returns:
            Status da conexão
        """
        try:
            # Tentar acessar endpoint de estatísticas
            if self.r2_endpoint:
                stats_url = f"{self.r2_endpoint}/stats"
                
                response = requests.get(
                    stats_url,
                    headers=self.headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return ProcessingStatus(
                        success=True,
                        message="Conexão com R2 estabelecida",
                        details=response.json()
                    )
                else:
                    return ProcessingStatus(
                        success=False,
                        message=f"Erro na conexão com R2: {response.status_code}",
                        details={"status_code": response.status_code}
                    )
            else:
                return ProcessingStatus(
                    success=False,
                    message="Endpoint R2 não configurado"
                )
                
        except Exception as e:
            return ProcessingStatus(
                success=False,
                message=f"Erro ao testar conexão: {str(e)}",
                details={"error": str(e)}
            )
    
    def get_image_info(self, image_url: str) -> Dict[str, Any]:
        """
        Obtém informações sobre uma imagem
        
        Args:
            image_url: URL da imagem
            
        Returns:
            Informações da imagem
        """
        try:
            response = requests.head(
                image_url,
                headers=self.headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                return {
                    "url": image_url,
                    "content_type": response.headers.get("Content-Type", "unknown"),
                    "content_length": int(response.headers.get("Content-Length", 0)),
                    "last_modified": response.headers.get("Last-Modified"),
                    "available": True
                }
            else:
                return {
                    "url": image_url,
                    "available": False,
                    "status_code": response.status_code
                }
                
        except Exception as e:
            return {
                "url": image_url,
                "available": False,
                "error": str(e)
            }


def fetch_image_from_r2(image_url: str,
                       r2_endpoint: str = None,
                       auth_token: str = None) -> Optional[str]:
    """
    Função de conveniência para buscar uma imagem do R2
    
    Args:
        image_url: URL da imagem
        r2_endpoint: Endpoint do R2
        auth_token: Token de autenticação
        
    Returns:
        Imagem em base64 ou None
    """
    fetcher = ImageFetcher(r2_endpoint, auth_token)
    return fetcher.fetch_image_as_base64(image_url)


def enrich_results_with_images(search_results: List[SearchResult],
                              **kwargs) -> List[SearchResult]:
    """
    Função de conveniência para enriquecer resultados com imagens
    
    Args:
        search_results: Resultados de busca
        **kwargs: Argumentos para ImageFetcher
        
    Returns:
        Resultados enriquecidos
    """
    fetcher = ImageFetcher(**kwargs)
    return fetcher.enrich_search_results(search_results)