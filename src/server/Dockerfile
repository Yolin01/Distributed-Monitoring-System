FROM python:3.11-slim

# Installer les dépendances système
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Installer les dépendances Python (en root, dans /usr/local)
COPY src/server/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code source
COPY src/server/app ./app
COPY config ./config
COPY scripts ./scripts
COPY tests ./tests

# Variables d'environnement
ENV PYTHONPATH="/app"
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]