from typing import Any

from app.graph.session import run_read
from app.graph import templates as T


def load_known_entities() -> dict[str, set[str]]:
    symbols = {r["symbol"] for r in run_read(T.LIST_SYMBOLS)}
    sectors = {r["name"] for r in run_read(T.LIST_SECTORS)}
    customers = run_read(T.LIST_CUSTOMERS)
    return {
        "symbols": symbols,
        "sectors": sectors,
        "customer_ids": {r["customer_id"] for r in customers},
        "customer_names": {r["name"] for r in customers},
    }
