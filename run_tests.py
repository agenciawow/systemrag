#!/usr/bin/env python3
"""
Script de conveniência para executar testes

Redireciona para o executor completo em tests/run_tests.py
"""

import subprocess
import sys
import os

def main():
    """Executa o script de testes principal"""
    script_path = os.path.join("tests", "run_tests.py")
    
    try:
        # Passar todos os argumentos para o script principal
        result = subprocess.run([
            sys.executable, script_path
        ] + sys.argv[1:], cwd=os.path.dirname(os.path.abspath(__file__)))
        
        return result.returncode
        
    except Exception as e:
        print(f"❌ Erro ao executar testes: {e}")
        return 1

if __name__ == "__main__":
    exit(main())