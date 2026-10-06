#!/usr/bin/env bash
ROOT="$(cd "$(dirname "$0")" && pwd)"
if [[ -f "$ROOT/.backend.pid" ]]; then
  kill "$(cat "$ROOT/.backend.pid")" 2>/dev/null || true
  rm -f "$ROOT/.backend.pid"
fi
if [[ -f "$ROOT/.frontend.pid" ]]; then
  kill "$(cat "$ROOT/.frontend.pid")" 2>/dev/null || true
  rm -f "$ROOT/.frontend.pid"
fi
# Vite may spawn a child; free the port if still held
fuser -k 8001/tcp 5173/tcp 2>/dev/null || true
echo "Stopped API (8001) and UI (5173). Neo4j container was left running."
