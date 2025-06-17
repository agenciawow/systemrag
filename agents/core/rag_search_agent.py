"""
Agente de Busca RAG

Agente especializado em busca e análise de documentos usando o sistema RAG.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from openai import OpenAI
from agents.tools.retrieval_tool import RetrievalTool
from agents.core.zep_client import get_zep_client, is_zep_available, ZepMessage
from system_rag.config.settings import settings

logger = logging.getLogger(__name__)


class RAGSearchAgent:
    """
    Agente especializado em busca RAG
    
    Funcionalidades:
    - Busca inteligente em documentos
    - Análise contextual de resultados
    - Geração de respostas baseadas em evidências
    - Suporte a imagens e multimodalidade
    - Conversação com histórico
    """
    
    # Metadados para descoberta automática
    name = "RAG Search Agent"
    agent_id = "rag-search"
    description = "Agente especializado em busca e análise de documentos acadêmicos e técnicos"
    
    def __init__(self,
                 max_candidates: int = 10,
                 max_selected: int = 2,
                 enable_reranking: bool = True,
                 enable_image_analysis: bool = True):
        """
        Inicializa o agente de busca RAG
        
        Args:
            max_candidates: Máximo de candidatos da busca
            max_selected: Máximo de documentos selecionados
            enable_reranking: Habilitar re-ranking inteligente
            enable_image_analysis: Habilitar análise de imagens
        """
        self.max_candidates = max_candidates
        self.max_selected = max_selected
        self.enable_reranking = enable_reranking
        self.enable_image_analysis = enable_image_analysis
        
        # Histórico da conversa
        self.chat_history: List[Dict[str, str]] = []
        
        # Inicializar tool de retrieval
        self.retrieval_tool = RetrievalTool(
            max_candidates=max_candidates,
            max_selected=max_selected,
            enable_reranking=enable_reranking,
            enable_image_fetching=enable_image_analysis
        )
        
        # Cliente OpenAI para geração de respostas
        if not settings.api.openai_api_key:
            raise ValueError("OpenAI API key não encontrada nas configurações")
        self.openai_client = OpenAI(api_key=settings.api.openai_api_key)
        
        logger.info(f"Agente {self.name} inicializado com sucesso")
    
    def ask(self, user_message: str, user_id: Optional[str] = None, session_id: Optional[str] = None) -> str:
        """
        Interface principal do agente com suporte a memória Zep
        
        Args:
            user_message: Mensagem do usuário
            user_id: ID do usuário (para gerenciamento de memória)
            session_id: ID da sessão (para gerenciamento de memória)
            
        Returns:
            Resposta do agente
        """
        try:
            logger.info(f"[{self.agent_id}] Processando: {user_message}")
            
            # FLUXO ZEP: Verificar usuário → verificar sessão → buscar contexto → adicionar mensagem
            memory_context = ""
            zep_messages = []
            is_new_session = True
            
            if user_id and session_id and is_zep_available():
                try:
                    zep_client = get_zep_client()
                    
                    # 1. Garantir usuário e sessão existem + buscar contexto
                    memory_context, zep_messages, is_new_session = zep_client.ensure_session_context(session_id, user_id)
                    logger.info(f"[{self.agent_id}] Contexto Zep: {len(memory_context)} chars, {len(zep_messages)} msgs, nova={is_new_session}")
                    
                    # 2. Adicionar mensagem do usuário à memória
                    user_messages = [ZepMessage(content=user_message, role_type="user")]
                    zep_client.add_memory_to_session(session_id, user_messages, user_id)
                    logger.info(f"[{self.agent_id}] ✅ Mensagem do usuário adicionada ao Zep")
                    
                except Exception as e:
                    logger.warning(f"[{self.agent_id}] ❌ Erro no fluxo Zep: {e}")
                    # Continuar sem Zep em caso de erro
            
            # Adicionar mensagem ao histórico local
            self.chat_history.append({"role": "user", "content": user_message})
            
            # Usar tool de retrieval para buscar documentos
            search_result = self.retrieval_tool.search_documents(
                query=user_message,
                chat_history=self.chat_history[:-1]  # Histórico sem a mensagem atual
            )
            
            if not search_result.success:
                logger.warning(f"[{self.agent_id}] Busca falhou: {search_result.error}")
                response = self._handle_search_error(search_result.error)
            elif not search_result.query_info.get("needs_rag", True):
                # Query simples que não precisa de RAG
                response = self._generate_simple_response(user_message)
            else:
                # Gerar resposta baseada nos documentos encontrados com contexto de memória
                response = self._generate_document_response(
                    user_message,
                    search_result.documents,
                    search_result.query_info,
                    memory_context,
                    zep_messages
                )
            
            # Adicionar resposta ao histórico local
            self.chat_history.append({"role": "assistant", "content": response})
            
            # 3. Adicionar resposta do assistente à memória Zep
            if user_id and session_id and is_zep_available():
                try:
                    zep_client = get_zep_client()
                    assistant_messages = [ZepMessage(content=response, role_type="assistant")]
                    zep_client.add_memory_to_session(session_id, assistant_messages, user_id)
                    logger.info(f"[{self.agent_id}] ✅ Resposta do assistente adicionada ao Zep")
                except Exception as e:
                    logger.warning(f"[{self.agent_id}] ❌ Erro ao adicionar resposta ao Zep: {e}")
            
            # Limitar tamanho do histórico local
            self._limit_history()
            
            logger.info(f"[{self.agent_id}] Resposta gerada com sucesso")
            return response
            
        except Exception as e:
            logger.error(f"[{self.agent_id}] Erro no processamento: {e}")
            return "Desculpe, ocorreu um erro interno. Tente novamente."
    
    def _generate_simple_response(self, query: str) -> str:
        """Gera resposta simples para queries que não precisam de RAG"""
        greetings = ["oi", "olá", "hello", "hi", "boa tarde", "bom dia", "boa noite"]
        thanks = ["obrigado", "obrigada", "thanks", "valeu"]
        
        if any(greeting in query.lower() for greeting in greetings):
            return "Olá! Sou seu assistente especializado em busca de documentos. Como posso ajudar você hoje?"
        elif any(thank in query.lower() for thank in thanks):
            return "De nada! Fico feliz em ajudar. Há mais alguma coisa que gostaria de saber?"
        else:
            return "Como posso ajudar você com consultas sobre os documentos? Faça uma pergunta específica e eu buscarei as informações relevantes."
    
    def _generate_document_response(self, 
                                  query: str,
                                  documents: List[Dict[str, Any]],
                                  query_info: Dict[str, Any],
                                  memory_context: str = "",
                                  zep_messages: List[Dict[str, Any]] = None) -> str:
        """
        Gera resposta baseada nos documentos encontrados
        
        Args:
            query: Query original do usuário
            documents: Documentos encontrados pela busca
            query_info: Informações sobre a query processada
            
        Returns:
            Resposta gerada pelo agente
        """
        try:
            # Construir contexto da conversa se disponível
            conversation_context = ""
            
            if memory_context:
                conversation_context += f"CONTEXTO DA CONVERSA:\n{memory_context}\n"
            
            if zep_messages and len(zep_messages) > 0:
                conversation_context += "HISTÓRICO RECENTE:\n"
                for msg in zep_messages[-5:]:  # Últimas 5 mensagens
                    role = msg.get('role_type', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user':
                        conversation_context += f"Usuário: {content}\n"
                    elif role == 'assistant':
                        conversation_context += f"Assistente: {content}\n"
                conversation_context += "\n"
            
            # Instruções base para o agente
            base_instructions = (
                "Você é um assistente especializado em análise de documentos acadêmicos e técnicos. "
                "Analise os documentos fornecidos e responda à pergunta de forma clara e precisa. "
                "Sempre cite as fontes específicas (documento e página). "
                "NÃO use formatação Markdown como **, _, #. Escreva texto corrido natural. "
                "Use o contexto da conversa anterior para fornecer respostas mais personalizadas e coerentes."
            )
            
            if len(documents) == 1:
                # Resposta baseada em um documento
                doc = documents[0]
                
                prompt = (
                    f"{base_instructions}\n\n"
                    f"{conversation_context}"
                    f"PERGUNTA ATUAL: {query}\n\n"
                    f"Use APENAS o documento '{doc['document_name']}', página {doc['page_number']}.\n"
                    f"Conteúdo:\n{doc['content']}\n\n"
                    f"Instruções: Responda de forma clara e direta considerando o contexto da conversa. "
                    f"Cite a fonte: documento '{doc['document_name']}', página {doc['page_number']}."
                )
                
                content = [{"type": "text", "text": prompt}]
                
                # Adicionar imagem se disponível
                if doc.get("image_base64") and self.enable_image_analysis:
                    content.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{doc['image_base64']}"}
                    })
            
            else:
                # Resposta baseada em múltiplos documentos
                sources = " e ".join(
                    f"{doc['document_name']} p.{doc['page_number']}"
                    for doc in documents
                )
                
                combined_content = "\n\n".join(
                    f"=== {doc['document_name']} - PÁGINA {doc['page_number']} ===\n{doc['content']}"
                    for doc in documents
                )
                
                prompt = (
                    f"{base_instructions}\n\n"
                    f"{conversation_context}"
                    f"PERGUNTA ATUAL: {query}\n\n"
                    f"Use os documentos: {sources}\n\n"
                    f"Conteúdo:\n{combined_content}\n\n"
                    f"Instruções: Integre as informações dos documentos considerando o contexto da conversa e cite todas as fontes utilizadas."
                )
                
                content = [{"type": "text", "text": prompt}]
                
                # Adicionar imagens se disponíveis e análise habilitada
                if self.enable_image_analysis:
                    for doc in documents:
                        if doc.get("image_base64"):
                            content.append({
                                "type": "text", 
                                "text": f"\n--- IMAGEM DA PÁGINA {doc['page_number']} ---"
                            })
                            content.append({
                                "type": "image_url",
                                "image_url": {"url": f"data:image/png;base64,{doc['image_base64']}"}
                            })
            
            # Gerar resposta com OpenAI
            try:
                response = self.openai_client.chat.completions.create(
                    model=settings.openai_models.answer_generation_model,
                    messages=[{"role": "user", "content": content}],
                    max_tokens=2048,
                    temperature=settings.openai_models.answer_generation_temperature
                )
                
                answer = response.choices[0].message.content
                
            except Exception as e:
                logger.error(f"Erro ao gerar resposta com OpenAI: {e}")
                answer = f"Desculpe, não consegui processar sua pergunta no momento. Com base na busca, encontrei informações sobre: {', '.join([doc.get('title', 'documento') for doc in documents[:3]])}. Tente reformular sua pergunta."
            
            # Adicionar informação sobre o processo de busca se relevante
            if query_info.get("reranking_enabled") and len(documents) > 1:
                justification = query_info.get("justification", "")
                if justification and "reranked" in justification.lower():
                    answer += f"\n\n[Informação processada através de análise inteligente de {query_info.get('total_candidates', 0)} documentos candidatos]"
            
            return answer
            
        except Exception as e:
            logger.error(f"Erro ao gerar resposta: {e}")
            return f"Encontrei informações relevantes, mas ocorreu um erro ao processar a resposta. Erro: {e}"
    
    def _handle_search_error(self, error: str) -> str:
        """Trata erros de busca de forma amigável"""
        if "não foi encontrada" in error.lower():
            return "Não encontrei informações específicas sobre sua pergunta nos documentos disponíveis. Você poderia reformular a pergunta ou ser mais específico?"
        elif "embedding" in error.lower():
            return "Ocorreu um problema técnico com o processamento da sua pergunta. Tente novamente em alguns instantes."
        elif "ambiente" in error.lower():
            return "Existe um problema de configuração do sistema. Por favor, contate o administrador."
        else:
            return f"Ocorreu um erro na busca: {error}. Tente reformular sua pergunta."
    
    def _limit_history(self, max_messages: int = 20):
        """Limita o tamanho do histórico de conversa"""
        if len(self.chat_history) > max_messages:
            # Manter as mensagens mais recentes
            self.chat_history = self.chat_history[-max_messages:]
            logger.debug(f"Histórico limitado para {max_messages} mensagens")
    
    def clear_history(self):
        """Limpa o histórico de conversa"""
        self.chat_history = []
        logger.info(f"[{self.agent_id}] Histórico limpo")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Retorna o histórico atual da conversa"""
        return self.chat_history.copy()
    
    def get_agent_stats(self) -> Dict[str, Any]:
        """Obtém estatísticas do agente"""
        stats = {
            "agent_info": {
                "name": self.name,
                "agent_id": self.agent_id,
                "description": self.description
            },
            "chat_history_length": len(self.chat_history),
            "config": {
                "max_candidates": self.max_candidates,
                "max_selected": self.max_selected,
                "reranking_enabled": self.enable_reranking,
                "image_analysis_enabled": self.enable_image_analysis
            },
            "last_interaction": datetime.now().isoformat() if self.chat_history else None
        }
        
        # Adicionar estatísticas da tool de retrieval
        try:
            retrieval_stats = self.retrieval_tool.get_stats()
            stats["retrieval_tool"] = retrieval_stats
        except Exception as e:
            stats["retrieval_tool"] = {"error": str(e)}
        
        return stats
    
    def test_agent(self) -> Dict[str, Any]:
        """Testa a funcionalidade do agente"""
        try:
            # Testar tool de retrieval
            tool_test = self.retrieval_tool.test_connection()
            
            # Teste básico de geração de resposta
            test_query = "teste de funcionamento"
            try:
                test_response = self._generate_simple_response(test_query)
                response_test = True
            except Exception as e:
                response_test = f"Erro: {e}"
            
            return {
                "agent_status": "operational",
                "retrieval_tool": tool_test,
                "response_generation": response_test,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                "agent_status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }