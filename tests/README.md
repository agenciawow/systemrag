# 🧪 Testes do Sistema RAG Multimodal

## 🎯 Estrutura Simplificada

Esta pasta contém testes organizados por funcionalidade específica.

### 📁 Estrutura

```
tests/
├── simple/                    # 🎯 TESTES SIMPLIFICADOS
│   ├── run_simple_tests.py    # Interface principal
│   ├── test_01_api_connections.py     # APIs e conectividade
│   ├── test_02_document_ingestion.py  # Ingestão de documentos
│   ├── test_03_system_rag_search.py   # Busca System RAG
│   ├── test_04_agents_search.py       # Busca com Agentes
│   ├── test_05_fastapi_stress.py      # Stress test APIs
│   ├── test_06_zep_memory.py          # Sistema memória Zep
│   ├── test_07_system_rag_evaluation.py # Avaliação System RAG
│   └── test_08_agents_evaluation.py   # Avaliação Agentes
├── README.md                 # Este arquivo
├── conftest.py               # Configuração pytest
└── run_tests_legacy.py       # Runner antigo (backup)
```

## 🚀 Como Executar

### Método Recomendado (Interface Interativa)

```bash
# Interface simplificada e amigável
python tests/simple/run_simple_tests.py

# Ou usar o atalho na raiz
python run_tests.py
```

### Execução Direta

```bash
# Teste específico
python tests/simple/run_simple_tests.py --test 01

# Todos os testes disponíveis
python tests/simple/run_simple_tests.py --all

# Ver status de todos os testes
python tests/simple/run_simple_tests.py --status
```

### Testes Legados (Avançado)

```bash
# Runner completo antigo
python tests/run_tests_legacy.py
```

## 📋 Testes Disponíveis

| ID | Nome | Tempo | Funcionalidade |
|----|------|-------|----------------|
| 01 | APIs e Conexões | 30s | Conectividade básica |
| 02 | Ingestão Documentos | 2min | Pipeline de ingestão |
| 03 | Busca System RAG | 1min | Sistema RAG tradicional |
| 04 | Busca Agentes | 2min | Agentes com memória |
| 05 | Stress FastAPI | 3min | Performance das APIs |
| 06 | Memória Zep | 3min | Sistema Zep |
| 07 | Avaliação RAG | 5min | Qualidade System RAG |
| 08 | Avaliação Agentes | 7min | Qualidade dos Agentes |

## 🎯 Perguntas de Avaliação

Os testes de avaliação usam **10 perguntas em português** baseadas no documento do Zep:

- **Básicas**: O que é o Zep? Qual é o principal componente?
- **Intermediárias**: Performance no benchmark DMR, Graphiti, limitações RAG
- **Avançadas**: Dados temporais, melhoria latência, síntese de dados

## 📊 Indicadores de Status

- ✅ **Pronto** - Todos os requisitos atendidos
- ⚠️ **Requer API** - Precisa iniciar API correspondente
- ❌ **Configuração** - Falta configurar variáveis de ambiente

---

💡 **Dica**: Use a interface interativa para uma experiência mais amigável!