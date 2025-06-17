#!/usr/bin/env python3
"""Script dedicado para ingestão - equivale ao antigo ingestao.py"""

import subprocess
import sys

if __name__ == "__main__":
    print("🚀 Iniciando Ingestão RAG Modular...")
    
    # Executar o pipeline usando o comando que funciona
    try:
        # Usar echo para confirmar automaticamente
        result = subprocess.run([
            'bash', '-c', 'echo "s" | python -m system_rag.ingestion.run_pipeline'
        ], capture_output=True, text=True, cwd='.')
        
        # Mostrar a saída
        if result.stdout:
            print(result.stdout)
        if result.stderr:
            print(result.stderr)
        
        # Verificar se deu certo
        if result.returncode == 0:
            print("✅ Ingestão concluída com sucesso!")
        else:
            print(f"❌ Erro na ingestão (código: {result.returncode})")
            
    except Exception as e:
        print(f"❌ Erro ao executar ingestão: {e}")
        print("💡 Tente executar diretamente: python run_pipeline.py")