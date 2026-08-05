import shutil
import os
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.security import verificar_senha_upload
from app.services.importador import importar_planilha, ErroValidacaoPlanilha

router = APIRouter(prefix="/upload", tags=["Upload"])


@router.post("/planilha")
def upload_planilha(
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
    autorizado: bool = Depends(verificar_senha_upload),
):
    """
    Recebe um arquivo XLSX, valida e realiza a importação/atualização
    da base de clientes. Requer o header X-Upload-Secret correto.
    """
    if not arquivo.filename.endswith(".xlsx"):
        raise HTTPException(
            status_code=400,
            detail="Apenas arquivos .xlsx são aceitos."
        )

    caminho_temporario = f"temp_{arquivo.filename}"

    try:
        # Salva o arquivo temporariamente no disco para o pandas poder ler
        with open(caminho_temporario, "wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        resultado = importar_planilha(caminho_temporario, db, usuario="comercial")

        return {
            "status": "sucesso",
            "mensagem": "Planilha importada com sucesso.",
            "detalhes": resultado,
        }

    except ErroValidacaoPlanilha as erro:
        raise HTTPException(status_code=422, detail=str(erro))

    finally:
        # Remove o arquivo temporário, independentemente de sucesso ou erro
        if os.path.exists(caminho_temporario):
            os.remove(caminho_temporario)