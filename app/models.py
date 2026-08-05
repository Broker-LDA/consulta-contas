from sqlalchemy import Column, Integer, String, DateTime, CheckConstraint
from sqlalchemy.sql import func
from app.database import Base


class ClienteConta(Base):
    __tablename__ = "clientes_conta"

    id = Column(Integer, primary_key=True, index=True)
    sold = Column(String(20), unique=True, nullable=False, index=True)
    nome_cliente = Column(String(255), nullable=False)
    dados_bancarios = Column(String(30), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    atualizado_por = Column(String(100), nullable=True)

    __table_args__ = (
        CheckConstraint(
            "dados_bancarios IN ('Conta Bancária', 'Pagador', 'Conta e Pagador', 'Não Possui')",
            name="check_dados_bancarios"
        ),
    )