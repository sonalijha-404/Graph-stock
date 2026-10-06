# PortfolioGraph AI

Graph-powered portfolio intelligence demo: natural-language questions over a Neo4j graph, deterministic impact math in Python, and explainability in the UI.

All figures are **synthetic**. Not investment advice.

## Prerequisites

- Docker (Neo4j)
- Python 3.12+
- Node.js 20+

## Quick start

```bash
# 1. Environment
cp .env.example .env

# 2. Neo4j
docker compose up -d neo4j

# 3. Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python scripts/seed_data.py
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 4. Frontend (new terminal)
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Demo script

1. Dashboard shows live stats from `GET /stats`.
2. **Who owns TCS?** — includes Rahul Sharma.
3. **Who owns both TCS and Infosys?** — includes Rahul Sharma.
4. **Who is highly exposed to IT?** — Rahul at **75%** IT exposure.
5. **What happens if TCS drops 10%?** — Rahul **₹40,000** estimated unrealized impact.
6. **IT sector drops 10%** — sector → stocks → holdings path.
7. **How it works** — pipeline highlights stages from the last response.

## Tests

```bash
cd backend && source .venv/bin/activate
pytest
```

Integration tests require Neo4j running and seeded data.

## Architecture

- **Neo4j** — relationships and traversal
- **FastAPI** — catalog Cypher templates, validation, impact engine
- **LLM** (optional) — intent classification only; rule router is the fallback
