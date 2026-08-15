# Production Hardened Dockerfile for FastAPI API & Worker
FROM python:3.12-slim AS base

WORKDIR /app

# Create non-root user and group
RUN groupadd -g 10001 appgroup && \
    useradd -u 10001 -g appgroup -s /bin/bash -m appuser

# Install minimal system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .

# Install dependencies into virtual environment
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .[dev] redis fakeredis

COPY . .

# Set permissions for non-root appuser
RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

# Healthcheck for API
HEALTHCHECK --interval=10s --timeout=3s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/v1/health || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
