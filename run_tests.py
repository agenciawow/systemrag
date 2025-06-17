#!/usr/bin/env python3
"""
Executor Principal de Testes - Sistema RAG Multimodal

Execute os testes simplificados e focados do sistema.
"""

import subprocess
import sys
import os

def main():
    """Executa a interface simplificada de testes"""
    script_path = os.path.join("tests", "simple", "run_simple_tests.py")
    
    if not os.path.exists(script_path):
        print("❌ Arquivo de testes não encontrado!")
        print(f"   Esperado em: {script_path}")
        return 1
    
    try:
        # Passa todos os argumentos para o script de testes simplificados
        result = subprocess.run([
            sys.executable, script_path
        ] + sys.argv[1:], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        print(f"💡 Tente executar diretamente: python {script_path}")
        return 1

if __name__ == "__main__":
    exit(main())