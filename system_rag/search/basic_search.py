"""
Exemplo Básico de Uso do Sistema de Busca

Demonstra como usar o sistema RAG modular para diferentes tipos de busca.
"""
import os
from dotenv import load_dotenv

from ..components.retrieval import RAGPipeline, create_rag_pipeline
from ..components.embeddings.voyage_embedder import VoyageEmbedder
from .conversational_rag import SimpleRAG


def exemplo_pipeline_direto():
    """Exemplo usando o pipeline RAG diretamente"""
    print("=== Exemplo: Pipeline RAG Direto ===")
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    # Criar pipeline
    pipeline = create_rag_pipeline(
        max_candidates=5,
        max_selected=2,
        enable_reranking=True,
        enable_image_fetching=True
    )
    
    # Fazer busca
    query = "Como funciona o sistema Zep?"
    print(f"Query: {query}")
    
    result = pipeline.search_and_answer(query)
    
    if "error" in result:
        print(f"Erro: {result['error']}")
    else:
        print(f"Resposta: {result['answer']}")
        print(f"Documentos usados: {result['selected_pages']}")
        print(f"Justificativa: {result['justification']}")


def exemplo_interface_simples():
    """Exemplo usando a interface simplificada"""
    print("\n=== Exemplo: Interface Simples ===")
    
    # Criar interface simples
    rag = SimpleRAG()
    
    # Fazer perguntas
    perguntas = [
        "Olá!",
        "O que é o Zep?",
        "Como ele funciona?",
        "Obrigado!"
    ]
    
    for pergunta in perguntas:
        print(f"\nUsuário: {pergunta}")
        resposta = rag.search(pergunta)
        print(f"Assistente: {resposta}")


def exemplo_busca_com_contexto():
    """Exemplo de busca conversacional com contexto"""
    print("\n=== Exemplo: Busca com Contexto ===")
    
    # Criar pipeline
    pipeline = RAGPipeline()
    
    # Simular uma conversa
    chat_history = [
        {"role": "user", "content": "O que é o Zep?"},
        {"role": "assistant", "content": "O Zep é um sistema de..."},
        {"role": "user", "content": "Como ele se compara com outros sistemas?"}
    ]
    
    # Nova pergunta com contexto
    nova_query = "E sobre sua performance?"
    
    result = pipeline.search_and_answer(
        query=nova_query,
        chat_history=chat_history
    )
    
    if "error" not in result:
        print(f"Query original: {nova_query}")
        print(f"Query transformada: {result.get('transformed_query', nova_query)}")
        print(f"Resposta: {result['answer']}")


def exemplo_extracao_dados():
    """Exemplo de extração de dados estruturados"""
    print("\n=== Exemplo: Extração de Dados ===")
    
    # Criar interface simples
    rag = SimpleRAG()
    
    # Template para extração
    template = {
        "title": "",
        "authors": [],
        "main_concepts": [],
        "performance_metrics": {}
    }
    
    print("Extraindo dados estruturados...")
    result = rag.extract(template)
    
    if result.get("status") == "success":
        print("Dados extraídos:")
        import json
        print(json.dumps(result["data"], indent=2, ensure_ascii=False))
    else:
        print(f"Erro na extração: {result.get('message')}")


def exemplo_componentes_individuais():
    """Exemplo usando componentes individuais"""
    print("\n=== Exemplo: Componentes Individuais ===")
    
    from ..components.retrieval import QueryTransformer, VectorSearcher
    
    # 1. Transformador de queries
    transformer = QueryTransformer()
    
    chat_history = [
        {"role": "user", "content": "Me fale sobre o Zep"},
        {"role": "assistant", "content": "O Zep é um sistema..."},
        {"role": "user", "content": "Como funciona isso?"}
    ]
    
    transformed = transformer.transform_query(chat_history)
    print(f"Query transformada: {transformed}")
    
    # 2. Busca vetorial
    if transformer.needs_rag(transformed):
        print("Query precisa de RAG, fazendo busca...")
        
        # Gerar embedding
        embedder = VoyageEmbedder()
        query_embedding = embedder.embed_query(transformed)
        
        if query_embedding:
            # Buscar documentos
            searcher = VectorSearcher(max_results=3)
            search_results = searcher.search_by_text(
                transformed, 
                query_embedding.embedding
            )
            
            print(f"Encontrados {search_results.total_results} documentos:")
            for i, doc in enumerate(search_results.documents[:2]):
                print(f"  {i+1}. {doc.document_name} (p.{doc.page_number}) - Score: {doc.similarity:.3f}")


def exemplo_monitoramento():
    """Exemplo de monitoramento do sistema"""
    print("\n=== Exemplo: Monitoramento ===")
    
    # Criar pipeline
    pipeline = RAGPipeline()
    
    # Testar componentes
    test_result = pipeline.test_pipeline()
    print(f"Teste do pipeline: {'✅ Sucesso' if test_result.success else '❌ Falha'}")
    print(f"Detalhes: {test_result.details}")
    
    # Estatísticas
    stats = pipeline.get_pipeline_stats()
    print("\nEstatísticas do sistema:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Executa todos os exemplos"""
    print("🚀 EXEMPLOS DO SISTEMA RAG MODULAR 🚀")
    print("=" * 50)
    
    try:
        # Verificar variáveis de ambiente
        required_vars = ["VOYAGE_API_KEY", "OPENAI_API_KEY", "ASTRA_DB_API_ENDPOINT"]
        missing = [var for var in required_vars if not os.getenv(var)]
        
        if missing:
            print(f"❌ Variáveis de ambiente ausentes: {missing}")
            print("Configure o arquivo .env antes de executar os exemplos.")
            return
        
        # Executar exemplos
        exemplo_pipeline_direto()
        exemplo_interface_simples()
        exemplo_busca_com_contexto()
        exemplo_extracao_dados()
        exemplo_componentes_individuais()
        exemplo_monitoramento()
        
        print("\n✅ Todos os exemplos executados com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro ao executar exemplos: {e}")
        print("Verifique se todos os serviços estão configurados corretamente.")


if __name__ == "__main__":
    main()