# 🤖 RAG com Busca Híbrida e Banco Vetorial para Suporte Técnico

Um projeto de **Retrieval-Augmented Generation (RAG)** que combina busca por palavras-chave (BM25) com busca semântica vetorial para criar um assistente inteligente de suporte técnico local.

## 📋 Descrição do Projeto

Este projeto implementa um sistema completo de suporte técnico baseado em IA que:

- **Busca Híbrida**: Combina busca por palavras-chave (BM25) e busca semântica vetorial para encontrar artigos relevantes
- **Banco Vetorial**: Utiliza Weaviate para armazenar e recuperar documentos através de embeddings
- **Banco Relacional**: Utiliza SQLite para armazenar dados estruturados de suporte técnico
- **Geração de Respostas**: Usa Ollama com LLaMA 3 para gerar respostas contextualizadas baseadas nos artigos encontrados
- **Processamento Local**: Funciona completamente offline sem dependências de APIs externas

## 🎯 Caso de Uso

O sistema é ideal para:
- 📚 **Base de Conhecimento Corporativa**: Criar assistentes privados com documentação interna
- 🔧 **Suporte Técnico Automatizado**: Responder perguntas com base em artigos de suporte existentes
- 📖 **RAG em Produção**: Demonstrar um pipeline completo de RAG com busca híbrida
- 🔬 **Estudos em IA/ML**: Aprender sobre embeddings, indexação vetorial e retrieval

## 🏗️ Arquitetura

```
┌─────────────────────────────────────────────────────────────┐
│                    Pergunta do Usuário                      │
└────────────────┬────────────────────────────────────────────┘
                 │
         ┌───────▼──────────┐
         │  Embedding Model │ (sentence-transformers)
         │ (all-MiniLM-L6)  │
         └───────┬──────────┘
                 │
         ┌───────▼──────────────────────────┐
         │     Busca Híbrida (Weaviate)     │
         │  ┌─────────────────────────────┐ │
         │  │ Busca Vetorial (α=1.0)      │ │
         │  │ Busca por Palavra (α=0.0)   │ │
         │  │ Combinada (α=0.5)           │ │
         │  └─────────────────────────────┘ │
         └───────┬──────────────────────────┘
                 │
         ┌───────▼─────────────────┐
         │  Artigos Recuperados    │
         │  (do Banco Vetorial)    │
         └───────┬─────────────────┘
                 │
         ┌───────▼──────────────────┐
         │  Prompt + Contexto       │
         │  (para o LLM)            │
         └───────┬──────────────────┘
                 │
         ┌───────▼──────────────────┐
         │  Ollama (LLaMA 3)        │
         │  Geração de Resposta     │
         └───────┬──────────────────┘
                 │
         ┌───────▼──────────────────┐
         │   Resposta Final         │
         │   (Contextualizada)      │
         └──────────────────────────┘
```

## 📁 Estrutura do Projeto

```
dsa_RAG_busca_hibrida/
├── 1_setup_database.py        # Cria banco SQLite com artigos de suporte
├── 2_rag_app.py               # Aplicação RAG com busca híbrida
├── 3_insere_artigos.py        # Script para inserir mais artigos no banco
├── dsa_app.py                 # Aplicação Streamlit (UI)
├── docker-compose.yml         # Orchestração de containers (Weaviate)
├── requirements.txt           # Dependências Python
└── README.md                  # Este arquivo
```

## 🚀 Como Executar

### 1️⃣ Pré-requisitos

- Python 3.10+
- Docker e Docker Compose (para Weaviate)
- Ollama instalado e rodando localmente
- Modelo LLaMA 3 baixado no Ollama

### 2️⃣ Instalação

```bash
# Clone o repositório
git clone https://github.com/alinemiranda036/dsa_RAG_busca_hibrida.git
cd dsa_RAG_busca_hibrida

# Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # No Windows: venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt
```

### 3️⃣ Configurar Ollama

```bash
# Instale Ollama de https://ollama.ai
# Execute o serviço
ollama serve

# Em outro terminal, baixe o modelo LLaMA 3
ollama pull llama3
```

### 4️⃣ Iniciar Weaviate (Banco Vetorial)

```bash
# Na pasta do projeto
docker-compose up -d

# Verifique se está rodando
curl http://localhost:8080/v1/meta
```

### 5️⃣ Criar Banco de Dados e Indexar

```bash
# Cria o banco SQLite com artigos de exemplo
python 1_setup_database.py

# Executa a aplicação RAG
python 2_rag_app.py
```

### 6️⃣ (Opcional) Usar Interface Streamlit

```bash
streamlit run dsa_app.py
```

Acesse `http://localhost:8501`

## 🔧 Componentes Principais

### 1. `1_setup_database.py` - Configuração do Banco de Dados

Cria um banco SQLite com uma tabela de artigos de suporte:

```python
CREATE TABLE artigos_suporte (
    id INTEGER PRIMARY KEY,
    titulo TEXT NOT NULL,
    conteudo TEXT NOT NULL,
    categoria TEXT,
    data_atualizacao TEXT
)
```

**Dados de exemplo**: 5 artigos técnicos sobre:
- Gateway de Pagamento
- Reset de Senha
- Erros Python
- Performance SQL
- VPN Corporativa

### 2. `2_rag_app.py` - Aplicação RAG Principal

**Funções principais:**

#### `dsa_setup_weaviate()`
Configura o schema no Weaviate com:
- Propriedades: `titulo`, `conteudo`, `sql_id`
- Índice Vetorial: HNSW com distância cosseno

#### `dsa_indexa_dados()`
Lê artigos do SQLite e indexa no Weaviate:
1. Busca artigos no SQLite
2. Gera embeddings com `sentence-transformers`
3. Insere vetores no Weaviate em batch

#### `dsa_busca_solucao(query, alpha=0.5)`
Realiza busca híbrida:
- **alpha=1.0**: Puramente semântica (vetorial)
- **alpha=0.0**: Puramente lexical (BM25)
- **alpha=0.5**: Equilibrada

```python
response = collection.query.hybrid(
    query=query_usuario,      # Para BM25
    vector=vector_query,      # Para busca vetorial
    alpha=alpha,              # Peso relativo
    limit=2
)
```

#### `dsa_gera_resposta_ollama(query, contextos)`
Gera resposta usando LLaMA 3:
1. Formata contexto dos artigos recuperados
2. Cria prompt com instruções e contexto
3. Chama Ollama para gerar resposta

### 3. `3_insere_artigos.py` - Inserir Artigos Adicionais

Script para adicionar novos artigos ao banco sem perder os existentes.

### 4. `dsa_app.py` - Interface Streamlit

Interface web interativa para:
- Inserir perguntas
- Visualizar artigos recuperados
- Ver respostas do assistente
- Análise de scores de relevância

## 📚 Dependências Principais

| Biblioteca | Versão | Uso |
|-----------|--------|-----|
| `weaviate-client` | 4.18+ | Banco vetorial |
| `sentence-transformers` | 5.2+ | Geração de embeddings |
| `ollama` | 0.6+ | Cliente para LLaMA |
| `streamlit` | latest | Interface web |
| `torch` | 2.9+ | Backend ML |
| `scikit-learn` | 1.8+ | Utilities ML |

Ver `requirements.txt` para lista completa.

## 🔍 Exemplo de Uso

```python
# 1. Usuário faz uma pergunta
pergunta = "Meu gateway está retornando erro 503, o que fazer?"

# 2. Sistema busca artigos relevantes
resultados = dsa_busca_solucao(pergunta, alpha=0.5)
# Retorna: [Artigo sobre "Erro 503 no Gateway de Pagamento"]

# 3. Sistema gera resposta contextualizada
resposta = dsa_gera_resposta_ollama(pergunta, resultados)
# Retorna: "Verifique a configuração de timeout do Nginx..."
```

## ⚙️ Configuração Avançada

### Ajustar o peso da busca híbrida

```python
# Mais semântica (entende sinônimos)
resultados = dsa_busca_solucao(query, alpha=0.8)

# Mais exato (prioriza palavras-chave)
resultados = dsa_busca_solucao(query, alpha=0.2)
```

### Mudar o modelo de embedding

```python
# No arquivo 2_rag_app.py
EMBEDDING_MODEL = "sentence-transformers/paraphrase-MiniLM-L6-v2"
# ou qualquer modelo da HuggingFace
```

### Mudar o modelo LLM

```python
# No arquivo 2_rag_app.py
LLM_MODEL = "mistral"  # ou outro modelo instalado no Ollama
# ollama pull mistral
```

## 📊 Comparação: Busca Híbrida vs Alternativas

| Tipo de Busca | Vantagens | Desvantagens |
|--------------|-----------|-------------|
| **Vetorial Pura** | Entende sinônimos e contexto | Pode ignorar termos críticos exatos |
| **Keyword Pura (BM25)** | Precisa em termos exatos | Não entende variações/sinônimos |
| **Híbrida** ✅ | Combina o melhor dos dois | Requer tuning do parâmetro alpha |

## 🛡️ Segurança e Privacidade

- ✅ **Totalmente Local**: Nenhum dado enviado para APIs externas
- ✅ **Privado**: Seus documentos ficam apenas no seu servidor
- ✅ **Offline**: Funciona sem conexão à internet
- ✅ **Open Source**: Código aberto e auditável

## 📈 Melhorias Futuras

- [ ] Suportar múltiplos formatos de entrada (PDF, Word, CSV)
- [ ] Interface de admin para gerenciar artigos
- [ ] Métricas de performance e relevância
- [ ] Cache de embeddings
- [ ] Suporte a múltiplos idiomas
- [ ] API REST
- [ ] Testes automatizados

## 🤝 Contribuindo

Contribuições são bem-vindas! Sinta-se à vontade para:
1. Abrir issues
2. Submeter pull requests
3. Sugerir melhorias

## 📝 Licença

Este projeto é fornecido como exemplo educacional.

## 📞 Suporte

Para dúvidas ou problemas:
- Abra uma issue no GitHub
- Verifique a documentação do Weaviate: https://weaviate.io
- Verifique a documentação do Ollama: https://ollama.ai

## 🎓 Referências e Recursos

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Sentence Transformers](https://www.sbert.net/)
- [Ollama GitHub](https://github.com/ollama/ollama)
- [RAG Patterns](https://docs.llamaindex.ai/en/stable/modules/retrieval_augmented_generation/)
- [Hybrid Search Best Practices](https://weaviate.io/blog/hybrid-search-explained)

---

**Desenvolvido com ❤️ para a comunidade de IA e ML**
