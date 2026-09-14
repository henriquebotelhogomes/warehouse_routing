# ==========================================
# STAGE 1: Frontend Builder (React 19 / Vite)
# ==========================================
FROM node:22-slim AS frontend-builder

WORKDIR /app/frontend

COPY frontend/package.json ./
RUN npm install

COPY frontend/ ./
RUN npm run build

# ==========================================
# STAGE 2: Backend Dependencies Builder
# ==========================================
FROM python:3.12-slim AS backend-builder

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src/ ./src/

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# ==========================================
# STAGE 3: Production Runtime (Cloud Run Optimized)
# ==========================================
FROM python:3.12-slim AS runtime

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app/src
ENV PORT=8000

# Usuário não-root para segurança corporativa
RUN useradd -m -u 1000 appuser && \
    mkdir -p /app/data && \
    chown -R appuser:appuser /app

# Copia pacotes Python pré-compilados do Stage 2
COPY --from=backend-builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copia o código fonte do backend
COPY --chown=appuser:appuser src/ ./src/

# Copia os arquivos compilados do frontend do Stage 1
COPY --from=frontend-builder --chown=appuser:appuser /app/frontend/dist ./frontend/dist

USER appuser

EXPOSE 8000

# Execução com suporte à variável PORT do Google Cloud Run
CMD ["sh", "-c", "uvicorn warehouse_routing.api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]