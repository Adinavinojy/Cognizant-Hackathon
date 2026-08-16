FROM python:3.12-slim

# Keeps Python from generating .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensures stdout/stderr are flushed immediately
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system deps (psycopg2 needs libpq-dev)
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq-dev \
        gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps before copying source for layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

EXPOSE 8000

# Run migrations then start the server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
