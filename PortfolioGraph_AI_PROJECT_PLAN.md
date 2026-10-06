# PortfolioGraph AI — Graph-Based Stock Portfolio Impact Analysis

## 1. Purpose

**PortfolioGraph AI** is a graph-powered portfolio intelligence demo.

A user asks a plain-language question about customer stock holdings. The system traverses a real graph of customers, portfolios, holdings, stocks, and sectors, calculates exposure in ordinary Python, and shows both the answer and the path that produced it.

The project demonstrates two things together:

- A graph database is a good fit for multi-hop portfolio questions.
- A language model is a good interface to that graph, and a bad place to do arithmetic.

This is an analytical demo. It is not a trading platform.

---

## 2. Non-goals

The MVP does not include:

- Investment advice, trade recommendations, price forecasts, or return guarantees
- Live market data
- User accounts, authentication, or multiple tenants
- Saved chat history
- Free-form Cypher written by the model and executed directly
- News ingestion, graph algorithms, embeddings, or a vector database
- Production deployment, high availability, or performance tuning beyond indexes and query limits

If a feature is not required by the demo script in section 4, do not build it in the MVP.

---

## 3. What the demo must prove

### Graph modelling

Relationships are first-class. A holding is not a column on a customer, and a sector is not only a string on a stock.

### Multi-hop traversal

The system answers questions by walking paths such as:

```text
Customer → Portfolio → Holding → Stock → Sector
```

and the reverse:

```text
Sector → Stock → Holding → Portfolio → Customer
```

### A natural-language interface over safe queries

The language model identifies intent and entities. The backend runs a known, parameterized Cypher template. The model never becomes the query engine.

### Deterministic impact math

Estimated loss and sector exposure are computed in Python from quantities and prices stored in the graph. The same inputs always produce the same numbers.

### Visible reasoning

Every demo answer shows the intent, the entities, the Cypher that ran, the subgraph that matched, the calculation, and the time taken. The graph view highlights that same subgraph.

---

## 4. Demo script

This script is the acceptance test for the finished MVP. Seed data and APIs must make every step true.

1. Open the dashboard. It shows live counts, total market value, and a small graph preview. Numbers come from Neo4j.
2. Ask: **"Who owns TCS?"** The answer lists customers, including Rahul Sharma, and the explorer highlights Stock → Holding → Portfolio → Customer.
3. Ask: **"Who owns both TCS and Infosys?"** Rahul Sharma is included. This is an intersection, not a single lookup.
4. Ask: **"Who is highly exposed to IT?"** Customers are ranked by sector exposure. Rahul Sharma's primary portfolio is exactly **75%** IT.
5. Ask: **"What happens if TCS drops 10%?"** Rahul Sharma's estimated unrealized impact is exactly **₹40,000**. The calculation panel shows the arithmetic.
6. Ask: **"What happens if the IT sector drops 10%?"** The path runs from the sector through its stocks, holdings, portfolios, and customers.
7. Open **How it works**. The pipeline diagram highlights the stages that actually ran for the last question.

Every answer uses this wording family: estimated exposure, estimated unrealized impact, potentially affected customers. The UI labels all figures as synthetic.

---

## 5. Scope

### MVP screens

Four screens are enough:

| Screen | Job |
| --- | --- |
| Dashboard | Counts, value, concentration, scenario buttons, graph preview |
| Ask | Question, structured answer, explainability, link to the highlighted path |
| Graph | Search, expand, inspect, filter, highlight the last answer |
| How it works | Pipeline diagram. Nodes explain themselves. The last query lights the stages that ran |

Customer, portfolio, and event detail are drill-ins from the dashboard and the graph. They are not separate top-level products.

### Build order

Each phase ends with something runnable. Do not start a later phase because it is described here.

Visual polish waits until the demo script works.

---

## 6. Architecture

```text
User
  ↓
React UI
  Dashboard / Ask / Graph / How it works
  ↓ HTTP
FastAPI
  ├── Intent router      rule-based first, LLM classifier later
  ├── Query catalog      one parameterized Cypher template per intent
  ├── Impact engine      Python only
  └── Explanation        assembled from real execution, not invented
  ↓
Neo4j
  Customer → Portfolio → Holding → Stock → Sector
                         MarketEvent → Sector or Stock
```

Three responsibilities stay separate.

| Layer | Owns | Must not own |
| --- | --- | --- |
| Neo4j | Nodes, relationships, traversal | Impact formulas, answer prose |
| FastAPI | Validation, templates, arithmetic, API shape | Guessing facts that are not in the graph |
| LLM | Intent and entity extraction, optional wording polish | Cypher authorship, financial arithmetic, missing facts |

Local demo only. The API binds to localhost. There is no authentication.

### Stack

- Backend: Python, FastAPI, Pydantic, official Neo4j driver
- Graph: Neo4j Community in Docker. Browser is for development only
- Frontend: React, TypeScript, Vite, Tailwind
- Data graph: Cytoscape.js
- Pipeline diagram: React Flow
- LLM: any OpenAI-compatible endpoint already configured in the environment

Environment variables:

```text
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=          # local demo password, never committed
NEO4J_DATABASE=neo4j

LLM_BASE_URL=
LLM_API_KEY=
LLM_MODEL=
```

If the LLM variables are empty, the demo still runs. The rule-based router serves the demo script.

Infrastructure for the MVP:

```text
Docker Compose
  ├── neo4j        ports 7474 and 7687, named volume
  └── backend
```

The frontend runs separately in development. Compose it later only if it is needed to run the demo on one machine.

---

## 7. Query strategy

This is the main design constraint.

Supported questions map to a fixed intent. Each intent has one Cypher template stored in the backend. The template receives parameters. It is not string-built from user text.

```text
Question
  ↓
Intent + entities     (rules, later an LLM)
  ↓
Template lookup
  ↓
Parameter binding
  ↓
Read-only Neo4j transaction
  ↓
Python calculation, when the intent needs it
  ↓
Answer + subgraph + calculation trace
```

### Intents

| Intent | Example | Parameters |
| --- | --- | --- |
| `STOCK_HOLDERS` | Who owns TCS? | `symbol` |
| `MULTI_STOCK_HOLDERS` | Who owns both TCS and Infosys? | `symbols[]` |
| `SECTOR_EXPOSURE` | Who is highly exposed to IT? | `sector`, `min_percent` |
| `STOCK_IMPACT` | What if TCS drops 10%? | `symbol`, `change_percent` |
| `SECTOR_IMPACT` | What if IT drops 10%? | `sector`, `change_percent` |
| `CUSTOMER_EXPOSURE` | Explain Rahul Sharma's exposure | `customer_id` or exact name |
| `UNKNOWN` | Anything else | none |

`min_percent` defaults to **40**. A customer or portfolio at or above that threshold is "highly exposed" in this demo. Say the threshold in the answer.

### LLM contract

When the LLM is enabled, its only structured output is:

```json
{
  "intent": "STOCK_IMPACT",
  "entities": {
    "symbol": "TCS",
    "symbols": [],
    "sector": null,
    "change_percent": -10,
    "customer_name": null
  }
}
```

The prompt includes the intent list, the stock symbols, the sector names, and the customer names currently in the graph. The model must choose from those values. If it cannot, the intent is `UNKNOWN`.

The backend checks the JSON against the schema, checks that symbols and sectors exist, and only then runs a template. A failure at this step does not execute a query.

Do not add a free-form text-to-Cypher path in the MVP. Showing the template that ran is already a clear explanation of the query.

### Rule router

Ship a small rule router before the LLM exists. It must understand the demo-script phrasings and obvious variants ("which customers hold TCS", "TCS falls 10 percent"). The LLM replaces classification only. Templates stay. If the LLM is down or fails validation, the router is the fallback. If both fail, return `UNKNOWN`.

---

## 8. Graph model

Start with this model and do not add node labels until a demo query needs them.

### Nodes

**Customer**

- `customer_id` unique
- `name`
- `risk_profile` one of Conservative, Moderate, Aggressive
- `country`

**Portfolio**

- `portfolio_id` unique
- `name`
- `portfolio_type` one of Growth, Income, Balanced

**Holding** — the position, not the stock

- `holding_id` unique
- `quantity` integer, greater than 0
- `average_buy_price` number, for display only

**Stock**

- `symbol` unique
- `company_name`
- `current_price` number, INR per share

**Sector**

- `name` unique

**Exchange**

- `exchange_id` unique
- `name`

One exchange is enough: NSE. Every stock is listed there. This keeps `LISTED_ON` real without an exchange feature.

**MarketEvent**

- `event_id` unique
- `title`
- `event_type`
- `severity` one of low, medium, high
- `change_percent` number
- `timestamp` ISO-8601 string

### Relationships

```text
(:Customer)-[:OWNS]->(:Portfolio)
(:Portfolio)-[:HAS_HOLDING]->(:Holding)
(:Holding)-[:HOLDS]->(:Stock)
(:Stock)-[:BELONGS_TO]->(:Sector)
(:Stock)-[:LISTED_ON]->(:Exchange)
(:MarketEvent)-[:AFFECTS]->(:Sector)
(:MarketEvent)-[:AFFECTS]->(:Stock)
```

A stock's sector is the `BELONGS_TO` relationship only. Do not also store a sector string on the stock.

### Why Holding is a node

```text
Customer → Portfolio → Holding → Stock
```

Quantity belongs to the position. The same stock is held in many portfolios. Collapsing this to `Customer -[:OWNS]-> Stock` removes the portfolio hop and leaves nowhere honest to put quantity.

### Values that are computed, not stored

Do not store `allocation_percentage` or `portfolio.total_value` as facts. They go stale as soon as a price or quantity changes.

Every read path computes:

```text
position_value = quantity × stock.current_price
portfolio_value = sum of its position values
customer_value = sum of its portfolio values
```

`average_buy_price` is not used in impact math. Impact is mark-to-market from `current_price`.

### Constraints

Create these before loading data:

```cypher
CREATE CONSTRAINT customer_id_unique IF NOT EXISTS
FOR (c:Customer) REQUIRE c.customer_id IS UNIQUE;

CREATE CONSTRAINT portfolio_id_unique IF NOT EXISTS
FOR (p:Portfolio) REQUIRE p.portfolio_id IS UNIQUE;

CREATE CONSTRAINT holding_id_unique IF NOT EXISTS
FOR (h:Holding) REQUIRE h.holding_id IS UNIQUE;

CREATE CONSTRAINT stock_symbol_unique IF NOT EXISTS
FOR (s:Stock) REQUIRE s.symbol IS UNIQUE;

CREATE CONSTRAINT sector_name_unique IF NOT EXISTS
FOR (s:Sector) REQUIRE s.name IS UNIQUE;

CREATE CONSTRAINT exchange_id_unique IF NOT EXISTS
FOR (e:Exchange) REQUIRE e.exchange_id IS UNIQUE;

CREATE CONSTRAINT event_id_unique IF NOT EXISTS
FOR (e:MarketEvent) REQUIRE e.event_id IS UNIQUE;
```

### Out of the MVP graph

News, `COMPETES_WITH`, `SUPPLIES_TO`, and a separate RiskProfile node. Add one only when a demo sentence requires it.

---

## 9. Impact calculations

Currency is INR. Prices and results are synthetic.

### Position value

```text
position_value = quantity × current_price
```

### Estimated unrealized impact of a percent move

```text
impact = position_value × (change_percent / 100)
```

A −10% move on a ₹400,000 position is ₹−40,000. The sign is kept. The UI may say "estimated decline of ₹40,000" when the number is negative.

Customer impact is the sum of that customer's matching positions, across every portfolio. Portfolio impact is the sum inside one portfolio. Also return the parent totals so the UI can show rank and share of value.

### Sector exposure

```text
sector_exposure_percent = sector_position_value / portfolio_value × 100
```

For a customer with several portfolios, use customer totals, not an average of portfolio percentages.

### Sector shock

A sector percent move applies the same `change_percent` to every stock in that sector. It does not also apply a second shock to those stocks. Impact is the sum of the stock-level impacts.

### Worked fixture

These rows are exact. Tests assert them.

Rahul Sharma, `C001`, portfolio `P001` "Rahul Growth":

| Symbol | Quantity | Price (INR) | Position value |
| --- | ---: | ---: | ---: |
| TCS | 100 | 4000 | 400,000 |
| INFY | 100 | 2000 | 200,000 |
| HDFCBANK | 100 | 2000 | 200,000 |

- Portfolio value = **800,000**
- IT value = **600,000**
- IT exposure = **75%**
- TCS −10% impact = **−40,000**

Priya Nair, `C002`, proves a customer total across two portfolios.

| Portfolio | Symbol | Quantity | Price | Position value |
| --- | --- | ---: | ---: | ---: |
| P010 | TCS | 10 | 4000 | 40,000 |
| P010 | SBIN | 10 | 800 | 8,000 |
| P011 | SUNPHARMA | 10 | 1500 | 15,000 |

- Priya's TCS −10% impact = **−4,000**
- Her customer value = **63,000**

No other holding of TCS for these two customers may exist. Other customers may also hold TCS.

Rounding: money is rounded to 2 decimal places only at the API boundary. Tests for these fixtures use exact integers.

---

## 10. Synthetic dataset

The database is dedicated to this demo. The seed script may delete all nodes and relationships, then reload. It must be safe to run twice and end at the same counts and the same fixture numbers.

### Shape

| Thing | Target |
| --- | --- |
| Customers | 50, including C001 and C002 |
| Portfolios | 75 |
| Stocks | 24 to 30 |
| Sectors | 8 |
| Holdings | 150 to 200, including the fixture rows |
| Market events | 5 |
| Exchanges | 1 (NSE) |

Sectors: IT, Banking, Financial Services, Pharma, Automobile, Energy, FMCG, Telecommunications.

Named stocks must include TCS, INFY, WIPRO, HCLTECH, HDFCBANK, ICICIBANK, SBIN, SUNPHARMA, RELIANCE, ITC, BHARTIARTL. Hero prices are fixed:

```text
TCS 4000, INFY 2000, HDFCBANK 2000, SBIN 800, SUNPHARMA 1500
```

Other prices come from a fixed price table in the seed script, not from an unseeded random draw.

### Guarantees beyond the worked fixture

The generator must force these outcomes after random fill, overwriting collisions if needed:

- At least 6 customers hold TCS
- At least 3 customers hold both TCS and INFY, including Rahul
- At least 1 customer holds no IT stock
- At least 1 portfolio has a single stock above 50% of its value
- One event, `E001`, title "IT sector weakness", `AFFECTS` the IT sector, `change_percent` −10

Use `random.Random(42)` only for the non-fixture portion. Names must be clearly synthetic. The UI must not present them as live market data.

---

## 11. API

JSON only. Lists in this demo are small enough to return whole. Graph responses are not.

### Error body

```json
{
  "error": {
    "code": "GRAPH_UNAVAILABLE",
    "message": "Graph database unavailable. Check the database connection."
  }
}
```

Codes: `GRAPH_UNAVAILABLE`, `NOT_FOUND`, `VALIDATION_FAILED`, `UNSUPPORTED`, `NO_RESULTS`, `LLM_UNAVAILABLE`.

`LLM_UNAVAILABLE` is internal. The API uses the rule router instead of failing the request, unless the router also cannot classify.

### Endpoints

```http
GET  /health
GET  /stats
GET  /customers
GET  /customers/{customer_id}
GET  /portfolios/{portfolio_id}
GET  /stocks
GET  /stocks/{symbol}
GET  /sectors
GET  /events

GET  /graph/customer/{customer_id}?depth=1
GET  /graph/stock/{symbol}?depth=1
GET  /graph/sector/{name}?depth=1

POST /chat
POST /impact/simulate
```

`depth` is 1 by default and 2 at most. Every graph payload is capped at **80 nodes**. If the natural neighborhood is larger, truncate and set `truncated: true`. The UI says the view is partial and asks the user to expand or filter.

`GET /health` checks the process and a `RETURN 1` query. It returns 503 when Neo4j is down.

`GET /stats` returns customer count, portfolio count, stock count, sector count, total market value, the sector with the largest total position value, the portfolio with the highest single-stock concentration, and the latest event.

### Chat request

```json
{
  "question": "What happens if TCS drops 10%?"
}
```

Stateless. No conversation id.

### Chat response

```json
{
  "answer": "TCS exposure was found in 7 portfolios belonging to 6 customers. The largest estimated decline is Rahul Sharma at ₹40,000.",
  "intent": "STOCK_IMPACT",
  "entities": {
    "symbol": "TCS",
    "change_percent": -10
  },
  "cypher": "MATCH (s:Stock {symbol: $symbol}) ...",
  "parameters": { "symbol": "TCS" },
  "subgraph": {
    "nodes": [],
    "edges": [],
    "truncated": false
  },
  "results": [],
  "calculations": [
    {
      "label": "Rahul Sharma / P001 / TCS",
      "expression": "100 × 4000 × -0.10",
      "value": -40000
    }
  ],
  "stages": ["intent", "template", "neo4j", "impact", "answer"],
  "execution_ms": {
    "neo4j": 12,
    "calculation": 1,
    "total": 20
  },
  "disclaimer": "Synthetic data. Estimated exposure only. Not investment advice."
}
```

`subgraph.nodes` and `subgraph.edges` use stable ids that the explorer can highlight. A list of labels such as `["Stock", "Holding"]` is not enough.

`stages` lists stages that actually ran. The How it works page highlights those and no others.

`POST /impact/simulate` accepts:

```json
{ "scope": "stock", "symbol": "TCS", "change_percent": -10 }
```

or:

```json
{ "scope": "sector", "sector": "IT", "change_percent": -10 }
```

It uses the same impact functions as chat. Event buttons call this with the event's sector or stock and `change_percent`. There is one calculation path.

### Graph payload

```json
{
  "nodes": [
    { "id": "stock:TCS", "type": "Stock", "label": "TCS", "properties": {} }
  ],
  "edges": [
    { "id": "holding:H1-HOLDS-stock:TCS", "type": "HOLDS", "source": "holding:H1", "target": "stock:TCS" }
  ],
  "truncated": false
}
```

Node `type` is one of Customer, Portfolio, Holding, Stock, Sector, Exchange, MarketEvent.

---

## 12. Safety

### Query execution

Chat and impact routes run only catalog templates, inside a read transaction, with a server-side timeout of 5 seconds and a `LIMIT` inside every template that returns rows.

User text is never concatenated into Cypher. Identifiers from the model are parameters, and they are accepted only if they match a known symbol, sector, or customer.

Rejected even if a later experiment generates Cypher: multiple statements, and any use of `CREATE`, `MERGE`, `DELETE`, `DETACH`, `SET`, `REMOVE`, `DROP`, `LOAD CSV`, `CALL`, `FOREACH`, or `APOC`. The MVP does not need that experiment.

### Financial language

Allowed: estimated exposure, estimated unrealized impact, potentially affected.

Not allowed: buy, sell, safe, guaranteed, will fall, will rise, recommendation.

The disclaimer string in the chat contract is shown on every answer.

### Honest empty states

| Situation | Behavior |
| --- | --- |
| Neo4j down | `GRAPH_UNAVAILABLE`. No invented numbers |
| Question not in the catalog | `UNSUPPORTED`. Say the graph cannot answer that |
| Query matches nothing | `NO_RESULTS`. Say no matching relationships were found |
| Generated entity not in the graph | Do not run the template. Same as unsupported |
| LLM down | Rule router, then unsupported |

---

## 13. UI

The product should feel like a calm internal research dashboard. Dense enough to look serious, quiet enough that the graph path is the focus.

### Layout

```text
┌──────────────────────────────────────────────────────────┐
│ PortfolioGraph AI                      Synthetic · Neo4j │
├────────────┬─────────────────────────────────────────────┤
│ Dashboard  │                                             │
│ Ask        │              Current screen                 │
│ Graph      │                                             │
│ How it     │                                             │
│ works      │                                             │
├────────────┴─────────────────────────────────────────────┤
│ Health · last query time · database                      │
└──────────────────────────────────────────────────────────┘
```

The header always shows that figures are synthetic.

### Dashboard

Cards from `GET /stats`: customers, portfolios, stocks, sectors, total market value, top sector, highest concentration, latest event.

A graph preview shows a bounded subgraph, not the full database.

Scenario buttons run the demo script through the same `POST /chat` or `POST /impact/simulate` path and then open Ask with the result:

- Who owns TCS
- Who owns TCS and Infosys
- IT exposure
- TCS −10%
- IT sector −10%
- Explain Rahul Sharma

### Ask

The answer is a short paragraph plus result rows. It is not a long essay.

Tabs on the answer, fed only by the response JSON:

- Answer
- Graph path
- Cypher
- Calculation
- Execution

"Graph path" links to the Graph screen with the returned subgraph highlighted.

### Graph

- Search customer, stock, or sector
- Expand neighbors one hop
- Click a node to see properties
- Filter by node type
- Zoom, pan, reset
- Mute nodes that are not in the active answer subgraph
- Never draw the full 150-holding graph at once

Visual types stay stable:

```text
Customer, Portfolio, Holding, Stock, Sector, Event
```

Relationship labels show when the visible edge count is small enough to read. Above that, show labels on hover or selection.

### How it works

A React Flow diagram:

```text
Question → Intent → Template → Neo4j → Impact → Answer
```

Each node has a short explanation. Impact's explanation states that Python does the arithmetic. After a query, only `stages` from the last response are highlighted.

### States the UI must design

- Loading
- Neo4j unavailable
- Unsupported question
- No results
- Truncated graph
- LLM fallback in use, without alarming the user; the answer is still from the graph

---

## 14. Implementation phases

Each phase has one checkpoint. Write the checkpoint result into `docs/progress.md` before starting the next phase:

```text
Phase:
Status:
Implemented:
Files changed:
Tests:
Known issues:
Next phase:
```

Tests that belong to a phase are part of that phase, not a later cleanup.

### Phase 0 — Foundation

Repository, README, `.gitignore`, `.env.example`, backend package, frontend shell, Docker Compose for Neo4j.

Checkpoint: frontend loads, `GET /health` returns the process status, Neo4j is up. Health may report the database as down until Phase 1, and the README says so.

### Phase 1 — Connection

Neo4j driver, settings, startup and shutdown, health query `RETURN 1`, clear error when the database is unreachable.

Checkpoint: with Neo4j running, health is ok. With Neo4j stopped, health is 503 and the process stays up.

### Phase 2 — Schema

Constraints from section 8. No sample business data yet.

Checkpoint: constraints exist and a second run of the schema script does not fail.

### Phase 3 — Seed

Fixture rows first, generated rows second, guarantees from section 10 enforced in code.

Checkpoint:

- Counts match the target bands
- Rahul's three positions, portfolio value 800,000, and IT exposure 75% match section 9
- Priya's TCS impact input matches section 9
- Running the seed twice does not duplicate nodes

### Phase 4 — Templates and read APIs

Implement `STOCK_HOLDERS`, `MULTI_STOCK_HOLDERS`, `CUSTOMER_EXPOSURE`, stats, and the bounded graph endpoints. No LLM.

Checkpoint: HTTP calls return Rahul for TCS holders and for TCS+INFY. Graph payloads stay within 80 nodes. A test hits Neo4j and the API.

### Phase 5 — Graph screen

Explorer over the real graph endpoints. Search, expand, inspect, filter, reset.

Checkpoint: searching Rahul shows Customer → Portfolio → Holding → Stock → Sector for his fixture, and the picture matches the API payload.

### Phase 6 — Dashboard

Stats cards and preview from the API. No hardcoded metrics.

Checkpoint: card values change if the seed changes, and they match `GET /stats`.

### Phase 7 — Ask, without an LLM

Rule router, chat UI, response contract, explainability tabs. Intents that do not need impact can return empty `calculations`.

Checkpoint: the three non-impact demo questions work from the chat box and from the scenario buttons. An unsupported question does not query Neo4j with invented Cypher.

### Phase 8 — Impact engine

`STOCK_IMPACT`, `SECTOR_EXPOSURE`, and `POST /impact/simulate` for a single stock. Shared Python functions. Calculation traces in the response.

Checkpoint: automated tests assert Rahul −40,000 and Priya −4,000 for TCS −10%, and Rahul 75% IT exposure. The Ask calculation tab shows the expression.

### Phase 9 — Sector shock and events

`SECTOR_IMPACT`. Events list on the dashboard. `E001` runs a −10% IT shock through the same function.

Checkpoint: the IT −10% total equals the sum of −10% impacts of IT stocks, with no double counting. The highlighted path includes the sector.

### Phase 10 — LLM classifier

Structured intent extraction only. Prompt built from live symbols, sectors, and customer names. Router remains the fallback.

Eval file: `backend/tests/fixtures/questions.jsonl`, at least 20 questions, with expected intent and entities. Include paraphrases of each demo question and at least 4 unsupported questions.

Checkpoint: at least 18 of 20 classifications are correct on one run. Unsupported questions stay unsupported. Entity values that are not in the graph do not execute. If the bar is missed, the demo still ships on the rule router and the gap is written in `docs/progress.md`.

### Phase 11 — How it works

Pipeline diagram bound to `stages` on the last real response.

Checkpoint: a stock-holder question does not light the Impact stage. A TCS −10% question does.

### Phase 12 — Finish the script

Wire every scenario button. Loading, empty, error, and truncated-graph states. Responsive layout good enough for a laptop demo. README with setup, seed, test, and the demo script.

Checkpoint: a person can follow section 4 from a cold start using the README and hit every expected number.

---

## 15. Repository

```text
portfolio-graph-ai/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── graph/          schema, templates, session
│   │   ├── services/       impact, explanation
│   │   ├── llm/
│   │   └── main.py
│   ├── scripts/
│   │   └── seed_data.py
│   └── tests/
│       └── fixtures/questions.jsonl
├── frontend/
│   └── src/
│       ├── pages/
│       ├── graph/
│       ├── chat/
│       └── flow/
├── docs/
│   └── progress.md
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 16. Rules for implementation

1. One phase at a time. The app stays runnable between phases.
2. Do not invent graph results, counts, or animation stages.
3. Financial math lives in Python and is covered by the fixture tests.
4. Chat runs catalog templates only.
5. Visuals show the subgraph and stages returned by the API.
6. Do not add a node, screen, or dependency the current phase does not need.
7. Preserve working behavior when extending it.
8. Update `docs/progress.md` at every checkpoint.

---

## 17. Definition of done

- Cold start is documented and works
- Schema, seed, and fixture numbers match this plan
- The section 4 script succeeds on real queries
- Ask shows Cypher, subgraph, calculation, and timing from the response
- Graph highlights that subgraph and does not dump the full database
- How it works highlights only stages that ran
- Impact tests cover Rahul and Priya
- The LLM eval file exists, and a miss does not weaken query safety
- No demo number is hardcoded in the frontend

---

## 18. Later, not now

Real market prices, portfolio history, rebalancing advice, news, embeddings, hybrid graph and vector search, PageRank, community detection, centrality, shortest path, and similarity.

Add one of these only when the demo script is already solid and the new piece answers a question the current graph cannot.
