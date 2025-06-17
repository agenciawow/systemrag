#!/usr/bin/env python3
"""
Script executor de testes para o Sistema RAG Multimodal

Este script fornece uma interface amigável para executar diferentes conjuntos de testes
sem necessidade de conhecer todos os comandos pytest.
"""

import os
import sys
import subprocess
import argparse
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

class TestRunner:
    """Runner principal para execução de testes"""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.project_root = self.tests_dir.parent
        self.api_url = os.getenv("TEST_API_URL", "http://localhost:8000")
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        
    def check_pytest(self):
        """Verifica se pytest está instalado"""
        try:
            subprocess.run(["pytest", "--version"], capture_output=True, check=True)
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ pytest não está instalado")
            print("   Instale com: pip install pytest pytest-asyncio")
            return False
    
    def check_api_status(self):
        """Verifica se a API está rodando"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✅ API está rodando em {self.api_url}")
                return True
            else:
                print(f"⚠️  API respondeu com status {response.status_code}")
                return False
        except requests.exceptions.RequestException:
            print(f"❌ API não está acessível em {self.api_url}")
            print("   Inicie com: python run_system_api.py")
            return False
    
    def check_environment(self):
        """Verifica configuração do ambiente"""
        print("🔍 Verificando configuração...")
        
        required_vars = {
            "Críticas": ["OPENAI_API_KEY", "VOYAGE_API_KEY", "ASTRA_DB_APPLICATION_TOKEN", "ASTRA_DB_API_ENDPOINT"],
            "Ingestão": ["LLAMA_CLOUD_API_KEY", "R2_ENDPOINT", "R2_AUTH_TOKEN"],
            "Avaliação": ["EVAL_QUESTIONS", "EVAL_KEYWORDS", "EVAL_CATEGORIES"],
            "Zep Memory": ["ZEP_API_KEY"]
        }
        
        status = {}
        for category, vars_list in required_vars.items():
            configured = [var for var in vars_list if os.getenv(var)]
            status[category] = {
                "configured": len(configured),
                "total": len(vars_list),
                "missing": [var for var in vars_list if not os.getenv(var)]
            }
        
        for category, info in status.items():
            if info["configured"] == info["total"]:
                print(f"✅ {category}: {info['configured']}/{info['total']} configuradas")
            elif info["configured"] > 0:
                print(f"⚠️  {category}: {info['configured']}/{info['total']} configuradas")
                print(f"   Ausentes: {', '.join(info['missing'])}")
            else:
                print(f"❌ {category}: {info['configured']}/{info['total']} configuradas")
        
        return status
    
    def run_command(self, command, description):
        """Executa comando e mostra resultado"""
        print(f"\n🚀 {description}")
        print(f"💻 Comando: {' '.join(command)}")
        print("─" * 50)
        
        start_time = time.time()
        
        try:
            result = subprocess.run(command, cwd=self.project_root, check=False)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"✅ {description} - Concluído em {execution_time:.1f}s")
                return True
            else:
                print(f"❌ {description} - Falhou com código {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print(f"\n⚠️ {description} - Interrompido pelo usuário")
            return False
        except Exception as e:
            print(f"❌ {description} - Erro: {e}")
            return False
    
    def run_basic_tests(self):
        """Executa testes básicos (rápidos)"""
        command = ["pytest", "tests/system_rag/", "tests/agents/", "-v", "--tb=short"]
        return self.run_command(command, "Testes Básicos (Sistema RAG + Agents)")
    
    def run_all_tests(self):
        """Executa todos os testes incluindo lentos"""
        command = ["pytest", "tests/", "-v", "--run-slow", "--tb=short"]
        return self.run_command(command, "Todos os Testes (Sistema RAG + Agents + Integração)")
    
    def run_api_tests(self):
        """Executa apenas testes da API"""
        if not self.check_api_status():
            print("⚠️ Pulando testes da API - servidor não está rodando")
            return False
        
        command = ["pytest", "tests/system_rag/test_api.py", "-v"]
        return self.run_command(command, "Testes da API Sistema RAG")
    
    def run_ingestion_tests(self):
        """Executa testes de ingestão"""
        command = ["pytest", "tests/system_rag/test_ingestion.py", "-v"]
        return self.run_command(command, "Testes de Ingestão")
    
    def run_search_tests(self):
        """Executa testes de busca"""
        command = ["pytest", "tests/system_rag/test_search.py", "-v"]
        return self.run_command(command, "Testes de Busca")
    
    def run_evaluator_tests(self):
        """Executa testes do avaliador"""
        command = ["pytest", "tests/system_rag/test_evaluator.py", "-v"]
        return self.run_command(command, "Testes do Avaliador")
    
    def run_agents_tests(self):
        """Executa testes dos agents"""
        command = ["pytest", "tests/agents/", "-v"]
        return self.run_command(command, "Testes dos Agents")
    
    def run_zep_tests(self):
        """Executa testes de integração Zep"""
        command = ["pytest", "tests/agents/test_zep_integration.py", "-v"]
        return self.run_command(command, "Testes de Integração Zep")
    
    def run_integration_tests(self):
        """Executa testes de integração"""
        if not self.check_api_status():
            print("⚠️ Pulando testes de integração - API não está rodando")
            return False
        
        command = ["pytest", "tests/system_rag/test_integration.py", "-v", "--run-slow", "-s"]
        return self.run_command(command, "Testes de Integração End-to-End")
    
    def run_smoke_tests(self):
        """Executa smoke tests (verificação básica)"""
        print("\n🔥 Executando Smoke Tests...")
        
        tests = [
            ("Health Check da API", self.check_api_status),
            ("Configuração de Ambiente", lambda: bool(self.check_environment())),
        ]
        
        results = []
        for test_name, test_func in tests:
            try:
                result = test_func()
                results.append((test_name, result))
                status = "✅ PASSOU" if result else "❌ FALHOU"
                print(f"{status} - {test_name}")
            except Exception as e:
                results.append((test_name, False))
                print(f"❌ ERRO - {test_name}: {e}")
        
        # Teste simples da API se disponível
        if any(result for name, result in results if "API" in name):
            try:
                response = requests.post(
                    f"{self.api_url}/search",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={"query": "teste smoke", "include_history": False},
                    timeout=30
                )
                api_test_result = response.status_code == 200
                results.append(("Busca da API", api_test_result))
                status = "✅ PASSOU" if api_test_result else "❌ FALHOU"
                print(f"{status} - Busca da API")
            except Exception as e:
                results.append(("Busca da API", False))
                print(f"❌ ERRO - Busca da API: {e}")
        
        passed = sum(1 for _, result in results if result)
        print(f"\n📊 Smoke Tests: {passed}/{len(results)} passaram")
        return passed == len(results)
    
    def interactive_menu(self):
        """Menu interativo para seleção de testes"""
        while True:
            print("\n" + "="*60)
            print("🧪 SISTEMA RAG MULTIMODAL - EXECUTOR DE TESTES")
            print("="*60)
            
            options = [
                ("1", "Smoke Tests (verificação rápida)", self.run_smoke_tests),
                ("2", "Testes Básicos (Sistema RAG + Agents)", self.run_basic_tests),
                ("3", "Testes da API Sistema RAG", self.run_api_tests),
                ("4", "Testes de Ingestão", self.run_ingestion_tests),
                ("5", "Testes de Busca", self.run_search_tests),
                ("6", "Testes do Avaliador", self.run_evaluator_tests),
                ("7", "Testes dos Agents", self.run_agents_tests),
                ("8", "Testes de Integração Zep", self.run_zep_tests),
                ("9", "Testes de Integração End-to-End", self.run_integration_tests),
                ("10", "Todos os Testes", self.run_all_tests),
                ("c", "Verificar Configuração", lambda: self.check_environment()),
                ("0", "Sair", lambda: sys.exit(0))
            ]
            
            for num, desc, _ in options:
                print(f"  {num}. {desc}")
            
            choice = input("\n🎯 Escolha uma opção: ").strip()
            
            # Encontrar e executar opção
            for num, desc, func in options:
                if choice == num:
                    if choice == "0":
                        print("👋 Até logo!")
                        sys.exit(0)
                    
                    print(f"\n▶️ Executando: {desc}")
                    func()
                    input("\n⏸️ Pressione Enter para continuar...")
                    break
            else:
                print("❌ Opção inválida. Tente novamente.")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Executor de testes para Sistema RAG Multimodal")
    parser.add_argument("--smoke", action="store_true", help="Executar smoke tests")
    parser.add_argument("--basic", action="store_true", help="Executar testes básicos (RAG + Agents)")
    parser.add_argument("--all", action="store_true", help="Executar todos os testes")
    parser.add_argument("--api", action="store_true", help="Executar testes da API")
    parser.add_argument("--ingestion", action="store_true", help="Executar testes de ingestão")
    parser.add_argument("--search", action="store_true", help="Executar testes de busca")
    parser.add_argument("--evaluator", action="store_true", help="Executar testes do avaliador")
    parser.add_argument("--agents", action="store_true", help="Executar testes dos agents")
    parser.add_argument("--zep", action="store_true", help="Executar testes de integração Zep")
    parser.add_argument("--integration", action="store_true", help="Executar testes de integração")
    parser.add_argument("--check", action="store_true", help="Verificar configuração")
    parser.add_argument("--interactive", action="store_true", help="Menu interativo")
    
    args = parser.parse_args()
    
    runner = TestRunner()
    
    # Verificar pytest
    if not runner.check_pytest():
        sys.exit(1)
    
    # Se nenhum argumento, mostrar menu interativo
    if not any(vars(args).values()):
        args.interactive = True
    
    # Executar ações baseadas em argumentos
    if args.interactive:
        runner.interactive_menu()
    elif args.smoke:
        success = runner.run_smoke_tests()
        sys.exit(0 if success else 1)
    elif args.basic:
        success = runner.run_basic_tests()
        sys.exit(0 if success else 1)
    elif args.all:
        success = runner.run_all_tests()
        sys.exit(0 if success else 1)
    elif args.api:
        success = runner.run_api_tests()
        sys.exit(0 if success else 1)
    elif args.ingestion:
        success = runner.run_ingestion_tests()
        sys.exit(0 if success else 1)
    elif args.search:
        success = runner.run_search_tests()
        sys.exit(0 if success else 1)
    elif args.evaluator:
        success = runner.run_evaluator_tests()
        sys.exit(0 if success else 1)
    elif args.agents:
        success = runner.run_agents_tests()
        sys.exit(0 if success else 1)
    elif args.zep:
        success = runner.run_zep_tests()
        sys.exit(0 if success else 1)
    elif args.integration:
        success = runner.run_integration_tests()
        sys.exit(0 if success else 1)
    elif args.check:
        runner.check_environment()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()