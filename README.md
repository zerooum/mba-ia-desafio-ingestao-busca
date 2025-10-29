# 🔍 Sistema de Busca e Chat com RAG

Sistema de ingestão, busca e chat inteligente para análise de documento usando RAG (Retrieval-Augmented Generation) com LangChain, OpenAI e PostgreSQL com pgvector.

Projeto desenvolvido como desafio de ingestão e busca com RAG do MBA em IA da FullCycle.

## 📋 Índice

- [Visão Geral](#-visão-geral)
- [Funcionalidades](#-funcionalidades)
- [Arquitetura](#-arquitetura)
- [Pré-requisitos](#-pré-requisitos)
- [Instalação](#-instalação)
- [Configuração](#-configuração)
- [Uso](#-uso)
- [Estrutura do Projeto](#-estrutura-do-projeto)
- [Tecnologias Utilizadas](#-tecnologias-utilizadas)

## 🎯 Visão Geral

Este projeto implementa um sistema completo de RAG (Retrieval-Augmented Generation) que:
1. **Ingere** dados de empresas de documentos PDF
2. **Armazena** embeddings vetoriais no PostgreSQL com pgvector
3. **Busca** informações usando similaridade semântica ou Self-Query Retriever
4. **Responde** perguntas usando LLMs da OpenAI com contexto relevante

## ✨ Funcionalidades

### 🗂️ Ingestão de Dados (`ingest.py`)
- Leitura de PDFs com informações de empresas
- Extração e validação de dados (nome, faturamento, ano de fundação)
- Ordenação automática por faturamento
- Divisão em chunks com metadados enriquecidos
- Geração de embeddings com OpenAI
- Armazenamento no PostgreSQL com pgvector

### 🔎 Sistema de Busca (`search.py`)
Duas modalidades de busca:

1. **Self-Query Retriever** (Busca Inteligente)
   - Interpretação automática de queries complexas
   - Filtragem por faixa de faturamento
   - Combinação de busca semântica + filtros de metadados

2. **Similarity Search** (Busca por Similaridade)
   - Busca puramente vetorial
   - Top-k documentos mais relevantes

### 💬 Interface de Chat (`chat.py`)
- CLI interativa com questionary
- Escolha do tipo de busca
- Visualização de respostas e documentos de contexto
- Interface amigável com emojis e formatação

## 🏗️ Arquitetura

```
┌─────────────┐
│   PDF File  │
└──────┬──────┘
       │
       ▼
┌─────────────────────┐
│   ingest.py         │
│  - Lê PDF           │
│  - Ordena dados     │
│  - Cria chunks      │
│  - Gera embeddings  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│  PostgreSQL +       │
│  pgvector           │
│  (Armazena vetores) │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   search.py         │
│  - Retriever        │
│  - Busca semântica  │
└──────┬──────────────┘
       │
       ▼
┌─────────────────────┐
│   chat.py           │
│  - Interface CLI    │
│  - Respostas LLM    │
└─────────────────────┘
```

## 🔧 Pré-requisitos

- Python 3.8+
- Docker e Docker Compose
- Conta OpenAI com API Key

## 📦 Instalação

### 1. Clone o repositório
```bash
git clone <repo-url>
cd mba-ia-desafio-ingestao-busca
```

### 2. Instale as dependências
```bash
pip install -r requirements.txt
```

### 3. Inicie o PostgreSQL com pgvector
```bash
docker-compose up -d
```

Aguarde o banco estar saudável (healthcheck):
```bash
docker-compose ps
```

## ⚙️ Configuração

Crie um arquivo `.env` na raiz do projeto:

```env
# OpenAI
OPENAI_API_KEY=sk-...
OPENAI_EMBEDDING_MODEL=text-embedding-3-small
OPENAI_CHAT_MODEL=gpt-4

# Database
DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/rag
PG_VECTOR_COLLECTION_NAME=empresas

# PDF
PDF_PATH=dados/empresas.pdf
```

### Variáveis de Ambiente

| Variável | Descrição | Exemplo |
|----------|-----------|---------|
| `OPENAI_API_KEY` | Chave da API OpenAI | `sk-...` |
| `OPENAI_EMBEDDING_MODEL` | Modelo de embeddings | `text-embedding-3-small` |
| `OPENAI_CHAT_MODEL` | Modelo de chat | `gpt-4` |
| `DATABASE_URL` | URL de conexão PostgreSQL | `postgresql+psycopg://...` |
| `PG_VECTOR_COLLECTION_NAME` | Nome da coleção no banco | `empresas` |
| `PDF_PATH` | Caminho do PDF a ingerir | `dados/empresas.pdf` |

## 🚀 Uso

### 1. Ingestão de Dados

Execute o processo de ingestão para carregar dados do PDF:

```bash
python src/ingest.py
```

**Formato esperado do PDF:**
```
Nome da empresa    Faturamento    Ano de fundação
Empresa XYZ ME     R$ 1.234.567,89    2010
Outra Corp LTDA    R$ 9.876.543,21    2015
```

### 2. Interface de Chat

Inicie a CLI interativa:

```bash
python src/chat.py
```

**Fluxo de uso:**
1. Escolha o tipo de busca (Self Query ou Similarity)
2. Digite sua pergunta
3. Visualize a resposta
4. Opcionalmente, veja os documentos de contexto
5. Continue ou encerre

### 3. Exemplos de Perguntas

**Com Self-Query Retriever:**
```
- Quais empresas têm faturamento superior a 5 milhões?
```

**Com Similarity Search:**
```
- Qual o faturamento da Empresa SuperTechIABrazil?
```

## 📁 Estrutura do Projeto

```
mba-ia-desafio-ingestao-busca/
├── src/
│   ├── ingest.py          # Ingestão de PDFs e geração de embeddings
│   ├── search.py          # Sistema de busca e retrieval
│   └── chat.py            # Interface CLI interativa
├── docker-compose.yml     # Configuração PostgreSQL + pgvector
├── requirements.txt       # Dependências Python
├── .env                   # Variáveis de ambiente (criar)
└── README.md             # Este arquivo
```

### Detalhes dos Módulos

#### `ingest.py`
- `read_pdf()`: Carrega PDF e remove cabeçalhos
- `extract_revenue()`: Extrai valores monetários
- `sort_documents_by_revenue()`: Ordena empresas por faturamento
- `split_documents()`: Divide em chunks com metadados
- `generate_embeddings()`: Gera e armazena embeddings

#### `search.py`
- `get_vector_store()`: Inicializa conexão com pgvector
- `get_self_query_retriever()`: Cria Self-Query Retriever
- `search_prompt()`: Executa busca e gera resposta

#### `chat.py`
- Interface CLI com `questionary`
- Estilo customizado
- Loop interativo de perguntas/respostas

## 🛠️ Tecnologias Utilizadas

### Core
- **Python 3.8+**: Linguagem principal
- **LangChain**: Framework RAG e orquestração
- **OpenAI**: Embeddings e LLM

### Banco de Dados
- **PostgreSQL 17**: Banco de dados relacional
- **pgvector**: Extensão para vetores de alta dimensão
- **asyncpg/psycopg**: Drivers Python

### Processamento
- **PyPDF**: Leitura de documentos PDF
- **RecursiveCharacterTextSplitter**: Divisão de textos

### Interface
- **questionary**: CLI interativa moderna
- **python-dotenv**: Gerenciamento de variáveis de ambiente

### Infraestrutura
- **Docker Compose**: Orquestração de containers
- **pgvector/pgvector:pg17**: Imagem Docker oficial

## 📊 Metadados dos Chunks

Cada chunk armazenado contém:

```json
{
  "min_revenue": 1234567.89,
  "max_revenue": 9876543.21,
  "file_name": "empresas.pdf",
  "creation_date": "2025-10-29T12:34:56.789Z"
}
```

Esses metadados permitem filtragem avançada com Self-Query Retriever.

## 🔍 Prompt Template

O sistema usa um template rigoroso para evitar alucinações:

```
CONTEXT: {documentos recuperados}

REGRAS:
- Responda somente com base no CONTEXTO
- Se não tiver informação, diga: "Não tenho informações necessárias"
- Nunca invente ou use conhecimento externo

PERGUNTA: {input}
```

## 🐛 Troubleshooting

### Erro: "Environment variable not defined"
- Verifique se o arquivo `.env` existe e contém todas as variáveis necessárias

### Erro de conexão com PostgreSQL
- Confirme que o Docker está rodando: `docker-compose ps`
- Verifique os logs: `docker-compose logs postgres`
- Teste a conexão: `psql postgresql://postgres:postgres@localhost:5432/rag`

### Erro ao processar PDF
- Verifique o formato do PDF
- Confirme que cada linha tem: Nome + R$ + valor + ano
- Verifique o caminho em `PDF_PATH`

### Respostas vazias ou genéricas
- Verifique se a ingestão foi concluída com sucesso
- Confirme que há dados no banco: consulte a tabela de embeddings
- Experimente reformular a pergunta
