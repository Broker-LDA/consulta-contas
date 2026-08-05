from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ClienteContaResponse(BaseModel):
    sold: str
    nome_cliente: str
    dados_bancarios: str
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True  # permite converter direto de um objeto SQLAlchemy