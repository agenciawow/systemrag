"""
LlamaParse Multimodal Merger

Combina conteúdo markdown do LlamaParse com screenshots em chunks multimodais estruturados.
"""
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import asdict

from ...models.data_models import (
    ParsedDocument, ScreenshotCollection, MultimodalChunk, 
    ChunkCollection, Screenshot
)
from ...utils.helpers import (
    extract_document_name, truncate_text, 
    safe_get_nested
)


class MultimodalMerger:
    """
    Componente para combinação de conteúdo multimodal
    
    Funcionalidades:
    - Múltiplas estratégias de chunking
    - Associação inteligente de texto e imagens
    - Preservação de metadados
    - Otimização de tamanho de chunks
    """
    
    def __init__(self,
                 merge_strategy: str = "page_based",
                 max_chunk_size: int = 1500,
                 include_metadata: bool = True,
                 preserve_page_structure: bool = True):
        """
        Inicializa o merger multimodal
        
        Args:
            merge_strategy: Estratégia de combinação
            max_chunk_size: Máximo de caracteres por chunk
            include_metadata: Incluir metadados de parsing
            preserve_page_structure: Manter organização original
        """
        self.merge_strategy = merge_strategy
        self.max_chunk_size = max_chunk_size
        self.include_metadata = include_metadata
        self.preserve_page_structure = preserve_page_structure
        
        # Estratégias disponíveis
        self.strategies = {
            "page_based": self._merge_by_page,
            "section_based": self._merge_by_sections,
            "smart_chunks": self._merge_smart_chunks,
            "text_only": self._merge_text_only,
            "image_only": self._merge_image_only
        }
    
    def merge_content(self, 
                     parsed_doc: ParsedDocument,
                     screenshots: ScreenshotCollection,
                     document_name: Optional[str] = None) -> ChunkCollection:
        """
        Combina documento parseado com screenshots
        
        Args:
            parsed_doc: Documento processado pelo LlamaParse
            screenshots: Screenshots das páginas
            document_name: Nome do documento (auto-detectado se vazio)
            
        Returns:
            ChunkCollection com chunks multimodais
        """
        # Determinar nome do documento
        doc_name = self._extract_document_name(parsed_doc, document_name)
        
        # Verificar se estratégia existe
        if self.merge_strategy not in self.strategies:
            raise ValueError(f"Estratégia '{self.merge_strategy}' não suportada")
        
        # Executar estratégia de merge
        strategy_func = self.strategies[self.merge_strategy]
        chunks = strategy_func(parsed_doc, screenshots, doc_name)
        
        # Calcular estatísticas
        multimodal_chunks = sum(1 for chunk in chunks if chunk.image_base64)
        text_only_chunks = len(chunks) - multimodal_chunks
        
        return ChunkCollection(
            chunks=chunks,
            total_chunks=len(chunks),
            multimodal_chunks=multimodal_chunks,
            text_only_chunks=text_only_chunks,
            document_name=doc_name
        )
    
    def _extract_document_name(self, 
                              parsed_doc: ParsedDocument, 
                              manual_name: Optional[str] = None) -> str:
        """
        Extrai nome do documento com prioridades
        """
        if manual_name:
            return manual_name
        
        # Tentar extrair de metadados (se houver)
        if hasattr(parsed_doc, 'metadata') and parsed_doc.metadata:
            job_info = safe_get_nested(parsed_doc.metadata, "jobInfo", {})
            if "fileName" in job_info:
                return extract_document_name(job_info["fileName"])
        
        # Usar filename do documento
        if parsed_doc.filename:
            return extract_document_name(parsed_doc.filename)
        
        # Fallback com job_id
        return f"Document_{parsed_doc.job_id[:8]}"
    
    def _merge_by_page(self, 
                      parsed_doc: ParsedDocument,
                      screenshots: ScreenshotCollection,
                      doc_name: str) -> List[MultimodalChunk]:
        """
        Estratégia page-based: Um chunk por página
        """
        chunks = []
        
        if not parsed_doc.markdown_content:
            return chunks
        
        # Dividir markdown por páginas
        page_contents = self._split_markdown_by_pages(parsed_doc.markdown_content)
        
        # Criar mapeamento de screenshots por página
        screenshots_map = {shot.page: shot for shot in screenshots.screenshots}
        
        # Criar chunk para cada página
        for page_num, content in enumerate(page_contents, 1):
            if not content.strip():
                continue
            
            # Obter screenshot correspondente
            screenshot = screenshots_map.get(page_num)
            
            chunk = MultimodalChunk(
                chunk_id=f"{doc_name}_page_{page_num}",
                content=truncate_text(content, self.max_chunk_size),
                page_number=page_num,
                document_name=doc_name,
                char_count=len(content),
                source="llamaparse",
                merge_strategy="page_based"
            )
            
            # Adicionar imagem se disponível
            if screenshot:
                chunk.image_base64 = screenshot.content_base64
                chunk.image_filename = screenshot.filename
                chunk.image_size = screenshot.size
            
            # Adicionar metadados
            if self.include_metadata:
                chunk.metadata = {
                    "document_name": doc_name,
                    "parse_mode": parsed_doc.parse_mode,
                    "job_id": parsed_doc.job_id,
                    "output_format": parsed_doc.output_format
                }
            
            chunks.append(chunk)
        
        return chunks
    
    def _merge_by_sections(self,
                          parsed_doc: ParsedDocument,
                          screenshots: ScreenshotCollection,
                          doc_name: str) -> List[MultimodalChunk]:
        """
        Estratégia section-based: Chunks por cabeçalhos
        """
        chunks = []
        
        if not parsed_doc.markdown_content:
            return chunks
        
        # Dividir por cabeçalhos
        sections = self._split_markdown_by_headers(parsed_doc.markdown_content)
        total_content_length = len(parsed_doc.markdown_content)
        
        # Criar mapeamento de screenshots
        screenshots_map = {shot.page: shot for shot in screenshots.screenshots}
        
        for i, (section_title, section_content) in enumerate(sections):
            if not section_content.strip():
                continue
            
            # Estimar página baseada na posição no texto
            estimated_page = self._estimate_page_from_position(
                section_content, parsed_doc.markdown_content, 
                screenshots.total_screenshots
            )
            
            # Obter screenshot correspondente
            screenshot = screenshots_map.get(estimated_page)
            
            chunk = MultimodalChunk(
                chunk_id=f"{doc_name}_section_{i+1}",
                content=truncate_text(section_content, self.max_chunk_size),
                page_number=estimated_page,
                document_name=doc_name,
                char_count=len(section_content),
                source="llamaparse",
                merge_strategy="section_based"
            )
            
            # Adicionar imagem se disponível
            if screenshot:
                chunk.image_base64 = screenshot.content_base64
                chunk.image_filename = screenshot.filename
                chunk.image_size = screenshot.size
            
            # Adicionar metadados com título da seção
            if self.include_metadata:
                chunk.metadata = {
                    "document_name": doc_name,
                    "section_title": section_title,
                    "parse_mode": parsed_doc.parse_mode,
                    "job_id": parsed_doc.job_id
                }
            
            chunks.append(chunk)
        
        return chunks
    
    def _merge_smart_chunks(self,
                           parsed_doc: ParsedDocument,
                           screenshots: ScreenshotCollection,
                           doc_name: str) -> List[MultimodalChunk]:
        """
        Estratégia smart chunking: Divisão inteligente respeitando max_chunk_size
        """
        chunks = []
        
        if not parsed_doc.markdown_content:
            return chunks
        
        # Dividir texto inteligentemente
        text_chunks = self._split_text_smart(parsed_doc.markdown_content)
        
        # Distribuir screenshots proporcionalmente
        screenshots_per_chunk = self._distribute_screenshots_proportionally(
            text_chunks, screenshots.screenshots
        )
        
        for i, (text_chunk, screenshot) in enumerate(zip(text_chunks, screenshots_per_chunk)):
            if not text_chunk.strip():
                continue
            
            # Estimar página
            estimated_page = i + 1 if screenshot else None
            
            chunk = MultimodalChunk(
                chunk_id=f"{doc_name}_chunk_{i+1}",
                content=text_chunk,
                page_number=estimated_page,
                document_name=doc_name,
                char_count=len(text_chunk),
                source="llamaparse",
                merge_strategy="smart_chunks"
            )
            
            # Adicionar imagem se disponível
            if screenshot:
                chunk.image_base64 = screenshot.content_base64
                chunk.image_filename = screenshot.filename
                chunk.image_size = screenshot.size
            
            # Adicionar metadados
            if self.include_metadata:
                chunk.metadata = {
                    "document_name": doc_name,
                    "parse_mode": parsed_doc.parse_mode,
                    "job_id": parsed_doc.job_id
                }
            
            chunks.append(chunk)
        
        return chunks
    
    def _merge_text_only(self,
                        parsed_doc: ParsedDocument,
                        screenshots: ScreenshotCollection,
                        doc_name: str) -> List[MultimodalChunk]:
        """
        Estratégia text-only: Só texto, sem imagens
        """
        chunks = []
        
        if not parsed_doc.markdown_content:
            return chunks
        
        # Dividir texto em chunks
        text_chunks = self._split_text_smart(parsed_doc.markdown_content)
        
        for i, text_chunk in enumerate(text_chunks):
            if not text_chunk.strip():
                continue
            
            chunk = MultimodalChunk(
                chunk_id=f"{doc_name}_text_{i+1}",
                content=text_chunk,
                content_type="text",
                document_name=doc_name,
                char_count=len(text_chunk),
                source="llamaparse",
                merge_strategy="text_only"
            )
            
            # Adicionar metadados
            if self.include_metadata:
                chunk.metadata = {
                    "document_name": doc_name,
                    "parse_mode": parsed_doc.parse_mode,
                    "job_id": parsed_doc.job_id
                }
            
            chunks.append(chunk)
        
        return chunks
    
    def _merge_image_only(self,
                         parsed_doc: ParsedDocument,
                         screenshots: ScreenshotCollection,
                         doc_name: str) -> List[MultimodalChunk]:
        """
        Estratégia image-only: Só imagens, sem texto
        """
        chunks = []
        
        for screenshot in screenshots.screenshots:
            chunk = MultimodalChunk(
                chunk_id=f"{doc_name}_image_{screenshot.page}",
                content=f"Imagem da página {screenshot.page}",
                content_type="image",
                page_number=screenshot.page,
                document_name=doc_name,
                char_count=len(f"Imagem da página {screenshot.page}"),
                image_base64=screenshot.content_base64,
                image_filename=screenshot.filename,
                image_size=screenshot.size,
                source="llamaparse",
                merge_strategy="image_only"
            )
            
            # Adicionar metadados
            if self.include_metadata:
                chunk.metadata = {
                    "document_name": doc_name,
                    "parse_mode": parsed_doc.parse_mode,
                    "job_id": parsed_doc.job_id
                }
            
            chunks.append(chunk)
        
        return chunks
    
    def _split_markdown_by_pages(self, content: str) -> List[str]:
        """
        Divide markdown por páginas (usando separadores --- ou divisão igual)
        """
        # Tentar dividir por separadores de página
        if '---' in content:
            pages = content.split('---')
            return [page.strip() for page in pages if page.strip()]
        
        # Divisão igual se não houver separadores
        paragraphs = content.split('\n\n')
        if len(paragraphs) <= 1:
            return [content]
        
        # Dividir em grupos aproximadamente iguais
        num_pages = max(1, len(paragraphs) // 3)  # ~3 parágrafos por página
        page_size = len(paragraphs) // num_pages
        
        pages = []
        for i in range(0, len(paragraphs), page_size):
            page_content = '\n\n'.join(paragraphs[i:i+page_size])
            pages.append(page_content)
        
        return pages
    
    def _split_markdown_by_headers(self, content: str) -> List[Tuple[str, str]]:
        """
        Divide markdown por cabeçalhos (# ##)
        """
        sections = []
        current_section = ""
        current_title = "Introdução"
        
        lines = content.split('\n')
        
        for line in lines:
            # Verificar se é cabeçalho
            if line.strip().startswith('#'):
                # Salvar seção anterior
                if current_section.strip():
                    sections.append((current_title, current_section.strip()))
                
                # Iniciar nova seção
                current_title = line.strip()
                current_section = ""
            else:
                current_section += line + '\n'
        
        # Adicionar última seção
        if current_section.strip():
            sections.append((current_title, current_section.strip()))
        
        return sections
    
    def _split_text_smart(self, content: str) -> List[str]:
        """
        Divide texto inteligentemente respeitando max_chunk_size
        """
        if len(content) <= self.max_chunk_size:
            return [content]
        
        chunks = []
        paragraphs = content.split('\n\n')
        current_chunk = ""
        
        for paragraph in paragraphs:
            # Se parágrafo é muito grande, divide por sentenças
            if len(paragraph) > self.max_chunk_size:
                sentences = re.split(r'[.!?]+', paragraph)
                for sentence in sentences:
                    if len(current_chunk) + len(sentence) > self.max_chunk_size:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                            current_chunk = sentence
                        else:
                            # Sentence muito longa, força divisão
                            chunks.append(sentence[:self.max_chunk_size].strip())
                            current_chunk = sentence[self.max_chunk_size:]
                    else:
                        current_chunk += sentence
            else:
                # Adicionar parágrafo se couber
                if len(current_chunk) + len(paragraph) <= self.max_chunk_size:
                    current_chunk += paragraph + '\n\n'
                else:
                    # Salvar chunk atual e iniciar novo
                    if current_chunk:
                        chunks.append(current_chunk.strip())
                    current_chunk = paragraph + '\n\n'
        
        # Adicionar último chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _estimate_page_from_position(self, 
                                   section_content: str, 
                                   full_content: str,
                                   total_pages: int) -> int:
        """
        Estima página baseada na posição no texto
        """
        section_pos = full_content.find(section_content[:100])  # Primeiros 100 chars
        if section_pos == -1:
            return 1
        
        # Calcular proporção
        proportion = section_pos / len(full_content)
        estimated_page = max(1, int(proportion * total_pages) + 1)
        
        return min(estimated_page, total_pages)
    
    def _distribute_screenshots_proportionally(self, 
                                             text_chunks: List[str],
                                             screenshots: List[Screenshot]) -> List[Optional[Screenshot]]:
        """
        Distribui screenshots proporcionalmente entre chunks de texto
        """
        if not screenshots:
            return [None] * len(text_chunks)
        
        result = []
        screenshot_idx = 0
        
        for i, chunk in enumerate(text_chunks):
            # Calcular proporção do chunk atual
            chunk_proportion = i / len(text_chunks)
            target_screenshot_idx = int(chunk_proportion * len(screenshots))
            
            # Garantir que não exceda o índice
            target_screenshot_idx = min(target_screenshot_idx, len(screenshots) - 1)
            
            if target_screenshot_idx < len(screenshots):
                result.append(screenshots[target_screenshot_idx])
            else:
                result.append(None)
        
        return result


# Função de conveniência
def merge_multimodal_content(parsed_doc: ParsedDocument,
                           screenshots: ScreenshotCollection,
                           document_name: Optional[str] = None,
                           **kwargs) -> ChunkCollection:
    """
    Função de conveniência para merge multimodal
    
    Args:
        parsed_doc: Documento processado
        screenshots: Screenshots das páginas
        document_name: Nome do documento
        **kwargs: Parâmetros adicionais para MultimodalMerger
        
    Returns:
        ChunkCollection com chunks multimodais
    """
    merger = MultimodalMerger(**kwargs)
    return merger.merge_content(parsed_doc, screenshots, document_name)