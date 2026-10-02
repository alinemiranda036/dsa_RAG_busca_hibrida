# Projeto 2 - RAG com Busca Híbrida, Orquestração SQL e Banco Vetorial Para Suporte Técnico
# Módulo de Configuração do Banco de Dados SQL

# Import
import sqlite3

# Função para criação do banco de dados
def dsa_cria_banco_suporte():

    # Conecta ou cria o arquivo .db
    conn = sqlite3.connect('suporte_tecnico.db')
    cursor = conn.cursor()

    # Criação da tabela
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS artigos_suporte (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        titulo TEXT NOT NULL,
        conteudo TEXT NOT NULL,
        categoria TEXT,
        data_atualizacao TEXT
    )
    ''')

    # Dados de exemplo (Casos difíceis para busca puramente vetorial ou puramente keyword)
    dados = [
        ("Erro 503 no Gateway de Pagamento", "Se o gateway retornar 503, verifique se o balanceador de carga Nginx está com a configuração de timeout correta. Reinicie o serviço com 'systemctl restart nginx'.", "Infraestrutura", "2026-01-10"),
        ("Reset de Senha de Usuário Admin", "Para resetar a senha de admin, acesse o painel de controle, vá em Configurações > Segurança e clique em 'Forçar Logout'. O link de reset será enviado ao email cadastrado.", "Acesso", "2025-12-05"),
        ("Python: ModuleNotFound Error", "Esse erro ocorre quando a biblioteca não está instalada no ambiente virtual (venv). Execute 'pip install -r requirements.txt' e verifique se o venv está ativo.", "Desenvolvimento", "2024-02-20"),
        ("Lentidão na Consulta SQL", "Queries lentas geralmente indicam falta de índices. Use o comando EXPLAIN ANALYZE para verificar o plano de execução. Evite SELECT * em tabelas grandes.", "Banco de Dados", "2024-01-15"),
        ("Configuração de VPN Corporativa", "Para acessar a VPN, utilize o cliente Cisco AnyConnect. O endereço do servidor é vpn.empresa.com. O protocolo utilizado é DTLS para maior performance.", "Rede", "2023-11-30")
    ]

    # Executa o insert no banco de dados
    cursor.executemany('''
    INSERT INTO artigos_suporte (titulo, conteudo, categoria, data_atualizacao) 
    VALUES (?, ?, ?, ?)
    ''', dados)

    # Grava no banco de dados
    conn.commit()
    print(f"Banco SQLite criado com {len(dados)} artigos de suporte.")

    # Fecha a conexão
    conn.close()

# Bloco de execução
if __name__ == "__main__":
    dsa_cria_banco_suporte()




    