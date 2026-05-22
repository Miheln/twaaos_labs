#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$LAB_DIR"

PORT=8000
APP_URL="http://127.0.0.1:${PORT}"
DOCS_URL="${APP_URL}/docs"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "Pornesc Laborator #03 pe portul ${PORT}..."
uvicorn main:app --host 127.0.0.1 --port "$PORT" &
SERVER_PID=$!

trap 'kill "$SERVER_PID" 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 40); do
  if curl -sf "$APP_URL/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$DOCS_URL" >/dev/null 2>&1 || true
else
  echo "Deschide in browser: $DOCS_URL"
fi

echo "Swagger: $DOCS_URL"
echo "Oprire: Ctrl+C"
wait "$SERVER_PID"
