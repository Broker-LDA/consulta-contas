from app.database import SessionLocal
from app.services.importador import importar_planilha, ErroValidacaoPlanilha

def testar_importacao():
    db = SessionLocal()
    try:
        resultado = importar_planilha("teste_planilha.xlsx", db, usuario="teste_local")
        print("✅ Importação concluída com sucesso!")
        print(resultado)
    except ErroValidacaoPlanilha as erro:
        print("❌ Erro de validação na planilha:")
        print(erro)
    except Exception as erro:
        print("❌ Erro inesperado:")
        print(erro)
    finally:
        db.close()

if __name__ == "__main__":
    testar_importacao()