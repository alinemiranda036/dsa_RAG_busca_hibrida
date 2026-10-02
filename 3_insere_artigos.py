# Projeto 2 - RAG com Busca Híbrida, Orquestração SQL e Banco Vetorial Para Suporte Técnico
# Módulo de Inserção de Novos Artigos no Banco de Dados SQL

# Import
import sqlite3

# Função para inserir novos artigos no banco de dados já existente
def dsa_insere_artigos():

    # Conecta ao arquivo .db (criado previamente pelo 1_setup_database.py)
    conn = sqlite3.connect('suporte_tecnico.db')
    cursor = conn.cursor()

    # Novos dados de exemplo
    dados = [
        ("Erro 401 Unauthorized na API", "O erro 401 indica que o token de autenticação está ausente ou expirado. Gere um novo token no portal do desenvolvedor e envie no header 'Authorization: Bearer <token>'.", "Acesso", "2026-02-12"),
        ("Container Docker Não Inicia", "Verifique os logs com 'docker logs <nome_container>'. Causas comuns são porta já em uso ou variável de ambiente ausente. Use 'docker ps -a' para ver o status do container.", "Infraestrutura", "2026-03-01"),
        ("Impressora Corporativa Offline", "Confirme se a impressora está conectada à rede Wi-Fi corporativa. Remova e adicione novamente a impressora em Configurações > Dispositivos usando o endereço print.empresa.com.", "Hardware", "2025-10-18"),
    ]

    # Evita duplicidade: insere apenas os artigos cujo título ainda não existe na tabela
    inseridos = 0
    for titulo, conteudo, categoria, data_atualizacao in dados:

        cursor.execute("SELECT 1 FROM artigos_suporte WHERE titulo = ?", (titulo,))

        if cursor.fetchone():
            print(f"⏭️  Já existe, ignorado: {titulo}")
            continue

        # Executa o insert no banco de dados
        cursor.execute('''
        INSERT INTO artigos_suporte (titulo, conteudo, categoria, data_atualizacao)
        VALUES (?, ?, ?, ?)
        ''', (titulo, conteudo, categoria, data_atualizacao))

        print(f"➕ Inserido: {titulo}")
        inseridos += 1

    # Grava no banco de dados
    conn.commit()

    # Total atual da tabela
    total = cursor.execute("SELECT COUNT(*) FROM artigos_suporte").fetchone()[0]
    print(f"\n{inseridos} novo(s) artigo(s) inserido(s). Total na tabela: {total} artigos.")
    print("Agora clique em '📂 Indexar Base SQL' no app para atualizar o Weaviate.")

    # Fecha a conexão
    conn.close()

# Bloco de execução
if __name__ == "__main__":
    dsa_insere_artigos()
