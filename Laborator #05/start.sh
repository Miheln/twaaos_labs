#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$LAB_DIR"

PORT=8000
APP_URL="http://127.0.0.1:${PORT}"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

if [[ ! -f .env ]]; then
  cp .env.example .env
fi

echo "Pornesc Laborator #05 pe portul ${PORT}..."
uvicorn main:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 40); do
  if curl -sf "$APP_URL/healthz" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$APP_URL" >/dev/null 2>&1 || true
else
  echo "Deschide in browser: $APP_URL"
fi

echo "Aplicatie: $APP_URL"
echo "Swagger: ${APP_URL}/docs"
echo "Oprire: Ctrl+C"
wait "$SERVER_PID"
