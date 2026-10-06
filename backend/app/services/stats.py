from typing import Any

from app.graph import templates as T
from app.graph.session import run_read


def get_stats() -> dict[str, Any]:
    counts = run_read(T.STATS_COUNTS.strip())
    c = counts[0] if counts else {"customers": 0, "portfolios": 0, "stocks": 0, "sectors": 0}
    tv = run_read(T.STATS_TOTAL_VALUE.strip())
    total_value = float(tv[0]["total_value"]) if tv and tv[0]["total_value"] is not None else 0.0
    top_sec = run_read(T.STATS_TOP_SECTOR.strip())
    conc = run_read(T.STATS_TOP_CONCENTRATION.strip())
    ev = run_read(T.LATEST_EVENT.strip())
    latest_event = None
    if ev and ev[0].get("e"):
        node = ev[0]["e"]
        e = dict(node.items()) if hasattr(node, "items") else node
        latest_event = {
            "event_id": e.get("event_id"),
            "title": e.get("title"),
            "change_percent": e.get("change_percent"),
            "severity": e.get("severity"),
        }
    return {
        "customers": c["customers"],
        "portfolios": c["portfolios"],
        "stocks": c["stocks"],
        "sectors": c["sectors"],
        "total_market_value": round(total_value, 2),
        "top_sector": top_sec[0] if top_sec else None,
        "highest_concentration": conc[0] if conc else None,
        "latest_event": latest_event,
    }
