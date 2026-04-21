FROM python:3.11-slim

WORKDIR /app

# Dépendances système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python
COPY src/agent/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code agent
COPY src/agent/agent.py .

# Variables d'environnement
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

CMD ["python", "agent.py"]