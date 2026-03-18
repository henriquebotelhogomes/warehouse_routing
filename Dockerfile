# Stage 1: Builder
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# 1. Copia as definições de dependências
COPY pyproject.toml .

# 2. COPIA O CÓDIGO FONTE ANTES DA INSTALAÇÃO (Crucial para gerar os binários)
COPY src/ ./src/

# 3. Instala o projeto e todas as dependências (incluindo dev para o pytest)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir ".[dev]"

# Stage 2: Runtime
FROM python:3.12-slim

WORKDIR /app

RUN useradd -m appuser && chown -R appuser /app

# Copia as libs e os binários gerados no builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copia o código para o runtime
COPY src/ ./src/

RUN mkdir -p /app/data && chown appuser:appuser /app/data

ENV PYTHONPATH=/app/src
ENV MODEL_SAVE_PATH=/app/data/model.joblib

USER appuser