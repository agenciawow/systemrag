"""
Sistema RAG Conversacional Modular

Sistema de busca conversacional usando a arquitetura modular e Cloudflare R2.
Substitui o código do exemplo.py com uma implementação mais limpa e modular.
"""
import os
import logging
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

from openai import OpenAI

from .retrieval import RAGPipeline
from ..config.settings import settings

# Configurações do sistema
# LLM_MODEL agora vem das configurações
MAX_CANDIDATES = 5
MAX_SELECTED = 2
COLLECTION_NAME = "agenciawow"


def setup_rag_logging():
    """Configura logging específico para o RAG com rotação automática"""
    from logging.handlers import RotatingFileHandler
    
    # Rotaciona log se estiver muito grande
    log_file = "rag_modular_debug.log"
    if os.path.exists(log_file):
        file_size = os.path.getsize(log_file) / (1024 * 1024)  # MB
        if file_size > 100:  # Se maior que 100MB
            import shutil
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{log_file}.{timestamp}.bak"
            shutil.move(log_file, backup_name)
    
    rag_logger = logging.getLogger(__name__)
    rag_logger.setLevel(logging.INFO)
    
    # Remove handlers existentes para evitar duplicação
    for handler in rag_logger.handlers[:]:
        rag_logger.removeHandler(handler)
    
    # Formatter detalhado
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
    )
    
    # Handler para console (apenas WARNING e acima)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_handler.setFormatter(formatter)
    rag_logger.addHandler(console_handler)
    
    # Handler rotativo para arquivo do RAG (máximo 50MB, 5 backups)
    file_handler = RotatingFileHandler(
        "rag_modular_debug.log",
        maxBytes=50*1024*1024,  # 50MB
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    rag_logger.addHandler(file_handler)
    
    # Não propagar para o logger pai para evitar duplicação
    rag_logger.propagate = False
    
    return rag_logger


logger = setup_rag_logging()


def get_sao_paulo_time():
    """Retorna datetime atual no fuso horário de São Paulo"""
    return datetime.now(ZoneInfo("America/Sao_Paulo"))


class ModularConversationalRAG:
    """
    Sistema RAG conversacional usando arquitetura modular
    
    Funcionalidades:
    - Pipeline RAG modular
    - Suporte a imagens do Cloudflare R2
    - Histórico conversacional
    - Logging estruturado
    - Fallbacks robustos
    """
    
    def __init__(self) -> None:
        """Inicializa com configurações do sistema"""
        load_dotenv()
        
        # Validação de ambiente
        required_vars = [
            "VOYAGE_API_KEY", "OPENAI_API_KEY",
            "ASTRA_DB_API_ENDPOINT", "ASTRA_DB_APPLICATION_TOKEN"
        ]
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Variáveis de ambiente ausentes: {missing_vars}")
        
        # Inicialização do cliente OpenAI
        self.openai_client = OpenAI()
        
        # Histórico da conversa
        self.chat_history: List[Dict[str, str]] = []
        
        # Inicializar pipeline RAG modular
        self._initialize_rag_pipeline()
        
        logger.info("Sistema RAG modular inicializado com sucesso")
    
    def _initialize_rag_pipeline(self):
        """Inicializa o pipeline RAG modular"""
        try:
            logger.info("Inicializando pipeline RAG modular...")
            
            # Configurar pipeline com imagens do R2 habilitadas
            self.rag_pipeline = RAGPipeline(
                openai_client=self.openai_client,
                max_candidates=MAX_CANDIDATES,
                max_selected=MAX_SELECTED,
                enable_reranking=True,
                enable_image_fetching=True  # Habilita busca de imagens do R2
            )
            
            # Testar pipeline
            test_result = self.rag_pipeline.test_pipeline()
            if test_result.success:
                logger.info("Pipeline RAG testado com sucesso")
            else:
                logger.warning(f"Alguns componentes do pipeline falharam: {test_result.details}")
                
        except Exception as e:
            logger.error(f"Falha ao inicializar pipeline RAG: {e}")
            raise
    
    def ask(self, user_message: str) -> str:
        """Interface conversacional principal"""
        import time
        start_time = time.time()
        
        logger.info(f"[ASK] === INICIANDO PROCESSAMENTO ===")
        logger.info(f"[ASK] Pergunta do usuário: {user_message}")
        
        try:
            # Adiciona mensagem do usuário ao histórico
            self.chat_history.append({"role": "user", "content": user_message})
            logger.debug(f"[ASK] Mensagem adicionada ao histórico. Total: {len(self.chat_history)} mensagens")
            
            # Usar o pipeline RAG modular
            logger.info(f"[ASK] 🔄 Executando pipeline RAG modular...")
            rag_start = time.time()
            
            result = self.rag_pipeline.search_and_answer(
                query=user_message,
                chat_history=self.chat_history[:-1]  # Histórico sem a mensagem atual
            )
            
            rag_time = time.time() - rag_start
            
            if "error" in result:
                logger.warning(f"[ASK] ❌ Pipeline retornou erro em {rag_time:.2f}s: {result['error']}")
                response = f"Desculpe, não consegui encontrar informações sobre isso. {result['error']}"
            else:
                logger.info(f"[ASK] ✅ Pipeline completado em {rag_time:.2f}s")
                
                if result.get("requires_rag", True):
                    # Resposta baseada em documentos
                    logger.info(f"[ASK] 📊 Páginas selecionadas: {result.get('selected_pages_count', 0)}")
                    logger.info(f"[ASK] 📚 Fonte: {result.get('selected_pages', 'N/A')}")
                else:
                    # Resposta conversacional simples
                    logger.info(f"[ASK] 💬 Resposta conversacional simples")
                
                response = result["answer"]
            
            # Limita histórico para controle de memória
            if len(self.chat_history) > 20:
                old_len = len(self.chat_history)
                self.chat_history = self.chat_history[-16:]
                logger.debug(f"[ASK] Histórico limitado: {old_len} -> {len(self.chat_history)} mensagens")
            
            total_time = time.time() - start_time
            logger.info(f"[ASK] ✅ === PROCESSAMENTO COMPLETO em {total_time:.2f}s ===")
            
            return response
            
        except Exception as e:
            error_time = time.time() - start_time
            logger.error(f"[ASK] ❌ Erro no processamento após {error_time:.2f}s: {e}", exc_info=True)
            return "Desculpe, ocorreu um erro interno. Tente novamente."
    
    def search_and_answer(self, query: str) -> dict:
        """
        Interface direta para busca (compatibilidade com código existente)
        """
        result = self.rag_pipeline.search_and_answer(
            query=query,
            chat_history=self.chat_history
        )
        return result
    
    def extract_structured_data(self, template: dict, document_filter: Optional[str] = None) -> dict:
        """
        Extração de dados estruturados usando o pipeline modular
        """
        try:
            # Buscar documentos relevantes
            if document_filter:
                search_query = f"informações sobre {document_filter}"
            else:
                search_query = "extrair dados estruturados"
            
            # Usar o pipeline para buscar documentos
            result = self.rag_pipeline.search_and_answer(search_query)
            
            if "error" in result:
                return {"error": result["error"]}
            
            # Preparar dados para extração
            selected_docs = result.get("selected_pages_details", [])
            
            if not selected_docs:
                return {"error": "Nenhum documento encontrado para extração"}
            
            # Usar OpenAI para extrair dados estruturados
            import json
            
            template_str = json.dumps(template, indent=2)
            
            content = [{
                "type": "text",
                "text": f"""
Extraia dados estruturados seguindo este template: {template_str}

Se informação não disponível, deixe em branco.
Responda APENAS com JSON válido.

DOCUMENTOS ANALISADOS:"""
            }]
            
            # Adicionar informações dos documentos selecionados
            for doc_info in selected_docs[:3]:  # Limitar a 3 documentos
                content.append({
                    "type": "text",
                    "text": f"\n=== {doc_info['document'].upper()} - PÁGINA {doc_info['page_number']} ===\n"
                })
            
            response = self.openai_client.chat.completions.create(
                model=settings.openai_models.extraction_model,
                messages=[{"role": "user", "content": content}],
                response_format={"type": "json_object"},
                temperature=settings.openai_models.extraction_temperature
            )
            
            extracted_data = json.loads(response.choices[0].message.content)
            
            return {
                "status": "success",
                "data": extracted_data,
                "pages_analyzed": len(selected_docs)
            }
            
        except Exception as e:
            logger.error(f"Erro na extração de dados: {e}")
            return {
                "status": "error",
                "message": f"Erro na extração: {e}"
            }
    
    def clear_history(self):
        """Limpa histórico da conversa"""
        self.chat_history = []
        logger.info("Histórico de conversa limpo")
    
    def get_chat_history(self) -> List[Dict[str, str]]:
        """Retorna histórico atual"""
        return self.chat_history.copy()
    
    def get_system_stats(self) -> Dict[str, Any]:
        """Estatísticas do sistema para monitoramento"""
        stats = {
            "chat_history_length": len(self.chat_history),
            "system_health": "operational"
        }
        
        try:
            # Estatísticas do pipeline
            pipeline_stats = self.rag_pipeline.get_pipeline_stats()
            stats.update(pipeline_stats)
            
        except Exception as e:
            stats["pipeline_error"] = str(e)
            stats["system_health"] = "degraded"
        
        return stats


# Wrapper para compatibilidade com código existente
class ProductionConversationalRAG(ModularConversationalRAG):
    """Alias para compatibilidade com código existente"""
    pass


class ConversationalMultimodalRAG(ModularConversationalRAG):
    """Alias para compatibilidade com código existente"""
    pass


# Classe simples para interface externa
class SimpleRAG:
    """Interface simplificada para uso externo"""
    
    def __init__(self):
        self.rag = ModularConversationalRAG()
    
    def search(self, query: str) -> str:
        """Busca simples"""
        return self.rag.ask(query)
    
    def extract(self, template: dict, document: str = None) -> dict:
        """Extrai dados estruturados"""
        return self.rag.extract_structured_data(template, document)
    
    def clear_chat(self):
        """Limpa histórico"""
        self.rag.clear_history()


# Interface CLI otimizada
def main() -> None:
    """Interface CLI com o sistema modular"""
    try:
        rag = ModularConversationalRAG()
        
        print("🚀 SISTEMA RAG CONVERSACIONAL MODULAR 🚀")
        print("=" * 70)
        print("✨ Funcionalidades:")
        print("  • Arquitetura modular")
        print("  • Imagens do Cloudflare R2")
        print("  • Query transformer inteligente")
        print("  • Re-ranking com IA")
        print("  • Logging estruturado")
        print("=" * 70)

        print(rag.ask("Olá!"))
        print()

        while True:
            try:
                user_input = input("💬 Você: ").strip()
                
                if user_input.lower() in {"sair", "exit", "quit", "/quit"}:
                    print("👋 Até logo!")
                    break
                
                if not user_input:
                    continue
                
                # Comandos especiais
                if user_input.startswith("/"):
                    if user_input == "/help":
                        print_modular_help()
                    elif user_input == "/clear":
                        rag.clear_history()
                        print("🧹 Histórico limpo!")
                    elif user_input == "/stats":
                        stats = rag.get_system_stats()
                        print("📊 Estatísticas do sistema:")
                        for key, value in stats.items():
                            print(f"  {key}: {value}")
                    elif user_input.startswith("/extract"):
                        handle_modular_extract_command(rag, user_input)
                    else:
                        print("❓ Comando não reconhecido. Digite /help")
                    continue

                # Resposta normal
                print("\n🤖 Assistente: ", end="")
                try:
                    response = rag.ask(user_input)
                    print(response)
                except Exception as e:
                    logger.error(f"Erro no processamento: {e}")
                    print("❌ Erro temporário. Tente novamente.")
                print()

            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                logger.error(f"Erro na interface: {e}")
                print("❌ Erro na interface. Continuando...")

    except Exception as e:
        logger.critical(f"Erro fatal: {e}")
        print(f"❌ Erro fatal na inicialização: {e}")
        print("Verifique:")
        print("1. Arquivo .env com chaves corretas")
        print("2. Conexão com Astra DB")
        print("3. Documentos indexados")
        print("4. Configuração do Cloudflare R2")


def print_modular_help():
    """Ajuda do sistema modular"""
    print("""
📚 COMANDOS:
• /help     - Esta ajuda
• /clear    - Limpa histórico
• /stats    - Estatísticas do sistema
• /extract  - Extração de dados
  Exemplo: /extract {"title": "", "authors": []}

💡 RECURSOS MODULARES:
• Query Transformer (cache + IA)
• Vector Searcher (Astra DB)
• Image Fetcher (Cloudflare R2)
• Re-ranker inteligente (GPT-4)
• Pipeline configurável

🔍 TIPOS DE CONSULTA SUPORTADOS:
• Perguntas sobre documentos específicos
• Referências contextuais na conversa
• Consultas técnicas multimodais
• Extração de dados estruturados
""")


def handle_modular_extract_command(rag, command):
    """Manipula extração de dados do sistema modular"""
    try:
        if len(command.split(" ", 1)) < 2:
            print("💡 Uso: /extract {\"campo\": \"valor\"}")
            print("📝 Exemplo: /extract {\"title\": \"\", \"methodology\": \"\"}")
            return
        
        template_str = command.split(" ", 1)[1]
        import json
        template = json.loads(template_str)
        
        print("🔍 Extraindo dados com sistema modular...")
        result = rag.extract_structured_data(template)
        
        if result.get("status") == "success":
            print("✅ Extração bem-sucedida:")
            print(json.dumps(result["data"], indent=2, ensure_ascii=False))
            print(f"📊 Páginas analisadas: {result['pages_analyzed']}")
        else:
            print(f"❌ Erro: {result.get('message')}")
            
    except json.JSONDecodeError:
        print("❌ JSON inválido. Use aspas duplas!")
    except Exception as e:
        logger.error(f"Erro na extração: {e}")
        print(f"❌ Erro: {e}")


# Para monitoramento do sistema
def health_check() -> Dict[str, str]:
    """Health check para monitoramento do sistema modular"""
    try:
        rag = ModularConversationalRAG()
        
        # Testar pipeline
        test_result = rag.rag_pipeline.test_pipeline()
        
        return {
            "status": "healthy" if test_result.success else "degraded",
            "pipeline_test": "passed" if test_result.success else "failed",
            "details": str(test_result.details),
            "timestamp": get_sao_paulo_time().isoformat()
        }
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": get_sao_paulo_time().isoformat()
        }


# Aliases para compatibilidade
MultimodalRagSearcher = ModularConversationalRAG
EnhancedMultimodalRagSearcher = ModularConversationalRAG

__all__ = [
    'ModularConversationalRAG',
    'ProductionConversationalRAG', 
    'ConversationalMultimodalRAG',
    'SimpleRAG', 
    'MultimodalRagSearcher',
    'EnhancedMultimodalRagSearcher',
    'health_check'
]


if __name__ == "__main__":
    main()