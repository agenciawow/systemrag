"""
Transformador de Queries para Sistema RAG

Converte mensagens conversacionais em queries otimizadas para busca.
"""
import logging
from typing import List, Dict, Any
from openai import OpenAI

from ...models.data_models import ProcessingStatus
from ...config.settings import settings

logger = logging.getLogger(__name__)


class QueryTransformer:
    """
    Transformador de queries otimizado para conversas
    
    Funcionalidades:
    - Classificação determinística (sem IA quando possível)
    - Cache de transformações
    - Fallbacks robustos
    - Integração com contexto conversacional
    """
    
    def __init__(self, 
                 openai_client: OpenAI = None,
                 max_cache_size: int = 1000):
        """
        Inicializa o transformador
        
        Args:
            openai_client: Cliente OpenAI (opcional)
            max_cache_size: Tamanho máximo do cache
        """
        self.openai_client = openai_client or OpenAI(api_key=settings.api.openai_api_key)
        self.max_cache_size = max_cache_size
        self.transformation_cache: Dict[str, str] = {}
        self._init_patterns()
    
    def _init_patterns(self):
        """Inicializa padrões para classificação determinística"""
        self.greeting_patterns = {
            'simple': ['oi', 'olá', 'hello', 'hi', 'hey'],
            'formal': ['bom dia', 'boa tarde', 'boa noite', 'good morning'],
            'casual': ['opa', 'salve', 'e aí']
        }
        
        self.thank_patterns = [
            'obrigado', 'obrigada', 'thanks', 'thank you', 'valeu', 
            'brigado', 'grato', 'grata'
        ]
        
        self.document_terms = [
            'zep', 'graphiti', 'rag', 'temporal', 'knowledge graph',
            'grafo', 'arquitetura', 'paper', 'documento', 'artigo',
            'tabela', 'table', 'figura', 'figure', 'performance', 
            'resultado', 'metodologia', 'algorithm', 'invalidação', 
            'memória', 'embedding', 'vector', 'similarity'
        ]
        
        self.inquiry_keywords = [
            'explique', 'explain', 'como', 'how', 'o que', 'what',
            'quais', 'which', 'where', 'onde', 'quando', 'when',
            'por que', 'why', 'porque', 'me fale', 'tell me',
            'descreva', 'describe', 'mostre', 'show', 'qual',
            'quero saber', 'want to know', 'preciso entender',
            'pode explicar', 'can you explain'
        ]
        
        self.contextual_pronouns = [
            'isso', 'isto', 'aquilo', 'ele', 'ela', 'eles', 'elas',
            'this', 'that', 'these', 'those', 'it', 'they'
        ]
    
    def transform_query(self, chat_history: List[Dict[str, str]]) -> str:
        """
        Transforma histórico de chat em query para busca
        
        Args:
            chat_history: Lista de mensagens [{role, content}]
            
        Returns:
            Query transformada ou "Not applicable"
        """
        try:
            if not chat_history:
                logger.debug("Histórico vazio, retornando 'Not applicable'")
                return "Not applicable"
            
            last_message = self._get_last_user_message(chat_history)
            if not last_message:
                logger.debug("Nenhuma mensagem de usuário encontrada")
                return "Not applicable"
            
            logger.debug(f"Processando mensagem: '{last_message[:50]}...'")
            
            # Verificar cache
            cache_key = self._create_cache_key(last_message, chat_history)
            if cache_key in self.transformation_cache:
                cached_result = self.transformation_cache[cache_key]
                logger.debug(f"Cache hit: '{cached_result[:50]}...'")
                return cached_result
            
            # Classificação determinística (sem IA)
            deterministic_result = self._deterministic_classification(last_message, chat_history)
            if deterministic_result != "NEEDS_AI":
                self._cache_result(cache_key, deterministic_result)
                logger.debug(f"Classificação determinística: '{deterministic_result[:50]}...'")
                return deterministic_result
            
            # Transformação com IA (apenas quando necessário)
            logger.debug("Usando IA para transformação complexa...")
            ai_result = self._ai_transformation(last_message, chat_history)
            self._cache_result(cache_key, ai_result)
            
            return ai_result
            
        except Exception as e:
            logger.error(f"Erro na transformação: {e}")
            return self._safe_fallback(last_message if 'last_message' in locals() else "erro")
    
    def _deterministic_classification(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Classificação determinística sem IA
        """
        message_lower = message.lower().strip()
        
        # Saudações simples
        if self._is_simple_greeting(message_lower):
            return "Not applicable"
        
        # Agradecimentos simples
        if self._is_simple_thanks(message_lower):
            return "Not applicable"
        
        # Menções diretas ao documento
        if self._mentions_document_directly(message_lower):
            return message
        
        # Perguntas gerais sobre documentos
        if self._is_general_document_inquiry(message_lower):
            return f"Sobre o documento: {message}"
        
        # Referências contextuais com contexto de documento
        if (self._has_contextual_references(message_lower) and 
            self._has_document_context(chat_history)):
            return f"Sobre o documento: {message}"
        
        # Perguntas com palavras-chave de consulta
        if self._has_inquiry_pattern(message_lower):
            return f"Sobre o documento: {message}"
        
        # Precisa de IA para contexto mais complexo
        return "NEEDS_AI"
    
    def _is_simple_greeting(self, message: str) -> bool:
        """Detecta saudações simples"""
        words = message.split()
        if len(words) <= 2:
            for pattern_group in self.greeting_patterns.values():
                if any(pattern in message for pattern in pattern_group):
                    return True
        return False
    
    def _is_simple_thanks(self, message: str) -> bool:
        """Detecta agradecimentos simples"""
        return (any(thank in message for thank in self.thank_patterns) and 
                len(message.split()) <= 3)
    
    def _mentions_document_directly(self, message: str) -> bool:
        """Verifica menções diretas a termos do documento"""
        return any(term in message for term in self.document_terms)
    
    def _is_general_document_inquiry(self, message: str) -> bool:
        """Detecta perguntas gerais sobre documentos"""
        has_inquiry = any(keyword in message for keyword in self.inquiry_keywords)
        is_question = any(char in message for char in ['?', 'qual', 'como', 'o que'])
        return has_inquiry or is_question
    
    def _has_contextual_references(self, message: str) -> bool:
        """Detecta pronomes que referenciam contexto anterior"""
        return any(pronoun in message for pronoun in self.contextual_pronouns)
    
    def _has_document_context(self, chat_history: List[Dict[str, str]]) -> bool:
        """Verifica se há contexto de documento nas mensagens recentes"""
        recent_messages = chat_history[-6:]
        
        for msg in recent_messages:
            if msg.get('role') == 'assistant':
                content = msg.get('content', '').lower()
                if any(term in content for term in ['documento', 'página', 'paper', 'artigo']):
                    return True
        return False
    
    def _has_inquiry_pattern(self, message: str) -> bool:
        """Detecta padrões de consulta"""
        return any(keyword in message for keyword in self.inquiry_keywords)
    
    def _ai_transformation(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """
        Transformação com IA - usada apenas quando necessário
        """
        try:
            # Contexto reduzido para economizar tokens
            recent_context = self._build_minimal_context(chat_history[-4:])
            
            prompt = f"""Transforme a mensagem em uma pergunta específica sobre documentos acadêmicos.

REGRAS:
1. Se menciona termos técnicos específicos, mantenha como está
2. Se é pergunta geral, adicione "Sobre o documento:"
3. Se referencia conversa anterior, combine contextos
4. Seja conciso e direto

CONTEXTO RECENTE:
{recent_context}

MENSAGEM: {message}

RESPONDA APENAS COM A PERGUNTA TRANSFORMADA:"""

            response = self.openai_client.chat.completions.create(
                model=settings.openai_models.query_transform_model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=150,
                temperature=settings.openai_models.query_transform_temperature
            )
            
            transformed = response.choices[0].message.content.strip()
            transformed = self._clean_ai_output(transformed)
            
            logger.debug(f"IA transform: '{message}' → '{transformed}'")
            return transformed
            
        except Exception as e:
            logger.error(f"Erro na transformação com IA: {e}")
            return self._safe_fallback(message)
    
    def _build_minimal_context(self, recent_messages: List[Dict[str, str]]) -> str:
        """Constrói contexto mínimo para economizar tokens"""
        context_parts = []
        
        for msg in recent_messages:
            role = msg.get('role', '')
            content = msg.get('content', '')[:100]  # Limita a 100 chars
            
            if role in ['user', 'assistant']:
                context_parts.append(f"{role.title()}: {content}")
        
        return "\n".join(context_parts)
    
    def _clean_ai_output(self, output: str) -> str:
        """Limpa saída da IA"""
        prefixes = ['rag query:', 'query:', 'pergunta:', 'question:']
        
        for prefix in prefixes:
            if output.lower().startswith(prefix):
                output = output[len(prefix):].strip()
        
        return output.strip('"\'')
    
    def _safe_fallback(self, message: str) -> str:
        """Fallback seguro quando tudo mais falha"""
        document_terms_in_message = any(term in message.lower() for term in self.document_terms)
        
        if document_terms_in_message:
            return message
        else:
            return f"Sobre o documento: {message}"
    
    def _create_cache_key(self, message: str, chat_history: List[Dict[str, str]]) -> str:
        """Cria chave de cache baseada na mensagem e contexto"""
        recent_topics = []
        for msg in chat_history[-3:]:
            content = msg.get('content', '').lower()
            if any(term in content for term in self.document_terms):
                recent_topics.append('doc_context')
        
        context_key = '+'.join(set(recent_topics))
        return f"{message.lower()[:50]}||{context_key}"
    
    def _cache_result(self, key: str, result: str):
        """Adiciona resultado ao cache com limite de tamanho"""
        if len(self.transformation_cache) >= self.max_cache_size:
            # Remove item mais antigo
            oldest_key = next(iter(self.transformation_cache))
            del self.transformation_cache[oldest_key]
        
        self.transformation_cache[key] = result
    
    def _get_last_user_message(self, chat_history: List[Dict[str, str]]) -> str:
        """Pega última mensagem do usuário"""
        for msg in reversed(chat_history):
            if msg.get("role") == "user":
                return msg.get("content", "")
        return ""
    
    def needs_rag(self, transformed_query: str) -> bool:
        """Verifica se precisa fazer busca RAG"""
        return "not applicable" not in transformed_query.lower()
    
    def clean_query(self, transformed_query: str) -> str:
        """Limpa query final"""
        return transformed_query.strip()
    
    def get_cache_stats(self) -> Dict[str, int]:
        """Estatísticas do cache para monitoramento"""
        return {
            "cache_size": len(self.transformation_cache),
            "max_cache_size": self.max_cache_size
        }


def transform_conversational_query(chat_history: List[Dict[str, str]], 
                                 openai_client: OpenAI = None) -> str:
    """
    Função de conveniência para transformar query conversacional
    
    Args:
        chat_history: Histórico de chat
        openai_client: Cliente OpenAI opcional
        
    Returns:
        Query transformada
    """
    transformer = QueryTransformer(openai_client)
    return transformer.transform_query(chat_history)