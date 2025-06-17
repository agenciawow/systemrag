#!/usr/bin/env python3
"""Script para testar busca sem interface interativa"""

import os
from dotenv import load_dotenv

def main():
    print("🔍 Sistema de Busca RAG Completo")
    print("=" * 45)
    
    # Carregar variáveis de ambiente
    load_dotenv()
    
    try:
        # Importar o pipeline completo
        from system_rag.search.retrieval import RAGPipeline
        from openai import OpenAI
        
        print("✅ Sistema carregado!")
        
        # Inicializar OpenAI e RAG Pipeline completo
        openai_client = OpenAI()
        
        # Pipeline completo com rerank + OpenAI + imagens R2
        rag_pipeline = RAGPipeline(
            openai_client=openai_client,
            max_candidates=5,        # Busca 5 candidatos
            max_selected=2,          # Seleciona os 2 melhores após rerank
            enable_reranking=True,   # Habilita rerank com IA
            enable_image_fetching=True  # Busca imagens do R2
        )
        
        # Testar pipeline
        test_result = rag_pipeline.test_pipeline()
        print(f"🔗 Pipeline: {'✅' if test_result.success else '❌'}")
        
        if not test_result.success:
            print(f"⚠️  Alguns componentes falharam: {test_result.details}")
        
        # Listar documentos disponíveis
        try:
            from system_rag.search.retrieval import VectorSearcher
            searcher = VectorSearcher()
            docs = searcher.list_documents()
            print(f"📄 Documentos: {len(docs)}")
            for doc in docs:
                print(f"   - {doc['document_name']} (página {doc['page_number']})")
        except:
            print("📄 Documentos: Verificando...")
        
        print("\n🎯 Sistema RAG Completo:")
        print("   • Busca vetorial com embeddings")
        print("   • Rerank inteligente com IA") 
        print("   • Resposta contextualizada da OpenAI")
        print("   • Imagens do Cloudflare R2")
        
        print("\n💡 Digite sua pergunta (ou 'sair' para encerrar)")
        print("   Exemplos: 'Qual o preço do hambúrguer?', 'Que sobremesas vocês têm?'")
        
        # Histórico da conversa para contexto
        chat_history = []
        
        while True:
            try:
                # Receber pergunta do usuário
                pergunta = input("\n🔍 Sua pergunta: ").strip()
                
                if not pergunta:
                    continue
                    
                if pergunta.lower() in ['sair', 'exit', 'quit']:
                    print("👋 Até logo!")
                    break
                
                print(f"🔎 Processando: '{pergunta}'")
                print("⏳ Buscando → Reranking → Respondendo...")
                
                # Usar pipeline completo
                result = rag_pipeline.search_and_answer(
                    query=pergunta,
                    chat_history=chat_history
                )
                
                if "error" in result:
                    print(f"❌ Erro: {result['error']}")
                    continue
                
                # Mostrar resposta da IA
                print(f"\n🤖 Resposta:")
                print(f"{result['answer']}")
                
                # Mostrar fontes utilizadas
                if result.get('selected_pages_details'):
                    print(f"\n📚 Fontes utilizadas:")
                    for i, doc in enumerate(result['selected_pages_details'], 1):
                        print(f"   {i}. {doc['document']} - página {doc['page_number']}")
                        if doc.get('image_url'):
                            print(f"      🖼️  {doc['image_url']}")
                
                # Mostrar justificativa do rerank (se disponível)
                if result.get('justification'):
                    print(f"\n💭 Justificativa: {result['justification']}")
                
                # Adicionar ao histórico para contexto
                chat_history.append({"role": "user", "content": pergunta})
                chat_history.append({"role": "assistant", "content": result['answer']})
                
                # Limitar histórico para não crescer muito
                if len(chat_history) > 10:
                    chat_history = chat_history[-8:]
                    
            except KeyboardInterrupt:
                print("\n👋 Até logo!")
                break
            except Exception as e:
                print(f"❌ Erro: {e}")
                print("💡 Tente uma pergunta mais simples ou verifique a conexão")
        
    except Exception as e:
        print(f"❌ Erro na inicialização: {e}")
        print("\n🔧 Verifique:")
        print("   • Variáveis de ambiente (.env)")
        print("   • Conexão com Astra DB") 
        print("   • Chave da OpenAI")
        print("   • Documentos indexados")

if __name__ == "__main__":
    main()