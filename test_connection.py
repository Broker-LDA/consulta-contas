from app.database import engine, Base
from app import models

def testar_conexao():
    try:
        # Tenta abrir uma conexão real com o banco
        conexao = engine.connect()
        print("✅ Conexão com o PostgreSQL estabelecida com sucesso!")
        conexao.close()

        # Cria a tabela clientes_conta, se ainda não existir
        Base.metadata.create_all(bind=engine)
        print("✅ Tabela 'clientes_conta' criada (ou já existia).")

    except Exception as erro:
        print("❌ Falha ao conectar ou criar tabela:")
        print(erro)

if __name__ == "__main__":
    testar_conexao()