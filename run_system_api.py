
#!/usr/bin/env python3
"""
Script de conveniência para executar a API do Sistema RAG

Executa: python -m system_rag.api.api
"""

import subprocess
import sys
import os

def main():
    """Executa a API do Sistema RAG"""
    try:
        # Configurações do servidor
        host = os.getenv("SYSTEM_RAG_HOST", "0.0.0.0")
        port = os.getenv("SYSTEM_RAG_PORT", "8000")
        
        print("🚀 Iniciando API do Sistema RAG...")
        print(f"📍 Porta: {port}")
        print(f"📚 Docs: http://localhost:{port}/docs")
        print("🔐 Auth: Bearer Token required")
        print("=" * 50)
        
        # Executar API do sistema RAG (sem reload para evitar conflitos)
        result = subprocess.run([
            sys.executable, "-m", "uvicorn", "system_rag.api.api:app", 
            "--host", host, "--port", port
        ], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return result.returncode
        
    except KeyboardInterrupt:
        print("\n🛑 API interrompida pelo usuário")
        return 0
    except Exception as e:
        print(f"❌ Erro ao executar API: {e}")
        return 1

if __name__ == "__main__":
    exit(main())