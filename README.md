# PortfolioGraph AI

Graph-powered portfolio intelligence demo: natural-language questions over a Neo4j graph, deterministic impact math in Python, and explainability in the UI.

All figures are **synthetic**. Not investment advice.

## Prerequisites

- Docker (Neo4j)
- Python 3.12+
- Node.js 20+

## Run it again

From the project folder:

```bash
./start-demo.sh
```

Open **http://127.0.0.1:5173**

Stop the UI and API (Neo4j stays up):

```bash
./stop-demo.sh
```

The API uses **port 8001** on purpose. Port 8000 is often already taken by other local apps. The UI proxies `/api` to 8001.

## First-time setup

Only needed once on a new machine:

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd ../frontend
npm install
cd ..
./start-demo.sh
```

`start-demo.sh` starts Neo4j, seeds the graph if it is empty, then starts the API and UI.

Reload demo data any time:

```bash
cd backend && source .venv/bin/activate && python scripts/seed_data.py
```

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
