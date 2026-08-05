from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from app.database import get_db
from app.models import ClienteConta
from app.schemas import ClienteContaResponse
from typing import Optional, List

router = APIRouter(prefix="/consulta", tags=["Consulta"])

@router.get("/estatisticas/resumo")
def obter_estatisticas(db: Session = Depends(get_db)):
    """
    Retorna a contagem de clientes agrupada por tipo de Dados Bancários.
    Usado para alimentar o gráfico/dashboard da tela de consulta.
    """
    resultado = (
        db.query(ClienteConta.dados_bancarios, func.count(ClienteConta.id))
        .group_by(ClienteConta.dados_bancarios)
        .all()
    )

    contagem = {categoria: total for categoria, total in resultado}
    total_geral = sum(contagem.values())

    return {
        "total_geral": total_geral,
        "categorias": {
            "Conta Bancária": contagem.get("Conta Bancária", 0),
            "Pagador": contagem.get("Pagador", 0),
            "Conta e Pagador": contagem.get("Conta e Pagador", 0),
            "Não Possui": contagem.get("Não Possui", 0),
        }
    }

@router.get("/{sold}", response_model=ClienteContaResponse)
def buscar_cliente_por_sold(sold: str, db: Session = Depends(get_db)):
    """
    Busca um cliente pelo código Sold.
    Retorna 404 caso o Sold não seja encontrado na base.
    """
    cliente = db.query(ClienteConta).filter(ClienteConta.sold == sold.strip()).first()

    if not cliente:
        raise HTTPException(
            status_code=404,
            detail=f"Nenhum cliente encontrado com o Sold '{sold}'."
        )

    return cliente

@router.get("", response_model=dict)
def listar_clientes(
    db: Session = Depends(get_db),
    busca: Optional[str] = Query(None, description="Filtra por Sold ou Nome do cliente"),
    pagina: int = Query(1, ge=1, description="Número da página, começando em 1"),
    por_pagina: int = Query(50, ge=1, le=100, description="Quantidade de itens por página"),
):
    """
    Lista clientes de forma paginada, com filtro opcional por Sold ou Nome.
    """
    query = db.query(ClienteConta)

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                ClienteConta.sold.ilike(termo),
                ClienteConta.nome_cliente.ilike(termo),
            )
        )

    total_registros = query.count()

    resultados = (
        query.order_by(ClienteConta.nome_cliente)
        .offset((pagina - 1) * por_pagina)
        .limit(por_pagina)
        .all()
    )

    return {
        "total_registros": total_registros,
        "pagina_atual": pagina,
        "total_paginas": (total_registros + por_pagina - 1) // por_pagina,
        "resultados": [ClienteContaResponse.model_validate(c) for c in resultados],
    }