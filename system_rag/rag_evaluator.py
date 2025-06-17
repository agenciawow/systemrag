# rag_evaluator.py

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

# Importa a classe RAG de produção
try:
    from system_rag.search.conversational_rag import ModularConversationalRAG as MultimodalRagSearcher
except ImportError:
    print("ERRO: O sistema RAG modular não foi encontrado.")
    print("Por favor, certifique-se de que o system_rag está instalado corretamente.")
    exit()


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@dataclass
class TestQuestion:
    """Estrutura para perguntas de teste"""
    id: str
    question: str
    expected_pages: List[int]  # Páginas que deveriam ser encontradas
    expected_keywords: List[str]  # Palavras-chave que deveriam aparecer na resposta
    category: str  # Categoria da pergunta (ex: "technical", "conceptual", "specific")
    difficulty: str  # "easy", "medium", "hard"
    ground_truth: Optional[str] = None  # Resposta esperada (opcional)

@dataclass
class EvaluationResult:
    """Resultado da avaliação de uma pergunta"""
    question_id: str
    question: str
    selected_pages: List[int]
    expected_pages: List[int]
    answer: str
    response_time: float
    precision: float
    recall: float
    f1_score: float
    page_accuracy: float
    keyword_coverage: float
    total_candidates: int
    error: Optional[str] = None

class RAGEvaluator:
    """Avaliador completo do sistema RAG"""
    
    def __init__(self, rag_searcher: MultimodalRagSearcher):
        """
        Inicializa o avaliador
        
        Args:
            rag_searcher: Instância do MultimodalRagSearcher real.
        """
        self.rag_searcher = rag_searcher
        self.results: List[EvaluationResult] = []
        
    def create_test_dataset(self, questions_file: Optional[str] = None) -> List[TestQuestion]:
        """
        Cria dataset de teste a partir de arquivo JSON ou variáveis de ambiente
        """
        # Tentar carregar de arquivo primeiro
        if not questions_file:
            questions_file = "test_configs/system_rag_questions.json"
        
        if questions_file and os.path.exists(questions_file):
            try:
                with open(questions_file, 'r', encoding='utf-8') as f:
                    questions_data = json.load(f)
                
                test_questions = []
                for q_data in questions_data:
                    test_questions.append(TestQuestion(**q_data))
                
                logger.info(f"Carregadas {len(test_questions)} perguntas de {questions_file}")
                return test_questions
            except Exception as e:
                logger.warning(f"Erro ao carregar perguntas de {questions_file}: {e}")
        
        # Fallback para variáveis de ambiente
        questions_str = os.getenv("EVAL_QUESTIONS", "")
        keywords_str = os.getenv("EVAL_KEYWORDS", "")
        categories_str = os.getenv("EVAL_CATEGORIES", "")
        
        if not questions_str:
            logger.warning("EVAL_QUESTIONS não definida no .env, usando perguntas padrão")
            return self._create_default_dataset()
        
        questions = questions_str.split("|")
        keywords_list = keywords_str.split("|") if keywords_str else []
        categories = categories_str.split("|") if categories_str else []
        
        # Ajusta listas para ter o mesmo tamanho
        max_len = len(questions)
        keywords_list = keywords_list + [""] * (max_len - len(keywords_list))
        categories = categories + ["general"] * (max_len - len(categories))
        
        test_questions = []
        for i, question in enumerate(questions):
            if not question.strip():
                continue
                
            keywords = keywords_list[i].split(",") if keywords_list[i] else []
            keywords = [kw.strip() for kw in keywords if kw.strip()]
            
            test_questions.append(TestQuestion(
                id=f"eval_{i+1:03d}",
                question=question.strip(),
                expected_pages=[],  # Será determinado dinamicamente
                expected_keywords=keywords,
                category=categories[i].strip() if i < len(categories) else "general",
                difficulty="medium"
            ))
        
        logger.info(f"Criado dataset com {len(test_questions)} perguntas das variáveis de ambiente")
        return test_questions
    
    def _create_default_dataset(self) -> List[TestQuestion]:
        """
        Dataset padrão caso não haja variáveis de ambiente definidas
        """
        return [
            TestQuestion(
                id="default_001",
                question="Quais produtos estão disponíveis?",
                expected_pages=[],
                expected_keywords=["produtos", "cardápio", "menu", "disponível"],
                category="catalog",
                difficulty="easy"
            ),
            TestQuestion(
                id="default_002", 
                question="Qual é o preço mais alto do cardápio?",
                expected_pages=[],
                expected_keywords=["preço", "valor", "caro", "alto"],
                category="pricing",
                difficulty="medium"
            ),
            TestQuestion(
                id="default_003",
                question="Vocês têm opções para dietas especiais?",
                expected_pages=[],
                expected_keywords=["dieta", "vegetariano", "vegano", "especial"],
                category="dietary",
                difficulty="medium"
            ),
            TestQuestion(
                id="negative_001",
                question="Qual é o número do CPF do proprietário?",
                expected_pages=[],  # Pergunta que não deveria ter resposta
                expected_keywords=[],
                category="negative",
                difficulty="easy"
            ),
        ]
    
    def calculate_metrics(self, 
                          selected_pages: List[int], 
                          expected_pages: List[int],
                          answer: str,
                          expected_keywords: List[str]) -> Tuple[float, float, float, float, float]:
        """
        Calcula métricas de avaliação.
        """
        if not expected_pages:
            if not selected_pages:
                return 1.0, 1.0, 1.0, 1.0, 1.0  # Acerto: não retornou nada quando não devia
            else:
                return 0.0, 0.0, 0.0, 0.0, 0.0  # Erro: retornou algo quando não devia
        
        if not selected_pages:
            return 0.0, 0.0, 0.0, 0.0, 0.0 # Erro: não retornou nada quando devia

        relevant_selected_set = set(selected_pages) & set(expected_pages)
        
        precision = len(relevant_selected_set) / len(selected_pages)
        recall = len(relevant_selected_set) / len(expected_pages)
        
        if precision + recall == 0:
            f1_score = 0.0
        else:
            f1_score = 2 * (precision * recall) / (precision + recall)
        
        union_set = set(selected_pages) | set(expected_pages)
        page_accuracy = len(relevant_selected_set) / len(union_set) if union_set else 1.0
        
        if not expected_keywords:
            keyword_coverage = 1.0
        else:
            answer_lower = answer.lower()
            found_keywords = sum(1 for kw in expected_keywords if kw.lower() in answer_lower)
            keyword_coverage = found_keywords / len(expected_keywords)
        
        return precision, recall, f1_score, page_accuracy, keyword_coverage
    
    def evaluate_single_question(self, test_q: TestQuestion) -> EvaluationResult:
        """Avalia uma única pergunta."""
        start_time = time.time()
        
        try:
            # Nosso sistema usa o método ask() que retorna uma string
            answer = self.rag_searcher.ask(test_q.question)
            response_time = time.time() - start_time
            
            # Verifica se a resposta indica que não foi encontrada informação
            no_info_indicators = [
                "não consegui encontrar",
                "não foi encontrada",
                "informação não encontrada",
                "não tenho informações",
                "não está disponível"
            ]
            
            found_no_info = any(indicator in answer.lower() for indicator in no_info_indicators)
            
            # Para perguntas negativas (que não deveriam ter resposta), considerar sucesso
            if test_q.category == "negative" and found_no_info:
                logger.info(f"Pergunta negativa '{test_q.id}' corretamente identificada como sem resposta")
                precision, recall, f1_score, page_accuracy, keyword_coverage = self.calculate_metrics(
                    [], test_q.expected_pages, answer, test_q.expected_keywords
                )
            else:
                # Para outras perguntas, assumimos que houve busca (não temos info detalhada de páginas)
                # Como não temos acesso aos detalhes internos, simulamos métricas baseadas na resposta
                selected_pages = self._estimate_pages_from_answer(answer)
                precision, recall, f1_score, page_accuracy, keyword_coverage = self.calculate_metrics(
                    selected_pages, test_q.expected_pages, answer, test_q.expected_keywords
                )
            
            return EvaluationResult(
                question_id=test_q.id, question=test_q.question,
                selected_pages=selected_pages if 'selected_pages' in locals() else [],
                expected_pages=test_q.expected_pages,
                answer=answer, response_time=response_time,
                precision=precision, recall=recall, f1_score=f1_score,
                page_accuracy=page_accuracy, keyword_coverage=keyword_coverage,
                total_candidates=1 if answer and not found_no_info else 0
            )
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(f"Erro fatal avaliando pergunta {test_q.id}: {e}", exc_info=True)
            return EvaluationResult(
                question_id=test_q.id, question=test_q.question,
                selected_pages=[], expected_pages=test_q.expected_pages,
                answer="", response_time=response_time,
                precision=0.0, recall=0.0, f1_score=0.0, page_accuracy=0.0,
                keyword_coverage=0.0, total_candidates=0, error=str(e)
            )
    
    def _estimate_pages_from_answer(self, answer: str) -> List[int]:
        """
        Estima páginas baseado na presença de resposta.
        Como não temos acesso aos detalhes internos, assumimos que respostas válidas vêm de páginas.
        """
        if not answer or len(answer.strip()) < 10:
            return []
        
        no_info_indicators = [
            "não consegui encontrar",
            "não foi encontrada", 
            "informação não encontrada",
            "não tenho informações",
            "não está disponível"
        ]
        
        if any(indicator in answer.lower() for indicator in no_info_indicators):
            return []
        
        # Simula que houve busca bem-sucedida (assumindo página 1 como padrão)
        return [1]
    
    def run_evaluation(self, test_questions: Optional[List[TestQuestion]] = None) -> Dict[str, Any]:
        """Executa avaliação completa."""
        if test_questions is None:
            test_questions = self.create_test_dataset()
        
        logger.info(f"Iniciando avaliação com {len(test_questions)} perguntas")
        
        self.results = [self.evaluate_single_question(test_q) for test_q in tqdm(test_questions, desc="Avaliando perguntas")]
        
        for result in self.results:
             logger.info(f"Q_ID:{result.question_id}: P={result.precision:.2f}, R={result.recall:.2f}, "
                        f"F1={result.f1_score:.2f}, T={result.response_time:.2f}s")

        successful_results = [r for r in self.results if r.error is None]
        
        if not successful_results:
            logger.error("Nenhuma pergunta foi avaliada com sucesso!")
            return {"error": "Nenhuma avaliação bem-sucedida"}
        
        # Agrega métricas gerais
        overall_metrics = {
            "average_precision": statistics.mean([r.precision for r in successful_results]),
            "average_recall": statistics.mean([r.recall for r in successful_results]),
            "average_f1_score": statistics.mean([r.f1_score for r in successful_results]),
            "average_page_accuracy": statistics.mean([r.page_accuracy for r in successful_results]),
            "average_keyword_coverage": statistics.mean([r.keyword_coverage for r in successful_results]),
            "average_response_time": statistics.mean([r.response_time for r in successful_results]),
        }
        
        # Agrega métricas por categoria
        categories = {q.category for q in test_questions}
        category_stats = {}
        for cat in categories:
            cat_results = [r for r in successful_results if r.question_id.startswith(cat)]
            if cat_results:
                category_stats[cat] = {
                    "count": len(cat_results),
                    "avg_precision": statistics.mean([r.precision for r in cat_results]),
                    "avg_recall": statistics.mean([r.recall for r in cat_results]),
                    "avg_f1": statistics.mean([r.f1_score for r in cat_results]),
                    "avg_response_time": statistics.mean([r.response_time for r in cat_results]),
                }

        report = {
            "evaluation_summary": {
                "total_questions": len(test_questions),
                "successful_evaluations": len(successful_results),
                "failed_evaluations": len(self.results) - len(successful_results),
                "success_rate": len(successful_results) / len(test_questions) if test_questions else 0,
            },
            "overall_metrics": overall_metrics,
            "category_breakdown": category_stats,
            "detailed_results": [asdict(r) for r in self.results],
            "evaluation_timestamp": datetime.now(ZoneInfo("America/Sao_Paulo")).isoformat(),
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_path: str = "rag_evaluation_report.json"):
        """Salva relatório em arquivo JSON."""
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        logger.info(f"Relatório JSON salvo em: {output_path}")
    
    def create_detailed_report(self, report: Dict[str, Any]) -> str:
        """Cria relatório detalhado em texto."""
        lines = ["=" * 80, "RELATÓRIO DE AVALIAÇÃO DO SISTEMA RAG MULTIMODAL", "=" * 80, ""]
        
        summary = report["evaluation_summary"]
        lines.extend([
            "📊 RESUMO GERAL:",
            f"• Total de perguntas: {summary['total_questions']}",
            f"• Avaliações bem-sucedidas: {summary['successful_evaluations']}",
            f"• Avaliações com falha: {summary['failed_evaluations']}",
            f"• Taxa de sucesso: {summary['success_rate']:.1%}", ""
        ])
        
        metrics = report["overall_metrics"]
        lines.extend([
            "📈 MÉTRICAS GERAIS:",
            f"• Precisão média: {metrics['average_precision']:.3f}",
            f"• Recall médio: {metrics['average_recall']:.3f}",
            f"• F1-Score médio: {metrics['average_f1_score']:.3f}",
            f"• Acurácia de páginas (Jaccard): {metrics['average_page_accuracy']:.3f}",
            f"• Cobertura de palavras-chave: {metrics['average_keyword_coverage']:.3f}",
            f"• Tempo de resposta médio: {metrics['average_response_time']:.2f}s", ""
        ])
        
        lines.append("🏷️ ANÁLISE POR CATEGORIA:")
        for cat, stats in report["category_breakdown"].items():
            lines.extend([
                f"• {cat.upper()} ({stats['count']} perguntas):",
                f"  - Precisão: {stats['avg_precision']:.3f}",
                f"  - Recall: {stats['avg_recall']:.3f}",
                f"  - F1-Score: {stats['avg_f1']:.3f}",
                f"  - Tempo médio: {stats['avg_response_time']:.2f}s"
            ])
        lines.append("")
        
        lines.append("📋 RESULTADOS DETALHADOS:")
        for result in report["detailed_results"]:
            lines.append(f"• {result['question_id']}: {result['question']}")
            if result['error']:
                lines.append(f"  ❌ ERRO: {result['error']}")
            else:
                lines.append(f"  ✅ Páginas: {result['selected_pages']} (Esperado: {result['expected_pages']})")
                lines.append(f"     P={result['precision']:.2f}, R={result['recall']:.2f}, F1={result['f1_score']:.2f}")
        lines.append("")
        
        return "\n".join(lines)

def main():
    """Função principal para execução standalone."""
    print("🚀 AVALIADOR DE SISTEMA RAG MULTIMODAL 🚀")
    print("=" * 60)
    
    try:
        print("🔧 Inicializando o sistema RAG real...")
        rag_searcher = MultimodalRagSearcher()
        print("✅ Sistema RAG inicializado com sucesso!")
        
        evaluator = RAGEvaluator(rag_searcher=rag_searcher)
        
        print("\n🔍 Executando avaliação completa...")
        report = evaluator.run_evaluation()
        
        # Salva e imprime relatórios
        evaluator.save_report(report)
        
        detailed_report = evaluator.create_detailed_report(report)
        report_path = "rag_evaluation_detailed.txt"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(detailed_report)
        logger.info(f"Relatório detalhado salvo em: {report_path}")

        
        print("\n" + detailed_report)
        print("\n✅ Avaliação concluída! Arquivos salvos:")
        print("• rag_evaluation_report.json")
        print("• rag_evaluation_detailed.txt")
        
    except Exception as e:
        print(f"\n❌ Erro fatal durante a execução do avaliador: {e}")
        logger.critical("Erro fatal no main do avaliador", exc_info=True)
        print("\nVerifique se:")
        print("1. O arquivo 'buscador.py' está na mesma pasta.")
        print("2. O arquivo '.env' com as chaves de API está configurado corretamente.")
        print("3. O sistema RAG foi indexado (rode o 'indexador.py' primeiro).")
        print("4. Todas as dependências (`requirements.txt`) estão instaladas.")

if __name__ == "__main__":
    main()
