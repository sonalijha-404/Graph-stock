# Progress log

## Phase 0–12 — MVP implementation

Phase: 0–12 (combined delivery)  
Status: complete (pending local verification)  
Implemented:

- Docker Neo4j, FastAPI backend, React frontend
- Schema constraints, seed script with Rahul/Priya fixtures
- Catalog intents, rule router, optional LLM classifier
- Impact engine, chat + impact simulate APIs
- Dashboard, Ask, Graph, How it works screens

Files changed: backend/, frontend/, docker-compose.yml, README.md  

Tests: `backend/tests/test_impact.py`, `test_router.py`  

Known issues: Run `docker compose up -d neo4j` and `python scripts/seed_data.py` before API tests against live graph.  

Next phase: optional polish and LLM eval when API keys are configured.
