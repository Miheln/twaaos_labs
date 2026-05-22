#!/usr/bin/env bash
set -euo pipefail

LAB_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$LAB_DIR"

API_PORT=8000
UI_PORT=5500
API_URL="http://127.0.0.1:${API_PORT}"
UI_URL="http://127.0.0.1:${UI_PORT}/index.html"

if [[ ! -d venv ]]; then
  python3 -m venv venv
fi

source venv/bin/activate
pip install -q -r requirements.txt

echo "Pornesc API Laborator #04 pe portul ${API_PORT}..."
uvicorn main:app --host 127.0.0.1 --port "$API_PORT" &
API_PID=$!

echo "Pornesc interfata web pe portul ${UI_PORT}..."
python3 -m http.server "$UI_PORT" --bind 127.0.0.1 >/tmp/twaaos_lab04_ui.log 2>&1 &
UI_PID=$!

trap 'kill "$API_PID" "$UI_PID" 2>/dev/null || true' EXIT INT TERM

for _ in $(seq 1 40); do
  if curl -sf "$API_URL/" >/dev/null 2>&1; then
    break
  fi
  sleep 0.25
done

if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "$UI_URL" >/dev/null 2>&1 || true
else
  echo "Deschide in browser: $UI_URL"
fi

echo "Interfata: $UI_URL"
echo "Swagger: ${API_URL}/docs"
echo "Oprire: Ctrl+C"
wait "$API_PID" "$UI_PID"
