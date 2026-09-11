import pandas as pd
from sqlalchemy.orm import Session
from app.models import ClienteConta

COLUNAS_CANONICAS = {
    "sold": "Sold",
    "nome": "Nome",
    "dados bancários": "Dados Bancários",
}

COLUNAS_ESPERADAS = {"Sold", "Nome", "Dados Bancários"}

VALORES_PERMITIDOS = {"Conta Bancária", "Pagador", "Conta e Pagador", "Não Possui"}

# Traduz qualquer variação de texto (antiga ou nova) para o valor canônico
MAPA_NORMALIZACAO = {
    "conta bancária": "Conta Bancária",
    "sim, conta bancária": "Conta Bancária",
    "pagador": "Pagador",
    "sim, pagador": "Pagador",
    "conta e pagador": "Conta e Pagador",
    "sim, conta e pagador": "Conta e Pagador",
    "não possui": "Não Possui",
}


class ErroValidacaoPlanilha(Exception):
    """Exceção customizada para erros de validação da planilha."""
    pass


def normalizar_dados_bancarios(valor: str) -> str | None:
    """
    Recebe o valor bruto da planilha (em qualquer formato aceito)
    e retorna a categoria canônica usada internamente e no gráfico,
    ou None se não corresponder a nenhum valor conhecido.
    """
    chave = str(valor).strip().lower()
    return MAPA_NORMALIZACAO.get(chave)


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Renomeia as colunas do DataFrame para os nomes canônicos esperados,
    tolerando variações de maiúsculas/minúsculas e espaços no cabeçalho.
    """
    mapa_renomeacao = {}
    for coluna_original in df.columns:
        chave = coluna_original.strip().lower()
        if chave in COLUNAS_CANONICAS:
            mapa_renomeacao[coluna_original] = COLUNAS_CANONICAS[chave]

    return df.rename(columns=mapa_renomeacao)


def validar_planilha(df: pd.DataFrame) -> None:
    """
    Valida estrutura e conteúdo da planilha (já com colunas normalizadas).
    Cada Sold deve aparecer EXATAMENTE UMA VEZ no arquivo.
    """
    colunas_encontradas = set(df.columns)

    if not COLUNAS_ESPERADAS.issubset(colunas_encontradas):
        colunas_faltando = COLUNAS_ESPERADAS - colunas_encontradas
        raise ErroValidacaoPlanilha(
            f"Colunas obrigatórias ausentes na planilha: {colunas_faltando}"
        )

    if df["Sold"].isnull().any():
        raise ErroValidacaoPlanilha("Existem linhas com o campo 'Sold' vazio.")

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

    valores_normalizados = df["Dados Bancários"].dropna().apply(normalizar_dados_bancarios)
    valores_invalidos_mask = valores_normalizados.isna()

    if valores_invalidos_mask.any():
        valores_originais_invalidos = set(df.loc[valores_invalidos_mask, "Dados Bancários"].dropna().unique())
        raise ErroValidacaoPlanilha(
            f"A coluna 'Dados Bancários' contém valor(es) não permitido(s): "
            f"{', '.join(str(v) for v in valores_originais_invalidos)}. "
            f"Valores aceitos (em qualquer um dos formatos reconhecidos): "
            f"{', '.join(sorted(VALORES_PERMITIDOS))}."
        )


def importar_planilha(caminho_arquivo: str, db: Session, usuario: str = "sistema") -> dict:
    """
    Lê o arquivo XLSX, valida seu conteúdo e realiza o upsert.
    Grava tanto a categoria (para o dashboard) quanto o texto original
    da planilha (para exibição fiel na tela de consulta).
    """
    df = pd.read_excel(caminho_arquivo, dtype={"Sold": str})
    df.columns = df.columns.str.strip()
    df = normalizar_colunas(df)

    validar_planilha(df)

    total_inseridos = 0
    total_atualizados = 0

    for _, linha in df.iterrows():
        sold = str(linha["Sold"]).strip()
        nome = str(linha["Nome"]).strip()

        valor_bruto = linha["Dados Bancários"]
        categoria = normalizar_dados_bancarios(valor_bruto)
        descricao_original = str(valor_bruto).strip()

        cliente_existente = db.query(ClienteConta).filter(
            ClienteConta.sold == sold
        ).first()

        if cliente_existente:
            cliente_existente.nome_cliente = nome
            cliente_existente.dados_bancarios = categoria
            cliente_existente.dados_bancarios_descricao = descricao_original
            cliente_existente.atualizado_por = usuario
            total_atualizados += 1
        else:
            novo_cliente = ClienteConta(
                sold=sold,
                nome_cliente=nome,
                dados_bancarios=categoria,
                dados_bancarios_descricao=descricao_original,
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