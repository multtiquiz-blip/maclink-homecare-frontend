FROM python:3.12-slim

WORKDIR /app

# Copia e instala as dependências do projeto
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copia o restante do código
COPY . .

# Expõe a porta que o Fly.io vai usar internamente
EXPOSE 8080

# Comando para iniciar a API
CMD uvicorn --host 0.0.0.0 --port 8080 backend.modo_local.main:app
