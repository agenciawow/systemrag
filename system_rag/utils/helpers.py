"""
Funções utilitárias para o Sistema RAG
"""
import re
import base64
import imghdr
import os
from typing import Optional, Dict, Any, List, Generator


def extract_google_drive_id(url: str) -> Optional[str]:
    """
    Extrai o ID do Google Drive de diferentes formatos de URL
    
    Suporta:
    - drive.google.com/file/d/[FILE_ID]
    - drive.google.com/open?id=[FILE_ID]
    - docs.google.com/.*[?&]id=[FILE_ID]
    """
    patterns = [
        r'/file/d/([a-zA-Z0-9-_]+)',
        r'[?&]id=([a-zA-Z0-9-_]+)',
        r'/open\?id=([a-zA-Z0-9-_]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    return None


def convert_to_direct_download_url(url: str) -> Optional[str]:
    """
    Converte URL do Google Drive para download direto
    """
    file_id = extract_google_drive_id(url)
    if file_id:
        return f"https://drive.google.com/uc?export=download&id={file_id}"
    return None


def clean_filename(filename: str) -> str:
    """
    Limpa nome de arquivo removendo caracteres especiais
    mas mantém acentos
    """
    # Remove caracteres problemáticos mas mantém acentos e espaços
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove espaços extras
    filename = re.sub(r'\s+', ' ', filename).strip()
    return filename


def extract_document_name(filename: str) -> str:
    """
    Extrai nome do documento removendo extensão
    """
    if '.' in filename:
        return os.path.splitext(filename)[0]
    return filename


def format_file_size(size_bytes: int) -> str:
    """
    Formata tamanho do arquivo em formato legível
    """
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def encode_image_to_base64(image_bytes: bytes, include_header: bool = True) -> str:
    """
    Codifica imagem para base64 com header opcional
    """
    b64_string = base64.b64encode(image_bytes).decode('utf-8')
    
    if include_header:
        # Detecta tipo da imagem
        img_type = imghdr.what(None, image_bytes) or "jpeg"
        return f"data:image/{img_type};base64,{b64_string}"
    
    return b64_string


def decode_base64_image(base64_string: str) -> bytes:
    """
    Decodifica imagem base64 removendo header se necessário
    """
    if base64_string.startswith('data:'):
        # Remove header data:image/...;base64,
        base64_string = base64_string.split(',', 1)[1]
    
    return base64.b64decode(base64_string)


def truncate_text(text: str, max_length: int) -> str:
    """
    Trunca texto mantendo integridade
    """
    if len(text) <= max_length:
        return text
    
    # Tenta truncar em uma quebra de palavra
    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # Se conseguir truncar perto do limite
        return truncated[:last_space] + "..."
    else:
        return truncated + "..."


def clean_base64_from_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Remove recursivamente todos os campos que contêm base64
    para otimizar armazenamento
    """
    if isinstance(data, dict):
        cleaned = {}
        for key, value in data.items():
            if isinstance(key, str) and 'base64' in key.lower():
                continue  # Pula campos base64
            elif isinstance(value, (dict, list)):
                cleaned_value = clean_base64_from_dict(value)
                if cleaned_value:  # Só adiciona se não for vazio
                    cleaned[key] = cleaned_value
            else:
                cleaned[key] = value
        return cleaned
    elif isinstance(data, list):
        return [clean_base64_from_dict(item) for item in data if item is not None]
    else:
        return data


def extract_text_content(chunk: Dict[str, Any]) -> str:
    """
    Extrai conteúdo de texto de um chunk
    Prioridade: content -> markdown_content -> text
    """
    for field in ['content', 'markdown_content', 'text']:
        if field in chunk and chunk[field]:
            return str(chunk[field])
    return ""


def extract_image_content(chunk: Dict[str, Any]) -> Optional[str]:
    """
    Extrai conteúdo de imagem de um chunk
    Prioridade: image_base64 -> image_data
    """
    for field in ['image_base64', 'image_data']:
        if field in chunk and chunk[field]:
            image_data = chunk[field]
            # Garante que tem header correto
            if isinstance(image_data, str) and not image_data.startswith('data:'):
                return f"data:image/jpeg;base64,{image_data}"
            return image_data
    return None


def generate_unique_filename(document_name: str, page_num: int, original_filename: str) -> str:
    """
    Gera nome único para arquivo no R2
    """
    clean_doc_name = clean_filename(document_name)
    clean_original = clean_filename(original_filename)
    
    # Se o original_filename já contém informação de página (ex: page_1.jpg),
    # usar apenas o chunk_id com a extensão do arquivo
    if "page_" in clean_original.lower():
        # Extrair apenas a extensão do arquivo original
        file_extension = ""
        if "." in clean_original:
            file_extension = "." + clean_original.split(".")[-1]
        return f"{clean_doc_name}_page_{page_num}{file_extension}"
    
    # Caso contrário, usar o formato original
    return f"{clean_doc_name}_page_{page_num}_{clean_original}"


def parse_similarity_score(similarity_str: str) -> float:
    """
    Converte string de similaridade para float
    """
    try:
        if isinstance(similarity_str, (int, float)):
            return float(similarity_str)
        
        # Remove caracteres não numéricos exceto ponto e vírgula
        clean_str = re.sub(r'[^\d.,]', '', str(similarity_str))
        if ',' in clean_str and '.' in clean_str:
            # Formato brasileiro: 0,892
            clean_str = clean_str.replace(',', '.')
        elif ',' in clean_str:
            clean_str = clean_str.replace(',', '.')
        
        return float(clean_str)
    except (ValueError, TypeError):
        return 0.0


def chunk_list(lst: List[Any], chunk_size: int) -> Generator[List[Any], None, None]:
    """
    Divide lista em chunks menores
    """
    for i in range(0, len(lst), chunk_size):
        yield lst[i:i + chunk_size]


def safe_get_nested(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """
    Obtém valor aninhado de dict usando path com pontos
    Ex: safe_get_nested(data, "metadata.document_name", "Unknown")
    """
    keys = path.split('.')
    current = data
    
    try:
        for key in keys:
            current = current[key]
        return current
    except (KeyError, TypeError):
        return default