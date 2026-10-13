#!/bin/sh
set -e

echo "=================================================="
echo " Starting Project Hares Zero-Cost Free-Tier Node "
echo "=================================================="

# Determine port (Render injects $PORT, defaults to 8000)
LISTEN_PORT="${PORT:-8000}"

echo "[1/2] Launching in-process Celery worker (queues: high_priority_triage, media_triage)..."
celery -A hares.workers.celery_app.celery_app worker \
    --loglevel=info \
    -Q high_priority_triage,media_triage \
    -c 2 \
    --max-tasks-per-child=100 &

CELERY_PID=$!
echo "Celery worker launched in background (PID: $CELERY_PID)."

echo "[2/2] Launching FastAPI ASGI Gateway via Uvicorn on 0.0.0.0:$LISTEN_PORT..."
exec uvicorn hares.main:app --host 0.0.0.0 --port "$LISTEN_PORT" --workers 2
