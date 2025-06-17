# 🤖 API de Agentes - Sistema RAG Multimodal com Memória Zep

## ⚡ Início Rápido

### 1. Instalação
```bash
pip install fastapi uvicorn
```

### 2. Configurar Variáveis de Ambiente
Configure no arquivo `.env`:
```bash
# Obrigatória - Sistema falha se não configurada
API_KEY=sua-chave-api-segura-aqui

# Obrigatória - Para memória persistente dos agentes
ZEP_API_KEY=sua-chave-zep-aqui

# Configuração do servidor (opcional)
AGENTS_HOST=0.0.0.0
AGENTS_PORT=8001

# CORS seguro (opcional)
CORS_ALLOW_ORIGINS=http://localhost:3000,http://localhost:8000,http://localhost:8001
```

### 3. Iniciar API
```bash
# Desenvolvimento
python run_agents_api.py

# Produção
uvicorn api:app --host 0.0.0.0 --port 8001 --workers 4
```

### 4. Testar
```bash
# Documentação automática
http://localhost:8001/docs

# Testes automatizados focados
python run_tests.py --test 04  # Busca com Agentes
python run_tests.py --test 06  # Sistema de Memória Zep
python run_tests.py --test 08  # Avaliação dos Agentes
```

---

## 🔑 Autenticação

**Todas as rotas requerem API Key via Bearer token:**

```bash
curl -H "Authorization: Bearer sistemarag-api-key-secure-2024" \
     -H "Content-Type: application/json" \
     http://localhost:8001/search \
     -d '{"query": "Seus produtos?"}'
```

---

## 📚 Rotas Principais

### 🔍 POST /search - Busca Inteligente
```json
{
  "query": "Quais produtos vocês têm?",
  "user_id": "user123",
  "session_id": "session123",
  "include_history": false
}
```

**🧠 Parâmetros Obrigatórios (Zep Memory):**
- `user_id`: Identificador único do usuário (ex: "carlos", "user123")
- `session_id`: Identificador da sessão de conversa (ex: "trabalho", "session123")
- **Por que são obrigatórios?** Permitem que os agents usem o Zep para lembrar de conversas anteriores e manter contexto entre sessões

**Resposta:**
```json
{
  "success": true,
  "answer": "Temos hambúrgueres, batatas fritas...",
  "response_time": 5.23,
  "timestamp": "2024-06-16T14:30:00Z",
  "query": "Quais produtos vocês têm?"
}
```

### 📊 POST /evaluate - Avaliação Automática
```bash
curl -X POST \
  -H "Authorization: Bearer sua-api-key" \
  http://localhost:8001/evaluate
```

**Resposta:**
```json
{
  "success": true,
  "total_questions": 10,
  "success_rate": 0.8,
  "average_response_time": 6.5,
  "summary": {
    "successful_evaluations": 8,
    "failed_evaluations": 2,
    "average_precision": 0.75
  }
}
```

### 📄 POST /ingest - Indexar Documentos
```json
{
  "document_url": "https://drive.google.com/file/d/FILE_ID/view",
  "document_name": "Novo Cardápio",
  "overwrite": true
}
```

**Resposta:**
```json
{
  "success": true,
  "message": "Documento indexado com sucesso",
  "document_name": "Novo Cardápio",
  "chunks_created": 15,
  "processing_time": 45.3
}
```

---

## 🎯 Características

- ✅ **Autenticação fixa** - API Key reutilizável
- ✅ **Alta performance** - Instâncias reutilizadas
- ✅ **Documentação automática** - Swagger UI
- ✅ **Validação de dados** - Pydantic models
- ✅ **CORS habilitado** - Pronto para frontend
- ✅ **Logs estruturados** - Monitoramento completo

---

## 💡 Exemplos de Integração

### JavaScript
```javascript
const response = await fetch('http://localhost:8001/search', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer sua-api-key',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: 'Quais produtos vocês têm?',
    user_id: 'user123',
    session_id: 'session123'
  })
});

const data = await response.json();
console.log(data.answer);
```

### Python
```python
import requests

response = requests.post(
    'http://localhost:8001/search',
    headers={'Authorization': 'Bearer sua-api-key'},
    json={
        'query': 'Quais produtos vocês têm?',
        'user_id': 'user123',
        'session_id': 'session123'
    }
)

print(response.json()['answer'])
```

---

## 🚀 Deploy em Produção

### Docker
```dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
EXPOSE 8001
CMD ["uvicorn", "api:app", "--host", "0.0.0.0"]
```

### Nginx
```nginx
location /api/ {
    proxy_pass http://127.0.0.1:8001/;
    proxy_read_timeout 300s;
}
```

---

## 📋 Arquivos Criados

- **`api.py`** - Código principal da FastAPI
- **`test_api.py`** - Script de testes automatizados
- **`API_DOCUMENTATION.md`** - Documentação completa
- **`README_API.md`** - Este guia rápido

---

## 🔧 Configurações Importantes

### Performance
```bash
# Use modelos menores para economia
OPENAI_ANSWER_GENERATION_MODEL=gpt-4o-mini
OPENAI_RERANK_MODEL=gpt-4o-mini
```

### Segurança
```bash
# API Key forte (32+ caracteres)
API_KEY=sua-chave-super-segura-aqui-2024-production
```

### Produção
```bash
# Múltiplos workers
uvicorn api:app --workers 4 --host 0.0.0.0 --port 8001
```

---

## 🚨 Troubleshooting

**API não inicia:**
```bash
# Verificar dependências
pip install fastapi uvicorn

# Verificar configuração
python -c "from api import app; print('OK')"
```

**Erro 401 - Unauthorized:**
- Verificar se API_KEY está no .env
- Confirmar header: `Authorization: Bearer sua-chave`

**Erro 503 - Service Unavailable:**
- Sistema RAG não conseguiu inicializar
- Verificar todas as chaves de API (OpenAI, Voyage, etc.)

**Timeout:**
- Queries muito complexas podem demorar
- Aumentar timeout do cliente para 60s+

---

🔥 **Sistema RAG Multimodal - Arquitetura Modular Completa**