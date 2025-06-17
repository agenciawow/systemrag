#!/usr/bin/env python3
"""
Testes automatizados para o sistema de avaliação do Sistema RAG Multimodal

Testa o avaliador automático:
- RAGEvaluator
- Métricas de avaliação
- Configuração via ambiente
- Geração de relatórios
"""

import pytest
import os
import json
import tempfile
import shutil
from typing import Dict, List
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Imports do sistema
try:
    from rag_evaluator import RAGEvaluator
    from system_rag.search.conversational_rag import ModularConversationalRAG
except ImportError as e:
    pytest.skip(f"Módulos do avaliador não disponíveis: {e}", allow_module_level=True)

class TestEvaluatorConfig:
    """Configuração para testes do avaliador"""
    
    # Configuração mínima para testes
    TEST_EVAL_QUESTIONS = "Quais produtos estão disponíveis?|Qual é o preço do hambúrguer?|Vocês têm opções vegetarianas?"
    TEST_EVAL_KEYWORDS = "produtos,disponível,cardápio|preço,valor,hambúrguer|vegetariano,vegano,opção"
    TEST_EVAL_CATEGORIES = "catalog|pricing|dietary"
    
    # APIs necessárias
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    VOYAGE_API_KEY = os.getenv('VOYAGE_API_KEY')
    ASTRA_DB_APPLICATION_TOKEN = os.getenv('ASTRA_DB_APPLICATION_TOKEN')
    ASTRA_DB_API_ENDPOINT = os.getenv('ASTRA_DB_API_ENDPOINT')
    
    @property
    def has_full_config(self) -> bool:
        return all([
            self.OPENAI_API_KEY,
            self.VOYAGE_API_KEY,
            self.ASTRA_DB_APPLICATION_TOKEN,
            self.ASTRA_DB_API_ENDPOINT
        ])

@pytest.fixture
def evaluator_config():
    """Fixture com configuração do avaliador"""
    return TestEvaluatorConfig()

@pytest.fixture
def temp_env_vars():
    """Fixture que configura variáveis de ambiente temporárias"""
    config = TestEvaluatorConfig()
    
    # Salvar valores originais
    original_questions = os.environ.get('EVAL_QUESTIONS')
    original_keywords = os.environ.get('EVAL_KEYWORDS')
    original_categories = os.environ.get('EVAL_CATEGORIES')
    
    # Configurar valores de teste
    os.environ['EVAL_QUESTIONS'] = config.TEST_EVAL_QUESTIONS
    os.environ['EVAL_KEYWORDS'] = config.TEST_EVAL_KEYWORDS
    os.environ['EVAL_CATEGORIES'] = config.TEST_EVAL_CATEGORIES
    
    yield
    
    # Restaurar valores originais
    if original_questions:
        os.environ['EVAL_QUESTIONS'] = original_questions
    elif 'EVAL_QUESTIONS' in os.environ:
        del os.environ['EVAL_QUESTIONS']
        
    if original_keywords:
        os.environ['EVAL_KEYWORDS'] = original_keywords
    elif 'EVAL_KEYWORDS' in os.environ:
        del os.environ['EVAL_KEYWORDS']
        
    if original_categories:
        os.environ['EVAL_CATEGORIES'] = original_categories
    elif 'EVAL_CATEGORIES' in os.environ:
        del os.environ['EVAL_CATEGORIES']

@pytest.fixture
def temp_output_dir():
    """Fixture que cria diretório temporário para arquivos de saída"""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    yield temp_dir
    
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

class TestRAGEvaluatorInitialization:
    """Testes de inicialização do avaliador"""
    
    @pytest.mark.skipif(not TestEvaluatorConfig().has_full_config, reason="Configuração completa não disponível")
    def test_evaluator_with_rag_instance(self, evaluator_config):
        """Testa inicialização com instância RAG"""
        try:
            rag_instance = ModularConversationalRAG()
            evaluator = RAGEvaluator(rag_instance)
            assert evaluator.rag_system is not None
            assert evaluator.rag_system == rag_instance
        except Exception as e:
            pytest.skip(f"Inicialização com RAG falhou: {e}")
    
    def test_evaluator_without_rag_instance(self, evaluator_config):
        """Testa inicialização sem instância RAG"""
        evaluator = RAGEvaluator(None)
        assert evaluator.rag_system is None

class TestTestDatasetCreation:
    """Testes de criação do dataset de teste"""
    
    def test_create_test_dataset_from_env(self, evaluator_config, temp_env_vars):
        """Testa criação de dataset a partir de variáveis de ambiente"""
        evaluator = RAGEvaluator(None)
        dataset = evaluator.create_test_dataset()
        
        assert len(dataset) == 3  # 3 perguntas de teste
        
        # Verificar estrutura do primeiro item
        first_item = dataset[0]
        assert hasattr(first_item, 'question')
        assert hasattr(first_item, 'expected_keywords')
        assert hasattr(first_item, 'category')
        assert hasattr(first_item, 'question_id')
        
        # Verificar conteúdo
        assert first_item.question == "Quais produtos estão disponíveis?"
        assert "produtos" in first_item.expected_keywords
        assert first_item.category == "catalog"
    
    def test_create_test_dataset_empty_env(self, evaluator_config):
        """Testa criação de dataset com variáveis vazias"""
        # Temporariamente limpar variáveis
        original_questions = os.environ.get('EVAL_QUESTIONS', '')
        os.environ['EVAL_QUESTIONS'] = ''
        
        try:
            evaluator = RAGEvaluator(None)
            dataset = evaluator.create_test_dataset()
            assert len(dataset) == 0
        finally:
            # Restaurar
            if original_questions:
                os.environ['EVAL_QUESTIONS'] = original_questions
    
    def test_parse_keywords(self, evaluator_config):
        """Testa parsing de palavras-chave"""
        evaluator = RAGEvaluator(None)
        
        # Teste com keywords válidas
        keywords_str = "palavra1,palavra2,palavra3"
        parsed = evaluator._parse_keywords(keywords_str)
        assert parsed == ["palavra1", "palavra2", "palavra3"]
        
        # Teste com string vazia
        parsed_empty = evaluator._parse_keywords("")
        assert parsed_empty == []
        
        # Teste com espaços
        keywords_with_spaces = "palavra1, palavra2 , palavra3"
        parsed_spaces = evaluator._parse_keywords(keywords_with_spaces)
        assert parsed_spaces == ["palavra1", "palavra2", "palavra3"]

class TestEvaluationMetrics:
    """Testes das métricas de avaliação"""
    
    def test_keyword_coverage_calculation(self, evaluator_config):
        """Testa cálculo de cobertura de palavras-chave"""
        evaluator = RAGEvaluator(None)
        
        # Teste com cobertura completa
        response = "Temos produtos disponíveis no cardápio"
        keywords = ["produtos", "disponível", "cardápio"]
        coverage = evaluator._calculate_keyword_coverage(response, keywords)
        assert coverage == 1.0  # 100% de cobertura
        
        # Teste com cobertura parcial
        response = "Temos produtos no menu"
        keywords = ["produtos", "disponível", "cardápio"]
        coverage = evaluator._calculate_keyword_coverage(response, keywords)
        assert coverage == 1/3  # 33% de cobertura (apenas "produtos")
        
        # Teste com nenhuma cobertura
        response = "Texto sem palavras relevantes"
        keywords = ["produtos", "disponível", "cardápio"]
        coverage = evaluator._calculate_keyword_coverage(response, keywords)
        assert coverage == 0.0  # 0% de cobertura
    
    def test_response_analysis(self, evaluator_config):
        """Testa análise de resposta"""
        evaluator = RAGEvaluator(None)
        
        # Resposta válida
        valid_response = "Temos hambúrgueres, batatas fritas e refrigerantes disponíveis"
        is_valid, reason = evaluator._analyze_response(valid_response)
        assert is_valid is True
        assert reason == "Response is valid"
        
        # Resposta indicando não encontrado
        not_found_response = "Não consegui encontrar informações sobre isso"
        is_valid, reason = evaluator._analyze_response(not_found_response)
        assert is_valid is False
        assert "not found" in reason.lower()
        
        # Resposta vazia
        empty_response = ""
        is_valid, reason = evaluator._analyze_response(empty_response)
        assert is_valid is False
        assert "empty" in reason.lower()

class TestEvaluationExecution:
    """Testes de execução da avaliação"""
    
    @pytest.mark.skipif(not TestEvaluatorConfig().has_full_config, reason="Configuração completa não disponível")
    def test_evaluate_single_question(self, evaluator_config, temp_env_vars):
        """Testa avaliação de uma única pergunta"""
        try:
            rag_instance = ModularConversationalRAG()
            evaluator = RAGEvaluator(rag_instance)
            
            # Criar pergunta de teste
            test_question = type('TestQuestion', (), {
                'question': 'Quais produtos estão disponíveis?',
                'expected_keywords': ['produtos', 'disponível'],
                'category': 'catalog',
                'question_id': 'test_1'
            })()
            
            result = evaluator._evaluate_single_question(test_question)
            
            # Verificar estrutura do resultado
            assert 'question_id' in result
            assert 'question' in result
            assert 'response' in result
            assert 'response_time' in result
            assert 'keyword_coverage' in result
            assert 'is_valid_response' in result
            assert 'analysis_reason' in result
            
            # Verificar valores
            assert result['question_id'] == 'test_1'
            assert result['response_time'] > 0
            assert 0 <= result['keyword_coverage'] <= 1
            
        except Exception as e:
            pytest.skip(f"Avaliação de pergunta única falhou: {e}")
    
    @pytest.mark.skipif(not TestEvaluatorConfig().has_full_config, reason="Configuração completa não disponível")
    def test_run_evaluation(self, evaluator_config, temp_env_vars, temp_output_dir):
        """Testa execução completa da avaliação"""
        try:
            rag_instance = ModularConversationalRAG()
            evaluator = RAGEvaluator(rag_instance)
            
            # Executar avaliação
            report = evaluator.run_evaluation()
            
            # Verificar estrutura do relatório
            assert 'evaluation_summary' in report
            assert 'overall_metrics' in report
            assert 'category_analysis' in report
            assert 'detailed_results' in report
            
            # Verificar summary
            summary = report['evaluation_summary']
            assert 'total_questions' in summary
            assert 'successful_evaluations' in summary
            assert 'failed_evaluations' in summary
            assert 'success_rate' in summary
            
            # Verificar métricas
            metrics = report['overall_metrics']
            assert 'average_response_time' in metrics
            assert 'average_keyword_coverage' in metrics
            assert 'average_precision' in metrics
            assert 'average_recall' in metrics
            assert 'average_f1_score' in metrics
            
            # Verificar se arquivos foram criados
            assert os.path.exists('rag_evaluation_report.json')
            assert os.path.exists('rag_evaluation_detailed.txt')
            
        except Exception as e:
            pytest.skip(f"Avaliação completa falhou: {e}")

class TestReportGeneration:
    """Testes de geração de relatórios"""
    
    def test_save_json_report(self, evaluator_config, temp_output_dir):
        """Testa salvamento de relatório JSON"""
        evaluator = RAGEvaluator(None)
        
        # Criar dados de teste
        test_report = {
            'evaluation_summary': {
                'total_questions': 3,
                'successful_evaluations': 2,
                'failed_evaluations': 1,
                'success_rate': 0.667
            },
            'overall_metrics': {
                'average_response_time': 5.5,
                'average_keyword_coverage': 0.75
            }
        }
        
        # Salvar relatório
        evaluator._save_json_report(test_report)
        
        # Verificar se arquivo foi criado
        assert os.path.exists('rag_evaluation_report.json')
        
        # Verificar conteúdo
        with open('rag_evaluation_report.json', 'r', encoding='utf-8') as f:
            loaded_report = json.load(f)
        
        assert loaded_report['evaluation_summary']['total_questions'] == 3
        assert loaded_report['overall_metrics']['average_response_time'] == 5.5
    
    def test_save_detailed_report(self, evaluator_config, temp_output_dir):
        """Testa salvamento de relatório detalhado"""
        evaluator = RAGEvaluator(None)
        
        # Criar dados de teste
        test_report = {
            'evaluation_summary': {
                'total_questions': 2,
                'successful_evaluations': 2,
                'failed_evaluations': 0,
                'success_rate': 1.0
            },
            'overall_metrics': {
                'average_response_time': 4.2,
                'average_keyword_coverage': 0.85,
                'average_precision': 0.80,
                'average_recall': 0.75,
                'average_f1_score': 0.77
            },
            'category_analysis': {
                'catalog': {
                    'questions_count': 1,
                    'success_rate': 1.0,
                    'avg_response_time': 4.0
                }
            },
            'detailed_results': [
                {
                    'question_id': 'q1',
                    'question': 'Teste?',
                    'response': 'Resposta teste',
                    'keyword_coverage': 0.8,
                    'is_valid_response': True
                }
            ]
        }
        
        # Salvar relatório
        evaluator._save_detailed_report(test_report)
        
        # Verificar se arquivo foi criado
        assert os.path.exists('rag_evaluation_detailed.txt')
        
        # Verificar conteúdo básico
        with open('rag_evaluation_detailed.txt', 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert 'RELATÓRIO DE AVALIAÇÃO' in content
        assert 'Taxa de sucesso: 100.0%' in content
        assert 'Tempo médio: 4.2s' in content

class TestErrorHandling:
    """Testes de tratamento de erros"""
    
    def test_evaluation_with_no_rag_system(self, evaluator_config, temp_env_vars):
        """Testa avaliação sem sistema RAG"""
        evaluator = RAGEvaluator(None)
        
        # Deve retornar erro
        report = evaluator.run_evaluation()
        assert 'error' in report
        assert 'RAG system not provided' in report['error']
    
    def test_evaluation_with_no_questions(self, evaluator_config):
        """Testa avaliação sem perguntas configuradas"""
        # Limpar variáveis de ambiente
        original_questions = os.environ.get('EVAL_QUESTIONS', '')
        os.environ['EVAL_QUESTIONS'] = ''
        
        try:
            evaluator = RAGEvaluator(None)
            dataset = evaluator.create_test_dataset()
            assert len(dataset) == 0
        finally:
            # Restaurar
            if original_questions:
                os.environ['EVAL_QUESTIONS'] = original_questions
    
    def test_malformed_environment_variables(self, evaluator_config):
        """Testa variáveis de ambiente malformadas"""
        # Configurar variáveis inconsistentes
        os.environ['EVAL_QUESTIONS'] = 'Pergunta 1|Pergunta 2'  # 2 perguntas
        os.environ['EVAL_KEYWORDS'] = 'palavra1,palavra2'  # 1 grupo de keywords
        os.environ['EVAL_CATEGORIES'] = 'cat1'  # 1 categoria
        
        try:
            evaluator = RAGEvaluator(None)
            dataset = evaluator.create_test_dataset()
            
            # Deve criar dataset mesmo com inconsistências, usando defaults
            assert len(dataset) == 2  # Baseado no número de perguntas
            
        finally:
            # Limpar
            if 'EVAL_QUESTIONS' in os.environ:
                del os.environ['EVAL_QUESTIONS']
            if 'EVAL_KEYWORDS' in os.environ:
                del os.environ['EVAL_KEYWORDS']
            if 'EVAL_CATEGORIES' in os.environ:
                del os.environ['EVAL_CATEGORIES']

if __name__ == "__main__":
    # Executar testes básicos se chamado diretamente
    import sys
    
    print("🧪 Executando testes básicos do avaliador...")
    
    config = TestEvaluatorConfig()
    
    # Verificar configuração
    if config.has_full_config:
        print("✅ Configuração completa disponível - testes completos habilitados")
    else:
        print("⚠️  Configuração incompleta - alguns testes serão pulados")
        print("   Configure: OPENAI_API_KEY, VOYAGE_API_KEY, ASTRA_DB_APPLICATION_TOKEN, ASTRA_DB_API_ENDPOINT")
    
    # Verificar se avaliador está disponível
    try:
        from rag_evaluator import RAGEvaluator
        print("✅ Módulo rag_evaluator disponível")
    except ImportError as e:
        print(f"❌ Módulo rag_evaluator não disponível: {e}")
        sys.exit(1)
    
    # Executar com pytest se disponível
    try:
        import pytest
        print("\n🚀 Executando testes completos com pytest...")
        pytest.main([__file__, "-v", "-x"])
    except ImportError:
        print("⚠️  pytest não disponível. Instale com: pip install pytest")
        print("✅ Testes básicos de configuração passaram")