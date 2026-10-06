#!/usr/bin/env bash
# Everyday start: Neo4j + API on 8001 + UI on 5173.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

if ! docker start graphdemodb-neo4j-1 >/dev/null 2>&1; then
  docker compose up -d neo4j
fi

echo "Waiting for Neo4j..."
ready=0
for _ in $(seq 1 30); do
  if docker exec graphdemodb-neo4j-1 cypher-shell -u neo4j -p portfolio123 "RETURN 1" >/dev/null 2>&1; then
    ready=1
    break
  fi
  sleep 2
done
if [[ "$ready" != "1" ]]; then
  echo "Neo4j did not become ready. Check: docker logs graphdemodb-neo4j-1"
  exit 1
fi

cd "$ROOT/backend"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  . .venv/bin/activate
  pip install -r requirements.txt
else
  . .venv/bin/activate
fi

CUSTOMERS=$(docker exec graphdemodb-neo4j-1 cypher-shell -u neo4j -p portfolio123 --format plain \
  "MATCH (c:Customer) RETURN count(c)" | awk 'NF && $1 ~ /^[0-9]+$/ {n=$1} END {print n+0}')
if [[ "$CUSTOMERS" == "0" ]]; then
  echo "Seeding graph..."
  python scripts/seed_data.py
fi

if ! curl -sf http://127.0.0.1:8001/health | grep -q '"neo4j"'; then
  echo "Starting API on 8001..."
  nohup uvicorn app.main:app --host 127.0.0.1 --port 8001 > "$ROOT/backend.log" 2>&1 &
  echo $! > "$ROOT/.backend.pid"
  sleep 2
fi

cd "$ROOT/frontend"
if [[ ! -d node_modules ]]; then
  npm install
fi

if ! curl -sf -o /dev/null http://127.0.0.1:5173/; then
  echo "Starting UI on 5173..."
  nohup npm run dev -- --host 127.0.0.1 --port 5173 > "$ROOT/frontend.log" 2>&1 &
  echo $! > "$ROOT/.frontend.pid"
  sleep 2
fi

echo ""
echo "PortfolioGraph AI is running."
echo "  UI:  http://127.0.0.1:5173"
echo "  API: http://127.0.0.1:8001/health"
echo "Stop with: ./stop-demo.sh"
