# 🤖 Sistema de Agents RAG - Guia para Iniciantes

## 🎯 O que são Agents?

**Agents** são como "assistentes virtuais inteligentes" que conseguem pensar antes de responder. Enquanto o Sistema RAG tradicional funciona como uma "busca rápida", os Agents funcionam como um "consultor experiente" que analisa sua pergunta e dá respostas mais elaboradas.

### 🤔 **Quando usar Agents em vez do Sistema RAG tradicional?**

| Situação | Sistema RAG (8000) | Agents (8001) |
|----------|-------------------|---------------|
| Preciso de resposta rápida | ✅ **Recomendado** | ❌ Mais lento |
| Quero conversar como com uma pessoa | ❌ Respostas diretas | ✅ **Recomendado** |
| Site simples ou chatbot básico | ✅ **Ideal** | ❌ Complexo demais |
| Assistente virtual inteligente | ❌ Limitado | ✅ **Perfeito** |
| Primeira vez usando o sistema | ✅ **Comece aqui** | ❌ Use depois |

### 🚀 **Para Iniciantes: Recomendação**

1. **Comece sempre com o Sistema RAG tradicional** (porta 8000)
2. **Depois que dominar**, experimente os Agents (porta 8001) 
3. **Use ambos** para casos diferentes

---

## 🛠️ **Como Funciona Tecnicamente**

Sistema de agents inteligentes baseado no sistema RAG existente, mantendo total compatibilidade com a API atual.

## 🏗️ Arquitetura

```
📁 sistemarag/
├── 📄 run_agents_api.py          # 🚀 Script fácil para iniciar agents
│
├── 📁 agents/                    # 🤖 Sistema de Agents
│   ├── 📁 api/                   # API REST dos Agents (porta 8001)
│   │   ├── 📄 main.py           # FastAPI app principal
│   │   └── 📁 routes/           # Rotas organizadas
│   ├── 📁 core/                 # Core dos agents
│   │   ├── 📄 operator.py       # Descoberta automática de agents
│   │   ├── 📄 rag_search_agent.py  # Agent principal de busca
│   │   └── 📄 zep_client.py     # 🧠 Cliente Zep para memória persistente
│   └── 📁 tools/                # Ferramentas para agents
│       └── 📄 retrieval_tool.py # Tool de busca integrada
│
└── 📁 system_rag/               # 🔧 Sistema RAG original (inalterado)
```

## 🚀 Como Usar (Iniciantes)

### 1. **Sistema RAG Tradicional (Recomendado para começar)**
```bash
# Inicia API tradicional (mais simples)
python run_system_api.py
# Acessível em: http://localhost:8000
```

### 2. **Sistema de Agents (Depois que dominar o básico)**
```bash
# Inicia API de agents (mais inteligente)
python run_agents_api.py  
# Acessível em: http://localhost:8001
```

### 3. **Usando Ambos ao Mesmo Tempo**
```bash
# Terminal 1: Sistema RAG
python run_system_api.py

# Terminal 2: Agents (novo terminal)
python run_agents_api.py
```

### 4. **Testando se Funcionou**

Acesse no navegador após iniciar:
- **Sistema RAG**: http://localhost:8000/docs
- **Agents**: http://localhost:8001/docs

Você verá a documentação automática da API.

---

## 🧑‍💻 **Para Desenvolvedores (Avançado)**

### Descoberta Automática de Agents
```python
from agents.core.operator import agent_operator

# Listar agents disponíveis
agents = agent_operator.list_agents()
print(agents)

# Usar um agent diretamente
agent = agent_operator.get_agent("rag-search")
response = agent.ask("Qual é o objetivo do projeto?")
```

## 🔐 Autenticação

A API de agents usa o **mesmo sistema de autenticação** da API atual:

```http
Authorization: Bearer sistemarag-api-key-2024
```

**Configuração:**
- Variável de ambiente: `API_KEY`
- Valor padrão: `sistemarag-api-key-2024`
- Endpoint público: `GET /auth-info` (sem autenticação)

## 📡 Endpoints da API de Agentes

**⚠️ Todos os endpoints requerem autenticação Bearer Token**

### Listar Agentes
```http
GET /v1/agents
Authorization: Bearer sistemarag-api-key-2024
```

### Informações do Agente
```http
GET /v1/agents/{agent_id}
Authorization: Bearer sistemarag-api-key-2024
```

### Fazer Pergunta
```http
POST /v1/agents/{agent_id}/ask
Authorization: Bearer sistemarag-api-key-2024
Content-Type: application/json

{
  "message": "Sua pergunta aqui",
  "user_id": "user123",           # 🧠 OBRIGATÓRIO para memória Zep
  "session_id": "session123",     # 🧠 OBRIGATÓRIO para memória Zep 
  "clear_history": false
}
```

**🧠 Novos Parâmetros Obrigatórios (Zep Memory):**
- `user_id`: Identificador único do usuário (ex: "carlos", "user123")
- `session_id`: Identificador da sessão de conversa (ex: "trabalho", "session123")
- **Por que são obrigatórios?** Permitem que os agents lembrem de conversas anteriores e mantenham contexto entre sessões

### Histórico
```http
GET /v1/agents/{agent_id}/history
Authorization: Bearer sistemarag-api-key-2024

POST /v1/agents/{agent_id}/clear
Authorization: Bearer sistemarag-api-key-2024
```

### Teste
```http
GET /v1/agents/{agent_id}/test
Authorization: Bearer sistemarag-api-key-2024
```

## 🔧 Criando Novos Agentes

### 1. Estrutura Básica
```python
# agents/novo_agente.py
class NovoAgente:
    # Metadados para descoberta automática
    name = "Novo Agente"
    agent_id = "novo-agente"
    description = "Descrição do agente"
    
    def __init__(self):
        # Inicialização
        pass
    
    def ask(self, message: str) -> str:
        # Lógica principal
        return "resposta"
    
    def clear_history(self):
        # Limpar histórico
        pass
    
    def get_chat_history(self):
        # Retornar histórico
        return []
```

### 2. Descoberta Automática
- Salve na pasta `agents/`
- O operador descobre automaticamente
- Use `POST /v1/agents/refresh` para recarregar

## 🛠️ Componentes

### RetrievalTool
- Encapsula pipeline RAG até reranking
- Retorna documentos selecionados
- Deixa geração de resposta para o agente

### RAGSearchAgent  
- Agente especializado em busca
- Usa RetrievalTool + OpenAI para resposta
- Mantém histórico conversacional
- Suporte a imagens

### AgentOperator
- Descoberta automática de agents
- Cache de instâncias
- API dinâmica

## 🧪 Testes

```bash
# Testar sistema completo
python test_agent_system.py

# Testar apenas a tool
python -c "from tools.retrieval_tool import test_retrieval_tool; print(test_retrieval_tool())"
```

## 🔄 Vantagens da Abordagem

### ✅ Mantém Compatibilidade
- API atual (`api.py`) inalterada
- Sistema RAG original intacto
- Migração gradual possível

### ✅ Descoberta Automática
- Novos agentes = novos arquivos
- Zero alterações no roteamento
- Inspirado no framework Agno

### ✅ Modularidade
- Tool reutilizável
- Agentes especializados
- Fácil extensão

### ✅ Flexibilidade
- Histórico por agente
- Configuração individual
- Testes automáticos

## 🚦 Exemplo de Uso Completo

```python
import requests

# Headers de autenticação
headers = {
    "Authorization": "Bearer sistemarag-api-key-2024",
    "Content-Type": "application/json"
}

# Exemplo completo com memória Zep
url = "http://localhost:8001/v1/agents/rag-search/ask"
data = {
    "message": "Olá! Meu nome é João e sou desenvolvedor",
    "user_id": "joao123",
    "session_id": "conversa_trabalho"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())

# Segunda pergunta - agent lembra do contexto
data2 = {
    "message": "Você se lembra do meu nome e profissão?",
    "user_id": "joao123",
    "session_id": "conversa_trabalho"
}

response2 = requests.post(url, headers=headers, json=data2)
# Resposta: "Sim, você é o João e trabalha como desenvolvedor!"

# 1. Listar agentes
response = requests.get("http://localhost:8001/v1/agents", headers=headers)
agents = response.json()["agents"]
print(f"Agentes disponíveis: {[a['name'] for a in agents]}")

# 2. Fazer pergunta
response = requests.post(
    "http://localhost:8001/v1/agents/rag-search/ask",
    headers=headers,
    json={"message": "Qual é o objetivo do projeto?"}
)
answer = response.json()["response"]
print(f"Resposta: {answer}")

# 3. Ver histórico
response = requests.get("http://localhost:8001/v1/agents/rag-search/history", headers=headers)
history = response.json()["history"]
print(f"Histórico: {len(history)} mensagens")
```

## 🔗 Próximos Passos

1. **Teams**: Implementar sistema de teams (múltiplos agentes)
2. **Workflows**: Adicionar workflows mais complexos  
3. **Streaming**: Implementar respostas em streaming
4. **Autenticação**: Adicionar autenticação mais robusta
5. **Monitoramento**: Dashboard para monitorar agentes

## ⚙️ Configuração

As mesmas variáveis de ambiente do sistema RAG atual:
- `VOYAGE_API_KEY`
- `OPENAI_API_KEY` 
- `ASTRA_DB_API_ENDPOINT`
- `ASTRA_DB_APPLICATION_TOKEN`
- `CLOUDFLARE_R2_*` (opcional, para imagens)

---

🔥 **Sistema RAG Multimodal - Arquitetura Modular Completa**