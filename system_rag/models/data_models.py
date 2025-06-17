"""
Modelos de dados para o Sistema RAG
"""
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from datetime import datetime


@dataclass
class FileInfo:
    """Informações de um arquivo baixado"""
    filename: str
    original_url: str
    direct_url: Optional[str] = None
    size: int = 0
    size_mb: float = 0.0
    content_base64: Optional[str] = None
    local_path: Optional[str] = None
    download_success: bool = False
    error_message: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SelectionInfo:
    """Informações sobre seleção de arquivo"""
    selected_from_count: int
    valid_files_count: int
    selection_method: str  # "filename" ou "index"
    selection_criteria: str


@dataclass
class SelectedFile(FileInfo):
    """Arquivo selecionado com informações adicionais"""
    selection_info: SelectionInfo = None


@dataclass
class ParsedDocument:
    """Documento processado pelo LlamaParse"""
    job_id: str
    filename: str
    output_format: str
    parse_mode: str
    success: bool
    markdown_content: Optional[str] = None
    char_count: int = 0
    screenshots_available: bool = False
    screenshots_count: int = 0
    error_message: Optional[str] = None


@dataclass
class Screenshot:
    """Screenshot de uma página"""
    page: int
    filename: str
    content_base64: str
    size: int
    content_type: str = "image/jpeg"
    image_type: str = "screenshot"


@dataclass
class ScreenshotCollection:
    """Coleção de screenshots"""
    screenshots: List[Screenshot]
    total_screenshots: int
    job_id: str
    success: bool


@dataclass
class MultimodalChunk:
    """Chunk multimodal com texto e imagem"""
    chunk_id: str
    content: str
    content_type: str = "multimodal"
    page_number: Optional[int] = None
    document_name: str = ""
    char_count: int = 0
    image_base64: Optional[str] = None
    image_filename: Optional[str] = None
    image_size: Optional[int] = None
    source: str = "llamaparse"
    merge_strategy: str = "page_based"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ChunkCollection:
    """Coleção de chunks multimodais"""
    chunks: List[MultimodalChunk]
    total_chunks: int
    multimodal_chunks: int
    text_only_chunks: int
    document_name: str


@dataclass
class EmbeddedChunk(MultimodalChunk):
    """Chunk com embedding"""
    embedding: List[float] = field(default_factory=list)
    dimension: int = 1024
    model: str = "voyage-multimodal-3"


@dataclass
class QueryEmbedding:
    """Embedding de uma consulta"""
    query: str
    embedding: List[float]
    dimension: int = 1024
    model: str = "voyage-multimodal-3"
    type: str = "query"


@dataclass
class SearchResult:
    """Resultado de busca vetorial"""
    document_id: str
    content: str
    document_name: str
    page_number: Optional[int] = None
    similarity: float = 0.0
    image_url: Optional[str] = None
    image_filename_r2: Optional[str] = None
    image_base64: Optional[str] = None
    has_image: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SearchResults:
    """Coleção de resultados de busca"""
    documents: List[SearchResult]
    total_results: int
    query_text: str
    similarity_stats: Dict[str, float] = field(default_factory=dict)


@dataclass
class RerankedResult:
    """Resultado após reranking"""
    selected_docs: List[SearchResult]
    justification: str
    indices: List[int]
    total_candidates: int
    model: str
    query: str
    config: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProcessingStatus:
    """Status de processamento"""
    success: bool
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class UploadResult:
    """Resultado de upload para R2"""
    image_url: str
    image_filename_r2: str
    image_size_original: int
    image_size_bytes: int
    document_name_used: str
    prefix_used: str
    success: bool = True


@dataclass
class InsertionResult:
    """Resultado de inserção no Astra DB"""
    inserted_count: int
    inserted_ids: List[str]
    total_batches: int
    success: bool = True