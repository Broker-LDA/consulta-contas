import pandas as pd
from sqlalchemy.orm import Session
from app.models import ClienteConta

COLUNAS_ESPERADAS = {"Sold", "Nome", "Dados Bancários"}
VALORES_PERMITIDOS = {"Conta Bancária", "Pagador", "Conta e Pagador", "Não Possui"}
MAPA_NORMALIZACAO = {valor.strip().lower(): valor for valor in VALORES_PERMITIDOS}

class ErroValidacaoPlanilha(Exception):
    """Exceção customizada para erros de validação da planilha."""
    pass

def normalizar_dados_bancarios(valor: str) -> str | None:
    """
    Recebe o valor bruto da planilha e retorna a versão padronizada
    (exatamente como o banco espera), ou None se não corresponder
    a nenhum valor permitido, mesmo após normalização.
    """
    chave = str(valor).strip().lower()
    return MAPA_NORMALIZACAO.get(chave)

def validar_planilha(df: pd.DataFrame) -> None:
    """
    Valida estrutura e conteúdo da planilha.
    Cada Sold deve aparecer EXATAMENTE UMA VEZ no arquivo — a planilha
    representa o estado atual de cada cliente, não um histórico de mudanças.
    Lança ErroValidacaoPlanilha se algo estiver fora do padrão.
    """
    colunas_encontradas = set(df.columns)

    if not COLUNAS_ESPERADAS.issubset(colunas_encontradas):
        colunas_faltando = COLUNAS_ESPERADAS - colunas_encontradas
        raise ErroValidacaoPlanilha(
            f"Colunas obrigatórias ausentes na planilha: {colunas_faltando}"
        )

    if df["Sold"].isnull().any():
        raise ErroValidacaoPlanilha("Existem linhas com o campo 'Sold' vazio.")

    # --- Cada Sold só pode aparecer uma única vez na planilha ---
    solds_normalizados = df["Sold"].astype(str).str.strip()
    contagem_por_sold = solds_normalizados.value_counts()
    solds_duplicados = contagem_por_sold[contagem_por_sold > 1]

    if not solds_duplicados.empty:
        detalhes = ", ".join(
            f"{sold} ({qtd}x)" for sold, qtd in solds_duplicados.items()
        )
        raise ErroValidacaoPlanilha(
            f"Você está inserindo solds duplicados. "
            f"Valide a planilha para que cada sold apareça apenas uma vez. "
            f"Solds duplicados: {detalhes}. "
        )

    # --- Verifica valores de "Dados Bancários", com normalização ---
    valores_normalizados = df["Dados Bancários"].dropna().apply(normalizar_dados_bancarios)
    valores_invalidos_mask = valores_normalizados.isna()

    if valores_invalidos_mask.any():
        valores_originais_invalidos = set(df.loc[valores_invalidos_mask, "Dados Bancários"].dropna().unique())
        raise ErroValidacaoPlanilha(
            f"A coluna 'Dados Bancários' contém valor(es) não permitido(s): "
            f"{', '.join(str(v) for v in valores_originais_invalidos)}. "
            f"Valores aceitos: {', '.join(sorted(VALORES_PERMITIDOS))}."
        )

def importar_planilha(caminho_arquivo: str, db: Session, usuario: str = "sistema") -> dict:
    """
    Lê o arquivo XLSX, valida seu conteúdo e realiza o upsert
    (atualiza se o Sold já existe no banco, insere se é novo).
    Cada Sold deve aparecer uma única vez na planilha.
    """
    df = pd.read_excel(caminho_arquivo, dtype={"Sold": str})
    print("COLUNAS ENCONTRADAS:", list(df.columns))  # linha temporária de debug
    df.columns = df.columns.str.strip()

    validar_planilha(df)

    total_inseridos = 0
    total_atualizados = 0

    for _, linha in df.iterrows():
        sold = str(linha["Sold"]).strip()
        nome = str(linha["Nome"]).strip()
        dados_bancarios = normalizar_dados_bancarios(linha["Dados Bancários"])

        cliente_existente = db.query(ClienteConta).filter(
            ClienteConta.sold == sold
        ).first()

        if cliente_existente:
            cliente_existente.nome_cliente = nome
            cliente_existente.dados_bancarios = dados_bancarios
            cliente_existente.atualizado_por = usuario
            total_atualizados += 1
        else:
            novo_cliente = ClienteConta(
                sold=sold,
                nome_cliente=nome,
                dados_bancarios=dados_bancarios,
                atualizado_por=usuario,
            )
            db.add(novo_cliente)
            total_inseridos += 1

    db.commit()

    return {
        "total_processado": len(df),
        "inseridos": total_inseridos,
        "atualizados": total_atualizados,
    }