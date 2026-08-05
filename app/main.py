from fastapi import FastAPI, Depends, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, engine, Base
from app import models
from app.routes import consulta, upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Consulta de Contas - Clientes")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Conecta as rotas do arquivo consulta.py à aplicação principal
app.include_router(consulta.router)
app.include_router(upload.router)

@app.get("/")
def healthcheck():
    return {"status": "ok", "mensagem": "API rodando normalmente"}


@app.get("/healthcheck/db")
def healthcheck_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "banco": "conectado"}
    except Exception as erro:
        return {"status": "erro", "detalhe": str(erro)}

@app.get("/tela/consulta")
def tela_consulta(request: Request):
    return templates.TemplateResponse("consulta.html", {"request": request})

@app.get("/tela/upload")
def tela_upload(request: Request):
    return templates.TemplateResponse("upload.html", {"request": request})