# 🧠 Integração Zep - Gerenciamento de Memória Avançado

> Sistema avançado de memória persistente para agents com contexto conversacional inteligente

## 🎯 **O que é o Zep?**

O **Zep** é uma plataforma de gerenciamento de memória para aplicações de IA conversacional que oferece:

- **Memória persistente** entre sessões
- **Extração automática** de fatos e entidades
- **Grafos de conhecimento** dinâmicos
- **Busca semântica** no histórico
- **Resumos automáticos** de conversas

## ⚡ **Integração no Sistema**

### 🔧 **Configuração**

1. **Obter API Key do Zep**:
   - Acesse: https://cloud.getzep.com
   - Crie uma conta
   - Gere uma API Key

2. **Configurar variáveis de ambiente**:
   ```bash
   # No arquivo .env
   ZEP_API_KEY=your-zep-api-key-here
   ```

3. **Instalar dependências**:
   ```bash
   pip install zep-cloud
   ```

### 🏗️ **Arquitetura da Integração**

```
agents/core/
├── zep_client.py      # 🧠 Cliente oficial Zep SDK
├── rag_search_agent.py # 🤖 Agent com integração Zep
└── operator.py        # 🎯 Operador de agents
```

## 🚀 **Funcionalidades Implementadas**

### 1. **Gerenciamento de Usuários**
- Criação automática de usuários
- Vinculação correta de sessões
- Tratamento de usuários existentes

### 2. **Gerenciamento de Sessões**
- Criação explícita com `user_id` vinculado
- Verificação de sessões existentes
- Contexto isolado por sessão

### 3. **Persistência de Mensagens**
- Salvamento automático de mensagens user/assistant
- Formato padronizado com timestamps
- Recuperação de histórico completo

### 4. **Geração de Memória**
- Extração automática de fatos importantes
- Resumos de conversas
- Grafos de conhecimento dinâmicos

## 🔄 **Fluxo de Execução**

### **Fluxo Completo do Zep:**

```mermaid
graph TD
    A[Receber mensagem] --> B{Usuário existe?}
    B -->|Não| C[Criar usuário]
    B -->|Sim| D[Verificar sessão]
    C --> D
    D -->|Nova| E[Criar sessão com user_id]
    D -->|Existente| F[Buscar contexto]
    E --> F
    F --> G[Buscar memória + mensagens]
    G --> H[Adicionar mensagem do usuário]
    H --> I[Processar com agent + contexto]
    I --> J[Adicionar resposta do assistente]
    J --> K[Retornar resposta]
```

### **Exemplo de Código:**

```python
from agents.core.operator import agent_operator

# Obter agent
agent = agent_operator.get_agent(\"rag-search\")

# Usar com memória Zep
response = agent.ask(
    \"Olá! Meu nome é João e sou desenvolvedor\",
    user_id=\"user123\",
    session_id=\"session123\"
)

# Segunda mensagem - agent lembra do contexto
response2 = agent.ask(
    \"Você se lembra do meu nome?\",
    user_id=\"user123\", 
    session_id=\"session123\"
)
# Resposta: \"Sim, você é o João, desenvolvedor!\"
```

## 🛠️ **Configuração Detalhada**

### **Classe ZepClient**

```python
from agents.core.zep_client import get_zep_client, ZepMessage

# Obter cliente
zep_client = get_zep_client()

# Criar usuário
user = zep_client.create_user(\"user123\")

# Adicionar mensagens
messages = [
    ZepMessage(content=\"Olá!\", role_type=\"user\"),
    ZepMessage(content=\"Olá! Como posso ajudar?\", role_type=\"assistant\")
]
zep_client.add_memory_to_session(\"session123\", messages, \"user123\")

# Buscar contexto
context, msgs, is_new = zep_client.ensure_session_context(\"session123\", \"user123\")
```

### **Parâmetros Obrigatórios na API**

Na **API de Agents** (porta 8001), os parâmetros `user_id` e `session_id` são **obrigatórios**:

```bash
curl -X POST \"http://localhost:8001/v1/agents/rag-search/ask\" \\
  -H \"Authorization: Bearer sistemarag-api-key-secure-2024\" \\
  -H \"Content-Type: application/json\" \\
  -d '{
    \"message\": \"Olá! Meu nome é Carlos\",
    \"user_id\": \"carlos123\",
    \"session_id\": \"session_carlos\"
  }'
```

## 📊 **Monitoramento no Painel Zep**

### **Verificar no Painel:**
1. Acesse: https://cloud.getzep.com
2. Vá para **Users** → procure por seu `user_id`
3. Clique no usuário → **Sessions**
4. Veja as mensagens e memória gerada

### **Estrutura no Painel:**
```
Users
├── user123
│   ├── Sessions
│   │   └── session123
│   │       ├── Messages (user + assistant)
│   │       ├── Memory Summary
│   │       ├── Facts Extracted
│   │       └── Entities
│   └── Graph Knowledge
```

## 🧪 **Testes**

### **Executar Testes do Zep:**

```bash
# Teste específico do Zep
python -m pytest tests/agents/test_zep_integration.py -v

# Ou via runner
python tests/run_tests.py --zep

# Menu interativo
python tests/run_tests.py
# Escolha: \"8. Testes de Integração Zep\"
```

### **Testes Incluídos:**
- ✅ Criação de usuários
- ✅ Gerenciamento de sessões  
- ✅ Persistência de mensagens
- ✅ Geração de memória
- ✅ Recuperação de contexto
- ✅ Integração com agents
- ✅ Casos extremos e robustez

## 🔧 **Solução de Problemas**

### **Problemas Comuns:**

#### 1. **API Key não configurada**
```bash
# Erro: \"ZEP_API_KEY não encontrada\"
# Solução: Configure no .env
ZEP_API_KEY=sua-chave-aqui
```

#### 2. **Usuários duplicados no painel**
```bash
# Problema: Usuários com hash automático
# Causa: Sessão não vinculada ao user_id
# Solução: Use user_id e session_id obrigatórios na API
```

#### 3. **Mensagens não aparecem**
```bash
# Problema: Mensagens não salvam
# Causa: Erro na criação de sessão
# Solução: Verificar logs e configuração da API Key
```

### **Debug Detalhado:**

```python
# Script de debug
python -c \"
from agents.core.zep_client import get_zep_client, is_zep_available
print('Zep disponível:', is_zep_available())
if is_zep_available():
    client = get_zep_client()
    print('Cliente criado:', client is not None)
\"
```

## 📈 **Benefícios da Integração**

### **Para Usuários:**
- 🧠 **Memória persistente** entre conversas
- 🎯 **Contexto relevante** automaticamente aplicado
- 📚 **Histórico completo** de interações

### **Para Desenvolvedores:**
- 🔧 **SDK oficial** bem documentado
- 📊 **Métricas detalhadas** no painel
- 🚀 **Escalabilidade** para múltiplos usuários
- 🛡️ **Isolamento** por usuário e sessão

### **Para o Sistema:**
- ⚡ **Performance** otimizada com cache
- 🔒 **Segurança** com isolamento de dados
- 📈 **Escalabilidade** para produção
- 🔄 **Reliability** com tratamento de erros

## 🎯 **Casos de Uso**

### **1. Assistente Pessoal**
```python
# João conversa sobre trabalho
agent.ask(\"Trabalho como engenheiro de software\", user_id=\"joao\", session_id=\"trabalho\")

# Mais tarde, em outra conversa
agent.ask(\"Como posso melhorar no meu trabalho?\", user_id=\"joao\", session_id=\"trabalho\")
# Agent lembra que João é engenheiro de software
```

### **2. Suporte ao Cliente**
```python
# Cliente relata problema
agent.ask(\"Estou com problema no produto X\", user_id=\"cliente123\", session_id=\"suporte\")

# Agente de follow-up
agent.ask(\"O problema foi resolvido?\", user_id=\"cliente123\", session_id=\"suporte\") 
# Agent lembra do problema específico
```

### **3. Sessões Múltiplas**
```python
# Sessão sobre vendas
agent.ask(\"Preciso de info sobre vendas\", user_id=\"user1\", session_id=\"vendas\")

# Sessão sobre marketing  
agent.ask(\"Preciso de info sobre marketing\", user_id=\"user1\", session_id=\"marketing\")
# Contextos isolados por sessão
```

## 🔗 **Links Úteis**

- 🌐 **Zep Cloud Dashboard**: https://cloud.getzep.com
- 📚 **Documentação Zep**: https://docs.getzep.com
- 🐍 **SDK Python**: https://pypi.org/project/zep-cloud/
- 📖 **Exemplos de Código**: [Testes Zep](../tests/agents/test_zep_integration.py)

---

**💡 Dica**: Use sempre os mesmos `user_id` e `session_id` para manter contexto entre conversas. O Zep gerenciará automaticamente a memória e o contexto relevante!