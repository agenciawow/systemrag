#!/usr/bin/env python3
"""
Script para executar o pipeline RAG completo
"""
import os
import asyncio
import sys

# Carregar variáveis de ambiente
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("📝 Variáveis de ambiente carregadas do .env")
except ImportError:
    print("⚠️  python-dotenv não instalado. Usando variáveis do sistema.")

# Importar e executar pipeline
sys.path.append('..')
from .basic_usage import basic_rag_pipeline, quick_test


def process_document_url(document_url: str, document_name: str = None, overwrite: bool = False) -> dict:
    """
    Processa um documento a partir de uma URL
    
    Args:
        document_url: URL do documento para processar
        document_name: Nome opcional para o documento
        overwrite: Se deve sobrescrever documento existente
        
    Returns:
        Dict com resultado do processamento
    """
    import tempfile
    import os
    
    # Salvar URL original e temporariamente atualizar
    original_url = os.environ.get('GOOGLE_DRIVE_URL')
    os.environ['GOOGLE_DRIVE_URL'] = document_url
    
    try:
        # Executar pipeline básico
        result = asyncio.run(basic_rag_pipeline())
        
        return {
            'success': True,
            'message': 'Documento processado com sucesso',
            'document_name': document_name or 'Documento processado',
            'chunks_created': len(result) if result else 0
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'message': f'Erro ao processar documento: {e}'
        }
        
    finally:
        # Restaurar URL original
        if original_url:
            os.environ['GOOGLE_DRIVE_URL'] = original_url
        elif 'GOOGLE_DRIVE_URL' in os.environ:
            del os.environ['GOOGLE_DRIVE_URL']


def main():
    """Função principal"""
    print("🚀 Sistema RAG Multimodal")
    print("=" * 50)
    
    # Verificar se é teste rápido
    if len(sys.argv) > 1 and sys.argv[1] == "test":
        print("🧪 Executando teste rápido...")
        quick_test()
        return
    
    # Verificar variável GOOGLE_DRIVE_URL
    google_url = os.getenv('GOOGLE_DRIVE_URL')
    if not google_url or 'YOUR_FILE_ID' in google_url:
        print("❌ Configure GOOGLE_DRIVE_URL no arquivo .env")
        print("\nExemplo:")
        print("GOOGLE_DRIVE_URL=https://drive.google.com/file/d/SEU_FILE_ID/view")
        print("\nPara obter o FILE_ID:")
        print("1. Abra seu documento no Google Drive")
        print("2. Clique em 'Compartilhar' > 'Copiar link'")
        print("3. Extraia o ID entre '/d/' e '/view'")
        return
    
    print(f"📄 Documento configurado: {google_url}")
    print("\n⚠️  ATENÇÃO: Este pipeline irá consumir créditos das APIs:")
    print("   - LlamaParse: ~$0.003 por página")
    print("   - Voyage AI: ~$0.00012 por 1K tokens")
    print("   - Cloudflare R2: storage mínimo")
    print("   - Astra DB: gratuito até 25GB")
    
    # Auto-confirmar se executado com argumento --auto ou -y
    if "--auto" in sys.argv or "-y" in sys.argv:
        print("\n🤔 Continuar? (s/N): s [auto-confirmado]")
    else:
        response = input("\n🤔 Continuar? (s/N): ").lower().strip()
        if response not in ['s', 'sim', 'y', 'yes']:
            print("❌ Pipeline cancelado pelo usuário")
            return
    
    print("\n🚀 Iniciando pipeline completo...")
    try:
        asyncio.run(basic_rag_pipeline())
    except KeyboardInterrupt:
        print("\n❌ Pipeline interrompido pelo usuário")
    except Exception as e:
        print(f"\n❌ Erro no pipeline: {e}")
        print("\n💡 Dicas para resolver:")
        print("   1. Execute 'python run_pipeline.py test' para verificar APIs")
        print("   2. Verifique se todas as variáveis estão configuradas no .env")
        print("   3. Confirme que o documento do Google Drive é público")


if __name__ == "__main__":
    main()