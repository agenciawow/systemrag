# 🚀 Sistema RAG Multimodal - Python Puro

Sistema completo de RAG (Retrieval-Augmented Generation) multimodal implementado em Python puro, seguindo arquitetura modular e componente por componente.

## 📋 Visão Geral

Este sistema implementa um pipeline completo para processamento de documentos multimodais (texto + imagens) com capacidades de busca vetorial e geração de respostas contextualizadas.

### 🏗️ Arquitetura Atual

```
📁 sistemarag/
├── 🚀 Scripts de Execução (Iniciantes)
│   ├── 📄 run_system_api.py     # Inicia API Sistema RAG (porta 8000)
│   ├── 📄 run_agents_api.py     # Inicia API Agents (porta 8001)
│   └── 📄 run_tests.py          # Executa todos os testes
│
├── 📁 system_rag/               # 🔧 Sistema RAG Core
│   ├── 📁 api/                  # API REST Sistema RAG (porta 8000)
│   ├── 📁 config/               # Configurações globais
│   ├── 📁 models/               # Modelos de dados
│   ├── 📁 utils/                # Utilitários e helpers
│   ├── 📁 ingestion/            # 🚀 Sistema de Ingestão
│   │   ├── 📁 ingestion/        # Download de documentos
│   │   ├── 📁 processing/       # Processamento de documentos
│   │   ├── 📁 storage/          # Armazenamento (R2 + Astra DB)
│   │   └── 📄 run_pipeline.py   # Pipeline de ingestão
│   ├── 📁 search/               # 🔍 Sistema de Busca
│   │   ├── 📁 embeddings/       # Geração de embeddings
│   │   ├── 📁 retrieval/        # Busca e recuperação
│   │   └── 📄 conversational_rag.py  # Interface conversacional
│   ├── 📄 ingestion.py          # Script de ingestão
│   ├── 📄 search.py             # Script de busca
│   └── 📄 rag_evaluator.py      # Sistema de avaliação
│
├── 📁 agents/                   # 🤖 Sistema de Agents (Avançado)
│   ├── 📁 api/                  # API REST Agents (porta 8001)
│   ├── 📁 core/                 # Agents, operadores e Zep client
│   │   ├── 📄 zep_client.py     # 🧠 Cliente Zep para memória persistente
│   │   ├── 📄 rag_search_agent.py # Agent principal com integração Zep
│   │   └── 📄 operator.py       # Operador de descoberta automática
│   ├── 📁 tools/                # Ferramentas para agents
│   └── 📄 agent_evaluator.py    # Avaliação de agents
│
├── 📁 tests/                    # 🧪 Testes Organizados
│   ├── 📁 system_rag/           # Testes do sistema RAG
│   ├── 📁 agents/               # Testes dos agents
│   └── 📄 run_tests.py          # Executor completo de testes
│
├── 📁 test_configs/             # ⚙️ Configurações de Teste
│   ├── 📄 system_rag_questions.json   # Perguntas para avaliação RAG
│   └── 📄 agent_questions.json        # Perguntas para avaliação agents
│
└── 📁 documentation/            # 📚 Documentação Completa
    ├── 📄 README.md             # Índice da documentação
    ├── 📄 02_MANUAL_INSTALACAO_USO.md  # Manual para iniciantes
    └── 📄 ...                   # Outros guias especializados
```

## 🔧 Componentes Implementados

### ✅ Sistema Dual de APIs

#### 🔧 **API Sistema RAG (Porta 8000)**
- **FastAPI** tradicional com endpoints clássicos
- **3 Endpoints Principais** - Busca, Avaliação e Ingestão
- **Ideal para**: Sites, chatbots simples, integrações diretas
- **Características**: Rápido, direto, confiável

#### 🤖 **API de Agents (Porta 8001)**
- **Sistema inteligente** com agents conversacionais
- **Descoberta automática** de agents disponíveis
- **Ideal para**: Assistentes virtuais, conversação complexa
- **Características**: Mais inteligente, mantém contexto

### ✅ Ingestão de Documentos
- **Google Drive Downloader** - Download automático de arquivos do Google Drive
- **File Selector** - Seleção inteligente de arquivos com múltiplos critérios
- **Suporte Multiformat** - PDF, DOCX, PPTX, XLSX, TXT, MD

### ✅ Processamento de Documentos  
- **LlamaParse Processor** - Processamento com LlamaParse + screenshots
- **Multimodal Merger** - Combinação de texto e imagens em chunks
- **Otimização Automática** - Chunks inteligentes por tipo de documento

### ✅ Sistema de Embeddings
- **Voyage Embedder** - Embeddings multimodais com Voyage AI
- **Cache Inteligente** - Evita reprocessamento desnecessário

### ✅ Armazenamento
- **Cloudflare R2 Uploader** - Upload otimizado de imagens
- **Astra DB Inserter** - Inserção otimizada no Astra DB
- **Organização Automática** - Estrutura de pastas por data

### ✅ Sistema de Busca Modular
- **RAG Pipeline** - Pipeline completo de busca e resposta
- **Query Transformer** - Transformação inteligente de queries conversacionais
- **Vector Searcher** - Busca vetorial otimizada no Astra DB
- **Image Fetcher** - Busca de imagens do Cloudflare R2
- **Reranker** - Reordenação inteligente com GPT-4

### ✅ Sistema de Agents (Avançado)
- **Agent Operator** - Descoberta automática de agents
- **RAG Search Agent** - Agent especializado em busca
- **Retrieval Tool** - Ferramenta modular para busca
- **Agent Evaluator** - Avaliação específica de agents

### ✅ Suíte de Testes Automatizados
- **Testes Organizados** - Separados por sistema (RAG + Agents)
- **Menu Interativo** - Interface amigável para execução
- **Testes Específicos** - API, Ingestão, Busca, Agents, Integração
- **Configuração Flexível** - Perguntas configuráveis por JSON
- **Runner Inteligente** - Execução seletiva por categoria

### ✅ Documentação Completa para Iniciantes
- **Manual de Instalação** - Passo-a-passo para iniciantes
- **Guias Especializados** - Para cada componente do sistema
- **Exemplos Práticos** - Casos de uso reais
- **Troubleshooting** - Soluções para problemas comuns

## 📦 Dependências

```bash
pip install -r requirements.txt
```

### APIs Necessárias

1. **LlamaParse** - Processamento de documentos
2. **Voyage AI** - Embeddings multimodais  
3. **Cloudflare R2** - Armazenamento de imagens
4. **Astra DB** - Banco vetorial
5. **OpenAI** (opcional) - Para reranking e geração

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Copie `.env.example` para `.env` e configure:

```bash
# APIs Externas
OPENAI_API_KEY=sk-your-openai-key-here
VOYAGE_API_KEY=pa-your-voyage-key-here
LLAMA_CLOUD_API_KEY=llx-your-llama-key-here

# APIs para Modo Multimodal LlamaParse (opcional, reduz custo)
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-api-key-here

# Astra DB
ASTRA_DB_APPLICATION_TOKEN=AstraCS:your-token-here
ASTRA_DB_API_ENDPOINT=https://database-id-region.apps.astra.datastax.com
ASTRA_DB_KEYSPACE=default_keyspace
ASTRA_DB_COLLECTION=agenciawow

# Cloudflare R2
R2_ENDPOINT=https://your-worker.workers.dev
R2_AUTH_TOKEN=your-r2-token-here

# Google Drive Document
GOOGLE_DRIVE_URL=https://drive.google.com/file/d/YOUR_FILE_ID/view

# Configuração dos Modelos OpenAI (opcional - usa defaults se não definido)
# Reranking de resultados
OPENAI_RERANK_MODEL=gpt-4.1-mini
OPENAI_RERANK_TEMPERATURE=0.1

# Transformação de queries
OPENAI_QUERY_TRANSFORM_MODEL=gpt-4.1-mini
OPENAI_QUERY_TRANSFORM_TEMPERATURE=0.3

# Geração de respostas finais
OPENAI_ANSWER_GENERATION_MODEL=gpt-4.1
OPENAI_ANSWER_GENERATION_TEMPERATURE=0.7

# Extração de dados estruturados
OPENAI_EXTRACTION_MODEL=gpt-4.1
OPENAI_EXTRACTION_TEMPERATURE=0.1
```

### 1.1. Configuração dos Modelos OpenAI

O sistema permite configurar diferentes modelos para cada função:

- **OPENAI_RERANK_MODEL**: Modelo para reordenar resultados (padrão: `gpt-4o`)
- **OPENAI_QUERY_TRANSFORM_MODEL**: Modelo para transformar perguntas (padrão: `gpt-4o-mini`) 
- **OPENAI_ANSWER_GENERATION_MODEL**: Modelo para gerar respostas finais (padrão: `gpt-4o`)
- **OPENAI_EXTRACTION_MODEL**: Modelo para extrair dados estruturados (padrão: `gpt-4o`)

Cada modelo também permite configurar a temperatura:
- **OPENAI_RERANK_TEMPERATURE**: Temperatura para reranking (padrão: 0.1)
- **OPENAI_QUERY_TRANSFORM_TEMPERATURE**: Temperatura para transformação (padrão: 0.3)
- **OPENAI_ANSWER_GENERATION_TEMPERATURE**: Temperatura para geração (padrão: 0.7)
- **OPENAI_EXTRACTION_TEMPERATURE**: Temperatura para extração (padrão: 0.1)

**Exemplos de configuração:**
```bash
# Usar GPT-4.1 para tudo (configuração atual)
OPENAI_RERANK_MODEL=gpt-4.1-mini
OPENAI_QUERY_TRANSFORM_MODEL=gpt-4.1-mini
OPENAI_ANSWER_GENERATION_MODEL=gpt-4.1
OPENAI_EXTRACTION_MODEL=gpt-4.1

# Configuração econômica (GPT-4o-mini onde possível)
OPENAI_RERANK_MODEL=gpt-4o-mini
OPENAI_QUERY_TRANSFORM_MODEL=gpt-4o-mini
OPENAI_ANSWER_GENERATION_MODEL=gpt-4o
OPENAI_EXTRACTION_MODEL=gpt-4o-mini

# Usar o mais recente GPT-4o
OPENAI_ANSWER_GENERATION_MODEL=gpt-4o
OPENAI_RERANK_MODEL=gpt-4o
```

### 2. Configuração do Astra DB

1. Crie um banco Astra DB
2. Crie uma coleção com dimensão **1024** (para Voyage AI)
3. Obtenha o token de aplicação e endpoint

### 3. Configuração do Cloudflare R2

#### 3.1. Criar o Worker

1. Acesse o [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Vá para **Workers & Pages** → **Create Application** → **Create Worker**
3. Substitua o código padrão pelo código abaixo:

```javascript
function isAuthorized(request, env) {
  const authHeader = request.headers.get("Authorization");
  return authHeader === `Bearer ${env.AUTH_TOKEN}`;
}

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // Verificação de autenticação
    if (!isAuthorized(request, env)) {
      return new Response("Não autorizado", { status: 401 });
    }

    // Upload de imagem: /upload/<key>
    if (request.method === "PUT" && pathname.startsWith("/upload/")) {
      const key = decodeURIComponent(pathname.replace("/upload/", ""));
      const body = await request.arrayBuffer();
      await env.BUCKET.put(key, body);
      return new Response(`Upload feito: ${key}`, { status: 200 });
    }

    // Download de arquivo: /file/<key>
    if (request.method === "GET" && pathname.startsWith("/file/")) {
      const key = decodeURIComponent(pathname.replace("/file/", ""));
      try {
        const object = await env.BUCKET.get(key);
        if (!object) {
          return new Response("Arquivo não encontrado", { status: 404 });
        }
        // Detecta o content-type se possível
        const contentType = object.httpMetadata?.contentType || "image/jpeg";
        return new Response(object.body, {
          status: 200,
          headers: {
            "Content-Type": contentType,
            "Cache-Control": "public, max-age=31536000",
          }
        });
      } catch (e) {
        return new Response("Erro ao buscar arquivo", { status: 500 });
      }
    }

    // Delete por documento: /delete-doc/<docId>
    if (request.method === "DELETE" && pathname.startsWith("/delete-doc/")) {
      const docId = decodeURIComponent(pathname.replace("/delete-doc/", ""));
      const prefix = `${docId}_`;
      const list = await env.BUCKET.list({ prefix });

      const deletions = list.objects.map(obj => env.BUCKET.delete(obj.key));
      await Promise.all(deletions);

      return new Response(`Deletados ${list.objects.length} arquivos com prefixo: ${prefix}`, {
        status: 200,
      });
    }

    // Delete TODOS os arquivos: /delete-all
    if (request.method === "DELETE" && pathname === "/delete-all") {
      let totalDeleted = 0;
      let cursor = undefined;

      // Lista e deleta em batches (R2 retorna max 1000 por vez)
      do {
        const listResponse = await env.BUCKET.list({ cursor });

        if (listResponse.objects.length > 0) {
          const deletions = listResponse.objects.map(obj => env.BUCKET.delete(obj.key));
          await Promise.all(deletions);
          totalDeleted += listResponse.objects.length;
        }

        cursor = listResponse.truncated ? listResponse.cursor : undefined;
      } while (cursor);

      return new Response(`Deletados ${totalDeleted} arquivos do bucket`, {
        status: 200,
      });
    }

    // Listar arquivos por prefixo: /list/<prefix> (para dry run)
    if (request.method === "GET" && pathname.startsWith("/list/")) {
      const prefix = decodeURIComponent(pathname.replace("/list/", ""));
      const list = await env.BUCKET.list({ prefix: `${prefix}_` });

      const files = list.objects.map(obj => ({
        name: obj.key,
        size: obj.size,
        modified: obj.uploaded
      }));

      return new Response(JSON.stringify({
        files: files,
        count: files.length,
        total_size: files.reduce((sum, file) => sum + file.size, 0)
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }

    // Stats do bucket: /stats (para dry run delete-all)
    if (request.method === "GET" && pathname === "/stats") {
      let totalFiles = 0;
      let totalSize = 0;
      let cursor = undefined;

      // Lista todos os arquivos para contar
      do {
        const listResponse = await env.BUCKET.list({ cursor });
        totalFiles += listResponse.objects.length;
        totalSize += listResponse.objects.reduce((sum, obj) => sum + obj.size, 0);
        cursor = listResponse.truncated ? listResponse.cursor : undefined;
      } while (cursor);

      return new Response(JSON.stringify({
        total_files: totalFiles,
        total_size: totalSize
      }), {
        status: 200,
        headers: { "Content-Type": "application/json" }
      });
    }

    return new Response(
      "Use PUT /upload/<nome>, DELETE /delete-doc/<docId>, DELETE /delete-all, GET /list/<prefix>, GET /stats, ou GET /file/<key>",
      { status: 400 }
    );
  }
}
```

#### 3.2. Configurar Variáveis de Ambiente

1. No painel do Worker, vá para **Settings** → **Variables**
2. Adicione a variável:
   - **Nome**: `AUTH_TOKEN`
   - **Valor**: Um token seguro (ex: `your-secret-token-123`)

#### 3.3. Criar Bucket R2

1. No Cloudflare Dashboard, vá para **R2 Object Storage**
2. Clique em **Create bucket**
3. Nomeie seu bucket (ex: `sistema-rag-images`)

#### 3.4. Associar Worker ao Bucket

1. No painel do Worker, vá para **Settings** → **Variables**
2. Na seção **R2 Bucket Bindings**, clique em **Add binding**
3. Configure:
   - **Variable name**: `BUCKET`
   - **R2 bucket**: Selecione o bucket criado

#### 3.5. Atualizar .env

No seu arquivo `.env`, configure:
```bash
R2_ENDPOINT=https://seu-worker.seu-subdominio.workers.dev
R2_AUTH_TOKEN=your-secret-token-123
```

### 4. Configuração do Google Drive

1. **Faça upload do seu documento** para o Google Drive
2. **Torne o documento público**:
   - Clique com o botão direito > "Compartilhar"
   - Clique em "Alterar para qualquer pessoa com o link"
   - Defina permissão como "Visualizador"
3. **Copie o link** e extraia o FILE_ID:
   ```
   https://drive.google.com/file/d/1EDArLh4yTTf43UP9ilmeKN02Yyl6rVyQ/view
                                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                                            Este é o FILE_ID
   ```
4. **Configure no .env**:
   ```bash
   GOOGLE_DRIVE_URL=https://drive.google.com/file/d/SEU_FILE_ID/view
   ```

## 📚 Documentação Completa

Este sistema possui documentação detalhada dividida em três documentos principais:

### 📖 Para Iniciantes Completos
- **[MANUAL_COMPLETO.md](./MANUAL_COMPLETO.md)** - Manual passo a passo para configurar e usar o sistema do zero
  - Instalação e configuração completa
  - Guia para APIs externas (OpenAI, Voyage, Astra DB, etc.)
  - Exemplos práticos e solução de problemas
  - Sistema de avaliação automática
  - Seção completa sobre a API RESTful

### 🚀 API RESTful - Documentação Técnica
- **[API_DOCUMENTATION.md](./API_DOCUMENTATION.md)** - Documentação completa da API
  - Endpoints detalhados (/search, /evaluate, /ingest)
  - Exemplos em JavaScript, Python, PHP
  - Configuração para produção (Docker, Nginx, SSL)
  - Códigos de erro e troubleshooting
  - Integração com chatbots e sistemas

### ⚡ API RESTful - Guia Rápido
- **[README_API.md](./README_API.md)** - Guia de início rápido da API
  - Comandos essenciais para começar imediatamente
  - Configuração básica e exemplos mínimos
  - Troubleshooting comum

## 🚀 Uso Básico

### 📋 Comandos Principais

```bash
# 🚀 Ingestão de documentos
python ingestion.py

# 🔍 Busca/consulta (RAG completo)
python search.py

# 🌐 APIs RESTful (integração com outros sistemas)
# Sistema RAG Tradicional (porta 8000)
python run_system_api.py

# Sistema de Agents IA (porta 8001) 
python run_agents_api.py

# Acesse: 
# http://localhost:8000/docs (Sistema RAG)
# http://localhost:8001/docs (Agents)
```

### 🧪 Comandos de Teste

```bash
# Teste rápido das APIs
python -m sistema_rag.run_pipeline test

# Pipeline completo de ingestão (alternativo)
python -m sistema_rag.run_pipeline

# Sistema de busca conversacional (avançado)
python -m sistema_rag.search.conversational_rag
```

### 🔍 Sistema de Busca - Interface Completa

**Comando Principal (Recomendado):**
```bash
python search.py
```

**Funcionalidades:**
- 🤖 **Pipeline RAG Completo**: Busca + Rerank + IA + Imagens
- 💬 **Interface Interativa**: Digite perguntas em linguagem natural
- 📚 **Fontes Citadas**: Mostra documentos utilizados
- 🖼️ **Imagens Integradas**: Acesso direto às imagens do R2
- 🧠 **Contexto Conversacional**: Mantém histórico da conversa

**Exemplo de Uso:**
```
🔍 Sua pergunta: Qual o preço do hambúrguer de frango?
🔎 Processando: 'Qual o preço do hambúrguer de frango?'
⏳ Buscando → Reranking → Respondendo...

🤖 Resposta:
O hambúrguer de frango custa R$ 18,90 segundo o cardápio...

📚 Fontes utilizadas:
   1. cardapio_american - página 1
      🖼️ https://agenciawow.ilceccato88.workers.dev/file/cardapio_american_page_1.jpg

💭 Justificativa: Selecionei esta página porque contém...
```

**Interface Programática (Alternativa):**
```python
from sistema_rag import SimpleRAG

# Criar interface
rag = SimpleRAG()

# Fazer perguntas
resposta = rag.search("Qual o preço do hambúrguer?")
print(resposta)

# Conversa com contexto
resposta = rag.search("E sobre as sobremesas?")
print(resposta)

# Extração de dados estruturados
template = {"pratos": [], "precos": [], "ingredientes": []}
dados = rag.extract(template)
print(dados)
```

### 🔧 Pipeline RAG Personalizado

```python
from sistema_rag import RAGPipeline

# Criar pipeline personalizado
pipeline = RAGPipeline(
    max_candidates=10,
    max_selected=2,
    enable_reranking=True,
    enable_image_fetching=True  # Cloudflare R2
)

# Buscar com histórico de conversa
chat_history = [
    {"role": "user", "content": "O que é o Zep?"},
    {"role": "assistant", "content": "O Zep é um sistema..."}
]

result = pipeline.search_and_answer(
    query="Como ele funciona?",
    chat_history=chat_history
)

print(result["answer"])
print(f"Documentos: {result['selected_pages']}")
print(f"Justificativa: {result['justification']}")
```

### 📱 Interface CLI Conversacional

```bash
python -m sistema_rag.search.conversational_rag
```

**Comandos disponíveis:**
- `/help` - Ajuda
- `/clear` - Limpar histórico
- `/stats` - Estatísticas do sistema
- `/extract {"campo": ""}` - Extração de dados

## 🎯 Exemplo Prático

### Ingestão do Cardápio

```bash
# Processa cardápio American Burger
python ingestion.py
```

**Resultado:**
- ✅ 2 páginas processadas
- 🖼️ Imagens no Cloudflare R2
- 🧬 Embeddings no Astra DB

### Busca no Cardápio

```bash
# Sistema de busca completo com IA
python search.py
```

**O que o sistema faz:**
- 🔍 Busca vetorial nos documentos
- 🎯 Rerank inteligente com IA  
- 🤖 Resposta contextualizada da OpenAI
- 🖼️ Acesso às imagens do Cloudflare R2
- 💬 Histórico conversacional

**Exemplos de perguntas:**
- 🍔 "Qual o preço do hambúrguer de frango?"
- 🍰 "Que sobremesas vocês têm disponíveis?"
- 💰 "Mostre-me os preços do cardápio"
- 🥤 "Quais bebidas estão no menu?"

### Modo Multimodal LlamaParse

O sistema suporta o novo modo multimodal do LlamaParse que gera screenshots automaticamente:

#### Configuração Básica (usando créditos LlamaParse)
```python
from sistema_rag.components.processing import LlamaParseProcessor

processor = LlamaParseProcessor.create_multimodal(
    api_key="llx-...",
    model_name="anthropic-sonnet-3.5"
)
```

#### Configuração Econômica (usando sua própria chave)
```python
processor = LlamaParseProcessor.create_multimodal(
    api_key="llx-...",
    model_name="anthropic-sonnet-3.5", 
    model_api_key="sk-ant-..."  # Reduz custo para ~$0.003/página
)
```

#### Modelos Disponíveis
- **Anthropic**: `anthropic-sonnet-3.5`, `anthropic-sonnet-3.7`, `anthropic-sonnet-4.0`
- **OpenAI**: `openai-gpt4o`, `openai-gpt-4o-mini`, `openai-gpt-4-1`
- **Google**: `gemini-2.0-flash-001`, `gemini-2.5-pro`, `gemini-1.5-pro`

Ou usando o módulo diretamente:

```python
from sistema_rag.ingestion.basic_usage import basic_rag_pipeline
import asyncio

# Executar pipeline completo
asyncio.run(basic_rag_pipeline())
```

### Uso por Componentes

#### Pipeline de Ingestão
```python
# 1. Download do Google Drive
from sistema_rag.ingestion.ingestion import GoogleDriveDownloader

downloader = GoogleDriveDownloader()
files = downloader.download_files(["sua_url_aqui"])

# 2. Seleção de arquivo
from sistema_rag.ingestion.ingestion import FileSelector

selector = FileSelector()
selected = selector.select_file(files, file_index=0)

# 3. Processamento com LlamaParse
from sistema_rag.ingestion.processing import LlamaParseProcessor

processor = LlamaParseProcessor(api_key="sua_chave")
parsed_doc = processor.process_document(selected)
screenshots = processor.get_screenshots(parsed_doc.job_id)

# 4. Merge multimodal
from sistema_rag.ingestion.processing import MultimodalMerger

merger = MultimodalMerger(merge_strategy="page_based")
chunks = merger.merge_content(parsed_doc, screenshots)

# 5. Embeddings
from sistema_rag.search.embeddings import VoyageEmbedder

embedder = VoyageEmbedder(api_key="sua_chave")
embedded_chunks = embedder.embed_chunks(chunks)

# 6. Upload para R2
from sistema_rag.ingestion.storage import CloudflareR2Uploader

uploader = CloudflareR2Uploader(r2_endpoint="...", auth_token="...")
upload_result = uploader.upload_chunk_images(embedded_chunks)

# 7. Inserção no Astra DB
from sistema_rag.ingestion.storage import AstraDBInserter

inserter = AstraDBInserter(api_endpoint="...", auth_token="...", collection_name="docs")
final_result = inserter.insert_chunks(upload_result["documents"])
```

#### Componentes de Busca
```python
# 1. Transformador de queries
from sistema_rag.search.retrieval import QueryTransformer

transformer = QueryTransformer()
chat_history = [{"role": "user", "content": "O que é isso?"}]
transformed = transformer.transform_query(chat_history)

# 2. Busca vetorial
from sistema_rag.search.retrieval import VectorSearcher

searcher = VectorSearcher()
search_results = searcher.search_by_text("query", embedding)

# 3. Busca de imagens R2
from sistema_rag.search.retrieval import ImageFetcher

fetcher = ImageFetcher()
enriched_results = fetcher.enrich_search_results(search_results)

# 4. Re-ranking
from sistema_rag.search.retrieval import SearchReranker

reranker = SearchReranker()
reranked = reranker.rerank_results("query", search_results)
```

## 🧪 Testes Automatizados

### 📁 Pasta de Testes Completa

O sistema inclui uma suíte profissional de testes automatizados localizada na pasta `tests/`:

```bash
tests/
├── README.md              # 📖 Documentação completa dos testes  
├── TESTING_SUMMARY.md     # 📊 Resumo executivo dos testes
├── run_tests.py           # 🚀 Executor inteligente com menu
├── test_api.py            # 🌐 Testes da API (17 testes)
├── test_ingestion.py      # 📥 Testes de ingestão
├── test_search.py         # 🔍 Testes de busca
├── test_evaluator.py      # 📊 Testes do avaliador
└── test_integration.py    # 🔄 Testes de integração E2E
```

### 🚀 Comandos Principais

```bash
# Menu interativo (recomendado para iniciantes)
python tests/run_tests.py

# Verificação rápida do sistema
python tests/run_tests.py --smoke

# Testes da API (17 testes - ~2 minutos)
python tests/run_tests.py --api

# Todos os testes básicos
python tests/run_tests.py --basic

# Testes completos incluindo integração
python tests/run_tests.py --all
```

### 📊 Status dos Testes

- ✅ **17/17 testes da API** passando (100% sucesso)
- ✅ **Cobertura completa** de todos os componentes
- ✅ **Testes de integração** end-to-end
- ✅ **Casos de uso reais** (restaurante, atendimento)
- ✅ **Documentação detalhada** na pasta `tests/`

> 📖 **Para instruções detalhadas**, consulte:
> - `tests/README.md` - Guia completo de uso dos testes
> - `MANUAL_COMPLETO.md` - Seção 13 sobre testes para iniciantes

### Teste Rápido das APIs (Método Tradicional)

```bash
# Teste completo do sistema
python -m sistema_rag.run_pipeline test
```

### Diagnóstico de Problemas

```bash
# Verificar variáveis de ambiente
cat .env | grep -E "(VOYAGE|ASTRA|R2)"

# Testar componentes individualmente
python -c "
from dotenv import load_dotenv; load_dotenv()
from sistema_rag.search.retrieval import VectorSearcher
searcher = VectorSearcher()
print(searcher.test_connection().message)
"
```

## 🧪 Sistema de Avaliação Automática

O sistema inclui um avaliador automático (`rag_evaluator.py`) que testa a qualidade das respostas do RAG usando perguntas configuráveis via variáveis de ambiente.

### Configuração das Perguntas de Avaliação

As perguntas de teste são definidas no arquivo `.env` usando três variáveis principais:

#### 1. EVAL_QUESTIONS - Lista de Perguntas
Define as perguntas que serão testadas, separadas por `|`:

```bash
EVAL_QUESTIONS="Quais produtos estão disponíveis?|Qual é o preço mais alto do cardápio?|Vocês têm opções para dietas especiais?|Quais são as opções de acompanhamentos?|Qual é o horário de funcionamento?|Quais formas de entrega vocês oferecem?|Tem alguma promoção disponível?|Quais bebidas vocês servem?|Quais formas de pagamento vocês aceitam?|Qual é o produto mais popular?"
```

#### 2. EVAL_KEYWORDS - Palavras-chave Esperadas
Define as palavras-chave que devem aparecer nas respostas, na mesma ordem das perguntas, separadas por `|` (pergunta) e `,` (palavras):

```bash
EVAL_KEYWORDS="produtos,cardápio,menu,disponível|preço,valor,caro,alto,maior|dieta,vegetariano,vegano,especial,restrito|acompanhamento,lado,adicional,extra|horário,funcionamento,aberto,fecha,atendimento|entrega,retirada,balcão,domicílio|promoção,desconto,oferta,combo,especial|bebida,refrigerante,suco,água,drinks|pagamento,cartão,dinheiro,pix,forma|popular,favorito,vendido,preferido"
```

#### 3. EVAL_CATEGORIES - Categorias das Perguntas
Define a categoria de cada pergunta para análise estatística, na mesma ordem:

```bash
EVAL_CATEGORIES="catalog|pricing|dietary|sides|hours|delivery|promotions|drinks|payment|popular"
```

### Como Funciona o Sistema de Avaliação

1. **Leitura das Variáveis**: O avaliador carrega as perguntas, palavras-chave e categorias do `.env`
2. **Execução das Perguntas**: Cada pergunta é enviada para o sistema RAG
3. **Análise das Respostas**: O sistema calcula métricas baseadas em:
   - **Cobertura de palavras-chave**: Quantas palavras esperadas aparecem na resposta
   - **Tempo de resposta**: Velocidade do sistema
   - **Detecção de "não encontrado"**: Se o sistema identifica corretamente quando não há informação

### Executando a Avaliação

```bash
# Executar avaliação completa
python rag_evaluator.py
```

### Resultados Gerados

A avaliação gera dois arquivos:

- **`rag_evaluation_report.json`**: Relatório completo em JSON com métricas detalhadas
- **`rag_evaluation_detailed.txt`**: Relatório em texto legível com resumo executivo

### Personalizando para Seu Contexto

Para adaptar o avaliador para diferentes tipos de documentos, ajuste as variáveis no `.env`:

**Exemplo para um e-commerce:**
```bash
EVAL_QUESTIONS="Quais produtos você vende?|Qual o prazo de entrega?|Como faço uma devolução?"
EVAL_KEYWORDS="produtos,vendas,catálogo|entrega,prazo,tempo|devolução,troca,garantia"
EVAL_CATEGORIES="catalog|shipping|support"
```

**Exemplo para documentação técnica:**
```bash
EVAL_QUESTIONS="Como instalar o software?|Quais são os requisitos do sistema?|Como resolver erros comuns?"
EVAL_KEYWORDS="instalação,setup,configuração|requisitos,sistema,mínimo|erro,problema,solução"
EVAL_CATEGORIES="installation|requirements|troubleshooting"
```

### Métricas de Avaliação

O sistema calcula automaticamente:

- **Taxa de Sucesso**: Porcentagem de perguntas processadas sem erro
- **Cobertura de Palavras-chave**: Média de palavras esperadas encontradas nas respostas
- **Tempo de Resposta Médio**: Performance do sistema
- **Análise por Categoria**: Métricas agrupadas por tipo de pergunta

## 📊 Estratégias de Chunking

### Page-based (Padrão)
- Um chunk por página
- Associação direta texto-imagem
- Ideal para documentos estruturados

### Section-based
- Chunks por cabeçalhos
- Estimativa de página por posição
- Ideal para documentos longos

### Smart Chunks
- Respeita limite de caracteres
- Divisão inteligente por parágrafos
- Distribuição proporcional de imagens

### Text-only / Image-only
- Processamento separado
- Para casos específicos

## 🔍 Características Técnicas

### Otimizações Implementadas

1. **Limpeza de Base64** - Remove campos base64 antes do Astra DB
2. **Truncamento Inteligente** - Limita texto preservando integridade
3. **Processamento em Lotes** - Otimiza chamadas de API
4. **URLs vs Base64** - Usa URLs para reduzir tamanho no DB
5. **Retry Logic** - Tratamento de erros e tentativas

### Limites e Considerações

- **Voyage AI**: 10 chunks por lote, 5000 chars por texto
- **Astra DB**: 100 docs por inserção, 7000 chars por campo texto
- **LlamaParse**: 100MB por arquivo, 300s timeout
- **Cloudflare R2**: Dependente da configuração do Worker

## 📝 Exemplos de Dados

### Chunk Multimodal Final

```json
{
  "_id": "documento_page_1",
  "content": "Conteúdo da página 1...",
  "$vector": [0.1, -0.2, 0.3, ...],
  "document_name": "documento",
  "page_number": 1,
  "image_url": "https://r2.example.com/file/documento_page_1.jpg",
  "metadata": {
    "document_name": "documento",
    "parse_mode": "parse_page_with_agent",
    "job_id": "abc123"
  }
}
```

## 📊 Performance e Melhorias

### ⚡ Otimizações Implementadas

| **Componente** | **Melhoria** | **Benefício** |
|----------------|--------------|---------------|
| **Arquitetura** | Modular | Escalabilidade e manutenibilidade |
| **Imagens** | Cloudflare R2 | URLs diretas vs base64 |
| **Cache** | Inteligente | Reduz chamadas de API |
| **Fallbacks** | Robustos | Alta disponibilidade |
| **Busca** | Vetorial + IA | Precisão otimizada |

### 🚀 Comandos Simplificados

**Sistema atual:**
```bash
# Ingestão
python ingestion.py

# Busca
python search.py
```

### 📈 Resultados de Performance
- **Cache de Queries**: Reduz chamadas à IA em 60-80%
- **Classificação Determinística**: Evita IA para queries simples
- **Cache de Imagens**: Reduz downloads do R2
- **Re-ranking Otimizado**: Seleção mais precisa

## 🗺️ Status do Projeto

### ✅ Componentes Completos
- [x] **Sistema de Ingestão** - Pipeline completo com LlamaParse
- [x] **Sistema de Busca** - Busca vetorial multimodal
- [x] **Armazenamento** - Astra DB + Cloudflare R2
- [x] **Embeddings** - Voyage AI multimodal
- [x] **API RESTful** - FastAPI profissional com 3 endpoints
- [x] **Testes Automatizados** - Suíte completa com 17+ testes
- [x] **Sistema de Avaliação** - Métricas automáticas de qualidade
- [x] **Cache Inteligente** - Otimizações de performance
- [x] **Arquitetura Modular** - Componentes independentes

### 🚧 Roadmap Futuro
- [ ] **Interface Web** - Dashboard para interação
- [ ] **Métricas Avançadas** - Monitoring e analytics
- [ ] **Multi-idioma** - Suporte a múltiplos idiomas
- [ ] **Embeddings Locais** - Opção open-source

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Implemente seguindo a arquitetura modular
4. **Execute os testes**: `python tests/run_tests.py --smoke`
5. **Adicione testes** para novas funcionalidades
6. **Verifique cobertura**: `python tests/run_tests.py --basic`
7. Submeta um Pull Request

> 📋 **Importante**: Todos os PRs devem passar nos testes automatizados. Consulte `tests/README.md` para detalhes.

## 📄 Licença

MIT License - veja LICENSE para detalhes.

## 🆘 Suporte

### 🔧 Comandos de Diagnóstico

```bash
# Verificação rápida completa (RECOMENDADO)
python tests/run_tests.py --smoke

# Teste geral do sistema
python -m sistema_rag.run_pipeline test

# Verificar variáveis de ambiente
cat .env | grep -E "(VOYAGE|ASTRA|R2)"

# Testar API completa
python tests/run_tests.py --api

# Testar busca completa com IA
python search.py
```

### 📞 Para Dúvidas

- **APIs**: Consulte documentação oficial de cada serviço
- **Configuração**: Verifique `.env.example` e variáveis
- **Erros**: Execute `python -m sistema_rag.run_pipeline test`
- **Performance**: Ajuste configurações no `sistema_rag/config/`

---

🔥 **Sistema RAG Multimodal - Arquitetura Modular Completa**
