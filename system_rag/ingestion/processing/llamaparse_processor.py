"""
LlamaParse with Screenshots

Processa documentos usando LlamaParse com captura de screenshots das páginas.
"""
import requests
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import asdict

from ...models.data_models import (
    SelectedFile, ParsedDocument, Screenshot, ScreenshotCollection,
    ProcessingStatus
)
from ...utils.helpers import decode_base64_image, encode_image_to_base64
from ...config.settings import settings


class LlamaParseProcessor:
    """
    Componente para processamento de documentos com LlamaParse
    
    Funcionalidades:
    - Upload de documentos para LlamaParse
    - Processamento com múltiplos modos
    - Captura de screenshots das páginas
    - Download de resultados processados
    """
    
    def __init__(self,
                 api_key: str,
                 api_endpoint: str = "https://api.cloud.llamaindex.ai/",
                 parse_mode: str = "parse_page_with_agent",
                 output_format: str = "markdown",
                 take_screenshot: bool = True,
                 use_vendor_multimodal_model: bool = False,
                 vendor_multimodal_model_name: str = "anthropic-sonnet-3.5",
                 vendor_multimodal_api_key: Optional[str] = None,
                 max_wait_time: int = 300,
                 poll_interval: int = 5):
        """
        Inicializa o processador LlamaParse
        
        Args:
            api_key: Chave da API LlamaCloud
            api_endpoint: Endpoint da API
            parse_mode: Método de parsing (ignorado se use_vendor_multimodal_model=True)
            output_format: Formato de saída (markdown, text, json)
            take_screenshot: Capturar screenshots
            use_vendor_multimodal_model: Usar modo multimodal com LLM/LVM
            vendor_multimodal_model_name: Nome do modelo multimodal
            vendor_multimodal_api_key: Chave própria do modelo (opcional, reduz custo)
            max_wait_time: Tempo máximo de espera em segundos
            poll_interval: Intervalo de polling em segundos
        """
        self.api_key = api_key
        self.api_endpoint = api_endpoint.rstrip('/')
        self.parse_mode = parse_mode
        self.output_format = output_format
        self.take_screenshot = take_screenshot
        self.use_vendor_multimodal_model = use_vendor_multimodal_model
        self.vendor_multimodal_model_name = vendor_multimodal_model_name
        self.vendor_multimodal_api_key = vendor_multimodal_api_key
        self.max_wait_time = max_wait_time
        self.poll_interval = poll_interval
        
        # Headers padrão para API
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }
    
    @classmethod
    def create_multimodal(cls, 
                         api_key: str,
                         model_name: str = "anthropic-sonnet-3.5",
                         model_api_key: Optional[str] = None,
                         **kwargs) -> 'LlamaParseProcessor':
        """
        Cria uma instância configurada para modo multimodal
        
        Args:
            api_key: Chave da API LlamaCloud
            model_name: Nome do modelo multimodal
                      - anthropic-sonnet-3.5, anthropic-sonnet-3.7, anthropic-sonnet-4.0
                      - openai-gpt4o, openai-gpt-4o-mini, openai-gpt-4-1
                      - gemini-2.0-flash-001, gemini-2.5-pro, gemini-1.5-pro
            model_api_key: Chave própria do modelo (opcional, reduz custo)
            **kwargs: Outros parâmetros para __init__
            
        Returns:
            LlamaParseProcessor configurado para multimodal
        """
        return cls(
            api_key=api_key,
            use_vendor_multimodal_model=True,
            vendor_multimodal_model_name=model_name,
            vendor_multimodal_api_key=model_api_key,
            **kwargs
        )
    
    def process_document(self, selected_file: SelectedFile) -> ParsedDocument:
        """
        Processa documento completo
        
        Args:
            selected_file: Arquivo selecionado para processamento
            
        Returns:
            ParsedDocument com resultado do processamento
        """
        try:
            # Upload do arquivo
            job_id = self._upload_document(selected_file)
            
            # Aguardar processamento
            self._wait_for_completion(job_id)
            
            # Download do resultado
            parsed_doc = self._download_result(job_id, selected_file.filename)
            
            return parsed_doc
            
        except Exception as e:
            return ParsedDocument(
                job_id="",
                filename=selected_file.filename,
                output_format=self.output_format,
                parse_mode=self.parse_mode,
                success=False,
                error_message=str(e)
            )
    
    def get_screenshots(self, job_id: str) -> ScreenshotCollection:
        """
        Obtém screenshots do trabalho processado
        
        Args:
            job_id: ID do trabalho LlamaParse
            
        Returns:
            ScreenshotCollection com todas as screenshots
        """
        try:
            # CORREÇÃO: Obter detalhes do job primeiro para ver imagens disponíveis
            job_details = self._get_job_details(job_id)
            
            # Tentar várias estruturas de resposta possíveis
            available_images = []
            
            # Estrutura 1: jobInfo.images
            if "jobInfo" in job_details and "images" in job_details["jobInfo"]:
                available_images = job_details["jobInfo"]["images"]
            
            # Estrutura 2: images direto
            elif "images" in job_details:
                available_images = job_details["images"]
            
            # Estrutura 3: result.images
            elif "result" in job_details and "images" in job_details["result"]:
                available_images = job_details["result"]["images"]
            
            # Debug: mostrar estrutura completa se não encontrar imagens
            if not available_images:
                print(f"🔍 Debug job details keys: {list(job_details.keys())}")
                if "jobInfo" in job_details:
                    print(f"🔍 Debug jobInfo keys: {list(job_details['jobInfo'].keys())}")
            
            print(f"🔍 Imagens disponíveis no job: {available_images}")
            
            if not available_images:
                # Tentar abordagem alternativa: verificar se existem images no endpoint específico
                return self._try_alternative_screenshot_approach(job_id)
            
            # Filtrar apenas screenshots (page_X.jpg)
            screenshot_images = []
            for image_name in available_images:
                if any(pattern in image_name.lower() for pattern in ["page_", "screenshot", ".jpg", ".png"]):
                    screenshot_images.append(image_name)
                else:
                    print(f"⚠️  Imagem não é screenshot: {image_name}")
                    # Incluir mesmo assim, pode ser screenshot com nome diferente
                    screenshot_images.append(image_name)
            
            print(f"📸 Screenshots para download: {len(screenshot_images)} - {screenshot_images}")
            
            screenshots = []
            
            # Download de cada screenshot
            for i, image_name in enumerate(screenshot_images):
                screenshot = self._download_screenshot(job_id, image_name, i + 1)
                if screenshot:
                    screenshots.append(screenshot)
            
            print(f"✅ Screenshots baixadas: {len(screenshots)}/{len(screenshot_images)}")
            
            return ScreenshotCollection(
                screenshots=screenshots,
                total_screenshots=len(screenshots),
                job_id=job_id,
                success=True
            )
            
        except Exception as e:
            print(f"❌ Erro ao obter screenshots: {e}")
            return ScreenshotCollection(
                screenshots=[],
                total_screenshots=0,
                job_id=job_id,
                success=False
            )
    
    def _try_alternative_screenshot_approach(self, job_id: str) -> ScreenshotCollection:
        """
        Tenta abordagem alternativa para encontrar screenshots
        """
        try:
            # Tentar URLs comuns de imagens
            common_image_names = [
                "page_1.jpg", "page_2.jpg", "page_3.jpg", 
                "screenshot_1.jpg", "screenshot_2.jpg",
                "image_1.jpg", "image_2.jpg"
            ]
            
            screenshots = []
            
            for i, image_name in enumerate(common_image_names):
                screenshot = self._download_screenshot(job_id, image_name, i + 1)
                if screenshot:
                    screenshots.append(screenshot)
                else:
                    # Se não conseguir baixar, para de tentar
                    break
            
            if screenshots:
                print(f"✅ Encontradas {len(screenshots)} screenshots via abordagem alternativa")
            
            return ScreenshotCollection(
                screenshots=screenshots,
                total_screenshots=len(screenshots),
                job_id=job_id,
                success=True
            )
            
        except Exception as e:
            print(f"❌ Erro na abordagem alternativa: {e}")
            return ScreenshotCollection(
                screenshots=[],
                total_screenshots=0,
                job_id=job_id,
                success=False
            )
    
    def _upload_document(self, selected_file: SelectedFile) -> str:
        """
        Faz upload do documento para LlamaParse
        """
        upload_url = f"{self.api_endpoint}/api/v1/parsing/upload"
        
        # Preparar arquivo para upload
        if selected_file.content_base64:
            # Decodificar base64
            file_content = decode_base64_image(selected_file.content_base64)
        elif selected_file.local_path:
            # Ler arquivo local
            with open(selected_file.local_path, 'rb') as f:
                file_content = f.read()
        else:
            raise ValueError("Arquivo não possui conteúdo base64 nem caminho local")
        
        # Preparar dados do formulário
        files = {
            'file': (selected_file.filename, file_content, 'application/octet-stream')
        }
        
        data = {
            'output_format': self.output_format,
            'take_screenshot': str(self.take_screenshot).lower(),
        }
        
        # Configurar modo multimodal ou parse_mode tradicional
        if self.use_vendor_multimodal_model:
            data['use_vendor_multimodal_model'] = 'true'
            data['vendor_multimodal_model_name'] = self.vendor_multimodal_model_name
            
            # Adicionar chave própria se fornecida (reduz custo para 1 crédito/página)
            if self.vendor_multimodal_api_key:
                data['vendor_multimodal_api_key'] = self.vendor_multimodal_api_key
        else:
            data['parse_mode'] = self.parse_mode
        
        # Headers específicos para upload
        upload_headers = {
            "Authorization": f"Bearer {self.api_key}"
        }
        
        response = requests.post(
            upload_url,
            headers=upload_headers,
            files=files,
            data=data
        )
        response.raise_for_status()
        
        result = response.json()
        return result['id']  # Job ID
    
    def _wait_for_completion(self, job_id: str):
        """
        Aguarda conclusão do processamento
        """
        status_url = f"{self.api_endpoint}/api/v1/parsing/job/{job_id}"
        start_time = time.time()
        
        while time.time() - start_time < self.max_wait_time:
            response = requests.get(status_url, headers=self.headers)
            response.raise_for_status()
            
            job_info = response.json()
            status = job_info.get('status', '').upper()
            
            if status == 'SUCCESS':
                return
            elif status == 'ERROR' or status == 'FAILED':
                error_msg = job_info.get('error', 'Processamento falhou')
                raise Exception(f"Erro no processamento: {error_msg}")
            
            # Aguardar antes da próxima verificação
            time.sleep(self.poll_interval)
        
        raise TimeoutError(f"Processamento não concluído em {self.max_wait_time} segundos")
    
    def _download_result(self, job_id: str, filename: str) -> ParsedDocument:
        """
        Faz download do resultado processado
        """
        result_url = f"{self.api_endpoint}/api/v1/parsing/job/{job_id}/result/{self.output_format}"
        
        response = requests.get(result_url, headers=self.headers)
        response.raise_for_status()
        
        # Conteúdo processado
        if self.output_format == 'json':
            content = response.json()
            markdown_content = json.dumps(content, indent=2)
        else:
            markdown_content = response.text
        
        # Contar screenshots disponíveis
        screenshots_count = 0
        screenshots_available = False
        
        if self.take_screenshot:
            try:
                screenshots_collection = self.get_screenshots(job_id)
                screenshots_count = screenshots_collection.total_screenshots
                screenshots_available = screenshots_collection.success and screenshots_count > 0
            except:
                pass  # Ignorar erros na contagem de screenshots
        
        return ParsedDocument(
            job_id=job_id,
            filename=filename,
            output_format=self.output_format,
            parse_mode=self.parse_mode,
            success=True,
            markdown_content=markdown_content,
            char_count=len(markdown_content),
            screenshots_available=screenshots_available,
            screenshots_count=screenshots_count
        )
    
    def _get_job_details(self, job_id: str) -> Dict[str, Any]:
        """
        Obtém detalhes completos do job incluindo imagens disponíveis
        """
        try:
            # Usar endpoint de details conforme documentação oficial - deve ser GET
            details_url = f"{self.api_endpoint}/api/v1/parsing/job/{job_id}/details"
            response = requests.get(details_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"❌ Erro ao obter detalhes do job: {e}")
            return {}
    
    def _download_screenshot(self, job_id: str, image_name: str, page_num: int) -> Optional[Screenshot]:
        """
        Faz download de uma screenshot específica
        """
        try:
            image_url = f"{self.api_endpoint}/api/v1/parsing/job/{job_id}/result/image/{image_name}"
            
            response = requests.get(image_url, headers=self.headers)
            response.raise_for_status()
            
            # Codificar para base64
            image_base64 = encode_image_to_base64(response.content, include_header=True)
            
            return Screenshot(
                page=page_num,
                filename=image_name,
                content_base64=image_base64,
                size=len(response.content),
                content_type=response.headers.get('content-type', 'image/jpeg'),
                image_type="screenshot"
            )
            
        except Exception:
            return None
    
    def get_job_status(self, job_id: str) -> Dict[str, Any]:
        """
        Obtém status detalhado de um trabalho
        """
        try:
            status_url = f"{self.api_endpoint}/api/v1/parsing/job/{job_id}"
            response = requests.get(status_url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            return {'error': str(e)}
    
    def list_supported_formats(self) -> List[str]:
        """
        Lista formatos suportados pelo LlamaParse
        """
        return [
            'pdf', 'docx', 'doc', 'pptx', 'ppt', 'xlsx', 'xls',
            'txt', 'rtf', 'html', 'xml', 'epub'
        ]
    
    def validate_file_format(self, filename: str) -> bool:
        """
        Valida se formato do arquivo é suportado
        """
        if '.' not in filename:
            return False
        
        extension = filename.lower().split('.')[-1]
        return extension in self.list_supported_formats()


# Função de conveniência
def process_with_llamaparse(selected_file: SelectedFile,
                           api_key: str,
                           **kwargs) -> ParsedDocument:
    """
    Função de conveniência para processamento com LlamaParse
    
    Args:
        selected_file: Arquivo selecionado
        api_key: Chave da API LlamaParse
        **kwargs: Parâmetros adicionais para LlamaParseProcessor
        
    Returns:
        ParsedDocument com resultado do processamento
    """
    processor = LlamaParseProcessor(api_key=api_key, **kwargs)
    return processor.process_document(selected_file)


def get_screenshots_from_job(job_id: str, api_key: str) -> ScreenshotCollection:
    """
    Função de conveniência para obter screenshots
    
    Args:
        job_id: ID do trabalho LlamaParse
        api_key: Chave da API LlamaParse
        
    Returns:
        ScreenshotCollection com screenshots
    """
    processor = LlamaParseProcessor(api_key=api_key)
    return processor.get_screenshots(job_id)