# Imagem base: Python 3.12 na versão "slim" (mais leve, sem pacotes desnecessários)
FROM python:3.12-slim

# Define o diretório de trabalho dentro do container
WORKDIR /app

# Copia primeiro só o requirements.txt (otimização de cache de build)
COPY requirements.txt .

# Instala as dependências
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código para dentro do container
COPY . .

# Expõe a porta que a aplicação vai usar
EXPOSE 8000

# Comando que inicia a aplicação quando o container sobe
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]