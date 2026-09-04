#!/bin/sh
set -eu

# Railway MVP deployment: keep API and durable review worker on one service so
# both processes share the same local /app/data volume.
python review_worker.py &
worker_pid=$!

cleanup() {
  kill "$worker_pid" 2>/dev/null || true
}
trap cleanup TERM INT EXIT

uvicorn main:app --host 0.0.0.0 --port "${PORT:-8000}"
