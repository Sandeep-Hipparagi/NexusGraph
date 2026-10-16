FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt /app/backend/requirements.txt
RUN pip install --no-cache-dir -r /app/backend/requirements.txt

# Copy source code
COPY backend /app/backend
COPY .env.example /app/.env

ENV PYTHONPATH=/app
ENV FALKORDB_HOST=falkordb
ENV FALKORDB_PORT=6379

EXPOSE 8000

# Startup script: auto-seed graph on startup then start FastAPI
CMD ["sh", "-c", "python -m backend.db.seed_graph && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
