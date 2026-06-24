FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
RUN pip install --upgrade pip

# --- Couche dépendances (mise en cache tant que pyproject.toml ne change pas) ---
# On installe les deps avec un stub app/ : un simple changement de code n'invalide plus le pip install.
COPY pyproject.toml ./
RUN mkdir -p app && touch app/__init__.py && pip install -e ".[dev,agents]"

# --- Couche code (rapide) ---
COPY . .

RUN chmod +x entrypoint.sh

EXPOSE 8000

# Healthcheck aligné sur la Definition of Done.
HEALTHCHECK --interval=30s --timeout=5s --start-period=25s --retries=3 \
    CMD python -c "import urllib.request,sys; sys.exit(0) if urllib.request.urlopen('http://localhost:8000/health').status==200 else sys.exit(1)"

CMD ["./entrypoint.sh"]
