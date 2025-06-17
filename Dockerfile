# Usar uma imagem base do Python mais enxuta
FROM python:3.10-slim

# Definir variáveis de ambiente para Python e Playwright
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Criar o diretório de trabalho
WORKDIR /app

# Copiar o arquivo de dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .

# Instalar as dependências do sistema e do Python
# O --with-deps instala as dependências do sistema para os navegadores
RUN apt-get update && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    playwright install --with-deps chromium && \
    apt-get purge -y --auto-remove && \
    rm -rf /var/lib/apt/lists/*

# Copiar o restante do código da aplicação
COPY . .

# Comando para executar o script
CMD ["python", "main.py"]
