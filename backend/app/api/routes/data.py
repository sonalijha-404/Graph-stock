from fastapi import APIRouter, Depends

from app.api.deps import require_graph
from app.core import exceptions as exc
from app.graph.path_parser import subgraph_from_entity_records
from app.graph.session import run_read
from app.services.stats import get_stats

router = APIRouter(tags=["data"])


def _node_props(node) -> dict:
    return dict(node.items()) if node is not None else {}


@router.get("/stats")
def stats(_=Depends(require_graph)):
    return get_stats()


@router.get("/customers")
def list_customers(_=Depends(require_graph)):
    rows = run_read("MATCH (c:Customer) RETURN c ORDER BY c.name LIMIT 200")
    return [_node_props(r["c"]) for r in rows]


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


@router.get("/stocks")
def list_stocks(_=Depends(require_graph)):
    rows = run_read("MATCH (s:Stock) RETURN s ORDER BY s.symbol")
    return [_node_props(r["s"]) for r in rows]


@router.get("/stocks/{symbol}")
def get_stock(symbol: str, _=Depends(require_graph)):
    rows = run_read("MATCH (s:Stock {symbol: $sym}) RETURN s", {"sym": symbol.upper()})
    if not rows:
        raise exc.not_found(f"Stock {symbol} not found.")
    return _node_props(rows[0]["s"])


@router.get("/sectors")
def list_sectors(_=Depends(require_graph)):
    rows = run_read("MATCH (s:Sector) RETURN s ORDER BY s.name")
    return [_node_props(r["s"]) for r in rows]


@router.get("/events")
def list_events(_=Depends(require_graph)):
    rows = run_read("MATCH (e:MarketEvent) RETURN e ORDER BY e.timestamp DESC LIMIT 20")
    return [_node_props(r["e"]) for r in rows]


@router.get("/graph/customer/{customer_id}")
def graph_customer(customer_id: str, depth: int = 1, _=Depends(require_graph)):
    depth = min(max(depth, 1), 2)
    if depth == 1:
        cypher = """
        MATCH (c:Customer {customer_id: $customer_id})
        MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        RETURN c, p, h, s, sec
        LIMIT 80
        """
    else:
        cypher = """
        MATCH (c:Customer {customer_id: $customer_id})
        MATCH (c)-[:OWNS]->(p:Portfolio)-[:HAS_HOLDING]->(h:Holding)-[:HOLDS]->(s:Stock)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        OPTIONAL MATCH (s)-[:LISTED_ON]->(ex:Exchange)
        RETURN c, p, h, s, sec, ex
        LIMIT 80
        """
    rows = run_read(cypher, {"customer_id": customer_id})
    if not rows:
        raise exc.not_found(f"Customer {customer_id} not found.")
    return subgraph_from_entity_records(rows)


@router.get("/graph/stock/{symbol}")
def graph_stock(symbol: str, depth: int = 1, _=Depends(require_graph)):
    _ = depth
    rows = run_read(
        """
        MATCH (s:Stock {symbol: $symbol})<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
        OPTIONAL MATCH (s)-[:BELONGS_TO]->(sec:Sector)
        RETURN c, p, h, s, sec
        LIMIT 80
        """,
        {"symbol": symbol.upper()},
    )
    if not rows:
        raise exc.not_found(f"Stock {symbol} not found.")
    return subgraph_from_entity_records(rows)


@router.get("/graph/sector/{name}")
def graph_sector(name: str, depth: int = 1, _=Depends(require_graph)):
    _ = depth
    rows = run_read(
        """
        MATCH (sec:Sector {name: $sector})<-[:BELONGS_TO]-(s:Stock)<-[:HOLDS]-(h:Holding)<-[:HAS_HOLDING]-(p:Portfolio)<-[:OWNS]-(c:Customer)
        RETURN c, p, h, s, sec
        LIMIT 80
        """,
        {"sector": name},
    )
    if not rows:
        raise exc.not_found(f"Sector {name} not found.")
    return subgraph_from_entity_records(rows)
