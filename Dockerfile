FROM python:3.11-slim

WORKDIR /app

# Instalar utilitários essenciais
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Permissões de execução
RUN chmod +x run.sh server.py

EXPOSE 5050
ENV PORT=5050
ENV PYTHONUNBUFFERED=1

CMD ["python3", "server.py"]
