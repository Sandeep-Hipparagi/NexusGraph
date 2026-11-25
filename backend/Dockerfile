FROM python:3.12-slim

WORKDIR /app

# Install system dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy source code
COPY . /app

ENV PYTHONPATH=/app
ENV FALKORDB_HOST=falkordb
ENV FALKORDB_PORT=6379

# Run as an unprivileged user
RUN useradd --uid 1000 --create-home nexususer && chown -R nexususer:nexususer /app
USER nexususer

# OCI labels for GitHub Packages repository linking
LABEL org.opencontainers.image.source="https://github.com/Sandeep-Hipparagi/NexusGraph" \
      org.opencontainers.image.description="Multi-agent incident intelligence on FalkorDB: deterministic tenant isolation, Cypher-level execution traces, MCP tooling, and episodic graph memory" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.title="NexusGraph" \
      org.opencontainers.image.version="1.0.0"

EXPOSE 8000

# Startup script: auto-seed graph on startup then start FastAPI
CMD ["sh", "-c", "python -m backend.db.seed_graph && uvicorn backend.main:app --host 0.0.0.0 --port 8000"]
