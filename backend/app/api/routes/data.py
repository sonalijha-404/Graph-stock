from fastapi import APIRouter, Depends

from app.api.deps import require_graph
from app.core.config import settings
from app.core import exceptions as exc
from app.graph.path_parser import subgraph_from_entity_records
from app.graph.session import run_read
from app.services.stats import get_stats

router = APIRouter(tags=["data"])


def _node_props(node) -> dict:
    return dict(node.items()) if node is not None else {}


def _graph_row_limit(view: str) -> int:
    if view == "complete":
        return settings.graph_node_limit_complete
    return settings.graph_node_limit


def _normalize_view(view: str) -> str:
    return "complete" if view == "complete" else "partial"


@router.get("/stats")
def stats(_=Depends(require_graph)):
    return get_stats()


def _clean(values: list | None) -> list:
    if not values:
        return []
    return [v for v in values if v not in (None, "")]


@router.get("/customers")
def list_customers(_=Depends(require_graph)):
    rows = run_read(
        """
        MATCH (c:Customer)
        OPTIONAL MATCH (c)-[:OWNS]->(p:Portfolio)
        RETURN c.customer_id AS customer_id, c.name AS name,
               c.risk_profile AS risk_profile, c.country AS country,
               count(p) AS portfolios
        ORDER BY c.customer_id
        """
    )
    return rows


@router.get("/customers/{customer_id}")
def get_customer(customer_id: str, _=Depends(require_graph)):
    rows = run_read("MATCH (c:Customer {customer_id: $id}) RETURN c", {"id": customer_id})
    if not rows:
        raise exc.not_found(f"Customer {customer_id} not found.")
    return _node_props(rows[0]["c"])


@router.get("/portfolios/{portfolio_id}")
def get_portfolio(portfolio_id: str, _=Depends(require_graph)):
    rows = run_read(
        """
        MATCH (p:Portfolio {portfolio_id: $id})<-[:OWNS]-(c:Customer)
        OPTIONAL MATCH (p)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        RETURN p, c, h, s
        """,
        {"id": portfolio_id},
    )
    if not rows:
        raise exc.not_found(f"Portfolio {portfolio_id} not found.")
    holdings = []
    for r in rows:
        if r.get("h") and r.get("s"):
            holdings.append({"holding": _node_props(r["h"]), "stock": _node_props(r["s"])})
    return {
        "portfolio": _node_props(rows[0]["p"]),
        "customer": _node_props(rows[0]["c"]),
        "holdings": holdings,
    }


@router.get("/portfolios")
def list_portfolios(_=Depends(require_graph)):
    rows = run_read(
        """
        MATCH (c:Customer)-[:OWNS]->(p:Portfolio)
        OPTIONAL MATCH (p)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        RETURN p.portfolio_id AS portfolio_id, p.name AS name,
               p.portfolio_type AS portfolio_type,
               c.customer_id AS customer_id, c.name AS customer_name,
               collect(DISTINCT s.symbol) AS symbols,
               collect(DISTINCT sec.name) AS sectors,
               sum(h.quantity * s.current_price) AS value
        ORDER BY p.portfolio_id
        """
    )
    for row in rows:
        row["symbols"] = _clean(row.get("symbols"))
        row["sectors"] = _clean(row.get("sectors"))
        row["value"] = round(float(row["value"] or 0), 2)
    return rows


@router.get("/stocks")
def list_stocks(_=Depends(require_graph)):
    return run_read(
        """
        MATCH (s:Stock)-[:BELONGS_TO]->(sec:Sector)
        OPTIONAL MATCH (s)<-[:HOLDS]-(h:Holding)
        RETURN s.symbol AS symbol, s.company_name AS company_name,
               s.current_price AS current_price, sec.name AS sector,
               count(h) AS holders
        ORDER BY sec.name, s.symbol
        """
    )


@router.get("/stocks/{symbol}")
def get_stock(symbol: str, _=Depends(require_graph)):
    rows = run_read("MATCH (s:Stock {symbol: $sym}) RETURN s", {"sym": symbol.upper()})
    if not rows:
        raise exc.not_found(f"Stock {symbol} not found.")
    return _node_props(rows[0]["s"])


@router.get("/sectors")
def list_sectors(_=Depends(require_graph)):
    rows = run_read(
        """
        MATCH (sec:Sector)
        OPTIONAL MATCH (sec)<-[:BELONGS_TO]-(s:Stock)
        RETURN sec.name AS name, count(s) AS stocks, collect(s.symbol) AS symbols
        ORDER BY sec.name
        """
    )
    for row in rows:
        row["symbols"] = _clean(row.get("symbols"))
    return rows


@router.get("/events")
def list_events(_=Depends(require_graph)):
    rows = run_read("MATCH (e:MarketEvent) RETURN e ORDER BY e.timestamp DESC LIMIT 20")
    return [_node_props(r["e"]) for r in rows]


@router.get("/graph/customer/{customer_id}")
def graph_customer(
    customer_id: str,
    depth: int = 1,
    view: str = "partial",
    _=Depends(require_graph),
):
    view = _normalize_view(view)
    depth = min(max(depth, 1), 2)
    row_limit = _graph_row_limit(view)
    if depth == 1:
        cypher = f"""
        MATCH (c:Customer {{customer_id: $customer_id}})
        MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        RETURN c, p, h, s, sec
        LIMIT {row_limit}
        """
    else:
        cypher = f"""
        MATCH (c:Customer {{customer_id: $customer_id}})
        MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        OPTIONAL MATCH (s)-[:LISTED_ON]->(ex:Exchange)
        RETURN c, p, h, s, sec, ex
        LIMIT {row_limit}
        """
    rows = run_read(cypher, {"customer_id": customer_id})
    if not rows:
        raise exc.not_found(f"Customer {customer_id} not found.")
    return subgraph_from_entity_records(rows, node_limit=row_limit)


@router.get("/graph/stock/{symbol}")
def graph_stock(symbol: str, depth: int = 1, view: str = "partial", _=Depends(require_graph)):
    view = _normalize_view(view)
    _ = depth
    row_limit = _graph_row_limit(view)
    rows = run_read(
        f"""
        MATCH (s:Stock {{symbol: $symbol}})<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        RETURN c, p, h, s, sec
        LIMIT {row_limit}
        """,
        {"symbol": symbol.upper()},
    )
    if not rows:
        raise exc.not_found(f"Stock {symbol} not found.")
    return subgraph_from_entity_records(rows, node_limit=row_limit)


@router.get("/graph/sector/{name}")
def graph_sector(name: str, depth: int = 1, view: str = "partial", _=Depends(require_graph)):
    view = _normalize_view(view)
    _ = depth
    row_limit = _graph_row_limit(view)
    rows = run_read(
        f"""
        MATCH (sec:Sector {{name: $sector}})<-[:BELONGS_TO]-(s:Stock)<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
        RETURN c, p, h, s, sec
        LIMIT {row_limit}
        """,
        {"sector": name},
    )
    if not rows:
        raise exc.not_found(f"Sector {name} not found.")
    return subgraph_from_entity_records(rows, node_limit=row_limit)
