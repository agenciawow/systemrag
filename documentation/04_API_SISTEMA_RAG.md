# 🚀 API do Sistema RAG Multimodal

## 📋 Visão Geral

FastAPI RESTful para busca inteligente e avaliação automática do Sistema RAG Multimodal. Otimizada para alta performance e uso contínuo em produção.

### 🔑 Características Principais

- ✅ **Autenticação fixa via API Key** - Ideal para integração contínua
- ✅ **Alta performance** - Instâncias reutilizadas, sem reinicialização
- ✅ **Documentação automática** - Swagger UI integrada
- ✅ **Validação de dados** - Pydantic models
- ✅ **Logs estruturados** - Monitoramento completo
- ✅ **CORS configurado** - Pronto para frontend
- ✅ **Health checks** - Monitoramento de saúde

---

## 🚀 Início Rápido

### 1. Instalação
```bash
pip install fastapi uvicorn
```

### 2. Configuração
Adicione no arquivo `.env`:
```bash
API_KEY=sua-chave-api-segura-aqui
```

### 3. Iniciar Servidor
```bash
# Desenvolvimento
python run_system_api.py

# Produção
uvicorn api:app --host 0.0.0.0 --port 8000 --workers 4
```

### 4. Acessar Documentação
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 Autenticação

### API Key via Bearer Token

Todas as rotas (exceto `/` e `/health`) requerem autenticação via Bearer token.

**Header necessário:**
```
Authorization: Bearer sua-api-key-aqui
```

**Exemplo com curl:**
```bash
curl -H "Authorization: Bearer sua-api-key" \
     -H "Content-Type: application/json" \
     http://localhost:8000/search \
     -d '{"query": "Seus produtos?"}'
```

**Exemplo com Python:**
```python
import requests

headers = {
    "Authorization": "Bearer sua-api-key",
    "Content-Type": "application/json"
}

response = requests.post(
    "http://localhost:8000/search",
    headers=headers,
    json={"query": "Quais produtos vocês têm?"}
)
```

---

## 📚 Endpoints

### 1. **GET /** - Informações da API
Retorna informações básicas da API.

**Response:**
```json
{
  "message": "Sistema RAG Multimodal API",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/health"
}
```

### 2. **GET /health** - Health Check
Verifica saúde da API e sistema RAG.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-06-16T14:30:00Z",
  "system_info": {
    "rag_initialized": true,
    "python_version": "3.12.1",
    "timestamp": "2024-06-16T14:30:00Z"
  }
}
```

### 3. **POST /search** - Busca Inteligente 🔍
Realiza busca no sistema RAG.

**Headers:**
- `Authorization: Bearer API_KEY` (obrigatório)

**Request Body:**
```json
{
  "query": "Quais produtos vocês têm no cardápio?",
  "include_history": false
}
```

**Response (Sucesso):**
```json
{
  "success": true,
  "answer": "Temos hambúrgueres, batatas fritas, refrigerantes...",
  "response_time": 5.23,
  "timestamp": "2024-06-16T14:30:00Z",
  "query": "Quais produtos vocês têm?"
}
```

**Response (Erro):**
```json
{
  "detail": {
    "success": false,
    "error": "Descrição do erro",
    "timestamp": "2024-06-16T14:30:00Z"
  }
}
```

### 4. **POST /evaluate** - Avaliação Automática 📊
Executa avaliação completa do sistema.

**Headers:**
- `Authorization: Bearer API_KEY` (obrigatório)

**Request Body:** Nenhum (usa configurações do .env)

**Response (Sucesso):**
```json
{
  "success": true,
  "total_questions": 10,
  "success_rate": 0.8,
  "average_response_time": 6.5,
  "timestamp": "2024-06-16T14:30:00Z",
  "summary": {
    "successful_evaluations": 8,
    "failed_evaluations": 2,
    "average_precision": 0.75,
    "average_recall": 0.73,
    "average_f1_score": 0.74,
    "average_keyword_coverage": 0.82,
    "evaluation_duration": 45.2
  }
}
```

### 5. **POST /ingest** - Ingestão de Documentos 📄
Indexa um novo documento a partir de uma URL.

**Headers:**
- `Authorization: Bearer API_KEY` (obrigatório)

**Request Body:**
```json
{
  "document_url": "https://drive.google.com/file/d/FILE_ID/view?usp=sharing",
  "document_name": "Nome do Documento",
  "overwrite": true
}
```

**Parâmetros:**
- `document_url` (obrigatório): URL do documento (Google Drive, PDF público, etc.)
- `document_name` (opcional): Nome para identificar o documento
- `overwrite` (opcional): Se deve sobrescrever documento existente (padrão: false)

**Response (Sucesso):**
```json
{
  "success": true,
  "message": "Documento indexado com sucesso",
  "document_name": "Nome do Documento",
  "chunks_created": 15,
  "processing_time": 45.3,
  "timestamp": "2024-06-16T14:30:00Z"
}
```

**Response (Erro):**
```json
{
  "detail": {
    "success": false,
    "error": "Descrição do erro",
    "timestamp": "2024-06-16T14:30:00Z"
  }
}
```

**Tipos de URL Suportadas:**
- ✅ Google Drive (compartilhamento público)
- ✅ URLs de PDFs públicos
- ✅ Links diretos para documentos

**⚠️ Considerações:**
- Processamento pode demorar 30-300 segundos
- Configure timeout alto (5+ minutos)
- Consome créditos das APIs (LlamaParse, Voyage, etc.)

---

## 💡 Exemplos de Uso

### JavaScript/Node.js
```javascript
const axios = require('axios');

const API_KEY = 'sua-api-key';
const BASE_URL = 'http://localhost:8000';

const headers = {
  'Authorization': `Bearer ${API_KEY}`,
  'Content-Type': 'application/json'
};

// Busca
async function search(query) {
  try {
    const response = await axios.post(`${BASE_URL}/search`, {
      query: query,
      include_history: false
    }, { headers });
    
    return response.data;
  } catch (error) {
    console.error('Erro na busca:', error.response.data);
  }
}

// Avaliação
async function evaluate() {
  try {
    const response = await axios.post(`${BASE_URL}/evaluate`, {}, { headers });
    return response.data;
  } catch (error) {
    console.error('Erro na avaliação:', error.response.data);
  }
}

// Ingestão
async function ingest(documentUrl, documentName) {
  try {
    const response = await axios.post(`${BASE_URL}/ingest`, {
      document_url: documentUrl,
      document_name: documentName,
      overwrite: true
    }, { 
      headers,
      timeout: 300000 // 5 minutos
    });
    return response.data;
  } catch (error) {
    console.error('Erro na ingestão:', error.response.data);
  }
}

// Uso
search("Quais produtos vocês têm?").then(result => {
  console.log('Resposta:', result.answer);
});

ingest("https://drive.google.com/file/d/FILE_ID/view", "Novo Cardápio").then(result => {
  console.log('Documento processado:', result.document_name);
  console.log('Chunks criados:', result.chunks_created);
});
```

### Python com requests
```python
import requests
import os

API_KEY = os.getenv('API_KEY')
BASE_URL = 'http://localhost:8000'

headers = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

def search(query):
    """Realizar busca"""
    response = requests.post(
        f'{BASE_URL}/search',
        headers=headers,
        json={
            'query': query,
            'include_history': False
        }
    )
    return response.json()

def evaluate():
    """Executar avaliação"""
    response = requests.post(
        f'{BASE_URL}/evaluate',
        headers=headers
    )
    return response.json()

def ingest(document_url, document_name=None):
    """Indexar documento"""
    response = requests.post(
        f'{BASE_URL}/ingest',
        headers=headers,
        json={
            'document_url': document_url,
            'document_name': document_name,
            'overwrite': True
        },
        timeout=300  # 5 minutos
    )
    return response.json()

# Uso
result = search("Quais produtos vocês têm?")
print(f"Resposta: {result['answer']}")

eval_result = evaluate()
print(f"Taxa de sucesso: {eval_result['success_rate']:.1%}")

ingest_result = ingest("https://drive.google.com/file/d/FILE_ID/view", "Novo Cardápio")
print(f"Documento: {ingest_result['document_name']}")
print(f"Chunks: {ingest_result['chunks_created']}")
```

### PHP
```php
<?php
$apiKey = 'sua-api-key';
$baseUrl = 'http://localhost:8000';

$headers = [
    'Authorization: Bearer ' . $apiKey,
    'Content-Type: application/json'
];

// Busca
function search($query) {
    global $baseUrl, $headers;
    
    $data = json_encode([
        'query' => $query,
        'include_history' => false
    ]);
    
    $ch = curl_init($baseUrl . '/search');
    curl_setopt($ch, CURLOPT_POST, 1);
    curl_setopt($ch, CURLOPT_POSTFIELDS, $data);
    curl_setopt($ch, CURLOPT_HTTPHEADER, $headers);
    curl_setopt($ch, CURLOPT_RETURNTRANSFER, true);
    
    $response = curl_exec($ch);
    curl_close($ch);
    
    return json_decode($response, true);
}

// Uso
$result = search("Quais produtos vocês têm?");
echo "Resposta: " . $result['answer'];
?>
```

---

## 🔧 Configuração para Produção

### 1. Configuração do Servidor
```bash
# Uvicorn com múltiplos workers
uvicorn api:app \
  --host 0.0.0.0 \
  --port 8000 \
  --workers 4 \
  --log-level info \
  --access-log

# Com SSL (recomendado)
uvicorn api:app \
  --host 0.0.0.0 \
  --port 443 \
  --ssl-keyfile private.key \
  --ssl-certfile certificate.crt
```

### 2. Nginx como Proxy Reverso
```nginx
server {
    listen 80;
    server_name seu-dominio.com;
    
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeout para requests longas (avaliação)
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
}
```

### 3. Docker
```dockerfile
FROM python:3.12-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 4. Variáveis de Ambiente para Produção
```bash
# Segurança
API_KEY=chave-super-segura-production-2024

# OpenAI
OPENAI_API_KEY=sk-sua-chave-real

# Performance (use modelos menores se necessário)
OPENAI_ANSWER_GENERATION_MODEL=gpt-4o-mini
OPENAI_RERANK_MODEL=gpt-4o-mini
```

---

## 📊 Monitoramento

### Logs
A API gera logs estruturados para monitoramento:

```
2024-06-16 14:30:01 - INFO - 📥 POST /search
2024-06-16 14:30:06 - INFO - 📤 POST /search - Status: 200 - Tempo: 5.23s
```

### Métricas Importantes
- **Tempo de resposta** - Deve ser < 10s para busca
- **Taxa de sucesso** - Deve ser > 80% nas avaliações
- **Uso de memória** - Monitorar instâncias RAG
- **Rate limit** - Implementar se necessário

### Health Check para Load Balancer
```bash
# Verificação simples
curl -f http://localhost:8000/health || exit 1

# Verificação completa
curl -H "Authorization: Bearer sua-api-key" \
     http://localhost:8000/health \
     | jq '.status == "healthy"'
```

---

## 🚨 Códigos de Erro

| Código | Significado | Ação |
|--------|-------------|------|
| 200 | Sucesso | - |
| 401 | API Key inválida | Verificar header Authorization |
| 422 | Dados inválidos | Verificar formato do JSON |
| 500 | Erro interno | Verificar logs do servidor |
| 503 | Serviço indisponível | Sistema RAG não inicializado |

---

## 🔒 Segurança

### Melhores Práticas
1. **Use HTTPS em produção**
2. **API Key forte** - Mínimo 32 caracteres
3. **Rate limiting** - Implemente conforme necessário
4. **Logs auditáveis** - Não logue dados sensíveis
5. **Firewall** - Restrinja IPs se possível
6. **Backup** - Configure backup das configurações

### Exemplo de API Key Segura
```bash
# Gerar API key segura (Linux/Mac)
openssl rand -hex 32

# Ou usar Python
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## 📈 Performance

### Benchmarks Típicos
- **Busca simples**: 3-8 segundos
- **Avaliação completa**: 30-120 segundos (dependendo do número de perguntas)
- **Inicialização**: 5-15 segundos

### Otimizações
1. **Use modelos menores** para desenvolvimento
2. **Cache de instâncias** - Já implementado
3. **Múltiplos workers** - Para alta carga
4. **CDN** - Para assets estáticos

---

## 🤝 Integração

### Webhook Example
```python
# Exemplo de webhook que chama a API
from flask import Flask, request
import requests

app = Flask(__name__)

@app.route('/webhook', methods=['POST'])
def webhook():
    data = request.json
    question = data.get('question')
    
    # Chamar API do RAG
    response = requests.post(
        'http://localhost:8000/search',
        headers={'Authorization': 'Bearer sua-api-key'},
        json={'query': question}
    )
    
    return response.json()
```

### Chatbot Integration
```python
# Exemplo para chatbot
class RAGChatbot:
    def __init__(self, api_key, base_url):
        self.api_key = api_key
        self.base_url = base_url
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
    
    def ask(self, question):
        response = requests.post(
            f'{self.base_url}/search',
            headers=self.headers,
            json={'query': question}
        )
        
        if response.status_code == 200:
            return response.json()['answer']
        else:
            return "Desculpe, não consegui processar sua pergunta."

# Uso
bot = RAGChatbot('sua-api-key', 'http://localhost:8000')
answer = bot.ask("Quais produtos vocês têm?")
```

---

🔥 **Sistema RAG Multimodal - Arquitetura Modular Completa**