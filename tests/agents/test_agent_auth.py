"""
Teste da autenticação da API de agentes

Verifica se a autenticação está funcionando corretamente.
"""

import requests
import sys
import os

# Adicionar diretório raiz ao path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# URL base da API de agentes
BASE_URL = "http://localhost:8001"

# API Key para testes
API_KEY = os.getenv("API_KEY", "sistemarag-api-key-2024")

def test_public_endpoint():
    """Testa endpoint público (sem autenticação)"""
    print("=== TESTE ENDPOINT PÚBLICO ===")
    
    try:
        response = requests.get(f"{BASE_URL}/auth-info")
        print(f"✅ Endpoint público funcionando")
        print(f"Resposta: {response.json()}")
        assert response.status_code == 200
    except Exception as e:
        print(f"❌ Erro no endpoint público: {e}")
        assert False, f"Erro no endpoint público: {e}"


def test_protected_endpoint_without_auth():
    """Testa endpoint protegido sem autenticação (deve falhar)"""
    print("\n=== TESTE SEM AUTENTICAÇÃO (deve falhar) ===")
    
    try:
        response = requests.get(f"{BASE_URL}/v1/agents")
        print("✅ Rejeição de acesso sem auth funcionando")
        print(f"Resposta: {response.json()}")
        assert response.status_code in [401, 403], f"Expected 401 or 403, got {response.status_code}"
    except Exception as e:
        print(f"❌ Erro no teste sem auth: {e}")
        assert False, f"Erro no teste sem auth: {e}"


def test_protected_endpoint_with_wrong_auth():
    """Testa endpoint protegido com autenticação errada (deve falhar)"""
    print("\n=== TESTE COM AUTENTICAÇÃO ERRADA (deve falhar) ===")
    
    headers = {
        "Authorization": "Bearer chave-errada",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/v1/agents", headers=headers)
        print("✅ Rejeição de chave inválida funcionando")
        print(f"Resposta: {response.json()}")
        assert response.status_code == 401
    except Exception as e:
        print(f"❌ Erro no teste com auth errada: {e}")
        assert False, f"Erro no teste com auth errada: {e}"


def test_protected_endpoint_with_correct_auth():
    """Testa endpoint protegido com autenticação correta (deve funcionar)"""
    print("\n=== TESTE COM AUTENTICAÇÃO CORRETA (deve funcionar) ===")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{BASE_URL}/v1/agents", headers=headers)
        print("✅ Acesso com auth correta funcionando")
        data = response.json()
        print(f"Agentes encontrados: {len(data.get('agents', []))}")
        assert response.status_code == 200
    except Exception as e:
        print(f"❌ Erro no teste com auth correta: {e}")
        assert False, f"Erro no teste com auth correta: {e}"


def load_test_questions():
    """Carrega perguntas de teste de arquivo de configuração"""
    import json
    questions_file = "test_configs/test_auth_questions.json"
    
    try:
        if os.path.exists(questions_file):
            with open(questions_file, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        print(f"⚠️ Erro ao carregar perguntas de {questions_file}: {e}")
    
    # Fallback para perguntas padrão
    return [
        {
            "question": "Olá, você está funcionando?",
            "expected_response_indicators": ["olá", "funcionando", "sim", "ativo"],
            "test_type": "basic_functionality",
            "description": "Teste básico de funcionamento",
            "timeout": 10
        }
    ]


def test_agent_interaction():
    """Testa interação completa com agente (autenticado)"""
    print("\n=== TESTE INTERAÇÃO COM AGENTE ===")
    
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        # 1. Listar agentes
        response = requests.get(f"{BASE_URL}/v1/agents", headers=headers)
        assert response.status_code == 200, f"Falha ao listar agentes: {response.status_code}"
        
        agents = response.json().get("agents", [])
        assert agents, "Nenhum agente encontrado"
        
        print(f"Agentes disponíveis: {[a['name'] for a in agents]}")
        
        # 2. Carregar perguntas de teste  
        test_questions = load_test_questions()
        agent_id = agents[0]["agent_id"]
        
        # 3. Testar primeira pergunta apenas (para não demorar)
        question_data = test_questions[0]
        print(f"Testando pergunta: {question_data['question']}")
        
        ask_data = {
            "message": question_data["question"],
            "user_id": "test-user",
            "session_id": "test-session",
            "clear_history": True
        }
        
        response = requests.post(
            f"{BASE_URL}/v1/agents/{agent_id}/ask",
            headers=headers,
            json=ask_data,
            timeout=question_data.get("timeout", 30)
        )
        
        assert response.status_code == 200, f"Falha ao fazer pergunta: {response.status_code} - {response.text}"
        
        answer_data = response.json()
        print(f"✅ Pergunta respondida com sucesso")
        print(f"Resposta: {answer_data['response'][:100]}...")
        
    except Exception as e:
        print(f"❌ Erro na interação: {e}")
        assert False, f"Erro na interação: {e}"


def run_auth_tests():
    """Executa todos os testes de autenticação"""
    print("🔐 INICIANDO TESTES DE AUTENTICAÇÃO DA API DE AGENTES\n")
    
    tests = [
        ("Endpoint Público", test_public_endpoint),
        ("Sem Autenticação", test_protected_endpoint_without_auth),
        ("Autenticação Errada", test_protected_endpoint_with_wrong_auth),
        ("Autenticação Correta", test_protected_endpoint_with_correct_auth),
        ("Interação Completa", test_agent_interaction)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        success = test_func()
        results.append((test_name, success))
    
    print(f"\n{'='*50}")
    print("RESUMO DOS TESTES DE AUTENTICAÇÃO")
    print(f"{'='*50}")
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSOU" if success else "❌ FALHOU"
        print(f"{test_name}: {status}")
    
    print(f"\nResultado: {passed}/{total} testes passaram")
    
    if passed == total:
        print("🎉 AUTENTICAÇÃO FUNCIONANDO PERFEITAMENTE!")
        print(f"\nAPI Key em uso: {API_KEY}")
        print("Para testar manualmente:")
        print(f'curl -H "Authorization: Bearer {API_KEY}" {BASE_URL}/v1/agents')
    else:
        print("⚠️  Alguns testes de autenticação falharam.")
        print("\nVerifique:")
        print("1. API de agentes está rodando na porta 8001")
        print("2. Variável API_KEY está configurada")
        print("3. Dependências estão instaladas")


if __name__ == "__main__":
    try:
        run_auth_tests()
    except KeyboardInterrupt:
        print("\n\n❌ Testes interrompidos pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro geral nos testes: {e}")
        import traceback
        traceback.print_exc()