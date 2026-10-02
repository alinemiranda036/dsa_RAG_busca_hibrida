# Projeto 2 - RAG com Busca Híbrida, Orquestração SQL e Banco Vetorial Para Suporte Técnico
# Módulo da App (Interface Streamlit)

# Imports
import os
import importlib
import sqlite3
import streamlit as st

# Variável de ambiente
# Evita um comportamento indesejado do Hugging Face Tokenizers quando usado dentro de aplicações que executam várias threads em paralelo,
# como Streamlit, FastAPI ou Jupyter.
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Garante que caminhos relativos (ex: 'suporte_tecnico.db') sejam resolvidos a partir da pasta do projeto
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Configuração Inicial da Aplicação Streamlit
st.set_page_config(
    page_title="Engenharia de Dados para IA - Data Science Academy",  # Título que aparece na aba do navegador
    page_icon="🛠️",                     # Ícone (emoji) que aparece na aba do navegador
    layout="wide",                      # Define o layout da página para usar a largura total da tela
    initial_sidebar_state="expanded",   # Garante que a sidebar (menu lateral) comece aberta
)

# Estilização customizada (CSS)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }

    /* Reduz o espaço vazio no topo da página */
    .block-container {
        padding-top: 2rem;
    }

    /* Fundo em degradê para o app inteiro */
    .stApp {
        background: linear-gradient(160deg, #0F172A 0%, #14224a 45%, #0B1220 100%);
    }

    /* Bolhas de chat mais suaves */
    div[data-testid="stChatMessage"] {
        border-radius: 14px;
        border: 1px solid #1E293B;
        box-shadow: 0 2px 10px rgba(0,0,0,0.25);
        padding: 0.5rem 0.25rem;
    }

    /* Botão: gradiente azul + sombra + brilho espelhado no topo */
    .stButton > button {
        position: relative;
        overflow: hidden;
        border-radius: 999px;
        border: none;
        color: white;
        font-weight: 600;
        padding: 0.5rem 1.3rem;
        background: linear-gradient(180deg, #2C5282 0%, #1A365D 100%);
        box-shadow:
            0 4px 14px rgba(59, 130, 246, 0.45),
            inset 0 1px 0 rgba(255, 255, 255, 0.25);
        transition: all 0.2s ease;
    }

    /* Faixa de "reflexo" na metade superior do botão (efeito espelhado) */
    .stButton > button::before {
        content: "";
        position: absolute;
        top: 0; left: 0; right: 0;
        height: 50%;
        background: linear-gradient(180deg, rgba(255,255,255,0.35) 0%, rgba(255,255,255,0) 100%);
        pointer-events: none;
    }

    .stButton > button:hover {
        background: linear-gradient(180deg, #2B6CB0 0%, #2C5282 100%);
        box-shadow:
            0 6px 20px rgba(59, 130, 246, 0.6),
            inset 0 1px 0 rgba(255, 255, 255, 0.3);
        transform: translateY(-2px);
    }

    .stButton > button:active {
        transform: translateY(0px);
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.4);
    }
</style>
""", unsafe_allow_html=True)


# Carrega o módulo do RAG uma única vez (modelo de embedding + conexão com o Weaviate)
# O nome do arquivo começa com número (2_rag_app.py), por isso usamos importlib
@st.cache_resource(show_spinner="Carregando modelo de embedding e conectando ao Weaviate...")
def dsa_carrega_rag():
    return importlib.import_module("2_rag_app")

rag = dsa_carrega_rag()


# Verifica se a coleção existe e quantos artigos estão indexados
def dsa_total_indexado():
    if not rag.client.collections.exists("ArtigoSuporte"):
        return 0
    collection = rag.client.collections.get("ArtigoSuporte")
    return collection.aggregate.over_all(total_count=True).total_count


# Busca no SQLite os dados que não foram vetorizados (ex: categoria), usando o sql_id como chave
def dsa_busca_categorias(sql_ids):
    placeholders = ",".join("?" for _ in sql_ids)
    with sqlite3.connect("suporte_tecnico.db") as conn:
        linhas = conn.execute(
            f"SELECT id, categoria FROM artigos_suporte WHERE id IN ({placeholders})", sql_ids
        ).fetchall()
    return dict(linhas)


# Títulos
st.markdown("""
<div style="text-align:center; padding: 0.5rem 0 1.5rem 0;">
    <h1 style="margin-bottom:0;">🛠️ Assistente de Suporte Técnico</h1>
    <p style="color:#94A3B8; font-size:0.95rem; margin-top:0.3rem;">
        Engenharia de Dados para IA · Data Science Academy
    </p>
</div>
""", unsafe_allow_html=True)

with st.expander("ℹ️ Sobre este sistema", expanded=True):
    st.markdown("""
    Este sistema utiliza **RAG com Busca Híbrida** (vetorial + palavra-chave) para responder
    perguntas com base na base de conhecimento de suporte técnico da empresa.
    - Modelo de Embeddings: `all-MiniLM-L6-v2` (Hugging Face)
    - Modelo de LLM: `llama3` (Ollama - local)
    - Banco Vetorial e Busca Híbrida (HNSW + BM25): `Weaviate`
    - Fonte de Dados: `SQLite` (suporte_tecnico.db)
    """)

with st.expander("💡 Perguntas modelo", expanded=False):
    st.markdown("""
    - Estou recebendo o Erro 503. O que fazer?
    - Minha consulta SQL está mais lenta do que o normal. O que pode causar isso?
    - Como faço para acessar a VPN da empresa?

    **Fora da base de conhecimento** (o assistente deve responder que não sabe):
    - Qual a antecedência mínima para solicitação de férias?
    - Qual o horário de funcionamento do refeitório da empresa?
    """)


# --- Sidebar: Área de Gestão de Conhecimento (Indexação e Configuração da Busca) ---
with st.sidebar:

    st.header("⚙️ Gestão de Conhecimento")

    # Status da indexação
    total = dsa_total_indexado()
    if total > 0:
        st.success(f"✅ {total} artigos indexados no Weaviate.")
    else:
        st.info("Nenhum artigo indexado. Clique em **Indexar Base SQL** para começar.")

    if st.button("📂 Indexar Base SQL"):

        with st.spinner("Processando (Lendo SQLite, Vetorizando e Indexando)..."):

            # Recria o schema e indexa os artigos do SQLite no Weaviate
            rag.dsa_setup_weaviate()
            rag.dsa_indexa_dados()

        st.rerun()

    st.markdown("---")

    # Peso da busca híbrida
    alpha = st.slider(
        "🎚️ Peso da Busca Híbrida (alpha)",
        min_value=0.0,
        max_value=1.0,
        value=0.5,
        step=0.1,
        help="0.0 = apenas palavra-chave (BM25) · 0.5 = híbrido equilibrado · 1.0 = apenas vetorial (semântica)",
    )
    st.caption("""
- **0.0** - favorece a busca por palavra-chave (BM25)
- **0.5** - favorece a busca híbrida (equilibrada)
- **1.0** - favorece a busca vetorial (semântica)
""")

    st.markdown("---")

    st.markdown("⚠️ Ao acionar o botão abaixo a coleção vetorial criada a partir do banco SQL será deletada.")

    if st.button("🗑️ Limpar Banco Vetorial"):
        if rag.client.collections.exists("ArtigoSuporte"):
            rag.client.collections.delete("ArtigoSuporte")
            st.warning("Coleção 'ArtigoSuporte' removida do Weaviate.")
        else:
            st.warning("Não há coleção para remover.")

    st.markdown("---")

    st.sidebar.markdown(
        """
        <div style="background-color:#1A365D; padding: 10px; border-radius: 5px; text-align: center; margin-bottom: 15px;">
            <h3 style="color:white; margin:0; font-weight:bold;">Dúvidas?</h3>
            <p style="color:white; margin:0; font-weight:bold; font-size:0.7rem; white-space:nowrap;">suporte@datascienceacademy.com.br</p>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- Área Principal: Chat ---

# Inicializa histórico de chat
if "messages" not in st.session_state:
    st.session_state.messages = []

# Exibe mensagens anteriores
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Input do usuário
if prompt := st.chat_input("Descreva seu problema técnico (ex: Erro 503, VPN, SQL lento...)"):

    # 1. Adiciona pergunta ao histórico
    st.session_state.messages.append({"role": "user", "content": prompt})

    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Gera resposta usando a Busca Híbrida + Ollama
    with st.chat_message("assistant"):

        if dsa_total_indexado() == 0:
            answer = "⚠️ A base de conhecimento ainda não foi indexada. Clique em **📂 Indexar Base SQL** na barra lateral."
            st.markdown(answer)

        else:
            with st.spinner("Executando busca híbrida no Weaviate..."):

                # Etapa A: Busca Híbrida
                resultados = rag.dsa_busca_solucao(prompt, alpha=alpha)

            if not resultados:
                answer = "❌ Nenhum artigo relevante encontrado."
                st.markdown(answer)

            else:
                with st.spinner("Ollama gerando resposta..."):

                    # Etapa B: Geração (RAG)
                    answer = rag.dsa_gera_resposta_ollama(prompt, resultados)

                # Exibe a resposta
                st.markdown(answer)

                # --- Exibindo Metadados ---
                with st.expander("📚 Artigos Consultados (Metadados)"):

                    # Enriquece os resultados com a categoria vinda do SQLite (orquestração SQL)
                    categorias = dsa_busca_categorias([doc.properties['sql_id'] for doc in resultados])

                    for doc in resultados:

                        # Extrai metadados do artigo recuperado
                        titulo = doc.properties.get('titulo', 'Desconhecido')
                        sql_id = doc.properties.get('sql_id', 'N/A')
                        categoria = categorias.get(sql_id, 'N/A')
                        score = doc.metadata.score
                        preview = doc.properties.get('conteudo', '')[:150] + "..."

                        st.markdown(f"**Artigo:** `{titulo}` | **Categoria:** `{categoria}` | **ID SQL:** `{sql_id}` | **Score:** `{score:.4f}`")
                        st.caption(f"Trecho: {preview}")

    # 3. Adiciona resposta ao histórico
    st.session_state.messages.append({"role": "assistant", "content": answer})


# Fim
