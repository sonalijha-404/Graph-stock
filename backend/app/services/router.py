import re
from typing import Any

from app.core.config import settings

STOCK_SYMBOLS = {
    "TCS", "INFY", "INFOSYS", "WIPRO", "HCLTECH", "HDFCBANK", "ICICIBANK", "SBIN",
    "SUNPHARMA", "RELIANCE", "ITC", "BHARTIARTL",
}

SYMBOL_ALIASES = {"INFOSYS": "INFY"}


def normalize_symbol(token: str) -> str | None:
    t = token.upper().strip()
    if t in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[t]
    if t in STOCK_SYMBOLS and t != "INFOSYS":
        return t
    return None


def extract_percent(text: str) -> float | None:
    m = re.search(r"(-?\d+(?:\.\d+)?)\s*(?:%|percent)", text, re.I)
    if m:
        val = float(m.group(1))
        if val > 0 and re.search(r"drop|fall|declin|down", text, re.I):
            val = -val
        return val
    m = re.search(r"(?:drops?|falls?|declines?|down)\s*(?:by\s*)?(-?\d+(?:\.\d+)?)", text, re.I)
    if m:
        val = float(m.group(1))
        return -abs(val)
    return None


def extract_sector(text: str) -> str | None:
    sectors = ["IT", "Banking", "Financial Services", "Pharma", "Automobile", "Energy", "FMCG", "Telecommunications"]
    lower = text.lower()
    for s in sectors:
        if s.lower() in lower or (s == "IT" and re.search(r"\bit\b", lower)):
            return s
    return None


def extract_symbols(text: str) -> list[str]:
    found: list[str] = []
    upper = text.upper()
    for sym in ["TCS", "INFY", "INFOSYS", "WIPRO", "HCLTECH", "HDFCBANK", "ICICIBANK", "SBIN", "SUNPHARMA", "RELIANCE", "ITC", "BHARTIARTL"]:
        if sym in upper or sym.lower() in text.lower():
            norm = normalize_symbol(sym)
            if norm and norm not in found:
                found.append(norm)
    return found


def extract_customer_name(text: str) -> str | None:
    m = re.search(r"rahul\s+sharma", text, re.I)
    if m:
        return "Rahul Sharma"
    m = re.search(r"priya\s+nair", text, re.I)
    if m:
        return "Priya Nair"
    m = re.search(r"explain\s+(.+?)(?:'s|\s+exposure|$)", text, re.I)
    if m:
        return m.group(1).strip().title()
    return None


def classify(question: str, known_symbols: set[str] | None = None, known_sectors: set[str] | None = None) -> tuple[str, dict[str, Any]]:
    q = question.strip()
    lower = q.lower()
    symbols = extract_symbols(q)
    if known_symbols:
        symbols = [s for s in symbols if s in known_symbols]

    if re.search(r"both|and", lower) and len(symbols) >= 2:
        return "MULTI_STOCK_HOLDERS", {"symbols": symbols[:2]}

    pct = extract_percent(q)
    sector = extract_sector(q)
    if sector and known_sectors and sector not in known_sectors:
        sector = None

    if pct is not None and sector and ("sector" in lower or "it sector" in lower):
        return "SECTOR_IMPACT", {"sector": sector, "change_percent": pct}

    if pct is not None and symbols:
        sym = symbols[0]
        return "STOCK_IMPACT", {"symbol": sym, "change_percent": pct}

    if ("highly exposed" in lower or "exposure" in lower) and sector:
        return "SECTOR_EXPOSURE", {"sector": sector, "min_percent": settings.sector_exposure_min_percent}

    if "explain" in lower or "exposure" in lower and extract_customer_name(q):
        name = extract_customer_name(q)
        return "CUSTOMER_EXPOSURE", {"customer_name": name, "customer_id": ""}

    if symbols and ("own" in lower or "hold" in lower or "who" in lower or "which" in lower):
        return "STOCK_HOLDERS", {"symbol": symbols[0]}

    if "highly exposed" in lower and sector:
        return "SECTOR_EXPOSURE", {"sector": sector, "min_percent": settings.sector_exposure_min_percent}

    return "UNKNOWN", {}


def validate_entities(intent: str, entities: dict[str, Any], known: dict[str, set[str]]) -> dict[str, Any] | None:
    if intent == "STOCK_HOLDERS":
        sym = entities.get("symbol")
        if sym not in known.get("symbols", set()):
            return None
        return {"symbol": sym}
    if intent == "MULTI_STOCK_HOLDERS":
        syms = entities.get("symbols") or []
        if not all(s in known.get("symbols", set()) for s in syms):
            return None
        return {"symbols": syms}
    if intent == "STOCK_IMPACT":
        sym = entities.get("symbol")
        if sym not in known.get("symbols", set()):
            return None
        return {"symbol": sym, "change_percent": float(entities.get("change_percent", 0))}
    if intent in ("SECTOR_IMPACT", "SECTOR_EXPOSURE"):
        sec = entities.get("sector")
        if sec not in known.get("sectors", set()):
            return None
        out = {"sector": sec}
        if intent == "SECTOR_EXPOSURE":
            out["min_percent"] = float(entities.get("min_percent", settings.sector_exposure_min_percent))
        else:
            out["change_percent"] = float(entities.get("change_percent", 0))
        return out
    if intent == "CUSTOMER_EXPOSURE":
        cid = entities.get("customer_id")
        name = entities.get("customer_name")
        if cid and cid in known.get("customer_ids", set()):
            return {"customer_id": cid, "customer_name": name or ""}
        if name:
            names = known.get("customer_names", set())
            if name in names or any(name.lower() in n.lower() for n in names):
                return {"customer_id": "", "customer_name": name}
        return None
    return None
