import os
from fastapi import Header, HTTPException, status
from dotenv import load_dotenv

load_dotenv()

UPLOAD_SECRET = os.getenv("UPLOAD_SECRET")


def verificar_senha_upload(x_upload_secret: str = Header(...)):
    """
    Verifica se a senha enviada no header 'X-Upload-Secret' 
    corresponde à senha configurada no servidor.
    Usado como dependência para proteger a rota de upload.
    """
    if x_upload_secret != UPLOAD_SECRET:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Senha de upload inválida."
        )
    return True