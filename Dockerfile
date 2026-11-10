FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_ENV=production \
    SERVE_FRONTEND=false \
    DATABASE_URL=sqlite:////data/customer_support.db \
    QDRANT_PATH=/data/vectors \
    KNOWLEDGE_PATH=/data/knowledge_base

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends gosu \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --home-dir /app app \
    && mkdir -p /data/vectors /data/knowledge_base \
    && chown -R app:app /app /data

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir -r requirements.txt

COPY --chown=app:app app/ ./app/

EXPOSE 10000

ENTRYPOINT ["sh", "-c", "mkdir -p /data/vectors /data/knowledge_base && chown app:app /data /data/vectors /data/knowledge_base && exec gosu app uvicorn app.main:app --host 0.0.0.0 --port \"${PORT:-10000}\" --workers 1 --no-access-log --no-server-header"]
