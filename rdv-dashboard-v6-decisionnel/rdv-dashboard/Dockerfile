FROM python:3.11-slim

# Dépendances système nécessaires à hdbscan (compilation C) et psycopg2
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1) On copie SEULEMENT requirements.txt d'abord
#    → Docker met cette étape en cache tant que ce fichier ne change pas
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2) Le code applicatif est copié APRÈS
#    → modifier un .py ne invalide pas le cache pip (gain de temps énorme)
COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0", "--server.port=8501"]
