#!/usr/bin/env python3
"""
Interface Simplificada para Testes do Sistema RAG Multimodal

Este script oferece uma interface mais simples e focada para executar testes individuais,
cada um focado em uma funcionalidade específica do sistema.
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

class SimpleTestRunner:
    """Runner simplificado para execução de testes individuais"""
    
    def __init__(self):
        self.tests_dir = Path(__file__).parent
        self.project_root = self.tests_dir.parent.parent
        self.api_key = os.getenv("API_KEY", "sistemarag-api-key-secure-2024")
        
        # Definição dos testes disponíveis
        self.available_tests = [
            {
                "id": "01",
                "name": "APIs e Conexões",
                "file": "test_01_api_connections.py",
                "description": "Testa conectividade básica com todas as APIs necessárias",
                "estimated_time": "30s",
                "requires_api": False
            },
            {
                "id": "02", 
                "name": "Ingestão de Documentos",
                "file": "test_02_document_ingestion.py",
                "description": "Testa o processo de ingestão de documentos no sistema",
                "estimated_time": "2min",
                "requires_api": True,
                "api_port": 8000
            },
            {
                "id": "03",
                "name": "Busca System RAG",
                "file": "test_03_system_rag_search.py", 
                "description": "Testa a funcionalidade de busca usando o sistema RAG",
                "estimated_time": "1min",
                "requires_api": True,
                "api_port": 8000
            },
            {
                "id": "04",
                "name": "Busca com Agentes",
                "file": "test_04_agents_search.py",
                "description": "Testa a funcionalidade de busca usando o sistema de agentes",
                "estimated_time": "2min",
                "requires_api": True,
                "api_port": 8001
            },
            {
                "id": "05",
                "name": "Stress Test FastAPI",
                "file": "test_05_fastapi_stress.py",
                "description": "Testa requisições assíncronas e simultâneas para estressar a API",
                "estimated_time": "3min",
                "requires_api": True,
                "api_port": [8000, 8001]
            },
            {
                "id": "06",
                "name": "Sistema de Memória Zep",
                "file": "test_06_zep_memory.py",
                "description": "Testa a integração e funcionalidade do sistema de memória Zep",
                "estimated_time": "3min",
                "requires_api": True,
                "api_port": 8001
            },
            {
                "id": "07",
                "name": "Avaliação System RAG",
                "file": "test_07_system_rag_evaluation.py",
                "description": "Testa a qualidade das respostas do sistema RAG usando perguntas específicas",
                "estimated_time": "5min",
                "requires_api": True,
                "api_port": 8000
            },
            {
                "id": "08",
                "name": "Avaliação dos Agentes",
                "file": "test_08_agents_evaluation.py",
                "description": "Testa a qualidade das respostas do sistema de agentes usando perguntas específicas",
                "estimated_time": "7min",
                "requires_api": True,
                "api_port": 8001
            }
        ]
    
    def check_api_status(self, port):
        """Verifica se uma API está rodando na porta especificada"""
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=5)
            return response.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_test_requirements(self, test_info):
        """Verifica se os requisitos de um teste estão atendidos"""
        if not test_info["requires_api"]:
            return True, "Nenhuma API necessária"
        
        api_ports = test_info["api_port"]
        if not isinstance(api_ports, list):
            api_ports = [api_ports]
        
        missing_apis = []
        for port in api_ports:
            if not self.check_api_status(port):
                api_name = "Sistema RAG" if port == 8000 else "Agentes"
                missing_apis.append(f"{api_name} (porta {port})")
        
        if missing_apis:
            return False, f"APIs não disponíveis: {', '.join(missing_apis)}"
        
        return True, "Requisitos atendidos"
    
    def run_test(self, test_info, verbose=True):
        """Executa um teste específico"""
        test_file = self.tests_dir / test_info["file"]
        
        if not test_file.exists():
            print(f"❌ Arquivo de teste não encontrado: {test_file}")
            return False
        
        print(f"\n🚀 Executando: {test_info['name']}")
        print(f"📝 Descrição: {test_info['description']}")
        print(f"⏱️  Tempo estimado: {test_info['estimated_time']}")
        
        # Verifica requisitos
        requirements_ok, requirements_msg = self.check_test_requirements(test_info)
        if not requirements_ok:
            print(f"⚠️  Requisitos não atendidos: {requirements_msg}")
            print("   Para executar este teste, inicie as APIs necessárias:")
            if isinstance(test_info.get("api_port"), list):
                for port in test_info["api_port"]:
                    if port == 8000:
                        print("   - python run_system_api.py")
                    elif port == 8001:
                        print("   - python run_agents_api.py")
            else:
                port = test_info.get("api_port")
                if port == 8000:
                    print("   - python run_system_api.py")
                elif port == 8001:
                    print("   - python run_agents_api.py")
            return False
        
        print(f"✅ {requirements_msg}")
        print("─" * 60)
        
        # Executa o teste
        start_time = time.time()
        
        try:
            cmd = ["pytest", str(test_file), "-v"]
            if verbose:
                cmd.append("-s")
            
            result = subprocess.run(cmd, cwd=self.project_root, check=False)
            execution_time = time.time() - start_time
            
            if result.returncode == 0:
                print(f"\n✅ {test_info['name']} - Concluído com sucesso em {execution_time:.1f}s")
                return True
            else:
                print(f"\n❌ {test_info['name']} - Falhou com código {result.returncode}")
                return False
                
        except KeyboardInterrupt:
            print(f"\n⚠️ {test_info['name']} - Interrompido pelo usuário")
            return False
        except Exception as e:
            print(f"\n❌ {test_info['name']} - Erro: {e}")
            return False
    
    def show_test_status(self):
        """Mostra o status de todos os testes"""
        print("\n📊 STATUS DOS TESTES DISPONÍVEIS")
        print("=" * 80)
        
        for test_info in self.available_tests:
            requirements_ok, requirements_msg = self.check_test_requirements(test_info)
            status_icon = "✅" if requirements_ok else "⚠️"
            
            print(f"{status_icon} {test_info['id']}. {test_info['name']} ({test_info['estimated_time']})")
            print(f"   {test_info['description']}")
            if not requirements_ok:
                print(f"   ⚠️ {requirements_msg}")
            print()
    
    def run_all_available_tests(self):
        """Executa todos os testes que têm requisitos atendidos"""
        print("\n🎯 EXECUTANDO TODOS OS TESTES DISPONÍVEIS")
        print("=" * 60)
        
        total_tests = 0
        successful_tests = 0
        skipped_tests = 0
        
        for test_info in self.available_tests:
            total_tests += 1
            
            requirements_ok, _ = self.check_test_requirements(test_info)
            if not requirements_ok:
                print(f"⏭️  Pulando {test_info['name']} - requisitos não atendidos")
                skipped_tests += 1
                continue
            
            success = self.run_test(test_info, verbose=False)
            if success:
                successful_tests += 1
            
            # Pausa entre testes
            if total_tests < len(self.available_tests):
                time.sleep(2)
        
        print(f"\n📊 RESUMO FINAL:")
        print(f"   Total: {total_tests}")
        print(f"   Executados: {total_tests - skipped_tests}")
        print(f"   Bem-sucedidos: {successful_tests}")
        print(f"   Falharam: {total_tests - skipped_tests - successful_tests}")
        print(f"   Pulados: {skipped_tests}")
        
        return successful_tests == (total_tests - skipped_tests)
    
    def interactive_menu(self):
        """Menu interativo para seleção de testes"""
        while True:
            print("\n" + "="*80)
            print("🧪 SISTEMA RAG MULTIMODAL - TESTES SIMPLIFICADOS")
            print("="*80)
            print("Selecione um teste para executar:")
            print()
            
            # Lista os testes disponíveis
            for test_info in self.available_tests:
                requirements_ok, _ = self.check_test_requirements(test_info)
                status_icon = "✅" if requirements_ok else "⚠️"
                print(f"  {test_info['id']}. {status_icon} {test_info['name']} ({test_info['estimated_time']})")
            
            print(f"\n  99. 📊 Mostrar status detalhado de todos os testes")
            print(f"  00. 🚀 Executar todos os testes disponíveis")
            print(f"   0. 🚪 Sair")
            
            choice = input(f"\n🎯 Escolha uma opção: ").strip()
            
            if choice == "0":
                print("👋 Até logo!")
                break
            elif choice == "00":
                self.run_all_available_tests()
                input("\n⏸️ Pressione Enter para continuar...")
            elif choice == "99":
                self.show_test_status()
                input("\n⏸️ Pressione Enter para continuar...")
            else:
                # Procura o teste pelo ID
                test_found = None
                for test_info in self.available_tests:
                    if test_info["id"] == choice:
                        test_found = test_info
                        break
                
                if test_found:
                    self.run_test(test_found)
                    input("\n⏸️ Pressione Enter para continuar...")
                else:
                    print("❌ Opção inválida. Tente novamente.")

def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description="Executor simplificado de testes para Sistema RAG Multimodal")
    parser.add_argument("--test", type=str, help="ID do teste específico para executar (01-08)")
    parser.add_argument("--all", action="store_true", help="Executar todos os testes disponíveis")
    parser.add_argument("--status", action="store_true", help="Mostrar status de todos os testes")
    parser.add_argument("--list", action="store_true", help="Listar todos os testes disponíveis")
    parser.add_argument("--interactive", action="store_true", help="Menu interativo (padrão)")
    
    args = parser.parse_args()
    
    runner = SimpleTestRunner()
    
    # Se nenhum argumento, mostrar menu interativo
    if not any(vars(args).values()) or args.interactive:
        runner.interactive_menu()
        return
    
    # Executar ações baseadas em argumentos
    if args.list:
        print("\n📋 TESTES DISPONÍVEIS:")
        print("=" * 60)
        for test_info in runner.available_tests:
            print(f"{test_info['id']}. {test_info['name']} ({test_info['estimated_time']})")
            print(f"   {test_info['description']}")
            print()
    
    elif args.status:
        runner.show_test_status()
    
    elif args.all:
        success = runner.run_all_available_tests()
        sys.exit(0 if success else 1)
    
    elif args.test:
        test_found = None
        for test_info in runner.available_tests:
            if test_info["id"] == args.test:
                test_found = test_info
                break
        
        if test_found:
            success = runner.run_test(test_found)
            sys.exit(0 if success else 1)
        else:
            print(f"❌ Teste '{args.test}' não encontrado.")
            print("Use --list para ver todos os testes disponíveis.")
            sys.exit(1)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()