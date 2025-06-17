#!/usr/bin/env python3
"""
Script de conveniência para executar a API de agents

Executa: python -m agents.api.main
"""

import subprocess
import sys
import os

def main():
    """Executa a API de agents"""
    try:
        # Configurações do servidor
        host = os.getenv("AGENTS_HOST", "0.0.0.0")
        port = os.getenv("AGENTS_PORT", "8001")
        
        print("🚀 Iniciando API de Agents...")
        print(f"📍 Porta: {port}")
        print(f"📚 Docs: http://localhost:{port}/docs")
        print("🔐 Auth: Bearer Token required")
        print("=" * 50)
        
        # Executar API de agents (sem reload para evitar conflitos)
        result = subprocess.run([
            sys.executable, "-m", "uvicorn", "agents.api.main:app",
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