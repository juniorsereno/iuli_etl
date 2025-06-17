# Use a imagem oficial do Python
FROM python:3.10-slim

# Define variáveis de ambiente
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Instala dependências do sistema
RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Cria e define o diretório de trabalho
WORKDIR /app

# Copia os arquivos necessários
COPY . .

# Instala dependências do Python
RUN pip install --upgrade pip && \
    pip install playwright psycopg2-binary python-dotenv

# Instala os browsers do Playwright
RUN playwright install --with-deps chromium

# Comando para executar o script
CMD ["python", "./main.py"]