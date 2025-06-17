# 🤖 Sistema RAG Inteligente

> Sistema avançado de busca e análise de documentos com agents inteligentes e memória persistente

## 🎯 **O que é?**

Sistema RAG (Retrieval-Augmented Generation) que combina:
- **Busca vetorial inteligente** em documentos
- **Agentes autônomos** para análise contextual  
- **Memória persistente com Zep** para contexto conversacional
- **APIs REST** para integração fácil
- **Interface multimodal** (texto + imagens)

## ⚡ **Funcionalidades Principais**

### 🔍 **Sistema RAG Core**
- Busca semântica em documentos indexados
- Reranking inteligente com IA
- Suporte a múltiplos formatos (PDF, DOCX, etc.)
- Integração com imagens (Cloudflare R2)

### 🤖 **Sistema de Agents**  
- Agents especializados em diferentes tarefas
- Descoberta automática de novos agents
- **Memória persistente com Zep** (gerenciamento inteligente de contexto)
- Conversação com histórico contextual entre sessões
- Extração automática de fatos e entidades
- Grafos de conhecimento dinâmicos
- API REST dedicada

### 🔌 **APIs Disponíveis**
- **API Principal** (porta 8000): Sistema RAG tradicional
- **API de Agents** (porta 8001): Interação com agents
- Ambas com autenticação Bearer Token

## 🚀 **Início Rápido**

```bash
# 1. Instalar dependências
pip install -r requirements.txt

# 2. Configurar ambiente (.env)
VOYAGE_API_KEY=sua_chave
OPENAI_API_KEY=sua_chave  
ASTRA_DB_API_ENDPOINT=seu_endpoint
ASTRA_DB_APPLICATION_TOKEN=seu_token
ZEP_API_KEY=sua_chave_zep          # Para memória persistente dos agents

# 3. Rodar APIs
python run_system_api.py             # API Sistema RAG (porta 8000)
python run_agents_api.py             # API Agents (porta 8001)
# ou: python -m system_rag.api / python -m agents.api

# 4. Testar sistema (Interface Simplificada)  
python run_tests.py                  # Interface interativa
python run_tests.py --test 01        # Teste específico
```

## 🏗️ **Arquitetura**

```
sistema_rag/
├── system_rag/          # 🔧 Sistema RAG Core
│   ├── search/         # Busca e embeddings
│   ├── ingestion/      # Processamento de documentos
│   ├── api/            # API REST (porta 8000)
│   ├── search.py       # Script de busca
│   └── ingestion.py    # Script de ingestão
├── agents/            # 🤖 Sistema de Agents
│   ├── core/          # Agents, operadores e Zep client
│   ├── tools/         # Ferramentas reutilizáveis  
│   └── api/           # API REST (porta 8001)
├── tests/              # 🧪 Testes simplificados
│   └── simple/        # Interface e testes individuais
└── documentation/      # 📚 Documentação numerada
```

## 📚 **Documentação**

**Documentação completa disponível em [`documentation/`](./documentation/)**

### 📖 **Principais Guias:**
- [**Manual de Instalação**](./documentation/02_MANUAL_INSTALACAO_USO.md) - Instalação e configuração detalhada
- [**Sistema de Agents**](./documentation/03_SISTEMA_AGENTES.md) - Como usar agents inteligentes
- [**API Sistema RAG**](./documentation/04_API_SISTEMA_RAG.md) - API principal (porta 8000)
- [**API Agentes**](./documentation/05_API_AGENTES.md) - API de agentes (porta 8001)
- [**Integração Zep**](./documentation/07_ZEP_MEMORY.md) - Gerenciamento de memória avançado
- [**Guia de Testes**](./documentation/06_GUIA_TESTES.md) - Como executar e interpretar testes

### 🎯 **Para diferentes perfis:**
- **Usuários**: [Manual de Instalação](./documentation/02_MANUAL_INSTALACAO_USO.md)
- **Desenvolvedores**: [Visão Geral Completa](./documentation/01_VISAO_GERAL_COMPLETA.md)  
- **Integradores**: [APIs](./documentation/04_API_SISTEMA_RAG.md) + [Agents](./documentation/05_API_AGENTES.md)

## ✨ **Características Técnicas**

- **🚀 Performance**: Pipeline otimizado com cache inteligente
- **🔒 Segurança**: Autenticação Bearer Token em todas APIs
- **📊 Monitoramento**: Logs estruturados e métricas detalhadas
- **🔧 Modularidade**: Componentes independentes e reutilizáveis
- **🤖 Extensibilidade**: Sistema de agents com descoberta automática
- **🧠 Memória Inteligente**: Zep como camada central de memória
  - Persistência de conversas entre sessões
  - Extração automática de insights
  - Busca semântica no histórico
  - Grafos de conhecimento personalizados

## 🎭 **Casos de Uso**

- **Análise de documentos técnicos** e acadêmicos
- **Assistente inteligente** com memória persistente
- **Busca contextual** em grandes volumes de texto
- **Extração automatizada** de informações estruturadas
- **Sistema de perguntas e respostas** empresarial
- **Consultoria personalizada** com histórico de interações
- **Suporte ao cliente** com contexto de conversas anteriores

## 🤝 **Contribuição**

1. Fork o projeto
2. Crie sua branch (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 **Licença**

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para detalhes.

---

**🔗 Links Rápidos:**
- 📚 [Documentação Completa](./documentation/)
- 🤖 [Sistema de Agents](./documentation/03_SISTEMA_AGENTES.md)
- 🔌 [API Sistema RAG](./documentation/04_API_SISTEMA_RAG.md)
- 🔗 [API Agentes](./documentation/05_API_AGENTES.md)
- 🧪 [Testes](./documentation/06_GUIA_TESTES.md)