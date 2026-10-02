# Projeto 2 - RAG com Busca Híbrida, Orquestração SQL e Banco Vetorial Para Suporte Técnico
# Módulo do RAG

# Imports
import ollama
import sqlite3
import weaviate
import weaviate.classes.config as wvc
from weaviate.classes.query import MetadataQuery
from sentence_transformers import SentenceTransformer
import warnings
warnings.filterwarnings('ignore')

# --- CONFIGURAÇÕES INICIAIS ---

WEAVIATE_URL = "http://localhost:8080"
LLM_MODEL = "llama3"                 # Certifique-se de ter rodado: ollama pull llama3
EMBEDDING_MODEL = "all-MiniLM-L6-v2" # Modelo de embedding leve e rápido para rodar local
# https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2

# --- 1. PREPARAÇÃO DOS CLIENTES ---

print("⏳ Carregando Modelo de Embedding...")
encoder = SentenceTransformer(EMBEDDING_MODEL)

print("🔌 Conectando ao Banco Vetorial (Weaviate)...")
client = weaviate.connect_to_local()

# --- 2. DEFINIÇÃO DO SCHEMA (COLLECTION) ---

def dsa_setup_weaviate():

    # Se a classe já existe, deletamos para começar limpo
    if client.collections.exists("ArtigoSuporte"):
        client.collections.delete("ArtigoSuporte")
    
    # Criamos a coleção com configuração explícita
    client.collections.create(
        name = "ArtigoSuporte",
        properties = [
            wvc.Property(name = "titulo", data_type = wvc.DataType.TEXT),
            wvc.Property(name = "conteudo", data_type = wvc.DataType.TEXT),
            wvc.Property(name = "sql_id", data_type = wvc.DataType.INT), # Chave estrangeira para o SQLite
        ],
        # Configuração do índice vetorial (HNSW)
        vector_index_config = wvc.Configure.VectorIndex.hnsw(
            distance_metric = wvc.VectorDistances.COSINE
        )
    )

    print("✅ Schema definido no Weaviate.")

# -- EXPLICANDO A CONFIGURAÇÃO DO SCHEMA --

# No início, a função verifica se já existe uma coleção chamada ArtigoSuporte no Weaviate. Caso exista,
# essa coleção é removida. Essa etapa é importante, pois garante idempotência e evita conflitos de
# schema, dados duplicados ou configurações antigas que poderiam afetar a indexação vetorial e as
# consultas semânticas.

# Em seguida, a função cria novamente a coleção ArtigoSuporte com uma definição explícita de
# propriedades. O campo titulo armazena o título textual do artigo, o campo conteudo guarda o texto
# completo que será vetorizado para busca semântica e o campo sql_id é um inteiro que funciona como
# chave estrangeira para um banco relacional como SQLite, permitindo rastreabilidade e integração
# entre o mundo vetorial e dados estruturados tradicionais.

# Por fim, a função configura explicitamente o índice vetorial usando o algoritmo HNSW com métrica de
# distância cosseno. Essa configuraçao é fundamental para buscas semânticas eficientes, pois o HNSW
# oferece excelente desempenho em consultas aproximadas de alta dimensionalidade, enquanto a
# distância cosseno é adequada para embeddings textuais. A mensagem final apenas confirma que o
# schema foi definido com sucesso, sinalizando que o ambiente está pronto para ingestão e consultas.

# --- 3. INGESTÃO: SQL -> WEAVIATE ---

def dsa_indexa_dados():

    # Conecta ao banco de dados
    conn = sqlite3.connect('suporte_tecnico.db')
    cursor = conn.cursor()

    # Executa consulta no banco de dados
    cursor.execute("SELECT id, titulo, conteudo FROM artigos_suporte")

    # Extrai os dados
    artigos = cursor.fetchall() # [(id, titulo, conteudo), ...]

    # Obtém a collection
    collection = client.collections.get("ArtigoSuporte")
    
    print(f"🚀 Iniciando indexação de {len(artigos)} artigos...")
    
    # Batch Insert para eficiência
    with collection.batch.dynamic() as batch:

        # Loop
        for sql_id, titulo, conteudo in artigos:

            # 1. Gerar vetor (Embedding)
            texto_para_vetorizar = f"{titulo}: {conteudo}"
            vetor = encoder.encode(texto_para_vetorizar).tolist()
            
            # 2. Adicionar ao Batch
            batch.add_object(
                properties = {
                    "titulo": titulo,
                    "conteudo": conteudo,
                    "sql_id": sql_id
                },
                vector = vetor
            )
            
    conn.close()
    print("✅ Indexação concluída.")

# --- 4. FUNÇÃO DE BUSCA HÍBRIDA ---

def dsa_busca_solucao(query_usuario, alpha = 0.5):
    """
    alpha=1.0 -> Busca puramente Vetorial (Semântica)
    alpha=0.0 -> Busca puramente por Palavra-Chave (BM25)
    alpha=0.5 -> Híbrido equilibrado
    """

    # Obtém a collection
    collection = client.collections.get("ArtigoSuporte")

    # Encoding
    vector_query = encoder.encode(query_usuario).tolist()

    # Busca híbrida
    response = collection.query.hybrid(
        query = query_usuario,    # Usado para a parte keyword (BM25)
        vector = vector_query,    # Usado para a parte vetorial
        alpha = alpha,            # Peso da busca
        limit = 2,
        return_metadata = MetadataQuery(score = True)
    )
    
    return response.objects

# -- EXPLICANDO AS FUNCIONALIDADES DA FUNÇÃO DE BUSCA HÍBRIDA --

# O objetivo principal é equilibrar compreensão de significado com precisão lexical, algo essencial em cenários reais de suporte, documentação técnica e RAG.

# A função recebe a consulta do usuário em texto e um parâmetro alpha que controla o peso relativo
# entre os dois mecanismos de busca. Quando alpha é igual a 1, o resultado depende exclusivamente da
# similaridade vetorial, ou seja, do significado semântico da pergunta. Quando alpha é igual a O, a busca
# passa a ser puramente lexical, baseada em BM25, favorecendo correspondência exata de termos.
# Valores intermediários permitem um equilíbrio entre os dois mundos.

# Internamente, a função acessa a coleção ArtigoSuporte no Weaviate e transforma o texto da consulta
# em um vetor numérico usando um modelo de embeddings. Esse vetor representa semanticamente a
# intenção do usuário e será usado na parte vetorial da busca. Ao mesmo tempo, o texto original da
# consulta é mantido para alimentar o mecanismo de busca por palavras chave.

# A chamada hybrid executa simultaneamente os dois tipos de busca e combina os scores de relevância
# usando o parâmetro alpha. O Weaviate calcula um score final ponderado, retornando os documentos
# mais relevantes segundo esse critério híbrido. O limite define quantos resultados serão retornados e o
# metadata com score habilitado permite inspecionar a relevância de cada item recuperado.

# O resultado final da função são os objetos mais relevantes encontrados na coleção, já ordenados pelo
# score híbrido. Esse padrão é amplamente utilizado em sistemas profissionais de busca e RAG porque
# reduz falhas típicas da busca puramente semantica, como ignorar termos críticos, e também supera
# limitações da busca puramente lexical, como não entender sinônimos ou contexto.

# --- 5. GERAÇÃO COM OLLAMA (RAG) ---

def dsa_gera_resposta_ollama(query, contextos):

    # Formata o contexto recuperado
    contexto_str = "\n---\n".join([f"Título: {obj.properties['titulo']}\nConteúdo: {obj.properties['conteudo']}" for obj in contextos])
    
    prompt = f"""
    Você é um assistente de suporte técnico Sênior. Use APENAS as informações abaixo para responder à pergunta do usuário.
    Se a informação não estiver no contexto, diga que não sabe.
    
    CONTEXTO RECUPERADO DO BANCO DE CONHECIMENTO:
    {contexto_str}
    
    PERGUNTA DO USUÁRIO:
    {query}
    
    RESPOSTA (Seja direto e técnico):
    """
    
    print("\n🤖 OLLAMA Gerando resposta...")
    response = ollama.chat(model = LLM_MODEL, messages = [{'role': 'user', 'content': prompt},])
    
    return response['message']['content']

# --- EXECUÇÃO PRINCIPAL ---

if __name__ == "__main__":

    # Executa as funções
    dsa_setup_weaviate()
    dsa_indexa_dados()
    
    # loop
    while True:

        print("\n" + "="*50)
        pergunta = input("Digite seu problema técnico (ou 'sair'): ")

        if pergunta.lower() == 'sair': break
        
        # Etapa A: Busca Híbrida
        # Usamos alpha=0.5 para equilibrar termos exatos (ex: 'Erro 503') com o sentido
        resultados = dsa_busca_solucao(pergunta, alpha = 0.5)
        
        if not resultados:
            print("❌ Nenhum artigo relevante encontrado.")
            continue
            
        print(f"\n🔍 Encontrados {len(resultados)} artigos relevantes:")
        
        for doc in resultados:
            print(f" - [{doc.metadata.score:.4f}] {doc.properties['titulo']}")
        
        # Etapa B: Geração (RAG)
        resposta = dsa_gera_resposta_ollama(pergunta, resultados)
        
        print("\n📝 RESPOSTA DO ASSISTENTE:")
        print(resposta)


        