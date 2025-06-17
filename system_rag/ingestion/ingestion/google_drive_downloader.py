"""
Google Drive Downloader

Baixa arquivos do Google Drive convertendo URLs de compartilhamento em downloads diretos.
"""
import requests
import base64
import os
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from ...models.data_models import FileInfo, ProcessingStatus
from ...utils.helpers import (
    extract_google_drive_id, 
    convert_to_direct_download_url,
    format_file_size,
    encode_image_to_base64
)
from ...config.settings import settings


class GoogleDriveDownloader:
    """
    Componente para download de arquivos do Google Drive
    
    Funcionalidades:
    - Converte URLs de compartilhamento para download direto
    - Suporta múltiplos formatos de URL
    - Download para arquivo local ou base64
    - Validação de tamanho e timeout
    """
    
    def __init__(self,
                 timeout: int = 30,
                 validate_ssl: bool = True,
                 silent_errors: bool = False,
                 max_file_size_mb: int = 100):
        """
        Inicializa o downloader
        
        Args:
            timeout: Timeout em segundos para downloads
            validate_ssl: Validar certificados SSL
            silent_errors: Não lançar exceções em erros
            max_file_size_mb: Tamanho máximo em MB
        """
        self.timeout = timeout
        self.validate_ssl = validate_ssl
        self.silent_errors = silent_errors
        self.max_file_size_mb = max_file_size_mb
        self.max_file_size_bytes = max_file_size_mb * 1024 * 1024
        
        # Configurar sessão HTTP
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
    
    def download_files(self, 
                      urls: List[str], 
                      save_directory: Optional[str] = None) -> List[FileInfo]:
        """
        Baixa múltiplos arquivos do Google Drive
        
        Args:
            urls: Lista de URLs do Google Drive
            save_directory: Diretório para salvar (None = retorna base64)
            
        Returns:
            Lista de FileInfo com resultados dos downloads
        """
        results = []
        
        for url in urls:
            try:
                result = self._download_single_file(url, save_directory)
                results.append(result)
            except Exception as e:
                error_result = FileInfo(
                    filename="unknown",
                    original_url=url,
                    download_success=False,
                    error_message=str(e)
                )
                results.append(error_result)
                
                if not self.silent_errors:
                    raise
        
        return results
    
    def _download_single_file(self, 
                             url: str, 
                             save_directory: Optional[str] = None) -> FileInfo:
        """
        Baixa um único arquivo
        """
        # Extrair ID do Google Drive
        file_id = extract_google_drive_id(url)
        if not file_id:
            raise ValueError(f"Não foi possível extrair ID do Google Drive da URL: {url}")
        
        # Converter para URL de download direto
        direct_url = convert_to_direct_download_url(url)
        if not direct_url:
            raise ValueError(f"Não foi possível converter URL para download direto: {url}")
        
        # Fazer download
        response = self.session.get(
            direct_url,
            timeout=self.timeout,
            verify=self.validate_ssl,
            stream=True
        )
        response.raise_for_status()
        
        # Verificar tamanho do arquivo
        content_length = response.headers.get('content-length')
        if content_length and int(content_length) > self.max_file_size_bytes:
            raise ValueError(f"Arquivo muito grande: {format_file_size(int(content_length))}")
        
        # Obter nome do arquivo
        filename = self._extract_filename_from_response(response, file_id)
        
        # Ler conteúdo
        content = b''
        total_size = 0
        
        for chunk in response.iter_content(chunk_size=8192):
            if chunk:
                content += chunk
                total_size += len(chunk)
                
                # Verificar tamanho durante download
                if total_size > self.max_file_size_bytes:
                    raise ValueError(f"Arquivo excede tamanho máximo: {format_file_size(total_size)}")
        
        # Criar FileInfo
        file_info = FileInfo(
            filename=filename,
            original_url=url,
            direct_url=direct_url,
            size=total_size,
            size_mb=round(total_size / (1024 * 1024), 2),
            download_success=True
        )
        
        # Salvar ou converter para base64
        if save_directory:
            file_info.local_path = self._save_to_file(content, filename, save_directory)
        else:
            file_info.content_base64 = self._encode_to_base64(content, filename)
        
        return file_info
    
    def _extract_filename_from_response(self, response: requests.Response, file_id: str) -> str:
        """
        Extrai nome do arquivo da resposta HTTP
        """
        # Tentar extrair do header Content-Disposition
        content_disposition = response.headers.get('content-disposition', '')
        if 'filename=' in content_disposition:
            filename = content_disposition.split('filename=')[1].strip('"\'')
            if filename:
                return filename
        
        # Tentar extrair do Content-Type
        content_type = response.headers.get('content-type', '')
        if 'pdf' in content_type:
            return f"document_{file_id}.pdf"
        elif 'image' in content_type:
            ext = content_type.split('/')[-1]
            return f"image_{file_id}.{ext}"
        elif 'text' in content_type:
            return f"document_{file_id}.txt"
        elif 'document' in content_type:
            return f"document_{file_id}.docx"
        
        # Fallback
        return f"file_{file_id}"
    
    def _save_to_file(self, content: bytes, filename: str, save_directory: str) -> str:
        """
        Salva conteúdo em arquivo
        """
        # Criar diretório se não existir
        os.makedirs(save_directory, exist_ok=True)
        
        # Caminho completo do arquivo
        file_path = os.path.join(save_directory, filename)
        
        # Evitar sobrescrever arquivos
        counter = 1
        original_path = file_path
        while os.path.exists(file_path):
            name, ext = os.path.splitext(original_path)
            file_path = f"{name}_{counter}{ext}"
            counter += 1
        
        # Salvar arquivo
        with open(file_path, 'wb') as f:
            f.write(content)
        
        return file_path
    
    def _encode_to_base64(self, content: bytes, filename: str) -> str:
        """
        Codifica conteúdo para base64
        """
        # Determinar se é imagem
        is_image = any(ext in filename.lower() for ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp'])
        
        if is_image:
            return encode_image_to_base64(content, include_header=True)
        else:
            # Para outros tipos de arquivo, apenas base64
            return base64.b64encode(content).decode('utf-8')
    
    def validate_urls(self, urls: List[str]) -> Dict[str, Any]:
        """
        Valida URLs do Google Drive
        
        Returns:
            Relatório de validação
        """
        results = {
            'valid_urls': [],
            'invalid_urls': [],
            'total_urls': len(urls),
            'valid_count': 0,
            'invalid_count': 0
        }
        
        for url in urls:
            file_id = extract_google_drive_id(url)
            if file_id:
                results['valid_urls'].append({
                    'url': url,
                    'file_id': file_id,
                    'direct_url': convert_to_direct_download_url(url)
                })
                results['valid_count'] += 1
            else:
                results['invalid_urls'].append({
                    'url': url,
                    'error': 'Não foi possível extrair ID do Google Drive'
                })
                results['invalid_count'] += 1
        
        return results
    
    def get_file_info(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Obtém informações básicas do arquivo sem fazer download
        """
        try:
            file_id = extract_google_drive_id(url)
            if not file_id:
                return None
            
            direct_url = convert_to_direct_download_url(url)
            
            # Fazer HEAD request para obter metadados
            response = self.session.head(
                direct_url,
                timeout=self.timeout,
                verify=self.validate_ssl
            )
            
            if response.status_code == 200:
                return {
                    'file_id': file_id,
                    'direct_url': direct_url,
                    'content_type': response.headers.get('content-type'),
                    'content_length': response.headers.get('content-length'),
                    'size_mb': round(int(response.headers.get('content-length', 0)) / (1024 * 1024), 2) if response.headers.get('content-length') else None
                }
            
        except Exception as e:
            if not self.silent_errors:
                raise
        
        return None
    
    def close(self):
        """
        Fecha a sessão HTTP
        """
        self.session.close()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Função de conveniência
def download_from_google_drive(urls: List[str], 
                              save_directory: Optional[str] = None,
                              **kwargs) -> List[FileInfo]:
    """
    Função de conveniência para download de arquivos do Google Drive
    
    Args:
        urls: Lista de URLs do Google Drive
        save_directory: Diretório para salvar (None = retorna base64)
        **kwargs: Parâmetros adicionais para GoogleDriveDownloader
        
    Returns:
        Lista de FileInfo com resultados dos downloads
    """
    with GoogleDriveDownloader(**kwargs) as downloader:
        return downloader.download_files(urls, save_directory)