# 🤖 Sistema de Agentes

Diretório centralizado para todo o sistema de agentes inteligentes.

## 📁 **Estrutura**

```
agentes/
├── core/                    # 🧠 Agentes e operadores principais
│   ├── operator.py         # Descoberta automática de agentes
│   ├── rag_search_agent.py # Agente de busca RAG
│   └── __init__.py
├── tools/                   # 🔧 Ferramentas reutilizáveis
│   ├── retrieval_tool.py   # Tool de busca vetorial
│   └── __init__.py
├── api/                     # 🔌 Interface REST
│   ├── main.py             # FastAPI app principal
│   ├── auth.py             # Sistema de autenticação
│   └── routes/             # Rotas da API
├── test_agent_system.py    # 🧪 Testes do sistema
├── test_agent_auth.py      # 🔐 Testes de autenticação
└── README.md               # Este arquivo
```

## 🚀 **Como Usar**

### **Desenvolver um novo agente:**
1. Crie arquivo em `core/` (ex: `novo_agente.py`)
2. Implemente classe com metadados necessários
3. Agente será descoberto automaticamente

### **Criar uma nova tool:**  
1. Adicione arquivo em `tools/`
2. Exporte na `__init__.py`
3. Use em qualquer agente

### **Rodar API de agentes:**
```bash
python agentes/api/main.py
# ou
python -m agentes.api.main
```

### **Testar sistema:**
```bash
python agentes/test_agent_system.py
python agentes/test_agent_auth.py  
```

## 🔧 **Imports**

```python
# Importar componentes principais
from agentes import agent_operator, RAGSearchAgent, RetrievalTool

# Uso básico
agente = agent_operator.get_agent("rag-search")
resposta = agente.ask("Sua pergunta")
```

## 📚 **Documentação**

Para documentação completa, veja:
- [**README_AGENTES.md**](../documentation/README_AGENTES.md) - Guia completo
- [**API Documentation**](../documentation/API_DOCUMENTATION.md) - APIs
- [**Manual Completo**](../documentation/MANUAL_COMPLETO.md) - Setup geral

## 🎯 **Desenvolvimento**

### **Padrões:**
- Agentes devem ter `name`, `agent_id`, `description`
- Tools devem ser reutilizáveis e testáveis
- API segue padrão REST com autenticação

### **Testes:**
- Cada componente deve ter testes
- Use `test_agent_system.py` como modelo
- Sempre teste descoberta automática