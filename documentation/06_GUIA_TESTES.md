# 🧪 Testes Automatizados - Sistema RAG Multimodal

## 📋 Visão Geral

Esta pasta contém uma suíte completa de testes automatizados para todos os componentes do Sistema RAG Multimodal, incluindo testes simples individuais e testes complexos de integração.

## 📁 Estrutura dos Testes

```
tests/
├── __init__.py                 # Inicialização do módulo
├── conftest.py                 # Configuração global do pytest
├── run_tests.py                # Executor de testes completo (original)
├── simple/                     # 🆕 TESTES SIMPLIFICADOS
│   ├── __init__.py
│   ├── run_simple_tests.py     # 🎯 Interface simplificada
│   ├── test_01_api_connections.py      # APIs e conectividade
│   ├── test_02_document_ingestion.py   # Ingestão de documentos
│   ├── test_03_system_rag_search.py    # Busca System RAG
│   ├── test_04_agents_search.py        # Busca com Agentes
│   ├── test_05_fastapi_stress.py       # Stress test FastAPI
│   ├── test_06_zep_memory.py           # Sistema de memória Zep
│   ├── test_07_system_rag_evaluation.py # Avaliação System RAG
│   └── test_08_agents_evaluation.py    # Avaliação Agentes
├── system_rag/                # Testes específicos System RAG
│   ├── test_api.py
│   ├── test_ingestion.py
│   ├── test_search.py
│   ├── test_evaluator.py
│   └── test_integration.py
└── agents/                    # Testes específicos Agentes
    ├── test_agent_auth.py
    ├── test_agent_core.py
    ├── test_agent_system.py
    └── test_zep_integration.py
```

## 🎯 TESTES SIMPLIFICADOS (RECOMENDADO)

### 🚀 Execução Rápida e Simples

Para uma experiência simplificada, use a nova interface de testes:

```bash
# Interface interativa (RECOMENDADO)
python tests/simple/run_simple_tests.py

# Ver todos os testes disponíveis
python tests/simple/run_simple_tests.py --list

# Executar teste específico
python tests/simple/run_simple_tests.py --test 01

# Executar todos os testes disponíveis
python tests/simple/run_simple_tests.py --all

# Ver status de todos os testes
python tests/simple/run_simple_tests.py --status
```

### 📋 Testes Individuais Disponíveis

| ID | Nome | Tempo | Descrição |
|----|------|-------|-----------|
| 01 | APIs e Conexões | 30s | Testa conectividade básica com todas as APIs |
| 02 | Ingestão de Documentos | 2min | Testa processo de ingestão de documentos |
| 03 | Busca System RAG | 1min | Testa funcionalidade de busca RAG |
| 04 | Busca com Agentes | 2min | Testa sistema de agentes com memória |
| 05 | Stress Test FastAPI | 3min | Testa requisições assíncronas/simultâneas |
| 06 | Sistema Memória Zep | 3min | Testa integração com sistema Zep |
| 07 | Avaliação System RAG | 5min | Avalia qualidade das respostas RAG |
| 08 | Avaliação Agentes | 7min | Avalia qualidade dos agentes |

### 🎮 Menu Interativo

Execute `python tests/simple/run_simple_tests.py` para acessar o menu:

```
🧪 SISTEMA RAG MULTIMODAL - TESTES SIMPLIFICADOS
================================================================
Selecione um teste para executar:

  01. ✅ APIs e Conexões (30s)
  02. ⚠️ Ingestão de Documentos (2min)
  03. ✅ Busca System RAG (1min)
  04. ⚠️ Busca com Agentes (2min)
  05. ✅ Stress Test FastAPI (3min)
  06. ⚠️ Sistema Memória Zep (3min)
  07. ✅ Avaliação System RAG (5min)
  08. ⚠️ Avaliação Agentes (7min)

  99. 📊 Mostrar status detalhado de todos os testes
  00. 🚀 Executar todos os testes disponíveis
   0. 🚪 Sair

🎯 Escolha uma opção:
```

### 🎯 Perguntas de Avaliação Baseadas no Zep

Os testes de avaliação agora usam perguntas específicas sobre o documento do Zep:

1. **Básicas (fáceis)**:
   - O que é o Zep?
   - Qual é o principal componente do Zep?
   - Contra qual sistema o Zep foi comparado?

2. **Intermediárias**:
   - Qual foi a performance do Zep no benchmark DMR?
   - O que é o Graphiti no contexto do Zep?
   - Quais são as limitações dos frameworks RAG atuais que o Zep resolve?

3. **Avançadas (difíceis)**:
   - Como o Zep lida com dados temporais e históricos?
   - Qual foi a melhoria de latência que o Zep alcançou?
   - Como o Zep sintetiza dados conversacionais não estruturados e dados empresariais estruturados?

## 🔧 TESTES COMPLETOS (AVANÇADO)

### 🚀 Executando os Testes

### Pré-requisitos

1. **Instalar dependências de teste:**
```bash
pip install pytest pytest-asyncio
```

2. **Configurar variáveis de ambiente:**
   - Configure todas as variáveis no arquivo `.env`
   - Consulte `MANUAL_COMPLETO.md` para instruções detalhadas

3. **Iniciar APIs (para testes completos):**
```bash
# Sistema RAG Tradicional (porta 8000)
python run_system_api.py

# Em outro terminal - Sistema de Agents (porta 8001)
python run_agents_api.py
```

> **Nota**: Para testes completos que incluem agents, ambas as APIs devem estar rodando.

### Comandos de Execução

#### Executar Todos os Testes
```bash
# Executar tudo (rápido - pula testes lentos)
pytest tests/

# Executar incluindo testes lentos
pytest tests/ --run-slow

# Executar com saída detalhada
pytest tests/ -v
```

#### Executar Testes Específicos
```bash
# Apenas testes da API
pytest tests/test_api.py -v

# Apenas testes de ingestão
pytest tests/test_ingestion.py -v

# Apenas testes de busca
pytest tests/test_search.py -v

# Apenas testes do avaliador
pytest tests/test_evaluator.py -v

# Apenas testes de integração
pytest tests/test_integration.py -v --run-slow
```

#### Executar por Categoria
```bash
# Testes que requerem APIs externas
pytest tests/ -m "api" -v

# Testes de integração
pytest tests/ -m "integration" --run-slow -v

# Testes que precisam de todas as APIs
pytest tests/ -m "requires_all_apis" -v
```

#### Opções Úteis
```bash
# Parar no primeiro erro
pytest tests/ -x

# Executar em paralelo (se pytest-xdist instalado)
pytest tests/ -n auto

# Pular testes de APIs externas
pytest tests/ --skip-external

# Usar URL diferente para API
pytest tests/ --api-url http://localhost:8001
```

### Executar Testes Individuais

Cada arquivo de teste pode ser executado independentemente:

```bash
# Teste da API
python tests/test_api.py

# Teste de ingestão
python tests/test_ingestion.py

# Teste de busca
python tests/test_search.py

# Teste do avaliador
python tests/test_evaluator.py

# Teste de integração
python tests/test_integration.py
```

## 📊 Tipos de Teste

### 1. **test_api.py** - Testes da API REST
- ✅ Health check e endpoints básicos
- ✅ Autenticação (válida e inválida)
- ✅ Endpoint `/search` (busca)
- ✅ Endpoint `/evaluate` (avaliação)
- ✅ Endpoint `/ingest` (ingestão)
- ✅ Tratamento de erros e validação
- ✅ Performance e limites
- ✅ Requisições concorrentes

**Pré-requisitos:** API rodando em localhost:8000

### 2. **test_ingestion.py** - Testes do Pipeline de Ingestão
- ✅ Google Drive Downloader
- ✅ File Selector
- ✅ LlamaParse Processor
- ✅ Multimodal Merger
- ✅ Voyage Embedder
- ✅ Cloudflare R2 Uploader
- ✅ Astra DB Inserter
- ✅ Pipeline completo
- ✅ Tratamento de erros

**Pré-requisitos:** Chaves de API configuradas (LlamaParse, Voyage, R2, Astra)

### 3. **test_search.py** - Testes do Sistema de Busca
- ✅ Query Transformer
- ✅ Vector Searcher
- ✅ Image Fetcher
- ✅ Search Reranker
- ✅ RAG Pipeline
- ✅ Conversational RAG
- ✅ Contexto conversacional
- ✅ Performance e casos extremos

**Pré-requisitos:** OpenAI, Voyage AI, Astra DB configurados

### 4. **test_evaluator.py** - Testes do Sistema de Avaliação
- ✅ Inicialização do avaliador
- ✅ Criação de dataset de teste
- ✅ Métricas de avaliação
- ✅ Execução de avaliação
- ✅ Geração de relatórios
- ✅ Configuração via ambiente
- ✅ Tratamento de erros

**Pré-requisitos:** Sistema RAG completo configurado

### 5. **test_integration.py** - Testes de Integração End-to-End
- ✅ Pipeline completo (ingestão → busca)
- ✅ Performance com múltiplas queries
- ✅ Fluxo conversacional
- ✅ Recuperação de erros
- ✅ Stress do sistema
- ✅ Casos de uso reais (restaurante, atendimento)
- ✅ Requisições concorrentes

**Pré-requisitos:** Sistema completo + API rodando

## 🏷️ Marcadores de Teste

### Marcadores Automáticos
- `slow` - Testes que demoram >30s (use `--run-slow`)
- `api` - Testes que usam APIs externas
- `integration` - Testes de integração
- `requires_all_apis` - Testes que precisam de todas as APIs

### Como Usar Marcadores
```bash
# Apenas testes rápidos
pytest tests/

# Incluir testes lentos
pytest tests/ --run-slow

# Apenas testes de API
pytest tests/ -m "api"

# Excluir testes de integração
pytest tests/ -m "not integration"
```

## ⚙️ Configuração

### Variáveis de Ambiente Importantes

```bash
# Para testes da API
TEST_API_URL=http://localhost:8000
API_KEY=sua-api-key-aqui

# Para testes de ingestão
LLAMA_CLOUD_API_KEY=sua-chave-llama
VOYAGE_API_KEY=sua-chave-voyage
R2_ENDPOINT=https://seu-worker.workers.dev
R2_AUTH_TOKEN=seu-token-r2
ASTRA_DB_APPLICATION_TOKEN=seu-token-astra
ASTRA_DB_API_ENDPOINT=seu-endpoint-astra

# Para testes de busca
OPENAI_API_KEY=sua-chave-openai
VOYAGE_API_KEY=sua-chave-voyage
ASTRA_DB_APPLICATION_TOKEN=seu-token-astra

# Para testes do avaliador
EVAL_QUESTIONS="Pergunta 1|Pergunta 2|Pergunta 3"
EVAL_KEYWORDS="palavra1,palavra2|palavra3,palavra4"
EVAL_CATEGORIES="categoria1|categoria2"
```

### Configuração Pytest

O arquivo `conftest.py` contém:
- Fixtures globais
- Configuração de marcadores
- Helpers de teste
- Skip automático para APIs não configuradas
- Configuração de logging

## 📈 Interpretando Resultados

### Status dos Testes
- ✅ **PASSED** - Teste passou
- ❌ **FAILED** - Teste falhou
- ⚠️ **SKIPPED** - Teste pulado (API não configurada)
- 🔄 **TIMEOUT** - Teste excedeu tempo limite

### Métricas Importantes
- **Taxa de Sucesso**: % de testes que passaram
- **Tempo de Execução**: Deve ser razoável (<30s para maioria)
- **Coverage**: Cobertura de funcionalidades

### Exemplos de Saída
```bash
tests/test_api.py::TestHealthAndBasics::test_health_check PASSED    [10%]
tests/test_api.py::TestAuthentication::test_valid_authentication PASSED [20%]
tests/test_search.py::TestRAGPipeline::test_search_and_answer SKIPPED [30%]
```

## 🐛 Troubleshooting

### Problemas Comuns

#### 1. "API não está acessível"
```bash
# Solução: Iniciar a API
python run_system_api.py
```

#### 2. "APIs não configuradas"
```bash
# Solução: Configurar variáveis no .env
cp .env.example .env
# Editar .env com suas chaves reais
```

#### 3. "Testes muito lentos"
```bash
# Solução: Executar apenas testes rápidos
pytest tests/ -x  # Para no primeiro erro
```

#### 4. "Muitos testes falhando"
```bash
# Verificar configuração básica
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('OpenAI:', bool(os.getenv('OPENAI_API_KEY')))
print('Voyage:', bool(os.getenv('VOYAGE_API_KEY')))
print('Astra:', bool(os.getenv('ASTRA_DB_APPLICATION_TOKEN')))
"
```

### Logs e Debug

```bash
# Executar com logs detalhados
pytest tests/ -v -s --tb=long

# Executar apenas um teste específico para debug
pytest tests/test_api.py::TestSearchEndpoint::test_search_basic -v -s
```

## 🎯 Boas Práticas

### Para Desenvolvedores

1. **Execute testes antes de commit:**
```bash
pytest tests/ -x
```

2. **Adicione testes para novas funcionalidades:**
   - Testes unitários em arquivos específicos
   - Testes de integração em `test_integration.py`

3. **Use marcadores apropriados:**
```python
@pytest.mark.slow
def test_long_operation():
    pass

@pytest.mark.requires_all_apis
def test_full_pipeline():
    pass
```

4. **Configure skips inteligentes:**
```python
@pytest.mark.skipif(not os.getenv('API_KEY'), reason="API key not configured")
def test_api_feature():
    pass
```

### Para CI/CD

```bash
# Pipeline básico (rápido)
pytest tests/ --skip-external -x

# Pipeline completo (com APIs)
pytest tests/ --run-slow

# Com relatórios
pytest tests/ --junitxml=results.xml --cov=sistema_rag
```

## 📞 Suporte

Se você encontrar problemas com os testes:

1. **Verifique pré-requisitos:** APIs configuradas, sistema rodando
2. **Execute teste individual:** `pytest tests/test_api.py::test_health_check -v`
3. **Verifique logs:** Use `-s` para ver prints e logs
4. **Consulte documentação:** `MANUAL_COMPLETO.md` e `API_DOCUMENTATION.md`

---

🔥 **Sistema RAG Multimodal - Arquitetura Modular Completa**