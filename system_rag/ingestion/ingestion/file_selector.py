"""
File Selector

Seleciona um arquivo específico de uma lista de arquivos baixados.
"""
from typing import List, Optional, Dict, Any
from dataclasses import asdict

from ...models.data_models import FileInfo, SelectedFile, SelectionInfo


class FileSelector:
    """
    Componente para seleção de arquivos da lista de downloads
    
    Funcionalidades:
    - Seleção por índice ou filtro de nome
    - Remove arquivos com erros automaticamente
    - Adiciona metadados de seleção
    """
    
    def __init__(self):
        """Inicializa o seletor de arquivos"""
        pass
    
    def select_file(self, 
                   file_list: List[FileInfo],
                   file_index: int = 0,
                   filename_filter: Optional[str] = None) -> SelectedFile:
        """
        Seleciona um arquivo da lista
        
        Args:
            file_list: Lista de arquivos do downloader
            file_index: Índice do arquivo (0 = primeiro, -1 = último)
            filename_filter: Filtro por nome (sobrescreve índice se fornecido)
            
        Returns:
            SelectedFile com informações de seleção
            
        Raises:
            ValueError: Se nenhum arquivo válido for encontrado
            IndexError: Se índice for inválido
        """
        # Filtrar arquivos válidos (sem erros)
        valid_files = [f for f in file_list if f.download_success and not f.error_message]
        
        if not valid_files:
            raise ValueError("Nenhum arquivo válido encontrado na lista")
        
        # Determinar método de seleção
        selected_file = None
        selection_method = "index"
        selection_criteria = str(file_index)
        
        if filename_filter:
            # Seleção por nome
            selection_method = "filename"
            selection_criteria = filename_filter
            
            for file_info in valid_files:
                if filename_filter.lower() in file_info.filename.lower():
                    selected_file = file_info
                    break
            
            if not selected_file:
                raise ValueError(f"Nenhum arquivo encontrado com filtro: {filename_filter}")
        
        else:
            # Seleção por índice
            try:
                selected_file = valid_files[file_index]
            except IndexError:
                raise IndexError(f"Índice {file_index} inválido. Arquivos válidos: {len(valid_files)}")
        
        # Criar informações de seleção
        selection_info = SelectionInfo(
            selected_from_count=len(file_list),
            valid_files_count=len(valid_files),
            selection_method=selection_method,
            selection_criteria=selection_criteria
        )
        
        # Criar SelectedFile
        selected_file_dict = asdict(selected_file)
        selected_file_obj = SelectedFile(**selected_file_dict)
        selected_file_obj.selection_info = selection_info
        
        return selected_file_obj
    
    def get_selection_summary(self, file_list: List[FileInfo]) -> Dict[str, Any]:
        """
        Obtém resumo dos arquivos disponíveis para seleção
        
        Args:
            file_list: Lista de arquivos
            
        Returns:
            Dicionário com resumo dos arquivos
        """
        valid_files = [f for f in file_list if f.download_success and not f.error_message]
        invalid_files = [f for f in file_list if not f.download_success or f.error_message]
        
        summary = {
            'total_files': len(file_list),
            'valid_files': len(valid_files),
            'invalid_files': len(invalid_files),
            'valid_files_info': [],
            'invalid_files_info': []
        }
        
        # Informações dos arquivos válidos
        for i, file_info in enumerate(valid_files):
            summary['valid_files_info'].append({
                'index': i,
                'filename': file_info.filename,
                'size_mb': file_info.size_mb,
                'original_url': file_info.original_url
            })
        
        # Informações dos arquivos inválidos
        for file_info in invalid_files:
            summary['invalid_files_info'].append({
                'filename': file_info.filename,
                'error': file_info.error_message,
                'original_url': file_info.original_url
            })
        
        return summary
    
    def select_by_extension(self, 
                           file_list: List[FileInfo],
                           extension: str) -> List[SelectedFile]:
        """
        Seleciona todos os arquivos com uma extensão específica
        
        Args:
            file_list: Lista de arquivos
            extension: Extensão desejada (ex: '.pdf', 'pdf')
            
        Returns:
            Lista de SelectedFile correspondentes
        """
        # Normalizar extensão
        if not extension.startswith('.'):
            extension = '.' + extension
        extension = extension.lower()
        
        # Filtrar arquivos válidos
        valid_files = [f for f in file_list if f.download_success and not f.error_message]
        
        # Filtrar por extensão
        matching_files = []
        for file_info in valid_files:
            if file_info.filename.lower().endswith(extension):
                matching_files.append(file_info)
        
        # Criar SelectedFile para cada arquivo
        selected_files = []
        for i, file_info in enumerate(matching_files):
            selection_info = SelectionInfo(
                selected_from_count=len(file_list),
                valid_files_count=len(valid_files),
                selection_method="extension",
                selection_criteria=extension
            )
            
            selected_file_dict = asdict(file_info)
            selected_file_obj = SelectedFile(**selected_file_dict)
            selected_file_obj.selection_info = selection_info
            selected_files.append(selected_file_obj)
        
        return selected_files
    
    def select_largest_file(self, file_list: List[FileInfo]) -> SelectedFile:
        """
        Seleciona o maior arquivo válido da lista
        
        Args:
            file_list: Lista de arquivos
            
        Returns:
            SelectedFile com o maior arquivo
        """
        valid_files = [f for f in file_list if f.download_success and not f.error_message]
        
        if not valid_files:
            raise ValueError("Nenhum arquivo válido encontrado na lista")
        
        # Encontrar o maior arquivo
        largest_file = max(valid_files, key=lambda f: f.size)
        
        # Criar informações de seleção
        selection_info = SelectionInfo(
            selected_from_count=len(file_list),
            valid_files_count=len(valid_files),
            selection_method="largest",
            selection_criteria=f"{largest_file.size_mb} MB"
        )
        
        # Criar SelectedFile
        selected_file_dict = asdict(largest_file)
        selected_file_obj = SelectedFile(**selected_file_dict)
        selected_file_obj.selection_info = selection_info
        
        return selected_file_obj
    
    def select_by_criteria(self, 
                          file_list: List[FileInfo],
                          criteria: Dict[str, Any]) -> List[SelectedFile]:
        """
        Seleciona arquivos baseado em critérios customizados
        
        Args:
            file_list: Lista de arquivos
            criteria: Critérios de seleção:
                - min_size_mb: Tamanho mínimo em MB
                - max_size_mb: Tamanho máximo em MB
                - filename_contains: Texto que deve estar no nome
                - filename_excludes: Texto que não deve estar no nome
                
        Returns:
            Lista de SelectedFile que atendem aos critérios
        """
        valid_files = [f for f in file_list if f.download_success and not f.error_message]
        matching_files = []
        
        for file_info in valid_files:
            # Verificar critérios
            match = True
            
            # Tamanho mínimo
            if 'min_size_mb' in criteria:
                if file_info.size_mb < criteria['min_size_mb']:
                    match = False
                    continue
            
            # Tamanho máximo
            if 'max_size_mb' in criteria:
                if file_info.size_mb > criteria['max_size_mb']:
                    match = False
                    continue
            
            # Nome deve conter
            if 'filename_contains' in criteria:
                if criteria['filename_contains'].lower() not in file_info.filename.lower():
                    match = False
                    continue
            
            # Nome não deve conter
            if 'filename_excludes' in criteria:
                if criteria['filename_excludes'].lower() in file_info.filename.lower():
                    match = False
                    continue
            
            if match:
                matching_files.append(file_info)
        
        # Criar SelectedFile para cada arquivo
        selected_files = []
        for file_info in matching_files:
            selection_info = SelectionInfo(
                selected_from_count=len(file_list),
                valid_files_count=len(valid_files),
                selection_method="criteria",
                selection_criteria=str(criteria)
            )
            
            selected_file_dict = asdict(file_info)
            selected_file_obj = SelectedFile(**selected_file_dict)
            selected_file_obj.selection_info = selection_info
            selected_files.append(selected_file_obj)
        
        return selected_files


# Função de conveniência
def select_file_from_list(file_list: List[FileInfo],
                         file_index: int = 0,
                         filename_filter: Optional[str] = None) -> SelectedFile:
    """
    Função de conveniência para seleção de arquivo
    
    Args:
        file_list: Lista de arquivos do downloader
        file_index: Índice do arquivo (0 = primeiro, -1 = último)
        filename_filter: Filtro por nome (sobrescreve índice se fornecido)
        
    Returns:
        SelectedFile com informações de seleção
    """
    selector = FileSelector()
    return selector.select_file(file_list, file_index, filename_filter)