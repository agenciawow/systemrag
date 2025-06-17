"""
Avaliador de Agentes

Sistema de avaliação específico para agentes inteligentes baseado no avaliador RAG existente.
"""

import os
import json
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
import statistics

from tqdm import tqdm

try:
    from agents.core.operator import agent_operator, get_agent
    from agents.core.rag_search_agent import RAGSearchAgent
except ImportError as e:
    print(f"Erro ao importar agentes: {e}")
    print("Por favor, certifique-se de que o sistema de agentes está configurado corretamente.")
    exit()

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class AgentTestQuestion:
    """Estrutura de uma pergunta de teste para agentes"""
    question: str
    expected_topics: List[str]
    test_type: str
    difficulty: str = "medium"
    timeout: int = 30
    metadata: Dict[str, Any] = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class AgentEvaluationResult:
    """Resultado da avaliação de um agente"""
    agent_id: str
    agent_name: str
    question: str
    answer: str
    response_time: float
    success: bool
    score: float
    topics_found: List[str]
    evaluation_notes: str
    test_type: str
    timestamp: str


@dataclass
class AgentEvaluationReport:
    """Relatório completo da avaliação de agentes"""
    agent_id: str
    agent_name: str
    total_questions: int
    successful_answers: int
    average_score: float
    average_response_time: float
    results: List[AgentEvaluationResult]
    evaluation_summary: str
    timestamp: str
    test_duration: float


class AgentEvaluator:
    """
    Avaliador especializado para agentes inteligentes
    
    Baseado no RAGEvaluator existente, mas adaptado para avaliar:
    - Qualidade das respostas dos agentes
    - Tempo de resposta
    - Precisão contextual
    - Capacidade conversacional
    """
    
    def __init__(self, agent_id: str = "rag-search", output_dir: str = "agents/evaluation_results"):
        """
        Inicializa o avaliador de agentes
        
        Args:
            agent_id: ID do agente a ser avaliado
            output_dir: Diretório para salvar resultados
        """
        self.agent_id = agent_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Verificar se agente existe
        if not agent_operator.agent_exists(agent_id):
            raise ValueError(f"Agente '{agent_id}' não encontrado. Agentes disponíveis: {[a['agent_id'] for a in agent_operator.list_agents()]}")
        
        # Obter instância do agente
        self.agent = get_agent(agent_id)
        
        # Perguntas de teste configuráveis
        self.test_questions = self._load_default_questions()
        
        logger.info(f"Avaliador inicializado para agente: {agent_id}")
    
    def _load_default_questions(self) -> List[AgentTestQuestion]:
        """Carrega perguntas padrão para teste"""
        # Tentar carregar de arquivo primeiro
        default_questions_file = "test_configs/agent_questions.json"
        if os.path.exists(default_questions_file):
            try:
                with open(default_questions_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                
                questions = []
                for q_data in questions_data:
                    question = AgentTestQuestion(**q_data)
                    questions.append(question)
                
                logger.info(f"Carregadas {len(questions)} perguntas padrão de {default_questions_file}")
                return questions
            except Exception as e:
                logger.warning(f"Erro ao carregar perguntas padrão de arquivo: {e}")
        
        # Fallback para perguntas hardcoded
        return [
            AgentTestQuestion(
                question="Olá, como você está?",
                expected_topics=["saudação", "apresentação", "assistente"],
                test_type="conversational",
                difficulty="easy"
            ),
            AgentTestQuestion(
                question="Qual é o objetivo principal dos documentos disponíveis?",
                expected_topics=["objetivo", "propósito", "finalidade"],
                test_type="informational",
                difficulty="medium"
            ),
            AgentTestQuestion(
                question="Pode me explicar sobre metodologias apresentadas?",
                expected_topics=["metodologia", "método", "processo"],
                test_type="analytical",
                difficulty="medium"
            ),
            AgentTestQuestion(
                question="Quais são as principais conclusões?",
                expected_topics=["conclusão", "resultado", "resumo"],
                test_type="analytical",
                difficulty="hard"
            ),
            AgentTestQuestion(
                question="Obrigado pela ajuda!",
                expected_topics=["agradecimento", "encerramento", "cortesia"],
                test_type="conversational",
                difficulty="easy"
            )
        ]
    
    def load_custom_questions(self, questions_file: str) -> None:
        """
        Carrega perguntas customizadas de arquivo JSON
        
        Args:
            questions_file: Caminho para arquivo JSON com perguntas
        """
        try:
            with open(questions_file, 'r', encoding='utf-8') as f:
                questions_data = json.load(f)
            
            custom_questions = []
            for q_data in questions_data:
                question = AgentTestQuestion(**q_data)
                custom_questions.append(question)
            
            self.test_questions = custom_questions
            logger.info(f"Carregadas {len(custom_questions)} perguntas customizadas de {questions_file}")
            
        except Exception as e:
            logger.error(f"Erro ao carregar perguntas de {questions_file}: {e}")
            raise
    
    def evaluate_single_question(self, question: AgentTestQuestion) -> AgentEvaluationResult:
        """
        Avalia uma única pergunta
        
        Args:
            question: Pergunta de teste
            
        Returns:
            Resultado da avaliação
        """
        logger.info(f"Avaliando pergunta: {question.question}")
        
        start_time = time.time()
        success = False
        answer = ""
        score = 0.0
        topics_found = []
        evaluation_notes = ""
        
        try:
            # Fazer pergunta ao agente
            answer = self.agent.ask(question.question)
            response_time = time.time() - start_time
            
            # Avaliar resposta
            evaluation = self._evaluate_answer(question, answer)
            success = evaluation['success']
            score = evaluation['score']
            topics_found = evaluation['topics_found']
            evaluation_notes = evaluation['notes']
            
        except Exception as e:
            response_time = time.time() - start_time
            answer = f"ERRO: {str(e)}"
            evaluation_notes = f"Erro durante avaliação: {e}"
            logger.error(f"Erro ao avaliar pergunta: {e}")
        
        return AgentEvaluationResult(
            agent_id=self.agent_id,
            agent_name=self.agent.name,
            question=question.question,
            answer=answer,
            response_time=response_time,
            success=success,
            score=score,
            topics_found=topics_found,
            evaluation_notes=evaluation_notes,
            test_type=question.test_type,
            timestamp=datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat()
        )
    
    def _evaluate_answer(self, question: AgentTestQuestion, answer: str) -> Dict[str, Any]:
        """
        Avalia a qualidade da resposta
        
        Args:
            question: Pergunta original
            answer: Resposta do agente
            
        Returns:
            Dicionário com avaliação
        """
        evaluation = {
            'success': False,
            'score': 0.0,
            'topics_found': [],
            'notes': ''
        }
        
        if not answer or "erro" in answer.lower():
            evaluation['notes'] = "Resposta com erro ou vazia"
            return evaluation
        
        answer_lower = answer.lower()
        
        # Verificar tópicos esperados
        topics_found = []
        for topic in question.expected_topics:
            if topic.lower() in answer_lower:
                topics_found.append(topic)
        
        evaluation['topics_found'] = topics_found
        
        # Calcular score baseado nos tópicos encontrados
        if question.expected_topics:
            topic_score = len(topics_found) / len(question.expected_topics)
        else:
            topic_score = 1.0 if len(answer) > 10 else 0.0
        
        # Score baseado no tipo de teste
        if question.test_type == "conversational":
            # Para conversação, verificar se resposta é apropriada
            if len(answer) > 20 and any(word in answer_lower for word in ['assistente', 'ajuda', 'olá', 'obrigado']):
                evaluation['success'] = True
                evaluation['score'] = max(0.8, topic_score)
            else:
                evaluation['score'] = topic_score * 0.6
        
        elif question.test_type == "informational":
            # Para informações, verificar se tem conteúdo substantivo
            if len(answer) > 50 and topic_score > 0:
                evaluation['success'] = True
                evaluation['score'] = topic_score
            else:
                evaluation['score'] = topic_score * 0.7
        
        elif question.test_type == "analytical":
            # Para análise, verificar profundidade da resposta
            if len(answer) > 100 and topic_score > 0.5:
                evaluation['success'] = True
                evaluation['score'] = topic_score
            else:
                evaluation['score'] = topic_score * 0.8
        
        # Ajustar score por dificuldade
        difficulty_multiplier = {
            'easy': 1.0,
            'medium': 0.9,
            'hard': 0.8
        }
        evaluation['score'] *= difficulty_multiplier.get(question.difficulty, 1.0)
        
        # Notas da avaliação
        if evaluation['success']:
            evaluation['notes'] = f"Resposta adequada. Tópicos encontrados: {len(topics_found)}/{len(question.expected_topics)}"
        else:
            evaluation['notes'] = f"Resposta inadequada. Tópicos: {len(topics_found)}/{len(question.expected_topics)}"
        
        return evaluation
    
    def evaluate_agent(self, questions: Optional[List[AgentTestQuestion]] = None) -> AgentEvaluationReport:
        """
        Avalia o agente com conjunto de perguntas
        
        Args:
            questions: Lista de perguntas (usa padrão se None)
            
        Returns:
            Relatório completo da avaliação
        """
        if questions is None:
            questions = self.test_questions
        
        logger.info(f"Iniciando avaliação do agente {self.agent_id} com {len(questions)} perguntas")
        
        # Limpar histórico do agente
        if hasattr(self.agent, 'clear_history'):
            self.agent.clear_history()
        
        start_time = time.time()
        results = []
        
        # Avaliar cada pergunta
        for question in tqdm(questions, desc="Avaliando perguntas"):
            result = self.evaluate_single_question(question)
            results.append(result)
            
            # Pequena pausa entre perguntas
            time.sleep(0.5)
        
        total_duration = time.time() - start_time
        
        # Calcular métricas
        successful_answers = sum(1 for r in results if r.success)
        average_score = statistics.mean([r.score for r in results]) if results else 0.0
        average_response_time = statistics.mean([r.response_time for r in results]) if results else 0.0
        
        # Gerar resumo
        summary = self._generate_evaluation_summary(results, successful_answers, average_score)
        
        report = AgentEvaluationReport(
            agent_id=self.agent_id,
            agent_name=self.agent.name,
            total_questions=len(questions),
            successful_answers=successful_answers,
            average_score=average_score,
            average_response_time=average_response_time,
            results=results,
            evaluation_summary=summary,
            timestamp=datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
            test_duration=total_duration
        )
        
        # Salvar relatório
        self._save_report(report)
        
        logger.info(f"Avaliação concluída. Score médio: {average_score:.2f}, Sucesso: {successful_answers}/{len(questions)}")
        
        return report
    
    def _generate_evaluation_summary(self, results: List[AgentEvaluationResult], 
                                   successful_answers: int, average_score: float) -> str:
        """Gera resumo da avaliação"""
        total = len(results)
        success_rate = (successful_answers / total) * 100 if total > 0 else 0
        
        # Análise por tipo de teste
        type_analysis = {}
        for result in results:
            test_type = result.test_type
            if test_type not in type_analysis:
                type_analysis[test_type] = {'total': 0, 'success': 0, 'scores': []}
            
            type_analysis[test_type]['total'] += 1
            if result.success:
                type_analysis[test_type]['success'] += 1
            type_analysis[test_type]['scores'].append(result.score)
        
        summary_lines = [
            f"AVALIAÇÃO DO AGENTE {self.agent_id.upper()}",
            "=" * 50,
            f"Taxa de Sucesso Geral: {success_rate:.1f}% ({successful_answers}/{total})",
            f"Score Médio: {average_score:.3f}",
            "",
            "ANÁLISE POR TIPO DE TESTE:",
        ]
        
        for test_type, data in type_analysis.items():
            type_success_rate = (data['success'] / data['total']) * 100
            type_avg_score = statistics.mean(data['scores'])
            summary_lines.append(f"  {test_type.title()}: {type_success_rate:.1f}% sucesso, score {type_avg_score:.3f}")
        
        # Recomendações
        summary_lines.extend([
            "",
            "RECOMENDAÇÕES:",
        ])
        
        if success_rate >= 80:
            summary_lines.append("✅ Agente performando muito bem!")
        elif success_rate >= 60:
            summary_lines.append("⚠️  Agente performando adequadamente, mas há espaço para melhorias")
        else:
            summary_lines.append("❌ Agente precisa de ajustes significativos")
        
        if average_score < 0.5:
            summary_lines.append("- Revisar lógica de resposta e treinamento")
        
        return "\n".join(summary_lines)
    
    def _save_report(self, report: AgentEvaluationReport) -> None:
        """Salva relatório em arquivos"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Salvar JSON detalhado
        json_file = self.output_dir / f"agent_evaluation_{self.agent_id}_{timestamp}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)
        
        # Salvar resumo em texto
        txt_file = self.output_dir / f"agent_evaluation_{self.agent_id}_{timestamp}.txt"
        with open(txt_file, 'w', encoding='utf-8') as f:
            f.write(report.evaluation_summary)
            f.write("\n\n" + "="*50 + "\n")
            f.write("RESULTADOS DETALHADOS:\n")
            f.write("="*50 + "\n\n")
            
            for i, result in enumerate(report.results, 1):
                f.write(f"{i}. PERGUNTA: {result.question}\n")
                f.write(f"   RESPOSTA: {result.answer[:200]}{'...' if len(result.answer) > 200 else ''}\n")
                f.write(f"   SCORE: {result.score:.3f} | TEMPO: {result.response_time:.2f}s | SUCESSO: {result.success}\n")
                f.write(f"   NOTAS: {result.evaluation_notes}\n\n")
        
        logger.info(f"Relatório salvo em: {json_file} e {txt_file}")
    
    def compare_agents(self, agent_ids: List[str], questions: Optional[List[AgentTestQuestion]] = None) -> Dict[str, AgentEvaluationReport]:
        """
        Compara múltiplos agentes
        
        Args:
            agent_ids: Lista de IDs dos agentes
            questions: Perguntas para teste (usa padrão se None)
            
        Returns:
            Dicionário com relatórios de cada agente
        """
        reports = {}
        
        for agent_id in agent_ids:
            logger.info(f"Avaliando agente: {agent_id}")
            
            # Criar avaliador temporário para este agente
            temp_evaluator = AgentEvaluator(agent_id, self.output_dir)
            if questions:
                temp_evaluator.test_questions = questions
            
            # Avaliar agente
            report = temp_evaluator.evaluate_agent()
            reports[agent_id] = report
        
        # Salvar comparação
        self._save_comparison_report(reports)
        
        return reports
    
    def _save_comparison_report(self, reports: Dict[str, AgentEvaluationReport]) -> None:
        """Salva relatório de comparação entre agentes"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        comparison_file = self.output_dir / f"agent_comparison_{timestamp}.txt"
        
        with open(comparison_file, 'w', encoding='utf-8') as f:
            f.write("COMPARAÇÃO ENTRE AGENTES\n")
            f.write("=" * 50 + "\n\n")
            
            # Tabela de comparação
            f.write(f"{'Agente':<15} {'Sucesso':<10} {'Score Médio':<12} {'Tempo Médio':<12}\n")
            f.write("-" * 50 + "\n")
            
            for agent_id, report in reports.items():
                success_rate = (report.successful_answers / report.total_questions) * 100
                f.write(f"{agent_id:<15} {success_rate:>7.1f}%   {report.average_score:>9.3f}   {report.average_response_time:>9.2f}s\n")
            
            f.write("\n" + "=" * 50 + "\n\n")
            
            # Resumos individuais
            for agent_id, report in reports.items():
                f.write(f"RESUMO - {agent_id.upper()}:\n")
                f.write(report.evaluation_summary)
                f.write("\n\n")
        
        logger.info(f"Relatório de comparação salvo em: {comparison_file}")


def run_agent_evaluation(agent_id: str = "rag-search", questions_file: Optional[str] = None) -> AgentEvaluationReport:
    """
    Função de conveniência para executar avaliação de agente
    
    Args:
        agent_id: ID do agente a avaliar
        questions_file: Arquivo opcional com perguntas customizadas
        
    Returns:
        Relatório da avaliação
    """
    try:
        evaluator = AgentEvaluator(agent_id)
        
        if questions_file and os.path.exists(questions_file):
            evaluator.load_custom_questions(questions_file)
        
        report = evaluator.evaluate_agent()
        
        print("\n" + "="*60)
        print("AVALIAÇÃO DO AGENTE CONCLUÍDA")
        print("="*60)
        print(f"Agente: {report.agent_name} ({report.agent_id})")
        print(f"Taxa de Sucesso: {(report.successful_answers/report.total_questions)*100:.1f}%")
        print(f"Score Médio: {report.average_score:.3f}")
        print(f"Tempo Médio de Resposta: {report.average_response_time:.2f}s")
        print(f"\nRelatórios salvos em: agents/evaluation_results/")
        
        return report
        
    except Exception as e:
        logger.error(f"Erro na avaliação: {e}")
        raise


if __name__ == "__main__":
    # Executar avaliação se chamado diretamente
    import sys
    
    agent_id = sys.argv[1] if len(sys.argv) > 1 else "rag-search"
    questions_file = sys.argv[2] if len(sys.argv) > 2 else None
    
    report = run_agent_evaluation(agent_id, questions_file)