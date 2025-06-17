"""
Re-ranker para Sistema RAG

Re-ordena resultados de busca usando modelos de linguagem.
"""
import logging
import re
from typing import List, Dict, Any, Tuple
from openai import OpenAI

from ...models.data_models import SearchResult, RerankedResult, ProcessingStatus
from ...config.settings import settings

logger = logging.getLogger(__name__)


class SearchReranker:
    """
    Re-ranker para resultados de busca
    
    Funcionalidades:
    - Re-ranking com GPT-4
    - Seleção inteligente de documentos
    - Justificativas para seleções
    - Suporte a imagens multimodais
    """
    
    def __init__(self,
                 openai_client: OpenAI = None,
                 model: str = None,
                 max_tokens: int = 512,
                 max_candidates: int = 10):
        """
        Inicializa o re-ranker
        
        Args:
            openai_client: Cliente OpenAI
            model: Modelo para re-ranking (usa configuração se None)
            max_tokens: Máximo de tokens na resposta
            max_candidates: Máximo de candidatos para avaliar
        """
        self.openai_client = openai_client or OpenAI(api_key=settings.api.openai_api_key)
        self.model = model or settings.openai_models.rerank_model
        self.max_tokens = max_tokens
        self.max_candidates = max_candidates
    
    def rerank_results(self,
                      query: str,
                      search_results: List[SearchResult],
                      max_selected: int = 2,
                      include_images: bool = True) -> RerankedResult:
        """
        Re-rankeia resultados de busca
        
        Args:
            query: Query original
            search_results: Resultados da busca vetorial
            max_selected: Máximo de documentos para selecionar
            include_images: Incluir imagens no re-ranking
            
        Returns:
            Resultado do re-ranking
        """
        try:
            if not search_results:
                return self._create_empty_result(query)
            
            # Limitar candidatos para evitar excesso de tokens
            candidates = search_results[:self.max_candidates]
            
            logger.debug(f"Re-rankeando {len(candidates)} candidatos para query: '{query}'")
            
            if len(candidates) == 1:
                return self._single_candidate_result(query, candidates[0])
            
            # Preparar prompt multimodal
            content = self._build_rerank_prompt(query, candidates, max_selected)
            
            # Executar re-ranking
            response = self.openai_client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": content}],
                max_tokens=self.max_tokens,
                temperature=settings.openai_models.rerank_temperature
            )
            
            result_text = response.choices[0].message.content or ""
            logger.debug(f"Resposta do re-ranking: {result_text}")
            
            # Parsear resultado
            selected_docs, justification, indices = self._parse_rerank_response(
                result_text, candidates
            )
            
            return RerankedResult(
                selected_docs=selected_docs,
                justification=justification,
                indices=indices,
                total_candidates=len(candidates),
                model=self.model,
                query=query,
                config={
                    "max_selected": max_selected,
                    "include_images": include_images,
                    "max_tokens": self.max_tokens
                }
            )
            
        except Exception as e:
            logger.error(f"Erro no re-ranking: {e}")
            # Fallback: retornar os primeiros resultados
            fallback_selected = search_results[:max_selected]
            return RerankedResult(
                selected_docs=fallback_selected,
                justification=f"Fallback devido a erro: {str(e)}",
                indices=list(range(len(fallback_selected))),
                total_candidates=len(search_results),
                model=self.model,
                query=query,
                config={"error": str(e)}
            )
    
    def _build_rerank_prompt(self,
                           query: str,
                           candidates: List[SearchResult],
                           max_selected: int) -> List[Dict[str, Any]]:
        """
        Constrói prompt multimodal para re-ranking
        """
        # Preparar informações dos candidatos
        pages_info = ", ".join(
            f"{candidate.document_name} (p.{candidate.page_number or 'N/A'})"
            for candidate in candidates
        )
        
        # Prompt principal
        prompt_text = (
            f"Pergunta: '{query}'\n"
            f"Candidatos ({len(candidates)}): {pages_info}\n\n"
            f"Selecione os {max_selected} documentos mais relevantes para responder a pergunta.\n"
            f"Máximo {max_selected} documentos.\n\n"
            "Formato da resposta:\n"
            "Páginas_Selecionadas: [nº] ou [nº1, nº2]\n"
            "Justificativa: [explique por que estes documentos são mais relevantes]\n\n"
            "CANDIDATOS:"
        )
        
        content = [{"type": "text", "text": prompt_text}]
        
        # Adicionar cada candidato
        for i, candidate in enumerate(candidates, 1):
            # Informações textuais
            preview = candidate.content[:300] if candidate.content else ""
            similarity = candidate.similarity
            
            candidate_text = (
                f"\n=== CANDIDATO {i}: {candidate.document_name.upper()} - "
                f"PÁGINA {candidate.page_number or 'N/A'} ===\n"
                f"Similaridade: {similarity:.4f}\n"
                f"Conteúdo: {preview}{'...' if len(candidate.content or '') > 300 else ''}\n"
            )
            content.append({"type": "text", "text": candidate_text})
            
            # Adicionar imagem se disponível
            if candidate.image_base64:
                content.append({
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{candidate.image_base64}"}
                })
            elif candidate.image_url:
                # Nota: em produção, você pode querer buscar a imagem aqui
                content.append({
                    "type": "text", 
                    "text": f"[Imagem disponível em: {candidate.image_url}]"
                })
        
        return content
    
    def _parse_rerank_response(self,
                              response_text: str,
                              candidates: List[SearchResult]) -> Tuple[List[SearchResult], str, List[int]]:
        """
        Parseia resposta do re-ranking
        """
        selected_nums: List[int] = []
        justification = "Justificativa não fornecida."
        
        # Parsear linhas da resposta
        for line in response_text.splitlines():
            line = line.strip()
            
            if line.lower().startswith("páginas_selecionadas"):
                # Extrair números
                numbers = re.findall(r'\d+', line)
                selected_nums = [int(n) for n in numbers if 1 <= int(n) <= len(candidates)]
                
            elif line.startswith("Justificativa:"):
                justification = line.replace("Justificativa:", "").strip()
        
        # Selecionar documentos
        if selected_nums:
            selected_docs = [candidates[num - 1] for num in selected_nums]
            indices = [num - 1 for num in selected_nums]
        else:
            # Fallback: selecionar o primeiro
            logger.warning("Re-ranker não selecionou páginas válidas, usando fallback")
            selected_docs = [candidates[0]]
            indices = [0]
            justification = "Fallback: seleção automática do primeiro candidato"
        
        return selected_docs, justification, indices
    
    def _create_empty_result(self, query: str) -> RerankedResult:
        """Cria resultado vazio"""
        return RerankedResult(
            selected_docs=[],
            justification="Nenhum candidato disponível",
            indices=[],
            total_candidates=0,
            model=self.model,
            query=query
        )
    
    def _single_candidate_result(self, query: str, candidate: SearchResult) -> RerankedResult:
        """Resultado para único candidato"""
        return RerankedResult(
            selected_docs=[candidate],
            justification=f"Único candidato disponível: {candidate.document_name}, página {candidate.page_number}",
            indices=[0],
            total_candidates=1,
            model=self.model,
            query=query
        )
    
    def batch_rerank(self, 
                    queries_and_results: List[Tuple[str, List[SearchResult]]],
                    **kwargs) -> List[RerankedResult]:
        """
        Re-rankeia múltiplas queries em lote
        
        Args:
            queries_and_results: Lista de (query, resultados)
            **kwargs: Argumentos para rerank_results
            
        Returns:
            Lista de resultados re-rankeados
        """
        results = []
        
        for query, search_results in queries_and_results:
            try:
                reranked = self.rerank_results(query, search_results, **kwargs)
                results.append(reranked)
            except Exception as e:
                logger.error(f"Erro no re-ranking da query '{query}': {e}")
                # Adicionar resultado de erro
                results.append(self._create_empty_result(query))
        
        return results
    
    def get_rerank_config(self) -> Dict[str, Any]:
        """
        Obtém configuração atual do re-ranker
        
        Returns:
            Configuração do re-ranker
        """
        return {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "max_candidates": self.max_candidates,
            "openai_client_configured": self.openai_client is not None
        }


class SimpleReranker:
    """
    Re-ranker simples baseado apenas em similaridade
    """
    
    def __init__(self, similarity_threshold: float = 0.7):
        """
        Inicializa re-ranker simples
        
        Args:
            similarity_threshold: Threshold mínimo de similaridade
        """
        self.similarity_threshold = similarity_threshold
    
    def rerank_results(self,
                      query: str,
                      search_results: List[SearchResult],
                      max_selected: int = 2) -> RerankedResult:
        """
        Re-ranking simples baseado em similaridade
        """
        # Filtrar por threshold
        filtered_results = [
            result for result in search_results 
            if result.similarity >= self.similarity_threshold
        ]
        
        if not filtered_results:
            # Se nenhum atende o threshold, pegar os melhores
            filtered_results = search_results[:max_selected]
        
        # Selecionar os top N
        selected = filtered_results[:max_selected]
        
        # Criar justificativa
        if len(selected) == 1:
            justification = f"Documento mais similar (score: {selected[0].similarity:.3f})"
        else:
            scores = [f"{doc.similarity:.3f}" for doc in selected]
            justification = f"Top {len(selected)} documentos por similaridade (scores: {', '.join(scores)})"
        
        return RerankedResult(
            selected_docs=selected,
            justification=justification,
            indices=list(range(len(selected))),
            total_candidates=len(search_results),
            model="similarity_based",
            query=query,
            config={"similarity_threshold": self.similarity_threshold}
        )


def rerank_search_results(query: str,
                         search_results: List[SearchResult],
                         use_ai: bool = True,
                         **kwargs) -> RerankedResult:
    """
    Função de conveniência para re-ranking
    
    Args:
        query: Query original
        search_results: Resultados da busca
        use_ai: Usar IA para re-ranking
        **kwargs: Argumentos adicionais
        
    Returns:
        Resultado re-rankeado
    """
    if use_ai:
        reranker = SearchReranker(**kwargs)
    else:
        reranker = SimpleReranker(**kwargs)
    
    return reranker.rerank_results(query, search_results)