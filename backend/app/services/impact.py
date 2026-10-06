from dataclasses import dataclass
from typing import Any

from app.schemas.chat import CalculationTrace


@dataclass
class HoldingRow:
    customer_id: str
    customer_name: str
    portfolio_id: str
    portfolio_name: str
    holding_id: str
    symbol: str
    quantity: int
    current_price: float
    sector: str | None


def position_value(quantity: int, price: float) -> float:
    return quantity * price


def impact_value(quantity: int, price: float, change_percent: float) -> float:
    pv = position_value(quantity, price)
    return pv * (change_percent / 100.0)


def _props(node: Any) -> dict[str, Any] | None:
    if node is None:
        return None
    if hasattr(node, "items"):
        return dict(node.items())
    if isinstance(node, dict):
        return node
    return None


def rows_from_neo4j(records: list[dict[str, Any]]) -> list[HoldingRow]:
    rows: list[HoldingRow] = []
    seen: set[str] = set()
    for rec in records:
        c = _props(rec.get("c"))
        p = _props(rec.get("p"))
        h = _props(rec.get("h"))
        s = _props(rec.get("s"))
        sec = _props(rec.get("sec"))
        if not all([c, p, h, s]):
            continue
        hid = h.get("holding_id")
        if hid in seen:
            continue
        seen.add(hid)
        sector_name = sec.get("name") if sec else None
        rows.append(
            HoldingRow(
                customer_id=c["customer_id"],
                customer_name=c["name"],
                portfolio_id=p["portfolio_id"],
                portfolio_name=p["name"],
                holding_id=hid,
                symbol=s["symbol"],
                quantity=int(h["quantity"]),
                current_price=float(s["current_price"]),
                sector=sector_name,
            )
        )
    return rows


def stock_impact(rows: list[HoldingRow], symbol: str, change_percent: float) -> tuple[list[dict], list[CalculationTrace]]:
    matching = [r for r in rows if r.symbol == symbol]
    calcs: list[CalculationTrace] = []
    by_customer: dict[str, dict] = {}
    for r in matching:
        val = impact_value(r.quantity, r.current_price, change_percent)
        expr = f"{r.quantity} × {int(r.current_price)} × {change_percent / 100:.2f}"
        calcs.append(
            CalculationTrace(
                label=f"{r.customer_name} / {r.portfolio_id} / {r.symbol}",
                expression=expr,
                value=val,
            )
        )
        if r.customer_id not in by_customer:
            by_customer[r.customer_id] = {
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "estimated_impact": 0.0,
                "holdings": [],
            }
        by_customer[r.customer_id]["estimated_impact"] += val
        by_customer[r.customer_id]["holdings"].append(
            {"portfolio_id": r.portfolio_id, "symbol": r.symbol, "impact": val}
        )
    results = sorted(by_customer.values(), key=lambda x: x["estimated_impact"])
    return results, calcs


def sector_exposure_for_customer(rows: list[HoldingRow], sector: str, min_percent: float) -> list[dict]:
    by_customer: dict[str, dict] = {}
    for r in rows:
        if r.sector != sector:
            continue
        cid = r.customer_id
        if cid not in by_customer:
            by_customer[cid] = {
                "customer_id": cid,
                "customer_name": r.customer_name,
                "sector_value": 0.0,
                "total_value": 0.0,
                "portfolios": {},
            }
        pv = position_value(r.quantity, r.current_price)
        by_customer[cid]["sector_value"] += pv
        by_customer[cid]["portfolios"].setdefault(r.portfolio_id, {"portfolio_id": r.portfolio_id, "value": 0.0, "sector_value": 0.0})
        by_customer[cid]["portfolios"][r.portfolio_id]["sector_value"] += pv

    all_rows = rows_from_customer_totals(by_customer.keys(), rows)
    for cid, data in by_customer.items():
        total = all_rows.get(cid, 0.0)
        data["total_value"] = total
        if total > 0:
            data["sector_exposure_percent"] = data["sector_value"] / total * 100.0
        else:
            data["sector_exposure_percent"] = 0.0
        for pid, pdata in data["portfolios"].items():
            ptotal = portfolio_total(rows, cid, pid)
            pdata["exposure_percent"] = (pdata["sector_value"] / ptotal * 100.0) if ptotal else 0.0

    out = [v for v in by_customer.values() if v["sector_exposure_percent"] >= min_percent]
    out.sort(key=lambda x: -x["sector_exposure_percent"])
    return out


def rows_from_customer_totals(customer_ids: set[str] | list[str], rows: list[HoldingRow]) -> dict[str, float]:
    totals: dict[str, float] = {cid: 0.0 for cid in customer_ids}
    seen: set[tuple[str, str]] = set()
    for r in rows:
        key = (r.customer_id, r.holding_id)
        if key in seen:
            continue
        if r.customer_id in totals:
            seen.add(key)
            totals[r.customer_id] += position_value(r.quantity, r.current_price)
    return totals


def portfolio_total(all_rows: list[HoldingRow], customer_id: str, portfolio_id: str) -> float:
    total = 0.0
    seen: set[str] = set()
    for r in all_rows:
        if r.customer_id == customer_id and r.portfolio_id == portfolio_id and r.holding_id not in seen:
            seen.add(r.holding_id)
            total += position_value(r.quantity, r.current_price)
    return total


def sector_impact(rows: list[HoldingRow], sector: str, change_percent: float) -> tuple[list[dict], list[CalculationTrace]]:
    matching = [r for r in rows if r.sector == sector]
    calcs: list[CalculationTrace] = []
    by_customer: dict[str, dict] = {}
    for r in matching:
        val = impact_value(r.quantity, r.current_price, change_percent)
        expr = f"{r.quantity} × {int(r.current_price)} × {change_percent / 100:.2f}"
        calcs.append(
            CalculationTrace(
                label=f"{r.customer_name} / {r.portfolio_id} / {r.symbol}",
                expression=expr,
                value=val,
            )
        )
        if r.customer_id not in by_customer:
            by_customer[r.customer_id] = {
                "customer_id": r.customer_id,
                "customer_name": r.customer_name,
                "estimated_impact": 0.0,
            }
        by_customer[r.customer_id]["estimated_impact"] += val
    results = sorted(by_customer.values(), key=lambda x: x["estimated_impact"])
    return results, calcs


def customer_exposure_summary(rows: list[HoldingRow]) -> dict[str, Any]:
    if not rows:
        return {}
    c = rows[0]
    by_sector: dict[str, float] = {}
    total = 0.0
    seen: set[str] = set()
    for r in rows:
        if r.holding_id in seen:
            continue
        seen.add(r.holding_id)
        pv = position_value(r.quantity, r.current_price)
        total += pv
        sec = r.sector or "Unknown"
        by_sector[sec] = by_sector.get(sec, 0.0) + pv
    sectors = [
        {"sector": k, "value": v, "percent": (v / total * 100.0) if total else 0.0}
        for k, v in sorted(by_sector.items(), key=lambda x: -x[1])
    ]
    return {
        "customer_id": c.customer_id,
        "customer_name": c.customer_name,
        "total_value": total,
        "sectors": sectors,
    }
